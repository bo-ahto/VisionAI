"""Track 3 H11 — prediction interval / confidence confirm."""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h11_prediction_interval_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

COMMON_FEATURES = [
    "medium_category",
    "support_category",
    "depth_cm",
    "log_area",
    "estimated_ho",
    "orientation",
    "medium_ho_bucket",
    "aspect_ratio",
]
COMMON_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]
HISTORY_FEATURES = [
    "artist_works_log",
    "artist_ln_price_median",
    "artist_ln_price_mean",
    "artist_ln_price_iqr",
]


def add_base_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    medium = out["medium_category"].fillna("unknown").astype(str)
    out["ho_bucket"] = pd.cut(
        out["estimated_ho"],
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"],
    ).astype(str)
    out["medium_ho_bucket"] = medium + "_" + out["ho_bucket"]
    out["aspect_ratio"] = np.log(out["width_cm"] / out["height_cm"].replace(0, 1))
    return out


def build_artist_history(train: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    grouped = train.groupby(ARTIST_COL)[TARGET]
    q75 = grouped.quantile(0.75)
    q25 = grouped.quantile(0.25)
    hist = grouped.agg(["count", "median", "mean"]).rename(
        columns={"count": "artist_count", "median": "artist_ln_price_median", "mean": "artist_ln_price_mean"}
    )
    hist["artist_ln_price_iqr"] = q75 - q25
    global_values = {
        "artist_count": 0.0,
        "artist_ln_price_median": float(train[TARGET].median()),
        "artist_ln_price_mean": float(train[TARGET].mean()),
        "artist_ln_price_iqr": float((q75 - q25).median()),
    }
    return hist, global_values


def add_history(df: pd.DataFrame, hist: pd.DataFrame, global_values: dict) -> pd.DataFrame:
    out = df.copy()
    joined = out[[ARTIST_COL]].join(hist, on=ARTIST_COL)
    for col, default in global_values.items():
        out[col] = joined[col].fillna(default)
    out["artist_works_log"] = np.log1p(out["artist_count"])
    return out


def to_cat(df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> pd.DataFrame:
    out = df[features].copy()
    for col in cat_cols:
        if col in out.columns:
            out[col] = out[col].astype("category")
    return out


def train_lgb(train_df: pd.DataFrame, val_df: pd.DataFrame, features: list[str], cat_cols: list[str]) -> lgb.Booster:
    params = {
        "objective": "regression",
        "metric": "rmse",
        "learning_rate": 0.04,
        "num_leaves": 198,
        "min_data_in_leaf": 75,
        "feature_fraction": 0.987,
        "bagging_fraction": 0.978,
        "bagging_freq": 5,
        "reg_alpha": 0.36,
        "reg_lambda": 4.75,
        "verbose": -1,
        "seed": 42,
    }
    ds_tr = lgb.Dataset(to_cat(train_df, features, cat_cols), train_df[TARGET].values, categorical_feature=cat_cols)
    ds_val = lgb.Dataset(to_cat(val_df, features, cat_cols), val_df[TARGET].values, categorical_feature=cat_cols, reference=ds_tr)
    return lgb.train(params, ds_tr, num_boost_round=2000, valid_sets=[ds_val], callbacks=[lgb.early_stopping(30, verbose=False)])


def build_lad(features: list[str], cat_cols: list[str]) -> Pipeline:
    cat = [c for c in features if c in cat_cols]
    num = [c for c in features if c not in cat_cols]
    prep = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
            ("num", StandardScaler(), num),
        ]
    )
    return Pipeline([("prep", prep), ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def interval_metrics(y_true_ln: np.ndarray, pred_ln: np.ndarray, calib_resid: np.ndarray, coverage_target: float) -> dict:
    q = float(np.quantile(calib_resid, coverage_target))
    lo = pred_ln - q
    hi = pred_ln + q
    covered = (y_true_ln >= lo) & (y_true_ln <= hi)
    pred_price = np.exp(pred_ln)
    width_pct = (np.exp(hi) - np.exp(lo)) / pred_price
    ape = np.abs(np.exp(pred_ln) - np.exp(y_true_ln)) / np.exp(y_true_ln)
    narrow = width_pct <= np.median(width_pct)
    return {
        "target_coverage": float(coverage_target),
        "actual_coverage": float(np.mean(covered)),
        "median_width_pct": float(np.median(width_pct)),
        "median_ape": float(np.median(ape)),
        "narrow_half_coverage": float(np.mean(covered[narrow])),
        "wide_half_coverage": float(np.mean(covered[~narrow])),
        "narrow_half_median_width_pct": float(np.median(width_pct[narrow])),
        "wide_half_median_width_pct": float(np.median(width_pct[~narrow])),
    }


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")

    rng = np.random.default_rng(42)
    perm = rng.permutation(len(train_raw))
    cut_cal = int(len(train_raw) * 0.15)
    cal_raw = train_raw.iloc[perm[:cut_cal]].reset_index(drop=True)
    fit_raw = train_raw.iloc[perm[cut_cal:]].reset_index(drop=True)

    hist, global_values = build_artist_history(fit_raw)
    fit = add_history(add_base_features(fit_raw), hist, global_values)
    cal = add_history(add_base_features(cal_raw), hist, global_values)
    warm = add_history(add_base_features(warm_raw), hist, global_values)
    cold_fit = add_base_features(fit_raw)
    cold_cal = add_base_features(cal_raw)
    cold = add_base_features(cold_raw)

    warm_features = COMMON_FEATURES + [ARTIST_COL] + HISTORY_FEATURES
    warm_cat = COMMON_CAT + [ARTIST_COL]
    warm_model = train_lgb(fit, cal, warm_features, warm_cat)
    warm_cal_pred = warm_model.predict(to_cat(cal, warm_features, warm_cat))
    warm_pred = warm_model.predict(to_cat(warm, warm_features, warm_cat))
    warm_resid = np.abs(cal[TARGET].values - warm_cal_pred)

    cold_features = COMMON_FEATURES
    cold_cat = COMMON_CAT
    cold_model = build_lad(cold_features, cold_cat)
    cold_model.fit(cold_fit[cold_features], cold_fit[TARGET].values)
    cold_cal_pred = cold_model.predict(cold_cal[cold_features])
    cold_pred = cold_model.predict(cold[cold_features])
    cold_resid = np.abs(cold_cal[TARGET].values - cold_cal_pred)

    result = {
        "experiment_id": "H11_prediction_interval_confirm",
        "data": {
            "fit_rows": int(len(fit)),
            "calibration_rows": int(len(cal)),
            "test_warm_rows": int(len(warm)),
            "test_cold_rows": int(len(cold)),
        },
        "warm": {},
        "cold": {},
    }
    for target in [0.80, 0.90]:
        result["warm"][f"coverage_{int(target * 100)}"] = interval_metrics(
            warm[TARGET].values, warm_pred, warm_resid, target
        )
        result["cold"][f"coverage_{int(target * 100)}"] = interval_metrics(
            cold[TARGET].values, cold_pred, cold_resid, target
        )
    result["judgement"] = {
        "usable_as_auxiliary_output": bool(
            result["warm"]["coverage_80"]["actual_coverage"] >= 0.75
            and result["cold"]["coverage_80"]["actual_coverage"] >= 0.75
        ),
        "not_a_point_model_replacement": True,
        "reason": "intervals provide uncertainty context, but cold intervals are wide",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H11 prediction interval confirm")
    print(f"saved: {OUT_PATH}")
    for split in ["warm", "cold"]:
        for key, row in result[split].items():
            print(
                f"{split:<5} {key:<12} coverage={row['actual_coverage']:.3f} "
                f"width={row['median_width_pct']:.3f} median_ape={row['median_ape']:.4f}"
            )
    print(f"usable={result['judgement']['usable_as_auxiliary_output']}")


if __name__ == "__main__":
    main()
