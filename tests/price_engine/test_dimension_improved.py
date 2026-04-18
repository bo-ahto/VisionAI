"""크기(호수) 처리 개선 테스트."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from visionai.price_engine.features.hedonic_stats import (
    compute_estimated_ho,
    compute_ln_surface_area,
    compute_orientation,
    compute_size_bucket,
)
from visionai.price_engine.preprocessing.dimension_parser import (
    area_to_ho_f,
    parse_dimension,
)


class TestAreaToHoF:
    """F 타입 호수 보간."""

    def test_exact_40ho(self) -> None:
        """40호F 면적(8030cm²) → 정확히 40.0."""
        assert area_to_ho_f(8030) == pytest.approx(40.0, abs=0.1)

    def test_exact_20ho(self) -> None:
        """20호F 면적(4406cm²) → 정확히 20.0."""
        assert area_to_ho_f(4406) == pytest.approx(20.0, abs=0.1)

    def test_exact_100ho(self) -> None:
        """100호F 면적(21135cm²) → 정확히 100.0."""
        assert area_to_ho_f(21135) == pytest.approx(100.0, abs=0.1)

    def test_zero_area(self) -> None:
        """면적 0 → 0.0호."""
        assert area_to_ho_f(0) == 0.0

    def test_negative_area(self) -> None:
        """음수 면적 → 0.0호."""
        assert area_to_ho_f(-100) == 0.0


class TestHoDirectParsing:
    """호수 직접 표기 파싱."""

    def test_20ho(self) -> None:
        """'20호' → F 기준 72.7x60.6."""
        r = parse_dimension("20호")
        assert r.pattern_used == "ho_direct"
        assert r.ho_number == 20
        assert r.ho_type == "F"
        assert r.height_cm == pytest.approx(72.7)
        assert r.width_cm == pytest.approx(60.6)

    def test_20f(self) -> None:
        """'20F' → F 타입."""
        r = parse_dimension("20F")
        assert r.ho_number == 20
        assert r.ho_type == "F"

    def test_20p_uses_f_approx(self) -> None:
        """'20P' → F 규격으로 근사 (현재 F만 지원)."""
        r = parse_dimension("20P")
        assert r.ho_type == "P"
        # 현재는 F 규격 사용
        assert r.height_cm == pytest.approx(72.7)

    def test_cm_with_ho_suffix(self) -> None:
        """'72.7x60.6cm (20호)' → 2D 패턴 우선."""
        r = parse_dimension("72.7x60.6cm (20호)")
        assert r.pattern_used == "2d"


class TestDepthCm:
    """3D depth 보존."""

    def test_3d_h_marker(self) -> None:
        """'31x13x22(h)cm' → depth=13."""
        r = parse_dimension("31x13x22(h)cm")
        assert r.depth_cm == pytest.approx(13.0)
        assert r.is_3d is True

    def test_3d_standard(self) -> None:
        """'30x20x15cm' → depth=15 (최소값)."""
        r = parse_dimension("30x20x15cm")
        assert r.depth_cm == pytest.approx(15.0)

    def test_2d_no_depth(self) -> None:
        """2D 작품은 depth=None."""
        r = parse_dimension("81x116cm")
        assert r.depth_cm is None


class TestNewHedoStatsFunctions:
    """신규 hedonic_stats 함수."""

    def test_estimated_ho(self) -> None:
        """compute_estimated_ho: 면적 → 호수."""
        areas = pd.Series([4406, 8030, 21135, 0])
        result = compute_estimated_ho(areas)
        assert result.iloc[0] == pytest.approx(20.0, abs=0.1)
        assert result.iloc[1] == pytest.approx(40.0, abs=0.1)
        assert result.iloc[3] == 0.0

    def test_ln_surface_area(self) -> None:
        """compute_ln_surface_area: ln(면적)."""
        areas = pd.Series([1, 100, 10000])
        result = compute_ln_surface_area(areas)
        np.testing.assert_allclose(
            result.values, [0.0, np.log(100), np.log(10000)], rtol=1e-5,
        )

    def test_size_bucket(self) -> None:
        """compute_size_bucket: 면적 → 소/중/대/초대형."""
        areas = pd.Series([1000, 3000, 10000, 30000])
        result = compute_size_bucket(areas)
        assert list(result) == ["소형", "중형", "대형", "초대형"]

    def test_orientation(self) -> None:
        """compute_orientation: 종횡비 → portrait/landscape/square."""
        h = pd.Series([150, 80, 100])
        w = pd.Series([100, 120, 100])
        result = compute_orientation(h, w)
        assert result.iloc[0] == "portrait"
        assert result.iloc[1] == "landscape"
        assert result.iloc[2] == "square"
