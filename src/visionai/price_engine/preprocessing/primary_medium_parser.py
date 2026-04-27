"""A 모델(1차 시장) 매체/지지체 파서 — 새 분류 시트 기반.

스펙: docs/A모델_분류재설계_step0_노트.md §4

입력: Artsy `medium` 단일 영문 free-text, Saatchi `materials` + `mediums` 분리.
출력: 계층(L1/leaf) + 다중 매체 list + 호환 컬럼(영문 8/6) + 학습 제외 플래그.

분류 시트:
- data/k-artmarket 1차 데이터 정제 - 지지체(바탕재) 분류.csv
- data/k-artmarket 1차 데이터 정제 - 도구_기법 분류.csv

참고:
- 시트는 한/영 keyword 혼합. 영문 단어는 word boundary 매칭, 한글은 substring.
- 입체 제외 4규칙 + glass/stainless 평면 override (사용자 결정 2026-04-27).
- value_grade 컬럼은 메모성 메타로만 보존 (Codex 권고, 모델 입력 X).
"""
from __future__ import annotations

import csv
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar


# ─── 시트 경로 ─────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[4]
_SUPPORT_SHEET_PATH = (
    _REPO_ROOT / "data" / "k-artmarket 1차 데이터 정제 - 지지체(바탕재) 분류.csv"
)
_TOOL_SHEET_PATH = (
    _REPO_ROOT / "data" / "k-artmarket 1차 데이터 정제 - 도구_기법 분류.csv"
)


# ─── 학습 제외 기준 (사용자 확정 2026-04-27) ────────────────────────────
EXCLUDED_SUPPORT_L1: frozenset[str] = frozenset({"금속", "플라스틱", "나무"})
"""지지체 단독 시 학습 제외 (l1 기준). '없음' = 미매칭은 별도 처리."""

EXCLUDED_TOOL_L1: frozenset[str] = frozenset({"조각", "도자", "옻칠", "목공예"})
"""도구 자체가 입체 제작 기법인 경우 (시트 l2/leaf 일부도 포함 — 보강 필요)."""

# 입체 키워드 (raw 문자열에 등장하면 sneak-in 후보)
_THREE_D_KEYWORDS_HIGH: tuple[str, ...] = (
    # 영문 (확실한 입체)
    "bronze", "porcelain", "ceramic", "stoneware", "terracotta",
    "sculpt", "carved", "carving", "installation", "figurine", "bust",
    "bas-relief", "relief sculpture",
    # 한글
    "조각", "입체", "브론즈", "청동", "도자", "세라믹", "백자", "분청", "옹기",
    "태피스트리", "tapestry",
)

# Glass/stainless: 기본 제외 + 평면 override (사용자 확정 2026-04-27)
_THREE_D_KEYWORDS_PLANAR_OVERRIDE: tuple[str, ...] = (
    "glass",
    "stainless",
)

# 평면 override 패턴: "X on glass" / "X on stainless" 형태면 평면 회화로 간주 → 포함
_PLANAR_OVERRIDE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bon\s+glass\b", re.IGNORECASE),
    re.compile(r"\bon\s+stainless(\s+steel)?\b", re.IGNORECASE),
    re.compile(r"\bpainted\s+on\s+(glass|stainless)", re.IGNORECASE),
    re.compile(r"\bscratched\s+and\s+painted\s+on\s+stainless", re.IGNORECASE),
)

# False-positive 화이트리스트 (carved/carving 키워드가 평면 작품에 사용된 경우)
# 실 Artsy 데이터 분석 (2026-04-27, 48건) 기반:
# - "carving with colors" — 평면 회화 기법 (캔버스 표면 깎기로 색 표현)
# - "carved/carving frame" — 액자만 carved, 작품은 평면
# - "carved on resin" — 레진 부속(액자 등)이 carved, 작품은 평면
# - "carving knives" — 도구 이름, 작품 형태 정보 아님
# - "carved acrylic plate" — 평면 작품의 carved 부속
_THREE_D_FALSE_POSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    # 액자 패턴 (다양한 어순)
    re.compile(r"carved\s+(\w+\s+){0,2}?frame", re.IGNORECASE),
    re.compile(r"carving\s+in\s+(wood\b|wooden\s+frame|frame\b)", re.IGNORECASE),
    re.compile(r"frame\s+on\s+(wood|resin)", re.IGNORECASE),
    # 레진 부속
    re.compile(r"carved\s+on\s+resin", re.IGNORECASE),
    # 평면 회화 기법
    re.compile(r"carving\s+with\s+colors?\b", re.IGNORECASE),
    # 도구·부품
    re.compile(r"carving\s+knives?\b", re.IGNORECASE),
    re.compile(r"carved\s+acrylic\s+plate", re.IGNORECASE),
)

