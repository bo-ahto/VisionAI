# Warm Huber 최고 성능 탐색용 Codex /goal Prompt

아래 프롬프트는 Codex의 `/goal` 명령어 뒤에 그대로 붙여 넣어 사용할 수 있다.

바로 실행하기 쉬운 축약/고도화 버전은 `docs/track6/experiments/warm_huber_highest_performance_goal_prompt.md`에 별도로 정리했다. 새 실험을 이어갈 때는 해당 문서를 우선 사용하고, 이 문서는 기존 실험 맥락과 상세 후보 설명을 확인하는 용도로 사용한다.

핵심 기준은 `test` 한 번의 점수 개선이 아니라, 반복 검증에서 안정적으로 개선되는 후보를 찾는 것이다. 현재까지는 `hcoef2_size_reliability_cap005_s050`가 Warm 개선 후보이므로, 새 실험은 이 후보를 넘는지를 1차 기준으로 본다.

단, “최고 성능”은 하나의 숫자로만 판단하지 않는다. 운영 기본 후보, MAPE 개선 후보, p95 방어 후보, 추가 검증 후보를 분리해 관리한다.

## 기준 후보

- 서비스 v0.1 기준 후보: `current_70_30`
  - 의미: 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합.
  - fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996`.
  - 0604 신규 데이터 일부 라벨 확인: MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871`.

- 현재 Warm 개선 후보: `hcoef2_size_reliability_cap005_s050`
  - 의미: `current_70_30` 위에 작은 Huber 잔차 보정을 추가한 후보.
  - 보정 제한: cap `0.05`, strength `0.50`.
  - fixed test: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988`.
  - 0604 신규 데이터 일부 라벨 확인: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
  - 반복 검증: HCOEF11 확장 검증 기준 row OOF `80`회와 artist OOF `80`회 모두 MdAPE/MAPE/p95 개선 확률 `1.0`.
  - paired bootstrap: MAPE/RMSE 개선은 강하고, MdAPE/p95는 split별 신뢰구간이 넓어 최신 라벨 stress test를 추가 확인 기준으로 둔다.

- 기준가 생성 고도화 보류 후보: `loose_huber_basis_core_alpha0.1`
  - 의미: 작가+크기+재료/지지체 등 세밀한 기준가를 만들고 Huber가 직접 계수로 재학습한 후보.
  - fixed test: MdAPE `0.1346`, MAPE `0.2618`, p95_APE `0.8916`.
  - 0604 신규 데이터 일부 라벨 확인: MdAPE `0.2304`, MAPE `0.3447`, p95_APE `0.9514`.
  - 판단: MdAPE/MAPE 개선 잠재력은 크지만 fixed test p95_APE가 악화되어 운영 기본 후보는 아님.

- 기준가-HCOEF 제한 결합 보류 후보: `loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.75`
  - 의미: HCOEF3 안정 후보 위에 기준가-Huber 후보와의 차이를 cap/strength로 제한해 일부만 반영한 후보.
  - fixed test: MdAPE `0.1384`, MAPE `0.2681`, p95_APE `0.8124`.
  - 0604 신규 데이터 일부 라벨 확인: MdAPE 약 `0.2621`, MAPE 약 `0.3618`, p95_APE 약 `0.9573`.
  - 판단: fixed test와 0604는 좋지만 반복 OOF 안정성이 부족해 기본 후보는 아님.

- 조건부 기준가 routing 보류 후보: `loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075`
  - 의미: HCOEF3 안정 후보를 기본으로 두고, 신뢰도 높은 일부 샘플에만 basis-Huber 차이를 제한 반영한 후보.
  - fixed test: MdAPE `0.1384`, MAPE `0.2728`, p95_APE `0.8064`.
  - 판단: p95는 방어했지만 개선폭이 작고 반복 OOF all3 gate가 `0.0`이라 기본 후보는 아님.

- 면적단가 직접 잔차 피처 보류 후보: `hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.50`
  - 의미: HCOEF3 잔차 피처에 면적단가 기준가, shrink 기준가 gap, 기준가 신뢰도 피처를 직접 추가한 후보.
  - fixed test: MdAPE `0.1361`, MAPE `0.2718`, p95_APE `0.8298`.
  - 판단: MdAPE/MAPE는 개선됐지만 p95가 HCOEF3 기준 `0.8064`보다 악화되어 기본 후보는 아님.

- segmented Huber 보류 후보: `hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority`
  - 의미: HCOEF7 raw residual을 기준가 위험도 low/mid/high 구간별 cap/strength로 제한한 후보.
  - fixed test: MdAPE `0.1395`, MAPE `0.2744`, p95_APE `0.8340`.
  - 판단: HCOEF3보다 MdAPE/MAPE/p95가 모두 악화되어 탈락.

- 위험도 기반 기준가 결합 보류 후보: `hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only`
  - 의미: HCOEF3 안정 후보와 HCOEF4 loose basis-Huber 예측 차이가 작은 구간에만 basis-Huber 방향으로 제한 이동한 후보.
  - fixed test: MdAPE `0.1356`, MAPE `0.2670`, p95_APE `0.8308`.
  - 반복 검증: row OOF all3 `0.50`, artist OOF all3 `0.35`.
  - 판단: MdAPE/MAPE는 개선됐지만 p95가 HCOEF3 기준 `0.8064`보다 악화되고 반복 안정성도 부족해 기본 후보는 아님.

- 원인 구간 기반 약한 보정 보류 후보: `hcoef10_pred_reliability_cap0.02_s0.25`
  - 의미: 예측 가격대와 기준가 표본 수 조합별 residual 중앙값을 validation에서 학습하고 아주 작게 보정한 후보.
  - fixed test: MdAPE `0.1383`, MAPE `0.2729`, p95_APE `0.8062`.
  - 반복 검증: row OOF all3 `0.00`, artist OOF all3 `0.10`.
  - 판단: fixed test는 3지표 소폭 개선이지만 반복 OOF 안정성이 부족해 기본 후보는 아님.

- HCOEF3 안정 후보 확장 검증: `PP-HCOEF11`
  - 의미: 새 보정을 추가하지 않고 `hcoef2_size_reliability_cap005_s050`를 row/artist OOF 80회와 paired bootstrap 2000회로 재검증.
  - fixed test: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`.
  - 0604 신규 데이터 일부 라벨 확인: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
  - 반복 검증: row/artist OOF all3 `1.0 / 1.0`.
  - 판단: 현재 Warm 개선 후보 유지 근거가 강화됨. 다음은 운영 패키징, 최신 라벨 stress test, 작품별 큰 오차 진단이 우선.

