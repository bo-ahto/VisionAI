"""Track 3 PR13 — TRUE_homonym 38명 entity_id 분리 + Dual eval.

Codex 권장 옵션 B:
1. TRUE_homonym 38명만 자동 분리 (보조 entity는 #2, #3...)
2. Cold-start eval 2축:
   - artist_name 기준 (기존)
   - entity 분리 후 기준 (신규)
3. Platform별 (Artsy/Saatchi/Artue) breakdown

설계:
- TRUE_homonym 식별: 한글명 group → 보조 entity 중 ≥3건 + 가격 CV >0.5
- 분리 방식: 메인 entity = 한글명 그대로 / 보조 = 한글명#suffix
- artist_works_log 재계산 (train fold 기준)
- LAD Cold 모델 (PR7 ALL features) 5-fold GroupKFold OOF

평가 비교:
- V1: artist_name_ko (기존 — 동명이인 합쳐서 학습)
- V2: artist_id_split (분리 후)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GroupKFold

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1.parquet"  # parquet (모든 컬럼 보존)
OUT_PATH = REPO / "data" / "track3_pr13_homonym_results.json"

PRICE_COL = "price_krw_unified"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"

BASE_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
BASE_CAT = ["medium_category", "support_category", "orientation"]
CAT_ALL = BASE_CAT + ["medium_ho_bucket"]
SEED = 42
N_MIN_SECONDARY = 3  # 보조 entity ≥N건이면 분리 대상


def identify_true_homonyms(df, conservative=False):
    """TRUE_homonym 식별 + 분리 mapping.

    conservative=False (V2):
      - TRUE_homonym 38명 → 모든 보조 entity 분리 (singleton도 분리)
    conservative=True (V3):
      - 동일 TRUE_homonym pool에서
      - 보조 entity ≥3건 AND non-Artue dominant 인 것만 분리
      - 나머지(singleton, Artue dominant)는 메인과 merge (= 한글명 유지)
    """
    homonym_map = {}
    homonym_artists = []

    for name, group in df.groupby("artist_name_ko"):
        entities = group.groupby("artist_entity_id_raw").agg(
            n=("artist_name_raw", "size"),
            median_price=(PRICE_COL, "median"),
            artue_share=(SOURCE_COL, lambda s: (s == "artue").mean()),
        ).reset_index().sort_values("n", ascending=False)

        if len(entities) <= 1:
            continue

        secondary_multi = entities.iloc[1:][entities.iloc[1:]["n"] >= N_MIN_SECONDARY]
        prices = entities["median_price"].dropna()
        cv = float(prices.std() / max(prices.mean(), 1)) if len(prices) >= 2 else 0.0

        if len(secondary_multi) >= 1 and cv > 0.5:
            homonym_artists.append(name)
            split_counter = 1  # 분리될 entity 번호
            for i, (_, row) in enumerate(entities.iterrows()):
                eid = row["artist_entity_id_raw"]
                if i == 0:
                    homonym_map[(name, eid)] = name  # 메인
                    continue
                # 보조 entity
                if conservative:
                    # V3 기준: ≥3건 AND Artue dominant 아님(<0.5)
                    if row["n"] >= N_MIN_SECONDARY and row["artue_share"] < 0.5:
                        split_counter += 1
                        homonym_map[(name, eid)] = f"{name}#{split_counter}"
                    else:
                        # singleton or Artue 우세 → 메인과 merge
                        homonym_map[(name, eid)] = name
                else:
                    # V2 기준: 모두 분리
                    homonym_map[(name, eid)] = f"{name}#{i+1}"

    return homonym_artists, homonym_map


def apply_split(df, homonym_map):
    """artist_id_split 컬럼 추가."""
    def get_split_id(row):
        key = (row["artist_name_ko"], row["artist_entity_id_raw"])
        if key in homonym_map:
            return homonym_map[key]
        return row["artist_name_ko"]
    df = df.copy()
    df["artist_id_split"] = df.apply(get_split_id, axis=1)
    return df


def make_features(df, train_counts, artist_col):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[artist_col].map(train_counts).fillna(0))
    return df


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)),
            "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50))}


def evaluate_cold(df, artist_col, name):
    """Cold LAD 5-fold GroupKFold (작가 기준 분리)."""
    features = BASE_FEATURES + ["medium_ho_bucket", "artist_works_log", "aspect_ratio"]
    cat_cols = CAT_ALL

    gkf = GroupKFold(n_splits=5)
    fold_results = []
    oof_pred = np.full(len(df), np.nan)

    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(df, groups=df[artist_col])):
        tr_df = df.iloc[train_idx]
        te_df = df.iloc[test_idx]

        # train 작가 작품수
        train_counts = tr_df[artist_col].value_counts().to_dict()
        tr_feat = make_features(tr_df, train_counts, artist_col)
        te_feat = make_features(te_df, train_counts, artist_col)

        # LAD
        cat = [c for c in features if c in cat_cols]
        num = [c for c in features if c not in cat_cols]
        preprocess = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
            ("num", StandardScaler(), num),
        ])
        model = Pipeline([("prep", preprocess),
                          ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])
        model.fit(tr_feat[features], tr_feat[TARGET].values)
        pred = model.predict(te_feat[features])

        oof_pred[test_idx] = pred
        m = compute_metrics(te_feat[TARGET].values, pred)
        m["fold"] = fold_idx
        m["n_train_artists"] = int(tr_df[artist_col].nunique())
        m["n_test_artists"] = int(te_df[artist_col].nunique())
        fold_results.append(m)
        logger.info(f"  {name} fold {fold_idx}: med_APE={m['median_ape']:.4f} "
                    f"(train artists {m['n_train_artists']}, test {m['n_test_artists']})")

    # Source breakdown
    sources = df[SOURCE_COL].values
    y_true = df[TARGET].values
    source_breakdown = {}
    for src in ["artsy", "saatchi", "artue"]:
        mask = sources == src
        if mask.sum() > 0:
            source_breakdown[src] = compute_metrics(y_true[mask], oof_pred[mask])

    return {
        "name": name,
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "source_breakdown": source_breakdown,
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR13 — TRUE_homonym 38명 entity_id 분리 + Dual eval")
    logger.info("=" * 70)

    df = pd.read_parquet(DATA_PATH)
    df = df[df["is_outlier"] == 0].reset_index(drop=True)
    logger.info(f"전체 데이터: {len(df):,} 작품 / {df['artist_name_ko'].nunique():,} 작가")

    # Step 1: V2 (모두 분리) + V3 (보수적: ≥3건 AND non-Artue) mapping 동시 생성
    homonym_artists, homonym_map_v2 = identify_true_homonyms(df, conservative=False)
    _, homonym_map_v3 = identify_true_homonyms(df, conservative=True)
    logger.info(f"\nTRUE_homonym 식별: {len(homonym_artists)} 명")
    logger.info(f"  V2 (모두 분리) → entity 매핑 {len(homonym_map_v2)} / 분리 결과 {len({v for v in homonym_map_v2.values() if '#' in v})} 보조 ID")
    logger.info(f"  V3 (보수적)   → entity 매핑 {len(homonym_map_v3)} / 분리 결과 {len({v for v in homonym_map_v3.values() if '#' in v})} 보조 ID")

    # V3 분리 sample
    print()
    print("=" * 80)
    print("V3 보수적 분리 — 한글명별 split 결과 (≥3건 & non-Artue만 분리)")
    print("=" * 80)
    for name in homonym_artists[:8]:
        v3_splits = sorted({v for k, v in homonym_map_v3.items() if k[0] == name})
        n_entities = len([k for k in homonym_map_v3 if k[0] == name])
        print(f"  {name:<10} entities={n_entities:>2} → split IDs: {v3_splits}")

    # Step 2: Apply
    df_v2 = apply_split(df, homonym_map_v2)
    df_v3 = apply_split(df, homonym_map_v3)
    n_unique_v1 = df["artist_name_ko"].nunique()
    n_unique_v2 = df_v2["artist_id_split"].nunique()
    n_unique_v3 = df_v3["artist_id_split"].nunique()
    logger.info(f"\n작가 수: V1={n_unique_v1} / V2={n_unique_v2} (+{n_unique_v2-n_unique_v1}) / V3={n_unique_v3} (+{n_unique_v3-n_unique_v1})")

    # Step 3: Dual eval (V1, V2, V3)
    logger.info("\n" + "=" * 70)
    logger.info("V1: artist_name_ko (기존)")
    logger.info("=" * 70)
    res_v1 = evaluate_cold(df, "artist_name_ko", "V1_baseline")

    logger.info("\n" + "=" * 70)
    logger.info("V2: 모든 보조 entity 분리")
    logger.info("=" * 70)
    res_v2 = evaluate_cold(df_v2, "artist_id_split", "V2_full_split")

    logger.info("\n" + "=" * 70)
    logger.info("V3: 보수적 분리 (≥3건 & non-Artue만)")
    logger.info("=" * 70)
    res_v3 = evaluate_cold(df_v3, "artist_id_split", "V3_conservative_split")

    # 출력
    print()
    print("=" * 80)
    print("📊 PR13 — Homonym 분리 효과 (Cold LAD 5-fold GroupKFold OOF)")
    print("=" * 80)
    print()
    print(f"{'Variant':<32} {'med_APE':>9} {'MAPE':>8} {'W30':>7} {'vs V1':>10}")
    print("-" * 72)
    v1m, v2m, v3m = res_v1["median"], res_v2["median"], res_v3["median"]
    print(f"{'V1: artist_name_ko (기존)':<32} {v1m['median_ape']:>9.4f} {v1m['mape']:>8.4f} {v1m['within_30pct']:>7.4f}     —")
    d2 = v2m["median_ape"] - v1m["median_ape"]
    d3 = v3m["median_ape"] - v1m["median_ape"]
    print(f"{'V2: 모두 분리':<32} {v2m['median_ape']:>9.4f} {v2m['mape']:>8.4f} {v2m['within_30pct']:>7.4f}  {d2:+.4f}")
    print(f"{'V3: 보수적 (≥3건 & non-Artue)':<32} {v3m['median_ape']:>9.4f} {v3m['mape']:>8.4f} {v3m['within_30pct']:>7.4f}  {d3:+.4f}")

    print()
    print("[Source breakdown] — V1 vs V2 vs V3 (med_APE)")
    print(f"  {'Source':<8} {'V1':>8} {'V2':>8} {'V3':>8} {'V3-V1':>9}")
    for src in ["artsy", "saatchi", "artue"]:
        v1s = res_v1["source_breakdown"].get(src, {})
        v2s = res_v2["source_breakdown"].get(src, {})
        v3s = res_v3["source_breakdown"].get(src, {})
        if v1s and v2s and v3s:
            d31 = v3s["median_ape"] - v1s["median_ape"]
            print(f"  {src:<8} {v1s['median_ape']:>8.4f} {v2s['median_ape']:>8.4f} "
                  f"{v3s['median_ape']:>8.4f} {d31:>+9.4f}")

    # Save
    output = {
        "homonym_artists": homonym_artists,
        "homonym_map_v2_count": len(homonym_map_v2),
        "homonym_map_v3_count": len(homonym_map_v3),
        "n_unique_v1": int(n_unique_v1),
        "n_unique_v2": int(n_unique_v2),
        "n_unique_v3": int(n_unique_v3),
        "V1": res_v1, "V2": res_v2, "V3": res_v3,
        "delta_v2_v1": float(d2),
        "delta_v3_v1": float(d3),
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
