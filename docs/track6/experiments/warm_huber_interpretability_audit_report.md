# Warm Huber 해석 감사 보고서

- 작성일: `2026-05-31`

- 결론: 기존 Warm 해석 산출물은 최종 artifact와 피처셋이 불일치하므로, 최종 Warm Huber 설명 근거로 그대로 쓰기 어렵다.

- 보정: 최종 artifact `data/track6/artifacts/track6_warm_huber.joblib`를 직접 불러와 계수, 기여도, Huber outlier 진단을 재산출했다.

- 해석 기준: 범주형 피처는 one-hot 원계수 대신 같은 원본 피처 안의 평균 범주 효과를 뺀 centered 기여도를 우선 사용한다.

- 재실험 판단: 성능 관점에서는 즉시 모델 전체를 재실험할 근거는 약하다. 다만 `epsilon=1.1`은 validation MdAPE가 낮지만 수렴 실패와 test p95 악화가 있어, 별도 안정성 실험 후보로만 둔다.

## 1. 피처셋 일치성 감사
| feature | final_artifact_feature | old_interpretability_feature | status |
| --- | --- | --- | --- |
| area_cm2 | True | False | 불일치 |
| artist_key | True | False | 불일치 |
| artist_name_ko | False | True | 불일치 |
| artist_works_log | False | True | 불일치 |
| artist_works_log_is_missing | False | True | 불일치 |
| aspect_ratio | True | True | 일치 |
| depth_cm | True | False | 불일치 |
| has_depth | True | False | 불일치 |
| height_cm | True | True | 일치 |
| is_3d_candidate | True | False | 불일치 |
| is_extreme_aspect_ratio | True | False | 불일치 |
| log_area | True | True | 일치 |
| medium_category | True | False | 불일치 |
| medium_support_bucket | True | False | 불일치 |
| support_category | True | False | 불일치 |
| width_cm | True | True | 일치 |

## 2. 최종 artifact 성능 재확인
| split | rows | MdAPE | MAPE | p90_APE | p95_APE | Within_30 | Within_50 | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train+validation(final artifact fit data) | 27433 | 0.167748 | 0.36987 | 0.72476 | 1.03453 | 0.691685 | 0.828054 | 0.536718 |
| test_warm | 607 | 0.224072 | 0.495073 | 1.10726 | 2.02092 | 0.593081 | 0.726524 | 0.60927 |

## 3. Huber outlier 진단
| split | rows | epsilon | scale | outlier_threshold_log | outlier_count | outlier_rate | median_abs_residual_log | p95_abs_residual_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train+validation | 27433 | 1.35 | 0.170999 | 0.230848 | 10858 | 0.395801 | 0.168412 | 1.09838 |
| test_warm | 607 | 1.35 | 0.170999 | 0.230848 | 297 | 0.489292 | 0.221419 | 1.36446 |

## 4. Huber epsilon 민감도 추가 진단
| epsilon | split | rows | MdAPE | MAPE | p90_APE | p95_APE | Within_30 | Within_50 | RMSE_log | outlier_rate | n_iter | scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1 | val_warm | 519 | 0.207855 | 0.409035 | 0.916492 | 1.292 | 0.593449 | 0.743738 | 0.649733 | 0.780347 | 3000 | 0.0510113 |
| 1.1 | test_warm_locked | 607 | 0.225431 | 0.492333 | 1.10654 | 2.04155 | 0.581549 | 0.728171 | 0.606968 | 0.83196 | 3000 | 0.0510113 |
| 1.35 | val_warm | 519 | 0.212583 | 0.41668 | 0.919498 | 1.31936 | 0.595376 | 0.732177 | 0.644612 | 0.479769 | 2512 | 0.173951 |
| 1.35 | test_warm_locked | 607 | 0.227425 | 0.495201 | 1.10215 | 2.01304 | 0.589786 | 0.723229 | 0.608054 | 0.482702 | 2512 | 0.173951 |
| 1.5 | val_warm | 519 | 0.21903 | 0.419185 | 0.924615 | 1.33153 | 0.597303 | 0.736031 | 0.642874 | 0.393064 | 2872 | 0.223968 |
| 1.5 | test_warm_locked | 607 | 0.231553 | 0.496428 | 1.12695 | 2.02251 | 0.591433 | 0.723229 | 0.608372 | 0.388797 | 2872 | 0.223968 |
| 1.75 | val_warm | 519 | 0.226088 | 0.422145 | 0.906341 | 1.35108 | 0.585742 | 0.732177 | 0.64023 | 0.254335 | 2438 | 0.285655 |
| 1.75 | test_warm_locked | 607 | 0.234718 | 0.498946 | 1.13591 | 2.06907 | 0.583196 | 0.719934 | 0.608053 | 0.288303 | 2438 | 0.285655 |
| 2 | val_warm | 519 | 0.22028 | 0.424712 | 0.897043 | 1.36199 | 0.581888 | 0.732177 | 0.63725 | 0.169557 | 2129 | 0.329435 |
| 2 | test_warm_locked | 607 | 0.239602 | 0.50288 | 1.12196 | 2.11526 | 0.579901 | 0.711697 | 0.608097 | 0.222405 | 2129 | 0.329435 |

