# D1-extended: D1.Z2 + D1.split + D1.alt2 Combined Prospective Cycle (R1 HOLD → amendment / decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: D1.Y (`d774938`) HOLD_n32_default + D1.Z+alt (`a564e2e`) hypothesis-generating finding
> **Decision binding**: ✅ YES — 새 prospective cycle (fresh N=10 seeds preregister / threshold-shopping 회피 / R1 HOLD amendment 정합 strict primary)
> **R1 amendment 반영** (codex P0+P1.1+P1.2 정합 / Q7 risk acknowledgment):
> - Strict primary 유지 (bootstrap → secondary corroboration only / decision object 변경 X)
> - N=5 → **N=10** fresh seeds (codex P1.1)
> - ADOPT_canary 최소 조건 강화: lax-1 PASS 필수 (codex P1.2)
> - Codex Q7 우려 명시: D1 axis는 PR-WARM-B (clean positive)와 conflict / 본 cycle은 last-attempt scientific completeness

## 1. Goal

D1.Z+alt analysis (non-binding) finding:
- Bootstrap CI cold_overall PASS (mean -1.16 / CI95 [-1.71, **-0.60**] / 95% confident negative)
- Threshold relaxation 단독 efficacy 작음 (strong outliers 잔존 / +0.8 / +1.0 모두 FAIL)
- 모든 cell mean negative (saatchi CI 0 포함하지만 mean -0.64)

본 cycle = **fresh N=10 seeds + strict primary endpoint preregister + bootstrap secondary corroboration**:

- **D1.Y rule strict (Primary / R1 amendment 정합)**: D1.Y와 동일 strict per-seed aggregate (champion swap 의도 보존 / single-bad-split user impact frequency)
- **D1.alt2 Bootstrap CI (Secondary corroboration / not binding alone)**: cold_overall hierarchical CI / strict primary와 정합 검증
- **D1.Z2 (Tertiary record)**: relaxed threshold sensitivity (+0.8 / +1.0) 정합 검증
- **D1.split (Tertiary informational)**: per-source separate decomposition (artsy heavy-tail vs saatchi)

PASS 시: 운영 best_params 교체 권고 (D1.Y와 동일 strict primary / fresh N=10 corroborates).
FAIL 시: D1 axis 완전 종결 (strict primary 2 cycles 연속 fail).
INCONCLUSIVE 시: 추가 cycle 또는 cycle methodology 재고.

본 cycle 정당성 (codex R1 HOLD 정합 amendment):
- ✅ **Fresh N=10 seeds** (이전 cycle 비중복 / codex P1.1 / N=5 too small fix)
- ✅ **Strict primary 유지** (codex P0 / decision object 변경 X / D1.Y와 동일 framework)
- ✅ **Bootstrap secondary corroboration** (codex P0 / supplementary only / standalone PASS 발동 X)
- ✅ **ADOPT_canary 최소 조건 강화** (codex P1.2 / lax-1 PASS 필수)
- ✅ **D1.Z+alt finding과 분리** — non-binding hypothesis / 본 cycle은 fresh validation 검증
- ⚠️ **D1 axis last-attempt acknowledgment** (codex Q7): D1.Y 이미 fail / 본 cycle도 fail 시 abandon path / PR-WARM-B (clean positive line)와 conflict 인정

## 2. Method

### 2.1 Search 미실행 정합 (D1.Y 정합)

D1.X / D1.Y 모두 사용한 retuned best_params (`model_test_results/n32_champion_retuned_best_params.json` / commit d06ea22) 그대로 재사용. 새 search 없음 / validation only.

### 2.2 Fresh seeds (R1 P1.1 amendment / N=5 → N=10)

`split_seed ∈ {631, 661, 691, 727, 757, 787, 821, 853, 877, 907}` — 모두 prime / 이전 cycle 비중복 검증.

10 seeds × ~50s = ~10분 wall (compute cheap / D1.Y와 동일 path).

### 2.3 Validation 절차 (D1.Y validate_seed 정합)

각 seed × `optuna_n32_champion_retune.py:validate_seed`:
- GroupShuffleSplit(test=0.20, random_state=seed, groups=artist_slug) cold
- train_test_split(test=0.20, random_state=seed) on warm subset
- Default + retuned base 학습 / 20% holdout 위 prediction
- Per-cell MdAPE: cold_overall / cold_artsy / cold_saatchi / warm
- Δ_cell = retuned − default

### 2.4 Strict Primary endpoint (R1 amendment / codex P0 / D1.Y rule preserved)

**N=10 strict per-seed aggregate** (D1.Y와 동일 framework / decision object 변경 X):

Per-seed verdict (G1-G4 strict / `validate_seed`):
- PASS: G1 (Δ_cold_overall ≤0) + G2 (artsy ≤+0.3) + G3 (saatchi ≤+0.3) + G4 (warm ≤+0.1)
- INCONCLUSIVE: Δ_cold_overall ∈ (0, +0.3] + G2/G3/G4 PASS
- FAIL: 임의 G FAIL

