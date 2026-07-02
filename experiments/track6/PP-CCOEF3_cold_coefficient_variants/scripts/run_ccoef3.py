"""PP-CCOEF3 — country-convention coefficient variants for cold prediction.

Two variants beyond PP-CCOEF1/2 (which used the US/KR area-based continuous form):
- C1 (German perimeter basis): target = log(price / (width+height)), reconstruct
  price = exp(pred) * (width+height). Linear size term — less tail amplification
  than area (which grows quadratically) — the documented A failure mode.
- C2 (German/Italian discrete tier band): build an ordinal artist tier from a
  composite metadata score (exhibition, followers, total_works, gallery_tier,
  career_stage), assign the tier's MEDIAN coefficient (ln(price/area)) rather than
  a continuous regression. Discreteness bounds the coefficient, directly testing
  whether it avoids B's +43% MAPE blowup from extreme regressed coefficients.

Same gate as PP-CCOEF1 (Task 3): paired artist 80/70% holdout, 200 runs, candidate
vs direct ln_price target, pass iff MAPE and p95 improvement prob >= 0.90.
Fixed test is RECORD ONLY (never selection). 0604 not used.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "PP-CCOEF1_cold_size_normalized_target" / "scripts"))
import numpy as np, pandas as pd
from lightgbm import LGBMRegressor
from common_cold import load_splits, prep, metrics, lgb_params

ART = Path(__file__).resolve().parents[1] / "artifacts"
BASE = {"MdAPE": 0.4823, "MAPE": 1.242, "p95_APE": 4.380}
SCORE_FEATS = ["artist_exhibition_total_count_log", "artist_meta_followers_log",
               "artist_meta_total_works_log", "gallery_tier_validated_score",
               "artist_meta_career_stage"]
K_TIERS = 5
RUNS, FRACS, SEED0 = 200, [0.80, 0.70], 20260622


# ---------- C1: perimeter basis ----------
def perim(df):
    return pd.to_numeric(df["width_cm"], errors="coerce").to_numpy(float) + \
           pd.to_numeric(df["height_cm"], errors="coerce").to_numpy(float)

def c1_train(train):
    x = prep(train)
    y = train["ln_price"].to_numpy(float) - np.log(perim(train))  # log(price/(w+h))
    return LGBMRegressor(**lgb_params(0.50)).fit(x, y)

def c1_predict_pricelog(model, frame):
    return np.asarray(model.predict(prep(frame)), dtype=float) + np.log(perim(frame))


# ---------- C2: discrete tier band ----------
def _score_stats(train_df):
    """Standardization stats (median/mean/std per feat) fit on the given artists."""
    art = train_df.drop_duplicates("artist_key").set_index("artist_key")
    stats = {}
    for c in SCORE_FEATS:
        v = pd.to_numeric(art[c], errors="coerce")
        med = float(v.median())
        s = v.fillna(med)
        stats[c] = (med, float(s.mean()), float(s.std() or 1.0))
    return stats

def _artist_score(df_unique_index, stats):
    """Composite z-score per artist (index = artist_key)."""
    z = pd.DataFrame(index=df_unique_index.index)
    for c in SCORE_FEATS:
        med, mu, sd = stats[c]
        v = pd.to_numeric(df_unique_index[c], errors="coerce").fillna(med)
        z[c] = (v - mu) / sd
    return z.mean(axis=1)

def c2_fit(train):
    """Fit on warm artists: standardization, quantile tier cuts, tier-median ln_coef."""
    stats = _score_stats(train)
    art = train.drop_duplicates("artist_key").set_index("artist_key")
    score = _artist_score(art, stats)
    coef = train.groupby("artist_key")["ln_coef"].median().reindex(score.index)
    cuts = np.quantile(score.to_numpy(), np.linspace(0, 1, K_TIERS + 1)[1:-1])
    tier = np.digitize(score.to_numpy(), cuts)
    tmed = pd.Series(coef.to_numpy(), index=tier).groupby(level=0).median()
    gmed = float(coef.median())
    return {"stats": stats, "cuts": cuts, "tmed": tmed, "gmed": gmed}

def c2_predict_pricelog(model, frame):
    art = frame.drop_duplicates("artist_key").set_index("artist_key")
    score = _artist_score(art, model["stats"])
    tier = pd.Series(np.digitize(score.to_numpy(), model["cuts"]), index=score.index)
    coef_by_artist = tier.map(lambda t: model["tmed"].get(t, model["gmed"]))
    coef = frame["artist_key"].map(coef_by_artist).to_numpy(float)
    return coef + np.log(pd.to_numeric(frame["area_cm2"], errors="coerce").to_numpy(float))


# ---------- fixed test (record only) ----------
def run_fixed_test():
    train, test = load_splits()
    actual = test["ln_price"].to_numpy(float)
    c1 = metrics(actual, c1_predict_pricelog(c1_train(train), test))
    c2 = metrics(actual, c2_predict_pricelog(c2_fit(train), test))
    out = {"n_test": int(len(test)), "C1_perimeter": c1, "C2_tier": c2, "v0_2_base": BASE,
           "delta_C1": {k: c1[k] - BASE[k] for k in c1},
           "delta_C2": {k: c2[k] - BASE[k] for k in c2}}
    ART.mkdir(exist_ok=True)
    (ART / "ccoef3_fixed_test.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


# ---------- paired holdout gate ----------
def run_gate():
    train, _ = load_splits()
    artists = np.array(sorted(train["artist_key"].dropna().unique()))
    rng = np.random.default_rng(SEED0)
    wins = {v: {k: [] for k in ["MdAPE", "MAPE", "p95_APE"]} for v in ["C1", "C2"]}
    for r in range(RUNS):
        frac = FRACS[r % len(FRACS)]
        pick = rng.choice(artists, size=int(len(artists) * frac), replace=False)
        tr = train[train["artist_key"].isin(pick)]
        ev = train[~train["artist_key"].isin(pick)]
        if ev.empty or tr.empty:
            continue
        ev_actual = ev["ln_price"].to_numpy(float)
        # shared baseline: direct ln_price q50
        b_model = LGBMRegressor(**lgb_params(0.50)).fit(prep(tr), tr["ln_price"].to_numpy(float))
        by = metrics(ev_actual, np.asarray(b_model.predict(prep(ev)), dtype=float))
        # C1 candidate
        c1y = metrics(ev_actual, c1_predict_pricelog(c1_train(tr), ev))
        # C2 candidate (lookup, fit on held-in only)
        c2y = metrics(ev_actual, c2_predict_pricelog(c2_fit(tr), ev))
        for k in ["MdAPE", "MAPE", "p95_APE"]:
            wins["C1"][k].append(1.0 if c1y[k] < by[k] else 0.0)
            wins["C2"][k].append(1.0 if c2y[k] < by[k] else 0.0)
    out = {"runs": RUNS}
    for v in ["C1", "C2"]:
        probs = {f"improve_prob_{k}": float(np.mean(wins[v][k])) for k in wins[v]}
        out[v] = {**probs,
                  "pass": probs["improve_prob_MAPE"] >= 0.90 and probs["improve_prob_p95_APE"] >= 0.90}
    ART.mkdir(exist_ok=True)
    (ART / "ccoef3_gate.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "gate":
        run_gate()
    else:
        run_fixed_test()
