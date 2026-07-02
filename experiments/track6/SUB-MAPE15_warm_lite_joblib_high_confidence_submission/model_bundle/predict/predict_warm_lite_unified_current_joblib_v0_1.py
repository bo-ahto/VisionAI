#!/usr/bin/env python3
"""Joblib-only Warm-lite unified current predictor.

이 파일은 official 0.1v Warm 예측 후보를 CSV/DB 없이 실행하기 위한
독립 실행 predictor다.

런타임에서 읽는 모델 데이터 파일은 하나다.

- artifacts/runtime_store.joblib

`runtime_store.joblib` 안에는 다음이 함께 들어 있다.

- 작가 registry: 내부 artist_key, 한글명/영문명, 동명이인 표시 등
- 작가 alias: 검수된 이름 표기 변형과 alias confidence
- 작가 학습 이력: 같은 작가 과거 가격 통계 생성을 위한 train history
- LightGBM Quantile 모델과 LightGBM Huber residual 모델
- size_bucket / shape_bucket 생성을 위한 feature_generation 설정
- 학습/예측에 필요한 params, fallback 통계, seed 목록

예측 시점에는 아래 파일을 읽지 않는다.

- SQLite DB
- artist_registry.csv / artist_aliases.csv / artist_train_history.csv
- 개별 seed 모델 joblib 파일
- fixed_replay_feature_store.csv

최종 로그가격 산식은 다음 구조다.

    seed_mean(qavg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10))

여기서 qavg는 full 피처 q50과 lean 피처 q50의 평균이고,
LightGBMHuberResidual은 qavg 기준가격에서 남은 오차를 보정하는 모델이다.
"""

from __future__ import annotations

import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", message="X does not have valid feature names")

# BUNDLE은 이 predictor가 들어 있는 모델 번들 루트다.
# 예: models/track6/warm_lite_unified_current_joblib_v0.1_candidate
BUNDLE = Path(__file__).resolve().parents[1]
STORE_PATH = BUNDLE / "artifacts" / "runtime_store.joblib"

# 같은 작가 과거 이력에서 만들어 모델에 직접 넣는 group 통계 피처들이다.
# grp_log_price_*는 같은 작가의 과거 로그가격 분포를 요약하고,
# grp_unit_area_*는 면적을 감안한 가격대를 요약한다.
# grp_n_log는 참고한 과거 작품 수를 log1p로 변환한 값이며,
# grp_match_level은 어떤 비교군 단계에서 통계를 찾았는지 나타낸다.
GRP_COLS = [
    "grp_log_price_median",
    "grp_log_price_q25",
    "grp_log_price_q75",
    "grp_log_price_iqr",
    "grp_unit_area_median",
    "grp_unit_area_iqr",
    "grp_n_log",
    "grp_match_level",
]

# 같은 작가 이력 통계를 만들 때 좁은 비교군부터 넓은 비교군 순서로 찾는다.
# 1단계: 같은 작가 + 같은 매체/지지체 + 같은 크기 구간
# 2단계: 같은 작가 + 같은 크기 구간
# 3단계: 같은 작가 전체
# 각 단계에서 1건 이상 있으면 그 단계의 통계를 사용한다.
ARTIST_LADDER = [["medium_support_bucket", "size_bucket"], ["size_bucket"], []]

# 외부 사용자가 반드시 넣어야 하는 원본 입력 컬럼이다.
# area, log_area, bucket 등은 코드가 내부에서 계산한다.
REQUIRED_INPUT = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "medium_category",
    "support_category",
]

# LightGBM 모델에 들어가기 전 기본 작품 피처 세트다.
# 여기에 assign_stats()가 붙이는 같은 작가 group 통계가 더해져
# 최종 모델 입력 feature_frame이 된다.
REQUIRED_MODEL = [
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
    "size_bucket",
    "medium_support_bucket",
]


@dataclass(frozen=True)
class ArtistResolution:
    """작가명/artist_key 입력을 내부 artist_key로 해석한 결과."""

    artist_key: str | None
    match_score: float
    match_basis: str
    homonym_risk: float
    price_history_count: int
    review_required: bool


def normalize_name(value: object) -> str:
    """작가명 비교를 위해 공백/특수문자/대소문자 차이를 줄인다."""
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)
    return text


