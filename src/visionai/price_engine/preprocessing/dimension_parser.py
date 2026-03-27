"""크기 문자열 파싱 모듈.

5개 패턴으로 경매 작품 크기 문자열을 height_cm, width_cm, surface_area,
aspect_ratio, is_3d로 변환한다.

기획서 참조: 3.2.1
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np


@dataclass
class DimensionResult:
    """크기 파싱 결과."""

    height_cm: float | None
    width_cm: float | None
    surface_area: float | None
    aspect_ratio: float | None
    is_3d: bool
    is_size_imputed: bool = False
    pattern_used: str = "none"


# 패턴 정의 (우선순위 순)
_PAT_3D = re.compile(
    r"(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)"
)
_PAT_3D_H = re.compile(
    r"(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*\(?[hH]\)?"
)
_PAT_2D = re.compile(r"(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)")
_PAT_HEIGHT = re.compile(r"[高Hh]\s*(\d+\.?\d*)")
_PAT_DIAMETER = re.compile(
    r"(?:[Øø]|diameter|지름)\s*(\d+\.?\d*)", re.IGNORECASE
)


def parse_dimension(raw: str | None) -> DimensionResult:
    """크기 문자열을 파싱하여 DimensionResult를 반환한다.

    Args:
        raw: 원본 크기 문자열. 예: "81×116cm", "31×13×22(h)cm", "高48"

    Returns:
        DimensionResult with parsed dimensions.
    """
    if not raw or not isinstance(raw, str):
        return DimensionResult(
            height_cm=None,
            width_cm=None,
            surface_area=None,
            aspect_ratio=None,
            is_3d=False,
            is_size_imputed=True,
            pattern_used="missing",
        )

    text = raw.strip()

    # 패턴 5: 원형 (diameter)
    m = _PAT_DIAMETER.search(text)
    if m:
        d = float(m.group(1))
        return DimensionResult(
            height_cm=d,
            width_cm=d,
            surface_area=d * d,
            aspect_ratio=1.0,
            is_3d=False,
            pattern_used="diameter",
        )

    # 패턴 2: 3D with (h) marker
    m = _PAT_3D_H.search(text)
    if m:
        v1, v2, v3 = float(m.group(1)), float(m.group(2)), float(m.group(3))
        # (h) 표기가 있으면 세 번째 값이 height
        height = v3
        width = max(v1, v2)
        return DimensionResult(
            height_cm=height,
            width_cm=width,
            surface_area=height * width,
            aspect_ratio=round(height / width, 4) if width > 0 else None,
            is_3d=True,
            pattern_used="3d_h",
        )

    # 패턴 2: 3D 표준 (without h marker)
    m = _PAT_3D.search(text)
    if m:
        vals = sorted(
            [float(m.group(1)), float(m.group(2)), float(m.group(3))],
            reverse=True,
        )
        height = vals[0]
        width = vals[1]
        return DimensionResult(
            height_cm=height,
            width_cm=width,
            surface_area=height * width,
            aspect_ratio=round(height / width, 4) if width > 0 else None,
            is_3d=True,
            pattern_used="3d",
        )

    # 패턴 1: 2D 표준
    m = _PAT_2D.search(text)
    if m:
        v1, v2 = float(m.group(1)), float(m.group(2))
        height = max(v1, v2)
        width = min(v1, v2)
        return DimensionResult(
            height_cm=height,
            width_cm=width,
            surface_area=height * width,
            aspect_ratio=round(height / width, 4) if width > 0 else None,
            is_3d=False,
            pattern_used="2d",
        )

    # 패턴 3: 높이만
    m = _PAT_HEIGHT.search(text)
    if m:
        h = float(m.group(1))
        return DimensionResult(
            height_cm=h,
            width_cm=None,
            surface_area=None,
            aspect_ratio=None,
            is_3d=True,
            pattern_used="height_only",
        )

    # 파싱 실패
    return DimensionResult(
        height_cm=None,
        width_cm=None,
        surface_area=None,
        aspect_ratio=None,
        is_3d=False,
        is_size_imputed=True,
        pattern_used="failed",
    )


def impute_surface_area(
    area: float | None,
    artist: str | None,
    medium: str | None,
    artist_medium_medians: dict[tuple[str, str], float] | None = None,
    medium_medians: dict[str, float] | None = None,
    global_median: float = 2800.0,
) -> tuple[float, bool]:
    """결측 면적을 조건부 대체한다.

    기획서 3.2.1 결측 대체 순서:
    1순위: 동일 작가 + 동일 매체 중앙값
    2순위: 동일 매체 전체 중앙값
    3순위: 전체 중앙값 (~2800 cm²)

    Returns:
        (imputed_area, was_imputed)
    """
    if area is not None and not np.isnan(area):
        return area, False

    if artist_medium_medians and artist and medium:
        key = (artist, medium)
        if key in artist_medium_medians:
            return artist_medium_medians[key], True

    if medium_medians and medium and medium in medium_medians:
        return medium_medians[medium], True

    return global_median, True
