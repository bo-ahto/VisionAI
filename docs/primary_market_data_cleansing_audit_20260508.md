# 1차 시장 데이터 cleansing audit (28,376 rows 기준)

> **작성일**: 2026-05-08
> **Source**: `data/primary_market_dataset.parquet` (Artsy 7,640) + `data/saatchi_cleaned.parquet` (Saatchi 21,721)
> **After `is_excluded_for_training==0` filter**: 28,376 rows (Artsy 7,289 + Saatchi 21,087)
> **Audit script**: `scripts/audit_primary_market_data.py`
> **Audit JSON**: `experiments/structural_v1/results/primary_market_audit_20260508.json`
> **Decision binding**: ❌ X — 본 cycle = 데이터 quality audit 만 / 운영 채택 결정 X / Cycle 1 verdict 무관

## 0. 한 줄 요약

> 운영 28,376 rows 의 **74.3% (Saatchi 21,087)** 가 `year_made` / `work_age` / `career_age` **100% 결측** + `has_seoul` / `is_krw` / gallery_type 등 **사실상 placeholder 영역**. 실측 + anomaly-free dataset = **4,460 rows (15.72%)** (Tier 6, Artsy 4-field notna + 컬럼별 anomaly 제거).

## 1. 결측 (실측 없음) 영역

### 1.1 Source-stratified 핵심 결측

| 컬럼 | Artsy (n=7,289) | Saatchi (n=21,087) | 전체 (n=28,376) |
|---|---|---|---|
| `year_made` notna | 7,231 (99.20%) | **0 (0.00%)** | 7,231 (25.48%) |
| `work_age` notna | 7,224 (99.11%) | **0 (0.00%)** | 7,224 (25.46%) |
| `artist_birth_year` notna | 5,888 (80.78%) | 1,952 (9.26%) | 7,840 (27.63%) |
| `career_age` notna | 5,599 (76.81%) | **0 (0.00%)** | 5,599 (19.73%) |
| `has_seoul` = 1 | 6,414 (88.00%) | **0 (0.00%)** | 6,414 (22.60%) |
| `is_krw` = 1 | 868 (11.91%) | **0 (0.00%)** | 868 (3.06%) |

> ⚠️ **Saatchi 21,087 rows = 메타데이터 의 거의 전부 가 결손/placeholder**. 운영 모델 의 32 features 중 핵심 시간 정보 (`year_made`, `work_age`, `career_age`) 가 전부 null → 모델 이 Saatchi rows 에서는 dimension + medium 정보 만으로 학습.

### 1.2 Placeholder 컬럼 (operational `load_data()` 가 0.0 으로 채움)

| 컬럼 | Zero/null 비율 | 비고 |
|---|---|---|
| `ho_price_level` | 100% zero | placeholder (실측 X) |
| `medium_price_level` | 100% zero | placeholder (실측 X) |
| `profile_completeness` | 100% zero | placeholder (실측 X) |
| `vintage_premium` | 99.93% zero | 사실상 미작동 |
| `value_grade_note` | 99.09% empty | 사실상 미작동 |
| `request_ratio` | 94.69% zero | 변별력 거의 없음 |
| `artist_is_p1` | 99.68% False | 변별력 거의 없음 |
| `has_special_finish` | 99.59% zero | 변별력 거의 없음 |
| `is_edition` | 99.88% zero | 사실상 모두 Unique |

### 1.3 단일 vs 결합 실측 row count

| 조건 | n | % |
|---|---|---|
| `year_made` notna | 7,231 | 25.48% |
| `artist_birth_year` notna | 7,840 | 27.63% |
| `career_age` notna | 5,599 | 19.73% |
| `work_age` notna | 7,224 | 25.46% |
| `year_made + artist_birth_year` 둘 다 notna | 5,845 | 20.60% |
| **4-field 전부 notna** (year + birth + career + work_age) | **4,628** | **16.31%** |

## 2. Anomaly (잘못된 데이터) 영역

### 2.1 가격 (price_krw)

| 항목 | n | 비고 |
|---|---|---|
| null / zero / negative | 0 | ✅ 정상 |
| < 100,000 KRW (10만원 미만) | 0 | ✅ 정상 |
| > 1,000,000,000 KRW (10억 초과) | 3 | outlier (1차 시장 의심) |
| > 5,000,000,000 KRW (50억 초과) | 0 | — |
| Range | [110,400, 4,968,000,000] | min ≈ 11만원 / max ≈ 49.68억원 |

### 2.2 크기 (area_cm2 / aspect_ratio / ho)

