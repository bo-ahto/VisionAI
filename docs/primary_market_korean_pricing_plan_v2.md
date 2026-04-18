# 한국 작가 1차 시장(갤러리) 가격 예측 실험계획서 v2

> **작성일**: 2026-04-09
> **버전**: v2 (현장 피드백 12건 반영)
> **범위**: 한국 작가 한정, 갤러리/아트페어 가격 예측
> **현재 데이터**: 96건 / 11명 작가 / 가격 유효 94건 / 가격 범위 30만~1억 56만원

---

## 0. v2 개선 사항 요약

v1 계획서에 대한 현장 전문가 피드백을 반영한 개정판. 피드백 원문은 별도 문서(`실험계획서_피드백_답변.md`)에 정리되어 있으며, 본 v2에서 12개 개선 사항을 실제 반영했다.

| # | 개선 항목 | 반영 섹션 |
|---|----------|----------|
| 1 | 경력 분류에 Career Age(첫 개인전 이후 경과 연수) 추가 | 6.2, 7.2 |
| 2 | 전시 기관 티어 가중치 (카페 갤러리 vs 국제갤러리 구분) | 3.2, 6.2 |
| 3 | 3호 이하 소품은 점당 가격 체계로 분리 | 2.1, 3.1, 4.2 |
| 4 | 지지체(캔버스/종이) 및 유니크/에디션 1차 필터 | 1.2, 3.1, 4.2 |
| 5 | F/P/M/S형 호수 변환 (aspect_ratio 기반 추정) | 4.1 |
| 6 | 갤러리 명성 효과를 한국 시장 방향(+)으로 수정 | 2.3, 3.2 |
| 7 | 작품 연식 × 경력 인터랙션 피처 | 6.3 |
| 8 | 국공립 레지던시 선정 횟수 피처 | 3.2, 6.2 |
| 9 | 비평(전문가 평가) 정량화 로드맵 | 6.4, 8.2 |
| 10 | 작가 고정효과(fixed effect)로 아트페어 편향 제거 | 4.3 |
| 11 | 서울옥션 크롤러 데이터 1차 활용 | 9.1 |
| 12 | 경매 모델 예측값을 1차 가격 예측의 피처로 통합 | 3.3 |

---

## 1. 현재 데이터 현황

### 1.1 한국 작가 데이터 요약

| 항목 | 값 |
|------|-----|
| 총 건수 | 96건 (11명 작가) — 가격 유효 94건 |
| 가격 범위 | 30만 ~ 1억 56만원 |
| 중앙값 / 평균 | 300만원 / 810만원 |
| 전시 유형 | 개인전 54, 그룹전 27, 단체전 10, 아트페어 3 (가격 유효 기준 94건) |
| 참여 갤러리 | 8개 |

### 1.2 지지체별 가격 분포 (신규 분석)

v1에서 놓쳤던 지지체 구분이 실제로 큰 가격 차이를 만든다:

| 지지체 | 건수 | 중앙가 | 비고 |
|--------|:---:|-------:|------|
| 캔버스 (canvas/linen) | 60 | 215만 | 주류 (가격 유효 전부) |
| 혼합 (캔버스+종이/한지) | 9 | 911만 | 특수 혼합 |
| 종이 (paper/한지) | 17 | 50만 | **캔버스의 25% 수준** |
| 면 (cotton) | 3 | 1,400만 | 특수 재료 |
| 목재/패널 | 1 | 300만 | |
| 기타 (혼합재료 등) | 6 | 1,800만 | |

합계 96건 (11명 기준). 가격 유효 94건.

**핵심 발견**: 종이 작업을 구분 없이 호당가 모델에 넣으면 작가 내 CV가 인위적으로 높아진다. 순이지 34건의 CV 0.55는 대부분 지지체 혼합(종이 13 + 캔버스 20 + 목재 1)이 원인이며, v2 방식 적용 시 실측 기준 CV가 0.073으로 감소 (섹션 5.4 참조).

### 1.3 작가별 가격 분포

| 작가 | 건수 | 중앙가 | 비고 |
|------|:---:|-------:|------|
| 김윤신 | 3 | 8,620만 | 원로, 최고가 |
| 김주리 | 5 | 2,000만 | 안정적 |
| 임노식 | 4 | 1,800만 | |
| 이진주 | 3 | 1,400만 | |
| 주연수 | 12 | 816만 | 최다 건수 |
| 정수정 | 8 | 500만 | 변동성 |
| 조이솝 | 4 | 250만 | |
| 이동혁 | 3 | 120만 | |
| 남석우 | 8 | 115만 | |
| 이시현 | 10 | 90만 | |
| 순이지 | 34 | 60만 | 종이 13 + 캔버스 20 + 목재 1 혼재 |

---

## 2. 한국 갤러리 가격 책정 구조