N=10 aggregate (D1.Y R1 P1.1 정합):
- PASS × 10 → PASS
- PASS × 9 + 1 outlier (INC OR FAIL) → PASS_with_caveat
- PASS × 8 + INCONCLUSIVE × 2 (FAIL=0) → PASS_with_caveat
- FAIL × 2 이상 → FAIL
- 기타 → INCONCLUSIVE

### 2.5 Bootstrap CI Secondary corroboration (R1 amendment / codex P0 / not binding alone)

**N=10 paired percentile bootstrap on mean Δ per cell**:
- n_boot = 10000 / 95% CI percentile method
- Hierarchical (R1 Q3): cold_overall primary metric / artsy/saatchi/warm guards

**Bootstrap status (informational / corroboration)**:
- bootstrap_PASS: cold_overall CI95 upper ≤ 0
- bootstrap_INCONCLUSIVE: cold_overall CI95 upper ∈ (0, +0.5]
- bootstrap_FAIL: cold_overall CI95 upper > +0.5

**Role (codex P0)**: strict primary와 corroboration. **Bootstrap PASS 단독 ADOPT 발동 X**. Strict primary FAIL → 무조건 HOLD (bootstrap PASS여도).

### 2.6 D1.Z2 Tertiary record: Threshold sensitivity

**N=10 strict aggregate at 3 tiers**:

| Tier | G2 / G3 | G1 / G4 | Role |
|---|---|---|---|
| strict (Primary) | +0.3 / +0.3 | 0 / +0.1 | binding primary |
| lax-1 | +0.8 / +0.8 | 0 / +0.1 | ADOPT_canary 최소 조건 (R1 P1.2) |
| lax-2 | +1.0 / +1.0 | 0 / +0.1 | record only |

**Role (R1 P1.2)**: lax-1 PASS = ADOPT_canary 최소 조건. lax-1 FAIL이면 canary 발동 X (→ NEEDS_MORE_DATA / HOLD).

### 2.7 D1.split Tertiary informational: Per-source decomposition

각 seed에서 artsy / saatchi 별도 mean Δ + N=10 bootstrap CI95.

**Role**: split variance 큰 cell 식별 / 후속 source-conditional cycle 정보 제공 (본 cycle decision direct binding X / informational only).

### 2.8 Combined adoption decision (R1 amendment / codex P0+P1.2 정합)

**Strict primary가 binding** (Bootstrap secondary corroborates / does not bypass strict / lax-1 minimum for canary):

| Strict Primary | Bootstrap Secondary | Lax-1 (D1.Z2) | Combined Decision |
|---|---|---|---|
| **PASS** | bootstrap_PASS | any | **ADOPT (full migration)** |
| **PASS** | bootstrap_INC/FAIL | any | **ADOPT_canary** (strict PASS but bootstrap weak / canary 보수적) |
| **PASS_with_caveat** | bootstrap_PASS | PASS at lax-1 | **ADOPT_canary** (R1 P1.2 / 3-way confirmation) |
| **PASS_with_caveat** | any | FAIL at lax-1 | **NEEDS_MORE_DATA** (R1 P1.2 / lax-1 minimum 미달) |
| **INCONCLUSIVE** | any | any | **NEEDS_MORE_DATA** |
| **FAIL** | any | any | **HOLD / D1 axis 완전 abandon** (codex Q7 정합) |

**핵심 (R1 codex amendment)**:
- Strict primary FAIL → 무조건 HOLD (bootstrap PASS여도 / D1 axis abandon path)
- ADOPT_canary 최소 조건 (PASS_with_caveat 시) = 3-way confirmation (strict + bootstrap + lax-1 모두 PASS)
- Strict-only PASS (bootstrap weak) → canary 보수적 (full migration X)
- bootstrap mean-CI는 strict primary 의도 (single bad split user impact)와 다른 object — corroboration only

## 3. Output

- `docs/d1_extended_prospective_prereg_20260510.md` (본 문서)
- `docs/d1_extended_prospective_results_20260510.md`
- `scripts/d1_extended_validation.py` (D1.Y `optuna_n32_champion_retune.validate_seed` 재사용 / 10 fresh seed validation + bootstrap + threshold sensitivity + per-source)
- `data/d1_extended_holdout_20260510/seed{631,661,691,727,757,787,821,853,877,907}_holdout_indices.json`
- (gitignored) `model_test_results/d1_extended_results.json` (per-seed + bootstrap + threshold + per-source 종합)

## 4. Out-of-scope

- ❌ 새 Optuna search (D1 retuned params 그대로)
- ❌ 새 threshold rule formalization (본 cycle은 sensitivity record / formalization은 별도 amendment)
- ❌ Source-conditional model retune (D1.split decomposition만 / 모델 변경 X)
- ❌ Bootstrap method 다른 형태 (BCa 등) — percentile method R1 답변 정합

