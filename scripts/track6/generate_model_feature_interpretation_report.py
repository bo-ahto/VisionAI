#!/usr/bin/env python3
"""Generate model-level feature interpretation report for Track6."""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DOC_DIR = REPO / "docs" / "track6" / "experiments"
INT_DIR = REPO / "experiments" / "track6" / "FINAL_model_interpretability" / "outputs"

OUT_CSV = DOC_DIR / "model_feature_interpretation_table.csv"
OUT_MD = DOC_DIR / "model_feature_interpretation_report.md"
OUT_HTML = DOC_DIR / "model_feature_interpretation_report.html"


FEATURE_GROUPS: list[dict[str, Any]] = [
    {
        "feature": "artist_key / artist_name",
        "domain": "작가 식별 정보",
        "warm_terms": ["artist_name_ko_"],
        "cold_terms": [],
        "performance_key": "작가명",
        "interpretation": "Warm에서는 동일 작가의 과거 가격 수준과 시장 포지션을 직접 반영하는 핵심 기준이다. 신규 작가 중심의 Cold에서는 직접 사용하기 어렵다.",
        "caution": "작가명 효과는 예측 모델의 가격 수준 보정에 가깝다. 작가 자체가 가격을 인과적으로 올린다고 단정하지 않는다.",
        "grade": "A",
    },
    {
        "feature": "log_area / ln_estimated_ho",
        "domain": "작품 크기",
        "warm_terms": ["log_area", "width_cm", "height_cm"],
        "cold_terms": ["ln_estimated_ho"],
        "performance_key": "호수/크기 대표값",
        "interpretation": "작품 크기는 가격 산정의 기본 축이다. Warm에서는 선형 계수와 평균 기여도 모두 가격 상승 방향으로 작동하고, Cold에서도 SHAP 상위 피처로 확인된다.",
        "caution": "크기 단독 효과는 제한적일 수 있다. 작가명, 재료, 지지체와 결합될 때 설명력이 커진다.",
        "grade": "A",
    },
    {
        "feature": "width_cm / height_cm",
        "domain": "가로/세로 실측 크기",
        "warm_terms": ["width_cm", "height_cm"],
        "cold_terms": [],
        "performance_key": "작가명 + 전체 크기",
        "interpretation": "Warm Huber에서 가로/세로는 로그면적과 함께 작품 스케일을 보완한다. 작가명으로 가격 수준을 잡은 뒤 실제 크기가 추가 설명력을 제공한다.",
        "caution": "면적과 중복 정보가 있으므로 개별 계수만으로 독립 효과를 과대 해석하지 않는다.",
        "grade": "A",
    },
    {
        "feature": "aspect_ratio / shape_bucket",
        "domain": "작품 형태",
        "warm_terms": ["aspect_ratio"],
        "cold_terms": [],
        "performance_key": "작가명 x 면적",
        "interpretation": "형태 비율은 가격을 직접 크게 움직이는 핵심 피처라기보다 크기 효과의 안정성을 보조한다. CatBoost 보정에서는 shape segment가 반복 오차를 나누는 후보가 된다.",
        "caution": "단독 영향은 약하다. extreme aspect ratio 같은 위험 구간 해석에 우선 활용한다.",
        "grade": "B",
    },
    {
        "feature": "medium_category / nant_material_idx / nant_tool",
        "domain": "재료",
        "warm_terms": [],
        "cold_terms": ["nant_material_idx", "nant_tool_"],
        "performance_key": "재료 + 크기",
        "interpretation": "재료는 단독 가격 설명력은 약하지만, Cold에서는 작가 정보가 부족할 때 작품 물성과 제작 방식의 보조 신호로 작동한다. CatBoost SHAP에서도 재료 계열이 상위 보조 피처로 확인된다.",
        "caution": "재료 단독으로 가격을 설명하면 위험하다. 크기/형태/지지체와 조합해 해석해야 한다.",
        "grade": "B",
    },
    {
        "feature": "support_category / nant_support",
        "domain": "지지체",
        "warm_terms": [],
        "cold_terms": ["nant_support_"],
        "performance_key": "지지체 + 크기/재료",
        "interpretation": "지지체는 단독 영향은 약하지만, 재료 및 크기와 함께 작품의 물성을 구분하는 보조 신호다. Cold에서는 일부 지지체 SHAP 방향이 가격 상승/하락을 나누는 데 사용된다.",
        "caution": "표본 수가 작은 지지체는 해석 불안정성이 크다. 후처리에서는 최소 표본 수 기준이 필요하다.",
        "grade": "B",
    },
    {
        "feature": "artist_meta_total_works",
        "domain": "작가 전체 작품 수",
        "warm_terms": [],
        "cold_terms": ["artist_meta_total_works"],
        "performance_key": "전체 작가 메타",
        "interpretation": "Cold CatBoost에서 높은 중요도를 보이며, 신규 작가의 시장 활동량 또는 데이터 축적 수준을 대체하는 신호로 작동한다.",
        "caution": "SHAP 평균 방향이 하락일 수 있어 단순히 작품 수가 많을수록 비싸다고 해석하면 안 된다. 구간별 비선형 관계 확인이 필요하다.",
        "grade": "A",
    },
    {
        "feature": "artist_meta_for_sale_works",
        "domain": "판매 노출 작품 수",
        "warm_terms": [],
        "cold_terms": ["artist_meta_for_sale_works"],
        "performance_key": "활동량/판매 노출",
        "interpretation": "Cold SHAP 상위 피처로, 판매 시장에 노출된 작품 수가 신규 작가의 시장성 또는 거래 가능성을 보완하는 신호로 작동한다.",
        "caution": "판매 노출이 많다는 사실이 항상 가격 상승을 뜻하지는 않는다. 총 작품 수, 팔로워, 크기와 함께 해석해야 한다.",
        "grade": "A",
    },
    {
        "feature": "artist_meta_followers",
        "domain": "작가 팔로워/인지도",
        "warm_terms": [],
        "cold_terms": ["artist_meta_followers"],
        "performance_key": "활동량/인지도 + CatBoost",
        "interpretation": "Cold CatBoost에서 중요도 상위에 있으며, 신규 작가의 대체 시장 인지도 신호로 작동한다.",
        "caution": "SHAP 평균 방향이 약하거나 음수일 수 있어 팔로워 수를 선형 가격 프리미엄으로 해석하지 않는다.",
        "grade": "B",
    },
    {
        "feature": "depth_cm / has_depth / is_3d_candidate",
        "domain": "깊이/3D 여부",
        "warm_terms": [],
        "cold_terms": [],
        "performance_key": "깊이/3D",
        "interpretation": "단독 성능 개선은 약하지만, 3D/입체 작품은 일반 2D 작품과 오차 구조가 다를 수 있어 위험 구간 태깅과 후처리 후보로 의미가 있다.",
        "caution": "가격 상승 피처라기보다 모델 오차가 커질 수 있는 조건으로 해석하는 편이 안전하다.",
        "grade": "C",
    },
    {
        "feature": "artist_works_log",
        "domain": "Warm 작가 학습 이력량",
        "warm_terms": ["artist_works_log"],
        "cold_terms": [],
        "performance_key": "작가 학습 작품 수",
        "interpretation": "작가명을 대체할 만큼의 가격 설명력은 없지만, Warm 모델의 신뢰도와 저이력 작가 위험 구간을 판단하는 데 유용하다.",
        "caution": "가격을 직접 올리는 핵심 피처로 해석하지 않고, 예측 안정성/후처리 조건으로 활용한다.",
        "grade": "C",
    },
    {
        "feature": "artwork_age / 제작연도",
        "domain": "제작 시점",
        "warm_terms": [],
        "cold_terms": [],
        "performance_key": "제작연도/작품 연한",
        "interpretation": "현재 실험에서는 단독 또는 추가 효과가 제한적이다. 운영 입력값으로 받을 수 있으면 보조 후보로 유지한다.",
        "caution": "작가 경력, 작품 시리즈, 재료와 결합하지 않으면 해석력이 약하다.",
        "grade": "C",
    },
    {
        "feature": "edition",
        "domain": "에디션 여부",
        "warm_terms": [],
        "cold_terms": [],
        "performance_key": "에디션",
        "interpretation": "현재 결과에서는 핵심 가격 설명 피처로 보기 어렵다. 다만 edition 여부는 작품 유형과 시장 유통 방식의 보조 정보가 될 수 있다.",
        "caution": "단독 영향은 약하므로 최종 핵심 피처로 설명하지 않는다.",
        "grade": "D",
    },
]


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def first_matches(df: pd.DataFrame, col: str, terms: list[str], limit: int = 3) -> pd.DataFrame:
    if df.empty or not terms or col not in df.columns:
        return pd.DataFrame()
    mask = pd.Series(False, index=df.index)
    for term in terms:
        if term.endswith("_"):
            mask |= df[col].astype(str).str.startswith(term)
        else:
            mask |= df[col].astype(str).eq(term)
    return df.loc[mask].head(limit).copy()


