#!/usr/bin/env python3
"""Generate Track 6 experiment dashboard from Markdown management tables."""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs" / "track6"
HYPOTHESIS_TABLE = DOCS / "tables" / "hypothesis_table.md"
RESULTS_TABLE = DOCS / "tables" / "experiment_results_table.md"
SPLIT_REPORT = DOCS / "dataset" / "split_report.md"
OUT_PATH = DOCS / "dashboard" / "experiment_dashboard.html"


def split_md_row(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def parse_tables(path: Path) -> list[list[dict[str, str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    tables: list[list[dict[str, str]]] = []
    idx = 0
    while idx < len(lines):
        if not lines[idx].startswith("|") or idx + 1 >= len(lines) or not re.match(r"^\|\s*-", lines[idx + 1]):
            idx += 1
            continue
        headers = split_md_row(lines[idx])
        idx += 2
        rows: list[dict[str, str]] = []
        while idx < len(lines) and lines[idx].startswith("|"):
            cells = split_md_row(lines[idx])
            if len(cells) >= len(headers):
                rows.append(dict(zip(headers, cells)))
            idx += 1
        tables.append(rows)
    return tables


def inline_md(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def id_number(value: str, prefix: str) -> int:
    match = re.search(rf"{re.escape(prefix)}(\d+)", value)
    return int(match.group(1)) if match else -1


def status_class(status: str) -> str:
    if "완료" in status:
        return "done"
    if "부분" in status or "진행" in status:
        return "partial"
    if "예정" in status or "보류" in status:
        return "hold"
    return "neutral"


def render_goals(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        f"<article><strong>{inline_md(r.get('목표 ID', ''))}</strong><h3>{inline_md(r.get('세부 목표', ''))}</h3><p>{inline_md(r.get('설명', ''))}</p></article>"
        for r in rows
    )


def render_hypotheses(rows: list[dict[str, str]]) -> str:
    rows = sorted(rows, key=lambda r: id_number(r.get("가설 ID", ""), "T6-H"), reverse=True)
    rendered = []
    for r in rows:
        status = r.get("현재 상태", "")
        rendered.append(
            "<tr>"
            f"<td>{inline_md(r.get('가설 ID', ''))}</td>"
            f"<td>{inline_md(r.get('세부 목표', ''))}</td>"
            f"<td><span class='status {status_class(status)}'>{html.escape(status)}</span></td>"
            f"<td>{inline_md(r.get('가설 요약', ''))}</td>"
            f"<td>{inline_md(r.get('연구 방법', ''))}</td>"
            f"<td>{inline_md(r.get('현재 판단', ''))}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def render_results(rows: list[dict[str, str]]) -> str:
    rows = sorted(rows, key=lambda r: (r.get("날짜", ""), id_number(r.get("실험 ID", ""), "T6-E")), reverse=True)
    rendered = []
    for r in rows:
        status = r.get("상태", "")
        rendered.append(
            "<tr>"
            f"<td>{inline_md(r.get('날짜', ''))}</td>"
            f"<td>{inline_md(r.get('실험 ID', ''))}</td>"
            f"<td>{inline_md(r.get('관련 가설', ''))}</td>"
            f"<td><span class='status {status_class(status)}'>{html.escape(status)}</span></td>"
            f"<td>{inline_md(r.get('사용 모델', ''))}</td>"
            f"<td>{inline_md(r.get('사용 피처', ''))}</td>"
            f"<td>{inline_md(r.get('Warm 결과 요약', ''))}</td>"
            f"<td>{inline_md(r.get('Cold 결과 요약', ''))}</td>"
            f"<td>{inline_md(r.get('결론', ''))}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def main() -> None:
    tables = parse_tables(HYPOTHESIS_TABLE)
    goal_rows = tables[0] if tables else []
    hypothesis_rows = tables[1] if len(tables) > 1 else []
    result_tables = parse_tables(RESULTS_TABLE)
    result_rows = result_tables[0] if result_tables else []
    done_count = sum(1 for r in hypothesis_rows if "완료" in r.get("현재 상태", ""))
    planned_count = sum(1 for r in hypothesis_rows if "예정" in r.get("현재 상태", ""))
    latest_h = max((r.get("가설 ID", "") for r in hypothesis_rows), key=lambda x: id_number(x, "T6-H"), default="-")
    latest_e = max((r.get("실험 ID", "") for r in result_rows), key=lambda x: id_number(x, "T6-E"), default="-")
    split_text = SPLIT_REPORT.read_text(encoding="utf-8") if SPLIT_REPORT.exists() else ""
    split_status = "생성 전" if "아직 split 생성 전" in split_text else "생성 완료"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Track 6 실험 대시보드</title>
  <style>
    :root {{ --bg:#eef2ec; --panel:#fffdf6; --ink:#17211b; --line:#d8d2c2; --green:#2f6f4e; --blue:#264f73; --amber:#a96a1f; }}
    body {{ margin:0; color:var(--ink); font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif; background:linear-gradient(135deg,#edf4ec,#f5ead9); line-height:1.55; }}
    main {{ max-width:1380px; margin:0 auto; padding:32px; }}
    .grid {{ display:grid; grid-template-columns:1.25fr .8fr; gap:20px; }}
    .panel {{ background:rgba(255,253,246,.95); border:1px solid var(--line); border-radius:24px; padding:24px; box-shadow:0 16px 40px rgba(35,30,20,.10); }}
    h1 {{ margin:0 0 14px; font-size:52px; letter-spacing:-.06em; }}
    h2 {{ margin:0 0 14px; }}
    code {{ background:rgba(38,79,115,.10); padding:1px 5px; border-radius:6px; }}
    .pills {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
    .pill {{ padding:7px 10px; background:#eadfcd; border-radius:999px; font-weight:800; font-size:12px; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:20px 0; }}
    .card, article {{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:16px; }}
    .card strong {{ display:block; font-size:24px; }}
    .card span, article p {{ color:#647064; font-size:13px; }}
    .goals {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
    article strong {{ display:inline-block; color:var(--green); margin-bottom:6px; }}
    article h3 {{ margin:0 0 6px; font-size:15px; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:18px; background:var(--panel); margin-top:14px; }}
    table {{ width:100%; border-collapse:collapse; min-width:1040px; }}
    th,td {{ padding:12px 14px; border-bottom:1px solid var(--line); vertical-align:top; font-size:13px; }}
    th {{ background:#eadfcd; text-align:left; position:sticky; top:0; }}
    .status {{ display:inline-flex; padding:4px 8px; border-radius:999px; font-weight:800; font-size:12px; }}
    .done {{ background:rgba(47,111,78,.14); color:var(--green); }}
    .hold {{ background:rgba(169,106,31,.14); color:var(--amber); }}
    .partial {{ background:rgba(38,79,115,.14); color:var(--blue); }}
    @media(max-width:900px) {{ .grid,.cards,.goals {{ grid-template-columns:1fr; }} main {{ padding:18px; }} }}
  </style>
</head>
<body>
<main>
  <section class="grid">
    <div class="panel">
      <h1>Track 6 실험 대시보드</h1>
      <ul>
        <li>Track5는 종료하고 Track6에서 최종 보고용 split을 새로 구성</li>
        <li>Cold는 작가 ID와 한글명 기준 중복을 함께 제거</li>
        <li>Warm은 train에 충분한 작품이 남는 작가 중심으로 평가</li>
        <li>모델 학습/예측은 feature 파일만 읽고, 정답 가격은 평가 단계에서만 사용</li>
        <li>validation에서 후보를 고르고 test는 최종 확인에만 사용</li>
      </ul>
      <div class="pills">
        <span class="pill">가설 {len(hypothesis_rows)}개</span>
        <span class="pill">완료 {done_count}개</span>
        <span class="pill">예정 {planned_count}개</span>
        <span class="pill">생성 {date.today().isoformat()}</span>
      </div>
    </div>
    <div class="panel">
      <h2>현재 상태</h2>
      <div class="cards" style="grid-template-columns:1fr 1fr;">
        <div class="card"><span>Split 상태</span><strong>{split_status}</strong></div>
        <div class="card"><span>최신 실험</span><strong>{html.escape(latest_e)}</strong></div>
        <div class="card"><span>최신 가설</span><strong>{html.escape(latest_h)}</strong></div>
        <div class="card"><span>다음 작업</span><strong>T6-E002</strong><span>누수 차단 기준 baseline</span></div>
      </div>
    </div>
  </section>

  <section class="panel" style="margin-top:20px;">
    <h2>세부 목표</h2>
    <div class="goals">{render_goals(goal_rows)}</div>
  </section>

  <section class="panel" style="margin-top:20px;">
    <h2>가설 상태</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>가설</th><th>목표</th><th>상태</th><th>요약</th><th>연구 방법</th><th>현재 판단</th></tr></thead>
        <tbody>{render_hypotheses(hypothesis_rows)}</tbody>
      </table>
    </div>
  </section>

  <section class="panel" style="margin-top:20px;">
    <h2>실험 결과</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>날짜</th><th>실험</th><th>가설</th><th>상태</th><th>모델</th><th>피처</th><th>Warm</th><th>Cold</th><th>결론</th></tr></thead>
        <tbody>{render_results(result_rows)}</tbody>
      </table>
    </div>
  </section>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    print(OUT_PATH)


if __name__ == "__main__":
    main()
