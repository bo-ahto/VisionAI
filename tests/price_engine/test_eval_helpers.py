"""Tests for visionai.price_engine._eval_helpers."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from visionai.price_engine._eval_helpers import (
    CATEGORICAL_NORMALIZE_MAP,
    WARM_MIN_COUNT,
    apply_cell_calibration,
    cell_key,
    cell_keys,
    derive_target_market,
    label_encode_xgb,
    load_oof_predictions,
    normalize_categoricals,
    production_routed_predictions,
    warm_mask,
)


# ─── warm_mask ─────────────────────────────────────────────────────────


def test_warm_mask_default_threshold() -> None:
    groups = np.array(["a", "a", "a", "a", "a", "b", "b", "c"])
    m = warm_mask(groups)
    # a appears 5x → warm. b 2x → cold. c 1x → cold.
    assert m.tolist() == [True, True, True, True, True, False, False, False]


def test_warm_mask_custom_threshold() -> None:
    groups = np.array(["a", "a", "b", "b", "b"])
    m = warm_mask(groups, min_count=3)
    assert m.tolist() == [False, False, True, True, True]


def test_warm_mask_all_cold() -> None:
    groups = np.array(["a", "b", "c", "d"])
    m = warm_mask(groups)
    assert not m.any()


def test_warm_mask_constant_used() -> None:
    assert WARM_MIN_COUNT == 5


def test_warm_mask_empty() -> None:
    m = warm_mask(np.array([], dtype=str))
    assert m.shape == (0,)


# ─── derive_target_market ──────────────────────────────────────────────


def test_derive_target_market_int_array() -> None:
    arr = np.array([0, 1, 0, 1, 0])
    out = derive_target_market(arr)
    assert out.tolist() == ["online", "gallery", "online", "gallery", "online"]


def test_derive_target_market_pandas_series() -> None:
    s = pd.Series([1, 0, 1])
    out = derive_target_market(s)
    assert out.tolist() == ["gallery", "online", "gallery"]


def test_derive_target_market_bool_array() -> None:
    arr = np.array([True, False, True])
    out = derive_target_market(arr)
    assert out.tolist() == ["gallery", "online", "gallery"]


def test_derive_target_market_float_array() -> None:
    arr = np.array([1.0, 0.0, 1.0])
    out = derive_target_market(arr)
    assert out.tolist() == ["gallery", "online", "gallery"]


def test_derive_target_market_empty() -> None:
    out = derive_target_market(np.array([]))
    assert out.shape == (0,)


# ─── cell_key / cell_keys ──────────────────────────────────────────────


def test_cell_key_format() -> None:
    assert cell_key("artsy", "online") == "artsy_online"
    assert cell_key("saatchi", "gallery") == "saatchi_gallery"


def test_cell_keys_vectorized_matches_scalar() -> None:
    src = np.array(["artsy", "saatchi", "artsy"])
    tm = np.array(["online", "online", "gallery"])
    out = cell_keys(src, tm)
    assert out.tolist() == ["artsy_online", "saatchi_online", "artsy_gallery"]


def test_cell_keys_empty() -> None:
    out = cell_keys(np.array([]), np.array([]))
    assert out.shape == (0,)


# ─── apply_cell_calibration ────────────────────────────────────────────


def test_apply_cell_calibration_basic() -> None:
    pred = np.array([100.0, 200.0, 300.0])
    cell = np.array(["artsy_online", "saatchi_online", "artsy_gallery"])
    factors = {"artsy_online": 0.9, "saatchi_online": 1.1}
    out = apply_cell_calibration(pred, cell, factors)
    np.testing.assert_allclose(out, [90.0, 220.0, 300.0])


def test_apply_cell_calibration_unknown_cell_unchanged() -> None:
    """factors 에 정의 안 된 cell 은 그대로."""
    pred = np.array([100.0, 200.0])
    cell = np.array(["unknown_cell", "artsy_online"])
    factors = {"artsy_online": 0.9}
    out = apply_cell_calibration(pred, cell, factors)
    np.testing.assert_allclose(out, [100.0, 180.0])


def test_apply_cell_calibration_only_mask_restricts() -> None:
    """only_mask=True 행만 보정."""
    pred = np.array([100.0, 100.0, 100.0])
    cell = np.array(["artsy_online", "artsy_online", "artsy_online"])
    factors = {"artsy_online": 0.5}
    only_mask = np.array([True, False, True])
    out = apply_cell_calibration(pred, cell, factors, only_mask=only_mask)
    np.testing.assert_allclose(out, [50.0, 100.0, 50.0])


def test_apply_cell_calibration_does_not_mutate_input() -> None:
    pred = np.array([100.0, 200.0])
    pred_copy = pred.copy()
    cell = np.array(["artsy_online", "saatchi_online"])
    factors = {"artsy_online": 0.5}
    apply_cell_calibration(pred, cell, factors)
    np.testing.assert_allclose(pred, pred_copy)


def test_apply_cell_calibration_empty_factors() -> None:
    pred = np.array([100.0, 200.0])
    cell = np.array(["artsy_online", "saatchi_online"])
    out = apply_cell_calibration(pred, cell, {})
    np.testing.assert_allclose(out, pred)


# ─── normalize_categoricals ────────────────────────────────────────────


def test_normalize_categoricals_replaces_nan_none_empty() -> None:
    df = pd.DataFrame({
        "src": ["artsy", "saatchi", None, "", "nan", "None"],
        "other": [1, 2, 3, 4, 5, 6],
    })
    out = normalize_categoricals(df, ["src"])
    assert out["src"].tolist() == ["artsy", "saatchi", "unknown", "unknown", "unknown", "unknown"]
    assert out["other"].tolist() == [1, 2, 3, 4, 5, 6]  # 미지정 컬럼 변경 X


def test_normalize_categoricals_does_not_mutate_input() -> None:
    df = pd.DataFrame({"src": ["artsy", None]})
    df_copy = df.copy()
    normalize_categoricals(df, ["src"])
    pd.testing.assert_frame_equal(df, df_copy)


def test_normalize_categoricals_missing_column_skipped() -> None:
    df = pd.DataFrame({"x": [1, 2]})
    out = normalize_categoricals(df, ["nonexistent"])
    pd.testing.assert_frame_equal(out, df)


def test_normalize_categoricals_map_constant() -> None:
    assert CATEGORICAL_NORMALIZE_MAP == {"nan": "unknown", "None": "unknown", "": "unknown"}


# ─── label_encode_xgb ──────────────────────────────────────────────────


def test_label_encode_xgb_train_only_mapping_built() -> None:
    df_tr = pd.DataFrame({"cat": ["a", "b", "c"]})
    df_te = pd.DataFrame({"cat": ["a", "b", "d"]})  # d unseen
    enc_tr, enc_te, maps = label_encode_xgb(df_tr, df_te, categorical_features=["cat"])
    # mapping: a=0, b=1, c=2 (sorted)
    assert maps["cat"] == {"a": 0, "b": 1, "c": 2}
    assert enc_tr["cat"].tolist() == [0.0, 1.0, 2.0]
    # d → sentinel = len(mapping) = 3
    assert enc_te["cat"].tolist() == [0.0, 1.0, 3.0]


def test_label_encode_xgb_missing_categorical_skipped() -> None:
    df_tr = pd.DataFrame({"x": [1, 2]})
    df_te = pd.DataFrame({"x": [3, 4]})
    enc_tr, enc_te, maps = label_encode_xgb(df_tr, df_te, categorical_features=["nonexistent"])
    assert maps == {}
    pd.testing.assert_frame_equal(enc_tr, df_tr)
    pd.testing.assert_frame_equal(enc_te, df_te)


def test_label_encode_xgb_does_not_mutate_input() -> None:
    df_tr = pd.DataFrame({"cat": ["a", "b"]})
    df_te = pd.DataFrame({"cat": ["a", "c"]})
    df_tr_copy = df_tr.copy()
    df_te_copy = df_te.copy()
    label_encode_xgb(df_tr, df_te, categorical_features=["cat"])
    pd.testing.assert_frame_equal(df_tr, df_tr_copy)
    pd.testing.assert_frame_equal(df_te, df_te_copy)


def test_label_encode_xgb_handles_string_coercion() -> None:
    """numeric/mixed → str 강제 변환 후 매핑."""
    df_tr = pd.DataFrame({"cat": [1, 2, 3]})
    df_te = pd.DataFrame({"cat": [1, 4]})  # 4 unseen
    enc_tr, enc_te, maps = label_encode_xgb(df_tr, df_te, categorical_features=["cat"])
    # str map: '1', '2', '3' sorted
    assert maps["cat"] == {"1": 0, "2": 1, "3": 2}
    assert enc_te["cat"].tolist() == [0.0, 3.0]


# ─── load_oof_predictions ──────────────────────────────────────────────


def test_load_oof_predictions_round_trip(tmp_path: Path) -> None:
    arr1 = np.array([1.0, 2.0, 3.0])
    arr2 = np.array([[1, 2], [3, 4]])
    out = tmp_path / "oof.npz"
    np.savez(out, y=arr1, mat=arr2)
    loaded = load_oof_predictions(out)
    np.testing.assert_array_equal(loaded["y"], arr1)
    np.testing.assert_array_equal(loaded["mat"], arr2)


def test_load_oof_predictions_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_oof_predictions(tmp_path / "nonexistent.npz")


# ─── production_routed_predictions ─────────────────────────────────────


def test_production_routed_predictions_warm_uses_xgb_no_cal() -> None:
    cb_full = np.log(np.array([100.0, 200.0, 300.0]))  # ln(price)
    xgb_warm = np.log(np.array([110.0, 220.0]))  # warm only (rows 0, 2)
    warm_mask_full = np.array([True, False, True])
    source = np.array(["artsy", "saatchi", "artsy"])
    tm = np.array(["online", "online", "gallery"])
    # cold cells: artsy_online, saatchi_online; cold factor 0.5 should NOT apply to warm
    factors = {"saatchi_online": 0.5}
    out = production_routed_predictions(
        cb_pred_ln_full=cb_full, xgb_pred_ln_warm=xgb_warm,
        warm_mask_full=warm_mask_full, source=source, target_market=tm,
        cold_factors=factors,
    )
    # row 0: warm → 110 (XGB, no cal)
    # row 1: cold + saatchi_online → 200 * 0.5 = 100
    # row 2: warm → 220 (XGB, no cal)
    np.testing.assert_allclose(out, [110.0, 100.0, 220.0])


def test_production_routed_predictions_cold_only_factors() -> None:
    """cold path 만 factor 적용 — same-cell warm 행은 변하지 않음."""
    cb_full = np.log(np.array([100.0, 100.0]))
    xgb_warm = np.log(np.array([100.0]))
    warm_mask_full = np.array([True, False])
    source = np.array(["artsy", "artsy"])
    tm = np.array(["online", "online"])
    factors = {"artsy_online": 0.5}
    out = production_routed_predictions(
        cb_pred_ln_full=cb_full, xgb_pred_ln_warm=xgb_warm,
        warm_mask_full=warm_mask_full, source=source, target_market=tm,
        cold_factors=factors,
    )
    # warm row uses XGB exp = 100, cold row gets 100 * 0.5 = 50
    np.testing.assert_allclose(out, [100.0, 50.0])


def test_production_routed_predictions_warm_count_mismatch_raises() -> None:
    cb_full = np.log(np.array([100.0, 200.0, 300.0]))
    xgb_warm_wrong = np.log(np.array([110.0]))  # warm_mask says 2 warm, but only 1 here
    warm_mask_full = np.array([True, False, True])
    with pytest.raises(ValueError, match="warm_mask sum"):
        production_routed_predictions(
            cb_pred_ln_full=cb_full, xgb_pred_ln_warm=xgb_warm_wrong,
            warm_mask_full=warm_mask_full,
            source=np.array(["a", "b", "c"]),
            target_market=np.array(["online"] * 3),
            cold_factors={},
        )


def test_production_routed_predictions_all_cold() -> None:
    cb_full = np.log(np.array([100.0, 200.0]))
    xgb_warm: np.ndarray = np.array([])
    warm_mask_full = np.array([False, False])
    source = np.array(["artsy", "saatchi"])
    tm = np.array(["online", "online"])
    factors = {"artsy_online": 0.9, "saatchi_online": 1.1}
    out = production_routed_predictions(
        cb_pred_ln_full=cb_full, xgb_pred_ln_warm=xgb_warm,
        warm_mask_full=warm_mask_full, source=source, target_market=tm,
        cold_factors=factors,
    )
    np.testing.assert_allclose(out, [100.0 * 0.9, 200.0 * 1.1])


def test_production_routed_predictions_all_warm_no_cal() -> None:
    cb_full = np.log(np.array([100.0, 200.0]))
    xgb_warm = np.log(np.array([99.0, 199.0]))
    warm_mask_full = np.array([True, True])
    out = production_routed_predictions(
        cb_pred_ln_full=cb_full, xgb_pred_ln_warm=xgb_warm,
        warm_mask_full=warm_mask_full,
        source=np.array(["artsy", "saatchi"]),
        target_market=np.array(["online", "online"]),
        cold_factors={"artsy_online": 0.5, "saatchi_online": 0.5},
    )
    # warm 모두 XGB exp 사용, factor 영향 없음
    np.testing.assert_allclose(out, [99.0, 199.0])
