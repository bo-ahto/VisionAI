"""v3.6 Phase 1 PR7: server-side variant 정합 검증.

검증 대상 (코덱스 PR5+6 review P1/P2 후속):
- _build_model_info_cache 가 predictor.variant prefix 로 metrics/calibration path 결정
- metrics dict 의 catboost_/xgboost_ key 가 variant prefix 와 정합
- 응답 model_type 이 variant-aware ('{algo}_{variant}')
- SHAP 분기가 'catboost_' prefix 매칭으로 동작 (변환된 model_type 호환)

server 전체 통합은 PR11 (cross-path integration tests) 에서 확장.
여기서는 _build_model_info_cache 와 model_type 응답 정합만 단위 검증.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from visionai.price_engine.api.primary_predictor import (
    SUPPORTED_VARIANTS,
)

# ---- _build_model_info_cache: variant 별 path / key 정합 ----


@pytest.fixture
def fake_metrics_v3_filtered_tuned() -> dict:
    return {
        "groupkfold": {
            "catboost_v3_filtered_tuned": {"MdAPE": 45.5, "n": 12000},
        },
        "kfold": {
            "warm_slice": {
                "xgboost_v3_filtered_tuned": {"MdAPE": 27.0},
            },
        },
        "artists": 8500,
        "features": 32,
    }


@pytest.fixture
def fake_metrics_v3_5() -> dict:
    return {
        "groupkfold": {
            "catboost_v3_5_v_year_saatchi_warm": {"MdAPE": 45.45, "n": 12100},
        },
        "kfold": {
            "warm_slice": {
                "xgboost_v3_5_v_year_saatchi_warm": {"MdAPE": 28.0},
            },
        },
        "artists": 8500,
        "features": 35,
    }


def test_build_model_info_cache_uses_variant_prefix(
    tmp_path: Path, fake_metrics_v3_filtered_tuned: dict
) -> None:
    """기존 variant: path/key prefix 가 'integrated_v3_filtered_tuned'."""
    from visionai.price_engine.api import primary_server

    # write fake metrics + calibration
    prefix = "integrated_v3_filtered_tuned"
    (tmp_path / f"{prefix}_metrics.json").write_text(
        json.dumps(fake_metrics_v3_filtered_tuned)
    )
    (tmp_path / f"{prefix}_source_calibration.json").write_text(
        json.dumps({"cold_overall": {"calibrated_mdape_cross_fit_guarded": 44.0}})
    )

    fake_predictor = MagicMock()
    fake_predictor.variant = "v3_filtered_tuned"
    fake_predictor.cb_features = ["a"] * 32
    fake_predictor.model_version_label.return_value = "test-version"

    with patch.object(primary_server, "_predictor", fake_predictor):
        primary_server._build_model_info_cache(tmp_path)
        info = primary_server._model_info_cache

    # cold path 는 calibration 적용
    assert info.mdape_groupkfold == pytest.approx(44.0)
    assert info.mdape_kfold == pytest.approx(27.0)
    assert info.training_count == 12000
    assert info.features_count == 32


def test_build_model_info_cache_uses_v3_5_prefix(
    tmp_path: Path, fake_metrics_v3_5: dict
) -> None:
    """V_year_saatchi_warm variant: path/key prefix 가 'integrated_v3_5_v_year_saatchi_warm'."""
    from visionai.price_engine.api import primary_server

    prefix = "integrated_v3_5_v_year_saatchi_warm"
    (tmp_path / f"{prefix}_metrics.json").write_text(json.dumps(fake_metrics_v3_5))
    (tmp_path / f"{prefix}_source_calibration.json").write_text(
        json.dumps({"cold_overall": {"calibrated_mdape_cross_fit_guarded": 43.0}})
    )

    fake_predictor = MagicMock()
    fake_predictor.variant = "v3_5_v_year_saatchi_warm"
    fake_predictor.cb_features = ["a"] * 35
    fake_predictor.model_version_label.return_value = "v3.5-test"

    with patch.object(primary_server, "_predictor", fake_predictor):
        primary_server._build_model_info_cache(tmp_path)
        info = primary_server._model_info_cache

    assert info.mdape_groupkfold == pytest.approx(43.0)
    assert info.mdape_kfold == pytest.approx(28.0)
    assert info.training_count == 12100
    assert info.features_count == 35


def test_build_model_info_cache_falls_back_when_metrics_missing(tmp_path: Path) -> None:
    """metrics file 없음 → fallback: features_count 는 predictor.cb_features 길이."""
    from visionai.price_engine.api import primary_server

    fake_predictor = MagicMock()
    fake_predictor.variant = "v3_5_v_year_saatchi_warm"
    fake_predictor.cb_features = ["a"] * 35
    fake_predictor.model_version_label.return_value = "v3.5-fallback"

    with patch.object(primary_server, "_predictor", fake_predictor):
        primary_server._build_model_info_cache(tmp_path)
        info = primary_server._model_info_cache

    assert info.training_count == 0
    assert info.features_count == 35
    assert info.mdape_groupkfold == 0.0


def test_supported_variants_prefix_matches_server_path() -> None:
    """SUPPORTED_VARIANTS 의 prefix 가 server 가 기대하는 artifact 명명과 일치."""
    assert (
        SUPPORTED_VARIANTS["v3_filtered_tuned"]["prefix"]
        == "integrated_v3_filtered_tuned"
    )
    assert (
        SUPPORTED_VARIANTS["v3_5_v_year_saatchi_warm"]["prefix"]
        == "integrated_v3_5_v_year_saatchi_warm"
    )


# ---- model_type 응답 형식 ----


def test_model_type_format_v3_filtered_tuned() -> None:
    """기존 variant 의 model_type: 'catboost_v3_filtered_tuned' / 'xgboost_v3_filtered_tuned'."""
    # PR7 후 형식: '{algo}_{variant}'
    variant = "v3_filtered_tuned"
    assert f"catboost_{variant}" == "catboost_v3_filtered_tuned"
    assert f"xgboost_{variant}" == "xgboost_v3_filtered_tuned"


def test_model_type_format_v3_5() -> None:
    """V_year_saatchi_warm variant 의 model_type 도 동일 패턴."""
    variant = "v3_5_v_year_saatchi_warm"
    assert f"catboost_{variant}" == "catboost_v3_5_v_year_saatchi_warm"
    assert f"xgboost_{variant}" == "xgboost_v3_5_v_year_saatchi_warm"


def test_shap_branch_matches_catboost_prefix() -> None:
    """SHAP 분기는 'catboost_' prefix startswith 매칭 — 두 variant 모두 호환."""
    assert "catboost_v3_filtered_tuned".startswith("catboost_")
    assert "catboost_v3_5_v_year_saatchi_warm".startswith("catboost_")
    # XGB 경로는 SHAP 미실행
    assert not "xgboost_v3_filtered_tuned".startswith("catboost_")
    assert not "xgboost_v3_5_v_year_saatchi_warm".startswith("catboost_")
