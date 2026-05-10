# D1.Arch: Architecture Change Cycle — LightGBM Cold Replacement (R1 amendment / decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: VFR (commit `f48f67b`) framework reform abandon / 16 cycles 누적 / 새 architecture axis 진입
> **Decision binding**: ✅ YES — LightGBM **cold-only** replacement 채택 결정 (vs default unified CB cold)
> **R1 amendment 반영** (codex P0 + P1×2):
> - P0 fix: **cold-only test** / warm은 default XGB freeze (B winner와 conflict 회피)
> - P1.1 fix: FAIL 해석 narrow ("default LGBM insufficient") — tuned LGBM도 fail 시만 architecture-independent confirmed
> - P1.2 fix: full migration cap → **best outcome = ADOPT_lgbm_canary 또는 PROMOTE_TO_TUNING_AND_CANARY** (단일 cycle full migration X)

## 1. Goal

본 세션 누적 결과:
- **B (warm-only XGB retune)**: 5/5 PASS / unique ADOPT (Stage 1+2 commit / Stage 3-5 pending)
- **D1 cold axis 5 cycles**: 모두 fail (HP retune / source-split / threshold relax / framework reform 모두 abandon)
- **VFR analysis** (commit f48f67b): **Cold path effect는 statistically unstable** (CV 5.38-6.93 / cycle별 mean -1.87 → +0.22 sampling lottery) / 본 framework 정확 작동 입증

**핵심 hypothesis (R1 amendment / cold-only narrow scope)**:
- (b) **Cold CB algorithm-specific issue** — 다른 cold architecture (LGBM)은 heavy-tail / small-cell에 더 robust / PASS 가능
- 본 cycle은 (b) 검증 / cold-only architecture probe / **full-stack challenger 아님 (codex Q7)**

본 cycle = **LightGBM cold-only replacement / warm freeze (default XGB)**:

질문: LGBM cold replace CB (default params)가 default unified CB cold 대비 strict per-seed framework PASS 가능한가? **Warm path는 default XGB freeze (B winner와 orthogonal 보존)**.

PASS 시 → cold architecture에 promise / **PROMOTE_TO_TUNING_AND_CANARY** (LGBM HP retune 후속 + canary deployment / full migration은 후속).
INCONCLUSIVE / FAIL 시 → **default LGBM insufficient** (R1 P1.1 narrow / "architecture-independent" overclaim 회피) → 후속 tuned LGBM cycle 또는 architecture axis abandon 검토.

**Important** (R1 codex Q3 / P0): 본 cycle은 PR-WARM-B (B winner)와 **conflict 없음** (cold-only / warm path 변경 X / B-retuned warm 그대로 deploy 가능).

## 2. Method

### 2.1 LightGBM 사용 정합

LightGBM 4.6.0 사용 (Python LightGBM library / 환경 확인 완료):
- Algorithm: gradient boosting / leaf-wise tree growth (CB / XGB는 level-wise / depth-wise)
- Categorical feature handling: native (CatBoost와 비슷)
- Speed: typically 2-5× XGB / 1.5-3× CB

**Drop-in 정합**:
- N=32 features 그대로 (CB_FEATURES_BASE)
- Categorical features (CAT_FEATURES 6개) native handling
- Train interface: `lgb.train(params, dtrain, num_boost_round)` / D1.Y XGB 정합

### 2.2 LGBM 학습 정합 (default params)

본 cycle은 **default LGBM params** / HP search 미실행 (D1.SC 정합 / data partitioning + architecture 단독 효과 측정):

```python
lgb_params = {
    "objective": "regression",
    "metric": "l2",
    "num_leaves": 31,        # default / depth ≈ 5
    "learning_rate": 0.05,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq": 5,
    "verbose": -1,
    "seed": 42,
}
num_boost_round = 1000
```

**근거**: D1.X / D1.Y / D1-extended 모두 retuned best_params로 fail. Default params로 LGBM 단독 architecture 효과만 측정. PASS 시 → architecture matters / LGBM HP retune은 별도 cycle.

### 2.3 Fresh seeds (R1 amendment 정합 / N=10)

`split_seed ∈ {1153, 1171, 1187, 1201, 1217, 1231, 1249, 1259, 1277, 1289}` — 모두 prime / 이전 cycle 비중복:

