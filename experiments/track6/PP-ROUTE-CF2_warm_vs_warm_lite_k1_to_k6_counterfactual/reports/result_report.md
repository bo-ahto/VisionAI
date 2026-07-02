# PP-ROUTE-CF2 Warm vs Warm-lite k=1~6 Same-Row Counterfactual

## 1. 목적

Warm fixed-test 작품 중 같은 작가 train 이력이 6건 이상 있는 동일 작품만 사용해, Warm과 Warm-lite를 각각 k=1~6 이력 노출 조건으로 비교한다.

## 2. 해석 범위

- 주 비교 n은 519개다. Warm fixed-test 607개 중 88개는 train 이력이 정확히 6건까지 없어서 k=1~6 동일 n 비교에서 제외했다.
- Warm-lite forced k=1~6은 최신 Warm-lite Quantile + LightGBM Huber residual 번들을 강제 적용한 값이다. k=5~6은 실제 라우팅 범위 밖의 스트레스 비교다.
- Warm WMIN8-shell forced k=1~6은 같은작가 비교군 Huber 축을 k건 이력으로 재학습하고, WMIN8의 Huber/refit/router shell에 통과시킨 비교용 값이다.
- Warm WMIN8-shell은 PPV8/V2 등 상류 Warm stack 전체를 k별로 재학습한 완전한 full WMIN8이 아니다. 따라서 운영 확정 기준선은 `Warm WMIN8 operational`을 별도로 본다.

## 3. Same-n seed-mean metrics

| candidate | condition | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm WMIN8 operational | current 5+ route baseline | 519 | 0.101759 | 0.232914 | 0.721263 | 0.360312 | 3 | 3 |
| Warm WMIN8-shell forced | k=1 seed-mean | 519 | 0.179373 | 0.314265 | 0.948419 | 0.429333 | 13 | 13 |
| Warm-lite forced | k=1 seed-mean | 519 | 0.175953 | 0.310822 | 0.835598 | 0.446967 | 12 | 9 |
| Warm WMIN8-shell forced | k=2 seed-mean | 519 | 0.169095 | 0.290692 | 0.820199 | 0.402740 | 10 | 8 |
| Warm-lite forced | k=2 seed-mean | 519 | 0.153789 | 0.302417 | 0.900039 | 0.421684 | 11 | 12 |
| Warm WMIN8-shell forced | k=3 seed-mean | 519 | 0.153660 | 0.257849 | 0.819434 | 0.407907 | 9 | 7 |
| Warm-lite forced | k=3 seed-mean | 519 | 0.137825 | 0.255224 | 0.867408 | 0.429379 | 8 | 11 |
| Warm WMIN8-shell forced | k=4 seed-mean | 519 | 0.133112 | 0.252850 | 0.808804 | 0.386698 | 6 | 6 |
| Warm-lite forced | k=4 seed-mean | 519 | 0.107963 | 0.254272 | 0.864770 | 0.397774 | 7 | 10 |
| Warm WMIN8-shell forced | k=5 seed-mean | 519 | 0.134460 | 0.240955 | 0.667401 | 0.369261 | 5 | 1 |
| Warm-lite forced | k=5 seed-mean | 519 | 0.117423 | 0.230043 | 0.670049 | 0.368827 | 2 | 2 |
| Warm WMIN8-shell forced | k=6 seed-mean | 519 | 0.129591 | 0.237755 | 0.763263 | 0.372354 | 4 | 4 |
| Warm-lite forced | k=6 seed-mean | 519 | 0.114197 | 0.225359 | 0.777724 | 0.369350 | 1 | 5 |

## 4. 관찰 요약

- Best by MdAPE: `Warm-lite forced k=4 seed-mean`.
- Best by MAPE: `Warm-lite forced k=6 seed-mean`.
- Best by p95 APE: `Warm WMIN8-shell forced k=5 seed-mean`.
- Best by RMSE log: `Warm-lite forced k=5 seed-mean`.
- k=6에서 Warm WMIN8-shell vs Warm-lite: MdAPE `0.129591` vs `0.114197`, MAPE `0.237755` vs `0.225359`, p95 `0.763263` vs `0.777724`.

## 5. Paired row-level comparison

| k | n | warm_better_share | warm_lite_better_share | median_ape_delta_warm_minus_warm_lite | mean_ape_delta_warm_minus_warm_lite |
| --- | --- | --- | --- | --- | --- |
| 1 | 519 | 0.535645 | 0.464355 | -0.007154 | 0.003443 |
| 2 | 519 | 0.477842 | 0.522158 | 0.003051 | -0.011725 |
| 3 | 519 | 0.470135 | 0.529865 | 0.004780 | 0.002625 |
| 4 | 519 | 0.458574 | 0.541426 | 0.008544 | -0.001422 |
| 5 | 519 | 0.452794 | 0.547206 | 0.007284 | 0.010912 |
| 6 | 519 | 0.452794 | 0.547206 | 0.006184 | 0.012397 |

