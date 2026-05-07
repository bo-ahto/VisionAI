# Track 2 Baseline Sample Size + Composition Sensitivity — Results

> **작성일**: 2026-05-07
> **mini-freeze**: `docs/sample_size_sensitivity_freeze_20260507.md` (코덱스 사전 자문 조건부 GO 적용)
> **실험**: `experiments/structural_v1/sample_size_sensitivity.py` / `results/sample_size_sensitivity.json`
> **본질**: **descriptive sample-size + composition sensitivity analysis** (운영 검증 X / decision-binding X / spec 변경 단독 trigger X)

> ⚠️ **본 분석 framing (코덱스 P0)**: "baseline 검증" 이 아닌 **"sample size + composition sensitivity descriptive analysis"**. §17 hard gate / practical gate **적용 X** — descriptive only.

## 0. 한 줄 요약 (의사결정자용)

> **운영 baseline (F4 + spline + Huber) 의 dataset 별 stability 관찰**:
> - **Curated cohort (stage1/2/3, 200-1378 rows / 20-100 artists, 작가당 ≥10 works uniform)**: Overall MdAPE 24-27%
> - **Full dataset (stage4, 8495 rows / 807 artists, 작가당 1-250 works heavy variance)**: Overall MdAPE 38.03%
> - **Δ ≈ +13%p 차이는 sample size 가 아닌 composition (artist 당 작품 수 분산 / cold artist 비율) 효과** (코덱스 P0 caveat — "순수 sample size claim 금지")
>
> **Stability**: Sample size 증가 시 stability 개선 — std 9.41% (200x20) → 6.30% (500x50) → 4.30% (1000x100) → 4.23% (full). 200x20 = floor / stress point (코덱스 P1 caveat 입증).
>
> **운영 영향 X**: 본 분석 단독 spec 변경 trigger X (코덱스 P0). 운영 spec §1-§16 그대로 / 분기 B calibration only 유지.

## 1. 종합 결과 (코덱스 권고 표 형식)

### 1.1 Dataset × Metric Snapshot (100-seed LAO mean)

| Dataset | Rows | Artists | Works/artist | Overall MdAPE | Std | IQR | Low MdAPE | Mid-high | Newly-warm | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| stage1_200x20 | 200 | 20 | 10 (uniform) | 25.95% | **9.41%** | 12.96% | 30.73% | 24.97% | N/A | **Floor / stress point** (코덱스 P1) |
| stage2_500x50 | 500 | 50 | 10 (uniform) | 27.21% | 6.30% | 9.02% | 30.79% | 25.45% | N/A | curated cohort |
| stage3_1000x100 | 1,378 | 100 | 10-15 | **24.30%** | **4.30%** | 4.60% | 24.41% | 24.34% | N/A | curated cohort, 가장 stable |
| **stage4_full** | **8,495** | **807** | **1-250** | **38.03%** | 4.23% | 5.48% | 38.29% | 38.00% | **46.11%** | **운영 baseline / 정상 distribution** |

### 1.2 핵심 관찰 (descriptive)

**A. Stability (sample size 효과)**:
- std: 200x20 = 9.41% (높음) → 500x50 = 6.30% → 1000x100 = 4.30% → full = 4.23% (안정)
- 200x20 = 가장 unstable (코덱스 P1 caveat 입증, train 16 / test 4 artists per seed)
- 1000x100 ≈ full = stability 비슷 (sample size 충분)

**B. Effect size (composition 효과 — 코덱스 P0 caveat 핵심)**:
- curated cohort (1/2/3): Overall mean 24-27% / Low ≈ Mid-high (stage3 = 24.41% vs 24.34%)
- full (4): Overall mean 38.03% / Low ≈ Mid-high (38.29% vs 38.00%)
- **Δ ≈ +13%p (curated → full) = sample size 가 아닌 composition 변화** (코덱스 P0):
  * curated = 작가당 ≥10 works (uniform depth) — warm-skewed distribution
  * full = 작가당 1-250 (heavy variance) — cold-tail 다수 포함

**C. Low vs Mid-high (sub-segment effect)**:
- stage1/2 (small curated): Low > Mid-high (Δ +5-6%p) — small dataset 에서 segment 분리 noisy
- stage3 (curated 1378): Low ≈ Mid-high (Δ ≈ 0) — segment 균형
- stage4 (full): Low ≈ Mid-high (Δ ≈ 0)

**D. Newly-warm (stage4 only)**:
- stage4_full: 46.11% (mean) — Stage 3 cohort 외 작가 = cold-er distribution
- stage1/2/3 = N/A (코덱스 P0 — Stage 3 cohort 기준 정의 부적합)

