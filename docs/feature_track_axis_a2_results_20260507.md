# Feature Track Axis A.2 결과 보고서 — Artist Popularity FAIL

> **작성일**: 2026-05-07
> **사전등록 freeze**: `docs/feature_track_axis_a2_prereg_20260507.md` (2026-05-07)
> **실험**: `experiments/structural_v1/feature_track_axis_a2.py` / `results/feature_track_axis_a2.json`
> **판정**: **FAIL (🔴 Hard gate Δ_low > 0 위반)** → A.3 escalation (Step gate B안)

## 0. 한 줄 요약 (의사결정자용 — 코덱스 framing 톤 다운 v2)

> **A.2 artist popularity bundle (4종) 은 cold-start LAO 에서 baseline 대비 실질 개선을 만들지 못했고, prereg hard gate 를 미세하게 위반해 FAIL** (코덱스 권고 framing). Overall **-0.21%p (사실상 동등)** + 저가 **+0.05%p (마진 5bp 위반)** + Mid-high -0.47%p + Newly-warm -0.81%p.
>
> **Provisional 메커니즘 가설 (입증 X — A.3-A.5 에서 재시험 필요)**: A.2 bundle 의 결과는 single-snapshot artist-level features 가 cold-start LAO 에서 효과 약함을 **시사** (Stage 6B partial pooling 의 random intercept 무력화 패턴과 유사). 그러나 본 실험은 4-feature bundle 단일 add-on test 이며 `year_made` 처럼 artist-binding 이 아닌 항목도 포함 → "artist-binding 신호 일반이 무력" 으로 일반화 X.
>
> **A.1 vs A.2 — working hypothesis (입증 X)**:
> - A.1 (cross-artist signal — 작품 분류 + 갤러리): BORDERLINE (promising but not decision-grade)
> - A.2 (artist-binding 추정 — popularity bundle): FAIL (this spec, this evaluation)
> - → Working hypothesis: "Cold-start LAO 에서 유효한 신호는 cross-artist applicable 가능성" → A.3 (geometry, 더 직접적인 artwork-level falsification step) 에서 재시험
>
> **운영 영향 X**: A.2 bundle 운영 spec 추가 X / 운영 모델 (F4 + spline + Huber) + 분기 B (calibration only) 그대로 유지. **운영 F4 의 `artist_total_works` 효용 재평가 = 별도 ablation 필요** (본 결과로 추론 jump 금지, 코덱스 P1).

## 1. 핵심 결과 (사전등록 §3 적용)

### 1.1 100-seed LAO MdAPE

| Metric | Baseline | A.2 | Δ (낮을수록 좋음) |
|---|---|---|---|
| **Overall** | 38.03% | 37.82% | **-0.21%p** (사실상 동등) |
| **Low (price < 5M)** | 38.29% | 38.34% | **+0.05%p** ⚠️ Hard gate 위반 |
| Mid/high (≥ 5M) | 38.00% | 37.54% | -0.47%p |
| Newly-warm (Stage 3 외) | 46.11% | 45.31% | -0.81%p |

### 1.2 Cluster bootstrap (rep seed=0, n=2000, 진짜 cluster bootstrap A.1 v2 fix)
- Δ overall mean: **-0.39%p** (single seed 결과)
- 95% CI: **[-3.85, +3.03]** — 0 걸침 (참고만)
- **99% CI (α=0.01 Bonferroni 5 step decision rule): [-5.40, +4.47]** — 0 걸침 (CI 상한 +4.47%p)
- P(diff ≥ 0) = 0.4240

### 1.3 Seed-level Low violation rate

| 지표 | 결과 |
|---|---|
| **Low Δ > 0 violation rate** | **45/100 seeds (45.0%)** |
| Low Δ mean | +0.05%p |
| Low Δ std | 4.49%p |

→ 45 seeds 에서 low harm + mean +0.05%p 위반 — Hard gate 점추정 위반 = **즉시 FAIL**.

