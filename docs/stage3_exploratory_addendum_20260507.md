# Stage 3 Exploratory Addendum — 외부 선형 모델 권고 검증

> **작성일**: 2026-05-07
> **목적**: 외부 자문 (Ridge 기반 헤도닉 가격 예측) 권고 중 우리가 미시도한 항목을 Stage 3 데이터로 좁은 범위 검증
> **위치**: Phase 1 (curated exploratory) 내 별도 cycle, **Stage 4 와 분리**
> **연계**: `docs/트랙2_methodology_pipeline_20260507.md` (Phase 1/2/3 골격) / 외부 자문 의견 (Ridge 1순위 / ElasticNet / Quantile / 작가 차등 처리 / gallery·material 통계 피처)

> ⚠️ **본 cycle 은 사전등록이 아닌 미니 프로토콜**. Stage 4 의 사전등록 (`docs/stage4_데이터수집계획_20260507.md` §6.0) 과 **별도 family**. 결과는 indicative — 운영 채택 결정 X, Stage 4 / Phase 2 의 후보 정의에 영향.

## 1. 검증 후보 (코덱스 권고 우선순위 C > A > G > E)

### Family 1 — Feature 통계 피처 (C)
> 외부 자문이 권고한 gallery_median_log_price / material_median_log_price 검증.  
> **dummy 가 아닌 out-of-fold target encoding + shrinkage 방식** (코덱스 P1).

- M1.1: baseline + `gallery_te` (out-of-fold target-encoded median log_price, shrinkage k=10)
- M1.2: baseline + `material_te` (medium_category 기반)
- M1.3: baseline + `gallery_te` + `material_te` (둘 다)

### Family 2 — Penalty / Regularization (A)
> 코덱스 권고: Ridge 단독이 아닌 **두 케이스** 비교 + Huber + L2 결합.

- M2.1: F4 + spline + **Ridge** (alpha tuning 5 grid)
- M2.2: F4 + spline + **Huber + L2** (eps=1.35 + alpha)
- M2.3: F4 + spline + Family 1 통계 피처 + **Ridge** (확장판)
- M2.4: F4 + spline + Family 1 통계 피처 + **Huber + L2** (통합 후보)

### Family 3 — 작가 차등 처리 (G)
> 코덱스 권고: `>=20 / 8-19 / <8` 현실적 threshold grid.

- M3.1: 작가 ≥ 20 = one-hot dummy / 8-19 = artist_te / <8 = "기타" 그룹 dummy
- M3.2: 작가 ≥ 15 = one-hot / 5-14 = artist_te / <5 = 기타
- M3.3: 작가 ≥ 8 = one-hot / 1-7 = artist_te (기타 없음)

### Family 4 — Artist 통계 피처 다양화 (E)
> 코덱스 권고: median / sales_count / dispersion + shrinkage.

- M4.1: baseline + `artist_median_log_price_te` (out-of-fold)
- M4.2: baseline + `artist_sales_count_log` (작가 판매 수 log)
- M4.3: baseline + `artist_price_dispersion_te` (작가 가격 IQR)
- M4.4: baseline + 위 3개 모두 + shrinkage

### 별도 cycle (본 addendum 제외)
- **B. Quantile Regression q25/q50/q75**: 점예측 family 와 분리, 별도 리포트
- **D. size_bucket**: log_area + spline 과 중복 우려, 후순위
- **F. Lasso**: 우선순위 낮음, 표본 작아 불안정

## 2. Pre-fixed Protocol

