#!/usr/bin/env python3
"""Build a Warm feature correction policy from previous experiment evidence.

The goal is not to train another model yet. This step freezes the feature
groups, allowed combinations, and correction caps/strengths that should be used
by the next Huber residual calibration experiment.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[4]
EXP_ID = "PP-FPOL1"
EXP_DIR = REPO / "experiments/track6/PP-FPOL1_warm_artist_artwork_feature_correction_policy"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(rel: str) -> pd.DataFrame:
    path = REPO / rel
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def get_metric(df: pd.DataFrame, mask: pd.Series, column: str, default: float | None = None) -> float | None:
    if df.empty or column not in df.columns:
        return default
    values = df.loc[mask, column].dropna()
    if values.empty:
        return default
    return float(values.iloc[0])


def policy_rows() -> list[dict[str, object]]:
    amw9_features = load_csv(
        "experiments/track6/PP-AMW9_warm_artist_feature_impact_summary/outputs/feature_level_numeric_impact.csv"
    )
    amw9_combos = load_csv(
        "experiments/track6/PP-AMW9_warm_artist_feature_impact_summary/outputs/feature_combo_numeric_impact.csv"
    )
    warm_drop = load_csv(
        "experiments/track6/PP-AMW9_warm_artist_feature_impact_summary/outputs/warm_group_drop_numeric_impact.csv"
    )
    warm_contrib = load_csv(
        "experiments/track6/WARM_HUBER_interpretability_audit/outputs/warm_huber_feature_group_contribution_summary.csv"
    )
    amw10_summary = load_csv(
        "experiments/track6/PP-AMW10_warm_birth_generation_activity_external_residual_correction/outputs/feature_set_summary.csv"
    )
    c10 = load_csv("experiments/track6/C10_c8_plus_edition/outputs/result_sheet.csv")

    def drop_delta(group: str, metric: str) -> float | None:
        return get_metric(warm_drop, warm_drop.get("drop_group", pd.Series(dtype=str)).eq(group), f"delta_{metric}")

    def contrib(group: str, column: str) -> float | None:
        return get_metric(warm_contrib, warm_contrib.get("feature_group", pd.Series(dtype=str)).eq(group), column)

    size_feature = amw9_features["feature_or_group"].eq("작품 크기 파생 피처") & amw9_features["scope"].eq("warm")
    size_combo = amw9_combos["feature_combo"].eq("작가명 + 전체 크기") & amw9_combos["scope"].eq("warm")
    medium_combo = amw9_combos["feature_combo"].eq("크기/재료 + 지지체") & amw9_combos["scope"].eq("warm")
    year_combo = amw9_combos["feature_combo"].eq("작가명 + 제작연도") & amw9_combos["scope"].eq("warm")

    def amw10_delta(feature_set: str, metric: str) -> float | None:
        return get_metric(
            amw10_summary,
            amw10_summary.get("feature_set", pd.Series(dtype=str)).eq(feature_set),
            f"best_test_delta_{metric}",
        )

    limited = c10["variable_block"].eq("C8 + 리미티드 에디션 여부") & c10["scope"].eq("Warm") & c10["model_name"].eq("Huber")
    c8 = c10["variable_block"].eq("C8 기준") & c10["scope"].eq("Warm") & c10["model_name"].eq("Huber")
    c8_mdape = get_metric(c10, c8, "MdAPE")
    limited_mdape = get_metric(c10, limited, "MdAPE")
    limited_mape = get_metric(c10, limited, "MAPE")
    c8_mape = get_metric(c10, c8, "MAPE")

    return [
        {
            "feature_group": "artwork_size_shape",
            "korean_name": "작품 크기/형태",
            "columns": "width_cm,height_cm,area_cm2,log_area,aspect_ratio,is_extreme_aspect_ratio",
            "decision": "adopt_core",
            "role": "모든 Warm residual Huber 보정의 기본 작품 축",
            "evidence": (
                f"크기 추가 MdAPE delta {get_metric(amw9_features, size_feature, 'delta_MdAPE'):.4f}; "
                f"작가명+전체크기 MdAPE delta {get_metric(amw9_combos, size_combo, 'delta_MdAPE'):.4f}; "
                f"size 제거 test MdAPE/MAPE/p95 delta {drop_delta('size', 'MdAPE'):.4f}/"
                f"{drop_delta('size', 'MAPE'):.4f}/{drop_delta('size', 'p95_APE'):.4f}; "
                f"기여도 rank {int(contrib('size', 'rank'))}"
            ),
            "correction_policy": "include_in_residual_model; pred_price_bin tail guard 적용",
            "recommended_cap": "0.06 또는 0.08",
            "recommended_strength": "0.25 또는 0.35",
            "risk": "면적 단독 구간 보정은 MdAPE 악화 가능. Huber residual 안에서만 사용.",
        },
        {
            "feature_group": "artwork_medium_support",
            "korean_name": "작품 재료/지지체",
            "columns": "medium_category,support_category,medium_support_bucket,nant_support",
            "decision": "adopt_conditional",
            "role": "크기 피처와 결합할 때만 작품 보정축으로 사용",
            "evidence": (
                f"크기+재료+지지체 MdAPE delta {get_metric(amw9_combos, medium_combo, 'delta_MdAPE'):.4f}; "
                f"medium_support 제거 test MdAPE/MAPE/p95 delta {drop_delta('medium_support', 'MdAPE'):.4f}/"
                f"{drop_delta('medium_support', 'MAPE'):.4f}/{drop_delta('medium_support', 'p95_APE'):.4f}; "
                f"medium_support 기여도 rank {int(contrib('medium_support', 'rank'))}"
            ),
            "correction_policy": "size/SVC/artist 신호와 함께 약한 residual 보정에만 포함",
            "recommended_cap": "0.03 또는 0.06",
            "recommended_strength": "0.25 또는 0.35",
            "risk": "단독 재료/지지체는 악화. 범주 수가 많아 과보정 방지 필요.",
        },
        {
            "feature_group": "artist_birth_generation",
            "korean_name": "작가 생년/세대",
            "columns": "artist_meta_birth_year,artist_birth_generation_bin",
            "decision": "adopt_core_artist",
            "role": "작가 가격대 내부의 시대/세대 편향 보정",
            "evidence": (
                f"PP-AMW10 생년+세대 best test delta MdAPE/MAPE/p95 "
                f"{amw10_delta('birth_generation', 'MdAPE'):.4f}/"
                f"{amw10_delta('birth_generation', 'MAPE'):.4f}/"
                f"{amw10_delta('birth_generation', 'p95_APE'):.4f}"
            ),
            "correction_policy": "작품 보정축과 별도 후보 및 결합 후보 모두 유지",
            "recommended_cap": "0.03",
            "recommended_strength": "0.50",
            "risk": "career/activity까지 전부 묶으면 test MAPE 악화 가능.",
        },
        {
            "feature_group": "artist_followers_for_sale",
            "korean_name": "작가 팔로워/판매중 작품 수",
            "columns": "artist_meta_followers_log1p,artist_meta_followers_missing,artist_meta_for_sale_works_log1p,artist_meta_for_sale_works_missing",
            "decision": "adopt_light",
            "role": "작가 활동/노출의 작은 잔차 편향 보정",
            "evidence": (
                f"팔로워 best test delta MdAPE/MAPE/p95 {amw10_delta('birth_generation_followers', 'MdAPE'):.4f}/"
                f"{amw10_delta('birth_generation_followers', 'MAPE'):.4f}/"
                f"{amw10_delta('birth_generation_followers', 'p95_APE'):.4f}; "
                f"판매중 작품 수 best test delta MdAPE/MAPE/p95 {amw10_delta('birth_generation_for_sale', 'MdAPE'):.4f}/"
                f"{amw10_delta('birth_generation_for_sale', 'MAPE'):.4f}/"
                f"{amw10_delta('birth_generation_for_sale', 'p95_APE'):.4f}"
            ),
            "correction_policy": "생년/세대와 함께 소규모 Huber 보정",
            "recommended_cap": "0.03",
            "recommended_strength": "0.50",
            "risk": "activity bundle 전체는 test에서 MAPE/p95 악화.",
        },
        {
            "feature_group": "artwork_year_age",
            "korean_name": "작품 제작연도/연식",
            "columns": "artwork_year,has_artwork_year,artwork_year_missing,artwork_year_source,artwork_year_match_method",
            "decision": "diagnostic_or_guard",
            "role": "작품 시기 신호 및 신뢰도 gate",
            "evidence": f"작가명+제작연도 MdAPE delta {get_metric(amw9_combos, year_combo, 'delta_MdAPE'):.4f}",
            "correction_policy": "직접 보정값보다 year availability/source guard로 우선 사용",
            "recommended_cap": "0.02 또는 0.03",
            "recommended_strength": "0.25",
            "risk": "제작연도 입력 신뢰도에 민감하고 개선 폭이 작음.",
        },
        {
            "feature_group": "artwork_depth_3d",
            "korean_name": "작품 깊이/3D",
            "columns": "depth_cm,has_depth,is_3d_candidate",
            "decision": "guard_only",
            "role": "3D/깊이 특수 케이스의 tail guard",
            "evidence": (
                f"depth_3d 제거 test MdAPE/MAPE/p95 delta {drop_delta('depth_3d', 'MdAPE'):.4f}/"
                f"{drop_delta('depth_3d', 'MAPE'):.4f}/{drop_delta('depth_3d', 'p95_APE'):.4f}; "
                f"기여도 rank {int(contrib('depth_3d', 'rank'))}"
            ),
            "correction_policy": "보정 모델 핵심 피처 제외. 큰 오차 원인 분류/gate로 사용.",
            "recommended_cap": "0.02",
            "recommended_strength": "0.25",
            "risk": "Warm에서는 평균 효과 작고 tail 악화 위험.",
        },
        {
            "feature_group": "edition",
            "korean_name": "에디션 정보",
            "columns": "edition_class,is_edition,is_limited_edition,is_open_edition,is_unknown_edition,edition_info_available",
            "decision": "holdout_diagnostic",
            "role": "에디션 작품 slice 진단",
            "evidence": (
                f"C8+limited edition Huber MdAPE delta {(limited_mdape - c8_mdape):.4f}; "
                f"MAPE delta {(limited_mape - c8_mape):.4f}"
            ),
            "correction_policy": "메인 계수 보정 후보에서 제외. 충분 표본 확보 후 slice 보정 재검증.",
            "recommended_cap": "0.00",
            "recommended_strength": "0.00",
            "risk": "에디션 표본이 작고 MAPE 악화 신호.",
        },
        {
            "feature_group": "gallery_exhibition",
            "korean_name": "갤러리/전시 외부 메타",
            "columns": "gallery_tier_raw_numeric,gallery_feature_source,gallery_city_count_log,artist_exhibition_total_count_log,artist_exhibition_available_count",
            "decision": "guard_or_auxiliary",
            "role": "외부 메타 보유 여부와 신뢰도 gate",
            "evidence": (
                f"갤러리 best test delta MdAPE/MAPE/p95 {amw10_delta('birth_generation_gallery', 'MdAPE'):.4f}/"
                f"{amw10_delta('birth_generation_gallery', 'MAPE'):.4f}/"
                f"{amw10_delta('birth_generation_gallery', 'p95_APE'):.4f}; "
                f"전시 best test delta MdAPE/MAPE/p95 {amw10_delta('birth_generation_exhibition', 'MdAPE'):.4f}/"
                f"{amw10_delta('birth_generation_exhibition', 'MAPE'):.4f}/"
                f"{amw10_delta('birth_generation_exhibition', 'p95_APE'):.4f}"
            ),
            "correction_policy": "메인 보정 계수에서 제외. 외부 신뢰도 gate나 리포팅 설명 피처로 사용.",
            "recommended_cap": "0.00 또는 0.02",
            "recommended_strength": "0.00 또는 0.25",
            "risk": "커버리지가 낮고 gate 적용 시 효과가 거의 사라짐.",
        },
        {
            "feature_group": "svc_comparable_reliability",
            "korean_name": "유사작품/비교군 신뢰도",
            "columns": "svc_group_n,svc_spread,quantile_width,l10_price_range_ratio,model_prediction_gap",
            "decision": "adopt_gate",
            "role": "작품 보정값 적용 강도와 tail guard 결정",
            "evidence": "PP-WCOEF/PP-WHUBER7에서 pred_size_svc 또는 pred_size_material_svc_artist 후보가 p95/MAPE 방어에 반복적으로 유효",
            "correction_policy": "보정 모델 피처 또는 reliability shrink/gate로 사용",
            "recommended_cap": "0.06 또는 0.08",
            "recommended_strength": "0.25 또는 0.35",
            "risk": "비교군 품질이 낮은 구간은 큰 보정 금지.",
        },
    ]


def candidate_grid_rows() -> list[dict[str, object]]:
    feature_sets = {
        "artist_core": [
            "artist_meta_birth_year",
            "artist_birth_generation_bin",
        ],
        "artist_core_activity_light": [
            "artist_meta_birth_year",
            "artist_birth_generation_bin",
            "artist_meta_followers_log1p",
            "artist_meta_followers_missing",
            "artist_meta_for_sale_works_log1p",
            "artist_meta_for_sale_works_missing",
        ],
        "artwork_size_shape": [
            "width_cm",
            "height_cm",
            "area_cm2",
            "log_area",
            "aspect_ratio",
            "is_extreme_aspect_ratio",
        ],
        "artwork_size_material_support": [
            "width_cm",
            "height_cm",
            "area_cm2",
            "log_area",
            "aspect_ratio",
            "is_extreme_aspect_ratio",
            "medium_category",
            "support_category",
            "medium_support_bucket",
            "nant_support",
        ],
        "artist_artwork_core": [
            "artist_meta_birth_year",
            "artist_birth_generation_bin",
            "artist_meta_followers_log1p",
            "artist_meta_followers_missing",
            "artist_meta_for_sale_works_log1p",
            "artist_meta_for_sale_works_missing",
            "width_cm",
            "height_cm",
            "area_cm2",
            "log_area",
            "aspect_ratio",
            "is_extreme_aspect_ratio",
            "medium_category",
            "support_category",
            "medium_support_bucket",
            "nant_support",
        ],
        "artist_artwork_core_year_guard": [
            "artist_meta_birth_year",
            "artist_birth_generation_bin",
            "artist_meta_followers_log1p",
            "artist_meta_followers_missing",
            "artist_meta_for_sale_works_log1p",
            "artist_meta_for_sale_works_missing",
            "width_cm",
            "height_cm",
            "area_cm2",
            "log_area",
            "aspect_ratio",
            "is_extreme_aspect_ratio",
            "medium_category",
            "support_category",
            "medium_support_bucket",
            "nant_support",
            "artwork_year",
            "has_artwork_year",
            "artwork_year_missing",
        ],
    }
    policies = [
        ("hard_clip", 0.03, 0.50, "small_global"),
        ("hard_clip", 0.06, 0.25, "medium_global"),
        ("soft_tanh_cap", 0.06, 0.35, "medium_soft"),
        ("pred_bin_tail_guard", 0.06, 0.35, "mid_open_tail_guard"),
        ("pred_bin_tail_guard", 0.08, 0.25, "wide_low_strength"),
    ]
    rows: list[dict[str, object]] = []
    for set_name, features in feature_sets.items():
        for policy, cap, strength, guard in policies:
            if set_name.startswith("artist_") and cap > 0.03 and "artwork" not in set_name:
                continue
            rows.append(
                {
                    "candidate_family": "warm_huber_residual_feature_policy",
                    "feature_set": set_name,
                    "features": ",".join(features),
                    "model_kind": "huber",
                    "alpha": 0.01,
                    "epsilon": 1.35 if "material" in set_name or "artwork" in set_name else 1.05,
                    "correction_policy": policy,
                    "correction_cap": cap,
                    "correction_strength": strength,
                    "guard": guard,
                    "expected_role": expected_role(set_name, policy),
                }
            )
    return rows


def expected_role(set_name: str, policy: str) -> str:
    if set_name == "artist_core":
        return "안정 baseline 보정 후보"
    if set_name == "artist_core_activity_light":
        return "작가 메타 약한 추가 보정 후보"
    if set_name == "artwork_size_shape":
        return "작품 크기 중심 p95/MAPE 방어 후보"
    if set_name == "artwork_size_material_support":
        return "작품 크기+재료/지지체 결합 보정 후보"
    if set_name == "artist_artwork_core":
        return "작가+작품 통합 잔차 보정 주 후보"
    if set_name == "artist_artwork_core_year_guard":
        return "제작연도 신뢰도 guard 포함 진단 후보"
    return policy


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df[columns].iterrows():
        rows.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(rows)


def write_report(policy_df: pd.DataFrame, grid_df: pd.DataFrame) -> None:
    adopted = policy_df[policy_df["decision"].str.contains("adopt")]
    guarded = policy_df[~policy_df["decision"].str.contains("adopt")]
    report = [
        "# PP-FPOL1 Warm 작가+작품 피처 계수 보정 정책",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 지금까지의 Warm/Huber/작품/작가 실험 결과를 종합해 다음 Huber residual 보정 실험의 피처군과 보정값 후보를 고정",
        "- 기준: 현재 Warm 1순위 `blend_svcnum_ppv8_wsvc_0.70` 위에 잔차 보정을 얹는 정책",
        "",
        "## 1. 채택 피처군",
        "",
        markdown_table(
            adopted,
            [
                "korean_name",
                "decision",
                "role",
                "recommended_cap",
                "recommended_strength",
                "risk",
            ],
        ),
        "",
        "## 2. 보류/보조 피처군",
        "",
        markdown_table(
            guarded,
            [
                "korean_name",
                "decision",
                "role",
                "recommended_cap",
                "recommended_strength",
                "risk",
            ],
        ),
        "",
        "## 3. 피처별 근거",
        "",
        markdown_table(
            policy_df,
            [
                "korean_name",
                "columns",
                "evidence",
                "correction_policy",
            ],
        ),
        "",
        "## 4. 다음 실험 후보 grid",
        "",
        markdown_table(
            grid_df,
            [
                "feature_set",
                "correction_policy",
                "correction_cap",
                "correction_strength",
                "guard",
                "expected_role",
            ],
        ),
        "",
        "## 5. 결정 요약",
        "",
        "- 크기/면적은 작품 피처의 핵심 보정축으로 유지한다.",
        "- 재료/지지체는 단독 계수 보정 금지, 크기와 결합한 Huber residual 보정에서만 허용한다.",
        "- 작가 생년/세대와 팔로워/판매중 작품 수는 작가 메타의 안정 보정축으로 유지한다.",
        "- 갤러리/전시/에디션/깊이/제작연도는 메인 계수 보정보다 guard 또는 진단 피처로 우선 사용한다.",
        "- 다음 실험은 `artist_artwork_core`와 `artwork_size_material_support`를 중심으로 cap 0.06, strength 0.25~0.35, pred-bin tail guard를 검증한다.",
        "",
        "## 6. 산출물",
        "",
        "- `outputs/feature_group_correction_policy.csv`",
        "- `outputs/candidate_correction_grid.csv`",
        "- `outputs/policy_manifest.json`",
    ]
    md = "\n".join(report)
    (REPORT_DIR / "feature_correction_policy.md").write_text(md, encoding="utf-8")
    html_body = "<html><head><meta charset='utf-8'><style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.45;margin:32px;}table{border-collapse:collapse;width:100%;font-size:13px;}th,td{border:1px solid #ddd;padding:6px;vertical-align:top;}th{background:#f4f6f8;}code{background:#f6f8fa;padding:1px 3px;border-radius:3px;}</style></head><body>"
    html_body += "<h1>PP-FPOL1 Warm 작가+작품 피처 계수 보정 정책</h1>"
    for line in report[2:]:
        if line.startswith("## "):
            html_body += f"<h2>{html.escape(line[3:])}</h2>"
        elif line.startswith("- "):
            html_body += f"<p>{html.escape(line)}</p>"
        elif line.startswith("| "):
            continue
        elif line:
            html_body += f"<p>{html.escape(line)}</p>"
    html_body += "<h2>채택 피처군</h2>" + adopted.to_html(index=False, escape=True)
    html_body += "<h2>전체 정책</h2>" + policy_df.to_html(index=False, escape=True)
    html_body += "<h2>다음 실험 후보 grid</h2>" + grid_df.to_html(index=False, escape=True)
    html_body += "</body></html>"
    (REPORT_DIR / "feature_correction_policy.html").write_text(html_body, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    policy_df = pd.DataFrame(policy_rows())
    grid_df = pd.DataFrame(candidate_grid_rows())
    policy_df.to_csv(OUT_DIR / "feature_group_correction_policy.csv", index=False)
    grid_df.to_csv(OUT_DIR / "candidate_correction_grid.csv", index=False)
    manifest = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "policy_rows": int(len(policy_df)),
        "candidate_grid_rows": int(len(grid_df)),
        "source_experiments": [
            "PP-AMW9",
            "PP-AMW10",
            "PP-WCOEF",
            "PP-WHUBER7",
            "PRE-PP-W",
            "WARM_HUBER_interpretability_audit",
            "C10",
        ],
        "outputs": [
            "outputs/feature_group_correction_policy.csv",
            "outputs/candidate_correction_grid.csv",
            "reports/feature_correction_policy.md",
            "reports/feature_correction_policy.html",
        ],
    }
    (OUT_DIR / "policy_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(policy_df, grid_df)


if __name__ == "__main__":
    main()