> **A.1 (41/100) vs A.2 (45/100) 비교 caveat (코덱스 P2)**: 차이 +4%p 의 95% CI ≈ [-9.7%p, +17.7%p] — **robust difference X** (sample 충돌 가능성 큼). "A.1 보다 더 나쁘다" 단정 X — **사실상 비슷한 분포** 로 봐야 정직.

### 1.4 사전등록 §3 PASS / BORDERLINE / FAIL 판정

> **Hard gate 정의**: `Δ_low ≤ 0%p` (100-seed LAO mean 점추정 기준).
> **Decision rule**: Hard gate 위반 시 즉시 FAIL — primary / secondary 무관.

| 조건 | 결과 |
|---|---|
| 🔴 **Hard gate Δ_low ≤ 0%p** | **✗ (+0.05%p)** |
| Primary 99% CI 상한 ≤ 0 (α=0.01 decision) | ✗ (+4.47%p) |
| Primary 95% CI 상한 ≤ 0 (참고만) | ✗ (+3.03%p) |
| Primary practical Δ ≤ -1.0%p | ✗ (-0.21%p) |

→ **🔴 Hard gate 위반 → 즉시 FAIL** (사전등록 §3.3) — primary / secondary 모든 조건 동시 미달 (decisive).

## 2. A.1 vs A.2 비교 (Working hypothesis, 코덱스 P1 — 입증 X)

| 지표 | A.1 (BORDERLINE) | A.2 (FAIL) |
|---|---|---|
| Overall Δ | -1.34%p ✓ practical | -0.21%p (사실상 동등) |
| Low Δ (hard gate) | -0.98%p ✓ | +0.05%p ✗ |
| Mid-high Δ | -1.67%p | -0.47%p |
| Newly-warm Δ | -4.06%p | -0.81%p |
| 99% CI 상한 | +3.58%p (참고용 미달) | +4.47%p (decisive 미달) |
| Seed-level low violation | 41/100 | 45/100 (~4%p, robust difference X) |
| 판정 | BORDERLINE → escalation | FAIL → escalation |

> **Working hypothesis (입증 X — 코덱스 P1)**: A.1 (cross-artist signal: 작품 분류 + 갤러리) 에서 약한 promising signal 관측 / A.2 (artist-binding 추정 popularity bundle) 에서는 이 spec / 이 평가에서 실질 개선 X. 6B partial pooling 의 random intercept 무력화 패턴과 **유사**하나, A.2 bundle 단일 결과로 "artist-binding 신호 일반 무력" 으로 일반화 X. **A.3-A.5 escalation 에서 재시험 필요**.

## 3. Provisional 메커니즘 분석 (코덱스 P1 — working hypothesis, 입증 X)

### 3.1 왜 A.2 bundle 이 near-null net effect 였나? (가설 수준)
- **Single-snapshot artist features**: followers / for_sale / is_p1 = artist 당 unique 1.00 (single snapshot), train 에서 학습된 weight 가 unseen artist 에 generalization 가능성 약함
- **Cold-start LAO 평가 구조의 추정 한계**: test artists 가 train 에 0 작품 → artist-binding feature 의 generalization 약할 가능성 (입증 X — bundle 단일 결과)
- **`year_made` 가능성**: 작품 제작년도는 모든 작품에 적용 가능, birth_year_centered (운영 F4) 와 일부 redundant 가능
- → **A.2 bundle 이 이 spec / 이 평가에서 실질 개선 만들지 못했다** (provisional 결론, 코덱스 framing)

### 3.2 6B vs A.2 패턴 — 유사하나 동일 단정 X
- 6B (partial pooling): ICC 0.81 ✓ but cold-start LAO 무력 → "mis-targeted"
- A.2 (popularity bundle): single-snapshot artist features → **유사 패턴 시사** (입증 X)
- → **Working hypothesis**: artist-binding 신호 일부가 cold-start LAO 에서 약할 가능성 / **A.3-A.5 에서 재시험 필요**

