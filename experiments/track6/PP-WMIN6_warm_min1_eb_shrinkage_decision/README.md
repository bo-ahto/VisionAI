# PP-WMIN6 Warm min1 EB shrinkage decision 결과

- 작성일: 2026-06-12 22:58
- 데이터 기준: 기존 Warm validation OOF 519건 + fixed test 607건
- 선택 기준: WMIN4와 동일하게 validation 반복 안정성 + validation replacement score
- fixed test: 최종 확인용으로만 기록
- 0604: 사용하지 않음. WMIN5에서 stress 통과 후 본 실험은 기존 비교 기준으로만 수행
- 결론: adopt_candidate: `min1_huber_refit_partial` 선택. validation 0.101568/0.178407/0.571291, fixed test 0.106598/0.239302/0.779196.
- 판단 근거: validation gate를 통과했고 fixed test 확인에서도 기존 PP258 운영 후보보다 MdAPE/MAPE/p95가 모두 낮다.
- 선택 후보 fixed confirmation 통과: `True`

## 1. 후보별 교체 판단
| candidate_label | passes_validation_gate | passes_fixed_confirmation | fixed_validation_MdAPE | fixed_validation_MAPE | fixed_validation_p95_APE | validation_avg_MAPE_win_rate | validation_avg_p95_win_rate | validation_replacement_score | fixed_test_MdAPE | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_MAPE_vs_current_pp258 | fixed_test_delta_p95_vs_current_pp258 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min1_huber_refit_partial | True | True | 0.101568 | 0.178407 | 0.571291 | 0.996795 | 0.980769 | -0.027222 | 0.106598 | 0.239302 | 0.779196 | -0.030586 | -0.028129 |
| min1_eb_huber_refit_partial_k5 | True | True | 0.100735 | 0.178499 | 0.569644 | 0.996154 | 0.979487 | -0.027129 | 0.105082 | 0.239249 | 0.784989 | -0.030639 | -0.022336 |
| min1_eb_huber_refit_partial_k2 | True | True | 0.101795 | 0.178514 | 0.568402 | 0.996154 | 0.981410 | -0.027115 | 0.107634 | 0.238903 | 0.784956 | -0.030986 | -0.022368 |
| min1_eb_huber_refit_partial_k10 | True | True | 0.100809 | 0.178594 | 0.570946 | 0.996154 | 0.978846 | -0.027034 | 0.103407 | 0.239620 | 0.784747 | -0.030269 | -0.022578 |
| min1_eb_huber_refit_partial_k20 | True | True | 0.102016 | 0.178708 | 0.572038 | 0.996795 | 0.978846 | -0.026921 | 0.104960 | 0.239884 | 0.784256 | -0.030004 | -0.023069 |
| min1_eb_huber_refit_partial_k50 | True | True | 0.101764 | 0.178768 | 0.572231 | 0.996795 | 0.978846 | -0.026861 | 0.104639 | 0.239967 | 0.784241 | -0.029921 | -0.023084 |
| min1_eb_70_30_basis_k5 | True | True | 0.106053 | 0.180417 | 0.581692 | 0.996154 | 0.982051 | -0.025211 | 0.108974 | 0.239440 | 0.782871 | -0.030448 | -0.024454 |
| min1_eb_70_30_basis_k2 | True | True | 0.106717 | 0.180430 | 0.587087 | 0.996154 | 0.978846 | -0.025199 | 0.110449 | 0.239273 | 0.782740 | -0.030615 | -0.024585 |
| min1_eb_70_30_basis_k10 | True | True | 0.106809 | 0.180488 | 0.581938 | 0.996154 | 0.985256 | -0.025141 | 0.109066 | 0.239646 | 0.782860 | -0.030242 | -0.024465 |
| min1_eb_70_30_basis_k20 | True | True | 0.107995 | 0.180584 | 0.581866 | 0.996154 | 0.985256 | -0.025045 | 0.108392 | 0.239787 | 0.782566 | -0.030101 | -0.024759 |
| min1_eb_70_30_basis_k50 | True | True | 0.107654 | 0.180620 | 0.581660 | 0.996154 | 0.985256 | -0.025008 | 0.108429 | 0.239802 | 0.782585 | -0.030086 | -0.024739 |
| min1_eb_svc_numeric_reference_k5 | True | True | 0.095444 | 0.185292 | 0.605840 | 0.976282 | 0.909615 | -0.020337 | 0.110578 | 0.252622 | 0.797858 | -0.017267 | -0.009467 |
| min1_eb_svc_numeric_reference_k2 | True | True | 0.095252 | 0.185293 | 0.602709 | 0.975000 | 0.902564 | -0.020336 | 0.108272 | 0.251900 | 0.793060 | -0.017988 | -0.014264 |
| min1_eb_svc_numeric_reference_k10 | True | True | 0.095512 | 0.185467 | 0.606120 | 0.976282 | 0.912179 | -0.020161 | 0.110566 | 0.253401 | 0.802796 | -0.016487 | -0.004529 |
| min1_eb_svc_numeric_reference_k20 | True | True | 0.095481 | 0.185657 | 0.605585 | 0.974359 | 0.910897 | -0.019971 | 0.112023 | 0.253923 | 0.804782 | -0.015965 | -0.002542 |
| min1_eb_svc_numeric_reference_k50 | True | True | 0.095689 | 0.185736 | 0.605253 | 0.973718 | 0.909615 | -0.019892 | 0.111384 | 0.254053 | 0.804790 | -0.015835 | -0.002535 |
| current_pp258_operational_reference | True | True | 0.122707 | 0.205629 | 0.637888 | 0.000000 | 0.000000 | 0.000000 | 0.140976 | 0.269888 | 0.807325 | 0.000000 | 0.000000 |

