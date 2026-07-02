# Cold 사용자 입력 작가 메타 강건성 검증

- 작성일: 2026-06-18T14:42:15
- 목적: PP-CMETA4 권장 후보 `user_meta_core_bucket`의 운영 강건성을 추가 검증한다.
- strict Cold 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.

## 1. 기본 후보 재현
| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | n_features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_only | test | strict_user_meta_lgbq_base_q50 | 0.482312 | 1.242417 | 4.380572 | 0.941084 | 0.286221 | 0.516296 | 12 |
| user_meta_core_bucket | test | strict_user_meta_lgbq_base_q50 | 0.461481 | 1.126798 | 3.089863 | 0.894627 | 0.317199 | 0.528880 | 34 |
| artwork_only | validation | strict_user_meta_lgbq_base_q50 | 0.396190 | 0.663304 | 1.791011 | 0.678909 | 0.343625 | 0.637123 | 12 |
| user_meta_core_bucket | validation | strict_user_meta_lgbq_base_q50 | 0.392975 | 0.555096 | 1.422948 | 0.658183 | 0.403197 | 0.619324 | 34 |

## 2. artwork_only 대비 paired bootstrap

- delta는 `user_meta_core_bucket - artwork_only`이다. 음수면 user_meta_core_bucket이 더 좋다는 뜻이다.
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MdAPE_a_minus_b_lt_0 | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | user_meta_core_bucket | artwork_only | 2753 | 800 | -0.002425 | -0.109826 | -0.336492 | 0.636250 | 1.000000 | 1.000000 |
| test | user_meta_core_bucket | artwork_only | 3099 | 800 | -0.020461 | -0.115923 | -1.431837 | 0.997500 | 1.000000 | 1.000000 |

## 3. 입력 메타 누락 stress

- 학습된 `user_meta_core_bucket` 모델에 대해 사용 단계에서 특정 사용자 입력 메타가 비어 있는 상황을 시뮬레이션했다.
- `missing_all_core_numeric`은 core 숫자 메타가 대부분 비어 있는 경우다. 이 경우에도 category/작품 피처와 missing flag는 남는다.
| stress_scenario | split | MdAPE | MAPE | p95_APE | RMSE_log | n_missing_fields | missing_fields |
| --- | --- | --- | --- | --- | --- | --- | --- |
| missing_birth_year | test | 0.461481 | 1.124969 | 3.142891 | 0.894131 | 1 | artist_meta_birth_year |
| as_is | test | 0.461481 | 1.126798 | 3.089863 | 0.894627 | 0 |  |
| missing_career_stage | test | 0.469583 | 1.171376 | 3.207598 | 0.895497 | 1 | artist_meta_career_stage |
| missing_all_core_numeric | test | 0.479310 | 1.161910 | 3.498690 | 0.902087 | 6 | artist_meta_birth_year,artist_meta_total_works,artist_meta_total_works_log,artist_meta_followers,artist_meta_followers_log,artist_meta_career_stage |
| missing_total_works | test | 0.487701 | 1.066544 | 3.120488 | 0.897406 | 2 | artist_meta_total_works,artist_meta_total_works_log |
| missing_birth_and_followers | test | 0.504369 | 1.139409 | 3.218260 | 0.914834 | 3 | artist_meta_birth_year,artist_meta_followers,artist_meta_followers_log |
| missing_followers | test | 0.507182 | 1.146838 | 3.218260 | 0.917912 | 2 | artist_meta_followers,artist_meta_followers_log |

## 4. test 위험 세그먼트
| candidate | split | segment_type | segment | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| user_meta_core_bucket | test | actual_price_band | lt_1m | 540 | 0.945583 | 3.695863 | 29.815975 | 1.320860 |
| user_meta_core_bucket | test | quantile_width_band | qwidth_q2 | 775 | 0.471558 | 2.422290 | 8.681353 | 1.102109 |
| user_meta_core_bucket | test | exhibition_available | exhibition_available | 1693 | 0.446583 | 1.474644 | 4.102543 | 0.884729 |
| user_meta_core_bucket | test | gallery_available | gallery_available | 1734 | 0.448578 | 1.457768 | 4.102543 | 0.881007 |
| user_meta_core_bucket | test | actual_price_band | 1m_3m | 866 | 0.534829 | 0.811454 | 2.272944 | 0.704876 |
| user_meta_core_bucket | test | quantile_width_band | qwidth_q4_high | 775 | 0.542486 | 0.736605 | 2.251776 | 1.008327 |
| user_meta_core_bucket | test | gallery_available | gallery_missing | 1365 | 0.477770 | 0.706356 | 2.232105 | 0.911635 |
| user_meta_core_bucket | test | exhibition_available | exhibition_missing | 1406 | 0.479262 | 0.707947 | 2.231939 | 0.906401 |
| user_meta_core_bucket | test | quantile_width_band | qwidth_q3 | 774 | 0.458727 | 0.690183 | 2.210305 | 0.789828 |
| user_meta_core_bucket | test | quantile_width_band | qwidth_q1_low | 775 | 0.410216 | 0.657549 | 1.920240 | 0.588220 |
| user_meta_core_bucket | test | actual_price_band | 3m_10m | 1057 | 0.377955 | 0.466493 | 1.107585 | 0.606324 |
| user_meta_core_bucket | test | actual_price_band | gt_10m | 636 | 0.453924 | 0.472291 | 0.897747 | 1.063493 |

## 5. 결론

- `user_meta_core_bucket`은 strict Cold test에서 artwork_only 대비 MdAPE, MAPE, p95 APE, RMSE log를 모두 개선했다.
- paired bootstrap에서도 test 기준 MdAPE/MAPE/p95 개선 확률이 높아, 사용자 입력 작가 메타를 쓰는 방향은 추가 근거가 생겼다.
- 다만 followers 계열, career stage, total works 입력이 비면 MdAPE 또는 p95가 흔들리므로 입력 폼에서는 필수/권장 필드 정책이 필요하다.
- 100만원 미만 작품 구간은 p95가 매우 커서 Cold 운영에서 검수 표시 또는 보수 범위 표시 대상으로 관리해야 한다.
- 이 실험도 strict Cold 하네스 조건을 유지하므로 artist_key 기반 lookup 성능으로 해석하지 않는다.