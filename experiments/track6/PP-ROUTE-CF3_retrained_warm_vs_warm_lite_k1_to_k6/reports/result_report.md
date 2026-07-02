# PP-ROUTE-CF3 Retrained Warm vs Warm-lite k=1~6

## 1. 목적

Warm fixed-test 중 k=1~6을 모두 만들 수 있는 동일 작품에서, Warm과 Warm-lite를 각 k 조건별로 다시 학습해 비교한다.

## 2. CF2와 다른 점

- CF2는 동결 Warm-lite 번들과 WMIN8-shell을 강제 적용했다.
- CF3는 각 seed/k 조건마다 Warm-lite Quantile/잔차 모델을 다시 학습한다.
- CF3는 각 seed/k 조건마다 Warm의 비교군 Huber 축, 버킷 순차 보정 축, validation Huber refit, validation risk router를 다시 학습한다.
- 단, 과거 WMIN8의 모든 PPV8/V2 상류 실험 산출물을 그대로 재현한 것은 아니므로 후보명은 `Warm retrained clean stack`으로 분리한다.

## 3. Same-n seed-mean metrics

| candidate | condition | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm retrained clean stack | k=1 retrained seed-mean | 519 | 0.228377 | 0.349077 | 0.940275 | 0.470595 | 12 | 12 |
| Warm-lite retrained | k=1 retrained seed-mean | 519 | 0.199623 | 0.317564 | 0.874862 | 0.415761 | 11 | 9 |
| Warm retrained clean stack | k=2 retrained seed-mean | 519 | 0.201354 | 0.293245 | 0.936806 | 0.431259 | 10 | 11 |
| Warm-lite retrained | k=2 retrained seed-mean | 519 | 0.154445 | 0.252358 | 0.827550 | 0.385730 | 4 | 5 |
| Warm retrained clean stack | k=3 retrained seed-mean | 519 | 0.170056 | 0.291045 | 0.887342 | 0.446368 | 9 | 10 |
| Warm-lite retrained | k=3 retrained seed-mean | 519 | 0.136824 | 0.263566 | 0.798208 | 0.409857 | 7 | 3 |
| Warm retrained clean stack | k=4 retrained seed-mean | 519 | 0.164994 | 0.271088 | 0.854571 | 0.426418 | 8 | 7 |
| Warm-lite retrained | k=4 retrained seed-mean | 519 | 0.116362 | 0.239851 | 0.772824 | 0.379825 | 2 | 2 |
| Warm retrained clean stack | k=5 retrained seed-mean | 519 | 0.156848 | 0.257445 | 0.800696 | 0.410500 | 5 | 4 |
| Warm-lite retrained | k=5 retrained seed-mean | 519 | 0.116743 | 0.232401 | 0.695368 | 0.386942 | 1 | 1 |
| Warm retrained clean stack | k=6 retrained seed-mean | 519 | 0.139844 | 0.261411 | 0.856599 | 0.425187 | 6 | 8 |
| Warm-lite retrained | k=6 retrained seed-mean | 519 | 0.118285 | 0.245230 | 0.836558 | 0.399638 | 3 | 6 |

## 4. 관찰 요약

- Best by MdAPE: `Warm-lite retrained k=4 retrained seed-mean`.
- Best by MAPE: `Warm-lite retrained k=5 retrained seed-mean`.
- Best by p95 APE: `Warm-lite retrained k=5 retrained seed-mean`.
- Best by RMSE log: `Warm-lite retrained k=4 retrained seed-mean`.

## 5. Paired row-level comparison

| k | n | warm_better_share | warm_lite_better_share | median_ape_delta_warm_minus_warm_lite | mean_ape_delta_warm_minus_warm_lite |
| --- | --- | --- | --- | --- | --- |
| 1 | 519 | 0.416185 | 0.583815 | 0.019375 | 0.031513 |
| 2 | 519 | 0.352601 | 0.647399 | 0.026596 | 0.040887 |
| 3 | 519 | 0.393064 | 0.606936 | 0.017170 | 0.027479 |
| 4 | 519 | 0.389210 | 0.610790 | 0.017207 | 0.031238 |
| 5 | 519 | 0.396917 | 0.603083 | 0.016266 | 0.025043 |
| 6 | 519 | 0.404624 | 0.595376 | 0.013488 | 0.016181 |

## 6. Repeated seed metrics