| Seed | D1.X | D1.Y | B | D3 | D3.B | D1-ext | D1.SC | 비고 |
|---|---|---|---|---|---|---|---|---|
| 1153-1289 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 모두 fresh |

### 2.4 Validation 절차 (R1 P0 amendment / cold-only)

각 seed × 80/20 split (cold: GroupShuffleSplit / warm: row split):

**Candidate (LGBM cold + freeze warm)**:
- LGBM cold = LGBM 학습 on 80% cold pool (default LGBM params)
- Warm = **default XGB freeze** (R1 P0 / cold-only 측정 / B와 orthogonal)
- Cold inference: LGBM cold (CB 대체)
- Warm inference: default XGB warm (변경 X)

**Baseline (default CB cold + freeze warm)**:
- CB cold = default CB on 80% cold pool
- Warm = default XGB (candidate와 동일)
- Cold inference: CB cold
- Warm inference: default XGB warm

**Per-cell MdAPE (cold만 측정 / warm Δ=0 by design)**:
- cold_overall / cold_artsy / cold_saatchi
- Δ_cell = candidate − baseline (warm Δ는 0 / orthogonal 보존)

### 2.5 Strict Primary endpoint (D1.Y framework / R1 P1.1)

Per-seed verdict (G1-G4):
- PASS: G1 (≤0) + G2 (artsy ≤+0.3) + G3 (saatchi ≤+0.3) + G4 (warm ≤+0.1)
- INCONCLUSIVE: Δ_cold_overall ∈ (0, +0.3] + G2/G3/G4 PASS
- FAIL: 임의 G FAIL

N=10 aggregate (D1.Y R1 P1.1):
- PASS × 10 → PASS
- PASS × 9 + 1 outlier → PASS_with_caveat
- PASS × 8 + INCONCLUSIVE × 2 (FAIL=0) → PASS_with_caveat
- FAIL × 2 이상 → FAIL
- 기타 → INCONCLUSIVE

### 2.6 Bootstrap CI Secondary corroboration (VFR 결과 정합)

VFR 결과 = `1_strict_per_seed` recommendation / bootstrap secondary corroboration. 본 cycle:
- N=10 paired percentile bootstrap on mean Δ per cell
- Hierarchical: cold_overall primary
- Not binding alone (D1-extended / D1.SC 정합)

### 2.7 Combined decision (R1 P1.2 amendment / cap at canary)

Strict primary가 binding (VFR 결과 정합) / **R1 P1.2: full migration cap / 단일 cycle ADOPT_full X**:

| Strict Primary | Bootstrap | Combined (R1 amendment) |
|---|---|---|
| PASS | bootstrap_PASS | **PROMOTE_TO_TUNING_AND_CANARY** (LGBM HP retune 후속 + canary deployment / full migration은 두 번째 cycle 후) |
| PASS | bootstrap_INC/FAIL | **ADOPT_lgbm_canary** (보수적 / shadow first) |
| PASS_with_caveat | bootstrap_PASS | **ADOPT_lgbm_canary** |
| INCONCLUSIVE | any | **NEEDS_MORE_DATA / 후속 LGBM HP retune cycle** |
| FAIL | any | **default LGBM insufficient** (R1 P1.1 narrow) — 후속 tuned LGBM cycle 또는 architecture axis abandon 검토 |

**핵심 (R1 P1.1 / P1.2 amendment)**:
- FAIL ≠ "architecture-independent confirmed" / "default LGBM insufficient" 만 (narrow interpretation)
- "Architecture-independent" 결론은 **tuned LGBM도 fail 시만** (별도 cycle)
- Full migration은 두 번째 cycle (tuned + implementation validation) 후 결정 / 단일 cycle PASS만으로 X

## 3. PR-WARM-B와 interaction (R1 P0 amendment / orthogonal 보존)

**R1 P0 amendment**: D1.Arch = **cold-only** replacement / warm = default XGB freeze.

→ PR-WARM-B (B-retuned XGB warm)와 **orthogonal / conflict 없음**:
- D1.Arch ADOPT_lgbm_canary 시 → LGBM cold + B-retuned warm XGB (Stage 5 후) 결합 가능
- D1.Arch FAIL 시 → cold default 그대로 / PR-WARM-B 단독 deploy
- 둘은 분리된 inference path (cold by LGBM / warm by XGB) — D1.SC 정합

