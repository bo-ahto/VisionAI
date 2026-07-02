import numpy as np
from common_cold import load_splits
from run_ccoef2_stage1_coef_table import build_coef_table


def test_shrinkage_pulls_small_artists_toward_global():
    train, _ = load_splits()
    tbl = build_coef_table(train, k=5.0)
    g = train["ln_coef"].median()
    small = tbl[tbl["n_works"] == 1]
    # 1-work artists are pulled at least halfway to global vs their raw coef
    assert (np.abs(small["shrunk_coef"] - g) <= np.abs(small["raw_coef"] - g) + 1e-9).all()
    assert tbl["artist_key"].is_unique