| candidate | trunc_seed | k | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warm retrained clean stack | 20260612 | 1 | 519 | 0.252714 | 0.486424 | 1.009002 | 0.590389 |
| Warm retrained clean stack | 20260613 | 1 | 519 | 0.235105 | 0.458775 | 1.032753 | 0.551263 |
| Warm retrained clean stack | 20260614 | 1 | 519 | 0.261232 | 0.378492 | 1.060145 | 0.501292 |
| Warm-lite retrained | 20260612 | 1 | 519 | 0.193091 | 0.504041 | 1.025039 | 0.578043 |
| Warm-lite retrained | 20260613 | 1 | 519 | 0.199551 | 0.396978 | 0.920058 | 0.490448 |
| Warm-lite retrained | 20260614 | 1 | 519 | 0.219200 | 0.356065 | 1.022073 | 0.472380 |
| Warm retrained clean stack | 20260612 | 2 | 519 | 0.211482 | 0.302689 | 0.885020 | 0.431543 |
| Warm retrained clean stack | 20260613 | 2 | 519 | 0.214275 | 0.335475 | 0.968765 | 0.490139 |
| Warm retrained clean stack | 20260614 | 2 | 519 | 0.205461 | 0.347145 | 1.227138 | 0.498124 |
| Warm-lite retrained | 20260612 | 2 | 519 | 0.154668 | 0.272666 | 0.857547 | 0.418003 |
| Warm-lite retrained | 20260613 | 2 | 519 | 0.184533 | 0.296892 | 0.873076 | 0.465123 |
| Warm-lite retrained | 20260614 | 2 | 519 | 0.168253 | 0.319520 | 1.122147 | 0.450208 |
| Warm retrained clean stack | 20260612 | 3 | 519 | 0.166380 | 0.288041 | 0.942673 | 0.445064 |
| Warm retrained clean stack | 20260613 | 3 | 519 | 0.193540 | 0.333175 | 1.059539 | 0.494816 |
| Warm retrained clean stack | 20260614 | 3 | 519 | 0.188062 | 0.326521 | 0.966217 | 0.498678 |
| Warm-lite retrained | 20260612 | 3 | 519 | 0.144271 | 0.270673 | 0.902461 | 0.410738 |
| Warm-lite retrained | 20260613 | 3 | 519 | 0.142357 | 0.295117 | 0.919604 | 0.477280 |
| Warm-lite retrained | 20260614 | 3 | 519 | 0.157776 | 0.308705 | 0.955062 | 0.480519 |
| Warm retrained clean stack | 20260612 | 4 | 519 | 0.164870 | 0.277032 | 0.897712 | 0.411816 |
| Warm retrained clean stack | 20260613 | 4 | 519 | 0.180833 | 0.294969 | 0.946168 | 0.470200 |
| Warm retrained clean stack | 20260614 | 4 | 519 | 0.159921 | 0.307590 | 0.972059 | 0.487217 |
| Warm-lite retrained | 20260612 | 4 | 519 | 0.140983 | 0.247986 | 0.860369 | 0.371271 |
| Warm-lite retrained | 20260613 | 4 | 519 | 0.141164 | 0.274393 | 0.919310 | 0.445517 |
| Warm-lite retrained | 20260614 | 4 | 519 | 0.121385 | 0.282798 | 0.914199 | 0.462595 |
| Warm retrained clean stack | 20260612 | 5 | 519 | 0.144418 | 0.275957 | 0.949081 | 0.486594 |
| Warm retrained clean stack | 20260613 | 5 | 519 | 0.165847 | 0.283371 | 0.901034 | 0.435927 |
| Warm retrained clean stack | 20260614 | 5 | 519 | 0.160842 | 0.266226 | 0.798898 | 0.392213 |
| Warm-lite retrained | 20260612 | 5 | 519 | 0.111984 | 0.256916 | 0.905811 | 0.475638 |
| Warm-lite retrained | 20260613 | 5 | 519 | 0.121924 | 0.268895 | 0.957002 | 0.429900 |
| Warm-lite retrained | 20260614 | 5 | 519 | 0.132755 | 0.243332 | 0.773700 | 0.378579 |
| Warm retrained clean stack | 20260612 | 6 | 519 | 0.147661 | 0.279228 | 0.906718 | 0.443931 |
| Warm retrained clean stack | 20260613 | 6 | 519 | 0.153196 | 0.280718 | 0.969392 | 0.479967 |
| Warm retrained clean stack | 20260614 | 6 | 519 | 0.151194 | 0.279116 | 0.884200 | 0.416424 |
| Warm-lite retrained | 20260612 | 6 | 519 | 0.114891 | 0.274380 | 0.910278 | 0.440968 |
| Warm-lite retrained | 20260613 | 6 | 519 | 0.118241 | 0.274465 | 0.967180 | 0.467128 |
| Warm-lite retrained | 20260614 | 6 | 519 | 0.120615 | 0.255723 | 0.932854 | 0.386933 |

