#!/usr/bin/env python3
"""PP-CSIM17: Cold similar-artwork grouping grid.

Follow-up to PP-CSIM16.  Weighted similar-artwork q35 improved test MAPE/p95
slightly but did not beat q35 on validation.  This grid checks whether the
similar-artwork grouping itself has a more stable setting:

- k80 / k160 / k320
- unweighted reference stats
- similarity-weighted reference stats
- unweighted + weighted combined stats

Strict Cold contract is unchanged.
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
from run_pp_cmeta4_user_input_meta_only import META_BUCKET_FEATURES, USER_META_CORE, load_user_meta_frames  # noqa: E402
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
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pp_csim16_cold_improvement_suite import compute_weighted_reference_stats  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM17"
SLUG = "PP-CSIM17_cold_similarity_grouping_grid"
TITLE = "Cold 유사작품 그룹핑 k/가중 통계 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim17_cold_similarity_grouping_grid_summary.md"

TOP_KS = [80, 160, 320]

ENTERABLE_META = [
    "artist_meta_birth_year",
    "artist_meta_career_stage",
    "artist_meta_birth_year_missing",
    "artist_meta_career_stage_missing",
    "artist_meta_nationality",
]

ENTERABLE_BUCKETS = [
    "artist_birth_period_bucket",
    "artist_career_stage_bucket",
    "medium_birth_period_bucket",
    "career_size_bucket",
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def fit_predict(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str], *, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return (
        np.asarray(model.predict(val_n[features]), dtype=float),
        np.asarray(model.predict(test_n[features]), dtype=float),
    )


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, family: str, policy: str, extra: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "family": family,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **extra,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
    }


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, family: str) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "family": family,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
    })


def write_reports(metrics_df: pd.DataFrame, boot_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "family", "split", "top_k", "alpha", "MdAPE", "MAPE", "p95_APE",
        "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"])
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"])
    tail = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"])
    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: Cold q35 후보의 유사작품 그룹핑 k와 가중 통계가 안정적으로 개선되는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "",
        "## 1. Test 성능: MAPE 기준",
        md_table(test, metric_cols),
        "",
        "## 2. Validation 성능: MAPE 기준",
        md_table(val, metric_cols),
        "",
        "## 3. Test 성능: APE > 5 기준",
        md_table(tail, metric_cols),
        "",
        "## 4. Paired bootstrap vs q35_k160_unweighted",
        md_table(boot_df, boot_cols),
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 성능</h2>{html_table(test, metric_cols)}
<h2>Validation 성능</h2>{html_table(val, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    artwork_features = unique(fs["cold_lgb"])
    enterable_base = unique(artwork_features + ENTERABLE_META + ENTERABLE_BUCKETS)
    required = unique(enterable_base + USER_META_CORE + META_BUCKET_FEATURES + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    assert_strict_cold_features(enterable_base, context=f"{EXP_ID}:enterable_base")

    candidates: dict[str, dict[str, Any]] = {}
    for top_k in TOP_KS:
        train_u, val_u, test_u, u_features = compute_reference_stats(
            train,
            val,
            test,
            ARTWORK_SIM_FEATURES,
            prefix=f"artwork_sim_k{top_k}",
            top_k=top_k,
        )
        train_w, val_w, test_w, w_features = compute_weighted_reference_stats(
            train,
            val,
            test,
            ARTWORK_SIM_FEATURES,
            prefix=f"artwork_wsim_k{top_k}",
            top_k=top_k,
        )
        for family, train_f, val_f, test_f, ref_features, policy in [
            ("unweighted", train_u, val_u, test_u, u_features, f"비가중 유사작품 k{top_k} 통계 + q35"),
            ("weighted", train_w, val_w, test_w, w_features, f"거리 가중 유사작품 k{top_k} 통계 + q35"),
        ]:
            features = unique(enterable_base + ref_features)
            val_pred, test_pred = fit_predict(train_f, val_f, test_f, features, alpha=0.35)
            candidates[f"q35_k{top_k}_{family}"] = {
                "family": family,
                "top_k": top_k,
                "alpha": 0.35,
                "policy": policy,
                "validation_frame": val_f,
                "test_frame": test_f,
                "validation": val_pred,
                "test": test_pred,
            }
        train_c = pd.concat([train_u.reset_index(drop=True), train_w[w_features].reset_index(drop=True)], axis=1)
        val_c = pd.concat([val_u.reset_index(drop=True), val_w[w_features].reset_index(drop=True)], axis=1)
        test_c = pd.concat([test_u.reset_index(drop=True), test_w[w_features].reset_index(drop=True)], axis=1)
        features_c = unique(enterable_base + u_features + w_features)
        val_pred, test_pred = fit_predict(train_c, val_c, test_c, features_c, alpha=0.35)
        candidates[f"q35_k{top_k}_combined"] = {
            "family": "combined",
            "top_k": top_k,
            "alpha": 0.35,
            "policy": f"비가중+거리 가중 유사작품 k{top_k} 통계 + q35",
            "validation_frame": val_c,
            "test_frame": test_c,
            "validation": val_pred,
            "test": test_pred,
        }

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for candidate, pack in candidates.items():
        for split in ["validation", "test"]:
            frame = pack[f"{split}_frame"]
            pred = pack[split]
            extra = {"top_k": pack["top_k"], "alpha": pack["alpha"]}
            metric_rows.append(metric_row(candidate, split, frame, pred, pack["family"], pack["policy"], extra))
            pred_frames.append(prediction_frame(candidate, split, frame, pred, pack["family"]))
    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    baseline = "q35_k160_unweighted"
    boot_rows = []
    for split in ["validation", "test"]:
        base_pack = candidates[baseline]
        base_frame = base_pack[f"{split}_frame"]
        base_pred = base_pack[split]
        top_names = unique(
            metrics_df[metrics_df["split"].eq(split)].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(6)["candidate"].tolist()
            + [baseline]
        )
        for candidate in top_names:
            if candidate == baseline:
                continue
            boot_rows.append(paired_bootstrap(
                base_frame,
                candidates[candidate][split],
                base_pred,
                a_name=candidate,
                b_name=baseline,
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "uses_weighted_similarity_reference_stats": True,
        "router_used": False,
        "top_k_grid": TOP_KS,
        "candidate_count": len(candidates),
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_q35_k160_unweighted.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, boot_df, summary)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
