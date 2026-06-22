from common_cold import load_splits, assert_disjoint, metrics, FEATURES
import numpy as np

def test_splits_disjoint_and_area_positive():
    train, test = load_splits()
    assert (train["area_cm2"] > 0).all() and (test["area_cm2"] > 0).all()
    assert_disjoint(train, test)  # raises if any shared artist_key
    # ln_coef identity: ln_price - ln(area) == ln_coef
    assert np.allclose(train["ln_coef"], train["ln_price"] - np.log(train["area_cm2"]))

def test_metrics_perfect_is_zero():
    m = metrics([0.0, 1.0], [0.0, 1.0])
    assert m["MdAPE"] == 0.0
