# N=15 + Source-Conditional Integration cycle 결과 (decision-binding)

> **작성일**: 2026-05-09 (run 2026-05-10 00:07–00:19)
> **분기**: `exp/track1-feature-optimization-cycle`
> **Prereg**: `docs/n15_source_conditional_integration_prereg_20260509.md` (R3 LGTM 잠금)
> **Run**: `scripts/validate_n15_source_conditional_integration.py`
> **Results JSON**: `model_test_results/n15_sc_integration_20260509.json`
> **Holdout indices**: `data/n15_sc_integration_holdout_20260509/{artsy,saatchi}_seed{31337,7,13}_holdout_indices.json`

## 1. TL;DR

**Overall verdict**: **NEEDS_MORE_DATA** (per prereg §3.6).

**핵심 발견 (split-driven variance dominates)**:
- **Artsy load_bearing 2 cells**: 둘 다 **INCONCLUSIVE** (PASS×2 + FAIL×1 each / 3-seed mixed)
  - 단일 seed Δ_v2_v1pool 범위가 **−20.60 ~ +12.08pp** (작은 cell n_holdout ~150-250)
  - Multi-seed N=3 부족 / N=10+ 확대 시 시그널 stabilize 가능성
- **Saatchi (consistency_only only)**: 모든 path × seed PASS (Δ ≤ +0.24 / cold 일관 안정)
  - v2 (N=15) ≈ v1_pool (N=32) on Saatchi → simplification candidate
- **Artsy warm artsy_gallery (consistency_only)**: INCONCLUSIVE×3 (small cell + CI 0 가로지름 / boundary)
- **Artsy warm artsy_online (consistency_only)**: PASS×3 (large cell stable)

| Source | load_bearing | consistency_only | Verdict |
|---|---|---|---|
| Artsy | INCONCLUSIVE × 2 | PASS × 1 + INCONCLUSIVE × 1 | **NEEDS_MORE_DATA** |
| Saatchi | (none) | PASS × 2 | N/A_no_load_bearing |

→ 3 cycle 통합 결과 (N15.A HOLD / N15.B HOLD / N15.C NEEDS_MORE_DATA): **N=15 migration은 현 결정으로 보류**. Saatchi 단독 simplification 후보 정도.

## 2. Per-cell × per-seed 상세 결과

### 2.1 Artsy load_bearing cells (decision-binding endpoint)

| Cell | Seed | Δ_v2_v1pool | calibrated_v2 | calibrated_v1_pool | Decision | Note |
|---|---|---|---|---|---|---|
| `artsy_gallery` cold | 31337 | **−4.05** | 9.93 | 13.98 | PASS | 강한 개선 |
| `artsy_gallery` cold | 7 | **+12.08** ⚠️ | 49.39 | 37.30 | FAIL | 큰 악화 |
| `artsy_gallery` cold | 13 | **−20.60** ⭐ | 48.06 | 68.66 | PASS | 압도적 개선 |
| `artsy_online` cold | 31337 | +2.33 ⚠️ | 28.68 | 26.35 | FAIL | mild |
| `artsy_online` cold | 7 | **−3.85** | 37.93 | 41.79 | PASS | 강한 개선 |
| `artsy_online` cold | 13 | −1.05 | 32.25 | 33.30 | PASS | 개선 |

**관찰**:
- `artsy_gallery` cold에서 단일 seed Δ 범위 = **−20.60 ~ +12.08pp** (range 32.7pp).
  - n_holdout per cell ≈ 150-250 (small cell + Artsy gallery tail-heavy distribution)
  - seed 13 v1_pool baseline 68.66 (한 split이 매우 어려운 holdout) → seed 7과 정반대
  - 단순 multi-seed N=3로는 robust 시그널 추출 불가
- `artsy_online` cold는 large cell (n~1300) 이지만 split마다 +2.3 / −3.9 / −1.1pp 범위.