- HCOEF3 안정 후보 운영 패키징 감사: `PP-HCOEF12`
  - 의미: `hcoef2_size_reliability_cap005_s050`를 joblib 패키지로 저장하고, 재로딩 예측이 direct rebuild와 같은지 확인.
  - fixed test 재현: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`.
  - 0604 재현: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
  - readiness check: 전체 `pass`.
  - 판단: 연구 산출물 기준 재현성은 충족. 다음은 production artifact 반영 전 최신 라벨 stress test와 서비스 feature pipeline 통합 검증이 우선.

- HCOEF3 안정 후보 잔차 위험 원인 진단: `PP-HCOEF13`
  - 의미: 새 보정을 고르지 않고 현재 후보가 남긴 큰 오차를 기준가 표본 수, IQR, basis level, 예측 가격대, 크기, 재료/지지체, 후보 간 gap별로 정량화.
  - fixed test 재현: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`.
  - 0604 재현: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
  - validation 위험 구간: `n_10_19`, `iqr_mid/high`, `ppv8_pos`, `basis_current_disagreement`, `artist_overall`.
  - 판단: 새 후보 채택 없음. 이 위험 구간은 HCOEF14에서 실제 shrinkage/routing 후보로 검증 완료.

- HCOEF3 안정 후보 위험 구간 shrinkage/routing 검증: `PP-HCOEF14`
  - 의미: HCOEF13 위험 구간에 한정해 Huber 잔차 보정폭 축소, `current_70_30` 기준 routing, segment residual 중앙값 보정을 실제 후보로 검증.
  - fixed test 상위 후보: `hcoef14_shrink_iqr_mid_high_keep050` MdAPE `0.1384`, MAPE `0.2731`, p95_APE `0.8047`.
  - 0604 확인: MdAPE `0.2734`, MAPE `0.3748`, p95_APE `0.9833`.
  - 반복 검증: row/artist OOF all3 gate 통과 후보 `0`개.
  - 판단: fixed test p95 소폭 개선은 있었지만 반복 안정성이 부족해 새 후보 채택 없음. 다음은 같은 위험 구간 보정보다 최신 라벨 stress test, 서비스 feature pipeline 통합 검증, 또는 별도 risk/quantile 모델 결합이 우선.

