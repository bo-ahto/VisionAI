"""Test suite for primary_medium_parser (A model 1차 시장 파서)."""
from __future__ import annotations

import pytest

from visionai.price_engine.preprocessing.primary_medium_parser import (
    parse_artsy_medium,
    parse_saatchi_medium,
)


# ─── Artsy: 단일 매체 기본 케이스 ─────────────────────────────────────────
@pytest.mark.parametrize(
    "medium,exp_l1,exp_leaf,exp_compat_med,exp_compat_sup",
    [
        ("Oil on canvas", "회화/드로잉", "유채", "oil", "canvas"),
        ("Acrylic on canvas", "회화/드로잉", "아크릴릭", "acrylic", "canvas"),
        ("Watercolor on paper", "회화/드로잉", "수채", "watercolor", "paper"),
        ("Ink on Korean paper", "회화/드로잉", "수묵", "ink", "paper"),
        ("Color on Korean paper", "회화/드로잉", "채색", "pigment", "paper"),
        ("Pencil on paper", "회화/드로잉", "연필/흑연", "pencil", "paper"),
        ("Charcoal on paper", "회화/드로잉", "목탄/숯", "pencil", "paper"),
        ("Gouache on paper", "회화/드로잉", "과슈", "watercolor", "paper"),
        ("Mixed media on canvas", "혼합 매체", "혼합재료", "mixed", "canvas"),
    ],
)
def test_artsy_single_medium(medium, exp_l1, exp_leaf, exp_compat_med, exp_compat_sup):
    r = parse_artsy_medium(medium, "Painting")
    assert r.medium_l1 == exp_l1
    assert r.medium_leaf == exp_leaf
    assert r.medium_category == exp_compat_med
    assert r.support_type == exp_compat_sup
    assert r.is_excluded_for_training is False


# ─── Artsy: 다중 매체 raw-first ────────────────────────────────────────
def test_artsy_multi_medium_raw_first():
    """raw 등장 순서가 primary 결정. (Codex Q3 권고)"""
    r1 = parse_artsy_medium("Acrylic and oil on canvas", "Painting")
    assert r1.medium_leaf == "아크릴릭"
    assert r1.mediums[0] == "아크릴릭"
    assert "유채" in r1.mediums

    r2 = parse_artsy_medium("Oil and acrylic on canvas", "Painting")
    assert r2.medium_leaf == "유채"
    assert r2.mediums[0] == "유채"
    assert r2.has_multimedia is True


# ─── Artsy: 특수 마감/가공은 secondary 강제 ─────────────────────────────
def test_artsy_special_finish_secondary():
    """디아섹·금박 등 마감/가공 leaf는 다른 매체 있으면 primary 금지."""
    r = parse_artsy_medium("Acrylic on canvas, gold leaf", "Painting")
    assert r.medium_leaf == "아크릴릭"  # not 금박
    assert r.has_special_finish is True
    assert "금박" in r.mediums


def test_artsy_diasec():
    r = parse_artsy_medium("Pigment print, diasec", "Photography")
    # category=Photography is in 3D set... but it's actually planar print.
    # 본 PR 범위에서 Photography는 학습 제외 카테고리 아님.
    assert r.has_special_finish is True
    assert "디아섹" in r.mediums


# ─── 입체 제외 4규칙 ──────────────────────────────────────────────────
def test_excluded_by_category_sculpture():
    r = parse_artsy_medium("Bronze", "Sculpture")
    assert r.is_excluded_for_training is True
    assert r.exclude_reason == "category_3d"


def test_excluded_by_category_installation():
    r = parse_artsy_medium("Mixed media", "Installation")
    assert r.is_excluded_for_training is True
    assert r.exclude_reason == "category_3d"


def test_excluded_by_keyword_bronze():
    r = parse_artsy_medium("Bronze sculpture on wood", "Painting")
    assert r.is_excluded_for_training is True
    assert "keyword_3d" in r.exclude_reason


def test_excluded_by_keyword_porcelain():
    r = parse_artsy_medium("Porcelain, acrylic on canvas", "Painting")
    assert r.is_excluded_for_training is True
    assert "keyword_3d" in r.exclude_reason
    assert "porcelain" in r.exclude_reason.lower()


def test_excluded_by_keyword_ceramic():
    r = parse_artsy_medium("Ceramic, mixed media", "Painting")
    assert r.is_excluded_for_training is True


def test_excluded_by_support_wood_alone():
    """지지체 '나무 패널' 단독 + 도구 없음 → 학습 제외 (사용자 결정)."""
    r = parse_artsy_medium("Wood panel", "Painting")
    assert r.is_excluded_for_training is True
    assert r.exclude_reason == "support_excluded"


def test_excluded_by_support_metal_with_planar_tool():
    """지지체 금속 + 평면 도구도 제외 (사용자 결정 2)."""
    r = parse_artsy_medium("Aluminum panel with oil", "Painting")
    assert r.is_excluded_for_training is True


# ─── glass / stainless 평면 override (사용자 결정 3) ───────────────────
def test_planar_override_acrylic_on_glass():
    """'Acrylic on glass'는 유리에 회화 = 평면 → 포함."""
    r = parse_artsy_medium("Acrylic on glass", "Painting")
    assert r.is_excluded_for_training is False


def test_glass_3d_when_object_attached():
    """'Glass, Acrylic on canvas'는 유리 객체 부착 = 3D → 제외."""
    r = parse_artsy_medium("Glass, Acrylic on canvas", "Painting")
    assert r.is_excluded_for_training is True
    assert "glass" in r.exclude_reason.lower()


