"""Track 3 PR5 — 가격 데이터 source bias audit.

목적: Artsy/Saatchi/Artue 간 listing price 정책 차이 정량화.
     (Artsy 갤러리 마크업 vs Saatchi 직거래 vs Artue 등)

설계: 동일 특성 작품을 source 별로 비교
  1. 매체/크기/orientation 별 source 가격 분포 비교
  2. 호수별 (estimated_ho) source 가격 분포 비교
  3. 같은 작가 작품이 두 source에 모두 있는지 (cross-source overlap) 검증
  4. Linear regression: ln_price ~ source (control: medium/area/ho)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
OUT_PATH = REPO / "data" / "track3_pr5_source_bias_results.json"

TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"
ARTIST_COL = "artist_name_ko"
SOURCE_COL = "source_platform"


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR5 — Source bias audit")
    logger.info("=" * 70)

    df = pd.read_csv(DATA_PATH)
    logger.info(f"Dataset: {len(df):,} rows / {df[SOURCE_COL].nunique()} sources")

    # 1. Source 별 가격 분포
    logger.info("\n--- [1] Source 별 가격 분포 ---")
    src_stats = df.groupby(SOURCE_COL)[PRICE_COL].agg(
        ["count", "median", "mean", lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)]
    ).rename(columns={"<lambda_0>": "q25", "<lambda_1>": "q75"})
    logger.info(f"\n{src_stats}")

    # 2. Medium 별 source 가격 비교
    logger.info("\n--- [2] Medium × Source 가격 (median) ---")
    pivot = df.pivot_table(index="medium_category", columns=SOURCE_COL,
                            values=PRICE_COL, aggfunc="median")
    logger.info(f"\n{pivot.fillna(0).astype(int).to_string()}")

    # 3. 호수 bucket × source
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"])
    logger.info("\n--- [3] 호수 bucket × Source 가격 (median) ---")
    ho_pivot = df.pivot_table(index="ho_bucket", columns=SOURCE_COL,
                                values=PRICE_COL, aggfunc="median", observed=False)
    logger.info(f"\n{ho_pivot.fillna(0).astype(int).to_string()}")

    # 4. Cross-source artist overlap
    logger.info("\n--- [4] Cross-source artist overlap ---")
    artist_sources = df.groupby(ARTIST_COL)[SOURCE_COL].apply(set)
    multi_src_artists = artist_sources[artist_sources.apply(len) > 1]
    logger.info(f"  Artists in multiple sources: {len(multi_src_artists):,} / "
                f"{len(artist_sources):,} ({100*len(multi_src_artists)/len(artist_sources):.1f}%)")
    overlap_counts = multi_src_artists.apply(lambda s: tuple(sorted(s))).value_counts()
    logger.info(f"\n{overlap_counts}")

    # 5. Same-artist cross-source price comparison
    logger.info("\n--- [5] 같은 작가 cross-source 가격 차이 ---")
    same_artist_diff = []
    for artist in multi_src_artists.index[:50]:  # top 50 for speed
        sub = df[df[ARTIST_COL] == artist]
        if sub[SOURCE_COL].nunique() < 2:
            continue
        # median ln_price per source
        ln_meds = sub.groupby(SOURCE_COL)[TARGET].median().to_dict()
        srcs = sorted(ln_meds.keys())
        for i in range(len(srcs)):
            for j in range(i+1, len(srcs)):
                same_artist_diff.append({
                    "artist": artist,
                    "src1": srcs[i],
                    "src2": srcs[j],
                    "ln_diff": float(ln_meds[srcs[i]] - ln_meds[srcs[j]]),
                    "ratio": float(np.exp(ln_meds[srcs[i]] - ln_meds[srcs[j]])),
                })

    if same_artist_diff:
        comp_df = pd.DataFrame(same_artist_diff)
        pair_summary = comp_df.groupby(["src1", "src2"]).agg(
            n=("ratio", "count"),
            median_ratio=("ratio", "median"),
            mean_ratio=("ratio", "mean"),
        ).reset_index()
        logger.info(f"\n{pair_summary.to_string()}")
    else:
        pair_summary = pd.DataFrame()

    # 6. Linear regression with controls (medium/log_area/has_depth + source FE)
    logger.info("\n--- [6] Regression: ln_price ~ source (controls) ---")
    features = ["medium_category", "support_category", "log_area", "estimated_ho",
                "has_depth", "orientation"]
    cat_cols = ["medium_category", "support_category", "orientation"]
    num_cols = ["log_area", "estimated_ho", "has_depth"]

    # Source dummies (saatchi reference)
    df_reg = df.copy()
    for src in ["artsy", "artue"]:
        df_reg[f"src_{src}"] = (df_reg[SOURCE_COL] == src).astype(int)

    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), cat_cols),
        ("num", StandardScaler(), num_cols),
        ("src", "passthrough", ["src_artsy", "src_artue"]),
    ])

    pipe = Pipeline([("prep", preprocess), ("est", LinearRegression())])
    X = df_reg[features + ["src_artsy", "src_artue"]]
    y = df_reg[TARGET].values
    pipe.fit(X, y)

    # 마지막 2개 coefficient = source dummies
    coefs = pipe.named_steps["est"].coef_
    # Source coefficients are last 2 (after cat OneHot + scaled num)
    src_coefs = coefs[-2:]
    src_artsy_log = float(src_coefs[0])
    src_artue_log = float(src_coefs[1])
    src_artsy_pct = (np.exp(src_artsy_log) - 1) * 100
    src_artue_pct = (np.exp(src_artue_log) - 1) * 100

    logger.info(f"  Saatchi (reference): 0 (baseline)")
    logger.info(f"  Artsy:   log coef = {src_artsy_log:+.3f}  → {src_artsy_pct:+.1f}% vs Saatchi (same features)")
    logger.info(f"  Artue:   log coef = {src_artue_log:+.3f}  → {src_artue_pct:+.1f}% vs Saatchi (same features)")

    # 결과 출력
    print()
    print("=" * 80)
    print("📊 PR5 — Source Bias Audit")
    print("=" * 80)
    print()
    print("[1] Source 가격 분포 (KRW)")
    print(src_stats.astype(int).to_string())
    print()
    print("[2] Cross-source artist overlap")
    print(f"  Multi-source artists: {len(multi_src_artists):,} / "
          f"{len(artist_sources):,} ({100*len(multi_src_artists)/len(artist_sources):.1f}%)")
    print()
    print("[3] Same-artist cross-source price 비율 (median)")
    if not pair_summary.empty:
        print(pair_summary.to_string(index=False))
    print()
    print("[4] Source effect on ln_price (controls: medium/support/log_area/ho/orientation/has_depth)")
    print(f"  Saatchi (baseline):  0")
    print(f"  Artsy:  {src_artsy_log:+.3f} log → {src_artsy_pct:+.1f}% (same features 대비)")
    print(f"  Artue:  {src_artue_log:+.3f} log → {src_artue_pct:+.1f}% (same features 대비)")

    print()
    print("📝 해석:")
    if abs(src_artsy_pct) > 30 or abs(src_artue_pct) > 30:
        print(f"  ⚠️ Source bias 크다 (>30% 차이). 운영 시 source 정보 입력 또는 calibration 필요.")
    elif abs(src_artsy_pct) > 10:
        print(f"  ⚠️ Source bias 중간 (10-30%). 가격 차이 caveat 명시 권장.")
    else:
        print(f"  ✓ Source bias 작음 (<10%). 운영 시 source 무관 적용 가능.")

    # Save
    output = {
        "source_stats": src_stats.to_dict(),
        "medium_x_source_median": pivot.fillna(0).to_dict(),
        "ho_bucket_x_source_median": ho_pivot.fillna(0).to_dict(),
        "multi_source_artists": int(len(multi_src_artists)),
        "total_artists": int(len(artist_sources)),
        "multi_source_pct": float(100*len(multi_src_artists)/len(artist_sources)),
        "overlap_pair_counts": {str(k): int(v) for k, v in overlap_counts.items()},
        "same_artist_cross_source_pairs": int(len(same_artist_diff)),
        "pair_summary": pair_summary.to_dict("records") if not pair_summary.empty else [],
        "regression": {
            "saatchi_baseline": 0,
            "artsy_log_coef": src_artsy_log,
            "artue_log_coef": src_artue_log,
            "artsy_pct_vs_saatchi": float(src_artsy_pct),
            "artue_pct_vs_saatchi": float(src_artue_pct),
        },
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
