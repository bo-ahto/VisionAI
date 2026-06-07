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
| collector_run_id | pp_h11_20260603_164345 |
| run_started_at | 2026-06-03T16:43:45 |
| run_finished_at | 2026-06-03T16:56:57 |
| seconds | 791.34 |
| seed | 20260602 |
| snapshot_month | 2026-06 |
| selection_policy | test_frequency |
| artist_scope | warm |
| limit_artists | 210 |
| selected_artist_n | 210 |
| snapshot_artist_n | 428 |
| providers | python_ddg, python_ddg_art_context |
| query_templates | name_artist_ko, name_artwork_ko, name_exhibition_ko, name_gallery_ko, name_auction_ko |
| merge_with_latest | True |
| replace_latest_providers | False |
| drop_latest_providers |  |
| max_results_per_query | 5 |
| sleep_seconds | 0.15 |
| timeout | 12 |
| latest_snapshot_path | data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv |
| note | Use naver_api_blog/naver_api_news/naver_api_webkr when NAVER_CLIENT_ID/NAVER_CLIENT_SECRET are present. Use python_ddg/python_ddg_art_context as reusable no-key library providers. python_ddg_art_domains is a stricter diagnostic provider and may be sparse. google_cse requires GOOGLE_API_KEY/GOOGLE_CSE_ID but may be unavailable for new Google projects. HTML providers remain pilot fallbacks. |

## 전체 수집 품질

| experiment_id | candidate | split | policy | artist_n | provider_n | query_template_n | max_results_per_query | request_n | request_success_rate | request_error_rate | artist_success_rate | quality_high_rate | quality_medium_rate | quality_low_rate | quality_missing_rate | homonym_risk_rate | avg_result_count_per_artist | avg_unique_domain_per_artist | avg_quality_score | art_context_ratio_mean | exhibition_ratio_mean | market_ratio_mean | name_match_ratio_mean | source_group | source_group_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H11 | operational_search_collection_standardization | collection | artist_level_periodic_collection | 428 | 5 | 5 | 5 | 5480 | 0.977737 | 0 | 1 | 0 | 0.0280374 | 0.971963 | 0 | 0.088785 | 71.9346 | 27.9042 | 0.197744 | 0.190302 | 0.0595789 | 0.0221496 | 0.27377 |  |  |

## 품질 등급 분포

| grade | artist_count |
| --- | --- |
| low | 416 |
| medium | 12 |

## 동명이인 위험 분포

| homonym_risk | artist_count |
| --- | --- |
| clear | 354 |
| risk | 38 |
| watch | 36 |

## 품질 상위 샘플

| artist_search_name | search_quality_grade | search_homonym_risk_grade | search_quality_score | search_result_count | search_art_match_ratio | search_name_match_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 송수정 | medium | clear | 0.69 | 50 | 0.8 | 1 |
| 권예주 | medium | clear | 0.665 | 50 | 0.82 | 1 |
| 서경희 | medium | clear | 0.62 | 50 | 1 | 1 |
| 이우환 | medium | clear | 0.61 | 50 | 1 | 1 |
| 정현숙 | medium | watch | 0.584 | 50 | 1 | 1 |
| 유재연 | medium | clear | 0.57 | 50 | 0.6 | 1 |
| 박지은 | medium | clear | 0.5684 | 125 | 0.824 | 0.968 |
| 김홍빈 | medium | clear | 0.49918 | 122 | 0.647541 | 0.901639 |
| 박소연 | medium | clear | 0.4648 | 125 | 0.576 | 0.968 |
| 이준희 | medium | watch | 0.4564 | 125 | 0.648 | 0.968 |
| 양지훈 | medium | clear | 0.455328 | 122 | 0.622951 | 0.57377 |
| 갤러리 헥사곤 | medium | clear | 0.452362 | 127 | 0.968504 | 0 |

## 품질 하위 샘플

| artist_search_name | search_quality_grade | search_homonym_risk_grade | search_quality_score | search_result_count | search_art_match_ratio | search_name_match_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 유선 | low | risk | 0 | 50 | 0 | 1 |
| 이계진 | low | risk | 0 | 50 | 0 | 1 |
| 강유정 | low | risk | 0 | 50 | 0 | 1 |
| 김영란 | low | risk | 0 | 50 | 0 | 1 |
| 전미선 | low | risk | 0 | 50 | 0.2 | 1 |
| 이연후이 | low | risk | 0 | 50 | 0 | 0 |
| 조조 아나빔 | low | risk | 0 | 50 | 0 | 0 |
| 김윤경 | low | risk | 0.01 | 50 | 0 | 1 |
| 이지연 | low | risk | 0.02 | 50 | 0 | 1 |
| 송유정 | low | risk | 0.02 | 50 | 0 | 1 |
| 김보민 | low | risk | 0.026 | 50 | 0.08 | 0.98 |
| 서예지 | low | risk | 0.04 | 50 | 0 | 0.8 |

