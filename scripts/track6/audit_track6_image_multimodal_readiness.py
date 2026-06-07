#!/usr/bin/env python3
"""Audit Track6 readiness for image/tabular multimodal experiments."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track6_split"
OUT_DIR = REPO / "data" / "track6" / "image_multimodal"
DOC_PATH = REPO / "docs" / "track6" / "experiments" / "track6_image_multimodal_readiness_report.md"

SPLIT_FILES = {
    "train": SPLIT_DIR / "track6_train.csv",
    "val_cold": SPLIT_DIR / "track6_val_cold.csv",
    "test_cold": SPLIT_DIR / "track6_test_cold.csv",
    "val_warm": SPLIT_DIR / "track6_val_warm.csv",
    "test_warm": SPLIT_DIR / "track6_test_warm.csv",
}

MANIFEST_COLUMNS = [
    "_track6_row_id",
    "track4_source",
    "track4_source_row_index",
    "source_artwork_id",
    "artist_key",
    "artist_name_ko",
    "title_raw",
    "price_krw",
    "ln_price_krw",
    "artwork_url",
    "image_url",
]


def domain(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return "__missing__"
    parsed = urlparse(value.strip())
    return parsed.netloc.lower() or "__missing__"


def source_bucket(value: object) -> str:
    host = domain(value)
    if "saatchiart" in host:
        return "saatchi"
    if "artsy" in host:
        return "artsy"
    if host == "__missing__":
        return "__missing__"
    return "other"


def resolved_source_bucket(row: pd.Series) -> str:
    track4_source = str(row.get("track4_source", "")).strip().lower()
    if track4_source in {"saatchi", "artsy", "artue", "gallery_primary"}:
        return track4_source
    artwork_source = str(row.get("artwork_source_bucket", "")).strip().lower()
    if artwork_source not in {"", "__missing__", "other"}:
        return artwork_source
    image_source = str(row.get("image_source_bucket", "")).strip().lower()
    if image_source not in {"", "__missing__"}:
        return image_source
    return "__missing__"


def load_manifest() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for split, path in SPLIT_FILES.items():
        frame = pd.read_csv(path, low_memory=False)
        missing = [col for col in MANIFEST_COLUMNS if col not in frame.columns]
        if missing:
            raise ValueError(f"{path} missing columns: {missing}")
        frame = frame[MANIFEST_COLUMNS].copy()
        frame["split"] = split
        frame["image_url"] = frame["image_url"].fillna("").astype(str)
        frame["artwork_url"] = frame["artwork_url"].fillna("").astype(str)
        frame["has_image_url"] = frame["image_url"].str.strip().ne("")
        frame["image_domain"] = frame["image_url"].map(domain)
        frame["image_source_bucket"] = frame["image_url"].map(source_bucket)
        frame["artwork_domain"] = frame["artwork_url"].map(domain)
        frame["artwork_source_bucket"] = frame["artwork_url"].map(source_bucket)
        frame["resolved_source_bucket"] = frame.apply(resolved_source_bucket, axis=1)
        frames.append(frame)
    out = pd.concat(frames, ignore_index=True)
    out["_track6_row_id"] = pd.to_numeric(out["_track6_row_id"], errors="coerce").astype("Int64")
    return out


def coverage_table(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, group in manifest.groupby("split", sort=False):
        rows.append({
            "split": split,
            "rows": int(len(group)),
            "image_url_rows": int(group["has_image_url"].sum()),
            "missing_image_url_rows": int((~group["has_image_url"]).sum()),
            "image_url_rate": round(float(group["has_image_url"].mean()), 4),
            "unique_image_urls": int(group.loc[group["has_image_url"], "image_url"].nunique()),
        })
    return pd.DataFrame(rows)


def source_coverage_table(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (split, source), group in manifest.groupby(["split", "resolved_source_bucket"], sort=False):
        rows.append({
            "split": split,
            "source": source,
            "rows": int(len(group)),
            "image_url_rows": int(group["has_image_url"].sum()),
            "missing_image_url_rows": int((~group["has_image_url"]).sum()),
            "image_url_rate": round(float(group["has_image_url"].mean()), 4),
        })
    return pd.DataFrame(rows)


def embedding_audit(manifest: pd.DataFrame) -> dict[str, object]:
    audits: dict[str, object] = {}
    expected_direct_columns = {"_track6_row_id", "image_url", "image_url_hash"}
    for name in ["clip", "image"]:
        index_path = REPO / "data" / f"{name}_embeddings_index.csv"
        npy_path = REPO / "data" / f"{name}_embeddings.npy"
        if name == "image":
            npy_path = REPO / "data" / "image_embeddings_raw.npy"
        record: dict[str, object] = {
            "index_path": str(index_path.relative_to(REPO)),
            "embedding_path": str(npy_path.relative_to(REPO)),
            "index_exists": index_path.exists(),
            "embedding_exists": npy_path.exists(),
        }
        if index_path.exists():
            idx = pd.read_csv(index_path, low_memory=False)
            record["index_rows"] = int(len(idx))
            record["index_columns"] = list(idx.columns)
            record["has_direct_track6_key"] = bool(expected_direct_columns.intersection(idx.columns))
            if "idx" in idx.columns:
                track6_ids = set(manifest["_track6_row_id"].dropna().astype(int).tolist())
                old_ids = set(pd.to_numeric(idx["idx"], errors="coerce").dropna().astype(int).tolist())
                record["numeric_id_overlap_count"] = int(len(track6_ids.intersection(old_ids)))
                record["numeric_id_overlap_note"] = (
                    "Numeric overlap is not a valid match because the index column is named idx, "
                    "not _track6_row_id or image_url."
                )
        if npy_path.exists():
            arr = np.load(npy_path, mmap_mode="r")
            record["embedding_shape"] = list(arr.shape)
            record["embedding_dtype"] = str(arr.dtype)
            record["embedding_size_mb"] = round(npy_path.stat().st_size / 1024 / 1024, 2)
        audits[name] = record
    return audits


def markdown_table(frame: pd.DataFrame) -> str:
    headers = list(frame.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def write_report(
    manifest: pd.DataFrame,
    coverage: pd.DataFrame,
    source_coverage: pd.DataFrame,
    audit: dict[str, object],
) -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_rows = len(manifest)
    image_rows = int(manifest["has_image_url"].sum())
    unique_images = int(manifest.loc[manifest["has_image_url"], "image_url"].nunique())
    duplicate_images = image_rows - unique_images
    audit_json = json.dumps(audit, ensure_ascii=False, indent=2)
    text = f"""# Track6 이미지 멀티모달 실험 준비 상태 점검

