# Track 4 cleaned_v2 생성 보고서

- 목적: 가격/크기/작가/재료/중복/출처/갤러리 감사 결과를 반영한 학습 후보 데이터 생성
- cleaned 파일: `data/track4_primary_market_cleaned_v2.csv`
- feature 후보 파일: `data/track4_primary_market_feature_candidates_v1.csv`
- 전체 rows: `54,842`
- 학습 후보 rows: `34,219`
- 제외 rows: `20,623`
- 한글 작가명 rows: `54,840`
- 동명이인 분리 작가 수: `32`
- 동명이인 분리 작품 rows: `1,926`

## 1. 출처별 row 수

| 출처 | 전체 | 학습 후보 |
|---|---:|---:|
| artsy | `30,046` | `10,722` |
| saatchi | `21,721` | `20,531` |
| artue | `2,783` | `2,680` |
| gallery_primary | `292` | `286` |

## 2. 제외 사유

| 사유 | rows |
|---|---:|
| `missing_price_krw` | `18,928` |
| `duplicate_non_representative` | `1,956` |
| `missing_core_size` | `97` |
| `price_under_10000` | `55` |
| `width_or_height_over_1000cm` | `54` |
| `extreme_aspect_ratio` | `52` |
| `area_over_1m_cm2` | `33` |
| `area_under_10cm2` | `31` |
| `missing_medium_raw` | `28` |
| `price_over_1b` | `10` |
| `artist_audit_issue` | `2` |

## 3. 모델 피처 제외 원칙

- source 계열 컬럼은 추적용으로만 남기고 모델 입력에서는 제외함
- gallery_name / gallery_tier는 기본 feature 후보에서 제외함
- source와 gallery 정보는 원본 추적과 품질 감사 용도로만 사용함

## 4. 동명이인 처리

- Track 3 방식과 동일하게 같은 한글명 안에서 여러 작가 key가 있는 경우를 점검함
- 보조 작가 key가 3건 이상이고, key별 가격 중앙값 차이가 큰 경우만 동명이인으로 봄
- 동명이인은 `artist_name_ko` 뒤에 `_A`, `_B`, `_C` suffix를 붙여 분리함
- 원래 한글명은 `artist_name_ko_orig`에 보존함
- 동명이인 여부는 `is_homonym`으로 표시함
- Track 4 split은 이미 `artist_key` 기준으로 나누고 있어, 이번 처리는 이름 표시와 후속 피처 계산의 혼선을 막는 목적임

## 5. 다음 단계

- `track4_primary_market_feature_candidates_v1.csv` 기준으로 Warm/Cold split 생성
- split 생성 시 `artist_key` 기준으로 Cold 작가를 분리
- 모델 실험 전 feature 후보 컬럼 결측률을 다시 점검
