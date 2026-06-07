#!/usr/bin/env python3
"""Generate one combined model interpretability HTML report for Track6."""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DOC_DIR = REPO / "docs" / "track6" / "experiments"
WARM_OUT = REPO / "experiments" / "track6" / "WARM_HUBER_interpretability_audit" / "outputs"
COLD_OUT = REPO / "experiments" / "track6" / "COLD_models_interpretability_audit" / "outputs"
OUT_HTML = DOC_DIR / "model_interpretability_combined_report.html"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame({"message": [f"missing: {path.relative_to(REPO)}"]})
    return pd.read_csv(path)


def fmt_value(value: object) -> str:
    if pd.isna(value):
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def table_html(df: pd.DataFrame, max_rows: int | None = None, columns: list[str] | None = None) -> str:
    if df.empty:
        return '<p class="empty">데이터 없음</p>'
    view = df.copy()
    if columns:
        view = view[[col for col in columns if col in view.columns]]
    if max_rows is not None:
        view = view.head(max_rows)
    head = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    body_rows = []
    for row in view.itertuples(index=False):
        cells = "".join(f"<td>{html.escape(fmt_value(value))}</td>" for value in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def metric_cards(warm_metrics: pd.DataFrame, cold_metrics: pd.DataFrame) -> str:
    cards = []
    if not warm_metrics.empty:
        warm_test = warm_metrics.loc[warm_metrics["split"].astype(str).eq("test_warm")]
        if not warm_test.empty:
            row = warm_test.iloc[0]
            cards.append(card("Warm Huber", "base_existing_combo + artist_key", row))
    for model, feature_set in [("cold_catboost", "base_medium_shape"), ("cold_lightgbm", "base_support_size")]:
        row_df = cold_metrics.loc[cold_metrics["model"].astype(str).eq(model)] if "model" in cold_metrics else pd.DataFrame()
        if not row_df.empty:
            cards.append(card(model.replace("_", " ").title(), feature_set, row_df.iloc[0]))
    return '<div class="cards">' + "".join(cards) + "</div>"


def card(title: str, subtitle: str, row: pd.Series) -> str:
    return f"""
    <section class="card">
      <h3>{html.escape(title)}</h3>
      <p class="sub">{html.escape(subtitle)}</p>
      <dl>
        <dt>MdAPE</dt><dd>{fmt_value(row.get('MdAPE'))}</dd>
        <dt>p95_APE</dt><dd>{fmt_value(row.get('p95_APE'))}</dd>
        <dt>RMSE_log</dt><dd>{fmt_value(row.get('RMSE_log'))}</dd>
        <dt>Within_30</dt><dd>{fmt_value(row.get('Within_30'))}</dd>
      </dl>
    </section>
    """


def section(title: str, body: str, note: str | None = None) -> str:
    note_html = f'<p class="note">{html.escape(note)}</p>' if note else ""
    return f"<section><h2>{html.escape(title)}</h2>{note_html}{body}</section>"


def commentary_table(rows: list[dict[str, str]]) -> str:
    return table_html(pd.DataFrame(rows))


def model_commentary() -> str:
    return commentary_table(
        [
            {
                "모델": "Warm Huber",
                "현재 설명": "선형 HuberRegressor이므로 최종 예측은 각 피처값에 계수를 곱한 값을 더해 로그 가격을 만드는 구조다. 일반 선형 회귀와 달리 Huber 손실은 큰 오차 샘플을 제곱 손실로 계속 강하게 따라가지 않고, 일정 기준을 넘으면 선형 손실로 처리해 이상치의 학습 영향력을 줄인다. 현재 최종 artifact 기준으로는 size 그룹이 가장 큰 실제 기여도를 보이고, medium/support 조합과 artist_key가 그 다음 설명 축이다.",
                "알기 쉬운 설명": "Warm Huber는 가격을 계산할 때 '작품이 얼마나 큰가', '어떤 재료와 지지체인가', '이미 학습 데이터에 있던 작가인가'를 각각 점수처럼 더해서 최종 가격을 만든다고 보면 된다. 단, 너무 특이하게 비싸거나 싼 작품 하나에 모델이 과하게 끌려가지 않도록 조심스럽게 학습하는 방식이다. 그래서 피처별로 어떤 항목이 가격을 올리는 쪽인지, 낮추는 쪽인지 비교적 직접 설명할 수 있다.",
                "주의점": "숫자형 피처는 표준화 후 들어가므로 원 단위 환산 계수를 같이 봐야 한다. 범주형 one-hot 원계수는 기준 범주와 공선성 때문에 과대 해석될 수 있어 centered contribution 기준으로 설명해야 한다. outlier 비율이 높으므로 큰 오차 구간은 별도 slice로 봐야 한다.",
                "후처리 연결": "전체적으로 예측이 높거나 낮게 치우친 경우에는 global median residual 보정이 자연스럽다. 특정 재료/지지체/작가 이력 구간에서 반복 오차가 보이면 group residual 보정이 적합하다. epsilon 변경은 수렴 여부와 p95 안정성을 확인한 뒤 별도 실험으로 판단한다.",
            },
            {
                "모델": "Cold CatBoost",
                "현재 설명": "CatBoost는 대칭 트리, 즉 Oblivious Tree 구조를 사용한다. 같은 depth의 모든 노드가 동일한 split 조건을 공유하기 때문에, 단순히 한 피처의 중요도만 보는 것보다 어떤 피처 조합이 반복적으로 가격 구간을 나누는지 보는 것이 중요하다. 최종 CatBoost에서는 크기 피처가 가격대를 먼저 나누고, depth_cm과 medium/support/shape 조합이 세부 구간을 조정한다. interaction 상위에 width_cm × depth_cm, height_cm × depth_cm, depth_cm × medium_category가 반복적으로 나타난다.",
                "알기 쉬운 설명": "Cold CatBoost는 처음 보는 작가의 작품을 볼 때, 먼저 작품 크기로 대략적인 가격대를 나누고, 그 다음 '깊이가 있는가', '어떤 재료인가', '어떤 형태인가'를 조합해서 더 세밀하게 판단하는 모델이다. 예를 들어 같은 크기라도 깊이가 있는 작품인지, 캔버스인지, 특정 재료인지에 따라 다른 길로 분기해서 가격을 다르게 본다.",
                "주의점": "feature importance 순위만으로 '이 피처 하나가 가격을 올린다'고 단정하면 안 된다. CatBoost에서는 피처 조합과 leaf segment가 중요하다. leaf pattern은 세분화가 강해 coverage가 낮으므로, leaf 단독 보정은 과적합 위험이 있다.",
                "후처리 연결": "CatBoost에는 전체 보정보다 leaf/segment residual 보정이 구조적으로 맞다. 다만 leaf pattern coverage가 낮기 때문에 leaf pattern → medium_shape_bucket → shape/medium → overall residual 순서의 fallback 보정이 필요하다.",
            },
            {
                "모델": "Cold LightGBM",
                "현재 설명": "LightGBM은 leaf-wise 방식으로 트리를 성장시킨다. 손실을 크게 줄일 수 있는 leaf를 우선적으로 깊게 확장하기 때문에 평균 성능은 좋아질 수 있지만, 일부 좁은 구간에서 오차가 크게 튀는 tail risk가 생길 수 있다. 현재 최종 LightGBM은 area_cm2 permutation 영향이 매우 크고, MdAPE는 CatBoost와 비슷하지만 p95_APE가 더 높다. 이는 대표 오차보다 큰 오차 구간 관리가 더 중요하다는 뜻이다.",
                "알기 쉬운 설명": "Cold LightGBM은 가격을 맞추기 위해 특정 조건을 아주 세밀하게 파고드는 모델이다. 그래서 보통 수준의 예측은 CatBoost와 비슷하게 할 수 있지만, 특정 크기나 지지체 조합에서는 크게 틀릴 가능성이 더 크다. 특히 면적 정보에 많이 의존하고 있어서, 큰 캔버스 작품 같은 구간에서 예측이 흔들릴 수 있다.",
                "주의점": "split importance는 모델이 자주 사용한 피처를 보여줄 뿐, 그 피처를 흔들었을 때 실제 오차가 얼마나 커지는지는 permutation으로 확인해야 한다. LightGBM은 leaf 단위가 복잡하므로 비전공자 설명이나 운영 보정 기준으로 leaf 자체를 직접 쓰기 어렵다.",
                "후처리 연결": "LightGBM은 leaf pattern 보정보다 pred_log bin, size_bucket, support_size_bucket 기반 tail 안정화가 적합하다. 특히 canvas__q5, acrylic, q3 같은 p95가 큰 구간은 가격 범위/신뢰도 표시와 보정 우선 후보로 둔다.",
            },
        ]
    )


def warm_feature_commentary() -> str:
    return commentary_table(
        [
            {
                "피처/그룹": "size: log_area, width_cm, height_cm, area_cm2",
                "현재 설명": "작품 크기는 미술품 가격 산정에서 가장 기본적인 물리량이다. Huber 계수와 실제 기여도 모두 크기 계열이 최상위다. log_area, width_cm, height_cm은 예측 로그가격을 올리는 방향이고, area_cm2는 다른 크기 피처와 함께 들어가면서 보정적 음의 방향을 보인다.",
                "알기 쉬운 설명": "작품이 클수록 대체로 가격이 높아지는 경향이 있기 때문에, 모델도 크기를 가장 먼저 본다. 다만 모델은 단순히 '면적이 크면 무조건 비싸다'로 보지 않고, 가로·세로·면적·로그면적을 함께 보면서 적정 가격대를 맞춘다.",
                "주의점": "크기 피처끼리 중복 정보가 많다. area_cm2 음의 계수는 면적이 가격을 낮춘다는 뜻이 아니라, log_area/width/height를 같이 통제한 뒤의 잔여 조정으로 봐야 한다.",
                "후처리 활용": "크기 구간별 residual을 확인하되, 개별 크기 계수보다 size 그룹 단위로 해석한다.",
            },
            {
                "피처/그룹": "medium_support_bucket",
                "현재 설명": "같은 크기라도 재료와 지지체 조합에 따라 시장 가격대가 달라진다. mixed_media__canvas, acrylic__canvas, oil__canvas 등 조합별 centered contribution 차이가 확인된다.",
                "알기 쉬운 설명": "같은 크기의 작품이라도 캔버스에 그린 유화인지, 종이에 그린 혼합재료인지에 따라 시장에서 받아들이는 가격대가 다를 수 있다. 이 피처는 재료와 바탕재의 조합 차이를 모델이 기억하도록 만든 것이다.",
                "주의점": "조합 카테고리는 희소한 값이 있을 수 있어 표본 수와 active_rate를 같이 봐야 한다.",
                "후처리 활용": "Warm 보정에서 medium/support 조합별 residual 보정 후보로 사용할 수 있다.",
            },
            {
                "피처/그룹": "support_category",
                "현재 설명": "캔버스, 종이, 패널, 린넨 등 지지체는 작품 유형과 보존/시장 인식을 반영한다. canvas와 unknown은 상승 방향, paper/linen/fabric은 상대적으로 하락 방향으로 나타난다.",
                "알기 쉬운 설명": "작품이 어떤 바탕 위에 만들어졌는지도 가격 판단에 영향을 준다. 예를 들어 캔버스 작품과 종이 작품은 같은 크기라도 시장에서 다르게 평가될 수 있어서, 모델이 이 차이를 가격 판단에 반영한다.",
                "주의점": "지지체 자체가 가격의 인과 요인이라고 단정하지 않는다. 재료/크기/작가 효과와 함께 나타난 평균적 패턴이다.",
                "후처리 활용": "support별 잔차가 반복되면 group residual 보정 대상으로 삼는다.",
            },
            {
                "피처/그룹": "medium_category",
                "현재 설명": "재료는 작품의 제작 방식과 시장 분류를 반영한다. mixed_media, painting_material, textile 등은 상승 방향, acrylic/oil/print 등은 상대적으로 하락 방향으로 나타난다.",
                "알기 쉬운 설명": "작품이 유화인지, 아크릴인지, 혼합재료인지 같은 정보다. 모델은 이 재료 정보를 통해 비슷한 크기의 작품들 사이에서도 어떤 종류가 더 높은 가격대로 형성되는지 참고한다.",
                "주의점": "재료 카테고리는 작가/작품 유형과 섞여 있어 단독 가격 프리미엄으로 해석하면 안 된다.",
                "후처리 활용": "재료별 반복 오차가 있으면 medium/support 조합 기준 보정이 더 적합하다.",
            },
            {
                "피처/그룹": "artist_key",
                "현재 설명": "Warm은 학습 데이터에 같은 작가가 있는 조건이므로 작가 식별값이 과거 가격 수준을 반영한다. 개별 artist_key 계수는 해당 작가의 평균적 가격 수준 보정에 가깝다.",
                "알기 쉬운 설명": "이미 데이터에 등장했던 작가라면, 모델은 그 작가의 기존 가격대 정보를 어느 정도 알고 있다. 그래서 Warm 모델에서는 작가 식별값이 '이 작가는 보통 어느 가격대였는가'를 알려주는 중요한 단서가 된다.",
                "주의점": "작가가 가격을 인과적으로 올린다는 뜻이 아니라, 해당 작가의 과거 거래/등록 가격 패턴이 반영된 것이다.",
                "후처리 활용": "저이력 작가, infrequent artist 그룹은 신뢰도 경고나 별도 residual 점검 대상이다.",
            },
        ]
    )


def catboost_feature_commentary() -> str:
    return commentary_table(
        [
            {
                "피처/조합": "width_cm, area_cm2, log_area, height_cm",
                "현재 설명": "Cold에는 작가 이력이 없으므로 작품 자체의 물리 크기가 가격대를 나누는 핵심 축이 된다. SHAP 상위 1~4위가 모두 크기 계열이다. 대칭 트리에서 반복 split으로 가격 구간을 먼저 나누는 역할을 한다.",
                "알기 쉬운 설명": "처음 보는 작가의 작품은 작가의 과거 가격대를 알 수 없기 때문에, 모델은 먼저 작품 크기를 강하게 참고한다. 큰 작품인지 작은 작품인지가 대략적인 가격대를 나누는 첫 기준이 된다.",
                "주의점": "크기 피처가 많아 서로 대체/보완 관계가 있다. 단일 피처 중요도보다 size 그룹으로 봐야 한다.",
                "보정 연결": "대형/중형/소형 구간별 residual, pred_log bin 보정 후보가 된다.",
            },
            {
                "피처/조합": "depth_cm",
                "현재 설명": "깊이는 입체성, 오브제성, 설치/조각 가능성을 반영한다. importance 1위이며 interaction 상위 대부분에 포함된다. 단독 가격 영향보다 크기/형태/재료와 같이 작동한다.",
                "알기 쉬운 설명": "깊이가 있다는 것은 평면 작품이 아니라 입체적이거나 오브제 성격을 가질 가능성이 있다는 뜻이다. 모델은 깊이를 보고 작품의 종류가 달라질 수 있다고 판단하며, 크기나 재료와 함께 가격대를 다시 나눈다.",
                "주의점": "depth_cm이 높다고 항상 비싸다는 뜻은 아니다. 3D 여부, 지지체, 재료와 결합된 조건으로 해석해야 한다.",
                "보정 연결": "depth 관련 leaf segment에서 오차가 반복되면 leaf 또는 medium_shape fallback 보정이 적합하다.",
            },
            {
                "피처/조합": "width_cm × depth_cm",
                "현재 설명": "넓이와 깊이가 함께 커지는 작품은 일반 2D 작품과 다른 가격 구조를 가질 수 있다. interaction score 1위다. CatBoost 대칭 트리가 크기와 깊이 조건을 함께 사용해 segment를 나눈다.",
                "알기 쉬운 설명": "가로로 큰데 깊이까지 있는 작품은 단순히 큰 평면 작품과 다르게 취급될 수 있다. 모델은 '넓고 깊은 작품'이라는 조합을 별도 가격 판단 단서로 보고 있다.",
                "주의점": "상호작용은 두 피처가 각각 독립적으로 가격을 올린다는 뜻이 아니라, 특정 조합에서 모델 판단이 달라진다는 뜻이다.",
                "보정 연결": "CatBoost 보정은 이 조합이 반영된 leaf pattern 또는 size/depth slice를 우선 확인한다.",
            },
            {
                "피처/조합": "depth_cm × medium_category",
                "현재 설명": "입체성의 가격 의미는 재료에 따라 달라진다. interaction score 상위권이다. 재료 단독보다 깊이와 결합될 때 가격 구간 분화가 커진다.",
                "알기 쉬운 설명": "같이 깊이가 있는 작품이라도 어떤 재료로 만들어졌는지에 따라 시장에서 다르게 평가될 수 있다. 모델은 깊이와 재료를 따로따로 보는 것이 아니라, 조합으로 가격 판단에 사용한다.",
                "주의점": "medium_category 단독 중요도가 낮아도 interaction 안에서는 의미가 있을 수 있다.",
                "보정 연결": "medium_shape_bucket 또는 medium/depth segment residual 보정 근거가 된다.",
            },
            {
                "피처/조합": "support_category",
                "현재 설명": "지지체는 작품 제작 방식과 시장 분류의 보조 신호다. SHAP과 importance에서 중위권이며, depth/size interaction과 함께 쓰인다.",
                "알기 쉬운 설명": "캔버스인지, 종이인지, 금속인지 같은 바탕재 정보다. CatBoost는 이 정보를 단독으로 크게 보기보다 크기, 깊이, 재료와 함께 참고해서 세부 가격대를 조정한다.",
                "주의점": "지지체 단독 효과는 강하지 않다. 크기와 재료 조건을 같이 봐야 한다.",
                "보정 연결": "support별 p95가 반복되면 segment fallback 기준으로 사용한다.",
            },
        ]
    )


def lightgbm_feature_commentary() -> str:
    return commentary_table(
        [
            {
                "피처/구간": "area_cm2",
                "현재 설명": "면적은 가격대 분리에 직접적인 크기 정보다. permutation 시 MdAPE delta +0.2542, p95 delta +7.5139로 가장 민감하다. leaf-wise 구조에서 area_cm2가 일부 leaf를 강하게 분화시킨다.",
                "알기 쉬운 설명": "LightGBM은 면적 정보를 매우 강하게 보고 있다. 면적 값을 일부러 섞어버리면 예측 오차가 크게 나빠지므로, 이 모델은 작품의 넓이를 가격 판단의 핵심 기준으로 쓰고 있다고 볼 수 있다.",
                "주의점": "width/height/log_area와 중복되어 tail에서 과민하게 작동할 수 있다.",
                "보정 연결": "크기 파생 피처 ablation과 size_bucket/pred_bin tail 보정이 필요하다.",
            },
            {
                "피처/구간": "width_cm, height_cm, log_area",
                "현재 설명": "면적과 함께 작품 크기의 여러 표현을 제공한다. split importance와 permutation에서 모두 상위권이다. 모델이 크기 정보를 여러 경로로 반복 사용한다.",
                "알기 쉬운 설명": "모델은 면적 하나만 보지 않고 가로, 세로, 로그 크기까지 같이 본다. 같은 면적이라도 가로로 긴 작품인지 세로로 긴 작품인지에 따라 가격 판단이 달라질 수 있기 때문이다.",
                "주의점": "중복 피처가 많으면 일부 leaf에서 과분화가 생길 수 있다.",
                "보정 연결": "크기 피처를 줄인 ablation과 tail slice 비교가 필요하다.",
            },
            {
                "피처/구간": "support_size_bucket: canvas__q5",
                "현재 설명": "캔버스 대형 구간은 Cold에서 가격 편차가 큰 대표 slice다. tail slice에서 p95_APE가 26.43으로 가장 높다. 평균 성능보다 큰 오차 위험이 중요하다.",
                "알기 쉬운 설명": "큰 캔버스 작품 구간은 가격 차이가 매우 크게 벌어지는 구간이다. 어떤 작품은 비슷해 보여도 실제 가격이 크게 다를 수 있어서, LightGBM이 이 구간에서 크게 틀릴 가능성이 높다.",
                "주의점": "이 구간은 표본 수가 충분하지만 가격 분산이 크므로 단일 점예측만으로 설명이 어렵다.",
                "보정 연결": "가격 범위/신뢰도 표시, p95 안정화 보정 우선 후보다.",
            },
            {
                "피처/구간": "medium_category: acrylic",
                "현재 설명": "acrylic은 표본이 많고 가격대 편차가 커 tail risk가 나타난다. tail slice p95_APE가 10.50으로 높다. medium 자체보다 size/support와 결합해 봐야 한다.",
                "알기 쉬운 설명": "아크릴 작품은 데이터가 많지만 가격대가 고르게 모여 있지 않고 넓게 퍼져 있는 것으로 보인다. 그래서 단순히 '아크릴이면 이 정도 가격'으로 맞추기 어렵고, 크기나 지지체와 함께 봐야 한다.",
                "주의점": "acrylic 전체가 위험하다는 뜻이 아니라 특정 크기/지지체 조합에서 오차가 커질 수 있다는 뜻이다.",
                "보정 연결": "medium × size 또는 support_size_bucket 기준 후처리 후보로 사용한다.",
            },
            {
                "피처/구간": "leaf-wise worst leaf",
                "현재 설명": "LightGBM은 손실을 줄이는 leaf를 깊게 확장하므로 일부 leaf에 큰 오차가 몰릴 수 있다. worst leaf MdAPE가 매우 큰 tree들이 확인된다. 이는 p95 tail risk와 연결된다.",
                "알기 쉬운 설명": "LightGBM은 특정 조건을 아주 깊게 파고들어 판단한다. 이 과정에서 일부 좁은 조건 그룹에 큰 오차가 몰릴 수 있는데, 이것이 전체 평균은 괜찮아도 극단적으로 틀리는 사례가 생기는 이유다.",
                "주의점": "leaf 자체는 운영 설명 단위로 복잡하므로 직접 보정보다는 사람이 이해 가능한 bucket으로 내려와야 한다.",
                "보정 연결": "pred_log bin, size_bucket, support_size_bucket으로 tail 안정화한다.",
            },
        ]
    )


def numeric_interpretation_bridge(
    warm_group: pd.DataFrame,
    warm_coef: pd.DataFrame,
    cat_shap: pd.DataFrame,
    cat_interactions: pd.DataFrame,
    lgb_perm: pd.DataFrame,
    lgb_tail: pd.DataFrame,
) -> str:
    rows = [
        {
            "모델": "Warm Huber",
            "확인한 수치": "size 그룹 mean_abs_centered_contribution_sum 1.2222, rank 1",
            "수치 해석": "최종 로그가격을 움직인 실제 평균 기여도 기준으로 size가 가장 크다.",
            "조합 판단": "Warm에서는 size를 단독 피처 하나가 아니라 log_area, width_cm, height_cm, area_cm2 묶음으로 유지하는 것이 타당하다.",
        },
        {
            "모델": "Warm Huber",
            "확인한 수치": "medium_support 0.5625 rank 2, support 0.5121 rank 3",
            "수치 해석": "크기 다음으로 재료/지지체 조합과 지지체가 가격 차이를 설명한다.",
            "조합 판단": "size만으로 설명되지 않는 잔여 가격 차이는 medium_support_bucket, support_category를 함께 봐야 한다.",
        },
        {
            "모델": "Warm Huber",
            "확인한 수치": "log_area, height_cm, width_cm이 centered contribution 상위 1~3위",
            "수치 해석": "계수 크기만이 아니라 실제 데이터에서 자주 가격을 움직인 피처도 크기 계열이다.",
            "조합 판단": "계수표 해석은 개별 계수 순위보다 size 그룹 기여도와 샘플별 contribution을 같이 보는 방식이 맞다.",
        },
        {
            "모델": "Cold CatBoost",
            "확인한 수치": "width_cm SHAP 0.2629 rank 1, area_cm2 0.2217 rank 2, log_area 0.1974 rank 3",
            "수치 해석": "처음 보는 작가에서는 작품 크기가 예측값을 가장 많이 흔든다.",
            "조합 판단": "Cold CatBoost의 기본 조합은 size 피처를 중심에 두고 시작하는 것이 맞다.",
        },
        {
            "모델": "Cold CatBoost",
            "확인한 수치": "width_cm × depth_cm interaction 5.5493 rank 1, height_cm × depth_cm 5.2242 rank 2",
            "수치 해석": "CatBoost는 크기와 깊이를 따로만 보지 않고 조합 조건으로 가격 구간을 나눈다.",
            "조합 판단": "CatBoost에서는 size + depth_3d 조합이 좋은 후보이며, leaf/segment 보정도 이 조합을 우선 확인해야 한다.",
        },
        {
            "모델": "Cold CatBoost",
            "확인한 수치": "depth_cm × medium_category interaction 4.8243",
            "수치 해석": "입체성의 가격 의미가 재료에 따라 달라진다.",
            "조합 판단": "depth_cm을 단독으로 해석하기보다 medium_category 또는 medium_shape_bucket과 함께 설명해야 한다.",
        },
        {
            "모델": "Cold LightGBM",
            "확인한 수치": "area_cm2 permutation MdAPE_delta +0.2542, p95_APE_delta +7.5139",
            "수치 해석": "면적 정보를 섞으면 대표 오차와 큰 오차가 동시에 크게 악화된다.",
            "조합 판단": "LightGBM은 area_cm2 의존도가 매우 높으므로 size 관련 피처 조합과 과민 구간 점검이 필요하다.",
        },
        {
            "모델": "Cold LightGBM",
            "확인한 수치": "support_size_bucket=canvas__q5 p95_APE 26.4323",
            "수치 해석": "대형 캔버스 구간은 평균 설명보다 큰 오차 위험이 더 중요하다.",
            "조합 판단": "LightGBM 후처리는 leaf 자체보다 size_bucket, support_size_bucket, pred_log bin으로 tail을 안정화하는 쪽이 맞다.",
        },
    ]

    combo_rows = [
        {
            "후보 조합": "Warm: size + medium_support + artist_key",
            "채택 근거": "size가 기여도 1위이고, medium_support/support가 다음 설명 축이며, Warm은 기존 작가 이력을 사용할 수 있다.",
            "설명 방식": "크기로 기본 가격대를 잡고, 재료/지지체 조합으로 작품 유형 차이를 보정한 뒤, 기존 작가 가격대 정보를 반영한다고 설명한다.",
            "주의점": "artist_key는 신규 작가에는 사용할 수 없으므로 Warm 전용 설명으로 제한한다.",
        },
        {
            "후보 조합": "Cold CatBoost: size + depth_3d + medium/shape",
            "채택 근거": "SHAP 상위는 size이고, interaction 상위는 size × depth, depth × medium/shape 계열이다.",
            "설명 방식": "처음 보는 작가에서는 크기로 큰 가격대를 나누고, 깊이/재료/형태 조합으로 세부 구간을 나눈다고 설명한다.",
            "주의점": "대칭 트리 구조상 단일 피처 효과보다 조합 조건과 leaf segment를 함께 봐야 한다.",
        },
        {
            "후보 조합": "Cold LightGBM: area/size + support_size_bucket + pred_log bin",
            "채택 근거": "area_cm2 permutation 영향이 압도적이고, support_size_bucket tail slice에서 p95가 크게 튄다.",
            "설명 방식": "면적 의존도가 높은 모델이므로 크기 구간과 지지체-크기 구간에서 위험도를 따로 표시한다고 설명한다.",
            "주의점": "leaf-wise 구조는 일부 좁은 구간을 과도하게 파고들 수 있어, 사람이 이해 가능한 bucket으로 내려와야 한다.",
        },
    ]

    rule_rows = [
        {
            "판단 기준": "1. 모델 안에서 실제로 크게 쓰였는가",
            "확인 수치": "Huber contribution, CatBoost SHAP, LightGBM permutation",
            "의미": "성능이 좋아진 피처가 아니라 해당 모델의 예측값을 실제로 움직인 피처인지 확인한다.",
        },
        {
            "판단 기준": "2. 모델 구조와 맞는 조합인가",
            "확인 수치": "Huber 계수/기여도, CatBoost interaction, LightGBM tail/leaf-wise",
            "의미": "같은 피처라도 선형 모델, 대칭 트리, leaf-wise 트리에서 해석 단위가 다르다.",
        },
        {
            "판단 기준": "3. 후처리로 이어질 반복 오차가 있는가",
            "확인 수치": "residual, p95_APE, tail slice, leaf segment",
            "의미": "피처 조합이 설명에서 끝나는 것이 아니라 보정 기준으로 쓸 수 있는지 판단한다.",
        },
    ]

    return (
        '<section id="evidence"><h2>4. 수치 해석과 조합 판단 근거</h2>'
        '<p class="note">이 섹션은 피처별 수치를 어떻게 해석했고, 그 해석이 어떤 피처 조합 판단으로 이어졌는지를 명시한다. '
        '좋은 조합은 단순히 성능이 좋아진 조합이 아니라, 모델 안에서 실제로 예측값을 움직이고 모델 구조와도 맞으며 후처리 기준으로도 쓸 수 있는 조합이다.</p>'
        "<h3>피처별 수치 해석</h3>"
        + table_html(pd.DataFrame(rows))
        + "<h3>조합 후보 판단</h3>"
        + table_html(pd.DataFrame(combo_rows))
        + "<h3>좋은 조합으로 판단하는 기준</h3>"
        + table_html(pd.DataFrame(rule_rows))
        + "</section>"
    )


def main() -> None:
    warm_alignment = read_csv(WARM_OUT / "warm_huber_feature_alignment_audit.csv")
    warm_metrics = read_csv(WARM_OUT / "warm_huber_final_artifact_metrics.csv")
    warm_outlier = read_csv(WARM_OUT / "warm_huber_outlier_diagnostics.csv")
    warm_epsilon = read_csv(WARM_OUT / "warm_huber_epsilon_sensitivity.csv")
    warm_group = read_csv(WARM_OUT / "warm_huber_feature_group_contribution_summary.csv")
    warm_coef = read_csv(WARM_OUT / "warm_huber_final_coefficients_contributions.csv")
    warm_samples = read_csv(WARM_OUT / "warm_huber_sample_explanations.csv")

    cold_alignment = read_csv(COLD_OUT / "cold_feature_alignment_audit.csv")
    cold_metrics = read_csv(COLD_OUT / "cold_final_artifact_metrics.csv")
    cold_group = read_csv(COLD_OUT / "cold_feature_group_interpretation_summary.csv")
    cat_importance = read_csv(COLD_OUT / "cold_catboost_final_feature_importance.csv")
    cat_shap = read_csv(COLD_OUT / "cold_catboost_final_shap_summary.csv")
    cat_interactions = read_csv(COLD_OUT / "cold_catboost_final_interactions.csv")
    cat_structure = read_csv(COLD_OUT / "cold_catboost_structure_summary.csv")
    cat_leaf = read_csv(COLD_OUT / "cold_catboost_leaf_segment_residuals.csv")
    cat_samples = read_csv(COLD_OUT / "cold_catboost_final_sample_shap_explanations.csv")
    lgb_importance = read_csv(COLD_OUT / "cold_lightgbm_final_feature_importance.csv")
    lgb_perm = read_csv(COLD_OUT / "cold_lightgbm_final_permutation_diagnostics.csv")
    lgb_leaf = read_csv(COLD_OUT / "cold_lightgbm_leafwise_diagnostics.csv")
    lgb_tail = read_csv(COLD_OUT / "cold_lightgbm_tail_slice_diagnostics.csv")

    css = """
    :root{--ink:#1f2933;--muted:#5f6c7b;--line:#d9e2ec;--head:#f0f4f8;--note:#f5f7fa;--accent:#486581}
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:32px;color:var(--ink);line-height:1.58;background:#fff}
    h1{font-size:28px;margin:0 0 8px} h2{font-size:21px;margin:32px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
    h3{font-size:16px;margin:0 0 6px}.meta{color:var(--muted);margin-bottom:18px}.note{background:var(--note);border-left:4px solid var(--accent);padding:10px 12px}
    .toc{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;margin:18px 0 26px}.toc a{border:1px solid var(--line);padding:8px 10px;color:var(--ink);text-decoration:none;background:#fbfcfd}
    .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:14px 0}.card{border:1px solid var(--line);padding:14px;background:#fbfcfd}.card .sub{margin:0 0 8px;color:var(--muted)}
    .commentary{background:#fbfcfd;border:1px solid var(--line);padding:14px;margin:12px 0 18px}.commentary h3{margin-top:0}.commentary ul{margin:8px 0 0 20px;padding:0}
    dl{display:grid;grid-template-columns:1fr 1fr;gap:5px 10px;margin:0}dt{color:var(--muted)}dd{margin:0;font-weight:650}
    table{border-collapse:collapse;width:100%;font-size:12.5px;margin:10px 0 24px}th,td{border:1px solid var(--line);padding:7px 8px;vertical-align:top}th{background:var(--head);text-align:left;position:sticky;top:0}
    code{background:var(--head);padding:2px 4px;border-radius:4px}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.empty{color:var(--muted)}
    @media(max-width:900px){body{margin:18px}.two{grid-template-columns:1fr}table{font-size:12px}}
    """

    body = [
        "<h1>Track6 최종 모델 통합 해석 보고서</h1>",
        f'<p class="meta">작성일: <code>{date.today().isoformat()}</code> / 대상: Warm Huber, Cold CatBoost, Cold LightGBM</p>',
        '<nav class="toc">'
        '<a href="#summary">1. 종합 요약</a>'
        '<a href="#alignment">2. 피처셋 감사</a>'
        '<a href="#commentary">3. 모델별 코멘터리</a>'
        '<a href="#evidence">4. 수치 해석/조합 근거</a>'
        '<a href="#warm">5. Warm Huber 상세</a>'
        '<a href="#catboost">6. Cold CatBoost 상세</a>'
        '<a href="#lightgbm">7. Cold LightGBM 상세</a>'
        '<a href="#policy">8. 해석/보정 원칙</a>'
        "</nav>",
        '<section id="summary"><h2>1. 종합 요약</h2>',
        '<p class="note">기존 해석 산출물은 최종 artifact와 피처셋이 달라 최종 모델 설명 자료로 그대로 쓰기 어렵다. 이 보고서는 최종 artifact 기준의 재산출 결과를 한 파일에 통합한 것이다.</p>',
        metric_cards(warm_metrics, cold_metrics),
        table_html(pd.DataFrame(
            [
                {
                    "모델": "Warm Huber",
                    "구조": "선형 HuberRegressor",
                    "해석 우선 기준": "계수, 원 단위 환산 계수, 실제 기여도, outlier 여부",
                    "적합한 보정": "global median residual, group residual",
                },
                {
                    "모델": "Cold CatBoost",
                    "구조": "대칭 트리, Oblivious Tree",
                    "해석 우선 기준": "SHAP, interaction, leaf segment residual",
                    "적합한 보정": "leaf/segment residual + fallback",
                },
                {
                    "모델": "Cold LightGBM",
                    "구조": "leaf-wise gradient boosting tree",
                    "해석 우선 기준": "permutation, tail slice, leaf-wise 진단",
                    "적합한 보정": "pred bin, size/support bucket, tail 안정화",
                },
            ]
        )),
        "</section>",
        '<section id="alignment"><h2>2. 피처셋 일치성 감사</h2>',
        '<p class="note">status 불일치는 최종 artifact 피처와 기존 해석 스크립트 피처가 다르다는 뜻이다. 불일치 피처는 기존 해석 보고서로 설명하면 안 된다.</p>',
        "<h3>Warm Huber</h3>",
        table_html(warm_alignment),
        "<h3>Cold CatBoost / LightGBM</h3>",
        table_html(cold_alignment),
        "</section>",
        '<section id="commentary"><h2>3. 모델별/피처별 코멘터리</h2>',
        '<p class="note">아래 코멘터리는 표의 수치를 사람이 이해할 수 있는 설명으로 바꾼 것이다. 모델별 특성, 상위 피처, 선택 피처의 해석과 후처리 연결을 함께 정리한다.</p>',
        "<h3>모델별 코멘터리</h3>",
        model_commentary(),
        "<h3>Warm Huber 선택 피처 코멘터리</h3>",
        warm_feature_commentary(),
        "<h3>Cold CatBoost 상위/선택 피처 코멘터리</h3>",
        catboost_feature_commentary(),
        "<h3>Cold LightGBM 상위/위험 구간 코멘터리</h3>",
        lightgbm_feature_commentary(),
        "</section>",
        numeric_interpretation_bridge(warm_group, warm_coef, cat_shap, cat_interactions, lgb_perm, lgb_tail),
        '<section id="warm"><h2>5. Warm Huber 상세 해석</h2>',
        '<p class="note">Huber는 선형 모델이므로 직접 계수 해석이 가능하다. 단, 숫자형은 표준화 후 들어가며 범주형 one-hot은 centered contribution 기준으로 봐야 한다.</p>',
        "<h3>성능 재확인</h3>",
        table_html(warm_metrics),
        "<h3>Huber outlier 진단</h3>",
        table_html(warm_outlier),
        "<h3>epsilon 민감도</h3>",
        table_html(warm_epsilon),
        "<h3>피처 그룹별 기여도</h3>",
        table_html(warm_group),
        "<h3>계수/기여도 상위 80개</h3>",
        table_html(
            warm_coef,
            80,
            [
                "encoded_feature",
                "raw_feature",
                "feature_group",
                "coef",
                "centered_coef",
                "original_unit_coef",
                "active_rate",
                "mean_abs_centered_contribution",
                "mean_centered_contribution",
                "rank_by_centered_abs_contribution",
            ],
        ),
        "<h3>샘플별 설명</h3>",
        table_html(warm_samples, 50),
        "</section>",
        '<section id="catboost"><h2>6. Cold CatBoost 상세 해석</h2>',
        '<p class="note">CatBoost는 대칭 트리 구조이므로 단독 중요도만 보지 않고 SHAP, interaction, leaf segment 잔차를 함께 해석한다.</p>',
        "<h3>성능 재확인</h3>",
        table_html(cold_metrics.loc[cold_metrics["model"].astype(str).eq("cold_catboost")] if "model" in cold_metrics else cold_metrics),
        "<h3>대칭 트리 구조 요약</h3>",
        table_html(cat_structure),
        "<h3>Feature Importance</h3>",
        table_html(cat_importance),
        "<h3>SHAP Summary</h3>",
        table_html(cat_shap),
        "<h3>Interaction</h3>",
        table_html(cat_interactions, 45),
        "<h3>Leaf Segment Residual</h3>",
        table_html(cat_leaf, 80),
        "<h3>샘플별 SHAP 설명</h3>",
        table_html(cat_samples, 50),
        "</section>",
        '<section id="lightgbm"><h2>7. Cold LightGBM 상세 해석</h2>',
        '<p class="note">LightGBM은 leaf-wise 구조라 split importance만으로 단정하면 위험하다. permutation, leaf-wise, tail slice를 함께 봐야 한다.</p>',
        "<h3>성능 재확인</h3>",
        table_html(cold_metrics.loc[cold_metrics["model"].astype(str).eq("cold_lightgbm")] if "model" in cold_metrics else cold_metrics),
        "<h3>Split Importance</h3>",
        table_html(lgb_importance),
        "<h3>Permutation 진단</h3>",
        table_html(lgb_perm),
        "<h3>Leaf-wise 분화 진단</h3>",
        table_html(lgb_leaf),
        "<h3>Tail Slice 진단</h3>",
        table_html(lgb_tail, 80),
        "</section>",
        '<section id="policy"><h2>8. 모델별 해석/보정 원칙</h2>',
        table_html(cold_group),
        '<p class="note">Warm은 선형 편향 보정, CatBoost는 leaf/segment fallback 보정, LightGBM은 tail 안정화 보정이 모델 구조와 가장 잘 맞는다.</p>',
        "</section>",
    ]

    OUT_HTML.write_text(f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>Track6 최종 모델 통합 해석 보고서</title><style>{css}</style></head><body>{''.join(body)}</body></html>", encoding="utf-8")
    print(f"wrote {OUT_HTML}")


if __name__ == "__main__":
    main()