def format_warm_evidence(group: dict[str, Any], coef: pd.DataFrame, contrib: pd.DataFrame) -> str:
    rows = []
    contrib_rows = first_matches(contrib, "feature", group["warm_terms"], 3)
    coef_rows = first_matches(coef, "feature", group["warm_terms"], 3)
    if not contrib_rows.empty:
        parts = [
            f"{r.feature}: 평균|기여| {r.mean_abs_contribution:.4f}, 방향 {r.direction}"
            for r in contrib_rows.itertuples(index=False)
        ]
        rows.append("기여도 " + " / ".join(parts))
    if not coef_rows.empty:
        parts = [
            f"{r.feature}: coef {r.coef:.4f}, {r.direction}"
            for r in coef_rows.itertuples(index=False)
        ]
        rows.append("계수 " + " / ".join(parts))
    return " / ".join(rows) if rows else "직접 계수/기여도 근거 없음 또는 보조 해석 대상"


def format_cold_evidence(group: dict[str, Any], shap: pd.DataFrame, importance: pd.DataFrame) -> str:
    rows = []
    shap_rows = first_matches(shap, "feature", group["cold_terms"], 3)
    imp_rows = first_matches(importance, "feature", group["cold_terms"], 3)
    if not shap_rows.empty:
        parts = [
            f"{r.feature}: mean|SHAP| {r.mean_abs_shap:.4f}, 방향 {r.direction}"
            for r in shap_rows.itertuples(index=False)
        ]
        rows.append("SHAP " + " / ".join(parts))
    if not imp_rows.empty:
        parts = [f"{r.feature}: importance {r.importance:.4f}, rank {int(r.rank)}" for r in imp_rows.itertuples(index=False)]
        rows.append("중요도 " + " / ".join(parts))
    return " / ".join(rows) if rows else "직접 SHAP/importance 근거 없음 또는 보조 해석 대상"


