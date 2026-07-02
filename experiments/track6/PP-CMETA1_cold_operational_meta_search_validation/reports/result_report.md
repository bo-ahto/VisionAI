# Cold 운영형 작가 메타/인터넷 검색 피처 검증

- 작성일: 2026-06-18T03:05:38
- 목적: 같은 작가 가격 이력 없이, 작품 정보와 운영 수집 가능한 작가 메타/인터넷 검색 피처만으로 Cold 가격을 예측할 수 있는지 확인한다.
- 제외: `artist_key` 모델 피처, 같은 작가 가격 통계, 작가별 search_delta lookup 후처리.
- 검색 피처: 이번 실행에서는 기존 동결 검색 cache를 사용했다. 운영에서는 같은 schema로 신규 작가를 검색 수집해 넣는 방식으로 연결한다.

## Test 결과
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | n_features | feature_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_artist_meta_search_external_lgbq | test | 0.442147 | 1.048405 | 3.353732 | 0.856668 | 87 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_external_core_lgbq | test | 0.444391 | 1.129475 | 3.849633 | 0.892502 | 56 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |
| artwork_artist_meta_search_context_lgbq | test | 0.474061 | 1.048328 | 3.353192 | 0.874039 | 50 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_artist_meta_lgbq | test | 0.477150 | 1.081916 | 3.030531 | 0.890215 | 32 | 작품 정보 + 비가격성 작가 메타 |
| artwork_only_lgbq | test | 0.482312 | 1.242417 | 4.380572 | 0.941084 | 12 | 작품 정보만 사용 |

## Validation 결과
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | n_features | feature_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_artist_meta_lgbq | validation | 0.382133 | 0.547061 | 1.453648 | 0.657704 | 32 | 작품 정보 + 비가격성 작가 메타 |
| artwork_artist_meta_search_context_lgbq | validation | 0.385326 | 0.556472 | 1.430343 | 0.664056 | 50 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_only_lgbq | validation | 0.396190 | 0.663304 | 1.791011 | 0.678909 | 12 | 작품 정보만 사용 |
| artwork_artist_meta_search_external_lgbq | validation | 0.412904 | 0.588742 | 1.504212 | 0.655553 | 87 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_external_core_lgbq | validation | 0.420587 | 0.652333 | 1.990710 | 0.692781 | 56 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |

## 외부 피처 커버리지
| split | feature | covered_rows | n | coverage_rate |
| --- | --- | --- | --- | --- |
| train | artist_meta_birth_year | 4366 | 26914 | 0.162220 |
| train | artist_meta_followers | 19744 | 26914 | 0.733596 |
| train | artist_meta_total_works | 19744 | 26914 | 0.733596 |
| train | search_success_flag | 11962 | 26914 | 0.444453 |
| train | search_quality_score | 26914 | 26914 | 1.000000 |
| train | artist_exhibition_total_count | 16284 | 26914 | 0.605038 |
| train | gallery_tier_any_available_flag | 16304 | 26914 | 0.605781 |
| validation | artist_meta_birth_year | 209 | 2753 | 0.075917 |
| validation | artist_meta_followers | 2129 | 2753 | 0.773338 |
| validation | artist_meta_total_works | 2129 | 2753 | 0.773338 |
| validation | search_success_flag | 1573 | 2753 | 0.571377 |
| validation | search_quality_score | 2753 | 2753 | 1.000000 |
| validation | artist_exhibition_total_count | 1902 | 2753 | 0.690883 |
| validation | gallery_tier_any_available_flag | 1902 | 2753 | 0.690883 |
| test | artist_meta_birth_year | 767 | 3099 | 0.247499 |
| test | artist_meta_followers | 2322 | 3099 | 0.749274 |
| test | artist_meta_total_works | 2322 | 3099 | 0.749274 |
| test | search_success_flag | 1449 | 3099 | 0.467570 |
| test | search_quality_score | 3099 | 3099 | 1.000000 |
| test | artist_exhibition_total_count | 1693 | 3099 | 0.546305 |
| test | gallery_tier_any_available_flag | 1734 | 3099 | 0.559535 |

## 후보별 피처 설계
| candidate | n_features | feature_strategy | hypothesis |
| --- | --- | --- | --- |
| artwork_only_lgbq | 12 | 작품 정보만 사용 | 작가 외부 정보가 전혀 없을 때의 운영 최저 기준 |
| artwork_artist_meta_lgbq | 32 | 작품 정보 + 비가격성 작가 메타 | 학습 작가의 메타 패턴을 배워 신규 작가 메타와 작품 정보로 예측 |
| artwork_artist_meta_search_context_lgbq | 50 | 작품 정보 + 작가 메타 + 검색 문맥 | 인터넷 검색에서 얻은 미술/전시/갤러리 문맥이 Cold 예측을 보완하는지 확인 |
| artwork_artist_meta_external_core_lgbq | 56 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 | 검색 결과를 구조화한 전시/갤러리 피처가 예측력을 갖는지 확인 |
| artwork_artist_meta_search_external_lgbq | 87 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 | 운영 수집 가능한 외부 정보를 모두 사용한 Cold 후보 |

## 해석
- 이 실험은 사용자가 기대한 운영형 Cold 구조를 lookup 없이 분리 검증한다.
- `artwork_only_lgbq` 대비 작가 메타/검색/전시 피처 후보의 개선 여부가 핵심 판단 기준이다.
- 실제 운영 승격 전에는 신규 작가 live search 수집 -> feature 생성 -> same schema inference -> fallback 정책 검증이 필요하다.