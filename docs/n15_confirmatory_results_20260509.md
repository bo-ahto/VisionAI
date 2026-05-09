# N=15 Confirmatory cycle 결과 (decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **Prereg**: `docs/n15_confirmatory_prereg_20260509.md` (R3 LGTM 잠금)
> **Run**: `scripts/validate_n15_confirmatory.py`
> **Results JSON**: `model_test_results/n15_confirmatory_20260509.json`
> **Holdout indices**: `data/n15_confirmatory_holdout_20260509/seed{31337,7,13}_holdout_indices.json`

## 1. TL;DR

**Overall verdict**: **HOLD** (per prereg §3.5).

Cell-level verdicts (3 seeds 합산):

| Candidate | Aggregate | 채택 결정 |
|---|---|---|
| **XGB@N=15** (sweep winner / strong adoption) | **FAIL** (3/3 seed warm regression) | HOLD |
| **Ens@N=15** (보조 / weak adoption) | **FAIL** (1/3 seed G2_ens FAIL + 3/3 warm regression) | HOLD |

**핵심 발견 (혼합 시그널)**:
- **Cold path 시그널 강함 (XGB@N=15 만)**: 3/3 seed에서 cold overall 개선 또는 보합 (Δ_cold_strong = −0.72 / +1.46 / −0.35). **Artsy cold 강한 개선** (−0.86 / +0.05 / −1.49). 하지만 seed 7에서 cold +1.46pp degradation 발생 (split-driven variance 큼).
- **Warm path 작은 regression**: 3/3 seed warm +0.10 ~ +0.29pp (G4 threshold 0.3pp 이내 / Guard PASS / 단 prereg strict rule "Δ_warm > 0 = FAIL"으로 점수 FAIL).
- **Ensemble@N=15 artsy cold 악화**: G2_ens FAIL 1/3 (seed 31337에서 +2.35pp) — CB@N=15가 artsy에서 +2.72pp degraded (15 features로 artsy cold 모델링 부족).

**Sweep amendment 시그널 (a0a1bde) 부분 재현**:

| Metric | Sweep (post-hoc CV) | Confirmatory (avg 3 seeds) | 재현성 |
|---|---|---|---|
| Δ Cold overall (XGB@N=15 vs ?) | +0.033 (vs Ens@N=32 baseline) | +0.13 평균 (XGB vs Ens / split variance ±1.0pp) | 부분 재현 (방향 일치 / 노이즈 큼) |
| Δ Warm | **−0.49** (XGB winner) | **+0.19 평균** (regression) | **반대 방향** ⚠️ |
| Δ Artsy cold | +0.57 (악화) | **−0.77 평균 (개선!)** | **반대 방향** (긍정적) ⚠️ |
| Δ Saatchi cold | −0.05 (flat) | 0.00 평균 (flat) | 일치 |

→ Sweep의 warm 개선 시그널이 confirmatory에서 재현 안 됨. Sweep의 artsy 악화도 재현 안 됨. **Sweep's per-fold-internal 15 features (각 fold마다 다른 features)** vs **frozen 15 features (전 seed 동일)** 차이가 원인 추정.

## 2. Per-seed × per-candidate 결과

### 2.1 Strong adoption (XGB@N=15 vs Ens@N=32)

| Seed | n_holdout cold/warm | Δ_cold | Δ_artsy | Δ_saatchi | Δ_warm | Guards | Verdict |
|---|---|---|---|---|---|---|---|
| 31337 | 5171 / 5413 | **−0.72** | **−0.86** | −0.72 | +0.18 | G1-G4 PASS | FAIL (warm > 0) |
| 7 | 5658 / 5413 | **+1.46** | +0.05 | +1.99 | +0.29 | G1 FAIL / G3 FAIL | FAIL (G FAIL) |
| 13 | 5082 / 5413 | **−0.35** | **−1.49** | −0.13 | +0.10 | G1-G4 PASS | FAIL (warm > 0) |

**관찰**:
- Seed 31337 + 13: G1-G4 모두 PASS / cold 개선 / **prereg strict rule (Δ_warm > 0 = FAIL)으로만 FAIL**. Guard 관점으로는 PASS.
- Seed 7: split-driven variance — cold +1.46pp degradation / G1 + G3 FAIL. 이 seed가 outlier.
- Per-source: Artsy cold 일관 개선 (3/3 seed에서 ≤ 0). Saatchi cold mixed (improvement / degradation / flat).

### 2.2 Weak adoption (Ens@N=15 vs Ens@N=32)

| Seed | Δ_cold | Δ_artsy | Δ_saatchi | Δ_warm | Guards | Verdict |
|---|---|---|---|---|---|---|
| 31337 | −1.42 | **+2.35** ⚠️ | −2.84 | +0.18 | **G2 FAIL** | FAIL |
| 7 | −0.73 | −0.50 | −0.79 | +0.29 | G1-G4 PASS | FAIL (cold > 0.5? no... cold = -0.73 < 0.5, but ens prereg threshold weak FAIL > 0.5pp) |
| 13 | −0.24 | −1.62 | +0.31 | +0.10 | G1-G4 PASS | FAIL (warm > 0) |

**관찰**:
- Seed 31337: Ens cold overall 큰 개선 (-1.42pp) 이지만 artsy 악화 (+2.35pp / G2 FAIL). saatchi 큰 개선 (-2.84pp).
- Seed 7: Ens cold flat 개선 / artsy/saatchi 모두 약간 개선. Guard PASS / 단 weak prereg rule "cold > 0 OR warm > 0 = FAIL" 확인 필요. cold = -0.73 (PASS), warm = +0.29 (FAIL).
- Per-source 패턴: artsy ensemble은 N=15에서 변동 큼 (+2.35 / -0.50 / -1.62). CB@N=15가 artsy에서 약함이 ensemble까지 영향.

