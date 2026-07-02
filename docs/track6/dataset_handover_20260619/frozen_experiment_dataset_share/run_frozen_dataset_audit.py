#!/usr/bin/env python3
"""Audit the frozen Track6 experiment dataset in one command.

이 스크립트는 Track6 기존 실험 데이터셋 공유 폴더를 받은 사람이
한 번에 기준 데이터셋을 점검할 수 있게 만든 종합 점검 스크립트다.

중요한 설계 의도:
1. 이 스크립트는 데이터셋을 새로 만들지 않는다.
   - 기존 실험 성능표의 기준은 이미 고정된 frozen split이다.
   - 원본 CSV부터 현재 코드로 다시 돌리면 입력 후보가 달라질 수 있으므로
     기존 실험 재현 기준과 섞으면 안 된다.

2. 이 스크립트는 frozen split이 올바른 기준 파일인지 검증한다.
   - 모델 번들에 들어 있는 기준 데이터셋과 공유 폴더 복사본의 checksum 비교
   - train / validation / test row 수 확인
   - Warm / Cold split 조건 확인
   - feature / label 파일의 row 수 정합성 확인

실행 위치:
    repo root 또는 이 스크립트가 들어 있는 공유 폴더 어디에서 실행해도 된다.

예시:
    python3 docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/run_frozen_dataset_audit.py

출력:
    04_verification/frozen_dataset_audit_report.md
    04_verification/frozen_dataset_audit_summary.json
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------


def find_repo_root(start: Path) -> Path:
    """Find the repository root by walking upward until .git is found.

    공유 폴더 안에서 실행해도 되고 repo root에서 실행해도 되게 하기 위해
    현재 파일 위치부터 부모 폴더를 따라 올라가며 `.git` 폴더를 찾는다.
    """

    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / ".git").exists():
            return path
    raise RuntimeError("Repo root를 찾지 못했습니다. .git 폴더가 있는 repo 안에서 실행해야 합니다.")


SCRIPT_PATH = Path(__file__).resolve()
SHARE_ROOT = SCRIPT_PATH.parent
REPO_ROOT = find_repo_root(SCRIPT_PATH)

# 기존 Track6 v0.1 모델 번들에 들어 있는 기준 데이터셋.
# 기존 실험 성능표는 이 폴더의 split을 기준으로 나온다.
MODEL_BUNDLE_SPLIT = REPO_ROOT / "models" / "track6" / "price_prediction_v0.1" / "data" / "training" / "track6_split"

# 공유 폴더 안에 복사해 둔 frozen split.
# 외부 공유 시에는 이 폴더만 봐도 기존 실험 데이터셋을 확인할 수 있게 했다.
SHARED_FROZEN_SPLIT = SHARE_ROOT / "03_frozen_training_dataset" / "track6_split"

# 점검 결과를 저장할 위치.
VERIFICATION_DIR = SHARE_ROOT / "04_verification"


# ---------------------------------------------------------------------------
# 기존 실험에서 기대하는 row/column 기준
# ---------------------------------------------------------------------------


EXPECTED_FULL_SPLITS = {
    "track6_train.csv": {"rows": 26914, "columns": 50},
    "track6_val_warm.csv": {"rows": 519, "columns": 50},
    "track6_test_warm.csv": {"rows": 607, "columns": 50},
    "track6_val_cold.csv": {"rows": 2753, "columns": 50},
    "track6_test_cold.csv": {"rows": 3099, "columns": 50},
}

EXPECTED_FEATURES = {
    "features/warm/track6_train_warm_features.csv": {"rows": 26914, "columns": 23},
    "features/warm/track6_val_warm_warm_features.csv": {"rows": 519, "columns": 23},
    "features/warm/track6_test_warm_warm_features.csv": {"rows": 607, "columns": 23},
    "features/cold/track6_train_cold_features.csv": {"rows": 26914, "columns": 20},
    "features/cold/track6_val_cold_cold_features.csv": {"rows": 2753, "columns": 20},
    "features/cold/track6_test_cold_cold_features.csv": {"rows": 3099, "columns": 20},
}

EXPECTED_LABELS = {
    "labels/track6_train_labels.csv": {"rows": 26914, "columns": 12},
    "labels/track6_val_warm_labels.csv": {"rows": 519, "columns": 12},
    "labels/track6_test_warm_labels.csv": {"rows": 607, "columns": 12},
    "labels/track6_val_cold_labels.csv": {"rows": 2753, "columns": 12},
    "labels/track6_test_cold_labels.csv": {"rows": 3099, "columns": 12},
}


# Cold feature에는 같은 작가 이력 누수 가능성이 있는 컬럼이 없어야 한다.
# Cold는 train에 없는 작가를 예측하는 경로이기 때문에 artist_key나
# train 내 같은 작가 작품 수가 feature에 직접 들어가면 실험 정의와 충돌한다.
COLD_FORBIDDEN_FEATURE_COLUMNS = {
    "artist_key",
    "artist_works_log",
    "artist_works_count_train",
}


# Warm 평가셋은 같은 작가가 train에 남아 있는 상황을 평가한다.
# 기존 Stable Warm 평가는 평가 작품의 작가가 train에 최소 5작품 이상 남는 기준이다.
WARM_MIN_TRAIN_PER_ARTIST = 5


@dataclass
class CheckResult:
    """A single audit result.

    name:
        사람이 읽을 수 있는 점검 이름.
    passed:
        통과 여부.
    detail:
        통과/실패 이유를 짧게 설명한 문자열.
    """

    name: str
    passed: bool
    detail: str


# ---------------------------------------------------------------------------
# 작은 유틸 함수
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    """Return SHA256 checksum for a file.

    큰 CSV도 처리할 수 있게 한 번에 전부 읽지 않고 chunk 단위로 읽는다.
    """

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV with stable options for mixed-type columns."""

    return pd.read_csv(path, low_memory=False)


