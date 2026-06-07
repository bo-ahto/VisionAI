#!/usr/bin/env python3
"""Freeze Cold prediction v0.3 (guard + search 2-layer defense) — PP-COLD-ARTIFACT3.

Extends v0.1 (guard) with the PP-COLD-DEFENSE1-validated search layer:
- representative = PP-Y18 qwidth
- defense        = guard (PP-QR4) + per-artist search delta (PP-H28 gallery_museum cap0.2)
- fallback       = uncovered artist -> guard only
- review flag    = low-confidence rows

Builds a frozen per-artist search delta lookup, verifies the shipped post-processor
reproduces the PP-COLD-DEFENSE1 guard_search_gm test metrics, then writes the bundle.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_qr2_cold_quantile_final_candidate_blend as qr2  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.3"
DEFENSE1_DIR = REPO / "experiments" / "track6" / "PP-COLD-DEFENSE1_cold_guard_search_layer_combination"
H28_PRED = REPO / "experiments" / "track6" / "PP-H20_H26_search_feature_expansion" / "outputs" / "candidate_predictions.csv"
FREEZE_TS = "2026-06-07T00:00:00"
SEARCH_SOURCE = "h23_gallery_museum_median_cap0.2"


def metric_triplet(price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pp = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pp - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)), "p95_APE": float(np.quantile(ape, 0.95))}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_postprocessor():
    path = BUNDLE / "predict" / "apply_cold_postprocess_v0_3.py"
    spec = importlib.util.spec_from_file_location("apply_cold_postprocess_v0_3", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    qf = qr2.add_qr1_predictions(qr2.load_y18_frame())
    qf = qf[["split", "_track6_row_id", "actual_price", "quantile_width_log",
             "y18_qwidth_pred_log", "lgb_q40_pred_log", "cat_q40_pred_log", "y2_pred_log", "artist_key"]].copy()
    h = pd.read_csv(H28_PRED, low_memory=False)
    h = h[["split", "_track6_row_id", "pred_log", f"{SEARCH_SOURCE}__pred_log"]]
    m = qf.merge(h, on=["split", "_track6_row_id"], how="inner")
    m["search_delta"] = m[f"{SEARCH_SOURCE}__pred_log"] - m["pred_log"]

    val = m[m["split"] == "validation"]
    test = m[m["split"] == "test"].copy()
    thresholds = qr2.validation_thresholds(val)
    guard_params = {"qwidth_q67": float(thresholds["qwidth_q67"]), "gap_q50": float(thresholds["gap_q50"]), "weight": 0.50}

    # Frozen per-artist search delta lookup (constant within artist; take mean as canonical).
    art_delta = m.groupby("artist_key")["search_delta"].mean()
    lookup = {str(k): float(v) for k, v in art_delta.items()}

    (BUNDLE / "config").mkdir(parents=True, exist_ok=True)
    (BUNDLE / "config" / "search_delta_lookup_v0_3.json").write_text(
        json.dumps({"source": SEARCH_SOURCE, "n_artists": len(lookup), "artist_delta": lookup}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    params = {
        "version": "v0.3",
        "guard": guard_params,
        "search": {"source": SEARCH_SOURCE, "lookup": "config/search_delta_lookup_v0_3.json",
                   "apply": "per-artist additive delta; uncovered artist -> 0 (guard only)"},
        "review_flag": "qwidth >= qwidth_q67 OR artist not covered by search lookup",
    }
    (BUNDLE / "config" / "cold_postprocess_params_v0_3.json").write_text(
        json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")

    # Shipped post-processor on test.
    pp = load_postprocessor()
    test_out = pp.apply(test, params=params, lookup=lookup)
    price = test["actual_price"].to_numpy(dtype=float)
    ship_rep = test_out["cold_representative_pred_log"].to_numpy(dtype=float)
    ship_def = test_out["cold_defense_pred_log"].to_numpy(dtype=float)

    # Independent recompute (guard + delta) for cross-check.
    y18 = test["y18_qwidth_pred_log"].to_numpy(dtype=float)
    lgb = test["lgb_q40_pred_log"].to_numpy(dtype=float)
    qw = test["quantile_width_log"].to_numpy(dtype=float)
    mask = (qw >= guard_params["qwidth_q67"]) & ((y18 - lgb) >= guard_params["gap_q50"]) & (lgb < y18)
    guard = y18.copy(); guard[mask] = 0.5 * y18[mask] + 0.5 * lgb[mask]
    ref_def = guard + test["search_delta"].to_numpy(dtype=float)
    max_diff = float(np.max(np.abs(ship_def - ref_def)))
    if max_diff > 1e-9:
        raise SystemExit(f"FREEZE ABORT: post-processor mismatch (max abs diff {max_diff:.3e})")

    m_rep = metric_triplet(price, ship_rep)
    m_def = metric_triplet(price, ship_def)
    m_guard = metric_triplet(price, guard)

    # Cross-check vs PP-COLD-DEFENSE1 recorded guard_search_gm.
    d1 = pd.read_csv(DEFENSE1_DIR / "outputs" / "test_metrics.csv").set_index("candidate")
    d1_md = float(d1.loc["guard_search_gm", "test_MdAPE"])
    reproduced = abs(m_def["MdAPE"] - d1_md) <= 1e-6

    coverage_test = float(test_out["search_covered"].mean())
    review_rate_test = float(test_out["cold_review_flag"].mean())

    policy = {
        "version": "v0.3",
        "name": "cold_prediction_v0.3",
        "status": "validated_two_layer_defense_freeze",
        "created_at": FREEZE_TS,
        "purpose": "PP-COLD-DEFENSE1이 가산 검증한 guard+search 2단 방어를 작가 lookup fallback + 검수 플래그와 함께 고정.",
        "representative_policy": {"candidate": "component_pp_y18_qwidth_bin", "metrics_test": m_rep,
                                  "note": "대표 점예측은 PP-Y18 유지."},
        "defense_policy": {"layers": ["guard (PP-QR4)", "search per-artist delta (PP-H28 gallery_museum cap0.2)"],
                           "metrics_test": m_def, "guard_only_metrics_test": m_guard,
                           "fallback": "uncovered artist -> guard only",
                           "search_coverage_test": coverage_test,
                           "note": "두 방어 가산적(PP-COLD-DEFENSE1 redundancy gap≈0). 검색층은 분산 추가 → 검수 플래그 동반."},
        "review_flag_policy": {"rule": params["review_flag"], "review_rate_test": review_rate_test},
        "confidence_range_policy": {"display": "참고가 + 넓은 범위 + 낮은 신뢰도. review_flag=True는 수동 검수."},
        "relation": {"v0_1": "guard only (post-processing freeze)", "v0_2_operational": "search-free raw-input runnable",
                     "v0_3": "guard+search 최고 정확도(post-processing freeze, PP-Y18 base는 상류 search 의존)"},
        "operational_note": (
            "후처리층만 실행 가능(component 예측 + artist_key 입력). 하부 Quantile/PP-Y18은 상류 참조. "
            "검색 delta는 작가 단위 frozen snapshot(372 작가) — 신규 작가는 fallback(guard). "
            "0604는 전부 warm(0 cold)이라 cold 운영 트래픽 확보 후 재평가 필요."),
        "reproduced_defense1_guard_search_mdape": reproduced,
        "postprocessor_max_abs_diff": max_diff,
    }
    (BUNDLE / "config" / "cold_model_policy_v0_3.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")

    # Evidence copy.
    ev = BUNDLE / "evidence" / "PP-COLD-DEFENSE1"
    if ev.exists():
        shutil.rmtree(ev)
    (ev / "outputs").mkdir(parents=True, exist_ok=True)
    (ev / "reports").mkdir(parents=True, exist_ok=True)
    shutil.copy2(DEFENSE1_DIR / "reports" / "PP-COLD-DEFENSE1_cold_guard_search_layer_combination.md", ev / "reports" / "PP-COLD-DEFENSE1.md")
    for rel in ["outputs/test_metrics.csv", "outputs/additivity_decomposition.csv"]:
        shutil.copy2(DEFENSE1_DIR / rel, ev / rel)

    (BUNDLE / "reproduction").mkdir(exist_ok=True)
    (BUNDLE / "reproduction" / "upstream_sources.json").write_text(json.dumps({
        "pp_y18_predictions": str(qr2.Y18_PATH.relative_to(REPO)),
        "pp_qr1_predictions": str(qr2.QR1_PATH.relative_to(REPO)),
        "h28_search_predictions": str(H28_PRED.relative_to(REPO)),
        "search_source": SEARCH_SOURCE,
        "freeze_command": "python3 scripts/track6/freeze_cold_prediction_artifact_v0_3.py",
        "validation_evidence": "experiments/track6/PP-COLD-DEFENSE1_cold_guard_search_layer_combination",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    release = "\n".join([
        "# Cold prediction v0.3 (guard + search 2-layer defense) release",
        "",
        f"- 작성일(고정): {FREEZE_TS}",
        f"- 상태: {policy['status']}",
        "",
        "## 정책",
        "",
        f"- 대표 점예측: PP-Y18 qwidth — test MdAPE {m_rep['MdAPE']:.4f} / MAPE {m_rep['MAPE']:.4f} / p95 {m_rep['p95_APE']:.4f}",
        f"- 방어(guard+search): test MdAPE {m_def['MdAPE']:.4f} / MAPE {m_def['MAPE']:.4f} / p95 {m_def['p95_APE']:.4f}",
        f"- 참고 guard 단독: test MdAPE {m_guard['MdAPE']:.4f} / MAPE {m_guard['MAPE']:.4f} / p95 {m_guard['p95_APE']:.4f}",
        f"- 검색 커버리지(test): {coverage_test:.3f}, 검수 플래그율(test): {review_rate_test:.3f}",
        "",
        "## 검증",
        "",
        f"- 후처리기 재현(vs 독립 계산) max abs diff = {max_diff:.2e}",
        f"- PP-COLD-DEFENSE1 guard_search_gm MdAPE 재현: {reproduced} (defense1 {d1_md:.4f} vs artifact {m_def['MdAPE']:.4f})",
        "- 두 방어 가산성: PP-COLD-DEFENSE1 redundancy gap ≈ 0 (evidence/PP-COLD-DEFENSE1).",
        "",
        "## 정직한 범위",
        "",
        "- 후처리층만 실행 가능(component 예측 + artist_key 입력). 하부 Quantile/PP-Y18은 상류 search 의존.",
        "- 검색 delta는 작가 단위 frozen snapshot(372 작가). 신규 작가 → guard fallback. 검색층은 분산 추가 → review_flag 동반.",
        "- 0604는 전부 warm(0 cold) → cold 운영 트래픽 확보 후 재평가 필요.",
        "- 3종 비교: v0.1(guard only) / v0.2_operational(search-free raw-input) / v0.3(guard+search 최고 정확도).",
        "",
        "## 구성",
        "",
        "- `config/cold_model_policy_v0_3.json`, `cold_postprocess_params_v0_3.json`, `search_delta_lookup_v0_3.json`",
        "- `predict/apply_cold_postprocess_v0_3.py`, `evidence/PP-COLD-DEFENSE1/`, `reproduction/upstream_sources.json`",
        "- `manifest/MANIFEST.sha256`",
    ])
    (BUNDLE / "reports").mkdir(exist_ok=True)
    (BUNDLE / "reports" / "cold_artifact_release_v0_3.md").write_text(release, encoding="utf-8")
    (BUNDLE / "README.md").write_text(
        "# Cold prediction v0.3 (guard + search 2-layer defense)\n\n"
        "PP-COLD-DEFENSE1이 가산 검증한 guard+search 방어 고정. 최고 정확도 cold 정책.\n\n"
        "재생성: `python3 scripts/track6/freeze_cold_prediction_artifact_v0_3.py`\n"
        "후처리기: `predict/apply_cold_postprocess_v0_3.py`\n"
        "릴리스: `reports/cold_artifact_release_v0_3.md`\n", encoding="utf-8")

    for cache in BUNDLE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    rows: list[dict[str, Any]] = []
    for p in sorted(BUNDLE.rglob("*")):
        parts = p.relative_to(BUNDLE).parts
        if p.is_file() and "manifest" not in parts and "__pycache__" not in parts and p.suffix != ".pyc":
            rows.append({"path": str(p.relative_to(BUNDLE)), "sha256": sha256_file(p)})
    (BUNDLE / "manifest").mkdir(exist_ok=True)
    (BUNDLE / "manifest" / "MANIFEST.sha256").write_text(
        "\n".join(f"{r['sha256']}  {r['path']}" for r in rows) + "\n", encoding="utf-8")

    print(f"[ARTIFACT3] post-processor max abs diff: {max_diff:.2e}")
    print(f"[ARTIFACT3] DEFENSE1 guard_search MdAPE reproduced: {reproduced} (d1 {d1_md:.4f} / artifact {m_def['MdAPE']:.4f})")
    print(f"[ARTIFACT3] representative test: {m_rep}")
    print(f"[ARTIFACT3] defense (guard+search) test: {m_def}")
    print(f"[ARTIFACT3] guard-only test: {m_guard}")
    print(f"[ARTIFACT3] search lookup artists: {len(lookup)}, test coverage: {coverage_test:.3f}, review rate: {review_rate_test:.3f}")
    print(f"[ARTIFACT3] bundle files: {len(rows)}")


if __name__ == "__main__":
    main()
