# 1차 시장 데이터 cleansing audit (28,376 rows 기준)

> **작성일**: 2026-05-08
> **Source**: `data/primary_market_dataset.parquet` (Artsy 7,640) + `data/saatchi_cleaned.parquet` (Saatchi 21,721)
> **After `is_excluded_for_training==0` filter**: 28,376 rows (Artsy 7,289 + Saatchi 21,087)
> **Audit script**: `scripts/audit_primary_market_data.py`
> **Audit JSON**: `experiments/structural_v1/results/primary_market_audit_20260508.json`
> **Decision binding**: ❌ X — 본 cycle = 데이터 quality 의 정량 관측 만 / 운영 채택 결정 X / Cycle 1 verdict 무관

## 0. 한 줄 요약

> 운영 28,376 rows 의 **74.3% (Saatchi 21,087)** 가 `year_made` / `work_age` / `career_age` **100% 결측** + `has_seoul` / `is_krw` / gallery_type 등 **가공 시 단일값으로 채워진 영역**. 본 audit 의 정의된 rule (T6) 적용 시 **rule-filtered subset = 4,460 rows (15.72%)**. 본 결과 의 모든 해석 = 관측 사실 만 / 운영 의사결정 / cleansed dataset 채택 / 모델 성능 인과 추론 모두 별도 prereg cycle 의무.

## 1. 결측 / placeholder 영역

### 1.1 Source-stratified 핵심 결측 (관측 사실)

| 컬럼 | Artsy (n=7,289) | Saatchi (n=21,087) | 전체 (n=28,376) |
|---|---|---|---|
| `year_made` notna | 7,231 (99.20%) | **0 (0.00%)** | 7,231 (25.48%) |
| `work_age` notna | 7,224 (99.11%) | **0 (0.00%)** | 7,224 (25.46%) |
| `artist_birth_year` notna | 5,888 (80.78%) | 1,952 (9.26%) | 7,840 (27.63%) |
| `career_age` notna | 5,599 (76.81%) | **0 (0.00%)** | 5,599 (19.73%) |
| `has_seoul` = 1 | 6,414 (88.00%) | **0 (0.00%)** | 6,414 (22.60%) |
| `is_krw` = 1 | 868 (11.91%) | **0 (0.00%)** | 868 (3.06%) |

> Saatchi 21,087 rows = 위 컬럼 영역 의 결측 / 단일값. **이 관측 가 모델 의 학습 효과 / Saatchi cell 의 cold MdAPE 41.70% 의 인과 영역 X** (본 audit 영역 외 / 별도 인과 cycle 의무).

### 1.2 Placeholder 컬럼 (taxonomy 분리)

#### 1.2.1 System-fill (operational `load_data()` 가 코드 로 채운 0.0)

| 컬럼 | Zero/null 비율 | 근거 |
|---|---|---|
| `ho_price_level` | 100% zero | `train_primary_market_v3_filtered.py:84-88` 의 if-fill |
| `medium_price_level` | 100% zero | 위 동일 |
| `profile_completeness` | 100% zero | 위 동일 |

위 3 컬럼 = source data 미존재 → operational 코드 가 0.0 으로 채움 (관측 사실 만 / 모델 영향 의 인과 해석 영역 X).

#### 1.2.2 원래 희소 (source data 의 sparse 분포)

| 컬럼 | Zero 비율 | 비고 |
|---|---|---|
| `vintage_premium` | 99.93% zero | source 의 sparse 분포 (placeholder 가 아닐 가능성) |
| `value_grade_note` | 99.09% empty | 위 동일 |
| `request_ratio` | 94.69% zero | 위 동일 |
| `artist_is_p1` | 99.68% False | 위 동일 (binary indicator) |
| `has_special_finish` | 99.59% zero | 위 동일 |
| `is_edition` | 99.88% zero | 99.87% Unique 와 정합 |

위 6 컬럼 = source data 의 자연스러운 sparse 분포. 모델 변별력 영역 의 해석 = 본 audit 영역 외.

### 1.3 단일 vs 결합 실측 row count (관측 사실)

| 조건 | n | % |
|---|---|---|
| `year_made` notna | 7,231 | 25.48% |
| `artist_birth_year` notna | 7,840 | 27.63% |
| `career_age` notna | 5,599 | 19.73% |
| `work_age` notna | 7,224 | 25.46% |
| `year_made + artist_birth_year` 둘 다 notna | 5,845 | 20.60% |
| **4-field 전부 notna** (year + birth + career + work_age) | **4,628** | **16.31%** |

## 2. Anomaly 영역 (taxonomy 분리)

### 2.1 Anomaly taxonomy

