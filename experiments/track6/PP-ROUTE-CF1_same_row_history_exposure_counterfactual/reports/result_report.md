# PP-ROUTE-CF1 Same-Row History Exposure Counterfactual

## 1. 목적

Warm fixed-test 607개 동일 작품에 대해 작가 가격 이력 노출량만 바꿔 Warm, Warm-lite, Cold 경로를 비교한다.

## 2. 해석 범위

- 같은 작품·같은 n 기준이므로 경로별 native benchmark보다 직접 비교성이 높다.
- Warm-lite는 같은 작품에서 같은 작가 train 이력을 k=1~4로 제한한 강제 시나리오다.
- Cold는 같은 작품에서 같은 작가 가격 이력을 숨긴 강제 시나리오다.
- 이 결과는 라우팅 경계 설명용이며, 실제 Warm-lite/Cold 운영 분포의 성능표를 대체하지 않는다.

## 3. Same-n metrics

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warm-lite forced k=4 | 607 | 0.118152 | 0.233539 | 0.811938 | 0.378648 | 1 | 2 |
| Warm WMIN8, 5+ history | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 | 2 | 1 |
| Warm-lite forced k=3 | 607 | 0.129779 | 0.245549 | 0.893261 | 0.403622 | 3 | 3 |
| Warm-lite forced k=2 | 607 | 0.159686 | 0.273277 | 0.908304 | 0.417175 | 4 | 5 |
| Warm-lite forced k=1 | 607 | 0.181202 | 0.300843 | 0.907625 | 0.503364 | 5 | 4 |
| Cold forced, no same-artist price history | 607 | 0.441059 | 0.707066 | 2.258632 | 0.909298 | 6 | 6 |

## 4. Observed interpretation

- Best by MdAPE: `Warm WMIN8, 5+ history`.
- Best by MAPE: `Warm-lite forced k=4`.
- Best by p95 APE: `Warm WMIN8, 5+ history`.
- Best by RMSE log: `Warm WMIN8, 5+ history`.
- Warm WMIN8 vs Warm-lite k=4: MdAPE `0.104326` vs `0.118152`, MAPE `0.235814` vs `0.233539`, p95 `0.739416` vs `0.811938`.
- Warm-lite improves as k increases: k=1 MAPE `0.300843` -> k=4 MAPE `0.233539`.
- Cold forced is much harder on the same rows: Cold MAPE `0.707066`, p95 `2.258632`.

Interpretation: the same-row test supports keeping Cold separate. It also supports that more same-artist history improves prediction stability. Warm WMIN8 remains stronger on median/tail/log-error stability, while Warm-lite k=4 is very close and slightly better on mean APE in this counterfactual. Therefore this result is evidence for route separation, but not a claim that Warm dominates Warm-lite on every metric.

## 5. Warm-lite repeated condition metrics

| trunc_seed | k | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| 20260612 | 1 | 607 | 0.190179 | 0.344228 | 1.359756 | 0.545369 |
| 20260613 | 1 | 607 | 0.207117 | 0.356917 | 1.088423 | 0.600675 |
| 20260614 | 1 | 607 | 0.205979 | 0.339769 | 1.004328 | 0.570472 |
| 20260612 | 2 | 607 | 0.166149 | 0.276601 | 0.940233 | 0.418964 |
| 20260613 | 2 | 607 | 0.157133 | 0.360916 | 1.180819 | 0.502614 |
| 20260614 | 2 | 607 | 0.163389 | 0.320041 | 0.990520 | 0.502487 |
| 20260612 | 3 | 607 | 0.124682 | 0.270892 | 0.885141 | 0.434739 |
| 20260613 | 3 | 607 | 0.137974 | 0.305346 | 0.948040 | 0.476240 |
| 20260614 | 3 | 607 | 0.143844 | 0.283334 | 0.987984 | 0.433309 |
| 20260612 | 4 | 607 | 0.135742 | 0.258572 | 0.933404 | 0.402799 |
| 20260613 | 4 | 607 | 0.129216 | 0.263700 | 0.967694 | 0.404315 |
| 20260614 | 4 | 607 | 0.124010 | 0.260902 | 0.929473 | 0.441882 |

