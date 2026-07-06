"""Artsy API 작가 프로필 + 전시 이력 수집.

URL: https://api.artsy.net/api
Docs: https://developers.artsy.net/

수집 항목:
- 작가 프로필 (국적, 생년, 사망년)
- 전시 이력 (전시 수, 기관전/갤러리전)
- 갤러리 소속 정보

Usage:
    # 먼저 Artsy 계정에서 Client ID/Secret 발급 필요
    export ARTSY_CLIENT_ID="your_client_id"
    export ARTSY_CLIENT_SECRET="your_client_secret"
    python scripts/collectors/collect_artsy.py --output data/artsy_artists.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

API_BASE = "https://api.artsy.net/api"
REQUEST_DELAY = 1.0


class ArtsyClient:
    """Artsy API 클라이언트."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None

    def _get_token(self) -> str:
        """OAuth2 토큰 발급."""
        if self._token:
            return self._token

        data = json.dumps({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }).encode()

        req = urllib.request.Request(
            f"{API_BASE}/tokens/xapp_token",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode())
        self._token = result["token"]
        logger.info("Artsy token acquired.")
        return self._token

    def _request(self, endpoint: str, params: dict | None = None) -> dict | None:
        """API 요청."""
        token = self._get_token()
        url = f"{API_BASE}{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        try:
            req = urllib.request.Request(url, headers={
                "X-Xapp-Token": token,
                "Accept": "application/vnd.artsy-v2+json",
            })
            resp = urllib.request.urlopen(req, timeout=15)
            return json.loads(resp.read().decode())
        except Exception as e:
            logger.warning("API request failed: %s — %s", endpoint, e)
            return None

    def search_artist(self, name: str) -> dict | None:
        """작가명으로 검색."""
        result = self._request("/search", {"q": name, "type": "artist"})
        if result and "_embedded" in result and "results" in result["_embedded"]:
            results = result["_embedded"]["results"]
            if results:
                return results[0]
        return None

    def get_artist(self, artist_id: str) -> dict | None:
        """작가 상세 정보."""
        return self._request(f"/artists/{artist_id}")

    def get_artist_shows(self, artist_id: str) -> list[dict]:
        """작가 전시 이력."""
        result = self._request("/shows", {"artist_id": artist_id, "size": 100})
        if result and "_embedded" in result and "shows" in result["_embedded"]:
            return result["_embedded"]["shows"]
        return []

    def collect_artist_profile(self, name: str) -> dict | None:
        """작가명 → 프로필 + 전시 이력 수집."""
        search = self.search_artist(name)
        if not search:
            return None

        # artist ID 추출
        links = search.get("_links", {})
        self_link = links.get("self", {}).get("href", "")
        if "/api/artists/" not in self_link:
            return None
        artist_id = self_link.split("/api/artists/")[-1]

        # 상세 정보
        artist = self.get_artist(artist_id)
        if not artist:
            return None

        # 전시 이력
        shows = self.get_artist_shows(artist_id)

        return {
            "artist_name_query": name,
            "artsy_id": artist_id,
            "artsy_name": artist.get("name", ""),
            "nationality": artist.get("nationality", ""),
            "birthday": artist.get("birthday", ""),
            "deathday": artist.get("deathday", ""),
            "hometown": artist.get("hometown", ""),
            "location": artist.get("location", ""),
            "exhibition_count": len(shows),
            "solo_show_count": sum(
                1 for s in shows
                if s.get("fair") is None and "solo" in s.get("name", "").lower()
            ),
            "institutional_show_count": sum(
                1 for s in shows if s.get("at_a_fair", False)
            ),
            "source": "artsy",
        }


def collect_all(
    artist_names: list[str],
    client_id: str,
    client_secret: str,
    output_path: str | Path,
) -> int:
    """전체 작가 프로필 수집."""
    client = ArtsyClient(client_id, client_secret)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for i, name in enumerate(artist_names):
        logger.info("[%d/%d] Collecting: %s", i + 1, len(artist_names), name)
        profile = client.collect_artist_profile(name)
        if profile:
            results.append(profile)
            logger.info("  → Found: %s (exhibitions: %d)",
                        profile["artsy_name"], profile["exhibition_count"])
        else:
            logger.info("  → Not found")
        time.sleep(REQUEST_DELAY)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("Saved %d profiles to %s", len(results), output_path)

    return len(results)


def main() -> None:
    """CLI 진입점."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    parser = argparse.ArgumentParser(description="Artsy API 작가 프로필 수집")
    parser.add_argument("--output", type=str, default="data/artsy_artists.json")
    parser.add_argument("--sample", type=int, default=0)
    args = parser.parse_args()

    client_id = os.environ.get("ARTSY_CLIENT_ID", "")
    client_secret = os.environ.get("ARTSY_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        logger.error(
            "ARTSY_CLIENT_ID와 ARTSY_CLIENT_SECRET 환경변수를 설정하세요.\n"
            "Artsy 개발자 포털에서 발급: https://developers.artsy.net/"
        )
        return

    # K-Auction 작가 리스트
    import pandas as pd
    works_path = Path("data/k-auction-works-20260325.csv")
    df = pd.read_csv(works_path, encoding="utf-8-sig")
    artists = sorted(df["작가"].dropna().unique().tolist())
    logger.info("Loaded %d artists", len(artists))

    if args.sample > 0:
        artists = artists[:args.sample]

    collect_all(artists, client_id, client_secret, args.output)


if __name__ == "__main__":
    main()
