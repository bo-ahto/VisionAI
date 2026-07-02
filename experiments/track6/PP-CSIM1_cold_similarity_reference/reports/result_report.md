# Cold 유사작가/유사작품 비교군 피처 검증

- 작성일: 2026-06-18T14:53:27
- 목적: strict Cold에서 비슷한 작품, 비슷한 작가, 비슷한 작가의 비슷한 작품 기준가격 통계가 성능을 높이는지 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.
- 학습 행의 유사 비교군 통계는 KFold out-of-fold로 생성해 자기 가격 누수를 차단했다.
- validation/test의 유사 비교군 통계는 train 데이터만 기준으로 생성했다.

## 1. Test 결과
| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | n_features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_similarity_stats | test | 작품 유사 비교군 통계 추가 | 0.458500 | 1.167041 | 3.385369 | 0.897699 | 0.315908 | 0.539852 | 45 |
| user_meta_core_bucket | test | 작품+사용자 입력 작가 메타 bucket | 0.473483 | 1.100452 | 2.942330 | 0.887405 | 0.321071 | 0.527267 | 34 |
| artwork_only | test | 작품 정보만 | 0.489892 | 1.238691 | 4.117775 | 0.938639 | 0.293643 | 0.508228 | 12 |
| artist_artwork_similarity_stats | test | 작가 메타+작품 유사 비교군 통계 추가 | 0.526217 | 1.683167 | 7.388707 | 1.035963 | 0.277832 | 0.477251 | 56 |
| artist_meta_similarity_stats | test | 작가 메타 유사 비교군 통계 추가 | 0.547528 | 1.649842 | 8.832447 | 1.036608 | 0.280736 | 0.456276 | 45 |

## 2. Validation 결과
| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | n_features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| user_meta_core_bucket | validation | 작품+사용자 입력 작가 메타 bucket | 0.381784 | 0.552089 | 1.467202 | 0.654447 | 0.395568 | 0.627316 | 34 |
| artist_meta_similarity_stats | validation | 작가 메타 유사 비교군 통계 추가 | 0.385166 | 0.579645 | 1.551798 | 0.661283 | 0.388667 | 0.601526 | 45 |
| artwork_similarity_stats | validation | 작품 유사 비교군 통계 추가 | 0.404950 | 0.566857 | 1.528045 | 0.667428 | 0.375590 | 0.617871 | 45 |
| artist_artwork_similarity_stats | validation | 작가 메타+작품 유사 비교군 통계 추가 | 0.405569 | 0.586790 | 1.553460 | 0.677202 | 0.382855 | 0.594261 | 56 |
| artwork_only | validation | 작품 정보만 | 0.419155 | 0.683096 | 1.846274 | 0.694097 | 0.357792 | 0.602979 | 12 |

## 3. 해석

- test MdAPE 기준 최상위 후보는 `artwork_similarity_stats`이다.
- test p95/MAPE 안정성 기준 최상위 후보는 `user_meta_core_bucket`이다.
- `artwork_similarity_stats`는 입력 작품과 비슷한 train 작품들의 가격 분포를 추가한다.
- `artist_meta_similarity_stats`는 사용자가 입력 가능한 작가 메타가 비슷한 train 작가군의 가격 분포를 추가한다.
- `artist_artwork_similarity_stats`는 위 두 기준을 함께 넣은 후보로, 비슷한 작가의 비슷한 작품이라는 설명 가능한 Cold 기준가격 구조에 가장 가깝다.
- 이번 1차 실험에서는 작품 유사 비교군이 중앙 오차(MdAPE)는 낮췄지만, user_meta_core_bucket 대비 MAPE/p95/RMSE는 나빠졌다.
- 작가 메타 유사 비교군과 작가+작품 결합 유사 비교군은 tail이 크게 악화되어, 현재 방식 그대로는 운영 후보로 보기 어렵다.
- 따라서 현재 운영 후보는 user_meta_core_bucket을 유지하고, 유사작품 통계는 별도 보조 피처 또는 라우터 후보로 후속 검증하는 것이 맞다.
- 이 실험 결과가 좋더라도 동일 작가를 직접 찾은 성능이 아니라, strict Cold 조건에서 train 비교군을 검색해 만든 보조 통계 성능으로 해석해야 한다.