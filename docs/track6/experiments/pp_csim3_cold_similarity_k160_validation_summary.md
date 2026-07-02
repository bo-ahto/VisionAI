# Cold 유사작품 k160 후보 후속 검증

- 작성일: 2026-06-18T15:11:53
- 목적: PP-CSIM2에서 나온 `artwork_similarity_k160` 후보를 라우터 없이 후속 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.
- 학습 행 유사작품 통계는 out-of-fold, validation/test는 train-only 기준이다.

## 1. 기본 성능
| candidate | split | policy | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | n_features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_similarity_k160 | test | 작품 유사 비교군 top_k=160 통계 추가 | 0.467623 | 1.068718 | 2.920315 | 0.876089 | 0.328816 | 0.529848 | 45 |
| user_meta_core_bucket | test | 작품+사용자 입력 작가 메타 bucket | 0.473483 | 1.100452 | 2.942330 | 0.887405 | 0.321071 | 0.527267 | 34 |
| artwork_only | test | 작품 정보만 | 0.489892 | 1.238691 | 4.117775 | 0.938639 | 0.293643 | 0.508228 | 12 |

## 2. Paired bootstrap

- delta는 `artwork_similarity_k160 - 비교 후보`다. 음수면 k160 후보가 더 좋다는 뜻이다.
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MdAPE_a_minus_b_lt_0 | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | artwork_similarity_k160 | user_meta_core_bucket | 2753 | 800 | -0.004023 | -0.003858 | 0.090867 | 0.780000 | 0.831250 | 0.051250 |
| validation | artwork_similarity_k160 | artwork_only | 2753 | 800 | -0.036388 | -0.135039 | -0.318447 | 1.000000 | 1.000000 | 1.000000 |
| test | artwork_similarity_k160 | user_meta_core_bucket | 3099 | 800 | -0.006349 | -0.031274 | -0.059461 | 0.892500 | 1.000000 | 0.713750 |
| test | artwork_similarity_k160 | artwork_only | 3099 | 800 | -0.023447 | -0.170607 | -1.335227 | 0.997500 | 1.000000 | 1.000000 |

## 3. 메타 누락 stress

- 작품 유사 통계는 유지하고, 사용 단계에서 사용자 작가 메타가 비어 있는 상황만 시뮬레이션했다.
| stress_scenario | split | MdAPE | MAPE | p95_APE | RMSE_log | n_missing_fields | missing_fields |
| --- | --- | --- | --- | --- | --- | --- | --- |
| missing_career_stage | test | 0.453454 | 1.036247 | 3.005875 | 0.866578 | 1 | artist_meta_career_stage |
| as_is | test | 0.467623 | 1.068718 | 2.920315 | 0.876089 | 0 |  |
| missing_birth_year | test | 0.471759 | 1.071326 | 2.920315 | 0.877536 | 1 | artist_meta_birth_year |
| missing_all_core_numeric | test | 0.476827 | 1.106826 | 3.485506 | 0.886451 | 6 | artist_meta_birth_year,artist_meta_total_works,artist_meta_total_works_log,artist_meta_followers,artist_meta_followers_log,artist_meta_career_stage |
| missing_birth_and_followers | test | 0.497094 | 1.096480 | 3.122680 | 0.901178 | 3 | artist_meta_birth_year,artist_meta_followers,artist_meta_followers_log |
| missing_followers | test | 0.498320 | 1.099765 | 3.122680 | 0.905107 | 2 | artist_meta_followers,artist_meta_followers_log |
| missing_total_works | test | 0.501137 | 1.179235 | 3.688202 | 0.918661 | 2 | artist_meta_total_works,artist_meta_total_works_log |

## 4. 위험 세그먼트
| candidate | split | segment_type | segment | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| user_meta_core_bucket | test | actual_price_band | lt_1m | 540 | 1.000966 | 3.577087 | 29.759225 | 1.301054 |
| artwork_similarity_k160 | test | actual_price_band | lt_1m | 540 | 1.011363 | 3.447568 | 28.190455 | 1.287387 |
| user_meta_core_bucket | test | quantile_width_band | qwidth_q2 | 775 | 0.561877 | 2.312685 | 8.861493 | 1.100124 |
| artwork_similarity_k160 | test | quantile_width_band | qwidth_q2 | 775 | 0.470188 | 2.153302 | 7.740302 | 1.040201 |
| user_meta_core_bucket | test | quantile_width_band | qwidth_q3 | 774 | 0.470242 | 0.709678 | 2.502411 | 0.771685 |
| artwork_similarity_k160 | test | quantile_width_band | qwidth_q4_high | 774 | 0.560605 | 0.776683 | 2.374737 | 0.996226 |
| user_meta_core_bucket | test | actual_price_band | 1m_3m | 866 | 0.523406 | 0.784250 | 2.278503 | 0.691021 |
| artwork_similarity_k160 | test | actual_price_band | 1m_3m | 866 | 0.531981 | 0.762641 | 2.187840 | 0.677232 |
| artwork_similarity_k160 | test | quantile_width_band | qwidth_q3 | 775 | 0.448406 | 0.695848 | 2.171372 | 0.799454 |
| user_meta_core_bucket | test | quantile_width_band | qwidth_q1_low | 775 | 0.382989 | 0.709891 | 2.166730 | 0.614463 |
| artwork_similarity_k160 | test | quantile_width_band | qwidth_q1_low | 775 | 0.392543 | 0.648662 | 1.950467 | 0.597333 |
| user_meta_core_bucket | test | quantile_width_band | qwidth_q4_high | 775 | 0.524902 | 0.669048 | 1.741136 | 0.983038 |
| artwork_similarity_k160 | test | actual_price_band | 3m_10m | 1057 | 0.380260 | 0.467040 | 1.069804 | 0.606447 |
| user_meta_core_bucket | test | actual_price_band | 3m_10m | 1057 | 0.383002 | 0.471443 | 1.031206 | 0.614236 |
| user_meta_core_bucket | test | actual_price_band | gt_10m | 636 | 0.453373 | 0.473580 | 0.907910 | 1.059568 |
| artwork_similarity_k160 | test | actual_price_band | gt_10m | 636 | 0.471703 | 0.465663 | 0.905791 | 1.047368 |

## 5. 결론

- `artwork_similarity_k160`은 기본 test 성능에서 `user_meta_core_bucket`보다 MdAPE/MAPE/p95/RMSE를 모두 소폭 개선했다.
- bootstrap 기준 MAPE/RMSE 개선은 강하고, MdAPE 개선도 비교적 일관적이다. p95 개선은 test에서는 우세하지만 validation에서는 우세하지 않아 tail 안정성은 추가 확인이 필요하다.
- 메타 누락 stress에서는 followers/total works 계열이 빠질 때 성능이 약해지므로, 이 후보를 쓰더라도 해당 입력값은 권장 또는 필수 입력으로 관리해야 한다.
- 라우터는 사용하지 않았으므로 이 결과는 후보 모델 자체의 피처 변경 효과다.