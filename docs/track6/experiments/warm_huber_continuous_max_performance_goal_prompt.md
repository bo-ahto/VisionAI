# Warm Huber 최고 성능 지속 실험 /goal 프롬프트

이 문서는 Codex의 `/goal` 기능으로 Warm Huber 계열 실험을 계속 이어가기 위한 실행용 프롬프트다.

- 사용 방식: `/goal` 명령어 뒤에 아래의 “붙여넣기용 프롬프트” 전체를 붙여 넣는다.
- 문서 경로만 넣는 방식보다, 목표와 기준을 함께 넣는 방식이 더 안정적이다.
- 목적: 현재 최고 Warm 후보를 넘기 위한 실험을 계속하되, fixed test 한 번의 성능이 아니라 반복 검증과 운영 안정성까지 통과하는 후보를 찾는다.

## 1. 기준 설정

| 기준 | 후보 | 의미 | fixed test | 0604 stress test | 판단 |
| --- | --- | --- | ---: | ---: | --- |
| 최소 기준 | `current_70_30` | 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% | MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`, RMSE_log `0.3996` | MdAPE `0.2779`, MAPE `0.3774`, p95 `0.9871` | 서비스 v0.1 기준 후보 |
| 1차 기준 | `hcoef2_size_reliability_cap005_s050` | `current_70_30` 위에 Huber 잔차 보정을 작게 더한 현재 Warm 개선 후보 | MdAPE `0.1388`, MAPE `0.2730`, p95 `0.8064`, RMSE_log `0.3988` | MdAPE `0.2731`, MAPE `0.3744`, p95 `0.9835` | 현재 넘겨야 할 기준 |

- `hcoef2_size_reliability_cap005_s050`는 row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률이 모두 `1.0`으로 확인된 후보다.
- 새 후보는 최소한 `current_70_30`보다 좋아야 한다.
- 운영 기본 후보가 되려면 가능하면 `hcoef2_size_reliability_cap005_s050`를 넘어야 한다.
- 0604 데이터는 최신 라벨 stress test이며, 후보 선택용 학습 데이터가 아니다.

## 2. 후보 판단 기준

| 후보 유형 | 기준 | 처리 |
| --- | --- | --- |
| 운영 기본 후보 | `hcoef2_size_reliability_cap005_s050` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선 | 운영 반영 검토 |
| 강한 개선 후보 | row OOF와 artist OOF의 `all3_improve_prob >= 0.95`, fixed test와 0604에서 악화 없음 | 운영 기본 후보 우선 검토 |
| 개선 후보 | row OOF와 artist OOF의 `all3_improve_prob >= 0.90`, fixed test p95 악화 없음 | 추가 반복 검증 |
| MAPE 특화 후보 | MAPE는 낮아지지만 MdAPE 또는 p95가 약함 | 운영 기본 후보와 분리 |
| p95 방어 후보 | 큰 오차는 줄지만 MdAPE/MAPE 개선폭이 작음 | 신뢰도/범위 정책 후보 |
| 연구 후보 | fixed test 또는 0604는 좋지만 반복 검증이 약함 | 문서화하고 기본 후보 미채택 |

## 3. 고정 금지 기준

- test residual 또는 0604 residual을 보고 보정값, 가중치, 구간 경계를 새로 만들지 않는다.
- fixed test만 좋아지고 반복 OOF가 약하면 운영 기본 후보로 채택하지 않는다.
- MdAPE가 좋아져도 fixed test p95_APE가 `0.8064`보다 악화되면 운영 기본 후보에서 제외한다.
- 0604 p95_APE가 `0.9835`보다 악화되면 운영 후보 승격을 보류한다.
- 실제 가격 구간은 운영 예측 시점에 알 수 없으므로 보정 기준으로 쓰지 않고 원인 진단용으로만 쓴다.
- 복잡도가 크게 증가했는데 개선폭이 작거나 계수/정책 해석이 불가능하면 연구 후보로만 남긴다.

## 4. 우선 실험 축

1. 기준가 생성 고도화
   - 작가 전체 기준가, 작가+크기 기준가, 작가+재료/지지체 기준가, 작가+크기+재료/지지체 기준가 비교.
   - 최소 표본 수, fallback 순서, IQR 완화, 표본 수 기반 shrinkage, 최근 거래 가중치 비교.
   - 기준가는 train/validation 안에서만 만들고 test 정보는 사용하지 않음.

2. Huber 계수 조정
   - Huber가 선형 계수를 학습한다는 특성을 활용.
   - 기준가, 크기, 신뢰도, 후보 간 gap, 작가 메타 보조 피처의 계수 방향과 크기를 확인.
   - 기본 피처 후보: `current_70_30`, `svc_fallback`, `shrunk_svc_prior`, `ppv8_defensive`, `shrunk_huber_refit`, `current_shrunk_huber_gap`, `current_ppv8_gap`, `raw_shrunk_prior_gap`, `log_area`, `svc_group_n_log`, `svc_prior_iqr`.
   - 작가 생년, 활동량, 갤러리 tier, 전시 횟수, 검색 피처는 운영 예측 시점에 알 수 있고 기존 정리 파일이 있을 때만 잔차 보조 피처로 사용.

3. 잔차 보정 방식
   - `residual_log = actual_log - pred_log`로 정의.
   - 보정 모델은 반드시 OOF 예측 residual로 학습.
   - Huber residual, Ridge/ElasticNet residual, Quantile residual, 작은 CatBoost residual 비교.
   - cap 후보: `0.02`, `0.03`, `0.05`.
   - 공격형 cap 후보: `0.08`, `0.12`.
   - strength 후보: `0.25`, `0.50`, `0.75`.

4. 원인 구간별 라우팅
   - 전체 가중치만 바꾸지 않고 큰 오차 원인 구간별로 후보를 선택.
   - 안정 구간은 현재 최고 후보 유지.
   - 위험 구간은 기준가-Huber, 잔차-Huber, p95 방어 후보, 보수형 fallback을 비교.
   - 라우팅 기준은 예측 시점에 알 수 있는 피처만 사용.

5. risk/quantile guard 결합
   - 별도 risk 또는 quantile 모델은 점 예측을 크게 움직이기보다 큰 오차 가능성, 가격 범위, 신뢰도 조정에 우선 사용.
   - 점 예측 후보와 신뢰도/범위 후보를 분리.
   - PP-V8이 0604에서 맞춘 샘플을 직접 따라가지 않고, validation에서 예측 가능한 risk 피처로만 분기.

6. 서비스 피처 파이프라인 검증
   - 연구 산출물과 실제 서비스 피처 생성 결과가 같은지 확인.
   - artist_key 매핑, 유사 작품 기반 가격 피처, coverage tier, 표본 수, 가격 단위, 환율, 누락값 처리 차이를 감사.
   - 연구 후보가 운영 입력으로 재현될 때 성능이 유지되는지 확인.

## 5. 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 현재 최고 후보를 넘기 위한 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수를 좋게 만드는 것이 아니라, 반복 검증과 운영 안정성까지 통과하는 최고 성능 후보를 찾는 것이다.

먼저 아래 문서를 읽고 현재 후보, 이미 실패한 실험 유형, 남은 검증 방향을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- docs/track6/experiments/warm_huber_max_performance_continuation_goal_prompt.md
- docs/track6/experiments/warm_huber_hcoef22_continuation_goal_prompt.md
- experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
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

최소 비교 기준은 `current_70_30`이다.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 최신 라벨 stress test: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

실험 기준은 아래처럼 고정해줘.

1. 새 후보는 최소한 `current_70_30`보다 좋아야 한다.
2. 운영 기본 후보가 되려면 `hcoef2_size_reliability_cap005_s050` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 한다.
3. row OOF와 artist OOF의 `all3_improve_prob >= 0.90`이면 개선 후보로 본다.
4. row OOF와 artist OOF의 `all3_improve_prob >= 0.95`이고 fixed test와 0604에서 악화가 없으면 강한 후보로 본다.
5. fixed test p95_APE가 0.8064보다 악화되면 운영 기본 후보로 채택하지 않는다.
6. 0604 p95_APE가 0.9835보다 악화되면 운영 후보 승격을 보류한다.
7. 0604 또는 test residual을 보고 새 보정값, 경계값, 가중치를 만들지 않는다.
8. 실제 가격 구간은 원인 진단용으로만 쓰고 보정 기준으로 쓰지 않는다.

후보 유형은 반드시 분리해줘.

- 운영 기본 후보: MdAPE/MAPE/p95가 모두 안정적인 후보.
- MAPE 특화 후보: MAPE는 개선되지만 MdAPE 또는 p95 위험이 남는 후보.
- p95 방어 후보: 큰 오차를 줄이지만 중앙 오차 개선폭은 작은 후보.
- 연구 후보: fixed test 또는 0604는 좋지만 반복 OOF가 약한 후보.

다음 실험은 마지막 완료된 HCOEF 번호를 확인한 뒤 다음 번호로 이어서 관리해줘. 현재 PP-HCOEF21까지 완료되어 있으면 PP-HCOEF22부터 시작해줘.

우선 실험 방향은 아래 순서로 잡아줘.

1. 현재 최고 후보의 작품별 큰 오차 원인 분석
   - 기준가 표본 수, 기준가 IQR, fallback level, 예측 가격대, 작품 크기, 재료/지지체 bucket, 작가 이력량, 후보 간 예측 gap으로 residual을 나눠줘.
   - 실제 가격 구간은 진단용으로만 쓰고 보정 기준으로 쓰지 마.

2. 기준가 생성 방식 고도화
   - 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체 기준가를 비교해줘.
   - 최소 표본 수, fallback 순서, IQR 완화, 표본 수 기반 shrinkage, 최근 거래 가중치를 비교해줘.
   - 기준가는 train/validation 안에서만 만들고 test 정보는 쓰지 마.

3. Huber 계수 조정 고도화
   - Huber가 선형 계수를 학습한다는 특성을 활용해 기준가, 크기, 신뢰도, gap 피처의 계수를 직접 조정해줘.
   - 기본 후보 피처는 current_70_30, svc_fallback, shrunk_svc_prior, ppv8_defensive, shrunk_huber_refit, current_shrunk_huber_gap, current_ppv8_gap, raw_shrunk_prior_gap, log_area, svc_group_n_log, svc_prior_iqr로 둬.
   - 작가 생년, 활동량, 갤러리 tier, 전시 횟수, 검색 피처는 운영 시점에 알 수 있는 값이고 기존 정리 파일이 있을 때만 잔차 보조 피처로 넣어줘.

4. 잔차 보정 모델 비교
   - residual_log = actual_log - pred_log로 정의해줘.
   - OOF 예측 기반 residual로만 보정 모델을 학습해줘.
   - Huber residual, Ridge/ElasticNet residual, Quantile residual, 작은 CatBoost residual을 비교해줘.
   - Huber residual 보정에는 cap과 strength를 둬.
   - cap 후보는 0.02, 0.03, 0.05를 기본으로 하고, 0.08과 0.12는 공격형 후보로 따로 분리해줘.
   - strength 후보는 0.25, 0.50, 0.75로 둬.

5. 원인 구간별 라우팅
   - 전체 가중치만 바꾸지 말고, 원인 구간별로 어떤 후보가 맞는지 확인해줘.
   - 안정 구간은 현재 최고 후보 유지, 위험 구간은 기준가-Huber, 잔차-Huber, p95 방어 후보, 보수형 fallback 중 비교해줘.
   - 라우팅 기준은 운영 예측 시점에 알 수 있는 피처만 사용해줘.

6. risk/quantile guard 결합
   - HCOEF 안정 후보를 점 예측 기본값으로 유지해줘.
   - quantile 또는 risk 모델은 큰 오차 가능성, 가격 범위, 신뢰도 조정에 우선 사용해줘.
   - 점 예측을 움직이는 후보와 가격 범위/신뢰도만 조정하는 후보를 분리해줘.
   - PP-V8이 0604에서 잘 맞춘 샘플을 직접 따라가지 말고, validation에서 예측 가능한 위험도 피처로만 분기해줘.
   - PP-HCOEF18의 quantile width risk guard는 fixed MdAPE 개선 신호는 있었지만 MAPE/반복 검증 기준을 통과하지 못했으므로 같은 방식의 점 예측 이동은 반복하지 마.

7. 서비스 feature pipeline 통합 검증
   - 연구 산출물과 실제 서비스 피처 생성 결과가 같은지 확인해줘.
   - artist_key 매핑, 유사 작품 기반 가격 피처, coverage tier, 표본 수, 가격 단위, 환율, 누락값 처리 차이를 감사해줘.
   - 연구 후보가 운영 입력으로 재현될 때 성능이 유지되는지 확인해줘.
   - PP-HCOEF19에서 서비스 feature pipeline 재현성 감사는 완료됐고 component/formula/schema가 통과했으므로 같은 감사만 반복하지 마.
   - PP-HCOEF20의 운영 component 기반 저차원 Huber/Ridge residual grid와 PP-HCOEF21의 가변 SVC:PP-V8 기준가/adaptive reliability residual grid가 이미 완료되어 있으면 같은 피처와 같은 cap/strength 조합으로 반복하지 마.
   - 다음은 목적별 후보 분리, quantile width 기반 가격 범위/신뢰도 표시, 또는 아직 쓰지 않은 새 원인 피처가 있을 때만 저차원 Huber 계수 재탐색을 우선 검토해줘.

실험 관리 규칙은 아래처럼 지켜줘.

- `experiments/track6/` 아래에 실험별 독립 폴더를 만들어줘.
- 새 실험은 `PP-HCOEF##_짧은_설명` 형식으로 관리해줘.
- 실행 스크립트는 `scripts/track6/run_pp_hcoef##_짧은_설명.py`로 남겨줘.
- 각 실험에는 최소한 아래 파일을 남겨줘.
  - artifacts/experiment_config.json
  - outputs/metrics.csv
  - outputs/candidate_predictions.csv
  - outputs/feature_coefficients.csv 또는 outputs/policy_map.csv
  - outputs/residual_analysis.csv
  - outputs/repeated_validation_summary.csv 또는 outputs/bootstrap_or_repeated_split_summary.csv
  - reports/result_report.md
  - reports/result_report.html

실험 후에는 아래 문서를 업데이트해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_best_performance_goal_prompt.md
- docs/track6/experiments/warm_huber_max_performance_continuation_goal_prompt.md
- 필요하면 최신 continuation goal prompt 문서

최종 응답에는 아래 내용을 요약해줘.

- 실행한 실험 ID와 폴더
- 새 후보명과 후보 유형
- current_70_30 대비 개선폭
- hcoef2_size_reliability_cap005_s050 대비 개선폭
- row OOF와 artist OOF 반복 검증 결과
- fixed test와 0604 stress test 결과
- Huber 계수 또는 보정 정책 해석
- 운영 후보 / 목적별 후보 / 보류 후보 판단
- 다음 실험에서 반복하지 말아야 할 점
```
