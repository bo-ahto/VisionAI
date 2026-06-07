# T6-E006 validation 기준 후보 선정

- 날짜: `2026-05-29`
- 관련 가설: `T6-H6`
- 상태: 부분 검증
- 목적: validation 결과만 보고 test에 올릴 Warm/Cold 후보를 고정
- 사용 스크립트: `scripts/track6/run_t6_e006_select_validation_candidates.py`
- 결과 JSON: `data/track6/results/t6_e006_validation_candidate_selection.json`

## 1. 후보 선정 원칙

- test 결과를 보기 전에 validation 결과만 사용해 후보를 고정
- Warm과 Cold는 같은 후보로 묶지 않고 분리 선정
- Cold는 대표 오차 후보와 큰 오차 위험 후보를 분리
- 운영에서 만들 수 없는 피처는 후보에서 제외

## 2. 선정 후보

| 구분 | 모델 | 피처셋 | validation median APE | validation p95 APE | 선정 이유 |
|---|---|---|---:|---:|---|
| Warm | `huber_warm_artist` | `base_existing_combo` | `0.2126` | `1.3194` | Warm median APE 최저 |
| Cold CatBoost | `catboost_cold` | `base_medium_shape` | `0.4251` | `2.4420` | CatBoost 내 median APE 최저 |
| Cold LightGBM | `lightgbm_cold` | `base_support_size` | `0.3848` | `2.0207` | LightGBM 내 median APE 최저 |
| Cold 대표 오차 | `lightgbm_cold` | `base_support_size` | `0.3848` | `2.0207` | Cold median APE 최저 |
| Cold 큰 오차 위험 | `lightgbm_cold` | `base_large_flags` | `0.3938` | `1.9783` | Cold p95 APE 최저 |

## 3. 해석

- Warm은 작가 식별값을 포함한 Huber가 유지 후보
- Warm 피처는 validation 기준으로 가장 안정적인 조합을 고정
- Cold는 CatBoost와 LightGBM 중 대표 오차 기준 후보를 고정
- Cold의 큰 오차를 줄이는 목적이면 p95 APE 기준 후보를 별도로 고정

## 4. 다음 단계

- T6-E007에서 위 후보만 test 데이터에 적용
- test 결과가 validation과 같은 방향인지 확인
- test에서 급락하면 해당 후보는 최종 운영 후보에서 제외하거나 보류
