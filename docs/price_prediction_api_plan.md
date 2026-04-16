# VisionAI 1차 시장 가격 예측 API 서비스 기획

> **작성일**: 2026-04-16
> **버전**: v1.5 (코덱스 리뷰 5회 반영, Phase 1 구현 스펙 분리)
> **목적**: 한국 신진/중견 작가의 1차 시장(갤러리) 작품 가격을 예측하는 API 서비스

---

## 1. 서비스 개요

### 1.1 목적

갤러리, 아트 플랫폼, 작가가 작품의 적정 가격을 산출할 수 있는 AI 가격 예측 API.

최소 입력(작가명, 작품 크기, 매체)만으로 외부 소스에서 작가 프로필을 자동 수집하고, 머신러닝 모델로 예측 가격과 예측 범위를 반환한다.

**대상 작품**: 2D 회화 (painting). 조각, 설치, 에디션 프린트는 v1 범위 밖.

**가격 기준**: 학습 데이터는 Artsy(갤러리), Artue(갤러리), Saatchi(온라인 직거래) 혼합. Saatchi는 갤러리 대비 30~50% 저렴하므로, 예측 시 source별 가격 수준 보정을 적용한다.

### 1.2 대상 사용자

| 사용자 | 용도 |
|--------|------|
| 갤러리 | 신규 작가 가격 책정, 기존 작가 가격 조정 참고 |
| 아트 플랫폼 | 리스팅 시 자동 추천 가격 |
| 작가 | 작품 크기/매체별 시장 적정가 확인 |
| 컬렉터 | 구매 전 가격 타당성 검증 |

### 1.3 핵심 가치

- **최소 입력**: 작가명 + 크기 + 매체만으로 예측 가능
- **외부 정보 자동 수집**: Artsy, Saatchi Art, 웹검색에서 작가 프로필 자동 보강
- **신뢰도 등급**: 예측의 신뢰도를 A~D로 표시, 예측 범위 함께 제공 (주관적 밴드, 교정된 통계적 구간은 아님)
- **학습 작가 매칭**: 29,361건 학습 데이터에서 작가 자동 매칭 시 고정밀 예측

---

## 2. 현재 모델 성능

### 2.1 학습 데이터

| 소스 | 건수 | 작가 | 가격 중앙 | 특성 |
|------|:----:|:----:|:---------:|------|
| Artsy | 7,551 | 757 | 414만원 | 국제 갤러리, 전시 이력 풍부 |
| Artue | 2,756 | 363 | 279만원 | 한국 신진 작가, KRW |
| Saatchi Art | 21,721 | 832 | 256만원 | 온라인 직거래, USD |
| **합계** | **29,361** | **1,589** | **300만원** | |

### 2.2 모델 구조 (v3)

```
입력 (작가명, 크기, 매체, 프로필 정보)
  │
  ├─ 학습된 작가 매칭?
  │   ├─ Yes → XGBoost — MdAPE 11.7%, W30 78.8%
  │   └─ No  → CatBoost 앙상블 — MdAPE 38.7%, W30 40.1%
  │
  └─ 출력: 예측 가격 + 신뢰 구간 + 신뢰도 등급
```

### 2.3 피처 중요도 (상위 10)

| 순위 | 피처 | 중요도 | 카테고리 |
|:----:|------|:------:|----------|
| 1 | artist_total_works | 37.1% | 작가 — 총 작품수 |
| 2 | ln_followers | 10.0% | 작가 — 팔로워 |
| 3 | profile_completeness | 8.4% | 작가 — 프로필 충실도 |
| 4 | artist_birth_year | 7.1% | 작가 — 생년 |
| 5 | area_cm2 | 5.7% | 크기 — 면적 |
| 6 | ln_area | 3.7% | 크기 — log 면적 |
| 7 | ln_ho | 3.1% | 크기 — log 호수 |
| 8 | ho_price_level | 2.9% | 호수별 가격 매핑 |
| 9 | has_birth_year | 2.2% | 생년 유무 |
| 10 | ho_x_support | 2.0% | 호수 x 지지체 계수 |

**카테고리별**: 작가 프로필 68.2%, 크기/호수 21.1%, 매체/컨텍스트 7.7%, 갤러리 2.4%

### 2.4 가격대별 정확도 (GroupKFold)

| 가격대 | MdAPE | 비율 | W30 | 건수 |
|--------|:-----:|:----:|:---:|:----:|
| ~100만 | 51.6% | 1.51x | 33% | 5,977 |
| **100~300만** | **36.6%** | 1.19x | **44%** | 9,036 |
| **300~500만** | **31.0%** | **1.05x** | **49%** | 4,524 |
| 500~1천만 | 32.9% | 0.89x | 46% | 4,827 |
| 1천~3천만 | 35.9% | 0.71x | 40% | 3,319 |
| 3천만+ | 88.8% | 0.11x | 9% | 1,678 |

---

## 3. API 아키텍처

### 3.1 전체 데이터 흐름

```
[클라이언트]
    │
    ▼
[API Gateway]  POST /api/v1/predict
    │
    ├─ 1. 입력 검증 (Pydantic)
    │   └─ 작가명, 크기, 매체 (필수) + 생년, 전시 등 (선택)
    │
    ├─ 2. 작가 매칭
    │   ├─ 학습 DB 매칭 (1,589명, fuzzy match 0.85+)
    │   └─ 매칭 실패 → 외부 수집 트리거
    │
    ├─ 3. 외부 정보 수집 (캐시 우선, 미스 시 동기 수집)
    │   ├─ 캐시 히트 → 즉시 사용 (< 10ms)
    │   ├─ 캐시 미스 → Artsy GraphQL (작품수, 팔로워, 전시)
    │   ├─ 캐시 미스 → Saatchi 프로필 (bio, exhibitions, 팔로워)
    │   └─ 생년 미확보 시 → 웹검색 (조건부, 타임아웃 2초)
    │
    ├─ 4. 피처 생성
    │   ├─ 크기 → 호수 변환 (dimension_parser)
    │   ├─ 매체 → 카테고리 분류 (medium_parser)
    │   ├─ 작가 → 프로필 피처 (career_stage, birth_year 등)
    │   └─ 37개 피처 생성
    │
    ├─ 5. 모델 예측
    │   ├─ 학습 작가 → XGBoost (MdAPE 11.7%)
    │   └─ Cold Start → CatBoost 앙상블 + source ratio 보정 (MdAPE 38.7%)
    │
    └─ 6. 응답 생성
        ├─ 예측 가격 (KRW). USD는 고정 환율 ₩1,380/$1 적용
        ├─ 예측 범위 (하한~상한, 등급별 마진 기반)
        ├─ 신뢰도 등급 (A/B/C/D)
        └─ 수집된 작가 프로필 요약
```

### 3.2 시스템 구성도

