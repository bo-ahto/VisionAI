#!/usr/bin/env python3
"""PP-CSIM22: adaptive-k and Quantile grid for strict Cold.

This experiment extends PP-CSIM17/21:
- fixed top-k grid: 40, 80, 120, 160, 200, 240, 320, 480, 640
- Quantile alpha grid: q35, q45, q50, plus q10/q90 for uncertainty width
- transparent adaptive-k rules using only inference-time signals

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
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM22"
SLUG = "PP-CSIM22_cold_adaptive_k_quantile_grid"
TITLE = "Cold adaptive-k / Quantile 유사작품 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim22_cold_adaptive_k_quantile_grid_summary.md"

TOP_KS = [40, 80, 120, 160, 200, 240, 320, 480, 640]
ALPHAS = {"q10": 0.10, "q35": 0.35, "q45": 0.45, "q50": 0.50, "q90": 0.90}

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


def fit_predict_quantiles(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
) -> dict[str, dict[str, np.ndarray]]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    y = train_n["ln_price_krw"].to_numpy(dtype=float)
    out: dict[str, dict[str, np.ndarray]] = {}
    for name, alpha in ALPHAS.items():
        model = lgbm_quantile_model(train_n, features, alpha=alpha)
        model.fit(train_n[features], y)
        out[name] = {
            "validation": np.asarray(model.predict(val_n[features]), dtype=float),
            "test": np.asarray(model.predict(test_n[features]), dtype=float),
        }
    return out


def metric_row(
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred: np.ndarray,
    *,
    top_k: int | None,
    alpha_name: str,
    family: str,
    policy: str,
    selected_rate: float | None = None,
) -> dict[str, Any]:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "family": family,
        "scope": "cold",
        "split": split,
        "top_k": top_k,
        "alpha": alpha_name,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
    }
    if selected_rate is not None:
        row["adaptive_selected_rate"] = selected_rate
    return row


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


def split_signals(frame: pd.DataFrame, preds: dict[int, dict[str, dict[str, np.ndarray]]], split: str, k: int) -> pd.DataFrame:
    prefix = f"artwork_sim_k{k}"
    out = pd.DataFrame(index=frame.index)
    out["qwidth"] = np.maximum(preds[k]["q90"][split] - preds[k]["q10"][split], 0.0)
    out["q35_pred"] = preds[k]["q35"][split]
    out["q45_pred"] = preds[k]["q45"][split]
    out["q50_pred"] = preds[k]["q50"][split]
    out["q35_price"] = np.exp(out["q35_pred"].to_numpy(dtype=float))
    out["ref_median"] = pd.to_numeric(frame.get(f"{prefix}_ref_log_price_median"), errors="coerce")
    out["ref_q25"] = pd.to_numeric(frame.get(f"{prefix}_ref_log_price_q25"), errors="coerce")
    out["ref_iqr"] = pd.to_numeric(frame.get(f"{prefix}_ref_log_price_iqr"), errors="coerce").fillna(0.0)
    out["ref_median_price"] = np.exp(out["ref_median"].to_numpy(dtype=float))
    out["pred_minus_ref_q25"] = out["q35_pred"].to_numpy(dtype=float) - out["ref_q25"].to_numpy(dtype=float)
    return out


def adaptive_candidates(
    frames: dict[int, dict[str, pd.DataFrame]],
    preds: dict[int, dict[str, dict[str, np.ndarray]]],
) -> dict[str, dict[str, Any]]:
    base_k = 160
    wider_ks = [200, 240, 320, 480, 640]
    val_sig = split_signals(frames[base_k]["validation"], preds, "validation", base_k)
    qwidth_thresholds = {
        "qwidth_q50": float(val_sig["qwidth"].quantile(0.50)),
        "qwidth_q67": float(val_sig["qwidth"].quantile(0.67)),
        "qwidth_q75": float(val_sig["qwidth"].quantile(0.75)),
    }
    ref_iqr_thresholds = {
        "refiqr_q50": float(val_sig["ref_iqr"].quantile(0.50)),
        "refiqr_q67": float(val_sig["ref_iqr"].quantile(0.67)),
        "refiqr_q75": float(val_sig["ref_iqr"].quantile(0.75)),
    }
    out: dict[str, dict[str, Any]] = {}
    for wider_k in wider_ks:
        for threshold_name, threshold in qwidth_thresholds.items():
            name = f"if_{threshold_name}_use_k{wider_k}"
            out[name] = {
                "family": "adaptive_qwidth",
                "policy": f"k160 q90-q10 예측 불확실성 폭이 validation {threshold_name}({threshold:.4f}) 이상이면 k{wider_k} q35, 아니면 k160 q35",
                "wider_k": wider_k,
                "mask_kind": "qwidth",
                "threshold": threshold,
            }
        for threshold_name, threshold in ref_iqr_thresholds.items():
            name = f"if_{threshold_name}_use_k{wider_k}"
            out[name] = {
                "family": "adaptive_ref_iqr",
                "policy": f"k160 유사작품 가격 IQR이 validation {threshold_name}({threshold:.4f}) 이상이면 k{wider_k} q35, 아니면 k160 q35",
                "wider_k": wider_k,
                "mask_kind": "ref_iqr",
                "threshold": threshold,
            }
        name = f"low_or_ref_low_and_k{wider_k}_lower"
        out[name] = {
            "family": "adaptive_low_tail",
            "policy": f"k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k{wider_k} q35가 k160 q35보다 낮으면 k{wider_k}, 아니면 k160",
            "wider_k": wider_k,
            "mask_kind": "low_tail_lower",
            "threshold": 8_000_000.0,
        }
        name = f"uncertain_and_k{wider_k}_lower"
        out[name] = {
            "family": "adaptive_qwidth_lower",
            "policy": f"k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k{wider_k} q35가 k160 q35보다 낮으면 k{wider_k}, 아니면 k160",
            "wider_k": wider_k,
            "mask_kind": "qwidth_lower",
            "threshold": qwidth_thresholds["qwidth_q67"],
        }
    return out


def adaptive_mask(sig: pd.DataFrame, wider_pred: np.ndarray, spec: dict[str, Any]) -> np.ndarray:
    base_pred = sig["q35_pred"].to_numpy(dtype=float)
    kind = spec["mask_kind"]
    threshold = float(spec["threshold"])
    if kind == "qwidth":
        return sig["qwidth"].to_numpy(dtype=float) >= threshold
    if kind == "ref_iqr":
        return sig["ref_iqr"].to_numpy(dtype=float) >= threshold
    if kind == "low_tail_lower":
        low = (sig["q35_price"].to_numpy(dtype=float) < threshold) | (sig["ref_median_price"].to_numpy(dtype=float) < threshold)
        return low & (wider_pred < base_pred)
    if kind == "qwidth_lower":
        return (sig["qwidth"].to_numpy(dtype=float) >= threshold) & (wider_pred < base_pred)
    raise ValueError(kind)


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
                **metrics(
                    group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                    ),
                    pred,
                ),
                **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
            })
    return pd.DataFrame(rows)


def write_reports(
    metrics_df: pd.DataFrame,
    boot_df: pd.DataFrame,
    seg_df: pd.DataFrame,
    summary: dict[str, Any],
) -> None:
    metric_cols = [
        "candidate", "family", "split", "top_k", "alpha", "MdAPE", "MAPE", "p95_APE",
        "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10", "adaptive_selected_rate", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]
    fixed = metrics_df[metrics_df["family"].eq("fixed_k")]
    fixed_test = fixed[fixed["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"])
    fixed_val = fixed[fixed["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"])
    adaptive_test = metrics_df[(metrics_df["split"].eq("test")) & metrics_df["family"].str.startswith("adaptive")].sort_values(["MAPE", "p95_APE", "MdAPE"])
    adaptive_val = metrics_df[(metrics_df["split"].eq("validation")) & metrics_df["family"].str.startswith("adaptive")].sort_values(["MAPE", "p95_APE", "MdAPE"])
    tail_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"]).head(30)
    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: Cold 유사작품 개수 k와 Quantile/불확실성 기반 adaptive-k 선택이 의미 있는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        f"- k 후보: {', '.join(map(str, TOP_KS))}",
        "- Quantile 후보: q35, q45, q50. q10/q90은 예측 불확실성 폭(q90-q10) 계산용.",
        "",
        "## 1. 고정 k Test 성능: MAPE 기준",
        md_table(fixed_test, metric_cols),
        "",
        "## 2. 고정 k Validation 성능: MAPE 기준",
        md_table(fixed_val, metric_cols),
        "",
        "## 3. adaptive-k Validation 성능: MAPE 기준",
        md_table(adaptive_val.head(30), metric_cols),
        "",
        "## 4. adaptive-k Test 성능: MAPE 기준",
        md_table(adaptive_test.head(30), metric_cols),
        "",
        "## 5. Test 성능: APE > 5 기준",
        md_table(tail_test, metric_cols),
        "",
        "## 6. Paired bootstrap vs base k160 q35",
        md_table(boot_df, boot_cols),
        "",
        "## 7. 가격대별 진단",
        md_table(seg_df, seg_cols),
        "",
        "## 8. 해석",
        "- k를 촘촘하게 늘려도 validation과 test가 같은 방향으로 좋아지는지 확인해야 한다.",
        "- q90-q10은 예측 불확실성 폭으로, k160이 불확실한 행에서 더 넓은 k를 쓰는 규칙이 효과적인지 확인하기 위한 신호다.",
        "- adaptive-k 후보는 실제 가격을 보지 않고 사용 단계에서 알 수 있는 예측값과 유사작품 통계만 사용한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}code{{background:#eef2f7;padding:2px 5px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<p>strict Cold 조건에서 k-grid, Quantile, adaptive-k 규칙을 비교한다.</p>
<h2>고정 k Test</h2>{html_table(fixed_test, metric_cols)}
<h2>고정 k Validation</h2>{html_table(fixed_val, metric_cols)}
<h2>adaptive-k Validation</h2>{html_table(adaptive_val.head(30), metric_cols)}
<h2>adaptive-k Test</h2>{html_table(adaptive_test.head(30), metric_cols)}
<h2>APE &gt; 5 기준</h2>{html_table(tail_test, metric_cols)}
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

    frames: dict[int, dict[str, pd.DataFrame]] = {}
    ref_features_by_k: dict[int, list[str]] = {}
    preds: dict[int, dict[str, dict[str, np.ndarray]]] = {}
    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []

    for top_k in TOP_KS:
        train_k, val_k, test_k, ref_features = compute_reference_stats(
            train,
            val,
            test,
            ARTWORK_SIM_FEATURES,
            prefix=f"artwork_sim_k{top_k}",
            top_k=top_k,
        )
        features = unique(enterable_base + ref_features)
        bundle = fit_predict_quantiles(train_k, val_k, test_k, features)
        frames[top_k] = {"train": train_k, "validation": val_k, "test": test_k}
        ref_features_by_k[top_k] = ref_features
        preds[top_k] = bundle
        for alpha_name in ["q35", "q45", "q50"]:
            for split, frame in [("validation", val_k), ("test", test_k)]:
                pred = bundle[alpha_name][split]
                candidate = f"k{top_k}_{alpha_name}"
                metric_rows.append(metric_row(
                    candidate,
                    split,
                    frame,
                    pred,
                    top_k=top_k,
                    alpha_name=alpha_name,
                    family="fixed_k",
                    policy=f"유사작품 {top_k}건 통계 + LightGBM Quantile {alpha_name}",
                ))
                pred_frames.append(prediction_frame(candidate, split, frame, pred, "fixed_k"))

    base_candidate = "k160_q35"
    adaptive_specs = adaptive_candidates(frames, preds)
    base_frame_by_split = {"validation": frames[160]["validation"], "test": frames[160]["test"]}
    for name, spec in adaptive_specs.items():
        wider_k = int(spec["wider_k"])
        for split in ["validation", "test"]:
            frame = base_frame_by_split[split]
            sig = split_signals(frame, preds, split, 160)
            base_pred = preds[160]["q35"][split]
            wider_pred = preds[wider_k]["q35"][split]
            mask = adaptive_mask(sig, wider_pred, spec)
            pred = np.where(mask, wider_pred, base_pred)
            metric_rows.append(metric_row(
                name,
                split,
                frame,
                pred,
                top_k=None,
                alpha_name="q35",
                family=spec["family"],
                policy=spec["policy"],
                selected_rate=float(np.mean(mask)),
            ))
            pred_frames.append(prediction_frame(name, split, frame, pred, spec["family"]))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    top_for_boot = unique(
        [base_candidate]
        + metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(10)["candidate"].tolist()
        + metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(10)["candidate"].tolist()
        + metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"]).head(8)["candidate"].tolist()
    )
    boot_rows = []
    for split in ["validation", "test"]:
        frame = base_frame_by_split[split]
        base_pred = predictions_df[
            predictions_df["split"].eq(split) & predictions_df["candidate"].eq(base_candidate)
        ].sort_values("_track6_row_id")["pred_log"].to_numpy(dtype=float)
        for cand in top_for_boot:
            if cand == base_candidate:
                continue
            cand_df = predictions_df[predictions_df["split"].eq(split) & predictions_df["candidate"].eq(cand)].sort_values("_track6_row_id")
            if len(cand_df) != len(frame):
                continue
            row = paired_bootstrap(
                frame.sort_values("_track6_row_id").reset_index(drop=True),
                cand_df["pred_log"].to_numpy(dtype=float),
                base_pred,
                a_name=cand,
                b_name=base_candidate,
                n_boot=800,
                seed=20260619,
            )
            row["split"] = split
            boot_rows.append(row)
    boot_df = pd.DataFrame(boot_rows)
    seg_candidates = unique([
        base_candidate,
        *metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(5)["candidate"].tolist(),
        *metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(5)["candidate"].tolist(),
        *metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"]).head(5)["candidate"].tolist(),
    ])
    seg_df = segment_summary(predictions_df, seg_candidates)

    summary = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "top_ks": TOP_KS,
        "alphas": ALPHAS,
        "strict_cold": strict_cold_run_summary({
            "feature_columns": enterable_base,
            "notes": [
                "fixed and adaptive k selection use inference-time predictions/reference stats only",
                "q10/q90 are used to compute qwidth, not as final price candidates",
            ],
        }),
        "metrics": json_clean(metrics_df.to_dict(orient="records")),
        "bootstrap": json_clean(boot_df.to_dict(orient="records")),
    }
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    seg_df.to_csv(OUT / "segment_summary.csv", index=False)
    write_reports(metrics_df, boot_df, seg_df, summary)
    print(f"[{EXP_ID}] wrote {DOC_MD}")
    print(metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(10).to_string(index=False))


if __name__ == "__main__":
    main()