# 특수 마감/가공 — primary 금지 (Codex 권고). 다른 생성 매체와 같이 나오면 secondary
_SPECIAL_FINISH_L1 = "특수 마감/가공"


# ─── 호환 매핑 (새 시트 leaf → 기존 A 영문 8 매체 / 6 지지체) ────────────
# primary_feature_builder.py:19-37 기존 라벨 호환
_TOOL_LEAF_TO_COMPAT: dict[str, str] = {
    # 유성 → oil
    "유채": "oil",
    "밀랍화": "oil",
    "오일스틱": "oil",
    "오일펜": "oil",
    "오일 파스텔": "oil",
    "콜타르": "oil",
    "파라핀": "oil",
    "에나멜": "oil",
    "스프레이": "oil",
    "카슈연필": "oil",
    # 아크릴
    "아크릴릭": "acrylic",
    # 수묵/잉크
    "수묵": "ink",
    "수묵담채": "ink",
    "잉크": "ink",
    # 채색/안료
    "채색": "pigment",
    "니금": "pigment",
    "은니": "pigment",
    "템페라": "pigment",
    "옻칠": "pigment",
    # 수성
    "수채": "watercolor",
    "과슈": "watercolor",
    # 건식/드로잉
    "연필/흑연": "pencil",
    "목탄/숯": "pencil",
    "색연필": "pencil",
    "콘테": "pencil",
    "펜/마커": "pencil",
    "초크": "pencil",
    "프로타주": "pencil",
    # 파스텔
    "파스텔": "pastel",
    # 혼합
    "혼합재료": "mixed",
    "핸드페인팅": "mixed",
    "콜라주": "mixed",
    "데콜라주": "mixed",
}

_SUPPORT_LEAF_TO_COMPAT: dict[str, str] = {
    # 섬유 대분류
    "캔버스": "canvas",
    "비단": "silk",
    "섬유": "linen",
    "태피스트리": "linen",
    # 종이 대분류
    "한지": "paper",
    "장지": "paper",
    "순지": "paper",
    "닥지": "paper",
    "칠한지": "paper",
    "종이": "paper",
    "보드": "paper",
    "트레이싱지": "paper",
    "금속지": "paper",
    "수제지": "paper",
    "인쇄물": "paper",
    "봉투": "paper",
    "부채": "paper",
    # 나무 대분류
    "패널": "panel",
    # 금속 대분류
    "스테인리스": "metal",
    "알루미늄 패널": "metal",
    "철판": "metal",
    "동판": "metal",
    # 플라스틱 / 기타 → other
}

# 영문 8 매체 (호환). primary_feature_builder.py:28-37 와 동일.
_COMPAT_MEDIUM_LABELS: tuple[str, ...] = (
    "oil", "acrylic", "ink", "watercolor", "pigment", "mixed", "pastel", "pencil", "other"
)
_COMPAT_SUPPORT_LABELS: tuple[str, ...] = (
    "canvas", "linen", "paper", "panel", "silk", "metal", "other"
)

# 매체 → 기본 지지체 (지지체 명시 없을 때 inference). B 모델 _MEDIUM_DEFAULT_SUPPORT와 동일 규칙.
_MEDIUM_L1_DEFAULT_SUPPORT: dict[str, tuple[str, str, str]] = {
    # l1 → (support_l1, support_leaf, compat)
    "판화": ("종이", "종이", "paper"),
    "사진/디지털": ("종이", "종이", "paper"),
}


# ─── 시트 룰 데이터 구조 ────────────────────────────────────────────────
@dataclass(frozen=True)
class _LeafRule:
    """시트 한 행 = 한 leaf의 매칭 룰."""
    l1: str
    l2: str
    leaf: str
    keywords: tuple[str, ...]
    value_grade: str  # 메모성 (모델 입력 X)