## 2. WMIN4 선택 후보 대비 변화량
| candidate_label | eval_split | delta_MdAPE_vs_wmin4_selected | delta_MAPE_vs_wmin4_selected | delta_p95_APE_vs_wmin4_selected | delta_RMSE_log_vs_wmin4_selected |
| --- | --- | --- | --- | --- | --- |
| min1_eb_huber_refit_partial_k2 | test | 0.001036 | -0.000399 | 0.005760 | -0.000381 |
| min1_eb_huber_refit_partial_k5 | test | -0.001516 | -0.000053 | 0.005793 | -0.000131 |
| min1_eb_70_30_basis_k2 | test | 0.003851 | -0.000029 | 0.003544 | -0.000812 |
| min1_eb_70_30_basis_k5 | test | 0.002376 | 0.000138 | 0.003675 | -0.000643 |
| min1_eb_huber_refit_partial_k10 | test | -0.003191 | 0.000318 | 0.005551 | 0.000129 |
| min1_eb_70_30_basis_k10 | test | 0.002468 | 0.000344 | 0.003664 | -0.000453 |
| min1_eb_70_30_basis_k20 | test | 0.001794 | 0.000485 | 0.003370 | -0.000377 |
| min1_eb_70_30_basis_k50 | test | 0.001831 | 0.000500 | 0.003389 | -0.000349 |
| min1_eb_huber_refit_partial_k20 | test | -0.001638 | 0.000582 | 0.005060 | 0.000244 |
| min1_eb_huber_refit_partial_k50 | test | -0.001959 | 0.000665 | 0.005045 | 0.000288 |
| min1_eb_svc_numeric_reference_k2 | test | 0.001674 | 0.012598 | 0.013864 | 0.014561 |
| min1_eb_svc_numeric_reference_k5 | test | 0.003981 | 0.013320 | 0.018662 | 0.014991 |
| min1_eb_svc_numeric_reference_k10 | test | 0.003969 | 0.014099 | 0.023600 | 0.015416 |
| min1_eb_svc_numeric_reference_k20 | test | 0.005425 | 0.014621 | 0.025586 | 0.015619 |
| min1_eb_svc_numeric_reference_k50 | test | 0.004786 | 0.014751 | 0.025594 | 0.015689 |
| min1_eb_huber_refit_partial_k5 | validation_oof | -0.000832 | 0.000092 | -0.001647 | 0.000149 |
| min1_eb_huber_refit_partial_k2 | validation_oof | 0.000227 | 0.000107 | -0.002889 | 0.000168 |
| min1_eb_huber_refit_partial_k10 | validation_oof | -0.000759 | 0.000187 | -0.000346 | 0.000150 |
| min1_eb_huber_refit_partial_k20 | validation_oof | 0.000448 | 0.000301 | 0.000747 | 0.000164 |
| min1_eb_huber_refit_partial_k50 | validation_oof | 0.000196 | 0.000361 | 0.000940 | 0.000161 |
| min1_eb_70_30_basis_k5 | validation_oof | 0.004485 | 0.002010 | 0.010401 | 0.002275 |
| min1_eb_70_30_basis_k2 | validation_oof | 0.005149 | 0.002023 | 0.015796 | 0.002333 |
| min1_eb_70_30_basis_k10 | validation_oof | 0.005242 | 0.002081 | 0.010647 | 0.002258 |
| min1_eb_70_30_basis_k20 | validation_oof | 0.006428 | 0.002177 | 0.010575 | 0.002258 |
| min1_eb_70_30_basis_k50 | validation_oof | 0.006086 | 0.002213 | 0.010369 | 0.002247 |
| min1_eb_svc_numeric_reference_k5 | validation_oof | -0.006124 | 0.006884 | 0.034548 | 0.016732 |
| min1_eb_svc_numeric_reference_k2 | validation_oof | -0.006316 | 0.006886 | 0.031418 | 0.016737 |
| min1_eb_svc_numeric_reference_k10 | validation_oof | -0.006056 | 0.007060 | 0.034829 | 0.016780 |
| min1_eb_svc_numeric_reference_k20 | validation_oof | -0.006087 | 0.007250 | 0.034294 | 0.016848 |
| min1_eb_svc_numeric_reference_k50 | validation_oof | -0.005879 | 0.007329 | 0.033962 | 0.016882 |