def performance_evidence(group: dict[str, Any], perf: pd.DataFrame) -> str:
    if perf.empty:
        return "성능 요약 파일 없음"
    key = group["performance_key"]
    row = perf.loc[perf["피처/효과"].astype(str).eq(key)]
    if row.empty:
        return "직접 매칭되는 성능 요약 없음"
    r = row.iloc[0]
    warm = clean_cell(r.get("Warm 판정", ""))
    cold = clean_cell(r.get("Cold 판정", ""))
    comp = clean_cell(r.get("최고 개선 비교", ""))
    final = clean_cell(r.get("최종 판단", ""))
    return f"성능 판정 Warm={warm or '-'}, Cold={cold or '-'} / 최고 비교: {comp} / 판단: {final}"


def clean_cell(value: Any) -> str:
    if pd.isna(value):
        return "-"
    return str(value).strip() or "-"


def row_for_group(group: dict[str, Any], coef: pd.DataFrame, contrib: pd.DataFrame, shap: pd.DataFrame, importance: pd.DataFrame, perf: pd.DataFrame) -> dict[str, str]:
    return {
        "피처": group["feature"],
        "도메인 의미": group["domain"],
        "성능 근거": performance_evidence(group, perf),
        "Warm Huber 내부 근거": format_warm_evidence(group, coef, contrib),
        "Cold CatBoost 내부 근거": format_cold_evidence(group, shap, importance),
        "해석": group["interpretation"],
        "주의점": group["caution"],
        "해석 등급": group["grade"],
    }


def esc(value: Any) -> str:
    return html.escape(str(value))


