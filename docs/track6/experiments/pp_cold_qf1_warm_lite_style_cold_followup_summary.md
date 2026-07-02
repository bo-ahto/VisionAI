# PP-COLD-QF1 Warm-lite style Cold follow-up

## 목적
- 새 Warm-lite에서 효과가 있었던 `full/lean Quantile`, `clip 잔차 보정`, `불일치 기반 tail guard`를 Cold에 맞게 검증했다.
- Cold는 같은 작가 가격 이력이 없으므로 작가 이력 대신 작품 피처와 작가 미사용 비교군 그룹 통계를 사용했다.
- 기준선은 두 개다: raw-input 후보끼리는 `qf1_full_lean_avg`, 최종 Cold 교체/추가 후보는 `current_v03_research_guard_search`다.
- threshold와 후보 순위는 validation에서만 정하고 fixed test는 확인용으로만 보고했다.

## 실험 설계
- full Quantile: 기존 Cold LightGBM 12피처 + medium_support_bucket + 작가 미사용 그룹 통계 full + grp_price_proxy.
- lean Quantile: log_area/aspect/depth/medium/support/size + 그룹 통계 lean + grp_price_proxy.
- residual: train 5-fold OOF `actual_log - full_lean_avg`를 HuberRegressor로 학습하고, 적용 시 clip cap을 둔다.
- qf1 guard: full/lean 예측 차이와 full Quantile qwidth가 큰 행에서 lower(q50_full, q50_lean) 방향으로 이동한다.
- v0.3 hybrid: 현행 v0.3 예측이 qf1 평균보다 높고 qwidth/gap이 큰 행만 qf1 쪽으로 작게 내린다.

## 주요 기준선과 선택 후보 test 결과
| candidate | MdAPE | MAPE | p95_APE | RMSE_log | within_30 | over_50pct_error_rate | delta_MAPE_vs_v03 | delta_p95_vs_v03 | delta_MdAPE_vs_v03 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_v03_research_guard_search | 0.409820 | 0.849260 | 2.346465 | 0.850259 | 0.374314 | 0.415295 | 0.000000 | 0.000000 | 0.000000 |
| current_v03_guard_only | 0.417765 | 0.963963 | 2.537708 | 0.869143 | 0.346886 | 0.424653 | 0.114703 | 0.191242 | 0.007945 |
| current_y18_qwidth_base | 0.424663 | 0.991042 | 3.305298 | 0.857474 | 0.346241 | 0.422072 | 0.141782 | 0.958832 | 0.014843 |
| current_v02_defense | 0.485162 | 1.177120 | 4.122299 | 0.937146 | 0.287512 | 0.481446 | 0.327860 | 1.775834 | 0.075342 |
| qf1_full_q50 | 0.493332 | 1.282713 | 4.442776 | 0.945301 | 0.276541 | 0.490158 | 0.433453 | 2.096310 | 0.083512 |
| qf1_lean_q50 | 0.488125 | 1.200580 | 3.927830 | 0.925868 | 0.299129 | 0.487899 | 0.351320 | 1.581365 | 0.078305 |
| qf1_full_lean_avg | 0.488673 | 1.200943 | 3.949554 | 0.926607 | 0.278477 | 0.482091 | 0.351683 | 1.603089 | 0.078853 |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q50_w0.75 | 0.491939 | 1.152026 | 3.695348 | 0.918783 | 0.278154 | 0.484350 | 0.302766 | 1.348883 | 0.082119 |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q67_w0.75 | 0.488972 | 1.155432 | 3.696499 | 0.918404 | 0.280090 | 0.482091 | 0.306172 | 1.350034 | 0.079152 |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q80_w0.75 | 0.486959 | 1.161237 | 3.696499 | 0.918089 | 0.279445 | 0.478864 | 0.311977 | 1.350034 | 0.077139 |
| qf1_avg_full_lean_lower_guard_width_q67_gap_q50_w0.75 | 0.490433 | 1.161796 | 3.756261 | 0.920316 | 0.276541 | 0.483382 | 0.312536 | 1.409796 | 0.080613 |
| qf1_avg_full_lean_lower_guard_width_q67_gap_q67_w0.75 | 0.488676 | 1.163804 | 3.756261 | 0.919905 | 0.277832 | 0.480478 | 0.314544 | 1.409796 | 0.078856 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q50_w0.5_cap0.1 | 0.413664 | 0.846852 | 2.211440 | 0.853394 | 0.369151 | 0.418199 | -0.002408 | -0.135025 | 0.003844 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q67_w0.5_cap0.1 | 0.413664 | 0.846883 | 2.211440 | 0.853357 | 0.369151 | 0.418199 | -0.002377 | -0.135025 | 0.003844 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q50_w0.35_cap0.1 | 0.413055 | 0.847171 | 2.211440 | 0.853071 | 0.370442 | 0.417554 | -0.002089 | -0.135025 | 0.003235 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q67_w0.35_cap0.1 | 0.413055 | 0.847193 | 2.211440 | 0.853045 | 0.370442 | 0.417554 | -0.002067 | -0.135025 | 0.003235 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q80_w0.5_cap0.1 | 0.412957 | 0.847431 | 2.211440 | 0.852727 | 0.369797 | 0.417877 | -0.001829 | -0.135025 | 0.003137 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q80_w0.35_cap0.1 | 0.412921 | 0.847582 | 2.211440 | 0.852616 | 0.370765 | 0.417554 | -0.001678 | -0.135025 | 0.003101 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q50_w0.5_cap0.075 | 0.413664 | 0.847231 | 2.211440 | 0.852711 | 0.370119 | 0.417231 | -0.002029 | -0.135025 | 0.003844 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q67_w0.5_cap0.075 | 0.413664 | 0.847262 | 2.211440 | 0.852674 | 0.370119 | 0.417231 | -0.001998 | -0.135025 | 0.003844 |

