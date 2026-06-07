#!/usr/bin/env python3
"""Extract v0.1 price-prediction features from an operation-style CSV.

이 스크립트의 목적
-----------------
가격 라벨이 없는 운영 입력 CSV를 받아서, 가격 예측 모델 v0.1이 사용할 수 있는
피처 파일로 변환한다.

관리자가 알아야 할 실행 방식
---------------------------
기본값은 2026-06-04 noprice 테스트 파일을 사용한다.

    python3 scripts/track6/extract_price_prediction_v0_1_features.py

다른 파일을 변환하려면 input만 바꾸면 된다.

    python3 scripts/track6/extract_price_prediction_v0_1_features.py \
      --input data/some_new_artworks.csv \
      --output-dir models/track6/price_prediction_v0.1/data/evaluation/some_new_artworks_features

중요한 해석
-----------
- 이 스크립트는 "피처 추출"까지만 담당한다.
- 실제 가격 예측은 v0.1 Warm/Cold 추론 artifact가 준비된 뒤 별도 추론 스크립트가 담당한다.
- Warm/Cold 구분은 v0.1 학습 데이터의 artist_key registry 기준으로 한다.
- Warm v0.1에 필요한 유사 작품 기반 가격 피처는 v0.1 학습 데이터 스냅샷에서 계산한다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------
def find_repo_root(start: Path) -> Path:
    """스크립트 위치와 무관하게 VisionAI repository root를 찾는다.

    이 스크립트는 두 위치에서 실행될 수 있다.
    1. 개발용 원본: scripts/track6/extract_price_prediction_v0_1_features.py
    2. v0.1 재현용 복사본:
       models/track6/price_prediction_v0.1/reproduction/scripts/extract_price_prediction_v0_1_features.py

    단순히 parents[2]처럼 고정 깊이를 쓰면 2번 위치에서 repository root가 아니라
    model version 폴더를 root로 잘못 잡는다. 그래서 상위 폴더를 하나씩 올라가며
    src/visionai와 data 폴더가 함께 있는 위치를 repository root로 판단한다.
    """
    for candidate in [start, *start.parents]:
        if (candidate / "src" / "visionai").exists() and (candidate / "data").exists():
            return candidate
    raise RuntimeError(f"VisionAI repository root를 찾을 수 없습니다: {start}")


REPO = find_repo_root(Path(__file__).resolve())

# src/ 아래의 파서 모듈을 import하기 위해 repo root를 sys.path에 추가한다.
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.visionai.price_engine.preprocessing.dimension_parser import parse_dimension  # noqa: E402
from src.visionai.price_engine.preprocessing.primary_medium_parser import parse_artsy_medium  # noqa: E402


MODEL_ROOT_DEFAULT = REPO / "models" / "track6" / "price_prediction_v0.1"
INPUT_DEFAULT = REPO / "data" / "test_new_artworks_test_noprice_0604.csv"
OUTPUT_DIR_DEFAULT = (
    MODEL_ROOT_DEFAULT
    / "data"
    / "evaluation"
    / "test_new_artworks_test_noprice_0604_features"
)


# ---------------------------------------------------------------------------
# v0.1 모델에서 쓰는 주요 피처 정의
# ---------------------------------------------------------------------------
# Warm Huber 계열의 기본 피처. v0.1 Warm 후보는 여기에 유사 작품 기반 가격
# 피처(SVC_NUMERIC)를 추가해서 사용한다.
WARM_BASE_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
    "artist_key",
]

# Cold baseline 및 Cold reference 계열이 공통적으로 필요로 하는 작품 조건 피처.
# Cold v0.1 reference는 LightGBM Quantile + 외부/검색 피처까지 포함하지만,
# 이 스크립트는 입력 CSV에서 바로 만들 수 있는 작품 기본 피처를 우선 생성한다.
COLD_BASE_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
]

# v0.1 이전 실험들에서 공통적으로 생성해 쓰던 bucket 피처.
# 모델이나 보정 정책에 따라 일부만 사용될 수 있으므로 전체를 같이 출력한다.
GENERATED_BUCKET_FEATURES = [
    "size_bucket",
    "shape_bucket",
    "medium_size_bucket",
    "support_size_bucket",
    "medium_shape_bucket",
    "is_large_2d",
    "is_large_3d",
]

# PP-SVC1/2/3 Warm 비교군 통계 피처.
# SVC는 여기서 "유사 작품 기반 가격 피처"로 이해하면 된다.
SVC_NUMERIC = [
    "svc_group_log_price_median",
    "svc_group_log_price_q25",
    "svc_group_log_price_q75",
    "svc_group_log_price_iqr",
    "svc_group_log_unit_area_median",
    "svc_group_log_unit_area_iqr",
    "svc_group_n_log",
]

SVC_CATEGORICAL = [
    "svc_group_level",
    "svc_coverage_tier",
    "svc_has_artist_level",
]

SVC_OUTPUT_COLUMNS = [
    *SVC_NUMERIC,
    *SVC_CATEGORICAL,
    "svc_group_n",
]


# PP-SVC1과 동일한 비교군 fallback 순서.
# 위에서부터 조건이 더 구체적이고, 아래로 갈수록 더 넓은 비교군이다.
# 예: 작가+재료/지지체+크기 조건에 충분한 표본이 있으면 그 통계를 쓰고,
# 표본이 부족하면 작가+크기, 작가 전체, 재료/크기 순으로 내려간다.
GROUP_DEFS = [
    {
        "level": "artist_medium_support_size",
        "keys": ["artist_key", "medium_support_bucket", "size_bucket"],
        "min_n": 5,
        "service_label": "작가+재료/지지체+크기",
    },
    {
        "level": "artist_size",
        "keys": ["artist_key", "size_bucket"],
        "min_n": 5,
        "service_label": "작가+크기",
    },
    {
        "level": "artist",
        "keys": ["artist_key"],
        "min_n": 5,
        "service_label": "작가 전체",
    },
    {
        "level": "medium_support_size",
        "keys": ["medium_support_bucket", "size_bucket"],
        "min_n": 30,
        "service_label": "재료/지지체+크기",
    },
    {
        "level": "medium_category_support_size",
        "keys": ["medium_category", "support_category", "size_bucket"],
        "min_n": 30,
        "service_label": "재료+지지체+크기",
    },
    {
        "level": "medium_size",
        "keys": ["medium_category", "size_bucket"],
        "min_n": 50,
        "service_label": "재료+크기",
    },
]


ID_COLUMNS = [
    "_v01_row_id",
    "_track6_row_id",
    "slug",
    "title",
    "artist_name",
    "artist_slug",
    "matched_train_artist",
    "artist_key",
    "artist_match_source",
    "artist_match_status",
    "warm_cold_route",
    "artwork_url",
]


def clean_text(value: Any) -> str:
    """문자형 값을 안전하게 정리한다."""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def slug_to_artist_key(value: Any) -> str:
    """artist_slug를 artist_key 후보로 바꾼다.

    예:
    - "seongeun-moon" -> "seongeun moon"
    - "parkha" -> "parkha"
    """
    text = clean_text(value).lower()
    return text.replace("-", " ")


def name_to_artist_key(value: Any) -> str:
    """artist_name을 artist_key 후보로 바꾼다.

    이 fallback은 완벽한 동명이인 처리를 보장하지 않는다. 그래서 결과에는
    artist_match_source를 같이 남겨서 어떤 방식으로 매칭됐는지 확인할 수 있게 한다.
    """
    return clean_text(value).lower()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_model_policy(model_root: Path) -> dict[str, Any]:
    policy_path = model_root / "config" / "model_policy_v0.1.json"
    if not policy_path.exists():
        raise FileNotFoundError(f"v0.1 policy file not found: {policy_path}")
    return load_json(policy_path)


def load_artifact_feature_generation(model_root: Path) -> dict[str, Any]:
    """v0.1 legacy manifest에서 bucket 생성 기준을 읽는다.

    size_bucket은 학습 데이터의 log_area 분위 경계에 의존한다. 신규 데이터마다
    분위 경계를 다시 계산하면 학습 때와 다른 bucket이 생기므로, 반드시 v0.1에
    저장된 학습 기준 경계를 사용한다.
    """
    manifest_path = model_root / "legacy_artifacts" / "track6_artifact_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"v0.1 legacy artifact manifest not found: {manifest_path}")
    return load_json(manifest_path)["feature_generation"]


def load_training_snapshot(model_root: Path) -> pd.DataFrame:
    """v0.1 학습 데이터 스냅샷을 읽는다.

    유사 작품 기반 가격 피처는 반드시 학습 데이터만으로 계산해야 한다.
    신규 테스트 데이터를 섞어서 비교군 통계를 만들면 평가가 오염된다.
    """
    train_path = model_root / "data" / "training" / "track6_split" / "track6_train.csv"
    if not train_path.exists():
        raise FileNotFoundError(f"v0.1 training snapshot not found: {train_path}")
    return pd.read_csv(train_path, low_memory=False)


def build_artist_registry(train: pd.DataFrame) -> pd.DataFrame:
    """학습 artist_key registry를 만든다.

    Warm/Cold 구분 기준:
    - artist_key가 학습 registry에 있으면 Warm
    - 없으면 Cold

    artist_works_count_train과 artist_works_log도 Warm 피처에 필요하므로 같이 보존한다.
    """
    cols = ["artist_key", "artist_works_count_train", "artist_works_log"]
    registry = train[cols].dropna(subset=["artist_key"]).copy()
    registry["artist_key"] = registry["artist_key"].astype(str)
    registry["artist_works_count_train"] = pd.to_numeric(registry["artist_works_count_train"], errors="coerce")
    registry["artist_works_log"] = pd.to_numeric(registry["artist_works_log"], errors="coerce")
    return (
        registry
        .sort_values(["artist_key", "artist_works_count_train"], ascending=[True, False])
        .drop_duplicates("artist_key", keep="first")
        .reset_index(drop=True)
    )


def choose_artist_key(row: pd.Series, artist_keys: set[str]) -> tuple[str, str, str]:
    """입력 행에서 Warm/Cold 라우팅용 artist_key를 결정한다.

    우선순위:
    1. matched_train_artist
       - 외부에서 이미 학습 작가와 매칭한 값
       - 가장 신뢰할 수 있는 입력
    2. artist_slug
       - slug의 하이픈을 공백으로 바꿔 artist_key 후보로 사용
    3. artist_name
       - 소문자 정규화 fallback

    반환:
    - artist_key: 모델 피처에 들어갈 key
    - source: 어떤 컬럼으로 매칭했는지
    - status: matched / unmatched
    """
    candidates = [
        ("matched_train_artist", clean_text(row.get("matched_train_artist")).lower()),
        ("artist_slug", slug_to_artist_key(row.get("artist_slug"))),
        ("artist_name", name_to_artist_key(row.get("artist_name"))),
    ]
    for source, candidate in candidates:
        if candidate and candidate in artist_keys:
            return candidate, source, "matched"
    fallback = candidates[0][1] or candidates[1][1] or candidates[2][1] or "__MISSING__"
    return fallback, "fallback_unmatched", "unmatched"


def category_is_3d(category: Any) -> bool:
    """카테고리만 보고 3D 후보인지 판단하는 보조 함수."""
    text = clean_text(category).lower()
    return text in {"sculpture", "installation", "design/decorative art", "textile arts"}


def parse_one_row(row: pd.Series) -> dict[str, Any]:
    """입력 행 하나를 모델 기본 피처로 변환한다."""
    dim_raw = clean_text(row.get("dimensions_cm"))
    medium_raw = clean_text(row.get("medium"))
    category_raw = clean_text(row.get("category"))

    # 크기 문자열 파싱
    # width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio가 여기서 나온다.
    dim = parse_dimension(dim_raw)
    width = dim.width_cm
    height = dim.height_cm
    depth = dim.depth_cm
    area = dim.surface_area

    # 면적은 log_area 계산의 기준이다. 면적이 없거나 0 이하이면 log_area는 결측으로 둔다.
    log_area = float(np.log(area)) if area is not None and area > 0 else np.nan

    # 재료/지지체 파싱
    # Artsy형 medium 문자열을 기준으로 "oil", "acrylic", "canvas", "paper" 같은
    # 모델 호환 카테고리로 변환한다.
    medium_result = parse_artsy_medium(medium_raw, category_raw)
    medium_category = medium_result.medium_category or "other"
    support_category = medium_result.support_type or "other"
    medium_support_bucket = f"{medium_category}__{support_category}"

    # 기존 track6 기준에서는 aspect_ratio > 10을 극단 비율 flag로 관리했다.
    aspect = dim.aspect_ratio
    is_extreme = bool(aspect is not None and aspect > 10)

    # depth가 있다고 해서 모두 조각은 아니지만, 기존 크기 파서는 3개 치수를 3D로 표시한다.
    # category가 명확히 3D인 경우도 3D 후보로 둔다.
    is_3d_candidate = bool(dim.is_3d or category_is_3d(category_raw))
    has_depth = bool(depth is not None and depth > 0)

    return {
        "width_cm": width,
        "height_cm": height,
        "depth_cm": depth if depth is not None else 0.0,
        "area_cm2": area,
        "log_area": log_area,
        "aspect_ratio": aspect,
        "has_depth": has_depth,
        "is_3d_candidate": is_3d_candidate,
        "medium_category": medium_category,
        "support_category": support_category,
        "medium_support_bucket": medium_support_bucket,
        "is_extreme_aspect_ratio": is_extreme,
        "is_training_candidate": not bool(medium_result.is_excluded_for_training),
        "collected_material_raw": medium_raw,
        "nant_support": "",
        "nant_tool": "",
        "nant_material_note": "",
        "nant_material_match_method": "v0_1_artsy_medium_parser",
        "nant_material_idx": "",
        "dimension_parse_status": "parsed" if not dim.is_size_imputed else dim.pattern_used,
        "dimension_pattern_used": dim.pattern_used,
        "medium_parse_raw": medium_result.raw,
        "medium_l1": medium_result.medium_l1,
        "medium_leaf": medium_result.medium_leaf,
        "support_l1": medium_result.support_l1,
        "support_leaf": medium_result.support_leaf,
        "medium_excluded_for_training": bool(medium_result.is_excluded_for_training),
        "medium_exclude_reason": medium_result.exclude_reason or "",
    }


def add_bucket_features(frame: pd.DataFrame, feature_generation: dict[str, Any], scope: str) -> pd.DataFrame:
    """v0.1 학습 기준으로 size/shape bucket을 만든다."""
    out = frame.copy()
    cfg = feature_generation[scope]
    edges = np.asarray(cfg["log_area_quantiles"], dtype=float)
    edges[0] = -np.inf
    edges[-1] = np.inf
    labels = [f"q{i + 1}" for i in range(len(edges) - 1)]

    log_area = pd.to_numeric(out["log_area"], errors="coerce")
    aspect = pd.to_numeric(out["aspect_ratio"], errors="coerce")
    area = pd.to_numeric(out["area_cm2"], errors="coerce")
    is_3d = out["is_3d_candidate"].astype(str).str.lower().isin(["true", "1", "yes"])

    out["size_bucket"] = pd.cut(log_area, bins=edges, labels=labels, include_lowest=True).astype(str)
    out.loc[log_area.isna(), "size_bucket"] = "__MISSING__"
    out["shape_bucket"] = np.select(
        [aspect.isna(), aspect < 0.65, aspect <= 1.55, aspect <= 2.5, aspect > 2.5],
        ["__MISSING__", "tall", "balanced", "wide", "extreme_wide"],
        default="__MISSING__",
    )
    out["medium_size_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
    out["support_size_bucket"] = out["support_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
    out["medium_shape_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["shape_bucket"].astype(str)
    out["is_large_2d"] = ((area >= float(cfg["large_area_cutoff_q80"])) & ~is_3d).astype(str)
    out["is_large_3d"] = ((area >= float(cfg["large_area_cutoff_q80"])) & is_3d).astype(str)
    out[f"{scope}_size_bucket_source"] = cfg["size_bucket_source"]
    return out


def comparable_ready(frame: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """비교군 통계 계산용으로 타입을 정리한다."""
    out = frame.copy()
    out[id_col] = out[id_col]
    for col in ["price_krw", "ln_price_krw", "area_cm2"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    area = np.clip(pd.to_numeric(out["area_cm2"], errors="coerce").to_numpy(dtype=float), 1.0, None)
    # 학습 source에는 ln_price_krw가 있으므로 면적당 로그 가격을 계산한다.
    # 운영 target에는 가격 라벨이 없기 때문에 이 값을 만들 수 없고, 만들 필요도 없다.
    # target은 group key merge에만 쓰이며 통계값은 모두 source에서 온다.
    if "ln_price_krw" in out.columns:
        out["svc_source_log_unit_area"] = pd.to_numeric(out["ln_price_krw"], errors="coerce").to_numpy(dtype=float) - np.log(area)
    for col in ["artist_key", "medium_category", "support_category", "medium_support_bucket", "size_bucket"]:
        out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def aggregate_stats(source: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    """source 학습 데이터에서 비교군별 가격 통계를 계산한다."""
    if key_cols:
        grouped = source.groupby(key_cols, dropna=False, observed=False)
        stats = grouped.agg(
            svc_group_log_price_median=("ln_price_krw", "median"),
            svc_group_log_price_q25=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.25))),
            svc_group_log_price_q75=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.75))),
            svc_group_log_unit_area_median=("svc_source_log_unit_area", "median"),
            svc_group_log_unit_area_q25=("svc_source_log_unit_area", lambda x: float(np.quantile(x.astype(float), 0.25))),
            svc_group_log_unit_area_q75=("svc_source_log_unit_area", lambda x: float(np.quantile(x.astype(float), 0.75))),
            svc_group_n=("ln_price_krw", "size"),
        ).reset_index()
    else:
        stats = pd.DataFrame([{
            "svc_group_log_price_median": float(source["ln_price_krw"].median()),
            "svc_group_log_price_q25": float(source["ln_price_krw"].quantile(0.25)),
            "svc_group_log_price_q75": float(source["ln_price_krw"].quantile(0.75)),
            "svc_group_log_unit_area_median": float(source["svc_source_log_unit_area"].median()),
            "svc_group_log_unit_area_q25": float(source["svc_source_log_unit_area"].quantile(0.25)),
            "svc_group_log_unit_area_q75": float(source["svc_source_log_unit_area"].quantile(0.75)),
            "svc_group_n": int(len(source)),
        }])
    stats["svc_group_log_price_iqr"] = stats["svc_group_log_price_q75"] - stats["svc_group_log_price_q25"]
    stats["svc_group_log_unit_area_iqr"] = stats["svc_group_log_unit_area_q75"] - stats["svc_group_log_unit_area_q25"]
    return stats


def coverage_tier(level: str, n: float) -> str:
    """비교군 표본 수를 사람이 보기 쉬운 coverage 등급으로 변환한다."""
    if level == "global":
        return "fallback_global"
    if n >= 50:
        return "high_n"
    if n >= 15:
        return "medium_n"
    return "low_n"


def apply_comparable_stats(train: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    """신규 target 행에 유사 작품 기반 가격 피처를 붙인다.

    이 함수는 target 가격을 사용하지 않는다. 오직 v0.1 학습 데이터 가격만으로
    비교군 통계를 만들기 때문에 운영 입력에도 안전하게 쓸 수 있다.
    """
    id_col = "_v01_row_id"
    source_ready = comparable_ready(train, "_track6_row_id")
    target_ready = comparable_ready(target, id_col)

    result = target_ready[[id_col]].copy()
    for col in SVC_NUMERIC:
        result[col] = np.nan
    for col in SVC_CATEGORICAL:
        result[col] = "__UNASSIGNED__"
    result["svc_group_n"] = np.nan

    assigned = np.zeros(len(result), dtype=bool)
    stat_cols = [
        "svc_group_log_price_median",
        "svc_group_log_price_q25",
        "svc_group_log_price_q75",
        "svc_group_log_price_iqr",
        "svc_group_log_unit_area_median",
        "svc_group_log_unit_area_iqr",
        "svc_group_n",
    ]
    for group_def in GROUP_DEFS:
        keys = group_def["keys"]
        stats = aggregate_stats(source_ready, keys)
        merged = target_ready[keys].merge(stats, on=keys, how="left")
        eligible = (
            (~assigned)
            & (pd.to_numeric(merged["svc_group_n"], errors="coerce").fillna(0) >= group_def["min_n"]).to_numpy()
        )
        if not eligible.any():
            continue
        for col in stat_cols:
            result.loc[eligible, col] = merged.loc[eligible, col].to_numpy()
        result.loc[eligible, "svc_group_level"] = group_def["level"]
        result.loc[eligible, "svc_has_artist_level"] = str("artist_key" in keys)
        assigned |= eligible

    # 어떤 비교군에도 충분한 표본이 없으면 전체 학습 데이터 중앙값으로 fallback한다.
    # 이 경우도 모델 입력은 가능하지만, 신뢰도는 낮게 봐야 한다.
    if (~assigned).any():
        global_stats = aggregate_stats(source_ready, [])
        for col in stat_cols:
            result.loc[~assigned, col] = global_stats.iloc[0][col]
        result.loc[~assigned, "svc_group_level"] = "global"
        result.loc[~assigned, "svc_has_artist_level"] = "False"

    result["svc_group_n_log"] = np.log1p(pd.to_numeric(result["svc_group_n"], errors="coerce").fillna(0))
    result["svc_coverage_tier"] = [
        coverage_tier(str(level), float(n))
        for level, n in zip(result["svc_group_level"], pd.to_numeric(result["svc_group_n"], errors="coerce").fillna(0), strict=False)
    ]
    result["svc_has_artist_level"] = result["svc_has_artist_level"].astype(str)
    return result[[id_col, *SVC_OUTPUT_COLUMNS]]


def extract_features(input_path: Path, model_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """입력 CSV 전체를 v0.1 피처 DataFrame으로 변환한다."""
    raw = pd.read_csv(input_path, low_memory=False)
    train = load_training_snapshot(model_root)
    policy = load_model_policy(model_root)
    feature_generation = load_artifact_feature_generation(model_root)
    registry = build_artist_registry(train)
    artist_keys = set(registry["artist_key"].astype(str))

    # 입력 원본에는 track6 학습 row id가 없으므로 신규 데이터 전용 row id를 만든다.
    # 기존 실험 코드와 호환하기 위해 _track6_row_id alias도 같이 제공하지만,
    # 이 값은 v0.1 신규 입력 내부에서만 쓰는 local id다.
    raw = raw.copy()
    raw.insert(0, "_v01_row_id", np.arange(len(raw), dtype=int))
    raw["_track6_row_id"] = raw["_v01_row_id"]

    parsed_rows = []
    for _idx, row in raw.iterrows():
        parsed_rows.append(parse_one_row(row))
    features = pd.concat([raw.reset_index(drop=True), pd.DataFrame(parsed_rows)], axis=1)

    # artist_key와 Warm/Cold route 생성
    matches = features.apply(lambda row: choose_artist_key(row, artist_keys), axis=1)
    features["artist_key"] = [item[0] for item in matches]
    features["artist_match_source"] = [item[1] for item in matches]
    features["artist_match_status"] = [item[2] for item in matches]
    features["warm_cold_route"] = np.where(features["artist_match_status"].eq("matched"), "warm", "cold")

    # 학습 registry에서 작가별 학습 작품 수 피처를 붙인다.
    features = features.merge(registry, on="artist_key", how="left")
    features["artist_works_count_train"] = pd.to_numeric(features["artist_works_count_train"], errors="coerce").fillna(0).astype(int)
    features["artist_works_log"] = pd.to_numeric(features["artist_works_log"], errors="coerce").fillna(np.log1p(features["artist_works_count_train"]))

    # Warm 기준 bucket과 Cold 기준 bucket의 경계가 약간 다르므로 둘 다 계산한다.
    # all_features에는 Warm 기준 bucket을 기본 bucket 컬럼으로 두고,
    # cold 전용 파일에는 cold 기준 bucket을 다시 입힌다.
    warm_features = add_bucket_features(features, feature_generation, "warm")
    cold_bucket_features = add_bucket_features(features, feature_generation, "cold")
    for col in GENERATED_BUCKET_FEATURES:
        warm_features[f"cold_{col}"] = cold_bucket_features[col]

    # 유사 작품 기반 가격 피처 계산에는 Warm bucket 기준을 사용한다.
    train_for_svc = add_bucket_features(train, feature_generation, "warm")
    svc = apply_comparable_stats(train_for_svc, warm_features)
    all_features = warm_features.merge(svc, on="_v01_row_id", how="left")

    metadata = {
        "model_policy": policy,
        "input_path": str(input_path),
        "model_root": str(model_root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rows": int(len(all_features)),
        "warm_rows": int(all_features["warm_cold_route"].eq("warm").sum()),
        "cold_rows": int(all_features["warm_cold_route"].eq("cold").sum()),
    }
    return all_features, metadata


def stable_columns(columns: list[str], frame: pd.DataFrame) -> list[str]:
    """존재하는 컬럼만 순서대로 반환한다."""
    return [col for col in columns if col in frame.columns]


def write_quality_report(frame: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """변환 품질을 빠르게 확인할 수 있는 summary CSV를 만든다."""
    rows = [
        {"metric": "total_rows", "value": int(len(frame))},
        {"metric": "warm_rows", "value": int(frame["warm_cold_route"].eq("warm").sum())},
        {"metric": "cold_rows", "value": int(frame["warm_cold_route"].eq("cold").sum())},
        {"metric": "artist_matched_rows", "value": int(frame["artist_match_status"].eq("matched").sum())},
        {"metric": "dimension_parsed_rows", "value": int(frame["dimension_parse_status"].eq("parsed").sum())},
        {"metric": "dimension_problem_rows", "value": int(frame["dimension_parse_status"].ne("parsed").sum())},
        {"metric": "medium_other_rows", "value": int(frame["medium_category"].astype(str).eq("other").sum())},
        {"metric": "support_other_rows", "value": int(frame["support_category"].astype(str).eq("other").sum())},
        {"metric": "svc_artist_level_rows", "value": int(frame["svc_has_artist_level"].astype(str).eq("True").sum())},
        {"metric": "svc_global_fallback_rows", "value": int(frame["svc_group_level"].astype(str).eq("global").sum())},
        {"metric": "median_svc_group_n", "value": float(pd.to_numeric(frame["svc_group_n"], errors="coerce").median())},
    ]
    report = pd.DataFrame(rows)
    report.to_csv(output_dir / "feature_quality_report.csv", index=False)

    # 사람이 문제 행을 볼 수 있도록 별도 샘플 파일도 남긴다.
    issue_mask = (
        frame["artist_match_status"].ne("matched")
        | frame["dimension_parse_status"].ne("parsed")
        | frame["medium_category"].astype(str).eq("other")
        | frame["support_category"].astype(str).eq("other")
        | frame["svc_group_level"].astype(str).eq("global")
    )
    issue_cols = stable_columns([
        "_v01_row_id",
        "slug",
        "title",
        "artist_name",
        "matched_train_artist",
        "artist_key",
        "artist_match_status",
        "warm_cold_route",
        "dimensions_cm",
        "dimension_parse_status",
        "medium",
        "medium_category",
        "support_category",
        "svc_group_level",
        "svc_group_n",
    ], frame)
    frame.loc[issue_mask, issue_cols].head(300).to_csv(output_dir / "feature_issue_sample.csv", index=False)
    return report


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    """tabulate 의존성 없이 Markdown table을 만든다."""
    if frame.empty:
        return "_No rows._"
    columns = [str(col) for col in frame.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        values = []
        for value in row:
            if pd.isna(value):
                values.append("")
            else:
                values.append(str(value).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_readme(output_dir: Path, metadata: dict[str, Any], quality: pd.DataFrame) -> None:
    """출력 폴더 사용법 README를 생성한다."""
    readme = f"""# v0.1 가격 예측 피처 추출 결과

