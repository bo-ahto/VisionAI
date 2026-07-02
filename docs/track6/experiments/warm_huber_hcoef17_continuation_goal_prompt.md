# Warm Huber HCOEF17 이후 지속 실험 /goal 프롬프트

아래 프롬프트는 Codex의 `/goal` 명령어 뒤에 그대로 붙여 넣어 사용한다.

## 기준

- 현재 Warm 개선 기준 후보: `hcoef2_size_reliability_cap005_s050`
  - 의미: `current_70_30` 위에 Huber 잔차 보정을 작게 더한 후보.
  - fixed test: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988`.
  - 0604 최신 라벨 stress test: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
  - 반복 검증: row OOF와 artist OOF에서 MdAPE/MAPE/p95 개선확률 `1.0`.

- 최소 비교 기준 후보: `current_70_30`
  - 의미: 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합.
  - fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996`.
  - 0604 최신 라벨 stress test: MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871`.

- 이미 확인한 보류 축:
  - loose 기준가 Huber: MdAPE/MAPE 개선 잠재력은 있으나 fixed test p95 악화.
  - capped blend/조건부 routing/면적단가 잔차 피처/segmented 보정/risk-gated 결합/원인 구간 median 보정: 반복 OOF 또는 p95 guard 미통과.
  - PP-V8/service component: 0604에서는 강하지만 HCOEF16 fixed test와 artist OOF 기준 미통과.

## 판단 기준

| 후보 유형 | 기준 | 판단 |
|---|---|---|
| 운영 기본 후보 | `hcoef2_size_reliability_cap005_s050` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선 | 실제 반영 검토 |
| 강한 개선 후보 | row OOF와 artist OOF의 `all3_improve_prob >= 0.95`, fixed test와 0604에서 악화 없음 | 우선 검토 |
| 개선 후보 | row OOF와 artist OOF의 `all3_improve_prob >= 0.90`, fixed test p95 악화 없음 | 추가 반복 검증 |
| 목적별 후보 | MAPE 또는 p95만 개선되고 다른 지표가 약함 | 운영 기본 후보와 분리 |
| 연구 후보 | fixed test 또는 0604만 좋고 반복 OOF가 약함 | 문서화만 하고 미채택 |

## /goal 붙여넣기용 프롬프트

```text
Track6 가격 예측 프로젝트에서 Warm Huber 계열의 HCOEF17 이후 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수를 좋게 만드는 것이 아니라, 반복 검증과 운영 안정성을 함께 통과하는 최고 성능 후보를 찾는 것이다.

먼저 아래 문서를 읽고 현재 후보, 이미 실패한 실험 유형, 남은 검증 방향을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- docs/track6/experiments/warm_huber_max_performance_continuation_goal_prompt.md
- experiments/track6/PP-HCOEF11_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF12_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF13_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF14_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

현재 1차 기준 후보는 `hcoef2_size_reliability_cap005_s050`다.

- fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
- 0604 최신 라벨 stress test: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
- row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 1.0

최소 비교 기준은 `current_70_30`이다.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 최신 라벨 stress test: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

아래 결론은 반복하지 말아줘.

1. loose 기준가 Huber는 MdAPE/MAPE 개선 잠재력은 있지만 fixed test p95가 악화되어 기본 후보가 아니다.
2. capped blend, 조건부 routing, 면적단가 직접 잔차 피처, segmented 보정, risk-gated 결합, 원인 구간 median 보정은 반복 OOF 또는 p95 guard를 통과하지 못했다.
3. PP-V8/service component는 0604에서는 강했지만 HCOEF16에서 fixed test와 artist OOF 기준을 통과하지 못했다.
4. 0604 또는 test residual을 보고 새 보정값, 경계값, 가중치를 만들지 않는다.

새 실험은 마지막 완료된 번호를 확인한 뒤 `PP-HCOEF17`부터 이어서 관리해줘.

우선순위는 아래처럼 잡아줘.

1. 서비스 feature pipeline 통합 검증
   - 연구 산출물과 실제 서비스 피처 생성 결과가 같은지 확인한다.
   - artist_key 매핑, 유사 작품 기반 가격 피처, coverage tier, 표본 수, 가격 단위, 환율, 누락값 처리 차이를 감사한다.
   - 연구 후보가 운영 입력으로 재현될 때 성능이 유지되는지 확인한다.

2. 최신 라벨 원인 분석
   - 0604는 학습에 쓰지 않고 stress test로만 사용한다.
   - HCOEF 안정 후보가 틀리는 작품과 PP-V8 component가 맞추는 작품을 나눠 원인을 본다.
   - 원인 축은 예측 시점에 알 수 있는 피처만 사용한다.
   - 실제 가격 구간은 진단용으로만 쓰고 보정 기준으로 쓰지 않는다.

3. risk/quantile guard 결합
   - HCOEF 안정 후보를 기본 가격으로 유지한다.
   - 별도 risk 또는 quantile 모델은 큰 오차 가능성, 가격 범위, 신뢰도 조정에만 사용한다.
   - 점 예측을 크게 움직이는 후보와 가격 범위/신뢰도만 조정하는 후보를 분리한다.

4. 아주 작은 계수형 보정 재탐색
   - Huber residual 보정은 cap 0.02, 0.03, 0.05를 기본으로 둔다.
   - strength는 0.25, 0.50, 0.75를 비교한다.
   - 새 피처는 저차원으로 제한하고 계수 해석이 가능해야 한다.
   - artist meta, birth year, 활동량, 검색/전시 피처는 운영 시점에 실제로 생성 가능한 경우에만 사용한다.

검증 기준은 아래처럼 고정해줘.

1. 운영 기본 후보가 되려면 `hcoef2_size_reliability_cap005_s050` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 한다.
2. row OOF와 artist OOF의 `all3_improve_prob >= 0.90`이면 개선 후보로 본다.
3. row OOF와 artist OOF의 `all3_improve_prob >= 0.95`이고 fixed test와 0604에서 악화가 없으면 강한 후보로 본다.
4. fixed test p95_APE가 0.8064보다 악화되면 운영 기본 후보로 채택하지 않는다.
5. 0604 p95_APE가 0.9835보다 악화되면 운영 후보 승격을 보류한다.
6. fixed test만 좋아지는 후보, 0604만 좋아지는 후보는 연구 후보로만 남긴다.

실험 산출물은 아래 구조로 남겨줘.

- 실험 폴더: experiments/track6/PP-HCOEF17_짧은_설명
- 실행 스크립트: scripts/track6/run_pp_hcoef17_짧은_설명.py
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

최종 응답에는 아래 내용을 정리해줘.

- 실행한 실험 ID와 폴더
- 새 후보명과 후보 유형
- current_70_30 대비 개선폭
- hcoef2_size_reliability_cap005_s050 대비 개선폭
- row OOF와 artist OOF 반복 검증 결과
- fixed test와 0604 stress test 결과
- Huber 계수 또는 정책 해석
- 운영 후보 / 목적별 후보 / 보류 후보 판단
- 다음 실험에서 반복하지 말아야 할 점
```
