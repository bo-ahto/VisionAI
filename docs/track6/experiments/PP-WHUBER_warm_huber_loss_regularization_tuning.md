# PP-WHUBER Warm Huber 손실/규제 특성 튜닝

- 작성일: 2026-06-06 16:22
- 목적: Huber의 이상치 처리 기준과 계수 규제를 조정해 Warm 성능 개선 여지를 확인
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 기준 validation MdAPE/MAPE/p95: `0.1305` / `0.2110` / `0.6580`
- 기준 test MdAPE/MAPE/p95: `0.1405` / `0.2748` / `0.8331`

## 0. 실행 결론

- 직접 Huber 재학습 계열은 현재 Warm 1순위 후보를 대체하지 못함
- Huber `epsilon`/`alpha` 직접 튜닝, 표본 가중치, 2-pass 이상치 재가중, 구간별 Huber 라우팅은 일부 validation 개선이 있었지만 test에서 MdAPE/MAPE/p95 균형이 약함
- 가장 의미 있는 개선은 현재 Warm 1순위 후보 위에 residual Huber를 약하게 적용한 PP-WHUBER5에서 발생
- MdAPE 우선 후보: `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p25`
- MdAPE 우선 후보 test 성능: MdAPE `0.1346`, MAPE `0.2745`, p95_APE `0.8387`
- 균형 후보: `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p08_s0p25`
- 균형 후보 test 성능: MdAPE `0.1353`, MAPE `0.2747`, p95_APE `0.8291`
- 판단: v0.1 운영 후보에 바로 반영하기보다 PP-WHUBER5 후보를 반복 split 또는 OOF 재검증 대상으로 승격

## 1. 실험 구성

- PP-WHUBER1: Huber `epsilon`/`alpha` 그리드
- PP-WHUBER2: 유사 작품 신뢰도/target tail 기반 표본 가중치
- PP-WHUBER3: 1차 Huber outlier를 낮은 가중치로 두는 2-pass Huber
- PP-WHUBER4: 유사 작품 신뢰도, 작가 이력량, 크기 구간별 별도 Huber 라우팅
- PP-WHUBER5: 현재 Warm 1순위 후보 위 residual Huber의 `epsilon` 튜닝
- PP-WHUBER6: row/artist bootstrap 안정성 검증

## 2. Test 상위 후보