## 3. fixed validation/test 지표
| candidate_label | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_current_pp258_MAPE | delta_vs_current_pp258_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min1_eb_huber_refit_partial_k2 | test | 607 | 0.107634 | 0.238903 | 0.784956 | 0.376503 | -0.030986 | -0.022368 |
| min1_eb_huber_refit_partial_k5 | test | 607 | 0.105082 | 0.239249 | 0.784989 | 0.376753 | -0.030639 | -0.022336 |
| min1_eb_70_30_basis_k2 | test | 607 | 0.110449 | 0.239273 | 0.782740 | 0.376071 | -0.030615 | -0.024585 |
| min1_huber_refit_partial | test | 607 | 0.106598 | 0.239302 | 0.779196 | 0.376884 | -0.030586 | -0.028129 |
| min1_eb_70_30_basis_k5 | test | 607 | 0.108974 | 0.239440 | 0.782871 | 0.376240 | -0.030448 | -0.024454 |
| min1_eb_huber_refit_partial_k10 | test | 607 | 0.103407 | 0.239620 | 0.784747 | 0.377013 | -0.030269 | -0.022578 |
| min1_eb_70_30_basis_k10 | test | 607 | 0.109066 | 0.239646 | 0.782860 | 0.376431 | -0.030242 | -0.024465 |
| min1_eb_70_30_basis_k20 | test | 607 | 0.108392 | 0.239787 | 0.782566 | 0.376507 | -0.030101 | -0.024759 |
| min1_eb_70_30_basis_k50 | test | 607 | 0.108429 | 0.239802 | 0.782585 | 0.376534 | -0.030086 | -0.024739 |
| min1_eb_huber_refit_partial_k20 | test | 607 | 0.104960 | 0.239884 | 0.784256 | 0.377128 | -0.030004 | -0.023069 |
| min1_eb_huber_refit_partial_k50 | test | 607 | 0.104639 | 0.239967 | 0.784241 | 0.377172 | -0.029921 | -0.023084 |
| min1_eb_svc_numeric_reference_k2 | test | 607 | 0.108272 | 0.251900 | 0.793060 | 0.391444 | -0.017988 | -0.014264 |
| min1_eb_svc_numeric_reference_k5 | test | 607 | 0.110578 | 0.252622 | 0.797858 | 0.391874 | -0.017267 | -0.009467 |
| min1_eb_svc_numeric_reference_k10 | test | 607 | 0.110566 | 0.253401 | 0.802796 | 0.392300 | -0.016487 | -0.004529 |
| min1_eb_svc_numeric_reference_k20 | test | 607 | 0.112023 | 0.253923 | 0.804782 | 0.392503 | -0.015965 | -0.002542 |
| min1_eb_svc_numeric_reference_k50 | test | 607 | 0.111384 | 0.254053 | 0.804790 | 0.392573 | -0.015835 | -0.002535 |
| current_pp258_operational_reference | test | 607 | 0.140976 | 0.269888 | 0.807325 | 0.397454 | 0.000000 | 0.000000 |
| min1_huber_refit_partial | validation_oof | 519 | 0.101568 | 0.178407 | 0.571291 | 0.297318 | -0.027222 | -0.066597 |
| min1_eb_huber_refit_partial_k5 | validation_oof | 519 | 0.100735 | 0.178499 | 0.569644 | 0.297466 | -0.027129 | -0.068244 |
| min1_eb_huber_refit_partial_k2 | validation_oof | 519 | 0.101795 | 0.178514 | 0.568402 | 0.297486 | -0.027115 | -0.069486 |
| min1_eb_huber_refit_partial_k10 | validation_oof | 519 | 0.100809 | 0.178594 | 0.570946 | 0.297468 | -0.027034 | -0.066943 |
| min1_eb_huber_refit_partial_k20 | validation_oof | 519 | 0.102016 | 0.178708 | 0.572038 | 0.297481 | -0.026921 | -0.065850 |
| min1_eb_huber_refit_partial_k50 | validation_oof | 519 | 0.101764 | 0.178768 | 0.572231 | 0.297479 | -0.026861 | -0.065657 |
| min1_eb_70_30_basis_k5 | validation_oof | 519 | 0.106053 | 0.180417 | 0.581692 | 0.299593 | -0.025211 | -0.056196 |
| min1_eb_70_30_basis_k2 | validation_oof | 519 | 0.106717 | 0.180430 | 0.587087 | 0.299650 | -0.025199 | -0.050801 |
| min1_eb_70_30_basis_k10 | validation_oof | 519 | 0.106809 | 0.180488 | 0.581938 | 0.299575 | -0.025141 | -0.055950 |
| min1_eb_70_30_basis_k20 | validation_oof | 519 | 0.107995 | 0.180584 | 0.581866 | 0.299575 | -0.025045 | -0.056022 |
| min1_eb_70_30_basis_k50 | validation_oof | 519 | 0.107654 | 0.180620 | 0.581660 | 0.299565 | -0.025008 | -0.056228 |
| min1_eb_svc_numeric_reference_k5 | validation_oof | 519 | 0.095444 | 0.185292 | 0.605840 | 0.314050 | -0.020337 | -0.032048 |
| min1_eb_svc_numeric_reference_k2 | validation_oof | 519 | 0.095252 | 0.185293 | 0.602709 | 0.314055 | -0.020336 | -0.035179 |
| min1_eb_svc_numeric_reference_k10 | validation_oof | 519 | 0.095512 | 0.185467 | 0.606120 | 0.314097 | -0.020161 | -0.031768 |
| min1_eb_svc_numeric_reference_k20 | validation_oof | 519 | 0.095481 | 0.185657 | 0.605585 | 0.314165 | -0.019971 | -0.032303 |
| min1_eb_svc_numeric_reference_k50 | validation_oof | 519 | 0.095689 | 0.185736 | 0.605253 | 0.314200 | -0.019892 | -0.032635 |
| current_pp258_operational_reference | validation_oof | 519 | 0.122707 | 0.205629 | 0.637888 | 0.323337 | 0.000000 | 0.000000 |

