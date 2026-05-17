# T4-E049 Warm RandomForest artifact dry-run

- 날짜: 2026-05-17
- 관련 가설: T4-H38
- 상태: 완료
- 목적: T4-E047에서 확인된 Warm RandomForest 후보를 실제 artifact로 생성하고 성능을 재확인

## 1. 확인하려는 것

- RandomForest Warm 후보를 운영 artifact 형태로 저장할 수 있는가
- 기존 Ridge artifact보다 test 성능이 유지 또는 개선되는가
- Warm 가격 범위 정책을 다시 계산했을 때 사용할 수 있는 수준인가

## 2. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- calibration 데이터: `data/track4_split/track4_val_warm.csv`
- 테스트 데이터: `data/track4_split/track4_test_warm.csv`

## 3. 사용 피처

- `artist_key`
- `medium_category`
- `support_category`
- `artist_works_log`
- `artist_works_count_train`
- `artist_train_median_log_price`
- `artist_train_mean_log_price`
- `artist_train_iqr_log_price`
- `log_area`
- `aspect_ratio`

## 4. 실행 방법

- 실행 명령:
  - `python3 scripts/track4/run_t4_e049_warm_random_forest_artifact_dry_run.py`

## 5. 결과

| 후보 | test median APE | test p95 APE | Within-30% | Within-50% |
|---|---:|---:|---:|---:|
| 기존 Ridge artifact | 0.2201 | 1.1118 | 0.6131 | 0.8321 |
| RandomForest artifact | 0.1970 | 0.9219 | 0.6715 | 0.8613 |

## 6. 가격 범위 재계산

| 범위 기준 | validation 기준 log 폭 | 가격 범위 폭 | test coverage |
|---|---:|---:|---:|
| q80 | 0.5599 | x3.06 | 0.8832 |
| q90 | 0.8066 | x5.02 | 0.9416 |

- q80 기준도 test coverage가 `0.8832`로 높게 나왔다.
- RandomForest로 바꾸면 Warm 가격 범위 정책도 기존보다 안정적으로 볼 수 있다.

## 7. 결론

- Warm 최종 artifact는 Ridge에서 RandomForest로 교체하는 것이 현재 결과 기준으로 타당하다.
- RandomForest는 median APE와 p95 APE 모두 개선했다.
- Warm 가격 범위도 validation 기준으로 계산했을 때 test coverage가 충분히 나왔다.

## 8. 산출물

- 실행 스크립트: `scripts/track4/run_t4_e049_warm_random_forest_artifact_dry_run.py`
- 결과 JSON: `data/track4/results/t4_e049_warm_random_forest_artifact_dry_run.json`
- 모델 artifact: `data/track4/models/track4_warm_final_conditional_stats_random_forest.joblib`
