#!/usr/bin/env python3
"""Audit exact adapter readiness for official price_prediction_v0.1.

The official v0.1 API currently runs report final-layer proxy adapters.  This
audit distinguishes three levels:

1. final_layer_replay_ready: frozen final formulas can be replayed from saved
   fixed-split inputs.
2. raw_proxy_ready: raw input can be passed through a compatible proxy bridge.
3. exact_raw_adapter_ready: the original upstream models/features required by
   the report model are serialized and callable for new raw inputs.
"""
from __future__ import annotations

import importlib.util
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
OUT_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_exact_adapter_readiness.json"
OUT_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_exact_adapter_readiness.md"

WARM_PACKAGE = REPO / "experiments" / "track6" / "SUB-WARM-PP258_operational_fixed_test_submission"
WARM_SCRIPT = WARM_PACKAGE / "scripts" / "pp258_reproduce_fixed_test.py"
WARM_INPUT = WARM_PACKAGE / "data" / "pp258_model_input_validation_test.csv"
WARM_STORED_METRICS = WARM_PACKAGE / "outputs" / "pp258_test_metrics.json"
WARM_SOURCE_EXP = REPO / "experiments" / "track6" / "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement"
WARM_SOURCE_FEATURE_DETAIL = WARM_SOURCE_EXP / "artifacts" / "pp252_narrow_refinement_feature_detail.csv"
WARM_SOURCE_RUN_CONFIG = WARM_SOURCE_EXP / "artifacts" / "run_config.json"
WARM_REFREEZE_MANIFEST = REPO / "models" / "track6" / "warm_pp252_upstream_refreeze_candidate" / "manifest.json"
WARM_REFREEZE_AUDIT = REPO / "docs" / "track6" / "experiments" / "warm_pp252_upstream_refreeze_candidate.json"

COLD_BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.3"
COLD_POSTPROCESSOR = COLD_BUNDLE / "predict" / "apply_cold_postprocess_v0_3.py"
COLD_POLICY = COLD_BUNDLE / "config" / "cold_model_policy_v0_3.json"
COLD_PARAMS = COLD_BUNDLE / "config" / "cold_postprocess_params_v0_3.json"
COLD_LOOKUP = COLD_BUNDLE / "config" / "search_delta_lookup_v0_3.json"
COLD_REPRO_CHECK = COLD_BUNDLE / "reproduction" / "best_research_reproducibility_check.json"
COLD_UPSTREAM_SOURCES = COLD_BUNDLE / "reproduction" / "upstream_sources.json"
COLD_V02_RAW = REPO / "models" / "track6" / "cold_prediction_v0.2_operational" / "predict" / "predict_cold_operational_v0_2.py"
COLD_REFREEZE_MANIFEST = REPO / "models" / "track6" / "cold_v03_research_upstream_refreeze_candidate" / "manifest.json"
COLD_REFREEZE_AUDIT = REPO / "docs" / "track6" / "experiments" / "cold_v03_research_upstream_refreeze_candidate.json"
COLD_FEATURE_STORE = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_cold_feature_store.csv"
COLD_FEATURE_PARITY_AUDIT = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_cold_feature_parity_audit.json"
COLD_NEW_INPUT_PIPELINE_AUDIT = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_cold_new_input_pipeline_audit.json"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exists(path: Path) -> bool:
    return path.exists()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def warm_final_layer_check() -> dict[str, Any]:
    result: dict[str, Any] = {
        "script": rel(WARM_SCRIPT),
        "input": rel(WARM_INPUT),
        "stored_metrics": rel(WARM_STORED_METRICS),
        "script_exists": exists(WARM_SCRIPT),
        "input_exists": exists(WARM_INPUT),
        "stored_metrics_exists": exists(WARM_STORED_METRICS),
        "final_layer_replay_ready": False,
        "max_price_abs_diff_vs_stored": None,
        "metrics_match": False,
    }
    if not (WARM_SCRIPT.exists() and WARM_INPUT.exists() and WARM_STORED_METRICS.exists()):
        return result
    module = load_module(WARM_SCRIPT, "official_v01_warm_pp258_readiness")
    frame = pd.read_csv(WARM_INPUT, low_memory=False)
    calculated = module.calculate_pp258_predictions(frame)
    stored_prediction_path = WARM_PACKAGE / "outputs" / "pp258_test_predictions.csv"
    if stored_prediction_path.exists():
        stored = pd.read_csv(stored_prediction_path, low_memory=False)
        key_cols = ["eval_split", "_track6_row_id"]
        compare = calculated.merge(
            stored[key_cols + ["final_price"]],
            on=key_cols,
            suffixes=("_calc", "_stored"),
            how="inner",
        )
        if not compare.empty:
            result["max_price_abs_diff_vs_stored"] = float(
                np.max(np.abs(compare["final_price_calc"].to_numpy(dtype=float) - compare["final_price_stored"].to_numpy(dtype=float)))
            )
    stored_metrics = json.loads(WARM_STORED_METRICS.read_text(encoding="utf-8"))
    test = calculated[calculated["eval_split"].eq("test")].copy()
    metrics = module.metrics(test)
    stored_m = stored_metrics["metrics"]
    metric_diffs = {
        key: abs(float(metrics[key]) - float(stored_m[key]))
        for key in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    }
    result["metric_diffs"] = metric_diffs
    result["metrics_match"] = all(value <= 1e-12 for value in metric_diffs.values())
    result["final_layer_replay_ready"] = bool(result["metrics_match"])
    return result