```
┌─────────────────────────────────────────────────┐
│                  FastAPI Server                  │
├─────────────────────────────────────────────────┤
│                                                  │
│  [Startup]                                       │
│  ├─ CatBoost v3 모델 로드                          │
│  ├─ XGBoost v3 모델 로드                           │
│  ├─ 학습 작가 인덱스 (1,589명) 로드                   │
│  └─ 호수/매체 가격 레벨 테이블 로드                      │
│                                                  │
│  [Endpoints]                                     │
│  ├─ POST /api/v1/predict        단건 예측           │
│  ├─ POST /api/v1/predict/batch  다건 예측 (Phase 3)  │
│  ├─ GET  /api/v1/artist/{name}  작가 조회           │
│  ├─ GET  /api/v1/model/info     모델 정보           │
│  ├─ POST /api/v1/training-data  학습 데이터 적재      │
│  └─ GET  /health                헬스체크             │
│                                                  │
│  [Services]                                      │
│  ├─ ArtistMatcher      학습 DB 매칭                 │
│  ├─ ExternalCollector   외부 정보 수집               │
│  │   ├─ ArtsyClient    GraphQL API                │
│  │   ├─ SaatchiClient  프로필 크롤링                 │
│  │   └─ WebSearcher    웹검색 (생년/이력)             │
│  ├─ FeatureBuilder     37개 피처 생성                │
│  ├─ PricePredictor     모델 라우팅 + 예측             │
│  └─ ConfidenceGrader   신뢰도 등급 산정               │
│                                                  │
│  [Cache]                                         │
│  └─ 작가 프로필 캐시 (TTL 24h)                       │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 4. 외부 정보 수집 파이프라인

### 4.1 수집 소스 및 피처 기여

| 소스 | 수집 정보 | 피처 기여 | 동명이인 리스크 | 응답 시간 |
|------|----------|----------|:-------------:|:---------:|
| **학습 DB** | 가격 이력, 통계 | 전체 피처 | 없음 (ID 기반) | < 10ms |
| **Artsy GraphQL** | 작품수, 팔로워, 국적, 전시, 생년 | 37.1% + 10.0% + 7.1% | 낮음 (slug 유일) | ~500ms |
| **Saatchi 프로필** | bio, education, exhibitions, 팔로워 | 8.4% + 10.0% | 낮음 (ID 유일) | ~1s |
| **웹검색** | 생년, 학력, 전시 (보완용) | 7.1% + 2.2% | **높음** | ~2s |

> **소스 선정 기준**: KADA/KAP 등 공공 DB와 갤러리 사이트 직접 파싱을 검토했으나, 공개 API 미제공, 작가 수 부족(DA-Arts 500명), 서비스 중단(뮤움) 등으로 현시점에서 실용적이지 않아 제외했다. 향후 공공 데이터 API가 정비되면 추가 검토.

### 4.2 소스별 상세

#### A. Artsy GraphQL API

```graphql
# Step 1: 작가 검색 (이름 → slug)
query SearchArtist($query: String!) {
  searchConnection(query: $query, first: 5, entities: [ARTIST]) {
    edges {
      node {
        ... on SearchableItem {
          slug
          displayLabel
          description    # 국적, 생년 포함
        }
      }
    }
  }
}

# Step 2: 프로필 수집 (slug → 상세)
query ArtistProfile($slug: String!) {
  artist(id: $slug) {
    name, nationality, birthday, gender, hometown
    counts { artworks, follows, forSaleArtworks }
    showsConnection(first: 100) {
      edges { node { name, startAt, kind, partner { name, cities } } }
    }
  }
}
```

- **엔드포인트**: `https://metaphysics-cdn.artsy.net/v2` (공개, 무인증)
- **Rate Limit**: ~100 req/min
- **검색 → 매칭**: 검색 결과 5건 중 이름 fuzzy 0.85+ 매칭 확인
- **수집 피처**: artist_total_works, ln_followers, solo_count, group_count, fair_count, career_age, artist_birth_year, nationality

#### B. Saatchi Art 프로필

- **Step 1**: Constructor.io API로 작가 작품 검색
  ```
  GET ac.cnstrc.com/autocomplete/{artist_name}?key=key_cn3mctZ73MD3U2jM
  ```
- **Step 2**: 검색 결과에서 artist_id 추출 → 프로필 페이지 파싱
  ```
  GET saatchiart.com/account/profile/{artist_id} → __NEXT_DATA__ JSON
  ```
- **수집 필드**: bio, education, exhibitions, events, followers, total_artworks, badges
- **NLP 추출**: bio에서 생년, exhibitions에서 개인전/단체전 횟수

#### C. 웹검색 (보완용, 동명이인 처리 포함)

Artsy/Saatchi에서 충분한 정보가 확보되지 않을 때만 사용.

**검색 쿼리 설계** (정밀도 우선):
```
# 한국어 검색 (네이버)
"{작가명}" 작가 회화 생년 이력
"{작가명}" 작가 전시 개인전

# 영어 검색 (구글)
"{artist_name}" artist painter born Korea
"{artist_name}" artist CV exhibitions
```

**동명이인 구분 전략**:

웹검색의 가장 큰 리스크는 동명이인. "김현수"를 검색하면 화가, 배우, 가수가 모두 나온다.

| 단계 | 방법 | 설명 |
|:----:|------|------|
| 1 | **검색어 특화** | `"{이름}" 작가 회화` 등 직업+분야 한정어 필수 포함 |
| 2 | **맥락 키워드 검증** | 검색 결과 페이지에 미술 관련 키워드 존재 여부 확인 |
| | | 필수 포함: `전시`, `갤러리`, `painting`, `exhibition`, `gallery` 중 1개+ |
| | | 제외: `배우`, `가수`, `영화`, `드라마`, `actor`, `singer` |
| 3 | **생년 범위 검증** | 추출된 생년이 1930~2005 범위인지 검증 |
| 4 | **다중 소스 교차** | 2개 이상의 **독립 도메인** 페이지에서 동일 생년이 나와야 채택 (동일 bio 복사본 제외) |
| 5 | **채택/기각 판정** | 위 4단계를 모두 통과하면 채택, 아니면 기각 (생년 NaN 유지). 점수화하지 않고 pass/fail 이진 판정 |

> 매체 교차 검증(입력 매체가 웹 결과에서도 언급되는지)은 신뢰도가 낮아 제외. 많은 작가 CV에는 매체가 명시되지 않으므로 false negative가 높다.

**동명이인 판정 예시**:
```
입력: "김현수", medium: "oil on canvas"

검색 결과 1: "김현수 배우 드라마 출연작" → 제외 (미술 키워드 없음)
검색 결과 2: "김현수 작가 갤러리 전시" → 후보
  → 페이지에 "개인전 5회", "갤러리 전시" 언급 → 미술 키워드 통과
  → "1978년생" 추출 → 범위 통과
검색 결과 3: "김현수 화가 1978 서울대 미대" → 후보 (독립 도메인)
  → 생년 "1978" 일치 → 다중 소스 교차 통과 → 채택
```

**파싱 우선순위 (신뢰도 순)**:
1. 네이버 인물정보 (구조화, 직업 분류 있음) → 동명이인 구분 용이
2. 위키피디아/나무위키 (검증된 정보, 분류 태그로 직업 확인)
3. 갤러리/미술관 작가 소개 페이지 (직업 오분류 리스크 없음)
4. 블로그/기사 (직접 파싱, 동명이인 리스크 높음 → 교차 검증 필수)

**웹검색 구현 방법**:
- **검색 API**: SerpAPI, Google Custom Search API, 또는 Naver Search API 사용 (스크래핑 아님)
- **비용**: SerpAPI 월 100건 무료, Google CSE 하루 100건 무료 → Cold Start 작가 대상이므로 충분
- **대체**: API 미사용 시 Phase 3+ 으로 이동, Artsy/Saatchi 2개 소스만으로 서비스

**Artsy/Saatchi 검색 시 동명이인 리스크**:
Artsy slug, Saatchi artist_id는 유일하지만, **이름→slug/ID 매칭 단계**에서 오매칭 가능.
- Artsy searchConnection은 여러 결과 반환 → 상위 결과의 nationality가 "Korean"인지 확인
- Saatchi Constructor.io 검색 → country가 "south korea"인 결과만 사용
- 매칭된 작가의 ID를 영구 저장 시 **수동 검증 플래그** 추가 (자동 매칭 vs 검증 완료 구분)

