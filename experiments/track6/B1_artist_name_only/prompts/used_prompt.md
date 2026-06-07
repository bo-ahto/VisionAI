# B1 작가명 단독 실험 지시 기록

- 실험 목적:
  - 작가명 한글 변수만으로 작품 가격대가 어느 정도 설명되는지 확인한다.
  - 작품 변수 없이 작가명 자체의 영향만 따로 본다.

- 실험군:
  - Group B: 작가 변수만

- 사용 데이터:
  - 기준 원천 split: `data/track6_split_with_year_type_edition_size`
  - 보강 split: `data/track6_split_with_year_type_edition_size_artist_name`
  - 보강 방식: `track6_train.csv`, `track6_test_warm.csv`, `track6_test_cold.csv`의 `artist_name_ko`를 `_track6_row_id` 기준으로 feature split에 추가

- 학습 데이터:
  - 입력값: `data/track6_split_with_year_type_edition_size_artist_name/features/warm/track6_train_warm_features.csv`
  - 정답값: `data/track6_split_with_year_type_edition_size_artist_name/labels/track6_train_labels.csv`
  - 연결 키: `_track6_row_id`
  - 학습 피처: `artist_name_ko`

- Warm 테스트 데이터:
  - 입력값: `data/track6_split_with_year_type_edition_size_artist_name/features/warm/track6_test_warm_warm_features.csv`
  - 정답값: `data/track6_split_with_year_type_edition_size_artist_name/labels/track6_test_warm_labels.csv`
  - 테스트 피처: `artist_name_ko`
  - 의미: 학습 데이터에 같은 작가가 있는 경우 작가명만으로 가격대가 설명되는지 확인

- Cold 테스트 데이터:
  - 입력값: `data/track6_split_with_year_type_edition_size_artist_name/features/cold/track6_test_cold_cold_features.csv`
  - 정답값: `data/track6_split_with_year_type_edition_size_artist_name/labels/track6_test_cold_labels.csv`
  - 테스트 피처: `artist_name_ko`
  - 의미: 신규 작가명은 학습에 없으므로 최종 Cold 모델 판단이 아니라 작가명 only 모델의 한계를 확인하는 참고값

- 모델:
  - Warm A: Huber
  - Warm B: Linear Regression
  - Warm C: Ridge
  - Cold D: Huber
  - Cold E: Quantile-LAD
  - Cold F: LightGBM

- 전처리:
  - `artist_name_ko`는 범주형 피처로 처리한다.
  - 범주형 피처는 `OneHotEncoder(handle_unknown="ignore")`를 사용한다.
  - Cold의 처음 보는 작가명은 학습에 없는 카테고리로 처리된다.

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
  - Warm에서 MdAPE와 RMSE(log)가 낮으면 작가명 자체의 가격 설명력이 있다고 본다.
  - Cold 결과는 신규 작가명 상황에서 작가명 only 모델을 사용할 수 있는지에 대한 참고값으로만 본다.