### 2.1 호당 가격제 + 점당 가격제 (이중 구조)

한국 갤러리 가격 체계는 크기에 따라 두 가지 방식이 공존한다:

**4호 이상 (호당 가격제)**
```
Price = α × Ho^β × 지지체_보정 × 매체_보정
  α: 작가 호당 기준가
  β ≈ 0.74 (체감 효과, Shin 2010 + 파일럿 실측)
```

**3호 이하 (점당 가격제)** — 신규 반영
```
Price = α × ho_curve(ho) × small_discount(ho)
  ho_curve(ho) = 1^0.74 if ho == 0 else ho^0.74   # 0호는 1호 곡선값으로 flat
  small_discount: 업계 관행상 소품 할인율
    0호: α × 1^0.74 × 0.50 = 0.50α   (최소 점당가, 초소형 특례)
    1호: α × 1^0.74 × 0.70 = 0.70α
    2호: α × 2^0.74 × 0.80 = 1.34α
    3호: α × 3^0.74 × 0.90 = 2.03α
  4호 이상: α × ho^0.74 (할인 없음, 2.79α부터 시작)
  
  이유: 소품은 최소 거래 단위로 할인 책정 (업계 관행).
        호당가 곡선에 곱셈 할인을 적용해 4호 경계에서 단조 증가 유지.
  ※ 0호(10×10cm 등 초소형)는 곡선값을 1^0.74로 고정하되,
    할인율(0.50)은 1호(0.70)보다 더 낮아 실제 가격은 0.50α로
    1호 0.70α보다 더 싸게 책정된다.
```

### 2.2 경력별 호당가 기준 (업계 관행)

| 경력 | 나이대 | 호당 가격 | 10호 기준 | career_stage 인코딩 |
|------|-------|----------|----------|:-----------------:|
| 신진 | 20대 | 5~8만원 | 50~80만원 | **1** |
| 신진 후기 | 30대 | 10~15만원 | 100~150만원 | **2** |
| 중견 초기 | 40대 | 15~20만원 | 150~200만원 | **3** |
| 중견 | 50대 | 25~30만원 | 250~300만원 | **3** |
| 원로 | 60대+ | 40~50만원+ | 400~500만원+ | **4** |
| 블루칩 | - | 100만원+ | 1,000만원+ | **4** (원로와 동일) |

> 업계 관행상 6단계로 나누지만, 모델 입력에서는 시장 구조(신진/신진후기/중견/원로)에 맞춰 4단계(1~4)로 압축한다. "블루칩"은 원로(4) 범주 내의 특수 케이스로 취급하며, `auction_avg_price` 등 2차 시장 피처가 따로 고점 효과를 흡수한다.

### 2.3 가격 결정 요인 (학술 근거 + 한국 시장 반영)

| 요인 | 가격 효과 | 학술 근거 | 한국 시장 조정 |
|------|:--------:|----------|--------------|
| 작가 경력 단계 | 높을수록 가격↑ | Rengers & Velthuis (2002) | |
| 전시 이력 × 기관 위신 | 높을수록 가격↑ | Fraiberger et al. (2018) | ArtFacts 랭킹 원리 |
| **소속 갤러리 등급 (메이저↑)** | **가격↑** | - | **한국: 메이저 갤러리 프리미엄** ※ |
| 미술관 소장/레지던시 | 많을수록 가격↑ | Fraiberger et al. (2018) | 국공립 레지던시 별도 가중 |
| 경매 실적 | 있을수록 가격↑ | 2차 시장 검증 | |
| 시장 트렌드 | 변동 | - | |

※ **중요 수정 사항 (부호 규칙 명시)**: Schönfeld & Reinstaller(2007)는 유럽 투자형 갤러리에서 갤러리 명성과 가격의 음의 상관(유망 신진을 낮은 진입가로 판매)을 보고했으나, 한국 시장에서는 메이저 갤러리(국제, 학고재, PKM, 현대 등) 소속이 곧 가격 프리미엄으로 작동한다.<br>
**부호 규칙**: `gallery_tier` 인코딩은 본 리포지토리 기존 정의에 따라 **1=메가 갤러리, 5=신생 갤러리** (숫자가 작을수록 상위)이다. 따라서 "메이저일수록 가격↑"을 수식으로 표현하려면 `gallery_tier`의 회귀 계수 방향은 **음(-)**이 되어야 한다. v2에서 이 부호 규칙을 모든 회귀식에 일관되게 적용한다.

### 2.4 학술 근거

