"""v3.6 Phase 1 PR5+6: predictor variant + bundle + MODEL_VARIANT 단위 테스트.

검증:
- SUPPORTED_VARIANTS 정의
- _resolve_variant: 인자 / env var / default / unknown
- get_cb_features: variant 별 CB_FEATURES list
- CB_FEATURES_BASE 32 + 3 = 35 (V_year_saatchi_warm)
- Backward compat (CB_FEATURES alias = BASE)

Note: load_models 의 실제 file load 는 artifact 가 필요하므로 skip.
v3.5 step 4 monitoring 직전 별도 commit (out of scope §10) 에서 retraining 후
integration test 추가.
"""

from __future__ import annotations

import os

import pytest

from visionai.price_engine.api.primary_predictor import (
    CAT_FEATURES,
    CAT_FEATURES_29,
    CB_FEATURES,
    CB_FEATURES_BASE,
    CB_FEATURES_BASE_29,
    CB_FEATURES_V3_5_V_YEAR_SAATCHI_WARM,
    DEFAULT_VARIANT,
    SUPPORTED_VARIANTS,
    _resolve_variant,
    get_cb_features,
)

# ---- Variant 정의 검증 ----


def test_supported_variants_defined():
    assert "v3_filtered_tuned" in SUPPORTED_VARIANTS
    assert "v3_5_v_year_saatchi_warm" in SUPPORTED_VARIANTS


def test_default_variant_is_v3_filtered_tuned():
    """backward compat: env var 미설정 시 기존 variant 그대로."""
    assert DEFAULT_VARIANT == "v3_filtered_tuned"


def test_v3_filtered_tuned_config():
    cfg = SUPPORTED_VARIANTS["v3_filtered_tuned"]
    assert cfg["prefix"] == "integrated_v3_filtered_tuned"
    assert cfg["expected_target"] == "integrated_v3_filtered_tuned"
    assert cfg["cb_features"] == CB_FEATURES_BASE
    assert len(cfg["cb_features"]) == 32


def test_v3_5_v_year_saatchi_warm_config():
    cfg = SUPPORTED_VARIANTS["v3_5_v_year_saatchi_warm"]
    assert cfg["prefix"] == "integrated_v3_5_v_year_saatchi_warm"
    assert cfg["expected_target"] == "v3_5_v_year_saatchi_warm"
    assert len(cfg["cb_features"]) == 35
    # V_year_saatchi_warm variant 만 year 3종 포함
    assert "year_made" in cfg["cb_features"]
    assert "has_year_made" in cfg["cb_features"]
    assert "work_age" in cfg["cb_features"]


def test_v3_filtered_tuned_b_warm_config():
    """PR-WARM-B: cycle B (3a27002) ADOPT_warm_retuned 운영 적용 variant."""
    cfg = SUPPORTED_VARIANTS["v3_filtered_tuned_b_warm"]
    assert cfg["prefix"] == "integrated_v3_filtered_tuned_b_warm"
    assert cfg["expected_target"] == "v3_filtered_tuned_b_warm"
    # cold path = N=32 그대로 (warm XGB params만 변경)
    assert cfg["cb_features"] == CB_FEATURES_BASE
    assert len(cfg["cb_features"]) == 32


# ---- CB_FEATURES backward compat ----


def test_cb_features_alias_equals_base():
    """v3.6 변경 후에도 기존 import (`from primary_predictor import CB_FEATURES`) 호환."""
    assert CB_FEATURES is CB_FEATURES_BASE
    assert len(CB_FEATURES) == 32


def test_v3_5_features_extends_base():
    """V_year_saatchi_warm 의 features = BASE + 3."""
    assert len(CB_FEATURES_V3_5_V_YEAR_SAATCHI_WARM) == 35
    assert CB_FEATURES_V3_5_V_YEAR_SAATCHI_WARM[:32] == CB_FEATURES_BASE
    assert CB_FEATURES_V3_5_V_YEAR_SAATCHI_WARM[32:] == ["year_made", "has_year_made", "work_age"]


# ---- _resolve_variant ----


def test_resolve_variant_explicit_arg():
    assert _resolve_variant("v3_filtered_tuned") == "v3_filtered_tuned"
    assert _resolve_variant("v3_5_v_year_saatchi_warm") == "v3_5_v_year_saatchi_warm"


def test_resolve_variant_default_when_no_env(monkeypatch):
    monkeypatch.delenv("MODEL_VARIANT", raising=False)
    assert _resolve_variant() == DEFAULT_VARIANT


def test_resolve_variant_env_var(monkeypatch):
    monkeypatch.setenv("MODEL_VARIANT", "v3_5_v_year_saatchi_warm")
    assert _resolve_variant() == "v3_5_v_year_saatchi_warm"


