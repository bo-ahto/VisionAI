# PP-QR4 Cold qwidth/guard 생존 후보 반복 split·artist holdout 재검증

- 작성일: 2026-06-07 20:45
- 검증 대상: `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50`(대표 개선), `guard_y18_lgb_q40_qwidth67_gap50_down_w0p50`(MAPE/p95 방어)
- 기준선: `component_pp_y18_qwidth_bin` (PP-Y18 qwidth, test MdAPE 참고 0.4247)
- 프로토콜: row 5-fold x 12 seeds + artist GroupKFold 5-fold x 12 seeds + test bootstrap 400회. 보정맵은 fold calibration에서만 재학습

## 1. 실행 결론

- `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` [representative] → **보류 (row/artist holdout 불일치 — 작가 구성 의존)** (row/artist MdAPE 개선확률 0.97/0.22, MAPE 1.00/0.32, p95 0.83/0.35, test MdAPE 0.4175)
- `guard_y18_lgb_q40_qwidth67_gap50_down_w0p50` [defense] → **채택 (MAPE/p95 방어 후보, MdAPE 비악화)** (row/artist MdAPE 개선확률 0.43/0.52, MAPE 1.00/0.98, p95 0.98/0.85, test MdAPE 0.4178)

## 2. holdout MdAPE 개선확률 (vs PP-Y18, scheme별)

| candidate | artist_5fold | row_5fold |
| --- | --- | --- |
| component_pp_y18_qwidth_bin | 0.0000 | 0.0000 |
| component_pp_y2_baseline | 0.3167 | 0.0000 |
| guard_y18_lgb_q40_qwidth67_gap50_down_w0p50 | 0.5167 | 0.4333 |
| segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50 | 0.2167 | 0.9667 |

## 3. holdout 평균 MdAPE (scheme별)

| candidate | artist_5fold | row_5fold |
| --- | --- | --- |
| component_pp_y18_qwidth_bin | 0.3790 | 0.3671 |
| component_pp_y2_baseline | 0.4195 | 0.4126 |
| guard_y18_lgb_q40_qwidth67_gap50_down_w0p50 | 0.3742 | 0.3665 |
| segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50 | 0.3874 | 0.3575 |

## 4. holdout 후보 요약 (scheme별 상세)

| scheme | candidate | folds | mean_MdAPE | std_MdAPE | mean_MAPE | mean_p95_APE | prob_MdAPE_improve | prob_MAPE_improve | prob_p95_improve |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_5fold | guard_y18_lgb_q40_qwidth67_gap50_down_w0p50 | 60 | 0.3742 | 0.0473 | 0.5360 | 1.4332 | 0.5167 | 0.9833 | 0.8500 |
| artist_5fold | component_pp_y18_qwidth_bin | 60 | 0.3790 | 0.0502 | 0.5701 | 1.5577 | 0.0000 | 0.0000 | 0.0000 |
| artist_5fold | segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50 | 60 | 0.3874 | 0.0506 | 0.5795 | 1.5874 | 0.2167 | 0.3167 | 0.3500 |
| artist_5fold | component_pp_y2_baseline | 60 | 0.4195 | 0.0686 | 0.6102 | 1.6339 | 0.3167 | 0.1667 | 0.2667 |
| row_5fold | segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50 | 60 | 0.3575 | 0.0145 | 0.5350 | 1.3682 | 0.9667 | 1.0000 | 0.8333 |
| row_5fold | guard_y18_lgb_q40_qwidth67_gap50_down_w0p50 | 60 | 0.3665 | 0.0116 | 0.5182 | 1.3219 | 0.4333 | 1.0000 | 0.9833 |
| row_5fold | component_pp_y18_qwidth_bin | 60 | 0.3671 | 0.0115 | 0.5460 | 1.4140 | 0.0000 | 0.0000 | 0.0000 |
| row_5fold | component_pp_y2_baseline | 60 | 0.4126 | 0.0144 | 0.5887 | 1.4952 | 0.0000 | 0.0000 | 0.1167 |

## 5. test 점추정

| candidate | test_MdAPE | test_MAPE | test_p95_APE |
| --- | --- | --- | --- |
| component_pp_y18_qwidth_bin | 0.4247 | 0.9910 | 3.3053 |
| component_pp_y2_baseline | 0.4421 | 1.0484 | 3.3537 |
| segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50 | 0.4175 | 1.0029 | 3.0018 |
| guard_y18_lgb_q40_qwidth67_gap50_down_w0p50 | 0.4178 | 0.9640 | 2.5377 |

## 6. test bootstrap (400회) 95% CI

| candidate | boot_MdAPE_mean | boot_MdAPE_ci_low | boot_MdAPE_ci_high | boot_MAPE_mean | boot_p95_mean | prob_MdAPE_beats_baseline | ci_high_le_baseline_ref |
| --- | --- | --- | --- | --- | --- | --- | --- |
| component_pp_y18_qwidth_bin | 0.4237 | 0.4079 | 0.4431 | 0.9909 | 3.1583 | 0.0000 | False |
| component_pp_y2_baseline | 0.4429 | 0.4218 | 0.4607 | 1.0479 | 3.3796 | 0.0000 | False |
| segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50 | 0.4188 | 0.4085 | 0.4348 | 1.0028 | 3.0360 | 0.8625 | False |
| guard_y18_lgb_q40_qwidth67_gap50_down_w0p50 | 0.4192 | 0.4051 | 0.4364 | 0.9636 | 2.6169 | 0.9075 | False |

## 7. 산출물

- `outputs/repeated_holdout_metrics.csv`, `outputs/holdout_summary.csv`
- `outputs/test_point_metrics.csv`, `outputs/test_bootstrap_ci.csv`, `artifacts/run_config.json`