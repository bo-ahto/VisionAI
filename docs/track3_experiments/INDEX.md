# Track 3 실험 기록 인덱스

- 목적: Track 3 실험 기록을 날짜 / 실험 ID 기준으로 빠르게 찾기 위한 목록
- 상태 값
- `채택`
- `보류`
- `중단`
- `재현완료`
- `종결`

## 기준 문서

- 문서 구조 안내
- [`docs/track3_docs_structure.md`](/Users/bo/VisionAI/docs/track3_docs_structure.md:1)
- 실험 계획서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 현재 의사결정 요약
- [`docs/track3_current_decision_summary.md`](/Users/bo/VisionAI/docs/track3_current_decision_summary.md:1)
- 가설 리스트
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 가설 요약표
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- 가설 결과 종합표
- [`docs/track3_hypothesis_result_summary.md`](/Users/bo/VisionAI/docs/track3_hypothesis_result_summary.md:1)
- 실험 결과 요약표
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)
- 재현 요약
- [`docs/track3_reproduction_summary_20260513.md`](/Users/bo/VisionAI/docs/track3_reproduction_summary_20260513.md:1)
- 실험 코드 감사
- [`docs/track3_experiment_code_audit_20260515.md`](/Users/bo/VisionAI/docs/track3_experiment_code_audit_20260515.md:1)

## 실험 목록

