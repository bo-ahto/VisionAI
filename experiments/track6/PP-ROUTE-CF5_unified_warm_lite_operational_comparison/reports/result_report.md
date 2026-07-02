# PP-ROUTE-CF5 Unified Warm-lite Operational Comparison

## 1. 목적

Warm과 Warm-lite를 나누지 않고 Warm-lite 계열 단일 모델로 1건 이상 warm row 전체를 처리할 수 있는지 검증한다.

## 2. 핵심 설계

- Warm-lite unified 모델은 실제 full Warm train distribution으로 seed별 1개씩 학습한다.
- 학습 시 train row 통계는 5-fold internal stats로 자기 가격 누수를 막는다.
- 운영형 비교는 Warm fixed-test 607개에 전체 작가 train history를 그대로 넣고, 현재 Warm WMIN8 operational과 비교한다.
- 보조 비교는 같은 unified 모델을 k=1~6 capped history로 평가해 CF3 Warm clean stack과 비교한다.

## 3. Full-history operational comparison

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| Warm WMIN8 operational | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 |
| Warm-lite unified full-history retrained | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |

## 4. Full-history paired comparison

| n | warm_better_share | warm_lite_unified_better_share | median_ape_delta_warm_minus_unified | mean_ape_delta_warm_minus_unified |
| --- | --- | --- | --- | --- |
| 607 | 0.457990 | 0.542010 | 0.007110 | 0.010600 |

## 5. k=1~6 capped-history stress metrics

| candidate | condition | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm retrained clean stack | k=1 seed-mean | 519 | 0.228377 | 0.349077 | 0.940275 | 0.470595 | 12 | 12 |
| Warm-lite unified full-history retrained | k=1 seed-mean | 519 | 0.172755 | 0.311118 | 0.890055 | 0.446076 | 11 | 10 |
| Warm retrained clean stack | k=2 seed-mean | 519 | 0.201354 | 0.293245 | 0.936806 | 0.431259 | 9 | 11 |
| Warm-lite unified full-history retrained | k=2 seed-mean | 519 | 0.161448 | 0.304920 | 0.889889 | 0.423878 | 10 | 9 |
| Warm retrained clean stack | k=3 seed-mean | 519 | 0.170056 | 0.291045 | 0.887342 | 0.446368 | 8 | 8 |
| Warm-lite unified full-history retrained | k=3 seed-mean | 519 | 0.142914 | 0.257082 | 0.877410 | 0.430237 | 4 | 7 |
| Warm retrained clean stack | k=4 seed-mean | 519 | 0.164994 | 0.271088 | 0.854571 | 0.426418 | 7 | 5 |
| Warm-lite unified full-history retrained | k=4 seed-mean | 519 | 0.111142 | 0.255190 | 0.841395 | 0.397345 | 3 | 4 |
| Warm retrained clean stack | k=5 seed-mean | 519 | 0.156848 | 0.257445 | 0.800696 | 0.410500 | 5 | 3 |
| Warm-lite unified full-history retrained | k=5 seed-mean | 519 | 0.119911 | 0.230864 | 0.676274 | 0.369027 | 2 | 1 |
| Warm retrained clean stack | k=6 seed-mean | 519 | 0.139844 | 0.261411 | 0.856599 | 0.425187 | 6 | 6 |
| Warm-lite unified full-history retrained | k=6 seed-mean | 519 | 0.114118 | 0.226295 | 0.764952 | 0.370710 | 1 | 2 |

## 6. k=1~6 capped paired comparison

| k | n | warm_better_share | warm_lite_unified_better_share | median_ape_delta_warm_minus_unified | mean_ape_delta_warm_minus_unified |
| --- | --- | --- | --- | --- | --- |
| 1 | 519 | 0.423892 | 0.576108 | 0.034527 | 0.037959 |
| 2 | 519 | 0.414258 | 0.585742 | 0.032865 | -0.011675 |
| 3 | 519 | 0.431599 | 0.568401 | 0.018293 | 0.033963 |
| 4 | 519 | 0.394990 | 0.605010 | 0.020031 | 0.015898 |
| 5 | 519 | 0.394990 | 0.605010 | 0.021193 | 0.026581 |
| 6 | 519 | 0.373796 | 0.626204 | 0.024905 | 0.035116 |

