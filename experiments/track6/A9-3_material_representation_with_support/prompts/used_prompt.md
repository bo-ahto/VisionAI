# Track6 A9-3 실험 지시 기록

## 실험 제목

- Track6 A9-3 재료 표현별 지지체 추가 실험 결과

## 실험 목적

- 재료 표현 방식이 달라질 때 지지체 추가 효과가 어떻게 달라지는지 확인한다.
- A9 대표 실험을 세부 실험으로 나누어 어떤 조건에서 지지체/재료/크기 조합이 실제로 도움이 되는지 확인한다.

## 사용 데이터

- 기준 split: `data/track6_split_with_year_type_edition_size`
- 학습 입력: `data/track6_split_with_year_type_edition_size/features/warm/track6_train_warm_features.csv`
- 학습 정답: `data/track6_split_with_year_type_edition_size/labels/track6_train_labels.csv`
- Warm 테스트 입력: `data/track6_split_with_year_type_edition_size/features/warm/track6_test_warm_warm_features.csv`
- Warm 테스트 정답: `data/track6_split_with_year_type_edition_size/labels/track6_test_warm_labels.csv`
- Cold 테스트 입력: `data/track6_split_with_year_type_edition_size/features/cold/track6_test_cold_cold_features.csv`
- Cold 테스트 정답: `data/track6_split_with_year_type_edition_size/labels/track6_test_cold_labels.csv`

## 라벨 사용 기준

- 가격 라벨은 학습 target과 평가 지표 계산에만 사용한다.
- 입력 피처와 정답 가격은 `_track6_row_id`로만 연결한다.
- 가격 라벨은 모델 입력 피처에 포함하지 않는다.

## 공통 실행 기준

- 공통 실행 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 실험별 차이는 `experiment_config.json`의 변수 조합만 바꾼다.
- 숫자형 피처는 중앙값 결측 보정 후 `StandardScaler`를 적용한다.
- 범주형 피처는 문자열화 후 결측을 `__missing__`으로 두고 one-hot encoding한다.

## 모델군

- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 실험 변수 조합

- 로그면적 + 수집 재료 대분류 + NANT 지지체: `log_area, medium_category, nant_support`
- 로그면적 + 수집 원문 재료 묶음 + NANT 지지체: `log_area, collected_material_raw_bucket, nant_support`
- 로그면적 + NANT 재료 번호 + NANT 지지체: `log_area, nant_material_idx, nant_support`
- 로그면적 + NANT 도구명 + NANT 지지체: `log_area, nant_tool, nant_support`
- 로그면적 + NANT 재료 번호 + 도구명 + NANT 지지체: `log_area, nant_material_idx, nant_tool, nant_support`

## 평가 지표

- R2
- MdAPE
- p95 APE
- Within-30
- Within-50
- MAPE

## 판단 기준

- 같은 모델군과 같은 split에서 MdAPE가 낮아지면 대표 오차가 개선된 것으로 본다.
- p95 APE가 함께 낮아지면 큰 오차 안정성도 개선된 것으로 본다.
- Warm과 Cold 결과는 합치지 않고 별도로 판단한다.
- Warm에서만 좋은 조합과 Cold에서만 좋은 조합은 분리 후보로 둔다.