| 순위 | 세부 실험 | 후보 | 계열 | MdAPE | MAPE | p95_APE | RMSE_log |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p25` | residual_huber_epsilon_tuning | 0.1346 | 0.2745 | 0.8387 | 0.3990 |
| 2 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p25` | residual_huber_epsilon_tuning | 0.1350 | 0.2745 | 0.8382 | 0.3990 |
| 3 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p08_s0p25` | residual_huber_epsilon_tuning | 0.1353 | 0.2747 | 0.8291 | 0.3991 |
| 4 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p01_cap0p08_s0p25` | residual_huber_epsilon_tuning | 0.1353 | 0.2747 | 0.8291 | 0.3991 |
| 5 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p02_s0p5` | residual_huber_epsilon_tuning | 0.1355 | 0.2744 | 0.8384 | 0.3992 |
| 6 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p05_s0p5` | residual_huber_epsilon_tuning | 0.1355 | 0.2747 | 0.8538 | 0.3990 |
| 7 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p15` | residual_huber_epsilon_tuning | 0.1357 | 0.2745 | 0.8368 | 0.3992 |
| 8 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p15` | residual_huber_epsilon_tuning | 0.1358 | 0.2745 | 0.8365 | 0.3992 |
| 9 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p05_s0p5` | residual_huber_epsilon_tuning | 0.1359 | 0.2747 | 0.8524 | 0.3990 |
| 10 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p01_cap0p05_s0p5` | residual_huber_epsilon_tuning | 0.1359 | 0.2751 | 0.8288 | 0.3992 |
| 11 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p02_s0p5` | residual_huber_epsilon_tuning | 0.1359 | 0.2745 | 0.8384 | 0.3992 |
| 12 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p01_cap0p02_s0p5` | residual_huber_epsilon_tuning | 0.1361 | 0.2747 | 0.8311 | 0.3993 |
| 13 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_svc_eps1.20_alpha0p001_cap0p08_s0p25` | residual_huber_epsilon_tuning | 0.1361 | 0.2743 | 0.8135 | 0.3989 |
| 14 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p05_s0p5` | residual_huber_epsilon_tuning | 0.1361 | 0.2750 | 0.8288 | 0.3991 |
| 15 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.05_alpha0p001_cap0p08_s0p25` | residual_huber_epsilon_tuning | 0.1361 | 0.2740 | 0.8152 | 0.3979 |
| 16 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.20_alpha0p001_cap0p08_s0p15` | residual_huber_epsilon_tuning | 0.1362 | 0.2744 | 0.8240 | 0.3990 |
| 17 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.20_alpha0p01_cap0p08_s0p15` | residual_huber_epsilon_tuning | 0.1362 | 0.2745 | 0.8260 | 0.3991 |
| 18 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p08_s0p15` | residual_huber_epsilon_tuning | 0.1362 | 0.2746 | 0.8266 | 0.3992 |
| 19 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p01_cap0p08_s0p15` | residual_huber_epsilon_tuning | 0.1362 | 0.2746 | 0.8274 | 0.3992 |
| 20 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p05_s0p25` | residual_huber_epsilon_tuning | 0.1362 | 0.2745 | 0.8389 | 0.3991 |
| 21 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p05_s0p25` | residual_huber_epsilon_tuning | 0.1362 | 0.2745 | 0.8392 | 0.3991 |
| 22 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.05_alpha0p01_cap0p08_s0p25` | residual_huber_epsilon_tuning | 0.1362 | 0.2738 | 0.8152 | 0.3978 |
| 23 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p03_s0p5` | residual_huber_epsilon_tuning | 0.1363 | 0.2744 | 0.8428 | 0.3990 |
| 24 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p03_s0p5` | residual_huber_epsilon_tuning | 0.1363 | 0.2745 | 0.8428 | 0.3991 |
| 25 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p01_cap0p03_s0p5` | residual_huber_epsilon_tuning | 0.1363 | 0.2748 | 0.8311 | 0.3993 |
| 26 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.05_alpha0p01_cap0p05_s0p25` | residual_huber_epsilon_tuning | 0.1367 | 0.2740 | 0.8180 | 0.3984 |
| 27 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p05_s0p25` | residual_huber_epsilon_tuning | 0.1367 | 0.2746 | 0.8325 | 0.3992 |
| 28 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p01_cap0p05_s0p25` | residual_huber_epsilon_tuning | 0.1367 | 0.2746 | 0.8328 | 0.3992 |
| 29 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.05_alpha0p001_cap0p08_s0p15` | residual_huber_epsilon_tuning | 0.1367 | 0.2741 | 0.8180 | 0.3985 |
| 30 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_svc_eps1.20_alpha0p01_cap0p08_s0p25` | residual_huber_epsilon_tuning | 0.1368 | 0.2743 | 0.8131 | 0.3989 |
| 31 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.05_alpha0p001_cap0p05_s0p25` | residual_huber_epsilon_tuning | 0.1370 | 0.2741 | 0.8182 | 0.3984 |
| 32 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.05_alpha0p01_cap0p08_s0p15` | residual_huber_epsilon_tuning | 0.1371 | 0.2741 | 0.8180 | 0.3984 |
| 33 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p02_s0p5` | residual_huber_epsilon_tuning | 0.1372 | 0.2747 | 0.8311 | 0.3993 |
| 34 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p03_s0p5` | residual_huber_epsilon_tuning | 0.1372 | 0.2748 | 0.8311 | 0.3992 |
| 35 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.05_alpha0p01_cap0p02_s0p5` | residual_huber_epsilon_tuning | 0.1374 | 0.2741 | 0.8212 | 0.3986 |

## 3. Validation 기준 선택 후보

| 선택 기준 | 세부 실험 | 후보 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| MdAPE 우선 | PP-WHUBER4 | `PP-WHUBER4_segment_size_bin_balanced_min250` | 0.1195 | 0.2493 | 0.7094 | 0.1459 | 0.2828 | 1.0596 |
| MAPE 우선 + MdAPE 5% 이내 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_svc_eps1.05_alpha0p01_cap0p08_s0p5` | 0.1280 | 0.2077 | 0.6521 | 0.1449 | 0.2747 | 0.8222 |
| p95 우선 + MdAPE 8% 이내 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p5` | 0.1320 | 0.2094 | 0.6304 | 0.1429 | 0.2754 | 0.8518 |
| 균형 점수 | PP-WHUBER5 | `PP-WHUBER5_resid_pred_size_svc_eps1.60_alpha0p001_cap0p05_s0p5` | 0.1242 | 0.2096 | 0.6366 | 0.1410 | 0.2751 | 0.8179 |

## 4. Bootstrap 안정성 요약

| 표본 추출 방식 | 후보 | MdAPE 평균 차이 | MdAPE 개선 확률 | MAPE 개선 확률 | p95 개선 확률 |
|---|---|---:|---:|---:|---:|
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p05_s0p5` | -0.00447 | 0.737 | 0.553 | 0.620 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p25` | -0.00427 | 0.777 | 0.617 | 0.633 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p25` | -0.00418 | 0.767 | 0.620 | 0.627 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p01_cap0p08_s0p25` | -0.00349 | 0.717 | 0.567 | 0.767 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p02_s0p5` | -0.00346 | 0.870 | 0.747 | 0.613 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p15` | -0.00342 | 0.843 | 0.717 | 0.613 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p08_s0p25` | -0.00342 | 0.717 | 0.577 | 0.787 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p15` | -0.00337 | 0.843 | 0.713 | 0.607 |
| artist_bootstrap | `blend_svcnum_ppv8_wsvc_0.70` | 0.00000 | 0.000 | 0.000 | 0.000 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p5` | 0.00000 | 0.523 | 0.410 | 0.623 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_svc_eps1.60_alpha0p001_cap0p05_s0p5` | 0.00214 | 0.360 | 0.433 | 0.693 |
| artist_bootstrap | `PP-WHUBER4_segment_size_bin_balanced_min250` | 0.00311 | 0.377 | 0.253 | 0.050 |
| artist_bootstrap | `PP-WHUBER5_resid_pred_size_svc_eps1.05_alpha0p01_cap0p08_s0p5` | 0.00433 | 0.237 | 0.510 | 0.737 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p05_s0p5` | -0.00531 | 0.773 | 0.527 | 0.570 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p25` | -0.00504 | 0.807 | 0.607 | 0.590 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p25` | -0.00497 | 0.803 | 0.610 | 0.587 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p08_s0p25` | -0.00437 | 0.777 | 0.540 | 0.763 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p01_cap0p08_s0p25` | -0.00437 | 0.783 | 0.533 | 0.747 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p15` | -0.00425 | 0.913 | 0.727 | 0.553 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p15` | -0.00420 | 0.897 | 0.727 | 0.553 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p02_s0p5` | -0.00407 | 0.897 | 0.737 | 0.567 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p01_cap0p08_s0p5` | -0.00021 | 0.557 | 0.367 | 0.580 |
| row_bootstrap | `blend_svcnum_ppv8_wsvc_0.70` | 0.00000 | 0.000 | 0.000 | 0.000 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_svc_eps1.60_alpha0p001_cap0p05_s0p5` | 0.00180 | 0.367 | 0.357 | 0.713 |
| row_bootstrap | `PP-WHUBER4_segment_size_bin_balanced_min250` | 0.00292 | 0.360 | 0.220 | 0.017 |
| row_bootstrap | `PP-WHUBER5_resid_pred_size_svc_eps1.05_alpha0p01_cap0p08_s0p5` | 0.00410 | 0.227 | 0.510 | 0.720 |

## 5. 해석 기준

- 직접 Huber가 개선되면 Huber 설정/가중치 자체를 v0.1 후속 후보로 검토
- residual Huber만 개선되면 기본 모델은 유지하고 사후 보정 후보로 분리
- validation 선택 후보와 test 상위 후보가 다르면 바로 반영하지 않고 추가 split 검증
- MAPE 개선 확률이 낮으면 대표 가격 후보가 아니라 큰 오차 방어 후보로 분리

## 6. 산출물

- `outputs/all_candidate_metrics.csv`
- `outputs/predictions.csv`
- `outputs/selected_validation_candidates.csv`
- `outputs/bootstrap_summary.csv`
- `outputs/bootstrap_samples.csv`
- `outputs/direct_huber_outlier_diagnostics.csv`
- `outputs/two_pass_diagnostics.csv`
