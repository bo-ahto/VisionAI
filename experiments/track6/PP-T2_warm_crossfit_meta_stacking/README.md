# PP-T2 Warm cross-fitted meta stacking

- 목적: Warm 최종 후보 PP-R5 이후에도 조합, 메타 보정, 2차 residual 안정화로 개선 여지가 있는지 확인한다.
- 기준: 가중치, meta 모델, 보정값, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `huber_crossfit_component_range_clipped` | `test` | `warm_crossfit_meta_stacking` | `0.1705` | `0.2916` | `0.9582` | `0.4098` |
| `huber_crossfit_raw` | `test` | `warm_crossfit_meta_stacking` | `0.1750` | `0.2976` | `0.9582` | `0.4143` |
| `ridge_1_crossfit_component_range_clipped` | `test` | `warm_crossfit_meta_stacking` | `0.1864` | `0.3015` | `1.0245` | `0.4155` |
| `ridge_10_crossfit_component_range_clipped` | `test` | `warm_crossfit_meta_stacking` | `0.1868` | `0.3000` | `0.9970` | `0.4147` |
| `ridge_10_crossfit_raw` | `test` | `warm_crossfit_meta_stacking` | `0.1943` | `0.3109` | `1.0555` | `0.4230` |
| `ridge_1_crossfit_raw` | `test` | `warm_crossfit_meta_stacking` | `0.1960` | `0.3132` | `1.0667` | `0.4245` |
| `huber_crossfit_component_range_clipped` | `validation` | `warm_crossfit_meta_stacking` | `0.1564` | `0.2610` | `0.8080` | `0.3774` |
| `huber_crossfit_raw` | `validation` | `warm_crossfit_meta_stacking` | `0.1568` | `0.2628` | `0.8216` | `0.3741` |
| `ridge_10_crossfit_component_range_clipped` | `validation` | `warm_crossfit_meta_stacking` | `0.1569` | `0.2648` | `0.8149` | `0.3763` |
| `ridge_10_crossfit_raw` | `validation` | `warm_crossfit_meta_stacking` | `0.1595` | `0.2706` | `0.8443` | `0.3746` |
| `ridge_1_crossfit_component_range_clipped` | `validation` | `warm_crossfit_meta_stacking` | `0.1613` | `0.2656` | `0.8119` | `0.3767` |
| `ridge_1_crossfit_raw` | `validation` | `warm_crossfit_meta_stacking` | `0.1626` | `0.2723` | `0.8495` | `0.3755` |
