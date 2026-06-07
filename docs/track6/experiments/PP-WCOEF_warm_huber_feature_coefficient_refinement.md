# PP-WCOEF Warm Huber 계수 세분화 및 잔차 보정 실험

- 작성일: 2026-06-06 02:07
- 목적: Huber 선형 모델의 피처별 계수를 더 세밀하게 나누거나 현재 Warm 1순위 후보 위에 약한 잔차 보정을 적용했을 때 추가 개선이 가능한지 확인
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 기준 validation MdAPE/MAPE/p95: `0.1305` / `0.2110` / `0.6580`
- 기준 test MdAPE/MAPE/p95: `0.1405` / `0.2748` / `0.8331`

## 0. 실행 결론

- PP-WCOEF1~4 직접 Huber 재학습 후보는 기존 Huber 기준선보다 일부 개선됐지만 현재 Warm 1순위 후보를 대체하지 못함
- 직접 Huber 후보 중 가장 강한 축은 PP-WCOEF3 유사 작품 기반 가격 피처 신뢰도별 계수 조정
- PP-WCOEF3 test MdAPE는 `0.1532`로 기존 Huber test MdAPE `0.2274`보다 개선됐지만 현재 Warm 1순위 `0.1405`에는 미달
- PP-WCOEF5 약한 잔차 보정은 test 일부 후보에서 MdAPE `0.1353`, p95_APE `0.8291`까지 개선 신호 확인
- 다만 validation 선택 후보와 test 최상위 후보가 완전히 일치하지 않고, bootstrap에서 MAPE 개선 확률이 낮아 즉시 v0.1 반영은 보류
- 현재 판단: v0.1 기본 Warm 후보는 유지, PP-WCOEF5는 추가 split/OOF 재검증 후보로 승격

## 1. 실험 구성

- PP-WCOEF1: 크기 구간별 Huber 계수 세분화
- PP-WCOEF2: 재료/지지체와 크기 조합 계수 세분화
- PP-WCOEF3: 유사 작품 기반 가격 피처의 표본 수/분산 신뢰도별 계수 조정
- PP-WCOEF4: 작가 기준선과 작가 메타 구간별 계수 조정
- PP-WCOEF5: 현재 Warm 1순위 후보 위 약한 Huber 잔차 보정
- PP-WCOEF6: 선택 후보의 row/artist bootstrap 안정성 검증

## 2. Test 상위 후보

| 순위 | 세부 실험 | 후보 | 계열 | 방식 | MdAPE | MAPE | p95_APE | RMSE_log |
|---:|---|---|---|---|---:|---:|---:|---:|
| 1 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p08_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1353 | 0.2751 | 0.8291 | 0.3993 |
| 2 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p08_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1353 | 0.2751 | 0.8291 | 0.3993 |
| 3 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p03_s0p75` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1354 | 0.2755 | 0.8289 | 0.3995 |
| 4 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p03_s0p75` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1355 | 0.2757 | 0.8289 | 0.3996 |
| 5 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p05_s0p5` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1361 | 0.2757 | 0.8288 | 0.3995 |
| 6 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p05_s0p5` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1362 | 0.2756 | 0.8288 | 0.3995 |
| 7 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p05_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1367 | 0.2749 | 0.8328 | 0.3994 |
| 8 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p05_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1367 | 0.2749 | 0.8328 | 0.3994 |
| 9 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p12_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1367 | 0.2755 | 0.8285 | 0.3993 |
| 10 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p03_s0p5` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1375 | 0.2751 | 0.8311 | 0.3994 |
| 11 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p03_s0p5` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1375 | 0.2751 | 0.8311 | 0.3995 |
| 12 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p03_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1377 | 0.2748 | 0.8293 | 0.3995 |
| 13 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p03_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1377 | 0.2748 | 0.8293 | 0.3995 |
| 14 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p12_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1378 | 0.2753 | 0.8285 | 0.3992 |
| 15 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p03_s1p0` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1378 | 0.2764 | 0.8285 | 0.3998 |
| 16 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p03_s1p0` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1388 | 0.2762 | 0.8285 | 0.3998 |
| 17 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p08_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1395 | 0.2741 | 0.8073 | 0.3987 |
| 18 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p03_s0p5` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1396 | 0.2744 | 0.8114 | 0.3989 |
| 19 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p03_s0p5` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1397 | 0.2744 | 0.8114 | 0.3990 |
| 20 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p05_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1400 | 0.2743 | 0.8143 | 0.3989 |
| 21 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p12_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1400 | 0.2743 | 0.8073 | 0.3986 |
| 22 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p08_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1402 | 0.2741 | 0.8073 | 0.3987 |
| 23 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p05_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1403 | 0.2743 | 0.8144 | 0.3990 |
| 24 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p03_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1403 | 0.2745 | 0.8207 | 0.3992 |
| 25 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p05_s0p5` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1404 | 0.2744 | 0.8184 | 0.3985 |
| 26 | REFERENCE | `blend_svcnum_ppv8_wsvc_0.70` | reference | reference_prediction | 0.1405 | 0.2748 | 0.8331 | 0.3996 |
| 27 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p05_s0p5` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1405 | 0.2744 | 0.8184 | 0.3986 |
| 28 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p12_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1405 | 0.2744 | 0.8073 | 0.3987 |
| 29 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p03_s1p0` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1405 | 0.2748 | 0.8252 | 0.3988 |
| 30 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p03_s0p25` | weak_residual_huber_correction | validation_calibrated_residual_huber | 0.1406 | 0.2745 | 0.8207 | 0.3992 |

