#!/usr/bin/env python3
"""Build unified Track6 experiment metric tables.

This script collects each experiment folder's representative result CSV and
normalizes it into one long table. It intentionally ignores rerun/archive CSVs
so the integrated view does not double count the same experiment.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pandas as pd


ROOT = Path("experiments/track6")
OUT_DIR = Path("docs/track6/experiments")


STANDARD_COLUMNS = [
    "experiment_id",
    "experiment_dir",
    "group_label",
    "feature_block",
    "features",
    "scope",
    "model_code",
    "model_name",
    "n_train",
    "n_test",
    "R2",
    "RMSE_log",
    "MdAPE",
    "p95_APE",
    "Within_30",
    "Within_50",
    "MAPE",
    "source_csv",
]


def group_label(experiment_id: Any, experiment_dir: str) -> str:
    text = str(experiment_id or "") or experiment_dir
    match = re.match(r"^([A-J])(?:\d|-)", text)
    if match:
        return f"Group {match.group(1)}"
    if text.startswith("OPT-W") or experiment_dir.startswith("OPT-W"):
        return "OPT-Warm"
    if text.startswith("OPT-C") or experiment_dir.startswith("OPT-C"):
        return "OPT-Cold"
    if text.startswith("WM") or experiment_dir.startswith("WM"):
        return "Warm Model Compare"
    if text.startswith("CM") or experiment_dir.startswith("CM"):
        return "Cold Model Compare"
    if text.startswith("T6-") or experiment_dir.startswith("T6-"):
        return "Legacy T6"
    return "Other"


def pick_result_csv(exp_dir: Path) -> Path | None:
    output_dir = exp_dir / "outputs"
    if not output_dir.exists():
        return None
    if exp_dir.name.startswith(("WM", "CM")):
        scored = output_dir / "result_sheet_scored.csv"
        if scored.exists():
            return scored
    for name in ["metrics_long.csv", "result_sheet.csv", "metrics.csv"]:
        path = output_dir / name
        if path.exists():
            return path
    return None


def normalize_long(path: Path, exp_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.copy()
    rename = {
        "variable_block": "feature_block",
        "feature_set": "feature_block",
        "variant": "feature_block",
        "test_name": "scope",
        "model": "model_name",
        "median_ape": "MdAPE",
        "p95_ape": "p95_APE",
        "within_30": "Within_30",
        "within_50": "Within_50",
        "mape": "MAPE",
        "rmse_log": "RMSE_log",
        "n": "n_test",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    if "experiment_id" not in df.columns:
        df["experiment_id"] = exp_dir.name.split("_", 1)[0]
    if "features" not in df.columns:
        cat = df["cat_features"].fillna("") if "cat_features" in df.columns else ""
        num = df["num_features"].fillna("") if "num_features" in df.columns else ""
        if isinstance(cat, str) and isinstance(num, str):
            df["features"] = ""
        else:
            df["features"] = (cat.astype(str) + ", " + num.astype(str)).str.strip(", ")
    if "feature_block" not in df.columns:
        df["feature_block"] = ""
    if "scope" not in df.columns:
        df["scope"] = ""
    if "model_code" not in df.columns:
        df["model_code"] = ""
    if "model_name" not in df.columns:
        df["model_name"] = ""
    if "n_train" not in df.columns:
        df["n_train"] = pd.NA
    if "R2" not in df.columns:
        df["R2"] = pd.NA
    if "RMSE_log" not in df.columns:
        df["RMSE_log"] = pd.NA
    if "Within_50" not in df.columns:
        df["Within_50"] = pd.NA
    if "MAPE" not in df.columns:
        df["MAPE"] = pd.NA

    df["experiment_dir"] = exp_dir.name
    df["group_label"] = [
        group_label(eid, exp_dir.name) for eid in df["experiment_id"].tolist()
    ]
    if df["scope"].isna().all() or (df["scope"].astype(str).str.strip() == "").all():
        if exp_dir.name.startswith("WM") or exp_dir.name.startswith("OPT-W"):
            df["scope"] = "Warm"
        elif exp_dir.name.startswith("CM") or exp_dir.name.startswith("OPT-C"):
            df["scope"] = "Cold"
    df["source_csv"] = str(path)

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    return df[STANDARD_COLUMNS]


def rank_for_selection(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["MdAPE_sort"] = pd.to_numeric(out["MdAPE"], errors="coerce")
    out["p95_APE_sort"] = pd.to_numeric(out["p95_APE"], errors="coerce")
    out["Within_30_sort"] = pd.to_numeric(out["Within_30"], errors="coerce")
    out["RMSE_log_sort"] = pd.to_numeric(out["RMSE_log"], errors="coerce")
    out["R2_sort"] = pd.to_numeric(out["R2"], errors="coerce")
    out = out.sort_values(
        ["MdAPE_sort", "p95_APE_sort", "Within_30_sort", "RMSE_log_sort", "R2_sort"],
        ascending=[True, True, False, True, False],
        na_position="last",
    )
    out["rank_in_feature_scope"] = range(1, len(out) + 1)
    return out.drop(
        columns=["MdAPE_sort", "p95_APE_sort", "Within_30_sort", "RMSE_log_sort", "R2_sort"]
    )


def build_best_model_table(long_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["experiment_id", "experiment_dir", "group_label", "feature_block", "features", "scope"]
    for _, group in long_df.groupby(keys, dropna=False):
        ranked = rank_for_selection(group).head(3)
        for _, row in ranked.iterrows():
            rows.append(row.to_dict())
    result = pd.DataFrame(rows)
    keep = [
        "experiment_id",
        "experiment_dir",
        "group_label",
        "feature_block",
        "features",
        "scope",
        "rank_in_feature_scope",
        "model_name",
        "MdAPE",
        "p95_APE",
        "Within_30",
        "Within_50",
        "RMSE_log",
        "R2",
        "MAPE",
        "source_csv",
    ]
    return result[keep].sort_values(
        ["group_label", "experiment_id", "scope", "feature_block", "rank_in_feature_scope"]
    )


def build_pivot_summary(best_df: pd.DataFrame) -> pd.DataFrame:
    top = best_df[best_df["rank_in_feature_scope"] == 1].copy()
    rows = []
    keys = ["experiment_id", "experiment_dir", "group_label", "feature_block", "features"]
    for key, group in top.groupby(keys, dropna=False):
        row = dict(zip(keys, key))
        for scope in ["Warm", "Cold"]:
            g = group[group["scope"].astype(str).str.contains(scope, case=False, na=False)]
            if not g.empty:
                r = g.iloc[0]
                row[f"{scope}_best_model"] = r["model_name"]
                row[f"{scope}_MdAPE"] = r["MdAPE"]
                row[f"{scope}_p95_APE"] = r["p95_APE"]
                row[f"{scope}_Within_30"] = r["Within_30"]
                row[f"{scope}_RMSE_log"] = r["RMSE_log"]
                row[f"{scope}_R2"] = r["R2"]
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["group_label", "experiment_id", "feature_block"])


def build_delta_table(best_df: pd.DataFrame) -> pd.DataFrame:
    """Build within-experiment deltas from each experiment's best block.

    The first row per experiment/scope is the local best. Other feature blocks are
    compared against that local best so reviewers can see what each alternative
    lost or gained inside the same experiment.
    """
    top = best_df[best_df["rank_in_feature_scope"] == 1].copy()
    rows = []
    keys = ["experiment_id", "experiment_dir", "group_label", "scope"]
    for key, group in top.groupby(keys, dropna=False):
        group = group.copy()
        group["MdAPE_num"] = pd.to_numeric(group["MdAPE"], errors="coerce")
        if group["MdAPE_num"].dropna().empty:
            continue
        baseline = group.sort_values("MdAPE_num").iloc[0]
        for _, row in group.iterrows():
            base = float(baseline["MdAPE_num"])
            cand = float(row["MdAPE_num"])
            rows.append(
                {
                    "experiment_id": key[0],
                    "experiment_dir": key[1],
                    "group_label": key[2],
                    "scope": key[3],
                    "best_feature_block": baseline["feature_block"],
                    "best_model": baseline["model_name"],
                    "best_MdAPE": base,
                    "candidate_feature_block": row["feature_block"],
                    "candidate_model": row["model_name"],
                    "candidate_MdAPE": cand,
                    "MdAPE_gap_vs_best": cand - base,
                    "MdAPE_gap_pct_vs_best": (cand - base) / base * 100 if base else pd.NA,
                    "candidate_p95_APE": row["p95_APE"],
                    "candidate_Within_30": row["Within_30"],
                    "candidate_RMSE_log": row["RMSE_log"],
                    "candidate_R2": row["R2"],
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["group_label", "experiment_id", "scope", "MdAPE_gap_vs_best"]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    skipped = []
    for exp_dir in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        path = pick_result_csv(exp_dir)
        if path is None:
            skipped.append(str(exp_dir))
            continue
        try:
            frames.append(normalize_long(path, exp_dir))
        except Exception as exc:  # noqa: BLE001
            skipped.append(f"{exp_dir}: {exc}")
    long_df = pd.concat(frames, ignore_index=True)

    numeric_cols = [
        "n_train",
        "n_test",
        "R2",
        "RMSE_log",
        "MdAPE",
        "p95_APE",
        "Within_30",
        "Within_50",
        "MAPE",
    ]
    for col in numeric_cols:
        long_df[col] = pd.to_numeric(long_df[col], errors="coerce")

    long_df.to_csv(OUT_DIR / "track6_all_experiment_model_metrics_long.csv", index=False)

    best_df = build_best_model_table(long_df)
    best_df.to_csv(OUT_DIR / "track6_best_model_by_feature_block.csv", index=False)

    pivot_df = build_pivot_summary(best_df)
    pivot_df.to_csv(OUT_DIR / "track6_feature_model_pivot_summary.csv", index=False)

    delta_df = build_delta_table(best_df)
    delta_df.to_csv(OUT_DIR / "track6_feature_influence_delta.csv", index=False)

    pd.DataFrame({"skipped": skipped}).to_csv(
        OUT_DIR / "track6_unified_metric_skipped_sources.csv", index=False
    )

    print("long rows", len(long_df))
    print("best rows", len(best_df))
    print("pivot rows", len(pivot_df))
    print("delta rows", len(delta_df))
    print("skipped", len(skipped))


if __name__ == "__main__":
    main()
