"""통합 데이터 스키마 및 출처별 변환기.

다중 경매사·갤러리 데이터를 단일 스키마로 통합한다.
모든 파이프라인 코드는 이 스키마의 컬럼명을 사용한다.

통합 스키마 컬럼:
  - artist: 작가명
  - title: 작품 제목
  - material: 재료
  - size_raw: 크기 원본 문자열
  - price: 판매/낙찰가 (원화, int)
  - sale_date: 판매일 (YYYY-MM-DD)
  - source: 출처명 (경매사명/갤러리명)
  - source_type: "auction" / "gallery"
  - status: "sold" / "unsold" / "withdrawn"
  - year_created: 제작연도 (문자열, 없으면 "")
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── 통합 스키마 컬럼 ───
SCHEMA_COLS = [
    "artist", "title", "material", "size_raw", "price",
    "sale_date", "source", "source_type", "status", "year_created",
]

# ─── 상태값 정규화 ───
_STATUS_SOLD = {"낙찰", "sold", "Sold"}
_STATUS_UNSOLD = {"유찰", "패스", "미낙찰", "부매", "응찰없음", "Passed", "Bought-in", "unsold"}
_STATUS_WITHDRAWN = {"철회", "withdrawn", "Withdrawn"}


def normalize_status(raw: str | None, price: float | None = None) -> str:
    """상태값을 sold/unsold/withdrawn으로 정규화."""
    if raw and isinstance(raw, str):
        s = raw.strip()
        if s in _STATUS_SOLD:
            return "sold"
        if s in _STATUS_UNSOLD:
            return "unsold"
        if s in _STATUS_WITHDRAWN:
            return "withdrawn"
    # 가격이 있으면 sold로 간주
    if price is not None and price > 0:
        return "sold"
    return "unsold"


# ─── 경매사명 정규화 ───
_HOUSE_NORMALIZE: dict[str, str] = {
    "케이": "케이옥션",
    "헤럴드 아트데이": "헤럴드아트데이",
    "HERALD ARTDAY AUCTION": "헤럴드아트데이",
    "라이즈": "라이즈아트",
    "꼬": "꼬모옥션",
    "마이": "마이아트옥션",
    "마이아": "마이아트옥션",
    "대구 신세계 문화홀 8층": "기타",
}

_PAT_HOUSE_IN_NAME = re.compile(
    r"^(서울옥션|케이옥션|에이옥션|아이옥션)\s",
)


def _normalize_auction_house(house: str, auction_name: str = "") -> str:
    """경매사명을 정규화."""
    h = house.strip()
    if h in _HOUSE_NORMALIZE:
        return _HOUSE_NORMALIZE[h]
    m = _PAT_HOUSE_IN_NAME.match(auction_name.strip())
    if m:
        return m.group(1)
    return h


def _extract_source_type(auction_name: str, source: str) -> str:
    """출처 타입(auction/gallery) 추정."""
    name = str(auction_name).lower()
    if any(kw in name for kw in ["갤러리", "gallery", "아트페어", "art fair"]):
        return "gallery"
    return "auction"


# ─── K-Auction CSV → 통합 스키마 ───

def convert_kauction(
    path: str | Path,
    artmarket_path: str | Path | None = None,
) -> pd.DataFrame:
    """K-Auction CSV를 통합 스키마로 변환.

    K-Auction 원본에 날짜가 없으므로, artmarket_path가 제공되면
    k-artmarket 케이옥션 데이터와 매칭하여 실제 날짜를 유추한다.
    """
    logger.info("Loading K-Auction: %s", path)
    df = pd.read_csv(path, encoding="utf-8-sig")
    logger.info("K-Auction raw: %d rows", len(df))

    price = pd.to_numeric(df["낙찰가"], errors="coerce").fillna(0).astype(int)

    out = pd.DataFrame({
        "artist": df["작가"].fillna(""),
        "title": df["제목"].fillna(""),
        "material": df["재료"].fillna(""),
        "size_raw": df["크기"].fillna(""),
        "price": price,
        "sale_date": "",
        "source": "케이옥션",
        "source_type": "auction",
        "status": df.apply(
            lambda row: normalize_status(
                str(row.get("상태", "")), price[row.name],
            ),
            axis=1,
        ),
        "year_created": df["제작연도"].fillna("").astype(str),
    })

    # K-Auction 회차 → 실제 날짜 유추 (k-artmarket 케이옥션 매칭)
    if "회차" in df.columns and "타입" in df.columns and artmarket_path:
        out["sale_date"] = _infer_kauction_dates(df, artmarket_path)
    elif "회차" in df.columns:
        # artmarket 없으면 회차 순서 기반 균등 날짜 생성 (fallback)
        base = pd.Timestamp("2019-01-01")
        end = pd.Timestamp("2025-06-30")
        total_days = (end - base).days
        max_session = df["회차"].max()
        out["sale_date"] = df["회차"].apply(
            lambda x: (base + pd.Timedelta(days=int(x / max_session * total_days))
                       ).strftime("%Y-%m-%d") if pd.notna(x) else ""
        )

    return out


def _infer_kauction_dates(
    kauction_df: pd.DataFrame,
    artmarket_path: str | Path,
) -> pd.Series:
    """k-artmarket 케이옥션 데이터로부터 타입+회차별 실제 날짜를 유추."""
    am = pd.read_csv(artmarket_path, encoding="utf-8-sig")
    ka = am[am["auction_house"].str.contains("케이옥션", na=False)].copy()

    if ka.empty:
        logger.warning("No K-Auction data in artmarket for date inference")
        return pd.Series("", index=kauction_df.index)

    # 작가+제목+가격으로 매칭 (제목 중복 회차 충돌 방지 — 코덱스 P1 2026-04-18)
    # 작가|제목만 쓰면 "김환기|무제" 등 반복 제목이 여러 회차에 걸쳐 동일 key로 묶여
    # 잘못된 날짜로 매칭됨. 가격을 포함해 구체적 판매 행 단위로 매칭.
    # 가격 컬럼은 데이터셋에 따라 price/price_krw/낙찰가로 다름 → 자동 감지.
    kauction_df = kauction_df.copy()
    _ka_price_col = next(
        (c for c in ["price", "price_krw", "낙찰가"] if c in ka.columns), None
    )
    if _ka_price_col is None:
        logger.warning(
            "artmarket에 price 컬럼 없음 — 제목+작가만 매칭 (정확도 저하)",
        )
        kauction_df["_key"] = (
            kauction_df["작가"].fillna("").str.strip()
            + "|" + kauction_df["제목"].fillna("").str.strip()
        )
        ka["_key"] = (
            ka["name_kor"].fillna("").str.strip()
            + "|" + ka["title"].fillna("").str.strip()
        )
    else:
        kauction_df["_key"] = (
            kauction_df["작가"].fillna("").str.strip()
            + "|" + kauction_df["제목"].fillna("").str.strip()
            + "|" + pd.to_numeric(kauction_df.get("낙찰가", 0), errors="coerce")
            .fillna(0).astype(int).astype(str)
        )
        ka["_key"] = (
            ka["name_kor"].fillna("").str.strip()
            + "|" + ka["title"].fillna("").str.strip()
            + "|" + pd.to_numeric(ka[_ka_price_col], errors="coerce")
            .fillna(0).astype(int).astype(str)
        )

    matched = kauction_df[["_key", "회차", "타입"]].merge(
        ka[["_key", "auction_date"]].drop_duplicates("_key"),
        on="_key", how="inner",
    )
    logger.info("Date inference: matched %d rows from artmarket", len(matched))

    # 타입+회차별 최빈 날짜
    session_date = matched.groupby(["타입", "회차"])["auction_date"].agg(
        lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
    ).reset_index().rename(columns={"auction_date": "sale_date"})

    # 조인
    result = kauction_df.merge(session_date, on=["타입", "회차"], how="left")
    mapped = result["sale_date"].notna().sum()
    logger.info("Date mapped: %d/%d (%.1f%%)", mapped, len(kauction_df),
                mapped / len(kauction_df) * 100)

    return result["sale_date"].fillna("").values


# ─── K-Artmarket CSV → 통합 스키마 ───

def convert_kartmarket(path: str | Path) -> pd.DataFrame:
    """K-Artmarket CSV를 통합 스키마로 변환."""
    logger.info("Loading K-Artmarket: %s", path)
    df = pd.read_csv(path, encoding="utf-8-sig")
    logger.info("K-Artmarket raw: %d rows", len(df))

    # 경매사명 정규화
    df["_house"] = df.apply(
        lambda row: _normalize_auction_house(
            str(row.get("auction_house", "")),
            str(row.get("auction_name", "")),
        ),
        axis=1,
    )

    # 작가명 3단계 결정
    def resolve_artist(row: pd.Series) -> str:
        kor = row.get("name_kor")
        eng = row.get("name_eng")
        title = row.get("title")
        if pd.notna(kor) and str(kor).strip():
            return str(kor).strip()
        if pd.notna(eng) and str(eng).strip():
            return str(eng).strip()
        if pd.notna(title) and str(title).strip():
            return "__UNKNOWN__"
        return ""

    artists = df.apply(resolve_artist, axis=1)

    # 가격 변환
    price = pd.to_numeric(
        df["price"].astype(str).str.replace(",", ""), errors="coerce",
    ).fillna(0).astype(int)

    # 크기: width/height 수치 컬럼이 있으면 size_raw보다 우선 사용
    # k-artmarket은 width/height가 96.5% 존재 → size_raw 파싱 실패 방지
    size_raw = df["size_raw"].fillna("")
    has_wh = df["width"].notna() & df["height"].notna()
    unit = df["unit"].fillna("cm")
    size_raw = size_raw.copy()
    size_raw.loc[has_wh] = (
        df.loc[has_wh, "width"].astype(str) + "x"
        + df.loc[has_wh, "height"].astype(str)
        + unit.loc[has_wh]
    )
    logger.info("Size: %d/%d from width/height columns (%.1f%%)",
                has_wh.sum(), len(df), has_wh.mean() * 100)

    out = pd.DataFrame({
        "artist": artists,
        "title": df["title"].fillna(""),
        "material": df["materials"].fillna(""),
        "size_raw": size_raw,
        "price": price,
        "sale_date": df["auction_date"].fillna(""),
        "source": df["_house"],
        "source_type": df.apply(
            lambda row: _extract_source_type(
                str(row.get("auction_name", "")), str(row.get("_house", "")),
            ),
            axis=1,
        ),
        "status": "sold",  # k-artmarket은 낙찰 건만 포함
        "year_created": "",
    })

    return out


# ─── 통합 파이프라인 ───

def merge_and_cleanse(
    old_path: str | Path,
    new_path: str | Path,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """K-Auction + K-Artmarket 데이터를 통합하고 클렌징."""
    # 1. 변환 (K-Auction에 artmarket 경로 전달하여 날짜 유추)
    old = convert_kauction(old_path, artmarket_path=new_path)
    new = convert_kartmarket(new_path)

    # 2. 품질 필터
    # 작가 없음 제거
    old = old[old["artist"].str.strip() != ""]
    new_before = len(new)
    new = new[new["artist"].str.strip() != ""]
    logger.info("Artist filter: removed %d from new", new_before - len(new))

    # 가격 0 제거
    old = old[old["price"] > 0]
    new = new[new["price"] > 0]

    # 3. 중복 제거 (K-Auction과 K-Artmarket의 케이옥션 데이터)
    # 코덱스 P2 (2026-04-18): sale_date도 dedup key에 포함.
    # 이전엔 artist|title|material|price만 보아서 동일 조건으로 팔린 서로 다른 회차
    # (예: 실크스크린 에디션 재판매)의 resale history가 통째로 날아갔음.
    def _dedup_key(frame: pd.DataFrame) -> pd.Series:
        date_part = frame.get("sale_date")
        if date_part is None:
            date_part = pd.Series("", index=frame.index)
        return (
            frame["artist"].astype(str)
            + "|" + frame["title"].astype(str)
            + "|" + frame["material"].astype(str)
            + "|" + frame["price"].astype(str)
            + "|" + date_part.fillna("").astype(str)
        )

    old["_dedup"] = _dedup_key(old)
    new["_dedup"] = _dedup_key(new)
    ka_mask = new["source"] == "케이옥션"
    is_dup = ka_mask & new["_dedup"].isin(set(old["_dedup"]))
    dup_count = is_dup.sum()
    new = new[~is_dup]
    logger.info("Dedup: removed %d K-Auction duplicates (key: artist|title|material|price|date)", dup_count)

    # 4. 통합
    merged = pd.concat([old, new], ignore_index=True)
    merged = merged.drop(columns=["_dedup"], errors="ignore")

    # 5. 비미술 클렌징
    from visionai.price_engine.preprocessing.data_cleanser import cleanse_dataframe

    merged, removed = cleanse_dataframe(
        merged, title_col="title", material_col="material",
    )

    # 6. 내부 컬럼 정리
    internal = [c for c in merged.columns if c.startswith("_")]
    merged = merged.drop(columns=internal, errors="ignore")

    logger.info("Final merged: %d rows", len(merged))

    # 7. 저장
    if output_path:
        merged.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info("Saved: %s", output_path)

    return merged
