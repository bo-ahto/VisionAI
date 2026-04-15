# 한국 작가 1차 시장(갤러리) 가격 예측 실험계획서

> **작성일**: 2026-04-13
> **범위**: 한국 작가 한정, 갤러리 판매 가격 예측
> **데이터**: Artsy 수집 30,046건 / 가격 공개 11,118건 / 1,029명 작가

---

## 1. 데이터 현황

### 1.1 수집 결과 요약

Artsy GraphQL API를 통해 한국 작가(South Korean, Korean) 작품 데이터를 수집했다.
가격은 갤러리가 Artsy에 등록한 **1차 시장 판매가**이다.

| 항목 | 값 |
|------|-----|
| 총 작품 | 30,046건 |
| 가격 공개 | 11,118건 (37%) |
| 가격 비공개 (Price on request) | 8,247건 (27%) |
| 판매 완료 (Sold) | 7,421건 (25%) |
| 가격 공개 작가 | 1,029명 |
| 작가 프로필 (전시 이력) | 1,462명 |
| 갤러리 | 194개 |
| 가격 중앙값 (KRW 환산) | 414만원 |
| 가격 범위 | ~1만원 ~ 552억원 |

### 1.2 수집 피처

#### 작품 피처

| 피처 | 수집률 | 원본 형태 | 예시 |
|------|:------:|----------|------|
| width_cm, height_cm | 99% | `"90.9 × 60.6 cm"` | 90.9, 60.6 |
| depth_cm (3D) | 28% | `"27.3 × 22 × 3 cm"` | 3.0 |
| medium | 100% | 영문 상세 | "Oil on canvas" |
| category | 100% | 영문 대분류 | "Painting", "Sculpture" |
| attribution_class | 100% | 유니크/에디션 | "Unique", "Limited edition" |
| date (제작연도) | 100% | 문자열 | "2025" |
| price (갤러리가) | 37% | 다중 통화 | "US$3,900", "KRW ₩18,000,000" |

#### 작가 피처

| 피처 | 수집률 | 소스 | 비고 |
|------|:------:|------|------|
| nationality | 100% | Artsy API | "South Korean", "Korean" |
| birth_year | 81% | Artsy API | birthday 필드 파싱 |
| followers | 85% | Artsy API | 시장 관심도 대리변수 |
| total_works | 99% | Artsy API | 등록 작품 수 |
| for_sale_works | 100% | Artsy API | 현재 판매중 |
| is_p1 | 2% (44명) | Artsy API | Artsy Target Supply (주목 작가) |
| solo_count | 664명 | Artsy API (showsConnection) | 개인전 횟수 |
| group_count | 859명 | Artsy API (showsConnection) | 그룹전 횟수 |
| fair_count | 833명 | Artsy API (showsConnection) | 아트페어 참여 |
| bio | 679명 | Artsy API (showsConnection) | 영문 약력 |

#### 갤러리 피처

| 피처 | 수집률 | 예시 |
|------|:------:|------|
| gallery_name | 100% | "Pontone Gallery", "Gallery Planet" |
| gallery_type | 100% | "Gallery", "Institution" |
| gallery_cities | 98% | "Seoul", "London, New York, Seoul" |

### 1.3 통화 분포

| 통화 | 건수 | 비율 | 환산 기준 |
|------|------|------|----------|
| USD | 9,691 | 87.2% | ×1,380 |
| KRW | 1,221 | 11.0% | ×1 |
| EUR | 103 | 0.9% | ×1,530 |
| GBP | 102 | 0.9% | ×1,780 |
| HKD | 1 | 0.0% | ×178 |

**KRW 표기 작품**: Gallery Planet, Kimreeaa Gallery 등 **국내 갤러리** 작품. 호당 가격제 검증에 핵심 서브셋.

### 1.4 카테고리 분포

| 카테고리 | 전체 | 가격 공개 | 비율 |
|----------|------|---------|------|
| Painting | 20,616 | 7,725 | 69% |
| Sculpture | 2,514 | 763 | 7% |
| Mixed Media | 2,452 | 1,132 | 10% |
| Drawing/Paper | 2,041 | 519 | 5% |
| Photography | 950 | 416 | 4% |
| Print | 910 | 417 | 4% |
| 기타 (Installation, Video 등) | 563 | 146 | 1% |

### 1.5 지지체 분류 (가격 공개 작품)

medium 필드에서 파싱한 지지체 분류:

| 지지체 | 건수 | 비율 | 가격 보정 계수 |
|--------|------|------|:-----------:|
| Canvas | 5,440 | 49% | 1.0 (기준) |
| Paper/Korean paper | 1,916 | 17% | 0.3~0.5 |
| Panel/Wood | 606 | 5% | 0.7 |
| Linen | 422 | 4% | 1.0 (canvas 동급) |
| Silk | 380 | 3% | 별도 |
| Other | 2,354 | 21% | 개별 판단 |

