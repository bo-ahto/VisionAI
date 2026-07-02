from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from lightgbm import LGBMRegressor
from common_cold import load_splits, prep, metrics, lgb_params, assert_disjoint

ART = Path(__file__).resolve().parents[1] / "artifacts"
QUANTILES = {"q10": 0.10, "q40": 0.40, "q50": 0.50, "q90": 0.90}


def train_coef_models(train):
    x = prep(train)
    y = train["ln_coef"].to_numpy(float)  # size-normalized target
    return {q: LGBMRegressor(**lgb_params(a)).fit(x, y) for q, a in QUANTILES.items()}


def predict_price_log(models, frame):
    x = prep(frame)
    log_area = np.log(frame["area_cm2"].to_numpy(float))
    return {q: np.asarray(models[q].predict(x), dtype=float) + log_area for q in models}


def main():
    train, test = load_splits()
    assert_disjoint(train, test)
    models = train_coef_models(train)
    pred = predict_price_log(models, test)
    actual_log = test["ln_price"].to_numpy(float)
    m = metrics(actual_log, pred["q50"])
    base = {"MdAPE": 0.4823, "MAPE": 1.242, "p95_APE": 4.380}
    out = {"n_test": int(len(test)), "ccoef1_q50": m, "v0_2_base": base,
           "delta": {k: m[k] - base[k] for k in m}}
    ART.mkdir(exist_ok=True)
    (ART / "fixed_test_metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
