# PP-WLITE-GUARD2 locked Warm-lite guard validation

## Locked Policy

If `component_spread >= 0.005` and `c2_single <= all6_current`, use `0.50 * all6_current + 0.50 * c2_single`; otherwise keep `all6_current`.

## Overall Metrics

| dataset | candidate | n | changed_rate | MdAPE | MAPE | p95_APE | delta_MdAPE_minus_all6 | delta_MAPE_minus_all6 | delta_p95_APE_minus_all6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-WCUT5_real_low_history | all6_current | 1947 | 0.000000 | 0.109227 | 0.286566 | 0.876470 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT5_real_low_history | c2_single | 1947 | 1.000000 | 0.108869 | 0.285808 | 0.873016 | -0.000358 | -0.000758 | -0.003454 |
| PP-WCUT5_real_low_history | full4_only | 1947 | 1.000000 | 0.109365 | 0.286545 | 0.873505 | 0.000137 | -0.000021 | -0.002964 |
| PP-WCUT5_real_low_history | guard_c2_blend_spread005 | 1947 | 0.402671 | 0.108662 | 0.285795 | 0.874871 | -0.000565 | -0.000771 | -0.001599 |
| PP-WCUT6_frozen_truncation | all6_current | 7284 | 0.000000 | 0.170119 | 0.344418 | 1.160823 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT6_frozen_truncation | c2_single | 7284 | 1.000000 | 0.171385 | 0.344947 | 1.156169 | 0.001266 | 0.000529 | -0.004653 |
| PP-WCUT6_frozen_truncation | full4_only | 7284 | 1.000000 | 0.171020 | 0.344909 | 1.152455 | 0.000901 | 0.000490 | -0.008368 |
| PP-WCUT6_frozen_truncation | guard_c2_blend_spread005 | 7284 | 0.425316 | 0.169968 | 0.343915 | 1.147363 | -0.000151 | -0.000504 | -0.013460 |

## Metrics By k

| dataset | k | candidate | n | changed_rate | MdAPE | MAPE | p95_APE | delta_MdAPE_minus_all6 | delta_MAPE_minus_all6 | delta_p95_APE_minus_all6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-WCUT5_real_low_history | 1 | all6_current | 621 | 0.000000 | 0.120677 | 0.341476 | 0.955881 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT5_real_low_history | 1 | guard_c2_blend_spread005 | 621 | 0.433172 | 0.121219 | 0.340268 | 0.955973 | 0.000543 | -0.001208 | 0.000093 |
| PP-WCUT5_real_low_history | 2 | all6_current | 489 | 0.000000 | 0.118375 | 0.270704 | 0.877912 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT5_real_low_history | 2 | guard_c2_blend_spread005 | 489 | 0.386503 | 0.118375 | 0.270462 | 0.876482 | 0.000000 | -0.000242 | -0.001430 |
| PP-WCUT5_real_low_history | 3 | all6_current | 324 | 0.000000 | 0.105981 | 0.254102 | 0.714172 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT5_real_low_history | 3 | guard_c2_blend_spread005 | 324 | 0.376543 | 0.107127 | 0.252524 | 0.721927 | 0.001145 | -0.001578 | 0.007755 |
| PP-WCUT5_real_low_history | 4 | all6_current | 513 | 0.000000 | 0.092263 | 0.255719 | 0.788372 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT5_real_low_history | 4 | guard_c2_blend_spread005 | 513 | 0.397661 | 0.091555 | 0.255482 | 0.788027 | -0.000708 | -0.000237 | -0.000345 |
| PP-WCUT6_frozen_truncation | 1 | all6_current | 1821 | 0.000000 | 0.216741 | 0.394669 | 1.371119 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT6_frozen_truncation | 1 | guard_c2_blend_spread005 | 1821 | 0.511807 | 0.216994 | 0.394132 | 1.367034 | 0.000253 | -0.000537 | -0.004084 |
| PP-WCUT6_frozen_truncation | 2 | all6_current | 1821 | 0.000000 | 0.178439 | 0.366070 | 1.255724 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT6_frozen_truncation | 2 | guard_c2_blend_spread005 | 1821 | 0.420648 | 0.178916 | 0.365626 | 1.255724 | 0.000477 | -0.000444 | 0.000000 |
| PP-WCUT6_frozen_truncation | 3 | all6_current | 1821 | 0.000000 | 0.147936 | 0.321928 | 1.014404 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT6_frozen_truncation | 3 | guard_c2_blend_spread005 | 1821 | 0.393191 | 0.147997 | 0.321427 | 1.014404 | 0.000061 | -0.000501 | 0.000000 |
| PP-WCUT6_frozen_truncation | 4 | all6_current | 1821 | 0.000000 | 0.144331 | 0.295006 | 1.018258 | 0.000000 | 0.000000 | 0.000000 |
| PP-WCUT6_frozen_truncation | 4 | guard_c2_blend_spread005 | 1821 | 0.375618 | 0.144794 | 0.294474 | 1.018258 | 0.000462 | -0.000532 | 0.000000 |

