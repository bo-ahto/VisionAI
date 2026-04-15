# 작가 프로필-가격 매칭 데이터 파이프라인 전략

## 1. 문제 정의

### 1.1 현재 상황

수집 테스트(2026-04-13)에서 확인된 핵심 사실:

| 소스 | 수집량 | 특성 |
|------|--------|------|
| KADA 작가 이름 | 96명 | 신진/중견, 한글+영문 |
| KAP Career | 111명 | 원로/중견, 학력/전시/수상/소장 |
| K-ARTMARKET 경매 | 103,694건 | 국내 최대 경매 데이터 |
| Artsy CV | ~2,000+ 한국 작가 추정 | 구조화된 CV, 국제 전시 |

**테스트 매칭 결과:**
- KADA 96명 중 K-ARTMARKET 가격 보유: **22명** (23%)
- 가격 22명 중 Artsy CV 보유: **13명** (59%)
- KADA와 KAP 중복: **0명** (완전히 다른 작가 풀)

### 1.2 근본 병목: 이름 매칭

작가 가격 예측 모델에 필요한 데이터는 **프로필(전시/학력/수상) + 가격(경매 낙찰)**이 같은 작가에게 있어야 한다. 문제는 각 소스의 작가 이름이 다르다:

| 작가 | KADA | K-ARTMARKET | Artsy | KAP |
|------|------|-------------|-------|-----|
| 이광호 | Lee Kwang-Ho | 이광호 | (미등록) | (미등록) |
| 김창영 | Kim Changyoung | 김창영 | changyoung-kim (404) | (미등록) |
| 강원제 | Kang Wonje | 강원제 | wonje-kang | (미등록) |

- **영문 표기 불일치**: Kwang-Ho vs KwangHo vs Gwangho
- **이름 순서 차이**: First Last vs Last First
- **동명이인**: 김지수(KADA) vs Jeesoo Kim(Artsy, Australian)
- **소스 간 풀 불일치**: KAP 원로 vs KADA 신진, 경매 등장 작가 vs 갤러리 전용 작가

### 1.3 목표

1차 시장 가격 예측 모델 학습에 필요한 **200명 이상**의 (프로필 + 가격) 매칭 데이터를 확보하고, 이를 지속적으로 업데이트 가능한 파이프라인으로 운영한다.


## 2. 전략적 접근법

### 2.1 전략 A: 가격-우선 역방향 파이프라인 (추천)

**개념:** K-ARTMARKET의 103,694건에서 고유 작가를 추출한 뒤, 각 작가의 프로필을 Artsy/KAP에서 찾는다.

```
K-ARTMARKET (103K works)
    → 고유 작가 추출 (~3,000-5,000명 추정)
    → 한글 이름 → Artsy slug 변환 시도
    → Artsy CV 수집
    → 매칭 실패 시 KAP/KADA에서 프로필 수집
```

**장점:**
- 모든 매칭 레코드에 가격이 보장됨
- K-ARTMARKET이 가장 큰 단일 소스 (103K건)
- 한글 이름이 1차 키이므로 K-ARTMARKET 내부 검색 정확도 높음

**단점:**
- 경매 시장에 등장하지 않는 갤러리 전용 작가 누락
- K-ARTMARKET 크롤링 규모가 큼 (전체 작가 목록 추출 필요)

**예상 수율:** K-ARTMARKET 고유 작가 ~3,000명 중 Artsy 매칭 ~500명 (17%), KAP/KADA 추가 매칭 ~200명 → **총 ~700명**

### 2.2 전략 B: Artsy-중심 프로필 우선

**개념:** Artsy의 한국 작가 디렉토리에서 시작해, 구조화된 CV를 수집하고 K-ARTMARKET에서 가격을 매칭한다.

```
Artsy Korean Artists (~2,000명)
    → CV 페이지 크롤링 (solo, group, fair, collection)
    → 한글 이름 추출/변환
    → K-ARTMARKET 검색으로 경매 가격 매칭
    → 매칭 실패 시 Seoul Auction/K Auction 직접 검색
```

**장점:**
- Artsy CV가 가장 구조화된 프로필 데이터
- 국제 전시 이력 포함 (국내 소스에 없는 정보)
- Fair booth 데이터로 갤러리 티어 추정 가능
- slug 기반 URL로 안정적 접근

