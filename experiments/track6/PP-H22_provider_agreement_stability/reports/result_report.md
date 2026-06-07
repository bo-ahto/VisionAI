# PP-H22 Naver x Python 검색 Provider 일치도 검증

- 목적: Naver 공식 검색 API와 Python 검색 provider가 같은 작가에 대해 일관된 외부 신호를 주는지 검증한다.
- 핵심 산출물: 작가별 provider agreement score, disagreement risk flag, agreement 등급별 예측 오차.

## Provider 수집 현황

| provider_family | provider | rows | result_rows | artist_count | template_count |
| --- | --- | --- | --- | --- | --- |
| naver_official | naver_api_blog | 1760 | 1723 | 80 | 5 |
| naver_official | naver_api_news | 1599 | 1530 | 80 | 5 |
| naver_official | naver_api_webkr | 1900 | 1884 | 80 | 5 |
| python_search | python_ddg | 12818 | 12818 | 428 | 5 |
| python_search | python_ddg_art_context | 12833 | 12833 | 428 | 5 |

## 작가별 일치도 등급 요약

| provider_agreement_grade | artist_count | agreement_median | source_similarity_median | context_similarity_median | domain_jaccard_median | risk_rate |
| --- | --- | --- | --- | --- | --- | --- |
| low | 69 | 0.384286 | 0.173333 | 0.548075 | 0 | 1 |
| medium | 9 | 0.532586 | 0.5175 | 0.815179 | 0 | 0.222222 |

## Test 오차 Slice

| candidate | slice | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| h23_gallery_museum_median_cap0.2 | agreement_grade=low | 1192 | 0.347606 | 1.29959 | 3.60856 | 0.857301 |
| h23_gallery_museum_median_cap0.2 | agreement_grade=missing | 1907 | 0.47651 | 0.696558 | 2.24234 | 0.82543 |
| h23_gallery_museum_median_cap0.2 | disagreement_risk=True | 3099 | 0.431277 | 0.928508 | 3.13899 | 0.837833 |
| h23_gallery_museum_median_cap0.2 | overall | 3099 | 0.431277 | 0.928508 | 3.13899 | 0.837833 |
| h23_news_median_cap0.2 | agreement_grade=low | 1192 | 0.3344 | 1.36435 | 4.62019 | 0.846901 |
| h23_news_median_cap0.2 | agreement_grade=missing | 1907 | 0.47651 | 0.696558 | 2.24234 | 0.82543 |
| h23_news_median_cap0.2 | disagreement_risk=True | 3099 | 0.425322 | 0.95342 | 3.15419 | 0.833754 |
| h23_news_median_cap0.2 | overall | 3099 | 0.425322 | 0.95342 | 3.15419 | 0.833754 |
| h23_social_blog_median_cap0.2 | agreement_grade=low | 1192 | 0.380624 | 1.29574 | 3.60856 | 0.862851 |
| h23_social_blog_median_cap0.2 | agreement_grade=missing | 1907 | 0.47651 | 0.696558 | 2.24234 | 0.82543 |
| h23_social_blog_median_cap0.2 | disagreement_risk=True | 3099 | 0.434409 | 0.927026 | 3.13899 | 0.840021 |
| h23_social_blog_median_cap0.2 | overall | 3099 | 0.434409 | 0.927026 | 3.13899 | 0.840021 |
| pp_y2_base | agreement_grade=low | 1192 | 0.379951 | 1.57822 | 4.62891 | 0.909012 |
| pp_y2_base | agreement_grade=missing | 1907 | 0.481657 | 0.717236 | 2.34541 | 0.822259 |
| pp_y2_base | disagreement_risk=True | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 |
| pp_y2_base | overall | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 |

## 일치도 낮은 작가 우선 검수 목록

| artist_search_name | provider_agreement_score | provider_agreement_grade | source_group_similarity | context_similarity | domain_jaccard | coverage_balance | homonym_safety | provider_disagreement_risk_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 김기섭 | 0.264809 | low | 0.0416667 | 0.584236 | 0 | 0.694444 | 0 | True |
| 박용호 | 0.27437 | low | 0.0821918 | 0.544178 | 0.0454545 | 0.684932 | 0 | True |
| 김영옥 | 0.276667 | low | 0 | 0.546667 | 0 | 0.666667 | 0.4 | True |
| 홍정우 | 0.306556 | low | 0.109589 | 0.555753 | 0.0434783 | 0.684932 | 0.2 | True |
| 김병관 | 0.307229 | low | 0.108333 | 0.45625 | 0 | 0.375 | 0.99 | True |
| 강선미 | 0.307792 | low | 0.113333 | 0.4575 | 0 | 0.375 | 0.975 | True |
| 박영 | 0.316063 | low | 0 | 0.419583 | 0 | 0.75 | 0.986667 | True |
| 장은하 | 0.316857 | low | 0.125 | 0.486429 | 0 | 0.35 | 0.99 | True |
| 안교범 | 0.319331 | low | 0.155509 | 0.498909 | 0.0190476 | 0.351351 | 0.846154 | True |
| 장지원 | 0.319844 | low | 0.111667 | 0.519375 | 0 | 0.375 | 0.946667 | True |
| 김연홍 | 0.325313 | low | 0.165 | 0.472132 | 0 | 0.34 | 0.985294 | True |
| 김지훈 | 0.327375 | low | 0.146667 | 0.6075 | 0.0277778 | 0.666667 | 0.2 | True |
| 허정록 | 0.329917 | low | 0.126667 | 0.485 | 0 | 0.5 | 0.893333 | True |
| 박노엘 | 0.331333 | low | 0.175714 | 0.507857 | 0.0176991 | 0.28 | 0.982143 | True |
| 김소정 | 0.332389 | low | 0.16 | 0.523333 | 0.037037 | 0.666667 | 0.4 | True |
| 배준성 | 0.335917 | low | 0.06 | 0.465 | 0 | 0.666667 | 0.986667 | True |
| 홍미희 | 0.342976 | low | 0.0547945 | 0.457192 | 0 | 0.73 | 1 | True |
| 김레이시 | 0.349635 | low | 0.146154 | 0.481923 | 0 | 0.52 | 1 | True |
| 양지훈 | 0.352545 | low | 0.0877778 | 0.481736 | 0 | 0.694444 | 0.972222 | True |
| 이다겸 | 0.35325 | low | 0.12 | 0.525 | 0 | 0.666667 | 0.8 | True |

## 해석

- agreement score가 높다는 것은 두 provider가 비슷한 source group, 미술 문맥, 도메인 범위를 반환했다는 뜻이다.
- agreement score가 낮은 작가는 동명이인, 무관 검색 결과, provider별 편향 가능성이 있어 가격점 예측 직접 반영보다 신뢰도 하향 또는 수동 검수 후보로 보는 것이 안전하다.
- domain jaccard는 검색 엔진 특성상 낮게 나올 수 있으므로 source/context similarity를 더 중요하게 해석한다.
