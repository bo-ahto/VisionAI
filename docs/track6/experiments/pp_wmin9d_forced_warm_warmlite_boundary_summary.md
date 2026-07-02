# PP-WMIN9D Warm/Warm-lite boundary forced comparison summary

## Summary

- 5+ history rows: forced Warm-lite is compared against the selected WMIN8 Warm prediction on the same 607 fixed-test rows.
- k=1 rows: existing PP-WMIN9C same-row low-history comparison is reused because full WMIN8 is a 5+ router; the comparable Warm-like evidence is WMIN8 svc-core proxy.

## 5+ history same-row result

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| forced_warm_lite_on_5plus | 607 | 0.108722 | 0.248054 | 0.837824 | 0.393963 |
| wmin8_warm_selected | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 |

## 5+ history by train-history bin

| history_bin | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| 5_to_9 | forced_warm_lite_on_5plus | 244 | 0.112847 | 0.232965 | 0.838649 | 0.384414 |
| 5_to_9 | wmin8_warm_selected | 244 | 0.133761 | 0.231396 | 0.798541 | 0.363216 |
| 50_plus | forced_warm_lite_on_5plus | 72 | 0.074689 | 0.152254 | 0.485094 | 0.240245 |
| 50_plus | wmin8_warm_selected | 72 | 0.080039 | 0.131918 | 0.413381 | 0.202646 |
| 10_to_19 | forced_warm_lite_on_5plus | 150 | 0.117635 | 0.358908 | 1.297520 | 0.425538 |
| 10_to_19 | wmin8_warm_selected | 150 | 0.085733 | 0.330417 | 1.385369 | 0.420408 |
| 20_to_49 | forced_warm_lite_on_5plus | 141 | 0.086443 | 0.205152 | 0.779498 | 0.436261 |
| 20_to_49 | wmin8_warm_selected | 141 | 0.097632 | 0.195871 | 0.745711 | 0.418551 |

## k=1 Warm-like result

| candidate | k | n | MdAPE | MAPE | p95_APE |
| --- | --- | --- | --- | --- | --- |
| warm_lite | 1 | 621 | 0.120700 | 0.341500 | 0.955900 |
| wmin8_svc_core | 1 | 621 | 0.127100 | 0.340600 | 0.957300 |

## Interpretation

- 5+ same-row fixed-test shows forced Warm-lite is worse than WMIN8 on MdAPE, MAPE, and p95_APE.
- For k=1, Warm-lite beats WMIN8 svc-core proxy on MdAPE and p95_APE; MAPE is checked separately because the two are nearly tied.

## Caveats

- Forced Warm-lite on 5+ is a counterfactual measurement, not a valid production route.
- k=1 Warm-like evidence uses WMIN8 svc-core proxy from PP-WMIN9C, not full WMIN8.
