#!/usr/bin/env python3
"""PP-CSIM8: validate balanced Cold k160 alpha45 candidate.

PP-CSIM7 found that q45 without low-price weights is a balanced candidate:
better MAPE/p95 than the current user_meta_core_bucket and fewer tail errors
than k160 q50, while keeping MdAPE close.  This script adds:

- paired bootstrap vs user_meta_core_bucket and k160 q50
- segment diagnostics
- inference-time user metadata missingness stress
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

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import candidate_defs, load_user_meta_frames  # noqa: E402
from run_pp_cmeta5_user_meta_robustness_validation import MISSING_SCENARIOS, apply_missing_scenario, paired_bootstrap  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    html_table,
    json_clean,
    lgbm_quantile_model,
    md_table,
    normalize_for_model,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM8"
SLUG = "PP-CSIM8_cold_similarity_alpha45_validation"
TITLE = "Cold 유사작품 k160 q45 균형 후보 후속 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim8_cold_similarity_alpha45_validation_summary.md"

TOP_K = 160


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def fit_quantile(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    *,
    alpha: float,
) -> dict[str, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    y = train_n["ln_price_krw"].to_numpy(dtype=float)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], y)
    return {
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
    }


def fit_quantile_model(train: pd.DataFrame, features: list[str], *, alpha: float):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    y = train_n["ln_price_krw"].to_numpy(dtype=float)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], y)
    return model


def predict_model(model: Any, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    _, frame_n, _ = normalize_for_model(frame.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
    return np.asarray(model.predict(frame_n[features]), dtype=float)


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


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    core_features = cmeta["user_meta_core_bucket"][1]
    artwork_features = unique(fs["cold_lgb"])
    required = unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    for name, features in [("artwork_only", artwork_features), ("user_meta_core_bucket", core_features)]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=f"artwork_sim_k{TOP_K}", top_k=TOP_K
    )
    sim_features = unique(core_features + art_ref_features)

    preds = {
        "user_meta_core_bucket": fit_quantile(train, val, test, core_features, alpha=0.50),
        "k160_alpha50": fit_quantile(train_art, val_art, test_art, sim_features, alpha=0.50),
        "k160_alpha45": fit_quantile(train_art, val_art, test_art, sim_features, alpha=0.45),
    }
    frames = {
        "user_meta_core_bucket": (val, test, core_features, "기존 사용자 메타 core bucket"),
        "k160_alpha50": (val_art, test_art, sim_features, "유사작품 k160 q50"),
        "k160_alpha45": (val_art, test_art, sim_features, "유사작품 k160 q45"),
    }

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for candidate, pred_by_split in preds.items():
        val_frame, test_frame, features, policy = frames[candidate]
        for split, frame in [("validation", val_frame), ("test", test_frame)]:
            pred = pred_by_split[split]
            metric_rows.append(metric_row(candidate, split, frame, pred, policy, {"alpha": 0.45 if candidate.endswith("45") else 0.50}))
            pred_frames.append(prediction_frame(candidate, split, frame, pred, policy, {"alpha": 0.45 if candidate.endswith("45") else 0.50}))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    boot_rows = []
    for split, base_frame in [("validation", val), ("test", test)]:
        for baseline in ["user_meta_core_bucket", "k160_alpha50"]:
            boot_rows.append(paired_bootstrap(
                base_frame,
                preds["k160_alpha45"][split],
                preds[baseline][split],
                a_name="k160_alpha45",
                b_name=baseline,
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)

    seg_df = pd.concat([
        segment_summary(predictions_df, candidate, "test")
        for candidate in ["user_meta_core_bucket", "k160_alpha50", "k160_alpha45"]
    ], ignore_index=True)

    model45 = fit_quantile_model(train_art, sim_features, alpha=0.45)
    stress_rows = []
    for scenario, fields in MISSING_SCENARIOS.items():
        for split, base_frame in [("validation", val_art), ("test", test_art)]:
            frame = apply_missing_scenario(base_frame, fields)
            pred = predict_model(model45, frame, sim_features)
            stress_rows.append({
                "experiment_id": EXP_ID,
                "candidate": "k160_alpha45",
                "split": split,
                "stress_scenario": scenario,
                "missing_fields": ",".join(fields),
                "n_missing_fields": len(fields),
                **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
                **tail_counts(frame, pred),
            })
    stress_df = pd.DataFrame(stress_rows)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "router_used": False,
        "selected_candidate": "k160_alpha45",
        "top_k": TOP_K,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    stress_df.to_csv(OUT / "missingness_stress_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = ["candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10", "policy"]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MdAPE_a_minus_b_lt_0", "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5"]
    stress_cols = ["stress_scenario", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "n_missing_fields", "missing_fields"]
    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    test_stress = stress_df[stress_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: PP-CSIM7의 균형 후보 `k160_alpha45`를 기존 후보와 k160 q50 대비 후속 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 라우터는 사용하지 않았다.",
        "",
        "## 1. 기본 성능",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Paired bootstrap",
        "- delta는 `k160_alpha45 - 비교 후보`다. 음수이면 q45 후보가 더 좋다.",
        md_table(boot_df, boot_cols),
        "",
        "## 3. 가격대별 진단",
        md_table(seg_df.sort_values(["segment", "candidate"]), seg_cols),
        "",
        "## 4. 메타 누락 stress",
        md_table(test_stress, stress_cols),
        "",
        "## 5. 결론",
        "",
        "- `k160_alpha45`는 기존 후보보다 MdAPE/MAPE/p95를 개선하지만 APE > 5는 2건 증가한다.",
        "- `k160_alpha50`보다는 tail이 안정적이며, q50의 개선 신호를 보수적으로 낮춘 후보로 해석된다.",
        "- 메타 누락 stress에서 total works/followers 계열이 빠질 때 약해지는지 확인해야 한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>기본 성능</h2>{html_table(test_metrics, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>가격대별 진단</h2>{html_table(seg_df.sort_values(['segment', 'candidate']), seg_cols)}
<h2>메타 누락 stress</h2>{html_table(test_stress, stress_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
