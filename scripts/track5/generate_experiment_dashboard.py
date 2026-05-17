#!/usr/bin/env python3
"""Generate a compact Track 5 experiment dashboard from Markdown tables."""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs" / "track5"
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


def inline_md_to_html(text: str) -> str:
    def link(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        href = html.escape(match.group(2))
        return f'<a href="{href}">{label}</a>'

    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, escaped)


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


def md_metric(label: str, text: str, default: str = "-") -> str:
    pattern = re.compile(rf"\| `{re.escape(label)}` \| `([^`]+)` \| `([^`]+)` \|")
    match = pattern.search(text)
    if not match:
        return default
    return f"{match.group(1)} / {match.group(2)}"


def split_metrics() -> dict[str, str]:
    text = SPLIT_REPORT.read_text(encoding="utf-8") if SPLIT_REPORT.exists() else ""
    return {
        "train": md_metric("train", text),
        "val_warm": md_metric("val_warm", text),
        "test_warm": md_metric("test_warm", text),
        "val_cold": md_metric("val_cold", text),
        "test_cold": md_metric("test_cold", text),
        "cold_overlap": "0",
    }


def render_goals(rows: list[dict[str, str]]) -> str:
    return "\n".join(
        f"<article><strong>{inline_md_to_html(r['목표 ID'])}</strong><h3>{inline_md_to_html(r['세부 목표'])}</h3><p>{inline_md_to_html(r['설명'])}</p></article>"
        for r in rows
    )


def render_hypotheses(rows: list[dict[str, str]]) -> str:
    rows = sorted(rows, key=lambda r: id_number(r.get("가설 ID", ""), "T5-H"), reverse=True)
    out = []
    for r in rows:
        status = r.get("현재 상태", "")
        out.append(
            "<tr>"
            f"<td>{inline_md_to_html(r.get('가설 ID', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('세부 목표', ''))}</td>"
            f"<td><span class='status {status_class(status)}'>{html.escape(status)}</span></td>"
            f"<td>{inline_md_to_html(r.get('가설 요약', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('연구 방법', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('현재 판단', ''))}</td>"
            "</tr>"
        )
    return "\n".join(out)


def render_results(rows: list[dict[str, str]]) -> str:
    rows = sorted(rows, key=lambda r: (r.get("날짜", ""), id_number(r.get("실험 ID", ""), "T5-E")), reverse=True)
    out = []
    for r in rows:
        status = r.get("상태", "")
        out.append(
            "<tr>"
            f"<td>{inline_md_to_html(r.get('날짜', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('실험 ID', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('관련 가설', ''))}</td>"
            f"<td><span class='status {status_class(status)}'>{html.escape(status)}</span></td>"
            f"<td>{inline_md_to_html(r.get('사용 모델', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('Warm 결과 요약', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('Cold 결과 요약', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('결론', ''))}</td>"
            f"<td>{inline_md_to_html(r.get('상세 기록', ''))}</td>"
            "</tr>"
        )
    return "\n".join(out)


