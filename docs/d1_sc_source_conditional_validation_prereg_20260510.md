# D1.SC: Source-Conditional Validation Cycle (R1 amendment / decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: PR1 v1 source-conditional artifacts (commit `f74f73b`) + D1-extended (commit `9f7be57`) HOLD_D1_axis_abandon
> **Decision binding**: ✅ YES — Source-conditional CB serving (vs unified CB default) 채택 결정
> **R1 amendment 반영** (codex P0 + P1×2):
> - P0 fix: candidate AND baseline 둘 다 80% pool retrain (fair comparison / in-sample bias 회피)
> - P1.1 fix: per-source binding primaries (artsy_primary / saatchi_primary) for partial migration
> - P1.2 fix: 명시 serving contract — cold rows route by source-specific CB / warm rows use unified XGB (PR-WARM-B와 orthogonal 명시)

## 1. Goal

D1 axis 4 cycle 누적 fail 후 codex Q7 추천 = "D1 abandon / B + source-conditional 우선". 본 cycle = **PR1 v1 source-conditional 운영 채택 가능성 검증**:

- **PR1 v1 (commit f74f73b)**: artsy / saatchi 별도 dataset 학습 / **default best_params 그대로** (HP retune X / data partitioning만)
- 운영 시점 = PR2A (`source_router.py` / commit 938d585) default OFF 상태 / PR1 v1 artifacts 등록만

질문: PR1 v1 source-conditional이 unified default 대비 strict per-seed framework에서 PASS 가능한가?

PASS 시: PR1 v1 운영 적용 권고 (source router 활성화 / artsy / saatchi separate model serving).
FAIL 시: source-conditional axis abandon (split variance가 unified와 같거나 더 나쁨 / source split만으로 부족).
INCONCLUSIVE 시: full HP retune cycle (artsy / saatchi 각각 Optuna search) 후속 후보.

본 cycle 정당성:
- ✅ **Fresh N=10 seeds preregister** (D1.Y framework 정합 / threshold shopping 회피)
- ✅ **Strict primary** (D1.Y rule preserved / champion swap 의도 보존)
- ✅ **Bootstrap secondary corroboration** (codex R1 정합 / not binding alone)
- ✅ **PR1 v1 methodology validation with fresh per-seed retrain** (R1 P0 amendment / candidate AND baseline 둘 다 80% pool 위 fresh retrain / frozen PR1 v1 artifacts는 secondary shipped benchmark only)

## 2. Method

### 2.1 Default best_params 활용 (R1 amendment / fresh retrain per seed)

PR1 v1 artifacts (commit f74f73b)는 reference only / 본 cycle은 **fresh retrain per seed**:

**Best params**: 양 source 모두 default unified best_params (`integrated_v3_filtered_tuned_best_params.json`):
- CB: iter=1000 / depth=8 / lr=0.0953 / l2=1.63
- XGB: num_boost=3000 / depth=7 / eta=0.040

**Candidate vs baseline 차이**:
- **Candidate**: source-conditional CB (artsy-only CB on artsy pool / saatchi-only CB on saatchi pool) + unified warm XGB
- **Baseline**: unified CB (full pool) + unified warm XGB
- **공유**: unified warm XGB (warm 모든 작가 통합 학습 / 둘 다 동일)

**Secondary endpoint (record only)**: PR1 v1 frozen artifacts 위 fresh holdout prediction → "shipped artifact benchmark" / 본 cycle decision binding 직접 X.

### 2.2 Fresh seeds (R1 amendment 정합 / N=10)

`split_seed ∈ {941, 967, 991, 1009, 1031, 1049, 1069, 1093, 1117, 1129}` — 모두 prime / 이전 cycle 비중복 검증:

| Seed | D1.X | D1.Y | B | D3 | D3.B | D1-ext | 비고 |
|---|---|---|---|---|---|---|---|
| 941 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | fresh |
| 967 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | fresh |
| ... | | | | | | | (모두 fresh) |

### 2.3 Validation 절차 (per seed / R1 P0 fair retrain-vs-retrain)

각 seed:

1. **GroupShuffleSplit cold (test=0.20 / random_state=seed / artist groups)**
2. **Pool partitioning**:
   - 80% pool (cold): pool_artsy = pool ∩ artsy / pool_saatchi = pool ∩ saatchi
   - Warm 별도: train_test_split(test=0.20 / random_state=seed) on warm subset → pool_warm

3. **Candidate retrain (R1 P0 fix / fresh 80% pool every seed)**:
   - **artsy_cb**: CB train on `pool_artsy` (default best_params)
   - **saatchi_cb**: CB train on `pool_saatchi` (default best_params)
   - **unified_xgb_warm**: XGB train on `pool_warm` (default best_params) — warm path 공유

4. **Baseline retrain (fresh 80% pool every seed / D1.Y 정합)**:
   - **unified_cb**: CB train on `pool` (default best_params / full pool)
   - **unified_xgb_warm**: XGB train on `pool_warm` (default best_params) — candidate와 same artifact 공유