**단점:**
- 한국 작가 중 Artsy 등록률이 제한적 (특히 원로 작가)
- Artsy CV 내용이 빈약한 작가 많음 ("no solo shows yet")
- 영문→한글 역변환 필요 (slug → 한글 이름)

**예상 수율:** Artsy 한국 작가 ~2,000명 중 K-ARTMARKET 가격 매칭 ~400명 (20%) → **총 ~400명**

### 2.3 전략 C: 마스터 레지스트리 + 하이브리드

**개념:** 모든 소스에서 작가를 수집하고 중앙 이름 레지스트리로 통합, 퍼지 매칭으로 연결한다.

```
[모든 소스] → 작가 이름 추출
    → Master Name Registry (canonical_id, name_kor, name_eng_variants[])
    → 퍼지 매칭 + 수동 검증
    → 각 소스의 데이터를 canonical_id로 조인
```

**장점:**
- 가장 높은 커버리지 (모든 소스 통합)
- 이름 변환 문제를 한번에 해결
- 장기적으로 가장 확장성 높음

**단점:**
- 초기 구축 비용 높음 (퍼지 매칭 + 수동 검증)
- 동명이인 처리 복잡
- 유지보수 부담 (새 소스 추가마다 매칭 로직 필요)

**예상 수율:** 최종 ~1,000명+ (시간이 걸림)


## 3. 추천 파이프라인 아키텍처

**전략 A + B 하이브리드** 를 추천한다. 가격 확보가 보장되는 A를 1차로, Artsy 프로필 품질이 높은 B를 2차로 실행.

### 3.1 데이터 흐름

```
┌─────────────────────────────────────────────────────┐
│                  Layer 1: 수집 (Collection)           │
│                                                       │
│  K-ARTMARKET ──→ [작가명, 작품, 가격, 경매사, 날짜]   │
│  Artsy       ──→ [slug, CV, bio, nationality]        │
│  KAP         ──→ [학력, 전시, 수상, 소장처]           │
│  Seoul/K옥션  ──→ [가격, 작품, 경매 날짜]              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Layer 2: 이름 해소 (Name Resolution)     │
│                                                       │
│  ┌──────────────────────────────────┐                │
│  │   Master Artist Registry (SQLite) │                │
│  │                                    │                │
│  │   canonical_id: UUID               │                │
│  │   name_kor: 이광호                  │                │
│  │   name_eng: [Lee Kwang-Ho,         │                │
│  │              Kwangho Lee,           │                │
│  │              Lee KwangHo]           │                │
│  │   artsy_slug: kwangho-lee          │                │
│  │   kap_id: 47                       │                │
│  │   kartmarket_name: 이광호           │                │
│  │   match_confidence: 0.95           │                │
│  │   verified: true                   │                │
│  └──────────────────────────────────┘                │
│                                                       │
│  매칭 엔진:                                           │
│  - 한글 이름 완전 일치 (confidence 1.0)               │
│  - 영문 이름 정규화 후 매칭 (0.8-0.95)                │
│  - Jaro-Winkler 유사도 (0.6-0.8)                     │
│  - 생년+성별+분야 보조 매칭 (disambiguation)           │
│  - confidence < 0.8 → 수동 검증 큐                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│           Layer 3: 프로필 조립 (Assembly)              │
│                                                       │
│  canonical_id별로 모든 소스 데이터를 병합:              │
│  - 프로필: Artsy CV > KAP Career > KADA               │
│  - 가격: K-ARTMARKET > Seoul Auction > K Auction      │
│  - 필드별 last_updated 추적                           │
│  - 데이터 충돌 시 최신 소스 우선                       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│         Layer 4: 모델 피처 (Feature Engineering)      │
│                                                       │
│  solo_exhibition_count (Artsy + KAP 합산, 중복 제거)  │
│  group_exhibition_count                               │
│  institutional_score = Σ(weight × exhibition_count)   │
│  career_age = 현재연도 - 첫 개인전 연도               │
│  auction_price_median, auction_price_trend             │
│  education_tier (MFA 유무, 학교 랭킹)                 │
│  gallery_tier (Artsy fair booth → 갤러리 추정)        │
└───────────────────────────────────────────────────────┘
```

### 3.2 이름 매칭 알고리즘

한국 작가 영문 이름의 특수성을 반영한 매칭 로직:

