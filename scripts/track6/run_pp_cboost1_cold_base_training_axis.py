#!/usr/bin/env python3
"""PP-CBOOST1: Cold base 학습 축 검증 (시드 앙상블 / 이종 계열 / 미니 HPO / 이종 blend).

보정·신호·정책 축 전수 소진 후 남은 base 학습 축을 검증한다. 대상은
raw-input 운영 base(v0.2 계열, search-free) — 연구 base(v0.3)는 상류 동결.

후보:
  A  single_seed      : 현행 v0.2 방식 (단일 seed)
  B  seed_mean5       : LGB Quantile 5-seed 평균 (Warm 기준가 방식)
  C  linear_huber_grp : 선형 Huber + 비작가 그룹 가격 통계 (Warm 기준가의 Cold판,
                        CGRP1과 달리 트리 피처가 아니라 선형 모델 본체로 사용)
  D  blend(B,C)       : 이종 계열 blend w∈{0.1..0.5} — CCORR2의 '후보 다양성
                        부재'를 깨는 시도
  E  mini-HPO 3종     : lr/leaves 변형 LGB

게이트(경량): validation defense 기준 선택(p95 비악화+MAPE 개선 vs B) →
artist-cluster bootstrap 400회 >=0.90 → fixed test 1회. 0604 미사용.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py")
cgrp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cgrp)

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-CBOOST1_cold_base_training_axis"
CATEGORICAL = {"medium_category", "support_category", "size_bucket", "support_size_bucket"}
QUANTILES = {"q10": 0.10, "q40": 0.40, "q50": 0.50, "q90": 0.90}
SEEDS = [20260610, 20260611, 20260612, 20260613, 20260614]
HPO = {"hpo_lr02_lv63": dict(learning_rate=0.02, num_leaves=63, n_estimators=1400),
       "hpo_lr06_lv15": dict(learning_rate=0.06, num_leaves=15, n_estimators=600),
       "hpo_lr035_lv63": dict(learning_rate=0.035, num_leaves=63, n_estimators=900)}
BLEND_W = [0.1, 0.2, 0.3, 0.4, 0.5]
N_BOOT = 400


def lgb_pipe(features, alpha, seed, **over):
    num = [f for f in features if f not in CATEGORICAL]
    cat = [f for f in features if f in CATEGORICAL]
    tr = [("num", Pipeline([("i", SimpleImputer(strategy="median"))]), num)]
    if cat:
        tr.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat))
    params = dict(objective="quantile", alpha=alpha, n_estimators=900, learning_rate=0.035,
                  num_leaves=31, min_child_samples=35, subsample=0.9, colsample_bytree=0.9,
                  reg_lambda=1.2, random_state=seed, verbosity=-1)
    params.update(over)
    return Pipeline([("prep", ColumnTransformer(tr)), ("model", LGBMRegressor(**params))])


def mt(price, pred_log):
    pp = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    a = np.abs(pp - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(a)), "MAPE": float(np.mean(a)),
            "p95_APE": float(np.quantile(a, 0.95))}


def defense(rep, q40, width, guard=None):
    if guard is None:
        guard = {"w67": float(np.quantile(width, 0.67)), "g50": float(np.quantile(rep - q40, 0.50))}
    m = (width >= guard["w67"]) & ((rep - q40) >= guard["g50"]) & (q40 < rep)
    out = rep.copy()
    out[m] = 0.5 * rep[m] + 0.5 * q40[m]
    return out, guard


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260610)

    feats = artifact_features()["cold_lightgbm"]
    train, val, test = load_scope("cold", feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area",
                                       "price_krw", "artist_key"]))
    train = train[need].reset_index(drop=True)
    val, test = val.reset_index(drop=True), test.reset_index(drop=True)
    y = train["ln_price_krw"].to_numpy(dtype=float)

    # LGB: 5-seed × 4분위 (A=seed0, B=mean)
    seed_preds = {s: {} for s in SEEDS}
    for s in SEEDS:
        for q, a in QUANTILES.items():
            m = lgb_pipe(feats, a, s).fit(train[feats], y)
            seed_preds[s][q] = {"val": m.predict(val[feats]), "test": m.predict(test[feats])}

    def pack(getter):
        return {sp: {q: getter(sp, q) for q in QUANTILES} for sp in ("val", "test")}

    cands = {"A_single_seed": pack(lambda sp, q: np.asarray(seed_preds[SEEDS[0]][q][sp], dtype=float)),
             "B_seed_mean5": pack(lambda sp, q: np.mean([seed_preds[s][q][sp] for s in SEEDS], axis=0))}
    for name, over in HPO.items():
        ms = {q: lgb_pipe(feats, a, SEEDS[0], **over).fit(train[feats], y) for q, a in QUANTILES.items()}
        cands[f"E_{name}"] = {sp: {q: np.asarray(ms[q].predict((val if sp == "val" else test)[feats]), dtype=float)
                                   for q in QUANTILES} for sp in ("val", "test")}

    # C: 선형 Huber + 그룹 통계 (CGRP1 사다리 재사용, fold-제외 train 통계)
    train_s = cgrp.train_with_internal_stats(train)
    val_s = cgrp.assign_group_stats(train, val)
    test_s = cgrp.assign_group_stats(train, test)
    num_c = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
             "has_depth", "is_3d_candidate"] + cgrp.GRP_FULL
    cat_c = ["medium_category", "support_category", "size_bucket"]
    hub = Pipeline([("prep", ColumnTransformer([
        ("num", Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())]), num_c),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_c)])),
        ("m", HuberRegressor(epsilon=1.35, alpha=1e-4, max_iter=4000))]).fit(train_s[num_c + cat_c], y)
    c_pred = {"val": np.asarray(hub.predict(val_s[num_c + cat_c]), dtype=float),
              "test": np.asarray(hub.predict(test_s[num_c + cat_c]), dtype=float)}

    # 평가표 (defense 기준, guard는 validation label-free)
    rows, store = [], {}
    for cname, P in cands.items():
        vrep = P["val"]["q50"]
        vdef, guard = defense(vrep, P["val"]["q40"], P["val"]["q90"] - P["val"]["q10"])
        tdef, _ = defense(P["test"]["q50"], P["test"]["q40"],
                          P["test"]["q90"] - P["test"]["q10"], guard)
        store[cname] = {"val": vdef, "test": tdef}
        rows.append({"candidate": cname, **{f"val_{k}": v for k, v in
                     mt(val["price_krw"].to_numpy(), vdef).items()},
                     **{f"test_{k}": v for k, v in mt(test["price_krw"].to_numpy(), tdef).items()}})
    # C 단독 + D blend (B의 quantile로 guard)
    B = cands["B_seed_mean5"]
    for w in [1.0] + BLEND_W:
        name = "C_linear_huber_grp" if w == 1.0 else f"D_blend_w{w}"
        vrep = (1 - (w if w < 1 else 1)) * B["val"]["q50"] + (w if w < 1 else 1) * c_pred["val"] \
            if w < 1 else c_pred["val"]
        trep = (1 - w) * B["test"]["q50"] + w * c_pred["test"] if w < 1 else c_pred["test"]
        vdef, guard = defense(vrep, B["val"]["q40"], B["val"]["q90"] - B["val"]["q10"])
        tdef, _ = defense(trep, B["test"]["q40"], B["test"]["q90"] - B["test"]["q10"], guard)
        store[name] = {"val": vdef, "test": tdef}
        rows.append({"candidate": name, **{f"val_{k}": v for k, v in
                     mt(val["price_krw"].to_numpy(), vdef).items()},
                     **{f"test_{k}": v for k, v in mt(test["price_krw"].to_numpy(), tdef).items()}})
    summary = pd.DataFrame(rows).sort_values("val_MAPE")
    summary.to_csv(EXP / "outputs" / "candidate_metrics.csv", index=False)

    # artist-cluster bootstrap vs B (validation)
    vb = store["B_seed_mean5"]["val"]
    price_v = val["price_krw"].to_numpy(dtype=float)
    groups = pd.Series(np.arange(len(val))).groupby(val["artist_key"].astype(str).to_numpy()).apply(list)
    boot_rows = []
    bsel = summary[(summary["candidate"] != "B_seed_mean5")
                   & (summary["val_MAPE"] < float(summary.loc[summary["candidate"] == "B_seed_mean5",
                                                              "val_MAPE"].iloc[0]))]
    for cname in list(bsel["candidate"]) or ["A_single_seed"]:
        cv = store[cname]["val"]
        wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
        for _ in range(N_BOOT):
            arts = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[a] for a in arts])
            bm, cm = mt(price_v[idx], vb[idx]), mt(price_v[idx], cv[idx])
            wins["MAPE"] += cm["MAPE"] < bm["MAPE"]
            wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
            wins["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
        boot_rows.append({"candidate": cname, **{f"p_{k}": v / N_BOOT for k, v in wins.items()}})
    boot = pd.DataFrame(boot_rows)
    boot.to_csv(EXP / "outputs" / "validation_artist_bootstrap_vs_seedmean.csv", index=False)

    cfg = {"experiment_id": "PP-CBOOST1", "seeds": SEEDS, "hpo": HPO, "blend_w": BLEND_W,
           "scope": "raw-input 운영 base 축 (연구 base는 상류 동결)",
           "gate": "validation defense 선택 + artist-cluster bootstrap>=0.90 vs B + fixed test 1회",
           "prohibitions": ["0604 사용 금지", "test 후보 선택 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-CBOOST1 base 학습 축\n\n" + summary.round(4).to_string(index=False)
        + "\n\n## bootstrap vs seed_mean5\n\n" + boot.round(4).to_string(index=False), encoding="utf-8")
    print(summary.round(4).to_string(index=False))
    print()
    print(boot.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