- HCOEF3 안정 후보 최신 라벨 stress test: `PP-HCOEF15`
  - 의미: 0604 최신 라벨 829건을 외부 stress test로 사용해 HCOEF 안정 후보, 기존 70:30 기준, 운영 v0.1 component를 같은 기준으로 비교.
  - HCOEF 안정 후보 0604: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
  - 기존 70:30 기준 0604: MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871`.
  - 운영 PP-V8/service primary 0604: MdAPE `0.2298`, MAPE `0.3359`, p95_APE `0.9273`.
  - 판단: HCOEF 안정 후보는 기존 70:30 대비 개선을 유지. 운영 PP-V8/service primary는 0604에서 강하지만 OOF/fixed test 후보가 아니므로 바로 채택하지 않았고, HCOEF16에서 저차원 Huber 계수 입력으로 재검증 완료.

- PP-V8 운영 component OOF 재검증: `PP-HCOEF16`
  - 의미: 0604에서 강했던 PP-V8/service component를 validation OOF와 artist OOF 기준으로 다시 검증.
  - PP-V8 proxy fixed test: MdAPE `0.1632`, MAPE `0.2816`, p95_APE `0.9311`.
  - PP-V8 proxy 0604: MdAPE `0.2298`, MAPE `0.3359`, p95_APE `0.9273`.
  - PP-V8 gap Huber 상위 후보 fixed test: MdAPE `0.1394`, MAPE `0.2728`, p95_APE `0.8091`.
  - 판단: 0604에서는 강하지만 fixed test와 artist OOF gate를 통과하지 못해 새 후보 채택 없음.

- PP-V8 제한 이동 정책 검증: `PP-HCOEF17`
  - 의미: PP-V8을 전체 반영하지 않고, PP-V8과 HCOEF 안정 후보의 예측 차이가 작거나 비교군 신뢰도가 높은 구간에서만 제한 이동.
  - fixed test 상위 후보: MdAPE `0.1374`, MAPE `0.2735`, p95_APE `0.8064`.
  - coverage 제한 후보 fixed test: MdAPE `0.1384`, MAPE `0.2729`, p95_APE `0.8064`.
  - coverage 제한 후보 0604: MdAPE `0.2731`, MAPE `0.3739`, p95_APE `0.9790`.
  - 판단: fixed test 또는 0604 소폭 개선 신호는 있으나 validation/bootstrap gate를 통과한 후보가 없어 새 후보 채택 없음.

## 새 후보 판단 기준

- 1순위 기준: 반복 OOF 안정성.
  - row split 반복 OOF에서 MdAPE/MAPE/p95 평균 개선.
  - artist-level split 반복 OOF에서 MdAPE/MAPE/p95 평균 개선.
  - `all3_improve_prob >= 0.90`이면 개선 후보.
  - `all3_improve_prob >= 0.95`이고 fixed test/0604도 악화가 없으면 강한 후보.

- 2순위 기준: fixed validation/test 확인.
  - `hcoef2_size_reliability_cap005_s050` 대비 MdAPE 개선.
  - MAPE 악화 없음.
  - p95_APE 악화 없음.
  - RMSE_log 악화가 크지 않음.

- 3순위 기준: 운영 안정성.
  - 보정폭이 너무 크지 않아야 함.
  - 기본 cap은 `0.05` 이하.
  - cap `0.08` 이상은 공격형 후보로 분리하고, 반복 검증에서 확실히 좋을 때만 검토.
  - 특정 작가, 특정 크기, 특정 재료 구간에서만 좋아지는 후보는 보류.

- 운영 기본 후보 기준:
  - `hcoef2_size_reliability_cap005_s050` 대비 반복 OOF와 fixed test에서 MdAPE/MAPE/p95가 모두 개선 또는 동등해야 함.
  - fixed test p95_APE는 `0.8064`보다 나빠지면 기본 후보로 채택하지 않음.
  - 0604는 최종 채택 기준이 아니라 외부 스트레스 테스트로만 사용함.

- 목적별 후보 기준:
  - MAPE 개선 후보: MAPE가 의미 있게 좋아지되 p95_APE 악화폭을 별도 표시.
  - MdAPE 개선 후보: 중앙 오차가 좋아지되 MAPE/p95 위험을 별도 표시.
  - p95 방어 후보: 큰 오차를 줄이는 데 목적이 있으므로 MdAPE 개선폭이 작아도 보류하지 않음.
  - 공격형 후보: fixed test만 좋거나 p95가 악화되는 후보는 운영 기본 후보와 분리.

- 채택 보류 기준:
  - fixed test만 좋아지고 validation 또는 반복 OOF가 나쁜 경우.
  - MdAPE는 좋아졌지만 p95_APE가 악화되는 경우.
  - MAPE만 좋아지고 MdAPE가 악화되는 경우.
  - 0604 신규 데이터에서 방향이 크게 반대로 나오는 경우.
  - 실험 복잡도가 커졌는데 개선폭이 작고 설명력이 떨어지는 경우.

## /goal 붙여넣기용 프롬프트

```text
Track6 가격 예측 프로젝트에서 Warm Huber 계열 모델의 최고 성능 후보를 계속 탐색해줘.