## 5. 피처 그룹별 실제 기여도
| feature_group | encoded_feature_count | mean_abs_centered_contribution_sum | top_features | top_up_features | top_down_features | rank |
| --- | --- | --- | --- | --- | --- | --- |
| size | 4 | 1.22221 | num__log_area / num__height_cm / num__width_cm / num__area_cm2 | num__log_area / num__height_cm / num__width_cm | num__area_cm2 | 1 |
| medium_support | 58 | 0.562494 | cat__medium_support_bucket_mixed_media__canvas / cat__medium_support_bucket_mixed_media__unknown / cat__medium_support_bucket_acrylic__canvas / cat__medium_support_bucket_oil__linen / cat__medium_support_bucket_oil__canvas | cat__medium_support_bucket_acrylic__canvas / cat__medium_support_bucket_oil__linen / cat__medium_support_bucket_oil__canvas / cat__medium_support_bucket_mixed_media__paper / cat__medium_support_bucket_acrylic__linen | cat__medium_support_bucket_mixed_media__canvas / cat__medium_support_bucket_mixed_media__unknown / cat__medium_support_bucket_painting_material__unknown / cat__medium_support_bucket_textile__unknown / cat__medium_support_bucket_painting_material__paper | 2 |
| support | 9 | 0.512101 | cat__support_category_paper / cat__support_category_canvas / cat__support_category_unknown / cat__support_category_linen / cat__support_category_fabric | cat__support_category_canvas / cat__support_category_unknown / cat__support_category_metal / cat__support_category_glass | cat__support_category_paper / cat__support_category_linen / cat__support_category_fabric / cat__support_category_panel / cat__support_category_wood | 3 |
| medium | 18 | 0.492027 | cat__medium_category_mixed_media / cat__medium_category_acrylic / cat__medium_category_oil / cat__medium_category_painting_material / cat__medium_category_textile | cat__medium_category_mixed_media / cat__medium_category_painting_material / cat__medium_category_textile / cat__medium_category_ink / cat__medium_category_charcoal | cat__medium_category_acrylic / cat__medium_category_oil / cat__medium_category_other / cat__medium_category_print / cat__medium_category_sculpture_material | 4 |
| artist | 648 | 0.43531 | cat__artist_key_infrequent_sklearn / cat__artist_key_sang oktabu kim / cat__artist_key_sheean kim / cat__artist_key_young sung kim / cat__artist_key_ham sup 함섭 | cat__artist_key_sang oktabu kim / cat__artist_key_sheean kim / cat__artist_key_young sung kim / cat__artist_key_ham sup 함섭 / cat__artist_key_yoo suntai | cat__artist_key_infrequent_sklearn / cat__artist_key_jeremy yong / cat__artist_key_hyungjun suh / cat__artist_key_ro un lee / cat__artist_key_chang beom son | 5 |
| depth_3d | 5 | 0.0320326 | cat__is_3d_candidate_True / cat__is_3d_candidate_False / cat__has_depth_False / cat__has_depth_True / num__depth_cm | cat__is_3d_candidate_True / cat__has_depth_False | cat__is_3d_candidate_False / cat__has_depth_True / num__depth_cm | 6 |
| shape | 2 | 0.00665425 | num__aspect_ratio / cat__is_extreme_aspect_ratio_False |  | num__aspect_ratio | 7 |

