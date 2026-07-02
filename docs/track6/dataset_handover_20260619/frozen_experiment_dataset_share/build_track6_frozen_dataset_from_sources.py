#!/usr/bin/env python3
"""Build and freeze the Track6 experiment dataset from source CSV files.

이 파일은 "공유 폴더 하나 안에 원본 CSV와 고정 기준 파일이 있으면
결과 데이터도 같은 공유 폴더 안에 생성되도록" 만든 단일 진입점
(entrypoint) 스크립트다.

필요한 입력 파일:
    아래 파일들은 스크립트와 같은 폴더에 직접 두거나,
    같은 폴더의 `01_source_files/` 아래에 두면 된다.

    1. saatchi_cleaned.csv
    2. artsy_kr_artworks.csv
    3. artue_테스트_가격포함.csv
    4. 1차 시장 데이터 - 전달본_260504.csv
    5. track6_reference/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv

필요한 고정 기준 파일:
    아래 파일/폴더는 같은 공유 폴더 안에 있어야 한다.

    1. 03_frozen_training_dataset/track6_split/track6_split_membership.csv
    2. 03_frozen_training_dataset/track6_split/*.csv
    3. 03_frozen_training_dataset/track6_split/features/
    4. 03_frozen_training_dataset/track6_split/labels/

실행 전제:
    이 스크립트는 Track4/Track6 기존 파이프라인 코드를 호출한다.
    따라서 `/Users/bo/VisionAI` 같은 VisionAI repo 안에서 실행해야 한다.
    최종 결과물은 repo의 `data/`가 아니라 이 공유 폴더 안의
    `05_generated_frozen_training_dataset/`에 생성된다.

중요:
    이 스크립트는 검증만 하는 스크립트가 아니다.
    원본 CSV를 repo의 `data/` 위치에 배치하고,
    Track4 정제 -> Track6 작가명 보정 -> 작가 메타 보강 -> split 생성
    -> feature/label 분리 -> frozen output 복사까지 수행한다.

왜 "기존 스크립트를 호출"하는 방식인가:
    실제 데이터셋 생성 로직은 이미 repo의 Track4/Track6 파이프라인
    스크립트에 구현되어 있다. 이 파일은 그 로직을 다시 복붙하지 않고
    순서를 하나로 묶어 실행한다. 그래야 기존 실험 당시의 처리 기준과
    어긋날 가능성이 낮다.

기본 실행:
    python3 docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/build_track6_frozen_dataset_from_sources.py

기본 입력:
    스크립트와 같은 폴더 또는 01_source_files/

기본 출력:
    05_generated_frozen_training_dataset/track6_split/

기본 출력이 기존 기준 frozen split과 다른 경우:
    원본 파일, 보정 테이블, 코드 버전 중 하나가 기존 실험 시점과 달라진 것이다.
    기존 성능표 재현 기준은 `03_frozen_training_dataset/track6_split/`이다.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# 기준 경로
# ---------------------------------------------------------------------------


SCRIPT_PATH = Path(__file__).resolve()
SHARE_ROOT = SCRIPT_PATH.parent


def find_repo_root(start: Path) -> Path:
    """Find repo root by walking upward until `.git` is found."""

    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / ".git").exists():
            return path
    raise RuntimeError("Repo root를 찾지 못했습니다. .git 폴더가 있는 repo 안에서 실행해야 합니다.")


REPO_ROOT = find_repo_root(SCRIPT_PATH)


# 원본 파일은 repo 안의 data/ 아래에서 기존 스크립트들이 읽는다.
# 따라서 source-dir에 있는 파일을 이 이름으로 data/에 배치한 뒤 파이프라인을 실행한다.
SOURCE_FILE_MAP = {
    "saatchi_cleaned.csv": "saatchi_cleaned.csv",
    "artsy_kr_artworks.csv": "artsy_kr_artworks.csv",
    "artue_테스트_가격포함.csv": "artue_테스트_가격포함.csv",
    "1차 시장 데이터 - 전달본_260504.csv": "1차 시장 데이터 - 전달본_260504.csv",
    # Track6 기존 실험 split에는 난트 기준 재료/지지체 보강 컬럼이 포함되어 있다.
    # 이 기준표가 없으면 full split은 같은 row로 만들어져도 50컬럼이 아니라 44컬럼이 된다.
    "track6_reference/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv": "track6/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv",
}


# 기존 실험 frozen split의 기대 row/column 수.
# 이 값은 "생성 결과가 기존 실험 기준과 같은지" 판단하기 위한 기준이다.
EXPECTED_SPLIT_SHAPES = {
    "track6_train.csv": {"rows": 26914, "columns": 50},
    "track6_val_warm.csv": {"rows": 519, "columns": 50},
    "track6_test_warm.csv": {"rows": 607, "columns": 50},
    "track6_val_cold.csv": {"rows": 2753, "columns": 50},
    "track6_test_cold.csv": {"rows": 3099, "columns": 50},
}

EXPECTED_FEATURE_LABEL_SHAPES = {
    "features/warm/track6_train_warm_features.csv": {"rows": 26914, "columns": 23},
    "features/warm/track6_val_warm_warm_features.csv": {"rows": 519, "columns": 23},
    "features/warm/track6_test_warm_warm_features.csv": {"rows": 607, "columns": 23},
    "features/cold/track6_train_cold_features.csv": {"rows": 26914, "columns": 20},
    "features/cold/track6_val_cold_cold_features.csv": {"rows": 2753, "columns": 20},
    "features/cold/track6_test_cold_cold_features.csv": {"rows": 3099, "columns": 20},
    "labels/track6_train_labels.csv": {"rows": 26914, "columns": 12},
    "labels/track6_val_warm_labels.csv": {"rows": 519, "columns": 12},
    "labels/track6_test_warm_labels.csv": {"rows": 607, "columns": 12},
    "labels/track6_val_cold_labels.csv": {"rows": 2753, "columns": 12},
    "labels/track6_test_cold_labels.csv": {"rows": 3099, "columns": 12},
}


# 파이프라인 실행 순서.
# 각 script는 repo root를 기준으로 실행한다.
PIPELINE_STEPS = [
    (
        "track4_cleaning_pipeline",
        "scripts/track4/run_cleaning_pipeline.py",
        "원본 CSV를 통합하고 가격/크기/재료/중복 감사를 거쳐 Track4 feature candidate를 만든다.",
    ),
    (
        "track6_artist_korean_name_correction",
        "scripts/track6/improve_artist_korean_names.py",
        "검수된 override 기준으로 작가 한글명을 보정하고 원래 이름을 보존한다.",
    ),
    (
        "track6_artist_metadata_enrichment",
        "scripts/track6/enrich_track6_artist_metadata.py",
        "raw 수집 row에서 작가 메타 정보를 Track6 후보 데이터에 row 단위로 붙인다.",
    ),
    (
        "track6_nant_material_enrichment",
        "scripts/track6/enrich_track6_nant_material.py",
        "난트 기준 재료/지지체 보강 컬럼을 후보 데이터에 붙인다.",
    ),
    (
        "track6_feature_label_export",
        "scripts/track6/export_feature_label_splits.py",
        "full split에서 모델 입력 feature와 평가 label을 물리적으로 분리한다.",
    ),
]


# ---------------------------------------------------------------------------
# 기존 실험 기준 feature/label export 설정
# ---------------------------------------------------------------------------


# 현재 repo의 `export_feature_label_splits.py`는 운영/후속 실험 기준으로 바뀌어
# `nant_*`와 `collected_material_raw`를 feature에서 제외한다.
# 그러나 기존 Track6 v0.1 frozen dataset의 feature 파일은 해당 6개 컬럼을
# 포함한 23개 Warm feature / 20개 Cold feature였다.
#
# 따라서 이 단일 생성 스크립트는 현재 export 스크립트를 실행한 뒤,
# frozen output 폴더 안에서 기존 실험 기준 feature/label 파일을 다시 만든다.
# 이렇게 해야 "기존 실험 데이터셋"을 원본 CSV에서 끝까지 재현할 수 있다.
LEGACY_TARGET_COLUMNS = ["price_krw", "ln_price_krw"]
LEGACY_LABEL_META_COLUMNS = [
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "artist_name_ko_orig",
    "medium_category",
    "support_category",
    "has_depth",
    "is_3d_candidate",
    "is_high_price_candidate",
    "is_extreme_aspect_ratio",
]
LEGACY_TRACKING_ONLY_COLUMNS = [
    "track4_source",
    "track4_source_row_index",
    "source_artwork_id",
    "artwork_url",
    "image_url",
    "cleaning_exclude_reasons",
]
LEGACY_MODEL_EXCLUDE_COLUMNS = [
    "artist_name_ko",
    "artist_name_ko_orig",
    "artist_name_standardized",
    "is_homonym",
    "artist_entity_suffix",
    "title_raw",
]
LEGACY_MODEL_EXCLUDE_PREFIXES = [
    "artist_meta_",
]
LEGACY_COLD_FORBIDDEN_COLUMNS = [
    "artist_key",
    "artist_works_log",
    "artist_works_count_train",
]
LEGACY_PRICE_LEAK_ALLOWLIST = {"estimated_ho"}
LEGACY_PRICE_LEAK_TOKENS = [
    "price",
    "krw",
    "usd",
    "currency",
    "amount",
    "sold",
    "sale",
    "for_sale",
    "cost",
    "fee",
]

NANT_COLUMNS = [
    "collected_material_raw",
    "nant_support",
    "nant_tool",
    "nant_material_note",
    "nant_material_match_method",
    "nant_material_idx",
]

FROZEN_MEMBERSHIP = SHARE_ROOT / "03_frozen_training_dataset" / "track6_split" / "track6_split_membership.csv"
FROZEN_REFERENCE_SPLIT = SHARE_ROOT / "03_frozen_training_dataset" / "track6_split"
FROZEN_IDENTITY_COLUMNS = [
    "artist_name_ko",
    "artist_name_ko_orig",
    "is_homonym",
    "artist_entity_suffix",
]


@dataclass
class StepResult:
    """Pipeline step execution record."""

    name: str
    script: str
    return_code: int
    description: str


def sha256_file(path: Path) -> str:
    """Compute SHA256 checksum without loading the full file in memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_source_roots(source_dir: Path) -> list[Path]:
    """Return input roots to search for required source files.

    공유용 패키지를 전달할 때 사람마다 파일 배치 방식이 다를 수 있다.
    그래서 기본적으로 아래 순서로 원본 파일을 찾는다.

        1. 사용자가 지정한 source-dir
        2. source-dir/01_source_files
        3. 스크립트와 같은 공유 폴더
        4. 공유 폴더/01_source_files

    이렇게 해두면 원본 파일을 전부 같은 폴더에 풀어도 되고,
    기존 구조처럼 `01_source_files/` 아래에 둬도 된다.
    """

    roots = [
        source_dir.resolve(),
        (source_dir / "01_source_files").resolve(),
        SHARE_ROOT.resolve(),
        (SHARE_ROOT / "01_source_files").resolve(),
    ]
    unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root not in seen:
            seen.add(root)
            unique.append(root)
    return unique


