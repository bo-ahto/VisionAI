# 실험계획서 v3 브레인스토밍: Artsy 데이터 기반 1차 시장 가격 예측

> **작성일**: 2026-04-13
> **배경**: Artsy GraphQL API로 한국 작가 30,046건 수집 완료. 가격 공개 11,118건, 1,029명.
> **핵심 변화**: v2의 전제(96건/11명, 크로스소스 매칭)가 완전히 바뀜.

---

## 1. v2 → v3 전제 변화

| 항목 | v2 (기존 계획) | v3 (실제 수집 결과) |
|------|---------------|-------------------|
| **데이터 규모** | 96건 / 11명 | **11,118건 / 1,029명** (116배) |
| **가격 성격** | 갤러리 전시 가격 (수동 수집) | **Artsy 갤러리 판매가** (1차 시장 직접) |
| **소스** | KADA + KAP + K-ARTMARKET + Artsy | **Artsy 단일 소스** |
| **이름 매칭** | 크로스소스 퍼지 매칭 필요 | **불필요** (동일 플랫폼) |
| **작가 프로필** | 외부 수집 후 매칭 | **같은 API에서 함께 수집** (shows, followers, bio) |
| **크기 데이터** | 98% | **98%** (동일) |
| **매체 정보** | 한글 (수동 분류) | **영문 상세** (Oil on canvas, Acrylic on Korean paper 등) |
| **갤러리 정보** | 제한적 | **갤러리명 + 유형 + 도시** (194개 갤러리) |
| **통화** | KRW 단일 | **USD 87% + KRW 11% + EUR/GBP 2%** |
| **호당 가격제** | 핵심 모델 구조 | **검증 가능한 가설**로 격하 |


## 2. 핵심 질문: 호당 가격제가 Artsy 데이터에도 적용되는가?

### 가설
v2는 `Price = α × Ho^0.74`를 전제로 설계됐다. 이 구조가 Artsy 국제 갤러리 데이터에서도 성립하는지가 v3의 핵심 검증 포인트.

### 예상 시나리오

**시나리오 A: 호당 구조 성립**
- Artsy 한국 작가도 크기-가격 관계가 power law를 따름
- β ≈ 0.7~0.8 범위
- → v2 모델 구조를 그대로 사용하되 데이터만 확대

**시나리오 B: 호당 구조 약하게 성립**
- 크기-가격 관계는 있지만 power law가 아님 (ex. 로그, 구간선형)
- 또는 β가 카테고리마다 다름 (painting vs sculpture)
- → 크기를 피처로 사용하되, 모델이 자유롭게 학습

**시나리오 C: 호당 구조 불성립**
- Artsy는 국제 시장이라 한국식 호당 가격제가 적용 안 됨
- 크기보다 작가 명성, 갤러리 티어가 가격을 결정
- → GBT 모델로 전체 피처 학습, 호당은 참고용

### 검증 방법
```python
# EDA Phase에서 실행
for artist in top_artists:
    works = artist_works[artist]
    plot(log(ho), log(price))  # power law면 직선
    estimate β via OLS: log(price) = log(α) + β × log(ho)
```


## 3. 데이터 특성과 주의점

### 3.1 가격 선택 편향 (Selection Bias)

Artsy에서 가격 공개율 37%. 비공개 이유:
- **Price on request (27%)**: 고가 작품일수록 비공개 → 공개 가격은 저가 편향
- **Sold (25%)**: 판매 완료 후 가격 삭제 → 인기 작품의 가격 유실

**대응:**
- 공개 가격만으로 학습 (편향 인지하고 사용)
- 같은 작가의 공개/비공개 비율을 피처로 활용 (request_ratio)
- Sold 작품은 가격은 없지만 "거래 발생" 사실 자체가 정보

### 3.2 통화 혼재

| 통화 | 건수 | 비율 |
|------|------|------|
| USD | 9,691 | 87% |
| KRW | 1,221 | 11% |
| EUR | 103 | 1% |
| GBP | 102 | 1% |

**대응:**
- 고정 환율로 KRW 통일 (USD 1,380원 기준)
- 또는 `currency`를 피처로 포함 (KRW 가격 작품 = 국내 갤러리 특성)
- KRW 표기 작품은 국내 갤러리(Gallery Planet, Kimreeaa 등) → 호당 가격제 적용 가능성 높음

### 3.3 이상치

- **$1 작품**: Gallery SoSo의 프로모션 가격 → 제거 필요
- **$420,000+**: 이우환, 박서보 등 블루칩 → 별도 처리 또는 로그 변환
- **가격 범위 표기**: "US$12,500–US$13,750" → 중간값 사용

### 3.4 카테고리별 가격 구조 차이

