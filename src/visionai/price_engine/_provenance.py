"""Provenance manifest helper for primary-market price engine artifacts.

코덱스 하네스 리뷰 P1 (2026-04-30): 학습/진단 산출물에 git SHA, 데이터 해시,
의존성 버전, parser rule version, 생성 시각을 자동 stamping 하기 위한 공용 모듈.

사용 예시:
    from visionai.price_engine._provenance import (
        _provenance_dict, write_provenance_manifest,
    )

    payload = _provenance_dict(
        model_target="integrated_v3_filtered_tuned",
        data_paths={
            "artsy": Path("data/primary_market_dataset.parquet"),
            "saatchi": Path("data/saatchi_cleaned.parquet"),
        },
        artifact_paths={
            "catboost": Path("model_test_results/integrated_v3_filtered_tuned_catboost.cbm"),
            "xgboost": Path("model_test_results/integrated_v3_filtered_tuned_xgboost.json"),
        },
    )
    write_provenance_manifest(
        Path("model_test_results/integrated_v3_filtered_tuned_provenance.json"),
        payload=payload,
    )
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Any

DEFAULT_DEPENDENCY_PACKAGES: tuple[str, ...] = (
    "pandas",
    "numpy",
    "scikit-learn",
    "catboost",
    "xgboost",
    "scipy",
    "matplotlib",
)
"""기본 추적 의존성. OOF reproducibility 핵심 패키지 우선."""

DEFAULT_PARSER_RULE_FILES: tuple[str, ...] = (
    "src/visionai/price_engine/preprocessing/primary_medium_parser.py",
    "data/k-artmarket 1차 데이터 정제 - 지지체(바탕재) 분류.csv",
    "data/k-artmarket 1차 데이터 정제 - 도구_기법 분류.csv",
)
"""primary_medium_parser rule source — 입체 분류 / 매체 분류 시트 + 파서 코드."""


def _git_sha(repo_root: Path) -> str | None:
    """Return current git commit SHA (HEAD), None if git unavailable."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None


def _git_dirty(repo_root: Path) -> bool | None:
    """Return True if working tree has uncommitted modifications to tracked files.

    Excludes untracked files. This stable definition prevents flip-flopping when
    a script writes a new artifact (e.g. a manifest) mid-run — the new file is
    untracked, so it would not flip dirty=True under this rule.

    Implementation: `git diff --quiet` (working tree vs index) AND
    `git diff --cached --quiet` (index vs HEAD). dirty if either is non-zero.
    """
    try:
        for cmd in (
            ["git", "-C", str(repo_root), "diff", "--quiet"],
            ["git", "-C", str(repo_root), "diff", "--cached", "--quiet"],
        ):
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode not in (0, 1):
                # 0=clean, 1=changes, anything else = git error
                return None
            if res.returncode == 1:
                return True
        return False
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None


def _file_sha256(path: Path) -> str:
    """Return sha256 hex digest of file content."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_meta(path: Path) -> dict[str, Any]:
    """File metadata: existence, size, sha256."""
    if not path.exists():
        return {"exists": False, "size_bytes": None, "sha256": None}
    return {
        "exists": True,
        "size_bytes": path.stat().st_size,
        "sha256": _file_sha256(path),
    }


def _dependency_versions(packages: tuple[str, ...]) -> dict[str, str | None]:
    """Resolve installed package versions via importlib.metadata. None if missing."""
    out: dict[str, str | None] = {}
    for p in packages:
        try:
            out[p] = pkg_version(p)
        except PackageNotFoundError:
            out[p] = None
    return out


def _parser_rule_version(
    repo_root: Path,
    files: tuple[str, ...],
) -> dict[str, Any]:
    """Compose parser rule version: combined hash + per-file metadata.

    Combined hash is sha256 of concatenated per-file sha256 hex strings (in input
    order). Files with missing sha256 are skipped from the combined input.
    """
    metas: dict[str, dict[str, Any]] = {}
    combined = hashlib.sha256()
    any_hashed = False
    for f in files:
        p = repo_root / f
        meta = _file_meta(p)
        metas[f] = meta
        if meta.get("sha256"):
            combined.update(meta["sha256"].encode())
            any_hashed = True
    return {
        "combined_sha256": combined.hexdigest() if any_hashed else None,
        "files": metas,
    }


def _provenance_dict(
    *,
    model_target: str,
    data_paths: dict[str, Path],
    parser_rule_files: tuple[str, ...] = DEFAULT_PARSER_RULE_FILES,
    artifact_paths: dict[str, Path] | None = None,
    dependency_packages: tuple[str, ...] = DEFAULT_DEPENDENCY_PACKAGES,
    repo_root: Path | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build provenance manifest payload.

    Required keys (always present):
    - model_target, git_sha, git_dirty, created_at_utc
    - data_hashes (dict of name → file meta)
    - dependency_versions (dict of pkg → version str)
    - parser_rule_version (combined sha + per-file meta)

    Optional keys:
    - artifact_hashes (if artifact_paths provided)
    - extra (free-form caller metadata, e.g. n_rows, hyperparams)
    """
    if repo_root is None:
        # src/visionai/price_engine/_provenance.py → repo root is 4 levels up
        repo_root = Path(__file__).resolve().parents[3]

    payload: dict[str, Any] = {
        "model_target": model_target,
        "git_sha": _git_sha(repo_root),
        "git_dirty": _git_dirty(repo_root),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "data_hashes": {name: _file_meta(path) for name, path in data_paths.items()},
        "dependency_versions": _dependency_versions(dependency_packages),
        "parser_rule_version": _parser_rule_version(repo_root, parser_rule_files),
    }
    if artifact_paths:
        payload["artifact_hashes"] = {
            name: _file_meta(path) for name, path in artifact_paths.items()
        }
    if extra:
        payload["extra"] = extra
    return payload


def write_provenance_manifest(output_path: Path, *, payload: dict[str, Any]) -> None:
    """Write payload as JSON. Creates parent directory if needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)


def stamp_artifact_with_provenance(
    artifact_path: Path,
    *,
    model_target: str,
    data_paths: dict[str, Path],
    parser_rule_files: tuple[str, ...] = DEFAULT_PARSER_RULE_FILES,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Convenience: build payload + write to `<artifact>.provenance.json` sibling.

    Returns the written manifest path.
    """
    payload = _provenance_dict(
        model_target=model_target,
        data_paths=data_paths,
        parser_rule_files=parser_rule_files,
        artifact_paths={"main": artifact_path},
        extra=extra,
    )
    manifest_path = artifact_path.with_suffix(artifact_path.suffix + ".provenance.json")
    write_provenance_manifest(manifest_path, payload=payload)
    return manifest_path