def find_required_source(source_dir: Path, relative_name: str) -> Path:
    """Find a required source file in the supported package layouts."""

    tried: list[Path] = []
    for root in candidate_source_roots(source_dir):
        path = root / relative_name
        tried.append(path)
        if path.exists():
            return path
    lines = "\n".join(f"- {path}" for path in tried)
    raise FileNotFoundError(f"필수 원본 파일을 찾지 못했습니다: {relative_name}\n검색 위치:\n{lines}")


def read_csv_shape(path: Path) -> dict[str, int]:
    """Return CSV row and column count."""

    frame = pd.read_csv(path, low_memory=False)
    return {"rows": int(len(frame)), "columns": int(len(frame.columns))}


def copy_source_files(source_dir: Path, *, dry_run: bool) -> list[dict[str, Any]]:
    """Copy required source files from source_dir to repo data/.

    기존 파이프라인 스크립트는 원본 파일 경로를 인자로 받지 않고
    repo의 `data/` 아래 고정 파일명을 읽는다.
    그래서 이 함수가 공유 폴더 또는 `01_source_files/`의 원본 파일을
    repo `data/`로 복사한다.
    """

    copied: list[dict[str, Any]] = []
    for source_name, repo_name in SOURCE_FILE_MAP.items():
        src = find_required_source(source_dir, source_name)
        dst = REPO_ROOT / "data" / repo_name

        copied.append(
            {
                "source": str(src),
                "destination": str(dst),
                "bytes": int(src.stat().st_size),
                "sha256": sha256_file(src),
            }
        )
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return copied