# ─── 결과 dataclass ────────────────────────────────────────────────────
@dataclass
class PrimaryMediumResult:
    """A 모델 매체/지지체 파싱 결과.

    호환 컬럼(`medium_category`, `support_type`)은 기존 다운스트림 보호용.
    신규 다운스트림은 `medium_l1`, `medium_leaf`, `mediums` 등을 사용.
    """
    # 호환 (기존 A 코드와 동일 라벨)
    medium_category: str = "other"
    support_type: str = "other"
    # 신규 — 시트 기반 계층
    medium_l1: str = ""
    medium_leaf: str = ""
    mediums: list[str] = field(default_factory=list)  # primary + secondary leaves
    has_multimedia: bool = False
    has_special_finish: bool = False
    support_l1: str = ""
    support_leaf: str = ""
    supports: list[str] = field(default_factory=list)
    has_multisupport: bool = False
    # 학습 제외
    is_excluded_for_training: bool = False
    exclude_reason: str | None = None  # tool_3d/support_excluded/keyword_3d/category_3d
    # 메모 (모델 입력 X)
    value_grade_note: str | None = None
    # 원본 보존
    raw: str = ""


# ─── 시트 룰 로더 (싱글톤, 첫 호출 시 lazy load) ──────────────────────────
_RULES_LOCK = threading.Lock()
_TOOL_RULES: tuple[_LeafRule, ...] | None = None
_SUPPORT_RULES: tuple[_LeafRule, ...] | None = None


def _split_keywords(kw_raw: str) -> list[str]:
    """시트 keyword 컬럼을 phrase 단위로 분할.

    영문 단어 단독 추출은 **한+영 혼합 phrase**에서만 (예: "유화 oil" → ["유화 oil", "oil"]).
    pure 영문 phrase("canvas paper", "Acrylic on canvas")는 그대로 유지 — 아니면 leaf 간
    keyword bleed 발생 (canvas paper의 canvas → 캔버스 leaf로 잘못 매칭).
    """
    parts = re.split(r"[,，/]|\s+or\s+", kw_raw)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(p)
        has_korean = bool(re.search(r"[가-힣]", p))
        has_english = bool(re.search(r"[A-Za-z]{2,}", p))
        if has_korean and has_english:
            eng_words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", p)
            for ew in eng_words:
                ew_low = ew.lower()
                # 도메인 generic 단어는 stoplist (단독 leak 방지)
                if ew_low not in {
                    "on", "and", "with", "the", "of", "from", "to", "or", "in",
                    "print", "color", "block", "type", "art",
                }:
                    out.append(ew)
    return out


# A 모델 영문 데이터용 keyword 보강 패치 (시트 sparse 보완)
# leaf 이름 → 추가 영문 keyword list
_EN_TOOL_KEYWORD_PATCHES: dict[str, list[str]] = {
    "유채": ["oil"],
    "아크릴릭": ["acrylic"],
    "수채": ["watercolor", "watercolour"],
    "과슈": ["gouache"],
    "수묵": ["ink"],   # 영문 "ink"는 수묵 우선 (잉크 leaf보다)
    "채색": ["color on", "mineral pigment"],
    "혼합재료": ["mixed media", "mixed-media"],
    "콜라주": ["collage"],
    "파스텔": ["pastel"],
    "연필/흑연": ["pencil", "graphite"],
    "목탄/숯": ["charcoal"],
    "색연필": ["colored pencil"],
    "펜/마커": ["marker"],  # "pen"은 단독 모호하므로 제외
    "지클레이 프린트": ["giclee", "giclée"],
    "디지털 피그먼트 프린트": ["pigment print", "archival pigment"],
    "디지털 프린트": ["digital print", "inkjet"],
    "젤라틴 실버 프린트": ["gelatin silver", "silver gelatin"],
    "크로모제닉 프린트": ["chromogenic", "c-print"],
    "에칭": ["etching"],
    "리노컷": ["linocut"],
    "목판": ["woodcut", "woodblock"],
    "석판": ["lithograph", "litho"],
    "실크스크린": ["silkscreen", "screenprint", "screen print", "serigraph"],
    "메조틴트": ["mezzotint"],
    "드라이포인트": ["drypoint"],
    "아쿼틴트": ["aquatint"],
    "모노타이프": ["monotype"],
    "모노프린트": ["monoprint"],
    "디아섹": ["diasec", "face-mount", "face mount"],
    "금박": ["gold leaf"],
    "은박": ["silver leaf"],
    "자수": ["embroider", "embroidered", "embroidery"],
    "각": ["scratched", "engraved"],
}

