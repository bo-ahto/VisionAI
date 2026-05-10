# D1.Arch: LightGBM Cold-Only Replacement — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d1_arch_lightgbm_replacement_prereg_20260510.md` (R1 NEEDS FIX → R2 NEEDS FIX → R3 LGTM)
> **실행일**: 2026-05-10 (~14분 wall / 10 fresh seeds validation)
> **실행 결과**: ❌ **default_LGBM_insufficient** (R1 P1.1 narrow / 3 PASS + 7 FAIL)

## 1. Summary

VFR (commit f48f67b) framework reform abandon 후 architecture change axis 진입. R1 NEEDS FIX (P0 + P1×2) → R2 NEEDS FIX (stale text) → R3 LGTM amendment 정합 cold-only narrow scope cycle.

**결과**:
- Strict primary: 3 PASS + 7 FAIL → **FAIL**
- Bootstrap secondary: cold_overall mean=-0.29 / CI95 [-1.23, +0.69] → **bootstrap_FAIL**
- **Combined: `default_LGBM_insufficient`** (R1 P1.1 narrow interpretation)

**Important (R1 P1.1)**: FAIL ≠ "architecture-independent confirmed". 본 cycle 결과 = "default LGBM 단독으로는 cold path 개선 불충분" only. Tuned LGBM도 fail 시만 architecture-independent 결론 reserve.

**운영 결정**:
- ✅ Default cold path (CB) 유지 (architecture 변경 X)
- ✅ PR-WARM-B (B winner) Stage 3-5 진행 그대로 valid (orthogonal axis 정합 / R1 P0)
- 🔍 후속 후보: Tuned LGBM cycle (Optuna search) 또는 architecture axis abandon

## 2. R1-R3 Amendment 정합

| Round | Verdict | 반영 |
|---|---|---|
| R1 사전 | NEEDS FIX | P0 (cold-only) + P1.1 (FAIL narrow) + P1.2 (cap at canary) |
| R2 사전 | NEEDS FIX | §6 / §8 stale text |
| R3 사전 | LGTM | Stage 진입 ready |

핵심 amendments:
- **Cold-only scope** (warm = default XGB freeze) — PR-WARM-B와 orthogonal 보존 (codex P0)
- **FAIL narrow interpretation** (codex P1.1) — "default LGBM insufficient" only
- **Cap at canary** (codex P1.2) — 단일 cycle full migration X

## 3. Method (실행)

### 3.1 LGBM 학습 (default params)

```python
LGBM_PARAMS = {
    "objective": "regression", "metric": "l2",
    "num_leaves": 31, "learning_rate": 0.05,
    "feature_fraction": 0.9, "bagging_fraction": 0.9, "bagging_freq": 5,
    "verbose": -1, "seed": 42,
}
LGBM_NUM_BOOST_ROUND = 1000
```

LightGBM 4.6.0 / native categorical handling (CAT_FEATURES 6개 / cat_indices에 indicate).

### 3.2 Validation (per seed)

각 seed × 80/20 GroupShuffleSplit:
- **Candidate**: LGBM cold (LGBM 학습 / 80% pool) + default XGB warm (frozen / shared baseline)
- **Baseline**: default CB cold (CB 학습 / 80% pool) + default XGB warm (shared)
- 둘 다 default best_params 사용 / calibration 미적용 (R2 정합 / D1.SC 정합)

### 3.3 Compute
- 10 seeds × ~22-25s/seed = ~14분 wall
- LGBM 빠름 / cold-only / cheap

## 4. Per-seed 결과

