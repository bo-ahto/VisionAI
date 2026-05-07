# Feature Track Axis A.4 결과 보고서 — Title Text Embedding FAIL

> **작성일**: 2026-05-07
> **사전등록 freeze**: `docs/feature_track_axis_a4_prereg_20260507.md` (2026-05-07)
> **실험**: `experiments/structural_v1/feature_track_axis_a4.py` / `results/feature_track_axis_a4.json`
> **판정**: **FAIL (🔴 Hard gate Δ_low > 0 위반, decisive)** → A.5 escalation (Step gate B안)

> ⚠️ **핵심 framing (코덱스 P1 톤 정정)**: A.4 = **frozen A.4 spec (MiniLM + PCA K=10 + current sample + LAO setup) 의 실패** — "text embedding 일반의 최종 반증" 이 아닌 "본 spec 의 실패". A.3 의 signal 이 geometry-specific 가능성을 **높이며**, artwork-level cross-artist signal 의 단순 확장은 **지지되지 않음** (입증/반증 X — "단순 일반화 반박" 톤 톤다운).

## 0. 한 줄 요약 (의사결정자용)

> **A.4 title text embedding (multilingual MiniLM, PCA K=10) FAIL** — 사전등록 §3.3 hard gate 위반 (decisive). Overall **+0.66%p 악화** + 저가 **+1.22%p 악화** + Mid-high +0.00%p (사실상 동등) + Newly-warm +0.08%p (사실상 동등).
>
> **Cluster bootstrap (rep seed=0, n=2000, 진짜 cluster bootstrap)**: mean -0.33%p / 95% CI [-2.04, +1.46] / 99% CI [-2.35, +1.85] — 둘 다 0 걸침. P(diff ≥ 0) = 0.34.
>
> **판정**: FAIL — Hard gate Δ_low +1.22%p 위반 (즉시 FAIL trigger). Seed-level violation 75/100 (Axis A 최악).
>
> **Working hypothesis 보수적 해석 (코덱스 P1 톤 정정)**: A.3 (geometry) = strongest / A.4 (text frozen spec) = FAIL → A.3 의 signal 이 **geometry-specific 가능성 ↑** (단정 X) / artwork-level cross-artist signal 의 **단순 확장은 지지되지 않음** (반증 X). A.4 단일 결과는 **"text embedding 일반의 최종 반증" 이 아닌 "frozen A.4 spec 의 실패"** — PCA K=10 / pretrained model task mismatch / current sample size 등 implementation 한계와 text embedding 본질 한계 분리 X (본 cycle 미목표).
>
> **운영 영향 X**: A.4 features 운영 spec 추가 X / 운영 모델 (F4 + spline + Huber) + 분기 B (calibration only) 그대로 유지 / **A.3 단독 shadow 검토 가치는 변동 X** (A.3 결과 보고 §4.2 그대로).

## 1. 핵심 결과 (사전등록 §3 적용)

### 1.1 100-seed LAO MdAPE

| Metric | Baseline | A.4 | Δ (낮을수록 좋음) |
|---|---|---|---|
| **Overall** | 38.03% | 38.69% | **+0.66%p** ⚠️ 악화 |
| **Low (price < 5M)** | 38.29% | 39.51% | **+1.22%p** ⚠️ Hard gate 위반 |
| Mid/high (≥ 5M) | 38.00% | 38.01% | +0.00%p (사실상 동등) |
| Newly-warm (Stage 3 외) | 46.11% | 46.19% | +0.08%p (사실상 동등) |

### 1.2 Cluster bootstrap (rep seed=0, n=2000, 진짜 cluster bootstrap)
- Δ overall mean: **-0.33%p** (single seed=0)
- **95% CI: [-2.04, +1.46]** — 0 걸침 (참고만)
- **99% CI (α=0.01 Bonferroni 5 step decision rule): [-2.35, +1.85]** — 0 걸침
- P(diff ≥ 0) = 0.3400 (34%)

> **Single-seed CI vs 100-seed mean discrepancy** (A.1-A.3 동일 caveat): single seed=0 의 -0.33%p 는 100-seed mean +0.66%p 와 정반대 sign — single seed bootstrap noise 의 wide range. **100-seed mean 이 더 robust effect estimate**.

### 1.3 Seed-level Low violation rate

| 지표 | 결과 |
|---|---|
| **Low Δ > 0 violation rate** | **75/100 seeds (75.0%)** |
| Low Δ mean | +1.22%p |
| 분포 (대략) | <0%p: 25, ≥0%p: 75 — **분포 자체가 우측 (악화 방향) 으로 치우침** |

