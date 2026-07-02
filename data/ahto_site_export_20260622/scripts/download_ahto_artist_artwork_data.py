#!/usr/bin/env python3
"""
Artsy / Saatchi AHTO 데이터 뷰어에서 원본 JSON을 내려받아 CSV로 변환한다.

입력:
  - https://artsy.ahto.city/artsy_kr_artworks.json
  - https://artsy.ahto.city/artsy_kr_artists.json
  - https://saatchi.ahto.city/saatchi_kr_artworks.json
  - https://saatchi.ahto.city/saatchi_kr_artists.json

출력:
  - raw_json/*.json: 사이트에서 받은 원본 JSON
  - csv/*.csv: CSV 변환 결과
  - export_summary.json: 다운로드/변환 요약

처리:
  - JSON을 그대로 저장한다.
  - 작품 JSON과 작가 JSON을 각각 CSV로 변환한다.
  - 가격, 작가명, 작품명 등을 새로 계산하지 않는다.
  - 중첩된 값은 pandas.json_normalize 기준으로 컬럼을 펼친다.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "raw_json"
CSV_DIR = BASE_DIR / "csv"
SUMMARY_PATH = BASE_DIR / "export_summary.json"

SOURCES = {
    "artsy_artworks": "https://artsy.ahto.city/artsy_kr_artworks.json",
    "artsy_artists": "https://artsy.ahto.city/artsy_kr_artists.json",
    "saatchi_artworks": "https://saatchi.ahto.city/saatchi_kr_artworks.json",
    "saatchi_artists": "https://saatchi.ahto.city/saatchi_kr_artists.json",
}


def download_json(name: str, url: str) -> Any:
    """URL에서 JSON을 받아 raw_json 폴더에 원본 그대로 저장한다."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()

    out_path = RAW_DIR / f"{name}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def to_records(data: Any, source_name: str) -> list[dict[str, Any]]:
    """JSON 구조를 CSV로 저장 가능한 records 형태로 바꾼다."""
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # Artsy artists JSON은 {artist_slug: profile} 형태라 key를 컬럼으로 보존한다.
        records: list[dict[str, Any]] = []
        for key, value in data.items():
            if isinstance(value, dict):
                row = {"source_record_key": key, **value}
            else:
                row = {"source_record_key": key, "value": value}
            records.append(row)
        return records

    raise TypeError(f"{source_name}: 지원하지 않는 JSON 구조입니다: {type(data).__name__}")


def write_csv(name: str, data: Any) -> tuple[Path, int, int]:
    """JSON records를 CSV로 저장하고 행/열 수를 반환한다."""
    records = to_records(data, name)
    frame = pd.json_normalize(records, sep=".")

    out_path = CSV_DIR / f"{name}.csv"
    frame.to_csv(out_path, index=False, encoding="utf-8-sig")
    return out_path, int(len(frame)), int(frame.shape[1])


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_dir": str(BASE_DIR),
        "sources": {},
    }

    for name, url in SOURCES.items():
        print(f"download: {name} <- {url}")
        data = download_json(name, url)
        csv_path, rows, cols = write_csv(name, data)
        raw_path = RAW_DIR / f"{name}.json"
        summary["sources"][name] = {
            "url": url,
            "raw_json": str(raw_path.relative_to(BASE_DIR)),
            "csv": str(csv_path.relative_to(BASE_DIR)),
            "rows": rows,
            "columns": cols,
        }
        print(f"  rows={rows:,} cols={cols:,} csv={csv_path.relative_to(BASE_DIR)}")

    with SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"summary: {SUMMARY_PATH.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