def test_resolve_variant_explicit_overrides_env(monkeypatch):
    """explicit 인자가 env var 보다 우선."""
    monkeypatch.setenv("MODEL_VARIANT", "v3_5_v_year_saatchi_warm")
    assert _resolve_variant("v3_filtered_tuned") == "v3_filtered_tuned"


def test_resolve_variant_unknown_raises():
    with pytest.raises(RuntimeError, match="Unsupported MODEL_VARIANT"):
        _resolve_variant("v_unknown_variant")


def test_resolve_variant_env_unknown_raises(monkeypatch):
    monkeypatch.setenv("MODEL_VARIANT", "v_unknown")
    with pytest.raises(RuntimeError, match="Unsupported MODEL_VARIANT"):
        _resolve_variant()


# ---- get_cb_features ----


def test_get_cb_features_v3_filtered_tuned():
    f = get_cb_features("v3_filtered_tuned")
    assert len(f) == 32
    assert "year_made" not in f


def test_get_cb_features_v3_5():
    f = get_cb_features("v3_5_v_year_saatchi_warm")
    assert len(f) == 35
    assert "year_made" in f


def test_get_cb_features_uses_env_when_no_arg(monkeypatch):
    monkeypatch.setenv("MODEL_VARIANT", "v3_5_v_year_saatchi_warm")
    f = get_cb_features()
    assert len(f) == 35


def test_get_cb_features_unknown_raises():
    with pytest.raises(RuntimeError):
        get_cb_features("v_unknown")


# ---- artifact path prefix consistency (구현 정합 검증) ----


def test_artifact_prefix_pattern_v3_filtered_tuned():
    """v3.5 step 2 §6.5 명시 — 기존 artifact 그대로 사용 가능."""
    cfg = SUPPORTED_VARIANTS["v3_filtered_tuned"]
    expected_files = [
        f"{cfg['prefix']}_catboost.cbm",
        f"{cfg['prefix']}_xgboost.json",
        f"{cfg['prefix']}_warm_artists.json",
        f"{cfg['prefix']}_xgboost_label_maps.json",
        f"{cfg['prefix']}_source_calibration.json",
    ]
    assert expected_files == [
        "integrated_v3_filtered_tuned_catboost.cbm",
        "integrated_v3_filtered_tuned_xgboost.json",
        "integrated_v3_filtered_tuned_warm_artists.json",
        "integrated_v3_filtered_tuned_xgboost_label_maps.json",
        "integrated_v3_filtered_tuned_source_calibration.json",
    ]


def test_artifact_prefix_pattern_v3_5():
    cfg = SUPPORTED_VARIANTS["v3_5_v_year_saatchi_warm"]
    expected_files = [
        f"{cfg['prefix']}_catboost.cbm",
        f"{cfg['prefix']}_xgboost.json",
        f"{cfg['prefix']}_warm_artists.json",
        f"{cfg['prefix']}_xgboost_label_maps.json",
        f"{cfg['prefix']}_source_calibration.json",
    ]
    assert expected_files == [
        "integrated_v3_5_v_year_saatchi_warm_catboost.cbm",
        "integrated_v3_5_v_year_saatchi_warm_xgboost.json",
        "integrated_v3_5_v_year_saatchi_warm_warm_artists.json",
        "integrated_v3_5_v_year_saatchi_warm_xgboost_label_maps.json",
        "integrated_v3_5_v_year_saatchi_warm_source_calibration.json",
    ]


def test_artifact_prefix_pattern_v3_filtered_tuned_b_warm():
    """PR-WARM-B / R3 minor follow-up: bundle naming contract 명시 검증."""
    cfg = SUPPORTED_VARIANTS["v3_filtered_tuned_b_warm"]
    expected_files = [
        f"{cfg['prefix']}_catboost.cbm",
        f"{cfg['prefix']}_xgboost.json",
        f"{cfg['prefix']}_warm_artists.json",
        f"{cfg['prefix']}_xgboost_label_maps.json",
        f"{cfg['prefix']}_source_calibration.json",
    ]
    assert expected_files == [
        "integrated_v3_filtered_tuned_b_warm_catboost.cbm",
        "integrated_v3_filtered_tuned_b_warm_xgboost.json",
        "integrated_v3_filtered_tuned_b_warm_warm_artists.json",
        "integrated_v3_filtered_tuned_b_warm_xgboost_label_maps.json",
        "integrated_v3_filtered_tuned_b_warm_source_calibration.json",
    ]


# ---- model_target 정합 ----


def test_v3_5_model_target_matches_calibration_expectation():
    """v3.5 step 2 §6.5: calibration JSON 의 model_target 이 variant 와 일치 검증."""
    cfg = SUPPORTED_VARIANTS["v3_5_v_year_saatchi_warm"]
    # expected_target 이 variant 명과 일치 (load 시 calibration JSON 의 model_target 검증)
    assert cfg["expected_target"] == "v3_5_v_year_saatchi_warm"


