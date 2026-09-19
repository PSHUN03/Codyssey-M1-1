"""
[보너스] 분해 모델 선택 근거 검증
- 질문 1: 계절 변동폭이 가격 수준에 비례하는가? (비례하면 승법, 일정하면 가법)
- 질문 2: 고전적 분해(이동평균)와 STL(LOESS, 로버스트) 결과가 다른가?
- X-11/SEATS는 외부 실행파일(X-13ARIMA-SEATS)이 필요해 이 환경에서는 실행하지 않고, 사용 가능 여부만 기록한다.
"""
import os
import shutil
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose, STL

BASE_DIR = r"C:\Users\hunhu\OneDrive\Desktop\Codyssey AI\3. AI 응용 학습\M1-1"
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
TARGETS = ["서울", "지방광역시_통합"]

def main():
    wide = pd.read_csv(os.path.join(PROCESSED_DIR, "wide_monthly.csv"), index_col=0, parse_dates=True).asfreq("MS")
    rows = []
    lines = []

    for name in TARGETS:
        s = wide[name]

        # 1) 계절 변동폭의 규모 의존성: 초기(2007-2012) vs 후기(2019-2024), 추세 대비 편차의 표준편차
        add = seasonal_decompose(s, model="additive", period=12)
        mul = seasonal_decompose(s, model="multiplicative", period=12)
        dev_abs = s - add.trend            # 절대 편차(만원/㎡)
        dev_ratio = s / mul.trend - 1      # 상대 편차(비율)
        early, late = slice("2007-01", "2012-12"), slice("2019-01", "2024-12")
        lvl_e, lvl_l = mul.trend[early].mean(), mul.trend[late].mean()
        sd_abs_e, sd_abs_l = dev_abs[early].std(), dev_abs[late].std()
        sd_rat_e, sd_rat_l = dev_ratio[early].std(), dev_ratio[late].std()
        lines.append(f"[{name}] 추세 수준 {lvl_e:.0f} -> {lvl_l:.0f} 만원/㎡ (x{lvl_l/lvl_e:.2f})")
        lines.append(f"[{name}] 추세 대비 편차 표준편차(절대, 만원/㎡): {sd_abs_e:.1f} -> {sd_abs_l:.1f} (x{sd_abs_l/sd_abs_e:.2f})")
        lines.append(f"[{name}] 추세 대비 편차 표준편차(상대, %): {sd_rat_e*100:.2f} -> {sd_rat_l*100:.2f} (x{sd_rat_l/sd_rat_e:.2f})")

        # 2) 가법 vs 승법: 잔차의 상대 변동
        res_add_rel = (add.resid / mul.trend).dropna()
        res_mul_rel = (mul.resid - 1).dropna()
        lines.append(f"[{name}] 잔차 상대 표준편차(%): 가법 초기 {res_add_rel[early].std()*100:.2f} / 후기 {res_add_rel[late].std()*100:.2f}, "
                     f"승법 초기 {res_mul_rel[early].std()*100:.2f} / 후기 {res_mul_rel[late].std()*100:.2f}")

        # 3) 고전적(승법) vs STL(로그 변환 = 승법에 해당, 로버스트)
        stl = STL(np.log(s), period=12, robust=True).fit()
        stl_seas = np.exp(stl.seasonal)
        stl_by_month = stl_seas.groupby(stl_seas.index.month).mean()
        cls_by_month = mul.seasonal.groupby(mul.seasonal.index.month).mean()
        yearly_amp = stl_seas.groupby(stl_seas.index.year).apply(lambda x: (x.max() - x.min()) * 100)
        corr = np.corrcoef(stl_by_month.values, cls_by_month.values)[0, 1]
        lines.append(f"[{name}] 고전적(승법) 계절 진폭 {(cls_by_month.max()-cls_by_month.min())*100:.2f}%p, 최고 {cls_by_month.idxmax()}월/최저 {cls_by_month.idxmin()}월")
        lines.append(f"[{name}] STL(로그,로버스트) 계절 진폭 평균 {(stl_by_month.max()-stl_by_month.min())*100:.2f}%p, 최고 {stl_by_month.idxmax()}월/최저 {stl_by_month.idxmin()}월, "
                     f"연도별 진폭 범위 {yearly_amp.min():.2f}~{yearly_amp.max():.2f}%p, 월별 계절계수 상관 {corr:.3f}")
        lines.append(f"[{name}] 추세값 산출 개월 수: 고전적 {mul.trend.notna().sum()} / STL {stl.trend.notna().sum()} (전체 {len(s)})")

        for m in range(1, 13):
            rows.append({"시리즈": name, "월": m, "고전적_승법": cls_by_month[m], "STL_로그": stl_by_month[m]})

    lines.append(f"X-13ARIMA-SEATS 실행파일(x13as) 사용 가능 여부: {'가능' if shutil.which('x13as') else '불가(미설치)'}")

    pd.DataFrame(rows).to_csv(os.path.join(PROCESSED_DIR, "seasonal_method_comparison.csv"), index=False, encoding="utf-8-sig")
    with open(os.path.join(PROCESSED_DIR, "decomposition_method_comparison.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("ok")

if __name__ == "__main__":
    main()