| 분류 | 의미 | 처리 정책 (본 audit 의 default) |
|---|---|---|
| **(A) Data 오류** | 논리적 불가능 / source 의 입력 오류 | T6 의 strict filter 에 포함 |
| **(B) 결손 placeholder** | source 미입력 / 0 으로 채워진 영역 | T6 strict filter 포함 |
| **(C) Scope exclusion** | 1차 시장 정의 외 가능성 | T6 conservative filter (anomaly cutoff X) |
| **(D) Rare outlier** | 통계적 outlier 이지만 valid 가능 | T6 conservative filter (제거 시 시장 영역 narrow 가능성) |

### 2.2 Anomaly 영역 의 rule 별 fail count (T0 28,376 기준)

| # | Rule | Fail n | 분류 | Threshold 근거 |
|---|---|---|---|---|
| 1 | `price_krw` null/zero/negative | 0 | A | source 의 정량 무결성 |
| 2 | `price_krw ≥ 1,000,000,000` (10억 이상) | 3 | D | 1차 시장 의 통상 범위 외 (운영 reported 의 max 약 49.68억 = outlier) |
| 3 | `area_cm2` null/zero | 0 | A | source 정량 무결성 |
| 4 | `area_cm2 ≤ 100` (10×10 이하) | 52 | C | 1차 시장 의 통상 작품 크기 의 conservative cutoff |
| 5 | `area_cm2 ≥ 50,000` (224×224 이상) | 135 | D | 운영 dataset 의 95-percentile 영역 의 conservative filter (anomaly cutoff X — 대형 valid 작품 가능) |
| 6 | `area_cm2 > 100,000` (316×316 초과) | 30 | D | 운영 max 187,200 cm² 영역 의 outlier (1차 시장 의 통상 외) |
| 7 | `aspect_ratio ≤ 0` / null | 0 | A | source 정량 무결성 |
| 8 | `aspect_ratio > 10` (1:10 초과) | 20 | D | 1차 시장 의 통상 작품 비율 의 conservative cutoff |
| 9 | `ho == 0` | 380 | B | placeholder (호수 미입력) |
| 10 | `ho > 200` (200호 초과) | 96 | D | 한국 호수 표기 의 통상 범위 외 (max 500호 = outlier) |
| 11 | `year_made > 2026` (미래 연도) | 5 | A | 데이터 오류 (현재 시점 외 미래) |
| 12 | `year_made < 1900` | 9 | C | 1차 시장 의 통상 영역 외 (오래된 작품) |
| 13 | `year_made < 1950` | 12 | C | T6 의 conservative scope filter (1차 시장 의 modern 영역) |
| 14 | `year_made < artist_birth_year` (논리 모순) | 2 | A | 데이터 오류 (작가 출생 이전 작품 불가) |
| 15 | `year_made - birth_year < 10` (10세 미만 작품) | 4 | A | 데이터 오류 (작가 10세 미만 의 작품 의문) |
| 16 | `year_made - birth_year < 18` (미성년 작품) | 32 | C | 일부 천재 작가 가능 / scope exclusion 의 conservative cutoff |
| 17 | `work_age < 0` (미래 작품) | 5 | A | 데이터 오류 |
| 18 | `work_age > 100` | 2 | C | 1차 시장 의 통상 범위 외 (오래된 작품) |
| 19 | `artist_total_works == 0` | 417 | B | placeholder (작가 정보 누락) |
| 20 | `gallery_city_count == 0` | 116 | B | placeholder (gallery 정보 결손) |
| 21 | `support_type` 'other' | 1,142 (4.02%) | B | placeholder (support 미분류) |
| 22 | `medium_category` 'other' | 1,144 (4.03%) | B | placeholder (medium 미분류) |
| 23 | Unit price (KRW/cm²) < 100 | 154 (0.54%) | D | 단가 outlier (저가 영역) |
| 24 | Unit price > 1M | 2 (0.01%) | D | 단가 outlier (고가 영역) |

> **Threshold 근거 의 본질**: 위 모든 threshold = **본 audit 의 conservative cutoff 정의 만**. 도메인 규칙 / percentile 기반 / 운영 범위 제한 의 정확 근거 = 본 audit 의 영역 외 (별도 도메인 정의 cycle 의무 — 사용자 / 도메인 전문가 결정 영역).

## 3. Cleansed dataset 후보 (사용자 의사결정 영역)

> ⚠️ **본 절 의 본질**: 아래 후보 = 보고서 의 권고 X / **사용자 가 후속 prereg + validation cycle 진입 시 의 선택지** 만. 각 Tier 의 적합성 / 운영 효과 = 본 audit 의 영역 외.

### 3.1 Tier 정의 + row counts