| 연구 | 핵심 발견 | 적용 |
|------|----------|------|
| Rengers & Velthuis (2002) | 1차 시장 hedonic 회귀 원형 | 기본 회귀식 |
| Beckert & Rössel (2013) | 가격은 상호주관적 명성 인정 과정에서 결정 | 명성 피처 근거 |
| Schönfeld & Reinstaller (2007) | 갤러리 명성 효과 (유럽) | **한국 시장에서는 방향 반전 필요** |
| Park et al. (2024) | Popularity + Ability 통합 모델 | 시간 가변 명성 |
| Shin (2010) | P = α × Ho^β, β < 1 (한국) | 비선형 크기-가격 |
| Fraiberger et al. (2018, Science) | 기관 위신이 커리어 궤적 결정 | 전시 기관 가중치 |

---

## 3. 실험 방법론 — 3가지 접근법

### 3.1 Option A: 이중 구조 호당가/점당가 모델 (즉시 적용)

**핵심 개선**: v1의 단일 호당가 모델을 이중 구조로 확장

```
입력 분류 (1차):
  지지체: 캔버스 / 종이 / 기타
  복제성: 유니크 / 에디션

호당가 기준선 학습 (α):
  학습 단계에서는 캔버스 + 유니크 작품만으로 작가별 α(호당 기준가)를 추정.
  종이/에디션은 α 학습에서 제외 (왜곡 방지).

예측 단계 (모든 지지체에 적용):
  크기 분기 (2차):
    ho ≤ 3: 점당 가격 (호당가 곡선 × 할인율, 연속성 유지)
      α × ho^0.74 × small_discount(ho) × support_factor × medium_factor
      small_discount:
        0호 → 0.50 (ho^0.74는 1^0.74로 고정)
        1호 → 0.70
        2호 → 0.80
        3호 → 0.90
    
    ho ≥ 4: 호당 가격 체계 (비선형, 할인 없음)
      α × ho^0.74 × support_factor × medium_factor
  
  지지체 보정 (양 분기 공통):
    support_factor: 캔버스=1.0, 종이=0.30~0.50, 목재/패널=0.70 등
    → 종이 작업은 캔버스 α 기준으로 계산 후 support_factor로 할인

  경계 연속성: 3호 할인가(2.03α) < 4호(2.79α) → 크기 단조 증가 보장

에디션: 별도 가격 체계 (에디션 넘버, 총 부수 기반, 본 모델 범위 외)
```

**정리**: α는 "캔버스 유니크 기준"으로만 학습하되, 예측 시에는 지지체 보정 계수를 곱해 종이 등 다른 지지체에도 적용한다. 에디션은 가격 메커니즘이 다르므로 별도 처리.

**장점**: 업계 관행 반영, 순이지 같은 혼합 작가의 CV 왜곡 해소, 적은 데이터로 작동

**단점**: 신규 작가의 α(호당 기준가) 불명 — Option B로 해결

### 3.2 Option B: 작가 명성 회귀 (데이터 수집 후)

**핵심 개선**: 전시 횟수 → 기관 위신 가중 점수로 대체

```
ln(α) = β₀
  + β₁ × career_stage (1~4)
  + β₂ × ln(career_age + 1)         ← 신규: 첫 개인전 이후 경과 연수
  + β₃ × ln(institutional_score + 1) ← 개선: 가중 점수 (0 보호 위해 +1)
  + β₄ × museum_collection_count    ← 국공립 미술관 소장 수
  + β₅ × residency_score            ← 신규: 국공립 레지던시 가중 점수
  + β₆ × gallery_tier               ← 부호: 음(-) (1=메가, 5=신생)
  + β₇ × has_auction_record
  + β₈ × ln(auction_avg_price + 1)
  + β₉ × award_score                ← 가중 수상 점수
  + ε

부호 예상 (한국 시장):
  β₁, β₂, β₃, β₄, β₅, β₇, β₈, β₉ > 0 (가격 상승)
  β₆ < 0 (gallery_tier 숫자↓ = 메가 → 가격↑)

institutional_score = Σ(기관 가중치 × 전시 횟수)
  기관 가중치: MMCA/서울시립 = 10, 국제갤러리급 = 5,
              중견 갤러리 = 3, 소형 = 1, 카페/대안공간 = 0.5
              Art Basel/Frieze = 10, KIAF = 5, 지역 페어 = 2

residency_score = Σ(레지던시 가중치 × 선정 횟수)
  Tier 1 (MMCA 창동/고양, 서울시립 난지) = 5
  Tier 2 (경기도립, 인천아트플랫폼, 금천예술공장) = 3
  Tier 3 (사립, 해외) = 2
```

**필요 데이터**: 50~100명 작가 프로필 (KADA 아카이브 기반)

**주의**: 독립변수 대부분이 작가 수준이므로 유효 표본은 작가 수에 가까움. mixed-effects 또는 hierarchical 모델 고려.

### 3.3 Option C: 경매 앵커 + 갤러리 업리프트

**핵심 개선**: 단순 연결이 아닌, 경매 모델 예측값을 Option B의 피처로 직접 주입

