#!/usr/bin/env python3
"""PP-CMETA3: strict Cold meta/external-live-search bucket validation.

This run keeps the unresolved-artist Cold harness:
- no artist_key model feature
- no same-artist price history feature
- no artist_key lookup postprocess

It tests whether artist metadata buckets, external live search/context buckets, and
artwork-meta interaction buckets improve the operational Cold candidate.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import (  # noqa: E402
    assert_no_artist_lookup_postprocess,
    assert_strict_cold_features,
    strict_cold_run_summary,
)
from run_pre_pp_experiments import BASE_EXP_DIR, metrics  # noqa: E402
from run_pp_w_experiments import META_ALL, base_feature_sets, unique  # noqa: E402
from run_pp_y_cold_combination_experiments import (  # noqa: E402
    ADDED_NUMERIC,
    add_bundle_predictions,
    add_metric,
    external_core_features,
    external_interaction_features,
    fit_predict,
    fit_quantile_bundle,
    frame_with_base_features,
    kfold_oof_base,
    lgbm_model,
    load_cold_full,
    load_search_df,
    normalize_frame,
    prediction_frame,
    search_all_features,
    width_values,
)


EXP_ID = "PP-CMETA3"
SLUG = "PP-CMETA3_cold_strict_meta_bucket_validation"
TITLE = "Cold strict 작가 메타 bucket 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"

META_BUCKET_FEATURES = [
    "artist_birth_period_bucket",
    "artist_inventory_bucket",
    "artist_followers_bucket",
    "artist_sale_ratio_bucket",
    "artist_career_stage_bucket",
    "artist_meta_completeness_bucket",
]

SEARCH_BUCKET_FEATURES = [
    "search_quality_bucket",
    "search_result_count_bucket",
    "search_art_context_bucket",
    "search_exhibition_context_bucket",
    "search_gallery_context_bucket",
    "search_homonym_risk_bucket",
    "search_context_strength_bucket",
]

COMBO_BUCKET_FEATURES = [
    "medium_birth_period_bucket",
    "size_search_quality_bucket2",
    "support_meta_completeness_bucket",
    "medium_context_strength_bucket",
    "career_size_bucket",
]


def safe_bucket(series: pd.Series, bins: list[float], labels: list[str], missing: str = "missing") -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    bucket = pd.cut(numeric, bins=bins, labels=labels, include_lowest=True)
    out = bucket.astype("string").fillna(missing)
    return out.replace({"": missing})


def safe_quantile_bucket(series: pd.Series, labels: list[str], missing: str = "missing") -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    if valid.nunique() < 3:
        return pd.Series(missing, index=series.index, dtype="string")
    qs = np.unique(np.nanquantile(valid, np.linspace(0.0, 1.0, len(labels) + 1)))
    if len(qs) <= 2:
        return pd.Series(missing, index=series.index, dtype="string")
    actual_labels = labels[: len(qs) - 1]
    bucket = pd.cut(numeric, bins=qs, labels=actual_labels, include_lowest=True, duplicates="drop")
    return bucket.astype("string").fillna(missing).replace({"": missing})


def str_col(frame: pd.DataFrame, col: str, default: str = "missing") -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="string")
    return frame[col].astype("string").fillna(default).replace({"": default})


def add_strict_buckets(frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    out_frames: list[pd.DataFrame] = []
    for frame in frames:
        out = frame.copy()
        out["artist_birth_period_bucket"] = safe_bucket(
            out.get("artist_meta_birth_year"),
            [-np.inf, 1900, 1949, 1979, np.inf],
            ["pre_1900", "1900_1949", "1950_1979", "1980_plus"],
        )
        out["artist_inventory_bucket"] = safe_quantile_bucket(
            out.get("artist_meta_total_works_log", pd.Series(index=out.index, dtype=float)),
            ["inv_low", "inv_mid", "inv_high", "inv_top"],
        )
        out["artist_followers_bucket"] = safe_quantile_bucket(
            out.get("artist_meta_followers_log", pd.Series(index=out.index, dtype=float)),
            ["followers_low", "followers_mid", "followers_high", "followers_top"],
        )
        out["artist_sale_ratio_bucket"] = safe_bucket(
            out.get("artist_meta_for_sale_ratio"),
            [-np.inf, 0.05, 0.25, 0.60, np.inf],
            ["sale_ratio_low", "sale_ratio_mid", "sale_ratio_high", "sale_ratio_top"],
        )
        out["artist_career_stage_bucket"] = str_col(out, "artist_meta_career_stage").map({
            "0.0": "career_0",
            "1.0": "career_1",
            "2.0": "career_2",
            "3.0": "career_3",
            "4.0": "career_4",
        }).astype("string").fillna(str_col(out, "artist_meta_career_stage"))

        meta_missing_cols = [
            "artist_meta_birth_year_missing",
            "artist_meta_total_works_missing",
            "artist_meta_for_sale_works_missing",
            "artist_meta_followers_missing",
            "artist_meta_career_stage_missing",
        ]
        missing_parts = []
        for col in meta_missing_cols:
            default = pd.Series(1.0, index=out.index)
            missing_parts.append(pd.to_numeric(out.get(col, default), errors="coerce").fillna(1.0))
        missing_sum = sum(missing_parts)
        out["artist_meta_completeness_bucket"] = pd.cut(
            missing_sum,
            bins=[-np.inf, 0, 2, np.inf],
            labels=["meta_complete", "meta_partial", "meta_sparse"],
            include_lowest=True,
        ).astype("string").fillna("meta_sparse")

        out["search_quality_bucket"] = safe_bucket(
            out.get("search_quality_score"),
            [-np.inf, 0.08, 0.16, 0.28, np.inf],
            ["quality_low", "quality_mid", "quality_high", "quality_top"],
        )
        out["search_result_count_bucket"] = safe_bucket(
            out.get("search_result_count"),
            [-np.inf, 0, 3, 6, np.inf],
            ["result_none", "result_low", "result_mid", "result_high"],
        )
        out["search_art_context_bucket"] = safe_bucket(
            out.get("search_art_context_count"),
            [-np.inf, 0, 1, 3, np.inf],
            ["art_none", "art_low", "art_mid", "art_high"],
        )
        out["search_exhibition_context_bucket"] = safe_bucket(
            out.get("search_exhibition_context_count"),
            [-np.inf, 0, 1, 3, np.inf],
            ["exh_none", "exh_low", "exh_mid", "exh_high"],
        )
        out["search_gallery_context_bucket"] = safe_bucket(
            out.get("search_gallery_context_count"),
            [-np.inf, 0, 1, 3, np.inf],
            ["gallery_none", "gallery_low", "gallery_mid", "gallery_high"],
        )
        out["search_homonym_risk_bucket"] = str_col(out, "search_homonym_risk_grade")

        context_sum = (
            pd.to_numeric(out.get("search_art_context_count", 0.0), errors="coerce").fillna(0.0)
            + pd.to_numeric(out.get("search_exhibition_context_count", 0.0), errors="coerce").fillna(0.0)
            + pd.to_numeric(out.get("search_gallery_context_count", 0.0), errors="coerce").fillna(0.0)
        )
        out["search_context_strength_bucket"] = pd.cut(
            context_sum,
            bins=[-np.inf, 0, 2, 5, np.inf],
            labels=["context_none", "context_low", "context_mid", "context_high"],
            include_lowest=True,
        ).astype("string").fillna("context_none")

        medium = str_col(out, "medium_category")
        support = str_col(out, "support_category")
        size = str_col(out, "size_bucket")
        out["medium_birth_period_bucket"] = medium + "__" + out["artist_birth_period_bucket"]
        out["size_search_quality_bucket2"] = size + "__" + out["search_quality_bucket"]
        out["support_meta_completeness_bucket"] = support + "__" + out["artist_meta_completeness_bucket"]
        out["medium_context_strength_bucket"] = medium + "__" + out["search_context_strength_bucket"]
        out["career_size_bucket"] = out["artist_career_stage_bucket"] + "__" + size
        out_frames.append(out)
    return out_frames


def candidate_defs() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    artwork = fs["cold_lgb"]
    baseline_full = unique(artwork + META_ALL + search_all_features() + external_interaction_features())
    meta_bucket = unique(artwork + META_ALL + META_BUCKET_FEATURES)
    search_bucket = unique(artwork + META_ALL + search_all_features() + external_interaction_features() + SEARCH_BUCKET_FEATURES)
    combo_bucket = unique(search_bucket + META_BUCKET_FEATURES + COMBO_BUCKET_FEATURES)
    bucket_only = unique(artwork + META_BUCKET_FEATURES + SEARCH_BUCKET_FEATURES + COMBO_BUCKET_FEATURES)
    return [
        ("cmeta1_repro_artwork_only", "작품 정보만", unique(artwork), "PP-CMETA1 artwork_only 재현"),
        ("cmeta1_repro_full", "작품+작가메타+외부 live 검색+전시/갤러리", baseline_full, "PP-CMETA1 strict 최상위 후보 재현"),
        ("meta_bucket_raw", "작품+작가메타+메타 bucket", meta_bucket, "작가 메타 구간화 단독 효과"),
        ("search_external_bucket", "작품+작가메타+외부 live 검색/전시+외부 live 검색 bucket", search_bucket, "외부 live 검색/전시 문맥 구간화 효과"),
        ("meta_search_combo_bucket", "작품+작가메타+외부 live 검색/전시+메타/외부 live 검색 조합 bucket", combo_bucket, "작품 조건과 메타/외부 live 검색 상태 조합 bucket 효과"),
        ("bucket_only_no_raw_meta", "작품+bucket only", bucket_only, "raw meta 없이 구간화 표현만 사용했을 때 안정성"),
    ]


def load_bucketed_frames(features: list[str], search_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    generated_buckets = set(META_BUCKET_FEATURES + SEARCH_BUCKET_FEATURES + COMBO_BUCKET_FEATURES)
    source_features = [feature for feature in features if feature not in generated_buckets]
    train, val, test = load_cold_full(source_features, search_df)
    train, val, test = add_strict_buckets([train, val, test])
    return train, val, test


def run_quantile_candidates(
    cands: list[tuple[str, str, list[str], str]],
    search_df: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    all_features = unique([feature for *_head, features, _hyp in cands for feature in features])
    train, val, test = load_bucketed_frames(all_features, search_df)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for candidate, strategy, features, hypothesis in cands:
        bundle = fit_quantile_bundle("lightgbm", train, val, test, features)
        maps.append({
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "model": "lightgbm",
            "loss_or_objective": "quantile_q10_q50_q90",
            "feature_strategy": strategy,
            "hypothesis": hypothesis,
            "n_features": len(features),
            "features": ", ".join(features),
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred = bundle["q50"][split]
            width, ratio = width_values(bundle, split)
            add_metric(rows, EXP_ID, candidate, split, frame, pred, "strict_bucket_lgbq_base_q50", {
                "model": "lightgbm",
                "feature_strategy": strategy,
                "n_features": len(features),
                "quantile_width_median": float(np.median(width)),
                "price_range_ratio_median": float(np.median(ratio)),
            })
            pred_frame = prediction_frame(EXP_ID, candidate, split, frame, pred, "strict_bucket_lgbq_base_q50", {
                "model": "lightgbm",
                "feature_strategy": strategy,
                "n_features": len(features),
            })
            preds.append(add_bundle_predictions(pred_frame, bundle, split))
    return rows, preds, maps


def metric_dict(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred_log)


def add_followup_row(
    rows: list[dict[str, Any]],
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any],
) -> None:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metric_dict(frame, pred_log),
        **extra,
    }
    rows.append(row)


def run_residual_followup(
    base_candidate: tuple[str, str, list[str], str],
    search_df: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidate, strategy, features, hypothesis = base_candidate
    train, val, test = load_bucketed_frames(features + ADDED_NUMERIC, search_df)
    bundle = fit_quantile_bundle("lightgbm", train, val, test, features)
    base_val = bundle["q50"]["validation"]
    base_test = bundle["q50"]["test"]
    val_width, _ = width_values(bundle, "validation")
    test_width, _ = width_values(bundle, "test")
    oof = kfold_oof_base("lightgbm", "quantile", train, features, alpha=0.5)
    train_residual = train["ln_price_krw"].to_numpy(dtype=float) - oof
    resid_features = unique(features + ADDED_NUMERIC)
    train_rf = normalize_frame(frame_with_base_features(train, oof, resid_features), resid_features)
    val_rf = normalize_frame(frame_with_base_features(val, base_val, resid_features, val_width), resid_features)
    test_rf = normalize_frame(frame_with_base_features(test, base_test, resid_features, test_width), resid_features)

    model = lgbm_model(resid_features, objective="regression_l1", n_estimators=320)
    model.fit(train_rf[resid_features], train_residual)
    val_resid = np.asarray(model.predict(val_rf[resid_features]), dtype=float)
    test_resid = np.asarray(model.predict(test_rf[resid_features]), dtype=float)

    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{
        "experiment_id": EXP_ID,
        "candidate": f"{candidate}_lgb_residual_clip",
        "model": "lightgbm_quantile_plus_lgb_residual",
        "loss_or_objective": "q50_plus_regression_l1_residual",
        "feature_strategy": strategy,
        "hypothesis": f"{hypothesis}; residual 보정 follow-up",
        "n_features": len(resid_features),
        "features": ", ".join(resid_features),
    }]

    best: tuple[float, float, float, float, float] | None = None
    best_params: dict[str, float] = {}
    for scale in [0.25, 0.5, 0.75]:
        for cap in [0.03, 0.05, 0.08, 0.10]:
            pred = base_val + np.clip(scale * val_resid, -cap, cap)
            mv = metric_dict(val, pred)
            score = (mv["MdAPE"], mv["MAPE"], mv["p95_APE"], scale, cap)
            if best is None or score < best:
                best = score
                best_params = {"residual_scale": scale, "residual_clip": cap}

    assert best is not None
    for split, frame, base_pred, resid, width in [
        ("validation", val, base_val, val_resid, val_width),
        ("test", test, base_test, test_resid, test_width),
    ]:
        pred = base_pred + np.clip(best_params["residual_scale"] * resid, -best_params["residual_clip"], best_params["residual_clip"])
        add_followup_row(rows, f"{candidate}_lgb_residual_clip", split, frame, pred, "strict_lgb_residual_clip", {
            "model": "lightgbm_quantile_plus_lgb_residual",
            "feature_strategy": strategy,
            "n_features": len(resid_features),
            **best_params,
        })
        pred_frame = prediction_frame(EXP_ID, f"{candidate}_lgb_residual_clip", split, frame, pred, "strict_lgb_residual_clip", {
            "model": "lightgbm_quantile_plus_lgb_residual",
            "feature_strategy": strategy,
            "n_features": len(resid_features),
            **best_params,
        })
        pred_frame["quantile_width_log"] = width
        preds.append(pred_frame)
    return rows, preds, maps


def run_guard_followup(
    base_candidate: tuple[str, str, list[str], str],
    search_df: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidate, strategy, features, hypothesis = base_candidate
    train, val, test = load_bucketed_frames(features, search_df)
    bundle = fit_quantile_bundle("lightgbm", train, val, test, features)
    q40 = fit_predict("lightgbm", "quantile", train, val, test, features, alpha=0.4)
    val_q50 = bundle["q50"]["validation"]
    test_q50 = bundle["q50"]["test"]
    val_q40 = q40["validation"]
    test_q40 = q40["test"]
    val_width, _ = width_values(bundle, "validation")
    test_width, _ = width_values(bundle, "test")
    val_quality = pd.to_numeric(val.get("search_quality_score", 0.0), errors="coerce").fillna(0.0).to_numpy(dtype=float)
    test_quality = pd.to_numeric(test.get("search_quality_score", 0.0), errors="coerce").fillna(0.0).to_numpy(dtype=float)

    best: tuple[float, float, float, float, float, float] | None = None
    best_params: dict[str, float] = {}
    for width_q in [0.50, 0.67, 0.75]:
        width_thr = float(np.quantile(val_width, width_q))
        for gap in [0.03, 0.05, 0.08, 0.10]:
            for quality_thr in [0.08, 0.16, 0.28]:
                mask = (val_width >= width_thr) & ((val_q50 - val_q40) >= gap) & (val_quality <= quality_thr)
                pred = np.where(mask, val_q40, val_q50)
                mv = metric_dict(val, pred)
                score = (mv["MdAPE"], mv["MAPE"], mv["p95_APE"], width_q, gap, quality_thr)
                if best is None or score < best:
                    best = score
                    best_params = {
                        "width_quantile": width_q,
                        "width_threshold": width_thr,
                        "q50_q40_gap": gap,
                        "search_quality_max": quality_thr,
                    }
    assert best is not None
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{
        "experiment_id": EXP_ID,
        "candidate": f"{candidate}_guard_only_q40",
        "model": "lightgbm_quantile_guard_only",
        "loss_or_objective": "q50_or_q40_guard",
        "feature_strategy": strategy,
        "hypothesis": f"{hypothesis}; artist_key lookup 없는 보수 후보 조건부 선택",
        "n_features": len(features),
        "features": ", ".join(features),
    }]
    for split, frame, q50, q40_pred, width, quality in [
        ("validation", val, val_q50, val_q40, val_width, val_quality),
        ("test", test, test_q50, test_q40, test_width, test_quality),
    ]:
        mask = (
            (width >= best_params["width_threshold"])
            & ((q50 - q40_pred) >= best_params["q50_q40_gap"])
            & (quality <= best_params["search_quality_max"])
        )
        pred = np.where(mask, q40_pred, q50)
        add_followup_row(rows, f"{candidate}_guard_only_q40", split, frame, pred, "strict_guard_only_q40", {
            "model": "lightgbm_quantile_guard_only",
            "feature_strategy": strategy,
            "n_features": len(features),
            "guard_rate": float(mask.mean()) if len(mask) else 0.0,
            **best_params,
        })
        pred_frame = prediction_frame(EXP_ID, f"{candidate}_guard_only_q40", split, frame, pred, "strict_guard_only_q40", {
            "model": "lightgbm_quantile_guard_only",
            "feature_strategy": strategy,
            "n_features": len(features),
            "guard_rate": float(mask.mean()) if len(mask) else 0.0,
            **best_params,
        })
        pred_frame["quantile_width_log"] = width
        pred_frame["q40_log"] = q40_pred
        pred_frame["q50_log"] = q50
        pred_frame["guard_applied"] = mask
        preds.append(pred_frame)
    return rows, preds, maps


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_empty_"
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            value = row[col]
            vals.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def html_table(df: pd.DataFrame, cols: list[str]) -> str:
    head = "".join(f"<th>{html.escape(col)}</th>" for col in cols)
    body = []
    for _, row in df[cols].iterrows():
        cells = []
        for col in cols:
            value = row[col]
            text = f"{value:.6f}" if isinstance(value, float) else str(value)
            cells.append(f"<td>{html.escape(text)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [json_clean(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if pd.isna(value):
        return None
    return value


def main() -> None:
    for path in [OUT, REPORTS, ARTIFACTS]:
        path.mkdir(parents=True, exist_ok=True)

    search_df = load_search_df()
    cands = candidate_defs()
    for candidate, _strategy, features, _hypothesis in cands:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{candidate}")
    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)

    metric_rows, prediction_frames, feature_maps = run_quantile_candidates(cands, search_df)
    metrics_df = pd.DataFrame(metric_rows)
    validation = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    best_base_name = str(validation.iloc[0]["candidate"])
    best_base = next(c for c in cands if c[0] == best_base_name)

    residual_rows, residual_preds, residual_maps = run_residual_followup(best_base, search_df)
    guard_rows, guard_preds, guard_maps = run_guard_followup(best_base, search_df)
    metric_rows.extend(residual_rows)
    metric_rows.extend(guard_rows)
    prediction_frames.extend(residual_preds)
    prediction_frames.extend(guard_preds)
    feature_maps.extend(residual_maps)
    feature_maps.extend(guard_maps)

    metrics_df = pd.DataFrame(metric_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    feature_map_df = pd.DataFrame(feature_maps)

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions.to_csv(OUT / "predictions.csv", index=False)
    feature_map_df.to_csv(OUT / "feature_map.csv", index=False)

    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).reset_index(drop=True)
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).reset_index(drop=True)
    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "design": {
            "uses_same_artist_price_history": False,
            "uses_artist_key_as_model_feature": False,
            "uses_per_artist_lookup_postprocess": False,
            "uses_artist_meta_buckets": True,
            "uses_external_live_search_buckets": True,
            "uses_combo_buckets": True,
            "live_search_in_this_run": False,
        },
        "validation_selected_base_candidate": best_base_name,
        "best_test_candidate": test.iloc[0].to_dict() if not test.empty else {},
        "baseline_reference": {
            "PP-CMETA1_best_strict": {
                "candidate": "artwork_artist_meta_search_external_lgbq",
                "MdAPE": 0.44214745036112113,
                "MAPE": 1.0484047531277625,
                "p95_APE": 3.353732420489309,
            }
        },
    })
    summary = json_clean(summary)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")

    metric_cols = [
        "candidate",
        "split",
        "policy",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "n_features",
        "feature_strategy",
    ]
    map_cols = ["candidate", "model", "loss_or_objective", "n_features", "feature_strategy", "hypothesis"]
    report_md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- strict Cold 조건: `artist_key`, 같은 작가 가격 통계, artist_key lookup 후처리 미사용.",
        "- 목적: 작가 메타/외부 live 검색/작품 bucket이 unresolved-artist Cold 성능을 개선하는지 확인.",
        "- 외부 live 검색 피처는 이번 실행에서 실제 live 호출이 아니라, live 검색과 같은 schema로 저장된 동결 cache를 사용했다.",
        f"- validation 선택 base 후보: `{best_base_name}`",
        "",
        "## Test 결과",
        md_table(test[metric_cols], metric_cols),
        "",
        "## Validation 결과",
        md_table(val[metric_cols], metric_cols),
        "",
        "## 후보별 피처 설계",
        md_table(feature_map_df[map_cols], map_cols),
        "",
        "## 해석 기준",
        "- `cmeta1_repro_full`은 PP-CMETA1 strict 최상위 후보 재현 기준이다.",
        "- bucket 후보는 이 기준 대비 MdAPE/MAPE/p95가 개선되는지 본다.",
        "- residual/guard follow-up은 validation에서 선택한 bucket 후보에만 적용했다.",
        "- 모든 후보는 artist_key lookup 없이 동작하므로 strict Cold 운영 후보로 해석 가능하다.",
    ])
    (REPORTS / "result_report.md").write_text(report_md, encoding="utf-8")

    report_html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(TITLE)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #17202a; }}
    table {{ border-collapse: collapse; margin: 16px 0; width: 100%; font-size: 13px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 7px 9px; text-align: left; vertical-align: top; }}
    th {{ background: #edf2f7; }}
    code {{ background: #eef2f7; padding: 1px 4px; border-radius: 4px; }}
    .note {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 12px 16px; margin: 18px 0; }}
  </style>
</head>
<body>
  <h1>{html.escape(TITLE)}</h1>
  <div class="note">artist_key와 같은 작가 가격 이력 없이, 작품정보 + 작가 메타/외부 live 검색 bucket만으로 검증한 strict Cold 실험이다. 이번 실행은 동결 cache를 사용했다.</div>
  <h2>Test 결과</h2>
  {html_table(test, metric_cols)}
  <h2>Validation 결과</h2>
  {html_table(val, metric_cols)}
  <h2>후보별 피처 설계</h2>
  {html_table(feature_map_df, map_cols)}
</body>
</html>
"""
    (REPORTS / "result_report.html").write_text(report_html, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
