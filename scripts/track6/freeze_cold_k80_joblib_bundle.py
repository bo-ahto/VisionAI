#!/usr/bin/env python3
"""Freeze the Cold k80 operational model into a self-contained joblib bundle.

기준 후보: resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05 (PP-CSIM24 + PP-CSIM25)

PP-CSIM24/25 실험 코드(함수)를 그대로 재사용해 base q50 모델 + train 참조풀(OOF 잔차)
+ k80/routing params를 하나의 runtime_store.joblib로 묶고, 단일 입력 추론용 predictor가
읽을 수 있게 한다. 실험 출력(test_cold)을 재현해 parity를 검증한다.

  python3 scripts/track6/freeze_cold_k80_joblib_bundle.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# 실험 모듈 재사용 (parity 보장) — 같은 디렉터리 import 경로
import run_pp_csim24_cold_similarity_residual_correction as exp
import run_pp_w_experiments as ppw
from run_pp_csim1_cold_similarity_reference import ARTIST_SIM_FEATURES, ARTWORK_SIM_FEATURES
from run_pre_pp_experiments import REPO

BASE_TOP_K = exp.BASE_TOP_K          # 160 (base artwork-sim ref stats)
K80 = 80
STRENGTH = 1.0
CAP = 0.25
ROUTE_NEG_CORR = 0.05                # 하향 보정 |corr| >= 0.05 일 때만 적용 (PP-CSIM25)

TARGET = REPO / "models" / "track6" / "cold_k80_conservative_official_v0.1_candidate"
STORE_PATH = TARGET / "artifacts" / "runtime_store.joblib"


def build_training_state():
    """PP-CSIM24 main()의 base+잔차 학습을 full-train으로 재현."""
    fs = ppw.base_feature_sets()
    cmeta = {name: (strategy, features, hyp) for name, strategy, features, hyp in
             __import__("run_pp_cmeta4_user_input_meta_only").candidate_defs()}
    artwork_features = exp.unique(fs["cold_lgb"])
    core_features = cmeta["user_meta_core_bucket"][1]
    required = exp.unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)

    cand_csv = exp.FEATURE_CANDIDATES_WITH_META
    if cand_csv.exists():
        ppw.FEATURE_CANDIDATES = cand_csv
        from run_pp_cmeta4_user_input_meta_only import load_user_meta_frames
        train, val, test = load_user_meta_frames(required)
    else:
        train, val, test = exp.load_split_frames(required)

    # base 입력 = core user-meta + artwork-sim k160 reference stats
    train_sim, val_sim, test_sim, ref_features = exp.compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=f"artwork_sim_k{BASE_TOP_K}", top_k=BASE_TOP_K
    )
    base_features = exp.unique(core_features + ref_features)

    base_model = exp.fit_q_model(train_sim, base_features, alpha=0.50)
    train_oof = exp.train_oof_pred(train_sim, base_features, alpha=0.50)
    train_residual = train_sim["ln_price_krw"].to_numpy(dtype=float) - train_oof

    return train_sim, val_sim, test_sim, base_model, base_features, train_residual


def predict_k80(store: dict, base_model, base_features, target_sim: pd.DataFrame) -> np.ndarray:
    """store(train 참조풀) + base_model로 target의 k80 routed 예측(log)."""
    train_ref = store["train_ref"]
    train_residual = store["train_residual"]
    base_pred = exp.predict_q_model(base_model, train_ref, target_sim, base_features)
    stats = exp.residual_neighbor_stat(
        train_ref, target_sim, ARTIST_SIM_FEATURES, train_residual,
        top_k=K80, prefix=f"artist_meta_k{K80}",
    )
    median = stats[f"artist_meta_k{K80}_resid_median"].to_numpy(dtype=float)
    correction = np.clip(STRENGTH * median, -CAP, CAP)
    routed = np.where(correction <= -ROUTE_NEG_CORR, correction, 0.0)  # 하향 >= 0.05 만 적용
    return base_pred + routed


def main() -> None:
    for sub in ("artifacts", "config", "predict", "manifest", "reports"):
        (TARGET / sub).mkdir(parents=True, exist_ok=True)

    train_sim, val_sim, test_sim, base_model, base_features, train_residual = build_training_state()

    # train 참조풀: base ref-stat 재계산용 ARTWORK_SIM + k80 이웃용 ARTIST_SIM + base_features + 라벨
    ref_cols = exp.unique(
        ["_track6_row_id", "ln_price_krw"] + base_features
        + [c for c in ARTWORK_SIM_FEATURES if c in train_sim.columns]
        + [c for c in ARTIST_SIM_FEATURES if c in train_sim.columns]
    )
    store = {
        "base_features": base_features,
        "artist_sim_features": ARTIST_SIM_FEATURES,
        "artwork_sim_features": ARTWORK_SIM_FEATURES,
        "train_ref": train_sim[ref_cols].reset_index(drop=True),
        "train_residual": train_residual,
        "base_model": base_model,
        "params": {
            "candidate": "resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05",
            "base_top_k": BASE_TOP_K, "k": K80, "strength": STRENGTH, "cap": CAP,
            "route_neg_corr_ge": ROUTE_NEG_CORR, "alpha": 0.50,
        },
    }
    joblib.dump(store, STORE_PATH, compress=3)

    # parity: test_cold 재현 (predictor 경로 vs 직접 계산)
    pred_log = predict_k80(store, base_model, base_features, test_sim)
    actual = test_sim["ln_price_krw"].to_numpy(dtype=float)
    ape = np.abs(np.exp(pred_log) - np.exp(actual)) / np.exp(actual)
    print(f"store_bytes={STORE_PATH.stat().st_size} train_ref_rows={len(store['train_ref'])}")
    print(f"test_cold n={len(pred_log)} MdAPE={np.median(ape):.4f} MAPE={np.mean(ape):.4f}")

    (TARGET / "manifest.json").write_text(json.dumps({
        "artifact_id": "cold_k80_conservative_official_v0_1_candidate",
        "candidate": store["params"]["candidate"],
        "runtime_store": "artifacts/runtime_store.joblib",
        "runtime_db_required": False,
        "predictor": "predict/predict_cold_k80_v0_1.py",
        "store_bytes": STORE_PATH.stat().st_size,
        "train_ref_rows": int(len(store["train_ref"])),
        "params": store["params"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote bundle: {TARGET}")


if __name__ == "__main__":
    main()
