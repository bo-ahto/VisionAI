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
| `data/track3_unified_v1.parquet` | 메인 데이터셋 (41,365 rows × 20 cols, ~1.3MB) |
| `data/track3_unified_v1.csv` | CSV export (6.0 MB, UTF-8 BOM) |
| `data/track3_unified_v1_sample.csv` | 100 rows/source = 300 rows (44 KB) |
| `data/track3_unified_v1_summary.json` | 분포/통계 summary |
| `scripts/track3/build_unified_dataset.py` | Pipeline (재생성 가능) |
| `scripts/track3/validate_unified_dataset.py` | Validation (11 checks) |

**Git 상태**: `.parquet` / `data/*.json`은 `.gitignore`. 데이터셋 자체는 git에 들어가지 않음 — 별도 sharing (S3 / Drive / 직접 전달) 필요.

## 3. Schema v3 (15 columns)

> **변경 이력 (User 요구)**: v1 (24) → v2 (17) → v3 (15). 9 columns 제거.
> 1) 3 source raw에 systematic absence 컬럼 (v2)
> 2) 변별력 없는 컬럼 (v3 — 95%+ same value)

### 3.0 v1 → v3 변경 (제거됨)

| 제거 column | 이유 | Version |
|---|---|---|
| `year_made` / `has_year_made` / `age_years` | Saatchi raw에 없음 | v2 |
| `artist_birth_year` / `has_birth_year` / `artist_age_at_execution` | Saatchi/Artue raw에 없음 | v2 |
| `attribution_class` | Saatchi/Artue raw에 없음 (추정만 가능) | v2 |
| `nationality_region` | **98.4% korea** (변별력 없음) | **v3** |
| `has_nationality` | **100% = 1** (사실상 constant) | **v3** |

### 3.1 IDs (5) — 모델 input 아님, 추적/매칭용

| Column | Type | Description |
|---|---|---|
| `source_platform` | str (artsy/saatchi/artue) | 데이터 origin |
| `source_listing_id` | str | 원본 platform의 artwork ID |
| `artist_entity_id_raw` | str | 원본 platform의 artist ID (Artsy slug / Saatchi numeric / Artue handle) |
| `artist_name_raw` | str | 원본 platform의 artist name (영문) |
| `artist_name_ko` | str / null | **한글명** (매핑 source 통합 + name-order swap + raw 한글 추출, 11.8% 매칭) |

#### 작가 한글명 매핑 (artist_name_ko) 변환 규칙

**4 단계 cascading** (User 한국어 이름 규칙 반영):

1. **매핑 source 통합 lookup**: 5 source 파일 (`artist_profiles.csv`, `artist_slug_mapping_expanded.csv`, `merged_artist_profiles.csv`, `kada_artist_profiles.csv`, `wikidata_korean_artists.csv`) → 영문명 ↔ 한글명 dict (5,671 entries).
2. **Name-order swap**: 한국식 (Last First) ↔ 서양식 (First Last) 두 순서 모두 시도.
   - 예: "Lee Ufan" → "leeufan" + "ufanlee" 둘 다 lookup
3. **Raw 한글 추출 fallback**: artist_name_raw에 한글 character 있으면 추출 (e.g. "Songfeel 송필" → "송필").
4. **한국 성 (Surname) Romanization 매핑** (신규): 영문 last token이 한국 성 표 (`KOREAN_SURNAME_TO_KO`, 60+ entries) 매칭 시 한글 성 + 영문 first name 형식 부여.
   - User 단서: "1음절이면 성, 2음절이 붙는 게 이름"
   - 예: `Eun-hye Seo` → `서 Eunhye` (Seo=서, Eun-hye=Eunhye)
   - 예: `mihyun kim` → `김 Mihyun`
   - 한국식 "Last First" 순서도 동시 시도: `Kim Hongbin` → `김 Hongbin`

**한국 성 표 커버**: Top 60 성씨 (인구 95%+ cover). Kim/Lee/Park/Choi/Jung/Kang/Cho/Yoon/Jang/Lim/Han/Shin/Seo/Kwon/Hwang/Ahn/Song/Yoo/Hong/Jeon/Ko/Moon/Yang/Son/Bae/Baek 등.

**매핑 placeholder 제외**: kada 등 일부 source에서 "중견작가" / "신진작가" 같은 generic placeholder는 제외.

**매칭률 (v7 — Romanization → Hangul 음역 적용)**:
- 전체: **41,365 / 41,365 (100.0%)** ⬆️⬆️
- Unique artists 단위: 2,185 unique ko names

