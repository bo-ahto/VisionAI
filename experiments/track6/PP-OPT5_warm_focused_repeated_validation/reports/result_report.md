# PP-OPT5 Warm 집중 반복 검증

- 작성일: 2026-06-08 21:19
- 기준 후보: `hcoef_stable`
- 반복 검증: validation OOF 내부에서 `80`회씩 3가지 샘플링
- 샘플링 방식: confidence stratified rows, artist group holdout, row bootstrap
- 목적: PP-OPT4에서 가능성이 보인 후보가 반복 샘플에서도 안정적인지 확인한다.

## 1. 기준 성능

| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| test | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 |
| validation_oof | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 |

## 2. 후보군별 요약

| family | candidates | stable_validation_pass | test_diagnostic_pass | best_test_MAPE | best_test_p95_APE | mean_all3_rate |
| --- | --- | --- | --- | --- | --- | --- |
| catboost_artist_focus | 1152 | 909 | 161 | 0.2680 | 0.8100 | 0.7500 |
| xgboost_focus | 36 | 7 | 3 | 0.2721 | 0.8008 | 0.7917 |
| catboost_focus | 162 | 0 | 140 | 0.2682 | 0.8071 | 0.3250 |
| artist_focus | 8 | 0 | 0 | 0.2740 | 0.8140 | 0.1667 |
| source | 3 | 0 | 0 | 0.2748 | 0.8331 | 0.0000 |

## 3. 반복 검증 종합 순위

