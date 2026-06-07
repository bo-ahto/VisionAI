#!/usr/bin/env python3
"""Create a stricter PP-H12 review-label draft from operational search results.

This is not a substitute for human review. It removes obvious search-UI/noise
results and produces a conservative artist-level queue for rerunning H14/H18.
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
EXP_ID = "PP-H12B"
EXP_SLUG = "PP-H12B_search_match_review_label_refinement"
TITLE = "검색 결과 작가 일치 라벨 검수 초안 v2"

H12_RESULT_LABELS = REPO / "experiments" / "track6" / "PP-H12_search_match_disambiguation_review" / "outputs" / "search_result_auto_labels.csv"
H12_ARTIST_QUEUE = REPO / "experiments" / "track6" / "PP-H12_search_match_disambiguation_review" / "outputs" / "artist_match_review_queue.csv"

NOISE_DOMAINS = {
    "myprofile.naver.com",
    "m.pay.naver.com",
    "mkt.naver.com",
    "help.naver.com",
    "keep.naver.com",
    "nid.naver.com",
}
NOISE_TITLE_PATTERNS = [
    "인물정보 본인참여",
    "직업별 등재기준",
    "본인참여 수정신청",
    "네이버 아이디 하나로",
    "오늘의 경험, 클립으로",
    "검색옵션",
    "Keep에 바로가기",
]
ART_DOMAINS = [
    "gallery",
    "museum",
    "opengallery",
    "ecorockgallery",
    "daljin",
    "art",
    "auction",
    "k-artmarket",
    "seoulauction",
    "k-auction",
    "daarts",
    "arko",
    "artnet",
    "artsy",
]


def norm(value: Any) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", "", str(value)).lower()


def has_artist_name(row: pd.Series) -> bool:
    name = norm(row.get("artist_search_name", ""))
    text = norm(f"{row.get('title', '')} {row.get('snippet', '')} {row.get('url', '')}")
    return bool(name and name in text)


def is_noise(row: pd.Series) -> bool:
    domain = str(row.get("domain", "")).lower()
    title = str(row.get("title", ""))
    if domain in NOISE_DOMAINS:
        return True
    return any(pattern in title for pattern in NOISE_TITLE_PATTERNS)


def art_domain(row: pd.Series) -> bool:
    domain = str(row.get("domain", "")).lower()
    return any(token in domain for token in ART_DOMAINS)


def draft_label(row: pd.Series) -> tuple[str, str, float]:
    if not bool(row.get("has_result", False)):
        return "missing", "검색 결과 없음", 0.0
    if is_noise(row):
        return "irrelevant", "검색 UI/프로필/결제 노이즈", 0.0

    name_match = bool(row.get("artist_name_in_result", False)) or has_artist_name(row)
    is_art = bool(row.get("is_art_context", False))
    is_exhibition = bool(row.get("is_exhibition_context", False))
    is_gallery = bool(row.get("is_gallery_context", False))
    is_market = bool(row.get("is_market_context", False))
    is_homonym = bool(row.get("is_homonym_context", False))
    domain_art = art_domain(row)
    source_group = str(row.get("source_group", ""))
    original = str(row.get("auto_result_label", ""))

    score = 0.0
    reasons = []
    if name_match:
        score += 0.42
        reasons.append("작가명 포함")
    if is_art:
        score += 0.18
        reasons.append("미술 문맥")
    if is_exhibition:
        score += 0.14
        reasons.append("전시 문맥")
    if is_gallery:
        score += 0.14
        reasons.append("갤러리 문맥")
    if is_market:
        score += 0.10
        reasons.append("시장/경매 문맥")
    if domain_art:
        score += 0.08
        reasons.append("미술 도메인")
    if source_group in {"social_blog", "news"} and not name_match:
        score -= 0.06
        reasons.append("약한 출처+작가명 없음")
    if is_homonym:
        score -= 0.45
        reasons.append("동명이인 위험")
    score = float(np.clip(score, 0.0, 1.0))

    if is_homonym and not (name_match and (is_art or is_gallery or is_exhibition or is_market)):
        return "homonym", ", ".join(reasons), score
    if name_match and (is_art or is_exhibition or is_gallery or is_market) and score >= 0.58:
        return "match_artist", ", ".join(reasons), score
    if original == "match_artist" and name_match and score >= 0.48:
        return "match_artist", ", ".join(reasons + ["기존 match 유지"]), score
    if name_match and (is_art or domain_art) and score >= 0.34:
        return "partial_match", ", ".join(reasons), score
    if not name_match and (is_gallery or is_exhibition or is_market) and domain_art and score >= 0.32:
        return "partial_match", ", ".join(reasons + ["작가명 없음"]), score
    return "irrelevant", ", ".join(reasons or ["작가/미술 문맥 부족"]), score


def aggregate_artist(results: pd.DataFrame, original_artist: pd.DataFrame) -> pd.DataFrame:
    orig = original_artist.set_index("artist_search_name", drop=False)
    rows = []
    for artist_name, group in results.groupby("artist_search_name", dropna=False):
        counts = group["review_label_draft"].value_counts().to_dict()
        n = max(int(group["has_result"].sum()), 1)
        match_count = int(counts.get("match_artist", 0))
        partial_count = int(counts.get("partial_match", 0))
        homonym_count = int(counts.get("homonym", 0))
        irrelevant_count = int(counts.get("irrelevant", 0))
        match_rate = match_count / n
        usable_rate = (match_count + 0.5 * partial_count) / n
        homonym_rate = homonym_count / n
        confidence = float(group["review_confidence_score"].mean())
        if artist_name in orig.index:
            base = orig.loc[artist_name].to_dict()
        else:
            base = {"artist_search_name": artist_name}

        if homonym_rate >= 0.20:
            label = "homonym_risk"
            action = "manual_review_required"
        elif match_rate >= 0.35 and usable_rate >= 0.48 and confidence >= 0.42:
            label = "usable_match"
            action = "candidate_for_h14_h18"
        elif usable_rate >= 0.34 and confidence >= 0.28:
            label = "weak_match"
            action = "confidence_only_or_manual_review"
        else:
            label = "low_match"
            action = "do_not_use_for_point_prediction"

        rows.append({
            **base,
            "auto_artist_label": label,
            "recommended_action": action,
            "artist_match_confidence": confidence,
            "auto_artist_reason": (
                f"draft_match_rate={match_rate:.3f}, draft_usable_rate={usable_rate:.3f}, "
                f"draft_homonym_rate={homonym_rate:.3f}"
            ),
            "result_count": n,
            "match_artist_count": match_count,
            "partial_match_count": partial_count,
            "homonym_count": homonym_count,
            "irrelevant_count": irrelevant_count,
            "missing_count": int(counts.get("missing", 0)),
        })
    return pd.DataFrame(rows)


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


def render_report(results: pd.DataFrame, artist_queue: pd.DataFrame, metrics: pd.DataFrame, config: dict[str, Any]) -> tuple[str, str]:
    result_counts = results["review_label_draft"].value_counts().rename_axis("review_label_draft").reset_index(name="result_count")
    artist_counts = artist_queue["auto_artist_label"].value_counts().rename_axis("auto_artist_label").reset_index(name="artist_count")
    action_counts = artist_queue["recommended_action"].value_counts().rename_axis("recommended_action").reset_index(name="artist_count")
    candidates = artist_queue[artist_queue["recommended_action"].eq("candidate_for_h14_h18")].sort_values("artist_match_confidence", ascending=False)[
        ["artist_search_name", "auto_artist_label", "recommended_action", "artist_match_confidence", "match_artist_count", "partial_match_count", "irrelevant_count", "h11_search_quality_grade", "total_row_count"]
    ].head(20)
    review = artist_queue[artist_queue["recommended_action"].ne("candidate_for_h14_h18")].sort_values(["total_row_count", "artist_match_confidence"], ascending=[False, True])[
        ["artist_search_name", "auto_artist_label", "recommended_action", "artist_match_confidence", "match_artist_count", "partial_match_count", "irrelevant_count", "h11_search_quality_grade", "total_row_count"]
    ].head(20)
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 목적",
        "",
        "- H12 자동 라벨에서 검색 UI/프로필/결제 노이즈를 보수적으로 제거한다.",
        "- 사람이 확정하기 전 사용할 수 있는 검수 초안 v2 작가 큐를 만든다.",
        "- 이 결과 역시 최종 수동 검수 라벨은 아니며, H14/H18 재실행용 보수적 후보군이다.",
        "",
        "## 실행 설정",
        "",
        markdown_table(pd.DataFrame([config]).T.reset_index().rename(columns={"index": "항목", 0: "값"}), max_rows=80),
        "",
        "## 결과 라벨 분포",
        "",
        markdown_table(result_counts),
        "",
        "## 작가 라벨 분포",
        "",
        markdown_table(artist_counts),
        "",
        "## 추천 액션 분포",
        "",
        markdown_table(action_counts),
        "",
        "## H14/H18 후보",
        "",
        markdown_table(candidates),
        "",
        "## 검수/제외 후보",
        "",
        markdown_table(review),
        "",
        "## Metrics",
        "",
        markdown_table(metrics),
        "",
    ]
    md = "\n".join(lines)
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{EXP_ID}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}.note{{background:#f8fafc;border-left:4px solid #667085;padding:10px 12px}}</style></head>
<body><h1>{EXP_ID} {TITLE}</h1><div class="note">수동 확정 전 검수 초안입니다. 최종 채택 전 사람 검수가 필요합니다.</div>
<h2>실행 설정</h2>{pd.DataFrame([config]).T.reset_index().rename(columns={'index':'항목',0:'값'}).to_html(index=False, escape=True)}
<h2>결과 라벨 분포</h2>{result_counts.to_html(index=False, escape=True)}
<h2>작가 라벨 분포</h2>{artist_counts.to_html(index=False, escape=True)}
<h2>추천 액션 분포</h2>{action_counts.to_html(index=False, escape=True)}
<h2>H14/H18 후보</h2>{candidates.to_html(index=False, escape=True)}
<h2>검수/제외 후보</h2>{review.to_html(index=False, escape=True)}
<h2>Metrics</h2>{metrics.to_html(index=False, escape=True)}</body></html>"""
    return md, html