## 4. EB SVC와 70:30 기준가 자체 지표
| candidate_label | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_current_pp258_MAPE | delta_vs_current_pp258_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min1_eb_70_30_basis_k10 | test | 607 | 0.109066 | 0.239646 | 0.782860 | 0.376431 | -0.030242 | -0.024465 |
| min1_eb_70_30_basis_k2 | test | 607 | 0.110449 | 0.239273 | 0.782740 | 0.376071 | -0.030615 | -0.024585 |
| min1_eb_70_30_basis_k20 | test | 607 | 0.108392 | 0.239787 | 0.782566 | 0.376507 | -0.030101 | -0.024759 |
| min1_eb_70_30_basis_k5 | test | 607 | 0.108974 | 0.239440 | 0.782871 | 0.376240 | -0.030448 | -0.024454 |
| min1_eb_70_30_basis_k50 | test | 607 | 0.108429 | 0.239802 | 0.782585 | 0.376534 | -0.030086 | -0.024739 |
| min1_eb_svc_numeric_reference_k10 | test | 607 | 0.110566 | 0.253401 | 0.802796 | 0.392300 | -0.016487 | -0.004529 |
| min1_eb_svc_numeric_reference_k2 | test | 607 | 0.108272 | 0.251900 | 0.793060 | 0.391444 | -0.017988 | -0.014264 |
| min1_eb_svc_numeric_reference_k20 | test | 607 | 0.112023 | 0.253923 | 0.804782 | 0.392503 | -0.015965 | -0.002542 |
| min1_eb_svc_numeric_reference_k5 | test | 607 | 0.110578 | 0.252622 | 0.797858 | 0.391874 | -0.017267 | -0.009467 |
| min1_eb_svc_numeric_reference_k50 | test | 607 | 0.111384 | 0.254053 | 0.804790 | 0.392573 | -0.015835 | -0.002535 |
| min1_eb_70_30_basis_k10 | validation_oof | 519 | 0.106809 | 0.180488 | 0.581938 | 0.299575 | -0.025141 | -0.055950 |
| min1_eb_70_30_basis_k2 | validation_oof | 519 | 0.106717 | 0.180430 | 0.587087 | 0.299650 | -0.025199 | -0.050801 |
| min1_eb_70_30_basis_k20 | validation_oof | 519 | 0.107995 | 0.180584 | 0.581866 | 0.299575 | -0.025045 | -0.056022 |
| min1_eb_70_30_basis_k5 | validation_oof | 519 | 0.106053 | 0.180417 | 0.581692 | 0.299593 | -0.025211 | -0.056196 |
| min1_eb_70_30_basis_k50 | validation_oof | 519 | 0.107654 | 0.180620 | 0.581660 | 0.299565 | -0.025008 | -0.056228 |
| min1_eb_svc_numeric_reference_k10 | validation_oof | 519 | 0.095512 | 0.185467 | 0.606120 | 0.314097 | -0.020161 | -0.031768 |
| min1_eb_svc_numeric_reference_k2 | validation_oof | 519 | 0.095252 | 0.185293 | 0.602709 | 0.314055 | -0.020336 | -0.035179 |
| min1_eb_svc_numeric_reference_k20 | validation_oof | 519 | 0.095481 | 0.185657 | 0.605585 | 0.314165 | -0.019971 | -0.032303 |
| min1_eb_svc_numeric_reference_k5 | validation_oof | 519 | 0.095444 | 0.185292 | 0.605840 | 0.314050 | -0.020337 | -0.032048 |
| min1_eb_svc_numeric_reference_k50 | validation_oof | 519 | 0.095689 | 0.185736 | 0.605253 | 0.314200 | -0.019892 | -0.032635 |

