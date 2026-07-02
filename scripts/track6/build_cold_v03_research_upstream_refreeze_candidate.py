#!/usr/bin/env python3
"""Build a Cold v0.3 research-upstream refreeze candidate.

The selected Cold research path is:

PP-Y2 search/external LightGBM quantile -> PP-Y16 fixed segment correction ->
PP-Y18 stability selection -> v0.3 guard + frozen search delta.

This script serializes the model parts that can be reconstructed from existing
training code and measures parity against the fixed validation/test artifacts.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO / "scripts" / "track6"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

YCOMBO_SCRIPT = SCRIPT_DIR / "run_pp_y_cold_combination_experiments.py"
QR1_SCRIPT = SCRIPT_DIR / "run_pp_qr1_cold_quantile_regression_alpha_grid.py"
Y16_SCRIPT = SCRIPT_DIR / "run_pp_y15_oof_fixed_revalidation.py"
V03_POSTPROCESSOR = REPO / "models" / "track6" / "cold_prediction_v0.3" / "predict" / "apply_cold_postprocess_v0_3.py"

PP_Y2_PRED = REPO / "experiments" / "track6" / "PP-Y2_cold_lgbq_search_external_combo" / "outputs" / "predictions.csv"
PP_Y2_POLICY = REPO / "experiments" / "track6" / "PP-Y2_cold_lgbq_search_external_combo" / "outputs" / "policy_map.csv"
PP_Y16_PRED = REPO / "experiments" / "track6" / "PP-Y16_cold_y15_oof_fixed_revalidation" / "outputs" / "predictions.csv"
PP_QR1_PRED = REPO / "experiments" / "track6" / "PP-QR1_cold_quantile_regression_alpha_grid" / "outputs" / "predictions.csv"
PP_DEFENSE_METRICS = REPO / "experiments" / "track6" / "PP-COLD-DEFENSE1_cold_guard_search_layer_combination" / "outputs" / "test_metrics.csv"
V03_PARAMS = REPO / "models" / "track6" / "cold_prediction_v0.3" / "config" / "cold_postprocess_params_v0_3.json"
V03_LOOKUP = REPO / "models" / "track6" / "cold_prediction_v0.3" / "config" / "search_delta_lookup_v0_3.json"

MODEL_DIR = REPO / "models" / "track6" / "cold_v03_research_upstream_refreeze_candidate"
ARTIFACT_DIR = MODEL_DIR / "artifacts"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "cold_v03_research_upstream_refreeze_candidate.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "cold_v03_research_upstream_refreeze_candidate.md"

Y2_CANDIDATE = "lgbq_search_all_external_interaction"
Y16_REPRESENTATIVE_CANDIDATE = "lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25"
QR1_LGB_Q40_CANDIDATE = "lightgbm_quantile_q40"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def ensure_dirs() -> None:
    for path in [ARTIFACT_DIR, DOC_JSON.parent]:
        path.mkdir(parents=True, exist_ok=True)


def feature_list_from_policy() -> list[str]:
    policy = pd.read_csv(PP_Y2_POLICY, low_memory=False)
    row = policy[policy["candidate"].eq(Y2_CANDIDATE)]
    if row.empty:
        raise ValueError(f"missing PP-Y2 policy row: {Y2_CANDIDATE}")
    raw = str(row.iloc[0]["features"])
    return [item.strip() for item in raw.split(",") if item.strip()]


def compare_series(name: str, split: str, actual: np.ndarray, expected: np.ndarray) -> dict[str, Any]:
    a = np.asarray(actual, dtype=float)
    e = np.asarray(expected, dtype=float)
    diff = np.abs(a - e)
    return {
        "name": name,
        "split": split,
        "n": int(len(diff)),
        "max_abs_diff": float(np.nanmax(diff)) if len(diff) else None,
        "mean_abs_diff": float(np.nanmean(diff)) if len(diff) else None,
        "p95_abs_diff": float(np.nanquantile(diff, 0.95)) if len(diff) else None,
        "allclose_1e_9": bool(np.allclose(a, e, rtol=0.0, atol=1e-9, equal_nan=True)) if len(diff) else False,
    }


def source_candidate(path: Path, candidate: str, split: str) -> pd.DataFrame:
    raw = pd.read_csv(path, low_memory=False)
    part = raw[raw["candidate"].eq(candidate) & raw["split"].eq(split)].copy()
    if part.empty:
        raise ValueError(f"missing {candidate} {split} in {path}")
    return part.drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)


def metric_triplet(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(np.asarray(pred_log, dtype=float) - actual_log)))),
    }


def train_y2_quantile_models(ycombo: Any, features: list[str]) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    search_df = ycombo.load_search_df()
    train, val, test = ycombo.load_cold_full(features, search_df)
    train = ycombo.normalize_frame(train, features)
    val = ycombo.normalize_frame(val, features)
    test = ycombo.normalize_frame(test, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    out: dict[str, Any] = {}
    for label, alpha in [("q10", 0.1), ("q50", 0.5), ("q90", 0.9)]:
        model = ycombo.lgbm_model(features, objective="quantile", alpha=alpha)
        model.fit(train[features], y)
        out[label] = {
            "alpha": alpha,
            "model": model,
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    return out, val, test


def train_qr1_lgb_q40(qr1: Any) -> tuple[Any, pd.DataFrame, pd.DataFrame, dict[str, np.ndarray]]:
    features = qr1.artifact_features()["cold_lightgbm"]
    train, val, test = qr1.load_scope("cold", features)
    train = qr1.normalize(train, features)
    val = qr1.normalize(val, features)
    test = qr1.normalize(test, features)
    model = qr1.lgbm_quantile_model(features, 0.4, n_estimators=430)
    model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
    preds = {
        "validation": np.asarray(model.predict(val[features]), dtype=float),
        "test": np.asarray(model.predict(test[features]), dtype=float),
    }
    return model, val, test, preds


def build_y16_representative(y16: Any, y2_val: pd.DataFrame, y2_test: pd.DataFrame, y2_preds: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    val = pd.DataFrame({
        "_track6_row_id": y2_val["_track6_row_id"].to_numpy(),
        "actual_log": y2_val["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": y2_val["price_krw"].to_numpy(dtype=float),
        "pred_log": y2_preds["q50"]["validation"],
        "q10_log": y2_preds["q10"]["validation"],
        "q90_log": y2_preds["q90"]["validation"],
    })
    test = pd.DataFrame({
        "_track6_row_id": y2_test["_track6_row_id"].to_numpy(),
        "actual_log": y2_test["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": y2_test["price_krw"].to_numpy(dtype=float),
        "pred_log": y2_preds["q50"]["test"],
        "q10_log": y2_preds["q10"]["test"],
        "q90_log": y2_preds["q90"]["test"],
    })
    for frame in [val, test]:
        frame["residual_log"] = frame["actual_log"] - frame["pred_log"]
        frame["quantile_width_log"] = np.maximum(frame["q90_log"] - frame["q10_log"], 0.0)
        frame["price_range_ratio"] = np.exp(np.clip(frame["quantile_width_log"], 0.0, 8.0))

    for target, source in [(val, y2_val), (test, y2_test)]:
        for col in [
            "gallery_tier_any_available_flag",
            "artist_exhibition_available_count",
            "search_quality_score",
        ]:
            target[col] = (
                pd.to_numeric(source[col], errors="coerce").fillna(0.0).to_numpy(dtype=float)
                if col in source.columns
                else np.zeros(len(target), dtype=float)
            )

    val, test, bin_config = y16.add_segment_columns(val, test)
    val["segment"] = y16.build_segment(val, ["qwidth_bin_fixed"])
    test["segment"] = y16.build_segment(test, ["qwidth_bin_fixed"])
    corr_map, global_corr, segment_map = y16.fit_correction_map(val, min_rows=30)
    test_pred, test_corr = y16.apply_correction(test, corr_map, global_corr, cap=0.25)
    val_pred, val_corr = y16.apply_correction(val, corr_map, global_corr, cap=0.25)
    val_out = y16.prediction_frame(
        Y16_REPRESENTATIVE_CANDIDATE,
        "validation",
        val,
        val_pred,
        val_corr,
        "y15_full_validation_segment_cap_refreeze",
        {"segment": "qwidth_bin", "min_rows": 30, "cap": 0.25, "source_candidate": Y2_CANDIDATE},
    )
    test_out = y16.prediction_frame(
        Y16_REPRESENTATIVE_CANDIDATE,
        "test",
        test,
        test_pred,
        test_corr,
        "y15_full_validation_segment_cap_refreeze",
        {"segment": "qwidth_bin", "min_rows": 30, "cap": 0.25, "source_candidate": Y2_CANDIDATE},
    )
    output = pd.concat([val_out, test_out], ignore_index=True)
    details = {
        "bin_config": bin_config,
        "global_correction": global_corr,
        "eligible_segments": int((segment_map["n"] >= 30).sum()),
        "total_segments": int(len(segment_map)),
        "correction_map": {str(k): float(v) for k, v in corr_map.items()},
    }
    return output, details


def apply_v03(v03: Any, y16_test: pd.DataFrame, qr1_q40_test: np.ndarray) -> pd.DataFrame:
    params = json.loads(V03_PARAMS.read_text(encoding="utf-8"))
    lookup_raw = json.loads(V03_LOOKUP.read_text(encoding="utf-8"))
    lookup = {str(k): float(v) for k, v in lookup_raw["artist_delta"].items()}
    frame = y16_test[[
        "split",
        "_track6_row_id",
        "actual_log",
        "actual_price",
        "quantile_width_log",
        "price_range_ratio",
        "artist_key",
        "pred_log",
    ]].rename(columns={"pred_log": "y18_qwidth_pred_log"}).copy()
    frame["lgb_q40_pred_log"] = qr1_q40_test
    return v03.apply(frame, params=params, lookup=lookup)


def render_markdown(payload: dict[str, Any]) -> str:
    cold = payload["cold_refreeze"]
    lines = [
        "# Cold v0.3 연구 기준 상류 재동결 후보 감사",
        "",
        f"- 작성일: {payload['created_at']}",
        "- 목적: 보고서 기준 Cold 최고 성능 경로를 raw 입력 서비스로 승격하기 위한 저장 가능 범위 확인",
        "- 결론: PP-Y2 LightGBM Quantile과 QR1 LightGBM q40은 재학습/저장 가능 후보로 생성. 검색 피처 수집/표준화 파이프라인은 운영 입력용 별도 연결 필요",
        "",
        "## 1. 저장한 후보 아티팩트",
        "",
        "| 구분 | 파일 |",
        "|---|---|",
    ]
    for key, path in cold["artifacts"].items():
        lines.append(f"| {key} | `{path}` |")
    lines.extend(["", "## 2. 원본 예측 대비 차이", "", "| 항목 | split | n | 최대 차이 | 평균 차이 | p95 차이 | 1e-9 일치 |", "|---|---|---:|---:|---:|---:|---|"])
    for item in cold["parity_checks"]:
        lines.append(
            f"| {item['name']} | {item['split']} | {item['n']} | {item['max_abs_diff']} | {item['mean_abs_diff']} | {item['p95_abs_diff']} | {'예' if item['allclose_1e_9'] else '아니오'} |"
        )
    metrics = cold["v03_test_metrics"]
    compare = cold["recorded_metric_compare"]
    lines.extend([
        "",
        "## 3. v0.3 최종 후처리 재계산",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
        f"| test n | {metrics['n']} |",
        f"| MdAPE | {metrics['MdAPE']:.12f} |",
        f"| MAPE | {metrics['MAPE']:.12f} |",
        f"| p95 APE | {metrics['p95_APE']:.12f} |",
        f"| RMSE log | {metrics['RMSE_log']:.12f} |",
        f"| 기록 지표 대비 최대 차이 | {compare['max_abs_diff']} |",
        "",
        "## 4. 운영 adapter 승격 판단",
        "",
        "- 승격 가능 후보: PP-Y2 검색 포함 LightGBM Quantile, QR1 LightGBM q40, PP-Y16 qwidth segment 보정 map",
        "- 추가 필요: 신규 입력에 대한 검색 피처 수집/표준화, 전시/갤러리 파생 피처 연결, 작가 key 매칭 후 검색 delta fallback 정책",
        "- 현재 의미: 저장 모델 후보는 생성됐지만, 실제 서비스 raw 입력에서 같은 피처를 만들 수 있어야 exact adapter로 승격 가능",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    ensure_dirs()
    ycombo = load_module(YCOMBO_SCRIPT, "cold_v03_refreeze_ycombo")
    qr1 = load_module(QR1_SCRIPT, "cold_v03_refreeze_qr1")
    y16 = load_module(Y16_SCRIPT, "cold_v03_refreeze_y16")
    v03 = load_module(V03_POSTPROCESSOR, "cold_v03_refreeze_postprocessor")

    y2_features = feature_list_from_policy()
    y2_preds, y2_val, y2_test = train_y2_quantile_models(ycombo, y2_features)
    qr1_model, qr1_val, qr1_test, qr1_preds = train_qr1_lgb_q40(qr1)
    y16_predictions, y16_details = build_y16_representative(y16, y2_val, y2_test, y2_preds)

    parity_checks: list[dict[str, Any]] = []
    for split, frame in [("validation", y2_val), ("test", y2_test)]:
        stored = source_candidate(PP_Y2_PRED, Y2_CANDIDATE, split)
        generated = pd.DataFrame({
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "q10_log": y2_preds["q10"][split],
            "pred_log": y2_preds["q50"][split],
            "q90_log": y2_preds["q90"][split],
        }).merge(stored[["_track6_row_id", "q10_log", "pred_log", "q90_log"]], on="_track6_row_id", suffixes=("_candidate", "_stored"))
        for col in ["q10_log", "pred_log", "q90_log"]:
            parity_checks.append(compare_series(f"PP-Y2 {col}", split, generated[f"{col}_candidate"], generated[f"{col}_stored"]))

    for split, frame in [("validation", qr1_val), ("test", qr1_test)]:
        stored = source_candidate(PP_QR1_PRED, QR1_LGB_Q40_CANDIDATE, split)
        generated = pd.DataFrame({
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "pred_log": qr1_preds[split],
        }).merge(stored[["_track6_row_id", "pred_log"]], on="_track6_row_id", suffixes=("_candidate", "_stored"))
        parity_checks.append(compare_series("QR1 LightGBM q40 pred_log", split, generated["pred_log_candidate"], generated["pred_log_stored"]))

    for split in ["test"]:
        stored = source_candidate(PP_Y16_PRED, Y16_REPRESENTATIVE_CANDIDATE, split)
        generated = y16_predictions[y16_predictions["split"].eq(split)].merge(
            stored[["_track6_row_id", "pred_log", "correction_log", "quantile_width_log"]],
            on="_track6_row_id",
            suffixes=("_candidate", "_stored"),
        )
        for col in ["pred_log", "correction_log", "quantile_width_log"]:
            parity_checks.append(compare_series(f"PP-Y16 {col}", split, generated[f"{col}_candidate"], generated[f"{col}_stored"]))

    # Apply v0.3 on generated representative and generated QR1 q40, aligned by row.
    y16_test = y16_predictions[y16_predictions["split"].eq("test")].copy()
    y16_test = y16_test.merge(y2_test[["_track6_row_id"]], on="_track6_row_id", how="inner")
    artist_source = source_candidate(PP_Y2_PRED, Y2_CANDIDATE, "test")[["_track6_row_id"]].copy()
    y18_stored = pd.read_csv(REPO / "experiments" / "track6" / "PP-Y18_cold_y16_top_candidate_stability" / "outputs" / "predictions.csv", low_memory=False)
    y18_stored = y18_stored[y18_stored["candidate"].eq(f"stability_{Y16_REPRESENTATIVE_CANDIDATE}") & y18_stored["split"].eq("test")][["_track6_row_id", "artist_key"]]
    artist_source = artist_source.merge(y18_stored, on="_track6_row_id", how="left")
    y16_test = y16_test.merge(artist_source, on="_track6_row_id", how="left")
    q40_by_row = pd.DataFrame({"_track6_row_id": qr1_test["_track6_row_id"].to_numpy(), "lgb_q40": qr1_preds["test"]})
    y16_test = y16_test.merge(q40_by_row, on="_track6_row_id", how="inner")
    v03_out = apply_v03(v03, y16_test, y16_test["lgb_q40"].to_numpy(dtype=float))
    v03_metrics = metric_triplet(
        v03_out.rename(columns={"cold_defense_pred_log": "pred_log"}),
        v03_out["cold_defense_pred_log"].to_numpy(dtype=float),
    )
    recorded = pd.read_csv(PP_DEFENSE_METRICS, low_memory=False).set_index("candidate")
    recorded_guard_search = {
        "MdAPE": float(recorded.loc["guard_search_gm", "test_MdAPE"]),
        "MAPE": float(recorded.loc["guard_search_gm", "test_MAPE"]),
        "p95_APE": float(recorded.loc["guard_search_gm", "test_p95_APE"]),
    }
    recorded_compare = {
        "recorded": recorded_guard_search,
        "max_abs_diff": float(max(abs(v03_metrics[key] - recorded_guard_search[key]) for key in recorded_guard_search)),
    }

    model_paths = {
        "pp_y2_lgbq_q10": ARTIFACT_DIR / "pp_y2_search_external_lgbq_q10.joblib",
        "pp_y2_lgbq_q50": ARTIFACT_DIR / "pp_y2_search_external_lgbq_q50.joblib",
        "pp_y2_lgbq_q90": ARTIFACT_DIR / "pp_y2_search_external_lgbq_q90.joblib",
        "qr1_lgb_q40": ARTIFACT_DIR / "qr1_lightgbm_q40.joblib",
    }
    joblib.dump(y2_preds["q10"]["model"], model_paths["pp_y2_lgbq_q10"])
    joblib.dump(y2_preds["q50"]["model"], model_paths["pp_y2_lgbq_q50"])
    joblib.dump(y2_preds["q90"]["model"], model_paths["pp_y2_lgbq_q90"])
    joblib.dump(qr1_model, model_paths["qr1_lgb_q40"])
    y16_predictions.to_csv(ARTIFACT_DIR / "pp_y16_refreeze_candidate_predictions.csv", index=False)
    v03_out.to_csv(ARTIFACT_DIR / "cold_v03_refreeze_candidate_test_predictions.csv", index=False)
    (ARTIFACT_DIR / "pp_y16_segment_map.json").write_text(json.dumps(y16_details, ensure_ascii=False, indent=2), encoding="utf-8")
    schema = {
        "pp_y2_feature_columns": y2_features,
        "qr1_lgb_q40_feature_columns": qr1.artifact_features()["cold_lightgbm"],
        "pp_y16_segment_policy": {
            "segment": "qwidth_bin",
            "min_rows": 30,
            "cap": 0.25,
        },
    }
    (ARTIFACT_DIR / "feature_schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "cold_refreeze": {
            "model_dir": rel(MODEL_DIR),
            "rows": {
                "pp_y2_validation": int(len(y2_val)),
                "pp_y2_test": int(len(y2_test)),
                "qr1_validation": int(len(qr1_val)),
                "qr1_test": int(len(qr1_test)),
            },
            "artifacts": {
                "pp_y2_lgbq_q10": rel(model_paths["pp_y2_lgbq_q10"]),
                "pp_y2_lgbq_q50": rel(model_paths["pp_y2_lgbq_q50"]),
                "pp_y2_lgbq_q90": rel(model_paths["pp_y2_lgbq_q90"]),
                "qr1_lgb_q40": rel(model_paths["qr1_lgb_q40"]),
                "pp_y16_segment_map": rel(ARTIFACT_DIR / "pp_y16_segment_map.json"),
                "feature_schema": rel(ARTIFACT_DIR / "feature_schema.json"),
                "candidate_predictions": rel(ARTIFACT_DIR / "cold_v03_refreeze_candidate_test_predictions.csv"),
            },
            "parity_checks": parity_checks,
            "v03_test_metrics": v03_metrics,
            "recorded_metric_compare": recorded_compare,
            "remaining_blockers": [
                "신규 입력에서 PP-Y2와 동일한 검색 피처를 만드는 수집/표준화 파이프라인 연결",
                "전시/갤러리 파생 피처를 운영 DB 또는 feature store에서 안정적으로 생성",
                "신규 작가 또는 검색 미커버 작가의 lookup fallback과 검수 정책",
            ],
        },
    }
    manifest = {
        "model_id": "cold_v03_research_upstream_refreeze_candidate",
        "created_at": payload["created_at"],
        "status": "research_upstream_refreeze_candidate",
        "can_serve_new_raw_input_fully": False,
        "serialized_components": [
            "PP-Y2 search/external LightGBM Quantile q10/q50/q90",
            "QR1 LightGBM Quantile q40",
            "PP-Y16 qwidth segment correction map",
        ],
        "remaining_feature_pipeline_components": payload["cold_refreeze"]["remaining_blockers"],
        "docs": {
            "json": rel(DOC_JSON),
            "markdown": rel(DOC_MD),
        },
    }
    (MODEL_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
