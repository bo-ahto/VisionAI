# C1 작가명 + 크기 실험 지시 기록

- 실험 목적:
  - 작가명을 이미 넣은 상태에서도 크기 정보가 작품 가격 예측을 개선하는지 확인한다.
  - “비싼 작가라서 비싼 것”을 먼저 반영한 뒤, “작품 크기 때문에 추가로 비싸지는지”를 확인한다.

- 실험군:
  - Group C: 작가명 + 작품 변수

- 기준선:
  - `artist_name_ko only`
  - B1과 같은 기준이다.

- 비교 피처:
  - `artist_name_ko + estimated_ho`
  - `artist_name_ko + ln_estimated_ho`
  - `artist_name_ko + log_area`
  - `artist_name_ko + width_cm + height_cm + log_area + aspect_ratio`

- 사용 데이터:
  - split root: `data/track6_split_with_year_type_edition_size_artist_name`
  - 학습 입력: `features/warm/track6_train_warm_features.csv`
  - 학습 정답: `labels/track6_train_labels.csv`
  - Warm 테스트 입력: `features/warm/track6_test_warm_warm_features.csv`
  - Warm 테스트 정답: `labels/track6_test_warm_labels.csv`
  - Cold 테스트 입력: `features/cold/track6_test_cold_cold_features.csv`
  - Cold 테스트 정답: `labels/track6_test_cold_labels.csv`

- 숫자형 처리:
  - `estimated_ho`, `ln_estimated_ho`, `log_area`, `width_cm`, `height_cm`, `aspect_ratio`는 숫자형으로 처리한다.
  - 숫자형은 중앙값 결측 보정 후 `StandardScaler`를 적용한다.
  - 문자열로 바꿔 one-hot 처리하지 않는다.

- 범주형 처리:
  - `artist_name_ko`는 범주형으로 처리한다.
  - 범주형은 `OneHotEncoder(handle_unknown="ignore")`를 사용한다.

- 모델:
  - Warm A: Huber
  - Warm B: Linear Regression
  - Warm C: Ridge
  - Cold D: Huber
  - Cold E: Quantile-LAD
  - Cold F: LightGBM

- 라벨 사용:
  - 정답 가격은 학습 target과 평가 지표 계산에만 사용한다.
  - 정답 가격은 모델 입력 피처에 넣지 않는다.
  - feature 파일과 label 파일은 `_track6_row_id`로만 연결한다.

- 평가 지표:
  - R2
  - RMSE(log)
  - MdAPE
  - p95 APE
  - Within-30
  - Within-50
  - MAPE

- 판단 기준:
  - Warm에서 `artist_name_ko only`보다 MdAPE가 낮아지면 크기 정보의 추가 설명력이 있다고 본다.
  - RMSE(log)가 낮아지면 로그 가격 기준 예측 안정성이 좋아졌다고 본다.
  - p95 APE가 커지면 큰 오차 위험이 커진 것으로 보고 보류한다.
  - Cold는 신규 작가명 상황이라 참고값으로만 본다.
