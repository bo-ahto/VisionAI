# PP-ROUTE-CF4 Pooled Warm-lite vs Warm k=1~6

## 1. 목적

Warm-lite를 k=1~6 전체 저이력 조건으로 한 번에 학습한 단일 모델로 만들고, 같은 seed/k/row에서 CF3 Warm retrained clean stack과 비교한다.

## 2. 설계

- Warm-lite pooled는 seed별 1개 모델이다. k=1~6 노출 조건을 합친 augmented train으로 학습한다.
- 학습용 각 k 조건은 작가당 최대 k+1개 행을 남긴다. train 행 하나를 예측할 때 자기 행을 제외하고 대략 k개 같은작가 이력을 볼 수 있게 하기 위한 구성이다.
- 평가 시에는 같은 작가 이력을 정확히 k개만 보이도록 test 작가 train history를 자른다.
- Warm 비교값은 CF3에서 같은 조건으로 재학습한 `Warm retrained clean stack`을 재사용한다.

## 3. Same-n seed-mean metrics

| candidate | condition | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm retrained clean stack | k=1 seed-mean | 519 | 0.228377 | 0.349077 | 0.940275 | 0.470595 | 12 | 12 |
| Warm-lite pooled retrained | k=1 seed-mean | 519 | 0.166687 | 0.307110 | 0.928624 | 0.435073 | 11 | 10 |
| Warm retrained clean stack | k=2 seed-mean | 519 | 0.201354 | 0.293245 | 0.936806 | 0.431259 | 9 | 11 |
| Warm-lite pooled retrained | k=2 seed-mean | 519 | 0.145009 | 0.296213 | 0.855157 | 0.413805 | 10 | 5 |
| Warm retrained clean stack | k=3 seed-mean | 519 | 0.170056 | 0.291045 | 0.887342 | 0.446368 | 8 | 8 |
| Warm-lite pooled retrained | k=3 seed-mean | 519 | 0.142388 | 0.252386 | 0.874414 | 0.421577 | 3 | 7 |
| Warm retrained clean stack | k=4 seed-mean | 519 | 0.164994 | 0.271088 | 0.854571 | 0.426418 | 7 | 4 |
| Warm-lite pooled retrained | k=4 seed-mean | 519 | 0.109619 | 0.255846 | 0.914329 | 0.397638 | 4 | 9 |
| Warm retrained clean stack | k=5 seed-mean | 519 | 0.156848 | 0.257445 | 0.800696 | 0.410500 | 5 | 3 |
| Warm-lite pooled retrained | k=5 seed-mean | 519 | 0.115575 | 0.227508 | 0.631320 | 0.368213 | 2 | 1 |
| Warm retrained clean stack | k=6 seed-mean | 519 | 0.139844 | 0.261411 | 0.856599 | 0.425187 | 6 | 6 |
| Warm-lite pooled retrained | k=6 seed-mean | 519 | 0.108227 | 0.225703 | 0.714609 | 0.367700 | 1 | 2 |

## 4. 관찰 요약

- Best by MdAPE: `Warm-lite pooled retrained k=6 seed-mean`.
- Best by MAPE: `Warm-lite pooled retrained k=6 seed-mean`.
- Best by p95 APE: `Warm-lite pooled retrained k=5 seed-mean`.
- Best by RMSE log: `Warm-lite pooled retrained k=6 seed-mean`.

## 5. Paired row-level comparison

| k | n | warm_better_share | warm_lite_pooled_better_share | median_ape_delta_warm_minus_warm_lite_pooled | mean_ape_delta_warm_minus_warm_lite_pooled |
| --- | --- | --- | --- | --- | --- |
| 1 | 519 | 0.387283 | 0.612717 | 0.052096 | 0.041967 |
| 2 | 519 | 0.394990 | 0.605010 | 0.032670 | -0.002968 |
| 3 | 519 | 0.443160 | 0.556840 | 0.020540 | 0.038658 |
| 4 | 519 | 0.402697 | 0.597303 | 0.022611 | 0.015242 |
| 5 | 519 | 0.377649 | 0.622351 | 0.026129 | 0.029937 |
| 6 | 519 | 0.362235 | 0.637765 | 0.032818 | 0.035708 |

## 6. Repeated seed metrics

