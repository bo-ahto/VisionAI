#!/usr/bin/env python3
"""Step 04: export feature/label files from generated split.

이 단계는 repo의 `scripts/track6/export_feature_label_splits.py`를 실행한다.
최종 공유용 output 폴더로 복사하고 legacy feature/label 컬럼을 재생성하는 작업은
Step 05에서 수행한다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import build_track6_dataset_from_source_files as core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 04: export Track6 feature/label files.")
    parser.add_argument("--dry-run", action="store_true", help="실행하지 않고 대상 스크립트만 출력한다.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    name, script, description = core.PIPELINE_STEPS[-1]
    script_path = core.REPO_ROOT / script
    print(f"== {name}")
    print(f"script: {script}")
    print(f"role: {description}")
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "script": script}, ensure_ascii=False, indent=2))
        return 0
    completed = subprocess.run([sys.executable, str(script_path)], cwd=core.REPO_ROOT, check=False)
    status = "done" if completed.returncode == 0 else "fail"
    print(json.dumps({"status": status, "script": script, "return_code": int(completed.returncode)}, ensure_ascii=False, indent=2))
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
