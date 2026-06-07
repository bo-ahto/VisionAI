#!/usr/bin/env python3
"""Run PP-H11 operational search feature standardization.

PP-H7~H10 used a bounded search-feature pilot file. PP-H11 focuses on the
operational question: can external artist search signals be collected repeatedly,
standardized, quality-checked, and converted into stable features that the model
and service layer can consume?
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import io
import json
import os
import re
import sys
import time
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

warnings.filterwarnings(
    "ignore",
    message=r"This package \(`duckduckgo_search`\) has been renamed to `ddgs`!.*",
    category=RuntimeWarning,
)

try:  # Optional no-key search library used for PP-H21-PY.
    from ddgs import DDGS
except Exception:  # pragma: no cover - optional dependency availability
    try:
        from duckduckgo_search import DDGS
    except Exception:
        DDGS = None

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED  # noqa: E402
from run_pp_w_experiments import META_ALL, base_feature_sets, load_cold_with_meta, unique  # noqa: E402


EXP_ID = "PP-H11"
EXP_SLUG = "PP-H11_operational_search_feature_standardization"
TITLE = "운영형 작가 검색 피처 표준화 수집 검증"

SEARCH_DIR = REPO / "data" / "track6" / "external_search" / "operational"
LATEST_SNAPSHOT_PATH = SEARCH_DIR / "track6_artist_search_operational_snapshot_latest.csv"
LATEST_STANDARDIZED_PATH = SEARCH_DIR / "track6_artist_search_operational_standardized_latest.csv"
SPLIT_DIR = REPO / "data" / "track6_split"

QUERY_TEMPLATES = [
    ("name_artist_ko", "{name} 미술 작가"),
    ("name_artwork_ko", "{name} 작품 미술"),
    ("name_exhibition_ko", "{name} 전시 작가"),
    ("name_gallery_ko", "{name} 갤러리 미술"),
    ("name_auction_ko", "{name} 작품 경매"),
]

ART_KEYWORDS = [
    "작가",
    "미술",
    "화가",
    "아티스트",
    "artist",
    "art",
    "painting",
    "contemporary",
    "갤러리",
    "gallery",
    "museum",
    "전시",
]
EXHIBITION_KEYWORDS = ["전시", "개인전", "단체전", "아트페어", "비엔날레", "exhibition", "solo", "fair", "biennale"]
GALLERY_KEYWORDS = ["갤러리", "화랑", "gallery", "museum", "미술관", "art center", "kunsthalle"]
MARKET_KEYWORDS = ["auction", "옥션", "경매", "price", "판매", "작품가격", "작품 가격", "k-artmarket", "artprice"]
SOCIAL_KEYWORDS = ["instagram", "인스타", "blog", "블로그", "facebook", "youtube", "뉴스", "news", "naver"]
HOMONYM_KEYWORDS = ["배우", "가수", "축구", "야구", "정치", "기업인", "교수", "아나운서", "model", "singer", "actor"]
TRUSTED_DOMAIN_KEYWORDS = [
    "gallery",
    "museum",
    "art",
    "auction",
    "k-artmarket",
    "biennale",
    "frieze",
    "artsy",
    "artnet",
    "seoulauction",
    "k-auction",
]
COMMON_SINGLE_NAMES = {"김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송"}
ART_DOMAIN_QUERY = (
    "(site:artsy.net OR site:artnet.com OR site:mutualart.com OR "
    "site:sothebys.com OR site:christies.com OR site:phillips.com OR "
    "site:seoulauction.com OR site:k-auction.com)"
)
ARTIST_COUNT_COLUMNS = ["train_row_count", "validation_row_count", "test_row_count", "total_row_count"]


@dataclass(frozen=True)
class SearchResult:
    title: str
    snippet: str
    url: str
    domain: str
    published_at: str = ""


def clean_artist_name(name: Any) -> str:
    value = "" if pd.isna(name) else str(name)
    value = re.sub(r"_[A-Z]+$", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def is_collectable_artist_name(name: str) -> bool:
    stripped = name.strip()
    if len(stripped) < 2:
        return False
    if stripped in COMMON_SINGLE_NAMES:
        return False
    if stripped.lower() in {"unknown", "nan", "none", "__missing__"}:
        return False
    return True


def _artist_name_counts_from_frames(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for split, frame in frames.items():
        if "artist_name_ko" not in frame.columns:
            continue
        names = frame["artist_name_ko"].map(clean_artist_name)
        for name, count in names.value_counts().items():
            if is_collectable_artist_name(name):
                rows.append({"artist_search_name": name, f"{split}_row_count": int(count)})
    counts = pd.DataFrame(rows)
    if counts.empty:
        return pd.DataFrame(columns=["artist_search_name", "train_row_count", "validation_row_count", "test_row_count", "total_row_count"])
    counts = counts.groupby("artist_search_name", as_index=False).sum(numeric_only=True)
    for col in ["train_row_count", "validation_row_count", "test_row_count"]:
        if col not in counts.columns:
            counts[col] = 0
    counts["total_row_count"] = counts[["train_row_count", "validation_row_count", "test_row_count"]].sum(axis=1)
    return counts


def select_artist_names(limit_artists: int, selection_policy: str, artist_scope: str = "cold") -> pd.DataFrame:
    fs = base_feature_sets()
    base_features = unique(fs["generated_all"] + META_ALL)
    if artist_scope == "cold":
        train, val, test = load_cold_with_meta(base_features)
        frames = {"train": train, "validation": val, "test": test}
    elif artist_scope == "warm":
        frames = {
            "train": pd.read_csv(SPLIT_DIR / "track6_train.csv", low_memory=False),
            "validation": pd.read_csv(SPLIT_DIR / "track6_val_warm.csv", low_memory=False),
            "test": pd.read_csv(SPLIT_DIR / "track6_test_warm.csv", low_memory=False),
        }
    elif artist_scope == "all":
        cold_train, cold_val, cold_test = load_cold_with_meta(base_features)
        frames = {
            "train": pd.concat([pd.read_csv(SPLIT_DIR / "track6_train.csv", low_memory=False), cold_train], ignore_index=True, sort=False),
            "validation": pd.concat([pd.read_csv(SPLIT_DIR / "track6_val_warm.csv", low_memory=False), cold_val], ignore_index=True, sort=False),
            "test": pd.concat([pd.read_csv(SPLIT_DIR / "track6_test_warm.csv", low_memory=False), cold_test], ignore_index=True, sort=False),
        }
    else:
        raise ValueError(f"Unsupported artist_scope: {artist_scope}")
    counts = _artist_name_counts_from_frames(frames)
    sort_cols = ["total_row_count", "train_row_count", "validation_row_count", "test_row_count", "artist_search_name"]
    ascending = [False, False, False, False, True]
    if selection_policy == "train_frequency":
        sort_cols = ["train_row_count", "total_row_count", "validation_row_count", "test_row_count", "artist_search_name"]
    elif selection_policy == "eval_frequency":
        counts["eval_row_count"] = counts["validation_row_count"] + counts["test_row_count"]
        sort_cols = ["eval_row_count", "validation_row_count", "test_row_count", "train_row_count", "artist_search_name"]
    elif selection_policy == "test_frequency":
        sort_cols = ["test_row_count", "validation_row_count", "train_row_count", "total_row_count", "artist_search_name"]
    counts = counts.sort_values(sort_cols, ascending=ascending)
    return counts.head(limit_artists).reset_index(drop=True)


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def clean_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def unwrap_duckduckgo_href(href: str) -> str:
    if not href:
        return ""
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(uddg) if uddg else href
    return href


def text_hash(*parts: str) -> str:
    payload = "\u241f".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(payload).hexdigest()


def sanitize_error_message(error: Any) -> str:
    value = "" if error is None else str(error)
    value = re.sub(r"([?&]key=)[^&\s]+", r"\1REDACTED", value)
    value = re.sub(r"(X-Naver-Client-Secret['\"]?:\s*)[^,\s}]+", r"\1REDACTED", value)
    value = re.sub(r"(X-Naver-Client-Id['\"]?:\s*)[^,\s}]+", r"\1REDACTED", value)
    return value


def merge_artist_selection_with_latest(artist_df: pd.DataFrame) -> pd.DataFrame:
    """Preserve existing latest snapshot artists when adding a partial provider run."""
    if not LATEST_SNAPSHOT_PATH.exists():
        return artist_df
    try:
        existing = pd.read_csv(LATEST_SNAPSHOT_PATH, low_memory=False)
    except Exception:
        return artist_df
    if "artist_search_name" not in existing.columns:
        return artist_df
    keep_cols = ["artist_search_name", *[col for col in ARTIST_COUNT_COLUMNS if col in existing.columns]]
    existing_artists = existing[keep_cols].drop_duplicates("artist_search_name").copy()
    for col in ARTIST_COUNT_COLUMNS:
        if col not in existing_artists.columns:
            existing_artists[col] = 0
        if col not in artist_df.columns:
            artist_df[col] = 0
    combined = pd.concat(
        [
            existing_artists[["artist_search_name", *ARTIST_COUNT_COLUMNS]],
            artist_df[["artist_search_name", *ARTIST_COUNT_COLUMNS]],
        ],
        ignore_index=True,
        sort=False,
    )
    combined = combined.drop_duplicates("artist_search_name", keep="last")
    for col in ARTIST_COUNT_COLUMNS:
        combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0).astype(int)
    return combined.sort_values(
        ["total_row_count", "train_row_count", "validation_row_count", "test_row_count", "artist_search_name"],
        ascending=[False, False, False, False, True],
    ).reset_index(drop=True)


def extract_years(text: str) -> set[int]:
    years = set()
    for raw in re.findall(r"(20[0-3][0-9]|19[7-9][0-9])", text):
        try:
            years.add(int(raw))
        except ValueError:
            continue
    return years


def is_recent_result(text: str, snapshot_year: int) -> bool:
    years = extract_years(text)
    return any(year >= snapshot_year - 1 for year in years)


def classify_source_group(domain: str, text: str) -> str:
    lowered = f"{domain} {text}".lower()
    if contains_any(lowered, MARKET_KEYWORDS):
        return "market"
    if contains_any(lowered, GALLERY_KEYWORDS):
        return "gallery_museum"
    if "news" in lowered or "신문" in lowered or "일보" in lowered:
        return "news"
    if "instagram" in lowered or "youtube" in lowered or "blog" in lowered or "facebook" in lowered:
        return "social_blog"
    if contains_any(lowered, EXHIBITION_KEYWORDS):
        return "exhibition"
    if contains_any(lowered, ART_KEYWORDS):
        return "art_general"
    return "other"


def search_duckduckgo_html(query: str, max_results: int, timeout: float) -> tuple[list[SearchResult], int, str]:
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    }
    response = requests.get(url, params={"q": query}, headers=headers, timeout=timeout)
    status = response.status_code
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []
    for node in soup.select(".result"):
        link = node.select_one(".result__a")
        if link is None:
            continue
        title = link.get_text(" ", strip=True)
        href = unwrap_duckduckgo_href(str(link.get("href", "")))
        snippet_node = node.select_one(".result__snippet")
        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""
        domain = clean_domain(href)
        if not title and not snippet:
            continue
        results.append(SearchResult(title=title, snippet=snippet, url=href, domain=domain))
        if len(results) >= max_results:
            break
    return results, status, ""


def duckduckgo_item_to_result(item: dict[str, Any]) -> SearchResult:
    href = str(item.get("href") or item.get("url") or "")
    title = str(item.get("title") or "")
    snippet = str(item.get("body") or item.get("snippet") or "")
    return SearchResult(title=title, snippet=snippet, url=href, domain=clean_domain(href))


def search_duckduckgo_library(query: str, max_results: int, timeout: float) -> tuple[list[SearchResult], int, str]:
    if DDGS is None:
        return [], 0, "missing_duckduckgo_search_library"
    errors: list[str] = []
    for verify in [True, False]:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with contextlib.redirect_stderr(io.StringIO()):
                    with DDGS(timeout=max(int(timeout), 1), verify=verify) as ddgs:
                        items = list(ddgs.text(
                            query,
                            region="kr-kr",
                            safesearch="moderate",
                            backend="auto",
                            max_results=max_results,
                        ))
            results = [
                duckduckgo_item_to_result(item)
                for item in items[:max_results]
                if str(item.get("title") or "").strip() or str(item.get("body") or item.get("snippet") or "").strip()
            ]
            return results, 200, ""
        except Exception as exc:  # pragma: no cover - network/certificate behavior
            errors.append(f"verify={verify}: {type(exc).__name__}: {exc}")
    return [], 0, sanitize_error_message(" | ".join(errors))


def search_duckduckgo_library_art_domains(query: str, max_results: int, timeout: float) -> tuple[list[SearchResult], int, str]:
    return search_duckduckgo_library(f"{query} {ART_DOMAIN_QUERY}", max_results=max_results, timeout=timeout)


def search_duckduckgo_library_art_context(query: str, max_results: int, timeout: float) -> tuple[list[SearchResult], int, str]:
    return search_duckduckgo_library(f"{query} artist gallery exhibition auction artwork", max_results=max_results, timeout=timeout)


def search_naver_api(provider: str, query: str, max_results: int, timeout: float) -> tuple[list[SearchResult], int, str]:
    client_id = os.getenv("NAVER_CLIENT_ID") or os.getenv("NAVER_SEARCH_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET") or os.getenv("NAVER_SEARCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        return [], 0, "missing_naver_credentials"
    endpoint_by_provider = {
        "naver_api_blog": "https://openapi.naver.com/v1/search/blog.json",
        "naver_api_news": "https://openapi.naver.com/v1/search/news.json",
        "naver_api_webkr": "https://openapi.naver.com/v1/search/webkr.json",
    }
    endpoint = endpoint_by_provider[provider]
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    response = requests.get(endpoint, params={"query": query, "display": max_results, "sort": "sim"}, headers=headers, timeout=timeout)
    status = response.status_code
    response.raise_for_status()
    payload = response.json()
    results = []
    for item in payload.get("items", [])[:max_results]:
        title = re.sub(r"<[^>]+>", "", str(item.get("title", "")))
        snippet = re.sub(r"<[^>]+>", "", str(item.get("description", "")))
        if provider == "naver_api_news":
            snippet = re.sub(r"<[^>]+>", "", str(item.get("description", "")))
        if provider == "naver_api_blog":
            snippet = re.sub(r"<[^>]+>", "", str(item.get("description", "")))
        href = str(item.get("link", ""))
        published_at = str(item.get("postdate", "") or item.get("pubDate", ""))
        results.append(SearchResult(title=title, snippet=snippet, url=href, domain=clean_domain(href), published_at=published_at))
    return results, status, ""


def search_google_cse(query: str, max_results: int, timeout: float) -> tuple[list[SearchResult], int, str]:
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    if not api_key or not cse_id:
        return [], 0, "missing_google_credentials"
    endpoint = "https://www.googleapis.com/customsearch/v1"
    response = requests.get(
        endpoint,
        params={
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": min(max(max_results, 1), 10),
        },
        timeout=timeout,
    )
    status = response.status_code
    response.raise_for_status()
    payload = response.json()
    results = []
    for item in payload.get("items", [])[:max_results]:
        title = str(item.get("title", ""))
        snippet = str(item.get("snippet", ""))
        href = str(item.get("link", ""))
        results.append(SearchResult(title=title, snippet=snippet, url=href, domain=clean_domain(href)))
    return results, status, ""


def search_naver_html(query: str, max_results: int, timeout: float) -> tuple[list[SearchResult], int, str]:
    endpoint = "https://search.naver.com/search.naver"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    response = requests.get(endpoint, params={"where": "nexearch", "query": query}, headers=headers, timeout=timeout)
    status = response.status_code
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []
    seen_urls: set[str] = set()
    skip_texts = {"더보기", "이미지", "동영상", "뉴스", "쇼핑", "지도", "전체", "블로그", "카페", "NAVER"}
    skip_text_fragments = ["검색옵션", "Keep", "바로가기", "자세히 보기"]
    for link in soup.find_all("a", href=True):
        href = str(link.get("href", "")).strip()
        title = link.get_text(" ", strip=True)
        classes = set(link.get("class", []))
        if not href.startswith("http"):
            continue
        if "tab" in classes or "link_help" in classes:
            continue
        if not title or title in skip_texts or len(title) < 6:
            continue
        if any(fragment in title for fragment in skip_text_fragments):
            continue
        if "›" in title or re.match(r"^(www\.|[a-z0-9.-]+\.(co\.kr|com|net|org|kr))\b", title.lower()):
            continue
        if any(skip in href for skip in ["adcr.naver.com", "help.naver.com", "nid.naver.com", "keep.naver.com"]):
            continue
        if href.rstrip("/") in {"https://www.naver.com", "https://m.naver.com"}:
            continue
        if href in seen_urls:
            continue
        seen_urls.add(href)
        parent_text = link.parent.get_text(" ", strip=True) if link.parent is not None else ""
        snippet = parent_text.replace(title, " ", 1).strip()
        if len(snippet) > 320:
            snippet = snippet[:320]
        results.append(SearchResult(title=title, snippet=snippet, url=href, domain=clean_domain(href)))
        if len(results) >= max_results:
            break
    return results, status, ""


def search_provider(provider: str, query: str, max_results: int, timeout: float) -> tuple[list[SearchResult], int, str]:
    try:
        if provider in {"naver_api_blog", "naver_api_news", "naver_api_webkr"}:
            return search_naver_api(provider, query, max_results, timeout)
        if provider == "google_cse":
            return search_google_cse(query, max_results, timeout)
        if provider == "naver_html":
            return search_naver_html(query, max_results, timeout)
        if provider == "duckduckgo_html":
            return search_duckduckgo_html(query, max_results, timeout)
        if provider == "python_ddg":
            return search_duckduckgo_library(query, max_results, timeout)
        if provider == "python_ddg_art_domains":
            return search_duckduckgo_library_art_domains(query, max_results, timeout)
        if provider == "python_ddg_art_context":
            return search_duckduckgo_library_art_context(query, max_results, timeout)
    except Exception as exc:  # pragma: no cover - network behavior
        status = getattr(getattr(exc, "response", None), "status_code", 0) or 0
        return [], int(status), sanitize_error_message(f"{type(exc).__name__}: {exc}")
    return [], 0, f"unsupported_provider:{provider}"


def result_to_raw_row(
    *,
    run_id: str,
    snapshot_month: str,
    artist_name: str,
    provider: str,
    template_id: str,
    query: str,
    rank: int,
    result: SearchResult,
    status: int,
    error: str,
    collected_at: str,
) -> dict[str, Any]:
    text = f"{result.title} {result.snippet} {result.url}"
    return {
        "collector_run_id": run_id,
        "snapshot_month": snapshot_month,
        "artist_search_name": artist_name,
        "provider": provider,
        "query_template_id": template_id,
        "query_text": query,
        "rank": rank,
        "title": result.title,
        "snippet": result.snippet,
        "url": result.url,
        "domain": result.domain,
        "source_group": classify_source_group(result.domain, text),
        "published_at": result.published_at,
        "http_status": status,
        "error": error,
        "raw_payload_hash": text_hash(result.title, result.snippet, result.url),
        "collected_at": collected_at,
    }


def empty_raw_row(
    *,
    run_id: str,
    snapshot_month: str,
    artist_name: str,
    provider: str,
    template_id: str,
    query: str,
    status: int,
    error: str,
    collected_at: str,
) -> dict[str, Any]:
    return {
        "collector_run_id": run_id,
        "snapshot_month": snapshot_month,
        "artist_search_name": artist_name,
        "provider": provider,
        "query_template_id": template_id,
        "query_text": query,
        "rank": 0,
        "title": "",
        "snippet": "",
        "url": "",
        "domain": "",
        "source_group": "missing",
        "published_at": "",
        "http_status": status,
        "error": error,
        "raw_payload_hash": text_hash(artist_name, provider, template_id, query, error),
        "collected_at": collected_at,
    }


def collect_raw_results(
    artist_df: pd.DataFrame,
    providers: list[str],
    query_templates: list[tuple[str, str]],
    max_results: int,
    sleep_seconds: float,
    timeout: float,
    run_id: str,
    snapshot_month: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total_requests = len(artist_df) * len(providers) * len(query_templates)
    request_idx = 0
    for artist_name in artist_df["artist_search_name"].tolist():
        for provider in providers:
            for template_id, template in query_templates:
                request_idx += 1
                query = template.format(name=artist_name)
                collected_at = datetime.now().isoformat(timespec="seconds")
                results, status, error = search_provider(provider, query, max_results, timeout)
                if results:
                    for rank, result in enumerate(results, start=1):
                        rows.append(result_to_raw_row(
                            run_id=run_id,
                            snapshot_month=snapshot_month,
                            artist_name=artist_name,
                            provider=provider,
                            template_id=template_id,
                            query=query,
                            rank=rank,
                            result=result,
                            status=status,
                            error=error,
                            collected_at=collected_at,
                        ))
                else:
                    rows.append(empty_raw_row(
                        run_id=run_id,
                        snapshot_month=snapshot_month,
                        artist_name=artist_name,
                        provider=provider,
                        template_id=template_id,
                        query=query,
                        status=status,
                        error=error,
                        collected_at=collected_at,
                    ))
                if request_idx % 10 == 0:
                    print(json.dumps({
                        "request": request_idx,
                        "total_requests": total_requests,
                        "latest_artist": artist_name,
                        "provider": provider,
                        "template": template_id,
                        "result_count": len(results),
                        "error": error,
                    }, ensure_ascii=False), flush=True)
                time.sleep(sleep_seconds)
    return pd.DataFrame(rows)


def standardize_results(raw_df: pd.DataFrame, snapshot_year: int) -> pd.DataFrame:
    out = raw_df.copy()
    for col in ["title", "snippet", "url", "domain", "source_group", "error"]:
        out[col] = out[col].astype("string").fillna("")
    out["result_text"] = (out["title"] + " " + out["snippet"] + " " + out["url"]).astype(str)
    out["has_result"] = out["rank"].astype(float).gt(0) & out["title"].astype(str).ne("")
    out["is_art_context"] = out["result_text"].map(lambda value: contains_any(value, ART_KEYWORDS))
    out["is_exhibition_context"] = out["result_text"].map(lambda value: contains_any(value, EXHIBITION_KEYWORDS))
    out["is_gallery_context"] = out["result_text"].map(lambda value: contains_any(value, GALLERY_KEYWORDS))
    out["is_market_context"] = out["result_text"].map(lambda value: contains_any(value, MARKET_KEYWORDS))
    out["is_social_context"] = out["result_text"].map(lambda value: contains_any(value, SOCIAL_KEYWORDS))
    out["is_homonym_context"] = out["result_text"].map(lambda value: contains_any(value, HOMONYM_KEYWORDS))
    out["is_trusted_domain"] = out["domain"].map(lambda value: contains_any(str(value), TRUSTED_DOMAIN_KEYWORDS))
    out["is_recent_context"] = out["result_text"].map(lambda value: is_recent_result(value, snapshot_year))
    out["artist_name_in_result"] = out.apply(
        lambda row: str(row["artist_search_name"]).replace(" ", "") in str(row["result_text"]).replace(" ", ""),
        axis=1,
    )
    return out


def ratio(numer: float, denom: float) -> float:
    if denom <= 0:
        return 0.0
    return float(numer / denom)


def grade_quality(score: float, homonym_ratio: float) -> str:
    if score >= 0.70 and homonym_ratio < 0.20:
        return "high"
    if score >= 0.45 and homonym_ratio < 0.40:
        return "medium"
    if score <= 0 and homonym_ratio <= 0:
        return "missing"
    return "low"


def build_snapshot(standard_df: pd.DataFrame, artist_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for artist_name, group in standard_df.groupby("artist_search_name", dropna=False):
        result_group = group[group["has_result"]].copy()
        total = float(len(result_group))
        provider_success = group.groupby("provider")["has_result"].max()
        query_success = group.groupby(["provider", "query_template_id"])["has_result"].max()
        art_count = float(result_group["is_art_context"].sum())
        exhibition_count = float(result_group["is_exhibition_context"].sum())
        gallery_count = float(result_group["is_gallery_context"].sum())
        market_count = float(result_group["is_market_context"].sum())
        social_count = float(result_group["is_social_context"].sum())
        homonym_count = float(result_group["is_homonym_context"].sum())
        trusted_count = float(result_group["is_trusted_domain"].sum())
        recent_count = float(result_group["is_recent_context"].sum())
        name_match_count = float(result_group["artist_name_in_result"].sum())
        unique_domain_count = float(result_group["domain"].replace("", np.nan).dropna().nunique())
        provider_coverage_count = float(provider_success.sum())
        provider_coverage_score = ratio(provider_coverage_count, max(float(len(provider_success)), 1.0))
        art_match_ratio = ratio(art_count, total)
        exhibition_ratio = ratio(exhibition_count, total)
        market_ratio = ratio(market_count, total)
        trusted_domain_ratio = ratio(trusted_count, total)
        recent_result_ratio = ratio(recent_count, total)
        homonym_risk_ratio = ratio(homonym_count, total)
        name_match_ratio = ratio(name_match_count, total)
        search_quality_score = (
            0.30 * art_match_ratio
            + 0.20 * trusted_domain_ratio
            + 0.15 * exhibition_ratio
            + 0.15 * market_ratio
            + 0.10 * recent_result_ratio
            + 0.10 * provider_coverage_score
            + 0.10 * name_match_ratio
            - 0.30 * homonym_risk_ratio
        )
        search_quality_score = float(np.clip(search_quality_score, 0.0, 1.0))
        rows.append({
            "artist_search_name": artist_name,
            "search_result_count": total,
            "search_source_count": unique_domain_count,
            "provider_coverage_count": provider_coverage_count,
            "query_success_count": float(query_success.sum()),
            "search_art_context_count": art_count,
            "search_exhibition_context_count": exhibition_count,
            "search_gallery_context_count": gallery_count,
            "search_market_context_count": market_count,
            "search_social_context_count": social_count,
            "search_homonym_context_count": homonym_count,
            "search_trusted_domain_count": trusted_count,
            "search_recent_result_count": recent_count,
            "search_name_match_count": name_match_count,
            "search_art_match_ratio": art_match_ratio,
            "search_exhibition_ratio": exhibition_ratio,
            "search_market_ratio": market_ratio,
            "search_trusted_domain_ratio": trusted_domain_ratio,
            "search_recent_result_ratio": recent_result_ratio,
            "search_homonym_risk_ratio": homonym_risk_ratio,
            "search_name_match_ratio": name_match_ratio,
            "search_source_ratio": ratio(unique_domain_count, total),
            "search_quality_score": search_quality_score,
            "search_quality_grade": grade_quality(search_quality_score, homonym_risk_ratio),
            "search_homonym_risk_grade": "risk" if homonym_risk_ratio >= 0.40 else ("watch" if homonym_risk_ratio >= 0.20 else "clear"),
            "search_result_count_log": float(np.log1p(total)),
            "search_source_count_log": float(np.log1p(unique_domain_count)),
            "search_art_context_count_log": float(np.log1p(art_count)),
            "search_exhibition_context_count_log": float(np.log1p(exhibition_count)),
            "search_collected_flag": 1.0,
            "search_success_flag": 1.0 if total > 0 else 0.0,
        })
    snapshot = pd.DataFrame(rows)
    snapshot = artist_df.merge(snapshot, on="artist_search_name", how="left")
    for col in snapshot.columns:
        if col.startswith("search_") and snapshot[col].dtype.kind in {"f", "i"}:
            snapshot[col] = snapshot[col].fillna(0.0)
    for col in ["search_quality_grade", "search_homonym_risk_grade"]:
        if col in snapshot.columns:
            snapshot[col] = snapshot[col].astype("string").fillna("missing")
    return snapshot


def build_metrics(raw_df: pd.DataFrame, standard_df: pd.DataFrame, snapshot_df: pd.DataFrame, providers: list[str], max_results: int) -> pd.DataFrame:
    request_level = raw_df.groupby(["artist_search_name", "provider", "query_template_id"], dropna=False).agg(
        has_result=("rank", lambda values: bool(pd.Series(values).astype(float).gt(0).any())),
        has_error=("error", lambda values: bool(pd.Series(values).astype(str).replace("", np.nan).notna().any())),
    ).reset_index()
    total_requests = len(request_level)
    rows = [{
        "experiment_id": EXP_ID,
        "candidate": "operational_search_collection_standardization",
        "split": "collection",
        "policy": "artist_level_periodic_collection",
        "artist_n": int(snapshot_df["artist_search_name"].nunique()),
        "provider_n": len(providers),
        "query_template_n": int(raw_df["query_template_id"].nunique()) if "query_template_id" in raw_df.columns else len(QUERY_TEMPLATES),
        "max_results_per_query": max_results,
        "request_n": int(total_requests),
        "request_success_rate": float(request_level["has_result"].mean()) if total_requests else 0.0,
        "request_error_rate": float(request_level["has_error"].mean()) if total_requests else 0.0,
        "artist_success_rate": float(snapshot_df["search_success_flag"].mean()) if len(snapshot_df) else 0.0,
        "quality_high_rate": float(snapshot_df["search_quality_grade"].eq("high").mean()) if len(snapshot_df) else 0.0,
        "quality_medium_rate": float(snapshot_df["search_quality_grade"].eq("medium").mean()) if len(snapshot_df) else 0.0,
        "quality_low_rate": float(snapshot_df["search_quality_grade"].eq("low").mean()) if len(snapshot_df) else 0.0,
        "quality_missing_rate": float(snapshot_df["search_quality_grade"].eq("missing").mean()) if len(snapshot_df) else 0.0,
        "homonym_risk_rate": float(snapshot_df["search_homonym_risk_grade"].eq("risk").mean()) if len(snapshot_df) else 0.0,
        "avg_result_count_per_artist": float(snapshot_df["search_result_count"].mean()) if len(snapshot_df) else 0.0,
        "avg_unique_domain_per_artist": float(snapshot_df["search_source_count"].mean()) if len(snapshot_df) else 0.0,
        "avg_quality_score": float(snapshot_df["search_quality_score"].mean()) if len(snapshot_df) else 0.0,
        "art_context_ratio_mean": float(snapshot_df["search_art_match_ratio"].mean()) if len(snapshot_df) else 0.0,
        "exhibition_ratio_mean": float(snapshot_df["search_exhibition_ratio"].mean()) if len(snapshot_df) else 0.0,
        "market_ratio_mean": float(snapshot_df["search_market_ratio"].mean()) if len(snapshot_df) else 0.0,
        "name_match_ratio_mean": float(snapshot_df["search_name_match_ratio"].mean()) if len(snapshot_df) else 0.0,
    }]
    source_rows = []
    if not standard_df.empty:
        source_counts = standard_df[standard_df["has_result"]]["source_group"].value_counts(normalize=True)
        for source_group, value in source_counts.items():
            source_rows.append({
                "experiment_id": EXP_ID,
                "candidate": f"source_group_share__{source_group}",
                "split": "collection",
                "policy": "source_group_diagnostics",
                "source_group": source_group,
                "source_group_share": float(value),
            })
    return pd.DataFrame(rows + source_rows)


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "- 없음"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("\n", " ").replace("|", "\\|")


def render_report(
    metrics_df: pd.DataFrame,
    snapshot_df: pd.DataFrame,
    sample_df: pd.DataFrame,
    run_config: dict[str, Any],
) -> tuple[str, str]:
    main_metrics = metrics_df[metrics_df["candidate"].eq("operational_search_collection_standardization")]
    grade_counts = snapshot_df["search_quality_grade"].value_counts(dropna=False).rename_axis("grade").reset_index(name="artist_count")
    risk_counts = snapshot_df["search_homonym_risk_grade"].value_counts(dropna=False).rename_axis("homonym_risk").reset_index(name="artist_count")
    low_samples = snapshot_df.sort_values(["search_quality_score", "search_homonym_risk_ratio"], ascending=[True, False])[
        ["artist_search_name", "search_quality_grade", "search_homonym_risk_grade", "search_quality_score", "search_result_count", "search_art_match_ratio", "search_name_match_ratio"]
    ].head(12)
    high_samples = snapshot_df.sort_values(["search_quality_score", "search_art_match_ratio"], ascending=[False, False])[
        ["artist_search_name", "search_quality_grade", "search_homonym_risk_grade", "search_quality_score", "search_result_count", "search_art_match_ratio", "search_name_match_ratio"]
    ].head(12)
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 목적",
        "",
        "- 외부 검색 결과를 운영에서 반복 수집 가능한 형태로 표준화할 수 있는지 검증한다.",
        "- 가격 예측 모델에는 검색 결과 원문을 직접 넣지 않고, 작가 단위 품질 점수와 문맥 비율로 변환한 스냅샷만 사용한다.",
        "- 이번 실행은 기존 PP-H7~H10 파일을 덮어쓰지 않고 별도 운영형 경로에 산출물을 생성한다.",
        "",
        "## 실행 설정",
        "",
        markdown_table(pd.DataFrame([run_config]).T.reset_index().rename(columns={"index": "항목", 0: "값"}), max_rows=80),
        "",
        "## 전체 수집 품질",
        "",
        markdown_table(main_metrics, max_rows=10),
        "",
        "## 품질 등급 분포",
        "",
        markdown_table(grade_counts),
        "",
        "## 동명이인 위험 분포",
        "",
        markdown_table(risk_counts),
        "",
        "## 품질 상위 샘플",
        "",
        markdown_table(high_samples),
        "",
        "## 품질 하위 샘플",
        "",
        markdown_table(low_samples),
        "",
        "## 원본 결과 샘플",
        "",
        markdown_table(sample_df[["artist_search_name", "provider", "query_template_id", "rank", "title", "domain", "source_group"]].head(30), max_rows=30),
        "",
        "## 해석",
        "",
        "- H11의 합격 기준은 단순 검색 성공률이 아니라 `high/medium` 등급 비율과 동명이인 위험률이다.",
        "- `low` 또는 `risk` 등급 작가는 가격점 예측 피처로 직접 쓰기보다, 신뢰도 하향/가격 범위 확대/수동 검수 대상으로 사용해야 한다.",
        "- 동일 스키마로 월 단위 스냅샷을 누적하면 검색 인지도 변화량, 최근 전시 노출, 출처 다양성 변화까지 후속 실험 피처로 만들 수 있다.",
        "",
    ]
    md = "\n".join(lines)
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}"
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}th,td{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}"
        "th{background:#eef2f7}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}.note{background:#f8fafc;border-left:4px solid #667085;padding:10px 12px}"
    )
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title><style>{style}</style></head>
<body><h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<h2>목적</h2><div class="note">외부 검색 결과를 반복 수집 가능한 운영형 피처로 표준화하는 검증입니다. 검색 원문은 보관하고, 모델에는 작가 단위 스냅샷 피처만 전달합니다.</div>
<h2>실행 설정</h2>{pd.DataFrame([run_config]).T.reset_index().rename(columns={'index':'항목',0:'값'}).to_html(index=False, escape=True)}
<h2>전체 수집 품질</h2>{main_metrics.to_html(index=False, escape=True)}
<h2>품질 등급 분포</h2>{grade_counts.to_html(index=False, escape=True)}
<h2>동명이인 위험 분포</h2>{risk_counts.to_html(index=False, escape=True)}
<h2>품질 상위 샘플</h2>{high_samples.to_html(index=False, escape=True)}
<h2>품질 하위 샘플</h2>{low_samples.to_html(index=False, escape=True)}
<h2>원본 결과 샘플</h2>{sample_df[['artist_search_name','provider','query_template_id','rank','title','domain','source_group']].head(30).to_html(index=False, escape=True)}
<h2>해석</h2><ul><li>H11의 합격 기준은 단순 검색 성공률이 아니라 high/medium 등급 비율과 동명이인 위험률입니다.</li><li>low/risk 등급은 가격점 예측 피처보다 신뢰도 하향, 가격 범위 확대, 수동 검수에 우선 활용합니다.</li><li>월 단위 스냅샷을 누적하면 인지도 변화량과 최근 전시 노출 변화까지 후속 피처로 확장할 수 있습니다.</li></ul>
</body></html>"""
    return md, html_doc


