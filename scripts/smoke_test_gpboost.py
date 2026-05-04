"""GPBoost smoke test (V5 cycle Track D).

목적: GPBoost Python interface 안정성 검증.
- 설치 OK?
- toy example random intercept 모델 동작?
- prediction (seen/unseen group) 동작?
- runtime baseline 측정 (CatBoost 대비)

코덱스 권고: native API > scikit wrapper.

Usage: python3 scripts/smoke_test_gpboost.py
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd


def main() -> None:
    print("=" * 60)
    print("GPBoost Smoke Test (V5 Track D)")
    print("=" * 60)

    # 1. Import 확인
    try:
        import gpboost as gpb
        print(f"✓ gpboost {gpb.__version__} import OK")
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return

    # 2. Toy data 생성 (artist random intercept)
    rng = np.random.default_rng(42)
    n_artists = 100
    n_per_artist = 30
    n = n_artists * n_per_artist

    artist_ids = np.repeat(np.arange(n_artists), n_per_artist)
    # Random intercept per artist: ln_price ~ Normal(0, 0.5)
    artist_effect = rng.normal(0, 0.5, size=n_artists)
    # Features
    X = rng.standard_normal(size=(n, 5))
    beta = np.array([0.3, -0.2, 0.5, 0.0, 0.1])
    # ln_price = X @ beta + artist_effect[artist_ids] + noise
    y = X @ beta + artist_effect[artist_ids] + rng.normal(0, 0.3, size=n)

    print(f"\n[Data] {n} samples, {n_artists} artists, 5 features")
    print(f"  True artist effect std: {np.std(artist_effect):.3f}")

    # 3. Train/test split (artist-level, leave-artist-out)
    test_artists = rng.choice(n_artists, size=20, replace=False)
    test_mask = np.isin(artist_ids, test_artists)
    X_tr, X_te = X[~test_mask], X[test_mask]
    y_tr, y_te = y[~test_mask], y[test_mask]
    art_tr, art_te = artist_ids[~test_mask], artist_ids[test_mask]
    print(f"  Train: {len(y_tr)} ({pd.Series(art_tr).nunique()} artists)")
    print(f"  Test: {len(y_te)} ({pd.Series(art_te).nunique()} artists, all unseen)")

    # 4. GPModel (random intercept) + Boosting
    print("\n[Train] GPBoost with grouped random intercept")
    gp_model = gpb.GPModel(group_data=art_tr, likelihood="gaussian")

    t0 = time.time()
    data_train = gpb.Dataset(X_tr, label=y_tr)
    bst = gpb.train(
        params={
            "objective": "regression_l2",
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_data_in_leaf": 20,
            "verbose": -1,
        },
        train_set=data_train,
        gp_model=gp_model,
        num_boost_round=200,
    )
    train_time = time.time() - t0
    print(f"  ✓ Train OK ({train_time:.1f}s, 200 rounds)")

    # 5. Prediction (unseen artists)
    t0 = time.time()
    pred = bst.predict(data=X_te, group_data_pred=art_te)
    pred_time = time.time() - t0

    # GPBoost returns dict with 'response_mean' etc.
    if isinstance(pred, dict):
        keys = list(pred.keys())
        print(f"  Prediction returns dict with keys: {keys}")
        y_pred = pred.get("response_mean")
        if y_pred is None:
            # Try alternative keys
            y_pred = pred.get("fixed_effect", np.zeros(len(y_te)))
            re = pred.get("random_effect_mean", np.zeros(len(y_te)))
            y_pred = y_pred + re
    else:
        y_pred = pred

    rmse = float(np.sqrt(np.mean((y_te - y_pred) ** 2)))
    print(f"  ✓ Predict OK ({pred_time:.2f}s, unseen artists)")
    print(f"  Test RMSE: {rmse:.3f} (lower=better)")

    # 6. Variance components 확인 (random effect 추정 OK?)
    cov_pars = gp_model.get_cov_pars()
    print(f"\n[Variance components]")
    if hasattr(cov_pars, 'iloc'):
        # DataFrame
        print(cov_pars.to_string())
    else:
        print(cov_pars)

    # 7. Predict on training set (seen artists, BLUP 적용)
    pred_train = bst.predict(data=X_tr[:100], group_data_pred=art_tr[:100])
    if isinstance(pred_train, dict):
        y_pred_tr = pred_train.get("response_mean", pred_train.get("fixed_effect", np.zeros(100)))
    else:
        y_pred_tr = pred_train
    rmse_train = float(np.sqrt(np.mean((y_tr[:100] - y_pred_tr) ** 2)))
    print(f"\n[Train (seen) prediction RMSE]: {rmse_train:.3f}")
    print(f"[Test (unseen) prediction RMSE]: {rmse:.3f}")
    print(f"  Gap (unseen - seen): {rmse - rmse_train:+.3f}")
    print(f"  ※ 정상: unseen RMSE > seen (artist random effect 학습됨)")

    print("\n" + "=" * 60)
    print("✓ GPBoost smoke test PASSED")
    print("=" * 60)
    print(f"Runtime ({n} samples, 200 rounds): train={train_time:.1f}s, pred={pred_time:.2f}s")


if __name__ == "__main__":
    main()