목표는 단순히 fixed test 점수를 한 번 좋게 만드는 것이 아니라, 반복 검증에서도 안정적으로 좋아지는 Warm 후보를 찾는 것이다. 현재 기준 후보와 개선 후보를 모두 기준으로 삼아야 한다.

반드시 먼저 아래 문서를 읽고 지금까지의 실험 흐름과 기준 후보를 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef1_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef2_warm_huber_conservative_residual_selection_summary.md
- docs/track6/experiments/pp_hcoef3_warm_huber_residual_repeated_validation_summary.md
- docs/track6/experiments/pp_hcoef4_warm_basis_generation_refinement_summary.md
- docs/track6/experiments/pp_hcoef5_warm_basis_hcoef_blend_repeated_validation_summary.md
- docs/track6/experiments/pp_hcoef6_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef7_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef8_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef9_warm_huber_risk_gated_basis_blend_summary.md
- docs/track6/experiments/pp_hcoef10_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef11_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef12_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef13_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef14_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- experiments/track6/PP-HCOEF3_warm_huber_residual_repeated_validation/reports/result_report.md
- experiments/track6/PP-HCOEF4_warm_basis_generation_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF5_warm_basis_hcoef_blend_repeated_validation/reports/result_report.md
- experiments/track6/PP-HCOEF6_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF7_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF8_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF9_warm_huber_risk_gated_basis_blend/reports/result_report.md
- experiments/track6/PP-HCOEF10_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF11_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF12_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF13_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF14_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

현재 비교 기준은 기준 후보 2개, 보류 후보 8개, 확장 검증 1개, 패키징 감사 1개로 둔다.

1. 서비스 v0.1 기준 후보 `current_70_30`
   - 의미: 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합
   - fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
   - 0604 신규 데이터 일부 라벨 확인: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

