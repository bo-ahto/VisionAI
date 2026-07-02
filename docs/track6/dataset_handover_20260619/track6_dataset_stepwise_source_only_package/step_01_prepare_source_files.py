#!/usr/bin/env python3
"""Step 01: copy source CSV files into the repo data directory.

입력:
  - 01_source_files/*.csv

출력:
  - repo data/ 아래 기존 Track4/Track6 파이프라인이 읽는 위치
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import build_track6_dataset_from_source_files as core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 01: prepare source files.")
    parser.add_argument("--source-dir", type=Path, default=core.SHARE_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = core.copy_source_files(args.source_dir.resolve(), dry_run=args.dry_run)
    print(json.dumps({"status": "dry_run" if args.dry_run else "done", "files": files}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