```
Step 1. 경매 모델 예측 (기존 시스템)
  auction_prediction = existing_auction_model.predict(작가, 매체, 크기)
  → 이 작가 작품이 한국 경매에 나오면 예상 낙찰가

Step 2. 갤러리 업리프트 모델 (신규)
  ln(gallery_price / auction_prediction) = f(
    gallery_tier,              ← 부호 음(-): 숫자↓ (메이저) → uplift↑
    exhibition_type,           ← 개인전 > 그룹전
    career_stage,              ← 신진일수록 uplift 불확실
    vintage_premium,           ← 신규: 중견/원로 한정 연식 프리미엄
    freshness_discount,        ← 신규: 신진 한정 재고 할인
    market_momentum
  )

Step 3. 최종 예측
  gallery_price = auction_prediction × exp(uplift)

Step 4. 경매 이력 없는 작가 (Cold)
  유사 작가 K-NN 매칭 → 이웃들의 uplift 평균 → Option B의 호당가 예측에 exp(평균 uplift)를 곱함
  gallery_price = option_b_prediction × exp(mean_uplift_of_knn)
```

**학술 근거**: Schönfeld & Reinstaller (2007)의 이중 명성 모델 실용화.

---

## 4. 실험 설계 (Option A 기준)

### 4.1 호수 변환 규칙 개선

v1의 F형 단순 변환 → aspect_ratio 기반 타입 추정

```python
def aspect_to_canvas_type(aspect_ratio):
    """종횡비로 F/P/M/S 타입 추정."""
    if abs(aspect_ratio - 1.0) < 0.1:
        return "S"  # 정방형
    elif aspect_ratio < 1.2:
        return "F"  # Figure (인물)
    elif aspect_ratio < 1.4:
        return "P"  # Paysage (풍경)
    else:
        return "M"  # Marine (해경)

def area_to_ho_by_type(area, ctype):
    """타입별 표준 면적 테이블에서 호수 매칭."""
    table = HO_TABLE[ctype]  # F/P/M/S 각각 별도 테이블
    return nearest_ho(area, table)
```

현실적 제약: 현재 데이터에 명시적 타입 정보 없음. aspect_ratio로 추정하되, 대부분 F형 범위(1.0~1.2)에 분포하므로 94건 파일럿에서는 단순 F형 변환의 영향이 크지 않을 것으로 예상. Phase 1 이후 타입별 변환 정밀화.

### 4.2 소품(3호 이하) 분리 처리

```python
SMALL_DISCOUNT = {0: 0.50, 1: 0.70, 2: 0.80, 3: 0.90}

def predict_price(artist, work):
    ho = area_to_ho_by_type(work.area, work.ctype)
    support_factor = SUPPORT_FACTOR[work.support_type]  # 캔버스 1.0, 종이 0.3~0.5
    medium_factor = MEDIUM_FACTOR[work.medium]
    
    if work.edition_size > 1:
        # 에디션 작품: 별도 로직
        return predict_edition_price(artist, work)
    
    # α는 Option A(호당가 역산 중앙값) 또는 Option B(회귀 예측값)
    if ho <= 3:
        # 소품: 호당가 곡선 × 할인율 (연속성 유지)
        # 0호는 1^0.74 × 0.50으로 flat 처리 (초소형 최소가)
        ho_curve = 1.0 ** 0.74 if ho == 0 else ho ** 0.74
        return artist.alpha * ho_curve * SMALL_DISCOUNT[ho] * support_factor * medium_factor
    else:
        # 호당 가격 (비선형)
        return artist.alpha * (ho ** 0.74) * support_factor * medium_factor
```

> 주의: 소품 분기에서도 `support_factor`를 반드시 곱해야 한다.
> 종이 1호 소품은 캔버스 1호 소품의 약 30~50% 가격이 정상이다.
> 
> 단조성 확인: 3호 할인가 (α × 2.26 × 0.90 = 2.03α) < 4호 (α × 2.79 = 2.79α) → 경계 연속.

### 4.3 검증 가설 (작가 고정효과 통제)

v1에서 아트페어 215만원이 김윤신 1명에서만 관측된 문제를 해결하기 위해 **작가 고정효과**로 편향을 통제한다.

```python
# 가설 3 재설계: 전시 유형 효과 (작가 고정효과)
# 전제: 4호 이상 캔버스 유니크 작품만 사용 (v2 호당가 모델 동일 조건)
#      0~3호 소품(점당 체계)과 종이/에디션/목재는 검증에서 제외

subset = data.filter(
    support_type == "canvas",
    is_edition == False,
    ho >= 4,
)

model: ln(price) ~ exhibition_type + C(artist_id) + ln(ho) + ε
→ artist_id 더미로 작가별 기저 가격(α)을 흡수
→ exhibition_type 계수만이 순수 전시 유형 효과
→ ln(ho)는 ho≥4 조건에서 정의되며, Shin(2010)의 β 추정도 재현 가능
```

