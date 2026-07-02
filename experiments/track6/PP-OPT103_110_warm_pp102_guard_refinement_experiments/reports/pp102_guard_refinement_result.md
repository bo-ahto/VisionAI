# PP-OPT103~110 Warm PP102 guard refinement 실험 결과

- 작성일: 2026-06-09 14:31
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP102 보정값을 risk/gain/harm 조건에 맞춰 줄이거나 rollback하여 안정성을 개선
- 결론: 운영 후보 candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 fixed test MAPE 0.270555, p95 0.807490. PP64 대비 MAPE -0.000009, p95 -0.000009.
- 해석: 의미 있는 모델 특성 실험이다. PP102의 보정은 validation에서 배운 gain label을 쓰기 때문에 확률 margin이 약하거나 기존 risk score가 높은 row에서는 보정을 줄이는 것이 Huber/잔차 보정 계열의 보수적 특성과 맞는다. 다만 개선폭이 1e-5 수준이면 운영 교체는 안정성 지표까지 같이 봐야 한다.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_pp102_operational | reference_prior | REFERENCE | 0.137878 | 0.270555 | 0.807490 | 0.397983 | -0.000840 | -0.000640 |
| ppopt110_operational_guarded_pp102_challenger__source=ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | guarded_pp102_operational_selection | PP-OPT110 | 0.137878 | 0.270555 | 0.807490 | 0.397983 | -0.000840 | -0.000640 |
| ppopt110_p95_guarded_pp102_challenger__source=ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | guarded_pp102_p95_selection | PP-OPT110 | 0.137878 | 0.270557 | 0.807482 | 0.397978 | -0.000838 | -0.000648 |
| reference_pp81_best | reference_prior | REFERENCE | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp95_operational | reference_prior | REFERENCE | 0.137878 | 0.270559 | 0.807490 | 0.397989 | -0.000836 | -0.000640 |
| reference_pp70_refinement | reference_prior | REFERENCE | 0.137878 | 0.270561 | 0.807490 | 0.397991 | -0.000834 | -0.000640 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | gain-harm margin gate | 768 | 0.270556 | 0.807490 | 0.270553 | 0.807490 | True | gain_harm_margin_gate | ppopt104_margin_gate__gain=gain_any__hpen=0p85__rpen=0p26__thr=0p0__s=1p0 |
| 8 | final guarded PP102 decision | 2 | 0.270555 | 0.807490 | 0.270557 | 0.807482 | True | guarded_pp102_operational_selection | ppopt110_operational_guarded_pp102_challenger__source=ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 |
| 4 | stable-baseline gated adoption | 324 | 0.270561 | 0.807490 | 0.270554 | 0.807490 | True | stable_baseline_gated_adoption | ppopt106_stable_adoption__safe=pp81__gain=tail_intent__hpen=0p95__rpen=0p12__thr=0p2 |
| 5 | risk rollback router | 240 | 0.270557 | 0.807490 | 0.270556 | 0.807490 | True | risk_harm_rollback_router | ppopt107_rollback__safe=pp81__rthr=0p74__hthr=0p02__s=1p0 |
| 1 | PP102 risk-score shrink | 180 | 0.270556 | 0.807490 | 0.270555 | 0.807490 | True | pp102_risk_score_shrink | ppopt103_risk_shrink__safe=pp81__thr=0p62__width=0p26__shrink=1p0 |
| 6 | tail-purpose hybrid router | 192 | 0.270556 | 0.807490 | 0.270557 | 0.807482 | True | tail_purpose_hybrid_router | ppopt108_tail_hybrid__target=pp102_p95__opthr=0p02__tailthr=0p32__tails=0p1 |
| 3 | risk adaptive correction cap | 60 | 0.270555 | 0.807490 | 0.270555 | 0.807490 | True | risk_adaptive_correction_cap | ppopt105_adaptive_cap__basecap=0p016__mincap=0p004__rshrink=0p25 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt104_margin_gate__gain=gain_any__hpen=0p85__rpen=0p26__thr=0p0__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270556 | 0.807490 | -0.000839 | -0.000640 | 1.000000 | 0.537500 | -0.001384 |
| ppopt104_margin_gate__gain=gain_any__hpen=1p05__rpen=0p26__thr=0p0__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001384 |
| ppopt104_margin_gate__gain=gain_any__hpen=1p05__rpen=0p18__thr=0p04__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001384 |
| ppopt104_margin_gate__gain=gain_any__hpen=1p05__rpen=0p0__thr=0p14__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt110_operational_guarded_pp102_challenger__source=ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | PP-OPT110 | guarded_pp102_operational_selection | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p85__rpen=0p18__thr=0p04__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270556 | 0.807490 | -0.000839 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=1p05__rpen=0p1__thr=0p08__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270556 | 0.807490 | -0.000839 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=1p05__rpen=0p18__thr=0p0__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p65__rpen=0p26__thr=0p0__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p85__rpen=0p1__thr=0p08__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p65__rpen=0p18__thr=0p04__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p85__rpen=0p18__thr=0p0__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270556 | 0.807490 | -0.000839 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=1p05__rpen=0p1__thr=0p04__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270556 | 0.807490 | -0.000839 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt106_stable_adoption__safe=pp81__gain=tail_intent__hpen=0p95__rpen=0p12__thr=0p2 | PP-OPT106 | stable_baseline_gated_adoption | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt106_stable_adoption__safe=pp95_op__gain=tail_intent__hpen=0p95__rpen=0p12__thr=0p2 | PP-OPT106 | stable_baseline_gated_adoption | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p85__rpen=0p0__thr=0p14__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt107_rollback__safe=pp81__rthr=0p74__hthr=0p02__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt107_rollback__safe=pp95_op__rthr=0p74__hthr=0p02__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p65__rpen=0p1__thr=0p08__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270554 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt107_rollback__safe=pp81__rthr=0p74__hthr=0p04__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt107_rollback__safe=pp95_op__rthr=0p74__hthr=0p04__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p45__rpen=0p26__thr=0p0__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt107_rollback__safe=pp81__rthr=0p64__hthr=0p02__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt107_rollback__safe=pp95_op__rthr=0p64__hthr=0p02__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001383 |
| ppopt107_rollback__safe=pp81__rthr=0p64__hthr=0p04__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270558 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp95_op__rthr=0p64__hthr=0p04__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270558 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt106_stable_adoption__safe=pp81__gain=tail_intent__hpen=0p45__rpen=0p22__thr=0p2 | PP-OPT106 | stable_baseline_gated_adoption | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt106_stable_adoption__safe=pp95_op__gain=tail_intent__hpen=0p45__rpen=0p22__thr=0p2 | PP-OPT106 | stable_baseline_gated_adoption | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p65__rpen=0p0__thr=0p14__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270554 | 0.807490 | -0.000841 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p45__rpen=0p18__thr=0p04__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p85__rpen=0p1__thr=0p04__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp81__rthr=0p74__hthr=0p02__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp95_op__rthr=0p74__hthr=0p02__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp81__rthr=0p74__hthr=0p04__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp95_op__rthr=0p74__hthr=0p04__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp81__rthr=0p64__hthr=0p02__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp95_op__rthr=0p64__hthr=0p02__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt106_stable_adoption__safe=pp81__gain=tail_intent__hpen=0p7__rpen=0p12__thr=0p2 | PP-OPT106 | stable_baseline_gated_adoption | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt106_stable_adoption__safe=pp95_op__gain=tail_intent__hpen=0p7__rpen=0p12__thr=0p2 | PP-OPT106 | stable_baseline_gated_adoption | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt104_margin_gate__gain=gain_any__hpen=1p05__rpen=0p1__thr=0p0__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270556 | 0.807490 | -0.000839 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp81__rthr=0p64__hthr=0p07__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270558 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp95_op__rthr=0p64__hthr=0p07__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270558 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp81__rthr=0p64__hthr=0p04__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp95_op__rthr=0p64__hthr=0p04__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000838 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p65__rpen=0p18__thr=0p0__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp81__rthr=0p74__hthr=0p07__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270558 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp95_op__rthr=0p74__hthr=0p07__s=1p0 | PP-OPT107 | risk_harm_rollback_router | 0.270558 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt106_stable_adoption__safe=pp70__gain=tail_intent__hpen=0p95__rpen=0p12__thr=0p2 | PP-OPT106 | stable_baseline_gated_adoption | 0.270561 | 0.807490 | -0.000834 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt104_margin_gate__gain=gain_any__hpen=0p45__rpen=0p1__thr=0p08__s=1p0 | PP-OPT104 | gain_harm_margin_gate | 0.270555 | 0.807490 | -0.000840 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |
| ppopt107_rollback__safe=pp81__rthr=0p64__hthr=0p07__s=0p85 | PP-OPT107 | risk_harm_rollback_router | 0.270557 | 0.807490 | -0.000837 | -0.000640 | 1.000000 | 0.537500 | -0.001382 |

