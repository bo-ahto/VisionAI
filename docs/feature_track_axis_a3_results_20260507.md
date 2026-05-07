# Feature Track Axis A.3 결과 보고서 — Geometry BORDERLINE (strongest Axis A signal)

> **작성일**: 2026-05-07
> **사전등록 freeze**: `docs/feature_track_axis_a3_prereg_20260507.md` (2026-05-07)
> **실험**: `experiments/structural_v1/feature_track_axis_a3.py` / `results/feature_track_axis_a3.json`
> **판정**: **BORDERLINE — 95% CI 통과 / 99% CI (α=0.01 Bonferroni decision) +0.41%p 미달, Hard gate decisive 통과** → A.4 escalation (Step gate B안)

> ⚠️ **핵심 framing (코덱스 검수 lessons 반영, evidence 톤)**: A.3 = **Axis A cheap-feature ladder 의 가장 강한 신호**. Overall -2.11%p / 저가 -2.65%p (큰 개선) / 95% CI 상한 -0.36%p (통과). 단 **99% CI (α=0.01 Bonferroni 5 step program-level decision rule) 상한 +0.41%p (very close miss)** → BORDERLINE — promising signal but **α=0.01-controlled decision-grade 미도달**.

## 0. 한 줄 요약 (의사결정자용)

> **A.3 geometry 3종 = Axis A 최강 신호** — 100-seed mean: overall **-2.11%p** ✓ practical / 저가 **-2.65%p** ✓ hard gate (decisive 큰 개선) / mid-high -1.79%p / newly-warm -3.15%p.
>
> **Cluster bootstrap (rep seed=0, n=2000, 진짜 cluster bootstrap)**: mean -4.43%p / **95% CI [-9.54, -0.36]** ✓ (CI 상한 -0.36%p) / **99% CI [-11.37, +0.41]** ✗ (CI 상한 +0.41%p, very close miss). P(diff ≥ 0) = 0.0120.
>
> **판정**: BORDERLINE — α=0.01 (Bonferroni 5 step) program-level decision rule 미달 / 95% CI 만으로는 통과. Step gate B안 적용 → A.4 escalation.
>
> **Seed-level violation 13/100 = 13%** — A.1 (41/100) / A.2 (45/100) 대비 압도적으로 낮음 → 분포상 robust (mean ≈ -2.65%p, 87% seeds negative).
>
> **Working hypothesis 부분 일치 (provisionally consistent — escalation rationale 강화) (provisional)**: A.1 (cross-artist artwork-level: 분류/갤러리) 약한 신호 / A.2 (artist-binding popularity) near-null / **A.3 (pure artwork-level geometry) 강한 신호** → "Cold-start LAO 에서 유효한 신호 = artwork-level cross-artist applicable" 가설 **부분 일치** (A.4-A.5 재시험으로 확정 필요, 코덱스 framing).
>
> **운영 영향 X (본 cycle)**: A.3 features 운영 spec 추가 X / 운영 모델 (F4 + spline + Huber) + 분기 B (calibration only) 그대로 유지. 단 A.3 의 effect size + low harm decisive 통과 = 추가 검증 가치 있음 (A.4 escalation 후 재평가).

## 1. 핵심 결과 (사전등록 §3 적용)

### 1.1 100-seed LAO MdAPE

| Metric | Baseline | A.3 | Δ (낮을수록 좋음) | Std |
|---|---|---|---|---|
| **Overall** | 38.03% | 35.92% | **-2.11%p** ✓ practical (큰 개선) | — |
| **Low (price < 5M)** | 38.29% | 35.65% | **-2.65%p** ✓ hard gate (큰 개선) | — |
| Mid/high (≥ 5M) | 38.00% | 36.21% | **-1.79%p** | — |
| **Newly-warm (Stage 3 외)** | 46.11% | 42.97% | **-3.15%p** | — |

### 1.2 Cluster bootstrap (rep seed=0, n=2000, 진짜 cluster bootstrap A.1 v2 fix)
- Δ overall mean: **-4.43%p** (single seed=0 결과)
- **95% CI: [-9.54, -0.36]** — **CI 상한 -0.36%p ✓ 통과** (참고만)
- **🎯 99% CI (α=0.01 Bonferroni 5 step decision rule): [-11.37, +0.41]** — **CI 상한 +0.41%p ✗ very close miss**
- P(diff ≥ 0) = **0.0120** (1.2%)

### 1.3 Seed-level Low violation rate

| 지표 | 결과 |
|---|---|
| **Low Δ > 0 violation rate** | **13/100 seeds (13.0%)** |
| Low Δ mean | -2.65%p |
| 분포 (Stage 6B 표준 형식) | <0%p: 87, 0-1%p: 5, 1-3%p: 4, ≥3%p: 4 |

