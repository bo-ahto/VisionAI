from __future__ import annotations
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "PP-CCOEF1_cold_size_normalized_target" / "scripts"))
import numpy as np, pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import KFold
from common_cold import load_splits, prep, metrics, lgb_params
from run_ccoef2_stage1_coef_table import build_coef_table
from run_ccoef1_fixed_test import train_coef_models, predict_price_log

ART = Path(__file__).resolve().parents[1] / "artifacts"
META = ["artist_meta_birth_year", "artist_meta_total_works_log", "artist_meta_followers_log",
        "artist_meta_career_stage", "artist_exhibition_total_count_log",
        "gallery_tier_validated_score"]
CAT_META = ["artist_meta_career_stage"]


def _meta_frame(df, keys):
    # one row per artist: first non-null meta per artist_key
    cols = ["artist_key"] + META
    m = df[cols].drop_duplicates("artist_key").set_index("artist_key")
    return m.reindex(keys)


def _prep_meta(m):
    x = m.copy()
    for c in CAT_META:
        x[c] = x[c].astype("category")
    for c in [f for f in META if f not in CAT_META]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x


def oof_artist_coef_regression(coef_table, n_splits=5, seed=20260622):
    train, _ = load_splits()
    keys = coef_table["artist_key"].to_numpy()
    m = _prep_meta(_meta_frame(train, keys))
    y = coef_table.set_index("artist_key").loc[keys, "shrunk_coef"].to_numpy(float)
    oof = np.full(len(keys), np.nan)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr_idx, va_idx in kf.split(keys):
        reg = LGBMRegressor(**{**lgb_params(0.50), "objective": "regression"})
        reg.fit(m.iloc[tr_idx], y[tr_idx])
        oof[va_idx] = reg.predict(m.iloc[va_idx])
    return pd.DataFrame({"artist_key": keys, "oof_pred_coef": oof})


def coverage_mask(test):
    present = np.zeros(len(test), bool)
    for c in META:
        present |= pd.to_numeric(test[c], errors="coerce").notna().to_numpy() if c not in CAT_META \
                   else test[c].notna().to_numpy()
    return present


def main():
    train, test = load_splits()
    tbl = build_coef_table(train)
    # fit final stage-2 on all warm artists (OOF only used for honesty checks)
    keys = tbl["artist_key"].to_numpy()
    m_tr = _prep_meta(_meta_frame(train, keys))
    y_tr = tbl.set_index("artist_key").loc[keys, "shrunk_coef"].to_numpy(float)
    reg = LGBMRegressor(**{**lgb_params(0.50), "objective": "regression"})
    reg.fit(m_tr, y_tr)
    # cold inference: coef_hat from metadata, price = exp(coef_hat) * area
    m_te = _prep_meta(_meta_frame(test, test["artist_key"].to_numpy()))
    coef_hat = reg.predict(m_te)
    log_area = np.log(test["area_cm2"].to_numpy(float))
    b_pred = coef_hat + log_area
    # A fallback for uncovered artists
    a_models = train_coef_models(train)
    a_pred = predict_price_log(a_models, test)["q50"]
    cov = coverage_mask(test)
    blended = np.where(cov, b_pred, a_pred)
    actual = test["ln_price"].to_numpy(float)
    base = {"MdAPE": 0.4823, "MAPE": 1.242, "p95_APE": 4.380}
    out = {
        "coverage_rate": float(cov.mean()),
        "covered_subset": {"B": metrics(actual[cov], b_pred[cov]),
                            "A": metrics(actual[cov], a_pred[cov]), "n": int(cov.sum())},
        "overall_with_fallback": {"B_blend": metrics(actual, blended),
                                  "A_only": metrics(actual, a_pred)},
        "v0_2_base": base,
    }
    ART.mkdir(exist_ok=True)
    (ART / "stage2_eval.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
