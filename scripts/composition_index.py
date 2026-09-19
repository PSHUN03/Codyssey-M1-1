"""
구성 보정 지수 + 국면별 변화율(3가지 산정 방식 비교)

문제: 월별 ㎡당 중앙값은 거래 구성(면적·연식·지역 비중)이 바뀌면 가격이 오르지 않아도 변한다.
방법: 거래를 (지역 x 면적대 x 연식대) 칸으로 나눠 칸별 연도 중앙값을 구하고,
      인접한 두 해에 모두 충분한 거래(각 5건 이상)가 있는 칸만 골라 칸별 변화율을
      두 해 거래 비중의 평균으로 가중한 기하평균(Tornqvist 방식)으로 합치고, 이를 연쇄 연결한다.
      연도별 값이 1년(12개월) 창이므로 단월 종점 문제(방법 1)도 함께 해소한다.
출력: data/processed/composition_adjusted_index.csv, period_comparison.csv, adjustment_diagnostics.txt
      images/03_period_comparison.png, images/05_composition_adjusted_check.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = r"C:\Users\hunhu\OneDrive\Desktop\Codyssey AI\3. AI 응용 학습\M1-1"
PROC = os.path.join(BASE_DIR, "data", "processed")
IMG = os.path.join(BASE_DIR, "images")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

METRO = ["부산", "대구", "인천", "광주", "대전", "울산"]
SERIES = ["서울", "지방광역시_통합"] + METRO
MIN_N = 5
PERIODS = {  # 구간: (직전 기준 연도, 끝 연도)
    "2008 금융위기\n(2008-2009)": (2007, 2009),
    "회복기\n(2013-2016)": (2012, 2016),
    "급등기\n(2017-2021)": (2016, 2021),
    "금리인상기\n(2022-2023)": (2021, 2023),
    "최근\n(2024-2025)": (2023, 2025),
}
CELL = ["지역", "aband", "ageband"]


def load_cells():
    df = pd.read_csv(
        os.path.join(PROC, "apt_trade_clean.csv"), encoding="utf-8-sig",
        usecols=["지역", "도시", "buildYear", "dealYear_num", "excluUseAr_num", "price_per_m2"],
        dtype={"지역": str, "도시": str, "buildYear": str},
    )
    n_all = len(df)
    df["by"] = pd.to_numeric(df["buildYear"], errors="coerce")
    n_missing_by = int(df["by"].isna().sum())
    df = df.dropna(subset=["by"]).copy()
    df["age"] = df["dealYear_num"] - df["by"]
    df["aband"] = pd.cut(df["excluUseAr_num"], [0, 60, 85, 10000], labels=["60이하", "60-85", "85초과"])
    df["ageband"] = pd.cut(df["age"], [-1000, 10, 25, 1000], labels=["10년이하", "11-25년", "25년초과"])
    g = df.groupby(CELL + ["dealYear_num"], observed=True)["price_per_m2"].agg(med="median", n="size").reset_index()
    city_of = df.drop_duplicates("지역").set_index("지역")["도시"]
    return g, city_of, n_all, n_missing_by


def chain_index(cells, log):
    """cells: 한 시리즈의 (칸, 연도, med, n). 2006=100인 연쇄 지수와 단계별 커버리지를 반환."""
    years = sorted(cells["dealYear_num"].unique())
    idx = {years[0]: 100.0}
    cover = {}
    for y in years[1:]:
        a = cells[cells.dealYear_num == y - 1]
        b = cells[cells.dealYear_num == y]
        m = a.merge(b, on=CELL, suffixes=("_a", "_b"))
        m = m[(m.n_a >= MIN_N) & (m.n_b >= MIN_N)]
        w = (m.n_a / m.n_a.sum() + m.n_b / m.n_b.sum()) / 2
        growth = float(np.exp((w * np.log(m.med_b / m.med_a)).sum()))
        idx[y] = idx[y - 1] * growth
        cover[y] = m.n_b.sum() / b.n.sum()
    log.append(f"  최소 커버리지(해당 해 거래 중 지수 계산에 쓰인 비중): {min(cover.values())*100:.1f}% ({min(cover, key=cover.get)}년), 평균 {np.mean(list(cover.values()))*100:.1f}%")
    return pd.Series(idx)


def main():
    log = []
    cells, city_of, n_all, n_missing_by = load_cells()
    log.append(f"정제 데이터 {n_all:,}건 중 건축년도 결측 {n_missing_by:,}건 제외")
    cells["도시"] = cells["지역"].map(city_of)
    log.append(f"칸 정의: 지역(구·군) x 면적대(60이하/60-85/85초과) x 연식대(10년이하/11-25/25년초과), 칸당 최소 {MIN_N}건")

    result = {}
    for name in SERIES:
        sub = cells[cells["도시"] == name] if name in ["서울"] + METRO else cells[cells["도시"].isin(METRO)]
        log.append(f"[{name}] 칸 수 {sub[CELL].drop_duplicates().shape[0]}")
        result[name] = chain_index(sub, log)
    adj = pd.DataFrame(result)
    adj.index.name = "연도"
    adj.to_csv(os.path.join(PROC, "composition_adjusted_index.csv"), encoding="utf-8-sig")

    # 방식별 국면 변화율
    wide = pd.read_csv(os.path.join(PROC, "wide_monthly.csv"), index_col=0, parse_dates=True)
    ma12 = pd.read_csv(os.path.join(PROC, "ma12_monthly.csv"), index_col=0, parse_dates=True)
    rows = []
    for label, (a, b) in PERIODS.items():
        start, end = a + 1, b
        seg = wide.loc[f"{start}-01":f"{end}-12"]
        for s in SERIES:
            rows.append({
                "구간": label.replace("\n", " "), "시리즈": s,
                "기존_첫달끝달(%)": (seg[s].iloc[-1] / seg[s].iloc[0] - 1) * 100,
                "MA12_12월기준(%)": (ma12.loc[f"{b}-12-01", s] / ma12.loc[f"{a}-12-01", s] - 1) * 100,
                "구성보정지수(%)": (adj.loc[b, s] / adj.loc[a, s] - 1) * 100,
            })
    comp = pd.DataFrame(rows)
    comp.to_csv(os.path.join(PROC, "period_comparison.csv"), index=False, encoding="utf-8-sig")

    log.append("\n[20년 누적 상승률: 2025 vs 2006]")
    for s in SERIES:
        log.append(f"  {s}: 구성보정 {adj.loc[2025, s]/adj.loc[2006, s]*100-100:+.1f}% (지수 {adj.loc[2025, s]:.0f})")
    gap_adj = adj["서울"] / adj["지방광역시_통합"] * 100
    gap_pooled = (wide["서울"] / wide["지방광역시_통합"]).groupby(wide.index.year).mean()
    gap_pooled_rel = gap_pooled / gap_pooled.loc[2006] * 100
    log.append(f"\n[서울/지방 상대 격차 지수, 2006=100] 구성보정 2025: {gap_adj.loc[2025]:.0f}, 풀링 중앙값 배율 기준 2025: {gap_pooled_rel.loc[2025]:.0f}")
    for y in [2009, 2015, 2021, 2024, 2025]:
        log.append(f"  {y}: 구성보정 {gap_adj.loc[y]:.0f} / 풀링 {gap_pooled_rel.loc[y]:.0f}")
    pd.DataFrame({"구성보정": gap_adj, "풀링중앙값배율": gap_pooled_rel}).to_csv(
        os.path.join(PROC, "gap_relative_index.csv"), encoding="utf-8-sig")

    # ---- 시각화 3: 국면별 누적 변화율 (구성 보정 채택, 방식별 비교) ----
    labels = list(PERIODS.keys())
    x = np.arange(len(labels))
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1])
    ax0 = fig.add_subplot(gs[0, :])
    for k, (s, col) in enumerate([("서울", "#d62728"), ("지방광역시_통합", "#1f77b4")]):
        vals = [comp[(comp["구간"] == l.replace("\n", " ")) & (comp["시리즈"] == s)]["구성보정지수(%)"].iloc[0] for l in labels]
        bars = ax0.bar(x + (k - 0.5) * 0.36, vals, 0.36, color=col, label=s.replace("_", " "))
        for r, v in zip(bars, vals):
            ax0.text(r.get_x() + r.get_width() / 2, v + (2 if v >= 0 else -7), f"{v:+.1f}%", ha="center", fontsize=9)
    ax0.axhline(0, color="black", linewidth=0.8)
    ax0.set_ylim(-14, 122)
    ax0.set_xticks(x); ax0.set_xticklabels(labels)
    ax0.set_ylabel("구간 누적 변화율 (%)")
    ax0.set_title("국면별 누적 가격 변화율: 서울 vs 지방광역시 통합 (구성 보정 지수 채택)")
    ax0.legend(); ax0.grid(alpha=0.3, axis="y")

    method_cols = [("기존_첫달끝달(%)", "#9e9e9e", "기존: 첫 달→끝 달"), ("MA12_12월기준(%)", "#7fb2e5", "12개월 이동평균 기준"), ("구성보정지수(%)", "#2b5d9b", "구성 보정 지수 (채택)")]
    for j, (s, title) in enumerate([("서울", "서울"), ("지방광역시_통합", "지방광역시 통합")]):
        ax = fig.add_subplot(gs[1, j])
        for k, (c, col, lab) in enumerate(method_cols):
            vals = [comp[(comp["구간"] == l.replace("\n", " ")) & (comp["시리즈"] == s)][c].iloc[0] for l in labels]
            ax.bar(x + (k - 1) * 0.26, vals, 0.26, color=col, label=lab)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks(x); ax.set_xticklabels([l.replace("\n", "\n") for l in labels], fontsize=8)
        ax.set_title(f"{title}: 산정 방식별 비교")
        ax.grid(alpha=0.3, axis="y")
        if j == 0:
            ax.set_ylabel("구간 누적 변화율 (%)"); ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "03_period_comparison.png"), dpi=150)
    plt.close(fig)

    # ---- 시각화 4(파일 05): 구성 보정 지수 경로 + 격차 상대지수 검증 ----
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    colors = {"서울": "#d62728", "지방광역시_통합": "#1f77b4"}
    for s in SERIES:
        if s in colors:
            axes[0].plot(adj.index, adj[s], linewidth=3, color=colors[s], label=s.replace("_", " "))
        else:
            axes[0].plot(adj.index, adj[s], linewidth=1, linestyle="--", alpha=0.7, label=s)
    for ax in axes:
        ax.set_xticks(range(2006, 2026, 3))
        ax.set_xticks(range(2006, 2026), minor=True)
    axes[0].set_title("구성 보정 가격지수 (2006=100)")
    axes[0].set_xlabel("연도"); axes[0].set_ylabel("지수")
    axes[0].legend(fontsize=8, ncol=2); axes[0].grid(alpha=0.3)
    axes[1].plot(gap_adj.index, gap_adj, linewidth=2.5, color="#9467bd", label="구성 보정 기준")
    axes[1].plot(gap_pooled_rel.index, gap_pooled_rel, linewidth=2, color="#7f7f7f", linestyle="--", label="풀링 중앙값 배율 기준")
    axes[1].axhline(100, color="black", linewidth=0.6, linestyle=":")
    axes[1].set_title("서울/지방광역시 통합 상대 격차 지수 (2006=100)")
    axes[1].set_xlabel("연도"); axes[1].set_ylabel("2006년 대비 격차 (100=변화 없음)")
    axes[1].legend(); axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "05_composition_adjusted_check.png"), dpi=150)
    plt.close(fig)

    with open(os.path.join(PROC, "adjustment_diagnostics.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    print("ok")


if __name__ == "__main__":
    main()
