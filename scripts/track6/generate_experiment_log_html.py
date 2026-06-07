#!/usr/bin/env python3
"""Generate a journal-style HTML page for one Track6 experiment folder."""
from __future__ import annotations

import argparse
import html
import json
from datetime import date
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fmt_float(value: object, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def table_html(frame: pd.DataFrame, cols: list[str] | None = None, max_rows: int | None = None) -> str:
    if cols is not None:
        frame = frame[cols].copy()
    if max_rows is not None:
        frame = frame.head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in frame.columns)
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for col in frame.columns:
            value = row[col]
            if isinstance(value, float):
                value = fmt_float(value)
            cells.append(f"<td>{html.escape(str(value))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def metric_lookup(metrics: pd.DataFrame, case: str) -> dict[str, object]:
    rows = metrics[metrics["experiment_case"].eq(case)]
    return rows.iloc[0].to_dict() if len(rows) else {}


def make_file_cards(manifest: dict) -> str:
    generated = manifest.get("generated_files", {})
    cards = []
    for key, value in generated.items():
        cards.append(
            "<article>"
            f"<strong>{html.escape(key)}</strong>"
            f"<code>{html.escape(value)}</code>"
            "</article>"
        )
    return "\n".join(cards)


def make_slice_tables(slices: pd.DataFrame) -> str:
    if slices.empty:
        return "<p>slice 결과가 없습니다.</p>"
    selected_cases = ["warm_model_warm_test_log", "cold_model_cold_test_log"]
    blocks = []
    for case in selected_cases:
        case_df = slices[slices["experiment_case"].eq(case)].copy()
        if case_df.empty:
            continue
        case_df = case_df.sort_values(["slice_type", "median_ape"])
        blocks.append(
            f"<h3>{html.escape(case)}</h3>"
            + table_html(
                case_df,
                cols=["slice_type", "slice_value", "n", "median_ape", "p95_ape", "within_30", "within_50"],
            )
        )
    return "\n".join(blocks)


def make_feature_case_table() -> str:
    rows = [
        {
            "케이스": "Warm 일반",
            "학습에 사용된 피처": "artist_name_ko, estimated_ho",
            "학습 정답값": "price_krw",
            "테스트에 사용된 피처": "artist_name_ko, estimated_ho",
            "테스트 정답값": "price_krw",
            "테스트 대상": "Warm test / Cold test",
            "예측 후 처리": "원화 가격 그대로 평가",
            "확인하려는 내용": "작가명과 원 호수만으로 가격을 예측할 수 있는지 확인",
        },
        {
            "케이스": "Warm ln 변형",
            "학습에 사용된 피처": "artist_name_ko, ln_estimated_ho",
            "학습 정답값": "ln_price_krw",
            "테스트에 사용된 피처": "artist_name_ko, ln_estimated_ho",
            "테스트 정답값": "price_krw",
            "테스트 대상": "Warm test / Cold test",
            "예측 후 처리": "예측한 ln가격을 원화 가격으로 되돌려 평가",
            "확인하려는 내용": "ln 변환이 Warm 예측을 개선하는지 확인",
        },
        {
            "케이스": "Cold 일반",
            "학습에 사용된 피처": "estimated_ho",
            "학습 정답값": "price_krw",
            "테스트에 사용된 피처": "estimated_ho",
            "테스트 정답값": "price_krw",
            "테스트 대상": "Cold test / Warm test",
            "예측 후 처리": "원화 가격 그대로 평가",
            "확인하려는 내용": "신규 작가 상황에서 호수만으로 예측 가능한지 확인",
        },
        {
            "케이스": "Cold ln 변형",
            "학습에 사용된 피처": "ln_estimated_ho",
            "학습 정답값": "ln_price_krw",
            "테스트에 사용된 피처": "ln_estimated_ho",
            "테스트 정답값": "price_krw",
            "테스트 대상": "Cold test / Warm test",
            "예측 후 처리": "예측한 ln가격을 원화 가격으로 되돌려 평가",
            "확인하려는 내용": "ln 변환이 Cold 예측을 개선하는지 확인",
        },
    ]
    return table_html(pd.DataFrame(rows))


def make_pipeline_steps() -> str:
    steps = [
        {
            "순서": "1",
            "단계": "원본 후보 데이터 로드",
            "사용 파일": "data/track6/track6_feature_candidates_name_corrected.csv",
            "설명": "Track6 정제 후보 데이터에서 실험용 row를 다시 선별",
        },
        {
            "순서": "2",
            "단계": "학습 후보 필터링",
            "사용 파일": "원본 후보 데이터",
            "설명": "is_training_candidate=true, 가격/작가/면적이 있는 row만 사용",
        },
        {
            "순서": "3",
            "단계": "피처 생성",
            "사용 파일": "필터링 데이터",
            "설명": "area_cm2를 F형 호수표에 매칭해 estimated_ho 생성, ln_estimated_ho와 ln_price_krw 생성",
        },
        {
            "순서": "4",
            "단계": "Warm / Cold 분리",
            "사용 파일": "생성 피처 포함 데이터",
            "설명": "Warm은 train에 같은 작가가 있는 평가 row, Cold는 train에 없는 작가 row",
        },
        {
            "순서": "5",
            "단계": "실험별 feature/label 파일 생성",
            "사용 파일": "data/*.csv",
            "설명": "입력 feature와 정답 label을 분리 저장해 가격 누수 가능성을 줄임",
        },
        {
            "순서": "6",
            "단계": "모델 학습",
            "사용 파일": "train_features + train_labels",
            "설명": "Ridge 기반 헤도닉 선형 회귀 학습. 작가명은 one-hot, 수치 피처는 표준화",
        },
        {
            "순서": "7",
            "단계": "예측",
            "사용 파일": "test_features",
            "설명": "평가 feature만 모델에 넣어 예측값 생성. 이 단계에서는 정답 가격을 모델에 넣지 않음",
        },
        {
            "순서": "8",
            "단계": "결과 평가",
            "사용 파일": "predictions + test_labels",
            "설명": "예측값과 정답 가격을 합쳐 median APE, p95 APE, Within-30/50 계산",
        },
    ]
    return table_html(pd.DataFrame(steps))


def make_model_info_table() -> str:
    rows = [
        {
            "항목": "사용 모델",
            "내용": "Ridge 기반 Hedonic Linear Regression",
            "설명": "가격을 작품 속성의 합으로 설명하는 선형 회귀 baseline",
        },
        {
            "항목": "구현",
            "내용": "sklearn Ridge(alpha=1.0)",
            "설명": "작가 one-hot 피처가 많아질 수 있어 일반 Linear Regression보다 안정적인 Ridge를 사용",
        },
        {
            "항목": "범주형 처리",
            "내용": "artist_name_ko -> OneHotEncoder(handle_unknown='ignore')",
            "설명": "학습에 없는 작가가 테스트에 나오면 해당 작가 피처는 0으로 처리",
        },
        {
            "항목": "수치형 처리",
            "내용": "estimated_ho / ln_estimated_ho -> StandardScaler",
            "설명": "호수 값의 스케일 영향을 줄이기 위해 표준화 후 학습",
        },
        {
            "항목": "base 모델 목표값",
            "내용": "price_krw",
            "설명": "원화 가격을 직접 예측",
        },
        {
            "항목": "log 모델 목표값",
            "내용": "ln_price_krw",
            "설명": "로그 가격을 예측한 뒤 exp 변환으로 원화 가격 복원",
        },
        {
            "항목": "이번 실험에서 제외한 모델",
            "내용": "LightGBM, CatBoost, XGBoost, Huber, Quantile",
            "설명": "이번 실험은 모델 튜닝이 아니라 작가명/호수/ln 변환 신호 확인이 목적이므로 후속 실험에서 비교",
        },
    ]
    return table_html(pd.DataFrame(rows))


def make_data_file_role_table(manifest: dict) -> str:
    generated = manifest.get("generated_files", {})
    rows = [
        {
            "파일": "warm_train_base_features",
            "역할": "Warm 일반 학습 입력",
            "컬럼": "_experiment_row_id, artist_name_ko, estimated_ho",
            "경로": generated.get("warm_train_base_features", ""),
        },
        {
            "파일": "warm_train_base_labels",
            "역할": "Warm 일반 학습 정답",
            "컬럼": "_experiment_row_id, price_krw, ln_price_krw",
            "경로": generated.get("warm_train_base_labels", ""),
        },
        {
            "파일": "warm_train_log_features",
            "역할": "Warm ln 학습 입력",
            "컬럼": "_experiment_row_id, artist_name_ko, estimated_ho, ln_estimated_ho",
            "경로": generated.get("warm_train_log_features", ""),
        },
        {
            "파일": "warm_train_log_labels",
            "역할": "Warm ln 학습 정답",
            "컬럼": "_experiment_row_id, price_krw, ln_price_krw",
            "경로": generated.get("warm_train_log_labels", ""),
        },
        {
            "파일": "warm_test_*",
            "역할": "Warm 평가 입력/정답",
            "컬럼": "feature 파일은 입력값, labels 파일은 평가용 가격",
            "경로": generated.get("warm_test_base_features", ""),
        },
        {
            "파일": "cold_train_base_features",
            "역할": "Cold 일반 학습 입력",
            "컬럼": "_experiment_row_id, estimated_ho",
            "경로": generated.get("cold_train_base_features", ""),
        },
        {
            "파일": "cold_train_log_features",
            "역할": "Cold ln 학습 입력",
            "컬럼": "_experiment_row_id, estimated_ho, ln_estimated_ho",
            "경로": generated.get("cold_train_log_features", ""),
        },
        {
            "파일": "cold_test_*",
            "역할": "Cold 평가 입력/정답",
            "컬럼": "feature 파일은 입력값, labels 파일은 평가용 가격",
            "경로": generated.get("cold_test_base_features", ""),
        },
    ]
    return table_html(pd.DataFrame(rows))


def render(exp_dir: Path) -> str:
    readme = read_text(exp_dir / "README.md")
    manifest = json.loads(read_text(exp_dir / "outputs" / "experiment_manifest.json"))
    metrics = pd.read_csv(exp_dir / "outputs" / "metrics.csv")
    slices = pd.read_csv(exp_dir / "outputs" / "slice_metrics.csv")

    warm_base = metric_lookup(metrics, "warm_model_warm_test_base")
    warm_log = metric_lookup(metrics, "warm_model_warm_test_log")
    cold_base = metric_lookup(metrics, "cold_model_cold_test_base")
    cold_log = metric_lookup(metrics, "cold_model_cold_test_log")
    warm_on_cold_log = metric_lookup(metrics, "warm_model_cold_test_log")

    warm_delta = float(warm_base["median_ape"]) - float(warm_log["median_ape"])
    cold_delta = float(cold_base["median_ape"]) - float(cold_log["median_ape"])

    metrics_view = metrics[
        ["experiment_case", "n", "median_ape", "p95_ape", "mape", "within_30", "within_50", "rmse_log"]
    ].copy()

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>T6-E010 실험 일지</title>
  <style>
    :root {{
      --bg:#f4efe5;
      --paper:#fffdf7;
      --ink:#1c241f;
      --muted:#667167;
      --line:#d8cdb8;
      --green:#27684a;
      --blue:#234f73;
      --amber:#9b6124;
      --red:#9c3d2f;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      background:linear-gradient(135deg,#efe7d7,#f8f5ec 45%,#e9f0e7);
      color:var(--ink);
      font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif;
      line-height:1.62;
    }}
    main {{ max-width:1180px; margin:0 auto; padding:34px 22px 80px; }}
    header {{
      background:var(--paper);
      border:1px solid var(--line);
      border-radius:28px;
      padding:34px;
      box-shadow:0 18px 50px rgba(42,34,22,.12);
    }}
    h1 {{ margin:0; font-size:46px; letter-spacing:-.055em; }}
    h2 {{ margin:0 0 14px; font-size:24px; letter-spacing:-.035em; }}
    h3 {{ margin:22px 0 8px; font-size:18px; }}
    section {{
      background:rgba(255,253,247,.94);
      border:1px solid var(--line);
      border-radius:24px;
      padding:26px;
      margin-top:18px;
      box-shadow:0 12px 34px rgba(42,34,22,.08);
    }}
    ul {{ margin:10px 0 0; padding-left:21px; }}
    li {{ margin:5px 0; }}
    code {{
      display:inline-block;
      max-width:100%;
      overflow-wrap:anywhere;
      background:#eee5d4;
      color:#22362d;
      border-radius:7px;
      padding:2px 6px;
      font-family:"SFMono-Regular",Consolas,monospace;
      font-size:.92em;
    }}
    .meta {{
      display:grid;
      grid-template-columns:repeat(4,1fr);
      gap:12px;
      margin-top:24px;
    }}
    .card, .file-grid article {{
      background:#f8f1e5;
      border:1px solid var(--line);
      border-radius:18px;
      padding:16px;
    }}
    .card span {{ color:var(--muted); font-size:13px; font-weight:700; }}
    .card strong {{ display:block; margin-top:5px; font-size:24px; letter-spacing:-.03em; }}
    .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
    .file-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }}
    .file-grid strong {{ display:block; margin-bottom:6px; }}
    .badge {{
      display:inline-flex;
      padding:5px 9px;
      border-radius:999px;
      font-size:12px;
      font-weight:800;
      margin-right:6px;
    }}
    .ok {{ background:rgba(39,104,74,.14); color:var(--green); }}
    .warn {{ background:rgba(155,97,36,.14); color:var(--amber); }}
    .risk {{ background:rgba(156,61,47,.14); color:var(--red); }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:16px; }}
    table {{ width:100%; border-collapse:collapse; min-width:820px; background:var(--paper); }}
    th, td {{ padding:11px 12px; border-bottom:1px solid var(--line); vertical-align:top; font-size:13px; }}
    th {{ background:#eadfcd; text-align:left; position:sticky; top:0; }}
    .note {{ color:var(--muted); font-size:14px; }}
    .markdown {{
      white-space:pre-wrap;
      background:#fbf7ef;
      border:1px dashed var(--line);
      border-radius:18px;
      padding:18px;
      max-height:360px;
      overflow:auto;
    }}
    @media(max-width:860px) {{
      .meta, .grid-2, .file-grid {{ grid-template-columns:1fr; }}
      h1 {{ font-size:34px; }}
      main {{ padding:18px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <span class="badge ok">실험 일지 샘플</span>
    <span class="badge ok">검증 완료</span>
    <span class="badge warn">ln 변환 효과 확인</span>
    <h1>T6-E010 작가명 + 호수 헤도닉 실험</h1>
    <p>개별 실험 폴더에서 데이터 생성, 모델 실행, 결과 해석, 재현 방법을 한 번에 확인하기 위한 첫 번째 HTML 일지입니다.</p>
    <div class="meta">
      <div class="card"><span>생성일</span><strong>{date.today().isoformat()}</strong></div>
      <div class="card"><span>Train</span><strong>{manifest['rows']['train']:,}건</strong></div>
      <div class="card"><span>Warm Test</span><strong>{manifest['rows']['warm_test']:,}건</strong></div>
      <div class="card"><span>Cold Test</span><strong>{manifest['rows']['cold_test']:,}건</strong></div>
    </div>
  </header>

  <section>
    <h2>1. 실험 목적과 가설</h2>
    <ul>
      <li>가설 1: 작가명(한글)과 사이즈(호)만으로도 가격 예측에서 유의미한 결과를 볼 수 있다.</li>
      <li>가설 2: 호수와 가격을 ln 변환하면 원값을 쓰는 것보다 예측 결과가 개선될 것이다.</li>
      <li>1차 목적: ln 변환이 예측 정확도를 개선하는지 확인한다.</li>
      <li>2차 목적: Warm과 Cold에서 같은 방식의 모델을 써도 되는지 확인한다.</li>
    </ul>
  </section>

  <section>
    <h2>2. 유의미함 기준</h2>
    <ul>
      <li><strong>median APE</strong>: 대표 오차. 낮을수록 좋다.</li>
      <li><strong>p95 APE</strong>: 큰 오차 위험. 낮을수록 좋다.</li>
      <li><strong>Within-30</strong>: 실제 가격의 30% 이내로 맞춘 비율. 높을수록 좋다.</li>
      <li><strong>Within-50</strong>: 실제 가격의 50% 이내로 맞춘 비율. 높을수록 좋다.</li>
      <li><strong>Warm / Cold 분리 판단</strong>: Cold 전용 모델이 Cold test에서 더 안정적이면 모델을 분리한다.</li>
      <li><strong>운영 가능 여부</strong>: 사용자가 입력 가능한 값으로 재현 가능한 피처만 최종 후보로 본다.</li>
    </ul>
  </section>

  <section>
    <h2>3. 데이터 생성 방식</h2>
    <div class="grid-2">
      <div>
        <h3>원본 데이터</h3>
        <ul>
          <li><code>{html.escape(manifest['source'])}</code></li>
          <li><code>is_training_candidate = true</code>인 row만 사용</li>
          <li>가격, 작가명, 작가 key, 면적이 없는 row 제외</li>
          <li>호수는 원본 컬럼이 아니라 <code>area_cm2</code>를 F형 호수표에 매칭해 생성</li>
        </ul>
      </div>
      <div>
        <h3>Split 검증</h3>
        <ul>
          <li>Cold/train 작가 겹침: <strong>{manifest['checks']['cold_train_artist_overlap']}</strong></li>
          <li>Warm test 작가별 train 최소 작품 수: <strong>{manifest['checks']['warm_test_min_train_works']}</strong></li>
          <li>Warm test 작가별 평가 최소 작품 수: <strong>{manifest['checks']['warm_test_rows_per_artist_min']}</strong></li>
          <li>Seed: <code>{manifest['seed']}</code></li>
        </ul>
      </div>
    </div>
  </section>

  <section>
    <h2>4. 실험 케이스</h2>
    <p class="note">아래 표는 이번 실험에서 학습에 사용된 피처와 테스트에 사용된 피처를 케이스별로 명확히 구분한 것입니다.</p>
    <div class="table-wrap">{make_feature_case_table()}</div>
    <h3>케이스 설명</h3>
    <ul>
      <li>Warm 일반: <code>artist_name_ko + estimated_ho -> price_krw</code></li>
      <li>Warm 변형: <code>artist_name_ko + ln_estimated_ho -> ln_price_krw</code></li>
      <li>Cold 일반: <code>estimated_ho -> price_krw</code></li>
      <li>Cold 변형: <code>ln_estimated_ho -> ln_price_krw</code></li>
      <li>Warm 모델을 Cold test에 적용해 단일 모델 가능성도 함께 확인</li>
      <li>Cold 모델을 Warm test에 적용해 작가명 없이 어느 정도 예측 가능한지도 확인</li>
    </ul>
  </section>

  <section>
    <h2>5. 사용 모델</h2>
    <p class="note">이번 실험에서 실제로 학습에 사용한 모델과 전처리 방식입니다.</p>
    <div class="table-wrap">{make_model_info_table()}</div>
  </section>

  <section>
    <h2>6. 생성 데이터 파일</h2>
    <p class="note">가격 컬럼은 feature 파일에 넣지 않고 label 파일에 분리했습니다. 모델 학습 때는 train label을 쓰고, 평가는 예측 완료 후 test label과 비교합니다.</p>
    <div class="table-wrap">{make_data_file_role_table(manifest)}</div>
    <h3>전체 생성 파일</h3>
    <div class="file-grid">
      {make_file_cards(manifest)}
    </div>
  </section>

  <section>
    <h2>7. 학습과 평가 흐름</h2>
    <p class="note">모델이 정답 가격을 보는 시점과 보지 않는 시점을 분리해 기록했습니다.</p>
    <div class="table-wrap">{make_pipeline_steps()}</div>
  </section>

  <section>
    <h2>8. 전체 결과</h2>
    <div class="table-wrap">{table_html(metrics_view)}</div>
  </section>

  <section>
    <h2>9. 핵심 해석</h2>
    <div class="grid-2">
      <div class="card">
        <span>Warm ln 개선폭</span>
        <strong>{fmt_float(warm_base['median_ape'])} → {fmt_float(warm_log['median_ape'])}</strong>
        <p class="note">median APE 기준 {fmt_float(warm_delta)} 개선. 작가명 + ln호수 조합은 Warm에서 강한 baseline으로 볼 수 있음.</p>
      </div>
      <div class="card">
        <span>Cold ln 개선폭</span>
        <strong>{fmt_float(cold_base['median_ape'])} → {fmt_float(cold_log['median_ape'])}</strong>
        <p class="note">median APE 기준 {fmt_float(cold_delta)} 개선. Cold에서도 원값보다 ln 변환이 훨씬 안정적임.</p>
      </div>
    </div>
    <ul>
      <li>Warm 최고 결과: <code>warm_model_warm_test_log</code>, median APE <strong>{fmt_float(warm_log['median_ape'])}</strong></li>
      <li>Cold 전용 log 결과: <code>cold_model_cold_test_log</code>, median APE <strong>{fmt_float(cold_log['median_ape'])}</strong></li>
      <li>Warm 모델을 Cold에 적용한 log 결과는 median APE <strong>{fmt_float(warm_on_cold_log['median_ape'])}</strong>로 낮지만, 신규 작가명은 미등록 처리되므로 운영 기준 Cold 전용 baseline을 별도로 유지하는 것이 안전함</li>
      <li>Cold는 호수 단독으로는 한계가 크므로 재료, 지지체, 크기 구간, 작가 메타 피처 추가 실험이 필요함</li>
    </ul>
  </section>

  <section>
    <h2>10. Slice별 오차</h2>
    <p class="note">대표 케이스인 Warm log와 Cold log의 호수 구간/가격 구간별 오차입니다.</p>
    {make_slice_tables(slices)}
  </section>

  <section>
    <h2>11. 결론</h2>
    <ul>
      <li><span class="badge ok">T6-H9 부분 채택</span> Warm에서는 작가명과 호수만으로 유의미한 예측 신호가 있음.</li>
      <li><span class="badge ok">T6-H10 채택</span> ln 변환은 Warm/Cold 모두에서 원값보다 성능을 크게 개선함.</li>
      <li><span class="badge warn">Cold 후속 필요</span> Cold는 호수 단독보다 추가 피처를 붙이는 실험이 필요함.</li>
      <li><span class="badge warn">운영 주의</span> 가격은 입력값이 아니라 학습 정답/평가 라벨로만 사용해야 함.</li>
    </ul>
  </section>

  <section>
    <h2>12. 재현 방법</h2>
    <ul>
      <li>실행 명령: <code>python3 experiments/track6/T6-E010_hedonic_artist_ho_log/scripts/run_experiment.py</code></li>
      <li>실행 로그: <code>{rel(exp_dir / 'logs' / 'run.log')}</code></li>
      <li>결과 요약: <code>{rel(exp_dir / 'outputs' / 'summary.md')}</code></li>
      <li>전체 예측 결과: <code>{rel(exp_dir / 'outputs')}</code> 하위 <code>predictions_*.csv</code></li>
    </ul>
  </section>

  <section>
    <h2>부록. Markdown 일지 원문</h2>
    <div class="markdown">{html.escape(readme)}</div>
  </section>
</main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "experiment_dir",
        nargs="?",
        default="experiments/track6/T6-E010_hedonic_artist_ho_log",
        help="Experiment folder containing README.md and outputs/*.csv",
    )
    args = parser.parse_args()
    exp_dir = (REPO / args.experiment_dir).resolve()
    out = exp_dir / "experiment_log.html"
    out.write_text(render(exp_dir), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