**v7 cascading 단계 (lookup_artist_name_ko)**:
1. **Stage 1 — dict exact lookup**: 작가별 한글명 sheet 매핑 (5대 source 통합, 5,671 entries)
2. **Stage 2 — raw 한글 추출**: `artist_name_raw`에 한글 포함 시 그대로 사용 (예: `"Songfeel 송필" → 송필`)
3. **Stage 3a — 한국 성 + 한글 음역 ("First Last" 형식)**: last token이 한국 성이면 성+이름음역
   - `Yeji Seok → 석예지`, `Lee Yejoo → 이예주`, `Seontae Hwang → 황선태`
4. **Stage 3b — 한국 성 + 한글 음역 ("Last First" 한국식)**: first token이 한국 성
   - `Bang Soyun → 방소윤`, `Kim Hongbin → 김홍빈`, `Hyuckjin Oh → 오혁진` (Oh가 last면 3a 적용)
5. **Stage 4 — 외국인 이름 전체 음역**: 한국 성 매칭 실패 시 전체 영문을 한글 발음으로 음역
   - `Maria Santos → 마리아산토스`, `Smith John → 스미트흐조흐느`
6. **Stage 5 — None**: 빈 입력 등

**음역 방식 (Romanization → Hangul)**:
- `HANGUL_SYLLABLE_MAP` (~350 entries): 5-char → 4-char → 3-char → 2-char → 1-char greedy longest match
- 한국 이름 first name 음절 cover (자음+모음+받침 형식): `byung→병`, `hyun→현`, `seok→석`, `hong→홍`, `eun→은` 등
- 외국 이름은 1-char fallback ("smith" → "스미트흐")로 처리 — 정확하지 않으나 user 의도 "최대한 한글로 표기" 충족

**예시**:
| `artist_name_raw` | `artist_name_ko` (v7) | 비고 |
|---|---|---|
| `Seontae Hwang` | `황선태` | Stage 3a — Hwang=황 surname |
| `Lee Yejoo` | `이예주` | Stage 3a — Lee=이 surname |
| `Yeji Seok` | `석예지` | Stage 3a — Seok=석 surname |
| `Bang Soyun` | `방소윤` | Stage 3b — Bang=방 surname |
| `Kim Hongbin` | `김홍빈` | Stage 3b — Kim=김 surname |
| `ByungHo Lee` | `이병호` | Stage 3a — byung=병 5-char syllable |
| `Hyuckjin Oh` | `오혁진` | Stage 3a — Oh=오, hyuck=혁 |
| `Hye Rim Baek` | `백혜림` | Stage 3a — Baek=백, rim=림 |
| `Bonhwa Cho` | `조본화` | Stage 3a — Cho=조 |
| `Nam June Paik` | `백남준` | Stage 1 dict — sheet 매핑 |
| `Maria Santos` | `마리아산토스` | Stage 4 — 외국 작가 음역 |

### 3.2 Cold-start core features (9) — 3 source 공통

| Column | Type | Source coverage | Description |
|---|---|---|---|
| `medium_category` | categorical (8) | 100% | oil / acrylic / ink / watercolor / pigment / mixed / pastel / pencil / other |
| `support_category` | categorical (7) | 100% | canvas / paper / linen / panel / silk / metal / other |
| `width_cm` | float | 100% | 가로 (cm) |
| `height_cm` | float | 100% | 세로 (cm) |
| `depth_cm` | float | 78% measured | 깊이 (cm). measured 안 됨 → 0 + `has_depth`=0 |
| `has_depth` | binary | 100% | depth_cm > 0 |
| `area_cm2` | float | 100% | width × height |
| `log_area` | float | 100% | log(area_cm2) — heavy tail 안정화 |
| `orientation` | categorical (4) | 100% | portrait / landscape / square / unknown |

### 3.3 Hybrid 가격 (4) — User 요구 정합

원본 표기 + 통일 환율 모두 제공. 환전 여부 명시.

| Column | Type | Description |
|---|---|---|
| `price_amount_raw` | float | **원본 통화 가격** (예: USD 12500.0 / EUR 2000.0 / KRW 3750000.0) |
| `price_currency_raw` | str | **원본 통화** (USD / KRW / EUR / GBP / HKD) |
| `price_krw` | int | source 표기 그대로 (Artsy/Saatchi raw 1,380 fixed / Artue 변동 환율) |
| `was_converted` | binary | **환전 여부** (0=원래 KRW, 1=외화 환전됨) |

