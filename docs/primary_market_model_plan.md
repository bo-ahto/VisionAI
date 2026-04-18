# 1차 시장(갤러리) 가격 예측 모델 고도화 계획

> **작성일**: 2026-04-03
> **배경**: 갤러리/아트페어 290건 예측 결과 갤러리 가격 대비 경매 모델 예측이 10.2x 과소추정.
> 원인: 대부분 모델/도메인 오류(Cold Start + 국제 시장 불일치). 정확한 비율은 ablation 미수행으로 미확정.
> **목표**: 1차 시장 가격을 직접 예측할 수 있는 모델 구축
>
> **Codex Review (2026-04-03)**: 아래 본문에 `[CR]` 표기는 Codex 리뷰에서 지적된 사항 반영.

---

## 0. Codex 리뷰 핵심 지적 사항

> 이 계획에 대해 독립적 AI 리뷰(OpenAI Codex)를 수행한 결과, 다음 핵심 이슈가 식별됨.

| # | 지적 | 심각도 | 반영 |
|---|------|:------:|------|
| 1 | **타깃 미정의**: "1차 시장 가격"이 게시가인지 실거래가인지 정의 안 됨 | 높음 | 섹션 1.3 추가 |
| 2 | **Artsy API 불안정**: retirement 경고, 필드 보장 안 됨 | 높음 | 섹션 2.1 주의사항 추가 |
| 3 | **60/25/15 분해 근거 없음**: ablation 없이 storytelling | 중간 | 섹션 1.1 수정 |
| 4 | **할인/censoring 무시**: sticker ≠ 실거래, 미판매 데이터 누락 | 높음 | 섹션 8 추가 |
| 5 | **트리 모델에 transfer learning 용어 오용** | 중간 | 섹션 4.2 수정 |
| 6 | **명성 피처 중복**: 5~6개가 같은 잠재변수의 프록시 | 중간 | 섹션 3.1 압축 권고 추가 |
| 7 | **rule-based multiplier는 편향 고착** | 중간 | 섹션 5.2 경고 추가 |
| 8 | **누락 문헌**: Beckert & Rössel, Rengers & Velthuis, Biased Auctioneers | 낮음 | 섹션 6 보완 |
| 9 | **4개 출력 분리 권장**: auction_anchor / gallery_list / net_transaction / confidence | 높음 | 섹션 4.5 추가 |

---

## 1. 현재 상태 진단

### 1.1 왜 실패했는가

| 실패 요인 | 기여도 | 구체적 원인 |
|-----------|--------|------------|
| **국제작가 도메인 불일치** | 지배적 | 모델이 한국 K-Auction 데이터만으로 학습. 해외 블루칩 작가(Baselitz, Katz 등)의 브랜드 가치를 전혀 모름 |
| **Cold Start 붕괴** | 큼 | 290건 전원 `artist_total_sold=0`, `comp_match_count=0`. 매체 평균으로만 폴백 → 모든 유화가 200만원대로 수렴 |
| **1차/2차 시장 구조 차이** | 미확정 | 갤러리 retail pricing vs 경매 공개 입찰. 1차/2차 가격 관계는 세그먼트/작가/생애주기에 따라 다름 |

> **[CR] 주의**: 위 기여도 비율은 ablation/counterfactual 분석 없이 추정한 것으로, 정확한 분해에는 (1) 경매 이력 있는 한국 vs 해외 작가 비교, (2) 같은 작가의 채널 간 가격 비교, (3) list price vs transaction price 분리가 필요함.

### 1.2 현재 모델의 한계

```
현재: 한국 경매(K-Auction) 전용 모델
  - 학습 데이터: K-Auction 55,938건
  - 작가 풀: 5,269명 (대부분 한국 작가)
  - 가격 신호: 경매 낙찰가 기반 비교매출, 작가 통계
  - 시장 범위: 한국 내 경매만

필요: 1차+2차 시장 통합 모델
  - 갤러리 판매가 + 아트페어 가격 + 경매 낙찰가 통합
  - 국제 작가 커버리지
  - 갤러리 등급, 전시 이력 등 1차 시장 고유 신호
```

