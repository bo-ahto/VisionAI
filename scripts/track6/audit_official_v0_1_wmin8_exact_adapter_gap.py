"""Audit remaining gaps for an exact WMIN8 raw-input adapter."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
WMIN8_MANIFEST = REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "manifest.json"
WMIN8_POLICY = REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "config" / "warm_model_policy_wmin8.json"
WMIN8_EXACT_RUNTIME = REPO / "models" / "track6" / "warm_wmin8_exact_runtime_candidate" / "manifest.json"
WMIN7_COEFFICIENTS = REPO / "experiments" / "track6" / "PP-WMIN7_warm_min1_weight_retuning" / "outputs" / "huber_refit_coefficients.csv"
WMIN8_GATE_AUDIT = REPO / "experiments" / "track6" / "PP-WMIN8_warm_min1_weight_router" / "outputs" / "gate_audit.csv"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_wmin8_exact_adapter_gap_audit.md"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_wmin8_exact_adapter_gap_audit.json"


SERVICE_RUNTIME_COLUMN_MAP = {
    "ppv8_defensive": "pp_v8_compact_blend_mape_guarded_pred_log",
    "svc_fallback": "svc_numeric_seed_mean_pred_log",
    "log_area": "log_area",
    "svc_group_n_log": "svc_group_n_log",
    "svc_prior_iqr": "svc_group_log_price_iqr",
    "quantile_width": "l10_quantile_width",
    "component_prediction_spread": "computed_from_component_logs",
    "current_vs_stable_gap_abs": "computed_from_candidate_logs",
    "stable_price_band": "computed_from_candidate_log_price",
    "confidence_tier": "service_confidence_tier",
}

MISSING_EXACT_RUNTIME_INPUTS = {
    "shrunk_huber_refit": "Requires the upstream shrunk comparable Huber refit model output used by PP-HCOEF1/WMIN3.",
    "shrunk_svc_prior": "Requires the upstream comparable-prior shrinkage output used by PP-HCOEF1/WMIN3.",
    "raw_svc_prior": "Required indirectly for raw_shrunk_prior_gap = raw_svc_prior - shrunk_svc_prior.",
    "current_shrunk_huber_gap": "Requires current_70_30 - shrunk_huber_refit.",
    "raw_shrunk_prior_gap": "Requires raw_svc_prior - shrunk_svc_prior.",
}

REQUIRED_HUBER_FEATURES = [
    "ppv8_defensive",
    "svc_fallback",
    "shrunk_huber_refit",
    "shrunk_svc_prior",
    "log_area",
    "svc_group_n_log",
    "svc_prior_iqr",
    "current_ppv8_gap",
    "current_shrunk_huber_gap",
    "raw_shrunk_prior_gap",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def file_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(REPO)),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def selected_gate() -> dict[str, Any]:
    if not WMIN8_GATE_AUDIT.exists():
        return {}
    audit = pd.read_csv(WMIN8_GATE_AUDIT)
    selected = audit[audit["candidate_label"].eq("min1_route_w850_risk_q50_altlower_gap005")]
    if selected.empty:
        return {}
    row = selected.iloc[0]
    return {
        "candidate_label": str(row["candidate_label"]),
        "base_candidate": "min1_huber_refit_partial",
        "alternative_candidate": str(row["alt_candidate"]),
        "gate_kind": str(row["gate_kind"]),
        "threshold": float(row["threshold"]),
        "gap": float(row["gap"]),
        "validation_route_share": float(row["validation_route_share"]),
        "test_route_share": float(row["test_route_share"]),
    }


def exact_runtime_ready(payload: dict[str, Any]) -> bool:
    return bool(payload.get("huber_pipeline_parity", {}).get("passes_prediction_csv_replay") is True)


def huber_feature_status(runtime_ready: bool) -> list[dict[str, Any]]:
    rows = []
    for feature in REQUIRED_HUBER_FEATURES:
        if feature in SERVICE_RUNTIME_COLUMN_MAP:
            rows.append(
                {
                    "feature": feature,
                    "service_runtime_status": "available",
                    "service_source": SERVICE_RUNTIME_COLUMN_MAP[feature],
                    "exact_adapter_gap": "",
                }
            )
        elif feature == "current_ppv8_gap":
            rows.append(
                {
                    "feature": feature,
                    "service_runtime_status": "computable",
                    "service_source": "current_70_30 - ppv8_defensive",
                    "exact_adapter_gap": "",
                }
            )
        else:
            status = "resolved_by_runtime_artifact" if runtime_ready else "missing_for_exact"
            rows.append(
                {
                    "feature": feature,
                    "service_runtime_status": status,
                    "service_source": (
                        "models/track6/warm_wmin8_exact_runtime_candidate"
                        if runtime_ready
                        else ""
                    ),
                    "exact_adapter_gap": (
                        ""
                        if runtime_ready
                        else MISSING_EXACT_RUNTIME_INPUTS.get(feature, "Missing exact runtime source.")
                    ),
                }
            )
    return rows


def coefficient_status(runtime_ready: bool) -> dict[str, Any]:
    if not WMIN7_COEFFICIENTS.exists():
        return {"exists": False}
    coef = pd.read_csv(WMIN7_COEFFICIENTS)
    needed = ["min1_w700_huber_refit_partial", "min1_w850_huber_refit_partial"]
    rows = {}
    for label in needed:
        subset = coef[coef["candidate_label"].eq(label)]
        rows[label] = {
            "coefficient_rows": int(len(subset)),
            "features": sorted(subset["feature"].astype(str).tolist()),
            "has_scaled_coefficients": bool(len(subset) > 0 and "coefficient_on_scaled_feature" in subset.columns),
            "has_intercept": "intercept" in subset.columns,
            "has_imputer_median": False,
            "has_scaler_mean_std": False,
            "exact_replay_status": (
                "resolved_by_serialized_pipeline"
                if runtime_ready
                else "insufficient_without_serialized_pipeline"
            ),
        }
    return {
        "exists": True,
        "path": str(WMIN7_COEFFICIENTS.relative_to(REPO)),
        "candidate_status": rows,
    }


def build_payload() -> dict[str, Any]:
    manifest = load_json(WMIN8_MANIFEST)
    policy = load_json(WMIN8_POLICY)
    exact_runtime = load_json(WMIN8_EXACT_RUNTIME)
    runtime_ready = exact_runtime_ready(exact_runtime)
    gate = selected_gate()
    features = huber_feature_status(runtime_ready)
    missing_features = [row for row in features if row["service_runtime_status"] == "missing_for_exact"]
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "decision": "exact_wmin8_runtime_candidate_connected" if runtime_ready else "exact_wmin8_adapter_not_ready",
        "reason": (
            "WMIN8 missing upstream values are now supplied by the packaged exact runtime candidate. "
            "The remaining validation item is fixed-test parity through the official API endpoint."
            if runtime_ready
            else "WMIN8 route gate can be reproduced from service runtime columns after base/alternative predictions exist, "
            "but exact base/alternative Huber refit predictions require upstream shrinkage outputs and serialized "
            "Huber pipelines that are not currently packaged as runtime artifacts."
        ),
        "selected_candidate": manifest.get("selected_candidate_label"),
        "source_experiment": manifest.get("source_experiment"),
        "artifact_files": {
            "manifest": file_status(WMIN8_MANIFEST),
            "policy": file_status(WMIN8_POLICY),
            "wmin7_coefficients": file_status(WMIN7_COEFFICIENTS),
            "wmin8_gate_audit": file_status(WMIN8_GATE_AUDIT),
            "wmin8_exact_runtime": file_status(WMIN8_EXACT_RUNTIME),
        },
        "exact_runtime_ready": runtime_ready,
        "exact_runtime_parity": exact_runtime.get("huber_pipeline_parity", {}) if exact_runtime else {},
        "route_policy": policy.get("warm_route_policy", {}),
        "selected_gate": gate,
        "service_feature_status": features,
        "missing_exact_feature_count": len(missing_features),
        "missing_exact_features": missing_features,
        "coefficient_status": coefficient_status(runtime_ready),
        "can_validate_now": {
            "warm_lite_api_boundary": True,
            "wmin8_artifact_status_endpoint": True,
            "wmin8_gate_rule_definition": bool(gate),
            "wmin8_exact_fixed_test_parity": False,
        },
        "next_required_artifacts": (
            [
                "Fixed-test parity script comparing API exact WMIN8 predictions with experiments/track6/PP-WMIN8 outputs.",
                "If row-level differences remain, align service feature construction with the original WMIN8 candidate_predictions columns.",
            ]
            if runtime_ready
            else [
                "Serialized WMIN3/WMIN7 validation-trained Huber pipelines for min1_huber_refit_partial and min1_w850_huber_refit_partial.",
                "Runtime package for upstream shrunk comparable prior and shrunk Huber refit outputs.",
                "Exact WMIN8 adapter function that builds base and alternative predictions from raw service input.",
                "Fixed-test parity script comparing API exact WMIN8 predictions with experiments/track6/PP-WMIN8 outputs.",
            ]
        ),
    }
    return payload


def markdown_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in cols) + " |")
    return "\n".join(lines)


def write_docs(payload: dict[str, Any]) -> None:
    DOC_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Official v0.1 WMIN8 Exact Adapter Gap Audit",
        "",
        f"- Created at: {payload['created_at']}",
        f"- Decision: `{payload['decision']}`",
        f"- Selected candidate: `{payload.get('selected_candidate')}`",
        f"- Source experiment: `{payload.get('source_experiment')}`",
        "",
        "## 1. Summary",
        "",
        f"- {payload['reason']}",
        "- Warm-lite API boundary and deterministic repeat are already validated.",
        "- WMIN8 selected target is exposed in the model-status endpoint.",
        "- WMIN8 5+ Warm API output uses the packaged WMIN8 runtime adapter when `exact_runtime_ready=true`.",
        "",
        "## 2. Selected Gate",
        "",
        markdown_table([payload["selected_gate"]], ["candidate_label", "base_candidate", "alternative_candidate", "gate_kind", "threshold", "gap", "validation_route_share", "test_route_share"]),
        "",
        "## 3. Service Feature Readiness",
        "",
        markdown_table(payload["service_feature_status"], ["feature", "service_runtime_status", "service_source", "exact_adapter_gap"]),
        "",
        "## 4. Coefficient Artifact Readiness",
        "",
        "- WMIN7 coefficient CSV exists, but it stores coefficients on scaled features only.",
        "- Exact replay is supplied by serialized Huber pipelines in `models/track6/warm_wmin8_exact_runtime_candidate` when `exact_runtime_ready=true`.",
        "",
        "## 5. Required Next Work",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["next_required_artifacts"])
    DOC_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    payload = build_payload()
    write_docs(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