> **Axis A 최악**: A.1 (41/100) / A.2 (45/100) / **A.3 (13/100, min)** / **A.4 (75/100, max)** — A.4 가 분포상 가장 negative.

### 1.4 사전등록 §3 PASS / BORDERLINE / FAIL 판정

| 조건 | 결과 |
|---|---|
| 🔴 **Hard gate Δ_low ≤ 0%p** | **✗ (+1.22%p, decisive)** |
| Primary 99% CI 상한 ≤ 0 (α=0.01 decision) | ✗ (+1.85%p) |
| Primary 95% CI 상한 ≤ 0 (참고만) | ✗ (+1.46%p) |
| Primary practical Δ ≤ -1.0%p | ✗ (+0.66%p, 악화) |

→ **🔴 Hard gate 위반 → 즉시 FAIL** (사전등록 §3.3) — primary / secondary 모든 조건 동시 미달.

## 2. Axis A 누적 비교 (코덱스 framing 톤, working hypothesis 재평가)

| 지표 | A.1 | A.2 | **A.3 (strongest)** | **A.4 (worst)** |
|---|---|---|---|---|
| Feature category | cross-artist artwork-level (분류+갤러리) | artist-binding (popularity) | pure artwork-level (geometry) | artwork-level text embedding |
| Overall Δ | -1.34%p ✓ | -0.21%p | **-2.11%p ✓** | **+0.66%p ✗** |
| Low Δ (hard gate) | -0.98%p ✓ | +0.05%p ✗ | **-2.65%p ✓** | **+1.22%p ✗** |
| Seed-level low violation | 41/100 | 45/100 | **13/100** | **75/100** |
| 99% CI 상한 | +3.58%p | +4.47%p | **+0.41%p (close)** | +1.85%p |
| 판정 | BORDERLINE | FAIL | BORDERLINE | **FAIL** |

> **Working hypothesis 재평가 (코덱스 framing — 입증/반증 X)**:
> - A.1 (cross-artist artwork: 분류+갤러리) 약한 / A.2 (artist-binding: popularity) near-null / A.3 (pure artwork: geometry) **strongest** / A.4 (artwork: text) **FAIL**
> - "artwork-level cross-artist signal 일반이 cold-start LAO 에 유효" 의 **단순 일반화 반박** — text embedding 도 artwork-level cross-artist 인데 negative effect
> - **수정된 working hypothesis (provisional)**: A.3 의 강한 signal = **geometry 의 특수 효과** (low-dim 3 cols, A.1 category 와 partial overlap 가능 — A.3 P2 caveat 동일)
> - 또는 cold-start LAO 평가에서 **dim 증가 자체가 noise / overfitting risk** (A.4 PCA K=10 vs A.3 3 cols vs A.1 ~15 cols vs A.2 4 cols) → A.5 image embedding (heavier dim) 진입 시 더 검증

## 3. 메커니즘 분석 (provisional, 코덱스 framing — 입증 X)

### 3.1 왜 A.4 가 FAIL 했나? (plausible mechanism — 코덱스 P2 톤 다운)
- **PCA K=10 의 overfitting risk (plausible)**: 384-dim → 10 reduction 후에도 8,495 sample 기준 dim ratio 가 새 features 중 가장 큼 (단정 X)
- **Text embedding 의 noise dominance (plausible)**: `Untitled` (164회) 등 generic title 이 noise driver 가능 / multilingual model 의 zero-shot 한계 (작품 가격 prediction 에 unfine-tuned)
- **Pretrained embedding 의 task mismatch (plausible)**: paraphrase task 로 학습된 model 이 art price prediction 의미 capture X 가능
- → 본 frozen A.4 spec 의 net effect 가 negative (단일 결과로 일반화 X)

### 3.2 A.3 vs A.4 — geometry 의 특수성 시사
- A.3 (geometry, 3 cols low-dim): strongest signal
- A.4 (text, PCA K=10): worst signal
- → "artwork-level cross-artist applicable" 가설은 **dim / signal-to-noise 에 의존** — geometry 만의 특수 효과 가능
- → **A.5 (image embedding, heavier dim)** 진입 시 동일 패턴 (dim ↑ → noise ↑ → FAIL) 가능성 ↑

### 3.3 Cold-start LAO 평가 구조의 dim sensitivity (plausible mechanism, 코덱스 P2 톤 다운)
- 작은 sample (8,495) + cold-start (artist holdout) → high-dim feature 의 generalization 약함 가능 (단정 X)
- A.4 결과 = "dim 증가 자체가 cold-start LAO 에서 risk" plausible mechanism (provisional, 단일 결과)
- → A.5 (image embedding, 큰 model) 진입 의사결정 영역 — 본 결과 후 효용 의문

## 4. 운영 영향 X / A.3 shadow 검토 가치 변동 X

