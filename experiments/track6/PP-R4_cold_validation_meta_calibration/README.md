# PP-R4 Cold validation meta 보정

- 목적: PP-Q 이후 남은 개선 여지를 모델 조합, 단계 보정, 라우팅, 메타 보정으로 확인한다.
- 기준: 가중치, 보정값, threshold, meta 모델은 validation에서만 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | scope | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---|---:|---:|---:|---:|
| `huber_meta_component_range_clipped` | `cold` | `test` | `validation_meta_calibration` | `0.4796` | `1.2148` | `3.4131` | `0.9436` |
| `huber_meta_raw` | `cold` | `test` | `validation_meta_calibration` | `0.4806` | `1.2157` | `3.4131` | `0.9440` |
| `ridge_10_component_range_clipped` | `cold` | `test` | `validation_meta_calibration` | `0.4819` | `1.2247` | `3.4260` | `0.9399` |
| `ridge_10_raw` | `cold` | `test` | `validation_meta_calibration` | `0.4820` | `1.2259` | `3.4260` | `0.9402` |
| `ridge_0_1_component_range_clipped` | `cold` | `test` | `validation_meta_calibration` | `0.4825` | `1.2266` | `3.4243` | `0.9399` |
| `ridge_1_component_range_clipped` | `cold` | `test` | `validation_meta_calibration` | `0.4840` | `1.2265` | `3.4268` | `0.9399` |
| `ridge_0_1_raw` | `cold` | `test` | `validation_meta_calibration` | `0.4840` | `1.2278` | `3.4243` | `0.9402` |
| `ridge_1_raw` | `cold` | `test` | `validation_meta_calibration` | `0.4841` | `1.2277` | `3.4268` | `0.9403` |
| `positive_linear_raw` | `cold` | `test` | `validation_meta_calibration` | `0.4873` | `1.2737` | `3.6879` | `0.9533` |
| `positive_linear_component_range_clipped` | `cold` | `test` | `validation_meta_calibration` | `0.4873` | `1.2737` | `3.6879` | `0.9533` |
| `huber_meta_component_range_clipped` | `cold` | `validation` | `validation_meta_calibration` | `0.3550` | `0.5416` | `1.5292` | `0.6374` |
| `huber_meta_raw` | `cold` | `validation` | `validation_meta_calibration` | `0.3552` | `0.5418` | `1.5422` | `0.6376` |
| `positive_linear_raw` | `cold` | `validation` | `validation_meta_calibration` | `0.3564` | `0.5659` | `1.6137` | `0.6452` |
| `positive_linear_component_range_clipped` | `cold` | `validation` | `validation_meta_calibration` | `0.3564` | `0.5659` | `1.6137` | `0.6452` |
| `ridge_1_component_range_clipped` | `cold` | `validation` | `validation_meta_calibration` | `0.3616` | `0.5516` | `1.5750` | `0.6363` |
| `ridge_1_raw` | `cold` | `validation` | `validation_meta_calibration` | `0.3617` | `0.5519` | `1.5954` | `0.6365` |
| `ridge_0_1_component_range_clipped` | `cold` | `validation` | `validation_meta_calibration` | `0.3619` | `0.5516` | `1.5796` | `0.6363` |
| `ridge_0_1_raw` | `cold` | `validation` | `validation_meta_calibration` | `0.3624` | `0.5519` | `1.5958` | `0.6365` |
| `ridge_10_component_range_clipped` | `cold` | `validation` | `validation_meta_calibration` | `0.3628` | `0.5517` | `1.5636` | `0.6364` |
| `ridge_10_raw` | `cold` | `validation` | `validation_meta_calibration` | `0.3633` | `0.5520` | `1.5714` | `0.6366` |
