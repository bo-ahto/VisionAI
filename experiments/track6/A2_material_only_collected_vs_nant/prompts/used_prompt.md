# A2 실험 사용 프롬프트 기록

- 기록 성격: 실제 대화 지시를 바탕으로 정리한 실험 지시 기록
- 실험 ID: A2
- 실험 목적: 재료 정보만으로 가격 예측에 도움이 되는지 확인하고, 수집 재료 표현과 NANT 재료 표현 중 어느 쪽이 더 안정적인지 비교한다.

## 실제 지시 요약

- A2 실험으로 `재료만` 사용하는 실험을 진행한다.
- 재료 효과를 확인한다.
- 수집된 재료와 NANT 재료를 모두 실험한다.
- 실험 폴더를 따로 만든다.
- 사용 프롬프트를 실험 폴더에 같이 저장한다.
- 학습 데이터와 테스트 데이터 기준을 명확히 남긴다.
- 결과는 HTML과 CSV로 저장한다.

## 비교 조건

- 수집 재료 대분류:
  - `medium_category`
- 수집 재료 원문 묶음:
  - `collected_material_raw_bucket`
  - 원문 재료 값은 종류가 많으므로 학습 데이터 상위 80개 값만 유지하고 나머지는 `other_raw_material`로 묶는다.
- NANT 재료 번호:
  - `nant_material_idx`
- NANT 재료 도구명:
  - `nant_tool`
- NANT 재료 번호 + 도구명:
  - `nant_material_idx`
  - `nant_tool`

## 비교 모델

- Warm A: Huber
- Warm B: Linear Regression
- Warm C: Ridge
- Cold D: Huber
- Cold E: Quantile-LAD
- Cold F: LightGBM

## 데이터 사용 기준

- 학습 데이터:
  - `data/track6_split/features/warm/track6_train_warm_features.csv`
  - `data/track6_split/labels/track6_train_labels.csv`
- Warm 테스트 데이터:
  - `data/track6_split/features/warm/track6_test_warm_warm_features.csv`
  - `data/track6_split/labels/track6_test_warm_labels.csv`
- Cold 테스트 데이터:
  - `data/track6_split/features/cold/track6_test_cold_cold_features.csv`
  - `data/track6_split/labels/track6_test_cold_labels.csv`
- NANT 재료 정보는 Track6 split feature 파일에 포함된 컬럼을 사용한다.
- 정제 전체 데이터는 A2 실험 실행 중에 별도로 조인하지 않는다.
- feature 파일과 label 파일은 `_track6_row_id`로 연결한다.
- label은 학습 목표값과 평가 지표 계산에만 사용한다.
- label은 모델 입력 피처로 사용하지 않는다.
- 샘플링 없이 전체 split을 사용한다.

## 결과 지표

- R2
- MdAPE
- p95 APE
- Within-30
- Within-50
- MAPE
