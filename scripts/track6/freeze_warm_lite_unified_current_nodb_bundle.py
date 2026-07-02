#!/usr/bin/env python3
"""Freeze a no-DB Warm-lite unified current runtime bundle.

This bundle removes the runtime dependency on
`data/track6/service_v0_1/price_prediction_v0_1.sqlite`.

It does not retrain the LightGBM models. It reuses the already frozen
Warm-lite unified model files and freezes the DB-backed lookup data that the
runtime needs:

- artist registry
- artist aliases
- train-only artwork price observations

The resulting runtime still uses only training-history information for
same-artist statistics. Validation/test rows are not included in the frozen
history table.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SOURCE_BUNDLE = REPO / "models" / "track6" / "warm_lite_unified_route_gap_q50_v0.1_candidate"
TARGET_BUNDLE = REPO / "models" / "track6" / "warm_lite_unified_current_nodb_v0.1_candidate"
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
FROZEN_TRAIN_CSV = REPO / "models" / "track6" / "price_prediction_v0.1" / "data" / "training" / "track6_split" / "track6_train.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sql(query: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)


def ensure_dirs() -> None:
    for sub in ["artifacts", "config", "predict", "manifest", "reports"]:
        (TARGET_BUNDLE / sub).mkdir(parents=True, exist_ok=True)


def copy_model_config() -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    for rel in [
        "config/warm_lite_unified_route_gap_q50_params_v0_1.json",
        "config/warm_lite_unified_route_gap_q50_policy_v0_1.json",
    ]:
        src = SOURCE_BUNDLE / rel
        dst = TARGET_BUNDLE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append({"source": str(src.relative_to(REPO)), "target": str(dst.relative_to(REPO))})

    # Keep model files as physical files in the no-DB bundle, not symlinks.
    src_models = SOURCE_BUNDLE / "models"
    dst_models = TARGET_BUNDLE / "models"
    if dst_models.exists():
        shutil.rmtree(dst_models)
    shutil.copytree(src_models, dst_models, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    copied.append({"source": str(src_models.relative_to(REPO)), "target": str(dst_models.relative_to(REPO))})
    return copied


def freeze_tables() -> dict[str, object]:
    registry = read_sql(
        """
        SELECT artist_key, name_ko, name_en, birth_year, nationality,
               nationality_ko, entity_suffix, is_homonym, valid_price_count,
               primary_medium_category, primary_support_category,
               median_price_krw, median_log_area
        FROM artist_registry
        """
    )
    aliases = read_sql(
        """
        SELECT artist_key, alias_text, alias_normalized, alias_type, source,
               confidence
        FROM artist_aliases
        """
    )
    train_history = read_sql(
        """
        SELECT artist_key, artist_name_ko, price_krw, log_price_krw,
               width_cm, height_cm, depth_cm, area_cm2, log_area,
               aspect_ratio, has_depth, is_3d_candidate,
               medium_category, support_category, medium_support_bucket,
               track6_row_id, source_artwork_id
        FROM artwork_price_observations
        WHERE split_name = 'train'
          AND price_krw IS NOT NULL
          AND price_krw > 0
          AND area_cm2 IS NOT NULL
          AND area_cm2 > 0
        """
    )
    frozen_train_ids = pd.read_csv(
        FROZEN_TRAIN_CSV,
        usecols=["_track6_row_id", "source_artwork_id"],
        low_memory=False,
    )
    frozen_train_ids["_source_artwork_id_str"] = frozen_train_ids["source_artwork_id"].astype(str)
    train_history["_source_artwork_id_str"] = train_history["source_artwork_id"].astype(str)

    if frozen_train_ids["_source_artwork_id_str"].duplicated().any():
        raise RuntimeError("Frozen train source_artwork_id is not unique.")
    if frozen_train_ids["_track6_row_id"].duplicated().any():
        raise RuntimeError("Frozen train _track6_row_id is not unique.")

    before_duplicate_track6_ids = int(train_history["track6_row_id"].duplicated().sum())
    train_history = train_history.drop(columns=["track6_row_id"]).merge(
        frozen_train_ids[["_source_artwork_id_str", "_track6_row_id"]],
        on="_source_artwork_id_str",
        how="left",
        validate="many_to_one",
    )
    missing_remapped_ids = int(train_history["_track6_row_id"].isna().sum())
    if missing_remapped_ids:
        raise RuntimeError(f"Missing frozen _track6_row_id remap rows: {missing_remapped_ids}")
    train_history["track6_row_id"] = train_history["_track6_row_id"].astype(int)
    train_history = train_history.drop(columns=["_source_artwork_id_str", "_track6_row_id"])

    after_duplicate_track6_ids = int(train_history["track6_row_id"].duplicated().sum())
    if after_duplicate_track6_ids:
        raise RuntimeError(f"Remapped train history still has duplicate track6_row_id rows: {after_duplicate_track6_ids}")

    registry.to_csv(TARGET_BUNDLE / "artifacts" / "artist_registry.csv", index=False)
    aliases.to_csv(TARGET_BUNDLE / "artifacts" / "artist_aliases.csv", index=False)
    train_history.to_csv(TARGET_BUNDLE / "artifacts" / "artist_train_history.csv", index=False)

    return {
        "artist_registry_rows": int(len(registry)),
        "artist_alias_rows": int(len(aliases)),
        "train_history_rows": int(len(train_history)),
        "train_history_unique_track6_row_ids": int(train_history["track6_row_id"].nunique()),
        "train_history_duplicate_track6_row_ids_before_remap": before_duplicate_track6_ids,
        "train_history_duplicate_track6_row_ids_after_remap": after_duplicate_track6_ids,
        "track6_row_id_source": str(FROZEN_TRAIN_CSV.relative_to(REPO)),
        "train_history_artists": int(train_history["artist_key"].astype(str).nunique()),
        "train_only": True,
    }


def write_policy(table_status: dict[str, object], copied: list[dict[str, str]]) -> None:
    source_policy = json.loads(
        (SOURCE_BUNDLE / "config" / "warm_lite_unified_route_gap_q50_policy_v0_1.json").read_text(encoding="utf-8")
    )
    policy = {
        "version": "v0.1-candidate",
        "name": "warm_lite_unified_current_nodb",
        "status": "candidate_no_db_runtime",
        "base_model_bundle": str(SOURCE_BUNDLE.relative_to(REPO)),
        "selected_candidate": "current",
        "formula": "seed_mean(qavg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10))",
        "routing_precondition": source_policy.get(
            "routing_precondition",
            "artist_match_score >= 0.80 AND same_artist_training_price_count >= 1",
        ),
        "runtime_dependency": "no sqlite db; uses frozen CSV lookup/history artifacts",
        "frozen_tables": table_status,
        "copied_model_artifacts": copied,
    }
    (TARGET_BUNDLE / "config" / "warm_lite_unified_current_nodb_policy_v0_1.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_docs(table_status: dict[str, object]) -> None:
    readme = f"""# Warm-lite unified current no-DB candidate

