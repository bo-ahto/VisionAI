# 가격 예측 정확도 개선 기획서

> **작성일**: 2026-03-31
> **현재 성능**: MdAPE 52.73%, R² 0.34, Cold-start MdAPE 67.55%
> **목표**: MdAPE < 35%
> **방법**: 1차 리서치 에이전트 + 2차 Codex CLI 독립 분석 → 종합

---

## 1. 현재 성능 병목 진단

### 1.1 데이터 품질 문제 (가장 심각)

| 문제 | 영향 범위 | 심각도 |
|------|-----------|--------|
| **크기(height/width) 50% 결측** | 서울옥션 86%, 아이옥션 92%, 에이옥션·라이즈아트 100% | **CRITICAL** |
| **artist_unsold_rate 100% NaN** | 전 데이터 | **HIGH** |
| **Artsy 글로벌 데이터 13% 커버리지** | 87% 작가 미커버 | **MEDIUM** |

### 1.2 모델 구조 한계

- 단일 CatBoost → 가격 범위 100배 이상 (20만원 ~ 72억원)을 하나의 모델이 처리
- 피처 중요도 상위 4개가 전부 **작가 가격 이력** (34.5%) → 이력 없으면 예측 불가
- Cold-start 10% → MdAPE 67.55% (전체 평균 대비 +15%p)

---

## 2. 개선 전략 (우선순위별)

### P0: 즉시 실행 — 데이터 품질 수정 (예상 MdAPE -3~5%p)

#### 2.1 크기 결측 개선 (현재 50% → 목표 <20%)

**2.1a. 작가×매체 조건부 대체 (최우선)**

대부분의 작가는 특정 매체에서 일정한 크기 범위 내에서 작업.

```
대체 순서:
1. [artist_clean, medium_category] (min 5건) → 작가의 해당 매체 중앙 크기
2. [artist_clean]                  (min 5건) → 작가 전체 중앙 크기
3. [is_3d, medium_category]        (기존)
4. [medium_category]               (기존)
5. 전체 중앙값                      (기존)
```

- **근거**: Renneboog & Spaenjers (2013) — 크기는 가격의 log-linear 결정 요인
- **효과**: 기존 50% 결측 중 ~30%를 작가 기반으로 정확 대체 가능
- **난이도**: 낮음 (기존 imputation 체인 확장)

**2.1b. "크기 미상" 자체를 피처로 활용**

결측이 정보인 경우: 판화·복제품·딜러 출품작은 크기 미기재가 일반적.

```python
df["has_dimensions"] = df["height_cm"].notna()
# + medium_category와 교차: "유화인데 크기 없음"은 비정상, "판화인데 크기 없음"은 정상
```

- **난이도**: 매우 낮음

**2.1c. k-artmarket의 width/height 컬럼 활용**

현재 `data_schema.py`에서 `size_raw`만 가져오고, 원본의 `width`/`height` 수치 컬럼을 버리고 있음.

```python
# convert_kartmarket()에서 width/height가 있으면 직접 사용
if pd.notna(row["width"]) and pd.notna(row["height"]):
    size_raw = f'{row["width"]}x{row["height"]}cm'
```

- **난이도**: 매우 낮음 — 가장 큰 효과를 가장 적은 노력으로

#### 2.2 artist_unsold_rate 복구

현재 100% NaN인 이유: k-artmarket이 전부 `"sold"` 상태.

**해결**: 가격이 0이거나 NaN인 레코드를 "unsold"로 간주 (원본 데이터에서 유찰 건 복구).

- **근거**: Hwang, Ryu & Hong (2025, J. Cultural Economics) — 한국 경매에서 유찰 경험은 이후 수익률 **14.4% 하락** 시그널
- **효과**: MdAPE -1~2%p
- **난이도**: 중간 (원본 데이터에서 유찰 건 식별 필요)

#### 2.3 경력 궤적 피처 추가 (기존 데이터로 즉시 계산 가능)

| 피처 | 설명 | 근거 |
|------|------|------|
| `lot_density_12m` | 최근 12개월 출품 수 (희소성 신호) | 공급량과 가격의 반비례 |
| `price_acceleration` | 가격 추세의 2차 도함수 | 상승/하락 가속 감지 |
| `market_share_in_medium` | 해당 매체 내 작가 점유율 | 지배적 작가 프리미엄 |
| `auction_house_diversity` | 거래 경매사 수 (=`source_count`, 이미 있음) | 시장 폭 |

