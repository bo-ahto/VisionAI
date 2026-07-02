#!/usr/bin/env python3
"""Freeze the Cold prediction v0.1 policy artifact (PP-COLD-ARTIFACT1).

Freezes the PP-QR4-validated Cold policy:
- representative point prediction = PP-Y18 qwidth
- MAPE/p95 defense layer          = guard_y18_lgb_q40_qwidth67_gap50_down_w0.50
- fallback                        = PP-Y2 baseline

It computes the guard's frozen parameters (validation thresholds + weight),
verifies that the shipped standalone post-processor reproduces the exact PP-QR4
guard test metrics, then writes the policy / params / release report / manifest.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_qr2_cold_quantile_final_candidate_blend as qr2  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.1"
QR4_DIR = REPO / "experiments" / "track6" / "PP-QR4_cold_qwidth_repeated_split_revalidation"

REPRESENTATIVE = "component_pp_y18_qwidth_bin"
GUARD = "guard_y18_lgb_q40_qwidth67_gap50_down_w0p50"
FALLBACK = "component_pp_y2_baseline"
WEIGHT = 0.50
VERSION = "v0.1"
FREEZE_TS = "2026-06-07T00:00:00"  # fixed for reproducible manifest


def metric_triplet(actual_price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95)), "RMSE_log": float("nan")}


def load_postprocessor():
    path = BUNDLE / "predict" / "apply_cold_postprocess_v0_1.py"
    spec = importlib.util.spec_from_file_location("cold_postprocess_v0_1", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    frame = qr2.add_qr1_predictions(qr2.load_y18_frame())
    val = frame[frame["split"] == "validation"].copy().reset_index(drop=True)
    test = frame[frame["split"] == "test"].copy().reset_index(drop=True)

    # Frozen guard thresholds from validation.
    thresholds = qr2.validation_thresholds(val)
    qwidth_q67 = float(thresholds["qwidth_q67"])
    gap_q50 = float(thresholds["gap_q50"])
    params = {
        "version": VERSION,
        "candidate": GUARD,
        "components": {"base": "y18_qwidth_pred_log", "comp": "lgb_q40_pred_log"},
        "thresholds": {"qwidth_q67": qwidth_q67, "gap_q50": gap_q50},
        "gap_definition": "gap_q50 = validation 50th pct of (y18_qwidth_pred_log - cat_q40_pred_log)",
        "mask": "qwidth >= qwidth_q67 AND (base - lgb_q40) >= gap_q50 AND lgb_q40 < base",
        "weight": WEIGHT,
        "direction": "down_only",
        "source": "PP-QR4 validated; thresholds fit on Track6 validation split",
    }
    (BUNDLE / "config" / "cold_postprocess_params_v0_1.json").write_text(
        json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")

    # Reference candidate via QR2 (exact original definition), refit on validation.
    qr2_thresholds = qr2.validation_thresholds(val)
    qr2_guard = {c.candidate: c for c in qr2.guarded_candidates(test, qr2_thresholds)}[GUARD]
    qr2_guard_pred = np.asarray(qr2_guard.pred_log, dtype=float)

    # Shipped post-processor.
    pp = load_postprocessor()
    test_applied = pp.apply(test, params)
    ship_defense = test_applied["cold_defense_pred_log"].to_numpy(dtype=float)
    ship_rep = test_applied["cold_representative_pred_log"].to_numpy(dtype=float)

    # Verify shipped post-processor reproduces QR2 guard exactly.
    max_diff = float(np.max(np.abs(ship_defense - qr2_guard_pred)))
    if max_diff > 1e-9:
        raise SystemExit(f"FREEZE ABORT: shipped post-processor mismatch vs QR2 guard (max abs diff {max_diff:.3e})")

    actual = test["actual_price"].to_numpy(dtype=float)
    m_rep = metric_triplet(actual, ship_rep)
    m_guard = metric_triplet(actual, ship_defense)
    m_fallback = metric_triplet(actual, test[qr2.Y2_PRED if hasattr(qr2, "Y2_PRED") else "y2_pred_log"].to_numpy(dtype=float))

    # Cross-check against PP-QR4 recorded test metrics.
    qr4_point = pd.read_csv(QR4_DIR / "outputs" / "test_point_metrics.csv").set_index("candidate")
    qr4_guard_md = float(qr4_point.loc[GUARD, "test_MdAPE"])
    reproduced = abs(m_guard["MdAPE"] - qr4_guard_md) <= 1e-6

    policy = {
        "version": VERSION,
        "name": "cold_prediction_v0.1",
        "status": "validated_policy_freeze",
        "created_at": FREEZE_TS,
        "purpose": "PP-QR4가 반복검증한 Cold guard 방어 후보 + PP-Y18 대표 점예측 + fallback/신뢰도·범위 정책 고정",
        "target": "ln_price_krw",
        "price_unit": "KRW",
        "representative_policy": {
            "name": "Cold representative point prediction",
            "candidate": REPRESENTATIVE,
            "model_family": "LightGBM Quantile + qwidth bin OOF 보정 (PP-Y18)",
            "metrics_test": m_rep,
            "note": "대표 점예측은 PP-Y18 유지(교체하지 않음).",
        },
        "defense_policy": {
            "name": "Cold MAPE/p95 defense layer",
            "candidate": GUARD,
            "params_ref": "config/cold_postprocess_params_v0_1.json",
            "metrics_test": m_guard,
            "validation_evidence": {
                "source": "PP-QR4",
                "MAPE_improve_prob_row_artist": [1.00, 0.98],
                "p95_improve_prob_row_artist": [0.98, 0.85],
                "mdape_not_worse_vs_pp_y18": True,
            },
            "note": "고위험 구간(qwidth 높음 + gap 큼)에서 lgb_q40 쪽으로 하향 결합. 대표 점예측을 대체하지 않는 방어층.",
        },
        "fallback_policy": {"candidate": FALLBACK, "metrics_test": m_fallback,
                            "note": "guard/representative 산출 불가 시 PP-Y2 baseline."},
        "confidence_range_policy": {
            "display": "확정 가격 아님. 참고 예측가 + 넓은 가격 범위 + 낮은 신뢰도로 표시.",
            "range_basis": "quantile_width_log 기반 범위, qwidth 높을수록 신뢰도 하향.",
        },
        "operational_note": (
            "후처리 파라미터층(predict/apply_cold_postprocess_v0_1.py)은 component 예측 입력 시 실행 가능. "
            "하부 LightGBM Quantile 모델은 상류 OOF 예측(PP-Y18/PP-QR1)을 참조하며 별도 직렬화 필요. "
            "0604 평가는 전부 warm(6873 warm/0 cold)이라 cold 운영 트래픽 확보 후 재평가 필요."
        ),
        "reproduced_pp_qr4_guard_mdape": reproduced,
        "shipped_postprocessor_max_abs_diff_vs_qr2": max_diff,
    }
    (BUNDLE / "config" / "cold_model_policy_v0_1.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")

    # Copy PP-QR4 evidence (reports + key outputs only).
    ev = BUNDLE / "evidence" / "PP-QR4"
    if ev.exists():
        shutil.rmtree(ev)
    (ev / "reports").mkdir(parents=True, exist_ok=True)
    (ev / "outputs").mkdir(parents=True, exist_ok=True)
    for rel in ["reports/PP-QR4_cold_qwidth_repeated_split_revalidation.md"]:
        shutil.copy2(QR4_DIR / rel, ev / rel)
    for rel in ["outputs/holdout_summary.csv", "outputs/test_point_metrics.csv", "outputs/test_bootstrap_ci.csv"]:
        shutil.copy2(QR4_DIR / rel, ev / rel)

    # Reproduction pointers (upstream sources + checksums).
    upstream = {
        "pp_y18_predictions": str(qr2.Y18_PATH.relative_to(REPO)),
        "pp_qr1_predictions": str(qr2.QR1_PATH.relative_to(REPO)),
        "pp_y2_predictions": str(qr2.Y2_PATH.relative_to(REPO)),
        "representative_candidate": qr2.Y18_CANDIDATE,
        "quantile_candidates": qr2.QUANTILE_CANDIDATES,
        "validation_split": "Track6 validation split (qr2.load_y18_frame)",
        "freeze_command": "python3 scripts/track6/freeze_cold_prediction_artifact_v0_1.py",
        "reproduce_guard": "python3 scripts/track6/run_pp_qr4_cold_qwidth_repeated_split_revalidation.py",
    }
    for key in ["pp_y18_predictions", "pp_qr1_predictions", "pp_y2_predictions"]:
        p = REPO / upstream[key]
        upstream[f"{key}_sha256"] = sha256_file(p) if p.exists() else "MISSING"
    (BUNDLE / "reproduction" / "upstream_sources.json").write_text(
        json.dumps(upstream, ensure_ascii=False, indent=2), encoding="utf-8")

    # Release report.
    release = "\n".join([
        "# Cold prediction v0.1 release",
        "",
        f"- 작성일(고정): {FREEZE_TS}",
        f"- 상태: {policy['status']}",
        "",
        "## 정책",
        "",
        f"- 대표 점예측: `{REPRESENTATIVE}` (PP-Y18) — test MdAPE {m_rep['MdAPE']:.4f} / MAPE {m_rep['MAPE']:.4f} / p95 {m_rep['p95_APE']:.4f}",
        f"- MAPE/p95 방어층: `{GUARD}` — test MdAPE {m_guard['MdAPE']:.4f} / MAPE {m_guard['MAPE']:.4f} / p95 {m_guard['p95_APE']:.4f}",
        f"- fallback: `{FALLBACK}` — test MdAPE {m_fallback['MdAPE']:.4f} / MAPE {m_fallback['MAPE']:.4f} / p95 {m_fallback['p95_APE']:.4f}",
        "- 신뢰도/범위: 확정가 아님, 참고가 + 넓은 범위 + 낮은 신뢰도.",
        "",
        "## 검증",
        "",
        f"- 후처리기 재현: shipped 후처리기 vs PP-QR2 guard 정의 max abs diff = {max_diff:.2e}",
        f"- PP-QR4 guard test MdAPE 재현: {reproduced} (PP-QR4 {qr4_guard_md:.4f} vs artifact {m_guard['MdAPE']:.4f})",
        "- PP-QR4 반복검증 근거: MAPE 개선확률 row/artist 1.00/0.98, p95 0.98/0.85 (evidence/PP-QR4).",
        "",
        "## 정직한 범위",
        "",
        "- 후처리 파라미터층만 실행 가능(component 예측 입력 필요). 하부 LightGBM Quantile 모델은 상류 OOF 예측 참조 — 신규 raw-input 추론은 하부 모델 직렬화 별도 필요.",
        "- 0604 신규 라벨은 전부 warm(6873 warm/0 cold)이라 cold 운영 트래픽 확보 후 재평가 필요.",
        "",
        "## 구성",
        "",
        "- `config/cold_model_policy_v0_1.json`, `config/cold_postprocess_params_v0_1.json`",
        "- `predict/apply_cold_postprocess_v0_1.py` (후처리기 + self-test)",
        "- `evidence/PP-QR4/`, `reproduction/upstream_sources.json`",
        "- `manifest/files_manifest.csv`, `manifest/MANIFEST.sha256`",
    ])
    (BUNDLE / "reports" / "cold_artifact_release_v0_1.md").write_text(release, encoding="utf-8")

    readme = "\n".join([
        "# Cold prediction v0.1",
        "",
        "PP-QR4가 반복검증한 Cold 정책 고정 번들.",
        "",
        "- 대표 점예측: PP-Y18 qwidth",
        "- MAPE/p95 방어층: guard (PP-QR4 채택)",
        "- fallback: PP-Y2",
        "",
        "재생성: `python3 scripts/track6/freeze_cold_prediction_artifact_v0_1.py`",
        "릴리스 문서: `reports/cold_artifact_release_v0_1.md`",
        "후처리기: `predict/apply_cold_postprocess_v0_1.py`",
    ])
    (BUNDLE / "README.md").write_text(readme, encoding="utf-8")

    # Drop transient bytecode so the manifest is reproducible.
    for cache in BUNDLE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)

    # Manifest (exclude manifest dir itself and any bytecode).
    rows: list[dict[str, Any]] = []
    for p in sorted(BUNDLE.rglob("*")):
        parts = p.relative_to(BUNDLE).parts
        if p.is_file() and "manifest" not in parts and "__pycache__" not in parts and p.suffix != ".pyc":
            rows.append({"path": str(p.relative_to(BUNDLE)), "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    pd.DataFrame(rows).to_csv(BUNDLE / "manifest" / "files_manifest.csv", index=False)
    (BUNDLE / "manifest" / "MANIFEST.sha256").write_text(
        "\n".join(f"{r['sha256']}  {r['path']}" for r in rows) + "\n", encoding="utf-8")

    print(f"[PP-COLD-ARTIFACT1] shipped post-processor max abs diff vs QR2 guard: {max_diff:.2e}")
    print(f"[PP-COLD-ARTIFACT1] PP-QR4 guard MdAPE reproduced: {reproduced} (qr4 {qr4_guard_md:.4f} / artifact {m_guard['MdAPE']:.4f})")
    print(f"[PP-COLD-ARTIFACT1] representative test: {m_rep}")
    print(f"[PP-COLD-ARTIFACT1] defense test: {m_guard}")
    print(f"[PP-COLD-ARTIFACT1] frozen thresholds: qwidth_q67={qwidth_q67:.4f}, gap_q50={gap_q50:.4f}, weight={WEIGHT}")
    print(f"[PP-COLD-ARTIFACT1] bundle files: {len(rows)}")


if __name__ == "__main__":
    main()
