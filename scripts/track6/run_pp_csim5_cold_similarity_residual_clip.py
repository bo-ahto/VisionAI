#!/usr/bin/env python3
"""PP-CSIM5: Cold similar-artwork basis + residual clip.

Router-free structural follow-up to PP-CSIM3/4.  Instead of letting LightGBM
predict the final log price directly, this experiment uses similar-artwork
k160 median log price as an interpretable basis and trains a residual model:

    final_log = similar_artwork_median_log + clip(residual_pred, lower, upper)

The goal is to keep the useful similar-artwork signal while reducing extreme
tail errors, especially APE > 5.
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
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import candidate_defs, load_user_meta_frames  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    fit_quantile_bundle,
    html_table,
    json_clean,
    md_table,
    normalize_for_model,
    split_types,
)
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM5"
SLUG = "PP-CSIM5_cold_similarity_residual_clip"
TITLE = "Cold 유사작품 기준가격 + 잔차 clip 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim5_cold_similarity_residual_clip_summary.md"

TOP_K = 160
CLIP_GRID = [
    ("basis_only", 0.0, 0.0, 0.0),
    ("clip_m030_p030", 1.0, -0.30, 0.30),
    ("clip_m040_p030", 1.0, -0.40, 0.30),
    ("clip_m050_p040", 1.0, -0.50, 0.40),
    ("clip_m070_p050", 1.0, -0.70, 0.50),
    ("half_clip_m050_p040", 0.5, -0.50, 0.40),
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def residual_model(train: pd.DataFrame, features: list[str]) -> Pipeline:
    numeric, categorical = split_types(train, features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="huber",
            alpha=0.9,
            n_estimators=360,
            learning_rate=0.035,
            num_leaves=24,
            min_child_samples=45,
            subsample=0.9,
            colsample_bytree=0.85,
            reg_lambda=1.8,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def fit_residual_predictions(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    basis_col: str,
) -> dict[str, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    y = pd.to_numeric(train_n["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
    basis_train = pd.to_numeric(train_n[basis_col], errors="coerce").to_numpy(dtype=float)
    residual_y = y - basis_train
    model = residual_model(train_n, features)
    model.fit(train_n[features], residual_y)
    return {
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
    }


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
    }
    if extra:
        row.update(extra)
    return row


def tail_counts(frame: pd.DataFrame, pred: np.ndarray) -> dict[str, int]:
    actual = pd.to_numeric(frame["price_krw"], errors="coerce").to_numpy(dtype=float)
    ape = np.abs(np.exp(pred) - actual) / np.maximum(actual, 1.0)
    return {
        "APE_gt_1": int((ape > 1.0).sum()),
        "APE_gt_2": int((ape > 2.0).sum()),
        "APE_gt_5": int((ape > 5.0).sum()),
        "APE_gt_10": int((ape > 10.0).sum()),
    }


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> pd.DataFrame:
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
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_empty_"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            value = row[col]
            vals.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def segment_summary(predictions: pd.DataFrame, candidate: str, split: str) -> pd.DataFrame:
    df = predictions[predictions["candidate"].eq(candidate) & predictions["split"].eq(split)].copy()
    if df.empty:
        return pd.DataFrame()
    df["actual_price_band"] = pd.cut(
        pd.to_numeric(df["actual_price"], errors="coerce"),
        bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
        labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
        include_lowest=True,
    ).astype("string")
    rows = []
    for segment, group in df.groupby("actual_price_band", dropna=False, observed=False):
        pred = group["pred_log"].to_numpy(dtype=float)
        md = metrics(
            group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
            ),
            pred,
        )
        rows.append({
            "candidate": candidate,
            "split": split,
            "segment": str(segment),
            "n": int(len(group)),
            **md,
            **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
        })
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    core_features = cmeta["user_meta_core_bucket"][1]
    required = unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    for name, features in [("artwork_only", artwork_features), ("user_meta_core_bucket", core_features)]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")

    prefix = f"artwork_sim_k{TOP_K}"
    basis_col = f"{prefix}_ref_log_price_median"
    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=prefix, top_k=TOP_K
    )
    direct_features = unique(core_features + art_ref_features)
    residual_features = unique(core_features + art_ref_features)

    direct_bundle = fit_quantile_bundle(train_art, val_art, test_art, direct_features)
    residual_pred = fit_residual_predictions(train_art, val_art, test_art, residual_features, basis_col)
    user_bundle = fit_quantile_bundle(train, val, test, core_features)

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for split, frame, frame_art in [("validation", val, val_art), ("test", test, test_art)]:
        user_pred = user_bundle["q50"][split]
        metric_rows.append(metric_row(
            "user_meta_core_bucket",
            split,
            frame,
            user_pred,
            "기존 사용자 메타 core bucket",
            tail_counts(frame, user_pred),
        ))
        pred_frames.append(prediction_frame("user_meta_core_bucket", split, frame, user_pred, "기존 사용자 메타 core bucket"))

        direct_pred = direct_bundle["q50"][split]
        metric_rows.append(metric_row(
            "artwork_similarity_k160_direct",
            split,
            frame_art,
            direct_pred,
            "유사작품 k160 직접 q50 예측",
            tail_counts(frame_art, direct_pred),
        ))
        pred_frames.append(prediction_frame("artwork_similarity_k160_direct", split, frame_art, direct_pred, "유사작품 k160 직접 q50 예측"))

        basis = pd.to_numeric(frame_art[basis_col], errors="coerce").to_numpy(dtype=float)
        res = residual_pred[split]
        for name, strength, low, high in CLIP_GRID:
            clipped = np.clip(strength * res, low, high)
            pred = basis + clipped
            candidate = f"similar_basis_residual_{name}"
            policy = f"유사작품 median 기준가격 + residual strength={strength} clip=({low},{high})"
            metric_rows.append(metric_row(candidate, split, frame_art, pred, policy, {
                "basis_col": basis_col,
                "residual_strength": strength,
                "clip_low": low,
                "clip_high": high,
                **tail_counts(frame_art, pred),
            }))
            pred_frames.append(prediction_frame(candidate, split, frame_art, pred, policy, {
                "basis_col": basis_col,
                "residual_strength": strength,
                "clip_low": low,
                "clip_high": high,
            }))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    segment_df = pd.concat([
        segment_summary(predictions_df, candidate, "test")
        for candidate in metrics_df[metrics_df["split"].eq("test")]["candidate"].unique()
    ], ignore_index=True)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "router_used": False,
        "top_k": TOP_K,
        "basis_col": basis_col,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    segment_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10",
        "policy",
    ]
    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    stable_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "p95_APE", "MAPE"])
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5"]
    best_candidate = test_metrics.iloc[0]["candidate"]
    stable_candidate = stable_metrics.iloc[0]["candidate"]

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: 유사작품 k160을 최종 가격 직접 예측이 아니라 기준가격 + 제한된 잔차 보정 구조로 바꿔 극단 오차를 줄일 수 있는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "",
        "## 1. Test 결과: MdAPE 기준",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Test 결과: APE > 5 안정성 기준",
        md_table(stable_metrics, metric_cols),
        "",
        "## 3. 저가/고가 구간 진단",
        md_table(segment_df.sort_values(["segment", "APE_gt_5", "p95_APE"]).head(40), seg_cols),
        "",
        "## 4. 결론",
        "",
        f"- MdAPE 기준 최상위 후보는 `{best_candidate}`이다.",
        f"- APE > 5 안정성 기준 최상위 후보는 `{stable_candidate}`이다.",
        "- 잔차 clip 구조가 직접 q50 예측보다 극단 오차를 줄이는지와 중앙 오차를 얼마나 희생하는지를 함께 봐야 한다.",
        "- 라우터는 사용하지 않았으므로 결과는 모델 구조 변경 효과로 해석한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 결과: MdAPE 기준</h2>{html_table(test_metrics, metric_cols)}
<h2>Test 결과: APE &gt; 5 안정성 기준</h2>{html_table(stable_metrics, metric_cols)}
<h2>저가/고가 구간 진단</h2>{html_table(segment_df.sort_values(['segment', 'APE_gt_5', 'p95_APE']).head(40), seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
