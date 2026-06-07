# PP-H12 검색 결과 작가 일치/동명이인 판정 검수

## 목적

- PP-H11에서 수집한 검색 결과가 해당 작가 본인과 관련 있는지 자동 판정 초안을 만든다.
- 사람이 검수할 우선순위 큐를 생성해 H13/H14/H18에서 검색 피처를 안전하게 쓸 수 있는 기준을 만든다.
- 이 결과는 최종 정답 라벨이 아니라 `수동 검수 전 1차 판정`이다.

## 실행 설정

| 항목 | 값 |
| --- | --- |
| experiment_id | PP-H12 |
| title | 검색 결과 작가 일치/동명이인 판정 검수 |
| run_id | pp_h12_20260603_160528 |
| started_at | 2026-06-03T16:05:27 |
| finished_at | 2026-06-03T16:05:28 |
| input_snapshot | data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv |
| input_standardized | data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv |
| result_rows | 9259 |
| artist_rows | 80 |
| manual_review_rows | 240 |
| candidate_for_h14_h18_artist_n | 42 |
| manual_or_reject_artist_n | 38 |
| note | Automatic triage only. Fill manual_label before using as final artist-match ground truth. |

## 결과 단위 자동 라벨 분포

| auto_result_label | result_count |
| --- | --- |
| match_artist | 4190 |
| irrelevant | 3129 |
| partial_match | 1157 |
| homonym | 661 |
| missing | 122 |

## 작가 단위 자동 라벨 분포

| auto_artist_label | artist_count |
| --- | --- |
| usable_match | 42 |
| low_match | 17 |
| homonym_risk | 11 |
| weak_match | 10 |

## 추천 액션 분포

| recommended_action | artist_count |
| --- | --- |
| candidate_for_h14_h18 | 42 |
| do_not_use_for_point_prediction | 17 |
| manual_review_required | 11 |
| confidence_only_or_manual_review | 10 |

## 검수 우선순위 분포

| manual_review_priority | artist_count |
| --- | --- |
| P3_spot_check | 42 |
| P2_low_match | 17 |
| P0_homonym | 11 |
| P1_weak_match | 10 |

## H14/H18 후보 작가 상위

| artist_search_name | auto_artist_label | recommended_action | artist_match_confidence | match_artist_count | partial_match_count | irrelevant_count | h11_search_quality_grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 박지은 | usable_match | candidate_for_h14_h18 | 0.661584 | 111 | 14 | 0 | medium |
| 김홍빈 | usable_match | candidate_for_h14_h18 | 0.579859 | 70 | 40 | 7 | medium |
| 박소연 | usable_match | candidate_for_h14_h18 | 0.569892 | 66 | 56 | 2 | medium |
| 김소정 | homonym_risk | manual_review_required | 0.54614 | 73 | 22 | 0 | low |
| 김미아 | usable_match | candidate_for_h14_h18 | 0.54192 | 74 | 31 | 10 | low |
| 김재현 | usable_match | candidate_for_h14_h18 | 0.53484 | 69 | 23 | 24 | low |
| 이경 | usable_match | candidate_for_h14_h18 | 0.534492 | 78 | 21 | 2 | low |
| 이준희 | usable_match | candidate_for_h14_h18 | 0.529356 | 69 | 42 | 4 | medium |
| 김은미 | usable_match | candidate_for_h14_h18 | 0.529089 | 68 | 36 | 0 | low |
| 김승환 | usable_match | candidate_for_h14_h18 | 0.528208 | 70 | 32 | 2 | low |
| 박영 | usable_match | candidate_for_h14_h18 | 0.523104 | 72 | 3 | 50 | medium |
| 김선우 | usable_match | candidate_for_h14_h18 | 0.520756 | 71 | 31 | 14 | low |
| 김현주 | usable_match | candidate_for_h14_h18 | 0.520152 | 67 | 38 | 0 | low |
| 김태일 | usable_match | candidate_for_h14_h18 | 0.517679 | 74 | 33 | 4 | low |
| 강선미 | usable_match | candidate_for_h14_h18 | 0.510176 | 71 | 3 | 51 | low |

## 검수 필요 작가 상위

| artist_search_name | auto_artist_label | recommended_action | artist_match_confidence | match_artist_count | partial_match_count | irrelevant_count | h11_search_quality_grade | total_row_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 이혜라 | weak_match | confidence_only_or_manual_review | 0.434442 | 63 | 2 | 55 | low | 699 |
| 카이 액스 | homonym_risk | manual_review_required | 0.122303 | 0 | 17 | 52 | low | 366 |
| 고병준 | low_match | do_not_use_for_point_prediction | 0.352631 | 41 | 9 | 57 | low | 346 |
| 서은혜 | weak_match | confidence_only_or_manual_review | 0.400935 | 59 | 7 | 58 | low | 278 |
| 김레이시 | low_match | do_not_use_for_point_prediction | 0.43151 | 45 | 4 | 53 | low | 256 |
| 박한지 | weak_match | confidence_only_or_manual_review | 0.426496 | 60 | 8 | 52 | low | 255 |
| 김태 | weak_match | confidence_only_or_manual_review | 0.449796 | 68 | 5 | 51 | low | 249 |
| 아이비 아이브스 | homonym_risk | manual_review_required | 0.105817 | 0 | 18 | 31 | low | 232 |
| 김카리스 | low_match | do_not_use_for_point_prediction | 0.274667 | 0 | 43 | 65 | low | 218 |
| 김영옥 | homonym_risk | manual_review_required | 0.459944 | 62 | 20 | 9 | low | 217 |
| 유진나 | low_match | do_not_use_for_point_prediction | 0.104121 | 3 | 0 | 61 | low | 215 |
| 박중현 | homonym_risk | manual_review_required | 0.455942 | 62 | 17 | 2 | low | 199 |
| 홍정우 | homonym_risk | manual_review_required | 0.493801 | 70 | 12 | 0 | low | 172 |
| 이효윤 | low_match | do_not_use_for_point_prediction | 0.205672 | 15 | 12 | 65 | low | 158 |
| 임최느 | low_match | do_not_use_for_point_prediction | 0.04059 | 0 | 0 | 47 | low | 157 |
| 윤주 | homonym_risk | manual_review_required | 0.46408 | 65 | 17 | 3 | low | 153 |
| 권아이 | low_match | do_not_use_for_point_prediction | 0.082951 | 0 | 1 | 49 | low | 129 |
| 김훈정 | low_match | do_not_use_for_point_prediction | 0.3141 | 37 | 5 | 62 | low | 129 |
| 이리디아 | low_match | do_not_use_for_point_prediction | 0.281154 | 1 | 52 | 65 | low | 121 |
| 황오철 | low_match | do_not_use_for_point_prediction | 0.096822 | 1 | 0 | 58 | low | 120 |

## 해석

- `candidate_for_h14_h18`는 검색 결과를 가격점 예측에 바로 넣는다는 뜻이 아니라, 신뢰도/가격 범위/q-width 보정 실험에 사용할 수 있는 후보라는 뜻이다.
- `confidence_only_or_manual_review`는 검색 신호가 일부 있으나 작가 본인 여부를 사람이 확인해야 한다.
- `do_not_use_for_point_prediction`은 검색 결과가 있더라도 모델 점 예측 피처로 직접 쓰면 노이즈가 될 가능성이 크다.
- 다음 단계는 manual review template의 `manual_label`을 채운 뒤 threshold를 다시 보정하는 것이다.
