# Phase 4 최종 보고서 — 가격 예측 고도화

> **작성일**: 2026-03-29
> **Champion**: Ensemble (CatBoost + RandomForest → Ridge meta)
> **최종 성능**: MdAPE 30.16% (Validation), 34.38% (Test)

---

## 1. 성능 개선 추이

| Phase | 피처 | V-MdAPE | V-W30% | T-MdAPE |
|-------|------|---------|--------|---------|
| Phase 3 기본 | 23 | 34.13% | 45.2% | — |
| Phase 4a (피처 고도화) | 39 | 33.14% | 46.7% | — |
| Phase 4a (앙상블) | 39 | 31.31% | 48.0% | — |
| Phase 4b (외부 데이터) | 42 | 30.65% | 48.9% | — |
| **Phase 4 최종 (NLP)** | **49** | **30.16%** | **49.9%** | **34.38%** |

**총 개선: MdAPE -3.97%p, Within 30% +4.7%p**

---

## 2. Champion 비교

| 모델 | V-MdAPE | V-R² | T-MdAPE | T-R² |
|------|---------|------|---------|------|
| Model-A (CatBoost) | 31.58% | 0.579 | 35.16% | 0.300 |
| **Ensemble (CB+RF)** | **30.16%** | **0.608** | **34.38%** | **0.312** |

**타입별 (Validation):**

| 타입 | Model-A | Ensemble |
|------|---------|---------|
| 메이저 | 36.35% | **32.82%** |
| 프리미엄 | 26.62% | **23.70%** |
| 위클리 | **28.59%** | 29.66% |

**Warm/Cold:**

| 그룹 | Model-A | Ensemble | 비중 |
|------|---------|---------|------|
| Warm | 30.41% | **28.82%** | 94.6% |
| Cold | **62.28%** | 62.87% | 5.4% |

---

## 3. 피처 구성 (49개)

| 카테고리 | 피처 수 | 주요 피처 |
|---------|--------|----------|
| 기본 Hedonic (Phase 3) | 15 | artist_clean, medium, size, 회차 |
| Phase 3 신규 | 8 | artist_median, trend, unsold_rate, size_ho |
| Phase 4 작가 이력 | 10 | recent_avg, momentum, volatility, last_hammer |
| Phase 4 comp 매칭 | 5 | comp_artist_avg, comp_weighted, match_level |
| Phase 4 시장 | 1 | market_price_index |
| Phase 4b 글로벌 | 3 | global_avg/median/count |
| Phase 4 NLP | 7 | title_subject, is_series, language |

---

## 4. 외부 데이터

| 소스 | 작가 | 건수 | 데이터 |
|------|------|------|--------|
| Artsy Price Database | 23명 | ~780건 | 낙찰가, 추정가, 재료, 크기, 경매사 |
| 경매사 | Christie's, Sotheby's, Phillips, SBI | — | 글로벌 5대 |

---

## 5. 코드 산출물

| 카테고리 | 파일 수 |
|---------|--------|
| 소스 코드 | 20+ |
| 테스트 | 14 (291 tests) |
| 스크립트 | 8 |
| 문서 | 7 |
| 데이터 | 5 |

---

## 6. Codex 리뷰

| 대상 | 회수 |
|------|------|
| 기획서 (Phase 3+4) | ~25 |
| 코드 리뷰 | ~35 |
| **총계** | **~60회** |

---

## 7. 실무 적용

### 가능한 적용
- 내부 가이드 가격 (MdAPE 30% 수준)
- 추정가 적정성 검증
- 사전 가치 평가 (Pre-auction)
- 가격 구간 제공 (q25~q75)

### 한계
- Cold artist (5.4%) MdAPE 62% — 외부 데이터 확대 필요
- 추정가 포함 엔진(27%) 대비 여전히 격차
- 이미지 데이터 미활용

---

*Phase 1-2(추정가 포함) + Phase 3(추정가 생성) + Phase 4(고도화) 전체 구현 완료.*
*Claude(구현) + Codex(리뷰) 듀얼 체계, 총 ~60회 리뷰.*