### 1.3 [CR] 타깃 정의 — "1차 시장 가격"이란 무엇인가

> Codex 리뷰에서 가장 심각한 지적: 예측 타깃이 정의되지 않음.

| 가격 유형 | 정의 | 관측 가능성 | 비고 |
|-----------|------|:----------:|------|
| **Gallery List Price** | 갤러리 게시가 / 아트페어 표시가 | 높음 | 공개 정보이나, 실거래가와 10~50% 괴리 |
| **Gallery Net Price** | 실제 거래가 (할인 후) | 매우 낮음 | 비공개, 관계 의존적 |
| **Fair Sticker Price** | 아트페어 부스 표시가 | 중간 | list price와 유사하나 fair premium 포함 |
| **Auction Hammer** | 경매 낙찰가 | 높음 | 공개, buyer's premium 별도 |
| **Auction Hammer + Premium** | 낙찰가 + 수수료 | 높음 | 실 구매가, 낙찰가의 115~125% |

**결정 필요:**
- 현재 데이터의 `price`는 대부분 **gallery list price** (게시가) 또는 **fair asking price**
- 이것을 타깃으로 쓰면 "실거래가"가 아닌 "희망가"를 예측하는 모델이 됨
- 할인율 10~50%를 감안하면 list price 기반 모델은 **체계적 과대추정** 위험

**권장 접근:**
```
Phase 1: Gallery List Price 예측 (관측 가능, 데이터 확보 용이)
Phase 2: Discount Factor 모델 추가 (list → net 변환)
Phase 3: Net Transaction 예측 (파트너십 데이터 확보 시)
```

---

## 2. 데이터 전략

### 2.1 필요한 데이터 소스

| 소스 | 데이터 유형 | 확보 방법 | 난이도 | 기대 효과 |
|------|------------|----------|:------:|----------|
| **Artsy API** | 국제 경매 실적, 작가 정보, 전시 이력 | 공식 API (비상업용) | 중간 | 해외 작가 가격 앵커 확보 → Cold Start 해소 |

> **[CR] Artsy API 주의**: API retirement 경고가 있으며 "may be taken down at any time" 문구 존재.
> `auction_lots_count`, `partner_shows_count` 등 일부 필드는 공식 문서에 보장되지 않음.
> 대안: Artsy 웹 크롤링 (법적 리스크), MutualArt API, Artfacts.net 등 병행 검토 필요.
| **Artnet Price Database** | 1,800만건 경매 실적 (1983~) | 유료 구독 ($50~500/월) | 중간 | 가장 포괄적인 2차 시장 데이터 |
| **갤러리 판매 데이터** | 1차 시장 실거래가 | 갤러리 파트너십 또는 아트페어 데이터 제공 | 높음 | 1차 시장 직접 학습 가능 |
| **전시 이력 DB** | 전시 횟수, 참여 기관 등급 | Artsy API + 미술관 오픈 API | 중간 | 작가 명성 정량화 |
| **아트페어 가격** | 부스 가격, 출품작 리스트 | 아트페어 리포트, 언론 보도 | 높음 | 아트페어 프리미엄 학습 |

### 2.2 데이터 확보 우선순위

```
Phase 1 (즉시): Artsy API → 국제 작가 프로필 + 경매 실적
Phase 2 (1~2개월): Artnet 구독 → 글로벌 경매 데이터 통합
Phase 3 (3~6개월): 갤러리 파트너십 → 1차 시장 실거래 수집
Phase 4 (지속): 아트페어 데이터 축적
```

### 2.3 데이터 볼륨 추정

