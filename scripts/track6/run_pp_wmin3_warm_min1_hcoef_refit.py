#!/usr/bin/env python3
"""Run PP-WMIN3 Warm min1 basis + HCOEF stable refit validation.

PP-WMIN2 showed that relaxing the Warm artist comparable ladder to min_n=1
improves both svc_numeric and the 70:30 basis. PP-WMIN3 checks whether the
existing HCOEF stable correction remains useful after that basis change.

Selection is validation OOF only. Fixed test is written as confirmation.
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


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_hcoef3_warm_huber_residual_repeated_validation as hcoef3  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WMIN3"
EXP_SLUG = "PP-WMIN3_warm_min1_hcoef_refit"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm min1 70:30 기준가와 HCOEF 안정 보정 재검증"
SEED = 20260612
N_FOLDS = 5
N_REPEATS = 40
STABLE_CONFIG = next(
    item for item in hcoef3.CANDIDATES if item["candidate"] == "hcoef2_size_reliability_cap005_s050"
)

WMIN2_PREDICTIONS = EXP_ROOT / "PP-WMIN2_warm_artist_min1_svc_numeric" / "outputs" / "predictions.csv"
WMIN2_FEATURES = EXP_ROOT / "PP-WMIN2_warm_artist_min1_svc_numeric" / "outputs" / "comparable_features_min1.csv"
HCOEF18_PREDICTIONS = (
    EXP_ROOT / "PP-HCOEF18_warm_huber_price_basis_coefficient_refinement" / "outputs" / "candidate_predictions.csv"
)

OLD_CURRENT = "old_current_70_30_min5"
OLD_STABLE = "old_hcoef_stable_min5"
NEW_SVC = "wmin2_svc_numeric_seed_mean_min1"
NEW_BASIS = "wmin3_min1_70_30_basis"
TRANSPLANT = "wmin3_min1_hcoef_delta_transplant"
REFIT_PARTIAL = "wmin3_min1_hcoef_refit_partial"
REFIT_SVC_PROXY = "wmin3_min1_hcoef_refit_svc_proxy"


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def safe_exp(values: np.ndarray | pd.Series) -> np.ndarray:
    return np.clip(np.exp(np.asarray(values, dtype=float)), 1_000.0, None)


def metric(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    return hcoef1.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    order = rng.permutation(np.arange(n))
    folds = np.array_split(order, N_FOLDS)
    all_idx = np.arange(n)
    return [(np.setdiff1d(all_idx, hold, assume_unique=False), hold) for hold in folds]


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    artists = frame["artist_key"].astype(str).to_numpy()
    unique = rng.permutation(np.unique(artists))
    fold_of = {artist: idx % N_FOLDS for idx, artist in enumerate(unique)}
    all_idx = np.arange(len(frame))
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for fold_id in range(N_FOLDS):
        hold = np.flatnonzero([fold_of[artist] == fold_id for artist in artists])
        train = np.setdiff1d(all_idx, hold, assume_unique=False)
        out.append((train, hold))
    return out


def load_old_stable() -> pd.DataFrame:
    old = pd.read_csv(HCOEF18_PREDICTIONS, low_memory=False)
    old = old[
        old["candidate"].eq("hcoef_stable")
        & old["split"].isin(["validation", "test"])
    ].copy()
    keep = ["split", "_track6_row_id", "hcoef_stable", "current_70_30"]
    return old[keep].rename(
        columns={
            "hcoef_stable": OLD_STABLE,
            "current_70_30": OLD_CURRENT,
        }
    ).drop_duplicates(["split", "_track6_row_id"])


def load_wmin2_values() -> pd.DataFrame:
    pred = pd.read_csv(WMIN2_PREDICTIONS, low_memory=False)
    pred = pred[
        pred["split"].isin(["validation", "test"])
        & pred["candidate"].isin([NEW_SVC, "wmin2_70_30_min1_svc_ppv8"])
    ].copy()
    wide = pred.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={"wmin2_70_30_min1_svc_ppv8": NEW_BASIS})

    feat = pd.read_csv(WMIN2_FEATURES, low_memory=False)
    feat = feat[feat["split"].isin(["validation", "test"])].copy()
    feat_keep = [
        "split",
        "_track6_row_id",
        "svc_group_log_price_iqr",
        "svc_group_n",
        "svc_group_level",
        "svc_coverage_tier",
    ]
    feat = feat[[col for col in feat_keep if col in feat.columns]].drop_duplicates(["split", "_track6_row_id"])
    return wide.merge(feat, on=["split", "_track6_row_id"], how="left")


def build_old_frames() -> dict[str, pd.DataFrame]:
    shrunk_pred, raw_prior, shrunk_prior, _model = hcoef1.train_shrunk_huber_refit()
    frames = hcoef1.build_validation_test_frames(shrunk_pred, raw_prior, shrunk_prior)
    return {split: frame.copy() for split, frame in frames.items() if split in {"validation", "test"}}


def make_variant_frames(mode: str) -> dict[str, pd.DataFrame]:
    old_frames = build_old_frames()
    old_stable = load_old_stable()
    wmin2 = load_wmin2_values()
    frames: dict[str, pd.DataFrame] = {}
    for split, frame in old_frames.items():
        merged = (
            frame.merge(old_stable, on=["split", "_track6_row_id"], how="left")
            .merge(wmin2, on=["split", "_track6_row_id"], how="left", suffixes=("", "_min1"))
        )
        if merged[[OLD_STABLE, OLD_CURRENT, NEW_SVC, NEW_BASIS]].isna().any().any():
            missing = merged[[OLD_STABLE, OLD_CURRENT, NEW_SVC, NEW_BASIS]].isna().sum().to_dict()
            raise ValueError(f"Missing WMIN3 merge values for {split}: {missing}")

        merged["old_hcoef_delta_log"] = merged[OLD_STABLE] - merged[OLD_CURRENT]
        merged[TRANSPLANT] = merged[NEW_BASIS] + merged["old_hcoef_delta_log"]

        merged["current_70_30"] = merged[NEW_BASIS]
        merged["svc_fallback"] = merged[NEW_SVC]
        if "svc_group_n_min1" in merged.columns:
            merged["svc_group_n"] = pd.to_numeric(merged["svc_group_n_min1"], errors="coerce")
        if "svc_group_level_min1" in merged.columns:
            merged["svc_group_level"] = merged["svc_group_level_min1"].astype(str)
        if "svc_coverage_tier_min1" in merged.columns:
            merged["svc_coverage_tier"] = merged["svc_coverage_tier_min1"].astype(str)
        if "svc_group_log_price_iqr_min1" in merged.columns:
            merged["svc_group_log_price_iqr"] = pd.to_numeric(merged["svc_group_log_price_iqr_min1"], errors="coerce")

        if mode == "svc_proxy":
            merged["raw_svc_prior"] = merged[NEW_SVC]
            merged["shrunk_svc_prior"] = merged[NEW_SVC]
        elif mode == "partial":
            # Keep old raw/shrunk SVC priors. This isolates the 70:30 basis swap.
            pass
        else:
            raise ValueError(f"Unknown variant mode: {mode}")

        refreshed = hcoef1.add_derived_features(merged, split)
        for col in [OLD_STABLE, OLD_CURRENT, NEW_SVC, NEW_BASIS, TRANSPLANT, "old_hcoef_delta_log"]:
            refreshed[col] = pd.to_numeric(merged[col], errors="coerce").to_numpy()
        frames[split] = refreshed.reset_index(drop=True)
    return frames


def fit_refit_candidate(train: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, Any]:
    features = hcoef1.RESIDUAL_FEATURE_SETS[STABLE_CONFIG["feature_key"]]
    target = train["actual_log"].to_numpy(dtype=float) - train["current_70_30"].to_numpy(dtype=float)
    model = hcoef1.linear_pipeline("huber", float(STABLE_CONFIG["alpha"]))
    model.fit(train[features], target)
    raw = np.asarray(model.predict(eval_frame[features]), dtype=float)
    correction = np.clip(raw, -float(STABLE_CONFIG["cap"]), float(STABLE_CONFIG["cap"])) * float(STABLE_CONFIG["strength"])
    pred = eval_frame["current_70_30"].to_numpy(dtype=float) + correction
    return pred, model


def prediction_frame(
    frame: pd.DataFrame,
    candidate: str,
    scope: str,
    split: str,
    pred_log: np.ndarray,
    method: str,
    repeat: int | None = None,
) -> pd.DataFrame:
    pred_price = safe_exp(pred_log)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "method": method,
        "scope": scope,
        "split": split,
        "repeat": repeat,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "artist_key": frame["artist_key"].astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series("", index=frame.index)).astype(str).to_numpy(),
        "actual_log": frame["actual_log"].to_numpy(dtype=float),
        "actual_price": actual_price,
        "pred_log": pred_log,
        "pred_price": pred_price,
        OLD_STABLE: frame[OLD_STABLE].to_numpy(dtype=float),
        OLD_CURRENT: frame[OLD_CURRENT].to_numpy(dtype=float),
        NEW_SVC: frame[NEW_SVC].to_numpy(dtype=float),
        NEW_BASIS: frame[NEW_BASIS].to_numpy(dtype=float),
        "old_hcoef_delta_log": frame["old_hcoef_delta_log"].to_numpy(dtype=float),
        "svc_group_level": frame["svc_group_level"].astype(str).to_numpy(),
        "svc_coverage_tier": frame["svc_coverage_tier"].astype(str).to_numpy(),
        "svc_group_n": frame["svc_group_n"].to_numpy(dtype=float),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def source_predictions(frame: pd.DataFrame) -> dict[str, tuple[np.ndarray, str]]:
    return {
        OLD_CURRENT: (frame[OLD_CURRENT].to_numpy(dtype=float), "source_old_current"),
        OLD_STABLE: (frame[OLD_STABLE].to_numpy(dtype=float), "source_old_stable"),
        NEW_SVC: (frame[NEW_SVC].to_numpy(dtype=float), "source_new_svc"),
        NEW_BASIS: (frame[NEW_BASIS].to_numpy(dtype=float), "source_new_basis"),
        TRANSPLANT: (frame[TRANSPLANT].to_numpy(dtype=float), "old_delta_transplant"),
    }


def repeated_oof_for_mode(mode: str, frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"].reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            seed = SEED + repeat
            folds = row_folds(len(validation), seed) if scheme == "row_oof" else artist_folds(validation, seed)
            source_map = source_predictions(validation)
            candidates = {
                **source_map,
                REFIT_PARTIAL if mode == "partial" else REFIT_SVC_PROXY: (np.full(len(validation), np.nan), f"refit_{mode}"),
            }
            refit_pred = np.full(len(validation), np.nan, dtype=float)
            for train_idx, hold_idx in folds:
                train = validation.iloc[train_idx].copy()
                hold = validation.iloc[hold_idx].copy()
                pred, _ = fit_refit_candidate(train, hold)
                refit_pred[hold_idx] = pred
            refit_name = REFIT_PARTIAL if mode == "partial" else REFIT_SVC_PROXY
            candidates[refit_name] = (refit_pred, f"refit_{mode}")

            old_stable_metric = metric(validation, validation[OLD_STABLE].to_numpy(dtype=float))
            new_basis_metric = metric(validation, validation[NEW_BASIS].to_numpy(dtype=float))
            for candidate, (pred, method) in candidates.items():
                m = metric(validation, pred)
                rows.append({
                    "experiment_id": EXP_ID,
                    "variant_mode": mode,
                    "validation_scheme": scheme,
                    "repeat": repeat,
                    "candidate": candidate,
                    "method": method,
                    "scope": f"validation_oof_{scheme}",
                    "split": "validation",
                    "n": len(validation),
                    **m,
                    "delta_MdAPE_vs_old_stable": m["MdAPE"] - old_stable_metric["MdAPE"],
                    "delta_MAPE_vs_old_stable": m["MAPE"] - old_stable_metric["MAPE"],
                    "delta_p95_APE_vs_old_stable": m["p95_APE"] - old_stable_metric["p95_APE"],
                    "delta_MdAPE_vs_new_basis": m["MdAPE"] - new_basis_metric["MdAPE"],
                    "delta_MAPE_vs_new_basis": m["MAPE"] - new_basis_metric["MAPE"],
                    "delta_p95_APE_vs_new_basis": m["p95_APE"] - new_basis_metric["p95_APE"],
                    "improve_count_vs_old_stable": int(m["MdAPE"] < old_stable_metric["MdAPE"])
                    + int(m["MAPE"] < old_stable_metric["MAPE"])
                    + int(m["p95_APE"] < old_stable_metric["p95_APE"]),
                    "improve_count_vs_new_basis": int(m["MdAPE"] < new_basis_metric["MdAPE"])
                    + int(m["MAPE"] < new_basis_metric["MAPE"])
                    + int(m["p95_APE"] < new_basis_metric["p95_APE"]),
                })
                if repeat == 0:
                    pred_rows.append(
                        prediction_frame(validation, candidate, f"validation_oof_{scheme}", "validation", pred, method, repeat)
                    )
    return pd.DataFrame(rows), pd.concat(pred_rows, ignore_index=True)


def fixed_confirmation_for_mode(mode: str, frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"].reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    refit_name = REFIT_PARTIAL if mode == "partial" else REFIT_SVC_PROXY
    for split in ["validation", "test"]:
        frame = frames[split].reset_index(drop=True)
        candidates = source_predictions(frame)
        pred, model = fit_refit_candidate(validation, frame)
        candidates[refit_name] = (pred, f"refit_{mode}")
        old_stable_metric = metric(frame, frame[OLD_STABLE].to_numpy(dtype=float))
        new_basis_metric = metric(frame, frame[NEW_BASIS].to_numpy(dtype=float))
        for candidate, (pred_log, method) in candidates.items():
            m = metric(frame, pred_log)
            rows.append({
                "experiment_id": EXP_ID,
                "variant_mode": mode,
                "validation_scheme": "fixed_confirmation",
                "repeat": -1,
                "candidate": candidate,
                "method": method,
                "scope": "fixed_confirmation",
                "split": split,
                "n": len(frame),
                **m,
                "delta_MdAPE_vs_old_stable": m["MdAPE"] - old_stable_metric["MdAPE"],
                "delta_MAPE_vs_old_stable": m["MAPE"] - old_stable_metric["MAPE"],
                "delta_p95_APE_vs_old_stable": m["p95_APE"] - old_stable_metric["p95_APE"],
                "delta_MdAPE_vs_new_basis": m["MdAPE"] - new_basis_metric["MdAPE"],
                "delta_MAPE_vs_new_basis": m["MAPE"] - new_basis_metric["MAPE"],
                "delta_p95_APE_vs_new_basis": m["p95_APE"] - new_basis_metric["p95_APE"],
                "improve_count_vs_old_stable": int(m["MdAPE"] < old_stable_metric["MdAPE"])
                + int(m["MAPE"] < old_stable_metric["MAPE"])
                + int(m["p95_APE"] < old_stable_metric["p95_APE"]),
                "improve_count_vs_new_basis": int(m["MdAPE"] < new_basis_metric["MdAPE"])
                + int(m["MAPE"] < new_basis_metric["MAPE"])
                + int(m["p95_APE"] < new_basis_metric["p95_APE"]),
            })
            pred_rows.append(prediction_frame(frame, candidate, "fixed_confirmation", split, pred_log, method, None))
        if split == "test":
            coef = hcoef3.coefficient_frame(model, STABLE_CONFIG)
            coef["experiment_id"] = EXP_ID
            coef["variant_mode"] = mode
            coef_rows.append(coef)
    return pd.DataFrame(rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coef_rows, ignore_index=True)


def summarize_repeats(metrics: pd.DataFrame) -> pd.DataFrame:
    repeated = metrics[metrics["validation_scheme"].isin(["row_oof", "artist_oof"])].copy()
    rows: list[dict[str, Any]] = []
    for (mode, scheme, candidate), group in repeated.groupby(["variant_mode", "validation_scheme", "candidate"], dropna=False):
        row = {
            "experiment_id": EXP_ID,
            "variant_mode": mode,
            "validation_scheme": scheme,
            "candidate": candidate,
            "method": str(group["method"].iloc[0]),
            "repeats": int(group["repeat"].nunique()),
            "MdAPE_mean": float(group["MdAPE"].mean()),
            "MAPE_mean": float(group["MAPE"].mean()),
            "p95_APE_mean": float(group["p95_APE"].mean()),
            "RMSE_log_mean": float(group["RMSE_log"].mean()),
            "mean_delta_MdAPE_vs_old_stable": float(group["delta_MdAPE_vs_old_stable"].mean()),
            "mean_delta_MAPE_vs_old_stable": float(group["delta_MAPE_vs_old_stable"].mean()),
            "mean_delta_p95_APE_vs_old_stable": float(group["delta_p95_APE_vs_old_stable"].mean()),
            "old_stable_MdAPE_win_rate": float((group["delta_MdAPE_vs_old_stable"] < 0).mean()),
            "old_stable_MAPE_win_rate": float((group["delta_MAPE_vs_old_stable"] < 0).mean()),
            "old_stable_p95_win_rate": float((group["delta_p95_APE_vs_old_stable"] < 0).mean()),
            "old_stable_all3_win_rate": float((group["improve_count_vs_old_stable"] == 3).mean()),
            "new_basis_MdAPE_win_rate": float((group["delta_MdAPE_vs_new_basis"] < 0).mean()),
            "new_basis_MAPE_win_rate": float((group["delta_MAPE_vs_new_basis"] < 0).mean()),
            "new_basis_p95_win_rate": float((group["delta_p95_APE_vs_new_basis"] < 0).mean()),
            "new_basis_all3_win_rate": float((group["improve_count_vs_new_basis"] == 3).mean()),
        }
        rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["validation_scheme", "MdAPE_mean", "MAPE_mean", "p95_APE_mean", "candidate"]
    )


def markdown_table(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df.empty:
        return "_결과 없음_"
    show = df.head(max_rows).copy()
    cols = list(show.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in show.iterrows():
        vals = []
        for col in cols:
            value = row[col]
            if isinstance(value, (float, np.floating)):
                vals.append(f"{float(value):.4f}")
            else:
                vals.append(str(value))
        lines.append("| " + " | ".join(vals) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(df)} rows shown._")
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

    for raw in md.splitlines():
        line = raw.rstrip()
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
        "body{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:32px;color:#1f2937;line-height:1.55}"
        "table{border-collapse:collapse;margin:12px 0;width:100%;font-size:13px}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;text-align:left}"
        "th{background:#f3f4f6}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def render_report(metrics: pd.DataFrame, summary: pd.DataFrame, fixed: pd.DataFrame, coeffs: pd.DataFrame) -> tuple[str, str]:
    focus_cols = [
        "variant_mode",
        "validation_scheme",
        "candidate",
        "MdAPE_mean",
        "MAPE_mean",
        "p95_APE_mean",
        "old_stable_MdAPE_win_rate",
        "old_stable_MAPE_win_rate",
        "old_stable_p95_win_rate",
        "new_basis_MdAPE_win_rate",
        "new_basis_MAPE_win_rate",
        "new_basis_p95_win_rate",
    ]
    fixed_cols = [
        "variant_mode",
        "split",
        "candidate",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE_vs_old_stable",
        "delta_MAPE_vs_old_stable",
        "delta_p95_APE_vs_old_stable",
        "delta_MdAPE_vs_new_basis",
        "delta_MAPE_vs_new_basis",
        "delta_p95_APE_vs_new_basis",
    ]
    val_summary = summary[summary["validation_scheme"].eq("artist_oof")].copy()
    best = val_summary.sort_values(["MdAPE_mean", "MAPE_mean", "p95_APE_mean"]).iloc[0]
    refit = val_summary[val_summary["candidate"].isin([REFIT_PARTIAL, REFIT_SVC_PROXY])].copy()
    if not refit.empty:
        refit_best = refit.sort_values(["MdAPE_mean", "MAPE_mean", "p95_APE_mean"]).iloc[0]
        refit_line = (
            f"- 재학습 HCOEF 최상위: `{refit_best['candidate']}` "
            f"artist OOF 평균 `{refit_best['MdAPE_mean']:.4f}/{refit_best['MAPE_mean']:.4f}/{refit_best['p95_APE_mean']:.4f}`."
        )
    else:
        refit_line = "- 재학습 HCOEF 후보 없음."
    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: WMIN2의 min1 SVC/70:30 개선이 HCOEF 안정 보정 단계에서도 유지되는지 확인한다.",
        "- selection 기준: validation row/artist OOF. fixed test는 최종 확인용.",
        "- partial 모드: min1 `current_70_30`과 `svc_fallback`만 교체하고 기존 raw/shrunk SVC prior는 유지한다.",
        "- svc_proxy 모드: raw/shrunk SVC prior도 min1 SVC로 치환해 전체 SVC 교체에 가까운 proxy를 본다.",
        "",
        "## 1. 결론 요약",
        "",
        f"- validation artist OOF 최상위: `{best['candidate']}` `{best['MdAPE_mean']:.4f}/{best['MAPE_mean']:.4f}/{best['p95_APE_mean']:.4f}`.",
        refit_line,
        "- min1 70:30 자체가 기존 HCOEF 안정 후보보다 강해지는지와, 그 위에 기존 HCOEF 잔차 보정을 다시 얹을 가치가 있는지를 분리해 판단한다.",
        "",
        "## 2. Repeated Validation Summary",
        "",
        markdown_table(summary[focus_cols].round(4), max_rows=80),
        "",
        "## 3. Fixed Confirmation",
        "",
        markdown_table(fixed[fixed_cols].round(4), max_rows=80),
        "",
        "## 4. HCOEF Refit Coefficients",
        "",
        markdown_table(coeffs.sort_values(["variant_mode", "abs_coefficient"], ascending=[True, False]).round(5), max_rows=60),
        "",
        "## 5. 다음 판단",
        "",
        "- refit 후보가 min1 70:30보다 validation OOF에서 안정적으로 좋아지면 PP-WMIN4 decision layer 재학습 대상에 포함한다.",
        "- refit 후보가 min1 70:30보다 약하면 WMIN4는 min1 70:30 또는 min1 SVC 기반 PP258 decision 재학습 중심으로 진행한다.",
    ])
    return md + "\n", md_to_html(md)


def main() -> None:
    start = time.time()
    ensure_dirs()
    all_metrics: list[pd.DataFrame] = []
    all_preds: list[pd.DataFrame] = []
    all_coeffs: list[pd.DataFrame] = []
    all_fixed: list[pd.DataFrame] = []
    for mode in ["partial", "svc_proxy"]:
        frames = make_variant_frames(mode)
        repeated_metrics, repeated_preds = repeated_oof_for_mode(mode, frames)
        fixed_metrics, fixed_preds, coeffs = fixed_confirmation_for_mode(mode, frames)
        all_metrics.extend([repeated_metrics, fixed_metrics])
        all_preds.extend([repeated_preds, fixed_preds])
        all_coeffs.append(coeffs)
        all_fixed.append(fixed_metrics)

    metrics = pd.concat(all_metrics, ignore_index=True, sort=False)
    predictions = pd.concat(all_preds, ignore_index=True, sort=False)
    coeffs = pd.concat(all_coeffs, ignore_index=True, sort=False)
    fixed = pd.concat(all_fixed, ignore_index=True, sort=False)
    summary = summarize_repeats(metrics)

    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    summary.to_csv(EXP_DIR / "outputs" / "repeated_summary.csv", index=False)
    fixed.to_csv(EXP_DIR / "outputs" / "fixed_candidate_metrics.csv", index=False)
    coeffs.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)

    run_config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "n_folds": N_FOLDS,
        "n_repeats": N_REPEATS,
        "source_wmin2_predictions": str(WMIN2_PREDICTIONS.relative_to(REPO)),
        "source_wmin2_features": str(WMIN2_FEATURES.relative_to(REPO)),
        "source_old_hcoef": str(HCOEF18_PREDICTIONS.relative_to(REPO)),
        "stable_config": STABLE_CONFIG,
        "candidate_definitions": {
            OLD_CURRENT: "기존 min5 SVC 기반 70:30",
            OLD_STABLE: "기존 HCOEF 안정 후보",
            NEW_SVC: "WMIN2 min1 SVC seed mean",
            NEW_BASIS: "WMIN2 min1 SVC 70% + PP-V8 30%",
            TRANSPLANT: "min1 70:30 + 기존 HCOEF 이동분",
            REFIT_PARTIAL: "min1 current/svc 교체 후 HCOEF 안정 보정 재학습",
            REFIT_SVC_PROXY: "min1 current/svc/raw/shrunk proxy 교체 후 HCOEF 안정 보정 재학습",
        },
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(metrics, summary, fixed, coeffs)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_wmin3_warm_min1_hcoef_refit_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")

    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "summary_doc": str((DOC_ROOT / "pp_wmin3_warm_min1_hcoef_refit_summary.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