def check_exists(path: Path, label: str) -> CheckResult:
    """Check that a required file or directory exists."""

    return CheckResult(
        name=f"exists: {label}",
        passed=path.exists(),
        detail=str(path),
    )


def csv_shape(path: Path) -> dict[str, Any]:
    """Return row/column count for a CSV."""

    frame = read_csv(path)
    return {"rows": int(len(frame)), "columns": int(len(frame.columns))}


# ---------------------------------------------------------------------------
# Dataset audit checks
# ---------------------------------------------------------------------------


def audit_checksum_against_model_bundle() -> list[CheckResult]:
    """Compare shared frozen split files against model bundle files.

    이 검사는 공유 폴더의 frozen split이 실제 모델 번들 기준 데이터셋과
    byte-level로 같은지 확인한다. mismatch가 0이어야 기존 실험 기준 데이터셋을
    정확히 전달했다고 볼 수 있다.
    """

    results: list[CheckResult] = []

    if not MODEL_BUNDLE_SPLIT.exists():
        return [
            CheckResult(
                "checksum: model bundle split",
                False,
                f"모델 번들 split 폴더가 없습니다: {MODEL_BUNDLE_SPLIT}",
            )
        ]

    model_files = [
        path
        for path in sorted(MODEL_BUNDLE_SPLIT.rglob("*"))
        if path.is_file() and path.name != ".DS_Store"
    ]
    mismatch: list[str] = []
    missing: list[str] = []

    for model_file in model_files:
        relative = model_file.relative_to(MODEL_BUNDLE_SPLIT)
        shared_file = SHARED_FROZEN_SPLIT / relative
        if not shared_file.exists():
            missing.append(str(relative))
            continue
        if sha256_file(model_file) != sha256_file(shared_file):
            mismatch.append(str(relative))

    results.append(
        CheckResult(
            "checksum: shared frozen split matches model bundle",
            not missing and not mismatch,
            f"checked={len(model_files)}, missing={len(missing)}, mismatch={len(mismatch)}",
        )
    )
    if missing:
        results.append(CheckResult("checksum missing files", False, ", ".join(missing[:20])))
    if mismatch:
        results.append(CheckResult("checksum mismatch files", False, ", ".join(mismatch[:20])))
    return results


def audit_shapes() -> list[CheckResult]:
    """Check row/column counts for full split, feature, and label files."""

    results: list[CheckResult] = []
    groups = [
        ("full split", EXPECTED_FULL_SPLITS),
        ("features", EXPECTED_FEATURES),
        ("labels", EXPECTED_LABELS),
    ]

    for group_name, expectations in groups:
        for relative, expected in expectations.items():
            path = SHARED_FROZEN_SPLIT / relative
            if not path.exists():
                results.append(CheckResult(f"shape: {group_name}: {relative}", False, "file missing"))
                continue
            actual = csv_shape(path)
            passed = actual == expected
            results.append(
                CheckResult(
                    f"shape: {group_name}: {relative}",
                    passed,
                    f"actual={actual}, expected={expected}",
                )
            )
    return results


