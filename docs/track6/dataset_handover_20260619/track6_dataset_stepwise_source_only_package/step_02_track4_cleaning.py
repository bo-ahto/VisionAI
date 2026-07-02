#!/usr/bin/env python3
"""Step 02: run the Track4 cleaning pipeline.

역할:
  - 원본 row 통합
  - 가격, 크기, 재료, 지지체, 중복 등 기본 정제
  - Track6 후보 데이터의 기반이 되는 Track4 feature candidate 생성
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import build_track6_dataset_from_source_files as core


STEP = core.PIPELINE_STEPS[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 02: run Track4 cleaning pipeline.")
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
