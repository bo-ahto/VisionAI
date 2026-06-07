# A10 작품 기본 피처 묶음 + 제작연도 실험

## 실험 목적

- 작품 기본 피처 묶음에 제작연도 계열 변수를 추가했을 때 가격 예측 성능이 개선되는지 확인한다.
- 작가명은 사용하지 않고 작품 자체 정보만 사용한다.
- 운영에서 입력 가능한 제작연도 정보만 사용한다.
- Warm / Cold split에서 제작연도 계열 변수의 일반화 성능 차이를 확인한다.

## 기준 피처

- `ln_estimated_ho`
- `nant_material_idx`
- `nant_tool`
- `nant_support`

## 추가 실험 변수

- `artwork_year`
  - 작품 제작연도 원값
  - 연속형 숫자 변수로 처리한다.
- `artwork_age`
  - 2026년 기준 작품이 만들어진 후 경과한 연수
  - 계산식: `artwork_age = 2026 - artwork_year`
  - 연속형 숫자 변수로 처리한다.

## 비교 조합

- 작품 기본 피처 묶음
- 작품 기본 피처 묶음 + `artwork_year`
- 작품 기본 피처 묶음 + `artwork_age`
- 작품 기본 피처 묶음 + `artwork_year` + `artwork_age`

## 중요 구현 조건

- `artwork_year`와 `artwork_age`는 문자열이나 범주형으로 처리하지 않는다.
- 숫자형 피처는 중앙값 결측 보정 후 `StandardScaler`를 적용한다.
- `nant_material_idx`, `nant_tool`, `nant_support`는 범주형으로 처리한다.
- `artwork_year_source`, `artwork_year_match_method`, `artwork_year_missing`은 모델 입력에서 제외한다.
- label은 학습 target과 평가 지표 계산에만 사용한다.
- feature 파일과 label 파일은 `_track6_row_id`로 연결한다.
- sampling 없이 전체 split을 사용한다.
- 실험 코드는 `scripts/track6/fixed_variable_experiment_runner.py`를 사용하고, 실험별 차이는 설정 파일로만 관리한다.

## 데이터 정책

- 학습 데이터: `data/track6_split_with_year_type_edition_size/features/warm/track6_train_warm_features.csv`
- 학습 라벨: `data/track6_split_with_year_type_edition_size/labels/track6_train_labels.csv`
- Warm 테스트 데이터: `data/track6_split_with_year_type_edition_size/features/warm/track6_test_warm_warm_features.csv`
- Warm 테스트 라벨: `data/track6_split_with_year_type_edition_size/labels/track6_test_warm_labels.csv`
- Cold 테스트 데이터: `data/track6_split_with_year_type_edition_size/features/cold/track6_test_cold_cold_features.csv`
- Cold 테스트 라벨: `data/track6_split_with_year_type_edition_size/labels/track6_test_cold_labels.csv`

## 모델 구성

- Warm A: Huber
- Warm B: Linear Regression
- Warm C: Ridge
- Cold D: Huber
- Cold E: Quantile-LAD
- Cold F: LightGBM

## 평가지표

- R2
- MdAPE
- p95 APE
- Within-30
- Within-50
- MAPE

## 판단 기준

- 기준 피처 묶음 대비 MdAPE가 낮아지면 제작연도 계열 변수가 도움이 된 것으로 본다.
- p95 APE가 낮아지면 큰 오차 감소에도 도움이 된 것으로 본다.
- Warm에서만 개선되면 Warm 전용 후보로 둔다.
- Cold에서만 개선되면 Cold 전용 후보로 둔다.
- Warm/Cold 모두 악화되면 A10 제작연도 계열 변수는 보류한다.

## 재현성 확인

- 같은 설정으로 1차 실행 후 결과를 baseline으로 저장한다.
- 같은 설정으로 2차 실행 후 결과를 rerun으로 저장한다.
- `metrics_long.csv` 기준으로 두 결과가 같은지 비교한다.