## 5. 한계 / Risk

- **N=10 sample (R1 amendment)**: D1.Y와 동일 size / strict per-seed aggregate primary 정합. Bootstrap CI는 corroboration only (R1 P0).
- **Bootstrap secondary risk acknowledgment**: codex R1 P1.1 warning — bootstrap mean-CI ≠ strict guard 의도. 본 cycle에서 bootstrap은 secondary corroboration only / strict primary가 binding.
- **Strong outlier 잔존 가능성**: D1.Y에서 30% bad-seed rate / 본 10 fresh seed에서도 비슷 rate 가능 → strict primary FAIL 가능성 높음 (codex Q7 prediction 정합 / D1 axis abandon path 시작).
- **Compute cheap**: ~10분 wall (10 fresh seed × ~50s validation / D1.Y 정합 / search 없음).

## 6. PR-WARM-B Deployment Conflict (R1 codex Q7 / D1.Y prereg §2.7 정합)

D1-extended ADOPT 시 운영 stack 영향:
- **D1 retuned warm XGB** (boost=1876 / depth=8 / lr=0.087 / mcw=9): cold + warm joint retune
- **B (PR-WARM-B) retuned warm XGB** (boost=947 / depth=9 / lr=0.125 / mcw=11): warm only retune
- 둘은 다른 best_params → simultaneous deploy 시 conflict

**충돌 해결 (R1 codex Q7 답변 정합)**:
- D1-extended PASS 시 control = post-B production baseline (B-retuned warm + default cold)
- D1-extended PASS 시 D1 retune은 cold path (CB) + warm path (XGB)를 새 best_params로 모두 변경
- B의 warm retune은 D1 warm retune으로 대체 (D1이 cold + warm 모두 retune이라 B-only는 D1 부분집합 X / 둘은 별도 best_params)
- Stage 4 canary 시 D1 vs B 비교 metric 명시 / 의사결정 시점에 baseline 정합 명시

본 cycle 시점 = PR-WARM-B Stage 1+2만 commit (Stage 3-5 운영팀 의존 / 미진행) → control = legacy stack (default cold + default warm). 운영 결정 시점 baseline 명시 필요.

## 7. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전** | **HOLD** | P0 (bootstrap → primary 승격은 success criterion 재정의 / strict 유지) + P1.1 (N=5 → N=10) + P1.2 (decision table 너무 permissive / canary lax-1 PASS 최소) + Q7 strong recommendation: D1 axis abandon |
| **R2 사전 (post-amendment)** | (예정) | strict primary + N=10 + lax-1 canary minimum 정합 검증 |
| R3 사후 | (예정) | 결과 검수 / 채택 결정 |

**R1 amendment 반영 항목**:
1. **P0 fix**: Strict primary 유지 (D1.Y rule preserved) / Bootstrap → secondary corroboration (decision object 변경 X)
2. **P1.1 fix**: N=5 → **N=10** fresh seeds (compute cheap / under-power 회피)
3. **P1.2 fix**: ADOPT_canary 최소 조건 강화 = strict PASS_with_caveat + bootstrap PASS + lax-1 PASS (3-way confirmation)
4. **Q7 acknowledgment**: D1 axis last-attempt / FAIL 시 abandon path / PR-WARM-B (clean positive line)와 conflict 인정 / 본 cycle = scientific completeness 측면 fresh prospective 검증

## 8. 결론 (R1 amendment 반영)

D1-extended = **새 prospective cycle** (fresh **N=10** seeds + **strict per-seed aggregate primary** + bootstrap CI secondary corroboration). D1.Z+alt analysis-only finding을 hypothesis로, 본 cycle 결과로 binding decision.

**Primary (binding / R1 P0)**: D1.Y rule strict per-seed aggregate (G1-G4 / champion swap 의도 보존).
**Secondary (corroboration / R1 P0)**: bootstrap CI cold_overall hierarchical (not binding alone).
**Tertiary record (R1 P1.2)**: lax-1 (+0.8) threshold = ADOPT_canary 최소 조건.
**Tertiary informational**: per-source decomposition (artsy / saatchi / 후속 cycle 정보).

**Compute**: ~10분 wall (10 fresh seed × ~50s validation / D1 retuned params 재사용 / search 없음).

후속 별도 cycle (본 cycle 결과 따라 추가 결정):
- Strict FAIL → **D1 axis 완전 abandon** (codex Q7 정합 / 가장 가능성 큰 시나리오)
- Strict PASS / PASS_with_caveat → ADOPT 또는 ADOPT_canary deployment (PR-WARM-B와 conflict 처리 필요)
- INCONCLUSIVE → 추가 cycle 또는 D1 axis abandon
