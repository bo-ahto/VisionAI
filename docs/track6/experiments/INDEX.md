# Track 6 실험 기록 인덱스

- 목적: Track6 개별 실험 기록을 한눈에 관리
- 정렬 기준: 최신 실험이 위로 오도록 관리
- 상태: T6-E010 헤도닉 작가명 + 호수 / ln 변환 실험 완료

## 종합 문서

- [A~J + OPT 피처/모델 종합 분석 HTML](a_to_j_optimal_feature_model_analysis.html)
- [A~J + OPT 피처/모델 종합 분석 Markdown](a_to_j_optimal_feature_model_analysis.md)
- [A~J 피처별 영향도 분석 HTML](feature_influence_analysis.html)
- [A~J 피처별 영향도 분석 Markdown](feature_influence_analysis.md)
- [A~J 피처별 영향도 분석 CSV](feature_influence_analysis.csv)
- [A~J 피처별 영향도 요약 CSV](feature_influence_summary.csv)
- [Track6 중간 실험 결과 요약 및 후처리 계획 HTML](midterm_result_postprocessing_report.html)
- [Track6 중간 실험 결과 요약 및 후처리 계획 Markdown](midterm_result_postprocessing_report.md)
- [Track6 실험 결과 통합 CSV 안내](track6_unified_metrics_readme.md)
- [Track6 전체 실험 모델 지표 long CSV](track6_all_experiment_model_metrics_long.csv)
- [Track6 피처 조합별 모델 1~3위 CSV](track6_best_model_by_feature_block.csv)
- [Track6 Warm/Cold 피처-모델 요약 CSV](track6_feature_model_pivot_summary.csv)
- [Track6 실험 내부 피처 차이 CSV](track6_feature_influence_delta.csv)
- [Cold CatBoost 테스트 근거 정리 HTML](cold_catboost_performance_summary.html)
- [Cold CatBoost 테스트 근거 정리 Markdown](cold_catboost_performance_summary.md)
- [Cold CatBoost 테스트 근거 CSV](cold_catboost_performance_summary.csv)
- [Cold CatBoost vs 기존 후보 비교 HTML](cold_catboost_vs_previous_candidates.html)
- [Cold CatBoost vs 기존 후보 비교 Markdown](cold_catboost_vs_previous_candidates.md)
- [A~J + OPT 전체 지표 CSV](a_to_j_plus_opt_all_metrics.csv)
- [A1-D11 실험 종합 HTML](a1_d11_experiment_summary.html)
- [A1-D11 실험 종합 Markdown](a1_d11_experiment_summary.md)
- [A1-D11 실험 종합 CSV](a1_d11_summary_table.csv)
- [최적 피처 조합 요약 CSV](optimal_feature_combo_summary_table.csv)
- [실험 결과 지표 해석 기준](metric_interpretation_standard.md)
- [모델 후보 종합 점수 기준](composite_score_method.md)
- [Warm / Cold 모델 후보 확정 근거와 고도화 계획 HTML](final_model_decision_and_enhancement_plan.html)
- [Warm / Cold 모델 후보 확정 근거와 고도화 계획 Markdown](final_model_decision_and_enhancement_plan.md)
- [Warm Huber 계수 / Cold CatBoost SHAP 해석 리포트](../../../experiments/track6/FINAL_model_interpretability/outputs/interpretability_report.html)
- [후속 실험 계획 HTML](followup_experiment_plan.html)
- [후속 실험 계획 Markdown](followup_experiment_plan.md)
- [3일 후처리/튜닝 실행 계획 HTML](three_day_model_postprocessing_tuning_plan.html)
- [3일 후처리/튜닝 실행 계획 Markdown](three_day_model_postprocessing_tuning_plan.md)
- [후처리 및 모델 고도화 검증 계획 HTML](postprocessing_enhancement_validation_plan.html)
- [후처리 및 모델 고도화 검증 계획 Markdown](postprocessing_enhancement_validation_plan.md)
- [후처리 실험 매트릭스 HTML](postprocessing_experiment_matrix.html)
- [후처리 실험 매트릭스 Markdown](postprocessing_experiment_matrix.md)
- [후처리 실험 매트릭스 CSV](postprocessing_experiment_matrix.csv)
- [Claude Code용 가격 예측 실험 인수인계](claude_code_experiment_handoff.md)
- [PP-AMW5 Warm 작가 메타/전시·갤러리 잔차 보정 요약](pp_amw5_warm_artist_meta_external_coefficient_correction_summary.md)
- [PP-AMW6 Warm 작가 메타 잔차 보정 반복 재검증 요약](pp_amw6_warm_artist_meta_residual_revalidation_summary.md)
- [후속 실험 참여용 후임 온보딩 문서](track6_junior_project_onboarding.md)
- [피처별 영향도 해석 및 실험 결과](track6_feature_influence_with_results.md)
- [Group E 작가 변수 실행 가능성 검토](group_e_artist_variable_execution_review.md)
- [Group F/G 작가 메타 조합 실행 전 검토](group_f_g_execution_review.md)
- [Group F/G 실행 결과 종합 HTML](group_f_g_execution_summary.html)
- [Group F/G 실행 결과 종합 Markdown](group_f_g_execution_summary.md)
- [Group F/G 실행 결과 종합 CSV](group_f_g_summary_table.csv)
- [Group H/I/J 중복 매핑](group_h_i_j_duplicate_mapping.md)
- [Group H/I/J 실행 결과 종합 HTML](group_h_i_j_execution_summary.html)
- [Group H/I/J 실행 결과 종합 Markdown](group_h_i_j_execution_summary.md)
- [Group H/I/J 실행 결과 종합 CSV](group_h_i_j_summary_table.csv)
- [작가 메타 feature 보강 보고서](../dataset/artist_meta_feature_augmentation_report.md)

