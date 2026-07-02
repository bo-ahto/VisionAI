#!/usr/bin/env python3
"""Step 05: copy generated split into package output and verify it.

이 단계는 repo `data/track6_split` 결과를 패키지의
`05_generated_frozen_training_dataset/` 아래로 복사하고,
legacy feature/label 파일 재생성, manifest, build report를 만든다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import build_track6_dataset_from_source_files as core


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 05: copy and verify Track6 generated dataset.")
    parser.add_argument(
        "--frozen-output-dir",
        type=Path,
        default=core.SHARE_ROOT / "05_generated_frozen_training_dataset" / "track6_split",
        help="결과 데이터 출력 폴더.",
    )
    parser.add_argument(
        "--split-mode",
        choices=["frozen-if-available", "frozen", "auto"],
        default="frozen-if-available",
        help="검증 기준에 사용할 split mode.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    split_mode = core.resolve_split_mode(args.split_mode)
    summary = core.finalize_generated_output(
        args.frozen_output_dir.resolve(),
        split_mode=split_mode,
        requested_split_mode=args.split_mode,
        source_dir=core.SHARE_ROOT,
    )
    print(json.dumps({"status": summary["status"], "build_report": str(args.frozen_output_dir.resolve().parent / "verification" / "build_report.md")}, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