2. 현재 Warm 개선 후보 `hcoef2_size_reliability_cap005_s050`
   - 의미: current_70_30 위에 작은 Huber 잔차 보정을 추가한 후보
   - 보정 제한: cap 0.05, strength 0.50
   - fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
   - 0604 신규 데이터 일부 라벨 확인: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
   - row OOF와 artist OOF 반복 검증 모두 MdAPE/MAPE/p95 개선 확률 1.0

참고해야 할 보류 후보도 있다.

3. 기준가 생성 고도화 후보 `loose_huber_basis_core_alpha0.1`
   - 의미: 세밀한 기준가와 기존 후보들을 Huber가 직접 재학습한 후보
   - fixed test: MdAPE 0.1346, MAPE 0.2618, p95_APE 0.8916
   - 0604 신규 데이터 일부 라벨 확인: MdAPE 0.2304, MAPE 0.3447, p95_APE 0.9514
   - 판단: MdAPE/MAPE는 좋지만 fixed test p95가 악화되어 기본 후보로는 보류

4. 기준가-HCOEF 제한 결합 후보 `loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.75`
   - 의미: HCOEF3 안정 후보 위에 basis-Huber 차이를 제한적으로 더한 후보
   - fixed test: MdAPE 0.1384, MAPE 0.2681, p95_APE 0.8124
   - 0604 신규 데이터 일부 라벨 확인: MdAPE 약 0.2621, MAPE 약 0.3618, p95_APE 약 0.9573
   - 판단: fixed test/0604는 좋지만 반복 OOF 안정성이 부족해 보류

5. 조건부 기준가 routing 후보 `loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075`
   - 의미: HCOEF3 안정 후보를 기본으로 두고, 신뢰도 높은 일부 샘플에만 basis-Huber 차이를 제한 반영한 후보
   - fixed test: MdAPE 0.1384, MAPE 0.2728, p95_APE 0.8064
   - 판단: p95는 방어했지만 개선폭이 작고 반복 OOF all3 gate가 0.0이라 보류

6. 면적단가 직접 잔차 피처 후보 `hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.50`
   - 의미: HCOEF3 잔차 피처에 면적단가 기준가, shrink 기준가 gap, 기준가 신뢰도 피처를 직접 추가한 후보
   - fixed test: MdAPE 0.1361, MAPE 0.2718, p95_APE 0.8298
   - 판단: MdAPE/MAPE는 개선됐지만 p95가 HCOEF3 기준 0.8064보다 악화되어 보류

7. segmented Huber 후보 `hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority`
   - 의미: HCOEF7 raw residual을 기준가 위험도 low/mid/high 구간별 cap/strength로 제한한 후보
   - fixed test: MdAPE 0.1395, MAPE 0.2744, p95_APE 0.8340
   - 판단: HCOEF3보다 MdAPE/MAPE/p95가 모두 악화되어 탈락

8. 위험도 기반 기준가 결합 후보 `hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only`
   - 의미: HCOEF3와 HCOEF4 예측 차이가 작은 구간에만 loose basis-Huber 방향으로 제한 이동한 후보
   - fixed test: MdAPE 0.1356, MAPE 0.2670, p95_APE 0.8308
   - 반복 검증: row OOF all3 0.50, artist OOF all3 0.35
   - 판단: MdAPE/MAPE는 개선됐지만 p95 악화와 반복 안정성 부족으로 보류

9. 원인 구간 기반 약한 보정 후보 `hcoef10_pred_reliability_cap0.02_s0.25`
   - 의미: 예측 가격대와 기준가 표본 수 조합별 residual 중앙값을 아주 작게 보정한 후보
   - fixed test: MdAPE 0.1383, MAPE 0.2729, p95_APE 0.8062
   - 반복 검증: row OOF all3 0.00, artist OOF all3 0.10
   - 판단: fixed test는 3지표 소폭 개선이나 반복 OOF 안정성이 부족해 보류

