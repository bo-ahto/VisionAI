"""Feature Track Axis A.4 — Title Text Embedding (MiniLM, PCA K=10) cold-start LAO.

사전등록 freeze: docs/feature_track_axis_a4_prereg_20260507.md (2026-05-07)
- Embedding model: paraphrase-multilingual-MiniLM-L12-v2 (384-dim)
- PCA top-K=10 (train fold fit, test transform — leakage-safe)
- Estimator: HuberRegressor(epsilon=1.35, alpha=1e-4)
- Primary: Δ ≤ -1.0%p AND Cluster bootstrap 99% CI 상한 ≤ 0 (α=0.01)
- 🔴 Hard gate: Δ_low ≤ 0%p
- 100-seed LAO + cluster bootstrap n=2000 (진짜 cluster bootstrap, A.1 v2 fix)
- A.1/A.2/A.3 features drop = alternative hypothesis sequence
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.decomposition import PCA

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
EMB_CACHE = ROOT / "data" / "curated" / "title_embeddings_minilm_v1.npy"
RESULTS = Path(__file__).parent / "results"
LOW_PRICE_KRW = 5_000_000
N_SEEDS = 100
N_BOOT = 2000
PCA_K = 10
PCA_SEED = 42

STAGE3 = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
EMB_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def restricted_cubic_spline(x, knots):
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


def build_f4_spline(df, knots=None):
    out = df[["log_area", "birth_year_centered", "log_artist_total_works"]].copy().reset_index(drop=True)
    if knots is None:
        knots = np.percentile(df["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    out["log_area_spline"] = sp[:, 0]
    return out, knots


def build_or_load_embeddings(df):
    """모든 title 의 384-dim embedding 사전 계산 (deterministic, leakage 무관)."""
    if EMB_CACHE.exists():
        logger.info(f"Loading cached embeddings: {EMB_CACHE.relative_to(ROOT)}")
        embs = np.load(EMB_CACHE)
        if len(embs) == len(df):
            return embs
        logger.warning(f"  cache row mismatch ({len(embs)} vs {len(df)}), regenerating")

    from sentence_transformers import SentenceTransformer
    logger.info(f"Loading embedding model: {EMB_MODEL_NAME}")
    model = SentenceTransformer(EMB_MODEL_NAME)
    titles = df["title"].fillna("").tolist()
    logger.info(f"Encoding {len(titles)} titles ...")
    embs = model.encode(titles, show_progress_bar=False, batch_size=64)
    embs = np.asarray(embs, dtype=np.float32)
    EMB_CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.save(EMB_CACHE, embs)
    logger.info(f"Cached embeddings: {EMB_CACHE.relative_to(ROOT)} (shape {embs.shape})")
    return embs


def fit_pca(emb_train, k=PCA_K, seed=PCA_SEED):
    pca = PCA(n_components=k, random_state=seed)
    pca.fit(emb_train)
    return pca


def build_a4_features(df_tr, df_te, emb_full, train_mask, test_mask):
    """A.4 spec features = F4 + spline + title PCA top-K (train fold fit)."""
    feat_tr_base, knots = build_f4_spline(df_tr)
    feat_te_base, _ = build_f4_spline(df_te, knots=knots)
    Xtr_base = feat_tr_base.values
    Xte_base = feat_te_base.values

    emb_tr = emb_full[train_mask]
    emb_te = emb_full[test_mask]
    pca = fit_pca(emb_tr, k=PCA_K, seed=PCA_SEED)
    Xtr_emb = pca.transform(emb_tr)
    Xte_emb = pca.transform(emb_te)

    Xtr_a4 = np.column_stack([Xtr_base, Xtr_emb])
    Xte_a4 = np.column_stack([Xte_base, Xte_emb])
    return Xtr_base, Xte_base, Xtr_a4, Xte_a4


def fit_huber(Xtr, ytr, Xte):
    if len(ytr) < 5:
        return np.full(len(Xte), float(np.mean(ytr) if len(ytr) else 0.0))
    m = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=2000)
    m.fit(Xtr, ytr)
    return Xte @ m.coef_ + m.intercept_


def mdape_log(yte, pred):
    if len(yte) == 0:
        return None
    return float(np.median(np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)) * 100)


def lao_split(df, seed):
    rng = np.random.default_rng(seed)
    artists = df["artist_slug"].unique()
    n_test = max(1, int(len(artists) * 0.2))
    test_artists = set(rng.choice(artists, size=n_test, replace=False))
    return ~df["artist_slug"].isin(test_artists).values, df["artist_slug"].isin(test_artists).values


def eval_one_seed(df, y, emb_full, seed, stage3_artists):
    train_mask, test_mask = lao_split(df, seed)
    df_tr = df[train_mask].reset_index(drop=True)
    df_te = df[test_mask].reset_index(drop=True)
    if len(df_tr) < 50 or len(df_te) < 5:
        return None

    y_tr = y[train_mask].values.astype(float)
    y_te = y[test_mask].values.astype(float)

    Xtr_base, Xte_base, Xtr_a4, Xte_a4 = build_a4_features(df_tr, df_te, emb_full, train_mask, test_mask)

    pred_baseline = fit_huber(Xtr_base, y_tr, Xte_base)
    pred_a4 = fit_huber(Xtr_a4, y_tr, Xte_a4)

    is_low_te = (df_te["price_krw"].values < LOW_PRICE_KRW)
    is_newly_warm_te = ~df_te["artist_slug"].isin(stage3_artists).values

    return {
        "seed": seed,
        "n_test": int(len(y_te)),
        "n_test_low": int(is_low_te.sum()),
        "n_test_high": int((~is_low_te).sum()),
        "n_test_newly_warm": int(is_newly_warm_te.sum()),
        "baseline_overall": mdape_log(y_te, pred_baseline),
        "a4_overall": mdape_log(y_te, pred_a4),
        "baseline_low": mdape_log(y_te[is_low_te], pred_baseline[is_low_te]) if is_low_te.sum() else None,
        "a4_low": mdape_log(y_te[is_low_te], pred_a4[is_low_te]) if is_low_te.sum() else None,
        "baseline_high": mdape_log(y_te[~is_low_te], pred_baseline[~is_low_te]) if (~is_low_te).sum() else None,
        "a4_high": mdape_log(y_te[~is_low_te], pred_a4[~is_low_te]) if (~is_low_te).sum() else None,
        "baseline_newly": mdape_log(y_te[is_newly_warm_te], pred_baseline[is_newly_warm_te]) if is_newly_warm_te.sum() else None,
        "a4_newly": mdape_log(y_te[is_newly_warm_te], pred_a4[is_newly_warm_te]) if is_newly_warm_te.sum() else None,
        "test_artists": df_te["artist_slug"].values.tolist(),
        "y_te": y_te.tolist(),
        "pred_baseline": pred_baseline.tolist(),
        "pred_a4": pred_a4.tolist(),
    }


def cluster_bootstrap_diff(yte, pred_a, pred_b, test_artists, n_boot=N_BOOT, seed=42):
    rng = np.random.default_rng(seed)
    yte = np.asarray(yte)
    pred_a = np.asarray(pred_a)
    pred_b = np.asarray(pred_b)
    test_artists = np.asarray(test_artists)
    unique = np.unique(test_artists)
    artist_indices = {a: np.where(test_artists == a)[0] for a in unique}
    diffs = []
    for _ in range(n_boot):
        sample_artists = rng.choice(unique, size=len(unique), replace=True)
        idx = np.concatenate([artist_indices[a] for a in sample_artists])
        if len(idx) < 3:
            continue
        diffs.append(mdape_log(yte[idx], pred_a[idx]) - mdape_log(yte[idx], pred_b[idx]))
    diffs = np.array(diffs)
    return {
        "mean": float(np.mean(diffs)),
        "ci_lo_95": float(np.percentile(diffs, 2.5)),
        "ci_hi_95": float(np.percentile(diffs, 97.5)),
        "ci_lo_99": float(np.percentile(diffs, 0.5)),
        "ci_hi_99": float(np.percentile(diffs, 99.5)),
        "p_1sided": float((diffs >= 0).mean()),
    }


def run():
    df = pd.read_parquet(DATA)
    y = df["log_price"]

    if STAGE3.exists():
        stage3_artists = set(pd.read_parquet(STAGE3)["artist_slug"].unique())
    else:
        stage3_artists = set()

    logger.info("=" * 80)
    logger.info("Feature Track Axis A.4 — Title Text Embedding (MiniLM, PCA K=10) cold-start LAO")
    logger.info("=" * 80)
    logger.info(f"Source: {DATA.relative_to(ROOT)} ({len(df):,} 작품)")
    logger.info(f"Embedding model: {EMB_MODEL_NAME} (384-dim → PCA K={PCA_K})")
    logger.info(f"Stage 3 cohort artists (newly-warm 정의용): {len(stage3_artists)}")

    emb_full = build_or_load_embeddings(df)
    logger.info(f"Embedding shape: {emb_full.shape}")

    seed_results = []
    skipped = 0
    for s in range(N_SEEDS):
        try:
            r = eval_one_seed(df, y, emb_full, s, stage3_artists)
            if r is None:
                skipped += 1
                continue
            seed_results.append(r)
        except Exception as e:
            logger.warning(f"  seed {s} FAIL: {e}")
            skipped += 1
        if (s + 1) % 25 == 0:
            logger.info(f"  ... {s+1}/{N_SEEDS} done")

    logger.info(f"\n[100-seed LAO] 완료 {len(seed_results)} / skip {skipped}")

    def agg(key):
        vals = [r[key] for r in seed_results if r.get(key) is not None]
        return np.array(vals)

    base_overall = agg("baseline_overall")
    a4_overall = agg("a4_overall")
    base_low = agg("baseline_low")
    a4_low = agg("a4_low")
    base_high = agg("baseline_high")
    a4_high = agg("a4_high")
    base_newly = agg("baseline_newly")
    a4_newly = agg("a4_newly")

    diff_overall = a4_overall - base_overall
    diff_low = np.array([r["a4_low"] - r["baseline_low"] for r in seed_results if r.get("baseline_low") is not None and r.get("a4_low") is not None])
    diff_high = np.array([r["a4_high"] - r["baseline_high"] for r in seed_results if r.get("baseline_high") is not None and r.get("a4_high") is not None])
    diff_newly = np.array([r["a4_newly"] - r["baseline_newly"] for r in seed_results if r.get("baseline_newly") is not None and r.get("a4_newly") is not None])

    logger.info(f"\n{'metric':>22} {'baseline':>10} {'a4':>10} {'Δ (mean)':>12} {'n_seeds':>8}")
    logger.info(f"{'overall MdAPE':>22} {base_overall.mean():>8.2f}% {a4_overall.mean():>8.2f}% {diff_overall.mean():>+9.2f}%p {len(diff_overall):>5}")
    logger.info(f"{'low MdAPE':>22} {base_low.mean():>8.2f}% {a4_low.mean():>8.2f}% {diff_low.mean():>+9.2f}%p {len(diff_low):>5}")
    logger.info(f"{'mid/high MdAPE':>22} {base_high.mean():>8.2f}% {a4_high.mean():>8.2f}% {diff_high.mean():>+9.2f}%p {len(diff_high):>5}")
    logger.info(f"{'newly-warm MdAPE':>22} {base_newly.mean():>8.2f}% {a4_newly.mean():>8.2f}% {diff_newly.mean():>+9.2f}%p {len(diff_newly):>5}")

    low_violations = int((diff_low > 0).sum())
    n_low_seeds = len(diff_low)
    logger.info(f"\n[Seed-level low violation rate] {low_violations}/{n_low_seeds} = {100*low_violations/n_low_seeds:.1f}%")

    rep = seed_results[0]
    boot = cluster_bootstrap_diff(rep["y_te"], rep["pred_a4"], rep["pred_baseline"], rep["test_artists"])
    logger.info(f"\n[Primary cluster bootstrap (rep seed=0, n={N_BOOT}, 진짜 cluster bootstrap)]")
    logger.info(f"  Δ overall (a4 - baseline) mean: {boot['mean']:+.2f}%p")
    logger.info(f"  95% CI: [{boot['ci_lo_95']:+.2f}, {boot['ci_hi_95']:+.2f}]")
    logger.info(f"  99% CI (α=0.01, Bonferroni 5 step): [{boot['ci_lo_99']:+.2f}, {boot['ci_hi_99']:+.2f}]")
    logger.info(f"  P(diff ≥ 0) = {boot['p_1sided']:.4f}")

    primary_ci_99_pass = boot["ci_hi_99"] <= 0
    primary_ci_95_pass = boot["ci_hi_95"] <= 0
    primary_practical_pass = diff_overall.mean() <= -1.0
    low_harm_pass = diff_low.mean() <= 0

    logger.info(f"\n[PASS/BORDERLINE/FAIL 판정 (사전등록 §3 + α=0.01 99% CI decision)]")
    logger.info(f"  🔴 Hard gate Δ_low ≤ 0%p:    {'✓' if low_harm_pass else '✗'} ({diff_low.mean():+.2f}%p)")
    logger.info(f"  Primary 99% CI 상한 ≤ 0 (α=0.01 decision): {'✓' if primary_ci_99_pass else '✗'} ({boot['ci_hi_99']:+.2f}%p)")
    logger.info(f"  Primary 95% CI 상한 ≤ 0 (참고만):           {'✓' if primary_ci_95_pass else '✗'} ({boot['ci_hi_95']:+.2f}%p)")
    logger.info(f"  Primary practical Δ ≤ -1.0%p: {'✓' if primary_practical_pass else '✗'} ({diff_overall.mean():+.2f}%p)")

    if not low_harm_pass:
        verdict = "FAIL (🔴 Hard gate Δ_low > 0)"
        next_action = "A.5 escalation (image embedding, CLIP/ResNet)"
    elif primary_ci_99_pass and primary_practical_pass:
        verdict = "PASS (Phase 3 cold shadow 진입 후보, α=0.01 operationalized)"
        next_action = "운영 채택 후보 / A.5 진입 불필요"
    elif (-1.0 < diff_overall.mean() <= -0.3) and low_harm_pass:
        verdict = "BORDERLINE (소폭 개선 -1.0 < Δ ≤ -0.3%p)"
        next_action = "A.5 escalation"
    elif diff_overall.mean() > -0.3:
        verdict = "FAIL (Δ > -0.3%p, 개선 미달)"
        next_action = "A.5 escalation"
    else:
        verdict = "BORDERLINE (Primary 99% CI 미달, α=0.01)"
        next_action = "A.5 escalation"

    logger.info(f"\n  → 판정: {verdict}")
    logger.info(f"  → 다음 단계: {next_action}")

    summary = {
        "n_seeds": len(seed_results),
        "n_skipped": skipped,
        "metrics_100seed_mean": {
            "baseline_overall": float(base_overall.mean()),
            "a4_overall": float(a4_overall.mean()),
            "diff_overall_mean": float(diff_overall.mean()),
            "diff_overall_std": float(diff_overall.std()),
            "diff_low_mean": float(diff_low.mean()),
            "diff_low_std": float(diff_low.std()),
            "diff_high_mean": float(diff_high.mean()),
            "diff_newly_mean": float(diff_newly.mean()),
        },
        "seed_level_low_violation": {
            "n_violations": low_violations,
            "n_total": n_low_seeds,
            "rate_pct": 100 * low_violations / n_low_seeds,
        },
        "cluster_bootstrap_seed0": boot,
        "verdict": verdict,
        "next_action": next_action,
        "primary_pass": {
            "hard_gate_low_le_0": bool(low_harm_pass),
            "ci_99_upper_le_0_decision": bool(primary_ci_99_pass),
            "ci_95_upper_le_0_reference": bool(primary_ci_95_pass),
            "practical_le_neg1": bool(primary_practical_pass),
        },
        "freeze_spec": {
            "embedding_model": EMB_MODEL_NAME,
            "embedding_dim": int(emb_full.shape[1]),
            "pca_k": PCA_K,
            "pca_seed": PCA_SEED,
        },
    }

    out = RESULTS / "feature_track_axis_a4.json"
    RESULTS.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