**통일 환율 (UNIFIED_FX_TO_KRW)**: Track 1 + Artsy raw 정합 fixed rate.

| 통화 | KRW 환율 |
|---|---:|
| USD | 1,380 |
| EUR | 1,530 |
| GBP | 1,780 |
| HKD | 178 |
| KRW | 1.0 (identity) |

### 3.4 Target (2)

| Column | Type | Description |
|---|---|---|
| `price_krw_unified` | int | **통일 환율 적용 KRW 가격** (학습/평가 standard, 100K ~ 5B 필터) |
| `ln_price_krw_unified` | float | log(price_krw_unified) — **학습 target** |

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

**Schema v3 적용 후**: 모든 feature가 3 source에서 raw 수집 가능 + 변별력 있음.

### 4.3 Price stats (KRW)

- median: 2,684,100
- mean: 9,016,013
- Q05 / Q95: 280,000 / 31,050,000
- range: 100K ~ 5B (필터됨)

### 4.4 Categorical distributions

- `orientation`: portrait 17,313 (42%) / landscape 15,278 (37%) / square 8,775 (21%)
- `medium_category` top: acrylic / oil / mixed / ink / pigment
- `support_category` top: canvas (59%) / paper / panel

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
cat_cols = ["medium_category", "support_category", "orientation"]
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
| 2 | Schema (15 cols + 순서) | EXPECTED_COLS 일치 |
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

1. **9 columns 제거됨** (v1 → v3): Saatchi/Artue raw에 systematic absent (year/birth/attribution — v2) + 변별력 없는 컬럼 (nationality 98.4% korea — v3). User 결정 반영.
2. **Artsy 가격 공개 36%만** — Saatchi/Artue 대비 sparse.
3. **Cross-source 작가 disjoint** — 80~89 작가만 cross-source overlap. 작가 단위 통합 분석은 별도 작업.
4. **Gallery 정보 없음** — Track 1 교훈으로 의도 제외 (train-only signal).
5. **Followers / total_works 없음** — Track 1 PR-29F 결과 정합 (운영 입력 불가).

## 9. Track 1 모델과의 비교

| 항목 | Track 1 v3_filtered_tuned_29_hf_htw | Track 3 unified v1 |
|---|---|---|
| Features | 29 (cold-start core 27 + has flags) | **9** (cold-start only — parsimony) |
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
- **v2 (2026-05-11)**: 41,366 rows / **17 cols**. 3 source raw에 없는 7 columns 제거.
- **v3 (2026-05-11)**: 41,366 rows / **15 cols**. 변별력 없는 2 columns 제거.
- **v4 (2026-05-11)**: 41,365 rows / **19 cols**. Hybrid 가격 추가 (price_amount_raw, price_currency_raw, was_converted) + 통일 환율 적용 (price_krw_unified, ln_price_krw_unified). target = ln_price_krw_unified.
- **v5 (2026-05-11)**: 41,365 rows / **20 cols**. `artist_name_ko` 추가 — 5 매핑 source 통합 + name-order swap + 한글 추출 fallback. 11.8% 매칭.
- **v6 (2026-05-11)**: 41,365 rows / **20 cols**. `artist_name_ko` 매칭 강화 — 한국 성 (Surname) Romanization 매핑 (60+ 성씨). 매칭률 **11.8% → 85.2%** (Saatchi 6% → 86%). 형식: full_hangul (11%) + surname_only "한글성+영문이름" (73%).
- **v7 (2026-05-11)**: 41,365 rows / **20 cols**. `artist_name_ko` — Romanization → Hangul 음역 도입 (`HANGUL_SYLLABLE_MAP` ~350 entries + greedy longest match). 외국인 작가도 한국어 발음 표기. 매칭률 **85.2% → 100.0%**. 형식: 한글 전용 (`황선태`, `이병호`, `오혁진` 등) — surname+영문 hybrid 폐기.

## 13. 참고 자료

- Codex 사전 조율: 본 session conversation 참조
- Track 1 본 세션 audit: `docs/track1_session_complete_20260511.html`
- Source 데이터:
  - Artsy: `data/artsy_kr_artworks.csv` (30,046 raw rows)
  - Saatchi: `data/saatchi_kr_artworks.csv` (30,607 raw rows)
  - Artue: `data/artue_테스트_가격포함.csv` (2,783 raw rows)
