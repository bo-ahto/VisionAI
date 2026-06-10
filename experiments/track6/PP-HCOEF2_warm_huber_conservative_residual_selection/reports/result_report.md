# PP-HCOEF2 Warm Huber 보수적 잔차 보정 선택 검증

- 작성일: 2026-06-07 22:18
- source: PP-HCOEF1 outputs.
- 목적: test만 좋은 후보를 배제하고, validation에서 명확히 개선된 작은 보정 후보만 분리.
- 선택 기준: Huber 잔차 보정 후보, validation 3개 지표 모두 개선, cap <= 0.05, strength <= 0.75.

## 1. 실행 결론

- 반복 재검증 후보: `residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75`. validation에서 3개 지표를 모두 개선하고 cap=0.03, strength=0.75로 보정 폭이 작다.
- 이 후보는 즉시 v0.1 반영이 아니라 반복 split/OOF 재검증 후보로 둔다.

## 2. 선택 후보

| candidate | feature_set | alpha | cap | strength | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | selection_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | resid_basis_size_reliability | 0.0001 | 0.0300 | 0.7500 | 0.1263 | 0.2090 | 0.6376 | -0.0042 | -0.0020 | -0.0204 | 0.2846 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.75 | resid_basis_size_reliability | 0.0010 | 0.0300 | 0.7500 | 0.1263 | 0.2090 | 0.6376 | -0.0042 | -0.0020 | -0.0204 | 0.2846 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.75 | resid_basis_size_reliability | 0.0100 | 0.0300 | 0.7500 | 0.1263 | 0.2090 | 0.6376 | -0.0042 | -0.0020 | -0.0204 | 0.2846 |
| residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | resid_basis_gap | 0.0001 | 0.0300 | 0.7500 | 0.1282 | 0.2092 | 0.6382 | -0.0024 | -0.0018 | -0.0199 | 0.2855 |
| residual_huber_resid_basis_gap_alpha0.001_cap0.03_s0.75 | resid_basis_gap | 0.0010 | 0.0300 | 0.7500 | 0.1282 | 0.2092 | 0.6382 | -0.0024 | -0.0018 | -0.0199 | 0.2855 |
| residual_huber_resid_basis_gap_alpha0.01_cap0.03_s0.75 | resid_basis_gap | 0.0100 | 0.0300 | 0.7500 | 0.1282 | 0.2092 | 0.6382 | -0.0024 | -0.0018 | -0.0199 | 0.2855 |
| residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.05_s0.75 | resid_basis_size_reliability | 0.0001 | 0.0500 | 0.7500 | 0.1293 | 0.2081 | 0.6370 | -0.0012 | -0.0030 | -0.0210 | 0.2863 |
| residual_huber_resid_basis_size_reliability_alpha0.001_cap0.05_s0.75 | resid_basis_size_reliability | 0.0010 | 0.0500 | 0.7500 | 0.1293 | 0.2081 | 0.6370 | -0.0012 | -0.0030 | -0.0210 | 0.2863 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.75 | resid_basis_size_reliability | 0.0100 | 0.0500 | 0.7500 | 0.1294 | 0.2081 | 0.6370 | -0.0011 | -0.0030 | -0.0210 | 0.2863 |
| residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | resid_basis_size_reliability | 0.0100 | 0.0500 | 0.5000 | 0.1250 | 0.2088 | 0.6448 | -0.0055 | -0.0022 | -0.0133 | 0.2868 |

## 3. 선택 후보 validation/test/0604 확인

