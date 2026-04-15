# Artsy 한국 작가 데이터 수집 결과 정리

## 1. 수집 방식

Artsy의 공개 GraphQL API(`metaphysics-cdn.artsy.net/v2`)를 직접 호출하여 수집.
**Playwright 불필요** — 순수 Python HTTP 요청만으로 가능.

| 항목 | 내용 |
|------|------|
| 엔드포인트 | `https://metaphysics-cdn.artsy.net/v2` (POST, GraphQL) |
| 인증 | 불필요 (공개 API) |
| 페이지네이션 | 커서 기반, 100건/페이지 |
| 속도 | ~28건/초 |
| 전체 수집 예상 시간 | **~18분** (31,044건) |
| 스크립트 | `scripts/crawl_artsy_graphql.py` |


## 2. 수집 대상

**검색 조건:**
- 국적: South Korean, Korean
- 갤러리 위치: Seoul + Busan
- 총 **31,044건** 작품

**이 가격은 1차 시장(갤러리) 판매 가격이다.**
경매 낙찰가가 아니라, 갤러리가 Artsy를 통해 직접 판매하는 가격.
"Purchase" 버튼으로 바로 구매 가능한 실제 판매가.


## 3. 수집 가능 필드

### 3.1 작품 데이터

| 필드 | 예시 | 수집률 |
|------|------|--------|
| 작품 제목 (title) | "Wave of Still Life" | 100% |
| 제작 연도 (date) | "2025" | 100% |
| **가격 (saleMessage)** | "US$241", "KRW ₩18,000,000" | **77%** |
| **크기 (dimensions.cm)** | "27.3 × 22 × 3 cm" | **99%** |
| 매체 (medium) | "Oil on canvas" | 98% |
| 카테고리 (category) | "Painting", "Sculpture" | 99% |
| 유니크/에디션 | "Unique work", "Edition of 30" | 있음 |
| 갤러리명 | "galerie bruno massa" | 99% |

### 3.2 가격 통화 분포 (500건 테스트 기준)

| 통화 | 건수 | 비율 |
|------|------|------|
| **USD** | 384건 | 76.8% |
| **KRW (₩)** | 55건 | 11.0% |
| GBP (£) | 45건 | 9.0% |
| EUR (€) | 6건 | 1.2% |
| Price on request | 10건 | 2.0% |

**통화 처리 방안:**
- USD: 기본 통화, 환율 변환 없이 사용
- KRW: `KRW ₩18,000,000` → 18,000,000원으로 파싱
- GBP/EUR: 수집 시점 환율로 USD 변환
- "Price on request": null 처리 (학습 제외)

### 3.3 작품 크기 데이터

**수집률: 99%** — 거의 모든 작품에 cm 단위 크기 포함.

```
형식 예시:
  2D: "90.9 × 60.6 cm"           → width=90.9, height=60.6
  3D: "27.3 × 22 × 3 cm"         → width=27.3, height=22, depth=3
  원형: "diameter 71cm"           → diameter=71
```

**파싱 후 생성 가능한 피처:**
- `width_cm`, `height_cm`, `depth_cm`
- `area_cm2` = width × height
- `ho` = area_to_ho(area_cm2)  (호수 변환)
- `orientation` = height/width (세로/가로 비율)
- `is_3d` = depth 존재 여부

### 3.4 작가 프로필 데이터

| 필드 | 예시 | 설명 |
|------|------|------|
| 이름 (name) | "Sa Hara" | 영문 이름 |
| slug | "sa-hara" | Artsy 고유 ID |
| 국적/생년 | "Korean, b. 1975" | 파싱 → nationality, birth_year |
| 총 작품 수 | 44 | Artsy 등록 작품 |
| 판매중 작품 | 36 | 현재 판매 가능 |
| 팔로워 수 | 2,273 | Artsy 내 팔로워 |

### 3.5 작가 전시 이력 (showsConnection)

| 필드 | 예시 |
|------|------|
| 전시명 | "Kukje Gallery at Art Basel" |
| 유형 (kind) | solo / group / fair |
| 기간 | start_at, end_at |
| 도시 | "Seoul", "Hong Kong" |
| 갤러리/기관 | "Kukje Gallery" |

**전시 데이터 상위 작가:**

| 작가 | 국적/생년 | solo | group | fair | total | followers |
|------|----------|------|-------|------|-------|-----------|
| 전광영 | South Korean, b.1944 | 2 | 19 | 62 | 83 | 2,273 |
| 백남준 | 1932-2006 | 7 | 32 | 37 | 76 | 3,510 |
| 이우환 | Korean, b.1936 | 5 | 29 | 30 | 64 | 9,100 |
| 박서보 | 1931-2023 | 2 | 9 | 50 | 61 | 4,890 |
| 김창열 | 1929-2021 | 3 | 11 | 27 | 41 | 2,106 |
| 하종현 | b.1935 | 4 | 5 | 29 | 38 | 3,555 |
| 이배 | b.1956 | 2 | 12 | 22 | 36 | 3,127 |


