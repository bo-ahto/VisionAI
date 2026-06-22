import numpy as np
from common_cold import load_splits, prep
from run_ccoef3 import (c1_train, c1_predict_pricelog, perim,
                        c2_fit, c2_predict_pricelog)


def test_c1_reconstruction_is_coef_plus_log_perimeter():
    train, test = load_splits()
    m = c1_train(train.head(3000))
    out = c1_predict_pricelog(m, test.head(50))
    expected = np.asarray(m.predict(prep(test.head(50))), dtype=float) + np.log(perim(test.head(50)))
    assert np.allclose(out, expected)


def test_c2_assigns_only_held_in_tier_medians():
    # tier-median coefficients must come from the FIT set only, and the assigned
    # coefficient must lie within the fit set's tier-median range (bounded — the
    # whole point vs B's unbounded continuous regression).
    train, test = load_splits()
    model = c2_fit(train)
    pred = c2_predict_pricelog(model, test)
    log_area = np.log(test["area_cm2"].to_numpy(float))
    coef = pred - log_area  # recover assigned coefficient
    lo, hi = model["tmed"].min(), model["tmed"].max()
    assert np.isfinite(pred).all()
    assert (coef >= lo - 1e-9).all() and (coef <= hi + 1e-9).all()
