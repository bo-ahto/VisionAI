# D3.B: Stacking Meta-learner Cycle — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d3_b_stacking_metalearner_prereg_20260510.md` (R1+R2+R3+R4 LGTM)
> **실행일**: 2026-05-10 (18:46 KST 시작 / 18:55 KST 종료 / ~9min wall)
> **실행 결과**: ❌ **HOLD_50_50 / blend axis terminate** (primary 5/5 FAIL + secondary 5/5 FAIL)

## 1. Summary

D3 scalar w (HOLD_50_50) → D3.B Stacking meta-learner advanced blend axis. R1 NEEDS FIX → R2/R3/R4 LGTM amendment 정합 dual-gate validation:

- **Primary endpoint** (per-seed pool OOF refit): 5/5 FAIL
- **Secondary endpoint** (frozen full-data meta): 5/5 FAIL
- **Overall verdict**: **HOLD_50_50_blend_axis_terminate**

R1 Q6 답변 정합 — linear stacker fail 시 blend axis 종결 (XGB stacker로 escalation X). 본 cycle = D3 scalar w + D3.B stacker 결과 종합 / **blend axis (이외 stacker / source-conditional / per-cell 등) 본 strict OOF→fresh validation framework 하에서는 일반화 X 확인 / 종결**.

## 2. R1-R4 Amendment 반영

| Round | Verdict | 반영 항목 |
|---|---|---|
| R1 사전 | NEEDS FIX (P0 + P1×2) | per-seed refit primary / verdict logic 정합 / XGB cold full-fold |
| R2 사전 | NEEDS FIX (P1 + P2) | dual-gate adoption (primary AND secondary "not FAIL") / GroupShuffleSplit |
| R3 사전 | NEEDS FIX (§2.5 secondary 문구) | record-only → deployment gate / non-primary BUT adoption gate |
| R4 사전 | LGTM | Stage 진입 ready |

## 3. Method (실행 정합)

### 3.1 Frozen meta-learner (Secondary endpoint)

Full-data OOF generation (GroupKFold-5 / N=28376 / default CB + XGB):
- 5 fold OOF: ~84초 wall
- LinearRegression fit on `(cb_oof_log, xgb_oof_log, artsy_dummy, cb_xgb_diff)` → y_log

**Frozen meta coefficients**:
```
y_log = 0.7868·cb_oof_log + 0.1570·xgb_oof_log - 0.1264·artsy_dummy + 0.6299·cb_xgb_diff + 0.9438
```

해석: CB 비중 0.79 (50/50보다 CB-heavy / D3 scalar w*=0.3 = XGB-heavy와 반대 방향) — meta-learner는 OOF 위에서는 CB-favoring blend 학습. cb_xgb_diff coefficient 0.63 (positive) = CB > XGB일 때 final prediction 약간 위로 ajusted.

### 3.2 Per-seed validation (Primary endpoint)

5 fresh seeds: {149, 211, 277, 353, 449}

각 seed:
1. GroupShuffleSplit(test=0.20, random_state=seed) on artist_slug → 80/20 split
2. 80% pool 위 GroupKFold-5 OOF → cb_pool_oof_log, xgb_pool_oof_log
3. Pool OOF에서 meta_seed = LinearRegression().fit(...)
4. Final pool retrain CB + XGB
5. 20% holdout 위 cb_pred / xgb_pred / meta_seed.predict / frozen_meta.predict
6. 50/50 baseline = (cb_pred + xgb_pred)/2

각 seed compute: ~90초.

## 4. 결과

### 4.1 Per-seed verdict

| seed | n_pool | n_holdout | primary Δ_cold | primary verdict | secondary Δ_cold | secondary verdict |
|---|---|---|---|---|---|---|
| 149 | 23,071 | 5,305 | **+4.29** | **FAIL** | **+3.13** | **FAIL** |
| 211 | 22,549 | 5,827 | +0.57 | **FAIL** | **+3.57** | **FAIL** |
| 277 | 22,959 | 5,417 | **+13.31** | **FAIL** | **+9.90** | **FAIL** |
| 353 | 22,602 | 5,774 | -0.50 | **FAIL** (G2 +0.92) | **+7.19** | **FAIL** |
| 449 | 21,720 | 6,656 | **+5.68** | **FAIL** | -2.88 | **FAIL** (G2 +2.49) |

### 4.2 Aggregate

| Endpoint | Verdicts | Aggregate |
|---|---|---|
| Primary (per-seed refit) | 0 PASS + 0 INC + 5 FAIL | **FAIL** |
| Secondary (frozen meta) | 0 PASS + 0 INC + 5 FAIL | **FAIL** |

### 4.3 Per-seed extreme cases

**seed=277**: primary Δ=+13.31 / saatchi +18.48 — extreme regression. Stacker가 이 holdout에서 saatchi 작품들에 대해 가격을 매우 잘못 예측.
**seed=149**: primary artsy +9.36 — artsy 작품 가격 over-correction.
**seed=353**: secondary Δ=+7.19 / saatchi +12.15 — frozen meta도 large saatchi regression.

