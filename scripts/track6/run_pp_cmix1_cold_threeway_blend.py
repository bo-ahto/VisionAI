#!/usr/bin/env python3
"""PP-CMIX1: 작가 가중 학습 + kNN 제3계열 + 3원 blend (브레인스토밍 (a)+(d)).

비교 기준 = v0.5 동결 blend(B 0.7 + C 0.3). 신규 요소:
- B': LGB Quantile 5-seed, 표본 가중 1/sqrt(작가 train 행수) — 대형 작가
  과적합 완화로 작가 구성 이동(val→test) 강건화 시도
- D: kNN 국소 비모수 회귀(k=25, distance 가중) — 트리/선형과 다른 제3계열
- 3원 convex blend grid(tree∈{B,B'} × wT/wC/wD), 선택은 validation
  (MdAPE 비악화 + MAPE 개선 vs v0.5) → bootstrap+subsample 게이트 →
  pseudo-cold 방향 → fixed test 1회. 0604 미사용.
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
from sklearn.neighbors import KNeighborsRegressor
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
EXP = REPO / "experiments" / "track6" / "PP-CMIX1_cold_threeway_blend"
SEEDS = [20260610, 20260611, 20260612, 20260613, 20260614]
KNN_K = 25
WT = [0.5, 0.6, 0.7, 0.8]
WC = [0.0, 0.1, 0.2, 0.3]
N_BOOT = 400
N_SUB = 200
NUM_D = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]
CAT_D = ["medium_category", "support_category", "size_bucket"]


def train_B(train, val, test, feats, y, weights=None):
    out = {sp: {q: np.zeros(len(f)) for q in cb1.QUANTILES} for sp, f in (("val", val), ("test", test))}
    for s in SEEDS:
        for q, a in cb1.QUANTILES.items():
            m = cb1.lgb_pipe(feats, a, s)
            m.fit(train[feats], y, model__sample_weight=weights)
            out["val"][q] += m.predict(val[feats]) / len(SEEDS)
            out["test"][q] += m.predict(test[feats]) / len(SEEDS)
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
    aw = 1.0 / np.sqrt(train.groupby("artist_key")["artist_key"].transform("size").to_numpy(dtype=float))

    B = train_B(train, val, test, feats, y)
    Bw = train_B(train, val, test, feats, y, weights=aw)

    train_s = cgrp.train_with_internal_stats(train)
    val_s = cgrp.assign_group_stats(train, val)
    test_s = cgrp.assign_group_stats(train, test)
    C = cb3.fit_C_ens(train_s, {"val": val_s, "test": test_s})

    knn = Pipeline([("prep", ColumnTransformer([
        ("num", Pipeline([("i", SimpleImputer(strategy="median")), ("s", StandardScaler())]), NUM_D),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_D)])),
        ("m", KNeighborsRegressor(n_neighbors=KNN_K, weights="distance"))]).fit(train[NUM_D + CAT_D], y)
    D = {"val": np.asarray(knn.predict(val[NUM_D + CAT_D]), dtype=float),
         "test": np.asarray(knn.predict(test[NUM_D + CAT_D]), dtype=float)}

    price = {"val": val["price_krw"].to_numpy(dtype=float), "test": test["price_krw"].to_numpy(dtype=float)}
    trees = {"B": B, "Bw": Bw}
    guards = {t: cb1.defense(P["val"]["q50"], P["val"]["q40"], P["val"]["q90"] - P["val"]["q10"])[1]
              for t, P in trees.items()}

    def mk(sp, tree, wt, wc):
        P = trees[tree]
        rep = wt * P[sp]["q50"] + wc * C[sp] + (1 - wt - wc) * D[sp]
        return cb1.defense(rep, P[sp]["q40"], P[sp]["q90"] - P[sp]["q10"], guards[tree])[0]

    # 기준 = v0.5 blend (B, 0.7/0.3/0)
    v5 = {sp: mk(sp, "B", 0.7, 0.3) for sp in ("val", "test")}
    rm = cb1.mt(price["val"], v5["val"])

    rows = []
    for tree in trees:
        for wt in WT:
            for wc in WC:
                if 1 - wt - wc < 0 or (tree == "B" and wt == 0.7 and wc == 0.3):
                    continue
                m = cb1.mt(price["val"], mk("val", tree, wt, wc))
                rows.append({"tree": tree, "wt": wt, "wc": wc, "wd": round(1 - wt - wc, 2),
                             "val_dMdAPE": m["MdAPE"] - rm["MdAPE"],
                             "val_dMAPE": m["MAPE"] - rm["MAPE"],
                             "val_dp95": m["p95_APE"] - rm["p95_APE"]})
    oof = pd.DataFrame(rows).sort_values("val_dMAPE")
    oof.to_csv(EXP / "outputs" / "oof_candidate_metrics.csv", index=False)
    top = oof[(oof["val_dMdAPE"] <= 0.002) & (oof["val_dMAPE"] < 0)].head(3).to_dict("records")

    arts = val["artist_key"].astype(str).to_numpy()
    groups = pd.Series(np.arange(len(val))).groupby(arts).apply(list)
    uniq = np.unique(arts)
    gate_rows = []
    for c in top:
        pv = mk("val", c["tree"], c["wt"], c["wc"])
        rec = {k: c[k] for k in ("tree", "wt", "wc", "wd")}
        wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
        for _ in range(N_BOOT):
            a = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[g] for g in a])
            bm, cm = cb1.mt(price["val"][idx], v5["val"][idx]), cb1.mt(price["val"][idx], pv[idx])
            wins["MAPE"] += cm["MAPE"] < bm["MAPE"]; wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
            wins["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
        for k in wins:
            rec[f"boot_p_{k}"] = wins[k] / N_BOOT
        for frac in (0.80, 0.70):
            wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
            for _ in range(N_SUB):
                keep = set(rng.choice(uniq, size=int(len(uniq) * frac), replace=False))
                idx = np.where(np.isin(arts, list(keep)))[0]
                bm, cm = cb1.mt(price["val"][idx], v5["val"][idx]), cb1.mt(price["val"][idx], pv[idx])
                wins["MAPE"] += cm["MAPE"] < bm["MAPE"]; wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
                wins["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
            for k in wins:
                rec[f"sub{frac}_p_{k}"] = wins[k] / N_SUB
        rec["gate_pass"] = all(rec[f"{s}_p_MAPE"] >= 0.90 and rec[f"{s}_p_p95"] >= 0.90
                               and rec[f"{s}_p_MdAPE"] >= 0.50 for s in ("boot", "sub0.8", "sub0.7"))
        gate_rows.append(rec)
    gate = pd.DataFrame(gate_rows)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    trec = [{"candidate": "v0.5_blend(B,0.7C0.3)", **cb1.mt(price["test"], v5["test"])}]
    for c in top:
        trec.append({"candidate": f"{c['tree']}_wt{c['wt']}_wc{c['wc']}_wd{c['wd']}",
                     **cb1.mt(price["test"], mk("test", c["tree"], c["wt"], c["wc"]))})
    test_df = pd.DataFrame(trec)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    cfg = {"experiment_id": "PP-CMIX1", "knn_k": KNN_K, "grid": {"WT": WT, "WC": WC},
           "artist_weight": "1/sqrt(train artist rows)",
           "reference": "v0.5 blend (B unweighted, 0.7/0.3/0)",
           "prohibitions": ["0604 사용 금지", "test 후보 선택 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-CMIX1 3원 blend\n\n" + oof.head(12).round(5).to_string(index=False)
        + "\n\n" + (gate.round(4).to_string(index=False) if len(gate) else "(후보 없음)")
        + "\n\n" + test_df.round(4).to_string(index=False), encoding="utf-8")
    print(oof.head(10).round(5).to_string(index=False))
    print(gate.round(4).to_string(index=False) if len(gate) else "(no candidates)")
    print(test_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
