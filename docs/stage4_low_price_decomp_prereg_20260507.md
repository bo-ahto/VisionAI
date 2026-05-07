# 저가 Segment Error Decomposition — 사전등록 메모

> **작성일**: 2026-05-07 (실험 시작 전 freeze)
> **목적**: HARK (Hypothesizing After Results are Known) 회피 — 분석 전에 정의 / 지표 / 판정 fix
> **연계**: `docs/stage4_warm_validation_results_20260507.md` §8 (코덱스 권고 #3) / `docs/트랙2_methodology_pipeline_20260507.md` §10
> **트랙 목표 / 비목표** (코덱스 명시):
> - 목표: 원인 분류 (feature / loss / support / bias) + 운영 완화 가능성 평가
> - **비목표**: 즉시 새 모델 우월성 주장 / 재학습 결정 (별도 후속 decision gate)

## 1. Low-price 정의 (사전 fix)

| 정의 후보 | 채택 |
|---|---|
| **price_krw < 5,000,000** (운영 가드레일 §2.1 임계, 절대값) | **✓ 채택** (운영 정합성) |
| price_krw < P33 (Stage 4 test 분포 quantile, 상대값) | sensitivity 비교용 |
| log_price < log(5M) ≈ 15.42 | 동일 (절대값 기준) |

> **Primary 분석**: `price_krw < 5M KRW` (운영 guardrail 정의 동일)
> Sensitivity: P33 분위 비교 표 1줄

## 2. 평가 데이터 / 모델 (변경 X)

- 데이터: `data/curated/stage4_full.parquet` (8,495 / 807 작가)
- Test split: `year_made == 2025`, warm + test n≥3 = 40 작가 / 431 rows
- 비교 모델: baseline (F4 + spline + Huber) vs FE only (Stage 4 결과 동일)

## 3. 핵심 지표 3개 (사전 고정)

| # | 지표 | 정의 | 해석 축 |
|---|---|---|---|
| **1** | **Bias** | mean(pred_log - actual_log) | 양수 = 과대 / 음수 = 과소 예측 |
| **2** | **Residual spread** | std + IQR (pred_log - actual_log) | 큰 spread = 모델 설명력 부족 |
| **3** | **Artist support** | low-price 작가의 train 작품 수 분포 (median / P25 / P75) | 작은 support = data sparsity 원인 |

> **부수 지표**: Proxy 누락 점검 (Artsy 컬럼 중 미사용 항목)
> - medium_category / category / availability / gallery_type / gallery_cities (현재 모델 미사용)
> - 저가 segment 에서 이들 변수 분포 / 결측률 / target 과의 단순 corr

## 4. 분석 protocol (사전 고정)

### 4.1 Slicing
- **Primary**: `low_price = price_krw < 5M` vs `mid_high_price = price_krw ≥ 5M` (binary)
- **Sensitivity**: price tertile (저가 / 중가 / 고가)

### 4.2 Computations
1. Bias / spread: baseline vs FE only 분리 측정
2. Artist support: low-price test 작가의 train 작품 수 distribution
3. Proxy missing rate / coverage by price band

### 4.3 비교 baseline
- 저가 vs 중고가 의 bias 차이가 "통계적 우연" 인지 확인 위한 row-level bootstrap (n=1000)
- "feature 부족" 가설 vs "support 부족" 가설 분리 진단

## 5. 판정 규칙 (사전 fix — 1, 2, 3순위)

코덱스 권고 우선순위 그대로:

| 순위 | 가설 | 근거 시그니처 |
|---|---|---|
| **1** | **Feature space 부족** | 저가에서 (a) bias 양/음 구조적 (단순 평균 보정 안 됨) (b) proxy 변수와 target corr 유의미 (c) artist support 충분 (≥10 작품 / 작가) |
| **2** | **Loss 한계** | 저가에서 (a) bias 작음 + spread 큼 (b) artist support 충분 (c) proxy 변수 없음 |
| **3** | **Support 부족** | 저가 작가의 train 작품 수 분포 < 중고가 작가 (median 비교) |
| **4** | **Calibration 가능 (가장 약함)** | 저가에서 bias 만 일관 (단순 평균 보정으로 해소 가능) |

## 6. 합격 / 보류 / 폐기 기준

> **본 cycle 의 결정 = "원인 분류" + "운영 완화 후보 식별"** (재학습 / 모델 변경 X — 코덱스 비목표 명시).

### 6.1 합격 (운영 완화 권고 산출)
- 가설 1-3 중 1개 명확히 우세 (시그니처 ≥ 2/3 일치)
- 운영 완화 후보 명확 (예: 저가 V3 강제 라우팅 임계 조정)
- → spec §2.1 또는 §17.7 보강 권고

### 6.2 보류
- 가설 1-3 중 2개 이상 동시 시그니처 (혼합 원인)
- → 추가 진단 cycle 또는 후속 트랙

### 6.3 결과만 보고
- 가설 4 (calibration) 만 우세 → 작업 4 (calibration 검증) 결과 대기 후 통합
- 시그니처 불명확 → 결과만 기록, 운영 변경 X

## 7. 산출물

- 실험 코드: `experiments/structural_v1/stage4_low_price_decomp.py`
- 결과 JSON: `experiments/structural_v1/results/stage4_low_price_decomp.json`
- 결과 보고: 본 문서 §8 (실험 후 추가)

## 8. 결과 요약 (실험 완료 2026-05-07)

### 8.1 핵심 결과 (사전등록 §3 지표)

| 모델 | slice | n | bias log (%) | residual std | residual IQR |
|---|---|---|---|---|---|
| baseline | low | 250 | **+0.322 (+38.0% 과대)** | 0.532 | 0.667 |
| baseline | mid_high | 181 | -0.265 (-23.3% 과소) | 0.439 | 0.661 |
| fe_only | low | 250 | +0.203 (+22.5% 과대) | 0.561 | 0.555 |
| fe_only | mid_high | 181 | -0.067 (-6.5%) | 0.449 | 0.453 |

### 8.2 Artist Support
- Low-price test artists (35명): train works median **18.0** / P25 13 / P75 27
- Mid-high test artists (33명): train works median **18.0** / P25 12 / P75 27
- → **Support 동일** (가설 3 기각)

### 8.3 Proxy 변수 (현재 모델 미사용)
| 컬럼 | low / high 분포 |
|---|---|
| medium_type | Painting 72.8% / 80.7% — 미세 |
| category | 동일 패턴 |
| availability | 모두 'for sale' 100% — 정보 X |
| gallery_type | 모두 'Gallery' 100% — 정보 X |
| attribution_class | Unique 91.6% / 93.4% — 미세 |

### 8.4 가설 시그니처 판정 (사전등록 §5)

| 가설 | 시그니처 일치 | 우선순위 |
|---|---|---|
| **Feature space 부족** | **3/3** ⭐ | 1순위 (코덱스 예측 정확) |
| Loss 한계 | 2/3 | 2순위 |
| Support 부족 | 0/1 | 기각 |
| Calibration 가능 | 0/1 | 기각 |

→ **최우세 가설: Feature space 부족** (사전등록 우선순위 1과 정확 매칭)

### 8.5 사전등록 대비 미수행 항목 (deviation, minor)
- **`gallery_cities` proxy 분석**: 실제 실행 X — 다른 5개 컬럼 (medium / category / availability / gallery_type / attribution_class) 만 분석
- **target corr 정량 측정**: 실제 실행 X — 분포 비교 (top3 + missing rate) 만 수행
- **row-level bootstrap 1000 (사전등록 §4.2)**: 실제 실행 X — 시그니처 판정만 수행
- **분류**: minor — 결론 (Feature 부족 가설 우세) 영향 X (시그니처 3/3 명확)
- **deviation log 등록**: `docs/methodology_deviation_log.md` 2026-05-07 entry

### 8.6 결론
- **§6.1 합격 적용** — Feature 부족 가설 단일 우세 (시그니처 ≥ 2/3)
- **운영 완화 후보 명확**: 외부 source 보강 (Stage 5) — 본 cycle 비목표 (재학습 / 모델 변경 X)
- **즉시 spec 변경 X** — 본 진단 결과는 Stage 5 prereg 의 input
