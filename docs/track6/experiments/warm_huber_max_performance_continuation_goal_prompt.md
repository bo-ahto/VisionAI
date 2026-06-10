# Warm Huber 최고 성능 지속 탐색 /goal 프롬프트

이 문서는 Codex의 `/goal` 기능으로 Warm Huber 계열 실험을 계속 이어가기 위한 붙여넣기용 프롬프트다.

## 1. 기준 설정

- 서비스 v0.1 기준 후보: `current_70_30`
  - 의미: 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합.
  - fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996`.
  - 0604 stress: MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871`.
  - 역할: 새 후보가 최소한 넘어야 하는 서비스 기준선.

- 현재 안정 개선 후보: `hcoef_stable` / `hcoef2_size_reliability_cap005_s050`
  - 의미: 서비스 v0.1 기준 후보 위에 Huber 잔차 보정을 작게 더한 Warm 안정 후보.
  - fixed test: MdAPE `0.138803`, MAPE `0.272989`, p95_APE `0.806366`, RMSE_log `0.398822`.
  - 0604 stress: MdAPE `0.273062`, MAPE `0.374365`, p95_APE `0.983456`.
  - 반복 검증: row OOF와 artist OOF에서 MdAPE/MAPE/p95 개선 확률 모두 `1.0`.
  - 역할: 운영 후보가 넘겨야 하는 실제 비교 기준.

- 최근 확인 후보: `PP-HCOEF33`
  - 의미: HCOEF32 핵심 후보를 새로 튜닝하지 않고 row/artist 확장 반복 검증으로 재확인.
  - 핵심 후보: `hcoef32_s03_all3_dir_top2_w0p025_cap0p001`.
  - fixed test: MdAPE `0.138803`, MAPE `0.272948`, p95_APE `0.806244`, RMSE_log `0.398810`.
  - 0604 stress: MdAPE `0.272680`, MAPE `0.374361`, p95_APE `0.983448`.
  - 확장 반복 검증: min any2/all3 `0.8085 / 0.2785`.
  - 판단: fixed test와 0604에서 아주 작게 좋아졌지만 반복 all3가 낮아 운영 후보로 승격하지 않음.

- 최신 기준가 재탐색 후보: `PP-HCOEF34`
  - 의미: train-only 기준가를 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체, fallback, shrinkage 기준으로 다시 만들고 Huber 잔차 계수로 보정.
  - 핵심 후보: `hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5`.
  - fixed test: MdAPE `0.137345`, MAPE `0.272922`, p95_APE `0.807383`, RMSE_log `0.398674`.
  - 0604 stress: MdAPE `0.274877`, MAPE `0.374597`, p95_APE `0.983456`.
  - 판단: `current_70_30`보다 좋아졌고 `hcoef_stable`보다 MdAPE/MAPE는 좋아졌지만 p95가 약 `0.0010` 악화되어 운영 후보로 바로 승격하지 않음.

- 최신 p95 방어 fine grid: `PP-HCOEF35`
  - 의미: HCOEF34의 기준가 잔차 피처를 유지하고 cap/strength를 더 촘촘하게 낮춰 p95 방어 가능성을 확인.
  - best MdAPE 후보: `hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p35`.
  - fixed test: MdAPE `0.136510`, MAPE `0.272910`, p95_APE `0.807790`.
  - p95 근접 후보: fixed p95_APE `0.806407`.
  - 판단: MdAPE/MAPE는 더 좋아졌지만 `hcoef_stable`의 p95_APE `0.806366`을 정확히 넘는 후보는 없음. 같은 cap/strength fine grid 반복은 우선순위 낮음.

## 2. 최고 성능 판단 기준