## 7. Repeated seed metrics

| candidate | trunc_seed | k | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warm retrained clean stack | 20260612 | 1 | 519 | 0.252714 | 0.486424 | 1.009002 | 0.590389 |
| Warm retrained clean stack | 20260613 | 1 | 519 | 0.235105 | 0.458775 | 1.032753 | 0.551263 |
| Warm retrained clean stack | 20260614 | 1 | 519 | 0.261232 | 0.378492 | 1.060145 | 0.501292 |
| Warm-lite unified full-history retrained | 20260612 | 1 | 519 | 0.206123 | 0.329033 | 0.984585 | 0.568903 |
| Warm-lite unified full-history retrained | 20260613 | 1 | 519 | 0.183228 | 0.352937 | 1.102217 | 0.486995 |
| Warm-lite unified full-history retrained | 20260614 | 1 | 519 | 0.189950 | 0.463888 | 1.580843 | 0.551119 |
| Warm retrained clean stack | 20260612 | 2 | 519 | 0.211482 | 0.302689 | 0.885020 | 0.431543 |
| Warm retrained clean stack | 20260613 | 2 | 519 | 0.214275 | 0.335475 | 0.968765 | 0.490139 |
| Warm retrained clean stack | 20260614 | 2 | 519 | 0.205461 | 0.347145 | 1.227138 | 0.498124 |
| Warm-lite unified full-history retrained | 20260612 | 2 | 519 | 0.152662 | 0.360629 | 1.029033 | 0.441771 |
| Warm-lite unified full-history retrained | 20260613 | 2 | 519 | 0.154986 | 0.354378 | 0.986358 | 0.497607 |
| Warm-lite unified full-history retrained | 20260614 | 2 | 519 | 0.164993 | 0.339047 | 0.987864 | 0.496923 |
| Warm retrained clean stack | 20260612 | 3 | 519 | 0.166380 | 0.288041 | 0.942673 | 0.445064 |
| Warm retrained clean stack | 20260613 | 3 | 519 | 0.193540 | 0.333175 | 1.059539 | 0.494816 |
| Warm retrained clean stack | 20260614 | 3 | 519 | 0.188062 | 0.326521 | 0.966217 | 0.498678 |
| Warm-lite unified full-history retrained | 20260612 | 3 | 519 | 0.141822 | 0.359081 | 0.990953 | 0.539184 |
| Warm-lite unified full-history retrained | 20260613 | 3 | 519 | 0.149623 | 0.252402 | 0.865729 | 0.470513 |
| Warm-lite unified full-history retrained | 20260614 | 3 | 519 | 0.139678 | 0.289258 | 0.922329 | 0.477445 |
| Warm retrained clean stack | 20260612 | 4 | 519 | 0.164870 | 0.277032 | 0.897712 | 0.411816 |
| Warm retrained clean stack | 20260613 | 4 | 519 | 0.180833 | 0.294969 | 0.946168 | 0.470200 |
| Warm retrained clean stack | 20260614 | 4 | 519 | 0.159921 | 0.307590 | 0.972059 | 0.487217 |
| Warm-lite unified full-history retrained | 20260612 | 4 | 519 | 0.121152 | 0.328125 | 1.060020 | 0.428977 |
| Warm-lite unified full-history retrained | 20260613 | 4 | 519 | 0.116302 | 0.258614 | 0.826115 | 0.430330 |
| Warm-lite unified full-history retrained | 20260614 | 4 | 519 | 0.124534 | 0.313647 | 0.923777 | 0.503439 |
| Warm retrained clean stack | 20260612 | 5 | 519 | 0.144418 | 0.275957 | 0.949081 | 0.486594 |
| Warm retrained clean stack | 20260613 | 5 | 519 | 0.165847 | 0.283371 | 0.901034 | 0.435927 |
| Warm retrained clean stack | 20260614 | 5 | 519 | 0.160842 | 0.266226 | 0.798898 | 0.392213 |
| Warm-lite unified full-history retrained | 20260612 | 5 | 519 | 0.128457 | 0.283220 | 0.904091 | 0.394540 |
| Warm-lite unified full-history retrained | 20260613 | 5 | 519 | 0.121091 | 0.259683 | 0.816254 | 0.413856 |
| Warm-lite unified full-history retrained | 20260614 | 5 | 519 | 0.115584 | 0.238420 | 0.806018 | 0.421067 |
| Warm retrained clean stack | 20260612 | 6 | 519 | 0.147661 | 0.279228 | 0.906718 | 0.443931 |
| Warm retrained clean stack | 20260613 | 6 | 519 | 0.153196 | 0.280718 | 0.969392 | 0.479967 |
| Warm retrained clean stack | 20260614 | 6 | 519 | 0.151194 | 0.279116 | 0.884200 | 0.416424 |
| Warm-lite unified full-history retrained | 20260612 | 6 | 519 | 0.123039 | 0.241613 | 0.863950 | 0.364981 |
| Warm-lite unified full-history retrained | 20260613 | 6 | 519 | 0.123246 | 0.293298 | 0.897930 | 0.433961 |
| Warm-lite unified full-history retrained | 20260614 | 6 | 519 | 0.118907 | 0.248102 | 0.785432 | 0.413412 |