| 데이터셋 | 현재 | 목표 | 비고 |
|----------|------|------|------|
| 한국 경매 | 55,938건 | 유지 | K-Auction |
| 한국 타 경매사 | 0 | ~30,000건 | 서울옥션, 아이옥션 등 |
| 국제 경매 | 3개 피처(Artsy) | ~500,000건 | Artsy/Artnet 통합 |
| 갤러리 판매 | 0 | ~5,000~10,000건 | 파트너십 기반 |
| 작가 프로필 | 510명 | ~10,000명+ | Artsy API 확장 |

---

## 3. 신규 피처 설계

### 3.1 작가 명성 피처 (Artist Reputation Features)

학술 연구에 따르면 작가의 외적 명성(extrinsic reputation)이 작품 고유 속성보다 가격 예측에 더 중요.
특히 초기 고위 기관 접근 작가는 전시 2배, 경매 거래 4.7배, 최고가 5.2배 차이 (Science, 2018).

| 피처 | 정의 | 데이터 소스 | 타입 | 기대 중요도 |
|------|------|-----------|------|:----------:|
| `artist_exhibition_count` | 총 전시 횟수 (개인+그룹) | Artsy API | 수치 | 높음 |
| `artist_solo_exhibition_count` | 개인전 횟수 | Artsy API | 수치 | 높음 |
| `artist_museum_shows` | 미술관 전시 횟수 (갤러리 제외) | Artsy API | 수치 | 높음 |
| `artist_biennial_count` | 비엔날레/트리엔날레 참여 횟수 | Artsy/웹 크롤링 | 수치 | 중간 |
| `artist_institution_prestige_score` | 전시 기관의 평균 위신 점수 | 기관 등급 DB 구축 | 수치 | 매우 높음 |
| `artist_collection_count` | 공공 컬렉션 소장 기관 수 | Artsy API | 수치 | 높음 |
| `artist_years_active` | 활동 기간 (첫 전시~현재) | Artsy API | 수치 | 중간 |
| `artist_media_mention_count` | 주요 미술 매체 언급 횟수 | 웹 크롤링 | 수치 | 중간 |

> **[CR] 압축 권고**: 위 8개 중 exhibition_count, solo_count, museum_shows, collection_count,
> media_mentions는 같은 잠재 변수(작가 명성)의 중복 프록시. 희소 데이터에서 트리 과적합 위험.
> **PCA 또는 시간 인식 명성 인덱스 1~2개로 압축** 권장 (예: `reputation_score = f(전시, 컬렉션, 매체노출)`).

### 3.2 갤러리 피처 (Gallery Features)

갤러리 등급이 가격의 핵심 결정 요인. 동일 작가라도 메가갤러리 vs 로컬 갤러리 가격이 수배 차이.

| 피처 | 정의 | 데이터 소스 | 타입 | 기대 중요도 |
|------|------|-----------|------|:----------:|
| `gallery_tier` | 갤러리 등급 (1=메가~5=신생) | 수동 분류 + 규칙 | 범주 | 매우 높음 |
| `gallery_founding_year` | 설립 연도 | 갤러리 DB | 수치 | 중간 |
| `gallery_branch_count` | 지점 수 (국제화 지표) | 갤러리 DB | 수치 | 중간 |
| `gallery_artist_count` | 소속 작가 수 | Artsy/갤러리 웹 | 수치 | 낮음 |
| `gallery_avg_price` | 해당 갤러리의 평균 판매가 | 학습 데이터 | 수치 | 높음 |
| `gallery_country` | 갤러리 본사 국가 | 갤러리 DB | 범주 | 중간 |

**갤러리 등급 분류 기준 (안):**

| Tier | 정의 | 예시 |
|------|------|------|
| 1 (메가) | 연매출 $100M+, 글로벌 5개+ 지점 | Gagosian, Pace, Hauser & Wirth, David Zwirner |
| 2 (대형) | 연매출 $10M+, 국제 아트페어 상위 참여 | Thaddaeus Ropac, Lisson, Perrotin |
| 3 (중견) | 국내 상위 + 해외 아트페어 참여 | 국제갤러리, PKM, 학고재 |
| 4 (지역 명성) | 지역 내 인지도 | 갤러리현대, 아라리오 등 |
| 5 (신생/소형) | 5년 미만 또는 소규모 | 신진 갤러리 |