### 4.3 효율적 수집 전략

#### 수집 우선순위 (비용 대비 피처 기여도)

```
작가명 입력
  │
  ├─ 1. 학습 DB 매칭 (< 10ms, 피처 100%)
  │   ├─ 매칭 → 즉시 예측 가능
  │   └─ 미매칭 → 아래 순서로 수집 (병렬)
  │
  ├─ 2. [병렬] Artsy 검색 (~500ms, 피처 기여 ~49%)
  │   ├─ searchConnection으로 slug 확보
  │   ├─ 이름 fuzzy 매칭 확인 (0.85+)
  │   └─ 프로필 + 전시 수집
  │   ★ 가장 효율적: 작품수(37.1%) + 팔로워(10.0%) + 생년(7.1%) 한번에
  │
  ├─ 3. [병렬] Saatchi 검색 (~1s, 피처 기여 ~18%)
  │   ├─ Constructor.io autocomplete로 artist_id 확보
  │   └─ 프로필 파싱 (bio, education, exhibitions)
  │   ★ profile_completeness(8.4%) + 팔로워(10.0%)
  │
  ├─ 4. [조건부] 웹검색 (~2s, 생년 미확보 시에만)
  │   ├─ 동명이인 필터링 적용
  │   ├─ 다중 소스 교차 검증
  │   └─ 다중 소스 교차 통과 시만 채택 (pass/fail)
  │
  └─ 6. 정보 병합 → 충돌 해결 → 피처 생성 → 예측
```

#### 정보 충돌 해결 규칙

여러 소스에서 같은 피처(예: 생년)가 수집될 때:

| 우선순위 | 소스 | 이유 |
|:--------:|------|------|
| 1 | 학습 DB | 이미 검증된 데이터 |
| 2 | Artsy | 작가 본인이 등록한 공식 프로필 |
| 3 | Saatchi | 작가 본인 등록이지만 검증 수준 낮음 |
| 4 | 웹검색 | 동명이인 리스크, 교차 검증 필수 |

**불일치 시**: 상위 우선순위 값을 채택. 단, 생년이 3년 이상 차이나면 동명이인 가능성으로 판단하고 해당 소스 버림.

### 4.4 캐싱 설계

- **성공 캐시**: Artsy 24h, Saatchi 24h, 웹검색 7d
- **네거티브 캐시**: 검색 실패 시 1h (불필요한 재시도 방지)
- **Stale-on-error**: 외부 소스 장애 시 만료된 캐시라도 사용
- **사전 수집**: 학습 작가 1,589명의 외부 프로필은 배치 스크립트로 사전 수집 후 캐시 파일로 번들 (서버 시작 시 파일 로드, 외부 호출 없음)
- **배치 사전 수집**: 새 작가 데이터 학습 시, 외부 프로필도 함께 수집하여 캐시에 적재

### 4.5 수집 효율 최적화

| 방법 | 효과 |
|------|------|
| **병렬 수집** | Artsy + Saatchi 동시 호출 → 총 ~1s (직렬 1.5s 대비 30% 절감) |
| **조건부 웹검색** | 생년 미확보 시에만 → 불필요한 호출 80% 절감 |
| **배치 사전 수집** | 모델 재학습 시 외부 프로필 일괄 수집 → 서빙 시 캐시 히트율 90%+ |
| **점진적 보강** | 첫 요청은 캐시 미스로 3초, 이후 동일 작가 < 100ms |
| **작가 ID 매핑 테이블** | 한번 매칭된 작가의 Artsy slug / Saatchi ID 영구 저장 → 재검색 불필요 |

---

## 5. API 스펙

### 5.1 단건 예측

```
POST /api/v1/predict
```

**Request:**
```json
{
  "artist_name": "김선우",
  "width_cm": 72.7,
  "height_cm": 60.6,
  "medium": "acrylic on canvas",
  
  // 선택 (자동 수집 또는 수동 입력)
  "artist_birth_year": null,
  "artist_total_works": null,
  "solo_count": null,
  "group_count": null,
  "fair_count": null,
  "followers": null,
  "education": null,
  "exhibitions": null,
  "gallery_name": null,
  
  // 옵션
  "skip_external_lookup": false,
  "target_market": "gallery",    // "gallery" | "online" — source ratio 보정 기준
  "currency": "KRW"
}
```

**Response:**
```json
{
  "status": "success",
  "prediction": {
    "price_krw": 3210000,
    "price_usd": 2326,
    "price_range": {
      "low": 2247000,
      "high": 4173000
    },
    "confidence_grade": "B",
    "confidence_description": "외부 프로필 기반 예측, 오차 ±30% 내외"
  },
  "model_info": {
    "model_type": "cold_start_catboost_v3",
    "is_known_artist": false,
    "artist_matched_in_db": false,
    "feature_completeness": 0.78
  },
  "artist_profile": {
    "source": ["artsy", "saatchi"],
    "birth_year": 1985,
    "total_works": 120,
    "followers": 450,
    "solo_count": 8,
    "group_count": 15,
    "career_stage": 2,
    "profile_completeness": 3
  },
  "processing": {
    "total_ms": 1250,
    "db_lookup_ms": 5,
    "artsy_ms": 480,
    "saatchi_ms": 720,
    "web_search_ms": 0,
    "prediction_ms": 15
  }
}
```

### 5.2 다건 예측 (Phase 3)

```
POST /api/v1/predict/batch
```

**Request:**
```json
{
  "artworks": [
    {"artist_name": "김선우", "width_cm": 72.7, "height_cm": 60.6, "medium": "acrylic on canvas"},
    {"artist_name": "유선태", "width_cm": 53, "height_cm": 45.5, "medium": "oil on canvas"}
  ],
  "skip_external_lookup": false
}
```

**Response:** `predictions` 배열로 반환.

### 5.3 작가 조회

```
GET /api/v1/artist/{artist_name}
```

학습 DB + 외부 소스에서 작가 프로필을 조회하여 반환. 예측 없이 프로필만 확인.

**Response:**
```json
{
  "artist_name": "유선태",
  "matched_in_db": true,
  "db_info": {
    "source": "artsy",
    "artworks_in_training": 70,
    "median_price_krw": 37853400
  },
  "external_info": {
    "artsy": {"total_works": 150, "followers": 2100, "shows": 45},
    "saatchi": {"total_works": 0, "followers": 0}
  }
}
```

### 5.4 에러 응답

```json
{
  "status": "error",
  "error_code": "INVALID_DIMENSIONS",
  "message": "크기는 1cm 이상, 500cm 이하여야 합니다.",
  "details": {"width_cm": 0.5, "min_required": 1.0}
}
```

| 에러 코드 | HTTP | 설명 |
|-----------|:----:|------|
| INVALID_DIMENSIONS | 400 | 크기 범위 초과 |
| INVALID_MEDIUM | 400 | 매체 파싱 실패 |
| EXTERNAL_PARTIAL | 200 | 외부 수집 일부 실패. 확보된 정보로 예측 진행, 응답에 `warnings` 포함 |
| MODEL_ERROR | 500 | 모델 예측 실패 |

---

## 6. 모델 라우팅

### 6.1 라우팅 규칙

