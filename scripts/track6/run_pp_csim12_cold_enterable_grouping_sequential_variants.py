#!/usr/bin/env python3
"""PP-CSIM12: Cold enterable grouping and sequential-model variants.

This experiment keeps strict Cold constraints and the operationally preferred
enterable metadata set, then tests whether accuracy improves by changing:

- similar-artwork group size: k80/k160/k320
- multi-scale grouping: k80+k160+k320 reference stats together
- sequential training: q45 basis + clipped residual correction
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import META_BUCKET_FEATURES, USER_META_CORE, load_user_meta_frames  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    html_table,
    json_clean,
    lgbm_quantile_model,
    md_table,
    normalize_for_model,
    split_types,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM12"
SLUG = "PP-CSIM12_cold_enterable_grouping_sequential_variants"
TITLE = "Cold enterable 그룹핑/순차 학습 변형 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim12_cold_enterable_grouping_sequential_variants_summary.md"

TOP_KS = [80, 160, 320]
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


def fit_quantile(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    *,
    alpha: float,
) -> dict[str, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return {
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
    }


def lgbm_regression_model(train: pd.DataFrame, features: list[str]) -> Pipeline:
    numeric, categorical = split_types(train, features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="regression",
            n_estimators=360,
            learning_rate=0.035,
            num_leaves=24,
            min_child_samples=45,
            subsample=0.9,
            colsample_bytree=0.85,
            reg_lambda=2.0,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def fit_oof_quantile_basis(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    *,
    alpha: float = 0.45,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    y = train_n["ln_price_krw"].to_numpy(dtype=float)
    oof = np.zeros(len(train_n), dtype=float)
    kf = KFold(n_splits=OOF_SPLITS, shuffle=True, random_state=SEED)
    for tr_idx, hold_idx in kf.split(train_n):
        fold_train = train_n.iloc[tr_idx].copy()
        fold_hold = train_n.iloc[hold_idx].copy()
        model = lgbm_quantile_model(fold_train, features, alpha=alpha)
        model.fit(fold_train[features], y[tr_idx])
        oof[hold_idx] = np.asarray(model.predict(fold_hold[features]), dtype=float)
    final_model = lgbm_quantile_model(train_n, features, alpha=alpha)
    final_model.fit(train_n[features], y)
    return (
        oof,
        np.asarray(final_model.predict(val_n[features]), dtype=float),
        np.asarray(final_model.predict(test_n[features]), dtype=float),
    )


def sequential_residual_candidate(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    *,
    strength: float,
    cap: float,
) -> dict[str, np.ndarray]:
    train_basis, val_basis, test_basis = fit_oof_quantile_basis(train, val, test, features, alpha=0.45)
    train_seq = train.copy()
    val_seq = val.copy()
    test_seq = test.copy()
    for frame, basis in [(train_seq, train_basis), (val_seq, val_basis), (test_seq, test_basis)]:
        frame["basis_q45_log"] = basis
        ref_median = pd.to_numeric(
            frame.get("artwork_sim_k160_ref_log_price_median", pd.Series(np.nan, index=frame.index)),
            errors="coerce",
        ).to_numpy(dtype=float)
        ref_median = np.where(np.isfinite(ref_median), ref_median, basis)
        frame["basis_minus_ref_median"] = basis - ref_median
    residual_features = unique(features + ["basis_q45_log", "basis_minus_ref_median"])
    train_n, val_n, test_n = normalize_for_model(train_seq, val_seq, test_seq, residual_features)
    residual_y = train_n["ln_price_krw"].to_numpy(dtype=float) - train_basis
    model = lgbm_regression_model(train_n, residual_features)
    model.fit(train_n[residual_features], residual_y)
    val_resid = np.asarray(model.predict(val_n[residual_features]), dtype=float)
    test_resid = np.asarray(model.predict(test_n[residual_features]), dtype=float)
    return {
        "validation": val_basis + np.clip(strength * val_resid, -cap, cap),
        "test": test_basis + np.clip(strength * test_resid, -cap, cap),
    }


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


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "policy": policy,
    })


def segment_summary(predictions: pd.DataFrame, candidate: str, split: str) -> pd.DataFrame:
    df = predictions[predictions["candidate"].eq(candidate) & predictions["split"].eq(split)].copy()
    if df.empty:
        return pd.DataFrame()
    df["actual_price_band"] = pd.cut(
        pd.to_numeric(df["actual_price"], errors="coerce"),
        bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
        labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
        include_lowest=True,
    ).astype("string")
    rows = []
    for segment, group in df.groupby("actual_price_band", dropna=False, observed=False):
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


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    artwork_features = unique(fs["cold_lgb"])
    required = unique(artwork_features + USER_META_CORE + META_BUCKET_FEATURES + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    enterable_base = unique(artwork_features + ENTERABLE_META + ENTERABLE_BUCKETS)
    assert_strict_cold_features(enterable_base, context=f"{EXP_ID}:enterable_base")

    frames_by_k: dict[int, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]] = {}
    all_ref_features: list[str] = []
    train_multi, val_multi, test_multi = train.copy(), val.copy(), test.copy()
    for top_k in TOP_KS:
        tr, va, te, ref_features = compute_reference_stats(
            train,
            val,
            test,
            ARTWORK_SIM_FEATURES,
            prefix=f"artwork_sim_k{top_k}",
            top_k=top_k,
        )
        frames_by_k[top_k] = (tr, va, te, ref_features)
        all_ref_features.extend(ref_features)
        for feature in ref_features:
            train_multi[feature] = tr[feature].to_numpy()
            val_multi[feature] = va[feature].to_numpy()
            test_multi[feature] = te[feature].to_numpy()

    candidates: list[tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str], str, dict[str, Any], str]] = []
    for top_k in TOP_KS:
        tr, va, te, ref_features = frames_by_k[top_k]
        candidates.append((
            f"enterable_k{top_k}_q45",
            tr,
            va,
            te,
            unique(enterable_base + ref_features),
            f"enterable + 유사작품 k{top_k} 통계 + LightGBM q45",
            {"top_k": top_k, "alpha": 0.45, "model_type": "quantile"},
            "quantile",
        ))
    multi_features = unique(enterable_base + all_ref_features)
    candidates.append((
        "enterable_multi_k80_160_320_q45",
        train_multi,
        val_multi,
        test_multi,
        multi_features,
        "enterable + 유사작품 k80/k160/k320 통계 동시 사용 + LightGBM q45",
        {"top_k": "80,160,320", "alpha": 0.45, "model_type": "quantile"},
        "quantile",
    ))
    tr160, va160, te160, ref160 = frames_by_k[160]
    features160 = unique(enterable_base + ref160)
    for strength, cap in [(0.50, 0.05), (0.50, 0.10), (0.35, 0.08)]:
        candidates.append((
            f"enterable_k160_q45_residual_s{str(strength).replace('.', 'p')}_cap{str(cap).replace('.', 'p')}",
            tr160,
            va160,
            te160,
            features160,
            f"k160 q45 기준가격 + LightGBM residual * {strength} clip ±{cap}",
            {"top_k": 160, "alpha": 0.45, "model_type": "q45_plus_residual", "residual_strength": strength, "residual_cap": cap},
            "sequential",
        ))

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for name, tr, va, te, features, policy, extra, mode in candidates:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")
        if mode == "quantile":
            preds = fit_quantile(tr, va, te, features, alpha=float(extra["alpha"]))
        else:
            preds = sequential_residual_candidate(
                tr,
                va,
                te,
                features,
                strength=float(extra["residual_strength"]),
                cap=float(extra["residual_cap"]),
            )
        for split, frame in [("validation", va), ("test", te)]:
            pred = preds[split]
            metric_rows.append(metric_row(name, split, frame, pred, policy, extra))
            pred_frames.append(prediction_frame(name, split, frame, pred, policy))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    segment_df = pd.concat([
        segment_summary(predictions_df, candidate, "test")
        for candidate in metrics_df[metrics_df["split"].eq("test")]["candidate"].unique()
    ], ignore_index=True)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "router_used": False,
        "grouping_and_sequential_variants": True,
        "top_ks": TOP_KS,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    segment_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10",
        "top_k", "model_type", "policy",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5"]
    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    tail_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "p95_APE", "MAPE"])
    best_mdape = test_metrics.iloc[0]["candidate"]
    best_tail = tail_metrics.iloc[0]["candidate"]

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: 현재 권장 Cold 후보인 enterable_only 계열에서 유사작품 그룹핑과 순차 잔차 보정 변형으로 성능 개선 여지를 확인한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "",
        "## 1. Test 결과: MdAPE 기준",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Test 결과: APE > 5 기준",
        md_table(tail_metrics, metric_cols),
        "",
        "## 3. 가격대별 진단",
        md_table(segment_df.sort_values(["segment", "candidate"]), seg_cols),
        "",
        "## 4. 결론",
        "",
        f"- MdAPE 기준 최상위 후보는 `{best_mdape}`이다.",
        f"- APE > 5 안정성 기준 최상위 후보는 `{best_tail}`이다.",
        "- 순차 residual 후보는 q45 기준가격을 먼저 만든 뒤, OOF basis residual을 학습하고 clip된 보정만 더한다.",
        "- 최종 채택은 MdAPE/MAPE 개선뿐 아니라 p95와 APE > 5 악화 여부를 함께 봐야 한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 결과: MdAPE 기준</h2>{html_table(test_metrics, metric_cols)}
<h2>Test 결과: APE &gt; 5 기준</h2>{html_table(tail_metrics, metric_cols)}
<h2>가격대별 진단</h2>{html_table(segment_df.sort_values(['segment', 'candidate']), seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
