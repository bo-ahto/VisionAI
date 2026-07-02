#!/usr/bin/env python3
"""PP-CSIM14: Cold q35 selection policy search.

PP-CSIM13 showed that full q35 improves tail but hurts high-price rows.  This
experiment searches inference-time policies that choose q35 only where it is
likely to help, using validation metrics to select candidates and reporting
test metrics for the same frozen rules.
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


EXP_ID = "PP-CSIM14"
SLUG = "PP-CSIM14_cold_q35_selection_policy_search"
TITLE = "Cold q35 선택 정책 탐색"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim14_cold_q35_selection_policy_search_summary.md"

TOP_K = 160

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


def fit_quantile(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str], *, alpha: float) -> dict[str, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return {
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
    }


def add_inference_signals(frame: pd.DataFrame, q45: np.ndarray, q35: np.ndarray) -> pd.DataFrame:
    out = frame[["_track6_row_id", "ln_price_krw", "price_krw"]].copy()
    out["q45"] = q45
    out["q35"] = q35
    out["q_gap"] = q45 - q35
    out["pred_q45_price"] = np.exp(q45)
    ref_med = pd.to_numeric(frame.get(f"artwork_sim_k{TOP_K}_ref_log_price_median"), errors="coerce").to_numpy(dtype=float)
    ref_q25 = pd.to_numeric(frame.get(f"artwork_sim_k{TOP_K}_ref_log_price_q25"), errors="coerce").to_numpy(dtype=float)
    ref_iqr = pd.to_numeric(frame.get(f"artwork_sim_k{TOP_K}_ref_log_price_iqr"), errors="coerce").fillna(0.0).to_numpy(dtype=float)
    ref_std = pd.to_numeric(frame.get(f"artwork_sim_k{TOP_K}_ref_log_price_std"), errors="coerce").fillna(0.0).to_numpy(dtype=float)
    out["ref_median"] = ref_med
    out["ref_q25"] = ref_q25
    out["ref_iqr"] = ref_iqr
    out["ref_std"] = ref_std
    out["ref_median_price"] = np.exp(ref_med)
    out["basis_minus_ref_median"] = q45 - ref_med
    out["basis_minus_ref_q25"] = q45 - ref_q25
    out["actual_ape_q45"] = np.abs(np.exp(q45) - out["price_krw"]) / np.maximum(out["price_krw"], 1.0)
    out["actual_ape_q35"] = np.abs(np.exp(q35) - out["price_krw"]) / np.maximum(out["price_krw"], 1.0)
    out["q35_wins"] = out["actual_ape_q35"] < out["actual_ape_q45"]
    return out


def policy_masks(signals: pd.DataFrame) -> dict[str, np.ndarray]:
    pred = signals["pred_q45_price"].to_numpy(dtype=float)
    ref = signals["ref_median_price"].to_numpy(dtype=float)
    iqr = signals["ref_iqr"].to_numpy(dtype=float)
    gap_ref = signals["basis_minus_ref_median"].to_numpy(dtype=float)
    gap_q25 = signals["basis_minus_ref_q25"].to_numpy(dtype=float)
    masks: dict[str, np.ndarray] = {
        "always_q45": np.zeros(len(signals), dtype=bool),
        "always_q35": np.ones(len(signals), dtype=bool),
    }
    for pred_cap in [1_000_000, 1_500_000, 2_000_000, 3_000_000]:
        masks[f"pred_lt_{pred_cap//10000}w"] = pred < pred_cap
    for pred_cap in [1_500_000, 2_000_000, 3_000_000]:
        for ref_cap in [1_500_000, 2_000_000, 3_000_000]:
            masks[f"pred{pred_cap//10000}w_ref{ref_cap//10000}w"] = (pred < pred_cap) & np.isfinite(ref) & (ref < ref_cap)
    for pred_cap in [2_000_000, 3_000_000]:
        for iqr_cap in [0.75, 1.00, 1.25]:
            masks[f"pred{pred_cap//10000}w_iqr{str(iqr_cap).replace('.', 'p')}"] = (pred < pred_cap) & (iqr < iqr_cap)
    for gap_cap in [0.20, 0.35, 0.50]:
        masks[f"q45_above_ref_{str(gap_cap).replace('.', 'p')}"] = np.isfinite(gap_ref) & (gap_ref > gap_cap)
        masks[f"q45_above_refq25_{str(gap_cap).replace('.', 'p')}"] = np.isfinite(gap_q25) & (gap_q25 > gap_cap)
    for pred_cap in [2_000_000, 3_000_000]:
        for gap_cap in [0.20, 0.35]:
            masks[f"pred{pred_cap//10000}w_above_ref_{str(gap_cap).replace('.', 'p')}"] = (pred < pred_cap) & np.isfinite(gap_ref) & (gap_ref > gap_cap)
    return masks


def apply_mask(q45: np.ndarray, q35: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return np.where(mask, q35, q45)


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


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, mask: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "q35_selected": mask.astype(int),
        "policy": policy,
    })


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
        rows.append({
            "candidate": candidate,
            "split": split,
            "segment": str(segment),
            "n": int(len(group)),
            "q35_selected_rate": float(group["q35_selected"].mean()),
            **metrics(
                group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                    columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                ),
                pred,
            ),
            **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
        })
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    artwork_features = unique(fs["cold_lgb"])
    enterable_base = unique(artwork_features + ENTERABLE_META + ENTERABLE_BUCKETS)
    required = unique(enterable_base + USER_META_CORE + META_BUCKET_FEATURES + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    assert_strict_cold_features(enterable_base, context=f"{EXP_ID}:enterable_base")

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train,
        val,
        test,
        ARTWORK_SIM_FEATURES,
        prefix=f"artwork_sim_k{TOP_K}",
        top_k=TOP_K,
    )
    features = unique(enterable_base + art_ref_features)

    pred45 = fit_quantile(train_art, val_art, test_art, features, alpha=0.45)
    pred35 = fit_quantile(train_art, val_art, test_art, features, alpha=0.35)
    signals = {
        "validation": add_inference_signals(val_art, pred45["validation"], pred35["validation"]),
        "test": add_inference_signals(test_art, pred45["test"], pred35["test"]),
    }
    signals["validation"].to_csv(OUT / "validation_q35_win_signals.csv", index=False)
    signals["test"].to_csv(OUT / "test_q35_win_signals.csv", index=False)

    val_masks = policy_masks(signals["validation"])
    test_masks = policy_masks(signals["test"])
    policy_rows = []
    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for name, val_mask in val_masks.items():
        test_mask = test_masks[name]
        for split, frame, mask in [("validation", val_art, val_mask), ("test", test_art, test_mask)]:
            pred = apply_mask(pred45[split], pred35[split], mask)
            extra = {
                "q35_selected_rate": float(np.mean(mask)),
                "validation_policy": name,
            }
            metric_rows.append(metric_row(name, split, frame, pred, f"{name}: 조건 통과 시 q35, 아니면 q45", extra))
            pred_frames.append(prediction_frame(name, split, frame, pred, f"{name}: 조건 통과 시 q35, 아니면 q45", mask))
        q35_win_rate = float(signals["validation"].loc[val_mask, "q35_wins"].mean()) if np.any(val_mask) else 0.0
        policy_rows.append({
            "candidate": name,
            "validation_selected_n": int(np.sum(val_mask)),
            "validation_selected_rate": float(np.mean(val_mask)),
            "validation_selected_q35_win_rate": q35_win_rate,
        })

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    policy_df = pd.DataFrame(policy_rows)
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
        "router_used": True,
        "router_uses_actual_price": False,
        "q35_selection_policy_search": True,
        "top_k": TOP_K,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    policy_df.to_csv(OUT / "policy_selection_diagnostics.csv", index=False)
    segment_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10",
        "q35_selected_rate", "policy",
    ]
    policy_cols = ["candidate", "validation_selected_n", "validation_selected_rate", "validation_selected_q35_win_rate"]
    seg_cols = ["candidate", "split", "segment", "n", "q35_selected_rate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5"]
    val_metrics = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    tail_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "p95_APE", "MAPE"])
    best_validation = val_metrics.iloc[0]["candidate"]
    best_test = test_metrics.iloc[0]["candidate"]
    best_tail = tail_metrics.iloc[0]["candidate"]

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: q35가 도움이 되는 구간을 사용 단계에서 알 수 있는 피처로 선택할 수 있는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "",
        "## 1. Validation 결과: MdAPE 기준",
        md_table(val_metrics.head(12), metric_cols),
        "",
        "## 2. Test 결과: MdAPE 기준",
        md_table(test_metrics.head(12), metric_cols),
        "",
        "## 3. Test 결과: APE > 5 기준",
        md_table(tail_metrics.head(12), metric_cols),
        "",
        "## 4. 정책 선택 진단",
        md_table(policy_df.sort_values(["validation_selected_q35_win_rate", "validation_selected_rate"], ascending=[False, False]).head(16), policy_cols),
        "",
        "## 5. 가격대별 진단",
        md_table(segment_df[segment_df["candidate"].isin([best_validation, best_test, best_tail, "always_q45", "always_q35"])].sort_values(["segment", "candidate"]), seg_cols),
        "",
        "## 6. 결론",
        "",
        f"- validation MdAPE 기준 최상위 정책은 `{best_validation}`이다.",
        f"- test MdAPE 기준 최상위 정책은 `{best_test}`이다.",
        f"- test APE > 5 기준 최상위 정책은 `{best_tail}`이다.",
        "- 정책 탐색은 validation에서 선택하고 test에서 확인해야 하며, test만 보고 고른 정책은 운영 근거로 쓰지 않는다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Validation 결과</h2>{html_table(val_metrics.head(12), metric_cols)}
<h2>Test 결과</h2>{html_table(test_metrics.head(12), metric_cols)}
<h2>정책 선택 진단</h2>{html_table(policy_df.sort_values(['validation_selected_q35_win_rate', 'validation_selected_rate'], ascending=[False, False]).head(16), policy_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
