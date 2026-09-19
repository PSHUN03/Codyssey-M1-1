"""
전처리 스크립트
- 원본 개별 거래(raw) -> 정제(clean) -> 지역/도시별 월별 대표값(중앙값) 집계
- 가격 지표: 면적당 단가(만원/㎡) = dealAmount / excluUseAr
- 이상치 기준: (지역, 연도) 그룹별 면적당단가의 IQR 1.5배 벗어나는 거래 제거
- 최종 비교 시리즈 8개: 서울 / 지방광역시_통합 / 부산 / 대구 / 인천 / 광주 / 대전 / 울산
"""
import os
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\hunhu\OneDrive\Desktop\Codyssey AI\3. AI 응용 학습\M1-1"
RAW_CSV = os.path.join(BASE_DIR, "data", "raw", "apt_trade_raw.csv")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

METRO_CITIES = ["부산", "대구", "인천", "광주", "대전", "울산"]

def load_and_clean():
    df = pd.read_csv(RAW_CSV, encoding="utf-8-sig", dtype=str)
    n_raw = len(df)

    # 타입 변환
    df["dealAmount_num"] = (
        df["dealAmount"].str.replace(",", "", regex=False).astype(float)
    )  # 만원 단위
    df["excluUseAr_num"] = df["excluUseAr"].astype(float)
    df["dealYear_num"] = df["dealYear"].astype(int)
    df["dealMonth_num"] = df["dealMonth"].astype(int)

    # 기본 정합성: 면적/금액이 0 이하이거나 결측인 행 제거 (실제 결측/오류로 판단)
    before = len(df)
    df = df[(df["dealAmount_num"] > 0) & (df["excluUseAr_num"] > 0)].copy()
    n_invalid = before - len(df)

    # 면적당 단가 (만원/㎡)
    df["price_per_m2"] = df["dealAmount_num"] / df["excluUseAr_num"]

    return df, n_raw, n_invalid

def remove_outliers_iqr(df):
    """(지역, 연도) 그룹별 IQR 1.5배 기준으로 이상치 제거 (transform 기반, 컬럼 유실 없음)"""
    grp = df.groupby(["지역", "dealYear_num"])["price_per_m2"]
    q1 = grp.transform(lambda s: s.quantile(0.25))
    q3 = grp.transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (df["price_per_m2"] >= lower) & (df["price_per_m2"] <= upper)
    removed = int((~mask).sum())
    return df[mask].copy(), removed

def build_monthly_series(df):
    """지역(구) 단위 월별 중앙값과, 도시 단위(풀링) 월별 중앙값, 지방광역시 통합 월별 중앙값 생성"""
    df["연월"] = df["dealYear_num"].astype(str) + "-" + df["dealMonth_num"].astype(str).str.zfill(2)

    # 구 단위 월별 중앙값 (참고용)
    gu_monthly = (
        df.groupby(["도시", "지역", "연월"])["price_per_m2"]
        .median()
        .reset_index()
        .rename(columns={"price_per_m2": "중앙값_만원_m2"})
    )

    # 도시 단위(개별 6개 광역시 + 서울): 해당 도시의 모든 구 거래를 풀링해서 월별 중앙값
    city_monthly = (
        df.groupby(["도시", "연월"])["price_per_m2"]
        .median()
        .reset_index()
        .rename(columns={"price_per_m2": "중앙값_만원_m2"})
    )
    city_monthly["시리즈"] = city_monthly["도시"]

    # 지방광역시 통합: 6개 광역시 거래를 전부 풀링해서 월별 중앙값
    metro_pool = df[df["도시"].isin(METRO_CITIES)]
    metro_monthly = (
        metro_pool.groupby("연월")["price_per_m2"]
        .median()
        .reset_index()
        .rename(columns={"price_per_m2": "중앙값_만원_m2"})
    )
    metro_monthly["시리즈"] = "지방광역시_통합"
    metro_monthly["도시"] = "지방광역시_통합"

    # 최종 8개 시리즈 결합: 서울, 부산, 대구, 인천, 광주, 대전, 울산, 지방광역시_통합
    final_series = pd.concat(
        [city_monthly[["시리즈", "연월", "중앙값_만원_m2"]],
         metro_monthly[["시리즈", "연월", "중앙값_만원_m2"]]],
        ignore_index=True,
    )

    return gu_monthly, final_series

def main():
    df, n_raw, n_invalid = load_and_clean()
    df_clean, n_outlier = remove_outliers_iqr(df)

    gu_monthly, final_series = build_monthly_series(df_clean)

    # 저장
    df_clean.to_csv(os.path.join(PROCESSED_DIR, "apt_trade_clean.csv"), index=False, encoding="utf-8-sig")
    gu_monthly.to_csv(os.path.join(PROCESSED_DIR, "gu_monthly_median.csv"), index=False, encoding="utf-8-sig")
    final_series.to_csv(os.path.join(PROCESSED_DIR, "final_8series_monthly.csv"), index=False, encoding="utf-8-sig")

    log_lines = [
        f"원본 행 수: {n_raw:,}",
        f"금액/면적 결측·오류로 제거: {n_invalid:,}",
        f"IQR 이상치로 제거: {n_outlier:,}",
        f"최종 정제 행 수: {len(df_clean):,}",
        f"최종 시리즈 수: {final_series['시리즈'].nunique()} (목표 8개)",
        f"시리즈 목록: {sorted(final_series['시리즈'].unique().tolist())}",
        f"연월 범위: {final_series['연월'].min()} ~ {final_series['연월'].max()}",
        f"최종 8개 시리즈 데이터 포인트 수: {len(final_series):,}",
    ]
    with open(os.path.join(PROCESSED_DIR, "preprocess_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print("\n".join(log_lines))

if __name__ == "__main__":
    main()
