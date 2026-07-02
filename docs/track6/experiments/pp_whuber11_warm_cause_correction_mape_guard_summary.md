# PP-WHUBER11 Warm 원인 기반 보정 + MAPE guard + 과대예측 전용 cap

- 작성일: 2026-06-07 14:00
- 기준 Warm 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 가설: 과대예측 segment 한정 + 하향 전용 cap + MAPE guard로 MdAPE/p95를 낮추면서 MAPE를 악화시키지 않는 후보를 찾는다
- 누수 방지: 보정값은 validation 작가 holdout에서만 산출, test는 최종 확인 1회

## 1. 실행 결론

- 기준 후보 test MdAPE/MAPE/p95: `0.1405` / `0.2748` / `0.8331`
- MAPE guard 통과 validation 후보 수: 36 / 전체 36
- 채택 후보 test MdAPE/MAPE/p95: `0.1403` / `0.2744` / `0.8312`
- 채택 판정 후보: `PP-WHUBER11_guard_risk_pred_min20_cap0p05_s0p25_smooth20` → **보조 방어 후보 (MAPE 비악화 + 개선이 marginal, 단독 대표 교체는 보류)**
- MAPE 비악화: True / MdAPE 비악화: True / p95 개선: True
- 상대 개선: MdAPE -0.14% / p95 -0.23% (음수가 개선). 절대 개선폭이 작아 paired bootstrap 유의성 확인 전 대표 교체는 보류 권장

## 2. 설계 변경 요소 (PP-WHUBER10 대비)

- 과대예측 위험 segment(작가 기준선 약함)에만 보정 적용, 정상·과소예측 행 미접촉
- 하향 방향 보정만 적용(`clip(-cap, 0) * strength`)
- global fallback 제거(`risk_cause` level까지만), 표본 부족 segment는 보정 0
- validation MAPE 비악화 후보만 채택(MAPE guard)

## 3. 채택(MAPE guard 통과) 후보

| candidate | hierarchy | min_rows | cap | strength |
| --- | --- | --- | --- | --- |
| PP-WHUBER11_guard_risk_pred_min20_cap0p05_s0p25_smooth20 | risk_cause+pred_log_bin > risk_cause | 20 | 0.05 | 0.25 |
| PP-WHUBER11_guard_pred_svc_min20_cap0p05_s0p5_smooth20 | pred_log_bin+svc_reliability_bin > svc_reliability_bin | 20 | 0.05 | 0.5 |
| PP-WHUBER11_guard_works_pred_min8_cap0p05_s0p5_smooth20 | artist_works_bin+pred_log_bin > artist_works_bin | 8 | 0.05 | 0.5 |

## 4. Validation 작가 holdout 후보 요약

