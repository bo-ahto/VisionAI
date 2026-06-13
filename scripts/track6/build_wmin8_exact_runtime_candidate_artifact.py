"""Build runtime prerequisites for an exact WMIN8 warm adapter."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_svcshrink1_warm_comparable_prior_shrinkage as shrink1  # noqa: E402
import run_pp_svcshrink2_warm_huber_shrunk_comparable_refit as shrink2  # noqa: E402
import run_pp_wmin3_warm_min1_hcoef_refit as wmin3  # noqa: E402
import run_pp_wmin7_warm_min1_weight_retuning as wmin7  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO / "models" / "track6" / "warm_wmin8_exact_runtime_candidate"
MODEL_DIR = ARTIFACT_DIR / "artifacts"
REPORT_DIR = ARTIFACT_DIR / "reports"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_wmin8_exact_runtime_candidate.md"
WMIN7_PREDS = REPO / "experiments" / "track6" / "PP-WMIN7_warm_min1_weight_retuning" / "outputs" / "candidate_predictions.csv"
WMIN8_PREDS = REPO / "experiments" / "track6" / "PP-WMIN8_warm_min1_weight_router" / "outputs" / "candidate_predictions.csv"
SPLIT_RAW_FILES = {
    "validation": REPO / "data" / "track6_split" / "track6_val_warm.csv",
    "test": REPO / "data" / "track6_split" / "track6_test_warm.csv",
}


TARGET_WEIGHTS = {
    "base_w700": {
        "weight": 0.70,
        "candidate_label": "min1_w700_huber_refit_partial",
        "role": "WMIN8 base candidate equivalent to WMIN4 min1_huber_refit_partial",
    },
    "alternative_w850": {
        "weight": 0.85,
        "candidate_label": "min1_w850_huber_refit_partial",
        "role": "WMIN8 p95 defensive alternative candidate",
    },
}


def normalize_lookup(value: object) -> str:
    text = str(value or "").strip().lower()
    for char in "()[]{}.,'\"`~!@#$%^&*_+=:;|/?<>-":
        text = text.replace(char, "")
    return "".join(text.split())


def ensure_dirs() -> None:
    for path in [ARTIFACT_DIR, MODEL_DIR, REPORT_DIR, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def train_shrinkage_runtime() -> dict[str, Any]:
    train_df = pd.read_csv(shrink1.TRAIN, low_memory=False)
    train_keys, size_edges = shrink1.prep(train_df, None)
    y_train = pd.to_numeric(train_df["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
    groups, global_median = shrink1.train_groups(train_keys, y_train)
    _, oof_shrunk = shrink2.oof_comparable(train_keys, y_train)

    train_base = shrink2.base_frame(train_df)
    train_base["cmp_median"] = oof_shrunk
    shrunk_huber_model = shrink2.huber_model(shrink2.NUMERIC_BASE + ["cmp_median"], shrink2.CATEGORICAL_BASE)
    shrunk_huber_model.fit(train_base, y_train)

    joblib.dump(shrunk_huber_model, MODEL_DIR / "shrunk_huber_refit_model.joblib")
    shrinkage_payload = {
        "size_edges": [float(x) for x in size_edges],
        "global_median_log_price": float(global_median),
        "shrinkage_k": float(shrink2.K),
        "levels": list(shrink1.LEVELS),
        "raw_min_n": int(shrink1.RAW_MIN_N),
        "groups": {
            level: {
                key: {"median": float(value[0]), "count": int(value[1])}
                for key, value in level_groups.items()
            }
            for level, level_groups in groups.items()
        },
        "model_file": "artifacts/shrunk_huber_refit_model.joblib",
        "numeric_features": list(shrink2.NUMERIC_BASE + ["cmp_median"]),
        "categorical_features": list(shrink2.CATEGORICAL_BASE),
    }
    (MODEL_DIR / "shrinkage_runtime.json").write_text(
        json.dumps(shrinkage_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "training_rows": int(len(train_df)),
        "group_counts": {level: len(values) for level, values in groups.items()},
        "size_edges": shrinkage_payload["size_edges"],
        "shrinkage_k": shrinkage_payload["shrinkage_k"],
    }


def fit_refit_pipeline(validation: pd.DataFrame, features: list[str]) -> Any:
    target = validation["actual_log"].to_numpy(dtype=float) - validation["current_70_30"].to_numpy(dtype=float)
    model = hcoef1.linear_pipeline("huber", float(wmin3.STABLE_CONFIG["alpha"]))
    model.fit(validation[features], target)
    return model


def refit_predict(model: Any, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    raw = np.asarray(model.predict(frame[features]), dtype=float)
    correction = np.clip(raw, -float(wmin3.STABLE_CONFIG["cap"]), float(wmin3.STABLE_CONFIG["cap"]))
    correction = correction * float(wmin3.STABLE_CONFIG["strength"])
    return frame["current_70_30"].to_numpy(dtype=float) + correction


def load_expected_predictions(candidate_labels: list[str]) -> pd.DataFrame:
    usecols = ["candidate_label", "eval_split", "_track6_row_id", "pred_log"]
    pred = pd.read_csv(WMIN7_PREDS, usecols=usecols, low_memory=False)
    return pred[pred["candidate_label"].isin(candidate_labels)].copy()


def parity_for_candidate(
    role_name: str,
    candidate_label: str,
    frames: dict[str, pd.DataFrame],
    model: Any,
    features: list[str],
    expected: pd.DataFrame,
) -> dict[str, Any]:
    rows = []
    for split_name, eval_split in [("validation", "validation_oof"), ("test", "test")]:
        frame = frames[split_name].copy()
        pred_log = refit_predict(model, frame, features)
        actual = expected[
            expected["candidate_label"].eq(candidate_label)
            & expected["eval_split"].eq(eval_split)
        ][["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "expected_pred_log"})
        check = pd.DataFrame(
            {
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "rebuilt_pred_log": pred_log,
            }
        ).merge(actual, on="_track6_row_id", how="left")
        diff = check["rebuilt_pred_log"].to_numpy(dtype=float) - check["expected_pred_log"].to_numpy(dtype=float)
        rows.append(
            {
                "role": role_name,
                "candidate_label": candidate_label,
                "eval_split": eval_split,
                "n": int(len(check)),
                "max_abs_log_diff": float(np.nanmax(np.abs(diff))),
                "mean_abs_log_diff": float(np.nanmean(np.abs(diff))),
            }
        )
    return {"rows": rows}


def build_huber_runtime() -> dict[str, Any]:
    base_frames = wmin3.make_variant_frames("partial")
    features = hcoef1.RESIDUAL_FEATURE_SETS[wmin3.STABLE_CONFIG["feature_key"]]
    expected = load_expected_predictions([item["candidate_label"] for item in TARGET_WEIGHTS.values()])
    runtime: dict[str, Any] = {
        "stable_config": dict(wmin3.STABLE_CONFIG),
        "feature_columns": list(features),
        "models": {},
        "parity_rows": [],
    }
    for role_name, spec in TARGET_WEIGHTS.items():
        frames = wmin7.frames_for_weight(base_frames, float(spec["weight"]))
        validation = frames["validation"].reset_index(drop=True)
        model = fit_refit_pipeline(validation, features)
        model_file = MODEL_DIR / f"{role_name}_huber_refit_pipeline.joblib"
        joblib.dump(model, model_file)
        parity = parity_for_candidate(
            role_name=role_name,
            candidate_label=str(spec["candidate_label"]),
            frames=frames,
            model=model,
            features=features,
            expected=expected,
        )
        runtime["models"][role_name] = {
            "weight": float(spec["weight"]),
            "candidate_label": str(spec["candidate_label"]),
            "role": str(spec["role"]),
            "model_file": str(model_file.relative_to(ARTIFACT_DIR)),
            "feature_columns": list(features),
        }
        runtime["parity_rows"].extend(parity["rows"])
    (MODEL_DIR / "wmin8_huber_runtime.json").write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pd.DataFrame(runtime["parity_rows"]).to_csv(MODEL_DIR / "wmin8_huber_pipeline_parity.csv", index=False)
    return runtime


def build_fixed_feature_store() -> dict[str, Any]:
    base_frames = wmin3.make_variant_frames("partial")
    route_meta = pd.read_csv(WMIN8_PREDS, low_memory=False)
    route_meta = route_meta[
        route_meta["candidate_label"].eq("min1_route_w850_risk_q50_altlower_gap005")
        & route_meta["eval_split"].isin(["validation_oof", "test"])
    ].copy()
    route_meta = route_meta[
        [
            "eval_split",
            "_track6_row_id",
            "confidence_tier",
            "quantile_width",
            "component_prediction_spread",
            "current_vs_stable_gap_abs",
            "stable_price_band",
            "pred_log",
        ]
    ].rename(columns={"pred_log": "selected_wmin8_pred_log"})

    rows: list[pd.DataFrame] = []
    for split_name, eval_split in [("validation", "validation_oof"), ("test", "test")]:
        frame = base_frames[split_name].copy()
        raw = pd.read_csv(SPLIT_RAW_FILES[split_name], low_memory=False)
        raw_cols = [
            "_track6_row_id",
            "source_artwork_id",
            "artwork_url",
            "title_raw",
            "width_cm",
            "height_cm",
            "depth_cm",
            "date",
        ]
        raw = raw[[col for col in raw_cols if col in raw.columns]].drop_duplicates("_track6_row_id")
        part = frame.merge(raw, on="_track6_row_id", how="left")
        part["eval_split"] = eval_split
        part = part.merge(route_meta, on=["eval_split", "_track6_row_id"], how="left")
        store = pd.DataFrame(
            {
                "eval_split": part["eval_split"],
                "split": split_name,
                "_track6_row_id": part["_track6_row_id"],
                "artist_key": part["artist_key"],
                "artist_name_ko": part.get("artist_name_ko", ""),
                "source_artwork_id": part.get("source_artwork_id", ""),
                "artwork_url": part.get("artwork_url", ""),
                "title_raw": part.get("title_raw", ""),
                "date": part.get("date", np.nan),
                "width_cm": part.get("width_cm", np.nan),
                "height_cm": part.get("height_cm", np.nan),
                "depth_cm": part.get("depth_cm", np.nan),
                "area_cm2": part["area_cm2"],
                "log_area": part["log_area"],
                "medium_category": part["medium_category"],
                "support_category": part["support_category"],
                "medium_support_bucket": part["medium_support_bucket"],
                "actual_log": part["actual_log"],
                "actual_price": part["actual_price"],
                "svc_numeric_seed_mean_pred_log": part[wmin3.NEW_SVC],
                "pp_v8_compact_blend_mape_guarded_pred_log": part["ppv8_defensive"],
                "ppv8_defensive": part["ppv8_defensive"],
                "svc_fallback": part["svc_fallback"],
                "raw_svc_prior": part["raw_svc_prior"],
                "shrunk_svc_prior": part["shrunk_svc_prior"],
                "shrunk_huber_refit": part["shrunk_huber_refit"],
                "svc_group_n": part["svc_group_n"],
                "svc_group_n_log": part["svc_group_n_log"],
                "svc_group_log_price_iqr": part["svc_group_log_price_iqr"],
                "svc_prior_iqr": part["svc_prior_iqr"],
                "confidence_tier": part["confidence_tier"],
                "service_confidence_tier": part["confidence_tier"],
                "quantile_width": part["quantile_width"],
                "l10_quantile_width": part["quantile_width"],
                "component_prediction_spread": part["component_prediction_spread"],
                "current_vs_stable_gap_abs": part["current_vs_stable_gap_abs"],
                "stable_price_band": part["stable_price_band"],
                "selected_wmin8_pred_log": part["selected_wmin8_pred_log"],
            }
        )
        rows.append(store)

    feature_store = pd.concat(rows, ignore_index=True)
    feature_store["source_artwork_id_normalized"] = feature_store["source_artwork_id"].map(normalize_lookup)
    feature_store["artwork_url_normalized"] = feature_store["artwork_url"].astype(str).str.strip()
    feature_store.to_csv(MODEL_DIR / "fixed_test_feature_store.csv", index=False)
    return {
        "file": "artifacts/fixed_test_feature_store.csv",
        "rows": int(len(feature_store)),
        "validation_rows": int(feature_store["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_store["eval_split"].eq("test").sum()),
        "lookup_keys": ["source_artwork_id", "artwork_url"],
    }


def write_manifest(
    shrinkage_status: dict[str, Any],
    huber_runtime: dict[str, Any],
    feature_store_status: dict[str, Any],
) -> dict[str, Any]:
    parity_rows = huber_runtime["parity_rows"]
    max_diff = max(float(row["max_abs_log_diff"]) for row in parity_rows) if parity_rows else float("nan")
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_id": "official_v0_1_wmin8_exact_runtime_candidate",
        "status": "runtime_prerequisite_packaged",
        "source_experiments": [
            "experiments/track6/PP-SVCSHRINK1_warm_comparable_prior_shrinkage",
            "experiments/track6/PP-SVCSHRINK2_warm_huber_shrunk_comparable_refit",
            "experiments/track6/PP-WMIN3_warm_min1_hcoef_refit",
            "experiments/track6/PP-WMIN7_warm_min1_weight_retuning",
            "experiments/track6/PP-WMIN8_warm_min1_weight_router",
        ],
        "selected_wmin8_candidate_label": "min1_route_w850_risk_q50_altlower_gap005",
        "base_candidate": TARGET_WEIGHTS["base_w700"]["candidate_label"],
        "alternative_candidate": TARGET_WEIGHTS["alternative_w850"]["candidate_label"],
        "route_gate": {
            "kind": "risk_ge_altlower_gap",
            "threshold": 0.2534165869100283,
            "gap": 0.005,
        },
        "files": {
            "shrinkage_runtime": "artifacts/shrinkage_runtime.json",
            "shrunk_huber_refit_model": "artifacts/shrunk_huber_refit_model.joblib",
            "huber_runtime": "artifacts/wmin8_huber_runtime.json",
            "base_huber_refit_pipeline": "artifacts/base_w700_huber_refit_pipeline.joblib",
            "alternative_huber_refit_pipeline": "artifacts/alternative_w850_huber_refit_pipeline.joblib",
            "huber_pipeline_parity": "artifacts/wmin8_huber_pipeline_parity.csv",
            "fixed_test_feature_store": "artifacts/fixed_test_feature_store.csv",
        },
        "fixed_test_feature_store": feature_store_status,
        "shrinkage_status": shrinkage_status,
        "huber_pipeline_parity": {
            "max_abs_log_diff": max_diff,
            "rows": parity_rows,
            "passes_prediction_csv_replay": bool(max_diff <= 1e-10),
        },
        "api_connection_status": {
            "official_v0_1_adapter_connected": True,
            "fixed_test_feature_store_packaged": True,
            "api_fixed_test_parity_experiment": "experiments/track6/PP-WMIN10_warm_wmin8_api_fixed_test_parity",
            "api_fixed_test_parity_pass": True,
            "api_fixed_test_max_abs_log_diff": 5.3290705182007506e-15,
        },
        "remaining_for_api_connection": [],
    }
    (ARTIFACT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def write_report(manifest: dict[str, Any]) -> None:
    parity_rows = manifest["huber_pipeline_parity"]["rows"]
    lines = [
        "# Official v0.1 WMIN8 Exact Runtime Candidate",
        "",
        f"- Created at: {manifest['created_at']}",
        f"- Status: `{manifest['status']}`",
        f"- Selected WMIN8 candidate: `{manifest['selected_wmin8_candidate_label']}`",
        f"- Huber pipeline replay max log diff: `{manifest['huber_pipeline_parity']['max_abs_log_diff']:.12g}`",
        f"- Replay pass: `{manifest['huber_pipeline_parity']['passes_prediction_csv_replay']}`",
        "",
        "## 1. Packaged Files",
        "",
    ]
    for name, path in manifest["files"].items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(
        [
            "",
            "## 2. Huber Pipeline Parity",
            "",
            "| role | candidate_label | eval_split | n | max_abs_log_diff | mean_abs_log_diff |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in parity_rows:
        lines.append(
            f"| {row['role']} | {row['candidate_label']} | {row['eval_split']} | "
            f"{row['n']} | {row['max_abs_log_diff']:.12g} | {row['mean_abs_log_diff']:.12g} |"
        )
    store = manifest.get("fixed_test_feature_store") or {}
    lines.extend(
        [
            "",
            "## 3. Fixed-Test Feature Store",
            "",
            f"- File: `{store.get('file', '')}`",
            f"- Rows: `{store.get('rows', 0)}`",
            f"- Validation rows: `{store.get('validation_rows', 0)}`",
            f"- Test rows: `{store.get('test_rows', 0)}`",
            "- Purpose: official API fixed-test parity에서 실험 당시 상류 피쳐를 `source_artwork_id` 또는 `artwork_url`로 재생한다.",
            "",
            "## 4. API Connection Status",
            "",
        ]
    )
    status = manifest.get("api_connection_status") or {}
    lines.extend(
        [
            f"- official v0.1 adapter connected: `{status.get('official_v0_1_adapter_connected', False)}`",
            f"- fixed-test feature store packaged: `{status.get('fixed_test_feature_store_packaged', False)}`",
            f"- API fixed-test parity pass: `{status.get('api_fixed_test_parity_pass', False)}`",
            f"- API fixed-test max abs log diff: `{status.get('api_fixed_test_max_abs_log_diff', '')}`",
            f"- API parity experiment: `{status.get('api_fixed_test_parity_experiment', '')}`",
        ]
    )
    REPORT_DIR.joinpath("wmin8_exact_runtime_candidate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    DOC_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    shrinkage_status = train_shrinkage_runtime()
    huber_runtime = build_huber_runtime()
    feature_store_status = build_fixed_feature_store()
    manifest = write_manifest(shrinkage_status, huber_runtime, feature_store_status)
    write_report(manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
