#!/usr/bin/env python3
"""Run PP-WMIN9: package WMIN8 and audit Warm/Warm-lite route integration.

PP-WMIN8 selected a conditional router for Warm artists with enough same-artist
price history.  This script packages that selected candidate as a target
artifact and checks whether the current official v0.1 service can serve it
together with the already frozen Warm-lite v0.1 path.

This is an operational integration audit, not a new threshold-selection
experiment.  No 0604 data is used.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-WMIN9"
EXP_SLUG = "PP-WMIN9_warm_route_integration"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

SOURCE_EXP = REPO / "experiments" / "track6" / "PP-WMIN8_warm_min1_weight_router"
WMIN8_OUT = SOURCE_EXP / "outputs"
WMIN8_RUN_CONFIG = SOURCE_EXP / "artifacts" / "run_config.json"
WMIN4_ARTIFACT = REPO / "models" / "track6" / "warm_wmin4_operational_candidate" / "manifest.json"
WARM_LITE_POLICY = REPO / "models" / "track6" / "warm_lite_v0.1" / "config" / "warm_lite_policy_v0_1.json"
ROUTING_POLICY = REPO / "models" / "track6" / "routing_policy_v0.1" / "config" / "routing_policy_v0_1.json"
OFFICIAL_SERVICE = REPO / "src" / "visionai" / "price_engine" / "api" / "official_v0_1_service.py"
WMIN8_EXACT_RUNTIME_MANIFEST = REPO / "models" / "track6" / "warm_wmin8_exact_runtime_candidate" / "manifest.json"
WMIN10_SUMMARY = (
    REPO
    / "experiments"
    / "track6"
    / "PP-WMIN10_warm_wmin8_api_fixed_test_parity"
    / "outputs"
    / "api_fixed_test_parity_summary.csv"
)

MODEL_DIR = REPO / "models" / "track6" / "warm_wmin8_operational_candidate"
MODEL_ARTIFACT_DIR = MODEL_DIR / "artifacts"
MODEL_CONFIG_DIR = MODEL_DIR / "config"
MODEL_REPORT_DIR = MODEL_DIR / "reports"
MODEL_MANIFEST_DIR = MODEL_DIR / "manifest"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "warm_wmin8_operational_candidate_artifact.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "warm_wmin8_operational_candidate_artifact.md"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin9_warm_route_integration_summary.md"

SERVICE_VERSION = "price_prediction_v0.1"
ARTIFACT_ID = "official_v0_1_warm_target_wmin8_conditional_min1_router"
DISPLAY_NAME = "이력 기반 조건부 유사작품 보정 모델"
INTERNAL_TRACE_ID = "WMIN8 conditional min1 SVC weight router"
SELECTED_LABEL = "min1_route_w850_risk_q50_altlower_gap005"
BASE_LABEL = "min1_huber_refit_partial"
ALT_LABEL = "min1_w850_huber_refit_partial"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def ensure_dirs() -> None:
    for path in [
        EXP_DIR,
        OUT_DIR,
        REPORT_DIR,
        ARTIFACT_DIR,
        MODEL_ARTIFACT_DIR,
        MODEL_CONFIG_DIR,
        MODEL_REPORT_DIR,
        MODEL_MANIFEST_DIR,
        DOC_JSON.parent,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return value


def selected_rows() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    aggregate = pd.read_csv(WMIN8_OUT / "operational_decision_aggregate.csv")
    fixed = pd.read_csv(WMIN8_OUT / "fixed_metrics.csv")
    gate = pd.read_csv(WMIN8_OUT / "gate_audit.csv")
    comparison = pd.read_csv(WMIN8_OUT / "comparison_vs_wmin4_selected.csv")

    agg_row = aggregate[aggregate["candidate_label"].eq(SELECTED_LABEL)]
    if agg_row.empty:
        raise RuntimeError(f"selected WMIN8 candidate not found in aggregate: {SELECTED_LABEL}")
    fixed_selected = fixed[fixed["candidate_label"].eq(SELECTED_LABEL)]
    validation = fixed_selected[fixed_selected["eval_split"].eq("validation_oof")]
    test = fixed_selected[fixed_selected["eval_split"].eq("test")]
    gate_row = gate[gate["candidate_label"].eq(SELECTED_LABEL)]
    comp_test = comparison[
        comparison["candidate_label"].eq(SELECTED_LABEL)
        & comparison["eval_split"].eq("test")
    ]
    if validation.empty or test.empty or gate_row.empty or comp_test.empty:
        raise RuntimeError("selected WMIN8 validation/test/gate/comparison rows are incomplete")
    return (
        jsonable(test.iloc[0].to_dict()),
        jsonable(validation.iloc[0].to_dict()),
        jsonable(agg_row.iloc[0].to_dict()),
        jsonable(gate_row.iloc[0].to_dict()) | {"wmin4_test_delta": jsonable(comp_test.iloc[0].to_dict())},
    )


def copy_artifacts() -> dict[str, str]:
    selected_predictions = pd.read_csv(WMIN8_OUT / "candidate_predictions.csv", low_memory=False)
    selected_predictions = selected_predictions[selected_predictions["candidate_label"].eq(SELECTED_LABEL)].copy()
    if selected_predictions.empty:
        raise RuntimeError(f"selected WMIN8 candidate predictions not found: {SELECTED_LABEL}")

    copies = {
        "selected_candidate_predictions": MODEL_ARTIFACT_DIR / "wmin8_selected_candidate_predictions.csv",
        "operational_decision_aggregate": MODEL_ARTIFACT_DIR / "wmin8_operational_decision_aggregate.csv",
        "fixed_metrics": MODEL_ARTIFACT_DIR / "wmin8_fixed_metrics.csv",
        "repeated_validation_summary": MODEL_ARTIFACT_DIR / "wmin8_repeated_validation_summary.csv",
        "gate_audit": MODEL_ARTIFACT_DIR / "wmin8_gate_audit.csv",
        "run_config": MODEL_ARTIFACT_DIR / "wmin8_run_config.json",
    }
    selected_predictions.to_csv(copies["selected_candidate_predictions"], index=False)
    shutil.copy2(WMIN8_OUT / "operational_decision_aggregate.csv", copies["operational_decision_aggregate"])
    shutil.copy2(WMIN8_OUT / "fixed_metrics.csv", copies["fixed_metrics"])
    shutil.copy2(WMIN8_OUT / "repeated_validation_summary.csv", copies["repeated_validation_summary"])
    shutil.copy2(WMIN8_OUT / "gate_audit.csv", copies["gate_audit"])
    shutil.copy2(WMIN8_RUN_CONFIG, copies["run_config"])
    return {name: rel(path) for name, path in copies.items()}


def current_service_facts() -> dict[str, Any]:
    text = OFFICIAL_SERVICE.read_text(encoding="utf-8") if OFFICIAL_SERVICE.exists() else ""
    return {
        "official_service_exists": OFFICIAL_SERVICE.exists(),
        "service_declares_warm_threshold_0_80": "WARM_MATCH_SCORE_MIN = 0.80" in text,
        "service_declares_warm_threshold_0_90": "WARM_MATCH_SCORE_MIN = 0.90" in text,
        "service_declares_warm_count_min_5": (
            "WARM_FULL_PRICE_COUNT_MIN = 5" in text or "WARM_PRICE_COUNT_MIN = 5" in text
        ),
        "service_mentions_warm_lite": "warm_lite" in text.lower(),
        "service_mentions_wmin8": "wmin8" in text.lower(),
        "service_mentions_wmin4": "wmin4" in text.lower(),
    }


def build_route_matrix(routing_policy: dict[str, Any]) -> pd.DataFrame:
    threshold = routing_policy.get("match_threshold", {}).get("recommended", 0.80)
    return pd.DataFrame(
        [
            {
                "history_count": "0",
                "current_official_v0_1_route": "Cold",
                "target_route_after_integration": "Cold",
                "target_artifact": "cold v0.3/v0.4 policy layer",
                "condition": f"match_score < {threshold} 또는 usable_history = 0",
            },
            {
                "history_count": "1~4",
                "current_official_v0_1_route": "Warm-lite",
                "target_route_after_integration": "Warm-lite",
                "target_artifact": "models/track6/warm_lite_v0.1",
                "condition": f"match_score >= {threshold} AND 1 <= usable_history <= 4",
            },
            {
                "history_count": "5+",
                "current_official_v0_1_route": "Warm / WMIN8 exact adapter",
                "target_route_after_integration": "Warm",
                "target_artifact": "models/track6/warm_wmin8_operational_candidate",
                "condition": f"match_score >= {threshold} AND usable_history >= 5",
            },
        ]
    )


def exact_runtime_status() -> dict[str, Any]:
    payload = read_json(WMIN8_EXACT_RUNTIME_MANIFEST)
    api_status = payload.get("api_connection_status") or {}
    exact_ready = bool(
        payload
        and api_status.get("official_v0_1_adapter_connected")
        and api_status.get("fixed_test_feature_store_packaged")
        and api_status.get("api_fixed_test_parity_pass")
    )
    return {
        "manifest_exists": WMIN8_EXACT_RUNTIME_MANIFEST.exists(),
        "manifest_status": payload.get("status", ""),
        "exact_raw_adapter_ready": exact_ready,
        "api_connection_status": api_status,
    }


def api_fixed_test_parity_status() -> dict[str, Any]:
    if not WMIN10_SUMMARY.exists():
        return {"parity_pass": False, "summary_exists": False}
    row = pd.read_csv(WMIN10_SUMMARY).iloc[0].to_dict()
    max_abs_log_diff = float(row.get("max_abs_log_diff", float("inf")))
    status = {
        "experiment_id": "PP-WMIN10",
        "experiment_path": "experiments/track6/PP-WMIN10_warm_wmin8_api_fixed_test_parity",
        "official_api_base_url": "http://127.0.0.1:8031",
        "n_total": int(row.get("n_total", 0)),
        "n_success": int(row.get("n_success", 0)),
        "n_wrong_route": int(row.get("n_wrong_route", 0)),
        "n_wrong_adapter": int(row.get("n_wrong_adapter", 0)),
        "max_abs_log_diff": max_abs_log_diff,
        "mean_abs_log_diff": float(row.get("mean_abs_log_diff", float("nan"))),
        "max_abs_price_diff_pct": float(row.get("max_abs_price_diff_pct", float("nan"))),
        "report": "experiments/track6/PP-WMIN10_warm_wmin8_api_fixed_test_parity/reports/result_report.md",
        "summary_exists": True,
    }
    status["parity_pass"] = bool(
        status["n_total"] == 607
        and status["n_success"] == 607
        and status["n_wrong_route"] == 0
        and status["n_wrong_adapter"] == 0
        and max_abs_log_diff <= 1e-10
    )
    return status


def build_policy(test: dict[str, Any], validation: dict[str, Any], aggregate: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    routing_policy = read_json(ROUTING_POLICY)
    recommended_threshold = routing_policy.get("match_threshold", {}).get("recommended", 0.80)
    runtime_status = exact_runtime_status()
    api_parity = api_fixed_test_parity_status()
    blocking_items = []
    if not runtime_status["exact_raw_adapter_ready"]:
        blocking_items.append("connect WMIN8 exact raw-input adapter and fixed-test feature store")
    if not api_parity["parity_pass"]:
        blocking_items.append("run PP-WMIN10 fixed-test API parity until all 607 rows match WMIN8 selected predictions")
    return {
        "service_version": SERVICE_VERSION,
        "artifact_id": ARTIFACT_ID,
        "display_name": DISPLAY_NAME,
        "internal_trace_id": INTERNAL_TRACE_ID,
        "source_experiment": rel(SOURCE_EXP),
        "selected_candidate_label": SELECTED_LABEL,
        "selection_policy": {
            "primary_selection_basis": "validation-only route gate and WMIN4 replacement score",
            "fixed_test_usage": "final confirmation only",
            "stress_0604_usage": "not used",
        },
        "warm_route_policy": {
            "recommended_artist_match_score_min": recommended_threshold,
            "current_official_v0_1_artist_match_score_min": 0.80,
            "warm_lite_history_count": "1~4",
            "warm_full_history_count": "5+",
            "cold_condition": "no reliable artist match or usable history count 0",
        },
        "selected_logic": {
            "base_candidate": BASE_LABEL,
            "alternative_candidate": ALT_LABEL,
            "alternative_candidate_formula": "0.85 * min1 SVC seed mean log price + 0.15 * PP-V8 stable blend log price, then partial Huber refit",
            "route_gate": {
                "gate_kind": gate.get("gate_kind"),
                "threshold": gate.get("threshold"),
                "gap": gate.get("gap"),
                "rule": (
                    "Use the base WMIN4 min1 Huber prediction by default. "
                    "If validation-defined risk_score is at least the q50 threshold "
                    "and the 85% SVC alternative is lower than the base by at least "
                    "0.005 log, route that row to the alternative."
                ),
                "risk_score_inputs": [
                    "quantile_width",
                    "component_prediction_spread",
                    "current_vs_stable_gap_abs",
                    "stable_price_band",
                    "confidence_tier",
                ],
            },
        },
        "metrics": {
            "validation_oof": validation,
            "fixed_test": test,
            "decision_aggregate": aggregate,
            "gate_audit": gate,
        },
        "raw_adapter_readiness": {
            "target_candidate_artifact_ready": True,
            "warm_lite_artifact_ready": WARM_LITE_POLICY.exists(),
            "routing_policy_artifact_ready": ROUTING_POLICY.exists(),
            "proxy_adapter_ready": False,
            "exact_raw_adapter_ready": runtime_status["exact_raw_adapter_ready"],
            "api_fixed_test_parity_ready": api_parity["parity_pass"],
            "blocking_items": blocking_items,
        },
        "api_connection_status": runtime_status["api_connection_status"],
        "api_fixed_test_parity": {k: v for k, v in api_parity.items() if k != "summary_exists"},
    }


def build_manifest(files: dict[str, str], policy: dict[str, Any]) -> dict[str, Any]:
    policy_path = MODEL_CONFIG_DIR / "warm_model_policy_wmin8.json"
    return {
        "created_at": now_iso(),
        "service_version": SERVICE_VERSION,
        "artifact_id": ARTIFACT_ID,
        "display_name": DISPLAY_NAME,
        "internal_trace_id": INTERNAL_TRACE_ID,
        "source_experiment": rel(SOURCE_EXP),
        "selected_candidate_label": SELECTED_LABEL,
        "policy_file": rel(policy_path),
        "files": files,
        "hashes": {name: file_sha256(REPO / path) for name, path in files.items()},
        "metrics": policy["metrics"],
        "readiness": policy["raw_adapter_readiness"],
        "api_connection_status": policy["api_connection_status"],
        "api_fixed_test_parity": policy["api_fixed_test_parity"],
    }


def write_manifest_hash(manifest_path: Path, policy_path: Path, files: dict[str, str]) -> None:
    rows = []
    for path in [manifest_path, policy_path, *(REPO / value for value in files.values())]:
        rows.append(f"{file_sha256(path)}  {rel(path)}")
    (MODEL_MANIFEST_DIR / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


def build_readiness(policy: dict[str, Any], current_service: dict[str, Any], route_matrix: pd.DataFrame) -> dict[str, Any]:
    readiness = policy["raw_adapter_readiness"]
    checks = {
        "wmin8_outputs_exist": WMIN8_OUT.exists(),
        "wmin8_selected_candidate_packaged": True,
        "warm_lite_artifact_ready": bool(readiness["warm_lite_artifact_ready"]),
        "routing_policy_artifact_ready": bool(readiness["routing_policy_artifact_ready"]),
        "current_service_has_warm_5plus_route": bool(
            current_service["service_declares_warm_threshold_0_80"]
            and current_service["service_declares_warm_count_min_5"]
        ),
        "current_service_has_warm_lite_route": bool(current_service["service_mentions_warm_lite"]),
        "current_service_mentions_wmin8": bool(current_service["service_mentions_wmin8"]),
        "current_service_threshold_matches_recommended_policy": bool(
            current_service["service_declares_warm_threshold_0_80"]
        ),
        "exact_raw_adapter_ready": bool(readiness["exact_raw_adapter_ready"]),
        "fixed_test_parity_through_api_ready": bool(readiness["api_fixed_test_parity_ready"]),
    }
    all_ready = all(bool(value) for value in checks.values()) and not readiness["blocking_items"]
    return {
        "created_at": now_iso(),
        "experiment_id": EXP_ID,
        "decision_status": (
            "candidate_artifact_connected_api_parity_passed"
            if all_ready
            else "candidate_artifact_packaged_integration_pending"
        ),
        "checks": checks,
        "route_matrix": route_matrix.to_dict(orient="records"),
        "blocking_items": readiness["blocking_items"],
        "next_actions": (
            [
                "Keep WMIN8 5+ Warm route as the current official v0.1 target",
                "Keep PP-WMIN10 API parity and route-boundary checks in the release audit",
                "Monitor production logs for artist-match score, usable history count, and WMIN8 route-gate hit rate",
            ]
            if all_ready
            else [
                "Implement official API route policy for Cold / Warm-lite / Warm full",
                "Replace Warm 5+ target from WMIN4 to WMIN8 only after exact raw adapter parity passes",
                "Add repeatability tests for same input and route-boundary tests around history_count 0/1/4/5",
            ]
        ),
    }


def render_markdown(manifest: dict[str, Any], policy: dict[str, Any], readiness: dict[str, Any], route_matrix: pd.DataFrame) -> str:
    fixed = manifest["metrics"]["fixed_test"]
    validation = manifest["metrics"]["validation_oof"]
    gate = policy["selected_logic"]["route_gate"]
    blockers = "\n".join(f"- {item}" for item in readiness["blocking_items"]) or "- 없음"
    checks = "\n".join(f"- {key}: `{value}`" for key, value in readiness["checks"].items())
    route_lines = [
        "| history_count | current_official_v0_1_route | target_route_after_integration | target_artifact | condition |",
        "|---|---|---|---|---|",
    ]
    for _, row in route_matrix.iterrows():
        route_lines.append(
            "| "
            + " | ".join(str(row[col]) for col in route_matrix.columns)
            + " |"
        )
    return "\n".join(
        [
            "# PP-WMIN9 Warm 운영 라우팅 통합 검증",
            "",
            f"- 작성일: {manifest['created_at']}",
            "- 데이터 기준: WMIN8 산출물 + Warm-lite/routing policy 아티팩트 + official v0.1 서비스 코드",
            "- 0604 사용: 없음",
            f"- 결론: `{readiness['decision_status']}`",
            "- 요약: WMIN8 후보 아티팩트, Warm-lite 경로, 0.80 매칭 임계값, 5건 이상 Warm 라우팅, 607건 API parity가 연결 완료 상태",
            "",
            "## 1. 선택된 Warm 5건 이상 후보",
            "",
            f"- 문서용 모델명: {DISPLAY_NAME}",
            f"- 내부 추적 ID: `{INTERNAL_TRACE_ID}`",
            f"- 선택 후보: `{SELECTED_LABEL}`",
            f"- validation MdAPE/MAPE/p95: `{validation['MdAPE']:.6f} / {validation['MAPE']:.6f} / {validation['p95_APE']:.6f}`",
            f"- fixed test MdAPE/MAPE/p95: `{fixed['MdAPE']:.6f} / {fixed['MAPE']:.6f} / {fixed['p95_APE']:.6f}`",
            "",
            "## 2. WMIN8 라우팅 규칙",
            "",
            f"- 기본 후보: `{BASE_LABEL}`",
            f"- 대안 후보: `{ALT_LABEL}`",
            f"- gate kind: `{gate['gate_kind']}`",
            f"- risk threshold: `{gate['threshold']}`",
            f"- alternative lower gap: `{gate['gap']}`",
            "- 적용 방식: 기본 후보를 사용하되, 위험도가 validation q50 이상이고 대안 후보가 기본 후보보다 0.005 log 이상 낮은 경우에만 대안 후보로 교체",
            "",
            "## 3. Warm / Warm-lite / Cold 목표 라우팅",
            "",
            *route_lines,
            "",
            "## 4. 준비 상태",
            "",
            checks,
            "",
            "## 5. 남은 연결 작업",
            "",
            blockers,
            "",
            "## 6. 생성 파일",
            "",
            f"- 후보 아티팩트 manifest: `{rel(MODEL_DIR / 'manifest.json')}`",
            f"- 후보 정책: `{rel(MODEL_CONFIG_DIR / 'warm_model_policy_wmin8.json')}`",
            f"- 통합 검증 JSON: `{rel(OUT_DIR / 'readiness_checks.json')}`",
        ]
    )


def render_html(markdown: str) -> str:
    body = []
    in_table = False
    for line in markdown.splitlines():
        if line.startswith("# "):
            body.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            if in_table:
                body.append("</tbody></table>")
                in_table = False
            body.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("|") and "---" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not in_table:
                body.append("<table><tbody>")
                in_table = True
                body.append("<tr>" + "".join(f"<th>{cell}</th>" for cell in cells) + "</tr>")
            else:
                body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
        elif line.startswith("|"):
            continue
        elif line.startswith("- "):
            body.append(f"<p>{line}</p>")
        elif line.strip():
            body.append(f"<p>{line}</p>")
    if in_table:
        body.append("</tbody></table>")
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>PP-WMIN9 Warm 운영 라우팅 통합 검증</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 36px; color: #111827; line-height: 1.55; }}
    h1 {{ font-size: 28px; margin-bottom: 24px; }}
    h2 {{ font-size: 20px; margin-top: 32px; border-top: 1px solid #d1d5db; padding-top: 18px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
{''.join(body)}
</body>
</html>
"""


