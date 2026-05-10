# D3.B: Stacking Meta-learner Cycle (decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: D3 scalar w (commit `fd0f14e`) HOLD_50_50 후속 / advanced blend axis
> **Decision binding**: ✅ YES — 운영 ensemble blend 변경 결정 (D3 scalar w 종결 후 stacking meta-learner 별도 axis).

## 1. Goal

D3 scalar w (1D `w ∈ [0,1]` grid search) 결과 = HOLD_50_50 (1/5 PASS / OOF→fresh 일반화 X). OOF cold_overall에서 w*=0.3이 -0.34pp 개선했지만 fresh 5 seed validation 1개만 PASS / 4 FAIL.

원인 추정: scalar w로는 split variance 흡수 부족 / source / artist / 가격대별 optimal w가 다름.

질문: **stacking meta-learner** (linear regression / GBM / xgboost stacker) on `(cb_pred_log, xgb_pred_log, source)` 위에서 final blend를 학습하면 fresh seed 일반화 성능 향상되는가?

PASS 시: 운영 blend 시스템 → meta-learner 적용 (50/50 ensemble 대체).
FAIL 시: blend axis (scalar + meta-learner 둘 다) 종결 / 50/50 유지.

본 cycle = **stacking meta-learner 단일 axis** (D3 scalar w 후속). N=32 features 그대로 / base model params 변경 X.

## 2. Method

### 2.1 Stacking 설계

**Base predictions** (input features for stacker):
- `cb_oof_log`: CB OOF prediction (log-scale / GroupKFold-5 / N=28376)
- `xgb_oof_log`: XGB OOF prediction (log-scale / 같은 GroupKFold split)
- `source` (categorical): "artsy" / "saatchi" — 분포 차이 흡수

**Optional input (R1 검수 시 결정)**:
- `is_warm`: 0/1 (warm slice indicator)
- `target_market`: "gallery" / "online"
- `cb_xgb_diff`: cb_oof_log − xgb_oof_log (disagreement signal)

**Target**: `y_log = ln(price_krw)` — 운영 target과 동일.

### 2.2 Meta-learner 후보 (R1 검수 후 결정)

**옵션 A (선호)**: **Linear Regression** with source dummy variable
- `y_log = β_cb · cb_oof_log + β_xgb · xgb_oof_log + β_src · source_dummy + intercept`
- 단순 / 해석 가능 / overfitting risk 작음
- effectively learning a per-source weight + intercept

**옵션 B**: **XGBoost stacker** (n_estimators=100 / max_depth=3 / shallow / 등)
- 복잡 interaction 학습 가능 / 단 overfitting risk 큼
- N=28376 OOF on 2-3 features = high data-to-feature ratio / safer

**옵션 C**: **Lasso** (sparse linear / source-conditional)
- weight regularization / source × base interaction 등

선택은 R1 검수 시 / default 옵션 A.

### 2.3 OOF Generation (R1 P1.2 amendment)

`GroupKFold-5(artist_slug)` / default CB + XGB params (`integrated_v3_filtered_tuned_best_params.json` 그대로).

각 fold:
1. CB train on **full cold train fold** (default cb params) → predict on test fold → cb_oof_log[test_idx]
2. XGB train on **full cold train fold** (default xgb params) → predict on test fold → xgb_oof_log[test_idx]

→ D3 scalar w `scripts/d3_blend_search.py:generate_cold_oof` 정합 (CB / XGB 모두 full cold train fold 학습 / warm slice 한정 학습 X).

각 fold OOF prediction을 모아 N=28376 OOF vector 생성.

(D3 scalar w와 동일 OOF generator 재사용 가능)

### 2.4 Meta-learner 옵션 (R1 amendment / 옵션 A 채택)

R1 Q1 답변: 옵션 A (linear regression) 채택. R1: "D3 scalar 일반화 실패 본질 = 비선형 capacity 부족 X / 분포 mismatch / B (XGB stacker)는 overfitting risk only".

**Linear Regression with source dummy**:
```python
X_meta = np.column_stack([
    cb_oof_log,           # CB OOF (log)
    xgb_oof_log,          # XGB OOF (log)
    (source == "artsy").astype(int),  # source dummy (saatchi=baseline)
])
y_meta = y  # = ln(price_krw)

from sklearn.linear_model import LinearRegression
meta = LinearRegression(fit_intercept=True)
meta.fit(X_meta, y_meta)
```

