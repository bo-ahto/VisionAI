# 저가 Segment Error Decomposition — 사전등록 메모

> **작성일**: 2026-05-07 (실험 시작 전 freeze)
> **목적**: HARK (Hypothesizing After Results are Known) 회피 — 분석 전에 정의 / 지표 / 판정 fix
> **연계**: `docs/stage4_warm_validation_results_20260507.md` §8 (코덱스 권고 #3) / `docs/methodology_pipeline_20260507.md` §10
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

## 8. 결과 요약 (실험 후 추가)

(실험 완료 후 채워질 예정)
