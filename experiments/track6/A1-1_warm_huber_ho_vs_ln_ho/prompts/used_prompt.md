# A1-1 실험 사용 프롬프트 기록

- 기록 성격: 실제 대화 지시를 바탕으로 정리한 실험 지시 기록
- 실험 ID: A1-1
- 실험 목적: Warm Huber 모델에서 Ho 원값과 ln Ho 의 예측력 절대비교.

## 실제 지시 요약

- Warm Huber 모델만 사용한다.
- Ho와 ln Ho를 비교한다.
- 실험 폴더를 따로 만든다.
- 사용 프롬프트도 실험 폴더에 같이 저장한다.
- 학습 데이터와 테스트 데이터 기준을 명확히 남긴다.
- 결과는 HTML과 CSV로 저장한다.

## 비교 조건

- 조건 1: `estimated_ho`
- 조건 2: `ln_estimated_ho`
- 모델: Warm Huber
- 학습 목표값: `ln_price_krw`
- 평가 기준:
  - R2
  - MdAPE
  - p95 APE
  - Within-30
  - Within-50
  - MAPE

## 데이터 사용 기준

- 학습 데이터:
  - `data/track6_split/features/warm/track6_train_warm_features.csv`
  - `data/track6_split/labels/track6_train_labels.csv`
- Warm 테스트 데이터:
  - `data/track6_split/features/warm/track6_test_warm_warm_features.csv`
  - `data/track6_split/labels/track6_test_warm_labels.csv`
- feature 파일과 label 파일은 `_track6_row_id`로 연결한다.
- label은 학습 목표값과 평가 지표 계산에만 사용한다.
- label은 모델 입력 피처로 사용하지 않는다.
- 샘플링 없이 전체 split을 사용한다.
