# Cold strict 작가 메타 bucket 검증

- 작성일: 2026-06-18T09:58:56
- strict Cold 조건: `artist_key`, 같은 작가 가격 통계, artist_key lookup 후처리 미사용.
- 목적: 작가 메타/외부 live 검색/작품 bucket이 unresolved-artist Cold 성능을 개선하는지 확인.
- 외부 live 검색 피처는 이번 실행에서 실제 live 호출이 아니라, live 검색과 같은 schema로 저장된 동결 cache를 사용했다.
- validation 선택 base 후보: `meta_bucket_raw`

## Test 결과
| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | n_features | feature_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| search_external_bucket | test | strict_bucket_lgbq_base_q50 | 0.440549 | 1.037633 | 3.394335 | 0.857290 | 94 | 작품+작가메타+외부 live 검색/전시+외부 live 검색 bucket |
| cmeta1_repro_full | test | strict_bucket_lgbq_base_q50 | 0.442147 | 1.048405 | 3.353732 | 0.856668 | 87 | 작품+작가메타+외부 live 검색+전시/갤러리 |
| meta_search_combo_bucket | test | strict_bucket_lgbq_base_q50 | 0.458786 | 1.004085 | 3.473269 | 0.850752 | 105 | 작품+작가메타+외부 live 검색/전시+메타/외부 live 검색 조합 bucket |
| meta_bucket_raw_lgb_residual_clip | test | strict_lgb_residual_clip | 0.464247 | 1.085605 | 3.023533 | 0.888108 | 41 | 작품+작가메타+메타 bucket |
| meta_bucket_raw | test | strict_bucket_lgbq_base_q50 | 0.468331 | 1.094027 | 3.003857 | 0.891367 | 38 | 작품+작가메타+메타 bucket |
| meta_bucket_raw_guard_only_q40 | test | strict_guard_only_q40 | 0.470947 | 1.053826 | 2.876164 | 0.917438 | 38 | 작품+작가메타+메타 bucket |
| cmeta1_repro_artwork_only | test | strict_bucket_lgbq_base_q50 | 0.482312 | 1.242417 | 4.380572 | 0.941084 | 12 | 작품 정보만 |
| bucket_only_no_raw_meta | test | strict_bucket_lgbq_base_q50 | 0.581683 | 1.845496 | 7.496422 | 1.119626 | 30 | 작품+bucket only |

## Validation 결과
| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | n_features | feature_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meta_bucket_raw_lgb_residual_clip | validation | strict_lgb_residual_clip | 0.373396 | 0.563457 | 1.467470 | 0.653248 | 41 | 작품+작가메타+메타 bucket |
| meta_bucket_raw_guard_only_q40 | validation | strict_guard_only_q40 | 0.375213 | 0.525842 | 1.331826 | 0.658968 | 38 | 작품+작가메타+메타 bucket |
| meta_bucket_raw | validation | strict_bucket_lgbq_base_q50 | 0.381865 | 0.573758 | 1.510754 | 0.652067 | 38 | 작품+작가메타+메타 bucket |
| cmeta1_repro_artwork_only | validation | strict_bucket_lgbq_base_q50 | 0.396190 | 0.663304 | 1.791011 | 0.678909 | 12 | 작품 정보만 |
| meta_search_combo_bucket | validation | strict_bucket_lgbq_base_q50 | 0.398973 | 0.620492 | 1.681865 | 0.662108 | 105 | 작품+작가메타+외부 live 검색/전시+메타/외부 live 검색 조합 bucket |
| cmeta1_repro_full | validation | strict_bucket_lgbq_base_q50 | 0.412904 | 0.588742 | 1.504212 | 0.655553 | 87 | 작품+작가메타+외부 live 검색+전시/갤러리 |
| search_external_bucket | validation | strict_bucket_lgbq_base_q50 | 0.432493 | 0.595176 | 1.449541 | 0.665775 | 94 | 작품+작가메타+외부 live 검색/전시+외부 live 검색 bucket |
| bucket_only_no_raw_meta | validation | strict_bucket_lgbq_base_q50 | 0.514044 | 2.093649 | 12.913233 | 1.132804 | 30 | 작품+bucket only |

## 후보별 피처 설계
| candidate | model | loss_or_objective | n_features | feature_strategy | hypothesis |
| --- | --- | --- | --- | --- | --- |
| cmeta1_repro_artwork_only | lightgbm | quantile_q10_q50_q90 | 12 | 작품 정보만 | PP-CMETA1 artwork_only 재현 |
| cmeta1_repro_full | lightgbm | quantile_q10_q50_q90 | 87 | 작품+작가메타+외부 live 검색+전시/갤러리 | PP-CMETA1 strict 최상위 후보 재현 |
| meta_bucket_raw | lightgbm | quantile_q10_q50_q90 | 38 | 작품+작가메타+메타 bucket | 작가 메타 구간화 단독 효과 |
| search_external_bucket | lightgbm | quantile_q10_q50_q90 | 94 | 작품+작가메타+외부 live 검색/전시+외부 live 검색 bucket | 외부 live 검색/전시 문맥 구간화 효과 |
| meta_search_combo_bucket | lightgbm | quantile_q10_q50_q90 | 105 | 작품+작가메타+외부 live 검색/전시+메타/외부 live 검색 조합 bucket | 작품 조건과 메타/외부 live 검색 상태 조합 bucket 효과 |
| bucket_only_no_raw_meta | lightgbm | quantile_q10_q50_q90 | 30 | 작품+bucket only | raw meta 없이 구간화 표현만 사용했을 때 안정성 |
| meta_bucket_raw_lgb_residual_clip | lightgbm_quantile_plus_lgb_residual | q50_plus_regression_l1_residual | 41 | 작품+작가메타+메타 bucket | 작가 메타 구간화 단독 효과; residual 보정 follow-up |
| meta_bucket_raw_guard_only_q40 | lightgbm_quantile_guard_only | q50_or_q40_guard | 38 | 작품+작가메타+메타 bucket | 작가 메타 구간화 단독 효과; artist_key lookup 없는 보수 후보 조건부 선택 |

## 해석 기준
- `cmeta1_repro_full`은 PP-CMETA1 strict 최상위 후보 재현 기준이다.
- bucket 후보는 이 기준 대비 MdAPE/MAPE/p95가 개선되는지 본다.
- residual/guard follow-up은 validation에서 선택한 bucket 후보에만 적용했다.
- 모든 후보는 artist_key lookup 없이 동작하므로 strict Cold 운영 후보로 해석 가능하다.
