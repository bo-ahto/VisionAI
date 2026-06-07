# PP-QR1 Cold Quantile Regression 포함 분위수 종류별 비교

## 1. 실험 목적

- 기존 Cold Quantile 실험은 LightGBM q10/q50/q90, CatBoost q10/q50/q90 중심으로 진행됨.
- 이번 실험은 선형 Quantile Regression을 포함하여, 분위수 종류별 예측값이 가격 정확도와 가격 범위 산출에 어떤 차이를 만드는지 확인.
- 같은 데이터 분할, 같은 Cold 기준 피처셋, 같은 평가 지표로 비교하여 모델 특성 차이와 분위수 선택 효과를 분리.

## 2. 고정 조건

- 데이터 범위: Cold train/validation/test split.
- 기준 피처셋: `cold_lightgbm_final_artifact_common_features`.
- 사용 피처 수: `12`.
- 목표값: 실제 가격의 로그값 `ln_price_krw`.
- 평가지표: MdAPE, MAPE, p95_APE, RMSE_log, Within_30, Within_50.
- 점예측 비교: 각 분위수 예측값을 그대로 가격 예측값으로 사용.
- 범위 비교: q10~q90, q05~q95 구간의 실제 포함률과 구간 폭을 계산.

## 3. 모델별 의미

- LightGBM Quantile: 트리 리프를 이용해 비선형 구간별 분위수를 학습. Cold처럼 표본이 작고 가격 분포가 긴 경우, 고가/저가 꼬리 구간을 분리해 잡는 데 유리.
- CatBoost Quantile: 대칭 트리 구조로 범주형 조합을 안정적으로 반영. 작가, 매체, 크기 조합이 반복되는 구간에서 보수적인 분위수 예측을 확인하기 좋음.
- 선형 Quantile Regression: pinball loss로 특정 분위수를 직접 맞추는 선형 기준선. 트리 모델의 복잡한 분기 없이 피처 방향성을 확인하는 해석 기준으로 사용.

## 4. Test 핵심 결과

- 전체 후보 중 test MdAPE 최저: `catboost_quantile_q50` / MdAPE `0.4785`, MAPE `1.1557`, p95_APE `4.6234`.
- q50 후보 중 test MdAPE 최저: `catboost_quantile_q50` / MdAPE `0.4785`, MAPE `1.1557`, p95_APE `4.6234`.

## 5. Test 상위 후보

| 후보 | 모델 | 분위수 | MdAPE | MAPE | p95_APE | RMSE_log | Within_50 |
|---|---|---:|---:|---:|---:|---:|---:|
| `catboost_quantile_q50` | CatBoost Quantile | 0.50 | 0.4785 | 1.1557 | 4.6234 | 0.9203 | 0.5231 |
| `lightgbm_quantile_q50` | LightGBM Quantile | 0.50 | 0.4823 | 1.2424 | 4.3806 | 0.9411 | 0.5163 |
| `baseline_catboost_rmse` | CatBoost RMSE |  | 0.4835 | 1.4657 | 4.4439 | 0.9640 | 0.5176 |
| `catboost_quantile_q40` | CatBoost Quantile | 0.40 | 0.4853 | 1.0066 | 3.3333 | 0.9211 | 0.5202 |
| `linear_quantile_regression_q50` | Linear Quantile Regression | 0.50 | 0.4890 | 1.1245 | 3.6089 | 0.9175 | 0.5105 |
| `baseline_lightgbm_regression` | LightGBM Regression |  | 0.4909 | 1.4131 | 4.8212 | 0.9687 | 0.5131 |
| `lightgbm_quantile_q40` | LightGBM Quantile | 0.40 | 0.4922 | 1.0622 | 3.1623 | 0.9435 | 0.5115 |
| `catboost_quantile_q60` | CatBoost Quantile | 0.60 | 0.5077 | 1.5035 | 5.9329 | 0.9700 | 0.4934 |
| `lightgbm_quantile_q60` | LightGBM Quantile | 0.60 | 0.5101 | 1.5258 | 5.5155 | 0.9693 | 0.4914 |
| `catboost_quantile_q25` | CatBoost Quantile | 0.25 | 0.5213 | 0.8475 | 1.9741 | 1.0038 | 0.4743 |
| `lightgbm_quantile_q25` | LightGBM Quantile | 0.25 | 0.5221 | 0.8631 | 1.9362 | 1.0111 | 0.4705 |
| `linear_quantile_regression_q25` | Linear Quantile Regression | 0.25 | 0.5356 | 0.8560 | 1.9255 | 1.0443 | 0.4534 |

