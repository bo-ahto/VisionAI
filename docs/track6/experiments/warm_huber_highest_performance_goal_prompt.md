# Warm Huber 최고 성능 탐색 /goal 프롬프트

이 문서는 Codex의 `/goal` 명령어 뒤에 그대로 붙여 넣기 위한 실행용 프롬프트다.

목표는 Warm Huber 계열에서 지금까지의 최고 후보를 넘는 새 후보를 찾는 것이다. 단, fixed test 한 번만 좋아지는 후보가 아니라 반복 검증과 운영 안정성까지 통과하는 후보를 찾는 것을 기준으로 한다.

## 판단 기준

- 1차 기준 후보: `hcoef2_size_reliability_cap005_s050`
  - 의미: `current_70_30` 위에 Huber 잔차 보정을 작게 더한 현재 Warm 개선 후보.
  - fixed test: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988`.
  - 0604 신규 라벨 일부 확인: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
  - 반복 검증: row OOF와 artist OOF에서 MdAPE/MAPE/p95 개선 확률 모두 `1.0`.

- 서비스 v0.1 기준 후보: `current_70_30`
  - 의미: 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합.
  - fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996`.
  - 0604 신규 라벨 일부 확인: MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871`.

- 새 운영 후보 기준:
  - `hcoef2_size_reliability_cap005_s050` 대비 fixed test MdAPE/MAPE/p95_APE가 모두 동등 또는 개선.
  - fixed test p95_APE가 `0.8064`보다 악화되지 않음.
  - row OOF와 artist OOF에서 MdAPE/MAPE/p95 평균이 모두 개선.
  - row OOF와 artist OOF의 `all3_improve_prob >= 0.90`.
  - 가능하면 `all3_improve_prob >= 0.95`일 때 강한 후보로 판단.
  - 0604 신규 라벨 일부 확인에서는 최종 채택이 아니라 stress test로만 사용.

- 목적별 후보 기준:
  - MdAPE 특화 후보: 대표 오차를 낮추는 후보. MAPE/p95 악화가 있으면 운영 기본 후보와 분리.
  - MAPE 특화 후보: 평균 비율 오차를 낮추는 후보. MdAPE/p95 악화가 있으면 운영 기본 후보와 분리.
  - p95 방어 후보: 큰 오차를 줄이는 후보. MdAPE 개선폭이 작아도 별도 목적 후보로 유지.
  - 연구 후보: fixed test나 0604는 좋지만 반복 OOF가 부족한 후보. 운영 후보로 바로 올리지 않음.

- 중단 기준:
  - test 지표를 보고 보정값, 가중치, 구간 경계를 다시 정하면 중단.
  - fixed test만 좋고 반복 OOF가 약하면 보류.
  - MdAPE는 좋아지지만 p95_APE가 악화되면 운영 기본 후보에서 제외.
  - 복잡도가 커졌는데 개선폭이 아주 작으면 보류.

## 우선 실험 방향

1. 남은 큰 오차 원인 진단
   - 현재 최고 후보의 작품별 residual을 분석.
   - 기준가 표본 수, 기준가 분산, 예측 가격대, 작품 크기, 재료/지지체 bucket, 작가 이력량, 후보 간 예측 gap으로 원인 구간을 나눔.
   - 실제 가격 구간은 운영에서 알 수 없으므로 보정 기준으로 쓰지 않고 진단용으로만 사용.

2. 기준가 생성 방식 고도화
   - 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체 기준가 비교.
   - 최소 표본 수, fallback 순서, IQR 이상치 완화, 표본 수 기반 shrinkage, 최근 거래 가중치를 비교.
   - 기준가는 train/validation 안에서만 만들고 test 정보는 사용하지 않음.

3. Huber 계수 조정 고도화
   - Huber가 선형 계수를 직접 학습한다는 점을 활용.
   - `current_70_30`, `svc_fallback`, `shrunk_svc_prior`, `ppv8_defensive`, `shrunk_huber_refit`, gap 피처, `log_area`, `svc_group_n_log`, `svc_prior_iqr`를 기본 후보로 둠.
   - 피처를 과하게 늘리지 않고, 계수 해석이 가능한 저차원 후보부터 비교.
   - 작가 생년, 작가 활동량, 갤러리 tier, 전시 횟수, 검색 피처는 기존에 정리된 파일이 있을 때만 잔차 보조 피처로 사용.

4. 보정 방식 세분화
   - residual_log = actual_log - pred_log로 정의.
   - 보정값은 OOF 예측 기반 residual로만 학습.
   - Huber residual, Ridge/ElasticNet residual, Quantile residual, 작은 CatBoost residual을 비교.
   - Huber residual 보정은 cap과 strength를 둠.
   - 기본 cap 후보: `0.02`, `0.03`, `0.05`.
   - 공격형 cap 후보: `0.08`, `0.12`. 공격형 후보는 운영 기본 후보와 분리.
   - 기본 strength 후보: `0.25`, `0.50`, `0.75`.

5. 결합과 라우팅
   - 전체 결합 가중치만 바꾸는 실험보다, 원인 구간별로 어떤 후보가 맞는지 먼저 확인.
   - 안정 구간은 현재 최고 후보 유지.
   - 위험 구간은 기준가-Huber, 잔차-Huber, p95 방어 후보, 보수형 fallback 중 어떤 방식이 나은지 비교.
   - routing 기준은 운영에서 예측 시점에 알 수 있는 피처만 사용.

6. 검증과 산출물
   - 빠른 탐색은 validation OOF로 시작.
   - 가능성 있는 후보만 row OOF와 artist OOF 반복 검증.
   - 최종 후보는 paired bootstrap 95% CI와 0604 stress test까지 확인.
   - 각 실험은 `experiments/track6/` 아래 독립 폴더로 관리.
- 마지막 HCOEF 실험 번호를 확인한 뒤 다음 번호로 이어서 작성. 현재 `PP-HCOEF17`까지 완료되어 있으면 `PP-HCOEF18`부터 시작.

## /goal 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 현재 최고 후보를 넘는 새 후보를 찾는 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수 개선이 아니라, 반복 검증과 운영 안정성까지 통과하는 최고 성능 후보를 찾는 것이다.

먼저 아래 문서를 읽고 현재 후보와 기존 실험 결론을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/pp_hcoef11_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef12_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef13_warm_huber_price_basis_coefficient_refinement_summary.md
- experiments/track6/PP-HCOEF11_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF12_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF13_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF14_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

현재 1차 비교 기준은 `hcoef2_size_reliability_cap005_s050`다.

- fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
- 0604 신규 라벨 일부 확인: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
- row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률 모두 1.0

서비스 v0.1 기준 후보 `current_70_30`도 함께 비교해줘.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 신규 라벨 일부 확인: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

새 운영 후보는 아래 기준을 통과해야 한다.

1. `hcoef2_size_reliability_cap005_s050` 대비 fixed test MdAPE/MAPE/p95_APE가 모두 동등 또는 개선.
2. fixed test p95_APE가 0.8064보다 악화되지 않음.
3. row OOF와 artist OOF에서 MdAPE/MAPE/p95 평균이 모두 개선.
4. row OOF와 artist OOF의 all3_improve_prob가 각각 0.90 이상.
5. 가능하면 all3_improve_prob가 0.95 이상일 때 강한 후보로 판단.
6. 0604 신규 라벨 일부 확인은 stress test로만 사용하고, 0604만 보고 후보를 고르지 않음.

목적별 후보는 분리해줘.

- 운영 기본 후보: MdAPE/MAPE/p95가 모두 안정적인 후보.
- MdAPE 특화 후보: 대표 오차는 낮지만 MAPE/p95 위험이 있는 후보.
- MAPE 특화 후보: 평균 비율 오차는 낮지만 MdAPE/p95 위험이 있는 후보.
- p95 방어 후보: 큰 오차를 줄이는 후보.
- 연구 후보: 성능 잠재력은 있지만 반복 검증이나 운영 안정성이 부족한 후보.

우선 실험 방향은 아래 순서로 잡아줘.

1. 현재 최고 후보의 작품별 residual 원인 진단
   - 기준가 표본 수, 기준가 분산, 예측 가격대, 작품 크기, 재료/지지체 bucket, 작가 이력량, 후보 간 예측 gap으로 큰 오차 원인을 나눠줘.
   - 실제 가격 구간은 보정 기준으로 쓰지 말고 진단용으로만 사용해줘.

2. 기준가 생성 방식 고도화
   - 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체 기준가를 비교해줘.
   - 최소 표본 수, fallback 순서, IQR 이상치 완화, 표본 수 기반 shrinkage, 최근 거래 가중치를 비교해줘.
   - 기준가는 train/validation 안에서만 만들고 test 정보는 쓰지 마.

3. Huber 계수 조정 고도화
   - Huber가 선형 계수를 학습한다는 특성을 활용해 저차원 피처 조합을 비교해줘.
   - 기본 피처 후보는 current_70_30, svc_fallback, shrunk_svc_prior, ppv8_defensive, shrunk_huber_refit, current_shrunk_huber_gap, current_ppv8_gap, raw_shrunk_prior_gap, log_area, svc_group_n_log, svc_prior_iqr로 둬.
   - 기존에 정리된 작가 메타 피처가 있으면 생년, 활동량, 갤러리 tier, 전시 횟수, 검색 피처를 잔차 보조 피처로만 넣어봐.

4. 보정 방식 세분화
   - residual_log = actual_log - pred_log로 정의해줘.
   - OOF 예측 기반 residual로만 보정 모델을 학습해줘.
   - Huber residual, Ridge/ElasticNet residual, Quantile residual, 작은 CatBoost residual을 비교해줘.
   - Huber residual 보정에는 cap과 strength를 둬.
   - cap 후보는 0.02, 0.03, 0.05를 기본으로 하고 0.08, 0.12는 공격형 후보로 분리해줘.
   - strength 후보는 0.25, 0.50, 0.75로 둬.

5. 결합과 라우팅
   - 전체 가중치만 바꾸지 말고, 원인 구간별로 어떤 후보가 맞는지 확인해줘.
   - 안정 구간은 현재 최고 후보 유지, 위험 구간은 기준가-Huber, 잔차-Huber, p95 방어 후보, 보수형 fallback 중 어떤 방식이 나은지 비교해줘.
   - routing 기준은 운영 예측 시점에 알 수 있는 피처만 사용해줘.

실험 관리 규칙은 아래처럼 지켜줘.

- `experiments/track6/` 아래에 실험별 독립 폴더를 만들어줘.
- 마지막 HCOEF 실험 번호를 확인한 뒤 다음 번호로 이어서 실행해줘. 현재 PP-HCOEF17까지 완료되어 있으면 PP-HCOEF18부터 시작해줘.
- 각 실험에는 최소한 아래 파일을 남겨줘.
  - artifacts/experiment_config.json
  - outputs/metrics.csv
  - outputs/candidate_predictions.csv
  - outputs/feature_coefficients.csv
  - outputs/residual_analysis.csv
  - outputs/repeated_validation_summary.csv 또는 outputs/bootstrap_or_repeated_split_summary.csv
  - reports/result_report.md
  - reports/result_report.html

실험 후에는 아래 문서를 업데이트해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- experiments/track6/PP-HCOEF14_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- 필요하면 docs/track6/experiments/warm_huber_best_performance_goal_prompt.md

최종 응답에는 아래 내용을 요약해줘.

- 실행한 실험 ID와 폴더
- 새 후보명과 후보 유형
- current_70_30 대비 개선폭
- hcoef2_size_reliability_cap005_s050 대비 개선폭
- row OOF와 artist OOF 반복 검증 결과
- fixed test와 0604 stress test 결과
- Huber 계수 또는 보정값이 의미하는 해석
- 운영 후보 / 목적별 후보 / 보류 후보 판단
- 다음 실험 또는 운영 반영 전 필요한 검증
```
