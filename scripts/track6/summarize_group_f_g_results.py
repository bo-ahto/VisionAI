#!/usr/bin/env python3
"""Summarize Track6 Group F/G experiment results."""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
OUT_MD = REPO / "docs" / "track6" / "experiments" / "group_f_g_execution_summary.md"
OUT_HTML = REPO / "docs" / "track6" / "experiments" / "group_f_g_execution_summary.html"
OUT_CSV = REPO / "docs" / "track6" / "experiments" / "group_f_g_summary_table.csv"


EXPERIMENTS = [
    ("F1", "F1_artist_birth_exhibition_combo", "작가 생년 + 전시 경력 조합"),
    ("F2", "F2_artist_activity_popularity_combo", "작가 활동량 + 인지도 조합"),
    ("F3", "F3_artist_basic_profile_combo", "작가 기본 프로필 조합"),
    ("F4", "F4_artist_activity_popularity_information_combo", "활동량/인지도 + 정보량 조합"),
    ("F5", "F5_artist_full_meta_bundle", "전체 작가 메타 묶음"),
    ("G1", "G1_basic_artwork_plus_artist_name", "작품 기본 피처 + 작가명"),
    ("G2", "G2_basic_artwork_plus_artist_work_count", "작품 기본 피처 + 작가별 학습 작품 수"),
    ("G3", "G3_basic_artwork_plus_birth_year", "작품 기본 피처 + 작가 생년"),
    ("G4", "G4_basic_artwork_plus_exhibition_counts", "작품 기본 피처 + 전시 경력"),
    ("G5", "G5_basic_artwork_plus_nationality", "작품 기본 피처 + 작가 국적"),
    ("G6", "G6_basic_artwork_plus_activity", "작품 기본 피처 + 작가 활동량"),
    ("G7", "G7_basic_artwork_plus_popularity", "작품 기본 피처 + 작가 인지도"),
    ("G8", "G8_basic_artwork_plus_basic_profile", "작품 기본 피처 + 기본 작가 프로필"),
    ("G9", "G9_basic_artwork_plus_full_artist_meta", "작품 기본 피처 + 전체 작가 메타"),
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fmt(value: float) -> str:
    return f"{float(value):.4f}"


def best_rows(frame: pd.DataFrame, exp_id: str, title: str, folder: str) -> list[dict[str, object]]:
    rows = []
    for scope in ["Warm", "Cold"]:
        sub = frame[frame["scope"].eq(scope)].copy()
        best = sub.sort_values(["MdAPE", "p95_APE", "RMSE_log"]).iloc[0]
        baseline = sub[sub["variable_block"].eq("작품 기본 피처")]
        delta = None
        if len(baseline):
            baseline_best = baseline.sort_values(["MdAPE", "p95_APE", "RMSE_log"]).iloc[0]
            delta = float(baseline_best["MdAPE"] - best["MdAPE"])
        rows.append(
            {
                "실험 ID": exp_id,
                "그룹": exp_id[0],
                "실험명": title,
                "범위": scope,
                "최고 변수 블록": best["variable_block"],
                "최고 모델": best["model_name"],
                "MdAPE": float(best["MdAPE"]),
                "p95_APE": float(best["p95_APE"]),
                "RMSE_log": float(best["RMSE_log"]),
                "R2": float(best["R2"]),
                "기준선 대비 MdAPE 개선": delta,
                "결과 HTML": rel(EXP_ROOT / folder / "outputs" / "result_sheet.html"),
            }
        )
    return rows


def decision(row: pd.Series) -> str:
    exp_id = str(row["실험 ID"])
    scope = str(row["범위"])
    delta = row["기준선 대비 MdAPE 개선"]
    mdape = float(row["MdAPE"])
    if exp_id.startswith("F"):
        if mdape < 0.55:
            return "단독 메타 모델로는 일부 신호가 있으나 최종 피처는 G 그룹 통제 결과 기준으로 판단"
        return "단독 메타만으로는 약함"
    if pd.notna(delta) and float(delta) > 0.02:
        return f"{scope}에서 기준선 대비 개선"
    if pd.notna(delta) and float(delta) > 0:
        return f"{scope}에서 소폭 개선"
    return f"{scope}에서 기준선 개선 없음"


def load_summary() -> pd.DataFrame:
    rows = []
    for exp_id, folder, title in EXPERIMENTS:
        path = EXP_ROOT / folder / "outputs" / "metrics_long.csv"
        if not path.exists():
            rows.append(
                {
                    "실험 ID": exp_id,
                    "그룹": exp_id[0],
                    "실험명": title,
                    "범위": "미실행",
                    "최고 변수 블록": "-",
                    "최고 모델": "-",
                    "MdAPE": None,
                    "p95_APE": None,
                    "RMSE_log": None,
                    "R2": None,
                    "기준선 대비 MdAPE 개선": None,
                    "결과 HTML": rel(EXP_ROOT / folder / "outputs" / "result_sheet.html"),
                }
            )
            continue
        rows.extend(best_rows(pd.read_csv(path), exp_id, title, folder))
    out = pd.DataFrame(rows)
    out["해석"] = out.apply(decision, axis=1)
    return out


def load_g10() -> tuple[pd.DataFrame, pd.DataFrame]:
    base = EXP_ROOT / "G10_low_history_artist_routing" / "outputs"
    metrics = pd.read_csv(base / "metrics_summary.csv") if (base / "metrics_summary.csv").exists() else pd.DataFrame()
    slices = pd.read_csv(base / "warm_artist_count_slice_metrics.csv") if (base / "warm_artist_count_slice_metrics.csv").exists() else pd.DataFrame()
    return metrics, slices


def table_md(frame: pd.DataFrame, columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for _, row in frame.iterrows():
        cells = []
        for col in columns:
            value = row[col]
            if isinstance(value, float):
                value = fmt(value)
            elif pd.isna(value):
                value = "-"
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def table_html(frame: pd.DataFrame, columns: list[str]) -> str:
    headers = "".join(f"<th>{html.escape(col)}</th>" for col in columns)
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for col in columns:
            value = row[col]
            if isinstance(value, float):
                value = fmt(value)
            elif pd.isna(value):
                value = "-"
            if col == "결과 HTML" and value != "-":
                value = f'<a href="../../../{html.escape(str(value))}">열기</a>'
                cells.append(f"<td>{value}</td>")
            else:
                cells.append(f"<td>{html.escape(str(value))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def main() -> None:
    summary = load_summary()
    g10_metrics, g10_slices = load_g10()
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_CSV, index=False)

    cols = ["실험 ID", "실험명", "범위", "최고 변수 블록", "최고 모델", "MdAPE", "p95_APE", "기준선 대비 MdAPE 개선", "해석", "결과 HTML"]
    warm_best = summary[summary["범위"].eq("Warm")].sort_values(["MdAPE", "p95_APE"]).head(5)
    cold_best = summary[summary["범위"].eq("Cold")].sort_values(["MdAPE", "p95_APE"]).head(5)
    md = [
        "# Track6 Group F/G 실행 결과 종합",
        "",
        f"- 생성일: `{date.today().isoformat()}`",
        "- Group F: 작가 메타 변수 조합을 작가명 없이 단독으로 검증",
        "- Group G: 작품 기본 피처 묶음(`ln_estimated_ho + nant_material_idx + nant_tool + nant_support`)을 기준선으로 두고 작가명/작가 메타 추가 효과 검증",
        "- G10: 작가별 학습 작품 수 구간별 Warm 모델과 Cold 방식 모델 라우팅 비교",
        "",
        "## 핵심 결론",
        "",
        "- Warm에서는 `작품 기본 피처 + 작가명`이 가장 강한 개선을 보였다. 작가명은 Warm 최종 후보에서 핵심 피처로 유지할 근거가 있다.",
        "- Cold에서는 작가명이 직접 도움이 되지 않으므로 `작품 기본 피처 + 활동량/판매 노출량` 또는 `전체 작가 메타`를 후보로 두되, 메타 수집 재현성과 결측률을 같이 봐야 한다.",
        "- 작가 메타 단독(Group F)은 최종 모델 후보라기보다 보조 피처 후보를 고르는 사전 검증 성격이 강하다.",
        "- G10 기준 공식 Warm test의 5~9개 작가 구간에서도 Warm 작가 모델이 Cold 방식보다 안정적이었다. 다만 Track6 공식 Warm test에는 5개 미만 구간이 없어 1~4개 저이력 작가 정책은 별도 split이 필요하다.",
        "",
        "## Warm 상위 후보",
        "",
        table_md(warm_best, cols),
        "",
        "## Cold 상위 후보",
        "",
        table_md(cold_best, cols),
        "",
        "## 전체 F/G 결과",
        "",
        table_md(summary, cols),
        "",
        "## G10 라우팅 결과",
        "",
    ]
    if not g10_metrics.empty:
        md.append(table_md(g10_metrics, list(g10_metrics.columns)))
    if not g10_slices.empty:
        md.extend(["", "### Warm test 작가별 학습 작품 수 구간", "", table_md(g10_slices, list(g10_slices.columns))])
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    OUT_HTML.write_text(
        f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Track6 Group F/G 실행 결과 종합</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }}
    section {{ background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }}
    h1 {{ margin-top: 0; font-size: 36px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fffdf8; }}
    th, td {{ border: 1px solid #d6c7ad; padding: 9px 10px; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: #e8dcc8; }}
    code {{ background: #eee6d6; padding: 2px 5px; border-radius: 5px; }}
    .wrap {{ overflow:auto; }}
  </style>
</head>
<body>
  <section>
    <h1>Track6 Group F/G 실행 결과 종합</h1>
    <ul>
      <li>생성일: <code>{date.today().isoformat()}</code></li>
      <li>Group F: 작가 메타 변수 조합을 작가명 없이 단독 검증</li>
      <li>Group G: 작품 기본 피처 묶음을 기준선으로 작가명/작가 메타 추가 효과 검증</li>
      <li>G10: 작가별 학습 작품 수 구간별 Warm 모델과 Cold 방식 모델 라우팅 비교</li>
    </ul>
  </section>
  <section>
    <h2>핵심 결론</h2>
    <ul>
      <li>Warm은 <code>작품 기본 피처 + 작가명</code>이 가장 강하게 개선됐다.</li>
      <li>Cold는 작가명보다 작품 기본 피처에 활동량/판매 노출량 또는 전체 메타를 붙인 후보가 더 의미 있다.</li>
      <li>Group F 단독 메타는 최종 모델보다는 보조 피처 후보 선별용으로 해석한다.</li>
      <li>G10에서는 5~9개 구간도 Warm 작가 모델이 Cold 방식보다 안정적이었다. 5개 미만 구간은 공식 split에 없어 별도 검증이 필요하다.</li>
    </ul>
  </section>
  <section><h2>Warm 상위 후보</h2><div class="wrap">{table_html(warm_best, cols)}</div></section>
  <section><h2>Cold 상위 후보</h2><div class="wrap">{table_html(cold_best, cols)}</div></section>
  <section><h2>전체 F/G 결과</h2><div class="wrap">{table_html(summary, cols)}</div></section>
  <section><h2>G10 전체 성능</h2><div class="wrap">{table_html(g10_metrics, list(g10_metrics.columns)) if not g10_metrics.empty else '<p>결과 없음</p>'}</div></section>
  <section><h2>G10 구간별 성능</h2><div class="wrap">{table_html(g10_slices, list(g10_slices.columns)) if not g10_slices.empty else '<p>결과 없음</p>'}</div></section>
</body>
</html>
""",
        encoding="utf-8",
    )
    print(OUT_MD)
    print(OUT_HTML)
    print(OUT_CSV)


if __name__ == "__main__":
    main()
