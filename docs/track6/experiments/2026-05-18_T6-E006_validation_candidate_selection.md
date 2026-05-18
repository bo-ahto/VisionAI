# T6-E006 validation 기준 후보 선정

- 날짜: `2026-05-18`
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
| Warm | `catboost_warm_artist` | `base_medium_size` | `0.2665` | `1.1814` | Warm median APE 최저 |
| Cold 대표 오차 | `hist_quantile_cold` | `base` | `0.3782` | `1.9444` | Cold median APE 최저 |
| Cold 큰 오차 위험 | `huber_cold` | `base_size_shape` | `0.3888` | `1.3835` | Cold p95 APE 최저 |

## 3. 해석

- Warm은 작가 식별값을 포함한 CatBoost가 유지 후보
- Warm 피처는 `medium_category + size_bucket` 조합을 포함할 때 median APE가 가장 낮음
- Cold는 대표값 기준으로 단순한 구조 피처가 가장 안정적
- Cold의 큰 오차를 줄이는 목적이면 Huber + `size_bucket/shape_bucket` 후보가 더 적합

## 4. 다음 단계

- T6-E007에서 위 후보만 test 데이터에 적용
- test 결과가 validation과 같은 방향인지 확인
- test에서 급락하면 해당 후보는 최종 운영 후보에서 제외하거나 보류
