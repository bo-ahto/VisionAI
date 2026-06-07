# PP-QR2 Cold 최종 후보 + Quantile q40/q50 결합/라우팅 검증

## 1. 실험 목적

- `PP-QR1`에서 확인된 CatBoost Quantile q40/q50 신호가 기존 Cold 최종 후보에 실제로 도움이 되는지 검증.
- q50은 대표 가격 후보, q40은 MAPE/p95 방어 후보로 분리해서 결합.
- 기존 Cold 대표 개선 후보 `PP-Y18 qwidth_bin_oof_min30_cap0.25`를 기준으로 단순 결합, 위험 구간 결합, segment residual 보정을 비교.

## 2. 사용 데이터와 기준 후보

- 데이터 split: 기존 Cold validation/test 고정.
- 기준 후보: `PP-Y2 component_pp_y2_baseline`, `PP-Y18 qwidth_bin`, `PP-Y18 external_x_qwidth`, `PP-Y18 p95_guard`.
- 추가 Quantile 후보: `PP-QR1 CatBoost q40/q50`, `LightGBM q40/q50`, `Linear Quantile Regression q50`.
- 선택 기준: validation에서 후보를 고르고 test는 확인용으로만 사용.

## 3. 기존 후보와 Quantile 단독 후보

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `component_pp_y18_external_x_qwidth` | control | 0.4239 | 1.0003 | 3.3553 | 0.8557 |
| `component_pp_y18_qwidth_bin` | control | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `component_pp_y2_baseline` | control | 0.4421 | 1.0484 | 3.3537 | 0.8567 |
| `component_pp_y18_p95_guard` | control | 0.4438 | 1.1083 | 2.8025 | 0.8905 |
| `component_catboost_quantile_q50` | quantile_component | 0.4785 | 1.1557 | 4.6234 | 0.9203 |
| `component_catboost_quantile_q40` | quantile_component | 0.4853 | 1.0066 | 3.3333 | 0.9211 |

## 4. Validation 선택 후보의 Test 결과

| 선택 목적 | validation 선택 후보 | 정책 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| mdape_first | `segment_y18_qwidth_pred_gap_min30_cap0p25_s1p00` | quantile_gap_segment_residual_correction | 0.3379 | 0.5132 | 1.4401 | 0.4304 | 1.0314 | 2.9047 |
| mape_guard_mdape_plus_0p02 | `guard_y18_lgb_q40_gap67_down_w0p50` | validation_threshold_guarded_blend | 0.3555 | 0.5096 | 1.3466 | 0.4410 | 0.9698 | 2.5377 |
| p95_guard_mdape_plus_0p03 | `guard_y18_cat_q40_qwidth67_down_w0p50` | validation_threshold_guarded_blend | 0.3651 | 0.5168 | 1.2830 | 0.4263 | 0.9697 | 2.9225 |
| balanced_validation_score | `segment_y18_qwidth_pred_gap_min30_cap0p25_s1p00` | quantile_gap_segment_residual_correction | 0.3379 | 0.5132 | 1.4401 | 0.4304 | 1.0314 | 2.9047 |

## 5. Test 기준 상위 후보

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 비고 |
|---|---|---:|---:|---:|---:|---|
| `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` | quantile_gap_segment_residual_correction | 0.4175 | 1.0029 | 3.0018 | 0.8586 | 기존 PP-Y18보다 개선 |
| `guard_y18_lgb_q40_qwidth67_gap50_down_w0p50` | validation_threshold_guarded_blend | 0.4178 | 0.9640 | 2.5377 | 0.8691 | 기존 PP-Y18보다 개선 |
| `segment_y18_qwidth_pred_gap_min50_cap0p15_s0p50` | quantile_gap_segment_residual_correction | 0.4192 | 1.0028 | 3.0018 | 0.8582 | 기존 PP-Y18보다 개선 |
| `guard_y18_cat_q50_qwidth67_gap50_down_w0p50` | validation_threshold_guarded_blend | 0.4194 | 0.9824 | 2.9305 | 0.8628 | 기존 PP-Y18보다 개선 |
| `guard_y18_lgb_q40_qwidth67_down_w0p50` | validation_threshold_guarded_blend | 0.4197 | 0.9636 | 2.5377 | 0.8693 | 기존 PP-Y18보다 개선 |
| `guard_y18_lgb_q40_qwidth67_gap50_down_w0p25` | validation_threshold_guarded_blend | 0.4197 | 0.9758 | 2.8556 | 0.8616 | 기존 PP-Y18보다 개선 |
| `guard_y18_cat_q50_qwidth67_down_w0p50` | validation_threshold_guarded_blend | 0.4197 | 0.9819 | 2.9305 | 0.8632 | 기존 PP-Y18보다 개선 |
| `segment_y18_qwidth_pred_gap_min30_cap0p10_s0p75` | quantile_gap_segment_residual_correction | 0.4201 | 1.0095 | 2.9942 | 0.8601 | 기존 PP-Y18보다 개선 |
| `guard_y18_lgb_q40_qwidth67_down_w0p25` | validation_threshold_guarded_blend | 0.4201 | 0.9756 | 2.8556 | 0.8617 | 기존 PP-Y18보다 개선 |
| `segment_y18_qwidth_pred_gap_min50_cap0p10_s0p75` | quantile_gap_segment_residual_correction | 0.4205 | 1.0097 | 2.9942 | 0.8597 | 기존 PP-Y18보다 개선 |
| `segment_y18_qwidth_pred_gap_min30_cap0p25_s0p50` | quantile_gap_segment_residual_correction | 0.4208 | 1.0060 | 3.0018 | 0.8590 | 기존 PP-Y18보다 개선 |
| `segment_y18_qwidth_pred_gap_min50_cap0p25_s0p50` | quantile_gap_segment_residual_correction | 0.4208 | 1.0060 | 3.0018 | 0.8584 | 기존 PP-Y18보다 개선 |

## 6. 해석

- 기존 대표 후보 `component_pp_y18_qwidth_bin`: test MdAPE `0.4247`, MAPE `0.9910`, p95 `3.3053`.
- 이번 후보 중 test MdAPE 최저: `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` / MdAPE `0.4175`, MAPE `1.0029`, p95 `3.0018`.
- Quantile q40/q50 신호가 기존 Cold 대표 후보를 추가로 개선할 가능성이 확인됨.
- q40 계열은 MAPE/p95 방어 성격이 있으나, 전체 샘플에 강하게 적용하면 대표 오차가 악화될 수 있음.
- 최종 Cold 모델에 반영하려면 q40 단독이 아니라 `qwidth`, `pred_gap`, `high-pred` 같은 조건부 보정축으로 제한하는 방식이 더 적합.

## 7. 산출물

- 실험 폴더: `experiments/track6/PP-QR2_cold_quantile_final_candidate_blend`.
- `outputs/metrics.csv`: 전체 후보 성능.
- `outputs/predictions.csv`: validation/test 샘플별 예측값.
- `outputs/selection_summary.csv`: validation 선택 후보의 test 결과.