| candidate | hierarchy_name | cap | strength | mape_guard_pass | mean_delta_MdAPE | mean_delta_MAPE | mean_delta_p95_APE | improvement_probability_MdAPE | nonworse_probability_MAPE | improvement_probability_p95_APE | balanced_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-WHUBER11_guard_risk_pred_min20_cap0p05_s0p25_smooth20 | risk_pred | 0.05 | 0.25 | True | 0.00010737 | -0.00040002 | -0.0018949 | 0.125 | 1 | 1 | -0.00056637 |
| PP-WHUBER11_guard_risk_pred_min20_cap0p08_s0p25_smooth20 | risk_pred | 0.08 | 0.25 | True | 0.00011678 | -0.00041208 | -0.0018949 | 0.125 | 1 | 1 | -0.00056299 |
| PP-WHUBER11_guard_risk_pred_min20_cap0p12_s0p25_smooth20 | risk_pred | 0.12 | 0.25 | True | 0.00011678 | -0.00041208 | -0.0018949 | 0.125 | 1 | 1 | -0.00056299 |
| PP-WHUBER11_guard_pred_svc_min20_cap0p05_s0p5_smooth20 | pred_svc | 0.05 | 0.5 | True | 4.5668e-05 | -0.00020403 | -0.0017256 | 0.125 | 0.75 | 0.875 | -0.00048775 |
| PP-WHUBER11_guard_pred_svc_min8_cap0p05_s0p5_smooth20 | pred_svc | 0.05 | 0.5 | True | 4.5668e-05 | -0.00020403 | -0.0017256 | 0.125 | 0.75 | 0.875 | -0.00048775 |
| PP-WHUBER11_guard_pred_svc_min20_cap0p08_s0p5_smooth20 | pred_svc | 0.08 | 0.5 | True | 4.5668e-05 | -0.00019921 | -0.0017256 | 0.125 | 0.75 | 0.875 | -0.00048534 |
| PP-WHUBER11_guard_pred_svc_min20_cap0p12_s0p5_smooth20 | pred_svc | 0.12 | 0.5 | True | 4.5668e-05 | -0.00019921 | -0.0017256 | 0.125 | 0.75 | 0.875 | -0.00048534 |
| PP-WHUBER11_guard_pred_svc_min8_cap0p08_s0p5_smooth20 | pred_svc | 0.08 | 0.5 | True | 4.5668e-05 | -0.00019921 | -0.0017256 | 0.125 | 0.75 | 0.875 | -0.00048534 |
| PP-WHUBER11_guard_pred_svc_min8_cap0p12_s0p5_smooth20 | pred_svc | 0.12 | 0.5 | True | 4.5668e-05 | -0.00019921 | -0.0017256 | 0.125 | 0.75 | 0.875 | -0.00048534 |
| PP-WHUBER11_guard_pred_svc_min20_cap0p05_s0p25_smooth20 | pred_svc | 0.05 | 0.25 | True | 2.5092e-05 | -0.00011731 | -0.001407 | 0.125 | 0.875 | 0.875 | -0.00038531 |
| PP-WHUBER11_guard_pred_svc_min8_cap0p05_s0p25_smooth20 | pred_svc | 0.05 | 0.25 | True | 2.5092e-05 | -0.00011731 | -0.001407 | 0.125 | 0.875 | 0.875 | -0.00038531 |
| PP-WHUBER11_guard_pred_svc_min20_cap0p08_s0p25_smooth20 | pred_svc | 0.08 | 0.25 | True | 2.5092e-05 | -0.00011694 | -0.001407 | 0.125 | 0.875 | 0.875 | -0.00038512 |
| PP-WHUBER11_guard_pred_svc_min20_cap0p12_s0p25_smooth20 | pred_svc | 0.12 | 0.25 | True | 2.5092e-05 | -0.00011694 | -0.001407 | 0.125 | 0.875 | 0.875 | -0.00038512 |
| PP-WHUBER11_guard_pred_svc_min8_cap0p08_s0p25_smooth20 | pred_svc | 0.08 | 0.25 | True | 2.5092e-05 | -0.00011694 | -0.001407 | 0.125 | 0.875 | 0.875 | -0.00038512 |
| PP-WHUBER11_guard_pred_svc_min8_cap0p12_s0p25_smooth20 | pred_svc | 0.12 | 0.25 | True | 2.5092e-05 | -0.00011694 | -0.001407 | 0.125 | 0.875 | 0.875 | -0.00038512 |

## 5. Test 성능 비교

| candidate | role | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE | delta_MAPE | delta_p95_APE | corrected_row_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| blend_svcnum_ppv8_wsvc_0.70 | 현재 Warm 기준 조합 | 0.14048 | 0.2748 | 0.83307 | 0.39961 | 0 | 0 | 0 |  |
| PP-WHUBER11_guard_risk_pred_min20_cap0p05_s0p25_smooth20 | p95/MAPE 방어 [risk_pred] | 0.14029 | 0.27444 | 0.83119 | 0.39942 | -0.00019361 | -0.00036137 | -0.0018833 | 0.43822 |
| PP-WHUBER11_guard_pred_svc_min20_cap0p05_s0p5_smooth20 | p95/MAPE 방어 [pred_svc] | 0.13918 | 0.2744 | 0.82915 | 0.39951 | -0.0013039 | -0.0003941 | -0.0039203 | 0.28501 |
| PP-WHUBER11_guard_works_pred_min8_cap0p05_s0p5_smooth20 | p95/MAPE 방어 [works_pred] | 0.13979 | 0.27449 | 0.82905 | 0.39961 | -0.00069132 | -0.00030522 | -0.004023 | 0.37232 |

## 6. 원인군별 보정 효과 (test 진단)