def main() -> None:
    start = datetime.now()
    results = pd.read_csv(H12_RESULT_LABELS, low_memory=False)
    original_artist = pd.read_csv(H12_ARTIST_QUEUE, low_memory=False)
    drafts = results.apply(draft_label, axis=1, result_type="expand")
    drafts.columns = ["review_label_draft", "review_label_reason", "review_confidence_score"]
    reviewed_results = pd.concat([results, drafts], axis=1)
    refined_artist = aggregate_artist(reviewed_results, original_artist)
    refined_artist = refined_artist.sort_values(["recommended_action", "artist_match_confidence", "total_row_count"], ascending=[True, False, False])

    metrics = pd.DataFrame([
        {
            "experiment_id": EXP_ID,
            "candidate": "result_label_draft_distribution",
            "scope": "search_result",
            "n": int(len(reviewed_results)),
            "match_artist_rate": float(reviewed_results["review_label_draft"].eq("match_artist").mean()),
            "partial_match_rate": float(reviewed_results["review_label_draft"].eq("partial_match").mean()),
            "homonym_rate": float(reviewed_results["review_label_draft"].eq("homonym").mean()),
            "irrelevant_rate": float(reviewed_results["review_label_draft"].eq("irrelevant").mean()),
            "mean_confidence": float(reviewed_results["review_confidence_score"].mean()),
        },
        {
            "experiment_id": EXP_ID,
            "candidate": "artist_label_draft_distribution",
            "scope": "artist",
            "n": int(len(refined_artist)),
            "usable_match_rate": float(refined_artist["auto_artist_label"].eq("usable_match").mean()),
            "weak_match_rate": float(refined_artist["auto_artist_label"].eq("weak_match").mean()),
            "low_match_rate": float(refined_artist["auto_artist_label"].eq("low_match").mean()),
            "homonym_risk_rate": float(refined_artist["auto_artist_label"].eq("homonym_risk").mean()),
            "mean_confidence": float(refined_artist["artist_match_confidence"].mean()),
        },
    ])

    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    result_path = exp_dir / "outputs" / "search_result_review_label_draft.csv"
    artist_path = exp_dir / "outputs" / "artist_match_review_queue_refined.csv"
    metrics_path = exp_dir / "outputs" / "metrics.csv"
    reviewed_results.to_csv(result_path, index=False)
    refined_artist.to_csv(artist_path, index=False)
    metrics.to_csv(metrics_path, index=False)
    metrics.to_csv(BASE_EXP_DIR / "PP-H12B_search_match_refinement_summary_metrics.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": f"pp_h12b_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "started_at": start.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "input_result_labels": str(H12_RESULT_LABELS.relative_to(REPO)),
        "input_artist_queue": str(H12_ARTIST_QUEUE.relative_to(REPO)),
        "result_rows": int(len(reviewed_results)),
        "artist_rows": int(len(refined_artist)),
        "candidate_for_h14_h18_artist_n": int(refined_artist["recommended_action"].eq("candidate_for_h14_h18").sum()),
        "note": "Conservative draft labels only. Human review is still required for final acceptance.",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "output_paths.json").write_text(json.dumps({
        "search_result_review_label_draft": str(result_path.relative_to(REPO)),
        "artist_match_review_queue_refined": str(artist_path.relative_to(REPO)),
        "metrics": str(metrics_path.relative_to(REPO)),
        "experiment_dir": str(exp_dir.relative_to(REPO)),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html = render_report(reviewed_results, refined_artist, metrics, config)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "candidate_for_h14_h18_artist_n": config["candidate_for_h14_h18_artist_n"],
        "artist_queue": str(artist_path.relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
