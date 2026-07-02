#!/usr/bin/env python3
"""Step 06A: create a new Track6 split with the current auto split policy.

이 파일은 frozen reference를 보지 않는다.
현재 repo의 `scripts/track6/create_track6_splits.py` 정책으로 새 split을 만든다.
"""

from __future__ import annotations

import argparse
import json

import build_track6_dataset_from_source_files as core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 06A: create auto split.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "split_mode": "auto"}, ensure_ascii=False, indent=2))
        return 0
    core.create_working_splits_from_auto_policy()
    print(json.dumps({"status": "done", "split_mode": "auto"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
