#!/usr/bin/env python3
"""Step 01: copy package source CSV files into repo data paths.

이 단계는 원본 CSV를 기존 Track4/Track6 파이프라인이 읽는 repo `data/`
위치로 복사한다. 데이터 정제나 split 생성은 하지 않는다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import build_track6_dataset_from_source_files as core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 01: prepare Track6 source CSV files.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=core.SHARE_ROOT,
        help="원본 CSV가 들어 있는 폴더. 기본값은 패키지 폴더이며 01_source_files/도 함께 검색한다.",
    )
    parser.add_argument("--dry-run", action="store_true", help="복사하지 않고 대상만 확인한다.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    copied = core.copy_source_files(args.source_dir.resolve(), dry_run=args.dry_run)
    print(json.dumps({"status": "dry_run" if args.dry_run else "done", "files": copied}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