def audit_warm_split_definition() -> list[CheckResult]:
    """Check that Warm validation/test artists have enough train history."""

    train = read_csv(SHARED_FROZEN_SPLIT / "track6_train.csv")
    train_counts = train["artist_key"].value_counts()
    results: list[CheckResult] = []

    for file_name in ["track6_val_warm.csv", "track6_test_warm.csv"]:
        frame = read_csv(SHARED_FROZEN_SPLIT / file_name)

        # 각 평가 row의 작가가 train에 몇 작품 남아 있는지 계산한다.
        # Stable Warm 기준에서는 이 값이 모두 5 이상이어야 한다.
        counts = frame["artist_key"].map(train_counts).fillna(0).astype(int)
        min_count = int(counts.min()) if len(counts) else 0
        missing_artist_rows = int((counts == 0).sum())
        passed = min_count >= WARM_MIN_TRAIN_PER_ARTIST and missing_artist_rows == 0

        results.append(
            CheckResult(
                f"warm definition: {file_name}",
                passed,
                f"min_train_history={min_count}, missing_artist_rows={missing_artist_rows}",
            )
        )
    return results


def audit_cold_split_definition() -> list[CheckResult]:
    """Check that Cold validation/test artists and names do not overlap train."""

    train = read_csv(SHARED_FROZEN_SPLIT / "track6_train.csv")
    train_artist_keys = set(train["artist_key"].dropna().astype(str))
    train_names = set(train["artist_name_ko"].dropna().astype(str))
    train_orig_names = set(train["artist_name_ko_orig"].dropna().astype(str))

    results: list[CheckResult] = []
    for file_name in ["track6_val_cold.csv", "track6_test_cold.csv"]:
        frame = read_csv(SHARED_FROZEN_SPLIT / file_name)

        overlap_artist_key = len(set(frame["artist_key"].dropna().astype(str)) & train_artist_keys)
        overlap_name = len(set(frame["artist_name_ko"].dropna().astype(str)) & train_names)
        overlap_orig_name = len(set(frame["artist_name_ko_orig"].dropna().astype(str)) & train_orig_names)

        # split 이후 train 기준 같은 작가 작품 수가 Cold row에 남아 있으면 누수 가능성이다.
        nonzero_artist_history_rows = 0
        if "artist_works_log" in frame.columns:
            nonzero_artist_history_rows = int((frame["artist_works_log"].fillna(0) > 0).sum())

        passed = (
            overlap_artist_key == 0
            and overlap_name == 0
            and overlap_orig_name == 0
            and nonzero_artist_history_rows == 0
        )
        results.append(
            CheckResult(
                f"cold definition: {file_name}",
                passed,
                "artist_key_overlap="
                f"{overlap_artist_key}, artist_name_ko_overlap={overlap_name}, "
                f"artist_name_ko_orig_overlap={overlap_orig_name}, "
                f"artist_works_log_nonzero_rows={nonzero_artist_history_rows}",
            )
        )
    return results


def audit_feature_label_alignment() -> list[CheckResult]:
    """Check that feature and label rows align for each split.

    여기서는 row 수와 `_track6_row_id` 기준 정렬을 확인한다.
    모델 학습 시 feature와 label이 같은 작품 순서로 대응되어야 하기 때문이다.
    """

    pairs = [
        (
            "warm train",
            "features/warm/track6_train_warm_features.csv",
            "labels/track6_train_labels.csv",
        ),
        (
            "warm validation",
            "features/warm/track6_val_warm_warm_features.csv",
            "labels/track6_val_warm_labels.csv",
        ),
        (
            "warm test",
            "features/warm/track6_test_warm_warm_features.csv",
            "labels/track6_test_warm_labels.csv",
        ),
        (
            "cold train",
            "features/cold/track6_train_cold_features.csv",
            "labels/track6_train_labels.csv",
        ),
        (
            "cold validation",
            "features/cold/track6_val_cold_cold_features.csv",
            "labels/track6_val_cold_labels.csv",
        ),
        (
            "cold test",
            "features/cold/track6_test_cold_cold_features.csv",
            "labels/track6_test_cold_labels.csv",
        ),
    ]

    results: list[CheckResult] = []
    for label, feature_relative, label_relative in pairs:
        features = read_csv(SHARED_FROZEN_SPLIT / feature_relative)
        labels = read_csv(SHARED_FROZEN_SPLIT / label_relative)

        same_rows = len(features) == len(labels)
        has_row_id = "_track6_row_id" in features.columns and "_track6_row_id" in labels.columns
        same_row_ids = False
        if same_rows and has_row_id:
            same_row_ids = features["_track6_row_id"].astype(str).equals(labels["_track6_row_id"].astype(str))

        results.append(
            CheckResult(
                f"feature/label alignment: {label}",
                same_rows and has_row_id and same_row_ids,
                f"feature_rows={len(features)}, label_rows={len(labels)}, "
                f"has_row_id={has_row_id}, same_row_ids={same_row_ids}",
            )
        )
    return results


