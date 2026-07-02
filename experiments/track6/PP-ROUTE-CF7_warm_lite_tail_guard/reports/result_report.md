# PP-ROUTE-CF7 Warm-lite Tail Guard

## 1. 목적

CF5/CF6에서 확인된 Warm-lite unified의 남은 약점인 p95/RMSE tail 안정성을 개선한다.

## 2. 설계

- Warm train으로 unified Warm-lite stack을 seed 3개 재학습한다.
- Warm validation에서 residual clip, 불확실성 조건부 감쇠, 검증셋 보정층 후보를 평가한다.
- 후보 선택은 validation에서 수행하고, Warm fixed-test 607건은 최종 확인에만 사용한다.
- 선택 기준은 p95 우선이며, validation MAPE와 MdAPE가 current 대비 +0.005를 넘게 악화되는 후보는 p95 선택에서 제외한다.

## 3. 데이터 감사

```json
{
  "train_rows": 26914,
  "validation_rows": 519,
  "test_rows": 607,
  "train_artists": 1773,
  "validation_min_history": 5,
  "validation_max_history": 128,
  "test_min_history": 5,
  "test_max_history": 573
}
```

## 4. Validation Top Candidates by p95

| candidate | family | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| lgbres_s1p00_cap0p150 | residual_grid | 519 | 0.079075 | 0.168955 | 0.560746 | 0.299061 |
| lgbres_s1p00_cap0p100 | residual_grid | 519 | 0.080355 | 0.169290 | 0.566567 | 0.299576 |
| lgbres_s0p75_cap0p150 | residual_grid | 519 | 0.078054 | 0.168607 | 0.569797 | 0.299134 |
| lgbres_s0p75_cap0p100 | residual_grid | 519 | 0.078235 | 0.169214 | 0.570752 | 0.300023 |
| Warm WMIN8 operational | reference | 519 | 0.094033 | 0.175114 | 0.571291 | 0.297541 |
| validation_oof_huber_meta_calibrator | meta_calibrator | 519 | 0.097521 | 0.184684 | 0.573465 | 0.310111 |
| lgbres_s0p75_cap0p075 | residual_grid | 519 | 0.078558 | 0.169680 | 0.576151 | 0.300354 |
| lgbres_s1p00_cap0p075 | residual_grid | 519 | 0.080355 | 0.169829 | 0.576277 | 0.299977 |
| lgbres_s0p50_cap0p150 | residual_grid | 519 | 0.078725 | 0.168714 | 0.578906 | 0.299305 |
| asym_s05_neg0p150_pos0p100 | asymmetric_cap | 519 | 0.079021 | 0.168904 | 0.578906 | 0.299711 |
| asym_s05_neg0p150_pos0p075 | asymmetric_cap | 519 | 0.079021 | 0.168982 | 0.578906 | 0.299907 |
| gap_q90_corr_factor0p00 | full_lean_gap_guard | 519 | 0.080867 | 0.172114 | 0.579481 | 0.303033 |
| gap_q90_corr_factor0p25 | full_lean_gap_guard | 519 | 0.080681 | 0.171454 | 0.579544 | 0.302291 |
| gap_q90_corr_factor0p50 | full_lean_gap_guard | 519 | 0.080867 | 0.170795 | 0.579608 | 0.301596 |
| current_s05_cap010 | baseline | 519 | 0.079850 | 0.169485 | 0.579734 | 0.300351 |
| lgbres_s0p50_cap0p100 | residual_grid | 519 | 0.079850 | 0.169485 | 0.579734 | 0.300351 |
| asym_s05_neg0p100_pos0p100 | asymmetric_cap | 519 | 0.079850 | 0.169485 | 0.579734 | 0.300351 |
| asym_s05_neg0p100_pos0p075 | asymmetric_cap | 519 | 0.079850 | 0.169563 | 0.579734 | 0.300547 |
| asym_s05_neg0p075_pos0p100 | asymmetric_cap | 519 | 0.079850 | 0.169802 | 0.579734 | 0.300671 |
| lgbres_s0p50_cap0p075 | residual_grid | 519 | 0.079850 | 0.169880 | 0.579734 | 0.300867 |