### 4.1 본 cycle 운영 spec 변경 X
- A.4 FAIL → 운영 spec §1-§16 변경 X / 분기 B (calibration only) 그대로 유지
- A.4 features 운영 채택 X

### 4.2 A.3 단독 shadow 검토 가치 (변동 X)
- A.3 결과 보고 §4.2 의 권고 그대로 유지 — A.3 단독 shadow HOLD (코덱스 권고)
- **A.4 FAIL 이 A.3 의 단독 shadow 가치를 강화하지 않음** — A.3 의 99% CI miss 자체가 변하지 않음
- 단 working hypothesis 변경 (geometry 특수 효과 가설) → A.3 의 **현재 spec 으로 운영 적용은 위험** (메커니즘 불명, A.3 P2 caveat 동일)

## 5. Limitations / 정직 보고

- **PCA K=10 의 fixed spec**: 본 cycle 미변경 (HARK 회피). 향후 K 변경 ablation = 새 cycle 의무
- **Embedding model 의 task mismatch**: paraphrase MiniLM 의 art price prediction 에 unfine-tuned — fine-tuning ablation 도 새 cycle
- **Single-seed CI vs 100-seed mean discrepancy**: A.1-A.3 동일 caveat — single seed=0 의 -0.33%p 와 100-seed mean +0.66%p 의 sign 충돌 (single seed wide CI noise)
- **Working hypothesis 재평가는 잠정적**: A.4 단일 결과로 "artwork-level signal 일반 무효" 일반화 X — A.5 (image) 결과 후 종합 평가 의무
- **A.5 escalation ROI 의문**: A.4 의 negative effect 가 dim 증가의 함수일 가능성 → A.5 (image embedding, heavier dim) 도 유사 패턴 risk

## 6. 다음 단계 — Procedural step vs Management recommendation 분리 (코덱스 P1 권고)

> **분리 명시 (코덱스 P1)**: 방법론적 procedural next step 과 의사결정자 management recommendation 은 다름.

### 6.1 Procedural next step (Step gate B안)
- A.4 FAIL → A.5 prereg freeze (image embedding, CLIP/ResNet — heaviest escalation)

### 6.2 Management recommendation (코덱스 권고 — 의사결정자 영역)
- **A.5 HOLD 권고** (코덱스): A.4 가 Axis A 최악 (전체 악화 + low hard-gate 위반 + 75/100 violation) → heavier-dim image embedding 의 기대값 낮음 / A.5 도 유사 FAIL risk
- **Axis A 종료 + A.3 shadow 도 현재 HOLD 권고** (코덱스): A.5 진입 ROI 의문
- **예외 (A.5 GO 가능 조건)**: image 가 text 와 달리 본질적으로 더 직접적인 가격 시각 신호 / 별도 사업 예산 + 시간 / hypothesis 자체를 끝까지 닫기 위한 강한 사업적 이유 — 본 evidence 만으로 그 수준의 ROI 미관측

### 6.3 다음 단계 진행
1. ✅ A.4 결과 보고 — 본 commit (v2 framing 톤 다운 적용)
2. ⏳ Deviation log: 본 cycle entry + A.5 진입 의사결정 영역 명시
3. ⏳ 코덱스 결과 검수 (이미 1차 완료 — A.5 HOLD 권고)
4. ⏳ **(사용자 결정) A.5 진입 vs Axis A 종료** — 본 cycle 종결 후 사용자 의사결정 의무 영역
5. (조건부) A.5 진입 시: A.5 prereg freeze + 구현 + 결과 보고 + 코덱스 검수
6. (조건부) Axis A 종료 시: Axis B Phase A pre-screen 진입 또는 A.3 단독 shadow 검토 (별도 의사결정 gate)

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Feature track design / A.1-A.3 prereg+결과) | P0×6 + P1×30 + P2×8 적용 |
| **A.4 prereg freeze (2026-05-07)** | A.1-A.3 v2 lessons 사전 반영 + heavy escalation 환경 pin |
| **A.4 결과 보고 검수 (2026-05-07)** | FAIL 정당성 OK (P0 없음). P1 ×3 (working hypothesis 톤 다운 / procedural step vs management recommendation 분리 / "frozen A.4 spec fails" 톤) + P2 ×2 (negative information 단정 → plausible mechanism / single-seed sign 충돌 = single split 불안정성) — 본 v2 commit 일괄 반영. **A.5 의사결정 권고 = HOLD (Axis A 종료 권고)**. 사용자 명시 instruction 따라 A.5 진행 결정. |

## 8. 참조

- A.4 prereg / A.1-A.3 prereg+결과 / Feature track design / Stage 6B close
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