### 3.3 전시/판매 컨텍스트 피처

| 피처 | 정의 | 타입 | 기대 중요도 |
|------|------|------|:----------:|
| `sale_channel` | 판매 채널: auction / gallery / art_fair | 범주 | 매우 높음 |
| `fair_tier` | 아트페어 등급 (Art Basel=1 ~ 로컬=4) | 범주 | 높음 |
| `exhibition_type` | 개인전 / 그룹전 / 아트페어 | 범주 | 중간 |
| `is_primary_market` | 1차 시장 여부 (True/False) | 범주 | 높음 |
| `city_tier` | 도시 등급 (뉴욕/런던=1, 서울=2 등) | 범주 | 중간 |
| `currency_original` | 원래 가격 통화 (USD/EUR/KRW/GBP) | 범주 | 중간 |

### 3.4 국제 경매 실적 피처 (Cold Start 해소)

현재 모델의 최대 약점은 해외 작가의 경매 이력 부재. Artsy/Artnet 데이터로 해결.

| 피처 | 정의 | 현재 상태 | 개선 후 |
|------|------|----------|--------|
| `global_avg_price` | 국제 경매 평균가 | Artsy 3개 피처 (87.6% 결측) | Artnet 통합 → 결측 <20% |
| `global_median_price` | 국제 경매 중앙가 | 위와 동일 | 위와 동일 |
| `global_auction_count` | 국제 경매 거래 건수 | 위와 동일 | 위와 동일 |
| `global_max_price` | 국제 경매 최고가 | 없음 | 신규 추가 |
| `global_recent_price` | 최근 1년 국제 평균가 | 없음 | 신규 추가 |
| `global_price_trend` | 국제 가격 추세 | 없음 | 신규 추가 |
| `has_intl_auction_record` | 국제 경매 이력 유무 | 없음 | 신규 추가 (boolean) |

---

## 4. 모델 아키텍처 옵션

### 4.1 Option A: 통합 모델 (Unified Model)

```
[1차 시장 데이터 + 2차 시장 데이터]
    ↓
[통합 피처 빌더] — sale_channel, gallery_tier 등 시장 구분 피처 포함
    ↓
[단일 Ensemble Model] — CatBoost + LightGBM + XGBoost
    ↓
[채널별 Bias Correction]
    ↓
[예측: 어떤 채널이든 가격 예측]
```

**장점**: 데이터 효율적, 1차/2차 시장 간 정보 공유. sale_channel 피처가 시장 차이를 학습.
**단점**: 갤러리 데이터 비율이 낮으면 경매 패턴에 치우침. 타깃 혼재(list vs hammer) 문제.
**적합 시점**: 갤러리 데이터 5,000건 이상 + 타깃 정의 통일 후.

### 4.2 Option B: 도메인 적응 모델 (Domain Adaptation)

```
[2차 시장 모델] — 기존 경매 모델 (사전 학습 완료)
    ↓ Transfer Learning
[1차 시장 Fine-tuning] — 갤러리 데이터로 마지막 레이어만 재학습
    ↓
[도메인 보정 레이어] — 채널 프리미엄/디스카운트 학습
    ↓
[1차 시장 가격 예측]
```

**장점**: 갤러리 데이터가 적어도 경매 모델 지식을 활용 가능.
**단점**: CatBoost/트리 모델은 전통적 transfer learning이 어려움. 별도 설계 필요.
**적합 시점**: 갤러리 데이터 500~2,000건 수준일 때.

**구현 방안:**
- **2단계 학습**: 경매 모델 예측값을 피처로 사용 + 갤러리 데이터로 보정 모델 학습
- **Residual Learning**: `gallery_price = auction_prediction × channel_multiplier(features)`
- **Stacked Generalization**: 경매 모델 출력 + 1차 시장 피처 → 메타모델
- **Hierarchical Partial Pooling**: 작가/갤러리 그룹 간 정보 공유

