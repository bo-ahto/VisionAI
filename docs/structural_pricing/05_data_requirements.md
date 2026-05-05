# 05. Data Requirements — 변수 Spec / Feature Engineering

> **상태**: DRAFT (Week 1 Day 5 작업 대상)
> **목적**: Hedonic regression 의 RHS variables 확정 + 처리 spec

## 1. Source data

### 데이터 위치
- `data/primary_market_dataset.parquet` (Artsy 7,289 + filter)
- `data/saatchi_cleaned.parquet` (Saatchi 21,087)
- 통합 후 7,276 ~ 28,376 (필터링 / merge 따라)

### Filter
- `is_excluded_for_training == 0` (입체작 등 제외)
- `price_krw > 1` (positivity for log)

## 2. Target variable

### `log_price = log(price_krw)`
- **이유**: heavy-tail 분포 (₩300K ~ ₩3B), log normalize
- **분포**: log-normal 가정 (정규성 검증 필요)
- **검증**: QQ-plot of log_price (Week 1 Day 5)

## 3. RHS Variables (15-25 후보)

### Group 1: Size (continuous)
| 변수 | 정의 | 처리 | Reference |
|---|---|---|---|
| `log_area` | log(area_cm2) | log + center | Rengers & Velthuis 2002 |
| `aspect_ratio` | width / height | numerical | Renneboog & Spaenjers 2013 |
| `is_small` | binary, area < 1000cm² | dummy | (custom) |
| `has_depth` | binary, depth > 0 | dummy | (custom) |

### Group 2: Medium (categorical)
| 변수 | 정의 | 처리 | Reference category |
|---|---|---|---|
| `medium_oil` | binary | dummy | (use as base) |
| `medium_acrylic` | binary | dummy | — |
| `medium_paper` | binary | dummy (`watercolor` + `pencil`) | — |
| `medium_ink` | binary | dummy | — |
| `medium_pigment` | binary | dummy | — |
| `medium_mixed` | binary | dummy | — |
| `medium_other` | binary | dummy | — |
| `support_factor` | numerical (canvas/paper/board factor) | continuous | (custom) |

### Group 3: Time (continuous + binary)
| 변수 | 정의 | 처리 | Reference |
|---|---|---|---|
| `year_made_centered` | year_made - mean | center | — |
| `work_age` | current_year - year_made | continuous | (custom) |
| `is_recent` | binary, work_age <= 5 | dummy | (custom) |
| `has_year_made` | binary | dummy | — |

### Group 4: Artist (mix)
| 변수 | 정의 | 처리 | Reference |
|---|---|---|---|
| `log_followers` | log(1 + followers) | log + center | Schönfeld & Reinstaller 2007 |
| `career_stage_dummies` | early/mid/late/unknown | dummy (4 levels) | Galenson 2003 |
| `artist_age_at_creation` | year_made - birth_year | continuous | Galenson 2003 |
| `has_birth_year` | binary | dummy (control) | — |
| `artist_total_works` | log(1 + total works) | log + center | (custom) |
| `for_sale_ratio` | for_sale / total | continuous | (custom) |

### Group 5: Gallery (mix)
| 변수 | 정의 | 처리 | Reference |
|---|---|---|---|
| `gallery_tier_dummies` | A/B/C/D/E | dummy (5 levels, E base) | Schönfeld & Reinstaller 2007 |
| `gallery_city_count` | log(1 + city count) | log + center | (custom) |
| `has_seoul` | binary | dummy | (custom) |
| `has_international` | binary | dummy | (custom) |
| `gallery_type` | categorical | dummy | (custom) |

### Group 6: Source / market
| 변수 | 정의 | 처리 | Reference |
|---|---|---|---|
| `is_artsy` | binary (Artsy=1, Saatchi=0) | dummy | (custom) |
| `is_krw` | binary (price in KRW) | dummy (control) | — |

## 4. 변수 처리 protocol (코덱스 권고)

### Continuous
- **Log transform**: positive-skewed (area, followers, works)
- **Centering**: mean = 0 (interpretation 용이)
- **Standardization**: 모든 continuous β 비교 가능 → 1σ 변화 시 가격 % 변화

### Categorical (high cardinality)
- **Reference category**: 가장 많은 빈도 (oil, unknown, Tier_E)
- **Drop**: 빈도 < 10건 카테고리 → "other" 으로 합침
- **Avoid**: gallery_name (1,124 levels) 직접 dummy → random effect

### Missing value
- **Numerical**: median imputation + missingness flag dummy
- **Categorical**: "unknown" 별도 level + flag dummy
- **Treatment**: 각 imputation 의 sensitivity check

