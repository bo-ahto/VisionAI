#!/usr/bin/env python3
"""Create v0.1 feature files for the 0604 operation-style test input.

이 스크립트는 기능을 "전처리/피처 추출"로만 제한한다.
다음 단계 예측 스크립트는 여기서 생성한 `features_all_v0_1.csv`를 입력으로 사용한다.

기본 실행:
    python3 experiments/track6/OP-0605_v01_70_30_reprediction/scripts/01_preprocess_features.py

다른 입력 파일로 재실행:
    python3 experiments/track6/OP-0605_v01_70_30_reprediction/scripts/01_preprocess_features.py \
      --input data/some_new_artworks.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for current in [start, *start.parents]:
        if (current / "scripts" / "track6").exists() and (current / "models" / "track6").exists():
            return current
    raise RuntimeError(f"VisionAI repo root를 찾을 수 없습니다: {start}")


REPO = find_repo_root(Path(__file__).resolve())
SCRIPT_DIR = REPO / "scripts" / "track6"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_price_prediction_v0_1_features import extract_features, write_outputs  # noqa: E402


EXP_DIR = REPO / "experiments" / "track6" / "OP-0605_v01_70_30_reprediction"
MODEL_ROOT = REPO / "models" / "track6" / "price_prediction_v0.1"
DEFAULT_INPUT = REPO / "data" / "test_new_artworks_test_noprice_0604.csv"
DEFAULT_OUTPUT_DIR = EXP_DIR / "data" / "features"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess operation-style CSV into v0.1 feature files.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="가격 없는 운영 입력 CSV")
    parser.add_argument("--model-root", type=Path, default=MODEL_ROOT, help="v0.1 모델 기준 폴더")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="피처 출력 폴더")
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO / path


def main() -> None:
    args = parse_args()
    input_path = resolve(args.input)
    model_root = resolve(args.model_root)
    output_dir = resolve(args.output_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"input not found: {input_path}")
    if not model_root.exists():
        raise FileNotFoundError(f"model root not found: {model_root}")

    features, metadata = extract_features(input_path, model_root)
    write_outputs(features, metadata, output_dir)

    run_config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "step": "01_preprocess_features",
        "input": str(input_path.relative_to(REPO)),
        "model_root": str(model_root.relative_to(REPO)),
        "output_dir": str(output_dir.relative_to(REPO)),
        "rows": int(metadata["rows"]),
        "warm_rows": int(metadata["warm_rows"]),
        "cold_rows": int(metadata["cold_rows"]),
        "main_output": str((output_dir / "features_all_v0_1.csv").relative_to(REPO)),
    }
    (EXP_DIR / "data" / "preprocess_run_config.json").write_text(
        json.dumps(run_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"status": "completed", **run_config}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
