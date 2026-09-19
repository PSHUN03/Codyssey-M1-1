"""
[보너스] 시계열 심화 옵션 (A) 시계열 분해
- 서울, 지방광역시_통합 월별 면적당가격을 추세(Trend)/계절성(Seasonal)/잔차(Residual)로 분해
- 승법(multiplicative) 모델 사용: 가격 수준 자체가 20년간 4배 가까이 성장해 계절 변동폭도 가격 수준에 비례할 것으로 보고 채택
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

BASE_DIR = r"C:\Users\hunhu\OneDrive\Desktop\Codyssey AI\3. AI 응용 학습\M1-1"
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

def main():
    wide = pd.read_csv(os.path.join(PROCESSED_DIR, "wide_monthly.csv"), index_col=0, parse_dates=True)
    wide = wide.asfreq("MS")  # 월초 기준 고정 빈도 (statsmodels 요구사항)

    fig, axes = plt.subplots(4, 2, figsize=(14, 12), sharex=True)
    targets = ["서울", "지방광역시_통합"]
    titles = ["서울", "지방광역시 통합"]

    all_seasonal = {}
    for col, (series_name, title) in enumerate(zip(targets, titles)):
        result = seasonal_decompose(wide[series_name], model="multiplicative", period=12)
        axes[0, col].plot(result.observed, color="black", linewidth=1)
        axes[0, col].set_title(f"{title} — 원계열(Observed)")
        axes[1, col].plot(result.trend, color="#d62728", linewidth=1.5)
        axes[1, col].set_title(f"{title} — 추세(Trend)")
        axes[2, col].plot(result.seasonal, color="#2ca02c", linewidth=1)
        axes[2, col].set_title(f"{title} — 계절성(Seasonal)")
        axes[3, col].plot(result.resid, color="#7f7f7f", linewidth=0.8)
        axes[3, col].axhline(y=1, color="black", linewidth=0.5, linestyle=":")
        axes[3, col].set_title(f"{title} — 잔차(Residual, 노이즈)")

        for row in range(4):
            axes[row, col].grid(alpha=0.3)

        # 월별 계절 계수 저장 (12개월 반복 패턴에서 처음 12개만 추출)
        seasonal_by_month = result.seasonal.groupby(result.seasonal.index.month).mean()
        all_seasonal[series_name] = seasonal_by_month

        decomp_df = pd.DataFrame({
            "observed": result.observed, "trend": result.trend,
            "seasonal": result.seasonal, "resid": result.resid,
        })
        decomp_df.to_csv(os.path.join(PROCESSED_DIR, f"decomposition_{series_name}.csv"), encoding="utf-8-sig")

    fig.suptitle("[보너스] 시계열 분해: 추세 / 계절성 / 잔차(노이즈)", fontsize=14)
    fig.tight_layout()
    fig.savefig(os.path.join(IMAGES_DIR, "04_seasonal_decomposition.png"), dpi=150)
    plt.close(fig)

    # 계절 계수 요약 (어느 달이 계절적으로 높고/낮은지)
    seasonal_df = pd.DataFrame(all_seasonal)
    seasonal_df.index.name = "월"
    seasonal_df.to_csv(os.path.join(PROCESSED_DIR, "seasonal_coefficients.csv"), encoding="utf-8-sig")

    lines = []
    for series_name in targets:
        s = all_seasonal[series_name]
        top_month = s.idxmax()
        bottom_month = s.idxmin()
        lines.append(f"{series_name}: 계절 계수 최고 {top_month}월({s.max():.4f}), 최저 {bottom_month}월({s.min():.4f}), 진폭(최고-최저) {(s.max()-s.min())*100:.2f}%p")

    with open(os.path.join(PROCESSED_DIR, "seasonal_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print("\n04_seasonal_decomposition.png 저장 완료")

if __name__ == "__main__":
    main()
