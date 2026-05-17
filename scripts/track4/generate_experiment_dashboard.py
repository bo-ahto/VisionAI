#!/usr/bin/env python3
"""Generate the Track 4 experiment dashboard from Markdown source tables."""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
HYPOTHESIS_TABLE = DOCS / "track4_hypothesis_table.md"
RESULTS_TABLE = DOCS / "track4_experiment_results_table.md"
QUALITY_REVIEW = DOCS / "track4_dataset_final_quality_review_2026-05-17.md"
OUT_PATH = DOCS / "track4_experiment_dashboard.html"


def split_md_row(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def parse_tables(path: Path) -> list[list[dict[str, str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    tables: list[list[dict[str, str]]] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.startswith("|") or idx + 1 >= len(lines) or not re.match(r"^\|\s*-", lines[idx + 1]):
            idx += 1
            continue
        headers = split_md_row(line)
        rows: list[dict[str, str]] = []
        idx += 2
        while idx < len(lines) and lines[idx].startswith("|"):
            cells = split_md_row(lines[idx])
            if len(cells) >= len(headers):
                rows.append(dict(zip(headers, cells)))
            idx += 1
        tables.append(rows)
    return tables


def parse_first_table(path: Path) -> list[dict[str, str]]:
    tables = parse_tables(path)
    if not tables:
        raise ValueError(f"Markdown table not found: {path}")
    return tables[0]


def parse_second_table(path: Path) -> list[dict[str, str]]:
    tables = parse_tables(path)
    if len(tables) < 2:
        raise ValueError(f"Second Markdown table not found: {path}")
    return tables[1]


def relative_doc_link(target: str) -> str:
    target = target.strip()
    target = target.replace("/Users/bo/VisionAI/docs/", "")
    if target.startswith("docs/"):
        target = target.removeprefix("docs/")
    target = re.sub(r":\d+$", "", target)
    return target


def inline_md_to_html(text: str) -> str:
    links: list[tuple[str, str]] = []

    def store_link(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        href = html.escape(relative_doc_link(match.group(2)))
        links.append((label, href))
        return f"@@LINK{len(links) - 1}@@"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", store_link, text)
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    for idx, (label, href) in enumerate(links):
        escaped = escaped.replace(f"@@LINK{idx}@@", f'<a href="{href}">{label}</a>')
    return escaped


def status_class(status: str) -> str:
    if "완료" in status:
        return "done"
    if "부분" in status or "진행" in status:
        return "partial"
    if "보류" in status or "예정" in status:
        return "hold"
    if "중단" in status:
        return "stop"
    return "neutral"


def md_value(label: str, text: str, default: str = "-") -> str:
    pattern = re.compile(rf"^- {re.escape(label)}:\s*`?([^`\n]+)`?", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else default


def dataset_metrics() -> dict[str, str]:
    text = QUALITY_REVIEW.read_text(encoding="utf-8") if QUALITY_REVIEW.exists() else ""
    return {
        "training_rows": md_value("학습 후보 rows", text),
        "train_rows": md_value("train rows", text),
        "val_warm": md_value("val_warm rows", text),
        "val_cold": md_value("val_cold rows", text),
        "test_warm": md_value("test_warm rows", text),
        "test_cold": md_value("test_cold rows", text),
        "cold_overlap": md_value("test_cold 작가 train 겹침 수", text),
        "cold_leak": md_value("test_cold `artist_works_log > 0` rows", text),
        "aspect_extreme": md_value("aspect_ratio > 10 rows", text),
        "size_extreme": md_value("width_cm > 1000 또는 height_cm > 1000 rows", text),
    }


def summarize_status(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("현재 상태") or row.get("상태") or ""
        counts[status] = counts.get(status, 0) + 1
    return counts


def h_sort_key(row: dict[str, str]) -> int:
    match = re.search(r"T4-H(\d+)", row.get("가설 ID", ""))
    return int(match.group(1)) if match else -1


def e_sort_key(row: dict[str, str]) -> tuple[str, int]:
    match = re.search(r"T4-E(\d+)", row.get("실험 ID", ""))
    return (row.get("날짜", ""), int(match.group(1)) if match else -1)


def id_number(value: str, prefix: str) -> int:
    match = re.search(rf"{re.escape(prefix)}(\d+)", value)
    return int(match.group(1)) if match else -1


def render_goal_cards(goals: list[dict[str, str]]) -> str:
    cards = []
    for row in goals:
        cards.append(
            '<article class="goal-card">'
            f'<span>{inline_md_to_html(row["목표 ID"])}</span>'
            f'<h3>{inline_md_to_html(row["세부 목표"])}</h3>'
            f'<p>{inline_md_to_html(row["설명"])}</p>'
            "</article>"
        )
    return "\n".join(cards)


def render_hypothesis_rows(rows: list[dict[str, str]]) -> str:
    rendered = []
    for row in sorted(rows, key=h_sort_key, reverse=True):
        status = row.get("현재 상태", "")
        rendered.append(
            "<tr>"
            f"<td>{inline_md_to_html(row.get('가설 ID', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('세부 목표', ''))}</td>"
            f'<td><span class="status {status_class(status)}">{html.escape(status)}</span></td>'
            f"<td>{inline_md_to_html(row.get('가설 요약', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('연구 방법', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('성공 기준', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('현재 판단', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('후속 필요', ''))}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def render_result_rows(rows: list[dict[str, str]]) -> str:
    rendered = []
    for row in sorted(rows, key=e_sort_key, reverse=True):
        status = row.get("상태", "")
        rendered.append(
            "<tr>"
            f"<td>{inline_md_to_html(row.get('날짜', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('실험 ID', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('관련 가설', ''))}</td>"
            f'<td><span class="status {status_class(status)}">{html.escape(status)}</span></td>'
            f"<td>{inline_md_to_html(row.get('사용 모델', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('사용 피처', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('Warm 결과 요약', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('Cold 결과 요약', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('결론', ''))}</td>"
            f"<td>{inline_md_to_html(row.get('상세 기록', ''))}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def dashboard_html(goals: list[dict[str, str]], hypotheses: list[dict[str, str]], results: list[dict[str, str]]) -> str:
    metrics = dataset_metrics()
    counts = summarize_status(hypotheses)
    result_counts = summarize_status(results)
    latest_h = max((row.get("가설 ID", "") for row in hypotheses), key=lambda x: id_number(x, "T4-H"))
    latest_e = max((row.get("실험 ID", "") for row in results), key=lambda x: id_number(x, "T4-E"))
    today = date.today().isoformat()
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Track 4 실험 대시보드</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --panel: #fffaf0;
      --ink: #17201b;
      --muted: #687167;
      --line: #d8cfbf;
      --green: #276a4b;
      --blue: #295879;
      --amber: #b2671b;
      --red: #9b382f;
      --chip: #eee3d2;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Arita Dotum", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
      background:
        radial-gradient(circle at 8% 8%, rgba(39, 106, 75, .16), transparent 30rem),
        radial-gradient(circle at 90% 12%, rgba(41, 88, 121, .14), transparent 28rem),
        linear-gradient(135deg, #f8f2e8 0%, #eee3d1 54%, #faf7ef 100%);
      line-height: 1.55;
    }}
    a {{ color: var(--blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    code {{ background: rgba(41, 88, 121, .08); padding: 1px 5px; border-radius: 6px; }}
    .page {{ max-width: 1480px; margin: 0 auto; padding: 34px; }}
    .hero {{ display: grid; grid-template-columns: 1.4fr .8fr; gap: 22px; margin-bottom: 22px; }}
    .panel {{ background: rgba(255,250,240,.92); border: 1px solid var(--line); border-radius: 26px; padding: 26px; box-shadow: 0 18px 45px rgba(44,35,22,.12); }}
    h1 {{ margin: 0 0 16px; font-size: clamp(34px, 4vw, 58px); letter-spacing: -.06em; line-height: 1.05; }}
    h2 {{ margin: 0 0 14px; font-size: 24px; letter-spacing: -.04em; }}
    h3 {{ margin: 0 0 8px; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 5px 0; }}
    .pills {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }}
    .pill {{ padding: 7px 10px; background: var(--chip); border-radius: 999px; font-size: 12px; font-weight: 700; }}
    .pill.green {{ background: rgba(39,106,75,.13); color: var(--green); }}
    .pill.amber {{ background: rgba(178,103,27,.14); color: var(--amber); }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .metric {{ padding: 17px; border: 1px solid #ded1bf; border-radius: 18px; background: #f0e5d4; }}
    .metric small {{ display:block; color: var(--muted); font-weight: 700; margin-bottom: 4px; }}
    .metric strong {{ display:block; font-size: 30px; letter-spacing: -.04em; }}
    .brief-grid {{ display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 22px 0; }}
    .brief {{ background: var(--panel); border:1px solid var(--line); border-radius:20px; padding:18px; }}
    .brief strong {{ display:block; font-size:22px; }}
    .brief span {{ color: var(--muted); font-size:13px; }}
    .goal-grid {{ display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:12px; }}
    .goal-card {{ background: var(--panel); border:1px solid var(--line); border-radius:18px; padding:16px; }}
    .goal-card span {{ display:inline-block; padding:4px 8px; border-radius:999px; background:rgba(39,106,75,.12); color:var(--green); font-weight:800; font-size:12px; margin-bottom:8px; }}
    .goal-card h3 {{ font-size:15px; letter-spacing:-.03em; }}
    .goal-card p {{ margin:0; color:#465047; font-size:13px; }}
    .tabs {{ margin-top: 24px; }}
    .tab-buttons {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }}
    .tab-buttons button {{ border:1px solid var(--line); background:var(--panel); color:var(--ink); padding:10px 14px; border-radius:999px; cursor:pointer; font-weight:800; }}
    .tab-buttons button.active {{ background:var(--green); color:white; border-color:var(--green); }}
    .tab-panel {{ display:none; }}
    .tab-panel.active {{ display:block; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:20px; background:rgba(255,250,240,.9); }}
    table {{ width:100%; border-collapse:collapse; min-width:1100px; }}
    th, td {{ padding:12px 14px; border-bottom:1px solid var(--line); vertical-align:top; font-size:13px; }}
    th {{ position:sticky; top:0; background:#eee2cf; text-align:left; z-index:1; }}
    tr:nth-child(even) td {{ background:rgba(238,227,210,.28); }}
    .status {{ display:inline-flex; padding:4px 8px; border-radius:999px; font-weight:800; font-size:12px; white-space:nowrap; }}
    .status.done {{ background:rgba(39,106,75,.14); color:var(--green); }}
    .status.partial {{ background:rgba(178,103,27,.15); color:var(--amber); }}
    .status.hold {{ background:rgba(104,113,103,.14); color:#596158; }}
    .status.stop {{ background:rgba(155,56,47,.14); color:var(--red); }}
    .pager {{ display:flex; justify-content:flex-end; align-items:center; gap:8px; margin-top:10px; }}
    .pager button {{ border:1px solid var(--line); background:var(--panel); border-radius:10px; padding:7px 10px; cursor:pointer; }}
    footer {{ color:var(--muted); font-size:12px; margin-top:22px; }}
    @media (max-width: 980px) {{
      .hero, .brief-grid, .goal-grid {{ grid-template-columns: 1fr; }}
      .page {{ padding: 18px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="panel">
        <h1>Track 4 실험 대시보드</h1>
        <ul>
          <li>실험 순서: 데이터 검증 → 가설 등록 → 실험 방법 → 실행 → 검증 → 결론</li>
          <li>Warm / Cold는 합치지 않고 분리 판단</li>
          <li>HTML은 Markdown 기준 문서를 읽어 자동 생성</li>
          <li>source, URL, gallery tier는 모델 피처에서 제외</li>
        </ul>
        <div class="pills">
          <span class="pill green">가설 {len(hypotheses)}개</span>
          <span class="pill">최신 가설 {html.escape(latest_h)}</span>
          <span class="pill">최신 실험 {html.escape(latest_e)}</span>
          <span class="pill amber">생성 {today}</span>
        </div>
      </div>
      <div class="panel">
        <h2>데이터셋 핵심 지표</h2>
        <div class="metric-grid">
          <div class="metric"><small>학습 후보</small><strong>{metrics['training_rows']}</strong></div>
          <div class="metric"><small>train rows</small><strong>{metrics['train_rows']}</strong></div>
          <div class="metric"><small>Cold/train 겹침</small><strong>{metrics['cold_overlap']}</strong></div>
          <div class="metric"><small>Cold 이력 누수</small><strong>{metrics['cold_leak']}</strong></div>
        </div>
      </div>
    </section>

    <section class="brief-grid">
      <div class="brief"><strong>{metrics['val_warm']} / {metrics['test_warm']}</strong><span>Warm val / test rows</span></div>
      <div class="brief"><strong>{metrics['val_cold']} / {metrics['test_cold']}</strong><span>Cold val / test rows</span></div>
      <div class="brief"><strong>{metrics['aspect_extreme']}</strong><span>학습 후보 aspect_ratio &gt; 10</span></div>
      <div class="brief"><strong>{metrics['size_extreme']}</strong><span>학습 후보 width/height &gt; 1000cm</span></div>
    </section>

    <section class="panel">
      <h2>세부 목표</h2>
      <div class="goal-grid">
        {render_goal_cards(goals)}
      </div>
    </section>

    <section class="tabs">
      <div class="tab-buttons">
        <button class="active" data-tab="hypotheses">가설 상태</button>
        <button data-tab="results">실험 결과</button>
        <button data-tab="process">진행 기준</button>
      </div>
      <div class="tab-panel active" id="hypotheses">
        <div class="table-wrap">
          <table data-page-size="8">
            <thead><tr><th>가설 ID</th><th>목표</th><th>상태</th><th>가설</th><th>연구 방법</th><th>성공 기준</th><th>현재 판단</th><th>후속 필요</th></tr></thead>
            <tbody>{render_hypothesis_rows(hypotheses)}</tbody>
          </table>
        </div>
        <div class="pager"></div>
      </div>
      <div class="tab-panel" id="results">
        <div class="table-wrap">
          <table data-page-size="8">
            <thead><tr><th>날짜</th><th>실험 ID</th><th>가설</th><th>상태</th><th>모델</th><th>피처</th><th>Warm</th><th>Cold</th><th>결론</th><th>상세</th></tr></thead>
            <tbody>{render_result_rows(results)}</tbody>
          </table>
        </div>
        <div class="pager"></div>
      </div>
      <div class="tab-panel" id="process">
        <div class="panel">
          <h2>실험 진행 기준</h2>
          <ul>
            <li>가설표에 먼저 등록한 뒤 실험을 실행</li>
            <li>validation에서 후보를 고르고 test는 최종 확인에만 사용</li>
            <li>Warm은 작가 정보 사용 가능, Cold는 작가 정보 제외</li>
            <li>모든 실험은 사용 데이터, 피처, 모델, 비교 기준, 결론을 개별 기록에 남김</li>
            <li>대시보드 갱신 명령: <code>python3 scripts/track4/generate_experiment_dashboard.py</code></li>
          </ul>
        </div>
      </div>
    </section>
    <footer>
      Source: <code>track4_hypothesis_table.md</code>, <code>track4_experiment_results_table.md</code>, <code>track4_dataset_final_quality_review_2026-05-17.md</code>
    </footer>
  </main>
  <script>
    document.querySelectorAll('.tab-buttons button').forEach((button) => {{
      button.addEventListener('click', () => {{
        document.querySelectorAll('.tab-buttons button').forEach((b) => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));
        button.classList.add('active');
        document.getElementById(button.dataset.tab).classList.add('active');
      }});
    }});
    document.querySelectorAll('table[data-page-size]').forEach((table) => {{
      const rows = Array.from(table.querySelectorAll('tbody tr'));
      const pageSize = Number(table.dataset.pageSize || 8);
      const pager = table.closest('.tab-panel').querySelector('.pager');
      let page = 0;
      function render() {{
        rows.forEach((row, idx) => {{
          row.style.display = idx >= page * pageSize && idx < (page + 1) * pageSize ? '' : 'none';
        }});
        const pages = Math.max(1, Math.ceil(rows.length / pageSize));
        pager.innerHTML = `<button ${{page === 0 ? 'disabled' : ''}} data-prev>이전</button><span>${{page + 1}} / ${{pages}}</span><button ${{page >= pages - 1 ? 'disabled' : ''}} data-next>다음</button>`;
        pager.querySelector('[data-prev]')?.addEventListener('click', () => {{ page = Math.max(0, page - 1); render(); }});
        pager.querySelector('[data-next]')?.addEventListener('click', () => {{ page = Math.min(pages - 1, page + 1); render(); }});
      }}
      render();
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    goals = parse_first_table(HYPOTHESIS_TABLE)
    hypotheses = parse_second_table(HYPOTHESIS_TABLE)
    results = parse_first_table(RESULTS_TABLE)
    OUT_PATH.write_text(dashboard_html(goals, hypotheses, results), encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
