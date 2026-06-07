#!/usr/bin/env python3
"""Run Warm MAPE optimization combinations.

The experiment reuses existing Warm prediction artifacts and tests post-model
combinations that directly optimize MAPE while guarding MdAPE and p95_APE.
All correction values and routing choices are fitted on Warm validation only
and then applied to Warm test.
"""
from __future__ import annotations

import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED  # noqa: E402


EXP_ID = "PP-WMAPE"
EXP_SLUG = "PP-WMAPE_warm_mape_optimization"
TITLE = "Warm MAPE 최적화 조합 실험"

SPLIT_PATHS = {
    "validation": REPO / "data" / "track6_split" / "track6_val_warm.csv",
    "test": REPO / "data" / "track6_split" / "track6_test_warm.csv",
}
FEATURE_PATHS = {
    "validation": REPO / "data" / "track6_split" / "features" / "warm" / "track6_val_warm_warm_features.csv",
    "test": REPO / "data" / "track6_split" / "features" / "warm" / "track6_test_warm_warm_features.csv",
}
SEARCH_SNAPSHOT_PATH = REPO / "data" / "track6" / "external_search" / "operational" / "track6_artist_search_operational_snapshot_latest.csv"
SEARCH_STANDARDIZED_PATH = REPO / "data" / "track6" / "external_search" / "operational" / "track6_artist_search_operational_standardized_latest.csv"

PREDICTION_SOURCES = [
    {
        "prefix": "v8",
        "path": REPO / "experiments" / "track6" / "PP-V8_warm_deployment_simplification" / "outputs" / "predictions.csv",
        "metric_path": REPO / "experiments" / "track6" / "PP-V8_warm_deployment_simplification" / "outputs" / "metrics.csv",
        "pred_col": "pred_log",
        "candidate_limit": None,
    },
    {
        "prefix": "h29",
        "path": REPO / "experiments" / "track6" / "PP-H29_warm_search_feature_calibration" / "outputs" / "candidate_predictions.csv",
        "metric_path": REPO / "experiments" / "track6" / "PP-H29_warm_search_feature_calibration" / "outputs" / "metrics.csv",
        "pred_col": "corrected_pred_log",
        "candidate_limit": 18,
    },
    {
        "prefix": "r5",
        "path": REPO / "experiments" / "track6" / "PP-R5_warm_final_candidate_residual_stabilization" / "outputs" / "predictions.csv",
        "metric_path": REPO / "experiments" / "track6" / "PP-R5_warm_final_candidate_residual_stabilization" / "outputs" / "metrics.csv",
        "pred_col": "pred_log",
        "candidate_limit": None,
    },
    {
        "prefix": "l10",
        "path": REPO / "experiments" / "track6" / "PP-L10_warm_l8_feature_variant_sequential" / "outputs" / "predictions.csv",
        "metric_path": REPO / "experiments" / "track6" / "PP-L10_warm_l8_feature_variant_sequential" / "outputs" / "metrics.csv",
        "pred_col": "pred_log",
        "candidate_limit": 12,
    },
    {
        "prefix": "d4",
        "path": REPO / "experiments" / "track6" / "PP-D4_warm_three_model_blend" / "outputs" / "predictions.csv",
        "metric_path": REPO / "experiments" / "track6" / "PP-D4_warm_three_model_blend" / "outputs" / "metrics.csv",
        "pred_col": "pred_log",
        "candidate_limit": None,
    },
]

CURRENT_BASE_SOURCE = "v8__compact_blend_mape_guarded"
CURRENT_H29_SOURCE = "h29__h29_v8_compact_mape_gallery_median_cap0p05"
ALWAYS_INCLUDE_BY_PREFIX = {
    "h29": {
        "h29_v8_compact_mape_gallery_median_cap0p05",
        "h29_v8_compact_mape_gallery_median_cap0p1",
        "h29_v8_compact_mape_market_median_cap0p05",
        "h29_v8_compact_mape_name_match_median_cap0p05",
        "h29_v8_compact_mape_provider_cov_median_cap0p05",
    }
}


@dataclass
class CandidateResult:
    candidate: str
    policy: str
    split: str
    pred_log: pd.Series
    notes: str


def safe_name(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z가-힣_]+", "_", str(value))
    return re.sub(r"_+", "_", value).strip("_")


def clean_artist_name(name: Any) -> str:
    value = "" if pd.isna(name) else str(name)
    value = re.sub(r"_[A-Z]+$", "", value).strip()
    return re.sub(r"\s+", " ", value)


