# 다중 출처 피처 재설계 기획서

> **작성일**: 2026-03-30
> **방법**: 1차 리서치 에이전트 + 2차 Codex CLI 독립 분석 → 종합
> **목표**: K-Auction 단독 57개 피처 → 다중 출처 지원 52개 피처로 재설계
> **학술 근거**: Renneboog & Spaenjers (2013), Mei & Moses (2002), Ashenfelter & Graddy (NBER)

---

## 1. 현재 상태 요약

| 항목 | 수치 |
|------|------|
| 데이터 | 124,442건 (10+ 경매사) |
| 현재 피처 | 57개 (25 범용 + 28 K-Auction 전용 + 3 외부 + 1 신규) |
| **문제 피처** | **9개** — 상수/폐기/하드코딩/희소/상태 의존 |

---

## 2. 피처 변경 계획

### 2.1 제거 (9개)

| 피처 | 인덱스 | 제거 사유 |
|------|:------:|-----------|
| `source_type` | 14 | 현재 전부 "auction" → 상수. 갤러리 데이터 추가 전까지 정보 없음 |
| `size_ho` | 18 | 폐기 — `estimated_ho`가 대체 (F-타입 보간). 공선성 |
| `size_ho_above40` | 19 | 폐기 — `ln_surface_area` + CatBoost 비선형으로 대체 |
| `auction_type_factor` | 20 | K-Auction 3종 타입 비율 → 10+ 출처 비율로 의미 변질. `source_count`/`artist_cross_source_premium`으로 대체 |
| `medium_x_auction_avg` | 22 | medium × source 교차 → 10+ 출처에서 너무 희소. `medium_avg_price`가 매체 신호 커버 |
| `artist_premium_ratio` | 29 | "메이저" 하드코딩 → 비K-Auction은 항상 0. `artist_cross_source_premium`으로 대체 |
| `artist_reappear_flag` | 30 | `is_new_artist`와 사실상 동일 (공선성) |
| `global_avg_price` | 39 | `global_median_price`와 공선성. 중앙값만 유지 |
| `comp_match_level` | 37 | 구현 상세 (1-4 서수). `comp_match_count`(연속형)가 더 유의미 |

### 2.2 재설계 (4개)

| 피처 | 문제 | 수정 |
|------|------|------|
| `artist_unsold_rate` | k-artmarket에 상태 없음 → 0 | 상태 데이터 있는 출처만 계산, 없으면 NaN |
| `artist_sale_frequency` | status_col 의존 | price > 0 기반으로 전환 (판매 건수/기간) |
| `artist_lot_count_trend` | status_col 의존 | price > 0 기반으로 전환 |
| `artist_career_length` | status_col 의존 | price > 0 첫 판매 ~ cutoff 날짜 차이 |

### 2.3 신규 추가 (4개)

| 피처 | 타입 | 설명 | 기대 효과 | 구현 우선순위 |
|------|------|------|-----------|:------------:|
| **`source_count`** | int | 작가가 판매한 경매사 수 (cutoff 이전) | 높음 — 시장 폭/유동성 프록시. 다중 출처 핵심 장점 | 즉시 |
| **`artist_cross_source_premium`** | float | 현재 출처 평균가 / 전체 출처 평균가 - 1 | 중간 — `auction_type_factor` + `artist_premium_ratio` 대체. 데이터 기반, 하드코딩 없음 | 단기 |
| **`source_price_dispersion`** | float | 작가의 출처별 평균 ln(price) 표준편차 | 중간 — 가격 일관성/불안정성 지표. 다중 출처 고유 | 단기 |
| **`sale_month`** | int | 판매월 (1-12) | 중간 — 계절성. 5월/11월 프리미엄 (Renneboog 2013) | 즉시 |

---

## 3. 최종 피처 목록 (52개)

### 범주형 (8개)