| candidate | trunc_seed | k | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warm retrained clean stack | 20260612 | 1 | 519 | 0.252714 | 0.486424 | 1.009002 | 0.590389 |
| Warm retrained clean stack | 20260613 | 1 | 519 | 0.235105 | 0.458775 | 1.032753 | 0.551263 |
| Warm retrained clean stack | 20260614 | 1 | 519 | 0.261232 | 0.378492 | 1.060145 | 0.501292 |
| Warm-lite pooled retrained | 20260612 | 1 | 519 | 0.195067 | 0.319867 | 0.945271 | 0.535685 |
| Warm-lite pooled retrained | 20260613 | 1 | 519 | 0.195964 | 0.357871 | 1.181684 | 0.484558 |
| Warm-lite pooled retrained | 20260614 | 1 | 519 | 0.170493 | 0.417603 | 1.552412 | 0.525524 |
| Warm retrained clean stack | 20260612 | 2 | 519 | 0.211482 | 0.302689 | 0.885020 | 0.431543 |
| Warm retrained clean stack | 20260613 | 2 | 519 | 0.214275 | 0.335475 | 0.968765 | 0.490139 |
| Warm retrained clean stack | 20260614 | 2 | 519 | 0.205461 | 0.347145 | 1.227138 | 0.498124 |
| Warm-lite pooled retrained | 20260612 | 2 | 519 | 0.146665 | 0.360288 | 0.899050 | 0.434216 |
| Warm-lite pooled retrained | 20260613 | 2 | 519 | 0.145931 | 0.364193 | 1.022079 | 0.492103 |
| Warm-lite pooled retrained | 20260614 | 2 | 519 | 0.152690 | 0.318526 | 0.955552 | 0.481860 |
| Warm retrained clean stack | 20260612 | 3 | 519 | 0.166380 | 0.288041 | 0.942673 | 0.445064 |
| Warm retrained clean stack | 20260613 | 3 | 519 | 0.193540 | 0.333175 | 1.059539 | 0.494816 |
| Warm retrained clean stack | 20260614 | 3 | 519 | 0.188062 | 0.326521 | 0.966217 | 0.498678 |
| Warm-lite pooled retrained | 20260612 | 3 | 519 | 0.135285 | 0.366170 | 0.978116 | 0.537278 |
| Warm-lite pooled retrained | 20260613 | 3 | 519 | 0.148307 | 0.249883 | 0.866563 | 0.457504 |
| Warm-lite pooled retrained | 20260614 | 3 | 519 | 0.141662 | 0.277670 | 0.889349 | 0.469171 |
| Warm retrained clean stack | 20260612 | 4 | 519 | 0.164870 | 0.277032 | 0.897712 | 0.411816 |
| Warm retrained clean stack | 20260613 | 4 | 519 | 0.180833 | 0.294969 | 0.946168 | 0.470200 |
| Warm retrained clean stack | 20260614 | 4 | 519 | 0.159921 | 0.307590 | 0.972059 | 0.487217 |
| Warm-lite pooled retrained | 20260612 | 4 | 519 | 0.120774 | 0.334383 | 0.948176 | 0.429930 |
| Warm-lite pooled retrained | 20260613 | 4 | 519 | 0.120602 | 0.260932 | 0.799938 | 0.430070 |
| Warm-lite pooled retrained | 20260614 | 4 | 519 | 0.123862 | 0.312859 | 0.956709 | 0.499924 |
| Warm retrained clean stack | 20260612 | 5 | 519 | 0.144418 | 0.275957 | 0.949081 | 0.486594 |
| Warm retrained clean stack | 20260613 | 5 | 519 | 0.165847 | 0.283371 | 0.901034 | 0.435927 |
| Warm retrained clean stack | 20260614 | 5 | 519 | 0.160842 | 0.266226 | 0.798898 | 0.392213 |
| Warm-lite pooled retrained | 20260612 | 5 | 519 | 0.123503 | 0.275160 | 0.753974 | 0.390417 |
| Warm-lite pooled retrained | 20260613 | 5 | 519 | 0.123379 | 0.258394 | 0.727348 | 0.407114 |
| Warm-lite pooled retrained | 20260614 | 5 | 519 | 0.114439 | 0.229786 | 0.798824 | 0.422839 |
| Warm retrained clean stack | 20260612 | 6 | 519 | 0.147661 | 0.279228 | 0.906718 | 0.443931 |
| Warm retrained clean stack | 20260613 | 6 | 519 | 0.153196 | 0.280718 | 0.969392 | 0.479967 |
| Warm retrained clean stack | 20260614 | 6 | 519 | 0.151194 | 0.279116 | 0.884200 | 0.416424 |
| Warm-lite pooled retrained | 20260612 | 6 | 519 | 0.115180 | 0.241141 | 0.804666 | 0.359110 |
| Warm-lite pooled retrained | 20260613 | 6 | 519 | 0.123203 | 0.304381 | 0.947796 | 0.437774 |
| Warm-lite pooled retrained | 20260614 | 6 | 519 | 0.114439 | 0.241930 | 0.767560 | 0.408194 |

