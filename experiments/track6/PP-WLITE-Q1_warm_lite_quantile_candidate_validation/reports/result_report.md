# PP-WLITE-Q1 Warm-lite Quantile 후보 검증

## 1. 목적

Warm-lite v0.1의 현재 Huber 6구성 평균(all6_current)에 Quantile 회귀 후보를 적용할 근거가 있는지 확인한다.

## 2. 평가 설계

- PP-WCUT5와 같은 실존 저이력 작가 leave-one-out 설계
- train 이력 2~5건 작가에서 seed별 작가당 1작품 hold-out
- hold-out 작품 자기 가격은 작가 이력 통계에서 제외
- LightGBM Quantile q50을 full/lean 피처 구성으로 학습
- q10/q90은 full 피처 기준 quantile_width 진단용으로 산출

## 3. Overall metrics

| candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE | delta_MdAPE_minus_all6 | delta_MAPE_minus_all6 | delta_p95_APE_minus_all6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all6_50_lgbq_full_50 | 1947 | 0.104010 | 0.272166 | 0.870881 | 2 | 1 | 4 | -0.005217 | -0.014400 | -0.005589 |
| all6_75_lgbq_full_25 | 1947 | 0.106552 | 0.277130 | 0.868162 | 4 | 2 | 1 | -0.002675 | -0.009436 | -0.008308 |
| lgbq_full_q50 | 1947 | 0.101919 | 0.278263 | 0.880499 | 1 | 3 | 6 | -0.007308 | -0.008303 | 0.004029 |
| lgbq_full_lean_avg | 1947 | 0.105911 | 0.279288 | 0.869746 | 3 | 4 | 2 | -0.003316 | -0.007278 | -0.006724 |
| lgbq_lean_q50 | 1947 | 0.113711 | 0.285422 | 0.869784 | 6 | 5 | 3 | 0.004484 | -0.001144 | -0.006686 |
| all6_current | 1947 | 0.109227 | 0.286566 | 0.876470 | 5 | 6 | 5 | 0.000000 | 0.000000 | 0.000000 |

## 4. Metrics by history_k

| history_k | candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | lgbq_full_q50 | 621 | 0.122328 | 0.312917 | 0.942383 | 4 | 1 | 4 |
| 1 | lgbq_full_lean_avg | 621 | 0.124783 | 0.313015 | 0.878501 | 5 | 2 | 2 |
| 1 | all6_50_lgbq_full_50 | 621 | 0.115153 | 0.314462 | 0.956738 | 2 | 3 | 6 |
| 1 | lgbq_lean_q50 | 621 | 0.126557 | 0.318546 | 0.878040 | 6 | 4 | 1 |
| 1 | all6_75_lgbq_full_25 | 621 | 0.112589 | 0.324695 | 0.936048 | 1 | 5 | 3 |
| 1 | all6_current | 621 | 0.120677 | 0.341476 | 0.955881 | 3 | 6 | 5 |
| 2 | all6_50_lgbq_full_50 | 489 | 0.118455 | 0.258628 | 0.846719 | 2 | 1 | 3 |
| 2 | all6_75_lgbq_full_25 | 489 | 0.118746 | 0.261532 | 0.870198 | 3 | 2 | 5 |
| 2 | all6_current | 489 | 0.118375 | 0.270704 | 0.877912 | 1 | 3 | 6 |
| 2 | lgbq_full_q50 | 489 | 0.127923 | 0.275845 | 0.816993 | 5 | 4 | 2 |
| 2 | lgbq_full_lean_avg | 489 | 0.121626 | 0.279140 | 0.811334 | 4 | 5 | 1 |
| 2 | lgbq_lean_q50 | 489 | 0.132839 | 0.287792 | 0.850362 | 6 | 6 | 4 |
| 3 | all6_50_lgbq_full_50 | 324 | 0.088710 | 0.247326 | 0.770415 | 3 | 1 | 3 |
| 3 | all6_75_lgbq_full_25 | 324 | 0.100201 | 0.249700 | 0.704075 | 5 | 2 | 1 |
| 3 | all6_current | 324 | 0.105981 | 0.254102 | 0.714172 | 6 | 3 | 2 |
| 3 | lgbq_full_q50 | 324 | 0.081031 | 0.254126 | 0.894499 | 1 | 4 | 5 |
| 3 | lgbq_full_lean_avg | 324 | 0.087483 | 0.258709 | 0.887357 | 2 | 5 | 4 |
| 3 | lgbq_lean_q50 | 324 | 0.098790 | 0.267300 | 0.906093 | 4 | 6 | 6 |
| 4 | all6_50_lgbq_full_50 | 513 | 0.080160 | 0.249558 | 0.794447 | 2 | 1 | 3 |
| 4 | lgbq_full_lean_avg | 513 | 0.080328 | 0.251599 | 0.821067 | 3 | 2 | 5 |
| 4 | all6_75_lgbq_full_25 | 513 | 0.087872 | 0.251743 | 0.786252 | 5 | 3 | 1 |
| 4 | lgbq_full_q50 | 513 | 0.079887 | 0.253864 | 0.825560 | 1 | 4 | 6 |
| 4 | lgbq_lean_q50 | 513 | 0.086167 | 0.254511 | 0.816766 | 4 | 5 | 4 |
| 4 | all6_current | 513 | 0.092263 | 0.255719 | 0.788372 | 6 | 6 | 2 |