```python
def normalize_korean_eng_name(name: str) -> str:
    """영문 이름 정규화: 대소문자, 하이픈, 공백, 이름 순서 통일."""
    name = name.lower().strip()
    name = name.replace("-", " ").replace(".", " ")
    # 쉼표가 있으면 Last, First → First Last
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        name = " ".join(reversed(parts))
    # 연속 공백 제거
    name = " ".join(name.split())
    return name

def name_variants(name_kor: str, name_eng: str) -> list[str]:
    """가능한 Artsy slug 패턴 생성."""
    eng = normalize_korean_eng_name(name_eng)
    parts = eng.split()
    slugs = []
    if len(parts) == 2:
        slugs.append(f"{parts[0]}-{parts[1]}")  # first-last
        slugs.append(f"{parts[1]}-{parts[0]}")  # last-first
    elif len(parts) == 3:
        slugs.append(f"{parts[0]}-{parts[1]}-{parts[2]}")
        slugs.append(f"{parts[2]}-{parts[0]}-{parts[1]}")
        slugs.append(f"{parts[0]}{parts[1]}-{parts[2]}")  # 이름 붙임
    return slugs
```

### 3.3 기술 스택

| 구성요소 | 선택 | 이유 |
|----------|------|------|
| 저장소 | SQLite → PostgreSQL | 500명까지 SQLite, 이후 PostgreSQL |
| 크롤러 | Python + Playwright | JS 렌더링 사이트 대응 |
| 스케줄링 | cron (로컬) → Cloud Scheduler | 초기 단순, 이후 클라우드 |
| 매칭 엔진 | Python + jellyfish | Jaro-Winkler 유사도 |
| 수동 검증 UI | Streamlit 대시보드 | 저비용, 빠른 구축 |
| 모니터링 | 로그 + Slack 알림 | 크롤링 실패/이상 감지 |


## 4. 단계별 로드맵

### Phase 1: 기반 구축 (Foundation)

**목표:** 200명 매칭 데이터셋 확보

1. **K-ARTMARKET 작가 목록 추출**
   - 전체 103K 작품에서 고유 한국 작가명 추출
   - 작가별 작품 수, 가격 범위, 활동 기간 집계
   - 예상: ~3,000 고유 작가

2. **Artsy 한국 작가 크롤링**
   - nationality=Korean 필터로 전체 목록 수집
   - 각 작가의 /cv 페이지에서 CV 수집
   - 예상: ~2,000 작가

3. **이름 매칭 1차**
   - 한글 이름 완전 일치 (K-ARTMARKET → Artsy는 불가, 영문 기반)
   - 정규화된 영문 이름 매칭
   - slug 패턴 시도 (first-last, last-first)
   - confidence < 0.8은 수동 큐에 넣기

4. **수동 검증**
   - 자동 매칭 결과 검토 (예상 2-3시간)
   - 동명이인 분리, 오매칭 수정
   - 매칭 규칙 피드백으로 알고리즘 개선

**산출물:** `artist_registry.sqlite` + `matched_dataset.json` (200명+)

### Phase 2: 자동화 (Automation)

**목표:** 월간 자동 업데이트 파이프라인

1. **델타 크롤러 구축**
   - K-ARTMARKET: 최근 30일 경매 결과만 수집
   - Artsy: 신규 작가 페이지 감지
   - 변경 감지: hash 비교로 업데이트된 프로필만 처리

2. **자동 매칭 파이프라인**
   - 신규 작가 발견 시 자동 매칭 시도
   - 고신뢰도(>0.9) 자동 승인
   - 저신뢰도(<0.9) 수동 검증 큐

3. **스케줄링**
   ```
   # crontab 예시
   0 3 1 * *   python3 crawl_kartmarket_delta.py    # 매월 1일 03:00
   0 4 1 * *   python3 crawl_artsy_delta.py         # 매월 1일 04:00
   0 5 1 * *   python3 run_matching.py              # 매월 1일 05:00
   0 6 1 * *   python3 generate_features.py         # 매월 1일 06:00
   ```

4. **모니터링**
   - 크롤링 성공/실패 카운트
   - 신규 매칭 수
   - 데이터 품질 지표 (null 비율, 가격 이상치)

### Phase 3: 확장 (Scaling)

**목표:** 500명+ 데이터셋, 추가 소스 통합

