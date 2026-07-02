# PP-ROUTE-CF6 Full-History Retrained Warm vs Unified Warm-lite

## 1. 목적

full-history 조건에서 Warm clean stack과 unified Warm-lite를 모두 새로 학습해 Warm fixed-test 607개에서 비교한다.

## 2. 학습 조건

- 두 후보 모두 같은 Warm train split을 사용한다.
- 두 후보 모두 같은 Warm fixed-test 607개에서 평가한다.
- Warm은 CF3의 재현 가능한 clean stack 축을 full-history 조건으로 재학습한다.
- Warm-lite는 CF5의 unified 구조를 full Warm train distribution으로 seed 3개 재학습하고 seed-mean으로 평가한다.
- 이 비교도 운영 WMIN8 전체 PPV8/V2 artifact의 완전 재생성은 아니다.

## 3. Primary Metrics

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warm clean full-history retrained | 607 | 0.114838 | 0.244538 | 0.816909 | 0.387520 | 5 | 3 |
| Warm-lite unified full-history retrained | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 | 1 | 2 |

## 4. Warm-lite Seed Metrics

| condition | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| seed=20260612 | 607 | 0.084389 | 0.226349 | 0.825700 | 0.382537 |
| seed=20260613 | 607 | 0.083167 | 0.225632 | 0.817600 | 0.383112 |
| seed=20260614 | 607 | 0.090597 | 0.225277 | 0.791297 | 0.382007 |

## 5. Paired Row-Level Comparison

| n | warm_better_share | warm_lite_better_share | tie_share | median_ape_delta_warm_minus_warm_lite | mean_ape_delta_warm_minus_warm_lite |
| --- | --- | --- | --- | --- | --- |
| 607 | 0.415157 | 0.584843 | 0.000000 | 0.010362 | 0.019324 |

## 6. Warm Route Audit

| route_to_alt_share | median_risk_score | route_threshold |
| --- | --- | --- |
| 0.275124 | 0.416000 | 0.416000 |

## 7. Warm-lite Training Audit

| seed | train_rows | train_artists | median_train_rows_per_artist |
| --- | --- | --- | --- |
| 20260612 | 26914 | 1773 | 5 |
| 20260613 | 26914 | 1773 | 5 |
| 20260614 | 26914 | 1773 | 5 |

## 8. 해석 주의

- 이 비교는 학습 조건을 full-history로 맞춘 clean-stack 비교다.
- 현재 운영 Warm WMIN8 artifact와 직접 같지는 않다. 운영 Warm WMIN8과의 직접 비교는 CF5를 함께 본다.
- Cold/no-history 조건은 별도 라우트로 남는다.

## 9. Config

```json
{
  "created_at": "2026-06-16T14:59:41",
  "experiment_id": "PP-ROUTE-CF6",
  "experiment_slug": "PP-ROUTE-CF6_full_history_retrained_warm_vs_unified_warm_lite",
  "seeds": [
    20260612,
    20260613,
    20260614
  ],
  "base_eval_set": "Warm fixed-test 607 rows",
  "warm_eligibility_audit": {
    "warm_fixed_test_rows_total": 607,
    "exact_k1_to_k6_eligible_rows": 607,
    "excluded_rows_with_less_than_max_k_history": 0,
    "min_full_train_artist_history_n": 5,
    "max_full_train_artist_history_n": 573,
    "validation_rows_for_refit_and_router": 519
  },
  "warm_lite_eligibility_audit": {
    "warm_fixed_test_rows_total": 607,
    "k1_to_k6_eligible_rows": 519,
    "excluded_rows_with_less_than_6_history": 88,
    "full_history_min": 5,
    "full_history_max": 573
  },
  "warm_training": {
    "train_distribution": "actual full Warm train distribution",
    "validation": "Warm validation split for Huber refit and router",
    "stack": "SVC comparable Huber + L10 generated-bucket sequential + Huber refit + risk router",
    "caveat": "clean stack, not exact historical WMIN8/PPV8 full artifact rebuild"
  },
  "warm_lite_training": {
    "train_distribution": "actual full Warm train distribution",
    "group_stats": "5-fold internal stats for train, full train stats for test",
    "stack": "LightGBM Quantile full/lean + LightGBM objective=huber residual",
    "aggregation": "seed-mean over three retrained seeds"
  },
  "limitations": [
    "This is a full-history retrained clean-stack comparison, not exact Warm WMIN8 operational artifact reproduction.",
    "Use CF5 for direct comparison against current Warm WMIN8 operational.",
    "Cold/no-history route remains separate."
  ],
  "seconds": 362.56
}
```