## 4. 카테고리 및 매체 분포

### 카테고리

| 카테고리 | 건수 |
|----------|------|
| Painting | 394 |
| Print | 33 |
| Sculpture | 27 |
| Mixed Media | 17 |
| Photography | 15 |
| Drawing/Collage | 11 |

### 주요 매체

| 매체 | 건수 |
|------|------|
| Oil on canvas | 76 |
| Acrylic on canvas | 51+13 |
| Color on Korean paper | 23 |
| Ink and color on Korean paper | 12 |
| Mixed media on canvas | 8 |
| Pigments on Jangji (장지) | 8 |


## 5. 1차 시장 가격 예측 모델에 활용

### 5.1 Artsy 데이터로 생성 가능한 피처

```
작품 피처:
  - width_cm, height_cm → area → ho (호수)
  - medium_category (유채/아크릴/수묵채색/혼합)
  - support_type (canvas/Korean paper/panel/linen)
  - category (Painting/Sculpture/Print)
  - is_unique (유니크 vs 에디션)
  - year (제작 연도)

작가 피처:
  - birth_year → career_age
  - artsy_followers (팔로워 수 = 시장 관심도)
  - total_works (총 작품 수 = 생산성)
  - for_sale_ratio (판매중/총 = 수요 지표)
  - solo_show_count, group_show_count, fair_count
  - institutional_score (전시 기관 가중합)

갤러리 피처:
  - gallery_name → gallery_tier (갤러리 등급)
  - gallery_location (서울/부산/해외)
```

### 5.2 K-ARTMARKET 경매 데이터와의 차이

| 항목 | Artsy (1차 시장) | K-ARTMARKET (2차 시장) |
|------|------------------|----------------------|
| 가격 성격 | 갤러리 판매가 | 경매 낙찰가 |
| 데이터 규모 | 31,044건 | 103,694건 |
| 작가 풀 | 현역 + 갤러리 소속 | 경매 등장 (원로 중심) |
| 가격 통화 | USD/KRW/EUR 혼재 | KRW 단일 |
| 프로필 연결 | 같은 플랫폼 (slug 키) | 이름 매칭 필요 |
| 크기 데이터 | 99% 포함 | 포함 |
| 매체 데이터 | 상세 (영문) | 상세 (한글) |

**핵심 장점:** Artsy는 가격과 프로필이 **같은 플랫폼**에 있어서 이름 매칭 문제가 없음.


## 6. 전체 수집 계획

### 6.1 작품 수집 (전체 31K건)

```python
# scripts/crawl_artsy_graphql.py에서 max_pages=0으로 변경
artworks, artists = collect_artworks(max_pages=0)  # 전체 수집
```

- 예상 시간: ~18분
- 예상 작가: ~9,700명
- 예상 가격 있는 작품: ~24,000건 (77%)

### 6.2 작가 프로필 수집 (상위 작가)

```python
# 작품 10건 이상인 작가만 전시 이력 수집
active_slugs = [a["slug"] for a in artists_list if a["total_works"] >= 10]
shows = collect_artist_shows(active_slugs)
```

- 예상 대상: ~1,000-2,000명
- 예상 시간: ~30분 (0.5초/작가)

### 6.3 통화 정규화

```python
def normalize_price_to_krw(price_str: str, fx_rates: dict) -> int | None:
    """가격 문자열을 KRW로 통일."""
    if "KRW" in price_str or "₩" in price_str:
        return parse_number(price_str)
    elif "US$" in price_str:
        return int(parse_number(price_str) * fx_rates["USD_KRW"])
    elif "£" in price_str:
        return int(parse_number(price_str) * fx_rates["GBP_KRW"])
    elif "€" in price_str:
        return int(parse_number(price_str) * fx_rates["EUR_KRW"])
    return None  # "Price on request", "Sold" 등
```


## 7. 결론

Artsy GraphQL API는 1차 시장 가격 예측에 필요한 **모든 핵심 데이터**를 제공한다:

- **가격**: 갤러리 판매가 (1차 시장), 77% 수집률
- **크기**: cm 단위, 99% 수집률 → 호수 변환 가능
- **매체/형태**: 상세 영문 매체 정보
- **작가 프로필**: 전시 이력, 팔로워, 작품수
- **갤러리**: 갤러리명, 위치

31,044건 전체 수집에 약 18분 소요. 기존 접근법(KADA→K-ARTMARKET→Artsy 크로스 매칭)보다
**단일 소스에서 가격+프로필+작품을 모두 확보**할 수 있어 훨씬 효율적.
