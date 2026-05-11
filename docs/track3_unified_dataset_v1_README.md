# Track 3 Unified Dataset v1 — README

> **작성일**: 2026-05-11
> **브랜치**: `exp/track3-unified-dataset`
> **상태**: ✅ v1 확정 (validation 11/11 PASS, 팀원 공유 준비됨)

## 1. 데이터셋 목적

Track 3 신규 모델 (선형 + 비선형 hybrid) 학습용 통합 데이터셋. Artsy / Saatchi / Artue 3개 source 의 한국 작가 작품을 unified schema로 결합.

### 1.1 운영 원칙 (필수 제약 — Codex 사전 조율)

| 원칙 | 적용 |
|---|---|
| **신규 작가 운영 가능** | 외부 platform 의존 features 제외 (followers / total_works / gallery_tier 등) |
| **운영 입력 가능 features만** | 작품 물성 + self-reported artist metadata + missingness flags |
| **Missingness explicit** | `has_depth` / `has_year_made` / `has_birth_year` / `has_nationality` flags |
| **Source neutral** | source_platform tag는 추적용 (모델 input 사용 권고 X) |

### 1.2 평가 기준 (모델 비교 시 적용)

| 기준 | 의미 |
|---|---|
| **Predictive performance** | MdAPE / MAE (artist-holdout cold-start 기준) |
| **Parsimony** | 피처 수 적게 동등 성능이면 우월 (단순한 모델 선호) |
| **Generalization** | cold-start (unmatched artist) 분포에서 robust |
| **Latency** | serving cost / model complexity |

본 데이터셋은 18개 features를 제공 (cold-start 13 + enrichment 5). 모델 실험 시 일부만 선택 사용 가능 — **적은 피처로 비슷한 성능이면 그쪽이 선호됨**.

## 2. 파일 위치

| 파일 | 설명 |
|---|---|
| `data/track3_unified_v1.parquet` | 메인 데이터셋 (41,366 rows × 24 cols, ~1.3MB) |
| `data/track3_unified_v1_summary.json` | 분포/통계 summary |
| `scripts/track3/build_unified_dataset.py` | Pipeline (재생성 가능) |
| `scripts/track3/validate_unified_dataset.py` | Validation (11 checks) |

**Git 상태**: `.parquet` / `data/*.json`은 `.gitignore`. 데이터셋 자체는 git에 들어가지 않음 — 별도 sharing (S3 / Drive / 직접 전달) 필요.

## 3. Schema (24 columns)

### 3.1 IDs (4) — 모델 input 아님, 추적/매칭용

| Column | Type | Description |
|---|---|---|
| `source_platform` | str (artsy/saatchi/artue) | 데이터 origin |
| `source_listing_id` | str | 원본 platform의 artwork ID |
| `artist_entity_id_raw` | str | 원본 platform의 artist ID (Artsy slug / Saatchi numeric / Artue handle) |
| `artist_name_raw` | str | 원본 platform의 artist name |

### 3.2 Cold-start core features (13) — 신규 작가에서도 수집 가능

| Column | Type | Source coverage | Description |
|---|---|---|---|
| `medium_category` | categorical (8) | 100% | oil / acrylic / ink / watercolor / pigment / mixed / pastel / pencil / other |
| `support_category` | categorical (7) | 100% | canvas / paper / linen / panel / silk / metal / other |
| `attribution_class` | categorical (2) | 100% | unique / edition |
| `width_cm` | float | 100% | 가로 (cm) |
| `height_cm` | float | 100% | 세로 (cm) |
| `depth_cm` | float | 78% measured | 깊이 (cm). measured 안 됨 → 0 + `has_depth`=0 |
| `has_depth` | binary | 100% | depth_cm > 0 |
| `area_cm2` | float | 100% | width × height |
| `log_area` | float | 100% | log(area_cm2) — heavy tail 안정화 |
| `orientation` | categorical (4) | 100% | portrait / landscape / square / unknown |
| `year_made` | int | 31% measured | 제작연도 (1800-2030). missing → 0 |
| `has_year_made` | binary | 100% | year_made > 0 |
| `age_years` | float | 31% measured | 2026 - year_made (현재 기준). missing → 0 |

### 3.3 Enrichment features (5) — Saatchi/Artue 일부 누락 OK

