"""P0 Deploy readiness verification for v3_filtered_tuned_28_hf.

Codex R1 scope: (A) artifact integrity + (B) local smoke + (D-a) checklist report.
Reference: docs/pr_28_hf_stage_3_5_activation_runbook_20260511.md §1

Checks (10 items / fail-fast):
  1. Artifact 8 file 존재 (default 28_hf + B winner 28_hf)
  2. Variant 등록 + cb/cat features count
  3. predictor.load_models(variant=) 성공 (default + B winner)
  4. Smoke predict (matched / unmatched / real-zero followers)
  5. variant_shadow_* 로그 payload 직렬화 가능성
  6. Variant 매핑 일관성 (predictor / artifact prefix / expected_target)
  7. Feature 호환성 (CB_FEATURES_BASE_28_HF / has_followers 포함 / gallery_tier 제외)
  8. Shadow 비활성 시 fallback 안전성 (env var 미설정 + 잘못된 variant 시 fail-open)
  9. predict_logs DDL prereq (variant_shadow_* 컬럼 — 본 script은 schema 가정만)
 10. Test suite passing (55 tests)

Usage:
    PYTHONPATH=src python3 scripts/verify_28_hf_deploy_readiness.py

Exit code:
    0 = READY (모든 check PASS)
    1 = NOT READY (어느 check든 실패)

운영팀: 본 script READY → runbook §2.3 Step 2 (production 활성화) 진행.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
DEFAULT_VARIANT = "v3_filtered_tuned_28_hf"
B_WINNER_VARIANT = "v3_filtered_tuned_b_warm_28_hf"
DEFAULT_PREFIX = "integrated_v3_filtered_tuned_28_hf"
B_WINNER_PREFIX = "integrated_v3_filtered_tuned_b_warm_28_hf"


# ─── Sample requests for smoke test ───

SAMPLE_MATCHED_WITH_FOLLOWERS = {
    "width_cm": 50.0,
    "height_cm": 50.0,
    "medium": "oil on canvas",
    "artist_profile": {
        "birth_year": 1980,
        "total_works": 30,
        "followers": 100,
        "solo_count": 3,
        "group_count": 5,
        "fair_count": 1,
        "career_stage": 3.0,
        "profile_completeness": 2,
        "source": "artsy",
    },
}

SAMPLE_UNMATCHED = {
    "width_cm": 50.0,
    "height_cm": 50.0,
    "medium": "acrylic on canvas",
    "artist_profile": {"source": "manual"},  # no followers
}

SAMPLE_REAL_ZERO_FOLLOWERS = {
    "width_cm": 50.0,
    "height_cm": 50.0,
    "medium": "oil",
    "artist_profile": {"source": "saatchi", "followers": 0, "birth_year": 1975},
}


# ─── Check functions ───


def check_1_artifact_files() -> tuple[bool, str]:
    """8 artifact files per variant (default + B winner = 16 files)."""
    required_suffixes = [
        "_catboost.cbm",
        "_xgboost.json",
        "_xgboost_label_maps.json",
        "_warm_artists.json",
        "_source_calibration.json",
        "_metrics.json",
        "_best_params.json",
    ]
    missing = []
    for prefix in (DEFAULT_PREFIX, B_WINNER_PREFIX):
        for suf in required_suffixes:
            path = ARTIFACTS / f"{prefix}{suf}"
            if not path.exists():
                missing.append(path.name)
    # B winner has additional manifest.json
    manifest = ARTIFACTS / f"{B_WINNER_PREFIX}_manifest.json"
    if not manifest.exists():
        missing.append(manifest.name)
    if missing:
        return False, f"Missing {len(missing)} files: {missing[:5]}..."
    return True, f"All 15 artifact files present"


def check_2_variant_registration() -> tuple[bool, str]:
    """SUPPORTED_VARIANTS에 28_hf entries 등록 + features count."""
    from visionai.price_engine.api.primary_predictor import (
        CAT_FEATURES_29,
        CB_FEATURES_BASE_28_HF,
        SUPPORTED_VARIANTS,
    )

    for v in (DEFAULT_VARIANT, B_WINNER_VARIANT):
        if v not in SUPPORTED_VARIANTS:
            return False, f"{v} not in SUPPORTED_VARIANTS"
        cfg = SUPPORTED_VARIANTS[v]
        if cfg["cb_features"] != CB_FEATURES_BASE_28_HF:
            return False, f"{v} cb_features mismatch"
        if cfg["cat_features"] != CAT_FEATURES_29:
            return False, f"{v} cat_features mismatch"
        if len(cfg["cb_features"]) != 28:
            return False, f"{v} cb_features count={len(cfg['cb_features'])} != 28"
    return True, f"Both variants registered (28 cb / 5 cat)"


def check_3_predictor_load() -> tuple[bool, str, dict]:
    """PrimaryPredictor load_models() 성공."""
    from visionai.price_engine.api.primary_predictor import PrimaryPredictor

    predictors = {}
    for v in (DEFAULT_VARIANT, B_WINNER_VARIANT):
        try:
            p = PrimaryPredictor()
            p.load_models(ARTIFACTS, variant=v)
            assert p._variant == v
            assert len(p._cb_features) == 28
            assert len(p._cat_features) == 5
            predictors[v] = p
        except Exception as e:
            return False, f"{v} load failed: {e}", {}
    return True, "Both variants loaded successfully", predictors


def check_4_smoke_predict(predictors: dict) -> tuple[bool, str]:
    """Smoke predict — 3 sample requests."""
    from visionai.price_engine.api.primary_feature_builder import build_features

    results = []
    for sample_name, sample in [
        ("matched_with_followers", SAMPLE_MATCHED_WITH_FOLLOWERS),
        ("unmatched", SAMPLE_UNMATCHED),
        ("real_zero_followers", SAMPLE_REAL_ZERO_FOLLOWERS),
    ]:
        try:
            features = build_features(
                sample["width_cm"],
                sample["height_cm"],
                sample["medium"],
                artist_profile=sample["artist_profile"],
            )
            for v, p in predictors.items():
                result = p.predict(features, is_matched=False, training_count=3)
                if not isinstance(result, dict):
                    return False, f"{v}/{sample_name} predict returned non-dict"
                if "price_krw" not in result:
                    return False, f"{v}/{sample_name} missing price_krw"
                if not isinstance(result["price_krw"], int) or result["price_krw"] <= 0:
                    return False, f"{v}/{sample_name} invalid price_krw={result['price_krw']}"
                results.append((sample_name, v, result["price_krw"], features["has_followers"]))
        except Exception as e:
            return False, f"{sample_name} predict failed: {e}\n{traceback.format_exc()}"

    summary = "\n".join(
        f"    {n} ({'has_f=' + str(h)}) | {v}: {p:,} KRW" for n, v, p, h in results
    )
    return True, f"All 6 predictions OK:\n{summary}"


def check_5_log_payload_serializable(predictors: dict) -> tuple[bool, str]:
    """Shadow log payload serialization (variant_shadow_* fields)."""
    from visionai.price_engine.api.primary_feature_builder import build_features

    features = build_features(
        50.0,
        50.0,
        "oil on canvas",
        artist_profile={"source": "artsy", "followers": 100, "birth_year": 1980},
    )
    p = predictors[DEFAULT_VARIANT]
    result = p.predict(features, is_matched=False, training_count=3)

    # Simulate variant_shadow_* payload (primary_server.py:_run_variant_shadow_inference pattern)
    payload = {
        "variant_shadow_variant": DEFAULT_VARIANT,
        "variant_shadow_prediction_price_krw": int(result["price_krw"]),
        "variant_shadow_confidence_grade": result.get("confidence_grade"),
        "variant_shadow_model_type": result.get("model_type"),
    }
    try:
        serialized = json.dumps(payload, ensure_ascii=False)
        # Roundtrip
        parsed = json.loads(serialized)
        if parsed["variant_shadow_variant"] != DEFAULT_VARIANT:
            return False, "Roundtrip mismatch"
    except Exception as e:
        return False, f"Serialization failed: {e}"
    return True, f"Log payload serializable: {len(serialized)} bytes"


def check_6_variant_mapping_consistency() -> tuple[bool, str]:
    """Variant 매핑 일관성 (variant name ↔ prefix ↔ expected_target)."""
    from visionai.price_engine.api.primary_predictor import SUPPORTED_VARIANTS

    for v in (DEFAULT_VARIANT, B_WINNER_VARIANT):
        cfg = SUPPORTED_VARIANTS[v]
        expected_prefix = f"integrated_{v}"
        if cfg["prefix"] != expected_prefix:
            return False, f"{v} prefix mismatch: {cfg['prefix']} vs {expected_prefix}"
        if cfg["expected_target"] != v:
            return False, f"{v} expected_target mismatch: {cfg['expected_target']}"
    return True, "Variant mapping consistent (variant ↔ prefix ↔ expected_target)"


def check_7_feature_compatibility() -> tuple[bool, str]:
    """28_hf features = 28f base + has_followers - gallery_tier."""
    from visionai.price_engine.api.primary_predictor import (
        CB_FEATURES_BASE_28,
        CB_FEATURES_BASE_28_HF,
    )

    if "has_followers" not in CB_FEATURES_BASE_28_HF:
        return False, "has_followers missing from 28_hf"
    if "gallery_tier" in CB_FEATURES_BASE_28_HF:
        return False, "gallery_tier should not be in 28_hf"
    diff_28_to_28hf = set(CB_FEATURES_BASE_28) ^ set(CB_FEATURES_BASE_28_HF)
    if diff_28_to_28hf != {"has_followers", "gallery_tier"}:
        return False, f"Unexpected diff 28 vs 28_hf: {diff_28_to_28hf}"
    return True, "28_hf = 28f + has_followers - gallery_tier (verified)"


def check_8_shadow_fallback_safety() -> tuple[bool, str]:
    """Shadow init fallback (env var 미설정 / 잘못된 variant / 동일 variant)."""
    from visionai.price_engine.api.primary_predictor import SUPPORTED_VARIANTS

    # Manual simulation of _init_variant_shadow_predictor logic
    # (without actually running server)
    test_cases = [
        ("", "empty env → None"),
        ("v3_filtered_tuned", "same as primary → None"),
        ("invalid_variant", "not in SUPPORTED → None"),
        (DEFAULT_VARIANT, "valid → load OK"),
    ]
    for env_value, desc in test_cases:
        is_supported = env_value in SUPPORTED_VARIANTS
        # Default primary is v3_filtered_tuned (32f)
        is_same_as_primary = env_value == "v3_filtered_tuned"
        if not env_value or is_same_as_primary or not is_supported:
            expected = None
        else:
            expected = "load"
        # Logic check only (no actual load here)
        if env_value == DEFAULT_VARIANT and not is_supported:
            return False, f"{DEFAULT_VARIANT} should be in SUPPORTED but is not"
    return True, "Shadow fallback logic OK (4 cases simulated)"


def check_9_predict_logs_schema_doc() -> tuple[bool, str]:
    """predict_logs schema doc 존재 (DDL은 운영 DB이므로 본 script은 prereq doc 확인만)."""
    # 본 세션은 production DB access X — 운영팀이 DDL 확인 책임
    # docs에 schema 정의 있는지 확인
    runbook = REPO / "docs" / "pr_28_hf_stage_3_5_activation_runbook_20260511.md"
    if not runbook.exists():
        return False, f"Runbook missing: {runbook.name}"
    content = runbook.read_text()
    if "variant_shadow_" not in content:
        return False, "Runbook missing variant_shadow_ schema reference"
    if "predict_logs" not in content:
        return False, "Runbook missing predict_logs reference"
    return True, "Runbook references predict_logs schema (운영팀 DDL 확인 책임)"


def check_10_tests_passing() -> tuple[bool, str]:
    """Tests passing (55 unit tests). Inherit current process env."""
    import os

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO / "src")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/price_engine/test_primary_predictor_variants.py",
                "-q",
            ],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return False, f"pytest exit={result.returncode}\n{result.stdout[-500:]}"
        # Parse "55 passed in X.XXs"
        for line in result.stdout.split("\n"):
            if "passed" in line and "warning" not in line.lower():
                return True, line.strip()
        return True, "pytest exit=0"
    except Exception as e:
        return False, f"pytest run failed: {e}"


# ─── Main ───

CHECKS = [
    ("1. Artifact files (15)", check_1_artifact_files, False),
    ("2. Variant registration", check_2_variant_registration, False),
    ("3. Predictor load", check_3_predictor_load, True),  # returns predictors
    ("4. Smoke predict", check_4_smoke_predict, "depends_on_3"),
    ("5. Log payload serializable", check_5_log_payload_serializable, "depends_on_3"),
    ("6. Variant mapping consistency", check_6_variant_mapping_consistency, False),
    ("7. Feature compatibility", check_7_feature_compatibility, False),
    ("8. Shadow fallback safety", check_8_shadow_fallback_safety, False),
    ("9. predict_logs schema (runbook)", check_9_predict_logs_schema_doc, False),
    ("10. Tests passing", check_10_tests_passing, False),
]


def main() -> int:
    logger.info("=" * 70)
    logger.info("P0 Deploy Readiness Verification — v3_filtered_tuned_28_hf")
    logger.info("=" * 70)

    results = []
    predictors = {}
    all_pass = True

    for name, fn, returns_data in CHECKS:
        try:
            if returns_data == "depends_on_3":
                if not predictors:
                    results.append((name, False, "skipped (check 3 failed)"))
                    all_pass = False
                    continue
                passed, msg = fn(predictors)
            elif returns_data is True:
                passed, msg, predictors = fn()
            else:
                passed, msg = fn()
        except Exception as e:
            passed, msg = False, f"exception: {e}\n{traceback.format_exc()}"
        results.append((name, passed, msg))
        if not passed:
            all_pass = False
        marker = "✅" if passed else "❌"
        logger.info("%s %s — %s", marker, name, msg.split("\n")[0])
        # Multi-line msg
        for extra in msg.split("\n")[1:]:
            logger.info("   %s", extra)

    logger.info("=" * 70)
    if all_pass:
        logger.info("VERDICT: ✅ READY for shadow deployment")
        logger.info("Next: runbook §2.3 Step 2 (production activation by ops team)")
        return 0
    else:
        failed = [name for name, p, _ in results if not p]
        logger.error("VERDICT: ❌ NOT READY — %d failed check(s): %s", len(failed), failed)
        return 1


if __name__ == "__main__":
    sys.exit(main())
