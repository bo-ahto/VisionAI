# PP-MONLIVE1 실서비스 로그 모니터 (R1~R5)

```json
{
  "n_rows": 637,
  "R1_rule_violations": 0,
  "R2_route_share": {
    "warm": 0.9717,
    "cold": 0.0141,
    "warm_lite": 0.0094,
    "review_required": 0.0047
  },
  "R2_wlite_k_dist": {
    "4": 0.667,
    "1": 0.333
  },
  "R3_aux_missing_band_share": 0.0,
  "R4_wlite_perf_by_k": {
    "status": "no_labels (sale feedback < min)"
  },
  "R5_out_of_dict_homonym": {
    "status": "pending",
    "n_decisions": 0,
    "n_queue_pending": 92,
    "rho_measured": null,
    "rho_operating": 0.05,
    "note": "검수 결정 0건 — 라벨 기반 ρ 측정 불가, PP-RHO1 proxy 5% 유지. 대기 큐 92건 해소 시 측정 가능"
  },
  "alerts": [
    "없음"
  ],
  "_data_provenance": {
    "source": "data/track6/service_v0_1/price_prediction_v0_1.sqlite",
    "prediction_events": 637,
    "confirmed_sale_labels": 0,
    "raw_sale_feedback": 1,
    "identity_review_decisions": 0,
    "identity_review_queue_pending": 92
  }
}
```