> **[CR]** CatBoost/XGBoost/LightGBM은 전통적 "transfer learning" (last layer fine-tuning)이 불가.
> 정확한 용어는 stacking, residual learning, hierarchical partial pooling.

### 4.3 Option C: 채널 분리 모델 (Channel-Specific)

```
[공통 피처 빌더]
    ↓
[라우터: sale_channel?]
    ├─ auction → 기존 경매 모델 (검증 완료)
    └─ gallery → 갤러리 전용 모델 (신규)
         ↓
    [갤러리 모델]
      - 작가 명성 피처 (전시, 컬렉션)
      - 갤러리 등급 피처
      - 글로벌 경매 앵커 피처
```

**장점**: 각 시장 특성에 최적화, 기존 경매 모델 영향 없음.
**단점**: 갤러리 데이터 충분해야 함 (~10,000건+).
**적합 시점**: 충분한 갤러리 데이터 확보 후.

### 4.4 [CR] Option D: Anchor + Uplift 분리 모델 (Codex 권장)

```
[글로벌 경매 데이터]
    ↓
[Secondary Anchor Model] — 글로벌 경매 기준가 예측
    ↓
[Uplift Model] — log(primary_price / auction_anchor) 예측
    ↓ 별도 타깃 분리
[4개 출력]
  ├─ auction_anchor        경매 기준가
  ├─ expected_gallery_list 갤러리 게시가 추정
  ├─ expected_net_txn      실거래가 추정 (데이터 확보 시)
  └─ confidence / abstain  신뢰도 + 예측 불가 판정
```

**장점**: 타깃 정의가 명확, 경매 앵커와 1차 시장 프리미엄을 분리하여 해석 가능.
**단점**: 2단계 모델로 오차 전파 위험, 글로벌 경매 데이터 필수.
**적합 시점**: 글로벌 경매 앵커 확보 즉시.

> **[CR] 핵심**: "predict primary price"를 하나의 문제로 보지 말고,
> anchor + uplift로 분해하면 데이터 부족 상황에서도 해석 가능한 결과를 얻을 수 있음.

### 4.5 권장 로드맵 (수정)

```
즉시 (데이터 0건)     → Option B-1: 경매 모델 + 규칙 기반 채널 보정 계수
단기 (500~2,000건)   → Option B-2: 경매 예측 + 갤러리 보정 메타모델
중기 (5,000건+)      → Option A: 통합 모델
장기 (10,000건+)     → Option C: 채널 분리 전문 모델
```

---

## 5. 즉시 적용 가능한 개선 (데이터 추가 수집 없이)

### 5.1 Artsy API 활용 — 국제 작가 프로필 확장

현재 510명 → 목표 5,000명+ 작가 프로필 확보. Artsy API는 비상업 용도 무료.

```python
# Artsy API로 확보 가능한 정보
{
    "name": "Georg Baselitz",
    "birthday": "1938",
    "nationality": "German",
    "artworks_count": 1200,          # → artist_total_works
    "partner_shows_count": 85,        # → artist_exhibition_count
    "auction_lots_count": 3500,       # → global_auction_count
    "collections": "MoMA, Tate, ...", # → artist_collection_count
}
```

**기대 효과**: Cold Start D등급 → B/C등급으로 개선. 해외 작가 예측 정확도 대폭 향상.

### 5.2 규칙 기반 채널 보정 계수 (Rule-Based Channel Calibration)

Codex 리뷰에서 확인된 국적별/채널별 갭을 규칙으로 보정:

```python
# 채널 보정 계수 (현재 데이터 기반 추정)
CHANNEL_MULTIPLIER = {
    ("gallery", "KR"): 2.0,    # 한국 작가, 갤러리
    ("gallery", "WS"): 8.0,    # 해외 작가, 갤러리 (보수적)
    ("gallery", "JP"): 5.0,    # 일본 작가, 갤러리
    ("art_fair", "KR"): 3.0,   # 한국 작가, 아트페어
    ("art_fair", "WS"): 15.0,  # 해외 작가, 아트페어
}

# 적용: gallery_estimate = auction_prediction × multiplier
```