def load_store() -> dict[str, Any]:
    """단일 runtime_store.joblib을 읽고 예측에 바로 쓸 수 있게 준비한다."""
    store = joblib.load(STORE_PATH)
    return prepare_store(store)


def get_feature_generation(store: dict[str, Any] | None = None) -> dict[str, Any]:
    """store 안에 동결된 bucket 생성 기준을 반환한다.

    완전 독립 배포에서는 repo helper나 외부 manifest 파일을 읽지 않는다.
    size_bucket 경계, large-area cutoff 같은 피처 생성 기준도
    `runtime_store.joblib` 안에 들어 있어야 한다.
    """
    raw = store if store is not None else joblib.load(STORE_PATH)
    if "feature_generation" not in raw:
        raise KeyError("runtime_store.joblib에 feature_generation 설정이 없습니다.")
    return raw["feature_generation"]


def prepare_store(store: dict[str, Any]) -> dict[str, Any]:
    """store 안의 DataFrame을 런타임용 형태로 정리한다.

    joblib store는 원본 DataFrame과 모델 객체를 그대로 담고 있다. 예측을 위해
    필요한 정규화 이름, 로그가격 컬럼, 작품 feature bucket은 이 단계에서 만든다.
    한 번 준비한 store는 `_prepared=True`를 붙여 같은 세션에서 중복 전처리하지 않는다.
    """
    if store.get("_prepared"):
        return store
    registry = store["artist_registry"].copy()
    aliases = store["artist_aliases"].copy()
    history = store["artist_train_history"].copy()

    for frame in [registry, aliases, history]:
        if "artist_key" in frame.columns:
            frame["artist_key"] = frame["artist_key"].astype(str)

    # alias_normalized는 freeze 단계에서 생성된 정규화 alias다.
    # registry 이름은 이 predictor에서도 동일한 normalize_name() 규칙으로
    # 다시 정규화해서 입력 작가명과 비교한다.
    aliases["alias_normalized"] = aliases["alias_normalized"].fillna("").astype(str)
    registry["name_ko_norm"] = registry["name_ko"].map(normalize_name)
    registry["name_en_norm"] = registry["name_en"].map(normalize_name)

    # 학습 이력의 가격은 로그가격 기준으로 계산한다.
    # log_price_krw가 없는 row가 있으면 price_krw에서 보조로 계산한다.
    history["ln_price_krw"] = pd.to_numeric(history["log_price_krw"], errors="coerce")
    missing_log = history["ln_price_krw"].isna()
    if missing_log.any():
        history.loc[missing_log, "ln_price_krw"] = np.log(
            pd.to_numeric(history.loc[missing_log, "price_krw"], errors="coerce")
        )
    history["depth_cm"] = pd.to_numeric(history["depth_cm"], errors="coerce").fillna(0.0)

    # 같은 작가 이력도 입력 작품과 같은 bucket 체계로 비교해야 하므로,
    # history row에도 area/log_area/size_bucket 등을 생성한다.
    history = add_runtime_features(history, feature_generation=get_feature_generation(store))
    store["artist_registry"] = registry
    store["artist_aliases"] = aliases
    store["artist_train_history"] = history
    store["_prepared"] = True
    return store


def load_params() -> dict[str, Any]:
    """store에 포함된 학습/예측 파라미터를 반환한다."""
    return load_store()["params"]


def load_models() -> dict[int, dict[str, Any]]:
    """store에 포함된 seed별 LightGBM 모델 객체를 반환한다."""
    return load_store()["models"]


