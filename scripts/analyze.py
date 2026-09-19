"""
시계열 분석 및 시각화
- 시계열 기법 1: 12개월 이동평균 (추세 파악, 월별 노이즈 완화)
- 시계열 기법 2: 전년동월대비 변화율(YoY %) (변화 속도 파악)
- 파생 지표: 서울/지방광역시_통합 가격배율(격차) 추이
- 국면별 변화율(시각화 3)은 scripts/composition_index.py에서 산출
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

BASE_DIR = r"C:\Users\hunhu\OneDrive\Desktop\Codyssey AI\3. AI 응용 학습\M1-1"
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

SERIES_ORDER = ["서울", "지방광역시_통합", "부산", "대구", "인천", "광주", "대전", "울산"]
METRO = ["부산", "대구", "인천", "광주", "대전", "울산"]

def load_wide():
    df = pd.read_csv(os.path.join(PROCESSED_DIR, "final_8series_monthly.csv"), encoding="utf-8-sig")
    wide = df.pivot(index="연월", columns="시리즈", values="중앙값_만원_m2")
    wide = wide.sort_index()
    wide = wide[SERIES_ORDER]
    wide.index = pd.to_datetime(wide.index, format="%Y-%m")
    return wide

def compute_derived(wide):
    ma12 = wide.rolling(window=12, min_periods=12).mean()
    yoy = wide.pct_change(periods=12) * 100
    gap_ratio = wide["서울"] / wide["지방광역시_통합"]
    return ma12, yoy, gap_ratio

def plot1_trend(wide, ma12):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(wide.index, wide["서울"], color="#d62728", linewidth=1, alpha=0.3)
    ax.plot(ma12.index, ma12["서울"], color="#d62728", linewidth=2.5, label="서울 (12개월 이동평균)")
    ax.plot(wide.index, wide["지방광역시_통합"], color="#1f77b4", linewidth=1, alpha=0.3)
    ax.plot(ma12.index, ma12["지방광역시_통합"], color="#1f77b4", linewidth=2.5, label="지방광역시 통합 (12개월 이동평균)")
    for city in METRO:
        ax.plot(ma12.index, ma12[city], linewidth=0.8, alpha=0.5, linestyle="--", label=city)
    ax.set_title("서울 vs 지방광역시 아파트 면적당 가격 추이 (2006~2025)")
    ax.set_xlabel("연도")
    ax.set_ylabel("면적당 가격 (만원/㎡)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMAGES_DIR, "01_price_trend.png"), dpi=150)
    plt.close(fig)

def plot2_gap_ratio(gap_ratio):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(gap_ratio.index, gap_ratio, color="#9467bd", linewidth=1.5)
    ma12_gap = gap_ratio.rolling(12, min_periods=12).mean()
    ax.plot(ma12_gap.index, ma12_gap, color="#9467bd", linewidth=3, label="12개월 이동평균")
    ax.axhline(y=1, color="gray", linestyle=":", linewidth=1)
    ax.set_title("서울/지방광역시 통합 가격배율 추이 (격차 지표)")
    ax.set_xlabel("연도")
    ax.set_ylabel("배율 (서울 ÷ 지방광역시 통합)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMAGES_DIR, "02_gap_ratio.png"), dpi=150)
    plt.close(fig)

def main():
    wide = load_wide()
    ma12, yoy, gap_ratio = compute_derived(wide)

    plot1_trend(wide, ma12)
    plot2_gap_ratio(gap_ratio)

    wide.to_csv(os.path.join(PROCESSED_DIR, "wide_monthly.csv"), encoding="utf-8-sig")
    ma12.to_csv(os.path.join(PROCESSED_DIR, "ma12_monthly.csv"), encoding="utf-8-sig")
    yoy.to_csv(os.path.join(PROCESSED_DIR, "yoy_monthly.csv"), encoding="utf-8-sig")
    gap_ratio.to_csv(os.path.join(PROCESSED_DIR, "gap_ratio_monthly.csv"), encoding="utf-8-sig")

    # 핵심 수치 요약 (리포트용 근거 수치)
    lines = []
    lines.append(f"2006-01 서울 면적당가격: {wide['서울'].iloc[0]:.1f} 만원/㎡")
    lines.append(f"2025-12 서울 면적당가격: {wide['서울'].iloc[-1]:.1f} 만원/㎡")
    lines.append(f"2006-01 지방광역시통합 면적당가격: {wide['지방광역시_통합'].iloc[0]:.1f} 만원/㎡")
    lines.append(f"2025-12 지방광역시통합 면적당가격: {wide['지방광역시_통합'].iloc[-1]:.1f} 만원/㎡")
    lines.append(f"2006-01 서울/지방 배율: {gap_ratio.iloc[0]:.2f}배")
    lines.append(f"2025-12 서울/지방 배율: {gap_ratio.iloc[-1]:.2f}배")
    lines.append(f"배율 최고점: {gap_ratio.max():.2f}배 ({gap_ratio.idxmax().strftime('%Y-%m')})")
    lines.append(f"배율 최저점: {gap_ratio.min():.2f}배 ({gap_ratio.idxmin().strftime('%Y-%m')})")
    for city in SERIES_ORDER:
        total_growth = (wide[city].iloc[-1] / wide[city].iloc[0] - 1) * 100
        lines.append(f"{city} 2006~2025 첫 달 대비 마지막 달 변화율(단월 비교, 참고용): {total_growth:.1f}%")

    # 단월(첫 달/마지막 달) 비교는 해당 월의 변동에 민감하므로 연평균 기준 지표를 함께 산출
    annual = wide.groupby(wide.index.year).mean()
    annual.to_csv(os.path.join(PROCESSED_DIR, "annual_mean.csv"), encoding="utf-8-sig")
    gap_annual = gap_ratio.groupby(gap_ratio.index.year).mean()
    lines.append("")
    lines.append("[연평균 기준]")
    for city in SERIES_ORDER:
        growth = (annual.loc[2025, city] / annual.loc[2006, city] - 1) * 100
        lines.append(f"{city} 2006->2025 연평균 {annual.loc[2006, city]:.1f} -> {annual.loc[2025, city]:.1f} 만원/㎡ (+{growth:.1f}%)")
    for year in [2006, 2009, 2015, 2024, 2025]:
        lines.append(f"{year}년 서울/지방 배율 연평균: {gap_annual.loc[year]:.2f}배")

    with open(os.path.join(PROCESSED_DIR, "key_stats.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print("\n시각화 2개 저장 완료: 01_price_trend.png, 02_gap_ratio.png (03은 composition_index.py에서 생성)")

if __name__ == "__main__":
    main()
