# Track 4 cleaned_v2 생성 보고서

- 목적: 가격/크기/작가/재료/중복/출처/갤러리 감사 결과를 반영한 학습 후보 데이터 생성
- cleaned 파일: `data/track4_primary_market_cleaned_v2.csv`
- feature 후보 파일: `data/track4_primary_market_feature_candidates_v1.csv`
- 전체 rows: `54,842`
- 학습 후보 rows: `34,239`
- 제외 rows: `20,603`

## 1. 출처별 row 수

| 출처 | 전체 | 학습 후보 |
|---|---:|---:|
| artsy | `30,046` | `10,739` |
| saatchi | `21,721` | `20,530` |
| artue | `2,783` | `2,683` |
| gallery_primary | `292` | `287` |

## 2. 제외 사유

| 사유 | rows |
|---|---:|
| `missing_price_krw` | `18,928` |
| `duplicate_non_representative` | `1,953` |
| `missing_core_size` | `97` |
| `price_under_10000` | `55` |
| `area_over_1m_cm2` | `33` |
| `area_under_10cm2` | `31` |
| `missing_medium_raw` | `28` |
| `price_over_1b` | `10` |
| `artist_audit_issue` | `2` |

## 3. 모델 피처 제외 원칙

- source 계열 컬럼은 feature 후보 파일에서 제외함
- gallery_name / gallery_tier는 기본 feature 후보에서 제외함
- source와 gallery 정보는 원본 추적과 품질 감사 용도로만 사용함

## 4. 다음 단계

- `track4_primary_market_feature_candidates_v1.csv` 기준으로 Warm/Cold split 생성
- split 생성 시 `artist_key` 기준으로 Cold 작가를 분리
- 모델 실험 전 feature 후보 컬럼 결측률을 다시 점검
