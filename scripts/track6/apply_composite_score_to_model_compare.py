#!/usr/bin/env python3
"""Add composite model-selection scores to Track6 WM1/CM1 reports.

The score is a reporting layer only. It does not change model training or raw
metrics. Each metric is normalized within the experiment result table so that
100 is best and 0 is worst, then combined with Warm/Cold-specific weights.
"""
from __future__ import annotations

import argparse
import html
from datetime import datetime
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]

WEIGHTS = {
    "warm": {
        "MdAPE": 0.45,
        "Within_30": 0.20,
        "p95_APE": 0.20,
        "RMSE_log": 0.10,
        "R2": 0.05,
    },
    "cold": {
        "MdAPE": 0.35,
        "p95_APE": 0.30,
        "Within_30": 0.20,
        "RMSE_log": 0.10,
        "R2": 0.05,
    },
}

LOWER_IS_BETTER = {"MdAPE", "p95_APE", "RMSE_log"}
HIGHER_IS_BETTER = {"Within_30", "R2"}


def fmt(v: float) -> str:
    return "" if pd.isna(v) else f"{float(v):.4f}"


def score_series(s: pd.Series, lower_is_better: bool) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    min_v = s.min()
    max_v = s.max()
    if pd.isna(min_v) or pd.isna(max_v) or max_v == min_v:
        return pd.Series(100.0, index=s.index)
    if lower_is_better:
        return (max_v - s) / (max_v - min_v) * 100.0
    return (s - min_v) / (max_v - min_v) * 100.0