## 5. 선택 후보 반복 validation 시나리오
| candidate_label | scenario | mean_MdAPE | mean_MAPE | mean_p95_APE | current_pp258_MAPE_win_rate | current_pp258_p95_win_rate | current_pp258_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| min1_huber_refit_partial | artist_group_holdout | 0.100372 | 0.178079 | 0.568536 | 1.000000 | 0.988462 | 0.988462 |
| min1_huber_refit_partial | confidence_stratified_rows | 0.100436 | 0.177661 | 0.569253 | 1.000000 | 0.992308 | 0.992308 |
| min1_huber_refit_partial | full_validation | 0.101568 | 0.178407 | 0.571291 | 1.000000 | 1.000000 | 1.000000 |
| min1_huber_refit_partial | price_band_stratified_rows | 0.100793 | 0.179072 | 0.572879 | 1.000000 | 0.996154 | 0.996154 |
| min1_huber_refit_partial | risk_focus_bootstrap | 0.122476 | 0.210901 | 0.671301 | 0.980769 | 0.988462 | 0.900000 |
| min1_huber_refit_partial | row_bootstrap | 0.100985 | 0.177626 | 0.571172 | 1.000000 | 0.919231 | 0.915385 |

## 6. 실행 설정
```json
{
  "experiment_id": "PP-WMIN6",
  "experiment_slug": "PP-WMIN6_warm_min1_eb_shrinkage_decision",
  "created_at": "2026-06-12T22:58:55",
  "selection_policy": "validation repeated stability and validation replacement score only; fixed test is confirmation; 0604 is not used",
  "reference_candidate_label": "current_pp258_operational_reference",
  "wmin4_selected_candidate_label": "min1_huber_refit_partial",
  "k_grid": [
    2,
    5,
    10,
    20,
    50
  ],
  "seeds": [
    202606030,
    202606031,
    202606032,
    202606033,
    202606034,
    202606035,
    202606036,
    202606037,
    202606038,
    202606039
  ],
  "median_replacement": "replace only svc_group_log_price_median with hierarchical empirical-Bayes shrunk median",
  "eb_formula": "shrunk = n/(n+k)*group_median + k/(n+k)*parent_estimate, applied from global -> artist -> artist+size -> artist+medium/support+size",
  "basis_formula": "min1_eb_70_30_basis = 0.70 * min1_eb_svc_numeric_seed_mean + 0.30 * pp_v8_compact_blend_mape_guarded",
  "huber_refit": {
    "mode": "WMIN3 partial",
    "current_70_30": "EB 70:30 basis",
    "svc_fallback": "EB SVC seed mean",
    "stable_config": {
      "candidate": "hcoef2_size_reliability_cap005_s050",
      "source_candidate": "residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50",
      "feature_key": "resid_basis_size_reliability",
      "alpha": 0.01,
      "cap": 0.05,
      "strength": 0.5,
      "purpose": "작은 폭 MAPE/p95 안정화 대안"
    }
  },
  "decision": {
    "decision_status": "adopt_candidate",
    "selected_candidate_label": "min1_huber_refit_partial",
    "reason": "validation gate를 통과했고 fixed test 확인에서도 기존 PP258 운영 후보보다 MdAPE/MAPE/p95가 모두 낮다.",
    "selected_fixed_validation_MdAPE": 0.10156770146068649,
    "selected_fixed_validation_MAPE": 0.17840703537366578,
    "selected_fixed_validation_p95_APE": 0.5712913918014471,
    "selected_fixed_test_MdAPE": 0.10659775415481275,
    "selected_fixed_test_MAPE": 0.23930208581696472,
    "selected_fixed_test_p95_APE": 0.7791959634055454,
    "selected_validation_MAPE_win_rate": 0.9967948717948718,
    "selected_validation_p95_win_rate": 0.9807692307692308,
    "selected_validation_replacement_score": -0.027221524605975767
  }
}
```
