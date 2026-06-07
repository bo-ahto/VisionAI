# E5-1 실험 프롬프트

- 실험명: 작품 조건 통제 후 작가 국적 효과 실험
- 실험 목적:
  - 작가 국적 정보가 가격 차이를 설명하는지 확인한다.
  - 국적만 단독으로 넣지 않고, 작품의 기본 조건을 먼저 통제한다.
  - 작품 조건을 맞춘 뒤에도 국적 추가가 예측 성능을 개선하는지 확인한다.

## 가설

- 작가 국적 정보는 작품 조건을 통제한 뒤에도 가격 예측에 일부 도움을 줄 수 있다.
- 단, 국적은 원인 변수라기보다 시장, 플랫폼, 표본 편향이 섞인 대리 변수일 수 있다.

## 통제 조건

- 호수: `ln_estimated_ho`
- 난트 재료 번호: `nant_material_idx`
- 난트 도구: `nant_tool`
- 난트 지지체: `nant_support`

## 비교 피처

- 통제 기준:
  - `ln_estimated_ho`
  - `nant_material_idx`
  - `nant_tool`
  - `nant_support`
- 통제 기준 + 국적:
  - `ln_estimated_ho`
  - `nant_material_idx`
  - `nant_tool`
  - `nant_support`
  - `artist_meta_nationality`
- 통제 기준 + 국적 + 국적 결측 여부:
  - `ln_estimated_ho`
  - `nant_material_idx`
  - `nant_tool`
  - `nant_support`
  - `artist_meta_nationality`
  - `artist_meta_nationality_is_missing`

## 실험 방법

- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`에 명시하고 `StandardScaler`를 적용
- 범주형 변수는 `OneHotEncoder(handle_unknown='ignore')`로 처리

## Warm 테스트

- Warm 정의: 학습 데이터에 같은 작가가 있는 작품을 예측하는 상황
- Warm 학습 데이터: `data/train_features.csv` + `data/train_labels.csv`
- Warm 테스트 데이터: `data/test_warm_features.csv` + `data/test_warm_labels.csv`
- 비교 방식:
  - 통제 기준 모델과 국적 추가 모델의 성능을 비교한다.
  - MdAPE가 낮아지고 p95_APE가 악화되지 않으면 국적 추가를 후보로 본다.

## Cold 테스트

- Cold 정의: 학습 데이터에 한 번도 등장하지 않은 작가의 작품을 예측하는 상황
- Cold 학습 데이터: `data/train_features.csv` + `data/train_labels.csv`
- Cold 테스트 데이터: `data/test_cold_features.csv` + `data/test_cold_labels.csv`
- Cold 모델은 작가명을 쓰지 않는다.
- 비교 방식:
  - 통제 기준 모델과 국적 추가 모델의 성능을 비교한다.
  - 국적 정보는 운영에서 작가 DB로 확보 가능한 경우에만 후보로 둔다.

## 보조 분석

- 호수 구간, 난트 재료, 난트 도구, 난트 지지체가 같은 조건 묶음을 만든다.
- 같은 조건 묶음 안에서 국적별 예측 오차를 확인한다.
- 조건 묶음별 표본 수가 너무 적으면 결론을 내리지 않는다.

## 평가 지표

- R2
- RMSE(log)
- MdAPE
- p95_APE
- Within_30
- Within_50
- MAPE