| candidate | family | mean_delta_MAPE | mean_delta_p95_APE | mean_MAPE_improve_rate | mean_p95_not_worse_rate | mean_all3_improve_rate | full_validation_delta_MAPE | full_validation_delta_p95_APE | test_delta_MAPE | test_delta_p95_APE | stable_validation_pass | test_diagnostic_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0038 | -0.0123 | 1.0000 | 0.8042 | 0.7500 | -0.0039 | -0.0138 | -0.0026 | 0.0065 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0036 | -0.0095 | 1.0000 | 0.8000 | 0.6792 | -0.0037 | -0.0108 | -0.0034 | 0.0046 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0035 | -0.0097 | 1.0000 | 0.8083 | 0.6875 | -0.0036 | -0.0108 | -0.0026 | 0.0046 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0034 | -0.0094 | 1.0000 | 0.7833 | 0.7208 | -0.0035 | -0.0108 | -0.0025 | 0.0041 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0038 | -0.0112 | 1.0000 | 0.7958 | 0.6833 | -0.0039 | -0.0109 | -0.0036 | 0.0063 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0035 | -0.0091 | 1.0000 | 0.7833 | 0.7208 | -0.0036 | -0.0108 | -0.0025 | 0.0041 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0036 | -0.0109 | 1.0000 | 0.8083 | 0.6792 | -0.0037 | -0.0110 | -0.0026 | 0.0052 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0037 | -0.0091 | 1.0000 | 0.7750 | 0.6625 | -0.0038 | -0.0108 | -0.0035 | 0.0046 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0037 | -0.0105 | 1.0000 | 0.8000 | 0.6625 | -0.0038 | -0.0109 | -0.0035 | 0.0052 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0038 | -0.0089 | 1.0000 | 0.7708 | 0.6542 | -0.0038 | -0.0108 | -0.0036 | 0.0046 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0040 | -0.0119 | 1.0000 | 0.7792 | 0.7292 | -0.0041 | -0.0138 | -0.0028 | 0.0065 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0037 | -0.0094 | 1.0000 | 0.7833 | 0.6750 | -0.0037 | -0.0108 | -0.0027 | 0.0046 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0041 | -0.0118 | 1.0000 | 0.7792 | 0.7250 | -0.0042 | -0.0138 | -0.0029 | 0.0065 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0035 | -0.0091 | 1.0000 | 0.7750 | 0.6667 | -0.0035 | -0.0108 | -0.0033 | 0.0041 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0036 | -0.0105 | 1.0000 | 0.7833 | 0.7042 | -0.0036 | -0.0110 | -0.0024 | 0.0048 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0035 | -0.0088 | 1.0000 | 0.7708 | 0.6667 | -0.0036 | -0.0108 | -0.0033 | 0.0041 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0040 | -0.0110 | 1.0000 | 0.7750 | 0.6917 | -0.0041 | -0.0109 | -0.0038 | 0.0063 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0036 | -0.0103 | 1.0000 | 0.7833 | 0.7042 | -0.0037 | -0.0110 | -0.0024 | 0.0048 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0039 | -0.0101 | 1.0000 | 0.7750 | 0.6500 | -0.0039 | -0.0109 | -0.0037 | 0.0052 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0036 | -0.0113 | 1.0000 | 0.7750 | 0.6875 | -0.0037 | -0.0109 | -0.0034 | 0.0059 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0041 | -0.0109 | 1.0000 | 0.7708 | 0.6875 | -0.0041 | -0.0110 | -0.0039 | 0.0063 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0038 | -0.0105 | 1.0000 | 0.7833 | 0.6625 | -0.0039 | -0.0110 | -0.0027 | 0.0052 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0039 | -0.0099 | 1.0000 | 0.7708 | 0.6417 | -0.0040 | -0.0110 | -0.0037 | 0.0052 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0037 | -0.0119 | 1.0000 | 0.7792 | 0.7500 | -0.0038 | -0.0138 | -0.0023 | 0.0061 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0037 | -0.0117 | 1.0000 | 0.7792 | 0.7500 | -0.0038 | -0.0138 | -0.0024 | 0.0061 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | -0.0037 | -0.0092 | 1.0000 | 0.7833 | 0.6792 | -0.0038 | -0.0108 | -0.0027 | 0.0046 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0036 | -0.0101 | 1.0000 | 0.7750 | 0.6417 | -0.0037 | -0.0109 | -0.0034 | 0.0048 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | -0.0037 | -0.0111 | 1.0000 | 0.7708 | 0.6833 | -0.0037 | -0.0110 | -0.0034 | 0.0059 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0036 | -0.0099 | 1.0000 | 0.7708 | 0.6292 | -0.0037 | -0.0110 | -0.0034 | 0.0048 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | -0.0039 | -0.0103 | 1.0000 | 0.7833 | 0.6708 | -0.0040 | -0.0110 | -0.0028 | 0.0052 | True | False |

## 4. 시나리오별 안정성 상위 후보

