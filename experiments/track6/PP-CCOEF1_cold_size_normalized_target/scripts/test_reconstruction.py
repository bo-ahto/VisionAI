import numpy as np
import pandas as pd
from common_cold import load_splits, prep
from run_ccoef1_fixed_test import train_coef_models, predict_price_log


def test_reconstruction_is_coef_plus_logarea():
    train, test = load_splits()
    models = train_coef_models(train.head(2000))
    out = predict_price_log(models, test.head(50))
    raw_coef = np.asarray(models["q50"].predict(prep(test.head(50))), dtype=float)
    expected = raw_coef + np.log(test.head(50)["area_cm2"].to_numpy(float))
    assert np.allclose(out["q50"], expected)