- **Painting (69%)**: 호당 가격제 적용 가능, 면적-가격 관계 강함
- **Sculpture (8%)**: 3D 크기, 재료비 비중 높음, 호당 구조 약함
- **Photography/Print (6%)**: 에디션 수가 가격 결정 핵심
- **Mixed Media (8%)**: 다양한 가격 구조

→ 카테고리별 별도 모델 또는 카테고리를 피처로 포함


## 4. 모델 아키텍처 옵션

### Option A: CatBoost 단일 모델 (실용적)

```
Target: log(price_krw)
Features:
  작품: width_cm, height_cm, area, ho, log_ho, depth_cm
        medium_category, support_type, attribution_class
        year, is_recent (최근 2년)
  작가: birth_year, career_age, followers, log_followers
        total_works, for_sale_ratio
        solo_count, group_count, fair_count
        is_p1, request_ratio
  갤러리: gallery_name (categorical), gallery_type
          gallery_city_count, has_seoul, has_international
  통화: currency (USD/KRW/기타)
```

**장점:** 기존 경매 모델과 동일한 파이프라인, 검증된 접근법
**단점:** 호당 구조가 모델 내부에 숨겨짐

### Option B: Two-Stage (호당 이론 + ML)

```
Stage 1: Size Effect (호당 가격 곡선)
  - Painting만: log(price) = log(α_artist) + β × log(ho) + ε
  - β를 데이터에서 추정 (v2의 0.74 가정 검증)
  - α_artist = 작가별 고정효과

Stage 2: α Prediction (작가 프리미엄)
  - Target: log(α_artist) from Stage 1
  - Features: artist profile (shows, followers, career_age...)
  - Model: CatBoost

Final: Price = predicted_α × Ho^estimated_β × medium_factor × gallery_factor
```

**장점:** 이론 기반, 해석 가능, v2 구조와 연속성
**단점:** Painting 외 카테고리에 적용 어려움, 단계별 오차 누적

### Option C: Hybrid (추천)

```
CatBoost 모델이지만 호당 이론 기반 피처를 포함:
  - ho, ho_power (ho^0.74), log_ho
  - alpha_estimate = price / ho^0.74 (작가 내 중앙값)
  - artist_avg_alpha (작가별 평균 α)
  - ho_price_residual = actual_price - ho^0.74 × median_alpha

이론적 피처를 넣되, 모델이 자유롭게 학습.
SHAP 분석으로 호당 구조가 실제로 사용되는지 사후 검증.
```

**장점:** 이론의 장점(해석성) + ML의 장점(유연성), 가장 높은 정확도 기대
**단점:** 피처 엔지니어링 복잡

### 추천: Option C (Hybrid)

11K 데이터에서 CatBoost가 충분히 학습 가능하고, 호당 이론 피처가 중요하면 SHAP에서 드러남.


## 5. 피처 엔지니어링 상세

### 5.1 크기 → 호수 변환

```python
def area_to_ho(width_cm, height_cm):
    """Artsy cm 데이터 → 한국 호수 변환."""
    area = width_cm * height_cm
    # F형 기준 호수 테이블 매핑 (가장 일반적)
    HO_TABLE = {0: 180, 1: 364, 2: 520, 3: 727, ...}
    # 가장 가까운 호수 반환
    ...
```

### 5.2 매체 분류

Artsy 영문 매체 → 한국 가격 모델 카테고리:

| Artsy medium | 분류 | support_type |
|-------------|------|-------------|
| Oil on canvas | 유채 | canvas |
| Acrylic on canvas | 아크릴 | canvas |
| Oil on linen | 유채 | canvas |
| Color on Korean paper | 채색 | paper |
| Ink and color on Korean paper | 수묵채색 | paper |
| Pigments on Jangji | 채색 | paper |
| Mixed media on canvas | 혼합 | canvas |
| Watercolor on paper | 수채 | paper |

### 5.3 갤러리 티어 추정

Artsy 데이터에서 갤러리 티어를 추정하는 방법:

```python
# fair_count: 해당 갤러리 소속 작가들의 art fair 참여 횟수
# gallery_cities: 다도시 갤러리 = 규모 큼
# avg_price: 갤러리 평균 작품 가격
# artist_count: 갤러리 소속 작가 수 (Artsy 기준)

gallery_tier_score = (
    fair_count_norm * 0.3 +
    city_count_norm * 0.2 +
    avg_price_norm * 0.3 +
    artist_count_norm * 0.2
)
```

### 5.4 작가 레벨 피처

