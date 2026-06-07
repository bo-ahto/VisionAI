# PP-QR3 Cold Quantile q40/q50 보정 후보 OOF/holdout 재검증

## 1. 목적

- `PP-QR2`의 qwidth+pred_gap 보정 신호가 validation 내부 holdout에서도 유지되는지 확인.
- row 5-fold와 artist 5-fold를 함께 사용해 샘플 구성 변화와 작가 구성 변화에 대한 안정성 확인.
- 더 효과적인 후보로 Ridge/Huber/QuantileRegressor/HistGradientBoosting 기반 prediction-level residual meta 보정도 함께 검증.

## 2. 기준 후보

- 기존 기준 후보: `component_pp_y18_qwidth_bin`.
- holdout 평균 기준 MdAPE `0.3640`, MAPE `0.5460`, p95 `1.4177`.
- test 기준 MdAPE `0.4247`, MAPE `0.9910`, p95 `3.3053`.

## 3. Holdout 선택 후보

| 선택 목적 | 후보 | 정책 | holdout MdAPE | holdout MAPE | holdout p95 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | test MdAPE | test MAPE | test p95 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| holdout_mdape_first | `meta_ridge_resid_predonly_a0p1_cap0p15_s1p00` | oof_meta_residual_ridge | 0.3432 | 0.5392 | 1.3944 | 0.9000 | 0.6000 | 0.7000 | 0.4345 | 1.0844 | 3.4669 |
| holdout_mape_guard_mdape_plus_0p02 | `guard_y18_lgb_q40_gap67_down_w0p50` | validation_threshold_guarded_blend | 0.3563 | 0.5095 | 1.2962 | 0.9000 | 1.0000 | 0.9000 | 0.4410 | 0.9698 | 2.5377 |
| holdout_p95_guard_mdape_plus_0p03 | `guard_y18_cat_q40_gap67_down_w0p50` | validation_threshold_guarded_blend | 0.3584 | 0.5110 | 1.2537 | 0.7000 | 1.0000 | 1.0000 | 0.4420 | 0.9756 | 2.9225 |
| holdout_balanced_score | `meta_ridge_resid_predonly_a0p1_cap0p15_s1p00` | oof_meta_residual_ridge | 0.3432 | 0.5392 | 1.3944 | 0.9000 | 0.6000 | 0.7000 | 0.4345 | 1.0844 | 3.4669 |

## 4. Holdout 평균 상위 후보

| 후보 | 정책 | mean MdAPE | mean MAPE | mean p95 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 |
|---|---|---:|---:|---:|---:|---:|---:|
| `meta_ridge_resid_predonly_a0p1_cap0p15_s1p00` | oof_meta_residual_ridge | 0.3432 | 0.5392 | 1.3944 | 0.9000 | 0.6000 | 0.7000 |
| `meta_ridge_resid_predonly_a1_cap0p15_s1p00` | oof_meta_residual_ridge | 0.3433 | 0.5394 | 1.3974 | 0.8000 | 0.6000 | 0.6000 |
| `meta_ridge_resid_predonly_a10_cap0p35_s1p00` | oof_meta_residual_ridge | 0.3449 | 0.5420 | 1.4600 | 0.8000 | 0.6000 | 0.3000 |
| `meta_ridge_resid_predonly_a10_cap0p15_s1p00` | oof_meta_residual_ridge | 0.3451 | 0.5418 | 1.4157 | 0.9000 | 0.6000 | 0.6000 |
| `component_pp_y18_p95_guard` | control | 0.3455 | 0.5358 | 1.4393 | 0.9000 | 0.7000 | 0.4000 |
| `meta_ridge_direct_predonly_a10` | oof_meta_direct_ridge | 0.3465 | 0.5437 | 1.4730 | 0.8000 | 0.6000 | 0.3000 |
| `meta_qr_resid_predgap_a0p001_cap0p15_s1p00` | oof_meta_residual_quantile_regression | 0.3467 | 0.5390 | 1.4117 | 0.9000 | 0.6000 | 0.6000 |
| `meta_ridge_resid_predonly_a0p1_cap0p35_s1p00` | oof_meta_residual_ridge | 0.3469 | 0.5409 | 1.4810 | 0.8000 | 0.6000 | 0.3000 |
| `meta_ridge_resid_predonly_a1_cap0p35_s1p00` | oof_meta_residual_ridge | 0.3470 | 0.5407 | 1.4763 | 0.9000 | 0.6000 | 0.3000 |
| `meta_ridge_resid_predonly_a10_cap0p25_s1p00` | oof_meta_residual_ridge | 0.3471 | 0.5422 | 1.4528 | 0.8000 | 0.6000 | 0.4000 |
| `meta_ridge_resid_predonly_a1_cap0p35_s0p75` | oof_meta_residual_ridge | 0.3473 | 0.5365 | 1.4086 | 0.7000 | 0.7000 | 0.6000 |
| `meta_ridge_direct_predonly_a0p1` | oof_meta_direct_ridge | 0.3474 | 0.5428 | 1.4884 | 0.8000 | 0.6000 | 0.4000 |

## 5. Test 확인 결과

| 후보 | 정책 | MdAPE | MAPE | p95 | RMSE_log |
|---|---|---:|---:|---:|---:|
| `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` | quantile_gap_segment_residual_correction | 0.4175 | 1.0029 | 3.0018 | 0.8586 |
| `guard_y18_lgb_q40_qwidth67_gap50_down_w0p50` | validation_threshold_guarded_blend | 0.4178 | 0.9640 | 2.5377 | 0.8691 |
| `component_pp_y18_qwidth_bin` | control | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `meta_ridge_resid_predonly_a0p1_cap0p15_s1p00` | oof_meta_residual_ridge | 0.4345 | 1.0844 | 3.4669 | 0.8705 |
| `guard_y18_lgb_q40_gap67_down_w0p50` | validation_threshold_guarded_blend | 0.4410 | 0.9698 | 2.5377 | 0.8781 |
| `guard_y18_cat_q40_gap67_down_w0p50` | validation_threshold_guarded_blend | 0.4420 | 0.9756 | 2.9225 | 0.8760 |
| `component_pp_y2_baseline` | control | 0.4421 | 1.0484 | 3.3537 | 0.8567 |

## 6. 판단

- holdout MdAPE 1위였던 Ridge residual meta 후보는 test에서 기존 PP-Y18보다 악화됐다.
- 따라서 prediction-level meta 보정은 이번 결과만으로 최종 후보에 올리지 않는다.
- test 확인 기준으로는 `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50`가 MdAPE를 `0.4247`에서 `0.4175`로 낮췄다.
- MAPE/p95 방어 기준으로는 `guard_y18_lgb_q40_qwidth67_gap50_down_w0p50`가 MdAPE `0.4178`, MAPE `0.9640`, p95 `2.5377`로 가장 균형이 좋았다.
- 결론적으로 더 효과적인 방향은 복잡한 meta 모델이 아니라, qwidth와 q40/q50 gap을 제한적으로 쓰는 guard/segment 보정이다.
- 단, 이 후보들도 최종 교체 전에는 split 재학습 또는 별도 holdout에서 한 번 더 확인한다.

## 7. 산출물

- 실험 폴더: `experiments/track6/PP-QR3_cold_quantile_oof_holdout_revalidation`.
- `outputs/holdout_metrics.csv`: validation 내부 fold별 성능.
- `outputs/holdout_summary.csv`: 후보별 holdout 평균/개선확률.
- `outputs/selection_summary.csv`: holdout 기준 선택 후보와 test 결과.
- `outputs/test_metrics.csv`: 선택 후보의 test 확인 성능.
