#!/usr/bin/env python3
"""Cold prediction v0.5 동결 (PP-COLD-ARTIFACT5): 이종 blend 운영 옵션.

PP-CBOOST3 대표 후보(w0.3, p95 방어 목적, 2026-06-10 사용자 채택 결정)를
raw-input 실행형 번들로 직렬화하고, CBOOST3 fixed test 지표 재현을 검증한다.

- B: LGB Quantile(n_est 900) 5-seed × 4분위 joblib (비추적, 본 스크립트로 재생성)
- C: 선형 Huber 6구성 joblib + 그룹통계 사다리 테이블 JSON (full-train 동결)
- blend w=0.3, guard는 validation label-free 분위수 동결
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
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_s = importlib.util.spec_from_file_location("cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py")
cgrp = importlib.util.module_from_spec(_s); _s.loader.exec_module(cgrp)
_s2 = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s2); _s2.loader.exec_module(cb1)
_s3 = importlib.util.spec_from_file_location("cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py")
cb3 = importlib.util.module_from_spec(_s3); _s3.loader.exec_module(cb3)

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.5_operational"
CB3_TEST = REPO / "experiments" / "track6" / "PP-CBOOST3_cold_hetero_blend_gate_retry" / "outputs" / "fixed_test_metrics.csv"
SEEDS = [20260610, 20260611, 20260612, 20260613, 20260614]
BLEND_W = 0.3
FREEZE_TS = "2026-06-10T12:00:00"


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
    train, val, test = load_scope("cold", feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area",
                                       "price_krw"]))
    train = train[need].reset_index(drop=True)
    val, test = val.reset_index(drop=True), test.reset_index(drop=True)
    y = train["ln_price_krw"].to_numpy(dtype=float)

    # B 직렬화 + 예측
    B = {sp: {q: np.zeros(len(f)) for q in cb1.QUANTILES} for sp, f in (("val", val), ("test", test))}
    for i, s in enumerate(SEEDS):
        for q, a in cb1.QUANTILES.items():
            m = cb1.lgb_pipe(feats, a, s).fit(train[feats], y)
            joblib.dump(m, BUNDLE / "models" / f"lgbq_{q}_seed{i}.joblib")
            B["val"][q] += m.predict(val[feats]) / len(SEEDS)
            B["test"][q] += m.predict(test[feats]) / len(SEEDS)

    # C 직렬화 — CBOOST3 레시피 그대로: 학습은 fold-제외 내부 통계(자기가격
    # leakage 차단), 추론(query)은 full-train 사다리 테이블 사용
    train_s = cgrp.train_with_internal_stats(train)
    val_s = cgrp.assign_group_stats(train, val)
    test_s = cgrp.assign_group_stats(train, test)
    for f in (train_s, val_s, test_s):
        f["grp_price_proxy"] = f["grp_unit_area_median"] + f["log_area"].clip(lower=0)
    cat_c = cb3.CAT_C
    huber_num_cols, C_val, C_test = [], np.zeros(len(val)), np.zeros(len(test))
    for i, cfg in enumerate(cb3.C_CONFIGS):
        num = cb3.NUM_BASE + cfg["extra"]
        pipe = Pipeline([("prep", ColumnTransformer([
            ("num", Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())]), num),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_c)])),
            ("m", HuberRegressor(epsilon=cfg["epsilon"], alpha=cfg["alpha"], max_iter=4000))])
        pipe.fit(train_s[num + cat_c], y)
        joblib.dump(pipe, BUNDLE / "models" / f"huber_c{i}.joblib")
        huber_num_cols.append(num)
        C_val += pipe.predict(val_s[num + cat_c]) / len(cb3.C_CONFIGS)
        C_test += pipe.predict(test_s[num + cat_c]) / len(cb3.C_CONFIGS)

    # 그룹통계 사다리 테이블 동결 (full train)
    ladder = []
    for keys, min_n in cgrp.LADDER:
        t = cgrp.group_stat_table(train, keys)
        t = t[t["grp_n"] >= min_n]
        table = {}
        for _, r in t.iterrows():
            k = "|".join(str(r[c]) for c in keys)
            table[k] = {"grp_log_price_median": float(r["grp_log_price_median"]),
                        "grp_log_price_q25": float(r["grp_log_price_q25"]),
                        "grp_log_price_q75": float(r["grp_log_price_q75"]),
                        "grp_log_price_iqr": float(r["grp_log_price_iqr"]),
                        "grp_unit_area_median": float(r["grp_unit_area_median"]),
                        "grp_unit_area_iqr": float(r["grp_unit_area_iqr"]),
                        "grp_n_log": float(np.log1p(r["grp_n"]))}
        ladder.append({"keys": keys, "min_n": min_n, "table": table})
    unit = train["ln_price_krw"] - train["log_area"].clip(lower=0)
    gfb = {"grp_log_price_median": float(train["ln_price_krw"].median()),
           "grp_log_price_q25": float(train["ln_price_krw"].quantile(0.25)),
           "grp_log_price_q75": float(train["ln_price_krw"].quantile(0.75)),
           "grp_unit_area_median": float(unit.median()),
           "grp_unit_area_iqr": float(unit.quantile(0.75) - unit.quantile(0.25)),
           "grp_n_log": float(np.log1p(len(train)))}
    gfb["grp_log_price_iqr"] = gfb["grp_log_price_q75"] - gfb["grp_log_price_q25"]

    # guard 임계값은 CBOOST3 레시피 그대로 blend 전 B q50 기준 (label-free)
    rep_v = B["val"]["q50"] + BLEND_W * (C_val - B["val"]["q50"])
    guard = cb1.defense(B["val"]["q50"], B["val"]["q40"], B["val"]["q90"] - B["val"]["q10"])[1]
    params = {"version": "v0.5", "frozen_at": FREEZE_TS, "blend_w": BLEND_W,
              "n_seeds": len(SEEDS), "n_huber": len(cb3.C_CONFIGS),
              "huber_num_cols": huber_num_cols, "huber_cat_cols": cat_c,
              "guard": {"width_q67": guard["w67"], "gap_q50": guard["g50"]},
              "ladder": ladder, "global_fallback": gfb,
              "decision": "2026-06-10 사용자 채택 — p95 방어 목적별 운영 옵션 (PP-CBOOST3)"}
    (BUNDLE / "config" / "blend_params_v0_5.json").write_text(
        json.dumps(params, ensure_ascii=False), encoding="utf-8")

    # 검증: 동봉 예측기로 test 재현 vs PP-CBOOST3 fixed test (자체 계산과 함께)
    spec = importlib.util.spec_from_file_location(
        "pred5", BUNDLE / "predict" / "predict_cold_operational_v0_5.py")
    p5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p5)
    out = p5.predict(test, params=params)
    got = cb1.mt(test["price_krw"].to_numpy(dtype=float), out["defense_pred_log"].to_numpy(dtype=float))
    ref = pd.read_csv(CB3_TEST)
    exp_row = ref[ref["candidate"] == "w0.3_adFalse"].iloc[0]
    diffs = {k: abs(got[k] - float(exp_row[k])) for k in ("MdAPE", "MAPE", "p95_APE")}
    if max(diffs.values()) > 2e-3:
        raise AssertionError(f"CBOOST3 재현 실패: got {got} expected {dict(exp_row)} diffs {diffs}")

    v_metrics = cb1.mt(val["price_krw"].to_numpy(dtype=float),
                       cb1.defense(rep_v, B["val"]["q40"], B["val"]["q90"] - B["val"]["q10"], guard)[0])
    policy = {"version": "v0.5", "status": "purpose_specific_p95_defense_option",
              "recipe": "0.7*LGB(5seed,900est) q50 + 0.3*linearHuber(6cfg, 비작가 그룹통계+price_proxy), q40 guard",
              "metrics_test_defense": got, "metrics_val_defense": v_metrics,
              "vs_frozen_v0_2_defense_test": {"MdAPE": 0.4852, "MAPE": 1.1771, "p95_APE": 4.1223},
              "honest_note": "동결 v0.2 대비 MdAPE -0.003/MAPE 동등/p95 -11.5%. MdAPE 반복 비악화 확률 0.12~0.28(PP-CBOOST3) — all-metric 후보 아님, p95 방어 목적 채택(사용자 결정)",
              "verification_abs_diff_vs_cboost3": diffs,
              "prohibitions": ["0604 사용 금지", "v0.2 단독 tier 표시 금지(기존 원칙 유지)"]}
    (BUNDLE / "config" / "cold_model_policy_v0_5.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")

    (BUNDLE / "README.md").write_text(
        "# Cold prediction v0.5 (operational, hetero blend — p95 방어 목적 옵션)\n\n"
        "PP-CBOOST1~3 검증 blend(w0.3) 동결. joblib 모델은 비추적 — 재생성:\n"
        "`python3 scripts/track6/freeze_cold_prediction_artifact_v0_5.py`\n"
        "예측기: `predict/predict_cold_operational_v0_5.py` (raw-input)\n", encoding="utf-8")
    (BUNDLE / "reports" / "cold_artifact_release_v0_5.md").write_text("\n".join([
        "# Cold artifact release v0.5 (hetero blend, p95 방어 목적)",
        f"- 동결일: {FREEZE_TS} / 채택: 2026-06-10 사용자 결정",
        f"- test defense: {got}",
        f"- 동결 v0.2 defense 대비: MdAPE -0.003 / MAPE 동등 / p95 4.122→{got['p95_APE']:.3f} (-11.5%)",
        f"- CBOOST3 재현 diff: {diffs}",
        "- 한계: MdAPE 반복 비악화 확률 0.12~0.28 — all-metric 교체 아님. 기본 서빙은 v0.3+v0.4 유지,",
        "  v0.5는 raw-input 환경 p95 방어 모드.",
    ]), encoding="utf-8")

    files = sorted(p for p in BUNDLE.rglob("*") if p.is_file() and "manifest" not in p.parts)
    (BUNDLE / "manifest" / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha(p)}  {p.relative_to(BUNDLE)}" for p in files) + "\n", encoding="utf-8")
    print(f"[ARTIFACT5] test defense: {got}")
    print(f"[ARTIFACT5] CBOOST3 diff: {diffs}")
    print(f"[ARTIFACT5] files: {len(files)}")


if __name__ == "__main__":
    main()