def main() -> None:
    goal_rows = parse_tables(HYPOTHESIS_TABLE)[0]
    hypothesis_rows = parse_tables(HYPOTHESIS_TABLE)[1]
    result_rows = parse_tables(RESULTS_TABLE)[0]
    metrics = split_metrics()
    latest_h = max((r.get("가설 ID", "") for r in hypothesis_rows), key=lambda x: id_number(x, "T5-H"))
    latest_e = max((r.get("실험 ID", "") for r in result_rows), key=lambda x: id_number(x, "T5-E"))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Track 5 실험 대시보드</title>
  <style>
    :root {{ --bg:#f3efe5; --panel:#fffaf0; --ink:#18221d; --line:#d7ccbb; --green:#2d6a4f; --blue:#284b63; --amber:#b36b22; }}
    body {{ margin:0; color:var(--ink); font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif; background:linear-gradient(135deg,#f7f1e6,#eee1cf); line-height:1.55; }}
    main {{ max-width:1360px; margin:0 auto; padding:32px; }}
    .grid {{ display:grid; grid-template-columns:1.3fr .8fr; gap:20px; }}
    .panel {{ background:rgba(255,250,240,.95); border:1px solid var(--line); border-radius:24px; padding:24px; box-shadow:0 16px 40px rgba(40,32,20,.1); }}
    h1 {{ margin:0 0 16px; font-size:52px; letter-spacing:-.06em; }}
    h2 {{ margin:0 0 14px; }}
    code {{ background:rgba(40,75,99,.1); padding:1px 5px; border-radius:6px; }}
    .pills {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
    .pill {{ padding:7px 10px; background:#efe4d2; border-radius:999px; font-weight:800; font-size:12px; }}
    .cards {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin:20px 0; }}
    .card, article {{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:16px; }}
    .card strong {{ display:block; font-size:22px; }}
    .card span, article p {{ color:#667064; font-size:13px; }}
    .goals {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
    article strong {{ display:inline-block; color:var(--green); margin-bottom:6px; }}
    article h3 {{ margin:0 0 6px; font-size:15px; }}
    .tabs {{ margin-top:20px; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:18px; background:var(--panel); }}
    table {{ width:100%; border-collapse:collapse; min-width:1000px; }}
    th,td {{ padding:12px 14px; border-bottom:1px solid var(--line); vertical-align:top; font-size:13px; }}
    th {{ background:#eadfcd; text-align:left; position:sticky; top:0; }}
    .status {{ display:inline-flex; padding:4px 8px; border-radius:999px; font-weight:800; font-size:12px; }}
    .done {{ background:rgba(45,106,79,.14); color:var(--green); }}
    .hold {{ background:rgba(179,107,34,.14); color:var(--amber); }}
    .partial {{ background:rgba(40,75,99,.14); color:var(--blue); }}
    @media(max-width:900px) {{ .grid,.cards,.goals {{ grid-template-columns:1fr; }} main {{ padding:18px; }} }}
  </style>
</head>
<body>
<main>
  <section class="grid">
    <div class="panel">
      <h1>Track 5 실험 대시보드</h1>
      <ul>
        <li>Track 5는 데이터셋 split을 다시 고정하고 시작</li>
        <li>Warm / Cold는 분리 평가</li>
        <li>validation에서 후보 선택, test에서 최종 확인</li>
        <li>source, URL, gallery tier는 모델 피처 제외</li>
      </ul>
      <div class="pills">
        <span class="pill">가설 {len(hypothesis_rows)}개</span>
        <span class="pill">최신 가설 {html.escape(latest_h)}</span>
        <span class="pill">최신 실험 {html.escape(latest_e)}</span>
        <span class="pill">생성 {date.today().isoformat()}</span>
      </div>
    </div>
    <div class="panel">
      <h2>Split 핵심</h2>
      <ul>
        <li>Warm test: <code>{metrics['test_warm']}</code></li>
        <li>Cold test: <code>{metrics['test_cold']}</code></li>
        <li>Cold/train 작가 겹침: <code>{metrics['cold_overlap']}</code></li>
      </ul>
    </div>
  </section>
  <section class="cards">
    <div class="card"><strong>{metrics['train']}</strong><span>train rows / artists</span></div>
    <div class="card"><strong>{metrics['val_warm']}</strong><span>val_warm rows / artists</span></div>
    <div class="card"><strong>{metrics['test_warm']}</strong><span>test_warm rows / artists</span></div>
    <div class="card"><strong>{metrics['val_cold']}</strong><span>val_cold rows / artists</span></div>
    <div class="card"><strong>{metrics['test_cold']}</strong><span>test_cold rows / artists</span></div>
  </section>
  <section class="panel">
    <h2>세부 목표</h2>
    <div class="goals">{render_goals(goal_rows)}</div>
  </section>
  <section class="tabs">
    <div class="panel">
      <h2>가설 상태</h2>
      <div class="table-wrap"><table><thead><tr><th>가설</th><th>목표</th><th>상태</th><th>요약</th><th>연구 방법</th><th>현재 판단</th></tr></thead><tbody>{render_hypotheses(hypothesis_rows)}</tbody></table></div>
    </div>
    <div class="panel" style="margin-top:20px">
      <h2>실험 결과</h2>
      <div class="table-wrap"><table><thead><tr><th>날짜</th><th>실험</th><th>가설</th><th>상태</th><th>모델</th><th>Warm</th><th>Cold</th><th>결론</th><th>상세</th></tr></thead><tbody>{render_results(result_rows)}</tbody></table></div>
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
