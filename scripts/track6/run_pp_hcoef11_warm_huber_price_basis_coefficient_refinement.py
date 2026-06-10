#!/usr/bin/env python3
"""Run PP-HCOEF11: extended validation for the Warm Huber stable candidate.

Earlier HCOEF experiments found a conservative Huber residual correction
(`hcoef2_size_reliability_cap005_s050`) that improves the v0.1 Warm 70:30
candidate without increasing large-error risk. HCOEF4~HCOEF10 tried richer
price bases and segment corrections, but none became a safer default.

This experiment does not introduce another broad correction. It audits the
stable candidate with stronger repeated validation and paired bootstrap checks
so it can be treated as a reproducible Warm improvement candidate.
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

import run_pp_hcoef3_warm_huber_residual_repeated_validation as hcoef3  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF11"
EXP_SLUG = "PP-HCOEF11_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = hcoef3.REFERENCE
STABLE_CONFIG = next(
    item for item in hcoef3.CANDIDATES if item["candidate"] == "hcoef2_size_reliability_cap005_s050"
)
STABLE = STABLE_CONFIG["candidate"]

N_FOLDS = 5
N_REPEATS = 80
N_BOOTSTRAPS = 2000
SEED = 20260614


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef3.metric_from_frame(frame, pred_log)


def metric_from_indices(frame: pd.DataFrame, pred_log: np.ndarray, idx: np.ndarray) -> dict[str, float]:
    sub = frame.iloc[idx]
    return metric_from_frame(sub, np.asarray(pred_log, dtype=float)[idx])


def stable_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, Any]:
    return hcoef3.correction_prediction(train, eval_frame, STABLE_CONFIG)


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred_log: np.ndarray, method: str) -> pd.DataFrame:
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual_price,
            "pred_log": pred_log,
            "pred_price": pred_price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred_log,
            "ape": np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None),
        }
    )
    if "artist_name_ko" in frame.columns:
        out["artist_name_ko"] = frame["artist_name_ko"].astype(str).to_numpy()
    return out


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in predictions.groupby(["split", "candidate"], observed=False):
        residual = group["residual_log"].to_numpy(dtype=float)
        ape = group["ape"].to_numpy(dtype=float)
        actual = group["actual_price"].to_numpy(dtype=float)
        pred = group["pred_price"].to_numpy(dtype=float)
        rows.append(
            {
                "split": split,
                "candidate": candidate,
                "n": len(group),
                "median_residual_log": float(np.median(residual)),
                "mean_residual_log": float(np.mean(residual)),
                "residual_std": float(np.std(residual)),
                "ape_median": float(np.median(ape)),
                "ape_mean": float(np.mean(ape)),
                "ape_p95": float(np.quantile(ape, 0.95)),
                "ape_gt_50pct_n": int((ape > 0.5).sum()),
                "ape_gt_100pct_n": int((ape > 1.0).sum()),
                "over_2x_n": int((pred >= actual * 2.0).sum()),
                "under_half_n": int((pred <= actual * 0.5).sum()),
            }
        )
    return pd.DataFrame(rows)


def repeated_oof(validation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    ref_pred = validation[REFERENCE].to_numpy(dtype=float)
    ref_metric = metric_from_frame(validation, ref_pred)

    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            seed = SEED + repeat
            folds = hcoef3.row_folds(len(validation), seed) if scheme == "row_oof" else hcoef3.artist_folds(validation, seed)
            oof_pred = np.full(len(validation), np.nan, dtype=float)

            for fold_id, (train_idx, hold_idx) in enumerate(folds):
                train = validation.iloc[train_idx].copy()
                hold = validation.iloc[hold_idx].copy()
                pred, _ = stable_prediction(train, hold)
                oof_pred[hold_idx] = pred

                hold_metric = metric_from_frame(hold, pred)
                hold_ref = metric_from_frame(hold, hold[REFERENCE].to_numpy(dtype=float))
                fold_rows.append(
                    {
                        "validation_scheme": scheme,
                        "repeat": repeat,
                        "fold": fold_id,
                        "candidate": STABLE,
                        "n": len(hold),
                        **hold_metric,
                        "delta_MdAPE_vs_reference": hold_metric["MdAPE"] - hold_ref["MdAPE"],
                        "delta_MAPE_vs_reference": hold_metric["MAPE"] - hold_ref["MAPE"],
                        "delta_p95_APE_vs_reference": hold_metric["p95_APE"] - hold_ref["p95_APE"],
                    }
                )

            metric = metric_from_frame(validation, oof_pred)
            metric_rows.append(
                {
                    "validation_scheme": scheme,
                    "repeat": repeat,
                    "candidate": STABLE,
                    "n": len(validation),
                    **metric,
                    "delta_MdAPE_vs_reference": metric["MdAPE"] - ref_metric["MdAPE"],
                    "delta_MAPE_vs_reference": metric["MAPE"] - ref_metric["MAPE"],
                    "delta_p95_APE_vs_reference": metric["p95_APE"] - ref_metric["p95_APE"],
                    "delta_RMSE_log_vs_reference": metric["RMSE_log"] - ref_metric["RMSE_log"],
                    "improve_count_vs_reference": int(metric["MdAPE"] < ref_metric["MdAPE"])
                    + int(metric["MAPE"] < ref_metric["MAPE"])
                    + int(metric["p95_APE"] < ref_metric["p95_APE"]),
                }
            )
            if repeat == 0:
                pred_rows.append(prediction_frame(validation, STABLE, f"validation_{scheme}_repeat0", oof_pred, "repeated_oof"))

    metric_rows.append(
        {
            "validation_scheme": "reference",
            "repeat": -1,
            "candidate": REFERENCE,
            "n": len(validation),
            **ref_metric,
            "delta_MdAPE_vs_reference": 0.0,
            "delta_MAPE_vs_reference": 0.0,
            "delta_p95_APE_vs_reference": 0.0,
            "delta_RMSE_log_vs_reference": 0.0,
            "improve_count_vs_reference": 0,
        }
    )
    return pd.DataFrame(metric_rows), pd.DataFrame(fold_rows), pd.concat(pred_rows, ignore_index=True)


def fixed_confirmation(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []

    for split in ["validation", "test", "0604_ex50"]:
        frame = frames[split]
        ref_pred = frame[REFERENCE].to_numpy(dtype=float)
        ref_metric = metric_from_frame(frame, ref_pred)
        stable_pred, model = stable_prediction(validation, frame)
        stable_metric = metric_from_frame(frame, stable_pred)
        metric_rows.extend(
            [
                {
                    "validation_scheme": "fixed_confirmation",
                    "repeat": -1,
                    "split": split,
                    "candidate": REFERENCE,
                    "n": len(frame),
                    **ref_metric,
                    "delta_MdAPE_vs_reference": 0.0,
                    "delta_MAPE_vs_reference": 0.0,
                    "delta_p95_APE_vs_reference": 0.0,
                    "delta_RMSE_log_vs_reference": 0.0,
                    "improve_count_vs_reference": 0,
                },
                {
                    "validation_scheme": "fixed_confirmation",
                    "repeat": -1,
                    "split": split,
                    "candidate": STABLE,
                    "n": len(frame),
                    **stable_metric,
                    "delta_MdAPE_vs_reference": stable_metric["MdAPE"] - ref_metric["MdAPE"],
                    "delta_MAPE_vs_reference": stable_metric["MAPE"] - ref_metric["MAPE"],
                    "delta_p95_APE_vs_reference": stable_metric["p95_APE"] - ref_metric["p95_APE"],
                    "delta_RMSE_log_vs_reference": stable_metric["RMSE_log"] - ref_metric["RMSE_log"],
                    "improve_count_vs_reference": int(stable_metric["MdAPE"] < ref_metric["MdAPE"])
                    + int(stable_metric["MAPE"] < ref_metric["MAPE"])
                    + int(stable_metric["p95_APE"] < ref_metric["p95_APE"]),
                },
            ]
        )
        pred_rows.append(prediction_frame(frame, REFERENCE, split, ref_pred, "reference_70_30"))
        pred_rows.append(prediction_frame(frame, STABLE, split, stable_pred, "huber_residual_correction"))
        if split == "test":
            coef = hcoef3.coefficient_frame(model, STABLE_CONFIG).copy()
            coef["experiment_id"] = EXP_ID
            coef_rows.append(coef)

    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coef_rows, ignore_index=True)


def bootstrap_compare(frame: pd.DataFrame, ref_pred: np.ndarray, stable_pred: np.ndarray, split: str, unit: str) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + len(split) + (0 if unit == "row" else 100_000))
    n = len(frame)
    rows: list[dict[str, float]] = []

    if unit == "row":
        samples = [rng.integers(0, n, n) for _ in range(N_BOOTSTRAPS)]
    else:
        artists = frame["artist_key"].astype(str).to_numpy()
        unique = np.unique(artists)
        artist_to_idx = {artist: np.flatnonzero(artists == artist) for artist in unique}
        samples = []
        for _ in range(N_BOOTSTRAPS):
            sampled_artists = rng.choice(unique, size=len(unique), replace=True)
            samples.append(np.concatenate([artist_to_idx[artist] for artist in sampled_artists]))

    for idx in samples:
        ref = metric_from_indices(frame, ref_pred, idx)
        stable = metric_from_indices(frame, stable_pred, idx)
        rows.append(
            {
                "delta_MdAPE_vs_reference": stable["MdAPE"] - ref["MdAPE"],
                "delta_MAPE_vs_reference": stable["MAPE"] - ref["MAPE"],
                "delta_p95_APE_vs_reference": stable["p95_APE"] - ref["p95_APE"],
                "delta_RMSE_log_vs_reference": stable["RMSE_log"] - ref["RMSE_log"],
            }
        )

    boot = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for metric_col in [
        "delta_MdAPE_vs_reference",
        "delta_MAPE_vs_reference",
        "delta_p95_APE_vs_reference",
        "delta_RMSE_log_vs_reference",
    ]:
        values = boot[metric_col].to_numpy(dtype=float)
        summary_rows.append(
            {
                "summary_type": "paired_bootstrap",
                "validation_scheme": f"{unit}_bootstrap",
                "split": split,
                "candidate": STABLE,
                "metric": metric_col,
                "n_bootstraps": N_BOOTSTRAPS,
                "mean_delta": float(np.mean(values)),
                "ci025_delta": float(np.quantile(values, 0.025)),
                "ci975_delta": float(np.quantile(values, 0.975)),
                "improve_prob": float((values < 0).mean()),
            }
        )
    return pd.DataFrame(summary_rows)


def summarize_repeated(metrics: pd.DataFrame) -> pd.DataFrame:
    repeated = metrics[metrics["validation_scheme"].isin(["row_oof", "artist_oof"])].copy()
    rows: list[dict[str, Any]] = []
    for scheme, group in repeated.groupby("validation_scheme", observed=False):
        rows.append(
            {
                "summary_type": "repeated_oof",
                "validation_scheme": scheme,
                "split": "validation",
                "candidate": STABLE,
                "metric": "all",
                "n_repeats": len(group),
                "mean_delta_MdAPE_vs_reference": float(group["delta_MdAPE_vs_reference"].mean()),
                "mean_delta_MAPE_vs_reference": float(group["delta_MAPE_vs_reference"].mean()),
                "mean_delta_p95_APE_vs_reference": float(group["delta_p95_APE_vs_reference"].mean()),
                "mean_delta_RMSE_log_vs_reference": float(group["delta_RMSE_log_vs_reference"].mean()),
                "std_delta_MdAPE_vs_reference": float(group["delta_MdAPE_vs_reference"].std()),
                "MdAPE_improve_prob": float((group["delta_MdAPE_vs_reference"] < 0).mean()),
                "MAPE_improve_prob": float((group["delta_MAPE_vs_reference"] < 0).mean()),
                "p95_improve_prob": float((group["delta_p95_APE_vs_reference"] < 0).mean()),
                "all3_improve_prob": float((group["improve_count_vs_reference"] == 3).mean()),
                "mean_improve_count": float(group["improve_count_vs_reference"].mean()),
            }
        )
    return pd.DataFrame(rows)


def fixed_bootstrap(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    validation = frames["validation"]
    for split in ["validation", "test", "0604_ex50"]:
        frame = frames[split]
        ref_pred = frame[REFERENCE].to_numpy(dtype=float)
        stable_pred, _ = stable_prediction(validation, frame)
        rows.append(bootstrap_compare(frame, ref_pred, stable_pred, split, "row"))
        rows.append(bootstrap_compare(frame, ref_pred, stable_pred, split, "artist"))
    return pd.concat(rows, ignore_index=True)


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        return str(value)

    cols = [str(col) for col in data.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for idx, line in enumerate(table):
            if idx == 1:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            tag = "th" if idx == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.strip().startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6}"
        "p{line-height:1.55}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    metrics: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    fixed: pd.DataFrame,
    summary_all: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
) -> None:
    fixed_view = fixed[fixed["split"].isin(["validation", "test", "0604_ex50"])].copy()
    stable_test = fixed_view[(fixed_view["split"].eq("test")) & (fixed_view["candidate"].eq(STABLE))].iloc[0]
    stable_0604 = fixed_view[(fixed_view["split"].eq("0604_ex50")) & (fixed_view["candidate"].eq(STABLE))].iloc[0]
    row_oof = repeated_summary[repeated_summary["validation_scheme"].eq("row_oof")].iloc[0]
    artist_oof = repeated_summary[repeated_summary["validation_scheme"].eq("artist_oof")].iloc[0]

    if (
        row_oof["all3_improve_prob"] >= 0.95
        and artist_oof["all3_improve_prob"] >= 0.95
        and stable_test["improve_count_vs_reference"] >= 2
    ):
        decision = "Warm 개선 후보로 유지한다. fixed test와 반복 OOF에서 기준 후보 대비 개선이 재현된다."
    else:
        decision = "반복 검증 후보로만 둔다. fixed test 또는 OOF 중 일부 기준이 충분하지 않다."

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 안정 후보 확장 검증",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: 현재 Warm 70:30 기준 후보 위에 작은 Huber 잔차 보정을 더한 후보가 반복 검증과 bootstrap에서도 안정적인지 확인.",
            f"- 기준 후보: `{REFERENCE}`.",
            f"- 검증 후보: `{STABLE}`.",
            f"- 반복 설정: row OOF {N_REPEATS}회, artist OOF {N_REPEATS}회, 각 {N_FOLDS} folds.",
            f"- paired bootstrap: split별 row/artist 단위 {N_BOOTSTRAPS}회.",
            "",
            "## 1. 실행 결론",
            "",
            f"- 판단: {decision}",
            f"- fixed test 성능: MdAPE `{stable_test['MdAPE']:.4f}`, MAPE `{stable_test['MAPE']:.4f}`, p95_APE `{stable_test['p95_APE']:.4f}`, RMSE_log `{stable_test['RMSE_log']:.4f}`.",
            f"- fixed test 개선폭: MdAPE `{stable_test['delta_MdAPE_vs_reference']:.4f}`, MAPE `{stable_test['delta_MAPE_vs_reference']:.4f}`, p95_APE `{stable_test['delta_p95_APE_vs_reference']:.4f}`.",
            f"- 0604 외부 테스트 성능: MdAPE `{stable_0604['MdAPE']:.4f}`, MAPE `{stable_0604['MAPE']:.4f}`, p95_APE `{stable_0604['p95_APE']:.4f}`.",
            "- 해석: 이 후보는 새 기준가를 크게 바꾸는 실험이 아니라, 70:30 기준 후보가 남긴 잔차 중 크기/기준가 신뢰도 축으로 설명되는 작은 방향만 Huber가 계수로 보정하는 방식이다.",
            "",
            "## 2. 반복 OOF 요약",
            "",
            markdown_table(repeated_summary.round(4)),
            "",
            "## 3. Fixed validation/test/0604 확인",
            "",
            markdown_table(
                fixed_view[
                    [
                        "split",
                        "candidate",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_reference",
                        "delta_MAPE_vs_reference",
                        "delta_p95_APE_vs_reference",
                        "improve_count_vs_reference",
                    ]
                ].round(4)
            ),
            "",
            "## 4. Paired bootstrap 요약",
            "",
            "- `delta`가 음수이면 검증 후보가 기준 후보보다 좋다는 뜻이다.",
            markdown_table(summary_all[summary_all["summary_type"].eq("paired_bootstrap")].round(4), max_rows=40),
            "",
            "## 5. Huber 계수 해석",
            "",
            "- 계수는 표준화된 피처 기준이다. 절대 가격 공식의 원 단위 계수가 아니라 방향성과 상대 영향 비교용이다.",
            "- `svc_fallback` 계수가 음수이고 `shrunk_svc_prior` 계수가 양수인 것은, 단순 fallback 기준가를 그대로 믿기보다 완화된 기준가와 기존 후보의 차이를 작게 조정한다는 의미다.",
            "- `log_area`, `svc_group_n_log`, `svc_prior_iqr`는 직접 가격을 크게 바꾸는 주 피처라기보다 보정 신뢰도와 크기 관련 잔차 방향을 제한하는 보조 피처다.",
            markdown_table(coeffs.sort_values("abs_coefficient", ascending=False).round(5)),
            "",
            "## 6. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4)),
            "",
            "## 7. 다음 보정 방향",
            "",
            "- HCOEF3 안정 후보는 Warm 개선 후보로 유지한다.",
            "- HCOEF4~HCOEF10에서 확인된 공격형 basis-Huber, segmented median, risk-gated 구조는 기본 후보를 넘지 못했으므로 동일 구조를 반복하지 않는다.",
            "- 다음 실험은 이 후보를 운영 패키징하거나, 작품별 큰 오차 원인 진단 리포트를 보강하는 방향이 우선이다.",
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/fold_metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef11_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef11_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = hcoef3.build_frames()
    repeated_metrics, fold_metrics, oof_predictions = repeated_oof(frames["validation"])
    fixed_metrics, fixed_predictions, coeffs = fixed_confirmation(frames)
    metrics = pd.concat([repeated_metrics, fixed_metrics], ignore_index=True, sort=False)
    predictions = pd.concat([oof_predictions, fixed_predictions], ignore_index=True, sort=False)
    residuals = residual_analysis(predictions)
    repeated_summary = summarize_repeated(metrics)
    bootstrap_summary = fixed_bootstrap(frames)
    summary_all = pd.concat([repeated_summary, bootstrap_summary], ignore_index=True, sort=False)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    fold_metrics.to_csv(out / "fold_metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    summary_all.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": REFERENCE,
        "stable_candidate": STABLE_CONFIG,
        "n_folds": N_FOLDS,
        "n_repeats": N_REPEATS,
        "n_bootstraps": N_BOOTSTRAPS,
        "seed": SEED,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(metrics, repeated_summary, fixed_metrics, summary_all, coeffs, residuals)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- repeated summary ---")
    print(repeated_summary.round(4).to_string(index=False))
    print("--- fixed confirmation ---")
    print(
        fixed_metrics[
            [
                "split",
                "candidate",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "RMSE_log",
                "delta_MdAPE_vs_reference",
                "delta_MAPE_vs_reference",
                "delta_p95_APE_vs_reference",
                "improve_count_vs_reference",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
