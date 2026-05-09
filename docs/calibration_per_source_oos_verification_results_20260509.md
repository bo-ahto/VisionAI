# Per-source Calibration OOS Verification 결과 (Retrained-artifact + Multi-seed / decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **Prereg**: `docs/calibration_per_source_oos_verification_prereg_20260509.md` (R4 LGTM 잠금)
> **Run**: `scripts/validate_per_source_calibration_oos.py`
> **Results JSON**: `model_test_results/calibration_oos_20260509.json`
> **Holdout indices**: `data/oos_holdout_20260509/{artsy,saatchi}_seed{31337,7,13}_holdout_indices.json` (6 files)

## 1. TL;DR

**Overall verdict (per prereg §3.5)**: **NEEDS_MORE_DATA**.

Cell-level 결과 (load_bearing 한정 / 운영 채택 결정 endpoint):

| Cell | Primary aggregate | Secondary aggregate | Cell adoption |
|---|---|---|---|
| `artsy/cold/artsy_gallery` | PROCEDURE_NULL_likely (PASS, GF, GF) | SECONDARY_INCONCLUSIVE (PASS, FAIL, PASS) | **NEEDS_MORE_DATA** |
| `artsy/cold/artsy_online` | PRIMARY_PASS_with_caveat (PASS, GF, PASS) | SECONDARY_PASS (PASS, PASS, PASS) | **ADOPT_with_caveat** |

`saatchi` source: `N/A_no_load_bearing` (전 cell consistency_only / e3367ed shipped factor=1.0).

**Reprod cycle 대비 핵심 차이 (in-sample bias 해결 확인)**:

| Metric | Reprod cycle (in-sample) | OOS cycle (true OOS) |
|---|---|---|
| `artsy_gallery` baseline (seed 31337) | 3.21 | **19.80** (~6× / 진짜 OOS 수준) |
| `artsy_online` baseline (seed 31337) | 7.17 | **27.04** (~4× / 진짜 OOS 수준) |
| `artsy_gallery` Δ_shipped (seed 31337) | +5.46pp (FAIL) | **−3.86pp** (PASS / CI [-7.69, -1.86]) |
| `artsy_online` Δ_shipped (seed 31337) | +0.31pp (FAIL) | **−0.81pp** (PASS) |

→ R4 caveat (in-sample bias 가설) 강하게 지지. Reprod cycle의 FAIL은 method artifact였음. OOS cycle에서 같은 seed=31337 위에서 e3367ed shipped factor가 baseline 대비 개선 효과 확인.

## 2. Per-cell 결과 (load_bearing 만)

### 2.1 `artsy/cold/artsy_gallery` (3 seed × n_holdout ≈ 144-366)

| Seed | n_train_pool | n_holdout | baseline_mdape | applied_refit | Δ_refit | Δ_shipped | CI90_shipped | Primary | Secondary |
|---|---|---|---|---|---|---|---|---|---|
| 31337 | 502 | 366 | 19.80 | 0.872 | −5.82 | −3.86 | [−7.69, −1.86] | PASS | SHIPPED_PASS |
| 7 | 722 | 146 | 37.20 | 1.0 (guard) | 0 | +0.58 | [−5.84, +2.85] | GUARD_FIRED | SHIPPED_FAIL |
| 13 | 724 | 144 | 68.66 | 1.0 (guard) | 0 | −11.60 | [−14.11, −2.76] | GUARD_FIRED | SHIPPED_PASS |

**관찰**:
- baseline MdAPE의 split-driven variance가 매우 큼 (19.80 / 37.20 / 68.66) — small cell (n≈150-360) + Artsy gallery 구매 행동의 tail-heavy distribution.
- procedure는 1/3 seed에서만 nontrivial factor 산출 (seed 31337 = 0.872 / 나머지 guard fallback).
- shipped factor (0.9152) 효과:
  - seed 31337: −3.86pp (significant improvement / CI 전 음수)
  - seed 7: +0.58pp (slight regression / CI 0 가로지름 → INCONCLUSIVE 영역이지만 prereg 정의로 SHIPPED_FAIL)
  - seed 13: −11.60pp (large improvement / CI 전 음수)
- Aggregate: Primary `PROCEDURE_NULL_likely` (2 GUARD_FIRED + 1 PASS), Secondary `SECONDARY_INCONCLUSIVE` (mixed PASS+FAIL+PASS) → **NEEDS_MORE_DATA**

