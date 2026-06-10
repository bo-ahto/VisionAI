# Warm Huber 최고 성능 탐색용 Codex /goal 프롬프트

이 문서는 Codex의 `/goal` 기능으로 Warm Huber 계열 실험을 계속 이어가기 위한 붙여넣기용 프롬프트다.

- 사용 방식: `/goal` 명령어 뒤에 아래 프롬프트 전체를 붙여 넣는다.
- 권장 방식: 문서 경로만 넣기보다, 목표/기준/금지 조건/산출물 기준을 함께 넣는다.
- 핵심 기준: 현재 반복 검증을 통과한 `hcoef2_size_reliability_cap005_s050`를 1차 기준으로 둔다.

## 기준 설정

| 구분 | 후보 | 의미 | fixed test | 0604 stress test | 역할 |
| --- | --- | --- | --- | --- | --- |
| 최소 기준 | `current_70_30` | 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% | MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996` | MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871` | 서비스 v0.1 기준 후보 |
| 1차 기준 | `hcoef2_size_reliability_cap005_s050` | `current_70_30` 위에 Huber 잔차 보정을 작게 더한 후보 | MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988` | MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835` | 현재 넘어야 할 기준 |

## 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 현재 최고 후보를 넘기기 위한 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수만 좋게 만드는 것이 아니라, 반복 검증과 운영 안정성까지 통과하는 최고 성능 후보를 찾는 것이다.

먼저 아래 문서를 읽고 현재 후보, 이미 시도한 실험, 실패한 방식, 운영 재현성 검증 상태를 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_continuous_max_performance_goal_prompt.md
- docs/track6/experiments/warm_huber_hcoef22_continuation_goal_prompt.md
- experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

현재 1차 기준 후보는 `hcoef2_size_reliability_cap005_s050`다.

- fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
- 0604 최신 라벨 stress test: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
- row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 1.0

최소 비교 기준은 서비스 v0.1 후보 `current_70_30`이다.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 최신 라벨 stress test: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

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

후보 유형은 반드시 분리해줘.

- 운영 기본 후보: MdAPE/MAPE/p95가 모두 안정적으로 개선되는 후보.
- MAPE 특화 후보: MAPE는 개선되지만 MdAPE 또는 p95 위험이 남는 후보.
- p95 방어 후보: 큰 오차를 줄이지만 중앙 오차 개선폭은 작은 후보.
- 신뢰도/범위 정책 후보: 점 예측은 크게 바꾸지 않고 예측 범위와 신뢰도 표시를 개선하는 후보.
- 연구 후보: 일부 데이터에서는 좋지만 반복 OOF 또는 fixed test 안정성이 부족한 후보.

우선 실험 방향은 아래 순서로 잡아줘.

1. 현재 최고 후보의 작품별 오차 원인 분석
   - residual_log = actual_log - pred_log로 오차를 정의한다.
   - 기준가 표본 수, 기준가 fallback level, 기준가 IQR, 작품 크기, 재료/지지체 bucket, 후보 간 예측 gap, quantile width, service confidence tier별로 오차를 나눈다.
   - 실제 가격 구간은 결과 해석용으로만 쓰고 보정 기준으로 쓰지 않는다.

2. 기준가 생성 방식 고도화
   - 작가 전체 기준가, 작가+크기 기준가, 작가+재료/지지체 기준가, 작가+크기+재료/지지체 기준가를 비교한다.
   - 최소 표본 수, fallback 순서, IQR 완화, 표본 수 기반 shrinkage, 최근 거래 가중치를 비교한다.
   - 기준가는 train/validation 안에서만 만들고 test 정보는 쓰지 않는다.

3. Huber 계수 조정 고도화
   - Huber가 로그 가격을 선형 계수로 조정한다는 특성을 활용한다.
   - 기준가, 크기, 신뢰도, 후보 간 gap, quantile width의 계수 방향과 크기를 확인한다.
   - 기본 후보 피처는 `current_70_30`, `svc_numeric_seed_mean`, `ppv8_service_proxy`, `l10_seq_pred_log`, `hcoef_stable`, `quantile_width`, `l10_price_range_ratio`, `svc_group_n_log`, `coverage_numeric`, 후보 간 gap으로 둔다.
   - 작가 생년, 활동량, 갤러리 tier, 전시 횟수, 검색 피처는 운영 예측 시점에 알 수 있고 기존 정리 파일이 있을 때만 보조 피처로 넣는다.

