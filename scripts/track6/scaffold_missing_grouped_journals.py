#!/usr/bin/env python3
"""Create missing Track6 grouped experiment journals.

These journals are plan/blocker records, not experiment execution results.
They make every grouped matrix item traceable to a folder and HTML log.
"""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"


ITEMS = [
    {
        "id": "T6-E101",
        "slug": "low_history_artist_routing",
        "group": "Group C",
        "label": "C10",
        "title": "작가별 학습 작품 수 구간별 라우팅 실험",
        "status": "계획",
        "hypothesis": "학습 작품 수가 적은 작가는 Warm 모델보다 Cold 방식 또는 보수적 fallback이 더 안정적일 수 있다.",
        "purpose": "저이력 작가를 Warm으로 볼지 Cold로 볼지 결정하는 기준을 검증한다.",
        "train_features": "작품 기본 피처 묶음 + artist_works_log 구간",
        "test_features": "Warm test를 작가별 학습 작품 수 구간으로 나누어 평가",
        "models": "Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM",
        "warm": "학습 데이터에 같은 작가가 있는 작품을 작가별 학습 작품 수 1~2개, 3~4개, 5개 이상 등으로 나누어 비교한다.",
        "cold": "Cold 모델을 저이력 Warm 구간에 fallback으로 적용했을 때 median APE와 p95 APE가 줄어드는지 확인한다.",
        "decision": "저이력 구간에서 Cold fallback이 Warm보다 안정적이면 라우팅 정책 후보로 둔다.",
    },
    {
        "id": "T6-E102",
        "slug": "artist_log_area_interaction",
        "group": "Group D",
        "label": "D2",
        "title": "작가명 x 면적 교차항 실험",
        "status": "계획",
        "hypothesis": "같은 면적이라도 작가명에 따라 대형작 가격 프리미엄이 다를 수 있다.",
        "purpose": "작가별 대형작 프리미엄이 존재하는지 확인한다.",
        "train_features": "작품 기본 피처 묶음 + artist_name_ko + artist_name_ko x log_area",
        "test_features": "학습 피처와 동일. Cold에서는 artist_name_ko 교차항 제외",
        "models": "Warm: Huber/Linear/Ridge",
        "warm": "작품 기본 피처 묶음 + 작가명 모델과, 여기에 작가명 x log_area 교차항을 추가한 모델을 비교한다.",
        "cold": "Cold는 작가명이 없으므로 직접 적용하지 않고 Warm 전용 실험으로 기록한다.",
        "decision": "Warm median APE 또는 p95 APE가 줄면 작가별 대형작 효과 후보로 둔다.",
    },
    {
        "id": "T6-E103",
        "slug": "artist_material_interaction",
        "group": "Group D",
        "label": "D3",
        "title": "작가명 x 난트 재료 교차항 실험",
        "status": "계획",
        "hypothesis": "같은 재료라도 특정 작가에게서 가격 프리미엄이 다르게 나타날 수 있다.",
        "purpose": "작가별 특정 재료 프리미엄을 확인한다.",
        "train_features": "작품 기본 피처 묶음 + artist_name_ko + artist_name_ko x nant_material_idx",
        "test_features": "학습 피처와 동일. Cold에서는 artist_name_ko 교차항 제외",
        "models": "Warm: Huber/Linear/Ridge",
        "warm": "작품 기본 피처 묶음 + 작가명 모델과, 작가명 x 난트 재료 교차항 추가 모델을 비교한다.",
        "cold": "Cold는 작가명이 없으므로 직접 적용하지 않고 Warm 전용 실험으로 기록한다.",
        "decision": "성능 개선이 있고 희소 조합에서 p95 APE가 커지지 않으면 후보로 둔다.",
    },
    {
        "id": "T6-E104",
        "slug": "artist_support_interaction",
        "group": "Group D",
        "label": "D4",
        "title": "작가명 x 난트 지지체 교차항 실험",
        "status": "계획",
        "hypothesis": "같은 지지체라도 특정 작가에게서 가격 프리미엄이 다르게 나타날 수 있다.",
        "purpose": "작가별 지지체 프리미엄을 확인한다.",
        "train_features": "작품 기본 피처 묶음 + artist_name_ko + artist_name_ko x nant_support",
        "test_features": "학습 피처와 동일. Cold에서는 artist_name_ko 교차항 제외",
        "models": "Warm: Huber/Linear/Ridge",
        "warm": "작품 기본 피처 묶음 + 작가명 모델과, 작가명 x 난트 지지체 교차항 추가 모델을 비교한다.",
        "cold": "Cold는 작가명이 없으므로 직접 적용하지 않고 Warm 전용 실험으로 기록한다.",
        "decision": "개선이 작거나 희소 조합에서 p95 APE가 커지면 제외한다.",
    },
    {
        "id": "T6-E105",
        "slug": "artist_depth_interaction",
        "group": "Group D",
        "label": "D5",
        "title": "작가명 x 3D/깊이 교차항 실험",
        "status": "계획",
        "hypothesis": "같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다르게 나타날 수 있다.",
        "purpose": "작가별 입체 작품 프리미엄을 확인한다.",
        "train_features": "작품 기본 피처 묶음 + artist_name_ko + artist_name_ko x has_depth/is_3d_candidate",
        "test_features": "학습 피처와 동일. Cold에서는 artist_name_ko 교차항 제외",
        "models": "Warm: Huber/Linear/Ridge",
        "warm": "작가명 x 3D/깊이 교차항 추가 전후를 비교한다.",
        "cold": "Cold는 작가명이 없으므로 직접 적용하지 않고 Warm 전용 실험으로 기록한다.",
        "decision": "3D 작품 수가 충분한 작가 구간에서만 성능을 해석한다.",
    },
    {
        "id": "T6-E106",
        "slug": "artist_meta_missing_flag_check",
        "group": "Group B",
        "label": "B8",
        "title": "작가 메타 결측 여부 변수 영향 확인",
        "status": "계획",
        "hypothesis": "작가 메타 정보가 비어 있는 상태 자체가 예측 오차와 관련 있을 수 있다.",
        "purpose": "메타 값의 효과와 메타 결측 위험을 분리해서 본다.",
        "train_features": "artist_meta_missing_flags + artist_meta_available_count + artist_meta_completeness_score",
        "test_features": "학습 피처와 동일",
        "models": "Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM",
        "warm": "Warm test를 메타 있음/없음 구간으로 나누고 결측 flag 추가 전후를 비교한다.",
        "cold": "Cold test에서도 메타 있음/없음 구간별 median APE, p95 APE를 비교한다.",
        "decision": "결측 flag가 성능을 개선하거나 큰 오차 구간을 설명하면 신뢰도 피처 후보로 둔다.",
    },
    {
        "id": "T6-E107",
        "slug": "log_area_support_interaction",
        "group": "Group D",
        "label": "old-D2",
        "title": "면적 x 난트 지지체 교차항 실험",
        "status": "계획",
        "hypothesis": "같은 면적이라도 지지체가 캔버스인지 종이인지에 따라 가격 효과가 다를 수 있다.",
        "purpose": "큰 캔버스와 큰 종이 작품의 가격 차이를 확인한다.",
        "train_features": "작품 기본 피처 묶음 + log_area x nant_support",
        "test_features": "학습 피처와 동일",
        "models": "Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM",
        "warm": "작품 기본 피처 묶음에 log_area x nant_support 교차항을 추가해 Warm 성능 변화를 확인한다.",
        "cold": "작품 기본 피처 묶음에 log_area x nant_support 교차항을 추가해 Cold 성능 변화를 확인한다.",
        "decision": "Warm/Cold 중 한쪽에서만 개선되면 모델별 피처셋 분리 후보로 둔다.",
    },
    {
        "id": "AX1",
        "slug": "artist_name_normalization_before_after",
        "group": "AX",
        "label": "AX1",
        "title": "작가명 한글화 전/후 비교",
        "status": "계획",
        "hypothesis": "영문/한글 표기 정리가 Warm 성능과 작가 매칭 안정성을 개선할 수 있다.",
        "purpose": "작가명 자체 효과가 아니라 이름 정제 품질을 검증한다.",
        "train_features": "artist_name_ko_orig vs artist_name_ko",
        "test_features": "동일 비교 피처",
        "models": "Warm: Huber/Linear/Ridge",
        "warm": "원본 한글명과 보정 한글명을 각각 사용해 Warm 성능과 매칭 실패 건수를 비교한다.",
        "cold": "Cold는 작가명 자체를 쓰지 않으므로 직접 모델 성능보다 메타 매칭 성공률만 참고한다.",
        "decision": "보정명이 성능 또는 매칭률을 개선하면 정제 파이프라인 유지 근거로 기록한다.",
    },
    {
        "id": "AX2",
        "slug": "homonym_split_before_after",
        "group": "AX",
        "label": "AX2",
        "title": "동명이인 분리 전/후 비교",
        "status": "계획",
        "hypothesis": "동명이인이 섞이면 작가명 피처 성능이 왜곡될 수 있다.",
        "purpose": "작가명 효과가 실제 작가 효과인지 데이터 혼합 효과인지 분리한다.",
        "train_features": "artist_name_ko before/after homonym correction",
        "test_features": "동일 비교 피처",
        "models": "Warm: Huber/Linear/Ridge",
        "warm": "동명이인 분리 전/후 Warm 성능과 같은 이름 내부 가격 분산을 비교한다.",
        "cold": "Cold는 직접 적용하지 않고 신규 작가 매칭 오류 위험으로 기록한다.",
        "decision": "분리 후 p95 APE가 줄면 동명이인 필터를 필수 정제 단계로 둔다.",
    },
    {
        "id": "AX3",
        "slug": "artist_db_match_success_slice",
        "group": "AX",
        "label": "AX3",
        "title": "작가 DB 매칭 성공/실패 구간 비교",
        "status": "계획",
        "hypothesis": "작가 DB 매칭 성공 여부는 예측 오차와 신뢰도 판단에 영향을 줄 수 있다.",
        "purpose": "메타 변수 효과가 아니라 DB 커버리지 리스크를 확인한다.",
        "train_features": "artist_db_match_flag + 작품 기본 피처 묶음",
        "test_features": "학습 피처와 동일",
        "models": "Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM",
        "warm": "DB 매칭 성공/실패 구간별 Warm 오차를 비교한다.",
        "cold": "Cold에서 DB 매칭 성공 작가와 실패 작가의 오차 차이를 비교한다.",
        "decision": "매칭 실패 구간이 큰 오차와 연결되면 신뢰도 경고 후보로 둔다.",
    },
    {
        "id": "AX4",
        "slug": "warm_artist_count_threshold",
        "group": "AX",
        "label": "AX4",
        "title": "작가별 학습 작품 수 기준 변경 실험",
        "status": "계획",
        "hypothesis": "Warm으로 볼 작가의 최소 학습 작품 수 기준에 따라 성능 안정성이 달라질 수 있다.",
        "purpose": "1개, 3개, 5개 이상 기준 중 어떤 Warm 기준이 안정적인지 확인한다.",
        "train_features": "작품 기본 피처 묶음 + artist_name_ko",
        "test_features": "Warm test를 학습 작품 수 기준별로 재구성",
        "models": "Warm: Huber/Linear/Ridge, fallback Cold 모델",
        "warm": "Warm 기준을 1개 이상, 3개 이상, 5개 이상으로 바꿔 평가한다.",
        "cold": "기준 미달 작가에 Cold 모델을 적용해 전체 라우팅 성능을 비교한다.",
        "decision": "전체 median APE와 p95 APE가 동시에 안정적인 기준을 채택한다.",
    },
    {
        "id": "AX5",
        "slug": "low_history_artist_fallback",
        "group": "AX",
        "label": "AX5",
        "title": "저이력 작가 전용 fallback 실험",
        "status": "계획",
        "hypothesis": "학습 작품 수가 적은 작가는 Warm 모델보다 Cold 모델이 더 안정적일 수 있다.",
        "purpose": "Warm/Cold 경계 작가의 모델 선택 정책을 검증한다.",
        "train_features": "작품 기본 피처 묶음 + artist_works_log 구간",
        "test_features": "저이력 Warm slice",
        "models": "Warm 후보 vs Cold 후보",
        "warm": "저이력 Warm slice에 Warm 모델을 적용한 결과를 기준으로 둔다.",
        "cold": "같은 slice에 Cold 모델을 fallback 적용해 오차를 비교한다.",
        "decision": "저이력 slice에서 Cold가 더 안정적이면 fallback 정책 후보로 둔다.",
    },
    {
        "id": "AX6",
        "slug": "artist_meta_missing_pattern_slice",
        "group": "AX",
        "label": "AX6",
        "title": "작가 메타 결측 패턴별 성능 실험",
        "status": "계획",
        "hypothesis": "생년/국적/활동량 정보가 비어 있는 작가군은 예측 오차가 커질 수 있다.",
        "purpose": "메타 값을 넣는 실험이 아니라 결측 자체의 위험도를 확인한다.",
        "train_features": "artist_meta_missing_flags + artist_meta_completeness_score",
        "test_features": "학습 피처와 동일",
        "models": "Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM",
        "warm": "메타 결측 개수별 Warm 오차를 비교한다.",
        "cold": "메타 결측 개수별 Cold 오차를 비교한다.",
        "decision": "결측 구간 오차가 높으면 서비스 신뢰도 경고 후보로 둔다.",
    },
    {
        "id": "AX7",
        "slug": "artist_price_memorization_check",
        "group": "AX",
        "label": "AX7",
        "title": "작가 가격대 과적합 점검",
        "status": "계획",
        "hypothesis": "작가명만으로 좋아진 성능은 작품 정보를 설명한 것이 아니라 가격대를 외운 결과일 수 있다.",
        "purpose": "작가명 효과의 신뢰성을 검증한다.",
        "train_features": "artist_name_ko only vs artist_name_ko + 작품 기본 피처 묶음",
        "test_features": "Random split / GroupKFold by artist 비교",
        "models": "Warm: Huber/Linear/Ridge",
        "warm": "Random split과 GroupKFold by artist 성능 차이를 비교해 작가명 과적합 여부를 확인한다.",
        "cold": "Cold는 작가명 자체를 쓰지 않으므로 직접 적용하지 않는다.",
        "decision": "Random에서만 좋고 GroupKFold에서 무너지면 작가명 과적합 위험으로 기록한다.",
    },
    {
        "id": "AX8",
        "slug": "cold_artist_meta_only_model",
        "group": "AX",
        "label": "AX8",
        "title": "신규 작가 메타만 사용한 Cold 모델 실험",
        "status": "계획",
        "hypothesis": "작가명 없이도 생년/국적/활동량 같은 운영 가능 작가 메타가 Cold 예측을 개선할 수 있다.",
        "purpose": "Cold에서 작가 DB로 얻을 수 있는 메타만의 가치를 확인한다.",
        "train_features": "작품 기본 피처 묶음 + 운영 가능 작가 메타",
        "test_features": "Cold test에서 artist_name_ko 제외, 작가 메타만 사용",
        "models": "Cold: Huber/Quantile-LAD/LightGBM",
        "warm": "Warm에는 참고로 적용하되 최종 판단은 Cold를 우선한다.",
        "cold": "작품 기본 피처 묶음만 쓴 Cold 모델과 작가 메타 추가 Cold 모델을 비교한다.",
        "decision": "Cold median APE 또는 p95 APE가 개선되면 작가 DB 연동 가치로 기록한다.",
    },
    {
        "id": "BLOCK-A4",
        "slug": "artwork_year_column_required",
        "group": "Blocked",
        "label": "A4/A10/A11/C5/D5",
        "title": "제작연도 기반 실험 보류 일지",
        "status": "보류",
        "hypothesis": "제작연도와 작품 나이는 가격 예측에 영향을 줄 수 있다.",
        "purpose": "현재 데이터에 제작연도 명시 컬럼이 없어 실행 전 필요한 데이터 조건을 기록한다.",
        "train_features": "artwork_year 또는 artwork_age 필요",
        "test_features": "동일 컬럼 필요",
        "models": "Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM",
        "warm": "제작연도 컬럼 확보 후 작가명 + 작품 기본 피처 묶음에 제작연도를 추가해 비교한다.",
        "cold": "제작연도 컬럼 확보 후 Cold 작품 기본 피처 묶음에 제작연도를 추가해 비교한다.",
        "decision": "제작연도 컬럼 확보 전까지 실행하지 않고 보류한다.",
    },
]


