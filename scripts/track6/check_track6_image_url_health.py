#!/usr/bin/env python3
"""Sample-check Track6 image URLs before embedding extraction."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


REPO = Path(__file__).resolve().parents[2]
BASE_DIR = REPO / "data" / "track6" / "image_multimodal"
MANIFEST_PATH = BASE_DIR / "track6_image_manifest.csv"
OUT_PATH = BASE_DIR / "track6_image_url_health_sample.csv"
SUMMARY_PATH = BASE_DIR / "track6_image_url_health_summary.csv"
DOC_PATH = REPO / "docs" / "track6" / "experiments" / "track6_image_url_health_sample_report.md"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; VisionAITrack6ImageAudit/1.0)",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-split-source", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=OUT_PATH)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_PATH)
    return parser.parse_args()


def sample_manifest(manifest: pd.DataFrame, per_split_source: int, seed: int) -> pd.DataFrame:
    frame = manifest[manifest["has_image_url"]].copy()
    samples: list[pd.DataFrame] = []
    for _, group in frame.groupby(["split", "resolved_source_bucket"], sort=False):
        sample_size = min(per_split_source, len(group))
        samples.append(group.sample(n=sample_size, random_state=seed))
    if not samples:
        return frame.iloc[0:0].copy()
    return pd.concat(samples, ignore_index=True)


def check_url(url: str, timeout: float) -> dict[str, Any]:
    started = datetime.now()
    try:
        with requests.get(url, headers=HEADERS, timeout=timeout, stream=True, allow_redirects=True) as response:
            content_type = response.headers.get("content-type", "")
            content_length = response.headers.get("content-length", "")
            first_chunk = next(response.iter_content(chunk_size=512), b"")
            elapsed_ms = int((datetime.now() - started).total_seconds() * 1000)
            return {
                "ok": bool(response.ok and content_type.lower().startswith("image/") and first_chunk),
                "status_code": int(response.status_code),
                "final_url": response.url,
                "content_type": content_type,
                "content_length": content_length,
                "first_chunk_bytes": len(first_chunk),
                "elapsed_ms": elapsed_ms,
                "error": "",
            }
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((datetime.now() - started).total_seconds() * 1000)
        return {
            "ok": False,
            "status_code": None,
            "final_url": "",
            "content_type": "",
            "content_length": "",
            "first_chunk_bytes": 0,
            "elapsed_ms": elapsed_ms,
            "error": f"{type(exc).__name__}: {exc}",
        }


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (split, source), group in results.groupby(["split", "resolved_source_bucket"], sort=False):
        rows.append({
            "split": split,
            "source": source,
            "checked_rows": int(len(group)),
            "ok_rows": int(group["ok"].sum()),
            "ok_rate": round(float(group["ok"].mean()), 4) if len(group) else 0.0,
            "median_elapsed_ms": int(group["elapsed_ms"].median()) if len(group) else 0,
        })
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    headers = list(frame.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def write_report(summary: pd.DataFrame, output: Path) -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"""# Track6 이미지 URL 샘플 다운로드 검증

- 생성 시각: {generated_at}
- 목적: Track6 전용 이미지 임베딩 추출 전에 실제 이미지 URL이 다운로드 가능한지 확인한다.
- 결과 파일: `{output.relative_to(REPO)}`

## 요약

{markdown_table(summary)}

## 해석 기준

- `ok_rate`가 높으면 해당 출처의 이미지를 임베딩 추출 대상으로 삼을 수 있다.
- 특정 출처의 실패율이 높으면 해당 출처는 별도 다운로드 로직이나 fallback 정책이 필요하다.
- 이 검증은 샘플 확인이므로 전체 임베딩 추출 전 대량 다운로드 실패 가능성을 완전히 제거하지는 않는다.
"""
    DOC_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    manifest = pd.read_csv(MANIFEST_PATH, low_memory=False)
    sample = sample_manifest(manifest, args.per_split_source, args.seed)
    rows = []
    for _, row in sample.iterrows():
        checked = check_url(str(row["image_url"]), args.timeout)
        rows.append({
            "_track6_row_id": row["_track6_row_id"],
            "split": row["split"],
            "resolved_source_bucket": row["resolved_source_bucket"],
            "image_url": row["image_url"],
            **checked,
        })
    result = pd.DataFrame(rows)
    summary = summarize(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    summary.to_csv(args.summary_output, index=False)
    write_report(summary, args.output)
    print(f"wrote {args.output.relative_to(REPO)} rows={len(result)}")
    print(f"wrote {args.summary_output.relative_to(REPO)}")
    print(f"wrote {DOC_PATH.relative_to(REPO)}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