| risk_cause | error_direction | error_severity | n | current_MdAPE | current_MAPE | current_p95_APE | median_residual_log | adjusted_MdAPE | adjusted_MAPE | adjusted_p95_APE | improved_row_rate | worsened_row_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 유사작품_적음+작가이력_적음 | 과대예측 | 극단오차 | 14 | 1.733 | 2.1691 | 4.3127 | -1.0044 | 1.733 | 2.168 | 4.3127 | 0 | 0 |
| 작가이력_표본_부족 | 과대예측 | 극단오차 | 6 | 2.7577 | 2.6224 | 3.4958 | -1.3238 | 2.7444 | 2.5957 | 3.4471 | 0.83333 | 0 |
| 유사작품_표본_부족 | 과대예측 | 극단오차 | 3 | 1.559 | 1.8721 | 2.4327 | -0.93961 | 1.559 | 1.8721 | 2.4327 | 0 | 0 |
| 비교군_가격분산_큼 | 과대예측 | 극단오차 | 1 | 1.6488 | 1.6488 | 1.6488 | -0.97409 | 1.6488 | 1.6488 | 1.6488 | 0 | 0 |
| 작가이력_표본_부족 | 과대예측 | 큰오차 | 2 | 0.81979 | 0.81979 | 0.95363 | -0.59537 | 0.80253 | 0.80253 | 0.93272 | 1 | 0 |
| 유사작품_적음+작가이력_적음 | 과소예측 | 큰오차 | 13 | 0.59515 | 0.66114 | 0.93384 | 0.90424 | 0.5954 | 0.6613 | 0.93384 | 0 | 0 |
| 유사작품_적음+작가이력_적음 | 과대예측 | 큰오차 | 27 | 0.63831 | 0.67493 | 0.91218 | -0.49366 | 0.63831 | 0.67423 | 0.91162 | 0 | 0 |
| 작가이력_표본_부족 | 과소예측 | 큰오차 | 2 | 0.7621 | 0.7621 | 0.79269 | 1.4462 | 0.76294 | 0.76294 | 0.79342 | 0 | 0 |
| 재료지지체_불확실 | 과대예측 | 큰오차 | 1 | 0.77602 | 0.77602 | 0.77602 | -0.57437 | 0.77602 | 0.77602 | 0.77602 | 0 | 0 |
| 비교군_가격분산_큼 | 과대예측 | 큰오차 | 1 | 0.65954 | 0.65954 | 0.65954 | -0.50654 | 0.65954 | 0.65954 | 0.65954 | 0 | 0 |
| 유사작품_표본_부족 | 과소예측 | 큰오차 | 1 | 0.64995 | 0.64995 | 0.64995 | 1.0497 | 0.64995 | 0.64995 | 0.64995 | 0 | 0 |
| 고가대형_꼬리구간 | 과소예측 | 큰오차 | 1 | 0.55868 | 0.55868 | 0.55868 | 0.81799 | 0.55868 | 0.55868 | 0.55868 | 0 | 0 |
| 중간_안정구간 | 과대예측 | 큰오차 | 1 | 0.53696 | 0.53696 | 0.53696 | -0.4298 | 0.53696 | 0.53696 | 0.53696 | 0 | 0 |
| 저가소형_꼬리구간 | 과대예측 | 큰오차 | 1 | 0.51043 | 0.51043 | 0.51043 | -0.4124 | 0.51043 | 0.51043 | 0.51043 | 0 | 0 |
| 유사작품_적음+작가이력_적음 | 과대예측 | 중간오차 | 22 | 0.36346 | 0.37968 | 0.48456 | -0.31002 | 0.36304 | 0.37925 | 0.48307 | 0 | 0 |
| 작가이력_표본_부족 | 과대예측 | 중간오차 | 4 | 0.39272 | 0.40841 | 0.48237 | -0.33109 | 0.38865 | 0.40222 | 0.47183 | 0.25 | 0 |
| 중간_안정구간 | 과소예측 | 중간오차 | 2 | 0.39358 | 0.39358 | 0.47587 | 0.51169 | 0.39358 | 0.39358 | 0.47587 | 0 | 0 |
| 유사작품_적음+작가이력_적음 | 과소예측 | 중간오차 | 27 | 0.35019 | 0.36871 | 0.46721 | 0.43108 | 0.35019 | 0.36896 | 0.46754 | 0 | 0 |
| 유사작품_표본_부족 | 과소예측 | 중간오차 | 3 | 0.45839 | 0.4289 | 0.46076 | 0.6132 | 0.45839 | 0.4289 | 0.46076 | 0 | 0 |
| 고가대형_꼬리구간 | 과대예측 | 중간오차 | 2 | 0.41322 | 0.41322 | 0.44612 | -0.34554 | 0.41322 | 0.41322 | 0.44612 | 0 | 0 |
| 고가_예측구간 | 과대예측 | 중간오차 | 1 | 0.42224 | 0.42224 | 0.42224 | -0.35223 | 0.42224 | 0.42224 | 0.42224 | 0 | 0 |
| 저가소형_꼬리구간 | 과소예측 | 중간오차 | 1 | 0.41379 | 0.41379 | 0.41379 | 0.53408 | 0.41379 | 0.41379 | 0.41379 | 0 | 0 |
| 작가이력_표본_부족 | 과소예측 | 중간오차 | 1 | 0.4117 | 0.4117 | 0.4117 | 0.53051 | 0.41635 | 0.41635 | 0.41635 | 0 | 0 |
| 비교군_가격분산_큼 | 과소예측 | 중간오차 | 3 | 0.3654 | 0.35776 | 0.37664 | 0.45477 | 0.3654 | 0.35776 | 0.37664 | 0 | 0 |

## 7. 산출물

- `outputs/validation_artist_holdout_summary.csv`: validation 후보별 안정성 + MAPE guard 통과 여부
- `outputs/test_once_metrics.csv`: test 성능 비교
- `outputs/test_artwork_error_diagnostics.csv`: 작품별 보정 전/후 변화
- `outputs/test_cause_summary.csv`: 원인군별 개선·악화 요약
- `artifacts/run_config.json`: seed/grid/mask 정의(재현용)