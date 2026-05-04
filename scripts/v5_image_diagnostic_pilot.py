"""V5 Cycle Day 1-4 — Image retrieval prior 사전 진단 (EXPLORATORY PILOT).

⚠️ DECISION-BINDING X (코덱스 7차/8차 자문):
  - 본 진단은 V4 cycle data (Artsy 7,626) 기반 pilot
  - 본 마이그레이션 데이터 도착 후 compressed re-check 필수
  - 본 결과로 A 를 영구 cut 하지 않고 "provisional / pending re-check"

코덱스 6단계 진단 (Day 5 보류, 1-5 만):
1. LAO split (artist_slug overlap=0, hard gate)
2. Image-only 모델 cold-start metric
3. Retrieval sanity check (top-k NN, 정성 검토)
4. Memorization audit (same-artist neighbor allow vs forbid)
5. Cluster-conditional variance

Pass/Fail (V5 plan §5):
- LAO: overlap=0 (hard)
- Image-only: cold-start MdAPE 개선 ≥ 5% 또는 0.8pp
- Retrieval sanity: top-10 NN 무관 비율 ≤ 30%
- Memorization: same-artist 제거 후 gain ≥ 50% 유지
- Cluster variance: n≥30 cluster 과반에서 IQR -10%

Day 4 종료 시 ≥2 fail → A pilot fail (provisional cut, 본 데이터 후 재검증)

Usage: PYTHONPATH=src python3 scripts/v5_image_diagnostic_pilot.py
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from visionai.price_engine._v5_eval_framework import lao_split, mdape

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"

EMBED_PATH = OUT_DIR / "dinov2_embeddings.parquet"
SEED = 42  # pilot seed (마이그레이션 후 재추첨)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────
def load_artsy_with_embeddings() -> pd.DataFrame:
    """Artsy training data + DINOv2 embeddings inner join."""
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    artsy = artsy[artsy["is_excluded_for_training"] == 0].copy()
    artsy["artwork_id"] = artsy["artwork_id"].astype(str)

    embeds = pd.read_parquet(EMBED_PATH)
    embeds["artwork_id"] = embeds["artwork_id"].astype(str)

    df = artsy.merge(embeds[["artwork_id", "embedding"]], on="artwork_id", how="inner")
    df["ln_price"] = np.log(df["price_krw"].clip(lower=1.0))
    df = df[df["ln_price"].notna()].reset_index(drop=True)
    return df


def cosine_similarity_matrix(query: np.ndarray, key: np.ndarray) -> np.ndarray:
    """Cosine similarity (n_query, n_key). Both inputs already L2-normalized OK."""
    q_norm = query / (np.linalg.norm(query, axis=1, keepdims=True) + 1e-9)
    k_norm = key / (np.linalg.norm(key, axis=1, keepdims=True) + 1e-9)
    return q_norm @ k_norm.T


def knn_predict(
    train_emb: np.ndarray,
    train_y: np.ndarray,
    train_artists: np.ndarray,
    test_emb: np.ndarray,
    test_artists: np.ndarray,
    k: int = 10,
    exclude_same_artist: bool = True,
) -> np.ndarray:
    """Visual KNN prediction: median ln_price of top-k neighbors."""
    sim = cosine_similarity_matrix(test_emb, train_emb)  # (n_test, n_train)
    preds = np.zeros(len(test_emb))
    for i in range(len(test_emb)):
        scores = sim[i].copy()
        if exclude_same_artist:
            same_mask = (train_artists == test_artists[i])
            scores[same_mask] = -np.inf
        # top-k indices
        top_k_idx = np.argpartition(scores, -k)[-k:]
        # filter -inf (same artist completely)
        valid = scores[top_k_idx] > -np.inf
        if valid.sum() == 0:
            preds[i] = np.median(train_y)  # fallback
        else:
            preds[i] = np.median(train_y[top_k_idx[valid]])
    return preds


# ─────────────────────────────────────────────────────────────────────
# Step 1: LAO split (hard gate)
# ─────────────────────────────────────────────────────────────────────
def step1_lao_split(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, dict]:
    logger.info("=" * 60)
    logger.info("Step 1: LAO split (artist_slug overlap=0, hard gate)")
    logger.info("=" * 60)
    train_idx, test_idx = lao_split(df, group_col="artist_slug", test_size=0.20, seed=SEED)

    train_artists = set(df.iloc[train_idx]["artist_slug"].astype(str))
    test_artists = set(df.iloc[test_idx]["artist_slug"].astype(str))
    overlap = train_artists & test_artists
    assert len(overlap) == 0, f"Hard gate FAIL: {len(overlap)} overlap"

    res = {
        "train_n": int(len(train_idx)),
        "test_n": int(len(test_idx)),
        "train_artists": int(len(train_artists)),
        "test_artists": int(len(test_artists)),
        "overlap_artists": int(len(overlap)),
        "pass": True,
    }
    logger.info(f"  ✓ Hard gate PASS — overlap=0")
    logger.info(f"  Train {res['train_n']} ({res['train_artists']} artists) / Test {res['test_n']} ({res['test_artists']} artists)")
    return train_idx, test_idx, res


# ─────────────────────────────────────────────────────────────────────
# Step 2: Image-only model cold-start metric
# ─────────────────────────────────────────────────────────────────────
def step2_image_only(
    df: pd.DataFrame, train_idx: np.ndarray, test_idx: np.ndarray, k: int = 10,
) -> dict:
    logger.info("=" * 60)
    logger.info(f"Step 2: Image-only KNN model (k={k}, cold-start)")
    logger.info("=" * 60)
    train_emb = np.stack(df.iloc[train_idx]["embedding"].apply(np.array).values)
    test_emb = np.stack(df.iloc[test_idx]["embedding"].apply(np.array).values)
    train_y = df.iloc[train_idx]["ln_price"].to_numpy()
    test_y = df.iloc[test_idx]["ln_price"].to_numpy()
    train_artists = df.iloc[train_idx]["artist_slug"].astype(str).to_numpy()
    test_artists = df.iloc[test_idx]["artist_slug"].astype(str).to_numpy()

    # Image-only KNN (exclude same artist — but cold-start이라 어차피 같은 artist 없음)
    pred_log = knn_predict(train_emb, train_y, train_artists, test_emb, test_artists, k=k, exclude_same_artist=True)
    test_y_price = np.exp(test_y)
    pred_price = np.exp(pred_log)
    image_mdape = mdape(test_y_price, pred_price)

    # Naive baseline: train-set median price
    naive_pred = np.full_like(test_y_price, np.exp(np.median(train_y)))
    naive_mdape = mdape(test_y_price, naive_pred)

    # Improvement
    delta_pp = naive_mdape - image_mdape
    delta_pct = delta_pp / naive_mdape * 100 if naive_mdape > 0 else 0

    # Pass: cold-start MdAPE 개선 ≥ 5% 또는 0.8pp
    passed = delta_pp >= 0.8 or delta_pct >= 5.0

    res = {
        "k": k,
        "test_n": int(len(test_idx)),
        "naive_baseline_mdape": round(naive_mdape, 2),
        "image_only_mdape": round(image_mdape, 2),
        "delta_pp": round(delta_pp, 2),
        "delta_pct_relative": round(delta_pct, 2),
        "pass": passed,
    }
    logger.info(f"  Naive baseline MdAPE: {naive_mdape:.2f}")
    logger.info(f"  Image-only KNN MdAPE: {image_mdape:.2f}")
    logger.info(f"  Δ: {delta_pp:+.2f}pp ({delta_pct:+.2f}% relative)")
    logger.info(f"  Pass (≥0.8pp or ≥5%): {'✓' if passed else '✗'}")
    return res


# ─────────────────────────────────────────────────────────────────────
# Step 3: Retrieval sanity check
# ─────────────────────────────────────────────────────────────────────
def step3_retrieval_sanity(
    df: pd.DataFrame, train_idx: np.ndarray, test_idx: np.ndarray, n_samples: int = 30,
) -> dict:
    logger.info("=" * 60)
    logger.info(f"Step 3: Retrieval sanity check (top-10 NN, {n_samples} samples)")
    logger.info("=" * 60)
    rng = np.random.default_rng(SEED)
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    train_emb = np.stack(train_df["embedding"].apply(np.array).values)
    test_emb = np.stack(test_df["embedding"].apply(np.array).values)
    train_artists = train_df["artist_slug"].astype(str).to_numpy()

    # Sample n_samples test works
    sample_idx = rng.choice(len(test_df), size=min(n_samples, len(test_df)), replace=False)
    sim = cosine_similarity_matrix(test_emb[sample_idx], train_emb)

    samples = []
    duplicates = 0
    high_sim_count = 0  # similarity > 0.95 — possible near-duplicate

    for i, ti in enumerate(sample_idx):
        scores = sim[i]
        # Exclude same artist (cold-start, 어차피 same artist 없음)
        # Get top-10 NN
        top10_idx = np.argsort(scores)[::-1][:10]
        top10_sim = scores[top10_idx]
        if top10_sim[0] > 0.95:
            duplicates += 1  # potential near-duplicate
        high_sim_count += int(np.sum(top10_sim > 0.90))

        target = test_df.iloc[ti]
        sample = {
            "test_idx": int(ti),
            "test_artwork_id": str(target["artwork_id"]),
            "test_artist": str(target["artist_slug"]),
            "test_medium": str(target.get("medium_category", "")),
            "test_price_krw": float(target["price_krw"]),
            "top10_neighbors": [],
        }
        for rank, (ti_, score) in enumerate(zip(top10_idx, top10_sim), 1):
            nn = train_df.iloc[int(ti_)]
            sample["top10_neighbors"].append({
                "rank": rank,
                "artwork_id": str(nn["artwork_id"]),
                "artist": str(nn["artist_slug"]),
                "medium": str(nn.get("medium_category", "")),
                "price_krw": float(nn["price_krw"]),
                "similarity": round(float(score), 4),
                "image_url": str(nn.get("image_url", "")),
            })
        # Compute price coherence: NN price 분포 vs target price
        nn_prices = np.array([n["price_krw"] for n in sample["top10_neighbors"]])
        nn_log = np.log(nn_prices.clip(min=1))
        target_log = np.log(max(target["price_krw"], 1))
        sample["nn_log_median"] = round(float(np.median(nn_log)), 3)
        sample["nn_log_iqr"] = round(float(np.quantile(nn_log, 0.75) - np.quantile(nn_log, 0.25)), 3)
        sample["target_log"] = round(float(target_log), 3)
        sample["abs_log_residual"] = round(abs(target_log - sample["nn_log_median"]), 3)
        # Same medium share
        same_med = sum(1 for n in sample["top10_neighbors"] if n["medium"] == sample["test_medium"])
        sample["same_medium_share"] = round(same_med / 10, 2)
        samples.append(sample)

    duplicate_pct = duplicates / len(sample_idx) * 100
    avg_log_residual = float(np.mean([s["abs_log_residual"] for s in samples]))
    avg_same_medium = float(np.mean([s["same_medium_share"] for s in samples]))

    # Pass: duplicate_pct ≤ 2%, signal coherence (avg log residual ≤ 1.5 — exp(1.5)~4.5x)
    passed = duplicate_pct <= 2.0 and avg_log_residual <= 1.5

    res = {
        "n_samples": int(len(sample_idx)),
        "duplicate_suspicion_pct": round(duplicate_pct, 2),
        "high_sim_neighbor_count_avg": round(high_sim_count / len(sample_idx), 2),
        "avg_abs_log_residual": round(avg_log_residual, 3),
        "avg_same_medium_share": round(avg_same_medium, 3),
        "samples": samples[:10],  # 처음 10개만 저장 (디스크 절약)
        "pass": passed,
    }
    logger.info(f"  Duplicate 의심 (sim>0.95): {duplicate_pct:.1f}% (target ≤2%)")
    logger.info(f"  Avg |log_NN_median - log_target|: {avg_log_residual:.3f}")
    logger.info(f"  Avg same medium share: {avg_same_medium:.3f}")
    logger.info(f"  Pass (dup ≤2% + avg_residual ≤1.5): {'✓' if passed else '✗'}")
    return res


# ─────────────────────────────────────────────────────────────────────
# Step 4: Memorization audit
# ─────────────────────────────────────────────────────────────────────
def step4_memorization_audit(
    df: pd.DataFrame, train_idx: np.ndarray, test_idx: np.ndarray, k: int = 10,
) -> dict:
    """Same-artist neighbor 허용 vs 금지 비교.

    Cold-start (LAO) 환경에서는 test artists 가 train 에 없어서 same-artist 가
    어차피 0건. 따라서 memorization audit은 train internal 에서 평가:

    Train within-fold KFold:
    - Allow same-artist NN: A1
    - Forbid same-artist NN: A2
    - Compare gains over naive

    이게 cold-start (LAO) 보다 memorization 효과를 직접 평가.
    """
    logger.info("=" * 60)
    logger.info(f"Step 4: Memorization audit (train within-fold same-artist allow vs forbid)")
    logger.info("=" * 60)
    from sklearn.model_selection import KFold

    train_df = df.iloc[train_idx].reset_index(drop=True)
    train_emb = np.stack(train_df["embedding"].apply(np.array).values)
    train_y = train_df["ln_price"].to_numpy()
    train_artists = train_df["artist_slug"].astype(str).to_numpy()

    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    pred_allow = np.zeros(len(train_y))
    pred_forbid = np.zeros(len(train_y))
    naive_pred_log = np.zeros(len(train_y))

    for fold_tr, fold_te in kf.split(train_emb):
        emb_tr = train_emb[fold_tr]
        y_tr = train_y[fold_tr]
        art_tr = train_artists[fold_tr]
        emb_te = train_emb[fold_te]
        art_te = train_artists[fold_te]

        # Allow same-artist
        pred_allow[fold_te] = knn_predict(
            emb_tr, y_tr, art_tr, emb_te, art_te, k=k, exclude_same_artist=False,
        )
        # Forbid same-artist
        pred_forbid[fold_te] = knn_predict(
            emb_tr, y_tr, art_tr, emb_te, art_te, k=k, exclude_same_artist=True,
        )
        # Naive: train-fold median
        naive_pred_log[fold_te] = np.median(y_tr)

    y_price = np.exp(train_y)
    mdape_naive = mdape(y_price, np.exp(naive_pred_log))
    mdape_allow = mdape(y_price, np.exp(pred_allow))
    mdape_forbid = mdape(y_price, np.exp(pred_forbid))

    gain_allow = mdape_naive - mdape_allow
    gain_forbid = mdape_naive - mdape_forbid
    if gain_allow > 0:
        retention_pct = gain_forbid / gain_allow * 100
    else:
        retention_pct = float("nan")

    # Pass: gain_forbid ≥ 50% of gain_allow
    passed = retention_pct >= 50.0 if not np.isnan(retention_pct) else False

    res = {
        "k": k,
        "n_train": int(len(train_y)),
        "mdape_naive": round(mdape_naive, 2),
        "mdape_knn_allow_same_artist": round(mdape_allow, 2),
        "mdape_knn_forbid_same_artist": round(mdape_forbid, 2),
        "gain_allow_pp": round(gain_allow, 2),
        "gain_forbid_pp": round(gain_forbid, 2),
        "retention_pct": round(retention_pct, 1) if not np.isnan(retention_pct) else None,
        "pass": passed,
    }
    logger.info(f"  Naive MdAPE: {mdape_naive:.2f}")
    logger.info(f"  Allow same-artist: {mdape_allow:.2f} (gain {gain_allow:.2f}pp)")
    logger.info(f"  Forbid same-artist: {mdape_forbid:.2f} (gain {gain_forbid:.2f}pp)")
    logger.info(f"  Retention: {retention_pct:.1f}% (≥50% pass)")
    logger.info(f"  Pass: {'✓' if passed else '✗'}")
    return res


# ─────────────────────────────────────────────────────────────────────
# Step 5: Cluster-conditional variance
# ─────────────────────────────────────────────────────────────────────
def step5_cluster_variance(
    df: pd.DataFrame, train_idx: np.ndarray, n_clusters: int = 30, min_n: int = 30,
) -> dict:
    logger.info("=" * 60)
    logger.info(f"Step 5: Cluster-conditional variance (k-means k={n_clusters}, min_n={min_n})")
    logger.info("=" * 60)
    train_df = df.iloc[train_idx].reset_index(drop=True)
    train_emb = np.stack(train_df["embedding"].apply(np.array).values)
    train_y = train_df["ln_price"].to_numpy()

    # K-means cluster
    km = KMeans(n_clusters=n_clusters, random_state=SEED, n_init=10)
    cluster_labels = km.fit_predict(train_emb)

    global_iqr = float(np.quantile(train_y, 0.75) - np.quantile(train_y, 0.25))
    global_std = float(np.std(train_y, ddof=1))

    cluster_stats = []
    eligible_clusters = 0
    iqr_reduced_count = 0

    for c in range(n_clusters):
        mask = cluster_labels == c
        n = int(mask.sum())
        if n < min_n:
            cluster_stats.append({"cluster": c, "n": n, "status": "underpowered"})
            continue
        eligible_clusters += 1
        sub_y = train_y[mask]
        iqr = float(np.quantile(sub_y, 0.75) - np.quantile(sub_y, 0.25))
        std = float(np.std(sub_y, ddof=1))
        iqr_ratio = iqr / global_iqr
        if iqr_ratio <= 0.90:  # 10% reduction
            iqr_reduced_count += 1
        cluster_stats.append({
            "cluster": c, "n": n, "log_price_iqr": round(iqr, 3),
            "log_price_std": round(std, 3),
            "iqr_ratio_vs_global": round(iqr_ratio, 3),
        })

    iqr_reduced_pct = iqr_reduced_count / eligible_clusters * 100 if eligible_clusters else 0.0

    # Pass: 과반 (>50%) eligible clusters with IQR -10%
    passed = iqr_reduced_pct >= 50.0

    res = {
        "n_clusters": n_clusters,
        "min_n_threshold": min_n,
        "eligible_clusters": eligible_clusters,
        "global_log_iqr": round(global_iqr, 3),
        "global_log_std": round(global_std, 3),
        "iqr_reduced_count": iqr_reduced_count,
        "iqr_reduced_pct": round(iqr_reduced_pct, 1),
        "cluster_stats": cluster_stats,
        "pass": passed,
    }
    logger.info(f"  Global log_price IQR: {global_iqr:.3f}, std: {global_std:.3f}")
    logger.info(f"  Eligible clusters (n≥{min_n}): {eligible_clusters}/{n_clusters}")
    logger.info(f"  Clusters with IQR -10%: {iqr_reduced_count}/{eligible_clusters} ({iqr_reduced_pct:.1f}%)")
    logger.info(f"  Pass (≥50%): {'✓' if passed else '✗'}")
    return res


# ─────────────────────────────────────────────────────────────────────
# Main — 5단계 + 종합 판정
# ─────────────────────────────────────────────────────────────────────
def main() -> None:
    logger.info("=" * 70)
    logger.info("V5 cycle Day 1-4 — Image retrieval prior diagnostic pilot")
    logger.info("⚠️  EXPLORATORY — 본 결과는 V4 cycle data 기반, decision-binding X")
    logger.info("=" * 70)

    t0 = time.time()
    df = load_artsy_with_embeddings()
    logger.info(f"\nData: {len(df)} works × {len(df['embedding'].iloc[0])}-dim embedding")
    logger.info(f"Unique artists: {df['artist_slug'].nunique()}")

    # Step 1
    train_idx, test_idx, step1 = step1_lao_split(df)

    # Step 2
    step2 = step2_image_only(df, train_idx, test_idx, k=10)

    # Step 3
    step3 = step3_retrieval_sanity(df, train_idx, test_idx, n_samples=30)

    # Step 4
    step4 = step4_memorization_audit(df, train_idx, test_idx, k=10)

    # Step 5
    step5 = step5_cluster_variance(df, train_idx, n_clusters=30, min_n=30)

    # 종합 판정
    pass_count = sum([step1["pass"], step2["pass"], step3["pass"], step4["pass"], step5["pass"]])
    fail_count = 5 - pass_count
    overall_passed = fail_count <= 1  # ≤1 fail = pilot pass (Day 4 종료 기준 ≥2 fail = cut)

    overall = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pilot_status": "EXPLORATORY — V4 cycle data, decision-binding X",
        "data": {
            "n": int(len(df)),
            "embedding_dim": int(len(df["embedding"].iloc[0])),
            "n_artists": int(df["artist_slug"].nunique()),
        },
        "seed": SEED,
        "step1_lao_split": step1,
        "step2_image_only": step2,
        "step3_retrieval_sanity": step3,
        "step4_memorization_audit": step4,
        "step5_cluster_variance": step5,
        "summary": {
            "pass_count": pass_count,
            "fail_count": fail_count,
            "verdict": "PILOT PASS — A 후보 유지" if overall_passed else "PILOT FAIL — A provisional cut (본 데이터 후 재검증)",
            "overall_passed": overall_passed,
        },
        "elapsed_sec": round(time.time() - t0, 1),
    }

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / "v5_image_diagnostic_pilot.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(overall, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"PILOT 종합 ({pass_count}/5 pass, {fail_count} fail)")
    print("=" * 70)
    print(f"Step 1 LAO split:           {'✓' if step1['pass'] else '✗'}")
    print(f"Step 2 Image-only KNN:      {'✓' if step2['pass'] else '✗'}  Δ {step2['delta_pp']:+.2f}pp")
    print(f"Step 3 Retrieval sanity:    {'✓' if step3['pass'] else '✗'}  dup={step3['duplicate_suspicion_pct']:.1f}%, residual={step3['avg_abs_log_residual']:.2f}")
    print(f"Step 4 Memorization audit:  {'✓' if step4['pass'] else '✗'}  retention={step4['retention_pct']}%")
    print(f"Step 5 Cluster variance:    {'✓' if step5['pass'] else '✗'}  reduced={step5['iqr_reduced_pct']:.1f}%")
    print()
    print(f"Verdict: {overall['summary']['verdict']}")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