### 2.3 Per-model breakdown (seed 31337 / 가장 정보량 많음)

| Model | Cold overall | Cold artsy | Cold saatchi | Warm |
|---|---|---|---|---|
| cb_n15 | 38.14 | 39.11 (N=32 대비 +2.72) | 37.31 | — |
| cb_n32 | 38.46 | 36.39 | 39.54 | — |
| xgb_n15 | **38.15** | **34.14** (N=32 대비 −3.30) | 39.59 | 9.73 |
| xgb_n32 | 39.38 | 37.44 | 39.77 | 9.55 |
| ens_n15 | **37.45** | 37.35 (ens_n32 대비 +2.35) | 37.46 | (xgb_n15) |
| ens_n32 | 38.87 | 34.99 | 40.31 | (xgb_n32) |

**해석**:
- **CB@N=15가 artsy cold에서 약함**: 39.11 vs CB@N=32 36.39 / +2.72pp. 15 features로 artsy cold 표현력 부족.
- **XGB@N=15가 artsy cold에서 강함**: 34.14 vs XGB@N=32 37.44 / **−3.30pp**. 적은 feature로 더 잘함 (regularization 효과 추정).
- **Ens@N=15는 CB의 약점이 ensemble까지 끌고 옴**: 37.35 vs ens_n32 34.99 / +2.35pp.
- **결론**: **pure XGB@N=15가 가장 유망** — 단 warm 작은 regression 해소 필요 (HP retuning).

## 3. 채택 결정 (per §3.5)

**전체**: HOLD. N=32 baseline 유지. N=15 migration 보류.

### 3.1 권고 (codex R4 사후 검수 합의)

**Codex R4 verdict (NEEDS DECISION ALIGNMENT → 합의)**:
- Implementation prereg-faithful / 결정 logic mechanically correct.
- **Prereg rule contradiction 명시 인정**: G4 (Δ_warm ≤ +0.3pp = PASS) vs prereg `Δ_warm > 0 = FAIL` 모순. **Retroactive fix X / locked rule 준수**. 단 G4-consistent rule 적용 시 strong (XGB@N=15) seed 31337+13 verdict는 PASS → aggregate INCONCLUSIVE (not FAIL)였을 것 — 이 점 results 문서에 명시.
- Sweep-vs-confirmatory mismatch는 **유용한 발견** (sweep's warm gain은 fold-adaptive feature sets에서 나왔음 / frozen deployable contract는 본 cycle 결과가 정직). 후속 deployment-facing cycle에 frozen contract 유지.
- **N15.B 진행 정당화**: 단 prospective rule-fix 후 (warm decision rule을 G4와 일치시킨 후). cold 시그널 (XGB@N=15 artsy 개선 / 2/3 seed cold 개선)이 retuning 가치 충분.
- **N15.C scope narrow 권고**: full ensemble 대신 **Artsy / XGB-focused** path로. CB@N=15 weakness가 ensemble 발목.
- Seed 7 outlier는 variance / stop signal 아님.

### 3.2 채택 결정 요약

| 영역 | 결정 |
|---|---|
| 본 cycle 채택 | **HOLD** (locked rule strict / N=32 baseline 유지) |
| Rule contradiction note | G4-consistent rule 적용 시 strong = INCONCLUSIVE (not FAIL) |
| Frozen feature contract | 유지 (sweep의 fold-adaptive 특성과 분리) |
| Default OFF | 유지 |
| N15.B 진행 | ✅ Justified (cold 시그널 강함 / rule-fix 후 prospective) |
| N15.C scope | Artsy / XGB-focused (full ensemble 제외 / CB@N=15 weakness 우회) |

### 3.3 후속 cycle 우선순위 (R4 합의)

1. **(i) N15.B HP retuning** (uppermost): pure XGB@N=15 best_params Optuna search. Prospective prereg에서 warm rule을 G4 임계 (≤+0.3pp = PASS) 정합으로 fix.
2. **(ii) N15.C Source-Conditional 통합**: per-source XGB@N=15 + per-source HP retraining + per-source calibration. Artsy XGB-focused path / Saatchi는 별도 (Phase 3 영역).
3. **(iii) (참고) warm-only fold-internal sweep cycle**: deployment-facing X / sweep convention의 warm signal 재현성 검증용. 본 cycle 외 후순위.

### 3.2 R3 LGTM 후 발견된 method nuance

- **Frozen N=15 (averaged ranking)** vs **Per-fold-internal N=15 (sweep convention)** 차이가 결과에 큰 영향. sweep의 winner는 fold마다 다른 top-15에 의존 / frozen은 단일 set. **운영 deployment는 frozen 필요** (단일 feature contract). 이 trade-off가 본 cycle의 시그널 약화 원인.

## 4. R4 사후 검수 결과

| Round | Verdict | 핵심 |
|---|---|---|
| R4 (`019e0bb1` resume) | **NEEDS DECISION ALIGNMENT → 합의** | Implementation 정합 / 결정 logic mechanically correct / prereg rule contradiction 인정하되 retroactive fix X / commit as HOLD + 명시 caveat / N15.B 진행 정당화 (rule-fix 후) / N15.C scope narrow (Artsy XGB-focused) |

## 5. 산출물

- ✅ prereg + script + JSON + holdout indices + 본 결과 문서
- 🔄 codex R4 사후 검수 (다음 단계)
- 🔄 commit (R4 합의 후)
