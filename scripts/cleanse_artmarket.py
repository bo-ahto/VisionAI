"""k-artmarket 데이터 클렌징 스크립트.

docs/data_cleansing_spec.md 기반 10단계 파이프라인.
입력: k-artmarket_works_updated_s3.csv (99,593건)
출력: k-artmarket-cleansed.csv (19개 피처)

Usage:
    PYTHONPATH=src python3 scripts/cleanse_artmarket.py
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "k-artmarket 1차 데이터 정제 - k_artmarket_works_updated_s3.csv"
OUTPUT_PATH = ROOT / "data" / "k-artmarket-cleansed.csv"
HO_SIZE_PATH = ROOT / "data" / "ho_size.md"

# ─── 경매사명 정규화 ───
_HOUSE_MAP: dict[str, str] = {
    "케이": "케이옥션", "헤럴드 아트데이": "헤럴드아트데이",
    "HERALD ARTDAY AUCTION": "헤럴드아트데이", "라이즈": "라이즈아트",
    "꼬": "꼬모옥션", "마이": "마이아트옥션", "마이아": "마이아트옥션",
    "대구 신세계 문화홀 8층": "서울옥션(대구)",
    # 원본에서 auction_house가 경매명으로 잘못 입력된 경우
    "2022년 9월 183회 온라인": "에이옥션",
    "2022년 5월 9일 위클리 온라인미술품경매": "케이옥션",
    "2022년 11월 e BID 프리미엄 온라인 경매 l <오늘의 오브제>": "에이옥션",
}
_PAT_HOUSE_IN_NAME = re.compile(r"^(서울옥션|케이옥션|에이옥션|아이옥션)\s")

# ─── 한국 성씨 로마자 DB ───
_KOREAN_SURNAMES_ENG = {
    "Kim", "Lee", "Park", "Choi", "Jung", "Cho", "Kang", "Yoon", "Jang",
    "Lim", "Han", "Oh", "Seo", "Shin", "Kwon", "Hwang", "Ahn", "Song",
    "Yoo", "Hong", "Jeon", "Ko", "Moon", "Yang", "Son", "Bae", "Baek",
    "Huh", "Nam", "Ryu", "Ha", "Woo", "Kwak", "Chun", "Min", "Byun",
    "Noh", "Yi", "Rhee", "Pak", "Chung", "Jeong", "Yun", "Im", "Paik",
    "Whang", "Pyo", "Hyun", "Yoo", "Woo",
}

# ─── 일본 이름 키워드 ───
_JP_KEYWORDS = {
    "Murakami", "Kusama", "Nara", "Rokkaku", "Takashi", "Yayoi",
    "Yoshitomo", "Shiota", "Morimura", "Hokusai", "Hiroshige",
}

# ─── 호수 테이블 (ho_size.md 기반) ───
HO_F_TABLE: dict[int, tuple[float, float]] = {
    0: (18.0, 14.0), 1: (22.7, 15.8), 2: (25.8, 17.9),
    3: (27.3, 22.0), 4: (33.4, 24.2), 5: (34.8, 27.3),
    6: (40.9, 31.8), 8: (45.5, 37.9), 10: (53.0, 45.5),
    12: (60.6, 50.0), 15: (65.1, 53.0), 20: (72.7, 60.6),
    25: (80.3, 65.1), 30: (90.9, 72.7), 40: (100.0, 80.3),
    50: (116.8, 91.0), 60: (130.3, 97.0), 80: (145.5, 112.1),
    100: (162.2, 130.3), 120: (193.9, 130.3),
    150: (227.3, 181.8), 200: (259.1, 193.9),
    300: (290.9, 218.2), 500: (333.3, 248.5),
}

# F/P/M/S 전체 테이블 (정확 매칭용)
_ALL_HO_SIZES: list[tuple[int, str, float, float]] = []
_HO_P: dict[int, tuple[float, float]] = {
    1: (22.7, 14.0), 2: (25.8, 16.0), 3: (27.3, 19.0), 4: (33.4, 21.2),
    5: (34.8, 24.2), 6: (40.9, 27.3), 8: (45.5, 33.4), 10: (53.0, 40.9),
    12: (60.6, 45.5), 15: (65.1, 50.0), 20: (72.7, 53.0), 25: (80.3, 60.6),
    30: (90.9, 65.1), 40: (100.0, 72.7), 50: (116.8, 80.3), 60: (130.3, 89.4),
    80: (145.5, 97.0), 100: (162.2, 112.1), 120: (193.9, 112.1),
    150: (227.3, 162.1), 200: (259.1, 181.8), 300: (290.9, 197.0), 500: (333.3, 218.2),
}
_HO_M: dict[int, tuple[float, float]] = {
    1: (22.7, 12.0), 2: (25.8, 14.0), 3: (27.3, 16.0), 4: (33.4, 19.0),
    5: (34.8, 21.2), 6: (40.9, 24.2), 8: (45.5, 27.3), 10: (53.0, 33.4),
    12: (60.6, 40.9), 15: (65.1, 45.5), 20: (72.7, 50.0), 25: (80.3, 53.0),
    30: (90.9, 60.6), 40: (100.0, 65.1), 50: (116.8, 72.7), 60: (130.3, 80.3),
    80: (145.5, 89.4), 100: (162.2, 97.0), 120: (193.9, 97.0),
    150: (227.3, 145.5), 200: (259.1, 162.1), 300: (290.9, 181.8), 500: (333.3, 197.0),
}

for ho_num, (h, w) in HO_F_TABLE.items():
    _ALL_HO_SIZES.append((ho_num, "F", h, w))
for ho_num, (h, w) in _HO_P.items():
    _ALL_HO_SIZES.append((ho_num, "P", h, w))
for ho_num, (h, w) in _HO_M.items():
    _ALL_HO_SIZES.append((ho_num, "M", h, w))

_HO_F_KEYS = sorted(HO_F_TABLE.keys())
_HO_F_AREAS = [HO_F_TABLE[k][0] * HO_F_TABLE[k][1] for k in _HO_F_KEYS]


# 표준 호수 목록
_STANDARD_HO = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200, 300, 500]

# F/P/M/S 각 타입별 면적 테이블 (호수 → 면적)
_TYPE_TABLES = {
    "F": {k: v[0] * v[1] for k, v in HO_F_TABLE.items()},
    "P": {k: v[0] * v[1] for k, v in _HO_P.items()},
    "M": {k: v[0] * v[1] for k, v in _HO_M.items()},
}
# S형: 정사각형 — F 장변의 제곱
_TYPE_TABLES["S"] = {k: v[1] * v[1] for k, v in HO_F_TABLE.items() if k > 0}


def _snap_to_standard_ho(ho: float) -> int:
    """연속 호수값 → 가장 가까운 표준 호수로 반올림."""
    if np.isnan(ho):
        return np.nan
    diffs = [abs(ho - s) for s in _STANDARD_HO]
    return _STANDARD_HO[diffs.index(min(diffs))]


def _detect_aspect_type(w: float, h: float) -> str:
    """가로/세로 비율로 F/P/M/S 형식 추정.

    F: 장변/단변 ≈ 1.2~1.4 (인물형)
    P: 장변/단변 ≈ 1.3~1.6 (풍경형)
    M: 장변/단변 ≈ 1.5~2.0 (해경형)
    S: 장변/단변 ≈ 1.0~1.1 (정사각형)
    """
    long_side = max(w, h)
    short_side = min(w, h)
    if short_side <= 0:
        return "F"
    ratio = long_side / short_side
    if ratio <= 1.15:
        return "S"
    if ratio <= 1.35:
        return "F"
    if ratio <= 1.55:
        return "P"
    return "M"


def _area_to_ho_by_type(area: float, aspect_type: str) -> float:
    """면적 + 형식 → 해당 타입 테이블에서 가장 가까운 표준 호수."""
    if area <= 0 or not np.isfinite(area):
        return np.nan
    table = _TYPE_TABLES.get(aspect_type, _TYPE_TABLES["F"])
    keys = sorted(table.keys())
    areas = [table[k] for k in keys]
    # 보간 후 표준 호수로 snap
    ho = float(np.interp(area, areas, keys))
    return _snap_to_standard_ho(ho)


def _match_ho_exact(w: float, h: float, tol: float = 2.0) -> float | None:
    """width×height → 호수 테이블 정확 매칭 (±tol cm)."""
    best = None
    best_dist = float("inf")
    for ho_num, ho_type, th, tw in _ALL_HO_SIZES:
        d1 = abs(w - tw) + abs(h - th)
        d2 = abs(w - th) + abs(h - tw)
        d = min(d1, d2)
        if d <= tol * 2 and d < best_dist:
            best_dist = d
            best = ho_num
    return float(best) if best is not None else None


def _extract_ho(row: pd.Series) -> float:
    """행에서 환산 호수 추출.

    3단계: (1) size_raw 직접 파싱 → (2) 정확 매칭 → (3) 비율 판단 + 면적 환산
    """
    # Step 1: size_raw에서 직접 호수 파싱
    size_raw = str(row.get("size_raw", ""))
    m = re.search(r"(\d+)\s*호", size_raw)
    if m:
        return _snap_to_standard_ho(float(m.group(1)))
    m = re.search(r"(\d+)\s*([FPMSfpms])", size_raw)
    if m:
        return _snap_to_standard_ho(float(m.group(1)))

    # Step 2-3: width × height 기반
    w = pd.to_numeric(row.get("width_cm"), errors="coerce")
    h = pd.to_numeric(row.get("height_cm"), errors="coerce")
    if pd.notna(w) and pd.notna(h) and w > 0 and h > 0:
        # Step 2: 정확 매칭 (±2cm)
        exact = _match_ho_exact(w, h)
        if exact is not None:
            return exact

        # Step 3: 비율 판단 → 해당 타입 면적 테이블에서 환산
        aspect_type = _detect_aspect_type(w, h)
        area = w * h
        return _area_to_ho_by_type(area, aspect_type)

    return np.nan


def _normalize_source(house: str, auction_name: str) -> str:
    """경매사명 정규화."""
    h = str(house).strip()
    if h in _HOUSE_MAP:
        return _HOUSE_MAP[h]
    m = _PAT_HOUSE_IN_NAME.match(str(auction_name).strip())
    if m:
        return m.group(1)
    return h


def _estimate_nationality(name_kor: str | None, name_eng: str | None) -> str:
    """작가 국적 추정 (KR/JP/WS/UN)."""
    kor = str(name_kor).strip() if pd.notna(name_kor) else ""
    eng = str(name_eng).strip() if pd.notna(name_eng) else ""

    if kor == "작가미상" or (not kor and not eng):
        return "UN"

    # 영문명에서 일본 키워드
    if any(kw in eng for kw in _JP_KEYWORDS):
        return "JP"

    # 한글명 5글자+ = 외국인 음역
    if kor and len(kor.replace(" ", "")) >= 5:
        # 일본식 이름 패턴 (카타카나 음역: OO OO)
        if re.match(r"^[가-힣]{2,4}\s[가-힣]{2,4}$", kor):
            jp_kor = ["무라카미", "쿠사마", "요시토모", "나라 ", "로카쿠", "시오타"]
            if any(kw in kor for kw in jp_kor):
                return "JP"
        return "WS"

    # 영문명에서 한국 성씨
    if eng:
        parts = eng.split()
        if parts and (parts[0] in _KOREAN_SURNAMES_ENG or parts[-1] in _KOREAN_SURNAMES_ENG):
            return "KR"
        # 한국 성씨 아님 → 서양
        if len(parts) >= 2:
            return "WS"

    # 한글명 2-4글자 = 한국인
    if kor and 2 <= len(kor.replace(" ", "")) <= 4:
        return "KR"

    return "UN"


def _extract_edition(size_raw: str) -> int | None:
    """size_raw에서 에디션 번호 추출."""
    m = re.search(r"[Ee]d\.?\s*(\d+)", str(size_raw))
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)/(\d+)", str(size_raw))
    if m:
        return int(m.group(2))  # 에디션 총 수
    return None


def main() -> None:
    """10단계 클렌징 파이프라인."""
    # ─── 1. 헤더 정리 ───
    logger.info("=== Step 1: Load & fix header ===")
    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig", skiprows=1, low_memory=False,
        names=["idx", "page_index", "img_src", "img_file_name", "name_kor", "name_eng",
               "title", "materials", "size_raw", "width", "height", "unit", "ho",
               "price", "auction_name", "auction_house", "auction_date", "uci"])
    # 첫 행이 헤더 중복이면 제거
    if str(df.iloc[0]["idx"]) == "idx":
        df = df.iloc[1:]
    logger.info("Raw: %d rows", len(df))

    # ─── 2. 비미술 클렌징 ───
    logger.info("=== Step 2: Non-art cleansing ===")
    from visionai.price_engine.preprocessing.data_cleanser import classify_non_art

    cls = df.apply(
        lambda row: classify_non_art(str(row.get("title", "")), str(row.get("materials", ""))),
        axis=1,
    )
    non_art = pd.Series([r.is_non_art for r in cls], index=df.index)
    removed = non_art.sum()
    df = df[~non_art]
    logger.info("Removed %d non-art items", removed)

    # ─── 3. 가격 필터 ───
    logger.info("=== Step 3: Price filter ===")
    df["price"] = pd.to_numeric(df["price"].astype(str).str.replace(",", ""), errors="coerce")
    before = len(df)
    df = df[df["price"] > 0]
    logger.info("Removed %d with price <= 0", before - len(df))

    # ─── 4. 작가명 상호 채움 ───
    logger.info("=== Step 4: Artist name cross-fill ===")
    # 4a. 매핑 테이블 구축
    both = df[df["name_kor"].notna() & df["name_eng"].notna()]
    kor_to_eng = both.drop_duplicates("name_kor").set_index("name_kor")["name_eng"].to_dict()
    eng_to_kor = both.drop_duplicates("name_eng").set_index("name_eng")["name_kor"].to_dict()
    logger.info("Name mapping: %d kor→eng, %d eng→kor", len(kor_to_eng), len(eng_to_kor))

    # 4b. 채우기
    mask_no_kor = df["name_kor"].isna() & df["name_eng"].notna()
    df.loc[mask_no_kor, "name_kor"] = df.loc[mask_no_kor, "name_eng"].map(eng_to_kor)

    mask_no_eng = df["name_eng"].isna() & df["name_kor"].notna()
    df.loc[mask_no_eng, "name_eng"] = df.loc[mask_no_eng, "name_kor"].map(kor_to_eng)

    # 4c. 둘 다 없는 경우
    mask_none = df["name_kor"].isna() & df["name_eng"].isna()
    has_title = mask_none & df["title"].notna()
    df.loc[has_title, "name_kor"] = "작가미상"
    df.loc[has_title, "name_eng"] = "unknown"

    no_info = mask_none & df["title"].isna()
    df = df[~no_info]
    logger.info("Artist fill: %d still missing kor, %d still missing eng",
                df["name_kor"].isna().sum(), df["name_eng"].isna().sum())

    # 4d. 이름 품질 정리
    import re as _re

    # name_kor에 영문 입력 → name_eng로 복사 + name_kor에도 유지 (실제 작가)
    kor_is_eng = df["name_kor"].fillna("").apply(
        lambda x: bool(_re.match(r"^[A-Za-z\s\.\-\,]+$", x.strip())) if x.strip() and x != "작가미상" else False
    )
    if kor_is_eng.any():
        # name_eng가 비어있으면 name_kor 값을 name_eng에 복사
        no_eng = df["name_eng"].isna() | (df["name_eng"].astype(str).str.strip() == "")
        df.loc[kor_is_eng & no_eng, "name_eng"] = df.loc[kor_is_eng & no_eng, "name_kor"]
        # name_kor는 그대로 유지 (영문이지만 실제 작가명)
        logger.info("name_kor(영문)→eng 복사: %d건 (name_kor 유지)", kor_is_eng.sum())

    # name_eng에 한글 입력 → name_kor로 이동
    eng_is_kor = df["name_eng"].fillna("").apply(
        lambda x: bool(_re.search(r"[가-힣]", x)) if x.strip() and x != "unknown" else False
    )
    if eng_is_kor.any():
        df.loc[eng_is_kor & df["name_kor"].isna(), "name_kor"] = df.loc[eng_is_kor & df["name_kor"].isna(), "name_eng"]
        df.loc[eng_is_kor, "name_eng"] = "unknown"
        logger.info("name_eng→kor swap: %d건", eng_is_kor.sum())

    # "민화" → 장르지 작가 아님
    is_minhwa = df["name_kor"].fillna("") == "민화"
    df.loc[is_minhwa, "name_kor"] = "작가미상"
    df.loc[is_minhwa, "name_eng"] = "unknown"
    if is_minhwa.sum() > 0:
        logger.info("민화→작가미상: %d건", is_minhwa.sum())

    # "작자미상" → "작가미상" 통일
    df.loc[df["name_kor"].fillna("") == "작자미상", "name_kor"] = "작가미상"

    # Anonymous = 의도적 익명 → name_kor="익명", name_eng="Anonymous"
    # unknown = 정보 없음 → name_kor="작가미상", name_eng="unknown"
    is_anon = df["name_eng"].fillna("") == "Anonymous"
    df.loc[is_anon, "name_kor"] = "익명"
    # name_eng="Anonymous" 유지
    logger.info("Anonymous(익명): %d건", is_anon.sum())

    # 4e. 제목 정리: 대시+공백+줄바꿈 패턴에서 실제 제목 추출
    import re as _re2

    def _clean_title(t: str) -> str:
        if not isinstance(t, str):
            return ""
        # "-\n   \n   \n   실제제목" → "실제제목"
        cleaned = _re2.sub(r"^[-—]\s*", "", t)  # 앞 대시 제거
        cleaned = _re2.sub(r"\s+", " ", cleaned).strip()  # 연속 공백/줄바꿈 → 단일 공백
        return cleaned if cleaned else ""

    title_before = df["title"].fillna("")
    df["title"] = title_before.apply(_clean_title)
    title_fixed = (title_before != df["title"]).sum()
    logger.info("Title cleaned: %d건 정리", title_fixed)

    # 정리 후에도 빈 제목 → "무제"
    title_empty = df["title"].fillna("").str.strip() == ""
    df.loc[title_empty, "title"] = "무제"
    if title_empty.sum() > 0:
        logger.info("Title empty→무제: %d건", title_empty.sum())

    # 4f. 한쪽 이름만 있는 경우 — 원본 이름을 반대쪽에 복사
    kor_val = df["name_kor"].fillna("").astype(str).str.strip()
    eng_val = df["name_eng"].fillna("").astype(str).str.strip()

    # 한글만 있고 영문 없음 → 한글을 영문 칸에도 복사
    kor_only = (kor_val != "") & (kor_val != "작가미상") & (eng_val == "")
    df.loc[kor_only, "name_eng"] = df.loc[kor_only, "name_kor"]
    logger.info("name_eng ← name_kor 복사: %d건", kor_only.sum())

    # 영문만 있고 한글 없음 → 영문을 한글 칸에도 복사
    eng_only = (eng_val != "") & (eng_val != "unknown") & (kor_val == "")
    df.loc[eng_only, "name_kor"] = df.loc[eng_only, "name_eng"]
    logger.info("name_kor ← name_eng 복사: %d건", eng_only.sum())

    # 4g. 둘 다 없는 경우만 미상 처리
    kor_empty = df["name_kor"].isna() | (df["name_kor"].astype(str).str.strip() == "")
    eng_empty = df["name_eng"].isna() | (df["name_eng"].astype(str).str.strip() == "")
    both_empty = kor_empty & eng_empty
    df.loc[both_empty, "name_kor"] = "작가미상"
    df.loc[both_empty, "name_eng"] = "unknown"

    # 작가미상의 name_eng이 비어있으면 unknown
    is_misa = df["name_kor"] == "작가미상"
    misa_no_eng = is_misa & (df["name_eng"].isna() | (df["name_eng"].astype(str).str.strip() == ""))
    df.loc[misa_no_eng, "name_eng"] = "unknown"

    logger.info("Name final: 작가미상=%d, 빈값 kor=%d eng=%d",
                (df["name_kor"] == "작가미상").sum(),
                df["name_kor"].isna().sum(),
                df["name_eng"].isna().sum())

    # 4h. 제목 없음 + 재료/크기 있음 → "무제"
    title_na = df["title"].isna() | (df["title"].astype(str).str.strip() == "")
    has_mat = df["materials"].notna() & (df["materials"].astype(str).str.strip() != "")
    fill_title = title_na & has_mat
    df.loc[fill_title, "title"] = "무제"
    if fill_title.sum() > 0:
        logger.info("Title fill: %d → '무제'", fill_title.sum())

    # 4f. 작가명 "-" → "작가미상"/"unknown"
    dash_kor = df["name_kor"].astype(str).str.strip().isin(["-", "--", "—", ""])
    df.loc[dash_kor, "name_kor"] = "작가미상"
    dash_eng = df["name_eng"].astype(str).str.strip().isin(["-", "--", "—", ""])
    df.loc[dash_eng, "name_eng"] = "unknown"

    # ─── 5. materials 정규화 ───
    logger.info("=== Step 5: Materials classification ===")
    from visionai.price_engine.preprocessing.medium_parser import parse_medium

    parsed = df["materials"].apply(parse_medium)
    df["medium_category"] = parsed.apply(lambda r: r.medium_category)
    df["support_category"] = parsed.apply(lambda r: r.support_category)
    logger.info("Medium: %s", df["medium_category"].value_counts().head(5).to_dict())

    # ─── 6. 단위 통일 ───
    logger.info("=== Step 6: Unit conversion ===")
    df["width"] = pd.to_numeric(df["width"], errors="coerce")
    df["height"] = pd.to_numeric(df["height"], errors="coerce")
    unit = df["unit"].fillna("cm").str.strip().str.lower()
    inch_mask = unit == "in"
    m_mask = unit == "m"
    df.loc[inch_mask, "width"] = df.loc[inch_mask, "width"] * 2.54
    df.loc[inch_mask, "height"] = df.loc[inch_mask, "height"] * 2.54
    df.loc[m_mask, "width"] = df.loc[m_mask, "width"] * 100
    df.loc[m_mask, "height"] = df.loc[m_mask, "height"] * 100
    df["width_cm"] = df["width"]
    df["height_cm"] = df["height"]
    # 이상치 제거: 1000cm(10m) 초과는 데이터 오류
    size_outlier = (df["width_cm"] > 1000) | (df["height_cm"] > 1000)
    df.loc[size_outlier, ["width_cm", "height_cm"]] = np.nan
    df["surface_area"] = df["width_cm"] * df["height_cm"]
    logger.info("Unit: %d inch→cm, %d m→cm, %d size outliers nulled",
                inch_mask.sum(), m_mask.sum(), size_outlier.sum())

    # ─── 7. 호수 추출 ───
    logger.info("=== Step 7: Ho extraction ===")
    df["ho"] = df.apply(_extract_ho, axis=1)
    ho_valid = df["ho"].notna().sum()
    logger.info("Ho: %d/%d valid (%.1f%%)", ho_valid, len(df), ho_valid / len(df) * 100)

    # ─── 8. 경매사명 정규화 ───
    logger.info("=== Step 8: Source normalization ===")
    df["source"] = df.apply(
        lambda row: _normalize_source(
            str(row.get("auction_house", "")), str(row.get("auction_name", "")),
        ), axis=1,
    )
    logger.info("Sources: %s", df["source"].value_counts().head(5).to_dict())

    # ─── 9. 파생 피처 ───
    logger.info("=== Step 9: Derived features ===")
    df["artist_nationality"] = df.apply(
        lambda row: _estimate_nationality(row.get("name_kor"), row.get("name_eng")),
        axis=1,
    )
    df["edition_number"] = df["size_raw"].apply(_extract_edition)
    logger.info("Nationality: %s", df["artist_nationality"].value_counts().to_dict())
    logger.info("Edition: %d with edition number", df["edition_number"].notna().sum())

    # img_file_name: S3 URL 보존, 없으면 img_src에서 생성
    mask_no_img = df["img_file_name"].isna() | (df["img_file_name"].astype(str).str.strip() == "")
    if mask_no_img.any():
        def _img_src_to_s3(src: str) -> str:
            m = re.search(r"fileId=(FILE_ID\d+)", str(src))
            if m:
                return f"https://nant-art-database.s3.ap-northeast-2.amazonaws.com/k_artmarket/{m.group(1)}.jpg"
            return ""
        df.loc[mask_no_img, "img_file_name"] = df.loc[mask_no_img, "img_src"].apply(_img_src_to_s3)

    # ─── 10. idx 재부여 + 중복 제거 ───
    logger.info("=== Step 10: Reindex + dedup ===")
    before = len(df)
    # uci + sale_date + price로 중복 판정 (같은 작품이 다른 날짜/가격이면 재출품 → 보존)
    df["_dedup_key"] = (
        df["uci"].fillna("") + "|"
        + df["auction_date"].fillna("") + "|"
        + df["price"].astype(str)
    )
    df = df.drop_duplicates(subset=["_dedup_key"], keep="first")
    df = df.drop(columns=["_dedup_key"])
    logger.info("Dedup by uci+date+price: %d → %d (-%d)", before, len(df), before - len(df))

    df["year_created"] = ""
    df["sale_date"] = df["auction_date"]

    # 출력 컬럼 선택
    out_cols = [
        "img_file_name", "name_kor", "name_eng", "title", "materials",
        "ho", "price", "source", "sale_date", "year_created", "uci",
        "medium_category", "support_category", "width_cm", "height_cm",
        "surface_area", "artist_nationality", "edition_number",
    ]
    out = df[out_cols].reset_index(drop=True)
    out.insert(0, "idx", range(len(out)))

    # 수치 피처 소수점 정리 + 크기 없는 작품 -1 표기
    out["width_cm"] = out["width_cm"].round(1).fillna(-1)
    out["height_cm"] = out["height_cm"].round(1).fillna(-1)
    out["surface_area"] = out["surface_area"].round(1).fillna(-1)
    out["ho"] = out["ho"].round(1).fillna(-1)
    out["price"] = out["price"].astype("Int64")  # 정수 (NaN 허용)

    # 저장
    out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    logger.info("=" * 60)
    logger.info("Saved: %s (%d rows, %d columns)", OUTPUT_PATH, len(out), len(out.columns))
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
