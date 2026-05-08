# Tier CSV cleanup — 결과 보고서

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: Tier CSV 의 계산 column 정합성 검수 + 코덱스 의견 반영 의 cleansed CSV + column dictionary 산출
> **Decision binding**: ❌ **X** — 정리 자료 만 / 운영 코드 / `data/saatchi_cleaned.parquet` / `load_data()` / feature generation 로직 변경 X / 운영 채택 = 별도 검증 + 사용자 결정
> **사전 자문**: 코덱스 (제거 / 분리 / 보존+정의명시 / 한글 header 형식 권고)
> **검수 코드**: `scripts/verify_dataset_computed_columns.py`
> **검수 결과**: `experiments/structural_v1/results/dataset_computed_columns_verification_20260508.json`
> **Cleanup 코드**: `scripts/cleanup_dataset_tier_csv.py`
> **산출 영역**: `data/dataset_tiers_cleansed_20260508/`

## 0. 한 줄 요약

> 66 columns 의 검수 → **51 보존 + 2 분리 + 13 제거** 적용 한 cleansed Tier CSV (T0-T6) + 별도 column dictionary + 한글 column 명 사람용 파생본 산출. 운영 코드 / parquet 변경 X (read-only).

## 1. 검수 결과 (66 전체 columns 중 28 계산/파생 column 의 분류)

> **본 절 의 분류 합계 = 28** (= EXACT 12 + MISMATCH 1 + PLACEHOLDER 3 + SPARSE 3 + REQUIRES_SOURCE_AUDIT 5 + OK 4). 이는 **66 전체 column 중 의 계산 / 파생 / placeholder column 영역 만** 의 분류 / 나머지 38 column = identifier (6) + 수집 raw (8) + 수집+환산 (1) + 수집/enrichment / regex (2) + 수집→정규화 (3) + categorical 정규화 (7) + training_metadata (3) + mediums_json/supports_json (2) + 검증 외 derivation (6) 영역 의 직접 검증 외.

### 1.1 EXACT (12) — 정확 일치 / 보존 의무

```
ln_price, ln_area, ln_ho, ho_power, is_small,
is_unique, is_edition, is_krw, work_age,
has_year_made, has_birth_year, ho_x_support
```

각 정의 와 실제 값 의 max abs diff < 1e-9 (= 정확 동일).

### 1.2 MISMATCH (1) — `has_international`

- 정의: `1 if gallery_city_count >= 2 else 0`
- 실측: Saatchi rows 의 `gallery_city_count == 1` + `has_international == 1` 의 mismatch (Saatchi 영역 의 source-conditional definition)
- **코덱스 권고**: 보존 + 정의 명시 ("Artsy: city_count>=2 / Saatchi: source policy 항상 1")

### 1.3 PLACEHOLDER (3) — 100% zero

```
ho_price_level, medium_price_level, profile_completeness
```

operational `load_data()` 가 0.0 fill / source 미존재 / 모델 noise feature.

**코덱스 권고**: 즉시 제거.

### 1.4 SPARSE (3) — 95%+ zero / 변별력 거의 없음

| Column | zero/false 비율 |
|---|---|
| `request_ratio` | 94.69% zero (Artsy 만) |
| `artist_is_p1` | 99.68% False |
| `has_special_finish` | 99.59% zero |

**코덱스 권고**: 즉시 제거.

### 1.5 REQUIRES_SOURCE_AUDIT (5) — raw column 미포함 / 검수 불가

```
has_seoul       (raw gallery_cities 미포함)
ln_followers    (raw artist_followers 미포함)
has_depth       (raw depth_cm 미포함)
vintage_premium (career_stage_int 미포함 / 99.93% zero — 사실상 미작동)
freshness_discount (career_stage_int 미포함)
```

**코덱스 권고**: 본 cycle 산출물 에서 제외 + audit backlog (운영 채택 시 별도 검증 의무).

### 1.6 OK (4) — categorical 분포 정상

```
medium_category   (9 unique values)
support_type      (7 unique values)
gallery_type      (2 unique values)
attribution_class (4 unique values)
```

## 2. 코덱스 의견 (반영)

> 코덱스 자문 결과 정리:

### 2.1 Short list