## Condition Summary By seed/k

| dataset | candidate | conditions | conditions_improved_MdAPE | conditions_tied_MdAPE | conditions_worse_MdAPE | max_regression_MdAPE | mean_delta_MdAPE | conditions_improved_MAPE | conditions_tied_MAPE | conditions_worse_MAPE | max_regression_MAPE | mean_delta_MAPE | conditions_improved_p95_APE | conditions_tied_p95_APE | conditions_worse_p95_APE | max_regression_p95_APE | mean_delta_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-WCUT5_real_low_history | guard_c2_blend_spread005 | 12 | 6 | 4 | 2 | 0.002730 | -0.000492 | 12 | 0 | 0 | -0.000062 | -0.000817 | 7 | 3 | 2 | 0.000945 | -0.001936 |
| PP-WCUT6_frozen_truncation | guard_c2_blend_spread005 | 12 | 4 | 2 | 6 | 0.001966 | 0.000158 | 12 | 0 | 0 | -0.000245 | -0.000504 | 7 | 4 | 1 | 0.000008 | -0.002746 |

## Artist-cluster Bootstrap

| dataset | candidate | n_boot | p_candidate_better_all6_MdAPE | p_candidate_worse_all6_MdAPE | p_tie_MdAPE | p_candidate_better_all6_MAPE | p_candidate_worse_all6_MAPE | p_tie_MAPE | p_candidate_better_all6_p95_APE | p_candidate_worse_all6_p95_APE | p_tie_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-WCUT5_real_low_history | guard_c2_blend_spread005 | 600 | 0.566667 | 0.280000 | 0.153333 | 1.000000 | 0.000000 | 0.000000 | 0.555000 | 0.251667 | 0.193333 |
| PP-WCUT6_frozen_truncation | guard_c2_blend_spread005 | 600 | 0.303333 | 0.633333 | 0.063333 | 1.000000 | 0.000000 | 0.000000 | 0.726667 | 0.031667 | 0.241667 |

## Config

{
  "experiment_id": "PP-WLITE-GUARD2",
  "locked_candidate": "guard_c2_blend_spread005",
  "formula": "if component_spread >= 0.005 and c2_single <= all6_current then 0.5*all6_current + 0.5*c2_single else all6_current",
  "sources": {
    "PP-WCUT5_real_low_history": "experiments/track6/PP-WCUT5_warm_lite_huber_component_ablation/outputs/predictions_all_seeds.csv",
    "PP-WCUT6_frozen_truncation": "experiments/track6/PP-WCUT6_warm_lite_candidate_followup_validation/outputs/predictions_all_conditions.csv"
  },
  "n_boot": 600,
  "status": "offline locked-policy validation; not yet adopted into runtime artifact"
}