이 방식으로 1명만 출품한 아트페어의 "전시 유형 효과"는 식별 불가능해지며, 복수 작가에서 관측되는 개인전 vs 그룹전 차이만 측정된다. 소품과 비(非)캔버스 작품에 대한 검증은 별도 서브셋으로 수행.

---

## 5. 파일럿 검증 결과 (94건, v1)

### 5.1 호당 가격 역산 결과

> CV(변동계수) = 표준편차/평균. 같은 작가 호당가의 일관성 측정.
> CV < 0.3 안정, 0.3~0.5 보통, > 0.5 불안정 — 호당가만으로 부족하여 추가 요인 필요.

| 작가 | 건수 | 호당가 중앙 | CV | 판정 |
|------|:---:|-----------:|:--:|:----:|
| 김윤신 | 3 | 215만 | 0.14 | 안정 |
| 김주리 | 5 | 17만 | 0.10 | 안정 |
| 이진주 | 3 | 117만 | 0.33 | 보통 |
| 임노식 | 4 | 9만 | 0.35 | 보통 |
| 남석우 | 8 | 12만 | 0.44 | 보통 |
| 주연수 | 12 | 33만 | 0.52 | 불안정 |
| 정수정 | 8 | 56만 | 0.58 | 불안정 |
| 이시현 | 10 | 6만 | 0.64 | 불안정 |
| 조이솝 | 4 | 15만 | 0.78 | 불안정 |
| 이동혁 | 3 | 30만 | 1.00 | 불안정 |
| 순이지 | 34 | 12만 | 0.55 | 불안정 |

안정 2, 보통 3, 불안정 6. idx 112(10x10cm) 1건은 0호 매핑으로 0 나누기 발생하여 제외 후 산출.

### 5.2 v1 가설 검증

**가설 1 (호당가 일정성)**: PARTIAL. 11명 중 5명 안정/보통, 6명 불안정.

**가설 2 (크기-가격 비선형)**: CONFIRMED.
```
ln(Price) = 12.94 + 0.74 × ln(Ho)
β = 0.74 (체감 효과, Shin 2010의 0.8~0.9보다 강함)
```

**가설 3 (전시 유형 영향)**: PARTIAL (작가 혼동 주의).
```
아트페어 215만 (김윤신 1명) — 고정효과 통제 후 재검증 필요
개인전 27만 vs 그룹전 9만 — 복수 작가 관측, 유효
```

### 5.3 LOO 교차 검증

| 지표 | 값 |
|------|-----|
| MdAPE | 28.0% |
| W30 (30% 이내) | 51.6% |
| W50 (50% 이내) | 58.1% |
| 최악 | 421% |

### 5.4 v1 한계와 v2 개선 방향

v1 파일럿에서 **CV 불안정의 주원인**이 피드백 Q3/Q4/Q6로 대부분 설명됨:

**순이지 재분석 (v2 방식 적용, 실측 기반)**

순이지 34건을 지지체, 매체, 호수별로 분리하면:

| 서브그룹 | 건수 | 가격 | 호당가 | 분류 |
|---------|:---:|-----|--------|------|
| 종이 수채 1호 (15.8×22.7) | 13 | 50만 (12건) + 변형 1건 | — | 점당 체계 또는 별도 |
| 목재 아크릴 (72.7×90.9) | 1 | 300만 | 해당 없음 | 목재 (별도) |
| 캔버스 아크릴 0호 (10×10, idx 112) | 1 | 30만 | 0호 매핑 | 점당 체계 (소품) |
| 캔버스 아크릴 5호 | 7 | 60만 (전부 동일) | 12만/호 | 호당가 (ho≥4) |
| 캔버스 아크릴 12호 | 1 | 150만 | 12.5만/호 | 호당가 |
| 캔버스 아크릴 15호 | 5 | 150~160만 | 10~10.7만/호 | 호당가 |
| 캔버스 아크릴 30호 | 4 | 300~330만 | 10~11만/호 | 호당가 |
| 캔버스 아크릴 50호 | 2 | 500~600만 | 10~12만/호 | 호당가 |

합계 34건 (종이 13 + 목재 1 + 캔버스 20).

**v2 필터 적용:**
- 종이 13건: 점당 체계로 분리 → 호당가 역산 대상 제외
- 목재 1건: 별도 처리 (지지체 다름)
- 캔버스 0호 1건 (idx 112): 소품 점당 체계
- **캔버스 호당가 모델 투입: 19건 (5호 이상)**

**재계산 결과** (캔버스 ho≥4 기준, 19건 실측):

| 통계 | 값 |
|------|-----|
| 호당가 평균 | 112,719원 |
| 호당가 표준편차 | 8,263원 |
| **CV** | **0.073** |

