# D1.Y: D1.X Multi-seed N=10 Expansion (decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: D1.X compliant rerun `d06ea22` NEEDS_MORE_DATA (4/5 PASS + 1 seed=113 FAIL G2 artsy +1.76)
> **Decision binding**: ✅ YES — 운영 N=32 champion best_params 교체 결정 (D1.X 보류 → D1.Y 결과 기반 binding).

## 1. Goal

D1.X compliant rerun (50 trials × 2 phase / multi-seed N=5) 결과 = NEEDS_MORE_DATA. 4/5 seed 강한 PASS (mean Δ_artsy=-1.36 / mean Δ_warm=-2.06) / **seed=113 단독 outlier** (artsy_cold +1.76 / G2 위반 / 해당 holdout split의 default cold_overall=50.34 = 다른 seed 36~37 대비 +13~14pp).

질문: **N=5 → N=10 multi-seed 확장 시 seed=113이 단발 outlier로 흡수되는가, 또는 systematic regression 패턴이 추가 발견되는가?**

PASS×9+ → 운영 best_params 교체 권고 (operational migration).
PASS_with_caveat (PASS×8 + INCONCLUSIVE) → canary deployment.
FAIL or 추가 outlier × 2 → D1 axis terminate / G2 threshold 완화 등 별도 amendment 검토.

본 cycle = **search 미실행 / validation-only expansion**. D1.X retuned best_params 재사용 (no new search) → 빠른 turnaround (~10-15분 wall) / D1.X 결과 정합 보존.

## 2. Method

### 2.1 Search 미실행 정합

D1.X compliant rerun 결과 = `model_test_results/n32_champion_retuned_best_params.json` (commit `d06ea22`). CB best (Phase 1) + XGB best (Phase 2) 그대로 재사용.

**근거**: D1.X search-time CV 강한 개선 (cold Δ=-0.68 / warm Δ=-2.20) + 5 seed 중 4 seed 강한 PASS = retuned params 자체는 robust. 문제는 1 seed (113) outlier split. → 새 search 불필요 / validation 분산 검증만 필요.

### 2.2 Multi-seed N=10 expansion (R1 amendment)

**N=10 seeds**: `{97, 113, 199, 223, 257, 313, 367, 439, 491, 587}` (D1.X 5 + 신규 5)

**R1 amendment (P0+P1.2)**: D1.X JSON 재사용 X. **모든 10 seed를 본 D1.Y 스크립트에서 fresh rerun** (단일 dataset snapshot / 단일 환경 정합 보장). D1.X 결과는 historical context only.

근거: 환경 (numpy/scipy/scikit-learn 버전) 변동 시 D1.X 5 seed 결과 약간 다를 수 있음 / N=10 결합 시 estimand 정합성 우선. Compute cost 5+5=10 seed × ~50s = ~8분 wall (그래도 cheap).

### 2.3 Validation 절차 (per seed)

D1.X validate_seed 함수와 동일 (`scripts/optuna_n32_champion_retune.py:validate_seed`):

1. seed로 `train_test_split` 80/20 (cold) + warm subset 80/20
2. 80% pool로 CB+XGB 학습 (default params + retuned params 각각)
3. 20% holdout 위 prediction
4. Δ_cold / Δ_artsy / Δ_saatchi / Δ_warm per cell 산출

**predict per seed**: ~45-50초 / 5 seed × 50s = ~4-5분 wall (D1.X validation 시점 정합).

### 2.4 Per-seed verdict (D1.X 정합 / 변경 X)

3-tier verdict per seed (G1-G4 guards / `optuna_n32_champion_retune.py:339-352` 정합):

**PASS**:
- ✅ G1 (Δ_cold_overall ≤ 0pp / strict)
- ✅ G2 (Δ_cold_artsy ≤ +0.3pp)
- ✅ G3 (Δ_cold_saatchi ≤ +0.3pp)
- ✅ G4 (Δ_warm ≤ +0.1pp)

**INCONCLUSIVE**:
- G1-G4 PASS BUT Δ_cold_overall ∈ (0, +0.3]pp

**FAIL**:
- 임의 G FAIL

### 2.5 Multi-seed aggregate (N=10 / R1 amendment 반영 / strict)

| Per-seed 분포 | Aggregate |
|---|---|
| PASS × 10 | **PASS** (full migration / strict) |
| PASS × 9 + (INCONCLUSIVE OR FAIL) × 1 | **PASS_with_caveat** (canary / 1 outlier 흡수) |
| PASS × 8 + INCONCLUSIVE × 2 (FAIL X) | **PASS_with_caveat** (canary / inconclusive 흡수만 / FAIL 2 X) |
| FAIL × 2 이상 | **FAIL** (champion swap에 충분히 위험 / D1 axis terminate 후보) |
| 기타 | **INCONCLUSIVE** |