5. **Holdout prediction (R1 P1.2 / explicit serving contract)**:
   - **Cold rows (artist not in warm set)**:
     - Candidate: route by source → artsy_cb (artsy rows) / saatchi_cb (saatchi rows)
     - Baseline: unified_cb (all rows)
   - **Warm rows (artist in warm set)**:
     - 양쪽 모두: unified_xgb_warm (cold 루트와 별개 / orthogonal axis)

6. **Per-cell MdAPE**:
   - cold_overall / cold_artsy / cold_saatchi / warm
7. **Δ_cell = candidate − baseline**

**Compute estimate (per seed)**: artsy_cb (~5s on 7k rows) + saatchi_cb (~15s on 21k rows) + unified_cb (~20s on 28k rows) + unified_xgb_warm (~10s) = ~50s/seed. 10 seed × 50s = ~10분 wall.

### 2.4 Per-source binding primaries (R1 P1.1 amendment)

R1 P1.1 fix: source-specific deployment is only valid if source-specific rule is itself primary for that source. 따라서 본 cycle은 **3 binding primaries**:

**`artsy_primary`** (artsy migration binding):
- Per-seed verdict: Δ_cold_artsy 단독 평가
  - PASS: Δ_cold_artsy ≤ 0
  - INCONCLUSIVE: Δ_cold_artsy ∈ (0, +0.3]
  - FAIL: Δ_cold_artsy > +0.3
- N=10 aggregate (D1.Y R1 P1.1):
  - PASS × 10 → PASS
  - PASS × 9 + 1 outlier → PASS_with_caveat
  - PASS × 8 + INCONCLUSIVE × 2 (FAIL=0) → PASS_with_caveat
  - FAIL × 2 이상 → FAIL
  - 기타 → INCONCLUSIVE

**`saatchi_primary`** (saatchi migration binding / 동일 logic):
- Per-seed verdict: Δ_cold_saatchi 단독
- N=10 aggregate: 동일

**`overall_primary`** (full migration binding / D1.Y rule 정합):
- Per-seed verdict (D1.Y G1-G4 그대로):
  - PASS: G1 (Δ_cold_overall ≤0) + G2 (artsy ≤+0.3) + G3 (saatchi ≤+0.3) + G4 (warm ≤+0.1)
  - INCONCLUSIVE / FAIL: 동일
- N=10 aggregate: 동일

### 2.5 Bootstrap CI Secondary corroboration

N=10 paired percentile bootstrap on mean Δ per cell:
- n_boot = 10000 / 95% CI percentile
- Hierarchical: cold_overall primary / artsy / saatchi / warm guards

**Not binding alone** (D1-extended에서 입증됨 / strict primary FAIL 시 무조건 HOLD).

### 2.6 Combined decision (R1 P1.1 amendment / per-source binding primaries)

**3 primaries 각각 독립 binding** (partial migration is per-source primary, not derived from overall):

| `overall_primary` | `artsy_primary` | `saatchi_primary` | Bootstrap | Combined |
|---|---|---|---|---|
| PASS | PASS | PASS | bootstrap_PASS | **ADOPT (full migration / source router 활성화)** |
| PASS | PASS | PASS | bootstrap_INC/FAIL | **ADOPT_canary (full / 보수적)** |
| PASS_with_caveat | PASS / PASS_w_c | PASS / PASS_w_c | bootstrap_PASS | **ADOPT_canary (full)** |
| any | **PASS** | FAIL | any | **ADOPT_artsy_only_canary** (artsy만 source-conditional / saatchi unified 유지) |
| any | FAIL | **PASS** | any | **ADOPT_saatchi_only_canary** (saatchi만 source-conditional) |
| FAIL | FAIL | FAIL | any | **HOLD / source-conditional axis abandon** |
| 기타 | 기타 | 기타 | any | **NEEDS_MORE_DATA** |

**Partial migration (R1 P1.1 정합)**:
- artsy_primary PASS이고 saatchi_primary FAIL → artsy만 source-conditional 적용 / saatchi unified
- 반대도 동일 / per-source primary가 binding이므로 partial migration justified

**Bootstrap secondary (corroboration)**: 모든 ADOPT 시 bootstrap PASS 확인 권고 / not binding alone (R1 P0 / D1-extended 정합).

## 3. Output

- `docs/d1_sc_source_conditional_validation_prereg_20260510.md` (본 문서)
- `docs/d1_sc_source_conditional_validation_results_20260510.md`
- `scripts/d1_sc_validation.py` (PR1 v1 artifacts load + per-source inference + unified baseline retrain + aggregate)
- `data/d1_sc_holdout_20260510/seed{941-1129}_holdout_indices.json`
- (gitignored) `model_test_results/d1_sc_results.json`

## 4. Out-of-scope