새 실험은 `hcoef2_size_reliability_cap005_s050`를 넘는지를 1차 목표로 삼고, 최소한 `current_70_30`보다 안정적으로 좋아야 한다. `loose_huber_basis_core_alpha0.1`, capped blend, 조건부 routing, 면적단가 직접 잔차 피처, segmented Huber, 위험도 기반 기준가 결합, 원인 구간 median 보정, 위험 구간 shrinkage/routing, PP-V8 운영 component OOF 후보, PP-V8 제한 이동 정책, quantile width 기반 점 예측 이동은 성능 잠재력은 있었지만 p95/반복 안정성/개선폭 문제로 기본 후보가 되지 못했다. HCOEF11에서 HCOEF3 안정 후보의 반복 검증 확대는 완료됐고, HCOEF12에서 운영 전 실험 패키징 감사도 완료됐다. HCOEF13에서 큰 오차 원인 진단, HCOEF14에서 위험 구간 한정 보정 검증, HCOEF15에서 최신 라벨 stress test, HCOEF16에서 PP-V8 운영 component OOF 재검증, HCOEF17에서 PP-V8 제한 이동 정책 검증, HCOEF18에서 quantile width risk guard 검증, HCOEF19에서 서비스 feature pipeline 재현성 감사도 완료됐다. 다음 실험은 최신 라벨 원인 분석, quantile width 기반 가격 범위/신뢰도 정책 검증, 또는 운영 component 기반 저차원 Huber 계수 재탐색을 우선한다.

실험 방향은 아래 순서로 진행해줘.

1. 기준가 생성 방식 고도화
   - 유사 작품 기반 가격 피처를 더 잘 만드는 방법을 탐색한다.
   - 작가 전체, 작가+크기, 작가+재료/지지체, 작가+작품 유형, 작가+크기+재료/지지체 조합을 비교한다.
   - 최소 표본 수, 표본 수에 따른 완화, 최근 거래 가중치, IQR 기반 이상치 완화, shrinkage prior를 비교한다.
   - 기준가는 train/validation 안에서만 만들고 test 정보는 쓰지 않는다.

2. Huber 계수 조정 방식 고도화
   - Huber가 선형 계수를 직접 학습한다는 특성을 활용한다.
   - 피처는 많이 늘리지 말고, 설명 가능한 저차원 피처부터 추가한다.
   - 기본 후보 피처:
     - current_70_30
     - svc_fallback
     - shrunk_svc_prior
     - ppv8_defensive
     - shrunk_huber_refit
     - current_shrunk_huber_gap
     - current_ppv8_gap
     - raw_shrunk_prior_gap
     - log_area
     - svc_group_n_log
     - svc_prior_iqr
   - 추가 후보 피처:
     - 작품 크기 구간
     - 재료/지지체 bucket
     - 작가별 표본 수
     - 작가 가격 분산
     - 작가 메타 정보가 이미 정리되어 있으면 생년, 갤러리 티어, 전시 횟수, 검색/인지도 피처
   - 작가 메타 피처는 새로 크롤링하지 말고 기존 artifact나 정리된 데이터가 있는 경우에만 사용한다.

3. 잔차 보정 방식 고도화
   - current_70_30 또는 hcoef2 후보가 남긴 residual_log를 다시 분석한다.
   - residual_log = actual_log - pred_log로 정의한다.
   - residual 보정 모델은 반드시 OOF 예측 기반 residual로 학습한다.
   - Huber, Ridge, ElasticNet, Quantile residual, 작은 CatBoost residual 보정을 비교하되, 최종 후보는 설명 가능성과 안정성을 우선한다.
   - Huber 잔차 보정은 cap과 strength를 반드시 둔다.
   - 기본 cap 후보: 0.02, 0.03, 0.05.
   - 공격형 cap 후보: 0.08, 0.12. 단, 별도 aggressive 후보로만 관리한다.
   - 기본 strength 후보: 0.25, 0.50, 0.75.

4. 목적별 후보 분리
   - MdAPE 우선 후보
   - MAPE 우선 후보
   - p95_APE 방어 후보
   - 0604 신규 데이터 방어 후보
   - 운영 단순성 우선 후보
   - 후보별 목적을 분리해서 기록하고, 한 후보가 모든 목적을 만족하는지 확인한다.

