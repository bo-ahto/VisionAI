# Cold 사용자 입력 작가 메타 전용 재선정

- 작성일: 2026-06-18T10:43:45
- strict Cold 조건: `artist_key`, 같은 작가 가격 통계, `artist_key` lookup 후처리, `search_*` 피처 미사용.
- 목적: 외부 live 검색을 보류한 상태에서 사용자 입력 가능 작가 메타와 작품 정보만으로 쓸 Cold 후보를 재선정한다.
- validation 선택 base 후보: `existing_meta_full`
- test 기준 최상위 후보: `manual_profile_context_bucket`

## Test 결과
| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | n_features | feature_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| manual_profile_context_bucket | test | strict_user_meta_lgbq_base_q50 | 0.449483 | 1.130719 | 3.991237 | 0.892919 | 68 | 작품+사용자 입력 작가 메타+전시/갤러리 문맥+bucket |
| manual_profile_context | test | strict_user_meta_lgbq_base_q50 | 0.450695 | 1.107179 | 3.723805 | 0.885102 | 56 | 작품+사용자 입력 작가 메타+전시/갤러리 문맥 |
| user_meta_core_bucket | test | strict_user_meta_lgbq_base_q50 | 0.461481 | 1.126798 | 3.089863 | 0.894627 | 34 | 작품+사용자 입력 core 작가 메타+메타 bucket |
| user_meta_core_bucket_lgb_residual_clip | test | strict_user_meta_lgb_residual_clip | 0.466889 | 1.132662 | 3.165992 | 0.894758 | 37 | 작품+사용자 입력 core 작가 메타+메타 bucket |
| user_meta_core | test | strict_user_meta_lgbq_base_q50 | 0.469394 | 1.142682 | 3.072416 | 0.896604 | 26 | 작품+사용자 입력 core 작가 메타 |
| existing_meta_full_lgb_residual_clip | test | strict_user_meta_lgb_residual_clip | 0.473913 | 1.071422 | 3.111251 | 0.886653 | 35 | 작품+기존 작가 메타 전체 |
| user_meta_core_bucket_search_free_guard_q40 | test | strict_user_meta_search_free_guard_q40 | 0.475173 | 1.110410 | 3.026130 | 0.906090 | 34 | 작품+사용자 입력 core 작가 메타+메타 bucket |
| existing_meta_full_bucket | test | strict_user_meta_lgbq_base_q50 | 0.475252 | 1.067990 | 2.961438 | 0.885385 | 40 | 작품+기존 작가 메타 전체+메타 bucket |
| existing_meta_full | test | strict_user_meta_lgbq_base_q50 | 0.477150 | 1.081916 | 3.030531 | 0.890215 | 32 | 작품+기존 작가 메타 전체 |
| artwork_only | test | strict_user_meta_lgbq_base_q50 | 0.482312 | 1.242417 | 4.380572 | 0.941084 | 12 | 작품 정보만 |
| existing_meta_full_search_free_guard_q40 | test | strict_user_meta_search_free_guard_q40 | 0.488231 | 1.062018 | 2.829233 | 0.905488 | 32 | 작품+기존 작가 메타 전체 |

## Validation 결과
| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | n_features | feature_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| existing_meta_full_lgb_residual_clip | validation | strict_user_meta_lgb_residual_clip | 0.370536 | 0.542916 | 1.420557 | 0.660408 | 35 | 작품+기존 작가 메타 전체 |
| existing_meta_full_search_free_guard_q40 | validation | strict_user_meta_search_free_guard_q40 | 0.379313 | 0.508713 | 1.268693 | 0.657339 | 32 | 작품+기존 작가 메타 전체 |
| existing_meta_full | validation | strict_user_meta_lgbq_base_q50 | 0.382133 | 0.547061 | 1.453648 | 0.657704 | 32 | 작품+기존 작가 메타 전체 |
| manual_profile_context_bucket | validation | strict_user_meta_lgbq_base_q50 | 0.382540 | 0.572403 | 1.589028 | 0.646370 | 68 | 작품+사용자 입력 작가 메타+전시/갤러리 문맥+bucket |
| existing_meta_full_bucket | validation | strict_user_meta_lgbq_base_q50 | 0.385229 | 0.549168 | 1.443994 | 0.656607 | 40 | 작품+기존 작가 메타 전체+메타 bucket |
| manual_profile_context | validation | strict_user_meta_lgbq_base_q50 | 0.386259 | 0.581437 | 1.539144 | 0.653787 | 56 | 작품+사용자 입력 작가 메타+전시/갤러리 문맥 |
| user_meta_core_bucket_search_free_guard_q40 | validation | strict_user_meta_search_free_guard_q40 | 0.389634 | 0.528364 | 1.368703 | 0.658603 | 34 | 작품+사용자 입력 core 작가 메타+메타 bucket |
| user_meta_core_bucket_lgb_residual_clip | validation | strict_user_meta_lgb_residual_clip | 0.390760 | 0.550086 | 1.413565 | 0.659523 | 37 | 작품+사용자 입력 core 작가 메타+메타 bucket |
| user_meta_core_bucket | validation | strict_user_meta_lgbq_base_q50 | 0.392975 | 0.555096 | 1.422948 | 0.658183 | 34 | 작품+사용자 입력 core 작가 메타+메타 bucket |
| user_meta_core | validation | strict_user_meta_lgbq_base_q50 | 0.394259 | 0.561216 | 1.472625 | 0.666531 | 26 | 작품+사용자 입력 core 작가 메타 |
| artwork_only | validation | strict_user_meta_lgbq_base_q50 | 0.396190 | 0.663304 | 1.791011 | 0.678909 | 12 | 작품 정보만 |