## 6. Repeated seed metrics

| candidate | trunc_seed | k | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warm WMIN8-shell forced | 20260612 | 1 | 519 | 0.216482 | 0.327553 | 0.971022 | 0.511036 |
| Warm WMIN8-shell forced | 20260613 | 1 | 519 | 0.195565 | 0.367269 | 1.157705 | 0.469295 |
| Warm WMIN8-shell forced | 20260614 | 1 | 519 | 0.188712 | 0.395175 | 1.466763 | 0.504020 |
| Warm-lite forced | 20260612 | 1 | 519 | 0.206123 | 0.329033 | 0.984585 | 0.568903 |
| Warm-lite forced | 20260613 | 1 | 519 | 0.184115 | 0.352429 | 1.094092 | 0.484663 |
| Warm-lite forced | 20260614 | 1 | 519 | 0.192879 | 0.451213 | 1.303123 | 0.546323 |
| Warm WMIN8-shell forced | 20260612 | 2 | 519 | 0.168323 | 0.325295 | 0.953102 | 0.414787 |
| Warm WMIN8-shell forced | 20260613 | 2 | 519 | 0.164066 | 0.312499 | 0.932611 | 0.446169 |
| Warm WMIN8-shell forced | 20260614 | 2 | 519 | 0.177515 | 0.323566 | 0.931944 | 0.458877 |
| Warm-lite forced | 20260612 | 2 | 519 | 0.152662 | 0.360629 | 1.029033 | 0.441771 |
| Warm-lite forced | 20260613 | 2 | 519 | 0.158024 | 0.351857 | 0.980961 | 0.495035 |
| Warm-lite forced | 20260614 | 2 | 519 | 0.162810 | 0.332990 | 0.979828 | 0.492604 |
| Warm WMIN8-shell forced | 20260612 | 3 | 519 | 0.153374 | 0.317162 | 0.916935 | 0.487078 |
| Warm WMIN8-shell forced | 20260613 | 3 | 519 | 0.155306 | 0.248852 | 0.823968 | 0.424820 |
| Warm WMIN8-shell forced | 20260614 | 3 | 519 | 0.170217 | 0.284667 | 0.802081 | 0.448041 |
| Warm-lite forced | 20260612 | 3 | 519 | 0.141822 | 0.359081 | 0.990953 | 0.539184 |
| Warm-lite forced | 20260613 | 3 | 519 | 0.153394 | 0.248753 | 0.836199 | 0.467616 |
| Warm-lite forced | 20260614 | 3 | 519 | 0.142625 | 0.285971 | 0.884058 | 0.476848 |
| Warm WMIN8-shell forced | 20260612 | 4 | 519 | 0.134773 | 0.289825 | 0.930241 | 0.403335 |
| Warm WMIN8-shell forced | 20260613 | 4 | 519 | 0.143574 | 0.256715 | 0.796257 | 0.414836 |
| Warm WMIN8-shell forced | 20260614 | 4 | 519 | 0.136671 | 0.282519 | 0.946802 | 0.456369 |
| Warm-lite forced | 20260612 | 4 | 519 | 0.121152 | 0.328125 | 1.060020 | 0.428977 |
| Warm-lite forced | 20260613 | 4 | 519 | 0.121384 | 0.260814 | 0.809309 | 0.430498 |
| Warm-lite forced | 20260614 | 4 | 519 | 0.123960 | 0.306579 | 0.904083 | 0.501981 |
| Warm WMIN8-shell forced | 20260612 | 5 | 519 | 0.144047 | 0.276706 | 0.717035 | 0.377767 |
| Warm WMIN8-shell forced | 20260613 | 5 | 519 | 0.129737 | 0.264240 | 0.757170 | 0.408517 |
| Warm WMIN8-shell forced | 20260614 | 5 | 519 | 0.136349 | 0.239518 | 0.746276 | 0.400390 |
| Warm-lite forced | 20260612 | 5 | 519 | 0.128457 | 0.283220 | 0.904091 | 0.394540 |
| Warm-lite forced | 20260613 | 5 | 519 | 0.127560 | 0.258460 | 0.731229 | 0.411954 |
| Warm-lite forced | 20260614 | 5 | 519 | 0.110590 | 0.236255 | 0.818764 | 0.420932 |
| Warm WMIN8-shell forced | 20260612 | 6 | 519 | 0.137965 | 0.252064 | 0.754297 | 0.366467 |
| Warm WMIN8-shell forced | 20260613 | 6 | 519 | 0.130287 | 0.263364 | 0.820207 | 0.407383 |
| Warm WMIN8-shell forced | 20260614 | 6 | 519 | 0.121865 | 0.250859 | 0.795117 | 0.407192 |
| Warm-lite forced | 20260612 | 6 | 519 | 0.123039 | 0.241613 | 0.863950 | 0.364981 |
| Warm-lite forced | 20260613 | 6 | 519 | 0.121524 | 0.290088 | 0.880467 | 0.430896 |
| Warm-lite forced | 20260614 | 6 | 519 | 0.121836 | 0.249229 | 0.789778 | 0.412772 |

