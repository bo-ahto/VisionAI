#!/usr/bin/env python3
"""Revalidate the v0.1 fixed_125_width range policy with bootstraps."""

from __future__ import annotations

from html import escape
from pathlib import Path

import numpy as np
import pandas as pd


def find_repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


REPO = find_repo_root()
EXP_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

PRED_PATH = (
    REPO
    / "models/track6/price_prediction_v0.1/evidence/experiments/"
    / "PP-V8_warm_deployment_simplification/outputs/predictions.csv"
)
VAL_FEATURE_PATH = REPO / "models/track6/price_prediction_v0.1/data/training/track6_split/track6_val_warm.csv"
TEST_FEATURE_PATH = REPO / "models/track6/price_prediction_v0.1/data/training/track6_split/track6_test_warm.csv"
BASE_CANDIDATE = "compact_blend_mape_guarded"
SEEDS = list(range(2026060500, 2026060600))


def fmt_float(value: float | int, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.{digits}f}"


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_데이터 없음_"

    def clean(value: object) -> str:
        if pd.isna(value):
            return ""
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(clean(col) for col in df.columns) + " |",
        "| " + " | ".join("---" for _ in df.columns) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(clean(row[col]) for col in df.columns) + " |")
    return "\n".join(lines)


def markdown_to_html(markdown: str) -> str:
    html_lines: list[str] = []
    in_table = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if in_table and not (line.startswith("| ") and line.endswith(" |")):
            html_lines.append("</table>")
            in_table = False
        if not line:
            continue
        if line.startswith("| ") and line.endswith(" |"):
            cells = [escape(cell.strip()) for cell in line.strip("|").split("|")]
            if set(cells) == {"---"}:
                continue
            if not in_table:
                html_lines.append("<table>")
                html_lines.append("<tr>" + "".join(f"<th>{cell}</th>" for cell in cells) + "</tr>")
                in_table = True
            else:
                html_lines.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
            continue
        if line.startswith("# "):
            html_lines.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{escape(line[2:])}</li>")
        else:
            html_lines.append(f"<p>{escape(line)}</p>")
    if in_table:
        html_lines.append("</table>")
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>OP-V01-CAL-05 범위 정책 반복 검증</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.55; color: #1f2933; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 24px; font-size: 14px; }}
th, td {{ border: 1px solid #d8dee9; padding: 8px 10px; text-align: left; vertical-align: top; }}
th {{ background: #f3f6fa; }}
</style>
</head>
<body>
{chr(10).join(html_lines)}
</body>
</html>
"""


def load_data() -> pd.DataFrame:
    pred = pd.read_csv(PRED_PATH)
    pred = pred[
        (pred["candidate"] == BASE_CANDIDATE)
        & (pred["split"].isin(["validation", "test"]))
    ].copy()
    pred["_track6_row_id"] = pred["_track6_row_id"].astype(int)
    frames = []
    for split, path in [("validation", VAL_FEATURE_PATH), ("test", TEST_FEATURE_PATH)]:
        df = pd.read_csv(path, low_memory=False)
        df["split"] = split
        frames.append(df)
    features = pd.concat(frames, ignore_index=True)
    keep = [
        "split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "title_raw",
        "area_cm2",
        "artist_works_count_train",
        "medium_support_bucket",
    ]
    return pred.merge(features[[col for col in keep if col in features.columns]], on=["split", "_track6_row_id"], how="left")


def add_ranges(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for policy, multiplier in [("baseline", 1.0), ("fixed_125", 1.25)]:
        width = out["routing_width"].astype(float) * multiplier
        out[f"{policy}_low_log"] = out["pred_log"] - width / 2.0
        out[f"{policy}_high_log"] = out["pred_log"] + width / 2.0
        out[f"{policy}_range_ratio"] = np.exp(width)
        out[f"{policy}_contains"] = (
            (out["actual_log"] >= out[f"{policy}_low_log"])
            & (out["actual_log"] <= out[f"{policy}_high_log"])
        )
    out["actual_top5"] = False
    for split, frame in out.groupby("split"):
        cut = frame["actual_price"].quantile(0.95)
        out.loc[frame.index, "actual_top5"] = frame["actual_price"] >= cut
    out["severe_error"] = out["ape"] >= 1.0
    return out


def metrics_for(label: str, frame: pd.DataFrame) -> dict[str, object]:
    high = frame[frame["actual_top5"]]
    severe = frame[frame["severe_error"]]
    return {
        "sample": label,
        "n": len(frame),
        "baseline_coverage": float(frame["baseline_contains"].mean()),
        "fixed_125_coverage": float(frame["fixed_125_contains"].mean()),
        "delta_coverage": float(frame["fixed_125_contains"].mean() - frame["baseline_contains"].mean()),
        "baseline_p90_range_ratio": float(frame["baseline_range_ratio"].quantile(0.90)),
        "fixed_125_p90_range_ratio": float(frame["fixed_125_range_ratio"].quantile(0.90)),
        "width_penalty": float(frame["fixed_125_range_ratio"].quantile(0.90) / frame["baseline_range_ratio"].quantile(0.90)),
        "baseline_top5_coverage": float(high["baseline_contains"].mean()) if len(high) else np.nan,
        "fixed_125_top5_coverage": float(high["fixed_125_contains"].mean()) if len(high) else np.nan,
        "baseline_severe_coverage": float(severe["baseline_contains"].mean()) if len(severe) else np.nan,
        "fixed_125_severe_coverage": float(severe["fixed_125_contains"].mean()) if len(severe) else np.nan,
    }


def bootstrap_rows(test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(test)
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        idx = rng.choice(test.index.to_numpy(), size=n, replace=True)
        sample = test.loc[idx]
        row = metrics_for(f"row_bootstrap_{seed}", sample)
        row["mode"] = "row_bootstrap"
        row["seed"] = seed
        rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_artists(test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    artists = test["artist_key"].fillna("(missing)").drop_duplicates().to_numpy()
    artist_map = {artist: group.index.to_numpy() for artist, group in test.groupby(test["artist_key"].fillna("(missing)"))}
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        sampled_artists = rng.choice(artists, size=len(artists), replace=True)
        idx = np.concatenate([artist_map[artist] for artist in sampled_artists])
        sample = test.loc[idx]
        row = metrics_for(f"artist_bootstrap_{seed}", sample)
        row["mode"] = "artist_bootstrap"
        row["seed"] = seed
        row["sampled_artists"] = len(sampled_artists)
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_bootstrap(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mode, frame in df.groupby("mode"):
        rows.append(
            {
                "mode": mode,
                "runs": len(frame),
                "delta_coverage_mean": frame["delta_coverage"].mean(),
                "delta_coverage_std": frame["delta_coverage"].std(),
                "delta_coverage_min": frame["delta_coverage"].min(),
                "delta_coverage_p05": frame["delta_coverage"].quantile(0.05),
                "delta_coverage_median": frame["delta_coverage"].median(),
                "delta_coverage_max": frame["delta_coverage"].max(),
                "positive_delta_rate": (frame["delta_coverage"] > 0).mean(),
                "width_penalty_median": frame["width_penalty"].median(),
                "width_penalty_p95": frame["width_penalty"].quantile(0.95),
            }
        )
    return pd.DataFrame(rows)


def format_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda x: fmt_float(x, 4))
    return out


def build_report(overall: pd.DataFrame, summary: pd.DataFrame, bootstrap: pd.DataFrame) -> str:
    test_row = overall[overall["sample"] == "test"].iloc[0]
    row_rate = summary.loc[summary["mode"] == "row_bootstrap", "positive_delta_rate"].iloc[0]
    artist_rate = summary.loc[summary["mode"] == "artist_bootstrap", "positive_delta_rate"].iloc[0]
    verdict = "채택 보류"
    if test_row["delta_coverage"] > 0 and row_rate >= 0.95 and artist_rate >= 0.95:
        verdict = "범위/신뢰도 보정 후보 유지"
    return f"""# OP-V01-CAL-05 범위 정책 반복 검증 결과

## 1. 실행 요약

- 기준 정책: `baseline`
- 후보 정책: `fixed_125`
- 점가격: 변경 없음
- 검증 대상: 기존 Warm validation/test split
- 반복 검증: test row bootstrap 100회, test artist bootstrap 100회

## 2. validation/test 전체 지표

{md_table(format_frame(overall))}

## 3. bootstrap 요약

{md_table(format_frame(summary))}

## 4. 판단

- test 범위 포함률 변화: {fmt_float(test_row['delta_coverage'])}
- row bootstrap 양수 개선 비율: {fmt_float(row_rate)}
- artist bootstrap 양수 개선 비율: {fmt_float(artist_rate)}
- 판단: {verdict}

## 5. 해석

- `fixed_125`는 점가격을 바꾸지 않고 표시 범위만 25% 넓히는 정책이다.
- row bootstrap과 artist bootstrap 모두에서 포함률 개선이 반복되면, 특정 샘플에만 맞춘 결과일 가능성이 낮다.
- 이 검증은 모델 재학습 검증이 아니라 범위 표시 정책 검증이다.
- 이 결과는 운영 반영 승인이 아니라 범위/신뢰도 보정 후보 유지 판단이다.
- 운영 반영 전에는 별도 후보 출력 필드로 API/프론트 테스트를 진행해야 한다.

## 6. 산출물

- `outputs/overall_metrics.csv`
- `outputs/bootstrap_metrics.csv`
- `outputs/bootstrap_summary.csv`
- `outputs/test_predictions_with_ranges.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    df = add_ranges(load_data())
    val = df[df["split"] == "validation"].copy()
    test = df[df["split"] == "test"].copy()
    overall = pd.DataFrame([
        metrics_for("validation", val),
        metrics_for("test", test),
    ])
    row_boot = bootstrap_rows(test)
    artist_boot = bootstrap_artists(test)
    bootstrap = pd.concat([row_boot, artist_boot], ignore_index=True)
    summary = summarize_bootstrap(bootstrap)

    overall.to_csv(OUTPUT_DIR / "overall_metrics.csv", index=False)
    bootstrap.to_csv(OUTPUT_DIR / "bootstrap_metrics.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "bootstrap_summary.csv", index=False)
    test.to_csv(OUTPUT_DIR / "test_predictions_with_ranges.csv", index=False)
    report = build_report(overall, summary, bootstrap)
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(markdown_to_html(report), encoding="utf-8")


if __name__ == "__main__":
    main()