> **A.1/A.2 대비 robust 분포**: A.1 41/100 / A.2 45/100 / **A.3 13/100** — A.3 가 분포상 가장 robust. mean 통과 + violation rate 낮음 = "harm 해결 (mean) + 분포 robustness" (단 inferential 99% CI 는 별개 issue).

### 1.4 사전등록 §3 PASS / BORDERLINE / FAIL 판정 (α=0.01 99% CI decision)

| 조건 | 결과 |
|---|---|
| 🔴 **Hard gate Δ_low ≤ 0%p** | **✓ (-2.65%p, decisive)** |
| Primary practical Δ ≤ -1.0%p | ✓ (-2.11%p) |
| **Primary 99% CI 상한 ≤ 0 (α=0.01 decision)** | **✗ (+0.41%p, very close)** |
| Primary 95% CI 상한 ≤ 0 (참고만) | ✓ (-0.36%p) |

→ **BORDERLINE (Primary 99% CI 미달)** — Step gate B안 (A.4 escalation) 적용.

> **Decision rule 적용 정직 보고**: 99% CI +0.41%p miss = α=0.01 (Bonferroni 5 step program-level FWER ≤ 0.05) 통제하 결정 미달. 95% CI 만 사용 시 PASS 가능했음 — 그러나 A.1 prereg P0 fix 로 99% CI 가 decision rule 로 frozen → 사전등록 정합성 유지 의무 (HARK 회피).

## 2. Axis A 전체 패턴 비교 (Working hypothesis 부분 일치 (provisionally consistent — escalation rationale 강화), 코덱스 framing)

| 지표 | A.1 (BORDERLINE) | A.2 (FAIL) | **A.3 (BORDERLINE, strongest)** |
|---|---|---|---|
| Feature category | cross-artist artwork-level (작품 분류 + 갤러리) | artist-binding (popularity) | **pure artwork-level (geometry)** |
| Overall Δ | -1.34%p ✓ practical | -0.21%p (사실상 동등) | **-2.11%p** ✓ (Axis A max) |
| Low Δ (hard gate) | -0.98%p ✓ | +0.05%p ✗ | **-2.65%p ✓ (Axis A max)** |
| 95% CI 상한 | +1.94%p (참고용 미달) | +3.03%p (참고용 미달) | **-0.36%p (참고용 통과)** |
| 99% CI 상한 (α=0.01 decision) | +3.58%p ✗ | +4.47%p ✗ | **+0.41%p ✗ (very close)** |
| Seed-level low violation | 41/100 | 45/100 | **13/100 (Axis A min)** |
| 판정 | BORDERLINE | FAIL | **BORDERLINE (largest effect size, decision-grade 미도달)** |

> **Working hypothesis 부분 일치 (코덱스 framing — 입증 X)**: A.1 (cross-artist 작품 분류 / 갤러리) 약한 신호 → A.2 (artist-binding popularity) near-null → **A.3 (pure artwork-level geometry) 가장 강한 신호** = "Cold-start LAO 에서 유효한 신호 = artwork-level cross-artist applicable signal" 가설과 **일관 패턴**. 그러나 본 working hypothesis 의 confirmation 은 **A.4 (text) / A.5 (image) escalation** 에서도 검증 필요 (text embedding 도 artwork-level signal — 본 hypothesis 가 맞다면 promising 예상).

## 3. Provisional 메커니즘 분석

### 3.1 왜 A.3 가 Axis A 최강 신호인가? (working hypothesis)
- **Pure artwork-level signal**: aspect ratio (가로/세로) / 2D vs 3D / depth = artist 와 무관한 작품 자체 attribute → cold-start LAO 에서 unseen artist 의 작품에도 학습된 weight 적용 가능 (cross-artist applicable)
- **운영 F4 의 log_area 와 직교**: log_aspect_ratio = 작품 모양 (shape) / log_area = 작품 크기 (size). 두 신호는 직교 → A.3 features 가 새 정보 추가
- **2D/3D 분리 효과**: 2D 71.7% / 3D 28.3% 의 가격대 분포 차이가 신호로 작용 가능 (본 cycle effect attribution 미수행, likely driver 추정)

### 3.2 6B / A.2 패턴과 대조
- 6B (artist-level partial pooling) / A.2 (artist-binding popularity bundle) = artist-binding signal → cold-start LAO 무력
- A.3 (pure artwork-level geometry) = artwork-level signal → cold-start LAO 강한 효과
- → **Working hypothesis: cross-artist applicable feature = cold-start LAO 에 유효 / artist-binding feature = 무력** 부분 일치