_EN_SUPPORT_KEYWORD_PATCHES: dict[str, list[str]] = {
    "캔버스": ["canvas", "linen", "hemp cloth"],
    "한지": ["korean paper", "hanji", "washi", "japanese paper"],
    "장지": ["jangji"],
    "순지": ["sunji"],
    "닥지": ["dakji"],
    "종이": ["paper"],  # 'korean paper'면 한지가 먼저 매칭 (sheet 순서)
    "보드": ["cardboard", "board"],
    "비단": ["silk"],
    "패널": ["panel", "wood panel", "wooden panel", "mdf"],
    "알루미늄 패널": ["aluminum", "aluminium"],
    "철판": ["steel"],
    "스테인리스": ["stainless steel", "stainless"],
    "동판": ["copper plate"],
    "유리": ["glass"],
    "거울": ["mirror"],
    "섬유": ["fabric", "yarn", "felt", "velvet"],  # 'cotton'은 캔버스 leaf 우선이므로 제외
    "태피스트리": ["tapestry"],
    "플라스틱 패널": ["frp", "polycarbonate"],
    "아크릴 패널": ["acrylic panel", "plexiglass"],
}

# v3 추론 모델 호환 — linen은 캔버스 leaf로 매칭되지만 호환 컬럼은 'linen' 별도 유지
# (모델 학습 시 support_factor=1.1로 별도 카테고리)
_LINEN_PATTERN = re.compile(r"\blinen\b", re.IGNORECASE)
_ON_LINEN_PATTERN = re.compile(r"\bon\s+linen\b", re.IGNORECASE)
_ON_OTHER_SUPPORT_PATTERN = re.compile(
    r"\bon\s+(canvas|panel|board|paper|silk|wood|aluminum|aluminium|stainless|glass|mirror)",
    re.IGNORECASE,
)


_CANVAS_PATTERN = re.compile(r"\bcanvas\b", re.IGNORECASE)


def _adjust_compat_for_linen(raw: str, support_compat: str, support_leaf: str) -> str:
    """raw에 'linen' 명시 + 다른 painted surface(canvas) 없을 때만 호환 라벨을 'linen'으로.

    예시:
    - 'Oil on linen' → linen만 있음 → linen ✓
    - 'PLATINUM LEAF ANIMAL GLUE LINEN ON CANVAS' → canvas 동시 언급 → canvas 유지
    - 'canvas, linen' (Saatchi) → canvas 동시 언급 → canvas 유지
    - 'Acrylic on canvas' → linen 없음 → canvas 유지
    """
    if support_compat != "canvas" or support_leaf != "캔버스":
        return support_compat
    if not raw or not _LINEN_PATTERN.search(raw):
        return support_compat
    # canvas가 raw에 동시 언급되면 canvas 유지 (mixed materials 우선)
    if _CANVAS_PATTERN.search(raw):
        return support_compat
    # 'on linen'이 명시되어 있으면 우선
    if _ON_LINEN_PATTERN.search(raw):
        return "linen"
    # linen 언급 + 다른 명시적 'on X' 없음 → linen이 유일 support
    if not _ON_OTHER_SUPPORT_PATTERN.search(raw):
        return "linen"
    return support_compat


