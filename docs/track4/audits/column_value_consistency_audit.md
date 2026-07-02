# Track 4 컬럼별 값 정합성 감사

- 목적: cleaned_v2 전체 컬럼에서 값 타입, 범위, 파생값 계산, 필수값 누락 여부를 재점검
- 입력: `data/track4_primary_market_cleaned_v2.csv`
- 컬럼별 요약 CSV: `data/track4_column_value_consistency_audit.csv`
- 이슈 샘플 CSV: `data/track4_column_value_issue_samples.csv`
- 전체 rows: `54,842`
- 전체 columns: `97`
- 이슈가 있는 columns: `8`

## 1. 핵심 결론

- 학습 후보 rows: `34,219`
- 학습 후보 중 한글 작가명 누락: `0`
- 학습 후보 중 `medium_category=unknown`: `26`
- 학습 후보 중 `support_category=unknown`: `2,783`

## 2. 컬럼별 주요 이슈

| 컬럼 | 결측 rows | 고유값 수 | 이슈 rows | 이슈 내용 |
|---|---:|---:|---:|---|
| `price_krw` | `18,928` | `4,813` | `18,928` | missing_required=18928 |
| `height_cm` | `97` | `1,703` | `136` | above_max_1000=39;missing_required=97 |
| `width_cm` | `93` | `1,702` | `129` | above_max_1000=36;missing_required=93 |
| `area_cm2` | `97` | `8,370` | `33` | above_max_1e+06=33 |
| `medium_raw` | `28` | `5,319` | `28` | missing_required=28 |
| `depth_cm` | `24,324` | `418` | `15` | above_max_1000=15 |
| `aspect_ratio` | `97` | `6,186` | `2` | above_max_100=2 |
| `artist_name_ko` | `2` | `2,869` | `2` | missing_required=2 |

## 3. 파생값 계산 검증

| 검증 항목 | 이슈 rows | 기준 |
|---|---:|---|
| `ln_price_krw_mismatch` | `0` | abs(diff) > 1e-6 |
| `area_cm2_mismatch` | `0` | abs(diff) > 1e-6 |
| `log_area_mismatch` | `0` | abs(diff) > 1e-6 |
| `aspect_ratio_mismatch` | `0` | abs(diff) > 1e-6 |
| `has_depth_mismatch` | `0` | depth_cm > 0 기준 |
| `artist_works_log_mismatch` | `0` | abs(diff) > 1e-6 |
| `medium_support_bucket_mismatch` | `0` | medium_category__support_category 기준 |
| `training_candidate_reason_mismatch` | `0` | exclude reason 없음 = 학습 후보 |

## 4. 해석

- `support_category=unknown`은 대량으로 남아 있어 모델 피처로 쓸 경우 별도 실험 또는 보수적 처리 필요
- `gallery_audit_status`의 unmatched/missing은 갤러리 메타 참고용 이슈이며 현재 모델 피처에서는 제외
- `depth_cm` 결측은 2D 작품에서 자연스러운 결측일 수 있으므로 단순 오류로 보지 않고 `has_depth`로 관리
- 파생값 불일치가 0이면 클렌징 후 계산 컬럼은 재현 가능한 상태로 판단