### 1.6 유니크/에디션 분류

| 분류 | 건수 | 비율 |
|------|------|------|
| Unique | 10,172 | 91.5% |
| Limited edition | 890 | 8.0% |
| Unknown/Open edition | 56 | 0.5% |

---

## 2. 피처 설계

### 2.1 수집 데이터에서 파생하는 피처

| 피처 | Artsy 원본 필드 | 변환 방법 |
|------|----------------|----------|
| ho (호수) | width_cm × height_cm | area → 호수 테이블 매칭 |
| canvas_type (F/P/M/S) | width_cm / height_cm | aspect_ratio로 추정 |
| support_type (지지체) | medium | "canvas", "paper" 등 키워드 파싱 |
| is_edition | attribution_class | "Unique" vs "Limited edition" |
| medium_category (매체 분류) | medium | 영문 → 분류 매핑 (oil/acrylic/ink 등) |
| year_made | date | 연도 파싱 |
| work_age | date | 2026 - year_made |
| career_stage (1~4) | birth_year + solo_count | 나이+경력 기반 추정 |
| career_age | shows의 첫 전시 연도 | 2026 - first_show_year |
| institutional_score | shows (기관명 포함) | 기관 티어 DB 매칭 (부분 가능) |
| gallery_tier (1~5) | gallery_name + gallery_cities | 갤러리별 통계로 추정 |
| vintage_premium | date + birth_year | work_age × (career_stage >= 3) |
| freshness_discount | date + birth_year | work_age × (career_stage < 3) |
| for_sale_ratio | for_sale / total_works | 수요 지표 |
| request_ratio | 작가 내 "Price on request" 비율 | 고가 작가 지표 |
| gallery_city_count | gallery_cities | 쉼표 분리 후 카운트 |
| is_small | ho | ho <= 3 (소품 여부) |

### 2.2 향후 보완 가능한 피처

Artsy 데이터만으로 커버되지 않는 피처. Phase 2 이후 별도 수집 검토:

| 피처 | 현재 상태 | 대안/보완 방법 |
|------|----------|--------------|
| museum_collection_count | followers, is_p1으로 간접 추정 가능 | 작가 웹사이트/위키피디아 크롤링 |
| residency_score | shows에 일부 포함됨 | 수동 태깅 (상위 작가 한정) |
| award_score | Artsy bio에 일부 언급 | bio NLP 추출 또는 수동 태깅 |
| critic_review_count | 미확보 | 네이버 뉴스 API |

---

## 3. 호당 가격제 검증 실험

### 3.1 핵심 가설

한국 갤러리 가격 체계의 핵심 구조인 `Price = α × Ho^β`가 Artsy 데이터에서도 성립하는지 검증한다.

**가설 H1**: Painting 카테고리에서 `ln(Price) = ln(α) + β × ln(Ho) + ε`의 β가 0.6~0.9 범위에 있다.

**가설 H2**: KRW 표기 작품(국내 갤러리)에서 β가 USD 표기 작품(국제 갤러리)보다 0.74에 더 가깝다.

**가설 H3**: 작가 내 호당가(Price/Ho^β)의 CV가 0.3 이하인 작가가 전체의 50% 이상이다.

### 3.2 검증 방법

```
Step 1: 필터링
  - Painting + Unique + Canvas/Linen만 선택
  - 가격 이상치 제거 (< 10만원 or > 50억원)
  - 크기 이상치 제거 (< 1cm² or > 100,000cm²)

Step 2: 호수 변환
  area = width_cm × height_cm
  aspect_ratio = max(w,h) / min(w,h)
  canvas_type = aspect_to_type(aspect_ratio)  # F/P/M/S
  ho = area_to_ho(area, canvas_type)

Step 3: β 추정 (전체)
  OLS: ln(price_krw) = c + β × ln(ho) + ε
  → β 추정값 및 95% CI

Step 4: β 추정 (작가별)
  작품 5건 이상 작가 대상
  작가별 OLS → β 분포 히스토그램
  β < 1 비율 (체감 효과 확인)

Step 5: 시장 구분 (KRW vs USD)
  KRW 서브셋 (국내): β_domestic
  USD 서브셋 (국제): β_international
  → 두 β 비교

Step 6: 호당가 일관성 (CV)
  작가별 α_i = median(price / ho^β)
  CV_i = std(price / ho^β) / mean(price / ho^β)
  → CV < 0.3 비율
```

### 3.3 검증 결과에 따른 모델 전략