def _load_sheet(
    path: Path,
    leaf_col: int,
    kw_col: int,
    grade_col: int | None = None,
    en_patches: dict[str, list[str]] | None = None,
) -> tuple[_LeafRule, ...]:
    """시트 파일 → _LeafRule 튜플. en_patches로 leaf별 영문 keyword 보강."""
    rules: list[_LeafRule] = []
    last_l1 = ""
    last_l2 = ""
    skip_after_blank = False
    en_patches = en_patches or {}
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    for r in rows[1:]:  # skip header
        if not r or all(not c.strip() for c in r):
            # 완전히 빈 행 — 학습 제외 안내 메타 시작 신호
            skip_after_blank = True
            continue
        if skip_after_blank:
            # 빈 행 이후 메타 (학습 제외 권장 등) → 무시
            continue
        if len(r) < max(leaf_col, kw_col) + 1:
            continue
        l1 = r[0].strip() or last_l1
        l2 = r[1].strip() if len(r) > 1 else ""
        l2 = l2 or last_l2
        leaf = r[leaf_col].strip()
        kw_raw = r[kw_col].strip() if len(r) > kw_col else ""
        grade = r[grade_col].strip() if grade_col is not None and len(r) > grade_col else ""
        if not leaf:
            continue
        # 학습 제외 메타 행 (l2가 "학습 제외 권장")은 스킵
        if "학습 제외" in l2:
            continue
        last_l1, last_l2 = l1, l2
        keywords = [leaf]
        keywords.extend(_split_keywords(kw_raw))
        # 영문 보강 패치
        keywords.extend(en_patches.get(leaf, []))
        # 중복 제거 (case-insensitive) + length desc 정렬 (longer match first)
        seen, uniq = set(), []
        for kw in keywords:
            kn = kw.lower()
            if kn and kn not in seen:
                seen.add(kn)
                uniq.append(kw)
        uniq.sort(key=lambda x: (-len(x), x))
        rules.append(_LeafRule(
            l1=l1, l2=l2, leaf=leaf,
            keywords=tuple(uniq),
            value_grade=grade,
        ))
    return tuple(rules)


def _ensure_rules() -> tuple[tuple[_LeafRule, ...], tuple[_LeafRule, ...]]:
    """첫 호출 시 시트 로드. 이후 캐시 반환."""
    global _TOOL_RULES, _SUPPORT_RULES
    if _TOOL_RULES is None or _SUPPORT_RULES is None:
        with _RULES_LOCK:
            if _SUPPORT_RULES is None:
                _SUPPORT_RULES = _load_sheet(
                    _SUPPORT_SHEET_PATH, leaf_col=2, kw_col=3,
                    en_patches=_EN_SUPPORT_KEYWORD_PATCHES,
                )
            if _TOOL_RULES is None:
                _TOOL_RULES = _load_sheet(
                    _TOOL_SHEET_PATH, leaf_col=2, kw_col=3, grade_col=4,
                    en_patches=_EN_TOOL_KEYWORD_PATCHES,
                )
    return _TOOL_RULES, _SUPPORT_RULES


# ─── 키워드 매칭 ───────────────────────────────────────────────────────
_PURE_ENG_RE = re.compile(r"[a-z][a-z\-]*$")


def _kw_matches(kw: str, text_l: str) -> bool:
    """keyword가 text_l(이미 lower) 안에 있는지.

    - pure 영문 단어(특수문자 없음): word boundary + 단복수 매칭 (\\bword s?\\b)
    - 한국어/혼합: substring 매칭
    """
    kw_l = kw.lower()
    if _PURE_ENG_RE.fullmatch(kw_l):
        return bool(re.search(r"\b" + re.escape(kw_l) + r"s?\b", text_l))
    return kw_l in text_l


def _find_first_leaf(text: str, rules: tuple[_LeafRule, ...]) -> _LeafRule | None:
    """text에 매칭되는 첫 leaf rule."""
    if not text:
        return None
    text_l = text.lower()
    for rule in rules:
        for kw in rule.keywords:
            if _kw_matches(kw, text_l):
                return rule
    return None


# 호환 우선순위 (구 SUPPORT_RULES 순서, primary_feature_builder.py:19-26 참조)
# 다중 매칭 시 painted surface 우선 — canvas가 가장 먼저, metal이 가장 나중.
_SUPPORT_COMPAT_PRIORITY: dict[str, int] = {
    "canvas": 0, "linen": 1, "paper": 2, "panel": 3, "silk": 4, "metal": 5, "other": 6,
}


def _apply_support_priority(supports: list[_LeafRule]) -> list[_LeafRule]:
    """다중 support leaf 매칭을 호환 우선순위로 재정렬.

    예시:
    - 'Acrylic, paste board, canvas on panel' → [보드(paper), 캔버스(canvas), 패널(panel)]
      → 우선순위 적용 → [캔버스, 보드, 패널] (painted surface = canvas)
    - 'Real gold leaf and acrylic on canvas on board' → [캔버스, 보드] → 캔버스 primary
    """
    return sorted(
        supports,
        key=lambda s: _SUPPORT_COMPAT_PRIORITY.get(
            _SUPPORT_LEAF_TO_COMPAT.get(s.leaf, "other"), 99,
        ),
    )