**결론**: v2의 이중 구조 + 지지체 필터를 적용하면 순이지 CV가 **0.55 → 0.073**으로 급감 (안정 구간). 이는 업계 관행대로 "호당가는 캔버스 유니크 작품 기준"이라는 전제를 반영한 결과이며, 11명 중 불안정 작가 다수가 지지체 혼합에 의한 것이라면 유사한 개선이 가능할 것으로 예상된다.

---

## 6. 피처 설계 (v2 확장)

### 6.1 기본 피처 (v1 유지)

```
작가 수준:
  name_kor, birth_year, nationality
작품 수준:
  width, height, area, ho_number, canvas_type
  support_type (캔버스/종이/기타), medium, is_edition, edition_size
  year_made (제작연도)
컨텍스트:
  gallery_name, gallery_tier, exhibition_type, exhibition_date
```

### 6.2 v2 신규 피처

| 피처 | 정의 | 데이터 소스 | 학술 근거 |
|------|------|------------|----------|
| **career_age** | 현재연도 - 첫 개인전 연도 | KADA CV | Fraiberger (2018) |
| **institutional_score** | Σ(기관 가중치 × 전시 횟수) | KADA + 수동 티어 DB | ArtFacts 랭킹 원리 |
| **museum_collection_count** | 국공립/기업 미술관 소장 수 | KADA | Fraiberger (2018) |
| **residency_score** | Σ(레지던시 가중치 × 선정) | KADA | 한국 미술계 관행 |
| **gallery_tier** | 소속 갤러리 등급 (1~5) | 수동 분류 | 한국 시장 (+) |
| **work_age** | 현재연도 - 제작연도 | 기존 | - |
| **vintage_premium** | 중견/원로 한정 연식 프리미엄 (work_age if career_stage≥3 else 0) | 파생 | 현장 피드백 |
| **freshness_discount** | 신진 한정 재고 할인 (work_age if career_stage<3 else 0) | 파생 | 현장 피드백 |
| **auction_prediction** | 경매 모델 예측값 | 기존 경매 시스템 | Schönfeld (2007) |
| **support_type** | 캔버스/종이/기타 | materials 파싱 | 현장 피드백 |
| **is_edition** | 유니크/에디션 | materials 파싱 | 현장 피드백 |

### 6.3 작품 연식 × 경력 인터랙션 (신규)

현장 피드백: "중견 이상은 전성기 작품이 더 비싸고, 신진은 최신작일수록 가격이 상승"

```python
# 비대칭 효과를 단일 계수로 표현 불가 → 두 개의 파생 피처 사용
def vintage_premium(work_age, career_stage):
    """중견/원로: 빈티지 프리미엄 (연 2%)"""
    return work_age if career_stage >= 3 else 0

def freshness_discount(work_age, career_stage):
    """신진: 신선도 할인 (연 5%)"""
    return work_age if career_stage < 3 else 0

# 회귀식 추가 항:
#   + β_vintage × vintage_premium   (예상 계수 ≈ +0.02)
#   + β_freshness × freshness_discount (예상 계수 ≈ -0.05)
#
# 예시:
#   중견/원로 10년 작품: vintage_premium=10, freshness_discount=0 → +0.20
#   신진 10년 작품: vintage_premium=0, freshness_discount=10 → -0.50
```

이 계수는 데이터로 추출해야 하며, 현재 96건으로는 불안정하므로 Phase 1 이후 추정. 단일 `work_age × career_dir` 피처로는 비대칭 기울기(중견 +2% vs 신진 -5%)를 표현할 수 없으므로 **두 개의 분리된 피처**로 설계한다.

### 6.4 비평 정량화 (Phase 2+)

현장 피드백: "미디어 언급과 별개로 전문가 비평 정량화 가능?"

```
Tier 1 (단순, 즉시 가능):
  critic_review_count: 월간미술/아트인컬처 리뷰 건수
  
Tier 2 (중간, Phase 2):
  critic_review_weighted: 매체 등급 × 리뷰 건수
  
Tier 3 (고급, Phase 3+):
  critic_sentiment: NLP 감성 분석 (긍정/부정)
  critic_author_score: 유명 비평가 리뷰 = 높은 가중치
```

---

## 7. 데이터 확장 전략

### 7.1 필요 데이터

| 우선순위 | 데이터 | 소스 | 검증 | 기대 건수 |
|:--------:|--------|------|:----:|:---------:|
| 1 | 갤러리 판매 데이터 | 갤러리 파트너십, 아트페어 | - | +500건 |
| 2 | 작가 프로필 (학력/전시/수상/레지던시/소장) | KADA 아카이브 | VERIFIED | 100명+ |
| 3 | 전시 기관 티어 DB | 수동 구축 + ArtFacts 참조 | - | 200개 기관 |
| 4 | 서울옥션 낙찰 데이터 | **서울옥션 크롤러 (개발 완료)** | - | 수만 건 |
| 5 | K-ARTMARKET 경매 | K-ARTMARKET (웹 크롤링) | PARTIAL | 수만 건 |
| 6 | 미디어 언급 | 네이버 뉴스 API | VERIFIED | 실시간 |

