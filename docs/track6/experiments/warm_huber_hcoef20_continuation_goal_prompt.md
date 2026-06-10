# Warm Huber HCOEF20 이후 지속 실험 /goal 프롬프트

아래 프롬프트는 Codex의 `/goal` 명령어 뒤에 그대로 붙여 넣어 사용한다.

```text
Track6 가격 예측 프로젝트에서 Warm Huber 계열의 HCOEF20 이후 실험을 계속 진행해줘.

목표는 현재 Warm 개선 후보 `hcoef2_size_reliability_cap005_s050`를 무리하게 교체하는 것이 아니라, Huber의 선형 계수 해석 가능성과 운영 component 재현성을 유지하면서 더 좋은 후보 또는 서비스 신뢰도 정책을 찾는 것이다.

먼저 아래 문서를 읽고 현재 기준 후보, 이미 실패한 실험 유형, 완료된 운영 재현성 감사를 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- docs/track6/experiments/warm_huber_max_performance_continuation_goal_prompt.md
- docs/track6/experiments/warm_huber_continuous_max_performance_goal_prompt.md
- experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

현재 1차 기준 후보는 `hcoef2_size_reliability_cap005_s050`다.

- fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
- 0604 최신 라벨 stress test: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
- row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 1.0

최소 비교 기준은 서비스 v0.1 후보 `current_70_30`이다.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 최신 라벨 stress test: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

반복하지 말아야 할 결론은 아래와 같다.

1. loose 기준가 Huber, 면적단가 직접 잔차 피처, segmented 보정, risk-gated basis 결합은 p95 또는 반복 안정성 기준을 넘지 못했다.
2. PP-V8 전체 반영, PP-V8 제한 이동, quantile width 기반 점 예측 이동은 validation/bootstrap gate를 통과하지 못했다.
3. HCOEF19에서 연구 산출물과 운영 v0.1 component/formula/feature schema는 일치함이 확인됐으므로 같은 파이프라인 감사만 반복하지 않는다.
4. 0604 또는 test residual을 보고 새 보정값, 경계값, 가중치를 만들지 않는다.

새 실험은 마지막 완료 번호를 확인한 뒤 `PP-HCOEF20`부터 이어서 관리해줘.

우선순위는 아래처럼 잡아줘.

1. quantile width 기반 가격 범위/신뢰도 정책 검증
   - quantile width는 점 예측을 움직이는 기준이 아니라 예측 범위와 신뢰도 표시 기준으로 사용한다.
   - q10/q50/q90, q90-q10 로그 폭, price_range_ratio, service_confidence_tier를 사용한다.
   - validation 기준으로 범위/신뢰도 구간을 정의하고 fixed test와 0604에서 실제 포함률, MdAPE/MAPE/p95, 큰 오차율을 확인한다.
   - 결과는 점 예측 후보가 아니라 서비스 표시 정책 후보로 분리한다.

2. 운영 component 기반 저차원 Huber 계수 재탐색
   - 입력 후보는 `hcoef_stable`, `current_70_30`, `svc_numeric_seed_mean`, `ppv8_service_proxy`, `l10_seq_pred_log`, `quantile_width`, `svc_group_n_log`, `coverage_numeric`, 후보 간 gap만 사용한다.
   - 너무 많은 원본 피처를 추가하지 않는다.
   - Huber residual 보정은 OOF residual로만 학습하고 cap/strength를 둔다.
   - 목적별 후보를 운영 기본 후보, MAPE 특화 후보, p95 방어 후보, 신뢰도 표시 후보로 분리한다.

검증 기준은 아래처럼 고정해줘.

1. 운영 기본 후보가 되려면 `hcoef2_size_reliability_cap005_s050` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 한다.
2. row OOF와 artist OOF의 `all3_improve_prob >= 0.90`이면 개선 후보로 본다.
3. row OOF와 artist OOF의 `all3_improve_prob >= 0.95`이고 fixed test와 0604에서 악화가 없으면 강한 후보로 본다.
4. fixed test p95_APE가 0.8064보다 악화되면 운영 기본 후보로 채택하지 않는다.
5. 0604 p95_APE가 0.9835보다 악화되면 운영 후보 승격을 보류한다.
6. fixed test만 좋아지는 후보, 0604만 좋아지는 후보는 연구 후보로만 남긴다.

실험 산출물은 아래 구조로 남겨줘.

- 실험 폴더: experiments/track6/PP-HCOEF20_짧은_설명
- 실행 스크립트: scripts/track6/run_pp_hcoef20_짧은_설명.py
- 필수 산출물:
  - artifacts/experiment_config.json
  - outputs/metrics.csv
  - outputs/candidate_predictions.csv
  - outputs/residual_analysis.csv
  - outputs/bootstrap_or_repeated_split_summary.csv 또는 outputs/repeated_validation_summary.csv
  - outputs/feature_coefficients.csv 또는 outputs/policy_map.csv
  - reports/result_report.md
  - reports/result_report.html

실험 후 아래 문서를 업데이트해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- docs/track6/experiments/warm_huber_max_performance_continuation_goal_prompt.md
- 필요하면 최신 continuation goal prompt 문서

최종 응답에는 실행한 실험 ID, 후보 유형, current_70_30 대비 개선폭, hcoef2_size_reliability_cap005_s050 대비 개선폭, 반복 검증 결과, fixed test/0604 결과, 계수 또는 정책 해석, 운영 후보/목적별 후보/보류 후보 판단을 정리해줘.
```
