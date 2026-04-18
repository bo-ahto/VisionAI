# 다중 출처 데이터 통합 리팩터링 계획

> **작성일**: 2026-03-30
> **목적**: K-Auction 단일 경매사 → 다중 경매사 + 갤러리 데이터 지원을 위한 파이프라인 리팩터링
> **전제**: 향후 서울옥션, 아이옥션, 에이옥션, 갤러리 등 다양한 출처의 데이터가 지속 추가됨

---

## 1. 현재 상태 진단

### 1.1 K-Auction 의존성 (39개 발견)

| 심각도 | 건수 | 대표 |
|--------|------|------|
| **CRITICAL** | 5 | split 하드코딩, 피처 루프 타입 의존, "메이저"/"유찰" 하드코딩 |
| **HIGH** | 5 | 회차 직접 피처, 경력/최근성 회차 기반, auction_type_factor |
| **MEDIUM** | 8 | 컬럼명 기본값, 추정가 가정, 가격 반올림 규칙 |

### 1.2 현재 57개 피처 분류

| 분류 | 개수 | 설명 |
|------|------|------|
| **범용 (Universal)** | 26개 | 어떤 출처에서도 계산 가능 |
| **K-Auction 전용** | 28개 | 타입·회차·유찰 등 K-Auction 구조에 의존 |
| **외부 데이터** | 3개 | Artsy 글로벌 통계 |

---

## 2. 데이터 출처별 확보 가능 정보

### 2.1 확실하게 수집 가능한 정보 (모든 출처 공통)

| 정보 | 경매사 | 갤러리 | 비고 |
|------|:------:|:------:|------|
| **작가명** | O | O | 한글/영문 |
| **작품 제목** | O | O | |
| **재료** | O | O | 매체+지지체 |
| **크기 (size)** | O | O | 가로×세로, 호수 |
| **가격** | O | O | 낙찰가 / 판매가 |
| **날짜** | O | O | 경매일 / 판매일 |
| **출처명** | O | O | 경매사명 / 갤러리명 |

### 2.2 출처에 따라 있을 수도 없을 수도 있는 정보

| 정보 | 경매사 | 갤러리 | 비고 |
|------|:------:|:------:|------|
| 경매 타입 (위클리/메이저) | △ | X | K-Auction만 명확, 타사 불명확 |
| 추정가 (최저/최고) | △ | X | 일부 경매사만 공개 |
| 입찰수 | △ | X | K-Auction만 |
| 낙찰/유찰 상태 | △ | X | 경매사마다 표기 다름 |
| 회차 (세션 번호) | △ | X | K-Auction 전용 체계 |
| 제작연도 | △ | △ | 있는 경우도 있고 없는 경우도 있음 |
| 작가 영문명 | △ | △ | |
| 작품 이미지 | O | △ | |

### 2.3 외부 수집 가능한 작가 프로필 정보

| 정보 | 출처 | 수집 난이도 | 피처 활용도 |
|------|------|:----------:|:----------:|
| **생년/몰년** | Artsy, 위키, 경매사 DB | 낮음 | 높음 — 작고 작가 프리미엄, 경력 기간 |
| **국적** | Artsy, 위키 | 낮음 | 중간 — 한국/해외 작가 가격 차이 |
| **활동 장르** | Artsy, 갤러리 | 중간 | 중간 — 장르별 시장 트렌드 |
| **학력/수상** | 위키, 작가 DB | 높음 | 중간 — 명성 프록시 |
| **소속 갤러리** | 갤러리 웹사이트 | 중간 | 높음 — 갤러리 등급 = 가격 앵커 |
| **전시 이력** | Artsy, 미술관 | 높음 | 중간 — 활동성 지표 |
| **글로벌 경매 실적** | Artsy, Artnet | 중간 | 높음 — 현재 3개 피처로 활용 중 |

---

## 3. 리팩터링 후 피처 설계

### 3.1 Tier 1: 범용 피처 (모든 출처에서 즉시 사용 가능)

> 작가명, 제목, 재료, 크기, 가격, 날짜만으로 계산 가능한 피처