| 날짜 | 실험 ID | 상태 | 핵심 결론 | 기록 |
|---|---|---|---|---|
| 2026-05-12 | PR2_PR5_foundation_checks | 종결 | source 편향과 Cold baseline 재현성은 확인됐지만, blend 채택 근거는 약함 | [2026-05-12_pr2_pr5_foundation_checks.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-12_pr2_pr5_foundation_checks.md:1) |
| 2026-05-12 | PR8_PR15_exploratory_followups | 종결 | source conditional / reweight / homonym 정제는 열세, depth 정보는 유지 가치 확인 | [2026-05-12_pr8_pr15_exploratory_followups.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-12_pr8_pr15_exploratory_followups.md:1) |
| 2026-05-13 | repro_phase0_pr29 | 재현완료 | `Cold = LAD`, `Warm = tuned LightGBM` 재확인 | [2026-05-13_reproduction_log.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_reproduction_log.md:1) |
| 2026-05-13 | H1_size_representation_confirm | 종결 | 대표 크기 표현은 Warm에서 악화되어 전면 단순화 기각, `V0_all` 유지 | [2026-05-13_h1_size_representation_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h1_size_representation_confirm.md:1) |
| 2026-05-13 | H2_H3_H4_feature_foundation_confirm | 종결 | Cold 구조 baseline과 Warm 작가 정보 가치는 검증 완료, 파생 피처는 일부만 유지 | [2026-05-13_h2_h3_h4_feature_foundation_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h2_h3_h4_feature_foundation_confirm.md:1) |
| 2026-05-13 | H8_cold_2d_fallback_confirm | 종결 | Cold 2D fallback은 전체 Cold와 2D 구간 모두 악화되어 중단 | [2026-05-13_h8_cold_2d_fallback_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h8_cold_2d_fallback_confirm.md:1) |
| 2026-05-13 | H9_masking_robustness_confirm | 종결 | 마스킹 학습은 일부 크기 결측을 완화하지만 clean/재료 결측 악화가 커서 중단 | [2026-05-13_h9_masking_robustness_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h9_masking_robustness_confirm.md:1) |
| 2026-05-13 | H10_artist_history_feature_confirm | 종결 | 작가 이력 피처는 Warm 성능을 크게 개선하나 운영 전 temporal-safe 재계산이 필요함 | [2026-05-13_h10_artist_history_feature_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h10_artist_history_feature_confirm.md:1) |
| 2026-05-13 | H11_prediction_interval_confirm | 종결 | 가격 범위 출력은 Warm coverage 부족과 Cold 구간 폭 과대로 calibration 보완 필요 | [2026-05-13_h11_prediction_interval_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h11_prediction_interval_confirm.md:1) |
| 2026-05-13 | H12_artist_residual_confirm | 종결 | 잔차 구조는 직접 이력 모델과 유사하지만 약간 열세라 설명용 보조로 보류 | [2026-05-13_h12_artist_residual_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h12_artist_residual_confirm.md:1) |
| 2026-05-13 | H13_material_granularity_confirm | 종결 | 재료 flag/희소도 피처는 Cold 개선이 없고 Warm에서 악화되어 중단 | [2026-05-13_h13_material_granularity_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h13_material_granularity_confirm.md:1) |
| 2026-05-13 | H14_medium_size_combo_confirm | 종결 | 크기-재료 조합 피처는 Warm 소폭 개선이나 Cold 개선이 없어 중단 | [2026-05-13_h14_medium_size_combo_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h14_medium_size_combo_confirm.md:1) |
| 2026-05-13 | H15_missing_pattern_audit | 보류 | 현재 release split에는 핵심 입력 변수 결측이 없어 결측 패턴 피처 실험 불가 | [2026-05-13_h15_missing_pattern_audit.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h15_missing_pattern_audit.md:1) |
| 2026-05-13 | H16_temporal_safe_feature_audit | 보류 | 날짜 후보 컬럼이 없어 H10/H12 작가 이력 피처의 temporal-safe 재검증 불가 | [2026-05-13_h16_temporal_safe_feature_audit.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h16_temporal_safe_feature_audit.md:1) |
| 2026-05-13 | H17_artist_history_stability_confirm | 종결 | 작가 이력 피처 개선 효과는 3개 seed에서 안정적으로 유지됨 | [2026-05-13_h17_artist_history_stability_confirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h17_artist_history_stability_confirm.md:1) |
| 2026-05-13 | H18_interval_calibration_grid | 종결 | Warm 80% 예측 구간은 보정 가능성이 있으나 Cold는 구간 폭이 큼 | [2026-05-13_h18_interval_calibration_grid.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h18_interval_calibration_grid.md:1) |
| 2026-05-13 | H19_H22_ho_feature_ablation | 종결 | 호수 세분화와 대형 호수 flag는 개선 신호가 있고, 전체 호수 피처 조합이 Warm/Cold 모두 최고 | [2026-05-13_h19_h22_ho_feature_ablation.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h19_h22_ho_feature_ablation.md:1) |
| 2026-05-13 | H23_H25_size_3d_relative_ablation | 종결 | 3D/상대 크기 피처는 Cold를 개선하지만 Warm을 악화시켜 Warm/Cold 피처 분리 필요 | [2026-05-13_h23_h25_size_3d_relative_ablation.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h23_h25_size_3d_relative_ablation.md:1) |
| 2026-05-13 | H26_H28_size_feature_reduction | 종결 | `width_cm`, `height_cm` 제거는 가능하지만 `estimated_ho`만 남기는 단순화는 Cold에서 악화되어 기각 | [2026-05-13_h26_h28_size_feature_reduction.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h26_h28_size_feature_reduction.md:1) |
| 2026-05-14 | H29_H30_feature_policy_slice_analysis | 종결 | Warm/Cold 피처 분리 필요, Cold 개선은 3D slice에 집중되고 2D는 악화 | [2026-05-14_h29_h30_feature_policy_slice_analysis.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h29_h30_feature_policy_slice_analysis.md:1) |
| 2026-05-14 | H31_warm_champion_feature_retest | 종결 | H17 Warm champion 기준에서도 호수+3D 피처 조합이 `0.1147 -> 0.1090`으로 개선 | [2026-05-14_h31_warm_champion_feature_retest.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h31_warm_champion_feature_retest.md:1) |
| 2026-05-14 | H32_cold_3d_conditional_fallback | 종결 | Cold 3D 조건부 fallback이 2D 악화 없이 전체 Cold `0.3163 -> 0.2786`으로 개선 | [2026-05-14_h32_cold_3d_conditional_fallback.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h32_cold_3d_conditional_fallback.md:1) |
| 2026-05-14 | H33_pr7_release_warm_reconfirm | 종결 | PR7 운영 가능 피처는 release split에서 `0.2251`로 H31 `0.1090`을 넘지 못함 | [2026-05-14_h33_pr7_release_warm_reconfirm.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h33_pr7_release_warm_reconfirm.md:1) |
| 2026-05-14 | H34_H43_followup_validation | 종결 | Warm/Cold 분리 정책 유지, 저이력 Warm과 Cold 대형/3D는 신뢰도/보정 후보로 관리 | [2026-05-14_h34_h43_followup_validation.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h34_h43_followup_validation.md:1) |
| 2026-05-14 | H44_H47_priority_followups | 종결 | H45 Cold 3D 중간 부피 예외와 H47 Warm 이력 신뢰도 등급은 후보, H44 fallback은 기각 | [2026-05-14_h44_h47_priority_followups.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h44_h47_priority_followups.md:1) |
| 2026-05-14 | H48_H60_pending_followups | 종결 | Warm/Cold 신뢰도와 가격 범위 정책 근거를 보강했고, H57/H58은 multi-seed 재검증으로 이관 | [2026-05-14_h48_h60_pending_followups.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h48_h60_pending_followups.md:1) |
| 2026-05-14 | H61_H65_model_improvement_followups | 종결 | H62 Warm 튜닝은 H66에서 채택, H61/H63/H64/H65는 최종 후보 대체 근거 부족으로 미채택 | [2026-05-14_h61_h65_model_improvement_followups.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h61_h65_model_improvement_followups.md:1) |
| 2026-05-14 | H66_warm_lgbm_retune_multiseed | 종결 | H62 larger-low-lr Warm 후보가 multi-seed 평균 `0.1051`로 current-like `0.1090`보다 개선 | [2026-05-14_h66_warm_lgbm_retune_multiseed.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h66_warm_lgbm_retune_multiseed.md:1) |
| 2026-05-14 | H67_warm_feature_extension_multiseed | 종결 | H57/H58 피처 확장은 H66을 대체할 만큼 강하지 않아 Warm 후보는 H66 유지 | [2026-05-14_h67_warm_feature_extension_multiseed.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h67_warm_feature_extension_multiseed.md:1) |
| 2026-05-14 | H68_warm_routing_threshold | 종결 | Warm 사용 기준을 3건/5건 이상으로 올리면 악화되어 `artist_train_count >= 1` 기준 유지 | [2026-05-14_h68_warm_routing_threshold.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h68_warm_routing_threshold.md:1) |
| 2026-05-14 | H69_price_range_calibration_close | 종결 | H46을 닫고 Warm 등급별/Cold 조건별 가격 범위 정책을 확정 | [2026-05-14_h69_price_range_calibration_close.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h69_price_range_calibration_close.md:1) |
| 2026-05-15 | H70_H72_operational_revalidation | 종결 | 내부 calibration으로 가격 범위 정책을 재확인했고, Cold 3D 중간 부피 예외와 combo 정리는 미채택 | [2026-05-15_h70_h72_operational_revalidation.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-15_h70_h72_operational_revalidation.md:1) |
| 2026-05-13 | PR20_PR29_confirmatory_suite | 종결 | mini 신호의 다수가 confirm에서 기각, 운영 구조 유지 | [2026-05-13_pr20_pr29_confirmatory_suite.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_pr20_pr29_confirmatory_suite.md:1) |
| 2026-05-13 | PR17_PR18_PR19_depth_branch | 종결 | `Cold 2D` mini 신호는 있었으나 H8 release fallback에서 중단 | [2026-05-13_pr17_pr18_pr19_depth_branch.md](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_pr17_pr18_pr19_depth_branch.md:1) |