def _find_all_leaves(text: str, rules: tuple[_LeafRule, ...]) -> list[_LeafRule]:
    """text에 매칭되는 모든 leaf rule. **raw-first 정렬** (Codex 권고 Q3).

    leaf 중복 제거 + 텍스트 내 매칭 위치 오름차순 정렬.
    동일 위치(시작점) 시 시트 순서 fallback.
    """
    if not text:
        return []
    text_l = text.lower()
    seen: set[str] = set()
    found: list[tuple[int, int, _LeafRule]] = []  # (pos, sheet_idx, rule)
    for sheet_idx, rule in enumerate(rules):
        if rule.leaf in seen:
            continue
        for kw in rule.keywords:
            kw_l = kw.lower()
            pos = -1
            if _PURE_ENG_RE.fullmatch(kw_l):
                m = re.search(r"\b" + re.escape(kw_l) + r"s?\b", text_l)
                if m:
                    pos = m.start()
            elif kw_l in text_l:
                pos = text_l.find(kw_l)
            if pos >= 0:
                found.append((pos, sheet_idx, rule))
                seen.add(rule.leaf)
                break
    # raw-first: position asc, sheet_idx asc fallback
    found.sort(key=lambda t: (t[0], t[1]))
    return [r for _, _, r in found]


# ─── 입체 검출 ─────────────────────────────────────────────────────────
def _has_planar_override(text: str) -> bool:
    """glass/stainless에 대해 평면 override(예: 'on glass', 'on stainless')."""
    if not text:
        return False
    return any(p.search(text) for p in _PLANAR_OVERRIDE_PATTERNS)


def _has_3d_false_positive(text: str) -> bool:
    """'Carved frame' 등 액자만 carved인 false positive 패턴."""
    if not text:
        return False
    return any(p.search(text) for p in _THREE_D_FALSE_POSITIVE_PATTERNS)


def _has_3d_keyword(text: str) -> tuple[bool, str | None]:
    """입체 키워드 검출. (is_3d, matched_keyword) 반환.

    glass/stainless는 평면 override 없을 때만 입체로 처리.
    'Carved frame' 등은 화이트리스트 처리.
    """
    if not text:
        return False, None
    text_l = text.lower()
    # False positive 화이트리스트가 잡히면 carved 자체는 무시
    has_fp = _has_3d_false_positive(text)
    has_planar = _has_planar_override(text)

    for kw in _THREE_D_KEYWORDS_HIGH:
        if kw.lower() in text_l:
            # carved 키워드인데 'Carved frame'이면 false positive
            if has_fp and kw.lower() in {"carved", "carving"}:
                continue
            return True, kw
    for kw in _THREE_D_KEYWORDS_PLANAR_OVERRIDE:
        if re.search(r"\b" + re.escape(kw) + r"\w*", text_l):
            # 평면 override 패턴이 잡히면 입체 아님
            if has_planar:
                continue
            return True, kw
    return False, None


# ─── primary 선정 ─────────────────────────────────────────────────────
def _pick_primary_tool(found: list[_LeafRule]) -> tuple[_LeafRule | None, list[_LeafRule]]:
    """raw-first 기반 primary 선정. 마감/가공은 secondary로 강제.

    Codex 권고 (Q3, 2026-04-27): 특수 마감/가공 leaf는 다른 생성 매체가 있으면
    primary 금지. 나머지는 raw 등장 순서 = found list 순서.
    """
    if not found:
        return None, []
    finishes = [r for r in found if r.l1 == _SPECIAL_FINISH_L1]
    others = [r for r in found if r.l1 != _SPECIAL_FINISH_L1]
    if others:
        primary = others[0]
        secondary = others[1:] + finishes
        return primary, secondary
    # 마감/가공만 있는 경우 → 첫번째를 primary
    return found[0], found[1:]


