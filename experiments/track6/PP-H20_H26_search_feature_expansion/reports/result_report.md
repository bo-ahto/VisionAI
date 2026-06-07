# PP-H20~H26 검색 피처 보완 실험

## 목적

- 공식 API가 필요한 검색 피처 실험과 현재 데이터로 가능한 검색 보정 실험을 분리한다.
- H11의 `naver_html` 수집 결과를 사용해 소스군별/최근성/위험 구간 보정 가능성을 추가 확인한다.

## 실행 설정

| 항목 | 값 |
| --- | --- |
| title | 검색 피처 보완 실험 |
| started_at | 2026-06-03T16:06:13 |
| finished_at | 2026-06-03T16:06:14 |
| base_predictions | experiments/track6/PP-H14_H18_search_confidence_qwidth_policy_h12b/outputs/h14_confidence_range_predictions.csv |
| standardized_search | data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv |
| snapshot | data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv |
| min_rows | 30 |
| caps | 0.1, 0.2 |
| note | PP-H20~H22 require official API/provider data. PP-H23~H26 run on current H11 naver_html artifacts. |

## API Preflight

| experiment_id | candidate | status | required | next_action |
| --- | --- | --- | --- | --- |
| PP-H20 | naver_official_api_multi_source | completed_latest_snapshot | NAVER_CLIENT_ID/NAVER_CLIENT_SECRET 또는 NAVER_SEARCH_CLIENT_ID/NAVER_SEARCH_CLIENT_SECRET | 완료된 최신 snapshot 사용 |
| PP-H21 | secondary_global_search_collection | completed_python_latest_snapshot | python_ddg/python_ddg_art_domains 또는 GOOGLE_API_KEY + GOOGLE_CSE_ID | 완료된 Python 검색 snapshot 사용 |
| PP-H22 | provider_agreement_stability | ready | 최소 2개 provider의 동일 작가/동일 템플릿 수집 결과 | Naver x Python 검색 라이브러리 agreement score 계산 |

## Test 전체 결과

