"""트랙 2 Cold Validation Cycle 1 — Stage 1 실험 실행.

Pre-registered analysis plan: docs/track2_cold_validation_cycle1_prereg_20260508.md
Baseline 모델: F4 + log_area spline + Huber regression (Stage 3 운영 채택 spec)

Primary 1 (B): Stage 4 모집단 (8,495 / 807) Random LAO 80/20 → cold MdAPE
Primary 2 (D): Time-split (train year_made ≤ 2023 / test ≥ 2024) → cold MdAPE
Hard gates: low-price (P25 이하) + cold sub-bin (train_count 0/1-4/5-9)
Bootstrap: artist-cluster, n_boot=2000, percentile CI, seed=42
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import GroupShuffleSplit

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
RESULTS_DIR = Path(__file__).parent / "results"

# Pre-registered constants
TEST_SIZE = 0.20
N_BOOT = 2000
SEED = 42
HUBER_EPS = 1.35
HUBER_ALPHA = 0.0001
COLD_TRAIN_COUNT_THRESHOLD = 10  # < 10 = cold
TIME_SPLIT_YEAR = 2023  # train ≤ 2023 / test ≥ 2024

# Pre-registered thresholds
PRIMARY_THRESHOLD_PCT = 26.07  # baseline 24.07 + 2.0 tolerance
LOW_PRICE_HARM_THRESHOLD = 28.07
COLD_SUB_BIN_HARM_THRESHOLD = 28.07
TIME_DEGRADATION_THRESHOLD = 3.0


def restricted_cubic_spline(x: np.ndarray, knots: np.ndarray) -> np.ndarray:
    last_k, pre_last_k = knots[-1], knots[-2]
    denom = (last_k - knots[0]) ** 2
    out = []
    for i in range(len(knots) - 2):
        ti = knots[i]
        cube = lambda u: np.maximum(u, 0) ** 3
        spline = (
            cube(x - ti)
            - cube(x - pre_last_k) * (last_k - ti) / (last_k - pre_last_k)
            + cube(x - last_k) * (pre_last_k - ti) / (last_k - pre_last_k)
        )
        out.append(spline / denom)
    return np.column_stack(out)


def build_features(df: pd.DataFrame, train_knot_log_area: np.ndarray | None = None) -> tuple[pd.DataFrame, np.ndarray]:
    """Build F4 + spline features. Train-only knot fit (leakage prevention).

    Returns: (X DataFrame, knot percentile values)
    """
    df = df.copy()
    if train_knot_log_area is None:
        knots = np.percentile(df["log_area"].values, [10, 50, 90])
    else:
        knots = np.percentile(train_knot_log_area, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    X = pd.DataFrame({
        "log_area": df["log_area"].values,
        "birth_year_centered": df["birth_year_centered"].values,
        "log_artist_total_works": df["log_artist_total_works"].values,
        "log_area_spline": sp[:, 0],
    })
    return X, knots


def fit_huber(Xtr: np.ndarray, ytr: np.ndarray, Xte: np.ndarray) -> np.ndarray:
    m = HuberRegressor(epsilon=HUBER_EPS, max_iter=500, alpha=HUBER_ALPHA)
    m.fit(Xtr, ytr)
    return Xte @ m.coef_ + m.intercept_


def mdape_pct(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> float:
    actual = np.exp(y_true_log)
    pred = np.exp(y_pred_log)
    ape = np.abs(pred - actual) / actual
    return float(np.median(ape) * 100)


def cluster_bootstrap_ci(test_df: pd.DataFrame, y_pred_log: np.ndarray, n_boot: int = N_BOOT) -> tuple[float, float]:
    """Artist-cluster bootstrap percentile CI for cold MdAPE.

    Prereg §1.5 bootstrap hygiene: internal seed = range(n_boot) (b 별 결정론).
    """
    test_df = test_df.copy()
    test_df["__y_pred_log"] = y_pred_log
    artists = test_df["artist_slug"].unique()
    boot_mdapes = []
    for b in range(n_boot):
        rng = np.random.default_rng(b)  # prereg-faithful: internal seed = b
        sampled = rng.choice(artists, size=len(artists), replace=True)
        boot_df = pd.concat(
            [test_df[test_df["artist_slug"] == a] for a in sampled],
            ignore_index=True,
        )
        boot_mdape = mdape_pct(boot_df["log_price"].values, boot_df["__y_pred_log"].values)
        boot_mdapes.append(boot_mdape)
    arr = np.array(boot_mdapes)
    return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


def evaluate_random_lao(df: pd.DataFrame) -> dict:
    """Primary 1: Random LAO 80/20 (artist-level GroupShuffleSplit).

    Test fold = 정의상 모두 cold (artist 가 train 에 없음).
    """
    logger.info("=== Primary 1: Random LAO 80/20 ===")
    groups = df["artist_slug"].values
    gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
    train_idx, test_idx = next(gss.split(df, df["log_price"], groups))
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()

    Xtr, _ = build_features(train_df)
    Xte, _ = build_features(test_df, train_knot_log_area=train_df["log_area"].values)
    ytr = train_df["log_price"].values

    pred = fit_huber(Xtr.values, ytr, Xte.values)

    mdape = mdape_pct(test_df["log_price"].values, pred)
    ci_low, ci_up = cluster_bootstrap_ci(test_df, pred)

    # Hard gates: low-price (P25 이하 segment) + cold sub-bin
    p25 = train_df["price_krw"].quantile(0.25)
    test_df["__pred"] = pred
    low_mask = test_df["price_krw"] <= p25
    low_mdape = mdape_pct(test_df.loc[low_mask, "log_price"].values, pred[low_mask.values]) if low_mask.sum() > 0 else None

    train_cnt = train_df.groupby("artist_slug").size()
    test_df["__train_count"] = test_df["artist_slug"].map(train_cnt).fillna(0).astype(int)
    sub_bins = {"0": (0, 0), "1-4": (1, 4), "5-9": (5, 9)}
    sub_bin_mdapes = {}
    for label, (lo, hi) in sub_bins.items():
        mask = (test_df["__train_count"] >= lo) & (test_df["__train_count"] <= hi)
        n = int(mask.sum())
        sub_bin_mdapes[label] = {
            "n": n,
            "mdape": mdape_pct(test_df.loc[mask, "log_price"].values, pred[mask.values]) if n > 0 else None,
        }

    return {
        "n_train": len(train_df), "n_test": len(test_df),
        "n_train_artists": train_df["artist_slug"].nunique(),
        "n_test_artists": test_df["artist_slug"].nunique(),
        "cold_mdape": mdape,
        "ci_95": [ci_low, ci_up],
        "low_price_p25_threshold_krw": float(p25),
        "low_price_n": int(low_mask.sum()),
        "low_price_mdape": low_mdape,
        "cold_sub_bins": sub_bin_mdapes,
    }


def evaluate_time_split(df: pd.DataFrame) -> dict:
    """Primary 2: Time-split (train year_made ≤ 2023 / test ≥ 2024).

    Cold = test 작가 의 train 작품 < 10건.
    """
    logger.info("=== Primary 2: Time-split (train ≤ 2023 / test 2024+) ===")
    train_df = df[df["year_made"] <= TIME_SPLIT_YEAR].copy()
    test_df = df[df["year_made"] >= TIME_SPLIT_YEAR + 1].copy()

    Xtr, _ = build_features(train_df)
    Xte, _ = build_features(test_df, train_knot_log_area=train_df["log_area"].values)
    ytr = train_df["log_price"].values

    pred = fit_huber(Xtr.values, ytr, Xte.values)

    # Cold/warm split (test 작가 의 train 작품 count)
    train_cnt = train_df.groupby("artist_slug").size()
    test_df["__train_count"] = test_df["artist_slug"].map(train_cnt).fillna(0).astype(int)
    test_df["__pred"] = pred

    cold_mask = test_df["__train_count"] < COLD_TRAIN_COUNT_THRESHOLD
    warm_mask = ~cold_mask

    cold_mdape = mdape_pct(test_df.loc[cold_mask, "log_price"].values, pred[cold_mask.values]) if cold_mask.sum() > 0 else None
    warm_mdape = mdape_pct(test_df.loc[warm_mask, "log_price"].values, pred[warm_mask.values]) if warm_mask.sum() > 0 else None

    # Train cold MdAPE (degradation 계산용 — train 의 in-sample cold)
    train_cnt_train = train_df.groupby("artist_slug").size()
    train_df["__train_count"] = train_df["artist_slug"].map(train_cnt_train).fillna(0).astype(int)
    pred_tr = fit_huber(Xtr.values, ytr, Xtr.values)  # in-sample
    train_cold_mask = train_df["__train_count"] < COLD_TRAIN_COUNT_THRESHOLD
    train_cold_mdape = mdape_pct(train_df.loc[train_cold_mask, "log_price"].values, pred_tr[train_cold_mask.values]) if train_cold_mask.sum() > 0 else None

    # Bootstrap CI for cold
    if cold_mask.sum() > 0:
        cold_test_df = test_df[cold_mask].copy()
        cold_pred = pred[cold_mask.values]
        ci_low, ci_up = cluster_bootstrap_ci(cold_test_df, cold_pred)
    else:
        ci_low, ci_up = None, None

    # Cold sub-bins (Time-split base)
    sub_bins = {"0": (0, 0), "1-4": (1, 4), "5-9": (5, 9)}
    sub_bin_mdapes = {}
    for label, (lo, hi) in sub_bins.items():
        mask = (test_df["__train_count"] >= lo) & (test_df["__train_count"] <= hi)
        n = int(mask.sum())
        sub_bin_mdapes[label] = {
            "n": n,
            "mdape": mdape_pct(test_df.loc[mask, "log_price"].values, pred[mask.values]) if n > 0 else None,
        }

    # Low-price segment
    p25 = train_df["price_krw"].quantile(0.25)
    low_mask = (test_df["price_krw"] <= p25) & cold_mask  # cold 영역 내 저가
    low_mdape = mdape_pct(test_df.loc[low_mask, "log_price"].values, pred[low_mask.values]) if low_mask.sum() > 0 else None

    return {
        "n_train": len(train_df), "n_test": len(test_df),
        "n_train_artists": train_df["artist_slug"].nunique(),
        "n_test_artists": test_df["artist_slug"].nunique(),
        "n_test_cold": int(cold_mask.sum()), "n_test_warm": int(warm_mask.sum()),
        "n_test_cold_artists": test_df.loc[cold_mask, "artist_slug"].nunique(),
        "cold_mdape": cold_mdape,
        "warm_mdape": warm_mdape,
        "ci_95_cold": [ci_low, ci_up],
        "train_cold_mdape": train_cold_mdape,
        "time_degradation_pp": (cold_mdape - train_cold_mdape) if (cold_mdape is not None and train_cold_mdape is not None) else None,
        "low_price_p25_threshold_krw": float(p25),
        "low_price_cold_n": int(low_mask.sum()),
        "low_price_cold_mdape": low_mdape,
        "cold_sub_bins": sub_bin_mdapes,
    }


def judgment(p1: dict, p2: dict) -> dict:
    """Intersection-union confirmatory gate (prereg §1.7 logic).

    PASS: Primary 1 + Primary 2 모두 충족 + 모든 hard gate 충족
    FAIL: Primary 1 임계 미충족 OR hard gate ≥ 2건 violation
    BORDERLINE: Primary 1 충족 + (Primary 2 미충족 OR hard gate 1건 violation)
    """
    p1_point_pass = p1["cold_mdape"] <= PRIMARY_THRESHOLD_PCT
    p1_ci_pass = p1["ci_95"][1] <= PRIMARY_THRESHOLD_PCT
    p1_pass = p1_point_pass and p1_ci_pass

    p2_point_pass = p2["cold_mdape"] is not None and p2["cold_mdape"] <= PRIMARY_THRESHOLD_PCT
    p2_degrad_pass = p2["time_degradation_pp"] is not None and p2["time_degradation_pp"] <= TIME_DEGRADATION_THRESHOLD
    p2_pass = p2_point_pass and p2_degrad_pass

    # Hard gates (Time-split base)
    low_price_pass = p2["low_price_cold_mdape"] is None or p2["low_price_cold_mdape"] <= LOW_PRICE_HARM_THRESHOLD
    sub_bin_violations = [
        label for label, v in p2["cold_sub_bins"].items()
        if v["mdape"] is not None and v["mdape"] > COLD_SUB_BIN_HARM_THRESHOLD
    ]
    sub_bin_pass = len(sub_bin_violations) == 0
    hard_gate_violations = (0 if low_price_pass else 1) + len(sub_bin_violations)
    hard_gate_pass = hard_gate_violations == 0

    # Prereg §1.7 verdict logic
    if p1_pass and p2_pass and hard_gate_pass:
        verdict = "PASS"
    elif (not p1_pass) or hard_gate_violations >= 2:
        verdict = "FAIL"
    else:
        # Primary 1 충족 + (Primary 2 미충족 OR hard gate 1건)
        verdict = "BORDERLINE"

    return {
        "verdict": verdict,
        "primary_1_pass": p1_pass,
        "primary_1_point_pass": p1_point_pass,
        "primary_1_ci_pass": p1_ci_pass,
        "primary_2_pass": p2_pass,
        "primary_2_point_pass": p2_point_pass,
        "primary_2_degradation_pass": p2_degrad_pass,
        "hard_gate_pass": hard_gate_pass,
        "hard_gate_violations": hard_gate_violations,
        "low_price_pass": low_price_pass,
        "sub_bin_violations": sub_bin_violations,
    }


def main() -> None:
    logger.info("Loading dataset: %s", DATA)
    df = pd.read_parquet(DATA)
    logger.info("shape=%s artists=%d", df.shape, df["artist_slug"].nunique())

    p1 = evaluate_random_lao(df)
    logger.info("Primary 1 cold_mdape=%.2f%% CI=[%.2f, %.2f]", p1["cold_mdape"], p1["ci_95"][0], p1["ci_95"][1])

    p2 = evaluate_time_split(df)
    logger.info("Primary 2 cold_mdape=%.2f%% degradation=%.2f%%p", p2["cold_mdape"], p2["time_degradation_pp"])

    j = judgment(p1, p2)
    logger.info("Judgment: %s", j["verdict"])

    out = {
        "prereg": "docs/track2_cold_validation_cycle1_prereg_20260508.md",
        "dataset": str(DATA.name),
        "n_total": int(len(df)),
        "primary_1": p1,
        "primary_2": p2,
        "judgment": j,
        "thresholds": {
            "primary": PRIMARY_THRESHOLD_PCT,
            "low_price_harm": LOW_PRICE_HARM_THRESHOLD,
            "cold_sub_bin_harm": COLD_SUB_BIN_HARM_THRESHOLD,
            "time_degradation": TIME_DEGRADATION_THRESHOLD,
        },
        "spec": {
            "huber_epsilon": HUBER_EPS,
            "huber_alpha": HUBER_ALPHA,
            "n_boot": N_BOOT,
            "seed": SEED,
            "test_size": TEST_SIZE,
            "cold_threshold": COLD_TRAIN_COUNT_THRESHOLD,
            "time_split_year": TIME_SPLIT_YEAR,
        },
    }
    out_path = RESULTS_DIR / "track2_cold_validation_cycle1_stage1.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s", out_path)


if __name__ == "__main__":
    main()