def artifacts_from_store(store: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """준비된 store에서 작가 registry/alias/history DataFrame만 꺼낸다."""
    store = prepare_store(store)
    return {
        "registry": store["artist_registry"],
        "aliases": store["artist_aliases"],
        "history": store["artist_train_history"],
    }


def load_artifacts() -> dict[str, pd.DataFrame]:
    """runtime_store.joblib을 읽어 작가 관련 artifact만 반환한다."""
    return artifacts_from_store(load_store())


def add_bucket_features(frame: pd.DataFrame, feature_generation: dict[str, Any], scope: str = "cold") -> pd.DataFrame:
    """동결된 v0.1 기준으로 size/shape bucket을 만든다.

    기존 실험 코드의 bucket 생성 로직 중 Warm 모델이 실제로 쓰는 부분을
    predictor 안에 고정했다. 이 함수 덕분에 모델 번들만 복사해도 repo의
    `extract_price_prediction_v0_1_features.py` 없이 같은 bucket을 만들 수 있다.
    """
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


def add_runtime_features(frame: pd.DataFrame, feature_generation: dict[str, Any] | None = None) -> pd.DataFrame:
    """원본 작품 입력 또는 학습 이력 row에 런타임 피처를 붙인다.

    사용자가 넣는 값은 cm 단위 가로/세로/깊이, 매체, 지지체 정도다.
    모델은 면적, log_area, 종횡비, 3D 여부, size_bucket 등을 필요로 하므로
    이 함수에서 동일한 규칙으로 생성한다.
    """
    out = frame.copy()
    out["width_cm"] = pd.to_numeric(out["width_cm"], errors="coerce")
    out["height_cm"] = pd.to_numeric(out["height_cm"], errors="coerce")
    out["depth_cm"] = pd.to_numeric(out.get("depth_cm", 0.0), errors="coerce").fillna(0.0)
    out["area_cm2"] = pd.to_numeric(out.get("area_cm2"), errors="coerce")
    missing_area = out["area_cm2"].isna() | (out["area_cm2"] <= 0)
    out.loc[missing_area, "area_cm2"] = out.loc[missing_area, "width_cm"] * out.loc[missing_area, "height_cm"]
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1.0))
    min_side = np.minimum(out["width_cm"], out["height_cm"])
    max_side = np.maximum(out["width_cm"], out["height_cm"])
    out["aspect_ratio"] = np.where(min_side > 0, max_side / min_side, np.nan)
    out["has_depth"] = out["depth_cm"] > 0
    if "is_3d_candidate" not in out.columns:
        out["is_3d_candidate"] = out["has_depth"]
    out["medium_category"] = out["medium_category"].fillna("unknown").astype(str)
    out["support_category"] = out["support_category"].fillna("unknown").astype(str)
    out["medium_support_bucket"] = out["medium_category"] + "__" + out["support_category"]

    # 동결된 feature_generation 기준으로 size_bucket, shape_bucket 계열
    # 피처를 만든다. scope "cold"는 학습 당시 해당 bucket 기준을 재사용한다는
    # 의미이며, Warm 예측 자체가 Cold라는 뜻은 아니다.
    return add_bucket_features(out, feature_generation or get_feature_generation(), "cold")


def build_feature_frame(input_frame: pd.DataFrame) -> pd.DataFrame:
    """사용자 입력을 모델이 요구하는 기본 작품 피처 frame으로 바꾼다."""
    missing = [col for col in REQUIRED_INPUT if col not in input_frame.columns]
    if missing:
        raise ValueError(f"required input columns missing: {missing}")
    return add_runtime_features(input_frame)[REQUIRED_MODEL].copy()