def warm_exact_raw_check() -> dict[str, Any]:
    source_files = list(WARM_SOURCE_EXP.glob("**/*"))
    model_like = [
        p for p in source_files
        if p.is_file() and p.suffix.lower() in {".joblib", ".pkl", ".cbm", ".json"}
    ]
    serialized_models = [
        p for p in model_like
        if p.suffix.lower() in {".joblib", ".pkl", ".cbm"}
    ]
    refreeze_manifest = json.loads(WARM_REFREEZE_MANIFEST.read_text(encoding="utf-8")) if WARM_REFREEZE_MANIFEST.exists() else {}
    refreeze_audit = json.loads(WARM_REFREEZE_AUDIT.read_text(encoding="utf-8")) if WARM_REFREEZE_AUDIT.exists() else {}
    return {
        "source_experiment": rel(WARM_SOURCE_EXP),
        "feature_detail_exists": WARM_SOURCE_FEATURE_DETAIL.exists(),
        "run_config_exists": WARM_SOURCE_RUN_CONFIG.exists(),
        "serialized_model_files": [rel(p) for p in serialized_models],
        "partial_upstream_refreeze_ready": bool(WARM_REFREEZE_MANIFEST.exists() and WARM_REFREEZE_AUDIT.exists()),
        "partial_upstream_refreeze_manifest": rel(WARM_REFREEZE_MANIFEST),
        "partial_upstream_refreeze_status": refreeze_manifest.get("status"),
        "partial_upstream_refreeze_components": refreeze_manifest.get("serialized_components", []),
        "partial_upstream_refreeze_metric_summary": (
            refreeze_audit.get("warm_refreeze", {}).get("pp258_metrics_delta", {}).get("candidate_metrics", {})
            if refreeze_audit
            else {}
        ),
        "exact_raw_adapter_ready": False,
        "blockers": [
            "방향 분류와 Huber 잔차는 refreeze 후보로 저장되었습니다.",
            "다만 PP252 기준 후보와 PP252 안정 후보를 원시 입력에서 만드는 직전 후보 생성 adapter가 아직 남아 있습니다.",
            "따라서 현재 산출물만으로는 신규 사용자 입력에 대해 PP252 원 상류 컬럼 전체를 exact parity로 생성할 수 없습니다.",
        ],
    }


