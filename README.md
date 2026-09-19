# 서울 vs 지방광역시 아파트 가격 격차 분석

국토교통부 아파트매매 실거래자료(2006\~2025년, 20년치)를 76개 지역(서울 25개구 + 지방광역시 6곳 51개구)에서 수집해, 서울과 지방광역시 간 아파트 가격 격차가 어떻게 변화해왔는지 분석한 프로젝트입니다.

전체 분석 내용은 [**REPORT.md**](REPORT.md)에 있습니다. 아래 목차에서 원하는 항목으로 바로 이동할 수 있습니다.

---

## 목차

### 📄 리포트
- [1. 분석 주제 및 선정 이유](REPORT.md#1-분석-주제-및-선정-이유)
- [2. 분석 질문 (3개 이상)](REPORT.md#2-분석-질문-3개-이상)
- [3. 데이터 설명](REPORT.md#3-데이터-설명)
  - [가격 지표 정의](REPORT.md#가격-지표-정의)
- [4. 분석 결과 및 시각화](REPORT.md#4-분석-결과-및-시각화)
- [5. 인사이트 (3개 이상)](REPORT.md#5-인사이트-3개-이상)
- [6. 결론 및 한계점](REPORT.md#6-결론-및-한계점)
  - [결론](REPORT.md#결론)
  - [한계점](REPORT.md#한계점)
- [7. [보너스] 시계열 심화 — 추세/계절성 분해](REPORT.md#7-보너스-시계열-심화--추세계절성-분해)
- [8. AI 사용 로그](REPORT.md#8-ai-사용-로그)
- [9. 재현 방법](REPORT.md#9-재현-방법)

### 📊 시각화 바로가기
| 시각화 | 이미지 | 리포트 설명 |
|---|---|---|
| 서울 vs 지방광역시 가격 추이 | [열기](images/01_price_trend.png) | [설명](REPORT.md#시각화-1--서울-vs-지방광역시-면적당-가격-추이) |
| 서울/지방 가격배율(격차) 추이 | [열기](images/02_gap_ratio.png) | [설명](REPORT.md#시각화-2--서울지방광역시-가격배율격차-지표-추이) |
| 국면별 누적 변화율 비교 | [열기](images/03_period_comparison.png) | [설명](REPORT.md#시각화-3--국면별-누적-가격-변화율-비교) |
| [보너스] 추세/계절성 분해 | [열기](images/04_seasonal_decomposition.png) | [설명](REPORT.md#7-보너스-시계열-심화--추세계절성-분해) |

### 💡 인사이트 바로가기
- [인사이트 1 — 20년간 격차는 전반적으로 확대됐다](REPORT.md#인사이트-1--20년간-격차는-전반적으로-확대됐다)
- [인사이트 2 — 격차는 국면별로 출렁였다](REPORT.md#인사이트-2--격차는-일방적-확대가-아니라-국면별로-출렁였다)
- [인사이트 3 — 지방광역시 내부에도 격차가 있다](REPORT.md#인사이트-3--지방광역시로-뭉뚱그리면-안-보이는-내부-격차가-있다)

### 🐍 코드 바로가기
| 스크립트 | 역할 |
|---|---|
| [`scripts/collect_data.py`](scripts/collect_data.py) | 국토부 Open API로 76개 지역 × 240개월 원본 데이터 수집 (캐싱/재개 로직 포함) |
| [`scripts/preprocess.py`](scripts/preprocess.py) | 면적당 단가 계산, IQR 이상치 제거, 8개 시리즈 월별 집계 |
| [`scripts/analyze.py`](scripts/analyze.py) | 이동평균·국면별 변화율 계산 및 시각화 3종 생성 |
| [`scripts/decompose.py`](scripts/decompose.py) | [보너스] 추세/계절성/잔차 분해 및 시각화 생성 |

### 🗂 데이터 바로가기
| 파일 | 내용 |
|---|---|
| [**`data/regional/`**](data/regional/INDEX.md) | **API로 받은 원본 거래 데이터 460만 건을 지역(75개 구·군) → 월별 CSV로 분할** (예: [서울 강남구 2025-01](data/regional/서울/강남구/2025-01.csv)). 지역별 요약은 [INDEX.md](data/regional/INDEX.md) |
| [`final_8series_monthly.csv`](data/processed/final_8series_monthly.csv) | 서울/지방광역시_통합/6개 도시 — 8개 시리즈 월별 중앙값 (핵심 산출물) |
| [`wide_monthly.csv`](data/processed/wide_monthly.csv) | 위 데이터를 연월×시리즈 wide 포맷으로 피벗 |
| [`ma12_monthly.csv`](data/processed/ma12_monthly.csv) | 12개월 이동평균 |
| [`yoy_monthly.csv`](data/processed/yoy_monthly.csv) | 전년동월대비 변화율(YoY %) |
| [`gap_ratio_monthly.csv`](data/processed/gap_ratio_monthly.csv) | 서울/지방광역시 가격배율(격차 지표) |
| [`period_comparison.csv`](data/processed/period_comparison.csv) | 국면별 누적 변화율 비교 |
| [`key_stats.txt`](data/processed/key_stats.txt) | 리포트에 인용된 핵심 수치 요약 |
| [`gu_monthly_median.csv`](data/processed/gu_monthly_median.csv) | 76개 구 단위 월별 중앙값 (참고용 상세 데이터) |
| [`seasonal_coefficients.csv`](data/processed/seasonal_coefficients.csv) | [보너스] 월별 계절 계수 (서울/지방광역시 통합) |
| [`decomposition_서울.csv`](<data/processed/decomposition_서울.csv>) / [`decomposition_지방광역시_통합.csv`](<data/processed/decomposition_지방광역시_통합.csv>) | [보너스] 추세·계절성·잔차 분해 원본 값 |

---

## 빠른 시작 (재현 방법)

### 개발 환경
- Python 3.10 이상 (개발 시 사용한 버전: 3.14.7)

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
[`.env.example`](.env.example)을 복사해 `.env` 파일을 만들고, 공공데이터포털에서 발급받은 국토교통부_아파트 매매 실거래자료 API 인증키를 넣습니다.
```
MOLIT_API_KEY=발급받은키
```

### 3. 실행 순서
```bash
python scripts/collect_data.py   # 1) 원본 데이터 수집 — 76개 지역 x 240개월. 일일 API 트래픽 한도(약 10,000건)로 인해 여러 날에 나눠 실행될 수 있으며, 재실행 시 이미 받은 조합은 자동으로 건너뜁니다.
python scripts/split_by_region_month.py   # (선택) 원본을 data/regional/ 아래 지역별·월별 CSV로 분할
python scripts/preprocess.py     # 2) 정제 + IQR 이상치 제거 + 8개 시리즈 월별 집계
python scripts/analyze.py        # 3) 이동평균/변화율 계산 + 시각화 3종 생성 (images/ 폴더에 저장)
python scripts/decompose.py      # 4) [보너스] 추세/계절성/잔차 분해 + 시각화 1종 생성
```

---

## 프로젝트 구조

```
M1-1/
├── README.md                   # 이 파일 (목차/바로가기)
├── REPORT.md                   # 분석 리포트 (전체 내용)
├── requirements.txt            # 의존성 (버전 고정)
├── .env.example                # API 키 입력 양식
├── scripts/
│   ├── collect_data.py         # 국토부 API 데이터 수집
│   ├── preprocess.py           # 정제 + 이상치 제거 + 월별 집계
│   ├── analyze.py              # 시계열 분석 + 시각화
│   └── decompose.py            # [보너스] 추세/계절성 분해
├── images/
│   ├── 01_price_trend.png
│   ├── 02_gap_ratio.png
│   ├── 03_period_comparison.png
│   └── 04_seasonal_decomposition.png   # [보너스]
└── data/
    ├── raw/                    # 수집 로그 (460만 행 단일 CSV는 용량 때문에 .gitignore 처리)
    ├── regional/               # 원본 데이터를 도시/구·군/월별 CSV로 분할한 것 (INDEX.md 참고)
    └── processed/              # 분석에 사용된 집계 데이터 전체
```

## 데이터 출처 및 라이선스
국토교통부 아파트매매 실거래자료 (공공데이터포털 Open API, 공공누리 자유이용 조건). 자세한 출처·기간·정제 기준은 [REPORT.md — 데이터 설명](REPORT.md#3-데이터-설명) 참고.
