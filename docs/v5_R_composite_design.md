# R (Composite Retrieval Prior) 정의 — 사전 Design

> **상태**: 사전 design (DRAFT, 2026-05-05). V4 cycle data PoC 후 finalize.
>
> **기원**: 코덱스 9차 자문 (2026-05-05) — V5 image diagnostic pilot 결과 raw image prior 단독 fail. Image 신호를 medium/size 와 결합한 composite prior 가 V5 cycle 의 새 후보.
>
> **목적**: V5 cycle Day 3 시작 시 즉시 구현 가능하도록 R 의 mathematical/operational definition 사전 확정.

## 1. 배경 — PILOT 진단 후 R 신설 이유

V4 cycle data PILOT (2026-05-05) 결과:
- Step 2 image-only KNN: cold-start MdAPE -3.01pp (개선 — 약함)
- Step 4 Memorization audit: retention **-12.4%** (CRITICAL — 모든 gain 이 same-artist 의존)
- Step 5 Cluster variance: 41.4% < 50% (FAIL)

**해석 (코덱스 9차 자문)**:
> "Step 2 의 -3.01pp 는 visual prior 가 아니라 image 가 잡는 medium/format/scale/era proxy 우회 포착"

→ Image 단독 X. 단 medium/size 같은 명시적 변수와 결합 시 image 가 추가 신호 가능?

R 의 핵심 가설:
- **medium/size 가 가격 prior 의 1차 신호**
- **image 는 same-medium 내 미세 분류 (style, technique)** 추가 신호
- 결합 retrieval 이 raw image 보다 robust + structured-only 보다 incremental gain

## 2. R 의 Mathematical Definition

### 2.1 Notation
- Test work `q`: target work for prediction
- Train pool `T`: training set (artist-level LAO 분리 후, all from other artists)
- Embedding `e(·) ∈ ℝ^768`: DINOv2-base CLS token
- Medium `m(·) ∈ {oil, acrylic, paper, sculpture, mixed, other, ...}`: medium_category (V4 schema)
- Size `s(·) ∈ ℝ^+`: `area_cm2` (or `ho` — TBD)

### 2.2 Same-medium Hard Filter
Test work `q` 의 retrieval pool `T_m`:
```
T_m(q) = {t ∈ T : m(t) == m(q)}
```

만약 `|T_m(q)| < k_min`:
- Fallback A (proposed): expand to medium hierarchy (`medium_l1`, e.g. painting/works-on-paper/sculpture)
- Fallback B: drop the medium filter (rank all T by composite distance)
- 결정 시점: V4 PoC 결과 + 본 데이터 분포 후 fix

### 2.3 Composite Distance (image + size)

Image distance:
```
d_img(q, t) = 1 - cosine(e(q), e(t))
```

Size distance (log scale, normalized):
```
d_size(q, t) = |log(s(q)) - log(s(t))| / σ_log_size_train
```

Composite distance:
```
d_R(q, t) = (1 - λ) · d_img(q, t) + λ · d_size(q, t)
```

Hyperparameter `λ ∈ [0, 1]`:
- `λ = 0`: image-only (PILOT 했음)
- `λ = 0.5`: equal weight
- `λ = 1`: size-only (size+medium baseline)
- 추천 시작값: `λ = 0.3` (image 우세지만 size 보정)

### 2.4 KNN Prediction
Top-k NN by `d_R`:
```
N_k(q) = top-k nearest neighbors in T_m(q) by d_R
predicted_log_price(q) = median{log(price(t)) : t ∈ N_k(q)}
```

`k = 10` (PILOT 와 동일, robust)

## 3. Comparison Conditions (코덱스 권고: 3-way compressed re-check)

V5 cycle Day 3 에서 비교할 3 가지:

| Condition | Filter | Ranker | 의미 |
|---|---|---|---|
| **(A) Structured-only** | same-medium | size proximity | image 미사용 baseline (R 의 floor) |
| **(B) Composite** | same-medium | image (or composite) | R 본체 |
| **(C) Image-only** | none | image | PILOT 재현 (image 한계 baseline) |

Image incremental gain:
```
ΔMdAPE_image = MdAPE(B) - MdAPE(A)
```

R Pass gate (사전등록):
- ΔMdAPE_image ≤ -0.3pp (image 가 structured-only 대비 0.3pp+ 추가 gain)
- 미충족 시 → image cut, structured-only 도입 검토

## 4. Retrieval Statistics Features (Day 5 통합 시)

코덱스 V5 plan §10 권고 retrieval features (PILOT 에서 검증 보류 됐던 항목):

```python
# 각 test work 에 대해
NN_median_log_price = median{log(price(t)) for t in N_k(q)}
NN_iqr_log_price = q75 - q25 of {log(price(t))}
NN_distance_weighted_avg = sum(w_t * log(price(t))) / sum(w_t)
                           where w_t = exp(-d_R(q, t))
NN_local_density = mean{d_R(q, t) for t in N_k(q)}  # 작을수록 dense
NN_same_medium_share = (already enforced by filter, =1.0 in R)
```

Baseline (CB-32) 에 5-7개 추가 features 로 통합. 대신 PCA-32 raw embedding feature 직접 통합은 PILOT 결과로 X.

## 5. 논의 — 미정 사항 (PoC 후 결정)

### 5.1 Size 정의: `area_cm2` vs `ho`
- `area_cm2`: continuous, log-normal 분포
- `ho` (호): 한국 미술 시장 표준, discrete 1-150
- **추천**: `area_cm2` 의 log scale (continuous, smooth distance)
- Backup: `ho` if `area_cm2` 분포가 너무 분산

