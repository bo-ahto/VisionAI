"""재료 문자열 파싱 모듈.

17종 매체 + 8종 지지체로 정규화한다.
한국어 약어(지본/견본) 풀기 + 영문 소문자 통일 후 분류.

기획서 참조: docs/data_cleansing_spec.md Section 3
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class MediumResult:
    """재료 파싱 결과."""

    medium_category: str
    support_category: str


# ─── 한국어 약어 → 풀어쓰기 ───
_ABBREVIATIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^지본"), "종이에 "),
    (re.compile(r"^견본"), "비단에 "),
    (re.compile(r"^마본"), "마포에 "),
    (re.compile(r"^면본"), "면에 "),
]


# ─── 매체 분류 규칙 (17개, 우선순위 순) ───
_MEDIUM_RULES: list[tuple[re.Pattern[str], str]] = [
    # 유화 (최우선)
    (re.compile(r"유채|오일|oil\b", re.IGNORECASE), "유화"),
    # 아크릴
    (re.compile(r"아크릴|acrylic", re.IGNORECASE), "아크릴"),
    # 수채/과슈
    (re.compile(r"수채|watercolor|과슈|gouache|aquarelle", re.IGNORECASE), "수채"),
    # 수묵
    (re.compile(
        r"수묵|먹|묵서|묵|ink(?!\s*jet)",
        re.IGNORECASE,
    ), "수묵"),
    # 채색
    (re.compile(r"채색|담채|color on|분채|암채|석채|금니", re.IGNORECASE), "채색"),
    # 연필/드로잉
    (re.compile(
        r"연필|pencil|색연필|colored pencil|콩테|conte|파스텔|pastel|"
        r"목탄|charcoal|숯|크레용|crayon|그라파이트|graphite|흑연|"
        r"볼펜|ballpoint|마커|marker|펜\b|pen\b|사인펜|드로잉|drawing",
        re.IGNORECASE,
    ), "연필/드로잉"),
    # 판화 (에칭, 목판, 메조틴트 등)
    (re.compile(
        r"석판화|lithograph|에칭|etching|목판화|woodcut|woodblock|"
        r"메조틴트|mezzotint|드라이포인트|drypoint|아쿼틴트|aquatint|"
        r"콜라그래프|collagraph|믹소그라피|monotype|리노컷|linocut|"
        r"판화|포토그라비어|photogravure",
        re.IGNORECASE,
    ), "판화"),
    # 실크스크린 (판화와 별도)
    (re.compile(
        r"실크스크린|silkscreen|스크린프린트|screenprint|스크린\s*프린트|"
        r"세리그라프|serigraph|세리그래프",
        re.IGNORECASE,
    ), "실크스크린"),
    # 사진/디지털 (인쇄/복제보다 먼저 — C-프린트, 디지털 프린트 등)
    (re.compile(
        r"사진|c-print|C-프린트|디지털|digital|피그먼트|젤라틴|"
        r"photograph|lambda|람다|크로모제닉",
        re.IGNORECASE,
    ), "사진/디지털"),
    # 인쇄/복제
    (re.compile(
        r"오프셋|offset|인쇄\b|프린트$|포스터|렌티큘러|lenticular|"
        r"지클레이|giclee|지클레\b|잉크젯|inkjet",
        re.IGNORECASE,
    ), "인쇄/복제"),
    # 혼합재료 (+콜라주)
    (re.compile(r"혼합|mixed|콜라주|collage", re.IGNORECASE), "혼합재료"),
    # 조각
    (re.compile(
        r"브론즈|bronze|청동|대리석|marble|화강암|granite|"
        r"레진|resin|캐스트|cast|carved|폴리스톤|polystone|"
        r"스테인리스|stainless|알루미늄|aluminum|aluminium|PVC|vinyl",
        re.IGNORECASE,
    ), "조각"),
    # 도자
    (re.compile(
        r"도자|자기|ceramic|porcelain|백자|세라믹|stoneware|terracotta|테라코타",
        re.IGNORECASE,
    ), "도자"),
    # 옻칠/래커
    (re.compile(r"옻칠|lacquer|urushi|나전|칠기|칠보", re.IGNORECASE), "옻칠/래커"),
    # 목공예
    (re.compile(
        r"^소나무$|^오동나무$|^괴목$|^은행나무$|^참나무$|^느티나무$|^먹감나무$|"
        r"^흑단$|^화류목$|^배나무$|^대나무$|^월넛$|^피나무$|^추자나무$|"
        r"나무에\s*(각|서각|금속)|painting on wood",
        re.IGNORECASE,
    ), "목공예"),
    # 섬유
    (re.compile(
        r"자수|embroidery|타피스트리|tapestry|직물|fabric|needlework|"
        r"섬유|fiber|sewing",
        re.IGNORECASE,
    ), "섬유"),
]


# ─── 지지체 분류 규칙 (8개) ───
_SUPPORT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"캔버스|canvas|린넨|linen", re.IGNORECASE), "캔버스"),
    (re.compile(r"종이|paper|지본|한지|Korean paper|장지|순지", re.IGNORECASE), "종이"),
    (re.compile(r"비단|(?<!screen)silk(?!screen)|견본|견\b", re.IGNORECASE), "비단"),
    (re.compile(r"목재|wood|나무|패널|panel|보드|board", re.IGNORECASE), "목재"),
    (re.compile(
        r"금속|알루미늄|aluminum|aluminium|철\b|iron|steel|스틸|놋쇠|주석",
        re.IGNORECASE,
    ), "금속"),
    (re.compile(r"면\b|cotton|마포|광목|패브릭|fabric|천\b", re.IGNORECASE), "섬유"),
]

# 매체 → 기본 지지체 매핑 (명시적 지지체 없을 때)
_MEDIUM_DEFAULT_SUPPORT: dict[str, str] = {
    "판화": "종이",
    "실크스크린": "종이",
    "인쇄/복제": "종이",
    "조각": "없음",
    "도자": "없음",
    "목공예": "없음",
}


def parse_medium(raw: str | None) -> MediumResult:
    """재료 문자열을 매체/지지체로 분류한다.

    1. 한국어 약어 풀기 (지본→종이에, 견본→비단에)
    2. 영문 소문자 통일
    3. 17개 매체 분류
    4. 8개 지지체 분류 (없으면 매체 기본값)

    Args:
        raw: 원본 재료 문자열.

    Returns:
        MediumResult with medium_category and support_category.
    """
    if not raw or not isinstance(raw, str) or raw.strip() == "":
        return MediumResult(medium_category="unknown", support_category="unknown")

    text = raw.strip()

    # NaN 문자열 처리
    if text.lower() == "nan":
        return MediumResult(medium_category="unknown", support_category="unknown")

    # Step 1: 한국어 약어 풀기
    for pattern, replacement in _ABBREVIATIONS:
        text = pattern.sub(replacement, text)

    # Step 2: (영문 매칭은 re.IGNORECASE로 처리)

    # Step 3: 매체 분류
    medium = "기타"
    for pattern, category in _MEDIUM_RULES:
        if pattern.search(text):
            medium = category
            break

    # Step 4: 지지체 분류
    support = "기타"
    for pattern, category in _SUPPORT_RULES:
        if pattern.search(text):
            support = category
            break

    # 지지체 미매칭("기타") 또는 매체와 지지체가 동일 소재일 때 기본값 적용
    if support in ("기타", "목재") and medium in _MEDIUM_DEFAULT_SUPPORT:
        support = _MEDIUM_DEFAULT_SUPPORT[medium]

    return MediumResult(medium_category=medium, support_category=support)
