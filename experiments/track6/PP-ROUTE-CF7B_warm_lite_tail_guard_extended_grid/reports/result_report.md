# PP-ROUTE-CF7B Warm-lite Tail Guard Extended Grid

## 1. 목적

CF7에서 선택 후보가 residual cap grid의 상한에 걸렸기 때문에, 재학습 없이 보정 강도와 cap 범위를 확장해 확인한다.

## 2. Validation Top Candidates by p95

| candidate | source | strength | cap_neg | cap_pos | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lgb_asym_s1p25_neg0p300_pos0p150 | lgb | 1.250000 | 0.300000 | 0.150000 | 519 | 0.079698 | 0.168371 | 0.541322 | 0.297726 |
| lgb_asym_s1p25_neg0p250_pos0p150 | lgb | 1.250000 | 0.250000 | 0.150000 | 519 | 0.079364 | 0.168681 | 0.541322 | 0.298159 |
| lgb_asym_s1p25_neg0p200_pos0p150 | lgb | 1.250000 | 0.200000 | 0.150000 | 519 | 0.079364 | 0.168887 | 0.541322 | 0.298498 |
| lgb_s1p00_cap0p300 | lgb | 1 | 0.300000 | 0.300000 | 519 | 0.080458 | 0.167476 | 0.544010 | 0.296876 |
| lgb_asym_s1p00_neg0p300_pos0p250 | lgb | 1 | 0.300000 | 0.250000 | 519 | 0.080458 | 0.167695 | 0.544010 | 0.297159 |
| lgb_asym_s1p00_neg0p300_pos0p200 | lgb | 1 | 0.300000 | 0.200000 | 519 | 0.080566 | 0.167814 | 0.544010 | 0.297430 |
| lgb_asym_s1p00_neg0p300_pos0p150 | lgb | 1 | 0.300000 | 0.150000 | 519 | 0.080566 | 0.167878 | 0.544010 | 0.297656 |
| lgb_s1p00_cap0p250 | lgb | 1 | 0.250000 | 0.250000 | 519 | 0.080355 | 0.168021 | 0.544010 | 0.297614 |
| lgb_asym_s1p00_neg0p250_pos0p250 | lgb | 1 | 0.250000 | 0.250000 | 519 | 0.080355 | 0.168021 | 0.544010 | 0.297614 |
| lgb_asym_s1p00_neg0p250_pos0p200 | lgb | 1 | 0.250000 | 0.200000 | 519 | 0.080458 | 0.168140 | 0.544010 | 0.297885 |
| lgb_asym_s1p00_neg0p250_pos0p150 | lgb | 1 | 0.250000 | 0.150000 | 519 | 0.080458 | 0.168204 | 0.544010 | 0.298111 |
| lgb_asym_s1p00_neg0p200_pos0p250 | lgb | 1 | 0.200000 | 0.250000 | 519 | 0.080355 | 0.168374 | 0.544010 | 0.298120 |
| lgb_s1p00_cap0p200 | lgb | 1 | 0.200000 | 0.200000 | 519 | 0.080458 | 0.168493 | 0.544010 | 0.298390 |
| lgb_asym_s1p00_neg0p200_pos0p200 | lgb | 1 | 0.200000 | 0.200000 | 519 | 0.080458 | 0.168493 | 0.544010 | 0.298390 |
| lgb_asym_s1p00_neg0p200_pos0p150 | lgb | 1 | 0.200000 | 0.150000 | 519 | 0.080458 | 0.168557 | 0.544010 | 0.298616 |
| lgb_s1p50_cap0p300 | lgb | 1.500000 | 0.300000 | 0.300000 | 519 | 0.083229 | 0.170239 | 0.544151 | 0.298331 |
| lgb_s1p50_cap0p200 | lgb | 1.500000 | 0.200000 | 0.200000 | 519 | 0.083050 | 0.170270 | 0.544151 | 0.298942 |
| lgb_s1p50_cap0p250 | lgb | 1.500000 | 0.250000 | 0.250000 | 519 | 0.083050 | 0.170338 | 0.544151 | 0.298613 |
| lgb_s1p50_cap0p150 | lgb | 1.500000 | 0.150000 | 0.150000 | 519 | 0.080786 | 0.169625 | 0.545322 | 0.298777 |
| avg_s1p50_cap0p300 | avg | 1.500000 | 0.300000 | 0.300000 | 519 | 0.077981 | 0.168139 | 0.549238 | 0.297358 |

## 3. Selected Candidates

| candidate | source | strength | cap_neg | cap_pos | selection_reason | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lgb_asym_s1p25_neg0p300_pos0p150 | lgb | 1.250000 | 0.300000 | 0.150000 | best_validation_p95_with_balance_guard | 519 | 0.079698 | 0.168371 | 0.541322 | 0.297726 |
| lgb_s0p75_cap0p300 | lgb | 0.750000 | 0.300000 | 0.300000 | best_validation_mape | 519 | 0.078235 | 0.166982 | 0.550910 | 0.296946 |
| lgb_s1p00_cap0p300 | lgb | 1 | 0.300000 | 0.300000 | best_validation_rmse_with_balance_guard | 519 | 0.080458 | 0.167476 | 0.544010 | 0.296876 |

## 4. Selected Candidate Test Metrics

| candidate | source | strength | cap_neg | cap_pos | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lgb_s1p00_cap0p300 | lgb | 1 | 0.300000 | 0.300000 | 607 | 0.086482 | 0.223915 | 0.745513 | 0.382317 |
| lgb_asym_s1p25_neg0p300_pos0p150 | lgb | 1.250000 | 0.300000 | 0.150000 | 607 | 0.090981 | 0.222950 | 0.746679 | 0.381414 |
| lgb_s0p75_cap0p300 | lgb | 0.750000 | 0.300000 | 0.300000 | 607 | 0.085029 | 0.224020 | 0.754361 | 0.382293 |

## 5. Test Paired vs Current

| candidate | n | candidate_better_share | current_better_share | median_ape_delta_current_minus_candidate | mean_ape_delta_current_minus_candidate |
| --- | --- | --- | --- | --- | --- |
| lgb_asym_s1p25_neg0p300_pos0p150 | 607 | 0.457990 | 0.542010 | -0.001735 | 0.002264 |
| lgb_s0p75_cap0p300 | 607 | 0.467875 | 0.532125 | -0.000426 | 0.001194 |
| lgb_s1p00_cap0p300 | 607 | 0.457990 | 0.542010 | -0.001156 | 0.001299 |

## 6. Config

```json
{
  "created_at": "2026-06-16T15:23:31",
  "experiment_id": "PP-ROUTE-CF7B",
  "experiment_slug": "PP-ROUTE-CF7B_warm_lite_tail_guard_extended_grid",
  "source_experiment": "experiments/track6/PP-ROUTE-CF7_warm_lite_tail_guard",
  "source_predictions": "experiments/track6/PP-ROUTE-CF7_warm_lite_tail_guard/outputs/seed_mean_feature_predictions.csv",
  "selection_rule": "Choose on validation. p95 candidates must keep MAPE and MdAPE within +0.005 absolute of current_s05_cap010.",
  "candidate_count": 172,
  "seconds": 0.91
}
```
