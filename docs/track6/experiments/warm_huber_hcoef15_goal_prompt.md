# Warm Huber 최고 성능 탐색 /goal 프롬프트

아래 내용을 `/goal` 뒤에 붙여 넣어 사용한다.

```text
Warm Huber 계열 가격 예측 모델에서 현재 검증된 최고 후보를 넘는 실험을 이어서 진행해줘.

목표는 fixed test 한 번의 점수 개선이 아니라, 반복 검증과 운영 안정성을 함께 통과하는 최고 성능 후보를 찾는 것이다.

먼저 아래 문서를 읽고 현재 후보, 보류 후보, 실패한 실험 유형을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- experiments/track6/PP-HCOEF11_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF12_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF13_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF14_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

현재 1차 비교 기준은 `hcoef2_size_reliability_cap005_s050`다.

- fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
- 0604 신규 라벨 일부 확인: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
- row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 모두 1.0

서비스 v0.1 기준 후보 `current_70_30`도 함께 비교해줘.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 신규 라벨 일부 확인: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

이미 확인된 보류 결론은 반복하지 마.

- loose 기준가 Huber는 MdAPE/MAPE 개선 잠재력은 컸지만 p95가 악화되어 기본 후보 보류.
- capped blend와 조건부 routing은 개선폭 또는 반복 안정성이 부족해 기본 후보 보류.
- 면적단가 직접 잔차 피처와 segmented cap/strength는 p95 방어가 부족하거나 HCOEF3보다 악화.
- 원인 구간 median 보정과 HCOEF14 위험 구간 shrinkage/routing은 fixed test 소폭 개선이 있었지만 반복 OOF gate를 통과하지 못함.
- HCOEF12 패키징 감사는 완료됐으므로 같은 목적의 패키징 실험은 중복하지 않음.

다음 실험은 `PP-HCOEF15`부터 이어서 관리해줘.

우선순위는 아래 순서로 잡아줘.

1. 최신 라벨 stress test
   - 현재 최고 후보가 최신 라벨 또는 새 운영성 데이터에서 유지되는지 확인.
   - 데이터 정합성, 환율/가격 단위, Warm/Cold 분기, feature coverage를 먼저 점검.
   - 새 데이터로 보정값을 만들지 말고 확인용으로만 사용.

2. 서비스 feature pipeline 통합 검증
   - 운영 입력에서 `current_70_30`과 HCOEF residual 피처가 같은 방식으로 생성되는지 확인.
   - 누락 피처, artist_key 매핑, 유사 작품 기반 가격 피처 표본 수, IQR, fallback level을 점검.
   - 실험 코드와 운영 feature 생성 로직의 불일치가 있으면 성능 실험보다 먼저 수정 후보를 문서화.

3. risk/quantile meta guard
   - HCOEF14처럼 같은 위험 구간 median 보정을 반복하지 말고, 별도 위험도 또는 quantile 폭을 이용해 큰 오차 위험을 예측하는 보조 모델을 검증.
   - 보조 모델은 운영 예측 시점에 알 수 있는 피처만 사용.
   - 목적은 기본 가격을 크게 바꾸는 것이 아니라 p95_APE와 과대/과소 위험을 줄이는 것.

4. 추가 성능 탐색
   - 새로운 기준가 생성 방식이나 Huber 피처 계수 조정을 시도하려면 HCOEF4~HCOEF14와 무엇이 다른지 먼저 명시.
   - 피처 수를 무리하게 늘리지 말고 설명 가능한 저차원 피처부터 검증.
   - residual_log는 `actual_log - pred_log`로 정의하고, 보정 모델은 반드시 OOF residual로 학습.

후보 채택 기준은 아래처럼 고정해줘.

- row OOF와 artist OOF에서 MdAPE/MAPE/p95 평균이 모두 개선되어야 함.
- row OOF와 artist OOF에서 `all3_improve_prob >= 0.90`이면 개선 후보.
- `all3_improve_prob >= 0.95`이고 fixed validation/test/0604에서 악화가 없으면 강한 후보.
- fixed test만 좋은 후보는 채택하지 않음.
- fixed test p95_APE가 HCOEF3 기준 0.8064보다 악화되면 기본 후보로 채택하지 않음.
- 0604 p95_APE가 HCOEF3 기준 0.9835보다 악화되면 운영 후보 승격을 보류.
- MAPE/MdAPE 특화 후보는 기본 후보와 분리해 목적별 후보로만 기록.
- 보정폭이 큰 후보는 설명력과 운영 안정성 검토를 별도로 수행.

실험 관리 방식은 아래처럼 지켜줘.

- `experiments/track6/` 아래에 실험별 독립 폴더를 생성.
- 새 실험은 `PP-HCOEF15_*`부터 시작.
- 각 실험에는 최소한 아래 산출물을 남김.
  - artifacts/experiment_config.json
  - outputs/metrics.csv
  - outputs/candidate_predictions.csv
  - outputs/feature_coefficients.csv 또는 outputs/policy_map.csv
  - outputs/residual_analysis.csv
  - outputs/bootstrap_or_repeated_split_summary.csv 또는 outputs/repeated_validation_summary.csv
  - reports/result_report.md
  - reports/result_report.html

실험 후에는 아래 문서를 업데이트해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md

진행 중에는 먼저 계획을 짧게 세우고, 바로 실행 가능한 실험부터 실행해줘. 결과가 기준을 넘지 못하면 왜 넘지 못했는지와 다음 실험에서 반복하지 말아야 할 점을 정리해줘.
```
