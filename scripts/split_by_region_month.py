"""
원본 수집 데이터(data/raw/apt_trade_raw.csv)를 지역별 -> 월별 CSV로 분할
- 경로: data/regional/<도시>/<구·군>/<YYYY-MM>.csv
- 지역/도시/계약년월은 경로에 들어 있으므로 파일 안에서는 생략하고, 컬럼명은 한글로 변경
- 값은 원본 그대로이며, 거래금액의 천단위 쉼표만 제거해 숫자로 저장
- 거래가 없는 달은 파일을 만들지 않고, data/regional/INDEX.md에 지역별 요약을 남긴다
"""
import os
import pandas as pd

BASE_DIR = r"C:\Users\hunhu\OneDrive\Desktop\Codyssey AI\3. AI 응용 학습\M1-1"
RAW_CSV = os.path.join(BASE_DIR, "data", "raw", "apt_trade_raw.csv")
OUT_DIR = os.path.join(BASE_DIR, "data", "regional")

COLUMN_MAP = {
    "aptNm": "단지명",
    "buildYear": "건축년도",
    "dealAmount": "거래금액(만원)",
    "dealYear": "계약년",
    "dealMonth": "계약월",
    "dealDay": "계약일",
    "excluUseAr": "전용면적(㎡)",
    "floor": "층",
    "umdNm": "법정동",
    "jibun": "지번",
    "sggCd": "시군구코드",
    "dealingGbn": "거래유형",
    "buyerGbn": "매수자구분",
    "slerGbn": "매도자구분",
}

def main():
    df = pd.read_csv(RAW_CSV, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    df["dealAmount"] = df["dealAmount"].str.replace(",", "", regex=False).str.strip()
    df["dealDay_num"] = pd.to_numeric(df["dealDay"], errors="coerce")

    summary = []
    n_files = 0
    for (city, region), g_region in df.groupby(["도시", "지역"], sort=True):
        gu = region.split("_", 1)[1]
        region_dir = os.path.join(OUT_DIR, city, gu)
        os.makedirs(region_dir, exist_ok=True)

        for ym, g in g_region.groupby("계약년월", sort=True):
            g = g.sort_values(["dealDay_num", "aptNm"])
            out = g[list(COLUMN_MAP.keys())].rename(columns=COLUMN_MAP)
            out_name = f"{ym[:4]}-{ym[4:]}.csv"
            out.to_csv(os.path.join(region_dir, out_name), index=False, encoding="utf-8-sig")
            n_files += 1

        months = sorted(g_region["계약년월"].unique())
        summary.append({
            "도시": city, "구·군": gu, "거래 건수": len(g_region),
            "거래 있는 개월 수": len(months),
            "첫 달": f"{months[0][:4]}-{months[0][4:]}", "마지막 달": f"{months[-1][:4]}-{months[-1][4:]}",
        })

    lines = [
        "# 지역별·월별 원본 거래 데이터",
        "",
        "국토교통부 아파트매매 실거래자료를 **도시 > 구·군 > 월** 순으로 나눈 CSV입니다. `data/raw/apt_trade_raw.csv`(460만 행)를 분할한 것이며 파일 하나가 한 지역의 한 달 거래 목록입니다.",
        "",
        "- 경로: `data/regional/<도시>/<구·군>/<YYYY-MM>.csv` (예: `서울/강남구/2025-01.csv`)",
        "- 거래가 한 건도 없는 달은 파일이 없습니다.",
        "- 컬럼: 단지명, 건축년도, 거래금액(만원), 계약년/월/일, 전용면적(㎡), 층, 법정동, 지번, 시군구코드, 거래유형, 매수자구분, 매도자구분",
        "- 원본과 값은 같고, 거래금액의 천단위 쉼표만 제거했습니다. 이상치 제거 전 데이터입니다.",
        "- 광주는 2026년 행정통합 이후 시군구코드가 `12xxx`입니다.",
        "",
        f"총 {len(summary)}개 지역, {n_files:,}개 파일, {len(df):,}건",
        "",
        "| 도시 | 구·군 | 거래 건수 | 거래 있는 개월 수 | 첫 달 | 마지막 달 |",
        "|---|---|---:|---:|---|---|",
    ]
    for s in summary:
        lines.append(f"| {s['도시']} | [{s['구·군']}]({s['도시']}/{s['구·군']}) | {s['거래 건수']:,} | {s['거래 있는 개월 수']} | {s['첫 달']} | {s['마지막 달']} |")

    with open(os.path.join(OUT_DIR, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"regions={len(summary)} files={n_files} rows={len(df)}")

if __name__ == "__main__":
    main()
