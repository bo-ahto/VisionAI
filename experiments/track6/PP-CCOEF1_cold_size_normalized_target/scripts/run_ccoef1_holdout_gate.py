from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from lightgbm import LGBMRegressor
from common_cold import load_splits, prep, metrics, lgb_params

ART = Path(__file__).resolve().parents[1] / "artifacts"
RUNS, FRACS, SEED0 = 200, [0.80, 0.70], 20260622


def fit_q50(frame, target_col):
    return LGBMRegressor(**lgb_params(0.50)).fit(prep(frame), frame[target_col].to_numpy(float))


def main():
    train, _ = load_splits()
    artists = np.array(sorted(train["artist_key"].dropna().unique()))
    rng = np.random.default_rng(SEED0)
    wins = {k: [] for k in ["MdAPE", "MAPE", "p95_APE"]}
    for r in range(RUNS):
        frac = FRACS[r % len(FRACS)]
        pick = rng.choice(artists, size=int(len(artists) * frac), replace=False)
        tr = train[train["artist_key"].isin(pick)]
        ev = train[~train["artist_key"].isin(pick)]
        if ev.empty or tr.empty:
            continue
        # candidate A (coef target) vs base (direct ln_price), same features/params
        a_model = fit_q50(tr, "ln_coef")
        a_pred = np.asarray(a_model.predict(prep(ev)), dtype=float) + np.log(ev["area_cm2"].to_numpy(float))
        b_model = fit_q50(tr, "ln_price")
        b_pred = np.asarray(b_model.predict(prep(ev)), dtype=float)
        ay, by = metrics(ev["ln_price"], a_pred), metrics(ev["ln_price"], b_pred)
        for k in wins:
            wins[k].append(1.0 if ay[k] < by[k] else 0.0)
    probs = {f"improve_prob_{k}": float(np.mean(v)) for k, v in wins.items()}
    passed = probs["improve_prob_MAPE"] >= 0.90 and probs["improve_prob_p95_APE"] >= 0.90
    out = {"runs": RUNS, **probs, "pass": passed}
    ART.mkdir(exist_ok=True)
    (ART / "holdout_gate.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