## p95 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p02__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807482 | -0.000838 | -0.000648 | 1.000000 | 0.537500 | -0.001373 |
| ppopt110_p95_guarded_pp102_challenger__source=ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | PP-OPT110 | guarded_pp102_p95_selection | 0.270557 | 0.807482 | -0.000838 | -0.000648 | 1.000000 | 0.537500 | -0.001373 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p06__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270560 | 0.807482 | -0.000835 | -0.000648 | 1.000000 | 0.537500 | -0.001371 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p16__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270561 | 0.807482 | -0.000834 | -0.000648 | 1.000000 | 0.537500 | -0.001370 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p1__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270561 | 0.807482 | -0.000834 | -0.000648 | 1.000000 | 0.537500 | -0.001371 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p02__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807482 | -0.000838 | -0.000648 | 1.000000 | 0.537500 | -0.001373 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p06__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270560 | 0.807482 | -0.000835 | -0.000648 | 1.000000 | 0.537500 | -0.001371 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p16__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270561 | 0.807482 | -0.000834 | -0.000648 | 1.000000 | 0.537500 | -0.001370 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p1__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270561 | 0.807482 | -0.000834 | -0.000648 | 1.000000 | 0.537500 | -0.001371 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p02__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807485 | -0.000838 | -0.000645 | 1.000000 | 0.537500 | -0.001375 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p16__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270559 | 0.807485 | -0.000836 | -0.000645 | 1.000000 | 0.537500 | -0.001373 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p1__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270559 | 0.807485 | -0.000836 | -0.000645 | 1.000000 | 0.537500 | -0.001374 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p06__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270560 | 0.807485 | -0.000835 | -0.000645 | 1.000000 | 0.537500 | -0.001373 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p02__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807485 | -0.000838 | -0.000645 | 1.000000 | 0.537500 | -0.001375 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p16__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270559 | 0.807485 | -0.000836 | -0.000645 | 1.000000 | 0.537500 | -0.001373 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p1__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270559 | 0.807485 | -0.000836 | -0.000645 | 1.000000 | 0.537500 | -0.001374 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p06__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270560 | 0.807485 | -0.000835 | -0.000645 | 1.000000 | 0.537500 | -0.001373 |
| ppopt108_tail_hybrid__target=pp102_p95__opthr=0p02__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270561 | 0.807485 | -0.000834 | -0.000645 | 1.000000 | 0.537500 | -0.001372 |
| ppopt108_tail_hybrid__target=pp102_p95__opthr=0p06__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270564 | 0.807485 | -0.000831 | -0.000645 | 1.000000 | 0.537500 | -0.001370 |
| ppopt108_tail_hybrid__target=pp102_p95__opthr=0p16__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270564 | 0.807485 | -0.000831 | -0.000645 | 1.000000 | 0.537500 | -0.001370 |
| ppopt108_tail_hybrid__target=pp102_p95__opthr=0p1__tailthr=0p08__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270565 | 0.807485 | -0.000830 | -0.000645 | 1.000000 | 0.537500 | -0.001371 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p16__tailthr=0p08__tails=0p18 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807487 | -0.000838 | -0.000643 | 1.000000 | 0.537500 | -0.001376 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p02__tailthr=0p08__tails=0p18 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807487 | -0.000838 | -0.000643 | 1.000000 | 0.537500 | -0.001377 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p1__tailthr=0p08__tails=0p18 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807487 | -0.000838 | -0.000643 | 1.000000 | 0.537500 | -0.001377 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p06__tailthr=0p08__tails=0p18 | PP-OPT108 | tail_purpose_hybrid_router | 0.270558 | 0.807487 | -0.000837 | -0.000643 | 1.000000 | 0.537500 | -0.001376 |
| ppopt108_tail_hybrid__target=pp102_p95__opthr=0p02__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270560 | 0.807487 | -0.000835 | -0.000643 | 1.000000 | 0.537500 | -0.001375 |
| ppopt108_tail_hybrid__target=pp102_p95__opthr=0p16__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270561 | 0.807487 | -0.000834 | -0.000643 | 1.000000 | 0.537500 | -0.001373 |
| ppopt108_tail_hybrid__target=pp102_p95__opthr=0p1__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270561 | 0.807487 | -0.000833 | -0.000643 | 1.000000 | 0.537500 | -0.001374 |
| ppopt108_tail_hybrid__target=pp102_p95__opthr=0p06__tailthr=0p08__tails=0p28 | PP-OPT108 | tail_purpose_hybrid_router | 0.270562 | 0.807487 | -0.000833 | -0.000643 | 1.000000 | 0.537500 | -0.001373 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p16__tailthr=0p08__tails=0p18 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807487 | -0.000838 | -0.000643 | 1.000000 | 0.537500 | -0.001376 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p02__tailthr=0p08__tails=0p18 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807487 | -0.000838 | -0.000643 | 1.000000 | 0.537500 | -0.001377 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p1__tailthr=0p08__tails=0p18 | PP-OPT108 | tail_purpose_hybrid_router | 0.270557 | 0.807487 | -0.000838 | -0.000643 | 1.000000 | 0.537500 | -0.001377 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p06__tailthr=0p08__tails=0p18 | PP-OPT108 | tail_purpose_hybrid_router | 0.270558 | 0.807487 | -0.000837 | -0.000643 | 1.000000 | 0.537500 | -0.001376 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p02__tailthr=0p14__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270556 | 0.807487 | -0.000839 | -0.000643 | 1.000000 | 0.537500 | -0.001378 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p06__tailthr=0p14__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270558 | 0.807487 | -0.000836 | -0.000643 | 1.000000 | 0.537500 | -0.001376 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p16__tailthr=0p14__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270560 | 0.807487 | -0.000835 | -0.000643 | 1.000000 | 0.537500 | -0.001376 |
| ppopt108_tail_hybrid__target=pp82_p95__opthr=0p1__tailthr=0p14__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270560 | 0.807487 | -0.000835 | -0.000643 | 1.000000 | 0.537500 | -0.001377 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p02__tailthr=0p14__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270556 | 0.807487 | -0.000839 | -0.000643 | 1.000000 | 0.537500 | -0.001378 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p06__tailthr=0p14__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270558 | 0.807487 | -0.000836 | -0.000643 | 1.000000 | 0.537500 | -0.001376 |
| ppopt108_tail_hybrid__target=pp95_p95__opthr=0p16__tailthr=0p14__tails=0p4 | PP-OPT108 | tail_purpose_hybrid_router | 0.270560 | 0.807487 | -0.000835 | -0.000643 | 1.000000 | 0.537500 | -0.001376 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp81_stable_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | -0.015633 |
| pp95_operational_reference | 0.270559 | 0.807490 | -0.000005 | -0.000009 | -0.000004 | -0.000014 | 0.890705 | 0.410256 | -0.015633 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000001 | 0.786859 | 0.398077 | -0.011477 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000005 | -0.000016 | 0.782051 | 0.454808 | -0.011291 |
| pp110_operational_guarded_challenger | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000005 | -0.000016 | 0.782051 | 0.454808 | -0.011291 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p85__rpen_0p26__thr_0p0__s_1p0 | 0.270556 | 0.807490 | -0.000008 | -0.000009 | -0.000005 | -0.000016 | 0.781410 | 0.454808 | -0.011264 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p18__thr_0p04__s_1p0 | 0.270557 | 0.807490 | -0.000008 | -0.000009 | -0.000005 | -0.000016 | 0.781090 | 0.454808 | -0.011251 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p26__thr_0p0__s_1p0 | 0.270557 | 0.807490 | -0.000007 | -0.000009 | -0.000004 | -0.000015 | 0.775962 | 0.454808 | -0.011045 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p1__thr_0p08__s_1p0 | 0.270556 | 0.807490 | -0.000008 | -0.000009 | -0.000005 | -0.000016 | 0.695833 | 0.454808 | -0.007841 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p85__rpen_0p18__thr_0p04__s_1p0 | 0.270556 | 0.807490 | -0.000008 | -0.000009 | -0.000005 | -0.000016 | 0.692308 | 0.454808 | -0.007701 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p85__rpen_0p1__thr_0p08__s_1p0 | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000005 | -0.000017 | 0.688782 | 0.454808 | -0.007560 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p45__rpen_0p1__thr_0p14__s_1p0 | 0.270554 | 0.807490 | -0.000010 | -0.000009 | -0.000006 | -0.000014 | 0.687821 | 0.454808 | -0.007523 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p65__rpen_0p26__thr_0p0__s_1p0 | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000005 | -0.000016 | 0.687500 | 0.454808 | -0.007509 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p18__thr_0p0__s_1p0 | 0.270557 | 0.807490 | -0.000008 | -0.000009 | -0.000005 | -0.000017 | 0.683974 | 0.454808 | -0.007367 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p65__rpen_0p18__thr_0p04__s_1p0 | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000005 | -0.000016 | 0.681090 | 0.454808 | -0.007253 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p85__rpen_0p0__thr_0p14__s_1p0 | 0.270555 | 0.807490 | -0.000010 | -0.000009 | -0.000005 | -0.000017 | 0.680128 | 0.454808 | -0.007215 |
| candidate_ppopt107_rollback__safe_pp81__rthr_0p74__hthr_0p02__s_1p0 | 0.270557 | 0.807490 | -0.000007 | -0.000009 | -0.000003 | -0.000023 | 0.678205 | 0.450000 | -0.007135 |
| candidate_ppopt107_rollback__safe_pp95_op__rthr_0p74__hthr_0p02__s_1p0 | 0.270557 | 0.807490 | -0.000007 | -0.000009 | -0.000003 | -0.000023 | 0.678205 | 0.450000 | -0.007135 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p85__rpen_0p18__thr_0p0__s_1p0 | 0.270556 | 0.807490 | -0.000008 | -0.000009 | -0.000005 | -0.000017 | 0.675321 | 0.454808 | -0.007021 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p1__thr_0p04__s_1p0 | 0.270556 | 0.807490 | -0.000008 | -0.000009 | -0.000005 | -0.000017 | 0.674679 | 0.454808 | -0.006995 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_0p65__rpen_0p0__thr_0p14__s_1p0 | 0.270554 | 0.807490 | -0.000010 | -0.000009 | -0.000006 | -0.000017 | 0.666346 | 0.454808 | -0.006664 |
| candidate_ppopt106_stable_adoption__safe_pp81__gain_tail_intent__hpen_0p95__rpen_0p12__thr_0p2 | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000016 | 0.632692 | 0.446474 | -0.005311 |
| candidate_ppopt106_stable_adoption__safe_pp95_op__gain_tail_intent__hpen_0p95__rpen_0p12__thr_0p2 | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000016 | 0.632692 | 0.446474 | -0.005311 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p65__rpen_0p26__thr_0p04__s_1p0 | 0.270554 | 0.807490 | -0.000010 | -0.000009 | -0.000005 | -0.000023 | 0.624359 | 0.454808 | -0.004985 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p85__rpen_0p26__thr_0p0__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000023 | 0.622436 | 0.454808 | -0.004908 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_1p05__rpen_0p18__thr_0p0__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000021 | 0.621795 | 0.454808 | -0.004882 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p85__rpen_0p18__thr_0p04__s_1p0 | 0.270554 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000022 | 0.619231 | 0.454808 | -0.004780 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_1p05__rpen_0p1__thr_0p04__s_1p0 | 0.270554 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000021 | 0.618269 | 0.454808 | -0.004741 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_1p05__rpen_0p0__thr_0p08__s_1p0 | 0.270554 | 0.807490 | -0.000010 | -0.000009 | -0.000005 | -0.000020 | 0.617949 | 0.454808 | -0.004728 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p85__rpen_0p1__thr_0p08__s_1p0 | 0.270554 | 0.807490 | -0.000010 | -0.000009 | -0.000005 | -0.000021 | 0.617308 | 0.454808 | -0.004703 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p65__rpen_0p26__thr_0p08__s_1p0 | 0.270554 | 0.807490 | -0.000010 | -0.000009 | -0.000005 | -0.000025 | 0.615705 | 0.454808 | -0.004639 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p85__rpen_0p26__thr_0p04__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000024 | 0.615064 | 0.454808 | -0.004613 |
| pp102_operational_reference | 0.270555 | 0.807490 | -0.000009 | -0.000009 | -0.000004 | -0.000017 | 0.614423 | 0.454808 | -0.004586 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_1p05__rpen_0p26__thr_0p0__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000024 | 0.612500 | 0.454808 | -0.004511 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_1p05__rpen_0p18__thr_0p04__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000023 | 0.609295 | 0.454808 | -0.004383 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p85__rpen_0p18__thr_0p08__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000024 | 0.608013 | 0.454808 | -0.004331 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p85__rpen_0p0__thr_0p14__s_1p0 | 0.270554 | 0.807490 | -0.000010 | -0.000009 | -0.000004 | -0.000021 | 0.607372 | 0.454808 | -0.004305 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_1p05__rpen_0p1__thr_0p08__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000022 | 0.606410 | 0.454808 | -0.004267 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000005 | -0.000022 | 0.600641 | 0.454808 | -0.004037 |
| candidate_ppopt104_margin_gate__gain_gain75__hpen_0p85__rpen_0p1__thr_0p14__s_1p0 | 0.270553 | 0.807490 | -0.000011 | -0.000009 | -0.000004 | -0.000024 | 0.596795 | 0.454808 | -0.003883 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p28 | 0.270557 | 0.807485 | -0.000007 | -0.000014 | 0.000001 | 0.000007 | 0.492308 | 0.568269 | 0.000303 |
| candidate_ppopt108_tail_hybrid__target_pp95_p95__opthr_0p02__tailthr_0p08__tails_0p28 | 0.270557 | 0.807485 | -0.000007 | -0.000014 | 0.000001 | 0.000007 | 0.491667 | 0.568269 | 0.000329 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | 0.270557 | 0.807482 | -0.000007 | -0.000017 | 0.000002 | 0.000013 | 0.463141 | 0.572115 | 0.001473 |
| pp110_p95_guarded_challenger | 0.270557 | 0.807482 | -0.000007 | -0.000017 | 0.000002 | 0.000013 | 0.463141 | 0.572115 | 0.001473 |
| candidate_ppopt108_tail_hybrid__target_pp95_p95__opthr_0p02__tailthr_0p08__tails_0p4 | 0.270557 | 0.807482 | -0.000007 | -0.000016 | 0.000002 | 0.000013 | 0.462821 | 0.572115 | 0.001486 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p16__tailthr_0p08__tails_0p28 | 0.270559 | 0.807485 | -0.000005 | -0.000014 | 0.000002 | 0.000012 | 0.442628 | 0.568269 | 0.002295 |
| candidate_ppopt108_tail_hybrid__target_pp95_p95__opthr_0p16__tailthr_0p08__tails_0p28 | 0.270559 | 0.807485 | -0.000005 | -0.000014 | 0.000002 | 0.000012 | 0.441346 | 0.568269 | 0.002346 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p1__tailthr_0p08__tails_0p28 | 0.270559 | 0.807485 | -0.000005 | -0.000014 | 0.000002 | 0.000014 | 0.434936 | 0.568269 | 0.002604 |
| candidate_ppopt108_tail_hybrid__target_pp95_p95__opthr_0p1__tailthr_0p08__tails_0p28 | 0.270559 | 0.807485 | -0.000005 | -0.000014 | 0.000002 | 0.000015 | 0.434615 | 0.568269 | 0.002617 |
| candidate_ppopt108_tail_hybrid__target_pp95_p95__opthr_0p06__tailthr_0p08__tails_0p28 | 0.270560 | 0.807485 | -0.000004 | -0.000014 | 0.000003 | 0.000016 | 0.417949 | 0.568269 | 0.003285 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p06__tailthr_0p08__tails_0p28 | 0.270560 | 0.807485 | -0.000004 | -0.000014 | 0.000003 | 0.000016 | 0.417308 | 0.568269 | 0.003310 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p06__tailthr_0p08__tails_0p4 | 0.270560 | 0.807482 | -0.000004 | -0.000017 | 0.000005 | 0.000024 | 0.395192 | 0.572115 | 0.004199 |
| candidate_ppopt108_tail_hybrid__target_pp95_p95__opthr_0p06__tailthr_0p08__tails_0p4 | 0.270560 | 0.807482 | -0.000004 | -0.000016 | 0.000005 | 0.000024 | 0.394872 | 0.572115 | 0.004212 |
| candidate_ppopt108_tail_hybrid__target_pp102_p95__opthr_0p02__tailthr_0p08__tails_0p4 | 0.270561 | 0.807485 | -0.000003 | -0.000014 | 0.000005 | 0.000015 | 0.394231 | 0.588462 | 0.004236 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p16__tailthr_0p08__tails_0p4 | 0.270561 | 0.807482 | -0.000003 | -0.000017 | 0.000006 | 0.000027 | 0.376603 | 0.572115 | 0.004945 |
| candidate_ppopt108_tail_hybrid__target_pp95_p95__opthr_0p16__tailthr_0p08__tails_0p4 | 0.270561 | 0.807482 | -0.000003 | -0.000016 | 0.000006 | 0.000027 | 0.376282 | 0.572115 | 0.004958 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p1__tailthr_0p08__tails_0p4 | 0.270561 | 0.807482 | -0.000003 | -0.000017 | 0.000006 | 0.000029 | 0.366346 | 0.572115 | 0.005356 |
| candidate_ppopt108_tail_hybrid__target_pp95_p95__opthr_0p1__tailthr_0p08__tails_0p4 | 0.270561 | 0.807482 | -0.000003 | -0.000016 | 0.000006 | 0.000029 | 0.366346 | 0.572115 | 0.005356 |
| pp82_operational_reference | 0.270557 | 0.807450 | -0.000007 | -0.000049 | 0.000018 | 0.000050 | 0.362179 | 0.477244 | 0.005532 |
| pp82_p95_reference | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000082 | 0.000179 | 0.056090 | 0.603846 | 0.017948 |
| pp95_p95_reference | 0.270651 | 0.806840 | 0.000087 | -0.000659 | 0.000083 | 0.000178 | 0.055128 | 0.603846 | 0.017986 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.020000 |
| pp102_p95_reference | 0.270927 | 0.806859 | 0.000363 | -0.000640 | 0.000324 | 0.000610 | 0.003846 | 0.461218 | 0.020584 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.000748 | 0.001946 | 0.002244 | 0.450641 | 0.022238 |
| hcoef_stable_source | 0.272989 | 0.806366 | 0.002425 | -0.001133 | 0.002013 | 0.005297 | 0.002244 | 0.403526 | 0.025195 |