| 시나리오 | β 결과 | CV 결과 | 모델 전략 |
|----------|--------|---------|----------|
| A: 호당 성립 | 0.6~0.9 | 50%+ 안정 | Two-Stage (α 예측 모델) |
| B: 약하게 성립 | 범위 밖이나 유의미 | 30~50% 안정 | Hybrid (호당 피처 + GBT) |
| C: 불성립 | 유의미하지 않음 | 30% 미만 안정 | Full GBT (크기는 피처로만) |

---

## 4. 모델 아키텍처

### 4.1 Hybrid 접근 (추천)

호당 가격 이론을 피처로 활용하되, GBT(CatBoost)가 자유롭게 학습하는 구조.

```
Target: ln(price_krw)

피처 그룹 1 — 크기 (호당 이론 기반)
  ho                    : 호수 (면적 → 호 변환)
  ho_power              : ho^0.74 (이론적 크기 곡선)
  ln_ho                 : ln(ho + 1)
  area_cm2              : width × height (원본 면적)
  aspect_ratio          : max/min (작품 형태)
  canvas_type           : F/P/M/S (categorical)
  is_small              : ho <= 3 (소품 여부)

피처 그룹 2 — 작품 속성
  support_type          : canvas / paper / panel / linen / silk / other
  medium_category       : oil / acrylic / ink / mixed / watercolor / etc
  attribution_class     : Unique / Limited edition
  year_made             : 제작연도
  work_age              : 2026 - year_made
  depth_cm              : 3D 깊이 (없으면 0)
  is_3d                 : depth > 0

피처 그룹 3 — 작가
  birth_year            : 생년
  career_age            : 2026 - first_show_year (shows에서)
  career_stage          : 1~4 (나이+경력 기반)
  ln_followers          : ln(followers + 1)
  total_works           : Artsy 등록 작품 수
  for_sale_ratio        : for_sale / total_works
  request_ratio         : "Price on request" 작품 비율
  solo_count            : 개인전 횟수
  group_count           : 그룹전 횟수
  fair_count            : 아트페어 참여
  is_p1                 : Artsy Target Supply (주목 작가)
  artist_price_median   : 작가 내 가격 중앙값 (※ leakage 주의 — CV에서 제외)

피처 그룹 4 — 갤러리
  gallery_name          : 갤러리명 (categorical)
  gallery_type          : Gallery / Institution
  gallery_city_count    : 갤러리 도시 수
  has_seoul             : 서울에 갤러리 있음
  has_international     : 해외 도시에 갤러리 있음
  gallery_avg_price     : 갤러리 평균 가격 (leakage 주의)

피처 그룹 5 — 시장 컨텍스트
  currency              : USD / KRW / EUR / GBP
  vintage_premium       : work_age × (career_stage >= 3)
  freshness_discount    : work_age × (career_stage < 3)

Model: CatBoost Regressor
  cat_features: [support_type, medium_category, attribution_class,
                 canvas_type, gallery_name, gallery_type, currency]
```

### 4.2 Leakage 방지

| 피처 | Leakage 위험 | 대응 |
|------|:-----------:|------|
| artist_price_median | 높음 | CV fold 내에서만 계산, 또는 제외 |
| gallery_avg_price | 높음 | CV fold 내에서만 계산, 또는 제외 |
| for_sale_ratio | 낮음 | 수집 시점 고정값이므로 안전 |
| request_ratio | 낮음 | 수집 시점 고정값이므로 안전 |

### 4.3 Train/Val/Test 분할

```
방법 1: 시간 기반 (권장)
  Train: ~2023년 작품
  Val:   2024년 작품
  Test:  2025~2026년 작품

방법 2: 작가 기반 (Cold Start 평가용)
  Train: 작가 70%의 전체 작품
  Val:   작가 15%의 전체 작품 (학습 시 본 적 없는 작가)
  Test:  작가 15%의 전체 작품

방법 3: 5-Fold CV (기본)
  작가 단위 Stratified K-Fold (같은 작가가 train/val에 섞이지 않도록)
```

---

## 5. 데이터 전처리

### 5.1 이상치 제거

```python
# 1. 프로모션 가격 제거 (Gallery SoSo $1 등)
df = df[df.price_krw >= 100000]  # 10만원 미만 제거

# 2. 극단 고가 제거 (> 50억원)
df = df[df.price_krw <= 5_000_000_000]

# 3. 크기 이상치
df = df[df.width_cm > 1]
df = df[df.height_cm > 1]

# 4. 가격 범위 표기 → 중간값
# "US$12,500–US$13,750" → US$13,125
```

### 5.2 매체 분류 매핑

