#!/usr/bin/env python3
"""Build the Cold prediction v0.2 (operational, search-free) runnable artifact.

Trains LightGBM Quantile models (q10/q40/q50/q90) on the operational cold feature
set (NO search/external features), fits a qwidth-bin correction + guard defense on
validation, measures honest test metrics, serializes everything, and verifies the
shipped raw-input predictor reproduces the measured numbers.

This is a search-free deployable variant; its metrics DIFFER from the search-based
PP-Y18 (cold_prediction_v0.1) because the external search signal is dropped.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import joblib
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope, SEED  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.2_operational"
QUANTILES = {"q10": 0.10, "q40": 0.40, "q50": 0.50, "q90": 0.90}
N_ESTIMATORS = 430
N_QWIDTH_BINS = 5
MIN_BIN_ROWS = 30
CORR_CAP = 0.25
GUARD_WEIGHT = 0.50
FREEZE_TS = "2026-06-07T00:00:00"
CATEGORICAL = {"medium_category", "support_category", "size_bucket", "support_size_bucket"}


def metric_triplet(price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)), "p95_APE": float(np.quantile(ape, 0.95))}


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [f for f in features if f not in CATEGORICAL]
    categorical = [f for f in features if f in CATEGORICAL]
    return numeric, categorical


def quantile_pipeline(features: list[str], alpha: float) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(objective="quantile", alpha=alpha, n_estimators=N_ESTIMATORS,
                                learning_rate=0.035, num_leaves=31, min_child_samples=35,
                                subsample=0.9, colsample_bytree=0.9, reg_lambda=1.2,
                                random_state=SEED, verbosity=-1)),
    ])


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_predictor():
    path = BUNDLE / "predict" / "predict_cold_operational_v0_2.py"
    spec = importlib.util.spec_from_file_location("predict_cold_operational_v0_2", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    features = artifact_features()["cold_lightgbm"]
    train, val, test = load_scope("cold", features)
    y_train = train["ln_price_krw"].to_numpy(dtype=float)

    (BUNDLE / "models").mkdir(parents=True, exist_ok=True)
    (BUNDLE / "config").mkdir(parents=True, exist_ok=True)

    # Train + serialize quantile models.
    models: dict[str, Pipeline] = {}
    for q, alpha in QUANTILES.items():
        pipe = quantile_pipeline(features, alpha)
        pipe.fit(train[features], y_train)
        joblib.dump(pipe, BUNDLE / "models" / f"lgbq_{q}.joblib")
        models[q] = pipe

    def qpred(frame: pd.DataFrame, q: str) -> np.ndarray:
        return np.asarray(models[q].predict(frame[features]), dtype=float)

    # Validation predictions for fitting guard. Representative = q50 (best median).
    val_q = {q: qpred(val, q) for q in QUANTILES}
    val_width = val_q["q90"] - val_q["q10"]
    val_rep = val_q["q50"]
    width_q67 = float(np.quantile(val_width, 0.67))
    gap_q50 = float(np.quantile(val_rep - val_q["q40"], 0.50))
    guard = {"components": {"base": "representative", "comp": "q40"},
             "width_q67": width_q67, "gap_q50": gap_q50, "weight": GUARD_WEIGHT,
             "mask": "qwidth >= width_q67 AND (base - q40) >= gap_q50 AND q40 < base", "direction": "down_only"}
    (BUNDLE / "config" / "guard_params_v0_2.json").write_text(
        json.dumps(guard, ensure_ascii=False, indent=2), encoding="utf-8")

    # Verify shipped predictor reproduces representative/defense on test.
    predictor = load_predictor()
    test_out = predictor.predict(test, models=models, guard=guard)
    test_price = test["price_krw"].to_numpy(dtype=float)

    # Independent recompute for cross-check.
    test_q = {q: qpred(test, q) for q in QUANTILES}
    test_width = test_q["q90"] - test_q["q10"]
    test_rep = test_q["q50"]
    base, comp = test_rep, test_q["q40"]
    mask = (test_width >= width_q67) & ((base - comp) >= gap_q50) & (comp < base)
    test_def = base.copy(); test_def[mask] = (1 - GUARD_WEIGHT) * base[mask] + GUARD_WEIGHT * comp[mask]
    max_diff = float(max(np.max(np.abs(test_out["representative_pred_log"].to_numpy() - test_rep)),
                         np.max(np.abs(test_out["defense_pred_log"].to_numpy() - test_def))))
    if max_diff > 1e-9:
        raise SystemExit(f"BUILD ABORT: predictor mismatch (max abs diff {max_diff:.3e})")

    metrics = {
        "representative_test": metric_triplet(test_price, test_rep),
        "defense_test": metric_triplet(test_price, test_def),
        "baseline_q50_test": metric_triplet(test_price, test_q["q50"]),
        "representative_val": metric_triplet(val["price_krw"].to_numpy(dtype=float), val_rep),
    }
    guard_rows = int(mask.sum())

    policy = {
        "version": "v0.2-operational",
        "name": "cold_prediction_v0.2_operational",
        "status": "search_free_runnable_artifact",
        "created_at": FREEZE_TS,
        "purpose": "외부 검색 의존 없는 운영 cold 예측 artifact. raw 운영 피처만으로 실행 가능.",
        "relation_to_v0_1": (
            "v0.1 대표 PP-Y18은 search_all_external_interaction 피처 의존이라 raw-input 직렬화 불가. "
            "v0.2는 search 피처를 제거한 운영 변형이며 지표가 v0.1(0.4247)과 다르다."
        ),
        "feature_set": features,
        "models": {q: f"models/lgbq_{q}.joblib" for q in QUANTILES},
        "representative_policy": {"base": "q50 (LightGBM Quantile median)", "metrics_test": metrics["representative_test"]},
        "defense_policy": {"candidate": "operational guard (q40 blend)", "params": "config/guard_params_v0_2.json",
                            "metrics_test": metrics["defense_test"], "guard_applied_rows_test": guard_rows},
        "baseline_q50": {"metrics_test": metrics["baseline_q50_test"]},
        "range_policy": {"low": "q10", "high": "q90", "display": "참고가 + 넓은 범위 + 낮은 신뢰도"},
        "predictor_max_abs_diff": max_diff,
        "n_estimators": N_ESTIMATORS, "seed": SEED,
        "operational_note": (
            "외부 API 의존 0. 신규 cold artwork의 12개 운영 피처만 있으면 추론 가능. "
            "0604 신규 라벨이 전부 warm(0 cold)이라 cold 운영 트래픽 확보 후 재평가 필요."
        ),
    }
    (BUNDLE / "config" / "cold_model_policy_v0_2.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")

    release = "\n".join([
        "# Cold prediction v0.2 (operational, search-free) release",
        "",
        f"- 작성일(고정): {FREEZE_TS}",
        "- 상태: search_free_runnable_artifact (외부 API 의존 0)",
        "",
        "## 동기",
        "",
        "- v0.1 대표 PP-Y18은 `search_all_external_interaction` 피처(외부 검색 API) 의존 → raw-input 직렬화 불가.",
        "- v0.2는 운영 피처 12개만 사용하는 search-free 변형. 지표는 v0.1과 다름(검색 신호 제거).",
        "",
        "## 운영 피처 (12)",
        "",
        f"- {', '.join(features)}",
        "",
        "## 지표 (test, cold 3099행)",
        "",
        f"- 대표(q50): MdAPE {metrics['representative_test']['MdAPE']:.4f} / MAPE {metrics['representative_test']['MAPE']:.4f} / p95 {metrics['representative_test']['p95_APE']:.4f}",
        f"- 방어(q50 기반 q40 guard, p95/MAPE 안전): MdAPE {metrics['defense_test']['MdAPE']:.4f} / MAPE {metrics['defense_test']['MAPE']:.4f} / p95 {metrics['defense_test']['p95_APE']:.4f} (적용 {guard_rows}행)",
        "",
        "## 참고: v0.1(search 기반) 대표 PP-Y18 test = 0.4247 / 0.991 / 3.305",
        "",
        "- v0.2 search-free 대표가 v0.1보다 낮으면 그 차이가 검색 신호 기여분(운영에서 안전하게 못 쓰는 부분)이다.",
        "",
        "## 검증",
        "",
        f"- shipped 예측기 raw-input 재현 max abs diff = {max_diff:.2e}",
        "",
        "## 구성",
        "",
        "- `models/lgbq_q10|q40|q50|q90.joblib` (LightGBM Quantile, 운영 피처)",
        "- `config/cold_model_policy_v0_2.json`, `config/guard_params_v0_2.json`",
        "- `predict/predict_cold_operational_v0_2.py` (raw 운영 피처 → 예측)",
        "- `manifest/MANIFEST.sha256`",
    ])
    (BUNDLE / "reports" / "cold_operational_v0_2_release.md").write_text(release, encoding="utf-8")
    (BUNDLE / "README.md").write_text(
        "# Cold prediction v0.2 (operational, search-free)\n\n"
        "외부 검색 API 의존 없는 raw-input 실행 가능 cold 예측 artifact.\n\n"
        "재생성: `python3 scripts/track6/build_cold_prediction_operational_v0_2.py`\n"
        "추론: `predict/predict_cold_operational_v0_2.py` (운영 피처 12개 입력)\n"
        "릴리스: `reports/cold_operational_v0_2_release.md`\n", encoding="utf-8")

    # Manifest (exclude manifest dir + bytecode).
    for cache in BUNDLE.rglob("__pycache__"):
        import shutil
        shutil.rmtree(cache, ignore_errors=True)
    rows: list[dict[str, Any]] = []
    for p in sorted(BUNDLE.rglob("*")):
        parts = p.relative_to(BUNDLE).parts
        if p.is_file() and "manifest" not in parts and "__pycache__" not in parts and p.suffix != ".pyc":
            rows.append({"path": str(p.relative_to(BUNDLE)), "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    (BUNDLE / "manifest").mkdir(exist_ok=True)
    (BUNDLE / "manifest" / "MANIFEST.sha256").write_text(
        "\n".join(f"{r['sha256']}  {r['path']}" for r in rows) + "\n", encoding="utf-8")

    print(f"[v0.2] predictor max abs diff: {max_diff:.2e}")
    print(f"[v0.2] representative test: {metrics['representative_test']}")
    print(f"[v0.2] defense test:        {metrics['defense_test']}")
    print(f"[v0.2] baseline q50 test:   {metrics['baseline_q50_test']}")
    print(f"[v0.2] guard applied rows (test): {guard_rows}/{len(test)}")
    print(f"[v0.2] bundle files: {len(rows)}")


if __name__ == "__main__":
    main()