### 3.3 A.1 vs A.2 framing (working hypothesis, 입증 X)
- A.1 (작품 분류 + 갤러리): cross-artist applicable signal → 약한 개선 관측 (BORDERLINE)
- A.2 (artist popularity bundle): artist-binding 추정 → near-null net effect (FAIL)
- → A.3 (geometry — aspect ratio + 2D vs 3D) = artwork-level signal → working hypothesis 의 더 직접적 falsification step

## 4. 운영 영향 X

- 본 A.2 FAIL → **운영 spec §1-§16 변경 X** / artist popularity features 운영 채택 X
- 분기 B (calibration only) 운영 그대로 유지
- Step gate B안 적용: A.2 FAIL → **A.3 prereg freeze 진입** (geometry, A.2 features drop = alternative hypothesis sequence)

## 5. Limitations / 정직 보고 (코덱스 P1 톤 다운)

- **시점 정합성 caveat 적용 후 near-null net effect**: 운영 F4 의 `artist_total_works` 와 동등 snapshot spec 인 features (followers / for_sale / is_p1) 가 본 evaluation 에서 약함 — 단 **`artist_total_works` 자체 효용 평가는 별도 ablation 필요** (본 결과로 운영 F4 약화 추론 = inference jump, 코덱스 P1 — **운영 spec 재평가 트리거 X**)
- **`year_made` 단독 효과 미측정**: 4종 features 중 어느 것이 noise / 미세 negative driver 인지 분해 X (effect attribution 본 cycle 비목표)
- **Single-seed CI vs 100-seed mean discrepancy**: A.1 동일 caveat — single seed=0 의 -0.39%p 도 wide CI 노출 / 100-seed mean -0.21%p 가 더 robust effect

### 5.1 Effect attribution 미수행 (코덱스 P2 권고 — 향후 escalation 후)
- 본 cycle 측정 X (4종 동시 추가만 평가)
- 추후 권고: Axis A 종결 후 ablation (followers 단독 / for_sale 단독 / is_p1 단독 / year_made 단독 비교)

## 6. 다음 단계 (Step gate B안)

1. ✅ A.2 결과 보고 — 본 commit
2. ⏳ Deviation log: 본 cycle entry (none, 정상 흐름) + A.3 escalation 결정
3. ⏳ 코덱스 결과 검수 (선택)
4. ⏳ A.3 prereg freeze 진입 (geometry — aspect ratio + 2D vs 3D, A.2 features drop)
5. ⏳ (사용자 결정) A.3 진입 시점

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6B 결과 최종 검수 (2026-05-07) | architecture-only close → feature track |
| Feature track design draft 검수 (2026-05-07) | P0×2 / P1×6 / P2×1 |
| A.1 prereg freeze 검수 (2026-05-07) | HOLD → P0×3 + P1×4 + P2×1 fix → GO |
| A.1 결과 보고 검수 (2026-05-07) | HOLD → P0×2 + P1×4 fix → v2 |
| **A.2 prereg freeze (2026-05-07)** | A.1 v2 lessons 사전 반영 (cluster bootstrap fix / 99% CI / 시점 정합성 caveat) |
| **A.2 결과 보고 검수 (2026-05-07)** | **FAIL 정당성 OK + A.3 escalation GO**. P1 ×4 (메커니즘 톤 / artist_total_works inference jump / A.1 vs A.2 working hypothesis / 의사결정자 framing) + P2 ×2 (45 vs 41 robust difference X / effect attribution 톤) — 본 v2 commit 일괄 반영 |

## 8. 참조

- A.2 prereg: `docs/feature_track_axis_a2_prereg_20260507.md`
- A.1 결과: `docs/feature_track_axis_a1_results_20260507.md` (BORDERLINE → A.2 escalation)
- Feature track design: `docs/feature_track_design_20260507.md`
- Stage 6B close: `docs/stage6b_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
