# Feature Track Axis A.5 결과 보고서 — Image Embedding FAIL (Axis A 종결)

> **작성일**: 2026-05-07
> **사전등록 freeze**: `docs/feature_track_axis_a5_prereg_20260507.md` (2026-05-07)
> **실험**: `experiments/structural_v1/feature_track_axis_a5.py` / `results/feature_track_axis_a5.json`
> **판정**: **FAIL (Δ > -0.3%p, 개선 미달, 마지막 step)** → **Axis A 전체 종결** (사용자 의사결정 영역 진입)

> ⚠️ **핵심 framing (코덱스 lessons 반영, evidence 톤)**: A.5 = **frozen A.5 spec (CLIP-ViT-B-32 + PCA K=10) 의 near-null net effect** — Hard gate 통과 ✓ but practical Δ 미달 + 99% CI 0 걸침. 코덱스 사전 권고 (A.5 HOLD / Axis A 종료) 와 결과 일치. **Axis A 5 step 종결**.

## 0. 한 줄 요약 (의사결정자용)

> **A.5 image embedding (CLIP-ViT-B-32, PCA K=10) FAIL** — Hard gate 통과 (-0.06%p, very close to 0) but Overall **+0.22%p (사실상 동등 또는 미세 악화)** + Mid-high +0.43%p + Newly-warm +0.14%p. **Axis A 마지막 step → 전체 종결**.
>
> **Cluster bootstrap (rep seed=0, n=2000)**: mean -1.01%p / 95% CI [-4.35, +2.29] / 99% CI [-5.39, +3.22] — 둘 다 0 걸침. P(diff ≥ 0) = 0.2705.
>
> **Axis A 5 step 종합 결과**: A.3 (geometry, BORDERLINE strongest) 만 유일 promising signal / A.1 약한 BORDERLINE / A.2 FAIL / A.4 FAIL worst / **A.5 FAIL near-null**.
>
> **코덱스 권고 (A.4 검수) 검증**: A.5 HOLD / Axis A 종료 권고 = 본 결과로 정확히 입증. A.5 의 image embedding (heavier dim) 도 A.4 (text) 와 비슷한 패턴 — heavy escalation step 이 cold-start LAO 에서 일관 negative.
>
> **의사결정 영역 (사용자 결정 의무)**:
> 1. A.3 단독 운영 shadow 검토 (별도 의사결정 gate, 코덱스 권고 = 조건부 HOLD)
> 2. Axis B (Phase A pre-screen 후 external acquisition)
> 3. Program-level 재설계 (representation learning / 새 axis)
> 4. 운영 baseline + calibration only 유지 (현재 default)
>
> **운영 영향 X**: A.5 features 운영 spec 추가 X / 운영 모델 (F4 + spline + Huber) + 분기 B (calibration only) 그대로 유지.

## 1. 핵심 결과 (사전등록 §3 적용)

### 1.1 100-seed LAO MdAPE

| Metric | Baseline | A.5 | Δ (낮을수록 좋음) |
|---|---|---|---|
| **Overall** | 38.03% | 38.25% | **+0.22%p** (사실상 동등 또는 미세 악화) |
| **Low (price < 5M)** | 38.29% | 38.24% | **-0.06%p** ✓ Hard gate (very close to 0) |
| Mid/high (≥ 5M) | 38.00% | 38.43% | **+0.43%p** |
| Newly-warm (Stage 3 외) | 46.11% | 46.26% | +0.14%p |

### 1.2 Cluster bootstrap (rep seed=0, n=2000, 진짜 cluster bootstrap)
- Δ overall mean: **-1.01%p** (single seed=0)
- 95% CI: **[-4.35, +2.29]** — 0 걸침 (참고만)
- **99% CI (α=0.01 Bonferroni 5 step decision): [-5.39, +3.22]** — 0 걸침
- P(diff ≥ 0) = 0.2705

> Single-seed CI -1.01%p vs 100-seed mean +0.22%p sign 충돌 = single representative split 의 불안정성 (A.4 동일 caveat). 100-seed mean 이 더 robust effect estimate.

### 1.3 Seed-level Low violation rate

| 지표 | 결과 |
|---|---|
| **Low Δ > 0 violation rate** | **54/100 seeds (54.0%)** |
| Low Δ mean | -0.06%p |
| Low Δ std | (pending) |

> Hard gate 점추정 통과 ✓ but 분포 자체는 0 걸침 — robust 신호 X.

### 1.4 사전등록 §3 PASS / BORDERLINE / FAIL 판정 (마지막 step)

| 조건 | 결과 |
|---|---|
| 🔴 Hard gate Δ_low ≤ 0%p | ✓ (-0.06%p, very close to 0) |
| Primary 99% CI 상한 ≤ 0 (α=0.01 decision) | ✗ (+3.22%p) |
| Primary 95% CI 상한 ≤ 0 (참고만) | ✗ (+2.29%p) |
| Primary practical Δ ≤ -1.0%p | ✗ (+0.22%p, 사실상 동등) |

→ **FAIL (Δ > -0.3%p, 개선 미달, 마지막 step)** — Axis A 전체 종결.

## 2. Axis A 5 Step 종합 비교 (의사결정자 압축)

