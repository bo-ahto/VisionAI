# Warm Huber 최고 성능 지속 실험 /goal 프롬프트

이 문서는 Codex의 `/goal` 기능에 바로 붙여 넣기 위한 최신 실행 프롬프트다.

- 최신본: HCOEF37 실행 이후에는 `docs/track6/experiments/warm_huber_hcoef37_continuation_goal_prompt.md`를 사용한다.
- 목적: Warm Huber 계열에서 현재 안정 후보를 넘는 후보를 찾되, fixed test 한 번의 점수가 아니라 반복 검증과 운영 안정성까지 통과하는 후보를 찾는다.
- 사용 방식: `/goal` 명령어 뒤에 아래 “붙여넣기용 프롬프트” 전체를 붙여 넣는다.
- 기준일: 2026-06-08.

## 1. 기준을 이렇게 잡는 이유

- `current_70_30`은 서비스 v0.1에서 설명 가능한 최소 기준선이다.
- `hcoef_stable`은 반복 검증에서 안정성이 확인된 현재 실제 비교 기준이다.
- `PP-HCOEF34~36`은 성능 개선 신호가 있으나, 아직 운영 확정 후보가 아니라 추가 검증 후보다.
- 따라서 새 실험의 목표는 `current_70_30`을 넘는 것이 아니라, 최종적으로 `hcoef_stable`을 안정적으로 넘는 것이다.

## 2. 고정 비교 기준

| 기준 | 후보 | 의미 | fixed test | 0604 stress | 역할 |
|---|---|---|---|---|---|
| 최소 기준 | `current_70_30` | 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% | MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996` | MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871` | 새 후보가 최소한 넘어야 하는 서비스 v0.1 기준선 |
| 운영 비교 기준 | `hcoef_stable` / `hcoef2_size_reliability_cap005_s050` | `current_70_30` 위에 Huber 잔차 보정을 작게 더한 안정 후보 | MdAPE `0.138803`, MAPE `0.272989`, p95_APE `0.806366`, RMSE_log `0.398822` | MdAPE `0.273062`, MAPE `0.374365`, p95_APE `0.983456` | 운영 후보가 넘겨야 하는 실제 기준 |
| 최근 재검증 후보 | `hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66` | HCOEF35 개선 후보를 기준가 신뢰도가 높은 구간에만 적용한 라우팅 후보 | MdAPE `0.138290`, MAPE `0.272926`, p95_APE `0.806031`, RMSE_log `0.398712` | MdAPE `0.273407`, MAPE `0.374441`, p95_APE `0.983456` | fixed test는 개선됐지만 반복 all3가 약해 추가 재검증 필요 |

## 3. 채택 기준

