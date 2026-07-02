#!/usr/bin/env python3
"""PP-CSIM24: strict Cold similar-neighbor residual correction.

This tests a replacement for forbidden per-artist search_delta_lookup:

    base Cold prediction + correction from similar artwork / similar artist-meta
    neighbors' out-of-fold residuals

Strict Cold contract:
- no artist_key feature
- no same-artist price history feature
- no artist_key lookup postprocess
- no search_* or external live search features

For the train reference pool, residuals are generated out-of-fold. Validation
and test corrections use only those train OOF residuals and inference-time
similarity features, never validation/test labels.
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
from lightgbm import LGBMRegressor
from sklearn.model_selection import KFold
from sklearn.neighbors import NearestNeighbors

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
import run_pp_w_experiments as ppw  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import add_user_meta_buckets, candidate_defs, load_user_meta_frames  # noqa: E402
from run_pp_cmeta5_user_meta_robustness_validation import paired_bootstrap  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    html_table,
    json_clean,
    lgbm_quantile_model,
    md_table,
    normalize_for_model,
    similarity_preprocessor,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, GENERATED, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import engineer_artist_meta  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM24"
SLUG = "PP-CSIM24_cold_similarity_neighbor_residual_correction"
TITLE = "Cold 유사 이웃 잔차 보정 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim24_cold_similarity_neighbor_residual_correction_summary.md"

BASE_TOP_K = 160
OOF_SPLITS = 5
NEIGHBOR_KS = [40, 80, 160, 320]
STRENGTHS = [0.25, 0.50, 0.75, 1.00]
CAPS = [0.05, 0.10, 0.18, 0.25]
SPLIT_DIR = REPO / "data" / "track6_split_with_year_type_edition_size"
FEATURE_CANDIDATES_WITH_META = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year_type_edition_size.csv"


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def add_generated_buckets(frame: pd.DataFrame, *, size_edges: list[float] | None = None) -> tuple[pd.DataFrame, list[float]]:
    out = frame.copy()
    log_area = pd.to_numeric(out.get("log_area"), errors="coerce")
    edges = size_edges or [-np.inf, *np.nanquantile(log_area.dropna(), [0.2, 0.4, 0.6, 0.8]).tolist(), np.inf]
    labels = ["q1", "q2", "q3", "q4", "q5"]
    if len(np.unique(edges)) == len(edges):
        out["size_bucket"] = pd.cut(log_area, bins=edges, labels=labels, include_lowest=True).astype(str)
        out.loc[log_area.isna(), "size_bucket"] = "__MISSING__"
    else:
        out["size_bucket"] = "__MISSING__"

    aspect = pd.to_numeric(out.get("aspect_ratio"), errors="coerce")
    out["shape_bucket"] = pd.cut(
        aspect,
        bins=[-np.inf, 0.75, 1.33, np.inf],
        labels=["portrait", "square", "landscape"],
        include_lowest=True,
    ).astype(str)
    out.loc[aspect.isna(), "shape_bucket"] = "__MISSING__"

    medium = out.get("medium_category", pd.Series("__MISSING__", index=out.index)).astype("string").fillna("__MISSING__")
    support = out.get("support_category", pd.Series("__MISSING__", index=out.index)).astype("string").fillna("__MISSING__")
    out["medium_size_bucket"] = medium.astype(str) + "__" + out["size_bucket"].astype(str)
    out["support_size_bucket"] = support.astype(str) + "__" + out["size_bucket"].astype(str)
    out["medium_shape_bucket"] = medium.astype(str) + "__" + out["shape_bucket"].astype(str)
    out["is_large_2d"] = ((out["size_bucket"].eq("q5")) & (pd.to_numeric(out.get("has_depth"), errors="coerce").fillna(0) <= 0)).astype(float)
    out["is_large_3d"] = ((out["size_bucket"].eq("q5")) & (pd.to_numeric(out.get("has_depth"), errors="coerce").fillna(0) > 0)).astype(float)

    for col in GENERATED:
        if col not in out.columns:
            out[col] = "__MISSING__"
    return out, edges


def load_split_frames(required_features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = [
        pd.read_csv(SPLIT_DIR / "track6_train.csv", low_memory=False),
        pd.read_csv(SPLIT_DIR / "track6_val_cold.csv", low_memory=False),
        pd.read_csv(SPLIT_DIR / "track6_test_cold.csv", low_memory=False),
    ]
    out_frames: list[pd.DataFrame] = []
    size_edges: list[float] | None = None
    for frame in frames:
        out = frame.copy()
        if "_track6_row_id" not in out.columns:
            out["_track6_row_id"] = out["track4_source_row_index"]
        out["_track6_row_id"] = pd.to_numeric(out["_track6_row_id"], errors="coerce").astype(int)
        out = engineer_artist_meta(out)
        out, size_edges = add_generated_buckets(out, size_edges=size_edges)
        for col in [
            "artist_exhibition_total_count",
            "gallery_tier_any_available_flag",
            "gallery_tier_validated_score",
        ]:
            if col not in out.columns:
                out[col] = 0.0
        out_frames.append(out)
    out_frames = add_user_meta_buckets(out_frames)

    needed = unique(["_track6_row_id", "price_krw", "ln_price_krw"] + required_features)
    missing = sorted(col for col in needed if any(col not in frame.columns for frame in out_frames))
    if missing:
        raise ValueError(f"Missing required split columns after feature engineering: {missing}")
    return tuple(frame[needed].copy() for frame in out_frames)  # type: ignore[return-value]


def fit_q_model(train: pd.DataFrame, features: list[str], *, alpha: float = 0.50):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return model


def predict_q_model(model: Any, train_ref: pd.DataFrame, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    _, frame_n, _ = normalize_for_model(train_ref.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
    return np.asarray(model.predict(frame_n[features]), dtype=float)


def train_oof_pred(train: pd.DataFrame, features: list[str], *, alpha: float = 0.50) -> np.ndarray:
    oof = np.full(len(train), np.nan, dtype=float)
    kf = KFold(n_splits=OOF_SPLITS, shuffle=True, random_state=SEED)
    for fit_idx, hold_idx in kf.split(train):
        fit = train.iloc[fit_idx].copy()
        hold = train.iloc[hold_idx].copy()
        model = fit_q_model(fit, features, alpha=alpha)
        oof[hold_idx] = predict_q_model(model, fit, hold, features)
    if np.isnan(oof).any():
        raise RuntimeError("OOF prediction contains NaN")
    return oof


def residual_neighbor_stat(
    train_ref: pd.DataFrame,
    target: pd.DataFrame,
    sim_features: list[str],
    residuals: np.ndarray,
    *,
    top_k: int,
    prefix: str,
) -> pd.DataFrame:
    features = [f for f in sim_features if f in train_ref.columns and f in target.columns]
    if not features:
        raise ValueError(f"{prefix} has no similarity features")

    prep = similarity_preprocessor(train_ref, features)
    train_x = prep.fit_transform(train_ref[features])
    target_x = prep.transform(target[features])
    nn = NearestNeighbors(n_neighbors=min(top_k, len(train_ref)), metric="cosine")
    nn.fit(train_x)
    distances, indices = nn.kneighbors(target_x)

    rows = []
    for dist_row, idx_row in zip(distances, indices, strict=True):
        idx = np.asarray(idx_row, dtype=int)
        vals = np.asarray(residuals[idx], dtype=float)
        sim = 1.0 / (1.0 + np.asarray(dist_row, dtype=float))
        rows.append({
            f"{prefix}_resid_n": float(len(vals)),
            f"{prefix}_resid_median": float(np.median(vals)),
            f"{prefix}_resid_mean": float(np.mean(vals)),
            f"{prefix}_resid_q25": float(np.quantile(vals, 0.25)),
            f"{prefix}_resid_q75": float(np.quantile(vals, 0.75)),
            f"{prefix}_resid_iqr": float(np.quantile(vals, 0.75) - np.quantile(vals, 0.25)),
            f"{prefix}_resid_std": float(np.std(vals)),
            f"{prefix}_sim_mean": float(np.mean(sim)),
            f"{prefix}_sim_max": float(np.max(sim)),
        })
    return pd.DataFrame(rows)


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
    }
    if extra:
        row.update(extra)
    return row


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, correction: np.ndarray | None = None) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "policy": policy,
    })
    if correction is not None:
        out["correction_log"] = correction
    return out


def segment_summary(predictions: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rows = []
    df = predictions[predictions["candidate"].isin(candidates)].copy()
    for (candidate, split), group_all in df.groupby(["candidate", "split"], observed=False):
        work = group_all.copy()
        work["actual_price_band"] = pd.cut(
            pd.to_numeric(work["actual_price"], errors="coerce"),
            bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
            labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
            include_lowest=True,
        ).astype("string")
        for segment, group in work.groupby("actual_price_band", observed=False):
            if group.empty:
                continue
            pred = group["pred_log"].to_numpy(dtype=float)
            rows.append({
                "candidate": candidate,
                "split": split,
                "segment": str(segment),
                "n": int(len(group)),
                "mean_correction_log": float(group.get("correction_log", pd.Series(0, index=group.index)).mean()),
                **metrics(
                    group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                    ),
                    pred,
                ),
                **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
            })
    return pd.DataFrame(rows)


def select_validation_candidates(metrics_df: pd.DataFrame) -> pd.DataFrame:
    val = metrics_df[metrics_df["split"].eq("validation")].copy()
    val["is_base"] = val["candidate"].eq("base_similarity_k160_q50")
    return val.sort_values(["MAPE", "p95_APE", "MdAPE", "APE_gt_5", "is_base"]).head(12)


def write_reports(metrics_df: pd.DataFrame, predictions: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "APE_gt_2", "APE_gt_5", "APE_gt_10", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MdAPE_a_minus_b_lt_0", "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "mean_correction_log", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]

    val_top = select_validation_candidates(metrics_df)
    selected = unique(["base_similarity_k160_q50"] + val_top["candidate"].head(6).tolist())
    test_selected = metrics_df[(metrics_df["split"].eq("test")) & (metrics_df["candidate"].isin(selected))].sort_values(["MAPE", "p95_APE", "MdAPE"])
    test_top = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(16)
    selected_seg = seg_df[seg_df["candidate"].isin(selected)].sort_values(["split", "candidate", "segment"])

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: 작가별 `search_delta_lookup[artist_key]` 대신, 유사 작품/유사 작가 메타 이웃의 out-of-fold 잔차로 마지막 보정을 할 수 있는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 보정값 생성: train OOF residual만 reference로 사용. validation/test 실제 가격은 보정값 생성에 사용하지 않는다.",
        "",
        "## 1. Validation 선택 후보",
        md_table(val_top, metric_cols),
        "",
        "## 2. Validation 선택 후보의 Test 결과",
        md_table(test_selected, metric_cols),
        "",
        "## 3. Test 상위 후보 참고",
        md_table(test_top, metric_cols),
        "",
        "## 4. Paired bootstrap vs base",
        md_table(boot_df, boot_cols),
        "",
        "## 5. 가격대별 진단",
        md_table(selected_seg, seg_cols),
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Validation 선택 후보</h2>{html_table(val_top, metric_cols)}
<h2>Validation 선택 후보의 Test 결과</h2>{html_table(test_selected, metric_cols)}
<h2>Test 상위 후보 참고</h2>{html_table(test_top, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>가격대별 진단</h2>{html_table(selected_seg, seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()

    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    core_features = cmeta["user_meta_core_bucket"][1]
    required = unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    if FEATURE_CANDIDATES_WITH_META.exists():
        ppw.FEATURE_CANDIDATES = FEATURE_CANDIDATES_WITH_META
        train, val, test = load_user_meta_frames(required)
    else:
        train, val, test = load_split_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    for label, features in [
        ("artwork", artwork_features),
        ("core", core_features),
        ("artwork_sim", ARTWORK_SIM_FEATURES),
        ("artist_sim", ARTIST_SIM_FEATURES),
    ]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{label}")
        if any(str(feature).startswith("search_") for feature in features):
            raise ValueError(f"{label} contains forbidden search_* feature")

    train_sim, val_sim, test_sim, ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=f"artwork_sim_k{BASE_TOP_K}", top_k=BASE_TOP_K
    )
    base_features = unique(core_features + ref_features)
    assert_strict_cold_features(base_features, context=f"{EXP_ID}:base")

    base_model = fit_q_model(train_sim, base_features, alpha=0.50)
    base_pred = {
        "validation": predict_q_model(base_model, train_sim, val_sim, base_features),
        "test": predict_q_model(base_model, train_sim, test_sim, base_features),
    }
    train_oof = train_oof_pred(train_sim, base_features, alpha=0.50)
    train_residual = train_sim["ln_price_krw"].to_numpy(dtype=float) - train_oof

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    metric_rows.append(metric_row("base_similarity_k160_q50", "validation", val_sim, base_pred["validation"], "user_meta + artwork similarity k160 q50"))
    metric_rows.append(metric_row("base_similarity_k160_q50", "test", test_sim, base_pred["test"], "user_meta + artwork similarity k160 q50"))
    pred_frames.append(prediction_frame("base_similarity_k160_q50", "validation", val_sim, base_pred["validation"], "base"))
    pred_frames.append(prediction_frame("base_similarity_k160_q50", "test", test_sim, base_pred["test"], "base"))

    sim_families = {
        "artwork": ARTWORK_SIM_FEATURES,
        "artist_meta": ARTIST_SIM_FEATURES,
        "artwork_artist_meta": unique(ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES),
    }
    residual_stats: dict[tuple[str, int, str], pd.DataFrame] = {}
    for family, sim_features in sim_families.items():
        for top_k in NEIGHBOR_KS:
            prefix = f"{family}_k{top_k}"
            residual_stats[(family, top_k, "validation")] = residual_neighbor_stat(
                train_sim, val_sim, sim_features, train_residual, top_k=top_k, prefix=prefix
            )
            residual_stats[(family, top_k, "test")] = residual_neighbor_stat(
                train_sim, test_sim, sim_features, train_residual, top_k=top_k, prefix=prefix
            )

            for strength in STRENGTHS:
                for cap in CAPS:
                    candidate = f"resid_{family}_k{top_k}_s{str(strength).replace('.', 'p')}_cap{str(cap).replace('.', 'p')}"
                    policy = f"{family} top_k={top_k} residual median, correction=clip({strength:.2f}*median, +/-{cap:.2f})"
                    for split, frame in [("validation", val_sim), ("test", test_sim)]:
                        stats = residual_stats[(family, top_k, split)]
                        median_col = f"{prefix}_resid_median"
                        correction = np.clip(
                            strength * stats[median_col].to_numpy(dtype=float),
                            -cap,
                            cap,
                        )
                        pred = base_pred[split] + correction
                        metric_rows.append(metric_row(
                            candidate,
                            split,
                            frame,
                            pred,
                            policy,
                            extra={
                                "neighbor_family": family,
                                "top_k": top_k,
                                "strength": strength,
                                "cap_log": cap,
                                "mean_correction_log": float(np.mean(correction)),
                                "median_correction_log": float(np.median(correction)),
                            },
                        ))
                        pred_frames.append(prediction_frame(candidate, split, frame, pred, policy, correction))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    val_top = select_validation_candidates(metrics_df)
    selected = unique(["base_similarity_k160_q50"] + val_top["candidate"].head(6).tolist())
    boot_rows = []
    for split, frame in [("validation", val_sim), ("test", test_sim)]:
        base = predictions_df[(predictions_df["candidate"].eq("base_similarity_k160_q50")) & (predictions_df["split"].eq(split))].sort_values("_track6_row_id")
        for candidate in selected:
            if candidate == "base_similarity_k160_q50":
                continue
            cand = predictions_df[(predictions_df["candidate"].eq(candidate)) & (predictions_df["split"].eq(split))].sort_values("_track6_row_id")
            boot_rows.append(paired_bootstrap(
                frame.sort_values("_track6_row_id"),
                cand["pred_log"].to_numpy(dtype=float),
                base["pred_log"].to_numpy(dtype=float),
                a_name=candidate,
                b_name="base_similarity_k160_q50",
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)
    seg_df = segment_summary(predictions_df, selected)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_user_enterable_artist_meta": True,
        "uses_similarity_reference_stats": True,
        "uses_similarity_neighbor_residual_correction": True,
        "base_top_k": BASE_TOP_K,
        "neighbor_ks": NEIGHBOR_KS,
        "strengths": STRENGTHS,
        "caps": CAPS,
        "router_used": False,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_base.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, predictions_df, boot_df, seg_df, summary)


if __name__ == "__main__":
    main()
