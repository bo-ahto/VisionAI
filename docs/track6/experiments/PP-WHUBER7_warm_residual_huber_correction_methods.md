# PP-WHUBER7 Warm residual Huber 보정 방식 세분화 실험

- 작성일: 2026-06-06 16:39
- 목적: 현재 Warm 1순위 후보 위에 적용할 Huber residual 보정 방법을 세분화해 검증
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 기준 validation MdAPE/MAPE/p95: `0.1305` / `0.2110` / `0.6580`
- 기준 test MdAPE/MAPE/p95: `0.1405` / `0.2748` / `0.8331`

## 0. 실험 계획

- 기준 예측값은 현재 Warm 1순위 `blend_svcnum_ppv8_wsvc_0.70`로 고정
- validation 내부 교차검증으로 residual Huber 보정값을 만들고 validation 성능을 확인
- test에는 validation 전체로 학습한 residual Huber 보정식을 한 번만 적용
- 보정 방법은 hard clip, soft tanh, 신뢰도별 축소, 방향별 강도, 예측 가격 구간별 cap, 혼합 정책으로 분리
- test 결과는 후보 탐색 결과로만 보고, 운영 반영 전 반복 split 또는 OOF 재검증 필요

## 1. 실행 결론

- test 최상위 후보: `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35`
- test 최상위 후보 성능: MdAPE `0.1328`, MAPE `0.2743`, p95_APE `0.8447`
- 세 지표를 모두 개선한 후보 수: `495`
- 균형 후보: `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25`
- 균형 후보 성능: MdAPE `0.1334`, MAPE `0.2745`, p95_APE `0.8288`
- 큰 오차 방어 후보: `PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08`
- 큰 오차 방어 후보 성능: MdAPE `0.1396`, MAPE `0.2733`, p95_APE `0.8016`
- 현재 split에서는 residual Huber 보정 방식 세분화로 추가 개선 후보가 확인됨
- 다만 validation 선택 후보와 test 최상위 후보가 다를 수 있으므로, v0.1 반영 전 안정성 재검증 필요

## 2. Validation 기준 선택 후보

| 선택 기준 | 후보 | 방식 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| MdAPE 우선 | `PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p35` | pred_bin_cap | 0.1223 | 0.2085 | 0.6532 | 0.1388 | 0.2739 | 0.8118 |
| MAPE 우선 + MdAPE 3% 이내 | `PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_dir_under_guard_cap0p08` | directional_strength | 0.1254 | 0.2081 | 0.6531 | 0.1396 | 0.2733 | 0.8018 |
| p95 우선 + MdAPE 5% 이내 | `PP-WHUBER7_pred_size_svc_eps1.60_alpha0p001_clip_cap0p08_s0p3` | hard_clip | 0.1246 | 0.2095 | 0.6357 | 0.1409 | 0.2749 | 0.8117 |
| 균형 점수 | `PP-WHUBER7_pred_size_svc_eps1.20_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p35` | pred_bin_cap | 0.1228 | 0.2090 | 0.6439 | 0.1403 | 0.2741 | 0.8158 |

## 3. Test 상위 후보