```
작가명 → 학습 DB 매칭
  │
  ├─ 매칭 성공 + 학습 건수 ≥ 5건
  │   └─ XGBoost v3 — MdAPE 11.7%, W30 78.8%
  │       신뢰도: A (±20%)
  │
  ├─ 매칭 성공 + 학습 건수 < 5건
  │   └─ CatBoost v3 (작가 통계 반영)
  │       신뢰도: B (±30%)
  │
  ├─ 매칭 실패 + 외부 프로필 수집 성공
  │   └─ CatBoost v3 (외부 피처 반영)
  │       신뢰도: B~C (±30~50%)
  │
  └─ 매칭 실패 + 외부 수집 실패/부분 성공
      └─ CatBoost v3 (확보된 피처만으로 예측)
          신뢰도: C~D (±50~70%)
          외부 실패 시에도 예측은 진행, 등급만 하락 (404 반환 아님)
```

**source ratio 보정**: Cold Start 예측 후, 요청의 `target_market`(gallery/online)에 따라 log scale에서 보정 적용. Saatchi 학습 데이터의 과대 경향(1.078x)을 사후 차감.

### 6.2 신뢰도 등급

| 등급 | 조건 | 마진 | 의미 |
|:----:|------|:----:|------|
| **A** | 학습 작가, 5건+ 이력 | ±20% | 높은 신뢰도 |
| **B** | 학습 작가 소량 또는 외부 프로필 풍부 | ±30% | 보통 신뢰도 |
| **C** | 외부 프로필 일부만 확보 | ±50% | 참고용 |
| **D** | 프로필 없음, 크기/매체만 사용 | ±70% | 추정치 |

---

## 7. 외부 정보가 정확도에 미치는 영향

### 7.1 피처별 기여도와 외부 소스

| 피처 | 중요도 | 수집 소스 | Cold Start 시 |
|------|:------:|----------|:-------------:|
| artist_total_works | 37.1% | Artsy/Saatchi | 0 (기본값) → 수집 시 실제값 |
| ln_followers | 10.0% | Artsy/Saatchi | 0 → 수집 시 실제값 |
| profile_completeness | 8.4% | 모든 소스 | 0 → 최대 3 |
| artist_birth_year | 7.1% | Artsy/Saatchi/웹검색 | NaN → 수집 시 실제값 |
| has_birth_year | 2.2% | 위와 동일 | 0 → 1 |
| career_stage | 1.8% | 전시 횟수 기반 | 1 → 1~4 |

**외부 수집 효과**: 피처 완전도 0~30% → 70~90%로 향상 시, Cold Start MdAPE 38.7% → 추정 30~35%

### 7.2 외부 수집 유무에 따른 예측 차이 (예상)

| 시나리오 | 입력 | 예측 정확도 |
|----------|------|:---------:|
| 크기+매체만 | D등급 | MdAPE ~60% |
| + 생년 | C등급 | MdAPE ~50% |
| + 작품수/팔로워 | B등급 | MdAPE ~40% |
| + 전시 이력 | B등급 | MdAPE ~35% |
| 학습 작가 매칭 | A등급 | MdAPE ~12% |

---

## 8. 기존 코드 재사용

### 8.1 재사용 가능 모듈

| 모듈 | 경로 | 용도 | 수정 필요 |
|------|------|------|:---------:|
| dimension_parser | `src/.../preprocessing/dimension_parser.py` | 크기 파싱 (7패턴), 호수 변환 | 그대로 사용 |
| medium_parser | `src/.../preprocessing/medium_parser.py` | 매체/지지체 분류 | 그대로 사용 |
| artist_similarity | `src/.../features/artist_similarity.py` | K-NN 유사 작가 탐색 | 그대로 사용 |
| confidence_grade | `src/.../validation/confidence_grade.py` | 신뢰도 등급 산정 | 마진 로직 수정 |
| FastAPI server | `src/.../api/server.py` | 기존 경매용 서버 | **신규 작성 필요** (기존은 2차시장 전용) |
| schemas | `src/.../api/schemas.py` | Pydantic 모델 | **신규 작성 필요** (1차시장 스키마) |

> 기존 server.py는 경매(2차시장) 전용이라 1차시장 API는 별도 모듈로 신규 작성. FastAPI 프레임워크와 lifespan 패턴만 참고.

### 8.2 신규 개발 필요

| 모듈 | 역할 |
|------|------|
| `artist_matcher.py` | 학습 DB fuzzy 매칭 (rapidfuzz) |
| `external_collector.py` | Artsy/Saatchi/웹검색 비동기 수집 |
| `artsy_client.py` | Artsy GraphQL 실시간 조회 |
| `saatchi_client.py` | Saatchi 프로필 실시간 조회 |
| `web_searcher.py` | 웹검색 생년/이력 추출 |
| `profile_cache.py` | 작가 프로필 캐시 (Redis 또는 인메모리) |
| `primary_predictor.py` | v3 CatBoost + XGBoost 라우팅 |

---

## 9. 개선 로드맵

### Phase 1: API MVP (2주)

학습 작가 매칭 + 로컬 모델만. 외부 수집 없음.

**엔드포인트 (Phase 1 한정)**:
- `POST /api/v1/predict` — 단건 예측
- `GET /api/v1/model/info` — 모델 정보
- `GET /health` — 헬스체크

**범위 밖 (Phase 2+)**: `/predict/batch`, `/artist/{name}`, `/training-data`, 외부 수집, SHAP

#### Phase 1 Request

```json
{
  "artist_name": "김선우",        // 필수
  "width_cm": 72.7,              // 필수
  "height_cm": 60.6,             // 필수
  "medium": "acrylic on canvas", // 필수
  "target_market": "gallery",    // 선택. "gallery"(기본값) | "online"
  
  // 선택 (수동 입력, 미입력 시 DB 프로필 사용)
  "artist_birth_year": null,
  "artist_total_works": null,
  "solo_count": null,
  "group_count": null,
  "followers": null
}
```

> Phase 1에서는 `education`, `exhibitions`, `skip_external_lookup`을 받지 않음. 외부 수집 자체가 없으므로.

#### Phase 1 Response

```json
{
  "status": "success",
  "prediction": {
    "price_krw": 3210000,
    "price_usd": 2326,
    "price_range": { "low": 2568000, "high": 3852000 },
    "confidence_grade": "B",
    "margin": 0.20
  },
  "model_info": {
    "model_type": "xgboost_v3",
    "is_known_artist": true,
    "training_count": 15
  },
  "processing": { "total_ms": 45 }
}
```

#### Phase 1 신뢰도 결정 규칙 (결정적, 테스트 가능)

```python
def determine_confidence(is_matched: bool, training_count: int,
                         has_birth_year: bool, has_manual_profile: bool) -> tuple[str, float]:
    """(grade, margin) 반환."""
    if is_matched and training_count >= 5:
        return ("A", 0.20)
    if is_matched and training_count >= 1:
        return ("B", 0.30)
    if has_birth_year or has_manual_profile:
        return ("C", 0.50)
    return ("D", 0.70)
```

- `is_matched`: DB artists 테이블에서 fuzzy match 성공
- `training_count`: 매칭된 작가의 학습 데이터 건수
- `has_birth_year`: 요청에 birth_year 입력 또는 DB 프로필에 존재
- `has_manual_profile`: 요청에 total_works/solo_count/followers 중 1개 이상 입력

#### Phase 1 source ratio 보정 공식

```python
# Cold Start (CatBoost) 경로에서만 적용. XGBoost 경로는 보정 없음.
RATIO_CORRECTION = {
    "gallery": 0.0,        # 갤러리 가격 수준 = 학습 데이터 기준 그대로
    "online": -0.075,      # 온라인(Saatchi 등) = ln_price에서 0.075 차감 ≈ 7.2% 저렴
}

ln_price_corrected = ln_price_raw + RATIO_CORRECTION.get(target_market, 0.0)
predicted_krw = int(exp(ln_price_corrected))
```