| 분류 | columns |
|---|---|
| **즉시 제거 (13)** | placeholder 3 + sparse 3 + 미작동 2 (vintage_premium / freshness_discount) + empty 2 (value_grade_note / exclude_reason) + REQUIRES_SOURCE_AUDIT 3 (has_seoul / ln_followers / has_depth) |
| **분리 보존 (2)** | mediums_json / supports_json (UI 표시 용 / cleansed CSV 본체 미포함) |
| **보존 + 정의 명시 (1)** | has_international (source-conditional operational flag) |
| **보존 (50)** | EXACT 12 + identifier 6 + 수집 raw + categorical 정규화 + 검수 통과 |

> **총 보존 51 = 일반 보존 50 + 보존+정의명시 1** (cleansed CSV body 의 column 수 51 정합). + 분리 2 (display companion) + 제거 13 = **66 (원본 column 수) 정합**.

### 2.2 한글 header 형식

코덱스 권고 1순위 = **옵션 C (별도 dictionary)** — 영문 column 명 유지 / column_dictionary.csv 별도. 본 cycle = 권고 그대로 적용.

추가 옵션 = **human_readable_T0.csv** (한글 column 명 사람용 파생본) — 사용자 가 직접 보기 편한 형식.

### 2.3 Decision binding 명시 (의무)

> 본 cycle 산출물 = Tier CSV 계산 컬럼 검수 및 정리 자료 / decision-binding 결과물 X / 운영 코드 / parquet / `load_data()` / feature generation 로직 변경은 본 범위에 포함되지 않음 / 운영 채택 = 별도 검증 + 사용자 결정.

## 3. 산출 파일 (`data/dataset_tiers_cleansed_20260508/`)

| 파일 | rows | cols | 크기 |
|---|---:|---:|---:|
| `T0_operational_28376_cleansed.csv` | 28,376 | 51 | 14.64 MB |
| `T1_artsy_only_cleansed.csv` | 7,289 | 51 | 3.83 MB |
| `T2_artsy_year_notna_cleansed.csv` | 7,231 | 51 | 3.80 MB |
| `T3_artsy_year_birth_notna_cleansed.csv` | 5,845 | 51 | 3.08 MB |
| `T4_artsy_strict_4field_cleansed.csv` | 4,628 | 51 | 2.47 MB |
| `T5_krw_only_cleansed.csv` | 868 | 51 | 0.47 MB |
| `T6_t4_anomaly_filtered_cleansed.csv` | 4,460 | 51 | 2.38 MB |
| `display_companion_T0.csv` | 28,376 | 5 | mediums_json / supports_json 분리 보존 |
| `human_readable_T0.csv` | 28,376 | 51 | 한글 column 명 사람용 파생본 |
| `column_dictionary.csv` | 66 entries | 6 | 영문 / 한글 / 분류 / 정의 / 처리결정 / 사유 |
| `INDEX.json` / `INDEX.md` | — | — | summary index |

> 모든 CSV = `*.csv` gitignore 영역 (자동 추적 X / working tree only).

## 4. 보존 columns (51 / cleansed CSV body)

### 4.1 분류별 분포

