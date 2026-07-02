#!/usr/bin/env python3
"""PP-CBASE1: Cold 이중 base lock.

Warm PP-WBASE1을 모방해 이후 Cold 실험의 기준 base가 흔들리지 않도록 고정한다.

- 연구 base COLD_BASE_RESEARCH_V1: v0.3 체인(PP-Y18 + guard + 작가단위 검색 delta)
- 운영 base COLD_BASE_OPERATIONAL_V1: v0.2 search-free 직렬화 파이프라인의 방어 서빙값
- validation/test cold 전 행의 고정 base 예측 CSV, champion 비교표, residual target과
  채택 게이트(artist 반복 holdout 중심) manifest를 산출한다.
- v0.3/v0.2 정책 JSON의 test 지표를 재현해 lock의 정합성을 검증한다.
- 0604 데이터는 Warm 제출 전용이므로 어떤 용도로도 사용하지 않는다.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_qr2_cold_quantile_final_candidate_blend as qr2  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
V03 = REPO / "models" / "track6" / "cold_prediction_v0.3"
V02 = REPO / "models" / "track6" / "cold_prediction_v0.2_operational"
EXP = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock"

RESEARCH_BASE_NAME = "COLD_BASE_RESEARCH_V1"
OPERATIONAL_BASE_NAME = "COLD_BASE_OPERATIONAL_V1"
METRIC_TOL = 5e-4


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def metric_row(price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {
        "n": int(len(ape)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "within_30": float(np.mean(ape <= 0.30)),
        "over_50pct_error_rate": float(np.mean(ape > 0.50)),
    }


def check_metrics(label: str, got: dict[str, float], expected: dict[str, float]) -> dict[str, float]:
    diffs = {}
    for k, v in expected.items():
        d = abs(got[k] - float(v))
        diffs[k] = d
        if d > METRIC_TOL:
            raise AssertionError(f"{label} {k} 재현 실패: got {got[k]:.6f}, expected {float(v):.6f}")
    return diffs


def build_research_frame() -> pd.DataFrame:
    qf = qr2.add_qr1_predictions(qr2.load_y18_frame())
    qf = qf[[
        "split", "_track6_row_id", "actual_price", "quantile_width_log",
        "y18_qwidth_pred_log", "lgb_q40_pred_log", "y2_pred_log", "artist_key",
    ]].copy()

    pp = load_module(V03 / "predict" / "apply_cold_postprocess_v0_3.py", "apply_cold_postprocess_v0_3")
    params = pp.load_params()
    lookup = pp.load_search_lookup()

    out = pp.apply(qf, params=params, lookup=lookup)
    qf["guard_pred_log"] = pp.guard_pred_log(
        qf["y18_qwidth_pred_log"].to_numpy(dtype=float),
        qf["lgb_q40_pred_log"].to_numpy(dtype=float),
        qf["quantile_width_log"].to_numpy(dtype=float),
        params,
    )
    qf["research_base_pred_log"] = out["cold_defense_pred_log"].to_numpy(dtype=float)
    qf["search_covered"] = qf["artist_key"].astype(str).map(lambda a: a in lookup)
    if "review_flag" in out.columns:
        qf["review_flag"] = out["review_flag"].to_numpy()
    return qf


def build_operational_frame() -> pd.DataFrame:
    features = artifact_features()["cold_lightgbm"]
    _, val, test = load_scope("cold", features)
    predictor = load_module(V02 / "predict" / "predict_cold_operational_v0_2.py", "predict_cold_operational_v0_2")
    models = predictor.load_models()
    guard = predictor.load_guard()

    frames = []
    for split, frame in (("validation", val), ("test", test)):
        out = predictor.predict(frame, models=models, guard=guard)
        frames.append(pd.DataFrame({
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "v02_representative_pred_log": out["representative_pred_log"].to_numpy(dtype=float),
            "v02_defense_pred_log": out["defense_pred_log"].to_numpy(dtype=float),
            "v02_qwidth_log": out["qwidth_log"].to_numpy(dtype=float),
        }))
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    research = build_research_frame()
    operational = build_operational_frame()
    merged = research.merge(operational, on=["split", "_track6_row_id"], how="inner", validate="one_to_one")
    if len(merged) != len(research):
        raise AssertionError(f"v0.3/v0.2 row join 불일치: research {len(research)} vs merged {len(merged)}")
    merged["actual_log"] = np.log(np.clip(merged["actual_price"].to_numpy(dtype=float), 1.0, None))

    candidates = {
        "component_pp_y2_baseline": "y2_pred_log",
        "component_pp_y18_qwidth_bin": "y18_qwidth_pred_log",
        "guard_only_v0_1": "guard_pred_log",
        f"{RESEARCH_BASE_NAME} (v0.3 guard+search)": "research_base_pred_log",
        "v02_representative_q50": "v02_representative_pred_log",
        f"{OPERATIONAL_BASE_NAME} (v0.2 defense)": "v02_defense_pred_log",
    }
    rows = []
    for split, part in merged.groupby("split"):
        price = part["actual_price"].to_numpy(dtype=float)
        actual_log = part["actual_log"].to_numpy(dtype=float)
        for cand, col in candidates.items():
            rows.append({"candidate": cand, "split": split,
                         **metric_row(price, actual_log, part[col].to_numpy(dtype=float))})
    summary = pd.DataFrame(rows).sort_values(["split", "MAPE"]).reset_index(drop=True)

    # 정책 JSON 대비 재현 검증 (test).
    v03_policy = json.loads((V03 / "config" / "cold_model_policy_v0_3.json").read_text(encoding="utf-8"))
    v02_policy = json.loads((V02 / "config" / "cold_model_policy_v0_2.json").read_text(encoding="utf-8"))
    by_key = {(r["candidate"], r["split"]): r for r in summary.to_dict("records")}
    keep = ("MdAPE", "MAPE", "p95_APE")
    verification = {
        "v0_3_representative": check_metrics(
            "v0.3 대표", by_key[("component_pp_y18_qwidth_bin", "test")],
            {k: v03_policy["representative_policy"]["metrics_test"][k] for k in keep}),
        "v0_3_guard_only": check_metrics(
            "v0.3 guard", by_key[("guard_only_v0_1", "test")],
            {k: v03_policy["defense_policy"]["guard_only_metrics_test"][k] for k in keep}),
        "v0_3_defense": check_metrics(
            "연구 base", by_key[(f"{RESEARCH_BASE_NAME} (v0.3 guard+search)", "test")],
            {k: v03_policy["defense_policy"]["metrics_test"][k] for k in keep}),
        "v0_2_representative": check_metrics(
            "v0.2 대표", by_key[("v02_representative_q50", "test")],
            {k: v02_policy["representative_policy"]["metrics_test"][k] for k in keep}),
        "v0_2_defense": check_metrics(
            "운영 base", by_key[(f"{OPERATIONAL_BASE_NAME} (v0.2 defense)", "test")],
            {k: v02_policy["defense_policy"]["metrics_test"][k] for k in keep}),
    }

    lock_cols = [
        "split", "_track6_row_id", "artist_key", "actual_price", "actual_log",
        "y2_pred_log", "y18_qwidth_pred_log", "guard_pred_log", "research_base_pred_log",
        "quantile_width_log", "search_covered",
        "v02_representative_pred_log", "v02_defense_pred_log", "v02_qwidth_log",
    ]
    if "review_flag" in merged.columns:
        lock_cols.append("review_flag")
    locked = merged[lock_cols].copy()
    locked.to_csv(EXP / "outputs" / "fixed_cold_base_rows.csv", index=False)
    summary.to_csv(EXP / "outputs" / "cold_base_performance_summary.csv", index=False)

    artist_stats = {
        split: {
            "rows": int(len(part)),
            "artists": int(part["artist_key"].nunique()),
            "rows_per_artist_median": float(part.groupby("artist_key").size().median()),
            "rows_per_artist_max": int(part.groupby("artist_key").size().max()),
            "search_covered_rate": float(part["search_covered"].mean()),
        }
        for split, part in merged.groupby("split")
    }

    manifest = {
        "experiment_id": "PP-CBASE1",
        "purpose": "Cold 이중 base lock: 이후 Cold 실험의 고정 기준(base/residual target/게이트)",
        "bases": {
            RESEARCH_BASE_NAME: {
                "column": "research_base_pred_log",
                "definition": "v0.3 체인 = PP-Y18 대표 + guard(PP-QR4) + 작가단위 검색 delta(PP-H28, 미커버→guard)",
                "bundle": "models/track6/cold_prediction_v0.3",
                "residual_target": "actual_log - research_base_pred_log",
            },
            OPERATIONAL_BASE_NAME: {
                "column": "v02_defense_pred_log",
                "definition": "v0.2 search-free 직렬화 파이프라인의 guard 적용 서빙값 (raw-input 실행 가능)",
                "bundle": "models/track6/cold_prediction_v0.2_operational",
                "residual_target": "actual_log - v02_defense_pred_log",
            },
        },
        "gates": {
            "artist_repeated_holdout": "validation cold 작가 80%/70% holdout 각 >=200회: "
                                       "base 대비 MAPE 개선확률 >=0.90 AND p95 개선확률 >=0.90, MdAPE >=0.50",
            "row_repeated_subsample": "row 80% subsample >=200회 (보조; artist 게이트 미통과 시 기각)",
            "fixed_test": "최종 확인 1회: 3지표 비악화 + 목적 지표 개선. bootstrap >=400회는 보고용",
            "prohibitions": [
                "0604 데이터 사용 금지 (Warm 시험 제출 전용)",
                "test로 후보/경계값 선택 금지",
                "운영 입력 불가 피처를 보정 입력 기준으로 사용 금지",
            ],
        },
        "artist_stats": artist_stats,
        "verification_abs_diff_vs_policy_json": verification,
        "sources": {
            "pp_y18_predictions": str(qr2.Y18_PATH.relative_to(REPO)),
            "pp_qr1_predictions": str(qr2.QR1_PATH.relative_to(REPO)),
            "v0_3_postprocessor": "models/track6/cold_prediction_v0.3/predict/apply_cold_postprocess_v0_3.py",
            "v0_2_predictor": "models/track6/cold_prediction_v0.2_operational/predict/predict_cold_operational_v0_2.py",
        },
        "roadmap": "docs/track6/experiments/cold_improvement_roadmap.md",
    }
    (EXP / "artifacts" / "cold_base_lock_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    fmt = summary.copy()
    for c in ("MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_30", "over_50pct_error_rate"):
        fmt[c] = fmt[c].map(lambda v: f"{v:.4f}")
    header = list(fmt.columns)
    md_table = "\n".join(
        ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
        + ["| " + " | ".join(str(v) for v in row) + " |" for row in fmt.itertuples(index=False)]
    )
    report = [
        "# PP-CBASE1 Cold 이중 base lock",
        "",
        "- 목적: 이후 Cold 실험의 기준 base, residual target, 채택 게이트를 고정한다.",
        f"- 연구 base: `{RESEARCH_BASE_NAME}` = v0.3 guard+search 체인 (`research_base_pred_log`)",
        f"- 운영 base: `{OPERATIONAL_BASE_NAME}` = v0.2 search-free 방어 서빙값 (`v02_defense_pred_log`)",
        "- 0604는 Warm 시험 제출 전용 — Cold 실험 전 단계에서 사용 금지.",
        "",
        "## 고정 base 성능",
        "",
        md_table,
        "",
        "## 작가 단위 구성",
        "",
        json.dumps(artist_stats, ensure_ascii=False, indent=2),
        "",
        "## 정책 JSON 재현 검증 (test, 절대 오차)",
        "",
        json.dumps(verification, ensure_ascii=False, indent=2),
        "",
        "## 다음 실험 규칙",
        "",
        "- base prediction은 항상 `fixed_cold_base_rows.csv`의 고정 컬럼을 사용한다.",
        "- 후보는 두 base 대비 개선폭을 모두 보고한다.",
        "- 채택 게이트는 artist 반복 holdout(80%/70%, 각 >=200회) MAPE/p95 >=0.90이 1차다.",
        "- 상세 로드맵: `docs/track6/experiments/cold_improvement_roadmap.md`",
    ]
    (EXP / "reports" / "cold_base_lock.md").write_text("\n".join(report), encoding="utf-8")

    print(summary.to_string(index=False))
    print(json.dumps(artist_stats, ensure_ascii=False, indent=2))
    print("verification: OK (모든 지표가 정책 JSON과 일치)")


if __name__ == "__main__":
    main()
