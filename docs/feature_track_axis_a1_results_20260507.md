# Feature Track Axis A.1 결과 보고서 — Cheap Categorical BORDERLINE

> **작성일**: 2026-05-07
> **사전등록 freeze**: `docs/feature_track_axis_a1_prereg_20260507.md` (2026-05-07, P0×3 + P1×4 + P2×1 fix 후 GO)
> **실험**: `experiments/structural_v1/feature_track_axis_a1.py` / `results/feature_track_axis_a1.json`
> **판정**: **BORDERLINE — Primary CI 만 미달, Hard gate ✓ / practical Δ ✓ → A.2 escalation (B안)**

## 0. 한 줄 요약 (의사결정자용)

> **Stage 6B FAIL 후 첫 PASS 후보 신호** — A.1 cheap categorical 4종 추가로 **overall -1.34%p / 저가 -0.98%p / mid-high -1.67%p / newly-warm -4.06%p** 모두 개선 방향. 단 single seed cluster bootstrap CI 상한 +1.04%p (걸침) → **BORDERLINE 판정** + step gate B안에 따라 **A.2 escalation**.
>
> **6B 와 정반대 패턴**: 6B = aggregate parity but low-slice harm / **A.1 = aggregate 개선 + low-slice 비악화 + newly-warm 큰 개선**.
>
> **저가 specific 신호 일부 발견** (코덱스 사전 evidence 상 기대 낮았던 결과 — Stage 4 단기 트랙 시그니처 부분 반박): cheap categorical features (gallery_name target encoding 등) 가 **저가 segment 의 식별력 일부 보강**. 그러나 seed-level violation rate 41/100 = 41% 로 여전히 **마지노선** (6B 의 66% 보다 낮으나 robust 신호 X).

## 1. 핵심 결과 (사전등록 §3 적용)

### 1.1 100-seed LAO MdAPE

| Metric | Baseline | A.1 | Δ (낮을수록 좋음) | Std |
|---|---|---|---|---|
| **Overall** | 38.03% | 36.70% | **-1.34%p** ✓ practical | 3.43%p |
| **Low (price < 5M)** | 38.29% | 37.31% | **-0.98%p** ✓ hard gate | 4.36%p |
| Mid/high (≥ 5M) | 38.00% | 36.33% | **-1.67%p** ✓ | — |
| **Newly-warm (Stage 3 외)** | 46.11% | 42.05% | **-4.06%p** ✓ (큰 개선) | — |

### 1.2 Cluster bootstrap (rep seed=0, n=2000)
- Δ overall mean: **-3.54%p** (single seed 결과)
- 95% CI: **[-8.31, +1.04]** — **0 걸침 (CI 상한 +1.04%p)**
- P(diff ≥ 0) = 0.0715

> **Primary CI 위치 명시 (6B 동일 caveat)**: Inferential CI 는 canonical seed=0 cluster bootstrap 기준 **보조 해석**. 100-seed 전체 평균 (-1.34%p, std 3.43%p) 가 더 robust effect size — single seed=0 의 -3.54%p 는 운 좋은 큰 개선 (std 3.43%p 의 ~2σ).

### 1.3 Seed-level Low violation rate (코덱스 P2 패턴 적용)

| 지표 | 결과 |
|---|---|
| **Low Δ > 0 violation rate** | **41/100 seeds (41.0%)** |
| Low Δ mean | -0.98%p |
| Low Δ std | 4.36%p |

→ **41% seeds 에서 여전히 low harm** (그러나 6B 의 66% 대비 25%p 개선). Hard gate 점추정 통과 ✓ but **분포가 0 걸침** — robust 신호 X.

### 1.4 사전등록 §3 PASS / BORDERLINE / FAIL 판정

> **Hard gate 정의 (사전등록 §2.8 단일 line)**: `Δ_low ≤ 0%p` (100-seed LAO mean 점추정 기준).
>
> **판정 rule**: Hard gate 위반 시 즉시 FAIL. Hard gate 통과 후 primary CI + practical 동시 충족 → PASS / 하나만 충족 → BORDERLINE / 둘 다 미달 → FAIL.

| 조건 | 결과 |
|---|---|
| 🔴 **Hard gate Δ_low ≤ 0%p** | **✓ (-0.98%p)** |
| Primary practical Δ ≤ -1.0%p | ✓ (-1.34%p) |
| Primary CI 상한 ≤ 0 | ✗ (+1.04%p, 0 걸침) |

→ **BORDERLINE (Primary CI 만 미달)** — Step gate B안 (A.2 escalation 허용) 적용.

## 2. 6B vs A.1 패턴 대조 (의사결정자 압축)

| Metric | Stage 6B (FAIL) | A.1 (BORDERLINE) | 패턴 |
|---|---|---|---|
| Overall Δ | -0.09%p | **-1.34%p** | A.1 = 6B 의 약 15배 개선 |
| Low Δ (hard gate) | **+1.29%p ✗** | **-0.98%p ✓** | **정반대 — A.1 이 저가 harm 해결** |
| Mid-high Δ | -1.04%p | -1.67%p | A.1 더 큰 개선 |
| Newly-warm Δ | +0.31%p (noise) | **-4.06%p** | **A.1 = 큰 개선** (composition shift 정반대 방향) |
| Low seed violation | 66/100 | 41/100 | A.1 = 25%p 감소 (여전히 noise 영역) |
| ICC mechanism | 0.81 ✓ but mis-targeted | N/A (architecture-only X) | A.1 = direct feature signal |