## 5. Selected Candidates

| candidate | family | selection_reason | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lgbres_s1p00_cap0p150 | residual_grid | best_validation_p95_with_balance_guard | 519 | 0.079075 | 0.168955 | 0.560746 | 0.299061 |
| lgbres_s0p75_cap0p150 | residual_grid | best_validation_mape | 519 | 0.078054 | 0.168607 | 0.569797 | 0.299134 |
| validation_oof_huber_meta_calibrator | meta_calibrator | best_validation_meta_p95_with_balance_guard | 519 | 0.097521 | 0.184684 | 0.573465 | 0.310111 |

## 6. Test Reference Metrics

| candidate | family | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| Warm WMIN8 operational | reference | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 |
| Warm-lite current s0.50 cap0.10 | reference | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |
| Warm-lite qavg no residual | reference | 607 | 0.085041 | 0.229027 | 0.823648 | 0.384944 |

## 7. Selected Candidate Test Metrics

| candidate | family | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| lgbres_s0p75_cap0p150 | residual_grid | 607 | 0.085795 | 0.224312 | 0.754361 | 0.381204 |
| lgbres_s1p00_cap0p150 | residual_grid | 607 | 0.089227 | 0.223920 | 0.745513 | 0.379962 |
| validation_oof_huber_meta_calibrator | meta_calibrator | 607 | 0.088002 | 0.230273 | 0.865005 | 0.384127 |

## 8. Test Paired vs Current Warm-lite

| candidate | n | candidate_better_share | current_better_share | median_ape_delta_current_minus_candidate | mean_ape_delta_current_minus_candidate |
| --- | --- | --- | --- | --- | --- |
| lgbres_s0p75_cap0p150 | 607 | 0.467875 | 0.532125 | -0.000426 | 0.000902 |
| lgbres_s1p00_cap0p150 | 607 | 0.459638 | 0.540362 | -0.001156 | 0.001294 |
| validation_oof_huber_meta_calibrator | 607 | 0.477759 | 0.522241 | -0.001057 | -0.005059 |

## 9. 1차 판단

- Selected 중 test p95 최저 후보: `lgbres_s1p00_cap0p150`.
- current 대비 test p95 delta: `-0.057690`.
- current 대비 test MAPE delta: `-0.001294`.
- current 대비 test RMSE_log delta: `-0.002210`.

## 10. Config

```json
{
  "created_at": "2026-06-16T15:21:48",
  "experiment_id": "PP-ROUTE-CF7",
  "experiment_slug": "PP-ROUTE-CF7_warm_lite_tail_guard",
  "seeds": [
    20260612,
    20260613,
    20260614
  ],
  "base_eval_set": "Warm validation + Warm fixed-test",
  "selection_rule": "Choose on validation. p95 candidates must keep MAPE and MdAPE within +0.005 absolute of current_s05_cap010.",
  "candidate_families": [
    "residual_grid",
    "asymmetric_cap",
    "width_guard",
    "full_lean_gap_guard",
    "correction_size_guard",
    "low_history_width_guard",
    "meta_calibrator"
  ],
  "audit": {
    "train_rows": 26914,
    "validation_rows": 519,
    "test_rows": 607,
    "train_artists": 1773,
    "validation_min_history": 5,
    "validation_max_history": 128,
    "test_min_history": 5,
    "test_max_history": 573
  },
  "training_audit": [
    {
      "seed": 20260612,
      "train_rows": 26914,
      "train_artists": 1773,
      "median_train_rows_per_artist": 5.0
    },
    {
      "seed": 20260613,
      "train_rows": 26914,
      "train_artists": 1773,
      "median_train_rows_per_artist": 5.0
    },
    {
      "seed": 20260614,
      "train_rows": 26914,
      "train_artists": 1773,
      "median_train_rows_per_artist": 5.0
    }
  ],
  "seconds": 328.29
}
```
