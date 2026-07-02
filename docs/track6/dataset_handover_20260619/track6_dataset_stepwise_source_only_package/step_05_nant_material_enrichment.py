#!/usr/bin/env python3
"""Step 05: enrich Track6 candidate rows with NANT material/support columns.

역할:
  - NANT 기준표로 재료, 지지체, 도구 관련 보강 컬럼 생성
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import build_track6_dataset_from_source_files as core


STEP = core.PIPELINE_STEPS[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 05: enrich NANT material/support columns.")
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
