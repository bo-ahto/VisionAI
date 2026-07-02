#!/usr/bin/env python3
"""Render the Track6 price prediction report markdown to a standalone HTML file."""
from __future__ import annotations

import html
import re
import argparse
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO / "docs" / "track6" / "experiments" / "price_prediction_accuracy_experiment_result_report.md"
DEFAULT_TARGET = REPO / "docs" / "track6" / "experiments" / "price_prediction_accuracy_experiment_result_report.html"


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)


def slugify(text: str) -> str:
    slug = re.sub(r"<[^>]+>", "", text)
    slug = re.sub(r"[^\w가-힣.-]+", "-", slug).strip("-").lower()
    return slug or "section"


def is_table_line(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def is_align_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_table(lines: list[str]) -> str:
    rows = [split_table_row(line) for line in lines]
    if not rows:
        return ""
    header = rows[0]
    alignments = ["left"] * len(header)
    body_start = 1
    if len(rows) > 1 and is_align_row(rows[1]):
        alignments = []
        for cell in rows[1]:
            cell = cell.strip()
            if cell.startswith(":") and cell.endswith(":"):
                alignments.append("center")
            elif cell.endswith(":"):
                alignments.append("right")
            else:
                alignments.append("left")
        body_start = 2

    out = ["<div class=\"table-wrap\"><table>"]
    out.append("<thead><tr>")
    for idx, cell in enumerate(header):
        align = alignments[idx] if idx < len(alignments) else "left"
        out.append(f"<th class=\"align-{align}\">{inline(cell)}</th>")
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in rows[body_start:]:
        out.append("<tr>")
        for idx, cell in enumerate(row):
            align = alignments[idx] if idx < len(alignments) else "left"
            out.append(f"<td class=\"align-{align}\">{inline(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def render_markdown(markdown: str) -> tuple[str, list[tuple[int, str, str]]]:
    html_lines: list[str] = []
    toc: list[tuple[int, str, str]] = []
    paragraph: list[str] = []
    list_open = False
    in_code = False
    code_lines: list[str] = []
    table_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            html_lines.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_open
        if list_open:
            html_lines.append("</ul>")
            list_open = False

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            html_lines.append(render_table(table_lines))
            table_lines = []

    for raw in markdown.splitlines():
        line = raw.rstrip()

        if line.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_table()
            if in_code:
                html_lines.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if is_table_line(line):
            flush_paragraph()
            flush_list()
            table_lines.append(line)
            continue
        flush_table()

        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            flush_list()
            html_lines.append(f"<blockquote>{inline(stripped[2:].strip())}</blockquote>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            title_html = inline(title)
            slug = slugify(title)
            toc.append((level, title, slug))
            html_lines.append(f"<h{level} id=\"{slug}\">{title_html}</h{level}>")
            continue

        bullet = re.match(r"^-\s+(.+)$", stripped)
        if bullet:
            flush_paragraph()
            if not list_open:
                html_lines.append("<ul>")
                list_open = True
            html_lines.append(f"<li>{inline(bullet.group(1))}</li>")
            continue

        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    flush_table()
    if in_code:
        html_lines.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(html_lines), toc


def render_toc(toc: list[tuple[int, str, str]]) -> str:
    items = []
    for level, title, slug in toc:
        if level > 3:
            continue
        cls = f"toc-level-{level}"
        items.append(f"<a class=\"{cls}\" href=\"#{slug}\">{html.escape(title)}</a>")
    return "\n".join(items)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--title", default="Track6 가격 예측 정확도 실험 결과 종합 보고서")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.source if args.source.is_absolute() else REPO / args.source
    target = args.target if args.target.is_absolute() else REPO / args.target
    markdown = source.read_text(encoding="utf-8")
    body, toc = render_markdown(markdown)
    title = args.title
    css = """
:root {
  color-scheme: light;
  --text: #1f2933;
  --muted: #667085;
  --line: #d8dee4;
  --head: #eef2f7;
  --soft: #f8fafc;
  --accent: #1d4ed8;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Segoe UI", sans-serif;
  color: var(--text);
  background: white;
  line-height: 1.62;
}
.layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  min-height: 100vh;
}
aside {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: auto;
  border-right: 1px solid var(--line);
  background: #fbfdff;
  padding: 24px 20px;
}
aside h2 {
  margin: 0 0 14px;
  font-size: 15px;
}
.toc a {
  display: block;
  color: #344054;
  text-decoration: none;
  border-radius: 6px;
  padding: 5px 8px;
  font-size: 13px;
}
.toc a:hover { background: #eef4ff; color: var(--accent); }
.toc-level-1 { font-weight: 700; margin-top: 8px; }
.toc-level-2 { margin-left: 8px; }
.toc-level-3 { margin-left: 18px; color: var(--muted); }
main {
  max-width: 1180px;
  width: 100%;
  padding: 36px 44px 72px;
}
h1 {
  margin: 0 0 22px;
  font-size: 30px;
  line-height: 1.25;
  letter-spacing: 0;
}
h2 {
  margin: 42px 0 14px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
  font-size: 23px;
}
h3 {
  margin: 28px 0 12px;
  font-size: 18px;
}
h4, h5, h6 { margin: 24px 0 10px; }
p { margin: 10px 0 16px; }
ul { margin: 8px 0 18px; padding-left: 22px; }
li { margin: 5px 0; }
code {
  background: #f2f4f7;
  border: 1px solid #eaecf0;
  border-radius: 4px;
  padding: 1px 5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.92em;
}
pre {
  overflow: auto;
  background: #0f172a;
  color: #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  font-size: 13px;
}
pre code {
  background: transparent;
  border: 0;
  color: inherit;
  padding: 0;
}
.table-wrap {
  overflow-x: auto;
  margin: 14px 0 28px;
  border: 1px solid var(--line);
  border-radius: 8px;
}
table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
  font-size: 13px;
}
th, td {
  border-bottom: 1px solid var(--line);
  border-right: 1px solid var(--line);
  padding: 9px 10px;
  vertical-align: top;
}
th:last-child, td:last-child { border-right: 0; }
tr:last-child td { border-bottom: 0; }
th {
  background: var(--head);
  font-weight: 700;
}
tbody tr:nth-child(even) { background: var(--soft); }
.align-right { text-align: right; }
.align-center { text-align: center; }
.align-left { text-align: left; }
.meta {
  margin: 0 0 26px;
  color: var(--muted);
  font-size: 14px;
}
@media (max-width: 920px) {
  .layout { display: block; }
  aside { position: relative; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }
  main { padding: 28px 18px 56px; }
  h1 { font-size: 25px; }
}
@media print {
  aside { display: none; }
  .layout { display: block; }
  main { max-width: none; padding: 0; }
  .table-wrap { overflow: visible; }
  table { min-width: 0; font-size: 11px; }
}
"""
    document = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{css}</style>
</head>
<body>
  <div class="layout">
    <aside>
      <h2>목차</h2>
      <nav class="toc">
        {render_toc(toc)}
      </nav>
    </aside>
    <main>
      <div class="meta">Generated from <code>{html.escape(str(source.relative_to(REPO)))}</code></div>
      {body}
    </main>
  </div>
</body>
</html>
"""
    target.write_text(document, encoding="utf-8")
    print(target.relative_to(REPO))


if __name__ == "__main__":
    main()