## 6. 계수/기여도 상위 30개
| encoded_feature | raw_feature | feature_group | coef | centered_coef | original_unit_coef | active_rate | mean_abs_centered_contribution | mean_centered_contribution | rank_by_centered_abs_contribution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| num__log_area | log_area | size | 0.478722 | 0.478722 | 0.4029 | 0.0317986 | 0.409571 | 0.0152227 | 1 |
| num__height_cm | height_cm | size | 0.390577 | 0.390577 | 0.00859934 | 0.0631754 | 0.30147 | 0.0246749 | 2 |
| num__width_cm | width_cm | size | 0.396147 | 0.396147 | 0.00883326 | 0.0331091 | 0.299148 | 0.0131161 | 3 |
| num__area_cm2 | area_cm2 | size | -0.38819 | -0.38819 | -3.80059e-05 | 0.0382279 | 0.212018 | -0.0148397 | 4 |
| cat__medium_category_mixed_media | medium_category | medium | 0.338681 | 0.433021 | - | 0.397035 | 0.171924 | 0.171924 | 5 |
| cat__support_category_paper | support_category | support | -0.145475 | -0.843315 | - | 0.169687 | 0.1431 | -0.1431 | 6 |
| cat__medium_category_acrylic | medium_category | medium | -0.610797 | -0.516456 | - | 0.248764 | 0.128476 | -0.128476 | 7 |
| cat__support_category_canvas | support_category | support | 0.90977 | 0.21193 | - | 0.583196 | 0.123597 | 0.123597 | 8 |
| cat__support_category_unknown | support_category | support | 1.77248 | 1.07464 | - | 0.110379 | 0.118617 | 0.118617 | 9 |
| cat__medium_support_bucket_mixed_media__canvas | medium_support_bucket | medium_support | -0.497996 | -0.690225 | - | 0.146623 | 0.101203 | -0.101203 | 10 |
| cat__medium_category_oil | medium_category | medium | -0.504975 | -0.410634 | - | 0.243822 | 0.100122 | -0.100122 | 11 |
| cat__support_category_linen | support_category | support | -0.797257 | -1.4951 | - | 0.0477759 | 0.0714297 | -0.0714297 | 12 |
| cat__medium_support_bucket_mixed_media__unknown | medium_support_bucket | medium_support | -1.1117 | -1.30393 | - | 0.0510708 | 0.0665926 | -0.0665926 | 13 |
| cat__medium_support_bucket_acrylic__canvas | medium_support_bucket | medium_support | 0.470853 | 0.278624 | - | 0.217463 | 0.0605904 | 0.0605904 | 14 |
| cat__artist_key_infrequent_sklearn | artist_key | artist | -0.147938 | -0.148997 | - | 0.401977 | 0.0598935 | -0.0598935 | 15 |
| cat__medium_support_bucket_oil__linen | medium_support_bucket | medium_support | 2.18738 | 1.99515 | - | 0.0263591 | 0.0525904 | 0.0525904 | 16 |
| cat__medium_category_painting_material | medium_category | medium | 1.58461 | 1.67895 | - | 0.029654 | 0.0497878 | 0.0497878 | 17 |
| cat__medium_support_bucket_oil__canvas | medium_support_bucket | medium_support | 0.413236 | 0.221007 | - | 0.200988 | 0.0444198 | 0.0444198 | 18 |
| cat__medium_support_bucket_painting_material__unknown | medium_support_bucket | medium_support | -2.42123 | -2.61346 | - | 0.014827 | 0.0387498 | -0.0387498 | 19 |
| cat__medium_support_bucket_mixed_media__paper | medium_support_bucket | medium_support | 0.482082 | 0.289853 | - | 0.125206 | 0.0362913 | 0.0362913 | 20 |
| cat__support_category_fabric | support_category | support | -0.324424 | -1.02226 | - | 0.0230643 | 0.0235778 | -0.0235778 | 21 |
| cat__medium_support_bucket_textile__unknown | medium_support_bucket | medium_support | -4.32647 | -4.5187 | - | 0.00494234 | 0.0223329 | -0.0223329 | 22 |
| cat__artist_key_sang oktabu kim | artist_key | artist | 3.91811 | 3.91705 | - | 0.00494234 | 0.0193594 | 0.0193594 | 23 |
| cat__artist_key_sheean kim | artist_key | artist | 3.84712 | 3.84606 | - | 0.00494234 | 0.0190085 | 0.0190085 | 24 |
| cat__support_category_panel | support_category | support | 0.263956 | -0.433884 | - | 0.0411862 | 0.01787 | -0.01787 | 25 |
| cat__medium_category_textile | medium_category | medium | 3.46894 | 3.56328 | - | 0.00494234 | 0.017611 | 0.017611 | 26 |
| cat__medium_support_bucket_acrylic__linen | medium_support_bucket | medium_support | 2.2523 | 2.06007 | - | 0.00823723 | 0.0169693 | 0.0169693 | 27 |
| cat__medium_support_bucket_acrylic__paper | medium_support_bucket | medium_support | 1.40994 | 1.21771 | - | 0.0115321 | 0.0140428 | 0.0140428 | 28 |
| cat__support_category_metal | support_category | support | 1.74644 | 1.0486 | - | 0.0131796 | 0.0138201 | 0.0138201 | 29 |
| cat__is_3d_candidate_True | is_3d_candidate | depth_3d | 2.71458 | 0.60361 | - | 0.0197694 | 0.011933 | 0.011933 | 30 |
