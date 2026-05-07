# Stage 5A — External Source Feasibility + Acquisition Prereg

> **작성일**: 2026-05-07 (Stage 5 시작 전 freeze)
> **목적**: External feature acquisition 의 **source feasibility 검증 + 수집 protocol 사전등록** (acquisition vs modeling 분리, HARK 회피)
> **위치**: 새 Phase 2 = External Feature Acquisition + Validation (Stage 5) 의 **첫 단계**
> **연계**: `docs/stage4_short_term_track_results_20260507.md` (Feature 부족 가설 input) / `docs/stage5c_modeling_prereg_20260507.md` (별도 — 본 prereg 종결 후 작성)

> ⚠️ **본 prereg 적용 범위**: Stage 5A (feasibility) + 5B (acquisition execution + entity resolution + feature construction). **Modeling 검증 (5C) 는 별도 prereg** — acquisition 결과 보고 후 별도 freeze (HARK 회피).

> **트랙 목표 / 비목표** (코덱스):
> - 목표: 외부 source 의 acquisition 가능성 + 매칭 품질 + cohort coverage 검증
> - **비목표**: 새 모델 우월성 주장 / 재학습 결정 (5C 로 분리)

## 1. 배경 (Stage 5 의 input)

### 1.1 Stage 4 v3 + 단기 트랙 결과
- Stage 4 v3: BORDERLINE 보류 — 일반 warm 경로 `not advanced`
- **Feature 부족 가설 3/3 시그니처** (저가 error decomp): bias structural / spread 큼 / support 동일 / calibration 0/1
- Artsy 미사용 컬럼 모두 정보 X → **외부 source 필요** (코덱스)

### 1.2 Phase 2 재정의
- 기존 Phase 2 (Artsy-only confirmatory) **폐지** (Stage 4 가 사실상 confirmatory)
- 새 Phase 2 = **External Feature Acquisition + Validation = Stage 5 (5A-5D)**

## 2. Stage 5 구조 (코덱스 권고)

| 단계 | 목적 | 산출물 |
|---|---|---|
| **5A** (본 prereg) | Source feasibility + acquisition execution | scorecard / acquisition log / 통합 dataset |
| **5B** | Entity resolution + feature construction | matched dataset + feature dictionary |
| **5C** (별도 prereg) | Confirmatory modeling validation | 합격/보류/폐기 판정 |
| **5D** | Deployment / legal / monitoring decision | 운영 권고 |

## 3. Source Scorecard (사전 fix, 5축)

> 모든 candidate source 평가 — 평가 후 PASS source 만 5B 진입.

| 축 | 정의 | PASS 임계 |
|---|---|---|
| **1. Coverage** | 한국 작가 cohort cover 비율 (Artsy 823 / Stage 4 warm 120 기준) | warm artist ≥ 50% (≥ 60명) |
| **2. Price directness** | 가격 anchor 직접성 (가격 자체 / proxy / 정성) | 직접 (auction 가격 등) > proxy > 정성 |
| **3. Integration cost** | 데이터팀 / 인프라 / 매칭 비용 | 1주 이내 acquisition + entity resolution 가능 |
| **4. Legal risk** | 라이선스 / 저작권 / GDPR / TOS 위반 | 명시적 허용 또는 fair use 명확 |
| **5. Expected incremental signal** | Artsy 와 독립 정보 제공 정도 (correlation 낮을 것) | Artsy feature 와 corr ≤ 0.3 (사전 추정) |

> **PASS = 5축 모두 ✓** / **BORDERLINE = 4축 ✓ + 1축 ✗** (운영팀 / 의사결정자 검토) / **REJECT = 3축 이하 ✓**

## 4. Source Candidates (사전 우선순위)

### 4.1 1순위: Auction Archives
| Source | URL / 접근 | 한국 작가 추정 cover | 가격 anchor | License | LLM feasibility |
|---|---|---|---|---|---|
| **Christie's Online** | christies.com (검색 + scrape 가능) | 미상 — feasibility 필요 | 직접 (낙찰가) | TOS 검토 필요 | 검색 결과 sampling 가능 |
| **Sotheby's** | sothebys.com | 미상 | 직접 | TOS 검토 | 동일 |
| **Phillips** | phillips.com | 미상 (한국 작가 적음 예상) | 직접 | TOS 검토 | 동일 |
| **Heritage Auctions** | ha.com | 미상 (한국 작가 적음) | 직접 | TOS 검토 | 동일 |
| **K-Auction (한국 경매)** | k-auction.com | 높을 것 (한국 전문) | 직접 | TOS 검토 (한국법) | 한국어 검색 가능 |
| **Seoul Auction** | seoulauction.com | 매우 높음 (한국 전문) | 직접 | TOS 검토 | 한국어 검색 가능 |

> **5A feasibility 의무**: 위 6 source 중 K-Auction / Seoul Auction (한국 전문) 가 1차 우선 — 한국 작가 cover 자연 높음.

### 4.2 2순위: Provenance / Exhibition History
- **Artsy CV / Shows** (이미 가용): `data/artsy_kr_artists_with_links.csv` 의 `url_cv` / `url_shows` (1,925 작가)
  * 정량화 규칙 사전 제한 (코덱스 권고): 단순 count (solo / group / fair / institution) 만 사용, NLP 추출 X
- **Galerie Perrotin / Kukje / 학고재** 등 갤러리 직접 (개별 협의 필요, LLM 비목표)

### 4.3 3순위 (보조)
- **Artprice / Artnet** (paid): 가격 지수 / 시장 트렌드 — license 비용 검토
- **작가 SNS / Instagram followers** (Artsy followers 이미 보유)