| 후보 유형 | 기준 | 판단 |
|---|---|---|
| 운영 후보 | `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95_APE가 모두 동등 또는 개선, 0604 악화 없음 | v0.1 후속 반영 검토 |
| 강한 검증 후보 | row/artist repeated `all3_improve_prob >= 0.95`, fixed test와 0604 악화 없음 | 확장 반복 검증 후 운영 후보 검토 |
| 일반 검증 후보 | row/artist repeated `all3_improve_prob >= 0.90`, fixed test p95_APE 악화 없음 | 다음 실험에서 재검증 |
| MAPE 특화 후보 | MAPE는 개선되지만 MdAPE 또는 p95_APE가 약함 | 운영 기본값과 분리 |
| p95 방어 후보 | 큰 오차는 줄지만 MdAPE/MAPE 개선폭이 작음 | 가격 범위/신뢰도 정책 후보 |
| 연구 후보 | fixed test 또는 0604만 좋고 반복 검증이 약함 | 문서화하고 기본 후보 미채택 |

## 4. 실험 금지 기준

- fixed test residual 또는 0604 residual을 보고 보정값, 가중치, 구간 경계를 만들지 않는다.
- 0604 데이터는 최신 신규 라벨 stress test이며, 후보 선택용 학습 데이터가 아니다.
- 실제 가격 구간은 운영 예측 시점에 알 수 없으므로 보정 기준으로 쓰지 않는다.
- fixed test MdAPE가 좋아져도 p95_APE가 `0.806366`보다 악화되면 운영 후보로 채택하지 않는다.
- 0604 p95_APE가 `0.983456`보다 악화되면 운영 후보 승격을 보류한다.
- 이미 실패한 동일 cap/strength grid를 반복하지 않는다.
- 설명 불가능한 고차원 조합은 성능이 좋아도 운영 후보가 아니라 연구 후보로 분리한다.

## 5. 다음 실험 우선순위

1. `PP-HCOEF37`: HCOEF36 상위 라우팅 후보 확장 반복 검증
   - 대상 후보: `spread_q66`, `n_ge5_spread_q66`, `n_ge5_spread_q66_area90`.
   - 목적: fixed test 개선이 반복 split에서도 유지되는지 확인.
   - 기준: row OOF와 artist OOF 각각 50회 이상 반복, 가능하면 all3 개선 확률 `0.90` 이상.

2. `PP-HCOEF38`: 기준가 신뢰도 라우팅 경계 재검증
   - 대상 피처: `basis_component_spread`, `basis_n_log`, `fallback_level`, `log_area`, `stable_ppv8_gap_abs`.
   - 목적: 기준가를 믿을 수 있는 구간에만 HCOEF34/35 계열 보정을 적용.
   - 기준: 경계는 validation/OOF에서만 정하고 fixed test/0604로 정하지 않음.

3. `PP-HCOEF39`: Huber 계수 세분화
   - 대상 피처: 기준가 후보, 기준가 간 gap, 크기, 표본 수, 신뢰도, fallback level.
   - 목적: Huber 선형 계수를 이용해 어떤 피처가 가격을 올리거나 낮추는지 설명 가능한 후보 생성.
   - 기준: 계수 방향이 해석 가능하고 cap/strength가 작아야 함.

4. `PP-HCOEF40`: 목적별 후보 분리
   - 대상: MdAPE 최적 후보, MAPE 최적 후보, p95 방어 후보.
   - 목적: 하나의 후보에 모든 목표를 강제하지 않고 목적별로 후보를 분리한 뒤 운영 후보만 엄격하게 선택.
   - 기준: 운영 후보는 all3 안정성, 목적별 후보는 문서상 분리.

5. `PP-HCOEF41`: 신뢰도/가격 범위 정책 실험
   - 대상: 점 예측을 바꾸지 않고 가격 범위와 신뢰도만 조정하는 후보.
   - 목적: 점 예측 p95를 무리하게 낮추기보다 서비스 표시 안정성을 높임.
   - 기준: 점 예측 후보와 범위/신뢰도 후보를 분리해 평가.

## 6. 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 현재 안정 후보를 넘기기 위한 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수를 좋게 만드는 것이 아니라, 반복 검증과 운영 안정성까지 통과하는 최고 성능 후보를 찾는 것이다. 실험은 기존 HCOEF 실험 구조를 유지하고, 마지막 완료 번호 이후부터 이어서 관리해줘.

먼저 아래 문서를 읽고 현재 후보, 실패한 실험 유형, 남은 검증 방향을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_hcoef36_continuation_goal_prompt.md
- experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

비교 기준은 아래처럼 고정해줘.

1. 최소 기준은 `current_70_30`이다.
   - 의미: 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합.
   - fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
   - 0604 stress: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871
   - 새 후보가 최소한 넘어야 하는 서비스 v0.1 기준선이다.

2. 운영 비교 기준은 `hcoef_stable` 또는 `hcoef2_size_reliability_cap005_s050`이다.
   - fixed test: MdAPE 0.138803, MAPE 0.272989, p95_APE 0.806366, RMSE_log 0.398822
   - 0604 stress: MdAPE 0.273062, MAPE 0.374365, p95_APE 0.983456
   - row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 모두 1.0
   - 운영 후보가 넘겨야 하는 실제 비교 기준이다.

3. 최근 재검증 후보는 `hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66`이다.
   - fixed test: MdAPE 0.138290, MAPE 0.272926, p95_APE 0.806031, RMSE_log 0.398712
   - 0604 stress: MdAPE 0.273407, MAPE 0.374441, p95_APE 0.983456
   - hcoef_stable 대비 fixed test MdAPE/MAPE/p95는 모두 소폭 개선됐다.
   - 다만 row/artist stable all3 반복 확률이 0.375/0.375로 낮아 운영 후보가 아니라 추가 재검증 후보로 둔다.

채택 기준은 아래처럼 적용해줘.

1. 새 후보는 최소한 `current_70_30`보다 좋아야 한다.
2. 운영 후보가 되려면 `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95_APE가 모두 동등 또는 개선되어야 한다.
3. row OOF와 artist OOF의 repeated `all3_improve_prob >= 0.95`이고 fixed test와 0604에서 악화가 없으면 강한 검증 후보로 본다.
4. row OOF와 artist OOF의 repeated `all3_improve_prob >= 0.90`이고 fixed p95_APE 악화가 없으면 일반 검증 후보로 본다.
5. fixed test p95_APE가 0.806366보다 악화되면 운영 후보로 채택하지 않는다.
6. 0604 p95_APE가 0.983456보다 악화되면 운영 후보 승격을 보류한다.
7. fixed test residual 또는 0604 residual을 보고 새 보정값, 경계값, 가중치를 만들지 않는다.
8. 실제 가격 구간은 원인 진단용으로만 쓰고 보정 기준으로 쓰지 않는다.
9. 운영 예측 시점에 알 수 없는 값은 피처나 라우팅 기준으로 쓰지 않는다.

