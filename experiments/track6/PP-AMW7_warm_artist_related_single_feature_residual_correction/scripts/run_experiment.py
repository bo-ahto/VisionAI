#!/usr/bin/env python3
"""Warm artist-related single-feature residual correction experiment.

Each artist-related column is tested independently. The base Warm prediction is
fixed to PP-SVC3 `blend_svcnum_ppv8_wsvc_0.70`; validation corrections are
estimated out-of-fold by artist group, and test corrections are estimated from
the full validation split only.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


REPO = Path(__file__).resolve().parents[4]
EXP_DIR = REPO / "experiments/track6/PP-AMW7_warm_artist_related_single_feature_residual_correction"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

SPLIT_ROOT = REPO / "data/track6_split_with_year_type_edition_size_artist_name"
BASE_PREDICTIONS = REPO / "experiments/track6/PP-SVC3_warm_svc_blend_routing/outputs/predictions.csv"
BASE_CANDIDATE = "blend_svcnum_ppv8_wsvc_0.70"

RAW_COLLECTED = REPO / "data/track4_primary_market_raw_collected.csv"
CLEANED_V2 = REPO / "data/track4_primary_market_cleaned_v2.csv"

EXPERIMENT_ID = "PP-AMW7"
SEED = 20260608

NUMERIC_GRID = [
    {"min_n": 20, "cap": 0.03, "k": 20, "bins": 3},
    {"min_n": 30, "cap": 0.03, "k": 20, "bins": 3},
    {"min_n": 40, "cap": 0.03, "k": 20, "bins": 3},
    {"min_n": 20, "cap": 0.05, "k": 20, "bins": 3},
    {"min_n": 30, "cap": 0.05, "k": 20, "bins": 3},
    {"min_n": 40, "cap": 0.05, "k": 20, "bins": 3},
    {"min_n": 30, "cap": 0.08, "k": 20, "bins": 3},
]
CATEGORICAL_GRID = [
    {"min_n": 10, "cap": 0.03, "k": 20, "bins": 0},
    {"min_n": 20, "cap": 0.03, "k": 20, "bins": 0},
    {"min_n": 30, "cap": 0.03, "k": 20, "bins": 0},
    {"min_n": 10, "cap": 0.05, "k": 20, "bins": 0},
    {"min_n": 20, "cap": 0.05, "k": 20, "bins": 0},
    {"min_n": 30, "cap": 0.05, "k": 20, "bins": 0},
]


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def read_split(split: str) -> pd.DataFrame:
    return pd.read_csv(SPLIT_ROOT / f"track6_{split}.csv", low_memory=False)


def clean_count(series: pd.Series) -> pd.Series:
    value = pd.to_numeric(series, errors="coerce")
    return value.mask((value < 0) | (value > 200))


def tier_to_score(value: Any) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if text in {"tier a", "a", "1"}:
        return 3.0
    if text in {"tier b", "b", "2"}:
        return 2.0
    if text in {"tier c", "c", "3"}:
        return 1.0
    return np.nan


def load_raw_external_map() -> pd.DataFrame:
    raw_cols = [
        "track4_source",
        "track4_source_row_index",
        "saatchi__solo_count",
        "saatchi__group_count",
        "saatchi__fair_count",
        "saatchi__gallery_tier",
        "saatchi__gallery_city_count",
        "gallery_primary__gallery_tier",
    ]
    raw = pd.read_csv(RAW_COLLECTED, usecols=lambda c: c in set(raw_cols), low_memory=False)
    raw["track4_source_row_index"] = pd.to_numeric(raw["track4_source_row_index"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["track4_source", "track4_source_row_index"]).copy()
    raw["track4_source_row_index"] = raw["track4_source_row_index"].astype(int)
    raw = raw.drop_duplicates(["track4_source", "track4_source_row_index"], keep="first")
    raw = raw.rename(
        columns={
            "saatchi__solo_count": "artist_exhibition_solo_count",
            "saatchi__group_count": "artist_exhibition_group_count",
            "saatchi__fair_count": "artist_exhibition_fair_count",
            "saatchi__gallery_city_count": "gallery_city_count",
        }
    )
    for col in [
        "artist_exhibition_solo_count",
        "artist_exhibition_group_count",
        "artist_exhibition_fair_count",
    ]:
        raw[col] = clean_count(raw[col])
    raw["gallery_tier_raw_numeric"] = pd.to_numeric(raw.get("saatchi__gallery_tier"), errors="coerce")
    raw["gallery_tier_raw_numeric"] = raw["gallery_tier_raw_numeric"].where(
        raw["gallery_tier_raw_numeric"].notna(),
        pd.to_numeric(raw.get("gallery_primary__gallery_tier"), errors="coerce"),
    )
    raw["gallery_city_count"] = pd.to_numeric(raw.get("gallery_city_count"), errors="coerce")
    return raw[
        [
            "track4_source",
            "track4_source_row_index",
            "artist_exhibition_solo_count",
            "artist_exhibition_group_count",
            "artist_exhibition_fair_count",
            "gallery_tier_raw_numeric",
            "gallery_city_count",
        ]
    ]


def load_validated_gallery_map() -> pd.DataFrame:
    cols = [
        "track4_source",
        "track4_source_row_index",
        "gallery_tier_validated",
        "gallery_ref_type",
        "gallery_audit_status",
    ]
    gallery = pd.read_csv(CLEANED_V2, usecols=lambda c: c in set(cols), low_memory=False)
    gallery["track4_source_row_index"] = pd.to_numeric(gallery["track4_source_row_index"], errors="coerce").astype("Int64")
    gallery = gallery.dropna(subset=["track4_source", "track4_source_row_index"]).copy()
    gallery["track4_source_row_index"] = gallery["track4_source_row_index"].astype(int)
    return gallery.drop_duplicates(["track4_source", "track4_source_row_index"], keep="first")


def build_external_features(frame: pd.DataFrame) -> pd.DataFrame:
    raw = load_raw_external_map()
    gallery = load_validated_gallery_map()
    out = frame.merge(raw, on=["track4_source", "track4_source_row_index"], how="left")
    out = out.merge(gallery, on=["track4_source", "track4_source_row_index"], how="left")
    count_cols = [
        "artist_exhibition_solo_count",
        "artist_exhibition_group_count",
        "artist_exhibition_fair_count",
    ]
    for col in count_cols:
        out[col] = pd.to_numeric(out.get(col), errors="coerce")
        out[f"{col}_missing"] = out[col].isna().astype(float)
        out[f"{col}_log"] = np.log1p(out[col].clip(lower=0).fillna(0.0))
    out["artist_exhibition_total_count"] = out[count_cols].sum(axis=1, min_count=1)
    out["artist_exhibition_total_count_log"] = np.log1p(out["artist_exhibition_total_count"].clip(lower=0).fillna(0.0))
    out["artist_exhibition_available_count"] = 3.0 - out[[f"{col}_missing" for col in count_cols]].sum(axis=1)

    out["gallery_tier_raw_numeric"] = pd.to_numeric(out.get("gallery_tier_raw_numeric"), errors="coerce")
    out["gallery_tier_raw_available_flag"] = out["gallery_tier_raw_numeric"].notna().astype(float)
    out["gallery_tier_raw_bucket"] = out["gallery_tier_raw_numeric"].astype("Int64").astype("string").fillna("__MISSING__")
    out["gallery_tier_validated"] = out.get("gallery_tier_validated", pd.Series(index=out.index, dtype=object))
    out["gallery_tier_validated"] = out["gallery_tier_validated"].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    out["gallery_tier_validated_score"] = out["gallery_tier_validated"].map(tier_to_score).astype(float)
    out["gallery_tier_validated_available_flag"] = out["gallery_tier_validated_score"].notna().astype(float)
    out["gallery_tier_any_available_flag"] = (
        (out["gallery_tier_raw_available_flag"] > 0) | (out["gallery_tier_validated_available_flag"] > 0)
    ).astype(float)
    out["gallery_city_count"] = pd.to_numeric(out.get("gallery_city_count"), errors="coerce")
    out["gallery_city_count_log"] = np.log1p(out["gallery_city_count"].clip(lower=0).fillna(0.0))
    for col in ["gallery_ref_type", "gallery_audit_status"]:
        out[col] = out.get(col, pd.Series(index=out.index, dtype=object)).astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    out["gallery_feature_source"] = np.select(
        [
            out["gallery_tier_validated_available_flag"].eq(1),
            out["gallery_tier_raw_available_flag"].eq(1),
        ],
        ["validated", "raw"],
        default="missing",
    )
    return out


def engineer_artist_derivatives(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in [
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
        "artist_meta_birth_year",
        "artist_meta_career_age",
        "artist_works_count_train",
        "artist_works_log",
    ]:
        if col in out.columns:
            num = pd.to_numeric(out[col], errors="coerce")
            out[f"{col}_missing"] = num.isna().astype(float)
            if col.endswith("_ratio") or col.endswith("_birth_year"):
                continue
            out[f"{col}_log1p"] = np.log1p(num.clip(lower=0).fillna(0.0))
    if "artist_meta_birth_year" in out.columns:
        birth = pd.to_numeric(out["artist_meta_birth_year"], errors="coerce")
        out["artist_birth_generation_bin"] = pd.cut(
            birth,
            bins=[-np.inf, 1940, 1950, 1960, 1970, 1980, 1990, np.inf],
            labels=["pre_1940", "1940s", "1950s", "1960s", "1970s", "1980s", "1990_plus"],
        ).astype("string").fillna("__MISSING__")
    if "artist_meta_total_works" in out.columns and "artist_meta_for_sale_works" in out.columns:
        total = pd.to_numeric(out["artist_meta_total_works"], errors="coerce")
        sale = pd.to_numeric(out["artist_meta_for_sale_works"], errors="coerce")
        out["artist_meta_market_depth_gap"] = total - sale
        out["artist_meta_market_depth_gap_log1p"] = np.log1p(out["artist_meta_market_depth_gap"].clip(lower=0).fillna(0.0))
    return out


def load_base_predictions() -> tuple[pd.DataFrame, pd.DataFrame]:
    pred = pd.read_csv(BASE_PREDICTIONS)
    pred = pred[pred["candidate"].eq(BASE_CANDIDATE)].copy()
    val = pred[pred["split"].eq("validation")].copy()
    test = pred[pred["split"].eq("test")].copy()
    if val.empty or test.empty:
        raise RuntimeError(f"Missing base candidate predictions: {BASE_CANDIDATE}")
    return val, test


def prepare_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    val_base, test_base = load_base_predictions()
    val = read_split("val_warm")
    test = read_split("test_warm")
    val = build_external_features(val)
    test = build_external_features(test)
    val = engineer_artist_derivatives(val)
    test = engineer_artist_derivatives(test)

    keep = [
        "_track6_row_id",
        "actual_log",
        "pred_log",
        "actual_price",
        "pred_price",
        "residual_log",
        "ape",
    ]
    val = val.merge(val_base[keep], on="_track6_row_id", how="inner", suffixes=("", "_base"))
    test = test.merge(test_base[keep], on="_track6_row_id", how="inner", suffixes=("", "_base"))
    return val, test


def is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "<na>"}


def feature_columns(frame: pd.DataFrame) -> list[str]:
    prefixes = ("artist_", "gallery_")
    include = []
    excluded = {
        "actual_log",
        "actual_price",
        "pred_log",
        "pred_price",
        "residual_log",
        "ape",
    }
    for col in frame.columns:
        if col in excluded:
            continue
        if col.startswith(prefixes):
            include.append(col)
    return sorted(set(include))


def infer_feature_kind(series: pd.Series) -> str:
    if not is_numeric_dtype(series):
        return "categorical"
    num = pd.to_numeric(series, errors="coerce")
    non_null = num.dropna()
    if non_null.empty:
        return "empty"
    unique_n = int(non_null.nunique())
    if unique_n <= 8:
        return "categorical"
    return "numeric"


def numeric_spec(series: pd.Series, bins: int) -> dict[str, Any]:
    num = pd.to_numeric(series, errors="coerce")
    non_null = num.dropna()
    if non_null.nunique() <= bins:
        return {"kind": "categorical"}
    qs = np.linspace(0.0, 1.0, bins + 1)
    edges = np.unique(np.nanquantile(non_null.to_numpy(dtype=float), qs))
    if len(edges) <= 2:
        return {"kind": "categorical"}
    return {"kind": "numeric", "edges": edges.tolist()}


def transform_segments(series: pd.Series, spec: dict[str, Any]) -> pd.Series:
    if spec["kind"] == "numeric":
        values = pd.to_numeric(series, errors="coerce")
        edges = np.asarray(spec["edges"], dtype=float)
        labels = []
        inner = edges[1:-1]
        for value in values:
            if pd.isna(value):
                labels.append("__MISSING__")
            else:
                idx = int(np.searchsorted(inner, float(value), side="right")) + 1
                left = edges[idx - 1]
                right = edges[idx]
                labels.append(f"bin{idx}[{left:.4g},{right:.4g}]")
        return pd.Series(labels, index=series.index, dtype="string")
    return series.map(lambda x: "__MISSING__" if is_missing_value(x) else str(x)).astype("string")


def fit_correction(
    train: pd.DataFrame,
    feature: str,
    min_n: int,
    cap: float,
    k: int,
    bins: int,
) -> dict[str, Any]:
    kind = infer_feature_kind(train[feature])
    spec = numeric_spec(train[feature], bins) if kind == "numeric" else {"kind": "categorical"}
    seg = transform_segments(train[feature], spec)
    counts = seg.value_counts(dropna=False)
    rare = set(counts[counts < min_n].index.astype(str).tolist())
    seg_fit = seg.astype(str).where(~seg.astype(str).isin(rare), "__OTHER__")
    work = pd.DataFrame({"segment": seg_fit, "residual": train["residual_log"].astype(float)})
    group = work.groupby("segment", dropna=False)["residual"].agg(["count", "median", "mean"]).reset_index()
    corrections = {}
    map_rows = []
    for row in group.itertuples(index=False):
        n = int(row.count)
        if n < min_n:
            corr = 0.0
        else:
            shrink = n / (n + k)
            corr = float(np.clip(float(row.median) * shrink, -cap, cap))
        corrections[str(row.segment)] = corr
        map_rows.append(
            {
                "segment": str(row.segment),
                "n": n,
                "median_residual": float(row.median),
                "mean_residual": float(row.mean),
                "correction": corr,
            }
        )
    return {
        "feature": feature,
        "kind": kind,
        "spec": spec,
        "rare": sorted(rare),
        "corrections": corrections,
        "min_n": min_n,
        "cap": cap,
        "k": k,
        "bins": bins,
        "map_rows": map_rows,
    }


def apply_correction(frame: pd.DataFrame, model: dict[str, Any]) -> np.ndarray:
    seg = transform_segments(frame[model["feature"]], model["spec"]).astype(str)
    rare = set(model["rare"])
    seg = seg.where(~seg.isin(rare), "__OTHER__")
    corr = seg.map(model["corrections"]).fillna(0.0).astype(float)
    return corr.to_numpy(dtype=float)


def fold_for_artist(value: Any, n_folds: int = 5) -> int:
    text = "__MISSING__" if is_missing_value(value) else str(value)
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % n_folds


def oof_correction(frame: pd.DataFrame, feature: str, params: dict[str, Any]) -> np.ndarray:
    folds = frame["artist_key"].map(fold_for_artist)
    out = np.zeros(len(frame), dtype=float)
    for fold in sorted(folds.unique()):
        train = frame[folds.ne(fold)].copy()
        apply = frame[folds.eq(fold)].copy()
        if len(train) == 0 or len(apply) == 0:
            continue
        model = fit_correction(train, feature, **params)
        out[folds.eq(fold).to_numpy()] = apply_correction(apply, model)
    return out


def metric_values(actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.exp(actual_log)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def add_deltas(row: dict[str, Any], base: dict[str, float], prefix: str = "") -> None:
    for metric in ["RMSE_log", "MdAPE", "MAPE", "p95_APE", "Within_30", "Within_50"]:
        key = f"{prefix}{metric}"
        if key in row and metric in base:
            row[f"{prefix}delta_{metric}"] = float(row[key] - base[metric])


def correction_metrics(frame: pd.DataFrame, correction: np.ndarray) -> dict[str, float]:
    base = frame["pred_log"].to_numpy(dtype=float)
    actual = frame["actual_log"].to_numpy(dtype=float)
    corrected = base + correction
    return metric_values(actual, corrected)


def coverage_row(feature: str, val: pd.DataFrame, test: pd.DataFrame, kind: str) -> dict[str, Any]:
    def non_null(s: pd.Series) -> pd.Series:
        if not is_numeric_dtype(s):
            return ~s.map(is_missing_value)
        return pd.to_numeric(s, errors="coerce").notna()

    val_nn = non_null(val[feature])
    test_nn = non_null(test[feature])
    return {
        "feature": feature,
        "kind": kind,
        "validation_coverage": float(val_nn.mean()),
        "validation_non_null_n": int(val_nn.sum()),
        "validation_unique_n": int(val.loc[val_nn, feature].astype(str).nunique()),
        "test_coverage": float(test_nn.mean()),
        "test_non_null_n": int(test_nn.sum()),
        "test_unique_n": int(test.loc[test_nn, feature].astype(str).nunique()),
    }


def safe_feature_name(value: str) -> str:
    return (
        value.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("[", "")
        .replace("]", "")
        .replace(",", "_")
    )


def run() -> None:
    ensure_dirs()
    val, test = prepare_frames()
    features = feature_columns(val)

    base_val = metric_values(val["actual_log"].to_numpy(dtype=float), val["pred_log"].to_numpy(dtype=float))
    base_test = metric_values(test["actual_log"].to_numpy(dtype=float), test["pred_log"].to_numpy(dtype=float))

    coverage_rows = []
    metric_rows = []
    map_rows = []
    prediction_cols = [
        "_track6_row_id",
        "actual_log",
        "pred_log",
        "actual_price",
        "artist_key",
        "artist_name_ko",
    ]
    top_prediction_frames = []

    for feature in features:
        kind = infer_feature_kind(val[feature])
        if kind == "empty":
            continue
        coverage_rows.append(coverage_row(feature, val, test, kind))
        grid = NUMERIC_GRID if kind == "numeric" else CATEGORICAL_GRID
        for params in grid:
            val_corr = oof_correction(val, feature, params)
            full_model = fit_correction(val, feature, **params)
            test_corr = apply_correction(test, full_model)

            val_metrics = correction_metrics(val, val_corr)
            test_metrics = correction_metrics(test, test_corr)
            candidate = (
                f"single_{safe_feature_name(feature)}_"
                f"{kind}_min{params['min_n']}_cap{str(params['cap']).replace('.', 'p')}_k{params['k']}"
            )
            row = {
                "experiment_id": EXPERIMENT_ID,
                "candidate": candidate,
                "feature": feature,
                "kind": kind,
                "min_n": params["min_n"],
                "cap": params["cap"],
                "k": params["k"],
                "bins": params["bins"],
                "validation_mean_abs_correction": float(np.mean(np.abs(val_corr))),
                "validation_nonzero_rate": float(np.mean(np.abs(val_corr) > 1e-12)),
                "test_mean_abs_correction": float(np.mean(np.abs(test_corr))),
                "test_nonzero_rate": float(np.mean(np.abs(test_corr) > 1e-12)),
                **{f"validation_{key}": value for key, value in val_metrics.items()},
                **{f"test_{key}": value for key, value in test_metrics.items()},
            }
            add_deltas(row, base_val, "validation_")
            add_deltas(row, base_test, "test_")
            row["validation_balanced_delta"] = (
                row["validation_delta_MdAPE"] + row["validation_delta_MAPE"] + 0.20 * row["validation_delta_p95_APE"]
            )
            row["test_balanced_delta"] = row["test_delta_MdAPE"] + row["test_delta_MAPE"] + 0.20 * row["test_delta_p95_APE"]
            metric_rows.append(row)

            for mr in full_model["map_rows"]:
                map_rows.append(
                    {
                        "candidate": candidate,
                        "feature": feature,
                        "kind": kind,
                        "min_n": params["min_n"],
                        "cap": params["cap"],
                        "k": params["k"],
                        **mr,
                    }
                )

    metrics_df = pd.DataFrame(metric_rows).sort_values(["validation_balanced_delta", "validation_delta_MAPE"])
    coverage_df = pd.DataFrame(coverage_rows).sort_values(["feature"])
    maps_df = pd.DataFrame(map_rows)

    feature_best = (
        metrics_df.sort_values(["feature", "validation_balanced_delta", "validation_delta_MAPE"])
        .groupby("feature", as_index=False)
        .head(1)
        .sort_values(["validation_balanced_delta", "validation_delta_MAPE"])
    )
    test_top = metrics_df.sort_values(["test_balanced_delta", "test_delta_MAPE"]).head(30)
    val_top = metrics_df.head(30)

    for _, row in feature_best.head(12).iterrows():
        feature = str(row["feature"])
        params = {"min_n": int(row["min_n"]), "cap": float(row["cap"]), "k": int(row["k"]), "bins": int(row["bins"])}
        model = fit_correction(val, feature, **params)
        corr = apply_correction(test, model)
        out = test[prediction_cols].copy()
        out["candidate"] = row["candidate"]
        out["feature"] = feature
        out["correction_log"] = corr
        out["corrected_pred_log"] = out["pred_log"] + corr
        out["corrected_pred_price"] = np.clip(np.exp(out["corrected_pred_log"]), 1_000.0, None)
        out["corrected_ape"] = np.abs(out["corrected_pred_price"] - out["actual_price"]) / out["actual_price"]
        top_prediction_frames.append(out)

    metrics_df.to_csv(OUT_DIR / "single_feature_candidate_metrics.csv", index=False)
    feature_best.to_csv(OUT_DIR / "single_feature_best_by_feature.csv", index=False)
    val_top.to_csv(OUT_DIR / "validation_top_candidates.csv", index=False)
    test_top.to_csv(OUT_DIR / "test_top_candidates_diagnostic.csv", index=False)
    coverage_df.to_csv(OUT_DIR / "feature_coverage.csv", index=False)
    maps_df.to_csv(OUT_DIR / "correction_maps.csv", index=False)
    if top_prediction_frames:
        pd.concat(top_prediction_frames, ignore_index=True).to_csv(OUT_DIR / "top_feature_test_predictions.csv", index=False)

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "title": "Warm artist-related single-feature residual correction",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_candidate": BASE_CANDIDATE,
        "validation_rows": int(len(val)),
        "test_rows": int(len(test)),
        "validation_method": "artist-key grouped 5-fold OOF residual correction",
        "test_method": "fit correction map on full validation and apply once to fixed test",
        "candidate_features": features,
        "grid": {"numeric": NUMERIC_GRID, "categorical": CATEGORICAL_GRID},
        "outputs": [
            "outputs/single_feature_candidate_metrics.csv",
            "outputs/single_feature_best_by_feature.csv",
            "outputs/validation_top_candidates.csv",
            "outputs/test_top_candidates_diagnostic.csv",
            "outputs/feature_coverage.csv",
            "outputs/correction_maps.csv",
            "outputs/top_feature_test_predictions.csv",
        ],
    }
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(base_val, base_test, coverage_df, feature_best, val_top, test_top)


def fmt(value: Any, digits: int = 4) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)):
            return ""
        return f"{float(value):.{digits}f}"
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    view = df.loc[:, columns].head(max_rows).copy()
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def write_report(
    base_val: dict[str, float],
    base_test: dict[str, float],
    coverage: pd.DataFrame,
    feature_best: pd.DataFrame,
    val_top: pd.DataFrame,
    test_top: pd.DataFrame,
) -> None:
    best_cols = [
        "feature",
        "kind",
        "min_n",
        "cap",
        "validation_MdAPE",
        "validation_MAPE",
        "validation_p95_APE",
        "validation_delta_MdAPE",
        "validation_delta_MAPE",
        "validation_delta_p95_APE",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "test_mean_abs_correction",
    ]
    coverage_cols = [
        "feature",
        "kind",
        "validation_coverage",
        "validation_non_null_n",
        "validation_unique_n",
        "test_coverage",
        "test_non_null_n",
        "test_unique_n",
    ]
    lines = [
        "# PP-AMW7 Warm 작가 관련 단일 피처 잔차 보정 실험",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 후보: `{BASE_CANDIDATE}`",
        "- 목적: 작가 관련 컬럼을 묶음이 아니라 단일 컬럼별로 독립 보정해 실제 잔차 설명력과 영향도를 확인",
        "- validation: 작가 키 기준 5-fold OOF 보정",
        "- test: validation 전체로 만든 보정맵을 고정 test에 1회 적용",
        "- 보정 방식: 단일 피처 구간별 validation median residual을 shrink 후 cap으로 제한",
        "",
        "## 1. 기준 성능",
        "",
        "| split | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| validation | {fmt(base_val['RMSE_log'])} | {fmt(base_val['MdAPE'])} | {fmt(base_val['MAPE'])} | {fmt(base_val['p95_APE'])} | {fmt(base_val['Within_30'])} | {fmt(base_val['Within_50'])} |",
        f"| test | {fmt(base_test['RMSE_log'])} | {fmt(base_test['MdAPE'])} | {fmt(base_test['MAPE'])} | {fmt(base_test['p95_APE'])} | {fmt(base_test['Within_30'])} | {fmt(base_test['Within_50'])} |",
        "",
        "## 2. 실행 결론",
        "",
        "- 단일 피처 단위로 보면 validation OOF 개선과 test 개선이 항상 일치하지 않는다.",
        "- 따라서 validation OOF 기준 상위 후보와 test 진단 상위 후보를 분리해서 본다.",
        "- 직접 식별자 성격의 `artist_key`/작가명 계열은 test에서는 좋아 보일 수 있어도 OOF 안정성 기준으로 해석해야 한다.",
        "- 운영 후보 판단은 `validation_delta_*`와 `test_delta_*`, 평균 보정폭, 커버리지를 함께 확인한다.",
        "",
        "## 3. 피처별 validation 기준 최선 후보",
        "",
        markdown_table(feature_best, best_cols, max_rows=30),
        "",
        "## 4. validation OOF 상위 후보",
        "",
        markdown_table(val_top, best_cols, max_rows=20),
        "",
        "## 5. test 진단 상위 후보",
        "",
        markdown_table(test_top, best_cols, max_rows=20),
        "",
        "## 6. 커버리지",
        "",
        markdown_table(coverage, coverage_cols, max_rows=80),
        "",
        "## 7. 산출물",
        "",
        "- `outputs/single_feature_candidate_metrics.csv`",
        "- `outputs/single_feature_best_by_feature.csv`",
        "- `outputs/validation_top_candidates.csv`",
        "- `outputs/test_top_candidates_diagnostic.csv`",
        "- `outputs/feature_coverage.csv`",
        "- `outputs/correction_maps.csv`",
        "- `outputs/top_feature_test_predictions.csv`",
        "- `outputs/experiment_manifest.json`",
    ]
    md = "\n".join(lines)
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    body = html.escape(md)
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>PP-AMW7 Warm single feature correction</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 32px; line-height: 1.55; color: #1f2933; }}
    pre {{ white-space: pre-wrap; background: #f6f8fa; padding: 20px; border-radius: 8px; }}
  </style>
</head>
<body><pre>{body}</pre></body>
</html>
"""
    (REPORT_DIR / "result_report.html").write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    run()