| # | 피처명 | 원래 상태 | 변경 사항 |
|---|--------|-----------|-----------|
| 1 | `artist_clean` | 범용 | 유지 |
| 2 | `medium_category` | 범용 | 유지 |
| 3 | `support_category` | 범용 | 유지 |
| 4 | `is_3d` | 범용 | 유지 |
| 5 | `is_untitled` | 범용 | 유지 |
| 6 | `height_cm` | 범용 | 유지 |
| 7 | `width_cm` | 범용 | 유지 |
| 8 | `surface_area` | 범용 | 유지 |
| 9 | `aspect_ratio` | 범용 | 유지 |
| 10 | `is_size_imputed` | 범용 | 유지 |
| 11 | `estimated_ho` | 범용 | 유지 |
| 12 | `ln_surface_area` | 범용 | 유지 |
| 13 | `size_bucket` | 범용 | 유지 |
| 14 | `orientation` | 범용 | 유지 |
| 15 | `long_side_cm` | 범용 | 유지 |
| 16 | `short_side_cm` | 범용 | 유지 |
| 17 | `depth_cm` | 범용 | 유지 |
| 18 | `bbox_volume` | 범용 | 유지 |
| 19 | `title_length` | 범용 | 유지 |
| 20 | `title_has_number` | 범용 | 유지 |
| 21 | `title_is_korean` | 범용 | 유지 |
| 22 | `title_is_english` | 범용 | 유지 |
| 23 | `title_has_hanja` | 범용 | 유지 |
| 24 | `title_subject` | 범용 | 유지 |
| 25 | `title_is_series` | 범용 | 유지 |

**합계: 25개** (기존 26개에서 `is_size_imputed` 유지)

### 3.2 Tier 2: 일반화 피처 (K-Auction 전용 → 출처 무관으로 전환)

> 기존 K-Auction 전용 피처를 날짜 기반 + 출처 무관으로 재설계

| # | 기존 피처 | 문제점 | 새 피처 | 변경 내용 |
|---|----------|--------|---------|-----------|
| 26 | `회차` | 경매사별 번호 체계 다름 | `sale_date_ordinal` | 날짜 → 정수 (예: 2024-01-01=0) |
| 27 | `artist_total_sold` | 타입별 분리 | `artist_total_sold` | **타입 필터 제거**, 전체 출처 합산 |
| 28 | `artist_avg_price` | 타입별 분리 | `artist_avg_price` | 전체 출처 합산 |
| 29 | `artist_max_price` | 타입별 분리 | `artist_max_price` | 전체 출처 합산 |
| 30 | `is_new_artist` | 타입별 분리 | `is_new_artist` | 전체 출처 기준 |
| 31 | `artist_median_price` | 타입 필터 | `artist_median_price` | 타입 필터 제거, 날짜 기반 cutoff |
| 32 | `artist_price_trend` | 회차 기반 | `artist_price_trend` | **날짜 기반** 최근 6개월 / 이전 비교 |
| 33 | `medium_avg_price` | 타입 필터 | `medium_avg_price` | 타입 제거, 전체 출처 |
| 34 | `artist_unsold_rate` | "유찰" 하드코딩 | `artist_unsold_rate` | **상태 정규화** (유찰/패스/미낙찰→unsold) 또는 **제거** (갤러리에 미낙찰 개념 없음) |
| 35 | `medium_x_auction_avg` | medium×타입 교차 | `medium_source_avg` | medium × **source_type** (경매/갤러리) 교차 |
| 36 | `auction_type_factor` | K-Auction 3종 타입 | `source_price_level` | 출처별 평균 가격 비율 (경매사A/전체) |
| - | (신규) | - | `source_type` | 경매("auction") / 갤러리("gallery") 구분 — 1차/2차 시장 가격 차이 반영, 범주형 |
| 37 | `artist_recent_avg_price` | 회차 기반 | `artist_recent_avg_price` | **날짜 기반** 최근 6개월 |
| 38 | `artist_price_momentum` | 회차 기반 | `artist_price_momentum` | 날짜 기반 |
| 39 | `artist_sale_frequency` | 상태 컬럼 의존 | `artist_sale_frequency` | 날짜 간격 기반 (년간 판매 건수) |
| 40 | `artist_auctions_since_last` | 회차 차이 | `days_since_last_sale` | **날짜 차이** (일수) |
| 41 | `artist_price_volatility` | 타입 필터 | `artist_price_volatility` | 타입 제거 |
| 42 | `artist_lot_count_trend` | 회차 기반 | `artist_lot_count_trend` | 날짜 기반 |
| 43 | `artist_premium_ratio` | "메이저" 하드코딩 | **제거** | 대체: `source_type` (경매/갤러리) |
| 44 | `artist_reappear_flag` | 타입 필터 | `artist_reappear_flag` | 날짜 기반 재등장 (미낙찰 포함) — `is_new_artist`는 낙찰만 집계, 이건 출품 이력 포함으로 의미 다름 |
| 45 | `artist_last_hammer_price` | 타입 필터 | `artist_last_sale_price` | 전체 출처, 날짜 기반 |
| 46 | `artist_career_length` | 회차 차이 | `artist_career_days` | **날짜 차이** (일수) |
| 47 | `market_price_index` | 회차 기반 | `market_price_index` | **날짜 기반** 최근 3개월 평균 |
| 48 | `comp_artist_avg` | 타입 필터 | `comp_artist_avg` | 타입 제거 |
| 49 | `comp_medium_avg` | 타입 필터 | `comp_medium_avg` | 타입 제거 |
| 50 | `comp_weighted` | 타입 필터 | `comp_weighted` | 타입 제거 |
| 51 | `comp_match_level` | 타입 필터 | `comp_match_level` | 타입 제거 |
| 52 | `comp_match_count` | 타입 필터 | `comp_match_count` | 타입 제거 |
| 53 | `size_ho` | 호수 계산 (구 방식) | **제거** | `estimated_ho`로 대체 (이미 Tier 1에 포함) |
| 54 | `size_ho_above40` | hinge 피처 | **제거** | `estimated_ho`로 대체 |

