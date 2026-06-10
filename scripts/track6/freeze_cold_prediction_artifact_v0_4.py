#!/usr/bin/env python3
"""Cold prediction v0.4 동결: 신뢰도 tier/표시/검수 정책 + 미커버 fallback 옵션.

PP-COLD-ARTIFACT4. 점 예측 정책은 v0.3 그대로 두고, 검증 완료된 정책층을 고정한다.

- PP-CCONF1 채택 권고: research tier(qwidth+모델gap+검색커버) 경계/규칙,
  표시 정책(high/medium/low), 2단 검수(v0.3 플래그 OR low tier)
- PP-CSRCH1 보류(목적별): 미커버 작가 상수 delta fallback — 기본 off 옵션으로 포함
- 검증: 정책 적용기가 PP-CCONF1 tier 배정을 정확히 재현하는지(diff 0),
  fallback 모드가 PP-CSRCH1 미커버 시나리오 test 지표를 재현하는지,
  full lookup에서 v0.3 defense와 일치하는지 확인 후 MANIFEST 작성.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.4"
V03 = REPO / "models" / "track6" / "cold_prediction_v0.3"
CBASE = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
CCONF = REPO / "experiments" / "track6" / "PP-CCONF1_cold_confidence_tier_policy"
CSRCH = REPO / "experiments" / "track6" / "PP-CSRCH1_cold_search_delta_generalization"
FREEZE_TS = "2026-06-10T00:00:00"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def metric_triplet(price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95))}


def main() -> None:
    for sub in ("config", "predict", "manifest", "reports", "evidence"):
        (BUNDLE / sub).mkdir(parents=True, exist_ok=True)

    cconf_cfg = json.loads((CCONF / "artifacts" / "run_config.json").read_text(encoding="utf-8"))
    bounds = cconf_cfg["tier_bounds_frozen_from_validation"]
    v03_qw_q67 = json.loads((V03 / "config" / "cold_postprocess_params_v0_3.json")
                            .read_text(encoding="utf-8"))["guard"]["qwidth_q67"]

    # 검색 lookup은 v0.3 동결본을 그대로 복사 (자체 완결 번들)
    shutil.copyfile(V03 / "config" / "search_delta_lookup_v0_3.json",
                    BUNDLE / "config" / "search_delta_lookup_v0_4.json")
    lookup = {str(k): float(v) for k, v in json.loads(
        (BUNDLE / "config" / "search_delta_lookup_v0_4.json").read_text(encoding="utf-8"))["artist_delta"].items()}

    rows = pd.read_csv(CBASE)
    val_artists = rows.loc[rows["split"] == "validation", "artist_key"].astype(str).unique()
    const_delta = float(np.median([lookup[a] for a in val_artists if a in lookup]))

    params = {
        "version": "v0.4",
        "frozen_at": FREEZE_TS,
        "tier_bounds": {"qw_q33": bounds["qw_q33"], "qw_q90": bounds["qw_q90"],
                        "gap_q50": bounds["gap_q50"], "gap_q90": bounds["gap_q90"]},
        "tier_rule": cconf_cfg["tier_rules"]["research"],
        "prohibition": "v0.2 qwidth 단독 tier 제공 금지 (PP-CCONF1: test 역전/과신 확인)",
        "review_flag_v03": {"qwidth_q67": v03_qw_q67, "rule": "qwidth >= q67 OR not covered"},
        "review_two_stage": "review_flag_v03(재현율) OR priority_review(low tier, 정밀)",
        "uncovered_constant_delta": {
            "enabled": False,
            "delta": const_delta,
            "cap": 0.20,
            "evidence": "PP-CSRCH1: holdout MAPE/p95 개선확률 0.97~1.0, MdAPE 0.41~0.46 게이트 미통과",
            "note": "미커버 작가 p95 방어 모드. 기본 off — 서비스 목적(큰 오차 회피)에 따라 활성화",
        },
    }
    (BUNDLE / "config" / "confidence_tier_policy_v0_4.json").write_text(
        json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 검증 1: PP-CCONF1 tier 배정 재현 (diff 0)
    spec = importlib.util.spec_from_file_location(
        "apply_cold_confidence_policy_v0_4", BUNDLE / "predict" / "apply_cold_confidence_policy_v0_4.py")
    pol = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(pol)

    out = pol.apply(rows, params=params, lookup=lookup)
    ref = pd.read_csv(CCONF / "outputs" / "tier_assignments.csv")
    merged = out.merge(ref[["split", "_track6_row_id", "tier_research", "review_flag_v03"]]
                       .rename(columns={"review_flag_v03": "ref_review"}),
                       on=["split", "_track6_row_id"], validate="one_to_one")
    tier_mismatch = int((merged["confidence_tier"] != merged["tier_research"]).sum())
    review_mismatch = int((merged["review_flag_v03"].astype(bool) != merged["ref_review"].astype(bool)).sum())
    if tier_mismatch or review_mismatch:
        raise AssertionError(f"CCONF1 재현 실패: tier {tier_mismatch}행, review {review_mismatch}행")

    # ── 검증 2: fallback 모드 — 미커버 시나리오(빈 lookup)에서 PP-CSRCH1 test 지표 재현
    test = rows[rows["split"] == "test"]
    fb_params = json.loads(json.dumps(params))
    fb_params["uncovered_constant_delta"]["enabled"] = True
    fb_out = pol.apply(test, params=fb_params, lookup={})
    got = metric_triplet(test["actual_price"].to_numpy(dtype=float),
                         fb_out["cold_defense_with_uncovered_fallback_log"].to_numpy(dtype=float))
    ref_csrch = pd.read_csv(CSRCH / "outputs" / "fixed_test_metrics.csv")
    exp_row = ref_csrch[ref_csrch["candidate"] == "const_median_s1.0"].iloc[0]
    fb_diffs = {k: abs(got[k] - float(exp_row[k])) for k in ("MdAPE", "MAPE", "p95_APE")}
    if max(fb_diffs.values()) > 1e-9:
        raise AssertionError(f"CSRCH1 미커버 시나리오 재현 실패: {fb_diffs}")

    # ── 검증 3: full lookup에서 fallback 결과가 v0.3 defense(연구 base)와 일치
    fb_full = pol.apply(test, params=fb_params, lookup=lookup)
    full_diff = float(np.max(np.abs(
        fb_full["cold_defense_with_uncovered_fallback_log"].to_numpy(dtype=float)
        - test["research_base_pred_log"].to_numpy(dtype=float))))
    if full_diff > 1e-9:
        raise AssertionError(f"v0.3 defense 일치 실패: max diff {full_diff}")

    # ── 정책 JSON / evidence / 릴리스 문서
    tier_share_test = out.loc[out["split"] == "test", "confidence_tier"].value_counts(normalize=True)
    policy = {
        "version": "v0.4",
        "name": "cold_prediction_v0.4",
        "status": "confidence_display_policy_freeze",
        "created_at": FREEZE_TS,
        "purpose": "PP-CCONF1 신뢰도 tier/표시/2단 검수 정책 동결 + PP-CSRCH1 미커버 상수 fallback 옵션(기본 off). 점 예측 정책은 v0.3 그대로.",
        "point_prediction": "models/track6/cold_prediction_v0.3 (변경 없음)",
        "tier_metrics_test_research_base": {
            "high": {"share": 0.0823, "MdAPE": 0.3828, "MAPE": 0.6811, "p95_APE": 0.9904},
            "medium": {"share": 0.6260, "MdAPE": 0.3709, "MAPE": 0.9025, "p95_APE": 1.8243},
            "low": {"share": 0.2917, "MdAPE": 0.5549, "MAPE": 0.7824, "p95_APE": 2.9877},
        },
        "tier_share_test_reproduced": {k: float(v) for k, v in tier_share_test.items()},
        "uncovered_fallback_option": {
            "enabled_default": False,
            "delta": const_delta,
            "metrics_test_uncovered_scenario": got,
            "vs_guard_only": {"MdAPE": 0.4178, "MAPE": 0.9640, "p95_APE": 2.5377},
            "vs_true_delta_upper_bound": {"MdAPE": 0.4098, "MAPE": 0.8493, "p95_APE": 2.3465},
        },
        "verification": {"cconf1_tier_mismatch_rows": tier_mismatch,
                         "csrch1_fallback_max_abs_diff": max(fb_diffs.values()),
                         "v03_defense_max_abs_diff": full_diff},
        "prohibitions": ["0604 사용 금지(Warm 시험 제출 전용)", "v0.2 qwidth 단독 tier 제공 금지"],
        "evidence": ["PP-CCONF1", "PP-CSRCH1", "PP-CDIAG1", "PP-PCOLD1", "PP-CBASE1"],
    }
    (BUNDLE / "config" / "cold_model_policy_v0_4.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")

    for src, dst in [
        (CCONF / "outputs" / "tier_metrics.csv", BUNDLE / "evidence" / "PP-CCONF1_tier_metrics.csv"),
        (CSRCH / "outputs" / "fixed_test_metrics.csv", BUNDLE / "evidence" / "PP-CSRCH1_fixed_test_metrics.csv"),
    ]:
        shutil.copyfile(src, dst)

    release = "\n".join([
        "# Cold artifact release v0.4 (confidence/display policy)",
        "",
        f"- 동결일: {FREEZE_TS}",
        "- 점 예측: v0.3 그대로 (guard+search 2단 방어).",
        "- 추가 층: PP-CCONF1 research tier + 표시 정책 + 2단 검수, PP-CSRCH1 미커버 상수 fallback(기본 off).",
        "",
        "## 검증",
        "",
        f"- PP-CCONF1 tier 배정 재현: mismatch {tier_mismatch}행 / review flag mismatch {review_mismatch}행",
        f"- PP-CSRCH1 미커버 시나리오 재현: max abs diff {max(fb_diffs.values()):.2e}",
        f"- full lookup ↔ v0.3 defense 일치: max abs diff {full_diff:.2e}",
        "",
        "## 사용",
        "",
        "- 적용기: `predict/apply_cold_confidence_policy_v0_4.py` (입력: qwidth, y18/v0.2 예측, artist_key)",
        "- fallback 활성화: `confidence_tier_policy_v0_4.json`의 `uncovered_constant_delta.enabled`",
        "- 재생성: `python3 scripts/track6/freeze_cold_prediction_artifact_v0_4.py`",
    ])
    (BUNDLE / "reports" / "cold_artifact_release_v0_4.md").write_text(release, encoding="utf-8")
    (BUNDLE / "README.md").write_text(
        "# Cold prediction v0.4 (confidence/display policy layer)\n\n"
        "PP-CCONF1 신뢰도 tier/표시/검수 정책 동결 + PP-CSRCH1 미커버 상수 fallback 옵션(기본 off).\n"
        "점 예측은 v0.3 그대로.\n\n"
        "재생성: `python3 scripts/track6/freeze_cold_prediction_artifact_v0_4.py`\n"
        "적용기: `predict/apply_cold_confidence_policy_v0_4.py`\n",
        encoding="utf-8")

    files = sorted(p for p in BUNDLE.rglob("*") if p.is_file() and "manifest" not in p.parts)
    (BUNDLE / "manifest" / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(p)}  {p.relative_to(BUNDLE)}" for p in files) + "\n", encoding="utf-8")

    print(f"[ARTIFACT4] tier mismatch: {tier_mismatch}, review mismatch: {review_mismatch}")
    print(f"[ARTIFACT4] csrch1 fallback max diff: {max(fb_diffs.values()):.2e}")
    print(f"[ARTIFACT4] v0.3 defense max diff: {full_diff:.2e}")
    print(f"[ARTIFACT4] const_delta(frozen): {const_delta}")
    print(f"[ARTIFACT4] bundle files: {len(files)}")


if __name__ == "__main__":
    main()
