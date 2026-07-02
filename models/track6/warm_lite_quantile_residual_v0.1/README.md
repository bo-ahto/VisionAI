# Warm-lite Quantile residual v0.1

Official v0.1 API Warm-lite route bundle for same-artist price history 1~4.

- Selected candidate: `qavg_lgbres_s05_cap010`
- Formula: `lgbq_full_lean_avg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10)`
- Freeze script: `python3 scripts/track6/freeze_warm_lite_quantile_residual_artifact_v0_1.py`
- Predictor: `predict/predict_warm_lite_quantile_residual_v0_1.py`