## 원본 결과 샘플

| artist_search_name | provider | query_template_id | rank | title | domain | source_group |
| --- | --- | --- | --- | --- | --- | --- |
| 강달예 | python_ddg | name_artist_ko | 1 | 租房子常说的多少pw, 那个pw 究竟是什么意思？ - 知乎 | zhihu.com | other |
| 강달예 | python_ddg | name_artist_ko | 2 | pw是啥？pw是什么意思？ - 知乎 | zhihu.com | other |
| 강달예 | python_ddg | name_artist_ko | 3 | 票务和代拍哪个更靠谱？ - 知乎 | zhihu.com | other |
| 강달예 | python_ddg | name_artist_ko | 4 | 如何评价航发三巨头的自适应变循环（GE）、齿轮传动箱（PW）、三转子（RR）技术… | zhihu.com | other |
| 강달예 | python_ddg | name_artist_ko | 5 | 派克笔上的PP标/PW标分别有什么含义？ - 知乎 | zhihu.com | other |
| 강달예 | python_ddg | name_artwork_ko | 1 | Instagram | instagram.com | social_blog |
| 강달예 | python_ddg | name_artwork_ko | 2 | Instagram | instagram.com | social_blog |
| 강달예 | python_ddg | name_artwork_ko | 3 | Instagram | instagram.com | social_blog |
| 강달예 | python_ddg | name_artwork_ko | 4 | Instagram | instagram.com | social_blog |
| 강달예 | python_ddg | name_artwork_ko | 5 | Instagram | instagram.com | social_blog |
| 강달예 | python_ddg | name_auction_ko | 1 | Create a Gmail account - Gmail Help - Google Help | support.google.com | other |
| 강달예 | python_ddg | name_auction_ko | 2 | Sign in to Gmail | support.google.com | other |
| 강달예 | python_ddg | name_auction_ko | 3 | Gmail Help - Google Help | support.google.com | other |
| 강달예 | python_ddg | name_auction_ko | 4 | Sign in to Gmail - Computer - Gmail Help - Google Help | support.google.com | other |
| 강달예 | python_ddg | name_auction_ko | 5 | Create a Google Account - Computer - Google Account Help | support.google.com | other |
| 강달예 | python_ddg | name_exhibition_ko | 1 | YouTube Help - Google Help | support.google.com | social_blog |
| 강달예 | python_ddg | name_exhibition_ko | 2 | 如何在中国大陆用「合法」的方式观看到youtube上面的「有价值」的视频？ - 知乎 | zhihu.com | social_blog |
| 강달예 | python_ddg | name_exhibition_ko | 3 | YouTube Help - Google Help | support.google.com | social_blog |
| 강달예 | python_ddg | name_exhibition_ko | 4 | Verify your YouTube account - YouTube Help - Google Help | support.google.com | social_blog |
| 강달예 | python_ddg | name_exhibition_ko | 5 | YouTube帮助 - Google Help | support.google.com | social_blog |
| 강달예 | python_ddg | name_gallery_ko | 1 | CA – ぬきスト | xn--w8j1cxl6b.com | other |
| 강달예 | python_ddg | name_gallery_ko | 2 | CAのエロ動画（AV/DVD/無料動画）・オススメ作品まとめ ... | osusume.dmm.co.jp | other |
| 강달예 | python_ddg | name_gallery_ko | 3 | エアホステスAVをオンラインで見る - Jable.TV \| オンラインで無料 ... | jp.jable.tv | art_general |
| 강달예 | python_ddg | name_gallery_ko | 4 | ぬきスト 無料エロ動画まとめ - ODir | odir.us | other |
| 강달예 | python_ddg | name_gallery_ko | 5 | デビュー作品のCA AV・エロ動画 厳選37作品 - グラビアfit | gravurefit.com | other |
| 강달예 | python_ddg_art_context | name_artist_ko | 1 | ‎Google Gemini | gemini.google.com | other |
| 강달예 | python_ddg_art_context | name_artist_ko | 2 | ‎Google Gemini | gemini.google.com | other |
| 강달예 | python_ddg_art_context | name_artist_ko | 3 | ‎Google Gemini | gemini.google.com | other |
| 강달예 | python_ddg_art_context | name_artist_ko | 4 | ‎Google Gemini | gemini.google.com | other |
| 강달예 | python_ddg_art_context | name_artist_ko | 5 | ‎Google Gemini | gemini.google.com | other |

## 해석

- H11의 합격 기준은 단순 검색 성공률이 아니라 `high/medium` 등급 비율과 동명이인 위험률이다.
- `low` 또는 `risk` 등급 작가는 가격점 예측 피처로 직접 쓰기보다, 신뢰도 하향/가격 범위 확대/수동 검수 대상으로 사용해야 한다.
- 동일 스키마로 월 단위 스냅샷을 누적하면 검색 인지도 변화량, 최근 전시 노출, 출처 다양성 변화까지 후속 실험 피처로 만들 수 있다.