def cold_final_layer_check() -> dict[str, Any]:
    result: dict[str, Any] = {
        "postprocessor": rel(COLD_POSTPROCESSOR),
        "policy": rel(COLD_POLICY),
        "params": rel(COLD_PARAMS),
        "lookup": rel(COLD_LOOKUP),
        "repro_check": rel(COLD_REPRO_CHECK),
        "postprocessor_exists": COLD_POSTPROCESSOR.exists(),
        "policy_exists": COLD_POLICY.exists(),
        "params_exists": COLD_PARAMS.exists(),
        "lookup_exists": COLD_LOOKUP.exists(),
        "final_layer_replay_ready": False,
    }
    if COLD_REPRO_CHECK.exists():
        check = json.loads(COLD_REPRO_CHECK.read_text(encoding="utf-8"))
        result["repro_check_payload"] = check
        checks = check.get("checks", {})
        result["final_layer_replay_ready"] = bool(
            checks.get("all_passed") is True
            or check.get("postprocessor_max_abs_diff", math.inf) <= 1e-12
            or check.get("reproduced_defense1_guard_search_mdape") is True
        )
    return result


def cold_exact_raw_check() -> dict[str, Any]:
    upstream = json.loads(COLD_UPSTREAM_SOURCES.read_text(encoding="utf-8")) if COLD_UPSTREAM_SOURCES.exists() else {}
    source_paths = {
        key: REPO / value
        for key, value in upstream.items()
        if isinstance(value, str) and not value.startswith("python")
    }
    refreeze_manifest = json.loads(COLD_REFREEZE_MANIFEST.read_text(encoding="utf-8")) if COLD_REFREEZE_MANIFEST.exists() else {}
    refreeze_audit = json.loads(COLD_REFREEZE_AUDIT.read_text(encoding="utf-8")) if COLD_REFREEZE_AUDIT.exists() else {}
    feature_parity_audit = json.loads(COLD_FEATURE_PARITY_AUDIT.read_text(encoding="utf-8")) if COLD_FEATURE_PARITY_AUDIT.exists() else {}
    new_input_audit = json.loads(COLD_NEW_INPUT_PIPELINE_AUDIT.read_text(encoding="utf-8")) if COLD_NEW_INPUT_PIPELINE_AUDIT.exists() else {}
    feature_store_rows = 0
    if COLD_FEATURE_STORE.exists():
        with COLD_FEATURE_STORE.open("r", encoding="utf-8") as fh:
            feature_store_rows = max(sum(1 for _ in fh) - 1, 0)
    return {
        "upstream_sources": {key: rel(path) for key, path in source_paths.items()},
        "upstream_source_exists": {key: path.exists() for key, path in source_paths.items()},
        "raw_v02_predictor_exists": COLD_V02_RAW.exists(),
        "partial_upstream_refreeze_ready": bool(COLD_REFREEZE_MANIFEST.exists() and COLD_REFREEZE_AUDIT.exists()),
        "partial_upstream_refreeze_manifest": rel(COLD_REFREEZE_MANIFEST),
        "partial_upstream_refreeze_status": refreeze_manifest.get("status"),
        "partial_upstream_refreeze_components": refreeze_manifest.get("serialized_components", []),
        "partial_upstream_refreeze_metric_summary": (
            refreeze_audit.get("cold_refreeze", {}).get("v03_test_metrics", {})
            if refreeze_audit
            else {}
        ),
        "row_feature_store_exists": COLD_FEATURE_STORE.exists(),
        "row_feature_store_rows": feature_store_rows,
        "fixed_test_feature_store_replay_ready": bool(
            feature_parity_audit.get("exact_feature_parity_passed")
            and feature_parity_audit.get("exact_prediction_parity_passed")
        ),
        "fixed_test_feature_store_hit_rate": feature_parity_audit.get("coverage", {}).get("cold_feature_store_hit_rate"),
        "feature_parity_audit": {
            "audit_markdown": "docs/track6/experiments/price_prediction_official_v0_1_cold_feature_parity_audit.md",
            "audit_json": rel(COLD_FEATURE_PARITY_AUDIT),
            "fixed_test_rows": feature_parity_audit.get("n_rows"),
            "exact_feature_parity_passed": feature_parity_audit.get("exact_feature_parity_passed"),
            "exact_prediction_parity_passed": feature_parity_audit.get("exact_prediction_parity_passed"),
            "service_feature_metrics": feature_parity_audit.get("metrics_service_features", {}),
        },
        "new_input_cache_feature_pipeline_ready": bool(
            new_input_audit.get("all_deterministic")
            and new_input_audit.get("all_modes_matched")
        ),
        "new_input_pipeline_audit": {
            "audit_markdown": "docs/track6/experiments/price_prediction_official_v0_1_cold_new_input_pipeline_audit.md",
            "audit_json": rel(COLD_NEW_INPUT_PIPELINE_AUDIT),
            "all_deterministic": new_input_audit.get("all_deterministic"),
            "all_modes_matched": new_input_audit.get("all_modes_matched"),
        },
        "exact_raw_adapter_ready": False,
        "blockers": [
            "PP-Y2/PP-Y16/QR1 주요 상류 모델은 refreeze 후보로 저장되었습니다.",
            "fixed-test 행은 row-level feature store와 source_artwork_id/artwork_url lookup으로 exact parity를 통과했습니다.",
            "신규 입력은 search snapshot, 전시/갤러리 cache, missing/default fallback 순서로 deterministic하게 피처를 생성합니다.",
            "다만 feature cache에 없는 신규 작가의 검색/전시/갤러리 정보를 실시간 수집하고 검수해 같은 스키마로 저장하는 live collection pipeline은 아직 남아 있습니다.",
            "raw 실행 가능한 v0.2 predictor는 검색 피처를 제거한 별도 운영 변형이라 v0.3 fixed-test parity와 동일하지 않습니다.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    warm = payload["warm"]
    cold = payload["cold"]
    lines = [
        "# 공식 v0.1 정확 adapter readiness 감사",
        "",
        f"- 작성일: {payload['created_at']}",
        "- 목적: 보고서 기준 Warm/Cold 최종 모델을 raw 입력 서비스에 exact parity로 붙일 수 있는지 점검",
        "",
        "## 1. 결론",
        "",
        f"- Warm 최종층 fixed-test replay 가능: {'예' if warm['final_layer']['final_layer_replay_ready'] else '아니오'}",
        f"- Warm exact raw adapter 가능: {'예' if warm['exact_raw']['exact_raw_adapter_ready'] else '아니오'}",
        f"- Cold 최종층 fixed-test replay 가능: {'예' if cold['final_layer']['final_layer_replay_ready'] else '아니오'}",
        f"- Cold exact raw adapter 가능: {'예' if cold['exact_raw']['exact_raw_adapter_ready'] else '아니오'}",
        "- 현재 서비스 연결 수준: `report_final_layer_proxy`",
        "- 다음 승격 조건: 원 상류 모델을 raw-input 아티팩트로 재동결하거나 재학습해 fixed-test parity를 통과해야 함",
        "",
        "## 2. Warm",
        "",
        "| 항목 | 결과 |",
        "|---|---|",
        f"| PP258 최종층 replay | {'가능' if warm['final_layer']['final_layer_replay_ready'] else '불가'} |",
        f"| 지표 일치 | {'예' if warm['final_layer']['metrics_match'] else '아니오'} |",
        f"| 최대 가격 차이 | {warm['final_layer'].get('max_price_abs_diff_vs_stored')} |",
        f"| PP252 feature detail | {'있음' if warm['exact_raw']['feature_detail_exists'] else '없음'} |",
        f"| 저장 모델 파일 | {len(warm['exact_raw']['serialized_model_files'])}개 |",
        f"| 상류 일부 refreeze | {'완료' if warm['exact_raw'].get('partial_upstream_refreeze_ready') else '미완료'} |",
        f"| exact raw adapter | {'가능' if warm['exact_raw']['exact_raw_adapter_ready'] else '불가'} |",
        "",
        "Warm exact raw adapter blocker:",
        "",
    ]
    lines.extend(f"- {item}" for item in warm["exact_raw"]["blockers"])
    lines.extend([
        "",
        "## 3. Cold",
        "",
        "| 항목 | 결과 |",
        "|---|---|",
        f"| v0.3 후처리 replay | {'가능' if cold['final_layer']['final_layer_replay_ready'] else '불가'} |",
        f"| 후처리 파일 | {'있음' if cold['final_layer']['postprocessor_exists'] else '없음'} |",
        f"| 검색 delta lookup | {'있음' if cold['final_layer']['lookup_exists'] else '없음'} |",
        f"| raw v0.2 predictor | {'있음' if cold['exact_raw']['raw_v02_predictor_exists'] else '없음'} |",
        f"| 상류 일부 refreeze | {'완료' if cold['exact_raw'].get('partial_upstream_refreeze_ready') else '미완료'} |",
        f"| row-level feature store | {'있음' if cold['exact_raw'].get('row_feature_store_exists') else '없음'} ({cold['exact_raw'].get('row_feature_store_rows', 0)}건) |",
        f"| fixed-test feature store replay | {'가능' if cold['exact_raw'].get('fixed_test_feature_store_replay_ready') else '불가'} |",
        f"| fixed-test feature store hit rate | {cold['exact_raw'].get('fixed_test_feature_store_hit_rate')} |",
        f"| 신규 입력 cache/default feature pipeline | {'가능' if cold['exact_raw'].get('new_input_cache_feature_pipeline_ready') else '불가'} |",
        f"| exact raw adapter | {'가능' if cold['exact_raw']['exact_raw_adapter_ready'] else '불가'} |",
        "",
        "Cold exact raw adapter blocker:",
        "",
    ])
    lines.extend(f"- {item}" for item in cold["exact_raw"]["blockers"])
    lines.extend([
        "",
        "## 4. 다음 작업",
        "",
        "| 순서 | 작업 | 산출물 |",
        "|---|---|---|",
        "| 1 | Warm PP252 상류 모델 재동결 | PP252 기준/안정/방향/Huber raw predictor bundle |",
        "| 2 | Warm fixed-test parity 검증 | PP258 stored metrics와 동일한 재현 보고서 |",
        "| 3 | Cold fixed-test feature store replay 유지 | `artwork_url`/`source_artwork_id` 기준 exact parity 감사 결과 |",
        "| 4 | 신규 입력용 Cold live feature collection pipeline 구축 | feature cache에 없는 작가의 검색/전시/갤러리 피처 수집·검수·저장 |",
        "| 5 | 서비스 adapter 승격 | `report_model_adapter` 상태로 API 전환 |",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "service_version": "price_prediction_v0.1",
        "adapter_level_now": "report_final_layer_proxy",
        "warm": {
            "final_layer": warm_final_layer_check(),
            "exact_raw": warm_exact_raw_check(),
        },
        "cold": {
            "final_layer": cold_final_layer_check(),
            "exact_raw": cold_exact_raw_check(),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "created_at": payload["created_at"],
        "warm_final_layer_replay_ready": payload["warm"]["final_layer"]["final_layer_replay_ready"],
        "warm_exact_raw_adapter_ready": payload["warm"]["exact_raw"]["exact_raw_adapter_ready"],
        "cold_final_layer_replay_ready": payload["cold"]["final_layer"]["final_layer_replay_ready"],
        "cold_exact_raw_adapter_ready": payload["cold"]["exact_raw"]["exact_raw_adapter_ready"],
        "outputs": [rel(OUT_JSON), rel(OUT_MD)],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
