# PP-H 외부 검색 피처 파일럿 실행 요약

- 실행일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_h_search_pilot_experiments.py`
- 검색 피처 파일: `data/track6/external_search/track6_artist_search_pilot_features.csv`
- 검색 원문 캐시: `data/track6/external_search/track6_artist_search_pilot_raw.jsonl`
- 결과 요약 파일: `experiments/track6/PP-H_search_pilot_summary_metrics.csv`
- 실행 범위: `PP-H7` ~ `PP-H10`

## 1. 실험 추가 이유

- Cold는 `PP-W`에서 작가 메타를 추가하면서 MdAPE가 개선됐지만, 단일 가격으로 서비스 적용하기에는 p95_APE와 MAPE 위험이 남아 있다.
- 기존 작가 메타의 `followers`, `total_works`, `for_sale_works`는 이미 수집된 정적 메타에 가깝다.
- 실제 서비스에서는 작가명 기반 외부 검색 결과를 통해 작가의 시장 노출, 전시 문맥, 동명이인 위험을 추가로 만들 수 있다.
- 따라서 외부 검색 피처가 기존 작가 메타보다 추가 설명력을 주는지 파일럿으로 확인했다.

## 2. 수집 방식

- 수집 대상: Cold train/validation/test 전체에서 등장 빈도가 높은 작가명 상위 `120명`
- 검색어:
  - 한글 작가명: `{작가명} 작가 미술 전시`
  - 영문 작가명: `{artist name} artist art exhibition`
- 검색 결과: DuckDuckGo 공개 검색 상위 `6개` 결과의 제목, 요약, URL
- 주의:
  - 이번 `search_result_count`는 구글/네이버의 전체 검색 결과 수가 아니다.
  - 검색 요청에서 반환된 상위 결과 수와 그 결과의 문맥을 숫자화한 파일럿 피처다.

## 3. 생성 피처

| 피처 묶음 | 예시 피처 | 의미 |
|---|---|---|
| 검색 노출량 | `search_result_count`, `search_source_count` | 상위 검색 결과와 출처 수 |
| 미술 문맥 | `search_art_context_count`, `search_art_match_ratio` | 검색 결과가 미술/작가 문맥과 맞는 정도 |
| 전시/기관 문맥 | `search_exhibition_context_count`, `search_gallery_context_count`, `search_award_institution_context_count` | 전시, 갤러리, 기관, 수상 언급 여부 |
| 시장/소셜 문맥 | `search_market_context_count`, `search_social_context_count` | 경매/판매/뉴스/소셜 언급 여부 |
| 검색 품질 | `search_quality_score`, `search_quality_grade`, `search_homonym_risk_grade` | 검색 결과를 모델에 신뢰해도 되는지 판단하는 값 |
| 상호작용 | `search_quality_x_log_area`, `search_art_match_x_followers_log`, `search_size_quality_bucket` | 검색 인지도 효과가 크기/팔로워/크기 구간에 따라 달라지는지 확인 |

## 4. 수집 커버리지

| split | 전체 row | 고유 작가 수 | 검색 피처 적용 row | 커버리지 | 검색 품질 평균 | high 비율 | medium 비율 | low 비율 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 26,914 | 1,693 | 11,962 | 0.4445 | 0.0945 | 0.0000 | 0.0218 | 0.4226 |
| validation | 2,753 | 168 | 1,573 | 0.5714 | 0.0934 | 0.0000 | 0.0000 | 0.5714 |
| test | 3,099 | 188 | 1,449 | 0.4676 | 0.0963 | 0.0000 | 0.0271 | 0.4405 |

- 수집 작가 120명 중 `low` 품질은 113명, `medium`은 7명, `high`는 0명이었다.
- 다수 작가명에서 미술 작가가 아닌 동명이인, 일반 웹페이지, 해외 무관 페이지가 섞였다.
- 따라서 이번 검색 피처는 단순 검색량보다 “미술 문맥과 맞는지”를 나타내는 품질 피처가 더 중요하다.

## 5. 실행 실험

| 실험 | 내용 | 목적 |
|---|---|---|
| `PP-H7` | 외부 검색 피처 파일럿 수집 | 수집 가능률, 검색 품질, 동명이인 위험 확인 |
| `PP-H8` | Cold CatBoost + 검색 피처 | CatBoost가 작가 메타, 작품 조건, 검색 품질 조합을 가격 구간으로 나눌 수 있는지 확인 |
| `PP-H9` | Cold LightGBM Quantile + 검색 피처 | 검색 피처가 중앙값 예측과 p95/RMSE 안정화에 도움이 되는지 확인 |
| `PP-H10` | CatBoost 검색 피처 모델 + Huber residual 보정 | 검색 피처가 만든 조건별 잔차를 완만하게 보정할 수 있는지 확인 |

## 6. 주요 결과

### 6.1 MdAPE 기준

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| 기존/동일 기준 `PP-H8 baseline_catboost_ppw2_like` | 0.4497 | 1.1111 | 4.1587 | 0.8817 | 유지 |
| `PP-H8 catboost_search_interaction` | 0.4686 | 1.2233 | 3.9762 | 0.8887 | MdAPE/MAPE 악화 |
| `PP-H8 catboost_search_context` | 0.4728 | 1.1602 | 4.0167 | 0.8835 | MdAPE 악화 |

- CatBoost에 검색 피처를 추가하면 p95는 일부 낮아졌지만 MdAPE와 MAPE가 악화됐다.
- 검색 품질이 낮은 작가가 많아 CatBoost가 무관 검색 결과까지 조건 조합으로 학습했을 가능성이 있다.
- 현재 파일럿 기준으로는 CatBoost 검색 피처 추가를 대표 가격 후보로 채택하지 않는다.

### 6.2 MAPE/p95/RMSE 기준

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| `PP-H9 baseline_lightgbm_quantile_ppw4_like` | 0.4766 | 1.0847 | 3.0322 | 0.8907 | 기준 |
| `PP-H9 lightgbm_quantile_search_context` | 0.4788 | 1.0289 | 3.1172 | 0.8716 | MAPE/RMSE 개선, p95 악화 |
| `PP-H9 lightgbm_quantile_search_all` | 0.4773 | 1.0308 | 2.9954 | 0.8664 | p95/RMSE 개선, MdAPE 거의 유지 |

- LightGBM Quantile에서는 검색 피처가 MAPE와 RMSE_log를 줄였다.
- `lightgbm_quantile_search_all`은 p95_APE도 `3.0322`에서 `2.9954`로 낮췄다.
- 다만 기존 `PP-W4`의 Huber residual MAPE 최선 `0.9584`까지는 이기지 못했다.
- 현재 검색 피처는 대표 점 예측보다 가격 범위/위험 방어 후보로 해석하는 것이 적합하다.

### 6.3 검색 피처 기반 Huber residual

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| `PP-H10 base_catboost_search_interaction` | 0.4686 | 1.2233 | 3.9762 | 0.8887 | 기준 |
| `PP-H10 cap0.15_s0.5` | 0.4765 | 1.2784 | 4.3638 | 0.8953 | 악화 |

- CatBoost 검색 피처 모델 위에 Huber residual을 얹은 구조는 개선되지 않았다.
- 검색 피처 자체의 품질이 낮으면 잔차 보정도 잘못된 방향으로 과보정될 수 있다.

## 7. 모델 특성 기반 해석

- CatBoost는 범주형과 조건 조합을 잘 사용하지만, 입력 검색 피처가 노이즈일 때는 잘못된 검색 문맥까지 조건으로 나눌 수 있다.
- 이번 파일럿에서는 검색 품질 `high`가 0명이고 `low`가 대부분이어서 CatBoost의 조합 학습 장점이 오히려 불안정하게 작동했다.
- LightGBM Quantile은 중앙값과 tail 안정화에 강하므로, 검색 피처가 완전히 깨끗하지 않아도 큰 오차 방어 쪽에서는 일부 효과가 있었다.
- 따라서 외부 검색 피처는 CatBoost 대표 점 예측용이 아니라 LightGBM Quantile 기반 위험 보정/가격 범위 산출 보조 피처로 우선 검토하는 것이 맞다.

## 8. 결론

- 외부 검색 기반 실험은 실행 가능하다.
- 그러나 현재 DuckDuckGo 상위 결과 기반 파일럿은 검색 품질이 낮아 대표 가격 예측 후보를 갱신하지 못했다.
- Cold 대표 MdAPE 후보는 여전히 `PP-W2 generated_all_meta_all` 또는 동일 기준 `PP-H8 baseline_catboost_ppw2_like`의 `0.4497`이다.
- 검색 피처의 의미 있는 신호는 `PP-H9 lightgbm_quantile_search_all`에서 확인됐다.
  - MdAPE: `0.4766` -> `0.4773`으로 거의 유지
  - MAPE: `1.0847` -> `1.0308`로 개선
  - p95_APE: `3.0322` -> `2.9954`로 개선
  - RMSE_log: `0.8907` -> `0.8664`로 개선
- 즉, 검색 피처는 현재 단계에서 “점 예측 개선”보다 “큰 오차 방어와 신뢰도/범위 표시 보조”로 가치가 있다.

## 9. 다음 작업

- 전체 작가 수집 전에 검색 품질 개선이 먼저 필요하다.
- 다음 수집에서는 네이버 검색 API 또는 Google Custom Search처럼 결과 품질과 전체 검색 수를 더 안정적으로 제공하는 API를 우선 검토한다.
- 검색 쿼리는 단순 `{작가명} 작가 미술 전시`가 아니라 작가명 + 작품/갤러리/전시 출처 필터를 포함해 오염을 줄인다.
- 수집 피처에는 `동명이인 위험`, `미술 문맥 매칭률`, `출처 신뢰도`, `전시/기관 언급 여부`를 반드시 포함한다.
- 모델 적용은 CatBoost 대표 점 예측보다 LightGBM Quantile 가격 범위/위험 방어 후보부터 재검증한다.