**Codex Q3 답변 정합**: PR-WARM-B priority 보존 / D1.Arch single pass로 B abort X.

## 4. Output

- `docs/d1_arch_lightgbm_replacement_prereg_20260510.md` (본 문서)
- `docs/d1_arch_lightgbm_replacement_results_20260510.md`
- `scripts/d1_arch_lgbm_validation.py`
- `data/d1_arch_holdout_20260510/seed{1153-1289}_holdout_indices.json`
- (gitignored) `model_test_results/d1_arch_results.json`

## 5. Out-of-scope

- ❌ LGBM HP search (default params 그대로 / Optuna 미실행 / 후속 cycle 후보)
- ❌ Other architectures (Bayesian / NN / Quantile regression / 별도 cycles)
- ❌ Calibration 적용 (raw output / D1.SC 정합)
- ❌ Source-conditional split (D1.SC fail / 본 cycle scope 외)
- ❌ Ensemble of CB+XGB+LGBM (별도 cycle)

## 6. 한계 / Risk

- **Default LGBM params**: HP not optimized for 본 dataset / suboptimal possible / 단 default가 fail 시 architecture 자체 효과 약함 신호
- **Cold path noise fundamental 가정 검증**: VFR 결과 정합 / 본 cycle FAIL = **default LGBM insufficient only** (R1 P1.1 narrow / architecture-independent 결론은 tuned LGBM도 fail 시 reserve)
- **Compute light**: ~5-10분 wall (LGBM 빠름 / 10 seed × ~30-60s)
- **PR-WARM-B orthogonal** (R1 P0): D1.Arch는 cold-only / warm freeze / B winner와 conflict 없음 / D1.Arch ADOPT_canary + B Stage 5 결합 deploy 가능
- **Codex Q7 정합**: D1 abandon / B + source-conditional 우선 / 본 cycle은 architecture axis 추가 / source-conditional axis 종결 후 다음 axis

## 7. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전** | **NEEDS FIX** | P0 (cold-only / warm freeze) + P1.1 (FAIL 해석 narrow) + P1.2 (cap at canary / full migration X) |
| **R2 사전 (post-amendment)** | (예정) | amendment 정합 검증 |
| R3 사후 | (예정) | 결과 검수 / 채택 결정 |

**R1 amendment 반영 항목**:
1. **P0 fix**: D1.Arch = cold-only LGBM replacement / warm = default XGB freeze (PR-WARM-B와 orthogonal)
2. **P1.1 fix**: FAIL = "default LGBM insufficient" only / "architecture-independent confirmed"는 tuned LGBM도 fail 시 reserve
3. **P1.2 fix**: best outcome = PROMOTE_TO_TUNING_AND_CANARY 또는 ADOPT_lgbm_canary / 단일 cycle full migration X
4. Q3 답변: PR-WARM-B priority 보존 / D1.Arch single pass로 B abort X
5. Q5 답변: serving cost 높음 / 단일 cycle PASS로 full migration X (cap at canary)
6. Q7 답변: cold architecture probe / full-stack challenger 아님

## 8. 결론

D1.Arch = **LightGBM cold-only replacement (warm freeze) / D1.Y framework strict primary** (R1 amendment 정합).

Hypothesis test (cold-only narrow):
- (b) Cold CB algorithm-specific issue → LGBM cold이 heavy-tail / small-cell artsy_gallery에 더 robust → PASS 가능

PASS 시 → cold architecture promise / **PROMOTE_TO_TUNING_AND_CANARY** (LGBM HP retune 후속 + canary deploy / B와 결합 가능 / full migration은 두 번째 cycle 후).
FAIL 시 → **default LGBM insufficient** (R1 P1.1 narrow / "architecture-independent" overclaim 회피) → 후속 tuned LGBM cycle 또는 architecture axis abandon 검토.

**Compute**: ~5-10분 wall (LGBM은 CB+XGB 대비 빠름 / cold-only이라 더 cheap / D1.Y 정합 framework).

**PR-WARM-B와 orthogonal** (R1 P0): cold-only / warm 변경 X / B Stage 5 deploy 그대로 valid.
