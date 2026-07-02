# PP-CCOEF1 / PP-CCOEF2 — 콜드 작가계수(Artist Coefficient) 구조 재설계 실험 계획

- 날짜: 2026-06-22
- 트랙: Track6 가격예측 / Cold
- 브랜치: `exp/track6-price-prediction`
- 상태: 계획(미착수)
- 관련 메모리: track6-cold-search-meta-diagnosis, track6_price_prediction_state
- 선행 종결 라인: Cold 수집 없는 점예측 개선 17건 종결(PP-CDATA1/2 등) → 본 실험은 **타깃·학습 구조 재설계**로 그 종결을 재도전

## 0. 배경과 동기

세계 미술시장의 작가 단가(호당가 / Factor / $·in⁻² / Art Coefficient)는 공통적으로
`작품가격 = 크기 × 작가계수` 구조다. 리서치가 제안한 강력 피처(`artist_avg_price`,
`artist_price_per_area`, `sales_count`, `price_growth_3y`)는 **전부 작가 본인 거래 이력이
필요 = Warm 피처**이며, Track6는 이미 `pp_hcoef`(38회, 작가별 호당 가격계수)로 이를 소진했다.

**콜드 작가는 본인 이력이 0 → 계수를 직접 계산 불가.** 따라서 콜드에서 안 해본 영역은
"계수를 피처로 추가"가 아니라 **계수 개념을 학습 구조로 옮기는 것**이다:

1. 타깃을 `log(가격)` → `log(가격/면적)`(= 계수)로 재매개화 (PP-CCOEF1)
2. 메타데이터로 작가계수를 임퓨테이션 (PP-CCOEF2)

## 1. 데이터·자원 사실 (확인 완료 2026-06-22)

- 콜드 feature CSV = **작품 구조 피처만**: `width_cm, height_cm, depth_cm, area_cm2,
  log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category,
  medium_support_bucket, is_extreme_aspect_ratio` (작가 메타 없음).
- v0.2 운영 base feature_set(12) = 위 + `size_bucket, support_size_bucket`. 모델 =
  LightGBM Quantile q10/q40/q50/q90. test 지표 q50 = **0.4823 / 1.242 / 4.380**.
- 작가 메타는 **별도 조인**(PP-CDATA1 `run_cold_meta_*.py` 로직 재사용). 콜드 커버리지
  부분적: 생년 25% / 전시 37% / 팔로워 69%.
- 라벨: `price_krw`, `ln_price_krw`, `artist_key`.

## 2. PP-CCOEF1 (A안) — 크기 정규화 타깃 재매개화

### 설계
- **타깃**: `y = ln(price_krw / area_cm2)` (단위면적당 계수의 로그).
- **피처**: v0.2와 동일 12개. 면적 피처(`area_cm2`, `log_area`)는 **유지** — 트리가 잔여
  크기 곡률(대형작일수록 단위면적당 단가 하락 등)을 학습하도록.
- **모델**: v0.2와 동일 LGB Quantile q10/q40/q50/q90, 동일 하이퍼파라미터(공정 비교).
- **복원**: `price_hat = exp(pred) × area_cm2`. 각 분위수도 동일하게 면적 곱.

### 왜 안 해본 것인가
- 모든 콜드 모델은 `log(가격)`을 직접 예측. PP-CGRP1은 그룹통계를 **피처**로 넣은 것을
  기각(트리 base가 이미 학습)한 것이지 **타깃 변경**이 아님.
- E010은 크기를 **피처**로 사용(`ln호수`), 타깃에서 제거한 적 없음.

### 반증 기준 (falsification)
- artist 80/70% holdout ≥200회에서 MAPE/p95 개선확률 ≥0.90(PP-CBASE1 게이트) 미달 →
  **A 기각**. 단 "크기 정규화가 지배 축 분산을 줄이나?"라는 방향 신호는 B로 전달.

### 정직한 리스크 / 가드
- `area_cm2` 측정오차가 예측에 직접 곱해짐. → 면적 극단값(상·하위 1%) 예측오차 민감도를
  별도 측정. 악화 시 면적 클립 또는 극단 면적 fallback(v0.2 직접 예측) 가드 추가.

## 3. PP-CCOEF2 (B안) — 2단계 작가계수 임퓨테이션 *(A 학습 결과 반영 후 착수)*

