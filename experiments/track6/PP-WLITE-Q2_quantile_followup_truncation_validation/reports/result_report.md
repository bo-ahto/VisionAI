# PP-WLITE-Q2 Warm-lite Quantile 후속 절단 검증

## 1. 목적

PP-WLITE-Q1에서 개선 신호가 있었던 Quantile 보완 후보가 PP-WCUT6와 같은 k-truncation 구조에서도 유지되는지 확인한다.

## 2. 평가 설계

- 기준: 동결된 Warm-lite v0.1 Huber all6
- 후보: full train에서 학습한 LightGBM Quantile q50과 all6 blend
- 평가: warm fixed-test 607행에 대해 같은 작가 train 이력을 k=1~4로 절단
- 반복: truncation seed 3개, Quantile model seed 3개 평균
- 주의: Quantile 후보는 아직 운영 번들로 동결하지 않은 follow-up 후보

## 3. Overall metrics

| candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE | delta_MdAPE_minus_all6 | delta_MAPE_minus_all6 | delta_p95_APE_minus_all6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lgbq_full_lean_avg | 7284 | 0.157474 | 0.307616 | 1.027865 | 2 | 1 | 1 | -0.012645 | -0.036802 | -0.132958 |
| lgbq_lean_q50 | 7284 | 0.155882 | 0.308846 | 1.061158 | 1 | 2 | 4 | -0.014237 | -0.035572 | -0.099665 |
| lgbq_full_q50 | 7284 | 0.160414 | 0.309884 | 1.034175 | 3 | 3 | 2 | -0.009705 | -0.034534 | -0.126648 |
| all6_50_lgbq_full_50 | 7284 | 0.163181 | 0.320533 | 1.054414 | 4 | 4 | 3 | -0.006938 | -0.023885 | -0.106409 |
| all6_75_lgbq_full_25 | 7284 | 0.165791 | 0.331001 | 1.132204 | 5 | 5 | 5 | -0.004328 | -0.013417 | -0.028619 |
| all6_current | 7284 | 0.170119 | 0.344418 | 1.160823 | 6 | 6 | 6 | 0.000000 | 0.000000 | 0.000000 |

## 4. Metrics by k

| k | candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | lgbq_full_q50 | 1821 | 0.195071 | 0.356558 | 1.228966 | 1 | 3 | 4 |
| 1 | all6_50_lgbq_full_50 | 1821 | 0.203249 | 0.366988 | 1.209573 | 4 | 4 | 3 |
| 1 | all6_75_lgbq_full_25 | 1821 | 0.214286 | 0.378877 | 1.281283 | 5 | 5 | 5 |
| 1 | all6_current | 1821 | 0.216741 | 0.394669 | 1.371119 | 6 | 6 | 6 |
| 2 | lgbq_full_q50 | 1821 | 0.164608 | 0.325757 | 1.053832 | 3 | 3 | 2 |
| 2 | all6_50_lgbq_full_50 | 1821 | 0.170732 | 0.339283 | 1.167349 | 4 | 4 | 4 |
| 2 | all6_75_lgbq_full_25 | 1821 | 0.173956 | 0.351138 | 1.198780 | 5 | 5 | 5 |
| 2 | all6_current | 1821 | 0.178439 | 0.366070 | 1.255724 | 6 | 6 | 6 |
| 3 | lgbq_full_q50 | 1821 | 0.139968 | 0.295289 | 0.928814 | 3 | 3 | 1 |
| 3 | all6_50_lgbq_full_50 | 1821 | 0.145863 | 0.302598 | 0.977794 | 4 | 4 | 4 |
| 3 | all6_75_lgbq_full_25 | 1821 | 0.146777 | 0.311077 | 0.991935 | 5 | 5 | 5 |
| 3 | all6_current | 1821 | 0.147936 | 0.321928 | 1.014404 | 6 | 6 | 6 |
| 4 | lgbq_full_q50 | 1821 | 0.129434 | 0.261931 | 0.971361 | 3 | 1 | 3 |
| 4 | all6_50_lgbq_full_50 | 1821 | 0.134529 | 0.273264 | 0.967072 | 4 | 4 | 2 |
| 4 | all6_75_lgbq_full_25 | 1821 | 0.141028 | 0.282913 | 0.997869 | 5 | 5 | 5 |
| 4 | all6_current | 1821 | 0.144331 | 0.295006 | 1.018258 | 6 | 6 | 6 |

