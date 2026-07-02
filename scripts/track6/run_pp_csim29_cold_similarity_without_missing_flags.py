#!/usr/bin/env python3
"""PP-CSIM29: Cold artist-meta similarity without missing flags.

목적:
  Cold k40/k80 유사 이웃 잔차 보정에서 missing 여부 피처를 유사도 계산에
  넣지 않았을 때 성능이 좋아지는지 확인한다.

범위:
  - base Cold 모델 입력 피처는 기존과 동일하게 유지한다.
  - 유사 이웃 선택 피처에서만 `*_missing` 작가 메타 피처를 제거한다.
  - artist_key, 같은 작가 가격 이력, search/live lookup은 사용하지 않는다.
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
from run_pp_cmeta5_user_meta_robustness_validation import paired_bootstrap  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    html_table,
    json_clean,
    md_table,
)
from run_pp_csim24_cold_similarity_residual_correction import (  # noqa: E402
    BASE_TOP_K,
    CAPS,
    NEIGHBOR_KS,
    STRENGTHS,
    fit_q_model,
    predict_q_model,
    prediction_frame,
    residual_neighbor_stat,
    train_oof_pred,
)
from run_pp_csim25_cold_similarity_residual_rule_router import build_masks  # noqa: E402
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402
import run_pp_w_experiments as ppw  # noqa: E402


EXP_ID = "PP-CSIM29"
SLUG = "PP-CSIM29_cold_similarity_without_missing_flags"
TITLE = "Cold 유사도 missing 피처 제거 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim29_cold_similarity_without_missing_flags_summary.md"

MISSING_SIM_FEATURES = [
    "artist_meta_birth_year_missing",
    "artist_meta_total_works_missing",
    "artist_meta_followers_missing",
    "artist_meta_career_stage_missing",
]

FEATURE_CANDIDATES_WITH_META = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year_type_edition_size.csv"

FOCUS_ROUTE_CANDIDATES = [
    "base",
    "resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p03",
    "resid_artist_meta_no_missing_k40_s1p0_cap0p18__route_neg_corr_ge_0p05",
    "resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p03",
    "resid_artist_meta_no_missing_k40_s1p0_cap0p25__route_neg_corr_ge_0p05",
    "resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p03",
    "resid_artist_meta_no_missing_k80_s1p0_cap0p18__route_neg_corr_ge_0p05",
    "resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p03",
    "resid_artist_meta_no_missing_k80_s1p0_cap0p25__route_neg_corr_ge_0p05",
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


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


def routed_prediction_frame(source: pd.DataFrame, split: str, routed_candidate: str) -> pd.DataFrame:
    base = source[(source["split"].eq(split)) & (source["candidate"].eq("base_similarity_k160_q50"))].sort_values("_track6_row_id").reset_index(drop=True)
    base_pred = base["pred_log"].to_numpy(dtype=float)
    if routed_candidate == "base":
        return pd.DataFrame({
            "experiment_id": EXP_ID,
            "candidate": "base",
            "source_candidate": "base_similarity_k160_q50",
            "split": split,
            "_track6_row_id": base["_track6_row_id"].to_numpy(),
            "actual_log": base["actual_log"].to_numpy(dtype=float),
            "actual_price": base["actual_price"].to_numpy(dtype=float),
            "pred_log": base_pred,
            "pred_price": np.exp(base_pred),
            "selected": np.zeros(len(base), dtype=int),
            "policy": "항상 base similarity k160",
        })

    source_candidate, rule_name = routed_candidate.split("__route_", 1)
    cand = source[(source["split"].eq(split)) & (source["candidate"].eq(source_candidate))].sort_values("_track6_row_id").reset_index(drop=True)
    if cand.empty:
        raise ValueError(f"missing source candidate: {source_candidate}")
    masks = build_masks(base, cand)
    if rule_name not in masks:
        raise ValueError(f"missing route rule: {rule_name}")
    mask, policy = masks[rule_name]
    pred = np.where(mask, cand["pred_log"].to_numpy(dtype=float), base_pred)
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": routed_candidate,
        "source_candidate": source_candidate,
        "split": split,
        "_track6_row_id": base["_track6_row_id"].to_numpy(),
        "actual_log": base["actual_log"].to_numpy(dtype=float),
        "actual_price": base["actual_price"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "selected": mask.astype(int),
        "policy": policy,
    })


def routed_metric_row(candidate: str, split: str, pred: pd.DataFrame) -> dict[str, Any]:
    frame = pred[["_track6_row_id", "actual_log", "actual_price"]].rename(
        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
    )
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "source_candidate": str(pred["source_candidate"].iloc[0]),
        "scope": "cold",
        "split": split,
        "policy": str(pred["policy"].iloc[0]),
        "selected_rate": float(pred["selected"].mean()),
        "selected_n": int(pred["selected"].sum()),
        **metrics(frame, pred["pred_log"].to_numpy(dtype=float)),
        **tail_counts(frame, pred["pred_log"].to_numpy(dtype=float)),
    }


def paired_bootstraps(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "test"]:
        base = predictions[(predictions["split"].eq(split)) & (predictions["candidate"].eq("base"))].sort_values("_track6_row_id")
        frame = base[["_track6_row_id", "actual_log", "actual_price"]].rename(
            columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
        )
        for candidate in FOCUS_ROUTE_CANDIDATES:
            if candidate == "base":
                continue
            cand = predictions[(predictions["split"].eq(split)) & (predictions["candidate"].eq(candidate))].sort_values("_track6_row_id")
            rows.append(paired_bootstrap(
                frame,
                cand["pred_log"].to_numpy(dtype=float),
                base["pred_log"].to_numpy(dtype=float),
                a_name=candidate,
                b_name="base",
            ) | {"split": split})
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, routed_df: pd.DataFrame, boot_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "APE_gt_2", "APE_gt_5", "APE_gt_10", "selected_rate", "policy",
    ]
    raw_cols = ["candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10", "policy"]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MdAPE_a_minus_b_lt_0", "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: 유사 이웃 선택에서 missing 여부 피처를 제거했을 때 성능 변화를 확인한다.",
        "- 모델 입력 피처는 기존 user_meta_core_bucket을 유지하고, 유사도 피처에서만 missing flag를 제거했다.",
        "- 제거 피처: `" + "`, `".join(MISSING_SIM_FEATURES) + "`",
        "",
        "## 1. 라우터 후보 성능",
        md_table(routed_df.sort_values(["split", "MAPE", "p95_APE"]), metric_cols),
        "",
        "## 2. 원천 잔차 후보 성능",
        md_table(metrics_df.sort_values(["split", "MAPE", "p95_APE"]).head(40), raw_cols),
        "",
        "## 3. Paired bootstrap vs base",
        md_table(boot_df, boot_cols),
        "",
        "## 4. 해석",
        "",
        "- 이 실험은 전체 작가 메타에서 missing 정보를 제거한 것이 아니라, 유사도 계산에서만 제거한 것이다.",
        "- 성능이 좋아지면 missing 여부가 실제 작가 유사성보다 데이터 수집 상태를 기준으로 이웃을 묶고 있었을 가능성이 있다.",
        "- 성능이 나빠지면 missing 여부 자체가 입력 품질/작가 프로필 밀도를 나타내는 유효 신호였을 가능성이 있다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>라우터 후보 성능</h2>{html_table(routed_df.sort_values(['split', 'MAPE', 'p95_APE']), metric_cols)}
<h2>원천 잔차 후보 성능</h2>{html_table(metrics_df.sort_values(['split', 'MAPE', 'p95_APE']).head(40), raw_cols)}
<h2>Paired bootstrap vs base</h2>{html_table(boot_df, boot_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)

    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    core_features = cmeta["user_meta_core_bucket"][1]
    artist_sim_no_missing = [feature for feature in ARTIST_SIM_FEATURES if feature not in set(MISSING_SIM_FEATURES)]
    removed = [feature for feature in ARTIST_SIM_FEATURES if feature in set(MISSING_SIM_FEATURES)]
    required = unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + artist_sim_no_missing)
    if FEATURE_CANDIDATES_WITH_META.exists():
        ppw.FEATURE_CANDIDATES = FEATURE_CANDIDATES_WITH_META
    train, val, test = load_user_meta_frames(required)

    for label, features in [
        ("artwork", artwork_features),
        ("core", core_features),
        ("artist_sim_no_missing", artist_sim_no_missing),
    ]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{label}")
        bad = [feature for feature in features if feature.startswith("search_")]
        if bad:
            raise ValueError(f"{label} contains search features: {bad}")

    train_sim, val_sim, test_sim, ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=f"artwork_sim_k{BASE_TOP_K}", top_k=BASE_TOP_K
    )
    base_features = unique(core_features + ref_features)
    base_model = fit_q_model(train_sim, base_features, alpha=0.50)
    base_pred = {
        "validation": predict_q_model(base_model, train_sim, val_sim, base_features),
        "test": predict_q_model(base_model, train_sim, test_sim, base_features),
    }
    train_oof = train_oof_pred(train_sim, base_features, alpha=0.50)
    train_residual = train_sim["ln_price_krw"].to_numpy(dtype=float) - train_oof

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for split, frame in [("validation", val_sim), ("test", test_sim)]:
        metric_rows.append(metric_row("base_similarity_k160_q50", split, frame, base_pred[split], "user_meta + artwork similarity k160 q50", {"selected_rate": 0.0}))
        pred_frames.append(prediction_frame("base_similarity_k160_q50", split, frame, base_pred[split], "base"))

    for top_k in NEIGHBOR_KS:
        prefix = f"artist_meta_no_missing_k{top_k}"
        stats = {
            "validation": residual_neighbor_stat(train_sim, val_sim, artist_sim_no_missing, train_residual, top_k=top_k, prefix=prefix),
            "test": residual_neighbor_stat(train_sim, test_sim, artist_sim_no_missing, train_residual, top_k=top_k, prefix=prefix),
        }
        for strength in STRENGTHS:
            for cap in CAPS:
                candidate = f"resid_artist_meta_no_missing_k{top_k}_s{str(strength).replace('.', 'p')}_cap{str(cap).replace('.', 'p')}"
                policy = f"artist_meta_no_missing top_k={top_k} residual median, correction=clip({strength:.2f}*median, +/-{cap:.2f})"
                for split, frame in [("validation", val_sim), ("test", test_sim)]:
                    correction = np.clip(
                        strength * stats[split][f"{prefix}_resid_median"].to_numpy(dtype=float),
                        -cap,
                        cap,
                    )
                    pred = base_pred[split] + correction
                    metric_rows.append(metric_row(candidate, split, frame, pred, policy, {
                        "neighbor_family": "artist_meta_no_missing",
                        "top_k": top_k,
                        "strength": strength,
                        "cap_log": cap,
                        "selected_rate": 1.0,
                    }))
                    pred_frames.append(prediction_frame(candidate, split, frame, pred, policy, correction))

    metrics_df = pd.DataFrame(metric_rows)
    source_predictions = pd.concat(pred_frames, ignore_index=True)
    routed_frames = [
        routed_prediction_frame(source_predictions, split, candidate)
        for split in ["validation", "test"]
        for candidate in FOCUS_ROUTE_CANDIDATES
    ]
    routed_predictions = pd.concat(routed_frames, ignore_index=True)
    routed_metrics = pd.DataFrame([
        routed_metric_row(candidate, split, group)
        for (candidate, split), group in routed_predictions.groupby(["candidate", "split"], observed=False)
    ])
    boot_df = paired_bootstraps(routed_predictions)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_missing_flags_in_model_features": True,
        "uses_missing_flags_in_similarity_features": False,
        "removed_similarity_features": removed,
        "artist_similarity_features": artist_sim_no_missing,
        "base_top_k": BASE_TOP_K,
        "neighbor_ks": NEIGHBOR_KS,
        "strengths": STRENGTHS,
        "caps": CAPS,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    source_predictions.to_csv(OUT / "source_predictions.csv", index=False)
    routed_metrics.to_csv(OUT / "routed_metrics.csv", index=False)
    routed_predictions.to_csv(OUT / "routed_predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_base.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, routed_metrics, boot_df, summary)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