**변환: 28개 → 25개** (3개 제거: `artist_premium_ratio`, `size_ho`, `size_ho_above40`)

### 3.3 Tier 3: 외부 데이터 피처 (현행 유지 + 확장)

| # | 피처명 | 출처 | 상태 |
|---|--------|------|------|
| 55 | `global_avg_price` | Artsy | 유지 |
| 56 | `global_median_price` | Artsy | 유지 |
| 57 | `global_auction_count` | Artsy | 유지 |

### 3.4 Tier 4: 신규 작가 프로필 피처 (추가 수집 시)

> 작가별 한 번만 수집하면 모든 작품에 적용 가능한 피처

| # | 피처명 | 출처 | 설명 | 기대 효과 |
|---|--------|------|------|-----------|
| 58 | `artist_birth_year` | Artsy/위키 | 생년 | 세대별 가격 트렌드 |
| 59 | `artist_is_deceased` | Artsy/위키 | 작고 여부 | 작고 작가 프리미엄 (일반적으로 +20~50%) |
| 60 | `artist_death_year` | Artsy/위키 | 몰년 | 사후 경과 기간 |
| 61 | `artist_nationality` | Artsy/위키 | 국적 코드 (KR/US/FR 등) | 국내/해외 작가 가격 차이 |
| 62 | `artist_career_start_year` | 전시 이력 | 첫 전시/판매 연도 | 경력 기간 (날짜 무관 버전) |
| 63 | `artist_gallery_tier` | 갤러리 DB | 소속 갤러리 등급 (1~5) | 갤러리 = 가격 보증인 |
| 64 | `artist_exhibition_count` | Artsy/미술관 | 전시 횟수 | 활동성 지표 |
| 65 | `artist_museum_collection` | Artsy | 미술관 소장 여부 | 명성 프록시 |
| ~~66~~ | ~~`source_type`~~ | — | Tier 2로 이동 | `auction_type_factor` 대체 |

---

## 4. 리팩터링 후 최종 피처 목록

| Tier | 개수 | 특성 |
|------|------|------|
| **Tier 1** (범용) | 25개 | 즉시 사용 가능, 수정 불필요 |
| **Tier 2** (일반화) | 27개 | 타입/회차 의존 제거, 날짜 기반 전환 (+`source_type` 추가, `reappear_flag` 유지) |
| **Tier 3** (외부) | 3개 | Artsy 데이터, 현행 유지 |
| **Tier 4** (프로필) | 8개 | 신규, 추가 수집 시 |
| **합계** | **63개** | (기존 57 - 제거 3 + 신규 9: source_type 1 + 프로필 8) |

---

## 5. 데이터 클렌징 정책

### 5.1 통합 입력 스키마

