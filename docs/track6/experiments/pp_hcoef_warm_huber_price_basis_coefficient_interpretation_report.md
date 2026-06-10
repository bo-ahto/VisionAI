# Warm Huber 기준가/계수 고도화 해석 리포트

- 작성일: 2026-06-08
- 대상 실험: `PP-HCOEF1~PP-HCOEF38`
- 목적: Warm Huber에서 기준가 생성 방식, 피처별 계수 조정, 잔차 보정 후보를 종합해 현재 Warm 후보보다 안정적으로 좋은 조합이 있는지 판단
- 현재 결론: `hcoef2_size_reliability_cap005_s050`를 Warm 개선 후보로 유지
- 보류 결론: loose 기준가 Huber 후보는 MdAPE/MAPE 개선 잠재력은 크지만 p95_APE 방어가 부족해 기본 후보로 채택하지 않음
- 추가 결론: 조건부 routing은 p95를 방어했지만 개선폭이 작고 반복 OOF 안정성이 부족해 새 기본 후보로 채택하지 않음
- 추가 결론: 면적단가 기준가를 Huber 잔차 피처로 직접 넣으면 MdAPE/MAPE는 개선되지만 p95가 악화되어 기본 후보로 채택하지 않음
- 추가 결론: 면적단가 계열 segmented 보정은 MdAPE/MAPE/p95가 모두 HCOEF3보다 악화되어 새 기본 후보로 채택하지 않음
- 추가 결론: HCOEF4 loose 기준가 후보를 위험도 기반으로 제한 결합해도 p95 방어 기준을 통과하지 못해 새 기본 후보로 채택하지 않음
- 추가 결론: 원인 구간별 residual 중앙값 보정은 fixed test에서 일부 소폭 개선 후보가 있었지만 반복 OOF 안정성이 부족해 새 기본 후보로 채택하지 않음
- 추가 결론: HCOEF11 확장 반복 검증에서 `hcoef2_size_reliability_cap005_s050`는 row/artist OOF 80회 all3 개선확률 `1.0`으로 재확인됨
- 추가 결론: HCOEF12 운영 패키징 감사에서 저장 모델 재로딩 예측이 direct rebuild와 완전히 일치하고 readiness check가 모두 통과함
- 추가 결론: HCOEF13 잔차 위험 진단에서 현재 후보의 남은 큰 오차는 기준가 표본 수 `10~19`, 기준가 IQR 중간 이상, 후보 간 gap이 큰 구간, 작가 전체 fallback 구간에 집중됨
- 추가 결론: HCOEF14 위험 구간 한정 보정은 fixed test p95를 아주 작게 낮추는 후보가 있었지만 반복 OOF gate를 통과하지 못해 새 기본 후보로 채택하지 않음
- 추가 결론: HCOEF15 최신 라벨 stress test에서 HCOEF 안정 후보는 기존 70:30 대비 0604 개선을 유지했고, 운영 PP-V8/service primary component는 0604에서 더 강했지만 OOF 후보가 아니므로 즉시 채택하지 않음
- 추가 결론: HCOEF16에서 PP-V8/service component를 validation OOF와 artist OOF로 재검증했지만 fixed test p95 guard와 반복 OOF gate를 통과하지 못해 새 후보로 채택하지 않음
- 추가 결론: HCOEF17에서 PP-V8을 신뢰 구간에만 제한 반영하는 정책을 검증했지만 validation/bootstrap 기준을 통과한 후보가 없어 새 후보로 채택하지 않음
- 추가 결론: HCOEF18에서 PP-L10 quantile width를 risk gate로 붙여 HCOEF 보정폭 축소와 PP-V8 제한 이동을 검증했지만 validation/bootstrap 기준을 통과한 후보가 없어 새 후보로 채택하지 않음
- 추가 결론: HCOEF19에서 연구 산출물과 운영 v0.1 산출물의 Warm component/formula/필수 피처 재현성을 감사했고 0604 공통 829건 기준 모두 통과함
- 추가 결론: HCOEF20에서 운영 component 기반 저차원 Huber/Ridge 계수 재탐색을 수행했지만 fixed test p95 guard와 bootstrap all3 gate를 통과한 후보가 없어 새 점 예측 후보로 채택하지 않음
- 추가 결론: HCOEF20에서 quantile width 기반 가격 범위/신뢰도 tier는 validation/test에서 위험도 분리에 유효해 서비스 표시 정책 후보로 유지함
- 추가 결론: HCOEF21에서 고정 70:30 기준가를 표본 수/coverage/quantile width 기반 가변 기준가로 바꾸고 Huber residual을 검증했지만 fixed test p95 guard와 bootstrap all3 gate를 통과하지 못해 새 점 예측 후보로 채택하지 않음
- 추가 결론: HCOEF22에서 HCOEF20~21 후보를 validation OOF 구간별로 제한 적용하는 목적별 라우팅을 검증했지만 fixed test MdAPE/p95가 악화되어 새 점 예측 후보로 채택하지 않음
- 추가 결론: HCOEF23에서 현재 HCOEF 안정 후보의 남은 오차를 validation/OOF 기준으로 분해했고, `qwidth_extreme`, `gap_020_plus`, 후보 간 gap이 큰 구간이 다음 기준가/계수 조정의 우선 대상임을 확인함
- 추가 결론: HCOEF24에서 HCOEF23 위험 구간을 기준으로 risk-shrunk basis를 만들었지만 fixed test p95 guard를 통과하지 못해 새 점 예측 후보로 채택하지 않음
- 추가 결론: HCOEF25에서 더 작은 cap과 보수적 risk guard로 HCOEF24 신호를 안정화했지만 p95가 계속 소폭 악화되어 새 점 예측 후보로 채택하지 않음
- 추가 결론: HCOEF26에서 HCOEF25 후보 이동분을 low-risk/reliable 구간에만 제한 적용해 fixed test p95를 기준 후보와 동일하게 방어했지만 bootstrap all3 gate를 통과하지 못해 운영 후보 즉시 채택은 보류함
- 추가 결론: HCOEF27에서 HCOEF26 상위 후보를 반복 split/artist holdout으로 재검증했지만 repeated any2/all3 기준을 통과하지 못해 운영 후보 즉시 채택은 계속 보류함
- 추가 결론: HCOEF28에서 Huber risk model로 큰 오차 위험도를 예측해 후보 이동폭을 줄였지만 반복 검증 기준을 통과한 새 점 예측 후보는 나오지 않음
- 추가 결론: HCOEF29에서 OOF Huber meta residual 계수 결합을 시도했지만 fixed confirmation에서 MdAPE/p95가 악화되어 새 운영 후보로 채택하지 않음
- 추가 결론: HCOEF30에서 HCOEF29 source 후보를 validation-consensus segment에만 제한 적용했지만 fixed p95 guard를 통과하지 못해 새 운영 후보로 채택하지 않음
- 추가 결론: HCOEF31에서 방향 일치 segment에만 작은 cap으로 미세 보정했지만 fixed p95 guard와 반복 all3 안정성 기준을 통과하지 못해 새 운영 후보로 채택하지 않음
- 추가 결론: HCOEF32에서 ultra-micro p95-first 보정으로 fixed test p95를 소폭 낮춘 후보가 나왔지만 반복 all3 안정성이 부족해 운영 후보 즉시 채택은 보류함
- 추가 결론: HCOEF33에서 HCOEF32 핵심 후보를 row/artist 확장 반복 검증 2,000회 기준으로 재확인했지만 repeated min all3 `0.2785`로 운영 후보 승격 기준에 크게 못 미쳐 `hcoef_stable`을 현재 안정 후보로 유지함
- 추가 결론: HCOEF34에서 train-only 기준가를 재생성하고 기준가 gap을 Huber 잔차 피처로 넣으면 MdAPE/MAPE 개선 신호가 있었지만 fixed p95가 악화되어 기본 후보로 채택하지 않음
- 추가 결론: HCOEF35에서 cap/strength를 촘촘하게 낮춘 p95 방어 fine grid를 수행했지만 `hcoef_stable`의 p95를 명확히 넘는 후보가 없어 기본 후보로 채택하지 않음
- 추가 결론: HCOEF36에서 기준가 신뢰도가 높은 행에만 개선 후보를 적용하는 low-risk routing은 fixed test 세 지표를 소폭 개선했지만 반복 all3 안정성이 약해 운영 후보가 아니라 반복 검증 후보로 분리함
- 추가 결론: HCOEF37에서 HCOEF36 상위 라우팅 후보를 row/artist OOF 60회로 확장 재검증했고 any2 반복 안정성은 확인됐지만 all3 운영 기준에는 부족해 `hcoef_stable`을 현재 안정 후보로 유지함
- 추가 결론: HCOEF38에서 더 엄격한 low-risk routing을 적용했지만 repeated all3가 더 좋아지지 않았고, 적용 구간을 줄일수록 stable 대비 개선확률이 낮아져 운영 후보로 채택하지 않음

## 1. 현재 기준과 최종 판단

| 후보 | 의미 | validation MdAPE/MAPE/p95 | fixed test MdAPE/MAPE/p95 | 0604 MdAPE/MAPE/p95 | 판단 |
| --- | --- | ---: | ---: | ---: | --- |
| `current_70_30` | 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% | `0.1305 / 0.2110 / 0.6580` | `0.1405 / 0.2748 / 0.8331` | `0.2779 / 0.3774 / 0.9871` | 기존 Warm 1순위 기준 |
| `hcoef2_size_reliability_cap005_s050` | 기존 70:30 후보 위에 작은 Huber 잔차 보정 추가 | `0.1260 / 0.2082 / 0.6479`; HCOEF11 row/artist OOF all3 `1.0 / 1.0` | `0.1388 / 0.2730 / 0.8064` | `0.2731 / 0.3744 / 0.9835` | Warm 개선 후보 유지 |
| `loose_huber_basis_core_alpha0.1` | loose 기준가와 기존 후보를 Huber가 직접 재학습 | `0.1224 / 0.2077 / 0.6441` | `0.1346 / 0.2618 / 0.8916` | `0.2304 / 0.3447 / 0.9514` | MdAPE/MAPE는 좋지만 fixed test p95 악화로 보류 |
| `loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.75` | HCOEF3 안정 후보에 basis-Huber 차이를 제한 결합 | 반복 OOF 일부 개선 | `0.1384 / 0.2681 / 0.8124` | `0.2621 / 0.3618 / 0.9573` 수준의 개선 신호 | fixed test는 좋지만 반복 OOF 통과 부족으로 보류 |
| `loose_basis_core_huber_alpha0p01__route_broad_lowrisk_n30_iqr065_gap050_cap003_s075` | 신뢰도 높은 일부 샘플에만 basis-Huber 차이를 제한 적용 | 반복 OOF all3 `0.0` | `0.1384 / 0.2728 / 0.8064` | `0.2731 / 0.3744 / 0.9835` 수준 | p95는 방어했지만 개선폭과 반복 안정성 부족으로 보류 |
| `hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.50` | 면적단가/기준가 gap 피처를 HCOEF3 잔차 Huber에 직접 추가 | 반복 OOF all3 row `0.4167`, artist `0.5000` | `0.1361 / 0.2718 / 0.8298` | MAPE 개선 신호 | MdAPE/MAPE는 개선됐지만 p95 악화로 보류 |
| `hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority` | 면적단가 raw residual을 low/mid/high 위험 구간별 cap/strength로 제한 | 반복 OOF all3 `0.0` | `0.1395 / 0.2744 / 0.8340` | 악화 | segmented 방식도 HCOEF3보다 악화되어 탈락 |
| `hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only` | HCOEF3와 HCOEF4 예측 차이가 작은 구간에만 basis-Huber 방향으로 제한 이동 | 반복 OOF all3 row `0.50`, artist `0.35` | `0.1356 / 0.2670 / 0.8308` | 0604 개선 신호 | MdAPE/MAPE는 개선됐지만 p95 악화와 반복 안정성 부족으로 보류 |
| `hcoef10_pred_reliability_cap0.02_s0.25` | 예측 가격대와 기준가 표본 수 조합별 residual 중앙값을 아주 약하게 보정 | 반복 OOF all3 row `0.00`, artist `0.10` | `0.1383 / 0.2729 / 0.8062` | 0604 MdAPE 소폭 개선 | fixed test는 3지표 소폭 개선이나 반복 안정성 부족으로 보류 |
| `hcoef14_shrink_iqr_mid_high_keep050` | 기준가 IQR 중간/높음 위험 구간에서 Huber 잔차 보정폭을 절반으로 줄임 | 반복 OOF all3 row `0.00`, artist `0.00` | `0.1384 / 0.2731 / 0.8047` | `0.2734 / 0.3748 / 0.9833` | fixed test p95는 소폭 개선됐지만 반복 안정성 부족으로 보류 |
| `service_primary_ppv8_operational` | 운영 v0.1 0604 출력에서 PP-V8 계열 component가 service primary로 사용된 후보 | HCOEF OOF 후보 아님 | fixed test 미검증 | `0.2298 / 0.3359 / 0.9273` | 0604에서는 강하지만 OOF/fixed test 절차 미통과. HCOEF16에서 proxy로 재검증 완료 |
| `hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p02_s0p25` | PP-V8 component와 HCOEF 안정 후보의 차이를 Huber 잔차 피처로 제한 보정 | row/artist OOF all3 `0.85 / 0.45` | `0.1394 / 0.2728 / 0.8091` | 0604 개선 신호 | MAPE/RMSE만 극소 개선, MdAPE/p95와 artist OOF 기준 미통과로 보류 |
| `hcoef17_guard_agree_gap0p05_cap0p03_w0p5` | PP-V8과 HCOEF 안정 후보 차이가 작을 때만 PP-V8 방향으로 제한 이동 | validation bootstrap all3 낮음 | `0.1374 / 0.2735 / 0.8064` | 0604 일부 개선 | fixed test MdAPE만 개선, validation MAPE/p95 악화로 보류 |
| `hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p25` | coverage high, 표본수 10 이상, PP-V8 gap 0.15 이하일 때만 제한 이동 | validation/bootstrap gate 미통과 | `0.1384 / 0.2729 / 0.8064` | `0.2731 / 0.3739 / 0.9790` | fixed/0604 소폭 개선이나 validation 안정성 부족으로 보류 |
| `hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p03_w0p50` | quantile width가 낮고 PP-V8 gap이 작은 구간에만 PP-V8 방향으로 제한 이동 | validation/bootstrap gate 미통과 | `0.1361 / 0.2731 / 0.8064` | 0604 변화 작음 | fixed test MdAPE는 개선됐지만 MAPE 소폭 악화와 validation 안정성 부족으로 보류 |
| `hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75` | quantile width가 높은 구간에서 HCOEF 보정폭을 current_70_30 방향으로 축소 | validation MdAPE만 소폭 개선 | `0.1389 / 0.2737 / 0.8237` | `0.2731 / 0.3754 / 0.9833` | MAPE/p95와 bootstrap gate가 약해 보류 |
| `PP-HCOEF19 operational pipeline audit` | 연구 산출물과 운영 v0.1 산출물의 Warm component/formula/피처 schema 재현성 감사 | 후보 선택 실험 아님 | fixed test 후보 아님 | 0604 공통 829건 component 로그 차이 `0.0` | 다음 HCOEF 실험을 운영 산출물 기준으로 이어갈 수 있음 |
| `hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25` | 운영 component gap, quantile width, 표본 수 신뢰도를 Huber 잔차 보정 피처로 사용 | row/artist OOF `0.1263 / 0.2081 / 0.6409`, `0.1263 / 0.2080 / 0.6408` | `0.1388 / 0.2727 / 0.8089` | `0.2765 / 0.3736 / 0.9835` | OOF p95와 test MAPE는 개선됐지만 fixed p95 guard 미통과로 보류 |
| `HCOEF20 quantile range confidence tier` | quantile width와 유사 표본 수로 가격 범위/신뢰도 tier를 나눔 | high tier validation MdAPE `0.0692`, q10~q90 포함률 `0.9118` | high tier test MdAPE `0.1148`, q10~q90 포함률 `0.8636` | 0604에서는 medium/low tier가 더 안정 | 점 예측 후보가 아니라 서비스 신뢰도/범위 표시 정책 후보 |
| `hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25` | 표본 수/coverage/quantile width로 SVC:PP-V8 가변 기준가를 만들고 Huber residual로 작은 보정 | row/artist OOF `0.1263 / 0.2077 / 0.6409`, `0.1261 / 0.2078 / 0.6409` | `0.1388 / 0.2727 / 0.8099` | `0.2696 / 0.3731 / 0.9834` | OOF와 0604 MAPE 개선 신호는 있으나 fixed p95 guard와 bootstrap gate 미통과로 보류 |
| `hcoef22_route_mape_guard` | HCOEF20~21 후보 중 validation row/artist OOF에서 동시에 개선되는 구간에만 MAPE 후보를 제한 적용 | row/artist OOF `0.1250 / 0.2068 / 0.6394`, `0.1250 / 0.2068 / 0.6397` | `0.1448 / 0.2726 / 0.8164` | `0.2672 / 0.3694 / 0.9790` | validation/0604는 개선되지만 fixed test MdAPE/p95 악화로 보류 |
| `hcoef24_default_risk_basis_k8_cap0p05_s0p75` | HCOEF23 위험 구간에서 유사 작품 기준가 이동을 줄인 default risk-shrunk basis 후보 | row/artist OOF `0.1245 / 0.2082 / 0.6484` | `0.1383 / 0.2729 / 0.8079` | `0.2734 / 0.3736 / 0.9835` | MdAPE/MAPE는 소폭 개선됐지만 fixed p95 guard 미통과로 MAPE 특화 후보 |
| `hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25` | HCOEF24 기준가 신호를 더 작은 cap과 conservative guard로 제한한 저차원 Huber 잔차 후보 | row OOF `0.1252 / 0.2080 / 0.6440`, artist OOF `0.1252 / 0.2080 / 0.6453` | `0.1366 / 0.2727 / 0.8080` | `0.2726 / 0.3743 / 0.9835` | MdAPE/MAPE는 개선됐지만 p95가 `+0.0016` 악화되어 MAPE 특화 후보 |
| `hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1` | HCOEF25 후보 이동분을 극단 위험이 아닌 신뢰 구간에만 적용하고 나머지는 `hcoef_stable`로 fallback | row OOF `0.1260 / 0.2082 / 0.6425`, artist OOF `0.1260 / 0.2082 / 0.6416` | `0.1371 / 0.2727 / 0.8064` | `0.2731 / 0.3745 / 0.9835` | fixed p95는 방어했지만 bootstrap all3 gate 미통과로 반복 검증 후보 |
| `PP-HCOEF27 repeated split/artist holdout validation` | HCOEF26 후보 25개를 row 80% 반복 표본과 artist 80% holdout으로 재검증 | 상위 fixed 확인 후보 repeated min any2 `0.480`, min all3 `0.108` | `0.1371 / 0.2727 / 0.8064` | `0.2731 / 0.3745 / 0.9835` | fixed 확인 후보는 유지하지만 반복 검증 기준 미통과 |
| `hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80zero_boost0` | Huber가 예측한 큰 오차 위험도가 높으면 HCOEF26 후보 이동폭을 줄이는 risk-aware shrinkage | row OOF `0.1260 / 0.2082 / 0.6430`, artist OOF `0.1260 / 0.2082 / 0.6420`, repeated min any2/all3 `0.394 / 0.086` | `0.1372 / 0.2727 / 0.8064` | `0.2731 / 0.3745 / 0.9835` | fixed 확인 후보이나 반복 검증은 HCOEF26보다 약해 운영 후보 미채택 |
| `hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0` | 반복 OOF 신호가 강했던 direct guarded 후보를 risk Huber로 완화 | row OOF `0.1253 / 0.2081 / 0.6474`, artist OOF `0.1253 / 0.2080 / 0.6401`, repeated min any2/all3 `0.764 / 0.328` | `0.1410 / 0.2727 / 0.8064` | `0.2775 / 0.3749 / 0.9835` | 반복 신호는 비교적 강하지만 fixed MdAPE 악화로 MAPE 목적 연구 후보 |
| `hcoef29_risk_guarded_component_s0p5_cap0p08` | component delta와 risk 피처로 `actual_log - hcoef_stable` 잔차를 OOF Huber가 재학습 | row OOF `0.1242 / 0.2071 / 0.6347`, artist OOF `0.1239 / 0.2071 / 0.6392`, repeated min any2/all3 `0.928 / 0.548` | `0.1442 / 0.2718 / 0.8081` | `0.2789 / 0.3678 / 0.9446` | OOF 신호는 강하지만 fixed MdAPE/p95 악화로 보류 |
| `hcoef30_s01_all3_top5_w1` | HCOEF29 source 후보를 validation row/artist OOF가 동시에 개선된 segment에만 적용 | row OOF `0.1214 / 0.2057 / 0.6245`, artist OOF `0.1213 / 0.2053 / 0.6321`, repeated min any2/all3 `1.000 / 0.960` | `0.1402 / 0.2700 / 0.8081` | `0.2736 / 0.3716 / 0.9841` | 반복 신호는 가장 강하지만 fixed MdAPE/p95가 기준보다 악화되어 보류 |
| `hcoef30_s01_all3_top5_w0p5` | 같은 segment gate를 절반 weight로 약하게 적용 | row/artist OOF와 반복 신호는 강함, repeated min any2/all3 `0.998 / 0.892` | `0.1387 / 0.2713 / 0.8072` | `0.2792 / 0.3720 / 0.9838` | fixed p95가 기준 `0.8064`보다 소폭 높아 운영 후보 미채택 |
| `hcoef31_s06_mape_dir_top3_w0p1_cap0p005` | 잔차 방향과 source 이동 방향이 validation row/artist OOF 양쪽에서 일치하는 segment에만 작은 cap 보정 | repeated min any2/all3 `0.882 / 0.388` | `0.1382 / 0.2729 / 0.8070` | `0.2720 / 0.3744 / 0.9834` | MdAPE/MAPE는 소폭 개선됐지만 fixed p95와 반복 all3 기준 미통과로 보류 |
| `hcoef31_s06_any2_dir_top3_w0p1_cap0p005` | HCOEF31 p95 근접 후보. 방향 일치 segment 3개에만 미세 이동 | repeated min any2/all3 `0.898 / 0.410` | `0.1382 / 0.2730 / 0.8066` | `0.2731 / 0.3744 / 0.9834` | fixed p95가 기준 `0.8064`보다 근소하게 높아 운영 후보 미채택 |
| `hcoef32_s03_all3_dir_top2_w0p025_cap0p001` | HCOEF31보다 더 작은 weight/cap으로 p95-first 방향 일치 segment에만 초미세 이동 | repeated min any2/all3 `0.828 / 0.306` | `0.1388 / 0.2729 / 0.8062` | `0.2727 / 0.3744 / 0.9834` | fixed test p95는 소폭 개선됐지만 반복 all3 부족으로 fixed 확인 후보 |
| `PP-HCOEF33 extended validation` | HCOEF32 핵심 후보를 새로 튜닝하지 않고 row 80/70%, artist 80/70% 반복 검증 각 2,000회로 재확인 | 핵심 후보 repeated min any2/all3 `0.8085 / 0.2785` | `0.1388 / 0.2729 / 0.8062` | `0.2727 / 0.3744 / 0.9834` | fixed/0604 tiny 개선은 유지되지만 운영 후보 승격 기준 미달. `hcoef_stable` 유지 |
| `hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5` | train-only 기준가를 다시 만들고 기준가 gap/표본 수/IQR/크기 피처를 Huber 잔차 모델에 입력 | 확장 반복 전 후보 | `0.1373 / 0.2729 / 0.8074` | `0.2749 / 0.3746 / 0.9835` | MdAPE/MAPE 개선 신호는 있지만 p95가 기준보다 악화되어 보류 |
| `hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p35` | HCOEF34 구조에서 cap/strength를 더 촘촘하게 낮춘 p95 방어 fine grid 후보 | 확장 반복 전 후보 | `0.1365 / 0.2729 / 0.8078` | 0604 변화 작음 | MdAPE는 가장 낮지만 p95 guard 미통과로 보류 |
| `hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66` | HCOEF35 계수 이동을 전체가 아니라 기준가 신뢰도가 높은 행에만 적용하는 low-risk routing | row/artist stable all3 `0.375 / 0.375` | `0.1383 / 0.2729 / 0.8060` | `0.2734 / 0.3744 / 0.9835` | fixed test 세 지표는 개선됐지만 반복 all3가 약해 반복 검증 후보 |
| `hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90` | HCOEF36 상위 라우팅 후보를 row/artist OOF 60회로 확장 재검증한 최상위 안정 후보 | min stable any2/all3 `0.9333 / 0.4333` | `0.1383 / 0.2729 / 0.8060` | `0.2734 / 0.3743 / 0.9835` | any2 반복 안정성은 강하지만 all3 운영 기준에는 부족. Warm 안정 반복 검증 후보로 유지 |

