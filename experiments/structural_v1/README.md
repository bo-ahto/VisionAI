# Structural Pricing v1 — 실행 코드

> **상태**: 신규 트랙 skeleton (2026-05-05)
> **연계 docs**: `docs/structural_pricing/`
> **목적**: Hedonic regression 기반 1차 시장 가격 예측 모델 (논문 형식)

## Quick start

### Setup
```bash
# 의존성 설치 (이미 V5 cycle 환경 있으면 skip)
pip install statsmodels patsy
pip install pymer4  # optional (R lme4 wrapper)
pip install pymc arviz  # optional (Bayesian stretch)
```

### 실행 순서 (Week 1-4 plan)
```bash
# Week 1
python3 data_prep.py                  # 데이터 로드 + feature engineering

# Week 2
python3 hedonic_baseline.py            # OLS hedonic

# Week 3
python3 mixed_effects.py               # Mixed-effects (artist + gallery RE)

# Week 4
python3 quantile_regression.py         # Quantile τ grid
python3 bayesian_proto.py              # (stretch) PyMC NUTS
python3 reporting.py                   # 최종 table + figure 합성
```

## Folder structure

```
experiments/structural_v1/
├── README.md (본 문서)
├── data_prep.py             # ← Week 1 Day 6-7
├── hedonic_baseline.py      # ← Week 2
├── mixed_effects.py         # ← Week 3
├── quantile_regression.py   # ← Week 4 Day 22-23
├── bayesian_proto.py        # ← Week 4 stretch (Day 27-28)
├── evaluation.py            # V5 eval framework wrapper
├── reporting.py             # Coefficient table + figures
├── notebooks/               # Exploratory + ad-hoc analysis
└── results/
    ├── tables/              # CSV outputs (coefficients, comparisons)
    ├── figures/             # PNG outputs (residual, heatmap, etc.)
    └── metrics/             # JSON metrics (per-condition holdout)
```

## V5 eval framework 재사용

본 트랙은 V5 cycle 의 evaluation framework 와 동일 protocol:

```python
from visionai.price_engine._v5_eval_framework import (
    lao_split,
    lao_repeated_splits,
    metric_summary,
    segment_metrics,
)

# Artist-level holdout (V5 와 동일)
splits = lao_repeated_splits(df, seeds=[42, 123, 7777], test_size=0.20)
```

## Output 위치

### Tables (`results/tables/`)
- `ols_coefficients.csv` — Level 1 OLS β + SE + p
- `me_coefficients.csv` — Level 2-3 ME β + RE variance
- `quantile_coefficients.csv` — Level 4 τ × variable
- `variance_decomp.csv` — ICC table
- `v3_v5_comparison.csv` — Holdout MdAPE 비교
- `identification_grade.csv` — Causal vs descriptive

### Figures (`results/figures/`)
- `causal_dag.png` — DAG visual (Week 1 Day 4)
- `log_price_distribution.png` — Target distribution
- `correlation_heatmap.png` — Variable correlations
- `residual_diagnostic.png` — QQ + scale-location + leverage
- `variance_pie.png` — Variance decomposition
- `quantile_heatmap.png` — τ × variable

### Metrics (`results/metrics/`)
- `ols_holdout_metrics.json` — OLS LAO 3-seed metrics
- `me_holdout_metrics.json` — ME LAO 3-seed
- `quantile_holdout_metrics.json` — Quantile per τ

## 진행 status

### Week 1 (DRAFT)
- [ ] Day 1-2: Top 2 paper 발췌 (Rengers & Velthuis, Renneboog & Spaenjers)
- [ ] Day 3: Tier 2-4 paper 발췌
- [ ] Day 4: DAG visual
- [ ] Day 5: Variable spec 확정
- [ ] Day 6-7: `data_prep.py` 작성

### Week 2 (DRAFT)
- [ ] Day 8: OLS skeleton
- [ ] Day 9: Variable selection + VIF
- [ ] Day 10: LAO holdout 평가
- [ ] Day 11: Cold/warm + Tier segment
- [ ] Day 12: V3 비교
- [ ] Day 13-14: Coefficient table + diagnostic

### Week 3 (DRAFT)
- [ ] Day 15: ME skeleton
- [ ] Day 16: Gallery RE 추가
- [ ] Day 17: Within-artist FE 비교 + Hausman
- [ ] Day 18: Random slope 검토
- [ ] Day 19: Holdout + V3/V5 비교
- [ ] Day 20-21: Coefficient + variance + report

### Week 4 (DRAFT)
- [ ] Day 22: Quantile regression
- [ ] Day 23: Heatmap + interpretation
- [ ] Day 24: Causal interpretation memo
- [ ] Day 25-26: Final report 작성
- [ ] Day 27-28: (Stretch) Bayesian prototype

## 의존성

### 필수
- pandas, numpy
- statsmodels (OLS, MixedLM, QuantReg)
- scikit-learn (preprocessing, GroupShuffleSplit)
- matplotlib, seaborn (figures)
- 기존: `src/visionai/price_engine/_v5_eval_framework.py`

### 선택
- `pymer4` (R lme4 wrapper, MixedLM 안정성 향상)
- `pymc`, `arviz` (Bayesian stretch)
- `linearmodels` (FE/IV regression, 필요 시)

## 코드 작성 원칙

### Week 1-4 일관 standard
1. **Type hints**: 모든 public function
2. **Docstrings**: Google style (V4/V5 cycle 과 동일)
3. **Logging**: print 금지, `logging` 모듈 사용
4. **Path**: `pathlib.Path` (relative 위치 ROOT/data, ROOT/experiments)
5. **Random seed**: 모든 stochastic 연산에 fix
6. **Config**: hyperparameter / spec 은 함수 인자 또는 top-level constant

### V5 cycle 학습 적용
- Pre-registration 정신 (변수 spec / metric / pass criteria 사전 결정)
- Deviation log (Week 1-4 변경 사항 기록)
- Negative result 도 보고 의무

## Reference docs

- `docs/structural_pricing/README.md` — 전체 overview
- `docs/structural_pricing/01_approach_design.md` — 모델 spec + 수학 정의
- `docs/structural_pricing/02_literature_review.md` — Paper references
- `docs/structural_pricing/03_causal_dag.md` — DAG + 식별 가능성
- `docs/structural_pricing/04_4week_plan.md` — Day-by-day plan
- `docs/structural_pricing/05_data_requirements.md` — Variable spec
- `docs/structural_pricing/06_evaluation_framework.md` — Metric / table format

## 코덱스 자문 12차

본 트랙의 모든 design 권고는 코덱스 12차 자문 (2026-05-05) 결과:
- Hedonic mixed-effects 1순위
- Quantile / Bayesian 보조
- Within-artist design 권고 (IV non-credible)
- A+ deliverable realistic 1개월
- Comparative + Independent (V3/V5 와)
