#!/usr/bin/env python3
"""PP-CMETA4: strict Cold user-entered artist metadata only validation.

This experiment reselects Cold candidates after pausing external live search.
It forbids:
- artist_key as a feature
- same-artist price history
- artist_key lookup postprocess
- search_* features

It compares artwork-only, user-enterable artist metadata, metadata buckets,
and optional user-enterable profile context such as exhibition/gallery fields.
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
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import META_ALL, base_feature_sets, load_cold_with_meta, unique  # noqa: E402
from run_pp_x_gallery_exhibition_revalidation import (  # noqa: E402
    EXHIBITION_NUMERIC,
    EXTERNAL_INTERACTIONS_CATEGORICAL,
    EXTERNAL_INTERACTIONS_NUMERIC,
    GALLERY_CATEGORICAL,
    GALLERY_NUMERIC,
    add_external_features,
)
from run_pp_y_cold_combination_experiments import (  # noqa: E402
    ADDED_NUMERIC,
    add_bundle_predictions,
    add_metric,
    fit_predict,
    fit_quantile_bundle,
    frame_with_base_features,
    kfold_oof_base,
    lgbm_model,
    normalize_frame,
    prediction_frame,
    width_values,
)


EXP_ID = "PP-CMETA4"
SLUG = "PP-CMETA4_user_input_meta_only"
TITLE = "Cold 사용자 입력 작가 메타 전용 재선정"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_cmeta4_user_input_meta_only_summary.md"

USER_META_CORE = [
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_followers",
    "artist_meta_career_stage",
    "artist_meta_total_works_log",
    "artist_meta_followers_log",
    "artist_meta_birth_year_missing",
    "artist_meta_total_works_missing",
    "artist_meta_followers_missing",
    "artist_meta_career_stage_missing",
    "artist_meta_is_p1_flag",
    "artist_meta_has_international_flag",
    "artist_meta_nationality",
]

PROFILE_CONTEXT = unique(
    EXHIBITION_NUMERIC
    + GALLERY_NUMERIC
    + GALLERY_CATEGORICAL
    + EXTERNAL_INTERACTIONS_NUMERIC
    + EXTERNAL_INTERACTIONS_CATEGORICAL
)

META_BUCKET_FEATURES = [
    "artist_birth_period_bucket",
    "artist_inventory_bucket",
    "artist_followers_bucket",
    "artist_career_stage_bucket",
    "artist_meta_completeness_bucket",
]

PROFILE_BUCKET_FEATURES = [
    "artist_exhibition_bucket",
    "gallery_tier_bucket",
    "profile_context_bucket",
]

COMBO_BUCKET_FEATURES = [
    "medium_birth_period_bucket",
    "support_meta_completeness_bucket",
    "career_size_bucket",
    "size_profile_context_bucket",
]

GENERATED_BUCKET_FEATURES = META_BUCKET_FEATURES + PROFILE_BUCKET_FEATURES + COMBO_BUCKET_FEATURES


def assert_no_search_features(features: list[str], *, context: str) -> None:
    forbidden = sorted(feature for feature in features if feature.startswith("search_"))
    if forbidden:
        raise ValueError(f"{context} includes search features, which are forbidden in {EXP_ID}: {forbidden}")


def safe_bucket(series: pd.Series, bins: list[float], labels: list[str], missing: str = "missing") -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    bucket = pd.cut(numeric, bins=bins, labels=labels, include_lowest=True)
    return bucket.astype("string").fillna(missing).replace({"": missing})


def safe_quantile_bucket(series: pd.Series, labels: list[str], missing: str = "missing") -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    if valid.nunique() < 3:
        return pd.Series(missing, index=series.index, dtype="string")
    qs = np.unique(np.nanquantile(valid, np.linspace(0.0, 1.0, len(labels) + 1)))
    if len(qs) <= 2:
        return pd.Series(missing, index=series.index, dtype="string")
    bucket = pd.cut(numeric, bins=qs, labels=labels[: len(qs) - 1], include_lowest=True, duplicates="drop")
    return bucket.astype("string").fillna(missing).replace({"": missing})


def str_col(frame: pd.DataFrame, col: str, default: str = "missing") -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="string")
    return frame[col].astype("string").fillna(default).replace({"": default})


def add_user_meta_buckets(frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
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
        out["artist_career_stage_bucket"] = safe_bucket(
            out.get("artist_meta_career_stage"),
            [-np.inf, 5, 15, 30, np.inf],
            ["career_new", "career_early", "career_mid", "career_long"],
        )
        meta_missing_cols = [
            "artist_meta_birth_year_missing",
            "artist_meta_total_works_missing",
            "artist_meta_followers_missing",
            "artist_meta_career_stage_missing",
        ]
        missing_sum = sum(
            pd.to_numeric(out.get(col, pd.Series(1.0, index=out.index)), errors="coerce").fillna(1.0)
            for col in meta_missing_cols
        )
        out["artist_meta_completeness_bucket"] = pd.cut(
            missing_sum,
            bins=[-np.inf, 0, 2, np.inf],
            labels=["meta_complete", "meta_partial", "meta_sparse"],
            include_lowest=True,
        ).astype("string").fillna("meta_sparse")

        exhibition_total = pd.to_numeric(out.get("artist_exhibition_total_count", 0.0), errors="coerce").fillna(0.0)
        gallery_any = pd.to_numeric(out.get("gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0)
        gallery_score = pd.to_numeric(out.get("gallery_tier_validated_score", 0.0), errors="coerce").fillna(0.0)
        out["artist_exhibition_bucket"] = pd.cut(
            exhibition_total,
            bins=[-np.inf, 0, 2, 8, np.inf],
            labels=["exh_none", "exh_low", "exh_mid", "exh_high"],
            include_lowest=True,
        ).astype("string").fillna("exh_none")
        out["gallery_tier_bucket"] = np.where(
            gallery_any <= 0,
            "gallery_missing",
            pd.cut(
                gallery_score,
                bins=[-np.inf, 0.33, 0.66, np.inf],
                labels=["gallery_low", "gallery_mid", "gallery_high"],
                include_lowest=True,
            ).astype("string").fillna("gallery_low"),
        )
        profile_strength = exhibition_total.clip(lower=0) + 2.0 * gallery_any
        out["profile_context_bucket"] = pd.cut(
            profile_strength,
            bins=[-np.inf, 0, 3, 10, np.inf],
            labels=["profile_none", "profile_low", "profile_mid", "profile_high"],
            include_lowest=True,
        ).astype("string").fillna("profile_none")

        medium = str_col(out, "medium_category")
        support = str_col(out, "support_category")
        size = str_col(out, "size_bucket")
        out["medium_birth_period_bucket"] = medium + "__" + out["artist_birth_period_bucket"]
        out["support_meta_completeness_bucket"] = support + "__" + out["artist_meta_completeness_bucket"]
        out["career_size_bucket"] = out["artist_career_stage_bucket"] + "__" + size
        out["size_profile_context_bucket"] = size + "__" + out["profile_context_bucket"]
        out_frames.append(out)
    return out_frames


def candidate_defs() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    artwork = fs["cold_lgb"]
    core = unique(artwork + USER_META_CORE)
    core_bucket = unique(core + META_BUCKET_FEATURES + ["medium_birth_period_bucket", "support_meta_completeness_bucket", "career_size_bucket"])
    full = unique(artwork + META_ALL)
    full_bucket = unique(full + META_BUCKET_FEATURES + ["medium_birth_period_bucket", "support_meta_completeness_bucket", "career_size_bucket"])
    profile = unique(core + PROFILE_CONTEXT)
    profile_bucket = unique(profile + META_BUCKET_FEATURES + PROFILE_BUCKET_FEATURES + COMBO_BUCKET_FEATURES)
    return [
        ("artwork_only", "작품 정보만", unique(artwork), "사용자 작가 메타가 없을 때의 기준"),
        ("user_meta_core", "작품+사용자 입력 core 작가 메타", core, "운영 입력 가능성이 높은 작가 메타 효과"),
        ("user_meta_core_bucket", "작품+사용자 입력 core 작가 메타+메타 bucket", core_bucket, "작가 메타를 구간화해 안정화"),
        ("existing_meta_full", "작품+기존 작가 메타 전체", full, "기존 메타 전체를 search 없이 사용한 참고 후보"),
        ("existing_meta_full_bucket", "작품+기존 작가 메타 전체+메타 bucket", full_bucket, "기존 메타 전체 구간화 참고 후보"),
        ("manual_profile_context", "작품+사용자 입력 작가 메타+전시/갤러리 문맥", profile, "사용자가 알고 있는 전시/갤러리 정보까지 입력할 때의 후보"),
        ("manual_profile_context_bucket", "작품+사용자 입력 작가 메타+전시/갤러리 문맥+bucket", profile_bucket, "전시/갤러리와 작가 메타 구간화 후보"),
    ]


def load_user_meta_frames(features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source_features = [feature for feature in features if feature not in GENERATED_BUCKET_FEATURES]
    base_source_features = [
        feature
        for feature in source_features
        if feature not in PROFILE_CONTEXT and feature not in ADDED_NUMERIC
    ]
    train, val, test = load_cold_with_meta(base_source_features)
    train, val, test = add_external_features([train, val, test])
    train, val, test = add_user_meta_buckets([train, val, test])
    return train, val, test


def run_quantile_candidates(
    cands: list[tuple[str, str, list[str], str]],
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    all_features = unique([feature for *_head, features, _hyp in cands for feature in features])
    train, val, test = load_user_meta_frames(all_features)
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
            add_metric(rows, EXP_ID, candidate, split, frame, pred, "strict_user_meta_lgbq_base_q50", {
                "model": "lightgbm",
                "feature_strategy": strategy,
                "n_features": len(features),
                "quantile_width_median": float(np.median(width)),
                "price_range_ratio_median": float(np.median(ratio)),
            })
            pred_frame = prediction_frame(EXP_ID, candidate, split, frame, pred, "strict_user_meta_lgbq_base_q50", {
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
    rows.append({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metric_dict(frame, pred_log),
        **extra,
    })


def run_residual_followup(
    base_candidate: tuple[str, str, list[str], str],
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidate, strategy, features, hypothesis = base_candidate
    train, val, test = load_user_meta_frames(features + ADDED_NUMERIC)
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
        "hypothesis": f"{hypothesis}; search 없는 residual 보정",
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
        add_followup_row(rows, f"{candidate}_lgb_residual_clip", split, frame, pred, "strict_user_meta_lgb_residual_clip", {
            "model": "lightgbm_quantile_plus_lgb_residual",
            "feature_strategy": strategy,
            "n_features": len(resid_features),
            **best_params,
        })
        pred_frame = prediction_frame(EXP_ID, f"{candidate}_lgb_residual_clip", split, frame, pred, "strict_user_meta_lgb_residual_clip", {
            "model": "lightgbm_quantile_plus_lgb_residual",
            "feature_strategy": strategy,
            "n_features": len(resid_features),
            **best_params,
        })
        pred_frame["quantile_width_log"] = width
        preds.append(pred_frame)
    return rows, preds, maps


def run_search_free_guard_followup(
    base_candidate: tuple[str, str, list[str], str],
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidate, strategy, features, hypothesis = base_candidate
    train, val, test = load_user_meta_frames(features)
    bundle = fit_quantile_bundle("lightgbm", train, val, test, features)
    q40 = fit_predict("lightgbm", "quantile", train, val, test, features, alpha=0.4)
    val_q50 = bundle["q50"]["validation"]
    test_q50 = bundle["q50"]["test"]
    val_q40 = q40["validation"]
    test_q40 = q40["test"]
    val_width, _ = width_values(bundle, "validation")
    test_width, _ = width_values(bundle, "test")
    val_meta_missing = pd.to_numeric(val.get("artist_meta_completeness_bucket").astype("string").eq("meta_sparse"), errors="coerce").fillna(0.0).to_numpy(dtype=float)
    test_meta_missing = pd.to_numeric(test.get("artist_meta_completeness_bucket").astype("string").eq("meta_sparse"), errors="coerce").fillna(0.0).to_numpy(dtype=float)

    best: tuple[float, float, float, float, float, float] | None = None
    best_params: dict[str, float] = {}
    for width_q in [0.50, 0.67, 0.75]:
        width_thr = float(np.quantile(val_width, width_q))
        for gap in [0.03, 0.05, 0.08, 0.10]:
            for require_sparse in [0.0, 1.0]:
                sparse_mask = val_meta_missing >= 1.0 if require_sparse else np.ones_like(val_meta_missing, dtype=bool)
                mask = (val_width >= width_thr) & ((val_q50 - val_q40) >= gap) & sparse_mask
                pred = np.where(mask, val_q40, val_q50)
                mv = metric_dict(val, pred)
                score = (mv["MdAPE"], mv["MAPE"], mv["p95_APE"], width_q, gap, require_sparse)
                if best is None or score < best:
                    best = score
                    best_params = {
                        "width_quantile": width_q,
                        "width_threshold": width_thr,
                        "q50_q40_gap": gap,
                        "require_meta_sparse": require_sparse,
                    }
    assert best is not None
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{
        "experiment_id": EXP_ID,
        "candidate": f"{candidate}_search_free_guard_q40",
        "model": "lightgbm_quantile_guard_only",
        "loss_or_objective": "q50_or_q40_guard",
        "feature_strategy": strategy,
        "hypothesis": f"{hypothesis}; search 없이 Quantile 폭과 메타 완성도로 q40 보수 후보 조건부 선택",
        "n_features": len(features),
        "features": ", ".join(features),
    }]
    for split, frame, q50, q40_pred, width, sparse in [
        ("validation", val, val_q50, val_q40, val_width, val_meta_missing),
        ("test", test, test_q50, test_q40, test_width, test_meta_missing),
    ]:
        sparse_mask = sparse >= 1.0 if best_params["require_meta_sparse"] else np.ones_like(sparse, dtype=bool)
        mask = (width >= best_params["width_threshold"]) & ((q50 - q40_pred) >= best_params["q50_q40_gap"]) & sparse_mask
        pred = np.where(mask, q40_pred, q50)
        add_followup_row(rows, f"{candidate}_search_free_guard_q40", split, frame, pred, "strict_user_meta_search_free_guard_q40", {
            "model": "lightgbm_quantile_guard_only",
            "feature_strategy": strategy,
            "n_features": len(features),
            "guard_rate": float(mask.mean()) if len(mask) else 0.0,
            **best_params,
        })
        pred_frame = prediction_frame(EXP_ID, f"{candidate}_search_free_guard_q40", split, frame, pred, "strict_user_meta_search_free_guard_q40", {
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
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)

    cands = candidate_defs()
    for candidate, _strategy, features, _hypothesis in cands:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{candidate}")
        assert_no_search_features(features, context=f"{EXP_ID}:{candidate}")
    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)

    metric_rows, prediction_frames, feature_maps = run_quantile_candidates(cands)
    metrics_df = pd.DataFrame(metric_rows)
    validation = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    best_base_name = str(validation.iloc[0]["candidate"])
    best_base = next(c for c in cands if c[0] == best_base_name)

    followup_bases = [best_base]
    for name in ["user_meta_core_bucket"]:
        extra_base = next((cand for cand in cands if cand[0] == name), None)
        if extra_base is not None and extra_base[0] not in {base[0] for base in followup_bases}:
            followup_bases.append(extra_base)
    for followup_base in followup_bases:
        residual_rows, residual_preds, residual_maps = run_residual_followup(followup_base)
        guard_rows, guard_preds, guard_maps = run_search_free_guard_followup(followup_base)
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
    selected = test.iloc[0].to_dict() if not test.empty else {}
    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "allowed_artist_information": [
            "user-entered non-price artist_meta_* fields",
            "user-entered or approved-cache exhibition/gallery fields for profile-context challengers",
        ],
        "design": {
            "uses_same_artist_price_history": False,
            "uses_artist_key_as_model_feature": False,
            "uses_per_artist_lookup_postprocess": False,
            "uses_search_features": False,
            "uses_external_live_search": False,
            "uses_user_enterable_artist_meta": True,
            "uses_artist_meta_buckets": True,
            "uses_manual_profile_context_candidates": True,
        },
        "validation_selected_base_candidate": best_base_name,
        "best_test_candidate": selected,
        "recommended_official_candidate": {
            "candidate": "user_meta_core_bucket",
            "reason": "search-free, artist_key-free, uses user-enterable core artist metadata, and improves artwork-only without the p95 blow-up seen in profile-context candidates",
        },
        "optional_conservative_candidate": {
            "candidate": "user_meta_core_bucket_search_free_guard_q40",
            "reason": "lower p95 than user_meta_core_bucket, but worse MdAPE/MAPE; suitable as a conservative display or review-priority candidate, not the primary point estimate",
        },
        "candidate_count": int(metrics_df["candidate"].nunique()),
        "reference": {
            "PP-CMETA3_search_external_bucket_test": {
                "candidate": "search_external_bucket",
                "MdAPE": 0.4405492129795688,
                "MAPE": 1.0376326155477198,
                "p95_APE": 3.3943354548035987,
                "status": "external search/cache dependent; not official while live search is paused",
            },
            "PP-CMETA3_meta_bucket_raw_test": {
                "candidate": "meta_bucket_raw",
                "MdAPE": 0.468331,
                "MAPE": 1.094027,
                "p95_APE": 3.003857,
            },
        },
    })
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    cols = ["candidate", "split", "policy", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "n_features", "feature_strategy"]
    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- strict Cold 조건: `artist_key`, 같은 작가 가격 통계, `artist_key` lookup 후처리, `search_*` 피처 미사용.",
        "- 목적: 외부 live 검색을 보류한 상태에서 사용자 입력 가능 작가 메타와 작품 정보만으로 쓸 Cold 후보를 재선정한다.",
        f"- validation 선택 base 후보: `{best_base_name}`",
        f"- test 기준 최상위 후보: `{selected.get('candidate', '')}`",
        "",
        "## Test 결과",
        md_table(test, cols),
        "",
        "## Validation 결과",
        md_table(val, cols),
        "",
        "## 후보별 피처 설계",
        md_table(feature_map_df, ["candidate", "model", "loss_or_objective", "n_features", "feature_strategy", "hypothesis"]),
        "",
        "## 운영 권장안",
        "",
        "- 공식 Cold 기본 후보는 `user_meta_core_bucket`을 우선 권장한다.",
        "- 이유: `search_*`, `artist_key`, 같은 작가 가격 이력 없이 동작하면서 작품 only 대비 MdAPE/MAPE/p95가 모두 개선된다.",
        "- `manual_profile_context` 계열은 MdAPE가 가장 낮지만 p95가 크게 악화되므로 기본 후보로 두지 않는다. 사용자가 전시/갤러리 정보를 입력하더라도 검수 또는 별도 후보로만 관리한다.",
        "- `user_meta_core_bucket_search_free_guard_q40`는 p95를 낮추지만 MdAPE/MAPE가 손실되므로 기본 예측값보다 보수 참고값이나 검수 우선순위 후보에 가깝다.",
        "- `existing_meta_full_bucket`은 MAPE/p95가 좋지만 기존 메타 전체에 의존한다. 운영 입력 폼으로 동일 필드를 안정적으로 받을 수 있을 때만 별도 후보로 검토한다.",
        "",
        "## 해석 기준",
        "- `artwork_only`는 작가 메타가 전혀 없을 때의 기준이다.",
        "- `user_meta_core` 계열은 운영 입력 폼에서 직접 받을 수 있는 작가 메타 중심 후보이다.",
        "- `manual_profile_context` 계열은 사용자가 전시/갤러리 정보를 직접 입력하거나 승인 cache로 채웠을 때만 쓸 수 있는 후보이다.",
        "- 모든 후보는 `search_*` 피처를 금지하므로 외부 live 검색 중단 조건과 양립한다.",
        "- residual/guard follow-up은 validation에서 선택된 base 후보와 실제 운영 core 후보인 `user_meta_core_bucket`에 적용했다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;margin:12px 0;width:100%}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}td{{vertical-align:top}}code{{background:#f3f4f6;padding:1px 4px;border-radius:4px}}</style>
</head><body><h1>{html.escape(TITLE)}</h1>
<p>- 작성일: {html.escape(str(summary['created_at']))}</p>
<p>- strict Cold 조건: <code>artist_key</code>, 같은 작가 가격 통계, <code>artist_key</code> lookup 후처리, <code>search_*</code> 피처 미사용.</p>
<p>- validation 선택 base 후보: <code>{html.escape(best_base_name)}</code></p>
<p>- test 기준 최상위 후보: <code>{html.escape(str(selected.get('candidate', '')))}</code></p>
<h2>Test 결과</h2>{html_table(test, cols)}
<h2>Validation 결과</h2>{html_table(val, cols)}
<h2>후보별 피처 설계</h2>{html_table(feature_map_df, ['candidate', 'model', 'loss_or_objective', 'n_features', 'feature_strategy', 'hypothesis'])}
<h2>운영 권장안</h2>
<ul>
<li>공식 Cold 기본 후보는 <code>user_meta_core_bucket</code>을 우선 권장한다.</li>
<li><code>manual_profile_context</code> 계열은 MdAPE가 낮지만 p95가 크게 악화되어 기본 후보로 두지 않는다.</li>
<li><code>user_meta_core_bucket_search_free_guard_q40</code>는 보수 참고값 또는 검수 우선순위 후보에 가깝다.</li>
</ul>
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