## 5. Bootstrap summary vs all6_current

| candidate | conditions | mean_p_candidate_better_all6_MdAPE | mean_p_candidate_better_all6_MAPE | mean_p_candidate_better_all6_p95_APE | conditions_p_candidate_better_all6_MdAPE_ge_0_90 | conditions_p_candidate_better_all6_MAPE_ge_0_90 | conditions_p_candidate_better_all6_p95_APE_ge_0_90 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all6_50_lgbq_full_50 | 12 | 0.790417 | 1.000000 | 0.860417 | 4 | 12 | 5 |
| all6_75_lgbq_full_25 | 12 | 0.656667 | 1.000000 | 0.806875 | 0 | 12 | 3 |
| lgbq_full_q50 | 12 | 0.847292 | 0.993333 | 0.826250 | 8 | 12 | 4 |

## 6. Quantile width diagnostics

| width_bin | n | width_min | width_max | all6_current_MdAPE | all6_current_MAPE | all6_current_p95_APE | lgbq_full_q50_MdAPE | lgbq_full_q50_MAPE | lgbq_full_q50_p95_APE | all6_50_lgbq_full_50_MdAPE | all6_50_lgbq_full_50_MAPE | all6_50_lgbq_full_50_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1_low | 1821 | 0.037647 | 0.434658 | 0.057440 | 0.135054 | 0.481003 | 0.046752 | 0.126780 | 0.477668 | 0.048615 | 0.128034 | 0.483326 |
| q2 | 1821 | 0.434726 | 0.676121 | 0.137010 | 0.220507 | 0.668413 | 0.125399 | 0.209012 | 0.672419 | 0.127924 | 0.211930 | 0.658730 |
| q3 | 1821 | 0.676172 | 1.037924 | 0.237702 | 0.417404 | 1.330480 | 0.211903 | 0.381853 | 1.185068 | 0.225800 | 0.395719 | 1.233788 |
| q4_high | 1821 | 1.038387 | 3.927779 | 0.351510 | 0.604709 | 2.034158 | 0.303104 | 0.521890 | 1.673801 | 0.327877 | 0.546451 | 1.781790 |

## 7. Config

{
  "experiment_id": "PP-WLITE-Q2",
  "experiment_slug": "PP-WLITE-Q2_quantile_followup_truncation_validation",
  "eval_design": "PP-WCUT6-equivalent frozen Warm-lite k-truncation follow-up.",
  "model_seeds": [
    20260612,
    20260613,
    20260614
  ],
  "truncation_seeds": [
    20260612,
    20260613,
    20260614
  ],
  "ks": [
    1,
    2,
    3,
    4
  ],
  "rows_per_condition": 607,
  "total_rows": 7284,
  "baseline": "frozen warm_lite_v0.1 all6_current",
  "quantile_model": "LightGBM objective=quantile, q10/q50/q90 full features, q50 lean features, seed-averaged",
  "candidates": [
    "all6_current",
    "lgbq_full_q50",
    "lgbq_lean_q50",
    "lgbq_full_lean_avg",
    "all6_75_lgbq_full_25",
    "all6_50_lgbq_full_50"
  ],
  "all6_current_metrics": {
    "MdAPE": 0.170119,
    "MAPE": 0.344418,
    "p95_APE": 1.160823
  },
  "best_candidate_by_metric": {
    "MdAPE": "lgbq_lean_q50",
    "MAPE": "lgbq_full_lean_avg",
    "p95_APE": "lgbq_full_lean_avg"
  },
  "n_boot": 400,
  "prohibitions": [
    "0604 사용 금지"
  ]
}