STYLE = """
:root{--paper:#fffdf7;--ink:#1d251f;--line:#d8cdb8;--muted:#687268;--green:#27684a;--amber:#9b6124}
body{margin:0;color:var(--ink);background:linear-gradient(135deg,#efe7d7,#f8f5ec 48%,#e9f0e7);font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif;line-height:1.62}
main{max-width:1120px;margin:0 auto;padding:32px 22px 72px}
header,section{background:rgba(255,253,247,.96);border:1px solid var(--line);border-radius:24px;padding:26px;margin-top:18px;box-shadow:0 12px 34px rgba(42,34,22,.08)}
h1{margin:0;font-size:40px;letter-spacing:-.055em}h2{margin:0 0 12px;font-size:22px;letter-spacing:-.03em}
ul{margin:8px 0 0;padding-left:21px}code{background:#eee5d4;border-radius:7px;padding:2px 6px;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;background:var(--paper)}th,td{padding:11px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:14px}th{background:#eadfcd}
.badge{display:inline-flex;padding:5px 9px;border-radius:999px;font-size:12px;font-weight:800;margin-right:6px}.planned{background:rgba(155,97,36,.14);color:var(--amber)}.goal{background:rgba(39,104,74,.14);color:var(--green)}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:16px}
"""


def folder(item: dict[str, str]) -> Path:
    return EXP_ROOT / f"{item['id']}_{item['slug']}"