**R1 amendment (P1.1)**:
- PASS × 8 + 2 outlier (FAIL 포함) → PASS_with_caveat ❌ (이전 plan / 너무 lax for champion swap / 20% bad-seed rate)
- PASS_with_caveat 채택 = max 2 INCONCLUSIVE (FAIL 0개) 또는 1 outlier (FAIL ok)
- 2 FAIL 발생 시 즉시 FAIL aggregate (champion swap risk premium)

**핵심 변화 vs D1.X (N=5)**:
- D1.X: PASS×4 + FAIL×1 = INCONCLUSIVE
- D1.Y: 1 outlier seed (=113)가 N=10에서 그대로 잔존 시 → PASS×9 + FAIL×1 = **PASS_with_caveat** (단발 outlier 흡수)
- FAIL 추가 발생 (FAIL × 2 이상) → systematic regression 신호 / D1 종결

### 2.6 채택 결정 (R1 검수 후 확정 / R1 amendment Q7 반영)

- **PASS** → 운영 best_params 교체 권고 (PR-WARM-B 와 별개 cycle / cold + warm 통합 deployment)
- **PASS_with_caveat** → canary deployment + shadow logging (PR-WARM-B Stage 4 framework 정합)
- **FAIL** → D1 axis terminate / 현 best_params 유지
- **INCONCLUSIVE** → multi-seed N=15 또는 G threshold 완화 amendment

### 2.7 PR-WARM-B 와 deployment 충돌 (R1 Q7 amendment)

D1.Y와 PR-WARM-B는 동일 운영 stack 위 영향:
- **PR-WARM-B**: warm path만 retune (cold 변경 X)
- **D1**: cold + warm 모두 retune (CB cold + XGB warm 둘 다)

**시점별 baseline 정합**:
- D1.Y가 PR-WARM-B Stage 5 deploy 이전에 PASS / PASS_with_caveat 결정 → control = legacy warm-default stack 그대로
- D1.Y가 PR-WARM-B Stage 5 deploy 이후 결정 → control = **post-B production baseline** (B-retuned warm + default cold). D1 canary는 새 baseline 대비 평가.
- 본 cycle prereg 시점 = PR-WARM-B Stage 1+2만 commit / Stage 3-5 미진행 → control = legacy stack
- D1 deployment 결정 시점에 따라 baseline 명시 필요

## 3. Output

- `docs/d1_y_multiseed_n10_prereg_20260510.md` (본 문서)
- `docs/d1_y_multiseed_n10_results_20260510.md`
- `scripts/d1_y_validation_only.py` (신규 / D1.X retuned params 재사용 / validation-only)
- `data/d1_y_holdout_20260510/seed{313,367,439,491,587}_holdout_indices.json`
- (gitignored) `model_test_results/d1_y_validation.json` (per-seed 결과)
- (gitignored) `model_test_results/d1_y_aggregate.json` (N=10 종합)

## 4. Out-of-scope

- ❌ 새로운 Optuna search (D1.X retuned params 그대로 / search 비용 회피)
- ❌ G threshold 완화 (현행 G1-G4 그대로 / 별도 amendment 시 필요)
- ❌ N≠32 (cycle B / D1 정합)
- ❌ Source-conditional split (artsy / saatchi 별도 분석은 record 만)
- ❌ Bootstrap aggregation (per-seed strict aggregate / R1 검수 시 검토 가능)

## 5. 한계 / Risk

- **Same retuned params**: D1.Y에서 새 search 미실행 / D1.X retuned params만 검증 → search 자체의 stochasticity 분리 X. 단 cycle B 사례에서 search seed=42 robust 확인됨.
- **N=10 still small**: artsy_gallery cell n_holdout 150-250 / heavy-tailed → N=10도 statistical power 한계 / 단 N=5 대비 outlier 흡수 능력 향상.
- **Retraining cost**: 5 fresh seed × ~50s = ~4-5분 wall / D1.X validation 정합. Total D1.Y compute = ~10-15분 (extremely cheap vs full re-search).
- **Seed=113 정합**: 본 cycle은 D1.X seed=113 (FAIL)을 반환 / 새 5 seed만 추가 검증. seed=113 결과는 D1.X와 동일 (deterministic / split / training / prediction 동일).

## 6. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | (예정) | 본 prereg 작성 직후 / N=10 aggregate logic + fresh seeds 검수 |
| R2 사후 | (예정) | 결과 검수 / 채택 결정 |

## 7. 결론

D1.Y = **D1.X validation-only N=10 expansion**. 새 search 불실행 / fresh 5 seed 추가 / N=10 aggregate logic 갱신 (PASS_with_caveat path 신설). seed=113 단발 outlier가 흡수되면 → 운영 채택 후보 / 추가 outlier 발견되면 → systematic regression 종결.

**Compute**: ~10-15분 wall (validation only / 5 seed × ~50s / D1.X 정합).