def table_html(df: pd.DataFrame) -> str:
    header = "".join(f"<th>{esc(col)}</th>" for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{esc(row[col])}</td>" for col in df.columns)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def table_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row[col]).replace("\n", " ").replace("|", "\\|") for col in cols]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_markdown(df: pd.DataFrame) -> None:
    lines = [
        "# Track6 모델별 개별 피처 영향 해석",
        "",
        f"- 작성일: `{date.today().isoformat()}`",
        "- 목적: 단순히 성능이 오른 피처가 아니라, 각 모델 내부에서 해당 피처가 왜 영향력을 가지는지 해석한다.",
        "- 해석 순서: 개별 피처 해석 → 모델별 차이 확인 → 피처 조합 해석으로 확장.",
        "",
        "## 해석 기준",
        "",
        "| 모델 | 해석 기준 | 의미 |",
        "|---|---|---|",
        "| Warm Huber | 계수, 입력값 × 계수 | 피처가 로그 가격을 올리거나 낮추는 방향과 평균 기여도 |",
        "| Cold CatBoost | feature importance, SHAP | 모델이 해당 피처를 사용한 정도와 개별 예측 기여 방향 |",
        "| Cold LightGBM | 추가 필요 | 현재 동일 수준의 해석 산출물이 없어 별도 생성 필요 |",
        "",
        "## 개별 피처 해석표",
        "",
        table_markdown(df),
        "",
        "## 다음 단계",
        "",
        "- 개별 피처 해석 등급 A/B 피처를 중심으로 조합 해석을 진행한다.",
        "- Warm은 `artist_key + 크기`, `artist_key + 크기 + 재료/지지체` 순서로 해석한다.",
        "- Cold는 `크기 + 작가 메타`, `크기 + 재료/지지체`, `시장 노출 + 크기` 순서로 해석한다.",
        "- LightGBM은 SHAP 또는 permutation importance 산출 후 동일 표에 추가한다.",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_html(df: pd.DataFrame) -> None:
    content = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Track6 모델별 개별 피처 영향 해석</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 28px; color: #1f2933; }}
    h1 {{ margin-bottom: 6px; }}
    h2 {{ margin-top: 28px; border-bottom: 1px solid #d9e2ec; padding-bottom: 6px; }}
    p, li {{ line-height: 1.55; }}
    table {{ border-collapse: collapse; width: 100%; margin: 14px 0 24px; font-size: 13px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #f0f4f8; text-align: left; }}
    tr:nth-child(even) td {{ background: #fbfcfd; }}
    .note {{ background: #f7f9fb; border-left: 4px solid #486581; padding: 12px 14px; margin: 14px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #d9e2ec; padding: 12px; }}
    code {{ background: #f0f4f8; padding: 1px 4px; }}
  </style>
</head>
<body>
  <h1>Track6 모델별 개별 피처 영향 해석</h1>
  <p>작성일: <code>{date.today().isoformat()}</code></p>
  <div class="note">
    <p>이 문서는 성능이 오른 피처 목록이 아니라, 각 모델 내부에서 피처가 왜 영향력을 가지는지 설명하기 위한 1차 해석표입니다. 피처 조합 해석은 이 표에서 근거가 강한 피처를 중심으로 확장합니다.</p>
  </div>

  <h2>해석 기준</h2>
  <div class="grid">
    <div class="card"><strong>Warm Huber</strong><br>계수와 입력값×계수로 방향과 평균 기여도를 해석합니다.</div>
    <div class="card"><strong>Cold CatBoost</strong><br>feature importance와 SHAP으로 사용 정도와 예측 기여 방향을 해석합니다.</div>
    <div class="card"><strong>Cold LightGBM</strong><br>현재 동일 수준 산출물이 없어 SHAP 또는 permutation importance 추가 생성이 필요합니다.</div>
  </div>

  <h2>개별 피처 해석표</h2>
  {table_html(df)}

  <h2>해석 등급 기준</h2>
  <table>
    <thead><tr><th>등급</th><th>기준</th><th>의미</th></tr></thead>
    <tbody>
      <tr><td>A</td><td>성능 근거와 모델 내부 근거가 모두 강함</td><td>핵심 피처로 설명 가능</td></tr>
      <tr><td>B</td><td>성능 또는 내부 근거가 있으나 단독 해석은 제한적</td><td>조합 또는 보조 피처로 설명</td></tr>
      <tr><td>C</td><td>가격 직접 설명보다 위험 구간/신뢰도 판단에 유용</td><td>후처리 조건 또는 안정성 피처</td></tr>
      <tr><td>D</td><td>현재 근거가 약함</td><td>보류 또는 제외 후보</td></tr>
    </tbody>
  </table>

  <h2>다음 단계</h2>
  <ul>
    <li>개별 피처 해석 등급 A/B 피처를 중심으로 조합 해석을 진행합니다.</li>
    <li>Warm은 <code>artist_key + 크기</code>, <code>artist_key + 크기 + 재료/지지체</code> 순서로 해석합니다.</li>
    <li>Cold는 <code>크기 + 작가 메타</code>, <code>크기 + 재료/지지체</code>, <code>시장 노출 + 크기</code> 순서로 해석합니다.</li>
    <li>LightGBM은 SHAP 또는 permutation importance 산출 후 동일 표에 추가합니다.</li>
  </ul>
</body>
</html>
"""
    OUT_HTML.write_text(content, encoding="utf-8")


def main() -> None:
    coef = read_csv(INT_DIR / "warm_huber_numeric_coefficients.csv")
    contrib = read_csv(INT_DIR / "warm_huber_linear_contribution_summary.csv")
    shap = read_csv(INT_DIR / "cold_catboost_shap_summary.csv")
    importance = read_csv(INT_DIR / "cold_catboost_feature_importance.csv")
    perf = read_csv(DOC_DIR / "feature_influence_summary.csv")

    rows = [row_for_group(g, coef, contrib, shap, importance, perf) for g in FEATURE_GROUPS]
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    write_markdown(df)
    write_html(df)
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_HTML}")


if __name__ == "__main__":
    main()