### 4.4 비추천 (사전 제외)
- 미술 시장 일반 통계 (KAMS / 문체부) — 작가 단위 매칭 불가
- 미술 잡지 review / 비평 — 정량화 비용 너무 큼

## 5. Stage 5A Acquisition Protocol

### 5.1 1차 Feasibility (LLM 가능)
- 본 prereg 작성 (현재 단계)
- Source candidate 6 (auction) + 2 (Artsy CV) 의 web sample 검토 (10-20 samples per source)
- 한국 작가 cover 추정 (Stage 4 warm 120 명 기준 sampling)
- License / TOS 1차 검토 (각 source robots.txt + TOS 페이지)
- **scorecard 5축 평가** → PASS source 식별

### 5.2 2차 Acquisition (운영팀 / 데이터팀)
- LLM 비목표 — 데이터팀 작업
- PASS source 만 진입
- Entity resolution audit plan 별도 deliverable (코덱스 권고 #6)

### 5.3 3차 Feature Construction
- LLM 가능: feature dictionary 작성 (acquisition 데이터 기반)
- 데이터팀: matched dataset 생성

## 6. 합격 / 보류 / 폐기 결정 (5A 종료 시)

### 6.1 PASS (5B 진입)
- 1+ source 가 5축 scorecard 모두 ✓
- 또는 2+ source 가 4축 ✓ (BORDERLINE) + 운영팀 / 의사결정자 검토 후 합격

### 6.2 BORDERLINE (보류 — 추가 source 검토)
- PASS source 0 + BORDERLINE 1 — 후속 1주 검토
- License / 매칭 품질 추가 검증 필요

### 6.3 REJECT (Stage 5 폐기)
- 모든 candidate source REJECT (3축 이하 ✓)
- → Stage 5 자체 종결 + 다른 전략 (운영 calibration 의존 / 모델 family 변경) 검토

## 7. HARK 회피 / 비목표 명시

### 7.1 본 prereg 의 비목표 (5A-5B 한정)
- ❌ 새 모델 우월성 주장
- ❌ Cold-start MdAPE 개선 검증 (= 5C primary)
- ❌ 저가 segment harm 해소 검증 (= 5C secondary)
- ❌ 운영 spec 변경 (모델 fit 결과 기반 변경 X)

### 7.2 5C prereg 분리 의무
- 5A-5B 종결 후 acquisition 결과 (matched dataset) 확정
- 결과 보고 (5A-5B 종결 보고서)
- **그 후 5C prereg 별도 freeze** (modeling 가설 / metric / PASS 기준 사전등록)
- 5C prereg 는 acquisition 결과를 본 후 작성하므로 일부 HARK risk 존재 — 단, modeling family / baseline / metric 은 본 prereg 와 동일 freeze

### 7.3 Deviation log 의무
- 5A 진행 중 사전등록 외 source 발견 / 평가 기준 변경 시 즉시 기록
- `docs/methodology_deviation_log.md` 적용

## 8. 일정

| 주차 | 작업 | LLM 가능? |
|---|---|---|
| Week 1 | Source candidate web sampling + scorecard 평가 | ✓ |
| Week 2 | License / TOS 검토 + cover 정량 추정 | △ (법무 협의 필요) |
| Week 3 | 5A feasibility 결과 보고 | ✓ |
| Week 4-N | (PASS source 만) Acquisition execution + Entity resolution | ✗ 데이터팀 |

## 9. 산출물

- 본 prereg: `docs/stage5a_acquisition_prereg_20260507.md`
- Source scorecard: `docs/stage5a_source_scorecard.md` (Week 1 종료 시)
- Feasibility memo: `docs/stage5a_feasibility_memo.md` (Week 3 종료 시)
- 5A 결과 보고: `docs/stage5a_results_YYYYMMDD.md` (5A 종결 시)
- 5C prereg: `docs/stage5c_modeling_prereg_20260507.md` (별도, 5A 종결 후 작성)

## 10. 위험 + 대응

| 위험 | 대응 |
|---|---|
| K-Auction / Seoul Auction TOS 불허 | Christie's / Sotheby's 우선 + 학술 / fair use 검토 |
| Auction 한국 작가 cover < 50% | Artsy CV (2순위) 보강 또는 Stage 5 자체 보류 |
| Entity resolution 매칭률 < 70% | Manual audit sampling + threshold 재정의 (5B prereg 추가) |
| License / 저작권 risk | 법무 사전 검토 의무 (Week 2) |
| HARK risk (5C 가설 변경) | 5A-5B / 5C prereg 엄격 분리 + deviation log |

## 11. 코덱스 자문 이력 (Stage 5 관련)

| 차수 | 내용 |
|---|---|
| Stage 4 단기 트랙 종결 | Stage 5 prereg = "external feature acquisition" 중심 권고 |
| 본 prereg 사전 자문 (2026-05-07) | 4단계 (5A-5D) 구조 + 사전등록 9 항목 + acquisition vs modeling 분리 |
| 5A 종결 (예정) | feasibility 결과 review + 5C prereg 작성 자문 |

## 12. 다음 액션 (5A Week 1)

1. 본 prereg 검토 + 승인
2. K-Auction / Seoul Auction / Christie's / Sotheby's web sample 검토 (각 10-20 samples, 한국 작가 100 명 이름 sampling)
3. Robots.txt + TOS 1차 검토
4. Source scorecard 5축 평가 (`docs/stage5a_source_scorecard.md` 신규)
5. Week 1 종료 시 PASS / BORDERLINE / REJECT 판정