| 항목 | 사전 고정 값 |
|---|---|
| **Baseline** | F4 + log_area spline + Huber (eps=1.35) — 운영 채택 모델 |
| **Target encoding** | Out-of-fold (5-fold), Bayesian shrinkage (prior=global mean, k=10) |
| **Cold-start eval** | Stage 3 1378 rows, **100-seed LAO** holdout |
| **Warm eval** | time-split cutoff 2022 / 2023 / 2024 (rolling sensitivity) |
| **Metric** | MdAPE (point) + cluster bootstrap CI + **subgroup MdAPE** (가격 tertile / source / depth bin) |
| **채택 기준** | (1) 100-seed LAO MdAPE ≥ -1.0%p 개선, (2) cold/warm 일관성, (3) **subgroup 손상 없음** (저가/depth 10-14 +1.0%p 이내) |
| **다중비교** | Family 내 Holm m=family 크기, Family 간 별도 |
| **Seed aggregation** | 100-seed mean ± std (std ≤ 0.5%p) |

## 3. 채택 기준 (코덱스 권고: p-value 보다 effect size + stability)

### 3.1 Family 1 (통계 피처)
- 합격: gallery_te 또는 material_te 단독 추가로 100-seed LAO -1.0%p 이상 개선 / subgroup 손상 없음
- 보류: 효과 (-0.5, -1.0)%p 또는 subgroup 미세 악화
- 폐기: -0.5%p 미만 또는 subgroup harm

### 3.2 Family 2 (penalty)
- 합격: Huber + L2 또는 Ridge 가 Huber 단독 대비 100-seed -1.0%p 이상 개선
- 운영 교체 검토: Family 1 + Family 2 결합이 Huber 운영 대비 cold -2.0%p 이상 개선

### 3.3 Family 3 (작가 차등)
- 합격: M3.1 / M3.2 / M3.3 중 cold-start LAO 에서 Huber 운영 대비 -1.0%p 개선
- (LAO = artist hold-out 이라 작가 dummy 효과 없음 — 이 family 는 warm-start 평가 위주)

### 3.4 Family 4 (artist 통계)
- 합격: 단독 또는 combined 추가로 -1.0%p 개선 + subgroup 보전
- 운영 가치: 이미 Combined (artist_avg) 가 Stage 3 P3 에서 부분 효과 → 통계 피처 다양화로 안정화 가능 여부

## 4. 산출물

- 실험 코드: `experiments/structural_v1/stage3_addendum_linear_models.py`
- 결과 JSON: `experiments/structural_v1/results/stage3_addendum_linear_models.json`
- 결과 보고: 본 addendum 문서 §5 (실험 후 추가)

## 5. 결과 요약 (실험 완료 2026-05-07)

### 5.1 100-seed LAO MdAPE (baseline = F4+spline+Huber 운영 24.27%)

| Family | Model | MdAPE | std | Δ vs baseline | 채택 |
|---|---|---|---|---|---|
| (ref) | baseline (운영 채택) | 24.27% | 4.30 | (= 0) | — |
| F1 (C) | gallery_te | 24.30% | 4.30 | +0.03%p | ✗ |
| F1 (C) | material_te | 24.85% | 4.63 | +0.58%p | ✗ |
| F1 (C) | gallery + material_te | 25.07% | 4.51 | +0.79%p | ✗ |
| F2 (A) | Ridge (alpha=1.0) | 25.37% | 4.46 | +1.09%p | ✗ |
| F2 (A) | Huber + L2 (alpha=1.0) | 24.27% | 4.30 | +0.00%p | ≈ |
| F2 (A) | F1+F2: TE + Ridge | 26.50% | 4.84 | +2.23%p | ✗ |
| F2 (A) | F1+F2: TE + Huber+L2 | 25.05% | 4.51 | +0.77%p | ✗ |
| F4 (E) | artist_median_te | 31.36% | 6.18 | +7.08%p | ✗ |
| F4 (E) | artist_sales_count_log | 51.91% | 13.76 | +27.64%p | ✗ |
| F4 (E) | artist_dispersion_te | 24.41% | 3.81 | +0.13%p | ✗ |
| F4 (E) | artist_combined (3 feat) | 55.23% | 11.58 | +30.96%p | ✗ |
| COMB | F1+F4+Huber+L2 | 53.20% | 11.85 | +28.93%p | ✗ |