> 0.075 = Saatchi median ratio 1.078의 log값. 실험에서 측정된 값 (docs/saatchi_integration_result.md 참고).

#### Phase 1 구현 목록 (2026-04-16 완료)

- [x] FastAPI 서버 (`src/visionai/price_engine/api/primary_server.py`)
- [x] 요청/응답 Pydantic 스키마 (`primary_schemas.py`)
- [x] 작가 매칭 (`artist_matcher.py`) — DB JOIN 쿼리 + rapidfuzz
- [x] 피처 빌더 (`primary_feature_builder.py`) — 37개 피처 생성
- [x] 모델 라우팅 + 예측 (`primary_predictor.py`)
- [x] 신뢰도 결정 (`determine_confidence()`)
- [x] source ratio 보정
- [x] Dockerfile.api + Dokploy 배포 → `visionai-api.ahto.city`
- [x] DB 생성 + 데이터 적재 (artists 1,589명, profiles 1,577건)
- [x] 테스트: 학습 작가/Cold Start/수동 프로필/online 마켓 모두 통과

#### Phase 1 배포 결과

| 항목 | 값 |
|------|-----|
| **URL** | https://visionai-api.ahto.city |
| **Dokploy** | dev.ahto.city, artsy-viewer 프로젝트 내 |
| **DB** | postgres-proxy → visionai_dev |
| **작가 로드** | 1,526명 (DB 1,589명 중 프로필 있는 작가) |
| **모델** | CatBoost v3 (6.2MB) + XGBoost v3 (9.9MB) |
| **응답 시간** | 3~80ms |

#### Phase 1 테스트 결과

| 테스트 | 예측 가격 | 모델 | 등급 | 마진 |
|--------|:---------:|:----:|:----:|:----:|
| Yoo Suntai (학습 70건, 10호 oil) | 579만원 | XGBoost | A | ±20% |
| 미학습 작가 (20호 acrylic) | 118만원 | CatBoost | D | ±70% |
| 미학습 + 수동 프로필 (1985생, solo 10회) | 312만원 | CatBoost | C | ±50% |
| Yoo Suntai online | 565만원 (-2.5%) | XGBoost | A | ±20% |

**범위 밖 (Phase 2+)**: 외부 수집, 배치 API, SHAP 설명, 이미지, training-data 적재

### Phase 2: 외부 수집 + 캐시 (3주)

- Artsy GraphQL 작가 검색 + 프로필 수집
  - 작가명 → slug 검색 API 개발 (match_artist GraphQL query)
  - 검색 실패 시 graceful degradation (등급만 하락)
- Saatchi Constructor.io 검색 + 프로필 수집
  - 작가명 → artist_id 검색 → __NEXT_DATA__ 파싱
- 캐시: 소스별 TTL, 네거티브 캐시, stale-on-error
- 외부 소스 장애 대응: 타임아웃 3초, 부분 수집으로 예측 진행
- Rate limit: Artsy 100/min, Saatchi 60/min

### Phase 3: 생년 보강 + 배치 + 설명 (3주)

- 웹검색으로 생년 보강 (조건부, Artsy/Saatchi에서 미확보 시)
- SHAP 기반 피처 기여도 (feature_contributions 응답에 추가)
- 배치 API (최대 50건, 작가 중복 제거, 부분 실패 허용)
- 모니터링: 예측 로그, 정확도 추적

### Phase 4: 학습 데이터 적재 + 수동 재학습 파이프라인 (3주)

신규 데이터를 즉시 학습하지 않고, **적재 → 검토 → 수동 재학습 → 검증 → 배포** 흐름.

- 신규 작가/작품 데이터 적재 테이블 (`training_candidates`)
- 적재된 데이터 검토 대시보드 (건수, 가격 분포, 소스별 현황)
- 수동 트리거 재학습 스크립트 (일정량 이상 적재 시 운영자가 판단)
- 재학습 후 기존 모델과 성능 비교 (MdAPE, W30 자동 리포트)
- 성능 개선 확인 시 → 모델 교체 (model_versions 활성화)
- 성능 악화 시 → 기존 모델 유지, 적재 데이터 재검토

### Phase 5: 이미지 피처 (4주)

- 작품 이미지 CLIP 임베딩 → 스타일 피처
- 교정된 prediction interval (conformal prediction)

### 외부 의존성 리스크

| 소스 | 리스크 | 대응 |
|------|--------|------|
| Artsy GraphQL | 무인증 공개 API, 정책 변경 가능 | 캐시 + graceful degradation |
| Saatchi __NEXT_DATA__ | Next.js 빌드 구조 변경 시 파싱 실패 | 파서 버전 관리 + 모니터링 |
| 웹검색 | 파싱 신뢰도 낮음, 오정보 가능 | 신뢰도 임계값 + 수동 검증 플래그 |

---

## 10. 데이터베이스 설계

### 10.1 DB 선택

**PostgreSQL** (postgres-proxy 경유, 사무실 인프라 가이드 준수)

| 환경 | DB명 | 접근 방법 |
|------|------|----------|
| 개발 | visionai_dev | `https://postgres-proxy.ahto.city/db/visionai_dev/query` |
| 운영 | visionai_prod | 동일 proxy 또는 직접 연결 |

```bash
# postgres-proxy를 통한 SQL 실행
curl -s -X POST "https://postgres-proxy.ahto.city/db/visionai_dev/query" \
  -H "x-api-key: {POSTGRES_PROXY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT * FROM artists LIMIT 10"}'

# 파라미터 바인딩 (SQL Injection 방지)
curl -s -X POST "https://postgres-proxy.ahto.city/db/visionai_dev/query" \
  -H "x-api-key: {POSTGRES_PROXY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT * FROM artists WHERE name_normalized = $1","params":["kim sunwoo"]}'
```

**환경변수**:
```env
POSTGRES_PROXY_URL=https://postgres-proxy.ahto.city
POSTGRES_PROXY_API_KEY={key}
VISIONAI_DB=visionai_dev
```

> DB 생성 완료 (`visionai_dev`). postgres-proxy 대시보드에서 "DB 전체 재감지" 후 사용 가능.

API 서비스에 필요한 데이터는 5가지: 작가 마스터, 외부 프로필 캐시, 예측 로그, 학습 후보 적재, 모델 메타.

### 10.2 테이블 설계

#### artists — 작가 마스터 (학습 작가 + 외부 매칭 작가)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| name | VARCHAR(200) | 대표 이름 |
| name_ko | VARCHAR(100) | 한글 이름 (nullable) |
| name_en | VARCHAR(100) | 영문 이름 (nullable) |
| name_normalized | VARCHAR(200) | 소문자 정규화 이름 (검색용) |
| name_variants | JSONB | 이름 변형 목록 (추가 매칭용) |
| birth_year | INT | 출생년도 (nullable) |
| nationality | VARCHAR(50) | 국적 |
| gender | VARCHAR(10) | |
| source | VARCHAR(20) | 최초 등록 소스 (artsy/saatchi/manual) |
| artsy_slug | VARCHAR(100) | Artsy 작가 slug (nullable, unique) |
| saatchi_id | INT | Saatchi artist_id (nullable, unique) |
| is_in_training | BOOLEAN | 학습 데이터에 포함 여부 |
| training_count | INT | 학습 데이터 내 작품 수 |
| is_verified | BOOLEAN | 수동 검증 완료 여부 (동명이인 확인) |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**인덱스**: `name_normalized` (pg_trgm GIN 인덱스, trigram 유사도 검색용), `name_en`, `name_ko`, `artsy_slug`, `saatchi_id`
**제약조건**: `CHECK (training_count >= 0)`, `UNIQUE (artsy_slug)` WHERE NOT NULL, `UNIQUE (saatchi_id)` WHERE NOT NULL
**초기 데이터**: 학습 작가 1,589명 + 외부 프로필만 있는 작가(Artsy 1,925 + Saatchi 1,161에서 학습 작가 제외한 나머지)
**중복 방지**: `name_normalized` + `birth_year` 복합으로 동일인 판단. 동시 요청 시 `INSERT ... ON CONFLICT DO NOTHING`

