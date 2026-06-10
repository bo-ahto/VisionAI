#!/usr/bin/env python3
"""PP-CBOOST3: 이종 blend 게이트 재도전 (CBOOST2 후속, Cold 재개 1순위).

CBOOST2 대표 후보(w0.3, val/pseudo/test 전 축 동방향 개선)의 남은 문제는
작가 재표집 반복 안정성(bootstrap 0.87/0.76/0.25). 후보 자체의 분산을 줄여
게이트 통과를 시도한다.

- C 앙상블: 선형 Huber 6구성(alpha {1e-4,1e-3} × epsilon {1.2,1.35,1.5} 대표
  조합 + 피처셋 변형) 평균 → C 분산 축소
- w 미세 grid {0.20,0.25,0.30,0.35} + 적응 변형(최정밀 매칭 행만 blend)
- 이중 게이트: artist-cluster bootstrap 400회 + artist 80%/70% subsample
  200회 — 양쪽 모두 MAPE/p95 >=0.90, MdAPE >=0.50
- pseudo-cold 3 seed 방향 + fixed test 1회. 0604 미사용.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-CBOOST3_cold_hetero_blend_gate_retry"
SEEDS = [20260610, 20260611, 20260612, 20260613, 20260614]
WS = [0.20, 0.25, 0.30, 0.35]
N_BOOT = 400
N_SUB = 200
NUM_BASE = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
            "has_depth", "is_3d_candidate", "grp_price_proxy"]
CAT_C = ["medium_category", "support_category", "size_bucket"]
C_CONFIGS = [
    dict(alpha=1e-4, epsilon=1.35, extra=cgrp.GRP_FULL),
    dict(alpha=1e-3, epsilon=1.35, extra=cgrp.GRP_FULL),
    dict(alpha=1e-4, epsilon=1.20, extra=cgrp.GRP_FULL),
    dict(alpha=1e-4, epsilon=1.50, extra=cgrp.GRP_FULL),
    dict(alpha=1e-4, epsilon=1.35, extra=cgrp.GRP_LEAN),
    dict(alpha=1e-3, epsilon=1.50, extra=cgrp.GRP_LEAN),
]


def fit_C_ens(train_s, frames):
    for f in [train_s] + list(frames.values()):
        f["grp_price_proxy"] = f["grp_unit_area_median"] + f["log_area"].clip(lower=0)
    y = train_s["ln_price_krw"].to_numpy(dtype=float)
    out = {k: np.zeros(len(v)) for k, v in frames.items()}
    for cfg in C_CONFIGS:
        num = NUM_BASE + cfg["extra"]
        pipe = Pipeline([("prep", ColumnTransformer([
            ("num", Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())]), num),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_C)])),
            ("m", HuberRegressor(epsilon=cfg["epsilon"], alpha=cfg["alpha"], max_iter=4000))])
        pipe.fit(train_s[num + CAT_C], y)
        for k, v in frames.items():
            out[k] += np.asarray(pipe.predict(v[num + CAT_C]), dtype=float) / len(C_CONFIGS)
    return out


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

    B = {sp: {q: np.zeros(len(f)) for q in cb1.QUANTILES} for sp, f in (("val", val), ("test", test))}
    for s in SEEDS:
        for q, a in cb1.QUANTILES.items():
            m = cb1.lgb_pipe(feats, a, s).fit(train[feats], y)
            B["val"][q] += m.predict(val[feats]) / len(SEEDS)
            B["test"][q] += m.predict(test[feats]) / len(SEEDS)

    train_s = cgrp.train_with_internal_stats(train)
    val_s = cgrp.assign_group_stats(train, val)
    test_s = cgrp.assign_group_stats(train, test)
    C = fit_C_ens(train_s, {"val": val_s, "test": test_s})
    lvl1 = {"val": (val_s["grp_match_level"] == 1.0).to_numpy(),
            "test": (test_s["grp_match_level"] == 1.0).to_numpy()}

    price = {"val": val["price_krw"].to_numpy(dtype=float), "test": test["price_krw"].to_numpy(dtype=float)}
    vguard = cb1.defense(B["val"]["q50"], B["val"]["q40"], B["val"]["q90"] - B["val"]["q10"])[1]

    def pred(sp, w, adaptive):
        b50 = B[sp]["q50"]
        rep = b50 + w * (C[sp] - b50) * (lvl1[sp] if adaptive else 1.0)
        return cb1.defense(rep, B[sp]["q40"], B[sp]["q90"] - B[sp]["q10"], vguard)[0]

    vb = cb1.defense(B["val"]["q50"], B["val"]["q40"], B["val"]["q90"] - B["val"]["q10"], vguard)[0]
    tb = cb1.defense(B["test"]["q50"], B["test"]["q40"], B["test"]["q90"] - B["test"]["q10"], vguard)[0]
    bm_v = cb1.mt(price["val"], vb)

    rows = []
    for w in WS:
        for ad in (False, True):
            m = cb1.mt(price["val"], pred("val", w, ad))
            rows.append({"w": w, "adaptive": ad,
                         "val_dMdAPE": m["MdAPE"] - bm_v["MdAPE"],
                         "val_dMAPE": m["MAPE"] - bm_v["MAPE"],
                         "val_dp95": m["p95_APE"] - bm_v["p95_APE"]})
    oof = pd.DataFrame(rows).sort_values("val_dMAPE")
    oof.to_csv(EXP / "outputs" / "oof_candidate_metrics.csv", index=False)
    top = oof[(oof["val_dMdAPE"] <= 0.002) & (oof["val_dMAPE"] < 0)].head(3).to_dict("records")

    arts = val["artist_key"].astype(str).to_numpy()
    groups = pd.Series(np.arange(len(val))).groupby(arts).apply(list)
    uniq = np.unique(arts)
    gate_rows = []
    for c in top:
        pv = pred("val", c["w"], c["adaptive"])
        rec = {"w": c["w"], "adaptive": c["adaptive"]}
        wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
        for _ in range(N_BOOT):
            a = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[g] for g in a])
            bm, cm = cb1.mt(price["val"][idx], vb[idx]), cb1.mt(price["val"][idx], pv[idx])
            wins["MAPE"] += cm["MAPE"] < bm["MAPE"]; wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
            wins["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
        for k in wins:
            rec[f"boot_p_{k}"] = wins[k] / N_BOOT
        for frac in (0.80, 0.70):
            wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
            n = 0
            for _ in range(N_SUB):
                keep = set(rng.choice(uniq, size=int(len(uniq) * frac), replace=False))
                idx = np.where(np.isin(arts, list(keep)))[0]
                bm, cm = cb1.mt(price["val"][idx], vb[idx]), cb1.mt(price["val"][idx], pv[idx])
                n += 1
                wins["MAPE"] += cm["MAPE"] < bm["MAPE"]; wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
                wins["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
            for k in wins:
                rec[f"sub{frac}_p_{k}"] = wins[k] / n
        rec["gate_pass"] = all(rec[f"{s}_p_MAPE"] >= 0.90 and rec[f"{s}_p_p95"] >= 0.90
                               and rec[f"{s}_p_MdAPE"] >= 0.50
                               for s in ("boot", "sub0.8", "sub0.7"))
        gate_rows.append(rec)
    gate = pd.DataFrame(gate_rows)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    pc_dir = []
    if top:
        c = top[0]
        counts = train.groupby("artist_key").size()
        pool = counts[(counts >= 3) & (counts <= 10)].index.to_numpy()
        for pseed in SEEDS[:3]:
            prng = np.random.default_rng(pseed)
            masked, tot = [], 0
            for a in prng.permutation(pool):
                if tot >= 1200 or len(masked) >= 250:
                    break
                masked.append(a); tot += int(counts[a])
            is_m = train["artist_key"].isin(set(masked))
            tr_m, pseudo = train[~is_m].reset_index(drop=True), train[is_m].reset_index(drop=True)
            ym = tr_m["ln_price_krw"].to_numpy(dtype=float)
            b50 = np.asarray(cb1.lgb_pipe(feats, 0.50, SEEDS[0]).fit(tr_m[feats], ym)
                             .predict(pseudo[feats]), dtype=float)
            tr_ms = cgrp.train_with_internal_stats(tr_m)
            ps_s = cgrp.assign_group_stats(tr_m, pseudo)
            Cp = fit_C_ens(tr_ms, {"p": ps_s})["p"]
            mk = (ps_s["grp_match_level"] == 1.0).to_numpy() if c["adaptive"] else 1.0
            rep = b50 + c["w"] * (Cp - b50) * mk
            pp = pseudo["price_krw"].to_numpy(dtype=float)
            pc_dir.append({"seed": pseed,
                           "improves_MAPE": bool(cb1.mt(pp, rep)["MAPE"] < cb1.mt(pp, b50)["MAPE"])})

    trec = [{"candidate": "B_seed_mean5", **cb1.mt(price["test"], tb)}]
    for c in top:
        trec.append({"candidate": f"w{c['w']}_ad{c['adaptive']}",
                     **cb1.mt(price["test"], pred("test", c["w"], c["adaptive"]))})
    test_df = pd.DataFrame(trec)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    cfg = {"experiment_id": "PP-CBOOST3", "C_configs": len(C_CONFIGS), "ws": WS,
           "gate": "bootstrap400 + artist subsample 80/70% 200회, 전 스킴 MAPE/p95>=0.90 & MdAPE>=0.50",
           "pseudo_cold_direction": pc_dir,
           "prohibitions": ["0604 사용 금지", "test 후보 선택 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-CBOOST3 이종 blend 게이트 재도전\n\n" + oof.round(5).to_string(index=False)
        + "\n\n" + (gate.round(4).to_string(index=False) if len(gate) else "(후보 없음)")
        + "\n\n" + json.dumps(pc_dir, ensure_ascii=False)
        + "\n\n" + test_df.round(4).to_string(index=False), encoding="utf-8")
    print(oof.round(5).to_string(index=False))
    print(gate.round(4).to_string(index=False) if len(gate) else "(no candidates)")
    print(json.dumps(pc_dir, ensure_ascii=False))
    print(test_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