| experiment_id | candidate | split | slice | policy | feature | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H23 | h23_news_median_cap0.2 | test | overall | source_group_segment_median | source_group_news_ratio | 3099 | 0.425322 | 0.95342 | 3.15419 | 0.833754 | 0.36657 | 0.579864 |
| PP-H23 | h23_news_median_cap0.1 | test | overall | source_group_segment_median | source_group_news_ratio | 3099 | 0.428314 | 0.989039 | 3.21959 | 0.843963 | 0.349468 | 0.576638 |
| PP-H23 | h23_gallery_museum_median_cap0.2 | test | overall | source_group_segment_median | source_group_gallery_museum_ratio | 3099 | 0.431277 | 0.928508 | 3.13899 | 0.837833 | 0.359793 | 0.570184 |
| PP-H23 | h23_social_blog_median_cap0.1 | test | overall | source_group_segment_median | source_group_social_blog_ratio | 3099 | 0.432786 | 0.976556 | 3.21959 | 0.847065 | 0.338174 | 0.575024 |
| PP-H23 | h23_social_blog_median_cap0.2 | test | overall | source_group_segment_median | source_group_social_blog_ratio | 3099 | 0.434409 | 0.927026 | 3.13899 | 0.840021 | 0.339142 | 0.576638 |
| PP-H23 | h23_gallery_museum_median_cap0.1 | test | overall | source_group_segment_median | source_group_gallery_museum_ratio | 3099 | 0.434833 | 0.977021 | 3.21959 | 0.84598 | 0.34979 | 0.570184 |
| PP-H23 | pp_y2_base | test | overall | base |  | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |
| PP-H23 | h23_exhibition_median_cap0.1 | test | overall | source_group_segment_median | source_group_exhibition_ratio | 3099 | 0.445202 | 1.07556 | 2.93942 | 0.873313 | 0.337851 | 0.558245 |
| PP-H23 | h23_market_median_cap0.1 | test | overall | source_group_segment_median | source_group_market_ratio | 3099 | 0.448473 | 1.10049 | 3.21959 | 0.866827 | 0.340432 | 0.555986 |
| PP-H23 | h23_other_median_cap0.1 | test | overall | source_group_segment_median | source_group_other_ratio | 3099 | 0.448473 | 1.10049 | 3.21959 | 0.866827 | 0.340432 | 0.555986 |
| PP-H23 | h23_exhibition_median_cap0.2 | test | overall | source_group_segment_median | source_group_exhibition_ratio | 3099 | 0.45019 | 1.13823 | 2.76354 | 0.891847 | 0.349468 | 0.556631 |
| PP-H23 | h23_art_general_median_cap0.1 | test | overall | source_group_segment_median | source_group_art_general_ratio | 3099 | 0.450311 | 1.10247 | 3.21959 | 0.870834 | 0.325266 | 0.558245 |
| PP-H23 | h23_market_median_cap0.2 | test | overall | source_group_segment_median | source_group_market_ratio | 3099 | 0.450311 | 1.17704 | 3.21959 | 0.879418 | 0.349145 | 0.54566 |
| PP-H23 | h23_other_median_cap0.2 | test | overall | source_group_segment_median | source_group_other_ratio | 3099 | 0.450311 | 1.17704 | 3.21959 | 0.879418 | 0.349145 | 0.54566 |
| PP-H23 | h23_art_general_median_cap0.2 | test | overall | source_group_segment_median | source_group_art_general_ratio | 3099 | 0.457706 | 1.18023 | 3.21959 | 0.8873 | 0.316231 | 0.545015 |
| PP-H24 | h24_search_recent_result_ratio_median_cap0.1 | test | overall | recency_segment_median | search_recent_result_ratio | 3099 | 0.434889 | 0.991866 | 3.21959 | 0.852336 | 0.334301 | 0.571797 |
| PP-H24 | h24_is_recent_context_ratio_median_cap0.1 | test | overall | recency_segment_median | is_recent_context_ratio | 3099 | 0.434889 | 0.991866 | 3.21959 | 0.852336 | 0.334301 | 0.571797 |
| PP-H24 | h24_search_recent_result_ratio_median_cap0.2 | test | overall | recency_segment_median | search_recent_result_ratio | 3099 | 0.436746 | 0.957093 | 3.15419 | 0.850617 | 0.334947 | 0.569539 |
| PP-H24 | h24_is_recent_context_ratio_median_cap0.2 | test | overall | recency_segment_median | is_recent_context_ratio | 3099 | 0.436746 | 0.957093 | 3.15419 | 0.850617 | 0.334947 | 0.569539 |
| PP-H24 | pp_y2_base | test | overall | base |  | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |
| PP-H24 | h24_search_recent_result_count_median_cap0.1 | test | overall | recency_segment_median | search_recent_result_count | 3099 | 0.457856 | 1.09068 | 3.21959 | 0.869142 | 0.329784 | 0.549209 |
| PP-H24 | h24_search_recent_result_count_median_cap0.2 | test | overall | recency_segment_median | search_recent_result_count | 3099 | 0.46657 | 1.15737 | 3.21959 | 0.883975 | 0.324944 | 0.536947 |
| PP-H26 | h26_risk_action_median_cap0.1 | test | overall | risk_action_median | h26_action_segment | 3099 | 0.435175 | 1.00941 | 3.18215 | 0.857119 | 0.32817 | 0.565021 |
| PP-H26 | h26_risk_action_median_cap0.2 | test | overall | risk_action_median | h26_action_segment | 3099 | 0.435175 | 1.00941 | 3.18215 | 0.857119 | 0.32817 | 0.565021 |
| PP-H26 | h26_risk_qwidth_action_median_cap0.1 | test | overall | risk_qwidth_action_median | h26_qwidth_action_segment | 3099 | 0.435175 | 1.00941 | 3.18215 | 0.857119 | 0.32817 | 0.565021 |
| PP-H26 | h26_risk_qwidth_action_median_cap0.2 | test | overall | risk_qwidth_action_median | h26_qwidth_action_segment | 3099 | 0.435175 | 1.00941 | 3.18215 | 0.857119 | 0.32817 | 0.565021 |
| PP-H26 | pp_y2_base | test | overall | base |  | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |
| PP-H26 | h26_confidence_only_lower_q10_blend0.25 | test | overall | risk_quantile_blend | q10_log | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |
| PP-H26 | h26_confidence_only_lower_q10_blend0.5 | test | overall | risk_quantile_blend | q10_log | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |
| PP-H26 | h26_confidence_only_upper_q90_blend0.25 | test | overall | risk_quantile_blend | q90_log | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |
| PP-H26 | h26_confidence_only_upper_q90_blend0.5 | test | overall | risk_quantile_blend | q90_log | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |

## 위험 구간 결과

- 없음

## 수동 검수 우선순위 상위

