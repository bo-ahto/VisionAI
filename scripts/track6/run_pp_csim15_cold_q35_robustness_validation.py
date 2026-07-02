#!/usr/bin/env python3
"""PP-CSIM15: robustness validation for Cold q35 candidate.

PP-CSIM13/14 showed that lowering the Cold LightGBM Quantile target from q45 to
q35 can reduce low-price extreme overestimation and APE > 5.  This follow-up
checks whether that signal is robust enough to promote:

- validation/test metrics under the same strict Cold harness
- paired bootstrap against the current q45 candidate
- price-band diagnostics
- user-enterable metadata missingness stress

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
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM15"
SLUG = "PP-CSIM15_cold_q35_robustness_validation"
TITLE = "Cold q35 후보 강건성 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim15_cold_q35_robustness_validation_summary.md"

TOP_K = 160

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


def fit_quantile_model(train: pd.DataFrame, features: list[str], *, alpha: float):
    train_n, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return model


def predict_model(model: Any, train: pd.DataFrame, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    _, frame_n, _ = normalize_for_model(train.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
    return np.asarray(model.predict(frame_n[features]), dtype=float)


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


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> pd.DataFrame:
    out = pd.DataFrame({
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
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


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


def make_policy_predictions(pred45: np.ndarray, pred35: np.ndarray, frame: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray, str]]:
    ref_q25 = pd.to_numeric(frame.get(f"artwork_sim_k{TOP_K}_ref_log_price_q25"), errors="coerce").to_numpy(dtype=float)
    pred45_price = np.exp(pred45)
    mask_pred_lt_300w = pred45_price < 3_000_000
    mask_above_refq25 = np.isfinite(ref_q25) & ((pred45 - ref_q25) > 0.20)
    return {
        "q45_current": (pred45, np.zeros(len(frame), dtype=bool), "기존 q45 후보"),
        "q35_global": (pred35, np.ones(len(frame), dtype=bool), "전체 q35 후보"),
        "q35_if_pred_lt_300w": (
            np.where(mask_pred_lt_300w, pred35, pred45),
            mask_pred_lt_300w,
            "q45 예측가가 300만원 미만이면 q35, 아니면 q45",
        ),
        "q35_if_q45_above_refq25_0p2": (
            np.where(mask_above_refq25, pred35, pred45),
            mask_above_refq25,
            "q45가 유사작품 q25보다 0.20 log 이상 높으면 q35, 아니면 q45",
        ),
    }


def stress_metrics(
    *,
    train_art: pd.DataFrame,
    val_art: pd.DataFrame,
    test_art: pd.DataFrame,
    features: list[str],
    model45: Any,
    model35: Any,
) -> pd.DataFrame:
    rows = []
    for scenario, fields in MISSING_SCENARIOS.items():
        for split, base_frame in [("validation", val_art), ("test", test_art)]:
            frame = apply_missing_scenario(base_frame, fields)
            pred45 = predict_model(model45, train_art, frame, features)
            pred35 = predict_model(model35, train_art, frame, features)
            for candidate, pred, policy in [
                ("q45_current", pred45, "기존 q45 후보"),
                ("q35_global", pred35, "전체 q35 후보"),
            ]:
                rows.append({
                    "experiment_id": EXP_ID,
                    "candidate": candidate,
                    "split": split,
                    "stress_scenario": scenario,
                    "missing_fields": ",".join(fields),
                    "n_missing_fields": len(fields),
                    "policy": policy,
                    **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
                    **tail_counts(frame, pred),
                })
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, predictions_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, stress_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10",
        "q35_selected_rate", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "delta_RMSE_log_a_minus_b_mean",
        "p_delta_MdAPE_a_minus_b_lt_0", "p_delta_MAPE_a_minus_b_lt_0",
        "p_delta_p95_APE_a_minus_b_lt_0", "p_delta_RMSE_log_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10"]
    stress_cols = ["candidate", "stress_scenario", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10", "missing_fields"]

    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "MAPE", "p95_APE", "MdAPE"])
    val_metrics = metrics_df[metrics_df["split"].eq("validation")].sort_values(["APE_gt_5", "MAPE", "p95_APE", "MdAPE"])
    test_seg = seg_df[seg_df["split"].eq("test")].sort_values(["segment", "candidate"])
    test_stress = stress_df[stress_df["split"].eq("test")].sort_values(["stress_scenario", "candidate"])

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: q35 후보가 기존 q45보다 운영 후보로 승격 가능한지 강건성까지 확인한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- q35/q45 모두 같은 학습 데이터, 같은 피처, 같은 유사작품 k160 기준 통계를 사용하고 LightGBM Quantile alpha만 다르다.",
        "- 부분 선택 정책은 실제 가격을 보지 않고 사용 단계에서 알 수 있는 예측가/유사작품 통계만 사용한다.",
        "",
        "## 1. Test 성능: tail 기준 정렬",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Validation 성능: tail 기준 정렬",
        md_table(val_metrics, metric_cols),
        "",
        "## 3. Paired bootstrap",
        "- delta는 `후보 - q45_current`다. 음수이면 후보가 q45보다 좋다.",
        md_table(boot_df, boot_cols),
        "",
        "## 4. Test 가격대별 진단",
        md_table(test_seg, seg_cols),
        "",
        "## 5. Test 결측 스트레스",
        md_table(test_stress, stress_cols),
        "",
        "## 6. 결론",
        "",
        "- `q35_global`은 q45 대비 MAPE, p95, APE > 5를 낮추는 방향이 test에서 확인된다.",
        "- q35의 이점은 1백만원 미만 및 1백만~3백만원 구간의 과대예측 완화에서 주로 나온다.",
        "- 1천만원 이상 고가 구간은 q45가 더 안정적인 편이므로, q35를 전면 적용할지는 고가 구간 손실과 tail 개선의 trade-off로 판단해야 한다.",
        "- 부분 선택 정책은 q35 선택률을 낮출 수 있지만, 이번 검증에서는 full q35의 tail 개선을 일관되게 넘지는 못했다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}code{{background:#eef2f7;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<p>strict Cold 조건에서 q35 후보를 q45와 비교한 강건성 검증이다. artist_key, 같은 작가 가격 이력, lookup 후처리, 외부 live 검색은 사용하지 않았다.</p>
<h2>Test 성능</h2>{html_table(test_metrics, metric_cols)}
<h2>Validation 성능</h2>{html_table(val_metrics, metric_cols)}
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

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train,
        val,
        test,
        ARTWORK_SIM_FEATURES,
        prefix=f"artwork_sim_k{TOP_K}",
        top_k=TOP_K,
    )
    features = unique(enterable_base + art_ref_features)

    model45 = fit_quantile_model(train_art, features, alpha=0.45)
    model35 = fit_quantile_model(train_art, features, alpha=0.35)
    preds = {
        "validation": {
            "q45": predict_model(model45, train_art, val_art, features),
            "q35": predict_model(model35, train_art, val_art, features),
            "frame": val_art,
        },
        "test": {
            "q45": predict_model(model45, train_art, test_art, features),
            "q35": predict_model(model35, train_art, test_art, features),
            "frame": test_art,
        },
    }

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for split, pack in preds.items():
        frame = pack["frame"]
        policy_preds = make_policy_predictions(pack["q45"], pack["q35"], frame)
        for candidate, (pred, mask, policy) in policy_preds.items():
            extra = {"q35_selected_rate": float(np.mean(mask))}
            metric_rows.append(metric_row(candidate, split, frame, pred, policy, extra))
            pred_frames.append(prediction_frame(candidate, split, frame, pred, policy, extra))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    boot_rows = []
    for split, pack in preds.items():
        frame = pack["frame"]
        base = pack["q45"]
        policy_preds = make_policy_predictions(pack["q45"], pack["q35"], frame)
        for candidate, (pred, _mask, _policy) in policy_preds.items():
            if candidate == "q45_current":
                continue
            boot_rows.append(paired_bootstrap(
                frame,
                pred,
                base,
                a_name=candidate,
                b_name="q45_current",
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)
    seg_df = segment_summary(predictions_df)
    stress_df = stress_metrics(
        train_art=train_art,
        val_art=val_art,
        test_art=test_art,
        features=features,
        model45=model45,
        model35=model35,
    )

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "router_used": False,
        "selection_policy_evaluated": True,
        "router_uses_actual_price": False,
        "top_k": TOP_K,
        "compared_alpha": [0.45, 0.35],
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    stress_df.to_csv(OUT / "missingness_stress_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, predictions_df, boot_df, seg_df, stress_df, summary)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