| Column | Type | Source coverage | Description |
|---|---|---|---|
| `artist_birth_year` | int | 21% measured | 작가 생년 (Artsy only). missing → 0 |
| `has_birth_year` | binary | 100% | artist_birth_year > 0 |
| `artist_age_at_execution` | float | 21% measured | year_made - birth_year. missing → 0 |
| `nationality_region` | categorical (5) | 100% | korea / asia_other / north_america / europe / other / unknown |
| `has_nationality` | binary | 100% | nationality 정보 있음 |

### 3.4 Target (2)

| Column | Type | Description |
|---|---|---|
| `price_krw` | int | 한화 가격 (100K ~ 5B 필터됨) |
| `ln_price_krw` | float | log(price_krw) — 학습 target |

## 4. 데이터 분포

### 4.1 Row counts

| Source | Rows | Filter loss (raw → kept) |
|---|---:|---:|
| **Artsy** | 10,934 | 30,046 → 10,934 (36%) — 가격 비공개 많음 |
| **Saatchi** | 27,654 | 30,607 → 27,654 (90%) |
| **Artue** | 2,778 | 2,783 → 2,778 (99.8%) |
| **합계** | **41,366** | 63,436 → 41,366 (65%) |

### 4.2 Per-source missingness (has_X=1 비율)

| Flag | Artsy | Saatchi | Artue |
|---|---:|---:|---:|
| `has_depth` | 29% | **~100%** | 60% |
| `has_year_made` | **100%** | **0%** | 74% |
| `has_birth_year` | **81%** | **0%** | **0%** |
| `has_nationality` | 100% | 100% | ~100% |

**중요**: Saatchi raw에 year_made/birth_year 없음, Artue raw에 birth_year 없음. has_X=0 flag로 missingness explicit.

### 4.3 Price stats (KRW)

- median: 2,684,100
- mean: 9,016,013
- Q05 / Q95: 280,000 / 31,050,000
- range: 100K ~ 5B (필터됨)

### 4.4 Categorical distributions

- `attribution_class`: unique 40,423 (98%) / edition 943 (2%)
- `orientation`: portrait 17,313 / landscape 15,278 / square 8,775
- `medium_category` top: oil / acrylic / mixed / ink / pigment
- `nationality_region`: korea (대다수) / asia_other / 기타

## 5. Cross-source 작가 overlap (참고)

| Pair | Overlap (normalized name) |
|---|---:|
| Artsy ∩ Saatchi | 80 |
| Artsy ∩ Artue | 77 |
| Saatchi ∩ Artue | 9 |
| All 3 | 3 |
| **Union** | **3,218** |

대부분 disjoint. 작가 단위 dedup 필요 시 `artist_name_raw` 정규화 매핑 별도 진행 권고.

## 6. 사용 예시

### 6.1 데이터 로드

```python
import pandas as pd
df = pd.read_parquet("data/track3_unified_v1.parquet")
print(df.shape)  # (41366, 24)
```

### 6.2 Train/test split — artist-holdout (cold-start 평가)

```python
from sklearn.model_selection import GroupShuffleSplit

X_cols = [
    "medium_category", "support_category", "attribution_class",
    "width_cm", "height_cm", "depth_cm", "has_depth",
    "area_cm2", "log_area", "orientation",
    "year_made", "has_year_made", "age_years",
    "artist_birth_year", "has_birth_year", "artist_age_at_execution",
    "nationality_region", "has_nationality",
]
X = df[X_cols]
y = df["ln_price_krw"]
groups = df["artist_entity_id_raw"]

splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups))
```

### 6.3 Linear baseline (hedonic regression)

```python
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import Ridge

# Encode categoricals
cat_cols = ["medium_category", "support_category", "attribution_class",
            "orientation", "nationality_region"]
num_cols = [c for c in X_cols if c not in cat_cols]

# (실제 baseline은 ColumnTransformer + Pipeline 권고)
```

### 6.4 CatBoost (nonlinear)

```python
from catboost import CatBoostRegressor, Pool

cat_idx = [X_cols.index(c) for c in cat_cols]
pool = Pool(X.iloc[train_idx], y.iloc[train_idx], cat_features=cat_idx)
model = CatBoostRegressor(verbose=100)
model.fit(pool)
```

### 6.5 재생성 + 검증

```bash
PYTHONPATH=src python3 scripts/track3/build_unified_dataset.py
PYTHONPATH=src python3 scripts/track3/validate_unified_dataset.py  # 11/11 PASS
```

## 7. Validation (자동 11 checks)

