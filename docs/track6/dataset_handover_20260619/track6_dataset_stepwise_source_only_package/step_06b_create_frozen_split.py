#!/usr/bin/env python3
"""Step 06B: recreate the existing experiment split from frozen reference files.

이 파일은 자동 split을 만들지 않는다.
`02_frozen_reference/track6_split_membership.csv`와
`02_frozen_reference/track6_identity_overrides.csv`가 있을 때만 기존 실험 split을 재현한다.
"""

from __future__ import annotations

import argparse
import json

import build_track6_dataset_from_source_files as core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 06B: create frozen split.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run:
        missing = [
            str(path)
            for path in [core.FROZEN_MEMBERSHIP, core.FROZEN_IDENTITY_OVERRIDES]
            if not path.exists()
        ]
        print(json.dumps({"status": "dry_run", "split_mode": "frozen", "missing_reference_files": missing}, ensure_ascii=False, indent=2))
        return 0 if not missing else 1
    core.create_working_splits_from_frozen_membership()
    print(json.dumps({"status": "done", "split_mode": "frozen"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