| 분류 | n | 예시 |
|---|---|---|
| identifier | 6 | artwork_id / artist_slug / artist_name / title / image_url / artwork_url |
| 수집 raw | 8 | price_raw / price_currency / dimensions_cm / medium / artist_total_works / gallery_name / gallery_type / source |
| 수집+환산 | 1 | price_krw |
| 계산 (EXACT 검증) | 12 | ln_price / ln_area / ln_ho / ho_power / is_small / is_unique / is_edition / is_krw / work_age / has_year_made / has_birth_year / ho_x_support |
| 계산 (검증 통과 / 일부 derivation) | 9 | area_cm2 / aspect_ratio / ho / support_factor / has_multimedia / career_age / career_stage / for_sale_ratio / gallery_city_count |
| 계산 (source-conditional) | 1 | has_international (Artsy: city_count>=2 / Saatchi: 항상 1) |
| 수집/enrichment | 1 | year_made (Artsy 직접 / Saatchi PR #51 enrichment) |
| 수집/regex 추출 | 1 | artist_birth_year (Artsy 직접 / Saatchi bio regex) |
| 수집→정규화 | 3 | solo_count / group_count / fair_count |
| categorical 정규화 | 7 | medium_category / medium_l1 / medium_leaf / support_type / support_l1 / support_leaf / attribution_class |
| 계산 (gallery_alias_map) | 1 | gallery_tier |
| training_metadata | 1 | is_excluded_for_training |

## 5. 제거 columns (13 / 사유 명시)

| Column | 사유 |
|---|---|
| ho_price_level | 100% zero / placeholder |
| medium_price_level | 100% zero / placeholder |
| profile_completeness | 100% zero / placeholder |
| request_ratio | 94.69% zero / sparse / Artsy only |
| artist_is_p1 | 99.68% False / sparse |
| has_special_finish | 99.59% zero / sparse (변별력 거의 없음) |
| vintage_premium | 99.93% zero / 사실상 미작동 |
| freshness_discount | career_stage_int 미포함 / 검수 불가 |
| value_grade_note | 99.09% empty |
| exclude_reason | T0 = filter 후 100% empty |
| has_seoul | raw gallery_cities 미포함 / 검수 불가 (audit backlog) |
| ln_followers | raw artist_followers 미포함 / 검수 불가 (audit backlog) |
| has_depth | raw depth_cm 미포함 / 검수 불가 (audit backlog) |

## 6. Decision binding (반복 명시)

❌ **본 cycle = 정리 자료 만 / 분석적 증거 갱신 X**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | **변경 X** |
| B-2 (artifact reproducibility) verdict (PASS) | **변경 X** |
| Saatchi enrichment 복원 cycle (PR #51) verdict (PASS) | **변경 X** |
| Audit (PR #50) cleansed dataset 후보 (T0-T6) | **변경 X** (본 cycle = 동일 Tier 정의 유지 / column 영역 만 정리) |
| birthyear regex pilot (PR #52) verdict (FAIL) | **변경 X** (pilot 미적용) |
| 트랙 1 / 트랙 2 efficacy claim | **갱신 X** |
| 운영 채택 결정 | **영향 X** |
| 운영 `prepare_saatchi_dataset.py` / `train_primary_market_v3_filtered.py` / `load_data()` | **변경 X** |
| 운영 `data/saatchi_cleaned.parquet` / `data/primary_market_dataset.parquet` | **변경 X** |
| 외부 보고서 | 본 결과 미반영 영역 |

**본 cycle 의 영향 영역 만**:
- ✅ cleansed CSV (10 파일) = 데이터셋 의사결정 의 **사용자 검토 자료** (별도 prereg 의무 시)
- ✅ column_dictionary.csv = 운영 / 후속 cycle 의 column 영역 의 **참고 자료**
- ❌ 운영 코드 / 모델 / 데이터 변경 X

## 7. 사용자 의사결정 가능 영역 (본 cycle 영향 X)

본 cleansed CSV + column_dictionary 의 활용 영역 (모두 별도 prereg cycle 의무):

1. **Tier 채택 결정**: T0 / T1 / T3 / T4 / T5 / T6 중 선택 — 별도 prereg
2. **운영 데이터셋 컬럼 정리 적용**: 본 cycle 의 13 제거 column 의 운영 적용 — 별도 prereg + decision-binding cycle
3. **REQUIRES_SOURCE_AUDIT column 의 source 검증 cycle**: has_seoul / ln_followers / has_depth / vintage_premium / freshness_discount — 별도 audit cycle
4. **B-3 cycle 의 모집단 정의**: 본 cleansed CSV 의 정량 입력

## 8. 다음 단계

1. ✅ 본 결과 보고서 코덱스 사후 검수
2. ⏳ PR 작성 + merge (cleansed CSV 자료 만 / 운영 변경 X)
3. ⏳ (사용자 결정) 후속 cycle 진입

## 9. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Cleanup 사전 자문 (2026-05-08) | 제거 13 / 분리 2 / 보존+정의명시 1 / 한글 header 형식 옵션 C (별도 dictionary) 권고 + decision-binding 명시 의무 |
| 본 결과 보고서 round 1 사후 검수 (2026-05-08, NEEDS FIX) | P1×3 (§1 = 28 분류 vs 66 전체 의 관계 명시 / §2.1 = 보존 51 = 50 + 1 명시 / §5 has_special_finish 사유 sparse 통일) — round 1 fix |
| 본 결과 보고서 round 2 사후 검수 (2026-05-08, **GO**) | 미충족 영역 없음 / 신규 issue 없음 |
