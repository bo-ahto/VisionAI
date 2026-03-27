"""통합 테스트 — predictor, dataset_builder, bias_check, cold_start 경로.

Codex 리뷰 반영: 핵심 운영 경로의 조립 결과 회귀 방지.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from visionai.price_engine.preprocessing.dimension_parser import parse_dimension
from visionai.price_engine.preprocessing.medium_parser import parse_medium
from visionai.price_engine.preprocessing.year_parser import parse_year
from visionai.price_engine.validation.bias_check import compute_bias_table
from visionai.price_engine.validation.metrics import compute_metrics


@pytest.fixture()
def mini_works() -> pd.DataFrame:
    """통합 테스트용 최소 데이터셋."""
    return pd.DataFrame({
        "타입": ["위클리"] * 10,
        "회차": [100, 150, 200, 250, 300, 350, 400, 420, 440, 460],
        "Lot": list(range(1, 11)),
        "작가": ["A", "A", "A", "B", "B", "A", "C", "C", "A", "B"],
        "제목": ["작품1", "무제", "작품3", "Untitled", "작품5", "작품6", "작품7", "작품8", "작품9", "작품10"],
        "제작연도": ["1990", "", "2000", "2010", "", "1995", "2020", "", "2005", "2015"],
        "재료": ["캔버스에 유채", "종이에 수묵", "아크릴", "", "혼합재료", "캔버스에 유채", "판화", "Bronze", "캔버스에 유채", "종이에 먹"],
        "크기": ["81×116cm", "53x45.5cm", "", "30×20×15cm", "72.7×60.6cm", "100×80cm", "diameter 30cm", "高48", "90.9×72.7cm", "50×40cm"],
        "추정가(최저)": [500000, 300000, 1000000, 2000000, 800000, 3000000, 500000, 5000000, 2000000, 600000],
        "추정가(최고)": [1000000, 600000, 2000000, 4000000, 1500000, 5000000, 1000000, 8000000, 4000000, 1200000],
        "낙찰가": [700000, 400000, 1500000, 3000000, 1000000, 4000000, 600000, 6000000, 2500000, 800000],
        "입찰수": [5, 3, 8, 10, 4, 12, 2, 15, 7, 3],
        "상태": ["낙찰"] * 10,
    })


class TestParserIntegration:
    """파서 3종이 실제 데이터 패턴에서 올바르게 작동하는지."""

    def test_all_parsers_on_mini_data(self, mini_works: pd.DataFrame) -> None:
        for _, row in mini_works.iterrows():
            dim = parse_dimension(row["크기"])
            med = parse_medium(row["재료"])
            year = parse_year(row["제작연도"])

            # 파싱 결과는 항상 유효한 타입
            assert isinstance(dim.is_3d, bool)
            assert isinstance(med.medium_category, str)
            assert isinstance(year.is_year_missing, bool)

    def test_3d_detection(self) -> None:
        r = parse_dimension("30×20×15cm")
        assert r.is_3d is True

    def test_untitled_detection(self, mini_works: pd.DataFrame) -> None:
        titles = mini_works["제목"]
        untitled = titles.str.contains(r"무제|Untitled", regex=True, na=False)
        assert untitled.sum() == 2  # "무제", "Untitled"


class TestBiasCheckIntegration:
    """재변환 편향 검증이 올바른 결과를 내는지."""

    def test_perfect_prediction_no_bias(self) -> None:
        y_true = np.array([5e6, 10e6, 50e6, 1e8])
        y_pred = np.array([5e6, 10e6, 50e6, 1e8])
        table = compute_bias_table(y_true, y_pred)
        for _, row in table.iterrows():
            assert row["median_ratio"] == 1.0
            assert row["verdict"] == "정상"

    def test_overestimation_detected(self) -> None:
        y_true = np.array([500000, 800000, 900000])
        y_pred = np.array([800000, 1200000, 1400000])  # ~1.6x
        table = compute_bias_table(y_true, y_pred)
        low_tier = table[table["price_tier"] == "<100만"]
        assert len(low_tier) == 1
        assert low_tier.iloc[0]["verdict"] == "과대추정 조사"

    def test_underestimation_detected(self) -> None:
        y_true = np.array([2e8, 3e8, 5e8])
        y_pred = np.array([1.5e8, 2e8, 3.5e8])  # ~0.7x
        table = compute_bias_table(y_true, y_pred)
        high_tier = table[table["price_tier"] == "1억+"]
        assert len(high_tier) == 1
        assert "smearing" in high_tier.iloc[0]["verdict"]


class TestMetricsIntegration:
    """metrics가 엣지 케이스를 안전하게 처리하는지."""

    def test_empty_input(self) -> None:
        m = compute_metrics(np.array([]), np.array([]))
        assert m.n == 0
        assert np.isnan(m.mape)

    def test_single_element(self) -> None:
        m = compute_metrics(np.array([100.0]), np.array([120.0]))
        assert m.n == 1
        assert m.mape == 20.0

    def test_zero_true_excluded(self) -> None:
        y_true = np.array([0.0, 100.0, 200.0])
        y_pred = np.array([50.0, 120.0, 180.0])
        m = compute_metrics(y_true, y_pred)
        assert m.n == 2  # 0인 건 제외


class TestColdStartReport:
    """D등급 리포트가 is_new_artist 불리언으로 분류하는지."""

    def test_new_artist_slice(self) -> None:
        from visionai.price_engine.reporting.cold_start_report import generate_cold_start_report

        df = pd.DataFrame({
            "낙찰가": [1000000, 2000000, 500000],
            "artist_clean": ["A", "B", "__UNKNOWN__"],
            "is_new_artist": [True, False, False],
        })
        y_pred = np.array([1200000, 1800000, 600000])
        grades = pd.Series(["D", "D", "D"])

        report = generate_cold_start_report(df, y_pred, grades)
        assert "is_new_artist=True" in report
        assert "__UNKNOWN__" in report


class TestDatasetBuilderFallback:
    """dataset_builder의 cold_start fallback이 실제로 주입되는지."""

    def test_new_artist_gets_fallback_stats(self) -> None:
        from visionai.price_engine.features.cold_start import (
            build_cold_start_fallback,
            compute_estimate_tier,
        )

        # 과거 데이터: 작가 A만 있음
        works = pd.DataFrame({
            "타입": ["위클리"] * 5,
            "회차": [100, 150, 200, 250, 300],
            "Lot": [1, 2, 3, 4, 5],
            "작가": ["A"] * 5,
            "artist_clean": ["A"] * 5,
            "낙찰가": [1000000, 2000000, 3000000, 1500000, 2500000],
            "추정가(최저)": [500000] * 5,
            "추정가(최고)": [3000000] * 5,
        })

        fallback = build_cold_start_fallback(works, cutoff_session=400)
        # fallback 테이블이 비어있지 않아야 함
        assert not fallback.empty
        # fallback에 avg/max/count 컬럼이 있어야 함
        assert "fallback_avg_price" in fallback.columns
        assert "fallback_max_price" in fallback.columns

    def test_estimate_tier_classification(self) -> None:
        from visionai.price_engine.features.cold_start import compute_estimate_tier

        tiers = compute_estimate_tier(pd.Series([
            1_000_000,      # 하위
            10_000_000,     # 중하
            50_000_000,     # 중상
            200_000_000,    # 상위
            2_000_000_000,  # 최상
        ]))
        assert list(tiers) == ["하위", "중하", "중상", "상위", "최상"]


class TestPredictionsJsonSchema:
    """predictions.json 메타 필드가 올바르게 생성되는지."""

    def test_meta_fields_present(self) -> None:
        import json
        from pathlib import Path

        json_path = Path("frontend/data/predictions.json")
        if not json_path.exists():
            pytest.skip("predictions.json not generated yet")

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # 필수 최상위 필드
        assert "generated_at" in data
        assert "model_version" in data
        assert "model_metrics" in data
        assert "artists" in data
        assert "confidence_guide" in data
        assert "low_price_warning" in data

        # 작가별 예측에 메타 필드 존재
        for artist_name, artist_data in list(data["artists"].items())[:5]:
            for ho_name, pred in artist_data.get("predictions_by_size", {}).items():
                assert "prediction_method" in pred, f"{artist_name}/{ho_name} missing prediction_method"
                assert "is_recommended" in pred, f"{artist_name}/{ho_name} missing is_recommended"
                assert "option_b_blocked" in pred, f"{artist_name}/{ho_name} missing option_b_blocked"
                assert pred["prediction_method"] == "historical_aggregate"
                break  # 첫 호수만 확인
            break  # 첫 작가만 확인

    def test_option_b_blocked_for_low_basis(self) -> None:
        import json
        from pathlib import Path

        json_path = Path("frontend/data/predictions.json")
        if not json_path.exists():
            pytest.skip("predictions.json not generated yet")

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # basis_count < 3이면 option_b_blocked = True
        for artist_data in data["artists"].values():
            for pred in artist_data.get("predictions_by_size", {}).values():
                if pred["basis_count"] < 3:
                    assert pred["option_b_blocked"] is True