- `hcoef2_size_reliability_cap005_s050`는 fixed test와 0604에서 세 지표가 모두 기존 70:30 기준보다 개선됨.
- `hcoef2_size_reliability_cap005_s050`는 row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률이 모두 `1.0`으로 확인됨.
- loose 기준가 Huber는 중앙 오차와 평균 오차를 크게 줄이는 방향은 확인됐지만, 큰 오차 방어 지표인 p95_APE가 fixed test에서 악화됨.
- capped blend는 p95 악화를 줄였지만 반복 OOF와 fixed test guard를 동시에 만족하는 후보가 나오지 않음.
- 조건부 routing은 p95 악화를 막았지만 적용 조건을 강하게 둘수록 성능 이득이 거의 사라짐.
- 면적단가 기준가를 직접 잔차 피처로 넣으면 Huber가 평균 오차를 줄이는 방향은 학습하지만 큰 오차 방어는 아직 부족함.
- segmented cap/strength는 p95 방어를 목표로 했지만 HCOEF3보다 전체 성능이 악화됨.
- 위험도 기반 basis 결합은 HCOEF4의 중앙/평균 오차 개선 신호를 일부 유지했지만 fixed test p95와 반복 OOF 안정성 기준을 통과하지 못함.
- 원인 구간 기반 median 보정은 fixed test에서 아주 작은 개선 신호가 있었지만 반복 OOF에서 안정적으로 재현되지 않음.
- HCOEF11 확장 검증에서는 HCOEF3 안정 후보가 row OOF/artist OOF 80회 모두에서 MdAPE/MAPE/p95 개선확률 `1.0`을 유지함.
- Bootstrap에서는 MAPE와 RMSE 개선 신호가 강하고, MdAPE/p95는 split별 신뢰구간이 넓어 개선 방향은 확인되지만 과도하게 해석하지 않음.
- HCOEF12에서는 같은 후보를 joblib 패키지로 저장하고 다시 불러왔을 때 validation/test/0604 예측 차이가 모두 `0.0`으로 재현됨.
- HCOEF13에서는 새 후보를 고르지 않고, 현재 최고 후보의 남은 위험 구간을 validation 기준으로 분리함.
- HCOEF13 기준 다음 우선 실험 구간은 `basis_n_bucket=n_10_19`, `basis_iqr_bucket=iqr_mid/high`, `ppv8_gap_sign=ppv8_pos`, `risk_cause=basis_current_disagreement`, `basis_level_simple=artist_overall`임.
- HCOEF14에서는 위 위험 구간을 실제 보정 후보로 바꿨지만 반복 OOF gate를 통과한 후보가 없었음.
- HCOEF15에서는 0604 최신 라벨 829건의 actual price join이 모두 일치했고, HCOEF 안정 후보는 기존 70:30보다 0604에서 계속 개선됨.
- HCOEF15에서 운영 PP-V8/service primary는 0604 MdAPE/MAPE/p95 균형이 `0.2298 / 0.3359 / 0.9273`으로 가장 좋았지만, 이 값은 0604 라벨로 선택하면 과적합 위험이 있으므로 운영 후보로 즉시 승격하지 않음.
- HCOEF16에서는 PP-V8/service component를 validation/test에서 같은 proxy로 재현해 검증했지만, fixed test에서는 PP-V8 proxy가 `0.1632 / 0.2816 / 0.9311`로 HCOEF 안정 후보보다 약함.
- HCOEF16의 가장 나은 PP-V8 gap Huber 후보도 fixed test에서 `0.1394 / 0.2728 / 0.8091`로 MAPE/RMSE만 극소 개선하고 MdAPE/p95는 HCOEF 안정 후보보다 악화됨.
- HCOEF16 반복 검증에서 운영 후보 gate를 통과한 후보는 없으므로, 0604에서 좋아 보이는 PP-V8 component를 현재 Warm 기본 후보로 교체하지 않음.
- HCOEF17에서는 PP-V8을 전체 반영하지 않고 gap/coverage/표본 수 조건에서만 제한 이동했지만 전체 후보 100개가 모두 보류됨.
- HCOEF17 fixed test 상위 후보는 MdAPE를 `0.1374`까지 낮췄지만 validation에서 MAPE와 p95가 악화되어 test-only 후보로 판단함.
- HCOEF17 coverage 제한 후보는 fixed test와 0604에서 매우 작은 개선 신호가 있지만 validation/bootstrap gate를 통과하지 못함.
- 0604에서는 PP-V8이 HCOEF 안정 후보보다 APE가 낮은 샘플이 `52.2%`였으나, 현재의 gap/coverage 규칙만으로 해당 샘플을 안정적으로 선별하지 못함.
- HCOEF18에서는 PP-L10 quantile width를 validation 기준 risk gate로 사용했지만 전체 후보 101개가 모두 보류됨.
- HCOEF18 fixed test 상위 후보는 MdAPE를 `0.1361`까지 낮췄지만 MAPE가 `0.2731~0.2732`로 HCOEF 안정 후보보다 소폭 악화되어 운영 후보로 채택하지 않음.
- HCOEF18 high quantile width shrink 후보는 validation MdAPE를 소폭 낮췄지만 MAPE/p95와 bootstrap gate가 약해 보류함.
- HCOEF19에서는 연구 산출물과 운영 v0.1 산출물이 같은 component를 보고 있는지 확인했고, `svc`, `current_70_30`, `ppv8`, `l10`, `quantile_width`, `price_range_ratio`가 0604 공통 829건에서 모두 일치함.
- HCOEF19에서는 운영 공식 `ppv8 = 0.75 * pp_v2 + 0.25 * l10`, `v01 = 0.70 * svc + 0.30 * ppv8`, `service_primary = ppv8`가 저장된 운영 예측값과 일치함.
- HCOEF19에서는 운영 Warm feature file 기준 필수 입력 피처 누락이 `0`개로 확인됨.
- HCOEF20에서는 운영 component mismatch 걱정 없이 저차원 Huber/Ridge 잔차 후보와 direct stack 후보를 검증함.
- HCOEF20 상위 후보는 validation OOF에서 p95를 낮추는 신호가 있었지만 fixed test p95가 기준 `0.8064`보다 소폭 악화되어 운영 후보로 채택하지 않음.
- HCOEF20 bootstrap all3 개선확률 최대값은 `0.43` 수준으로 운영 후보 기준 `0.90`에 크게 못 미침.
- HCOEF20 quantile width tier는 validation/test에서 high confidence 구간의 MdAPE와 큰 오차율이 낮아 서비스 신뢰도 표시에는 유효한 후보임.
- HCOEF21에서는 `current_70_30 = 0.7 * SVC + 0.3 * PP-V8`임을 확인한 뒤, SVC:PP-V8 비율을 표본 수/coverage/quantile width로 가변화함.
- HCOEF21 상위 후보는 validation OOF에서 MAPE/p95를 낮췄지만 fixed test p95가 `0.8099`로 HCOEF 안정 후보 `0.8064`보다 악화됨.
- HCOEF21 bootstrap all3 개선확률 최대값은 약 `0.33`으로 운영 후보 기준에 미달함.
- HCOEF21 결과상 가변 기준가와 신뢰도 피처는 해석 가능한 연구 후보로 유지하되, 점 예측 기본값은 HCOEF 안정 후보로 유지함.
- HCOEF22에서는 validation row/artist OOF에서 동시에 개선되는 구간에만 HCOEF20~21 후보를 제한 적용하는 목적별 라우팅을 검증함.
- HCOEF22 `mape_guard`는 validation과 0604에서 MAPE를 낮췄지만 fixed test MdAPE와 p95가 악화되어 운영 기본 후보로 채택하지 않음.
- HCOEF22 range confidence tier는 fixed test에서 high tier p95 `0.4927`, low tier p95 `1.7126`으로 위험 구간 분리력이 있어 점 예측이 아니라 서비스 신뢰도/범위 표시 후보로 유지함.
- HCOEF23에서는 새 보정값을 만들지 않고 HCOEF 안정 후보의 남은 오차 원인을 validation 기준으로 재분해함.
- HCOEF23 기준 우선 위험 구간은 `qwidth_extreme`, `gap_020_plus`, `svc_group_n_band=n_10_19`, `svc_group_level=artist`, `pred_spread_band=spread_extreme`임.
- HCOEF23 잔차 크기 계수 감사에서 `quantile_width`, `stable_ppv8_gap_abs`, `gap_020_plus`가 오차 위험 증가 방향으로 확인됨.
- HCOEF34에서는 기준가 생성 방식을 다시 잡고 Huber가 기준가 gap 계수를 학습하도록 했으며, MdAPE/MAPE 개선 신호를 확인함.
- HCOEF35에서는 HCOEF34 신호의 p95 악화를 줄이기 위해 cap/strength를 더 작게 쪼갰지만 p95 방어 기준을 통과하지 못함.
- HCOEF36에서는 보정 신호를 기준가 신뢰도가 높은 구간에만 제한 적용해 fixed test 세 지표를 소폭 개선함.
- HCOEF37에서는 HCOEF36 후보를 확장 반복 검증했고 any2 안정성은 확인했지만 all3 운영 기준이 약해 운영 후보 승격은 보류함.
- 따라서 현재 운영 후보를 교체하지 않고, `hcoef2_size_reliability_cap005_s050`를 Warm 개선 후보로 유지하는 판단이 가장 안정적임.

## 2. Warm Huber 가격 계산 방식

- Warm Huber는 가격을 바로 예측하지 않고 로그 가격을 먼저 예측함.
- 기본 구조는 아래와 같음.

```text
pred_log = intercept + beta_1 * z_1 + beta_2 * z_2 + ... + beta_k * z_k
pred_price = exp(pred_log)
```

- `z_j`는 표준화된 피처 값임.
- `beta_j`는 Huber가 학습한 피처별 계수임.
- 계수가 양수이면 해당 피처가 커질수록 로그 가격을 올리는 방향임.
- 계수가 음수이면 해당 피처가 커질수록 로그 가격을 낮추는 방향임.
- 실제 가격 영향은 로그 가격에서 더해진 뒤 `exp()`로 원화 가격으로 환산됨.

### 2.1 HCOEF3 안정 후보의 보정 공식

```text
base_pred_log = current_70_30
residual_log = actual_log - base_pred_log
raw_correction = HuberResidualModel(features)
limited_correction = clip(raw_correction, -0.05, 0.05) * 0.50
corrected_pred_log = base_pred_log + limited_correction
corrected_pred_price = exp(corrected_pred_log)
```

- `current_70_30`은 이미 강한 기준 후보임.
- HCOEF3는 전체 예측을 다시 만들지 않고, 남은 반복 오차만 작게 보정함.
- cap `0.05`는 로그 가격 기준 보정폭을 제한하는 장치임.
- strength `0.50`은 산출된 보정값을 절반만 반영해 과보정을 줄이는 장치임.
- 이 구조 때문에 성능 개선 폭은 크지 않지만 p95_APE와 0604 방향성이 안정적으로 유지됨.

## 3. 기준가 생성 방식 해석

