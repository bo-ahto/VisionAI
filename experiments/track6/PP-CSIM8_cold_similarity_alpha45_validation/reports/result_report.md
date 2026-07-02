# Cold 유사작품 k160 q45 균형 후보 후속 검증

- 작성일: 2026-06-18T15:34:10
- 목적: PP-CSIM7의 균형 후보 `k160_alpha45`를 기존 후보와 k160 q50 대비 후속 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.
- 라우터는 사용하지 않았다.

## 1. 기본 성능
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k160_alpha50 | test | 0.467623 | 1.068718 | 2.920315 | 0.876089 | 0.328816 | 0.529848 | 564 | 263 | 76 | 38 | 유사작품 k160 q50 |
| k160_alpha45 | test | 0.471031 | 0.999148 | 2.569218 | 0.880774 | 0.310745 | 0.532430 | 501 | 233 | 74 | 37 | 유사작품 k160 q45 |
| user_meta_core_bucket | test | 0.473483 | 1.100452 | 2.942330 | 0.887405 | 0.321071 | 0.527267 | 582 | 269 | 72 | 39 | 기존 사용자 메타 core bucket |

## 2. Paired bootstrap
- delta는 `k160_alpha45 - 비교 후보`다. 음수이면 q45 후보가 더 좋다.
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MdAPE_a_minus_b_lt_0 | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | k160_alpha45 | user_meta_core_bucket | 2753 | 800 | 0.006075 | -0.030878 | -0.119737 | 0.160000 | 1.000000 | 1.000000 |
| validation | k160_alpha45 | k160_alpha50 | 2753 | 800 | 0.010098 | -0.027020 | -0.210604 | 0.037500 | 1.000000 | 1.000000 |
| test | k160_alpha45 | user_meta_core_bucket | 3099 | 800 | -0.002924 | -0.101338 | -0.494482 | 0.725000 | 1.000000 | 1.000000 |
| test | k160_alpha45 | k160_alpha50 | 3099 | 800 | 0.003426 | -0.070064 | -0.435021 | 0.271250 | 1.000000 | 1.000000 |

## 3. 가격대별 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k160_alpha45 | test | 1m_3m | 866 | 0.482545 | 0.703997 | 2.010462 | 0.652357 | 45 | 6 |
| k160_alpha50 | test | 1m_3m | 866 | 0.531981 | 0.762641 | 2.187840 | 0.677232 | 58 | 6 |
| user_meta_core_bucket | test | 1m_3m | 866 | 0.523406 | 0.784250 | 2.278503 | 0.691021 | 65 | 6 |
| k160_alpha45 | test | 3m_10m | 1057 | 0.421007 | 0.463703 | 0.940966 | 0.653641 | 12 | 2 |
| k160_alpha50 | test | 3m_10m | 1057 | 0.380260 | 0.467040 | 1.069804 | 0.606447 | 20 | 2 |
| user_meta_core_bucket | test | 3m_10m | 1057 | 0.383002 | 0.471443 | 1.031206 | 0.614236 | 16 | 2 |
| k160_alpha45 | test | gt_10m | 636 | 0.483473 | 0.486703 | 0.899568 | 1.106711 | 0 | 0 |
| k160_alpha50 | test | gt_10m | 636 | 0.471703 | 0.465663 | 0.905791 | 1.047368 | 0 | 0 |
| user_meta_core_bucket | test | gt_10m | 636 | 0.453373 | 0.473580 | 0.907910 | 1.059568 | 0 | 0 |
| k160_alpha45 | test | lt_1m | 540 | 0.815276 | 3.124113 | 26.272536 | 1.220932 | 176 | 66 |
| k160_alpha50 | test | lt_1m | 540 | 1.011363 | 3.447568 | 28.190455 | 1.287387 | 185 | 68 |
| user_meta_core_bucket | test | lt_1m | 540 | 1.000966 | 3.577087 | 29.759225 | 1.301054 | 188 | 64 |

## 4. 메타 누락 stress
| stress_scenario | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | n_missing_fields | missing_fields |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| missing_career_stage | test | 0.469969 | 0.994908 | 2.902143 | 0.878782 | 227 | 76 | 1 | artist_meta_career_stage |
| as_is | test | 0.471031 | 0.999148 | 2.569218 | 0.880774 | 233 | 74 | 0 |  |
| missing_birth_year | test | 0.471939 | 1.000315 | 2.569218 | 0.881514 | 232 | 74 | 1 | artist_meta_birth_year |
| missing_all_core_numeric | test | 0.482065 | 1.020080 | 3.097376 | 0.887332 | 250 | 76 | 6 | artist_meta_birth_year,artist_meta_total_works,artist_meta_total_works_log,artist_meta_followers,artist_meta_followers_log,artist_meta_career_stage |
| missing_total_works | test | 0.504547 | 1.010343 | 2.444215 | 0.895217 | 281 | 75 | 2 | artist_meta_total_works,artist_meta_total_works_log |
| missing_birth_and_followers | test | 0.517550 | 1.097983 | 2.870418 | 0.911389 | 284 | 77 | 3 | artist_meta_birth_year,artist_meta_followers,artist_meta_followers_log |
| missing_followers | test | 0.521527 | 1.102215 | 2.870418 | 0.915546 | 288 | 77 | 2 | artist_meta_followers,artist_meta_followers_log |

## 5. 결론

- `k160_alpha45`는 기존 후보보다 MdAPE/MAPE/p95를 개선하지만 APE > 5는 2건 증가한다.
- `k160_alpha50`보다는 tail이 안정적이며, q50의 개선 신호를 보수적으로 낮춘 후보로 해석된다.
- 메타 누락 stress에서 total works/followers 계열이 빠질 때 약해지는지 확인해야 한다.