| 피처 | 소스 | 설명 |
|------|------|------|
| followers | Artsy API | 시장 관심도 (log 변환) |
| solo_count | Shows API | 개인전 횟수 → 커리어 레벨 |
| group_count | Shows API | 그룹전 횟수 |
| fair_count | Shows API | 아트페어 참여 → 갤러리 급 |
| total_works | Artsy API | 생산성 지표 |
| for_sale_ratio | 계산 | 판매중/총작품 = 수요 지표 |
| request_ratio | 계산 | "Price on request" 비율 → 고가 작가 지표 |
| is_p1 | Artsy API | 블루칩 작가 여부 |
| career_age | 계산 | 첫 전시 ~ 현재 (shows 데이터) |
| price_median | 계산 | 작가 내 가격 중앙값 (leakage 주의) |


## 6. v2 피드백 항목의 v3 반영 상태

| # | v2 피드백 | v3 반영 | 비고 |
|---|----------|---------|------|
| 1 | Career Age | Artsy shows에서 계산 가능 | 첫 전시 연도 추출 |
| 2 | 전시 기관 티어 | fair_count + gallery 데이터로 추정 | 더 풍부한 데이터 |
| 3 | 3호 이하 점당 가격 | 면적 기반 필터 가능 | area < 727cm² |
| 4 | 지지체/에디션 구분 | attribution_class + medium 파싱 | Unique/Edition 구분 있음 |
| 5 | F/P/M/S형 호수 | aspect_ratio로 자동 판별 | dimensions에서 계산 |
| 6 | 갤러리 명성 방향 | gallery 피처로 학습 | 데이터가 결정 |
| 7 | 작품연식 × 경력 | date + career_age 인터랙션 | 그대로 적용 |
| 8 | 레지던시 횟수 | Artsy shows에 일부 포함 | 완전하진 않음 |
| 9 | 비평 정량화 | followers가 대리지표 | 간접적 |
| 10 | 아트페어 편향 제거 | gallery_type 피처로 제어 | 데이터로 해결 |
| 11 | 서울옥션 데이터 | K-ARTMARKET으로 검증용 확보 | 교차 검증 가능 |
| 12 | 경매 모델 예측값 피처 | 기존 auction model과 연결 | 동일 작가 매칭 필요 |


## 7. 실험 로드맵

### Phase 1: 데이터 준비
- 이상치 제거 ($1 프로모, 극단 고가)
- 통화 정규화 (→ KRW)
- 피처 엔지니어링 (ho, medium, gallery_tier, artist features)
- Train/Val/Test 분할 (시간 기반 또는 작가 기반)

### Phase 2: EDA + 호당 검증
- 크기-가격 power law 검증 (전체 + 작가별)
- β 추정 (v2의 0.74 가정 확인)
- 카테고리별 가격 구조 분석
- 갤러리별 가격 수준 분석

### Phase 3: 모델 학습
- Baseline: log(price) ~ log(area) 단순 회귀
- CatBoost Hybrid 모델 학습
- SHAP 분석으로 피처 기여도 확인
- 하이퍼파라미터 튜닝

### Phase 4: 검증 + 비교
- K-ARTMARKET 경매 데이터와 교차 검증
- 기존 경매 모델과 성능 비교
- 작가별 예측 일관성 확인
- 1차/2차 시장 가격 갭 분석

### Phase 5: 통합
- 기존 `estimate_generator` 파이프라인에 1차 시장 모델 추가
- Cold Start 처리 (Artsy 프로필은 있지만 가격이 없는 작가)
- API 서빙 (1차 시장 가격 예측 엔드포인트)


## 8. 기대 효과

| 지표 | v2 예상 | v3 예상 |
|------|---------|---------|
| 학습 데이터 | ~200건 | **~10,000건** |
| 작가 수 | ~50명 | **~1,000명** |
| 피처 수 | ~15개 | **~25-30개** |
| 예상 MAPE | 30-40% | **15-25%** (데이터 풍부) |
| 커버리지 | 한국 국내 | **한국 + 국제 갤러리** |
| 갱신 주기 | 수동 | **월 1회 자동** (GraphQL API) |


## 9. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Artsy 가격 ≠ 실제 거래가 | 모델이 호가를 학습 | Sold 비율로 보정, K-ARTMARKET 비교 |
| USD 기반 국제 가격 ≠ 국내 호당가 | 한국 시장 적용 어려움 | KRW 작품 서브셋으로 별도 분석 |
| 가격 비공개 편향 | 고가 작품 학습 불가 | request_ratio 피처, 생존 분석 검토 |
| Artsy API 변경/차단 | 데이터 갱신 불가 | 수집 데이터 보관, 재수집 간격 조절 |
| 호당 구조 불성립 | v2 이론 프레임 무용 | Option A(순수 ML)로 전환 |
