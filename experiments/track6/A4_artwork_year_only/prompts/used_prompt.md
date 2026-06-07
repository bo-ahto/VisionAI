# A4 실험 사용 프롬프트 기록

- 기록 성격: 실제 대화 지시를 바탕으로 정리한 실험 지시 기록
- 실험 ID: A4
- 실험 목적: 제작연도 정보만으로 가격 예측에 도움이 되는지 확인한다.

## 실제 지시 요약

- 제작연도까지 포함된 최신 데이터셋을 앞으로 사용한다.
- A4 실험으로 `제작연도만` 사용하는 실험을 진행한다.
- 운영에서 사용할 수 없는 제작연도 출처 정보는 모델 입력에서 제외한다.
- 제작연도 결측 여부 플래그도 운영 입력으로 쓰기 어렵기 때문에 제외한다.
- A2/A3와 같은 통제 방식으로 진행한다.
- 실험 폴더를 따로 만든다.
- 사용 프롬프트를 실험 폴더에 같이 저장한다.
- 학습 데이터와 테스트 데이터 기준을 명확히 남긴다.
- 사용 원본 데이터와 생성 데이터를 실험 폴더에 복사해서 관리한다.
- 결과는 HTML과 CSV로 저장한다.

## 사용 데이터

- 제작연도 포함 split:
  - `data/track6_split_with_year`
- 학습 데이터:
  - `data/track6_split_with_year/features/warm/track6_train_warm_features.csv`
  - `data/track6_split_with_year/labels/track6_train_labels.csv`
- Warm 테스트 데이터:
  - `data/track6_split_with_year/features/warm/track6_test_warm_warm_features.csv`
  - `data/track6_split_with_year/labels/track6_test_warm_labels.csv`
- Cold 테스트 데이터:
  - `data/track6_split_with_year/features/cold/track6_test_cold_cold_features.csv`
  - `data/track6_split_with_year/labels/track6_test_cold_labels.csv`

## 비교 조건

- 제작연도:
  - `artwork_year`
- 작품 연한:
  - `artwork_age`
- 제작연도 + 작품 연한:
  - `artwork_year`
  - `artwork_age`

## 비교 모델

- Warm A: Huber
- Warm B: Linear Regression
- Warm C: Ridge
- Cold D: Huber
- Cold E: Quantile-LAD
- Cold F: LightGBM

## 데이터 사용 기준

- feature 파일과 label 파일은 `_track6_row_id`로 연결한다.
- label은 학습 목표값과 평가 지표 계산에만 사용한다.
- label은 모델 입력 피처로 사용하지 않는다.
- 샘플링 없이 전체 split을 사용한다.
- 제작연도 보강 출처는 데이터 검토용으로만 남기고 모델 입력에는 사용하지 않는다.
- Saatchi 제작연도는 상세 페이지 HTML 보강값이므로 원본 CSV 수집값과 구분해서 해석한다.

## 결과 지표

- R2
- MdAPE
- p95 APE
- Within-30
- Within-50
- MAPE