def test_stainless_steel_3d_when_object_attached():
    r = parse_artsy_medium("Stainless steel on canvas", "Painting")
    assert r.is_excluded_for_training is True
    assert "stainless" in r.exclude_reason.lower()


def test_planar_override_painted_on_stainless_steel():
    r = parse_artsy_medium("Scratched and painted on stainless steel", "Painting")
    assert r.is_excluded_for_training is False


# ─── False positive 화이트리스트 ────────────────────────────────────────
def test_carved_frame_whitelist():
    """'Carved frame'은 액자만 carved이므로 작품은 평면 → 포함."""
    r = parse_artsy_medium("Oil on canvas, Carved frame on wood", "Painting")
    assert r.is_excluded_for_training is False
    assert r.medium_leaf == "유채"


def test_carved_frame_resin_whitelist():
    r = parse_artsy_medium("Oil on canvas, Carved frame on resin", "Painting")
    assert r.is_excluded_for_training is False


# ─── Saatchi: 분리 컬럼 ───────────────────────────────────────────────
@pytest.mark.parametrize(
    "materials,mediums,exp_med_leaf,exp_sup_leaf",
    [
        ("canvas", "acrylic", "아크릴릭", "캔버스"),
        ("canvas", "oil", "유채", "캔버스"),
        ("paper", "watercolor", "수채", "종이"),
        ("paper", "ink", "수묵", "종이"),
        ("linen", "oil", "유채", "캔버스"),
    ],
)
def test_saatchi_basic(materials, mediums, exp_med_leaf, exp_sup_leaf):
    r = parse_saatchi_medium(materials, mediums, "painting")
    assert r.medium_leaf == exp_med_leaf
    assert r.support_leaf == exp_sup_leaf
    assert r.is_excluded_for_training is False


def test_saatchi_multi_medium_raw_first():
    r1 = parse_saatchi_medium("canvas", "acrylic, oil", "painting")
    assert r1.medium_leaf == "아크릴릭"
    assert r1.mediums == ["아크릴릭", "유채"]

    r2 = parse_saatchi_medium("canvas", "oil, acrylic", "painting")
    assert r2.medium_leaf == "유채"


def test_saatchi_other_excluded():
    """materials='other' + mediums='other' → support 미매칭, 학습 제외."""
    r = parse_saatchi_medium("other", "other", "painting")
    assert r.is_excluded_for_training is True


def test_saatchi_sculpture_category():
    r = parse_saatchi_medium("wood", "carved", "sculpture")
    assert r.is_excluded_for_training is True
    assert r.exclude_reason == "category_3d"


def test_saatchi_stainless_steel_excluded():
    """Saatchi materials='stainless steel' + mediums='oil' — '평면 override' 패턴 없으므로 제외."""
    r = parse_saatchi_medium("stainless steel", "oil", "painting")
    assert r.is_excluded_for_training is True


# ─── Default support (매체 기반 지지체 inference) ───────────────────────
def test_default_support_for_print():
    """판화 매체인데 지지체 명시 없으면 종이 default."""
    r = parse_artsy_medium("Lithograph", "Print")
    assert r.medium_l1 == "판화"
    assert r.support_l1 == "종이"
    assert r.support_type == "paper"
    assert r.is_excluded_for_training is False


def test_default_support_for_pigment_print():
    r = parse_artsy_medium("Archival pigment print", "Painting")
    assert r.medium_l1 == "사진/디지털"
    assert r.support_l1 == "종이"
    assert r.is_excluded_for_training is False


# ─── 호환 컬럼 ─────────────────────────────────────────────────────────
def test_compat_columns_unchanged():
    """기존 다운스트림이 사용하는 영문 8/6 라벨이 유지되는지."""
    r = parse_artsy_medium("Oil on canvas", "Painting")
    assert r.medium_category in ("oil", "acrylic", "ink", "watercolor", "pigment", "mixed", "pastel", "pencil", "other")
    assert r.support_type in ("canvas", "linen", "paper", "panel", "silk", "metal", "other")


# ─── 빈 입력 ──────────────────────────────────────────────────────────
def test_empty_artsy():
    r = parse_artsy_medium(None, None)
    assert r.medium_leaf == ""
    assert r.support_leaf == ""
    assert r.is_excluded_for_training is False  # raw 비어있으면 제외 사유 없음


def test_empty_saatchi():
    r = parse_saatchi_medium(None, None, "painting")
    assert r.medium_leaf == ""


# ─── value_grade note (모델 입력 X, 메모만) ──────────────────────────────
def test_value_grade_preserved():
    r = parse_artsy_medium("Mezzotint", "Print")
    assert r.medium_leaf == "메조틴트"
    # 시트의 메조틴트 가치등급 = "S"
    assert r.value_grade_note == "S"


# ─── leaf 보존 (한지/장지/캔버스 등) ──────────────────────────────────────
def test_leaf_preservation_korean_paper():
    """한지 leaf가 종이 leaf보다 먼저 매칭."""
    r = parse_artsy_medium("Color on Korean paper", "Painting")
    assert r.support_leaf == "한지"
    assert r.support_l1 == "종이"


def test_leaf_preservation_canvas():
    r = parse_artsy_medium("Oil on canvas", "Painting")
    assert r.support_leaf == "캔버스"
    assert r.support_l1 == "섬유"


def test_leaf_preservation_panel():
    r = parse_artsy_medium("Oil on panel", "Painting")
    # 패널 leaf l1 = 나무
    assert r.support_leaf == "패널"
    # 사용자 결정: 나무 단독 = 제외
    assert r.is_excluded_for_training is True
