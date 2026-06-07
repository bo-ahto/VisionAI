#!/usr/bin/env python3
"""Run Warm gap follow-up experiments PP-V6~PP-V8.

PP-V6/PP-V7 refresh the existing PP-V Warm blend/meta structure by adding
the strongest PP-L10 sequential candidates as extra components.

PP-V8 checks whether a smaller deployment policy can keep most of the final
Warm performance with fewer candidate predictions.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_v_experiments as ppv  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402


EXPERIMENTS = {
    "PP-V6": {"slug": "PP-V6_warm_l10_refreshed_fine_blend", "title": "Warm PP-L10 반영 fine blend"},
    "PP-V7": {"slug": "PP-V7_warm_l10_refreshed_meta_stacking", "title": "Warm PP-L10 반영 meta stacking"},
    "PP-V8": {"slug": "PP-V8_warm_deployment_simplification", "title": "Warm 배포 단순화 후보 검증"},
}

L10_SOURCES = [
    (
        "l10_meta_external_search_seq",
        "PP-L10_warm_l8_feature_variant_sequential",
        "l8_seq__warm_base_meta_external_search_all",
        None,
    ),
    (
        "l10_generated_bucket_seq",
        "PP-L10_warm_l8_feature_variant_sequential",
        "l8_seq__full_plus_generated_buckets",
        None,
    ),
]

REFRESHED_WARM_SOURCES = [*ppv.WARM_SOURCES, *L10_SOURCES]

V8_SOURCES = [
    ("v1_representative", "PP-V1_warm_ppu_feature_augmented_fine_blend", "fine_blend_mape_guarded", None),
    ("v2_defensive", "PP-V2_warm_ppu_feature_augmented_meta_stacking", "huber_component_range_clipped", None),
    ("l10_generated_bucket_seq", "PP-L10_warm_l8_feature_variant_sequential", "l8_seq__full_plus_generated_buckets", None),
    ("l10_meta_external_search_seq", "PP-L10_warm_l8_feature_variant_sequential", "l8_seq__warm_base_meta_external_search_all", None),
]


def sync_experiments() -> None:
    ppv.EXPERIMENTS.update(EXPERIMENTS)


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["_track6_row_id", "actual_log", "actual_price"]].rename(
        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
    )


def add_metric(
    rows: list[dict[str, Any]],
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "policy": policy,
        **metrics(metric_frame(frame), pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def prediction_frame(
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["actual_log"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": frame["actual_price"].to_numpy(dtype=float),
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def run_deployment_simplification() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = ppv.merge_sources(V8_SOURCES, "warm", "validation")
    test = ppv.merge_sources(V8_SOURCES, "warm", "test")
    labels = [label for label, *_ in V8_SOURCES]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []

    for split, frame in [("validation", val), ("test", test)]:
        for label in labels:
            add_metric(rows, "PP-V8", f"component_{label}", split, frame, frame[label].to_numpy(dtype=float), "deployment_component")

    val_metrics = {label: metrics(metric_frame(val), val[label].to_numpy(dtype=float)) for label in labels}
    best_mdape = min(score["MdAPE"] for score in val_metrics.values())
    policies = {
        "single_mdape": lambda label: val_metrics[label]["MdAPE"],
        "single_mape_guarded": lambda label: val_metrics[label]["MAPE"] if val_metrics[label]["MdAPE"] <= best_mdape * 1.08 else np.inf,
        "single_p95_guarded": lambda label: val_metrics[label]["p95_APE"] if val_metrics[label]["MdAPE"] <= best_mdape * 1.10 else np.inf,
    }

    for policy, scorer in policies.items():
        selected = min(labels, key=scorer)
        maps.append({
            "experiment_id": "PP-V8",
            "policy": policy,
            "selected_label": selected,
            **{f"validation_{k}": v for k, v in val_metrics[selected].items()},
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred = frame[selected].to_numpy(dtype=float)
            candidate = f"deployment_{policy}"
            add_metric(rows, "PP-V8", candidate, split, frame, pred, "deployment_simplification", {"selected_source": selected})
            preds.append(prediction_frame("PP-V8", candidate, split, frame, pred, "deployment_simplification", {
                "selected_source": selected,
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
            }))

    for objective in ["mdape", "mape_guarded", "p95_guarded"]:
        weights, selected_metrics = ppv.best_blend(val, labels, objective, step=0.25, mdape_guard=1.08)
        maps.append({
            "experiment_id": "PP-V8",
            "policy": f"compact_blend_{objective}",
            "step": 0.25,
            **{f"weight_{label}": weight for label, weight in zip(labels, weights, strict=True)},
            **{f"validation_{k}": v for k, v in selected_metrics.items()},
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred = ppv.blend_prediction(frame, labels, weights)
            candidate = f"compact_blend_{objective}"
            add_metric(rows, "PP-V8", candidate, split, frame, pred, "deployment_simplification")
            preds.append(prediction_frame("PP-V8", candidate, split, frame, pred, "deployment_simplification", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
            }))

    return rows, preds, maps


def main() -> None:
    start = time.time()
    sync_experiments()
    runners = {
        "PP-V6": lambda: ppv.run_fine_blend("PP-V6", "warm", REFRESHED_WARM_SOURCES, step=0.10, mdape_guard=1.08),
        "PP-V7": lambda: ppv.run_meta_stacking("PP-V7", "warm", REFRESHED_WARM_SOURCES, base_col="r5_p95"),
        "PP-V8": run_deployment_simplification,
    }
    summary_frames: list[pd.DataFrame] = []
    for exp_id in ["PP-V6", "PP-V7", "PP-V8"]:
        rows, preds, maps = runners[exp_id]()
        ppv.write_exp(exp_id, rows, preds, maps)
        df = pd.DataFrame(rows)
        df["folder"] = str((BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]).relative_to(REPO))
        summary_frames.append(df)
    summary = pd.concat(summary_frames, ignore_index=True)
    summary_path = BASE_EXP_DIR / "PP-V6_V8_warm_gap_summary_metrics.csv"
    summary.to_csv(summary_path, index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": str(summary_path.relative_to(REPO)),
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
