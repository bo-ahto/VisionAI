#!/usr/bin/env python3
"""Freeze a joblib-only Warm-lite unified current runtime bundle.

This is the compact runtime package variant of the no-DB bundle.

Runtime dependency goal:
    - no SQLite DB
    - no CSV lookup/history files
    - no fixed replay feature store
    - one `artifacts/runtime_store.joblib` for lookup tables, params, and models

The store still contains the training-history data needed by the Warm model,
but it is packaged as a single binary artifact instead of CSV files.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SOURCE_BUNDLE = REPO / "models" / "track6" / "warm_lite_unified_current_nodb_v0.1_candidate"
TARGET_BUNDLE = REPO / "models" / "track6" / "warm_lite_unified_current_joblib_v0.1_candidate"
V01_MODEL_ROOT = REPO / "models" / "track6" / "price_prediction_v0.1"
STORE_PATH = TARGET_BUNDLE / "artifacts" / "runtime_store.joblib"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dirs() -> None:
    for sub in ["artifacts", "config", "predict", "manifest", "reports"]:
        (TARGET_BUNDLE / sub).mkdir(parents=True, exist_ok=True)


def load_models(params: dict) -> dict[int, dict[str, object]]:
    out: dict[int, dict[str, object]] = {}
    for seed in params["seeds"]:
        seed_dir = SOURCE_BUNDLE / "models" / f"seed_{seed}"
        out[int(seed)] = {
            "full_q10": joblib.load(seed_dir / "lgbq_full_q10.joblib"),
            "full_q50": joblib.load(seed_dir / "lgbq_full_q50.joblib"),
            "full_q90": joblib.load(seed_dir / "lgbq_full_q90.joblib"),
            "lean_q50": joblib.load(seed_dir / "lgbq_lean_q50.joblib"),
            "lightgbm_residual": joblib.load(seed_dir / "lightgbm_huber_residual.joblib"),
        }
    return out


def write_store() -> dict[str, object]:
    params = json.loads(
        (SOURCE_BUNDLE / "config" / "warm_lite_unified_route_gap_q50_params_v0_1.json").read_text(encoding="utf-8")
    )
    policy = json.loads(
        (SOURCE_BUNDLE / "config" / "warm_lite_unified_current_nodb_policy_v0_1.json").read_text(encoding="utf-8")
    )
    registry = pd.read_csv(SOURCE_BUNDLE / "artifacts" / "artist_registry.csv", low_memory=False)
    aliases = pd.read_csv(SOURCE_BUNDLE / "artifacts" / "artist_aliases.csv", low_memory=False)
    history = pd.read_csv(SOURCE_BUNDLE / "artifacts" / "artist_train_history.csv", low_memory=False)
    feature_generation = json.loads(
        (V01_MODEL_ROOT / "legacy_artifacts" / "track6_artifact_manifest.json").read_text(encoding="utf-8")
    )["feature_generation"]
    models = load_models(params)

    store = {
        "artifact_id": "warm_lite_unified_current_joblib_v0_1_candidate",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_bundle": str(SOURCE_BUNDLE.relative_to(REPO)),
        "params": params,
        "policy": policy,
        "artist_registry": registry,
        "artist_aliases": aliases,
        "artist_train_history": history,
        "feature_generation": feature_generation,
        "models": models,
        "runtime_contract": {
            "db_required": False,
            "csv_required": False,
            "repo_feature_helper_required": False,
            "fixed_replay_feature_store_required": False,
            "uses_train_history_only": True,
        },
    }
    joblib.dump(store, STORE_PATH, compress=3)
    return {
        "store": str(STORE_PATH.relative_to(REPO)),
        "store_bytes": int(STORE_PATH.stat().st_size),
        "artist_registry_rows": int(len(registry)),
        "artist_alias_rows": int(len(aliases)),
        "train_history_rows": int(len(history)),
        "train_history_artists": int(history["artist_key"].astype(str).nunique()),
        "seed_count": int(len(models)),
        "feature_generation_embedded": True,
    }


def write_docs(status: dict[str, object]) -> None:
    policy = {
        "version": "v0.1-candidate",
        "name": "warm_lite_unified_current_joblib",
        "status": "candidate_joblib_only_runtime",
        "formula": "seed_mean(qavg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10))",
        "runtime_dependency": "single joblib store; no SQLite DB; no CSV lookup/history files",
        "runtime_store": status,
    }
    (TARGET_BUNDLE / "config" / "warm_lite_unified_current_joblib_policy_v0_1.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    readme = f"""# Warm-lite unified current joblib-only candidate

이 번들은 Warm-lite unified current 모델을 CSV/DB 없이 실행하기 위한 후보 번들이다.

## Runtime input files

- `artifacts/runtime_store.joblib`
- `predict/predict_warm_lite_unified_current_joblib_v0_1.py`

## Store contents

```json
{json.dumps(status, ensure_ascii=False, indent=2)}
```

## Runtime contract

- SQLite DB를 읽지 않는다.
- CSV lookup/history 파일을 읽지 않는다.
- `fixed_replay_feature_store.csv`를 포함하지도, 읽지도 않는다.
- repo feature helper를 import하지 않는다.
- 같은 작가 train 이력은 `runtime_store.joblib` 안의 DataFrame에서 조회한다.
- size/shape bucket 생성 기준도 `runtime_store.joblib` 안에 동결되어 있다.
"""
    (TARGET_BUNDLE / "README.md").write_text(readme, encoding="utf-8")
    (TARGET_BUNDLE / "reports" / "warm_lite_unified_current_joblib_release_v0_1.md").write_text(
        readme,
        encoding="utf-8",
    )


def write_manifest(status: dict[str, object]) -> None:
    manifest = {
        "artifact_id": "warm_lite_unified_current_joblib_v0_1_candidate",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "bundle_path": str(TARGET_BUNDLE.relative_to(REPO)),
        "base_bundle": str(SOURCE_BUNDLE.relative_to(REPO)),
        "predictor": "predict/predict_warm_lite_unified_current_joblib_v0_1.py",
        "runtime_store": "artifacts/runtime_store.joblib",
        "runtime_db_required": False,
        "runtime_csv_required": False,
        "runtime_repo_feature_helper_required": False,
        "fixed_replay_feature_store_included": False,
        "status": status,
    }
    (TARGET_BUNDLE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    files = sorted(
        path
        for path in TARGET_BUNDLE.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and not path.name.endswith(".pyc")
        and path.name != ".DS_Store"
    )
    lines = [f"{sha256(path)}  {path.relative_to(TARGET_BUNDLE).as_posix()}" for path in files]
    (TARGET_BUNDLE / "manifest" / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    status = write_store()
    write_docs(status)
    write_manifest(status)
    print(json.dumps({"target_bundle": str(TARGET_BUNDLE.relative_to(REPO)), **status}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
