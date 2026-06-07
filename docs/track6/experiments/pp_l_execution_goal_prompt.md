# PP-L 실험 실행 Goal Prompt

## Goal

Track6 가격 예측 모델에서 `Huber`, `Quantile`, `CatBoost`를 조합한 PP-L 실험군을 실행한다. 목표는 MdAPE를 유지하거나 개선하는 범위 안에서 MAPE와 p95_APE를 줄일 수 있는 순차 학습 구조를 검증하는 것이다.

실험은 아래 문서를 기준으로 진행한다.

- `docs/track6/experiments/postprocessing_experiment_matrix.md`
- `docs/track6/experiments/huber_quantile_catboost_mape_optimization_plan.md`
- `docs/track6/experiments/supervisor_postprocessing_required_experiments.md`

## Execution Scope

실행 대상은 `Group PP-L` 전체다.

```text
PP-L1  CatBoost MAPE 목적 최적화
PP-L2  CatBoost 옵션별 MAPE 민감도
PP-L3  Huber 선행 + CatBoost residual 보정
PP-L4  Huber + Quantile width 위험 구간 보정
PP-L5  Huber + Quantile + CatBoost 라우팅
PP-L6  Huber / Quantile / CatBoost 가중 앙상블
PP-L7-0  Quantile 구간 생성 및 검증
PP-L7-H  Quantile 구간별 Huber 상세 학습
PP-L7-CB  Quantile 구간별 CatBoost 상세 학습
PP-L7-HCB  Quantile 구간별 Huber + CatBoost 결합
PP-L8  Quantile-Huber-CatBoost 순차 학습
PP-L9  Huber-Quantile-CatBoost residual 순차 학습
```

## Experiment Folder Management

기존 Track6 실험처럼 각 실험은 독립 폴더로 관리한다. 실험 결과를 한 폴더에 섞어 저장하지 않는다.

기본 경로:

```text
experiments/track6/
```

실험 ID별 권장 폴더명:

```text
experiments/track6/PP-L1_catboost_mape_objective/
experiments/track6/PP-L2_catboost_mape_sensitivity/
experiments/track6/PP-L3_huber_catboost_residual/
experiments/track6/PP-L4_huber_quantile_width_risk_calibration/
experiments/track6/PP-L5_huber_quantile_catboost_routing/
experiments/track6/PP-L6_huber_quantile_catboost_weighted_ensemble/
experiments/track6/PP-L7_0_quantile_segment_validation/
experiments/track6/PP-L7_H_quantile_segment_huber_refit/
experiments/track6/PP-L7_CB_quantile_segment_catboost_refit/
experiments/track6/PP-L7_HCB_quantile_segment_huber_catboost_combo/
experiments/track6/PP-L8_quantile_huber_catboost_sequential/
experiments/track6/PP-L9_huber_quantile_catboost_residual_sequential/
```

각 실험 폴더는 아래 구조를 사용한다.

```text
experiments/track6/{experiment_id_slug}/
  README.md
  experiment_config.json
  data/
    split_manifest.json
    feature_columns.json
    train_index.csv
    valid_index.csv
    test_index.csv
  outputs/
    metrics.csv
    slice_metrics.csv
    predictions.csv
    oof_predictions.csv
    residuals.csv
    segment_definition.csv
    statistical_tests.csv
    complexity_report.csv
  reports/
    result_report.md
    result_report.html
  artifacts/
    model_manifest.json
    calibration_map.json
    routing_policy.json
  logs/
    run_log.txt
```

필수 관리 규칙:

1. `experiment_config.json`에는 실험 ID, 실행 일시, 데이터 split, 사용 피처, 모델 설정, random seed, 평가 지표를 기록한다.
2. `split_manifest.json`에는 train / validation / test 기준이 기존 Track6 고정 split과 일치하는지 기록한다.
3. `feature_columns.json`에는 실제 학습에 사용한 피처를 모두 기록한다.
4. `oof_predictions.csv`는 residual 학습이 있는 실험에서 필수다.
5. `segment_definition.csv`에는 Quantile 구간 경계, `price_range_ratio`, `residual_range_ratio`, fallback 기준을 기록한다.
6. `statistical_tests.csv`에는 bootstrap CI, Wilcoxon test, seed 반복 결과를 기록한다.
7. `complexity_report.csv`에는 모델 수, 학습 단계 수, 구간 수, fallback 수, 추론 시 모델 호출 수를 기록한다.
8. `reports/result_report.html`은 상사 보고 또는 실험 검토 시 바로 볼 수 있게 작성한다.
9. 실패/보류 실험도 폴더를 유지하고 실패 사유를 `README.md`와 `reports/result_report.md`에 기록한다.
10. 동일 실험을 재실행할 경우 기존 폴더를 덮어쓰지 말고 `run_id` 또는 날짜 suffix를 사용한다.