| 기준가 방식 | 생성 방식 | 실험에서 본 역할 | 판단 |
| --- | --- | --- | --- |
| 작가 전체 기준가 | 같은 작가의 과거 거래 로그 가격 중앙값 | 작가별 가격 기준선을 잡는 가장 안정적인 fallback | Warm에서는 필수 기준선 |
| 작가+크기 기준가 | 같은 작가와 같은 size bucket의 과거 거래 중앙값 | 같은 작가 안에서 작품 크기별 가격 차이를 반영 | 표본이 충분하면 유효 |
| 작가+재료/지지체+크기 기준가 | 같은 작가, 재료/지지체 묶음, 크기 구간의 거래 중앙값 | 가장 세밀하지만 표본 부족 위험이 큼 | loose 정책에서 성능 잠재력 확인 |
| 재료/지지체+크기 기준가 | 작가를 빼고 재료/지지체와 크기 중심으로 묶음 | 작가 표본이 부족할 때 시장 공통 기준으로 fallback | Cold 성격의 보조 기준 |
| global 기준가 | 전체 학습 데이터 중앙값 | 모든 기준가가 비었을 때 마지막 fallback | 직접 예측력보다는 결측 방어용 |

- 기준가를 세밀하게 만들수록 MdAPE/MAPE가 좋아질 수 있음.
- 기준가를 너무 세밀하게 만들면 표본 수가 작아져 p95_APE가 악화될 수 있음.
- HCOEF4의 loose 정책은 이 효과를 잘 보여줌.
- loose 기준가 Huber는 fixed test MdAPE `0.1346`, MAPE `0.2618`로 좋았지만 p95_APE `0.8916`으로 악화됨.
- 따라서 기준가 세분화는 “대표 가격 개선”에는 유효하나, “큰 오차 방어”까지 자동으로 해결하지는 못함.

## 4. HCOEF3 안정 후보 계수 해석

`hcoef2_size_reliability_cap005_s050`의 주요 계수는 표준화된 피처 기준이다.

| 피처 | 계수 방향 | 계수 크기 | 해석 |
| --- | ---: | ---: | --- |
| `svc_fallback` | 음수 | `-0.4718` | 기존 유사 작품 기반 가격 피처가 일부 구간에서 과하게 높게 작동하는 경우를 낮추는 역할 |
| `shrunk_svc_prior` | 양수 | `0.2221` | 표본 수를 고려해 완화한 유사 작품 기준가는 안정적인 가격 기준으로 인정 |
| `current_shrunk_huber_gap` | 양수 | `0.1308` | 현재 70:30 후보와 완화 Huber 기준 사이의 차이가 남은 오차를 설명 |
| `ppv8_defensive` | 양수 | `0.1081` | 오차 안정화 후보가 큰 오차 방어에 보조적으로 기여 |
| `shrunk_huber_refit` | 양수 | `0.0877` | 완화된 기준가로 재학습한 Huber 예측값이 보조 중심선으로 작동 |
| `raw_shrunk_prior_gap` | 음수 | `-0.0580` | 원 기준가와 완화 기준가 차이가 클 때 과한 기준가 의존을 낮춤 |
| `log_area` | 양수 | `0.0570` | 같은 작가라도 작품 크기가 커질수록 가격이 올라가는 기본 시장 효과 |
| `current_ppv8_gap` | 양수 | `0.0491` | 70:30 후보와 오차 안정화 후보의 차이가 보정 방향을 알려줌 |
| `svc_group_n_log` | 음수 | `-0.0121` | 표본 수 자체는 강한 가격 상승 피처가 아니라 신뢰도 조정 축으로 작동 |
| `svc_prior_iqr` | 거의 0 | `0.0008` | 가격 범위 폭은 직접 가격 조정보다는 안정성 진단에 가까움 |

- 가장 큰 음수 계수는 `svc_fallback`임.
- 이는 “유사 작품 기반 가격 피처를 무조건 더 믿는다”가 아니라, 기존 fallback 예측이 높은 구간에서 과대예측을 낮추는 역할을 했다는 뜻임.
- `shrunk_svc_prior`는 양수로 남아 있음.
- 이는 표본 수와 fallback을 반영해 완화한 기준가는 여전히 가격 기준선으로 유효하다는 뜻임.
- `log_area`의 계수는 크지 않지만 양수로 유지됨.
- 이는 현재 후보가 이미 크기 정보를 많이 반영하고 있어, 추가 보정 단계에서는 크기가 보조 조정만 담당한다는 뜻임.

## 5. HCOEF4 기준가-Huber 후보 계수 해석

`loose_huber_basis_core_alpha0.1`의 주요 계수는 아래와 같다.

| 피처 | 계수 방향 | 계수 크기 | 해석 |
| --- | ---: | ---: | --- |
| `current_70_30` | 양수 | `0.8625` | 기존 70:30 후보가 여전히 가장 강한 중심선 |
| `basis_relaxed_unit_area_log` | 양수 | `0.4560` | 면적단가 기준가가 작품 크기 차이를 보정하는 강한 보조축 |
| `shrunk_huber_refit` | 음수 | `-0.2590` | 기존 후보들과 중복되는 중심선을 과하게 더하지 않도록 조정 |
| `shrunk_svc_prior` | 양수 | `0.2273` | 완화된 유사 작품 기준가는 여전히 유효한 가격 prior |
| `ppv8_defensive` | 양수 | `0.1711` | 오차 안정화 후보가 basis 후보에서도 방어축으로 작동 |
| `svc_fallback` | 음수 | `-0.1525` | 원 fallback 기준가에 대한 과신을 낮추는 역할 |
| `log_area` | 양수 | `0.0374` | 크기 효과는 이미 면적단가 기준가에 흡수되어 보조 역할 |
| `basis_relaxed_price_log` | 음수 | `-0.0305` | 직접 기준가 중앙값보다 면적단가 방식이 더 안정적으로 작동 |

- HCOEF4에서 가장 중요한 발견은 `basis_relaxed_unit_area_log`의 양수 계수가 큼.
- 이는 같은 작가라도 작품 크기 차이를 단순 크기 피처보다 “면적단가 기준가”로 반영하는 것이 유효하다는 의미임.
- 다만 이 후보는 p95_APE가 악화됨.
- 이유는 loose 기준이 더 많은 세부 기준가를 사용하면서 대표 가격은 좋아졌지만, 일부 희소/불안정 구간에서 큰 오차가 커졌기 때문임.
- 따라서 HCOEF4는 최종 후보가 아니라 “기준가 생성 방식 개선의 근거”로 쓰는 것이 적절함.

## 6. HCOEF5 capped blend 해석

| 후보 | 반복 OOF | fixed test | 판단 |
| --- | --- | --- | --- |
| `loose_basis_gap_huber_alpha0p1_on_hcoef2_cap0.03_s0.25` | row all3 `1.0`, artist all3 `0.9167` | MdAPE `+0.0012`, MAPE `-0.0013`, p95 `+0.0009` vs HCOEF3 | 반복 OOF는 좋지만 fixed test MdAPE 악화로 보류 |
| `loose_basis_core_huber_alpha0p01_on_hcoef2_cap0.05_s0.75` | row all3 `0.5000`, artist all3 `0.3333` | MdAPE `-0.0004`, MAPE `-0.0049`, p95 `+0.0060` vs HCOEF3 | fixed test는 좋지만 반복 OOF 불안정으로 보류 |
| `loose_basis_core_huber_alpha0p1` | row all3 `0.9167`, artist all3 `0.6667` | MdAPE `-0.0042`, MAPE `-0.0112`, p95 `+0.0853` vs HCOEF3 | p95 악화로 보류 |

- HCOEF5는 HCOEF4의 장점을 HCOEF3 안정 후보에 제한적으로 섞는 실험임.
- cap을 작게 두면 p95 악화는 줄지만 MdAPE 개선이 약해짐.
- cap을 크게 두면 MdAPE/MAPE는 좋아지지만 p95_APE가 악화됨.
- 반복 OOF와 fixed test guard를 동시에 만족한 후보는 없음.
- 따라서 HCOEF5는 “기준가 고도화 방향은 맞지만, 현재 데이터에서는 안전한 운영 후보까지는 아님”이라는 결론임.

## 7. HCOEF6 조건부 routing 해석

| 후보 | 적용 방식 | fixed test | 반복 OOF | 판단 |
| --- | --- | --- | --- | --- |
| full basis-Huber | 모든 샘플에 basis-Huber 적용 | `0.1346 / 0.2618~0.2628 / 0.8916~0.9110` | row OOF는 강하지만 artist OOF 불충분 | 중앙 오차는 좋지만 p95 위험으로 보류 |
| broad lowrisk routing | 표본 수 `>=30`, IQR `<=0.65`, gap `<=0.50`인 일부 샘플만 적용 | `0.1384 / 0.2728 / 0.8064` | all3 `0.0` | p95는 방어했지만 개선폭이 너무 작음 |
| detail/artist routing | 작가 계열 기준가가 있고 gap이 낮은 넓은 구간에 제한 적용 | MdAPE 악화, MAPE 소폭 개선, p95 유지 | all3 `0.5` 수준 | 목적별 MAPE 후보는 가능하나 기본 후보는 아님 |

- HCOEF6는 HCOEF4의 basis-Huber를 전체에 쓰지 않고, 신뢰도 조건을 만족한 샘플에만 적용한 실험임.
- 사용한 신뢰도 조건은 표본 수, 가격 분산 IQR, 기준가 level, 현재 후보와의 gap, 완화 weight임.
- 결과적으로 p95 악화는 막을 수 있었음.
- 그러나 조건을 강하게 걸면 적용 샘플이 줄어들어 MdAPE/MAPE 개선폭도 거의 사라짐.
- 조건을 넓히면 MAPE는 좋아지지만 fixed test MdAPE 또는 반복 p95 안정성이 부족함.
- 따라서 basis-Huber는 “전체 대체 모델”이나 “단순 routing 후보”보다는 HCOEF3 잔차 보정에 들어가는 설명 가능한 보조 피처로 쓰는 방향이 더 적절함.

## 8. HCOEF7 면적단가 기준가 직접 잔차 피처 해석

| 후보 | 구조 | fixed test | 반복 OOF | 판단 |
| --- | --- | --- | --- | --- |
| `hcoef7_shrunk_basis_gap_alpha0.001_cap0.03_s0.50` | HCOEF3 잔차 피처 + shrink 기준가 gap + 면적단가 기준가 | `0.1361 / 0.2718 / 0.8298` | row all3 `0.4167`, artist all3 `0.5000` | MdAPE/MAPE 개선, p95 악화로 보류 |
| `hcoef7_unit_area_reliability_alpha0.01_cap0.05_s0.75` | HCOEF3 잔차 피처 + 면적단가 기준가 + 표본 수/IQR/weight | fixed MdAPE 악화, MAPE 개선 | row all3 `0.8333`, artist all3 `0.5000` | 반복 신호는 있으나 fixed guard 미통과 |
| `hcoef7_risk_flags_alpha0.001_cap0.05_s0.50` | HCOEF3 잔차 피처 + basis risk flag | `0.1386 / 0.2719 / 0.8289` 수준 | row all3 `0.6667`, artist all3 `0.4167` | MAPE 개선 후보, p95 악화로 보류 |

- HCOEF7은 HCOEF6처럼 사람이 적용 구간을 고정하지 않고, Huber가 면적단가/신뢰도 피처의 계수를 직접 학습하게 한 실험임.
- fixed test에서는 MdAPE와 MAPE를 HCOEF3보다 낮추는 후보가 나왔음.
- 하지만 p95_APE가 HCOEF3의 `0.8064`보다 `0.017~0.026` 정도 악화됨.
- 반복 OOF에서도 row split은 일부 강하지만 artist-level split에서 all3 gate를 통과하지 못함.
- 따라서 면적단가 기준가는 가격 중심선 개선 신호가 있지만, 그대로 잔차 보정에 넣으면 큰 오차를 충분히 방어하지 못함.
- 다음 실험은 면적단가 피처 자체를 버리는 것이 아니라, p95 위험 구간을 별도로 분리해 보정 강도를 다르게 두는 segmented Huber가 더 적절함.

## 9. HCOEF8 segmented 보정 해석

| 후보 | 구조 | fixed test | 반복 OOF | 판단 |
| --- | --- | --- | --- | --- |
| `hcoef2_size_reliability_cap005_s050` | HCOEF3 안정 후보 | `0.1388 / 0.2730 / 0.8064` | 기준 후보 | 현재 유지 |
| `hcoef8_shrunk_basis_gap_alpha0.01_all_tiny_low_priority` | low/mid/high 구간별 아주 약한 basis residual 보정 | `0.1395 / 0.2744 / 0.8340` | all3 `0.0` | HCOEF3보다 악화 |
| `hcoef8_unit_area_reliability_alpha0.01_low_only_medium` | low risk 구간에만 약한 면적단가 보정 | `0.1398 / 0.2748 / 0.8331` | all3 `0.0` | HCOEF3보다 악화 |

- HCOEF8은 HCOEF7의 p95 악화를 막기 위해 보정 강도를 low/mid/high 기준가 위험 구간별로 다르게 둔 실험임.
- 기대는 low risk 구간에서는 면적단가 신호를 살리고, high risk 구간에서는 보정을 거의 하지 않는 것이었음.
- 실제 결과는 HCOEF3 안정 후보보다 모든 주요 후보가 악화됨.
- 이는 HCOEF3 잔차 보정이 이미 작은 cap/strength로 충분히 안정화되어 있고, 면적단가 기반 보정은 구간을 나누더라도 추가 이득보다 교란이 더 크다는 의미임.
- 따라서 HCOEF 계열에서는 HCOEF3 안정 후보가 현재 가장 균형 잡힌 후보임.

## 10. HCOEF9 위험도 기반 기준가 결합 해석

| 후보 | 구조 | fixed test | 반복 OOF | 판단 |
| --- | --- | --- | --- | --- |
| `hcoef2_size_reliability_cap005_s050` | HCOEF3 안정 후보 | `0.1388 / 0.2730 / 0.8064` | 기준 후보 | 현재 유지 |
| `loose_basis_core_huber_alpha0p1` | loose 기준가 Huber 단독 | `0.1346 / 0.2618 / 0.8916` | row/artist all3 `0.65 / 0.65` | MdAPE/MAPE 좋지만 p95 크게 악화 |
| `hcoef9_loose_basis_core_huber_alpha0p1_model_agreement_only` | HCOEF3와 HCOEF4 예측 차이가 작은 구간에만 제한 결합 | `0.1356 / 0.2670 / 0.8308` | row/artist all3 `0.50 / 0.35` | p95 악화와 반복 안정성 부족 |
| `hcoef9_loose_basis_core_huber_alpha0p1_low_strong_mid_light_high_stable` | low/mid 기준가 신뢰도 구간에만 제한 결합 | `0.1410 / 0.2717 / 0.8087` | row/artist all3 `0.55 / 0.25` | p95는 거의 방어했지만 MdAPE 악화 |

- HCOEF9는 HCOEF4의 강한 MdAPE/MAPE 개선 신호를 버리지 않고, 기준가 신뢰도와 모델 간 예측 차이로 적용 구간을 제한한 실험임.
- model agreement 방식은 fixed test에서 MdAPE/MAPE를 가장 많이 줄였지만 p95가 HCOEF3 기준 `0.8064`에서 `0.8308`로 악화됨.
- low/mid 신뢰도 방식은 p95를 거의 방어했지만 MdAPE 개선이 사라져 HCOEF3보다 대표 정확도가 나빠짐.
- 이는 HCOEF4 basis-Huber가 특정 구간에서는 유효하지만, 운영 기본 후보로 쓰려면 큰 오차 방어가 아직 부족하다는 의미임.
- 따라서 HCOEF9도 새 기본 후보로 채택하지 않고 HCOEF3 안정 후보를 유지함.

## 11. HCOEF10 원인 구간 기반 약한 보정 해석

| 후보 | 구조 | fixed test | 반복 OOF | 판단 |
| --- | --- | --- | --- | --- |
| `hcoef2_size_reliability_cap005_s050` | HCOEF3 안정 후보 | `0.1388 / 0.2730 / 0.8064` | 기준 후보 | 현재 유지 |
| `hcoef10_pred_reliability_cap0.02_s0.25` | 예측 가격대 + 기준가 표본 수 조합별 residual 중앙값 보정 | `0.1383 / 0.2729 / 0.8062` | row/artist all3 `0.00 / 0.10` | fixed test만 소폭 개선 |
| `hcoef10_medium_size_cap0.05_s0.50` | 재료/지지체 + 크기 조합별 residual 중앙값 보정 | `0.1441 / 0.2755 / 0.8035` | 반복 안정성 부족 | p95만 개선, 대표/평균 오차 악화 |
| `hcoef10_basis_gap_sign_cap0.03_s0.25` | 기준가와 기존 후보 간 gap 방향별 residual 중앙값 보정 | `0.1394 / 0.2734 / 0.8115` 수준 | row all3 `0.25`, artist all3 `0.20` | OOF p95 신호는 있으나 fixed guard 실패 |

- HCOEF10은 HCOEF3가 남긴 오차를 가격대, 기준가 표본 수, 기준가 분산, 크기, 재료/지지체, 기준가 gap 방향으로 나눠 확인한 실험임.
- `pred_reliability` 후보는 fixed test에서 MdAPE/MAPE/p95를 모두 아주 작게 개선했지만 반복 OOF에서는 같은 방향이 유지되지 않음.
- `medium_size`, `medium_support` 후보는 fixed test p95를 약간 낮췄지만 MdAPE/MAPE가 악화되어 가격 대표값 후보로는 부적합함.
- `basis_gap_sign` 후보는 validation 반복 OOF에서 p95 개선 신호가 일부 있었지만 artist OOF와 fixed test를 동시에 통과하지 못함.
- 따라서 원인 구간 median 보정은 운영 후보가 아니라 오차 원인 진단 자료로 유지하는 것이 적절함.

## 12. HCOEF11 확장 반복 검증 해석