모든 출처의 데이터를 아래 통합 스키마로 변환 후 사용:

```
필수 컬럼 (없으면 제거):
  - artist     : 작가명 (한글 또는 영문)
  - title      : 작품 제목
  - material   : 재료 문자열
  - size_raw   : 크기 문자열
  - price      : 판매/낙찰가 (원화)
  - sale_date  : 판매/낙찰 날짜 (YYYY-MM-DD)
  - source     : 출처명 (케이옥션, 서울옥션, 갤러리X 등)

선택 컬럼 (없으면 NaN):
  - source_type : "auction" / "gallery"
  - year_created: 제작연도
  - status      : "sold" / "unsold"
  - estimate_low, estimate_high : 추정가
```

### 5.2 클렌징 단계

```
1. 스키마 변환
   └── 각 출처 CSV → 통합 스키마 매핑

2. 필수 필드 검증
   ├── artist 없음 → name_eng 대체 → title 있으면 __UNKNOWN__ → 셋 다 없으면 제거
   ├── price <= 0 또는 NaN → 제거
   └── sale_date 없음 → 제거

3. 비미술 클렌징 (기존 data_cleanser.py)
   ├── 이벤트/상품권 → 제거
   ├── 주류/테이스팅 → 제거
   ├── 명품 (Birkin/Rolex) → 제거
   ├── 보석/장신구 → 제거
   ├── 도자기/공예 → 제거
   └── 목공예 (순수 목재) → 제거

4. 중복 제거
   ├── 동일 출처 내: (artist + title + material + price + date) 키
   └── 교차 출처: (artist + title + material + price) 키 + 날짜 ±7일

5. 이상치 필터
   ├── price < 10,000원 → 제거 (데이터 오류 의심)
   └── price > 100억원 → 검증 후 유지/제거
```

### 5.3 상태값 정규화

| 원본 값 | 정규화 |
|---------|--------|
| 낙찰, sold | `sold` |
| 유찰, 패스, 미낙찰, 부매, Passed, Bought-in | `unsold` |
| 빈값, NaN (가격 > 0) | `sold` (가격 있으면 판매로 간주) |

---

## 6. 리팩터링 실행 계획

### Phase A: 데이터 레이어 (1주)

| 단계 | 작업 | 파일 |
|------|------|------|
| A1 | 통합 입력 스키마 정의 + 변환 함수 | `preprocessing/data_schema.py` (신규) |
| A2 | **컬럼명 매핑 레이어** — 통합 스키마(`artist`, `price`, `sale_date`) → 파이프라인 내부 컬럼(`작가`, `낙찰가`, `회차`) 자동 변환. `_apply_parsers()`, `build_hedonic_features()`, `artist_stats_snapshot`, `data_cleanser` 모두 통합 스키마 기준으로 동작하도록 수정 | `hedonic_features.py`, `artist_stats_snapshot.py` |
| A3 | 출처별 변환기 (K-Auction, K-Artmarket, 갤러리) | `scripts/merge_artmarket_data.py` (수정) |
| A4 | 상태값 정규화 (유찰/패스/미낙찰/응찰없음→unsold, 철회→withdrawn) | `preprocessing/data_cleanser.py` (수정) |
| A5 | 통합 클렌징 파이프라인 | `preprocessing/data_cleanser.py` (확장) |
| A6 | 중복 제거 로직 (교차 출처: 동일 결과 건만, unsold 재출품은 유지) | `preprocessing/data_schema.py` |

### Phase B: 피처 레이어 (1주)

| 단계 | 작업 | 파일 |
|------|------|------|
| B1 | `_filter_by_cutoff_and_type()` → `_filter_by_date()` 전환 | `features/hedonic_stats.py` |
| B2 | 모든 `compute_*` 함수에서 `auction_type` 파라미터 제거 | `features/hedonic_stats.py` |
| B3 | `artist_premium_ratio`, `size_ho`, `size_ho_above40` 제거 (`artist_reappear_flag`는 유지) | `features/hedonic_stats.py` |
| B4 | `_join_artist_stats_and_hedonic()` 타입 루프 → 날짜 루프 전환 | `hedonic_features.py` |
| B5 | `HEDONIC_FEATURES` 목록 업데이트 (57 → 52 + 신규) | `hedonic_features.py` |
| B6 | `회차` → `sale_date_ordinal` 전환 | `hedonic_features.py` |

