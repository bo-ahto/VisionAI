from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "PP-CCOEF1_cold_size_normalized_target" / "scripts"))
import numpy as np
import pandas as pd
from common_cold import load_splits

ART = Path(__file__).resolve().parents[1] / "artifacts"


def build_coef_table(train: pd.DataFrame, k: float = 5.0) -> pd.DataFrame:
    g = float(train["ln_coef"].median())
    agg = (train.groupby("artist_key")["ln_coef"]
           .agg(n_works="count", raw_coef="median").reset_index())
    agg["shrunk_coef"] = (agg["n_works"] * agg["raw_coef"] + k * g) / (agg["n_works"] + k)
    return agg


def main():
    train, _ = load_splits()
    tbl = build_coef_table(train, k=5.0)
    ART.mkdir(exist_ok=True)
    tbl.to_csv(ART / "warm_coef_table.csv", index=False)
    print(f"warm artists: {len(tbl)}, global_ln_coef median used as prior")


if __name__ == "__main__":
    main()
