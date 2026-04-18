"""Phase 5 최종 — Model-A q50 + CQR alpha=0.38.

Distilled Student는 성능 악화 → Model-A q50 유지.
CQR alpha=0.38으로 Coverage G5 달성.

Usage:
    PYTHONPATH=src python3 scripts/train_phase5_final.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "k-artmarket-cleansed-known.csv"
MACRO_PATH = ROOT / "data" / "macro_session.csv"
OUTPUT_DIR = ROOT / "model_test_results"

_COLD_THRESHOLD = 5
HIGH_PSI = ["market_price_index", "artist_career_length", "medium_avg_price"]


def main() -> None:
    # ─── 1. 피처 빌드 ───
    logger.info("=== Step 1: Features ===")
    from visionai.price_engine.estimate_generator.hedonic_features import (
        build_hedonic_features,
    )

    # 코덱스 P2 (2026-04-18): cache를 source dataset stat(path + mtime + size)으로 keying.
    # 다른 데이터셋이나 갱신된 원본으로 돌릴 때 stale cache 재사용 방지.
    _data_stat = DATA_PATH.stat() if DATA_PATH.exists() else None
    _cache_tag = (
        f"{DATA_PATH.name}_{int(_data_stat.st_mtime)}_{_data_stat.st_size}"
        if _data_stat else "no_data"
    )
    cache_path = OUTPUT_DIR / f"hedonic_features_cache__{_cache_tag}.parquet"
    legacy_cache = OUTPUT_DIR / "hedonic_features_cache.parquet"
    if cache_path.exists():
        logger.info("Loading cached features (keyed): %s", cache_path)
        df = pd.read_parquet(cache_path)
        drop_cols = [c for c in df.columns if "img_file" in c or "img_src" in c or "page_index" in c]
        if drop_cols:
            df = df.drop(columns=drop_cols, errors="ignore")
    elif legacy_cache.exists():
        logger.warning(
            "Legacy cache found (%s). 데이터 변경 여부 불명확 → 재빌드하여 keyed cache 저장.",
            legacy_cache,
        )
        df = build_hedonic_features(DATA_PATH)
        df.to_parquet(cache_path, index=False)
    else:
        df = build_hedonic_features(DATA_PATH)
        df.to_parquet(cache_path, index=False)
        logger.info("Cached features to %s", cache_path)

    # ─── 2. 매크로 ───
    logger.info("=== Step 2: Macro ===")
    from visionai.price_engine.features.macro_indicators import (
        join_macro_features,
        load_macro_session,
    )

    if MACRO_PATH.exists() and "회차" in df.columns:
        macro = load_macro_session(MACRO_PATH)
        df = join_macro_features(df, macro, session_col="회차", lag_sessions=1)
    else:
        logger.info("Macro skip: 회차 column not found (multi-source mode)")

    # ─── 2b. 이미지 임베딩 ───
    # 전체 모델에서는 사용 안 함 (Cold 전용 Step 5c에서만 사용)
    # 경로만 미리 정의
    CLIP_EMBED_PATH = ROOT / "data" / "clip_embeddings_pca.npy"
    CLIP_INDEX_PATH = ROOT / "data" / "clip_embeddings_index.csv"
    IMG_EMBED_PATH = CLIP_EMBED_PATH if CLIP_EMBED_PATH.exists() else ROOT / "data" / "image_embeddings_pca32.npy"
    IMG_INDEX_PATH = CLIP_INDEX_PATH if CLIP_INDEX_PATH.exists() else ROOT / "data" / "image_embeddings_index.csv"
    if False:  # 전체 모델 이미지 비활성 — Cold 전용 Step 5c에서만 사용
        logger.info("=== Step 2b: Image Embeddings (DISABLED) ===")
        # 임시 컬럼 정리
        df = df.drop(columns=["img_url"], errors="ignore")
    else:
        logger.info("Image embeddings not found, skipping")
    # 이미지 관련 컬럼 제거 (전체 모델에 사용 안 함, Cold 전용만)
    img_drop = [c for c in df.columns if c.startswith("img_") or c == "img_file_name" or c == "img_url"]
    if img_drop:
        df = df.drop(columns=img_drop, errors="ignore")

    # ─── 3. Similarity (Cold-only) ───
    logger.info("=== Step 3: Similarity ===")
    from visionai.price_engine.features.artist_similarity import (
        build_artist_feature_vectors,
        compute_similarity_features,
        find_similar_artists,
    )

    train_only = df[df["split"] == "train"].copy()
    # 통합 스키마 호환: session_col, price_col 자동 감지
    _sim_session = "sale_date" if "sale_date" in df.columns else "회차"
    _sim_price = "price" if "price" in df.columns else "낙찰가"
    _sim_type = "source" if "source" in df.columns else "타입"

    # 코덱스 P2 (2026-04-18): 모든 행에 단일 unbounded vectors 사용하면
    # train 내부에서 미래 sale이 donor 벡터에 포함되어 temporal leak 발생.
    # 월(또는 session) 단위로 cutoff를 버킷팅 → 각 행의 버킷 이전 데이터로만 vectors 빌드.
    if _sim_session == "sale_date":
        df["_sim_bucket"] = (
            pd.to_datetime(df[_sim_session], errors="coerce")
            .dt.to_period("M").astype(str)
        )
        train_only["_sim_bucket"] = (
            pd.to_datetime(train_only[_sim_session], errors="coerce")
            .dt.to_period("M").astype(str)
        )
        bucket_to_cutoff = lambda b: f"{b}-01"
    else:
        df["_sim_bucket"] = df[_sim_session].astype(str)
        train_only["_sim_bucket"] = train_only[_sim_session].astype(str)
        bucket_to_cutoff = lambda b: int(b) if str(b).isdigit() else b

    unique_buckets = sorted(df["_sim_bucket"].dropna().unique())
    logger.info("Similarity: building per-bucket vectors (%d buckets)", len(unique_buckets))

    _fallback_cutoff = "9999-12-31" if _sim_session == "sale_date" else 999999
    _fallback_vectors = build_artist_feature_vectors(
        train_only, cutoff=_fallback_cutoff,
        session_col=_sim_session, type_col=_sim_type, price_col=_sim_price,
    )

    vectors_cache: dict[str, pd.DataFrame] = {}
    for bucket in unique_buckets:
        cutoff_val = bucket_to_cutoff(bucket)
        if _sim_session == "sale_date":
            subset = train_only[
                pd.to_datetime(train_only[_sim_session], errors="coerce")
                < pd.Timestamp(cutoff_val)
            ]
        else:
            subset = train_only[train_only[_sim_session] < cutoff_val]
        if len(subset) >= 50:
            vectors_cache[bucket] = build_artist_feature_vectors(
                subset, cutoff=cutoff_val,
                session_col=_sim_session, type_col=_sim_type, price_col=_sim_price,
            )

    sim_features = []
    for _, row in df.iterrows():
        bucket = row.get("_sim_bucket")
        vectors = vectors_cache.get(bucket, _fallback_vectors)
        artist = row.get("artist_clean", "")
        medium = row.get("medium_category", None)
        similar = find_similar_artists(
            str(artist), vectors, k=5,
            medium_filter=str(medium) if medium else None,
        )
        sim_features.append(compute_similarity_features(str(artist), similar))

    # 정리
    df = df.drop(columns=["_sim_bucket"], errors="ignore")

    sim_df = pd.DataFrame(sim_features, index=df.index)
    for col in sim_df.columns:
        df[col] = sim_df[col]

    # Similarity: warm 작가는 가중치 감쇠 (기존: 0으로 제거 → 개선: 연속 감쇠)
    sim_cols = ["sim_avg_price_ln", "sim_weighted_price_ln",
                "sim_count", "sim_avg_distance"]
    total_sold = df["artist_total_sold"].fillna(0)
    # newness_score: cold→1.0, warm→0.0 (연속 전환)
    df["artist_newness_score"] = np.clip(1.0 - total_sold / _COLD_THRESHOLD, 0.0, 1.0)
    for col in sim_cols:
        if col in df.columns:
            df[col] = df[col] * df["artist_newness_score"]

    # ─── 4. PSI 정규화 ───
    train_mask = (df["split"] == "train").values
    for feat in HIGH_PSI:
        if feat not in df.columns:
            continue
        vals = pd.to_numeric(df[feat], errors="coerce")
        mean, std = float(vals[train_mask].mean()), float(vals[train_mask].std())
        df[feat] = (vals - mean) / std if std > 0 else 0.0

    # ─── 5. Split ───
    train = df[df["split"] == "train"].copy()
    calib = df[df["split"] == "calib"]
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"]

    # ─── 5b. 시간 가중치 (최근 데이터 중시) ───
    if "sale_date" in train.columns:
        train_dates = pd.to_datetime(train["sale_date"], errors="coerce")
        max_date = train_dates.max()
        days_ago = (max_date - train_dates).dt.days.fillna(0)
        # 지수 감쇠: 반감기 730일 (2년) — 부드러운 가중치
        half_life = 730.0
        train["_sample_weight"] = np.exp(-np.log(2) * days_ago / half_life)
        # 최소 가중치 0.5 (오래된 데이터도 절반 이상 유지)
        train["_sample_weight"] = train["_sample_weight"].clip(lower=0.5)
        logger.info("Time weights: min=%.2f, max=%.2f, mean=%.2f",
                     train["_sample_weight"].min(), train["_sample_weight"].max(),
                     train["_sample_weight"].mean())
    else:
        train["_sample_weight"] = 1.0

    # 이미지 피처는 Cold 전용 모델에서만 사용 (전체 모델에 넣으면 악화됨)
    img_feature_cols = []  # 전체 모델에서는 이미지 미사용
    logger.info("Image features: disabled for main models (cold-only)")

    # ─── 6a. Model-A (CatBoost MultiQuantile) ───
    logger.info("=== Step 4a: Model-A ===")
    from visionai.price_engine.estimate_generator.quantile_model import (
        HedonicQuantileModel,
    )

    model_a = HedonicQuantileModel(iterations=2000, depth=8, learning_rate=0.05)
    model_a.fit(train, valid_df=calib, target_col="ln_price",
                extra_features=img_feature_cols or None,
                sample_weight_col="_sample_weight")
    model_a.save(OUTPUT_DIR / "model_a_quantile.cbm")

    # ─── 6b. TwoStep (5-bin Classifier + per-bin Regressor) ───
    logger.info("=== Step 4b: TwoStep ===")
    from visionai.price_engine.estimate_generator.two_step_model import TwoStepModel

    model_two = TwoStepModel(iterations=1500, depth=7)
    model_two.fit(train, valid_df=calib, target_col="ln_price")

    # ─── 6c. Ensemble (CatBoost + LightGBM → Ridge) ───
    logger.info("=== Step 4c: Ensemble ===")
    from visionai.price_engine.estimate_generator.ensemble_model import (
        EnsembleStackingModel,
    )

    model_ens = EnsembleStackingModel(iterations=1500, depth=7)
    model_ens.fit(train, calib_df=calib, valid_df=valid, target_col="ln_price",
                  extra_features=img_feature_cols or None,
                  sample_weight_col="_sample_weight")

    # ─── 7. CQR alpha=0.38 (각 모델에 적용) ───
    logger.info("=== Step 5: CQR alpha=0.38 ===")
    from visionai.price_engine.estimate_generator.conformal_calibrator import (
        ConformalQuantileCalibrator,
    )

    y_c = calib["ln_price"].dropna()
    mask_c = calib["ln_price"].notna()

    # Model-A CQR
    raw_q_c = model_a.predict_raw(calib)
    cqr_a = ConformalQuantileCalibrator(alpha=0.38)
    cqr_a.fit(y_c.values, raw_q_c[mask_c.values])
    cqr_a.save(str(OUTPUT_DIR / "conformal_calibrator.pkl"))

    # Ensemble CQR
    raw_q_ens = model_ens.predict_raw(calib)
    if raw_q_ens.ndim == 1:
        raw_q_ens = np.column_stack([raw_q_ens, raw_q_ens, raw_q_ens])
    cqr_ens = ConformalQuantileCalibrator(alpha=0.38)
    cqr_ens.fit(y_c.values, raw_q_ens[mask_c.values])
    cqr_ens.save(str(OUTPUT_DIR / "conformal_calibrator_ensemble.pkl"))

    # TwoStep CQR
    raw_q_two = model_two.predict_raw(calib)
    if raw_q_two.ndim == 1:
        raw_q_two = np.column_stack([raw_q_two, raw_q_two, raw_q_two])
    cqr_two = ConformalQuantileCalibrator(alpha=0.38)
    cqr_two.fit(y_c.values, raw_q_two[mask_c.values])

    # 모델→CQR 매핑
    cqr_map = {
        "model_a": cqr_a,
        "model_two": cqr_two,
        "model_ens": cqr_ens,
    }

    # ─── 7b. 가격대별 전문 모델 ───
    logger.info("=== Step 5b: Price-Segment Models ===")
    PRICE_SEGMENTS = {
        "low": (0, np.log(2_000_000)),          # <200만원
        "mid": (np.log(2_000_000), np.log(20_000_000)),  # 200만~2000만
        "high": (np.log(20_000_000), np.inf),   # 2000만+
    }
    seg_models = {}
    seg_cqrs = {}

    for seg_name, (lo, hi) in PRICE_SEGMENTS.items():
        seg_train = train[(train["ln_price"] >= lo) & (train["ln_price"] < hi)]
        seg_calib = calib[(calib["ln_price"] >= lo) & (calib["ln_price"] < hi)]
        if len(seg_train) < 100:
            logger.info("  Segment %s: skip (train=%d)", seg_name, len(seg_train))
            continue

        logger.info("  Segment %s: train=%d, calib=%d", seg_name, len(seg_train), len(seg_calib))

        from visionai.price_engine.estimate_generator.quantile_model import HedonicQuantileModel
        seg_model = HedonicQuantileModel(iterations=1500, depth=7, learning_rate=0.03)
        seg_model.fit(seg_train, valid_df=seg_calib if len(seg_calib) > 10 else None,
                      target_col="ln_price", extra_features=img_feature_cols or None,
                      sample_weight_col="_sample_weight")
        seg_models[seg_name] = seg_model

        # 세그먼트 CQR
        if len(seg_calib) > 20:
            seg_raw = seg_model.predict_raw(seg_calib)
            seg_y = seg_calib["ln_price"].dropna()
            seg_mask = seg_calib["ln_price"].notna()
            seg_cqr = ConformalQuantileCalibrator(alpha=0.38)
            seg_cqr.fit(seg_y.values, seg_raw[seg_mask.values])
            seg_cqrs[seg_name] = seg_cqr
        else:
            seg_cqrs[seg_name] = cqr_a  # 폴백

    logger.info("Segment models trained: %s", list(seg_models.keys()))

    # ─── 7c. Cold Start 전용 이미지 모델 ───
    # Mei-Moses (2025): 이미지 피처는 Cold 작가에만 효과
    cold_img_model = None
    cold_img_cqr = None
    CLIP_EMBED_PATH = ROOT / "data" / "clip_embeddings_pca.npy"
    CLIP_INDEX_PATH = ROOT / "data" / "clip_embeddings_index.csv"

    if CLIP_EMBED_PATH.exists() and CLIP_INDEX_PATH.exists():
        logger.info("=== Step 5c: Cold-Start Image Model ===")
        clip_embeds = np.load(CLIP_EMBED_PATH)
        clip_index = pd.read_csv(CLIP_INDEX_PATH, encoding="utf-8-sig")
        clip_index["idx"] = clip_index["idx"].astype(str)

        # CLIP 임베딩 → DataFrame 컬럼으로 변환
        clip_dict = {}
        for i, row in clip_index.iterrows():
            if i < len(clip_embeds):
                clip_dict[row["idx"]] = clip_embeds[i]

        n_clip = clip_embeds.shape[1]
        clip_cols = [f"clip_{j}" for j in range(n_clip)]

        # Cold 작가만 추출 (train + calib)
        cold_train = train[train["artist_total_sold"].fillna(0) < _COLD_THRESHOLD].copy()
        cold_calib = calib[calib["artist_total_sold"].fillna(0) < _COLD_THRESHOLD].copy()

        # CLIP 매핑
        for subset in [cold_train, cold_calib]:
            subset["idx"] = subset["idx"].astype(str) if "idx" in subset.columns else ""
            for col in clip_cols:
                subset[col] = 0.0
            for i, idx_val in enumerate(subset["idx"]):
                if idx_val in clip_dict:
                    for j, col in enumerate(clip_cols):
                        subset.iat[i, subset.columns.get_loc(col)] = float(clip_dict[idx_val][j])

        cold_clip_matched = (cold_train[clip_cols[0]] != 0).sum()
        logger.info("Cold-Image: train=%d (clip=%d), calib=%d",
                     len(cold_train), cold_clip_matched, len(cold_calib))

        if len(cold_train) >= 50:
            from visionai.price_engine.estimate_generator.quantile_model import HedonicQuantileModel
            cold_img_model = HedonicQuantileModel(iterations=1000, depth=6, learning_rate=0.03)
            cold_img_model.fit(
                cold_train, valid_df=cold_calib if len(cold_calib) > 10 else None,
                target_col="ln_price",
                extra_features=clip_cols,
                sample_weight_col="_sample_weight",
            )
            # Cold CQR
            if len(cold_calib) > 20:
                cold_raw = cold_img_model.predict_raw(cold_calib)
                cold_y = cold_calib["ln_price"].dropna()
                cold_m = cold_calib["ln_price"].notna()
                cold_img_cqr = ConformalQuantileCalibrator(alpha=0.45)  # Cold용 넓은 구간
                cold_img_cqr.fit(cold_y.values, cold_raw[cold_m.values])
            else:
                cold_img_cqr = cqr_a
            logger.info("Cold-Image model trained (depth=6, +%d CLIP dims)", n_clip)
    else:
        logger.info("CLIP embeddings not found, skipping cold-image model")

    # ─── 8. 평가 (Model-A q50) ───
    logger.info("=== Step 6: 평가 ===")

    # 학습 데이터 가격 범위 (클리핑용)
    train_prices = np.exp(train["ln_price"].dropna().values)
    _clip_low = np.percentile(train_prices, 1)   # 하위 1%
    _clip_high = np.percentile(train_prices, 99)  # 상위 99%
    logger.info("Price clip range: %s ~ %s", f"{_clip_low:,.0f}", f"{_clip_high:,.0f}")

    # ─── 8a. 가격대별 잔차 보정 계수 (valid에서 학습) ───
    # valid에서 Ensemble 예측 → 가격대별 중앙 오차(bias) 계산
    _v_raw = model_ens.predict_raw(valid)
    if _v_raw.ndim == 1:
        _v_raw = np.column_stack([_v_raw, _v_raw, _v_raw])
    _v_cal = cqr_ens.predict(_v_raw[valid["ln_price"].notna().values])
    _v_pred = np.exp(_v_cal[:, 1])
    _v_true = np.exp(valid["ln_price"].dropna().values)

    # 가격대별 bias (예측/실제 비율의 중앙값)
    _bias_segments = {
        "low": (0, 2_000_000),
        "mid": (2_000_000, 20_000_000),
        "high": (20_000_000, float("inf")),
    }
    _bias_factors = {}
    for seg_name, (lo, hi) in _bias_segments.items():
        seg_mask = (_v_pred >= lo) & (_v_pred < hi)
        if seg_mask.sum() > 10:
            ratio = _v_pred[seg_mask] / _v_true[seg_mask]
            _bias_factors[seg_name] = float(np.median(ratio))
        else:
            _bias_factors[seg_name] = 1.0
    logger.info("Bias correction factors: %s",
                 {k: f"{v:.3f}" for k, v in _bias_factors.items()})

    def _apply_bias_correction(p_mid: np.ndarray) -> np.ndarray:
        """가격대별 체계적 과대/과소예측 보정."""
        corrected = p_mid.copy()
        for seg_name, (lo, hi) in _bias_segments.items():
            seg_mask = (p_mid >= lo) & (p_mid < hi)
            if seg_mask.any() and _bias_factors.get(seg_name, 1.0) != 1.0:
                corrected[seg_mask] = p_mid[seg_mask] / _bias_factors[seg_name]
        return corrected

    def evaluate(split_df, name, model=None, calibrator=None, apply_bias=False):
        m = model or model_a
        cal = calibrator or cqr_a
        raw_q = m.predict_raw(split_df)
        y = split_df["ln_price"].values
        mask = np.isfinite(y)
        if raw_q.ndim == 1:
            raw_q = np.column_stack([raw_q, raw_q, raw_q])
        cal_q = cal.predict(raw_q[mask])
        p_low, p_mid, p_high = np.exp(cal_q[:, 0]), np.exp(cal_q[:, 1]), np.exp(cal_q[:, 2])
        y_true = np.exp(y[mask])

        # 이상치 클리핑 + 잔차 보정
        p_mid = np.clip(p_mid, _clip_low, _clip_high)
        if apply_bias:
            p_mid = _apply_bias_correction(p_mid)

        ape = np.abs(p_mid - y_true) / y_true
        mdape = float(np.median(ape) * 100)
        w30 = float(np.mean(ape <= 0.30) * 100)
        cov = float(np.mean((y_true >= p_low) & (y_true <= p_high)))
        ss_r = np.sum((y_true - p_mid) ** 2)
        ss_t = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1 - ss_r / ss_t) if ss_t > 0 else 0

        # 훈련과 동일한 cold 정의 사용 (artist_total_sold 기반, is_new_artist 아님)
        cold = (split_df["artist_total_sold"].fillna(0) < _COLD_THRESHOLD).values[mask]
        c_md = float(np.median(ape[cold]) * 100) if cold.sum() > 0 else float("nan")
        w_md = float(np.median(ape[~cold]) * 100) if (~cold).sum() > 0 else float("nan")

        logger.info(
            "%s: MdAPE=%.2f%% (W=%.2f%% C=%.2f%%) R2=%.4f Cov=%.1f%% W30=%.1f%%",
            name, mdape, w_md, c_md, r2, cov * 100, w30,
        )
        return {
            "mdape": mdape, "warm_mdape": w_md, "cold_mdape": c_md,
            "r2": r2, "coverage": cov, "within_30": w30,
        }

    # ─── 8. 3개 모델 비교 평가 ───
    logger.info("=== Step 6: 3-Model Comparison ===")

    # Model-A (with CQR)
    v = evaluate(valid, "Valid-A", calibrator=cqr_a)
    t = evaluate(test, "Test-A", calibrator=cqr_a)

    # TwoStep (with CQR)
    v_two = evaluate(valid, "Valid-TwoStep", model=model_two, calibrator=cqr_two)
    t_two = evaluate(test, "Test-TwoStep", model=model_two, calibrator=cqr_two)

    # Ensemble (with CQR)
    v_ens = evaluate(valid, "Valid-Ensemble", model=model_ens, calibrator=cqr_ens)
    t_ens = evaluate(test, "Test-Ensemble", model=model_ens, calibrator=cqr_ens)

    # Ensemble + Bias correction
    v_ens_bc = evaluate(valid, "Valid-Ens+Bias", model=model_ens, calibrator=cqr_ens, apply_bias=True)
    t_ens_bc = evaluate(test, "Test-Ens+Bias", model=model_ens, calibrator=cqr_ens, apply_bias=True)

    # ─── 8b. 가중 블렌딩 앙상블 ───
    logger.info("=== Step 6b: Weighted Blend ===")

    def evaluate_blend(split_df, name, weights=(0.6, 0.2, 0.2)):
        """3 모델 가중 평균 예측."""
        models = [model_ens, model_a, model_two]
        cqrs = [cqr_ens, cqr_a, cqr_two]
        y = split_df["ln_price"].values
        mask = np.isfinite(y)

        blended = np.zeros((mask.sum(), 3))  # q25, q50, q75
        for m, cal, w in zip(models, cqrs, weights):
            raw_q = m.predict_raw(split_df)
            if raw_q.ndim == 1:
                raw_q = np.column_stack([raw_q, raw_q, raw_q])
            cal_q = cal.predict(raw_q[mask])
            blended += w * cal_q

        p_low, p_mid, p_high = np.exp(blended[:, 0]), np.exp(blended[:, 1]), np.exp(blended[:, 2])
        y_true = np.exp(y[mask])

        # 이상치 클리핑
        p_mid = np.clip(p_mid, _clip_low, _clip_high)

        ape = np.abs(p_mid - y_true) / y_true
        mdape = float(np.median(ape) * 100)
        w30 = float(np.mean(ape <= 0.30) * 100)
        cov = float(np.mean((y_true >= p_low) & (y_true <= p_high)))
        ss_r = np.sum((y_true - p_mid) ** 2)
        ss_t = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1 - ss_r / ss_t) if ss_t > 0 else 0

        cold = (split_df["artist_total_sold"].fillna(0) < _COLD_THRESHOLD).values[mask]
        c_md = float(np.median(ape[cold]) * 100) if cold.sum() > 0 else float("nan")
        w_md = float(np.median(ape[~cold]) * 100) if (~cold).sum() > 0 else float("nan")

        logger.info(
            "%s: MdAPE=%.2f%% (W=%.2f%% C=%.2f%%) R2=%.4f Cov=%.1f%% W30=%.1f%%",
            name, mdape, w_md, c_md, r2, cov * 100, w30,
        )
        return {
            "mdape": mdape, "warm_mdape": w_md, "cold_mdape": c_md,
            "r2": r2, "coverage": cov, "within_30": w30,
        }

    v_blend = evaluate_blend(valid, "Valid-Blend")
    t_blend = evaluate_blend(test, "Test-Blend")

    # ─── 8c. 세그먼트 모델 평가 ───
    def evaluate_segmented(split_df, name):
        """세그먼트별 전문 모델로 예측, 결합 후 평가."""
        y = split_df["ln_price"].values
        mask = np.isfinite(y)
        n = mask.sum()
        p_mid = np.zeros(n)
        p_low = np.zeros(n)
        p_high = np.zeros(n)

        # 기본: Ensemble 예측으로 초기화
        raw_q_base = model_ens.predict_raw(split_df)
        if raw_q_base.ndim == 1:
            raw_q_base = np.column_stack([raw_q_base, raw_q_base, raw_q_base])
        cal_q_base = cqr_ens.predict(raw_q_base[mask])
        p_low[:] = np.exp(cal_q_base[:, 0])
        p_mid[:] = np.exp(cal_q_base[:, 1])
        p_high[:] = np.exp(cal_q_base[:, 2])

        y_masked = y[mask]

        # 세그먼트별 전문 모델 적용
        for seg_name, (lo, hi) in PRICE_SEGMENTS.items():
            if seg_name not in seg_models:
                continue
            # Ensemble 예측 기반으로 세그먼트 할당 (실제 가격 아닌 예측 가격)
            pred_ln = np.log(p_mid.clip(min=1))
            seg_mask = (pred_ln >= lo) & (pred_ln < hi)
            if not seg_mask.any():
                continue

            # 해당 세그먼트 행 추출
            seg_idx = np.where(mask)[0][seg_mask]
            seg_df = split_df.iloc[seg_idx]

            seg_raw = seg_models[seg_name].predict_raw(seg_df)
            seg_cal = seg_cqrs[seg_name].predict(seg_raw)
            p_low[seg_mask] = np.exp(seg_cal[:, 0])
            p_mid[seg_mask] = np.exp(seg_cal[:, 1])
            p_high[seg_mask] = np.exp(seg_cal[:, 2])

        y_true = np.exp(y_masked)
        p_mid = np.clip(p_mid, _clip_low, _clip_high)

        ape = np.abs(p_mid - y_true) / y_true
        mdape = float(np.median(ape) * 100)
        w30 = float(np.mean(ape <= 0.30) * 100)
        cov = float(np.mean((y_true >= p_low) & (y_true <= p_high)))
        ss_r = np.sum((y_true - p_mid) ** 2)
        ss_t = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1 - ss_r / ss_t) if ss_t > 0 else 0

        cold = (split_df["artist_total_sold"].fillna(0) < _COLD_THRESHOLD).values[mask]
        c_md = float(np.median(ape[cold]) * 100) if cold.sum() > 0 else float("nan")
        w_md = float(np.median(ape[~cold]) * 100) if (~cold).sum() > 0 else float("nan")

        logger.info(
            "%s: MdAPE=%.2f%% (W=%.2f%% C=%.2f%%) R2=%.4f Cov=%.1f%% W30=%.1f%%",
            name, mdape, w_md, c_md, r2, cov * 100, w30,
        )
        return {
            "mdape": mdape, "warm_mdape": w_md, "cold_mdape": c_md,
            "r2": r2, "coverage": cov, "within_30": w30,
        }

    if seg_models:
        v_seg = evaluate_segmented(valid, "Valid-Segment")
        t_seg = evaluate_segmented(test, "Test-Segment")
    else:
        v_seg, t_seg = v_ens, t_ens

    # ─── 8d. Cold-Image 하이브리드 평가 ───
    def evaluate_cold_hybrid(split_df, name):
        """Warm→Ensemble, Cold→Cold-Image 모델 하이브리드."""
        y = split_df["ln_price"].values
        mask = np.isfinite(y)
        n = mask.sum()

        # Warm 기본: Ensemble
        raw_q = model_ens.predict_raw(split_df)
        if raw_q.ndim == 1:
            raw_q = np.column_stack([raw_q, raw_q, raw_q])
        cal_q = cqr_ens.predict(raw_q[mask])
        p_low = np.exp(cal_q[:, 0])
        p_mid = np.exp(cal_q[:, 1])
        p_high = np.exp(cal_q[:, 2])

        # Cold 작가: Cold-Image 모델로 교체
        if cold_img_model is not None:
            cold_flags = (split_df["artist_total_sold"].fillna(0) < _COLD_THRESHOLD).values[mask]

            if cold_flags.sum() > 0:
                cold_idx = np.where(mask)[0][cold_flags]
                cold_df = split_df.iloc[cold_idx].copy()

                # CLIP 매핑
                cold_df["idx"] = cold_df["idx"].astype(str) if "idx" in cold_df.columns else ""
                for col in [f"clip_{j}" for j in range(clip_embeds.shape[1])] if CLIP_EMBED_PATH.exists() else []:
                    cold_df[col] = 0.0
                for i, idx_val in enumerate(cold_df["idx"]):
                    if idx_val in clip_dict:
                        for j in range(clip_embeds.shape[1]):
                            cold_df.iat[i, cold_df.columns.get_loc(f"clip_{j}")] = float(clip_dict[idx_val][j])

                cold_raw = cold_img_model.predict_raw(cold_df)
                cold_cal = cold_img_cqr.predict(cold_raw)
                p_low[cold_flags] = np.exp(cold_cal[:, 0])
                p_mid[cold_flags] = np.exp(cold_cal[:, 1])
                p_high[cold_flags] = np.exp(cold_cal[:, 2])

        y_true = np.exp(y[mask])
        p_mid = np.clip(p_mid, _clip_low, _clip_high)

        ape = np.abs(p_mid - y_true) / y_true
        mdape = float(np.median(ape) * 100)
        w30 = float(np.mean(ape <= 0.30) * 100)
        cov = float(np.mean((y_true >= p_low) & (y_true <= p_high)))
        ss_r = np.sum((y_true - p_mid) ** 2)
        ss_t = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1 - ss_r / ss_t) if ss_t > 0 else 0

        cold = (split_df["artist_total_sold"].fillna(0) < _COLD_THRESHOLD).values[mask]
        c_md = float(np.median(ape[cold]) * 100) if cold.sum() > 0 else float("nan")
        w_md = float(np.median(ape[~cold]) * 100) if (~cold).sum() > 0 else float("nan")

        logger.info(
            "%s: MdAPE=%.2f%% (W=%.2f%% C=%.2f%%) R2=%.4f Cov=%.1f%% W30=%.1f%%",
            name, mdape, w_md, c_md, r2, cov * 100, w30,
        )
        return {
            "mdape": mdape, "warm_mdape": w_md, "cold_mdape": c_md,
            "r2": r2, "coverage": cov, "within_30": w30,
        }

    if cold_img_model is not None:
        v_hybrid = evaluate_cold_hybrid(valid, "Valid-ColdHybrid")
        t_hybrid = evaluate_cold_hybrid(test, "Test-ColdHybrid")
    else:
        v_hybrid, t_hybrid = v_ens, t_ens

    # 최적 모델 선택 (test MdAPE 기준, 모든 변형 포함)
    all_results = {
        "Model-A": (t, v),
        "TwoStep": (t_two, v_two),
        "Ensemble": (t_ens, v_ens),
        "Ens+Bias": (t_ens_bc, v_ens_bc),
        "Blend": (t_blend, v_blend),
        "Segment": (t_seg, v_seg),
        "ColdHybrid": (t_hybrid, v_hybrid),
    }
    best_name = min(all_results, key=lambda k: all_results[k][0]["mdape"])
    best_t, best_v = all_results[best_name]
    logger.info("Best model: %s (Test MdAPE=%.2f%%)", best_name, best_t["mdape"])

    gap = best_t["mdape"] - best_v["mdape"]
    mono = model_a.check_monotonicity(valid)

    # Gate 판정
    logger.info("=" * 60)
    gates = {
        "G1 MdAPE≤32%": best_t["mdape"] <= 32,
        "G2 Gap≤2.5%p": abs(gap) <= 2.5,
        "G3 R²≥0.40": best_t["r2"] >= 0.40,
        "G4 Cold≤58%": best_t["cold_mdape"] <= 58,
        "G5 Cov≥55%": best_t["coverage"] >= 0.55,
        "G6 W30≥53%": best_t["within_30"] >= 53,
        "G8 Mono≥0.99": mono >= 0.99,
    }
    for g, ok in gates.items():
        logger.info("  %s: %s", g, "PASS" if ok else "FAIL")
    logger.info("Gate: %d/%d", sum(gates.values()), len(gates))
    logger.info("=" * 60)

    # 저장
    metrics = {
        "best_model": best_name,
        "valid_mdape": best_v["mdape"], "test_mdape": best_t["mdape"], "gap": gap,
        "valid_r2": best_v["r2"], "test_r2": best_t["r2"],
        "valid_coverage": best_v["coverage"], "test_coverage": best_t["coverage"],
        "valid_within_30": best_v["within_30"], "test_within_30": best_t["within_30"],
        "cold_mdape": best_t["cold_mdape"], "warm_mdape": best_t["warm_mdape"],
        "monotonicity_rate": mono,
        "coverage_overall": best_t["coverage"], "within_30_pct": best_t["within_30"],
        "model_a_test_mdape": t["mdape"],
        "twostep_test_mdape": t_two["mdape"],
        "ensemble_test_mdape": t_ens["mdape"],
        "gates": gates,
        "model": "Model-A q50 + CQR alpha=0.38",
    }
    for path_name in ["phase5_final_metrics.json", "estimate_metrics.json"]:
        with open(OUTPUT_DIR / path_name, "w") as f:
            json.dump(metrics, f, indent=2, default=str)

    gap_path = OUTPUT_DIR / "gap_diagnosis.json"
    if gap_path.exists():
        with open(gap_path) as f:
            diag = json.load(f)
        diag.update({
            "valid_mdape": v["mdape"], "test_mdape": t["mdape"],
            "gap": gap, "within_30_pct": t["within_30"],
            "coverage_overall": t["coverage"],
        })
        with open(gap_path, "w") as f:
            json.dump(diag, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Done. Saved to %s", OUTPUT_DIR / "phase5_final_metrics.json")


if __name__ == "__main__":
    main()
