# A8-1 호수 + 면적 조합 실험 지시 기록

- 기록 성격: 실제 대화 지시를 바탕으로 정리한 실험 지시 기록
- 실험 ID: A8-1
- 실험 목적: 호수와 면적을 함께 사용했을 때 단일 크기 표현보다 가격 예측력이 좋아지는지 확인한다.

## 실제 지시 요약

- A8의 세부 실험으로 진행한다.
- 호수 + 면적 조합을 추가로 검증한다.
- 기존 공통 실행기를 사용해 코드와 모델군은 고정한다.
- 변수 조합만 바꿔서 실험 통제를 유지한다.
- 학습/테스트 입력 파일과 라벨 파일은 분리해서 사용한다.
- 사용 데이터와 생성 데이터는 실험 폴더에 복사한다.
- 결과는 HTML, CSV, manifest, README로 남긴다.

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected_with_year_type_edition_size.csv`
- split 기준: `data/track6_split_with_year_type_edition_size`
- 학습 입력과 정답 가격은 분리해서 사용한다.
- 정답 가격은 `train_labels.csv`, `test_warm_labels.csv`, `test_cold_labels.csv`에만 둔다.
- 호수 파생 기준: `area_cm2`를 A1과 같은 F형 호수 면적표에 가장 가까운 값으로 매칭해 `estimated_ho`, `ln_estimated_ho`를 생성한다.

## 학습에 사용된 피처

- 비교 1: `estimated_ho`
- 비교 2: `ln_estimated_ho`
- 비교 3: `area_cm2`
- 비교 4: `log_area`
- 비교 5: `ln_estimated_ho + log_area`
- 비교 6: `estimated_ho + area_cm2`
- 비교 7: `ln_estimated_ho + width_cm + height_cm`
- 비교 8: `ln_estimated_ho + log_area + width_cm + height_cm`

## 테스트에 사용된 피처

- 학습 피처와 동일한 컬럼을 Warm/Cold 테스트에 사용한다.
- Warm과 Cold는 같은 피처 조합으로 평가하지만 결과는 합치지 않는다.

## 초기 실험 테스트: Warm

- Warm 정의: 학습 데이터에 같은 작가가 있는 작품을 예측하는 상황
- Warm 학습 데이터: `data/track6_split_with_year_type_edition_size/features/warm/track6_train_warm_features.csv` + `data/track6_split_with_year_type_edition_size/labels/track6_train_labels.csv`
- Warm 테스트 데이터: `data/track6_split_with_year_type_edition_size/features/warm/track6_test_warm_warm_features.csv` + `data/track6_split_with_year_type_edition_size/labels/track6_test_warm_labels.csv`
- 비교 방식: 단일 크기 표현과 크기 조합 표현의 성능을 비교한다.

## 초기 실험 테스트: Cold

- Cold 정의: 학습 데이터에 한 번도 등장하지 않은 작가의 작품을 예측하는 상황
- Cold 학습 데이터: `data/track6_split_with_year_type_edition_size/features/warm/track6_train_warm_features.csv` + `data/track6_split_with_year_type_edition_size/labels/track6_train_labels.csv`
- Cold 테스트 데이터: `data/track6_split_with_year_type_edition_size/features/cold/track6_test_cold_cold_features.csv` + `data/track6_split_with_year_type_edition_size/labels/track6_test_cold_labels.csv`
- 비교 방식: 작가명을 쓰지 않고 크기 표현만으로 신규 작가 작품의 가격대 설명력이 달라지는지 확인한다.

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

- `호수 + 면적` 조합의 median APE가 호수 단독 또는 면적 단독보다 낮으면 조합을 유지 후보로 본다.
- median APE 개선이 작더라도 p95 APE가 줄어들면 큰 오차 완화 후보로 본다.
- 개선이 거의 없으면 운영 입력과 설명이 쉬운 단일 크기 표현을 우선한다.
