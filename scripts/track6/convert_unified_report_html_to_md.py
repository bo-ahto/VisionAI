#!/usr/bin/env python3
"""partner_warm_cold_official_v0_1_unified_model_report.html → .md 충실 변환.

단독 hand-crafted HTML이라 render 스크립트로 재생성 불가(스타일 상이). 본문(<main>)을
markdown으로 변환해 읽기/유지보수용 md 동반본을 만든다. 다루는 태그: h1~h3, p, ul/li,
table(thead/tbody), div.callout, pre/code, 인라인 strong/em/code/br.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = (
    REPO
    / "docs"
    / "track6"
    / "experiments"
    / "partner_warm_cold_official_v0_1_unified_model_report.html"
)
DST = SRC.with_suffix(".md")


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out: list[str] = []
        self.in_main = False
        self.depth_main = 0
        self.cur = ""  # 현재 인라인 텍스트 버퍼
        self.mode = None  # h1/h2/h3/p/li
        self.in_table = False
        self.table: list[list[str]] = []
        self.row: list[str] | None = None
        self.in_pre = False
        self.callout = None  # 'note' | 'warn'

    # --- helpers ---
    def emit(self, text=""):
        self.out.append(text)

    def flush_block(self, prefix=""):
        text = re.sub(r"[ \t]+", " ", self.cur).strip()
        if text:
            self.emit(prefix + text)
            self.emit("")
        self.cur = ""

    # --- tags ---
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.in_main = True
            return
        if not self.in_main:
            return
        if tag in ("h1", "h2", "h3"):
            self.mode = tag
            self.cur = ""
        elif tag == "p":
            self.mode = "p"
            self.cur = ""
        elif tag == "li":
            self.mode = "li"
            self.cur = ""
        elif tag == "ul":
            pass
        elif tag == "table":
            self.in_table = True
            self.table = []
        elif tag == "tr":
            self.row = []
        elif tag in ("th", "td"):
            self.cur = ""
        elif tag == "pre":
            self.in_pre = True
            self.cur = ""
        elif tag == "div" and "callout" in a.get("class", ""):
            self.callout = "warn" if "warn" in a["class"] else "note"
            self.cur = ""  # callout 직접 텍스트 캡처 시작
        elif tag in ("strong", "b"):
            self.cur += "**"
        elif tag in ("em", "i"):
            self.cur += "*"
        elif tag == "code" and not self.in_pre:
            self.cur += "`"
        elif tag == "br":
            self.cur += "<br>"

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False
            return
        if not self.in_main:
            return
        if tag in ("h1", "h2", "h3"):
            level = {"h1": "# ", "h2": "## ", "h3": "### "}[tag]
            self.flush_block(level)
            self.mode = None
        elif tag == "p":
            prefix = ""
            if self.callout:
                prefix = "> "
            self.flush_block(prefix)
            self.mode = None
        elif tag == "li":
            text = re.sub(r"[ \t]+", " ", self.cur).strip()
            if text:
                self.emit("- " + text)
            self.cur = ""
            self.mode = None
        elif tag == "ul":
            self.emit("")
        elif tag in ("th", "td"):
            if self.row is not None:
                self.row.append(re.sub(r"[ \t]+", " ", self.cur).strip())
            self.cur = ""
        elif tag == "tr":
            if self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == "table":
            self._emit_table()
            self.in_table = False
        elif tag == "pre":
            self.emit("```text")
            self.emit(self.cur.strip("\n"))
            self.emit("```")
            self.emit("")
            self.in_pre = False
            self.cur = ""
        elif tag == "div" and self.callout:
            text = re.sub(r"[ \t]+", " ", self.cur).strip()
            if text:
                self.emit("> " + text)
                self.emit("")
            self.cur = ""
            self.callout = None
        elif tag in ("strong", "b"):
            self.cur += "**"
        elif tag in ("em", "i"):
            self.cur += "*"
        elif tag == "code" and not self.in_pre:
            self.cur += "`"

    def handle_data(self, data):
        if not self.in_main:
            return
        if self.in_pre or self.mode or self.in_table or self.callout:
            self.cur += data

    def _emit_table(self):
        if not self.table:
            return
        head, *body = self.table
        self.emit("| " + " | ".join(head) + " |")
        self.emit("|" + "|".join(["---"] * len(head)) + "|")
        for r in body:
            r = (r + [""] * len(head))[: len(head)]
            self.emit("| " + " | ".join(r) + " |")
        self.emit("")


def main():
    html = SRC.read_text(encoding="utf-8")
    p = ReportParser()
    p.feed(html)
    md = "\n".join(p.out)
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    DST.write_text(md, encoding="utf-8")
    print(f"wrote {DST.relative_to(REPO)} ({len(md.splitlines())} lines)")


if __name__ == "__main__":
    main()