## Required Principles

아래 원칙을 어기면 실험 결과를 채택하지 않는다.

1. train / validation / test 역할을 분리한다.
2. validation에서 구간 경계, 보정값, 가중치, 라우팅 기준을 정한다.
3. test는 최종 후보 1회 확인에만 사용한다.
4. residual 모델 학습에는 반드시 OOF 예측 기반 residual을 사용한다.
5. PP-L8의 `price_range_ratio`와 PP-L9의 `residual_range_ratio`를 혼동하지 않는다.
6. 개선된 후보뿐 아니라 실패/보류 후보도 기록한다.
7. MdAPE가 악화되면 MAPE가 좋아져도 바로 채택하지 않는다.

## Baselines

모든 PP-L 후보는 아래 baseline과 비교한다.

```text
B0 Warm Huber 단독
B1 Cold CatBoost 단독
B2 Quantile q50 단독
B3 기준 모델 + 전체 median residual 보정
B4 Huber + CatBoost residual
B5 Huber + Quantile residual q50
B6 PP-L8 Quantile → Huber → CatBoost
B7 PP-L9 Huber → Quantile residual → CatBoost
B8 Huber / Quantile / CatBoost 단순 가중 앙상블
```

## Metrics

Primary metric:

```text
MdAPE
```

Secondary metrics:

```text
MAPE
p95_APE
RMSE_log
Within_30
Within_50
```

Slice metrics:

```text
Warm / Cold
저가 / 중가 / 고가
stable / caution / risk
low / mid / high uncertainty
```

## Quantile Segment Definition

Quantile 모델은 구간을 직접 출력하지 않는다. Quantile 모델은 아래 값을 출력한다.

```text
q10_log
q50_log
q90_log
```

예측 가격 범위 폭은 아래처럼 계산한다.

```text
quantile_width = q90_log - q10_log
price_range_ratio = exp(quantile_width)
```

초기 탐색 기준:

```text
low uncertainty:
  quantile_width <= validation 33% 분위값

mid uncertainty:
  validation 33% 분위값 < quantile_width <= validation 66% 분위값

high uncertainty:
  quantile_width > validation 66% 분위값
```

추가 민감도 기준:

```text
50% / 80%
70% / 90%
price_range_ratio 1.5배 / 2.5배
```

해석 기준:

```text
stable:
  price_range_ratio <= 1.5배

caution:
  1.5배 < price_range_ratio <= 2.5배

risk:
  price_range_ratio > 2.5배
```

## PP-L Execution Plan

### Step 1. PP-L1 CatBoost MAPE 목적 최적화

목표:

- CatBoost 자체 설정을 MAPE 감소 방향으로 조정할 가치가 있는지 확인한다.

비교군:

```text
A 기존 CatBoost
B 기존 loss + eval_metric=MAPE
C 저가 구간 sample_weight
D MAE/Quantile 계열 loss 후보
```

확인:

- MdAPE 유지 여부
- MAPE 개선 여부
- p95_APE 악화 여부
- 저가 구간만 좋아지고 중가/고가가 악화되는지 여부

### Step 2. PP-L2 CatBoost 옵션별 MAPE 민감도

목표:

- CatBoost 옵션이 MAPE와 tail 안정성에 미치는 영향을 확인한다.

옵션:

```text
depth
learning_rate
l2_leaf_reg
early_stopping
```

제한된 grid로만 실행한다. 과도한 탐색으로 validation에 맞추지 않는다.

### Step 3. PP-L3 Huber 선행 + CatBoost residual 보정

목표:

- Huber 중심선 위에 CatBoost가 조건 조합 residual을 보정할 수 있는지 확인한다.

필수:

```text
huber_pred_log = OOF Huber 예측값
residual_log = actual_log - huber_pred_log
CatBoost target = residual_log
final_pred_log = huber_pred_log + catboost_residual_pred
```

OOF가 아니면 실험 결과를 채택하지 않는다.

### Step 4. PP-L4 Huber + Quantile width 위험 구간 보정

목표:

- Quantile width가 큰 구간에만 보정을 적용했을 때 MAPE와 p95_APE가 줄어드는지 확인한다.

필수:

- validation에서 구간 경계를 정한다.
- test에는 validation 경계를 그대로 적용한다.
- stable 구간이 악화되면 보류한다.

### Step 5. PP-L7-0 Quantile 구간 생성 및 검증

목표:

- `quantile_width`와 `price_range_ratio`가 실제 고오차 구간을 구분하는지 검증한다.

산출:

```text
구간별 rows
구간별 MdAPE
구간별 MAPE
구간별 p95_APE
구간별 실제 APE 분포
구간별 fallback 필요 여부
```

