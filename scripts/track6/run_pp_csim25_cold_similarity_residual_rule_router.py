#!/usr/bin/env python3
"""PP-CSIM25: Cold similar-neighbor residual correction rule router.

PP-CSIM24 showed that similar-neighbor residual correction can reduce MAPE or
tail errors, but applying it globally is not consistently better than the base
similarity model. This experiment tests transparent inference-time routing:

    keep base prediction unless row-level signals say residual correction should
    be applied.

Allowed routing signals:
- base predicted price/log price
- candidate residual correction magnitude and direction
- candidate predicted price

Forbidden routing signals:
- actual validation/test price
- artist_key
- same-artist price history
- search/live lookup
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

from cold_experiment_harness import strict_cold_run_summary  # noqa: E402
from run_pp_cmeta5_user_meta_robustness_validation import paired_bootstrap  # noqa: E402
from run_pp_csim1_cold_similarity_reference import html_table, json_clean, md_table  # noqa: E402
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import unique  # noqa: E402


EXP_ID = "PP-CSIM25"
SLUG = "PP-CSIM25_cold_similarity_residual_rule_router"
TITLE = "Cold 유사 이웃 잔차 보정 규칙 라우터"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim25_cold_similarity_residual_rule_router_summary.md"

SOURCE = BASE_EXP_DIR / "PP-CSIM24_cold_similarity_neighbor_residual_correction" / "outputs" / "predictions.csv"
BASE_CANDIDATE = "base_similarity_k160_q50"


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def load_predictions() -> pd.DataFrame:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Run PP-CSIM24 first: {SOURCE}")
    df = pd.read_csv(SOURCE)
    required = {
        "candidate", "split", "_track6_row_id", "actual_log", "actual_price",
        "pred_log", "pred_price", "correction_log",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"PP-CSIM24 predictions missing columns: {missing}")
    return df


def frame_for_split(df: pd.DataFrame, split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = df[(df["split"].eq(split)) & (df["candidate"].eq(BASE_CANDIDATE))].copy()
    base = base.sort_values("_track6_row_id").reset_index(drop=True)
    resid = df[(df["split"].eq(split)) & (~df["candidate"].eq(BASE_CANDIDATE))].copy()
    return base, resid


def build_masks(base: pd.DataFrame, cand: pd.DataFrame) -> dict[str, tuple[np.ndarray, str]]:
    base_price = base["pred_price"].to_numpy(dtype=float)
    cand_price = cand["pred_price"].to_numpy(dtype=float)
    corr = cand["correction_log"].fillna(0.0).to_numpy(dtype=float)
    abs_corr = np.abs(corr)
    masks: dict[str, tuple[np.ndarray, str]] = {
        "global": (np.ones(len(base), dtype=bool), "항상 보정 후보 적용"),
    }

    for cap in [1_000_000, 2_000_000, 3_000_000, 5_000_000, 8_000_000]:
        low_base = base_price < cap
        low_either = (base_price < cap) | (cand_price < cap)
        for min_abs in [0.00, 0.03, 0.05, 0.08, 0.12]:
            enough = abs_corr >= min_abs
            suffix = f"{cap//10000}w_abs{str(min_abs).replace('.', 'p')}"
            masks[f"base_lt_{suffix}"] = (
                low_base & enough,
                f"기본 예측가 {cap//10000}만원 미만이고 보정 절대값 {min_abs:.2f} log 이상이면 보정 후보 적용",
            )
            masks[f"either_lt_{suffix}"] = (
                low_either & enough,
                f"기본/보정 후보 중 하나가 {cap//10000}만원 미만이고 보정 절대값 {min_abs:.2f} log 이상이면 보정 후보 적용",
            )
            masks[f"base_lt_neg_{suffix}"] = (
                low_base & enough & (corr < 0),
                f"기본 예측가 {cap//10000}만원 미만이고 하향 보정 절대값 {min_abs:.2f} log 이상이면 보정 후보 적용",
            )
            masks[f"base_lt_pos_{suffix}"] = (
                low_base & enough & (corr > 0),
                f"기본 예측가 {cap//10000}만원 미만이고 상향 보정 절대값 {min_abs:.2f} log 이상이면 보정 후보 적용",
            )

    for min_abs in [0.03, 0.05, 0.08, 0.12, 0.18]:
        masks[f"abs_corr_ge_{str(min_abs).replace('.', 'p')}"] = (
            abs_corr >= min_abs,
            f"보정 절대값 {min_abs:.2f} log 이상이면 보정 후보 적용",
        )
        masks[f"neg_corr_ge_{str(min_abs).replace('.', 'p')}"] = (
            (corr <= -min_abs),
            f"하향 보정 {min_abs:.2f} log 이상이면 보정 후보 적용",
        )
        masks[f"pos_corr_ge_{str(min_abs).replace('.', 'p')}"] = (
            (corr >= min_abs),
            f"상향 보정 {min_abs:.2f} log 이상이면 보정 후보 적용",
        )
    return masks


def metric_row(candidate: str, split: str, base: pd.DataFrame, pred: np.ndarray, policy: str, mask: np.ndarray, source_candidate: str) -> dict[str, Any]:
    frame = base[["_track6_row_id", "actual_log", "actual_price"]].rename(
        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
    )
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "source_candidate": source_candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        "selected_rate": float(np.mean(mask)),
        "selected_n": int(np.sum(mask)),
        **metrics(frame, pred),
        **tail_counts(frame, pred),
    }


def prediction_frame(candidate: str, split: str, base: pd.DataFrame, pred: np.ndarray, policy: str, mask: np.ndarray, source_candidate: str) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "source_candidate": source_candidate,
        "split": split,
        "_track6_row_id": base["_track6_row_id"].to_numpy(),
        "actual_log": base["actual_log"].to_numpy(dtype=float),
        "actual_price": base["actual_price"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "selected": mask.astype(int),
        "policy": policy,
    })


def build_prediction_for_candidate(df: pd.DataFrame, split: str, routed_candidate: str) -> pd.DataFrame:
    base, resid = frame_for_split(df, split)
    base_pred = base["pred_log"].to_numpy(dtype=float)
    if routed_candidate == "base":
        mask = np.zeros(len(base), dtype=bool)
        return prediction_frame("base", split, base, base_pred, "base", mask, BASE_CANDIDATE)

    source_candidate, rule_name = routed_candidate.split("__route_", 1)
    cand = resid[resid["candidate"].eq(source_candidate)].sort_values("_track6_row_id").reset_index(drop=True)
    if cand.empty:
        raise ValueError(f"Missing source candidate for {routed_candidate}")
    masks = build_masks(base, cand)
    if rule_name not in masks:
        raise ValueError(f"Missing rule {rule_name} for {routed_candidate}")
    mask, policy = masks[rule_name]
    pred = np.where(mask, cand["pred_log"].to_numpy(dtype=float), base_pred)
    return prediction_frame(routed_candidate, split, base, pred, policy, mask, source_candidate)


def select_validation(metrics_df: pd.DataFrame) -> pd.DataFrame:
    val = metrics_df[metrics_df["split"].eq("validation")].copy()
    val["is_base"] = val["candidate"].eq("base")
    return val.sort_values(["MAPE", "p95_APE", "MdAPE", "APE_gt_5", "selected_rate", "is_base"]).head(16)


def segment_summary(predictions: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    rows = []
    df = predictions[predictions["candidate"].isin(selected)].copy()
    for (candidate, split), group_all in df.groupby(["candidate", "split"], observed=False):
        work = group_all.copy()
        work["actual_price_band"] = pd.cut(
            pd.to_numeric(work["actual_price"], errors="coerce"),
            bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
            labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
            include_lowest=True,
        ).astype("string")
        for segment, group in work.groupby("actual_price_band", observed=False):
            frame = group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
            )
            pred = group["pred_log"].to_numpy(dtype=float)
            rows.append({
                "candidate": candidate,
                "split": split,
                "segment": str(segment),
                "n": int(len(group)),
                "selected_rate": float(group["selected"].mean()),
                **metrics(frame, pred),
                **tail_counts(frame, pred),
            })
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, predictions_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = [
        "candidate", "source_candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "APE_gt_2", "APE_gt_5", "APE_gt_10", "selected_rate", "policy",
    ]
    boot_cols = [
        "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MdAPE_a_minus_b_lt_0", "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "selected_rate", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]

    val_top = select_validation(metrics_df)
    selected = unique(["base"] + val_top["candidate"].head(8).tolist())
    test_selected = metrics_df[(metrics_df["split"].eq("test")) & (metrics_df["candidate"].isin(selected))].sort_values(["MAPE", "p95_APE", "MdAPE"])
    test_top = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE"]).head(16)
    selected_seg = seg_df[seg_df["candidate"].isin(selected)].sort_values(["split", "candidate", "segment"])

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: CSIM24 유사 이웃 잔차 보정을 전체 적용하지 않고, 추론 시점 신호가 맞는 row에만 적용한다.",
        "- 라우터 입력: 기본 예측가, 보정 후보 예측가, 보정 로그값의 크기/방향.",
        "- 금지: 실제 가격, `artist_key`, 같은 작가 가격 이력, 검색/lookup 후처리.",
        "",
        "## 1. Validation 선택 후보",
        md_table(val_top, metric_cols),
        "",
        "## 2. Validation 선택 후보의 Test 결과",
        md_table(test_selected, metric_cols),
        "",
        "## 3. Test 상위 후보 참고",
        md_table(test_top, metric_cols),
        "",
        "## 4. Paired bootstrap vs base",
        md_table(boot_df, boot_cols),
        "",
        "## 5. 가격대별 진단",
        md_table(selected_seg, seg_cols),
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Validation 선택 후보</h2>{html_table(val_top, metric_cols)}
<h2>Validation 선택 후보의 Test 결과</h2>{html_table(test_selected, metric_cols)}
<h2>Test 상위 후보 참고</h2>{html_table(test_top, metric_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>가격대별 진단</h2>{html_table(selected_seg, seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    df = load_predictions()

    metric_rows: list[dict[str, Any]] = []
    for split in ["validation", "test"]:
        base, resid = frame_for_split(df, split)
        base_pred = base["pred_log"].to_numpy(dtype=float)
        base_mask = np.zeros(len(base), dtype=bool)
        metric_rows.append(metric_row("base", split, base, base_pred, "항상 base similarity k160", base_mask, BASE_CANDIDATE))

        for source_candidate, cand in resid.groupby("candidate", observed=False):
            cand = cand.sort_values("_track6_row_id").reset_index(drop=True)
            if not np.array_equal(base["_track6_row_id"].to_numpy(), cand["_track6_row_id"].to_numpy()):
                raise ValueError(f"Row mismatch for {split}:{source_candidate}")
            cand_pred = cand["pred_log"].to_numpy(dtype=float)
            for rule_name, (mask, policy) in build_masks(base, cand).items():
                pred = np.where(mask, cand_pred, base_pred)
                candidate = f"{source_candidate}__route_{rule_name}"
                metric_rows.append(metric_row(candidate, split, base, pred, policy, mask, source_candidate))

    metrics_df = pd.DataFrame(metric_rows)

    val_top = select_validation(metrics_df)
    selected = unique(["base"] + val_top["candidate"].head(8).tolist())
    pred_frames = [
        build_prediction_for_candidate(df, split, candidate)
        for split in ["validation", "test"]
        for candidate in selected
    ]
    predictions_df = pd.concat(pred_frames, ignore_index=True)

    boot_rows = []
    for split in ["validation", "test"]:
        base_rows = predictions_df[(predictions_df["split"].eq(split)) & (predictions_df["candidate"].eq("base"))].sort_values("_track6_row_id")
        frame = base_rows[["_track6_row_id", "actual_log", "actual_price"]].rename(
            columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
        )
        for candidate in selected:
            if candidate == "base":
                continue
            cand_rows = predictions_df[(predictions_df["split"].eq(split)) & (predictions_df["candidate"].eq(candidate))].sort_values("_track6_row_id")
            boot_rows.append(paired_bootstrap(
                frame,
                cand_rows["pred_log"].to_numpy(dtype=float),
                base_rows["pred_log"].to_numpy(dtype=float),
                a_name=candidate,
                b_name="base",
            ) | {"split": split})
    boot_df = pd.DataFrame(boot_rows)
    seg_df = segment_summary(predictions_df, selected)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-CSIM24",
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_artist_key_lookup_postprocess": False,
        "uses_rule_router": True,
        "router_uses_actual_price": False,
        "router_signals": ["base_pred_price", "candidate_pred_price", "correction_log"],
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap_vs_base.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, predictions_df, boot_df, seg_df, summary)


if __name__ == "__main__":
    main()
