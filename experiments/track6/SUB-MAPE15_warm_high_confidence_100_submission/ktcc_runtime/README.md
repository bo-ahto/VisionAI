# KTCC 가격예측 MAPE 시험 실행 패키지

이 폴더는 시험장에서 가격예측 모델 성능을 재현하기 위한 실행 패키지다.

## 실행 방법

### 1. 제공된 학습/테스트 CSV로 재학습 후 평가

```bash
python scripts/ktcc_price_mape_train_and_test.py
```

이 방식은 `data/price_train_reference_110.csv`로 모델을 다시 학습하고,
`data/price_test_features_100.csv`와 `data/price_test_labels_100.csv`로 MAPE를 재계산한다.

### 2. 동결 모델로 평가

```bash
python scripts/ktcc_price_mape_test.py
```

## 실행 결과

스크립트 실행 후 `outputs/` 폴더에 결과가 생성된다.

- `outputs/ktcc_price_predictions_100.csv`: 100건 예측 결과와 오차
- `outputs/ktcc_price_mape_metrics.csv`: MAPE 등 성능 지표
- `outputs/ktcc_price_mape_metrics.json`: 성능 지표 JSON
- `outputs/ktcc_retrained_price_predictions_100.csv`: 재학습 후 100건 예측 결과와 오차
- `outputs/ktcc_retrained_price_mape_metrics.csv`: 재학습 후 MAPE 등 성능 지표
- `outputs/ktcc_retrained_price_mape_metrics.json`: 재학습 후 성능 지표 JSON

## 기준

- 시험 항목: 가격 예측 모델 성능
- 목표: MAPE 15% 이하
- 테스트 데이터: 고신뢰 Warm 가격예측 구간 100건
- 학습 reference: validation split 고신뢰 구간에서 `_track6_row_id` 중복을 제거한 독립 110건
- 모델: Warm/HCOEF 안정 기준가 + Huber residual 보정
- 최종 결과: MAPE 12.60%
