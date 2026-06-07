#!/usr/bin/env python3
"""Run PP-H22 provider agreement checks for operational search features."""
from __future__ import annotations

import html
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BASE_EXP_DIR = REPO / "experiments" / "track6"
EXP_ID = "PP-H22"
EXP_SLUG = "PP-H22_provider_agreement_stability"
TITLE = "Naver x Python 검색 Provider 일치도 검증"

STANDARDIZED_SEARCH_PATH = (
    REPO
    / "data"
    / "track6"
    / "external_search"
    / "operational"
    / "track6_artist_search_operational_standardized_latest.csv"
)
H20_PRED_PATH = BASE_EXP_DIR / "PP-H20_H26_search_feature_expansion" / "outputs" / "candidate_predictions.csv"
SUMMARY_PATH = BASE_EXP_DIR / "PP-H22_provider_agreement_summary_metrics.csv"

SOURCE_GROUPS = ["gallery_museum", "art_general", "exhibition", "market", "news", "social_blog", "other"]
CONTEXT_FLAGS = [
    "is_art_context",
    "is_exhibition_context",
    "is_gallery_context",
    "is_market_context",
    "is_social_context",
    "is_trusted_domain",
    "is_recent_context",
    "artist_name_in_result",
]


def provider_family(provider: str) -> str:
    provider = str(provider)
    if provider.startswith("naver_api"):
        return "naver_official"
    if provider == "naver_html":
        return "naver_html"
    if provider.startswith("python_") or provider.startswith("duckduckgo"):
        return "python_search"
    if provider.startswith("google"):
        return "google"
    return "other"


def metric_values(frame: pd.DataFrame, pred_col: str) -> dict[str, float]:
    if frame.empty:
        return {"n": 0, "MdAPE": np.nan, "MAPE": np.nan, "p95_APE": np.nan, "RMSE_log": np.nan}
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred_log = frame[pred_col].to_numpy(dtype=float)
    actual = frame["actual_price"].to_numpy(dtype=float)
    pred = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred_log) ** 2))),
    }


def load_standardized() -> pd.DataFrame:
    df = pd.read_csv(STANDARDIZED_SEARCH_PATH, low_memory=False)
    df["provider_family"] = df["provider"].map(provider_family)
    df = df[df["provider_family"].isin(["naver_official", "python_search"])].copy()
    df["has_result"] = df["has_result"].fillna(False).astype(bool)
    for col in SOURCE_GROUPS:
        df[f"source_group__{col}"] = df["source_group"].astype(str).eq(col).astype(float)
    for col in CONTEXT_FLAGS + ["is_homonym_context"]:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool).astype(float)
        else:
            df[col] = 0.0
    return df