### 3.3 그럼에도 99% CI 미달 이유
- 95% CI passes (-0.36%p) but α=0.01 Bonferroni 5 step decision rule = 99% CI 사용 → +0.41%p 만 0 걸침
- single seed cluster bootstrap (rep seed=0) 의 inherent noise — 100-seed mean (-2.11%p) 이 더 robust effect estimate
- → A.4 escalation (text embedding) 으로 cross-artist signal hypothesis 추가 confirmation 필요

## 4. 운영 영향 (본 cycle 채택 X, 단 추가 검증 가치 high)

### 4.1 본 cycle 채택 X
- A.3 BORDERLINE → 운영 spec §1-§16 변경 X
- 분기 B (calibration only) 그대로 유지
- A.3 features 운영 채택 X — 사전등록 PASS 기준 (99% CI) 미달

### 4.2 추가 검증 가치 (의사결정자 영역, 코덱스 P1 톤 좁힘)
- A.3 의 effect size (-2.11%p overall / -2.65%p low) = **Axis A 최대값**
- Seed-level violation 13/100 = robust 분포
- 95% CI 통과 / 99% CI very close miss
- → 기본 결정: **A.4 GO / A.3 단독 shadow HOLD** (코덱스)
  - **A.4 진입**: working hypothesis 의 더 직접적 confirmation step (artwork-level cross-artist text signal)
  - **A.3 단독 shadow**: 운영 채택 검토 X — "추가 evidence 수집" 성격 한정 / **A.4 결과 확인 후 또는 별도 business-driven 탐색 트랙으로만** 검토 가능 / 본 cycle 의 inferential 근거 (single-seed bootstrap 99% CI) 가 닫히지 않은 상태에서는 운영 shadow 권고 X

## 5. Limitations / 정직 보고

- **99% CI vs 95% CI 의 decision rule 분리**: 사전등록 freeze 후 decision rule = 99% CI / 95% CI 만 통과 시 BORDERLINE — α=0.01 Bonferroni 의 conservatism (정직 보고)
- **Single-seed cluster bootstrap noise**: rep seed=0 의 -4.43%p 도 100-seed mean (-2.11%p) 의 ~2σ outlier (single seed 의 wide CI 노출)
- **Effect attribution 미수행**: log_aspect_ratio / is_3d / log_depth_3d 중 어느 것이 가장 큰 driver 인지 미측정 (본 cycle 비목표 — 향후 ablation 가능)
- **2D=71.7% / 3D=28.3% imbalance**: log_depth_3d 는 28.3% 만 informative — 실제 effect 의 majority 는 log_aspect_ratio (likely driver 추정, 본 cycle 입증 X)
- **Working hypothesis vs 입증 X**: Axis A 패턴 (A.1 약한 / A.2 무 / A.3 강함) 이 "cross-artist signal hypothesis" 와 일관하나 A.4 (text) / A.5 (image) escalation 에서 재시험 필요 (코덱스 P1 권고 톤)
- **Geometry effect 의 메커니즘 불명 (코덱스 P2 추가 caveat)**: geometry features 가 작품 자체의 형태 신호로 작동하는지, 또는 format / category / material proxy 로 작동하는지 본 cycle 미확인. log_aspect_ratio 가 작품 종류 (회화 vs 조각 vs 사진 등) 의 proxy 일 가능성 — A.1 의 category one-hot 과 partial overlap 가능. 메커니즘 자체는 별도 ablation 필요.

## 6. 다음 단계 (Step gate B안)

1. ✅ A.3 결과 보고 — 본 commit
2. ⏳ Deviation log: 본 cycle entry (none, 정상 흐름) + A.4 escalation 결정
3. ⏳ 코덱스 결과 검수 (선택, A.3 strongest signal 인 만큼 검수 가치 high)
4. ⏳ A.4 prereg freeze 진입 (title text embedding, multilingual BERT — first heavy escalation, compute / storage 비용 ↑)
5. ⏳ (사용자 결정) A.4 진입 vs A.3 단독 shadow 검토 / Cold Phase A 시작 시점

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Feature track design / A.1 prereg+결과 / A.2 prereg+결과) | P0×6 + P1×24 + P2×6 적용 |
| **A.3 prereg freeze (2026-05-07)** | A.1/A.2 v2 lessons 사전 반영 |
| **A.3 결과 보고 검수 (2026-05-07)** | **A.4 GO / A.3 shadow HOLD**. P0 없음. P1 ×3 ("near-PASS" 표현 / "부분 입증" 톤 / shadow 권고 좁힘) + P2 ×1 (geometry 메커니즘 proxy 가능성 caveat) — 본 v2 commit 일괄 반영 |

## 8. 참조

- A.3 prereg: `docs/feature_track_axis_a3_prereg_20260507.md`
- A.1/A.2 결과: `docs/feature_track_axis_a1_results_20260507.md` / `docs/feature_track_axis_a2_results_20260507.md`
- Feature track design: `docs/feature_track_design_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
