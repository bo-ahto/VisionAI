# OP-V01-CAL-06 유사 작품 기반 예측값 결합 비율 재검증 결과

## 1. 실행 요약

- 기준 후보: PP-V8 compact_blend_mape_guarded
- 비교 방향: 유사 작품 기반 예측값과 PP-V8의 로그 가격 결합
- 후보 선택: historical validation에서 MAPE를 우선하되 MdAPE/p95 악화 제한
- 0604 신규 라벨: 후보 선택에는 사용하지 않고 외부 확인용으로만 사용

핵심 결과:
- historical test PP-V8 기준 MAPE: 0.2816, MdAPE: 0.1632, p95_APE: 0.9311
- validation 선택 후보 중 historical test 최선: cand_global_svc_w0.60 / MAPE 0.2717, MdAPE 0.1362, p95_APE 0.8329
- 0604 50달러 미만 제외 PP-V8 기준 MAPE: 0.3359, MdAPE: 0.2298, p95_APE: 0.9273
- 0604 50달러 미만 제외 단순 스캔 최선: cand_global_svc_w0.20 / MAPE 0.3330, MdAPE 0.2385, p95_APE 0.9122

판단:
- historical split에서는 결합 비율 재조정으로 성능 개선 여지가 있다.
- 0604에서는 PP-V8 단독 또는 PP-V8에 가까운 낮은 결합 비율이 유리한지 확인이 필요하다.
- 따라서 이 실험 결과만으로 v0.1 기본 점가격을 바꾸지 않는다.
- 다음 보정은 전체 결합이 아니라 표본 수/coverage 조건부 결합 후보만 별도 API 후보로 내려 비교하는 방식이 안전하다.

## 2. validation 선택 후보

| candidate | selection_rule | validation_MdAPE | validation_MAPE | validation_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_over_3x_n | test_under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cand_global_svc_w0.75 | validation_mape_with_mdape_p95_guard | 0.1273 | 0.2107 | 0.6234 | 0.1430 | 0.2774 | 0.8669 | 10 | 7 |
| cand_global_svc_w0.70 | validation_mape_with_mdape_p95_guard | 0.1285 | 0.2107 | 0.6541 | 0.1401 | 0.2751 | 0.8351 | 11 | 7 |
| cand_gate_n5_svc_w0.70 | validation_mape_with_mdape_p95_guard | 0.1285 | 0.2107 | 0.6541 | 0.1401 | 0.2751 | 0.8351 | 11 | 7 |
| cand_gate_n5_covok_svc_w0.70 | validation_mape_with_mdape_p95_guard | 0.1285 | 0.2107 | 0.6541 | 0.1401 | 0.2751 | 0.8351 | 11 | 7 |
| cand_global_svc_w0.80 | validation_mape_with_mdape_p95_guard | 0.1249 | 0.2112 | 0.6252 | 0.1430 | 0.2802 | 0.9075 | 10 | 7 |
| cand_gate_n5_svc_w0.80 | validation_mape_with_mdape_p95_guard | 0.1249 | 0.2112 | 0.6252 | 0.1430 | 0.2802 | 0.9075 | 10 | 7 |
| cand_gate_n5_covok_svc_w0.80 | validation_mape_with_mdape_p95_guard | 0.1249 | 0.2112 | 0.6252 | 0.1430 | 0.2802 | 0.9075 | 10 | 7 |
| cand_global_svc_w0.65 | validation_mape_with_mdape_p95_guard | 0.1367 | 0.2113 | 0.6445 | 0.1382 | 0.2733 | 0.8432 | 11 | 7 |
| cand_global_svc_w0.85 | validation_mape_with_mdape_p95_guard | 0.1200 | 0.2123 | 0.6419 | 0.1425 | 0.2835 | 0.9259 | 10 | 7 |
| cand_global_svc_w0.60 | validation_mape_with_mdape_p95_guard | 0.1362 | 0.2125 | 0.6613 | 0.1362 | 0.2717 | 0.8329 | 10 | 7 |