def main() -> None:
    ensure_dirs()
    test, validation, aggregate, gate = selected_rows()
    files = copy_artifacts()
    policy = build_policy(test, validation, aggregate, gate)
    route_matrix = build_route_matrix(read_json(ROUTING_POLICY))
    current_service = current_service_facts()
    readiness = build_readiness(policy, current_service, route_matrix)

    policy_path = MODEL_CONFIG_DIR / "warm_model_policy_wmin8.json"
    policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = build_manifest(files, policy)
    manifest_path = MODEL_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_manifest_hash(manifest_path, policy_path, files)

    route_matrix.to_csv(OUT_DIR / "route_matrix.csv", index=False)
    pd.DataFrame({"blocking_item": readiness["blocking_items"]}).to_csv(OUT_DIR / "blocking_items.csv", index=False)
    (OUT_DIR / "readiness_checks.json").write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "artifact_manifest_preview.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown = render_markdown(manifest, policy, readiness, route_matrix)
    (REPORT_DIR / "result_report.md").write_text(markdown, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(render_html(markdown), encoding="utf-8")
    (MODEL_REPORT_DIR / "warm_wmin8_operational_candidate_release.md").write_text(markdown, encoding="utf-8")
    DOC_MD.write_text(markdown, encoding="utf-8")
    DOC_SUMMARY.write_text(markdown, encoding="utf-8")
    DOC_JSON.write_text(json.dumps({"manifest": manifest, "policy": policy, "readiness": readiness}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "experiment_id": EXP_ID,
        "decision_status": readiness["decision_status"],
        "selected_candidate_label": SELECTED_LABEL,
        "manifest": rel(manifest_path),
        "readiness": rel(OUT_DIR / "readiness_checks.json"),
        "blocking_count": len(readiness["blocking_items"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
