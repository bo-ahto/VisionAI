#!/usr/bin/env python3
"""PP-CBOOST2: 이종 blend 안정화 (CBOOST1 후속, Cold 재개 1순위).

CBOOST1에서 유일하게 val+test 동방향 개선을 보인 이종 계열 blend(LGB seed-mean
+ 선형 Huber·그룹통계)를 MdAPE 희생 없이 안정화한다.

- C 강화: 비교군 면적단가 기반 price proxy(grp_unit_area_median + log_area) 추가
- 합의 게이트: |B−C|가 validation 분위수(q50/q67) 이하인 행만 blend (중앙 보호)
- 이동량 cap(0.05/0.10), w(0.3/0.4/0.5)
- 선택: validation MdAPE 비악화(+0.002 이내) + MAPE 개선 → artist-cluster
  bootstrap 400회 vs B (MAPE/p95>=0.90, MdAPE>=0.50) → pseudo-cold 3 seed
  방향 일치 → fixed test 1회. 0604 미사용.
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

for name in ("cgrp", "cb1"):
    pass
_s = importlib.util.spec_from_file_location("cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py")
cgrp = importlib.util.module_from_spec(_s); _s.loader.exec_module(cgrp)
_s2 = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s2); _s2.loader.exec_module(cb1)

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-CBOOST2_cold_hetero_blend_stabilization"
SEEDS = [20260610, 20260611, 20260612, 20260613, 20260614]
WS = [0.3, 0.4, 0.5]
GATES = {"agree_q50": 0.50, "agree_q67": 0.67, "none": None}
CAPS = [0.05, 0.10, np.inf]
N_BOOT = 400


def fit_C(train_s, frames):
    num_c = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
             "has_depth", "is_3d_candidate", "grp_price_proxy"] + cgrp.GRP_FULL
    cat_c = ["medium_category", "support_category", "size_bucket"]
    for f in [train_s] + list(frames.values()):
        f["grp_price_proxy"] = f["grp_unit_area_median"] + f["log_area"].clip(lower=0)
    hub = Pipeline([("prep", ColumnTransformer([
        ("num", Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())]), num_c),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_c)])),
        ("m", HuberRegressor(epsilon=1.35, alpha=1e-4, max_iter=4000))]).fit(
        train_s[num_c + cat_c], train_s["ln_price_krw"].to_numpy(dtype=float))
    return {k: np.asarray(hub.predict(v[num_c + cat_c]), dtype=float) for k, v in frames.items()}


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

    # B: 5-seed 평균 LGB quantiles
    B = {sp: {q: np.zeros(len(f)) for q in cb1.QUANTILES} for sp, f in (("val", val), ("test", test))}
    for s in SEEDS:
        for q, a in cb1.QUANTILES.items():
            m = cb1.lgb_pipe(feats, a, s).fit(train[feats], y)
            B["val"][q] += m.predict(val[feats]) / len(SEEDS)
            B["test"][q] += m.predict(test[feats]) / len(SEEDS)

    # C 강화
    train_s = cgrp.train_with_internal_stats(train)
    val_s = cgrp.assign_group_stats(train, val)
    test_s = cgrp.assign_group_stats(train, test)
    C = fit_C(train_s, {"val": val_s, "test": test_s})

    price = {"val": val["price_krw"].to_numpy(dtype=float), "test": test["price_krw"].to_numpy(dtype=float)}
    d_val = np.abs(B["val"]["q50"] - C["val"])
    thr = {g: (float(np.quantile(d_val, p)) if p else np.inf) for g, p in
           [("agree_q50", 0.50), ("agree_q67", 0.67), ("none", None)]}

    def make_pred(sp, w, gname, cap):
        b50 = B[sp]["q50"]
        move = np.clip(w * (C[sp] - b50), -cap, cap)
        mask = np.abs(b50 - C[sp]) <= thr[gname]
        rep = b50.copy(); rep[mask] = b50[mask] + move[mask]
        dfs, guard = cb1.defense(B["val"]["q50"], B["val"]["q40"], B["val"]["q90"] - B["val"]["q10"])
        out, _ = cb1.defense(rep, B[sp]["q40"], B[sp]["q90"] - B[sp]["q10"], guard)
        return out

    vb, _ = cb1.defense(B["val"]["q50"], B["val"]["q40"], B["val"]["q90"] - B["val"]["q10"])
    guard_b = None
    tb, _ = cb1.defense(B["test"]["q50"], B["test"]["q40"], B["test"]["q90"] - B["test"]["q10"],
                        cb1.defense(B["val"]["q50"], B["val"]["q40"], B["val"]["q90"] - B["val"]["q10"])[1])
    bm_v, bm_t = cb1.mt(price["val"], vb), cb1.mt(price["test"], tb)

    rows, store = [], {}
    for w in WS:
        for g in GATES:
            for cap in CAPS:
                name = f"w{w}_{g}_cap{cap if np.isfinite(cap) else 'inf'}"
                pv = make_pred("val", w, g, cap)
                m = cb1.mt(price["val"], pv)
                store[name] = (w, g, cap)
                rows.append({"candidate": name,
                             "val_dMdAPE": m["MdAPE"] - bm_v["MdAPE"],
                             "val_dMAPE": m["MAPE"] - bm_v["MAPE"],
                             "val_dp95": m["p95_APE"] - bm_v["p95_APE"]})
    oof = pd.DataFrame(rows).sort_values("val_dMAPE")
    oof.to_csv(EXP / "outputs" / "oof_candidate_metrics.csv", index=False)
    top = oof[(oof["val_dMdAPE"] <= 0.002) & (oof["val_dMAPE"] < 0)].head(3).to_dict("records")

    # bootstrap vs B
    groups = pd.Series(np.arange(len(val))).groupby(val["artist_key"].astype(str).to_numpy()).apply(list)
    boot_rows = []
    for c in top:
        pv = make_pred("val", *store[c["candidate"]])
        wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
        for _ in range(N_BOOT):
            arts = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[a] for a in arts])
            bmx, cmx = cb1.mt(price["val"][idx], vb[idx]), cb1.mt(price["val"][idx], pv[idx])
            wins["MAPE"] += cmx["MAPE"] < bmx["MAPE"]
            wins["p95"] += cmx["p95_APE"] < bmx["p95_APE"]
            wins["MdAPE"] += cmx["MdAPE"] <= bmx["MdAPE"]
        rec = {"candidate": c["candidate"], **{f"p_{k}": v / N_BOOT for k, v in wins.items()}}
        rec["gate_pass"] = rec["p_MAPE"] >= 0.90 and rec["p_p95"] >= 0.90 and rec["p_MdAPE"] >= 0.50
        boot_rows.append(rec)
    boot = pd.DataFrame(boot_rows)
    boot.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    # pseudo-cold 방향 (top1, 단일 seed B)
    pc_dir = []
    if top:
        w, g, cap = store[top[0]["candidate"]]
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
            Bp = {q: cb1.lgb_pipe(feats, a, SEEDS[0]).fit(tr_m[feats], ym).predict(pseudo[feats])
                  for q, a in cb1.QUANTILES.items()}
            tr_ms = cgrp.train_with_internal_stats(tr_m)
            ps_s = cgrp.assign_group_stats(tr_m, pseudo)
            Cp = fit_C(tr_ms, {"p": ps_s})["p"]
            b50 = np.asarray(Bp["q50"], dtype=float)
            move = np.clip(w * (Cp - b50), -cap, cap)
            mask = np.abs(b50 - Cp) <= thr[g]
            rep = b50.copy(); rep[mask] = b50[mask] + move[mask]
            pp = pseudo["price_krw"].to_numpy(dtype=float)
            pc_dir.append({"seed": pseed,
                           "blend_improves_MAPE": bool(cb1.mt(pp, rep)["MAPE"] < cb1.mt(pp, b50)["MAPE"])})

    # fixed test (top 후보)
    trec = [{"candidate": "B_seed_mean5", **bm_t}]
    for c in top:
        pt = make_pred("test", *store[c["candidate"]])
        trec.append({"candidate": c["candidate"], **cb1.mt(price["test"], pt)})
    test_df = pd.DataFrame(trec)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    cfg = {"experiment_id": "PP-CBOOST2", "ws": WS, "gates": {k: thr[k] for k in thr},
           "caps": [c if np.isfinite(c) else "inf" for c in CAPS],
           "C_enhancement": "grp_price_proxy = grp_unit_area_median + log_area",
           "pseudo_cold_direction": pc_dir,
           "prohibitions": ["0604 사용 금지", "test 후보 선택 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-CBOOST2 이종 blend 안정화\n\n" + oof.head(10).round(5).to_string(index=False)
        + "\n\n" + (boot.round(4).to_string(index=False) if len(boot) else "(선택 후보 없음)")
        + "\n\n" + json.dumps(pc_dir, ensure_ascii=False)
        + "\n\n" + test_df.round(4).to_string(index=False), encoding="utf-8")
    print(oof.head(8).round(5).to_string(index=False))
    print(boot.round(4).to_string(index=False) if len(boot) else "(no candidates)")
    print(json.dumps(pc_dir, ensure_ascii=False))
    print(test_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
