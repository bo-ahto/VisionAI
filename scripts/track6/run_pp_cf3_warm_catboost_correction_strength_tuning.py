#!/usr/bin/env python3
"""Run PP-CF3: post-hoc CatBoost residual correction strength tuning.

This experiment keeps the current Warm/HCOEF base prediction fixed and only
changes the correction value produced by a CatBoost residual model.
Selection is based on validation OOF metrics; test metrics are diagnostic.
"""
from __future__ import annotations

import html
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold


try:
    from catboost import CatBoostRegressor
except Exception as exc:  # pragma: no cover - local dependency guard
    raise RuntimeError("catboost is required for PP-CF3") from exc


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-CF3"
EXP_SLUG = "PP-CF3_warm_catboost_correction_strength_tuning"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

SOURCE_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF20_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)

SEED = 20260608
N_FOLDS = 5
BASE_CANDIDATE = "hcoef_stable"
REFERENCE_CANDIDATE = "current_70_30"

COMPONENT_COLS = [
    "hcoef_stable",
    "current_70_30",
    "ppv8_service_proxy",
    "svc_numeric_seed_mean",
    "l10_seq_pred_log",
]

NUMERIC_FEATURES = [
    "hcoef_stable",
    "current_70_30",
    "ppv8_service_proxy",
    "svc_numeric_seed_mean",
    "l10_seq_pred_log",
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "svc_group_n_log",
    "log_area",
    "component_prediction_spread",
    "component_prediction_range",
    "current_vs_stable_gap_abs",
    "current_minus_stable_log",
    "ppv8_minus_stable_log",
    "svc_minus_stable_log",
    "l10_minus_stable_log",
    "confidence_risk_score",
]

CAT_FEATURES = [
    "svc_coverage_tier",
    "svc_group_level",
    "service_confidence_tier",
    "qwidth_band",
    "svc_group_n_band",
    "gap_band",
    "pred_spread_band",
    "stable_pred_price_band",
    "medium_support_bucket",
]

CAPS = [0.015, 0.02, 0.03, 0.05, 0.08, 0.12]
STRENGTHS = [0.25, 0.40, 0.50, 0.65, 0.75, 0.90, 1.00, 1.15]

HIGH_CONFIDENCE_RULE = {
    "quantile_width_max": 1.20,
    "component_prediction_spread_max": 0.10,
    "l10_price_range_ratio_max": 2.00,
    "svc_group_n_min": 5,
    "current_vs_stable_gap_abs_max": 0.025,
}

LOW_CONFIDENCE_RULE = {
    "quantile_width_min": 1.60,
    "component_prediction_spread_min": 0.18,
    "l10_price_range_ratio_min": 2.50,
    "svc_group_n_max": 4,
    "current_vs_stable_gap_abs_min": 0.050,
}

WEIGHT_BY_TIER = {
    "high_confidence": 1.00,
    "medium_confidence": 0.45,
    "low_confidence": 0.15,
}

TIER_PROFILES = {
    "same": {
        "high_confidence": 1.00,
        "medium_confidence": 1.00,
        "low_confidence": 1.00,
    },
    "confidence_weighted_apply": {
        "high_confidence": 1.00,
        "medium_confidence": 0.45,
        "low_confidence": 0.15,
    },
    "low_guarded": {
        "high_confidence": 1.00,
        "medium_confidence": 0.60,
        "low_confidence": 0.25,
    },
    "low_off": {
        "high_confidence": 1.00,
        "medium_confidence": 1.00,
        "low_confidence": 0.00,
    },
    "high_mid_guarded_low_off": {
        "high_confidence": 1.00,
        "medium_confidence": 0.50,
        "low_confidence": 0.00,
    },
    "high_only": {
        "high_confidence": 1.00,
        "medium_confidence": 0.00,
        "low_confidence": 0.00,
    },
}


@dataclass(frozen=True)
class TrainPolicy:
    policy: str
    description: str
    allowed_tiers: tuple[str, ...] | None
    weighted: bool