def run_pipeline_steps(*, dry_run: bool) -> list[StepResult]:
    """Run Track4/Track6 dataset generation scripts in the required order."""

    results: list[StepResult] = []
    for name, script, description in PIPELINE_STEPS:
        script_path = REPO_ROOT / script
        if not script_path.exists():
            raise FileNotFoundError(f"파이프라인 스크립트가 없습니다: {script_path}")

        print(f"\n== {name}")
        print(f"script: {script}")
        print(f"role: {description}")

        if dry_run:
            results.append(StepResult(name=name, script=script, return_code=0, description=description))
            continue

        completed = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=REPO_ROOT,
            check=False,
        )
        results.append(
            StepResult(
                name=name,
                script=script,
                return_code=int(completed.returncode),
                description=description,
            )
        )
        if completed.returncode != 0:
            raise RuntimeError(f"파이프라인 단계 실패: {name} ({script}), return_code={completed.returncode}")
        if name == "track6_nant_material_enrichment":
            create_working_splits_from_frozen_membership()
    return results


def create_working_splits_from_frozen_membership() -> None:
    """Create `data/track6_split` from the frozen membership file.

    기존 실험 데이터셋을 정확히 재현하려면 자동 split을 다시 뽑으면 안 된다.
    자동 split은 원본/보정/코드 상태가 조금만 달라져도 평가 row가 바뀔 수 있다.

    이 함수는 기존 frozen dataset에 포함된 `track6_split_membership.csv`를
    split 고정 명세로 사용한다.

    처리 방식:
        1. 보정/메타/NANT 보강이 끝난 후보 CSV를 읽는다.
        2. membership의 `track6_row_id`를 후보 CSV row index로 해석한다.
        3. membership의 split 값에 따라 train/val/test 파일을 만든다.
        4. train split 기준으로 `artist_works_count_train`, `artist_works_log`를 다시 계산한다.

    이 방식은 원본 row 내용은 파이프라인에서 생성하되,
    어떤 row가 train/test에 들어가는지는 기존 실험 membership으로 고정한다.
    """

    if not FROZEN_MEMBERSHIP.exists():
        raise FileNotFoundError(f"frozen membership 파일이 없습니다: {FROZEN_MEMBERSHIP}")

    candidate_path = REPO_ROOT / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"
    out_dir = REPO_ROOT / "data" / "track6_split"
    out_dir.mkdir(parents=True, exist_ok=True)

    candidate = pd.read_csv(candidate_path, low_memory=False)
    membership = pd.read_csv(FROZEN_MEMBERSHIP)
    required = {"split", "track6_row_id", "artist_key"}
    missing = required - set(membership.columns)
    if missing:
        raise ValueError(f"membership 필수 컬럼이 없습니다: {sorted(missing)}")

    row_ids = membership["track6_row_id"].astype(int)
    if row_ids.max() >= len(candidate) or row_ids.min() < 0:
        raise ValueError("membership의 track6_row_id가 후보 CSV row 범위를 벗어납니다.")

    candidate_keys = candidate.loc[row_ids, "artist_key"].astype(str).reset_index(drop=True)
    member_keys = membership["artist_key"].astype(str).reset_index(drop=True)
    mismatch = int((candidate_keys != member_keys).sum())
    if mismatch:
        raise ValueError(f"membership artist_key와 후보 CSV artist_key가 맞지 않습니다: mismatch={mismatch}")

    assembled = candidate.loc[row_ids].copy().reset_index(drop=True)
    assembled["_track6_row_id"] = row_ids.to_numpy()
    assembled["_split"] = membership["split"].astype(str).to_numpy()
    assembled = apply_frozen_identity_columns(assembled)

    train_counts = assembled.loc[assembled["_split"].eq("train"), "artist_key"].value_counts()
    assembled["artist_works_count_train"] = assembled["artist_key"].map(train_counts).fillna(0).astype(int)
    assembled["artist_works_log"] = (assembled["artist_works_count_train"].astype(float) + 1.0).map(math.log)

    split_to_file = {
        "train": "track6_train.csv",
        "val_warm": "track6_val_warm.csv",
        "test_warm": "track6_test_warm.csv",
        "val_cold": "track6_val_cold.csv",
        "test_cold": "track6_test_cold.csv",
    }
    summary: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "frozen_membership",
        "membership": str(FROZEN_MEMBERSHIP),
        "files": {},
    }

    for split, file_name in split_to_file.items():
        frame = assembled.loc[assembled["_split"].eq(split)].drop(columns=["_split"]).copy()
        frozen_columns = pd.read_csv(FROZEN_REFERENCE_SPLIT / file_name, nrows=0).columns.tolist()
        frame = frame[[column for column in frozen_columns if column in frame.columns]]
        frame.to_csv(out_dir / file_name, index=False)
        summary["files"][split] = {
            "path": str((out_dir / file_name).relative_to(REPO_ROOT)),
            "rows": int(len(frame)),
            "columns": int(len(frame.columns)),
            "artists": int(frame["artist_key"].nunique()),
            "artist_name_ko": int(frame["artist_name_ko"].nunique()),
        }

    membership.to_csv(out_dir / "track6_split_membership.csv", index=False)
    (out_dir / "track6_split_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"frozen_membership_split": summary["files"]}, ensure_ascii=False))


def apply_frozen_identity_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply frozen artist identity columns for existing experiment rows.

    기존 frozen split은 단순 membership만이 아니라 동명이인 처리 결과도
    고정되어 있다. 현재 작가명 매핑/동명이인 코드가 조금 달라지면 같은 row라도
    `artist_name_ko`가 달라질 수 있고, 그러면 Cold overlap 검증 결과가 달라진다.

    대표 사례:
        - 기존 frozen: `hyun jung kim` -> `김현정_B`
        - 현재 재생성: `hyun jung kim` -> `김중현`

    기존 실험 데이터셋을 재현하려면 평가 split membership뿐 아니라 당시 확정된
    작가 표시명/동명이인 suffix도 고정해야 한다. 이 함수는 frozen full split에서
    해당 identity 컬럼만 가져와 `_track6_row_id` 기준으로 덮어쓴다.
    """

    frozen_parts = []
    for file_name in [
        "track6_train.csv",
        "track6_val_warm.csv",
        "track6_test_warm.csv",
        "track6_val_cold.csv",
        "track6_test_cold.csv",
    ]:
        path = FROZEN_REFERENCE_SPLIT / file_name
        cols = ["_track6_row_id", *FROZEN_IDENTITY_COLUMNS]
        frozen_parts.append(pd.read_csv(path, usecols=cols, low_memory=False))

    frozen_identity = pd.concat(frozen_parts, ignore_index=True).drop_duplicates("_track6_row_id", keep="first")
    out = frame.drop(columns=[col for col in FROZEN_IDENTITY_COLUMNS if col in frame.columns], errors="ignore")
    out = out.merge(frozen_identity, on="_track6_row_id", how="left", validate="many_to_one")
    return out


def attach_nant_columns_to_working_splits() -> None:
    """Attach NANT material columns to already-created `data/track6_split`.

    기존 frozen dataset을 재현할 때 중요한 순서:
        1. split은 난트 컬럼이 붙기 전의 후보 데이터 기준으로 만든다.
        2. 그 뒤 후보 데이터에 난트 재료/지지체 컬럼을 붙인다.
        3. 이미 만들어진 split 파일에는 `_track6_row_id`로 난트 컬럼을 병합한다.

    이렇게 해야 평가 row 선택은 기존과 동일하게 유지하면서,
    full split 파일은 기존 frozen처럼 50컬럼이 된다.

    `_track6_row_id`는 `create_track6_splits.py`가 후보 CSV의 원래 row index를
    기록한 값이다. 그래서 보강된 후보 CSV를 `reset_index()`한 값과 병합하면
    split row에 해당하는 난트 컬럼을 되돌려 붙일 수 있다.
    """

    candidate_path = REPO_ROOT / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"
    split_dir = REPO_ROOT / "data" / "track6_split"
    candidate = pd.read_csv(candidate_path, low_memory=False)
    missing = [column for column in NANT_COLUMNS if column not in candidate.columns]
    if missing:
        raise RuntimeError(f"난트 보강 컬럼이 후보 데이터에 없습니다: {missing}")

    lookup = candidate.reset_index().rename(columns={"index": "_track6_row_id"})
    lookup = lookup[["_track6_row_id", *NANT_COLUMNS]].copy()

    for split_name in ["train", "val_warm", "test_warm", "val_cold", "test_cold"]:
        path = split_dir / f"track6_{split_name}.csv"
        frame = pd.read_csv(path, low_memory=False)
        before_rows = len(frame)
        frame = frame.drop(columns=[column for column in NANT_COLUMNS if column in frame.columns], errors="ignore")
        merged = frame.merge(lookup, on="_track6_row_id", how="left", validate="many_to_one")
        if len(merged) != before_rows:
            raise RuntimeError(f"난트 컬럼 병합 중 row 수가 바뀌었습니다: {path}")
        merged.to_csv(path, index=False)


def remove_existing_output(path: Path) -> None:
    """Remove an existing output directory before copying a fresh frozen split."""

    if path.exists():
        shutil.rmtree(path)


def copy_generated_split_to_frozen_output(output_dir: Path, *, dry_run: bool) -> None:
    """Copy generated `data/track6_split` into a frozen output directory."""

    generated = REPO_ROOT / "data" / "track6_split"
    if not generated.exists():
        raise FileNotFoundError(f"생성된 split 폴더가 없습니다: {generated}")

    if dry_run:
        print(f"[dry-run] would copy {generated} -> {output_dir}")
        return

    remove_existing_output(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        generated,
        output_dir,
        ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"),
    )


def legacy_is_price_like(column: str) -> bool:
    """Return whether a column name looks like target/price leakage.

    기존 feature export에서도 가격, 판매, 금액 계열 컬럼은 feature에서 제외했다.
    단 `estimated_ho`는 가격이 아니라 작품 크기 호수 추정값이라 예외로 둔다.
    """

    if column in LEGACY_PRICE_LEAK_ALLOWLIST:
        return False
    lowered = column.lower()
    return any(token in lowered for token in LEGACY_PRICE_LEAK_TOKENS)


def legacy_removed_columns(frame: pd.DataFrame, *, task: str) -> list[str]:
    """Return columns to remove for the legacy Track6 v0.1 feature export.

    현재 export 스크립트와 가장 중요한 차이:
        - `collected_material_raw`는 제거하지 않는다.
        - `nant_*` 컬럼도 제거하지 않는다.

    이 차이가 기존 frozen feature 23/20 컬럼을 재현하는 핵심이다.
    """

    removed = {
        column
        for column in frame.columns
        if column in LEGACY_TARGET_COLUMNS
        or column in LEGACY_TRACKING_ONLY_COLUMNS
        or column in LEGACY_MODEL_EXCLUDE_COLUMNS
        or any(column.startswith(prefix) for prefix in LEGACY_MODEL_EXCLUDE_PREFIXES)
        or legacy_is_price_like(column)
    }
    if task == "cold":
        removed.update(column for column in LEGACY_COLD_FORBIDDEN_COLUMNS if column in frame.columns)
    return sorted(removed)


def rebuild_legacy_feature_label_files(output_dir: Path) -> None:
    """Rebuild feature/label files inside frozen output using legacy rules.

    실행 순서상 현재 repo의 `export_feature_label_splits.py`도 이미 실행된다.
    하지만 그 스크립트의 현재 기준은 기존 frozen feature와 다르기 때문에,
    frozen output 폴더 안에서는 기존 실험 기준으로 다시 export한다.

    이 함수는 full split CSV 5개를 읽어:
        - labels/*.csv
        - features/warm/*.csv
        - features/cold/*.csv
    를 다시 쓴다.
    """

    feature_root = output_dir / "features"
    label_root = output_dir / "labels"
    warm_root = feature_root / "warm"
    cold_root = feature_root / "cold"
    warm_root.mkdir(parents=True, exist_ok=True)
    cold_root.mkdir(parents=True, exist_ok=True)
    label_root.mkdir(parents=True, exist_ok=True)

    split_names = ["train", "val_warm", "test_warm", "val_cold", "test_cold"]
    frames = {
        split: pd.read_csv(output_dir / f"track6_{split}.csv", low_memory=False)
        for split in split_names
    }

    for split, frame in frames.items():
        label_cols = [
            col
            for col in [*LEGACY_LABEL_META_COLUMNS, *LEGACY_TARGET_COLUMNS]
            if col in frame.columns
        ]
        labels = frame[list(dict.fromkeys(label_cols))].copy()
        labels.to_csv(label_root / f"track6_{split}_labels.csv", index=False)

    for split in ["train", "val_warm", "test_warm"]:
        frame = frames[split]
        features = frame.drop(columns=legacy_removed_columns(frame, task="warm"), errors="ignore").copy()
        frozen_feature_columns = pd.read_csv(
            FROZEN_REFERENCE_SPLIT / "features" / "warm" / f"track6_{split}_warm_features.csv",
            nrows=0,
        ).columns.tolist()
        features = features[[column for column in frozen_feature_columns if column in features.columns]]
        features.to_csv(warm_root / f"track6_{split}_warm_features.csv", index=False)

    for split in ["train", "val_cold", "test_cold"]:
        frame = frames[split]
        features = frame.drop(columns=legacy_removed_columns(frame, task="cold"), errors="ignore").copy()
        frozen_feature_columns = pd.read_csv(
            FROZEN_REFERENCE_SPLIT / "features" / "cold" / f"track6_{split}_cold_features.csv",
            nrows=0,
        ).columns.tolist()
        features = features[[column for column in frozen_feature_columns if column in features.columns]]
        features.to_csv(cold_root / f"track6_{split}_cold_features.csv", index=False)


def build_file_manifest(output_dir: Path) -> list[dict[str, Any]]:
    """Build checksum manifest for the frozen output directory."""

    rows: list[dict[str, Any]] = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        rows.append(
            {
                "relative_path": path.relative_to(output_dir).as_posix(),
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
    return rows


def audit_frozen_output(output_dir: Path) -> dict[str, Any]:
    """Check whether generated frozen output matches existing experiment expectations."""

    checks: list[dict[str, Any]] = []
    expectations = {**EXPECTED_SPLIT_SHAPES, **EXPECTED_FEATURE_LABEL_SHAPES}
    for relative, expected in expectations.items():
        path = output_dir / relative
        if not path.exists():
            checks.append(
                {
                    "path": relative,
                    "passed": False,
                    "actual": None,
                    "expected": expected,
                    "reason": "missing",
                }
            )
            continue
        actual = read_csv_shape(path)
        checks.append(
            {
                "path": relative,
                "passed": actual == expected,
                "actual": actual,
                "expected": expected,
                "reason": "ok" if actual == expected else "shape_mismatch",
            }
        )

    # Warm split 조건: 평가 작가가 train에 최소 5건 이상 남아 있는지.
    train = pd.read_csv(output_dir / "track6_train.csv", low_memory=False)
    train_counts = train["artist_key"].value_counts()
    for name in ["track6_val_warm.csv", "track6_test_warm.csv"]:
        frame = pd.read_csv(output_dir / name, low_memory=False)
        counts = frame["artist_key"].map(train_counts).fillna(0).astype(int)
        min_count = int(counts.min()) if len(counts) else 0
        checks.append(
            {
                "path": name,
                "passed": min_count >= 5,
                "actual": {"min_train_history": min_count},
                "expected": {"min_train_history_gte": 5},
                "reason": "warm_train_history_check",
            }
        )

    # Cold split 조건: train과 artist_key / 한글명 / 원한글명 겹침이 없는지.
    train_artist_keys = set(train["artist_key"].dropna().astype(str))
    train_names = set(train["artist_name_ko"].dropna().astype(str))
    train_orig_names = set(train["artist_name_ko_orig"].dropna().astype(str))
    for name in ["track6_val_cold.csv", "track6_test_cold.csv"]:
        frame = pd.read_csv(output_dir / name, low_memory=False)
        overlap_artist_key = len(set(frame["artist_key"].dropna().astype(str)) & train_artist_keys)
        overlap_name = len(set(frame["artist_name_ko"].dropna().astype(str)) & train_names)
        overlap_orig_name = len(set(frame["artist_name_ko_orig"].dropna().astype(str)) & train_orig_names)
        nonzero_history_rows = int((frame["artist_works_log"].fillna(0) > 0).sum()) if "artist_works_log" in frame.columns else -1
        passed = overlap_artist_key == 0 and overlap_name == 0 and overlap_orig_name == 0 and nonzero_history_rows == 0
        checks.append(
            {
                "path": name,
                "passed": passed,
                "actual": {
                    "artist_key_overlap": overlap_artist_key,
                    "artist_name_ko_overlap": overlap_name,
                    "artist_name_ko_orig_overlap": overlap_orig_name,
                    "artist_works_log_nonzero_rows": nonzero_history_rows,
                },
                "expected": {
                    "artist_key_overlap": 0,
                    "artist_name_ko_overlap": 0,
                    "artist_name_ko_orig_overlap": 0,
                    "artist_works_log_nonzero_rows": 0,
                },
                "reason": "cold_no_train_overlap_check",
            }
        )

    return {
        "status": "pass" if all(item["passed"] for item in checks) else "fail",
        "checks": checks,
    }


def write_csv_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write checksum manifest CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_report(path: Path, summary: dict[str, Any]) -> None:
    """Write a readable build report."""

    lines = [
        "# Track6 frozen dataset build report",
        "",
        f"- created_at: `{summary['created_at']}`",
        f"- status: `{summary['status']}`",
        f"- repo_root: `{summary['repo_root']}`",
        f"- source_dir: `{summary['source_dir']}`",
        f"- frozen_output_dir: `{summary['frozen_output_dir']}`",
        "",
        "## 1. Source files",
        "",
        "| source | destination | bytes | sha256 |",
        "|---|---|---:|---|",
    ]
    for item in summary["source_files"]:
        lines.append(
            f"| `{item['source']}` | `{item['destination']}` | `{item['bytes']}` | `{item['sha256']}` |"
        )

    lines.extend(
        [
            "",
            "## 2. Pipeline steps",
            "",
            "| step | script | return code | role |",
            "|---|---|---:|---|",
        ]
    )
    for step in summary["steps"]:
        lines.append(
            f"| `{step['name']}` | `{step['script']}` | `{step['return_code']}` | {step['description']} |"
        )

    lines.extend(
        [
            "",
            "## 3. Frozen output audit",
            "",
            f"- audit_status: `{summary['audit']['status']}`",
            "",
            "| path | status | actual | expected | reason |",
            "|---|---|---|---|---|",
        ]
    )
    for check in summary["audit"]["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        actual = json.dumps(check["actual"], ensure_ascii=False)
        expected = json.dumps(check["expected"], ensure_ascii=False)
        lines.append(f"| `{check['path']}` | `{status}` | `{actual}` | `{expected}` | `{check['reason']}` |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Build Track6 frozen experiment dataset from source CSV files.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=SHARE_ROOT,
        help=(
            "원본 CSV가 들어 있는 폴더. 기본값은 이 스크립트가 있는 공유 폴더이며, "
            "공유 폴더 직하위 또는 01_source_files/ 아래에서 필수 파일을 찾는다."
        ),
    )
    parser.add_argument(
        "--frozen-output-dir",
        type=Path,
        default=SHARE_ROOT / "05_generated_frozen_training_dataset" / "track6_split",
        help="결과 데이터 출력 폴더. 기본값은 같은 공유 폴더 아래 05_generated_frozen_training_dataset/track6_split.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="파일 복사/파이프라인 실행 없이 실행 계획만 확인한다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    frozen_output_dir = args.frozen_output_dir.resolve()

    print("== Track6 frozen dataset build")
    print(f"repo_root: {REPO_ROOT}")
    print(f"source_dir: {source_dir}")
    print(f"frozen_output_dir: {frozen_output_dir}")

    source_files = copy_source_files(source_dir, dry_run=args.dry_run)
    steps = run_pipeline_steps(dry_run=args.dry_run)

    if args.dry_run:
        print("\nDry-run complete. No files were modified.")
        return 0

    copy_generated_split_to_frozen_output(frozen_output_dir, dry_run=False)
    rebuild_legacy_feature_label_files(frozen_output_dir)
    manifest = build_file_manifest(frozen_output_dir)
    audit = audit_frozen_output(frozen_output_dir)

    verification_dir = frozen_output_dir.parent / "verification"
    verification_dir.mkdir(parents=True, exist_ok=True)
    write_csv_manifest(verification_dir / "files_manifest.csv", manifest)

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": audit["status"],
        "repo_root": str(REPO_ROOT),
        "source_dir": str(source_dir),
        "frozen_output_dir": str(frozen_output_dir),
        "source_files": source_files,
        "steps": [step.__dict__ for step in steps],
        "manifest_file": str(verification_dir / "files_manifest.csv"),
        "audit": audit,
    }
    (verification_dir / "build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_markdown_report(verification_dir / "build_report.md", summary)

    print(f"\nstatus: {summary['status']}")
    print(f"frozen output: {frozen_output_dir}")
    print(f"build report: {verification_dir / 'build_report.md'}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