def metric_values(actual_log: pd.Series, pred_log: pd.Series) -> dict[str, float]:
    actual_log = pd.Series(actual_log, dtype=float)
    pred_log = pd.Series(pred_log, dtype=float)
    actual = np.exp(actual_log)
    pred = np.exp(pred_log)
    ape = np.abs(actual - pred) / np.maximum(actual, 1e-9)
    return {
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    copy = df.copy()
    for col in copy.columns:
        if pd.api.types.is_float_dtype(copy[col]):
            copy[col] = copy[col].map(lambda value: "" if pd.isna(value) else f"{value:.6f}")
        else:
            copy[col] = copy[col].map(lambda value: "" if pd.isna(value) else str(value))
    lines = [
        "| " + " | ".join(map(str, copy.columns)) + " |",
        "| " + " | ".join(["---"] * len(copy.columns)) + " |",
    ]
    for row in copy.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def top_candidates_from_metrics(source: dict[str, Any]) -> set[str] | None:
    always_include = set(ALWAYS_INCLUDE_BY_PREFIX.get(str(source.get("prefix")), set()))
    limit = source.get("candidate_limit")
    if not limit:
        return always_include or None
    metric_path = Path(source["metric_path"])
    if not metric_path.exists():
        return always_include or None
    metrics = pd.read_csv(metric_path)
    if "split" not in metrics.columns or "candidate" not in metrics.columns or "MAPE" not in metrics.columns:
        return always_include or None
    validation = metrics[metrics["split"].astype(str).eq("validation")].copy()
    if validation.empty:
        return always_include or None
    selected = set(validation.sort_values(["MAPE", "MdAPE", "p95_APE"]).head(int(limit))["candidate"].astype(str))
    return selected | always_include


def load_prediction_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    source_rows = []
    for source in PREDICTION_SOURCES:
        path = Path(source["path"])
        if not path.exists():
            continue
        allowed = top_candidates_from_metrics(source)
        pred_col = str(source["pred_col"])
        df = pd.read_csv(path, low_memory=False)
        if "scope" in df.columns:
            df = df[df["scope"].astype(str).eq("warm")].copy()
        df = df[df["split"].astype(str).isin(["validation", "test"])].copy()
        if allowed is not None:
            df = df[df["candidate"].astype(str).isin(allowed)].copy()
        if pred_col not in df.columns:
            continue
        df["source_label"] = source["prefix"] + "__" + df["candidate"].astype(str).map(safe_name)
        keep = ["source_label", "candidate", "split", "_track6_row_id", "actual_log", pred_col]
        extras = [col for col in ["routing_width", "quantile_width", "q10_log", "q50_log", "q90_log"] if col in df.columns]
        part = df[keep + extras].rename(columns={pred_col: "pred_log"}).copy()
        part = part.drop_duplicates(["source_label", "split", "_track6_row_id"], keep="last")
        frames.append(part)
        source_rows.extend(
            {
                "source_label": label,
                "source_prefix": source["prefix"],
                "source_candidate": candidate,
                "prediction_path": str(path.relative_to(REPO)),
            }
            for label, candidate in part[["source_label", "candidate"]].drop_duplicates().itertuples(index=False, name=None)
        )
    if not frames:
        raise RuntimeError("No warm prediction source files were available.")
    long_df = pd.concat(frames, ignore_index=True)
    source_map = pd.DataFrame(source_rows).drop_duplicates("source_label").reset_index(drop=True)
    return long_df, source_map


def load_meta_features() -> pd.DataFrame:
    frames = []
    for split in ["validation", "test"]:
        base = pd.read_csv(SPLIT_PATHS[split], low_memory=False)
        feat = pd.read_csv(FEATURE_PATHS[split], low_memory=False)
        base_cols = [
            "_track6_row_id",
            "artist_name_ko",
            "artist_key",
            "price_krw",
            "ln_price_krw",
            "width_cm",
            "height_cm",
            "depth_cm",
            "area_cm2",
            "log_area",
            "aspect_ratio",
            "artist_works_log",
            "artist_works_count_train",
            "medium_category",
            "support_category",
            "medium_support_bucket",
            "nant_support",
            "nant_tool",
        ]
        base_cols = [col for col in base_cols if col in base.columns]
        feat_cols = [
            "_track6_row_id",
            "has_depth",
            "is_3d_candidate",
            "is_extreme_aspect_ratio",
            "nant_material_idx",
        ]
        feat_cols = [col for col in feat_cols if col in feat.columns]
        merged = base[base_cols].merge(feat[feat_cols].drop_duplicates("_track6_row_id"), on="_track6_row_id", how="left")
        merged["split"] = split
        merged["artist_search_name"] = merged["artist_name_ko"].map(clean_artist_name)
        frames.append(merged)
    meta = pd.concat(frames, ignore_index=True)

    if SEARCH_SNAPSHOT_PATH.exists():
        snap = pd.read_csv(SEARCH_SNAPSHOT_PATH, low_memory=False)
        snap["artist_search_name"] = snap["artist_search_name"].map(clean_artist_name)
        search_cols = [
            "artist_search_name",
            "search_quality_score",
            "search_name_match_ratio",
            "search_homonym_risk_ratio",
            "provider_coverage_count",
            "search_result_count_log",
            "search_source_count_log",
        ]
        search_cols = [col for col in search_cols if col in snap.columns]
        meta = meta.merge(snap[search_cols].drop_duplicates("artist_search_name", keep="last"), on="artist_search_name", how="left")
    if SEARCH_STANDARDIZED_PATH.exists():
        std = pd.read_csv(SEARCH_STANDARDIZED_PATH, low_memory=False)
        if {"artist_search_name", "source_group"}.issubset(std.columns):
            std["artist_search_name"] = std["artist_search_name"].map(clean_artist_name)
            source_counts = std.groupby(["artist_search_name", "source_group"], dropna=False).size().unstack(fill_value=0)
            total = source_counts.sum(axis=1).replace(0, np.nan)
            groups = ["gallery_museum", "news", "social_blog", "market", "exhibition", "art_general"]
            for group in groups:
                if group not in source_counts.columns:
                    source_counts[group] = 0
                source_counts[f"source_group_{group}_ratio"] = source_counts[group] / total
            ratios = source_counts[[f"source_group_{group}_ratio" for group in groups]].reset_index()
            meta = meta.merge(ratios, on="artist_search_name", how="left")
    return meta


def build_wide_predictions(long_df: pd.DataFrame, meta: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    actual = (
        long_df.groupby(["split", "_track6_row_id"], as_index=False)["actual_log"]
        .first()
    )
    pred_wide = long_df.pivot_table(
        index=["split", "_track6_row_id"],
        columns="source_label",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    source_cols = [col for col in pred_wide.columns if col not in {"split", "_track6_row_id"}]
    width_parts = []
    for col in ["routing_width", "quantile_width", "q10_log", "q50_log", "q90_log"]:
        if col in long_df.columns:
            part = (
                long_df.dropna(subset=[col])
                .groupby(["split", "_track6_row_id"], as_index=False)[col]
                .first()
            )
            width_parts.append(part)
    frame = actual.merge(pred_wide, on=["split", "_track6_row_id"], how="inner")
    for part in width_parts:
        frame = frame.merge(part, on=["split", "_track6_row_id"], how="left")
    frame = frame.merge(meta, on=["split", "_track6_row_id"], how="left")
    return frame, source_cols


def evaluate_prediction(frame: pd.DataFrame, pred_col: str | pd.Series, candidate: str, policy: str, notes: str) -> list[dict[str, Any]]:
    rows = []
    for split, group in frame.groupby("split"):
        pred = group[pred_col] if isinstance(pred_col, str) else pred_col.loc[group.index]
        rows.append({
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "policy": policy,
            "split": split,
            "notes": notes,
            "row_n": int(len(group)),
            **metric_values(group["actual_log"], pred),
        })
    return rows


def actual_price(frame: pd.DataFrame) -> pd.Series:
    return np.exp(frame["actual_log"])


def mape_score(actual_log: pd.Series, pred_log: pd.Series) -> float:
    actual = np.exp(actual_log)
    pred = np.exp(pred_log)
    return float(np.mean(np.abs(actual - pred) / np.maximum(actual, 1e-9)))


def grid_weight_combinations(n: int, units: int = 20) -> Iterable[np.ndarray]:
    combo = [0] * n

    def rec(pos: int, remaining: int) -> Iterable[np.ndarray]:
        if pos == n - 1:
            combo[pos] = remaining
            yield np.array(combo, dtype=float) / units
            return
        for value in range(remaining + 1):
            combo[pos] = value
            yield from rec(pos + 1, remaining - value)

    yield from rec(0, units)


def weighted_blend(frame: pd.DataFrame, source_cols: list[str], weights: np.ndarray) -> pd.Series:
    matrix = frame[source_cols].to_numpy(dtype=float)
    return pd.Series(matrix @ weights, index=frame.index)


def build_global_ensembles(frame: pd.DataFrame, source_metrics: pd.DataFrame) -> tuple[list[pd.DataFrame], list[dict[str, Any]]]:
    prediction_frames = []
    config_rows = []
    validation = frame[frame["split"].eq("validation")]
    test = frame[frame["split"].eq("test")]
    top_sources = (
        source_metrics[source_metrics["split"].eq("validation")]
        .dropna(subset=["MAPE"])
        .sort_values(["MAPE", "MdAPE", "p95_APE"])
        .head(6)["candidate"]
        .tolist()
    )
    top_sources = [source for source in top_sources if source in frame.columns and frame[source].notna().all()]
    if len(top_sources) < 2:
        return prediction_frames, config_rows

    search_sets = [
        ("global_mape_top4", top_sources[:4], 20, "validation MAPE 최소 convex log blend"),
        ("global_mape_top5", top_sources[:5], 20, "validation MAPE 최소 convex log blend"),
        ("global_guarded_top5", top_sources[:5], 20, "MAPE 우선 + MdAPE/p95 방어 convex log blend"),
    ]
    base = source_metrics[
        (source_metrics["split"].eq("validation")) & (source_metrics["candidate"].eq(CURRENT_BASE_SOURCE))
    ]
    base_mdape = float(base["MdAPE"].iloc[0]) if not base.empty else float(source_metrics[source_metrics["split"].eq("validation")]["MdAPE"].min())
    base_p95 = float(base["p95_APE"].iloc[0]) if not base.empty else float(source_metrics[source_metrics["split"].eq("validation")]["p95_APE"].min())

    for label, sources, units, note in search_sets:
        if len(sources) < 2:
            continue
        X_val = validation[sources].to_numpy(dtype=float)
        actual_val = validation["actual_log"]
        best_score = np.inf
        best_weights = None
        best_metrics = None
        for weights in grid_weight_combinations(len(sources), units=units):
            pred = pd.Series(X_val @ weights, index=validation.index)
            metrics = metric_values(actual_val, pred)
            score = metrics["MAPE"]
            if "guarded" in label:
                score += max(0.0, metrics["MdAPE"] - base_mdape * 1.015) * 3.0
                score += max(0.0, metrics["p95_APE"] - base_p95 * 1.010) * 0.7
            if score < best_score:
                best_score = score
                best_weights = weights
                best_metrics = metrics
        if best_weights is None:
            continue
        candidate = f"wmape_{label}"
        pred_all = weighted_blend(frame, sources, best_weights)
        prediction_frames.append(pd.DataFrame({
            "candidate": candidate,
            "policy": "W-MAPE-02/03_global_weighted_blend",
            "split": frame["split"],
            "_track6_row_id": frame["_track6_row_id"],
            "pred_log": pred_all,
            "notes": note,
        }))
        config_rows.append({
            "candidate": candidate,
            "policy": "global_weighted_blend",
            "sources": json.dumps(dict(zip(sources, [round(float(w), 4) for w in best_weights])), ensure_ascii=False),
            "validation_mape": best_metrics["MAPE"],
            "validation_mdape": best_metrics["MdAPE"],
            "validation_p95": best_metrics["p95_APE"],
            "notes": note,
        })
    return prediction_frames, config_rows


def assign_quantile_segments(train: pd.Series, values: pd.Series, label: str, bins: int = 3) -> tuple[pd.Series, dict[str, Any]]:
    valid = train.dropna()
    info: dict[str, Any] = {"segment_col": label, "mode": f"q{bins}", "valid_train_rows": int(len(valid))}
    if len(valid) < 30 or valid.nunique() < bins:
        threshold = float(valid.median()) if len(valid) else 0.0
        info.update({"mode": "median_binary", "threshold": threshold})
        return pd.Series(np.where(values.fillna(threshold) >= threshold, "high", "low"), index=values.index), info
    quantiles = np.linspace(0, 1, bins + 1)[1:-1]
    cuts = sorted(set(float(x) for x in valid.quantile(quantiles).tolist()))
    if len(cuts) < 1:
        threshold = float(valid.median())
        info.update({"mode": "median_binary", "threshold": threshold})
        return pd.Series(np.where(values.fillna(threshold) >= threshold, "high", "low"), index=values.index), info
    info["cuts"] = json.dumps(cuts)
    labels = [f"bin{i + 1}" for i in range(len(cuts) + 1)]
    return pd.Series(pd.cut(values, bins=[-np.inf] + cuts + [np.inf], labels=labels).astype(str), index=values.index), info


def fit_mape_corrections(train: pd.DataFrame, base_col: str, segment_col: str, cap: float = 0.12, min_rows: int = 18) -> pd.DataFrame:
    rows = []
    grid = np.linspace(-cap, cap, 121)
    for segment, group in train.groupby(segment_col, dropna=False):
        if len(group) < min_rows:
            correction = 0.0
            score = mape_score(group["actual_log"], group[base_col]) if len(group) else np.nan
        else:
            scores = [mape_score(group["actual_log"], group[base_col] + corr) for corr in grid]
            idx = int(np.argmin(scores))
            correction = float(grid[idx])
            score = float(scores[idx])
        rows.append({
            "segment": str(segment),
            "segment_row_count": int(len(group)),
            "correction": correction,
            "validation_segment_mape": score,
            "cap": cap,
            "min_rows": min_rows,
        })
    return pd.DataFrame(rows)


def build_segment_corrections(frame: pd.DataFrame, base_sources: list[str]) -> tuple[list[pd.DataFrame], pd.DataFrame]:
    prediction_frames = []
    correction_rows = []
    segment_specs = [
        ("pred_price_bin", None, "예측 가격 구간"),
        ("log_area", "log_area", "작품 면적 구간"),
        ("artist_works_log", "artist_works_log", "작가 학습량 구간"),
        ("routing_width", "routing_width", "V8 routing width 구간"),
        ("quantile_width", "quantile_width", "Quantile width 구간"),
        ("search_quality_score", "search_quality_score", "검색 품질 구간"),
        ("source_group_news_ratio", "source_group_news_ratio", "뉴스 비중 구간"),
        ("source_group_gallery_museum_ratio", "source_group_gallery_museum_ratio", "갤러리/미술관 비중 구간"),
        ("source_group_social_blog_ratio", "source_group_social_blog_ratio", "소셜/블로그 비중 구간"),
    ]
    for base_col in base_sources:
        if base_col not in frame.columns:
            continue
        for segment_name, feature_col, label in segment_specs:
            temp = frame.copy()
            if segment_name == "pred_price_bin":
                feature_values = temp[base_col]
            else:
                if feature_col not in temp.columns:
                    continue
                feature_values = pd.to_numeric(temp[feature_col], errors="coerce")
            validation_mask = temp["split"].eq("validation")
            segments, info = assign_quantile_segments(feature_values[validation_mask], feature_values, segment_name, bins=3)
            temp["_segment"] = segments.values
            corrections = fit_mape_corrections(temp[validation_mask], base_col, "_segment")
            temp = temp.merge(corrections[["segment", "correction"]], left_on="_segment", right_on="segment", how="left")
            temp["correction"] = temp["correction"].fillna(0.0)
            pred = temp[base_col] + temp["correction"]
            candidate = f"wmape_segment_{safe_name(base_col)}_{safe_name(segment_name)}"
            prediction_frames.append(pd.DataFrame({
                "candidate": candidate,
                "policy": "W-MAPE-05/06/07/08_segment_mape_correction",
                "split": temp["split"],
                "_track6_row_id": temp["_track6_row_id"],
                "pred_log": pred,
                "notes": f"{base_col} + {label}별 validation MAPE 최소 보정",
            }))
            for row in corrections.to_dict(orient="records"):
                row.update({
                    "candidate": candidate,
                    "base_source": base_col,
                    "segment_name": segment_name,
                    "segment_label": label,
                    **info,
                })
                correction_rows.append(row)
    return prediction_frames, pd.DataFrame(correction_rows)


def build_routing_candidates(frame: pd.DataFrame, source_metrics: pd.DataFrame) -> tuple[list[pd.DataFrame], pd.DataFrame]:
    prediction_frames = []
    routing_rows = []
    top_sources = (
        source_metrics[source_metrics["split"].eq("validation")]
        .sort_values(["MAPE", "MdAPE", "p95_APE"])
        .head(8)["candidate"]
        .tolist()
    )
    top_sources = [source for source in top_sources if source in frame.columns]
    route_features = ["routing_width", "quantile_width", "log_area", "artist_works_log"]
    for feature in route_features:
        if feature not in frame.columns or len(top_sources) < 2:
            continue
        temp = frame.copy()
        values = pd.to_numeric(temp[feature], errors="coerce")
        validation_mask = temp["split"].eq("validation")
        segments, info = assign_quantile_segments(values[validation_mask], values, feature, bins=3)
        temp["_segment"] = segments.values
        route_map = {}
        for segment, group in temp[validation_mask].groupby("_segment"):
            if len(group) < 18:
                best_source = top_sources[0]
                best_mape = np.nan
            else:
                scores = [(source, mape_score(group["actual_log"], group[source])) for source in top_sources]
                best_source, best_mape = min(scores, key=lambda item: item[1])
            route_map[str(segment)] = best_source
            routing_rows.append({
                "candidate": f"wmape_route_{feature}",
                "route_feature": feature,
                "segment": str(segment),
                "selected_source": best_source,
                "validation_segment_mape": best_mape,
                "segment_row_count": int(len(group)),
                **info,
            })
        pred = pd.Series(index=temp.index, dtype=float)
        for segment, source in route_map.items():
            mask = temp["_segment"].astype(str).eq(segment)
            pred.loc[mask] = temp.loc[mask, source]
        pred = pred.fillna(temp[top_sources[0]])
        prediction_frames.append(pd.DataFrame({
            "candidate": f"wmape_route_{feature}",
            "policy": "W-MAPE-04/11_segment_model_routing",
            "split": temp["split"],
            "_track6_row_id": temp["_track6_row_id"],
            "pred_log": pred,
            "notes": f"{feature} 구간별 validation MAPE 최저 source 선택",
        }))
    return prediction_frames, pd.DataFrame(routing_rows)


def numeric_feature_columns(frame: pd.DataFrame) -> list[str]:
    preferred = [
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "log_area",
        "aspect_ratio",
        "artist_works_log",
        "artist_works_count_train",
        "has_depth",
        "is_3d_candidate",
        "is_extreme_aspect_ratio",
        "nant_material_idx",
        "routing_width",
        "quantile_width",
        "q10_log",
        "q50_log",
        "q90_log",
        "search_quality_score",
        "search_name_match_ratio",
        "search_homonym_risk_ratio",
        "provider_coverage_count",
        "search_result_count_log",
        "search_source_count_log",
        "source_group_gallery_museum_ratio",
        "source_group_news_ratio",
        "source_group_social_blog_ratio",
        "source_group_market_ratio",
        "source_group_exhibition_ratio",
        "source_group_art_general_ratio",
    ]
    return [col for col in preferred if col in frame.columns]


def build_residual_model_candidates(frame: pd.DataFrame, base_sources: list[str]) -> tuple[list[pd.DataFrame], pd.DataFrame]:
    prediction_frames = []
    model_rows = []
    numeric_cols = numeric_feature_columns(frame)
    cat_cols = [col for col in ["medium_category", "support_category", "medium_support_bucket", "nant_support", "nant_tool"] if col in frame.columns]
    train_mask = frame["split"].eq("validation")
    test_mask = frame["split"].eq("test")

    try:
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import HuberRegressor, Ridge
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except Exception:
        SimpleImputer = HuberRegressor = Pipeline = Ridge = StandardScaler = None

    try:
        from catboost import CatBoostRegressor
    except Exception:
        CatBoostRegressor = None

    for base_col in base_sources:
        if base_col not in frame.columns:
            continue
        target = (frame.loc[train_mask, "actual_log"] - frame.loc[train_mask, base_col]).clip(-0.35, 0.35)
        base_features = frame[numeric_cols].copy()
        base_features["base_pred_log"] = frame[base_col]
        base_features["base_pred_price_log"] = frame[base_col]

        if Pipeline is not None and numeric_cols:
            X_train = base_features.loc[train_mask]
            model_specs = [
                ("ridge_residual", Ridge(alpha=5.0)),
                ("huber_residual", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000)),
            ]
            for model_name, estimator in model_specs:
                pipe = Pipeline([
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", StandardScaler()),
                    ("model", estimator),
                ])
                pipe.fit(X_train, target)
                correction = pd.Series(pipe.predict(base_features), index=frame.index).clip(-0.12, 0.12)
                candidate = f"wmape_{model_name}_{safe_name(base_col)}"
                prediction_frames.append(pd.DataFrame({
                    "candidate": candidate,
                    "policy": "W-MAPE-09/10_linear_residual_model",
                    "split": frame["split"],
                    "_track6_row_id": frame["_track6_row_id"],
                    "pred_log": frame[base_col] + correction,
                    "notes": f"{base_col} residual을 {model_name}로 validation 학습 후 cap 적용",
                }))
                model_rows.append({
                    "candidate": candidate,
                    "base_source": base_col,
                    "model": model_name,
                    "feature_count": int(X_train.shape[1]),
                    "train_rows": int(train_mask.sum()),
                    "correction_cap": 0.12,
                })

        if CatBoostRegressor is not None:
            X = frame[numeric_cols + cat_cols].copy()
            X["base_pred_log"] = frame[base_col]
            for col in cat_cols:
                X[col] = X[col].astype(str).fillna("__missing__")
            cat_indices = [X.columns.get_loc(col) for col in cat_cols if col in X.columns]
            model = CatBoostRegressor(
                loss_function="MAE",
                iterations=240,
                depth=4,
                learning_rate=0.04,
                l2_leaf_reg=12.0,
                random_seed=SEED,
                verbose=False,
                allow_writing_files=False,
            )
            model.fit(X.loc[train_mask], target, cat_features=cat_indices)
            correction = pd.Series(model.predict(X), index=frame.index).clip(-0.12, 0.12)
            candidate = f"wmape_catboost_residual_{safe_name(base_col)}"
            prediction_frames.append(pd.DataFrame({
                "candidate": candidate,
                "policy": "W-MAPE-09/10_catboost_residual_model",
                "split": frame["split"],
                "_track6_row_id": frame["_track6_row_id"],
                "pred_log": frame[base_col] + correction,
                "notes": f"{base_col} residual을 CatBoost로 validation 학습 후 cap 적용",
            }))
            model_rows.append({
                "candidate": candidate,
                "base_source": base_col,
                "model": "catboost_residual",
                "feature_count": int(X.shape[1]),
                "train_rows": int(train_mask.sum()),
                "correction_cap": 0.12,
            })
    return prediction_frames, pd.DataFrame(model_rows)


def evaluate_candidate_frames(frame: pd.DataFrame, prediction_frames: list[pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows = []
    prediction_rows = []
    actual = frame[["split", "_track6_row_id", "actual_log", "artist_search_name"]].copy()
    for pred_df in prediction_frames:
        candidate = str(pred_df["candidate"].iloc[0])
        policy = str(pred_df["policy"].iloc[0])
        notes = str(pred_df["notes"].iloc[0])
        merged = actual.merge(pred_df[["split", "_track6_row_id", "pred_log"]], on=["split", "_track6_row_id"], how="inner")
        for split, group in merged.groupby("split"):
            metric_rows.append({
                "experiment_id": EXP_ID,
                "candidate": candidate,
                "policy": policy,
                "split": split,
                "notes": notes,
                "row_n": int(len(group)),
                **metric_values(group["actual_log"], group["pred_log"]),
            })
        merged["candidate"] = candidate
        merged["policy"] = policy
        merged["pred_price"] = np.exp(merged["pred_log"])
        merged["actual_price"] = np.exp(merged["actual_log"])
        merged["ape"] = np.abs(merged["actual_price"] - merged["pred_price"]) / np.maximum(merged["actual_price"], 1e-9)
        prediction_rows.append(merged)
    return pd.DataFrame(metric_rows), pd.concat(prediction_rows, ignore_index=True) if prediction_rows else pd.DataFrame()


def source_metrics(frame: pd.DataFrame, source_cols: list[str]) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    rows = []
    pred_frames = []
    for source in source_cols:
        if frame[source].isna().any():
            continue
        for split, group in frame.groupby("split"):
            rows.append({
                "experiment_id": EXP_ID,
                "candidate": source,
                "policy": "W-MAPE-01_existing_source",
                "split": split,
                "notes": "기존 Warm 예측 산출물",
                "row_n": int(len(group)),
                **metric_values(group["actual_log"], group[source]),
            })
        pred_frames.append(pd.DataFrame({
            "candidate": source,
            "policy": "W-MAPE-01_existing_source",
            "split": frame["split"],
            "_track6_row_id": frame["_track6_row_id"],
            "pred_log": frame[source],
            "notes": "기존 Warm 예측 산출물",
        }))
    return pd.DataFrame(rows), pred_frames


def bootstrap_stability(predictions: pd.DataFrame, metrics_df: pd.DataFrame, baseline: str, top_n: int = 10, n_boot: int = 800) -> pd.DataFrame:
    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "MdAPE", "p95_APE"])
    candidates = [candidate for candidate in test_metrics["candidate"].head(top_n).tolist() if candidate != baseline]
    if baseline not in set(predictions["candidate"]):
        return pd.DataFrame()
    test_pred = predictions[predictions["split"].eq("test")].copy()
    rows = []
    rng = np.random.default_rng(SEED)
    base = test_pred[test_pred["candidate"].eq(baseline)][["_track6_row_id", "actual_log", "artist_search_name", "pred_log"]].rename(columns={"pred_log": "baseline_pred_log"})
    for candidate in candidates:
        cand = test_pred[test_pred["candidate"].eq(candidate)][["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "candidate_pred_log"})
        merged = base.merge(cand, on="_track6_row_id", how="inner").reset_index(drop=True)
        if merged.empty:
            continue
        actual = np.exp(merged["actual_log"].to_numpy())
        base_ape = np.abs(actual - np.exp(merged["baseline_pred_log"].to_numpy())) / np.maximum(actual, 1e-9)
        cand_ape = np.abs(actual - np.exp(merged["candidate_pred_log"].to_numpy())) / np.maximum(actual, 1e-9)
        row_improvements = []
        n = len(merged)
        for _ in range(n_boot):
            idx = rng.integers(0, n, size=n)
            row_improvements.append(float(base_ape[idx].mean() - cand_ape[idx].mean()))
        artists = merged["artist_search_name"].fillna("__missing__").astype(str).unique()
        artist_improvements = []
        for _ in range(n_boot):
            sampled = rng.choice(artists, size=len(artists), replace=True)
            mask_parts = []
            for artist in sampled:
                idx = np.flatnonzero(merged["artist_search_name"].fillna("__missing__").astype(str).to_numpy() == artist)
                if len(idx):
                    mask_parts.append(idx)
            if not mask_parts:
                continue
            idx = np.concatenate(mask_parts)
            artist_improvements.append(float(base_ape[idx].mean() - cand_ape[idx].mean()))
        rows.append({
            "baseline": baseline,
            "candidate": candidate,
            "row_prob_mape_improvement_gt_0": float(np.mean(np.array(row_improvements) > 0)),
            "row_mean_mape_improvement": float(np.mean(row_improvements)),
            "row_p05_mape_improvement": float(np.quantile(row_improvements, 0.05)),
            "artist_prob_mape_improvement_gt_0": float(np.mean(np.array(artist_improvements) > 0)) if artist_improvements else np.nan,
            "artist_mean_mape_improvement": float(np.mean(artist_improvements)) if artist_improvements else np.nan,
            "artist_p05_mape_improvement": float(np.quantile(artist_improvements, 0.05)) if artist_improvements else np.nan,
            "bootstrap_n": n_boot,
        })
    return pd.DataFrame(rows)


def render_report(
    metrics_df: pd.DataFrame,
    source_map: pd.DataFrame,
    ensemble_config: pd.DataFrame,
    corrections: pd.DataFrame,
    routing: pd.DataFrame,
    residual_models: pd.DataFrame,
    bootstrap: pd.DataFrame,
) -> tuple[str, str]:
    base_cols = ["candidate", "policy", "split", "MAPE", "MdAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "notes"]
    source_test = metrics_df[(metrics_df["split"].eq("test")) & (metrics_df["policy"].eq("W-MAPE-01_existing_source"))].sort_values(["MAPE", "MdAPE"]).head(15)
    top_val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(20)
    top_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(25)
    best = top_test.iloc[0].to_dict() if not top_test.empty else {}
    baseline = metrics_df[(metrics_df["split"].eq("test")) & (metrics_df["candidate"].eq(CURRENT_H29_SOURCE))]
    if baseline.empty:
        baseline = metrics_df[(metrics_df["split"].eq("test")) & (metrics_df["candidate"].eq(CURRENT_BASE_SOURCE))]
    baseline_row = baseline.iloc[0].to_dict() if not baseline.empty else {}

    md = f"""# {TITLE}

- 실험 ID: `{EXP_ID}`
- 실행 시각: {datetime.now().isoformat(timespec="seconds")}
- 목적: Warm에서 MAPE를 최우선으로 줄이는 조합, 라우팅, 구간 보정, 잔차 보정 후보를 한 번에 비교한다.
- 원칙: 모든 조합 선택과 보정값은 Warm validation에서 만들고 Warm test에 그대로 적용한다.
- 현재 비교 기준: `{baseline_row.get("candidate", CURRENT_H29_SOURCE)}` / test MAPE `{baseline_row.get("MAPE", np.nan):.6f}`

## 결론 요약

- test MAPE 최상위 후보: `{best.get("candidate", "")}`
- test MAPE: `{best.get("MAPE", np.nan):.6f}`
- test MdAPE: `{best.get("MdAPE", np.nan):.6f}`
- test p95_APE: `{best.get("p95_APE", np.nan):.6f}`
- 기존 기준 대비 MAPE 개선폭: `{baseline_row.get("MAPE", np.nan) - best.get("MAPE", np.nan):.6f}`

## 기존 Warm 후보 test MAPE 순위

{markdown_table(source_test[base_cols])}

## validation MAPE 상위 후보

{markdown_table(top_val[base_cols])}

## test MAPE 상위 후보

{markdown_table(top_test[base_cols])}

## 앙상블 구성

{markdown_table(ensemble_config.head(20))}

## 구간 보정 샘플

{markdown_table(corrections.head(40))}

## 라우팅 구성

{markdown_table(routing.head(40))}

## 잔차 보정 모델

{markdown_table(residual_models)}

## 안정성 검증

{markdown_table(bootstrap.head(20))}

## 해석

- MAPE는 실제 가격 대비 오차이기 때문에, 전역 평균 개선보다 큰 오차 행의 비율을 줄이는 조합이 유리하다.
- Warm에서는 `PP-V8`/`PP-H29` 계열이 이미 강하므로 새 조합의 개선 폭은 Cold보다 작을 수 있다.
- 그래도 validation 기준으로 만든 조합이 test에서도 MAPE를 낮추면 서비스 적용 후보로 볼 수 있다.
- 단, MdAPE와 p95_APE가 같이 악화되는 후보는 MAPE 단독 개선 후보로만 보류한다.
"""

    sections = [
        ("기존 Warm 후보 test MAPE 순위", source_test[base_cols]),
        ("validation MAPE 상위 후보", top_val[base_cols]),
        ("test MAPE 상위 후보", top_test[base_cols]),
        ("앙상블 구성", ensemble_config.head(30)),
        ("구간 보정 샘플", corrections.head(80)),
        ("라우팅 구성", routing.head(80)),
        ("잔차 보정 모델", residual_models),
        ("안정성 검증", bootstrap.head(30)),
        ("source map", source_map.head(80)),
    ]
    body = "\n".join(
        f"<section><h2>{html.escape(title)}</h2>{df.to_html(index=False, escape=True)}</section>"
        for title, df in sections
    )
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(TITLE)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2937; }}
    h1 {{ margin-bottom: 8px; }}
    h2 {{ margin-top: 32px; border-bottom: 1px solid #d8dee9; padding-bottom: 8px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; margin-top: 12px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 6px 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    .summary {{ background: #f8fafc; border: 1px solid #d8dee9; padding: 14px 16px; border-radius: 6px; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>{html.escape(TITLE)}</h1>
  <div class="summary">
    <p><strong>최상위 test 후보:</strong> <code>{html.escape(str(best.get("candidate", "")))}</code></p>
    <p><strong>MAPE:</strong> {best.get("MAPE", np.nan):.6f} / <strong>MdAPE:</strong> {best.get("MdAPE", np.nan):.6f} / <strong>p95_APE:</strong> {best.get("p95_APE", np.nan):.6f}</p>
    <p><strong>비교 기준:</strong> <code>{html.escape(str(baseline_row.get("candidate", CURRENT_H29_SOURCE)))}</code> MAPE {baseline_row.get("MAPE", np.nan):.6f}</p>
  </div>
  {body}
</body>
</html>
"""
    return md, html_doc


def main() -> None:
    np.random.seed(SEED)
    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for subdir in ["outputs", "reports", "logs", "artifacts"]:
        (exp_dir / subdir).mkdir(parents=True, exist_ok=True)

    long_df, source_map = load_prediction_sources()
    meta = load_meta_features()
    frame, source_cols = build_wide_predictions(long_df, meta)
    source_metric_df, baseline_prediction_frames = source_metrics(frame, source_cols)

    base_sources = [source for source in [CURRENT_H29_SOURCE, CURRENT_BASE_SOURCE, "v8__compact_blend_mdape", "v8__deployment_single_mdape"] if source in frame.columns]
    if CURRENT_H29_SOURCE not in base_sources and CURRENT_BASE_SOURCE in frame.columns:
        base_sources.insert(0, CURRENT_BASE_SOURCE)

    ensemble_frames, ensemble_config_rows = build_global_ensembles(frame, source_metric_df)
    segment_frames, corrections = build_segment_corrections(frame, base_sources[:3])
    routing_frames, routing = build_routing_candidates(frame, source_metric_df)
    residual_frames, residual_models = build_residual_model_candidates(frame, base_sources[:2])

    all_prediction_frames = baseline_prediction_frames + ensemble_frames + segment_frames + routing_frames + residual_frames
    candidate_metric_df, candidate_predictions = evaluate_candidate_frames(frame, all_prediction_frames)
    metrics_df = pd.concat([source_metric_df, candidate_metric_df[candidate_metric_df["policy"].ne("W-MAPE-01_existing_source")]], ignore_index=True, sort=False)
    metrics_df = metrics_df.drop_duplicates(["candidate", "split"], keep="last").sort_values(["split", "MAPE", "MdAPE", "p95_APE", "candidate"]).reset_index(drop=True)
    candidate_predictions = candidate_predictions.drop_duplicates(["candidate", "split", "_track6_row_id"], keep="last")

    baseline_for_bootstrap = CURRENT_H29_SOURCE if CURRENT_H29_SOURCE in set(candidate_predictions["candidate"]) else CURRENT_BASE_SOURCE
    bootstrap = bootstrap_stability(candidate_predictions, metrics_df, baseline_for_bootstrap)
    ensemble_config = pd.DataFrame(ensemble_config_rows)

    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    candidate_predictions.to_csv(exp_dir / "outputs" / "candidate_predictions.csv", index=False)
    source_map.to_csv(exp_dir / "outputs" / "source_map.csv", index=False)
    ensemble_config.to_csv(exp_dir / "outputs" / "ensemble_config.csv", index=False)
    corrections = corrections.drop_duplicates().reset_index(drop=True)
    routing = routing.drop_duplicates().reset_index(drop=True)
    residual_models = residual_models.drop_duplicates().reset_index(drop=True)
    bootstrap = bootstrap.drop_duplicates().reset_index(drop=True)
    corrections.to_csv(exp_dir / "outputs" / "segment_corrections.csv", index=False)
    routing.to_csv(exp_dir / "outputs" / "routing_map.csv", index=False)
    residual_models.to_csv(exp_dir / "outputs" / "residual_models.csv", index=False)
    bootstrap.to_csv(exp_dir / "outputs" / "bootstrap_summary.csv", index=False)

    md, html_doc = render_report(metrics_df, source_map, ensemble_config, corrections, routing, residual_models, bootstrap)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    (exp_dir / "artifacts" / "input_paths.json").write_text(json.dumps({
        "prediction_sources": [
            {
                "prefix": src["prefix"],
                "path": str(Path(src["path"]).relative_to(REPO)),
                "metric_path": str(Path(src["metric_path"]).relative_to(REPO)),
            }
            for src in PREDICTION_SOURCES
        ],
        "split_paths": {split: str(path.relative_to(REPO)) for split, path in SPLIT_PATHS.items()},
        "feature_paths": {split: str(path.relative_to(REPO)) for split, path in FEATURE_PATHS.items()},
        "search_snapshot_path": str(SEARCH_SNAPSHOT_PATH.relative_to(REPO)),
        "search_standardized_path": str(SEARCH_STANDARDIZED_PATH.relative_to(REPO)),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    top_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(10)
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "experiment_dir": str(exp_dir.relative_to(REPO)),
        "source_candidate_n": int(len(source_cols)),
        "generated_candidate_n": int(metrics_df["candidate"].nunique()),
        "top_test": top_test[["candidate", "policy", "MAPE", "MdAPE", "p95_APE", "RMSE_log"]].to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
