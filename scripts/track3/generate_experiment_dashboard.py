"""Generate the Track 3 experiment dashboard from Markdown source tables."""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent.parent
DOCS = REPO / "docs"
HYPOTHESIS_TABLE = DOCS / "track3_hypothesis_table.md"
EXPERIMENT_TABLE = DOCS / "track3_experiment_results_table.md"
OUT_PATH = DOCS / "track3_experiment_dashboard.html"


def split_md_row(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def parse_first_table(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        if idx + 1 >= len(lines) or not re.match(r"^\|\s*-", lines[idx + 1]):
            continue
        headers = split_md_row(line)
        rows: list[dict[str, str]] = []
        for data_line in lines[idx + 2 :]:
            if not data_line.startswith("|"):
                break
            cells = split_md_row(data_line)
            if len(cells) < len(headers):
                continue
            rows.append(dict(zip(headers, cells)))
        return rows
    raise ValueError(f"Markdown table not found: {path}")


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
    if "보류" in status or "예정" in status or "부분" in status:
        return "hold"
    if "중단" in status:
        return "stop"
    return "done"


def render_hypothesis_rows(rows: list[dict[str, str]]) -> str:
    rendered = []
    for row in rows:
        status = row["현재 상태"]
        rendered.append(
            "              <tr>"
            f"<td>{inline_md_to_html(row['가설 ID'])}</td>"
            f"<td>{inline_md_to_html(row.get('세부 목표', ''))}</td>"
            f'<td><span class="status {status_class(status)}">{html.escape(status)}</span></td>'
            f"<td>{inline_md_to_html(row.get('검증 강도', ''))}</td>"
            f"<td>{inline_md_to_html(row['가설 요약'])}</td>"
            f"<td>{inline_md_to_html(row['관련 실험'])}</td>"
            f"<td>{inline_md_to_html(row['현재 판단'])}</td>"
            f"<td>{inline_md_to_html(row['후속 필요'])}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def render_experiment_rows(rows: list[dict[str, str]]) -> str:
    rendered = []
    for row in rows:
        status = row["상태"]
        experiment_id = row["실험 ID"].strip("`")
        rendered.append(
            "              <tr>"
            f"<td>{inline_md_to_html(row['날짜'])}</td>"
            f"<td>{inline_md_to_html(experiment_id)}</td>"
            f"<td>{inline_md_to_html(row['관련 가설'])}</td>"
            f'<td><span class="status {status_class(status)}">{html.escape(status)}</span></td>'
            f"<td>{inline_md_to_html(row['Warm 결과 요약'])}</td>"
            f"<td>{inline_md_to_html(row['Cold 결과 요약'])}</td>"
            f"<td>{inline_md_to_html(row['결론'])}</td>"
            f"<td>{inline_md_to_html(row['상세 기록'])}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def summarize_status(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row["현재 상태"]
        counts[status] = counts.get(status, 0) + 1
    return counts


def latest_h_id(rows: list[dict[str, str]]) -> str:
    ids = [row["가설 ID"] for row in rows if re.fullmatch(r"H\d+", row["가설 ID"])]
    return max(ids, key=lambda value: int(value[1:]))


def hypothesis_sort_key(row: dict[str, str]) -> int:
    match = re.fullmatch(r"H(\d+)", row["가설 ID"].strip())
    return int(match.group(1)) if match else -1


def experiment_sort_key(row: dict[str, str]) -> tuple[str, int]:
    experiment_id = row["실험 ID"].strip().strip("`")
    h_numbers = [int(value) for value in re.findall(r"H(\d+)", experiment_id)]
    if not h_numbers:
        h_numbers = [int(value) for value in re.findall(r"H(\d+)", row.get("관련 가설", ""))]
    return (row["날짜"], max(h_numbers, default=-1))


GOALS = [
    ("G1", "기본 예측 가능성 확인", "작품 구조 정보만으로 가격 예측 baseline이 성립하는지 확인"),
    ("G2", "Warm 성능 개선", "이미 학습 데이터에 등장한 작가의 새 작품 가격을 더 잘 예측"),
    ("G3", "Cold 성능 개선", "처음 보는 작가의 작품 가격을 더 안정적으로 예측"),
    ("G4", "운영 가능 피처 선정", "실제 서비스 입력에서 다시 만들 수 있는 변수만 남김"),
    ("G5", "약점 구간 보완", "2D/3D, 대형 작품, 특정 재료 등 오차가 큰 구간 개선"),
    ("G6", "모델 안정성 확인", "반복 학습, split 차이, 기준 변경에도 성능이 유지되는지 확인"),
    ("G7", "결측/정보량/신뢰도 대응", "정보 부족 상황, 예측 범위, 신뢰도 표시 가능성 확인"),
    ("G8", "최종 후보 정책 결정", "Warm / Cold / Cold 3D 모델을 어떻게 나눠 쓸지 결정"),
]


def render_goal_cards() -> str:
    cards = []
    for goal_id, title, desc in GOALS:
        cards.append(
            "          <div class=\"goal-card\">"
            f"<div class=\"goal-id\">{goal_id}</div>"
            f"<h3>{html.escape(title)}</h3>"
            f"<p>{html.escape(desc)}</p>"
            "</div>"
        )
    return "\n".join(cards)


def dashboard_html(hypothesis_rows: list[dict[str, str]], experiment_rows: list[dict[str, str]]) -> str:
    counts = summarize_status(hypothesis_rows)
    done = counts.get("검증 완료", 0)
    hold = counts.get("보류", 0)
    latest = latest_h_id(hypothesis_rows)
    today = date.today().isoformat()
    hypothesis_body = render_hypothesis_rows(hypothesis_rows)
    experiment_body = render_experiment_rows(experiment_rows)
    goal_cards = render_goal_cards()
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Track 3 실험 대시보드</title>
  <style>
    :root {{
      --bg: #f6f2ea;
      --panel: #fffaf1;
      --ink: #1f2a24;
      --muted: #6f756d;
      --line: #d8cfc0;
      --green: #2f6f4e;
      --amber: #b36b18;
      --red: #9d3b30;
      --blue: #274f76;
      --chip: #ede3d2;
      --shadow: 0 18px 45px rgba(44, 35, 22, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(47, 111, 78, 0.16), transparent 34rem),
        linear-gradient(135deg, #f7f1e7 0%, #efe6d6 45%, #f8f5ee 100%);
      color: var(--ink);
      font-family: "Arita Dotum", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
      line-height: 1.55;
    }}
    a {{ color: var(--blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .page {{ display: grid; grid-template-columns: 260px minmax(0, 1fr); min-height: 100vh; }}
    aside {{
      position: sticky; top: 0; height: 100vh; padding: 28px 20px;
      border-right: 1px solid var(--line);
      background: rgba(255, 250, 241, 0.84);
      backdrop-filter: blur(14px);
    }}
    .brand {{ font-size: 22px; font-weight: 800; letter-spacing: -0.04em; margin-bottom: 8px; }}
    .sub {{ color: var(--muted); font-size: 13px; margin-bottom: 24px; }}
    nav a {{ display: block; padding: 10px 12px; border-radius: 12px; color: var(--ink); font-size: 14px; margin-bottom: 4px; }}
    nav a:hover {{ background: var(--chip); text-decoration: none; }}
    main {{ padding: 40px; max-width: 1440px; }}
    .hero {{ display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr); gap: 24px; align-items: stretch; margin-bottom: 24px; }}
    .panel {{ background: rgba(255, 250, 241, 0.9); border: 1px solid var(--line); border-radius: 24px; box-shadow: var(--shadow); padding: 26px; }}
    h1 {{ font-size: clamp(32px, 4vw, 56px); line-height: 1.05; letter-spacing: -0.06em; margin: 0 0 18px; }}
    h2 {{ font-size: 24px; letter-spacing: -0.04em; margin: 0 0 16px; }}
    h3 {{ font-size: 17px; margin: 0 0 10px; }}
    code {{ background: rgba(39, 79, 118, 0.08); border-radius: 6px; padding: 1px 5px; }}
    section {{ margin: 24px 0; }}
    .summary-list, .card ul, .event ul, .cell-list {{ margin: 0; padding-left: 18px; }}
    .summary-list li, .card li, .event li, .cell-list li {{ margin: 5px 0; }}
    .cell-list {{ font-size: 13px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 20px; }}
    .pill {{
      display: inline-flex; align-items: center; gap: 6px; padding: 7px 10px;
      border-radius: 999px; background: var(--chip); color: #3b3f38;
      font-size: 12px; font-weight: 700; white-space: nowrap;
    }}
    .pill.green {{ background: rgba(47, 111, 78, 0.13); color: var(--green); }}
    .pill.amber {{ background: rgba(179, 107, 24, 0.14); color: var(--amber); }}
    .pill.red {{ background: rgba(157, 59, 48, 0.12); color: var(--red); }}
    .score-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .score {{ padding: 18px; border-radius: 18px; background: #f1e7d7; border: 1px solid #ded1bf; }}
    .score small {{ display: block; color: var(--muted); font-weight: 700; margin-bottom: 6px; }}
    .score strong {{ display: block; font-size: 34px; letter-spacing: -0.05em; }}
    .score span {{ display: block; color: var(--muted); font-size: 12px; margin-top: 4px; }}
    .brief-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 24px; }}
    .brief {{
      background: rgba(255, 250, 241, 0.9);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 18px;
      box-shadow: 0 10px 28px rgba(44, 35, 22, 0.08);
    }}
    .brief h3 {{ font-size: 15px; margin: 0 0 8px; }}
    .brief p {{ margin: 0; color: #465047; font-size: 13px; }}
    .brief strong {{ display: block; margin-bottom: 4px; font-size: 20px; letter-spacing: -0.04em; }}
    .brief.green {{ border-top: 5px solid var(--green); }}
    .brief.blue {{ border-top: 5px solid var(--blue); }}
    .brief.amber {{ border-top: 5px solid var(--amber); }}
    .brief.red {{ border-top: 5px solid var(--red); }}
    .cards {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 20px; padding: 20px; }}
    .card p, .card li {{ margin: 0; color: #465047; font-size: 14px; }}
    .goal-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .goal-card {{
      background: #f1e7d7;
      border: 1px solid #ded1bf;
      border-radius: 18px;
      padding: 16px;
      min-height: 145px;
    }}
    .goal-id {{
      display: inline-flex;
      padding: 5px 9px;
      border-radius: 999px;
      background: rgba(47, 111, 78, 0.13);
      color: var(--green);
      font-size: 12px;
      font-weight: 900;
      margin-bottom: 10px;
    }}
    .goal-card p {{ margin: 0; color: #465047; font-size: 13px; }}
    .legend-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 14px 0 20px; }}
    .legend-item {{ border: 1px solid var(--line); border-radius: 16px; background: #f7eddd; padding: 14px; }}
    .legend-item strong {{ display: block; font-size: 13px; margin-bottom: 5px; }}
    .legend-item span {{ display: block; color: var(--muted); font-size: 12px; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }}
    input, select {{ border: 1px solid var(--line); border-radius: 12px; background: #fffaf1; padding: 10px 12px; font: inherit; min-height: 42px; }}
    input {{ min-width: 260px; flex: 1; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }}
    .tab-btn {{
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--chip);
      color: var(--ink);
      padding: 10px 16px;
      font: inherit;
      font-weight: 800;
      cursor: pointer;
    }}
    .tab-btn.active {{
      background: var(--green);
      border-color: var(--green);
      color: #fffaf1;
    }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    .table-wrap {{ overflow: auto; border: 1px solid var(--line); border-radius: 18px; background: rgba(255, 250, 241, 0.7); }}
    table {{ width: 100%; border-collapse: collapse; min-width: 1120px; font-size: 13px; }}
    th, td {{ padding: 12px 14px; border-bottom: 1px solid var(--line); vertical-align: top; text-align: left; }}
    th {{ position: sticky; top: 0; z-index: 1; background: #e6dac8; color: #252b25; font-size: 12px; white-space: nowrap; }}
    tr:hover td {{ background: rgba(47, 111, 78, 0.05); }}
    .status {{ display: inline-flex; padding: 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 800; white-space: nowrap; }}
    .done {{ color: var(--green); background: rgba(47, 111, 78, 0.13); }}
    .hold {{ color: var(--amber); background: rgba(179, 107, 24, 0.14); }}
    .stop {{ color: var(--red); background: rgba(157, 59, 48, 0.12); }}
    .pagination {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 14px;
      color: var(--muted);
      font-size: 13px;
    }}
    .page-controls {{ display: flex; align-items: center; gap: 8px; }}
    .page-btn {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fffaf1;
      padding: 8px 10px;
      font: inherit;
      cursor: pointer;
    }}
    .page-btn:disabled {{ opacity: 0.45; cursor: not-allowed; }}
    .timeline {{ display: grid; gap: 12px; }}
    .event {{ display: grid; grid-template-columns: 120px 1fr; gap: 14px; padding: 16px; border: 1px solid var(--line); border-radius: 18px; background: var(--panel); }}
    .date {{ font-weight: 900; color: var(--green); font-size: 13px; }}
    .event strong {{ display: block; margin-bottom: 5px; }}
    .decision {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .decision .card {{ border-top: 5px solid var(--green); }}
    .decision .card:nth-child(2) {{ border-top-color: var(--blue); }}
    .foot {{ color: var(--muted); font-size: 12px; margin-top: 30px; }}
    @media (max-width: 980px) {{
      .page {{ display: block; }}
      aside {{ position: static; height: auto; }}
      main {{ padding: 22px; }}
      .hero, .cards, .decision, .goal-grid, .brief-grid, .legend-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <aside>
      <div class="brand">Track 3 Dashboard</div>
      <div class="sub">작품 가격 예측 실험 가설과 결과를 한 화면에서 보는 페이지</div>
      <nav>
        <a href="#summary">요약</a>
        <a href="#decision">현재 모델 후보</a>
        <a href="#goals">세부 목표</a>
        <a href="#records">가설/실험 표</a>
        <a href="#timeline">진행 흐름</a>
        <a href="#links">문서 링크</a>
      </nav>
    </aside>

    <main>
      <section class="hero" id="summary">
        <div class="panel">
          <h1>Track 3 현재 판단</h1>
          <ul class="summary-list">
            <li>현재 결론: Warm / Cold 단일 공유 모델보다 분리 운영이 타당</li>
            <li>Warm: H66 <code>larger-low-lr LightGBM</code> 후보를 우선 유지</li>
            <li>Cold: H32 <code>2D 기본 + 3D 전용</code> 조건부 fallback 후보 유지</li>
            <li>서비스 출력: 단일 가격만 제공하는 것은 위험하며, 가격 범위는 아직 “운영 검토 후보”로 관리</li>
            <li>운영 확정 전 필수 보완: temporal-safe 작가 피처, calibration pipeline 고정</li>
          </ul>
          <div class="meta">
            <span class="pill green">검증 완료 {done}개</span>
            <span class="pill amber">보류 {hold}개</span>
            <span class="pill">최신 가설 {latest}</span>
            <span class="pill">최종 생성 {today}</span>
          </div>
        </div>
        <div class="panel">
          <h2>운영 판단 지표</h2>
          <div class="score-grid">
            <div class="score"><small>Warm 최종 후보</small><strong>0.1051</strong><span>H66, larger-low-lr multi-seed 평균</span></div>
            <div class="score"><small>Cold 최적 후보</small><strong>0.2786</strong><span>H32, 3D 조건부 fallback</span></div>
            <div class="score"><small>Warm 가격 범위 폭</small><strong>x1.52</strong><span>전체 기준, 저이력은 x1.94 필요</span></div>
            <div class="score"><small>Cold 가격 범위 폭</small><strong>x2.27</strong><span>전체 기준, 고위험은 x2.88~x3.11 필요</span></div>
          </div>
        </div>
      </section>

      <section class="brief-grid">
        <div class="brief green">
          <h3>모델 라우팅</h3>
          <strong>작가 학습 이력 1건 기준</strong>
          <p>학습 데이터에 작가가 있으면 Warm, 없으면 Cold. H68에서 3건/5건 기준은 성능 악화로 미채택.</p>
        </div>
        <div class="brief blue">
          <h3>운영 입력 피처</h3>
          <strong>운영 가능 피처만 유지</strong>
          <p>작품 구조, 호수, 3D, Warm 작가 이력 피처를 사용. 데이터 출처/가격대 같은 운영 불가 피처는 제외.</p>
        </div>
        <div class="brief amber">
          <h3>검증 리스크</h3>
          <strong>test 반복 사용 주의</strong>
          <p>release split으로 많은 결정을 했으므로, 출시 전 새 holdout 또는 내부 CV로 최종 재확인이 필요.</p>
        </div>
        <div class="brief red">
          <h3>운영 전 blocker</h3>
          <strong>temporal-safe 미해결</strong>
          <p>작가 가격 통계는 거래 시점 이전 정보만 쓰는 방식으로 재검증해야 운영 확정 가능.</p>
        </div>
        <div class="brief amber">
          <h3>가격 범위 상태</h3>
          <strong>후보, 확정 아님</strong>
          <p>H70 coverage는 목표에 근접했지만 범위가 넓다. 서비스 적용 전 문구, UX, 구간별 실패율 기준이 필요.</p>
        </div>
      </section>

      <section id="decision">
        <div class="decision">
          <div class="card">
            <h2>현재 채택 방향</h2>
            <ul>
              <li>Warm: H66 <code>H31 피처셋 + larger-low-lr</code> 후보로 갱신</li>
              <li>Cold: H32 <code>2D 기본 + 3D 전용</code> 조건부 후보 유지</li>
              <li>PR7 <code>0.1031</code>은 탐색 기록이며, 현재 release split 기준 최종 후보는 H66 <code>0.1051</code></li>
            </ul>
          </div>
          <div class="card">
            <h2>해석 주의</h2>
            <ul>
              <li>PR7 <code>0.1031</code>은 탐색/CV 기준 최고 기록</li>
              <li>H33 release split 재확인에서는 PR7 운영 가능 피처 최고가 <code>0.2251</code></li>
              <li>H66 multi-seed 재검증에서 Warm 후보가 <code>0.1090 -> 0.1051</code>로 갱신됨</li>
              <li>따라서 현재 Warm 기준 성능은 H66 <code>0.1051</code>을 우선 사용</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="panel" id="goals">
        <h2>세부 연구 목표</h2>
        <p class="foot">각 가설은 아래 목표 중 하나 이상을 검증하기 위해 설정한다. 가설 상태표의 `세부 목표` 컬럼에서 연결 관계를 확인한다.</p>
        <div class="goal-grid">
{goal_cards}
        </div>
      </section>

      <section class="panel" id="records">
        <h2>가설 / 실험 기록</h2>
        <p class="foot">표시는 최신순이다. 가설은 H번호가 큰 순서, 실험 결과는 날짜가 최신인 순서로 먼저 보여준다.</p>
        <div class="legend-grid" aria-label="검증 강도 설명">
          <div class="legend-item"><strong>release split 검증</strong><span>고정된 Warm / Cold 평가셋에서 결과를 확인한 상태</span></div>
          <div class="legend-item"><strong>multi-seed 재검증</strong><span>seed를 바꿔도 결과 방향이 유지되는지 확인한 상태</span></div>
          <div class="legend-item"><strong>내부 calibration + release test 검증</strong><span>정책/범위는 내부 calibration에서 정하고 release test에는 검증만 한 상태</span></div>
          <div class="legend-item"><strong>내부 calibration 선택 + release test 검증</strong><span>여러 후보 중 선택은 내부 calibration에서 하고, test에는 선택된 후보만 적용한 상태</span></div>
          <div class="legend-item"><strong>temporal-safe 필요</strong><span>성능은 확인됐지만 예측 시점 이후 정보 누수 가능성을 아직 닫지 못한 상태</span></div>
          <div class="legend-item"><strong>보류/데이터 조건 미충족</strong><span>현재 데이터만으로는 검증을 완료할 수 없는 상태</span></div>
        </div>
        <div class="tabs">
          <button class="tab-btn active" data-tab="hypothesesPanel">가설 상태</button>
          <button class="tab-btn" data-tab="experimentsPanel">실험 결과</button>
        </div>

        <div class="tab-panel active" id="hypothesesPanel">
          <div class="toolbar">
            <input id="hypothesisSearch" type="search" placeholder="가설 검색: H29, Cold, 3D, 보류...">
            <select id="statusFilter">
              <option value="">전체 상태</option>
              <option value="검증 완료">검증 완료</option>
              <option value="보류">보류</option>
              <option value="중단">중단</option>
            </select>
            <select id="hypothesisPageSize">
              <option value="10">10개씩 보기</option>
              <option value="20">20개씩 보기</option>
              <option value="50">50개씩 보기</option>
            </select>
          </div>
          <div class="table-wrap">
            <table id="hypothesisTable">
              <thead><tr><th>가설</th><th>세부 목표</th><th>상태</th><th>검증 강도</th><th>요약</th><th>관련 실험</th><th>현재 판단</th><th>후속</th></tr></thead>
              <tbody>
{hypothesis_body}
              </tbody>
            </table>
          </div>
          <div class="pagination" id="hypothesisPager">
            <span class="page-summary"></span>
            <div class="page-controls">
              <button class="page-btn prev">이전</button>
              <span class="page-current"></span>
              <button class="page-btn next">다음</button>
            </div>
          </div>
        </div>

        <div class="tab-panel" id="experimentsPanel">
          <div class="toolbar">
            <input id="experimentSearch" type="search" placeholder="실험 검색: H29, Warm, Cold, 보류...">
            <select id="experimentPageSize">
              <option value="10">10개씩 보기</option>
              <option value="20">20개씩 보기</option>
              <option value="50">50개씩 보기</option>
            </select>
          </div>
          <div class="table-wrap">
            <table id="experimentTable">
              <thead><tr><th>날짜</th><th>실험 ID</th><th>가설</th><th>상태</th><th>Warm 결과</th><th>Cold 결과</th><th>결론</th><th>기록</th></tr></thead>
              <tbody>
{experiment_body}
              </tbody>
            </table>
          </div>
          <div class="pagination" id="experimentPager">
            <span class="page-summary"></span>
            <div class="page-controls">
              <button class="page-btn prev">이전</button>
              <span class="page-current"></span>
              <button class="page-btn next">다음</button>
            </div>
          </div>
        </div>
      </section>

      <section class="panel" id="timeline">
        <h2>진행 흐름</h2>
        <div class="timeline">
          <div class="event"><div class="date">1단계</div><div><strong>데이터 기준 고정</strong><ul><li>release split 기준 유지</li><li>train / warm / cold 분리</li></ul></div></div>
          <div class="event"><div class="date">2단계</div><div><strong>기본 모델 및 기본 변수 확인</strong><ul><li>Warm: LightGBM 계열</li><li>Cold: robust 선형 계열</li></ul></div></div>
          <div class="event"><div class="date">3단계</div><div><strong>파생 피처 검증</strong><ul><li>호수/3D 피처 후보 검증</li><li>재료/조합/결측 후보 분리 관리</li></ul></div></div>
          <div class="event"><div class="date">4단계</div><div><strong>Warm/Cold 정책 분리</strong><ul><li>Warm: H66 후보</li><li>Cold: H32 조건부 후보</li></ul></div></div>
        </div>
      </section>

      <section class="panel" id="links">
        <h2>기준 문서 링크</h2>
        <div class="cards">
          <div class="card"><h3>실험 계획서</h3><p><a href="track3_experiment_plan_v1.md">track3_experiment_plan_v1.md</a></p></div>
          <div class="card"><h3>현재 의사결정 요약</h3><p><a href="track3_current_decision_summary.md">track3_current_decision_summary.md</a></p></div>
          <div class="card"><h3>가설 리스트</h3><p><a href="track3_hypothesis_list_v1.md">track3_hypothesis_list_v1.md</a></p></div>
          <div class="card"><h3>가설 요약표</h3><p><a href="track3_hypothesis_table.md">track3_hypothesis_table.md</a></p></div>
          <div class="card"><h3>가설 결과 종합</h3><p><a href="track3_hypothesis_result_summary.md">track3_hypothesis_result_summary.md</a></p></div>
          <div class="card"><h3>실험 결과표</h3><p><a href="track3_experiment_results_table.md">track3_experiment_results_table.md</a></p></div>
          <div class="card"><h3>실험 인덱스</h3><p><a href="track3_experiments/INDEX.md">track3_experiments/INDEX.md</a></p></div>
        </div>
        <p class="foot">문서 관리: 이 HTML은 자동 생성 파일이다. 직접 수정하지 말고 Markdown 기준 문서를 수정한 뒤 <code>python3 scripts/track3/generate_experiment_dashboard.py</code>를 실행한다. 최종 생성일: {today}</p>
      </section>
    </main>
  </div>

  <script>
    function setupTabs() {{
      document.querySelectorAll(".tab-btn").forEach((button) => {{
        button.addEventListener("click", () => {{
          document.querySelectorAll(".tab-btn").forEach((item) => item.classList.remove("active"));
          document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
          button.classList.add("active");
          document.getElementById(button.dataset.tab).classList.add("active");
        }});
      }});
    }}

    function setupPagedTable(options) {{
      const table = document.getElementById(options.tableId);
      const search = document.getElementById(options.searchId);
      const status = options.statusId ? document.getElementById(options.statusId) : null;
      const pageSize = document.getElementById(options.pageSizeId);
      const pager = document.getElementById(options.pagerId);
      const summary = pager.querySelector(".page-summary");
      const current = pager.querySelector(".page-current");
      const prev = pager.querySelector(".prev");
      const next = pager.querySelector(".next");
      let page = 1;
      let filteredRows = [];

      function rowMatches(row) {{
        const q = search.value.trim().toLowerCase();
        const s = status ? status.value : "";
        const text = row.innerText.toLowerCase();
        const statusText = row.querySelector(".status")?.innerText || "";
        return (!q || text.includes(q)) && (!s || statusText === s);
      }}

      function run(resetPage = false) {{
        if (resetPage) page = 1;
        const rows = [...table.querySelectorAll("tbody tr")];
        filteredRows = rows.filter(rowMatches);
        const size = Number(pageSize.value);
        const totalPages = Math.max(1, Math.ceil(filteredRows.length / size));
        page = Math.min(page, totalPages);
        const start = (page - 1) * size;
        const end = start + size;
        rows.forEach((row) => (row.style.display = "none"));
        filteredRows.slice(start, end).forEach((row) => (row.style.display = ""));
        summary.textContent = `총 ${{filteredRows.length}}개 중 ${{filteredRows.length ? start + 1 : 0}}-${{Math.min(end, filteredRows.length)}}개 표시`;
        current.textContent = `${{page}} / ${{totalPages}}`;
        prev.disabled = page <= 1;
        next.disabled = page >= totalPages;
      }}

      search.addEventListener("input", () => run(true));
      if (status) status.addEventListener("change", () => run(true));
      pageSize.addEventListener("change", () => run(true));
      prev.addEventListener("click", () => {{ page -= 1; run(); }});
      next.addEventListener("click", () => {{ page += 1; run(); }});
      run(true);
    }}

    setupTabs();
    setupPagedTable({{
      tableId: "hypothesisTable",
      searchId: "hypothesisSearch",
      statusId: "statusFilter",
      pageSizeId: "hypothesisPageSize",
      pagerId: "hypothesisPager",
    }});
    setupPagedTable({{
      tableId: "experimentTable",
      searchId: "experimentSearch",
      statusId: null,
      pageSizeId: "experimentPageSize",
      pagerId: "experimentPager",
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    hypothesis_rows = parse_first_table(HYPOTHESIS_TABLE)
    experiment_rows = parse_first_table(EXPERIMENT_TABLE)
    hypothesis_rows = sorted(hypothesis_rows, key=hypothesis_sort_key, reverse=True)
    experiment_rows = sorted(experiment_rows, key=experiment_sort_key, reverse=True)
    OUT_PATH.write_text(dashboard_html(hypothesis_rows, experiment_rows), encoding="utf-8")
    print(f"Generated {OUT_PATH}")
    print(f"Hypotheses: {len(hypothesis_rows)}")
    print(f"Experiments: {len(experiment_rows)}")


if __name__ == "__main__":
    main()
