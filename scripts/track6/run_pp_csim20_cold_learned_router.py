#!/usr/bin/env python3
"""PP-CSIM20: learned router on top of the best Cold candidates.

PP-CSIM19 found a useful rule-based limited k320 policy.  This experiment
checks whether a learned router can improve further by choosing between:

- base_k160: q35 k160 unweighted similar-artwork model
- k320_combined: q35 k320 unweighted + weighted similar-artwork model

The router is trained only from train OOF candidate predictions.  Validation
and test labels are never used to fit or select the learned router.

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
from lightgbm import LGBMClassifier
from sklearn.model_selection import KFold

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import META_BUCKET_FEATURES, USER_META_CORE, load_user_meta_frames  # noqa: E402
from run_pp_cmeta5_user_meta_robustness_validation import paired_bootstrap  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    html_table,
    json_clean,
    lgbm_quantile_model,
    md_table,
    normalize_for_model,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pp_csim16_cold_improvement_suite import compute_weighted_reference_stats  # noqa: E402
from run_pp_csim19_cold_k320_limited_policy import policy_masks  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM20"
SLUG = "PP-CSIM20_cold_learned_router"
TITLE = "Cold 학습형 k160/k320 라우터 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim20_cold_learned_router_summary.md"

N_SPLITS = 5

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

ROUTER_SIGNAL_COLS = [
    "base_pred",
    "k320_pred",
    "k320_minus_base",
    "base_price",
    "k320_price",
    "base_minus_ref_median",
    "base_minus_ref_q25",
    "ref_iqr",
    "ref_std",
    "ref_similarity_mean",
    "width_cm",
    "height_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "artist_meta_birth_year",
    "artist_meta_career_stage",
    "artist_meta_birth_year_missing",
    "artist_meta_career_stage_missing",
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def fit_model(train: pd.DataFrame, features: list[str]):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    model = lgbm_quantile_model(train_n, features, alpha=0.35)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return model


def predict_model(model: Any, train: pd.DataFrame, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    _, frame_n, _ = normalize_for_model(train.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
    return np.asarray(model.predict(frame_n[features]), dtype=float)


def oof_predictions(frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    out = np.full(len(frame), np.nan, dtype=float)
    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    for train_idx, target_idx in kf.split(frame):
        fold_train = frame.iloc[train_idx].copy()
        fold_target = frame.iloc[target_idx].copy()
        model = fit_model(fold_train, features)
        out[target_idx] = predict_model(model, fold_train, fold_target, features)
    if np.isnan(out).any():
        raise ValueError("OOF prediction contains NaN")
    return out


def candidate_ape(frame: pd.DataFrame, pred: np.ndarray) -> np.ndarray:
    actual = pd.to_numeric(frame["price_krw"], errors="coerce").to_numpy(dtype=float)
    return np.abs(np.exp(pred) - actual) / np.maximum(actual, 1.0)


def router_features(frame: pd.DataFrame, base_pred: np.ndarray, k320_pred: np.ndarray) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    out["base_pred"] = base_pred
    out["k320_pred"] = k320_pred
    out["k320_minus_base"] = k320_pred - base_pred
    out["base_price"] = np.exp(base_pred)
    out["k320_price"] = np.exp(k320_pred)
    ref_median = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_median"), errors="coerce")
    ref_q25 = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_q25"), errors="coerce")
    out["base_minus_ref_median"] = base_pred - ref_median.to_numpy(dtype=float)
    out["base_minus_ref_q25"] = base_pred - ref_q25.to_numpy(dtype=float)
    for src, dst in [
        ("artwork_sim_k160_ref_log_price_iqr", "ref_iqr"),
        ("artwork_sim_k160_ref_log_price_std", "ref_std"),
        ("artwork_sim_k160_ref_similarity_mean", "ref_similarity_mean"),
    ]:
        out[dst] = pd.to_numeric(frame.get(src), errors="coerce")
    for col in [
        "width_cm",
        "height_cm",
        "area_cm2",
        "log_area",
        "aspect_ratio",
        "artist_meta_birth_year",
        "artist_meta_career_stage",
        "artist_meta_birth_year_missing",
        "artist_meta_career_stage_missing",
    ]:
        out[col] = pd.to_numeric(frame.get(col), errors="coerce")
    return out[ROUTER_SIGNAL_COLS]


def router_model() -> LGBMClassifier:
    return LGBMClassifier(
        objective="binary",
        n_estimators=260,
        learning_rate=0.035,
        num_leaves=15,
        min_child_samples=120,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=3.0,
        class_weight="balanced",
        random_state=SEED,
        verbosity=-1,
    )


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, selected: np.ndarray | None = None) -> dict[str, Any]:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
    }
    if selected is not None:
        row["k320_selected_rate"] = float(np.mean(selected))
        row["k320_selected_n"] = int(np.sum(selected))
    return row


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, selected: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "k320_selected": selected.astype(int),
        "policy": policy,
    })


def segment_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, split), df in predictions.groupby(["candidate", "split"], observed=False):
        work = df.copy()
        work["actual_price_band"] = pd.cut(
            pd.to_numeric(work["actual_price"], errors="coerce"),
            bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
            labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
            include_lowest=True,
        ).astype("string")
        for segment, group in work.groupby("actual_price_band", observed=False):
            pred = group["pred_log"].to_numpy(dtype=float)
            rows.append({
                "candidate": candidate,
                "split": split,
                "segment": str(segment),
                "n": int(len(group)),
                "k320_selected_rate": float(group["k320_selected"].mean()),
                **metrics(
                    group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                    ),
                    pred,
                ),
                **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
            })
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, router_diag: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "APE_gt_2", "APE_gt_5", "APE_gt_10", "k320_selected_rate", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "k320_selected_rate", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]
    diag_cols = ["split", "threshold", "selected_rate", "selected_q320_win_rate", "overall_q320_win_rate"]
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"])
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["APE_gt_5", "MAPE", "p95_APE"])
    focus = ["base_k160", "rule_low_or_above_ref_and_k320_lower", "learned_router_t60", "learned_router_t70", "oracle_best_of_two"]
    test_seg = seg_df[seg_df["split"].eq("test") & seg_df["candidate"].isin(focus)].sort_values(["segment", "candidate"])
    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: 가장 유력한 Cold 후보 위에 학습형 라우터를 붙여 rule 기반 제한 정책보다 개선되는지 확인한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 학습형 라우터는 train OOF 후보 예측으로만 학습했다. validation/test 정답은 라우터 학습에 쓰지 않았다.",
        "",
        "## 1. Test 성능",
        md_table(test, metric_cols),
        "",
        "## 2. Validation 성능",
        md_table(val, metric_cols),
        "",
        "## 3. Paired bootstrap vs base_k160",
        md_table(boot_df, boot_cols),
        "",
        "## 4. Router 진단",
        md_table(router_diag, diag_cols),
        "",
        "## 5. Test 가격대별 진단",
        md_table(test_seg, seg_cols),
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 성능</h2>{html_table(test, metric_cols)}
<h2>Validation 성능</h2>{html_table(val, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>Router 진단</h2>{html_table(router_diag, diag_cols)}
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

    train160, val160, test160, ref160 = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix="artwork_sim_k160", top_k=160
    )
    train320, val320, test320, ref320 = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix="artwork_sim_k320", top_k=320
    )
    train320w, val320w, test320w, ref320w = compute_weighted_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix="artwork_wsim_k320", top_k=320
    )
    train320c = pd.concat([train320.reset_index(drop=True), train320w[ref320w].reset_index(drop=True)], axis=1)
    val320c = pd.concat([val320.reset_index(drop=True), val320w[ref320w].reset_index(drop=True)], axis=1)
    test320c = pd.concat([test320.reset_index(drop=True), test320w[ref320w].reset_index(drop=True)], axis=1)

    base_features = unique(enterable_base + ref160)
    k320_features = unique(enterable_base + ref320 + ref320w)

    base_oof = oof_predictions(train160, base_features)
    k320_oof = oof_predictions(train320c, k320_features)
    base_model = fit_model(train160, base_features)
    k320_model = fit_model(train320c, k320_features)
    base_pred = {
        "validation": predict_model(base_model, train160, val160, base_features),
        "test": predict_model(base_model, train160, test160, base_features),
    }
    k320_pred = {
        "validation": predict_model(k320_model, train320c, val320c, k320_features),
        "test": predict_model(k320_model, train320c, test320c, k320_features),
    }

    oof_base_ape = candidate_ape(train160, base_oof)
    oof_k320_ape = candidate_ape(train160, k320_oof)
    train_target = (oof_k320_ape + 0.02 < oof_base_ape).astype(int)
    router_train_x = router_features(train160, base_oof, k320_oof).fillna(-9999)
    router = router_model()
    router.fit(router_train_x, train_target)

    metrics_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    router_diag_rows: list[dict[str, Any]] = []
    boot_rows = []
    candidates_by_split: dict[str, dict[str, tuple[np.ndarray, np.ndarray, str]]] = {}
    for split, frame in [("validation", val160), ("test", test160)]:
        router_x = router_features(frame, base_pred[split], k320_pred[split]).fillna(-9999)
        prob = np.asarray(router.predict_proba(router_x)[:, 1], dtype=float)
        masks = policy_masks(frame, base_pred[split], k320_pred[split])
        split_candidates: dict[str, tuple[np.ndarray, np.ndarray, str]] = {
            "base_k160": (base_pred[split], np.zeros(len(frame), dtype=bool), "항상 k160 q35"),
            "k320_global": (k320_pred[split], np.ones(len(frame), dtype=bool), "항상 k320 combined q35"),
        }
        rule_mask = masks["low_or_above_ref_and_k320_lower"][0]
        split_candidates["rule_low_or_above_ref_and_k320_lower"] = (
            np.where(rule_mask, k320_pred[split], base_pred[split]),
            rule_mask,
            "저가/과대 후보이고 k320이 0.05 log 이상 낮으면 k320",
        )
        for threshold in [0.50, 0.60, 0.70, 0.80]:
            mask = prob >= threshold
            split_candidates[f"learned_router_t{int(threshold * 100)}"] = (
                np.where(mask, k320_pred[split], base_pred[split]),
                mask,
                f"학습형 라우터 확률 {threshold:.2f} 이상이면 k320",
            )
        base_ape = candidate_ape(frame, base_pred[split])
        k320_ape = candidate_ape(frame, k320_pred[split])
        oracle_mask = k320_ape < base_ape
        split_candidates["oracle_best_of_two"] = (
            np.where(oracle_mask, k320_pred[split], base_pred[split]),
            oracle_mask,
            "진단용 oracle: 실제 정답 기준 더 낮은 APE 후보 선택",
        )
        for threshold in [0.50, 0.60, 0.70, 0.80]:
            mask = prob >= threshold
            router_diag_rows.append({
                "split": split,
                "threshold": threshold,
                "selected_rate": float(np.mean(mask)),
                "selected_q320_win_rate": float(np.mean(oracle_mask[mask])) if np.any(mask) else 0.0,
                "overall_q320_win_rate": float(np.mean(oracle_mask)),
            })
        for name, (pred, mask, policy) in split_candidates.items():
            metrics_rows.append(metric_row(name, split, frame, pred, policy, mask))
            pred_frames.append(prediction_frame(name, split, frame, pred, policy, mask))
        candidates_by_split[split] = split_candidates

    metrics_df = pd.DataFrame(metrics_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    seg_df = segment_summary(predictions_df)
    router_diag = pd.DataFrame(router_diag_rows)

    for split, frame in [("validation", val160), ("test", test160)]:
        base = candidates_by_split[split]["base_k160"][0]
        for name, (pred, _mask, _policy) in candidates_by_split[split].items():
            if name == "base_k160":
                continue
            boot_rows.append(paired_bootstrap(
                frame,
                pred,
                base,
                a_name=name,
                b_name="base_k160",
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
        "router_used": True,
        "router_type": "learned_oof_binary_classifier",
        "router_training_uses_validation_or_test_labels": False,
        "router_uses_actual_price_at_inference": False,
        "oof_k320_win_rate": float(np.mean(train_target)),
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_base_k160.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    router_diag.to_csv(OUT / "router_diagnostics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, boot_df, seg_df, router_diag, summary)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
