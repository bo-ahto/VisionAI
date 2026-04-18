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
    depth_cm: float | None = None  # 3D 작품의 깊이
    surface_area: float | None = None
    aspect_ratio: float | None = None
    is_3d: bool = False
    is_size_imputed: bool = False
    pattern_used: str = "none"
    ho_number: int | None = None  # 호수 직접 표기 시
    ho_type: str | None = None  # F/P/M/S 타입


# ─── 한국 캔버스 호수 규격 (F 타입 기준) ───
HO_F_TABLE: dict[int, tuple[float, float]] = {
    0: (18.0, 14.0), 1: (22.7, 15.8), 2: (25.8, 17.9),
    3: (27.3, 22.0), 4: (33.4, 24.2), 5: (34.8, 27.3),
    6: (40.9, 31.8), 8: (45.5, 37.9), 10: (53.0, 45.5),
    12: (60.6, 50.0), 15: (65.1, 53.0), 20: (72.7, 60.6),
    25: (80.3, 65.1), 30: (90.9, 72.7), 40: (100.0, 80.3),
    50: (116.8, 91.0), 60: (130.3, 97.0), 80: (145.5, 112.1),
    100: (162.2, 130.3), 120: (193.9, 130.3),
    150: (227.3, 181.8), 200: (259.1, 193.9),
}

_HO_KEYS = sorted(HO_F_TABLE.keys())
_HO_AREAS = [HO_F_TABLE[k][0] * HO_F_TABLE[k][1] for k in _HO_KEYS]


def area_to_ho_f(surface_area: float) -> float:
    """면적(cm²) → F 타입 기준 호수 보간."""
    if surface_area <= 0 or not np.isfinite(surface_area):
        return 0.0
    return float(np.interp(surface_area, _HO_AREAS, _HO_KEYS))


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
_PAT_HO_TYPE = re.compile(r"(\d+)\s*([FPMSfpms])호?")
_PAT_HO = re.compile(r"(\d+)\s*호")


def _ho_to_dim(ho: int, ho_type: str = "F") -> DimensionResult:
    """호수 + 타입 → DimensionResult.

    현재는 F 타입 규격만 지원. P/M/S 입력 시에도 F 규격으로 근사.
    ho_type 필드에 원본 타입을 보존하여 향후 확장 가능.
    """
    table = HO_F_TABLE  # TODO: P/M/S 테이블 추가 시 타입별 분기
    if ho in table:
        h, w = table[ho]
    else:
        # 가장 가까운 호수로 보간
        keys = sorted(table.keys())
        areas = [table[k][0] * table[k][1] for k in keys]
        target_area = float(np.interp(ho, keys, areas))
        # 근사: sqrt(target_area * aspect_ratio) for h, w
        avg_ratio = 1.3  # F 타입 평균 종횡비
        h = float(np.sqrt(target_area * avg_ratio))
        w = target_area / h if h > 0 else 0
    return DimensionResult(
        height_cm=h, width_cm=w, surface_area=h * w,
        aspect_ratio=round(h / w, 4) if w > 0 else None,
        is_3d=False, pattern_used="ho_direct",
        ho_number=ho, ho_type=ho_type.upper(),
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
        height = v3
        width = max(v1, v2)
        depth = min(v1, v2)
        return DimensionResult(
            height_cm=height,
            width_cm=width,
            depth_cm=depth,
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
        depth = vals[2]
        return DimensionResult(
            height_cm=height,
            width_cm=width,
            depth_cm=depth,
            surface_area=height * width,
            aspect_ratio=round(height / width, 4) if width > 0 else None,
            is_3d=True,
            pattern_used="3d",
        )

    # 패턴 1: 2D 표준
    # 코덱스 P2 (2026-04-17): 원본 순서를 보존해야 compute_orientation이 landscape 감지.
    # api/server.py가 parse_dimension("{width}x{height}") 형식으로 호출 → v1=너비, v2=높이.
    # aspect_ratio는 스케일 무관성 위해 long/short 비율로 계산 (항상 ≥ 1).
    m = _PAT_2D.search(text)
    if m:
        v1, v2 = float(m.group(1)), float(m.group(2))
        width, height = v1, v2
        long_ = max(width, height)
        short = min(width, height)
        return DimensionResult(
            height_cm=height,
            width_cm=width,
            surface_area=height * width,
            aspect_ratio=round(long_ / short, 4) if short > 0 else None,
            is_3d=False,
            pattern_used="2d",
        )

    # 패턴 6: 호수 + 타입 ("20F", "30P")
    m = _PAT_HO_TYPE.search(text)
    if m:
        ho = int(m.group(1))
        ho_type = m.group(2).upper()
        return _ho_to_dim(ho, ho_type)

    # 패턴 7: 호수 단독 ("20호")
    m = _PAT_HO.search(text)
    if m:
        ho = int(m.group(1))
        return _ho_to_dim(ho, "F")

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