- 생성 시각: {generated_at}
- 목적: Deep Learning for Art Market Valuation 논문 방식처럼 이미지 정보와 정형 피처를 결합하는 실험이 가능한지 확인한다.
- 결론: 이미지 URL 커버리지는 충분하나, 기존 이미지 임베딩은 Track6 row와 직접 매칭되는 키가 없어 바로 사용하지 않는다.

## 1. Split별 이미지 URL 커버리지

{markdown_table(coverage)}

## 2. 출처별 이미지 URL 커버리지

{markdown_table(source_coverage)}

## 3. 전체 요약

- 전체 행 수: {total_rows}
- 이미지 URL 보유 행 수: {image_rows}
- 이미지 URL 보유율: {image_rows / total_rows:.4f}
- 고유 이미지 URL 수: {unique_images}
- 중복 이미지 URL 수: {duplicate_images}

## 4. 기존 이미지 임베딩 재사용 가능성

- 기존 `data/clip_embeddings.npy`와 `data/image_embeddings_raw.npy`는 존재한다.
- 기존 인덱스 파일의 키는 `idx`이다.
- Track6 split의 기준 키는 `_track6_row_id`, `image_url`, `artwork_url`이다.
- 따라서 숫자 값이 일부 겹치더라도 같은 작품이라고 해석하면 안 된다.
- 현재 기준으로는 Track6 전용 이미지 임베딩을 새로 생성하는 것이 안전하다.

```json
{audit_json}
```

## 5. 다음 실행 기준

- 1단계: 이 매니페스트를 기준으로 이미지 URL 샘플 다운로드 성공률을 확인한다.
- 2단계: 다운로드 가능성이 확인되면 Track6 전용 CLIP 임베딩을 `_track6_row_id` 기준으로 생성한다.
- 3단계: Cold부터 이미지 단독, 정형 피처 단독, 정형 피처 + 이미지 결합을 비교한다.
- 4단계: Cold에서 개선이 확인되면 Warm에도 같은 구조를 확장한다.
"""
    DOC_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    coverage = coverage_table(manifest)
    source_coverage = source_coverage_table(manifest)
    audit = embedding_audit(manifest)

    manifest_path = OUT_DIR / "track6_image_manifest.csv"
    coverage_path = OUT_DIR / "track6_image_coverage_summary.csv"
    source_coverage_path = OUT_DIR / "track6_image_source_coverage_summary.csv"
    audit_path = OUT_DIR / "track6_existing_embedding_audit.json"

    manifest.to_csv(manifest_path, index=False)
    coverage.to_csv(coverage_path, index=False)
    source_coverage.to_csv(source_coverage_path, index=False)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(manifest, coverage, source_coverage, audit)

    print(f"wrote {manifest_path.relative_to(REPO)} rows={len(manifest)}")
    print(f"wrote {coverage_path.relative_to(REPO)}")
    print(f"wrote {source_coverage_path.relative_to(REPO)}")
    print(f"wrote {audit_path.relative_to(REPO)}")
    print(f"wrote {DOC_PATH.relative_to(REPO)}")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