> **결론**: A.1 = **6B 의 mis-targeted partial pooling 과 달리 cheap categorical 이 식별력 일부 보강**. Stage 4 단기 트랙 시그니처 ("current inputs 분리력 부족") 가 **부분 반박** — 추가 features (특히 `gallery_name` target encoding) 가 의미 있는 신호.

## 3. A.1 의 의의 (정직 보고)

### 3.1 사전 evidence 상 기대 vs 결과
- **사전 expectation (코덱스 P1, prereg §1.2)**: Stage 4 단기 트랙 + 6A/6B 저가 systematic harm → "A.1 PASS 가능성 **낮음**" / "A.4-A.5 escalation 사실상 유력"
- **실제 결과**: A.1 100-seed mean -1.34%p / 저가 -0.98%p / Hard gate ✓ → **사전 expectation 부분 반박**
- → **저가 식별력 보강이 cheap categorical 만으로 일부 가능** (특히 `gallery_name` target encoding 의 효과 — gallery 별 가격대 prior 가 새 신호)

### 3.2 그러나 BORDERLINE 인 이유
- **Primary CI 상한 +1.04%p**: single seed cluster bootstrap (n=2000) 기반 — 운 좋게 큰 개선 seed=0 에 의한 noise (CI 가 wide [-8.31, +1.04])
- **Seed-level low violation 41%**: 100 seeds 중 41 seeds 에서 여전히 low harm — 분포 자체는 0 걸침
- **사전등록 PASS 기준 = primary CI 상한 ≤ 0 (단일 line)** → CI 미달 → 즉 결정 보류 = BORDERLINE

### 3.3 A.2 escalation 정당성
- **사전등록 §3.2 BORDERLINE → A.2 escalation** (B안 — Step gate)
- A.2 = artist popularity 4종 (followers / for_sale / is_p1 / year_made) — **시점 정합성 검증 필수**
- A.2 의 baseline = 운영 모델 F4 (A.1 features drop, alternative hypothesis sequence)
- → A.2 가 PASS 면 운영 채택 후보 / FAIL/BORDERLINE 시 A.3 escalation

## 4. 운영 영향 X

### 4.1 본 cycle 운영 spec 변경 X
- 사전등록 §3.2 BORDERLINE → **운영 spec §1-§16 cold rollout 변경 X** (사전등록 PASS 기준 미달 — point estimate 만으로 운영 채택 X)
- 분기 B (calibration only) 운영 그대로 유지
- A.1 features 운영 spec 추가 X — A.2 / A.3 / A.4 / A.5 escalation 결과 통합 후 재평가

### 4.2 Step gate B안 적용
- A.1 BORDERLINE → A.2 prereg freeze 진입 (alternative hypothesis sequence — A.1 features drop)

## 5. Limitations / 정직 보고

- **Single seed cluster bootstrap CI noise**: rep seed=0 의 -3.54%p 는 100-seed mean -1.34%p 의 ~2σ outlier — single seed CI 는 wide / 100-seed 평균이 더 신뢰할 만함 (6B 와 동일 issue)
- **Seed-level low violation 41% 의 의미**: hard gate 점추정 통과 ✓ but 분포 0 걸침 — robust 한 저가 specific 효과 X (마지노선 신호)
- **`gallery_name` target encoding 의 effect attribution 미확인**: 4종 features 중 어느 것이 가장 큰 기여인지 분해 X (본 cycle 미목표 — A.2 escalation 후 재검토 가능)
- **Newly-warm -4.06%p 의 의미**: composition shift (Stage 4 +0.25%p) 정반대 — Stage 3 외 작가 (newly-warm pool) 가 특히 cheap categorical 신호로 개선. 그러나 작품 수 적어서 std 큼 (해석 caveat)

### 5.1 A.1 의 effect breakdown 미수행 (코덱스 P2 권고 — 향후 A.2 후)
- 본 cycle 측정 X
- 추후 권고: 추가 분석 시 (a) feature ablation (cheap 4종 중 1종씩 drop) (b) gallery_name encoding 단독 vs 다른 categoricals 단독 비교

## 6. 다음 단계 (Step gate B안)

1. ✅ A.1 결과 보고 — 본 commit
2. ⏳ Deviation log: 본 cycle entry (none, 정상 흐름) + A.2 escalation 결정
3. ⏳ 코덱스 결과 검수 — BORDERLINE 정당성 + A.2 진입 spec
4. ⏳ A.2 prereg freeze 진입 (artist popularity 4종, 시점 정합성 검증 후)
5. ⏳ (사용자 결정) A.2 진입 시점 / Cold Phase A shadow 시작 여부

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6B 결과 최종 검수 (2026-05-07) | architecture-only close → feature track |
| Feature track design draft 검수 (2026-05-07) | P0×2 / P1×6 / P2×1 |
| A.1 prereg freeze 검수 1차 (2026-05-07) | HOLD → P0×3 + P1×4 + P2×1 fix → GO |
| **A.1 결과 보고 검수 (예정)** | BORDERLINE 정당성 + A.2 escalation 권고 |

## 8. 참조

- A.1 prereg: `docs/feature_track_axis_a1_prereg_20260507.md`
- Feature track design: `docs/feature_track_design_20260507.md`
- Stage 6B close: `docs/stage6b_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
