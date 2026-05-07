# 06. Evaluation Framework — V5 protocol 재사용 + 학술 표준

> **상태**: DRAFT
> **목적**: V5 cycle 평가 protocol 과 일관 + 학술 형식 (paper-style) outputs

## 1. Split protocol (V5 와 공유)

### Artist-level Holdout
```python
from visionai.price_engine._v5_eval_framework import lao_split, lao_repeated_splits

splits = lao_repeated_splits(df, seeds=[42, 123, 7777], test_size=0.20)
```

- Hard gate: `artist_slug` overlap=0
- 80% Train + 20% Holdout
- Repeated 3 seeds → mean ± std reported

### Inner CV (선택 — hyperparameter 결정 시)
- 5-fold KFold on training subset
- 본 트랙은 hyperparameter 적음 (regularization λ, RE prior etc.) → CV 없이 fix 가능

## 2. Metrics (V5 와 공유)

### Primary
- **Cold-start MdAPE**: holdout 의 0-shot artist segment MdAPE

### Secondary
- Overall MdAPE
- Seen-artist MdAPE (in 1+ shot training)
- W30 (±30% 정확도)
- W50 (±50% 정확도)
- MAE on log-price scale
- R² (학술 보고용 추가)

### 학술 추가
- **Adjusted R²** (number of predictors 조정)
- **AIC / BIC** (model comparison)
- **Likelihood ratio test** (RE vs FE / random slope)

### Diagnostic-only
- Residual std
- QQ-plot deviation
- Cook's distance distribution

## 3. Segment 보고

### 핵심 segment (V5 와 공유)
- **Exposure**: 0-shot / 1-3 / 4-10 / 10+ artists
- **Source**: Artsy / Saatchi
- **Tier**: A / B / C / D / E (gallery_tier_v4 사용 가능)
- **Career stage**: early / mid / late / unknown
- **Price tercile**: 1 / 2 / 3 (train-only quantile)

### 본 트랙 추가 segment
- **Medium**: oil / acrylic / paper / sculpture / mixed / other
- **Within-artist**: same artist 다 작품 (paired comparison 가능)

### Reporting rule
- All cells (가능 한 까지) 보고
- n < 30 cell → "underpowered (dropped)" 표시
- Mandatory aggregates (V5 와 동일)

## 4. 학술 보고 형식 (paper-style)

### Coefficient Table (Table 1)
```markdown
| Variable | OLS β (SE) | ME β (SE) | OLS p | ME p | Note |
|---|---|---|---|---|---|
| log_area | 0.45*** (0.02) | 0.42*** (0.02) | <0.001 | <0.001 | size elasticity |
| medium_oil (ref) | — | — | — | — | reference |
| medium_acrylic | -0.12** (0.05) | -0.10** (0.04) | 0.012 | 0.018 | vs oil |
| ... | ... | ... | ... | ... | ... |
| Constant | 14.5 (0.5) | 14.2 (0.4) | <0.001 | <0.001 | |
| N | 28,376 | 28,376 | | | |
| R² | 0.45 | — | | | |
| AIC | — | XXX | | | |
| Artist RE σ² | — | 0.85 | | | ICC = 0.45 |
| Gallery RE σ² | — | 0.30 | | | ICC = 0.16 |
```

★ p < 0.05, ★★ p < 0.01, ★★★ p < 0.001

### Variance Decomposition Table (Table 2)
```markdown
| Component | Variance | % Total |
|---|---|---|
| Artist RE | 0.85 | 45% |
| Gallery RE | 0.30 | 16% |
| Residual | 0.74 | 39% |
| Total | 1.89 | 100% |
```

### Holdout Comparison Table (Table 3)
```markdown
| Model | Overall | Artsy | Saatchi | Cold-start | Warm |
|---|---|---|---|---|---|
| Naive | 76.06 ± 1.84 | ... | ... | 76 | 75 |
| OLS hedonic | TBD | TBD | TBD | TBD | TBD |
| Mixed-effects | TBD | TBD | TBD | TBD | TBD |
| V3 (production) | 42.39 | 27.80 | 47.73 | 27.80 | — (warm undefined) |
| V5 candidate | TBD | TBD | TBD | TBD | TBD |
```

### Quantile Coefficient Heatmap (Figure 1)
- Y-axis: 변수
- X-axis: τ ∈ {0.1, 0.25, 0.5, 0.75, 0.9}
- Cell value: β_τ (color = magnitude, sign = blue/red)
- 해석: 분포 위치별 변수 효과 변화

### Residual Diagnostic (Figure 2)
- Subplot 1: QQ-plot of residuals (정규성 검증)
- Subplot 2: Scale-location (homoskedasticity)
- Subplot 3: Residual vs fitted (linearity)
- Subplot 4: Cook's distance (leverage)

### Variance Decomposition Pie (Figure 3)
- Pie chart: artist / gallery / residual variance share

