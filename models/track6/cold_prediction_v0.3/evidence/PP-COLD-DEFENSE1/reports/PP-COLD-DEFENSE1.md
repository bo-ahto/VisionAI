# PP-COLD-DEFENSE1 Cold guard + 검색 방어층 결합

- 작성일: 2026-06-07 21:26
- base = PP-Y18 대표. guard 임계값 qwidth_q67=1.4612, gap_q50=0.0772
- 검색 delta는 상류 고정값(h23 − pp_y2). 반복 subsample은 고정 후보 robustness.

## 1. 실행 결론

- 결합 가산적(중복 아님): redundancy gap +0.0006≈0. `guard_search_gm`가 guard 단독 대비 test ΔMdAPE -0.0079, ΔMAPE -0.1147, Δp95 -0.1912로 3지표 추가 개선. 두 방어는 거의 직교(guard=qwidth/gap tail, search=작가맥락 잔차). 단 검색층은 분산을 추가: validation fold MAPE 개선확률 guard 1.00 vs guard_search_gm 0.72. guard 단독이 가장 일관적(robust)이고, guard+search는 평균 최고지만 검색 커버리지/변동성 주의.

## 2. test 지표 (cold 3099)

| candidate | test_MdAPE | test_MAPE | test_p95_APE |
| --- | --- | --- | --- |
| y18_base | 0.4247 | 0.9910 | 3.3053 |
| guard | 0.4178 | 0.9640 | 2.5377 |
| search_gm | 0.4129 | 0.8757 | 2.9374 |
| search_sb | 0.4196 | 0.8781 | 2.9374 |
| guard_search_gm | 0.4098 | 0.8493 | 2.3465 |
| guard_search_sb | 0.4211 | 0.8517 | 2.3465 |
| ref_pp_y2_search_gm | 0.4313 | 0.9285 | 3.1390 |

## 3. 가산성 분해 (test MAPE, vs y18_base)

| search_source | dMAPE_guard | dMAPE_search | dMAPE_both | expected_if_additive | redundancy_gap | p95_guard | p95_both | incremental_vs_guard_MAPE | incremental_vs_guard_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gm | -0.0271 | -0.1153 | -0.1418 | -0.1424 | 0.0006 | 2.5377 | 2.3465 | -0.1147 | -0.1912 |
| sb | -0.0271 | -0.1129 | -0.1394 | -0.1400 | 0.0006 | 2.5377 | 2.3465 | -0.1123 | -0.1912 |

## 4. validation 반복 subsample (artist scheme, y18_base 대비 개선확률)

| candidate | mean_MdAPE | mean_MAPE | mean_p95_APE | prob_MdAPE_improve | prob_MAPE_improve | prob_p95_improve |
| --- | --- | --- | --- | --- | --- | --- |
| guard | 0.3793 | 0.5384 | 1.4390 | 0.4500 | 1.0000 | 0.8750 |
| guard_search_gm | 0.3723 | 0.5202 | 1.3967 | 0.6000 | 0.7250 | 0.7750 |
| guard_search_sb | 0.3676 | 0.5327 | 1.4846 | 0.6750 | 0.6500 | 0.6250 |
| ref_pp_y2_search_gm | 0.4007 | 0.5778 | 1.4982 | 0.4500 | 0.5250 | 0.7250 |
| search_gm | 0.3733 | 0.5518 | 1.5243 | 0.5750 | 0.6750 | 0.7500 |
| search_sb | 0.3680 | 0.5643 | 1.6104 | 0.7250 | 0.5500 | 0.6250 |
| y18_base | 0.3802 | 0.5719 | 1.5710 | 0.0000 | 0.0000 | 0.0000 |

## 5. 산출물

- `outputs/repeated_subsample_summary.csv`, `outputs/test_metrics.csv`, `outputs/additivity_decomposition.csv`, `artifacts/run_config.json`