## 8. Training audit

| seed | train_rows | train_artists | median_train_rows_per_artist |
| --- | --- | --- | --- |
| 20260612 | 26914 | 1773 | 5 |
| 20260613 | 26914 | 1773 | 5 |
| 20260614 | 26914 | 1773 | 5 |

## 9. 해석 주의

- 이 결과는 단일 Warm-lite 운영 후보의 가능성 검증이다.
- full-history 표는 현재 Warm WMIN8 operational과 직접 비교하므로 운영 단순화 판단에 가장 중요하다.
- capped-history 표는 같은 unified 모델의 저이력/중이력 스트레스 테스트다.
- Cold처럼 같은 작가 가격 이력이 0건인 경우는 이 실험 대상이 아니다.

## 10. Config

```json
{
  "created_at": "2026-06-16T14:47:12",
  "experiment_id": "PP-ROUTE-CF5",
  "experiment_slug": "PP-ROUTE-CF5_unified_warm_lite_operational_comparison",
  "seeds": [
    20260612,
    20260613,
    20260614
  ],
  "k_values_for_stress_test": [
    1,
    2,
    3,
    4,
    5,
    6
  ],
  "base_eval_set": "Warm fixed-test rows",
  "eligibility_audit": {
    "warm_fixed_test_rows_total": 607,
    "k1_to_k6_eligible_rows": 519,
    "excluded_rows_with_less_than_6_history": 88,
    "full_history_min": 5,
    "full_history_max": 573
  },
  "unified_warm_lite_training": {
    "train_distribution": "actual full Warm train distribution",
    "group_stats": "5-fold internal stats for train, full train stats for full-history test",
    "model": "LightGBM Quantile full/lean + LightGBM objective=huber residual",
    "candidate": "lgbq_full_lean_avg + clip(0.50 * lgb_huber_residual, -0.10, +0.10)"
  },
  "comparators": {
    "full_history": "Warm WMIN8 operational",
    "capped_k1_to_k6": "CF3 Warm retrained clean stack"
  },
  "limitations": [
    "This experiment covers same-artist-history warm rows only; Cold/no-history routing remains separate.",
    "The k=1~6 capped table is a stress test; the full-history table is the primary operational simplification comparison.",
    "CF3 Warm clean stack is not exact historical WMIN8/PPV8 full artifact rebuild."
  ],
  "seconds": 416.63
}
```