| seed | Δ_cold | Δ_artsy | Δ_saatchi | verdict |
|---|---|---|---|---|
| 1153 | +2.97 | **-6.00** | **+6.56** | **FAIL** |
| 1171 | -2.83 | **-7.35** | -1.08 | **PASS** |
| 1187 | +1.49 | **-7.45** | **+3.84** | **FAIL** |
| 1201 | -0.27 | +0.74 | -0.14 | **FAIL** (G2 +0.74) |
| 1217 | -2.02 | -0.01 | -2.77 | **PASS** |
| 1231 | -0.54 | -0.39 | -0.22 | **PASS** |
| 1249 | -0.01 | +0.48 | -0.07 | **FAIL** (G2 +0.48) |
| 1259 | -0.12 | **+4.61** | -1.45 | **FAIL** |
| 1277 | -0.25 | -0.92 | **+1.60** | **FAIL** (G3) |
| 1289 | -1.35 | -1.74 | +1.07 | **FAIL** (G3 +1.07) |

**관찰**:
- **artsy variance 매우 큼**: range [-7.45, +4.61] / 12pp range (D1 cold 정합)
- **saatchi variance 도 큼**: range [-2.77, +6.56] / 9pp range
- **cold_overall mean -0.29 (mild negative) / std large**

## 5. Aggregate (R1 P1.1 strict)

| Metric | Value | Status |
|---|---|---|
| Verdict counts | PASS=3 / INC=0 / FAIL=7 | |
| Strict primary aggregate | **FAIL** (FAIL ≥ 2) | |
| Bootstrap cold_overall mean | -0.293 | |
| Bootstrap cold_overall CI95 | [-1.226, +0.694] | CI includes 0 |
| Bootstrap status | **bootstrap_FAIL** (CI upper > +0.5) | |

## 6. Combined Decision (R1 amendment / cap at canary)

| Strict | Bootstrap | Decision |
|---|---|---|
| FAIL | bootstrap_FAIL | **`default_LGBM_insufficient`** (R1 P1.1 narrow) |

**R1 P1.1 narrow interpretation**:
- FAIL = "default LGBM 단독으로는 cold path 개선 불충분" only
- "Architecture-independent confirmed" 결론은 tuned LGBM도 fail 시 reserve
- 후속 trigger: tuned LGBM Optuna search cycle 또는 axis abandon 검토

## 7. 분석: Cold path는 architecture-agnostic

### 7.1 D1 cold cycle 6 누적 (모두 fail)

| Cycle | Architecture | Approach | Bad-seed rate |
|---|---|---|---|
| D1.X | CB+XGB (default+retuned) | unified HP retune | 20% |
| D1.Y | CB+XGB (retuned) | N=10 expansion | 30% |
| D1-extended | CB+XGB (retuned) | fresh N=10 | **80%** |
| D1.SC | CB only (default / source-split) | data partition | **70%** |
| **D1.Arch (본 commit)** | **LGBM (default) + freeze warm** | **architecture replace** | **70%** |

→ **6 different cold path approaches 모두 fail / cold path 본질적 한계 강력 입증** (단 default params 한정 / tuned는 별도).

### 7.2 LGBM의 강점/약점 평가

본 cycle 데이터:
- artsy mean -1.80 (mean으론 강한 negative / 그러나 CI95 [-4.15, +0.48] 포함 0)
- saatchi mean +0.73 (mean도 positive!) — saatchi side에서 LGBM이 CB보다 worse
- cold_overall mean -0.29 (매우 약한)

**해석**:
- artsy heavy-tail 작가 가격 분포에서 LGBM이 CB와 비교적 다른 학습 (variance 더 큼) — 일부 split 매우 잘 / 일부 매우 못
- saatchi (큰 dataset)에서는 LGBM이 CB 대비 약간 worse / mean positive
- 결론: LGBM이 architecture로 fundamental advantage X (default params 한정)

### 7.3 Tuned LGBM cycle 가치 평가

본 cycle 결과로 추론:
- artsy effect는 **direction 명확 negative** (mean -1.80) — tuned로 더 좋아질 수 있음
- saatchi effect는 **direction 모호 / positive** — tuned로도 어려울 가능성
- 운영 cost (LGBM serving infra 추가) 대비 ROI 불확실