| 항목 | n | 비고 |
|---|---|---|
| `area_cm2` null / zero | 0 | ✅ 정상 |
| `area_cm2` < 100 cm² (10×10 미만) | 52 | 매우 작음 — 1차 시장 의심 |
| `area_cm2` > 50,000 cm² (224×224 초과) | 135 | 대형 |
| `area_cm2` > 100,000 cm² (316×316 초과) | 30 | **비정상 큰** (max 187,200 cm²) |
| `aspect_ratio` ≤ 0 / null | 0 | ✅ 정상 |
| `aspect_ratio` > 10 (1:10 초과) | 20 | **비정상 비율** |
| `ho` == 0 | 380 | 호수 미정/placeholder |
| `ho` > 200 (200호 초과) | 96 | **outlier** (max 500호) |

### 2.3 시간 (year_made / artist_birth_year / age 정합성)

| 항목 | n | 비고 |
|---|---|---|
| `year_made` > 2026 (미래 연도) | 5 | **데이터 오류** |
| `year_made` < 1900 | 9 | 너무 옛날 (1차 시장 의심) |
| `year_made` < 1950 | 12 | 1차 시장 의심 |
| `birth_year` > 2026 / < 1900 | 0 / 0 | ✅ 정상 |
| `year_made < birth_year` (논리 모순) | 2 | **데이터 오류** |
| `year_made - birth_year < 10` (10세 미만 작품) | 4 | **의심** |
| `year_made - birth_year < 18` (미성년 작품) | 32 | 일부 천재 작가 가능 / 다수 의심 |
| `work_age < 0` (미래 작품) | 5 | **데이터 오류** |
| `work_age > 100` | 2 | 1차 시장 의심 |
| `career_age < 0` / > 80 | 0 / 0 | ✅ 정상 |

### 2.4 Artist profile

| 항목 | n | 비고 |
|---|---|---|
| `artist_total_works` == 0 | 417 | **작가 정보 누락** |
| `for_sale_ratio` outside [0,1] | 0 | ✅ 정상 |
| `request_ratio` outside [0,1] | 0 | ✅ 정상 |
| `ln_followers` < 0 | 0 | ✅ 정상 |

### 2.5 Categorical placeholder

| 컬럼 | placeholder('other'/'unknown'/'') 비율 |
|---|---|
| `support_type` | 1,142 (4.02%) |
| `medium_category` | 1,144 (4.03%) |
| `attribution_class` | 0 (0.00%) — 99.87% 'Unique' |
| `gallery_type` | 0 (0.00%) |

### 2.6 Gallery

| 항목 | n |
|---|---|
| `gallery_name` empty/null | 0 |
| `gallery_tier` == 0 | 0 |
| `gallery_tier` > 5 | 0 |
| `gallery_city_count` == 0 | 116 |

### 2.7 단가 정합성 (KRW per cm²)

| 항목 | n / 값 |
|---|---|
| Median 단가 | 796.20 KRW/cm² |
| < 100 KRW/cm² (비정상 저가) | 154 (0.54%) |
| > 100,000 KRW/cm² (고가) | 55 (0.19%) |
| > 1,000,000 KRW/cm² (비정상 고가) | 2 (0.01%) |

## 3. Cleansed dataset 후보 (사용자 의사결정 영역)

| Tier | 정의 | n | n artists | % of T0 | 적합 영역 |
|---|---|---|---|---|---|
| **T0** | operational v3 (current) | 28,376 | 1,551 | 100.00% | 운영 production (메타데이터 결손 영역 다수) |
| **T1** | Artsy only | 7,289 | 734 | 25.69% | source 통일 + 메타데이터 결손 일부 보존 |
| **T2** | Artsy + `year_made` notna | 7,231 | 731 | 25.48% | 시간 실측 보장 |
| **T3** | Artsy + `year_made` + `birth_year` notna | 5,845 | 584 | 20.60% | 시간 + 작가 실측 |
| **T4** | Artsy + 4-field notna (year + birth + career + work_age) | 4,628 | 346 | 16.31% | 시간 영역 strict |
| **T5** | KRW only (`is_krw=1`) | 868 | 91 | 3.06% | 한국 1차 시장 직접 가격 (Artsy gallery 영역) |
| **T6** | T4 + 컬럼별 anomaly 제거 | **4,460** | **336** | **15.72%** | **strict 실측 + anomaly free** |

### 3.1 T6 의 anomaly filter 정의

T4 (Artsy + 4-field notna) + 다음 모두 충족:
- `100,000 < price_krw < 1,000,000,000` (10만 ≤ 가격 ≤ 10억)
- `100 < area_cm2 < 50,000` (10×10 ≤ 크기 ≤ 224×224)
- `0 < aspect_ratio ≤ 10`
- `0 < ho ≤ 200`
- `1950 ≤ year_made ≤ 2026`
- `year_made - artist_birth_year ≥ 10`
- `0 ≤ work_age ≤ 100`
- `artist_total_works > 0`
- `gallery_city_count > 0`

