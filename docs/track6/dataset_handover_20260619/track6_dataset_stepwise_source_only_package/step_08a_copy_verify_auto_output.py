#!/usr/bin/env python3
"""Step 08A: copy and verify auto-split output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import build_track6_dataset_from_source_files as core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 08A: copy and verify auto output.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=core.SHARE_ROOT / "05_generated_dataset" / "track6_split",
        help="패키지 안에 생성할 최종 데이터셋 폴더.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = core.finalize_generated_output(
        args.output_dir.resolve(),
        split_mode="auto",
        requested_split_mode="auto",
        source_dir=core.SHARE_ROOT,
    )
    report = args.output_dir.resolve().parent / "verification" / "build_report.md"
    print(json.dumps({"status": summary["status"], "output_dir": str(args.output_dir.resolve()), "build_report": str(report)}, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
