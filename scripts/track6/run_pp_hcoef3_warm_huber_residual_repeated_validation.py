#!/usr/bin/env python3
"""Run PP-HCOEF3: repeated validation for Warm Huber residual corrections.

PP-HCOEF2 selected a conservative residual Huber correction. This script checks
whether that signal survives repeated row-level and artist-level validation
splits. Fixed test and 0604 are confirmation only.
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

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF3"
EXP_SLUG = "PP-HCOEF3_warm_huber_residual_repeated_validation"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = "current_70_30"
N_FOLDS = 5
N_REPEATS = 20
SEED = 20260607

CANDIDATES = [
    {
        "candidate": "hcoef2_size_reliability_cap003_s075",
        "source_candidate": "residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75",
        "feature_key": "resid_basis_size_reliability",
        "alpha": 0.0001,
        "cap": 0.03,
        "strength": 0.75,
        "purpose": "PP-HCOEF2 보수 선택 1순위",
    },
    {
        "candidate": "hcoef2_size_reliability_cap005_s050",
        "source_candidate": "residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50",
        "feature_key": "resid_basis_size_reliability",
        "alpha": 0.01,
        "cap": 0.05,
        "strength": 0.50,
        "purpose": "작은 폭 MAPE/p95 안정화 대안",
    },
    {
        "candidate": "hcoef2_gap_cap003_s075",
        "source_candidate": "residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75",
        "feature_key": "resid_basis_gap",
        "alpha": 0.0001,
        "cap": 0.03,
        "strength": 0.75,
        "purpose": "기준가 간 gap만 쓰는 단순 대안",
    },
    {
        "candidate": "hcoef1_size_reliability_cap012_s025",
        "source_candidate": "residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25",
        "feature_key": "resid_basis_size_reliability",
        "alpha": 0.0001,
        "cap": 0.12,
        "strength": 0.25,
        "purpose": "PP-HCOEF1 test 상위권 aggressive 대조군",
    },
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def build_frames() -> dict[str, pd.DataFrame]:
    shrunk_pred, raw_prior, shrunk_prior, _ = hcoef1.train_shrunk_huber_refit()
    frames = hcoef1.build_validation_test_frames(shrunk_pred, raw_prior, shrunk_prior)
    frames["0604_ex50"] = hcoef1.build_0604_frame(shrunk_pred, raw_prior, shrunk_prior)
    return frames


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef1.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def correction_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame, config: dict[str, Any]) -> tuple[np.ndarray, Any]:
    features = hcoef1.RESIDUAL_FEATURE_SETS[config["feature_key"]]
    target = train["actual_log"].to_numpy(dtype=float) - train[REFERENCE].to_numpy(dtype=float)
    model = hcoef1.linear_pipeline("huber", float(config["alpha"]))
    model.fit(train[features], target)
    raw = np.asarray(model.predict(eval_frame[features]), dtype=float)
    correction = np.clip(raw, -float(config["cap"]), float(config["cap"])) * float(config["strength"])
    pred = eval_frame[REFERENCE].to_numpy(dtype=float) + correction
    return pred, model


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    order = rng.permutation(np.arange(n))
    folds = np.array_split(order, N_FOLDS)
    out = []
    all_idx = np.arange(n)
    for hold in folds:
        train = np.setdiff1d(all_idx, hold, assume_unique=False)
        out.append((train, hold))
    return out


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    artists = frame["artist_key"].astype(str).to_numpy()
    unique = rng.permutation(np.unique(artists))
    fold_of = {artist: idx % N_FOLDS for idx, artist in enumerate(unique)}
    out = []
    all_idx = np.arange(len(frame))
    for fold_id in range(N_FOLDS):
        hold = np.flatnonzero([fold_of[artist] == fold_id for artist in artists])
        train = np.setdiff1d(all_idx, hold, assume_unique=False)
        out.append((train, hold))
    return out


def repeated_oof(validation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    ref_pred = validation[REFERENCE].to_numpy(dtype=float)
    ref_metric = metric_from_frame(validation, ref_pred)

    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            seed = SEED + repeat
            folds = row_folds(len(validation), seed) if scheme == "row_oof" else artist_folds(validation, seed)
            for config in CANDIDATES:
                oof_pred = np.full(len(validation), np.nan, dtype=float)
                fold_metrics: list[dict[str, Any]] = []
                for fold_id, (train_idx, hold_idx) in enumerate(folds):
                    train = validation.iloc[train_idx].copy()
                    hold = validation.iloc[hold_idx].copy()
                    pred, _ = correction_prediction(train, hold, config)
                    oof_pred[hold_idx] = pred
                    hold_metric = metric_from_frame(hold, pred)
                    hold_ref = metric_from_frame(hold, hold[REFERENCE].to_numpy(dtype=float))
                    fold_metrics.append(
                        {
                            "validation_scheme": scheme,
                            "repeat": repeat,
                            "fold": fold_id,
                            "candidate": config["candidate"],
                            "n": len(hold),
                            "MdAPE": hold_metric["MdAPE"],
                            "MAPE": hold_metric["MAPE"],
                            "p95_APE": hold_metric["p95_APE"],
                            "RMSE_log": hold_metric["RMSE_log"],
                            "delta_MdAPE": hold_metric["MdAPE"] - hold_ref["MdAPE"],
                            "delta_MAPE": hold_metric["MAPE"] - hold_ref["MAPE"],
                            "delta_p95_APE": hold_metric["p95_APE"] - hold_ref["p95_APE"],
                        }
                    )
                full_metric = metric_from_frame(validation, oof_pred)
                metric_rows.append(
                    {
                        "validation_scheme": scheme,
                        "repeat": repeat,
                        "candidate": config["candidate"],
                        "n": len(validation),
                        **full_metric,
                        "delta_MdAPE": full_metric["MdAPE"] - ref_metric["MdAPE"],
                        "delta_MAPE": full_metric["MAPE"] - ref_metric["MAPE"],
                        "delta_p95_APE": full_metric["p95_APE"] - ref_metric["p95_APE"],
                        "improve_count": int(full_metric["MdAPE"] < ref_metric["MdAPE"])
                        + int(full_metric["MAPE"] < ref_metric["MAPE"])
                        + int(full_metric["p95_APE"] < ref_metric["p95_APE"]),
                    }
                )
                if repeat == 0:
                    pred_rows.append(prediction_frame(validation, config["candidate"], f"validation_{scheme}_repeat0", oof_pred))

    # Add reference row once for clarity.
    metric_rows.append(
        {
            "validation_scheme": "reference",
            "repeat": -1,
            "candidate": REFERENCE,
            "n": len(validation),
            **ref_metric,
            "delta_MdAPE": 0.0,
            "delta_MAPE": 0.0,
            "delta_p95_APE": 0.0,
            "improve_count": 0,
        }
    )
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True)


def fixed_confirmation(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    residual_rows: list[dict[str, Any]] = []

    for split in ["validation", "test", "0604_ex50"]:
        frame = frames[split]
        ref_metric = metric_from_frame(frame, frame[REFERENCE].to_numpy(dtype=float))
        metric_rows.append(
            {
                "validation_scheme": "fixed_confirmation",
                "repeat": -1,
                "split": split,
                "candidate": REFERENCE,
                "n": len(frame),
                **ref_metric,
                "delta_MdAPE": 0.0,
                "delta_MAPE": 0.0,
                "delta_p95_APE": 0.0,
                "improve_count": 0,
            }
        )
        pred_rows.append(prediction_frame(frame, REFERENCE, split, frame[REFERENCE].to_numpy(dtype=float)))

    for config in CANDIDATES:
        for split in ["validation", "test", "0604_ex50"]:
            pred, model = correction_prediction(validation, frames[split], config)
            ref_metric = metric_from_frame(frames[split], frames[split][REFERENCE].to_numpy(dtype=float))
            metric = metric_from_frame(frames[split], pred)
            metric_rows.append(
                {
                    "validation_scheme": "fixed_confirmation",
                    "repeat": -1,
                    "split": split,
                    "candidate": config["candidate"],
                    "n": len(frames[split]),
                    **metric,
                    "delta_MdAPE": metric["MdAPE"] - ref_metric["MdAPE"],
                    "delta_MAPE": metric["MAPE"] - ref_metric["MAPE"],
                    "delta_p95_APE": metric["p95_APE"] - ref_metric["p95_APE"],
                    "improve_count": int(metric["MdAPE"] < ref_metric["MdAPE"])
                    + int(metric["MAPE"] < ref_metric["MAPE"])
                    + int(metric["p95_APE"] < ref_metric["p95_APE"]),
                }
            )
            pred_rows.append(prediction_frame(frames[split], config["candidate"], split, pred))
            residual_rows.append(residual_summary(frames[split], config["candidate"], split, pred))
            if split == "test":
                coef_rows.append(coefficient_frame(model, config))

    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coef_rows, ignore_index=True), pd.DataFrame(residual_rows)


def coefficient_frame(model: Any, config: dict[str, Any]) -> pd.DataFrame:
    features = hcoef1.RESIDUAL_FEATURE_SETS[config["feature_key"]]
    reg = model.named_steps["model"]
    coefs = getattr(reg, "coef_", np.full(len(features), np.nan))
    rows = []
    for idx, feature in enumerate(features):
        rows.append(
            {
                "candidate": config["candidate"],
                "source_candidate": config["source_candidate"],
                "feature": feature,
                "coefficient_on_scaled_feature": float(coefs[idx]),
                "abs_coefficient": float(abs(coefs[idx])),
                "alpha": config["alpha"],
                "cap": config["cap"],
                "strength": config["strength"],
            }
        )
    return pd.DataFrame(rows).sort_values("abs_coefficient", ascending=False)


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred_log: np.ndarray) -> pd.DataFrame:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "artist_name_ko": frame["artist_name_ko"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual_price,
            "pred_log": pred_log,
            "pred_price": pred_price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred_log,
            "ape": ape,
        }
    )


def residual_summary(frame: pd.DataFrame, candidate: str, split: str, pred_log: np.ndarray) -> dict[str, Any]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    residual = frame["actual_log"].to_numpy(dtype=float) - pred_log
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "split": split,
        "candidate": candidate,
        "median_residual_log": float(np.median(residual)),
        "mean_residual_log": float(np.mean(residual)),
        "residual_std": float(np.std(residual)),
        "over_2x_n": int((pred_price >= actual_price * 2.0).sum()),
        "under_half_n": int((pred_price <= actual_price * 0.5).sum()),
        "ape_gt_100pct_n": int((ape > 1.0).sum()),
    }


def repeated_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    repeated = metrics[metrics["validation_scheme"].isin(["row_oof", "artist_oof"])].copy()
    rows = []
    for (scheme, candidate), group in repeated.groupby(["validation_scheme", "candidate"], observed=False):
        rows.append(
            {
                "validation_scheme": scheme,
                "candidate": candidate,
                "mean_delta_MdAPE": float(group["delta_MdAPE"].mean()),
                "mean_delta_MAPE": float(group["delta_MAPE"].mean()),
                "mean_delta_p95_APE": float(group["delta_p95_APE"].mean()),
                "std_delta_MdAPE": float(group["delta_MdAPE"].std()),
                "MdAPE_improve_prob": float((group["delta_MdAPE"] < 0).mean()),
                "MAPE_improve_prob": float((group["delta_MAPE"] < 0).mean()),
                "p95_improve_prob": float((group["delta_p95_APE"] < 0).mean()),
                "all3_improve_prob": float((group["improve_count"] == 3).mean()),
                "mean_improve_count": float(group["improve_count"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["validation_scheme", "mean_delta_MdAPE"])


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
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(metrics: pd.DataFrame, summary: pd.DataFrame, fixed: pd.DataFrame, coeffs: pd.DataFrame, residuals: pd.DataFrame) -> None:
    fixed_key = fixed[fixed["split"].isin(["validation", "test", "0604_ex50"])].copy()
    best_summary = summary.sort_values(["all3_improve_prob", "mean_delta_MdAPE"], ascending=[False, True]).iloc[0]
    best_candidate = str(best_summary["candidate"])
    test_best = fixed_key[(fixed_key["candidate"].eq(best_candidate)) & (fixed_key["split"].eq("test"))].iloc[0]
    if (
        best_summary["all3_improve_prob"] >= 0.7
        and best_summary["MdAPE_improve_prob"] >= 0.7
        and best_summary["p95_improve_prob"] >= 0.7
    ):
        decision = f"반복 검증 통과 후보: `{best_candidate}`."
    else:
        decision = (
            f"반복 검증 보류: `{best_candidate}`가 fixed test는 개선했지만 반복 OOF 개선확률이 충분히 강하지 않다. "
            "기본 후보는 유지하고 후속 split 재검증 후보로만 둔다."
        )

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 잔차 보정 반복 검증",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: PP-HCOEF2의 보수적 잔차 보정 후보가 row/artist 반복 OOF에서도 유지되는지 확인.",
            f"- 반복 설정: row OOF {N_REPEATS}회, artist OOF {N_REPEATS}회, 각 {N_FOLDS} folds.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}",
            f"- 후보 `{best_candidate}` fixed test MdAPE/MAPE/p95: `{test_best['MdAPE']:.4f}` / `{test_best['MAPE']:.4f}` / `{test_best['p95_APE']:.4f}`.",
            "- fixed test 개선만으로는 채택하지 않고, 반복 OOF 개선 확률을 함께 본다.",
            "",
            "## 2. 반복 OOF 요약",
            "",
            markdown_table(summary.round(4)),
            "",
            "## 3. Fixed validation/test/0604 확인",
            "",
            markdown_table(
                fixed_key[
                    [
                        "split",
                        "candidate",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE",
                        "delta_MAPE",
                        "delta_p95_APE",
                        "improve_count",
                    ]
                ].round(4),
                max_rows=24,
            ),
            "",
            "## 4. 주요 계수",
            "",
            "- 계수는 표준화된 피처 기준이다. 방향성과 상대 영향 비교용이다.",
            markdown_table(coeffs.sort_values("abs_coefficient", ascending=False).head(40).round(5)),
            "",
            "## 5. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=30),
            "",
            "## 6. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef3_warm_huber_residual_repeated_validation_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef3_warm_huber_residual_repeated_validation_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = build_frames()
    repeated_metrics, oof_predictions = repeated_oof(frames["validation"])
    fixed_metrics, fixed_predictions, coeffs, residuals = fixed_confirmation(frames)
    summary = repeated_summary(repeated_metrics)

    metrics = pd.concat([repeated_metrics, fixed_metrics], ignore_index=True, sort=False)
    predictions = pd.concat([oof_predictions, fixed_predictions], ignore_index=True, sort=False)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": REFERENCE,
        "n_folds": N_FOLDS,
        "n_repeats": N_REPEATS,
        "candidates": CANDIDATES,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(metrics, summary, fixed_metrics, coeffs, residuals)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- repeated summary ---")
    print(summary.round(4).to_string(index=False))
    print("--- fixed confirmation ---")
    print(
        fixed_metrics[fixed_metrics["split"].isin(["validation", "test", "0604_ex50"])][
            ["split", "candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "improve_count"]
        ]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