## 6. q50 중심 비교

| 후보 | 모델 | MdAPE | MAPE | p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| `catboost_quantile_q50` | CatBoost Quantile | 0.4785 | 1.1557 | 4.6234 | 범주형 조합을 대칭 트리로 반영한 중앙값 후보. |
| `lightgbm_quantile_q50` | LightGBM Quantile | 0.4823 | 1.2424 | 4.3806 | 중앙값 기준의 비선형 구간 예측. Cold의 일반 오차 기준 후보. |
| `linear_quantile_regression_q50` | Linear Quantile Regression | 0.4890 | 1.1245 | 3.6089 | 선형 Quantile Regression 기준선. 복잡한 분기 없이 중앙값을 직접 학습. |

## 7. 가격 범위 후보

| 모델 | 범위 | 실제 포함률 | 목표 포함률 | 중앙 범위 배율 | q50 MdAPE | q50 MAPE | crossing |
|---|---|---:|---:|---:|---:|---:|---:|
| CatBoost Quantile | q05_q95 | 0.8387 | 0.9000 | 11.954 | 0.4785 | 1.1557 | 0.0135 |
| LightGBM Quantile | q05_q95 | 0.8151 | 0.9000 | 9.462 | 0.4823 | 1.2424 | 0.0305 |
| Linear Quantile Regression | q10_q90 | 0.7886 | 0.8000 | 7.991 | 0.4890 | 1.1245 | 0.0000 |
| CatBoost Quantile | q10_q90 | 0.7206 | 0.8000 | 5.788 | 0.4785 | 1.1557 | 0.0135 |
| LightGBM Quantile | q10_q90 | 0.6989 | 0.8000 | 5.110 | 0.4823 | 1.2424 | 0.0305 |
| Linear Quantile Regression | q25_q75 | 0.4253 | 0.5000 | 2.259 | 0.4890 | 1.1245 | 0.0000 |
| CatBoost Quantile | q25_q75 | 0.4034 | 0.5000 | 2.384 | 0.4785 | 1.1557 | 0.0135 |
| LightGBM Quantile | q25_q75 | 0.3750 | 0.5000 | 2.213 | 0.4823 | 1.2424 | 0.0305 |

## 8. 방법론 판단

- MdAPE 최적화에는 q50 또는 q50 근처 분위수가 우선 후보.
- MAPE만 보면 q10/q25처럼 낮은 분위수가 유리해 보일 수 있으나, MdAPE가 크게 악화되므로 대표 가격 후보로는 부적합.
- q10/q25는 점예측 후보보다 하단 가격 또는 보수적 가격 범위 해석에 가깝게 사용.
- q40은 q50 대비 MdAPE 악화가 제한적이면서 MAPE와 p95_APE를 줄여 MAPE 방어형 후속 조합 후보로 볼 수 있음.
- MAPE는 큰 오차에 민감하므로 q40/q50/q60 주변을 비교하여 과대/과소 예측 방향을 확인해야 함.
- q10/q90, q05/q95는 점예측 후보라기보다 가격 범위와 신뢰도 산출용 후보.
- q05~q95도 test 실제 포함률이 목표 90%보다 낮으므로, 서비스 표시 범위로 쓰려면 conformal 보정 또는 segment별 폭 보정이 필요.
- Quantile Regression은 최종 성능 모델이라기보다 선형 기준선과 피처 방향성 점검용으로 활용하는 것이 적합.

## 9. 산출물

- 실험 폴더: `experiments/track6/PP-QR1_cold_quantile_regression_alpha_grid`.
- `outputs/metrics.csv`: 분위수별 점예측 성능.
- `outputs/range_metrics.csv`: q10~q90, q05~q95 범위 성능.
- `outputs/predictions.csv`: validation/test 샘플별 예측값.
- `experiment_config.json`: split, 피처, 모델 설정.