## 7. Warm shell route audit

| trunc_seed | k | route_to_alt_share | median_risk_score |
| --- | --- | --- | --- |
| 20260612 | 1 | 0.452794 | 0.428536 |
| 20260613 | 1 | 0.369942 | 0.421446 |
| 20260614 | 1 | 0.360308 | 0.416052 |
| 20260612 | 2 | 0.373796 | 0.421446 |
| 20260613 | 2 | 0.387283 | 0.421446 |
| 20260614 | 2 | 0.408478 | 0.412294 |
| 20260612 | 3 | 0.400771 | 0.413120 |
| 20260613 | 3 | 0.393064 | 0.415325 |
| 20260614 | 3 | 0.373796 | 0.400703 |
| 20260612 | 4 | 0.373796 | 0.411874 |
| 20260613 | 4 | 0.385356 | 0.401197 |
| 20260614 | 4 | 0.360308 | 0.407861 |
| 20260612 | 5 | 0.371869 | 0.420232 |
| 20260613 | 5 | 0.375723 | 0.413552 |
| 20260614 | 5 | 0.387283 | 0.406659 |
| 20260612 | 6 | 0.341040 | 0.413901 |
| 20260613 | 6 | 0.346821 | 0.411210 |
| 20260614 | 6 | 0.368015 | 0.407976 |

## 8. 결론 사용법

- 이 표는 Warm/Warm-lite 라우팅 경계 설명용 same-n 실험이다.
- Warm-lite k=5~6이 좋아 보이더라도 실제 운영에서 5건 이상을 Warm-lite로 보내자는 결론으로 바로 연결하면 안 된다. k=5~6은 out-of-route 강제 적용이기 때문이다.
- Warm WMIN8-shell이 좋아 보이더라도 full WMIN8 전체 재학습 결과는 아니다. 운영 모델 설명에서는 현행 Warm WMIN8 operational 성능과 함께 보조 근거로 사용한다.

## 9. Config

```json
{
  "created_at": "2026-06-16T12:52:30",
  "experiment_id": "PP-ROUTE-CF2",
  "experiment_slug": "PP-ROUTE-CF2_warm_vs_warm_lite_k1_to_k6_counterfactual",
  "trunc_seeds": [
    20260612,
    20260613,
    20260614
  ],
  "k_values": [
    1,
    2,
    3,
    4,
    5,
    6
  ],
  "base_eval_set": "Warm fixed-test rows with >=6 same-artist train history rows",
  "eligibility_audit": {
    "warm_fixed_test_rows_total": 607,
    "exact_k1_to_k6_eligible_rows": 519,
    "excluded_rows_with_only_5_train_history": 88,
    "min_full_train_artist_history_n": 6,
    "max_full_train_artist_history_n": 573
  },
  "warm_lite_source": "models/track6/warm_lite_quantile_residual_v0.1/predict/predict_warm_lite_quantile_residual_v0_1.py",
  "warm_lite_design": "frozen official v0.1 Warm-lite Quantile + LightGBM Huber residual bundle, forced to k=1..6; k=5..6 are out-of-route stress cases",
  "warm_shell_sources": {
    "fixed_feature_store": "models/track6/warm_wmin8_exact_runtime_candidate/artifacts/fixed_test_feature_store.csv",
    "runtime": "models/track6/warm_wmin8_exact_runtime_candidate/artifacts/wmin8_huber_runtime.json",
    "operational_baseline": "models/track6/warm_wmin8_operational_candidate/artifacts/wmin8_selected_candidate_predictions.csv"
  },
  "warm_shell_design": "SVC comparable-stat Huber axis retrained after k-truncating target artists; PPV8/shrinkage stable context held fixed; WMIN8 Huber refit and risk router applied",
  "route_threshold": 0.2534165869100283,
  "route_gap": 0.005,
  "limitations": [
    "Warm WMIN8-shell forced k=1..6 is not full upstream WMIN8 retraining.",
    "Warm-lite forced k=5..6 is outside the official Warm-lite route and is used only for route-boundary stress comparison.",
    "Main same-n table excludes 88 Warm fixed-test rows with only 5 available same-artist train-history rows so every k=1..6 condition has exactly the same rows."
  ],
  "seconds": 428.6
}
```
