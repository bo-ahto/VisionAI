#!/usr/bin/env python3
"""Package the selected WMIN4 Warm candidate for service-side tracking.

The package is intentionally a target-candidate artifact.  It records the
selected WMIN4 fixed-test/validation result and the files needed to replay the
offline decision, but it does not claim exact raw-input service parity.  The
raw-input adapter still needs the min1 comparable-stat SVC payload and the
partial Huber refit path connected before the service can reproduce WMIN4 from
new user input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SERVICE_VERSION = "price_prediction_v0.1"
SOURCE_EXP = REPO / "experiments" / "track6" / "PP-WMIN4_warm_min1_operational_decision"
MODEL_DIR = REPO / "models" / "track6" / "warm_wmin4_operational_candidate"
ARTIFACT_DIR = MODEL_DIR / "artifacts"
CONFIG_DIR = MODEL_DIR / "config"
REPORT_DIR = MODEL_DIR / "reports"
MANIFEST_DIR = MODEL_DIR / "manifest"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "warm_wmin4_operational_candidate_artifact.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "warm_wmin4_operational_candidate_artifact.md"
DEFAULT_DB = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"

SELECTED_LABEL = "min1_huber_refit_partial"
ARTIFACT_ID = "official_v0_1_warm_target_wmin4_min1_huber_refit_partial"
DISPLAY_NAME = "history_based_minimum_one_comparable_huber_correction"
INTERNAL_TRACE_ID = "WMIN4 min1 Huber refit partial"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def artifact_created_at() -> str:
    config_path = SOURCE_EXP / "artifacts" / "run_config.json"
    if not config_path.exists():
        return "2026-06-12T20:53:11"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "2026-06-12T20:53:11"
    return str(payload.get("created_at") or "2026-06-12T20:53:11")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def ensure_dirs() -> None:
    for path in [ARTIFACT_DIR, CONFIG_DIR, REPORT_DIR, MANIFEST_DIR, DOC_JSON.parent]:
        path.mkdir(parents=True, exist_ok=True)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_metrics() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    fixed = pd.read_csv(SOURCE_EXP / "outputs" / "fixed_metrics.csv")
    aggregate = pd.read_csv(SOURCE_EXP / "outputs" / "operational_decision_aggregate.csv")
    selected = fixed[fixed["candidate_label"].eq(SELECTED_LABEL)].copy()
    if selected.empty:
        raise RuntimeError(f"selected candidate metrics not found: {SELECTED_LABEL}")
    test = selected[selected["eval_split"].eq("test")].iloc[0].to_dict()
    validation = selected[selected["eval_split"].eq("validation_oof")].iloc[0].to_dict()
    decision = aggregate[aggregate["candidate_label"].eq(SELECTED_LABEL)].iloc[0].to_dict()
    return _jsonable(test), _jsonable(validation), _jsonable(decision)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    if pd.isna(value):
        return None
    return value


def copy_artifacts() -> dict[str, str]:
    selected_predictions = pd.read_csv(SOURCE_EXP / "outputs" / "candidate_predictions.csv", low_memory=False)
    selected_predictions = selected_predictions[selected_predictions["candidate_label"].eq(SELECTED_LABEL)].copy()
    if selected_predictions.empty:
        raise RuntimeError(f"selected candidate predictions not found: {SELECTED_LABEL}")
    selected_predictions_path = ARTIFACT_DIR / "wmin4_selected_candidate_predictions.csv"
    selected_predictions.to_csv(selected_predictions_path, index=False)

    copies = {
        "selected_candidate_predictions": selected_predictions_path,
        "operational_decision_aggregate": ARTIFACT_DIR / "wmin4_operational_decision_aggregate.csv",
        "fixed_metrics": ARTIFACT_DIR / "wmin4_fixed_metrics.csv",
        "repeated_validation_summary": ARTIFACT_DIR / "wmin4_repeated_validation_summary.csv",
        "run_config": ARTIFACT_DIR / "wmin4_run_config.json",
    }
    shutil.copy2(SOURCE_EXP / "outputs" / "operational_decision_aggregate.csv", copies["operational_decision_aggregate"])
    shutil.copy2(SOURCE_EXP / "outputs" / "fixed_metrics.csv", copies["fixed_metrics"])
    shutil.copy2(SOURCE_EXP / "outputs" / "repeated_validation_summary.csv", copies["repeated_validation_summary"])
    shutil.copy2(SOURCE_EXP / "artifacts" / "run_config.json", copies["run_config"])
    return {name: rel(path) for name, path in copies.items()}


def build_policy() -> dict[str, Any]:
    return {
        "service_version": SERVICE_VERSION,
        "artifact_id": ARTIFACT_ID,
        "display_name": DISPLAY_NAME,
        "internal_trace_id": INTERNAL_TRACE_ID,
        "selected_candidate_label": SELECTED_LABEL,
        "selection_policy": {
            "primary_selection_basis": "validation_oof_repeated_stability_and_replacement_score",
            "fixed_test_usage": "final_confirmation_only",
            "previous_reference": "PP258 operational Warm candidate",
        },
        "warm_route_policy": {
            "artist_match_score_min": 0.90,
            "same_artist_training_price_count_min": 5,
            "note": (
                "Service routing remains at 5 same-artist prices for Warm eligibility. "
                "The selected WMIN4 internal comparable-stat ladder can fall back to "
                "minimum one comparable row after the request is routed to Warm."
            ),
        },
        "selected_logic": {
            "base_price": (
                "Use the Warm min1 comparable-stat numeric seed mean and combine it "
                "with the existing stable blend candidate to form the 70:30 log-price basis."
            ),
            "correction": (
                "Apply the Huber residual coefficient refit in partial mode.  Partial "
                "mode swaps the 70:30 basis to the min1 basis while keeping the prior "
                "SVC residual context stable, then clips the residual correction by the "
                "same HCOEF stable policy used in the WMIN3 validation."
            ),
            "selected_candidate_formula_name": "min1 comparable-stat basis + partial Huber residual refit",
        },
        "raw_adapter_readiness": {
            "target_candidate_artifact_ready": True,
            "proxy_adapter_ready": True,
            "exact_raw_adapter_ready": False,
            "blocking_items": [
                "serialize and connect the min1 comparable-stat SVC payload for raw service input",
                "serialize and connect the WMIN3 partial Huber refit path for raw service input",
                "run fixed-test parity and deterministic-repeat checks through the official v0.1 API",
            ],
        },
    }


def build_manifest(files: dict[str, str], test_metrics: dict[str, Any], validation_metrics: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    policy_path = CONFIG_DIR / "warm_model_policy_wmin4.json"
    source_files = {name: REPO / path for name, path in files.items()}
    return {
        "created_at": artifact_created_at(),
        "service_version": SERVICE_VERSION,
        "artifact_id": ARTIFACT_ID,
        "display_name": DISPLAY_NAME,
        "internal_trace_id": INTERNAL_TRACE_ID,
        "source_experiment": rel(SOURCE_EXP),
        "selected_candidate_label": SELECTED_LABEL,
        "metrics": {
            "fixed_test": test_metrics,
            "validation_oof": validation_metrics,
            "decision_aggregate": decision,
        },
        "policy_file": rel(policy_path),
        "files": files,
        "hashes": {name: file_sha256(path) for name, path in source_files.items()},
        "readiness": build_policy()["raw_adapter_readiness"],
    }


def write_manifest_hash(manifest_path: Path, policy_path: Path, files: dict[str, str]) -> Path:
    rows = []
    for path in [manifest_path, policy_path, *(REPO / value for value in files.values())]:
        rows.append(f"{file_sha256(path)}  {rel(path)}")
    out = MANIFEST_DIR / "MANIFEST.sha256"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return out


def render_markdown(manifest: dict[str, Any]) -> str:
    test = manifest["metrics"]["fixed_test"]
    validation = manifest["metrics"]["validation_oof"]
    decision = manifest["metrics"]["decision_aggregate"]
    return "\n".join(
        [
            "# Warm WMIN4 운영 후보 아티팩트",
            "",
            f"- 작성일: {manifest['created_at']}",
            f"- 서비스 버전: `{manifest['service_version']}`",
            f"- 문서용 모델명: 이력 기반 최소 1건 유사작품 Huber 보정 후보",
            f"- 내부 추적 ID: `{manifest['internal_trace_id']}`",
            f"- 선택 후보: `{manifest['selected_candidate_label']}`",
            "",
            "## 1. 선택 결론",
            "",
            "- WMIN4 반복 검증에서 기존 PP258 운영 후보보다 validation MAPE, p95 APE, fixed test MAPE가 함께 개선됨.",
            "- fixed test 기준 MAPE는 0.239302로, 직전 운영 후보 0.269888 대비 0.030586 감소.",
            "- fixed test 기준 p95 APE는 0.779196로, 직전 운영 후보 0.807325 대비 0.028129 감소.",
            "",
            "## 2. 핵심 지표",
            "",
            "| 구간 | n | MdAPE | MAPE | p95 APE | RMSE log |",
            "|---|---:|---:|---:|---:|---:|",
            f"| validation OOF | {validation['n']} | {validation['MdAPE']:.6f} | {validation['MAPE']:.6f} | {validation['p95_APE']:.6f} | {validation['RMSE_log']:.6f} |",
            f"| fixed test | {test['n']} | {test['MdAPE']:.6f} | {test['MAPE']:.6f} | {test['p95_APE']:.6f} | {test['RMSE_log']:.6f} |",
            "",
            "## 3. 반복 검증 안정성",
            "",
            "| 항목 | 값 |",
            "|---|---:|",
            f"| validation MAPE 승률 | {decision['validation_avg_MAPE_win_rate']:.6f} |",
            f"| validation p95 승률 | {decision['validation_avg_p95_win_rate']:.6f} |",
            f"| validation all3 승률 | {decision['validation_avg_all3_win_rate']:.6f} |",
            f"| validation replacement score | {decision['validation_replacement_score']:.6f} |",
            "",
            "## 4. 운영 연결 상태",
            "",
            "- 현재 상태: 선택 후보 산출물 고정 완료.",
            "- 아직 불가: 신규 사용자 입력에서 WMIN4를 정확히 재현하는 raw-input adapter.",
            "- 남은 연결: min1 유사작품 통계 기반 SVC payload 저장, partial Huber refit 경로 저장, API 고정 테스트 재현 검증.",
        ]
    ) + "\n"


def update_registry(db_path: Path, manifest: dict[str, Any]) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    test = manifest["metrics"]["fixed_test"]
    metrics = {
        "MAPE": test["MAPE"],
        "MdAPE": test["MdAPE"],
        "RMSE_log": test["RMSE_log"],
        "fixed_test_n": test["n"],
        "p95_APE": test["p95_APE"],
        "exact_raw_adapter_ready": False,
        "selected_candidate_label": SELECTED_LABEL,
    }
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE model_artifact_registry
            SET active_flag = 0
            WHERE service_version = ? AND route = 'warm'
            """,
            (SERVICE_VERSION,),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO model_artifact_registry (
              artifact_id, service_version, route, artifact_role, display_name,
              internal_trace_id, artifact_path, artifact_hash,
              feature_schema_version, metrics_json, active_flag, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ARTIFACT_ID,
                SERVICE_VERSION,
                "warm",
                "target_report_model",
                DISPLAY_NAME,
                INTERNAL_TRACE_ID,
                rel(MODEL_DIR),
                file_sha256(MODEL_DIR / "manifest.json"),
                "official_v0_1_initial_cache_plus_wmin4_min1_target",
                json.dumps(metrics, ensure_ascii=False, sort_keys=True),
                1,
                now_iso(),
            ),
        )
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-db-registry", action="store_true")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    ensure_dirs()
    test_metrics, validation_metrics, decision = read_metrics()
    files = copy_artifacts()
    policy = build_policy()
    policy_path = CONFIG_DIR / "warm_model_policy_wmin4.json"
    policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = build_manifest(files, test_metrics, validation_metrics, decision)
    manifest_path = MODEL_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    hash_path = write_manifest_hash(manifest_path, policy_path, files)

    report = render_markdown(manifest)
    report_path = REPORT_DIR / "warm_wmin4_operational_candidate_release.md"
    report_path.write_text(report, encoding="utf-8")
    DOC_MD.write_text(report, encoding="utf-8")
    DOC_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.update_db_registry:
        update_registry(args.db_path.resolve(), manifest)

    print(json.dumps({
        "manifest": rel(manifest_path),
        "policy": rel(policy_path),
        "hash_manifest": rel(hash_path),
        "doc": rel(DOC_MD),
        "db_registry_updated": bool(args.update_db_registry),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