- 1순위: 운영 안정성
  - `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 함.
  - fixed test 한 번만 좋아진 후보는 운영 후보로 바로 채택하지 않음.
  - 0604 stress에서 p95 또는 MAPE가 명확히 악화되면 운영 승격 보류.

- 2순위: 큰 오차 방어
  - fixed test p95_APE가 `0.806366`보다 악화되면 운영 기본 후보로 채택하지 않음.
  - 0604 p95_APE가 `0.983456`보다 악화되면 운영 후보 승격을 보류.
  - MAPE가 좋아져도 p95가 나빠지면 MAPE 특화 후보로 분리.

- 3순위: 중앙 오차와 평균 오차
  - MdAPE: 일반적인 작품에서 예측이 얼마나 안정적인지 보는 기준.
  - MAPE: 큰 비율 오차까지 포함해 평균적으로 얼마나 덜 틀리는지 보는 기준.
  - 새 후보는 최소한 `current_70_30`보다 좋아야 하고, 가능하면 `hcoef_stable`을 넘어야 함.

- 4순위: 설명 가능성과 운영 가능성
  - Huber의 선형 계수, 기준가 이동 방향, 보정 cap, segment 조건이 설명 가능해야 함.
  - test residual 또는 0604 residual을 보고 보정 기준을 만들지 않음.
  - 운영 예측 시점에 알 수 없는 값은 피처나 라우팅 기준으로 사용하지 않음.

## 3. 후보 분류 기준

| 후보 유형 | 기준 | 처리 |
|---|---|---|
| 운영 후보 | `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되고 0604 악화 없음 | v0.1 후속 반영 검토 |
| 강한 검증 후보 | row/artist repeated `all3_improve_prob >= 0.95`, fixed/0604 악화 없음 | 확장 반복 검증 후 운영 후보 검토 |
| 일반 검증 후보 | row/artist repeated `all3_improve_prob >= 0.90`, fixed p95 악화 없음 | 다음 실험에서 재검증 |
| MAPE 특화 후보 | MAPE는 명확히 개선되지만 MdAPE 또는 p95가 약함 | 운영 기본값과 분리, 목적별 후보로만 관리 |
| p95 방어 후보 | 큰 오차는 줄지만 MdAPE/MAPE 개선폭이 작음 | 가격 범위/신뢰도 정책 후보로 관리 |
| 연구 후보 | OOF 또는 0604는 좋지만 fixed/repeated 중 하나가 약함 | 문서화하고 기본 후보 미채택 |

## 4. 다음 실험 우선순위

- 1순위: HCOEF34/35 후보의 목적별 라우팅
  - HCOEF34/35는 MdAPE/MAPE 개선 신호가 있으나 p95 guard를 통과하지 못함.
  - 전체 교체가 아니라 안정 구간에만 HCOEF34/35를 쓰고 위험 구간은 `hcoef_stable`을 유지하는 라우팅을 먼저 검증.
  - 라우팅 기준은 validation/OOF에서만 만들고 fixed test와 0604로 만들지 않음.

- 2순위: 기준가 신뢰도 기반 shrinkage
  - HCOEF34에서 기준가 gap 피처는 성능 신호가 확인됨.
  - 표본 수가 적거나 기준가 컴포넌트 간 차이가 큰 구간은 기준가를 약하게 반영.
  - 표본 수가 충분하고 component spread가 작은 구간은 기준가를 더 강하게 반영.

- 3순위: p95 위험 구간 분리
  - 주요 위험 축: `qwidth_extreme`, `gap_020_plus`, `n_10_19`, `spread_extreme`, fallback level.
  - 안정 구간은 MdAPE/MAPE 개선 후보를 적용.
  - 위험 구간은 `hcoef_stable`, ultra-micro correction, 보수형 fallback 중 선택.

- 4순위: Huber 계수 세분화
  - Huber가 선형 계수를 학습한다는 점을 활용해 기준가, 크기, 신뢰도, 후보 간 gap 피처의 계수를 조정.
  - 기준가 피처와 reliability 피처를 함께 넣어 “기준가를 언제 얼마나 믿을지”를 계수로 학습.
  - 과도한 피처 확장은 피하고, 계수 방향이 설명 가능한 저차원 조합부터 검증.

- 5순위: 잔차 보정 모델 비교
  - `residual_log = actual_log - pred_log`로 정의.
  - OOF residual로만 보정 모델을 학습.
  - Huber residual, Ridge/ElasticNet residual, Quantile residual, 작은 CatBoost residual을 비교.
  - 큰 cap/strength 후보는 공격형으로 분리하고 운영 후보와 섞지 않음.

## 5. /goal 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 현재 안정 후보를 넘기기 위한 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수를 좋게 만드는 것이 아니라, 반복 검증과 운영 안정성을 함께 통과하는 최고 성능 후보를 찾는 것이다. 실험은 기존 HCOEF 실험 구조를 유지하고, 마지막 완료 번호 이후부터 이어서 관리해줘.