## 3. 선택 후보 전체 scope 지표

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n | within_30 | within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604:0604_excluding_under_50_usd | cand_ppv8_baseline | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 0.9321 | 4 | 58 | 0.5995 | 0.7901 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.60 | 829 | 0.2618 | 0.3619 | 0.9798 | 1.1932 | 0.9313 | 8 | 78 | 0.5332 | 0.7322 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.65 | 829 | 0.2672 | 0.3693 | 0.9839 | 1.2518 | 0.9346 | 8 | 79 | 0.5296 | 0.7214 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.70 | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.9248 | 8 | 79 | 0.5271 | 0.7141 |
| 0604:0604_excluding_under_50_usd | cand_gate_n5_svc_w0.70 | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.9248 | 8 | 79 | 0.5271 | 0.7141 |
| 0604:0604_excluding_under_50_usd | cand_gate_n5_covok_svc_w0.70 | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.9248 | 8 | 79 | 0.5271 | 0.7141 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.75 | 829 | 0.2803 | 0.3857 | 0.9933 | 1.3728 | 0.9230 | 8 | 82 | 0.5127 | 0.7105 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.80 | 829 | 0.2919 | 0.3942 | 0.9946 | 1.4348 | 0.9209 | 9 | 89 | 0.5115 | 0.7069 |
| 0604:0604_excluding_under_50_usd | cand_gate_n5_svc_w0.80 | 829 | 0.2919 | 0.3942 | 0.9946 | 1.4348 | 0.9209 | 9 | 89 | 0.5115 | 0.7069 |
| 0604:0604_excluding_under_50_usd | cand_gate_n5_covok_svc_w0.80 | 829 | 0.2919 | 0.3942 | 0.9946 | 1.4348 | 0.9209 | 9 | 89 | 0.5115 | 0.7069 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.85 | 829 | 0.2962 | 0.4030 | 0.9978 | 1.4977 | 0.9171 | 10 | 90 | 0.5054 | 0.6996 |
| 0604:0604_excluding_under_50_usd | cand_svc_only | 829 | 0.3072 | 0.4318 | 0.9998 | 1.6906 | 0.9204 | 11 | 108 | 0.4922 | 0.6731 |
| 0604:0604_labeled | cand_ppv8_baseline | 837 | 0.2342 | 14.2852 | 0.9844 | 0.9199 | 0.9341 | 12 | 58 | 0.5938 | 0.7826 |
| 0604:0604_labeled | cand_global_svc_w0.60 | 837 | 0.2642 | 28.5348 | 0.9941 | 1.3384 | 0.9349 | 16 | 78 | 0.5281 | 0.7252 |
| 0604:0604_labeled | cand_global_svc_w0.65 | 837 | 0.2705 | 30.3460 | 0.9979 | 1.3916 | 0.9415 | 16 | 79 | 0.5245 | 0.7145 |
| 0604:0604_labeled | cand_global_svc_w0.70 | 837 | 0.2835 | 32.2879 | 0.9996 | 1.4463 | 0.9295 | 16 | 79 | 0.5221 | 0.7073 |
| 0604:0604_labeled | cand_gate_n5_svc_w0.70 | 837 | 0.2835 | 32.2879 | 0.9996 | 1.4463 | 0.9295 | 16 | 79 | 0.5221 | 0.7073 |
| 0604:0604_labeled | cand_gate_n5_covok_svc_w0.70 | 837 | 0.2835 | 32.2879 | 0.9996 | 1.4463 | 0.9295 | 16 | 79 | 0.5221 | 0.7073 |
| 0604:0604_labeled | cand_global_svc_w0.75 | 837 | 0.2905 | 34.3697 | 1.0000 | 1.5024 | 0.9289 | 16 | 82 | 0.5078 | 0.7037 |
| 0604:0604_labeled | cand_global_svc_w0.80 | 837 | 0.2939 | 36.6018 | 1.0000 | 1.5598 | 0.9263 | 17 | 89 | 0.5066 | 0.7001 |
| 0604:0604_labeled | cand_gate_n5_svc_w0.80 | 837 | 0.2939 | 36.6018 | 1.0000 | 1.5598 | 0.9263 | 17 | 89 | 0.5066 | 0.7001 |
| 0604:0604_labeled | cand_gate_n5_covok_svc_w0.80 | 837 | 0.2939 | 36.6018 | 1.0000 | 1.5598 | 0.9263 | 17 | 89 | 0.5066 | 0.7001 |
| 0604:0604_labeled | cand_global_svc_w0.85 | 837 | 0.2988 | 38.9953 | 1.0000 | 1.6184 | 0.9195 | 18 | 90 | 0.5006 | 0.6930 |
| 0604:0604_labeled | cand_svc_only | 837 | 0.3174 | 47.2697 | 1.0882 | 1.7995 | 0.9254 | 19 | 108 | 0.4875 | 0.6667 |
| historical:test | cand_global_svc_w0.60 | 607 | 0.1362 | 0.2717 | 0.8329 | 0.4003 | 1.0035 | 10 | 7 | 0.7661 | 0.8797 |
| historical:test | cand_global_svc_w0.65 | 607 | 0.1382 | 0.2733 | 0.8432 | 0.4024 | 1.0027 | 11 | 7 | 0.7578 | 0.8764 |
| historical:test | cand_global_svc_w0.70 | 607 | 0.1401 | 0.2751 | 0.8351 | 0.4047 | 1.0005 | 11 | 7 | 0.7611 | 0.8764 |
| historical:test | cand_gate_n5_svc_w0.70 | 607 | 0.1401 | 0.2751 | 0.8351 | 0.4047 | 1.0005 | 11 | 7 | 0.7611 | 0.8764 |
| historical:test | cand_gate_n5_covok_svc_w0.70 | 607 | 0.1401 | 0.2751 | 0.8351 | 0.4047 | 1.0005 | 11 | 7 | 0.7611 | 0.8764 |
| historical:test | cand_global_svc_w0.75 | 607 | 0.1430 | 0.2774 | 0.8669 | 0.4074 | 0.9993 | 10 | 7 | 0.7628 | 0.8731 |
| historical:test | cand_global_svc_w0.80 | 607 | 0.1430 | 0.2802 | 0.9075 | 0.4104 | 1.0011 | 10 | 7 | 0.7628 | 0.8715 |
| historical:test | cand_gate_n5_svc_w0.80 | 607 | 0.1430 | 0.2802 | 0.9075 | 0.4104 | 1.0011 | 10 | 7 | 0.7628 | 0.8715 |
| historical:test | cand_gate_n5_covok_svc_w0.80 | 607 | 0.1430 | 0.2802 | 0.9075 | 0.4104 | 1.0011 | 10 | 7 | 0.7628 | 0.8715 |
| historical:test | cand_ppv8_baseline | 607 | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 0.9966 | 6 | 7 | 0.7364 | 0.8600 |
| historical:test | cand_global_svc_w0.85 | 607 | 0.1425 | 0.2835 | 0.9259 | 0.4137 | 1.0027 | 10 | 7 | 0.7611 | 0.8731 |
| historical:test | cand_svc_only | 607 | 0.1528 | 0.2956 | 0.9694 | 0.4255 | 1.0023 | 12 | 8 | 0.7595 | 0.8666 |
| historical:validation | cand_global_svc_w0.75 | 519 | 0.1273 | 0.2107 | 0.6234 | 0.3316 | 0.9934 | 1 | 5 | 0.7746 | 0.9133 |
| historical:validation | cand_global_svc_w0.70 | 519 | 0.1285 | 0.2107 | 0.6541 | 0.3313 | 0.9973 | 1 | 5 | 0.7746 | 0.9114 |
| historical:validation | cand_gate_n5_svc_w0.70 | 519 | 0.1285 | 0.2107 | 0.6541 | 0.3313 | 0.9973 | 1 | 5 | 0.7746 | 0.9114 |
| historical:validation | cand_gate_n5_covok_svc_w0.70 | 519 | 0.1285 | 0.2107 | 0.6541 | 0.3313 | 0.9973 | 1 | 5 | 0.7746 | 0.9114 |
| historical:validation | cand_global_svc_w0.80 | 519 | 0.1249 | 0.2112 | 0.6252 | 0.3324 | 0.9906 | 1 | 5 | 0.7707 | 0.9114 |
| historical:validation | cand_gate_n5_svc_w0.80 | 519 | 0.1249 | 0.2112 | 0.6252 | 0.3324 | 0.9906 | 1 | 5 | 0.7707 | 0.9114 |
| historical:validation | cand_gate_n5_covok_svc_w0.80 | 519 | 0.1249 | 0.2112 | 0.6252 | 0.3324 | 0.9906 | 1 | 5 | 0.7707 | 0.9114 |
| historical:validation | cand_global_svc_w0.65 | 519 | 0.1367 | 0.2113 | 0.6445 | 0.3314 | 0.9989 | 1 | 5 | 0.7784 | 0.9094 |
| historical:validation | cand_global_svc_w0.85 | 519 | 0.1200 | 0.2123 | 0.6419 | 0.3337 | 0.9886 | 1 | 5 | 0.7649 | 0.9171 |
| historical:validation | cand_global_svc_w0.60 | 519 | 0.1362 | 0.2125 | 0.6613 | 0.3319 | 1.0005 | 1 | 5 | 0.7803 | 0.9094 |
| historical:validation | cand_svc_only | 519 | 0.1212 | 0.2170 | 0.6502 | 0.3402 | 0.9886 | 1 | 5 | 0.7592 | 0.9152 |
| historical:validation | cand_ppv8_baseline | 519 | 0.1544 | 0.2544 | 0.8084 | 0.3721 | 1.0051 | 4 | 4 | 0.7225 | 0.8882 |