| 검증 항목 | 결과 | 해석 |
| --- | --- | --- |
| row OOF 80회 | MdAPE/MAPE/p95 개선확률 `1.0 / 1.0 / 1.0` | 행 단위로 반복 분할해도 70:30 기준 후보보다 안정적으로 개선 |
| artist OOF 80회 | MdAPE/MAPE/p95 개선확률 `1.0 / 1.0 / 1.0` | 작가 단위로 분리해도 같은 방향이 유지됨 |
| fixed test | `0.1388 / 0.2730 / 0.8064` | 기준 후보 `0.1405 / 0.2748 / 0.8331` 대비 3지표 개선 |
| 0604 외부 테스트 | `0.2731 / 0.3744 / 0.9835` | 정합성 검증 중인 외부 데이터에서도 같은 방향의 개선 |
| paired bootstrap | MAPE/RMSE 개선확률 높음, MdAPE/p95 CI는 넓음 | 개선 신호는 있으나 p95는 split 민감도가 있어 운영 전 추가 stress test 필요 |

- HCOEF11은 새 보정식을 추가한 실험이 아니라 HCOEF3 안정 후보의 재현성을 강화한 감사 실험임.
- fixed test만 보고 후보를 고른 것이 아니라 validation 반복 OOF에서 같은 방향이 유지되는지 확인함.
- `hcoef2_size_reliability_cap005_s050`는 기존 70:30 후보 위에 아주 작은 Huber 잔차 보정만 더하는 구조라 설명 가능성과 운영 안정성이 높음.
- 다만 bootstrap p95 신뢰구간은 넓기 때문에, “큰 오차가 항상 줄어든다”가 아니라 “현재 split에서는 큰 오차 지표가 악화되지 않았고 반복 OOF에서도 안정적”이라고 표현하는 것이 정확함.

## 13. HCOEF12 운영 패키징 감사 해석

| 검증 항목 | 결과 | 해석 |
| --- | --- | --- |
| 패키지 저장 | `warm_hcoef12_hcoef3_stable_residual_huber.joblib` 생성 | 선택된 residual Huber 보정식을 재현 가능한 파일로 보관 |
| 저장 모델 재로딩 | validation/test/0604 direct rebuild 대비 최대 예측 차이 `0.0` | 같은 입력 피처가 있으면 동일한 예측을 재현 가능 |
| fixed test 재현 | `0.1388 / 0.2730 / 0.8064` | HCOEF11과 같은 성능 재현 |
| 0604 재현 | `0.2731 / 0.3744 / 0.9835` | 외부 스트레스 테스트에서도 같은 수치 재현 |
| readiness check | 전체 `pass` | 운영 반영 전 실험 패키지로 관리 가능 |

- HCOEF12는 새 성능 후보를 만든 실험이 아니라, HCOEF11에서 검증된 후보를 저장 가능한 artifact로 묶는 감사 실험임.
- 패키지에는 후보명, 기준 후보명, Huber alpha/cap/strength, 사용 피처 목록, source evidence, 파일 hash가 포함됨.
- 사용 피처는 `ppv8_defensive`, `svc_fallback`, `shrunk_huber_refit`, `shrunk_svc_prior`, `log_area`, `svc_group_n_log`, `svc_prior_iqr`, `current_ppv8_gap`, `current_shrunk_huber_gap`, `raw_shrunk_prior_gap`임.
- 이 패키지는 production artifact를 덮어쓴 것이 아니라, 운영 반영 여부를 결정하기 위한 재현 가능한 실험 패키지임.
- 실제 운영 반영 시에는 `current_70_30` 기준 예측값과 위 residual 피처가 서비스 feature pipeline에서 동일하게 생성되는지 별도 통합 테스트가 필요함.

## 14. HCOEF13 잔차 위험 원인 진단

| 진단 축 | validation에서 확인된 현상 | 다음 실험 방향 |
| --- | --- | --- |
| 기준가 표본 수 `10~19` | `basis_n_bucket=n_10_19`는 전체적으로는 기준 후보보다 좋지만 p95_APE가 높게 남음 | 표본 수 `10~19` 구간의 shrinkage 강도와 fallback 우선순위 재검증 |
| 작은 크기 + 표본 수 `10~19` | `size00 + n_10_19`는 MdAPE `0.2320`, MAPE `0.4923`, p95 `1.4874`로 위험도가 큼 | 작은 작품에서 기준가 영향도를 줄이거나 보수형 fallback 적용 |
| 기준가 IQR 중간/높음 | `iqr_mid` 구간은 MAPE `0.4463`, p95 `1.4109`로 큰 오차 위험이 큼 | IQR이 큰 구간은 기준가 계수 축소 또는 p95 방어 cap 적용 |
| 후보 간 gap 양수 | `ppv8_pos` 구간은 현재 후보가 70:30 기준보다 MdAPE/MAPE/p95 모두 악화됨 | 후보 gap이 큰 구간에 current_70_30 또는 보수형 후보로 routing 검증 |
| 기준가와 현재 후보 불일치 | `basis_current_disagreement` 구간은 p95가 `1.0770` 수준으로 높음 | 기준가-Huber 방향을 그대로 반영하지 말고 gap별 cap/strength 분리 |
| 작가 전체 fallback | `artist_overall` 구간은 p95가 기준 후보보다 악화되는 구간이 있음 | 작가 전체 기준가 fallback의 신뢰도별 계수 조정 또는 하향 보정 후보 검증 |

- HCOEF13은 새 보정 후보를 채택하지 않는 진단 실험임.
- fixed test를 보고 구간 규칙을 만든 것이 아니라 validation 위험 구간을 다음 실험 후보로 정리함.
- 현재 후보는 fixed test `0.1388 / 0.2730 / 0.8064`, 0604 `0.2731 / 0.3744 / 0.9835`로 기존 70:30 대비 개선을 유지함.
- 다음 HCOEF 실험은 위 위험 구간에 한정해 shrinkage, fallback, routing, cap/strength를 OOF 기준으로 비교하는 것이 적절함.

## 15. HCOEF14 위험 구간 한정 보정 검증

| 후보 유형 | 적용 방식 | fixed test 결과 | 반복 OOF 판단 | 해석 |
| --- | --- | --- | --- | --- |
| Huber 보정폭 축소 | IQR 중간/높음, 표본 수 `10~19`, 핵심 위험 구간에서 Huber 잔차 보정폭을 줄임 | 최상위 fixed test `0.1384 / 0.2731 / 0.8047` | all3 gate 통과 `0`개 | 큰 오차 p95는 아주 작게 낮출 수 있지만 반복 안정성이 없음 |
| 70:30 기준 routing | 위험 구간을 `current_70_30` 쪽으로 일부 되돌림 | 일부 MdAPE/MAPE 소폭 개선 또는 p95 악화 | all3 gate 통과 `0`개 | 단순 되돌림은 HCOEF3의 장점을 깎거나 p95를 다시 악화시킴 |
| segment residual 중앙값 보정 | 위험 구간별 validation train residual 중앙값을 작은 cap/strength로 적용 | 일부 후보 fixed p95 `0.8055~0.8062` | all3 gate 통과 `0`개 | test-only 소폭 개선 신호는 있으나 fold가 바뀌면 재현되지 않음 |

- HCOEF14는 HCOEF13에서 찾은 위험 구간을 실제 보정 후보로 바꾼 검증 실험임.
- 보정값은 validation 전체나 test를 보고 만든 것이 아니라 각 train fold 안에서만 계산함.
- fixed test에서는 `hcoef14_shrink_iqr_mid_high_keep050`이 p95_APE를 `0.8064`에서 `0.8047`로 낮췄지만 MAPE는 `0.2730`에서 `0.2731`로 소폭 악화됨.
- 반복 OOF에서는 row/artist 양쪽 모두에서 all3 개선 gate를 통과한 후보가 없음.
- 따라서 HCOEF14 결과는 “위험 구간 보정은 더 세밀하게 만들 수 있으나, 현재 데이터에서는 운영 후보로 채택할 만큼 안정적이지 않다”로 해석함.
- fixed test만 보고 후보를 바꾸면 과적합 가능성이 크므로 `hcoef2_size_reliability_cap005_s050` 유지 판단이 맞음.
- 다음 HCOEF 계열은 같은 위험 구간 보정을 반복하기보다 최신 라벨 stress test, 서비스 feature pipeline 통합 검증, 또는 별도 risk/quantile 모델 결합으로 넘어가는 것이 더 적절함.

## 16. HCOEF15 최신 라벨 stress test

| 후보 | 0604 MdAPE/MAPE/p95 | HCOEF 안정 후보 대비 | 판단 |
| --- | ---: | ---: | --- |
| `current_70_30` | `0.2779 / 0.3774 / 0.9871` | 기준보다 악화 | 기존 서비스 v0.1 기준 후보 |
| `hcoef2_size_reliability_cap005_s050` | `0.2731 / 0.3744 / 0.9835` | 기준 후보 | 기존 70:30 대비 개선 유지 |
| `hcoef14_seg_iqr_cap002_s025` | `0.2731 / 0.3741 / 0.9834` | MAPE/p95 극소 개선 | 반복 OOF gate 미통과라 보류 |
| `hcoef14_shrink_iqr_mid_high_keep050` | `0.2734 / 0.3748 / 0.9833` | p95만 극소 개선 | 반복 OOF gate 미통과라 보류 |
| `service_primary_ppv8_operational` | `0.2298 / 0.3359 / 0.9273` | 0604에서는 크게 개선 | OOF/fixed test 후보가 아니므로 다음 입력 후보 |
| `pp_v2_defensive` | `0.2263 / 0.3623 / 1.0902` | MdAPE/MAPE는 좋지만 p95 악화 | 큰 오차 위험으로 보류 |

- HCOEF15는 0604 최신 라벨을 외부 stress test로 사용한 실험임.
- 0604 라벨로 새 보정값이나 가중치를 만들지 않았음.
- actual price join 감사 결과 829건 모두 HCOEF 연구 파일과 운영 평가 파일의 실제 가격이 일치함.
- HCOEF 안정 후보는 0604에서 `current_70_30`보다 MdAPE, MAPE, p95가 모두 낮아 기존 개선 방향을 유지함.
- 운영 `service_primary_ppv8_operational`은 0604에서 HCOEF 안정 후보보다 MdAPE `-0.0433`, MAPE `-0.0385`, p95 `-0.0561`만큼 낮음.
- row bootstrap 기준 service primary의 HCOEF 안정 후보 대비 all3 개선확률은 `0.875`, artist bootstrap 기준은 `0.748`임.
- 이 수치는 0604에서 PP-V8 운영 component가 강한 신호를 가진다는 뜻이지, HCOEF 최종 후보로 바로 채택할 수 있다는 뜻은 아님.
- 해당 신호는 HCOEF16에서 `pp_v8_compact_blend_mape_guarded` proxy, HCOEF stable pred_log, gap, coverage tier, 표본 수를 저차원 Huber 계수 피처로 넣어 validation OOF에서 재검증함.

## 17. HCOEF16 PP-V8 운영 component OOF 재검증

| 후보 | fixed test MdAPE/MAPE/p95 | 0604 MdAPE/MAPE/p95 | 반복 OOF 판단 | 판단 |
| --- | ---: | ---: | --- | --- |
| `hcoef_stable` | `0.1388 / 0.2730 / 0.8064` | `0.2731 / 0.3744 / 0.9835` | 기존 통과 후보 | 현재 Warm 개선 후보 유지 |
| `ppv8_service_proxy` | `0.1632 / 0.2816 / 0.9311` | `0.2298 / 0.3359 / 0.9273` | OOF 개선 후보 아님 | 0604는 강하지만 fixed test 약함 |
| `hcoef16_stable_ppv8_blend_w010` | `0.1415 / 0.2707 / 0.8308` | `0.2582 / 0.3638 / 0.9784` | row/artist all3 `0.00 / 0.00` | MAPE는 일부 개선, MdAPE/p95 악화 |
| `hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p02_s0p25` | `0.1394 / 0.2728 / 0.8091` | 0604 개선 신호 | row/artist all3 `0.85 / 0.45` | fixed p95 guard와 artist OOF 미통과 |

- HCOEF16은 HCOEF15에서 강하게 보인 PP-V8/service component를 바로 채택하지 않고, validation OOF 기준으로 다시 검증한 실험임.
- PP-SVC3와 PP-V8 산출물의 validation/test PP-V8 proxy는 1126건에서 최대 차이 `0.0`으로 일치함.
- PP-V8 proxy 단독은 0604에서는 HCOEF 안정 후보보다 좋지만 fixed test에서는 MdAPE, MAPE, p95가 모두 약함.
- HCOEF 안정 후보에 PP-V8을 10%만 섞으면 fixed test MAPE는 `0.2730`에서 `0.2707`로 낮아지지만, MdAPE는 `0.1388`에서 `0.1415`, p95는 `0.8064`에서 `0.8308`로 악화됨.
- PP-V8 gap/coverage를 Huber residual 피처로 넣은 후보는 fixed test MAPE/RMSE를 아주 작게 낮추지만 MdAPE와 p95가 악화됨.
- row OOF와 artist OOF를 함께 보면 운영 후보 gate를 통과한 후보가 없음.
- 결론: PP-V8 component는 최신 라벨 stress test에서만 강한 신호로 남기고, 현재 Warm 기본 후보는 `hcoef2_size_reliability_cap005_s050`로 유지함.

## 18. HCOEF17 PP-V8 제한 이동 정책 검증

| 후보 | validation MdAPE/MAPE/p95 | fixed test MdAPE/MAPE/p95 | 0604 MdAPE/MAPE/p95 | 판단 |
| --- | ---: | ---: | ---: | --- |
| `hcoef_stable` | `0.1260 / 0.2082 / 0.6479` | `0.1388 / 0.2730 / 0.8064` | `0.2731 / 0.3744 / 0.9835` | 현재 Warm 개선 후보 |
| `hcoef17_guard_agree_gap0p05_cap0p03_w0p5` | `0.1260 / 0.2085 / 0.6483` 수준 | `0.1374 / 0.2735 / 0.8064` | 소폭 변화 | fixed test MdAPE만 개선, validation MAPE/p95 악화 |
| `hcoef17_guard_cov2_n10_gap0p15_cap0p05_w0p25` | `0.1260 / 0.2083 / 0.6479` 수준 | `0.1384 / 0.2729 / 0.8064` | `0.2731 / 0.3739 / 0.9790` | fixed/0604 소폭 개선, validation/bootstrap gate 미통과 |
| `ppv8_service_proxy` | `0.1544 / 0.2544 / 0.8084` | `0.1632 / 0.2816 / 0.9311` | `0.2298 / 0.3359 / 0.9273` | 0604에서는 강하지만 validation/test 약함 |

- HCOEF17은 HCOEF16의 PP-V8 전체/계수 반영 실패 이후, PP-V8을 아주 제한적으로만 쓰는 정책 실험임.
- 정책은 HCOEF 안정 후보를 기본값으로 두고, PP-V8과의 로그 예측 차이를 `cap`으로 자른 뒤 `weight`만큼만 이동함.
- 적용 조건은 `abs_ppv8_stable_gap`, `svc_coverage_tier`, `svc_group_n`처럼 예측 시점에 알 수 있는 피처만 사용함.
- fixed test에서는 gap `0.05`, cap `0.03`, weight `0.50` 후보가 MdAPE를 `0.1388`에서 `0.1374`로 낮췄지만 MAPE는 `0.2730`에서 `0.2735`로 악화됨.
- coverage high 구간에만 적용한 후보는 fixed test `0.1384 / 0.2729 / 0.8064`, 0604 `0.2731 / 0.3739 / 0.9790`으로 매우 작은 개선을 보였지만 validation/bootstrap gate를 통과하지 못함.
- 전체 100개 후보의 decision은 모두 `보류`임.
- 0604에서는 PP-V8이 HCOEF 안정 후보보다 낮은 APE를 보인 샘플이 `433/829`, 즉 `52.2%`였음.
- 다만 PP-V8이 이기는 샘플을 현재의 gap/coverage/표본 수 규칙만으로 안정적으로 구분하지 못했음.
- 결론: PP-V8은 점 예측을 이동시키는 후보보다, 가격 범위/신뢰도/risk guard를 만드는 별도 모델 입력으로 쓰는 방향이 더 적절함.

## 19. HCOEF18 quantile width risk guard 검증

| 후보 | validation MdAPE/MAPE/p95 | fixed test MdAPE/MAPE/p95 | 0604 MdAPE/MAPE/p95 | 판단 |
| --- | ---: | ---: | ---: | --- |
| `hcoef_stable` | `0.1260 / 0.2082 / 0.6479` | `0.1388 / 0.2730 / 0.8064` | `0.2731 / 0.3744 / 0.9835` | 현재 Warm 개선 후보 |
| `hcoef18_qrisk_lowq_ppv8_qwidth_q50_gap0p05_cap0p03_w0p50` | `0.1260 / 0.2085 / 0.6482` 수준 | `0.1361 / 0.2731 / 0.8064` | 0604 변화 작음 | fixed test MdAPE만 개선, validation/bootstrap gate 미통과 |
| `hcoef18_qrisk_shrink_current_qwidth_q80_cap0p03_w0p75` | `0.1253 / 0.2095 / 0.6481` | `0.1389 / 0.2737 / 0.8237` | `0.2731 / 0.3754 / 0.9833` | validation MdAPE만 개선, MAPE/p95 악화 |
| `ppv8_service_proxy` | `0.1544 / 0.2544 / 0.8084` | `0.1632 / 0.2816 / 0.9311` | `0.2298 / 0.3359 / 0.9273` | 0604에서는 강하지만 validation/test 약함 |
| `l10_seq_full_generated_bucket` | `0.1685 / 0.2981 / 0.8769` | `0.1743 / 0.3265 / 0.9818` | 운영 0604 component로만 확인 | 단독 점 예측 후보로는 약함 |