| # | 피처 | 상태 |
|---|------|------|
| 1 | `artist_clean` | 유지 |
| 2 | `medium_category` | 유지 |
| 3 | `support_category` | 유지 |
| 4 | `is_3d` | 유지 |
| 5 | `is_untitled` | 유지 |
| 6 | `title_subject` | 유지 |
| 7 | `size_bucket` | 유지 |
| 8 | `orientation` | 유지 |

### 작가 통계 (17개)

| # | 피처 | 상태 |
|---|------|------|
| 9 | `artist_avg_price` | 유지 |
| 10 | `artist_max_price` | 유지 |
| 11 | `artist_total_sold` | 유지 |
| 12 | `is_new_artist` | 유지 |
| 13 | `artist_median_price` | 유지 |
| 14 | `artist_price_trend` | 유지 |
| 15 | `artist_recent_avg_price` | 유지 |
| 16 | `artist_price_momentum` | 유지 |
| 17 | `artist_unsold_rate` | **재설계** — NaN-safe |
| 18 | `artist_sale_frequency` | **재설계** — price 기반 |
| 19 | `artist_auctions_since_last` | 유지 (날짜 호환 완료) |
| 20 | `artist_price_volatility` | 유지 |
| 21 | `artist_lot_count_trend` | **재설계** — price 기반 |
| 22 | `artist_last_hammer_price` | 유지 |
| 23 | `artist_career_length` | **재설계** — price 기반 |
| 24 | **`source_count`** | **신규** |
| 25 | **`artist_cross_source_premium`** | **신규** |

### 물리적 속성 (11개)

| # | 피처 | 상태 |
|---|------|------|
| 26 | `height_cm` | 유지 |
| 27 | `width_cm` | 유지 |
| 28 | `surface_area` | 유지 |
| 29 | `aspect_ratio` | 유지 |
| 30 | `is_size_imputed` | 유지 |
| 31 | `estimated_ho` | 유지 |
| 32 | `ln_surface_area` | 유지 |
| 33 | `long_side_cm` | 유지 |
| 34 | `short_side_cm` | 유지 |
| 35 | `depth_cm` | 유지 |
| 36 | `bbox_volume` | 유지 |

### 시장/비교 (7개)

| # | 피처 | 상태 |
|---|------|------|
| 37 | `medium_avg_price` | 유지 |
| 38 | `market_price_index` | 유지 (날짜 기반 전환 완료) |
| 39 | `comp_artist_avg` | 유지 |
| 40 | `comp_medium_avg` | 유지 |
| 41 | `comp_weighted` | 유지 |
| 42 | `comp_match_count` | 유지 |
| 43 | **`source_price_dispersion`** | **신규** |

### 시간 (1개)

| # | 피처 | 상태 |
|---|------|------|
| 44 | **`sale_month`** | **신규** |

### 제목 NLP (6개)

| # | 피처 | 상태 |
|---|------|------|
| 45-50 | `title_length`, `title_has_number`, `title_is_korean`, `title_is_english`, `title_has_hanja`, `title_is_series` | 유지 |

### 외부 데이터 (2개)

| # | 피처 | 상태 |
|---|------|------|
| 51 | `global_median_price` | 유지 |
| 52 | `global_auction_count` | 유지 |

> **합계: 52개** (기존 57 - 제거 9 + 신규 4)

---

## 4. 구현 스프린트

### Sprint 0: 즉시 (피처 정리)

| 작업 | 파일 | 시간 |
|------|------|------|
| HEDONIC_FEATURES에서 9개 제거 | `hedonic_features.py` | 30분 |
| CAT_FEATURE_NAMES에서 `source_type` 제거 | `hedonic_features.py` | 10분 |
| `source_count` 구현 | `hedonic_stats.py` | 1시간 |
| `sale_month` 구현 | `hedonic_features.py` | 30분 |
| 4개 재설계 피처 수정 (status→price fallback) | `hedonic_stats.py` | 2시간 |
| 테스트 업데이트 | `tests/` | 1시간 |
| 재학습 + 성능 비교 | `scripts/` | 30분+학습시간 |

