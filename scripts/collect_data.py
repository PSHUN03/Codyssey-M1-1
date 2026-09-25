"""
국토교통부 아파트매매 실거래자료 수집 스크립트
- 서울 25개구 + 부산16 + 대구9 + 인천11 + 광주5(신코드) + 대전5 + 울산5 = 76개 지역
- 기간: 2006년 1월 ~ 2025년 12월 (240개월)
- 일일 트래픽 한도(10,000건)에 걸리면 자동 중단, 다시 실행하면 이어서 진행(캐싱/재개)
"""
import os
import re
import time
import csv
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from dotenv import load_dotenv

BASE_DIR = r"C:\Users\hunhu\OneDrive\Desktop\Codyssey AI\3. AI 응용 학습\M1-1"
load_dotenv(os.path.join(BASE_DIR, ".env"))
KEY = os.getenv("MOLIT_API_KEY")

URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"

RAW_CSV = os.path.join(BASE_DIR, "data", "raw", "apt_trade_raw.csv")
LOG_PATH = os.path.join(BASE_DIR, "data", "raw", "collect_log.txt")

REGIONS = {
    # 서울 25
    "서울_강남구": ("서울", "11680"), "서울_강동구": ("서울", "11740"), "서울_강북구": ("서울", "11305"),
    "서울_강서구": ("서울", "11500"), "서울_관악구": ("서울", "11620"), "서울_광진구": ("서울", "11215"),
    "서울_구로구": ("서울", "11530"), "서울_금천구": ("서울", "11545"), "서울_노원구": ("서울", "11350"),
    "서울_도봉구": ("서울", "11320"), "서울_동대문구": ("서울", "11230"), "서울_동작구": ("서울", "11590"),
    "서울_마포구": ("서울", "11440"), "서울_서대문구": ("서울", "11410"), "서울_서초구": ("서울", "11650"),
    "서울_성동구": ("서울", "11200"), "서울_성북구": ("서울", "11290"), "서울_송파구": ("서울", "11710"),
    "서울_양천구": ("서울", "11470"), "서울_영등포구": ("서울", "11560"), "서울_용산구": ("서울", "11170"),
    "서울_은평구": ("서울", "11380"), "서울_종로구": ("서울", "11110"), "서울_중구": ("서울", "11140"),
    "서울_중랑구": ("서울", "11260"),
    # 부산 16
    "부산_강서구": ("부산", "26440"), "부산_금정구": ("부산", "26410"), "부산_기장군": ("부산", "26710"),
    "부산_남구": ("부산", "26290"), "부산_동구": ("부산", "26170"), "부산_동래구": ("부산", "26260"),
    "부산_부산진구": ("부산", "26230"), "부산_북구": ("부산", "26320"), "부산_사상구": ("부산", "26530"),
    "부산_사하구": ("부산", "26380"), "부산_서구": ("부산", "26140"), "부산_수영구": ("부산", "26500"),
    "부산_연제구": ("부산", "26470"), "부산_영도구": ("부산", "26200"), "부산_중구": ("부산", "26110"),
    "부산_해운대구": ("부산", "26350"),
    # 대구 9
    "대구_군위군": ("대구", "27720"), "대구_남구": ("대구", "27200"), "대구_달서구": ("대구", "27290"),
    "대구_달성군": ("대구", "27710"), "대구_동구": ("대구", "27140"), "대구_북구": ("대구", "27230"),
    "대구_서구": ("대구", "27170"), "대구_수성구": ("대구", "27260"), "대구_중구": ("대구", "27110"),
    # 인천 11
    "인천_강화군": ("인천", "28710"), "인천_검단구": ("인천", "28290"), "인천_계양구": ("인천", "28245"),
    "인천_남동구": ("인천", "28200"), "인천_미추홀구": ("인천", "28177"), "인천_부평구": ("인천", "28237"),
    "인천_서해구": ("인천", "28275"), "인천_연수구": ("인천", "28185"), "인천_영종구": ("인천", "28155"),
    "인천_옹진군": ("인천", "28720"), "인천_제물포구": ("인천", "28125"),
    # 광주 5 (신코드, 전남광주통합특별시)
    "광주_동구": ("광주", "12210"), "광주_서구": ("광주", "12240"), "광주_남구": ("광주", "12270"),
    "광주_북구": ("광주", "12300"), "광주_광산구": ("광주", "12330"),
    # 대전 5
    "대전_대덕구": ("대전", "30230"), "대전_동구": ("대전", "30110"), "대전_서구": ("대전", "30170"),
    "대전_유성구": ("대전", "30200"), "대전_중구": ("대전", "30140"),
    # 울산 5
    "울산_남구": ("울산", "31140"), "울산_동구": ("울산", "31170"), "울산_북구": ("울산", "31200"),
    "울산_울주군": ("울산", "31710"), "울산_중구": ("울산", "31110"),
}

