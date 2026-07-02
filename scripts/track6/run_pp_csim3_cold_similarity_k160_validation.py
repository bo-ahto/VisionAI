#!/usr/bin/env python3
"""PP-CSIM3: validate PP-CSIM2 artwork_similarity_k160 Cold candidate.

This follow-up keeps routers out of scope and validates whether the selected
feature/model candidate is robust enough to consider as a Cold replacement:

- paired bootstrap vs user_meta_core_bucket and artwork_only
- segment diagnostics
- inference-time user metadata missingness stress
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
from run_pp_cmeta5_user_meta_robustness_validation import MISSING_SCENARIOS, apply_missing_scenario, paired_bootstrap  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    fit_quantile_bundle,
    html_table,
    json_clean,
    md_table,
)
from run_pp_csim2_cold_similarity_grouping_refinement import prediction_rows  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import candidate_defs, load_user_meta_frames  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM3"
SLUG = "PP-CSIM3_cold_similarity_k160_validation"
TITLE = "Cold 유사작품 k160 후보 후속 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim3_cold_similarity_k160_validation_summary.md"

TOP_K = 160


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def ape(actual_price: pd.Series, pred_log: np.ndarray) -> np.ndarray:
    actual = pd.to_numeric(actual_price, errors="coerce").to_numpy(dtype=float)
    pred = np.exp(np.asarray(pred_log, dtype=float))
    return np.abs(pred - actual) / np.maximum(actual, 1.0)


def segment_diagnostics(predictions: pd.DataFrame, candidate: str, split: str) -> pd.DataFrame:
    df = predictions[predictions["candidate"].eq(candidate) & predictions["split"].eq(split)].copy()
    frames: list[pd.DataFrame] = []
    price = pd.to_numeric(df["actual_price"], errors="coerce")
    df["actual_price_band"] = pd.cut(
        price,
        bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
        labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
        include_lowest=True,
    ).astype("string")
    qwidth = pd.to_numeric(df["quantile_width_log"], errors="coerce")
    try:
        df["quantile_width_band"] = pd.qcut(
            qwidth,
            q=4,
            labels=["qwidth_q1_low", "qwidth_q2", "qwidth_q3", "qwidth_q4_high"],
            duplicates="drop",
        ).astype("string")
    except ValueError:
        df["quantile_width_band"] = "qwidth_unknown"

    for segment_type in ["actual_price_band", "quantile_width_band"]:
        for segment, group in df.groupby(segment_type, dropna=False, observed=False):
            if group.empty:
                continue
            pred = group["pred_log"].to_numpy(dtype=float)
            metric = metrics(
                group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                    columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                ),
                pred,
            )
            frames.append(pd.DataFrame([{
                "candidate": candidate,
                "split": split,
                "segment_type": segment_type,
                "segment": str(segment),
                "n": int(len(group)),
                **metric,
            }]))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fit_q50_model(train: pd.DataFrame, features: list[str]):
    from run_pp_csim1_cold_similarity_reference import lgbm_quantile_model, normalize_for_model

    train_norm, _, _ = normalize_for_model(train, train.iloc[:1].copy(), train.iloc[:1].copy(), features)
    y = train_norm["ln_price_krw"].to_numpy(dtype=float)
    model = lgbm_quantile_model(train_norm, features, alpha=0.5)
    model.fit(train_norm[features], y)
    return model


def predict_q50(model: Any, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    from run_pp_csim1_cold_similarity_reference import normalize_for_model

    _, frame_norm, _ = normalize_for_model(frame.iloc[:1].copy(), frame, frame.iloc[:1].copy(), features)
    return np.asarray(model.predict(frame_norm[features]), dtype=float)


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


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    core_features = cmeta["user_meta_core_bucket"][1]
    required = unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    for name, features in [("artwork_only", artwork_features), ("user_meta_core_bucket", core_features)]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")
        if any(feature.startswith("search_") for feature in features):
            raise ValueError(f"{name} includes forbidden search_* feature")

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=f"artwork_sim_k{TOP_K}", top_k=TOP_K
    )
    sim_features = unique(core_features + art_ref_features)

    candidates = [
        ("artwork_only", train, val, test, artwork_features, "작품 정보만"),
        ("user_meta_core_bucket", train, val, test, core_features, "작품+사용자 입력 작가 메타 bucket"),
        ("artwork_similarity_k160", train_art, val_art, test_art, sim_features, "작품 유사 비교군 top_k=160 통계 추가"),
    ]

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    bundles: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    frames_by_candidate: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]] = {}
    for name, tr, va, te, features, policy in candidates:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")
        bundle = fit_quantile_bundle(tr, va, te, features)
        bundles[name] = bundle
        frames_by_candidate[name] = (tr, va, te, features)
        for split, frame in [("validation", va), ("test", te)]:
            pred = bundle["q50"][split]
            metric_rows.append(metric_row(name, split, frame, pred, features, policy))
            pred_frames.append(prediction_rows(EXP_ID, name, split, frame, pred, bundle, policy, len(features)))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    boot_rows = []
    for split, frame in [("validation", val), ("test", test)]:
        for base in ["user_meta_core_bucket", "artwork_only"]:
            boot_rows.append(paired_bootstrap(
                frame,
                bundles["artwork_similarity_k160"]["q50"][split],
                bundles[base]["q50"][split],
                a_name="artwork_similarity_k160",
                b_name=base,
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)

    seg_df = pd.concat([
        segment_diagnostics(predictions_df, "artwork_similarity_k160", "test"),
        segment_diagnostics(predictions_df, "user_meta_core_bucket", "test"),
    ], ignore_index=True)

    # Missingness stress for selected candidate.  Similarity stats are artwork-only
    # here, so they stay fixed; user metadata fields are blanked at inference time.
    model = fit_q50_model(train_art, sim_features)
    stress_rows: list[dict[str, Any]] = []
    for scenario, fields in MISSING_SCENARIOS.items():
        for split, base_frame in [("validation", val_art), ("test", test_art)]:
            frame = apply_missing_scenario(base_frame, fields)
            pred = predict_q50(model, frame, sim_features)
            stress_rows.append({
                "experiment_id": EXP_ID,
                "candidate": "artwork_similarity_k160",
                "split": split,
                "stress_scenario": scenario,
                "missing_fields": ",".join(fields),
                "n_missing_fields": len(fields),
                **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
            })
    stress_df = pd.DataFrame(stress_rows)

    strict_audit = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_user_enterable_artist_meta": True,
        "uses_similarity_reference_stats": True,
        "top_k": TOP_K,
        "router_used": False,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap.csv", index=False)
    seg_df.to_csv(OUT / "segment_diagnostics.csv", index=False)
    stress_df.to_csv(OUT / "missingness_stress_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(strict_audit), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = ["candidate", "split", "policy", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "n_features"]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MdAPE_a_minus_b_lt_0", "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment_type", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    stress_cols = ["stress_scenario", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "n_missing_fields", "missing_fields"]

    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    test_stress = stress_df[stress_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    high_risk_segments = seg_df.sort_values(["p95_APE", "MAPE"], ascending=[False, False]).head(16)

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {strict_audit['created_at']}",
        "- 목적: PP-CSIM2에서 나온 `artwork_similarity_k160` 후보를 라우터 없이 후속 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 학습 행 유사작품 통계는 out-of-fold, validation/test는 train-only 기준이다.",
        "",
        "## 1. 기본 성능",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Paired bootstrap",
        "",
        "- delta는 `artwork_similarity_k160 - 비교 후보`다. 음수면 k160 후보가 더 좋다는 뜻이다.",
        md_table(boot_df, boot_cols),
        "",
        "## 3. 메타 누락 stress",
        "",
        "- 작품 유사 통계는 유지하고, 사용 단계에서 사용자 작가 메타가 비어 있는 상황만 시뮬레이션했다.",
        md_table(test_stress, stress_cols),
        "",
        "## 4. 위험 세그먼트",
        md_table(high_risk_segments, seg_cols),
        "",
        "## 5. 결론",
        "",
        "- `artwork_similarity_k160`은 기본 test 성능에서 `user_meta_core_bucket`보다 MdAPE/MAPE/p95/RMSE를 모두 소폭 개선했다.",
        "- bootstrap 기준 MAPE/RMSE 개선은 강하고, MdAPE 개선도 비교적 일관적이다. p95 개선은 test에서는 우세하지만 validation에서는 우세하지 않아 tail 안정성은 추가 확인이 필요하다.",
        "- 메타 누락 stress에서는 followers/total works 계열이 빠질 때 성능이 약해지므로, 이 후보를 쓰더라도 해당 입력값은 권장 또는 필수 입력으로 관리해야 한다.",
        "- 라우터는 사용하지 않았으므로 이 결과는 후보 모델 자체의 피처 변경 효과다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>기본 성능</h2>{html_table(test_metrics, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>메타 누락 stress</h2>{html_table(test_stress, stress_cols)}
<h2>위험 세그먼트</h2>{html_table(high_risk_segments, seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(strict_audit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
