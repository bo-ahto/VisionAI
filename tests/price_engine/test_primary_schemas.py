"""v3.6 Phase 1 PR1: PredictRequest schema 확장 단위 테스트.

검증:
- PredictRequest + BatchItem 의 신규 필드 (artwork_id / artwork_url / year_made)
- year_made [1800, 2030] 범위 validation
- artwork_id / artwork_url length validation
- 모든 필드 default None (backward compat — 기존 client 영향 X)
- BatchPredictRequest 50 item limit 그대로
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from visionai.price_engine.api.primary_schemas import (
    BatchItem,
    BatchPredictRequest,
    PredictRequest,
)

# ---- 기존 필드 backward compat (신규 필드 없이 정상) ----


def test_predict_request_backward_compat_minimal():
    """v3.6 Phase 1 변경 후에도 기존 client (신규 필드 없이) 정상 동작."""
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic on canvas",
    )
    assert req.artwork_id is None
    assert req.artwork_url is None
    assert req.year_made is None


def test_batch_item_backward_compat_minimal():
    item = BatchItem(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="oil",
    )
    assert item.artwork_id is None
    assert item.artwork_url is None
    assert item.year_made is None


# ---- 신규 필드 valid 입력 ----


def test_predict_request_with_artwork_id_only():
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        artwork_id="13458973",
    )
    assert req.artwork_id == "13458973"
    assert req.year_made is None


def test_predict_request_with_artwork_url_only():
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        artwork_url="https://www.saatchiart.com/art/.../view",
    )
    assert req.artwork_url == "https://www.saatchiart.com/art/.../view"


def test_predict_request_with_year_made_manual():
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        year_made=2020,
    )
    assert req.year_made == 2020


def test_predict_request_all_three_v36_fields():
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        artwork_id="13458973",
        artwork_url="https://www.saatchiart.com/art/.../view",
        year_made=2020,
    )
    assert req.artwork_id == "13458973"
    assert req.artwork_url == "https://www.saatchiart.com/art/.../view"
    assert req.year_made == 2020


# ---- year_made validation (10 invalid cases 의 절반) ----


def test_year_made_below_min_1800_reject():
    with pytest.raises(ValidationError):
        PredictRequest(
            artist_name="kim",
            width_cm=100,
            height_cm=80,
            medium="acrylic",
            year_made=1799,
        )


def test_year_made_above_max_2030_reject():
    with pytest.raises(ValidationError):
        PredictRequest(
            artist_name="kim",
            width_cm=100,
            height_cm=80,
            medium="acrylic",
            year_made=2031,
        )


def test_year_made_min_boundary_1800_accept():
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        year_made=1800,
    )
    assert req.year_made == 1800


def test_year_made_max_boundary_2030_accept():
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        year_made=2030,
    )
    assert req.year_made == 2030


def test_year_made_negative_reject():
    with pytest.raises(ValidationError):
        PredictRequest(
            artist_name="kim",
            width_cm=100,
            height_cm=80,
            medium="acrylic",
            year_made=-1,
        )


# ---- artwork_id length validation ----


def test_artwork_id_max_length_64_accept():
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        artwork_id="x" * 64,
    )
    assert len(req.artwork_id) == 64


def test_artwork_id_over_max_length_reject():
    with pytest.raises(ValidationError):
        PredictRequest(
            artist_name="kim",
            width_cm=100,
            height_cm=80,
            medium="acrylic",
            artwork_id="x" * 65,
        )


# ---- artwork_url length validation ----


def test_artwork_url_max_length_500_accept():
    req = PredictRequest(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        artwork_url="https://www.saatchiart.com/"
        + "x" * (500 - len("https://www.saatchiart.com/")),
    )
    assert len(req.artwork_url) == 500


def test_artwork_url_over_max_length_reject():
    with pytest.raises(ValidationError):
        PredictRequest(
            artist_name="kim",
            width_cm=100,
            height_cm=80,
            medium="acrylic",
            artwork_url="x" * 501,
        )


# ---- BatchItem validation 동일하게 적용 ----


def test_batch_item_year_made_below_min_reject():
    with pytest.raises(ValidationError):
        BatchItem(
            artist_name="kim",
            width_cm=100,
            height_cm=80,
            medium="oil",
            year_made=1799,
        )


def test_batch_item_year_made_above_max_reject():
    with pytest.raises(ValidationError):
        BatchItem(
            artist_name="kim",
            width_cm=100,
            height_cm=80,
            medium="oil",
            year_made=2031,
        )


def test_batch_item_with_all_v36_fields():
    item = BatchItem(
        artist_name="kim",
        width_cm=100,
        height_cm=80,
        medium="oil",
        artwork_id="13458973",
        artwork_url="https://www.saatchiart.com/x",
        year_made=2018,
    )
    assert item.artwork_id == "13458973"
    assert item.year_made == 2018


def test_batch_predict_request_50_item_limit_unchanged():
    """50 item limit 보존 — v3.6 변경 영향 없음."""
    items = [
        BatchItem(artist_name="kim", width_cm=100, height_cm=80, medium="oil") for _ in range(50)
    ]
    req = BatchPredictRequest(artworks=items)
    assert len(req.artworks) == 50


def test_batch_predict_request_over_50_reject():
    items = [
        BatchItem(artist_name="kim", width_cm=100, height_cm=80, medium="oil") for _ in range(51)
    ]
    with pytest.raises(ValidationError):
        BatchPredictRequest(artworks=items)