## 5. Bootstrap vs all6_current

| candidate | n_boot | p_candidate_better_all6_MdAPE | p_candidate_better_all6_MAPE | p_candidate_better_all6_p95_APE | p_all6_better_candidate_MdAPE | p_all6_better_candidate_MAPE | p_all6_better_candidate_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all6_50_lgbq_full_50 | 400 | 0.940000 | 1.000000 | 0.617500 | 0.060000 | 0.000000 | 0.382500 |
| all6_75_lgbq_full_25 | 400 | 0.900000 | 1.000000 | 0.730000 | 0.100000 | 0.000000 | 0.270000 |
| lgbq_full_lean_avg | 400 | 0.782500 | 0.775000 | 0.625000 | 0.217500 | 0.225000 | 0.375000 |
| lgbq_full_q50 | 400 | 0.905000 | 0.790000 | 0.492500 | 0.095000 | 0.210000 | 0.507500 |
| lgbq_lean_q50 | 400 | 0.230000 | 0.617500 | 0.565000 | 0.770000 | 0.382500 | 0.435000 |

## 6. Quantile width diagnostics

| width_bin | n | width_min | width_max | all6_current_MdAPE | all6_current_MAPE | all6_current_p95_APE | lgbq_full_q50_MdAPE | lgbq_full_q50_MAPE | lgbq_full_q50_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1_low | 487 | 0.000000 | 0.384323 | 0.028895 | 0.168614 | 0.473808 | 0.027077 | 0.158689 | 0.451329 |
| q2 | 487 | 0.384370 | 0.578970 | 0.071240 | 0.140288 | 0.514338 | 0.064108 | 0.136723 | 0.488364 |
| q3 | 486 | 0.579107 | 0.900757 | 0.142368 | 0.290267 | 0.842643 | 0.145495 | 0.292021 | 0.865925 |
| q4_high | 487 | 0.901136 | 2.464622 | 0.299667 | 0.547102 | 1.557778 | 0.283493 | 0.525648 | 1.581822 |

## 7. Config

{
  "experiment_id": "PP-WLITE-Q1",
  "experiment_slug": "PP-WLITE-Q1_warm_lite_quantile_candidate_validation",
  "eval_design": "PP-WCUT5-equivalent real low-history leave-one-out, train history 2~5, seeds [20260612, 20260613, 20260614]",
  "rows": 1947,
  "artist_count": 649,
  "baseline": "all6_current",
  "quantile_model": "LightGBM objective=quantile, q10/q50/q90 full features, q50 lean features",
  "candidates": [
    "all6_current",
    "lgbq_full_q50",
    "lgbq_lean_q50",
    "lgbq_full_lean_avg",
    "all6_75_lgbq_full_25",
    "all6_50_lgbq_full_50"
  ],
  "all6_current_metrics": {
    "MdAPE": 0.109227,
    "MAPE": 0.286566,
    "p95_APE": 0.87647
  },
  "best_by_metric": {
    "MdAPE": "lgbq_full_q50",
    "MAPE": "all6_50_lgbq_full_50",
    "p95_APE": "all6_75_lgbq_full_25"
  },
  "n_boot": 400,
  "prohibitions": [
    "0604 사용 금지"
  ]
}