- ❌ HP retune (artsy / saatchi 각각 Optuna search) — 본 cycle은 PR1 v1 그대로 / retune cycle은 별도 후속
- ❌ Source router PR2A.5 코드 변경 — validation only
- ❌ **Calibration: 양쪽 arm 모두 미적용** (R2 P1.2 amendment / fresh retrain context에서 PR1 v1 frozen calibration JSON carry-forward는 invalid). 본 cycle MdAPE는 raw model output (uncalibrated) 위. 운영 채택 시 calibration 별도 재추정 cycle 필요.
- ❌ Feature 변경 (N=32 그대로)

## 5. 한계 / Risk

- **PR1 v1 artifacts는 default params 사용**: HP retune 효과 측정 X / 본 cycle은 data partitioning 효과만 검증
- **Source split power 제한**: artsy 7,289 rows < unified 28,376 rows / source-specific 모델은 작은 dataset / over-fit risk
- **Cold path 한정**: warm path (XGB / 모든 작가 통합 학습) PR1 v1에서 source-specific X / warm 영향 평가 분리 필요
- **D1 axis 4 cycle fail context**: 본 cycle도 split variance가 같은 fail mode에 빠질 가능성 / codex Q7 정합으로 prepare for FAIL
- **Compute light**: ~15-20분 wall (PR1 v1 artifacts load + per-seed retrain unified baseline + predict)

## 6. PR-WARM-B와 interaction (R1 P1.2 amendment / explicit serving contract)

**Explicit serving contract** (R1 P1.2 fix):

| Path | Routing | Inference |
|---|---|---|
| **Cold rows** (artist_count<5 / not in warm set) | route by source (artsy / saatchi) | source-specific CB (artsy_cb / saatchi_cb) |
| **Warm rows** (artist_count≥5 / in warm set) | unified (no source split) | unified warm XGB (B-retuned 후 / 또는 default 현행) |

**PR-WARM-B와 orthogonal 정당성**:
- D1.SC = **cold path serving contract 변경만** (CB by source / warm 영향 X)
- PR-WARM-B = **warm path serving contract 변경만** (XGB B-retuned / cold 영향 X)
- 두 axis는 분리된 inference path → 동시 deploy 가능

**시나리오별 deploy**:
- D1.SC PASS + PR-WARM-B Stage 5 → **결합 deploy** (cold by source + warm B-retuned)
- D1.SC PASS / PR-WARM-B 미진행 → cold by source / warm default
- D1.SC FAIL / PR-WARM-B PASS → cold unified / warm B-retuned (B-only deploy)
- D1.SC FAIL / PR-WARM-B 미진행 → 현 운영 그대로

**중요**: PR1 v1 artifacts에 source-specific warm_artists / xgboost.json 포함되어 있음. 단 본 cycle serving contract는 **warm path는 unified XGB만** (PR1 source-specific warm artifact는 사용 X / orthogonality 보존).

## 7. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전** | **NEEDS FIX** | P0 (fair retrain-vs-retrain) + P1.1 (per-source binding primaries) + P1.2 (explicit serving contract) |
| **R2 사전 (post-amendment)** | (예정) | amendment 정합 검증 |
| R3 사후 | (예정) | 결과 검수 / 채택 결정 |

**R1 amendment 반영 항목**:
1. **P0 fix**: §2.1 / §2.3 — fresh retrain per seed (candidate AND baseline 둘 다 80% pool 위 / in-sample bias 회피)
2. **P1.1 fix**: §2.4 / §2.6 — per-source binding primaries (artsy_primary / saatchi_primary / overall_primary 3개 독립 / partial migration은 per-source primary로만)
3. **P1.2 fix**: §6 — explicit serving contract (cold by source CB / warm by unified XGB / orthogonal 명시)
4. Q4 답변: bootstrap corroboration only (binding X)
5. Q6 답변: 본 cycle 1 pass 가치 인정 (codex Q7 next axis 정합)
6. Q7 답변: SC2 (full HP retune) 진입 조건 = 본 cycle 최소 INCONCLUSIVE + credible positive signal (FAIL 시 axis abandon)

## 8. 결론

D1.SC = **PR1 v1 source-conditional artifact의 fresh N=10 seeds validation** (D1.Y framework 정합 / strict primary + bootstrap secondary).

- D1 axis는 4 cycle fail (D1.X / D1.Y / D1.Z+alt / D1-extended) → 완전 abandon
- Source-conditional (PR1 v1) 은 별도 axis (data partitioning approach)
- 본 cycle 결과로 PR1 v1 채택 결정

**Compute**: ~15-20분 wall (10 fresh seed × ~50-90s validation / unified baseline retrain + source-specific prediction).

**예상 (D1.Y precedent 기반)**:
- D1 retune (HP change) 30-80% bad-seed rate → fail
- D1.SC (data partition without HP change) 도 같은 split variance 이슈 가능성
- 단 source-specific 학습이 source-internal patterns 더 잘 학습할 가능성 존재

**Operational consequence (PR-WARM-B와 orthogonal)**:
- PASS 시: PR1 v1 채택 / source router 활성화 / cold path 변경 / PR-WARM-B와 별도 stack
- FAIL 시: source-conditional axis 종결 / unified 그대로 / PR-WARM-B만 deploy