**Features (R1 Q2 amendment / minimal set)**:
- 기본 3개: `cb_oof_log`, `xgb_oof_log`, `source_dummy`
- 선택 1개 (R1 Q2 ok): `cb_xgb_diff = cb_oof_log − xgb_oof_log` (disagreement signal)
- 명시 제외 (R1 Q2): 작품 metadata feature (작품 자체 features 추가는 stacker가 second-stage model로 변질 / 본 cycle = blend refiner only)

### 2.5 Validation (R1 P0 amendment / per-seed re-fit primary endpoint)

`split_seed ∈ {149, 211, 277, 353, 449}` — **새 seeds** (D1.X / D3 / B / N15 / D1.Y 모두 비중복).

**R1 P0 critical fix**: meta-learner는 **각 fresh seed의 80% pool 위에서 재학습** (단일 frozen full-data meta 적용 X / estimand mismatch 회피).

**Primary endpoint procedure (per seed)**:
1. 80/20 split — **`GroupShuffleSplit(test_size=0.20, random_state=seed, groups=artist_slug)`** (R2 P2 amendment / D1 / D3 cold validation 정합 / artist-grouped holdout / row-level train_test_split X)
2. **80% pool 위 GroupKFold-5 OOF generation** (default CB + XGB / D3 scalar w 동일 generator):
   - 각 fold: pool train fold로 CB + XGB 학습 → pool test fold 위 predict → cb_pool_oof, xgb_pool_oof
   - 결과: pool OOF vector (n_pool ≈ 22,700)
3. **Pool OOF에서 meta-learner fit**: `meta_seed = LinearRegression().fit(X_meta_pool_oof, y_pool)`
4. **80% pool로 default CB + XGB final retrain** (full pool 위 / for holdout inference)
5. **20% holdout 위 prediction**:
   - cb_pred_holdout (log) / xgb_pred_holdout (log)
6. Meta features 생성 → `meta_seed.predict(X_meta_holdout)` → final_pred (log) → exp → KRW
7. baseline (50/50): `(cb_pred + xgb_pred)/2` in log → exp
8. Per cell MdAPE / Δ_blend = candidate − baseline

**Secondary endpoint (frozen-meta deployment gate / R2 P1 amendment / non-primary BUT adoption gate)**:
- Meta = LinearRegression on full-data OOF (5-fold full N=28376)
- 같은 fresh seed holdout 위에 frozen meta 적용 / per-seed Δ_blend 산출
- **§3 채택 결정의 secondary gate**: primary가 PASS여도 frozen full-data meta가 fresh seed holdout에서 FAIL이면 운영 채택 X (shipped-artifact non-regression 보장)
- 운영 deploy artifact = frozen full-data meta (per-seed refit은 절차 검증용 / 운영 inference 단계 X)

**Compute estimate**: per-seed pool OOF generation = 5-fold CB+XGB train ≈ 80s + meta fit + final retrain + predict ≈ ~3분/seed × 5 seed = ~15분 wall (D3 scalar w 정합).

### 2.6 Per-seed verdict (R1 P1.1 amendment / D1/B 정합)

3-tier (R1 P1.1: 이전 plan은 PASS의 G1과 INCONCLUSIVE 정의 모순 발생 / fix):

- **PASS**:
  - ✅ Δ_cold_overall ≤ 0pp (strict)
  - ✅ G2 (Δ_cold_artsy ≤ +0.3pp)
  - ✅ G3 (Δ_cold_saatchi ≤ +0.3pp)
- **INCONCLUSIVE**:
  - Δ_cold_overall ∈ (0, +0.3]pp (G1 미달 BUT 작은 regression)
  - ✅ G2 (≤ +0.3pp) ✅ G3 (≤ +0.3pp)
- **FAIL**:
  - Δ_cold_overall > +0.3pp OR G2 / G3 violation

### 2.7 Multi-seed aggregate (5 seeds / D3 정합)

| 분포 | Aggregate |
|---|---|
| PASS × 5 | PASS |
| PASS × 4 + INCONCLUSIVE × 1 | PASS_with_caveat |
| FAIL × 3 이상 | FAIL |
| 기타 | INCONCLUSIVE |

## 3. Decision Criterion (R2 P1 amendment / dual-gate)

**Primary endpoint** (per-seed refit / decision-binding) **AND** **Secondary endpoint** (frozen full-data meta / shipped-artifact 정합 gate) 둘 다 만족 시 채택.

