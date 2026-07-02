# PP-HCOEF16 Warm PP-V8 운영 component OOF 재검증 /goal 프롬프트

아래 내용을 `/goal` 뒤에 붙여 넣어 사용한다.

```text
Warm Huber 계열에서 PP-HCOEF16 실험을 진행해줘.

목표는 PP-HCOEF15 최신 라벨 stress test에서 강하게 보인 운영 PP-V8/service primary component를 바로 채택하는 것이 아니라, validation OOF 기준으로 Huber 계수 입력 또는 risk guard 피처로 재검증하는 것이다.

먼저 아래 자료를 확인해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv
- experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/outputs/service_vs_hcoef_gap_analysis.csv

현재 기준 후보는 아래와 같다.

- 기존 70:30 기준 후보 `current_70_30`
  - fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
  - 0604: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

- HCOEF 안정 후보 `hcoef2_size_reliability_cap005_s050`
  - fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
  - 0604: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
  - HCOEF11 row/artist OOF all3 개선확률 1.0

- HCOEF15에서 확인된 운영 PP-V8/service primary
  - 0604: MdAPE 0.2298, MAPE 0.3359, p95_APE 0.9273
  - 주의: 0604에서 강하지만 HCOEF OOF/fixed test 후보 선택 절차를 통과한 후보가 아니므로 바로 채택하지 않는다.

실험 방향은 아래처럼 잡아줘.

1. 입력 정합성 확인
   - PP-HCOEF15의 service primary/PP-V8 pred_log가 어떤 산출물에서 왔는지 확인한다.
   - validation/test/0604에서 같은 방식의 pred_log 또는 component를 만들 수 있는지 확인한다.
   - 운영 component가 fixed test에는 없거나 생성 방식이 다르면 새 후보 학습 전에 그 차이를 문서화한다.

2. OOF 입력 생성
   - 0604 라벨로 가중치나 보정값을 만들지 않는다.
   - validation 내부 OOF로 `service_primary_pred_log` 또는 `pp_v8_compact_blend_mape_guarded_pred_log`와 유사한 component를 생성할 수 있는지 확인한다.
   - 생성이 어렵다면 proxy component를 명확히 정의하고, 운영 component와 어떤 차이가 있는지 기록한다.

3. 저차원 Huber 계수 실험
   - 기본 입력:
     - current_70_30
     - hcoef stable pred_log
     - PP-V8/service component pred_log 또는 proxy
     - current_vs_ppv8_gap
     - hcoef_vs_ppv8_gap
     - svc_group_n_log
     - svc_coverage_tier 또는 coverage numeric
     - svc_prior_iqr
     - l10_price_range_ratio 또는 quantile width가 있으면 위험도 피처로 추가
   - 피처 수를 과하게 늘리지 말고 계수 해석 가능한 조합부터 비교한다.

4. 보정 방식 비교
   - Huber residual correction
   - Huber meta blend
   - risk guard routing
   - PP-V8 component를 전체 반영하지 않고 high-confidence 구간에만 제한 반영하는 후보
   - cap 후보는 0.02, 0.03, 0.05를 기본으로 둔다.
   - strength 후보는 0.25, 0.50, 0.75로 둔다.

5. 검증 기준
   - row OOF와 artist OOF에서 MdAPE/MAPE/p95 평균이 모두 개선되어야 한다.
   - row OOF와 artist OOF에서 all3_improve_prob >= 0.90이면 개선 후보로 본다.
   - fixed test p95_APE가 HCOEF 안정 후보 0.8064보다 악화되면 운영 기본 후보로 채택하지 않는다.
   - 0604 p95_APE가 HCOEF 안정 후보 0.9835보다 악화되면 운영 후보 승격을 보류한다.
   - 0604는 stress test로만 사용하고 후보 선택 기준으로 쓰지 않는다.

실험 산출물은 아래 경로 구조로 남겨줘.

- 실험 폴더: experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement
- 실행 스크립트: scripts/track6/run_pp_hcoef16_warm_huber_price_basis_coefficient_refinement.py
- 산출물:
  - artifacts/experiment_config.json
  - outputs/metrics.csv
  - outputs/candidate_predictions.csv
  - outputs/feature_coefficients.csv
  - outputs/residual_analysis.csv
  - outputs/bootstrap_or_repeated_split_summary.csv 또는 outputs/repeated_validation_summary.csv
  - reports/result_report.md
  - reports/result_report.html

실행 후 아래 문서를 업데이트해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md

최종 응답에는 아래 내용을 정리해줘.

- PP-V8/service component를 OOF로 재현할 수 있었는지
- 새 후보가 current_70_30과 HCOEF 안정 후보 대비 얼마나 개선됐는지
- row OOF와 artist OOF 검증 결과
- fixed test와 0604 stress test 결과
- Huber 계수 해석
- 운영 후보, 목적별 후보, 보류 후보 판단
```

