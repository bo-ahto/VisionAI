"""PR2B bundle integrity tests.

Source-conditional bundle (Artsy + Saatchi) artifact 정합 + Dockerfile copy
contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS = REPO_ROOT / "model_test_results"
DOCKERFILE = REPO_ROOT / "Dockerfile.api"

SOURCES = ["artsy", "saatchi"]
BUNDLE_FILES = [
    "catboost.cbm",
    "xgboost.json",
    "xgboost_label_maps.json",
    "warm_artists.json",
    "source_calibration.json",
    "metrics.json",
]


@pytest.mark.parametrize("source", SOURCES)
def test_bundle_files_exist(source: str):
    """Per-source bundle 영역 의 의무 영역 의 의무 6 file 영역 의 의무 영역 의 의무 영역."""
    for fname in BUNDLE_FILES:
        path = ARTIFACTS / f"source_conditional_v1_{source}_{fname}"
        assert path.exists(), f"Missing bundle file: {path.name}"


@pytest.mark.parametrize("source", SOURCES)
def test_warm_artists_schema(source: str):
    """warm_artists.json schema (loader 정합)."""
    path = ARTIFACTS / f"source_conditional_v1_{source}_warm_artists.json"
    data = json.loads(path.read_text())
    assert "warm_artist_slugs" in data
    assert isinstance(data["warm_artist_slugs"], list)
    assert "n_artists" in data
    assert "min_count" in data
    assert data["min_count"] == 5
    assert data.get("source") == source


@pytest.mark.parametrize("source", SOURCES)
def test_source_calibration_no_op_schema(source: str):
    """No-op calibration: cold_factors / warm_factors 모두 1.0 / loader schema 정합."""
    path = ARTIFACTS / f"source_conditional_v1_{source}_source_calibration.json"
    data = json.loads(path.read_text())
    assert data["version"].startswith("v1-source-conditional-noop")
    assert data["model_target"] == f"source_conditional_v1_{source}"
    cold = data["cold_factors"]
    warm = data["warm_factors"]
    assert isinstance(cold, dict)
    assert isinstance(warm, dict)
    assert all(v == 1.0 for v in cold.values()), f"cold_factors not no-op: {cold}"
    assert all(v == 1.0 for v in warm.values()), f"warm_factors not no-op: {warm}"

    # Per-source cells
    if source == "artsy":
        assert set(cold.keys()) == {"artsy_gallery", "artsy_online"}
    else:
        assert set(cold.keys()) == {"saatchi_online"}


@pytest.mark.parametrize("source", SOURCES)
def test_provenance_sibling_files_exist(source: str):
    """Per-artifact provenance sibling (helper 규약)."""
    for artifact in ["catboost.cbm", "xgboost.json", "source_calibration.json"]:
        prov = ARTIFACTS / f"source_conditional_v1_{source}_{artifact}.provenance.json"
        assert prov.exists(), f"Missing provenance: {prov.name}"
        data = json.loads(prov.read_text())
        assert data["model_target"] == f"source_conditional_v1_{source}"
        assert "artifact_hashes" in data
        assert data["artifact_hashes"]["main"]["sha256"] is not None


def test_dockerfile_includes_source_conditional_bundles():
    """Dockerfile.api 영역 source_conditional_v1 bundle 12 file 영역 의 의무 의무."""
    dockerfile = DOCKERFILE.read_text()
    for source in SOURCES:
        for fname in BUNDLE_FILES:
            artifact = f"source_conditional_v1_{source}_{fname}"
            assert artifact in dockerfile, f"Missing in Dockerfile.api: {artifact}"


def test_dockerfile_default_router_mode_off():
    """Dockerfile env default = SOURCE_ROUTER_MODE=off (backward compat)."""
    dockerfile = DOCKERFILE.read_text()
    assert "ENV SOURCE_ROUTER_MODE=off" in dockerfile
    assert "ENV SOURCE_ROUTER_PERCENT=0" in dockerfile
    assert "ENV SOURCE_ROUTER_RULE_VERSION=v1" in dockerfile


def test_artsy_warm_count_matches_expected():
    """PR1 산출 = Artsy 409 warm artists."""
    data = json.loads((ARTIFACTS / "source_conditional_v1_artsy_warm_artists.json").read_text())
    assert data["n_artists"] == 409


def test_saatchi_warm_count_matches_expected():
    """PR1 산출 = Saatchi 521 warm artists."""
    data = json.loads((ARTIFACTS / "source_conditional_v1_saatchi_warm_artists.json").read_text())
    assert data["n_artists"] == 521