| Primary aggregate | Secondary verdict | Decision |
|---|---|---|
| PASS | not FAIL | **운영 blend 변경 권고** (50/50 → frozen full-data meta artifact deploy) |
| PASS | FAIL | INCONCLUSIVE — 운영 적용 보류 / per-seed refit과 frozen artifact gap 분석 |
| PASS_with_caveat | not FAIL | **canary deployment** (PR-WARM-B Stage 4 framework) |
| FAIL | any | **50/50 유지** / blend axis 종결 (R1 Q6: linear-per-seed-refit fail 시 stacking axis terminate) |
| INCONCLUSIVE | any | multi-seed 확장 또는 다른 axis 별도 검토 |

**근거 (R2 P1)**: per-seed refit은 *procedure validity* 검증. 단 운영 deploy 대상 = frozen full-data meta artifact. 둘 사이 gap이 큰 경우 (procedure는 PASS인데 frozen artifact는 FAIL) 채택 보류 — frozen artifact deploy 후 traffic 영향이 per-seed refit과 다를 수 있으므로 non-regression gate 필수.

## 4. Output

- `docs/d3_b_stacking_metalearner_prereg_20260510.md` (본 문서)
- `docs/d3_b_stacking_metalearner_results_20260510.md`
- `scripts/d3_b_stacking_search.py` (OOF reuse from `d3_blend_search.py` + meta-learner training + validation)
- `data/d3_b_holdout_20260510/seed{149,211,277,353,449}_holdout_indices.json`
- (gitignored) `model_test_results/d3_b_stacker.pkl` (sklearn stacker / 또는 json coefficients)
- (gitignored) `model_test_results/d3_b_stacking_results.json`

## 5. Out-of-scope

- ❌ Base model params 변경 (D1 / D1.X / D1.Y 별도)
- ❌ Feature 변경 (N=32 그대로)
- ❌ Source-conditional separate base models (PR1 별도)
- ❌ Warm path blend (XGB only / 변경 X)

## 6. 한계 / Risk

- **Linear meta-learner is essentially scalar w generalization**: source dummy 추가 시 per-source w / 결국 D3 scalar w + per-source 보정. Base model이 동일하면 marginal gain 작을 수 있음.
- **Meta-learner overfitting OOF**: OOF GroupKFold 분포와 fresh train_test_split 분포 mismatch (D3 scalar 같은 이슈) → 일반화 위험.
- **Compute light**: ~30분 wall (5-fold OOF + meta train + 5-seed validation).
- **D1.X retuned base + meta-learner 결합 cycle은 별도** (D1+D3.B joint).

## 7. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전 (2026-05-10)** | **NEEDS FIX (P0 + P1×2)** | P0: per-seed re-fit / P1.1: verdict logic / P1.2: XGB cold full-fold |
| **R2 사전 (post-amendment)** | (예정) | amendment 정합 검증 |
| R3 사후 | (예정) | 결과 검수 / 채택 결정 |

**R1 amendment 반영 항목**:
1. P0 fix (§2.5): per-seed primary endpoint = 80% pool 위 OOF generation + pool에서 meta fit + 그 seed의 holdout 위 적용 / frozen full-data meta는 secondary record-only endpoint
2. P1.1 fix (§2.6): PASS / INCONCLUSIVE / FAIL 정의 정합 (G1 contradiction 해소)
3. P1.2 fix (§2.3): XGB는 full cold train fold 학습 (이전 prereg 잘못 명시 "warm slice만 학습" 정정 / D3 generator 정합)
4. Q1 답변 (§2.4): 옵션 A (linear regression) 채택 / 옵션 B는 배제
5. Q2 답변 (§2.4): features 최소 3개 + cb_xgb_diff 선택 / 작품 metadata 추가 X (blend refiner scope 유지)
6. Q6 답변: 본 cycle 기대값 modest / linear-per-seed-refit FAIL 시 blend axis 종결 (XGB stacker로 escalation X)
7. Q7 답변: PASS 시 운영 통합 PR-WARM-B 대비 복잡 / 별도 deploy PR 권고
8. Q8 답변: D1+D3.B 결합은 별도 후속 cycle

## 8. 결론

D3.B = **stacking meta-learner cycle** (D3 scalar w HOLD 후속 / advanced blend). Linear regression (옵션 A) 우선 / source dummy 추가하여 per-source weight 효과. OOF 위 학습 / fresh 5 seed validation. PASS 시 운영 blend 변경 / FAIL 시 blend axis 종결.
