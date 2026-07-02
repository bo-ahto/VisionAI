# PP-ROUTE-CF9 Conditional CF7 Router

## 1. 목적

Warm-lite current를 기본으로 유지하고, validation에서 선택한 조건에서만 CF7 tail guard를 적용한다.

## 2. Validation Top Candidates

| candidate | family | route_share | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| route_gap_q50 | gap | 0.500963 | 519 | 0.079075 | 0.167521 | 0.560746 | 0.298469 |
| route_absres_q50 | absres | 0.500963 | 519 | 0.079075 | 0.168823 | 0.560746 | 0.299015 |
| cf7_all | reference | 1 | 519 | 0.079075 | 0.168955 | 0.560746 | 0.299061 |
| route_width_q50 | width | 0.500963 | 519 | 0.079850 | 0.168583 | 0.560746 | 0.299095 |
| route_absres_q67 | absres | 0.331407 | 519 | 0.079850 | 0.168699 | 0.560746 | 0.299141 |
| route_width_q60 | width | 0.400771 | 519 | 0.079850 | 0.168515 | 0.560746 | 0.299175 |
| route_down_or_width_q50 | down_or_width | 0.807322 | 519 | 0.079075 | 0.168901 | 0.560746 | 0.299175 |
| route_down_or_width_q60 | down_or_width | 0.772640 | 519 | 0.079075 | 0.168840 | 0.560746 | 0.299250 |
| route_down_or_width_q67 | down_or_width | 0.745665 | 519 | 0.079075 | 0.169017 | 0.560746 | 0.299641 |
| route_down_or_width_q75 | down_or_width | 0.718690 | 519 | 0.077628 | 0.168882 | 0.560746 | 0.299646 |
| route_down_or_width_q80 | down_or_width | 0.703276 | 519 | 0.077628 | 0.168998 | 0.560746 | 0.299838 |
| route_down_or_width_q90 | down_or_width | 0.660886 | 519 | 0.076703 | 0.168658 | 0.560746 | 0.299967 |
| route_gap_q67 | gap | 0.329480 | 519 | 0.079075 | 0.167699 | 0.566755 | 0.298927 |
| route_down_gap_q50 | down_and_gap | 0.300578 | 519 | 0.078725 | 0.167794 | 0.566755 | 0.299408 |
| route_down_width_q50 | down_and_width | 0.308285 | 519 | 0.078725 | 0.167653 | 0.566755 | 0.299499 |
| route_down_absres_q50 | down_and_absres | 0.290944 | 519 | 0.078725 | 0.167987 | 0.566755 | 0.299501 |
| route_down_width_q60 | down_and_width | 0.242775 | 519 | 0.078725 | 0.167646 | 0.566755 | 0.299505 |
| route_down_gap_q67 | down_and_gap | 0.192678 | 519 | 0.079021 | 0.167985 | 0.566755 | 0.299549 |
| route_down_absres_q67 | down_and_absres | 0.171484 | 519 | 0.079021 | 0.167858 | 0.566755 | 0.299565 |
| route_residual_down | residual_direction | 0.614644 | 519 | 0.076703 | 0.167971 | 0.566755 | 0.299580 |

## 3. Selected Routers

| candidate | family | selection_reason | route_share | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE | delta_MAPE | delta_p95_APE | delta_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| route_gap_q50 | gap | best_validation_p95_strict_guard | 0.500963 | 519 | 0.079075 | 0.167521 | 0.560746 | 0.298469 | -0.000775 | -0.001877 | -0.018988 | -0.001846 |

## 4. Full-History Test References

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| Warm WMIN8 operational | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 |
| Warm-lite current | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |
| Warm-lite CF7 all | 607 | 0.089227 | 0.223920 | 0.745513 | 0.379962 |

## 5. Full-History Selected Router Test Metrics

| candidate | family | route_share | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| route_gap_q50 | gap | 0.565074 | 607 | 0.086405 | 0.223590 | 0.758056 | 0.380030 |

## 6. k=1~6 Stress Metrics