```python
MEDIUM_MAP = {
    'oil': ['oil on canvas', 'oil on linen', 'oil on panel', 'oil on wood'],
    'acrylic': ['acrylic on canvas', 'acrylic on panel', 'acrylic on linen'],
    'ink': ['ink and color on korean paper', 'ink on paper', 'sumi ink'],
    'mixed': ['mixed media on canvas', 'mixed media', 'mixed technique'],
    'watercolor': ['watercolor on paper', 'gouache'],
    'pigment': ['pigments on jangji', 'color on korean paper'],
    'print': ['screenprint', 'lithograph', 'etching', 'digital print'],
    'photo': ['c-print', 'archival pigment print', 'gelatin silver print'],
}

SUPPORT_MAP = {
    'canvas': ['canvas', 'linen'],         # factor 1.0
    'paper': ['paper', 'korean paper', 'jangji', 'hanji'],  # factor 0.3~0.5
    'panel': ['panel', 'wood', 'board'],    # factor 0.7
    'silk': ['silk'],                       # factor 별도
    'metal': ['aluminum', 'stainless'],     # factor 별도
}
```

### 5.3 갤러리 티어 추정

```python
def estimate_gallery_tier(gallery_name, gallery_cities, fair_count, avg_price):
    """수집된 데이터로 갤러리 티어 추정."""
    city_count = len(gallery_cities.split(',')) if gallery_cities else 0
    score = 0

    # 멀티 도시 갤러리 = 대형
    if city_count >= 4: score += 3
    elif city_count >= 2: score += 2

    # 아트페어 참여 (소속 작가 fair_count 합산)
    if fair_count >= 50: score += 3
    elif fair_count >= 20: score += 2
    elif fair_count >= 5: score += 1

    # 평균 가격
    if avg_price >= 50_000_000: score += 3  # 5천만+
    elif avg_price >= 10_000_000: score += 2
    elif avg_price >= 3_000_000: score += 1

    # Tier 분류 (1=메가, 5=신생)
    if score >= 8: return 1
    elif score >= 6: return 2
    elif score >= 4: return 3
    elif score >= 2: return 4
    else: return 5
```

---

## 6. 평가 지표

| 지표 | 정의 | 목표 |
|------|------|------|
| **MdAPE** | 절대 비율 오차 중앙값 | < 25% |
| **MAPE** | 절대 비율 오차 평균 | < 35% |
| **W30** | 30% 이내 비율 | > 60% |
| **W50** | 50% 이내 비율 | > 75% |
| **R²** | 결정 계수 | > 0.70 |

---

## 7. 실험 로드맵

### Phase 1: 데이터 준비 + EDA

- 이상치 제거, 통화 정규화
- 피처 엔지니어링 (ho, support_type, medium_category, gallery_tier)
- 호당 가격제 검증 (섹션 3)
- 가격 분포 분석 (카테고리별, 작가별, 갤러리별)

### Phase 2: 모델 학습

- CatBoost Hybrid 모델 학습
- 5-Fold CV (작가 단위 stratified)
- SHAP 분석: 피처 기여도 확인
- 호당 구조 검증 결과에 따라 모델 구조 조정 (시나리오 A/B/C)

### Phase 3: 검증

- Cold Start 평가 (학습에 없는 작가)
- 작가별 예측 일관성 검증

### Phase 4: 통합

- 기존 `estimate_generator` 파이프라인에 1차 시장 모델 추가
- 데이터 자동 갱신 파이프라인 (월 1회 Artsy API 수집)
- API 서빙 (1차 시장 가격 예측 엔드포인트)

---

## 8. 데이터 갱신 전략

### 8.1 자동 수집

```
수집 주기: 월 1회
방법: Artsy GraphQL API (scripts/crawl_artsy_complete.py)
소요 시간: ~70분
증분 처리: artwork_id 기준 중복 제거
```

### 8.2 추가 피처 보완 (Phase 2+)

| 소스 | 목적 | 우선순위 |
|------|------|:--------:|
| Artsy bio NLP 추출 | award, residency 정보 자동 추출 (679명 bio 보유) | 1 |
| 네이버 뉴스 API | critic_review_count (미디어 언급) | 2 |
| 갤러리 파트너십 | 실제 거래가 확보 | 3 |
| 작가 웹사이트/위키 | museum_collection 보완 | 3 |

---

## 9. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Artsy 가격 = 호가(listing), 실거래가 아님 | 모델이 호가를 학습 | Sold 비율로 거래 가능성 보정 |
| 가격 비공개 편향 (고가 → request) | 저가 편향 학습 | request_ratio 피처, 생존 분석 검토 |
| USD 기반 국제 가격 ≠ 국내 호당가 | 한국 시장 직접 적용 어려움 | KRW 서브셋(1,221건) 별도 분석 |
| Artsy API 변경/차단 | 데이터 갱신 불가 | 수집 데이터 보관, 재수집 간격 조절 |
| 호당 구조 불성립 | 이론 프레임 무용 | 시나리오 C(Full GBT)로 전환 |
| gallery_name categorical 과적합 | 194개 카테고리 | 갤러리 티어(1~5)로 압축, 또는 target encoding |