def esc(value: str) -> str:
    return html.escape(value)


def render_html(item: dict[str, str]) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(item['id'])} {esc(item['title'])}</title>
  <style>{STYLE}</style>
</head>
<body>
<main>
  <header>
    <span class="badge planned">{esc(item['status'])}</span><span class="badge goal">{esc(item['group'])} {esc(item['label'])}</span>
    <h1>{esc(item['id'])} {esc(item['title'])}</h1>
    <ul>
      <li>실험군: {esc(item['group'])}</li>
      <li>상사 기준 라벨: {esc(item['label'])}</li>
      <li>생성일: {date.today().isoformat()}</li>
    </ul>
  </header>
  <section>
    <h2>1. 실험 일지</h2>
    <ul>
      <li>가설: {esc(item['hypothesis'])}</li>
      <li>목적: {esc(item['purpose'])}</li>
      <li>테스트 모델: {esc(item['models'])}</li>
      <li>유의미함 기준: 같은 split과 같은 모델군에서 median APE 또는 p95 APE가 낮아지고, Within-30/Within-50이 높아지는지 확인한다.</li>
    </ul>
  </section>
  <section>
    <h2>2. 초기 실험 데이터</h2>
    <ul>
      <li>기준 원천 파일: <code>data/track6/track6_feature_candidates_name_corrected.csv</code></li>
      <li>학습 입력과 정답 가격은 분리해서 생성한다.</li>
      <li>정답 가격은 <code>train_labels.csv</code>, <code>test_warm_labels.csv</code>, <code>test_cold_labels.csv</code>에만 둔다.</li>
      <li>입력 피처와 정답 라벨은 <code>_track6_row_id</code>로 연결한다.</li>
    </ul>
    <div class="table-wrap"><table>
      <tr><th>구분</th><th>내용</th></tr>
      <tr><td>학습 피처</td><td><code>{esc(item['train_features'])}</code></td></tr>
      <tr><td>테스트 피처</td><td><code>{esc(item['test_features'])}</code></td></tr>
      <tr><td>비교 모델군</td><td>{esc(item['models'])}</td></tr>
    </table></div>
  </section>
  <section>
    <h2>3. 초기 실험 테스트: Warm</h2>
    <ul>
      <li>Warm 정의: 학습 데이터에 같은 작가가 있는 작품을 예측하는 상황</li>
      <li>Warm 학습 데이터: <code>data/train_features.csv</code> + <code>data/train_labels.csv</code></li>
      <li>Warm 테스트 데이터: <code>data/test_warm_features.csv</code> + <code>data/test_warm_labels.csv</code></li>
      <li>{esc(item['warm'])}</li>
    </ul>
  </section>
  <section>
    <h2>4. 초기 실험 테스트: Cold</h2>
    <ul>
      <li>Cold 정의: 학습 데이터에 한 번도 등장하지 않은 작가의 작품을 예측하는 상황</li>
      <li>Cold 학습 데이터: <code>data/train_features.csv</code> + <code>data/train_labels.csv</code></li>
      <li>Cold 테스트 데이터: <code>data/test_cold_features.csv</code> + <code>data/test_cold_labels.csv</code></li>
      <li>{esc(item['cold'])}</li>
    </ul>
  </section>
  <section>
    <h2>5. 결과 기록</h2>
    <ul>
      <li>주요 지표: median APE, p95 APE, Within-30, Within-50</li>
      <li>결과 파일: <code>outputs/metrics.csv</code></li>
      <li>예측 비교 파일: <code>outputs/predictions.csv</code></li>
      <li>구간별 오차 파일: <code>outputs/slice_metrics.csv</code></li>
      <li>요약 파일: <code>outputs/summary.md</code></li>
      <li>실행 로그: <code>logs/run.log</code></li>
    </ul>
  </section>
  <section>
    <h2>6. 판단 기준</h2>
    <ul>
      <li>{esc(item['decision'])}</li>
      <li>성능이 좋아도 운영에서 만들 수 없는 피처는 최종 후보에서 제외하거나 보류한다.</li>
      <li>Warm과 Cold 결과는 합치지 않고 따로 판단한다.</li>
    </ul>
  </section>
