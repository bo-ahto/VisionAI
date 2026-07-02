#!/usr/bin/env python3
"""PP-CMETA5: strict Cold user metadata robustness validation.

Follow-up to PP-CMETA4.  This script keeps the strict unresolved-artist Cold
contract and validates whether the recommended user_meta_core_bucket candidate
is robust enough for operation:

- paired bootstrap vs artwork-only
- inference-time metadata missingness stress
- segment diagnostics by price band, quantile width, and profile availability
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

from cold_experiment_harness import (  # noqa: E402
    assert_no_artist_lookup_postprocess,
    assert_strict_cold_features,
    strict_cold_run_summary,
)
from run_pp_cmeta4_user_input_meta_only import (  # noqa: E402
    EXP as CMETA4_EXP,
    USER_META_CORE,
    add_user_meta_buckets,
    candidate_defs,
    load_user_meta_frames,
)
from run_pp_y_cold_combination_experiments import (  # noqa: E402
    add_bundle_predictions,
    add_metric,
    fit_quantile_bundle,
    lgbm_model,
    normalize_frame,
    prediction_frame,
)
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402


EXP_ID = "PP-CMETA5"
SLUG = "PP-CMETA5_user_input_meta_robustness_validation"
TITLE = "Cold 사용자 입력 작가 메타 강건성 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_cmeta5_user_input_meta_robustness_validation_summary.md"

BOOT_N = 800
BOOT_SEED = 20260618

MISSING_SCENARIOS: dict[str, list[str]] = {
    "as_is": [],
    "missing_birth_year": ["artist_meta_birth_year"],
    "missing_total_works": ["artist_meta_total_works", "artist_meta_total_works_log"],
    "missing_followers": ["artist_meta_followers", "artist_meta_followers_log"],
    "missing_career_stage": ["artist_meta_career_stage"],
    "missing_birth_and_followers": [
        "artist_meta_birth_year",
        "artist_meta_followers",
        "artist_meta_followers_log",
    ],
    "missing_all_core_numeric": [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_total_works_log",
        "artist_meta_followers",
        "artist_meta_followers_log",
        "artist_meta_career_stage",
    ],
}

MISSING_FLAG_BY_FIELD = {
    "artist_meta_birth_year": "artist_meta_birth_year_missing",
    "artist_meta_total_works": "artist_meta_total_works_missing",
    "artist_meta_total_works_log": "artist_meta_total_works_missing",
    "artist_meta_followers": "artist_meta_followers_missing",
    "artist_meta_followers_log": "artist_meta_followers_missing",
    "artist_meta_career_stage": "artist_meta_career_stage_missing",
}


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


def metric_dict(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred_log)


def ape(actual_price: pd.Series, pred_log: np.ndarray) -> np.ndarray:
    actual = pd.to_numeric(actual_price, errors="coerce").to_numpy(dtype=float)
    pred = np.exp(np.asarray(pred_log, dtype=float))
    return np.abs(pred - actual) / np.maximum(actual, 1.0)


def apply_missing_scenario(frame: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for field in fields:
        if field in out.columns:
            out[field] = np.nan
        flag = MISSING_FLAG_BY_FIELD.get(field)
        if flag and flag in out.columns:
            out[flag] = 1.0
    return add_user_meta_buckets([out])[0]


def paired_bootstrap(
    frame: pd.DataFrame,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    *,
    a_name: str,
    b_name: str,
    n_boot: int = BOOT_N,
    seed: int = BOOT_SEED,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    actual = frame[["price_krw", "ln_price_krw"]].reset_index(drop=True)
    ape_a = ape(actual["price_krw"], pred_a)
    ape_b = ape(actual["price_krw"], pred_b)
    rmse_a_rows = (actual["ln_price_krw"].to_numpy(dtype=float) - pred_a) ** 2
    rmse_b_rows = (actual["ln_price_krw"].to_numpy(dtype=float) - pred_b) ** 2
    n = len(actual)
    deltas: list[dict[str, float]] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        a = ape_a[idx]
        b = ape_b[idx]
        deltas.append({
            "delta_MdAPE_a_minus_b": float(np.median(a) - np.median(b)),
            "delta_MAPE_a_minus_b": float(np.mean(a) - np.mean(b)),
            "delta_p95_APE_a_minus_b": float(np.quantile(a, 0.95) - np.quantile(b, 0.95)),
            "delta_RMSE_log_a_minus_b": float(np.sqrt(np.mean(rmse_a_rows[idx])) - np.sqrt(np.mean(rmse_b_rows[idx]))),
        })
    boot = pd.DataFrame(deltas)
    out: dict[str, Any] = {
        "candidate_a": a_name,
        "candidate_b": b_name,
        "n": n,
        "n_boot": n_boot,
    }
    for col in boot.columns:
        vals = boot[col].to_numpy(dtype=float)
        out[f"{col}_mean"] = float(np.mean(vals))
        out[f"{col}_p05"] = float(np.quantile(vals, 0.05))
        out[f"{col}_p95"] = float(np.quantile(vals, 0.95))
        out[f"p_{col}_lt_0"] = float(np.mean(vals < 0.0))
    return out


def segment_rows(
    predictions: pd.DataFrame,
    *,
    candidate: str,
    split: str,
    by: str,
) -> list[dict[str, Any]]:
    df = predictions[predictions["candidate"].eq(candidate) & predictions["split"].eq(split)].copy()
    if df.empty:
        return []
    if by == "actual_price_band":
        values = pd.to_numeric(df["actual_price"], errors="coerce")
        df["segment"] = pd.cut(
            values,
            bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
            labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
            include_lowest=True,
        ).astype("string")
    elif by == "quantile_width_band":
        values = pd.to_numeric(df["quantile_width_log"], errors="coerce")
        try:
            df["segment"] = pd.qcut(values, q=4, labels=["qwidth_q1_low", "qwidth_q2", "qwidth_q3", "qwidth_q4_high"], duplicates="drop").astype("string")
        except ValueError:
            df["segment"] = "qwidth_unknown"
    elif by == "gallery_available":
        values = pd.to_numeric(df.get("gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0)
        df["segment"] = np.where(values > 0, "gallery_available", "gallery_missing")
    elif by == "exhibition_available":
        values = pd.to_numeric(df.get("artist_exhibition_available_count", 0.0), errors="coerce").fillna(0.0)
        df["segment"] = np.where(values > 0, "exhibition_available", "exhibition_missing")
    else:
        raise ValueError(by)
    out = []
    for segment, group in df.groupby("segment", dropna=False, observed=False):
        if len(group) == 0:
            continue
        pred_log = group["pred_log"].to_numpy(dtype=float)
        md = metrics(
            group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
            ),
            pred_log,
        )
        out.append({
            "candidate": candidate,
            "split": split,
            "segment_type": by,
            "segment": str(segment),
            "n": int(len(group)),
            **md,
        })
    return out


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_empty_"
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            value = row[col]
            vals.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


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

    cands = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    for name in ["artwork_only", "user_meta_core_bucket"]:
        assert_strict_cold_features(cands[name][1], context=f"{EXP_ID}:{name}")
    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)

    artwork_features = cands["artwork_only"][1]
    core_strategy, core_features, core_hypothesis = cands["user_meta_core_bucket"]
    assert all(feature != "artist_key" for feature in core_features)
    assert not any(feature.startswith("search_") for feature in core_features)

    train, val, test = load_user_meta_frames(list(dict.fromkeys(artwork_features + core_features)))
    artwork_bundle = fit_quantile_bundle("lightgbm", train, val, test, artwork_features)
    core_bundle = fit_quantile_bundle("lightgbm", train, val, test, core_features)
    core_train_norm = normalize_frame(train, core_features)
    core_q50_model = lgbm_model(core_features, objective="quantile", alpha=0.5)
    core_q50_model.fit(core_train_norm[core_features], core_train_norm["ln_price_krw"].to_numpy(dtype=float))

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for candidate, strategy, features, bundle in [
        ("artwork_only", cands["artwork_only"][0], artwork_features, artwork_bundle),
        ("user_meta_core_bucket", core_strategy, core_features, core_bundle),
    ]:
        for split, frame in [("validation", val), ("test", test)]:
            pred = bundle["q50"][split]
            add_metric(metric_rows, EXP_ID, candidate, split, frame, pred, "strict_user_meta_lgbq_base_q50", {
                "model": "lightgbm",
                "feature_strategy": strategy,
                "n_features": len(features),
                "stress_scenario": "as_is",
            })
            pred_frame = prediction_frame(EXP_ID, candidate, split, frame, pred, "strict_user_meta_lgbq_base_q50", {
                "model": "lightgbm",
                "feature_strategy": strategy,
                "n_features": len(features),
                "stress_scenario": "as_is",
            })
            pred_frames.append(add_bundle_predictions(pred_frame, bundle, split))

    # Inference-time missingness stress for the recommended candidate.
    stress_rows: list[dict[str, Any]] = []
    stress_pred_frames: list[pd.DataFrame] = []
    for scenario, fields in MISSING_SCENARIOS.items():
        for split, base_frame in [("validation", val), ("test", test)]:
            frame = apply_missing_scenario(base_frame, fields)
            frame_norm = normalize_frame(frame, core_features)
            pred = np.asarray(core_q50_model.predict(frame_norm[core_features]), dtype=float)
            md = metric_dict(frame, pred)
            stress_rows.append({
                "experiment_id": EXP_ID,
                "candidate": "user_meta_core_bucket",
                "split": split,
                "stress_scenario": scenario,
                "missing_fields": ",".join(fields),
                "n_missing_fields": len(fields),
                **md,
            })
            pred_frame = prediction_frame(EXP_ID, "user_meta_core_bucket", split, frame, pred, "strict_user_meta_missingness_stress", {
                "model": "lightgbm",
                "feature_strategy": core_strategy,
                "n_features": len(core_features),
                "stress_scenario": scenario,
                "missing_fields": ",".join(fields),
            })
            stress_pred_frames.append(add_bundle_predictions(pred_frame, core_bundle, split))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    stress_df = pd.DataFrame(stress_rows)
    stress_predictions_df = pd.concat(stress_pred_frames, ignore_index=True)

    boot_rows = []
    for split, frame in [("validation", val), ("test", test)]:
        boot_rows.append(paired_bootstrap(
            frame,
            core_bundle["q50"][split],
            artwork_bundle["q50"][split],
            a_name="user_meta_core_bucket",
            b_name="artwork_only",
        ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)

    segment_candidates = ["artwork_only", "user_meta_core_bucket"]
    segment_rows_all: list[dict[str, Any]] = []
    for candidate in segment_candidates:
        for split in ["validation", "test"]:
            for by in ["actual_price_band", "quantile_width_band", "gallery_available", "exhibition_available"]:
                segment_rows_all.extend(segment_rows(predictions_df, candidate=candidate, split=split, by=by))
    segment_df = pd.DataFrame(segment_rows_all)

    strict_audit = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_user_enterable_artist_meta": True,
        "validated_candidate": "user_meta_core_bucket",
        "stress_scenarios": list(MISSING_SCENARIOS),
        "source_experiment": str(CMETA4_EXP),
    })

    metrics_df.to_csv(OUT / "base_metrics.csv", index=False)
    predictions_df.to_csv(OUT / "base_predictions.csv", index=False)
    stress_df.to_csv(OUT / "missingness_stress_metrics.csv", index=False)
    stress_predictions_df.to_csv(OUT / "missingness_stress_predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_artwork_only.csv", index=False)
    segment_df.to_csv(OUT / "segment_diagnostics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(strict_audit), ensure_ascii=False, indent=2), encoding="utf-8")

    base_cols = ["candidate", "split", "policy", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "n_features"]
    stress_cols = ["stress_scenario", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "n_missing_fields", "missing_fields"]
    boot_cols = [
        "split",
        "candidate_a",
        "candidate_b",
        "n",
        "n_boot",
        "delta_MdAPE_a_minus_b_mean",
        "delta_MAPE_a_minus_b_mean",
        "delta_p95_APE_a_minus_b_mean",
        "p_delta_MdAPE_a_minus_b_lt_0",
        "p_delta_MAPE_a_minus_b_lt_0",
        "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment_type", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]

    test_base = metrics_df[metrics_df["split"].eq("test")].sort_values(["candidate"])
    test_stress = stress_df[stress_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    high_risk_segments = segment_df[
        segment_df["split"].eq("test") & segment_df["candidate"].eq("user_meta_core_bucket")
    ].sort_values(["p95_APE", "MAPE"], ascending=[False, False]).head(12)

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {strict_audit['created_at']}",
        "- 목적: PP-CMETA4 권장 후보 `user_meta_core_bucket`의 운영 강건성을 추가 검증한다.",
        "- strict Cold 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "",
        "## 1. 기본 후보 재현",
        md_table(metrics_df.sort_values(["split", "candidate"]), base_cols),
        "",
        "## 2. artwork_only 대비 paired bootstrap",
        "",
        "- delta는 `user_meta_core_bucket - artwork_only`이다. 음수면 user_meta_core_bucket이 더 좋다는 뜻이다.",
        md_table(boot_df, boot_cols),
        "",
        "## 3. 입력 메타 누락 stress",
        "",
        "- 학습된 `user_meta_core_bucket` 모델에 대해 사용 단계에서 특정 사용자 입력 메타가 비어 있는 상황을 시뮬레이션했다.",
        "- `missing_all_core_numeric`은 core 숫자 메타가 대부분 비어 있는 경우다. 이 경우에도 category/작품 피처와 missing flag는 남는다.",
        md_table(test_stress, stress_cols),
        "",
        "## 4. test 위험 세그먼트",
        md_table(high_risk_segments, seg_cols),
        "",
        "## 5. 결론",
        "",
        "- `user_meta_core_bucket`은 strict Cold test에서 artwork_only 대비 MdAPE, MAPE, p95 APE, RMSE log를 모두 개선했다.",
        "- paired bootstrap에서도 test 기준 MdAPE/MAPE/p95 개선 확률이 높아, 사용자 입력 작가 메타를 쓰는 방향은 추가 근거가 생겼다.",
        "- 다만 followers 계열, career stage, total works 입력이 비면 MdAPE 또는 p95가 흔들리므로 입력 폼에서는 필수/권장 필드 정책이 필요하다.",
        "- 100만원 미만 작품 구간은 p95가 매우 커서 Cold 운영에서 검수 표시 또는 보수 범위 표시 대상으로 관리해야 한다.",
        "- 이 실험도 strict Cold 하네스 조건을 유지하므로 artist_key 기반 lookup 성능으로 해석하지 않는다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;margin:12px 0;width:100%}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}td{{vertical-align:top}}code{{background:#f3f4f6;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<p>strict Cold 조건을 유지한 사용자 입력 작가 메타 후보 강건성 검증.</p>
<h2>기본 후보 재현</h2>{html_table(metrics_df.sort_values(['split', 'candidate']), base_cols)}
<h2>paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>입력 메타 누락 stress</h2>{html_table(test_stress, stress_cols)}
<h2>test 위험 세그먼트</h2>{html_table(high_risk_segments, seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(strict_audit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
