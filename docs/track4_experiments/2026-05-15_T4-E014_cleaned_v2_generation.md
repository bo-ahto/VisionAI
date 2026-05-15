# T4-E014 cleaned_v2 생성

- 날짜: 2026-05-15
- 연결 가설: T4-C1~T4-C7
- 상태: 완료
- 목적: 가격/크기/작가/재료/중복/출처/갤러리 감사 결과를 반영해 Track 4 학습 후보 데이터를 생성

## 1. 실행 방법

- 스크립트: `scripts/track4/build_primary_market_cleaned_v2.py`
- 입력:
  - `data/track4_price_consistency_audit.csv`
  - `data/track4_size_consistency_audit.csv`
  - `data/track4_artist_consistency_audit.csv`
  - `data/track4_medium_support_consistency_audit.csv`
  - `data/track4_duplicate_consistency_audit.csv`
  - `data/track4_gallery_metadata_audit.csv`
- 출력:
  - `data/track4_primary_market_cleaned_v2.csv`
  - `data/track4_primary_market_feature_candidates_v1.csv`
  - `data/track4_primary_market_cleaned_v2_summary.json`
  - `docs/track4_primary_market_cleaned_v2_report.md`

## 2. 주요 결과

- 전체 rows: `54,842`
- 학습 후보 rows: `34,239`
- 제외 rows: `20,603`

## 3. 출처별 학습 후보

| 출처 | 전체 | 학습 후보 |
|---|---:|---:|
| Artsy | `30,046` | `10,739` |
| Saatchi | `21,721` | `20,530` |
| Artue | `2,783` | `2,683` |
| Gallery primary | `292` | `287` |

## 4. 제외 사유

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

## 5. feature 후보 원칙

- source 계열 컬럼은 feature 후보 파일에서 제외
- gallery_name / gallery_tier는 기본 feature 후보에서 제외
- source와 gallery 정보는 원본 추적과 품질 감사 용도로만 유지
- feature 후보 파일에는 운영 재현 가능성이 높은 작품/작가 key 기반 컬럼만 우선 포함

## 6. 결론

- 채택: `cleaned_v2`를 Track 4 split 생성 전 기준 데이터로 사용
- 채택: `feature_candidates_v1`을 모델 피처 검토용 입력으로 사용
- 보류: 갤러리/티어는 후속 별도 가설에서만 실험
- 보류: source는 모델 피처에서 계속 제외

## 7. 다음 작업

- Warm/Cold를 분리한 Track 4 split 생성
- split 전 feature 후보 컬럼 결측률 점검
- split 생성 후 모델 baseline 실험 진행