| 날짜 | 실험 ID | 연결 가설 | 상태 | 요약 | 기록 |
|---|---|---|---|---|---|
| 2026-06-07 | PP-H28 | Cold 검색 provider agreement 기반 제한 보정 검증 | 실행 완료 | 검색 보정(h23)을 agreement로 제한 적용 검증. **검색 보정은 유효한 방어**(gallery_museum/social_blog cap0.2 test 3지표 모두 개선: 0.4313/0.929/3.139 vs base 0.4421/1.048/3.354)이나, **provider agreement 게이팅은 비현실**: high 등급 0(max score 0.648<0.70), cold 커버리지 18작가뿐, gate가 test에서 0행 변경(no-op). 결론: cap 기반 방어층 + 저신뢰 검수 플래그로, agreement 커버리지 확대는 별도 데이터 과제 | [요약](pp_h28_cold_search_provider_agreement_gated_correction_summary.md), [실험 보고서](../../../experiments/track6/PP-H28_cold_search_provider_agreement_gated_correction/reports/PP-H28_cold_search_provider_agreement_gated_correction.md), [산출물](../../../experiments/track6/PP-H28_cold_search_provider_agreement_gated_correction/outputs/test_metrics.csv) |
| 2026-06-07 | PP-COLD-ARTIFACT2 | Cold 하부 Quantile 모델 직렬화 (search-free 운영 변형) | 실행 완료 | v0.1 대표 PP-Y18이 search/external 피처 의존이라 raw-input 직렬화 불가 → 운영 피처 12개만으로 LightGBM Quantile(q10/q40/q50/q90) 학습·직렬화한 search-free 변형 `cold_prediction_v0.2_operational` 구축. 외부 API 의존 0, raw-input 추론 검증(diff 0.0). 정직한 지표: 대표 q50 test 0.4823/1.242/4.381, 방어 guard 0.4852/1.177/4.122 — search 기반 v0.1(0.4247/0.991/3.305)보다 확연히 약함 = 검색 신호 기여분 정량화 | [릴리스](../../../models/track6/cold_prediction_v0.2_operational/reports/cold_operational_v0_2_release.md), [정책](../../../models/track6/cold_prediction_v0.2_operational/config/cold_model_policy_v0_2.json), [설계서 참조 PP-COLD-ARTIFACT1](PP-COLD-ARTIFACT1_cold_policy_artifact_freeze_plan.md) |
| 2026-06-07 | PP-COLD-ARTIFACT1 | Cold 예측 정책 artifact 고정 | 실행 완료 | PP-QR4 검증 guard 방어층 + PP-Y18 대표 점예측 + PP-Y2 fallback + 신뢰도/범위 정책을 `models/track6/cold_prediction_v0.1/`로 고정. 직렬화 guard 파라미터(qwidth_q67=1.4612, gap_q50=0.0772, w=0.5) + 독립 후처리기. 후처리기가 PP-QR4 guard test 지표(0.4178/0.964/2.538) 정확 재현(diff 0.0). 정직한 범위: 후처리층만 실행 가능, 하부 Quantile 모델은 상류 참조 | [릴리스](../../../models/track6/cold_prediction_v0.1/reports/cold_artifact_release_v0_1.md), [정책](../../../models/track6/cold_prediction_v0.1/config/cold_model_policy_v0_1.json), [설계서](PP-COLD-ARTIFACT1_cold_policy_artifact_freeze_plan.md) |
| 2026-06-07 | PP-QR4 | Cold qwidth/guard 생존 후보 반복 split·artist holdout 재검증 | 실행 완료 | PP-QR3 test 생존 후보 2개를 row 5fold×12 + artist 5fold×12 + test bootstrap 400으로 재검증. segment(대표)는 artist holdout에서 붕괴(MdAPE 개선확률 row 0.97/artist 0.22) → 보류(작가 구성 의존). guard(방어)는 MAPE(1.00/0.98)·p95(0.98/0.85) 양 holdout 견고 + test MdAPE 비악화(0.4178) → **채택(MAPE/p95 방어 후보)**. test p95 3.31→2.54, MAPE 0.991→0.964 | [요약](pp_qr4_cold_qwidth_repeated_split_revalidation_summary.md), [실험 보고서](../../../experiments/track6/PP-QR4_cold_qwidth_repeated_split_revalidation/reports/PP-QR4_cold_qwidth_repeated_split_revalidation.md), [산출물](../../../experiments/track6/PP-QR4_cold_qwidth_repeated_split_revalidation/outputs/test_bootstrap_ci.csv) |
| 2026-06-07 | PP-SVC9 | svc 최정밀 매칭 게이트(fine-match-only) | 실행 완료 | PP-SVC8 진단대로 svc를 최정밀 매칭(artist_medium_support_size)에서만 쓰고 나머지는 pp_v8. 게이트 레벨은 구조적 결정, w_fine만 validation 선택(=1.0). 고정 test는 pp_v8 대비 개선(ΔMdAPE -0.0083)이나 0604는 악화(ΔMdAPE +0.0075). 0604 최정밀에서 svc는 중앙값 개선/MAPE 악화 = staleness가 최정밀에서도 tail 위험으로 잔존, 어떤 weight도 0604에서 pp_v8 동시지배 불가 → 기각, pp_v8 유지 | [요약](pp_svc9_warm_svc_fine_match_gate_summary.md), [실험 보고서](../../../experiments/track6/PP-SVC9_warm_svc_fine_match_gate/reports/PP-SVC9_warm_svc_fine_match_gate.md), [산출물](../../../experiments/track6/PP-SVC9_warm_svc_fine_match_gate/outputs/region_candidate_metrics.csv) |
| 2026-06-07 | PP-SVC8 | svc 비교가격 prior의 0604 악화 원인 분해 | 실행 완료 | PP-SVC7이 가리킨 svc staleness를 편향/분산/매칭이동으로 분해. 편향 아님(전역 bias 제거가 0604 악화). 악화 0.1552 = 매칭이동 53% + 그룹내 분산 47%. svc std 0.42→1.64(4배) 폭증, 레벨 통제 후에도 분산 증가. svc는 최정밀 매칭(artist_medium_support_size)에서만 pp_v8보다 강건(0604 MdAPE 0.143<0.171)이나 0604는 그 비율이 40.7%→11%로 급감, 거친 레벨에선 svc std가 pp_v8의 2.3~3배 | [요약](pp_svc8_svc_prior_staleness_diagnosis_summary.md), [실험 보고서](../../../experiments/track6/PP-SVC8_svc_prior_staleness_diagnosis/reports/PP-SVC8_svc_prior_staleness_diagnosis.md), [산출물](../../../experiments/track6/PP-SVC8_svc_prior_staleness_diagnosis/outputs/mix_within_decomposition.csv) |
| 2026-06-07 | PP-SVC7 | Warm 70:30 vs 운영 pp_v8 조건부 라우팅 + 0604 동시검증 | 실행 완료 | svc 신뢰도/disagreement 신호로 70:30과 pp_v8을 라우팅해 두 영역을 동시에 잡으려 했으나 기각. 영역별 최적 svc weight가 정반대(고정 test 0.6, 0604 0.0)이고 0604는 svc 비중↑일수록 단조 악화. validation 선택 라우터는 모두 고정 test는 통과하나 0604에서 열위(최선 0.2682 vs pp_v8 0.2298) → 70:30 vs pp_v8 차이는 라우팅 불가한 distribution shift. 운영 기본값 pp_v8 유지 근거 강화 | [요약](pp_svc7_warm_svc_ppv8_conditional_routing_summary.md), [실험 보고서](../../../experiments/track6/PP-SVC7_warm_svc_ppv8_conditional_routing/reports/PP-SVC7_warm_svc_ppv8_conditional_routing.md), [산출물](../../../experiments/track6/PP-SVC7_warm_svc_ppv8_conditional_routing/outputs/region_candidate_metrics.csv) |
| 2026-06-07 | PP-WHUBER11 | Warm 원인 보정 + MAPE guard + 과대예측 cap | 실행 완료 | PP-WHUBER10 MdAPE/p95 개선의 MAPE 악화를 제거. 과대예측 segment 한정 + 하향 전용 cap + global fallback 제거 + validation MAPE guard로 36/36 후보가 MAPE 비악화. 단 개선폭 marginal(대표 risk_pred test `0.1403/0.2744/0.8312`, MdAPE -0.14%/p95 -0.23%) → 보조 방어 후보, 대표 교체 보류 | [요약](pp_whuber11_warm_cause_correction_mape_guard_summary.md), [실험 보고서](../../../experiments/track6/PP-WHUBER11_warm_cause_correction_mape_guard/reports/PP-WHUBER11_warm_cause_correction_mape_guard.md), [산출물](../../../experiments/track6/PP-WHUBER11_warm_cause_correction_mape_guard/outputs/test_once_metrics.csv) |
| 2026-06-07 | PP-AMW6 | Warm 작가 메타 잔차 보정 반복 재검증 | 실행 완료 | PP-AMW5 상위 후보를 validation 작가 단위 12회 x 5fold와 test bootstrap 400회로 재검증. 작가 메타 Huber 후보는 test `0.1368/0.2746/0.8323`, 생년 구간 median 후보는 test `0.1381/0.2740/0.8191`로 목적별 후보 분리 | [요약](pp_amw6_warm_artist_meta_residual_revalidation_summary.md), [실험 보고서](../../../experiments/track6/PP-AMW6_warm_artist_meta_residual_revalidation/reports/result_report.md), [산출물](../../../experiments/track6/PP-AMW6_warm_artist_meta_residual_revalidation/outputs/repeated_validation_summary.csv) |
| 2026-06-07 | PP-AMW5 | Warm 작가 메타/전시·갤러리 잔차 보정 | 실행 완료 | 현재 Warm 1순위 후보 위에 작가 생년/활동량/판매중 작품 수/전시·갤러리 피처로 Huber 잔차 보정을 적용. 작가 메타 핵심 후보 test MdAPE/MAPE/p95 `0.1368/0.2746/0.8323`으로 기준 `0.1405/0.2748/0.8331` 대비 소폭 개선 | [요약](pp_amw5_warm_artist_meta_external_coefficient_correction_summary.md), [실험 보고서](../../../experiments/track6/PP-AMW5_warm_artist_meta_external_coefficient_correction/reports/result_report.md), [산출물](../../../experiments/track6/PP-AMW5_warm_artist_meta_external_coefficient_correction/outputs/all_candidate_metrics.csv) |
| 2026-05-29 | E5-2 | Group E5 보완 | 실행 완료 | 정규화된 국적값 기준으로 국적별 가격대와 오차 차이를 분석. Cold MdAPE 0.5128 → 0.5000, Warm MdAPE 0.4962 → 0.4969 | [결과 HTML](../../../experiments/track6/E5-2_nationality_group_effect/outputs/result_sheet.html), [README](../../../experiments/track6/E5-2_nationality_group_effect/README.md), [국적별 CSV](../../../experiments/track6/E5-2_nationality_group_effect/outputs/nationality_group_summary.csv) |
| 2026-05-29 | E5-1 | Group E5 보완 | 실행 완료 | 호수/난트 재료/난트 도구/난트 지지체를 통제한 뒤 국적 추가 효과를 재검증. Warm Huber MdAPE 0.4962 → 0.4899, Cold Quantile-LAD MdAPE 0.5128 → 0.4888 | [결과 HTML](../../../experiments/track6/E5-1_controlled_nationality_effect/outputs/result_sheet.html), [README](../../../experiments/track6/E5-1_controlled_nationality_effect/README.md), [조건 묶음 CSV](../../../experiments/track6/E5-1_controlled_nationality_effect/outputs/controlled_condition_summary.csv) |
| 2026-05-29 | E2-1 | Group E2 보완 | 실행 완료 | 같은 작가/같은 테스트셋에서 작가당 학습 작품 수를 5/10/20/30개로 제한해 Warm 안정성 비교. Huber MdAPE가 0.1947 → 0.1269로 개선 | [결과 HTML](../../../experiments/track6/E2-1_same_artist_learning_volume/outputs/result_sheet.html), [README](../../../experiments/track6/E2-1_same_artist_learning_volume/README.md) |
| 2026-05-28 | CM1 | Cold 모델군 검증 | 실행 완료 | Cold 상위 피처 5개 조합에서 모델만 변경해 비교, 종합 점수 기준 `작품 기본 피처 + 활동량/인지도` + CatBoost 1위 | [실험 HTML](../../../experiments/track6/CM1_cold_top_feature_model_family_compare/outputs/result_sheet.html), [README](../../../experiments/track6/CM1_cold_top_feature_model_family_compare/README.md), [점수 기준](composite_score_method.md) |
| 2026-05-28 | WM1 | Warm 모델군 검증 | 실행 완료 | Warm 상위 피처 5개 조합에서 모델만 변경해 비교, 종합 점수 기준 `작가명 + 전체 크기 + 작가 학습 작품 수` + Huber 1위 | [실험 HTML](../../../experiments/track6/WM1_warm_top_feature_model_family_compare/outputs/result_sheet.html), [README](../../../experiments/track6/WM1_warm_top_feature_model_family_compare/README.md), [점수 기준](composite_score_method.md) |
| 2026-05-28 | A-J-OPT-Analysis | A~J + OPT | 분석 완료 | Warm/Cold별 최고 피처 조합과 모델 후보 선정, OPT-C2/OPT-W3 추가 실행 포함 | [HTML](a_to_j_optimal_feature_model_analysis.html), [Markdown](a_to_j_optimal_feature_model_analysis.md) |
| 2026-05-27 | Group-HIJ-Run | Group H/I/J | 실행 완료 | H1/H5, I1/I2/I3/I5/I6, J1-J7 실행 및 H2/H3/H4/I4 중복 매핑 완료 | [HTML](group_h_i_j_execution_summary.html), [Markdown](group_h_i_j_execution_summary.md) |
| 2026-05-27 | Group-FG-Run | Group F/G | 실행 완료 | F1-F5, G1-G10 작가 메타/작품 조건 통제 실험 완료 | [HTML](group_f_g_execution_summary.html), [Markdown](group_f_g_execution_summary.md) |
| 2026-05-27 | Group-FG-Review | Group F/G | 검토 완료 | 작가 메타 조합/작품 조건 통제 실험 실행 전 중복·가능성 검토 | [기록](group_f_g_execution_review.md) |
| 2026-05-27 | Group-E-Prep | Group E | 준비 완료 | 작가 메타/전시 횟수 split 보강 및 실행 가능성 검토 | [기록](group_e_artist_variable_execution_review.md) |
| 2026-05-19 | T6-E010 | T6-H9, T6-H10 | 검증 완료 | 작가명+호수와 ln 변환 효과 확인 | [기록](2026-05-19_T6-E010_hedonic_artist_ho_log.md) |
| 2026-05-18 | T6-E009 | T6-H8 | 검증 완료 | 최종 artifact manifest 생성 | [기록](2026-05-18_T6-E009_final_artifact_manifest.md) |
| 2026-05-18 | T6-E008 | T6-H7 | 검증 완료 | 신뢰도/위험 구간 분석 완료 | [기록](2026-05-18_T6-E008_risk_policy_analysis.md) |
| 2026-05-18 | T6-E007 | T6-H6 | 검증 완료 | test 최종 확인 완료 | [기록](2026-05-18_T6-E007_test_confirmation.md) |
| 2026-05-18 | T6-E006 | T6-H6 | 부분 검증 | validation 후보 선정 완료 | [기록](2026-05-18_T6-E006_validation_candidate_selection.md) |
| 2026-05-18 | T6-E005 | T6-H5 | 검증 완료 | 피처 조합 ablation 완료 | [기록](2026-05-18_T6-E005_feature_combo_ablation.md) |
| 2026-05-18 | T6-E004 | T6-H4 | 검증 완료 | Cold 모델 비교 완료 | [기록](2026-05-18_T6-E004_cold_model_compare.md) |
| 2026-05-18 | T6-E003 | T6-H3 | 검증 완료 | Warm 작가 피처 ablation 완료 | [기록](2026-05-18_T6-E003_warm_artist_ablation.md) |
| 2026-05-18 | T6-E002 | T6-H2 | 검증 완료 | 구조-only baseline 완료 | [기록](2026-05-18_T6-E002_structure_only_baseline.md) |
| 2026-05-18 | T6-E001C | T6-H1 | 검증 완료 | feature/label 분리, 상태 `pass` | [기록](2026-05-18_T6-E001C_feature_label_pipeline.md) |
| 2026-05-18 | T6-E001B | T6-H1 | 검토 완료 | 컬럼 품질 검증, fail 0 / review 14 | [기록](2026-05-18_T6-E001B_column_quality_validation.md) |
| 2026-05-18 | T6-E001 | T6-H1 | 검증 완료 | Track6 name-corrected split 생성 및 검증, 상태 `pass` | [기록](2026-05-18_T6-E001_strict_split_generation.md) |
