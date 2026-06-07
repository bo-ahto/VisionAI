# PP-S4 Cold cross-fitted meta stacking

- 목적: 모델 순서 변경, 목적함수 커스텀, 메타 조합이 기존 PP-Q/PP-R 이후 추가 개선을 주는지 확인한다.
- 근거: CatBoost/LightGBM의 MAPE/Quantile/Huber 목적함수와 stacking의 모델 출력값 결합 구조를 Track6 후보에 적용한다.
- 기준: 가중치, residual 모델, meta 모델, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `huber_crossfit_raw` | `test` | `crossfitted_meta_stacking` | `0.4765` | `1.2079` | `3.2827` | `0.9410` |
| `huber_crossfit_component_range_clipped` | `test` | `crossfitted_meta_stacking` | `0.4765` | `1.2079` | `3.2827` | `0.9409` |
| `ridge_10_crossfit_component_range_clipped` | `test` | `crossfitted_meta_stacking` | `0.4780` | `1.2203` | `3.4349` | `0.9377` |
| `ridge_10_crossfit_raw` | `test` | `crossfitted_meta_stacking` | `0.4780` | `1.2203` | `3.4349` | `0.9377` |
| `ridge_1_crossfit_component_range_clipped` | `test` | `crossfitted_meta_stacking` | `0.4786` | `1.2219` | `3.4454` | `0.9382` |
| `ridge_1_crossfit_raw` | `test` | `crossfitted_meta_stacking` | `0.4786` | `1.2219` | `3.4454` | `0.9383` |
| `huber_crossfit_raw` | `validation` | `crossfitted_meta_stacking` | `0.3533` | `0.5462` | `1.5559` | `0.6403` |
| `huber_crossfit_component_range_clipped` | `validation` | `crossfitted_meta_stacking` | `0.3547` | `0.5462` | `1.5559` | `0.6399` |
| `ridge_10_crossfit_component_range_clipped` | `validation` | `crossfitted_meta_stacking` | `0.3617` | `0.5554` | `1.5660` | `0.6392` |
| `ridge_10_crossfit_raw` | `validation` | `crossfitted_meta_stacking` | `0.3619` | `0.5555` | `1.5660` | `0.6394` |
| `ridge_1_crossfit_component_range_clipped` | `validation` | `crossfitted_meta_stacking` | `0.3631` | `0.5555` | `1.5698` | `0.6393` |
| `ridge_1_crossfit_raw` | `validation` | `crossfitted_meta_stacking` | `0.3634` | `0.5556` | `1.5698` | `0.6395` |
