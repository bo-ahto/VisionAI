#!/usr/bin/env python3
"""Run PP-SVC3 Warm SVC blend/routing experiment."""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-SVC3"
EXP_SLUG = "PP-SVC3_warm_svc_blend_routing"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm 비교군 통계 후보 결합/라우팅"
SOURCE_PREDICTIONS = EXP_ROOT / "PP-SVC2_warm_comparable_stats_stability" / "outputs" / "predictions.csv"
SEED = 20260603
BOOTSTRAP_ITERATIONS = 500

BASE_CANDIDATES = [
    "svc_numeric_seed_mean",
    "svc_full_seed_mean",
    "pp_v6_fine_blend_mape_guarded",
    "pp_v8_compact_blend_mape_guarded",
]
SVC_CANDIDATES = ["svc_numeric_seed_mean", "svc_full_seed_mean"]
PP_CANDIDATES = ["pp_v6_fine_blend_mape_guarded", "pp_v8_compact_blend_mape_guarded"]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_wide_predictions() -> pd.DataFrame:
    long = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    long = long[long["split"].isin(["validation", "test"])].copy()
    base_cols = ["split", "_track6_row_id", "actual_log", "actual_price", "artist_key", "artist_name_ko", "artist_works_count_train"]
    base = long[base_cols].drop_duplicates(["split", "_track6_row_id"]).copy()
    meta_cols = ["split", "_track6_row_id", "svc_group_level", "svc_coverage_tier", "svc_group_n"]
    meta = (
        long[meta_cols]
        .replace({"": np.nan})
        .dropna(subset=["svc_group_level"])
        .drop_duplicates(["split", "_track6_row_id"])
    )
    wide = long.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    out = base.merge(meta, on=["split", "_track6_row_id"], how="left").merge(wide, on=["split", "_track6_row_id"], how="inner")
    out["svc_group_level"] = out["svc_group_level"].fillna("__MISSING__")
    out["svc_coverage_tier"] = out["svc_coverage_tier"].fillna("__MISSING__")
    out["svc_group_n"] = pd.to_numeric(out["svc_group_n"], errors="coerce")
    missing = [candidate for candidate in BASE_CANDIDATES if candidate not in out.columns]
    if missing:
        raise ValueError(f"Missing base prediction columns: {missing}")
    return out


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    pred = np.asarray(pred_log, dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((pred - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def prediction_frame(frame: pd.DataFrame, candidate: str, pred_log: np.ndarray, method: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "method": method,
        "scope": "warm",
        "split": frame["split"],
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["actual_log"],
        "pred_log": pred_log,
        "actual_price": frame["actual_price"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
        "artist_key": frame["artist_key"],
        "artist_name_ko": frame["artist_name_ko"],
        "svc_group_level": frame["svc_group_level"],
        "svc_coverage_tier": frame["svc_coverage_tier"],
        "svc_group_n": frame["svc_group_n"],
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def score_metrics(metrics: dict[str, float], baseline: dict[str, float], objective: str) -> float:
    if objective == "mdape":
        return metrics["MdAPE"]
    if objective == "mape_guarded":
        penalty = max(0.0, metrics["MdAPE"] - baseline["MdAPE"]) * 10.0
        return metrics["MAPE"] + penalty
    if objective == "p95_guarded":
        penalty = max(0.0, metrics["MdAPE"] - baseline["MdAPE"]) * 10.0
        return metrics["p95_APE"] + penalty
    if objective == "balanced":
        return (
            0.40 * metrics["MdAPE"] / baseline["MdAPE"]
            + 0.35 * metrics["MAPE"] / baseline["MAPE"]
            + 0.25 * metrics["p95_APE"] / baseline["p95_APE"]
        )
    raise ValueError(f"Unknown objective: {objective}")


def candidate_metrics(frame: pd.DataFrame, candidates: dict[str, tuple[np.ndarray, str]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate, (pred, method) in candidates.items():
        rows.append({
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": str(frame["split"].iloc[0]),
            **metric_values(frame, pred),
        })
    return pd.DataFrame(rows)


def make_weighted_candidates(frame: pd.DataFrame) -> dict[str, tuple[np.ndarray, str]]:
    out: dict[str, tuple[np.ndarray, str]] = {}
    for candidate in BASE_CANDIDATES:
        out[candidate] = (frame[candidate].to_numpy(dtype=float), "base")
    weights = np.round(np.arange(0.0, 1.0001, 0.05), 2)
    short = {
        "svc_numeric_seed_mean": "svcnum",
        "svc_full_seed_mean": "svcfull",
        "pp_v6_fine_blend_mape_guarded": "ppv6",
        "pp_v8_compact_blend_mape_guarded": "ppv8",
    }
    for svc in SVC_CANDIDATES:
        for pp in PP_CANDIDATES:
            svc_pred = frame[svc].to_numpy(dtype=float)
            pp_pred = frame[pp].to_numpy(dtype=float)
            for weight in weights:
                label = f"blend_{short[svc]}_{short[pp]}_wsvc_{weight:.2f}"
                out[label] = (weight * svc_pred + (1.0 - weight) * pp_pred, "weighted_blend")
    return out


def select_by_segment(
    val: pd.DataFrame,
    test: pd.DataFrame,
    segment_col: str,
    objective: str,
    candidate_pool: list[str],
    baseline_metrics: dict[str, float],
    min_rows: int = 25,
) -> tuple[str, np.ndarray, np.ndarray, dict[str, Any]]:
    global_scores = []
    for candidate in candidate_pool:
        metrics = metric_values(val, val[candidate].to_numpy(dtype=float))
        global_scores.append((score_metrics(metrics, baseline_metrics, objective), candidate, metrics))
    global_scores.sort(key=lambda x: x[0])
    fallback = global_scores[0][1]
    mapping: dict[str, str] = {}
    mapping_metrics: dict[str, Any] = {}
    for segment, group in val.groupby(segment_col, dropna=False):
        if len(group) < min_rows:
            continue
        scores = []
        for candidate in candidate_pool:
            metrics = metric_values(group, group[candidate].to_numpy(dtype=float))
            scores.append((score_metrics(metrics, baseline_metrics, objective), candidate, metrics))
        scores.sort(key=lambda x: x[0])
        mapping[str(segment)] = scores[0][1]
        mapping_metrics[str(segment)] = {"n": int(len(group)), "selected": scores[0][1], **scores[0][2]}

    def apply(frame: pd.DataFrame) -> np.ndarray:
        pred = np.empty(len(frame), dtype=float)
        for idx, row in enumerate(frame.itertuples(index=False)):
            segment = str(getattr(row, segment_col))
            candidate = mapping.get(segment, fallback)
            pred[idx] = getattr(row, candidate)
        return pred

    label = f"route_{segment_col}_{objective}"
    info = {
        "segment_col": segment_col,
        "objective": objective,
        "fallback": fallback,
        "mapping": mapping,
        "mapping_metrics": mapping_metrics,
        "min_rows": min_rows,
    }
    return label, apply(val), apply(test), info


def add_disagreement_bins(wide: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    out = wide.copy()
    thresholds: dict[str, dict[str, float]] = {}
    pairs = [
        ("svc_numeric_seed_mean", "pp_v8_compact_blend_mape_guarded", "disagree_svcnum_ppv8_bin"),
        ("svc_full_seed_mean", "pp_v8_compact_blend_mape_guarded", "disagree_svcfull_ppv8_bin"),
        ("svc_numeric_seed_mean", "pp_v6_fine_blend_mape_guarded", "disagree_svcnum_ppv6_bin"),
    ]
    val_mask = out["split"].eq("validation")
    for left, right, col in pairs:
        diff = np.abs(out[left].astype(float) - out[right].astype(float))
        low, high = np.quantile(diff[val_mask], [0.33, 0.66])
        thresholds[col] = {"low": float(low), "high": float(high), "left": left, "right": right}
        out[col] = np.select(
            [diff <= low, diff <= high, diff > high],
            ["low_disagreement", "mid_disagreement", "high_disagreement"],
            default="__MISSING__",
        )
    return out, thresholds


def select_objectives(metrics: pd.DataFrame) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    ppv6 = val[val["candidate"].eq("pp_v6_fine_blend_mape_guarded")].iloc[0]
    rows: list[dict[str, Any]] = []
    objectives = {
        "mdape_primary": val.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0],
        "mape_guarded": val[val["MdAPE"] <= ppv6.MdAPE].sort_values(["MAPE", "MdAPE", "p95_APE"]).iloc[0],
        "p95_guarded": val[val["MdAPE"] <= ppv6.MdAPE].sort_values(["p95_APE", "MdAPE", "MAPE"]).iloc[0],
    }
    baseline = {"MdAPE": float(ppv6.MdAPE), "MAPE": float(ppv6.MAPE), "p95_APE": float(ppv6.p95_APE)}
    val["balanced_score"] = (
        0.40 * val["MdAPE"] / baseline["MdAPE"]
        + 0.35 * val["MAPE"] / baseline["MAPE"]
        + 0.25 * val["p95_APE"] / baseline["p95_APE"]
    )
    objectives["balanced"] = val.sort_values(["balanced_score", "MdAPE", "MAPE"]).iloc[0]
    for objective, selected in objectives.items():
        rows.append({
            "objective": objective,
            "selected_candidate": selected["candidate"],
            "validation_method": selected["method"],
            "selection_rule": "validation_only",
            "validation_MdAPE": float(selected["MdAPE"]),
            "validation_MAPE": float(selected["MAPE"]),
            "validation_p95_APE": float(selected["p95_APE"]),
        })
    return pd.DataFrame(rows).drop_duplicates(["objective", "selected_candidate"])


def bootstrap_compare(predictions: pd.DataFrame, baseline: str, candidates: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    test = predictions[predictions["split"].eq("test")].copy()
    base = test[["split", "_track6_row_id", "actual_log", "actual_price", "artist_key"]].drop_duplicates(["split", "_track6_row_id"])
    wide = test.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last").reset_index()
    data = base.merge(wide, on="_track6_row_id", how="inner").dropna(subset=[baseline])
    rng = np.random.default_rng(SEED)
    row_indices = np.arange(len(data))
    artist_keys = data["artist_key"].fillna("__MISSING__").astype(str).to_numpy()
    unique_artists = np.unique(artist_keys)
    artist_to_indices = {artist: np.flatnonzero(artist_keys == artist) for artist in unique_artists}
    rows: list[dict[str, Any]] = []
    for iteration in range(BOOTSTRAP_ITERATIONS):
        row_sample = rng.choice(row_indices, size=len(row_indices), replace=True)
        artist_sample_keys = rng.choice(unique_artists, size=len(unique_artists), replace=True)
        artist_sample = np.concatenate([artist_to_indices[artist] for artist in artist_sample_keys])
        for mode, indices in [("row_bootstrap", row_sample), ("artist_bootstrap", artist_sample)]:
            sample = data.iloc[indices].copy()
            for candidate in candidates:
                if candidate == baseline or candidate not in sample.columns:
                    continue
                usable = sample.dropna(subset=[baseline, candidate])
                base_metrics = metric_values(usable, usable[baseline])
                cand_metrics = metric_values(usable, usable[candidate])
                row: dict[str, Any] = {
                    "experiment_id": EXP_ID,
                    "candidate": candidate,
                    "baseline": baseline,
                    "bootstrap_mode": mode,
                    "iteration": iteration,
                    "n": int(len(usable)),
                }
                for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                    row[f"baseline_{metric}"] = base_metrics[metric]
                    row[f"candidate_{metric}"] = cand_metrics[metric]
                    row[f"delta_{metric}"] = base_metrics[metric] - cand_metrics[metric]
                rows.append(row)
    samples = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (candidate, mode), group in samples.groupby(["candidate", "bootstrap_mode"], dropna=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "baseline": baseline,
            "bootstrap_mode": mode,
            "iterations": int(group["iteration"].nunique()),
            "median_n": float(group["n"].median()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            values = group[f"delta_{metric}"].astype(float).to_numpy()
            row[f"delta_{metric}_median"] = float(np.median(values))
            row[f"delta_{metric}_ci_low"] = float(np.quantile(values, 0.025))
            row[f"delta_{metric}_ci_high"] = float(np.quantile(values, 0.975))
            row[f"delta_{metric}_prob_improve"] = float(np.mean(values > 0))
        summary_rows.append(row)
    return samples, pd.DataFrame(summary_rows)


def render_report(
    all_metrics: pd.DataFrame,
    selected: pd.DataFrame,
    selected_metrics: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
) -> tuple[str, str]:
    val_top = all_metrics[all_metrics["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(20)
    test_selected = selected_metrics[selected_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: Warm 비교군 통계 후보와 기존 Warm 후보를 결합해 MdAPE와 MAPE 균형이 좋아지는지 확인한다.",
        "- 원칙: 가중치와 라우팅 기준은 validation에서만 선택하고 test는 선택 후 확인으로 사용한다.",
        "",
        "## 1. Validation 상위 후보",
        "",
        "| 후보 | method | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in val_top.itertuples():
        lines.append(f"| `{row.candidate}` | {row.method} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")
    lines += ["", "## 2. Validation 선택 후보", "", "| objective | selected | val MdAPE | val MAPE | val p95 |", "|---|---|---:|---:|---:|"]
    for row in selected.itertuples():
        lines.append(f"| {row.objective} | `{row.selected_candidate}` | {row.validation_MdAPE:.4f} | {row.validation_MAPE:.4f} | {row.validation_p95_APE:.4f} |")
    lines += ["", "## 3. 선택 후보 test 결과", "", "| 후보 | method | MdAPE | MAPE | p95_APE | RMSE_log |", "|---|---|---:|---:|---:|---:|"]
    for row in test_selected.itertuples():
        lines.append(f"| `{row.candidate}` | {row.method} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")
    lines += ["", "## 4. PP-V6 대비 bootstrap", "", "| 후보 | mode | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | MdAPE delta 중앙값 |", "|---|---|---:|---:|---:|---:|"]
    for row in bootstrap_summary.itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.bootstrap_mode} | {row.delta_MdAPE_prob_improve:.3f} | "
            f"{row.delta_MAPE_prob_improve:.3f} | {row.delta_p95_APE_prob_improve:.3f} | {row.delta_MdAPE_median:.4f} |"
        )
    lines += [
        "",
        "## 5. 해석 기준",
        "",
        "- validation과 test가 같은 후보를 지지하면 운영 후보로 올린다.",
        "- validation 선택 후보가 test에서 기존 `PP-V6/PP-V8`보다 약하면, 결합 정책은 과적합 가능성이 있으므로 보류한다.",
        "- MdAPE와 MAPE가 서로 반대로 움직이면 단일 후보가 아니라 목적별 응답 정책으로 분리한다.",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<h2>Selected Candidates</h2>{selected_metrics.to_html(index=False, escape=True)}
<h2>All Metrics</h2>{all_metrics.to_html(index=False, escape=True)}
<h2>Bootstrap Summary</h2>{bootstrap_summary.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    wide = load_wide_predictions()
    wide, thresholds = add_disagreement_bins(wide)
    val = wide[wide["split"].eq("validation")].copy()
    test = wide[wide["split"].eq("test")].copy()
    val_candidates = make_weighted_candidates(val)
    test_candidates = make_weighted_candidates(test)
    route_infos: dict[str, Any] = {}
    baseline_metrics = metric_values(val, val["pp_v6_fine_blend_mape_guarded"].to_numpy(dtype=float))
    route_cols = ["svc_group_level", "svc_coverage_tier", "disagree_svcnum_ppv8_bin", "disagree_svcfull_ppv8_bin", "disagree_svcnum_ppv6_bin"]
    objectives = ["mdape", "mape_guarded", "p95_guarded", "balanced"]
    for col in route_cols:
        for objective in objectives:
            label, val_pred, test_pred, info = select_by_segment(val, test, col, objective, BASE_CANDIDATES, baseline_metrics)
            route_infos[label] = info
            val_candidates[label] = (val_pred, "segment_route")
            test_candidates[label] = (test_pred, "segment_route")

    val_metrics = candidate_metrics(val, val_candidates)
    test_metrics = candidate_metrics(test, test_candidates)
    all_metrics = pd.concat([val_metrics, test_metrics], ignore_index=True)
    selected = select_objectives(all_metrics)
    selected_names = list(dict.fromkeys([
        *BASE_CANDIDATES,
        *selected["selected_candidate"].tolist(),
    ]))
    selected_metrics = all_metrics[all_metrics["candidate"].isin(selected_names)].copy()

    pred_frames: list[pd.DataFrame] = []
    for split_frame, candidates in [(val, val_candidates), (test, test_candidates)]:
        for candidate in selected_names:
            pred, method = candidates[candidate]
            pred_frames.append(prediction_frame(split_frame, candidate, pred, method))
    predictions = pd.concat(pred_frames, ignore_index=True)
    bootstrap_samples, bootstrap_summary = bootstrap_compare(
        predictions,
        "pp_v6_fine_blend_mape_guarded",
        [c for c in selected_names if c != "pp_v6_fine_blend_mape_guarded"],
    )

    all_metrics.to_csv(EXP_DIR / "outputs" / "all_candidate_metrics.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    selected_metrics.to_csv(EXP_DIR / "outputs" / "selected_candidate_metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    bootstrap_samples.to_csv(EXP_DIR / "outputs" / "bootstrap_samples.csv", index=False)
    bootstrap_summary.to_csv(EXP_DIR / "outputs" / "bootstrap_summary.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(REPO)),
        "base_candidates": BASE_CANDIDATES,
        "weight_grid": [round(float(x), 2) for x in np.arange(0.0, 1.0001, 0.05)],
        "disagreement_thresholds": thresholds,
        "route_infos": route_infos,
        "selection_rule": "validation_only",
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "artifacts" / "route_policy.json").write_text(json.dumps(route_infos, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(all_metrics, selected, selected_metrics, bootstrap_summary)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_svc3_warm_svc_blend_routing_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "summary_doc": str((DOC_ROOT / "pp_svc3_warm_svc_blend_routing_summary.md").relative_to(REPO)),
        "selected": selected.to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