### Sprint 1: 단기 (다중 출처 피처)

| 작업 | 파일 | 시간 |
|------|------|------|
| `artist_cross_source_premium` 구현 | `hedonic_stats.py` | 2시간 |
| `source_price_dispersion` 구현 | `hedonic_stats.py` | 1시간 |
| A/B 성능 비교 | `scripts/` | 학습시간 |

### Sprint 2: 추후 (갤러리 데이터 추가 시)

| 작업 | 조건 |
|------|------|
| `source_type` 재도입 | 갤러리 데이터 추가 시 |
| `repeat_sale_index` | 작가당 5건+ 반복 판매 쌍 확보 시 |
| 작가 프로필 피처 (생년/국적) | 프로필 수집 완료 시 |

---

## 5. 학술 근거

| 피처 설계 원칙 | 참조 | 적용 |
|---------------|------|------|
| Hedonic 회귀 (크기, 매체, 작가) | Renneboog & Spaenjers 2013 | 25개 범용 피처 |
| 경매사 프리미엄 효과 | Ashenfelter & Graddy (NBER 8997) | `source_count`, `artist_cross_source_premium` |
| 반복 판매 지수 | Mei & Moses 2002 | `repeat_sale_index` (향후) |
| 유찰 시그널링 | Kim & Park, "The paradox of being unsold: hidden signaling value of bought-in in Korean art auction", J. Cultural Economics, 2025 | `artist_unsold_rate` (NaN-safe) |
| 계절성 | Renneboog 2013 | `sale_month` |
| 가격 이질성 | Scorcu & Zanola 2021 | `source_price_dispersion` |
| ML 예측 (CatBoost) | Karakasis et al., "Tabular Data Models for Predicting Art Auction Results", Applied Sciences 14(23), 2024 | CatBoost MultiQuantile 유지 |

---

## 6. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| 9개 피처 제거로 성능 하락 | 제거 피처 대부분 dead/상수/공선성 → 영향 최소. A/B 검증 |
| `source_count` 과적합 | Bayesian shrinkage 적용 (< 3건 → NaN) |
| 학습 시간 증가 (124K × 75 월) | 월 단위 윈도우 최적화 완료 (1,025 → 75 루프) |
| 기존 K-Auction 성능 퇴보 | Go/No-Go: K-Auction test MdAPE ≤ 40% (현재 37.9%) |
| HEDONIC_FEATURES 참조 파일 누락 | Sprint 0에서 `cold_start.py`, `quantile_model.py`의 HEDONIC_FEATURES 의존도 함께 업데이트 |

---

## 7. 1차/2차 리서치 교차 검증

| 항목 | 1차 에이전트 | 2차 Codex CLI | 합의 |
|------|:-----------:|:------------:|------|
| 제거: source_type | O | O | 동의 |
| 제거: size_ho/above40 | O | O | 동의 |
| 제거: auction_type_factor | O | O | 동의 |
| 제거: medium_x_auction_avg | - | O | Codex 제안 채택 |
| 제거: artist_premium_ratio | O | O | 동의 |
| 제거: artist_reappear_flag | - | O | Codex 제안 채택 |
| 제거: global_avg_price | - | O | Codex 제안 채택 (median과 공선성) |
| 제거: comp_match_level | - | O | Codex 제안 채택 |
| 신규: source_count | O | O | 동의 — 최우선 |
| 신규: source_price_dispersion | O | O | 동의 |
| 신규: artist_cross_source_premium | O | O | 동의 |
| 신규: sale_month | O | - | 에이전트 제안 채택 (계절성) |
| 신규: source_tier (범주형) | O (3단계) | - | **보류** — 현재 데이터로 tier 기준 불명확, 향후 검토 |
| 신규: repeat_sale_index | - | O | **향후** — 데이터 충분성 확인 필요 |
