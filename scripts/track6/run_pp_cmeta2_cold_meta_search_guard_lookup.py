#!/usr/bin/env python3
"""PP-CMETA2: add q40 guard and v0.3 lookup to operational meta/search Cold.

Follow-up to PP-CMETA1.  CMETA1 validated operationally collectable
artist-meta/search features without artist-key memorization or per-artist
lookup.  This experiment retrains the same candidate feature sets with q40 and
tests post-processing combinations:

- base_q50
- q50 + frozen v0.3 search_delta_lookup
- guard(q50, q40, qwidth)
- guard(q50, q40, qwidth) + frozen v0.3 search_delta_lookup
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

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_cmeta1_cold_operational_meta_search import candidates  # noqa: E402
from run_pp_y_cold_combination_experiments import (  # noqa: E402
    fit_predict,
    fit_quantile_bundle,
    load_cold_full,
    load_search_df,
    unique,
)


EXP_ID = "PP-CMETA2"
SLUG = "PP-CMETA2_cold_meta_search_guard_lookup_validation"
TITLE = "Cold 운영형 메타/검색 q40 guard + lookup 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
COLD_V03_PARAMS = REPO / "models" / "track6" / "cold_prediction_v0.3" / "config" / "cold_postprocess_params_v0_3.json"
COLD_V03_LOOKUP = REPO / "models" / "track6" / "cold_prediction_v0.3" / "config" / "search_delta_lookup_v0_3.json"


def load_guard_params() -> dict[str, float]:
    raw = json.loads(COLD_V03_PARAMS.read_text(encoding="utf-8"))
    guard = raw["guard"]
    return {
        "qwidth_q67": float(guard["qwidth_q67"]),
        "gap_q50": float(guard["gap_q50"]),
        "weight": float(guard["weight"]),
    }


def load_lookup() -> dict[str, float]:
    raw = json.loads(COLD_V03_LOOKUP.read_text(encoding="utf-8"))
    return {str(key): float(value) for key, value in raw["artist_delta"].items()}


def metric_row(
    candidate: str,
    split: str,
    policy: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    *,
    feature_strategy: str,
    n_features: int,
    lookup_covered: np.ndarray,
    guard_mask: np.ndarray,
    delta: np.ndarray,
) -> dict[str, Any]:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "policy": policy,
        "n": int(len(frame)),
        "feature_strategy": feature_strategy,
        "n_features": int(n_features),
        "lookup_coverage": float(lookup_covered.mean()) if len(lookup_covered) else 0.0,
        "guard_rate": float(guard_mask.mean()) if len(guard_mask) else 0.0,
        "mean_lookup_delta_log": float(delta.mean()) if len(delta) else 0.0,
    }
    row.update(metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred_log))
    return row


def prediction_rows(
    candidate: str,
    split: str,
    policy: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    q40: np.ndarray,
    q50: np.ndarray,
    qwidth: np.ndarray,
    delta: np.ndarray,
    lookup_covered: np.ndarray,
    guard_mask: np.ndarray,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "artist_key": frame["artist_key"].astype(str).to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
        "q40_log": q40,
        "q50_log": q50,
        "qwidth_log": qwidth,
        "lookup_delta_log": delta,
        "lookup_covered": lookup_covered,
        "guard_applied": guard_mask,
    })
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    return out


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_empty_"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        values = []
        for col in cols:
            value = row[col]
            values.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def html_table(df: pd.DataFrame, cols: list[str]) -> str:
    header = "".join(f"<th>{html.escape(col)}</th>" for col in cols)
    rows = []
    for _, row in df[cols].iterrows():
        cells = []
        for col in cols:
            value = row[col]
            text = f"{value:.6f}" if isinstance(value, float) else str(value)
            cells.append(f"<td>{html.escape(text)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def main() -> None:
    for path in [OUT, REPORTS, ARTIFACTS]:
        path.mkdir(parents=True, exist_ok=True)

    search_df = load_search_df()
    guard = load_guard_params()
    lookup = load_lookup()
    cands = candidates()
    all_features = unique([feature for _, _, features, _ in cands for feature in features])
    train, val, test = load_cold_full(all_features, search_df)

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    feature_rows: list[dict[str, Any]] = []

    for candidate, strategy, features, hypothesis in cands:
        bundle = fit_quantile_bundle("lightgbm", train, val, test, features)
        q40_pred = fit_predict("lightgbm", "quantile", train, val, test, features, alpha=0.4)
        feature_rows.append({
            "candidate": candidate,
            "feature_strategy": strategy,
            "hypothesis": hypothesis,
            "n_features": len(features),
            "features": ", ".join(features),
        })
        for split, frame in [("validation", val), ("test", test)]:
            q10 = bundle["q10"][split]
            q50 = bundle["q50"][split]
            q90 = bundle["q90"][split]
            q40 = q40_pred[split]
            qwidth = np.maximum(q90 - q10, 0.0)
            artist = frame["artist_key"].astype(str).to_numpy()
            delta = np.array([lookup.get(key, 0.0) for key in artist], dtype=float)
            covered = np.array([key in lookup for key in artist], dtype=bool)
            guard_mask = (
                (qwidth >= guard["qwidth_q67"])
                & ((q50 - q40) >= guard["gap_q50"])
                & (q40 < q50)
            )
            guarded = q50.copy()
            guarded[guard_mask] = (1.0 - guard["weight"]) * q50[guard_mask] + guard["weight"] * q40[guard_mask]
            policies = {
                "base_q50": q50,
                "lookup_only": q50 + delta,
                "guard_only": guarded,
                "guard_plus_lookup": guarded + delta,
            }
            for policy, pred_log in policies.items():
                metric_rows.append(metric_row(
                    candidate,
                    split,
                    policy,
                    frame,
                    pred_log,
                    feature_strategy=strategy,
                    n_features=len(features),
                    lookup_covered=covered,
                    guard_mask=guard_mask,
                    delta=delta,
                ))
                pred_frames.append(prediction_rows(
                    candidate,
                    split,
                    policy,
                    frame,
                    pred_log,
                    q40,
                    q50,
                    qwidth,
                    delta,
                    covered,
                    guard_mask,
                ))

    metrics_df = pd.DataFrame(metric_rows)
    predictions = pd.concat(pred_frames, ignore_index=True)
    feature_map = pd.DataFrame(feature_rows)
    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions.to_csv(OUT / "predictions.csv", index=False)
    feature_map.to_csv(OUT / "feature_map.csv", index=False)

    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).reset_index(drop=True)
    validation = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).reset_index(drop=True)
    best = test.iloc[0].to_dict() if not test.empty else {}
    summary = {
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "guard_params": guard,
        "lookup_artists": len(lookup),
        "best_test": best,
        "note": "This tests frozen v0.3 lookup as a postprocess. Fixed Cold test has high lookup coverage; live new-artist coverage must be validated separately.",
    }
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = [
        "candidate",
        "policy",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "guard_rate",
        "lookup_coverage",
        "feature_strategy",
    ]
    report_md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: PP-CMETA1 운영형 Cold 후보에 q40 guard와 v0.3 작가별 search_delta lookup을 붙였을 때 성능이 추가 개선되는지 검증한다.",
        "- 주의: lookup은 frozen 작가 단위 보정값이다. fixed test coverage가 높아도 신규 작가 운영 coverage를 보장하지 않는다.",
        "",
        "## Test 결과 상위",
        md_table(test[metric_cols], metric_cols),
        "",
        "## Validation 결과 상위",
        md_table(validation[metric_cols], metric_cols),
    ])
    (REPORTS / "result_report.md").write_text(report_md, encoding="utf-8")

    report_html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(TITLE)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #17202a; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin: 16px 0; }}
    th, td {{ border: 1px solid #d8dee9; padding: 7px 9px; text-align: left; vertical-align: top; }}
    th {{ background: #edf2f7; }}
    .note {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 12px 16px; }}
  </style>
</head>
<body>
  <h1>{html.escape(TITLE)}</h1>
  <div class="note">q40 guard와 frozen v0.3 lookup 후처리를 PP-CMETA1 후보에 조합해 검증했다.</div>
  <h2>Test 결과 상위</h2>
  {html_table(test, metric_cols)}
  <h2>Validation 결과 상위</h2>
  {html_table(validation, metric_cols)}
</body>
</html>
"""
    (REPORTS / "result_report.html").write_text(report_html, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