### 7.2 작가 프로필 수집 항목 (v2 확장)

| 항목 | 설명 | 소스 |
|------|------|------|
| name_kor / name_eng | 작가명 | KADA |
| birth_year | 생년 | KADA |
| education | 학력 (학부/석사/박사 + 미대 여부) | KADA |
| first_solo_year | **신규: 첫 개인전 연도 (Career Age 계산)** | KADA |
| solo_exhibitions | 개인전 목록 (기관명 포함) | KADA |
| group_exhibitions | 그룹전 목록 (기관명 포함) | KADA |
| museum_shows | 미술관 전시 목록 (기관명 포함) | KADA |
| biennial_count | 비엔날레/트리엔날레 참여 | KADA + 수동 |
| **residencies** | **신규: 레지던시 선정 이력 (기관명, 연도)** | KADA |
| gallery_tier | 소속 갤러리 등급 | 수동 분류 |
| has_auction_record | 경매 이력 유무 | K-ARTMARKET + 서울옥션 |
| auction_avg_price | 경매 평균 낙찰가 | 동일 |
| museum_collection_count | 공공/기업 미술관 소장 수 | KADA |
| award_score | 수상 이력 가중 점수 | KADA |

---

## 8. 모델 비교 및 로드맵

### 8.1 접근법 비교

| 항목 | Option A (호당가/점당가 이중) | Option B (명성 회귀) | Option C (앵커+업리프트) |
|------|:----:|:----:|:----:|
| 필요 데이터 | 현재 96건 충분 | 작가 100명+ 프로필 | 경매+갤러리 페어 (+ cold-start 경로) |
| 신규 작가 예측 | 불가 | 프로필로 가능 | 경매 이력 있으면 직접, 없으면 유사 작가 K-NN + Option B 호당가 |
| 해석 가능성 | 매우 높음 | 높음 (β 계수) | 중간 |
| 기대 정확도 | 같은 작가 MdAPE ~20% (지지체 분리 후) | MdAPE ~40% | MdAPE ~30% |
| 학술 근거 | Shin (2010) + 업계 관행 | Rengers & Velthuis (2002) | Schönfeld (2007) |

### 8.2 권장 로드맵

| 단계 | 작업 | 기대 결과 | 선행 조건 |
|------|------|----------|----------|
| **Phase 0** | Option A 이중 구조 구현<br>지지체/에디션 필터<br>소품 점당 가격 분리<br>작가 고정효과 재검증 | 순이지 CV 0.55 → 0.073 (실측)<br>MdAPE ~20% 목표 | 현재 96건 |
| **Phase 1** | KADA 100명 프로필 수집<br>기관 티어 DB 200개 구축<br>Career Age + 레지던시 피처<br>Option B 파일럿 | 신규 작가 호당가 예측<br>회귀 계수 학술 검증 | 프로필 100명 |
| **Phase 2** | 갤러리 데이터 확대<br>경매 앵커 통합 (Option C)<br>작품 연식 효과 추정<br>비평 Tier 1 피처 | 신규 작가 MdAPE ~35%<br>경매 이력 작가 MdAPE ~25% | 갤러리 500건+ |
| **Phase 3** | 통합 모델<br>비평 감성 분석<br>실시간 시장 모멘텀 | 전체 MdAPE ~30%<br>1차+2차 시장 통합 | 동일작가 페어 20명+ |

---

## 9. 외부 데이터 수집 및 검증 결과

### 9.1 국내 소스 (v2 업데이트)

| 소스 | 데이터 | 접근 | 검증 |
|------|-------|------|:----:|
| KADA | 작가 프로필 (학력/전시/소장/레지던시) | 웹 크롤링 | VERIFIED |
| **서울옥션 (자체 크롤러)** | **서울옥션 낙찰 이력** | **자체 크롤러 (완료, 1차 데이터로 활용)** | **조건부** |
| K-ARTMARKET 경매 | 경매 lot (갤러리는 집계만) | 웹 크롤링 | PARTIAL |
| 공공데이터 전시 API | 14개 기관 전시 정보 | REST API | PARTIAL |
| 네이버 뉴스 API | 미디어 언급 | REST API (25K/일) | VERIFIED |
| 문화공공데이터 (category=I) | - | - | DEAD (URL 오류) |