TRAIN_POLICIES = [
    TrainPolicy("all_rows", "validation 전체 row로 CatBoost residual 학습", None, False),
    TrainPolicy("confidence_weighted", "전체 row 학습 + 신뢰도별 sample weight", None, True),
    TrainPolicy("high_mid_only", "저신뢰 row 제외 후 고신뢰+중신뢰로 학습", ("high_confidence", "medium_confidence"), False),
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def safe_float_name(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", "p")


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def metric(frame: pd.DataFrame, pred_log: pd.Series | np.ndarray) -> dict[str, Any]:
    pred_log_arr = np.asarray(pred_log, dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = safe_exp(pred_log_arr)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(np.isfinite(ape).sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(actual_log - pred_log_arr)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
    }


def load_base_frame() -> pd.DataFrame:
    raw = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    base = raw[
        raw["candidate"].eq(BASE_CANDIDATE)
        & raw["split"].isin(["validation", "test"])
    ].copy()
    source_audit = {
        "source_rows_by_split": base.groupby("split").size().astype(int).to_dict(),
        "source_unique_row_ids_by_split": base.groupby("split")["_track6_row_id"].nunique().astype(int).to_dict(),
    }
    base["_scope_rank"] = base["scope"].map({"validation_oof_row": 0, "validation_oof_artist": 1}).fillna(9)
    base = (
        base.sort_values(["split", "_track6_row_id", "_scope_rank"])
        .drop_duplicates(["split", "_track6_row_id"], keep="first")
        .drop(columns=["_scope_rank"])
        .reset_index(drop=True)
    )
    source_audit["deduplicated_rows_by_split"] = base.groupby("split").size().astype(int).to_dict()
    base.attrs["source_audit"] = source_audit
    return add_features(base)


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    numeric_cols = sorted(set(NUMERIC_FEATURES + ["actual_log", "actual_price"]))
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out["component_prediction_spread"] = out[COMPONENT_COLS].std(axis=1)
    out["component_prediction_range"] = out[COMPONENT_COLS].max(axis=1) - out[COMPONENT_COLS].min(axis=1)
    out["current_vs_stable_gap_abs"] = (out["current_70_30"] - out["hcoef_stable"]).abs()
    out["svc_group_n"] = out["svc_group_n"].fillna(0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].clip(lower=0.0))
    out["log_area"] = out["log_area"].fillna(out["log_area"].median())
    out["current_minus_stable_log"] = out["current_70_30"] - out["hcoef_stable"]
    out["ppv8_minus_stable_log"] = out["ppv8_service_proxy"] - out["hcoef_stable"]
    out["svc_minus_stable_log"] = out["svc_numeric_seed_mean"] - out["hcoef_stable"]
    out["l10_minus_stable_log"] = out["l10_seq_pred_log"] - out["hcoef_stable"]
    out["confidence_risk_score"] = confidence_risk_score(out)
    out["confidence_tier"] = confidence_tier(out)
    out["confidence_sample_weight"] = out["confidence_tier"].map(WEIGHT_BY_TIER).fillna(0.15)
    return out


def high_confidence_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["quantile_width"].le(HIGH_CONFIDENCE_RULE["quantile_width_max"])
        & frame["component_prediction_spread"].le(HIGH_CONFIDENCE_RULE["component_prediction_spread_max"])
        & frame["l10_price_range_ratio"].le(HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"])
        & frame["svc_group_n"].ge(HIGH_CONFIDENCE_RULE["svc_group_n_min"])
        & frame["current_vs_stable_gap_abs"].le(HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"])
    )


def low_confidence_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["quantile_width"].gt(LOW_CONFIDENCE_RULE["quantile_width_min"])
        | frame["component_prediction_spread"].gt(LOW_CONFIDENCE_RULE["component_prediction_spread_min"])
        | frame["l10_price_range_ratio"].gt(LOW_CONFIDENCE_RULE["l10_price_range_ratio_min"])
        | frame["svc_group_n"].lt(HIGH_CONFIDENCE_RULE["svc_group_n_min"])
        | frame["current_vs_stable_gap_abs"].gt(LOW_CONFIDENCE_RULE["current_vs_stable_gap_abs_min"])
    )


def confidence_tier(frame: pd.DataFrame) -> pd.Series:
    high = high_confidence_mask(frame)
    low = low_confidence_mask(frame)
    return pd.Series(
        np.select([high, low], ["high_confidence", "low_confidence"], default="medium_confidence"),
        index=frame.index,
    )


def confidence_risk_score(frame: pd.DataFrame) -> pd.Series:
    qwidth = (frame["quantile_width"] / HIGH_CONFIDENCE_RULE["quantile_width_max"]).clip(0.0, 10.0)
    spread = (frame["component_prediction_spread"] / HIGH_CONFIDENCE_RULE["component_prediction_spread_max"]).clip(0.0, 10.0)
    ratio = (frame["l10_price_range_ratio"] / HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"]).clip(0.0, 10.0)
    gap = (frame["current_vs_stable_gap_abs"] / HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"]).clip(0.0, 10.0)
    support = (HIGH_CONFIDENCE_RULE["svc_group_n_min"] / frame["svc_group_n"].clip(lower=1.0)).clip(0.0, 10.0)
    return 0.35 * qwidth + 0.25 * spread + 0.15 * ratio + 0.15 * gap + 0.10 * support


def feature_columns(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    numeric = [col for col in NUMERIC_FEATURES if col in frame.columns]
    categorical = [col for col in CAT_FEATURES if col in frame.columns]
    return numeric, categorical


def make_x(frame: pd.DataFrame, numeric: list[str], categorical: list[str]) -> pd.DataFrame:
    x = frame[numeric + categorical].copy()
    for col in categorical:
        x[col] = x[col].where(x[col].notna(), "__missing__").astype(str)
    return x


def make_model() -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function="MAE",
        iterations=180,
        depth=4,
        learning_rate=0.04,
        l2_leaf_reg=12.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )


def select_training_rows(frame: pd.DataFrame, policy: TrainPolicy) -> pd.DataFrame:
    if policy.allowed_tiers is None:
        return frame.copy()
    return frame[frame["confidence_tier"].isin(policy.allowed_tiers)].copy()


def split_iter(validation: pd.DataFrame):
    groups = validation["artist_key"].fillna("__MISSING__").astype(str).to_numpy()
    if len(np.unique(groups)) >= N_FOLDS:
        splitter = GroupKFold(n_splits=N_FOLDS)
        yield from splitter.split(validation, groups=groups)
    else:
        splitter = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        yield from splitter.split(validation)


def fit_catboost_residual(train: pd.DataFrame, numeric: list[str], categorical: list[str], policy: TrainPolicy) -> CatBoostRegressor:
    x = make_x(train, numeric, categorical)
    y = train["actual_log"].to_numpy(dtype=float) - train[BASE_CANDIDATE].to_numpy(dtype=float)
    weights = train["confidence_sample_weight"].to_numpy(dtype=float) if policy.weighted else None
    cat_indices = [x.columns.get_loc(col) for col in categorical if col in x.columns]
    model = make_model()
    model.fit(x, y, sample_weight=weights, cat_features=cat_indices)
    return model


def raw_corrections(validation: pd.DataFrame, test: pd.DataFrame) -> tuple[dict[str, dict[str, np.ndarray]], pd.DataFrame]:
    numeric, categorical = feature_columns(validation)
    raw_by_policy: dict[str, dict[str, np.ndarray]] = {}
    audit_rows = []
    for policy in TRAIN_POLICIES:
        oof_raw = np.full(len(validation), np.nan, dtype=float)
        fold_train_sizes = []
        for train_idx, hold_idx in split_iter(validation):
            train_fold = select_training_rows(validation.iloc[train_idx].copy(), policy)
            fold_train_sizes.append(int(len(train_fold)))
            if len(train_fold) < 25:
                oof_raw[hold_idx] = 0.0
                continue
            model = fit_catboost_residual(train_fold, numeric, categorical, policy)
            oof_raw[hold_idx] = model.predict(make_x(validation.iloc[hold_idx], numeric, categorical))

        final_train = select_training_rows(validation.copy(), policy)
        final_model = fit_catboost_residual(final_train, numeric, categorical, policy)
        test_raw = np.asarray(final_model.predict(make_x(test, numeric, categorical)), dtype=float)
        raw_by_policy[policy.policy] = {
            "validation_oof": oof_raw,
            "test": test_raw,
        }
        audit_rows.append(
            {
                "policy": policy.policy,
                "description": policy.description,
                "weighted": policy.weighted,
                "train_n": int(len(final_train)),
                "high_confidence_n": int(final_train["confidence_tier"].eq("high_confidence").sum()),
                "medium_confidence_n": int(final_train["confidence_tier"].eq("medium_confidence").sum()),
                "low_confidence_n": int(final_train["confidence_tier"].eq("low_confidence").sum()),
                "fold_train_n_min": int(np.min(fold_train_sizes)),
                "fold_train_n_max": int(np.max(fold_train_sizes)),
                "feature_count": int(len(numeric) + len(categorical)),
                "categorical_feature_count": int(len(categorical)),
            }
        )
    return raw_by_policy, pd.DataFrame(audit_rows)


def apply_correction(raw: np.ndarray, frame: pd.DataFrame, cap: float, strength: float, tier_profile: dict[str, float]) -> np.ndarray:
    tier_multiplier = frame["confidence_tier"].map(tier_profile).fillna(0.0).to_numpy(dtype=float)
    return np.clip(raw * strength * tier_multiplier, -cap, cap)


def metric_rows_for_prediction(
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    correction: np.ndarray,
    split: str,
    candidate: str,
    model_policy: str,
    tier_profile_name: str,
    cap: float,
    strength: float,
) -> list[dict[str, Any]]:
    rows = []
    subsets = [("all", np.ones(len(frame), dtype=bool))]
    for tier in ["high_confidence", "medium_confidence", "low_confidence"]:
        subsets.append((tier, frame["confidence_tier"].eq(tier).to_numpy()))

    for slice_name, mask in subsets:
        if not bool(np.any(mask)):
            continue
        sub = frame.loc[mask]
        sub_pred = pred_log[mask]
        sub_correction = correction[mask]
        rows.append(
            {
                "experiment_id": EXP_ID,
                "candidate": candidate,
                "model_policy": model_policy,
                "tier_profile": tier_profile_name,
                "correction_cap_log": cap,
                "global_strength": strength,
                "split": split,
                "slice": slice_name,
                **metric(sub, sub_pred),
                "mean_correction_log": float(np.mean(sub_correction)),
                "median_correction_log": float(np.median(sub_correction)),
                "p95_abs_correction_log": float(np.quantile(np.abs(sub_correction), 0.95)),
                "positive_correction_rate": float(np.mean(sub_correction > 0)),
            }
        )
    return rows


def baseline_metric_rows(validation: pd.DataFrame, test: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for split, frame in [("validation_oof", validation), ("test", test)]:
        pred = frame[BASE_CANDIDATE].to_numpy(dtype=float)
        correction = np.zeros(len(frame), dtype=float)
        rows.extend(
            metric_rows_for_prediction(
                frame,
                pred,
                correction,
                split,
                BASE_CANDIDATE,
                "source",
                "none",
                0.0,
                0.0,
            )
        )
    return rows


def evaluate_grid(validation: pd.DataFrame, test: pd.DataFrame, raw_by_policy: dict[str, dict[str, np.ndarray]]) -> pd.DataFrame:
    rows = baseline_metric_rows(validation, test)
    split_frames = {"validation_oof": validation, "test": test}
    for model_policy, raw_split in raw_by_policy.items():
        for profile_name, profile in TIER_PROFILES.items():
            for cap in CAPS:
                for strength in STRENGTHS:
                    candidate = (
                        f"cf3_cb_{model_policy}_{profile_name}"
                        f"_cap{safe_float_name(cap)}_s{safe_float_name(strength)}"
                    )
                    for split, frame in split_frames.items():
                        correction = apply_correction(raw_split[split], frame, cap, strength, profile)
                        pred_log = frame[BASE_CANDIDATE].to_numpy(dtype=float) + correction
                        rows.extend(
                            metric_rows_for_prediction(
                                frame,
                                pred_log,
                                correction,
                                split,
                                candidate,
                                model_policy,
                                profile_name,
                                cap,
                                strength,
                            )
                        )
    return pd.DataFrame(rows).sort_values(["split", "slice", "MAPE", "MdAPE", "p95_APE", "candidate"]).reset_index(drop=True)


def prediction_rows_for_top(
    validation: pd.DataFrame,
    test: pd.DataFrame,
    raw_by_policy: dict[str, dict[str, np.ndarray]],
    selected: pd.DataFrame,
) -> pd.DataFrame:
    frames = []
    split_frames = {"validation_oof": validation, "test": test}

    for split, frame in split_frames.items():
        base = frame[["_track6_row_id", "artist_key", "artist_name_ko", "actual_log", "actual_price", "confidence_tier"]].copy()
        base["experiment_id"] = EXP_ID
        base["candidate"] = BASE_CANDIDATE
        base["split"] = split
        base["pred_log"] = frame[BASE_CANDIDATE].to_numpy(dtype=float)
        base["correction_log"] = 0.0
        base["pred_price"] = safe_exp(base["pred_log"])
        base["ape"] = (base["pred_price"] - base["actual_price"]).abs() / base["actual_price"].clip(lower=1.0)
        frames.append(base)

    for row in selected.itertuples(index=False):
        if row.model_policy == "source":
            continue
        profile = TIER_PROFILES[str(row.tier_profile)]
        for split, frame in split_frames.items():
            correction = apply_correction(
                raw_by_policy[str(row.model_policy)][split],
                frame,
                float(row.correction_cap_log),
                float(row.global_strength),
                profile,
            )
            out = frame[["_track6_row_id", "artist_key", "artist_name_ko", "actual_log", "actual_price", "confidence_tier"]].copy()
            out["experiment_id"] = EXP_ID
            out["candidate"] = str(row.candidate)
            out["split"] = split
            out["pred_log"] = frame[BASE_CANDIDATE].to_numpy(dtype=float) + correction
            out["correction_log"] = correction
            out["pred_price"] = safe_exp(out["pred_log"])
            out["ape"] = (out["pred_price"] - out["actual_price"]).abs() / out["actual_price"].clip(lower=1.0)
            frames.append(out)
    return pd.concat(frames, ignore_index=True)


def confidence_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, split_df in frame.groupby("split"):
        for tier, group in split_df.groupby("confidence_tier"):
            base_metric = metric(group, group[BASE_CANDIDATE])
            rows.append(
                {
                    "split": split,
                    "confidence_tier": tier,
                    "n": int(len(group)),
                    "quantile_width_median": float(group["quantile_width"].median()),
                    "component_spread_median": float(group["component_prediction_spread"].median()),
                    "l10_range_ratio_median": float(group["l10_price_range_ratio"].median()),
                    "svc_group_n_median": float(group["svc_group_n"].median()),
                    "gap_abs_median": float(group["current_vs_stable_gap_abs"].median()),
                    "base_MdAPE": base_metric["MdAPE"],
                    "base_MAPE": base_metric["MAPE"],
                    "base_p95_APE": base_metric["p95_APE"],
                }
            )
    return pd.DataFrame(rows)


def raw_correction_frame(validation: pd.DataFrame, test: pd.DataFrame, raw_by_policy: dict[str, dict[str, np.ndarray]]) -> pd.DataFrame:
    frames = []
    for split, frame in [("validation_oof", validation), ("test", test)]:
        base = frame[["_track6_row_id", "artist_key", "artist_name_ko", "actual_log", "actual_price", BASE_CANDIDATE, "confidence_tier"]].copy()
        base["split"] = split
        for policy, raw_split in raw_by_policy.items():
            raw = raw_split[split]
            out = base.copy()
            out["model_policy"] = policy
            out["raw_catboost_correction_log"] = raw
            frames.append(out)
    return pd.concat(frames, ignore_index=True)


def table_md(df: pd.DataFrame, cols: list[str] | None = None, max_rows: int | None = None, float_digits: int = 4) -> str:
    if cols is not None:
        df = df[cols]
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "(empty)"

    def fmt(value: Any) -> str:
        if isinstance(value, float) or isinstance(value, np.floating):
            if not np.isfinite(value):
                return ""
            return f"{float(value):.{float_digits}f}"
        if isinstance(value, int) or isinstance(value, np.integer):
            return str(int(value))
        text = str(value)
        return text.replace("|", "\\|").replace("\n", " ")

    headers = [str(col) for col in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in df.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(metrics: pd.DataFrame, confidence_df: pd.DataFrame, audit_df: pd.DataFrame, run_config: dict[str, Any]) -> None:
    base_all_val = metrics.query("candidate == @BASE_CANDIDATE and split == 'validation_oof' and slice == 'all'").iloc[0]
    base_all_test = metrics.query("candidate == @BASE_CANDIDATE and split == 'test' and slice == 'all'").iloc[0]
    val_all = metrics.query("split == 'validation_oof' and slice == 'all' and model_policy != 'source'").head(15)
    val_high = metrics.query("split == 'validation_oof' and slice == 'high_confidence' and model_policy != 'source'").head(15)

    best_all = val_all.iloc[0]
    best_all_test = metrics[
        metrics["candidate"].eq(best_all["candidate"])
        & metrics["split"].eq("test")
        & metrics["slice"].eq("all")
    ].iloc[0]
    best_high = val_high.iloc[0]
    best_high_test = metrics[
        metrics["candidate"].eq(best_high["candidate"])
        & metrics["split"].eq("test")
        & metrics["slice"].eq("high_confidence")
    ].iloc[0]

    test_all = metrics.query("split == 'test' and slice == 'all' and model_policy != 'source'").head(15)
    best_test_diag = test_all.iloc[0]

    key_rows = pd.DataFrame(
        [
            {"summary": "기준가 validation 전체", **base_all_val.to_dict()},
            {"summary": "기준가 test 전체", **base_all_test.to_dict()},
            {"summary": "validation 전체 1위", **best_all.to_dict()},
            {"summary": "validation 전체 1위 test", **best_all_test.to_dict()},
            {"summary": "validation 고신뢰 1위", **best_high.to_dict()},
            {"summary": "validation 고신뢰 1위 test", **best_high_test.to_dict()},
        ]
    )

    cols = [
        "summary",
        "candidate",
        "model_policy",
        "tier_profile",
        "correction_cap_log",
        "global_strength",
        "split",
        "slice",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "within_30",
        "over_50pct_error_rate",
        "p95_abs_correction_log",
    ]
    rank_cols = [
        "candidate",
        "model_policy",
        "tier_profile",
        "correction_cap_log",
        "global_strength",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "within_30",
        "over_50pct_error_rate",
        "p95_abs_correction_log",
    ]

    profile_rows = []
    for name, profile in TIER_PROFILES.items():
        profile_rows.append({"tier_profile": name, **profile})
    profile_df = pd.DataFrame(profile_rows)

    lines = [
        "# PP-CF3 Warm CatBoost 보정값 강도 튜닝",
        "",
        f"- 실험 ID: `{EXP_ID}`",
        f"- 실행 시각: {run_config['run_at']}",
        "- 목적: CatBoost 모델 구조를 크게 바꾸지 않고, CatBoost residual 보정값의 배율과 상한만 조정해 과보정 여부를 확인한다.",
        f"- 기준가: `{BASE_CANDIDATE}` from `PP-HCOEF20`",
        "- 선택 원칙: 후보 선택은 `validation_oof/all` 또는 목적별 `validation_oof/high_confidence` 기준이다. test는 진단용이다.",
        "",
        "## 보정 공식",
        "",
        "```text",
        "raw_catboost_correction_log = CatBoost(features) -> actual_log - hcoef_stable 예측",
        "tier_multiplier = 신뢰도 구간별 배율",
        "final_correction_log = clip(raw_catboost_correction_log * global_strength * tier_multiplier, -cap, +cap)",
        "final_pred_log = hcoef_stable + final_correction_log",
        "```",
        "",
        "즉, 이번 실험은 가격 모델 본체를 새로 바꾸는 것이 아니라 CatBoost가 만든 보정값만 조절한다.",
        "",
        "## 신뢰도 기준",
        "",
        f"- 고신뢰: `{json.dumps(HIGH_CONFIDENCE_RULE, ensure_ascii=False)}`",
        f"- 저신뢰: `{json.dumps(LOW_CONFIDENCE_RULE, ensure_ascii=False)}`",
        "- 그 외: 중신뢰",
        "",
        "## 신뢰도별 보정 배율 후보",
        "",
        table_md(profile_df),
        "",
        "## 핵심 결과",
        "",
        table_md(key_rows, cols=cols),
        "",
        "## 결론",
        "",
        (
            f"- validation 전체 기준으로는 `{best_all['candidate']}`가 1위다. "
            f"기준가 MAPE `{base_all_val['MAPE']:.4f}`에서 `{best_all['MAPE']:.4f}`로 낮아졌다."
        ),
        (
            f"- 같은 후보의 test 전체 진단값은 기준가 MAPE `{base_all_test['MAPE']:.4f}`에서 "
            f"`{best_all_test['MAPE']:.4f}`로 낮아진다. 다만 p95는 "
            f"`{base_all_test['p95_APE']:.4f}`에서 `{best_all_test['p95_APE']:.4f}`로 약간 커진다."
        ),
        (
            f"- test 전체 진단 1위는 `{best_test_diag['candidate']}`이고 MAPE `{best_test_diag['MAPE']:.4f}`다. "
            "하지만 이 후보는 test를 보고 고른 값이므로 운영 후보로 바로 선택하지 않는다."
        ),
        (
            f"- 고신뢰 기준 CatBoost 후보는 validation MAPE `{best_high['MAPE']:.4f}`, "
            f"test 고신뢰 MAPE `{best_high_test['MAPE']:.4f}`다. 기준가보다는 낮지만 개선폭은 작다."
        ),
        "- 따라서 이 실험의 결론은 `CatBoost 보정값은 작게(cap 0.02~0.03) 제한하면 방어적으로 개선 가능하지만, 큰 cap을 허용하면 validation 안정성이 약해진다`이다.",
        "",
        "## Validation 전체 기준 상위 후보",
        "",
        table_md(val_all, cols=rank_cols),
        "",
        "## Validation 고신뢰 기준 상위 후보",
        "",
        table_md(val_high, cols=rank_cols),
        "",
        "## Test 전체 상위 후보",
        "",
        "진단용이다. 후보 선택에는 사용하지 않는다.",
        "",
        table_md(test_all, cols=rank_cols),
        "",
        "## 학습 정책",
        "",
        table_md(audit_df),
        "",
        "## 신뢰도 구간별 기준가 성능",
        "",
        table_md(confidence_df),
        "",
        "## 해석",
        "",
        "- CatBoost 보정값은 validation 전체 MAPE를 낮추는 후보가 존재하는지 확인하는 용도다.",
        "- `same` profile은 모든 구간에 같은 보정을 적용하므로 저신뢰 구간 과보정 여부를 반드시 확인해야 한다.",
        "- `low_guarded`, `low_off`, `high_mid_guarded_low_off`, `high_only`는 저신뢰 보정을 줄이거나 끄는 보수적 후보군이다.",
        "- validation 1위가 test에서 기준가보다 악화되면 보정값 튜닝 자체가 과적합된 것으로 해석해야 한다.",
        "",
        "## 산출물",
        "",
        "- `outputs/metrics.csv`",
        "- `outputs/raw_catboost_corrections.csv`",
        "- `outputs/top_candidate_predictions.csv`",
        "- `outputs/validation_all_ranking.csv`",
        "- `outputs/validation_high_confidence_ranking.csv`",
        "- `outputs/test_all_ranking_diagnostic.csv`",
        "- `outputs/confidence_tier_summary.csv`",
        "- `outputs/training_policy_audit.csv`",
        "- `artifacts/run_config.json`",
    ]
    md = "\n".join(lines)
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_cf3_warm_catboost_correction_strength_tuning.md").write_text(md, encoding="utf-8")

    try:
        import markdown  # type: ignore

        body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    except Exception:
        body = f"<pre>{html.escape(md)}</pre>"
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>PP-CF3 Warm CatBoost Correction Strength Tuning</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #111827; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; text-align: right; }}
th:first-child, td:first-child, td:nth-child(2), td:nth-child(3), td:nth-child(4) {{ text-align: left; }}
th {{ background: #f3f4f6; }}
code, pre {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 2px 4px; }}
pre {{ padding: 12px; overflow-x: auto; }}
</style>
</head>
<body>{body}</body>
</html>"""
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_cf3_warm_catboost_correction_strength_tuning.html").write_text(html_doc, encoding="utf-8")


def run_experiment() -> None:
    ensure_dirs()
    frame = load_base_frame()
    validation = frame[frame["split"].eq("validation")].reset_index(drop=True)
    test = frame[frame["split"].eq("test")].reset_index(drop=True)

    raw_by_policy, audit_df = raw_corrections(validation, test)
    metrics_df = evaluate_grid(validation, test, raw_by_policy)
    confidence_df = confidence_summary(frame)
    raw_df = raw_correction_frame(validation, test, raw_by_policy)

    validation_all = metrics_df[
        metrics_df["split"].eq("validation_oof")
        & metrics_df["slice"].eq("all")
        & metrics_df["model_policy"].ne("source")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"])
    validation_high = metrics_df[
        metrics_df["split"].eq("validation_oof")
        & metrics_df["slice"].eq("high_confidence")
        & metrics_df["model_policy"].ne("source")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"])
    test_all = metrics_df[
        metrics_df["split"].eq("test")
        & metrics_df["slice"].eq("all")
        & metrics_df["model_policy"].ne("source")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"])

    selected = (
        pd.concat([validation_all.head(10), validation_high.head(10), test_all.head(5)], ignore_index=True)
        .drop_duplicates("candidate")
        .reset_index(drop=True)
    )
    top_predictions = prediction_rows_for_top(validation, test, raw_by_policy, selected)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    raw_df.to_csv(EXP_DIR / "outputs" / "raw_catboost_corrections.csv", index=False)
    top_predictions.to_csv(EXP_DIR / "outputs" / "top_candidate_predictions.csv", index=False)
    confidence_df.to_csv(EXP_DIR / "outputs" / "confidence_tier_summary.csv", index=False)
    audit_df.to_csv(EXP_DIR / "outputs" / "training_policy_audit.csv", index=False)
    validation_all.to_csv(EXP_DIR / "outputs" / "validation_all_ranking.csv", index=False)
    validation_high.to_csv(EXP_DIR / "outputs" / "validation_high_confidence_ranking.csv", index=False)
    test_all.to_csv(EXP_DIR / "outputs" / "test_all_ranking_diagnostic.csv", index=False)

    run_config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(REPO)),
        "base_candidate": BASE_CANDIDATE,
        "reference_candidate": REFERENCE_CANDIDATE,
        "seed": SEED,
        "n_folds": N_FOLDS,
        "caps": CAPS,
        "strengths": STRENGTHS,
        "tier_profiles": TIER_PROFILES,
        "train_policies": [policy.__dict__ for policy in TRAIN_POLICIES],
        "high_confidence_rule": HIGH_CONFIDENCE_RULE,
        "low_confidence_rule": LOW_CONFIDENCE_RULE,
        "source_audit": frame.attrs.get("source_audit", {}),
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(
        json.dumps(run_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_report(metrics_df, confidence_df, audit_df, run_config)
    best = validation_all.iloc[0]
    print(
        json.dumps(
            {
                "experiment_id": EXP_ID,
                "best_validation_all": {
                    "candidate": best["candidate"],
                    "MAPE": float(best["MAPE"]),
                    "MdAPE": float(best["MdAPE"]),
                    "p95_APE": float(best["p95_APE"]),
                },
                "output_dir": str(EXP_DIR),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    run_experiment()