후보 유형은 반드시 분리해줘.

- 운영 후보: MdAPE/MAPE/p95_APE가 모두 안정적인 후보.
- 강한 검증 후보: 반복 검증은 강하고 fixed/0604도 악화가 없는 후보.
- MAPE 특화 후보: MAPE는 개선되지만 MdAPE 또는 p95_APE 위험이 남는 후보.
- p95 방어 후보: 큰 오차는 줄지만 중앙 오차 개선폭은 작은 후보.
- 신뢰도/범위 후보: 점 예측보다 가격 범위나 신뢰도 표시 개선에 적합한 후보.
- 연구 후보: 성능 잠재력은 있지만 반복 검증 또는 운영 안정성이 부족한 후보.

우선 실험은 아래 순서로 진행해줘.

1. HCOEF36 상위 라우팅 후보 확장 반복 검증
   - 대상 후보는 `hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66`, `hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66`, `hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90`이다.
   - row OOF와 artist OOF를 각각 50회 이상 반복해 fixed test 개선이 우연인지 확인한다.
   - 반복 검증에서 all3 확률이 낮으면 운영 후보가 아니라 연구 후보로 유지한다.

2. 기준가 신뢰도 라우팅 경계 재검증
   - HCOEF34/35는 전체 교체 후보가 아니라 MdAPE/MAPE 개선 신호 후보로 본다.
   - 안정 구간에는 HCOEF34/35 계열 후보를 적용하고, 위험 구간에는 `hcoef_stable`을 유지하는 라우팅을 검증한다.
   - 라우팅 기준 후보는 `basis_component_spread`, `basis_n_log`, `fallback_level`, `log_area`, `stable_ppv8_gap_abs`, `price_range_ratio`, `quantile_width`로 둔다.
   - 구간 경계는 validation/OOF에서만 만들고 fixed test와 0604로 만들지 않는다.

3. Huber 계수 세분화
   - Huber가 선형 계수를 학습한다는 특성을 활용해 기준가, 크기, 표본 수, 신뢰도, 후보 간 gap 피처의 계수를 직접 조정한다.
   - 우선 피처 후보는 `current_70_30`, `hcoef_stable`, `svc`, `ppv8`, `log_area`, `svc_group_n_log`, `svc_prior_iqr`, `stable_ppv8_gap_abs`, `basis_component_spread`, `fallback_level`, `price_range_ratio`, `quantile_width`로 둔다.
   - 계수 방향이 설명 가능한 저차원 조합부터 검증한다.
   - 피처가 많아질 경우 L2, ElasticNet, cap, strength로 과적합을 방어한다.

4. 목적별 후보 분리
   - MdAPE 최적 후보, MAPE 최적 후보, p95 방어 후보를 분리해서 만든다.
   - 운영 후보는 세 지표가 모두 안정적인 후보만 채택한다.
   - MAPE 특화 후보나 p95 방어 후보는 서비스 점 예측 기본값이 아니라 보조 정책 후보로 문서화한다.

5. 신뢰도/가격 범위 정책 실험
   - 점 예측을 무리하게 움직이지 않고 가격 범위와 신뢰도만 조정하는 후보를 별도로 검증한다.
   - quantile width, 기준가 component spread, fallback level, 표본 수를 이용해 가격 범위와 신뢰도 tier를 조정한다.
   - 점 예측 후보와 범위/신뢰도 후보를 분리 평가한다.

실험 관리 규칙은 아래처럼 지켜줘.

- `experiments/track6/` 아래에 실험별 독립 폴더를 만든다.
- 새 실험은 `PP-HCOEF##_짧은_설명` 형식으로 관리한다.
- 기존 실험 번호와 충돌하지 않게 마지막 완료 번호 이후부터 시작한다.
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
- docs/track6/experiments/warm_huber_hcoef36_continuation_goal_prompt.md

최종 응답에는 아래 내용을 요약해줘.

- 실행한 실험 ID와 폴더
- 새 후보명과 후보 유형
- current_70_30 대비 개선폭
- hcoef_stable 대비 개선폭
- row OOF와 artist OOF 반복 검증 결과
- fixed test와 0604 stress 결과
- Huber 계수 또는 보정 정책 해석
- 운영 후보 / 목적별 후보 / 보류 후보 판단
- 다음 실험에서 반복하지 말아야 할 점
```