| 순위 | 후보 | 방식 | feature set | epsilon | alpha | cap | strength | MdAPE | MAPE | p95_APE | RMSE_log |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35` | pred_bin_cap | pred_size_material_svc_artist | 1.60 | 0.001 | 0.06 | 0.35 | 0.1328 | 0.2743 | 0.8447 | 0.3988 |
| 2 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p25` | pred_bin_cap | pred_size_material_svc_artist | 1.60 | 0.001 | 0.08 | 0.25 | 0.1331 | 0.2743 | 0.8387 | 0.3989 |
| 3 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25` | pred_bin_cap | pred_size_material_svc_artist | 1.60 | 0.010 | 0.08 | 0.25 | 0.1334 | 0.2743 | 0.8382 | 0.3989 |
| 4 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25` | pred_bin_cap | pred_size_material_svc_artist | 1.35 | 0.010 | 0.08 | 0.25 | 0.1334 | 0.2745 | 0.8288 | 0.3990 |
| 5 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_clip_cap0p06_s0p3` | hard_clip | pred_size_material_svc_artist | 1.60 | 0.001 | 0.06 | 0.3 | 0.1341 | 0.2745 | 0.8417 | 0.3990 |
| 6 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p25` | pred_bin_cap | pred_size_material_svc_artist | 1.35 | 0.001 | 0.08 | 0.25 | 0.1341 | 0.2745 | 0.8288 | 0.3990 |
| 7 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35` | pred_bin_cap | pred_size_material_svc_artist | 1.60 | 0.010 | 0.06 | 0.35 | 0.1342 | 0.2743 | 0.8437 | 0.3988 |
| 8 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35` | pred_bin_cap | pred_size_material_svc_artist | 1.35 | 0.001 | 0.06 | 0.35 | 0.1342 | 0.2745 | 0.8287 | 0.3989 |
| 9 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35` | pred_bin_cap | pred_size_material_svc_artist | 1.35 | 0.010 | 0.06 | 0.35 | 0.1342 | 0.2746 | 0.8287 | 0.3989 |
| 10 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_tanh_cap0p06_s0p3` | soft_tanh_cap | pred_size_material_svc_artist | 1.60 | 0.001 | 0.06 | 0.3 | 0.1344 | 0.2744 | 0.8390 | 0.3990 |
| 11 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p25` | pred_bin_cap | pred_size_material_svc_artist | 1.60 | 0.001 | 0.06 | 0.25 | 0.1345 | 0.2743 | 0.8389 | 0.3990 |
| 12 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p25` | pred_bin_cap | pred_size_material_svc_artist | 1.60 | 0.010 | 0.06 | 0.25 | 0.1345 | 0.2743 | 0.8387 | 0.3990 |
| 13 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p25` | pred_bin_cap | pred_size_material_svc_artist | 1.35 | 0.001 | 0.06 | 0.25 | 0.1345 | 0.2745 | 0.8311 | 0.3990 |
| 14 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p25` | pred_bin_cap | pred_size_material_svc_artist | 1.35 | 0.010 | 0.06 | 0.25 | 0.1345 | 0.2745 | 0.8311 | 0.3991 |
| 15 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_hybrid_strict_rel_mid_open_tail_guard_cap0p08_s0p25` | hybrid_rel_predbin | pred_size_material_svc_artist | 1.60 | 0.001 | 0.08 | 0.25 | 0.1345 | 0.2744 | 0.8359 | 0.3991 |
| 16 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_hybrid_strict_rel_mid_open_tail_guard_cap0p08_s0p25` | hybrid_rel_predbin | pred_size_material_svc_artist | 1.60 | 0.010 | 0.08 | 0.25 | 0.1345 | 0.2744 | 0.8357 | 0.3991 |
| 17 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_rel_soft_rel_cap0p08_s0p35` | reliability_shrink | pred_size_material_svc_artist | 1.60 | 0.001 | 0.08 | 0.35 | 0.1345 | 0.2744 | 0.8376 | 0.3990 |
| 18 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_hybrid_soft_rel_tail_open_mid_guard_cap0p08_s0p35` | hybrid_rel_predbin | pred_size_material_svc_artist | 1.60 | 0.001 | 0.08 | 0.35 | 0.1345 | 0.2745 | 0.8377 | 0.3991 |
| 19 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_rel_soft_rel_cap0p08_s0p35` | reliability_shrink | pred_size_material_svc_artist | 1.60 | 0.010 | 0.08 | 0.35 | 0.1345 | 0.2744 | 0.8372 | 0.3989 |
| 20 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_hybrid_soft_rel_tail_open_mid_guard_cap0p08_s0p35` | hybrid_rel_predbin | pred_size_material_svc_artist | 1.60 | 0.010 | 0.08 | 0.35 | 0.1345 | 0.2745 | 0.8375 | 0.3991 |
| 21 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_tanh_cap0p08_s0p25` | soft_tanh_cap | pred_size_material_svc_artist | 1.60 | 0.001 | 0.08 | 0.25 | 0.1346 | 0.2744 | 0.8384 | 0.3990 |
| 22 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_clip_cap0p08_s0p25` | hard_clip | pred_size_material_svc_artist | 1.60 | 0.001 | 0.08 | 0.25 | 0.1346 | 0.2745 | 0.8387 | 0.3990 |
| 23 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_dir_balanced_direction_cap0p08` | directional_strength | pred_size_material_svc_artist | 1.60 | 0.001 | 0.08 |  | 0.1346 | 0.2745 | 0.8387 | 0.3990 |
| 24 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_rel_strict_rel_cap0p06_s0p25` | reliability_shrink | pred_size_material_svc_artist | 1.60 | 0.001 | 0.06 | 0.25 | 0.1346 | 0.2744 | 0.8360 | 0.3992 |
| 25 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_rel_strict_rel_cap0p06_s0p25` | reliability_shrink | pred_size_material_svc_artist | 1.60 | 0.010 | 0.06 | 0.25 | 0.1346 | 0.2744 | 0.8359 | 0.3992 |
| 26 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_clip_cap0p06_s0p3` | hard_clip | pred_size_material_svc_artist | 1.60 | 0.010 | 0.06 | 0.3 | 0.1347 | 0.2745 | 0.8409 | 0.3990 |
| 27 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p001_clip_cap0p06_s0p3` | hard_clip | pred_size_material_svc_artist | 1.35 | 0.001 | 0.06 | 0.3 | 0.1347 | 0.2747 | 0.8292 | 0.3991 |
| 28 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_clip_cap0p06_s0p3` | hard_clip | pred_size_material_svc_artist | 1.35 | 0.010 | 0.06 | 0.3 | 0.1347 | 0.2747 | 0.8292 | 0.3991 |
| 29 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_dir_over_guard_cap0p06` | directional_strength | pred_size_material_svc_artist | 1.60 | 0.001 | 0.06 |  | 0.1347 | 0.2753 | 0.8417 | 0.3991 |
| 30 | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_dir_over_guard_cap0p08` | directional_strength | pred_size_material_svc_artist | 1.60 | 0.001 | 0.08 |  | 0.1348 | 0.2755 | 0.8416 | 0.3991 |

