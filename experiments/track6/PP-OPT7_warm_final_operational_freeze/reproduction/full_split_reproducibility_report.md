# PP-OPT7 Warm Full Split Reproducibility Audit

- created_at: 2026-06-09T10:29:28
- validation split: `data/track6_split_with_year_type_edition_size_artist_name/track6_val_warm.csv`
- fixed test split: `data/track6_split_with_year_type_edition_size_artist_name/track6_test_warm.csv`
- prediction table: `experiments/track6/PP-OPT7_warm_final_operational_freeze/outputs/final_candidate_predictions.csv`
- reported metrics: `experiments/track6/PP-OPT7_warm_final_operational_freeze/outputs/final_candidate_metrics.csv`

## Scope

This audit is not the high-confidence 100-row submission benchmark.
It checks the full base Warm validation/test split.

The current PP-OPT7 prediction table is an upstream-frozen feature/prediction
table. It can reproduce the full-split metrics exactly, but the raw
`track6_train.csv` alone is not enough to retrain the whole PP-SVC3/HCOEF/L10/
CatBoost/artist-correction chain from scratch without running the upstream
experiment scripts and their artifacts.

## Final Candidate Full Split Metrics

| model_id | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_MdAPE | delta_MAPE | delta_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warm_catboost_artist_qcap_risk_strict_v1 | test | 607 | 0.136892565899 | 0.271394888012 | 0.808129982713 | 0.398341481111 | 0.779242174629 | 0.883031301483 | -0.001910778420 | -0.001593785747 | 0.001763861658 |
| warm_catboost_artist_qcap_risk_strict_v1 | validation_oof | 519 | 0.125923017430 | 0.207023061669 | 0.636594786636 | 0.324132886426 | 0.782273603083 | 0.911368015414 | -0.000069570147 | -0.001183292163 | -0.011353191644 |

## Row Coverage Audit

| model_id | eval_split | expected_rows | prediction_rows | unique_prediction_row_ids | missing_from_predictions | extra_in_predictions | row_id_set_match |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_hcoef_stable | test | 607 | 607 | 607 | 0 | 0 | True |
| warm_catboost_artist_qcap_risk_strict_v1 | test | 607 | 607 | 607 | 0 | 0 | True |
| baseline_hcoef_stable | validation_oof | 519 | 519 | 519 | 0 | 0 | True |
| warm_catboost_artist_qcap_risk_strict_v1 | validation_oof | 519 | 519 | 519 | 0 | 0 | True |

## All Recomputed Metrics

| model_id | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | delta_MdAPE | delta_MAPE | delta_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_hcoef_stable | test | 607 | 0.138803344318 | 0.272988673759 | 0.806366121055 | 0.398821613075 | 0.774299835255 | 0.881383855025 | 0.000000000000 | 0.000000000000 | 0.000000000000 |
| warm_catboost_artist_qcap_risk_strict_v1 | test | 607 | 0.136892565899 | 0.271394888012 | 0.808129982713 | 0.398341481111 | 0.779242174629 | 0.883031301483 | -0.001910778420 | -0.001593785747 | 0.001763861658 |
| baseline_hcoef_stable | validation_oof | 519 | 0.125992587577 | 0.208206353831 | 0.647947978281 | 0.325184819666 | 0.778420038536 | 0.911368015414 | 0.000000000000 | 0.000000000000 | 0.000000000000 |
| warm_catboost_artist_qcap_risk_strict_v1 | validation_oof | 519 | 0.125923017430 | 0.207023061669 | 0.636594786636 | 0.324132886426 | 0.782273603083 | 0.911368015414 | -0.000069570147 | -0.001183292163 | -0.011353191644 |

## Difference From Reported Metrics

| model_id | eval_split | diff_n | diff_MdAPE | diff_MAPE | diff_p95_APE | diff_RMSE_log | diff_delta_MdAPE | diff_delta_MAPE | diff_delta_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_hcoef_stable | test | 0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 |
| warm_catboost_artist_qcap_risk_strict_v1 | test | 0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | -0.000000000000 | -0.000000000000 | 0.000000000000 |
| baseline_hcoef_stable | validation_oof | 0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 |
| warm_catboost_artist_qcap_risk_strict_v1 | validation_oof | 0 | 0.000000000000 | -0.000000000000 | -0.000000000000 | 0.000000000000 | 0.000000000000 | -0.000000000000 | -0.000000000000 |