| # | Check | 통과 기준 |
|---|---|---|
| 1 | File existence | parquet + summary 존재 |
| 2 | Schema (24 cols + 순서) | EXPECTED_COLS 일치 |
| 3 | Row count | ≥ 1,000 |
| 4 | Source distribution | {artsy, saatchi, artue} |
| 5 | Price range filter | [100K, 5B] |
| 6 | ln_price_krw consistency | max diff < 1e-6 |
| 7 | Size | width/height > 1, area = w*h |
| 8 | Categorical values | orientation/attribution 허용 set |
| 9 | has_X flag consistency | flag == (value > 0) |
| 10 | Missingness rates | informational (always PASS) |
| 11 | No null | 전 column NaN 없음 |

**현 상태**: ✅ 11/11 PASS

## 8. 알려진 제약 (Known Limitations)

1. **Saatchi year_made/birth_year 0%** — has_X=0 flag로 explicit. 모델이 이를 missingness signal로 학습.
2. **Artue birth_year 0%** — 동일.
3. **Artsy 가격 공개 36%만** — Saatchi/Artue 대비 sparse.
4. **Cross-source 작가 disjoint** — 80~89 작가만 cross-source overlap. 작가 단위 통합 분석은 별도 작업.
5. **Gallery 정보 없음** — Track 1 교훈으로 의도 제외 (train-only signal).
6. **Followers / total_works 없음** — Track 1 PR-29F 결과 정합 (운영 입력 불가).

## 9. Track 1 모델과의 비교

| 항목 | Track 1 v3_filtered_tuned_29_hf_htw | Track 3 unified v1 |
|---|---|---|
| Features | 29 (cold-start core 27 + has flags) | 18 (cold-start 13 + enrichment 5) |
| Rows | 28,376 (Artsy 7,640 + Saatchi 21,721 trained) | **41,366** (+Artue 2,778) |
| Source feature | 제거됨 (PR-29F) | 제거됨 |
| Gallery features | 제거됨 (gallery_tier) | 제거됨 |
| Follower / total_works | flag로 유지 | **제거됨** (운영 미수집) |
| year_made | V_year_saatchi_warm variant만 | **모든 row** + has_year_made flag |
| Hedonic baseline | 시도 X | **권장** |
| 학습 분포 | Artsy + Saatchi (Korean) | Artsy + Saatchi + Artue (Korean) |

Track 3는 **운영 fidelity 최우선** + **신규 작가 cold-start 강화** 방향.

## 10. 후속 작업 (Roadmap)

1. **Pilot linear baseline** (Codex 권고) — Ridge regression + log_area + categoricals
2. **CatBoost baseline** — 동일 features
3. **Linear + nonlinear ensemble**
4. **Cross-source dedup** — artist normalization 별도 PR
5. **Two-stage model** — matched (warm artist) + unmatched (cold-start) 분리
6. **Feature subset search** — parsimony 원칙: 적은 피처로 비슷 성능이면 그쪽 채택 (e.g. size + medium만으로 hedonic, 그 후 +1 feature씩 incremental)

## 11. 팀 공유

데이터셋 자체 (1.3MB parquet) 공유 방법:
- **option A**: S3 / GCS 업로드 + signed URL
- **option B**: Google Drive / Dropbox 폴더 공유
- **option C**: 직접 전달 (USB / 이메일 첨부)
- **option D**: 팀 내부 NAS 또는 데이터 lake

각 팀원은 다음 환경에서 작업 가능:
- `git clone` + branch `exp/track3-unified-dataset` checkout
- Parquet 파일 수령 후 `data/track3_unified_v1.parquet` 위치에 배치
- `pip install pandas pyarrow catboost scikit-learn` (필수)
- `python3 scripts/track3/validate_unified_dataset.py` (sanity check)
- 사용 예시 §6 참조

## 12. 변경 이력

- **v1 (2026-05-11)**: 초기 release. 41,366 rows / 24 cols. Codex schema v1 정합.

## 13. 참고 자료

- Codex 사전 조율: 본 session conversation 참조
- Track 1 본 세션 audit: `docs/track1_session_complete_20260511.html`
- Source 데이터:
  - Artsy: `data/artsy_kr_artworks.csv` (30,046 raw rows)
  - Saatchi: `data/saatchi_kr_artworks.csv` (30,607 raw rows)
  - Artue: `data/artue_테스트_가격포함.csv` (2,783 raw rows)