# ─── 학습 제외 결정 ────────────────────────────────────────────────────
def _decide_exclusion(
    raw: str,
    support_l1: str,
    supports: list[str],
    tool_l1: str,
    category: str | None,
) -> tuple[bool, str | None]:
    """4규칙으로 학습 제외 여부 + 사유.

    1. 카테고리가 'Sculpture'/'Installation' 등 명시적 입체 → category_3d
    2. tool_l1 ∈ {조각, 도자, 옻칠, 목공예} → tool_3d
    3. raw에 입체 키워드 (glass/stainless 평면 override 적용) → keyword_3d
    4. supports 모두 ∈ {금속, 플라스틱, 나무} 또는 비어있음 → support_excluded
       (단, 평면 override 패턴 매칭 시 → 포함)
    """
    has_planar = _has_planar_override(raw)

    # 1. category 기반 (Artsy)
    if category:
        cat_low = category.lower().strip()
        if cat_low in {"sculpture", "installation", "video/film/animation", "textile arts"}:
            return True, "category_3d"
    # 2. tool 기반
    if tool_l1 in EXCLUDED_TOOL_L1:
        return True, "tool_3d"
    # 3. 키워드 기반 (glass/stainless의 평면 override는 _has_3d_keyword 안에서 처리)
    is_3d, kw = _has_3d_keyword(raw)
    if is_3d:
        return True, f"keyword_3d:{kw}"
    # 4. support 단독 기반 — 평면 override 시 면제 (예: "Acrylic on glass"는 유리 leaf
    #    keyword 미매칭이지만 평면 패턴이 있으므로 포함)
    if has_planar:
        return False, None
    if not supports:
        if raw and raw.strip():
            return True, "support_excluded"
    elif all(s in EXCLUDED_SUPPORT_L1 for s in supports):
        return True, "support_excluded"
    return False, None


# ─── public API ───────────────────────────────────────────────────────
def parse_artsy_medium(medium: str | None, category: str | None = None) -> PrimaryMediumResult:
    """Artsy 단일 영문 free-text medium 파싱.

    예시:
    - "Oil on canvas" → tool=유채(oil), support=캔버스(canvas)
    - "Acrylic on canvas, gold leaf" → primary=아크릴릭, secondary=금박, has_special_finish=1
    - "Glass, Acrylic on canvas" → 3D sneak (glass 객체 부착), exclude
    - "Acrylic on glass" → 평면 override, include
    """
    tool_rules, support_rules = _ensure_rules()
    raw = (medium or "").strip()

    if not raw:
        return PrimaryMediumResult(raw=raw)

    # leaf 매칭
    all_supports = _find_all_leaves(raw, support_rules)
    all_tools = _find_all_leaves(raw, tool_rules)

    # primary 선정 — 다중 매칭 시 호환 우선순위(canvas > linen > paper > panel > ...)
    # 적용. painted surface 우선이 v3 모델 학습 분포와 일치.
    all_supports = _apply_support_priority(all_supports)
    primary_support = all_supports[0] if all_supports else None
    primary_tool, secondary_tools = _pick_primary_tool(all_tools)

    supports_list = [s.leaf for s in all_supports]
    tools_list = []
    if primary_tool:
        tools_list.append(primary_tool.leaf)
        tools_list.extend(s.leaf for s in secondary_tools)

    # 호환 컬럼
    medium_compat = _TOOL_LEAF_TO_COMPAT.get(primary_tool.leaf, "other") if primary_tool else "other"

    # 지지체 default 매핑 (지지체 명시 없을 때)
    if primary_support:
        support_l1 = primary_support.l1
        support_leaf = primary_support.leaf
        support_compat = _SUPPORT_LEAF_TO_COMPAT.get(primary_support.leaf, "other")
    elif primary_tool and primary_tool.l1 in _MEDIUM_L1_DEFAULT_SUPPORT:
        support_l1, support_leaf, support_compat = _MEDIUM_L1_DEFAULT_SUPPORT[primary_tool.l1]
        # 명시적 지지체 없이 default 사용 — supports list는 비워둠
    else:
        support_l1 = ""
        support_leaf = ""
        support_compat = "other"

    # 호환 보정 (v3 모델은 linen을 별도 카테고리로 학습)
    support_compat = _adjust_compat_for_linen(raw, support_compat, support_leaf)

    # 특수 마감/가공 플래그
    has_special = any(r.l1 == _SPECIAL_FINISH_L1 for r in all_tools)

    # 학습 제외 결정 — default support 적용 후 supports list로 평가
    eval_supports = [s.l1 for s in all_supports] if all_supports else (
        [support_l1] if support_l1 else []
    )
    is_excl, excl_reason = _decide_exclusion(
        raw=raw,
        support_l1=support_l1,
        supports=eval_supports,
        tool_l1=primary_tool.l1 if primary_tool else "",
        category=category,
    )

    # value_grade 메모
    value_grade_note = primary_tool.value_grade if primary_tool and primary_tool.value_grade else None

    return PrimaryMediumResult(
        medium_category=medium_compat,
        support_type=support_compat,
        medium_l1=primary_tool.l1 if primary_tool else "",
        medium_leaf=primary_tool.leaf if primary_tool else "",
        mediums=tools_list,
        has_multimedia=len(tools_list) >= 2,
        has_special_finish=has_special,
        support_l1=support_l1,
        support_leaf=support_leaf,
        supports=supports_list,
        has_multisupport=len(supports_list) >= 2,
        is_excluded_for_training=is_excl,
        exclude_reason=excl_reason,
        value_grade_note=value_grade_note,
        raw=raw,
    )