이 번들은 official 0.1v Warm-lite unified current 모델을 DB 없이 실행하기 위한 후보 번들이다.

## 포함된 것

- 기존 Warm-lite unified LightGBM 모델 파일
- 기존 params JSON
- `artifacts/artist_registry.csv`
- `artifacts/artist_aliases.csv`
- `artifacts/artist_train_history.csv`

## 포함하지 않는 것

- `fixed_replay_feature_store.csv`
- SQLite DB
- validation/test 가격 이력

## frozen table summary

```json
{json.dumps(table_status, ensure_ascii=False, indent=2)}
```

## 운영 해석

새 작품 예측 시 작가명 또는 artist_key를 입력하면, 이 번들 내부의 alias/registry CSV로
artist_key를 찾고, `artist_train_history.csv`에서 같은 작가 train 이력만 조회한다.
그 결과를 기존 Warm-lite unified current 모델에 넣어 예측한다.
"""
    (TARGET_BUNDLE / "README.md").write_text(readme, encoding="utf-8")
    (TARGET_BUNDLE / "reports" / "warm_lite_unified_current_nodb_release_v0_1.md").write_text(
        readme,
        encoding="utf-8",
    )


def write_manifest() -> None:
    files = sorted(
        [
            path
            for path in TARGET_BUNDLE.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and not path.name.endswith(".pyc")
            and path.name != ".DS_Store"
        ]
    )
    lines = [f"{sha256(path)}  {path.relative_to(TARGET_BUNDLE).as_posix()}" for path in files]
    (TARGET_BUNDLE / "manifest" / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "artifact_id": "warm_lite_unified_current_nodb_v0_1_candidate",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "bundle_path": str(TARGET_BUNDLE.relative_to(REPO)),
        "base_model_bundle": str(SOURCE_BUNDLE.relative_to(REPO)),
        "predictor": "predict/predict_warm_lite_unified_current_nodb_v0_1.py",
        "sha256_manifest": "manifest/MANIFEST.sha256",
        "runtime_db_required": False,
        "fixed_replay_feature_store_included": False,
    }
    (TARGET_BUNDLE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    if not SOURCE_BUNDLE.exists():
        raise FileNotFoundError(SOURCE_BUNDLE)
    ensure_dirs()
    copied = copy_model_config()
    table_status = freeze_tables()
    write_policy(table_status, copied)
    write_docs(table_status)
    write_manifest()
    print(json.dumps({"target_bundle": str(TARGET_BUNDLE.relative_to(REPO)), **table_status}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
