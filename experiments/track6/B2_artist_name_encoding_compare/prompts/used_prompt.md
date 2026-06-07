# B2 작가명 처리 방식 비교 실험 지시 기록

- 실험 목적:
  - `artist_name_ko`를 모델에 넣는 방식에 따라 성능이 달라지는지 확인한다.
  - B1의 one-hot 방식을 기준으로 두고 다른 encoding 방식이 더 안정적인지 비교한다.

- 실험군:
  - Group B: 작가 변수만

- 비교할 encoding 방식:
  - `one_hot`
    - 작가명을 범주형 값으로 그대로 넣고 one-hot encoding한다.
    - B1과 동일한 기준이다.
  - `frequency_log`
    - 학습 데이터 안에서 해당 작가가 몇 번 등장했는지를 로그값으로 바꾼다.
    - 가격 라벨을 쓰지 않는 안전한 방식이다.
  - `target_mean_log`
    - 학습 데이터 안에서 작가별 평균 로그가격을 계산해 숫자로 넣는다.
    - 평가 데이터의 가격은 절대 사용하지 않는다.
  - `smoothed_target_mean_log`
    - 작가별 평균 로그가격을 쓰되, 작품 수가 적은 작가는 전체 평균 쪽으로 보정한다.
    - 계산식: `(작가별 로그가격 합계 + 전체 평균 로그가격 * 10) / (작가별 작품 수 + 10)`

- 사용 데이터:
  - split root: `data/track6_split_with_year_type_edition_size_artist_name`
  - 학습 입력: `features/warm/track6_train_warm_features.csv`
  - 학습 정답: `labels/track6_train_labels.csv`
  - Warm 테스트 입력: `features/warm/track6_test_warm_warm_features.csv`
  - Warm 테스트 정답: `labels/track6_test_warm_labels.csv`
  - Cold 테스트 입력: `features/cold/track6_test_cold_cold_features.csv`
  - Cold 테스트 정답: `labels/track6_test_cold_labels.csv`

- 라벨 사용 원칙:
  - 학습 label은 모델 학습 target으로 사용한다.
  - target encoding 계산에는 학습 label만 사용한다.
  - Warm/Cold test label은 평가 지표 계산에만 사용한다.
  - feature와 label은 `_track6_row_id` 기준으로 연결한다.

- 모델:
  - Warm A: Huber
  - Warm B: Linear Regression
  - Warm C: Ridge
  - Cold D: Huber
  - Cold E: Quantile-LAD
  - Cold F: LightGBM

- 평가 지표:
  - R2
  - RMSE(log)
  - MdAPE
  - p95 APE
  - Within-30
  - Within-50
  - MAPE

- 판단 기준:
  - Warm에서 B1 one-hot보다 낮은 MdAPE 또는 RMSE(log)가 나오면 개선 후보로 본다.
  - p95 APE가 커지면 대표 오차가 좋아도 큰 오차 위험이 커진 것으로 본다.
  - Cold 결과는 신규 작가명 상황의 한계 확인용으로만 본다.