- **난이도**: 낮음 (기존 데이터에서 계산)

---

### P1: 모델 구조 개선 (예상 MdAPE -5~8%p)

#### 2.4 Two-Step 계층 모델

현재 단일 CatBoost가 20만원~72억원 전체를 처리 → **가격대별 전문 모델** 분리.

```
Step 1: 가격 구간 분류 (CatBoost Classifier)
  → ~100만 / 100~500만 / 500~2000만 / 2000만~1억 / 1억+

Step 2: 구간별 전문 회귀 (CatBoost Regressor × 5)
  → 각 구간에 최적화된 피처 중요도 학습
```

- **근거**: Kim & Kim (2024, KES) — 한국 경매 데이터에서 Two-step XGBoost가 단일 모델 대비 우위
- **효과**: MdAPE -3~5%p (가격대별 특화로 고가·저가 모두 개선)
- **난이도**: 중간 (기존 `two_step_model.py` 확장)

#### 2.5 앙상블 스태킹

```
Layer 1: CatBoost + LightGBM + XGBoost (다양성 확보)
Layer 2: Ridge 메타 학습기 (OOF predictions 스태킹)
```

- **근거**: Fedderke & Carugno (2025, Expert Systems) — RF·GBM이 OLS·CNN 대비 미술품 가격 예측에서 우위
- **효과**: MdAPE -2~3%p
- **난이도**: 낮음~중간 (기존 `ensemble_model.py` 있음)

#### 2.6 Cold-start 계층 강화

현재 cold-start (10%, MdAPE 67.55%)를 전용 전략으로 개선:

```
Tier 0: ≥3건 이력 → 전체 모델 사용
Tier 1: 1-2건 이력 → (매체×크기×연대) 그룹 shrinkage
Tier 2: 0건 + 유사 작가 발견 → K-NN 이웃 가중 평균
Tier 3: 0건 + 매체×경매사 → Bayesian shrinkage
Tier 4: 0건 → 매체 전체 중앙값
```

- **효과**: Cold MdAPE -5~8%p → 전체 MdAPE -0.5~1%p
- **난이도**: 중간

---

### P2: 작가 데이터 확장 (예상 MdAPE -3~5%p)

#### 2.7 한국 작가 프로필 수집