- 생성일: {metadata['generated_at']}
- 입력 파일: `{metadata['input_path']}`
- 모델 기준 폴더: `{metadata['model_root']}`
- 출력 폴더: `{output_dir}`
- 전체 행: {metadata['rows']:,}
- Warm 행: {metadata['warm_rows']:,}
- Cold 행: {metadata['cold_rows']:,}

## 기본 실행 명령

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py
```

## 다른 입력 파일 실행 예시

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py \\
  --input data/new_artworks.csv \\
  --output-dir models/track6/price_prediction_v0.1/data/evaluation/new_artworks_features
```

## 생성 파일

| 파일 | 설명 |
|---|---|
| `features_all_v0_1.csv` | 전체 입력 행 + v0.1 기본 피처 + Warm 비교군 피처 |
| `warm_features_v0_1.csv` | Warm route 행만 따로 저장한 파일 |
| `cold_features_v0_1.csv` | Cold route 행만 따로 저장한 파일 |
| `routing_v0_1.csv` | Warm/Cold 구분과 artist_key 매칭 상태 |
| `feature_quality_report.csv` | 변환 품질 요약 |
| `feature_issue_sample.csv` | 확인이 필요한 행 샘플 |
| `feature_schema_v0_1.json` | 컬럼 구성과 v0.1 정책 설명 |

