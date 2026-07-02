# PP-WCUT6 frozen Warm-lite component follow-up validation

## Purpose

Check whether the frozen Warm-lite v0.1 6-component average is clearly better than simpler component selections under the PP-WCUT2 k-truncation setup.

## Component metadata

component                  label feature_set  n_num_cols  uses_q25_q75  uses_unit_area_iqr
       c0 full_alpha1e-4_eps1.35        full          17          True                True
       c1 full_alpha1e-3_eps1.35        full          17          True                True
       c2 full_alpha1e-4_eps1.20        full          17          True                True
       c3 full_alpha1e-4_eps1.50        full          17          True                True
       c4 lean_alpha1e-4_eps1.35        lean          13         False               False
       c5 lean_alpha1e-3_eps1.50        lean          13         False               False

## Overall metrics

| candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE | delta_MAPE_minus_all6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all6_current | 7284 | 0.170119 | 0.344418 | 1.160823 | 1 | 3 | 6 | 0.000000 |
| c4_lean_default | 7284 | 0.171393 | 0.344445 | 1.175025 | 7 | 4 | 9 | 0.000027 |
| full4_only | 7284 | 0.171020 | 0.344909 | 1.152455 | 2 | 6 | 3 | 0.000491 |
| c2_full_low_epsilon | 7284 | 0.171385 | 0.344947 | 1.156169 | 6 | 7 | 5 | 0.000529 |

## Metrics by k

| k | candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | all6_current | 1821 | 0.216741 | 0.394669 | 1.371119 | 4 | 3 | 3 |
| 1 | c4_lean_default | 1821 | 0.208797 | 0.394698 | 1.368495 | 1 | 4 | 2 |
| 1 | c2_full_low_epsilon | 1821 | 0.217707 | 0.394927 | 1.356747 | 5 | 5 | 1 |
| 1 | full4_only | 1821 | 0.218461 | 0.394936 | 1.372109 | 7 | 6 | 4 |
| 2 | c4_lean_default | 1821 | 0.179727 | 0.365377 | 1.248185 | 7 | 3 | 1 |
| 2 | all6_current | 1821 | 0.178439 | 0.366070 | 1.255724 | 4 | 4 | 3 |
| 2 | full4_only | 1821 | 0.178345 | 0.366792 | 1.260449 | 3 | 6 | 7 |
| 2 | c2_full_low_epsilon | 1821 | 0.179643 | 0.367151 | 1.273123 | 6 | 9 | 9 |
| 3 | all6_current | 1821 | 0.147936 | 0.321928 | 1.014404 | 1 | 1 | 2 |
| 3 | c4_lean_default | 1821 | 0.148364 | 0.322153 | 1.026659 | 3 | 4 | 8 |
| 3 | c2_full_low_epsilon | 1821 | 0.147990 | 0.322658 | 1.027658 | 2 | 5 | 9 |
| 3 | full4_only | 1821 | 0.150709 | 0.322709 | 1.015529 | 5 | 6 | 5 |
| 4 | all6_current | 1821 | 0.144331 | 0.295006 | 1.018258 | 2 | 1 | 4 |
| 4 | c2_full_low_epsilon | 1821 | 0.144438 | 0.295052 | 1.015463 | 3 | 2 | 3 |
| 4 | full4_only | 1821 | 0.145291 | 0.295198 | 1.021050 | 4 | 4 | 8 |
| 4 | c4_lean_default | 1821 | 0.143043 | 0.295553 | 1.021262 | 1 | 7 | 9 |

## Bootstrap summary vs all6_current

| candidate | conditions | mean_p_candidate_better_all6_MdAPE | mean_p_candidate_better_all6_MAPE | mean_p_candidate_better_all6_p95_APE | conditions_p_candidate_better_all6_MdAPE_ge_0_90 | conditions_p_candidate_better_all6_MAPE_ge_0_90 | conditions_p_candidate_better_all6_p95_APE_ge_0_90 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all6_current | 12 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| c2_full_low_epsilon | 12 | 0.366875 | 0.301250 | 0.446250 | 0 | 0 | 0 |
| c4_lean_default | 12 | 0.534375 | 0.480000 | 0.443333 | 1 | 2 | 0 |
| full4_only | 12 | 0.325417 | 0.304583 | 0.530208 | 0 | 0 | 0 |

## Config

{
  "experiment_id": "PP-WCUT6",
  "eval_design": "Frozen Warm-lite v0.1 component comparison under PP-WCUT2 k-truncation setup.",
  "seeds": [
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
  "candidates": {
    "all6_current": [
      "c0",
      "c1",
      "c2",
      "c3",
      "c4",
      "c5"
    ],
    "full4_only": [
      "c0",
      "c1",
      "c2",
      "c3"
    ],
    "lean2_only": [
      "c4",
      "c5"
    ],
    "c0_full_default": [
      "c0"
    ],
    "c1_full_more_regularized": [
      "c1"
    ],
    "c2_full_low_epsilon": [
      "c2"
    ],
    "c3_full_high_epsilon": [
      "c3"
    ],
    "c4_lean_default": [
      "c4"
    ],
    "c5_lean_regularized_high_epsilon": [
      "c5"
    ]
  },
  "all6_current_metrics": {
    "MdAPE": 0.170119,
    "MAPE": 0.344418,
    "p95_APE": 1.160823
  },
  "best_candidate_by_metric": {
    "MdAPE": "all6_current",
    "MAPE": "c5_lean_regularized_high_epsilon",
    "p95_APE": "c0_full_default"
  },
  "n_boot": 400,
  "route_level_reference": "PP-WCUT2 remains the Warm-lite-vs-Cold route gate; PP-WCUT6 only validates component selection.",
  "prohibitions": [
    "0604 사용 금지"
  ]
}
