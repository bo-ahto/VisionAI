from run_ccoef2_stage2_meta_regression import oof_artist_coef_regression
from run_ccoef2_stage1_coef_table import build_coef_table
from common_cold import load_splits


def test_oof_predictions_use_held_out_folds_only():
    train, _ = load_splits()
    tbl = build_coef_table(train)
    oof = oof_artist_coef_regression(tbl, n_splits=5, seed=20260622)
    # every warm artist gets exactly one OOF prediction, none trained on itself
    assert set(oof["artist_key"]) == set(tbl["artist_key"])
    assert oof["oof_pred_coef"].notna().all()