### Outlier
- **Cook's distance**: > 4/n 인 row flag → robust regression sensitivity
- **Winsorize**: log_price 의 1% / 99% percentile (선택)
- **Drop X**: 학술 표준 — outlier 제거 X (sensitivity 만 보고)

## 5. Multicollinearity check

### Variance Inflation Factor (VIF)
- VIF > 10 → drop / 합침
- 예: `log_followers` 과 `artist_total_works` 강 상관 → 1개만 사용
- `gallery_tier` 과 `has_international` 강 상관 → 둘 다 유지하되 caveat

### Korean / international 분리
- `gallery_country == 'Korea'` vs not
- 분포 다른지 검증 (subsample 분석)

## 6. Final variable list (Week 1 Day 5 종료 시)

```python
# 후보 (Week 1 Day 5 에서 final 결정)
features_continuous = [
    "log_area",          # log(area_cm2)
    "aspect_ratio",
    "year_made_centered",
    "work_age",
    "log_followers",
    "artist_age_at_creation",
    "log_artist_total_works",
    "for_sale_ratio",
    "log_gallery_city_count",
    "support_factor",
]

features_binary = [
    "is_small",
    "has_depth",
    "is_recent",
    "has_year_made",
    "has_birth_year",
    "has_seoul",
    "has_international",
    "is_artsy",
    "is_krw",
]

features_categorical = [
    "medium_category",     # 6 levels (oil base)
    "career_stage",        # 4 levels (unknown base)
    "gallery_tier",        # 5 levels (Tier_E base)
    "gallery_type",        # categorical
]

# Random effect (mixed-effects only)
random_effect_groups = [
    "artist_slug",         # ~1,240 levels
    "gallery_name",        # ~1,124 levels
]
```

총 후보: ~25 features (실제 final 은 VIF / sensitivity 후 15-22 결정)

## 7. Feature engineering pipeline

### `experiments/structural_v1/data_prep.py` 의 역할

```python
def prepare_structural_data(df: pd.DataFrame) -> pd.DataFrame:
    """V5 eval framework + 본 트랙 변수 spec 적용."""
    # 1. Filter
    df = df[df["is_excluded_for_training"] == 0]
    df = df[df["price_krw"] > 1]

    # 2. Target
    df["log_price"] = np.log(df["price_krw"])

    # 3. Continuous
    df["log_area"] = np.log(df["area_cm2"].clip(lower=1))
    df["log_followers"] = np.log1p(df["ln_followers"].clip(lower=0))
    # ... 다른 log/center/standardize

    # 4. Binary
    df["is_small"] = (df["area_cm2"] < 1000).astype(int)
    # ...

    # 5. Categorical → dummy
    df = pd.get_dummies(df, columns=["medium_category", "career_stage", ...])

    # 6. Multicollinearity check
    # ...

    # 7. Standardize continuous (optional, after split)

    return df
```

### Train/test split (V5 eval framework)
- Artist-level GroupShuffleSplit 80/20
- Repeated 3 seeds: 42, 123, 7777
- 표준화 fit on train only (no leakage)

## 8. Descriptive statistics (Week 1 Day 5 보고)

### 산출물
```
experiments/structural_v1/results/data_summary.json
{
  "n_works": 28376,
  "n_artists": 1240,
  "n_galleries": 1124,
  "log_price": {"mean": ..., "median": ..., "std": ...},
  "log_area": {"mean": ..., "median": ...},
  "medium_distribution": {"oil": 2587, "acrylic": 2566, ...},
  "career_stage_distribution": {...},
  "gallery_tier_distribution": {...},
  "missingness": {
    "year_made": "X.X%",
    "career_stage": "X.X%",
    ...
  }
}
```

### 산출 도표
- `experiments/structural_v1/results/figures/log_price_distribution.png` (histogram + QQ plot)
- `experiments/structural_v1/results/figures/correlation_heatmap.png` (continuous variable corr)

## 9. 식별 가능 변수 vs descriptive 변수

본 트랙의 **causal claim 가능** 변수 (DAG `03_causal_dag.md` Tier A):
- `log_area`, `year_made`, `work_age` — within-artist FE 통제 후

본 트랙의 **descriptive only** 변수 (Tier B/C):
- `gallery_tier`, `log_followers`, `gallery_country`, `is_seoul` — selection bias / reverse causality

해당 구분은 final report 의 coefficient table 에서 명시 (★ 표시 등).

## 10. 다음 단계

### Week 1 Day 5 종료 시
- 본 문서 의 §6 final variable list 확정
- `experiments/structural_v1/data_prep.py` 작성 완료
- Descriptive statistics + plots 산출

### Week 2 시작 조건
- 본 문서 의 spec 이 fix
- `data_prep.py` 가 V5 eval framework 와 호환 (3 seeds × LAO split)
- VIF 검증 완료
