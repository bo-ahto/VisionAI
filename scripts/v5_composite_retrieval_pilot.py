"""V5 Cycle R (composite retrieval prior) PoC simulation — V4 cycle data.

⚠️ DECISION-BINDING X — V4 data PoC. 본 데이터 도착 후 재검증.

코덱스 9차 자문 권고:
- 3-way compressed re-check
- (A) structured-only (medium + size NN)
- (B) composite (image + medium/size joint)
- (C) image-only (PILOT 재현)
- Image incremental gain = (B) - (A) ≤ -0.3pp 시 R 유효

Design: docs/v5_R_composite_design.md
- Filter: same-medium hard filter
- Composite distance: (1-λ)*image_dist + λ*size_dist
- λ grid search: [0, 0.1, 0.3, 0.5, 0.7, 1.0]
- 3 seeds: 42, 123, 7777

Usage: PYTHONPATH=src python3 scripts/v5_composite_retrieval_pilot.py
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from visionai.price_engine._v5_eval_framework import lao_split, mdape

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"

EMBED_PATH = OUT_DIR / "dinov2_embeddings.parquet"
SEEDS = [42, 123, 7777]
LAMBDA_GRID = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]
K = 10
MIN_POOL_SIZE = 5  # 같은 medium pool 이 너무 작으면 fallback


def load_artsy_with_embeddings() -> pd.DataFrame:
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    artsy = artsy[artsy["is_excluded_for_training"] == 0].copy()
    artsy["artwork_id"] = artsy["artwork_id"].astype(str)

    embeds = pd.read_parquet(EMBED_PATH)
    embeds["artwork_id"] = embeds["artwork_id"].astype(str)

    df = artsy.merge(embeds[["artwork_id", "embedding"]], on="artwork_id", how="inner")
    df["ln_price"] = np.log(df["price_krw"].clip(lower=1.0))
    df = df[df["ln_price"].notna()].reset_index(drop=True)
    df["log_area"] = np.log(df["area_cm2"].clip(lower=1.0))
    df["medium_filter"] = df["medium_category"].fillna("unknown").astype(str)
    return df


def compute_image_distance(query_emb: np.ndarray, key_emb: np.ndarray) -> np.ndarray:
    """Image distance = 1 - cosine similarity (n_query, n_key)."""
    q_norm = query_emb / (np.linalg.norm(query_emb, axis=1, keepdims=True) + 1e-9)
    k_norm = key_emb / (np.linalg.norm(key_emb, axis=1, keepdims=True) + 1e-9)
    return 1.0 - q_norm @ k_norm.T


def compute_size_distance(query_log_area: np.ndarray, key_log_area: np.ndarray, sigma: float) -> np.ndarray:
    """Size distance |log(s_q) - log(s_t)| / sigma_log_size_train (n_query, n_key)."""
    return np.abs(query_log_area[:, None] - key_log_area[None, :]) / max(sigma, 1e-6)


def composite_retrieval_predict(
    train_emb: np.ndarray,
    train_y: np.ndarray,
    train_artists: np.ndarray,
    train_medium: np.ndarray,
    train_log_area: np.ndarray,
    test_emb: np.ndarray,
    test_artists: np.ndarray,
    test_medium: np.ndarray,
    test_log_area: np.ndarray,
    k: int,
    lambda_size: float,
    same_medium_filter: bool,
    exclude_same_artist: bool = True,
    sigma_log_size: float | None = None,
) -> tuple[np.ndarray, dict]:
    """Composite retrieval prediction.

    Args:
        lambda_size: weight on size distance (0 = image-only, 1 = size-only)
        same_medium_filter: True = filter to same medium, False = global pool
    Returns:
        (predictions, stats)
    """
    if sigma_log_size is None:
        sigma_log_size = float(np.std(train_log_area, ddof=1)) if len(train_log_area) > 1 else 1.0

    # Image distance (n_test, n_train)
    d_img = compute_image_distance(test_emb, train_emb)
    # Size distance (n_test, n_train)
    d_size = compute_size_distance(test_log_area, train_log_area, sigma_log_size)
    # Composite distance
    d_composite = (1 - lambda_size) * d_img + lambda_size * d_size

    n_test = len(test_emb)
    preds = np.zeros(n_test)
    stats = {"fallback_count": 0, "small_pool_count": 0}

    for i in range(n_test):
        # Filter
        valid = np.ones(len(train_emb), dtype=bool)
        if same_medium_filter:
            valid &= (train_medium == test_medium[i])
        if exclude_same_artist:
            valid &= (train_artists != test_artists[i])

        if valid.sum() < MIN_POOL_SIZE:
            stats["small_pool_count"] += 1
            if same_medium_filter:
                # Fallback: drop medium filter
                valid = exclude_same_artist and (train_artists != test_artists[i]) or np.ones(len(train_emb), dtype=bool)
                if exclude_same_artist:
                    valid = train_artists != test_artists[i]
                else:
                    valid = np.ones(len(train_emb), dtype=bool)
                stats["fallback_count"] += 1

        if valid.sum() == 0:
            preds[i] = np.median(train_y)
            continue

        # Get top-k by composite distance
        scores = d_composite[i].copy()
        scores[~valid] = np.inf
        top_k = np.argpartition(scores, min(k, valid.sum() - 1))[:k]
        top_k_valid = top_k[scores[top_k] < np.inf]
        if len(top_k_valid) == 0:
            preds[i] = np.median(train_y)
        else:
            preds[i] = np.median(train_y[top_k_valid])

    return preds, stats


def evaluate_seed(df: pd.DataFrame, seed: int) -> dict:
    """Run all 3 conditions × λ grid for one seed."""
    train_idx, test_idx = lao_split(df, group_col="artist_slug", test_size=0.20, seed=seed)
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    train_emb = np.stack(train_df["embedding"].apply(np.array).values)
    test_emb = np.stack(test_df["embedding"].apply(np.array).values)
    train_y = train_df["ln_price"].to_numpy()
    test_y = test_df["ln_price"].to_numpy()
    train_artists = train_df["artist_slug"].astype(str).to_numpy()
    test_artists = test_df["artist_slug"].astype(str).to_numpy()
    train_medium = train_df["medium_filter"].to_numpy()
    test_medium = test_df["medium_filter"].to_numpy()
    train_log_area = train_df["log_area"].to_numpy()
    test_log_area = test_df["log_area"].to_numpy()

    sigma = float(np.std(train_log_area, ddof=1))
    test_y_price = np.exp(test_y)

    # Naive baseline
    naive_pred = np.full_like(test_y_price, np.exp(np.median(train_y)))
    naive_mdape = mdape(test_y_price, naive_pred)

    seed_result = {
        "seed": seed,
        "train_n": int(len(train_idx)),
        "test_n": int(len(test_idx)),
        "sigma_log_size": round(sigma, 3),
        "naive_baseline_mdape": round(naive_mdape, 2),
        "conditions": {},
    }

    # (C) Image-only — global pool, image distance only (PILOT 재현)
    pred_C, stats_C = composite_retrieval_predict(
        train_emb, train_y, train_artists, train_medium, train_log_area,
        test_emb, test_artists, test_medium, test_log_area,
        k=K, lambda_size=0.0, same_medium_filter=False, sigma_log_size=sigma,
    )
    mdape_C = mdape(test_y_price, np.exp(pred_C))
    seed_result["conditions"]["C_image_only"] = {
        "mdape": round(mdape_C, 2),
        "delta_vs_naive": round(naive_mdape - mdape_C, 2),
        **stats_C,
    }

    # (A) Structured-only — same-medium filter + size-only ranking (λ=1.0, no image)
    pred_A, stats_A = composite_retrieval_predict(
        train_emb, train_y, train_artists, train_medium, train_log_area,
        test_emb, test_artists, test_medium, test_log_area,
        k=K, lambda_size=1.0, same_medium_filter=True, sigma_log_size=sigma,
    )
    mdape_A = mdape(test_y_price, np.exp(pred_A))
    seed_result["conditions"]["A_structured_only"] = {
        "mdape": round(mdape_A, 2),
        "delta_vs_naive": round(naive_mdape - mdape_A, 2),
        **stats_A,
    }

    # (B) Composite — same-medium filter + composite ranking (various λ)
    composite_results = {}
    for lam in LAMBDA_GRID:
        pred_B, stats_B = composite_retrieval_predict(
            train_emb, train_y, train_artists, train_medium, train_log_area,
            test_emb, test_artists, test_medium, test_log_area,
            k=K, lambda_size=lam, same_medium_filter=True, sigma_log_size=sigma,
        )
        mdape_B = mdape(test_y_price, np.exp(pred_B))
        composite_results[f"lambda_{lam:.1f}"] = {
            "lambda": lam,
            "mdape": round(mdape_B, 2),
            "delta_vs_naive": round(naive_mdape - mdape_B, 2),  # 양수 = composite 가 naive 보다 좋음
            "image_incremental_gain": round(mdape_A - mdape_B, 2),  # 양수 = composite 가 A 보다 좋음 (image가 도움)
            **stats_B,
        }
    seed_result["conditions"]["B_composite_grid"] = composite_results

    # Best λ in this seed
    best_lam = min(composite_results.values(), key=lambda x: x["mdape"])
    seed_result["best_composite_lambda"] = best_lam["lambda"]
    seed_result["best_composite_mdape"] = best_lam["mdape"]
    seed_result["image_incremental_gain_at_best_lambda"] = best_lam["image_incremental_gain"]

    return seed_result


def main() -> None:
    logger.info("=" * 70)
    logger.info("V5 R (composite retrieval prior) PoC — V4 cycle data")
    logger.info("⚠️ EXPLORATORY — decision-binding X")
    logger.info("=" * 70)

    t0 = time.time()
    df = load_artsy_with_embeddings()
    logger.info(f"\nData: {len(df)} works, {df['artist_slug'].nunique()} artists")
    logger.info(f"Medium distribution: {df['medium_filter'].value_counts().head(10).to_dict()}")
    logger.info(f"λ grid: {LAMBDA_GRID}, k={K}")

    seed_results = []
    for seed in SEEDS:
        logger.info(f"\n--- Seed {seed} ---")
        r = evaluate_seed(df, seed)
        seed_results.append(r)
        # Compact log
        c = r["conditions"]
        logger.info(f"  Naive: {r['naive_baseline_mdape']:.2f}")
        logger.info(f"  (C) Image-only: {c['C_image_only']['mdape']:.2f} ({c['C_image_only']['delta_vs_naive']:+.2f}pp vs naive)")
        logger.info(f"  (A) Structured-only: {c['A_structured_only']['mdape']:.2f} ({c['A_structured_only']['delta_vs_naive']:+.2f}pp vs naive)")
        for lam in LAMBDA_GRID:
            b = c["B_composite_grid"][f"lambda_{lam:.1f}"]
            logger.info(f"  (B) Composite λ={lam:.1f}: MdAPE {b['mdape']:.2f} (image gain vs A: {b['image_incremental_gain']:+.2f}pp)")

    # 종합 — 3 seeds aggregate
    def aggregate_condition(condition_key: str):
        vals = []
        for r in seed_results:
            v = r["conditions"].get(condition_key)
            if v is not None and "mdape" in v:
                vals.append(v["mdape"])
        if not vals:
            return None
        return {"mean": round(float(np.mean(vals)), 2), "std": round(float(np.std(vals, ddof=1)), 2), "values": vals}

    naive_vals = [r["naive_baseline_mdape"] for r in seed_results]
    summary = {
        "naive_baseline": {"mean": round(float(np.mean(naive_vals)), 2), "std": round(float(np.std(naive_vals, ddof=1)), 2), "values": naive_vals},
        "C_image_only": aggregate_condition("C_image_only"),
        "A_structured_only": aggregate_condition("A_structured_only"),
    }

    # Composite per λ
    summary["B_composite_per_lambda"] = {}
    for lam in LAMBDA_GRID:
        key = f"lambda_{lam:.1f}"
        vals = [r["conditions"]["B_composite_grid"][key]["mdape"] for r in seed_results]
        gains = [r["conditions"]["B_composite_grid"][key]["image_incremental_gain"] for r in seed_results]
        summary["B_composite_per_lambda"][key] = {
            "lambda": lam,
            "mdape_mean": round(float(np.mean(vals)), 2),
            "mdape_std": round(float(np.std(vals, ddof=1)), 2),
            "image_gain_mean": round(float(np.mean(gains)), 2),  # 양수 = composite 가 A 보다 좋음
            "image_gain_std": round(float(np.std(gains, ddof=1)), 2),
            "image_gain_values": [round(g, 2) for g in gains],
            "all_pos": all(g > 0 for g in gains),  # 모든 seed 에서 composite 가 A 보다 좋음
            "passes_gate": all(g >= 0.3 for g in gains),  # ≥ +0.3pp 양수 gate
        }

    # Best lambda decision (lowest MdAPE, but check vs A as well)
    best_lambda_keys = [r["best_composite_lambda"] for r in seed_results]
    image_incremental_gains_at_best = [r["image_incremental_gain_at_best_lambda"] for r in seed_results]
    summary["best_lambda_per_seed"] = best_lambda_keys
    summary["image_incremental_gain_at_best"] = {
        "values": image_incremental_gains_at_best,
        "mean": round(float(np.mean(image_incremental_gains_at_best)), 2),
        "all_pos": all(g > 0 for g in image_incremental_gains_at_best),
    }

    # Verdict
    any_lambda_passes = any(v["passes_gate"] for v in summary["B_composite_per_lambda"].values())
    summary["verdict"] = {
        "image_incremental_gate": "≥ +0.3pp on all 3 seeds (image makes composite better than A)",
        "any_lambda_passes_gate": any_lambda_passes,
        "best_lambdas": best_lambda_keys,
        "interpretation": (
            "R viable — at least one λ passes image incremental gate" if any_lambda_passes
            else "R image incremental insufficient — structured-only retrieval (A) is sufficient. Cut image."
        ),
    }

    final_result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pilot_status": "EXPLORATORY — V4 cycle data, decision-binding X",
        "data": {"n_works": int(len(df)), "n_artists": int(df["artist_slug"].nunique())},
        "seeds": SEEDS,
        "lambda_grid": LAMBDA_GRID,
        "k": K,
        "seed_results": seed_results,
        "aggregate_summary": summary,
        "elapsed_sec": round(time.time() - t0, 1),
    }

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / "v5_composite_retrieval_pilot.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("R PoC 종합 (3 seeds aggregate)")
    print("=" * 70)
    print(f"\n[Naive baseline]:        MdAPE {summary['naive_baseline']['mean']:.2f} ± {summary['naive_baseline']['std']:.2f}")
    print(f"[C: Image-only]:         MdAPE {summary['C_image_only']['mean']:.2f} ± {summary['C_image_only']['std']:.2f}")
    print(f"[A: Structured-only]:    MdAPE {summary['A_structured_only']['mean']:.2f} ± {summary['A_structured_only']['std']:.2f}")
    print(f"\n[B: Composite per λ]    image incremental gain (positive = image helps over A)")
    for lam in LAMBDA_GRID:
        key = f"lambda_{lam:.1f}"
        b = summary["B_composite_per_lambda"][key]
        gate_marker = "✓ gate pass (≥+0.3pp)" if b["passes_gate"] else ("± mixed" if not b["all_pos"] else "○ partial")
        print(f"  λ={lam:.1f}: MdAPE {b['mdape_mean']:.2f}, gain {b['image_gain_mean']:+.2f}pp (per seed: {b['image_gain_values']}) {gate_marker}")
    print(f"\nVerdict: {summary['verdict']['interpretation']}")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
