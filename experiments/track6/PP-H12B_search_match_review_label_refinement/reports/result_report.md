# PP-H12B 검색 결과 작가 일치 라벨 검수 초안 v2

## 목적

- H12 자동 라벨에서 검색 UI/프로필/결제 노이즈를 보수적으로 제거한다.
- 사람이 확정하기 전 사용할 수 있는 검수 초안 v2 작가 큐를 만든다.
- 이 결과 역시 최종 수동 검수 라벨은 아니며, H14/H18 재실행용 보수적 후보군이다.

## 실행 설정

| 항목 | 값 |
| --- | --- |
| experiment_id | PP-H12B |
| title | 검색 결과 작가 일치 라벨 검수 초안 v2 |
| run_id | pp_h12b_20260603_160549 |
| started_at | 2026-06-03T16:05:49 |
| finished_at | 2026-06-03T16:05:49 |
| input_result_labels | experiments/track6/PP-H12_search_match_disambiguation_review/outputs/search_result_auto_labels.csv |
| input_artist_queue | experiments/track6/PP-H12_search_match_disambiguation_review/outputs/artist_match_review_queue.csv |
| result_rows | 9259 |
| artist_rows | 80 |
| candidate_for_h14_h18_artist_n | 43 |
| note | Conservative draft labels only. Human review is still required for final acceptance. |

## 결과 라벨 분포

| review_label_draft | result_count |
| --- | --- |
| irrelevant | 4209 |
| match_artist | 4145 |
| homonym | 657 |
| partial_match | 126 |
| missing | 122 |

## 작가 라벨 분포

| auto_artist_label | artist_count |
| --- | --- |
| usable_match | 43 |
| low_match | 15 |
| weak_match | 11 |
| homonym_risk | 11 |

## 추천 액션 분포

| recommended_action | artist_count |
| --- | --- |
| candidate_for_h14_h18 | 43 |
| do_not_use_for_point_prediction | 15 |
| confidence_only_or_manual_review | 11 |
| manual_review_required | 11 |

## H14/H18 후보

| artist_search_name | auto_artist_label | recommended_action | artist_match_confidence | match_artist_count | partial_match_count | irrelevant_count | h11_search_quality_grade | total_row_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 박지은 | usable_match | candidate_for_h14_h18 | 0.66816 | 111 | 0 | 14 | medium | 73 |
| 박소연 | usable_match | candidate_for_h14_h18 | 0.60064 | 66 | 1 | 57 | medium | 74 |
| 김홍빈 | usable_match | candidate_for_h14_h18 | 0.59322 | 70 | 3 | 44 | medium | 96 |
| 김미아 | usable_match | candidate_for_h14_h18 | 0.56632 | 74 | 0 | 41 | low | 214 |
| 김승환 | usable_match | candidate_for_h14_h18 | 0.54512 | 70 | 0 | 34 | low | 139 |
| 김은미 | usable_match | candidate_for_h14_h18 | 0.544677 | 68 | 0 | 36 | low | 163 |
| 이경 | usable_match | candidate_for_h14_h18 | 0.54208 | 78 | 4 | 19 | low | 102 |
| 김현주 | usable_match | candidate_for_h14_h18 | 0.53584 | 66 | 1 | 38 | low | 276 |
| 김재현 | usable_match | candidate_for_h14_h18 | 0.53112 | 69 | 1 | 46 | low | 85 |
| 이준희 | usable_match | candidate_for_h14_h18 | 0.53024 | 63 | 8 | 44 | medium | 121 |
| 김선우 | usable_match | candidate_for_h14_h18 | 0.5292 | 71 | 0 | 45 | low | 105 |
| 김태일 | usable_match | candidate_for_h14_h18 | 0.523333 | 72 | 2 | 37 | low | 197 |
| 박영 | usable_match | candidate_for_h14_h18 | 0.50744 | 71 | 1 | 53 | medium | 186 |
| 김수현 | usable_match | candidate_for_h14_h18 | 0.4956 | 63 | 5 | 38 | low | 73 |
| 강선미 | usable_match | candidate_for_h14_h18 | 0.49344 | 71 | 0 | 54 | low | 132 |
| 김병관 | usable_match | candidate_for_h14_h18 | 0.48672 | 73 | 1 | 51 | medium | 152 |
| 홍미희 | usable_match | candidate_for_h14_h18 | 0.481951 | 67 | 5 | 51 | medium | 108 |
| 최승윤 | usable_match | candidate_for_h14_h18 | 0.47736 | 72 | 0 | 52 | medium | 163 |
| 배준성 | usable_match | candidate_for_h14_h18 | 0.47448 | 73 | 1 | 51 | low | 102 |
| 김홍식 | usable_match | candidate_for_h14_h18 | 0.47424 | 70 | 0 | 54 | low | 103 |

