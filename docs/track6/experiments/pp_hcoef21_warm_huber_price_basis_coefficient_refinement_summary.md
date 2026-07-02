# PP-HCOEF21 Warm Huber 가변 기준가/계수 검증 요약

- 실험 폴더: `experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement`
- 실행 스크립트: `scripts/track6/run_pp_hcoef21_warm_huber_price_basis_coefficient_refinement.py`
- 목적: 단일 70:30 기준가를 표본 수/coverage/quantile 폭 기반 가변 기준가로 바꾸고, Huber residual로 작게 보정 가능한지 검증.

## 핵심 결과

| candidate | decision | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 기준 후보 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 |
| hcoef21_resid_huber_adaptive_interactions_a0p001_cap0p02_s0p25 | OOF 개선 후보 | 0.1388 | 0.2727 | 0.8099 | 0.2696 | 0.3731 | 0.9834 |
| hcoef21_resid_huber_adaptive_interactions_a0p01_cap0p02_s0p25 | OOF 개선 후보 | 0.1388 | 0.2727 | 0.8099 | 0.2696 | 0.3731 | 0.9834 |
| hcoef21_resid_ridge_adaptive_interactions_a1_cap0p02_s0p25 | OOF 개선 후보 | 0.1388 | 0.2728 | 0.8097 | 0.2698 | 0.3730 | 0.9834 |
| hcoef21_resid_ridge_adaptive_interactions_a0p1_cap0p02_s0p25 | OOF 개선 후보 | 0.1388 | 0.2728 | 0.8097 | 0.2698 | 0.3730 | 0.9834 |
| hcoef21_resid_huber_adaptive_reliability_a0p001_cap0p02_s0p25 | OOF 개선 후보 | 0.1389 | 0.2727 | 0.8100 | 0.2725 | 0.3733 | 0.9834 |
| hcoef21_resid_huber_adaptive_reliability_a0p01_cap0p02_s0p25 | OOF 개선 후보 | 0.1389 | 0.2727 | 0.8100 | 0.2725 | 0.3733 | 0.9834 |
| hcoef21_resid_ridge_adaptive_reliability_a0p1_cap0p02_s0p25 | OOF 개선 후보 | 0.1389 | 0.2729 | 0.8100 | 0.2748 | 0.3733 | 0.9834 |

## 해석

- 가변 기준가는 Huber가 설명할 수 있는 기준가/신뢰도 피처를 명확히 만들기 위한 실험임.
- 운영 후보 판단은 fixed test 단독이 아니라 validation OOF, artist OOF, bootstrap을 우선함.
- 0604는 외부 stress test로만 사용함.