**주의**: 이 보정은 임시 조치. 실제 갤러리 데이터 학습으로 대체해야 함.

> **[CR] 경고**: 국적 기반 고정 multiplier는 편향을 시스템에 고착시킴.
> 더 나은 즉시 조치: 글로벌 경매 앵커를 확보하여 작가별 기준가를 계산하는 것.
> multiplier를 쓰더라도 매체×국적×전시유형 조합으로 세분화하고, 정기적으로 재보정해야 함.

### 5.3 갤러리 등급 피처 추가

현재 데이터에 이미 `gallery_name(EN)`, `gallery_Est.`, `gallery_Branch(#)` 있음.

```python
# 갤러리 등급 자동 분류 규칙
def classify_gallery_tier(name, branch_count, est_year):
    mega = {"Gagosian", "Pace", "Hauser & Wirth", "David Zwirner"}
    large = {"Thaddaeus Ropac", "Lisson", "Perrotin", "White Cube", "Lehmann Maupin"}
    if name in mega: return 1
    if name in large: return 2
    if branch_count >= 3: return 2
    if 2026 - est_year >= 30: return 3
    if 2026 - est_year >= 10: return 4
    return 5
```

---

## 6. 학술 근거 및 참고 문헌

### 6.1 가격 결정 요인 연구