## 7. Pooled training audit

| seed | training_exposure_k | rows | artists | median_rows_per_artist |
| --- | --- | --- | --- | --- |
| 20260612 | 1 | 3301 | 1773 | 2 |
| 20260612 | 2 | 4622 | 1773 | 3 |
| 20260612 | 3 | 5780 | 1773 | 4 |
| 20260612 | 4 | 6830 | 1773 | 5 |
| 20260612 | 5 | 7709 | 1773 | 5 |
| 20260612 | 6 | 8487 | 1773 | 5 |
| 20260613 | 1 | 3301 | 1773 | 2 |
| 20260613 | 2 | 4622 | 1773 | 3 |
| 20260613 | 3 | 5780 | 1773 | 4 |
| 20260613 | 4 | 6830 | 1773 | 5 |
| 20260613 | 5 | 7709 | 1773 | 5 |
| 20260613 | 6 | 8487 | 1773 | 5 |
| 20260614 | 1 | 3301 | 1773 | 2 |
| 20260614 | 2 | 4622 | 1773 | 3 |
| 20260614 | 3 | 5780 | 1773 | 4 |
| 20260614 | 4 | 6830 | 1773 | 5 |
| 20260614 | 5 | 7709 | 1773 | 5 |
| 20260614 | 6 | 8487 | 1773 | 5 |

## 8. 해석 주의

- 이 실험은 Warm-lite를 전체 k 조건으로 학습한 단일 모델의 가능성을 보는 실험이다.
- Warm 비교값은 CF3 clean stack 기준이며, 운영 WMIN8 artifact 전체 재생성 결과와 동일한 이름으로 부르면 안 된다.
- k=5~6 Warm-lite는 여전히 공식 라우팅 범위 밖의 정책 스트레스 비교다.

## 9. Config

```json
{
  "created_at": "2026-06-16T14:34:09",
  "experiment_id": "PP-ROUTE-CF4",
  "experiment_slug": "PP-ROUTE-CF4_pooled_warm_lite_vs_warm_k1_to_k6",
  "seeds": [
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
  "base_eval_set": "Warm fixed-test rows with at least 6 same-artist train-history rows",
  "eligibility_audit": {
    "warm_fixed_test_rows_total": 607,
    "exact_k1_to_k6_eligible_rows": 519,
    "excluded_rows_with_less_than_6_history": 88,
    "min_full_train_artist_history_n": 6,
    "max_full_train_artist_history_n": 573
  },
  "warm_lite_pooled_training": {
    "training_exposures": "k=1..6 pooled per seed",
    "artist_cap_rule": "training exposure k keeps at most k+1 rows per artist",
    "group_stats": "5-fold internal stats on each capped exposure frame, then pooled",
    "model": "LightGBM Quantile full/lean + LightGBM objective=huber residual",
    "candidate": "lgbq_full_lean_avg + clip(0.50 * lgb_huber_residual, -0.10, +0.10)"
  },
  "warm_comparator": {
    "source": "experiments/track6/PP-ROUTE-CF3_retrained_warm_vs_warm_lite_k1_to_k6/outputs/predictions_all_conditions.csv",
    "candidate": "Warm retrained clean stack"
  },
  "limitations": [
    "Warm comparator is CF3 clean stack, not exact historical WMIN8/PPV8 full artifact rebuild.",
    "Warm-lite k=5~6 remains outside the official Warm-lite route and is included as a stress comparison.",
    "Pooled training intentionally augments repeated low-history exposure conditions, so it should be treated as a new candidate family."
  ],
  "seconds": 731.65
}
```