# ---- Module env teardown safety ----


def test_resolve_variant_does_not_leak_env(monkeypatch):
    """monkeypatch 후 env teardown 정상."""
    monkeypatch.setenv("MODEL_VARIANT", "v3_5_v_year_saatchi_warm")
    assert _resolve_variant() == "v3_5_v_year_saatchi_warm"
    monkeypatch.delenv("MODEL_VARIANT")
    assert _resolve_variant() == DEFAULT_VARIANT
    # os.environ 에 잔존 X
    assert "MODEL_VARIANT" not in os.environ


# ---- PR-29F: 29-feature variant (dead 2 + source 제거) ----


def test_cb_features_base_29_count():
    """29 = 32 - 3 (ho_price_level, medium_price_level, source)."""
    assert len(CB_FEATURES_BASE_29) == 29


def test_cb_features_base_29_drops_correct():
    dropped = set(CB_FEATURES_BASE) - set(CB_FEATURES_BASE_29)
    assert dropped == {"ho_price_level", "medium_price_level", "source"}


def test_cat_features_29_count():
    """5 = 6 - 1 (source)."""
    assert len(CAT_FEATURES_29) == 5
    assert "source" not in CAT_FEATURES_29
    # 나머지 5개 동일
    assert set(CAT_FEATURES_29) == set(CAT_FEATURES) - {"source"}


def test_v3_filtered_tuned_29f_config():
    cfg = SUPPORTED_VARIANTS["v3_filtered_tuned_29f"]
    assert cfg["prefix"] == "integrated_v3_filtered_tuned_29f"
    assert cfg["expected_target"] == "v3_filtered_tuned_29f"
    assert cfg["cb_features"] == CB_FEATURES_BASE_29
    assert cfg["cat_features"] == CAT_FEATURES_29
    assert len(cfg["cb_features"]) == 29
    assert len(cfg["cat_features"]) == 5


def test_v3_filtered_tuned_b_warm_29f_config():
    cfg = SUPPORTED_VARIANTS["v3_filtered_tuned_b_warm_29f"]
    assert cfg["prefix"] == "integrated_v3_filtered_tuned_b_warm_29f"
    assert cfg["expected_target"] == "v3_filtered_tuned_b_warm_29f"
    assert cfg["cb_features"] == CB_FEATURES_BASE_29
    assert cfg["cat_features"] == CAT_FEATURES_29


def test_legacy_variants_keep_32f_cat_features():
    """Legacy 5개 variant는 32f / 6 cat — backward compat."""
    for name in (
        "v3_filtered_tuned",
        "v3_5_v_year_saatchi_warm",
        "source_conditional_v1_artsy",
        "source_conditional_v1_saatchi",
        "v3_filtered_tuned_b_warm",
    ):
        cfg = SUPPORTED_VARIANTS[name]
        assert (
            cfg.get("cat_features") == CAT_FEATURES
        ), f"{name}: cat_features != CAT_FEATURES (legacy 6-feature schema)"


def test_resolve_variant_29f_explicit():
    assert _resolve_variant("v3_filtered_tuned_29f") == "v3_filtered_tuned_29f"
    assert _resolve_variant("v3_filtered_tuned_b_warm_29f") == "v3_filtered_tuned_b_warm_29f"


def test_resolve_variant_29f_via_env(monkeypatch):
    monkeypatch.setenv("MODEL_VARIANT", "v3_filtered_tuned_29f")
    assert _resolve_variant() == "v3_filtered_tuned_29f"


def test_get_cb_features_29f():
    assert get_cb_features("v3_filtered_tuned_29f") == CB_FEATURES_BASE_29
    assert get_cb_features("v3_filtered_tuned_b_warm_29f") == CB_FEATURES_BASE_29
    f = get_cb_features("v3_filtered_tuned_29f")
    assert "source" not in f
    assert "ho_price_level" not in f
    assert "medium_price_level" not in f


def test_artifact_prefix_pattern_29f():
    """PR-29F: 신규 artifact bundle naming contract."""
    for name in ("v3_filtered_tuned_29f", "v3_filtered_tuned_b_warm_29f"):
        cfg = SUPPORTED_VARIANTS[name]
        expected_files = [
            f"{cfg['prefix']}_catboost.cbm",
            f"{cfg['prefix']}_xgboost.json",
            f"{cfg['prefix']}_warm_artists.json",
            f"{cfg['prefix']}_xgboost_label_maps.json",
            f"{cfg['prefix']}_source_calibration.json",
        ]
        assert all(f.startswith(cfg["prefix"]) for f in expected_files)
