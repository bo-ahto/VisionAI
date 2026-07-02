#!/usr/bin/env python3
"""Step 02: run cleaning and enrichment before split generation.

실행 순서:
1. Track4 원본 통합/정제 파이프라인
2. Track6 작가명 보정
3. Track6 작가 메타 보강
4. Track6 NANT 재료/지지체 보강

split 생성과 feature/label export는 다음 단계에서 실행한다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import build_track6_dataset_from_source_files as core


PRE_SPLIT_STEPS = core.PIPELINE_STEPS[:4]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 02: run Track4/Track6 cleaning and enrichment.")
    parser.add_argument("--dry-run", action="store_true", help="실행하지 않고 단계만 출력한다.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = []
    for name, script, description in PRE_SPLIT_STEPS:
        script_path = core.REPO_ROOT / script
        print(f"\n== {name}")
        print(f"script: {script}")
        print(f"role: {description}")
        if args.dry_run:
            results.append({"name": name, "script": script, "return_code": 0, "dry_run": True})
            continue
        completed = subprocess.run([sys.executable, str(script_path)], cwd=core.REPO_ROOT, check=False)
        results.append({"name": name, "script": script, "return_code": int(completed.returncode), "dry_run": False})
        if completed.returncode != 0:
            print(json.dumps({"status": "fail", "steps": results}, ensure_ascii=False, indent=2))
            return int(completed.returncode)
    print(json.dumps({"status": "done", "steps": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