### 2.2 `artsy/cold/artsy_online` (3 seed × n_holdout ≈ 1145-1313 / large cell / no bootstrap)

| Seed | n_train_pool | n_holdout | baseline_mdape | applied_refit | Δ_refit | Δ_shipped | Primary | Secondary |
|---|---|---|---|---|---|---|---|---|
| 31337 | 5108 | 1313 | 27.04 | 0.961 | −0.69 | −0.81 | PASS | SHIPPED_PASS |
| 7 | 5276 | 1145 | 41.79 | 1.0 (guard) | 0 | −1.23 | GUARD_FIRED | SHIPPED_PASS |
| 13 | 5216 | 1205 | 33.44 | 0.972 | −0.14 | −0.42 | PASS | SHIPPED_PASS |

**관찰**:
- baseline은 작은 cell보다 안정 (27.04 / 41.79 / 33.44).
- procedure는 2/3 seed에서 nontrivial factor (seed 31337 = 0.961 / seed 13 = 0.972 / seed 7 = guard fallback).
- shipped factor (0.9757) 효과: 3/3 seed에서 baseline 개선 (−0.81 / −1.23 / −0.42). 일관됨.
- Aggregate: Primary `PRIMARY_PASS_with_caveat` (2 PASS + 1 GUARD_FIRED), Secondary `SECONDARY_PASS` (3/3 SHIPPED_PASS) → **ADOPT_with_caveat**

## 3. Consistency_only cells (guard 정합 점검)

| Cell | seed 31337 | seed 7 | seed 13 | Aggregate |
|---|---|---|---|---|
| `artsy/warm/artsy_gallery` | GUARD_OK | GUARD_OK | GUARD_OK | PRIMARY_PASS (모든 seed guard fired or non-violation) |
| `artsy/warm/artsy_online` | GUARD_OK | GUARD_OK | GUARD_OK | PRIMARY_PASS |
| `saatchi/cold/saatchi_online` | GUARD_OK | GUARD_OK | GUARD_OK | PRIMARY_PASS |
| `saatchi/warm/saatchi_online` | GUARD_OK | GUARD_OK | GUARD_OK | PRIMARY_PASS |

GUARD_VIOLATION 0건. Saatchi cold는 sample boundary effect로 refit factor 변동 (seed 31337=1.0 / 7=1.0 / 13=0.955) — 단 prereg 정의상 guard implementation 정합 → GUARD_OK 유지.

## 4. 채택 결정 (per §3.5)

**Per-source verdict**:
- `artsy`: 1 cell `ADOPT_with_caveat` + 1 cell `NEEDS_MORE_DATA` → **NEEDS_MORE_DATA** (전 cell ADOPT 미달)
- `saatchi`: `N/A_no_load_bearing` (모든 cell shipped=1.0)

**Overall verdict**: **NEEDS_MORE_DATA**.

### 4.1 권고 (Reprod.C codex R5 사후 검수 합의)

**Codex R5 verdict (NEEDS DECISION ALIGNMENT → Strategy A 채택)**:
- Implementation prereg-faithful / 결정 logic mechanically correct.
- R4 in-sample bias caveat **해소 확인** (Reprod Δ_shipped=+5.46 → OOS Δ_shipped=−3.86 / 같은 seed 31337 / baseline 3.21 → 19.80 = OOS scale). Reprod FAIL이 method artifact였다는 가설 강하게 지지.
- **Strategy A**: 본 cycle은 NEEDS_MORE_DATA 그대로 commit + 전 채택 OFF 유지. artsy_online standalone partial adoption은 본 cycle scope 외 / 별도 narrow canary prereg에서 결정.
- artsy_gallery variance는 small cell + 적은 holdout artist (16-22 per seed)로 합당 / implementation 결함 X. multi-seed N 확대 (N=5 또는 N=7)가 우선.
- price-tier / seniority stratification 추가 X (estimand 변경 / 본 cycle scope 외).
- Saatchi adoption은 non-1.0 shipped factor가 별도 cycle (Phase 3 HP tuning)에서 surface 한 후만 가능.

### 4.2 채택 결정 요약