</main>
</body>
</html>
"""


def render_readme(item: dict[str, str]) -> str:
    return f"""# {item['id']} {item['title']}

- 상태: {item['status']}
- 실험군: {item['group']}
- 상사 기준 라벨: {item['label']}
- 가설: {item['hypothesis']}
- 목적: {item['purpose']}
- 학습 피처: `{item['train_features']}`
- 테스트 피처: `{item['test_features']}`
- 모델: {item['models']}
- HTML 일지: `experiment_log.html`
"""


def render_config(item: dict[str, str]) -> str:
    return f"""experiment_id: {item['id']}
status: {item['status']}
group: {item['group']}
label: {item['label']}
title: {item['title']}
hypothesis: {item['hypothesis']}
purpose: {item['purpose']}
train_features: {item['train_features']}
test_features: {item['test_features']}
models: {item['models']}
decision: {item['decision']}
"""


def main() -> int:
    for item in ITEMS:
        base = folder(item)
        for sub in ["data", "scripts", "outputs", "logs"]:
            (base / sub).mkdir(parents=True, exist_ok=True)
        (base / "experiment_log.html").write_text(render_html(item), encoding="utf-8")
        (base / "README.md").write_text(render_readme(item), encoding="utf-8")
        (base / "experiment_config.yaml").write_text(render_config(item), encoding="utf-8")
    print(f"created_or_updated={len(ITEMS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
