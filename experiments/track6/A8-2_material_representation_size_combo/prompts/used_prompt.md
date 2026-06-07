# A8-2 재료 표현 방식 + 크기 조합 실험 지시 기록

- 기록 성격: 실제 대화 지시를 바탕으로 정리한 실험 지시 기록
- 실험 ID: A8-2
- 실험 목적: 크기 기준을 고정한 상태에서 재료 표현 방식별 가격 예측 성능 차이를 확인한다.

## 실제 지시 요약

- A8의 세부 실험으로 진행한다.
- NANT 재료끼리만 비교하지 않고 NANT 적용 전 수집 재료 표현도 함께 비교한다.
- A8에서 이미 실행한 `log_area + medium_category`, `log_area + nant_material_idx`는 기준 비교군으로 포함한다.
- A8에서 빠졌던 `log_area + nant_tool`, `log_area + nant_material_idx + nant_tool`, `collected_material_raw_bucket` 조합을 보강한다.
- A8-1에서 좋았던 Warm/Cold 크기 조합도 참고해 재료 표현 효과를 확인한다.
- 공통 실행기를 사용해 코드와 모델군은 고정한다.
- 변수 조합만 바꿔서 실험 통제를 유지한다.

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected_with_year_type_edition_size.csv`
- split 기준: `data/track6_split_with_year_type_edition_size`
- 학습 입력과 정답 가격은 분리해서 사용한다.
- 정답 가격은 `train_labels.csv`, `test_warm_labels.csv`, `test_cold_labels.csv`에만 둔다.
- `collected_material_raw_bucket`은 학습 데이터 기준 상위 80개 원문 재료를 유지하고 나머지는 `other_raw_material`로 묶는다.

## 학습에 사용된 피처

- 공통 크기 기준:
  - `log_area + medium_category`
  - `log_area + collected_material_raw_bucket`
  - `log_area + nant_material_idx`
  - `log_area + nant_tool`
  - `log_area + nant_material_idx + nant_tool`
- A8-1 Warm 크기 조합 기준:
  - `ln_estimated_ho + log_area + width_cm + height_cm + medium_category`
  - `ln_estimated_ho + log_area + width_cm + height_cm + collected_material_raw_bucket`
  - `ln_estimated_ho + log_area + width_cm + height_cm + nant_material_idx`
  - `ln_estimated_ho + log_area + width_cm + height_cm + nant_tool`
  - `ln_estimated_ho + log_area + width_cm + height_cm + nant_material_idx + nant_tool`
- A8-1 Cold 크기 조합 기준:
  - `ln_estimated_ho + log_area + medium_category`
  - `ln_estimated_ho + log_area + collected_material_raw_bucket`
  - `ln_estimated_ho + log_area + nant_material_idx`
  - `ln_estimated_ho + log_area + nant_tool`
  - `ln_estimated_ho + log_area + nant_material_idx + nant_tool`

## 테스트에 사용된 피처

- 학습 피처와 동일한 컬럼을 Warm/Cold 테스트에 사용한다.
- Warm과 Cold는 같은 피처 조합으로 평가하지만 결과는 합치지 않는다.

## 초기 실험 테스트: Warm

- Warm 정의: 학습 데이터에 같은 작가가 있는 작품을 예측하는 상황
- Warm 학습 데이터: `data/track6_split_with_year_type_edition_size/features/warm/track6_train_warm_features.csv` + `data/track6_split_with_year_type_edition_size/labels/track6_train_labels.csv`
- Warm 테스트 데이터: `data/track6_split_with_year_type_edition_size/features/warm/track6_test_warm_warm_features.csv` + `data/track6_split_with_year_type_edition_size/labels/track6_test_warm_labels.csv`
- 비교 방식: 같은 크기 기준 안에서 재료 표현만 바꿔 성능 차이를 확인한다.

## 초기 실험 테스트: Cold

- Cold 정의: 학습 데이터에 한 번도 등장하지 않은 작가의 작품을 예측하는 상황
- Cold 학습 데이터: `data/track6_split_with_year_type_edition_size/features/warm/track6_train_warm_features.csv` + `data/track6_split_with_year_type_edition_size/labels/track6_train_labels.csv`
- Cold 테스트 데이터: `data/track6_split_with_year_type_edition_size/features/cold/track6_test_cold_cold_features.csv` + `data/track6_split_with_year_type_edition_size/labels/track6_test_cold_labels.csv`
- 비교 방식: 작가명을 쓰지 않고 크기와 재료 표현만으로 신규 작가 작품의 가격대 설명력이 달라지는지 확인한다.

## 모델군

- Warm:
  - Huber
  - Linear Regression
  - Ridge
- Cold:
  - Huber
  - Quantile-LAD
  - LightGBM

## 평가 지표

- R2
- median APE
- p95 APE
- Within-30
- Within-50

## 판단 기준

- 같은 크기 기준 안에서 `medium_category`, `collected_material_raw_bucket`, `nant_material_idx`, `nant_tool`, `nant_material_idx + nant_tool`을 비교한다.
- `nant_material_idx + nant_tool`이 가장 좋으면 NANT 번호와 도구명을 모두 유지 후보로 둔다.
- `nant_tool` 단독이 좋으면 사람이 읽기 쉬운 도구명 중심 표현을 후보로 둔다.
- 수집 재료 표현이 가장 좋으면 NANT 변환 전 재료 정보도 보존 후보로 둔다.
- 개선폭이 작으면 더 단순하고 운영에서 설명하기 쉬운 재료 표현을 우선한다.