## Full seed/k table

                   dataset     seed  k                candidate   n    MdAPE     MAPE  p95_APE  changed_rate  delta_MdAPE_minus_all6  delta_MAPE_minus_all6  delta_p95_APE_minus_all6
 PP-WCUT5_real_low_history 20260612  1 guard_c2_blend_spread005 207 0.123407 0.319105 0.877323      0.415459                0.002730              -0.001520                 -0.001116
 PP-WCUT5_real_low_history 20260612  2 guard_c2_blend_spread005 163 0.111694 0.246051 0.871359      0.392638               -0.000188              -0.000212                 -0.000422
 PP-WCUT5_real_low_history 20260612  3 guard_c2_blend_spread005 108 0.076917 0.306774 0.658473      0.342593               -0.001321              -0.004474                  0.000000
 PP-WCUT5_real_low_history 20260612  4 guard_c2_blend_spread005 171 0.087719 0.249505 0.968443      0.362573                0.000000              -0.000146                 -0.001262
 PP-WCUT5_real_low_history 20260613  1 guard_c2_blend_spread005 207 0.113961 0.396184 1.088507      0.473430               -0.002710              -0.001746                  0.000000
 PP-WCUT5_real_low_history 20260613  2 guard_c2_blend_spread005 163 0.125857 0.329609 0.827853      0.423313                0.000000              -0.000288                 -0.016124
 PP-WCUT5_real_low_history 20260613  3 guard_c2_blend_spread005 108 0.131946 0.232502 0.643966      0.425926                0.000396              -0.000086                 -0.002730
 PP-WCUT5_real_low_history 20260613  4 guard_c2_blend_spread005 171 0.108662 0.271541 0.620941      0.421053               -0.000565              -0.000062                  0.000000
 PP-WCUT5_real_low_history 20260614  1 guard_c2_blend_spread005 207 0.121219 0.305514 0.898704      0.410628                0.000000              -0.000360                  0.000163
 PP-WCUT5_real_low_history 20260614  2 guard_c2_blend_spread005 163 0.120305 0.235725 0.892577      0.343558                0.000000              -0.000225                 -0.000104
 PP-WCUT5_real_low_history 20260614  3 guard_c2_blend_spread005 108 0.102082 0.218295 0.778206      0.361111               -0.002986              -0.000176                 -0.002588
 PP-WCUT5_real_low_history 20260614  4 guard_c2_blend_spread005 171 0.086182 0.245399 0.745793      0.409357               -0.001257              -0.000504                  0.000945
PP-WCUT6_frozen_truncation 20260612  1 guard_c2_blend_spread005 607 0.200363 0.381543 1.598670      0.507414                0.000982              -0.000245                 -0.004051
PP-WCUT6_frozen_truncation 20260612  2 guard_c2_blend_spread005 607 0.161876 0.308970 1.087833      0.433278                0.000745              -0.000383                  0.000000
PP-WCUT6_frozen_truncation 20260612  3 guard_c2_blend_spread005 607 0.134727 0.303568 1.041888      0.378913               -0.000719              -0.000485                 -0.000135
PP-WCUT6_frozen_truncation 20260612  4 guard_c2_blend_spread005 607 0.156771 0.291688 1.043740      0.418451               -0.001844              -0.000655                 -0.001672
PP-WCUT6_frozen_truncation 20260613  1 guard_c2_blend_spread005 607 0.227610 0.416482 1.192120      0.532125                0.000000              -0.000584                 -0.008404
PP-WCUT6_frozen_truncation 20260613  2 guard_c2_blend_spread005 607 0.191791 0.425806 1.365640      0.400329               -0.001067              -0.000440                 -0.001469
PP-WCUT6_frozen_truncation 20260613  3 guard_c2_blend_spread005 607 0.159499 0.350009 1.005456      0.395387                0.001162              -0.000541                  0.000000
PP-WCUT6_frozen_truncation 20260613  4 guard_c2_blend_spread005 607 0.133660 0.282341 0.997844      0.362438                0.001966              -0.000398                  0.000000
PP-WCUT6_frozen_truncation 20260614  1 guard_c2_blend_spread005 607 0.218787 0.384373 1.223207      0.495881                0.000968              -0.000782                 -0.003917
PP-WCUT6_frozen_truncation 20260614  2 guard_c2_blend_spread005 607 0.189361 0.362101 1.310363      0.428336                0.000000              -0.000509                 -0.013308
PP-WCUT6_frozen_truncation 20260614  3 guard_c2_blend_spread005 607 0.150106 0.310705 0.999645      0.405272                0.000143              -0.000476                  0.000000
PP-WCUT6_frozen_truncation 20260614  4 guard_c2_blend_spread005 607 0.136692 0.309392 1.005302      0.345964               -0.000443              -0.000542                  0.000008