## 검수/제외 후보

| artist_search_name | auto_artist_label | recommended_action | artist_match_confidence | match_artist_count | partial_match_count | irrelevant_count | h11_search_quality_grade | total_row_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 이혜라 | weak_match | confidence_only_or_manual_review | 0.413967 | 60 | 3 | 57 | low | 699 |
| 카이 액스 | homonym_risk | manual_review_required | 0.07 | 0 | 0 | 69 | low | 366 |
| 고병준 | weak_match | confidence_only_or_manual_review | 0.317257 | 41 | 1 | 65 | low | 346 |
| 서은혜 | weak_match | confidence_only_or_manual_review | 0.371855 | 58 | 2 | 64 | low | 278 |
| 임철희 | weak_match | confidence_only_or_manual_review | 0.439661 | 53 | 6 | 57 | low | 274 |
| 김레이시 | weak_match | confidence_only_or_manual_review | 0.387619 | 45 | 3 | 54 | low | 256 |
| 박한지 | weak_match | confidence_only_or_manual_review | 0.399835 | 60 | 0 | 60 | low | 255 |
| 아이비 아이브스 | homonym_risk | manual_review_required | 0.0742553 | 0 | 0 | 49 | low | 232 |
| 김카리스 | low_match | do_not_use_for_point_prediction | 0.169744 | 0 | 8 | 100 | low | 218 |
| 김영옥 | homonym_risk | manual_review_required | 0.45384 | 62 | 0 | 29 | low | 217 |
| 유진나 | low_match | do_not_use_for_point_prediction | 0.0472 | 3 | 0 | 61 | low | 215 |
| 박중현 | homonym_risk | manual_review_required | 0.454628 | 61 | 1 | 20 | low | 199 |
| 홍정우 | homonym_risk | manual_review_required | 0.501951 | 70 | 0 | 12 | low | 172 |
| 이효윤 | low_match | do_not_use_for_point_prediction | 0.157778 | 15 | 0 | 77 | low | 158 |
| 임최느 | low_match | do_not_use_for_point_prediction | 0.00892308 | 0 | 0 | 47 | low | 157 |
| 윤주 | homonym_risk | manual_review_required | 0.4624 | 65 | 1 | 19 | low | 153 |
| 권아이 | low_match | do_not_use_for_point_prediction | 0.0249231 | 0 | 0 | 50 | low | 129 |
| 김훈정 | low_match | do_not_use_for_point_prediction | 0.278704 | 37 | 0 | 67 | low | 129 |
| 이리디아 | low_match | do_not_use_for_point_prediction | 0.1965 | 1 | 4 | 113 | low | 121 |
| 황오철 | low_match | do_not_use_for_point_prediction | 0.0391429 | 1 | 0 | 58 | low | 120 |

## Metrics

| experiment_id | candidate | scope | n | match_artist_rate | partial_match_rate | homonym_rate | irrelevant_rate | mean_confidence | usable_match_rate | weak_match_rate | low_match_rate | homonym_risk_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H12B | result_label_draft_distribution | search_result | 9259 | 0.447673 | 0.0136084 | 0.070958 | 0.454585 | 0.408355 |  |  |  |  |
| PP-H12B | artist_label_draft_distribution | artist | 80 |  |  |  |  | 0.390469 | 0.5375 | 0.1375 | 0.1875 | 0.1375 |