**Aggregate**:
- artsy_gallery: PASS × 2 + FAIL × 1 → **INCONCLUSIVE**
- artsy_online: PASS × 2 + FAIL × 1 → **INCONCLUSIVE**

### 2.2 Saatchi consistency_only (안정 / N=15 simplification 후보)

| Cell | Seed | Δ_v2_v1pool | Decision |
|---|---|---|---|
| `saatchi_online` cold | 31337 | **−0.004** | PASS |
| `saatchi_online` cold | 7 | **−1.18** | PASS |
| `saatchi_online` cold | 13 | **−3.12** | PASS |
| `saatchi_online` warm | 31337 | −0.012 | PASS |
| `saatchi_online` warm | 7 | +0.040 | PASS |
| `saatchi_online` warm | 13 | +0.243 | PASS |

**관찰**: Saatchi (n~4000 holdout / large cells) 모든 seed에서 PASS. cold path에서 v2가 평균 −1.4pp 개선 시그널. warm은 보합. simplification candidate (단 source-conditional v1는 saatchi에서 calibration 미적용 / shipped factor=1.0 이므로 deployment value는 model architecture 단순화에 한정).

### 2.3 Artsy warm consistency_only (boundary case)

| Cell | Seed | Δ_v2_v1pool | CI90 | Decision |
|---|---|---|---|---|
| `artsy_gallery` warm | 31337 | −0.30 | [−1.63, +1.62] | INCONCLUSIVE |
| `artsy_gallery` warm | 7 | +0.05 | [−1.82, +2.20] | INCONCLUSIVE |
| `artsy_gallery` warm | 13 | −0.86 | [−1.57, +1.58] | INCONCLUSIVE |
| `artsy_online` warm | 31337 | (PASS) | — | PASS |
| `artsy_online` warm | 7 | (PASS) | — | PASS |
| `artsy_online` warm | 13 | (PASS) | — | PASS |

**관찰**: artsy_gallery warm은 small cell (n~140 / 작가 5+ artworks 필터 후 미세 cell) + paired bootstrap CI 0 가로지름 → 통계적으로 INCONCLUSIVE 일관. point estimate는 보합 (−0.86 ~ +0.05). artsy_online warm은 large cell (n~1180) PASS 안정.

## 3. 채택 결정 (per prereg §3.5/§3.6)

### 3.1 Per-source verdict

**Artsy**:
- load_bearing aggregate: INCONCLUSIVE × 2 → source level **NEEDS_MORE_DATA**
- consistency_only aggregate: PASS × 1 + INCONCLUSIVE × 1 (no FAIL) → safety gate 통과
- Final: NEEDS_MORE_DATA

**Saatchi**:
- load_bearing: 없음 → N/A_no_load_bearing
- consistency_only: PASS × 2 → 안정

**Overall**: **NEEDS_MORE_DATA**.

### 3.2 권고 (R4 사후 검수에서 확정 예정)

1. **즉시**: 운영 Source-Conditional v1 (N=32 + e3367ed factor) 유지 / N=15 migration X.
2. **N=15 migration 의 deployment value 재현성 약함**: Artsy load_bearing cell Δ_v2_v1pool 단일 seed 범위 32.7pp (−20.60 ~ +12.08) → 3 seed 부족. Multi-seed N=10-20 확대 cycle 진행 가능 / 단 비용 검토 필요.
3. **부분 채택 (Saatchi only)**: N=15 features로 Saatchi-only artifact migration 후보 (Saatchi 안정 + simplification 가치). Artsy는 N=32 유지. 단 운영 파이프라인 source 별 feature schema 분기 필요 → 별도 architecture cycle.
4. **결론적 진단**: Track 1 N=15 candidacy는 본 3-cycle 결과로 **약함 확인**. Default best_params + N=15 features는 N=32 baseline 능가하지 않거나 split-variance에 묻힘. Feature optimization은 ADD-A (Phase 4 / N=33) 까지가 한계.

## 4. 3-cycle 통합 진단