#### artist_profiles — 외부 수집 프로필 캐시

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| artist_id | INT FK | artists.id |
| source | VARCHAR(20) NOT NULL | CHECK IN ('artsy', 'saatchi', 'web') |
| birth_year_from_source | INT | 이 소스에서 추출한 생년 (nullable) |
| nationality_from_source | VARCHAR(50) | 이 소스에서 확인한 국적 |
| total_works | INT DEFAULT 0 | 총 작품 수 |
| followers | INT DEFAULT 0 | 팔로워 수 |
| solo_count | INT DEFAULT 0 | CHECK >= 0 |
| group_count | INT DEFAULT 0 | CHECK >= 0 |
| fair_count | INT DEFAULT 0 | CHECK >= 0 |
| career_stage | INT | CHECK BETWEEN 1 AND 4 |
| bio | TEXT | 약력 텍스트 |
| education | TEXT | 학력 |
| exhibitions | TEXT | 전시 이력 텍스트 |
| profile_completeness | INT DEFAULT 0 | CHECK BETWEEN 0 AND 3 |
| raw_data | JSONB | 원본 수집 데이터 전체 |
| status | VARCHAR(10) NOT NULL DEFAULT 'success' | CHECK IN ('success', 'failed', 'stale') |
| error_message | TEXT | 실패 시 에러 메시지 |
| retry_after | TIMESTAMPTZ | 실패 시 재시도 가능 시각 |
| fetched_at | TIMESTAMPTZ NOT NULL | 수집 시각 |
| expires_at | TIMESTAMPTZ NOT NULL | 캐시 만료 시각 |

**인덱스**: `(artist_id, source)` unique, `expires_at`, `status`

**캐시 동작**:
- 성공: `status='success'`, `expires_at`에 TTL 적용 (Artsy 24h, Saatchi 24h, web 7d)
- 실패 (네거티브 캐시): `status='failed'`, `retry_after`에 1h 후 설정
- Stale-on-error: 외부 장애 시 만료된 `status='success'` 행을 `status='stale'`로 변경 후 사용

**artists.birth_year 결정**: 소스 우선순위(학습DB > Artsy > Saatchi > web) 기준으로 `artist_profiles.birth_year_from_source` 중 최우선 값을 `artists.birth_year`에 반영. 캐시 만료 시 재수집 후 우선순위 재적용.

#### predictions — 예측 로그

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | 예측 ID |
| artist_id | INT FK | artists.id (nullable, 미매칭 시 null) |
| artist_name_input | VARCHAR(200) | 입력된 작가명 |
| width_cm | FLOAT | |
| height_cm | FLOAT | |
| ho | INT | 호수 |
| medium_input | VARCHAR(200) | 입력된 매체 |
| medium_category | VARCHAR(20) | 파싱된 매체 카테고리 |
| target_market | VARCHAR(20) | gallery / online |
| predicted_krw | INT | 예측 가격 |
| price_range_low | INT | 하한 |
| price_range_high | INT | 상한 |
| confidence_grade | CHAR(1) | A/B/C/D |
| model_version_id | INT FK | model_versions.id |
| is_known_artist | BOOLEAN | 학습 작가 매칭 여부 |
| feature_completeness | FLOAT | CHECK BETWEEN 0 AND 1 |
| external_sources_used | VARCHAR[] | 사용된 외부 소스 |
| cache_hit | BOOLEAN | 프로필 캐시 히트 여부 |
| db_lookup_ms | INT | DB 매칭 시간 |
| external_fetch_ms | INT | 외부 수집 시간 |
| prediction_ms | INT | 모델 예측 시간 |
| total_ms | INT | 총 처리 시간 |
| warnings | JSONB | 부분 실패/동명이인 등 경고 목록 |
| actual_price | INT | 실제 판매가 (사후 입력, nullable) |
| request_id | UUID | 요청 추적 ID |
| created_at | TIMESTAMPTZ DEFAULT now() | |

**인덱스**: `artist_id`, `created_at`, `confidence_grade`, `model_version_id`
**제약조건**: `CHECK (predicted_krw > 0)`, `CHECK (confidence_grade IN ('A','B','C','D'))`
**용도**: 정확도 모니터링 (actual_price 입력 시), 성능 추적 (단계별 ms), 장애 분석 (warnings)

#### model_versions — 모델 메타데이터

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| version | VARCHAR(20) NOT NULL | v3, v4 등 — CatBoost+XGBoost 쌍의 버전 |
| catboost_hash | VARCHAR(64) | CatBoost 모델 파일 SHA-256 |
| xgboost_hash | VARCHAR(64) | XGBoost 모델 파일 SHA-256 |
| training_count | INT | 학습 데이터 건수 |
| artist_count | INT | 학습 작가 수 |
| new_candidates_count | INT DEFAULT 0 | 이번 버전에 포함된 신규 적재 데이터 건수 |
| mdape_groupkfold | FLOAT | Cold Start MdAPE |
| mdape_kfold | FLOAT | 학습 작가 MdAPE |
| mdape_prev_diff | FLOAT | 이전 버전 대비 MdAPE 변화 (%p) |
| features | JSONB | 피처 목록 |
| activated_at | TIMESTAMPTZ | 서빙 시작 시각 (nullable) |
| deactivated_at | TIMESTAMPTZ | 서빙 종료 시각 (nullable) |
| created_at | TIMESTAMPTZ DEFAULT now() | |

**설계**: CatBoost + XGBoost를 **하나의 버전(쌍)**으로 관리. 배포/롤백 시 쌍 단위로 전환.
**제약조건**: `activated_at IS NOT NULL AND deactivated_at IS NULL`인 행은 최대 1개 (partial unique index)

#### training_candidates — 학습 후보 데이터 적재

신규 데이터를 즉시 학습하지 않고, 검토 후 수동 재학습에 사용.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL PK | |
| artist_id | INT FK | artists.id (nullable, 미매칭 시 null) |
| artist_name | VARCHAR(200) NOT NULL | 입력된 작가명 |
| width_cm | FLOAT | |
| height_cm | FLOAT | |
| medium | VARCHAR(200) | |
| price_krw | INT | 실제 판매가 (핵심 — 이게 있어야 학습 가능) |
| price_source | VARCHAR(50) | 가격 출처 (갤러리 리포트, 직접 입력, 판매 확인 등) |
| gallery_name | VARCHAR(100) | |
| market_source | VARCHAR(20) | CHECK IN ('artsy', 'saatchi', 'gallery', 'online', 'other') — 시장 소스 (모델 피처 `source`와 동일 의미) |
| ingestion_channel | VARCHAR(20) | 입력 채널 (manual, gallery_report, api_feedback) |
| sale_date | DATE | 실제 판매/리스팅 일자 (피처 시점 고정용) |
| external_profile_snapshot | JSONB | 적재 시점의 작가 외부 프로필 스냅샷 (미래 정보 누출 방지) |
| prediction_id | UUID FK | predictions.id (예측 → 실제가 연결, nullable) |
| raw_data | JSONB | 원본 입력 데이터 전체 |
| dedupe_key | VARCHAR(200) | 중복 방지 키 (artist_name + medium + size + price) |
| status | VARCHAR(20) NOT NULL DEFAULT 'pending' | CHECK IN ('pending', 'approved', 'rejected', 'trained') |
| reject_reason | TEXT | 거절 사유 (rejected 시 필수) |
| review_notes | TEXT | 검토 메모 |
| reviewed_by | VARCHAR(50) | 검토자 |
| reviewed_at | TIMESTAMPTZ | 검토 시각 |
| trained_in_version | VARCHAR(20) | 학습에 포함된 모델 버전 (nullable) |
| created_at | TIMESTAMPTZ DEFAULT now() | |

