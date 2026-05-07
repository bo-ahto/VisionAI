# Track 2 Baseline Sample Size + Composition Sensitivity — Mini-Freeze

> **작성일**: 2026-05-07 (mini-freeze, 코덱스 사전 자문 조건부 GO 적용)
> **위치**: 운영 baseline (F4 + spline + Huber) 의 sample size + composition sensitivity descriptive analysis
> **사용자 요청**: data/curated 의 200/500/1000 데이터 기준 모델 검증

> ⚠️ **본 분석의 본질 (코덱스 P0 framing 정정)**: **"baseline 검증" 이 아닌 "sample size + composition sensitivity descriptive analysis"**. 운영 적합성 판정 X / decision-binding X / spec 변경 단독 trigger X.

## 1. Freeze 6항목 (코덱스 권고)

### 1.1 목적
- **Descriptive sample-size + composition sensitivity** — 운영 baseline (`track2_v1_20260507`) 의 dataset 별 stability 관찰
- **decision-binding 아님** — 운영 spec §1-§16 변경 단독 trigger X
- 이상 신호 발견 시 → 별도 prereg confirmatory cycle 진입 (본 분석 미목표)

### 1.2 데이터 (legacy stage1/2/3/full 사용)
| Dataset | Rows | Artists | Works/artist | Newly-warm 적용 |
|---|---|---|---|---|
| `stage1_200x20.parquet` | 200 | 20 | 10 (uniform) | N/A (Stage 3 cohort 외 = curated cohort 외) |
| `stage2_500x50.parquet` | 500 | 50 | 10 (uniform) | N/A (동일) |
| `stage3_1000x100.parquet` | 1,378 | 100 | 10-15 | N/A (Stage 3 자기 cohort = 0 newly-warm) |
| `stage4_full.parquet` | 8,495 | 807 | 1-250 (heavy variance) | ✓ Stage 3 cohort 외 = newly-warm |

> **Lineage caveat (코덱스 P0)**: `stage1/2/3` 는 `stage4_full` 의 **strict row subset 아님** + **artist 구성 다름** → **순수 sample size effect X / sample size + composition 같이 변동**. "Sample size sensitivity" 단독 claim 금지.

### 1.3 모델 (운영 spec freeze)
- `track2_v1_20260507` (F4 + spline + Huber 운영 채택 모델)
- Feature pipeline: `f4_spline_v1_20260506`
- F4 features: `log_area + birth_year_centered + log_artist_total_works + log_area_spline`
- Estimator: `HuberRegressor(epsilon=1.35, alpha=1e-4, max_iter=2000)`

### 1.4 Split + Seeds
- Cold-start LAO 20% artist holdout
- Seed range 0-99 (100 seeds, Stage 3 / 6B / A.1-A.5 동일)
- LAO 적용 가능 조건: train ≥ 50 rows / test ≥ 5 rows

### 1.5 Metrics
- **Primary**: Overall MdAPE (descriptive only — hard gate / decision rule X)
- **Secondary**: Low MdAPE (price < 5M KRW) / Mid-high MdAPE (≥ 5M)
- **Newly-warm**: `stage4_full only` 적용 (Stage 1/2/3 = curated cohort, Stage 3 cohort 기준 newly-warm 정의 부적합 → N/A 처리)
- Aggregate: 100-seed mean + median + std + IQR (코덱스 권고 — descriptive)
- 참고만: rep seed=0 cluster bootstrap CI (single seed wide noise, 부록 처리)

### 1.6 해석 rule (코덱스 P0)
- **§17 hard gate / practical gate 적용 X** — 본 분석은 baseline-across-datasets 비교 (post-decision baseline gate 와 다름)
- **본 분석 단독 spec 변경 trigger 금지**
- 이상 신호 발견 시 → 별도 prereg confirmatory cycle 진입

## 2. 실행 spec

- Code: `experiments/structural_v1/sample_size_sensitivity.py`
- Output: `experiments/structural_v1/results/sample_size_sensitivity.json`
- Result document: `docs/sample_size_sensitivity_results_20260507.md`
- Estimated runtime: ~5-10분 (4 dataset, dataset-별 100-seed)

## 3. Honesty Caveats (사전 명시)

- **200x20 한계**: LAO 20% holdout 시 seed-당 train 16 artists / test 4 artists → power 보다 stability 한계 큼 → **floor / stress point** 처리 (판정 근거 X)
- **Stage 1/2 의 newly-warm "stage4 only"**: Stage 1/2 도 stage4 cohort 외 작가 일부 보유하나 (코덱스 사전 분석 = stage1 5명 / stage2 12명) — 본 분석 spec freeze 으로 stage4 만 newly-warm metric 산출
- **Composition heterogeneity**: stage1/2/3 = 작가당 ≥10 works (uniform) / stage4 = 1-250 (heavy variance) → depth 구조 / warm-cold difficulty mix 도 같이 변동
- **본 분석 = LLM-only descriptive**: 운영 inquiry / 추가 confirmatory 평가 X

## 4. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Axis A / Axis B Round 1-3 / HTML v2) | P0×16 + P1×56 + P2×27 |
| **Sample sensitivity 사전 자문 (2026-05-07)** | 조건부 GO + freeze 6항목 + framing "descriptive only" + Stage 1/2/3 vs full = composition heterogeneity caveat |
| **Sample sensitivity 결과 검수 (예정)** | descriptive 결과 framing + 이상 신호 처리 |