## 선택 후보 시나리오별 안정성
| candidate_label | eval_split | scenario | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | test | artist_group_holdout | -0.000009 | -0.000004 | 0.992308 | 0.326923 | 0.126923 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | test | confidence_stratified_rows | -0.000009 | -0.000003 | 0.992308 | 0.442308 | 0.111538 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | test | full_split | -0.000009 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | test | price_band_stratified_rows | -0.000009 | -0.000003 | 1.000000 | 0.376923 | 0.115385 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | test | risk_focus_bootstrap | -0.000018 | -0.000044 | 0.950000 | 0.223077 | 0.019231 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | test | row_bootstrap | -0.000009 | -0.000018 | 0.934615 | 0.350000 | 0.069231 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | validation_oof | artist_group_holdout | -0.000000 | -0.000042 | 0.507692 | 0.480769 | 0.057692 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | validation_oof | confidence_stratified_rows | -0.000000 | -0.000020 | 0.500000 | 0.384615 | 0.065385 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | validation_oof | full_split | -0.000000 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | validation_oof | price_band_stratified_rows | -0.000001 | -0.000034 | 0.542308 | 0.446154 | 0.076923 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | validation_oof | risk_focus_bootstrap | -0.000000 | 0.000031 | 0.476923 | 0.046154 | 0.003846 |
| candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0 | validation_oof | row_bootstrap | 0.000000 | -0.000027 | 0.488462 | 0.380769 | 0.050000 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | test | artist_group_holdout | -0.000007 | 0.000058 | 0.869231 | 0.515385 | 0.234615 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | test | confidence_stratified_rows | -0.000007 | 0.000060 | 0.876923 | 0.488462 | 0.188462 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | test | full_split | -0.000007 | -0.000017 | 1.000000 | 1.000000 | 0.000000 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | test | price_band_stratified_rows | -0.000007 | 0.000068 | 0.934615 | 0.388462 | 0.184615 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | test | risk_focus_bootstrap | -0.000021 | 0.000098 | 0.823077 | 0.280769 | 0.100000 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | test | row_bootstrap | -0.000008 | 0.000046 | 0.746154 | 0.426923 | 0.130769 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | validation_oof | artist_group_holdout | 0.000011 | -0.000050 | 0.030769 | 0.688462 | 0.003846 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | validation_oof | confidence_stratified_rows | 0.000011 | -0.000029 | 0.034615 | 0.634615 | 0.011538 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | validation_oof | full_split | 0.000011 | -0.000025 | 0.000000 | 1.000000 | 0.000000 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | validation_oof | price_band_stratified_rows | 0.000010 | -0.000043 | 0.038462 | 0.696154 | 0.003846 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | validation_oof | risk_focus_bootstrap | 0.000027 | 0.000022 | 0.061538 | 0.242308 | 0.007692 |
| candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4 | validation_oof | row_bootstrap | 0.000011 | -0.000032 | 0.142308 | 0.503846 | 0.030769 |
| pp102_operational_reference | test | artist_group_holdout | -0.000009 | -0.000004 | 0.973077 | 0.326923 | 0.126923 |
| pp102_operational_reference | test | confidence_stratified_rows | -0.000009 | -0.000003 | 0.976923 | 0.442308 | 0.111538 |
| pp102_operational_reference | test | full_split | -0.000009 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp102_operational_reference | test | price_band_stratified_rows | -0.000009 | -0.000003 | 0.984615 | 0.376923 | 0.115385 |
| pp102_operational_reference | test | risk_focus_bootstrap | -0.000025 | -0.000044 | 0.969231 | 0.223077 | 0.019231 |
| pp102_operational_reference | test | row_bootstrap | -0.000009 | -0.000018 | 0.900000 | 0.350000 | 0.069231 |
| pp102_operational_reference | validation_oof | artist_group_holdout | 0.000003 | -0.000043 | 0.250000 | 0.480769 | 0.030769 |
| pp102_operational_reference | validation_oof | confidence_stratified_rows | 0.000003 | -0.000021 | 0.319231 | 0.384615 | 0.034615 |
| pp102_operational_reference | validation_oof | full_split | 0.000003 | -0.000025 | 0.000000 | 1.000000 | 0.000000 |
| pp102_operational_reference | validation_oof | price_band_stratified_rows | 0.000002 | -0.000034 | 0.315385 | 0.446154 | 0.046154 |
| pp102_operational_reference | validation_oof | risk_focus_bootstrap | 0.000010 | 0.000031 | 0.311538 | 0.046154 | 0.000000 |
| pp102_operational_reference | validation_oof | row_bootstrap | 0.000003 | -0.000027 | 0.373077 | 0.380769 | 0.038462 |
| pp81_stable_reference | test | artist_group_holdout | -0.000005 | -0.000002 | 0.996154 | 0.319231 | 0.119231 |
| pp81_stable_reference | test | confidence_stratified_rows | -0.000005 | -0.000001 | 0.996154 | 0.434615 | 0.100000 |
| pp81_stable_reference | test | full_split | -0.000005 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp81_stable_reference | test | price_band_stratified_rows | -0.000005 | -0.000003 | 0.996154 | 0.376923 | 0.115385 |
| pp81_stable_reference | test | risk_focus_bootstrap | -0.000008 | -0.000184 | 0.880769 | 0.338462 | 0.007692 |
| pp81_stable_reference | test | row_bootstrap | -0.000005 | -0.000014 | 0.953846 | 0.330769 | 0.065385 |
| pp81_stable_reference | validation_oof | artist_group_holdout | -0.000002 | 0.000002 | 0.803846 | 0.280769 | 0.092308 |
| pp81_stable_reference | validation_oof | confidence_stratified_rows | -0.000002 | 0.000003 | 0.911538 | 0.288462 | 0.115385 |
| pp81_stable_reference | validation_oof | full_split | -0.000002 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp81_stable_reference | validation_oof | price_band_stratified_rows | -0.000002 | 0.000000 | 0.880769 | 0.319231 | 0.076923 |
| pp81_stable_reference | validation_oof | risk_focus_bootstrap | -0.000001 | 0.000048 | 0.569231 | 0.000000 | 0.000000 |
| pp81_stable_reference | validation_oof | row_bootstrap | -0.000002 | 0.000012 | 0.700000 | 0.234615 | 0.057692 |
| pp95_operational_reference | test | artist_group_holdout | -0.000005 | -0.000002 | 0.996154 | 0.319231 | 0.119231 |
| pp95_operational_reference | test | confidence_stratified_rows | -0.000005 | -0.000001 | 0.996154 | 0.434615 | 0.100000 |
| pp95_operational_reference | test | full_split | -0.000005 | -0.000009 | 1.000000 | 1.000000 | 0.000000 |
| pp95_operational_reference | test | price_band_stratified_rows | -0.000005 | -0.000003 | 0.996154 | 0.376923 | 0.115385 |
| pp95_operational_reference | test | risk_focus_bootstrap | -0.000008 | -0.000184 | 0.880769 | 0.338462 | 0.007692 |
| pp95_operational_reference | test | row_bootstrap | -0.000005 | -0.000014 | 0.953846 | 0.330769 | 0.065385 |
| pp95_operational_reference | validation_oof | artist_group_holdout | -0.000002 | 0.000002 | 0.803846 | 0.280769 | 0.092308 |
| pp95_operational_reference | validation_oof | confidence_stratified_rows | -0.000002 | 0.000003 | 0.911538 | 0.288462 | 0.115385 |
| pp95_operational_reference | validation_oof | full_split | -0.000002 | -0.000025 | 1.000000 | 1.000000 | 0.000000 |
| pp95_operational_reference | validation_oof | price_band_stratified_rows | -0.000002 | 0.000000 | 0.880769 | 0.319231 | 0.076923 |
| pp95_operational_reference | validation_oof | risk_focus_bootstrap | -0.000001 | 0.000048 | 0.569231 | 0.000000 | 0.000000 |
| pp95_operational_reference | validation_oof | row_bootstrap | -0.000002 | 0.000012 | 0.700000 | 0.234615 | 0.057692 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT103-110",
  "experiment_slug": "PP-OPT103_110_warm_pp102_guard_refinement_experiments",
  "created_at": "2026-06-09T14:30:37",
  "seed": 20260609,
  "base_candidate": "hcoef_stable",
  "incumbent_candidate": "incumbent_operational_pp_opt7",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1778,
  "prediction_rows": 2002028,
  "selected_references": {
    "pp64": "reference_pp64_current_best",
    "pp70": "reference_pp70_refinement",
    "pp81": "reference_pp81_best",
    "pp82_op": "reference_pp82_operational",
    "pp82_p95": "reference_pp82_p95",
    "pp95_op": "reference_pp95_operational",
    "pp95_p95": "reference_pp95_p95",
    "pp102_op": "ppopt102_operational_label_refined_tail_challenger__source=ppopt96_best_gain__helper_prob_weighted_tail80__prob_best_gain_tail75__thr_0p32__width_0p18__s_0p46",
    "pp102_p95": "ppopt102_p95_label_refined_tail_challenger__source=ppopt96_best_gain__helper_pp20__prob_best_gain_any__thr_0p08__width_0p18__s_0p64"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0",
    "operational_candidate": "ppopt104_margin_gate__gain=gain_any__hpen=1p05__rpen=0p0__thr=0p14__s=1p0",
    "operational_fixed_test_MAPE": 0.2705553325774607,
    "operational_fixed_test_p95_APE": 0.8074900608978479,
    "operational_delta_vs_pp64_MAPE": -8.7093381996306e-06,
    "operational_delta_vs_pp64_p95_APE": -8.791408261932254e-06,
    "operational_avg_pp64_MAPE_win_rate": 0.782051282051282,
    "operational_avg_pp64_p95_win_rate": 0.4548076923076923,
    "operational_replacement_score": -0.011290760620250914,
    "p95_label": "candidate_ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4",
    "p95_candidate": "ppopt108_tail_hybrid__target=pp82_p95__opthr=0p02__tailthr=0p08__tails=0p4",
    "p95_fixed_test_MAPE": 0.2705572317653208,
    "p95_fixed_test_p95_APE": 0.8074823515298154,
    "p95_delta_vs_pp64_MAPE": -6.8101503395423535e-06,
    "p95_delta_vs_pp64_p95_APE": -1.6500776294448016e-05,
    "p95_avg_pp64_MAPE_win_rate": 0.4631410256410256,
    "p95_avg_pp64_p95_win_rate": 0.5721153846153846,
    "p95_replacement_score": 0.0014731835639919125,
    "operational_protocol_candidate": "ppopt110_operational_guarded_pp102_challenger__source=ppopt104_margin_gate__gain_gain_any__hpen_1p05__rpen_0p0__thr_0p14__s_1p0",
    "p95_protocol_candidate": "ppopt110_p95_guarded_pp102_challenger__source=ppopt108_tail_hybrid__target_pp82_p95__opthr_0p02__tailthr_0p08__tails_0p4"
  },
  "items": [
    {
      "item_id": "PP-OPT103",
      "priority": "1",
      "title": "PP102 risk-score shrink",
      "description": "기존 risk score가 높은 row에서 PP102 이동량을 PP81/PP95 안정 기준으로 되돌린다."
    },
    {
      "item_id": "PP-OPT104",
      "priority": "2",
      "title": "gain-harm margin gate",
      "description": "개선 확률이 손상 확률과 risk penalty를 충분히 이길 때만 PP102 보정을 허용한다."
    },
    {
      "item_id": "PP-OPT105",
      "priority": "3",
      "title": "risk adaptive correction cap",
      "description": "PP102 보정 로그 이동량을 risk/quantile 폭에 따라 다른 cap으로 제한한다."
    },
    {
      "item_id": "PP-OPT106",
      "priority": "4",
      "title": "stable-baseline gated adoption",
      "description": "PP81/PP95 안정 후보를 기준으로 두고 확률 margin이 충분한 row만 PP102로 이동한다."
    },
    {
      "item_id": "PP-OPT107",
      "priority": "5",
      "title": "risk rollback router",
      "description": "risk가 높거나 harm 확률이 큰 row는 PP102에서 안정 후보로 rollback한다."
    },
    {
      "item_id": "PP-OPT108",
      "priority": "6",
      "title": "tail-purpose hybrid router",
      "description": "운영형 PP102와 p95형 후보를 risk/gain 조건에 따라 제한적으로 섞는다."
    },
    {
      "item_id": "PP-OPT109",
      "priority": "7",
      "title": "stability-score selected challenger",
      "description": "고정 test와 반복 안정성 점수를 함께 사용해 최종 후보를 고른다."
    },
    {
      "item_id": "PP-OPT110",
      "priority": "8",
      "title": "final guarded PP102 decision",
      "description": "선택 후보를 운영형과 p95형으로 복제하고 PP64/PP70/PP81/PP95와 비교한다."
    }
  ],
  "sources": {
    "pp96_config": "experiments/track6/PP-OPT96_102_warm_tail_label_refinement_experiments/artifacts/run_config.json",
    "pp96_predictions": "experiments/track6/PP-OPT96_102_warm_tail_label_refinement_experiments/outputs/candidate_predictions.csv",
    "pp96_label_probabilities": "experiments/track6/PP-OPT96_102_warm_tail_label_refinement_experiments/artifacts/tail_label_probability_detail.csv",
    "pp96_helper": "scripts/track6/run_pp_opt96_102_warm_tail_label_refinement_experiments.py",
    "pp71_validation_helper": "scripts/track6/run_pp_opt71_75_warm_pp70_stability_validation.py"
  }
}
```