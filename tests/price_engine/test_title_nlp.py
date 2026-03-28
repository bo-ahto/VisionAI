"""제목 NLP 피처 테스트."""
from __future__ import annotations

import pandas as pd

from visionai.price_engine.features.title_nlp import extract_title_features


class TestSubjectClassification:
    def test_landscape(self) -> None:
        titles = pd.Series(["산수화", "풍경", "Landscape"])
        r = extract_title_features(titles)
        assert (r["title_subject"] == "landscape").all()

    def test_abstract(self) -> None:
        titles = pd.Series(["무제", "Untitled", "Abstract Composition"])
        r = extract_title_features(titles)
        assert (r["title_subject"] == "abstract").all()

    def test_other(self) -> None:
        titles = pd.Series(["루이비통 인피니", "회귀"])
        r = extract_title_features(titles)
        assert (r["title_subject"] == "other").all()

    def test_no_single_char_collision(self) -> None:
        """단일 음절 충돌 방지: '서설'은 calligraphy가 아님."""
        titles = pd.Series(["서설", "불투명", "소개"])
        r = extract_title_features(titles)
        assert (r["title_subject"] != "calligraphy").all()
        assert (r["title_subject"] != "religious").all()
        assert (r["title_subject"] != "animal").all()


class TestSeriesDetection:
    def test_ecriture(self) -> None:
        titles = pd.Series(["Ecriture No. 15", "ECRITURE N.78"])
        r = extract_title_features(titles)
        assert r["title_is_series"].all()

    def test_roman_numeral(self) -> None:
        titles = pd.Series(["작품 III", "Dialogue IV"])
        r = extract_title_features(titles)
        assert r["title_is_series"].all()

    def test_not_series(self) -> None:
        titles = pd.Series(["풍경", "미인도"])
        r = extract_title_features(titles)
        assert not r["title_is_series"].any()

    def test_sumuk_not_series(self) -> None:
        """수묵/산수는 장르이지 시리즈가 아님."""
        titles = pd.Series(["수묵화", "산수도"])
        r = extract_title_features(titles)
        assert not r["title_is_series"].any()


class TestLanguageDetection:
    def test_korean(self) -> None:
        titles = pd.Series(["풍경", "미인도"])
        r = extract_title_features(titles)
        assert r["title_is_korean"].all()
        assert not r["title_is_english"].any()

    def test_english(self) -> None:
        titles = pd.Series(["Landscape", "Abstract"])
        r = extract_title_features(titles)
        assert r["title_is_english"].all()

    def test_mixed(self) -> None:
        titles = pd.Series(["이브 Eve"])
        r = extract_title_features(titles)
        assert r["title_is_korean"].iloc[0]
        assert r["title_is_english"].iloc[0]

    def test_hanja(self) -> None:
        titles = pd.Series(["서록도 瑞鹿圖"])
        r = extract_title_features(titles)
        assert r["title_has_hanja"].iloc[0]


class TestFeatureCount:
    def test_output_columns(self) -> None:
        titles = pd.Series(["test"])
        r = extract_title_features(titles)
        expected = {
            "title_length", "title_has_year", "title_has_number",
            "title_is_untitled", "title_is_korean", "title_is_english",
            "title_has_hanja", "title_subject", "title_is_series",
        }
        assert expected.issubset(set(r.columns))