## qf1 내부 validation 상위 후보
| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q50_w0.75 | 0.418288 | 0.661192 | 1.854308 | -0.009448 | -0.081179 | -0.240925 | -0.165502 |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q67_w0.75 | 0.417532 | 0.664469 | 1.860605 | -0.010203 | -0.077902 | -0.234628 | -0.160021 |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q80_w0.75 | 0.418288 | 0.667914 | 1.874925 | -0.009448 | -0.074457 | -0.220308 | -0.151565 |
| qf1_avg_full_lean_lower_guard_width_q67_gap_q50_w0.75 | 0.418845 | 0.671535 | 1.874925 | -0.008890 | -0.070836 | -0.220308 | -0.147944 |
| qf1_avg_full_lean_lower_guard_width_q67_gap_q67_w0.75 | 0.417814 | 0.673663 | 1.874925 | -0.009922 | -0.068708 | -0.220308 | -0.145816 |
| qf1_avg_full_lean_lower_guard_width_q67_gap_q80_w0.75 | 0.417814 | 0.675811 | 1.878040 | -0.009922 | -0.066560 | -0.217193 | -0.142578 |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q50_w0.5 | 0.422325 | 0.683475 | 1.888586 | -0.005411 | -0.058896 | -0.206647 | -0.131222 |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q67_w0.5 | 0.420808 | 0.685677 | 1.893980 | -0.006927 | -0.056693 | -0.201253 | -0.127132 |
| qf1_avg_full_lean_lower_guard_width_q50_gap_q80_w0.5 | 0.421952 | 0.688011 | 1.901602 | -0.005783 | -0.054360 | -0.193631 | -0.122131 |
| qf1_avg_full_lean_lower_guard_width_q67_gap_q50_w0.5 | 0.422462 | 0.690924 | 1.900742 | -0.005273 | -0.051447 | -0.194491 | -0.119519 |
| qf1_avg_full_lean_lower_guard_width_q67_gap_q67_w0.5 | 0.421037 | 0.692354 | 1.900742 | -0.006699 | -0.050017 | -0.194491 | -0.118089 |
| qf1_avg_full_lean_lower_guard_width_q67_gap_q80_w0.5 | 0.421606 | 0.693811 | 1.901853 | -0.006129 | -0.048560 | -0.193380 | -0.116243 |

## v0.3 hybrid validation 상위 후보
| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q50_w0.5_cap0.1 | 0.348970 | 0.493535 | 1.476126 | -0.006308 | -0.004246 | -0.023516 | -0.012477 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q67_w0.5_cap0.1 | 0.348970 | 0.493551 | 1.476126 | -0.006308 | -0.004230 | -0.023516 | -0.012461 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q50_w0.35_cap0.1 | 0.348970 | 0.493910 | 1.476126 | -0.006308 | -0.003872 | -0.023516 | -0.012102 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q67_w0.35_cap0.1 | 0.348970 | 0.493921 | 1.476126 | -0.006308 | -0.003860 | -0.023516 | -0.012091 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q80_w0.5_cap0.1 | 0.348970 | 0.493940 | 1.476126 | -0.006308 | -0.003841 | -0.023516 | -0.012072 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q80_w0.35_cap0.1 | 0.348970 | 0.494196 | 1.476126 | -0.006308 | -0.003585 | -0.023516 | -0.011816 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q50_w0.5_cap0.075 | 0.350081 | 0.494407 | 1.476126 | -0.005196 | -0.003374 | -0.023516 | -0.011605 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q67_w0.5_cap0.075 | 0.350081 | 0.494423 | 1.476126 | -0.005196 | -0.003358 | -0.023516 | -0.011589 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q50_w0.35_cap0.075 | 0.350081 | 0.494611 | 1.476126 | -0.005196 | -0.003170 | -0.023516 | -0.011401 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q67_w0.35_cap0.075 | 0.350081 | 0.494622 | 1.476126 | -0.005196 | -0.003159 | -0.023516 | -0.011390 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q80_w0.5_cap0.075 | 0.350081 | 0.494814 | 1.476126 | -0.005196 | -0.002967 | -0.023516 | -0.011198 |
| v03_down_to_qf1_if_risky_qwidth_q50_gap_to_qf1_q80_w0.35_cap0.075 | 0.350081 | 0.494897 | 1.476126 | -0.005196 | -0.002884 | -0.023516 | -0.011115 |

## 판단 기준
- `qf1_*`가 v0.3보다 좋으면 Cold 자체를 Warm-lite 스타일로 단순화할 가능성이 있다.
- `qf1_*`는 v0.3보다 약하지만 `v03_down_to_qf1_*`가 test MAPE/p95를 낮추면 방어층 추가 가능성이 있다.
- v0.3 기준 test에서 MdAPE/MAPE/p95가 모두 악화되면 현행 Cold 체인을 유지해야 한다.

## 산출물
- 실험 폴더: `experiments/track6/PP-COLD-QF1_warm_lite_style_cold_followup`
- `outputs/candidate_metrics.csv`: 전체 후보 validation/test 지표.
- `outputs/qf1_validation_rank.csv`: qf1 내부 후보 validation 순위.
- `outputs/v03_hybrid_validation_rank.csv`: v0.3 조건부 보정 후보 validation 순위.
- `outputs/selected_candidate_metrics.csv`: 기준선과 상위 후보 비교표.
- `artifacts/run_config.json`: 피처, threshold, residual 학습 설정.