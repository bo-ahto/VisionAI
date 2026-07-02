# Warm Huber HCOEF37 이후 지속 실험 /goal 프롬프트

이 문서는 Codex의 `/goal` 기능에 바로 붙여 넣기 위한 최신 실행 프롬프트다.

- 기준일: 2026-06-08
- 최신 완료 실험: `PP-HCOEF37`
- 최신본 안내: `PP-HCOEF38` 실행 이후에는 `docs/track6/experiments/warm_huber_hcoef38_continuation_goal_prompt.md`를 사용한다.
- 목적: Warm Huber 계열에서 현재 안정 후보 `hcoef_stable`을 반복 검증까지 안정적으로 넘는 후보를 찾는다.
- 사용 방식: `/goal` 명령어 뒤에 아래 “붙여넣기용 프롬프트” 전체를 붙여 넣는다.

## 1. 기준 설정

- 최소 비교 기준: `current_70_30`
  - 의미: 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합.
  - fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996`.
  - 0604 stress: MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871`.
  - 새 후보가 최소한 넘어야 하는 서비스 v0.1 기준선.

- 운영 비교 기준: `hcoef_stable` / `hcoef2_size_reliability_cap005_s050`
  - 의미: `current_70_30` 위에 Huber 잔차 보정을 작게 더한 현재 안정 후보.
  - fixed test: MdAPE `0.138803`, MAPE `0.272989`, p95_APE `0.806366`, RMSE_log `0.398822`.
  - 0604 stress: MdAPE `0.273062`, MAPE `0.374365`, p95_APE `0.983456`.
  - 기존 반복 검증에서 row/artist OOF all3 개선 확률 `1.0 / 1.0`.
  - 운영 후보가 넘어야 하는 실제 기준.

- 최신 반복 검증 후보: `hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90`
  - 의미: HCOEF36의 low-risk routing 후보를 HCOEF37에서 확장 반복 검증한 최상위 후보.
  - fixed test: MdAPE `0.138290`, MAPE `0.272937`, p95_APE `0.806031`.
  - 0604 stress: MdAPE `0.273407`, MAPE `0.374329`, p95_APE `0.983456`.
  - 반복 검증: min stable any2/all3 `0.9333 / 0.4333`.
  - 판단: any2 안정성은 있지만 all3 운영 기준이 부족하므로 운영 후보가 아니라 “Warm 안정 반복 검증 후보”.

## 2. 채택 기준