| split | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE | delta_MAPE | delta_p95_APE | improve_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | 0.2752 | 0.3749 | 0.9834 | 1.3083 | -0.0027 | -0.0025 | -0.0036 | 3 |
| test | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | 0.1406 | 0.2745 | 0.8318 | 0.4000 | 0.0001 | -0.0003 | -0.0012 | 2 |
| validation | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | 0.1282 | 0.2092 | 0.6382 | 0.3263 | -0.0024 | -0.0018 | -0.0199 | 3 |
| 0604_ex50 | residual_huber_resid_basis_gap_alpha0.001_cap0.03_s0.75 | 0.2752 | 0.3749 | 0.9834 | 1.3083 | -0.0027 | -0.0025 | -0.0036 | 3 |
| test | residual_huber_resid_basis_gap_alpha0.001_cap0.03_s0.75 | 0.1406 | 0.2745 | 0.8318 | 0.4000 | 0.0001 | -0.0003 | -0.0012 | 2 |
| validation | residual_huber_resid_basis_gap_alpha0.001_cap0.03_s0.75 | 0.1282 | 0.2092 | 0.6382 | 0.3263 | -0.0024 | -0.0018 | -0.0199 | 3 |
| 0604_ex50 | residual_huber_resid_basis_gap_alpha0.01_cap0.03_s0.75 | 0.2752 | 0.3749 | 0.9834 | 1.3083 | -0.0027 | -0.0025 | -0.0036 | 3 |
| test | residual_huber_resid_basis_gap_alpha0.01_cap0.03_s0.75 | 0.1406 | 0.2745 | 0.8318 | 0.4000 | 0.0001 | -0.0003 | -0.0012 | 2 |
| validation | residual_huber_resid_basis_gap_alpha0.01_cap0.03_s0.75 | 0.1282 | 0.2092 | 0.6382 | 0.3263 | -0.0024 | -0.0018 | -0.0199 | 3 |
| 0604_ex50 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | 0.2749 | 0.3746 | 0.9834 | 1.3083 | -0.0031 | -0.0027 | -0.0036 | 3 |
| test | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | 0.1392 | 0.2735 | 0.8059 | 0.3991 | -0.0013 | -0.0013 | -0.0272 | 3 |
| validation | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | 0.1263 | 0.2090 | 0.6376 | 0.3261 | -0.0042 | -0.0020 | -0.0204 | 3 |
| 0604_ex50 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.05_s0.75 | 0.2654 | 0.3734 | 0.9792 | 1.3059 | -0.0125 | -0.0040 | -0.0079 | 3 |
| test | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.05_s0.75 | 0.1443 | 0.2728 | 0.8183 | 0.3988 | 0.0038 | -0.0020 | -0.0148 | 2 |
| validation | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.05_s0.75 | 0.1293 | 0.2081 | 0.6370 | 0.3245 | -0.0012 | -0.0030 | -0.0210 | 3 |
| 0604_ex50 | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.75 | 0.2749 | 0.3746 | 0.9834 | 1.3083 | -0.0031 | -0.0027 | -0.0036 | 3 |
| test | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.75 | 0.1392 | 0.2735 | 0.8059 | 0.3991 | -0.0013 | -0.0013 | -0.0272 | 3 |
| validation | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.75 | 0.1263 | 0.2090 | 0.6376 | 0.3261 | -0.0042 | -0.0020 | -0.0204 | 3 |
| 0604_ex50 | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.05_s0.75 | 0.2654 | 0.3734 | 0.9792 | 1.3059 | -0.0125 | -0.0040 | -0.0079 | 3 |
| test | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.05_s0.75 | 0.1443 | 0.2728 | 0.8183 | 0.3988 | 0.0038 | -0.0020 | -0.0148 | 2 |
| validation | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.05_s0.75 | 0.1293 | 0.2081 | 0.6370 | 0.3245 | -0.0012 | -0.0030 | -0.0210 | 3 |
| 0604_ex50 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.75 | 0.2749 | 0.3746 | 0.9834 | 1.3083 | -0.0031 | -0.0027 | -0.0036 | 3 |
| test | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.75 | 0.1392 | 0.2735 | 0.8059 | 0.3991 | -0.0013 | -0.0013 | -0.0272 | 3 |
| validation | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.75 | 0.1263 | 0.2090 | 0.6376 | 0.3262 | -0.0042 | -0.0020 | -0.0204 | 3 |
| 0604_ex50 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | -0.0049 | -0.0030 | -0.0036 | 3 |
| test | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | -0.0017 | -0.0018 | -0.0267 | 3 |
| validation | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | 0.1250 | 0.2088 | 0.6448 | 0.3258 | -0.0055 | -0.0022 | -0.0133 | 3 |
| 0604_ex50 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.75 | 0.2655 | 0.3734 | 0.9792 | 1.3059 | -0.0125 | -0.0040 | -0.0079 | 3 |
| test | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.75 | 0.1443 | 0.2727 | 0.8183 | 0.3988 | 0.0038 | -0.0020 | -0.0148 | 2 |
| validation | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.75 | 0.1294 | 0.2081 | 0.6370 | 0.3246 | -0.0011 | -0.0030 | -0.0210 | 3 |

## 4. Bootstrap 안정성

| sample_type | candidate | mean_delta_MdAPE | mean_delta_MAPE | mean_delta_p95_APE | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artist_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.75 | -0.0001 | -0.0013 | 0.0018 | 0.4820 | 0.9100 | 0.4880 |
| artist_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.75 | -0.0001 | -0.0013 | 0.0018 | 0.4800 | 0.9040 | 0.4880 |
| artist_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | -0.0001 | -0.0013 | 0.0018 | 0.4800 | 0.9040 | 0.4880 |
| artist_bootstrap | current_70_30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_bootstrap | residual_huber_resid_basis_gap_alpha0.001_cap0.03_s0.75 | 0.0002 | -0.0003 | 0.0124 | 0.4740 | 0.5940 | 0.3200 |
| artist_bootstrap | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | 0.0002 | -0.0003 | 0.0124 | 0.4740 | 0.5940 | 0.3200 |
| row_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.03_s0.75 | -0.0007 | -0.0012 | 0.0010 | 0.5480 | 0.9020 | 0.5040 |
| row_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.001_cap0.03_s0.75 | -0.0007 | -0.0012 | 0.0010 | 0.5480 | 0.9020 | 0.5040 |
| row_bootstrap | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | -0.0007 | -0.0012 | 0.0010 | 0.5480 | 0.9020 | 0.5040 |
| row_bootstrap | residual_huber_resid_basis_gap_alpha0.001_cap0.03_s0.75 | -0.0004 | -0.0002 | 0.0115 | 0.5360 | 0.6020 | 0.3080 |
| row_bootstrap | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | -0.0004 | -0.0002 | 0.0115 | 0.5360 | 0.6020 | 0.3080 |
| row_bootstrap | current_70_30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 5. 산출물

- `outputs/selected_conservative_candidates.csv`
- `outputs/selected_candidate_confirm_metrics.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`