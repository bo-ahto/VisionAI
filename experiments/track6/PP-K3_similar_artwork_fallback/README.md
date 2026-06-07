# PP-K3 유사 작품 fallback 예측

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `baseline` | `base_model` | `0.3899` | `0.7118` | `1.9728` | `0.6871` |
| `cold` | `baseline` | `base_model` | `0.3899` | `0.7118` | `1.9728` | `0.6871` |
| `cold` | `baseline` | `base_model` | `0.3899` | `0.7118` | `1.9728` | `0.6871` |
| `cold` | `similar_fallback_min_rows_5` | `similar_artwork_fallback` | `0.4506` | `0.7708` | `2.7310` | `0.7676` |
| `cold` | `similar_fallback_min_rows_10` | `similar_artwork_fallback` | `0.4506` | `0.7708` | `2.7310` | `0.7676` |
| `cold` | `similar_fallback_min_rows_3` | `similar_artwork_fallback` | `0.4506` | `0.7712` | `2.7310` | `0.7677` |
| `warm` | `similar_fallback_min_rows_3` | `similar_artwork_fallback` | `0.1996` | `0.3672` | `1.1230` | `0.5157` |
| `warm` | `baseline` | `base_model` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `baseline` | `base_model` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `baseline` | `base_model` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `similar_fallback_min_rows_5` | `similar_artwork_fallback` | `0.2193` | `0.4073` | `1.2702` | `0.6369` |
| `warm` | `similar_fallback_min_rows_10` | `similar_artwork_fallback` | `0.2347` | `0.4219` | `1.3194` | `0.6524` |