1. **추가 소스 통합**
   - Seoul Auction 낙찰 결과 (서울옥션 공식 사이트)
   - K Auction 낙찰 결과
   - 에이옥션, 아이옥션, 라이즈아트 등 중소 경매사
   - 한국미술시가감정협회 감정가 (공개 범위)

2. **프로필 소스 확장**
   - 국립현대미술관 작가 DB
   - 네이버 인물 정보 (생년, 학력)
   - 갤러리 웹사이트 (대형 갤러리의 소속 작가 목록)

3. **데이터 품질 고도화**
   - 전시 중복 제거 (같은 전시가 Artsy+KAP에 모두 있을 때)
   - 가격 이상치 감지 (동일 작가의 가격 분포에서 벗어난 건)
   - 작가 활동 상태 추적 (은퇴, 작고 등)


## 5. 데이터 스키마

### 5.1 Master Artist Registry

```sql
CREATE TABLE artists (
    canonical_id    TEXT PRIMARY KEY,
    name_kor        TEXT NOT NULL,
    name_eng        TEXT,
    birth_year      INTEGER,
    death_year      INTEGER,
    nationality     TEXT DEFAULT 'Korean',
    field           TEXT,  -- 회화, 조각, 미디어, 사진 등
    
    -- 소스 연결
    artsy_slug      TEXT,
    kap_id          INTEGER,
    kada_data_id     TEXT,
    
    -- 매칭 메타
    match_confidence REAL DEFAULT 1.0,
    verified         BOOLEAN DEFAULT FALSE,
    
    -- 타임스탬프
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE name_variants (
    canonical_id    TEXT REFERENCES artists(canonical_id),
    name_variant    TEXT NOT NULL,
    source          TEXT,  -- artsy, kap, kartmarket, manual
    UNIQUE(canonical_id, name_variant)
);
```

### 5.2 Profile Data

```sql
CREATE TABLE exhibitions (
    id              INTEGER PRIMARY KEY,
    canonical_id    TEXT REFERENCES artists(canonical_id),
    type            TEXT,  -- solo, group, fair
    title           TEXT,
    venue           TEXT,
    year            INTEGER,
    source          TEXT,  -- artsy, kap, kada
    source_url      TEXT,
    UNIQUE(canonical_id, title, venue, year)
);

CREATE TABLE education (
    id              INTEGER PRIMARY KEY,
    canonical_id    TEXT REFERENCES artists(canonical_id),
    institution     TEXT,
    degree          TEXT,
    year            INTEGER,
    source          TEXT
);

CREATE TABLE awards (
    id              INTEGER PRIMARY KEY,
    canonical_id    TEXT REFERENCES artists(canonical_id),
    title           TEXT,
    year            INTEGER,
    source          TEXT
);

CREATE TABLE collections (
    id              INTEGER PRIMARY KEY,
    canonical_id    TEXT REFERENCES artists(canonical_id),
    institution     TEXT,
    year            INTEGER,
    source          TEXT
);
```

### 5.3 Auction Data

```sql
CREATE TABLE auction_records (
    id              INTEGER PRIMARY KEY,
    canonical_id    TEXT REFERENCES artists(canonical_id),
    title           TEXT,
    material        TEXT,
    size_raw        TEXT,
    width_cm        REAL,
    height_cm       REAL,
    price_krw       INTEGER,
    auction_house   TEXT,
    auction_name    TEXT,
    auction_date    DATE,
    source          TEXT,  -- kartmarket, seoul_auction, k_auction
    source_id       TEXT,  -- UCI or unique ID from source
    UNIQUE(source, source_id)
);
```

### 5.4 Computed Features (View)