### 5.2 Medium 정의: `medium_category` vs raw `medium`
- `medium_category`: 6-8 buckets (V4 schema)
- raw `medium`: 자유 텍스트 (e.g. "Oil and acrylic on linen with sand")
- **추천**: `medium_category` (hard filter), 향후 fallback 으로 raw text similarity 도입 가능

### 5.3 Aspect ratio 추가 여부
- `aspect_ratio` 도 retrieval feature 후보
- Trade-off: 더 정밀한 매칭 vs filter 너무 엄격 (sparse pool)
- **추천**: 1차에서 제외, 결과 보고 추가 검토

### 5.4 λ 결정 protocol
- V4 PoC: λ ∈ {0, 0.1, 0.3, 0.5, 0.7, 1.0} grid search (선검증용)
- V5 정식: 사전등록 시 fixed (e.g. λ=0.3)
- λ 도 hyperparameter tuning 의 대상이지만 fairness 우려로 사전 고정

### 5.5 Source 처리
- Saatchi 학습 데이터 21K 는 image embedding 없음 (Artsy 만 7,626)
- R 은 **Artsy-only** 도입이 자연스러움
- Saatchi: V4 결정대로 v4 컬럼 X (별도 정책)

## 6. V5 cycle 적용 시점

| Cycle Day | 작업 | 본 design 활용 |
|---|---|---|
| Day 1 | LAO split + image embed 재계산 | — (eval framework only) |
| Day 2 | A compressed re-check | — (PILOT 재현, image-only) |
| **Day 3** | **R 진단 (3-way compressed)** | **본 design 의 (A)/(B)/(C) 비교** |
| Day 4 | R Memorization audit | (B) 기준 same-artist allow vs forbid |
| Day 5 | R retrieval features 통합 | §4 features → baseline + GBM |
| Day 6-7 | R gate 결정 | image incremental ≤ -0.3pp 평가 |

## 7. 운영 contract 영향 (장기)

R 도입 시 서빙 contract 변경 필요:
- `medium_category` (이미 있음)
- `area_cm2` (이미 있음)
- DINOv2 embedding (신규 — image inference 추가)

Image embedding 시점:
- 학습 시: pre-compute + cache (현재 구조 OK)
- 서빙 시: 새 작품마다 GPU inference (지연 추가 — 본 PR 머지 시 ETA 측정 필요)

대안: structured-only retrieval 만 도입 → image inference 불필요, 운영 단순.
**기준**: image incremental gain 이 0.3pp+ 인 동시에 운영 비용 정당화 가능한지.

## 8. Pilot 산출물 (V4 cycle data)

본 design 의 PoC 는 V4 cycle data (Artsy 7,276) 로 진행 — `scripts/v5_composite_retrieval_pilot.py`.

PoC 결과는 V5 시작 시 design 의 fix 항목 (λ, fallback rule 등) 정보로 활용. **Decision-binding X**.

### PoC 결과 (2026-05-05)

3 seeds (42/123/7777), λ grid [0.0, 0.1, 0.3, 0.5, 0.7, 1.0], k=10:

| Condition | MdAPE (mean ± std) | vs Naive |
|---|---:|---:|
| Naive baseline | 76.06 ± 1.84 | — |
| (C) Image-only (PILOT 재현) | 75.82 ± 0.66 | -0.24 (무가치) |
| **(A) Structured-only** (medium + size NN) | **53.76 ± 3.71** | **-22.30** ✅ |
| (B) Composite λ=0.1 | 56.45 ± 1.74 | -19.61 |
| (B) Composite λ=0.3 | 54.32 ± 2.99 | -21.74 |
| (B) Composite all λ | 53.76 ~ 77.07 | A 와 같거나 나쁨 |

**Image incremental gain (vs A)** — **모든 λ 음수** (-0.55 ~ -23.31pp).
어떤 seed 에서도 +0.3pp gate 통과 X.

### Verdict (PoC 기준, decision-binding X)

> **Image cut. Structured-only retrieval (A) 가 충분.** R 본 정의 (composite) 는 V4 data 에서 image incremental 미통과.

→ V5 cycle 시 본 데이터에서 재검증. 본 데이터에서도 동일 결과면 **R 제외, S 신설**.

## 9. S (Structured-only Retrieval Prior) — 신설 가능성

PoC 결과로 부상한 새 후보 — **R 의 (A) 단독 추출**:

### Definition
- Filter: same-medium hard filter
- Distance: `d_size(q, t) = |log(area_q) - log(area_t)| / σ_log_area`
- Top-k NN by `d_size` within same medium
- Predict: `median{log(price(t)) : t ∈ N_k}`

### Pass Gate (R 와 동일하나 image incremental 항목 X)
- Cold-start mean ΔMdAPE ≤ -max(0.8pp, baseline의 3%)
- 3/3 seeds 같은 방향
- Seed std ≤ 0.6pp
- 다른 segment 악화 ≤ +1.0pp
- **Memorization retention** ≥ 50% (R 와 동일)

### V5 cycle 시 처리
- **본 데이터 도착 시 R PoC (3-way compressed re-check) 실행**
- R image incremental 통과 → R 진행
- R image incremental 미통과 → **S 로 fallback** (코덱스 9차 자문 권고: "image 컷, structured 단독 도입 검토")

## References

- 코덱스 9차 자문 (2026-05-05): R 신설 권고
- V5 image diagnostic pilot (`model_test_results/v5_image_diagnostic_pilot.json`): A 강등 근거
- V5 cycle plan §4 Week 1 (`docs/v5_cycle_plan_20260504.md`): Day 3 3-way compressed re-check
- V5 사전등록 §1, §5 (`docs/v5_cycle_사전등록_초안.md`): R Hypothesis + Pass gate
