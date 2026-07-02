# Cold 운영형 메타/검색 q40 guard + lookup 검증

- 작성일: 2026-06-18T03:12:27
- 목적: PP-CMETA1 운영형 Cold 후보에 q40 guard와 v0.3 작가별 search_delta lookup을 붙였을 때 성능이 추가 개선되는지 검증한다.
- 주의: lookup은 frozen 작가 단위 보정값이다. fixed test coverage가 높아도 신규 작가 운영 coverage를 보장하지 않는다.

## Test 결과 상위
| candidate | policy | MdAPE | MAPE | p95_APE | RMSE_log | guard_rate | lookup_coverage | feature_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_artist_meta_external_core_lgbq | lookup_only | 0.422821 | 0.993299 | 3.390348 | 0.867314 | 0.469506 | 1.000000 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |
| artwork_artist_meta_search_external_lgbq | lookup_only | 0.431277 | 0.928508 | 3.138994 | 0.837833 | 0.392707 | 1.000000 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_external_core_lgbq | guard_plus_lookup | 0.433833 | 0.964857 | 2.908443 | 0.877675 | 0.469506 | 1.000000 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |
| artwork_artist_meta_search_external_lgbq | guard_plus_lookup | 0.435616 | 0.902715 | 2.876001 | 0.846652 | 0.392707 | 1.000000 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_search_external_lgbq | base_q50 | 0.442147 | 1.048405 | 3.353732 | 0.856668 | 0.392707 | 1.000000 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_external_core_lgbq | base_q50 | 0.444391 | 1.129475 | 3.849633 | 0.892502 | 0.469506 | 1.000000 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |
| artwork_artist_meta_search_external_lgbq | guard_only | 0.445887 | 1.023381 | 2.999220 | 0.865001 | 0.392707 | 1.000000 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_lgbq | lookup_only | 0.449360 | 0.953269 | 2.843848 | 0.865346 | 0.483704 | 1.000000 | 작품 정보 + 비가격성 작가 메타 |
| artwork_artist_meta_search_context_lgbq | lookup_only | 0.453890 | 0.930020 | 3.121927 | 0.852115 | 0.407228 | 1.000000 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_artist_meta_lgbq | guard_plus_lookup | 0.455603 | 0.931530 | 2.548208 | 0.881572 | 0.483704 | 1.000000 | 작품 정보 + 비가격성 작가 메타 |
| artwork_artist_meta_search_context_lgbq | guard_plus_lookup | 0.456128 | 0.902076 | 2.474609 | 0.862595 | 0.407228 | 1.000000 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_artist_meta_external_core_lgbq | guard_only | 0.459289 | 1.100325 | 3.454557 | 0.903412 | 0.469506 | 1.000000 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |
| artwork_only_lgbq | guard_plus_lookup | 0.473344 | 1.024546 | 3.566223 | 0.913701 | 0.525976 | 1.000000 | 작품 정보만 사용 |
| artwork_artist_meta_search_context_lgbq | base_q50 | 0.474061 | 1.048328 | 3.353192 | 0.874039 | 0.407228 | 1.000000 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_artist_meta_search_context_lgbq | guard_only | 0.474385 | 1.021412 | 2.795260 | 0.884392 | 0.407228 | 1.000000 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_only_lgbq | lookup_only | 0.476602 | 1.095001 | 4.163167 | 0.914496 | 0.525976 | 1.000000 | 작품 정보만 사용 |
| artwork_artist_meta_lgbq | base_q50 | 0.477150 | 1.081916 | 3.030531 | 0.890215 | 0.483704 | 1.000000 | 작품 정보 + 비가격성 작가 메타 |
| artwork_only_lgbq | base_q50 | 0.482312 | 1.242417 | 4.380572 | 0.941084 | 0.525976 | 1.000000 | 작품 정보만 사용 |
| artwork_only_lgbq | guard_only | 0.487651 | 1.162826 | 3.716939 | 0.939613 | 0.525976 | 1.000000 | 작품 정보만 사용 |
| artwork_artist_meta_lgbq | guard_only | 0.490841 | 1.060964 | 2.720025 | 0.907340 | 0.483704 | 1.000000 | 작품 정보 + 비가격성 작가 메타 |

