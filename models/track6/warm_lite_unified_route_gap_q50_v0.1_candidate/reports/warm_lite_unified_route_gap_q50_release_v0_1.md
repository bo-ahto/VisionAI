# Warm-lite unified route_gap_q50 v0.1 candidate release

- Frozen at: `2026-06-16T00:00:00+09:00`
- Artifact: `candidate_v0_1_warm_lite_unified_route_gap_q50`
- Selected candidate: `route_gap_q50`
- Gap threshold: `0.0252975144340901`
- Smoke test: passed
- Fixed replay feature store: `artifacts/fixed_replay_feature_store.csv`
- Bundle replay parity: CF9 validation/test 1,126 rows passed
- Default official 0.1v HTTP API parity: CF9 validation/test 1,126 rows passed

## Training Audit

```json
[
  {
    "seed": 20260612,
    "train_rows": 26914,
    "train_artists": 1773,
    "median_train_rows_per_artist": 5.0
  },
  {
    "seed": 20260613,
    "train_rows": 26914,
    "train_artists": 1773,
    "median_train_rows_per_artist": 5.0
  },
  {
    "seed": 20260614,
    "train_rows": 26914,
    "train_artists": 1773,
    "median_train_rows_per_artist": 5.0
  }
]
```

## Adoption Gate

This artifact has passed bundle replay parity and default official 0.1v HTTP API parity. The official 0.1v default Warm route policy is now `warm_lite_unified_route_gap_q50`: artists with at least one trusted same-artist price history row use the unified Warm-lite route_gap_q50 predictor. The previous split routing policy remains available for rollback with `PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY=current_split`.
