#!/usr/bin/env python3
"""PP-CSIM23: strict Cold three-way k160/k320/k640 router.

PP-CSIM22 showed:
- k160_q35 remains a simple strong baseline.
- k320 adaptive rules can preserve MdAPE better.
- k640 adaptive rules can improve MAPE/tail more.

This experiment focuses on transparent three-way rules:
- default: k160_q35
- use k320 when low-price signals suggest a lower wider-k candidate is safer
- use k640 when uncertainty/tail signals suggest a wider comparison group is safer

Rules use inference-time signals only.
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


EXP_ID = "PP-CSIM23"
SLUG = "PP-CSIM23_cold_threeway_k_router"
TITLE = "Cold k160/k320/k640 3-way 규칙 라우터 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim23_cold_threeway_k_router_summary.md"

TOP_KS = [160, 320, 640]
ALPHAS = {"q10": 0.10, "q35": 0.35, "q90": 0.90}

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


def fit_predict_quantiles(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, dict[str, np.ndarray]]:
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
    family: str,
    policy: str,
    k320_rate: float | None = None,
    k640_rate: float | None = None,
) -> dict[str, Any]:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "family": family,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
    }
    if k320_rate is not None:
        row["k320_selected_rate"] = k320_rate
    if k640_rate is not None:
        row["k640_selected_rate"] = k640_rate
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


def base_signals(frame: pd.DataFrame, preds: dict[int, dict[str, dict[str, np.ndarray]]], split: str) -> pd.DataFrame:
    prefix = "artwork_sim_k160"
    out = pd.DataFrame(index=frame.index)
    out["k160"] = preds[160]["q35"][split]
    out["k320"] = preds[320]["q35"][split]
    out["k640"] = preds[640]["q35"][split]
    out["k160_price"] = np.exp(out["k160"].to_numpy(dtype=float))
    out["qwidth160"] = np.maximum(preds[160]["q90"][split] - preds[160]["q10"][split], 0.0)
    out["ref_median"] = pd.to_numeric(frame.get(f"{prefix}_ref_log_price_median"), errors="coerce")
    out["ref_q25"] = pd.to_numeric(frame.get(f"{prefix}_ref_log_price_q25"), errors="coerce")
    out["ref_iqr"] = pd.to_numeric(frame.get(f"{prefix}_ref_log_price_iqr"), errors="coerce").fillna(0.0)
    out["ref_median_price"] = np.exp(out["ref_median"].to_numpy(dtype=float))
    out["k320_lower_gap"] = out["k160"].to_numpy(dtype=float) - out["k320"].to_numpy(dtype=float)
    out["k640_lower_gap"] = out["k160"].to_numpy(dtype=float) - out["k640"].to_numpy(dtype=float)
    out["k640_vs_k320_lower_gap"] = out["k320"].to_numpy(dtype=float) - out["k640"].to_numpy(dtype=float)
    return out


def rule_specs(validation_signals: pd.DataFrame) -> dict[str, dict[str, Any]]:
    qwidth_thresholds = {
        "q50": float(validation_signals["qwidth160"].quantile(0.50)),
        "q67": float(validation_signals["qwidth160"].quantile(0.67)),
        "q75": float(validation_signals["qwidth160"].quantile(0.75)),
    }
    ref_iqr_thresholds = {
        "q50": float(validation_signals["ref_iqr"].quantile(0.50)),
        "q67": float(validation_signals["ref_iqr"].quantile(0.67)),
        "q75": float(validation_signals["ref_iqr"].quantile(0.75)),
    }
    specs: dict[str, dict[str, Any]] = {}
    for cap in [3_000_000, 5_000_000, 8_000_000, 10_000_000]:
        cap_name = f"{cap // 10000}w"
        for gap in [0.00, 0.03, 0.05, 0.08]:
            gap_name = str(gap).replace(".", "p")
            specs[f"low_{cap_name}_k320_else_k160_gap{gap_name}"] = {
                "family": "two_way_low_k320",
                "cap": cap,
                "gap320": gap,
                "gap640": gap,
                "qwidth_threshold": None,
                "ref_iqr_threshold": None,
                "mode": "low_k320",
                "policy": f"k160 예측가 또는 유사작품 기준가가 {cap//10000}만원 미만이고 k320이 {gap:.2f} log 이상 낮으면 k320, 아니면 k160",
            }
            specs[f"low_{cap_name}_k640_else_k160_gap{gap_name}"] = {
                "family": "two_way_low_k640",
                "cap": cap,
                "gap320": gap,
                "gap640": gap,
                "qwidth_threshold": None,
                "ref_iqr_threshold": None,
                "mode": "low_k640",
                "policy": f"k160 예측가 또는 유사작품 기준가가 {cap//10000}만원 미만이고 k640이 {gap:.2f} log 이상 낮으면 k640, 아니면 k160",
            }
            for qname, qthr in qwidth_thresholds.items():
                specs[f"qwidth_{qname}_k640_low_{cap_name}_k320_gap{gap_name}"] = {
                    "family": "three_way_qwidth_first",
                    "cap": cap,
                    "gap320": gap,
                    "gap640": gap,
                    "qwidth_threshold": qthr,
                    "ref_iqr_threshold": None,
                    "mode": "qwidth640_then_low320",
                    "policy": f"qwidth160 >= validation {qname}이면 k640 우선, 아니면 저가 {cap//10000}만원 조건에서 k320. 둘 다 기존보다 {gap:.2f} log 이상 낮을 때만 교체",
                }
                specs[f"low_{cap_name}_k320_qwidth_{qname}_k640_gap{gap_name}"] = {
                    "family": "three_way_low_first",
                    "cap": cap,
                    "gap320": gap,
                    "gap640": gap,
                    "qwidth_threshold": qthr,
                    "ref_iqr_threshold": None,
                    "mode": "low320_then_qwidth640",
                    "policy": f"저가 {cap//10000}만원 조건에서는 k320 우선, 그 외 qwidth160 >= validation {qname}이면 k640. 둘 다 기존보다 {gap:.2f} log 이상 낮을 때만 교체",
                }
            for iname, ithr in ref_iqr_thresholds.items():
                specs[f"refiqr_{iname}_k640_low_{cap_name}_k320_gap{gap_name}"] = {
                    "family": "three_way_refiqr_first",
                    "cap": cap,
                    "gap320": gap,
                    "gap640": gap,
                    "qwidth_threshold": None,
                    "ref_iqr_threshold": ithr,
                    "mode": "refiqr640_then_low320",
                    "policy": f"유사작품 IQR >= validation {iname}이면 k640 우선, 아니면 저가 {cap//10000}만원 조건에서 k320. 둘 다 기존보다 {gap:.2f} log 이상 낮을 때만 교체",
                }
    return specs


def apply_rule(sig: pd.DataFrame, spec: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    base = sig["k160"].to_numpy(dtype=float)
    use320 = np.zeros(len(sig), dtype=bool)
    use640 = np.zeros(len(sig), dtype=bool)
    cap = float(spec["cap"])
    low = (sig["k160_price"].to_numpy(dtype=float) < cap) | (sig["ref_median_price"].to_numpy(dtype=float) < cap)
    lower320 = sig["k320_lower_gap"].to_numpy(dtype=float) > float(spec["gap320"])
    lower640 = sig["k640_lower_gap"].to_numpy(dtype=float) > float(spec["gap640"])
    qwidth_high = np.zeros(len(sig), dtype=bool)
    if spec.get("qwidth_threshold") is not None:
        qwidth_high = sig["qwidth160"].to_numpy(dtype=float) >= float(spec["qwidth_threshold"])
    refiqr_high = np.zeros(len(sig), dtype=bool)
    if spec.get("ref_iqr_threshold") is not None:
        refiqr_high = sig["ref_iqr"].to_numpy(dtype=float) >= float(spec["ref_iqr_threshold"])

    mode = spec["mode"]
    if mode == "low_k320":
        use320 = low & lower320
    elif mode == "low_k640":
        use640 = low & lower640
    elif mode == "qwidth640_then_low320":
        use640 = qwidth_high & lower640
        use320 = (~use640) & low & lower320
    elif mode == "low320_then_qwidth640":
        use320 = low & lower320
        use640 = (~use320) & qwidth_high & lower640
    elif mode == "refiqr640_then_low320":
        use640 = refiqr_high & lower640
        use320 = (~use640) & low & lower320
    else:
        raise ValueError(mode)

    pred = base.copy()
    pred[use320] = sig.loc[use320, "k320"].to_numpy(dtype=float)
    pred[use640] = sig.loc[use640, "k640"].to_numpy(dtype=float)
    return pred, use320, use640


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


def write_reports(metrics_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "family", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "APE_gt_2", "APE_gt_5", "APE_gt_10", "k320_selected_rate", "k640_selected_rate", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(30)
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(30)
    tail = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"]).head(30)
    selected = unique(["k160_q35", "k320_q35", "k640_q35"] + val["candidate"].head(8).tolist() + test["candidate"].head(8).tolist() + tail["candidate"].head(8).tolist())
    selected_test = metrics_df[metrics_df["split"].eq("test") & metrics_df["candidate"].isin(selected)].sort_values(["MAPE", "p95_APE", "MdAPE"])
    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: PP-CSIM22에서 확인된 k320/k640 장단점을 3-way 규칙으로 결합할 수 있는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 정책 선택은 validation 기준이며, test는 확인용이다.",
        "",
        "## 1. Validation 상위 정책",
        md_table(val, metric_cols),
        "",
        "## 2. Validation 선택/주요 후보의 Test 결과",
        md_table(selected_test, metric_cols),
        "",
        "## 3. Test 상위 정책: MAPE 기준",
        md_table(test, metric_cols),
        "",
        "## 4. Test 상위 정책: APE > 5 기준",
        md_table(tail, metric_cols),
        "",
        "## 5. Paired bootstrap vs k160_q35",
        md_table(boot_df, boot_cols),
        "",
        "## 6. 가격대별 진단",
        md_table(seg_df, seg_cols),
        "",
        "## 7. 해석",
        "- k320은 중앙 오차 방어, k640은 MAPE/tail 방어에 쓰일 수 있는지 확인한다.",
        "- 3-way 규칙은 실제 가격을 보지 않고 k160/k320/k640 예측값, k160 유사작품 기준가, qwidth/IQR만 사용한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Validation 상위 정책</h2>{html_table(val, metric_cols)}
<h2>주요 후보 Test 결과</h2>{html_table(selected_test, metric_cols)}
<h2>Test MAPE 기준</h2>{html_table(test, metric_cols)}
<h2>Test APE &gt; 5 기준</h2>{html_table(tail, metric_cols)}
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
    preds: dict[int, dict[str, dict[str, np.ndarray]]] = {}
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
        frames[top_k] = {"train": train_k, "validation": val_k, "test": test_k}
        preds[top_k] = fit_predict_quantiles(train_k, val_k, test_k, features)

    base_frame_by_split = {"validation": frames[160]["validation"], "test": frames[160]["test"]}
    sig_by_split = {
        "validation": base_signals(base_frame_by_split["validation"], preds, "validation"),
        "test": base_signals(base_frame_by_split["test"], preds, "test"),
    }
    specs = rule_specs(sig_by_split["validation"])
    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []

    fixed_policies = {
        "k160_q35": ("fixed_k", "항상 유사작품 160건 기준 q35"),
        "k320_q35": ("fixed_k", "항상 유사작품 320건 기준 q35"),
        "k640_q35": ("fixed_k", "항상 유사작품 640건 기준 q35"),
    }
    for split, frame in base_frame_by_split.items():
        for candidate, (family, policy) in fixed_policies.items():
            k = int(candidate.split("_")[0].replace("k", ""))
            pred = preds[k]["q35"][split]
            metric_rows.append(metric_row(candidate, split, frame, pred, family=family, policy=policy))
            pred_frames.append(prediction_frame(candidate, split, frame, pred, family))

    for name, spec in specs.items():
        for split, frame in base_frame_by_split.items():
            pred, use320, use640 = apply_rule(sig_by_split[split], spec)
            metric_rows.append(metric_row(
                name,
                split,
                frame,
                pred,
                family=spec["family"],
                policy=spec["policy"],
                k320_rate=float(np.mean(use320)),
                k640_rate=float(np.mean(use640)),
            ))
            pred_frames.append(prediction_frame(name, split, frame, pred, spec["family"]))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    selected = unique(
        ["k160_q35", "k320_q35", "k640_q35"]
        + metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(12)["candidate"].tolist()
        + metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(12)["candidate"].tolist()
        + metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"]).head(8)["candidate"].tolist()
    )
    boot_rows = []
    for split, frame in base_frame_by_split.items():
        frame_sorted = frame.sort_values("_track6_row_id").reset_index(drop=True)
        base_pred = predictions_df[
            predictions_df["split"].eq(split) & predictions_df["candidate"].eq("k160_q35")
        ].sort_values("_track6_row_id")["pred_log"].to_numpy(dtype=float)
        for cand in selected:
            if cand == "k160_q35":
                continue
            cand_pred = predictions_df[
                predictions_df["split"].eq(split) & predictions_df["candidate"].eq(cand)
            ].sort_values("_track6_row_id")["pred_log"].to_numpy(dtype=float)
            row = paired_bootstrap(frame_sorted, cand_pred, base_pred, a_name=cand, b_name="k160_q35", n_boot=800, seed=20260619)
            row["split"] = split
            boot_rows.append(row)
    boot_df = pd.DataFrame(boot_rows)
    seg_df = segment_summary(predictions_df, selected[:18])

    summary = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold": strict_cold_run_summary({
            "feature_columns": enterable_base,
            "notes": [
                "three-way rules use inference-time k160/k320/k640 predictions and k160 reference stats only",
                "no rule uses actual validation/test price labels",
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
    print(metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(12).to_string(index=False))


if __name__ == "__main__":
    main()
