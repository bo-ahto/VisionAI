"""Tests for visionai.price_engine._provenance."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from visionai.price_engine._provenance import (
    DEFAULT_DEPENDENCY_PACKAGES,
    _dependency_versions,
    _file_meta,
    _file_sha256,
    _git_dirty,
    _git_sha,
    _parser_rule_version,
    _provenance_dict,
    stamp_artifact_with_provenance,
    write_provenance_manifest,
)

# ─── _file_sha256 / _file_meta ─────────────────────────────────────────


def test_file_sha256_matches_hashlib(tmp_path: Path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"hello world")
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert _file_sha256(p) == expected


def test_file_sha256_deterministic(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("repeatable content")
    assert _file_sha256(p) == _file_sha256(p)


def test_file_sha256_large_file_chunked(tmp_path: Path) -> None:
    """File larger than chunk size (64KB) hashes correctly via chunked read."""
    p = tmp_path / "big.bin"
    payload = b"a" * (65536 * 3 + 17)
    p.write_bytes(payload)
    expected = hashlib.sha256(payload).hexdigest()
    assert _file_sha256(p) == expected


def test_file_meta_missing(tmp_path: Path) -> None:
    m = _file_meta(tmp_path / "missing.txt")
    assert m == {"exists": False, "size_bytes": None, "sha256": None}


def test_file_meta_exists(tmp_path: Path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"abc")
    m = _file_meta(p)
    assert m["exists"] is True
    assert m["size_bytes"] == 3
    assert isinstance(m["sha256"], str) and len(m["sha256"]) == 64


# ─── _git_sha / _git_dirty ─────────────────────────────────────────────


def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@e"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)
    (repo / "README").write_text("init")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)


def test_git_sha_returns_hex_for_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    sha = _git_sha(tmp_path)
    assert sha is not None
    assert len(sha) == 40
    assert all(c in "0123456789abcdef" for c in sha)


def test_git_sha_returns_none_for_non_repo(tmp_path: Path) -> None:
    assert _git_sha(tmp_path) is None


def test_git_dirty_false_after_commit(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    assert _git_dirty(tmp_path) is False


def test_git_dirty_true_with_unstaged_changes(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "README").write_text("modified")
    assert _git_dirty(tmp_path) is True


def test_git_dirty_false_with_untracked_files(tmp_path: Path) -> None:
    """untracked 파일은 dirty 로 잡지 않음 (manifest 자기 contamination 방지)."""
    _init_git_repo(tmp_path)
    (tmp_path / "new_file.txt").write_text("not staged")
    assert _git_dirty(tmp_path) is False


def test_git_dirty_true_with_staged_changes(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "README").write_text("modified")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    assert _git_dirty(tmp_path) is True


# ─── _dependency_versions ──────────────────────────────────────────────


def test_dependency_versions_resolves_installed() -> None:
    versions = _dependency_versions(("pytest",))
    assert "pytest" in versions
    assert versions["pytest"] is not None


def test_dependency_versions_returns_none_for_missing() -> None:
    versions = _dependency_versions(("definitely_not_a_real_pkg_xyz_123",))
    assert versions["definitely_not_a_real_pkg_xyz_123"] is None


def test_dependency_versions_default_set_resolvable() -> None:
    versions = _dependency_versions(DEFAULT_DEPENDENCY_PACKAGES)
    # 적어도 일부는 설치돼 있어야 함 (test 환경)
    assert any(v is not None for v in versions.values())


# ─── _parser_rule_version ──────────────────────────────────────────────


def test_parser_rule_version_combined_changes_with_content(tmp_path: Path) -> None:
    f1 = tmp_path / "rule1.txt"
    f1.write_text("v1")
    out_a = _parser_rule_version(tmp_path, ("rule1.txt",))
    f1.write_text("v2")
    out_b = _parser_rule_version(tmp_path, ("rule1.txt",))
    assert out_a["combined_sha256"] != out_b["combined_sha256"]


def test_parser_rule_version_missing_files_combined_none(tmp_path: Path) -> None:
    out = _parser_rule_version(tmp_path, ("nonexistent.txt",))
    assert out["combined_sha256"] is None
    assert out["files"]["nonexistent.txt"]["exists"] is False


def test_parser_rule_version_partial_missing_still_hashes(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    out = _parser_rule_version(tmp_path, ("a.txt", "missing.txt"))
    assert out["combined_sha256"] is not None
    assert out["files"]["a.txt"]["exists"] is True
    assert out["files"]["missing.txt"]["exists"] is False


# ─── _provenance_dict ──────────────────────────────────────────────────


def test_provenance_dict_contains_all_required_keys(tmp_path: Path) -> None:
    payload = _provenance_dict(
        model_target="test",
        data_paths={},
        parser_rule_files=(),
        repo_root=tmp_path,
    )
    required = {
        "model_target",
        "git_sha",
        "git_dirty",
        "created_at_utc",
        "data_hashes",
        "dependency_versions",
        "parser_rule_version",
    }
    assert required.issubset(payload.keys())


def test_provenance_dict_artifact_paths_optional(tmp_path: Path) -> None:
    payload = _provenance_dict(
        model_target="t",
        data_paths={},
        parser_rule_files=(),
        repo_root=tmp_path,
    )
    assert "artifact_hashes" not in payload


def test_provenance_dict_artifact_paths_present_when_given(tmp_path: Path) -> None:
    a = tmp_path / "art.json"
    a.write_text("{}")
    payload = _provenance_dict(
        model_target="t",
        data_paths={},
        parser_rule_files=(),
        artifact_paths={"main": a},
        repo_root=tmp_path,
    )
    assert "artifact_hashes" in payload
    assert payload["artifact_hashes"]["main"]["exists"] is True
    assert isinstance(payload["artifact_hashes"]["main"]["sha256"], str)


def test_provenance_dict_extra_passthrough(tmp_path: Path) -> None:
    payload = _provenance_dict(
        model_target="t",
        data_paths={},
        parser_rule_files=(),
        repo_root=tmp_path,
        extra={"n_rows": 28376, "hp": {"depth": 8}},
    )
    assert payload["extra"]["n_rows"] == 28376
    assert payload["extra"]["hp"] == {"depth": 8}


def test_provenance_dict_data_hashes_stable_for_same_content(tmp_path: Path) -> None:
    p = tmp_path / "data.parquet"
    p.write_bytes(b"deterministic content")
    payload1 = _provenance_dict(
        model_target="t",
        data_paths={"d": p},
        parser_rule_files=(),
        repo_root=tmp_path,
    )
    payload2 = _provenance_dict(
        model_target="t",
        data_paths={"d": p},
        parser_rule_files=(),
        repo_root=tmp_path,
    )
    assert payload1["data_hashes"]["d"]["sha256"] == payload2["data_hashes"]["d"]["sha256"]


def test_provenance_dict_iso8601_utc_timestamp(tmp_path: Path) -> None:
    payload = _provenance_dict(
        model_target="t",
        data_paths={},
        parser_rule_files=(),
        repo_root=tmp_path,
    )
    ts = payload["created_at_utc"]
    assert isinstance(ts, str)
    assert "T" in ts
    assert ts.endswith("+00:00") or ts.endswith("Z")


# ─── write_provenance_manifest ─────────────────────────────────────────


def test_write_manifest_round_trip(tmp_path: Path) -> None:
    payload = {"x": 1, "ts": "2026-04-30T00:00:00+00:00", "nested": {"k": "v"}}
    out = tmp_path / "out.json"
    write_provenance_manifest(out, payload=payload)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload


def test_write_manifest_creates_parent_dirs(tmp_path: Path) -> None:
    out = tmp_path / "deep" / "nest" / "out.json"
    write_provenance_manifest(out, payload={"k": "v"})
    assert out.exists()


def test_write_manifest_unicode_safe(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    write_provenance_manifest(out, payload={"한글": "정상", "emoji": "ok"})
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["한글"] == "정상"


def test_write_manifest_uses_str_default_for_path(tmp_path: Path) -> None:
    """Path 같은 비-JSON-native 객체도 default=str로 직렬화 가능해야 한다."""
    out = tmp_path / "out.json"
    write_provenance_manifest(out, payload={"path": Path("/some/where")})
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["path"] == "/some/where"


# ─── stamp_artifact_with_provenance ────────────────────────────────────


def test_stamp_artifact_writes_sibling_manifest(tmp_path: Path) -> None:
    art = tmp_path / "model.cbm"
    art.write_bytes(b"fake binary")
    manifest = stamp_artifact_with_provenance(
        art,
        model_target="m",
        data_paths={},
        parser_rule_files=(),
    )
    assert manifest == art.with_suffix(".cbm.provenance.json")
    assert manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["model_target"] == "m"
    assert payload["artifact_hashes"]["main"]["exists"] is True
    assert payload["artifact_hashes"]["main"]["sha256"] is not None