def aggregate_provider(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    work = df[df["has_result"]].copy()
    if work.empty:
        return pd.DataFrame()
    aggregations: dict[str, tuple[str, Any]] = {
        "result_count": ("has_result", "sum"),
        "unique_domain_count": ("domain", lambda s: int(s.dropna().astype(str).nunique())),
        "template_count": ("query_template_id", lambda s: int(s.dropna().astype(str).nunique())),
        "domain_set": ("domain", lambda s: "|".join(sorted(set(s.dropna().astype(str))))),
    }
    for group in SOURCE_GROUPS:
        aggregations[f"source_group_{group}_ratio"] = (f"source_group__{group}", "mean")
    for flag in CONTEXT_FLAGS:
        aggregations[f"{flag}_ratio"] = (flag, "mean")
    aggregations["homonym_risk_ratio"] = ("is_homonym_context", "mean")
    out = work.groupby([*keys, "provider_family"], dropna=False).agg(**aggregations).reset_index()
    return out


def domain_jaccard(left: str, right: str) -> float:
    lset = set(str(left).split("|")) if pd.notna(left) and str(left) else set()
    rset = set(str(right).split("|")) if pd.notna(right) and str(right) else set()
    if not lset and not rset:
        return 0.0
    return len(lset & rset) / max(1, len(lset | rset))


def pairwise_agreement(agg: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if agg.empty:
        return pd.DataFrame()
    naver = agg[agg["provider_family"].eq("naver_official")].drop(columns=["provider_family"])
    python = agg[agg["provider_family"].eq("python_search")].drop(columns=["provider_family"])
    merged = naver.merge(python, on=keys, how="inner", suffixes=("_naver", "_python"))
    if merged.empty:
        return merged

    naver_source = merged[[f"source_group_{group}_ratio_naver" for group in SOURCE_GROUPS]].to_numpy(dtype=float)
    python_source = merged[[f"source_group_{group}_ratio_python" for group in SOURCE_GROUPS]].to_numpy(dtype=float)
    merged["source_group_similarity"] = 1.0 - 0.5 * np.abs(naver_source - python_source).sum(axis=1)
    merged["source_group_similarity"] = merged["source_group_similarity"].clip(0.0, 1.0)

    context_scores = []
    for flag in CONTEXT_FLAGS:
        context_scores.append(1.0 - np.abs(merged[f"{flag}_ratio_naver"] - merged[f"{flag}_ratio_python"]))
    merged["context_similarity"] = np.vstack(context_scores).mean(axis=0).clip(0.0, 1.0)

    merged["coverage_balance"] = (
        np.minimum(merged["result_count_naver"], merged["result_count_python"])
        / np.maximum(merged["result_count_naver"], merged["result_count_python"]).replace(0, np.nan)
    ).fillna(0.0)
    merged["domain_jaccard"] = [
        domain_jaccard(left, right)
        for left, right in zip(merged["domain_set_naver"], merged["domain_set_python"], strict=False)
    ]
    merged["homonym_safety"] = (1.0 - np.maximum(merged["homonym_risk_ratio_naver"], merged["homonym_risk_ratio_python"])).clip(0.0, 1.0)
    merged["provider_agreement_score"] = (
        0.35 * merged["source_group_similarity"]
        + 0.25 * merged["context_similarity"]
        + 0.15 * merged["coverage_balance"]
        + 0.15 * merged["domain_jaccard"]
        + 0.10 * merged["homonym_safety"]
    ).clip(0.0, 1.0)
    merged["provider_agreement_grade"] = np.select(
        [
            merged["provider_agreement_score"].ge(0.70),
            merged["provider_agreement_score"].ge(0.50),
        ],
        ["high", "medium"],
        default="low",
    )
    merged["provider_disagreement_risk_flag"] = (
        merged["provider_agreement_score"].lt(0.50)
        | merged["homonym_safety"].lt(0.80)
        | merged["context_similarity"].lt(0.65)
    )
    return merged


def build_error_slices(artist_agreement: pd.DataFrame) -> pd.DataFrame:
    preds = pd.read_csv(H20_PRED_PATH, low_memory=False)
    cols = [
        "artist_search_name",
        "provider_agreement_score",
        "provider_agreement_grade",
        "provider_disagreement_risk_flag",
        "source_group_similarity",
        "context_similarity",
        "domain_jaccard",
    ]
    merged = preds.merge(artist_agreement[cols], on="artist_search_name", how="left")
    merged["provider_agreement_grade"] = merged["provider_agreement_grade"].fillna("missing")
    merged["provider_disagreement_risk_flag"] = merged["provider_disagreement_risk_flag"].fillna(True).astype(bool)

    candidate_cols = {
        "pp_y2_base": "pred_log",
        "h23_news_median_cap0.2": "h23_news_median_cap0.2__pred_log",
        "h23_gallery_museum_median_cap0.2": "h23_gallery_museum_median_cap0.2__pred_log",
        "h23_social_blog_median_cap0.2": "h23_social_blog_median_cap0.2__pred_log",
    }
    rows: list[dict[str, Any]] = []
    for split, split_df in merged.groupby("split", dropna=False):
        for candidate, pred_col in candidate_cols.items():
            if pred_col not in split_df.columns:
                continue
            rows.append({
                "experiment_id": EXP_ID,
                "candidate": candidate,
                "split": split,
                "slice": "overall",
                "agreement_grade": "overall",
                **metric_values(split_df, pred_col),
            })
            for grade, grade_df in split_df.groupby("provider_agreement_grade", dropna=False):
                rows.append({
                    "experiment_id": EXP_ID,
                    "candidate": candidate,
                    "split": split,
                    "slice": f"agreement_grade={grade}",
                    "agreement_grade": grade,
                    **metric_values(grade_df, pred_col),
                })
            for flag, flag_df in split_df.groupby("provider_disagreement_risk_flag", dropna=False):
                rows.append({
                    "experiment_id": EXP_ID,
                    "candidate": candidate,
                    "split": split,
                    "slice": f"disagreement_risk={bool(flag)}",
                    "agreement_grade": "risk" if bool(flag) else "stable",
                    **metric_values(flag_df, pred_col),
                })
    return pd.DataFrame(rows)


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6g}"
    return str(value).replace("\n", " ").replace("|", "\\|")


def markdown_table(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df.empty:
        return "- 없음"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def render_report(
    provider_counts: pd.DataFrame,
    artist_agreement: pd.DataFrame,
    template_agreement: pd.DataFrame,
    error_slices: pd.DataFrame,
) -> tuple[str, str]:
    artist_grade = (
        artist_agreement.groupby("provider_agreement_grade", dropna=False)
        .agg(
            artist_count=("artist_search_name", "size"),
            agreement_median=("provider_agreement_score", "median"),
            source_similarity_median=("source_group_similarity", "median"),
            context_similarity_median=("context_similarity", "median"),
            domain_jaccard_median=("domain_jaccard", "median"),
            risk_rate=("provider_disagreement_risk_flag", "mean"),
        )
        .reset_index()
        .sort_values("provider_agreement_grade")
    )
    test_slices = error_slices[error_slices["split"].eq("test")].copy()
    test_slices = test_slices.sort_values(["candidate", "slice"])
    top_low = artist_agreement.sort_values("provider_agreement_score").head(20)
    cols = [
        "artist_search_name",
        "provider_agreement_score",
        "provider_agreement_grade",
        "source_group_similarity",
        "context_similarity",
        "domain_jaccard",
        "coverage_balance",
        "homonym_safety",
        "provider_disagreement_risk_flag",
    ]
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "- 목적: Naver 공식 검색 API와 Python 검색 provider가 같은 작가에 대해 일관된 외부 신호를 주는지 검증한다.",
        "- 핵심 산출물: 작가별 provider agreement score, disagreement risk flag, agreement 등급별 예측 오차.",
        "",
        "## Provider 수집 현황",
        "",
        markdown_table(provider_counts),
        "",
        "## 작가별 일치도 등급 요약",
        "",
        markdown_table(artist_grade),
        "",
        "## Test 오차 Slice",
        "",
        markdown_table(test_slices[["candidate", "slice", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]], max_rows=80),
        "",
        "## 일치도 낮은 작가 우선 검수 목록",
        "",
        markdown_table(top_low[cols], max_rows=20),
        "",
        "## 해석",
        "",
        "- agreement score가 높다는 것은 두 provider가 비슷한 source group, 미술 문맥, 도메인 범위를 반환했다는 뜻이다.",
        "- agreement score가 낮은 작가는 동명이인, 무관 검색 결과, provider별 편향 가능성이 있어 가격점 예측 직접 반영보다 신뢰도 하향 또는 수동 검수 후보로 보는 것이 안전하다.",
        "- domain jaccard는 검색 엔진 특성상 낮게 나올 수 있으므로 source/context similarity를 더 중요하게 해석한다.",
        "",
    ]
    md = "\n".join(lines)
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<h2>Provider 수집 현황</h2>{provider_counts.to_html(index=False, escape=True)}
<h2>작가별 일치도 등급 요약</h2>{artist_grade.to_html(index=False, escape=True)}
<h2>작가별 일치도</h2>{artist_agreement.to_html(index=False, escape=True)}
<h2>Template별 일치도</h2>{template_agreement.to_html(index=False, escape=True)}
<h2>오차 Slice</h2>{error_slices.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    start = time.time()
    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    standard = load_standardized()
    provider_counts = (
        standard.groupby(["provider_family", "provider"], dropna=False)
        .agg(
            rows=("provider", "size"),
            result_rows=("has_result", "sum"),
            artist_count=("artist_search_name", "nunique"),
            template_count=("query_template_id", "nunique"),
        )
        .reset_index()
    )
    artist_agg = aggregate_provider(standard, ["artist_search_name"])
    template_agg = aggregate_provider(standard, ["artist_search_name", "query_template_id"])
    artist_agreement = pairwise_agreement(artist_agg, ["artist_search_name"])
    template_agreement = pairwise_agreement(template_agg, ["artist_search_name", "query_template_id"])
    if artist_agreement.empty:
        raise ValueError("provider agreement is empty; need both naver_official and python_search results")

    error_slices = build_error_slices(artist_agreement)

    provider_counts.to_csv(exp_dir / "outputs" / "provider_counts.csv", index=False)
    artist_agreement.to_csv(exp_dir / "outputs" / "provider_agreement_by_artist.csv", index=False)
    template_agreement.to_csv(exp_dir / "outputs" / "provider_agreement_by_template.csv", index=False)
    error_slices.to_csv(exp_dir / "outputs" / "agreement_error_slices.csv", index=False)
    error_slices.to_csv(SUMMARY_PATH, index=False)

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "standardized_search": str(STANDARDIZED_SEARCH_PATH.relative_to(REPO)),
        "base_predictions": str(H20_PRED_PATH.relative_to(REPO)),
        "score_formula": "0.35 source similarity + 0.25 context similarity + 0.15 coverage balance + 0.15 domain jaccard + 0.10 homonym safety",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(provider_counts, artist_agreement, template_agreement, error_slices)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed in {time.time() - start:.2f}s\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "experiment": str(exp_dir.relative_to(REPO)),
        "artist_agreement": str((exp_dir / "outputs" / "provider_agreement_by_artist.csv").relative_to(REPO)),
        "error_slices": str((exp_dir / "outputs" / "agreement_error_slices.csv").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