| candidate | condition | route_share | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm retrained clean stack | k=1 seed-mean |  | 519 | 0.228377 | 0.349077 | 0.940275 | 0.470595 | 4 | 4 |
| cf7_all | k=1 seed-mean | 1 | 519 | 0.173219 | 0.311373 | 0.880311 | 0.448299 | 2 | 1 |
| current | k=1 seed-mean | 0.000000 | 519 | 0.172755 | 0.311118 | 0.890055 | 0.446076 | 1 | 2 |
| route_gap_q50 | k=1 seed-mean | 0.669878 | 519 | 0.174032 | 0.311709 | 0.897335 | 0.447839 | 3 | 3 |
| Warm retrained clean stack | k=2 seed-mean |  | 519 | 0.201354 | 0.293245 | 0.936806 | 0.431259 | 1 | 4 |
| cf7_all | k=2 seed-mean | 1 | 519 | 0.157679 | 0.303237 | 0.863655 | 0.424533 | 3 | 1 |
| current | k=2 seed-mean | 0.000000 | 519 | 0.161448 | 0.304920 | 0.889889 | 0.423878 | 4 | 3 |
| route_gap_q50 | k=2 seed-mean | 0.615286 | 519 | 0.158753 | 0.302751 | 0.869473 | 0.423962 | 2 | 2 |
| Warm retrained clean stack | k=3 seed-mean |  | 519 | 0.170056 | 0.291045 | 0.887342 | 0.446368 | 4 | 4 |
| cf7_all | k=3 seed-mean | 1 | 519 | 0.143756 | 0.257369 | 0.876824 | 0.430291 | 3 | 1 |
| current | k=3 seed-mean | 0.000000 | 519 | 0.142914 | 0.257082 | 0.877410 | 0.430237 | 2 | 3 |
| route_gap_q50 | k=3 seed-mean | 0.576108 | 519 | 0.141770 | 0.256938 | 0.876824 | 0.430150 | 1 | 1 |
| Warm retrained clean stack | k=4 seed-mean |  | 519 | 0.164994 | 0.271088 | 0.854571 | 0.426418 | 4 | 4 |
| cf7_all | k=4 seed-mean | 1 | 519 | 0.112094 | 0.252893 | 0.781680 | 0.395508 | 2 | 1 |
| current | k=4 seed-mean | 0.000000 | 519 | 0.111142 | 0.255190 | 0.841395 | 0.397345 | 3 | 3 |
| route_gap_q50 | k=4 seed-mean | 0.547848 | 519 | 0.112640 | 0.252787 | 0.816695 | 0.395484 | 1 | 2 |
| Warm retrained clean stack | k=5 seed-mean |  | 519 | 0.156848 | 0.257445 | 0.800696 | 0.410500 | 4 | 4 |
| cf7_all | k=5 seed-mean | 1 | 519 | 0.118969 | 0.230655 | 0.661499 | 0.368704 | 1 | 2 |
| current | k=5 seed-mean | 0.000000 | 519 | 0.119911 | 0.230864 | 0.676274 | 0.369027 | 3 | 3 |
| route_gap_q50 | k=5 seed-mean | 0.542710 | 519 | 0.121648 | 0.230832 | 0.660076 | 0.368844 | 2 | 1 |
| Warm retrained clean stack | k=6 seed-mean |  | 519 | 0.139844 | 0.261411 | 0.856599 | 0.425187 | 4 | 4 |
| cf7_all | k=6 seed-mean | 1 | 519 | 0.114188 | 0.225065 | 0.756899 | 0.369826 | 1 | 1 |
| current | k=6 seed-mean | 0.000000 | 519 | 0.114118 | 0.226295 | 0.764952 | 0.370710 | 3 | 3 |
| route_gap_q50 | k=6 seed-mean | 0.533719 | 519 | 0.114295 | 0.225356 | 0.756899 | 0.370603 | 2 | 1 |

## 7. Native Warm-lite Residual-Down Router Overall

| scope | candidate | route_share | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q1_native | native_current | 0.000000 | 1947 | 0.107246 | 0.275773 | 0.852026 | 0.423003 |
| q1_native | native_cf7_all | 1 | 1947 | 0.112221 | 0.275745 | 0.851658 | 0.419824 |
| q1_native | native_route_residual_down | 0.559836 | 1947 | 0.108689 | 0.272493 | 0.834596 | 0.422073 |
| q2_native | native_current | 0.000000 | 7284 | 0.154475 | 0.303435 | 1.000528 | 0.482084 |
| q2_native | native_cf7_all | 1 | 7284 | 0.159414 | 0.301687 | 0.988525 | 0.480387 |
| q2_native | native_route_residual_down | 0.597337 | 7284 | 0.157698 | 0.298540 | 0.978524 | 0.481631 |

## 8. Config

```json
{
  "created_at": "2026-06-16T15:56:54",
  "experiment_id": "PP-ROUTE-CF9",
  "experiment_slug": "PP-ROUTE-CF9_conditional_cf7_router",
  "source_experiments": [
    "experiments/track6/PP-ROUTE-CF5_unified_warm_lite_operational_comparison",
    "experiments/track6/PP-ROUTE-CF7_warm_lite_tail_guard",
    "experiments/track6/PP-WLITE-Q6_cf7_candidate_native_validation"
  ],
  "default_formula": "qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)",
  "routed_formula": "qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)",
  "selection_rule": "validation only; strict guard MdAPE<=current+0.001 and MAPE<=current+0.001, plus loose balanced score",
  "candidate_count": 45,
  "seconds": 0.78
}
```
