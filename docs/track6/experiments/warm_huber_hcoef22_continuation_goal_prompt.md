# Warm Huber HCOEF22 이후 지속 실험 /goal 프롬프트

아래 프롬프트는 Codex의 `/goal` 명령어 뒤에 그대로 붙여 넣어 사용한다.

## 현재 기준

| 구분 | 후보 | fixed test | 0604 stress test | 판단 |
| --- | --- | ---: | ---: | --- |
| 최소 비교 기준 | `current_70_30` | MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`, RMSE_log `0.3996` | MdAPE `0.2779`, MAPE `0.3774`, p95 `0.9871` | 서비스 v0.1 최소 기준 |
| 현재 1순위 기준 | `hcoef2_size_reliability_cap005_s050` | MdAPE `0.1388`, MAPE `0.2730`, p95 `0.8064`, RMSE_log `0.3988` | MdAPE `0.2731`, MAPE `0.3744`, p95 `0.9835` | 운영 기본 후보 유지 |

## 기준 선택 이유

- 최소 비교 기준은 `current_70_30`으로 둠.
  - 이유: 서비스 v0.1에서 실제로 설명 가능한 기준 후보임.
  - 의미: 새 실험이 최소한 현재 서비스 기준보다 좋아야 함.

- 1차 기준은 `hcoef2_size_reliability_cap005_s050`로 둠.
  - 이유: fixed test뿐 아니라 row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95가 모두 개선된 후보임.
  - 의미: 새 운영 후보는 이 후보를 넘어야 실제 개선이라고 볼 수 있음.

- 0604 stress test는 보조 기준으로 둠.
  - 이유: 최신 운영 유사 데이터라 중요하지만, 데이터 정합성과 분포 차이가 있어 학습/튜닝 기준으로 쓰면 과적합 위험이 있음.
  - 의미: 후보 선택 기준이 아니라 외부 검증, 큰 오차 위험 확인, 서비스 적용 리스크 확인에 사용함.

## 성능 판단 우선순위

| 우선순위 | 지표 | 보는 이유 | 운영 판단 |
| --- | --- | --- | --- |
| 1 | 반복 OOF MdAPE/MAPE/p95 | 데이터 split이 바뀌어도 개선되는지 확인 | 운영 후보의 필수 조건 |
| 2 | fixed test MdAPE/MAPE/p95 | 기존 실험 기준에서 직접 비교 | 현재 1순위 기준보다 악화되면 보류 |
| 3 | fixed test p95_APE | 큰 오차 위험 확인 | `0.8064`보다 악화되면 기본 후보 미채택 |
| 4 | 0604 stress test | 최신 운영 유사 데이터에서 흔들림 확인 | p95 `0.9835`보다 악화되면 승격 보류 |
| 5 | 계수/정책 해석 가능성 | Huber 모델의 장점을 유지하는지 확인 | 설명 불가능하면 연구 후보로 분리 |

## HCOEF21까지의 핵심 결론

- HCOEF20은 운영 component 기반 저차원 Huber/Ridge 잔차 후보와 direct stack 후보를 검증했으나 새 점 예측 운영 후보를 채택하지 않음.
- HCOEF21은 고정 `70:30` 기준가를 표본 수/coverage/quantile width 기반 가변 SVC:PP-V8 기준가로 바꾸는 실험을 수행함.
- HCOEF21 상위 후보 `hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25`는 fixed test `0.1388 / 0.2727 / 0.8099`로 MAPE는 소폭 개선했지만 p95가 기준 `0.8064`보다 악화됨.
- HCOEF21 bootstrap all3 개선 확률 최대값은 약 `0.33`으로 운영 gate `0.90`에 미달함.
- 따라서 `hcoef2_size_reliability_cap005_s050`를 현재 Warm 운영 기본 후보로 유지함.
- 가변 기준가와 신뢰도 피처는 설명 가능한 연구 후보 또는 MAPE 특화 후보로만 유지함.

## 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 HCOEF22 이후 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수를 좋게 만드는 것이 아니라, 반복 검증과 운영 안정성까지 통과하는 최고 성능 후보 또는 목적별 보정 정책을 찾는 것이다.

먼저 아래 문서를 읽고 현재 후보, 이미 완료한 실험, 반복하면 안 되는 방식, 남은 실험 축을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

현재 1차 기준 후보는 `hcoef2_size_reliability_cap005_s050`다.

- fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
- 0604 stress test: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
- row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 1.0

최소 비교 기준은 `current_70_30`이다.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 stress test: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

후보 판단 기준은 아래처럼 고정해줘.

1. 새 후보는 최소한 `current_70_30`보다 좋아야 한다.
2. 운영 기본 후보가 되려면 `hcoef2_size_reliability_cap005_s050` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 한다.
3. row OOF와 artist OOF의 `all3_improve_prob >= 0.90`이면 개선 후보로 본다.
4. row OOF와 artist OOF의 `all3_improve_prob >= 0.95`이고 fixed test와 0604에서 악화가 없으면 강한 후보로 본다.
5. fixed test p95_APE가 0.8064보다 악화되면 운영 기본 후보로 채택하지 않는다.
6. 0604 p95_APE가 0.9835보다 악화되면 운영 후보 승격을 보류한다.
7. fixed test 또는 0604만 좋아지는 후보는 연구 후보로만 남긴다.
8. 0604 residual이나 test residual을 보고 새 보정값, 경계값, 가중치를 만들지 않는다.
9. 실제 가격 구간은 원인 진단용으로만 쓰고 보정 기준으로 쓰지 않는다.

성능 판단 우선순위는 아래처럼 둬.

1. 반복 OOF MdAPE/MAPE/p95 안정성
2. fixed test MdAPE/MAPE/p95
3. fixed test p95_APE 방어
4. 0604 stress test 악화 여부
5. Huber 계수 또는 보정 정책의 해석 가능성

반복하지 말아야 할 방식은 아래와 같다.

1. HCOEF18처럼 quantile width로 점 예측을 직접 움직이는 방식은 그대로 반복하지 않는다.
2. HCOEF20에서 완료한 운영 component 기반 저차원 Huber/Ridge residual grid와 direct stack grid를 같은 피처, 같은 cap/strength 조합으로 반복하지 않는다.
3. HCOEF21에서 완료한 가변 SVC:PP-V8 기준가와 adaptive reliability/interactions residual grid를 같은 피처, 같은 cap/strength 조합으로 반복하지 않는다.
4. HCOEF21 상위 후보는 fixed test p95와 bootstrap gate를 통과하지 못했으므로 운영 기본 후보가 아니라 연구 후보로 둔다.

HCOEF22 이후 우선 실험 방향은 아래 순서로 잡아줘.

1. 목적별 후보 분리 검증
   - 운영 기본 후보, MAPE 특화 후보, p95 방어 후보, 신뢰도/범위 정책 후보를 분리한다.
   - HCOEF20~21에서 보류된 MAPE 개선 후보는 p95 악화폭을 명시하고, 서비스에서 목적별로 쓸 수 있는지 판단한다.

2. 가격 범위/신뢰도 정책 고도화
   - 점 예측을 바꾸지 않고 q10/q50/q90, quantile width, price_range_ratio, service_confidence_tier를 활용한다.
   - validation에서 경계를 정의하고 fixed test와 0604에서 실제 포함률, 큰 오차율, tier별 MdAPE/MAPE/p95를 확인한다.

3. 현재 최고 후보의 남은 p95 원인 재분석
   - `residual_log = actual_log - pred_log`로 오차를 정의한다.
   - 기준가 표본 수, fallback level, 기준가 IQR, quantile width, 후보 간 gap, 작품 크기, 재료/지지체 bucket별로 p95 위험을 나눈다.
   - 보정 기준은 예측 시점에 알 수 있는 피처만 사용한다.

4. 정말 새 피처가 생긴 경우에만 Huber 계수 재탐색
   - 새 원인 피처가 없으면 같은 residual Huber grid를 반복하지 않는다.
   - 새 피처가 있으면 cap 0.02/0.03/0.05, strength 0.25/0.50/0.75 범위에서 작게 검증한다.

실험 관리 규칙은 아래처럼 지켜줘.

- 마지막 완료 번호가 PP-HCOEF21이면 다음 실험은 PP-HCOEF22부터 시작한다.
- 실험 폴더는 `experiments/track6/PP-HCOEF##_짧은_설명` 형식으로 만든다.
- 실행 스크립트는 `scripts/track6/run_pp_hcoef##_짧은_설명.py`로 남긴다.
- 각 실험에는 최소한 아래 파일을 남긴다.
  - artifacts/experiment_config.json
  - outputs/metrics.csv
  - outputs/candidate_predictions.csv
  - outputs/feature_coefficients.csv 또는 outputs/policy_map.csv
  - outputs/residual_analysis.csv
  - outputs/bootstrap_or_repeated_split_summary.csv 또는 outputs/repeated_validation_summary.csv
  - reports/result_report.md
  - reports/result_report.html

실험 후 아래 문서를 업데이트해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_hcoef22_continuation_goal_prompt.md
- 필요하면 최신 continuation goal prompt 문서

최종 응답에는 아래 내용을 정리해줘.

- 실행한 실험 ID와 폴더
- 새 후보명과 후보 유형
- `current_70_30` 대비 개선폭
- `hcoef2_size_reliability_cap005_s050` 대비 개선폭
- row OOF와 artist OOF 반복 검증 결과
- fixed test와 0604 stress test 결과
- Huber 계수 또는 보정 정책 해석
- 운영 후보 / 목적별 후보 / 보류 후보 판단
- 다음 실험에서 반복하지 말아야 할 점
```