5. 다음에 우선 시도할 실험 아이디어
   - HCOEF3 운영 패키징 재현은 PP-HCOEF12에서 완료했으므로 같은 목적의 패키징 실험은 중복 실행하지 않는다.
   - 큰 오차 원인 진단은 PP-HCOEF13에서 완료됐고, 위험 구간 실제 보정 후보 검증은 PP-HCOEF14에서 완료됐다.
   - 위험 구간 shrinkage/routing 검증은 PP-HCOEF14에서 완료했으므로 같은 방식의 단순 보정 실험은 중복 실행하지 않는다.
   - HCOEF3 반복 검증 확대는 PP-HCOEF11에서 완료했으므로 같은 목적의 반복 실험은 중복 실행하지 않는다.
   - 원인 분석 리포트 고도화: HCOEF10의 segment median 보정은 운영 후보가 되지 못했으므로, 큰 오차가 나는 작품군을 정량적으로 설명하는 진단표를 만든다.
   - 목적별 후보 분리: 면적단가 계열은 운영 기본 후보가 아니라 MAPE/MdAPE 목적 후보 또는 리포트용 해석 피처로만 유지한다.
   - 잔차 원인 기반 보정: fixed test에서 크게 튄 작품을 크기, 재료/지지체, 기준가 coverage, 작가 표본 수, 기존 후보 간 gap으로 나눠 원인별 보정 후보를 만든다.
   - 작가 메타 보정: 이미 정리된 작가 생년, 활동량, 갤러리/전시/검색 피처가 있으면 Warm에서도 잔차 보조 피처로만 넣어본다.

6. 검증 방식
   - fixed validation/test만 보지 않는다.
   - row split 반복 OOF를 실행한다.
   - artist-level split 반복 OOF를 실행한다.
   - 가능하면 20회 반복, 각 5 folds를 기본값으로 사용한다.
   - 시간이 오래 걸리면 먼저 5회 반복으로 후보를 줄이고, 최종 후보만 20회 반복한다.
   - paired bootstrap 95% CI를 산출한다.
   - 가능하면 Wilcoxon signed-rank test도 산출한다.
   - 0604 신규 데이터 라벨이 있는 범위에서 stress test를 한다.

7. 후보 채택 기준
   - row OOF와 artist OOF에서 MdAPE/MAPE/p95 평균이 모두 개선되어야 한다.
   - row OOF와 artist OOF에서 `all3_improve_prob >= 0.90`이면 개선 후보로 본다.
   - `all3_improve_prob >= 0.95`이고 fixed validation/test/0604에서도 악화가 없으면 강한 후보로 본다.
   - fixed test만 좋은 후보는 채택하지 않는다.
   - p95_APE가 악화되는 후보는 MAPE가 좋아도 보류한다.
   - 보정폭이 큰 후보는 설명력과 운영 안정성 검토를 별도로 한다.
   - 운영 기본 후보는 fixed test p95_APE가 HCOEF3 기준 `0.8064`보다 악화되면 채택하지 않는다.
   - MAPE 또는 MdAPE 특화 후보는 기본 후보와 분리해 목적별 후보로만 기록한다.

8. 실험 관리 방식
   - 기존 Track6 방식처럼 `experiments/track6/` 아래에 실험별 독립 폴더를 만든다.
   - 이미 `PP-HCOEF4`, `PP-HCOEF5`, `PP-HCOEF6`, `PP-HCOEF7`, `PP-HCOEF8`, `PP-HCOEF9`, `PP-HCOEF10`, `PP-HCOEF11`, `PP-HCOEF12`, `PP-HCOEF13`, `PP-HCOEF14`, `PP-HCOEF15`, `PP-HCOEF16`, `PP-HCOEF17`, `PP-HCOEF18`, `PP-HCOEF19`가 실행됐으므로 새 실험군은 `PP-HCOEF20`부터 이어서 관리한다.
   - 권장 폴더 예시:
     - `experiments/track6/PP-HCOEF20_warm_quantile_range_confidence_policy/`
     - `experiments/track6/PP-HCOEF21_warm_operational_component_huber_coefficients/`
   - 각 실험 폴더에는 최소한 아래 산출물을 남긴다.
     - `artifacts/experiment_config.json`
     - `outputs/metrics.csv`
     - `outputs/candidate_predictions.csv`
     - `outputs/feature_coefficients.csv`
     - `outputs/residual_analysis.csv`
     - `outputs/repeated_validation_summary.csv`
     - `reports/result_report.md`
     - `reports/result_report.html`

