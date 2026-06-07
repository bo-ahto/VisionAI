#!/usr/bin/env python3
"""Summarize Track6 Group H/I/J experiment results."""
from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
OUT_MD = DOC_ROOT / "group_h_i_j_execution_summary.md"
OUT_HTML = DOC_ROOT / "group_h_i_j_execution_summary.html"
OUT_CSV = DOC_ROOT / "group_h_i_j_summary_table.csv"


EXPERIMENT_DIRS = [
    "H1_artist_name_x_ln_ho",
    "H5_artist_name_x_depth",
    "I1_ho_birth_exhibition_cold_candidate",
    "I2_basic_artwork_birth_exhibition_cold_candidate",
    "I3_basic_artwork_activity_popularity_cold_candidate",
    "I5_basic_artwork_market_exposure_information",
    "I6_extended_size_full_artist_meta",
    "J1_profile_x_ln_ho",
    "J2_profile_x_material",
    "J3_profile_x_support",
    "J4_activity_popularity_x_ln_ho",
    "J5_activity_popularity_x_log_area",
    "J6_profile_x_material",
    "J7_market_exposure_x_depth",
]

DUPLICATE_MAPPINGS = [
    ("H2", "D8", "작가명 x 면적은 기존 D8 실험으로 대체"),
    ("H3", "D9", "작가명 x 재료는 기존 D9 실험으로 대체"),
    ("H4", "D10", "작가명 x 지지체는 기존 D10 실험으로 대체"),
    ("I4", "G8", "작품 기본 피처 + 기본 작가 프로필은 기존 G8 실험으로 대체"),
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fmt(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def read_config(folder: str) -> dict[str, Any]:
    path = EXP_ROOT / folder / "experiment_config.json"
    return json.loads(path.read_text(encoding="utf-8"))


def best_rows(frame: pd.DataFrame, config: dict[str, Any], folder: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scope in ["Warm", "Cold"]:
        sub = frame[frame["scope"].eq(scope)].copy()
        if sub.empty:
            continue
        best = sub.sort_values(["MdAPE", "p95_APE", "RMSE_log"]).iloc[0]
        baseline = sub[sub["variable_block"].astype(str).str.contains("기준", na=False)]
        delta = None
        baseline_block = "-"
        baseline_mdape = None
        if not baseline.empty:
            baseline_best = baseline.sort_values(["MdAPE", "p95_APE", "RMSE_log"]).iloc[0]
            baseline_block = baseline_best["variable_block"]
            baseline_mdape = float(baseline_best["MdAPE"])
            delta = baseline_mdape - float(best["MdAPE"])
        rows.append(
            {
                "실험 ID": config["experiment_id"],
                "그룹": config["experiment_id"][0],
                "실험명": config["purpose"],
                "범위": scope,
                "기준 변수 블록": baseline_block,
                "기준 MdAPE": baseline_mdape,
                "최고 변수 블록": best["variable_block"],
                "최고 모델": best["model_name"],
                "R2": float(best["R2"]),
                "RMSE_log": float(best["RMSE_log"]),
                "MdAPE": float(best["MdAPE"]),
                "p95_APE": float(best["p95_APE"]),
                "기준선 대비 MdAPE 개선": delta,
                "결과 HTML": rel(EXP_ROOT / folder / "outputs" / "result_sheet.html"),
            }
        )
    return rows


def interpret(row: pd.Series) -> str:
    delta = row["기준선 대비 MdAPE 개선"]
    scope = row["범위"]
    exp_id = str(row["실험 ID"])
    mdape = float(row["MdAPE"])
    p95 = float(row["p95_APE"])
    if pd.isna(delta):
        return "기준선이 없어 절대 성능만 참고"
    if delta >= 0.03:
        return f"{scope}에서 명확한 개선 후보"
    if delta >= 0.01:
        return f"{scope}에서 소폭 개선 후보"
    if delta > 0:
        return f"{scope}에서 개선폭이 작아 보류"
    if exp_id.startswith("J") and mdape > 0.65:
        return "교차항 복잡도 대비 성능 약함"
    if p95 > 5:
        return "대표 오차보다 큰 오차 위험이 커서 보류"
    return "기준선 개선 없음"


def load_summary() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for folder in EXPERIMENT_DIRS:
        config = read_config(folder)
        metrics_path = EXP_ROOT / folder / "outputs" / "metrics_long.csv"
        if not metrics_path.exists():
            rows.append(
                {
                    "실험 ID": config["experiment_id"],
                    "그룹": config["experiment_id"][0],
                    "실험명": config["purpose"],
                    "범위": "미실행",
                    "기준 변수 블록": "-",
                    "기준 MdAPE": None,
                    "최고 변수 블록": "-",
                    "최고 모델": "-",
                    "R2": None,
                    "RMSE_log": None,
                    "MdAPE": None,
                    "p95_APE": None,
                    "기준선 대비 MdAPE 개선": None,
                    "결과 HTML": rel(EXP_ROOT / folder / "outputs" / "result_sheet.html"),
                }
            )
            continue
        rows.extend(best_rows(pd.read_csv(metrics_path), config, folder))
    frame = pd.DataFrame(rows)
    frame["해석"] = frame.apply(interpret, axis=1)
    return frame


def table_md(frame: pd.DataFrame, columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def table_html(frame: pd.DataFrame, columns: list[str]) -> str:
    headers = "".join(f"<th>{html.escape(col)}</th>" for col in columns)
    body = []
    for _, row in frame.iterrows():
        cells = []
        for col in columns:
            value = fmt(row[col])
            if col == "결과 HTML" and value != "-":
                cells.append(f'<td><a href="../../../{html.escape(value)}">열기</a></td>')
            else:
                cells.append(f"<td>{html.escape(value)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def main() -> None:
    DOC_ROOT.mkdir(parents=True, exist_ok=True)
    summary = load_summary()
    summary.to_csv(OUT_CSV, index=False)

    cols = [
        "실험 ID",
        "실험명",
        "범위",
        "기준 MdAPE",
        "최고 변수 블록",
        "최고 모델",
        "MdAPE",
        "p95_APE",
        "기준선 대비 MdAPE 개선",
        "해석",
        "결과 HTML",
    ]
    warm_best = summary[summary["범위"].eq("Warm")].sort_values(["MdAPE", "p95_APE"]).head(7)
    cold_best = summary[summary["범위"].eq("Cold")].sort_values(["MdAPE", "p95_APE"]).head(7)
    duplicates = pd.DataFrame(DUPLICATE_MAPPINGS, columns=["실험 ID", "대체 실험", "처리"])

    md = [
        "# Track6 Group H/I/J 실행 결과 종합",
        "",
        f"- 생성일: `{date.today().isoformat()}`",
        "- Group H: 작가명과 작품 변수의 교차항 검증",
        "- Group I: 작가명 없이 작품 기본 변수와 작가 메타를 결합한 Cold 후보 검증",
        "- Group J: 작가 메타와 작품 변수의 교차항 검증",
        "- 중복 실험은 재실행하지 않고 기존 D/G 실험으로 매핑",
        "",
        "## 핵심 결론",
        "",
        "- Warm에서는 `H1 작가명 x 호수`가 작가명+호수 기준선보다 MdAPE를 낮췄지만 p95가 일부 악화되어 보류 후보이다.",
        "- Cold MdAPE만 보면 `J5 활동량/인지도 x 면적`이 가장 낮지만, p95는 `I3/I5 작품 기본 피처 + 활동량/인지도/정보량` 계열이 더 안정적이다.",
        "- J 그룹은 `활동량/인지도 x 호수/면적` 외에는 복잡도 대비 개선이 약하다. 기본 프로필 x 재료/지지체 계열은 현재 최종 후보로 보기 어렵다.",
        "- H2/H3/H4/I4는 기존 D8/D9/D10/G8과 실험 목적이 겹쳐 중복 실행하지 않았다.",
        "",
        "## Warm 상위 후보",
        "",
        table_md(warm_best, cols),
        "",
        "## Cold 상위 후보",
        "",
        table_md(cold_best, cols),
        "",
        "## 중복 매핑",
        "",
        table_md(duplicates, list(duplicates.columns)),
        "",
        "## 전체 H/I/J 결과",
        "",
        table_md(summary, cols),
    ]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    css = """
body { font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }
section { background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }
h1 { margin-top: 0; font-size: 36px; }
table { width: 100%; border-collapse: collapse; background: #fffdf8; }
th, td { border: 1px solid #d6c7ad; padding: 9px 10px; text-align: left; vertical-align: top; font-size: 13px; }
th { background: #e8dcc8; }
code { background: #eee6d6; padding: 2px 5px; border-radius: 5px; }
.wrap { overflow: auto; }
"""
    html_text = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Track6 Group H/I/J 실행 결과 종합</title>
  <style>{css}</style>
</head>
<body>
  <section>
    <h1>Track6 Group H/I/J 실행 결과 종합</h1>
    <ul>
      <li>생성일: <code>{date.today().isoformat()}</code></li>
      <li>Group H: 작가명과 작품 변수의 교차항 검증</li>
      <li>Group I: 작가명 없이 작품 기본 변수와 작가 메타를 결합한 Cold 후보 검증</li>
      <li>Group J: 작가 메타와 작품 변수의 교차항 검증</li>
      <li>중복 실험은 기존 D/G 결과로 매핑</li>
    </ul>
  </section>
  <section>
    <h2>핵심 결론</h2>
    <ul>
      <li>Warm: <code>H1 작가명 x 호수</code>는 MdAPE를 낮췄지만 p95가 일부 악화되어 보류 후보입니다.</li>
      <li>Cold MdAPE: <code>J5 활동량/인지도 x 면적</code>이 가장 낮습니다.</li>
      <li>Cold 안정성: <code>I3/I5 작품 기본 피처 + 활동량/인지도/정보량</code> 계열이 p95까지 함께 봤을 때 더 실용적인 후보입니다.</li>
      <li>J 그룹은 활동량/인지도 x 호수/면적 외에는 복잡도 대비 개선이 약합니다.</li>
    </ul>
  </section>
  <section><h2>Warm 상위 후보</h2><div class="wrap">{table_html(warm_best, cols)}</div></section>
  <section><h2>Cold 상위 후보</h2><div class="wrap">{table_html(cold_best, cols)}</div></section>
  <section><h2>중복 매핑</h2><div class="wrap">{table_html(duplicates, list(duplicates.columns))}</div></section>
  <section><h2>전체 H/I/J 결과</h2><div class="wrap">{table_html(summary, cols)}</div></section>
</body>
</html>
"""
    OUT_HTML.write_text(html_text, encoding="utf-8")
    print(OUT_MD)
    print(OUT_HTML)
    print(OUT_CSV)


if __name__ == "__main__":
    main()
