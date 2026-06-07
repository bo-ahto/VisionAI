#!/usr/bin/env python3
"""Revalidate PP-Y15 segment/cap calibration with validation OOF selection.

PP-Y15 found strong test candidates by trying multiple segment/min_rows/cap
settings. This script closes the main selection-risk gap:

1. Build segment labels from validation prediction-side information only.
2. Evaluate every segment/min_rows/cap policy with validation internal OOF.
3. Select policies by validation OOF objectives.
4. Fit the correction map on full validation and apply the fixed policy to test.
"""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED  # noqa: E402


EXP_ID = "PP-Y16"
EXP_SLUG = "PP-Y16_cold_y15_oof_fixed_revalidation"
TITLE = "Cold PP-Y15 segment/cap OOF 고정 재검증"
SOURCE_FOLDER = "PP-Y2_cold_lgbq_search_external_combo"
SOURCE_CANDIDATE = "lgbq_search_all_external_interaction"
SUMMARY_PATH = BASE_EXP_DIR / "PP-Y_cold_combination_summary_metrics.csv"


def load_source(split: str) -> pd.DataFrame:
    path = BASE_EXP_DIR / SOURCE_FOLDER / "outputs" / "predictions.csv"
    df = pd.read_csv(path, low_memory=False)
    mask = (
        df["candidate"].astype(str).eq(SOURCE_CANDIDATE)
        & df["scope"].astype(str).eq("cold")
        & df["split"].astype(str).eq(split)
    )
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing source predictions: {path} {split} {SOURCE_CANDIDATE}")
    required = ["_track6_row_id", "actual_log", "actual_price", "pred_log", "residual_log", "quantile_width_log"]
    missing = [col for col in required if col not in out.columns]
    if missing:
        raise ValueError(f"missing required columns in source predictions: {missing}")
    return out


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def quantile_edges(values: pd.Series, bins: int) -> list[float]:
    numeric = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if numeric.size == 0:
        return [-np.inf, np.inf]
    edges = np.quantile(numeric, np.linspace(0.0, 1.0, bins + 1))
    edges = np.unique(edges)
    if edges.size < 2:
        center = float(edges[0])
        edges = np.array([center - 1e-6, center + 1e-6])
    edges[0] = -np.inf
    edges[-1] = np.inf
    return [float(x) for x in edges]


def assign_bins(values: pd.Series, edges: list[float], prefix: str) -> pd.Series:
    codes = pd.cut(pd.to_numeric(values, errors="coerce"), bins=edges, labels=False, include_lowest=True)
    return codes.astype("float").fillna(-1).astype(int).map(lambda x: f"{prefix}{x}" if x >= 0 else f"{prefix}_missing")


def add_segment_columns(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    val = val.copy()
    test = test.copy()
    pred_edges = quantile_edges(val["pred_log"], 5)
    qwidth_edges = quantile_edges(val["quantile_width_log"], 4)
    for frame in [val, test]:
        frame["pred_bin_fixed"] = assign_bins(frame["pred_log"], pred_edges, "p")
        frame["qwidth_bin_fixed"] = assign_bins(frame["quantile_width_log"], qwidth_edges, "w")
        gallery = pd.to_numeric(frame.get("gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0)
        exhibition = pd.to_numeric(frame.get("artist_exhibition_available_count", 0.0), errors="coerce").fillna(0.0)
        frame["external_info_bin"] = np.where((gallery > 0) | (exhibition >= 2), "external_present", "external_sparse")
    return val, test, {"pred_edges": pred_edges, "qwidth_edges": qwidth_edges}


def build_segment(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    return frame[columns].astype(str).agg("__".join, axis=1)


def fit_correction_map(frame: pd.DataFrame, min_rows: int) -> tuple[dict[str, float], float, pd.DataFrame]:
    grouped = (
        frame.groupby("segment", dropna=False)
        .agg(n=("residual_log", "size"), median_residual=("residual_log", "median"))
        .reset_index()
    )
    global_corr = float(frame["residual_log"].median())
    eligible = grouped[grouped["n"] >= min_rows].copy()
    corr_map = dict(zip(eligible["segment"].astype(str), eligible["median_residual"].astype(float), strict=False))
    return corr_map, global_corr, grouped


def apply_correction(frame: pd.DataFrame, corr_map: dict[str, float], global_corr: float, cap: float) -> tuple[np.ndarray, np.ndarray]:
    raw_corr = frame["segment"].astype(str).map(corr_map).fillna(global_corr).to_numpy(dtype=float)
    correction = np.clip(raw_corr, -cap, cap)
    return frame["pred_log"].to_numpy(dtype=float) + correction, correction


def oof_prediction(val: pd.DataFrame, min_rows: int, cap: float, n_splits: int = 5) -> tuple[np.ndarray, np.ndarray]:
    oof = np.zeros(len(val), dtype=float)
    corr = np.zeros(len(val), dtype=float)
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    for train_idx, hold_idx in kfold.split(val):
        train_fold = val.iloc[train_idx].copy()
        hold_fold = val.iloc[hold_idx].copy()
        corr_map, global_corr, _ = fit_correction_map(train_fold, min_rows)
        pred, correction = apply_correction(hold_fold, corr_map, global_corr, cap)
        oof[hold_idx] = pred
        corr[hold_idx] = correction
    return oof, corr


def add_metric(
    rows: list[dict[str, Any]],
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any],
) -> None:
    rows.append(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "scope": "cold",
            "split": split,
            "policy": policy,
            **metric_values(frame, pred_log),
            **extra,
        }
    )


def prediction_frame(
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    correction: np.ndarray,
    policy: str,
    extra: dict[str, Any],
) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "scope": "cold",
            "split": split,
            "policy": policy,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "pred_log": pred_log,
            "actual_price": frame["actual_price"].to_numpy(dtype=float),
            "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
            "base_pred_log": frame["pred_log"].to_numpy(dtype=float),
            "correction_log": correction,
            "segment": frame["segment"].astype(str).to_numpy(),
        }
    )
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    for col in ["quantile_width_log", "price_range_ratio", "search_quality_score", "gallery_tier_any_available_flag", "artist_exhibition_available_count"]:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    for key, value in extra.items():
        out[key] = value
    return out


