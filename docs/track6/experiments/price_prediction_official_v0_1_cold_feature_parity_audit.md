# 공식 v0.1 Cold feature parity 감사

- 작성일: 2026-06-12T16:26:07+09:00
- 비교 범위: fixed-test Cold 3099건
- 비교 대상: 실험 feature 생성 결과 vs 공식 v0.1 서비스 adapter feature 생성 결과

## 1. 결론

- exact feature parity 통과: 예
- exact prediction parity 통과: 예
- 서비스 adapter 의미: exact_fixed_test_parity
- fixed-test 작가 수: 200명
- row-level Cold feature store hit rate: 1.0000
- 공식 전시/갤러리 cache 작가 수: 1773명, fixed-test 교집합: 0명
- 공식 검색 snapshot 작가 수: 150명, fixed-test 교집합: 0명
- 해석: row-level feature store가 적중한 행은 실험 당시 Cold 입력 피처를 그대로 재사용한다. 미적중 행은 공식 서비스 cache 기반 proxy feature로 계산한다.

## 2. Feature 그룹별 일치율

| 그룹 | 타입 | 피처 수 | 평균 일치율 | 최소 일치율 | 실험 non-missing | 서비스 non-missing |
|---|---|---:|---:|---:|---:|---:|
| artist_meta | categorical | 3 | 1.0000 | 1.0000 | 0.3164 | 0.3164 |
| artist_meta | numeric | 17 | 1.0000 | 1.0000 | 0.7496 | 0.7496 |
| artwork_base | categorical | 6 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| artwork_base | numeric | 6 | 1.0000 | 1.0000 | 0.9489 | 0.9489 |
| exhibition_gallery | categorical | 7 | 1.0000 | 1.0000 | 0.6528 | 0.6528 |
| exhibition_gallery | numeric | 23 | 1.0000 | 1.0000 | 0.8369 | 0.8369 |
| search | categorical | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| search | numeric | 22 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## 3. 불일치가 큰 피처

| 피처 | 그룹 | 타입 | 일치율 | 평균 차이 | p95 차이 |
|---|---|---|---:|---:|---:|
| artist_meta_birth_year | artist_meta | numeric | 1.0000 | 0.000000 | 0.000000 |
| search_art_context_count | search | numeric | 1.0000 | 0.000000 | 0.000000 |
| gallery_validated_x_followers_log | exhibition_gallery | numeric | 1.0000 | 0.000000 | 0.000000 |
| gallery_tier_x_exhibition_total_log | exhibition_gallery | numeric | 1.0000 | 0.000000 | 0.000000 |
| gallery_tier_validated_score | exhibition_gallery | numeric | 1.0000 | 0.000000 | 0.000000 |
| gallery_tier_validated_available_flag | exhibition_gallery | numeric | 1.0000 | 0.000000 | 0.000000 |
| gallery_tier_validated | exhibition_gallery | categorical | 1.0000 |  |  |
| gallery_tier_raw_numeric | exhibition_gallery | numeric | 1.0000 | 0.000000 | 0.000000 |
| gallery_tier_raw_bucket | exhibition_gallery | categorical | 1.0000 |  |  |
| search_art_context_count_log | search | numeric | 1.0000 | 0.000000 | 0.000000 |
| gallery_tier_raw_available_flag | exhibition_gallery | numeric | 1.0000 | 0.000000 | 0.000000 |
| gallery_ref_type | exhibition_gallery | categorical | 1.0000 |  |  |
| gallery_feature_source | exhibition_gallery | categorical | 1.0000 |  |  |
| gallery_exhibition_bucket | exhibition_gallery | categorical | 1.0000 |  |  |
| gallery_city_count_log | exhibition_gallery | numeric | 1.0000 | 0.000000 | 0.000000 |

## 4. 예측값 영향

| 항목 | 실험 feature 기준 | 서비스 feature 기준 |
|---|---:|---:|
| MdAPE | 0.409820 | 0.409820 |
| MAPE | 0.849260 | 0.849260 |
| p95_APE | 2.346465 | 2.346465 |
| RMSE_log | 0.850259 | 0.850259 |

## 5. 판단

- 현재 서비스 adapter는 검색 snapshot과 전시/갤러리 작가 단위 cache를 사용해 Cold 최고 경로의 입력을 생성할 수 있습니다.
- 다만 fixed-test와 완전히 같은 row-level feature parity는 아직 아닙니다.
- 완전 parity가 필요하면 실험에서 사용한 row-level 전시/갤러리 및 검색 feature store를 운영 DB에 동일 스키마로 저장하고, 신규 입력에는 같은 builder를 적용해야 합니다.