def resolve_artist(
    artist_name: str | None = None,
    artist_key: str | None = None,
    artifacts: dict[str, pd.DataFrame] | None = None,
) -> ArtistResolution:
    # Warm 예측은 "같은 작가의 과거 가격 이력"을 직접 사용한다.
    # 따라서 가격 피처를 만들기 전에, 외부 입력으로 들어온 작가명 또는
    # artist_key를 내부 기준의 단일 `artist_key`로 먼저 확정해야 한다.
    #
    # 매칭 순서:
    # 1. 입력에 artist_key가 직접 들어오면 가장 먼저 확인한다. 단, frozen
    #    registry에 존재하고 학습 이력이 1건 이상 있을 때만 신뢰한다.
    # 2. artist_key가 없거나 실패하면 입력 작가명을 정규화해서 frozen alias
    #    테이블에서 찾는다. alias에는 검수된 한글/영문 이름, 표기 변형,
    #    보정명이 들어 있다. 같은 alias가 여러 artist_key에 연결되면
    #    동명이인 가능성이 있으므로 review_required로 막는다.
    # 3. alias에서도 못 찾으면 registry의 정규화된 한글명/영문명을 찾는다.
    #    같은 이름 후보가 여러 명이면 가격 이력이 많은 작가를 우선 선택하지만,
    #    여전히 검수 필요 상태로 표시한다.
    # 4. 유일하고 학습 이력이 있는 artist_key를 확정하지 못하면 Warm 예측을
    #    차단한다. 불확실한 이름 매칭이나 동명이인 때문에 다른 작가의 가격
    #    이력을 가져와 예측하는 것을 막기 위한 처리다.
    artifacts = artifacts or load_artifacts()
    registry = artifacts["registry"]
    aliases = artifacts["aliases"]
    history = artifacts["history"]

    if artist_key:
        # 직접 들어온 artist_key는 가장 강한 매칭 근거다. 그래도 Warm은
        # 같은 작가의 가격 이력이 필요하므로, registry에 존재하고 학습 이력이
        # 1건 이상 있는 키만 사용한다.
        key = str(artist_key)
        hit = registry[registry["artist_key"].eq(key)]
        count = int((history["artist_key"].astype(str) == key).sum())
        if not hit.empty and count >= 1:
            row = hit.iloc[0]
            return ArtistResolution(
                artist_key=key,
                match_score=1.0,
                match_basis="direct_key",
                homonym_risk=float(row.get("is_homonym") or 0),
                price_history_count=count,
                review_required=False,
            )

    norm = normalize_name(artist_name)
    if not norm:
        return ArtistResolution(None, 0.0, "missing_name", 1.0, 0, True)

    # alias 테이블은 검수된 표기 변형과 이름 보정 정보를 담고 있으므로,
    # registry 원본 이름보다 먼저 확인한다. alias confidence를 매칭 점수로
    # 사용하고, 하나의 정규화 이름이 여러 artist_key에 연결되면 자동 예측하지
    # 않고 검수 대상으로 돌린다.
    alias_hits = aliases[aliases["alias_normalized"].eq(norm)].copy()
    if not alias_hits.empty:
        alias_hits["confidence"] = pd.to_numeric(alias_hits["confidence"], errors="coerce").fillna(1.0)
        grouped = alias_hits.groupby("artist_key", as_index=False)["confidence"].max()
        grouped = grouped.sort_values(["confidence", "artist_key"], ascending=[False, True])
        key = str(grouped.iloc[0]["artist_key"])
        count = int((history["artist_key"].astype(str) == key).sum())
        review = len(grouped) > 1
        return ArtistResolution(
            artist_key=key if count >= 1 else None,
            match_score=float(grouped.iloc[0]["confidence"]),
            match_basis="alias",
            homonym_risk=1.0 if review else 0.0,
            price_history_count=count,
            review_required=review or count < 1,
        )

    # alias가 없을 때의 fallback이다. registry의 한글명/영문명을 정규화해서
    # 비교한다. registry 이름에서도 동명이인이 생길 수 있으므로, 여러 후보가
    # 잡히면 review_required=True로 반환한다.
    name_hit = registry[(registry["name_ko_norm"].eq(norm)) | (registry["name_en_norm"].eq(norm))].copy()
    if not name_hit.empty:
        name_hit = name_hit.sort_values(["valid_price_count", "artist_key"], ascending=[False, True])
        key = str(name_hit.iloc[0]["artist_key"])
        count = int((history["artist_key"].astype(str) == key).sum())
        review = len(name_hit) > 1
        return ArtistResolution(
            artist_key=key if count >= 1 else None,
            match_score=1.0,
            match_basis="registry_name",
            homonym_risk=1.0 if review else 0.0,
            price_history_count=count,
            review_required=review or count < 1,
        )

    return ArtistResolution(None, 0.0, "not_found", 1.0, 0, True)


def _stats_from(rows: pd.DataFrame, level: float) -> dict[str, float]:
    """선택된 같은 작가 비교군 rows에서 group 통계 피처를 만든다.

    rows는 이미 같은 artist_key 안에서 특정 비교군 조건을 만족한 과거 작품들이다.
    이 통계는 모델이 "이 작가의 대표 가격대와 가격 분포 폭"을 알 수 있게 하는
    핵심 Warm 피처다.
    """
    lp = rows["ln_price_krw"].astype(float)

    # 면적당 로그가격 proxy다.
    # 로그가격 - log_area는 "작품 크기를 고려했을 때의 가격 수준"을 나타낸다.
    unit = lp - rows["log_area"].astype(float).clip(lower=0)
    return {
        # 같은 작가 과거 로그가격의 대표값과 분포 폭.
        # 표본이 1건이면 q25=q50=q75가 모두 같은 값이고 IQR은 0이 된다.
        "grp_log_price_median": float(lp.median()),
        "grp_log_price_q25": float(lp.quantile(0.25)),
        "grp_log_price_q75": float(lp.quantile(0.75)),
        "grp_log_price_iqr": float(lp.quantile(0.75) - lp.quantile(0.25)),

        # 면적 차이를 보정한 가격대 통계다.
        # 같은 작가라도 소품/대작 가격 차이가 크기 때문에 면적당 가격 정보를 함께 쓴다.
        "grp_unit_area_median": float(unit.median()),
        "grp_unit_area_iqr": float(unit.quantile(0.75) - unit.quantile(0.25)),

        # 참고한 과거 작품 수는 그대로 쓰지 않고 log1p로 완만하게 만든다.
        # 1건과 2건의 차이는 크게 보되, 50건과 51건의 차이는 작게 보려는 목적이다.
        "grp_n_log": float(np.log1p(len(rows))),

        # 1이면 가장 좁은 비교군, 숫자가 커질수록 fallback으로 넓어진 비교군이다.
        "grp_match_level": level,
    }