| 후보 유형 | 기준 | 판단 |
| --- | --- | --- |
| 운영 후보 | `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95_APE 모두 동등 또는 개선. 0604 p95 악화 없음 | v0.1 후속 반영 검토 |
| 강한 검증 후보 | row/artist repeated all3 개선 확률 `>= 0.95`, fixed test와 0604 악화 없음 | 확장 반복 검증 후 운영 후보 검토 |
| 일반 검증 후보 | row/artist repeated all3 개선 확률 `>= 0.90`, fixed p95 악화 없음 | 다음 실험에서 재검증 |
| MAPE 특화 후보 | MAPE는 개선되지만 MdAPE 또는 p95_APE가 약함 | 운영 기본값과 분리 |
| p95 방어 후보 | 큰 오차는 줄지만 MdAPE/MAPE 개선폭이 작음 | 가격 범위/신뢰도 정책 후보 |
| 연구 후보 | fixed test 또는 0604만 좋고 반복 검증이 약함 | 문서화하고 기본 후보 미채택 |

## 3. 금지 기준

- fixed test residual 또는 0604 residual을 보고 보정값, 가중치, 구간 경계를 만들지 않는다.
- 0604 데이터는 최신 신규 라벨 stress test이며, 후보 선택용 학습 데이터가 아니다.
- 실제 가격 구간은 운영 예측 시점에 알 수 없으므로 보정 기준으로 쓰지 않는다.
- fixed test p95_APE가 `0.806366`보다 악화되면 운영 후보로 채택하지 않는다.
- 0604 p95_APE가 `0.983456`보다 악화되면 운영 후보 승격을 보류한다.
- 이미 실패한 동일 cap/strength grid를 반복하지 않는다.
- 설명 불가능한 고차원 조합은 성능이 좋아도 운영 후보가 아니라 연구 후보로 분리한다.

## 4. 다음 실험 우선순위

1. `PP-HCOEF38`: all3 안정성 강화를 위한 stricter low-risk routing
   - HCOEF37은 any2 안정성은 강했지만 all3가 약했다.
   - 적용 대상을 더 줄여도 MdAPE/MAPE/p95가 동시에 안정되는 구간이 있는지 확인한다.
   - 후보 기준: `basis_component_spread`, `basis_n_log`, `fallback_level`, `log_area`, `stable_ppv8_gap_abs`, `quantile_width`, `price_range_ratio`.
   - 성공 기준: row/artist repeated all3 `>= 0.90`, fixed p95 `<= 0.806366`, 0604 p95 `<= 0.983456`.

2. `PP-HCOEF39`: 기준가 생성 방식 재탐색
   - HCOEF34~35에서 기준가 gap Huber는 MdAPE/MAPE 개선 신호가 있었지만 p95가 약했다.
   - 기준가 자체를 더 안정적으로 만들 수 있는지 확인한다.
   - 후보 기준가: 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체, fallback shrink 기준가.
   - 핵심은 기준가를 더 세분화하는 것이 아니라 “표본 수가 부족할 때 얼마나 보수적으로 fallback할지”를 검증하는 것이다.

3. `PP-HCOEF40`: Huber 계수 세분화
   - Huber의 선형 계수 특성을 살려 기준가, 크기, 표본 수, 신뢰도, 후보 간 gap 피처의 계수를 직접 해석한다.
   - 우선 피처: `current_70_30`, `hcoef_stable`, `svc`, `ppv8`, `log_area`, `svc_group_n_log`, `svc_prior_iqr`, `stable_ppv8_gap_abs`, `basis_component_spread`, `fallback_level`, `price_range_ratio`, `quantile_width`.
   - 피처가 많아질 경우 L2/ElasticNet/cap/strength로 과적합을 방어한다.

4. `PP-HCOEF41`: 목적별 후보 분리
   - MdAPE 최적 후보, MAPE 최적 후보, p95 방어 후보를 분리한다.
   - 운영 후보는 세 지표가 모두 안정적인 후보만 채택한다.
   - 목적별 후보는 서비스 기본 예측값이 아니라 신뢰도/가격 범위/관리자 참고 후보로 문서화한다.

5. `PP-HCOEF42`: 점 예측 유지 + 가격 범위/신뢰도 정책
   - HCOEF37까지의 결과상 점 예측을 조금 움직이는 방식은 all3 안정성이 병목이다.
   - `hcoef_stable`을 점 예측 기준으로 유지하고, quantile width, 기준가 spread, fallback level, 표본 수로 신뢰도와 가격 범위를 고도화한다.

## 5. 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 현재 안정 후보를 넘기기 위한 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수를 좋게 만드는 것이 아니라, 반복 검증과 운영 안정성까지 통과하는 최고 성능 후보를 찾는 것이다. 실험은 기존 HCOEF 실험 구조를 유지하고, 마지막 완료 번호인 PP-HCOEF37 이후부터 이어서 관리해줘.

먼저 아래 문서를 읽고 현재 후보, 실패한 실험 유형, 남은 검증 방향을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_hcoef37_continuation_goal_prompt.md
- experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

비교 기준은 아래처럼 고정해줘.

1. 최소 기준은 `current_70_30`이다.
   - fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
   - 0604 stress: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

2. 운영 비교 기준은 `hcoef_stable` 또는 `hcoef2_size_reliability_cap005_s050`이다.
   - fixed test: MdAPE 0.138803, MAPE 0.272989, p95_APE 0.806366, RMSE_log 0.398822
   - 0604 stress: MdAPE 0.273062, MAPE 0.374365, p95_APE 0.983456
   - row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 모두 1.0

3. 최신 반복 검증 후보는 `hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90`이다.
   - fixed test: MdAPE 0.138290, MAPE 0.272937, p95_APE 0.806031
   - 0604 stress: MdAPE 0.273407, MAPE 0.374329, p95_APE 0.983456
   - repeated min stable any2/all3: 0.9333 / 0.4333
   - any2 안정성은 확인됐지만 all3가 약하므로 운영 후보가 아니라 추가 검증 후보로 둔다.

채택 기준은 아래처럼 적용해줘.

1. 새 후보는 최소한 `current_70_30`보다 좋아야 한다.
2. 운영 후보가 되려면 `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95_APE가 모두 동등 또는 개선되어야 한다.
3. row OOF와 artist OOF의 repeated all3 개선 확률이 0.95 이상이고 fixed test와 0604에서 악화가 없으면 강한 검증 후보로 본다.
4. row OOF와 artist OOF의 repeated all3 개선 확률이 0.90 이상이고 fixed p95_APE 악화가 없으면 일반 검증 후보로 본다.
5. fixed test p95_APE가 0.806366보다 악화되면 운영 후보로 채택하지 않는다.
6. 0604 p95_APE가 0.983456보다 악화되면 운영 후보 승격을 보류한다.
7. fixed test residual 또는 0604 residual을 보고 새 보정값, 경계값, 가중치를 만들지 않는다.
8. 실제 가격 구간은 원인 진단용으로만 쓰고 보정 기준으로 쓰지 않는다.
9. 운영 예측 시점에 알 수 없는 값은 피처나 라우팅 기준으로 쓰지 않는다.

