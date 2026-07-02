#!/usr/bin/env python3
"""Step 03: create train/validation/test split.

기본값은 `frozen-if-available`이다.
- frozen reference 2개가 있으면 기존 실험 split을 재현한다.
- 없으면 현재 코드의 자동 split 정책으로 새 split을 만든다.
"""

from __future__ import annotations

import argparse
import json

import build_track6_dataset_from_source_files as core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 03: create Track6 train/validation/test split.")
    parser.add_argument(
        "--split-mode",
        choices=["frozen-if-available", "frozen", "auto"],
        default="frozen-if-available",
        help="split 생성 방식.",
    )
    parser.add_argument("--dry-run", action="store_true", help="실행하지 않고 해석된 mode만 출력한다.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    split_mode = core.resolve_split_mode(args.split_mode)
    payload = {"requested_split_mode": args.split_mode, "split_mode": split_mode}
    if args.dry_run:
        print(json.dumps({"status": "dry_run", **payload}, ensure_ascii=False, indent=2))
        return 0
    if split_mode == "frozen":
        core.create_working_splits_from_frozen_membership()
    else:
        core.create_working_splits_from_auto_policy()
    print(json.dumps({"status": "done", **payload}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