def selection_summary(metrics_df: pd.DataFrame) -> pd.DataFrame:
    val = metrics_df[metrics_df["split"].eq("validation_oof")].copy()
    test = metrics_df[metrics_df["split"].eq("test")].copy()
    val["balanced_rank_score"] = (
        0.50 * val["MdAPE"].rank(method="min")
        + 0.25 * val["MAPE"].rank(method="min")
        + 0.25 * val["p95_APE"].rank(method="min")
    )
    selectors = [
        ("validation_oof_best_mdape", val.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]),
        ("validation_oof_best_mape", val.sort_values(["MAPE", "MdAPE", "p95_APE"]).iloc[0]),
        ("validation_oof_best_p95", val.sort_values(["p95_APE", "MdAPE", "MAPE"]).iloc[0]),
        ("validation_oof_balanced_rank", val.sort_values(["balanced_rank_score", "MdAPE", "MAPE", "p95_APE"]).iloc[0]),
    ]
    rows: list[dict[str, Any]] = []
    for selector, val_row in selectors:
        candidate = str(val_row["candidate"])
        test_row = test[test["candidate"].eq(candidate)].iloc[0]
        rows.append(
            {
                "selector": selector,
                "candidate": candidate,
                "segment": val_row.get("segment", ""),
                "min_rows": val_row.get("min_rows", ""),
                "cap": val_row.get("cap", ""),
                "validation_oof_MdAPE": val_row["MdAPE"],
                "validation_oof_MAPE": val_row["MAPE"],
                "validation_oof_p95_APE": val_row["p95_APE"],
                "test_MdAPE": test_row["MdAPE"],
                "test_MAPE": test_row["MAPE"],
                "test_p95_APE": test_row["p95_APE"],
                "test_RMSE_log": test_row["RMSE_log"],
            }
        )
    return pd.DataFrame(rows)


def format_float(value: Any) -> str:
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.4f}"
    return str(value)