| 연구 | 핵심 발견 | 시사점 |
|------|----------|--------|
| [Kim & Kim (2024), SAGE](https://journals.sagepub.com/doi/full/10.3233/KES-230041) | XGBoost 2단계 모델이 경매 가격 예측에 효과적 | 가격대별 분리 학습 전략 유효 |
| [Aubry et al. (2023), Harvard](https://hdsr.mitpress.mit.edu/pub/1vdc2z91) | 이전 거래가가 가장 강력한 예측자, 이미지는 Cold Start에서만 유의 | 글로벌 거래 이력 확보가 최우선 |
| [Fraiberger et al. (2018), Science](https://www.science.org/doi/10.1126/science.aau7224) | 초기 고위 기관 접근이 커리어 성공의 핵심 결정 요인 | 전시 기관 등급 피처의 중요성 |
| [Springer (2024)](https://link.springer.com/article/10.1007/s10182-024-00504-3) | 작가의 인기도(popularity) + 능력(ability) 통합 모델 | 전시 횟수 + 비평 언급 = 명성 정량화 |
| [ArXiv 2512.23078 (2025)](https://arxiv.org/html/2512.23078v1) | 딥러닝 + 이미지 멀티모달이 Cold Start에서 의미있는 기여 | 이미지 피처 재검토 가치 (갤러리 컨텍스트에서) |

### 6.2 1차/2차 시장 가격 관계

일반론:
- 1차 시장(갤러리)은 작가/갤러리가 가격을 설정 (controlled pricing)
- 2차 시장(경매)은 수요/공급에 의한 공개 경쟁 가격 (market pricing)
- **일반적으로 2차 시장이 1차보다 높거나 비슷** (성공 작가 기준)
- 신진 작가는 1차 > 2차 가능 (경매에서 가치가 아직 미검증)

출처:
- [Artland Magazine — Primary vs Secondary](https://magazine.artland.com/the-primary-versus-the-secondary-art-market/)
- [OneArtNation — The Primary vs Secondary Art Market](https://www.oneartnation.com/the-primary-vs-secondary-art-market/)
- [Art-Mine — Primary and Secondary Markets](https://art-mine.com/collectors-corner/2020/07/all-about-the-primary-and-secondary-art-markets/)

### [CR] 6.3 추가 문헌 (Codex 리뷰 권장)

| 연구 | 핵심 내용 | 적용 |
|------|----------|------|
| [Beckert & Rössel (2013), European Sociological Review](https://www.tandfonline.com/doi/abs/10.1080/14616696.2013.767923) | 갤러리 가격은 불확실성 하 평판 기반 결정. 시장 가격이 아닌 사회적 구성 | 1차 시장 가격 형성 메커니즘 이해 |
| [Rengers & Velthuis (2002), Journal of Cultural Economics](https://ideas.repec.org/a/kap/jculte/v26y2002i1p1-28.html) | 네덜란드 갤러리 가격 결정 요인 실증 분석. 갤러리 등급, 작가 경력, 크기 | 1차 시장 hedonic 모델의 선행 연구 |
| [Pownall & Graddy (2016), Biased Auctioneers, Journal of Finance](https://researchportal.ip-paris.fr/en/publications/biased-auctioneers/) | 경매 사전 추정가의 체계적 편향 분석 | 경매 앵커의 편향 보정 필요성 |
| [Fraiberger et al. (2018), Science](https://pubmed.ncbi.nlm.nih.gov/30409804/) | 초기 고위 기관 접근 → 전시 2x, 거래 4.7x, 최고가 5.2x | institution_prestige_score 피처의 학술적 근거 |

---

## 7. 기대 효과

### 7.1 단계별 개선 목표

| 단계 | 작업 | 기대 결과 |
|------|------|----------|
| **즉시** | Artsy API 작가 프로필 확장 + 규칙 보정 | 한국 작가 갭 2.0x → 1.3x, 해외 53.6x → 10x |
| **3개월** | 국제 경매 데이터 통합 + 갤러리 tier 피처 | 전체 갭 10.2x → 3~4x |
| **6개월** | 갤러리 데이터 학습 + 도메인 적응 모델 | 전체 갭 3x → 1.5x |
| **12개월** | 통합 모델 + 전시 이력 피처 | 1차 시장 MdAPE < 50% 목표 |

### 7.2 피처 중요도 예상 (1차 시장 모델)

```
예상 순위 (1차 시장):
  1. gallery_tier                 ~15%  ← 신규 (가장 큰 변화)
  2. global_avg_price             ~12%  ← 기존 확장
  3. artist_exhibition_count      ~10%  ← 신규
  4. sale_channel                  ~8%  ← 신규
  5. artist_institution_prestige    ~7%  ← 신규
  6. comp_artist_avg               ~6%  ← 기존 (글로벌 확장)
  7. ln_surface_area               ~5%  ← 기존
  8. medium_category               ~5%  ← 기존
  9. fair_tier                     ~4%  ← 신규
 10. artist_collection_count       ~3%  ← 신규

vs 현재 경매 모델:
  1. comp_artist_avg              12.8%
  2. comp_weighted                12.6%
  3. artist_avg_price             10.6%
```

핵심 변화: **비교매출 중심 → 작가 명성 + 갤러리 등급 중심**으로 이동.
경매는 "같은 작가의 비슷한 작품이 얼마에 팔렸나"가 핵심이지만,
갤러리는 "이 작가가 얼마나 유명한가 × 이 갤러리가 얼마나 대단한가"가 핵심.

---

## 8. [CR] 추가 고려사항 (Codex 리뷰)

### 8.1 누락된 피처 (원본 계획에 없었던 것)

| 피처 | 설명 | 중요도 |
|------|------|:------:|
| `label_type` | 가격 유형: list / net / hammer / hammer+premium | 매우 높음 |
| `edition_size` | 에디션 크기 (판화/사진 등), 유일작 여부 | 높음 |
| `year_made` | 제작연도, 작가 커리어 내 시기 | 중간 |
| `provenance_depth` | 소장 이력 깊이 (전시, 이전 판매) | 중간 |
| `representation_graph` | 작가의 갤러리 네트워크 (공동 소속, 계약 관계) | 높음 |
| `fair_section` | 아트페어 내 섹터 (메인 vs 큐레이팅 vs 솔로 부스) | 중간 |
| `missingness_flags` | 각 피처의 결측 여부 자체가 정보 | 중간 |

### 8.2 할인(Discounting)과 검열(Censoring) 문제

**할인**: 1차 시장의 게시가(sticker price)와 실거래가는 10~50% 괴리가 일반적.
- 컬렉터 관계, 기관 할인, 대량 구매 할인 등
- 게시가 기반 모델은 체계적 과대추정 위험
- **완화**: 할인율 분포를 별도 모델로 학습하거나, 게시가 모델임을 명시

**검열**: 미판매 작품 데이터가 누락되면 생존 편향(survivorship bias) 발생.
- 높은 게시가로 미판매 → 데이터에서 탈락 → 모델이 높은 가격만 학습
- **완화**: 미판매 레코드 포함, censored regression (Tobit 모델) 검토

### 8.3 엔티티 해소(Entity Resolution) 리스크

한/영 이름 변환, 작가 별칭, 갤러리 리브랜딩 등 across datasets 문제.
- 예: "이우환" = "Lee Ufan", "박서보" = "Park Seo-Bo"
- 갤러리: "국제갤러리" = "Kukje Gallery" = "Tina Kim Gallery" (뉴욕 파트너)
- **완화**: fuzzy matching + 수동 매핑 테이블 + Artsy ID 활용

---

## 9. 리스크 및 제약 (원본 + CR 보완)

| 리스크 | 심각도 | 완화 방안 |
|--------|:------:|----------|
| 갤러리 거래 데이터 비공개 | 높음 | 아트페어 공개 데이터 + 갤러리 파트너십 |
| 갤러리 등급 주관적 | 중간 | 지점 수, 설립 연도, 아트페어 참여 등 객관 지표로 보완 |
| 국제 데이터 통합 시 환율 변동 | 중간 | 거래일 기준 환율 적용 |
| 1차 시장 가격 투명성 낮음 | 높음 | 할인 거래 등 실거래가 ≠ 게시가 |
| Artsy API 비상업 제한 + 폐지 위험 | 중간 | 연구/교육 목적 활용, 대안 API 병행 (MutualArt, Artfacts) |
| [CR] 라벨 품질 (list vs net vs hammer) | 높음 | 가격 유형 메타데이터 수집, label_type 피처화 |
| [CR] 생존 편향 (미판매 누락) | 중간 | 미판매 레코드 포함, censored regression 검토 |
| [CR] 법적 리스크 (3자 DB 학습) | 중간 | 이용약관 확인, 라이선스 협상 |

---

## 10. 실행 계획 요약 (CR 반영 수정)

```
[Phase 0: 즉시] ─────────────────────────────────────────
  □ [CR] 타깃 정의 확정 (list price vs net price vs hybrid)
  □ [CR] 현재 290건 데이터에 label_type 태깅
  □ Artsy API 연동 → 작가 프로필 확보 (API 안정성 모니터링)
  □ 갤러리 등급 DB 구축 (상위 200개 갤러리)
  □ 1차 시장 예측 신뢰도 등급 분리 (D-primary vs D-auction)
  □ [CR] 한국 타 경매사(서울옥션 등) 데이터 확보 → 빠른 ROI

[Phase 1: 1~2개월] ──────────────────────────────────────
  □ Artnet/Artsy 글로벌 경매 데이터 통합
  □ 작가 명성 피처 6종 추가 (전시, 컬렉션, 비엔날레)
  □ 갤러리/아트페어 tier 피처 추가
  □ sale_channel 피처 → 통합 학습 시작

[Phase 2: 3~6개월] ──────────────────────────────────────
  □ 갤러리 파트너십 → 실거래 데이터 수집
  □ 도메인 적응 모델 (Option B) 구현
  □ 1차 시장 전용 평가 지표 정의
  □ A/B 테스트: 규칙 보정 vs 학습 모델

[Phase 3: 6~12개월] ─────────────────────────────────────
  □ 통합 모델 (Option A) 전환
  □ 이미지 피처 재검토 (갤러리 컨텍스트에서)
  □ 실시간 시장 지수 반영
  □ 1차 시장 MdAPE < 50% 달성
```