| Tier | 정의 | n | n artists | % of T0 |
|---|---|---|---|---|
| T0 | operational v3 (current) | 28,376 | 1,551 | 100.00% |
| T1 | Artsy only | 7,289 | 734 | 25.69% |
| T2 | Artsy + `year_made` notna | 7,231 | 731 | 25.48% |
| T3 | Artsy + `year_made` + `birth_year` notna | 5,845 | 584 | 20.60% |
| T4 | Artsy + 4-field notna (year + birth + career + work_age) | 4,628 | 346 | 16.31% |
| T5 | KRW only (`is_krw=1`) | 868 | 91 | 3.06% |
| T6 | T4 + 본 audit 의 rule-filter 적용 | **4,460** | **336** | **15.72%** |

### 3.2 T6 의 rule-filter 정의

T4 + 다음 모두 충족 (boundary 모두 strict — `>` / `<` / 단독 `≥` / `≤` 명시):

- `price_krw > 100,000` AND `price_krw < 1,000,000,000`
- `area_cm2 > 100` AND `area_cm2 < 50,000` ⚠️ (50,000 = conservative filter / anomaly cutoff X)
- `aspect_ratio > 0` AND `aspect_ratio ≤ 10`
- `ho > 0` AND `ho ≤ 200`
- `year_made ≥ 1950` AND `year_made ≤ 2026` ⚠️ (1950 = scope filter / `year_made < 1950` 의 데이터 오류 영역 X)
- `(year_made - artist_birth_year) ≥ 10` (데이터 오류 + 의심 영역 동시 제거)
- `work_age ≥ 0` AND `work_age ≤ 100`
- `artist_total_works > 0` (placeholder 제거)
- `gallery_city_count > 0` (placeholder 제거)

> **Boundary 통일** (audit script `scripts/audit_primary_market_data.py` 의 정확 정의):
> - T6 pass = `area_cm2 > 100 AND area_cm2 < 50,000` (strict 양쪽)
> - T6 fail = §2.2 Rule 4 (`area_cm2 ≤ 100`, n=52) ∪ Rule 5 (`area_cm2 ≥ 50,000`, n=135) — boundary `≤`/`≥` 정확 동일
> - 즉, `area_cm2 == 100` 또는 `area_cm2 == 50,000` 인 row = T6 미충족 영역
> - 같은 원리 가 price (`>100,000 AND <1,000,000,000`) / aspect (`>0 AND ≤10`) / ho (`>0 AND ≤200`) 에도 적용 — 각 boundary 의 `≤`/`≥` 처리 = §2.2 의 fail rule 과 정확 동일

### 3.3 T4 → T6 rule 별 drop count (정량 분해)

T4 base = 4,628 rows / T6 = 4,460 / drop = 168.

| Rule (T6 boundary 와 정확 동일) | Single fail (해당 rule 만 fail) | Total fail (다른 rule fail 도 포함) |
|---|---|---|
| `ho > 0` AND `ho ≤ 200` | 38 | 87 |
| `gallery_city_count > 0` | 60 | 61 |
| `area_cm2 > 100` AND `area_cm2 < 50,000` | 10 | 59 |
| `year_made ≥ 1950` AND `year_made ≤ 2026` | 0 | 6 |
| `work_age ≥ 0` AND `work_age ≤ 100` | 0 | 6 |
| `(year_made - artist_birth_year) ≥ 10` | 2 | 4 |
| `aspect_ratio > 0` AND `aspect_ratio ≤ 10` | 2 | 3 |
| `price_krw > 100,000` AND `price_krw < 1,000,000,000` | 1 | 1 |
| `artist_total_works > 0` | 0 | 0 |

> **Drop rows (n=168) 의 fail rule 수 평균 = 1.35** (대부분 single rule fail / overlap 일부).

### 3.4 Tier 별 라벨 (중립)

| Tier | 라벨 | 정의 |
|---|---|---|
| T0 | 운영 채택 | 28,376 rows / 운영 production 영역 |
| T1 | Artsy source 통일 | 7,289 rows |
| T2 | + year_made notna | 7,231 rows |
| T3 | + year + birth notna | 5,845 rows |
| T4 | + career + work_age notna | 4,628 rows |
| T5 | KRW only | 868 rows |
| T6 | T4 + 본 audit rule-filter | 4,460 rows |

## 4. 운영 cell breakdown 과 의 정량 정합 (관측 사실 만)

### 4.1 운영 cold cell breakdown (B-2 reproduction PR #49 정합)

operational `_source_calibration.json` 의 cold cell 별 baseline MdAPE:

| Cell | n | Baseline MdAPE |
|---|---|---|
| artsy_gallery (= KRW 868 rows = T5) | 868 | 24.34% |
| artsy_online | 6,421 | 35.04% |
| saatchi_online | 21,087 | 41.70% |

