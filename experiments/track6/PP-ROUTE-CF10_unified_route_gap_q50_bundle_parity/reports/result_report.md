# PP-ROUTE-CF10 Unified route_gap_q50 bundle parity

```json
{
  "experiment_id": "PP-ROUTE-CF10",
  "check": "warm_lite_unified_route_gap_q50_bundle_replay_parity_vs_PP_ROUTE_CF9",
  "bundle": "models/track6/warm_lite_unified_route_gap_q50_v0.1_candidate",
  "n_reference": 1126,
  "n_replayed": 1126,
  "n_merged": 1126,
  "max_abs_log_diff": 5.329070518200751e-15,
  "mean_abs_log_diff": 5.521535468828487e-16,
  "n_route_mismatch": 0,
  "passed": true,
  "by_split": [
    {
      "split": "test",
      "n": 607,
      "MdAPE": 0.08640499173487216,
      "MAPE": 0.22359044054617647,
      "p95_APE": 0.758056358197116,
      "RMSE_log": 0.38003046113253736,
      "max_abs_log_diff": 3.552713678800501e-15,
      "mean_abs_log_diff": 5.589524815905236e-16,
      "n_route_mismatch": 0
    },
    {
      "split": "validation",
      "n": 519,
      "MdAPE": 0.07907501578161348,
      "MAPE": 0.1675208221151962,
      "p95_APE": 0.5607464999029876,
      "RMSE_log": 0.2984688839580961,
      "max_abs_log_diff": 5.329070518200751e-15,
      "mean_abs_log_diff": 5.442018062902502e-16,
      "n_route_mismatch": 0
    }
  ]
}
```
