#!/usr/bin/env python3
"""PP-CSRCH2 stage2+3: 수집 150작가 delta 파생 + pseudo-cold 3자 비교."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope
import importlib.util
_s = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s); _s.loader.exec_module(cb1)
REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-CSRCH2_cold_search_collection_expansion"
H23 = {"high": 0.20, "low": -0.20, "none": -0.031295}  # 동결 v0.3 보정맵

std = pd.read_csv(REPO / "data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv", low_memory=False)
gm = std.assign(is_gm=std["source_group"].eq("gallery_museum")).groupby("artist_search_name")["is_gm"].mean()
pos = gm[gm > 0]
thr = float(pos.median()) if len(pos) else 0.0
seg = np.where(gm <= 0, "none", np.where(gm <= thr, "low", "high"))
delta = pd.Series([H23[s] for s in seg], index=gm.index, name="delta")

feats = artifact_features()["cold_lightgbm"]
train, val, test = load_scope("cold", feats)
tmap = pd.read_csv(REPO / "data/track6_split/track6_train.csv", low_memory=False, usecols=["artist_key", "artist_name_ko"]).drop_duplicates()
name2key = tmap.set_index("artist_name_ko")["artist_key"].to_dict()
delta_by_key = {name2key[n]: float(d) for n, d in delta.items() if n in name2key}
train = train.reset_index(drop=True)
masked = train["artist_key"].isin(set(delta_by_key))
tr_m, pseudo = train[~masked].reset_index(drop=True), train[masked].reset_index(drop=True)
ym = tr_m["ln_price_krw"].to_numpy(dtype=float)
P = {q: np.asarray(cb1.lgb_pipe(feats, a, 20260610).fit(tr_m[feats], ym).predict(pseudo[feats]), dtype=float) for q, a in cb1.QUANTILES.items()}
Pv = {q: np.asarray(cb1.lgb_pipe(feats, a, 20260610).fit(tr_m[feats], ym).predict(val[feats]), dtype=float) for q, a in cb1.QUANTILES.items()}
guard = cb1.defense(Pv["q50"], Pv["q40"], Pv["q90"] - Pv["q10"])[1]
g, _ = cb1.defense(P["q50"], P["q40"], P["q90"] - P["q10"], guard)
price = pseudo["price_krw"].to_numpy(dtype=float)
d_real = pseudo["artist_key"].map(delta_by_key).to_numpy(dtype=float)
res = {
    "guard_only": cb1.mt(price, g),
    "guard_plus_const(-0.0313)": cb1.mt(price, g - 0.031295),
    "guard_plus_real_delta": cb1.mt(price, g + d_real),
}
out = {"n_collected": int(len(gm)), "n_matched_train_artists": len(delta_by_key),
       "pseudo_rows": int(len(pseudo)), "gm_ratio_threshold_batch_median(approx)": thr,
       "segment_share": pd.Series(seg).value_counts(normalize=True).round(3).to_dict(),
       "three_way": {k: {m: round(v, 4) for m, v in r.items()} for k, r in res.items()}}
(EXP / "outputs").mkdir(parents=True, exist_ok=True)
pd.DataFrame({"artist_key": list(delta_by_key), "delta": list(delta_by_key.values())}).to_csv(EXP / "outputs" / "expanded_delta_lookup_pilot.csv", index=False)
(EXP / "outputs" / "stage3_three_way.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
