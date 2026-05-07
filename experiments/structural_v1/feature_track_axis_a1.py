"""Feature Track Axis A.1 — Cheap Categorical (4종) cold-start LAO confirmatory.

사전등록 freeze: docs/feature_track_axis_a1_prereg_20260507.md (2026-05-07)
- Features: F4 + spline (운영 baseline) + A.1 4종
  * category one-hot drop "Painting" (13 columns)
  * attribution_class one-hot drop "Unique" (3 columns)
  * gallery_name target encoding (leakage-safe 5-fold OOF, smoothing α=10)
  * gallery_cities multi-hot top-5 (Seoul / Busan / Pohang / Daegu / Incheon, casefold parsing)
- Estimator: HuberRegressor(epsilon=1.35, alpha=1e-4) — 운영 모델 동일
- Primary: Δ ≤ -1.0%p AND Cluster bootstrap CI 상한 ≤ 0
- 🔴 Hard gate: Δ_low ≤ 0%p (즉시 FAIL trigger)
- LAO Secondary Holm m=3: low / mid-high / newly-warm (sparse-warm 제외 — LAO 정의상 측정 불가)
- 100-seed LAO + cluster bootstrap n=2000
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage4_full.parquet"
RESULTS = Path(__file__).parent / "results"
LOW_PRICE_KRW = 5_000_000
N_SEEDS = 100
N_BOOT = 2000
TARGET_ENCODE_ALPHA = 10
TARGET_ENCODE_FOLDS = 5
TARGET_ENCODE_SEED = 42
TOP5_CITIES = ["seoul", "busan", "pohang", "daegu", "incheon"]
DROP_CATEGORY = "Painting"
DROP_ATTRIBUTION = "Unique"

STAGE3 = ROOT / "data" / "curated" / "stage3_1000x100.parquet"


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


def parse_cities(s):
    """Parse comma-separated cities → set of casefolded names."""
    if pd.isna(s):
        return set()
    return {c.strip().casefold() for c in str(s).split(",") if c.strip()}


def gallery_cities_multihot(df):
    """Multi-hot encoding for top-5 cities (prereg §2.1.b)."""
    out = np.zeros((len(df), len(TOP5_CITIES)), dtype=float)
    for row_idx, raw in enumerate(df["gallery_cities"].values):
        cities = parse_cities(raw)
        for ci, city in enumerate(TOP5_CITIES):
            if city in cities:
                out[row_idx, ci] = 1.0
    return out


def categorical_one_hot(df_tr, df_te, col, drop_level):
    """One-hot encoding with explicit drop_first (drop_level = 가장 빈도 높음)."""
    levels = sorted([lv for lv in df_tr[col].dropna().unique().tolist() if lv != drop_level])
    out_tr = np.zeros((len(df_tr), len(levels)))
    out_te = np.zeros((len(df_te), len(levels)))
    for i, lv in enumerate(levels):
        out_tr[:, i] = (df_tr[col].values == lv).astype(float)
        out_te[:, i] = (df_te[col].values == lv).astype(float)
    return out_tr, out_te, levels


def gallery_target_encode_oof(df_tr, target_values, alpha=TARGET_ENCODE_ALPHA, n_splits=TARGET_ENCODE_FOLDS, seed=TARGET_ENCODE_SEED):
    """Leakage-safe 5-fold OOF target encoding for gallery_name (prereg §2.1.b).

    smoothing formula: enc[g] = (n_g · mean_g + α · global_mean) / (n_g + α)
    Train OOF: row-level KFold(n_splits=5, shuffle=True, random_state=42)
    Returns: encoded_train (length len(df_tr)), full_encoder dict (gallery → smoothed encoding)
    """
    df_tr = df_tr.reset_index(drop=True)
    target_values = np.asarray(target_values)
    global_mean = float(np.mean(target_values))
    encoded_train = np.full(len(df_tr), global_mean)

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr_idx, val_idx in kf.split(df_tr):
        fold_target = target_values[tr_idx]
        fold_galleries = df_tr.iloc[tr_idx]["gallery_name"].values
        # Smoothing per gallery in fold-train
        gallery_to_target = {}
        for g, t in zip(fold_galleries, fold_target):
            gallery_to_target.setdefault(g, []).append(t)
        gallery_enc = {}
        for g, vals in gallery_to_target.items():
            n_g = len(vals)
            mean_g = float(np.mean(vals))
            gallery_enc[g] = (n_g * mean_g + alpha * global_mean) / (n_g + alpha)
        # Apply to val fold
        for vi, gi in zip(val_idx, df_tr.iloc[val_idx]["gallery_name"].values):
            encoded_train[vi] = gallery_enc.get(gi, global_mean)

    # Full train encoder (for test inference)
    full_gallery_to_target = {}
    for g, t in zip(df_tr["gallery_name"].values, target_values):
        full_gallery_to_target.setdefault(g, []).append(t)
    full_encoder = {}
    for g, vals in full_gallery_to_target.items():
        n_g = len(vals)
        mean_g = float(np.mean(vals))
        full_encoder[g] = (n_g * mean_g + alpha * global_mean) / (n_g + alpha)

    return encoded_train, full_encoder, global_mean


def apply_gallery_encoder(df_te, full_encoder, global_mean):
    """Apply full-train smoothing-adjusted encoder to test (unseen → global_mean)."""
    out = np.full(len(df_te), global_mean)
    for i, g in enumerate(df_te["gallery_name"].values):
        out[i] = full_encoder.get(g, global_mean)
    return out


def build_a1_features(df_tr, df_te, y_tr):
    """A.1 spec features = F4 + spline + 4 cheap categoricals.

    Returns: Xtr_baseline, Xte_baseline (F4+spline only), Xtr_a1, Xte_a1 (F4+spline + A.1).
    """
    # F4 + spline (baseline)
    feat_tr_base, knots = build_f4_spline(df_tr)
    feat_te_base, _ = build_f4_spline(df_te, knots=knots)
    Xtr_base = feat_tr_base.values
    Xte_base = feat_te_base.values

    # category one-hot (drop "Painting")
    cat_tr, cat_te, _ = categorical_one_hot(df_tr, df_te, "category", DROP_CATEGORY)

    # attribution_class one-hot (drop "Unique")
    att_tr, att_te, _ = categorical_one_hot(df_tr, df_te, "attribution_class", DROP_ATTRIBUTION)

    # gallery_name target encoding (leakage-safe OOF on train)
    gal_tr, full_enc, gmean = gallery_target_encode_oof(df_tr, y_tr)
    gal_te = apply_gallery_encoder(df_te, full_enc, gmean)

    # gallery_cities multi-hot top-5
    cit_tr = gallery_cities_multihot(df_tr)
    cit_te = gallery_cities_multihot(df_te)

    Xtr_a1 = np.column_stack([Xtr_base, cat_tr, att_tr, gal_tr.reshape(-1, 1), cit_tr])
    Xte_a1 = np.column_stack([Xte_base, cat_te, att_te, gal_te.reshape(-1, 1), cit_te])
    return Xtr_base, Xte_base, Xtr_a1, Xte_a1


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


def eval_one_seed(df, y, seed, stage3_artists):
    train_mask, test_mask = lao_split(df, seed)
    df_tr = df[train_mask].reset_index(drop=True)
    df_te = df[test_mask].reset_index(drop=True)
    if len(df_tr) < 50 or len(df_te) < 5:
        return None

    y_tr = y[train_mask].values.astype(float)
    y_te = y[test_mask].values.astype(float)

    Xtr_base, Xte_base, Xtr_a1, Xte_a1 = build_a1_features(df_tr, df_te, y_tr)

    pred_baseline = fit_huber(Xtr_base, y_tr, Xte_base)
    pred_a1 = fit_huber(Xtr_a1, y_tr, Xte_a1)

    is_low_te = (df_te["price_krw"].values < LOW_PRICE_KRW)
    is_newly_warm_te = ~df_te["artist_slug"].isin(stage3_artists).values

    return {
        "seed": seed,
        "n_test": int(len(y_te)),
        "n_test_low": int(is_low_te.sum()),
        "n_test_high": int((~is_low_te).sum()),
        "n_test_newly_warm": int(is_newly_warm_te.sum()),
        "baseline_overall": mdape_log(y_te, pred_baseline),
        "a1_overall": mdape_log(y_te, pred_a1),
        "baseline_low": mdape_log(y_te[is_low_te], pred_baseline[is_low_te]) if is_low_te.sum() else None,
        "a1_low": mdape_log(y_te[is_low_te], pred_a1[is_low_te]) if is_low_te.sum() else None,
        "baseline_high": mdape_log(y_te[~is_low_te], pred_baseline[~is_low_te]) if (~is_low_te).sum() else None,
        "a1_high": mdape_log(y_te[~is_low_te], pred_a1[~is_low_te]) if (~is_low_te).sum() else None,
        "baseline_newly": mdape_log(y_te[is_newly_warm_te], pred_baseline[is_newly_warm_te]) if is_newly_warm_te.sum() else None,
        "a1_newly": mdape_log(y_te[is_newly_warm_te], pred_a1[is_newly_warm_te]) if is_newly_warm_te.sum() else None,
        "test_artists": df_te["artist_slug"].values.tolist(),
        "y_te": y_te.tolist(),
        "pred_baseline": pred_baseline.tolist(),
        "pred_a1": pred_a1.tolist(),
    }


def cluster_bootstrap_diff(yte, pred_a, pred_b, test_artists, n_boot=N_BOOT, seed=42):
    """Proper cluster bootstrap: 중복 draw 시 cluster 의 모든 indices 가 그만큼 여러 번 들어감 (코덱스 P0 fix).

    이전 구현의 np.isin() 은 중복 draw 를 collapse 해서 진짜 bootstrap 가중치가 반영 X.
    본 구현 = artist 별 indices 사전 매핑 후 sample 별 concatenate (with replicas).
    Returns 95% AND 99% CI (코덱스 P0 — α=0.01 Bonferroni 5 step operationalization).
    """
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
    logger.info("Feature Track Axis A.1 — Cheap Categorical (4종) cold-start LAO")
    logger.info("=" * 80)
    logger.info(f"Source: {DATA.relative_to(ROOT)} ({len(df):,} 작품)")
    logger.info(f"Stage 3 cohort artists (newly-warm 정의용): {len(stage3_artists)}")
    logger.info(f"Drop levels: category='{DROP_CATEGORY}' / attribution_class='{DROP_ATTRIBUTION}'")
    logger.info(f"Top-5 cities (multi-hot): {TOP5_CITIES}")
    logger.info(f"Target encoding: smoothing α={TARGET_ENCODE_ALPHA}, KFold={TARGET_ENCODE_FOLDS} seed={TARGET_ENCODE_SEED}")

    seed_results = []
    skipped = 0
    for s in range(N_SEEDS):
        try:
            r = eval_one_seed(df, y, s, stage3_artists)
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

    # Aggregate
    def agg(key):
        vals = [r[key] for r in seed_results if r.get(key) is not None]
        return np.array(vals)

    base_overall = agg("baseline_overall")
    a1_overall = agg("a1_overall")
    base_low = agg("baseline_low")
    a1_low = agg("a1_low")
    base_high = agg("baseline_high")
    a1_high = agg("a1_high")
    base_newly = agg("baseline_newly")
    a1_newly = agg("a1_newly")

    diff_overall = a1_overall - base_overall
    diff_low = np.array([r["a1_low"] - r["baseline_low"] for r in seed_results if r.get("baseline_low") is not None and r.get("a1_low") is not None])
    diff_high = np.array([r["a1_high"] - r["baseline_high"] for r in seed_results if r.get("baseline_high") is not None and r.get("a1_high") is not None])
    diff_newly = np.array([r["a1_newly"] - r["baseline_newly"] for r in seed_results if r.get("baseline_newly") is not None and r.get("a1_newly") is not None])

    logger.info(f"\n{'metric':>22} {'baseline':>10} {'a1':>10} {'Δ (mean)':>12} {'n_seeds':>8}")
    logger.info(f"{'overall MdAPE':>22} {base_overall.mean():>8.2f}% {a1_overall.mean():>8.2f}% {diff_overall.mean():>+9.2f}%p {len(diff_overall):>5}")
    logger.info(f"{'low MdAPE':>22} {base_low.mean():>8.2f}% {a1_low.mean():>8.2f}% {diff_low.mean():>+9.2f}%p {len(diff_low):>5}")
    logger.info(f"{'mid/high MdAPE':>22} {base_high.mean():>8.2f}% {a1_high.mean():>8.2f}% {diff_high.mean():>+9.2f}%p {len(diff_high):>5}")
    logger.info(f"{'newly-warm MdAPE':>22} {base_newly.mean():>8.2f}% {a1_newly.mean():>8.2f}% {diff_newly.mean():>+9.2f}%p {len(diff_newly):>5}")

    # Seed-level low violation rate (6B 패턴 — hard gate point estimate artifact 검증)
    low_violations = int((diff_low > 0).sum())
    n_low_seeds = len(diff_low)
    logger.info(f"\n[Seed-level low violation rate] {low_violations}/{n_low_seeds} = {100*low_violations/n_low_seeds:.1f}%")

    # Primary cluster bootstrap (rep seed=0)
    rep = seed_results[0]
    boot = cluster_bootstrap_diff(rep["y_te"], rep["pred_a1"], rep["pred_baseline"], rep["test_artists"])
    logger.info(f"\n[Primary cluster bootstrap (rep seed=0, n={N_BOOT}, 진짜 cluster bootstrap — 코덱스 P0 fix)]")
    logger.info(f"  Δ overall (a1 - baseline) mean: {boot['mean']:+.2f}%p")
    logger.info(f"  95% CI: [{boot['ci_lo_95']:+.2f}, {boot['ci_hi_95']:+.2f}]")
    logger.info(f"  99% CI (α=0.01, Bonferroni 5 step): [{boot['ci_lo_99']:+.2f}, {boot['ci_hi_99']:+.2f}]")
    logger.info(f"  P(diff ≥ 0) = {boot['p_1sided']:.4f}")

    # 사전등록 §3 PASS/BORDERLINE/FAIL 판정 (α=0.01 → 99% CI 사용, 코덱스 P0 fix)
    primary_ci_99_pass = boot["ci_hi_99"] <= 0
    primary_ci_95_pass = boot["ci_hi_95"] <= 0  # 보고만, decision 사용 X
    primary_practical_pass = diff_overall.mean() <= -1.0
    low_harm_pass = diff_low.mean() <= 0  # Hard gate: Δ_low ≤ 0%p (point estimate)

    logger.info(f"\n[PASS/BORDERLINE/FAIL 판정 (사전등록 §3 + α=0.01 operationalization)]")
    logger.info(f"  🔴 Hard gate Δ_low ≤ 0%p:    {'✓' if low_harm_pass else '✗'} ({diff_low.mean():+.2f}%p)")
    logger.info(f"  Primary 99% CI 상한 ≤ 0 (α=0.01 decision): {'✓' if primary_ci_99_pass else '✗'} ({boot['ci_hi_99']:+.2f}%p)")
    logger.info(f"  Primary 95% CI 상한 ≤ 0 (참고만):           {'✓' if primary_ci_95_pass else '✗'} ({boot['ci_hi_95']:+.2f}%p)")
    logger.info(f"  Primary practical Δ ≤ -1.0%p: {'✓' if primary_practical_pass else '✗'} ({diff_overall.mean():+.2f}%p)")

    # α=0.01 (Bonferroni 5 step) operationalization: 99% CI 가 decision rule
    if not low_harm_pass:
        verdict = "FAIL (🔴 Hard gate Δ_low > 0)"
        next_action = "A.2 escalation (artist popularity 4종, 시점 정합성 검증 후)"
    elif primary_ci_99_pass and primary_practical_pass:
        verdict = "PASS (Phase 3 cold shadow 진입 후보, α=0.01 operationalized)"
        next_action = "운영 채택 후보 / A.2 진입 불필요"
    elif (-1.0 < diff_overall.mean() <= -0.3) and low_harm_pass:
        verdict = "BORDERLINE (소폭 개선 -1.0 < Δ ≤ -0.3%p)"
        next_action = "A.2 escalation"
    elif diff_overall.mean() > -0.3:
        verdict = "FAIL (Δ > -0.3%p, 개선 미달)"
        next_action = "A.2 escalation"
    else:
        verdict = "BORDERLINE (Primary 99% CI 미달, α=0.01)"
        next_action = "A.2 escalation"

    logger.info(f"\n  → 판정: {verdict}")
    logger.info(f"  → 다음 단계: {next_action}")

    summary = {
        "n_seeds": len(seed_results),
        "n_skipped": skipped,
        "metrics_100seed_mean": {
            "baseline_overall": float(base_overall.mean()),
            "a1_overall": float(a1_overall.mean()),
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
            "drop_category": DROP_CATEGORY,
            "drop_attribution": DROP_ATTRIBUTION,
            "top5_cities": TOP5_CITIES,
            "target_encode_alpha": TARGET_ENCODE_ALPHA,
            "target_encode_folds": TARGET_ENCODE_FOLDS,
            "target_encode_seed": TARGET_ENCODE_SEED,
        },
    }

    out = RESULTS / "feature_track_axis_a1.json"
    RESULTS.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
