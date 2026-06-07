#!/usr/bin/env python3
"""Create A7 edition slice metrics after the fixed runner finishes."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[4]
CONFIG = REPO / "experiments" / "track6" / "A7_edition_only" / "experiment_config.json"
sys.path.insert(0, str(REPO))

from scripts.track6.fixed_variable_experiment_runner import (  # noqa: E402
    MODEL_ROWS,
    all_required_feature_columns,
    calc_metrics,
    fit_predict,
    load_join,
    normalize_values,
    read_config,
    split_paths,
)


def slice_metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_price: np.ndarray) -> dict[str, float]:
    if len(actual_price) < 2:
        return {
            "R2": np.nan,
            "MdAPE": np.nan,
            "p95_APE": np.nan,
            "Within_30": np.nan,
            "Within_50": np.nan,
            "MAPE": np.nan,
        }
    return calc_metrics(actual_price, actual_log, pred_price)


def main() -> None:
    config = read_config(CONFIG)
    exp_dir = Path(config["exp_dir"])
    out_dir = exp_dir / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    required = sorted(set(all_required_feature_columns(config)) | {"edition_class", "is_edition"})
    paths = split_paths(config)
    train = load_join(paths["train_features"], paths["train_labels"], required)
    warm = load_join(paths["warm_features"], paths["warm_labels"], required)
    cold = load_join(paths["cold_features"], paths["cold_labels"], required)
    train, warm, cold = normalize_values(config, train, warm, cold)

    rows = []
    numeric_features = list(config.get("numeric_features", []))
    for block in config["variable_blocks"]:
        for model in MODEL_ROWS:
            test = warm if model["scope"] == "Warm" else cold
            pred = fit_predict(model["kind"], train, test, block["features"], numeric_features)
            tmp = test[["_track6_row_id", "edition_class", "is_edition", "price_krw", "ln_price_krw"]].copy()
            tmp["pred_price"] = np.clip(pred, 1_000.0, None)
            tmp["ape"] = np.abs(tmp["pred_price"] - tmp["price_krw"]) / tmp["price_krw"]

            for slice_name, mask in [
                ("all", pd.Series(True, index=tmp.index)),
                ("edition", tmp["is_edition"].astype(str).eq("1")),
                ("non_edition", tmp["is_edition"].astype(str).eq("0")),
            ]:
                sub = tmp.loc[mask]
                metrics = slice_metrics(sub["price_krw"].to_numpy(), sub["ln_price_krw"].to_numpy(), sub["pred_price"].to_numpy())
                rows.append(
                    {
                        "experiment_id": config["experiment_id"],
                        "variable_block": block["name"],
                        "scope": model["scope"],
                        "model_code": model["code"],
                        "model_name": model["name"],
                        "slice_type": "edition_binary",
                        "slice_name": slice_name,
                        "n": int(len(sub)),
                        **metrics,
                    }
                )

            for edition_class, sub in tmp.groupby("edition_class", dropna=False):
                metrics = slice_metrics(
                    sub["price_krw"].to_numpy(), sub["ln_price_krw"].to_numpy(), sub["pred_price"].to_numpy()
                )
                rows.append(
                    {
                        "experiment_id": config["experiment_id"],
                        "variable_block": block["name"],
                        "scope": model["scope"],
                        "model_code": model["code"],
                        "model_name": model["name"],
                        "slice_type": "edition_class",
                        "slice_name": str(edition_class),
                        "n": int(len(sub)),
                        **metrics,
                    }
                )

    slice_df = pd.DataFrame(rows)
    slice_csv = out_dir / "edition_slice_metrics.csv"
    slice_df.to_csv(slice_csv, index=False)

    notes = {
        "purpose": "A7 전체 성능만으로는 에디션 효과를 해석하기 어려워 edition/non-edition 및 edition_class별 성능을 추가 확인한다.",
        "sample_warning": "Warm test의 edition 표본은 33건으로 작다. Warm edition slice 결과는 방향성 참고용이며 확정 결론으로 쓰지 않는다.",
        "cold_note": "Cold test의 edition 표본은 232건으로 Warm보다 해석 여지가 크지만, 여전히 전체 3,099건 중 일부다.",
        "signed_note": "signed는 구조화 수집 컬럼이 없어 A7 학습 피처에서 제외했다.",
    }
    (out_dir / "edition_slice_notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_rows = []
    for scope in ["Warm", "Cold"]:
        sub = slice_df[(slice_df["scope"].eq(scope)) & (slice_df["slice_type"].eq("edition_binary"))]
        for slice_name in ["all", "edition", "non_edition"]:
            cand = sub[sub["slice_name"].eq(slice_name)].sort_values("MdAPE").head(1)
            if len(cand):
                summary_rows.append(cand.iloc[0].to_dict())
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out_dir / "edition_slice_summary.csv", index=False)

    def fmt(v: float) -> str:
        return "" if pd.isna(v) else f"{float(v):.4f}"

    top_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(r.scope))}</td>"
        f"<td>{html.escape(str(r.slice_name))}</td>"
        f"<td>{int(r.n)}</td>"
        f"<td>{html.escape(str(r.variable_block))}</td>"
        f"<td>{html.escape(str(r.model_name))}</td>"
        f"<td>{fmt(r.MdAPE)}</td>"
        f"<td>{fmt(r.p95_APE)}</td>"
        f"<td>{fmt(r.R2)}</td>"
        "</tr>"
        for r in summary.itertuples()
    )
    class_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(r.scope))}</td>"
        f"<td>{html.escape(str(r.variable_block))}</td>"
        f"<td>{html.escape(str(r.model_name))}</td>"
        f"<td>{html.escape(str(r.slice_name))}</td>"
        f"<td>{int(r.n)}</td>"
        f"<td>{fmt(r.MdAPE)}</td>"
        f"<td>{fmt(r.p95_APE)}</td>"
        "</tr>"
        for r in slice_df[slice_df["slice_type"].eq("edition_class")]
        .sort_values(["scope", "variable_block", "model_code", "slice_name"])
        .itertuples()
    )
    html_text = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>A7 에디션 slice 분석</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }}
    .card {{ background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fffdf8; }}
    th, td {{ border: 1px solid #d6c7ad; padding: 9px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #e8dcc8; }}
    code {{ background: #eee6d6; padding: 2px 5px; border-radius: 5px; }}
  </style>
</head>
<body>
  <section class="card">
    <h1>A7 에디션 slice 분석</h1>
    <ul>
      <li>{html.escape(notes['purpose'])}</li>
      <li>{html.escape(notes['sample_warning'])}</li>
      <li>{html.escape(notes['cold_note'])}</li>
      <li>{html.escape(notes['signed_note'])}</li>
    </ul>
  </section>
  <section class="card">
    <h2>slice별 최고 조합</h2>
    <table>
      <tr><th>평가</th><th>slice</th><th>n</th><th>변수</th><th>모델</th><th>MdAPE</th><th>p95 APE</th><th>R2</th></tr>
      {top_rows}
    </table>
  </section>
  <section class="card">
    <h2>edition_class 상세 결과</h2>
    <table>
      <tr><th>평가</th><th>변수</th><th>모델</th><th>edition_class</th><th>n</th><th>MdAPE</th><th>p95 APE</th></tr>
      {class_rows}
    </table>
  </section>
</body>
</html>
"""
    (out_dir / "edition_slice_report.html").write_text(html_text, encoding="utf-8")
    print(summary[["scope", "slice_name", "n", "variable_block", "model_name", "MdAPE", "p95_APE", "R2"]].to_string(index=False))


if __name__ == "__main__":
    main()