### 설계
- **1단계 (계수 산출)**: Warm 작가별 `coef_a = shrunk_median over works of (price/area)`.
  EB(Empirical Bayes) 수축 — 작은/거친 그룹은 전역 중앙값으로 수축(SVCSHRINK 방식, k≈5).
  결과 = 작가 1명당 1행의 계수 테이블.
- **2단계 (메타 회귀)**: `ln(coef_a) ~ 메타`(career_stage, exhibition, gallery_tier,
  followers, birth_year, total_works), robust 회귀(Huber 또는 LGB). **Warm 작가만** 학습.
- **콜드 추론**: 콜드 작가 메타 → `coef_hat` 예측 → `price_hat = exp(coef_hat) × area_cm2`.
  메타 미보유 작가는 **PP-CCOEF1 또는 v0.2로 fallback**.

### 왜 안 해본 것인가
- 기존 콜드 메타 실험(PP-CDATA1/2 등)은 전부 **행 단위 `log(가격)`** 학습. 본 실험은
  **작가 단위로 집계한 계수**(독일·이탈리아의 "작가 Factor")를 타깃으로 두어, 메타 회귀가
  작가 내부 잡음을 보기 전에 먼저 걷어낸다.

### 선택편향 가드 (필수)
- 메모리 경고: rich-meta subset 이득은 운영 신규 작가로 전이 안 됨(선택편향).
- → **pseudo-cold에서 메타를 운영 커버리지 수준(생년 25%/전시 37%/팔로워 69%)으로
  마스킹**해 평가. 커버리지 층화 보고(보유/부분/무보유). 절대 rich subset만으로 결론 금지.

### 보고 축
- B vs A vs v0.2를 (a) 메타 보유 콜드 subset, (b) fallback 포함 전체 두 축으로 보고.
- 커버리지·fallback 비율을 명시(전체 이득 = subset 이득 × 커버리지).

## 4. 공통 평가 프로토콜

- **평가셋**: fixed cold test(3,099 / 200작가, 누수0) + artist 반복 holdout(80/70%, ≥200회)
  + pseudo-cold(저행수 작가 마스킹, seed≥3).
- **게이트**: PP-CBASE1 — artist holdout MAPE/p95 개선확률 ≥0.90.
- **비교 base**: 검색 없는 운영 base v0.2 q50 (0.4823 / 1.242 / 4.380). (raw-input 모델
  변경이므로 search 기반 v0.3가 아닌 v0.2가 공정 비교.)

## 5. 절대 규칙 (트랙 공통)

- **0604는 콜드에서 사용 금지** (사용자 지시).
- **test로 후보 선택 금지** — 최종 확인 1회만.
- 학습 보정/수축/회귀는 **OOF/fold에서만** 적합.
- 운영 입력 불가 피처를 라우팅/보정 기준으로 쓰지 않음.
- 실험은 `experiments/track6/PP-CCOEF1_cold_size_normalized_target/`,
  `experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/`에 저장,
  `postprocessing_experiment_matrix.md` 갱신.

## 6. 산출물

- 스크립트: 각 실험 폴더 `scripts/run_*.py` (v0.2 LGB config + PP-CDATA1 메타 조인 재사용).
- 아티팩트: 학습 모델 joblib, OOF 예측, holdout/pseudo-cold 지표 JSON.
- 요약: `pp_ccoef1_*_summary.md`, (B 진행 시) `pp_ccoef2_*_summary.md`.
- 결론에 따라 채택 시 별도 v0.x artifact 동결 여부 의사결정.

## 7. 성공/종결 기준

- **PP-CCOEF1**: artist holdout 게이트 통과 시 채택 후보 → B 설계에 size-모델 통합. 미달 시
  "크기 정규화 단독 무익" 기록 후 B로 진행(타깃 구조 신호만 활용).
- **PP-CCOEF2**: 메타 보유 subset + pseudo-cold 마스킹 평가에서 게이트 통과 + 전체(fallback
  포함) 비악화 시 채택 후보. 미달 시 "콜드 계수 임퓨테이션도 데이터 프런티어" 기록 →
  종결 재도전 결론(수집 없이 콜드 점예측 개선 불가) 강화.

## 8. 실행 순서

1. PP-CCOEF1 구현·평가 → 반증 판정.
2. (1 결과 반영) PP-CCOEF2 구현·평가 → 채택/기각 판정.
3. 매트릭스·요약 갱신, 필요 시 메모리 업데이트.