| candidate | family | scenario | mean_delta_MAPE | mean_delta_p95_APE | p90_delta_p95_APE | improve_MAPE_rate | p95_not_worse_rate | all3_improve_rate | stability_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgboost_focus__xgboost_low_only_diagnostic_cap0p08__route=low_only | xgboost_focus | artist_group_holdout | -0.0050 | -0.0139 | -0.0047 | 1.0000 | 0.9750 | 0.9250 | -0.0087 |
| xgboost_focus__xgboost_low_only_diagnostic_cap0p08__route=low_only | xgboost_focus | confidence_stratified_rows | -0.0049 | -0.0111 | -0.0012 | 1.0000 | 0.9375 | 0.8625 | -0.0083 |
| xgboost_focus__xgboost_low_only_diagnostic_cap0p08__route=low_only | xgboost_focus | row_bootstrap | -0.0051 | -0.0142 | 0.0000 | 0.9750 | 0.9375 | 0.5875 | -0.0074 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0040 | -0.0142 | 0.0020 | 1.0000 | 0.8750 | 0.8625 | -0.0071 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0040 | -0.0144 | 0.0020 | 1.0000 | 0.8750 | 0.8625 | -0.0070 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0037 | -0.0147 | 0.0012 | 1.0000 | 0.8750 | 0.8625 | -0.0069 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0040 | -0.0132 | 0.0021 | 1.0000 | 0.8500 | 0.8125 | -0.0068 |
| xgboost_focus__xgboost_low_only_diagnostic_cap0p05__route=low_only | xgboost_focus | artist_group_holdout | -0.0036 | -0.0121 | -0.0039 | 1.0000 | 0.9750 | 0.8125 | -0.0068 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0040 | -0.0134 | 0.0021 | 1.0000 | 0.8500 | 0.8125 | -0.0068 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0036 | -0.0142 | 0.0020 | 1.0000 | 0.8750 | 0.8750 | -0.0067 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0038 | -0.0126 | 0.0020 | 1.0000 | 0.8750 | 0.8125 | -0.0067 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0036 | -0.0144 | 0.0020 | 1.0000 | 0.8750 | 0.8750 | -0.0067 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0037 | -0.0137 | 0.0012 | 1.0000 | 0.8500 | 0.7875 | -0.0066 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0038 | -0.0129 | 0.0020 | 1.0000 | 0.8750 | 0.8000 | -0.0066 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0036 | -0.0133 | 0.0012 | 1.0000 | 0.8750 | 0.8000 | -0.0065 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0039 | -0.0121 | 0.0021 | 1.0000 | 0.8500 | 0.7625 | -0.0065 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0037 | -0.0113 | 0.0020 | 1.0000 | 0.8750 | 0.8125 | -0.0065 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0037 | -0.0112 | 0.0021 | 1.0000 | 0.8500 | 0.8000 | -0.0065 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0037 | -0.0109 | 0.0021 | 1.0000 | 0.8500 | 0.7875 | -0.0065 |
| xgboost_focus__xgboost_low_only_diagnostic_cap0p05__route=low_only | xgboost_focus | confidence_stratified_rows | -0.0035 | -0.0095 | 0.0000 | 1.0000 | 0.9250 | 0.7375 | -0.0065 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0038 | -0.0124 | 0.0021 | 1.0000 | 0.8500 | 0.7625 | -0.0065 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0037 | -0.0129 | 0.0012 | 1.0000 | 0.8500 | 0.7625 | -0.0065 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0036 | -0.0115 | 0.0020 | 1.0000 | 0.8750 | 0.8125 | -0.0065 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0040 | -0.0131 | 0.0047 | 1.0000 | 0.8500 | 0.8375 | -0.0064 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0036 | -0.0117 | 0.0012 | 1.0000 | 0.8500 | 0.7750 | -0.0064 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0035 | -0.0120 | 0.0012 | 1.0000 | 0.8750 | 0.8000 | -0.0064 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0035 | -0.0126 | 0.0020 | 1.0000 | 0.8750 | 0.8125 | -0.0064 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0036 | -0.0132 | 0.0021 | 1.0000 | 0.8500 | 0.7875 | -0.0063 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0035 | -0.0129 | 0.0020 | 1.0000 | 0.8750 | 0.8125 | -0.0063 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0034 | -0.0113 | 0.0020 | 1.0000 | 0.8750 | 0.8250 | -0.0063 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0034 | -0.0115 | 0.0020 | 1.0000 | 0.8750 | 0.8250 | -0.0063 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0036 | -0.0134 | 0.0021 | 1.0000 | 0.8500 | 0.7750 | -0.0063 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0043 | -0.0126 | 0.0049 | 1.0000 | 0.7375 | 0.7375 | -0.0062 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | artist_group_holdout | -0.0043 | -0.0123 | 0.0049 | 1.0000 | 0.7250 | 0.7250 | -0.0062 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0035 | -0.0109 | 0.0021 | 1.0000 | 0.8500 | 0.7875 | -0.0062 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p025 | catboost_artist_focus | artist_group_holdout | -0.0034 | -0.0112 | 0.0021 | 1.0000 | 0.8500 | 0.7875 | -0.0062 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0035 | -0.0124 | 0.0021 | 1.0000 | 0.8500 | 0.7375 | -0.0061 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0036 | -0.0121 | 0.0021 | 1.0000 | 0.8500 | 0.7125 | -0.0060 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | confidence_stratified_rows | -0.0037 | -0.0120 | 0.0028 | 1.0000 | 0.7750 | 0.7125 | -0.0060 |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=1p0__totalcap=0p03 | catboost_artist_focus | artist_group_holdout | -0.0038 | -0.0115 | 0.0047 | 1.0000 | 0.8500 | 0.7750 | -0.0060 |