우선 실험은 아래 순서로 진행해줘.

1. PP-HCOEF38: all3 안정성 강화를 위한 stricter low-risk routing
   - HCOEF37에서 any2는 강했지만 all3가 약했으므로, 적용 대상을 더 보수적으로 줄여도 세 지표가 동시에 개선되는지 확인한다.
   - 후보 기준은 basis_component_spread, basis_n_log, fallback_level, log_area, stable_ppv8_gap_abs, quantile_width, price_range_ratio로 둔다.
   - 경계는 validation/OOF에서만 만들고 fixed test와 0604로 만들지 않는다.

2. PP-HCOEF39: 기준가 생성 방식 재탐색
   - HCOEF34~35의 기준가 gap Huber 신호를 유지하되 p95가 악화되지 않는 기준가 fallback/shrink 구조를 찾는다.
   - 기준가 후보는 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체, fallback shrink 기준가로 둔다.

3. PP-HCOEF40: Huber 계수 세분화
   - Huber 선형 계수 특성을 활용해 기준가, 크기, 표본 수, 신뢰도, 후보 간 gap 피처의 계수를 직접 조정하고 해석한다.
   - 저차원 조합부터 검증하고, 피처가 많아지면 L2/ElasticNet/cap/strength로 과적합을 방어한다.

4. PP-HCOEF41: 목적별 후보 분리
   - MdAPE 최적 후보, MAPE 최적 후보, p95 방어 후보를 분리해서 만든다.
   - 운영 후보는 세 지표가 모두 안정적인 후보만 채택한다.

5. PP-HCOEF42: 점 예측 유지 + 가격 범위/신뢰도 정책
   - 점 예측 이동이 all3 안정성 기준을 통과하지 못하면 `hcoef_stable`을 유지하고, quantile width, 기준가 spread, fallback level, 표본 수로 가격 범위와 신뢰도 tier를 고도화한다.

실험 관리 규칙은 아래처럼 지켜줘.

- `experiments/track6/` 아래에 실험별 독립 폴더를 만든다.
- 새 실험은 `PP-HCOEF##_짧은_설명` 형식으로 관리한다.
- 기존 실험 번호와 충돌하지 않게 PP-HCOEF38부터 시작한다.
- 실행 스크립트는 `scripts/track6/run_pp_hcoef##_짧은_설명.py`로 남긴다.
- 각 실험에는 최소한 아래 파일을 남긴다.
  - artifacts/experiment_config.json
  - outputs/metrics.csv
  - outputs/candidate_predictions.csv
  - outputs/feature_coefficients.csv 또는 outputs/policy_map.csv
  - outputs/residual_analysis.csv
  - outputs/repeated_validation_summary.csv 또는 outputs/bootstrap_or_repeated_split_summary.csv
  - outputs/selected_candidates.csv
  - reports/result_report.md
  - reports/result_report.html
- fixed test 결과만 보고 후보를 고르지 말고, validation/OOF/repeated 결과를 먼저 보고 후보를 정한 뒤 fixed test와 0604는 확인용으로만 쓴다.
- 스크립트에는 재현 가능한 seed, split 방식, 입력 파일, 후보명 생성 규칙을 남긴다.

실험 후에는 아래 문서를 업데이트해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/postprocessing_experiment_matrix.html
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.html
- docs/track6/experiments/warm_huber_hcoef37_continuation_goal_prompt.md

최종 응답에는 실행한 실험 ID와 폴더, 새 후보명과 후보 유형, current_70_30 대비 개선폭, hcoef_stable 대비 개선폭, row/artist 반복 검증 결과, fixed test와 0604 stress 결과, Huber 계수 또는 보정 정책 해석, 운영 후보/목적별 후보/보류 후보 판단, 다음 실험에서 반복하지 말아야 할 점을 요약해줘.
```