def parse_saatchi_medium(
    materials: str | None,
    mediums: str | None,
    category: str | None = None,
) -> PrimaryMediumResult:
    """Saatchi materials + mediums 분리 컬럼 파싱.

    Saatchi는 이미 분리 구조 → tool은 mediums에서, support는 materials에서 매칭.
    예시:
    - materials="canvas", mediums="acrylic" → tool=아크릴릭, support=캔버스
    - materials="canvas, wood", mediums="acrylic, oil" → multi 처리
    - "other"/"" → 기타/missing
    """
    tool_rules, support_rules = _ensure_rules()
    mat_raw = (materials or "").strip()
    med_raw = (mediums or "").strip()
    raw = f"{mat_raw} | {med_raw}".strip()

    # leaf 매칭 (분리)
    all_supports = _find_all_leaves(mat_raw, support_rules)
    all_tools = _find_all_leaves(med_raw, tool_rules)

    # primary 선정 — 다중 support 매칭 시 호환 우선순위 (canvas > linen > paper > ...)
    # Saatchi materials='aluminum, canvas' 같은 케이스: canvas가 painted surface
    all_supports = _apply_support_priority(all_supports)
    primary_support = all_supports[0] if all_supports else None
    primary_tool, secondary_tools = _pick_primary_tool(all_tools)

    supports_list = [s.leaf for s in all_supports]
    tools_list = []
    if primary_tool:
        tools_list.append(primary_tool.leaf)
        tools_list.extend(s.leaf for s in secondary_tools)

    medium_compat = _TOOL_LEAF_TO_COMPAT.get(primary_tool.leaf, "other") if primary_tool else "other"

    if primary_support:
        support_l1 = primary_support.l1
        support_leaf = primary_support.leaf
        support_compat = _SUPPORT_LEAF_TO_COMPAT.get(primary_support.leaf, "other")
    elif primary_tool and primary_tool.l1 in _MEDIUM_L1_DEFAULT_SUPPORT:
        support_l1, support_leaf, support_compat = _MEDIUM_L1_DEFAULT_SUPPORT[primary_tool.l1]
    else:
        support_l1 = ""
        support_leaf = ""
        support_compat = "other"

    # 호환 보정 (v3 모델은 linen을 별도 카테고리로 학습)
    support_compat = _adjust_compat_for_linen(raw, support_compat, support_leaf)

    has_special = any(r.l1 == _SPECIAL_FINISH_L1 for r in all_tools)

    eval_supports = [s.l1 for s in all_supports] if all_supports else (
        [support_l1] if support_l1 else []
    )
    is_excl, excl_reason = _decide_exclusion(
        raw=raw,
        support_l1=support_l1,
        supports=eval_supports,
        tool_l1=primary_tool.l1 if primary_tool else "",
        category=category,
    )

    value_grade_note = primary_tool.value_grade if primary_tool and primary_tool.value_grade else None

    return PrimaryMediumResult(
        medium_category=medium_compat,
        support_type=support_compat,
        medium_l1=primary_tool.l1 if primary_tool else "",
        medium_leaf=primary_tool.leaf if primary_tool else "",
        mediums=tools_list,
        has_multimedia=len(tools_list) >= 2,
        has_special_finish=has_special,
        support_l1=support_l1,
        support_leaf=support_leaf,
        supports=supports_list,
        has_multisupport=len(supports_list) >= 2,
        is_excluded_for_training=is_excl,
        exclude_reason=excl_reason,
        value_grade_note=value_grade_note,
        raw=raw,
    )