## 품질 요약

{dataframe_to_markdown(quality)}

## 사용 순서

1. `feature_quality_report.csv`에서 `dimension_problem_rows`, `medium_other_rows`, `svc_global_fallback_rows` 확인
2. 문제가 있는 경우 `feature_issue_sample.csv`에서 원본 row 확인
3. Warm 예측 테스트에는 `warm_features_v0_1.csv` 사용
4. Cold 예측 테스트에는 `cold_features_v0_1.csv` 사용

## 주의

- 이 스크립트는 피처 추출만 수행하고 가격 예측값은 만들지 않음
- Warm v0.1의 정확한 가격 예측은 `PP-SVC3` component chain artifact가 준비된 뒤 수행
- Cold v0.1 reference는 외부/검색 피처와 qwidth 보정 artifact가 필요하므로, 이 출력은 Cold 기본 작품 피처 추출 결과로 해석
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def write_outputs(frame: pd.DataFrame, metadata: dict[str, Any], output_dir: Path) -> None:
    """피처 추출 결과를 CSV/JSON으로 저장한다."""
    output_dir.mkdir(parents=True, exist_ok=True)

    base_cols = stable_columns(
        [
            *ID_COLUMNS,
            "date",
            "artist_nationality",
            "partner_name",
            "partner_slug",
            "category",
            "medium",
            "dimensions_cm",
            "dimensions_in",
            "attribution",
            "is_for_sale",
            "is_sold",
            "price_currency",
            "image_large",
        ],
        frame,
    )
    diagnostic_cols = stable_columns(
        [
            "dimension_parse_status",
            "dimension_pattern_used",
            "medium_l1",
            "medium_leaf",
            "support_l1",
            "support_leaf",
            "medium_excluded_for_training",
            "medium_exclude_reason",
            "warm_size_bucket_source",
        ],
        frame,
    )
    feature_cols = stable_columns(
        [
            *WARM_BASE_FEATURES,
            "artist_works_count_train",
            "artist_works_log",
            *GENERATED_BUCKET_FEATURES,
            "cold_size_bucket",
            "cold_shape_bucket",
            "cold_medium_size_bucket",
            "cold_support_size_bucket",
            "cold_medium_shape_bucket",
            "cold_is_large_2d",
            "cold_is_large_3d",
            *SVC_OUTPUT_COLUMNS,
            "is_training_candidate",
            "collected_material_raw",
            "nant_support",
            "nant_tool",
            "nant_material_note",
            "nant_material_match_method",
            "nant_material_idx",
        ],
        frame,
    )
    all_cols = list(dict.fromkeys([*base_cols, *feature_cols, *diagnostic_cols]))

    frame[all_cols].to_csv(output_dir / "features_all_v0_1.csv", index=False)

    warm_feature_cols = stable_columns(
        [*ID_COLUMNS, *WARM_BASE_FEATURES, "artist_works_count_train", "artist_works_log", *SVC_OUTPUT_COLUMNS, *GENERATED_BUCKET_FEATURES],
        frame,
    )
    cold_feature_cols = stable_columns(
        [*ID_COLUMNS, *COLD_BASE_FEATURES, *GENERATED_BUCKET_FEATURES],
        frame,
    )
    frame.loc[frame["warm_cold_route"].eq("warm"), warm_feature_cols].to_csv(output_dir / "warm_features_v0_1.csv", index=False)
    frame.loc[frame["warm_cold_route"].eq("cold"), cold_feature_cols].to_csv(output_dir / "cold_features_v0_1.csv", index=False)

    routing_cols = stable_columns(
        [
            "_v01_row_id",
            "slug",
            "title",
            "artist_name",
            "artist_slug",
            "matched_train_artist",
            "artist_key",
            "artist_match_source",
            "artist_match_status",
            "warm_cold_route",
            "artist_works_count_train",
        ],
        frame,
    )
    frame[routing_cols].to_csv(output_dir / "routing_v0_1.csv", index=False)

    quality = write_quality_report(frame, output_dir)
    write_readme(output_dir, metadata, quality)

    schema = {
        "created_at": metadata["generated_at"],
        "input_path": metadata["input_path"],
        "model_root": metadata["model_root"],
        "output_dir": str(output_dir),
        "rows": metadata["rows"],
        "warm_rows": metadata["warm_rows"],
        "cold_rows": metadata["cold_rows"],
        "warm_base_features": WARM_BASE_FEATURES,
        "cold_base_features": COLD_BASE_FEATURES,
        "generated_bucket_features": GENERATED_BUCKET_FEATURES,
        "svc_numeric_features": SVC_NUMERIC,
        "svc_categorical_features": SVC_CATEGORICAL,
        "group_definitions": GROUP_DEFS,
        "notes": [
            "Warm/Cold route is based on the v0.1 training artist registry.",
            "SVC features are computed from the v0.1 training snapshot only.",
            "Cold v0.1 reference still requires external/search/qwidth inference artifacts for exact final prediction.",
        ],
    }
    (output_dir / "feature_schema_v0_1.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract price prediction v0.1 features from an operation-style CSV.")
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_DEFAULT,
        help=f"입력 CSV 경로. 기본값: {INPUT_DEFAULT.relative_to(REPO)}",
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=MODEL_ROOT_DEFAULT,
        help=f"v0.1 모델 기준 폴더. 기본값: {MODEL_ROOT_DEFAULT.relative_to(REPO)}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR_DEFAULT,
        help=f"출력 폴더. 기본값: {OUTPUT_DIR_DEFAULT.relative_to(REPO)}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input if args.input.is_absolute() else REPO / args.input
    model_root = args.model_root if args.model_root.is_absolute() else REPO / args.model_root
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO / args.output_dir

    if not input_path.exists():
        raise FileNotFoundError(f"input CSV not found: {input_path}")
    if not model_root.exists():
        raise FileNotFoundError(f"model root not found: {model_root}")

    features, metadata = extract_features(input_path, model_root)
    write_outputs(features, metadata, output_dir)

    print(json.dumps({
        "status": "completed",
        "input": str(input_path.relative_to(REPO)),
        "output_dir": str(output_dir.relative_to(REPO)),
        "rows": metadata["rows"],
        "warm_rows": metadata["warm_rows"],
        "cold_rows": metadata["cold_rows"],
        "main_outputs": [
            "features_all_v0_1.csv",
            "warm_features_v0_1.csv",
            "cold_features_v0_1.csv",
            "routing_v0_1.csv",
            "feature_quality_report.csv",
            "README.md",
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