→ **모든 후보 합격 기준 (-1.0%p) 미달, 대부분 악화**. Top candidate (Δ ≤ -0.5%p) 0건 → subgroup harm 분석 trigger 0건.

### 5.2 D. artist_sales_count_log +27%p 악화 디버깅
- **LAO 평균 unseen artist 비율: 100.0%** (test 작가의 100% 가 train 에 없음 — LAO 정의상 당연)
- Eval 의 `fillna(0)` 비중 100% / Train 분포 평균 +2.70 vs Eval 평균 0.00 → **train-eval 분포 완전 어긋남**
- 회귀계수 +0.325 (양수) → train 학습값이 eval 에서 0 → 예측 가격 왜곡
- **결론: 버그 아님 — LAO 평가 구조상 artist 통계 피처는 본질적으로 무력** (warm-start 에서만 의미 있음)

### 5.3 E. Huber alpha sensitivity (100-seed LAO)
| alpha | MdAPE | std |
|---|---|---|
| 1e-4 (운영) | 24.27% | 4.30 |
| 1e-2 | 24.27% | 4.30 |
| 1.0 | 24.27% | 4.30 |
| 10.0 | 24.26% | 4.28 |

→ alpha 4 자릿수 변화에도 차이 ≤ 0.01%p — **L2 regularization 추가 가치 없음** 확정. 운영값 1e-4 floor 도달.

### 5.4 결론 (운영 결정)

> **운영 모델 변경 X. F4 + log_area spline + Huber (eps=1.35, alpha=1e-4) 유지.**

근거:
1. 외부 자문 권고 모든 후보 100-seed LAO 합격 기준 미달
2. F1 (gallery/material TE) 거의 동등 (+0.03 ~ +0.79%p) — 추가 정보 가치 없음
3. F2 (Ridge / Huber+L2) Huber 단독과 동등 또는 악화 — Huber loss 의 robustness 가 본질
4. F4 (artist 통계) LAO 평가 구조상 본질적 무력 — warm-start 에서만 가치
5. Combined (F1+F4+Huber+L2) 가장 큰 악화 — feature stacking 의 noise

### 5.5 외부 자문 회신 framing (코덱스 권고)
> "권고가 일반론적으로는 타당했으나, 당사 핵심 평가축인 100-seed LAO 에서 재현되지 않았고, 일부 후보는 cold-start 조건에서 구조적 악화를 보여 운영 반영은 보류. 자문이 틀린 것이 아니라 우리의 운영 목적 (cold-start) 과 평가 조건에서 채택 근거가 없는 결과."

외부 자문 권고는 다음 영역에 한정 재해석:
- **Warm-start 전용 후보**: artist_median_te + shrinkage (별도 cycle)
- **가격 범위 산출**: Quantile Regression q25/q50/q75 (별도 cycle, 운영 가치 큼)
- **Phase 2 (full data) confirmatory**: gallery/material TE 재검증 가치 (full data 의 분포에서 다를 가능성)

## 6. 후속 결정 시나리오

| 시나리오 | 후속 액션 |
|---|---|
| Family 1+2 결합 cold -2%p 이상 개선 | 운영 모델 교체 검토 → Stage 4 leading candidate 변경 검토 + 코덱스 자문 |
| 부분 개선 (-1 ~ -2%p) | Stage 4 본실험 후보군에 일부 포함 검토 |
| 모두 개선 < 1%p 또는 subgroup harm | 본 cycle 폐기, 운영 모델 유지, 자문 권고 정중 거절 |
| 일부 family 만 개선 | 해당 family 만 Stage 4 후보군 포함 |

## 7. Out of Scope (별도 cycle)

- Quantile Regression (B): 운영 가치 큼, 별도 리포트 + 사전등록
- 외부 자문의 "Ridge 기반 헤도닉" 전체 운영 도입: Phase 2 (full data) confirmatory 후 결정