## 2. 해석 (코덱스 framing 톤 — descriptive only)

### 2.1 Curated cohort 의 baseline 25-27% 가 의미하는 것
- **Curated cohort = 작가당 ≥10 works uniform** = warm-skewed distribution
- 본 distribution 에서 baseline F4 + spline + Huber = 24-27% MdAPE 달성
- **단 운영 환경 (cold-start, 작가당 분포 가변) 과 다름** — 직접 비교 부적합

### 2.2 Full dataset (stage4) 의 baseline 38.03% 가 의미하는 것
- Full = 운영 baseline 학습 / 평가 distribution = **운영 환경 일치**
- Cold artist 다수 포함 (작가당 1-250 works) → cold-start LAO 가 더 어려움
- 38.03% MdAPE = **운영 정상 baseline** (Stage 3-6 / Axis A 전 단계의 baseline = 동일)

### 2.3 Composition 효과의 의미 (sample size effect 와 분리)
- 만약 stage4_full → stage4_curated_subset (≥10 works/artist 만) 으로 subset 시:
  * 작가 수 ≈ stage3 100 + 추가 (warm artists)
  * Overall MdAPE 추정: curated cohort 와 비슷 (24-27%) 가능
- 즉 **"운영 환경 vs curated 평가" 의 13%p gap = sample size 가 아닌 distribution shift** (코덱스 P0 framing 정확)

### 2.4 Stability 개선 (sample size 효과)
- 1000x100 vs full (8495) = std 4.30% vs 4.23% — **포화** (sample size 효과 minimal)
- 200x20 = std 9.41% — **2배 noisier** (floor / stress point 코덱스 P1 caveat)
- **운영 spec 의 1000x100 (stage3 = 운영 학습 cohort) 은 충분한 stability** 확보

## 3. 코덱스 framing 톤 적용 caveats

### 3.1 본 분석의 한계 (코덱스 P0/P1 — 의사결정자 핵심 caveat)
- **순수 sample size 비교 X**: stage1/2/3 vs full = sample size + composition 같이 변동
- **§17 hard gate / practical gate 적용 X**: 본 분석 = baseline-across-datasets descriptive (decision gate 와 다름)
- **본 분석 단독 spec 변경 trigger 금지 (코덱스 P0)**: 이상 신호 발견 시 별도 prereg confirmatory cycle
- **200x20 의 한계**: floor / stress point — 판정 근거 X
- **stage1/2 의 newly-warm "stage4 only"**: stage1/2 도 stage4 cohort 외 작가 일부 보유 (stage1 5명 / stage2 12명) — 본 분석 spec freeze 으로 stage4 만 newly-warm metric 산출

### 3.2 본 분석으로 알 수 있는 것 / 알 수 없는 것

**알 수 있는 것**:
- 운영 baseline F4 + spline + Huber 의 sample size 별 stability 개선 추세
- curated cohort 의 baseline 효과 (24-27%) vs 운영 환경 baseline (38.03%) gap
- 200x20 의 noise 한계

**알 수 없는 것 (본 분석 미목표)**:
- 운영 spec 변경 효과 (decision gate 적용 X)
- 새 모델 vs baseline 비교 (이미 Axis A 5 step / Stage 6A-6B 에서 검증 완료)
- License-first lane (Axis B) 진입 의사결정 (별도 cycle)

## 4. 운영 영향 X / 결정 권고

> **본 분석 단독 spec 변경 trigger 금지** (코덱스 P0). 운영 spec §1-§16 cold rollout default 그대로 / 분기 B calibration only 유지.

본 결과는 운영 baseline 의 stability 관찰 — 새 의사결정 영역 X.

## 5. 다음 단계

1. ✅ Sample sensitivity 결과 보고 — 본 commit
2. ⏳ Deviation log entry (none, 정상 흐름)
3. ⏳ 코덱스 사후 검수 (선택)
4. ⏳ (사용자 결정) 추가 분석 / 운영 baseline 다른 ablation 등

## 6. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Axis A / Axis B Round 1-3 / HTML v2) | P0×16 + P1×56 + P2×27 |
| Sample sensitivity 사전 자문 (2026-05-07) | 조건부 GO + freeze 6항목 + descriptive only framing |
| **Sample sensitivity 결과 검수 (예정)** | 결과 framing 톤 + composition vs sample size 분리 정합성 |

## 7. 참조

- Mini-freeze: `docs/sample_size_sensitivity_freeze_20260507.md`
- 운영 spec: `docs/트랙2_production_통합_spec_20260507.md`
- Stage 3 / 4 plan: `docs/stage4_확장검증계획_20260507.md`
- Stage 4 short-term track: `docs/stage4_short_term_track_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