## Validation 결과 상위
| candidate | policy | MdAPE | MAPE | p95_APE | RMSE_log | guard_rate | lookup_coverage | feature_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_only_lgbq | lookup_only | 0.375197 | 0.638058 | 1.566603 | 0.668859 | 0.477661 | 1.000000 | 작품 정보만 사용 |
| artwork_artist_meta_lgbq | guard_plus_lookup | 0.379196 | 0.512834 | 1.379557 | 0.659888 | 0.303669 | 1.000000 | 작품 정보 + 비가격성 작가 메타 |
| artwork_artist_meta_lgbq | base_q50 | 0.382133 | 0.547061 | 1.453648 | 0.657704 | 0.303669 | 1.000000 | 작품 정보 + 비가격성 작가 메타 |
| artwork_artist_meta_lgbq | lookup_only | 0.382575 | 0.539027 | 1.396444 | 0.657481 | 0.303669 | 1.000000 | 작품 정보 + 비가격성 작가 메타 |
| artwork_artist_meta_lgbq | guard_only | 0.383583 | 0.519518 | 1.338227 | 0.658481 | 0.303669 | 1.000000 | 작품 정보 + 비가격성 작가 메타 |
| artwork_artist_meta_search_external_lgbq | guard_plus_lookup | 0.383870 | 0.521932 | 1.115084 | 0.638107 | 0.309117 | 1.000000 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_only_lgbq | guard_plus_lookup | 0.384246 | 0.584684 | 1.423280 | 0.663050 | 0.477661 | 1.000000 | 작품 정보만 사용 |
| artwork_artist_meta_search_context_lgbq | base_q50 | 0.385326 | 0.556472 | 1.430343 | 0.664056 | 0.317835 | 1.000000 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_only_lgbq | guard_only | 0.385876 | 0.604521 | 1.548763 | 0.666708 | 0.477661 | 1.000000 | 작품 정보만 사용 |
| artwork_artist_meta_search_external_lgbq | lookup_only | 0.386246 | 0.549714 | 1.338196 | 0.635454 | 0.309117 | 1.000000 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_search_context_lgbq | guard_only | 0.390196 | 0.527218 | 1.271878 | 0.666324 | 0.317835 | 1.000000 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_artist_meta_search_context_lgbq | lookup_only | 0.392620 | 0.548320 | 1.614276 | 0.663471 | 0.317835 | 1.000000 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_artist_meta_search_context_lgbq | guard_plus_lookup | 0.392939 | 0.520643 | 1.498898 | 0.667488 | 0.317835 | 1.000000 | 작품 정보 + 작가 메타 + 검색 문맥 |
| artwork_only_lgbq | base_q50 | 0.396190 | 0.663304 | 1.791011 | 0.678909 | 0.477661 | 1.000000 | 작품 정보만 사용 |
| artwork_artist_meta_external_core_lgbq | guard_plus_lookup | 0.397272 | 0.547891 | 1.407557 | 0.655852 | 0.364693 | 1.000000 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |
| artwork_artist_meta_external_core_lgbq | lookup_only | 0.404466 | 0.599424 | 1.723741 | 0.666510 | 0.364693 | 1.000000 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |
| artwork_artist_meta_external_core_lgbq | guard_only | 0.412094 | 0.587826 | 1.679737 | 0.675631 | 0.364693 | 1.000000 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |
| artwork_artist_meta_search_external_lgbq | guard_only | 0.412338 | 0.559150 | 1.392738 | 0.656457 | 0.309117 | 1.000000 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_search_external_lgbq | base_q50 | 0.412904 | 0.588742 | 1.504212 | 0.655553 | 0.309117 | 1.000000 | 작품 정보 + 작가 메타 + 검색 + 전시/갤러리 |
| artwork_artist_meta_external_core_lgbq | base_q50 | 0.420587 | 0.652333 | 1.990710 | 0.692781 | 0.364693 | 1.000000 | 작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처 |