#!/usr/bin/env python3
"""PP-CSIM18: focused validation for Cold k320 q35 candidates.

PP-CSIM17 found that k320 candidates can reduce test MAPE and APE > 5, but the
signal was not clean enough for promotion.  This focused validation compares:

- q35_k160_unweighted: current conservative baseline
- q35_k320_unweighted: broader similar-artwork pool
- q35_k320_combined: unweighted + weighted k320 stats

Checks:
- validation/test metrics
- paired bootstrap vs q35_k160_unweighted
- actual-price-band diagnostics
- inference-time user metadata missingness stress
- prediction shift diagnostics

Strict Cold contract:
- no artist_key feature
- no same-artist price history feature
- no artist_key lookup postprocess
- no search_* or external live search features
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
from run_pp_csim16_cold_improvement_suite import compute_weighted_reference_stats  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM18"
SLUG = "PP-CSIM18_cold_k320_candidate_validation"
TITLE = "Cold k320 후보 집중 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim18_cold_k320_candidate_validation_summary.md"

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


def fit_model(train: pd.DataFrame, features: list[str], *, alpha: float = 0.35):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return model


def predict_model(model: Any, train: pd.DataFrame, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    _, frame_n, _ = normalize_for_model(train.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
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


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str) -> pd.DataFrame:
    return pd.DataFrame({
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


def segment_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, split), df in predictions.groupby(["candidate", "split"], observed=False):
        work = df.copy()
        work["actual_price_band"] = pd.cut(
            pd.to_numeric(work["actual_price"], errors="coerce"),
            bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
            labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
            include_lowest=True,
        ).astype("string")
        for segment, group in work.groupby("actual_price_band", observed=False):
            pred = group["pred_log"].to_numpy(dtype=float)
            rows.append({
                "candidate": candidate,
                "split": split,
                "segment": str(segment),
                "n": int(len(group)),
                **metrics(
                    group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                    ),
                    pred,
                ),
                **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
            })
    return pd.DataFrame(rows)


def prediction_shift(predictions: pd.DataFrame, baseline: str) -> pd.DataFrame:
    rows = []
    for split in ["validation", "test"]:
        base = predictions[(predictions["split"].eq(split)) & (predictions["candidate"].eq(baseline))]
        base_map = base.set_index("_track6_row_id")["pred_log"]
        for candidate, group in predictions[predictions["split"].eq(split)].groupby("candidate", observed=False):
            aligned = group.set_index("_track6_row_id").join(base_map.rename("base_pred_log"), how="inner")
            diff = aligned["pred_log"].to_numpy(dtype=float) - aligned["base_pred_log"].to_numpy(dtype=float)
            rows.append({
                "candidate": candidate,
                "split": split,
                "n": int(len(aligned)),
                "mean_log_shift_vs_baseline": float(np.mean(diff)),
                "median_log_shift_vs_baseline": float(np.median(diff)),
                "p05_log_shift_vs_baseline": float(np.quantile(diff, 0.05)),
                "p95_log_shift_vs_baseline": float(np.quantile(diff, 0.95)),
                "share_lower_than_baseline": float(np.mean(diff < 0.0)),
            })
    return pd.DataFrame(rows)


def stress_metrics(candidates: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for scenario, fields in MISSING_SCENARIOS.items():
        for split in ["validation", "test"]:
            for candidate, pack in candidates.items():
                frame = apply_missing_scenario(pack[f"{split}_frame"], fields)
                pred = predict_model(pack["model"], pack["train_frame"], frame, pack["features"])
                rows.append({
                    "experiment_id": EXP_ID,
                    "candidate": candidate,
                    "split": split,
                    "stress_scenario": scenario,
                    "missing_fields": ",".join(fields),
                    "n_missing_fields": len(fields),
                    **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
                    **tail_counts(frame, pred),
                })
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, stress_df: pd.DataFrame, shift_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = ["candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10", "policy"]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean",
        "delta_p95_APE_a_minus_b_mean", "delta_RMSE_log_a_minus_b_mean",
        "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10"]
    stress_cols = ["candidate", "stress_scenario", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10", "missing_fields"]
    shift_cols = ["candidate", "split", "n", "mean_log_shift_vs_baseline", "median_log_shift_vs_baseline", "p05_log_shift_vs_baseline", "p95_log_shift_vs_baseline", "share_lower_than_baseline"]

    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"])
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"])
    test_seg = seg_df[seg_df["split"].eq("test")].sort_values(["segment", "candidate"])
    test_stress = stress_df[stress_df["split"].eq("test")].sort_values(["stress_scenario", "candidate"])

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: k320 계열이 q35 k160 기준선을 대체할 수 있는지 집중 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "",
        "## 1. Test 성능",
        md_table(test, metric_cols),
        "",
        "## 2. Validation 성능",
        md_table(val, metric_cols),
        "",
        "## 3. Paired bootstrap vs q35_k160_unweighted",
        "- delta는 `후보 - q35_k160_unweighted`다. 음수이면 후보가 기준선보다 좋다.",
        md_table(boot_df, boot_cols),
        "",
        "## 4. Test 가격대별 진단",
        md_table(test_seg, seg_cols),
        "",
        "## 5. Test 결측 스트레스",
        md_table(test_stress, stress_cols),
        "",
        "## 6. 예측 이동량",
        md_table(shift_df, shift_cols),
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}code{{background:#eef2f7;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 성능</h2>{html_table(test, metric_cols)}
<h2>Validation 성능</h2>{html_table(val, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>Test 가격대별 진단</h2>{html_table(test_seg, seg_cols)}
<h2>Test 결측 스트레스</h2>{html_table(test_stress, stress_cols)}
<h2>예측 이동량</h2>{html_table(shift_df, shift_cols)}
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

    train160, val160, test160, ref160 = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix="artwork_sim_k160", top_k=160
    )
    train320, val320, test320, ref320 = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix="artwork_sim_k320", top_k=320
    )
    train320w, val320w, test320w, ref320w = compute_weighted_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix="artwork_wsim_k320", top_k=320
    )
    train320c = pd.concat([train320.reset_index(drop=True), train320w[ref320w].reset_index(drop=True)], axis=1)
    val320c = pd.concat([val320.reset_index(drop=True), val320w[ref320w].reset_index(drop=True)], axis=1)
    test320c = pd.concat([test320.reset_index(drop=True), test320w[ref320w].reset_index(drop=True)], axis=1)

    candidate_defs = {
        "q35_k160_unweighted": {
            "policy": "비가중 유사작품 k160 통계 + q35",
            "train_frame": train160,
            "validation_frame": val160,
            "test_frame": test160,
            "features": unique(enterable_base + ref160),
        },
        "q35_k320_unweighted": {
            "policy": "비가중 유사작품 k320 통계 + q35",
            "train_frame": train320,
            "validation_frame": val320,
            "test_frame": test320,
            "features": unique(enterable_base + ref320),
        },
        "q35_k320_combined": {
            "policy": "비가중+거리 가중 유사작품 k320 통계 + q35",
            "train_frame": train320c,
            "validation_frame": val320c,
            "test_frame": test320c,
            "features": unique(enterable_base + ref320 + ref320w),
        },
    }

    candidates: dict[str, dict[str, Any]] = {}
    for name, pack in candidate_defs.items():
        model = fit_model(pack["train_frame"], pack["features"], alpha=0.35)
        candidates[name] = pack | {
            "model": model,
            "validation": predict_model(model, pack["train_frame"], pack["validation_frame"], pack["features"]),
            "test": predict_model(model, pack["train_frame"], pack["test_frame"], pack["features"]),
        }

    metric_rows = []
    pred_frames = []
    for name, pack in candidates.items():
        for split in ["validation", "test"]:
            frame = pack[f"{split}_frame"]
            pred = pack[split]
            metric_rows.append(metric_row(name, split, frame, pred, pack["policy"]))
            pred_frames.append(prediction_frame(name, split, frame, pred, pack["policy"]))
    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    seg_df = segment_summary(predictions_df)
    shift_df = prediction_shift(predictions_df, "q35_k160_unweighted")
    stress_df = stress_metrics(candidates)

    boot_rows = []
    baseline = "q35_k160_unweighted"
    for split in ["validation", "test"]:
        base_pack = candidates[baseline]
        for name, pack in candidates.items():
            if name == baseline:
                continue
            boot_rows.append(paired_bootstrap(
                base_pack[f"{split}_frame"],
                pack[split],
                base_pack[split],
                a_name=name,
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
        "candidate_count": len(candidates),
        "baseline": baseline,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    shift_df.to_csv(OUT / "prediction_shift_vs_baseline.csv", index=False)
    stress_df.to_csv(OUT / "missingness_stress_metrics.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_q35_k160_unweighted.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, boot_df, seg_df, stress_df, shift_df, summary)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