def add_scores(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    out = df.copy()
    weights = WEIGHTS[mode]
    for metric in weights:
        lower = metric in LOWER_IS_BETTER
        out[f"{metric}_score"] = score_series(out[metric], lower)
    out["composite_score"] = sum(out[f"{metric}_score"] * weight for metric, weight in weights.items())
    out["composite_rank"] = out["composite_score"].rank(ascending=False, method="min").astype(int)
    return out.sort_values(["composite_rank", "MdAPE", "p95_APE"]).reset_index(drop=True)


def readable_features(feature_set: str, features: str) -> str:
    replacements = {
        "total_works_x_log_area": "artist_meta_total_works x log_area",
        "followers_x_log_area": "artist_meta_followers x log_area",
        "for_sale_works_x_log_area": "artist_meta_for_sale_works x log_area",
        "total_works_x_ln_ho": "artist_meta_total_works x ln_estimated_ho",
        "followers_x_ln_ho": "artist_meta_followers x ln_estimated_ho",
        "for_sale_works_x_ln_ho": "artist_meta_for_sale_works x ln_estimated_ho",
    }
    parts = [p.strip() for p in str(features).split(",") if p.strip()]
    if any(p.startswith("log_area_x_artist_name_ko_") for p in parts):
        base = [p for p in parts if not p.startswith("log_area_x_artist_name_ko_")]
        return ", ".join(base) + ", log_area x artist_name_ko(상위 10명 교차항)"
    if any(p.startswith("ln_ho_x_artist_name_ko_") for p in parts):
        base = [p for p in parts if not p.startswith("ln_ho_x_artist_name_ko_")]
        return ", ".join(base) + ", ln_estimated_ho x artist_name_ko(상위 10명 교차항)"
    return ", ".join(replacements.get(p, p) for p in parts)


def row_html(row: pd.Series, include_status: bool = False) -> str:
    status_cell = f"<td>{html.escape(str(row.get('status', '')))}</td>" if include_status else ""
    return (
        "<tr>"
        f"<td>{int(row['composite_rank'])}</td>"
        f"<td>{fmt(row['composite_score'])}</td>"
        f"<td>{html.escape(str(row['feature_set']))}<br><code>{html.escape(readable_features(str(row['feature_set']), str(row['features'])))}</code></td>"
        f"<td>{html.escape(str(row['model_name']))}</td>"
        f"{status_cell}"
        f"<td>{fmt(row['MdAPE'])}</td>"
        f"<td>{fmt(row['p95_APE'])}</td>"
        f"<td>{fmt(row['Within_30'])}</td>"
        f"<td>{fmt(row['RMSE_log'])}</td>"
        f"<td>{fmt(row['R2'])}</td>"
        "</tr>"
    )


def render_html(exp_dir: Path, df: pd.DataFrame, mode: str, title: str) -> str:
    weights = WEIGHTS[mode]
    best = df.iloc[0]
    by_feature = (
        df.sort_values(["feature_set", "composite_rank", "MdAPE"])
        .groupby("feature_set", as_index=False)
        .first()
        .sort_values(["composite_rank", "MdAPE"])
    )
    weight_rows = "".join(
        f"<tr><td>{html.escape(metric)}</td><td>{int(weight * 100)}%</td><td>{'낮을수록 좋음' if metric in LOWER_IS_BETTER else '높을수록 좋음'}</td></tr>"
        for metric, weight in weights.items()
    )
    by_feature_rows = "".join(row_html(row) for _, row in by_feature.iterrows())
    all_rows = "".join(row_html(row, include_status=True) for _, row in df.iterrows())
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }}
    .card {{ background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fffdf8; }}
    th, td {{ border: 1px solid #d6c7ad; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #e8dcc8; }}
    code {{ background: #eee6d6; padding: 2px 5px; border-radius: 5px; }}
  </style>
</head>
<body>
  <section class="card">
    <h1>{html.escape(title)}</h1>
    <ul>
      <li>종합 점수 1위: <code>{html.escape(str(best['feature_set']))}</code> + <code>{html.escape(str(best['model_name']))}</code> / {fmt(best['composite_score'])}점</li>
      <li>점수 방식: 각 지표를 0~100점으로 변환한 뒤 가중 평균으로 계산</li>
      <li>주의: 종합 점수는 후보 선택 보조 기준이며, 원 지표도 함께 확인해야 함</li>
      <li>생성일: <code>{datetime.now().isoformat(timespec='seconds')}</code></li>
    </ul>
  </section>
  <section class="card">
    <h2>가중치 기준</h2>
    <table><thead><tr><th>지표</th><th>비중</th><th>방향</th></tr></thead><tbody>{weight_rows}</tbody></table>
  </section>
  <section class="card">
    <h2>피처 조합별 종합 1위</h2>
    <table><thead><tr><th>순위</th><th>종합 점수</th><th>피처 조합 / 실제 피처명</th><th>모델</th><th>MdAPE</th><th>p95_APE</th><th>Within_30</th><th>RMSE_log</th><th>R2</th></tr></thead><tbody>{by_feature_rows}</tbody></table>
  </section>
  <section class="card">
    <h2>전체 결과</h2>
    <table><thead><tr><th>순위</th><th>종합 점수</th><th>피처 조합 / 실제 피처명</th><th>모델</th><th>상태</th><th>MdAPE</th><th>p95_APE</th><th>Within_30</th><th>RMSE_log</th><th>R2</th></tr></thead><tbody>{all_rows}</tbody></table>
  </section>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("exp_dir", type=Path)
    parser.add_argument("--mode", choices=["warm", "cold"], required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    exp_dir = args.exp_dir
    metrics_path = exp_dir / "outputs" / "metrics_long.csv"
    df = pd.read_csv(metrics_path)
    df = df[df["status"].eq("ok")].copy()
    scored = add_scores(df, args.mode)

    out_csv = exp_dir / "outputs" / "metrics_scored.csv"
    out_csv_all = exp_dir / "outputs" / "result_sheet_scored.csv"
    out_html = exp_dir / "outputs" / "result_sheet.html"
    scored.to_csv(out_csv, index=False)
    scored.to_csv(out_csv_all, index=False)
    out_html.write_text(render_html(exp_dir, scored, args.mode, args.title), encoding="utf-8")
    print(scored[["composite_rank", "composite_score", "feature_set", "model_name", "MdAPE", "p95_APE", "Within_30", "RMSE_log", "R2"]].head(12).to_string(index=False))


if __name__ == "__main__":
    main()