### Step 6. PP-L7-H Quantile 구간별 Huber 상세 학습

목표:

- Quantile 구간별 Huber 재학습이 중앙 가격선을 안정화하는지 확인한다.

확인:

- 구간별 Huber 계수
- 구간별 outlier 비율
- 구간별 residual 중앙값
- risk 구간 MAPE/p95_APE 개선 여부

### Step 7. PP-L7-CB Quantile 구간별 CatBoost 상세 학습

목표:

- Quantile 구간별 CatBoost 재학습이 조건 조합 오차를 줄이는지 확인한다.

확인:

- 구간별 CatBoost 성능
- leaf/segment residual
- leaf별 rows
- low 구간 과적합 여부
- risk 구간 MAPE/p95_APE 개선 여부

### Step 8. PP-L7-HCB Quantile 구간별 Huber + CatBoost 결합

목표:

- 구간별로 Huber와 CatBoost의 역할을 나누는 결합이 유효한지 확인한다.

전략:

```text
stable:
  Huber 유지

caution:
  Huber/CatBoost 가중 평균 비교

risk:
  CatBoost residual 보정 또는 CatBoost 대체 예측 비교
```

### Step 9. PP-L8 Quantile-Huber-CatBoost 순차 학습

목표:

- Quantile 선행 진단, Huber 중심선, CatBoost residual 보정 순서가 유효한지 확인한다.

구조:

```text
Quantile → Huber → CatBoost
```

주의:

- 여기서 ratio는 가격 예측 범위인 `price_range_ratio`다.
- Huber pred는 OOF로 생성한다.
- CatBoost residual target은 `actual_log - OOF huber_pred_log`다.

### Step 10. PP-L9 Huber-Quantile-CatBoost residual 순차 학습

목표:

- Huber 기준 모델을 유지하면서, Quantile이 Huber residual 범위를 추정하고 CatBoost가 남은 residual을 보정하는지 확인한다.

구조:

```text
Huber → Quantile residual → CatBoost remaining residual
```

계산:

```text
huber_pred_log = OOF Huber 예측값
residual_log = actual_log - huber_pred_log

residual_q10, residual_q50, residual_q90 = Quantile residual 예측
residual_width = residual_q90 - residual_q10
residual_range_ratio = exp(residual_width)

quantile_corrected_pred_log = huber_pred_log + residual_q50
remaining_residual_log = actual_log - quantile_corrected_pred_log

final_pred_log = huber_pred_log + residual_q50 + catboost_remaining_residual_pred
```

주의:

- 여기서 ratio는 가격 범위가 아니라 Huber residual 범위다.
- PP-L8의 `price_range_ratio`와 혼동하지 않는다.

### Step 11. PP-L5 / PP-L6 비교

목표:

- 순차 구조가 라우팅 또는 단순 가중 앙상블보다 실제로 나은지 확인한다.

비교:

```text
PP-L5 라우팅
PP-L6 단순 가중 앙상블
PP-L8 순차 구조
PP-L9 residual 순차 구조
```

## Statistical Validation

최종 후보는 아래 검증을 수행한다.

```text
paired bootstrap 95% CI
Wilcoxon signed-rank test
seed 반복 평균/표준편차
구간별 bootstrap
```

Sample-level delta:

```text
delta_APE_i = APE_baseline_i - APE_candidate_i
```

`delta_APE_i`가 양수이면 candidate가 해당 샘플에서 개선된 것이다.

## Acceptance Rule

채택:

```text
MdAPE 유지 또는 개선
MAPE 개선
p95_APE 악화 없음
stable 구간 악화 없음
validation/test 방향 일치
baseline 대비 통계적으로 안정적인 개선
```

보류:

```text
MAPE만 개선되고 MdAPE 악화
p95_APE 악화
stable 구간 악화
test 재현 실패
단순 baseline 대비 개선 불명확
복잡도 대비 개선폭 부족
```

## Required Outputs

각 실험은 자기 실험 폴더 아래에 아래 산출물을 남긴다.

```text
README.md
experiment_config.json
data/split_manifest.json
data/feature_columns.json
outputs/metrics.csv
outputs/slice_metrics.csv
outputs/predictions.csv
outputs/oof_predictions.csv
outputs/residuals.csv
outputs/segment_definition.csv
outputs/statistical_tests.csv
outputs/complexity_report.csv
reports/result_report.md
reports/result_report.html
artifacts/model_manifest.json
artifacts/calibration_map.json
artifacts/routing_policy.json
logs/run_log.txt
```

최종 보고서에는 아래 표를 포함한다.

```text
baseline 전체 비교표
PP-L 후보별 성능표
구간 기준 민감도 분석표
통계 검증표
복잡도 대비 개선표
실패/보류 실험 기록표
최종 채택/보류 판단표
```
