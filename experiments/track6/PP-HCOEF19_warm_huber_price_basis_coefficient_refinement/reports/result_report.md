# PP-HCOEF19 Warm Huber 운영 피처 파이프라인 재현성 검증

## 1. 실험 목적

- HCOEF16~18에서 사용한 연구용 component와 v0.1 운영 pipeline component가 같은 값을 내는지 확인.
- 새 보정값을 test/0604에서 만들지 않고, 다음 Huber 계수 실험 전에 입력 피처 재현성을 검증.
- 결론은 성능 후보 채택이 아니라, 다음 HCOEF 실험을 진행해도 되는지에 대한 감사 결과.

## 2. 핵심 결론

- component reconciliation: 통과.
- formula check: 통과.
- 운영 Warm feature file의 필수 피처 누락 수: 0.
- HCOEF19에서는 새 운영 후보를 채택하지 않음.
- quantile width는 HCOEF18 결론대로 점 예측 이동보다 가격 범위/신뢰도 정책 검증에 우선 사용.

## 3. 0604 공통 행 후보 성능

| scope | split | candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | over_2x_n | under_half_n | stable_MdAPE | stable_MAPE | stable_p95_APE | stable_RMSE_log | delta_MdAPE_vs_hcoef_stable | delta_MAPE_vs_hcoef_stable | delta_p95_APE_vs_hcoef_stable | delta_RMSE_log_vs_hcoef_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_reconciled_ex50 | 0604_ex50 | ppv8_operational_service_primary | operational_service_primary_on_0604 | 829 | 0.229792 | 0.335885 | 0.927338 | 0.712419 | 0.599517 | 0.790109 | 31 | 89 | 0.273062 | 0.374365 | 0.983456 | 1.307766 | -0.043269 | -0.038481 | -0.056118 | -0.595347 |
| 0604_reconciled_ex50 | 0604_ex50 | hcoef_stable | research_hcoef_stable_on_0604 | 829 | 0.273062 | 0.374365 | 0.983456 | 1.307766 | 0.516285 | 0.710495 | 26 | 152 | 0.273062 | 0.374365 | 0.983456 | 1.307766 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 0604_reconciled_ex50 | 0604_ex50 | current_70_30_operational | operational_70_30_on_0604 | 829 | 0.277935 | 0.377354 | 0.987056 | 1.311738 | 0.527141 | 0.714113 | 30 | 153 | 0.273062 | 0.374365 | 0.983456 | 1.307766 | 0.004873 | 0.002989 | 0.003601 | 0.003972 |

## 4. 연구 산출물과 운영 산출물 component 비교

| check_name | left_column | right_column | n | status | max_abs_log_diff | mean_abs_log_diff | median_abs_log_diff | p95_abs_log_diff | exact_match_rate_1e8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| svc_research_vs_operational | svc_numeric_seed_mean | svc_numeric_seed_mean_pred_log | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| ppv8_research_vs_operational | ppv8_service_proxy | pp_v8_compact_blend_mape_guarded_pred_log | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| current70_30_research_vs_operational | current_70_30 | v01_operational_pred_log | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| l10_research_vs_operational | l10_seq_pred_log | l10_generated_bucket_seq_pred_log | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| quantile_width_research_vs_operational | quantile_width | l10_quantile_width | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| price_range_ratio_research_vs_operational | l10_price_range_ratio_research | l10_price_range_ratio_operational | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |

## 5. 운영 예측식 검증

| check_name | left_column | right_column | n | status | max_abs_log_diff | mean_abs_log_diff | median_abs_log_diff | p95_abs_log_diff | exact_match_rate_1e8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| operational_ppv8_formula | formula_operational_ppv8 | pp_v8_compact_blend_mape_guarded_pred_log | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| operational_70_30_formula | formula_operational_v01 | v01_operational_pred_log | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| research_70_30_formula | formula_research_v01 | current_70_30 | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |
| service_primary_equals_ppv8 | service_primary_pred_log | pp_v8_compact_blend_mape_guarded_pred_log | 829 | pass | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 |

## 6. 운영 피처 파일 감사 요약

| audit_type | feature | required_by | status | n_rows | missing_rate | details |
| --- | --- | --- | --- | --- | --- | --- |

## 7. 정책 판단

| policy_item | status | details |
| --- | --- | --- |
| component_reconciliation | pass | Research and operational component logs match on common 0604 rows. |
| formula_checks | pass | Operational formulas reproduce saved prediction columns. |
| feature_schema | pass | Missing required operational features: 0 |
| next_experiment | ready | If ready, continue with HCOEF20 coefficient/range policy experiments without changing test-derived thresholds. |

## 8. 다음 보정 방향

- component/formula/feature schema가 모두 통과하면 HCOEF20에서 저차원 Huber 계수 재탐색 또는 가격 범위/신뢰도 정책 검증을 진행.
- component 불일치가 있으면 새 모델 실험보다 먼저 해당 column mapping과 피처 생성 로직을 수정.
- 운영 기본 후보 변경은 HCOEF19 결과만으로 결정하지 않음.