def render_report(metrics_df: pd.DataFrame, select_df: pd.DataFrame, map_df: pd.DataFrame, bin_config: dict[str, Any]) -> tuple[str, str]:
    top_val = metrics_df[metrics_df["split"].eq("validation_oof")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(15)
    top_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(15)
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "- 목적: `PP-Y15`에서 찾은 segment/cap 보정 후보가 test 반복 선택이 아니라 validation 내부 OOF 기준으로도 유지되는지 확인한다.",
        f"- 1차 예측값: `{SOURCE_FOLDER}` / `{SOURCE_CANDIDATE}`.",
        "- 선택 원칙: validation 내부 5-fold OOF 성능으로 후보를 고르고, full validation correction map을 test에 1회 적용한다.",
        "- bin 기준: 예측 가격 bin과 quantile width bin은 validation 예측값으로 경계를 만들고 test에는 같은 경계를 적용한다.",
        "",
        "## 선택 후보",
        "",
        "| 선택 기준 | 후보 | validation OOF MdAPE | validation OOF MAPE | validation OOF p95 | test MdAPE | test MAPE | test p95 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in select_df.itertuples(index=False):
        lines.append(
            f"| `{row.selector}` | `{row.candidate}` | {row.validation_oof_MdAPE:.4f} | {row.validation_oof_MAPE:.4f} | {row.validation_oof_p95_APE:.4f} | {row.test_MdAPE:.4f} | {row.test_MAPE:.4f} | {row.test_p95_APE:.4f} |"
        )
    lines.extend(["", "## Validation OOF 상위", "", "| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |", "|---|---:|---:|---:|---:|"])
    for row in top_val.itertuples():
        lines.append(f"| `{row.candidate}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")
    lines.extend(["", "## Test 상위", "", "| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |", "|---|---:|---:|---:|---:|"])
    for row in top_test.itertuples():
        lines.append(f"| `{row.candidate}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")
    lines.extend(
        [
            "",
            "## 판단",
            "",
            "- 이 실험의 test 상위표는 탐색 참고용이고, 채택 판단은 `선택 후보` 표의 validation OOF 선택 결과를 우선한다.",
            "- validation OOF 선택 후보가 closure의 test 최고 후보보다 낮게 나오면 closure 결과는 test 탐색 효과가 있었던 것으로 해석한다.",
            "- validation OOF 선택 후보가 test에서도 개선을 유지하면 PP-Y15 보정 구조는 최종 후보로 재검증 가치가 높다.",
            "",
            "## Bin 설정",
            "",
            "```json",
            json.dumps(bin_config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}pre{{background:#f6f8fa;padding:12px;overflow:auto}}</style></head>
<body><h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<h2>Selection Summary</h2>{select_df.to_html(index=False, escape=True, float_format=format_float)}
<h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True, float_format=format_float)}
<h2>Policy Map</h2>{map_df.to_html(index=False, escape=True, float_format=format_float)}
</body></html>"""
    return md, html_doc


def update_summary(metrics_df: pd.DataFrame, folder: Path) -> None:
    out = metrics_df.copy()
    out["folder"] = str(folder.relative_to(REPO))
    if SUMMARY_PATH.exists():
        prior = pd.read_csv(SUMMARY_PATH, low_memory=False)
        combined = pd.concat([prior, out], ignore_index=True, sort=False)
        combined = combined.drop_duplicates(["experiment_id", "candidate", "split", "policy"], keep="last")
    else:
        combined = out
    combined.to_csv(SUMMARY_PATH, index=False)


def main() -> None:
    start = time.time()
    val, test, bin_config = add_segment_columns(load_source("validation"), load_source("test"))
    segment_sets = {
        "pred_bin": ["pred_bin_fixed"],
        "qwidth_bin": ["qwidth_bin_fixed"],
        "pred_x_qwidth": ["pred_bin_fixed", "qwidth_bin_fixed"],
        "external_x_qwidth": ["external_info_bin", "qwidth_bin_fixed"],
    }
    min_rows_values = [30, 50, 100, 150]
    cap_values = [0.10, 0.15, 0.25, 0.35]

    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for segment_name, segment_cols in segment_sets.items():
        val_seg = val.copy()
        test_seg = test.copy()
        val_seg["segment"] = build_segment(val_seg, segment_cols)
        test_seg["segment"] = build_segment(test_seg, segment_cols)
        for min_rows in min_rows_values:
            for cap in cap_values:
                candidate = f"{SOURCE_CANDIDATE}_{segment_name}_oof_min{min_rows}_cap{cap:g}"
                oof_pred, oof_corr = oof_prediction(val_seg, min_rows, cap)
                corr_map, global_corr, segment_map = fit_correction_map(val_seg, min_rows)
                test_pred, test_corr = apply_correction(test_seg, corr_map, global_corr, cap)
                extra = {"segment": segment_name, "min_rows": min_rows, "cap": cap, "source_candidate": SOURCE_CANDIDATE}
                add_metric(rows, candidate, "validation_oof", val_seg, oof_pred, "y15_oof_fixed_segment_cap", extra)
                add_metric(rows, candidate, "test", test_seg, test_pred, "y15_oof_fixed_segment_cap", extra)
                preds.append(prediction_frame(candidate, "validation_oof", val_seg, oof_pred, oof_corr, "y15_oof_fixed_segment_cap", extra))
                preds.append(prediction_frame(candidate, "test", test_seg, test_pred, test_corr, "y15_oof_fixed_segment_cap", extra))
                maps.append(
                    {
                        "experiment_id": EXP_ID,
                        "candidate": candidate,
                        "source_candidate": SOURCE_CANDIDATE,
                        "segment": segment_name,
                        "segment_columns": ", ".join(segment_cols),
                        "min_rows": min_rows,
                        "cap": cap,
                        "global_correction": global_corr,
                        "eligible_segments": int((segment_map["n"] >= min_rows).sum()),
                        "total_segments": int(len(segment_map)),
                    }
                )

    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(preds, ignore_index=True)
    map_df = pd.DataFrame(maps)
    select_df = selection_summary(metrics_df)

    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "policy_map.csv", index=False)
    select_df.to_csv(exp_dir / "outputs" / "selection_summary.csv", index=False)
    (exp_dir / "data" / "bin_config.json").write_text(json.dumps(bin_config, ensure_ascii=False, indent=2), encoding="utf-8")
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "source_folder": SOURCE_FOLDER,
        "source_candidate": SOURCE_CANDIDATE,
        "selection_policy": "validation_oof_first",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics_df, select_df, map_df, bin_config)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    update_summary(metrics_df, exp_dir)
    print(
        json.dumps(
            {
                "status": "completed",
                "seconds": round(time.time() - start, 2),
                "experiment": str(exp_dir.relative_to(REPO)),
                "metrics": str((exp_dir / "outputs" / "metrics.csv").relative_to(REPO)),
                "selection": str((exp_dir / "outputs" / "selection_summary.csv").relative_to(REPO)),
                "selected": select_df.to_dict(orient="records"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