| artist_search_name | validation_rows | validation_mdape | validation_mape | validation_p95_ape | recommended_action | qwidth_bin | search_quality_score | search_name_match_ratio | search_homonym_risk_ratio | source_total_count | source_group_gallery_museum_ratio | source_group_market_ratio | source_group_news_ratio | manual_review_priority_score | review_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 마르세르두차므프 | 1 | 14.2468 | 14.2468 | 14.2468 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.816667 | validation 큰 오차가 커서 보정 영향이 큼 |
| 정은아 | 3 | 11.0276 | 8.09456 | 11.3241 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.812798 | validation 큰 오차가 커서 보정 영향이 큼 |
| 강로사 | 16 | 4.97801 | 4.24744 | 7.20242 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.808929 | validation 큰 오차가 커서 보정 영향이 큼 |
| 후그 | 10 | 3.13693 | 3.52373 | 6.62156 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.799107 | validation 큰 오차가 커서 보정 영향이 큼 |
| 안아바 | 3 | 4.84167 | 4.95288 | 5.14594 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.797917 | validation 큰 오차가 커서 보정 영향이 큼 |
| 김도영 | 2 | 3.7535 | 3.7535 | 6.06766 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.797321 | validation 큰 오차가 커서 보정 영향이 큼 |
| 제로즈 | 5 | 4.51627 | 4.25024 | 4.79072 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.794048 | validation 큰 오차가 커서 보정 영향이 큼 |
| 김성우 | 3 | 2.50559 | 3.01246 | 4.02843 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.782738 | validation 큰 오차가 커서 보정 영향이 큼 |
| 최인아 | 1 | 3.30263 | 3.30263 | 3.30263 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.781548 | validation 큰 오차가 커서 보정 영향이 큼 |
| 하종훈 | 1 | 3.13215 | 3.13215 | 3.13215 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.77381 | validation 큰 오차가 커서 보정 영향이 큼 |
| 김기정 | 13 | 2.72838 | 2.13513 | 3.13141 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.76994 | validation 큰 오차가 커서 보정 영향이 큼 |
| 채동민 | 7 | 1.49886 | 2.2385 | 3.66577 | not_collected_by_h11_h12 | caution | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.768452 | validation 큰 오차가 커서 보정 영향이 큼 |
| 김영현 | 24 | 1.10184 | 2.15488 | 6.54379 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.766964 | validation 큰 오차가 커서 보정 영향이 큼 |
| 홍지우 | 7 | 2.25336 | 1.57448 | 3.11823 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.761607 | validation 큰 오차가 커서 보정 영향이 큼 |
| 이지효 | 1 | 2.47294 | 2.47294 | 2.47294 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.759821 | validation 큰 오차가 커서 보정 영향이 큼 |
| 백종석 | 1 | 2.42846 | 2.42846 | 2.42846 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.753571 | validation 큰 오차가 커서 보정 영향이 큼 |
| 김령아 | 10 | 1.54695 | 1.71782 | 2.68149 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.753274 | validation 큰 오차가 커서 보정 영향이 큼 |
| 박상수 | 11 | 1.04112 | 1.29558 | 3.13433 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.74494 | validation 큰 오차가 커서 보정 영향이 큼 |
| 이바아이우시트이 | 2 | 1.59029 | 1.59029 | 2.31527 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.744345 | validation 큰 오차가 커서 보정 영향이 큼 |
| 박수산 | 4 | 1.90772 | 1.86022 | 2.19273 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.73869 | validation 큰 오차가 커서 보정 영향이 큼 |
| 권선용 | 4 | 1.42479 | 1.53653 | 2.37959 | not_collected_by_h11_h12 | caution | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.73631 | validation 큰 오차가 커서 보정 영향이 큼 |
| 후이수현 | 6 | 1.47618 | 1.49196 | 2.00706 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.728869 | validation 큰 오차가 커서 보정 영향이 큼 |
| 노누리 | 10 | 0.957129 | 1.07384 | 2.45482 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.72619 | validation 큰 오차가 커서 보정 영향이 큼 |
| 김재원 | 2 | 1.15733 | 1.15733 | 1.84011 | not_collected_by_h11_h12 | caution | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.71756 | validation 큰 오차가 커서 보정 영향이 큼 |
| 신수정 | 2 | 1.55311 | 1.55311 | 1.67057 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.716667 | validation 큰 오차가 커서 보정 영향이 큼 |
| 이재희 | 19 | 1.11491 | 1.05219 | 1.78129 | not_collected_by_h11_h12 | caution | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.71131 | validation 큰 오차가 커서 보정 영향이 큼 |
| 강준쿠 | 2 | 1.44964 | 1.44964 | 1.54114 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.705952 | 작가명 매칭률이 낮아 동명이인/무관 결과 검수 필요 |
| 이준희 | 7 | 1.06795 | 1.28743 | 2.30326 | candidate_for_h14_h18 | risk | 0.4564 | 0.968 | 0.208 | 125 | 0.2 | 0.088 | 0.328 | 0.702886 | validation 큰 오차가 커서 보정 영향이 큼 |
| 한은미 | 10 | 1.19952 | 1.11586 | 1.46015 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.696726 | 작가명 매칭률이 낮아 동명이인/무관 결과 검수 필요 |
| 김다운 | 3 | 1.42512 | 1.42512 | 1.42512 | not_collected_by_h11_h12 | risk | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.690179 | 작가명 매칭률이 낮아 동명이인/무관 결과 검수 필요 |

## 해석

- PP-H20~H22는 현재 공식 API 키 또는 2개 이상 provider 결과가 없어 blocked 상태다.
- PP-H23/H24는 H11 HTML 폴백 데이터의 소스군/최근성 신호를 validation residual 보정에 사용한 제한 실험이다.
- PP-H26은 H12B에서 가장 위험한 `confidence_only_or_manual_review` 구간을 별도로 방어할 수 있는지 확인한다.
- 이 결과는 공식 Naver/Google 수집 후 재실행해야 최종 결론으로 사용할 수 있다.