def month_range(start_ym, end_ym):
    start = datetime.strptime(start_ym, "%Y%m")
    end = datetime.strptime(end_ym, "%Y%m")
    months = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append(f"{y:04d}{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months

MONTHS = month_range("200601", "202512")

FIELDNAMES = [
    "지역", "도시", "계약년월", "aptNm", "buildYear", "dealAmount", "dealYear", "dealMonth", "dealDay",
    "excluUseAr", "floor", "jibun", "umdNm", "sggCd", "dealingGbn", "buyerGbn", "slerGbn",
]

def load_done_pairs():
    done = set()
    if os.path.exists(RAW_CSV):
        with open(RAW_CSV, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                done.add((row["지역"], row["계약년월"]))
    return done

def ensure_csv_header():
    if not os.path.exists(RAW_CSV):
        os.makedirs(os.path.dirname(RAW_CSV), exist_ok=True)
        with open(RAW_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def parse_items(xml_text):
    root = ET.fromstring(xml_text)
    header = root.find(".//header")
    result_code = header.find("resultCode").text if header is not None else None
    items_el = root.find(".//items")
    rows = []
    if items_el is not None:
        for item in items_el.findall("item"):
            row = {child.tag: (child.text or "").strip() for child in item}
            rows.append(row)
    return result_code, rows

def log(msg):
    msg = re.sub(r"serviceKey=[^&\s)']+", "serviceKey=***", str(msg))
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n")

def main():
    ensure_csv_header()
    done = load_done_pairs()
    log(f"시작. 이미 완료된 조합: {len(done)}개")

    total_pairs = len(REGIONS) * len(MONTHS)
    processed_this_run = 0
    written_rows_this_run = 0

    with open(RAW_CSV, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        for region_name, (city, code) in REGIONS.items():
            for ymd in MONTHS:
                if (region_name, ymd) in done:
                    continue

                params = {
                    "serviceKey": KEY,
                    "LAWD_CD": code,
                    "DEAL_YMD": ymd,
                    "numOfRows": 5000,
                    "pageNo": 1,
                }
                try:
                    res = requests.get(URL, params=params, timeout=15)
                except Exception as e:
                    log(f"네트워크 오류 {region_name} {ymd}: {e} -> 재시도 없이 다음으로")
                    continue

                if res.status_code == 429:
                    log(f"HTTP 429(요청 한도 초과) {region_name} {ymd} -> 일일 트래픽 한도 도달로 판단, 수집 중단")
                    log("내일 다시 실행하면 이어서 진행됩니다.")
                    return

                if res.status_code != 200:
                    log(f"HTTP 오류 {region_name} {ymd}: status={res.status_code}")
                    continue

                if "OpenAPI_ServiceResponse" in res.text or "LIMITED_NUMBER_OF_SERVICE_REQUESTS" in res.text or "SERVICE_KEY" in res.text.upper():
                    log(f"트래픽/인증 한도 관련 응답 감지 {region_name} {ymd}: {res.text[:300]}")
                    log("일일 트래픽 한도로 추정되어 수집을 중단합니다. 내일 다시 실행하면 이어서 진행됩니다.")
                    return

                try:
                    result_code, rows = parse_items(res.text)
                except ET.ParseError:
                    # 트래픽 초과 시 XML 대신 JSON 에러 메시지가 오는 경우가 많음
                    log(f"XML 파싱 실패 (트래픽 초과 가능성) {region_name} {ymd}: {res.text[:300]}")
                    log("일일 트래픽 한도로 추정되어 수집을 중단합니다. 내일 다시 실행하면 이어서 진행됩니다.")
                    return

                if result_code not in ("000", None):
                    log(f"API 오류 {region_name} {ymd}: resultCode={result_code}, body={res.text[:300]}")
                    if result_code in ("22", "30", "31"):
                        log("트래픽/인증 관련 오류로 판단되어 수집을 중단합니다.")
                        return
                    continue

                for row in rows:
                    out_row = {k: row.get(k, "") for k in FIELDNAMES if k not in ("지역", "도시", "계약년월")}
                    out_row["지역"] = region_name
                    out_row["도시"] = city
                    out_row["계약년월"] = ymd
                    writer.writerow(out_row)
                    written_rows_this_run += 1

                f.flush()
                processed_this_run += 1

                if processed_this_run % 200 == 0:
                    log(f"진행 중: {processed_this_run}개 조합 처리, 누적 행 {written_rows_this_run}건")

                time.sleep(0.05)

    log(f"완료. 이번 실행에서 {processed_this_run}개 조합 처리, {written_rows_this_run}건 저장. "
        f"전체 {total_pairs}개 조합 중 남은 것 없으면 수집 끝.")

if __name__ == "__main__":
    main()