**인덱스**: `status`, `created_at`, `artist_id`, `dedupe_key` (unique)
**제약조건**: `CHECK (price_krw > 0)`, `CHECK (width_cm > 0 AND height_cm > 0)`

**워크플로우**:
```
신규 데이터 입력 (API 또는 수동)
  │
  ├─ training_candidates에 INSERT (status='pending')
  │
  ├─ 운영자 검토
  │   ├─ 가격/작가/크기 타당성 확인
  │   ├─ status → 'approved' 또는 'rejected'
  │   └─ rejected 사유 기록
  │
  ├─ 일정량 누적 시 운영자 판단으로 재학습 트리거
  │   │
  │   ├─ Step 1: 피처 생성
  │   │   approved 행의 external_profile_snapshot 사용 (미래 정보 누출 방지)
  │   │   기존 파이프라인과 동일한 피처 엔지니어링 적용
  │   │   market_source → 모델 피처 'source' 컬럼으로 매핑
  │   │
  │   ├─ Step 2: 기존 학습 데이터 + approved 데이터 병합
  │   │   primary_market_dataset.parquet + saatchi_cleaned.parquet + 신규
  │   │
  │   ├─ Step 3: CatBoost + XGBoost 쌍으로 학습
  │   │   동일 하이퍼파라미터, 동일 피처
  │   │
  │   ├─ Step 4: 성능 비교 리포트 자동 생성
  │   │   GroupKFold/KFold MdAPE, W30 (전체/Artsy/Saatchi/신규)
  │   │   가격대별 정확도 비교
  │   │
  │   ├─ Step 5: 배포 판단 (운영자)
  │   │   ├─ 개선 → model_versions에 신규 쌍 등록 + 활성화
  │   │   │   artists.is_in_training / training_count 갱신
  │   │   └─ 악화 → 기존 모델 유지, 데이터 재검토
  │   │
  │   └─ Step 6: 학습 완료 시
  │       status → 'trained', trained_in_version 기록
  │       artists.is_in_training 갱신 (신규 작가 warm start 전환)
```

**재학습 판단 기준** (운영자 가이드):
- approved 데이터가 **전체 학습 데이터의 1% 이상** 누적 시 고려 (현재 ~300건)
- 또는 고가(1천만+) 구간에 50건+ 누적 시 (가장 약한 구간 보강)
- 또는 신규 작가 중 5건+ 이력 보유 작가가 10명+ (XGBoost 경로 전환 가능)
- 재학습 후 GroupKFold MdAPE가 기존 대비 **0.5%p 이상 악화하면 배포하지 않음**

**미래 정보 누출 방지**: 
적재 시점(`sale_date`)의 `external_profile_snapshot`을 사용하여 피처 생성. 
현재 시점의 외부 프로필(팔로워 수, 작품 수 변화)이 학습에 반영되지 않도록 함.

**predictions.actual_price와의 관계**:
- `predictions.actual_price`는 예측 정확도 모니터링용 (사후 실제가 기록)
- `training_candidates`는 학습 데이터 적재용 (재학습에 직접 사용)
- 연결: `training_candidates.prediction_id` → 기존 예측과 실제 판매가 연결 가능

### 10.3 데이터 흐름

```
[API 요청 — 예측]                     [데이터 적재]
  │                                    │
  ├─ artists 조회 (매칭)                 ├─ POST /api/v1/training-data
  ├─ artist_profiles 조회 (캐시)         │   (작가, 크기, 매체, 실제 판매가)
  ├─ 예측 수행                           │
  ├─ predictions INSERT (로그)          └─ training_candidates INSERT
  │                                        (status='pending')
  └─ 응답 반환
                                    [수동 재학습]
                                       │
                                       ├─ approved 100건+ 누적 확인
                                       ├─ 재학습 스크립트 실행
                                       ├─ 기존 vs 신규 모델 성능 비교
                                       ├─ 개선 → model_versions 교체
                                       └─ 악화 → 기존 유지
```

### 10.4 초기 데이터 마이그레이션 (완료)

> 2026-04-16 실행 완료. 아래는 실제 DB 상태.

| 테이블 | 건수 | 내용 |
|--------|:----:|------|
| artists | **1,589명** | Artsy 757 + Saatchi 832 (학습 작가만, `is_in_training=true`) |
| artist_profiles | **1,577건** | Artsy 757 + Saatchi 820 (학습 작가의 외부 프로필) |
| model_versions | **1건** | v3 (CatBoost+XGBoost 쌍, 활성) |
| predictions | 0건 | API 서빙 시 적재 |
| training_candidates | 0건 | Phase 4에서 사용 |

**향후 확장**: 학습에 없는 외부 작가(Artsy 1,168명 + Saatchi 329명)는 Phase 2에서 외부 수집 구현 시 추가.

서버 시작 시 외부 호출 없이 DB에서 로드.

---

## 11. 배포 구성

### 11.1 인프라