## 7. Warm retrained route audit

| trunc_seed | k | route_to_alt_share | median_risk_score | route_threshold |
| --- | --- | --- | --- | --- |
| 20260612 | 1 | 0.213873 | 0.603744 | 0.613004 |
| 20260613 | 1 | 0.236994 | 0.604504 | 0.603355 |
| 20260614 | 1 | 0.225434 | 0.606273 | 0.619098 |
| 20260612 | 2 | 0.244701 | 0.475395 | 0.465173 |
| 20260613 | 2 | 0.233141 | 0.467436 | 0.468905 |
| 20260614 | 2 | 0.310212 | 0.472285 | 0.455721 |
| 20260612 | 3 | 0.273603 | 0.461503 | 0.452964 |
| 20260613 | 3 | 0.296724 | 0.464299 | 0.455295 |
| 20260614 | 3 | 0.294798 | 0.448144 | 0.444196 |
| 20260612 | 4 | 0.265896 | 0.442073 | 0.428051 |
| 20260613 | 4 | 0.327553 | 0.442895 | 0.432376 |
| 20260614 | 4 | 0.240848 | 0.439912 | 0.452134 |
| 20260612 | 5 | 0.290944 | 0.439586 | 0.425715 |
| 20260613 | 5 | 0.275530 | 0.465554 | 0.441749 |
| 20260614 | 5 | 0.289017 | 0.441842 | 0.428009 |
| 20260612 | 6 | 0.346821 | 0.416000 | 0.416000 |
| 20260613 | 6 | 0.292871 | 0.428273 | 0.422356 |
| 20260614 | 6 | 0.271676 | 0.432439 | 0.433320 |

## 8. 해석 주의

- 이 결과는 학습까지 다시 한 route-boundary 실험이다.
- 실제 운영 Warm WMIN8 artifact와 이름을 혼용하지 않는다. CF3 Warm은 재현 가능한 clean stack이고, 운영 WMIN8 전체 상류 산출물의 완전 재생성은 아니다.
- Warm-lite k=5~6은 모델을 다시 학습했더라도 공식 라우팅 범위 밖의 정책 스트레스 비교다.

## 9. Config

```json
{
  "created_at": "2026-06-16T14:16:26",
  "experiment_id": "PP-ROUTE-CF3",
  "experiment_slug": "PP-ROUTE-CF3_retrained_warm_vs_warm_lite_k1_to_k6",
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
  "base_eval_set": "Warm fixed-test rows with at least max(k) same-artist train-history rows",
  "eligibility_audit": {
    "warm_fixed_test_rows_total": 607,
    "exact_k1_to_k6_eligible_rows": 519,
    "excluded_rows_with_less_than_max_k_history": 88,
    "min_full_train_artist_history_n": 6,
    "max_full_train_artist_history_n": 573,
    "validation_rows_for_refit_and_router": 519
  },
  "warm_lite_training": {
    "group_stats": "k-truncated train, 5-fold internal stats for train rows, full train_k stats for test rows",
    "quantile_models": "LightGBM Quantile q10/q50/q90 full + q50 lean retrained per seed/k",
    "residual_model": "LightGBM objective=huber residual retrained per seed/k from OOF Quantile residual",
    "candidate": "lgbq_full_lean_avg + clip(0.50 * lgb_huber_residual, -0.10, +0.10)"
  },
  "warm_training": {
    "svc_axis": "comparable-stat Huber retrained per seed/k with artist min_n=1",
    "sequential_axis": "CatBoost Quantile -> Huber -> CatBoost residual generated-bucket stack retrained per seed/k",
    "refit": "Huber residual refit trained on warm validation per seed/k",
    "router": "risk threshold q50 learned from warm validation per seed/k, gap=0.005",
    "candidate": "validation-routed 0.70/0.30 base vs 0.85/0.15 alternative"
  },
  "limitations": [
    "This is a condition-retrained clean stack comparison, not an exact historical WMIN8/PPV8 full artifact rebuild.",
    "Warm-lite k=5~6 remains outside the official Warm-lite route and is included as a stress comparison.",
    "The same-n main table excludes rows that cannot support all k values."
  ],
  "seconds": 2425.7
}
```