## 5. Robustness checks (Week 4 stretch)

### Within-artist FE
- Artist FE 통제 후 coefficient 비교
- RE 와 일치 → CIA 약 충족 신호
- 차이 발견 → omitted variable 의심

### Within-artist within-medium
- 작가 + medium 둘 다 통제
- size, year, support 의 더 강한 식별

### Sensitivity
- Outlier 제거 (Cook's d > 4/n) 후 재추정
- Heavy-tail truncation (1%/99% winsorize)
- Subsample (Korean only / international only)

## 6. V3 / V5 와의 비교 protocol

### 데이터 동일
- Same `primary_market_dataset.parquet` + `saatchi_cleaned.parquet`
- Same V5 LAO split (3 seeds)

### Inference 비교
- V3: cached predictions (load `model_test_results/integrated_v3_filtered_metrics.json`)
- V5: 계산 가능 시 (C-lite 도입 후)
- 본 트랙: OLS / ME / Quantile per holdout

### 표 양식 (Week 4 final report Table 3)
- 동일 row format
- Mean ± std across 3 seeds

## 7. 식별 등급표 (causal vs descriptive)

### Final report 의 critical 표 (DAG §3 채움)

```markdown
| 변수 | β (ME) | SE | 식별 등급 | Interpretation |
|---|---|---|---|---|
| log_area | 0.42*** | 0.02 | **Causal** (within-artist) | "1σ 큰 작품 → 가격 +X%" |
| year_made | 0.05** | 0.02 | **Causal** (within-artist) | "신작 premium" |
| medium_acrylic vs oil | -0.10** | 0.04 | Causal-restricted (within-artist within-size) | "같은 작가/크기 시 acrylic -X%" |
| career_stage_late | 0.25*** | 0.06 | Causal-restricted | "Galenson late peak 효과" |
| log_followers | 0.30*** | 0.03 | **Descriptive only** (reverse causality) | "popularity correlate" |
| gallery_tier_B | 0.20** | 0.07 | **Descriptive only** (selection bias) | "associational, not causal" |
| has_international | 0.15** | 0.05 | Descriptive only | "associational" |
```

★★★ p<0.001, ★★ p<0.01, ★ p<0.05

## 8. 보고 파일 (Week 4 final)

### `experiments/structural_v1/results/`

```
results/
├── tables/
│   ├── ols_coefficients.csv
│   ├── me_coefficients.csv
│   ├── quantile_coefficients.csv
│   ├── variance_decomp.csv
│   ├── v3_v5_comparison.csv
│   └── identification_grade.csv
├── figures/
│   ├── causal_dag.png
│   ├── log_price_distribution.png
│   ├── correlation_heatmap.png
│   ├── residual_diagnostic.png
│   ├── variance_pie.png
│   └── quantile_heatmap.png
└── metrics/
    ├── ols_holdout_metrics.json
    ├── me_holdout_metrics.json
    └── quantile_holdout_metrics.json
```

### `docs/structural_pricing/final_report.md`
- Paper-style 10-15 페이지
- Sections: Abstract, Introduction, Data, Methodology, Results, Causal Framing, Comparison, Limitations, Future Work
- All tables + figures 인용

## 9. Pre-registration 가이드 (V5 cycle 학습 적용)

본 트랙도 V5 cycle 의 사전등록 정신 적용:

### 사전 결정 (Week 1 종료 시)
- Variable spec (§5)
- LAO split + 3 seeds
- Primary metric (cold-start MdAPE)
- Pass criteria (Week 4 종료 시 self-eval ≥ 2/3)
- Stop conditions (Week 별 plan §)

### Deviation log
- Week 1-4 진행 중 변경 사항 기록
- "사전 결정 외 변경" 명시 (post-hoc 표시)

### 사후 cherry-picking 방지
- 모든 변수 결과 보고 의무 (significant 만 보고 X)
- 모든 segment 보고 의무
- Negative result 도 명시

## 10. 검토 cycle (선택)

### Week 2 종료 시 self-review
- OLS 결과가 literature 와 일치?
- Diagnostic plot 정상?
- → Week 3 진행 가능

### Week 3 종료 시 코덱스 review (선택)
- ME 결과 + variance decomposition
- Identification 등급표 초안
- → Week 4 final report 방향 검토

### Week 4 종료 시 final code review
- Final report 완성도
- 인용 형식 / table 양식 / 학술 표준 준수
- 사용자 own review

## 11. 다음 단계

### Week 1 Day 5
- 본 문서의 metric / table / figure 양식 확정
- `experiments/structural_v1/results/` 디렉토리 구조 생성

### Week 2-4
- 본 문서의 §4 paper-style table 채워나감
- §7 식별 등급표 채움
- §8 산출물 위치에 결과 저장

### Final
- Final report (`docs/structural_pricing/final_report.md`) 작성
- Self-evaluation (`README.md` §7 기준)