| 지표 | A.1 | A.2 | **A.3 strongest** | A.4 worst | **A.5 (last)** |
|---|---|---|---|---|---|
| Feature category | cross-artist artwork (분류+갤러리) | artist-binding (popularity) | pure artwork (geometry, 3 cols) | artwork text (PCA 10) | artwork image (PCA 10) |
| Overall Δ | -1.34%p ✓ | -0.21%p | **-2.11%p ✓** | +0.66%p ✗ | **+0.22%p** (≈0) |
| Low Δ (hard gate) | -0.98%p ✓ | +0.05%p ✗ | **-2.65%p ✓** | +1.22%p ✗ | **-0.06%p ✓ (close)** |
| Seed-level violation | 41/100 | 45/100 | **13/100 (min)** | 75/100 (max) | 54/100 |
| 99% CI 상한 | +3.58%p | +4.47%p | **+0.41%p (close)** | +1.85%p | +3.22%p |
| 판정 | BORDERLINE | FAIL | BORDERLINE strongest | FAIL worst | **FAIL (last)** |

> **Axis A 5 step 종합 (코덱스 framing 톤, working hypothesis 보수적):**
> - **A.3 (pure artwork geometry, 3 cols low-dim) = 유일 promising signal** — BORDERLINE near-PASS (99% CI very close miss)
> - **다른 axis (A.1/A.2/A.4/A.5) = 약하거나 negative**
> - **Working hypothesis 보수적 결론**: A.3 의 strong signal 이 **geometry-specific 또는 low-dim 효과** 가능성 ↑ — "artwork-level cross-artist signal 일반이 cold-start LAO 유효" 단순 일반화는 **지지되지 않음** (A.4/A.5 high-dim heavy escalation 모두 실패)
> - **Plausible mechanism (단정 X)**: Cold-start LAO 평가에서 dim 증가 자체가 risk — 8,495 sample / artist holdout 구조에서 high-dim feature 의 generalization 약함

## 3. Axis A 종결 — 의사결정 권고 (코덱스 framing 그대로)

### 3.1 Axis A 5 step 종합 결정
- A.5 (last step) FAIL → **Axis A 전체 종결**
- 운영 채택 후보 = 0 (5 step 모두 PASS 미달)
- A.3 만 BORDERLINE near-PASS — 단독 shadow 검토 가치 (조건부 HOLD)

### 3.2 사용자 의사결정 영역 (다음 단계)

| 옵션 | 사전 조건 | 가치 | 비용 |
|---|---|---|---|
| **A. A.3 단독 운영 shadow** (조건부) | 별도 의사결정 gate (코덱스 권고 = 조건부 HOLD) | A.3 의 BORDERLINE 신호 운영 환경 검증 | 운영 spec §1-§16 변경 / shadow infra |
| **B. Axis B (External Acquisition)** | Phase A 4-7항목 pre-screen 통과 (Legal/TOS/Access/Anti-bot/Labelability/Joinability/As-of-time) | 새 information source 획득 시 가치 큼 | 운영팀 / 법무팀 협업 (LLM 외) |
| **C. Program-level 재설계** | 새 식별 가설 / 새 axis 발견 시 | hypothesis 자체 reframe | 시간 / 사업 이유 필요 |
| **D. 운영 baseline + calibration only 유지** (default) | 무조건 가능 | 현재 단기 안전장치 | 0 (이미 진행 중) |

### 3.3 코덱스 권고 (A.4 결과 검수에서 명시)
- A.5 HOLD 권고 = 본 A.5 결과로 정확히 검증 (FAIL near-null)
- "Axis A 종료 + A.3 shadow 도 현재 HOLD" 권고
- 예외 (A.5 GO 가능 조건) — image 의 본질적 가격 시각 신호 / 별도 사업 예산 + 시간 — 본 A.5 결과로 ROI 미관측 입증

## 4. 운영 영향 X (Axis A 5 step 모두 채택 X)

- A.1-A.5 모두 운영 spec §1-§16 변경 X
- 분기 B (calibration only) 그대로 유지
- A.3 단독 spec 운영 적용 = 별도 의사결정 gate, 본 cycle 기준 = HOLD

## 5. Limitations / 정직 보고

- **A.5 FAIL 의 메커니즘 분리 X**: image embedding 본질 한계 vs PCA K=10 implementation 한계 분리 미수행 (A.4 동일 caveat) — frozen A.5 spec 의 실패
- **Plausible mechanism (단정 X)**: dim sensitivity 가설 (cold-start LAO 에서 high-dim feature noise) — A.4 + A.5 일관 패턴이지만 attribution X
- **Axis A 5 step 종결의 의미**: hypothesis 끝까지 시험 완료 / 그러나 현재 evidence 범위 내 결론은 "A.3 만 promising / 다른 axis 운영 미적합" — 새 evidence (Phase A pre-screen 통과 source / representation learning 등) 시 재평가 가능
- **A.3 단독 shadow 검토 = 별도 의사결정 gate**: 본 cycle 기준 코덱스 = 조건부 HOLD, 의사결정자 영역

## 6. 다음 단계

1. ✅ A.5 결과 보고 — 본 commit
2. ⏳ Deviation log: A.5 + Axis A 종결 entry
3. ⏳ 코덱스 결과 검수 (Axis A 5 step 종합 검토 + 의사결정 영역 권고)
4. ⏳ **(사용자 의사결정) Axis A 종결 후 path 선택** — 옵션 A/B/C/D 중

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Feature track design / A.1-A.4 prereg+결과) | P0×6 + P1×33 + P2×10 적용 |
| **A.5 prereg freeze (2026-05-07)** | A.1-A.4 v2 lessons + procedural vs management recommendation 분리 명시 (사용자 명시 instruction A.5 진행) |
| **A.5 결과 보고 검수 (예정)** | Axis A 5 step 종합 검토 + 의사결정 영역 권고 |

## 8. 참조

- A.5 prereg / A.1-A.4 prereg+결과 / Feature track design / Stage 6B close
- Methodology pipeline / Deviation log