- HCOEF18은 PP-L10의 `quantile_width = q90_log - q10_log`를 HCOEF 후보에 붙인 실험임.
- quantile width 경계는 validation 분포에서만 계산함.
- 사용한 validation 경계는 q33 `1.2116`, q50 `1.3780`, q66 `1.5114`, q80 `1.7065`임.
- low quantile width 구간은 quantile 모델이 가격 범위를 좁게 본 구간임.
- high quantile width 구간은 quantile 모델이 가격 범위를 넓게 본 구간임.
- low quantile width + PP-V8 gap small 후보는 fixed test MdAPE를 `0.1361`까지 낮췄지만 MAPE가 `0.2731~0.2732`로 HCOEF 안정 후보 `0.2730`보다 소폭 악화됨.
- high quantile width shrink 후보는 validation MdAPE를 소폭 낮췄지만 validation MAPE/p95와 fixed test p95가 악화됨.
- validation row/artist bootstrap all3 개선확률이 기준 `0.90`에 크게 못 미쳐 전체 후보 101개가 모두 보류됨.
- 결론: quantile width는 HCOEF 점 예측을 직접 움직이는 후보 선택 기준으로는 아직 약함.
- 다만 quantile width는 예측 가격 범위, 신뢰도 등급, 위험 경고를 만들기 위한 별도 서비스 표시 피처로는 유지 가치가 있음.

## 20. HCOEF19 운영 피처 파이프라인 재현성 감사

| 감사 항목 | 결과 | 해석 |
| --- | --- | --- |
| 연구 `svc_numeric_seed_mean` vs 운영 `svc_numeric_seed_mean_pred_log` | 829건 로그 차이 `0.0` | 유사 작품 기반 가격 component가 연구/운영에서 동일함 |
| 연구 `ppv8_service_proxy` vs 운영 `pp_v8_compact_blend_mape_guarded_pred_log` | 829건 로그 차이 `0.0` | HCOEF16~18에서 쓴 PP-V8 proxy와 운영 PP-V8 component가 동일함 |
| 연구 `current_70_30` vs 운영 `v01_operational_pred_log` | 829건 로그 차이 `0.0` | 보고서 기준 70:30 후보가 운영 산출물과 동일하게 재현됨 |
| 연구 `l10_seq_pred_log` vs 운영 `l10_generated_bucket_seq_pred_log` | 829건 로그 차이 `0.0` | Quantile-Huber-CatBoost 순차 component가 동일함 |
| 연구 `quantile_width` vs 운영 `l10_quantile_width` | 829건 로그 차이 `0.0` | HCOEF18의 quantile width 해석을 운영 산출물에도 그대로 연결 가능함 |
| 운영 공식 검증 | 모두 통과 | `ppv8 = 0.75 * pp_v2 + 0.25 * l10`, `v01 = 0.70 * svc + 0.30 * ppv8`, `service_primary = ppv8` 일치 |
| 운영 Warm 입력 피처 schema | 필수 피처 누락 `0`개 | 다음 실험에서 운영 피처 생성 차이를 별도 장애물로 보지 않아도 됨 |

- HCOEF19는 새 점 예측 후보를 만드는 실험이 아님.
- 목적은 HCOEF16~18에서 쓴 연구 component와 실제 서비스 v0.1 component가 같은 값인지 확인하는 것임.
- 0604 공통 Warm 829건에서 연구 산출물과 운영 산출물의 핵심 component가 모두 일치함.
- 따라서 HCOEF16~18의 결론은 운영 산출물 기준에서도 동일하게 해석할 수 있음.
- 운영 `service_primary`는 현재 `ppv8_compact_blend_mape_guarded`이고, 보고서용 70:30 후보는 `v01_operational`로 함께 저장됨.
- 0604에서는 운영 PP-V8/service primary가 `0.2298 / 0.3359 / 0.9273`으로 HCOEF 안정 후보보다 좋지만, HCOEF16~18의 OOF/fixed test 기준을 통과하지 못했으므로 기본 후보 교체 근거로 쓰지 않음.
- HCOEF19 결과상 이후 HCOEF20~HCOEF38에서는 column mismatch 걱정 없이 quantile width 기반 가격 범위/신뢰도 정책, 저차원 Huber 계수 재탐색, 가변 기준가 신뢰도 보정, 목적별 라우팅, 남은 오차 원인 분석, 위험 완화 기준가 생성, 보수적 cap guard, low-risk fallback, 반복 split/artist holdout 재검증, risk Huber shrinkage, OOF Huber meta 계수 결합, validation-consensus segment gate, p95-neutral 방향 일치 미세 보정, ultra-micro p95-first 보정, 기준가 재탐색, low-risk routing, 확장 반복 검증, stricter routing을 진행할 수 있었음.

## 21. HCOEF20 운영 component 기반 저차원 Huber 재탐색

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 기준 후보 | `hcoef_stable` fixed test `0.1388 / 0.2730 / 0.8064` | 현재 넘겨야 할 Warm 개선 후보 |
| 최소 비교 기준 | `current_70_30` fixed test `0.1405 / 0.2748 / 0.8331` | HCOEF 계열 이전 서비스 v0.1 기준 후보 |
| 상위 OOF 후보 | `hcoef20_resid_huber_component_gaps_qwidth_a0p001_cap0p02_s0p25` | component gap + quantile width + 표본 수 신뢰도를 Huber 잔차 피처로 사용 |
| 상위 후보 validation row OOF | `0.1263 / 0.2081 / 0.6409` | HCOEF 안정 후보 대비 p95는 낮아지는 신호 |
| 상위 후보 validation artist OOF | `0.1263 / 0.2080 / 0.6408` | 작가 단위 OOF에서도 비슷한 방향 |
| 상위 후보 fixed test | `0.1388 / 0.2727 / 0.8089` | MAPE는 소폭 개선, p95는 기준 `0.8064`보다 악화 |
| 상위 후보 0604 stress | `0.2765 / 0.3736 / 0.9835` | MAPE는 소폭 개선, MdAPE는 악화 |
| bootstrap all3 최대 | 약 `0.43` | 운영 후보 기준 `0.90`에 크게 못 미침 |

- HCOEF20은 HCOEF19에서 검증된 운영 component만 사용해 저차원 Huber/Ridge 잔차 후보를 만들었음.
- 사용 축은 `current_70_30`, `ppv8_service_proxy`, `svc_numeric_seed_mean`, `l10_seq_pred_log`, `hcoef_stable`, `quantile_width`, `l10_price_range_ratio`, `svc_group_n_log`, `coverage_numeric`, 후보 간 gap임.
- 상위 후보의 계수 방향은 대체로 component 간 gap과 예측값 spread가 커질 때 보정폭을 줄이는 방향임.
- `quantile_width` 계수는 일부 후보에서 양수, `l10_price_range_ratio` 계수는 음수로 나타나 불확실성 피처가 단순 가격 상승/하락 피처가 아니라 잔차 방향을 보조하는 역할임을 보여줌.
- 다만 fixed test p95가 기준보다 소폭 악화되고 bootstrap all3 확률이 낮아 새 운영 점 예측 후보로는 채택하지 않음.
- 결론: HCOEF 안정 후보는 유지하고, HCOEF20 후보는 OOF 개선 신호가 있는 연구 후보로만 보류함.

### 21.1 Quantile Width 가격 범위/신뢰도 정책

| split | tier | N | q10~q90 포함률 | stable MdAPE/MAPE/p95 | 해석 |
| --- | --- | ---: | ---: | ---: | --- |
| validation | high | 34 | `0.9118` | `0.0692 / 0.1104 / 0.3019` | 신뢰도 높은 구간은 실제로 오차가 작음 |
| validation | medium | 119 | `0.8487` | `0.1194 / 0.1991 / 0.6188` | 중간 신뢰 구간 |
| validation | low | 366 | `0.8197` | `0.1292 / 0.2203 / 0.6496` | 큰 오차율이 높음 |
| test | high | 44 | `0.8636` | `0.1148 / 0.1772 / 0.4927` | test에서도 high tier는 상대적으로 안정 |
| test | medium | 127 | `0.6929` | `0.1118 / 0.1978 / 0.5178` | 포함률은 낮지만 오차는 낮은 편 |
| test | low | 436 | `0.7982` | `0.1573 / 0.3045 / 1.0320` | low tier는 p95와 큰 오차율이 높음 |
| 0604 | high | 26 | `0.6538` | `0.2234 / 0.3580 / 1.0017` | 0604에서는 표본 수가 작아 불안정 |
| 0604 | medium | 148 | `0.9054` | `0.2374 / 0.3431 / 1.0134` | 0604에서는 medium tier가 포함률이 높음 |
| 0604 | low | 655 | `0.8321` | `0.3032 / 0.3821 / 0.9788` | 0604 low tier는 중앙 오차가 큼 |

- HCOEF20의 신뢰도 tier는 validation에서만 정한 `quantile_width` 경계와 유사 표본 수를 사용함.
- high tier는 `quantile_width <= validation q33`이고 `svc_group_n >= 20`인 경우임.
- medium tier는 `quantile_width <= validation q66`이고 `svc_group_n >= 10`인 경우임.
- 나머지는 low tier임.
- 이 정책은 점 예측값을 바꾸기 위한 후보가 아님.
- 서비스 화면에서 가격 범위, 신뢰도, 주의 문구를 다르게 보여주기 위한 후보임.
- fixed test 기준 low tier의 p95가 `1.0320`으로 높아, low tier에는 가격 범위를 넓게 보여주거나 신뢰도 낮음 표시를 붙이는 것이 타당함.

## 22. HCOEF21 가변 기준가 신뢰도별 Huber 보정

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 기준 확인 | `current_70_30 = 0.7 * svc_numeric_seed_mean + 0.3 * ppv8_service_proxy` | 기존 70:30 후보의 실제 구성 확인 |
| 가변 기준가 방식 | SVC 비중을 표본 수, coverage, quantile width로 조정 | 유사 작품 기준가를 항상 70%로 고정하지 않고 신뢰도에 따라 바꿈 |
| 상위 OOF 후보 | `hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25` | 가변 기준가 gap과 신뢰도 상호작용을 Huber residual 피처로 사용 |
| 상위 후보 validation row OOF | `0.1263 / 0.2077 / 0.6409` | HCOEF 안정 후보 대비 MAPE/p95 개선 신호 |
| 상위 후보 validation artist OOF | `0.1261 / 0.2078 / 0.6409` | 작가 단위 OOF에서도 유사한 개선 신호 |
| 상위 후보 fixed test | `0.1388 / 0.2727 / 0.8099` | MAPE는 소폭 개선, p95는 기준 `0.8064`보다 악화 |
| 상위 후보 0604 stress | `0.2696 / 0.3731 / 0.9834` | 0604에서는 MdAPE/MAPE가 개선되는 신호 |
| bootstrap all3 최대 | 약 `0.33` | 운영 후보 기준 `0.90`에 크게 못 미침 |

- HCOEF21은 HCOEF20과 달리 component를 단순히 다시 stack하지 않고, 고정 70:30 기준가 자체를 신뢰도별로 바꾸는 실험임.
- 신뢰도 점수는 유사 표본 수, coverage tier, quantile width를 결합해 만듦.
- 신뢰도가 높으면 SVC 비중을 높이고, quantile width가 크거나 component gap이 큰 경우 PP-V8 쪽으로 일부 이동함.
- Huber residual은 이 가변 기준가와 HCOEF 안정 후보의 차이, low/high reliability flag, quantile width extreme flag를 계수로 학습함.
- 상위 후보의 계수는 `adaptive_basis_conservative_minus_stable`에는 음수, `adaptive_basis_ppv8_guard_minus_stable`에는 양수로 나타남.
- 해석하면, 안정 후보보다 높은 보수형 SVC 기준가를 무조건 따라가기보다 low reliability와 qwidth extreme 구간에서는 이동폭을 제한하는 방향임.
- `basis_low_reliability` 계수는 음수로 나타나, 유사 기준가를 믿기 어려운 구간에서 가격을 무리하게 올리지 않는 방향을 학습함.
- 다만 fixed test p95가 안정 후보보다 악화되고 bootstrap all3 확률이 낮아 운영 점 예측 후보로 채택하지 않음.
- 결론: 가변 기준가는 Huber가 설명할 수 있는 피처 구조로는 유효하지만, 현재 split에서는 점 예측 기본값을 바꿀 만큼 안정적이지 않음.

## 23. HCOEF22 목적별 라우팅/신뢰도 정책 검증

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 라우팅 방식 | validation row/artist OOF에서 동시에 개선되는 segment에만 후보 적용 | fixed test나 0604 residual로 구간을 고르지 않음 |
| 후보군 | HCOEF20~21 OOF 개선 후보 + HCOEF 안정 후보 | 이미 검증된 후보를 목적별로 제한 적용 |
| `mape_guard` validation row OOF | `0.1250 / 0.2068 / 0.6394` | HCOEF 안정 후보 `0.1260 / 0.2082 / 0.6479`보다 개선 |
| `mape_guard` validation artist OOF | `0.1250 / 0.2068 / 0.6397` | 작가 단위 OOF에서도 개선 |
| `mape_guard` fixed test | `0.1448 / 0.2726 / 0.8164` | MAPE는 소폭 개선되지만 MdAPE/p95가 기준보다 악화 |
| `mape_guard` 0604 stress | `0.2672 / 0.3694 / 0.9790` | 최신 라벨 stress에서는 개선 신호 |
| bootstrap | row any2 `0.8133`, artist any2 `0.8467`, all3는 `0.42/0.33` | 2개 지표 개선 가능성은 있으나 운영 all3 gate 미달 |
| range confidence high tier | fixed test p95 `0.4927` | high tier는 실제로 큰 오차율이 낮음 |
| range confidence low tier | fixed test p95 `1.7126` | low tier는 가격 범위를 넓게 보여야 하는 위험 구간 |

- HCOEF22는 새 Huber 계수를 더 추가한 실험이 아니라, 이미 나온 후보를 “어느 구간에만 쓸 수 있는지” 검증한 실험임.
- validation OOF 기준으로는 라우팅이 효과가 있었지만, fixed test에서 MdAPE와 p95가 악화되어 운영 기본 후보로 채택하지 않음.
- 0604에서는 라우팅 후보가 좋아 보이지만, 0604는 stress test이므로 이 결과만으로 후보를 승격하지 않음.
- 이 결과는 HCOEF 내부에서 더 복잡한 점 예측 라우팅을 추가하는 것보다, HCOEF 안정 후보를 유지하고 신뢰도/범위 정책을 분리하는 편이 안전하다는 근거임.
- quantile width와 유사 표본 수를 결합한 tier는 점 예측값을 바꾸기보다 서비스에서 `신뢰도 낮음`, `가격 범위 넓음`, `추가 검수 필요` 표시를 붙이는 데 적합함.

## 24. HCOEF23 남은 오차 원인 분석

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 기준 후보 | `hcoef_stable` | fixed test `0.1388 / 0.2730 / 0.8064`, 0604 `0.2731 / 0.3744 / 0.9835` 재현 |
| 비교 기준 | `current_70_30` | HCOEF 안정 후보가 validation/test/0604에서 기존 70:30보다 우위 유지 |
| 1순위 위험 구간 | `qwidth_extreme` | validation MAPE +`0.0874`, p95 +`0.3066`; fixed test에서도 p95 +`1.1304` |
| 2순위 위험 구간 | `gap_020_plus` | validation MAPE +`0.0825`, p95 +`0.2198`; fixed test에서도 p95 +`0.8870` |
| 표본 수 위험 구간 | `svc_group_n_band=n_10_19` | validation p95 +`0.3015`; fixed test p95 +`0.4992` |
| 기준가 level 위험 구간 | `svc_group_level=artist` | 작가 전체 fallback 구간에서 p95 위험이 반복됨 |
| 예측 후보 간 불일치 | `pred_spread_band=spread_extreme` | 후보 간 예측 차이가 큰 구간은 validation/fixed/0604에서 평균 오차가 커짐 |
| 잔차 크기 계수 | `quantile_width`, `stable_ppv8_gap_abs`, `gap_020_plus` | Huber 안정 후보의 남은 오차를 키우는 설명 축 |

- HCOEF23은 새 보정값을 test나 0604에서 고른 실험이 아님.
- validation row OOF와 artist OOF에서 동시에 나쁜 구간을 먼저 찾고, fixed test와 0604는 확인용으로만 사용함.
- `qwidth_extreme`은 모델이 가격 범위를 넓게 보는 구간이므로, 점 예측을 크게 움직이기보다 신뢰도/범위 표시 또는 보수적 cap 기준으로 쓰는 것이 적절함.
- `gap_020_plus`와 `pred_spread_extreme`은 HCOEF 안정 후보, PP-V8, SVC 등 후보 예측값 사이의 의견 차이가 큰 구간임.
- 이 구간에서 한 후보를 강하게 선택하면 test에 맞춘 라우팅이 되기 쉬우므로, HCOEF24~38에서는 기준가 fallback, Huber 잔차 보정 cap 축소, low-risk hard fallback, 반복 split/artist holdout 재검증, risk Huber shrinkage, OOF Huber meta 계수 결합, validation-consensus segment gate, p95-neutral 방향 일치 미세 보정, ultra-micro p95-first 보정, 기준가 재탐색, low-risk routing, 확장 반복 검증, stricter routing을 함께 확인함.
- `svc_group_n_band=n_10_19`는 표본이 아주 적지는 않지만 충분히 안정적이지 않은 중간 표본 구간임.
- 따라서 다음 기준가 생성 실험은 표본 수가 많은 구간에 기준가 계수를 더 크게 주고, 중간/불확실 구간에서는 HCOEF 안정 후보 쪽으로 shrink하는 구조가 맞음.

## 25. HCOEF24 위험 완화 기준가 생성

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 실험 목적 | HCOEF23 위험 구간에서 기준가 이동을 줄임 | loose basis-Huber의 MdAPE/MAPE 장점을 살리되 p95 악화를 막는 시도 |
| 기준 후보 | `hcoef_stable` | fixed test `0.1388 / 0.2730 / 0.8064` |
| 상위 목적별 후보 | `hcoef24_default_risk_basis_k8_cap0p05_s0p75` | fixed test `0.1383 / 0.2729 / 0.8079` |
| validation OOF | row/artist `0.1245 / 0.2082 / 0.6484` | MdAPE는 개선되지만 p95는 기준보다 소폭 악화 |
| 0604 stress | `0.2734 / 0.3736 / 0.9835` | MAPE는 소폭 개선, p95는 기준과 같은 수준 |
| 판단 | MAPE 특화 후보 | fixed p95 guard 미통과, bootstrap all3 gate 미통과 |