## 4. 0604 50달러 미만 제외 상위 후보

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n | within_30 | within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.20 | 829 | 0.2385 | 0.3330 | 0.9122 | 0.8052 | 0.9336 | 6 | 59 | 0.5838 | 0.7744 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.15 | 829 | 0.2396 | 0.3332 | 0.9060 | 0.7731 | 0.9407 | 4 | 61 | 0.5935 | 0.7817 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.10 | 829 | 0.2358 | 0.3339 | 0.8974 | 0.7465 | 0.9401 | 3 | 60 | 0.5983 | 0.7877 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.25 | 829 | 0.2381 | 0.3342 | 0.9068 | 0.8421 | 0.9362 | 7 | 59 | 0.5802 | 0.7744 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.05 | 829 | 0.2284 | 0.3349 | 0.9229 | 0.7261 | 0.9338 | 3 | 58 | 0.5995 | 0.7853 |
| 0604:0604_excluding_under_50_usd | cand_ppv8_baseline | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 0.9321 | 4 | 58 | 0.5995 | 0.7901 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.00 | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 0.9321 | 4 | 58 | 0.5995 | 0.7901 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.30 | 829 | 0.2425 | 0.3361 | 0.9223 | 0.8834 | 0.9402 | 7 | 63 | 0.5730 | 0.7708 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.35 | 829 | 0.2476 | 0.3383 | 0.9266 | 0.9284 | 0.9401 | 7 | 65 | 0.5645 | 0.7660 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.40 | 829 | 0.2500 | 0.3413 | 0.9408 | 0.9766 | 0.9383 | 7 | 68 | 0.5669 | 0.7648 |
| 0604:0604_excluding_under_50_usd | cand_global_svc_w0.45 | 829 | 0.2475 | 0.3452 | 0.9535 | 1.0275 | 0.9348 | 7 | 68 | 0.5476 | 0.7539 |
| 0604:0604_excluding_under_50_usd | cand_gate_n100_svc_w0.50 | 829 | 0.2391 | 0.3453 | 0.9937 | 0.7200 | 0.9410 | 4 | 59 | 0.5826 | 0.7768 |
| 0604:0604_excluding_under_50_usd | cand_gate_n100_covok_svc_w0.50 | 829 | 0.2391 | 0.3453 | 0.9937 | 0.7200 | 0.9410 | 4 | 59 | 0.5826 | 0.7768 |
| 0604:0604_excluding_under_50_usd | cand_gate_n50_svc_w0.50 | 829 | 0.2391 | 0.3460 | 0.9937 | 0.7232 | 0.9394 | 4 | 59 | 0.5814 | 0.7756 |
| 0604:0604_excluding_under_50_usd | cand_gate_n50_covok_svc_w0.50 | 829 | 0.2391 | 0.3460 | 0.9937 | 0.7232 | 0.9394 | 4 | 59 | 0.5814 | 0.7756 |
| 0604:0604_excluding_under_50_usd | cand_gate_n100_svc_w0.60 | 829 | 0.2391 | 0.3476 | 0.9994 | 0.7228 | 0.9412 | 4 | 59 | 0.5826 | 0.7756 |
| 0604:0604_excluding_under_50_usd | cand_gate_n100_covok_svc_w0.60 | 829 | 0.2391 | 0.3476 | 0.9994 | 0.7228 | 0.9412 | 4 | 59 | 0.5826 | 0.7756 |
| 0604:0604_excluding_under_50_usd | cand_gate_n50_svc_w0.60 | 829 | 0.2391 | 0.3485 | 0.9994 | 0.7267 | 0.9410 | 4 | 59 | 0.5814 | 0.7744 |
| 0604:0604_excluding_under_50_usd | cand_gate_n50_covok_svc_w0.60 | 829 | 0.2391 | 0.3485 | 0.9994 | 0.7267 | 0.9410 | 4 | 59 | 0.5814 | 0.7744 |
| 0604:0604_excluding_under_50_usd | cand_gate_n20_svc_w0.50 | 829 | 0.2468 | 0.3489 | 0.9937 | 0.7217 | 0.9448 | 4 | 59 | 0.5682 | 0.7744 |

## 5. 산출물

- `outputs/candidate_metrics_all_scopes.csv`
- `outputs/validation_selected_candidates.csv`
- `outputs/selected_candidate_metrics_all_scopes.csv`
- `outputs/0604_core_top_candidates.csv`
- `outputs/baseline_metrics.csv`
- `reports/result_report.md`
- `reports/result_report.html`
