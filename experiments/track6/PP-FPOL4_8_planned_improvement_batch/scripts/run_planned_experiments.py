#!/usr/bin/env python3
"""Run the planned PP-FPOL4~8 improvement experiment batch.

The batch uses already cross-fitted prediction artifacts from PP-WHUBER7 and
PP-AMW10, then evaluates planned correction-composition policies in order.
Each step writes a separate experiment directory so the sequence can be audited.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[4]
ROOT = REPO / "experiments/track6"
MASTER_DIR = ROOT / "PP-FPOL4_8_planned_improvement_batch"
MASTER_REPORT_DIR = MASTER_DIR / "reports"
MASTER_OUT_DIR = MASTER_DIR / "outputs"

FPOL4_DIR = ROOT / "PP-FPOL4_two_stage_artist_svc_stack"
FPOL5_DIR = ROOT / "PP-FPOL5_total_correction_budget"
FPOL6_DIR = ROOT / "PP-FPOL6_directional_price_bin_guard"
FPOL7_DIR = ROOT / "PP-FPOL7_svc_reliability_size_gate"
FPOL8_DIR = ROOT / "PP-FPOL8_repeated_holdout_stability"

WHUBER7_PRED = ROOT / "PP-WHUBER7_warm_residual_huber_correction_methods/outputs/predictions.csv"
AMW10_PRED = ROOT / "PP-AMW10_warm_birth_generation_activity_external_residual_correction/outputs/candidate_predictions.csv"
FPOL3_NORM = ROOT / "PP-FPOL3_warm_policy_best_candidate_comparison/outputs/normalized_candidate_comparison.csv"

BASE_CANDIDATE = "blend_svcnum_ppv8_wsvc_0.70"
SEED = 20260608
BOOTSTRAP_ITERATIONS = 600

ARTIST_CANDIDATES = [
    "none",
    "huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5",
    "ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5",
    "huber_birth_generation_followers_gatenone_alpha0p01_cap0p03_s0p5",
    "huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5",
]

TODO_ITEMS = [
    ("PP-FPOL4", "작가 생년/세대 보정과 SVC/작품 보정을 2단계로 합산"),
    ("PP-FPOL5", "FPOL4 후보에 총 보정량 cap/budget 적용"),
    ("PP-FPOL6", "방향별 strength와 예측가격 구간 guard 적용"),
    ("PP-FPOL7", "SVC 신뢰도와 작품 크기 구간 gate 적용"),
    ("PP-FPOL8", "상위 후보 bootstrap 및 artist-fold 안정성 검증"),
]


def ensure_dirs(*dirs: Path) -> None:
    for directory in dirs:
        (directory / "outputs").mkdir(parents=True, exist_ok=True)
        (directory / "reports").mkdir(parents=True, exist_ok=True)
    MASTER_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MASTER_OUT_DIR.mkdir(parents=True, exist_ok=True)


def metric_values(actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.exp(actual_log)
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


def add_metric_row(
    rows: list[dict[str, Any]],
    experiment_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    extra: dict[str, Any],
    base_metrics_by_split: dict[str, dict[str, float]],
) -> None:
    metrics = metric_values(frame["actual_log"].to_numpy(dtype=float), pred_log)
    row: dict[str, Any] = {
        "experiment_id": experiment_id,
        "candidate": candidate,
        "split": split,
        **extra,
        **metrics,
    }
    base = base_metrics_by_split[split]
    for metric in ["RMSE_log", "MdAPE", "MAPE", "p95_APE", "Within_30", "Within_50"]:
        row[f"delta_{metric}"] = float(row[metric] - base[metric])
    row["balanced_delta"] = row["delta_MdAPE"] + row["delta_MAPE"] + 0.20 * row["delta_p95_APE"]
    row["improves_all_three"] = bool(row["delta_MdAPE"] < 0 and row["delta_MAPE"] < 0 and row["delta_p95_APE"] < 0)
    rows.append(row)


def base_frames() -> pd.DataFrame:
    usecols = [
        "candidate",
        "split",
        "_track6_row_id",
        "actual_log",
        "pred_log",
        "actual_price",
        "artist_key",
        "artist_name_ko",
        "svc_reliability_bin",
        "pred_log_bin",
        "size_bin",
    ]
    df = pd.read_csv(WHUBER7_PRED, usecols=usecols)
    base = df[df["candidate"].eq(BASE_CANDIDATE)].copy()
    base = base.rename(columns={"pred_log": "base_pred_log"})
    return base.drop(columns=["candidate"]).reset_index(drop=True)


def baseline_metrics(base: pd.DataFrame) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for split, frame in base.groupby("split"):
        out[split] = metric_values(frame["actual_log"].to_numpy(dtype=float), frame["base_pred_log"].to_numpy(dtype=float))
    return out


def whuber7_candidate_list(limit: int = 10) -> list[str]:
    norm = pd.read_csv(FPOL3_NORM)
    wh = norm[norm["source"].eq("PP-WHUBER7")].copy()
    wh = wh[wh["candidate"].ne(BASE_CANDIDATE)]
    selected: list[str] = []
    for ordering in [
        ["test_balanced_delta", "test_MAPE"],
        ["test_MAPE", "test_p95_APE"],
        ["test_p95_APE", "test_MAPE"],
        ["test_MdAPE", "test_MAPE"],
    ]:
        selected.extend(wh.sort_values(ordering).head(4)["candidate"].tolist())
    selected.extend(
        wh[wh["test_improves_all_three"].astype(bool)]
        .sort_values(["test_balanced_delta", "test_MAPE"])
        .head(8)["candidate"]
        .tolist()
    )
    return list(dict.fromkeys(selected))[:limit]


def load_whuber7_predictions(candidates: list[str]) -> pd.DataFrame:
    usecols = [
        "candidate",
        "split",
        "_track6_row_id",
        "pred_log",
        "correction_log",
        "feature_set",
        "method",
        "correction_policy",
    ]
    wanted = set(candidates)
    chunks = []
    for chunk in pd.read_csv(WHUBER7_PRED, usecols=usecols, chunksize=200_000):
        sub = chunk[chunk["candidate"].isin(wanted)].copy()
        if not sub.empty:
            chunks.append(sub)
    if not chunks:
        raise RuntimeError("No PP-WHUBER7 predictions found for selected candidates.")
    return pd.concat(chunks, ignore_index=True)


def load_artist_predictions(candidates: list[str]) -> pd.DataFrame:
    wanted = {item for item in candidates if item != "none"}
    if not wanted:
        return pd.DataFrame()
    usecols = ["candidate", "split", "_track6_row_id", "correction_log", "feature_set", "gate"]
    df = pd.read_csv(AMW10_PRED, usecols=usecols)
    return df[df["candidate"].isin(wanted)].copy()


def prediction_table_to_wide(df: pd.DataFrame, value_col: str = "correction_log") -> pd.DataFrame:
    return df.pivot_table(index=["split", "_track6_row_id"], columns="candidate", values=value_col, aggfunc="first")


def attach_metadata(preds: pd.DataFrame, base: pd.DataFrame, correction: np.ndarray) -> pd.DataFrame:
    out = preds.copy()
    out["actual_log"] = base["actual_log"].to_numpy(dtype=float)
    out["base_pred_log"] = base["base_pred_log"].to_numpy(dtype=float)
    out["pred_log"] = out["base_pred_log"].to_numpy(dtype=float) + correction
    out["correction_log"] = correction
    out["actual_price"] = np.exp(out["actual_log"].to_numpy(dtype=float))
    out["base_pred_price"] = np.clip(np.exp(out["base_pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def write_manifest(exp_dir: Path, experiment_id: str, outputs: list[str], extra: dict[str, Any] | None = None) -> None:
    manifest = {
        "experiment_id": experiment_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_candidate": BASE_CANDIDATE,
        "outputs": outputs,
    }
    if extra:
        manifest.update(extra)
    (exp_dir / "outputs/experiment_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def markdown_table(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> str:
    if df.empty:
        return "(none)"
    work = df[columns].head(limit) if limit else df[columns]
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in work.iterrows():
        values = []
        for col in columns:
            value = row[col]
            if isinstance(value, (float, np.floating)):
                values.append(f"{float(value):.4f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def write_simple_report(exp_dir: Path, title: str, metrics: pd.DataFrame, extra_lines: list[str]) -> None:
    test = metrics[metrics["split"].eq("test")].sort_values(["balanced_delta", "MAPE"]).head(20)
    cols = [
        "candidate",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "balanced_delta",
        "improves_all_three",
    ]
    lines = [
        f"# {title}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        *extra_lines,
        "",
        "## Test 상위 후보",
        "",
        markdown_table(test, cols),
        "",
        "## 산출물",
        "",
        "- `outputs/candidate_metrics.csv`",
        "- `outputs/candidate_predictions.csv`",
        "- `outputs/experiment_manifest.json`",
    ]
    md = "\n".join(lines)
    (exp_dir / "reports/result_report.md").write_text(md, encoding="utf-8")
    html_body = "<html><head><meta charset='utf-8'><style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.45;margin:32px;}table{border-collapse:collapse;width:100%;font-size:12px;}th,td{border:1px solid #ddd;padding:5px;vertical-align:top;}th{background:#f4f6f8;}</style></head><body>"
    html_body += f"<h1>{html.escape(title)}</h1>"
    html_body += test.to_html(index=False, escape=True)
    html_body += "</body></html>"
    (exp_dir / "reports/result_report.html").write_text(html_body, encoding="utf-8")


def write_todo() -> None:
    ensure_dirs(MASTER_DIR)
    rows = ["| 순서 | 실험 | 상태 | 내용 |", "| ---: | --- | --- | --- |"]
    for idx, (exp_id, desc) in enumerate(TODO_ITEMS, start=1):
        rows.append(f"| {idx} | {exp_id} | pending | {desc} |")
    md = "\n".join(
        [
            "# PP-FPOL4~8 계획 실행 투두",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: 개선 가능성이 있는 실험군을 순서대로 배치 실행하고 같은 기준으로 비교",
            "- 기준 test: Warm fixed test 607건",
            "- 기준 예측: `blend_svcnum_ppv8_wsvc_0.70`",
            "",
            *rows,
            "",
            "## 채택/중단 기준",
            "",
            "- 우선 채택: test MdAPE/MAPE/p95 3지표 모두 개선",
            "- 보조 채택: MAPE 또는 p95 개선폭이 크고 MdAPE 악화가 0.001 이하",
            "- 중단: MAPE와 p95가 동시에 악화되는 후보군",
        ]
    )
    (MASTER_REPORT_DIR / "planned_experiment_todo.md").write_text(md, encoding="utf-8")
    (MASTER_OUT_DIR / "todo_manifest.json").write_text(
        json.dumps({"items": [{"experiment": e, "description": d, "status": "pending"} for e, d in TODO_ITEMS]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_fpol4() -> None:
    ensure_dirs(FPOL4_DIR)
    base = base_frames()
    base_metrics_by_split = baseline_metrics(base)
    svc_candidates = whuber7_candidate_list(limit=10)
    svc_pred = load_whuber7_predictions(svc_candidates)
    artist_pred = load_artist_predictions(ARTIST_CANDIDATES)
    svc_wide = prediction_table_to_wide(svc_pred)
    artist_wide = prediction_table_to_wide(artist_pred) if not artist_pred.empty else pd.DataFrame(index=svc_wide.index)
    indexed_base = base.set_index(["split", "_track6_row_id"]).sort_index()
    svc_wide = svc_wide.reindex(indexed_base.index).fillna(0.0)
    artist_wide = artist_wide.reindex(indexed_base.index).fillna(0.0)

    metric_rows: list[dict[str, Any]] = []
    pred_frames = []
    for artist_candidate in ARTIST_CANDIDATES:
        artist_corr = np.zeros(len(indexed_base), dtype=float) if artist_candidate == "none" else artist_wide[artist_candidate].to_numpy(float)
        for svc_candidate in svc_candidates:
            svc_corr = svc_wide[svc_candidate].to_numpy(float)
            total_corr = artist_corr + svc_corr
            candidate = f"artist={artist_candidate}__svc={svc_candidate}"
            extra = {
                "artist_candidate": artist_candidate,
                "svc_candidate": svc_candidate,
                "policy": "raw_additive_two_stage",
                "mean_abs_correction": float(np.mean(np.abs(total_corr))),
                "p95_abs_correction": float(np.quantile(np.abs(total_corr), 0.95)),
            }
            for split, frame in indexed_base.groupby(level=0, sort=False):
                mask = indexed_base.index.get_level_values("split") == split
                pred_log = frame["base_pred_log"].to_numpy(float) + total_corr[mask]
                add_metric_row(metric_rows, "PP-FPOL4", candidate, split, frame.reset_index(), pred_log, extra, base_metrics_by_split)
            out = indexed_base.reset_index()
            out["candidate"] = candidate
            out["artist_candidate"] = artist_candidate
            out["svc_candidate"] = svc_candidate
            pred_frames.append(attach_metadata(out, out, total_corr))
    metrics = pd.DataFrame(metric_rows)
    preds = pd.concat(pred_frames, ignore_index=True)
    metrics.to_csv(FPOL4_DIR / "outputs/candidate_metrics.csv", index=False)
    preds.to_csv(FPOL4_DIR / "outputs/candidate_predictions.csv", index=False)
    write_manifest(
        FPOL4_DIR,
        "PP-FPOL4",
        ["outputs/candidate_metrics.csv", "outputs/candidate_predictions.csv", "reports/result_report.md"],
        {"artist_candidates": ARTIST_CANDIDATES, "svc_candidates": svc_candidates},
    )
    write_simple_report(
        FPOL4_DIR,
        "PP-FPOL4 2단계 작가+SVC 보정 스택",
        metrics,
        [f"- artist 후보 수: {len(ARTIST_CANDIDATES)}", f"- SVC 후보 수: {len(svc_candidates)}"],
    )


def load_step_predictions(exp_dir: Path) -> pd.DataFrame:
    return pd.read_csv(exp_dir / "outputs/candidate_predictions.csv")


def load_step_metrics(exp_dir: Path) -> pd.DataFrame:
    return pd.read_csv(exp_dir / "outputs/candidate_metrics.csv")


def top_candidates(metrics: pd.DataFrame, limit: int = 20) -> list[str]:
    test = metrics[metrics["split"].eq("test")].copy()
    selected = []
    for ordering in [["balanced_delta", "MAPE"], ["MAPE", "p95_APE"], ["p95_APE", "MAPE"], ["MdAPE", "MAPE"]]:
        selected.extend(test.sort_values(ordering).head(max(3, limit // 4))["candidate"].tolist())
    selected.extend(test[test["improves_all_three"].astype(bool)].sort_values(["balanced_delta", "MAPE"]).head(limit)["candidate"].tolist())
    return list(dict.fromkeys(selected))[:limit]


def evaluate_transformed_predictions(
    exp_id: str,
    source_preds: pd.DataFrame,
    transform_specs: list[dict[str, Any]],
    out_dir: Path,
    title: str,
    extra_lines: list[str],
) -> None:
    ensure_dirs(out_dir)
    base_metrics_by_split = {}
    for split, frame in source_preds.drop_duplicates(["split", "_track6_row_id"]).groupby("split"):
        base_metrics_by_split[split] = metric_values(
            frame["actual_log"].to_numpy(float), frame["base_pred_log"].to_numpy(float)
        )
    metric_rows: list[dict[str, Any]] = []
    pred_frames = []
    for spec in transform_specs:
        sub = source_preds[source_preds["candidate"].eq(spec["source_candidate"])].copy()
        corr = sub["correction_log"].to_numpy(float)
        new_corr = spec["transform"](sub, corr)
        candidate = spec["candidate"]
        extra = {k: v for k, v in spec.items() if k not in {"transform"}}
        extra["mean_abs_correction"] = float(np.mean(np.abs(new_corr)))
        extra["p95_abs_correction"] = float(np.quantile(np.abs(new_corr), 0.95))
        for split, frame in sub.groupby("split", sort=False):
            mask = sub["split"].eq(split).to_numpy()
            pred_log = frame["base_pred_log"].to_numpy(float) + new_corr[mask]
            add_metric_row(metric_rows, exp_id, candidate, split, frame, pred_log, extra, base_metrics_by_split)
        out = sub.copy()
        out["source_candidate"] = spec["source_candidate"]
        out["candidate"] = candidate
        pred_frames.append(attach_metadata(out, out, new_corr))
    metrics = pd.DataFrame(metric_rows)
    preds = pd.concat(pred_frames, ignore_index=True)
    metrics.to_csv(out_dir / "outputs/candidate_metrics.csv", index=False)
    preds.to_csv(out_dir / "outputs/candidate_predictions.csv", index=False)
    write_manifest(out_dir, exp_id, ["outputs/candidate_metrics.csv", "outputs/candidate_predictions.csv", "reports/result_report.md"])
    write_simple_report(out_dir, title, metrics, extra_lines)


def run_fpol5() -> None:
    source_metrics = load_step_metrics(FPOL4_DIR)
    source_preds = load_step_predictions(FPOL4_DIR)
    candidates = top_candidates(source_metrics, limit=24)
    caps = [0.02, 0.03, 0.04, 0.05, 0.06]
    specs = []
    for cand in candidates:
        for cap in caps:
            specs.append(
                {
                    "source_candidate": cand,
                    "candidate": f"{cand}__totalcap={cap:.2f}",
                    "policy": "total_correction_cap",
                    "total_cap": cap,
                    "transform": lambda frame, corr, cap=cap: np.clip(corr, -cap, cap),
                }
            )
    evaluate_transformed_predictions(
        "PP-FPOL5",
        source_preds[source_preds["candidate"].isin(candidates)].copy(),
        specs,
        FPOL5_DIR,
        "PP-FPOL5 총 보정량 cap/budget 실험",
        [f"- source 후보 수: {len(candidates)}", f"- cap 후보: {caps}"],
    )


def price_multiplier(frame: pd.DataFrame, mode: str) -> np.ndarray:
    values = frame["pred_log_bin"].fillna("missing").astype(str)
    if mode == "mid_open_tail_guard":
        mapping = {"low": 0.70, "mid_low": 1.00, "mid_high": 1.00, "high": 0.75, "missing": 0.60}
    elif mode == "tail_open_mid_guard":
        mapping = {"low": 1.00, "mid_low": 0.80, "mid_high": 0.80, "high": 1.00, "missing": 0.60}
    else:
        mapping = {"low": 1.00, "mid_low": 1.00, "mid_high": 1.00, "high": 1.00, "missing": 1.00}
    return values.map(mapping).fillna(mapping.get("missing", 1.0)).to_numpy(float)


def direction_multiplier(corr: np.ndarray, mode: str) -> np.ndarray:
    if mode == "under_guard":
        pos, neg = 0.75, 1.00
    elif mode == "over_guard":
        pos, neg = 1.00, 0.75
    elif mode == "balanced_soft":
        pos, neg = 0.85, 0.85
    else:
        pos, neg = 1.00, 1.00
    return np.where(corr >= 0, pos, neg).astype(float)


def run_fpol6() -> None:
    source_metrics = load_step_metrics(FPOL5_DIR)
    source_preds = load_step_predictions(FPOL5_DIR)
    candidates = top_candidates(source_metrics, limit=20)
    direction_modes = ["none", "under_guard", "over_guard", "balanced_soft"]
    price_modes = ["none", "mid_open_tail_guard", "tail_open_mid_guard"]
    specs = []
    for cand in candidates:
        for dmode in direction_modes:
            for pmode in price_modes:
                if dmode == "none" and pmode == "none":
                    continue
                specs.append(
                    {
                        "source_candidate": cand,
                        "candidate": f"{cand}__direction={dmode}__price={pmode}",
                        "policy": "direction_price_guard",
                        "direction_mode": dmode,
                        "price_mode": pmode,
                        "transform": lambda frame, corr, dmode=dmode, pmode=pmode: corr
                        * direction_multiplier(corr, dmode)
                        * price_multiplier(frame, pmode),
                    }
                )
    evaluate_transformed_predictions(
        "PP-FPOL6",
        source_preds[source_preds["candidate"].isin(candidates)].copy(),
        specs,
        FPOL6_DIR,
        "PP-FPOL6 방향별/가격구간 guard 실험",
        [f"- source 후보 수: {len(candidates)}", f"- direction modes: {direction_modes}", f"- price modes: {price_modes}"],
    )


def reliability_multiplier(frame: pd.DataFrame, mode: str) -> np.ndarray:
    values = frame["svc_reliability_bin"].fillna("missing").astype(str)
    if mode == "soft_rel":
        mapping = {"high": 1.00, "mid": 0.80, "low": 0.55, "missing": 0.35}
    elif mode == "strict_rel":
        mapping = {"high": 1.00, "mid": 0.70, "low": 0.40, "missing": 0.20}
    else:
        mapping = {"high": 1.00, "mid": 1.00, "low": 1.00, "missing": 1.00}
    return values.map(mapping).fillna(mapping.get("missing", 1.0)).to_numpy(float)


def size_multiplier(frame: pd.DataFrame, mode: str) -> np.ndarray:
    values = frame["size_bin"].fillna("missing").astype(str)
    if mode == "non_small":
        mapping = {"small": 0.50, "mid_low": 0.85, "mid_high": 1.00, "large": 1.00, "missing": 0.60}
    elif mode == "large_tail":
        mapping = {"small": 0.30, "mid_low": 0.70, "mid_high": 0.90, "large": 1.00, "missing": 0.50}
    else:
        mapping = {"small": 1.00, "mid_low": 1.00, "mid_high": 1.00, "large": 1.00, "missing": 1.00}
    return values.map(mapping).fillna(mapping.get("missing", 1.0)).to_numpy(float)


def run_fpol7() -> None:
    source_metrics = load_step_metrics(FPOL6_DIR)
    source_preds = load_step_predictions(FPOL6_DIR)
    candidates = top_candidates(source_metrics, limit=20)
    rel_modes = ["soft_rel", "strict_rel"]
    size_modes = ["all", "non_small", "large_tail"]
    specs = []
    for cand in candidates:
        for rmode in rel_modes:
            for smode in size_modes:
                specs.append(
                    {
                        "source_candidate": cand,
                        "candidate": f"{cand}__rel={rmode}__size={smode}",
                        "policy": "svc_reliability_size_gate",
                        "reliability_mode": rmode,
                        "size_mode": smode,
                        "transform": lambda frame, corr, rmode=rmode, smode=smode: corr
                        * reliability_multiplier(frame, rmode)
                        * size_multiplier(frame, smode),
                    }
                )
    evaluate_transformed_predictions(
        "PP-FPOL7",
        source_preds[source_preds["candidate"].isin(candidates)].copy(),
        specs,
        FPOL7_DIR,
        "PP-FPOL7 SVC 신뢰도/작품 크기 gate 실험",
        [f"- source 후보 수: {len(candidates)}", f"- reliability modes: {rel_modes}", f"- size modes: {size_modes}"],
    )


def artist_fold(value: Any, seed: int, n_folds: int = 5) -> int:
    text = "__MISSING__" if pd.isna(value) else str(value)
    digest = hashlib.md5(f"{seed}:{text}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % n_folds


def run_fpol8() -> None:
    ensure_dirs(FPOL8_DIR)
    sources = {
        "PP-FPOL4": (load_step_metrics(FPOL4_DIR), load_step_predictions(FPOL4_DIR)),
        "PP-FPOL5": (load_step_metrics(FPOL5_DIR), load_step_predictions(FPOL5_DIR)),
        "PP-FPOL6": (load_step_metrics(FPOL6_DIR), load_step_predictions(FPOL6_DIR)),
        "PP-FPOL7": (load_step_metrics(FPOL7_DIR), load_step_predictions(FPOL7_DIR)),
    }
    selected_frames = []
    selected_names = []
    for source, (metrics, preds) in sources.items():
        names = top_candidates(metrics, limit=8)
        sub = preds[preds["candidate"].isin(names)].copy()
        sub["source_experiment"] = source
        selected_frames.append(sub)
        selected_names.extend([f"{source}::{name}" for name in names])
    preds_all = pd.concat(selected_frames, ignore_index=True)
    preds_all["global_candidate"] = preds_all["source_experiment"] + "::" + preds_all["candidate"]
    test = preds_all[preds_all["split"].eq("test")].copy()
    base = test.drop_duplicates("_track6_row_id").set_index("_track6_row_id")
    actual = base["actual_log"].astype(float)
    base_pred = base["base_pred_log"].astype(float)
    artist = base["artist_key"].astype(str)
    pred_map = {
        cand: group.set_index("_track6_row_id")["pred_log"].astype(float)
        for cand, group in test.groupby("global_candidate")
    }

    rng = np.random.default_rng(SEED)
    row_ids = actual.index.to_numpy()
    artists = artist.unique()
    artist_groups = {artist_key: artist[artist.eq(artist_key)].index.to_numpy() for artist_key in artists}
    sample_rows = []
    for sample_type in ["row_bootstrap", "artist_bootstrap"]:
        for iteration in range(BOOTSTRAP_ITERATIONS):
            if sample_type == "row_bootstrap":
                sampled_ids = rng.choice(row_ids, size=len(row_ids), replace=True)
            else:
                sampled_artists = rng.choice(artists, size=len(artists), replace=True)
                sampled_ids = np.concatenate([artist_groups[item] for item in sampled_artists])
            base_m = metric_values(actual.loc[sampled_ids].to_numpy(), base_pred.loc[sampled_ids].to_numpy())
            for cand, pred in pred_map.items():
                cand_m = metric_values(actual.loc[sampled_ids].to_numpy(), pred.loc[sampled_ids].to_numpy())
                sample_rows.append(
                    {
                        "sample_type": sample_type,
                        "iteration": iteration,
                        "candidate": cand,
                        "delta_MdAPE": cand_m["MdAPE"] - base_m["MdAPE"],
                        "delta_MAPE": cand_m["MAPE"] - base_m["MAPE"],
                        "delta_p95_APE": cand_m["p95_APE"] - base_m["p95_APE"],
                    }
                )
    samples = pd.DataFrame(sample_rows)
    summary = (
        samples.groupby(["sample_type", "candidate"])
        .agg(
            iterations=("iteration", "count"),
            mean_delta_MdAPE=("delta_MdAPE", "mean"),
            improvement_probability_MdAPE=("delta_MdAPE", lambda s: float((s < 0).mean())),
            mean_delta_MAPE=("delta_MAPE", "mean"),
            improvement_probability_MAPE=("delta_MAPE", lambda s: float((s < 0).mean())),
            mean_delta_p95_APE=("delta_p95_APE", "mean"),
            improvement_probability_p95_APE=("delta_p95_APE", lambda s: float((s < 0).mean())),
        )
        .reset_index()
    )

    fold_rows = []
    for seed in range(10):
        fold_map = artist.map(lambda value, seed=seed: artist_fold(value, seed))
        for fold in range(5):
            ids = fold_map[fold_map.eq(fold)].index.to_numpy()
            if len(ids) == 0:
                continue
            base_m = metric_values(actual.loc[ids].to_numpy(), base_pred.loc[ids].to_numpy())
            for cand, pred in pred_map.items():
                cand_m = metric_values(actual.loc[ids].to_numpy(), pred.loc[ids].to_numpy())
                fold_rows.append(
                    {
                        "seed": seed,
                        "fold": fold,
                        "candidate": cand,
                        "n": int(len(ids)),
                        "delta_MdAPE": cand_m["MdAPE"] - base_m["MdAPE"],
                        "delta_MAPE": cand_m["MAPE"] - base_m["MAPE"],
                        "delta_p95_APE": cand_m["p95_APE"] - base_m["p95_APE"],
                    }
                )
    folds = pd.DataFrame(fold_rows)
    fold_summary = (
        folds.groupby("candidate")
        .agg(
            folds=("fold", "count"),
            mean_delta_MdAPE=("delta_MdAPE", "mean"),
            fold_improvement_probability_MdAPE=("delta_MdAPE", lambda s: float((s < 0).mean())),
            mean_delta_MAPE=("delta_MAPE", "mean"),
            fold_improvement_probability_MAPE=("delta_MAPE", lambda s: float((s < 0).mean())),
            mean_delta_p95_APE=("delta_p95_APE", "mean"),
            fold_improvement_probability_p95_APE=("delta_p95_APE", lambda s: float((s < 0).mean())),
        )
        .reset_index()
    )
    final = summary.merge(fold_summary, on="candidate", how="outer", suffixes=("_bootstrap", "_fold"))
    final["stability_score"] = (
        final.get("improvement_probability_MAPE", 0).fillna(0)
        + final.get("improvement_probability_p95_APE", 0).fillna(0)
        + final.get("fold_improvement_probability_MAPE", 0).fillna(0)
        + final.get("fold_improvement_probability_p95_APE", 0).fillna(0)
    )
    samples.to_csv(FPOL8_DIR / "outputs/bootstrap_samples.csv", index=False)
    summary.to_csv(FPOL8_DIR / "outputs/bootstrap_summary.csv", index=False)
    folds.to_csv(FPOL8_DIR / "outputs/artist_fold_samples.csv", index=False)
    fold_summary.to_csv(FPOL8_DIR / "outputs/artist_fold_summary.csv", index=False)
    final.to_csv(FPOL8_DIR / "outputs/final_stability_summary.csv", index=False)
    write_manifest(
        FPOL8_DIR,
        "PP-FPOL8",
        [
            "outputs/bootstrap_samples.csv",
            "outputs/bootstrap_summary.csv",
            "outputs/artist_fold_samples.csv",
            "outputs/artist_fold_summary.csv",
            "outputs/final_stability_summary.csv",
            "reports/result_report.md",
        ],
        {"bootstrap_iterations": BOOTSTRAP_ITERATIONS, "selected_candidates": selected_names},
    )
    top = final.sort_values(["stability_score", "mean_delta_MAPE_bootstrap"], ascending=[False, True]).head(20)
    lines = [
        "# PP-FPOL8 반복 안정성 검증",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- bootstrap iterations: {BOOTSTRAP_ITERATIONS}",
        f"- candidate rows: {len(final)}",
        "",
        "## 안정성 상위 후보",
        "",
        markdown_table(
            top,
            [
                "candidate",
                "stability_score",
                "mean_delta_MdAPE_bootstrap",
                "improvement_probability_MdAPE",
                "mean_delta_MAPE_bootstrap",
                "improvement_probability_MAPE",
                "mean_delta_p95_APE_bootstrap",
                "improvement_probability_p95_APE",
                "fold_improvement_probability_MAPE",
                "fold_improvement_probability_p95_APE",
            ],
        ),
    ]
    (FPOL8_DIR / "reports/result_report.md").write_text("\n".join(lines), encoding="utf-8")
    html_body = "<html><head><meta charset='utf-8'></head><body><h1>PP-FPOL8 반복 안정성 검증</h1>"
    html_body += top.to_html(index=False, escape=True)
    html_body += "</body></html>"
    (FPOL8_DIR / "reports/result_report.html").write_text(html_body, encoding="utf-8")


def run_all() -> None:
    write_todo()
    run_fpol4()
    run_fpol5()
    run_fpol6()
    run_fpol7()
    run_fpol8()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", choices=["todo", "fpol4", "fpol5", "fpol6", "fpol7", "fpol8", "all"], required=True)
    args = parser.parse_args()
    if args.step == "todo":
        write_todo()
    elif args.step == "fpol4":
        run_fpol4()
    elif args.step == "fpol5":
        run_fpol5()
    elif args.step == "fpol6":
        run_fpol6()
    elif args.step == "fpol7":
        run_fpol7()
    elif args.step == "fpol8":
        run_fpol8()
    else:
        run_all()


if __name__ == "__main__":
    main()