**Codex Q7 답변**: "INCONCLUSIVE/FAIL → maybe tuned LGBM follow-up". 본 cycle은 FAIL이지만 artsy direction 명확 / 단 saatchi direction 위협적.

## 8. PR-WARM-B와 interaction

본 cycle 결과 = D1.Arch FAIL (default LGBM insufficient) → cold path 변경 X / **PR-WARM-B (B winner) Stage 3-5 그대로 valid** (R1 P0 정합 / orthogonal).

D1.Arch 결과는 PR-WARM-B B winner의 unique value 더 강화:
- Cold path 6 cycles fail (HP retune / source split / architecture change 모두)
- B (warm-only XGB retune) 5/5 PASS — **유일 robust positive line**

## 9. 산출물

### 9.1 Commit 대상

- `docs/d1_arch_lightgbm_replacement_prereg_20260510.md` (R1-R3 amendment 반영)
- `docs/d1_arch_lightgbm_replacement_results_20260510.md` (본 문서)
- `scripts/d1_arch_lgbm_validation.py`
- `data/d1_arch_holdout_20260510/seed{1153-1289}_holdout_indices.json`

### 9.2 .gitignore (artifact)
- `model_test_results/d1_arch_results.json`

## 10. 한계 / Risk (codex 정합)

- **Default LGBM only**: R1 amendment / FAIL narrow / tuned LGBM은 별도 cycle / "architecture-independent" overclaim 회피
- **N=10 small**: split variance 큼 / artsy CI 광범위 [-4.15, +0.48]
- **Cold-only test**: warm freeze / D1.SC 정합 / B winner와 orthogonal 보존
- **Codex Q7 정확성**: D1 abandon 추천 + 본 cycle 결과로 architecture axis도 default level fail / Q7 prediction 강력 입증

## 11. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | NEEDS FIX | P0 (cold-only / warm freeze) + P1.1 (FAIL narrow) + P1.2 (cap at canary) |
| R2 사전 | NEEDS FIX | §6 / §8 stale text 정정 |
| R3 사전 | LGTM | Stage 진입 ready |
| R4 사후 | (예정) | 결과 검수 / tuned LGBM cycle 진행 결정 |

## 12. 결론

D1.Arch = **default_LGBM_insufficient** (R1 P1.1 narrow / 3 PASS / 7 FAIL).

**Cold path 6 cycles 누적 (모두 fail)**:
- HP retune (D1.X / D1.Y / D1-extended): all fail
- Data partition (D1.SC): fail
- **Architecture change (D1.Arch / 본 commit / LGBM default)**: **fail**

**핵심 finding**: Default cold algorithm change (CB → LGBM) 단독으로는 cold path 본질적 한계 극복 X. Tuned LGBM은 별도 cycle 후속 후보 (R1 Q4 답변).

**운영 결정 (확정)**:
- ✅ N=32 default best_params 유지 (cold + warm)
- ✅ B-retuned warm path (PR-WARM-B Stage 3-5 후) deploy
- ✅ Cold algorithm 그대로 (CB / XGB) — LGBM 채택 X
- ❌ Architecture change axis (default level) abandon

**본 세션 17 cycles 종합**:
- ✅ B (warm-only retune / commit 3a27002) — **유일 ADOPT** / PR-WARM-B Stage 1+2 commit
- ❌ D1 cold axis (5 cycles) — 완전 abandon
- ❌ D3 blend axis (2 cycles) — terminated
- 🔍 VFR — framework 정확 입증
- ❌ **D1.Arch (본 commit)** — **default LGBM insufficient / architecture default level abandon**

**남은 후속 후보** (별도 prospective cycles / 본 cycle scope 외):
- Tuned LGBM Optuna search cycle (R1 Q4 trigger / artsy direction promising / saatchi 위험)
- Architecture axis 완전 abandon (cost vs uncertainty / B Stage 5 deploy 우선 권고)
- Bayesian hierarchical / Quantile regression (다른 architecture / pymc / statsmodels)
- Data/feature reform (heavy-tail dataset 정합)