> **본 절 의 본질**: 위 cell 별 MdAPE 차이 = 관측 사실 만. cell 간 차이 의 원인 = 메타데이터 quality / source / KRW 여부 / gallery vs online / 모집단 구성 등 **다중 동시 변동** — 본 audit 만 으로 인과 결정 X (별도 인과 cycle 의무).

### 4.2 Cycle 1 의 관계 (관측 사실 만)

Cycle 1 의 Track 2 Stage 3 운영 채택 baseline 24.07% 는 **curated dataset (Artsy 8,495 row)** 기준. 본 audit 의 T5 (KRW 868) 의 artsy_gallery cell baseline 24.34% 는 **다른 모집단 / 다른 split / 다른 모델 family** 의 결과 — 정량 영역 의 단순 동시 관측 만 / equivalence 해석 X / 직접 비교 X.

## 5. Decision binding 적용

> 본 cycle = 데이터 의 정량 관측 만 / 운영 채택 / cleansed dataset 선택 / Cycle 1 verdict 변경 / 모델 성능 인과 추론 모두 영향 X

| 항목 | 본 audit 의 영향 |
|---|---|
| 운영 채택 결정 | ❌ 영향 X |
| Cycle 1 verdict (FAIL) | ❌ 변경 X |
| 트랙 1 / 트랙 2 efficacy | ❌ 갱신 X |
| Cleansed dataset 선택 | ❌ 본 audit 의 직접 결정 X (사용자 의사결정 영역) |
| 모델 성능 인과 추론 | ❌ 본 audit 영역 외 (별도 인과 cycle 의무) |
| 외부 보고서 | ❌ 본 결과 미반영 영역 |

**본 audit 의 가치 만**:
- ✅ 운영 28,376 rows 의 컬럼별 결측 / placeholder / anomaly 의 정량 관측 문서화
- ✅ Cleansed dataset 후보 의 정량 정의 (T0-T6) — 사용자 의사결정 가능한 형식
- ✅ Saatchi 21,087 rows 의 메타데이터 영역 의 정량 명시화

## 6. 사용자 의사결정 가능 영역

> ⚠️ **아래 = 보고서 의 권고 X**. 각 항목 = **사용자 가 후속 prereg + validation cycle 진입 시 의 선택지** 만 (decision-binding cycle 별도 의무).

1. **Cleansed dataset 선택**: T0 / T1 / T2 / T3 / T4 / T5 / T6 중 선택 → 별도 prereg cycle 의 입력
2. **Saatchi 영역 처리**: 운영 학습 의 21,087 rows 유지 vs 제외 → 별도 prereg cycle
3. **Anomaly filter 적용 여부**: T6 의 rule-filter 도입 vs 점진적 적용 → 별도 prereg cycle
4. **B-3 cycle 의 모집단 정의**: 본 audit 의 결과 가 B-3 의 split 의 모집단 정의 의 정량 입력 (별도 prereg)

## 7. 다음 단계 (조건부 / 사용자 결정 영역)

1. ✅ 본 audit 보고서 commit + PR
2. ⏳ 코덱스 audit 보고서 사후 검수
3. ⏳ (사용자 결정) Cleansed dataset 적용 cycle prereg (별도)
4. ⏳ (사용자 결정) B-3 cycle 의 모집단 정의 (본 audit 의 입력)

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 본 audit 보고서 round 1 사후 검수 (2026-05-08, NEEDS FIX) | P0×3 (§4.1/§4.2 over-claim, anomaly-free 표현 과대) / P1×5 (threshold 근거 결손, T6 분해 정량 부족, anomaly taxonomy 혼재, placeholder 분리 결손, trade-off 정량 부족) / P2×4 (area 기준 불일치, 시간 기준 정리, §6 disclaimer, 라벨 톤다운) |
| 본 audit 보고서 round 2 사후 검수 (2026-05-08, NEEDS FIX) | P2×2 (boundary 표기 불일치 — area/price 의 ≤/< 통일 / §1.2.1 "noise feature 영역" 표현 톤다운) — round 2 fix: §2.2 boundary `≤`/`≥` 명시 + §3.2/§3.3 boundary 의 explicit AND 표현 + §1.2.1 톤다운 |
| 본 audit 보고서 round 3 사후 검수 (2026-05-08, NEEDS FIX) | P2-1 잔존 (§3.2 의 boundary 통일 설명 예시 의 `<` 잔존) / 신규 issue 없음 — round 3 fix: §3.2 의 Boundary 통일 설명 의 area `≤`/`≥` explicit + price/aspect/ho 동일 원리 명시 |
| 본 audit 보고서 round 4 사후 검수 (예정) | round 3 fix commit 직후 |
