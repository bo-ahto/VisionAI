# Blind Test 대비 Warm 고신뢰 가격예측 프로토콜

이 폴더는 시험기관이 별도 blind candidate pool을 제공할 때 쓰는 고정 예측 프로토콜이다. 기존 제출용 모델을 재학습하지 않고 그대로 사용한다.

## 원칙

- 모델 재학습 없음
- blind label 사용 없음
- 고신뢰 rule 변경 없음
- 입력 candidate pool에서 feature-only 조건으로 eligible row를 고른 뒤 상위 100건 예측
- MAPE 15% 이하 주장은 `고신뢰 Warm 가격예측 구간`에 한정

## 고정 모델

- 기준 모델: `hcoef_stable`
- 보정 모델: `warm_high_confidence_residual_huber_rowid_dedup`
- 모델 artifact: `../SUB-MAPE15_warm_high_confidence_100_submission/artifacts/warm_high_confidence_residual_huber.joblib`
- 모델 설정: `../SUB-MAPE15_warm_high_confidence_100_submission/artifacts/model_config.json`

## Blind 입력 조건

입력 CSV에는 정답 가격이 없어야 한다. 필요한 컬럼은 [blind_input_schema.json](data/blind_input_schema.json)에 정리했다.

필수 component/policy 컬럼:

- `hcoef_stable`
- `current_70_30`
- `ppv8_service_proxy`
- `svc_numeric_seed_mean`
- `l10_seq_pred_log`
- `quantile_width`
- `l10_price_range_ratio`
- `svc_group_n`
- `log_area`

## 실행

내부 smoke 데이터 생성:

```bash
python3 experiments/track6/SUB-MAPE15_warm_high_confidence_blind_ready/scripts/build_internal_blind_smoke_data.py
```

blind 예측:

```bash
python3 experiments/track6/SUB-MAPE15_warm_high_confidence_blind_ready/scripts/predict_blind_high_confidence.py \
  --input experiments/track6/SUB-MAPE15_warm_high_confidence_blind_ready/data/internal_blind_smoke_candidate_pool_features.csv \
  --output experiments/track6/SUB-MAPE15_warm_high_confidence_blind_ready/outputs/internal_blind_smoke_predictions.csv \
  --required-n 100
```

label이 별도 제공된 경우 평가:

```bash
python3 experiments/track6/SUB-MAPE15_warm_high_confidence_blind_ready/scripts/evaluate_blind_predictions.py \
  --predictions experiments/track6/SUB-MAPE15_warm_high_confidence_blind_ready/outputs/internal_blind_smoke_predictions.csv \
  --labels experiments/track6/SUB-MAPE15_warm_high_confidence_blind_ready/data/internal_blind_smoke_candidate_pool_labels.csv \
  --output experiments/track6/SUB-MAPE15_warm_high_confidence_blind_ready/outputs/internal_blind_smoke_metrics.csv
```

## 주의

시험기관이 정확히 100건만 제공하고 그중 고신뢰 조건을 만족하지 않는 row가 많으면, 현재 제출 모델의 15% MAPE 주장을 그대로 보장할 수 없다. 이 프로토콜은 candidate pool에서 고신뢰 100건을 고정 선별하는 방식으로 제출해야 가장 방어력이 있다.
