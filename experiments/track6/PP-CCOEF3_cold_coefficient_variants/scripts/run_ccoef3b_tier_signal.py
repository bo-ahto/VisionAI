"""PP-CCOEF3B — C2 discrete-tier as a RANGE / INSPECTION auxiliary signal (not a
point-prediction replacement).

Two questions (the all-metric gate is the wrong lens for an auxiliary signal):
 1. Tier-count sweep: does raising K (5..30) recover the median (MdAPE) that the
    coarse 5-tier lost, and how does the tail (p95) move?
 2. Inspection value: does the DISAGREEMENT between the operational point model
    (direct ln_price q50) and the C2 tier anchor flag the rows where the point
    model is actually wrong (high APE)? If high-disagreement rows carry
    disproportionate error, the tier is a useful review/uncertainty flag even
    though it does not beat the point prediction.

Record-level (fixed test). Labels used only to MEASURE error, never to select.
0604 not used.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "PP-CCOEF1_cold_size_normalized_target" / "scripts"))
import numpy as np, pandas as pd
from lightgbm import LGBMRegressor
from common_cold import load_splits, prep, metrics, lgb_params
from run_ccoef3 import _score_stats, _artist_score  # composite metadata score

ART = Path(__file__).resolve().parents[1] / "artifacts"
KS = [5, 10, 15, 20, 30]
ANCHOR_K = 15  # mid sweet spot for the inspection-signal section


def c2_fit_k(train, k):
    stats = _score_stats(train)
    art = train.drop_duplicates("artist_key").set_index("artist_key")
    score = _artist_score(art, stats)
    coef = train.groupby("artist_key")["ln_coef"].median().reindex(score.index)
    cuts = np.quantile(score.to_numpy(), np.linspace(0, 1, k + 1)[1:-1])
    tier = np.digitize(score.to_numpy(), cuts)
    tmed = pd.Series(coef.to_numpy(), index=tier).groupby(level=0).median()
    return {"stats": stats, "cuts": cuts, "tmed": tmed, "gmed": float(coef.median())}


def c2_anchor_log(model, frame):
    """Tier-anchor price-log = tier_median_coef + log(area)."""
    art = frame.drop_duplicates("artist_key").set_index("artist_key")
    score = _artist_score(art, model["stats"])
    tier = pd.Series(np.digitize(score.to_numpy(), model["cuts"]), index=score.index)
    coef_by_artist = tier.map(lambda t: model["tmed"].get(t, model["gmed"]))
    coef = frame["artist_key"].map(coef_by_artist).to_numpy(float)
    return coef + np.log(pd.to_numeric(frame["area_cm2"], errors="coerce").to_numpy(float))


def main():
    train, test = load_splits()
    actual = test["ln_price"].to_numpy(float)
    actual_price = np.exp(actual)

    # (1) tier-count sweep, fixed-test record
    sweep = {}
    for k in KS:
        pred = c2_anchor_log(c2_fit_k(train, k), test)
        sweep[str(k)] = metrics(actual, pred)

    # (2) inspection signal: point model = direct ln_price q50
    point = np.asarray(LGBMRegressor(**lgb_params(0.50))
                       .fit(prep(train), train["ln_price"].to_numpy(float))
                       .predict(prep(test)), dtype=float)
    point_price = np.clip(np.exp(point), 1000.0, None)
    point_ape = np.abs(point_price - actual_price) / np.clip(actual_price, 1.0, None)

    anchor = c2_anchor_log(c2_fit_k(train, ANCHOR_K), test)
    disagree = np.abs(point - anchor)  # log-space gap between point and tier anchor

    order = np.argsort(disagree)
    deciles = np.array_split(order, 10)  # ascending disagreement
    ape_by_decile = [float(np.median(point_ape[idx])) for idx in deciles]

    # capture: of the worst 20% rows by actual APE, what share is in the top 20%
    # by disagreement? (0.20 = random baseline)
    n = len(test)
    worst20 = set(np.argsort(point_ape)[-(n // 5):])
    flagged20 = set(np.argsort(disagree)[-(n // 5):])
    capture = len(worst20 & flagged20) / len(worst20)

    # Spearman corr(disagreement, ape) via rank correlation
    rd = pd.Series(disagree).rank().to_numpy()
    ra = pd.Series(point_ape).rank().to_numpy()
    spearman = float(np.corrcoef(rd, ra)[0, 1])

    out = {
        "tier_sweep_fixed_test": sweep,
        "v0_2_base": {"MdAPE": 0.4823, "MAPE": 1.242, "p95_APE": 4.380},
        "inspection_signal": {
            "anchor_K": ANCHOR_K,
            "point_model": "direct ln_price q50 (operational-equivalent)",
            "spearman_disagreement_vs_ape": spearman,
            "median_ape_by_disagreement_decile_asc": ape_by_decile,
            "worst20pct_capture_by_top20pct_disagreement": capture,
            "random_baseline_capture": 0.20,
        },
    }
    ART.mkdir(exist_ok=True)
    (ART / "ccoef3b_tier_signal.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
