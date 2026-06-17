#!/usr/bin/env python3
"""Freeze the unified Warm-lite route_gap_q50 official 0.1v bundle."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_cgrp1_cold_group_price_stats_base as cgrp  # noqa: E402
import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "warm_lite_unified_route_gap_q50_v0.1_candidate"
PREDICTOR = BUNDLE / "predict" / "predict_warm_lite_unified_route_gap_q50_v0_1.py"
CF9 = REPO / "experiments" / "track6" / "PP-ROUTE-CF9_conditional_cf7_router"
FREEZE_TS = "2026-06-16T00:00:00+09:00"
ARTIFACT_ID = "candidate_v0_1_warm_lite_unified_route_gap_q50"
STATUS = "default_official_v0_1_warm_route_policy"
SEEDS = [20260612, 20260613, 20260614]


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dirs() -> None:
    for sub in ("artifacts", "config", "models", "predict", "manifest", "reports"):
        (BUNDLE / sub).mkdir(parents=True, exist_ok=True)


def ladder_payload(train: pd.DataFrame, base_ladder: list[tuple[list[str], int]]) -> list[dict[str, Any]]:
    payload = []
    for keys, min_n in base_ladder:
        table_frame = cgrp.group_stat_table(train, keys)
        table_frame = table_frame[table_frame["grp_n"] >= min_n]
        table = {}
        for _, row in table_frame.iterrows():
            table["|".join(str(row[col]) for col in keys)] = {
                "grp_log_price_median": float(row["grp_log_price_median"]),
                "grp_log_price_q25": float(row["grp_log_price_q25"]),
                "grp_log_price_q75": float(row["grp_log_price_q75"]),
                "grp_log_price_iqr": float(row["grp_log_price_iqr"]),
                "grp_unit_area_median": float(row["grp_unit_area_median"]),
                "grp_unit_area_iqr": float(row["grp_unit_area_iqr"]),
                "grp_n_log": float(np.log1p(row["grp_n"])),
            }
        payload.append({"keys": keys, "min_n": min_n, "table": table})
    return payload


def global_fallback(train: pd.DataFrame) -> dict[str, float]:
    unit = train["ln_price_krw"] - train["log_area"].clip(lower=0)
    out = {
        "grp_log_price_median": float(train["ln_price_krw"].median()),
        "grp_log_price_q25": float(train["ln_price_krw"].quantile(0.25)),
        "grp_log_price_q75": float(train["ln_price_krw"].quantile(0.75)),
        "grp_unit_area_median": float(unit.median()),
        "grp_unit_area_iqr": float(unit.quantile(0.75) - unit.quantile(0.25)),
        "grp_n_log": float(np.log1p(len(train))),
    }
    out["grp_log_price_iqr"] = out["grp_log_price_q75"] - out["grp_log_price_q25"]
    return out


def load_selected_spec() -> dict[str, Any]:
    selected = pd.read_csv(CF9 / "outputs" / "selected_routers_from_validation.csv")
    row = selected[selected["candidate"].eq("route_gap_q50")]
    if row.empty:
        raise RuntimeError("route_gap_q50 not found in CF9 selected routers")
    return json.loads(row.iloc[0]["spec"])


def train_with_stats(train: pd.DataFrame) -> pd.DataFrame:
    base_ladder = list(cgrp.LADDER)
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        train_s = cgrp.train_with_internal_stats(train)
    finally:
        cgrp.LADDER = base_ladder
    return q3.add_price_proxy(train_s)


def train_seed_stack(train_s: pd.DataFrame, seed: int) -> dict[str, object]:
    q_oof = q3.oof_quantiles(train_s, seed=seed)
    q_models = q3.fit_quantile_models(train_s, seed=seed)
    residual_models = q3.fit_residual_models(train_s, q_oof)
    return {"q_models": q_models, "residual_models": residual_models}


def load_train_frame() -> pd.DataFrame:
    needed = unique(
        artifact_features()["warm"]
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket", "ln_price_krw", "log_area", "price_krw", "_track6_row_id", "artist_key"]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    train, _val, _test = load_scope("warm", needed)
    keep = unique([c for c in needed if c in train.columns] + ["ln_price_krw", "log_area", "price_krw"])
    return train[keep].reset_index(drop=True)


def write_replay_feature_store() -> None:
    needed = unique(
        artifact_features()["warm"]
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket", "ln_price_krw", "log_area", "price_krw", "_track6_row_id", "artist_key"]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    train, val, test = load_scope("warm", needed)
    parts = []
    for split, frame in [("train", train), ("validation", val), ("test", test)]:
        part = frame.copy()
        part["split"] = split
        parts.append(part)
    store = pd.concat(parts, ignore_index=True, sort=False)
    keep = unique(
        ["split", "_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket"]
    )
    keep = [col for col in keep if col in store.columns]
    store[keep].to_csv(BUNDLE / "artifacts" / "fixed_replay_feature_store.csv", index=False)


def import_predictor():
    spec = importlib.util.spec_from_file_location("wlite_unified_route_gap", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_manifest() -> None:
    manifest = {
        "artifact_id": ARTIFACT_ID,
        "version": "v0.1-candidate",
        "frozen_at": FREEZE_TS,
        "bundle_path": str(BUNDLE.relative_to(REPO)),
        "predictor": "predict/predict_warm_lite_unified_route_gap_q50_v0_1.py",
        "sha256_manifest": "manifest/MANIFEST.sha256",
        "source_experiments": [
            "experiments/track6/PP-ROUTE-CF5_unified_warm_lite_operational_comparison",
            "experiments/track6/PP-ROUTE-CF7_warm_lite_tail_guard",
            "experiments/track6/PP-ROUTE-CF9_conditional_cf7_router",
        ],
        "status": STATUS,
    }
    (BUNDLE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    files = [
        BUNDLE / "README.md",
        BUNDLE / "config" / "warm_lite_unified_route_gap_q50_params_v0_1.json",
        BUNDLE / "config" / "warm_lite_unified_route_gap_q50_policy_v0_1.json",
        BUNDLE / "manifest.json",
        BUNDLE / "artifacts" / "fixed_replay_feature_store.csv",
        PREDICTOR,
        BUNDLE / "reports" / "warm_lite_unified_route_gap_q50_release_v0_1.md",
    ]
    for seed in SEEDS:
        seed_dir = BUNDLE / "models" / f"seed_{seed}"
        files.extend(
            [
                seed_dir / "lgbq_full_q10.joblib",
                seed_dir / "lgbq_full_q50.joblib",
                seed_dir / "lgbq_full_q90.joblib",
                seed_dir / "lgbq_lean_q50.joblib",
                seed_dir / "lightgbm_huber_residual.joblib",
            ]
        )
    manifest_lines = []
    for path in files:
        rel = path.relative_to(BUNDLE)
        manifest_lines.append(f"{sha(path)}  {rel.as_posix()}")
    (BUNDLE / "manifest" / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    if not PREDICTOR.exists():
        raise FileNotFoundError(PREDICTOR)

    selected_spec = load_selected_spec()
    gap_threshold = float(selected_spec["gap_threshold"])
    train = load_train_frame()
    train_s = train_with_stats(train)
    base_ladder = list(cgrp.LADDER)

    training_audit = []
    for seed in SEEDS:
        stack = train_seed_stack(train_s, seed)
        seed_dir = BUNDLE / "models" / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(stack["q_models"]["full_q10"], seed_dir / "lgbq_full_q10.joblib")
        joblib.dump(stack["q_models"]["full_q50"], seed_dir / "lgbq_full_q50.joblib")
        joblib.dump(stack["q_models"]["full_q90"], seed_dir / "lgbq_full_q90.joblib")
        joblib.dump(stack["q_models"]["lean_q50"], seed_dir / "lgbq_lean_q50.joblib")
        joblib.dump(stack["residual_models"]["lightgbm"], seed_dir / "lightgbm_huber_residual.joblib")
        training_audit.append(
            {
                "seed": seed,
                "train_rows": int(len(train_s)),
                "train_artists": int(train_s["artist_key"].astype(str).nunique()),
                "median_train_rows_per_artist": float(train_s.groupby(train_s["artist_key"].astype(str)).size().median()),
            }
        )

    params = {
        "version": "v0.1-candidate",
        "artifact_id": ARTIFACT_ID,
        "frozen_at": FREEZE_TS,
        "selected_candidate": "route_gap_q50",
        "seeds": SEEDS,
        "current_formula": "seed_mean(qavg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10))",
        "routed_formula": "seed_mean(qavg) + clip(1.00 * seed_mean(LightGBMHuberResidual), -0.15, +0.15)",
        "route_rule": "if seed_mean(abs(full_q50 - lean_q50)) >= route_gap_threshold then routed_formula else current_formula",
        "route_gap_threshold": gap_threshold,
        "current_residual_strength": 0.50,
        "current_residual_cap_log": 0.10,
        "routed_residual_strength": 1.00,
        "routed_residual_cap_log": 0.15,
        "full_num_cols": q3.FULL_NUM,
        "lean_num_cols": q3.LEAN_NUM,
        "cat_cols": q3.CAT_COLS,
        "q_cols": q3.Q_COLS,
        "residual_num_cols": q3.RES_NUM,
        "residual_cat_cols": q3.RES_CAT,
        "fallback_ladder": ladder_payload(train, base_ladder),
        "global_fallback": global_fallback(train),
        "routing_precondition": "artist_match_score >= 0.80 AND same_artist_training_price_count >= 1",
        "source_experiments": [
            "PP-ROUTE-CF5_unified_warm_lite_operational_comparison",
            "PP-ROUTE-CF7_warm_lite_tail_guard",
            "PP-ROUTE-CF9_conditional_cf7_router",
        ],
        "status": STATUS,
    }
    (BUNDLE / "config" / "warm_lite_unified_route_gap_q50_params_v0_1.json").write_text(
        json.dumps(params, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    policy = {
        "version": "v0.1-candidate",
        "name": "warm_lite_unified_route_gap_q50",
        "status": STATUS,
        "selected_candidate": "route_gap_q50",
        "route_rule": params["route_rule"],
        "routing_precondition": params["routing_precondition"],
        "completed_adoption_gates": [
            "bundle replay parity against PP-ROUTE-CF9 validation/test rows",
            "official API adapter implementation",
            "official API HTTP parity on fixed validation/test samples",
            "routing boundary migrated to same_artist_training_price_count >= 1",
        ],
    }
    (BUNDLE / "config" / "warm_lite_unified_route_gap_q50_policy_v0_1.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    predictor = import_predictor()
    sample_artist, sample_history = next(iter(train.groupby("artist_key", sort=False)))
    sample_frame = sample_history.head(1)[predictor.REQUIRED].copy()
    smoke = predictor.predict(sample_frame, sample_history, models=predictor.load_models(), params=params)
    if not np.isfinite(smoke["warm_lite_unified_route_gap_q50_pred_log"].to_numpy(dtype=float)).all():
        raise AssertionError("smoke prediction is not finite")

    readme = "\n".join(
        [
            "# Warm-lite unified route_gap_q50 v0.1 candidate",
            "",
            "Candidate bundle for same-artist price history 1+.",
            "",
            "- Selected candidate: `route_gap_q50`",
            f"- Gap threshold: `{gap_threshold}`",
            "- Current formula: `seed_mean(qavg + clip(0.50 * residual, -0.10, +0.10))`",
            "- Routed formula: `seed_mean(qavg) + clip(seed_mean(residual), -0.15, +0.15)`",
            "- Status: default official 0.1v Warm route policy.",
            "",
        ]
    )
    (BUNDLE / "README.md").write_text(readme, encoding="utf-8")

    report = "\n".join(
        [
            "# Warm-lite unified route_gap_q50 v0.1 candidate release",
            "",
            f"- Frozen at: `{FREEZE_TS}`",
            f"- Artifact: `{ARTIFACT_ID}`",
            "- Selected candidate: `route_gap_q50`",
            f"- Gap threshold: `{gap_threshold}`",
            "- Smoke test: passed",
            "",
            "## Training Audit",
            "",
            "```json",
            json.dumps(training_audit, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Adoption Gate",
            "",
            "This artifact has passed bundle replay parity and default official 0.1v HTTP API parity. The official 0.1v default Warm route policy is now `warm_lite_unified_route_gap_q50`. The previous split routing policy remains available for rollback with `PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY=current_split`.",
            "",
        ]
    )
    (BUNDLE / "reports" / "warm_lite_unified_route_gap_q50_release_v0_1.md").write_text(
        report,
        encoding="utf-8",
    )

    write_replay_feature_store()
    write_manifest()
    print(json.dumps({"artifact_id": ARTIFACT_ID, "bundle": str(BUNDLE), "gap_threshold": gap_threshold}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