| 출처 | 데이터 | 접근 | 난이도 |
|------|--------|------|--------|
| **한국예술인복지재단 (KAWF)** | 생년, 분야, 지역, 인증 현황 | [data.go.kr 공공데이터](https://www.data.go.kr/data/15037528/fileData.do) | **낮음** (무료) |
| **KIAF 출품 기록** | 갤러리 참여, 작가 대리 | kiaf.org 스크래핑 | 중간 |
| **K-artnow 아카이브** | 전시 이력, 리뷰 | k-artnow.com | 중간 |
| **국립현대미술관 (MMCA)** | 소장품 목록 | 공공 DB | 중간 |
| **Artnet / Artprice** | 글로벌 경매 실적 | 유료 구독 | 높음 (비용) |

**수집 우선순위**:
1. KAWF 공공데이터 (생년/몰년 → `is_deceased` 피처, 무료)
2. KIAF 출품 기록 (갤러리 등급 추정)
3. Artsy 확장 (현재 13% → 30%+ 목표)

**작가 프로필 피처**:

| 피처 | 효과 | 근거 |
|------|------|------|
| `artist_birth_year` | 세대별 가격 트렌드 | 경력 단계 프록시 |
| `is_deceased` | **작고 프리미엄 +30~60%** | Ursprung & Wiermann (2011) |
| `artist_nationality` | 한국/해외 가격 구조 차이 | Renneboog (2013) |
| `gallery_tier` (1-5) | 갤러리 = 가격 보증인 | **Fraiberger et al. (2018, Science)** — 초기 기관 접근이 가격 궤적의 최강 예측자 |
| `exhibition_count` | 명성 축적 프록시 | 활동성 지표 |
| `museum_collection` (bool) | 제도적 인정 | 가격 앵커 |

#### 2.8 Entity Resolution (작가명 통합)

한국 작가 이름 체계: 한글(이우환) / 영문(Lee Ufan) / 한자(李禹煥) / 로마자 변형(Lee U-Fan)

현재 `artist_clean`이 단순 문자열 → 같은 작가가 여러 이름으로 분리될 수 있음.

**해결**:
1. K-Artmarket의 `name_kor` + `name_eng` 쌍으로 매핑 테이블 구축
2. 자모(Jamo) 분해 + 편집 거리로 한글 유사 매칭
3. 영문→한글 음역 규칙 기반 매칭

- **효과**: 분리된 작가 통합 → 작가 이력 피처 정확도 향상
- **난이도**: 중간

---

### P3: 고급 피처 (예상 MdAPE -2~4%p)

#### 2.9 반복 판매 (Repeat Sale) 피처

같은 작가+제목 조합이 재출품되는 경우 → 가장 강력한 비교 가능 판매.

| 피처 | 설명 |
|------|------|
| `is_repeat_sale` | 동일 작품 재출품 여부 (bool) |
| `prev_sale_price_ln` | 이전 낙찰가 (log) |
| `repeat_appreciation_rate` | (현재가/이전가) - 1 |

- **근거**: Mei & Moses (2002) — 반복 판매 지수가 미술 시장 수익률 추정의 표준
- **근거**: Aubry et al. (2023) — 반복 판매가 가장 강력한 비교 가능 판매
- **효과**: 해당 건에 한해 MdAPE 대폭 감소
- **난이도**: 중간 (제목 fuzzy matching 필요)

#### 2.10 미술 사조 분류 (Title NLP 확장)

한국 미술 사조 → 가격 구조에 큰 영향:

| 사조 | 특징 | 가격 수준 |
|------|------|-----------|
| 단색화 (Dansaekhwa) | 1970s, 모노크롬 | 고가 (국제적 인지도) |
| 민중미술 | 1980s, 사회참여 | 중가 |
| 극사실주의 | 현대, 세밀묘사 | 중~고가 |
| 추상 | 다양 | 작가별 편차 큼 |

**구현**: 제목 + 재료 키워드 기반 규칙 분류 또는 작가별 사전 매핑.

- **난이도**: 중간

---

### P4: 장기 — 이미지 피처 + 심층 학습 (예상 MdAPE -4~6%p)

#### 2.11 시각 임베딩 (CNN/ResNet)

Mei, Moses, Wälty & Yang (2025) — *Deep Learning for Art Market Valuation*:

> 시각 임베딩은 **시장 최초 출품 작품**(Cold-start)에서 R²를 유의미하게 향상. 특히 거래 이력 없는 작품에 효과적.

```
Tabular branch: CatBoost → Dense(128)
Image branch:   ResNet50 → Dense(128)
Fusion:         Concat → Dense(64) → Price
```

- **효과**: Cold-start MdAPE -10~15%p, 전체 MdAPE -4~6%p
- **난이도**: 높음 (이미지 수집, GPU 인프라)

#### 2.12 작가 임베딩 (Collaborative Filtering)

같은 경매 세션에 등장하는 작가들 → 유사 작가 네트워크 구축 (Item2Vec 방식).

- **근거**: Fraiberger et al. (2018, Science) — 네트워크 위치가 성공의 최강 예측자
- **효과**: Cold-start MdAPE -5~8%p
- **난이도**: 중간

---

## 3. 예상 성과 로드맵

```
현재:         MdAPE 52.73%
              │
P0 (즉시):    -3~5%p → MdAPE ~48%
  크기 결측 개선, unsold_rate 복구, 경력 피처
              │
P1 (1-2주):   -5~8%p → MdAPE ~42%
  Two-Step 모델, 앙상블, cold-start 강화
              │
P2 (2-4주):   -3~5%p → MdAPE ~38%
  작가 프로필 수집, entity resolution
              │
P3 (1-2개월): -2~4%p → MdAPE ~35%
  반복 판매, 미술 사조, 고급 피처
              │
P4 (3개월+):  -4~6%p → MdAPE ~30%
  이미지 피처, 작가 임베딩, 멀티모달
```

> **주의**: 개선 효과는 누적이 아닌 중첩됨. 현실적 시나리오:
> - **낙관적**: P0~P3 전부 성공 → MdAPE ~35%
> - **현실적**: P0~P2 성공 + P3 부분 → MdAPE ~38~40%
> - **보수적**: P0~P1만 → MdAPE ~43~45%

---

## 4. 학술 근거 요약

| # | 논문 | 년도 | 핵심 발견 | 적용 |
|---|------|------|-----------|------|
| 1 | Renneboog & Spaenjers, "Buying Beauty" | 2013 | 작가 명성·크기·매체가 가격의 주 결정 요인 | Hedonic 피처 설계 기반 |
| 2 | **Kim & Kim**, "Two-step XGBoost for Korean art auctions", KES | 2024 | 한국 경매에서 2단계 모델이 단일 모델 대비 우위 | P1 Two-Step 모델 |
| 3 | **Fraiberger et al.**, "Quantifying reputation and success in art", Science | 2018 | 갤러리·미술관 네트워크 위치가 가격 궤적 최강 예측자 | P2 갤러리 등급 피처 |
| 4 | Aubry et al., "Machines and Masterpieces" | 2023 | ML이 Hedonic 대폭 우위; 유찰 예측이 가치 있음; 반복 판매 최강 비교 | P1 앙상블, P3 반복 판매 |
| 5 | **Hwang, Ryu & Hong**, "The paradox of being unsold", J. Cultural Economics | 2025 | 한국 경매 유찰 경험 → 수익률 14.4% 하락 | P0 unsold_rate 복구 |
| 6 | Mei & Moses, "Art as an Investment" | 2002 | 반복 판매 지수 = 미술 수익률 표준 | P3 반복 판매 피처 |
| 7 | Lee, Park, Goree, Crandall & Ahn, "Social signals predict contemporary art prices", Scientific Reports | 2024 | 사회적 신호가 시각적 피처보다 가격 예측에 효과적 | P2 전시·갤러리 피처 |
| 8 | Fedderke & Carugno, "ML Algorithms and Fine Art Pricing", Expert Systems | 2025 | RF·GBM이 OLS·CNN 대비 미술품 가격 예측에서 우위 | P1 앙상블 |
| 9 | Mei, Moses, Wälty & Yang, "Deep Learning for Art Market Valuation" | 2025 | 멀티모달(표+이미지)이 Cold-start에서 R² 개선 (approximate) | P4 이미지 피처 |
| 10 | "Artwork pricing: popularity & ability", AStA | 2024 | 인기(시장)와 능력(제도) 분리가 예측 개선 | P2 작가 프로필 |
| 11 | KOREASCIENCE, "Price Determinant Factors", 한국 경매 | 2019 | K-NN이 한국 미술 가격에서 선형회귀 우위 | P1 Cold-start K-NN |
| 12 | Romano et al., "Conformalized Quantile Regression", NeurIPS | 2019 | CQR로 유한 표본 커버리지 보장 | 기존 CQR 유지 |

---

## 5. 1차·2차 리서치 교차 검증

| 제안 | 1차 에이전트 | 2차 Codex CLI | 합의 |
|------|:-----------:|:------------:|------|
| 크기 작가×매체 대체 | O | O | **양측 최우선** |
| k-artmarket width/height 활용 | - | O | Codex 고유 — 가장 쉬운 해결 |
| unsold_rate 복구 | O | O | 동의 |
| Two-Step 계층 모델 | O | O | 동의 |
| 앙상블 스태킹 | O | O | 동의 |
| 작가 프로필 (KAWF) | O | O | 동의 — 공공데이터 우선 |
| 갤러리 등급 (Fraiberger) | O | O | 양측 최고 영향 예측 |
| 반복 판매 피처 | O | O | 동의 |
| 이미지 임베딩 | O | O | 장기 과제 |
| 작가 임베딩 (CF) | O | - | 에이전트 고유 |
| 미술 사조 분류 | O | - | 에이전트 고유 |
| has_dimensions 피처 | - | O | Codex 고유 |
| imputation 신뢰도 점수 | O | - | 에이전트 고유 |
