#!/usr/bin/env python3
"""PP-CSIM21: rule-router grid for Cold k160/k320 candidates.

PP-CSIM20 showed that a learned router underperformed the simple rule router,
while oracle diagnostics confirmed that better k160/k320 selection can improve
Cold accuracy.  This experiment searches transparent rule-router variants and
selects policies by validation, then reports test.

Rules use only inference-time signals:
- k160 prediction
- k320 prediction
- similar-artwork k160 reference stats
- artwork dimensions and enterable artist metadata indirectly through candidate
  predictions

No rule uses actual validation/test price.
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


EXP_ID = "PP-CSIM21"
SLUG = "PP-CSIM21_cold_rule_router_grid"
TITLE = "Cold 규칙 라우터 그리드 탐색"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim21_cold_rule_router_grid_summary.md"

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


def fit_model(train: pd.DataFrame, features: list[str]):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    model = lgbm_quantile_model(train_n, features, alpha=0.35)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return model


def predict_model(model: Any, train: pd.DataFrame, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    _, frame_n, _ = normalize_for_model(train.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
    return np.asarray(model.predict(frame_n[features]), dtype=float)


def signals(frame: pd.DataFrame, base_pred: np.ndarray, k320_pred: np.ndarray) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    out["base_pred"] = base_pred
    out["k320_pred"] = k320_pred
    out["base_price"] = np.exp(base_pred)
    out["k320_lower_gap"] = base_pred - k320_pred
    ref_med = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_median"), errors="coerce")
    ref_q25 = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_q25"), errors="coerce")
    ref_iqr = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_iqr"), errors="coerce").fillna(0.0)
    ref_std = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_std"), errors="coerce").fillna(0.0)
    out["ref_median"] = ref_med
    out["ref_q25"] = ref_q25
    out["ref_iqr"] = ref_iqr
    out["ref_std"] = ref_std
    out["ref_median_price"] = np.exp(ref_med)
    out["base_minus_ref_median"] = base_pred - ref_med.to_numpy(dtype=float)
    out["base_minus_ref_q25"] = base_pred - ref_q25.to_numpy(dtype=float)
    return out


def build_rule_masks(sig: pd.DataFrame) -> dict[str, tuple[np.ndarray, str]]:
    base_price = sig["base_price"].to_numpy(dtype=float)
    ref_price = sig["ref_median_price"].to_numpy(dtype=float)
    lower_gap = sig["k320_lower_gap"].to_numpy(dtype=float)
    above_q25 = sig["base_minus_ref_q25"].to_numpy(dtype=float)
    above_med = sig["base_minus_ref_median"].to_numpy(dtype=float)
    ref_iqr = sig["ref_iqr"].to_numpy(dtype=float)
    masks: dict[str, tuple[np.ndarray, str]] = {
        "base_k160": (np.zeros(len(sig), dtype=bool), "항상 k160 q35"),
        "k320_global": (np.ones(len(sig), dtype=bool), "항상 k320 combined q35"),
    }
    for gap in [0.00, 0.03, 0.05, 0.08, 0.12]:
        lower = lower_gap > gap
        for cap in [2_000_000, 3_000_000, 5_000_000, 8_000_000]:
            masks[f"pred_lt_{cap//10000}w_gap{str(gap).replace('.', 'p')}"] = (
                (base_price < cap) & lower,
                f"k160 예측가 {cap//10000}만원 미만이고 k320이 {gap:.2f} log 이상 낮으면 k320",
            )
            masks[f"ref_lt_{cap//10000}w_gap{str(gap).replace('.', 'p')}"] = (
                np.isfinite(ref_price) & (ref_price < cap) & lower,
                f"유사작품 기준가 {cap//10000}만원 미만이고 k320이 {gap:.2f} log 이상 낮으면 k320",
            )
            masks[f"pred_or_ref_lt_{cap//10000}w_gap{str(gap).replace('.', 'p')}"] = (
                ((base_price < cap) | (np.isfinite(ref_price) & (ref_price < cap))) & lower,
                f"k160 예측가 또는 유사작품 기준가 {cap//10000}만원 미만이고 k320이 {gap:.2f} log 이상 낮으면 k320",
            )
        for qgap in [0.10, 0.20, 0.30, 0.45]:
            masks[f"above_q25_{str(qgap).replace('.', 'p')}_gap{str(gap).replace('.', 'p')}"] = (
                np.isfinite(above_q25) & (above_q25 > qgap) & lower,
                f"k160 예측이 유사작품 q25보다 {qgap:.2f} log 이상 높고 k320이 {gap:.2f} log 이상 낮으면 k320",
            )
            masks[f"above_med_{str(qgap).replace('.', 'p')}_gap{str(gap).replace('.', 'p')}"] = (
                np.isfinite(above_med) & (above_med > qgap) & lower,
                f"k160 예측이 유사작품 중앙값보다 {qgap:.2f} log 이상 높고 k320이 {gap:.2f} log 이상 낮으면 k320",
            )
        for iqr in [0.60, 0.90, 1.20]:
            masks[f"iqr_{str(iqr).replace('.', 'p')}_above_q25_0p2_gap{str(gap).replace('.', 'p')}"] = (
                (ref_iqr > iqr) & np.isfinite(above_q25) & (above_q25 > 0.20) & lower,
                f"유사작품 IQR {iqr:.2f} 초과, q25 대비 과대, k320이 {gap:.2f} log 이상 낮으면 k320",
            )
        masks[f"low_or_above_ref_gap{str(gap).replace('.', 'p')}"] = (
            (
                (base_price < 5_000_000)
                | (np.isfinite(ref_price) & (ref_price < 5_000_000))
                | (np.isfinite(above_q25) & (above_q25 > 0.20))
                | (np.isfinite(above_med) & (above_med > 0.15))
            ) & lower,
            f"저가 또는 유사작품 대비 과대 후보이고 k320이 {gap:.2f} log 이상 낮으면 k320",
        )
    return masks


def apply_mask(base_pred: np.ndarray, k320_pred: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return np.where(mask, k320_pred, base_pred)


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, selected: np.ndarray) -> dict[str, Any]:
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        "k320_selected_rate": float(np.mean(selected)),
        "k320_selected_n": int(np.sum(selected)),
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
    }


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, selected: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "k320_selected": selected.astype(int),
        "policy": policy,
    })


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
            pred = group["pred_log"].to_numpy(dtype=float)
            rows.append({
                "candidate": candidate,
                "split": split,
                "segment": str(segment),
                "n": int(len(group)),
                "k320_selected_rate": float(group["k320_selected"].mean()),
                **metrics(
                    group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                    ),
                    pred,
                ),
                **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
            })
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "APE_gt_2", "APE_gt_5", "APE_gt_10", "k320_selected_rate", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "k320_selected_rate", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["APE_gt_5", "MAPE", "p95_APE", "MdAPE"]).head(20)
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE", "MdAPE"]).head(20)
    selected = unique(["base_k160", "k320_global"] + val["candidate"].head(6).tolist())
    test_selected = metrics_df[(metrics_df["split"].eq("test")) & (metrics_df["candidate"].isin(selected))].sort_values(["APE_gt_5", "MAPE", "p95_APE"])
    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: transparent rule router를 validation에서 고르고 test에서 확인한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 정책 선택은 validation 기준이며, test는 확인용이다.",
        "",
        "## 1. Validation 상위 정책",
        md_table(val, metric_cols),
        "",
        "## 2. Validation 선택 후보의 Test 결과",
        md_table(test_selected, metric_cols),
        "",
        "## 3. Test 상위 정책 참고",
        md_table(test, metric_cols),
        "",
        "## 4. Paired bootstrap vs base_k160",
        md_table(boot_df, boot_cols),
        "",
        "## 5. 가격대별 진단",
        md_table(seg_df, seg_cols),
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Validation 상위 정책</h2>{html_table(val, metric_cols)}
<h2>Validation 선택 후보의 Test 결과</h2>{html_table(test_selected, metric_cols)}
<h2>Test 상위 정책 참고</h2>{html_table(test, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>가격대별 진단</h2>{html_table(seg_df, seg_cols)}
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

    base_features = unique(enterable_base + ref160)
    k320_features = unique(enterable_base + ref320 + ref320w)
    base_model = fit_model(train160, base_features)
    k320_model = fit_model(train320c, k320_features)

    split_data: dict[str, dict[str, Any]] = {
        "validation": {
            "frame": val160,
            "base_pred": predict_model(base_model, train160, val160, base_features),
            "k320_pred": predict_model(k320_model, train320c, val320c, k320_features),
        },
        "test": {
            "frame": test160,
            "base_pred": predict_model(base_model, train160, test160, base_features),
            "k320_pred": predict_model(k320_model, train320c, test320c, k320_features),
        },
    }
    for pack in split_data.values():
        pack["signals"] = signals(pack["frame"], pack["base_pred"], pack["k320_pred"])
        pack["masks"] = build_rule_masks(pack["signals"])

    metric_rows = []
    pred_frames = []
    for split, pack in split_data.items():
        for name, (mask, policy) in pack["masks"].items():
            pred = apply_mask(pack["base_pred"], pack["k320_pred"], mask)
            metric_rows.append(metric_row(name, split, pack["frame"], pred, policy, mask))
            pred_frames.append(prediction_frame(name, split, pack["frame"], pred, policy, mask))
    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    val_top = metrics_df[metrics_df["split"].eq("validation")].sort_values(["APE_gt_5", "MAPE", "p95_APE", "MdAPE"]).head(12)["candidate"].tolist()
    boot_rows = []
    for split, pack in split_data.items():
        base_pred = pack["base_pred"]
        frame = pack["frame"]
        for name in unique(["k320_global"] + val_top):
            if name == "base_k160":
                continue
            mask = pack["masks"][name][0]
            pred = apply_mask(pack["base_pred"], pack["k320_pred"], mask)
            boot_rows.append(paired_bootstrap(
                frame,
                pred,
                base_pred,
                a_name=name,
                b_name="base_k160",
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)
    seg_candidates = unique(["base_k160", "k320_global"] + val_top[:6])
    seg_df = segment_summary(predictions_df, seg_candidates)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "uses_weighted_similarity_reference_stats": True,
        "router_used": True,
        "router_type": "transparent_rule_grid",
        "router_training_uses_validation_or_test_labels": False,
        "router_uses_actual_price_at_inference": False,
        "policy_count": int(metrics_df["candidate"].nunique()),
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_base_k160.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, boot_df, seg_df, summary)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