먼저 아래 문서를 읽고 현재 후보, 실패한 실험 유형, 남은 검증 방향을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_max_performance_continuation_goal_prompt.md
- experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

비교 기준은 아래처럼 고정해줘.

1. 서비스 v0.1 기준 후보는 `current_70_30`이다.
   - 의미: 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합.
   - fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
   - 0604 stress: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871
   - 새 후보가 최소한 넘어야 하는 서비스 기준선이다.

2. 현재 안정 개선 후보는 `hcoef_stable` 또는 `hcoef2_size_reliability_cap005_s050`이다.
   - fixed test: MdAPE 0.138803, MAPE 0.272989, p95_APE 0.806366, RMSE_log 0.398822
   - 0604 stress: MdAPE 0.273062, MAPE 0.374365, p95_APE 0.983456
   - row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 모두 1.0
   - 운영 후보가 넘겨야 하는 실제 비교 기준이다.

3. `PP-HCOEF33`은 fixed test와 0604에서 아주 작게 좋아졌지만 반복 all3가 낮아 운영 후보로 승격하지 않는다.
   - 후보: `hcoef32_s03_all3_dir_top2_w0p025_cap0p001`
   - fixed test: MdAPE 0.138803, MAPE 0.272948, p95_APE 0.806244, RMSE_log 0.398810
   - 0604 stress: MdAPE 0.272680, MAPE 0.374361, p95_APE 0.983448
   - extended repeated any2/all3: 0.8085 / 0.2785
   - 같은 초미세 이동을 단순 반복하지 않는다.

4. `PP-HCOEF34`는 기준가 생성 방식 재탐색으로 MdAPE/MAPE 개선 신호를 확인했지만 p95 guard를 통과하지 못했다.
   - 후보: `hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5`
   - fixed test: MdAPE 0.137345, MAPE 0.272922, p95_APE 0.807383, RMSE_log 0.398674
   - 0604 stress: MdAPE 0.274877, MAPE 0.374597, p95_APE 0.983456
   - `hcoef_stable` 대비 MdAPE/MAPE는 좋아졌지만 p95가 약 0.0010 악화된다.

5. `PP-HCOEF35`는 HCOEF34 피처로 cap/strength를 더 촘촘하게 낮췄지만 p95 guard 통과 후보가 없었다.
   - best MdAPE 후보: fixed MdAPE 0.136510, MAPE 0.272910, p95_APE 0.807790
   - p95 근접 후보: fixed p95_APE 0.806407
   - `hcoef_stable`의 fixed p95_APE 0.806366을 정확히 넘지 못했다.
   - 같은 cap/strength fine grid를 다시 반복하지 말고, 라우팅 또는 위험 구간 분리로 넘어간다.

채택 기준은 아래처럼 적용해줘.