## 6. Paired row-level comparisons

| candidate_a | candidate_b | n | a_better_share | b_better_share | median_ape_delta_a_minus_b | mean_ape_delta_a_minus_b |
| --- | --- | --- | --- | --- | --- | --- |
| Warm WMIN8 | Cold forced | 607 | 0.797364 | 0.202636 | -0.275258 | -0.471252 |
| Warm WMIN8 | Warm-lite k=1 | 607 | 0.635914 | 0.364086 | -0.043829 | -0.065029 |
| Warm-lite k=1 | Cold forced | 607 | 0.721582 | 0.278418 | -0.203543 | -0.406222 |
| Warm WMIN8 | Warm-lite k=2 | 607 | 0.589786 | 0.410214 | -0.015395 | -0.037463 |
| Warm-lite k=2 | Cold forced | 607 | 0.751236 | 0.248764 | -0.223729 | -0.433789 |
| Warm WMIN8 | Warm-lite k=3 | 607 | 0.522241 | 0.477759 | -0.002957 | -0.009735 |
| Warm-lite k=3 | Cold forced | 607 | 0.797364 | 0.202636 | -0.237590 | -0.461517 |
| Warm WMIN8 | Warm-lite k=4 | 607 | 0.509061 | 0.490939 | -0.000618 | 0.002275 |
| Warm-lite k=4 | Cold forced | 607 | 0.777595 | 0.222405 | -0.272412 | -0.473526 |

## 7. 주요 해석

- 5건 이상 이력이 있는 동일 작품에서는 Warm WMIN8이 Warm-lite 강제 k=1~4보다 전체적으로 낮은 오차를 보이는지 확인한다.
- Warm-lite k가 커질수록 성능이 개선되는지 확인해, 이력 수 증가가 가격 예측 안정성에 주는 효과를 본다.
- Cold forced 결과는 같은 작가 가격 이력을 숨겼을 때 난이도가 얼마나 올라가는지 보여주는 하한 비교다.

## 8. Config

```json
{
  "created_at": "2026-06-16T12:30:24",
  "experiment_id": "PP-ROUTE-CF1",
  "experiment_slug": "PP-ROUTE-CF1_same_row_history_exposure_counterfactual",
  "evaluation_rows": 607,
  "base_eval_set": "Warm fixed-test rows",
  "warm_source": "models/track6/warm_wmin8_operational_candidate/artifacts/wmin8_selected_candidate_predictions.csv",
  "warm_candidate": "min1_route_w850_risk_q50_altlower_gap005",
  "warm_lite_source": "experiments/track6/PP-WLITE-Q4_quantile_final_comparison/outputs/q2_final_comparison_rows.csv",
  "warm_lite_candidate": "residual_lgb_s05_cap010",
  "warm_lite_design": "same Warm fixed-test rows, same-artist train history truncated to k=1..4, three truncation seeds, seed-mean for same-n table",
  "cold_source": "models/track6/cold_prediction_v0.5_operational/predict/predict_cold_operational_v0_5.py",
  "cold_design": "same Warm fixed-test rows, no same-artist price history, cold-train bucket generation basis, frozen Cold v0.5",
  "scope_overlap_audit": {
    "warm_test_n": 607,
    "warm_test_vs_cold_train_overlap": 0,
    "warm_test_vs_cold_val_overlap": 0,
    "warm_test_vs_cold_test_overlap": 0
  },
  "limitations": [
    "Counterfactual on Warm fixed-test distribution; does not replace native Warm-lite/Cold operating benchmark.",
    "Warm-lite same-n table averages three truncation seeds per row/k.",
    "Cold forced comparison hides same-artist price history but still evaluates on Warm fixed-test artwork distribution."
  ]
}
```
