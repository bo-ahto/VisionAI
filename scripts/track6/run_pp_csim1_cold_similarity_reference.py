#!/usr/bin/env python3
"""PP-CSIM1: strict Cold similar artist/artwork reference features.

This experiment tests whether Cold accuracy improves when the model receives
reference-price statistics from similar artworks, similar artist metadata, or
the combination of similar artists and similar artworks.

Strict Cold contract:
- no artist_key feature
- no same-artist price history feature
- no artist_key lookup postprocess
- no search_* or external live search features

For train rows, similarity statistics are generated out-of-fold so the target
row price cannot enter its own reference group.  Validation/test rows use train
only as the reference pool.
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
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import (  # noqa: E402
    assert_no_artist_lookup_postprocess,
    assert_strict_cold_features,
    strict_cold_run_summary,
)
from run_pp_cmeta4_user_input_meta_only import (  # noqa: E402
    USER_META_CORE,
    add_user_meta_buckets,
    candidate_defs,
    load_user_meta_frames,
)
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM1"
SLUG = "PP-CSIM1_cold_similarity_reference"
TITLE = "Cold 유사작가/유사작품 비교군 피처 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim1_cold_similarity_reference_summary.md"

TOP_K = 80
OOF_SPLITS = 5

ARTWORK_SIM_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "size_bucket",
    "has_depth",
    "is_3d_candidate",
    "is_extreme_aspect_ratio",
]

ARTIST_SIM_FEATURES = USER_META_CORE + [
    "artist_birth_period_bucket",
    "artist_inventory_bucket",
    "artist_followers_bucket",
    "artist_career_stage_bucket",
    "artist_meta_completeness_bucket",
]

SIM_NUMERIC = [
    "ref_n",
    "ref_log_price_median",
    "ref_log_price_q25",
    "ref_log_price_q75",
    "ref_log_price_iqr",
    "ref_log_price_mean",
    "ref_log_price_std",
    "ref_area_price_median",
    "ref_similarity_mean",
    "ref_similarity_max",
    "ref_similarity_min",
]


def json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [json_clean(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if pd.isna(value):
        return None
    return value


def existing_columns(frame: pd.DataFrame, features: list[str]) -> list[str]:
    return [feature for feature in features if feature in frame.columns]


def split_types(frame: pd.DataFrame, features: list[str]) -> tuple[list[str], list[str]]:
    numeric: list[str] = []
    categorical: list[str] = []
    for feature in features:
        if feature.startswith("ref_") or pd.api.types.is_numeric_dtype(frame.get(feature)):
            numeric.append(feature)
        else:
            categorical.append(feature)
    return numeric, categorical


def normalize_for_model(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    out_frames = []
    numeric, categorical = split_types(train, features)
    for frame in [train, val, test]:
        out = frame.copy()
        for col in numeric:
            if col not in out.columns:
                out[col] = np.nan
            out[col] = pd.to_numeric(out[col], errors="coerce")
        for col in categorical:
            if col not in out.columns:
                out[col] = "__MISSING__"
            out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
        out_frames.append(out)
    return out_frames[0], out_frames[1], out_frames[2]


def lgbm_quantile_model(train: pd.DataFrame, features: list[str], *, alpha: float) -> Pipeline:
    numeric, categorical = split_types(train, features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="quantile",
            alpha=alpha,
            n_estimators=430,
            learning_rate=0.035,
            num_leaves=31,
            min_child_samples=35,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.2,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def fit_quantile_bundle(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, dict[str, np.ndarray]]:
    train, val, test = normalize_for_model(train, val, test, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    out: dict[str, dict[str, np.ndarray]] = {}
    for name, alpha in [("q10", 0.1), ("q50", 0.5), ("q90", 0.9)]:
        model = lgbm_quantile_model(train, features, alpha=alpha)
        model.fit(train[features], y)
        out[name] = {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    return out


def similarity_preprocessor(ref_frame: pd.DataFrame, features: list[str]) -> ColumnTransformer:
    numeric, categorical = split_types(ref_frame, features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric))
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=5), categorical))
    return ColumnTransformer(transformers)


def reference_stats_from_neighbors(ref_frame: pd.DataFrame, distances: np.ndarray, indices: np.ndarray, prefix: str) -> pd.DataFrame:
    prices = ref_frame["ln_price_krw"].to_numpy(dtype=float)
    area = np.maximum(pd.to_numeric(ref_frame.get("area_cm2", 0.0), errors="coerce").fillna(0.0).to_numpy(dtype=float), 1.0)
    area_price = prices - np.log(area)
    rows = []
    for dist_row, idx_row in zip(distances, indices, strict=True):
        idx = np.asarray(idx_row, dtype=int)
        vals = prices[idx]
        ap_vals = area_price[idx]
        sim = 1.0 / (1.0 + np.asarray(dist_row, dtype=float))
        rows.append({
            f"{prefix}_ref_n": float(len(idx)),
            f"{prefix}_ref_log_price_median": float(np.median(vals)),
            f"{prefix}_ref_log_price_q25": float(np.quantile(vals, 0.25)),
            f"{prefix}_ref_log_price_q75": float(np.quantile(vals, 0.75)),
            f"{prefix}_ref_log_price_iqr": float(np.quantile(vals, 0.75) - np.quantile(vals, 0.25)),
            f"{prefix}_ref_log_price_mean": float(np.mean(vals)),
            f"{prefix}_ref_log_price_std": float(np.std(vals)),
            f"{prefix}_ref_area_price_median": float(np.median(ap_vals)),
            f"{prefix}_ref_similarity_mean": float(np.mean(sim)),
            f"{prefix}_ref_similarity_max": float(np.max(sim)),
            f"{prefix}_ref_similarity_min": float(np.min(sim)),
        })
    return pd.DataFrame(rows)


def compute_reference_stats(
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
        fold_stats = reference_stats_from_neighbors(ref, dist, idx, prefix)
        train_stats.iloc[target_idx] = fold_stats.to_numpy(dtype=float)

    prep = similarity_preprocessor(train, features)
    train_x = prep.fit_transform(train[features])
    nn = NearestNeighbors(n_neighbors=min(top_k, len(train)), metric="cosine")
    nn.fit(train_x)
    val_dist, val_idx = nn.kneighbors(prep.transform(val[features]))
    test_dist, test_idx = nn.kneighbors(prep.transform(test[features]))
    val_stats = reference_stats_from_neighbors(train, val_dist, val_idx, prefix)
    test_stats = reference_stats_from_neighbors(train, test_dist, test_idx, prefix)

    return (
        pd.concat([train.reset_index(drop=True), train_stats.reset_index(drop=True)], axis=1),
        pd.concat([val.reset_index(drop=True), val_stats.reset_index(drop=True)], axis=1),
        pd.concat([test.reset_index(drop=True), test_stats.reset_index(drop=True)], axis=1),
        feature_names,
    )


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, features: list[str], policy: str) -> dict[str, Any]:
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        "n_features": len(features),
    }


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_empty_"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            value = row[col]
            vals.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def html_table(df: pd.DataFrame, cols: list[str]) -> str:
    head = "".join(f"<th>{html.escape(col)}</th>" for col in cols)
    rows = []
    for _, row in df[cols].iterrows():
        cells = []
        for col in cols:
            value = row[col]
            text = f"{value:.6f}" if isinstance(value, float) else str(value)
            cells.append(f"<td>{html.escape(text)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def main() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)

    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    core_features = cmeta["user_meta_core_bucket"][1]
    required = unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    for name, features in [("artwork_only", artwork_features), ("user_meta_core_bucket", core_features)]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")
        if any(feature.startswith("search_") for feature in features):
            raise ValueError(f"{name} includes forbidden search_* feature")
    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix="artwork_sim"
    )
    train_artist, val_artist, test_artist, artist_ref_features = compute_reference_stats(
        train, val, test, ARTIST_SIM_FEATURES, prefix="artist_meta_sim"
    )

    train_both = pd.concat([train_art, train_artist[artist_ref_features]], axis=1)
    val_both = pd.concat([val_art, val_artist[artist_ref_features]], axis=1)
    test_both = pd.concat([test_art, test_artist[artist_ref_features]], axis=1)

    candidates = [
        ("artwork_only", train, val, test, artwork_features, "작품 정보만"),
        ("user_meta_core_bucket", train, val, test, core_features, "작품+사용자 입력 작가 메타 bucket"),
        ("artwork_similarity_stats", train_art, val_art, test_art, unique(core_features + art_ref_features), "작품 유사 비교군 통계 추가"),
        ("artist_meta_similarity_stats", train_artist, val_artist, test_artist, unique(core_features + artist_ref_features), "작가 메타 유사 비교군 통계 추가"),
        ("artist_artwork_similarity_stats", train_both, val_both, test_both, unique(core_features + art_ref_features + artist_ref_features), "작가 메타+작품 유사 비교군 통계 추가"),
    ]

    metric_rows: list[dict[str, Any]] = []
    prediction_rows: list[pd.DataFrame] = []
    for name, tr, va, te, features, policy in candidates:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")
        if any(feature.startswith("search_") for feature in features):
            raise ValueError(f"{name} includes forbidden search_* feature")
        bundle = fit_quantile_bundle(tr, va, te, features)
        for split, frame in [("validation", va), ("test", te)]:
            pred = bundle["q50"][split]
            metric_rows.append(metric_row(name, split, frame, pred, features, policy))
            q10 = bundle["q10"][split]
            q90 = bundle["q90"][split]
            prediction_rows.append(pd.DataFrame({
                "experiment_id": EXP_ID,
                "candidate": name,
                "split": split,
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
                "actual_price": frame["price_krw"].to_numpy(dtype=float),
                "pred_log": pred,
                "pred_price": np.exp(pred),
                "q10_log": q10,
                "q90_log": q90,
                "quantile_width_log": np.maximum(q90 - q10, 0.0),
                "policy": policy,
                "n_features": len(features),
            }))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(prediction_rows, ignore_index=True)

    strict_audit = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_user_enterable_artist_meta": True,
        "uses_similarity_reference_stats": True,
        "reference_pool": "train only; train rows use out-of-fold reference stats",
        "top_k": TOP_K,
        "oof_splits": OOF_SPLITS,
        "candidate_count": len(candidates),
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(strict_audit), ensure_ascii=False, indent=2), encoding="utf-8")

    cols = ["candidate", "split", "policy", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "n_features"]
    test_df = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    validation_df = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    best_mdape_test = test_df.iloc[0].to_dict()
    stable_test = test_df.sort_values(["p95_APE", "MAPE", "RMSE_log"]).iloc[0].to_dict()

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {strict_audit['created_at']}",
        "- 목적: strict Cold에서 비슷한 작품, 비슷한 작가, 비슷한 작가의 비슷한 작품 기준가격 통계가 성능을 높이는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 학습 행의 유사 비교군 통계는 KFold out-of-fold로 생성해 자기 가격 누수를 차단했다.",
        "- validation/test의 유사 비교군 통계는 train 데이터만 기준으로 생성했다.",
        "",
        "## 1. Test 결과",
        md_table(test_df, cols),
        "",
        "## 2. Validation 결과",
        md_table(validation_df, cols),
        "",
        "## 3. 해석",
        "",
        f"- test MdAPE 기준 최상위 후보는 `{best_mdape_test['candidate']}`이다.",
        f"- test p95/MAPE 안정성 기준 최상위 후보는 `{stable_test['candidate']}`이다.",
        "- `artwork_similarity_stats`는 입력 작품과 비슷한 train 작품들의 가격 분포를 추가한다.",
        "- `artist_meta_similarity_stats`는 사용자가 입력 가능한 작가 메타가 비슷한 train 작가군의 가격 분포를 추가한다.",
        "- `artist_artwork_similarity_stats`는 위 두 기준을 함께 넣은 후보로, 비슷한 작가의 비슷한 작품이라는 설명 가능한 Cold 기준가격 구조에 가장 가깝다.",
        "- 이번 1차 실험에서는 작품 유사 비교군이 중앙 오차(MdAPE)는 낮췄지만, user_meta_core_bucket 대비 MAPE/p95/RMSE는 나빠졌다.",
        "- 작가 메타 유사 비교군과 작가+작품 결합 유사 비교군은 tail이 크게 악화되어, 현재 방식 그대로는 운영 후보로 보기 어렵다.",
        "- 따라서 현재 운영 후보는 user_meta_core_bucket을 유지하고, 유사작품 통계는 별도 보조 피처 또는 라우터 후보로 후속 검증하는 것이 맞다.",
        "- 이 실험 결과가 좋더라도 동일 작가를 직접 찾은 성능이 아니라, strict Cold 조건에서 train 비교군을 검색해 만든 보조 통계 성능으로 해석해야 한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}code{{background:#f3f4f6;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<p>strict Cold 조건에서 유사 비교군 통계 피처의 효과를 검증했다.</p>
<h2>Test 결과</h2>{html_table(test_df, cols)}
<h2>Validation 결과</h2>{html_table(validation_df, cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(strict_audit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