> **서울옥션 데이터 경로 설명**: 서울옥션 본 사이트(9.3 섹션)는 이용약관상 외부 스크래핑 금지 대상이다. 본 프로젝트에서는 이를 인지하고 **내부 자체 크롤러**로 수집한 서울옥션 낙찰 데이터를 사용하며, 이 데이터는 K-ARTMARKET 공개 데이터와의 교차 검증 후 1차 입력으로 활용된다. 9.3 URL 테이블의 "LIVE (크롤링 금지)" 표기는 **사이트는 열람 가능하나 외부 공개 스크래핑은 금지**임을 의미하며, 자체 크롤러의 운영과는 별개이다.

### 9.2 글로벌 소스

| 소스 | 데이터 | 비용 | 검증 |
|------|-------|------|:----:|
| Artsy API | 13.5만 작가 | 무료 (비상업) | PARTIAL (retirement) |
| MutualArt | 93만 작가 경매 | $24~39/월 | PARTIAL |
| ArtFacts | 30만 작가 랭킹 | 유료 | PARTIAL |
| Artnet | 1,800만 경매 | $50~500/월 | 미확인 |

### 9.3 소스별 URL 및 실측 검증 (2026-04-06)

| # | 소스 | URL | 검증 |
|---|------|-----|:----:|
| 1 | KADA | k-artmarket.kr/kada/katEn/main/index.do | LIVE |
| 2 | K-ARTMARKET 경매 | k-artmarket.kr/member/work/WorkList.do | LIVE |
| 3 | K-ARTMARKET 통계 | k-artmarket.kr/member/stats/... | LIVE |
| 4 | 공공데이터 전시 API | data.go.kr/data/15105037/openapi.do | LIVE |
| 5 | 문화공공데이터 | culture.go.kr/data/openapi/... (category=I) | DEAD |
| 6 | 네이버 뉴스 API | developers.naver.com/docs/.../news.md | LIVE |
| 7 | Artsy API | developers.artsy.net/ | LIVE (retirement) |
| 8 | Artsy Artists | developers.artsy.net/v2/docs/artists | LIVE (retirement) |
| 9 | MutualArt | mutualart.com/ | LIVE |
| 10 | MutualArt 요금 | mutualart.com/plans | LIVE |
| 11 | ArtFacts 랭킹 | artfacts.net/lists/global_top_100_artists | LIVE (JS) |
| 12 | Artnet Price DB | artnet.com/price-database/ | PAYWALL |
| 13 | 서울옥션 | seoulauction.com/auction-list/results | LIVE (크롤링 금지) |
| 14 | 아이옥션 | insaauction.com/auction/offline_past_list_all.html | LIVE |
| 15 | K옥션 | k-auction.com/ | LIVE |
| 16 | 마이아트옥션 | myartauction.com/ | LIVE |
| 17 | Korean Artist Project | koreanartistproject.com/ (HTTP만 응답) | PARTIAL (HTTPS TLS 오류, HTTP만 200) |
| 18 | Google Trends | trends.google.com/ | UNRELIABLE |

> Phase 0 실제 작동 확인: KADA + 네이버 뉴스 API + 서울옥션 자체 크롤러

### 9.4 피처 매핑

| 소스 | 피처 | 중요도 |
|------|------|:------:|
| KADA | career_age, institutional_score, residency_score, award_score | 높음 |
| 서울옥션 크롤러 | auction_avg_price, auction_total_sold | 매우 높음 |
| K-ARTMARKET 경매 | 교차 검증 | 높음 |
| 공공데이터 전시 API | 전시 기관 DB 보강 | 중간 |
| 네이버 뉴스 | media_mention_count | 중간 |
| 갤러리 파트너 | gallery_net_price (타깃) | 핵심 |
| 기존 경매 모델 | auction_prediction (Option C 앵커) | 매우 높음 |

---

## 10. 참고 문헌

1. Rengers, M. & Velthuis, O. (2002). Determinants of Prices for Contemporary Art in Dutch Galleries, 1992-1998. *Journal of Cultural Economics*, 26(1), 1-28.
2. Beckert, J. & Rössel, J. (2013). The Price of Art: Uncertainty and Reputation in the Art Field. *European Societies*, 15(2), 178-195.
3. Schönfeld, S. & Reinstaller, A. (2007). The Effects of Gallery and Artist Reputation on Prices in the Primary Market for Art. *Journal of Cultural Economics*, 31(2), 143-153.
4. Park, S. et al. (2024). Artwork Pricing Model Integrating the Popularity and Ability of Artists. *AStA Advances in Statistical Analysis*.
5. Shin, J. (2010). Price Determinants and Genre Effects in the Korean Art Market. *Journal of Cultural Economics*, 35(4).
6. Fraiberger, S.P. et al. (2018). Quantifying Reputation and Success in Art. *Science*, 362(6416), 825-829.
7. Rosen, S. (1974). Hedonic Prices and Implicit Markets. *Journal of Political Economy*, 82(1), 34-55.
8. 월간 ANDA (2019). 그림값, 어떻게 책정되나.