## 3. Validation 기준 선택 후보

| 선택 기준 | 세부 실험 | 후보 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| MdAPE 우선 | REFERENCE | `fallback_numeric` | 0.1212 | 0.2170 | 0.6502 | 0.1528 | 0.2956 | 0.9694 |
| MAPE 우선 + MdAPE 5% 이내 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p12_s0p5` | 0.1232 | 0.2088 | 0.6390 | 0.1464 | 0.2760 | 0.8238 |
| p95 우선 + MdAPE 8% 이내 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p05_s1p0` | 0.1281 | 0.2109 | 0.6254 | 0.1469 | 0.2789 | 0.8273 |
| 균형 점수 | PP-WCOEF5 | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p03_s0p75` | 0.1233 | 0.2090 | 0.6346 | 0.1411 | 0.2745 | 0.8153 |

## 4. Bootstrap 안정성 요약

| 표본 추출 방식 | 후보 | MdAPE 평균 차이 | MdAPE 개선 확률 | MAPE 개선 확률 | p95 개선 확률 |
|---|---|---:|---:|---:|---:|
| artist_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p08_s0p25` | -0.00374 | 0.763 | 0.390 | 0.713 |
| artist_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p08_s0p25` | -0.00362 | 0.737 | 0.413 | 0.720 |
| artist_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p03_s0p75` | -0.00304 | 0.697 | 0.293 | 0.710 |
| artist_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p03_s0p75` | -0.00300 | 0.690 | 0.240 | 0.700 |
| artist_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p05_s0p5` | -0.00284 | 0.703 | 0.267 | 0.713 |
| artist_bootstrap | `blend_svcnum_ppv8_wsvc_0.70` | 0.00000 | 0.000 | 0.000 | 0.000 |
| artist_bootstrap | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p03_s0p75` | 0.00042 | 0.493 | 0.597 | 0.683 |
| artist_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p05_s1p0` | 0.00552 | 0.203 | 0.070 | 0.697 |
| artist_bootstrap | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p12_s0p5` | 0.00635 | 0.147 | 0.347 | 0.643 |
| artist_bootstrap | `fallback_numeric` | 0.01019 | 0.080 | 0.003 | 0.030 |
| row_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p08_s0p25` | -0.00448 | 0.777 | 0.370 | 0.683 |
| row_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p08_s0p25` | -0.00427 | 0.777 | 0.397 | 0.687 |
| row_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p03_s0p75` | -0.00399 | 0.743 | 0.180 | 0.687 |
| row_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p03_s0p75` | -0.00395 | 0.743 | 0.233 | 0.690 |
| row_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p05_s0p5` | -0.00380 | 0.760 | 0.207 | 0.690 |
| row_bootstrap | `PP-WCOEF5_resid_pred_size_svc_alpha0p01_cap0p03_s0p75` | -0.00033 | 0.530 | 0.593 | 0.720 |
| row_bootstrap | `blend_svcnum_ppv8_wsvc_0.70` | 0.00000 | 0.000 | 0.000 | 0.000 |
| row_bootstrap | `PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p001_cap0p05_s1p0` | 0.00573 | 0.200 | 0.047 | 0.667 |
| row_bootstrap | `PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p12_s0p5` | 0.00612 | 0.127 | 0.300 | 0.643 |
| row_bootstrap | `fallback_numeric` | 0.00970 | 0.087 | 0.000 | 0.000 |

## 5. 해석 기준

- Huber 직접 재학습 후보가 좋아지면 피처 계수 구조를 더 세밀하게 두는 방향으로 후속 검증
- PP-WCOEF5가 좋아지면 현재 Warm 1순위 후보의 사후 보정값을 운영 후보로 분리해 추가 split 검증
- test 상위 후보라도 validation 선택 후보와 bootstrap 개선 확률이 낮으면 바로 반영하지 않음
- MdAPE, MAPE, p95_APE가 엇갈리면 대표 가격 후보와 큰 오차 방어 후보를 분리

## 6. 산출물

- `outputs/all_candidate_metrics.csv`
- `outputs/predictions.csv`
- `outputs/selected_validation_candidates.csv`
- `outputs/bootstrap_summary.csv`
- `outputs/bootstrap_samples.csv`
- `outputs/huber_coefficients_top.csv`
- `reports/result_report.md`
- `reports/result_report.html`