| 영역 | 결정 |
|---|---|
| 본 cycle 내 채택 | **전 채택 보류** (NEEDS_MORE_DATA / Strategy A) |
| 운영 unified bundle 변경 | X (prereg §5 out-of-scope) |
| Default OFF | 유지 |
| `artsy_online` standalone canary | 별도 narrow canary cycle 후보 (본 cycle scope 외) |
| `artsy_gallery` adoption | multi-seed N 확대 cycle 통과 후 결정 |
| `saatchi` adoption | Phase 3 (per-source HP) 결과 후만 가능 |

### 4.3 후속 cycle 후보 (R5 합의 시 우선순위)

1. **(i) Multi-seed N 확대 cycle** (uppermost priority): split_seeds ∈ {31337, 7, 13, 23, 47} (N=5) 또는 {31337, 7, 13, 23, 47, 53, 71} (N=7). artsy_gallery의 NEEDS_MORE_DATA 해소 목표. 컴퓨트 ~15-25분 추가. 본 cycle script + prereg 그대로 multi-seed 확장만 변경.
2. **(ii) artsy_online narrow canary prereg**: 본 cycle ADOPT_with_caveat 결과 기반 / mode=canary 활성화 / 2주 shadow logging 비교 (PR2B-prereq.1 `2d3af98` 인프라 활용). 별도 PR / decision-binding for online cell only.
3. **(iii) Saatchi Phase 3 HP tuning cycle**: per-source HP tuning이 saatchi에서 non-1.0 factor 산출하는지 / 산출 시 OOS verification 적용. 본 cycle scope 외.

## 5. Reprod cycle vs OOS cycle 비교

| 항목 | Reprod (in-sample) | OOS (true OOS) | 의미 |
|---|---|---|---|
| Method | PR1 artifact 그대로 holdout 위 prediction | 80% pool 재학습 artifact 위 holdout prediction | OOS bias 제거 |
| Holdout baseline (artsy_gallery seed 31337) | 3.21 | 19.80 | 진짜 OOS 수준 |
| Δ_shipped (artsy_gallery seed 31337) | +5.46pp (FAIL) | −3.86pp (PASS) | 부호 반전 / shipped factor가 진짜 도움 됨 |
| Verdict overall | 채택 보류 (FAIL) | NEEDS_MORE_DATA | View B 가설 지지 |

→ Reprod cycle의 FAIL은 method-induced artifact였음 확인. OOS cycle에서 e3367ed의 shipped factor 채택 가능성 가시화 (artsy_online에서 명확 / artsy_gallery에서 추가 검증 필요).

## 6. 코덱스 자문 이력 (이어서)

prereg §7의 R1/R2/R3/R4 LGTM 후 본 cycle 실행. R5 사후 검수 결과:

| Round | Verdict | 핵심 |
|---|---|---|
| 5차 사후 검수 (`019e0bb1` resume) | **NEEDS DECISION ALIGNMENT → Strategy A 합의** | Implementation prereg-faithful / 결정 logic mechanically correct. R4 in-sample bias caveat 해소 확인 (Reprod FAIL = method artifact 가설 지지). Strategy A: NEEDS_MORE_DATA 그대로 commit + 전 채택 OFF / artsy_online은 별도 narrow canary prereg 후보 / artsy_gallery는 multi-seed N=5,7 확대 우선. |

### 6.1 R5 합의 사항

- **본 cycle commit**: prereg + script + holdout indices + results doc → 단일 commit (NEEDS_MORE_DATA verdict).
- **본 cycle 단독 운영 채택 X**: prereg §3.5 overall verdict 존중 / 전 채택 OFF 유지.
- **artsy_online narrow canary**: 본 cycle 결과 ADOPT_with_caveat 기반 / 별도 PR 후보 / 본 commit에 미포함.
- **artsy_gallery follow-up**: multi-seed N 확대 cycle (N=5 우선) — 본 cycle script 그대로 활용.
- **R4 in-sample bias caveat 해소**: 본 cycle OOS evaluation이 Reprod cycle의 method artifact를 명확히 입증.

## 7. 산출물

- ✅ `docs/calibration_per_source_oos_verification_prereg_20260509.md` (R1-R4 LGTM 잠금 / ~270 lines)
- ✅ `docs/calibration_per_source_oos_verification_results_20260509.md` (본 문서)
- ✅ `scripts/validate_per_source_calibration_oos.py` (~500 lines / ruff clean)
- ✅ `data/oos_holdout_20260509/{artsy,saatchi}_seed{31337,7,13}_holdout_indices.json` (6 files / split index serialized)
- ✅ `model_test_results/calibration_oos_20260509.json` (gitignored / 재현 가능)
