# PP-H11 운영형 작가 검색 피처 표준화 수집 검증

## 목적

- 외부 검색 결과를 운영에서 반복 수집 가능한 형태로 표준화할 수 있는지 검증한다.
- 가격 예측 모델에는 검색 결과 원문을 직접 넣지 않고, 작가 단위 품질 점수와 문맥 비율로 변환한 스냅샷만 사용한다.
- 이번 실행은 기존 PP-H7~H10 파일을 덮어쓰지 않고 별도 운영형 경로에 산출물을 생성한다.

## 실행 설정

| 항목 | 값 |
| --- | --- |
| experiment_id | PP-H11 |
| title | 운영형 작가 검색 피처 표준화 수집 검증 |
| collector_run_id | pp_h11_20260618_101143 |
| run_started_at | 2026-06-18T10:11:43 |
| run_finished_at | 2026-06-18T10:11:44 |
| seconds | 1.63 |
| seed | 20260602 |
| snapshot_month | 2026-06-live-smoke |
| selection_policy | test_frequency |
| artist_scope | cold |
| limit_artists | 3 |
| selected_artist_n | 3 |
| snapshot_artist_n | 3 |
| providers | python_ddg_art_context |
| query_templates | name_artist_ko, name_exhibition_ko |
| merge_with_latest | False |
| replace_latest_providers | False |
| drop_latest_providers |  |
| max_results_per_query | 3 |
| sleep_seconds | 0 |
| timeout | 10 |
| latest_snapshot_path | data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv |
| note | Use naver_api_blog/naver_api_news/naver_api_webkr when NAVER_CLIENT_ID/NAVER_CLIENT_SECRET are present. Use python_ddg/python_ddg_art_context as reusable no-key library providers. python_ddg_art_domains is a stricter diagnostic provider and may be sparse. google_cse requires GOOGLE_API_KEY/GOOGLE_CSE_ID but may be unavailable for new Google projects. HTML providers remain pilot fallbacks. |

## 전체 수집 품질

| experiment_id | candidate | split | policy | artist_n | provider_n | query_template_n | max_results_per_query | request_n | request_success_rate | request_error_rate | artist_success_rate | quality_high_rate | quality_medium_rate | quality_low_rate | quality_missing_rate | homonym_risk_rate | avg_result_count_per_artist | avg_unique_domain_per_artist | avg_quality_score | art_context_ratio_mean | exhibition_ratio_mean | market_ratio_mean | name_match_ratio_mean | source_group | source_group_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H11 | operational_search_collection_standardization | collection | artist_level_periodic_collection | 3 | 1 | 2 | 3 | 6 | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0.333333 | 4 | 3 | 0.122222 | 0.0555556 | 0 | 0 | 0.666667 |  |  |

## 품질 등급 분포

| grade | artist_count |
| --- | --- |
| low | 3 |

## 동명이인 위험 분포

| homonym_risk | artist_count |
| --- | --- |
| clear | 1 |
| risk | 1 |
| watch | 1 |

## 품질 상위 샘플

| artist_search_name | search_quality_grade | search_homonym_risk_grade | search_quality_score | search_result_count | search_art_match_ratio | search_name_match_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 이준희 | low | watch | 0.2 | 3 | 0 | 1 |
| 임미량 | low | clear | 0.166667 | 6 | 0.166667 | 0 |
| 윤주 | low | risk | 5.55112e-17 | 3 | 0 | 1 |

## 품질 하위 샘플

| artist_search_name | search_quality_grade | search_homonym_risk_grade | search_quality_score | search_result_count | search_art_match_ratio | search_name_match_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 윤주 | low | risk | 5.55112e-17 | 3 | 0 | 1 |
| 임미량 | low | clear | 0.166667 | 6 | 0.166667 | 0 |
| 이준희 | low | watch | 0.2 | 3 | 0 | 1 |

## 원본 결과 샘플

| artist_search_name | provider | query_template_id | rank | title | domain | source_group |
| --- | --- | --- | --- | --- | --- | --- |
| 윤주 | python_ddg_art_context | name_artist_ko | 1 | 윤주 (배우) - 위키백과, 우리 모두의 백과사전 | ko.wikipedia.org | other |
| 윤주 | python_ddg_art_context | name_artist_ko | 2 | 윤주(배우) - 나무위키 | namu.wiki | other |
| 윤주 | python_ddg_art_context | name_artist_ko | 3 | 배우 윤주, 간이식 후 회복 근황 "기적 선물받은지 4년…고마운 ... | news.nate.com | news |
| 윤주 | python_ddg_art_context | name_exhibition_ko | 1 | 윤주 (배우) - 위키백과, 우리 모두의 백과사전 | ko.wikipedia.org | other |
| 윤주 | python_ddg_art_context | name_exhibition_ko | 2 | 윤주(배우) - 나무위키 | namu.wiki | other |
| 윤주 | python_ddg_art_context | name_exhibition_ko | 3 | 배우 윤주, 간이식 후 회복 근황 "기적 선물받은지 4년…고마운 ... | news.nate.com | news |
| 이준희 | python_ddg_art_context | name_artist_ko | 1 | 이준희 - 나무위키 | namu.wiki | other |
| 이준희 | python_ddg_art_context | name_artist_ko | 2 | 이준희 (농구선수) - 나무위키 | namu.wiki | other |
| 이준희 | python_ddg_art_context | name_artist_ko | 3 | 이준희 (씨름인) - 위키백과, 우리 모두의 백과사전 | ko.wikipedia.org | other |
| 이준희 | python_ddg_art_context | name_exhibition_ko | 1 | 이준희 - 나무위키 | namu.wiki | other |
| 이준희 | python_ddg_art_context | name_exhibition_ko | 2 | 이준희 (농구선수) - 나무위키 | namu.wiki | other |
| 이준희 | python_ddg_art_context | name_exhibition_ko | 3 | 이준희 (씨름인) - 위키백과, 우리 모두의 백과사전 | ko.wikipedia.org | other |
| 임미량 | python_ddg_art_context | name_artist_ko | 1 | 画像背景除去ツール - iLoveIMG | iloveimg.com | other |
| 임미량 | python_ddg_art_context | name_artist_ko | 2 | 画像背景 透過・透明（一部、部分的に透明にできます） \| 無料 ... | bannerkoubou.com | other |
| 임미량 | python_ddg_art_context | name_artist_ko | 3 | WEBブラウザ上で簡単に透過PNG画像を作成できるツール \| 無料 ... | peko-step.com | other |
| 임미량 | python_ddg_art_context | name_exhibition_ko | 1 | Roblox | roblox.com | other |
| 임미량 | python_ddg_art_context | name_exhibition_ko | 2 | Log in to Roblox | roblox.com | other |
| 임미량 | python_ddg_art_context | name_exhibition_ko | 3 | Download Roblox | roblox.com | art_general |

## 해석

- H11의 합격 기준은 단순 검색 성공률이 아니라 `high/medium` 등급 비율과 동명이인 위험률이다.
- `low` 또는 `risk` 등급 작가는 가격점 예측 피처로 직접 쓰기보다, 신뢰도 하향/가격 범위 확대/수동 검수 대상으로 사용해야 한다.
- 동일 스키마로 월 단위 스냅샷을 누적하면 검색 인지도 변화량, 최근 전시 노출, 출처 다양성 변화까지 후속 실험 피처로 만들 수 있다.