def write_outputs(
    raw_df: pd.DataFrame,
    standard_df: pd.DataFrame,
    snapshot_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    run_config: dict[str, Any],
) -> None:
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    run_id = str(run_config["collector_run_id"])
    snapshot_month = str(run_config["snapshot_month"])
    raw_jsonl_path = SEARCH_DIR / f"artist_search_result_raw_{run_id}.jsonl"
    raw_csv_path = SEARCH_DIR / f"artist_search_result_raw_{run_id}.csv"
    standard_csv_path = SEARCH_DIR / f"artist_search_result_standardized_{run_id}.csv"
    snapshot_csv_path = SEARCH_DIR / f"artist_search_feature_snapshot_{snapshot_month}_{run_id}.csv"
    run_json_path = SEARCH_DIR / f"artist_search_collection_run_{run_id}.json"

    with raw_jsonl_path.open("w", encoding="utf-8") as handle:
        for row in raw_df.to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    raw_df.to_csv(raw_csv_path, index=False)
    standard_df.to_csv(standard_csv_path, index=False)
    snapshot_df.to_csv(snapshot_csv_path, index=False)
    standard_df.to_csv(LATEST_STANDARDIZED_PATH, index=False)
    snapshot_df.to_csv(LATEST_SNAPSHOT_PATH, index=False)
    run_json_path.write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")

    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    snapshot_df.to_csv(exp_dir / "outputs" / "artist_search_feature_snapshot.csv", index=False)
    standard_df.to_csv(exp_dir / "outputs" / "artist_search_result_standardized.csv", index=False)
    raw_df.to_csv(exp_dir / "outputs" / "artist_search_result_raw.csv", index=False)
    (exp_dir / "experiment_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")

    sample_df = standard_df[standard_df["has_result"]].sort_values(["artist_search_name", "provider", "query_template_id", "rank"])
    md, html_doc = render_report(metrics_df, snapshot_df, sample_df, run_config)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    metrics_df.assign(folder=str(exp_dir.relative_to(REPO))).to_csv(BASE_EXP_DIR / "PP-H11_operational_search_summary_metrics.csv", index=False)

    artifact_paths = {
        "raw_jsonl": str(raw_jsonl_path.relative_to(REPO)),
        "raw_csv": str(raw_csv_path.relative_to(REPO)),
        "standardized_csv": str(standard_csv_path.relative_to(REPO)),
        "snapshot_csv": str(snapshot_csv_path.relative_to(REPO)),
        "latest_standardized_csv": str(LATEST_STANDARDIZED_PATH.relative_to(REPO)),
        "latest_snapshot_csv": str(LATEST_SNAPSHOT_PATH.relative_to(REPO)),
        "experiment_dir": str(exp_dir.relative_to(REPO)),
    }
    (exp_dir / "artifacts" / "output_paths.json").write_text(json.dumps(artifact_paths, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-artists", type=int, default=80)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--selection-policy", choices=["all_frequency", "train_frequency", "eval_frequency", "test_frequency"], default="all_frequency")
    parser.add_argument("--artist-scope", choices=["cold", "warm", "all"], default="cold")
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["naver_html"],
        choices=[
            "duckduckgo_html",
            "google_cse",
            "naver_api_blog",
            "naver_api_news",
            "naver_api_webkr",
            "naver_html",
            "python_ddg",
            "python_ddg_art_domains",
            "python_ddg_art_context",
        ],
    )
    parser.add_argument(
        "--query-template-ids",
        nargs="+",
        default=[template_id for template_id, _template in QUERY_TEMPLATES],
        choices=[template_id for template_id, _template in QUERY_TEMPLATES],
    )
    parser.add_argument(
        "--merge-with-latest",
        action="store_true",
        help="Merge this run with the existing latest standardized search results before rebuilding the latest snapshot.",
    )
    parser.add_argument(
        "--replace-latest-providers",
        action="store_true",
        help="When merging, remove existing latest rows for providers in this run before appending new rows.",
    )
    parser.add_argument(
        "--drop-latest-providers",
        nargs="*",
        default=[],
        help="When merging, remove these provider rows from the existing latest standardized results.",
    )
    parser.add_argument("--sleep-seconds", type=float, default=0.35)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--snapshot-month", default=datetime.now().strftime("%Y-%m"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = time.time()
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    run_id = f"pp_h11_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    snapshot_year = int(str(args.snapshot_month).split("-")[0])
    collection_artist_df = select_artist_names(args.limit_artists, args.selection_policy, args.artist_scope)
    query_templates = [(template_id, template) for template_id, template in QUERY_TEMPLATES if template_id in set(args.query_template_ids)]
    raw_df = collect_raw_results(
        artist_df=collection_artist_df,
        providers=args.providers,
        query_templates=query_templates,
        max_results=args.max_results,
        sleep_seconds=args.sleep_seconds,
        timeout=args.timeout,
        run_id=run_id,
        snapshot_month=args.snapshot_month,
    )
    standard_df = standardize_results(raw_df, snapshot_year=snapshot_year)
    snapshot_artist_df = collection_artist_df
    if args.merge_with_latest and LATEST_STANDARDIZED_PATH.exists():
        existing = pd.read_csv(LATEST_STANDARDIZED_PATH, low_memory=False)
        drop_providers = set(args.drop_latest_providers)
        if args.replace_latest_providers:
            drop_providers.update(args.providers)
        if drop_providers and "provider" in existing.columns:
            existing = existing[~existing["provider"].astype(str).isin(drop_providers)].copy()
        standard_df = pd.concat([existing, standard_df], ignore_index=True, sort=False)
        dedupe_cols = [
            "artist_search_name",
            "provider",
            "query_template_id",
            "rank",
            "url",
            "title",
        ]
        standard_df = standard_df.drop_duplicates(
            subset=[col for col in dedupe_cols if col in standard_df.columns],
            keep="last",
        ).reset_index(drop=True)
        snapshot_artist_df = merge_artist_selection_with_latest(collection_artist_df)
    snapshot_df = build_snapshot(standard_df, snapshot_artist_df)
    metric_providers = sorted(standard_df["provider"].dropna().astype(str).unique()) if "provider" in standard_df.columns else args.providers
    metrics_df = build_metrics(standard_df, standard_df, snapshot_df, metric_providers, args.max_results)
    run_config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "collector_run_id": run_id,
        "run_started_at": datetime.fromtimestamp(start).isoformat(timespec="seconds"),
        "run_finished_at": datetime.now().isoformat(timespec="seconds"),
        "seconds": round(time.time() - start, 2),
        "seed": SEED,
        "snapshot_month": args.snapshot_month,
        "selection_policy": args.selection_policy,
        "artist_scope": args.artist_scope,
        "limit_artists": args.limit_artists,
        "selected_artist_n": int(len(collection_artist_df)),
        "snapshot_artist_n": int(len(snapshot_artist_df)),
        "providers": ", ".join(args.providers),
        "query_templates": ", ".join(template_id for template_id, _template in query_templates),
        "merge_with_latest": bool(args.merge_with_latest),
        "replace_latest_providers": bool(args.replace_latest_providers),
        "drop_latest_providers": ", ".join(args.drop_latest_providers),
        "max_results_per_query": args.max_results,
        "sleep_seconds": args.sleep_seconds,
        "timeout": args.timeout,
        "latest_snapshot_path": str(LATEST_SNAPSHOT_PATH.relative_to(REPO)),
        "note": "Use naver_api_blog/naver_api_news/naver_api_webkr when NAVER_CLIENT_ID/NAVER_CLIENT_SECRET are present. Use python_ddg/python_ddg_art_context as reusable no-key library providers. python_ddg_art_domains is a stricter diagnostic provider and may be sparse. google_cse requires GOOGLE_API_KEY/GOOGLE_CSE_ID but may be unavailable for new Google projects. HTML providers remain pilot fallbacks.",
    }
    write_outputs(raw_df, standard_df, snapshot_df, metrics_df, run_config)
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "seconds": run_config["seconds"],
        "selected_artist_n": int(len(collection_artist_df)),
        "snapshot_artist_n": int(len(snapshot_artist_df)),
        "request_n": int(len(raw_df.groupby(["artist_search_name", "provider", "query_template_id"]))),
        "summary": str((BASE_EXP_DIR / "PP-H11_operational_search_summary_metrics.csv").relative_to(REPO)),
        "latest_snapshot": str(LATEST_SNAPSHOT_PATH.relative_to(REPO)),
        "experiment_dir": str((BASE_EXP_DIR / EXP_SLUG).relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