9. 필수 보고 내용
   - 어떤 기준가 생성 방식을 비교했는지
   - 어떤 피처를 추가/제거했는지
   - Huber 계수가 어떤 방향으로 잡혔는지
   - 성능이 좋아진 후보와 나빠진 후보의 차이가 무엇인지
   - 기존 `current_70_30`과 `hcoef2_size_reliability_cap005_s050` 대비 얼마나 개선됐는지
   - fixed test 개선인지, 반복 OOF에서도 유지되는 개선인지
   - 0604 신규 데이터에서는 같은 방향인지
   - 운영 반영 가능 후보인지, 추가 검증 후보인지, 보류 후보인지

10. 금지 사항
   - test 지표를 보고 후보를 고르지 않는다.
   - test 데이터로 구간 경계, 보정값, 가중치를 만들지 않는다.
   - 0604 신규 데이터만 보고 최종 후보를 고르지 않는다.
   - 작가 메타 피처를 새로 만들 때 출처와 생성 기준 없이 넣지 않는다.
   - 기존 사용자 변경사항이나 관련 없는 파일 변경을 되돌리지 않는다.

진행 순서:

1. 기존 HCOEF1~HCOEF19 산출물과 스크립트를 조사한다.
2. HCOEF4~HCOEF19에서 확인된 결론을 반복하지 않는다. basis-Huber/면적단가/segmented/risk-gated/segment median/위험 구간 shrinkage-routing/PP-V8 운영 component OOF/PP-V8 제한 이동/quantile width 점 예측 이동 방식은 기본 후보를 넘지 못했고, HCOEF15 최신 라벨 stress test, HCOEF16 PP-V8 OOF 재검증, HCOEF17 PP-V8 제한 이동 검증, HCOEF18 quantile width risk guard 검증, HCOEF19 서비스 feature pipeline 재현성 감사는 완료됐으므로 HCOEF3 안정 후보 유지, 최신 라벨 원인 분석, quantile width 기반 가격 범위/신뢰도 정책 검증, 또는 운영 component 기반 저차원 Huber 계수 재탐색을 우선한다.
3. 아직 시도하지 않은 기준가 생성/피처 계수/잔차 보정 후보를 리스트업한다.
4. 실험 계획을 간단히 세운 뒤 바로 실행한다.
5. 빠른 후보 탐색 후, 가능성 있는 후보만 반복 OOF로 검증한다.
6. 최종 후보, 목적별 후보, 보류 후보를 나누고 결과 보고서와 HTML을 작성한다.
7. `docs/track6/experiments/postprocessing_experiment_matrix.md`에 실행 결과를 업데이트한다.

최종 응답에서는 아래를 알려줘.

- 실행한 실험 ID와 폴더
- 최고 후보명
- 기준 후보 대비 fixed test/0604 개선폭
- row OOF와 artist OOF 반복 검증 결과
- Huber 계수 해석 요약
- 채택/보류 판단
- 다음에 이어서 해야 할 검증 또는 운영 반영 작업
```

## 기준 설정 메모

- `current_70_30`은 서비스 v0.1의 기준 성능을 보는 비교 기준으로 유지한다.
- `hcoef2_size_reliability_cap005_s050`는 새 실험이 넘어야 할 현재 Warm 개선 후보로 둔다.
- 최고 성능을 찾는 실험이어도 `test-only` 후보는 배제한다.
- 실험 목표가 MAPE 개선이어도 MdAPE와 p95_APE가 악화되면 보류한다.
- 운영 적용 후보는 반복 검증, fixed test, 0604 신규 데이터 방향이 모두 맞아야 한다.