def assign_stats(frame: pd.DataFrame, artist_history: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """입력 작품마다 같은 작가 이력 통계를 붙인다.

    Warm 모델의 핵심은 "입력 작품의 물성 피처"와 "같은 작가 과거 가격 이력 통계"를
    함께 쓰는 것이다. 이 함수는 입력 작품의 bucket과 같은 작가 history의 bucket을
    비교해서, 가능한 한 좁은 유사작품 비교군의 통계를 만든다.
    """
    out = frame.copy()
    for col in GRP_COLS:
        out[col] = np.nan

    for idx in out.index:
        hit = None

        # 1차 사다리: 같은 작가 안에서 먼저 비교군을 찾는다.
        # - 같은 매체/지지체 + 같은 크기 구간
        # - 같은 크기 구간
        # - 같은 작가 전체
        # 최소 1건부터 통계를 인정한다.
        for level, keys in enumerate(ARTIST_LADDER, start=1):
            sub = artist_history
            for key in keys:
                sub = sub[sub[key].astype(str) == str(out.at[idx, key])]
            if len(sub) >= 1:
                hit = _stats_from(sub, float(level))
                break
        if hit:
            for col, value in hit.items():
                out.at[idx, col] = value

    unresolved = out["grp_match_level"].isna()
    if unresolved.any():
        # 같은 작가 이력에서 통계를 만들 수 없는 예외 상황에 대비한 fallback이다.
        # params["fallback_ladder"]에는 학습 시점에 동결된 전역/그룹 통계가 들어 있다.
        # 정상 Warm 입력에서는 대체로 같은 작가 이력이 있으므로 이 경로는 방어 장치다.
        for level, ladder in enumerate(params["fallback_ladder"], start=len(ARTIST_LADDER) + 1):
            still = out["grp_match_level"].isna()
            if not still.any():
                break
            keys = ladder["keys"]
            kv = out.loc[still, keys].astype(str).agg("|".join, axis=1)
            hitmask = kv.map(lambda value: value in ladder["table"])
            idx = kv.index[hitmask]
            for col in GRP_COLS[:-1]:
                out.loc[idx, col] = [ladder["table"][key].get(col) for key in kv[hitmask]]
            out.loc[idx, "grp_match_level"] = float(level)

        still = out["grp_match_level"].isna()
        # 마지막까지 통계를 못 찾으면 global_fallback을 사용한다.
        # 이 값도 학습 시점에 동결된 값이라 요청마다 다시 계산하지 않는다.
        for col, value in params["global_fallback"].items():
            out.loc[still, col] = value
        out.loc[still, "grp_match_level"] = float(len(ARTIST_LADDER) + len(params["fallback_ladder"]) + 1)

    # group 면적당 가격 + 현재 작품 log_area로 현재 작품의 가격 proxy를 만든다.
    # 이 값은 최종 가격이 아니라 모델 입력 피처 중 하나다.
    out["grp_price_proxy"] = out["grp_unit_area_median"] + out["log_area"].clip(lower=0)
    return out


def _predict_quantiles(models: dict[str, Any], frame: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """seed 하나의 LightGBM Quantile 예측값을 만든다.

    full 모델은 전체 피처를 사용해 q10/q50/q90을 예측한다.
    lean 모델은 흔들림이 적은 안정 피처만 사용해 q50을 예측한다.
    최종 기준가격은 full q50과 lean q50을 50:50 평균낸 값이다.
    """
    out = pd.DataFrame(index=frame.index)
    full_cols = params["full_num_cols"] + params["cat_cols"]
    lean_cols = params["lean_num_cols"] + params["cat_cols"]

    # q10/q50/q90은 위에서 만든 q25/q75 통계값을 그대로 복사한 값이 아니다.
    # q25/q75/IQR 등 group 통계와 작품 피처를 입력으로 받은 LightGBM 모델이
    # 새로 출력하는 "예측 분포의 낮은값/중앙값/높은값"이다.
    out["lgbq_full_q10"] = np.asarray(models["full_q10"].predict(frame[full_cols]), dtype=float)
    out["lgbq_full_q50"] = np.asarray(models["full_q50"].predict(frame[full_cols]), dtype=float)
    out["lgbq_full_q90"] = np.asarray(models["full_q90"].predict(frame[full_cols]), dtype=float)
    out["lgbq_lean_q50"] = np.asarray(models["lean_q50"].predict(frame[lean_cols]), dtype=float)

    # 대표 기준가격. full은 정보량이 많고 lean은 안정적이므로 둘을 평균낸다.
    out["lgbq_full_lean_avg"] = 0.50 * out["lgbq_full_q50"] + 0.50 * out["lgbq_lean_q50"]

    # 예측 불확실성 폭. 최종 가격에 직접 더하지 않고, 결과 해석/검수 표시용으로 쓴다.
    out["lgbq_width"] = np.maximum(out["lgbq_full_q90"] - out["lgbq_full_q10"], 0.0)
    return out


def _residual_feature_frame(frame: pd.DataFrame, qpred: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """Huber residual 모델에 넣을 보정용 피처 frame을 만든다.

    residual 모델은 원본 작품/group 피처뿐 아니라 방금 계산한 Quantile 예측값도
    함께 본다. 즉 "기준가격 모델이 어떤 분포를 예측했는지"까지 참고해서
    남은 오차를 보정한다.
    """
    out = frame.copy()
    for col in params["q_cols"]:
        out[col] = qpred[col].to_numpy(dtype=float)

    # LightGBM categorical feature는 문자열 결측값을 명시적으로 채워준다.
    for col in params["residual_cat_cols"]:
        out[col] = out[col].astype(str).fillna("__MISSING__")
    return out[params["residual_num_cols"] + params["residual_cat_cols"]]


def _predict_one_seed(seed_models: dict[str, Any], feature_frame: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """seed 하나 기준의 최종 로그가격 후보를 계산한다."""

    # 1. Quantile 모델로 q10/q50/q90, lean q50, q50 평균 기준가격을 만든다.
    qpred = _predict_quantiles(seed_models, feature_frame, params)

    # 2. Quantile 결과를 포함한 보정 피처를 만들어 residual 모델에 넣는다.
    residual_x = _residual_feature_frame(feature_frame, qpred, params)
    residual = np.asarray(seed_models["lightgbm_residual"].predict(residual_x), dtype=float)

    # 3. residual은 그대로 전부 더하지 않는다.
    #    학습/검증에서 정한 보정 강도(current_residual_strength)를 곱하고,
    #    current_residual_cap_log 범위 안으로 clip한다.
    #    현재 값은 보통 0.50 * residual을 -0.10~+0.10 log 범위 안에서 반영한다.
    correction = np.clip(
        float(params["current_residual_strength"]) * residual,
        -float(params["current_residual_cap_log"]),
        float(params["current_residual_cap_log"]),
    )
    out = qpred.copy()
    out["lgb_huber_residual_log"] = residual
    out["current_residual_correction_log"] = correction

    # 4. seed 하나의 최종 로그가격 = Quantile 기준가격 + 제한된 residual 보정값.
    out["current_pred_log"] = out["lgbq_full_lean_avg"].to_numpy(dtype=float) + correction
    return out


def predict_by_artist_key(
    input_frame: pd.DataFrame,
    artist_key: str,
    *,
    artifacts: dict[str, pd.DataFrame] | None = None,
    models: dict[int, dict[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """이미 확정된 artist_key로 Warm 가격을 예측한다.

    이 함수는 작가명 매칭을 하지 않는다. 이미 내부 artist_key를 알고 있을 때
    사용하며, fixed test 검증에서도 이 경로를 사용한다.
    """
    params = params or load_params()
    models = models or load_models()
    artifacts = artifacts or load_artifacts()

    # 확정된 artist_key의 학습 이력을 꺼낸다. Warm 모델은 이 이력이 없으면
    # 같은 작가 가격 통계를 만들 수 없으므로 예측을 중단한다.
    history = artifacts["history"]
    artist_history = history[history["artist_key"].astype(str).eq(str(artist_key))].copy()
    if artist_history.empty:
        raise ValueError(f"artist train history not found: {artist_key}")

    # 사용자 입력 작품 피처 생성 -> 같은 작가 통계 부착 -> seed별 예측 순서로 진행한다.
    frame = build_feature_frame(input_frame)
    fs = assign_stats(frame, artist_history, params)

    # 학습 시 여러 seed로 만든 모델을 모두 호출한 뒤 평균낸다.
    # seed 평균은 특정 seed의 우연한 흔들림을 줄이기 위한 앙상블 처리다.
    seed_parts = [_predict_one_seed(models[int(seed)], fs, params) for seed in params["seeds"]]
    mean = pd.concat(seed_parts, keys=params["seeds"], names=["seed", "row"])
    mean = mean.groupby(level="row").mean(numeric_only=True).sort_index()

    # 출력은 원본 입력 frame에 예측 결과와 진단용 중간값을 붙여 반환한다.
    out = input_frame.copy()
    out["artist_key"] = str(artist_key)
    out["warm_lite_unified_current_pred_log"] = mean["current_pred_log"].to_numpy(dtype=float)

    # 모델은 로그가격을 예측하므로 exp()로 원화 가격으로 되돌린다.
    # 비정상적으로 작은 값은 최소 1,000원으로 방어한다.
    out["warm_lite_unified_current_pred_price_krw"] = np.clip(
        np.exp(out["warm_lite_unified_current_pred_log"].to_numpy(dtype=float)),
        1_000.0,
        None,
    )
    out["lgbq_full_q10"] = mean["lgbq_full_q10"].to_numpy(dtype=float)
    out["lgbq_full_q50"] = mean["lgbq_full_q50"].to_numpy(dtype=float)
    out["lgbq_full_q90"] = mean["lgbq_full_q90"].to_numpy(dtype=float)
    out["lgbq_lean_q50"] = mean["lgbq_lean_q50"].to_numpy(dtype=float)
    out["lgbq_full_lean_avg"] = mean["lgbq_full_lean_avg"].to_numpy(dtype=float)
    out["lgbq_width"] = mean["lgbq_width"].to_numpy(dtype=float)
    out["lgb_huber_residual_log"] = mean["lgb_huber_residual_log"].to_numpy(dtype=float)
    out["current_residual_correction_log"] = mean["current_residual_correction_log"].to_numpy(dtype=float)
    out["artist_history_n"] = int(len(artist_history))
    out["runtime_source"] = "joblib_runtime_store_no_db_csv"
    return out


def predict(
    input_frame: pd.DataFrame,
    *,
    artist_name: str | None = None,
    artist_key: str | None = None,
    artifacts: dict[str, pd.DataFrame] | None = None,
    models: dict[int, dict[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """외부 사용자가 호출하는 기본 예측 함수.

    입력 작품 DataFrame과 artist_name 또는 artist_key를 받아 Warm 예측을 수행한다.
    내부 순서는 다음과 같다.

    1. runtime_store.joblib에서 artifact/model/params 준비
    2. artist_name 또는 artist_key를 내부 artist_key로 해석
    3. 동명이인/복수 후보/이력 없음이면 Warm 예측 중단
    4. 확정된 artist_key로 predict_by_artist_key() 실행
    5. 작가 매칭 점수와 매칭 근거를 결과에 함께 반환

    운영 API에서는 3번 실패 상황을 Cold 또는 review_required로 라우팅할 수 있지만,
    이 predictor 단독 실행에서는 Warm 전용이므로 ValueError를 발생시킨다.
    """
    artifacts = artifacts or load_artifacts()
    resolved = resolve_artist(artist_name=artist_name, artist_key=artist_key, artifacts=artifacts)
    if resolved.artist_key is None or resolved.review_required:
        raise ValueError(f"artist not resolved for warm prediction: {resolved}")
    out = predict_by_artist_key(
        input_frame,
        resolved.artist_key,
        artifacts=artifacts,
        models=models,
        params=params,
    )
    out["artist_match_score"] = resolved.match_score
    out["artist_match_basis"] = resolved.match_basis
    out["artist_homonym_risk"] = resolved.homonym_risk
    return out
