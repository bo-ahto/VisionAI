#!/usr/bin/env python3
"""Freeze Warm-lite Quantile residual v0.1 bundle for the official v0.1 API."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_q3_spec = importlib.util.spec_from_file_location(
    "wlite_q3", SCRIPT_DIR / "run_pp_wlite_q3_quantile_residual_correction_validation.py"
)
q3 = importlib.util.module_from_spec(_q3_spec)
_q3_spec.loader.exec_module(q3)


REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "warm_lite_quantile_residual_v0.1"
PREDICTOR = BUNDLE / "predict" / "predict_warm_lite_quantile_residual_v0_1.py"
FREEZE_TS = "2026-06-15T00:00:00+09:00"
ARTIFACT_ID = "official_v0_1_warm_lite_quantile_residual"
SELECTED_CANDIDATE = "qavg_lgbres_s05_cap010"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dirs() -> None:
    for sub in ("config", "models", "predict", "manifest", "reports"):
        (BUNDLE / sub).mkdir(parents=True, exist_ok=True)


def ladder_payload(train: pd.DataFrame, base_ladder: list[tuple[list[str], int]]) -> list[dict]:
    payload = []
    for keys, min_n in base_ladder:
        table_frame = q3.cgrp.group_stat_table(train, keys)
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


def load_q4_summary() -> dict:
    path = REPO / "experiments" / "track6" / "PP-WLITE-Q4_quantile_final_comparison" / "artifacts" / "run_config.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("recommendation", {})


def import_predictor():
    spec = importlib.util.spec_from_file_location("wlite_qres", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ensure_dirs()
    if not PREDICTOR.exists():
        raise FileNotFoundError(PREDICTOR)

    feats = artifact_features()["cold_lightgbm"]
    need = list(
        dict.fromkeys(
            feats
            + [
                "medium_support_bucket",
                "ln_price_krw",
                "log_area",
                "price_krw",
                "artist_key",
            ]
        )
    )
    train, _, _ = load_scope("warm", feats + ["medium_support_bucket"])
    train = train[need].reset_index(drop=True)
    base_ladder = list(q3.cgrp.LADDER)

    q3.cgrp.LADDER = q3.LITE_LADDER + base_ladder
    train_s = q3.cgrp.train_with_internal_stats(train)
    q3.cgrp.LADDER = base_ladder

    stack = q3.train_stack(train_s)
    q_models = stack["q_models"]
    residual_model = stack["residual_models"]["lightgbm"]

    joblib.dump(q_models["full_q10"], BUNDLE / "models" / "lgbq_full_q10.joblib")
    joblib.dump(q_models["full_q50"], BUNDLE / "models" / "lgbq_full_q50.joblib")
    joblib.dump(q_models["full_q90"], BUNDLE / "models" / "lgbq_full_q90.joblib")
    joblib.dump(q_models["lean_q50"], BUNDLE / "models" / "lgbq_lean_q50.joblib")
    joblib.dump(residual_model, BUNDLE / "models" / "lightgbm_huber_residual.joblib")

    q4 = load_q4_summary()
    params = {
        "version": "v0.1",
        "artifact_id": ARTIFACT_ID,
        "frozen_at": FREEZE_TS,
        "selected_candidate": SELECTED_CANDIDATE,
        "candidate_formula": "lgbq_full_lean_avg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10)",
        "model_seed": q3.MODEL_SEED,
        "full_num_cols": q3.FULL_NUM,
        "lean_num_cols": q3.LEAN_NUM,
        "cat_cols": q3.CAT_COLS,
        "q_cols": q3.Q_COLS,
        "residual_num_cols": q3.RES_NUM,
        "residual_cat_cols": q3.RES_CAT,
        "residual_strength": 0.50,
        "residual_cap_log": 0.10,
        "ladder": ladder_payload(train, base_ladder),
        "global_fallback": global_fallback(train),
        "routing_precondition": "artist_match_score >= 0.80 AND same_artist_training_price_count 1~4",
        "evidence": [
            "PP-WLITE-Q1_warm_lite_quantile_candidate_validation",
            "PP-WLITE-Q2_quantile_followup_truncation_validation",
            "PP-WLITE-Q3_quantile_residual_correction_validation",
            "PP-WLITE-Q4_quantile_final_comparison",
        ],
        "q4_recommendation": q4,
        "prohibitions": ["0604 사용 금지", "매칭 미검증 작가 적용 금지"],
    }
    (BUNDLE / "config" / "warm_lite_quantile_residual_params_v0_1.json").write_text(
        json.dumps(params, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    policy = {
        "version": "v0.1",
        "name": "warm_lite_quantile_residual_v0.1",
        "status": "adopted_after_api_bundle_freeze",
        "selected_candidate": SELECTED_CANDIDATE,
        "candidate_formula": params["candidate_formula"],
        "q4_summary": q4,
        "route_rule": params["routing_precondition"],
        "display_policy": {
            "k1": "warm_lite_low, wide_range_with_review_flag",
            "k2_to_k4": "warm_lite_standard, point_estimate_with_standard_range",
        },
        "requires": ["bundle replay parity", "official v0.1 HTTP API parity"],
    }
    (BUNDLE / "config" / "warm_lite_quantile_residual_policy_v0_1.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    predictor = import_predictor()
    sample_artist, sample_history = next(iter(train.groupby("artist_key", sort=False)))
    sample_history = sample_history.head(min(4, len(sample_history))).copy()
    sample_frame = sample_history.head(1)[predictor.REQUIRED].copy()
    smoke = predictor.predict(sample_frame, sample_history, models=predictor.load_models(), params=params)
    if not np.isfinite(smoke["warm_lite_pred_log"].to_numpy(dtype=float)).all():
        raise AssertionError("warm_lite_quantile_residual smoke prediction is not finite")

    readme = "\n".join(
        [
            "# Warm-lite Quantile residual v0.1",
            "",
            "Official v0.1 API Warm-lite route bundle for same-artist price history 1~4.",
            "",
            f"- Selected candidate: `{SELECTED_CANDIDATE}`",
            "- Formula: `lgbq_full_lean_avg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10)`",
            "- Freeze script: `python3 scripts/track6/freeze_warm_lite_quantile_residual_artifact_v0_1.py`",
            "- Predictor: `predict/predict_warm_lite_quantile_residual_v0_1.py`",
            "",
        ]
    )
    (BUNDLE / "README.md").write_text(readme, encoding="utf-8")
    report = "\n".join(
        [
            "# Warm-lite Quantile residual v0.1 release",
            "",
            f"- Frozen at: `{FREEZE_TS}`",
            f"- Artifact: `{ARTIFACT_ID}`",
            f"- Selected candidate: `{SELECTED_CANDIDATE}`",
            f"- Formula: `{params['candidate_formula']}`",
            "- Evidence: PP-WLITE-Q1/Q2/Q3/Q4",
            "- Smoke test: passed",
            "",
            "## Q4 Recommendation",
            "",
            "```json",
            json.dumps(q4, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    (BUNDLE / "reports" / "warm_lite_quantile_residual_release_v0_1.md").write_text(report, encoding="utf-8")

    files = sorted(path for path in BUNDLE.rglob("*") if path.is_file() and "manifest" not in path.parts)
    (BUNDLE / "manifest" / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha(path)}  {path.relative_to(BUNDLE)}" for path in files) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "artifact_id": ARTIFACT_ID,
        "version": "v0.1",
        "frozen_at": FREEZE_TS,
        "selected_candidate": SELECTED_CANDIDATE,
        "candidate_formula": params["candidate_formula"],
        "bundle_path": str(BUNDLE.relative_to(REPO)),
        "files": {
            "params": "config/warm_lite_quantile_residual_params_v0_1.json",
            "policy": "config/warm_lite_quantile_residual_policy_v0_1.json",
            "predictor": "predict/predict_warm_lite_quantile_residual_v0_1.py",
            "manifest_sha256": "manifest/MANIFEST.sha256",
        },
        "q4_recommendation": q4,
        "smoke_prediction_log": float(smoke["warm_lite_pred_log"].iloc[0]),
        "smoke_prediction_price_krw": float(smoke["warm_lite_pred_price_krw"].iloc[0]),
    }
    (BUNDLE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
