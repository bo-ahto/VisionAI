# PP-WMIN9E Low-History Warm-Only Decision

## 1. Decision

- Warm-only 1~4 supported: `False`
- Reason: Overall 1~4 Warm-lite beats WMIN8 svc-core proxy on MdAPE/MAPE/p95. By k, Warm-lite wins all metrics for k=2 and k=3; k=1 and k=4 are mixed, but Warm-lite wins representative error and the overall 1~4 decision.

## 2. Per-k same-row comparison

| k | n | MdAPE_warm_lite | MAPE_warm_lite | p95_APE_warm_lite | MdAPE_warm_proxy | MAPE_warm_proxy | p95_APE_warm_proxy | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 621 | 0.120700 | 0.341500 | 0.955900 | 0.127100 | 0.340600 | 0.957300 | Mixed: Warm-lite wins MdAPE, p95_APE; Warm proxy wins MAPE |
| 2 | 489 | 0.118400 | 0.270700 | 0.877900 | 0.144800 | 0.282100 | 0.947800 | Warm-lite wins all primary metrics |
| 3 | 324 | 0.106000 | 0.254100 | 0.714200 | 0.119500 | 0.266100 | 0.748900 | Warm-lite wins all primary metrics |
| 4 | 513 | 0.092300 | 0.255700 | 0.788400 | 0.119000 | 0.263400 | 0.768200 | Mixed: Warm-lite wins MdAPE, MAPE; Warm proxy wins p95_APE |

## 3. Overall 1~4 comparison

| k | n | MdAPE_warm_lite | MAPE_warm_lite | p95_APE_warm_lite | MdAPE_warm_proxy | MAPE_warm_proxy | p95_APE_warm_proxy | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 1947 | 0.109200 | 0.286600 | 0.876500 | 0.129100 | 0.293200 | 0.916300 | Warm-lite wins all primary metrics |

## 4. Full WMIN8 direct-test status

- Status: `blocked_without_upstream_retraining`
- Blocker: The 1~4 LOO rows are held out from training rows. Calling the frozen full WMIN8 artifact would reuse PPV8/upstream models trained with those rows, so the result would be label-leaky. A clean full-WMIN8 low-history test requires retraining the PPV8/upstream Warm stack per hold-out.
