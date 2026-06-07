# PP-Y19 Cold PP-Y2 split/작가 bootstrap 안정성

- 목적: Cold 후속 실험에서 남은 validation 고정/재현성 gap을 닫는다.
- 원칙: test 결과만 보고 후보를 새로 고르지 않고, validation/OOF 또는 bootstrap 근거를 함께 기록한다.

## Test 결과 상위

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `pp_y2_baseline_stability` | `pp_y2_bootstrap_stability` | 0.4421 | 1.0484 | 3.3537 | 0.8567 |

## Map / Bootstrap

| experiment_id | candidate | row_bootstrap_MdAPE_median | row_bootstrap_MdAPE_ci_low | row_bootstrap_MdAPE_ci_high | row_bootstrap_MAPE_median | row_bootstrap_MAPE_ci_low | row_bootstrap_MAPE_ci_high | row_bootstrap_p95_APE_median | row_bootstrap_p95_APE_ci_low | row_bootstrap_p95_APE_ci_high | artist_bootstrap_MdAPE_median | artist_bootstrap_MdAPE_ci_low | artist_bootstrap_MdAPE_ci_high | artist_bootstrap_MAPE_median | artist_bootstrap_MAPE_ci_low | artist_bootstrap_MAPE_ci_high | artist_bootstrap_p95_APE_median | artist_bootstrap_p95_APE_ci_low | artist_bootstrap_p95_APE_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y19 | pp_y2_baseline_stability | 0.442147 | 0.421181 | 0.463496 | 1.0506 | 0.945469 | 1.16914 | 3.35373 | 2.94241 | 3.89784 | 0.439933 | 0.375108 | 0.525175 | 1.01008 | 0.554716 | 2.04176 | 3.07598 | 1.56261 | 6.46859 |
