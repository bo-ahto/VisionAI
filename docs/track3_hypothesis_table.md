# Track 3 가설 요약표

- 기록 유형:
- 가설 상태 관리 표
- 기준 설명 문서
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 가설별 결과 종합
- [`docs/track3_hypothesis_result_summary.md`](/Users/bo/VisionAI/docs/track3_hypothesis_result_summary.md:1)

| 가설 ID | 세부 목표 | 가설 요약 | 현재 상태 | 검증 강도 | 관련 실험 | 현재 판단 | 후속 필요 |
|---|---|---|---|---|---|---|---|
| H1 | G4 운영 가능 피처 선정 / G6 안정성 확인 | 크기 정보는 대표 표현으로 정리하는 것이 더 안정적일 것이다 | 검증 완료 | 기초/탐색+확증 | `baseline`, `PR20`, `PR21`, `H1_size_representation_confirm` | 대표 표현 전면 단순화 기각, `V0_all` 유지 | 없음 |
| H2 | G1 기본 예측 가능성 / G3 Cold 성능 개선 | 작가 정보 없이도 작품 구조 정보만으로 Cold 예측이 가능할 것이다 | 검증 완료 | 기초/탐색+확증 | `baseline`, `train_linear_cold`, `train_tree_cold`, `PR1`, `PR4`, `PR15`, `H2_H3_H4_feature_foundation_confirm` | Cold 구조 변수 baseline 성립, 약점 slice는 후속 가설로 이관 | 없음 |
| H3 | G2 Warm 성능 개선 | Warm에서는 작가 정보를 포함할 때 성능이 유의미하게 좋아질 것이다 | 검증 완료 | 기초/탐색+확증 | `train_linear_warm`, `train_tree_warm`, `PR7`, `H3_artist_feature_confirm`, `H2_H3_H4_feature_foundation_confirm` | 작가명과 작가 작품 수 피처 모두 Warm 개선 확인 | 없음 |
| H4 | G4 운영 가능 피처 선정 | 운영 가능한 파생 피처가 추가 성능 개선을 줄 것이다 | 검증 완료 | 기초/탐색+확증 | `PR7`, `PR8`, `PR9`, `PR22`, `PR23`, `H2_H3_H4_feature_foundation_confirm` | `artist_works_log`는 유지, 나머지 파생 피처 확장은 제한 | H13~H15로 이관 |
| H5 | G2 Warm 성능 개선 / G6 안정성 확인 | Warm에서는 비선형 트리 모델이 선형보다 우세할 것이다 | 검증 완료 | 기초/탐색+확증 | `train_linear_warm`, `train_tree_warm`, `PR24`, `PR1` | `tuned LightGBM` 우세 | 낮음 |
| H6 | G3 Cold 성능 개선 / G6 안정성 확인 | Cold에서는 robust 선형 계열이 더 안정적일 것이다 | 검증 완료 | 기초/탐색+확증 | `train_linear_cold`, `train_tree_cold`, `PR1`, `PR4`, `PR9` | robust 선형 계열 우세 | 낮음 |
| H7 | G3 Cold 성능 개선 / G5 약점 구간 보완 | 2D / 3D 분기는 특정 약점 구간 보완용으로 더 적합할 것이다 | 검증 완료 | 기초/탐색+확증 | `PR11`, `PR15`, `PR17`, `PR18`, `PR19`, `H8_cold_2d_fallback_confirm` | mini 신호는 있었지만 release fallback에서 채택 실패 | 없음 |
| H8 | G3 Cold 성능 개선 / G5 약점 구간 보완 | Cold 2D 한정 fallback이 전체 모델 교체보다 효율적일 것이다 | 검증 완료 | release split 검증 | `H8_cold_2d_fallback_confirm` | 전체 Cold와 Cold 2D 모두 악화되어 중단 | 없음 |
| H9 | G7 결측/정보량/신뢰도 대응 | 일부 정보를 의도적으로 가리고 학습한 모델이 결측 상황에서 더 잘 버틸 것이다 | 검증 완료 | release split 검증 | `H9_masking_robustness_confirm` | 크기 결측 일부 개선은 있으나 clean/재료 결측 악화가 커서 마스킹 학습 중단 | H15는 운영 결측 확보 후 재검증 |
| H10 | G2 Warm 성능 개선 / G4 운영 가능 피처 선정 | 작가명 자체보다 거래 이력 기반 구조화 피처가 Warm에서 더 안정적일 것이다 | 검증 완료 | 성능 검증 완료 / temporal-safe 필요 | `H10_artist_history_feature_confirm` | 작가 이력 피처가 Warm `0.2289 -> 0.1204`로 크게 개선, temporal-safe 재계산 필요 | H12 residual 구조로 확장 |
| H11 | G7 결측/정보량/신뢰도 대응 | 정보량에 따라 가격 범위와 신뢰도를 함께 주는 방식이 더 실용적일 것이다 | 검증 완료 | test 진단 / H70 재검증 필요 | `H11_prediction_interval_confirm`, `PR3` | Warm coverage 부족, Cold 구간 폭 과대로 보조 출력 후보 보류 | calibration 보완 필요 |
| H12 | G2 Warm 성능 개선 / G6 안정성 확인 | 작가 기본 가격대와 작품별 편차를 분리한 2단계 구조가 일부 Warm에서 더 설명력 있을 것이다 | 검증 완료 | 성능 검증 완료 / temporal-safe 필요 | `H12_artist_residual_confirm` | 잔차 구조는 직접 모델과 유사하나 약간 열세, 설명용 보조 구조로 보류 | temporal-safe 재검증 필요 |
| H13 | G3 Cold 성능 개선 / G5 약점 구간 보완 / G4 운영 가능 피처 선정 | 재료를 더 세분화한 피처가 Cold 정확도를 개선할 것이다 | 검증 완료 | release split 검증 | `H13_material_granularity_confirm` | Cold 개선 없음, Warm 악화로 재료 flag/희소도 피처 중단 | 없음 |
| H14 | G3 Cold 성능 개선 / G5 약점 구간 보완 / G4 운영 가능 피처 선정 | 크기와 재료의 조합 효과가 단독 피처보다 가격을 더 잘 설명할 것이다 | 검증 완료 | release split 검증 | `H14_medium_size_combo_confirm` | Warm 소폭 개선은 있으나 Cold 개선 없어 조합 피처 중단 | 없음 |
| H15 | G7 결측/정보량/신뢰도 대응 | 결측 패턴 자체가 신뢰도와 가격 오차를 설명할 것이다 | 보류 | 보류/데이터 조건 미충족 | `H15_missing_pattern_audit` | 현재 release split 핵심 입력 결측 0건, 결측 패턴 피처 실험 불가 | 운영 결측 데이터 확보 또는 H9 masking 후 재검증 |
| H16 | G4 운영 가능 피처 선정 / G6 안정성 확인 | 작가 이력 피처는 거래일 기준으로 다시 계산할 수 있어야 운영 피처로 채택 가능하다 | 보류 | 보류/데이터 조건 미충족 | `H16_temporal_safe_feature_audit` | 현재 release split에 날짜 컬럼이 없어 temporal-safe 재검증 불가 | 거래일/등록일 컬럼 확보 필요 |
| H17 | G2 Warm 성능 개선 / G6 안정성 확인 | 작가 이력 피처의 Warm 개선 효과는 반복 학습에서도 안정적으로 유지될 것이다 | 검증 완료 | 성능 검증 완료 / temporal-safe 필요 | `H17_artist_history_stability_confirm`, `H31_warm_champion_feature_retest` | 작가 이력 피처는 안정적이고, H31에서 호수/3D 피처를 더해 `0.1090`까지 개선 | H16 조건 해결 후 운영 재검증 |
| H18 | G7 결측/정보량/신뢰도 대응 | 예측 구간 calibration quantile을 조정하면 Warm coverage 부족을 줄일 수 있다 | 검증 완료 | release split 검증 | `H18_interval_calibration_grid` | Warm 80% 구간은 q0.90으로 보완 가능, Cold는 폭 과대 | 최종 모델 확정 후 calibration 재수행 |
| H19 | G2 Warm 성능 개선 / G3 Cold 성능 개선 / G4 운영 가능 피처 선정 | 호수 구간을 더 세분화하면 Warm/Cold 성능이 개선될 것이다 | 검증 완료 | release split 검증 | `H19_H22_ho_feature_ablation`, `H31_warm_champion_feature_retest` | 세분화 호수 구간은 H31 Warm champion 기준에서도 개선 유지 | H31 Warm 후보에 반영 |
| H20 | G3 Cold 성능 개선 / G5 약점 구간 보완 / G4 운영 가능 피처 선정 | 큰 호수/초대형 호수 여부는 가격 예측에 별도 신호를 줄 것이다 | 검증 완료 | release split 검증 | `H19_H22_ho_feature_ablation` | 대형 호수 flag가 Cold를 소폭 개선, Warm 영향은 거의 없음 | H30에서 대형 slice 확인 |
| H21 | G3 Cold 성능 개선 / G5 약점 구간 보완 / G4 운영 가능 피처 선정 | 실제 면적과 추정 호수의 불일치 정도가 가격 오차를 설명할 것이다 | 검증 완료 | release split 검증 | `H19_H22_ho_feature_ablation` | 일관성 피처 단독은 Cold 악화, 전체 조합에서는 보조 가능성 | 단독 채택 보류, H30에서 재확인 |
| H22 | G2 Warm 성능 개선 / G3 Cold 성능 개선 / G4 운영 가능 피처 선정 | 호수는 선형값보다 로그값이나 구간값으로 쓰는 것이 더 안정적일 것이다 | 검증 완료 | release split 검증 | `H19_H22_ho_feature_ablation`, `H31_warm_champion_feature_retest` | 호수 전체 조합은 H31 Warm champion 기준에서도 개선 유지 | H31 Warm 후보에 반영 |
| H23 | G5 약점 구간 보완 / G4 운영 가능 피처 선정 | 크기 구간/극단 크기 피처가 Warm/Cold 성능을 개선할 것이다 | 검증 완료 | release split 검증 | `H23_H25_size_3d_relative_ablation` | 크기 구간 피처는 Warm / Cold 모두 개선 없음 | 중단 |
| H24 | G3 Cold 성능 개선 / G5 약점 구간 보완 | 3D 작품은 면적보다 부피/긴 변 피처가 더 설명력이 있을 것이다 | 검증 완료 | release split 검증 | `H23_H25_size_3d_relative_ablation`, `H32_cold_3d_conditional_fallback` | 3D 피처는 Cold 3D에서 강하게 개선되며, H32 조건부 적용으로 2D 악화 없이 채택 가능 | Cold 3D 조건부 후보에 반영 |
| H25 | G3 Cold 성능 개선 / G5 약점 구간 보완 | 같은 재료 안에서의 상대적 크기 순위가 절대 크기보다 가격 설명력이 있을 것이다 | 검증 완료 | release split 검증 | `H23_H25_size_3d_relative_ablation` | Cold 개선, Warm 악화 | Cold 채택 후보 |
| H26 | G4 운영 가능 피처 선정 / G6 안정성 확인 | 크기 관련 피처가 중복되어 있어 일부를 제거하면 성능이 유지되거나 안정성이 좋아질 것이다 | 검증 완료 | release split 검증 | `H26_H28_size_feature_reduction` | `width_cm`, `height_cm` 제거안이 Cold 소폭 개선, Warm 거의 유지 | H29에서 최종 공통 피처 정리 |
| H27 | G4 운영 가능 피처 선정 / G6 안정성 확인 | `estimated_ho`와 `log_area` 중 하나만 남겨도 성능 차이가 크지 않을 것이다 | 검증 완료 | release split 검증 | `H26_H28_size_feature_reduction` | `estimated_ho`만 남기는 안은 Cold 악화로 기각, `log_area` 중심 축소는 제한적 허용 | H22 결과와 함께 최종 호수 표현 정리 |
| H28 | G4 운영 가능 피처 선정 / G6 안정성 확인 | `width_cm`, `height_cm`는 `log_area`, `aspect_ratio`로 대체 가능할 것이다 | 검증 완료 | release split 검증 | `H26_H28_size_feature_reduction` | `log_area + aspect_ratio` 대체 가능성 확인, `aspect_ratio` 제거는 Warm 악화 | H29에서 Warm/Cold 채택 기준 분리 검토 |
| H29 | G8 최종 후보 정책 결정 | Warm과 Cold에서 필요한 크기/호수 피처 구성이 다를 것이다 | 검증 완료 | release split 검증 | `H29_H30_feature_policy_slice_analysis`, `H31_warm_champion_feature_retest`, `H32_cold_3d_conditional_fallback` | Warm은 H31 호수+3D 후보, Cold는 H32 3D 조건부 fallback으로 분리 | production 후보 정리 |
| H30 | G5 약점 구간 보완 / G8 최종 후보 정책 결정 | 파생 피처는 전체 성능보다 약점 slice에서만 개선될 수 있다 | 검증 완료 | release split 검증 | `H29_H30_feature_policy_slice_analysis`, `H32_cold_3d_conditional_fallback` | 3D 개선이 특정 slice에 집중됨을 확인했고, 조건부 fallback으로 2D 악화를 방지 | production 후보 정리 |
| H31 | G2 Warm 성능 개선 / G8 최종 후보 정책 결정 | H17 Warm champion에 호수/3D 피처를 추가하면 Warm 성능이 더 좋아질 것이다 | 검증 완료 | multi-seed 재검증 | `H31_warm_champion_feature_retest` | 호수+3D 전체 조합이 Warm `0.1147 -> 0.1090`으로 개선 | production 후보 반영 검토 |
| H32 | G3 Cold 성능 개선 / G5 약점 구간 보완 / G8 최종 후보 정책 결정 | Cold 3D 피처는 전체 적용보다 3D 작품에만 조건부 적용하는 것이 더 안정적일 것이다 | 검증 완료 | release split 검증 | `H32_cold_3d_conditional_fallback` | 조건부 fallback이 2D 악화 없이 Cold `0.3163 -> 0.2786`으로 개선 | production 후보 반영 검토 |
| H33 | G2 Warm 성능 개선 / G6 안정성 확인 | PR7 Warm 최고 탐색 기록은 release split / 운영 가능 피처 기준에서도 유지될 것이다 | 검증 완료 | release split 검증 | `H33_pr7_release_warm_reconfirm` | PR7 운영 가능 피처 최고 `0.2251`로 H31 `0.1090`보다 낮아 최종 후보 대체 실패 | 없음 |
| H34 | G3 Cold 성능 개선 / G5 약점 구간 보완 | Cold 3D 조건부 모델은 모든 3D 작품보다 특정 3D 구간에서 효과가 클 것이다 | 검증 완료 | release split 검증 | `H34_H43_followup_validation` | 3D 전체는 개선되지만 중간 부피 3D는 악화 신호가 있어 세부 조건화 여지 있음 | 3D 중간 부피 구간 추가 분석 |
| H35 | G8 최종 후보 정책 결정 / G6 안정성 확인 | Warm/Cold를 하나의 모델로 합치는 것보다 분리 모델을 쓰는 것이 안정적일 것이다 | 검증 완료 | release split 검증 | `H34_H43_followup_validation` | 단일 H31형 모델 Cold `0.5938`로 H32 `0.2786`보다 크게 열세 | Warm/Cold 분리 정책 유지 |
| H36 | G2 Warm 성능 개선 / G5 약점 구간 보완 | H31 Warm 후보는 작가별 학습 작품 수가 적은 작가에서 성능이 불안정할 수 있다 | 검증 완료 | release split 검증 | `H34_H43_followup_validation` | 작가 1건 구간 Warm `0.2466`, 51건 이상 구간 `0.0621`로 차이 큼 | 저이력 작가 신뢰도 경고 검토 |
| H37 | G7 결측/정보량/신뢰도 대응 / G2 Warm 성능 개선 | 예측 오차는 작품 정보량보다 작가 학습 이력 수에 크게 영향을 받을 것이다 | 검증 완료 | release split 검증 | `H34_H43_followup_validation` | artist_works_log와 Warm APE Spearman `-0.2423`, 이력이 많을수록 오차 감소 경향 | 신뢰도 점수 후보로 유지 |
| H38 | G4 운영 가능 피처 선정 / G2 Warm 성능 개선 | artist_name_ko 자체보다 구조화된 작가 이력 피처가 운영 안정성이 높을 것이다 | 검증 완료 | 성능 검증 완료 / temporal-safe 필요 | `H34_H43_followup_validation` | 작가명만 `0.2273`, 이력만 `0.1120`, 작가명+이력 `0.1002` | H16 해결 전까지 이력 피처 운영성 재검증 필요 |
| H39 | G5 약점 구간 보완 / G7 신뢰도 대응 | 대형 작품은 일반 작품과 다른 가격 구조를 가지므로 별도 보정이 필요하다 | 검증 완료 | release split 검증 | `H34_H43_followup_validation` | Cold 대형 호수 `0.4448`, 초대형 호수 `0.5412`로 전체 Cold보다 약함 | Cold 대형 작품 경고/보정 후보 |
| H40 | G3 Cold 성능 개선 / G4 운영 가능 피처 선정 | Cold에서는 재료보다 크기/형태 피처가 더 중요한 설명 변수일 것이다 | 검증 완료 | release split 검증 | `H34_H43_followup_validation` | 재료 제거 `0.4112`, 크기/호수 제거 `0.4809`로 둘 다 중요하며 크기/호수 영향이 더 큼 | Cold 기본 피처 유지 |
| H41 | G6 모델 안정성 확인 / G8 최종 후보 정책 결정 | 현재 최적 후보는 반복 실행에서도 순위가 크게 바뀌지 않을 것이다 | 검증 완료 | multi-seed 재검증 | `H34_H43_followup_validation` | H31 3 seed 평균 Warm `0.1090` 수준 유지, H32는 deterministic 기준 유지 | 후보 안정성 유지 |
| H42 | G7 신뢰도 대응 / G5 약점 구간 보완 | 예측값이 크게 벗어나는 작품은 사전에 탐지 가능한 패턴이 있다 | 검증 완료 | release split 검증 | `H34_H43_followup_validation` | Cold 큰 오차 상위 10%는 3D 비율 `72.8%`, log_area 중앙값 `8.79`로 대형/3D 집중 | high-risk flag 후보 |
| H43 | G7 신뢰도 대응 / G8 최종 후보 정책 결정 | 최종 서비스에서는 단일 가격보다 가격 범위를 함께 제시하는 것이 더 안전하다 | 검증 완료 | release split 검증 | `H34_H43_followup_validation` | 90% 단순 로그 오차폭은 Warm `0.666`, Cold `1.070`으로 Cold 범위가 훨씬 넓음 | 최종 후보 확정 후 calibration 필요 |
| H44 | G2 Warm 성능 개선 / G7 신뢰도 대응 / G8 최종 후보 정책 결정 | Warm 저이력 작가에는 일반 Warm 모델보다 보수적 fallback이 더 안정적일 것이다 | 검증 완료 | release split 검증 | `H44_H47_priority_followups` | 구조-only fallback은 저이력 Warm에서도 H31보다 악화, 작가 1건 구간 `+0.2549` | fallback 기각, H31 유지 |
| H45 | G3 Cold 성능 개선 / G5 약점 구간 보완 / G8 최종 후보 정책 결정 | Cold 3D 중간 부피 구간은 3D fallback보다 기본 Cold 모델이 더 안정적일 것이다 | 검증 완료 | release split 검증 | `H44_H47_priority_followups` | 중간 부피 3D는 `0.2238 -> 0.1912`, 전체 Cold `0.2786 -> 0.2765`로 소폭 개선 | 조건부 예외 후보 |
| H46 | G7 신뢰도 대응 / G8 최종 후보 정책 결정 | High-risk 작품에는 가격 범위를 넓게 주는 방식이 실제 포함률을 개선할 것이다 | 검증 완료 | release split 검증 | `H44_H47_priority_followups`, `H69_price_range_calibration_close` | Warm D와 Cold 2D/대형/초대형은 별도 넓은 가격 범위가 필요함 | 최종 운영 정책에 반영 |
| H47 | G7 신뢰도 대응 / G2 Warm 성능 개선 | artist_works_log만으로도 Warm 신뢰도 등급을 만들 수 있을 것이다 | 검증 완료 | release split 검증 | `H44_H47_priority_followups` | 이력 등급별 Warm median APE가 `0.0621 -> 0.0759 -> 0.1350 -> 0.1608`로 단계적 악화 | Warm 신뢰도 등급 후보 |
| H48 | G7 신뢰도 대응 / G8 최종 후보 정책 결정 | Cold high-risk 기준을 더 좁게 잡으면 가격 범위 정책이 더 안정적일 것이다 | 검증 완료 | release split 검증 | `H48_H60_pending_followups` | `large_ho`, `very_large_area`, `extra_large_ho`는 high-risk 기준으로 유효, 단순 3D 여부는 부적합 | 운영 출력 정책에 반영 |
| H49 | G5 약점 구간 보완 / G8 최종 후보 정책 결정 | Cold 3D 중간 부피 예외는 median APE 개선보다 tail risk 악화를 기준으로 채택 여부를 판단해야 한다 | 검증 완료 | release split 검증 | `H48_H60_pending_followups` | median은 `0.2786 -> 0.2765`로 개선되지만 p95가 `1.4860 -> 1.6229`로 악화되어 채택 보류 | tail 기준 완화 없이는 미채택 |
| H50 | G7 신뢰도 대응 / G2 Warm 성능 개선 | Warm 신뢰도 등급은 artist_count 구간보다 p90 APE 기준으로 재구성하는 것이 더 실용적일 것이다 | 검증 완료 | release split 검증 | `H48_H60_pending_followups` | 작가 이력 구간별 median/p95 오차가 단계적으로 벌어져 신뢰도 등급 근거 확인 | 운영 등급 정책에 반영 |
| H51 | G7 신뢰도 대응 / G8 최종 후보 정책 결정 | Warm 신뢰도 등급과 가격 범위를 결합하면 사용자에게 더 안정적인 출력 정책을 만들 수 있다 | 검증 완료 | release split 검증 | `H48_H60_pending_followups` | 저이력 D 등급은 전역 width coverage가 부족해 별도 넓은 가격 범위가 필요함 | 최종 calibration 때 반영 |
| H52 | G7 신뢰도 대응 / G3 Cold 성능 개선 | Cold에서는 단일 가격 범위보다 모델 조건별 가격 범위가 더 적절할 것이다 | 검증 완료 | release split 검증 | `H48_H60_pending_followups` | Cold 2D/대형/초대형은 전역 width coverage 부족, 조건별 width가 필요함 | 최종 calibration 때 반영 |
| H57 | G2 Warm 성능 개선 | Warm에서는 작가 이력 피처를 더 세분화하면 성능이 개선될 것이다 | 검증 완료 | multi-seed 재검증 | `H48_H60_pending_followups`, `H67_warm_feature_extension_multiseed` | multi-seed 평균 `0.1051 -> 0.1032`로 개선 신호는 있으나 채택 기준 미달, p95 소폭 악화 | 현재 후보에는 미반영 |
| H58 | G2 Warm 성능 개선 / G4 운영 가능 피처 선정 | Warm에서는 작가별 가격대와 작품 크기의 상호작용 피처가 성능을 개선할 것이다 | 검증 완료 | multi-seed 재검증 | `H48_H60_pending_followups`, `H67_warm_feature_extension_multiseed` | multi-seed 평균 `0.1092`로 H66보다 악화되어 기각 | 없음 |
| H59 | G3 Cold 성능 개선 / G4 운영 가능 피처 선정 | Cold에서는 재료별 별도 스케일 보정이 성능을 개선할 것이다 | 검증 완료 | release split 검증 | `H48_H60_pending_followups` | best `0.2783`으로 H32 `0.2786` 대비 개선 폭이 너무 작고 within-30% 악화 | 채택 보류 |
| H60 | G3 Cold 성능 개선 / G4 운영 가능 피처 선정 | Cold에서는 medium_category와 support_category 조합을 더 정리하면 성능이 개선될 것이다 | 검증 완료 | release split 검증 | `H48_H60_pending_followups` | combo base와 combo+3D 모두 H32보다 악화되어 기각 | 없음 |
| H61 | G3 Cold 성능 개선 / G5 약점 구간 보완 | Cold에서는 비선형 모델이 전체는 약해도 특정 slice에서는 선형보다 우세할 것이다 | 검증 완료 | release split 검증 | `H61_H65_model_improvement_followups` | tree expert는 전체/slice 모두 악화, 3D 적용 시 Cold `0.4776` | tree expert 기각 |
| H62 | G2 Warm 성능 개선 / G6 안정성 확인 | Warm에서는 LightGBM 튜닝을 H31 피처 기준으로 다시 하면 성능이 개선될 것이다 | 검증 완료 | multi-seed 재검증 | `H61_H65_model_improvement_followups`, `H66_warm_lgbm_retune_multiseed` | multi-seed에서 larger-low-lr `0.1051`, current-like `0.1090`보다 개선 | Warm 후보에 반영 |
| H63 | G3 Cold 성능 개선 / G6 안정성 확인 | Cold LAD의 규제 강도 alpha를 조정하면 성능과 안정성이 개선될 것이다 | 검증 완료 | release split 검증 | `H61_H65_model_improvement_followups` | alpha 증가 시 Cold `0.3163 -> 0.3343~0.3901`로 악화 | alpha 튜닝 기각 |
| H64 | G3 Cold 성능 개선 / G6 안정성 확인 | Cold 예측값을 robust ensemble로 결합하면 tail risk가 줄어들 것이다 | 검증 완료 | release split 검증 | `H61_H65_model_improvement_followups` | Ridge base `0.3061`은 LAD base보다 좋지만 H32 조건부 후보 `0.2786`을 대체하지 못함 | 미채택 |
| H65 | G2 Warm 성능 개선 / G5 약점 구간 보완 | Warm 예측값과 작가별 기준가격을 blending하면 저이력 작가 성능이 개선될 것이다 | 검증 완료 | release split 검증 | `H61_H65_model_improvement_followups` | graded blending 전체 개선은 `0.1084 -> 0.1083`로 미미하고 저이력 개선 목적도 충족하지 못함 | 미채택 |
| H66 | G2 Warm 성능 개선 / G6 안정성 확인 / G8 최종 후보 정책 결정 | H62의 Warm LightGBM 재튜닝 개선 신호는 multi-seed에서도 유지될 것이다 | 검증 완료 | multi-seed 재검증 | `H66_warm_lgbm_retune_multiseed` | larger-low-lr 평균 `0.1051`, current-like 평균 `0.1090`, delta `-0.0039` | Warm 최종 후보 갱신 |
| H67 | G2 Warm 성능 개선 / G6 안정성 확인 | H57/H58의 Warm 피처 확장 개선 신호는 multi-seed에서도 유지될 것이다 | 검증 완료 | multi-seed 재검증 | `H67_warm_feature_extension_multiseed` | H57은 개선 신호가 있으나 채택 기준 미달, H58은 악화 | H66 Warm 후보 유지 |
| H68 | G2 Warm 성능 개선 / G7 신뢰도 대응 / G8 최종 후보 정책 결정 | Warm 모델 사용 기준을 작가 학습 작품 수 3건/5건 이상으로 올리면 더 안정적일 것이다 | 검증 완료 | multi-seed 재검증 | `H68_warm_routing_threshold` | 기준을 올릴수록 성능 악화, 저이력 작가도 Cold fallback보다 Warm이 우세 | `artist_train_count >= 1` 유지, 저이력은 신뢰도 경고 |
| H70 | G7 신뢰도 대응 / G8 최종 후보 정책 결정 | 가격 범위 calibration은 test residual이 아니라 내부 calibration split으로 계산해도 유지될 것이다 | 검증 완료 | 운영 전 재검증 완료 | `H70_H72_operational_revalidation` | Warm 전체 coverage `0.821`, Cold 전체 coverage `0.855`로 조건별 가격 범위 정책 유지 가능 | 운영 pipeline에 calibration split 고정 |
| H71 | G3 Cold 성능 개선 / G5 약점 구간 보완 / G8 최종 후보 정책 결정 | Cold 3D 중간 부피 예외는 train 기준 threshold로 정해도 유효할 것이다 | 검증 완료 | 운영 전 재검증 완료 | `H70_H72_operational_revalidation` | train 기준 예외는 Cold median `0.2786 -> 0.2798`, p95 `1.4860 -> 1.6192`로 악화 | 중간 부피 예외 미채택, H32 유지 |
| H72 | G3 Cold 성능 개선 / G4 운영 가능 피처 선정 | medium/support 조합 정리는 여러 희소도 기준에서도 Cold 성능을 개선할 것이다 | 검증 완료 | 운영 전 재검증 완료 | `H70_H72_operational_revalidation` | `min_count=20~500` 모두 H32보다 median APE 악화 | combo 정리 피처 미채택 |