### 3.2 Tier 별 trade-off

| Tier | 강점 | 약점 |
|---|---|---|
| T0 | 최대 row 수 (28,376) | Saatchi 21,087 의 메타데이터 결손 (모델 이 효과적 학습 불가 가능성) |
| T1-T2 | source 통일 + 시간 실측 일부 | 행 수 75% 감소 / Saatchi 학습 데이터 손실 |
| T3-T4 | 시간 + 작가 실측 strict | 행 수 80%+ 감소 / 일반화 의문 |
| T5 | 한국 KRW 1차 시장 직접 가격 | 868 rows / 91 artists 매우 적음 |
| T6 | strict 실측 + anomaly free | 4,460 rows / 336 artists |

## 4. Trade-off 의 본질 (정량적 evidence)

### 4.1 운영 의 cold cell breakdown 과 의 정합

operational `_source_calibration.json` 의 cold cell 별 baseline MdAPE (B-2 reproduction 정합):

| Cell | n | Baseline MdAPE |
|---|---|---|
| **artsy_gallery** (= KRW 868 rows) | 868 | **24.34%** ⭐ |
| artsy_online | 6,421 | 35.04% |
| saatchi_online | 21,087 | 41.70% |

→ **artsy_gallery (KRW) cell 의 baseline MdAPE 24.34%** 가 saatchi_online 의 41.70% 의 약 60% 수준 — **메타데이터 quality 와 정확도 의 강한 상관 시사** (단정 X — confounder 가능 / 본 cycle 의 분석 영역 X).

### 4.2 Cycle 1 (Track 2 cold validation) 의 baseline 24.07% 와 의 관계

Cycle 1 의 Track 2 Stage 3 운영 채택 baseline 24.07% 는 **curated dataset (Artsy 8,495 row)** 기준. 본 audit 의 T5 (KRW 868) 의 artsy_gallery cell baseline 24.34% 와 정량 영역 동일 → curated quality 의 의미 정합.

> **단정 X**: T5 / artsy_gallery 가 "실측 보장" 영역 이지만, Cycle 1 의 broader 모집단 (8,495) retract 결과 (Random LAO 36.18% / Time-split 43.15%) 처럼 **strict 실측 영역 의 작은 모집단 도 별도 cold validation 의무**. 본 audit 만 으로 모델 적용 결정 X.

## 5. Decision binding 적용

> 본 cycle = 데이터 audit 만 / 운영 채택 / cleansed dataset 선택 / Cycle 1 verdict 변경 모두 영향 X

| 항목 | 본 audit 의 영향 |
|---|---|
| 운영 채택 결정 | ❌ 영향 X |
| Cycle 1 verdict (FAIL) | ❌ 변경 X |
| 트랙 1 / 트랙 2 efficacy | ❌ 갱신 X |
| Cleansed dataset 선택 | ❌ 본 audit 의 직접 결정 X (사용자 의사결정 영역) |
| 외부 보고서 | ❌ 본 결과 미반영 영역 |

**본 audit 의 가치 만**:
- ✅ 운영 28,376 rows 의 quality 영역 의 정량 문서화
- ✅ Cleansed dataset 후보 의 의사결정 가능한 형식 정리
- ✅ 운영 dataset 의 메타데이터 결손 영역 (Saatchi 21,087) 의 명시화

## 6. 사용자 의사결정 가능 영역

본 audit 결과 를 토대로 사용자 가 결정 가능한 영역 (본 cycle 영향 X):

1. **Cleansed dataset 선택**: T0 / T1 / T3 / T4 / T5 / T6 중 선택 (별도 prereg cycle 의무)
2. **Saatchi 영역 처리**: 운영 학습 의 21,087 rows 유지 vs 제외
3. **Anomaly filter 적용 여부**: T6 의 strict filter 도입 vs 점진적 적용
4. **B-3 cycle 의 모집단 정의**: 본 audit 의 결과 가 B-3 의 split 의 모집단 정의 의 입력 (별도 prereg)

## 7. 다음 단계 (조건부)

1. ✅ 본 audit 보고서 commit + PR
2. ⏳ 코덱스 audit 보고서 사후 검수
3. ⏳ (사용자 결정) Cleansed dataset 적용 cycle prereg (별도)
4. ⏳ (사용자 결정) B-3 cycle 의 모집단 정의 (본 audit 의 입력)

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 본 audit 보고서 사후 검수 (예정) | 본 commit 직후 |
