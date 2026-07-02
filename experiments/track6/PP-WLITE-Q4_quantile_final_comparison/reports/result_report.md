# PP-WLITE-Q4 Warm-lite Quantile 최종 후보 비교

## 1. 목적

Q1/Q2/Q3 산출물을 같은 행 기준으로 병합해 단순 Quantile blend와 Quantile+LightGBM residual 보정 후보를 마지막으로 비교한다.

## 2. Q1-like 실존 저이력 leave-one-out

| candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| simple_all6_q50_blend | 1947 | 0.104010 | 0.272166 | 0.870881 | 1 | 1 | 4 |
| residual_lgb_s05_cap010 | 1947 | 0.107246 | 0.275773 | 0.852026 | 5 | 2 | 1 |
| residual_lgb_s05_cap005 | 1947 | 0.107155 | 0.277368 | 0.856712 | 4 | 3 | 2 |
| residual_cb_s05_cap010 | 1947 | 0.105628 | 0.278785 | 0.873310 | 2 | 4 | 5 |
| simple_qavg_q1 | 1947 | 0.105911 | 0.279288 | 0.869746 | 3 | 5 | 3 |
| all6_current | 1947 | 0.109227 | 0.286566 | 0.876470 | 6 | 6 | 6 |

## 3. Q1-like by history_k

| history_k | candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | residual_lgb_s05_cap010 | 621 | 0.110652 | 0.306967 | 0.875776 | 1 | 1 | 1 |
| 1 | simple_all6_q50_blend | 621 | 0.115153 | 0.314462 | 0.956738 | 3 | 5 | 6 |
| 1 | all6_current | 621 | 0.120677 | 0.341476 | 0.955881 | 5 | 6 | 5 |
| 2 | simple_all6_q50_blend | 489 | 0.118455 | 0.258628 | 0.846719 | 2 | 1 | 5 |
| 2 | all6_current | 489 | 0.118375 | 0.270704 | 0.877912 | 1 | 2 | 6 |
| 2 | residual_lgb_s05_cap010 | 489 | 0.130034 | 0.281075 | 0.826593 | 5 | 6 | 2 |
| 3 | simple_all6_q50_blend | 324 | 0.088710 | 0.247326 | 0.770415 | 2 | 1 | 2 |
| 3 | all6_current | 324 | 0.105981 | 0.254102 | 0.714172 | 6 | 2 | 1 |
| 3 | residual_lgb_s05_cap010 | 324 | 0.090080 | 0.254148 | 0.927107 | 3 | 3 | 6 |
| 4 | residual_lgb_s05_cap010 | 513 | 0.091271 | 0.246615 | 0.799123 | 5 | 1 | 3 |
| 4 | simple_all6_q50_blend | 513 | 0.080160 | 0.249558 | 0.794447 | 1 | 3 | 2 |
| 4 | all6_current | 513 | 0.092263 | 0.255719 | 0.788372 | 6 | 6 | 1 |

## 4. Q1 residual vs simple bootstrap

| candidate_a | candidate_b | n_boot | p_a_better_MdAPE | p_a_better_MAPE | p_a_better_p95_APE | p_b_better_MdAPE | p_b_better_MAPE | p_b_better_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_lgb_s05_cap010 | simple_all6_q50_blend | 800 | 0.208750 | 0.271250 | 0.755000 | 0.791250 | 0.728750 | 0.245000 |

## 5. Q2-like k절단 운영 시뮬레이션

| candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| residual_lgb_s05_cap010 | 7284 | 0.154475 | 0.303435 | 1.000528 | 1 | 1 | 1 |
| residual_lgb_s05_cap005 | 7284 | 0.155200 | 0.304895 | 1.010105 | 2 | 2 | 2 |
| simple_qavg_q2 | 7284 | 0.157474 | 0.307616 | 1.027865 | 3 | 3 | 3 |
| residual_cb_s05_cap010 | 7284 | 0.158520 | 0.309216 | 1.032895 | 4 | 4 | 4 |
| simple_all6_q50_blend | 7284 | 0.163181 | 0.320533 | 1.054414 | 5 | 5 | 5 |
| all6_current | 7284 | 0.170119 | 0.344418 | 1.160823 | 6 | 6 | 6 |

## 6. Q2-like by k