| Cycle | Verdict | 핵심 |
|---|---|---|
| N15.A Confirmatory | HOLD (warm strict rule) | Pure XGB@N=15 cold artsy 시그널 강함 / warm 작은 regression. Sweep의 warm improvement는 fold-adaptive 효과였음. |
| N15.B HP Retuning | HOLD (negative result) | Operational GroupKFold scale에서 retuned가 default 능가 X. constraint-feasible 5/30 trials best warm CV +3.76pp WORSE. |
| **N15.C SC Integration** | **NEEDS_MORE_DATA** | Artsy load_bearing cell split variance 압도적 (−20 ~ +12pp 범위) / Saatchi는 안정 PASS. 3-seed 부족. |

**3-cycle 통합 결론**:
- Track 1의 N=15 migration 가능성 = **현재 evidence 기준으로 약함**.
- Saatchi (consistency_only / no calibration) 단독 simplification 가능하나 partial deployment.
- Artsy load_bearing cells는 sample size 한계로 robust 시그널 추출 불가 → multi-seed 확대 cycle 또는 데이터 수집 / 별도 stratified holdout 필요.

## 5. 한계 / Risk

- **Multi-seed N=3 부족**: artsy_gallery cold seed 7 +12pp 극단치 + seed 13 -20pp 극단치 / 3 seed로는 평균치 unstable.
- **Small cell sample size**: artsy_gallery n_holdout ≈ 150-250 per seed / paired bootstrap CI도 ±10pp 폭. 본질적 statistical limit.
- **artsy_gallery v2 cold seed 7의 +12.08pp 시그널**: real outlier? 또는 v2 N=15 features가 특정 split에서 반복적으로 fail? 별도 ablation 필요.
- **Search-validation 일관성**: 본 cycle은 fair v1_pool vs v2_pool comparison (R1 P0 fix) → in-sample bias 없음. 단 small cell variance를 fully cover X.

## 6. R4 사후 검수 결과

| Round | Verdict | 핵심 |
|---|---|---|
| R4 (`019e0bb1` resume) | **LGTM-with-caveat** | Implementation prereg-faithful (R1 P0 fair v2_pool vs v1_pool / P1 safety gate / P2 tradeoff). NEEDS_MORE_DATA mechanically correct. Seed 7 artsy_gallery +12.08pp = real small-cell tail outlier (n=146 / artsy gallery distribution heavy-tailed) / impl bug X. **3-cycle 통합 결론으로 N=15 migration line 종결 권고** (option D). Multi-seed 확대 (option A)는 비추천 (비용 큰데 marginal value). Saatchi-only partial (option B)도 비추천 (source schema 분기 복잡성). 후속 다른 cycle은 N=18/20/25 sweep (option C) 또는 다른 방향 (warm-only path 등). |

### 6.1 R4 합의 사항

- **본 cycle commit**: prereg + script + indices + results doc. Verdict NEEDS_MORE_DATA로 종결.
- **N=15 direct migration line 종결**: 3 cycle (N15.A HOLD / N15.B clean negative / N15.C NEEDS_MORE_DATA) → 충분한 negative evidence.
- **Saatchi-only partial deployment X**: limited value + source-specific feature-schema complexity.
- **Multi-seed 확대 cycle 비추천**: Artsy load_bearing cell variance가 statistical limit / N=10-20 확대도 large variance fully cover X.
- **후속 후보**:
  - 다른 N grid (N=18, 20, 25) re-sweep
  - 다른 optimization 방향 (warm-only path 단독 / 또는 다른 axis)

## 7. 산출물

- ✅ `docs/n15_source_conditional_integration_prereg_20260509.md` (R1-R3 LGTM)
- ✅ `docs/n15_source_conditional_integration_results_20260509.md` (본 문서)
- ✅ `scripts/validate_n15_source_conditional_integration.py` (~430 lines / ruff clean)
- ✅ `data/n15_sc_integration_holdout_20260509/{artsy,saatchi}_seed{31337,7,13}_holdout_indices.json`
- (gitignored) `model_test_results/n15_sc_integration_20260509.json`
