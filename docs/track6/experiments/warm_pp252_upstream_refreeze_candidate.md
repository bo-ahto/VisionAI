# Warm PP252 상류 재동결 후보 감사

- 작성일: 2026-06-12T14:38:35
- 목적: 보고서 기준 Warm 최종 모델을 raw 입력 서비스로 승격하기 위해 저장 가능한 상류 모델 범위 확인
- 결론: 방향 분류와 Huber 잔차 보정은 full-fit 모델로 저장 가능. PP252 기준 후보값과 안정 후보값은 아직 이전 후보 생성 경로의 raw adapter가 필요

## 1. 저장한 후보 아티팩트

| 구분 | 파일 | 상태 |
|---|---|---|
| 방향 분류 모델 | `models/track6/warm_pp252_upstream_refreeze_candidate/artifacts/direction_hist_gbc_35_seed17_fullfit.joblib` | 저장 완료 |
| Huber 잔차 모델 | `models/track6/warm_pp252_upstream_refreeze_candidate/artifacts/huber_residual_epsilon1p15_fullfit.joblib` | 저장 완료 |
| 피처 스키마 | `models/track6/warm_pp252_upstream_refreeze_candidate/artifacts/feature_schema.json` | 저장 완료 |
| 입력 재생성 CSV | `models/track6/warm_pp252_upstream_refreeze_candidate/artifacts/pp252_refreeze_candidate_pp258_input.csv` | 저장 완료 |

## 2. 원본 PP258 입력 대비 차이

| 항목 | 구간 | n | 최대 차이 | 평균 차이 | p95 차이 | 1e-12 일치 |
|---|---|---:|---:|---:|---:|---|
| pp252_log | all | 1126 | 0.0 | 0.0 | 0.0 | 예 |
| pp252_log | validation_oof | 519 | 0.0 | 0.0 | 0.0 | 예 |
| pp252_log | test | 607 | 0.0 | 0.0 | 0.0 | 예 |
| pp252_stability_log | all | 1126 | 0.0 | 0.0 | 0.0 | 예 |
| pp252_stability_log | validation_oof | 519 | 0.0 | 0.0 | 0.0 | 예 |
| pp252_stability_log | test | 607 | 0.0 | 0.0 | 0.0 | 예 |
| prob_hist35_pp252 | all | 1126 | 0.2626488930083057 | 0.031089055012859267 | 0.1371647120386892 | 아니오 |
| prob_hist35_pp252 | validation_oof | 519 | 0.2626488930083057 | 0.06744947195468116 | 0.17732238757752322 | 아니오 |
| prob_hist35_pp252 | test | 607 | 5.551115123125783e-17 | 1.4449360617032515e-17 | 5.551115123125783e-17 | 예 |
| resid_huber_pp252 | all | 1126 | 0.51915645793096 | 0.012178102777304588 | 0.0435088179567422 | 아니오 |
| resid_huber_pp252 | validation_oof | 519 | 0.51915645793096 | 0.026421086179662694 | 0.08180480339287749 | 아니오 |
| resid_huber_pp252 | test | 607 | 9.8879238130678e-17 | 4.5696754901600844e-17 | 9.521463478767696e-17 | 예 |
| pp252_log | packaged_all | 1126 | 0.0 | 0.0 | 0.0 | 예 |
| pp252_log | packaged_test | 607 | 0.0 | 0.0 | 0.0 | 예 |
| pp252_stability_log | packaged_all | 1126 | 0.0 | 0.0 | 0.0 | 예 |
| pp252_stability_log | packaged_test | 607 | 0.0 | 0.0 | 0.0 | 예 |
| prob_hist35_pp252 | packaged_all | 1126 | 0.2626488930083057 | 0.031089055012859267 | 0.1371647120386892 | 아니오 |
| prob_hist35_pp252 | packaged_test | 607 | 5.551115123125783e-17 | 1.4449360617032515e-17 | 5.551115123125783e-17 | 예 |
| resid_huber_pp252 | packaged_all | 1126 | 0.51915645793096 | 0.012178102777304588 | 0.0435088179567422 | 아니오 |
| resid_huber_pp252 | packaged_test | 607 | 9.8879238130678e-17 | 4.5696754901600844e-17 | 9.521463478767696e-17 | 예 |

## 3. PP258 최종층 재계산 결과

| 항목 | 값 |
|---|---:|
| test n | 607 |
| MdAPE | 0.140976400627 |
| MAPE | 0.269888195779 |
| p95 APE | 0.807324707291 |
| RMSE log | 0.397453829551 |
| 저장 결과 대비 최대 가격 차이 | 1.4901161193847656e-08 |
| 저장 결과 대비 최대 로그가격 차이 | 3.552713678800501e-15 |

## 4. 운영 adapter 승격 판단

- 승격 가능: `prob_hist35_pp252`, `resid_huber_pp252`를 만드는 방향 분류/Huber 잔차 모델
- 추가 필요: `pp252_log`, `pp252_stability_log`를 원시 입력에서 만드는 직전 후보 생성 adapter
- 현재 의미: Warm 최종층 직전의 일부 상류 모델은 저장 가능 상태로 전환됨. 다만 전체 exact raw adapter는 아직 PP252 기준 후보 생성 경로가 남아 있음
