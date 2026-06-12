#!/usr/bin/env python3
"""Warm-lite v0.1 동결 (PP-WLITE-ARTIFACT1).

- 학습: full train, 작가 사다리 min1 + 비작가 fallback, fold-제외 내부 통계
  (PP-WCUT/CBOOST 레시피), 선형 Huber 6구성 직렬화
- 검증: 동결 모델 + k건 절단 '추론 통계'(k=1~4, WCUT seed)로 warm test 607행
  평가 → PP-WCUT2 per-k 재학습 수치와 비교(동등 수준 확인) + Cold 대비 우위 단언
- 정책: k=1 차등 등급(warm_lite_low) 동결. 라우팅 전제(매칭 >=0.90) 명시.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_s = importlib.util.spec_from_file_location("cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py")
cgrp = importlib.util.module_from_spec(_s); _s.loader.exec_module(cgrp)
_s3 = importlib.util.spec_from_file_location("cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py")
cb3 = importlib.util.module_from_spec(_s3); _s3.loader.exec_module(cb3)
_s1 = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s1); _s1.loader.exec_module(cb1)

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "warm_lite_v0.1"
FREEZE_TS = "2026-06-12T12:00:00"
LITE_LADDER = [
    (["artist_key", "medium_support_bucket", "size_bucket"], 1),
    (["artist_key", "size_bucket"], 1),
    (["artist_key"], 1),
]
WCUT2_REF = {1: 0.2179, 2: 0.1739, 3: 0.1597, 4: 0.1457}  # per-k 재학습 MdAPE(seed 평균)
COLD_REF_MDAPE = 0.47


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    for sub in ("config", "models", "predict", "manifest", "reports"):
        (BUNDLE / sub).mkdir(parents=True, exist_ok=True)

    feats = artifact_features()["cold_lightgbm"]
    train, _, wtest = load_scope("warm", feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area",
                                       "price_krw", "artist_key"]))
    train = train[need].reset_index(drop=True)
    wtest = wtest.reset_index(drop=True)
    price = wtest["price_krw"].to_numpy(dtype=float)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    base_ladder = list(cgrp.LADDER)

    # ── 학습 (min1 사다리, fold-제외 통계) + 직렬화
    cgrp.LADDER = LITE_LADDER + base_ladder
    tr_s = cgrp.train_with_internal_stats(train)
    tr_s["grp_price_proxy"] = tr_s["grp_unit_area_median"] + tr_s["log_area"].clip(lower=0)
    models, num_cols = [], []
    for i, cfg in enumerate(cb3.C_CONFIGS):
        num = cb3.NUM_BASE + cfg["extra"]
        pipe = Pipeline([("prep", ColumnTransformer([
            ("num", Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())]), num),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cb3.CAT_C)])),
            ("m", HuberRegressor(epsilon=cfg["epsilon"], alpha=cfg["alpha"], max_iter=4000))])
        pipe.fit(tr_s[num + cb3.CAT_C], y)
        joblib.dump(pipe, BUNDLE / "models" / f"huber_c{i}.joblib")
        models.append(pipe)
        num_cols.append(num)

    # ── 비작가 fallback 사다리 테이블 동결 (full train)
    ladder_json = []
    for keys, min_n in base_ladder:
        t = cgrp.group_stat_table(train, keys)
        t = t[t["grp_n"] >= min_n]
        table = {}
        for _, r in t.iterrows():
            table["|".join(str(r[c]) for c in keys)] = {
                "grp_log_price_median": float(r["grp_log_price_median"]),
                "grp_log_price_q25": float(r["grp_log_price_q25"]),
                "grp_log_price_q75": float(r["grp_log_price_q75"]),
                "grp_log_price_iqr": float(r["grp_log_price_iqr"]),
                "grp_unit_area_median": float(r["grp_unit_area_median"]),
                "grp_unit_area_iqr": float(r["grp_unit_area_iqr"]),
                "grp_n_log": float(np.log1p(r["grp_n"]))}
        ladder_json.append({"keys": keys, "min_n": min_n, "table": table})
    unit = train["ln_price_krw"] - train["log_area"].clip(lower=0)
    gfb = {"grp_log_price_median": float(train["ln_price_krw"].median()),
           "grp_log_price_q25": float(train["ln_price_krw"].quantile(0.25)),
           "grp_log_price_q75": float(train["ln_price_krw"].quantile(0.75)),
           "grp_unit_area_median": float(unit.median()),
           "grp_unit_area_iqr": float(unit.quantile(0.75) - unit.quantile(0.25)),
           "grp_n_log": float(np.log1p(len(train)))}
    gfb["grp_log_price_iqr"] = gfb["grp_log_price_q75"] - gfb["grp_log_price_q25"]

    params = {"version": "v0.1", "frozen_at": FREEZE_TS, "n_huber": len(models),
              "huber_num_cols": num_cols, "huber_cat_cols": cb3.CAT_C,
              "ladder": ladder_json, "global_fallback": gfb,
              "routing_precondition": "작가매칭신뢰도 >= 0.90 AND 사용가능 가격이력 1~4건 "
                                      "(매칭 점수 캘리브레이션은 운영 로그 과제 — PP-WMATCH1)",
              "k1_policy": "confidence_grade=warm_lite_low, 넓은 범위 표시 + 검수 플래그",
              "evidence": ["PP-WCUT1", "PP-WCUT2", "PP-WMATCH1"],
              "decision": "2026-06-12 사용자 채택 — 기존 Warm/Cold 유지 + 3-경로 라우팅 신설"}
    (BUNDLE / "config" / "warm_lite_params_v0_1.json").write_text(
        json.dumps(params, ensure_ascii=False), encoding="utf-8")

    # ── 검증: 동결 모델 + k건 절단 '추론 통계' (WCUT seed 20260612)
    cgrp.LADDER = LITE_LADDER + base_ladder
    rng = np.random.default_rng(20260612)
    test_artists = set(wtest["artist_key"].astype(str))
    verify = {}
    for k in [1, 2, 3, 4]:
        keep = []
        for a, idx in train.groupby(train["artist_key"].astype(str)).indices.items():
            keep.append(rng.choice(idx, size=k, replace=False)
                        if (a in test_artists and len(idx) > k) else idx)
        tr_k = train.iloc[np.concatenate(keep)].reset_index(drop=True)
        te_s = cgrp.assign_group_stats(tr_k, wtest)
        te_s["grp_price_proxy"] = te_s["grp_unit_area_median"] + te_s["log_area"].clip(lower=0)
        pred = np.mean([m.predict(te_s[nc + cb3.CAT_C]) for m, nc in zip(models, num_cols)], axis=0)
        m = cb1.mt(price, np.asarray(pred, dtype=float))
        verify[k] = {**{km: round(v, 4) for km, v in m.items()},
                     "wcut2_ref_MdAPE": WCUT2_REF[k]}
        if m["MdAPE"] >= COLD_REF_MDAPE / 1.5:
            raise AssertionError(f"k={k} 동결 모델 MdAPE {m['MdAPE']:.4f} — Cold 대비 1.5배 우위 미달")
    cgrp.LADDER = base_ladder

    # ── 동봉 예측기 스모크 테스트 (작가 1명, 이력 2건 시나리오 일치성)
    spec = importlib.util.spec_from_file_location("wl", BUNDLE / "predict" / "predict_warm_lite_v0_1.py")
    wl = importlib.util.module_from_spec(spec); spec.loader.exec_module(wl)
    a0 = wtest["artist_key"].iloc[0]
    hist = train[train["artist_key"] == a0].head(2)
    smoke = wl.predict(wtest[wtest["artist_key"] == a0].head(3), hist, models=None, params=params) \
        if False else wl.predict(wtest[wtest["artist_key"] == a0].head(3), hist,
                                 models=models, params=params)
    assert smoke["confidence_grade"].eq("warm_lite_standard").all()
    assert np.isfinite(smoke["warm_lite_pred_log"]).all()

    policy = {"version": "v0.1", "name": "warm_lite_v0.1",
              "status": "adopted_third_routing_path",
              "metrics_frozen_model_truncated_inference": verify,
              "wcut2_per_k_retrained_reference_MdAPE": WCUT2_REF,
              "cold_same_rows_reference": {"MdAPE": "0.47~0.49", "p95": "2.5~2.8"},
              "honest_note": "수치는 이력 5+ 작가의 절단 시뮬레이션 — 진짜 1~4건 작가(신진/무명)에선 "
                             "낙관 추정 가능, 운영 반영 시 신규 트래픽 모니터링 전제. k=1은 tail 변동 커서 차등 등급",
              "prohibitions": ["0604 사용 금지", "매칭 미검증 작가 적용 금지(Cold로)"]}
    (BUNDLE / "config" / "warm_lite_policy_v0_1.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")
    (BUNDLE / "README.md").write_text(
        "# Warm-lite v0.1 (이력 1~4건 고신뢰 매칭 작가 전용 경로)\n\n"
        "PP-WCUT1/2 검증, PP-WMATCH1 전제. 기존 Warm/Cold 유지 + 3-경로 라우팅.\n"
        "재생성: `python3 scripts/track6/freeze_warm_lite_artifact_v0_1.py`\n"
        "예측기: `predict/predict_warm_lite_v0_1.py` (입력: 작품 피처 + 작가 이력 1~4건)\n",
        encoding="utf-8")
    (BUNDLE / "reports" / "warm_lite_release_v0_1.md").write_text("\n".join([
        "# Warm-lite v0.1 release", f"- 동결일: {FREEZE_TS} / 채택: 2026-06-12 사용자 결정",
        "- 동결 모델 + k건 절단 추론 통계 검증 (vs WCUT2 per-k 재학습 참조):",
        json.dumps(verify, ensure_ascii=False, indent=1),
        "- k=1 차등 등급(warm_lite_low) 동결, 라우팅 전제(매칭 >=0.90) 명시"]), encoding="utf-8")

    files = sorted(p for p in BUNDLE.rglob("*") if p.is_file() and "manifest" not in p.parts)
    (BUNDLE / "manifest" / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha(p)}  {p.relative_to(BUNDLE)}" for p in files) + "\n", encoding="utf-8")
    print(json.dumps(verify, ensure_ascii=False, indent=1))
    print(f"[WLITE] bundle files: {len(files)}")


if __name__ == "__main__":
    main()
