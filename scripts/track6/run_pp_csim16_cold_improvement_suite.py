#!/usr/bin/env python3
"""PP-CSIM16: Cold improvement suite after q35 robustness validation.

This experiment keeps the strict unresolved-artist Cold contract and compares
the next plausible model improvements:

- price-band Quantile selection using only inference-time signals
- Quantile ensembles
- low-price-specialized model selected by inference-time proxy
- similarity-weighted reference statistics
- q35 basis + clipped residual correction

Strict Cold contract:
- no artist_key feature
- no same-artist price history feature
- no artist_key lookup postprocess
- no search_* or external live search features
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import KFold
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import META_BUCKET_FEATURES, USER_META_CORE, load_user_meta_frames  # noqa: E402
from run_pp_cmeta5_user_meta_robustness_validation import paired_bootstrap  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    SIM_NUMERIC,
    compute_reference_stats,
    existing_columns,
    html_table,
    json_clean,
    lgbm_quantile_model,
    md_table,
    normalize_for_model,
    similarity_preprocessor,
    split_types,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM16"
SLUG = "PP-CSIM16_cold_improvement_suite"
TITLE = "Cold 성능 개선 후보 종합 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim16_cold_improvement_suite_summary.md"

TOP_K = 160
OOF_SPLITS = 5

ENTERABLE_META = [
    "artist_meta_birth_year",
    "artist_meta_career_stage",
    "artist_meta_birth_year_missing",
    "artist_meta_career_stage_missing",
    "artist_meta_nationality",
]

ENTERABLE_BUCKETS = [
    "artist_birth_period_bucket",
    "artist_career_stage_bucket",
    "medium_birth_period_bucket",
    "career_size_bucket",
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[valid]
    weights = weights[valid]
    if len(values) == 0:
        return float("nan")
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights)
    cutoff = quantile * cdf[-1]
    return float(values[np.searchsorted(cdf, cutoff, side="left")])


def weighted_reference_stats_from_neighbors(ref_frame: pd.DataFrame, distances: np.ndarray, indices: np.ndarray, prefix: str) -> pd.DataFrame:
    prices = ref_frame["ln_price_krw"].to_numpy(dtype=float)
    area = np.maximum(pd.to_numeric(ref_frame.get("area_cm2", 0.0), errors="coerce").fillna(0.0).to_numpy(dtype=float), 1.0)
    area_price = prices - np.log(area)
    rows = []
    for dist_row, idx_row in zip(distances, indices, strict=True):
        idx = np.asarray(idx_row, dtype=int)
        vals = prices[idx]
        ap_vals = area_price[idx]
        sim = 1.0 / (1.0 + np.asarray(dist_row, dtype=float))
        weights = sim ** 2
        w_sum = float(np.sum(weights))
        rows.append({
            f"{prefix}_ref_n": float(len(idx)),
            f"{prefix}_ref_log_price_median": weighted_quantile(vals, weights, 0.50),
            f"{prefix}_ref_log_price_q25": weighted_quantile(vals, weights, 0.25),
            f"{prefix}_ref_log_price_q75": weighted_quantile(vals, weights, 0.75),
            f"{prefix}_ref_log_price_iqr": weighted_quantile(vals, weights, 0.75) - weighted_quantile(vals, weights, 0.25),
            f"{prefix}_ref_log_price_mean": float(np.sum(vals * weights) / w_sum) if w_sum else float("nan"),
            f"{prefix}_ref_log_price_std": float(np.sqrt(np.sum(weights * (vals - (np.sum(vals * weights) / w_sum)) ** 2) / w_sum)) if w_sum else float("nan"),
            f"{prefix}_ref_area_price_median": weighted_quantile(ap_vals, weights, 0.50),
            f"{prefix}_ref_similarity_mean": float(np.average(sim, weights=weights)) if w_sum else float("nan"),
            f"{prefix}_ref_similarity_max": float(np.max(sim)),
            f"{prefix}_ref_similarity_min": float(np.min(sim)),
        })
    return pd.DataFrame(rows)


def compute_weighted_reference_stats(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    *,
    prefix: str,
    top_k: int = TOP_K,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    features = existing_columns(train, features)
    if not features:
        raise ValueError(f"{prefix} has no similarity features")
    feature_names = [f"{prefix}_{name}" for name in SIM_NUMERIC]
    train_stats = pd.DataFrame(index=train.index, columns=feature_names, dtype=float)
    kf = KFold(n_splits=OOF_SPLITS, shuffle=True, random_state=SEED)
    for ref_idx, target_idx in kf.split(train):
        ref = train.iloc[ref_idx].copy()
        target = train.iloc[target_idx].copy()
        prep = similarity_preprocessor(ref, features)
        ref_x = prep.fit_transform(ref[features])
        target_x = prep.transform(target[features])
        nn = NearestNeighbors(n_neighbors=min(top_k, len(ref)), metric="cosine")
        nn.fit(ref_x)
        dist, idx = nn.kneighbors(target_x)
        fold_stats = weighted_reference_stats_from_neighbors(ref, dist, idx, prefix)
        train_stats.iloc[target_idx] = fold_stats.to_numpy(dtype=float)

    prep = similarity_preprocessor(train, features)
    train_x = prep.fit_transform(train[features])
    nn = NearestNeighbors(n_neighbors=min(top_k, len(train)), metric="cosine")
    nn.fit(train_x)
    val_dist, val_idx = nn.kneighbors(prep.transform(val[features]))
    test_dist, test_idx = nn.kneighbors(prep.transform(test[features]))
    val_stats = weighted_reference_stats_from_neighbors(train, val_dist, val_idx, prefix)
    test_stats = weighted_reference_stats_from_neighbors(train, test_dist, test_idx, prefix)

    return (
        pd.concat([train.reset_index(drop=True), train_stats.reset_index(drop=True)], axis=1),
        pd.concat([val.reset_index(drop=True), val_stats.reset_index(drop=True)], axis=1),
        pd.concat([test.reset_index(drop=True), test_stats.reset_index(drop=True)], axis=1),
        feature_names,
    )


def fit_quantile_model(train: pd.DataFrame, features: list[str], *, alpha: float):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return model


def predict_model(model: Any, train: pd.DataFrame, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    _, frame_n, _ = normalize_for_model(train.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
    return np.asarray(model.predict(frame_n[features]), dtype=float)


def huber_residual_model(train: pd.DataFrame, features: list[str]) -> Pipeline:
    numeric, categorical = split_types(train, features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="huber",
            alpha=0.9,
            n_estimators=260,
            learning_rate=0.03,
            num_leaves=20,
            min_child_samples=55,
            subsample=0.9,
            colsample_bytree=0.85,
            reg_lambda=2.2,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def fit_residual_model(train: pd.DataFrame, features: list[str], basis: np.ndarray):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    residual_y = train_n["ln_price_krw"].to_numpy(dtype=float) - np.asarray(basis, dtype=float)
    model = huber_residual_model(train_n, features)
    model.fit(train_n[features], residual_y)
    return model


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
    }
    if extra:
        row.update(extra)
    return row


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, family: str) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "family": family,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "policy": policy,
    })


def segment_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, split), df in predictions.groupby(["candidate", "split"], observed=False):
        if df.empty:
            continue
        work = df.copy()
        work["actual_price_band"] = pd.cut(
            pd.to_numeric(work["actual_price"], errors="coerce"),
            bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
            labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
            include_lowest=True,
        ).astype("string")
        for segment, group in work.groupby("actual_price_band", dropna=False, observed=False):
            pred = group["pred_log"].to_numpy(dtype=float)
            rows.append({
                "candidate": candidate,
                "split": split,
                "segment": str(segment),
                "n": int(len(group)),
                **metrics(
                    group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                    ),
                    pred,
                ),
                **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
            })
    return pd.DataFrame(rows)


def add_candidate(
    candidates: dict[str, dict[str, Any]],
    name: str,
    family: str,
    policy: str,
    val_pred: np.ndarray,
    test_pred: np.ndarray,
) -> None:
    candidates[name] = {
        "family": family,
        "policy": policy,
        "validation": val_pred,
        "test": test_pred,
    }


def write_reports(metrics_df: pd.DataFrame, predictions_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "family", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean",
        "delta_p95_APE_a_minus_b_mean", "delta_RMSE_log_a_minus_b_mean",
        "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10"]
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(16)
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(16)
    test_tail = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"]).head(16)
    focus_candidates = unique(["q45_current", "q35_global"] + test["candidate"].head(6).tolist() + test_tail["candidate"].head(6).tolist())
    test_seg = seg_df[(seg_df["split"].eq("test")) & (seg_df["candidate"].isin(focus_candidates))].sort_values(["segment", "candidate"])

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: q35 이후 추가 성능 개선 후보를 같은 strict Cold 조건에서 비교한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 모든 선택 규칙은 사용 단계에서 알 수 있는 예측값과 유사작품 통계만 사용한다.",
        "",
        "## 1. Test 성능: MAPE 기준",
        md_table(test, metric_cols),
        "",
        "## 2. Test 성능: APE > 5 기준",
        md_table(test_tail, metric_cols),
        "",
        "## 3. Validation 성능: MAPE 기준",
        md_table(val, metric_cols),
        "",
        "## 4. Paired bootstrap",
        "- delta는 `후보 - q35_global`이다. 음수이면 후보가 q35보다 좋다.",
        md_table(boot_df, boot_cols),
        "",
        "## 5. Test 가격대별 진단",
        md_table(test_seg, seg_cols),
        "",
        "## 6. 해석",
        "",
        "- q35 이후 개선 후보는 저가 tail 개선과 고가 손실 방어를 동시에 봐야 한다.",
        "- validation과 test가 같은 방향으로 개선되는 후보만 다음 단계 후보로 본다.",
        "- test만 좋아진 복잡한 선택 규칙은 운영 후보가 아니라 후속 검증 대상으로 둔다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}code{{background:#eef2f7;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<p>strict Cold 조건에서 q35 이후 개선 후보를 비교한다. artist_key, 같은 작가 가격 이력, lookup 후처리, 외부 live 검색은 사용하지 않았다.</p>
<h2>Test 성능: MAPE 기준</h2>{html_table(test, metric_cols)}
<h2>Test 성능: APE &gt; 5 기준</h2>{html_table(test_tail, metric_cols)}
<h2>Validation 성능</h2>{html_table(val, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>Test 가격대별 진단</h2>{html_table(test_seg, seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    artwork_features = unique(fs["cold_lgb"])
    enterable_base = unique(artwork_features + ENTERABLE_META + ENTERABLE_BUCKETS)
    required = unique(enterable_base + USER_META_CORE + META_BUCKET_FEATURES + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    assert_strict_cold_features(enterable_base, context=f"{EXP_ID}:enterable_base")

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train,
        val,
        test,
        ARTWORK_SIM_FEATURES,
        prefix=f"artwork_sim_k{TOP_K}",
        top_k=TOP_K,
    )
    features = unique(enterable_base + art_ref_features)

    models = {alpha: fit_quantile_model(train_art, features, alpha=alpha) for alpha in [0.35, 0.40, 0.45, 0.50]}
    val_pred = {alpha: predict_model(model, train_art, val_art, features) for alpha, model in models.items()}
    test_pred = {alpha: predict_model(model, train_art, test_art, features) for alpha, model in models.items()}

    candidates: dict[str, dict[str, Any]] = {}
    add_candidate(candidates, "q45_current", "baseline", "기존 q45 후보", val_pred[0.45], test_pred[0.45])
    add_candidate(candidates, "q35_global", "baseline", "전체 q35 후보", val_pred[0.35], test_pred[0.35])
    add_candidate(candidates, "q40_global", "quantile", "전체 q40 후보", val_pred[0.40], test_pred[0.40])
    add_candidate(
        candidates,
        "blend_60q35_30q45_10q50",
        "quantile_ensemble",
        "0.60*q35 + 0.30*q45 + 0.10*q50",
        0.60 * val_pred[0.35] + 0.30 * val_pred[0.45] + 0.10 * val_pred[0.50],
        0.60 * test_pred[0.35] + 0.30 * test_pred[0.45] + 0.10 * test_pred[0.50],
    )
    add_candidate(
        candidates,
        "blend_50q35_50q45",
        "quantile_ensemble",
        "0.50*q35 + 0.50*q45",
        0.50 * val_pred[0.35] + 0.50 * val_pred[0.45],
        0.50 * test_pred[0.35] + 0.50 * test_pred[0.45],
    )

    def band_candidates(frame: pd.DataFrame, p35: np.ndarray, p40: np.ndarray, p45: np.ndarray, p50: np.ndarray) -> dict[str, np.ndarray]:
        ref_med = pd.to_numeric(frame.get(f"artwork_sim_k{TOP_K}_ref_log_price_median"), errors="coerce").to_numpy(dtype=float)
        ref_price = np.exp(ref_med)
        pred45_price = np.exp(p45)
        low_by_pred = pred45_price < 3_000_000
        high_by_pred = pred45_price >= 10_000_000
        low_by_ref = np.isfinite(ref_price) & (ref_price < 3_000_000)
        high_by_ref = np.isfinite(ref_price) & (ref_price >= 10_000_000)
        return {
            "band_pred_q35_low_q45_high": np.where(low_by_pred, p35, np.where(high_by_pred, p45, p40)),
            "band_ref_q35_low_q45_high": np.where(low_by_ref, p35, np.where(high_by_ref, p45, p40)),
            "band_any_low_q35_high_q45": np.where(low_by_pred | low_by_ref, p35, np.where(high_by_pred | high_by_ref, p45, p40)),
        }

    val_bands = band_candidates(val_art, val_pred[0.35], val_pred[0.40], val_pred[0.45], val_pred[0.50])
    test_bands = band_candidates(test_art, test_pred[0.35], test_pred[0.40], test_pred[0.45], test_pred[0.50])
    for name in val_bands:
        add_candidate(candidates, name, "price_band_quantile", "예측가/유사작품 기준가로 저가 q35, 중간 q40, 고가 q45 선택", val_bands[name], test_bands[name])

    low_train = train_art[pd.to_numeric(train_art["price_krw"], errors="coerce") < 3_000_000].copy()
    if len(low_train) >= 500:
        low_model = fit_quantile_model(low_train, features, alpha=0.45)
        low_val = predict_model(low_model, low_train, val_art, features)
        low_test = predict_model(low_model, low_train, test_art, features)
        val_low_mask = np.exp(val_pred[0.45]) < 3_000_000
        test_low_mask = np.exp(test_pred[0.45]) < 3_000_000
        add_candidate(
            candidates,
            "low_specialist_if_pred_lt_300w",
            "low_price_specialist",
            "q45 예측가가 300만원 미만이면 저가 전용 모델, 아니면 q45",
            np.where(val_low_mask, low_val, val_pred[0.45]),
            np.where(test_low_mask, low_test, test_pred[0.45]),
        )

    train_w, val_w, test_w, weighted_ref_features = compute_weighted_reference_stats(
        train,
        val,
        test,
        ARTWORK_SIM_FEATURES,
        prefix=f"artwork_wsim_k{TOP_K}",
        top_k=TOP_K,
    )
    weighted_features = unique(enterable_base + weighted_ref_features)
    weighted_q35 = fit_quantile_model(train_w, weighted_features, alpha=0.35)
    weighted_q45 = fit_quantile_model(train_w, weighted_features, alpha=0.45)
    add_candidate(
        candidates,
        "weighted_similarity_q35",
        "weighted_similarity",
        "거리 가까운 유사작품에 더 큰 가중치를 둔 k160 통계 + q35",
        predict_model(weighted_q35, train_w, val_w, weighted_features),
        predict_model(weighted_q35, train_w, test_w, weighted_features),
    )
    add_candidate(
        candidates,
        "weighted_similarity_q45",
        "weighted_similarity",
        "거리 가까운 유사작품에 더 큰 가중치를 둔 k160 통계 + q45",
        predict_model(weighted_q45, train_w, val_w, weighted_features),
        predict_model(weighted_q45, train_w, test_w, weighted_features),
    )

    residual_model = fit_residual_model(train_art, features, val_pred[0.35][:1] if False else predict_model(models[0.35], train_art, train_art, features))
    residual_val = predict_model(residual_model, train_art, val_art, features)
    residual_test = predict_model(residual_model, train_art, test_art, features)
    for name, strength, lower, upper in [
        ("q35_resid_025_clip010", 0.25, -0.10, 0.10),
        ("q35_resid_050_clip010", 0.50, -0.10, 0.10),
        ("q35_resid_025_clip020", 0.25, -0.20, 0.20),
    ]:
        add_candidate(
            candidates,
            name,
            "q35_residual_clip",
            f"q35 + clip({strength} * Huber residual, {lower}, {upper})",
            val_pred[0.35] + np.clip(strength * residual_val, lower, upper),
            test_pred[0.35] + np.clip(strength * residual_test, lower, upper),
        )

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for candidate, pack in candidates.items():
        for split, frame in [("validation", val_art), ("test", test_art)]:
            pred = pack[split]
            metric_rows.append(metric_row(candidate, split, frame, pred, pack["policy"], {"family": pack["family"]}))
            pred_frames.append(prediction_frame(candidate, split, frame, pred, pack["policy"], pack["family"]))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    seg_df = segment_summary(predictions_df)

    boot_rows = []
    test_rank = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(10)["candidate"].tolist()
    val_rank = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(10)["candidate"].tolist()
    boot_candidates = unique(["q45_current"] + test_rank + val_rank)
    for split, frame in [("validation", val_art), ("test", test_art)]:
        base = candidates["q35_global"][split]
        for candidate in boot_candidates:
            if candidate == "q35_global":
                continue
            boot_rows.append(paired_bootstrap(
                frame,
                candidates[candidate][split],
                base,
                a_name=candidate,
                b_name="q35_global",
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "uses_weighted_similarity_reference_stats": True,
        "router_used": False,
        "selection_policy_evaluated": True,
        "router_uses_actual_price": False,
        "top_k": TOP_K,
        "candidate_count": len(candidates),
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_q35.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, predictions_df, boot_df, seg_df, summary)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