- HCOEF24는 HCOEF4/5의 loose 기준가를 그대로 반복하지 않고, HCOEF23에서 확인한 `qwidth_extreme`, `gap_020_plus`, `n_10_19`, `spread_extreme` 위험 신호를 기준으로 기준가 이동을 줄임.
- `risk_shrunk_basis`는 유사 작품 기준가를 바로 따르지 않고, 표본 수와 위험도에 따라 `hcoef_stable` 쪽으로 되돌린 기준가임.
- 상위 후보는 MdAPE/MAPE를 낮췄지만 fixed test p95가 `0.8064`에서 `0.8079`로 악화됨.
- direct Huber capped 후보는 validation과 0604에서 더 강한 개선 신호가 있었지만 fixed test p95가 더 크게 악화되어 기본 후보로 부적합함.
- 결론: 기준가 생성 방향은 유효하지만, HCOEF24 수준의 이동폭은 아직 p95 방어에 부족함.

## 26. HCOEF25 보수적 계수/기준가 보정

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 실험 목적 | HCOEF24의 MAPE 개선 신호를 더 작은 cap과 risk guard로 안정화 | p95 guard 통과가 핵심 |
| 기준 후보 | `hcoef_stable` | fixed test `0.1388 / 0.2730 / 0.8064` |
| 상위 목적별 후보 | `hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25` | fixed test `0.1366 / 0.2727 / 0.8080` |
| validation OOF | row `0.1252 / 0.2080 / 0.6440`, artist `0.1252 / 0.2080 / 0.6453` | OOF에서는 3지표 개선 |
| 0604 stress | `0.2726 / 0.3743 / 0.9835` | MdAPE/MAPE는 소폭 개선, p95는 기준보다 아주 작게 악화 |
| 판단 | MAPE 특화 후보 | fixed p95가 `+0.0016` 악화되어 운영 기본 후보 미채택 |

- HCOEF25는 `lowrisk_only`, `no_extreme`, `conservative`, `soft` guard를 만들어 HCOEF24 기준가 이동을 더 작게 제한함.
- cap은 `0.01~0.03`, strength는 `0.10~0.50` 범위로 낮춰 p95 방어를 우선함.
- 상위 후보의 계수에서는 `hcoef23_risk_score`가 음수 방향으로 나타나 위험 신호가 많을수록 보정 이동을 줄이는 구조가 확인됨.
- `svc_group_n_log`는 양수 방향으로 나타나 유사 표본 수가 많을수록 잔차 보정 신뢰도가 올라가는 방향을 보임.
- 다만 더 보수적으로 줄여도 fixed p95가 `0.8064` 아래로 내려가지 못했으므로, 현재 기준으로는 운영 기본 후보가 아님.
- 결론: HCOEF25는 MAPE/MdAPE 개선 가능성을 다시 확인했지만 p95 병목을 해결하지 못했으므로 `hcoef_stable`을 계속 기준 후보로 유지함.

## 27. HCOEF26 low-risk 적용/p95 fallback

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 실험 목적 | HCOEF25 후보 이동분을 안전 구간에만 제한 적용 | p95를 방어하면서 MdAPE/MAPE 개선 신호를 살리는지 확인 |
| 기준 후보 | `hcoef_stable` | fixed test `0.1388 / 0.2730 / 0.8064`, 0604 `0.2731 / 0.3744 / 0.9835` |
| 상위 목적별 후보 | `hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1` | fixed test `0.1371 / 0.2727 / 0.8064` |
| validation OOF | row `0.1260 / 0.2082 / 0.6425`, artist `0.1260 / 0.2082 / 0.6416` | p95는 OOF에서 개선, MdAPE/MAPE는 거의 기준 수준 |
| 0604 stress | `0.2731 / 0.3745 / 0.9835` | p95는 방어, MAPE는 아주 작게 악화 |
| 적용률 | fixed test `30.3%`, 0604 `15.4%` | 위험 구간은 `hcoef_stable`로 fallback하여 큰 오차 악화를 막음 |
| 판단 | 반복 검증 후보 | fixed p95 guard는 통과했지만 bootstrap all3 gate 미통과 |

- HCOEF26은 HCOEF25 후보를 전체에 적용하지 않음.
- `qwidth_extreme`, `gap_020_plus`, `spread_extreme`, `hcoef23_risk_score>=2` 같은 위험 구간은 기본적으로 `hcoef_stable`을 유지함.
- `no_extreme_reliable`, `p95_defense_core`처럼 위험 신호가 낮고 유사 표본 수가 충분한 구간에서만 HCOEF25 후보 이동분을 적용함.
- 이 방식은 fixed test에서 p95 악화를 막고 MdAPE/MAPE를 소폭 개선함.
- 다만 bootstrap all3 gate가 통과되지 않아, 운영 기본 후보로 즉시 교체하기에는 재검증 근거가 부족함.
- 결론: HCOEF26은 HCOEF25의 p95 병목을 “제한 적용”으로 완화한 첫 후보이며, HCOEF27에서 반복 split/artist holdout 재검증 대상으로 올림.

## 28. HCOEF27 반복 split/artist holdout 재검증

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 실험 목적 | HCOEF26 상위 후보가 반복 표본에서도 안정적인지 확인 | fixed test에서만 좋아진 후보를 운영 후보로 오판하지 않기 위한 재검증 |
| 후보군 | baseline/component 후보 + HCOEF26 validation OOF 상위 후보 + HCOEF26 보고서 상위 후보, 총 25개 | 새 보정식을 만들지 않고 HCOEF26 예측값을 재사용 |
| 검증 방식 | validation row OOF와 validation artist OOF에서 각각 500회 row 80% subsample, artist 80% holdout | 같은 후보가 일반 표본과 작가 단위 분리 표본에서 반복적으로 개선되는지 확인 |
| 상위 fixed 확인 후보 | `hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1` | HCOEF26의 대표 low-risk fallback 후보 |
| 상위 후보 fixed test | `0.1371 / 0.2727 / 0.8064` | MdAPE/MAPE는 `hcoef_stable`보다 개선, p95는 동일 수준 방어 |
| 상위 후보 0604 stress | `0.2731 / 0.3745 / 0.9835` | p95는 방어하지만 MAPE는 아주 작게 악화 |
| 상위 후보 반복 검증 | repeated min any2 `0.480`, min all3 `0.108` | 운영 후보로 보기에는 반복 개선 확률이 부족 |
| direct guarded 참고 후보 | repeated any2 최대 `0.776~0.832`, all3 최대 `0.350~0.406` | 반복 OOF 신호는 더 강하지만 fixed test MdAPE가 `0.1410` 수준으로 악화 |
| 판단 | 새 운영 후보 채택 없음 | HCOEF26은 fixed 확인 후보/연구 후보로 유지하고 `hcoef_stable`을 Warm 개선 기준 후보로 유지 |

- HCOEF27은 HCOEF26의 후보를 더 많이 튜닝한 실험이 아님.
- HCOEF27은 이미 나온 HCOEF26 후보가 반복 표본에서도 버틸 수 있는지 확인한 검증 실험임.
- 상위 후보는 fixed test에서 MdAPE/MAPE가 좋아지고 p95를 방어했지만, 반복 표본에서 최소 2개 지표 개선 확률이 `0.480`에 그침.
- 세 지표를 동시에 개선할 확률은 `0.108`로 낮아 운영 기본 후보로 승격하기에는 근거가 부족함.
- direct guarded 후보는 반복 OOF 개선 확률이 더 높았지만 fixed test MdAPE가 기준보다 악화되어, 안정적인 운영 후보가 아니라 연구 후보로만 남김.
- HCOEF27 결론: HCOEF26 정책을 단순히 더 미세 조정하기보다, p95/risk 전용 모델 또는 가격 범위/신뢰도 정책과 분리해서 다루는 방향이 더 적절함.

## 29. HCOEF28 Huber risk-aware shrinkage

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 실험 목적 | 큰 오차 위험도를 Huber로 예측하고 위험도가 높을수록 후보 이동폭을 줄임 | HCOEF26/27의 p95·반복 검증 병목을 해결하려는 시도 |
| risk 학습 대상 | `abs(actual_log - hcoef_stable_log)` | 현재 안정 후보가 크게 틀리는 정도를 예측 |
| risk 입력 피처 | `quantile_width`, 후보 간 gap, `svc_group_n`, `hcoef23_risk_score`, `log_area`, 위험 flag | 기준가 신뢰도와 후보 간 불일치를 선형 계수로 해석 |
| 적용식 | `corrected_log = hcoef_stable + weight * (source_candidate - hcoef_stable)` | 위험도가 높으면 후보 이동폭을 줄이고, 위험도가 낮으면 후보 이동을 일부 허용 |
| 대표 fixed 후보 | `hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80zero_boost0` | HCOEF26 low-risk 후보를 risk q80 이상에서 더 줄인 후보 |
| 대표 후보 fixed test | `0.1372 / 0.2727 / 0.8064` | HCOEF26 top `0.1371 / 0.2727 / 0.8064`보다 개선되지 않음 |
| 대표 후보 반복 검증 | repeated min any2 `0.394`, min all3 `0.086` | HCOEF26/HCOEF27 top 후보보다 반복 안정성이 약함 |
| direct guarded shrink 후보 | repeated min any2 최대 `0.764`, min all3 `0.328` | 반복 신호는 있으나 fixed MdAPE `0.1410`으로 기준보다 악화 |
| 판단 | 새 운영 후보 채택 없음 | risk Huber는 점 예측 이동보다 위험도/신뢰도 설명 피처로 남기는 것이 적절 |

- HCOEF28은 fixed test 결과를 보고 후보 이동폭을 고르지 않음.
- risk Huber는 validation OOF에서 현재 안정 후보의 절대 로그 오차를 학습함.
- 계수 해석상 `quantile_width`, `ppv8_svc_gap_abs`, `pred_spread_numeric`, `risk_gap_020_plus`, `risk_artist_fallback`이 큰 오차 위험 증가 방향으로 나타남.
- 이는 기존 HCOEF23의 위험 구간 진단과 방향이 일치함.
- 다만 이 위험도를 이용해 점 예측 이동폭을 줄여도 반복 검증 통과 후보는 나오지 않음.
- 결론: HCOEF28은 “큰 오차 위험을 설명하는 피처”는 확인했지만, 이를 점 예측 보정으로 바로 쓰기에는 부족함.
- 다음에는 이 위험 피처를 점 예측 보정이 아니라 가격 범위, 신뢰도, 수동 검수 필요 여부에 연결하는 것이 더 타당함.

## 30. HCOEF29 OOF Huber meta residual 계수 결합

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 실험 목적 | 기존 component delta와 신뢰도/risk 피처를 Huber가 OOF로 재결합 | 고정 70:30 비율보다 데이터 기반 계수 결합이 안정적인지 확인 |
| 학습 target | `actual_log - hcoef_stable_log` | 현재 안정 후보가 남긴 잔차만 작게 보정 |
| 입력 피처 | `current_delta`, `ppv8_delta`, `svc_delta`, `l10_delta`, `quantile_width`, `risk_norm`, `svc_group_n_log`, HCOEF26 후보 delta | 기준가/오차 안정화/유사 작품 피처가 stable 대비 얼마나 움직여야 하는지 선형 계수로 확인 |
| 적용식 | `corrected_log = hcoef_stable + clip(strength * HuberResidual, -cap, cap)` | Huber가 제안한 보정값을 cap으로 제한해 과한 이동 방어 |
| 대표 반복 후보 | `hcoef29_risk_guarded_component_s0p5_cap0p08` | risk 피처와 component delta를 함께 사용 |
| validation OOF | row `0.1242 / 0.2071 / 0.6347`, artist `0.1239 / 0.2071 / 0.6392` | OOF에서는 `hcoef_stable`보다 MdAPE/MAPE/p95가 모두 개선 |
| 반복 검증 | repeated min any2 `0.928`, min all3 `0.548` | 최소 2개 지표 개선 신호는 강하지만 세 지표 동시 개선은 충분하지 않음 |
| fixed test | `0.1442 / 0.2718 / 0.8081` | MAPE는 개선되지만 MdAPE와 p95가 기준보다 악화 |
| 0604 stress | `0.2789 / 0.3678 / 0.9446` | MAPE/p95는 개선되지만 MdAPE는 악화 |
| 판단 | 새 운영 후보 채택 없음 | OOF에서 잘 맞는 잔차 패턴이 fixed/stress에서 그대로 유지되지 않음 |

- HCOEF29는 fixed test 결과를 보고 계수나 cap을 고르지 않음.
- Huber meta residual은 validation OOF에서만 잔차 보정식을 학습함.
- `risk_guarded_component` 계열은 OOF에서 가장 강한 신호를 보였지만 fixed MdAPE가 `0.1388`에서 `0.1442`로 악화됨.
- `all_lowdim_signal` 계열도 OOF 개선 신호가 있으나 fixed p95가 `0.8302` 수준으로 악화됨.
- 결론: 현재 데이터에서는 Huber가 OOF 잔차를 너무 잘 따라가면 fixed test에서 일반화가 약해짐.
- HCOEF29 결과는 “component delta + risk 피처”가 설명력은 있지만, 점 예측 보정 후보로 쓰려면 더 강한 holdout 검증 또는 목적별 라우팅이 필요하다는 근거로 남김.

## 31. HCOEF30 validation-consensus segment gate

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 실험 목적 | HCOEF29 후보를 전체에 적용하지 않고 validation row OOF와 validation artist OOF가 동시에 개선된 segment에만 제한 적용 | OOF 잔차 추종의 과적합 위험을 줄이고, 실제로 개선 신호가 반복된 구간만 쓰려는 실험 |
| source 후보 | HCOEF29 repeated 상위 후보 10개 | 이미 OOF 신호가 있던 후보만 재사용해 새 search 공간을 과하게 넓히지 않음 |
| segment 선택 기준 | qwidth, 표본 수, 후보 간 gap, 예측 spread, 신뢰도 level 조합 | fixed test/0604를 보지 않고 validation row/artist OOF consensus로만 rule 선택 |
| 적용식 | `corrected_log = hcoef_stable + weight * (source_candidate - hcoef_stable)` | 선택된 segment 안에서만 source 후보 방향으로 이동하고, 나머지는 `hcoef_stable` 유지 |
| 반복 최상위 후보 | `hcoef30_s01_all3_top5_w1` | HCOEF29 `risk_guarded_component`를 validation-consensus segment 5개에 적용 |
| validation OOF | row `0.1214 / 0.2057 / 0.6245`, artist `0.1213 / 0.2053 / 0.6321` | HCOEF 전체 실험 중 OOF 신호는 가장 강한 편 |
| 반복 검증 | repeated min any2 `1.000`, min all3 `0.960` | 반복 표본에서는 매우 안정적인 개선 신호 |
| fixed test | `0.1402 / 0.2700 / 0.8081` | MAPE는 개선되지만 MdAPE와 p95가 `hcoef_stable`보다 악화 |
| p95 근접 후보 | `hcoef30_s01_all3_top5_w0p5` fixed `0.1387 / 0.2713 / 0.8072` | p95가 기준 `0.8064`보다 근소하게 높아 guard 미통과 |
| 판단 | 새 운영 후보 채택 없음 | segment gate로 반복 안정성은 크게 좋아졌지만 fixed p95 guard를 넘지 못함 |

- HCOEF30은 HCOEF29보다 과격한 보정이 아님.
- HCOEF30은 HCOEF29의 source 후보를 validation에서 반복 개선된 segment에만 제한 적용한 보수적 라우팅 실험임.
- `hcoef30_s01_all3_top5_w1`은 반복 검증 수치만 보면 매우 강하지만, fixed test에서 p95가 `0.8081`로 기준 후보 `0.8064`보다 높음.
- `hcoef30_s01_all3_top5_w0p5`는 p95 악화를 크게 줄였지만 여전히 fixed p95 guard를 아주 작게 통과하지 못함.
- 따라서 HCOEF30은 “OOF와 반복 split에서 좋아 보이는 구간 선택도 fixed p95 병목을 완전히 해결하지 못했다”는 근거임.
- 다음 실험에서 같은 component 이동을 더 세밀하게 반복하는 것보다, 이 segment/risk 신호를 가격 범위, 신뢰도, 수동 검수 필요 여부에 연결하는 방향이 더 타당함.

## 32. HCOEF31 p95-neutral directional micro correction

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 목적 | HCOEF30의 fixed p95 병목 완화 | 강한 source 이동 대신 방향이 맞는 구간에만 아주 작은 보정을 적용 |
| 방향 확인 | `actual_log - hcoef_stable` 중앙값과 `source_candidate - hcoef_stable` 중앙값의 부호가 validation row/artist OOF 양쪽에서 일치하는지 확인 | 안정 후보가 낮게 본 구간은 높이는 방향, 높게 본 구간은 낮추는 방향으로만 움직임 |
| 적용식 | `corrected_log = hcoef_stable + clip(weight * (source_candidate - hcoef_stable), -cap, cap)` | 조건을 만족하지 않으면 `hcoef_stable` 유지 |
| 상위 MAPE 후보 | `hcoef31_s06_mape_dir_top3_w0p1_cap0p005` fixed `0.1382 / 0.2729 / 0.8070`, 0604 `0.2720 / 0.3744 / 0.9834` | MdAPE/MAPE는 소폭 개선됐지만 p95가 기준 `0.8064`보다 높음 |
| p95 근접 후보 | `hcoef31_s06_any2_dir_top3_w0p1_cap0p005` fixed `0.1382 / 0.2730 / 0.8066`, repeated min any2/all3 `0.898 / 0.410` | p95 악화는 거의 줄였지만 기준 후보를 넘지는 못함 |
| 판단 | 새 운영 후보 채택 없음 | 방향 일치와 작은 cap만으로는 p95 병목을 넘기 어려움 |

