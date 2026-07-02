# Official v0.1 Warm-lite API Route Validation

- Created at: 2026-06-13
- Scope: official `price_prediction_v0.1` API routing boundary validation
- Server: `http://127.0.0.1:8031`
- Script: `scripts/track6/verify_official_v0_1_warm_lite_api_routing.py`

## 1. Validation Purpose

- Confirm that the official v0.1 API uses the current operating route policy.
- Confirm that low-history artists are no longer forced into Cold fallback.
- Confirm deterministic API output for repeated calls with identical input.

## 2. Current Route Policy

| Route | User-facing name | Condition |
|---|---|---|
| `cold` | 참고 예측 | Reliable artist match is unavailable, or usable same-artist price history count is 0 |
| `warm_lite` | 저이력 기반 예측 | Artist match score is at least 0.80 and same-artist training price count is 1 to 4 |
| `warm` | 이력 기반 예측 | Artist match score is at least 0.80 and same-artist training price count is at least 5 |
| `review_required` | 확인 필요 | Homonym risk is high enough to require user or operator confirmation |

## 3. API Boundary Result

Command:

```bash
python3 scripts/track6/verify_official_v0_1_warm_lite_api_routing.py --repeat 3
```

| Case | Expected route | Actual route | Display route | Price | Same-artist price count | Adapter level | Repeat deterministic |
|---|---:|---:|---|---:|---:|---|---|
| Unknown artist | `cold` | `cold` | 참고 예측 | 2,793,675 KRW | - | `report_final_layer_proxy` | true |
| 1 history row | `warm_lite` | `warm_lite` | 저이력 기반 예측 | 1,340,064 KRW | 1 | `report_model_adapter` | true |
| 4 history rows | `warm_lite` | `warm_lite` | 저이력 기반 예측 | 1,383,465 KRW | 4 | `report_model_adapter` | true |
| 5 history rows | `warm` | `warm` | 이력 기반 예측 | 832,962 KRW | 5 | `report_model_adapter` | true |

## 4. Interpretation

- Route boundary is working as intended in the actual API endpoint.
- Warm-lite route uses the serialized low-history model adapter, not the DB/cache fallback.
- Warm 5+ route uses the WMIN8 runtime adapter, not the previous PP258 report-layer proxy.
- Identical inputs returned identical route, price, range, confidence, same-artist count, adapter level, and warnings across 3 repeated calls per case.

## 5. Remaining Work

- WMIN8 5+ history Warm target artifact is selected and exposed in model status.
- WMIN8 runtime adapter is connected to the official API endpoint.
- Remaining work:
  - Run WMIN8 fixed-test parity through the official API endpoint.
  - If parity differs by row, align the runtime feature construction for `stable_price_band`, `component_prediction_spread`, and `current_vs_stable_gap_abs` with the original experiment output.
