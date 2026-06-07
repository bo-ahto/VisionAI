#!/usr/bin/env python3
"""Run PP-H12 search-result artist match and disambiguation triage.

This script does not replace human review. It creates a reproducible first-pass
label and a review queue from PP-H11 operational search snapshots so the team can
decide which search features are safe enough for model or service use.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BASE_EXP_DIR = REPO / "experiments" / "track6"
EXP_ID = "PP-H12"
EXP_SLUG = "PP-H12_search_match_disambiguation_review"
TITLE = "검색 결과 작가 일치/동명이인 판정 검수"

SEARCH_DIR = REPO / "data" / "track6" / "external_search" / "operational"
SNAPSHOT_PATH = SEARCH_DIR / "track6_artist_search_operational_snapshot_latest.csv"
STANDARDIZED_PATH = SEARCH_DIR / "track6_artist_search_operational_standardized_latest.csv"

ART_SOURCE_GROUPS = {"gallery_museum", "exhibition", "art_general", "market"}
WEAK_SOURCE_GROUPS = {"social_blog", "news"}


def norm_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", "", str(value)).lower()


def contains_name(row: pd.Series) -> bool:
    name = norm_text(row.get("artist_search_name", ""))
    text = norm_text(f"{row.get('title', '')} {row.get('snippet', '')} {row.get('url', '')}")
    return bool(name and name in text)


def label_result(row: pd.Series) -> tuple[str, str, float]:
    has_result = bool(row.get("has_result", False))
    if not has_result:
        return "missing", "검색 결과 없음", 0.0

    name_match = bool(row.get("artist_name_in_result", False)) or contains_name(row)
    is_art = bool(row.get("is_art_context", False))
    is_exhibition = bool(row.get("is_exhibition_context", False))
    is_gallery = bool(row.get("is_gallery_context", False))
    is_market = bool(row.get("is_market_context", False))
    is_homonym = bool(row.get("is_homonym_context", False))
    trusted = bool(row.get("is_trusted_domain", False))
    source_group = str(row.get("source_group", ""))
    rank = float(row.get("rank", 99) or 99)

    context_score = 0.0
    if name_match:
        context_score += 0.40
    if is_art:
        context_score += 0.20
    if is_exhibition:
        context_score += 0.15
    if is_gallery:
        context_score += 0.15
    if is_market:
        context_score += 0.10
    if trusted:
        context_score += 0.10
    if source_group in ART_SOURCE_GROUPS:
        context_score += 0.05
    if source_group in WEAK_SOURCE_GROUPS:
        context_score -= 0.03
    if is_homonym:
        context_score -= 0.35
    if rank <= 2:
        context_score += 0.04
    context_score = float(np.clip(context_score, 0.0, 1.0))

    reasons = []
    if name_match:
        reasons.append("작가명 포함")
    if is_art:
        reasons.append("미술 문맥")
    if is_exhibition:
        reasons.append("전시 문맥")
    if is_gallery:
        reasons.append("갤러리/미술관 문맥")
    if is_market:
        reasons.append("시장/경매 문맥")
    if trusted:
        reasons.append("신뢰 도메인")
    if is_homonym:
        reasons.append("동명이인 위험")
    if not reasons:
        reasons.append("작가/미술 문맥 약함")

    if is_homonym and not (name_match and (is_art or is_gallery or is_exhibition)):
        return "homonym", ", ".join(reasons), context_score
    if name_match and (is_art or is_exhibition or is_gallery or is_market) and context_score >= 0.55:
        return "match_artist", ", ".join(reasons), context_score
    if (name_match or is_art) and context_score >= 0.30:
        return "partial_match", ", ".join(reasons), context_score
    return "irrelevant", ", ".join(reasons), context_score


def grade_artist(group: pd.DataFrame, snapshot_row: pd.Series) -> tuple[str, str, float, str]:
    valid = group[group["auto_result_label"].ne("missing")].copy()
    if valid.empty:
        return "missing", "검색 결과 없음", 0.0, "manual_review_required"

    n = float(len(valid))
    match_rate = float(valid["auto_result_label"].eq("match_artist").mean())
    partial_rate = float(valid["auto_result_label"].eq("partial_match").mean())
    homonym_rate = float(valid["auto_result_label"].eq("homonym").mean())
    irrelevant_rate = float(valid["auto_result_label"].eq("irrelevant").mean())
    score = float(valid["match_confidence_score"].mean())
    search_quality = float(snapshot_row.get("search_quality_score", 0.0))
    search_grade = str(snapshot_row.get("search_quality_grade", "missing"))

    combined = 0.65 * score + 0.35 * search_quality
    reasons = [
        f"match_rate={match_rate:.3f}",
        f"partial_rate={partial_rate:.3f}",
        f"homonym_rate={homonym_rate:.3f}",
        f"irrelevant_rate={irrelevant_rate:.3f}",
        f"h11_grade={search_grade}",
    ]

    if homonym_rate >= 0.20:
        return "homonym_risk", ", ".join(reasons), combined, "manual_review_required"
    if match_rate >= 0.35 and combined >= 0.45:
        return "usable_match", ", ".join(reasons), combined, "candidate_for_h14_h18"
    if match_rate + partial_rate >= 0.50 and combined >= 0.35:
        return "weak_match", ", ".join(reasons), combined, "confidence_only_or_manual_review"
    return "low_match", ", ".join(reasons), combined, "do_not_use_for_point_prediction"


def build_outputs(snapshot: pd.DataFrame, standard: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result_rows = standard.copy()
    labels = result_rows.apply(label_result, axis=1, result_type="expand")
    labels.columns = ["auto_result_label", "auto_result_reason", "match_confidence_score"]
    result_rows = pd.concat([result_rows, labels], axis=1)

    artist_rows = []
    snapshot_by_artist = snapshot.set_index("artist_search_name", drop=False)
    for artist_name, group in result_rows.groupby("artist_search_name", dropna=False):
        snap = snapshot_by_artist.loc[artist_name] if artist_name in snapshot_by_artist.index else pd.Series(dtype=object)
        artist_label, reason, confidence, action = grade_artist(group, snap)
        counts = group["auto_result_label"].value_counts().to_dict()
        artist_rows.append({
            "artist_search_name": artist_name,
            "auto_artist_label": artist_label,
            "recommended_action": action,
            "artist_match_confidence": confidence,
            "auto_artist_reason": reason,
            "result_count": int(group["has_result"].sum()),
            "match_artist_count": int(counts.get("match_artist", 0)),
            "partial_match_count": int(counts.get("partial_match", 0)),
            "homonym_count": int(counts.get("homonym", 0)),
            "irrelevant_count": int(counts.get("irrelevant", 0)),
            "missing_count": int(counts.get("missing", 0)),
            "h11_search_quality_grade": snap.get("search_quality_grade", "missing"),
            "h11_search_quality_score": float(snap.get("search_quality_score", 0.0) or 0.0),
            "h11_search_art_match_ratio": float(snap.get("search_art_match_ratio", 0.0) or 0.0),
            "h11_search_name_match_ratio": float(snap.get("search_name_match_ratio", 0.0) or 0.0),
            "train_row_count": int(snap.get("train_row_count", 0) or 0),
            "validation_row_count": int(snap.get("validation_row_count", 0) or 0),
            "test_row_count": int(snap.get("test_row_count", 0) or 0),
            "total_row_count": int(snap.get("total_row_count", 0) or 0),
        })
    artist_review = pd.DataFrame(artist_rows).sort_values(
        ["recommended_action", "artist_match_confidence", "total_row_count"],
        ascending=[True, False, False],
    )

    priority = artist_review.copy()
    priority["manual_review_priority"] = np.select(
        [
            priority["auto_artist_label"].eq("homonym_risk"),
            priority["auto_artist_label"].eq("weak_match"),
            priority["auto_artist_label"].eq("low_match"),
            priority["h11_search_quality_grade"].eq("medium") & priority["auto_artist_label"].ne("usable_match"),
        ],
        ["P0_homonym", "P1_weak_match", "P2_low_match", "P1_medium_conflict"],
        default="P3_spot_check",
    )
    priority = priority.sort_values(
        ["manual_review_priority", "total_row_count", "artist_match_confidence"],
        ascending=[True, False, True],
    )

    review_rows = []
    for artist_name in priority["artist_search_name"].tolist():
        group = result_rows[result_rows["artist_search_name"].eq(artist_name)].copy()
        group["_review_sort"] = np.select(
            [
                group["auto_result_label"].eq("homonym"),
                group["auto_result_label"].eq("irrelevant"),
                group["auto_result_label"].eq("partial_match"),
                group["auto_result_label"].eq("match_artist"),
            ],
            [0, 1, 2, 3],
            default=4,
        )
        selected = group.sort_values(["_review_sort", "rank"]).head(3)
        review_rows.append(selected)
    manual_template = pd.concat(review_rows, ignore_index=True) if review_rows else pd.DataFrame()
    manual_template = manual_template.drop(columns=[col for col in ["_review_sort"] if col in manual_template.columns])
    manual_template.insert(0, "manual_label", "")
    manual_template.insert(1, "manual_notes", "")
    manual_template.insert(2, "manual_reviewer", "")

    metrics_rows = [
        {
            "experiment_id": EXP_ID,
            "candidate": "result_auto_label_distribution",
            "scope": "search_result",
            "n": len(result_rows),
            "match_artist_rate": float(result_rows["auto_result_label"].eq("match_artist").mean()),
            "partial_match_rate": float(result_rows["auto_result_label"].eq("partial_match").mean()),
            "homonym_rate": float(result_rows["auto_result_label"].eq("homonym").mean()),
            "irrelevant_rate": float(result_rows["auto_result_label"].eq("irrelevant").mean()),
            "mean_confidence": float(result_rows["match_confidence_score"].mean()),
        },
        {
            "experiment_id": EXP_ID,
            "candidate": "artist_auto_label_distribution",
            "scope": "artist",
            "n": len(artist_review),
            "usable_match_rate": float(artist_review["auto_artist_label"].eq("usable_match").mean()),
            "weak_match_rate": float(artist_review["auto_artist_label"].eq("weak_match").mean()),
            "low_match_rate": float(artist_review["auto_artist_label"].eq("low_match").mean()),
            "homonym_risk_rate": float(artist_review["auto_artist_label"].eq("homonym_risk").mean()),
            "mean_confidence": float(artist_review["artist_match_confidence"].mean()),
        },
    ]
    for label, count in artist_review["recommended_action"].value_counts().items():
        metrics_rows.append({
            "experiment_id": EXP_ID,
            "candidate": f"recommended_action__{label}",
            "scope": "artist",
            "n": int(count),
            "rate": float(count / max(len(artist_review), 1)),
        })
    metrics = pd.DataFrame(metrics_rows)
    return result_rows, artist_review, manual_template, metrics


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "- 없음"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("\n", " ").replace("|", "\\|")


def render_report(result_rows: pd.DataFrame, artist_review: pd.DataFrame, manual_template: pd.DataFrame, metrics: pd.DataFrame, config: dict[str, Any]) -> tuple[str, str]:
    artist_counts = artist_review["auto_artist_label"].value_counts().rename_axis("auto_artist_label").reset_index(name="artist_count")
    action_counts = artist_review["recommended_action"].value_counts().rename_axis("recommended_action").reset_index(name="artist_count")
    result_counts = result_rows["auto_result_label"].value_counts().rename_axis("auto_result_label").reset_index(name="result_count")
    priority_counts = (
        artist_review.assign(
            manual_review_priority=np.select(
                [
                    artist_review["auto_artist_label"].eq("homonym_risk"),
                    artist_review["auto_artist_label"].eq("weak_match"),
                    artist_review["auto_artist_label"].eq("low_match"),
                ],
                ["P0_homonym", "P1_weak_match", "P2_low_match"],
                default="P3_spot_check",
            )
        )["manual_review_priority"].value_counts().rename_axis("manual_review_priority").reset_index(name="artist_count")
    )
    top_usable = artist_review.sort_values("artist_match_confidence", ascending=False)[
        ["artist_search_name", "auto_artist_label", "recommended_action", "artist_match_confidence", "match_artist_count", "partial_match_count", "irrelevant_count", "h11_search_quality_grade"]
    ].head(15)
    needs_review = artist_review[artist_review["recommended_action"].ne("candidate_for_h14_h18")].sort_values(
        ["total_row_count", "artist_match_confidence"], ascending=[False, True]
    )[
        ["artist_search_name", "auto_artist_label", "recommended_action", "artist_match_confidence", "match_artist_count", "partial_match_count", "irrelevant_count", "h11_search_quality_grade", "total_row_count"]
    ].head(20)

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 목적",
        "",
        "- PP-H11에서 수집한 검색 결과가 해당 작가 본인과 관련 있는지 자동 판정 초안을 만든다.",
        "- 사람이 검수할 우선순위 큐를 생성해 H13/H14/H18에서 검색 피처를 안전하게 쓸 수 있는 기준을 만든다.",
        "- 이 결과는 최종 정답 라벨이 아니라 `수동 검수 전 1차 판정`이다.",
        "",
        "## 실행 설정",
        "",
        markdown_table(pd.DataFrame([config]).T.reset_index().rename(columns={"index": "항목", 0: "값"}), max_rows=80),
        "",
        "## 결과 단위 자동 라벨 분포",
        "",
        markdown_table(result_counts),
        "",
        "## 작가 단위 자동 라벨 분포",
        "",
        markdown_table(artist_counts),
        "",
        "## 추천 액션 분포",
        "",
        markdown_table(action_counts),
        "",
        "## 검수 우선순위 분포",
        "",
        markdown_table(priority_counts),
        "",
        "## H14/H18 후보 작가 상위",
        "",
        markdown_table(top_usable),
        "",
        "## 검수 필요 작가 상위",
        "",
        markdown_table(needs_review),
        "",
        "## 해석",
        "",
        "- `candidate_for_h14_h18`는 검색 결과를 가격점 예측에 바로 넣는다는 뜻이 아니라, 신뢰도/가격 범위/q-width 보정 실험에 사용할 수 있는 후보라는 뜻이다.",
        "- `confidence_only_or_manual_review`는 검색 신호가 일부 있으나 작가 본인 여부를 사람이 확인해야 한다.",
        "- `do_not_use_for_point_prediction`은 검색 결과가 있더라도 모델 점 예측 피처로 직접 쓰면 노이즈가 될 가능성이 크다.",
        "- 다음 단계는 manual review template의 `manual_label`을 채운 뒤 threshold를 다시 보정하는 것이다.",
        "",
    ]
    md = "\n".join(lines)
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{EXP_ID}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}.note{{background:#f8fafc;border-left:4px solid #667085;padding:10px 12px}}</style></head>
<body><h1>{EXP_ID} {TITLE}</h1>
<div class="note">이 결과는 수동 검수 전 자동 판정 초안입니다. 최종 모델 반영 전 manual_label 검수가 필요합니다.</div>
<h2>실행 설정</h2>{pd.DataFrame([config]).T.reset_index().rename(columns={'index':'항목',0:'값'}).to_html(index=False, escape=True)}
<h2>결과 단위 자동 라벨 분포</h2>{result_counts.to_html(index=False, escape=True)}
<h2>작가 단위 자동 라벨 분포</h2>{artist_counts.to_html(index=False, escape=True)}
<h2>추천 액션 분포</h2>{action_counts.to_html(index=False, escape=True)}
<h2>검수 우선순위 분포</h2>{priority_counts.to_html(index=False, escape=True)}
<h2>H14/H18 후보 작가 상위</h2>{top_usable.to_html(index=False, escape=True)}
<h2>검수 필요 작가 상위</h2>{needs_review.to_html(index=False, escape=True)}
<h2>Metrics</h2>{metrics.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    start = datetime.now()
    if not SNAPSHOT_PATH.exists():
        raise FileNotFoundError(f"Missing PP-H11 snapshot: {SNAPSHOT_PATH}")
    if not STANDARDIZED_PATH.exists():
        raise FileNotFoundError(f"Missing PP-H11 standardized result: {STANDARDIZED_PATH}")

    snapshot = pd.read_csv(SNAPSHOT_PATH, low_memory=False)
    standard = pd.read_csv(STANDARDIZED_PATH, low_memory=False)
    result_rows, artist_review, manual_template, metrics = build_outputs(snapshot, standard)

    run_id = f"pp_h12_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    result_path = exp_dir / "outputs" / "search_result_auto_labels.csv"
    artist_path = exp_dir / "outputs" / "artist_match_review_queue.csv"
    manual_path = exp_dir / "outputs" / "manual_review_template.csv"
    metrics_path = exp_dir / "outputs" / "metrics.csv"
    result_rows.to_csv(result_path, index=False)
    artist_review.to_csv(artist_path, index=False)
    manual_template.to_csv(manual_path, index=False)
    metrics.to_csv(metrics_path, index=False)
    metrics.to_csv(BASE_EXP_DIR / "PP-H12_search_match_summary_metrics.csv", index=False)

    usable_n = int(artist_review["recommended_action"].eq("candidate_for_h14_h18").sum())
    review_n = int(artist_review["recommended_action"].ne("candidate_for_h14_h18").sum())
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": run_id,
        "started_at": start.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "input_snapshot": str(SNAPSHOT_PATH.relative_to(REPO)),
        "input_standardized": str(STANDARDIZED_PATH.relative_to(REPO)),
        "result_rows": int(len(result_rows)),
        "artist_rows": int(len(artist_review)),
        "manual_review_rows": int(len(manual_template)),
        "candidate_for_h14_h18_artist_n": usable_n,
        "manual_or_reject_artist_n": review_n,
        "note": "Automatic triage only. Fill manual_label before using as final artist-match ground truth.",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    output_paths = {
        "search_result_auto_labels": str(result_path.relative_to(REPO)),
        "artist_match_review_queue": str(artist_path.relative_to(REPO)),
        "manual_review_template": str(manual_path.relative_to(REPO)),
        "metrics": str(metrics_path.relative_to(REPO)),
        "experiment_dir": str(exp_dir.relative_to(REPO)),
    }
    (exp_dir / "artifacts" / "output_paths.json").write_text(json.dumps(output_paths, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(result_rows, artist_review, manual_template, metrics, config)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "artist_n": int(len(artist_review)),
        "result_n": int(len(result_rows)),
        "candidate_for_h14_h18_artist_n": usable_n,
        "manual_or_reject_artist_n": review_n,
        "manual_review_template": str(manual_path.relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