```sql
CREATE VIEW artist_features AS
SELECT 
    a.canonical_id,
    a.name_kor,
    a.name_eng,
    a.birth_year,
    a.field,
    
    -- 전시 카운트
    COUNT(DISTINCT CASE WHEN e.type='solo' THEN e.id END) AS solo_count,
    COUNT(DISTINCT CASE WHEN e.type='group' THEN e.id END) AS group_count,
    COUNT(DISTINCT CASE WHEN e.type='fair' THEN e.id END) AS fair_count,
    
    -- 수상/소장
    (SELECT COUNT(*) FROM awards w WHERE w.canonical_id = a.canonical_id) AS award_count,
    (SELECT COUNT(*) FROM collections c WHERE c.canonical_id = a.canonical_id) AS collection_count,
    
    -- 학력
    (SELECT COUNT(*) FROM education ed WHERE ed.canonical_id = a.canonical_id) AS education_count,
    
    -- 경매 통계
    (SELECT COUNT(*) FROM auction_records ar WHERE ar.canonical_id = a.canonical_id) AS auction_count,
    (SELECT AVG(price_krw) FROM auction_records ar WHERE ar.canonical_id = a.canonical_id) AS price_avg,
    (SELECT MIN(price_krw) FROM auction_records ar WHERE ar.canonical_id = a.canonical_id) AS price_min,
    (SELECT MAX(price_krw) FROM auction_records ar WHERE ar.canonical_id = a.canonical_id) AS price_max,
    
    -- 경력 연수
    (SELECT MIN(year) FROM exhibitions e2 WHERE e2.canonical_id = a.canonical_id AND e2.type='solo') AS first_solo_year,
    
    -- 소스 수
    (SELECT COUNT(DISTINCT source) FROM exhibitions e3 WHERE e3.canonical_id = a.canonical_id) 
    + CASE WHEN a.artsy_slug IS NOT NULL THEN 1 ELSE 0 END AS source_count

FROM artists a
LEFT JOIN exhibitions e ON a.canonical_id = e.canonical_id
GROUP BY a.canonical_id;
```


## 6. 운영 지표 (KPI)

| 지표 | 현재 | Phase 1 목표 | Phase 2 목표 |
|------|------|-------------|-------------|
| 총 등록 작가 | 207 (KADA 96 + KAP 111) | 3,000+ | 5,000+ |
| 가격 보유 작가 | 22 | 500+ | 1,000+ |
| 프로필 보유 작가 | 111 (KAP) + 13 (Artsy) | 1,000+ | 2,500+ |
| **매칭(가격+프로필)** | **13** | **200+** | **500+** |
| 데이터 신선도 | 수동 | 월 1회 자동 | 주 1회 자동 |
| 이름 매칭 정확도 | 수동 | 90%+ | 95%+ |


## 7. 리스크와 대응

### 7.1 크롤링 차단
- **리스크:** K-ARTMARKET, Artsy가 크롤링을 차단할 수 있음
- **대응:** 요청 간격 2초+, User-Agent 로테이션, robots.txt 준수
- **대안:** Artsy GraphQL API 파트너십 요청, K-ARTMARKET 공공 API 확인

### 7.2 동명이인
- **리스크:** 김현수, 이승현 등 흔한 이름의 동명이인 오매칭
- **대응:** 생년+분야+활동 지역으로 보조 매칭, 수동 검증 큐
- **지표:** 동명이인 후보 비율 추적 (목표: 전체의 5% 미만)

### 7.3 데이터 품질
- **리스크:** 소스마다 전시 이름/연도가 미세하게 다름
- **대응:** 정규화 규칙 (연도 추출, 기관명 통일), 중복 제거 로직
- **지표:** 필드별 null 비율, 중복 레코드 비율

### 7.4 법적 리스크
- **리스크:** 크롤링 데이터의 상업적 이용 가능 여부
- **대응:** 공공 데이터(K-ARTMARKET은 예술경영지원센터 운영) 우선 활용
- **확인 필요:** Artsy Terms of Service, KAP 데이터 이용 약관


## 8. 즉시 실행 가능한 Quick Win

현재 인프라(Python + Playwright)로 바로 실행 가능한 것들:

### 8.1 K-ARTMARKET 전체 작가 추출 (예상 소요: 2-3시간)
```
K-ARTMARKET 103,694건 → 작가명 드롭다운/검색 → 고유 작가명 목록
→ 작가별 작품 수 집계 → 상위 500명 우선 타겟
```

### 8.2 Artsy 한국 작가 디렉토리 (예상 소요: 1-2시간)
```
artsy.net/collect?artist_nationalities[]=kr → 작가 slug 목록
→ /artist/{slug}/cv 일괄 수집
→ 한국 작가 Artsy 전체 목록 확보
```

### 8.3 KAP 111명 → K-ARTMARKET 가격 매칭 (예상 소요: 1시간)
```
KAP 111명의 한글 이름 → K-ARTMARKET 검색
→ KAP은 원로/중견이므로 경매 등장률이 KADA보다 높을 것으로 예상
→ 30-50명 추가 매칭 기대
```

이 세 가지를 실행하면 현재 13명 → **100-200명**으로 즉시 확대 가능.