### Phase C: 분할·학습 레이어 (3일)

| 단계 | 작업 | 파일 |
|------|------|------|
| C1 | `assign_split_4way()` → 날짜 기반 비율 분할 | `features/splits.py` |
| C2 | `CAT_FEATURE_NAMES`에서 `타입` 제거 | `hedonic_features.py` |
| C3 | `cold_start.py` 타입 → `source_type` 전환. Tier 1: `medium × source_type`, Tier 3: `source_type` alone. 경매 vs 갤러리 가격 차이를 cold-start에서도 반영 | `cold_start.py` |
| C4 | 학습 스크립트 경로·파라미터 업데이트 | `scripts/train_phase5_final.py` |

### Phase D: 프로필 피처 (추가 수집 후)

| 단계 | 작업 | 파일 |
|------|------|------|
| D1 | 작가 프로필 통합 테이블 생성 | `data/artist_profiles.csv` |
| D2 | 프로필 피처 빌더 | `features/artist_profile.py` (신규) |
| D3 | `HEDONIC_FEATURES`에 프로필 피처 추가 | `hedonic_features.py` |

### Phase E: 검증 + 롤백 전략 (3일)

| 단계 | 작업 |
|------|------|
| E1 | 기존 테스트 수정 + 신규 테스트 작성 |
| E2 | 통합 데이터로 재학습 |
| E3 | 성능 비교 (기존 vs 리팩터링) |
| E4 | Codex 리뷰 |
| E5 | **Go/No-Go 판정** |

**롤백 전략**: 리팩터링 기간 중 기존 단일 출처 파이프라인을 유지한다.
- 기존 `hedonic_features.py`를 `hedonic_features_v1.py`로 백업
- 기존 모델 아티팩트(`model_a_quantile.cbm`) 보존
- Go/No-Go 기준: K-Auction 단독 test set에서 MdAPE 악화 ≤ 2%p
  - PASS → 리팩터링 본 적용
  - FAIL → 원인 분석 후 특정 피처/로직만 선별 적용

---

## 7. 작가 프로필 수집 우선순위

| 순위 | 정보 | 기대 효과 | 수집 난이도 | 권장 출처 |
|------|------|-----------|:----------:|-----------|
| 1 | **생년/몰년 + 작고 여부** | 가장 높음 — 작고 프리미엄은 보편적 | 낮음 | Artsy API (기존 연동), 위키피디아 |
| 2 | **국적** | 높음 — 한국/해외 가격 구조 다름 | 낮음 | Artsy API |
| 3 | **소속 갤러리** | 높음 — 갤러리 등급 = 가격 보증 | 중간 | 갤러리 웹사이트, Artsy |
| 4 | **글로벌 경매 실적** | 높음 — 이미 3개 피처 활용 중 | 중간 | Artsy (기존), Artnet |
| 5 | **전시 횟수** | 중간 — 활동성 프록시 | 높음 | Artsy, 미술관 DB |
| 6 | **학력/수상** | 낮음 — 노이즈 가능성 | 높음 | 위키, 작가 DB |

---

## 8. 리팩터링 전후 비교

```
[현재]
K-Auction CSV (43,866건)
  ↓ 타입별 루프 (위클리/프리미엄/메이저)
  ↓ 회차 기반 cutoff
  ↓ "유찰"/"메이저" 하드코딩
  ↓ 57개 피처 (28개 K-Auction 전용)
  ↓ CatBoost

[리팩터링 후]
통합 CSV (경매사 N개 + 갤러리 M개)
  ↓ 통합 스키마 변환
  ↓ 클렌징 (비미술 제거 + 중복 제거)
  ↓ 날짜 기반 cutoff (출처 무관)
  ↓ 52~61개 피처 (전부 범용)
  ↓ CatBoost
```

### 기대 효과

| 항목 | 현재 | 리팩터링 후 |
|------|------|------------|
| 학습 데이터 | 42,588건 (K-Auction만) | ~109,000건+ (다중 출처) |
| 작가 커버리지 | 3,289명 | 5,294명+ |
| Cold-start 비율 | ~25% | ~15% (예상) |
| 출처 확장성 | 불가 | 무제한 |
| 갤러리 데이터 | 미지원 | 지원 |