1. 새 후보는 최소한 `current_70_30`보다 좋아야 한다.
2. 운영 후보가 되려면 `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 한다.
3. row OOF와 artist OOF의 repeated `all3_improve_prob >= 0.95`이고 fixed test와 0604에서 악화가 없으면 강한 검증 후보로 본다.
4. row OOF와 artist OOF의 repeated `all3_improve_prob >= 0.90`이고 fixed p95 악화가 없으면 일반 검증 후보로 본다.
5. fixed test p95_APE가 0.806366보다 악화되면 운영 기본 후보로 채택하지 않는다.
6. 0604 p95_APE가 0.983456보다 악화되면 운영 후보 승격을 보류한다.
7. 0604 신규 라벨, fixed test residual, 실제 가격 구간을 보고 보정값이나 구간 경계를 만들지 않는다.
8. 운영 예측 시점에 알 수 없는 값은 피처나 라우팅 기준으로 쓰지 않는다.

후보 유형은 반드시 분리해줘.

- 운영 후보: MdAPE/MAPE/p95가 모두 안정적인 후보.
- 강한 검증 후보: 반복 검증은 강하고 fixed/0604도 악화가 없는 후보.
- MAPE 특화 후보: MAPE는 개선되지만 MdAPE 또는 p95 위험이 남는 후보.
- p95 방어 후보: 큰 오차는 줄지만 중앙 오차 개선폭은 작은 후보.
- 연구 후보: 성능 잠재력은 있지만 반복 검증 또는 운영 안정성이 부족한 후보.

우선 실험은 아래 순서로 진행해줘.

1. HCOEF34/35 목적별 라우팅
   - HCOEF34/35는 전체 교체 후보가 아니라 MdAPE/MAPE 개선 신호 후보로 본다.
   - 안정 구간에는 HCOEF34/35 계열 후보를 적용하고, 위험 구간에는 `hcoef_stable`을 유지하는 라우팅을 검증한다.
   - 라우팅 기준 후보는 `quantile_width`, `price_range_ratio`, `basis_component_spread`, `fallback_level`, `basis_n_log`, `stable_ppv8_gap_abs`, `log_area`로 둔다.
   - 구간 경계는 validation/OOF에서만 만들고 fixed test와 0604로 만들지 않는다.

2. 기준가 신뢰도 기반 shrinkage
   - 기준가가 믿을 만한 구간과 불안정한 구간을 나누어 기준가 반영 강도를 다르게 한다.
   - 표본 수가 충분하고 component spread가 작은 구간은 HCOEF34/35 계열 이동을 더 허용한다.
   - 표본 수가 적거나 component spread가 큰 구간은 `hcoef_stable` 또는 fallback 기준가 쪽으로 수축한다.
   - shrinkage 강도는 validation에서 선택하고 test/0604는 확인용으로만 사용한다.

3. p95 위험 구간 분리
   - 주요 위험 축은 `qwidth_extreme`, `gap_020_plus`, `n_10_19`, `spread_extreme`, fallback level이다.
   - 안정 구간은 MdAPE/MAPE 개선 후보를 적용한다.
   - 위험 구간은 `hcoef_stable`, ultra-micro correction, 보수형 fallback, 기준가 shrinkage를 비교한다.
   - 목표는 p95_APE 0.806366 이하를 유지하면서 MdAPE/MAPE를 낮추는 것이다.

4. Huber 계수 세분화
   - Huber가 선형 계수를 학습한다는 특성을 활용해 기준가, 크기, 신뢰도, 후보 간 gap 피처의 계수를 직접 조정한다.
   - 우선 피처 후보는 `current_70_30`, `hcoef_stable`, `svc`, `ppv8`, `quantile_width`, `price_range_ratio`, `log_area`, `svc_group_n_log`, `svc_prior_iqr`, `current_ppv8_gap`, `stable_ppv8_gap_abs`, `basis_component_spread`, `fallback_level`로 둔다.
   - 계수 방향이 설명 가능한 저차원 조합부터 검증한다.
   - 피처가 많아질 경우 L2/ElasticNet 또는 cap으로 과적합을 방어한다.

5. 잔차 보정 모델 비교
   - `residual_log = actual_log - pred_log`로 정의한다.
   - OOF residual로만 보정 모델을 학습한다.
   - Huber residual, Ridge/ElasticNet residual, Quantile residual, 작은 CatBoost residual을 비교한다.
   - cap 후보는 0.001, 0.0025, 0.005, 0.01, 0.02, 0.03, 0.05로 둔다.
   - strength 후보는 0.025, 0.05, 0.10, 0.25, 0.50, 0.75로 둔다.
   - 큰 cap이나 큰 strength는 공격형 후보로 분리해서 운영 후보와 섞지 않는다.

6. 0604 stress test
   - 0604 데이터는 학습에 쓰지 않고 검증만 한다.
   - 환율, 가격 단위, Warm/Cold 분기, artist_key 매핑, feature coverage를 먼저 감사한다.
   - 기존 후보와 새 후보를 같은 metric, 같은 제외 기준으로 비교한다.

실험 관리 규칙은 아래처럼 지켜줘.

- `experiments/track6/` 아래에 실험별 독립 폴더를 만든다.
- 새 실험은 `PP-HCOEF##_짧은_설명` 형식으로 관리한다.
- 기존 실험 번호와 충돌하지 않게 마지막 완료 번호 이후부터 시작한다.
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
- docs/track6/experiments/warm_huber_max_performance_continuation_goal_prompt.md

최종 응답에는 아래 내용을 요약해줘.

- 실행한 실험 ID와 폴더
- 새 후보명과 후보 유형
- current_70_30 대비 개선폭
- hcoef_stable 대비 개선폭
- row OOF와 artist OOF 반복 검증 결과
- fixed test와 0604 stress 결과
- Huber 계수 또는 보정값 해석
- 운영 후보 / 목적별 후보 / 보류 후보 판단
- 다음 실험에서 반복하지 말아야 할 점
```