## 5. Test 진단 통과 후보

| candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | stable_validation_pass | test_diagnostic_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025 | catboost_artist_focus | 0.1388 | 0.2690 | 0.8109 | -0.0000 | -0.0039 | 0.0046 | True | True |
| catboost_focus__tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0 | catboost_focus | 0.1388 | 0.2696 | 0.8100 | -0.0000 | -0.0034 | 0.0036 | False | True |
| catboost_focus__tier=low_guarded__qmult=same__cap=0p05__capprof=fixed__s=0p75 | catboost_focus | 0.1380 | 0.2703 | 0.8089 | -0.0008 | -0.0027 | 0.0025 | False | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025 | catboost_artist_focus | 0.1382 | 0.2691 | 0.8109 | -0.0006 | -0.0039 | 0.0046 | True | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p025 | catboost_artist_focus | 0.1383 | 0.2691 | 0.8110 | -0.0005 | -0.0039 | 0.0046 | True | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025 | catboost_artist_focus | 0.1388 | 0.2695 | 0.8103 | -0.0000 | -0.0035 | 0.0040 | True | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025 | catboost_artist_focus | 0.1382 | 0.2695 | 0.8103 | -0.0006 | -0.0035 | 0.0040 | True | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_balanced__cap=0p05__capprof=fixed__s=0p75 | catboost_focus | 0.1365 | 0.2710 | 0.8078 | -0.0023 | -0.0020 | 0.0014 | False | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p025 | catboost_artist_focus | 0.1384 | 0.2691 | 0.8110 | -0.0004 | -0.0039 | 0.0046 | True | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=0p5__totalcap=0p025 | catboost_artist_focus | 0.1382 | 0.2691 | 0.8110 | -0.0006 | -0.0039 | 0.0046 | False | True |
| catboost_focus__tier=confidence_weighted_apply__qmult=same__cap=0p05__capprof=fixed__s=1p0 | catboost_focus | 0.1380 | 0.2704 | 0.8088 | -0.0008 | -0.0026 | 0.0024 | False | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025 | catboost_artist_focus | 0.1379 | 0.2691 | 0.8110 | -0.0009 | -0.0039 | 0.0046 | False | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_conservative__cap=0p05__capprof=fixed__s=0p75 | catboost_focus | 0.1360 | 0.2713 | 0.8074 | -0.0028 | -0.0017 | 0.0011 | False | True |
| catboost_focus__tier=low_guarded__qmult=same__cap=0p05__capprof=qcap_balanced__s=0p75 | catboost_focus | 0.1380 | 0.2704 | 0.8088 | -0.0008 | -0.0026 | 0.0025 | False | True |
| catboost_focus__tier=same__qmult=qwidth_conservative__cap=0p05__capprof=qcap_balanced__s=0p75 | catboost_focus | 0.1377 | 0.2706 | 0.8085 | -0.0011 | -0.0023 | 0.0021 | False | True |
| catboost_focus__tier=same__qmult=qwidth_conservative__cap=0p05__capprof=fixed__s=0p75 | catboost_focus | 0.1377 | 0.2706 | 0.8085 | -0.0011 | -0.0023 | 0.0021 | False | True |
| catboost_focus__tier=low_guarded__qmult=same__cap=0p05__capprof=fixed__s=1p0 | catboost_focus | 0.1376 | 0.2698 | 0.8098 | -0.0012 | -0.0031 | 0.0034 | False | True |
| catboost_focus__tier=low_guarded__qmult=same__cap=0p03__capprof=fixed__s=0p75 | catboost_focus | 0.1380 | 0.2704 | 0.8089 | -0.0008 | -0.0026 | 0.0025 | False | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=0p5__totalcap=0p025 | catboost_artist_focus | 0.1380 | 0.2692 | 0.8110 | -0.0008 | -0.0038 | 0.0046 | False | True |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025 | catboost_artist_focus | 0.1368 | 0.2692 | 0.8110 | -0.0020 | -0.0038 | 0.0046 | False | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_conservative__cap=0p03__capprof=fixed__s=1p15 | catboost_focus | 0.1370 | 0.2709 | 0.8081 | -0.0018 | -0.0021 | 0.0017 | False | True |
| catboost_focus__tier=same__qmult=qwidth_conservative__cap=0p03__capprof=qcap_balanced__s=0p75 | catboost_focus | 0.1374 | 0.2707 | 0.8085 | -0.0014 | -0.0023 | 0.0021 | False | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_conservative__cap=0p03__capprof=qcap_balanced__s=1p15 | catboost_focus | 0.1370 | 0.2709 | 0.8081 | -0.0018 | -0.0021 | 0.0017 | False | True |
| catboost_focus__tier=same__qmult=qwidth_balanced__cap=0p05__capprof=fixed__s=0p75 | catboost_focus | 0.1383 | 0.2702 | 0.8093 | -0.0005 | -0.0028 | 0.0029 | False | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_balanced__cap=0p03__capprof=qcap_balanced__s=1p0 | catboost_focus | 0.1375 | 0.2707 | 0.8083 | -0.0013 | -0.0022 | 0.0020 | False | True |
| catboost_focus__tier=same__qmult=qwidth_conservative__cap=0p03__capprof=fixed__s=0p75 | catboost_focus | 0.1374 | 0.2707 | 0.8085 | -0.0014 | -0.0023 | 0.0021 | False | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_balanced__cap=0p05__capprof=qcap_balanced__s=0p75 | catboost_focus | 0.1365 | 0.2711 | 0.8078 | -0.0023 | -0.0019 | 0.0014 | False | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_balanced__cap=0p05__capprof=fixed__s=1p0 | catboost_focus | 0.1375 | 0.2708 | 0.8083 | -0.0013 | -0.0022 | 0.0020 | False | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_balanced__cap=0p03__capprof=qcap_balanced__s=1p15 | catboost_focus | 0.1384 | 0.2706 | 0.8087 | -0.0004 | -0.0024 | 0.0023 | False | True |
| catboost_focus__tier=low_guarded__qmult=qwidth_balanced__cap=0p03__capprof=fixed__s=1p0 | catboost_focus | 0.1375 | 0.2708 | 0.8083 | -0.0013 | -0.0022 | 0.0020 | False | True |

