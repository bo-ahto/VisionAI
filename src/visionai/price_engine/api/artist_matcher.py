"""학습 작가 fuzzy 매칭.

NOTE (Codex 4차 P2, 2026-04-28): warm 라우팅 기준이 학습/CV와 정렬되려면
DB의 artists.training_count 값이 학습 데이터(is_excluded_for_training=0 적용 후)
의 row count와 일치해야 한다. 현재 DB 값이 raw count (필터 전)면, 입체 985건 제외로
인해 32명 작가가 미스라우팅 가능 (필터 전 ≥5, 필터 후 <5). 데이터 파이프라인에서
artists.training_count를 학습 직전 데이터 기준으로 동기화해야 함.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz


@dataclass
class MatchResult:
    artist_id: int
    name: str
    score: float
    training_count: int
    source: str
    profile: dict
    slug: str = ""  # artsy_slug 또는 saatchi_id (가격 이력 조회용)


def normalize_name(name: str) -> str:
    """이름을 매칭용으로 정규화."""
    return re.sub(r"\s+", " ", str(name).lower().strip())


def build_variants(name: str) -> list[str]:
    """작가명에서 매칭 가능한 변형 목록 생성."""
    parts = str(name).split()
    kor = [p for p in parts if any("\uac00" <= c <= "\ud7a3" for c in p)]
    eng = [p for p in parts if p.strip() and all(c.isascii() for c in p)]

    variants = {normalize_name(name)}
    if eng:
        eng_lower = " ".join(eng).lower()
        variants.add(eng_lower)
        if len(eng) >= 2:
            variants.add(" ".join(reversed(eng)).lower())
    if kor:
        variants.add(" ".join(kor))
        variants.add("".join(kor))

    return [v for v in variants if len(v) >= 2]


class ArtistMatcher:
    """인메모리 작가 매칭 엔진."""

    def __init__(self) -> None:
        self._index: dict[str, dict] = {}  # normalized_name → artist info
        self._all_names: list[str] = []

    def load_from_data(self, artists: list[dict], profiles: list[dict]) -> None:
        """artists + profiles 데이터로 인덱스 구축."""
        # profiles를 artist_id로 매핑
        profile_map: dict[int, dict] = {}
        for p in profiles:
            aid = p.get("artist_id")
            if aid is not None:
                profile_map[int(aid)] = p

        for a in artists:
            aid = int(a["id"])
            name = a.get("name", "")
            profile = profile_map.get(aid, {})

            info = {
                "id": aid,
                "name": name,
                "slug": a.get("artsy_slug") or str(a.get("saatchi_id") or aid),
                "training_count": a.get("training_count", 0) or 0,
                "source": a.get("source", ""),
                "is_in_training": a.get("is_in_training", False),
                "birth_year": a.get("birth_year") or profile.get("birth_year_from_source"),
                "profile": {
                    "birth_year": a.get("birth_year") or profile.get("birth_year_from_source"),
                    "birth_year_from_source": profile.get("birth_year_from_source"),
                    "total_works": profile.get("total_works", 0) or 0,
                    "followers": profile.get("followers", 0) or 0,
                    "solo_count": profile.get("solo_count", 0) or 0,
                    "group_count": profile.get("group_count", 0) or 0,
                    "fair_count": profile.get("fair_count", 0) or 0,
                    "career_stage": profile.get("career_stage", 1) or 1,
                    "career_age": 0,
                    "for_sale_ratio": 1.0,
                    "profile_completeness": profile.get("profile_completeness", 0) or 0,
                    "gallery_name": "Saatchi Art" if a.get("source") == "saatchi" else "Gallery",
                    "gallery_type": "Online Gallery" if a.get("source") == "saatchi" else "Gallery",
                    "gallery_tier": 3,
                    "source": a.get("source", "manual"),
                },
            }

            # 이름 변형 등록
            variants = build_variants(name)
            for v in variants:
                if v not in self._index or info["training_count"] > self._index[v].get("training_count", 0):
                    self._index[v] = info

        self._all_names = list(self._index.keys())

    def match(self, query_name: str) -> MatchResult | None:
        """작가명으로 매칭. 정확 → fuzzy 순서."""
        variants = build_variants(query_name)

        # 1. 정확 매칭
        for v in variants:
            if v in self._index:
                info = self._index[v]
                return MatchResult(
                    artist_id=info["id"], name=info["name"], score=100.0,
                    training_count=info["training_count"], source=info["source"],
                    profile=info["profile"], slug=info.get("slug", ""),
                )

        # 2. Fuzzy 매칭 (0.85+)
        best_score = 0.0
        best_key = None
        query_norm = normalize_name(query_name)

        for key in self._all_names:
            score = fuzz.ratio(query_norm, key)
            if score > best_score:
                best_score = score
                best_key = key

        if best_score >= 85 and best_key:
            info = self._index[best_key]
            return MatchResult(
                artist_id=info["id"], name=info["name"], score=best_score,
                training_count=info["training_count"], source=info["source"],
                profile=info["profile"], slug=info.get("slug", ""),
            )

        return None

    @property
    def count(self) -> int:
        return len(set(info["id"] for info in self._index.values()))