- HCOEF31은 HCOEF30의 보정 강도를 더 줄인 실험임.
- HCOEF31은 source 후보를 전체에 적용하지 않고, validation row/artist OOF 양쪽에서 잔차 방향과 source 이동 방향이 맞는 segment에만 적용함.
- 이 방식은 과한 보정을 막는 데는 도움이 됐지만, fixed p95가 기준 `0.8064`보다 근소하게 높아 운영 후보 기준을 통과하지 못함.
- repeated any2는 `0.88~0.90` 수준까지 나왔지만 repeated all3는 `0.39~0.41` 수준이라 안정 후보로 보기 부족함.
- 결론: 같은 component 이동을 더 작게 만드는 것만으로는 충분하지 않음.
- 다음 개선은 점 예측 이동을 계속 세분화하기보다, p95/risk 전용 모델이나 가격 범위/신뢰도 정책으로 위험 신호를 분리하는 방향이 더 적절함.

## 33. HCOEF32 ultra-micro p95-first directional correction

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 목적 | HCOEF31의 fixed p95 근소 악화 완화 | weight와 cap을 더 줄여 점 예측 이동을 거의 움직이지 않는 수준으로 제한 |
| 설정 | source 후보 3개, weight `0.025/0.050`, cap `0.001/0.0025/0.005`, top_n `1/2` | full grid는 비용이 커 lite grid로 반복 검증 비용 통제 |
| p95-first 조건 | validation row/artist OOF segment 양쪽에서 p95가 기준보다 나빠지지 않는 rule을 별도 목적 후보로 사용 | fixed test를 보지 않고 p95 방어 후보를 먼저 좁힘 |
| 상위 fixed 확인 후보 | `hcoef32_s03_all3_dir_top2_w0p025_cap0p001` fixed `0.1388 / 0.2729 / 0.8062` | `hcoef_stable` fixed `0.1388 / 0.2730 / 0.8064` 대비 MAPE/p95/RMSE가 아주 작게 개선 |
| 0604 확인 | `0.2727 / 0.3744 / 0.9834` | 0604에서도 기준보다 소폭 개선되지만 튜닝 기준은 아님 |
| 반복 검증 | repeated min any2/all3 `0.828 / 0.306` | any2는 참고 가능하지만 all3 안정성은 운영 후보 기준에 부족 |
| 판단 | fixed 확인 후보 | 운영 후보 즉시 채택은 보류하고 추가 반복 검증 후보로만 관리 |

- HCOEF32는 HCOEF31보다 더 보수적인 점 예측 이동 실험임.
- 상위 후보는 fixed test에서 p95를 `0.8064`에서 `0.8062`로 낮췄고 MAPE/RMSE도 아주 작게 개선함.
- 다만 MdAPE 개선폭은 사실상 0에 가깝고, repeated all3가 `0.306`이라 반복 안정성 기준에는 부족함.
- 이 결과는 “초미세 계수 보정으로 fixed p95를 넘길 수는 있지만, 운영 후보로 쓰기에는 개선폭과 반복 안정성이 약하다”는 근거임.
- 따라서 HCOEF32는 운영 후보 교체가 아니라 fixed 확인 후보/추가 반복 검증 후보로 관리함.

## 34. HCOEF33 HCOEF32 extended repeated validation

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 목적 | HCOEF32 핵심 후보의 tiny p95 개선이 반복 split/artist split에서도 안정적인지 확인 | 새 후보를 만들지 않고 검증 강도만 높임 |
| 검증 대상 | `hcoef_stable`, `current_70_30`, HCOEF32 핵심 후보 4개, HCOEF29 source 후보 2개 | fixed에서 좋아 보인 후보와 OOF에서 강했던 source 후보를 함께 비교 |
| 반복 방식 | validation row/artist OOF에서 row 80/70%, artist 80/70%를 각 2,000회 반복 | 한 번의 split이 아니라 표본 구성 변화에 대한 민감도를 확인 |
| 핵심 후보 | `hcoef32_s03_all3_dir_top2_w0p025_cap0p001` | fixed `0.1388 / 0.2729 / 0.8062`, 0604 `0.2727 / 0.3744 / 0.9834` |
| 확장 반복 결과 | min any2/all3 `0.8085 / 0.2785` | MAPE와 p95는 자주 좋아지지만 MdAPE까지 동시에 좋아지는 비율은 낮음 |
| 판단 | fixed/0604 확인 후보 | 운영 후보 승격 기준 repeated all3 `0.90`에 크게 못 미쳐 기본 후보로 채택하지 않음 |

- HCOEF33은 HCOEF32 결과를 다시 튜닝하지 않고 검증만 강화한 실험임.
- HCOEF32 핵심 후보는 fixed test와 0604에서 tiny p95 개선을 유지함.
- 그러나 확장 반복 검증에서 repeated min all3가 `0.2785`로 낮아, 세 지표가 동시에 안정적으로 개선된다고 보기 어려움.
- HCOEF29 source 후보들은 validation/OOF 반복 신호가 HCOEF32보다 강하지만 fixed test MdAPE/p95가 악화되어 운영 후보 기준을 통과하지 못함.
- 결론: 현재 component를 더 미세하게 움직이는 방식만으로는 `hcoef_stable`을 안정적으로 넘기 어렵고, 다음 개선은 기준가 생성 방식 재탐색 또는 가격 범위/신뢰도 정책으로 이동하는 것이 타당함.

## 35. HCOEF34 기준가 생성 방식 재탐색

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 목적 | 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체 기준가를 train-only로 다시 생성 | test 라벨을 보지 않고 유사 작품 기반 가격 축을 재구성 |
| Huber 입력 | 기준가 residual, 기준가 표본 수, 기준가 IQR, 크기/형태 피처 | Huber가 “기준가와 현재 예측의 차이를 얼마나 믿을지”를 계수로 학습 |
| 상위 후보 | `hcoef34_resid_basis_resid_all_a0p001_cap0p005_s0p5` | fixed `0.1373 / 0.2729 / 0.8074`, 0604 `0.2749 / 0.3746 / 0.9835` |
| 판단 | MdAPE/MAPE 개선 후보 | p95가 `hcoef_stable`보다 `+0.0010` 악화되어 운영 후보 미승격 |

- HCOEF34는 “기준가를 더 잘 만들면 Huber 계수 보정이 더 좋아질 수 있는가”를 확인한 실험임.
- 기준가 gap은 중앙/평균 오차를 줄이는 방향으로 작동했지만, 일부 큰 오차 구간에서 p95를 악화시킴.
- 따라서 기준가 신호는 버리지 않고, p95 방어를 위해 HCOEF35 fine grid로 이동함.

## 36. HCOEF35 p95 방어 fine grid

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 목적 | HCOEF34 구조에서 cap/strength를 더 작게 쪼개 p95 악화를 막을 수 있는지 확인 | 개선 신호를 유지하되 큰 오차 악화를 줄이는 실험 |
| 탐색 범위 | cap `0.001~0.010`, strength `0.10~0.50` | 보정폭을 작게 제한해 Huber 이동을 보수화 |
| 최고 MdAPE 후보 | `hcoef35_resid_basis_resid_all_a0p01_cap0p01_s0p35` fixed `0.1365 / 0.2729 / 0.8078` | 중앙 오차는 더 좋아졌지만 p95 guard 미통과 |
| p95 최접근 후보 | fixed p95 `0.806407` | `hcoef_stable`보다 약 `+0.000041` 높아 명확한 p95 개선으로 보기 어려움 |

- HCOEF35는 HCOEF34의 약점을 줄이려는 보수적 계수 실험임.
- MdAPE는 좋아졌지만 p95가 기준을 확실히 넘지 못했기 때문에 운영 후보로 올리지 않음.
- 다만 “좋은 방향을 전체에 적용하지 말고 신뢰 구간에만 적용하면 가능성이 있는가”라는 HCOEF36 가설로 이어짐.

## 37. HCOEF36 low-risk routing

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 목적 | HCOEF35 이동분을 전체에 적용하지 않고 기준가 신뢰도가 높은 행에만 적용 | p95 위험이 큰 행은 기존 `hcoef_stable`로 유지 |
| 대표 후보 | `hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66` | fixed `0.1383 / 0.2729 / 0.8060`, 0604 `0.2734 / 0.3744 / 0.9835` |
| 적용률 | test 약 `62.1%` | 전체가 아니라 절반 이상 신뢰 구간에만 제한 적용 |
| 반복 안정성 | row/artist stable all3 `0.375 / 0.375` | fixed test 개선은 있지만 운영 후보로 보기에는 반복 안정성이 약함 |

- HCOEF36은 Huber 계수 보정의 장점을 “신뢰도가 높은 샘플에만” 쓰는 실험임.
- fixed test에서는 MdAPE/MAPE/p95가 모두 소폭 좋아졌지만 반복 all3가 낮음.
- 따라서 바로 채택하지 않고 HCOEF37에서 상위 라우팅 후보를 더 많이 반복 검증함.

## 38. HCOEF37 HCOEF36 확장 반복 검증

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 목적 | HCOEF36 상위 라우팅 후보 8개가 반복 split에서도 유지되는지 확인 | 새 후보를 만들지 않고 검증 강도를 높임 |
| 반복 방식 | row OOF 60회, artist OOF 60회 | 행 단위 변동과 작가 단위 변동을 모두 확인 |
| 최상위 후보 | `hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90` | fixed `0.1383 / 0.2729 / 0.8060`, 0604 `0.2734 / 0.3743 / 0.9835` |
| 반복 결과 | min stable any2/all3 `0.9333 / 0.4333` | 두 지표 이상 개선은 안정적이나 세 지표 동시 개선은 아직 약함 |
| 판단 | Warm 안정 반복 검증 후보 | 운영 기본 후보는 `hcoef_stable` 유지 |

- HCOEF37은 HCOEF36이 test-only 개선인지 확인하기 위한 검증 실험임.
- any2 반복 안정성이 `0.90`을 넘었으므로 개선 신호 자체는 의미가 있음.
- all3가 `0.4333`에 그쳐 운영 기본 후보 교체 기준에는 부족함.
- 다음 실험은 더 강한 점 예측 이동보다 `hcoef_stable`을 유지한 상태에서 신뢰도/가격 범위 정책을 강화하거나, 더 엄격한 route 조건으로 all3 안정성을 다시 확인하는 방향이 타당함.

## 39. HCOEF38 stricter low-risk routing

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| 목적 | HCOEF37에서 부족했던 all3 안정성을 높이기 위해 적용 구간을 더 엄격하게 제한 | 더 좋은 fixed test가 아니라 반복 안정성 개선 여부를 확인 |
| 후보 수 | 27개 | HCOEF35 상위 3개 base improver x stricter route 9개 |
| 대표 route | `n_ge10_spread_q66_area80`, `spread_q50`, `n_ge5_spread_q50_area80`, `precise_level_spread_q50` | 표본 수, 기준가 component spread, 면적 중앙 구간, 정밀 기준가 level을 사용 |
| 최상위 후보 | `hcoef38_route_best_mdape_all_cap0p01_s0p35__n_ge10_spread_q66_area80` | fixed `0.1388 / 0.2728 / 0.8064`, 0604 `0.2731 / 0.3744 / 0.9835` |
| 반복 결과 | min stable any2/all3 `0.7167 / 0.2167` | HCOEF37의 `0.9333 / 0.4333`보다 낮음 |
| 판단 | 기존 70:30 대비 p95 방어 후보 | 운영 후보나 반복 검증 후보로 승격하지 않음 |

- HCOEF38은 HCOEF37 후보를 더 좁은 “안전 구간”에만 적용하면 all3가 올라가는지 확인한 실험임.
- 결과적으로 적용률이 test 약 `23.1%`까지 줄어든 상위 후보는 p95를 방어했지만, stable 대비 MdAPE/MAPE/p95가 동시에 좋아지는 반복 확률은 낮았음.
- `spread_q50`처럼 fixed test p95를 더 낮춘 후보도 있었지만, row/artist repeated all3는 `0.0`에 가까워 운영 후보가 아님.
- 결론: low-risk routing을 더 엄격하게 만드는 것만으로는 HCOEF37의 all3 병목을 해결하지 못함.
- 다음 방향은 라우팅 조건 추가가 아니라 기준가 생성 방식 또는 Huber 저차원 계수 구조를 다시 보는 것이 타당함.

## 40. 피처별 의미 정리

| 피처 축 | 왜 Warm Huber에서 의미가 있는가 | 이번 실험에서의 결론 |
| --- | --- | --- |
| 작가 기준가 | Warm은 같은 작가의 과거 거래가 있으므로 작가별 가격 수준을 직접 반영할 수 있음 | 가장 안정적인 fallback 축 |
| 작가+크기 기준가 | 같은 작가라도 크기에 따라 가격대가 달라짐 | 표본이 충분하면 유효 |
| 작가+재료/지지체+크기 기준가 | 작품 조건을 가장 세밀하게 맞춤 | 대표 오차 개선 가능, 희소 구간 p95 위험 존재 |
| 면적단가 기준가 | 작품 크기를 가격 총액이 아니라 단위 면적 가격으로 보정 | HCOEF4에서 강한 양수 계수 확인 |
| 유사 작품 표본 수 | 기준가 신뢰도를 알려줌 | 가격 자체를 올리는 피처라기보다 보정 강도 조절 축 |
| IQR | 비교군 가격 분산을 알려줌 | 직접 가격 계수보다는 위험도/신뢰도 진단 축 |
| 오차 안정화 후보 | 평균 오차와 큰 오차를 방어하는 보조 예측값 | HCOEF3 안정 후보에서 유지할 가치 있음 |
| Huber 기본/완화 예측값 | 기존 선형 예측 중심선 | 단독 대체보다 잔차 보정 또는 보조 피처로 적합 |
| 조건부 routing 신뢰도 | basis-Huber를 적용해도 되는 샘플을 고르는 기준 | p95 방어는 가능하지만 개선폭이 작아 기본 후보로는 부족 |
| 면적단가 기준가 잔차 피처 | 작품 크기 차이를 단위 면적 가격으로 다시 설명 | MdAPE/MAPE 개선 신호는 있으나 p95 방어 장치가 함께 필요 |
| segmented cap/strength | 위험 구간별로 보정 강도를 달리함 | 이번 데이터에서는 HCOEF3보다 악화되어 탈락 |
| quantile width | q90 로그 예측과 q10 로그 예측의 차이로, 모델이 가격 범위를 얼마나 넓게 보는지 나타냄 | 점 예측 이동보다는 가격 범위/신뢰도 표시 피처로 유지 |
| 운영 component 일치성 | 연구 후보와 서비스 산출물이 같은 값을 내는지 확인하는 재현성 기준 | HCOEF19에서 0604 공통 829건 기준 모두 일치 |
| 운영 component gap | HCOEF 안정 후보와 `current_70_30`/PP-V8/SVC/L10 component의 차이 | HCOEF20에서 OOF p95 개선 신호는 있으나 fixed p95 guard 미통과 |
| 가변 기준가 신뢰도 | 표본 수, coverage, quantile width로 SVC:PP-V8 비율을 조정하는 기준 | HCOEF21에서 설명 가능한 계수 후보이나 fixed p95 guard와 bootstrap gate 미통과 |
| 목적별 라우팅 구간 | qwidth, coverage, gap, component spread별로 후보를 다르게 적용하는 기준 | HCOEF22에서 validation/0604 개선 신호는 있으나 fixed test 안정성 부족 |
| 신뢰도/범위 tier | quantile width와 유사 표본 수로 예측 신뢰도와 가격 범위 폭을 나누는 기준 | 점 예측 후보가 아니라 서비스 표시 정책 후보로 유지 |
| 남은 오차 위험 구간 | HCOEF23에서 validation 기준으로 반복 확인된 큰 오차 구간 | `qwidth_extreme`, `gap_020_plus`, `n_10_19`, `spread_extreme`을 HCOEF24~38 우선 보정/검증 축으로 사용 |
| 후보 간 gap | HCOEF 안정 후보와 PP-V8/SVC component의 예측 차이 | gap이 클수록 남은 오차 크기가 커지는 방향이므로 강한 후보 교체보다 보수적 shrink/fallback이 필요 |
| 위험 완화 기준가 | 유사 작품 기준가를 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가 | HCOEF24에서 MdAPE/MAPE 개선 신호는 있으나 p95 guard 미통과 |
| 보수적 guard 계수 | 위험 구간에서 Huber 보정 이동폭을 줄이는 계수 | HCOEF25에서 MAPE/MdAPE 개선 신호는 유지됐지만 p95 병목은 계속 남음 |
| low-risk hard fallback | 위험 구간은 기준 후보를 유지하고 안전 구간에만 후보 이동분을 적용하는 정책 | HCOEF26에서 fixed p95 방어 신호를 확인했지만 HCOEF27 반복 검증 기준은 미통과 |
| 반복 split/artist holdout | 후보를 한 번의 test가 아니라 여러 표본과 작가 단위 분리 표본에서 다시 확인하는 검증 방식 | HCOEF27에서 HCOEF26 상위 후보의 운영 후보 승격 근거가 부족함을 확인 |
| Huber risk model | 현재 안정 후보의 절대 로그 오차를 Huber로 예측하는 선형 위험도 모델 | HCOEF28에서 `quantile_width`, 후보 간 gap, 작가 fallback이 큰 오차 위험 증가 방향임을 확인 |
| risk-aware shrinkage | 위험도가 높을수록 후보 이동폭을 `hcoef_stable` 쪽으로 줄이는 보정 방식 | HCOEF28에서 fixed 개선 후보는 있었지만 반복 검증 기준을 통과하지 못해 점 예측 후보로는 보류 |
| OOF Huber meta residual | `actual_log - hcoef_stable` 잔차를 component delta와 risk 피처로 직접 학습하는 방식 | HCOEF29에서 OOF 반복 신호는 강했지만 fixed MdAPE/p95 악화로 운영 후보 보류 |
| component delta | 각 후보가 `hcoef_stable`보다 높게/낮게 보는 정도 | HCOEF29에서 Huber 계수 해석은 가능하지만, 강한 잔차 추종은 fixed 일반화가 약함 |
| validation-consensus segment gate | validation row OOF와 validation artist OOF에서 동시에 개선된 segment에만 후보 이동을 허용하는 방식 | HCOEF30에서 반복 안정성은 강해졌지만 fixed p95 guard 미통과 |
| 방향 일치 미세 보정 | 안정 후보의 잔차 방향과 source 후보 이동 방향이 같은 구간에만 아주 작은 보정을 허용하는 방식 | HCOEF31에서 MdAPE/MAPE는 소폭 개선됐지만 fixed p95 guard와 repeated all3 기준 미통과 |
| ultra-micro p95-first 보정 | p95가 나빠지지 않는 validation segment에서만 weight/cap을 더 작게 적용하는 방식 | HCOEF32에서 fixed p95는 소폭 개선됐지만 repeated all3 부족으로 추가 검증 후보 |
| 확장 반복 검증 | 새 후보를 만들지 않고 같은 후보를 row/artist split 비율을 바꿔 더 많이 반복 확인하는 방식 | HCOEF33에서 HCOEF32 핵심 후보의 fixed/0604 개선은 유지됐지만 repeated all3가 `0.2785`로 낮아 운영 후보 승격 근거 부족 |
| segment rule | `svc_group_level=artist & gap_band=gap_003_005`, `qwidth_extreme`, `n_10_19` 같은 적용 조건 | 개선 구간을 설명하는 데는 유효하지만 현재는 점 예측 후보 교체보다 위험도/신뢰도 정책에 더 적합 |

