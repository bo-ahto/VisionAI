#!/usr/bin/env python3
"""Generate supervisor-facing Track6 model/feature/postprocessing report."""
from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DOC_DIR = REPO / "docs" / "track6" / "experiments"
WARM_OUT = REPO / "experiments" / "track6" / "WARM_HUBER_interpretability_audit" / "outputs"
COLD_OUT = REPO / "experiments" / "track6" / "COLD_models_interpretability_audit" / "outputs"
RESULT_DIR = REPO / "data" / "track6" / "results"

OUT_MD = DOC_DIR / "supervisor_model_feature_postprocessing_report.md"
OUT_HTML = DOC_DIR / "supervisor_model_feature_postprocessing_report.html"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame({"message": [f"missing: {path.relative_to(REPO)}"]})
    return pd.read_csv(path)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: object) -> str:
    if pd.isna(value):
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def md_table(df: pd.DataFrame, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    if df.empty:
        return "_데이터 없음_"
    view = df.copy()
    if columns:
        view = view[[col for col in columns if col in view.columns]]
    if max_rows is not None:
        view = view.head(max_rows)
    header = "| " + " | ".join(map(str, view.columns)) + " |"
    sep = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = [
        "| " + " | ".join(str(fmt(value)).replace("\n", " ") for value in row) + " |"
        for row in view.itertuples(index=False)
    ]
    return "\n".join([header, sep, *rows])


def html_table(df: pd.DataFrame, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    if df.empty:
        return '<p class="empty">데이터 없음</p>'
    view = df.copy()
    if columns:
        view = view[[col for col in columns if col in view.columns]]
    if max_rows is not None:
        view = view.head(max_rows)
    head = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    body = []
    for row in view.itertuples(index=False):
        cells = "".join(f"<td>{html.escape(fmt(value))}</td>" for value in row)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def metric_extract(df: pd.DataFrame, **filters: str) -> pd.Series:
    view = df.copy()
    for col, value in filters.items():
        if col in view:
            view = view.loc[view[col].astype(str).eq(value)]
    if view.empty:
        return pd.Series(dtype=object)
    return view.iloc[0]


def pp_summary(pp_metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope, model in [
        ("warm", "huber_warm_artist__base_existing_combo"),
        ("cold_catboost", "catboost_cold__base_medium_shape"),
        ("cold_lightgbm", "lightgbm_cold__base_support_size"),
    ]:
        base = metric_extract(pp_metrics, scope=scope, model=model, method="baseline")
        if base.empty:
            continue
        candidates = pp_metrics.loc[
            pp_metrics["scope"].astype(str).eq(scope)
            & pp_metrics["model"].astype(str).eq(model)
            & ~pp_metrics["method"].astype(str).eq("baseline")
        ].copy()
        if candidates.empty:
            continue
        best_mdape = candidates.sort_values("MdAPE").iloc[0]
        best_p95 = candidates.sort_values("p95_APE").iloc[0]
        rows.append(
            {
                "scope": scope,
                "baseline_MdAPE": base["MdAPE"],
                "best_MdAPE_method": best_mdape["method"],
                "best_MdAPE": best_mdape["MdAPE"],
                "baseline_p95_APE": base["p95_APE"],
                "best_p95_method": best_p95["method"],
                "best_p95_APE": best_p95["p95_APE"],
                "decision": decision_for(scope, base, best_mdape, best_p95),
            }
        )
    return pd.DataFrame(rows)


def root_cause_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def first_text(row: dict, keys: list[str]) -> str:
        for key in keys:
            value = row.get(key)
            if value is None or pd.isna(value):
                continue
            text = str(value)
            if text and text != "-":
                return text
        return "-"

    def standardize(df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for row in df.to_dict("records"):
            target = first_text(row, ["피처/그룹", "피처/조합", "피처/구간"])
            low_reason = first_text(
                row,
                [
                    "왜 일부 계수는 낮거나 음수인가",
                    "왜 낮게 나올 수 있는가",
                    "왜 낮게 나왔는가",
                    "왜 단독 방향 해석이 어려운가",
                    "왜 단일 피처로 보면 위험한가",
                    "왜 일부 영향이 분산되는가",
                    "왜 평균 지표만 보면 놓치는가",
                    "왜 단독 보정이 위험한가",
                    "왜 위험한가",
                ],
            )
            combination_reason = first_text(row, ["왜 조합으로 설명해야 하는가", "왜 무시하면 안 되는가", "후처리 의미"])
            rows.append(
                {
                    "피처/구간": target,
                    "관측 결과": first_text(row, ["관측 결과"]),
                    "모델 특성 기반 원인": first_text(row, ["모델 특성 기반 원인"]),
                    "높게 나온 이유": first_text(row, ["왜 높게 나왔는가"]),
                    "낮게/반대로 나온 이유": low_reason,
                    "조합/보정 의미": combination_reason,
                }
            )
        return pd.DataFrame(rows)

    warm = pd.DataFrame(
        [
            {
                "피처/그룹": "size: log_area, width_cm, height_cm, area_cm2",
                "관측 결과": "Warm Huber에서 contribution 1위 그룹",
                "모델 특성 기반 원인": "Huber는 선형 모델이라 각 크기 피처가 로그가격에 더해지는 독립 항으로 작동한다. 크기는 대부분 작품에서 관측되는 연속형 변수이고 결측/희소성이 낮아, 학습 과정에서 안정적인 공통 가격 축으로 선택되기 쉽다.",
                "왜 높게 나왔는가": "Warm 조건에서도 작가 이력만으로 가격을 설명할 수 없고, 같은 작가라도 작품 크기에 따라 가격대가 달라진다. 따라서 모델은 크기를 '작가 가격대 안에서 가격을 조정하는 기본 물리량'으로 크게 사용한다.",
                "왜 일부 계수는 낮거나 음수인가": "area_cm2는 log_area, width_cm, height_cm과 정보가 겹친다. 선형 모델은 중복 피처가 함께 있을 때 한 피처는 상승 방향, 다른 피처는 과대 상승을 눌러주는 보정 방향으로 배치할 수 있다. 따라서 area_cm2의 음의 계수는 면적이 가격을 낮춘다는 뜻이 아니라 중복 크기 정보 사이의 균형 조정이다.",
                "후처리 의미": "개별 크기 피처 하나를 보정 기준으로 쓰기보다 size 그룹 또는 size_bucket 기준으로 반복 편향을 확인해야 한다.",
            },
            {
                "피처/그룹": "medium_support_bucket",
                "관측 결과": "Warm Huber에서 contribution 2위 그룹",
                "모델 특성 기반 원인": "one-hot 범주형 피처는 해당 조합에 속하는 작품에만 일정한 로그가격 보정값을 더한다. Huber는 극단 가격 사례의 영향은 줄이지만, 반복적으로 나타나는 재료-지지체 조합의 평균 가격 차이는 계수로 남긴다.",
                "왜 높게 나왔는가": "재료와 지지체는 작품의 물리적 완성도, 시장 분류, 구매자가 기대하는 가격 범위를 동시에 반영한다. 단일 medium 또는 support보다 조합 피처가 더 구체적인 작품 유형을 나타내기 때문에 영향이 크게 나타났다.",
                "왜 낮게 나올 수 있는가": "희소 조합은 min_frequency 처리로 infrequent 그룹에 묶이거나 active_rate가 낮아 평균 contribution이 제한된다. 즉, 특정 조합의 계수가 커도 표본이 적으면 전체 영향도는 낮게 보인다.",
                "후처리 의미": "보정은 medium 단독보다 medium_support 조합을 우선 보되, 표본 수가 부족하면 support 또는 medium 단위로 fallback해야 한다.",
            },
            {
                "피처/그룹": "artist_key",
                "관측 결과": "Warm에서만 사용되는 주요 설명 축",
                "모델 특성 기반 원인": "Warm은 같은 작가가 학습 데이터에 존재하는 조건이다. one-hot artist_key는 해당 작가의 과거 가격대가 선형식의 절편 보정처럼 작동하게 만든다.",
                "왜 높게 나왔는가": "미술품 가격은 작품 물성뿐 아니라 작가의 기존 시장 가격대에 크게 의존한다. Warm에서는 이 정보가 직접 주어지므로 모델이 가격 기준선을 잡는 데 사용한다.",
                "왜 낮게 나올 수 있는가": "저빈도 작가는 infrequent 그룹으로 묶이고, Huber 손실은 극단 고가/저가 작가 사례에 과도하게 맞추지 않는다. 그래서 일부 작가 효과는 의도적으로 완화된다.",
                "후처리 의미": "low_artist_history 또는 infrequent artist 그룹은 별도 신뢰도 표시와 residual 점검이 필요하다.",
            },
            {
                "피처/그룹": "depth_3d / shape",
                "관측 결과": "Warm에서는 size, medium/support보다 낮은 영향",
                "모델 특성 기반 원인": "선형 Huber는 피처 간 복잡한 상호작용을 직접 만들지 않는다. 깊이나 형태가 가격에 영향을 주더라도 재료/크기와 결합되어야 의미가 커지는 경우, 선형 단독 항에서는 낮게 보일 수 있다.",
                "왜 낮게 나왔는가": "Warm에서는 이미 artist_key와 medium_support가 많은 가격 차이를 흡수한다. 따라서 depth나 shape가 단독으로 추가 설명하는 잔여 정보가 상대적으로 작다.",
                "왜 무시하면 안 되는가": "선형 Warm에서는 낮게 보여도 Cold 트리 모델에서는 depth와 size/medium interaction이 크게 나타난다. 즉, 낮은 영향은 피처가 무의미해서가 아니라 Warm Huber 구조 안에서 단독 선형 효과가 작다는 뜻이다.",
                "후처리 의미": "Warm에서는 보정 우선순위가 낮지만, 3D/극단 비율 구간은 risk slice로 별도 확인한다.",
            },
        ]
    )
    catboost = pd.DataFrame(
        [
            {
                "피처/조합": "size: width_cm, area_cm2, log_area, height_cm",
                "관측 결과": "CatBoost SHAP 상위 1~4위",
                "모델 특성 기반 원인": "Cold에는 artist_key가 없으므로 모델은 모든 작품에 공통으로 존재하는 물리량을 먼저 사용한다. CatBoost의 대칭 트리는 같은 depth에서 동일 split을 반복 적용하므로, 많은 샘플을 안정적으로 나눌 수 있는 크기 피처가 상단 분기 조건이 되기 쉽다.",
                "왜 높게 나왔는가": "처음 보는 작가의 가격 기준선을 직접 알 수 없기 때문에, 크기가 가격대의 대체 기준선 역할을 한다. 크기 피처는 결측이 적고 연속적이라 트리가 가격 구간을 나누기 좋은 신호다.",
                "왜 단일 피처로 보면 위험한가": "CatBoost는 크기 피처들을 독립 항으로 더하는 것이 아니라 분기 조건으로 사용한다. width_cm이 높다는 것은 단독 가격 프리미엄이 아니라, 특정 크기 구간으로 들어가는 경로가 예측값을 바꾼다는 뜻이다.",
                "후처리 의미": "size 구간별 잔차를 보되, CatBoost에서는 size 단독보다 size와 depth/medium 조합 segment를 우선한다.",
            },
            {
                "피처/조합": "depth_cm",
                "관측 결과": "SHAP 5위, interaction 상위 대부분에 포함",
                "모델 특성 기반 원인": "대칭 트리는 한 번 선택한 split 조건을 전체 depth에 반복 적용하기 때문에, depth가 size/medium/shape와 함께 구간을 나누면 여러 트리에서 반복적으로 영향이 커질 수 있다.",
                "왜 높게 나왔는가": "Cold 데이터에서 depth는 단순 치수가 아니라 2D/3D 성격, 오브제성, 설치/조각 가능성을 대신 나타낸다. 작가 정보가 없는 상황에서는 작품 유형을 구분하는 강한 단서가 된다.",
                "왜 단독 방향 해석이 어려운가": "깊이가 크면 항상 비싼 것이 아니라, 어떤 크기와 재료에서 깊이가 있는지가 중요하다. 그래서 interaction은 높지만 단독 방향성은 조합에 따라 달라진다.",
                "후처리 의미": "CatBoost 보정은 depth 관련 leaf segment를 확인하고, 표본이 적으면 medium_shape_bucket 또는 size/depth slice로 fallback한다.",
            },
            {
                "피처/조합": "width_cm x depth_cm, height_cm x depth_cm",
                "관측 결과": "interaction 1위, 2위",
                "모델 특성 기반 원인": "CatBoost interaction은 두 피처가 같은 트리 경로에서 예측값 변화를 함께 만든다는 뜻이다. 대칭 트리 구조에서는 반복 split 조합이 강한 segment 효과를 만든다.",
                "왜 높게 나왔는가": "넓거나 높은 작품에 깊이까지 있으면 일반 평면 작품과 다른 시장 분류가 된다. 모델은 이를 단순 대형 작품이 아니라 '큰 입체/오브제 가능성'으로 분리한다.",
                "왜 조합으로 설명해야 하는가": "width나 depth 각각의 값보다 두 조건이 동시에 만족될 때 가격 경로가 달라진다. 따라서 피처 영향도 보고에서 이 조합을 별도 설명해야 한다.",
                "후처리 의미": "leaf pattern 보정 후보를 만들 때 size-depth 조합을 우선 segment로 둔다.",
            },
            {
                "피처/조합": "medium_category / support_category",
                "관측 결과": "SHAP 중위권, depth/size와 interaction",
                "모델 특성 기반 원인": "CatBoost는 범주형 변수를 target statistics와 ordered boosting 방식으로 처리해 범주별 평균 가격 정보를 누수 위험을 줄이며 학습한다. 다만 범주 단독보다 다른 split과 결합될 때 영향이 커진다.",
                "왜 중위권인가": "재료/지지체는 가격을 설명하지만 Cold에서는 작가 정보 부재와 크기 효과가 더 크다. 그래서 단독 SHAP은 size보다 낮고, 조합 조건에서 의미가 커진다.",
                "왜 낮다고 버리면 안 되는가": "medium_category 단독 순위가 낮아도 depth_cm x medium_category interaction이 높다. 이는 재료가 단독 가격 신호가 아니라 입체성/크기 조건의 의미를 바꾸는 조절 변수라는 뜻이다.",
                "후처리 의미": "CatBoost 보정은 medium 단독보다 medium_shape_bucket 또는 depth-medium segment 기준이 더 적합하다.",
            },
        ]
    )
    lightgbm = pd.DataFrame(
        [
            {
                "피처/구간": "area_cm2",
                "관측 결과": "permutation 영향 최대",
                "모델 특성 기반 원인": "LightGBM은 leaf-wise 방식으로 손실 감소가 큰 leaf를 우선 확장한다. area_cm2는 연속형이고 가격대 분리에 강하므로, 특정 면적 기준 split이 반복적으로 깊은 leaf를 만들기 쉽다.",
                "왜 높게 나왔는가": "Cold에는 작가 기준선이 없고, 면적은 가격대 구분력이 강하다. permutation에서 area_cm2를 섞으면 기존 leaf 경로가 크게 무너져 MdAPE와 p95가 동시에 악화된다.",
                "왜 위험한가": "leaf-wise 구조는 강한 피처를 좁은 구간까지 깊게 파고들 수 있다. 따라서 area_cm2 의존도가 높다는 것은 평균 성능에는 유리하지만 큰 작품 구간 tail risk를 키울 수 있다.",
                "후처리 의미": "area 단독 보정보다 size_bucket, pred_log bin, support_size_bucket으로 과민 구간을 안정화한다.",
            },
            {
                "피처/구간": "width_cm, height_cm, log_area",
                "관측 결과": "split/permutation 상위권",
                "모델 특성 기반 원인": "LightGBM은 여러 크기 표현 중 손실을 가장 많이 줄이는 split을 선택한다. 서로 비슷한 정보를 가진 크기 피처들이 여러 경로에서 번갈아 사용될 수 있다.",
                "왜 높게 나왔는가": "같은 면적이라도 가로형/세로형/정방형 여부에 따라 가격 분포가 달라질 수 있어, 모델은 면적 외 크기 표현도 활용한다.",
                "왜 일부 영향이 분산되는가": "크기 피처끼리 상관이 높기 때문에 하나를 permutation해도 다른 크기 피처가 일부 대체한다. 그래서 area_cm2만 압도적으로 높고 나머지는 중간 수준으로 나타난다.",
                "후처리 의미": "크기 피처를 개별 보정하지 말고 크기 bucket과 형태 bucket의 결합으로 tail을 확인한다.",
            },
            {
                "피처/구간": "support_size_bucket: canvas__q5",
                "관측 결과": "tail slice p95_APE 최상위",
                "모델 특성 기반 원인": "LightGBM의 leaf-wise 성장은 특정 구간의 평균 손실을 줄이는 데 집중한다. 하지만 대형 캔버스처럼 가격 분산이 큰 구간은 같은 leaf 안에서도 실제 가격 편차가 커져 p95가 튈 수 있다.",
                "왜 높게 나왔는가": "대형 캔버스는 고가 가능성이 있지만 모든 대형 캔버스가 고가인 것은 아니다. 작가 정보가 없는 Cold 조건에서는 이 분산을 충분히 설명하지 못해 큰 오차가 발생한다.",
                "왜 평균 지표만 보면 놓치는가": "해당 구간의 MdAPE는 전체와 비슷해도 p95가 매우 높다. 즉 일반 사례는 맞추지만 일부 고위험 사례에서 크게 틀리는 구조다.",
                "후처리 의미": "가격 범위/신뢰도 표시, p95 안정화, 상한/하한 완충 보정의 우선 대상이다.",
            },
            {
                "피처/구간": "medium_category: acrylic",
                "관측 결과": "tail slice p95 상위",
                "모델 특성 기반 원인": "범주형이 ordinal encoding된 뒤 트리에 들어가면, LightGBM은 범주 자체보다 해당 범주가 놓인 split 경로의 손실 감소를 기준으로 사용한다. acrylic은 표본이 많고 내부 가격 분산도 커 tail risk가 나타난다.",
                "왜 높게 나왔는가": "아크릴은 작품 수가 많아 모델이 자주 만나는 범주지만, 같은 아크릴 안에서도 크기/지지체/작가 부재에 따라 가격 편차가 크다. 그래서 단순 medium 정보만으로는 충분하지 않다.",
                "왜 단독 보정이 위험한가": "acrylic 전체를 일괄 보정하면 정상 구간까지 흔들 수 있다. 문제는 acrylic 전체가 아니라 acrylic 중 특정 size/support 조합일 가능성이 높다.",
                "후처리 의미": "medium 단독보다 medium x size 또는 support_size_bucket과 함께 tail 보정을 설계한다.",
            },
        ]
    )
    return standardize(warm), standardize(catboost), standardize(lightgbm)


def decision_for(scope: str, base: pd.Series, best_mdape: pd.Series, best_p95: pd.Series) -> str:
    mdape_gain = float(base["MdAPE"]) - float(best_mdape["MdAPE"])
    p95_gain = float(base["p95_APE"]) - float(best_p95["p95_APE"])
    if scope == "warm" and mdape_gain > 0:
        return "채택 후보: 전체/예측구간 편향 보정이 MdAPE를 개선한다."
    if scope == "cold_lightgbm" and p95_gain > 0:
        return "조건부 후보: MdAPE 악화 여부를 제한하면서 tail 안정화 위주로 검증한다."
    if scope == "cold_catboost":
        return "보류: 단순 median 보정은 MdAPE를 악화시켜 leaf/segment fallback 재실험이 필요하다."
    return "보류"


def main() -> None:
    warm_metrics = read_csv(WARM_OUT / "warm_huber_final_artifact_metrics.csv")
    warm_group = read_csv(WARM_OUT / "warm_huber_feature_group_contribution_summary.csv")
    warm_coef = read_csv(WARM_OUT / "warm_huber_final_coefficients_contributions.csv")
    warm_outlier = read_csv(WARM_OUT / "warm_huber_outlier_diagnostics.csv")
    warm_epsilon = read_csv(WARM_OUT / "warm_huber_epsilon_sensitivity.csv")

    cold_metrics = read_csv(COLD_OUT / "cold_final_artifact_metrics.csv")
    cold_group = read_csv(COLD_OUT / "cold_feature_group_interpretation_summary.csv")
    cat_shap = read_csv(COLD_OUT / "cold_catboost_final_shap_summary.csv")
    cat_inter = read_csv(COLD_OUT / "cold_catboost_final_interactions.csv")
    cat_leaf = read_csv(COLD_OUT / "cold_catboost_leaf_segment_residuals.csv")
    cat_structure = read_csv(COLD_OUT / "cold_catboost_structure_summary.csv")
    lgb_perm = read_csv(COLD_OUT / "cold_lightgbm_final_permutation_diagnostics.csv")
    lgb_tail = read_csv(COLD_OUT / "cold_lightgbm_tail_slice_diagnostics.csv")
    lgb_leaf = read_csv(COLD_OUT / "cold_lightgbm_leafwise_diagnostics.csv")

    val_metrics = read_csv(RESULT_DIR / "t6_e005_feature_combo_ablation_metrics.csv")
    test_metrics = read_csv(RESULT_DIR / "t6_e007_test_confirmation_metrics.csv")
    pp_metrics = read_csv(RESULT_DIR / "t6_pp_residual_calibration_metrics.csv")
    risk_slices = read_csv(RESULT_DIR / "t6_e008_risk_policy_analysis_slices.csv")
    manifest = read_json(RESULT_DIR / "t6_e009_final_artifact_manifest.json")

    pp_decision = pp_summary(pp_metrics)
    warm_root, cat_root, lgb_root = root_cause_tables()
    warm_top_coef = warm_coef.sort_values("rank_by_centered_abs_contribution").head(12)
    cat_top_shap = cat_shap.head(8)
    cat_top_inter = cat_inter.head(8)
    lgb_top_perm = lgb_perm.sort_values("MdAPE_delta", ascending=False).head(8)
    lgb_top_tail = lgb_tail.sort_values("p95_APE", ascending=False).head(8)

    md = f"""# Track6 모델별 피처 영향도, 조합 근거, 후처리 튜닝 보고서

- 작성일: {date.today().isoformat()}
- 목적: 상사 보고용으로 Warm Huber, Cold CatBoost, Cold LightGBM이 가격을 예측하는 방식과 피처 영향도 해석, 피처 조합 선정 근거, 후처리 튜닝 계획을 한 문서로 정리한다.
- 사용 산출물: 최종 artifact 해석 감사 결과, T6-E005 피처 조합 ablation, T6-E007 test confirmation, T6-E008 risk slice, T6-PP residual calibration.

## 1. 결론 요약

- Warm Huber는 선형 예측식이므로 피처별 영향이 계수와 실제 contribution으로 직접 설명된다. 최종적으로 `size + medium_support + artist_key` 조합이 타당하다.
- Cold CatBoost는 대칭 트리 구조이므로 단일 중요도보다 `SHAP + interaction + leaf segment`를 함께 봐야 한다. 최종적으로 `size + depth_3d + medium/shape` 조합이 타당하다.
- Cold LightGBM은 leaf-wise 트리 구조이므로 평균 중요도보다 `permutation 영향 + tail slice`가 중요하다. 최종적으로 `area/size + support_size_bucket + pred_log bin` 중심의 tail 안정화가 필요하다.
- 후처리는 Warm은 즉시 채택 후보가 있고, Cold CatBoost는 단순 보정 보류, Cold LightGBM은 tail 안정화 후보로 보는 것이 맞다.

## 2. 최종 모델과 기준 성능

최종 artifact 구성은 아래와 같다.

```text
Warm Huber: base_existing_combo + artist_key
Cold CatBoost: base_medium_shape
Cold LightGBM: base_support_size
```

### 최종 artifact test 성능

{md_table(warm_metrics)}

{md_table(cold_metrics)}

### validation에서 조합을 고른 근거

{md_table(val_metrics, ["split", "model", "feature_set", "median_ape", "p95_ape", "within_30", "within_50", "rmse_log"], 12)}

### test 확인 결과

{md_table(test_metrics, ["split", "model", "feature_set", "validation_median_ape", "validation_p95_ape", "median_ape", "p95_ape", "rmse_log"])}

## 3. Warm Huber: 가격 예측 공식과 피처 영향 해석

### 예측 공식

Warm Huber는 로그 가격을 먼저 예측한 뒤 원 가격으로 환산한다.

```text
z_num = StandardScaler(x_num)
z_cat = OneHotEncoder(x_cat)
pred_log_price = intercept + sum_j(beta_j * z_j)
pred_price = exp(pred_log_price)
```

HuberRegressor의 핵심은 학습 손실 함수다. 일반 선형 회귀는 큰 오차를 계속 제곱으로 강하게 따라가지만, Huber는 기준을 넘는 큰 오차를 선형 손실로 바꿔 이상치 영향력을 줄인다.

```text
r_i = y_i - (intercept + x_i * beta)
u_i = r_i / sigma

loss(u_i) =
  0.5 * u_i^2                         if |u_i| <= epsilon
  epsilon * |u_i| - 0.5 * epsilon^2    if |u_i| > epsilon

objective = sum_i loss(u_i) + alpha * ||beta||^2
```

따라서 Warm Huber에서 피처 영향은 다음 순서로 해석했다.

- 계수 `beta_j`: 해당 피처가 로그 가격을 올리는지/내리는지 확인
- 원 단위 환산 계수: 표준화된 숫자형 피처를 실제 cm, 면적 단위로 바꿔 확인
- 실제 contribution: `beta_j * z_j`가 test 데이터에서 평균적으로 얼마나 예측값을 움직였는지 확인
- 범주형 피처: one-hot 원계수 대신 centered contribution으로 해석

### 피처 그룹 영향도

{md_table(warm_group)}

### 상위 피처 contribution

{md_table(warm_top_coef, ["encoded_feature", "raw_feature", "feature_group", "coef", "original_unit_coef", "active_rate", "mean_abs_centered_contribution", "mean_centered_contribution", "centered_direction", "rank_by_centered_abs_contribution"])}

### Warm 피처 조합을 이렇게 판단한 이유

- `size` 그룹이 mean_abs_centered_contribution_sum 1위다. 즉, 실제 test 예측값을 가장 많이 움직인 축은 작품 크기다.
- `medium_support`와 `support`가 그 다음 설명 축이다. 같은 크기라도 재료와 지지체 조합에 따라 가격대가 달라진다는 뜻이다.
- Warm은 기존 작가가 있는 조건이므로 `artist_key`가 과거 작가 가격대 정보를 반영한다.
- 그래서 Warm 조합은 `size + medium_support + artist_key`가 가장 설명 가능하고, 선형 모델의 특성과도 맞다.

### Huber 안정성 확인

{md_table(warm_outlier)}

{md_table(warm_epsilon)}

### Warm Huber 피처별 근본 해석

아래 표는 “수치가 높다/낮다”를 넘어, 왜 해당 피처가 Warm Huber 구조 안에서 그렇게 작동했는지를 정리한 것이다.

{md_table(warm_root)}

## 4. Cold CatBoost: 트리 예측 과정과 피처 조합 해석

### 예측 방식

CatBoost는 여러 개의 대칭 트리를 더해 로그 가격을 예측한다.

```text
pred_log_price = base_score + sum_t(leaf_value_t(x))
pred_price = exp(pred_log_price)
```

대칭 트리는 같은 depth의 모든 노드가 동일한 split 조건을 공유한다. 따라서 CatBoost에서는 “피처 하나가 가격을 올린다”보다 “어떤 피처 조합이 같은 경로에서 반복적으로 가격 구간을 나누는가”가 더 중요하다.

### 구조 확인

{md_table(cat_structure)}

### SHAP 기준 상위 피처

{md_table(cat_top_shap)}

### interaction 기준 상위 조합

{md_table(cat_top_inter)}

### CatBoost 조합을 이렇게 판단한 이유

- SHAP 상위가 `width_cm`, `area_cm2`, `log_area`, `height_cm`로 모두 size 계열이다. Cold에서는 작가 이력이 없으므로 작품 물리 크기가 가격대를 먼저 나눈다.
- interaction 1위와 2위가 `width_cm x depth_cm`, `height_cm x depth_cm`이다. 이는 CatBoost가 size와 depth를 조합 조건으로 사용한다는 뜻이다.
- `depth_cm x medium_category`도 상위권이다. 입체성의 가격 의미가 재료에 따라 달라진다.
- 그래서 CatBoost 조합은 `size + depth_3d + medium/shape`가 모델 구조와 맞다.

### leaf segment 진단

{md_table(cat_leaf, ["rows", "median_residual_log", "MdAPE", "p95_APE", "coverage_rate"], 12)}

### Cold CatBoost 피처별 근본 해석

아래 표는 CatBoost의 대칭 트리 구조와 ordered categorical 처리 특성에 맞춰 피처 영향의 원인을 설명한 것이다.

{md_table(cat_root)}

## 5. Cold LightGBM: 트리 예측 과정과 피처 조합 해석

### 예측 방식

LightGBM도 여러 트리를 더해 로그 가격을 예측한다.

```text
pred_log_price = base_score + learning_rate * sum_t(leaf_value_t(x))
pred_price = exp(pred_log_price)
```

LightGBM은 leaf-wise 방식으로 손실을 크게 줄일 수 있는 leaf를 우선 확장한다. 그래서 평균 성능은 좋아질 수 있지만 일부 좁은 구간에서 오차가 크게 튀는 tail risk가 생길 수 있다.

### permutation 기준 피처 영향

{md_table(lgb_top_perm)}

### tail 위험 구간

{md_table(lgb_top_tail)}

### leaf-wise 위험 확인

{md_table(lgb_leaf, max_rows=12)}

### LightGBM 조합을 이렇게 판단한 이유

- `area_cm2`를 섞었을 때 MdAPE_delta가 +0.2542, p95_APE_delta가 +7.5139로 가장 크다. 즉, LightGBM은 면적 의존도가 매우 높다.
- `support_size_bucket=canvas__q5`의 p95_APE가 26.43으로 가장 높다. 대형 캔버스 구간은 점예측보다 위험도 표시와 tail 안정화가 중요하다.
- leaf-wise 구조상 leaf 자체를 운영 보정 기준으로 쓰기에는 복잡하므로, 사람이 이해 가능한 `size_bucket`, `support_size_bucket`, `pred_log bin`으로 내려와 보정하는 것이 맞다.

### Cold LightGBM 피처별 근본 해석

아래 표는 LightGBM의 leaf-wise 성장 방식 때문에 어떤 피처가 크게 작동하고 어떤 구간에서 tail risk가 생기는지를 설명한 것이다.

{md_table(lgb_root)}

## 6. 지금까지 실험을 통해 조합을 찾은 과정

- 1단계: T6-E005에서 여러 feature_set을 validation 기준으로 비교했다.
- 2단계: T6-E006에서 Warm, Cold CatBoost, Cold LightGBM 후보를 선택했다.
- 3단계: T6-E007에서 선택 후보를 locked test로 확인했다.
- 4단계: 최종 artifact를 만든 뒤, 기존 해석 스크립트와 피처셋이 불일치하는 문제를 확인했다.
- 5단계: 최종 artifact 기준으로 Warm 계수/contribution, CatBoost SHAP/interaction, LightGBM permutation/tail slice를 재산출했다.
- 6단계: 단순 성능표가 아니라 모델 구조에 맞는 영향도 지표로 조합 이유를 다시 설명했다.

## 7. 후처리 튜닝 결과와 계획

### 기존 residual calibration 결과

{md_table(pp_decision)}

### 모델별 후처리 방향

| 모델 | 현재 판단 | 보정 방식 | 이유 | 적용 조건 |
| --- | --- | --- | --- | --- |
| Warm Huber | 채택 후보 | overall median residual 또는 pred_bin median residual | 선형 모델이라 전체 편향과 예측값 구간별 편향을 로그 공간에서 더하는 방식이 자연스럽고 MdAPE가 개선됐다. | validation/CV에서 보정값을 고정한 뒤 test/운영에서 재확인 |
| Cold CatBoost | 보류 후 재실험 | leaf/segment residual + fallback | 단순 median 보정은 MdAPE를 악화시켰다. CatBoost 구조상 대칭 트리 leaf와 interaction segment를 이용한 보정이 더 적합하다. | leaf coverage가 낮으면 medium_shape_bucket, shape/medium, overall 순서로 fallback |
| Cold LightGBM | 조건부 후보 | pred_log bin + size/support bucket tail 안정화 | 평균 예측보다 p95 tail risk가 문제이며, support_size_bucket과 area/size 의존도가 크다. | MdAPE 악화를 제한하고 p95 개선을 우선 목표로 검증 |

### risk slice 근거

{md_table(risk_slices, ["model", "slice", "n", "median_ape", "p95_ape", "within_30", "q80_range_multiplier", "risk_flag"], 14)}

## 8. 보고서 완성 기준과 추가 검증 계획

- 보고서 작성에 필요한 핵심 근거는 확보했다. 최종 artifact 기준 성능, 피처 영향도, 모델 구조별 해석 지표, 1차 residual calibration 결과가 모두 존재한다.
- Warm Huber: 현재 보정 후보가 이미 개선을 보였으므로 `PP-A1-W`는 실행 후보로 볼 수 있다. 단, 운영 적용 전 보정값은 validation 또는 cross-validation에서 고정해야 한다.
- Cold CatBoost: 단순 residual 보정은 보류다. 보고 결론은 “CatBoost는 단순 보정 적용이 아니라 leaf/segment fallback 보정으로 별도 실험해야 한다”가 맞다.
- Cold LightGBM: 단순 median 보정보다 tail 안정화 실험이 필요하다. 특히 `support_size_bucket`, `size_bucket`, `pred_log bin` 기준으로 p95 개선과 MdAPE 악화 제한을 같이 봐야 한다.
- 공통: 후처리 실험은 test 잔차로 보정값을 만들면 안 된다. 보정값은 validation 또는 OOF에서 만들고 locked test는 최종 확인에만 사용해야 한다.

## 9. 보고용 최종 메시지

- Warm Huber는 가격을 선형식으로 계산하기 때문에 피처별 계수와 contribution으로 영향도를 직접 설명할 수 있다.
- Cold CatBoost와 Cold LightGBM은 모두 트리형 모델이지만 예측 방식이 다르므로 같은 방식으로 해석하면 안 된다.
- CatBoost는 대칭 트리 구조라 피처 조합과 interaction을 중심으로 설명해야 한다.
- LightGBM은 leaf-wise 구조라 평균 중요도보다 tail 위험 구간을 중심으로 설명해야 한다.
- 후처리는 모델 구조에 맞춰 다르게 가야 한다. Warm은 로그 잔차 보정, CatBoost는 segment fallback, LightGBM은 tail 안정화가 맞다.
"""

    css = """
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:32px;color:#1f2933;line-height:1.62}
    h1{font-size:28px;margin-bottom:8px}h2{font-size:21px;margin-top:34px;border-bottom:1px solid #d9e2ec;padding-bottom:6px}h3{font-size:16px;margin-top:22px}
    table{border-collapse:collapse;width:100%;font-size:12.5px;margin:10px 0 24px}th,td{border:1px solid #d9e2ec;padding:7px 8px;vertical-align:top}th{background:#f0f4f8;text-align:left}
    code,pre{background:#f5f7fa;border:1px solid #d9e2ec;border-radius:4px}code{padding:1px 4px}pre{padding:12px;overflow:auto}
    ul{padding-left:22px}.empty{color:#5f6c7b}
    """
    html_body = md_to_html(md)
    OUT_MD.write_text(md, encoding="utf-8")
    OUT_HTML.write_text(
        f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Track6 모델별 피처/후처리 보고서</title><style>{css}</style></head><body>{html_body}</body></html>',
        encoding="utf-8",
    )
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_HTML}")
    if manifest:
        print(f"source_manifest={manifest.get('result_json', '-')}")


def md_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    in_code = False
    in_ul = False
    table_lines: list[str] = []

    def flush_table() -> None:
        nonlocal table_lines
        if not table_lines:
            return
        rows = [line.strip().strip("|").split("|") for line in table_lines if line.startswith("|")]
        if len(rows) >= 2:
            headers = [cell.strip() for cell in rows[0]]
            body_rows = rows[2:]
            out.append("<table><thead><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in headers) + "</tr></thead><tbody>")
            for row in body_rows:
                out.append("<tr>" + "".join(f"<td>{html.escape(cell.strip())}</td>" for cell in row) + "</tr>")
            out.append("</tbody></table>")
        table_lines = []

    for line in lines:
        if line.startswith("|"):
            flush_list = False
            if in_ul:
                out.append("</ul>")
                in_ul = False
            table_lines.append(line)
            continue
        flush_table()
        if line.startswith("```"):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append("<pre><code>" if not in_code else "</code></pre>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(line) + "\n")
            continue
        if line.startswith("# "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline_md(line[2:])}</li>")
        elif not line.strip():
            if in_ul:
                out.append("</ul>")
                in_ul = False
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<p>{inline_md(line)}</p>")
    flush_table()
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def inline_md(text: str) -> str:
    escaped = html.escape(text)
    parts = escaped.split("`")
    for idx in range(1, len(parts), 2):
        parts[idx] = f"<code>{parts[idx]}</code>"
    return "".join(parts)


if __name__ == "__main__":
    main()
