#!/usr/bin/env python3
"""Step 03: correct Track6 artist Korean names.

역할:
  - 검수된 override 기준으로 한글 작가명 보정
  - 원래 작가명 보존
  - 동명이인 구분 suffix 반영
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import build_track6_dataset_from_source_files as core


STEP = core.PIPELINE_STEPS[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 03: correct artist Korean names.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    name, script, description = STEP
    print(f"== {name}")
    print(f"script: {script}")
    print(f"role: {description}")
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "script": script}, ensure_ascii=False, indent=2))
        return 0
    completed = subprocess.run([sys.executable, str(core.REPO_ROOT / script)], cwd=core.REPO_ROOT, check=False)
    status = "done" if completed.returncode == 0 else "fail"
    print(json.dumps({"status": status, "script": script, "return_code": int(completed.returncode)}, ensure_ascii=False, indent=2))
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
