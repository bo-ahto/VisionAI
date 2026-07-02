#!/usr/bin/env python3
"""PP-CSIM19: limited k320-combined policy for Cold tail defense.

PP-CSIM18 showed that k320 combined improves MAPE and APE > 5 but increases
APE > 2 and worsens MdAPE/p95.  This experiment does not promote k320 globally.
Instead, it uses k320 only for inference-time low/overprediction-risk rows.

Strict Cold contract:
- no artist_key feature
- no same-artist price history feature
- no artist_key lookup postprocess
- no search_* or external live search features
- no policy uses actual price
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

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import META_BUCKET_FEATURES, USER_META_CORE, load_user_meta_frames  # noqa: E402
from run_pp_cmeta5_user_meta_robustness_validation import MISSING_SCENARIOS, apply_missing_scenario, paired_bootstrap  # noqa: E402
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
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM19"
SLUG = "PP-CSIM19_cold_k320_limited_policy"
TITLE = "Cold k320 제한 적용 정책 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim19_cold_k320_limited_policy_summary.md"

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


def fit_model(train: pd.DataFrame, features: list[str]):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    model = lgbm_quantile_model(train_n, features, alpha=0.35)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return model


def predict_model(model: Any, train: pd.DataFrame, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    _, frame_n, _ = normalize_for_model(train.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
    return np.asarray(model.predict(frame_n[features]), dtype=float)


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


def policy_masks(frame: pd.DataFrame, base_pred: np.ndarray, k320_pred: np.ndarray) -> dict[str, tuple[np.ndarray, str]]:
    ref_med = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_median"), errors="coerce").to_numpy(dtype=float)
    ref_q25 = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_q25"), errors="coerce").to_numpy(dtype=float)
    ref_iqr = pd.to_numeric(frame.get("artwork_sim_k160_ref_log_price_iqr"), errors="coerce").fillna(0.0).to_numpy(dtype=float)
    base_price = np.exp(base_pred)
    ref_med_price = np.exp(ref_med)
    k320_lower = (base_pred - k320_pred) > 0.05
    k320_not_much_higher = (k320_pred - base_pred) < 0.05
    low_pred_300w = base_price < 3_000_000
    low_pred_500w = base_price < 5_000_000
    low_ref_300w = np.isfinite(ref_med_price) & (ref_med_price < 3_000_000)
    low_ref_500w = np.isfinite(ref_med_price) & (ref_med_price < 5_000_000)
    above_ref_q25 = np.isfinite(ref_q25) & ((base_pred - ref_q25) > 0.20)
    above_ref_med = np.isfinite(ref_med) & ((base_pred - ref_med) > 0.15)
    high_iqr = ref_iqr > 0.90
    return {
        "base_k160": (np.zeros(len(frame), dtype=bool), "항상 k160 q35 기준선"),
        "k320_global": (np.ones(len(frame), dtype=bool), "항상 k320 combined q35"),
        "low_pred_300w_and_k320_lower": (
            low_pred_300w & k320_lower,
            "k160 예측가 300만원 미만이고 k320이 0.05 log 이상 낮으면 k320",
        ),
        "low_pred_500w_and_k320_lower": (
            low_pred_500w & k320_lower,
            "k160 예측가 500만원 미만이고 k320이 0.05 log 이상 낮으면 k320",
        ),
        "low_ref_300w_and_k320_lower": (
            low_ref_300w & k320_lower,
            "유사작품 중앙 기준가 300만원 미만이고 k320이 0.05 log 이상 낮으면 k320",
        ),
        "low_ref_500w_and_k320_lower": (
            low_ref_500w & k320_lower,
            "유사작품 중앙 기준가 500만원 미만이고 k320이 0.05 log 이상 낮으면 k320",
        ),
        "above_refq25_and_k320_lower": (
            above_ref_q25 & k320_lower,
            "k160 예측이 유사작품 q25보다 0.20 log 이상 높고 k320이 더 낮으면 k320",
        ),
        "low_or_above_ref_and_k320_lower": (
            (low_pred_500w | low_ref_500w | above_ref_q25 | above_ref_med) & k320_lower,
            "저가 또는 유사작품 대비 과대 후보이고 k320이 0.05 log 이상 낮으면 k320",
        ),
        "low_or_above_ref_and_k320_not_higher": (
            (low_pred_500w | low_ref_500w | above_ref_q25 | above_ref_med) & k320_not_much_higher,
            "저가 또는 유사작품 대비 과대 후보이고 k320이 크게 높지 않으면 k320",
        ),
        "high_iqr_above_ref_and_k320_lower": (
            high_iqr & (above_ref_q25 | above_ref_med) & k320_lower,
            "유사작품 분산이 크고 과대 후보이며 k320이 더 낮으면 k320",
        ),
    }


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


def stress_metrics(candidates: dict[str, dict[str, Any]], base_pack: dict[str, Any], k320_pack: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for scenario, fields in MISSING_SCENARIOS.items():
        for split in ["validation", "test"]:
            base_frame = apply_missing_scenario(base_pack[f"{split}_frame"], fields)
            k320_frame = apply_missing_scenario(k320_pack[f"{split}_frame"], fields)
            base_pred = predict_model(base_pack["model"], base_pack["train_frame"], base_frame, base_pack["features"])
            k320_pred = predict_model(k320_pack["model"], k320_pack["train_frame"], k320_frame, k320_pack["features"])
            masks = policy_masks(base_frame, base_pred, k320_pred)
            for name, pack in candidates.items():
                mask, policy = masks[name]
                pred = np.where(mask, k320_pred, base_pred)
                rows.append({
                    "experiment_id": EXP_ID,
                    "candidate": name,
                    "split": split,
                    "stress_scenario": scenario,
                    "missing_fields": ",".join(fields),
                    "n_missing_fields": len(fields),
                    "k320_selected_rate": float(np.mean(mask)),
                    "policy": policy,
                    **metrics(base_frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
                    **tail_counts(base_frame, pred),
                })
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, stress_df: pd.DataFrame, summary: dict[str, Any]) -> None:
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
    stress_cols = ["candidate", "stress_scenario", "split", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10", "k320_selected_rate"]
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE"]).head(16)
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["APE_gt_5", "MAPE", "p95_APE"]).head(16)
    test_seg = seg_df[seg_df["split"].eq("test") & seg_df["candidate"].isin(test["candidate"].head(8))].sort_values(["segment", "candidate"])
    test_stress = stress_df[stress_df["split"].eq("test") & stress_df["candidate"].isin(test["candidate"].head(6))].sort_values(["stress_scenario", "candidate"])
    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: k320 combined를 전체 적용하지 않고 저가/과대예측 위험 구간에만 적용할 때 개선되는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 모든 정책은 실제 가격을 보지 않고 사용 단계에서 알 수 있는 예측가와 유사작품 통계만 사용한다.",
        "",
        "## 1. Test 성능: APE > 5 기준",
        md_table(test, metric_cols),
        "",
        "## 2. Validation 성능: APE > 5 기준",
        md_table(val, metric_cols),
        "",
        "## 3. Paired bootstrap vs base_k160",
        md_table(boot_df, boot_cols),
        "",
        "## 4. Test 가격대별 진단",
        md_table(test_seg, seg_cols),
        "",
        "## 5. Test 결측 스트레스",
        md_table(test_stress, stress_cols),
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 성능</h2>{html_table(test, metric_cols)}
<h2>Validation 성능</h2>{html_table(val, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>Test 가격대별 진단</h2>{html_table(test_seg, seg_cols)}
<h2>Test 결측 스트레스</h2>{html_table(test_stress, stress_cols)}
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

    base_pack = {
        "train_frame": train160,
        "validation_frame": val160,
        "test_frame": test160,
        "features": unique(enterable_base + ref160),
    }
    k320_pack = {
        "train_frame": train320c,
        "validation_frame": val320c,
        "test_frame": test320c,
        "features": unique(enterable_base + ref320 + ref320w),
    }
    base_pack["model"] = fit_model(base_pack["train_frame"], base_pack["features"])
    k320_pack["model"] = fit_model(k320_pack["train_frame"], k320_pack["features"])

    split_packs: dict[str, dict[str, Any]] = {}
    for split in ["validation", "test"]:
        base_pred = predict_model(base_pack["model"], base_pack["train_frame"], base_pack[f"{split}_frame"], base_pack["features"])
        k320_pred = predict_model(k320_pack["model"], k320_pack["train_frame"], k320_pack[f"{split}_frame"], k320_pack["features"])
        split_packs[split] = {
            "frame": base_pack[f"{split}_frame"],
            "base_pred": base_pred,
            "k320_pred": k320_pred,
            "masks": policy_masks(base_pack[f"{split}_frame"], base_pred, k320_pred),
        }

    candidates = {name: {"policy": policy} for name, (_mask, policy) in split_packs["validation"]["masks"].items()}
    metric_rows = []
    pred_frames = []
    for split, pack in split_packs.items():
        for name, (mask, policy) in pack["masks"].items():
            pred = np.where(mask, pack["k320_pred"], pack["base_pred"])
            metric_rows.append(metric_row(name, split, pack["frame"], pred, policy, mask))
            pred_frames.append(prediction_frame(name, split, pack["frame"], pred, policy, mask))
    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    seg_df = segment_summary(predictions_df)

    boot_rows = []
    for split, pack in split_packs.items():
        base_pred = pack["base_pred"]
        frame = pack["frame"]
        for name, (mask, _policy) in pack["masks"].items():
            if name == "base_k160":
                continue
            pred = np.where(mask, pack["k320_pred"], pack["base_pred"])
            boot_rows.append(paired_bootstrap(
                frame,
                pred,
                base_pred,
                a_name=name,
                b_name="base_k160",
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)
    stress_df = stress_metrics(candidates, base_pack, k320_pack)

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
        "candidate_count": len(candidates),
        "baseline": "base_k160",
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_base_k160.csv", index=False)
    stress_df.to_csv(OUT / "missingness_stress_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, boot_df, seg_df, stress_df, summary)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