## 41. 최종 판단

- Warm 개선 후보는 `hcoef2_size_reliability_cap005_s050`로 유지.
- 이 후보는 기존 Warm 1순위 대비 fixed test에서 MdAPE, MAPE, p95_APE가 모두 개선됨.
- 이 후보는 HCOEF11 확장 검증에서 row OOF와 artist OOF 80회 모두 개선 방향이 안정적임.
- Bootstrap 기준으로는 MAPE/RMSE 개선은 강하고 MdAPE/p95는 split 민감도가 남아 있으므로, 운영 반영 전 최신 라벨 스트레스 테스트가 필요함.
- HCOEF12에서 저장 모델 재로딩 재현성은 확인됐으므로, 연구 산출물 기준의 재현성 요건은 충족함.
- HCOEF13에서 남은 오차 원인은 기준가 표본 수/IQR/gap 구간으로 좁혀졌으므로, 다음 실험은 전체 모델 교체가 아니라 위험 구간 한정 보정으로 진행하는 것이 맞음.
- HCOEF14에서 위험 구간 한정 보정은 반복 OOF gate를 통과하지 못했으므로, 같은 유형의 보정을 운영 후보로 승격하지 않음.
- HCOEF15에서 운영 PP-V8/service primary component가 0604에서 MdAPE/MAPE/p95 균형상 가장 강했지만, OOF/fixed test 후보 선택 절차를 거치지 않았으므로 바로 운영 후보로 교체하지 않음.
- HCOEF16에서 PP-V8/service component를 OOF 기준으로 재검증했지만 fixed test p95 guard와 artist OOF 안정성 기준을 통과하지 못했으므로 새 후보로 채택하지 않음.
- HCOEF17에서 PP-V8 제한 이동 정책을 검증했지만 validation/bootstrap 기준을 통과한 후보가 없으므로 새 후보로 채택하지 않음.
- HCOEF18에서 quantile width risk guard를 검증했지만 validation/bootstrap 기준을 통과한 후보가 없으므로 새 후보로 채택하지 않음.
- HCOEF19에서 연구 산출물과 운영 v0.1 산출물의 Warm component/formula/필수 피처 schema가 일치함을 확인했으므로, 다음 실험은 피처 파이프라인 수정이 아니라 성능/신뢰도 정책 자체에 집중할 수 있음.
- HCOEF20에서 운영 component 기반 저차원 Huber/Ridge 후보를 검증했지만 fixed test p95 guard와 bootstrap all3 gate를 통과하지 못했으므로 새 점 예측 후보로 채택하지 않음.
- HCOEF20에서 quantile width 기반 신뢰도 tier는 점 예측 교체 근거가 아니라 가격 범위/신뢰도 표시 정책 후보로 유지함.
- HCOEF21에서 가변 SVC:PP-V8 기준가와 신뢰도별 Huber residual 후보를 검증했지만 fixed test p95 guard와 bootstrap all3 gate를 통과하지 못했으므로 새 점 예측 후보로 채택하지 않음.
- HCOEF22에서 목적별 라우팅을 검증했지만 fixed test MdAPE/p95가 악화되므로 새 점 예측 후보로 채택하지 않음.
- HCOEF22의 신뢰도/범위 tier는 high/low 위험도 분리력이 있으므로 서비스 표시 정책 후보로 유지함.
- HCOEF23은 새 점 예측 후보가 아니라 다음 실험의 원인 근거임.
- HCOEF23에서 확인된 위험 구간은 기존 HCOEF13의 원인 진단과 방향이 맞고, 특히 quantile width와 후보 간 gap이 큰 구간은 단순 라우팅보다 보수적 기준가 shrink가 필요함.
- HCOEF24에서 위험 완화 기준가를 만들었지만 fixed p95 guard를 통과하지 못했으므로 새 점 예측 후보로 채택하지 않음.
- HCOEF25에서 더 작은 cap과 conservative/no-extreme guard를 적용했지만 p95가 계속 소폭 악화되어 새 점 예측 후보로 채택하지 않음.
- HCOEF26에서 low-risk hard fallback을 적용하자 fixed p95는 `hcoef_stable`과 동일하게 방어되고 MdAPE/MAPE는 소폭 개선됨.
- HCOEF27에서 HCOEF26 후보를 반복 split/artist holdout으로 재검증했지만 repeated any2/all3 기준을 통과하지 못했으므로 운영 기본 후보 즉시 채택은 보류함.
- HCOEF27에서 direct guarded 후보는 반복 OOF 개선 확률이 더 높았지만 fixed test MdAPE가 악화되어 연구 후보로만 유지함.
- HCOEF28에서 Huber risk model로 위험도를 예측해 후보 이동폭을 줄였지만, 대표 fixed 후보의 repeated min any2/all3가 `0.394/0.086`에 그쳐 새 운영 후보로 채택하지 않음.
- HCOEF28 direct guarded shrink 후보는 repeated min any2가 `0.764`까지 나오지만 fixed MdAPE가 `0.1410`으로 악화되어 MAPE 목적 연구 후보로만 유지함.
- HCOEF29에서 OOF Huber meta residual 후보는 repeated min any2가 `0.928`까지 올라갔지만 fixed MdAPE `0.1442`, p95 `0.8081`로 기준보다 악화되어 새 운영 후보로 채택하지 않음.
- HCOEF30에서 validation-consensus segment gate 후보는 repeated min any2/all3가 `1.000/0.960`까지 올라갔지만 fixed test `0.1402/0.2700/0.8081`로 MdAPE/p95가 악화되어 새 운영 후보로 채택하지 않음.
- HCOEF30 p95 근접 후보 `hcoef30_s01_all3_top5_w0p5`도 fixed test `0.1387/0.2713/0.8072`로 p95가 기준 `0.8064`보다 근소하게 높아 미채택.
- HCOEF31에서 방향 일치와 작은 cap을 적용하자 fixed test MdAPE/MAPE는 소폭 개선됐지만 p95가 `0.8070` 또는 `0.8066`으로 기준 `0.8064`보다 근소하게 높아 미채택.
- HCOEF31 repeated min any2는 `0.88~0.90` 수준이나 repeated min all3는 `0.39~0.41` 수준이므로 안정 후보 승격 근거가 부족함.
- HCOEF32는 fixed test `0.1388/0.2729/0.8062`로 MAPE/p95/RMSE를 아주 작게 개선했지만 repeated min all3가 `0.306`으로 부족해 운영 후보 즉시 채택은 보류함.
- HCOEF33에서 HCOEF32 핵심 후보를 row/artist 확장 반복 검증으로 재확인했지만 repeated min any2/all3가 `0.8085/0.2785`에 그쳐 운영 후보 승격 기준을 통과하지 못함.
- HCOEF24~38 결과상 Warm Huber는 MdAPE/MAPE를 더 낮출 수 있는 여지가 있지만, 현재 데이터에서는 p95 방어와 fixed/generalization 안정성이 기준 후보 교체의 병목임.
- loose 기준가 Huber는 대표 오차 개선 잠재력이 크므로 버리지 않음.
- 다만 loose 기준가 Huber는 p95_APE 방어가 부족하므로 현재 기본 후보로 채택하지 않음.
- capped blend는 목적별 후보로 남길 수 있으나, 현재 기준으로 운영 후보 승격은 보류.
- 조건부 routing은 p95 방어에는 성공했지만 성능 이득이 작아 운영 후보 승격은 보류.
- 면적단가 기준가 직접 잔차 피처는 MdAPE/MAPE 개선 신호가 있으나 p95 악화로 운영 후보 승격은 보류.
- segmented cap/strength는 HCOEF3보다 성능이 나빠져 탈락.
- quantile width는 점 예측 이동보다 가격 범위/신뢰도/risk 표시용 보조 피처로 유지.
- 가변 기준가 신뢰도 피처는 점 예측 기본 후보가 아니라 설명 가능한 연구 후보 또는 향후 목적별 MAPE 후보로 유지.
- 목적별 라우팅은 validation/0604에만 맞을 위험이 있으므로 현재 기본 후보로 쓰지 않음.
- low-risk hard fallback, OOF Huber meta residual, validation-consensus segment gate, 방향 일치 미세 보정, ultra-micro p95-first 보정, 기준가 재탐색, low-risk routing, stricter routing은 각각 fixed 또는 OOF/repeated에서는 강점이 있지만, HCOEF27~HCOEF38 기준으로 운영 후보 승격 기준을 완전히 통과하지 못했음.

## 42. 다음 보정 방향

- 조건부 routing과 직접 잔차 피처는 모두 p95 방어가 핵심 병목임.
- segmented Huber 계수 실험에서도 HCOEF3보다 나은 후보가 나오지 않았음.
- HCOEF11에서 반복 횟수 확대 재검증은 완료됨.
- HCOEF12에서 운영 전 실험 패키징 감사는 완료됨.
- HCOEF13에서 작품별 큰 오차 원인 진단은 완료됨.
- HCOEF14에서 위험 구간 한정 shrinkage/routing/cap-strength OOF 검증은 완료됐고, 새 후보는 채택하지 않음.
- HCOEF15에서 최신 라벨 stress test는 완료됐고, PP-V8 운영 component를 OOF 후보로 검토할 근거가 생겼음.
- HCOEF16에서 PP-V8 운영 component의 OOF 재검증은 완료됐고, 현재 기준으로 새 후보 채택은 보류함.
- HCOEF17에서 PP-V8 제한 이동 정책도 완료됐고, 현재 기준으로 새 후보 채택은 보류함.
- HCOEF18에서 quantile width risk guard도 완료됐고, 현재 기준으로 새 후보 채택은 보류함.
- HCOEF19에서 서비스 feature pipeline 재현성 감사가 통과했고 HCOEF20~HCOEF38에서 저차원 계수/가변 기준가/목적별 라우팅/남은 오차 원인 분석/위험 완화 기준가/보수적 cap guard/low-risk fallback/반복 split 재검증/risk Huber shrinkage/OOF Huber meta residual 계수 결합/validation-consensus segment gate/p95-neutral 방향 일치 미세 보정/ultra-micro p95-first 보정/기준가 재탐색/low-risk routing/확장 반복 검증/stricter routing을 완료함.
- HCOEF26의 p95 hard fallback은 fixed test에서는 작동했지만 HCOEF27 반복 split/artist holdout과 HCOEF28 risk Huber shrinkage 기준을 통과하지 못했고, HCOEF29의 OOF meta residual, HCOEF30의 validation-consensus segment gate, HCOEF31의 방향 일치 미세 보정, HCOEF32의 ultra-micro p95-first 보정, HCOEF33의 확장 반복 검증은 validation/반복 OOF에서는 일부 강점이 있지만 fixed confirmation 또는 repeated all3 기준을 통과하지 못함.
- 같은 component를 더 세밀하게 계수화하거나 segment gate를 더 쪼개는 방식만으로는 운영 후보 승격 가능성이 낮으므로, 다음은 점 예측 이동보다 가격 범위/신뢰도/수동 검수 정책으로 위험 신호를 분리하는 방향이 더 타당함.
- fixed p95를 더 낮추려면 점 예측 후보를 계속 복잡하게 하는 것보다 p95 전용 risk 모델, quantile 위험도, 가격 범위/신뢰도 정책과 결합하는 것이 적절함.
- 면적단가 기준가는 버리지 않고, HCOEF 기본 후보가 아니라 별도 MAPE 목적 후보나 리포트용 해석 피처로 유지하는 것이 적절함.
- p95를 더 줄이려면 HCOEF 내부 세분화보다 별도 p95/risk 모델, quantile 위험도, 작가 메타 방어 후보와 결합하는 방향이 더 적절함.
- 운영 반영 전에는 `hcoef2_size_reliability_cap005_s050`를 재현 가능한 v0.1 개선 후보 패키지로 유지하고, PP-V8/service primary component는 HCOEF16/HCOEF17 결과 기준으로 기본 후보 승격을 보류하는 것이 맞음.
- 다음 HCOEF 계열은 점 예측 초미세 이동을 반복하기보다 기준가 생성 방식 자체를 다시 만들거나, p95/risk 전용 모델을 가격 범위/신뢰도 정책으로 분리하거나, 현재 component와 독립적인 새 피처 신호를 추가하는 방향이 맞음.

## 43. 주요 산출물

- `experiments/track6/PP-HCOEF3_warm_huber_residual_repeated_validation/reports/result_report.md`
- `experiments/track6/PP-HCOEF4_warm_basis_generation_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF5_warm_basis_hcoef_blend_repeated_validation/reports/result_report.md`
- `experiments/track6/PP-HCOEF6_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF7_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF8_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF9_warm_huber_risk_gated_basis_blend/reports/result_report.md`
- `experiments/track6/PP-HCOEF10_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF11_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF12_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF13_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF14_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF3_warm_huber_residual_repeated_validation/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF4_warm_basis_generation_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF5_warm_basis_hcoef_blend_repeated_validation/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF6_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF7_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF8_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF9_warm_huber_risk_gated_basis_blend/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF10_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF11_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF12_warm_huber_price_basis_coefficient_refinement/artifacts/operational_candidate_manifest.json`
- `experiments/track6/PP-HCOEF13_warm_huber_price_basis_coefficient_refinement/outputs/risk_segment_summary.csv`
- `experiments/track6/PP-HCOEF13_warm_huber_price_basis_coefficient_refinement/outputs/next_experiment_candidates.csv`
- `experiments/track6/PP-HCOEF14_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF14_warm_huber_price_basis_coefficient_refinement/outputs/segment_correction_map.csv`
- `experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/outputs/service_vs_hcoef_gap_analysis.csv`
- `experiments/track6/PP-HCOEF15_warm_huber_price_basis_coefficient_refinement/outputs/actual_price_join_audit.csv`
- `experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF16_warm_huber_price_basis_coefficient_refinement/outputs/input_component_audit.csv`
- `experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/outputs/policy_map.csv`
- `experiments/track6/PP-HCOEF17_warm_huber_price_basis_coefficient_refinement/outputs/service_feature_gap_audit.csv`
- `experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/outputs/policy_map.csv`
- `experiments/track6/PP-HCOEF18_warm_huber_price_basis_coefficient_refinement/outputs/quantile_feature_audit.csv`
- `experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/outputs/component_reconciliation.csv`
- `experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/outputs/formula_checks.csv`
- `experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/outputs/feature_pipeline_audit.csv`
- `experiments/track6/PP-HCOEF19_warm_huber_price_basis_coefficient_refinement/outputs/policy_map.csv`
- `experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/outputs/range_confidence_policy.csv`
- `experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/outputs/adaptive_weight_summary.csv`
- `experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF22_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF22_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF22_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF22_warm_huber_price_basis_coefficient_refinement/outputs/segment_policy_selection.csv`
- `experiments/track6/PP-HCOEF22_warm_huber_price_basis_coefficient_refinement/outputs/range_confidence_policy.csv`
- `experiments/track6/PP-HCOEF22_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF23_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF23_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF23_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF23_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF23_warm_huber_price_basis_coefficient_refinement/outputs/risk_segments.csv`
- `experiments/track6/PP-HCOEF23_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF23_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF24_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF24_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF24_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF24_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF24_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF24_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF24_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF25_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF25_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF25_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF25_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF25_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF25_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF25_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/outputs/policy_map.csv`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/outputs/mask_coverage_summary.csv`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF26_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF27_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF27_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF27_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF27_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF27_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF27_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF27_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF28_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF28_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF28_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF28_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF28_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF28_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF28_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF28_warm_huber_price_basis_coefficient_refinement/outputs/risk_model_thresholds.csv`
- `experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF29_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/outputs/consensus_rules.csv`
- `experiments/track6/PP-HCOEF30_warm_huber_price_basis_coefficient_refinement/outputs/segment_rule_metrics.csv`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/outputs/consensus_rules.csv`
- `experiments/track6/PP-HCOEF31_warm_huber_price_basis_coefficient_refinement/outputs/segment_rule_metrics.csv`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/outputs/consensus_rules.csv`
- `experiments/track6/PP-HCOEF32_warm_huber_price_basis_coefficient_refinement/outputs/segment_rule_metrics.csv`
- `experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF33_warm_huber_price_basis_coefficient_refinement/outputs/segment_impact.csv`
- `experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF34_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF35_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/outputs/policy_map.csv`
- `experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF36_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/outputs/policy_map.csv`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/outputs/repeated_iteration_metrics.csv`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF37_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/reports/result_report.md`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/outputs/metrics.csv`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/outputs/candidate_predictions.csv`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/outputs/feature_coefficients.csv`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/outputs/policy_map.csv`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/outputs/residual_analysis.csv`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/outputs/repeated_validation_summary.csv`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/outputs/bootstrap_or_repeated_split_summary.csv`
- `experiments/track6/PP-HCOEF38_warm_huber_price_basis_coefficient_refinement/outputs/selected_candidates.csv`
