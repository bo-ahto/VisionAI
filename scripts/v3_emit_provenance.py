"""Retroactive provenance manifest 생성.

현재 production artifact + v3 진단 산출물에 대해 공통 provenance manifest 를 생성하여
정부 R&D / 협력사 제출 시 재현성 메타데이터를 첨부할 수 있게 한다.

산출:
    model_test_results/integrated_v3_filtered_tuned.provenance.json
        - production model 5개 artifact + best_params + metrics + source_calibration
    model_test_results/v3_diagnostics/v3_diagnostics.provenance.json
        - v3.0 Group 1 진단 산출물 전체 (JSON + PNG + npz)

Usage:
    PYTHONPATH=src python3 scripts/v3_emit_provenance.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from visionai.price_engine._provenance import (
    _provenance_dict,
    write_provenance_manifest,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
DATA_DIR = ROOT / "data"


def _emit_production_manifest() -> Path:
    artifact_paths = {
        "catboost_cbm": OUT_DIR / "integrated_v3_filtered_tuned_catboost.cbm",
        "xgboost_json": OUT_DIR / "integrated_v3_filtered_tuned_xgboost.json",
        "xgboost_label_maps": OUT_DIR / "integrated_v3_filtered_tuned_xgboost_label_maps.json",
        "warm_artists": OUT_DIR / "integrated_v3_filtered_tuned_warm_artists.json",
        "source_calibration": OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json",
        "best_params": OUT_DIR / "integrated_v3_filtered_tuned_best_params.json",
        "metrics": OUT_DIR / "integrated_v3_filtered_tuned_metrics.json",
    }
    data_paths = {
        "artsy_dataset": DATA_DIR / "primary_market_dataset.parquet",
        "saatchi_cleaned": DATA_DIR / "saatchi_cleaned.parquet",
        "data_version_file": DATA_DIR / "VERSION",
    }
    payload = _provenance_dict(
        model_target="integrated_v3_filtered_tuned",
        data_paths=data_paths,
        artifact_paths=artifact_paths,
        extra={
            "scope": "production primary-market model + calibration + tuning artifacts",
            "note": (
                "Retroactive provenance — original artifacts produced 2026-04-28 "
                "(tune_primary_market_v3_filtered.py + calibrate_source_bias.py). "
                "git_sha 는 본 manifest 생성 시점 HEAD."
            ),
        },
    )
    out = OUT_DIR / "integrated_v3_filtered_tuned.provenance.json"
    write_provenance_manifest(out, payload=payload)
    logger.info("manifest 저장: %s", out)
    return out


def _emit_diagnostics_manifest() -> Path:
    artifact_paths: dict[str, Path] = {}
    if DIAG_DIR.exists():
        for p in sorted(DIAG_DIR.iterdir()):
            # Codex Phase 1 P2: exclude provenance manifests themselves to avoid
            # self-referential stale hashes on reruns.
            if p.is_file() and not p.name.endswith(".provenance.json"):
                artifact_paths[p.name] = p
    data_paths = {
        "artsy_dataset": DATA_DIR / "primary_market_dataset.parquet",
        "saatchi_cleaned": DATA_DIR / "saatchi_cleaned.parquet",
        "data_version_file": DATA_DIR / "VERSION",
        # production model artifacts 의존 (cell calibration 적용 위해)
        "production_calibration": OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json",
        "production_best_params": OUT_DIR / "integrated_v3_filtered_tuned_best_params.json",
    }
    payload = _provenance_dict(
        model_target="v3_diagnostics_group_1",
        data_paths=data_paths,
        artifact_paths=artifact_paths,
        extra={
            "scope": (
                "v3.0 Group 1 (분석·통계 보강) 산출물 전체 — Bootstrap CI, "
                "source flip stats, learning curve, baseline comparison, "
                "calibration plot, residual analysis, LOO gallery/medium, "
                "time-axis feasibility report."
            ),
            "n_artifacts": len(artifact_paths),
        },
    )
    out = DIAG_DIR / "v3_diagnostics.provenance.json"
    write_provenance_manifest(out, payload=payload)
    logger.info("manifest 저장: %s", out)
    return out


def main() -> None:
    p1 = _emit_production_manifest()
    p2 = _emit_diagnostics_manifest()
    print("\n=== Provenance manifests 생성 완료 ===")
    print(f"  production: {p1}")
    print(f"  diagnostics: {p2}")
    print("\n각 manifest 는 다음을 포함합니다:")
    print("  - git_sha (현재 HEAD)")
    print("  - data_hashes (parquet 입력 + data/VERSION)")
    print("  - artifact_hashes (산출물 sha256)")
    print("  - dependency_versions (catboost / xgboost / sklearn 등)")
    print("  - parser_rule_version (primary_medium_parser + 시트 결합 해시)")
    print("  - created_at_utc")


if __name__ == "__main__":
    main()
