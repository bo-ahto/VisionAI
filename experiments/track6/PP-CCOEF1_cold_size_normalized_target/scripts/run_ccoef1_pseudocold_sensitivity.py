from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from common_cold import load_splits, metrics
from run_ccoef1_fixed_test import train_coef_models, predict_price_log

ART = Path(__file__).resolve().parents[1] / "artifacts"

def main():
    train, test = load_splits()
    models = train_coef_models(train)
    pred = predict_price_log(models, test)["q50"]
    actual = test["ln_price"].to_numpy(float)
    area = test["area_cm2"].to_numpy(float)
    lo, hi = np.quantile(area, 0.01), np.quantile(area, 0.99)
    slices = {
        "overall": np.ones(len(test), bool),
        "area_bottom_1pct": area <= lo,
        "area_top_1pct": area >= hi,
        "area_mid": (area > lo) & (area < hi),
    }
    out = {name: {**metrics(actual[m], pred[m]), "n": int(m.sum())}
           for name, m in slices.items()}
    ART.mkdir(exist_ok=True)
    (ART / "sensitivity.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