def audit_cold_forbidden_features() -> list[CheckResult]:
    """Check that Cold feature files do not contain direct same-artist history keys."""

    results: list[CheckResult] = []
    for relative in [
        "features/cold/track6_train_cold_features.csv",
        "features/cold/track6_val_cold_cold_features.csv",
        "features/cold/track6_test_cold_cold_features.csv",
    ]:
        frame = read_csv(SHARED_FROZEN_SPLIT / relative)
        forbidden = sorted(COLD_FORBIDDEN_FEATURE_COLUMNS & set(frame.columns))
        results.append(
            CheckResult(
                f"cold forbidden feature columns: {relative}",
                not forbidden,
                f"forbidden_columns={forbidden}",
            )
        )
    return results


def collect_source_file_summary() -> list[dict[str, Any]]:
    """Summarize source CSV files included in the package.

    이 값은 모델 학습 row 수와 직접 비교하는 값이 아니다.
    원본 공유 파일이 존재하고 대략 어떤 규모인지 확인하기 위한 요약이다.
    """

    source_dir = SHARE_ROOT / "01_source_files"
    rows: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.csv")):
        frame = read_csv(path)
        rows.append(
            {
                "file": path.name,
                "rows": int(len(frame)),
                "columns": int(len(frame.columns)),
                "bytes": int(path.stat().st_size),
            }
        )
    return rows


def run_audit() -> dict[str, Any]:
    """Run all checks and return a serializable summary."""

    VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)

    results: list[CheckResult] = []
    results.append(check_exists(SHARE_ROOT, "share root"))
    results.append(check_exists(MODEL_BUNDLE_SPLIT, "model bundle frozen split"))
    results.append(check_exists(SHARED_FROZEN_SPLIT, "shared frozen split"))
    results.extend(audit_checksum_against_model_bundle())
    results.extend(audit_shapes())
    results.extend(audit_warm_split_definition())
    results.extend(audit_cold_split_definition())
    results.extend(audit_feature_label_alignment())
    results.extend(audit_cold_forbidden_features())

    source_files = collect_source_file_summary()
    passed = all(item.passed for item in results)

    return {
        "status": "pass" if passed else "fail",
        "repo_root": str(REPO_ROOT),
        "share_root": str(SHARE_ROOT),
        "model_bundle_split": str(MODEL_BUNDLE_SPLIT),
        "shared_frozen_split": str(SHARED_FROZEN_SPLIT),
        "source_files": source_files,
        "checks": [
            {"name": item.name, "passed": item.passed, "detail": item.detail}
            for item in results
        ],
    }


def write_report(summary: dict[str, Any]) -> None:
    """Write machine-readable JSON and human-readable Markdown reports."""

    json_path = VERIFICATION_DIR / "frozen_dataset_audit_summary.json"
    md_path = VERIFICATION_DIR / "frozen_dataset_audit_report.md"

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Frozen Track6 기존 실험 데이터셋 종합 점검",
        "",
        f"- status: `{summary['status']}`",
        f"- repo root: `{summary['repo_root']}`",
        f"- 공유 폴더: `{summary['share_root']}`",
        f"- 모델 번들 기준 split: `{summary['model_bundle_split']}`",
        f"- 공유 frozen split: `{summary['shared_frozen_split']}`",
        "",
        "## 원본 CSV 요약",
        "",
        "| file | rows | columns | bytes |",
        "|---|---:|---:|---:|",
    ]
    for item in summary["source_files"]:
        lines.append(f"| `{item['file']}` | `{item['rows']}` | `{item['columns']}` | `{item['bytes']}` |")

    lines.extend(
        [
            "",
            "## 점검 결과",
            "",
            "| check | status | detail |",
            "|---|---|---|",
        ]
    )
    for item in summary["checks"]:
        status = "PASS" if item["passed"] else "FAIL"
        detail = str(item["detail"]).replace("|", "\\|")
        lines.append(f"| {item['name']} | `{status}` | {detail} |")

    md_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    """CLI entry point."""

    summary = run_audit()
    write_report(summary)

    print(f"status: {summary['status']}")
    print(f"report: {VERIFICATION_DIR / 'frozen_dataset_audit_report.md'}")
    print(f"json: {VERIFICATION_DIR / 'frozen_dataset_audit_summary.json'}")

    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