4. 잔차 보정 모델 비교
   - 잔차는 `residual_log = actual_log - pred_log`로 정의한다.
   - 보정 모델은 OOF 예측 residual로만 학습한다.
   - Huber residual, Ridge/ElasticNet residual, Quantile residual, 작은 CatBoost residual을 비교한다.
   - Huber residual 보정에는 cap과 strength를 둔다.
   - cap 후보는 0.02, 0.03, 0.05를 기본으로 하고 0.08, 0.12는 공격형 후보로 분리한다.
   - strength 후보는 0.25, 0.50, 0.75로 둔다.

5. 원인 구간별 라우팅
   - 전체 가중치만 바꾸지 말고, 예측 시점에 알 수 있는 원인 구간별로 후보를 선택한다.
   - 안정 구간은 현재 최고 후보를 유지한다.
   - 위험 구간은 기준가-Huber, 잔차-Huber, p95 방어 후보, 보수형 fallback을 비교한다.
   - 라우팅 기준은 운영 예측 시점에 알 수 있는 피처만 사용한다.

6. quantile/risk guard 활용
   - quantile width는 우선 점 예측 이동보다 예측 범위와 신뢰도 표시 기준으로 사용한다.
   - q10/q50/q90, q90-q10 로그 폭, price_range_ratio, service_confidence_tier를 사용한다.
   - validation 기준으로 범위/신뢰도 구간을 정의하고 fixed test와 0604에서 실제 포함률, MdAPE/MAPE/p95, 큰 오차율을 확인한다.
   - 점 예측 후보와 신뢰도/범위 정책 후보를 분리한다.
   - PP-HCOEF20에서는 quantile width가 점 예측 이동보다 가격 범위/신뢰도 정책에 더 적합하다고 확인했으므로, 이후에는 해당 정책 고도화를 우선한다.
   - PP-HCOEF21에서는 가변 SVC:PP-V8 기준가가 MAPE를 일부 낮췄지만 p95와 bootstrap gate를 통과하지 못했으므로, 같은 방식은 운영 기본 후보 탐색으로 반복하지 않는다.

반복하지 말아야 할 방식은 아래와 같다.

1. fixed test만 좋은 후보를 운영 후보로 승격하지 않는다.
2. 0604만 좋은 후보를 운영 후보로 승격하지 않는다.
3. test 또는 0604 residual을 보고 보정 경계와 가중치를 새로 만들지 않는다.
4. PP-HCOEF18처럼 quantile width로 점 예측을 직접 움직이는 방식은 그대로 반복하지 않는다.
5. PP-HCOEF19에서 완료된 운영 feature pipeline 감사는 같은 형태로 반복하지 않는다.
6. PP-HCOEF20에서 완료한 운영 component 기반 저차원 Huber/Ridge residual grid와 direct stack grid는 같은 피처, 같은 cap/strength 조합으로 반복하지 않는다.
7. PP-HCOEF21에서 완료한 가변 SVC:PP-V8 기준가와 adaptive reliability/interactions residual grid는 같은 피처, 같은 cap/strength 조합으로 반복하지 않는다.

실험 관리 규칙은 아래처럼 지켜줘.

- 마지막 완료된 HCOEF 번호를 확인한 뒤 다음 번호로 이어서 관리한다. 현재 PP-HCOEF21까지 완료되어 있으면 PP-HCOEF22부터 시작한다.
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
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- docs/track6/experiments/warm_huber_max_performance_continuation_goal_prompt.md
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

## 기준 선택 이유

- `current_70_30`만 기준으로 잡으면 이미 개선된 HCOEF 후보를 놓칠 수 있음.
- `hcoef2_size_reliability_cap005_s050`는 fixed test뿐 아니라 row OOF/artist OOF 반복 검증을 통과했기 때문에 현재 실험의 1차 기준으로 적합함.
- 0604 데이터는 신규 운영 유사 데이터라 중요하지만, 데이터 정합성/분포 차이가 있으므로 후보 선택 기준이 아니라 스트레스 테스트 기준으로 쓰는 것이 안전함.
- Huber의 장점은 선형 계수 해석과 이상치 완화이므로, 새 실험은 복잡한 모델 탐색보다 기준가, 신뢰도, 크기, 후보 간 gap의 계수 조정에 우선순위를 둠.
