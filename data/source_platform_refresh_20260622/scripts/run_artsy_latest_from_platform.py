#!/usr/bin/env python3
"""
Artsy 원본 플랫폼에서 최신 데이터를 수집한다.

사용 방식:
  - 기존 수집 코드: scripts/crawl_artsy_complete.py
  - 출력 폴더만 이 패키지 내부 artsy_latest로 바꿔서 실행한다.
  - 기본값은 1차 정리 CSV를 baseline으로 읽어 기존 작품을 건너뛰는 증분 수집이다.

출력:
  - artsy_latest/artsy_kr_artworks.json
  - artsy_latest/artsy_kr_artworks.csv
  - artsy_latest/artsy_kr_artists.json
  - artsy_latest/artsy_kr_artist_shows.json
  - artsy_latest/artsy_kr_artists_full.json
  - artsy_latest/artsy_kr_artists_full.csv

주의:
  - 이 스크립트는 Artsy GraphQL API에 직접 요청한다.
  - 전체 수집은 오래 걸릴 수 있다.
  - 전체 재수집이 필요하면 --full-refresh 옵션을 사용한다.
  - 기존 data/ 폴더의 파일은 덮어쓰지 않는다.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]
REPO = PACKAGE_DIR.parents[1]
OUTPUT_DIR = PACKAGE_DIR / "artsy_latest"
SOURCE_SCRIPT = REPO / "scripts" / "crawl_artsy_complete.py"


def default_baseline_csv() -> Path:
    """1차 정리 산출물 중 존재하는 baseline CSV를 찾는다."""
    output_dir = PACKAGE_DIR / "csv_collected_20260622/03_outputs"
    candidates = [
        output_dir / "standardized_artworks_merged_deduped.csv",
        output_dir / "standardized_artworks_merged_deduped_0622.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def load_module():
    spec = importlib.util.spec_from_file_location("crawl_artsy_complete_safe", SOURCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"수집 스크립트를 불러올 수 없습니다: {SOURCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    module = load_module()

    # 기존 스크립트는 DATA_DIR에 저장하므로, DATA_DIR만 안전한 출력 폴더로 바꾼다.
    module.DATA_DIR = OUTPUT_DIR
    module.DEFAULT_BASELINE_CSV = default_baseline_csv()
    module.main()


if __name__ == "__main__":
    main()