## 6. Test MAPE 상위 후보

| candidate | family | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | stable_validation_pass | test_diagnostic_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1378 | 0.2680 | 0.8137 | -0.0010 | -0.0050 | 0.0073 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1383 | 0.2680 | 0.8136 | -0.0005 | -0.0050 | 0.0072 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1396 | 0.2681 | 0.8137 | 0.0008 | -0.0049 | 0.0073 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1384 | 0.2681 | 0.8136 | -0.0004 | -0.0049 | 0.0072 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1379 | 0.2681 | 0.8134 | -0.0009 | -0.0049 | 0.0071 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1368 | 0.2682 | 0.8134 | -0.0020 | -0.0048 | 0.0071 | False | False |
| catboost_focus__tier=same__qmult=same__cap=0p05__capprof=fixed__s=1p15 | catboost_focus | 0.1397 | 0.2682 | 0.8203 | 0.0009 | -0.0047 | 0.0140 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1408 | 0.2683 | 0.8137 | 0.0020 | -0.0047 | 0.0073 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1376 | 0.2683 | 0.8138 | -0.0012 | -0.0047 | 0.0074 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1368 | 0.2683 | 0.8138 | -0.0020 | -0.0047 | 0.0074 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1376 | 0.2683 | 0.8138 | -0.0012 | -0.0047 | 0.0074 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gallery_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1368 | 0.2684 | 0.8138 | -0.0020 | -0.0046 | 0.0074 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1354 | 0.2684 | 0.8138 | -0.0034 | -0.0046 | 0.0074 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1371 | 0.2684 | 0.8138 | -0.0017 | -0.0046 | 0.0074 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1397 | 0.2684 | 0.8136 | 0.0009 | -0.0046 | 0.0072 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1368 | 0.2684 | 0.8138 | -0.0020 | -0.0046 | 0.0074 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1422 | 0.2684 | 0.8134 | 0.0034 | -0.0046 | 0.0070 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gallery_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1354 | 0.2685 | 0.8138 | -0.0034 | -0.0045 | 0.0074 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1388 | 0.2685 | 0.8132 | 0.0000 | -0.0045 | 0.0069 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1388 | 0.2685 | 0.8134 | -0.0000 | -0.0045 | 0.0071 | False | False |
| catboost_focus__tier=same__qmult=same__cap=0p05__capprof=fixed__s=1p0 | catboost_focus | 0.1391 | 0.2685 | 0.8200 | 0.0003 | -0.0045 | 0.0137 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1435 | 0.2685 | 0.8134 | 0.0047 | -0.0045 | 0.0070 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gallery_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1375 | 0.2685 | 0.8138 | -0.0013 | -0.0045 | 0.0074 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1396 | 0.2686 | 0.8138 | 0.0008 | -0.0044 | 0.0074 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_for_sale_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1378 | 0.2686 | 0.8138 | -0.0010 | -0.0044 | 0.0074 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=0p8__aw=0p75__totalcap=0p04 | catboost_artist_focus | 0.1412 | 0.2686 | 0.8132 | 0.0024 | -0.0044 | 0.0069 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p0__artist=am_h_birth_gen_gn_a01_c05_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1382 | 0.2686 | 0.8134 | -0.0006 | -0.0044 | 0.0071 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04 | catboost_artist_focus | 0.1410 | 0.2686 | 0.8131 | 0.0022 | -0.0044 | 0.0068 | True | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=0p75__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1391 | 0.2686 | 0.8131 | 0.0003 | -0.0044 | 0.0067 | False | False |
| combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_total_works_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p04 | catboost_artist_focus | 0.1365 | 0.2686 | 0.8132 | -0.0023 | -0.0044 | 0.0068 | False | False |

## 7. 해석

- 반복 검증에서 통과한 후보는 validation OOF의 여러 부분 샘플에서도 MAPE 개선이 재현된 후보로 본다.
- test_diagnostic_pass는 fixed test에서 MdAPE, MAPE가 개선되고 p95 악화가 0.005 이하인 후보를 뜻한다.
- CatBoost 계열은 MAPE 개선 폭이 크지만 p95가 흔들리는지 확인해야 한다.
- XGBoost medium-only 계열은 개선 폭은 작아도 p95 방어가 되는지 확인하는 후보로 둔다.
- 이 단계의 목적은 최종 모델 선택이 아니라, 다음 재학습/운영 후보를 줄이는 것이다.

## 8. 산출물

- `outputs/full_candidate_metrics.csv`
- `outputs/repeated_validation_detail.csv`
- `outputs/repeated_validation_summary.csv`
- `outputs/aggregate_candidate_stability.csv`
- `outputs/focused_candidate_predictions.csv`
- `reports/result_report.md`
- `reports/result_report.html`
- `artifacts/run_config.json`