```
[인터넷]
    │
    ├─ visionai-api.ahto.city  → 개발/스테이징
    └─ visionai-api.brut.bot   → 운영 (향후)

┌─ 개발 Dokploy (dev.ahto.city) ─────────────────────┐
│                                                     │
│  [API Container — mini-app-prod 단독]                │
│  ├─ FastAPI + Uvicorn                               │
│  ├─ CatBoost v3 + XGBoost v3 (컨테이너 내 번들)       │
│  └─ Python 3.11 + catboost, xgboost, pandas         │
│                                                     │
│  [PostgreSQL — db-primary (192.168.139.156)]         │
│  ├─ DB: visionai_dev                                │
│  ├─ artists (1,589+ 작가 마스터)                      │
│  ├─ artist_profiles (외부 프로필 캐시)                 │
│  ├─ predictions (예측 로그)                           │
│  ├─ training_candidates (학습 후보 적재)               │
│  └─ model_versions (모델 메타)                       │
│                                                     │
└─────────────────────────────────────────────────────┘

운영 배포 시:
┌─ 운영 Dokploy (100.88.186.74:3000) ────────────────┐
│  ├─ mini-app-prod + m3-app-prod (로드밸런서)          │
│  ├─ DB: prod-db-server (192.168.50.10) visionai_prod │
│  └─ visionai-api.brut.bot                           │
└─────────────────────────────────────────────────────┘
```
```

### 11.2 성능 목표

| 지표 | 목표 |
|------|------|
| 응답 시간 (DB 매칭) | < 100ms |
| 응답 시간 (외부 수집) | < 3s |
| 동시 요청 | 50 req/s |
| 가용성 | 99.5% |

---

## 12. 용어 설명

| 용어 | 설명 |
|------|------|
| Cold Start | 학습에 없는 작가의 가격 예측. 크기/매체/프로필만으로 예측 |
| MdAPE | 예측 오차의 중앙값. 38.7%면 절반의 작품이 이보다 정확 |
| W30 | 오차 30% 이내 비율 |
| 호수 | 한국 캔버스 크기 단위 (면적 기준 0~500호) |
| GroupKFold | 작가 단위 분할 검증. Cold Start 성능 측정용 |
| 피처 중요도 | 모델이 예측 시 각 피처에 의존하는 비율 |
| fuzzy match | 이름의 유사도 기반 매칭 (0.85 이상 일치 시 매칭) |

---

## 13. 코덱스 리뷰 결과

### Round 1 (v1.0 → v1.1)

> 14개 지적, 12개 반영.

| # | 지적 | 수정 |
|:-:|------|------|
| 1 | "비동기" 외부 수집이 사실 동기 | 캐시 우선 구조로 변경 |
| 2 | source ratio 보정 누락 | 모델 라우팅에 보정 추가 |
| 3 | 작가 매칭 과소 설계 | 한/영 정규화 + rapidfuzz |
| 4 | 아티스트 검색 미설계 | Phase 2에 검색 파이프라인 추가 |
| 5 | 에러 핸들링 모순 (404) | 등급 하락으로 변경 |
| 6 | "신뢰 구간" 용어 오용 | "예측 범위" + "주관적 밴드" 명시 |
| 7 | 코드 재사용 과대 평가 | server.py 신규 작성 필요 명시 |
| 8 | feature_contributions 시퀀싱 | MVP에서 제거, Phase 3 |
| 9 | 캐시 설계 빈약 | 소스별 TTL + stale-on-error |
| 10 | 배포 사이징 | 100MB → 2GB |
| 11 | 타임라인 비현실적 | MVP 범위 축소 |
| 12 | 외부 의존성 리스크 | 리스크 테이블 추가 |

### Round 2 (v1.1 → v1.2)

> 10개 지적, 8개 반영. KADA 잔여 참조 제거 + 동명이인 전략 현실화.

| # | 지적 | 수정 |
|:-:|------|------|
| 1 | source ratio의 target_source 미정의 | 요청 스키마에 `target_market` 필드 추가 |
| 2 | EXTERNAL_TIMEOUT 504 vs 예측 진행 모순 | 504 → `EXTERNAL_PARTIAL` 200 + warnings |
| 4 | Artsy/Saatchi 이름→ID 매칭 시 동명이인 | nationality/country 필터 + 수동 검증 플래그 |
| 5 | 웹검색 동명이인 6단계 비현실적 | 매체 교차 제거, 신뢰도 점수→pass/fail 이진 판정 |
| 6 | 웹검색 구현 방법 미정의 | SerpAPI/Google CSE/Naver API 명시 |
| 8 | KADA 잔여 참조 | 모든 KADA/KAP 참조 제거 |
| 9 | 배치 API 스코프 모호 | 시스템 구성도 + 스펙에 (Phase 3) 명시 |
| 10 | 사전 수집 1,589명 시작 시 크롤링 비현실적 | 배치 사전 수집 → 캐시 파일 번들로 변경 |

### Round 3 (v1.2 → v1.3, DB 설계 집중)

> 10개 지적, 8개 반영.

| # | 지적 | 수정 |
|:-:|------|------|
| 1 | artist_profiles에 birth_year/nationality 없음 | `birth_year_from_source`, `nationality_from_source` 추가 |
| 2 | 마이그레이션 FK 순서 미정의 | 8단계 순서 명시 (artists 먼저 → profiles → model_versions) |
| 3 | 캐시에 실패/stale 상태 저장 불가 | `status`, `error_message`, `retry_after` 컬럼 추가 |
| 4 | fuzzy 매칭용 인덱스 없음 | `name_normalized` + pg_trgm GIN 인덱스 추가 |
| 5 | predictions에 단계별 시간/경고 없음 | `db_lookup_ms`, `external_fetch_ms`, `warnings`, `cache_hit` 등 추가 |
| 7 | 동시 요청 시 중복 INSERT | `ON CONFLICT DO NOTHING` + name+birth_year 복합 판단 |
| 8 | CHECK 제약조건 없음 | 주요 컬럼에 CHECK/NOT NULL 추가 |
| 9 | model_versions에 is_active 복수 가능 | `activated_at`/`deactivated_at` + partial unique index |

### Round 4 (v1.3 → v1.4, 학습 파이프라인 집중)

> 9개 지적, 7개 반영.

| # | 지적 | 수정 |
|:-:|------|------|
| 1 | approved 행의 피처 생성 방법 미정의 | `external_profile_snapshot` + `sale_date` 추가, 미래 정보 누출 방지 |
| 2 | 재학습 후 artists.is_in_training 미갱신 | Step 6에 artists 갱신 명시 |
| 3 | rejected_reason 컬럼 없음, 중복 방지 없음 | `reject_reason`, `review_notes`, `dedupe_key` 추가 |
| 4 | predictions.actual_price와 training_candidates 관계 미정의 | `prediction_id` FK로 연결, 역할 구분 명시 |
| 6 | training_candidates.source가 모델 피처 source와 다른 의미 | `market_source`(시장 소스) + `ingestion_channel`(입력 채널) 분리 |
| 7 | 100건 임계값 비현실적 | 전체의 1%(~300건) + 고가 구간 + 신규 작가 조건으로 변경 |
| 8 | model_versions가 CB/XGB 독립 관리 | 쌍(pair) 버전 관리로 변경 + `mdape_prev_diff` |

### Round 5 (v1.4 → v1.5, 구현 준비 검증)

> **FAIL → PASS** 전환. 5개 블로커를 Phase 1 전용 스펙 분리로 해결.

| # | 지적 | 수정 |
|:-:|------|------|
| 1 | Phase 1 API 계약이 Phase 2+ 혼재 | Phase 1 전용 Request/Response/엔드포인트 분리 |
| 2 | DB 마이그레이션 섹션이 실제 DB 상태와 불일치 | "완료" 표기 + 실제 건수(1589/1577/1)로 갱신 |
| 3 | 신뢰도 등급 결정이 정성적 | `determine_confidence()` 함수 코드로 결정적 규칙 명시 |
| 4 | source ratio 공식 없음 | `RATIO_CORRECTION` 딕셔너리 + 공식 명시 (0.075 = ln(1.078)) |
| 5 | 입력 필드 중 Phase 1에서 미지원 필드 모호 | education/exhibitions/skip_external_lookup Phase 1에서 제거 |

### Round 6 (구현 코드 리뷰)

> 3 High, 3 Medium, 2 Low. High 3건 + Medium 1건 수정.

| # | 심각도 | 지적 | 수정 |
|:-:|:------:|------|------|
| 1 | **High** | XGBoost label map 미포함 (parquet 없음) | 하드코딩 fallback 추가 |
| 2 | **High** | DB 실패 시 health가 OK 반환 | `status: "degraded"` 분기 |
| 3 | **High** | 다중 소스 프로필 우선순위 미적용 | `SOURCE_PRIORITY` (artsy > saatchi > web) |
| 5 | Medium | manual override 0값이 무시됨 | `is not None` 체크로 변경 |

### 미반영 (의도적/향후)

| # | 지적 | 사유 |
|:-:|------|------|
| R6-4 | ErrorResponse 미사용, medium 미검증 | MVP에서는 unknown→"other" 허용. Phase 2에서 강화 |
| R6-6 | 동명이인 동일 이름 충돌 | 현재 1,589명 규모에서 실질적 영향 미미. Phase 2에서 개선 |
| R6-7 | model_info 하드코딩 | model_versions DB에서 조회로 변경 예정 |
| R6-8 | requirements 버전 고정, 컨테이너 non-root | Phase 2 배포 강화 시 적용 |
