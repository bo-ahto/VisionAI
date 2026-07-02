#!/usr/bin/env python3
"""
Saatchi 원본 플랫폼에서 최신 데이터를 다시 수집한다.

사용 방식:
  - 기존 수집 코드: scripts/crawl_saatchi.py
  - 출력 폴더만 이 패키지 내부 saatchi_latest로 바꿔서 실행한다.

출력:
  - saatchi_latest/saatchi_kr_artworks.json
  - saatchi_latest/saatchi_kr_artworks.csv
  - saatchi_latest/saatchi_kr_artists.json

주의:
  - 이 스크립트는 Saatchi Constructor.io API와 작가 프로필 페이지에 직접 요청한다.
  - 기존 수집 코드는 Constructor.io 검색 결과 100페이지 x 100건을 수집한다.
  - 따라서 현재 설정 기준 작품 수집 상한은 10,000건이다.
  - 기존 data/ 폴더의 파일은 덮어쓰지 않는다.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]
REPO = PACKAGE_DIR.parents[1]
OUTPUT_DIR = PACKAGE_DIR / "saatchi_latest"
SOURCE_SCRIPT = REPO / "scripts" / "crawl_saatchi.py"


def load_module():
    spec = importlib.util.spec_from_file_location("crawl_saatchi_safe", SOURCE_SCRIPT)
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
    module.main()


if __name__ == "__main__":
    main()