## 후보별 피처 설계
| candidate | model | loss_or_objective | n_features | feature_strategy | hypothesis |
| --- | --- | --- | --- | --- | --- |
| artwork_only | lightgbm | quantile_q10_q50_q90 | 12 | 작품 정보만 | 사용자 작가 메타가 없을 때의 기준 |
| user_meta_core | lightgbm | quantile_q10_q50_q90 | 26 | 작품+사용자 입력 core 작가 메타 | 운영 입력 가능성이 높은 작가 메타 효과 |
| user_meta_core_bucket | lightgbm | quantile_q10_q50_q90 | 34 | 작품+사용자 입력 core 작가 메타+메타 bucket | 작가 메타를 구간화해 안정화 |
| existing_meta_full | lightgbm | quantile_q10_q50_q90 | 32 | 작품+기존 작가 메타 전체 | 기존 메타 전체를 search 없이 사용한 참고 후보 |
| existing_meta_full_bucket | lightgbm | quantile_q10_q50_q90 | 40 | 작품+기존 작가 메타 전체+메타 bucket | 기존 메타 전체 구간화 참고 후보 |
| manual_profile_context | lightgbm | quantile_q10_q50_q90 | 56 | 작품+사용자 입력 작가 메타+전시/갤러리 문맥 | 사용자가 알고 있는 전시/갤러리 정보까지 입력할 때의 후보 |
| manual_profile_context_bucket | lightgbm | quantile_q10_q50_q90 | 68 | 작품+사용자 입력 작가 메타+전시/갤러리 문맥+bucket | 전시/갤러리와 작가 메타 구간화 후보 |
| existing_meta_full_lgb_residual_clip | lightgbm_quantile_plus_lgb_residual | q50_plus_regression_l1_residual | 35 | 작품+기존 작가 메타 전체 | 기존 메타 전체를 search 없이 사용한 참고 후보; search 없는 residual 보정 |
| existing_meta_full_search_free_guard_q40 | lightgbm_quantile_guard_only | q50_or_q40_guard | 32 | 작품+기존 작가 메타 전체 | 기존 메타 전체를 search 없이 사용한 참고 후보; search 없이 Quantile 폭과 메타 완성도로 q40 보수 후보 조건부 선택 |
| user_meta_core_bucket_lgb_residual_clip | lightgbm_quantile_plus_lgb_residual | q50_plus_regression_l1_residual | 37 | 작품+사용자 입력 core 작가 메타+메타 bucket | 작가 메타를 구간화해 안정화; search 없는 residual 보정 |
| user_meta_core_bucket_search_free_guard_q40 | lightgbm_quantile_guard_only | q50_or_q40_guard | 34 | 작품+사용자 입력 core 작가 메타+메타 bucket | 작가 메타를 구간화해 안정화; search 없이 Quantile 폭과 메타 완성도로 q40 보수 후보 조건부 선택 |

## 운영 권장안

- 공식 Cold 기본 후보는 `user_meta_core_bucket`을 우선 권장한다.
- 이유: `search_*`, `artist_key`, 같은 작가 가격 이력 없이 동작하면서 작품 only 대비 MdAPE/MAPE/p95가 모두 개선된다.
- `manual_profile_context` 계열은 MdAPE가 가장 낮지만 p95가 크게 악화되므로 기본 후보로 두지 않는다. 사용자가 전시/갤러리 정보를 입력하더라도 검수 또는 별도 후보로만 관리한다.
- `user_meta_core_bucket_search_free_guard_q40`는 p95를 낮추지만 MdAPE/MAPE가 손실되므로 기본 예측값보다 보수 참고값이나 검수 우선순위 후보에 가깝다.
- `existing_meta_full_bucket`은 MAPE/p95가 좋지만 기존 메타 전체에 의존한다. 운영 입력 폼으로 동일 필드를 안정적으로 받을 수 있을 때만 별도 후보로 검토한다.

## 해석 기준
- `artwork_only`는 작가 메타가 전혀 없을 때의 기준이다.
- `user_meta_core` 계열은 운영 입력 폼에서 직접 받을 수 있는 작가 메타 중심 후보이다.
- `manual_profile_context` 계열은 사용자가 전시/갤러리 정보를 직접 입력하거나 승인 cache로 채웠을 때만 쓸 수 있는 후보이다.
- 모든 후보는 `search_*` 피처를 금지하므로 외부 live 검색 중단 조건과 양립한다.
- residual/guard follow-up은 validation에서 선택된 base 후보와 실제 운영 core 후보인 `user_meta_core_bucket`에 적용했다.