## 4. Bootstrap 안정성 요약

| 표본 추출 방식 | 후보 | MdAPE 평균 차이 | MdAPE 개선 확률 | MAPE 개선 확률 | p95 개선 확률 |
|---|---|---:|---:|---:|---:|
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35` | -0.00484 | 0.813 | 0.673 | 0.633 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35` | -0.00472 | 0.817 | 0.673 | 0.627 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_clip_cap0p06_s0p3` | -0.00461 | 0.790 | 0.627 | 0.617 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p25` | -0.00457 | 0.830 | 0.693 | 0.647 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25` | -0.00444 | 0.830 | 0.697 | 0.643 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_tanh_cap0p06_s0p3` | -0.00439 | 0.790 | 0.657 | 0.623 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35` | -0.00382 | 0.760 | 0.613 | 0.743 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35` | -0.00372 | 0.760 | 0.613 | 0.747 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25` | -0.00370 | 0.767 | 0.637 | 0.773 |
| artist_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p25` | -0.00363 | 0.767 | 0.637 | 0.793 |
| artist_bootstrap | `PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_dir_under_guard_cap0p08` | -0.00003 | 0.570 | 0.920 | 0.720 |
| artist_bootstrap | `blend_svcnum_ppv8_wsvc_0.70` | 0.00000 | 0.000 | 0.000 | 0.000 |
| artist_bootstrap | `PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p35` | 0.00012 | 0.540 | 0.733 | 0.723 |
| artist_bootstrap | `PP-WHUBER7_pred_size_svc_eps1.20_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p35` | 0.00056 | 0.483 | 0.700 | 0.693 |
| artist_bootstrap | `PP-WHUBER7_pred_size_svc_eps1.60_alpha0p001_clip_cap0p08_s0p3` | 0.00116 | 0.447 | 0.477 | 0.700 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35` | -0.00547 | 0.840 | 0.673 | 0.570 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_clip_cap0p06_s0p3` | -0.00546 | 0.830 | 0.627 | 0.577 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p25` | -0.00537 | 0.857 | 0.700 | 0.597 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35` | -0.00533 | 0.830 | 0.677 | 0.567 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_tanh_cap0p06_s0p3` | -0.00526 | 0.830 | 0.640 | 0.600 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25` | -0.00524 | 0.853 | 0.687 | 0.590 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35` | -0.00463 | 0.800 | 0.560 | 0.697 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35` | -0.00450 | 0.797 | 0.567 | 0.703 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25` | -0.00439 | 0.797 | 0.590 | 0.740 |
| row_bootstrap | `PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p25` | -0.00436 | 0.797 | 0.590 | 0.760 |
| row_bootstrap | `PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_dir_under_guard_cap0p08` | -0.00079 | 0.607 | 0.947 | 0.773 |
| row_bootstrap | `PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p35` | -0.00037 | 0.577 | 0.767 | 0.747 |
| row_bootstrap | `PP-WHUBER7_pred_size_svc_eps1.20_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p35` | -0.00013 | 0.543 | 0.737 | 0.713 |
| row_bootstrap | `blend_svcnum_ppv8_wsvc_0.70` | 0.00000 | 0.000 | 0.000 | 0.000 |
| row_bootstrap | `PP-WHUBER7_pred_size_svc_eps1.60_alpha0p001_clip_cap0p08_s0p3` | 0.00070 | 0.453 | 0.433 | 0.737 |

## 5. 구간별 진단

- 구간별 진단은 `outputs/segment_diagnostics.csv`에 전체 저장
- 리포트에는 상위 일부만 표시