| k | candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | residual_lgb_s05_cap010 | 1821 | 0.200164 | 0.346971 | 1.131486 | 3 | 1 | 1 |
| 1 | simple_qavg_q2 | 1821 | 0.197038 | 0.353081 | 1.181688 | 1 | 3 | 4 |
| 1 | all6_current | 1821 | 0.216741 | 0.394669 | 1.371119 | 6 | 6 | 6 |
| 2 | residual_lgb_s05_cap010 | 1821 | 0.163295 | 0.319186 | 0.993204 | 2 | 1 | 1 |
| 2 | simple_qavg_q2 | 1821 | 0.162402 | 0.323546 | 1.038142 | 1 | 3 | 4 |
| 2 | all6_current | 1821 | 0.178439 | 0.366070 | 1.255724 | 6 | 6 | 6 |
| 3 | residual_lgb_s05_cap010 | 1821 | 0.136932 | 0.286524 | 0.940715 | 1 | 1 | 1 |
| 3 | simple_qavg_q2 | 1821 | 0.138381 | 0.290801 | 0.942537 | 4 | 3 | 3 |
| 3 | all6_current | 1821 | 0.147936 | 0.321928 | 1.014404 | 6 | 6 | 6 |
| 4 | residual_lgb_s05_cap010 | 1821 | 0.131539 | 0.261058 | 0.944798 | 2 | 1 | 1 |
| 4 | simple_qavg_q2 | 1821 | 0.128377 | 0.263036 | 0.972202 | 1 | 3 | 4 |
| 4 | all6_current | 1821 | 0.144331 | 0.295006 | 1.018258 | 6 | 6 | 6 |

## 7. Q2 residual vs simple bootstrap summary

| candidate_a | candidate_b | conditions | mean_p_a_better_MdAPE | mean_p_a_better_MAPE | mean_p_a_better_p95_APE | conditions_p_a_better_MdAPE_ge_0_90 | conditions_p_a_better_MAPE_ge_0_90 | conditions_p_a_better_p95_APE_ge_0_90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_lgb_s05_cap010 | simple_qavg_q2 | 12 | 0.487083 | 0.905833 | 0.722292 | 0 | 10 | 1 |

## 8. 최종 판단

{
  "recommended_candidate": "residual_lgb_s05_cap010",
  "candidate_formula": "lgbq_full_lean_avg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10)",
  "reason": [
    "Q2-like 운영 절단 검증에서 simple_qavg_q2보다 MdAPE/MAPE/p95가 모두 개선됨",
    "Q1-like에서는 simple_all6_q50_blend가 MdAPE/MAPE 우세이나 residual 후보가 p95를 크게 개선함",
    "운영 후보는 중앙오차만이 아니라 저이력 tail 안정성이 중요하므로 residual 후보를 우선 권장"
  ],
  "q1_tradeoff_vs_simple_all6_q50_blend": {
    "MdAPE_delta": 0.003235999999999989,
    "MAPE_delta": 0.0036069999999999713,
    "p95_delta": -0.018855000000000066
  },
  "q2_gain_vs_simple_qavg": {
    "MdAPE_delta": -0.0029990000000000017,
    "MAPE_delta": -0.00418099999999999,
    "p95_delta": -0.027336999999999945
  }
}

## 9. Config

{
  "experiment_id": "PP-WLITE-Q4",
  "experiment_slug": "PP-WLITE-Q4_quantile_final_comparison",
  "source_experiments": [
    "PP-WLITE-Q1_warm_lite_quantile_candidate_validation",
    "PP-WLITE-Q2_quantile_followup_truncation_validation",
    "PP-WLITE-Q3_quantile_residual_correction_validation"
  ],
  "n_boot": 800,
  "recommendation": {
    "recommended_candidate": "residual_lgb_s05_cap010",
    "candidate_formula": "lgbq_full_lean_avg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10)",
    "reason": [
      "Q2-like 운영 절단 검증에서 simple_qavg_q2보다 MdAPE/MAPE/p95가 모두 개선됨",
      "Q1-like에서는 simple_all6_q50_blend가 MdAPE/MAPE 우세이나 residual 후보가 p95를 크게 개선함",
      "운영 후보는 중앙오차만이 아니라 저이력 tail 안정성이 중요하므로 residual 후보를 우선 권장"
    ],
    "q1_tradeoff_vs_simple_all6_q50_blend": {
      "MdAPE_delta": 0.003235999999999989,
      "MAPE_delta": 0.0036069999999999713,
      "p95_delta": -0.018855000000000066
    },
    "q2_gain_vs_simple_qavg": {
      "MdAPE_delta": -0.0029990000000000017,
      "MAPE_delta": -0.00418099999999999,
      "p95_delta": -0.027336999999999945
    }
  },
  "prohibitions": [
    "0604 사용 금지"
  ]
}
