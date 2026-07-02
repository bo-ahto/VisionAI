#!/usr/bin/env python3
"""Render a slide-oriented markdown file to standalone HTML."""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)


def slugify(text: str) -> str:
    slug = re.sub(r"<[^>]+>", "", text)
    slug = re.sub(r"[^\w가-힣.-]+", "-", slug).strip("-").lower()
    return slug or "slide"


def is_table_line(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_align_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


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
            if cell.startswith(":") and cell.endswith(":"):
                alignments.append("center")
            elif cell.endswith(":"):
                alignments.append("right")
            else:
                alignments.append("left")
        body_start = 2
    out = ["<div class=\"table-wrap\"><table><thead><tr>"]
    for idx, cell in enumerate(header):
        align = alignments[idx] if idx < len(alignments) else "left"
        out.append(f"<th class=\"align-{align}\">{inline(cell)}</th>")
    out.append("</tr></thead><tbody>")
    for row in rows[body_start:]:
        out.append("<tr>")
        for idx, cell in enumerate(row):
            align = alignments[idx] if idx < len(alignments) else "left"
            out.append(f"<td class=\"align-{align}\">{inline(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def render_block(markdown: str) -> tuple[str, str]:
    html_lines: list[str] = []
    title = "Slide"
    paragraph: list[str] = []
    list_open = False
    ordered_open = False
    in_code = False
    code_lines: list[str] = []
    table_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            html_lines.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_lists() -> None:
        nonlocal list_open, ordered_open
        if list_open:
            html_lines.append("</ul>")
            list_open = False
        if ordered_open:
            html_lines.append("</ol>")
            ordered_open = False

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            html_lines.append(render_table(table_lines))
            table_lines = []

    for raw in markdown.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            flush_lists()
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
            flush_lists()
            table_lines.append(line)
            continue
        flush_table()
        if not stripped:
            flush_paragraph()
            flush_lists()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_lists()
            level = min(len(heading.group(1)), 3)
            heading_text = heading.group(2).strip()
            if title == "Slide":
                title = re.sub(r"`([^`]+)`", r"\1", heading_text)
            html_lines.append(f"<h{level}>{inline(heading_text)}</h{level}>")
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            flush_lists()
            html_lines.append(f"<blockquote>{inline(stripped[2:].strip())}</blockquote>")
            continue
        bullet = re.match(r"^-\s+(.+)$", stripped)
        if bullet:
            flush_paragraph()
            if ordered_open:
                html_lines.append("</ol>")
                ordered_open = False
            if not list_open:
                html_lines.append("<ul>")
                list_open = True
            html_lines.append(f"<li>{inline(bullet.group(1))}</li>")
            continue
        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            flush_paragraph()
            if list_open:
                html_lines.append("</ul>")
                list_open = False
            if not ordered_open:
                html_lines.append("<ol>")
                ordered_open = True
            html_lines.append(f"<li>{inline(ordered.group(1))}</li>")
            continue
        paragraph.append(stripped)
    flush_paragraph()
    flush_lists()
    flush_table()
    if in_code:
        html_lines.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(html_lines), title


def render_deck(markdown: str, title: str, source: Path, script_link: str | None, report_link: str | None) -> str:
    blocks = [block.strip() for block in re.split(r"^\s*---\s*$", markdown, flags=re.MULTILINE) if block.strip()]
    rendered = [render_block(block) for block in blocks]
    total = len(rendered)
    nav_links = []
    slide_html = []
    for idx, (body, slide_title) in enumerate(rendered, start=1):
        slug = f"slide-{idx}"
        nav_links.append(
            f"<a href=\"#{slug}\"><span>{idx:02d}</span>{html.escape(slide_title)}</a>"
        )
        cls = "slide title-slide" if idx == 1 else "slide"
        slide_html.append(
            f"<section class=\"{cls}\" id=\"{slug}\" data-slide=\"{idx}\">\n"
            f"<div class=\"slide-count\">{idx:02d} / {total:02d}</div>\n"
            f"{body}\n</section>"
        )
    link_html = []
    if script_link:
        link_html.append(f"<a href=\"{html.escape(script_link)}\">발표 스크립트</a>")
    if report_link:
        link_html.append(f"<a href=\"{html.escape(report_link)}\">기준 리포트</a>")
    css = """
:root {
  color-scheme: light;
  --ink: #17202a;
  --muted: #667085;
  --line: #d6dde7;
  --soft: #f7f9fc;
  --head: #eef3f8;
  --accent: #255f85;
  --paper: #ffffff;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Segoe UI", sans-serif;
  color: var(--ink);
  background: #e9eef4;
  line-height: 1.45;
}
.deck-shell { display: grid; grid-template-columns: 300px minmax(0, 1fr); min-height: 100vh; }
nav {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: auto;
  background: #f8fafc;
  border-right: 1px solid var(--line);
  padding: 20px 16px;
}
nav h2 { margin: 0 0 12px; font-size: 15px; }
nav .links { display: grid; gap: 6px; margin: 14px 0 18px; }
nav .links a { color: var(--accent); text-decoration: none; font-size: 13px; }
nav .toc { display: grid; gap: 3px; }
nav .toc a {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 6px;
  align-items: baseline;
  color: #344054;
  text-decoration: none;
  border-radius: 6px;
  padding: 5px 7px;
  font-size: 12px;
}
nav .toc a:hover { background: #eef4ff; color: var(--accent); }
nav .toc span { color: var(--muted); font-variant-numeric: tabular-nums; }
main { padding: 28px 0 60px; }
.slide {
  position: relative;
  width: min(1280px, calc(100vw - 360px));
  min-height: 720px;
  margin: 0 auto 28px;
  padding: 46px 56px 56px;
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: 0 14px 32px rgba(31, 41, 51, .10);
  page-break-after: always;
}
.title-slide {
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: linear-gradient(135deg, #ffffff 0%, #f3f7fb 100%);
}
.slide-count { position: absolute; right: 28px; bottom: 20px; color: var(--muted); font-size: 13px; }
h1 { margin: 0 0 22px; font-size: 42px; line-height: 1.18; letter-spacing: 0; }
h2 { margin: 0 0 24px; font-size: 34px; line-height: 1.2; letter-spacing: 0; }
h3 { margin: 18px 0 10px; font-size: 24px; }
p { margin: 0 0 14px; font-size: 22px; }
ul, ol { margin: 0 0 18px; padding-left: 28px; }
li { margin: 8px 0; font-size: 22px; }
strong { color: #111827; }
code {
  background: #f2f4f7;
  border: 1px solid #e4e7ec;
  border-radius: 4px;
  padding: 1px 5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: .9em;
}
pre {
  margin: 8px 0 20px;
  overflow: auto;
  background: #0f172a;
  color: #e5e7eb;
  border-radius: 8px;
  padding: 18px 20px;
  font-size: 19px;
  white-space: pre-wrap;
}
pre code { background: transparent; border: 0; color: inherit; padding: 0; }
.table-wrap { overflow-x: auto; margin: 8px 0 22px; border: 1px solid var(--line); border-radius: 8px; }
table { width: 100%; min-width: 760px; border-collapse: collapse; font-size: 18px; }
th, td { border-bottom: 1px solid var(--line); border-right: 1px solid var(--line); padding: 10px 12px; vertical-align: top; text-align: left; }
th:last-child, td:last-child { border-right: 0; }
tr:last-child td { border-bottom: 0; }
th { background: var(--head); font-weight: 700; }
tbody tr:nth-child(even) { background: var(--soft); }
.align-right { text-align: right; }
.align-center { text-align: center; }
.align-left { text-align: left; }
blockquote { margin: 10px 0 20px; border-left: 7px solid var(--accent); background: #f2f7fa; padding: 14px 18px; font-size: 22px; font-weight: 650; }
@media (max-width: 1100px) {
  .deck-shell { display: block; }
  nav { position: relative; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }
  main { padding: 18px 0 40px; }
  .slide { width: calc(100vw - 28px); min-height: auto; padding: 34px 24px 48px; }
  h1 { font-size: 32px; }
  h2 { font-size: 27px; }
  p, li { font-size: 18px; }
  table { font-size: 15px; }
  pre { font-size: 15px; }
}
@media print {
  body { background: #fff; }
  nav { display: none; }
  .deck-shell { display: block; }
  main { padding: 0; }
  .slide { width: 100%; min-height: 100vh; margin: 0; border: 0; box-shadow: none; }
}
"""
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{css}</style>
</head>
<body>
  <div class="deck-shell">
    <nav>
      <h2>{html.escape(title)}</h2>
      <div class="links">
        {''.join(link_html)}
      </div>
      <div class="toc">
        {''.join(nav_links)}
      </div>
    </nav>
    <main>
      {''.join(slide_html)}
    </main>
  </div>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--script-link")
    parser.add_argument("--report-link")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.source if args.source.is_absolute() else REPO / args.source
    target = args.target if args.target.is_absolute() else REPO / args.target
    markdown = source.read_text(encoding="utf-8")
    document = render_deck(markdown, args.title, source, args.script_link, args.report_link)
    target.write_text(document, encoding="utf-8")
    print(target.relative_to(REPO))


if __name__ == "__main__":
    main()