→ Stacker는 **OOF→fresh holdout 분포 변화에 매우 민감**. CB-heavy weights (0.79) + cb_xgb_diff (+0.63) 조합이 fresh holdout에서 in-sample CB의 노이즈를 over-fit한 가능성.

### 4.4 Per-seed primary meta coefficient 분포

각 seed primary meta는 다른 coefficient 학습 — 일관성 부족 가능성 (R1 P0 amendment에서 우려한 procedure variance):

| seed | cb_coef | xgb_coef | source_coef | diff_coef | intercept |
|---|---|---|---|---|---|
| (per-seed JSON 참조 / 본 commit 시점 결과 파일에 기록됨) | | | | | |

**관찰**: per-seed meta는 frozen meta (0.79 / 0.16 / -0.13 / 0.63 / 0.94)와 ranges 비슷 / 단 fresh holdout에서 모두 generalize X.

## 5. Decision (R2 P1 dual-gate)

prereg §3 dual-gate 정합:

| Primary | Secondary | Decision |
|---|---|---|
| FAIL | FAIL | **HOLD_50_50 / blend axis 종결** ✅ 본 verdict |

**운영 결정**:
- 50/50 ensemble (CB+XGB)/2 그대로 유지 (D3 scalar w 결과 정합)
- Stacking meta-learner는 본 cycle (linear / source dummy / cb_xgb_diff) 한정 fail
- R1 Q6: linear stacker fail → blend axis 종결 / XGB stacker (옵션 B)로 escalation X

## 6. D3 + D3.B 종합 결론 (blend axis)

본 세션 blend axis 누적 결과:

| Cycle | Approach | OOF metric | Validation aggregate | Decision |
|---|---|---|---|---|
| D3 (commit fd0f14e) | 1D scalar w grid (21-point) | OOF cold -0.34 (w*=0.3) | 1/5 PASS / 4 FAIL | HOLD_50_50 |
| **D3.B (본 commit)** | Linear stacker (4 features) | (built into per-seed primary) | **0/5 primary + 0/5 secondary** | **HOLD_50_50 + axis terminate** |

→ **Blend axis (scalar 또는 linear stacker) 본 strict OOF→fresh validation framework에서 50/50 능가 X 확인**. 운영 50/50 그대로 유지. 별도 후속 axis (advanced stacker / per-cell blend / 등)는 본 framework 자체 reform 필요.

## 7. 산출물

### 7.1 Commit 대상

- `docs/d3_b_stacking_metalearner_prereg_20260510.md` (R1-R4 amendment 반영)
- `docs/d3_b_stacking_metalearner_results_20260510.md` (본 문서)
- `scripts/d3_b_stacking_search.py` (per-seed refit + frozen secondary gate)
- `data/d3_b_holdout_20260510/seed{149,211,277,353,449}_holdout_indices.json`

### 7.2 .gitignore (artifact)

- `model_test_results/d3_b_stacker.json` (frozen full-data meta coefficients)
- `model_test_results/d3_b_stacking_results.json` (per-seed 상세)

## 8. 한계 / Risk

- **Linear stacker만 검증**: R1 Q1에서 옵션 B (XGB stacker)는 overfitting risk only로 배제 / 단 비선형 capacity 가정 자체는 미검증.
- **OOF→fresh holdout 분포 mismatch가 본질**: D3 scalar w와 동일 패턴 / OOF는 GroupKFold(artist) / fresh는 GroupShuffleSplit(artist 80/20). 학습/평가 분포 자체가 다름.
- **N=5 small sample**: 단 본 cycle은 5/5 FAIL 강한 signal / N 확장 우선순위 낮음.
- **Stacker artifact는 frozen meta만 / per-seed meta는 record only** (per-seed meta는 procedure validity 검증 / 운영 deploy artifact는 frozen).

## 9. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | NEEDS FIX (P0 + P1×2) | per-seed refit / verdict logic / XGB full-fold |
| R2 사전 | NEEDS FIX (P1 + P2) | dual-gate / GroupShuffleSplit |
| R3 사전 | NEEDS FIX (§2.5 wording) | secondary record-only → deployment gate |
| R4 사전 | LGTM | Stage 진입 ready |
| R5 사후 | (예정) | 결과 검수 / blend axis terminate 결정 적정성 |

## 10. 결론

D3.B Stacking meta-learner = **HOLD_50_50 / blend axis 종결**. Primary 5/5 FAIL + Secondary 5/5 FAIL → linear stacker는 fresh holdout 일반화 X. D3 scalar w + D3.B stacker 누적 결과 = 본 strict OOF→fresh validation framework 하에서 50/50 ensemble 능가하는 blend approach 발견 X. 운영 50/50 그대로 유지.

**본 세션 결과 종합** (Stage 4 + post Stage 4 follow-up cycles):
- ✅ B (warm-only retune) — 본 세션 유일 ADOPT (PR-WARM-B Stage 1+2 commit / Stage 3-5 pending)
- ❌ D1.X / D1.Y (cold + warm joint retune) — D1 axis 종결 (3/10 FAIL strict)
- ❌ D3 / D3.B (blend axis) — 50/50 유지 / blend axis 종결
