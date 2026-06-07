# A1 실험 사용 프롬프트 기록

- 기록 성격: 실제 대화 지시를 바탕으로 정리한 사후 기록
- 실험 ID: A1
- 실험 목적: Ho / ln Ho / Size / ln Size 변수가 가격 예측에 주는 영향을 Warm / Cold 기준으로 비교

## 실제 지시 요약

- 결과 양식에 맞춰 A1 실험 결과를 작성한다.
- 관련 실험 폴더를 만든다.
- 학습 데이터와 테스트 데이터를 Warm / Cold 기준으로 나누어 실험한다.
- 처음에는 샘플 테스트로 구조를 확인한다.
- 이후 샘플 제한을 제거하고 전체 Track6 split 기준으로 다시 실행한다.
- 학습 데이터와 테스트 데이터 기준을 명확하게 남긴다.
- 코드 주석에도 데이터 기준을 남긴다.
- 결과 HTML에서 사용 데이터와 사용 코드가 바로 보이게 한다.

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

## 실행 조건

- 샘플링 없이 전체 split을 사용한다.
- feature 파일과 label 파일은 `_track6_row_id`로 연결한다.
- label은 학습 목표값과 평가 지표 계산에만 사용한다.
- label은 모델 입력 피처로 사용하지 않는다.

## 비교 변수

- Ho: `estimated_ho`
- ln Ho: `ln_estimated_ho`
- Size: `area_cm2`
- ln Size: `log_area`

## 비교 모델

- Warm A: Huber
- Warm B: Linear Regression
- Warm C: Ridge
- Cold D: Huber
- Cold E: Quantile-LAD
- Cold F: LightGBM

## 결과 지표

- R2
- MdAPE
- p95 APE
- Within-30
- Within-50
- MAPE
