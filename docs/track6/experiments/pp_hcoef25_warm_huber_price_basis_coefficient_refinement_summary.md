# PP-HCOEF25 Warm Huber 보수적 계수/기준가 보정 실험

- 작성일: 2026-06-08 05:03
- 목적: HCOEF24의 MAPE 개선 신호를 더 작은 cap, 보수적 strength, 위험 구간 fallback으로 안정화할 수 있는지 검증.
- 현재 기준 후보: `hcoef_stable`.
- 최소 비교 기준: `current_70_30`.
- 선택 원칙: validation OOF/bootstrap에서 후보를 고르고 fixed test/0604는 확인용으로만 사용.

## 1. 실행 결론

- 새 운영 기본 후보는 없음. 상위 목적별 후보는 `hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25` (판단: MAPE 특화 후보, fixed test MdAPE/MAPE/p95 `0.1366/0.2727/0.8080`). `hcoef_stable`은 계속 현재 기준 후보로 유지.
- 현재 기준 fixed test: MdAPE `0.1388`, MAPE `0.2730`, p95 `0.8064`, RMSE_log `0.3988`.
- 최소 비교 기준 fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`, RMSE_log `0.3996`.
- HCOEF25는 HCOEF24의 위험 완화 기준가를 그대로 키우지 않고, `lowrisk_only`, `no_extreme`, `conservative`, `soft` guard로 이동폭을 조정한 실험임.

## 2. 후보 선택표

| candidate | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | bootstrap_all3_gate | fixed_test_p95_guard | stress0604_p95_guard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2080 | 0.6453 | 0.1366 | 0.2727 | 0.8080 | 0.2726 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2080 | 0.6453 | 0.1366 | 0.2727 | 0.8080 | 0.2726 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2080 | 0.6452 | 0.1366 | 0.2727 | 0.8080 | 0.2727 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2080 | 0.6452 | 0.1366 | 0.2727 | 0.8080 | 0.2727 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1259 | 0.2080 | 0.6440 | 0.1259 | 0.2080 | 0.6445 | 0.1366 | 0.2727 | 0.8080 | 0.2727 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1259 | 0.2080 | 0.6440 | 0.1259 | 0.2080 | 0.6445 | 0.1366 | 0.2727 | 0.8080 | 0.2727 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1256 | 0.2080 | 0.6440 | 0.1259 | 0.2080 | 0.6450 | 0.1366 | 0.2727 | 0.8080 | 0.2726 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1256 | 0.2080 | 0.6440 | 0.1259 | 0.2080 | 0.6450 | 0.1366 | 0.2727 | 0.8080 | 0.2726 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2080 | 0.6457 | 0.1367 | 0.2727 | 0.8080 | 0.2727 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2080 | 0.6457 | 0.1367 | 0.2727 | 0.8080 | 0.2727 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2080 | 0.6453 | 0.1368 | 0.2727 | 0.8080 | 0.2727 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2080 | 0.6453 | 0.1368 | 0.2727 | 0.8080 | 0.2727 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p02_s0p1 | MAPE 특화 후보 | 0.1253 | 0.2080 | 0.6448 | 0.1253 | 0.2081 | 0.6467 | 0.1371 | 0.2727 | 0.8074 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p02_s0p1 | MAPE 특화 후보 | 0.1253 | 0.2080 | 0.6448 | 0.1253 | 0.2081 | 0.6467 | 0.1371 | 0.2727 | 0.8074 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p02_s0p1 | MAPE 특화 후보 | 0.1253 | 0.2080 | 0.6448 | 0.1253 | 0.2081 | 0.6467 | 0.1371 | 0.2727 | 0.8074 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p02_s0p1 | MAPE 특화 후보 | 0.1253 | 0.2080 | 0.6448 | 0.1253 | 0.2081 | 0.6467 | 0.1371 | 0.2727 | 0.8074 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p02_s0p1 | MAPE 특화 후보 | 0.1253 | 0.2080 | 0.6448 | 0.1253 | 0.2081 | 0.6465 | 0.1371 | 0.2727 | 0.8074 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p02_s0p1 | MAPE 특화 후보 | 0.1253 | 0.2080 | 0.6448 | 0.1253 | 0.2081 | 0.6465 | 0.1371 | 0.2727 | 0.8074 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p02_s0p1 | MAPE 특화 후보 | 0.1253 | 0.2080 | 0.6448 | 0.1253 | 0.2081 | 0.6467 | 0.1371 | 0.2727 | 0.8074 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p02_s0p1 | MAPE 특화 후보 | 0.1253 | 0.2080 | 0.6448 | 0.1253 | 0.2081 | 0.6467 | 0.1371 | 0.2727 | 0.8074 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p1 | MAPE 특화 후보 | 0.1251 | 0.2079 | 0.6434 | 0.1255 | 0.2080 | 0.6453 | 0.1371 | 0.2726 | 0.8075 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p03_s0p1 | MAPE 특화 후보 | 0.1251 | 0.2079 | 0.6434 | 0.1255 | 0.2080 | 0.6453 | 0.1371 | 0.2726 | 0.8075 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p03_s0p1 | MAPE 특화 후보 | 0.1255 | 0.2079 | 0.6433 | 0.1255 | 0.2080 | 0.6452 | 0.1371 | 0.2726 | 0.8075 | 0.2729 | 0.3742 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p03_s0p1 | MAPE 특화 후보 | 0.1255 | 0.2079 | 0.6433 | 0.1255 | 0.2080 | 0.6452 | 0.1371 | 0.2726 | 0.8075 | 0.2729 | 0.3742 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p1 | MAPE 특화 후보 | 0.1251 | 0.2079 | 0.6435 | 0.1255 | 0.2080 | 0.6453 | 0.1371 | 0.2726 | 0.8075 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p1 | MAPE 특화 후보 | 0.1251 | 0.2079 | 0.6435 | 0.1255 | 0.2080 | 0.6453 | 0.1371 | 0.2726 | 0.8075 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p03_s0p1 | MAPE 특화 후보 | 0.1255 | 0.2079 | 0.6434 | 0.1255 | 0.2080 | 0.6453 | 0.1371 | 0.2727 | 0.8075 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p03_s0p1 | MAPE 특화 후보 | 0.1255 | 0.2079 | 0.6434 | 0.1255 | 0.2080 | 0.6453 | 0.1371 | 0.2727 | 0.8075 | 0.2729 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2081 | 0.6456 | 0.1374 | 0.2727 | 0.8080 | 0.2724 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2081 | 0.6456 | 0.1374 | 0.2727 | 0.8080 | 0.2724 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2081 | 0.6456 | 0.1374 | 0.2727 | 0.8080 | 0.2724 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2081 | 0.6456 | 0.1374 | 0.2727 | 0.8080 | 0.2724 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p01_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2081 | 0.6455 | 0.1374 | 0.2727 | 0.8080 | 0.2724 | 0.3743 | 0.9835 | False | False | True |
| hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p001_cap0p01_s0p25 | MAPE 특화 후보 | 0.1252 | 0.2080 | 0.6440 | 0.1252 | 0.2081 | 0.6455 | 0.1374 | 0.2727 | 0.8080 | 0.2724 | 0.3743 | 0.9835 | False | False | True |

## 3. Validation OOF 상위 후보

### Row OOF

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef25_loose_k16_soft_cap0p03_s0p5 | basis_component | 0.1247 | 0.2081 | 0.6433 | 0.3253 | -0.0013 | -0.0001 | -0.0046 |
| hcoef25_loose_k16_soft_cap0p03_s0p25 | basis_component | 0.1247 | 0.2081 | 0.6443 | 0.3252 | -0.0013 | -0.0001 | -0.0037 |
| hcoef25_loose_k8_soft_cap0p03_s0p1 | basis_component | 0.1247 | 0.2081 | 0.6479 | 0.3252 | -0.0013 | -0.0001 | -0.0000 |
| hcoef25_default_k8_soft_cap0p03_s0p1 | basis_component | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 |
| hcoef25_default_k16_soft_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3251 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_loose_k16_soft_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | -0.0000 |
| hcoef25_default_k8_conservative_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3251 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_loose_k8_conservative_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | -0.0000 |
| hcoef25_loose_k16_conservative_cap0p03_s0p25 | basis_component | 0.1247 | 0.2082 | 0.6469 | 0.3252 | -0.0013 | -0.0000 | -0.0011 |
| hcoef25_default_k8_no_extreme_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_loose_k8_no_extreme_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_loose_k16_no_extreme_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_default_k16_no_extreme_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | 0.0000 | 0.0000 |
| hcoef25_loose_k16_no_extreme_cap0p03_s0p25 | basis_component | 0.1247 | 0.2082 | 0.6462 | 0.3252 | -0.0013 | 0.0000 | -0.0017 |
| hcoef25_loose_k16_soft_cap0p02_s0p5 | basis_component | 0.1249 | 0.2080 | 0.6433 | 0.3252 | -0.0011 | -0.0002 | -0.0046 |
| hcoef25_loose_k8_conservative_cap0p03_s0p5 | basis_component | 0.1249 | 0.2082 | 0.6450 | 0.3253 | -0.0011 | -0.0000 | -0.0029 |
| hcoef25_default_k8_soft_cap0p015_s0p25 | basis_component | 0.1250 | 0.2081 | 0.6479 | 0.3251 | -0.0010 | -0.0001 | 0.0000 |
| hcoef25_loose_k8_soft_cap0p015_s0p25 | basis_component | 0.1250 | 0.2081 | 0.6471 | 0.3252 | -0.0010 | -0.0001 | -0.0008 |
| hcoef25_default_k16_soft_cap0p015_s0p25 | basis_component | 0.1250 | 0.2081 | 0.6479 | 0.3251 | -0.0010 | -0.0001 | 0.0000 |
| hcoef25_loose_k16_soft_cap0p015_s0p25 | basis_component | 0.1250 | 0.2081 | 0.6471 | 0.3252 | -0.0010 | -0.0001 | -0.0008 |

### Artist OOF

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef25_loose_k16_soft_cap0p03_s0p5 | basis_component | 0.1247 | 0.2081 | 0.6433 | 0.3253 | -0.0013 | -0.0001 | -0.0046 |
| hcoef25_loose_k16_soft_cap0p03_s0p25 | basis_component | 0.1247 | 0.2081 | 0.6443 | 0.3252 | -0.0013 | -0.0001 | -0.0037 |
| hcoef25_loose_k8_soft_cap0p03_s0p1 | basis_component | 0.1247 | 0.2081 | 0.6479 | 0.3252 | -0.0013 | -0.0001 | -0.0000 |
| hcoef25_default_k8_soft_cap0p03_s0p1 | basis_component | 0.1247 | 0.2081 | 0.6479 | 0.3251 | -0.0013 | -0.0001 | 0.0000 |
| hcoef25_default_k16_soft_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3251 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_loose_k16_soft_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | -0.0000 |
| hcoef25_default_k8_conservative_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3251 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_loose_k8_conservative_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | -0.0000 |
| hcoef25_loose_k16_conservative_cap0p03_s0p25 | basis_component | 0.1247 | 0.2082 | 0.6469 | 0.3252 | -0.0013 | -0.0000 | -0.0011 |
| hcoef25_default_k8_no_extreme_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_loose_k8_no_extreme_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_loose_k16_no_extreme_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | -0.0000 | 0.0000 |
| hcoef25_default_k16_no_extreme_cap0p03_s0p1 | basis_component | 0.1247 | 0.2082 | 0.6479 | 0.3252 | -0.0013 | 0.0000 | 0.0000 |
| hcoef25_loose_k16_no_extreme_cap0p03_s0p25 | basis_component | 0.1247 | 0.2082 | 0.6462 | 0.3252 | -0.0013 | 0.0000 | -0.0017 |
| hcoef25_loose_k16_soft_cap0p02_s0p5 | basis_component | 0.1249 | 0.2080 | 0.6433 | 0.3252 | -0.0011 | -0.0002 | -0.0046 |
| hcoef25_loose_k8_conservative_cap0p03_s0p5 | basis_component | 0.1249 | 0.2082 | 0.6450 | 0.3253 | -0.0011 | -0.0000 | -0.0029 |
| hcoef25_default_k8_soft_cap0p015_s0p25 | basis_component | 0.1250 | 0.2081 | 0.6479 | 0.3251 | -0.0010 | -0.0001 | 0.0000 |
| hcoef25_loose_k8_soft_cap0p015_s0p25 | basis_component | 0.1250 | 0.2081 | 0.6471 | 0.3252 | -0.0010 | -0.0001 | -0.0008 |
| hcoef25_default_k16_soft_cap0p015_s0p25 | basis_component | 0.1250 | 0.2081 | 0.6479 | 0.3251 | -0.0010 | -0.0001 | 0.0000 |
| hcoef25_loose_k16_soft_cap0p015_s0p25 | basis_component | 0.1250 | 0.2081 | 0.6471 | 0.3252 | -0.0010 | -0.0001 | -0.0008 |

## 4. Fixed Test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | 0.1366 | 0.2727 | 0.8080 | 0.3987 | -0.0022 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | 0.1366 | 0.2727 | 0.8080 | 0.3987 | -0.0022 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | 0.1366 | 0.2727 | 0.8080 | 0.3987 | -0.0022 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | 0.1366 | 0.2727 | 0.8080 | 0.3987 | -0.0022 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | 0.1366 | 0.2727 | 0.8080 | 0.3987 | -0.0022 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | 0.1366 | 0.2727 | 0.8080 | 0.3987 | -0.0022 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | 0.1366 | 0.2727 | 0.8080 | 0.3987 | -0.0022 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | 0.1366 | 0.2727 | 0.8080 | 0.3987 | -0.0022 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | 0.1367 | 0.2727 | 0.8080 | 0.3987 | -0.0021 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | 0.1367 | 0.2727 | 0.8080 | 0.3987 | -0.0021 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | 0.1368 | 0.2727 | 0.8080 | 0.3986 | -0.0020 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | 0.1368 | 0.2727 | 0.8080 | 0.3986 | -0.0020 | -0.0003 | 0.0016 |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p02_s0p1 | residual_huber | 0.1371 | 0.2727 | 0.8074 | 0.3987 | -0.0017 | -0.0003 | 0.0010 |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p02_s0p1 | residual_huber | 0.1371 | 0.2727 | 0.8074 | 0.3987 | -0.0017 | -0.0003 | 0.0010 |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p02_s0p1 | residual_huber | 0.1371 | 0.2727 | 0.8074 | 0.3987 | -0.0017 | -0.0003 | 0.0010 |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p02_s0p1 | residual_huber | 0.1371 | 0.2727 | 0.8074 | 0.3987 | -0.0017 | -0.0003 | 0.0010 |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p02_s0p1 | residual_huber | 0.1371 | 0.2727 | 0.8074 | 0.3987 | -0.0017 | -0.0003 | 0.0010 |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p02_s0p1 | residual_huber | 0.1371 | 0.2727 | 0.8074 | 0.3987 | -0.0017 | -0.0003 | 0.0010 |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p02_s0p1 | residual_huber | 0.1371 | 0.2727 | 0.8074 | 0.3987 | -0.0017 | -0.0002 | 0.0010 |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p02_s0p1 | residual_huber | 0.1371 | 0.2727 | 0.8074 | 0.3987 | -0.0017 | -0.0002 | 0.0010 |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p1 | residual_huber | 0.1371 | 0.2726 | 0.8075 | 0.3986 | -0.0017 | -0.0004 | 0.0012 |
| hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p03_s0p1 | residual_huber | 0.1371 | 0.2726 | 0.8075 | 0.3986 | -0.0017 | -0.0004 | 0.0012 |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p03_s0p1 | residual_huber | 0.1371 | 0.2726 | 0.8075 | 0.3986 | -0.0017 | -0.0003 | 0.0012 |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p03_s0p1 | residual_huber | 0.1371 | 0.2726 | 0.8075 | 0.3986 | -0.0017 | -0.0003 | 0.0012 |

## 5. 0604 Stress Test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppv8_service_proxy | source | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 |
| hcoef25_direct_huber_guarded_default_a0p01_cap0p02_s0p25 | direct_huber_capped | 0.2698 | 0.3744 | 0.9840 | 1.3071 | -0.0033 | 0.0000 | 0.0006 |
| hcoef25_direct_huber_guarded_loose_a0p01_cap0p02_s0p25 | direct_huber_capped | 0.2699 | 0.3745 | 0.9840 | 1.3071 | -0.0031 | 0.0001 | 0.0006 |
| hcoef25_direct_huber_guarded_strict_a0p01_cap0p02_s0p25 | direct_huber_capped | 0.2700 | 0.3744 | 0.9840 | 1.3071 | -0.0031 | 0.0001 | 0.0006 |
| hcoef25_direct_huber_guarded_default_a0p01_cap0p03_s0p25 | direct_huber_capped | 0.2709 | 0.3744 | 0.9860 | 1.3067 | -0.0022 | 0.0000 | 0.0026 |
| hcoef25_direct_huber_guarded_loose_a0p01_cap0p03_s0p25 | direct_huber_capped | 0.2709 | 0.3744 | 0.9860 | 1.3068 | -0.0022 | 0.0000 | 0.0026 |
| hcoef25_direct_huber_guarded_strict_a0p01_cap0p03_s0p25 | direct_huber_capped | 0.2709 | 0.3744 | 0.9860 | 1.3067 | -0.0022 | 0.0000 | 0.0026 |
| hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 0.2724 | 0.3741 | 0.9865 | 1.3069 | -0.0006 | -0.0002 | 0.0030 |
| hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 0.2724 | 0.3741 | 0.9865 | 1.3069 | -0.0006 | -0.0002 | 0.0030 |
| hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p01_cap0p02_s0p25 | residual_huber | 0.2724 | 0.3742 | 0.9850 | 1.3072 | -0.0006 | -0.0001 | 0.0015 |
| hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p01_cap0p02_s0p25 | residual_huber | 0.2724 | 0.3742 | 0.9850 | 1.3072 | -0.0006 | -0.0001 | 0.0015 |
| hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p01_cap0p01_s0p25 | residual_huber | 0.2724 | 0.3743 | 0.9835 | 1.3075 | -0.0006 | -0.0001 | 0.0000 |
| hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p01_cap0p01_s0p25 | residual_huber | 0.2724 | 0.3743 | 0.9835 | 1.3075 | -0.0006 | -0.0001 | 0.0000 |
| hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 0.2724 | 0.3741 | 0.9865 | 1.3069 | -0.0006 | -0.0002 | 0.0030 |
| hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 0.2724 | 0.3741 | 0.9865 | 1.3069 | -0.0006 | -0.0002 | 0.0030 |
| hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p001_cap0p02_s0p25 | residual_huber | 0.2724 | 0.3742 | 0.9850 | 1.3072 | -0.0006 | -0.0001 | 0.0015 |
| hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p001_cap0p02_s0p25 | residual_huber | 0.2724 | 0.3742 | 0.9850 | 1.3072 | -0.0006 | -0.0001 | 0.0015 |
| hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p001_cap0p01_s0p25 | residual_huber | 0.2724 | 0.3743 | 0.9835 | 1.3075 | -0.0006 | -0.0001 | 0.0000 |
| hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p001_cap0p01_s0p25 | residual_huber | 0.2724 | 0.3743 | 0.9835 | 1.3075 | -0.0006 | -0.0001 | 0.0000 |
| hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 0.2724 | 0.3741 | 0.9865 | 1.3069 | -0.0006 | -0.0002 | 0.0030 |

## 6. 주요 계수 해석

- 계수는 표준화된 피처 기준이며 방향성과 상대 영향 비교용.
- HCOEF25의 핵심은 유사 작품 기준가가 좋은 구간에서는 작게 반영하고, 위험 구간에서는 `hcoef_stable` 쪽으로 되돌리는 것.
- `hcoef25_guard_factor_*`는 기준가를 얼마나 믿을지 정하는 보수성 피처.

| candidate | method | feature | standardized_coefficient | raw_role | direction | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| current_70_30 | source | current_70_30 | 1.0000 | source_prediction | positive | 서비스 v0.1 70:30 기준 후보 |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0294 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | svc_group_n_log | 0.0175 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | pred_spread | 0.0014 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | quantile_width | -0.0001 | residual_log | lowers prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | ppv8_minus_stable | -0.0029 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_default_k8_conservative_gap | -0.0040 | residual_log | lowers prediction | HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | coverage_numeric | -0.0068 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | svc_minus_stable | -0.0095 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_low_risk_flag | -0.0151 | residual_log | lowers prediction | HCOEF23 위험 신호가 없는 저위험 구간 여부다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | current_minus_stable | -0.0322 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef23_risk_score | -0.0537 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0294 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | svc_group_n_log | 0.0175 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | pred_spread | 0.0014 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | quantile_width | -0.0001 | residual_log | lowers prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | ppv8_minus_stable | -0.0029 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_default_k8_conservative_gap | -0.0040 | residual_log | lowers prediction | HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | coverage_numeric | -0.0068 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | svc_minus_stable | -0.0095 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_low_risk_flag | -0.0151 | residual_log | lowers prediction | HCOEF23 위험 신호가 없는 저위험 구간 여부다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | current_minus_stable | -0.0322 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef23_risk_score | -0.0537 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0301 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | svc_group_n_log | 0.0176 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | pred_spread | 0.0011 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | quantile_width | -0.0001 | residual_log | lowers prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | ppv8_minus_stable | -0.0028 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | coverage_numeric | -0.0065 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_default_k8_no_extreme_gap | -0.0090 | residual_log | lowers prediction | HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | svc_minus_stable | -0.0098 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_low_risk_flag | -0.0148 | residual_log | lowers prediction | HCOEF23 위험 신호가 없는 저위험 구간 여부다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | current_minus_stable | -0.0329 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef23_risk_score | -0.0546 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0301 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | svc_group_n_log | 0.0176 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | pred_spread | 0.0011 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | quantile_width | -0.0001 | residual_log | lowers prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | ppv8_minus_stable | -0.0028 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | coverage_numeric | -0.0065 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_default_k8_no_extreme_gap | -0.0090 | residual_log | lowers prediction | HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | svc_minus_stable | -0.0098 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_low_risk_flag | -0.0148 | residual_log | lowers prediction | HCOEF23 위험 신호가 없는 저위험 구간 여부다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | current_minus_stable | -0.0329 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef23_risk_score | -0.0546 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0292 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | svc_group_n_log | 0.0172 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | pred_spread | 0.0014 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | quantile_width | -0.0003 | residual_log | lowers prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | ppv8_minus_stable | -0.0029 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_loose_k8_conservative_gap | -0.0049 | residual_log | lowers prediction | HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | coverage_numeric | -0.0070 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | svc_minus_stable | -0.0094 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_low_risk_flag | -0.0149 | residual_log | lowers prediction | HCOEF23 위험 신호가 없는 저위험 구간 여부다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | current_minus_stable | -0.0321 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef23_risk_score | -0.0533 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0292 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | svc_group_n_log | 0.0172 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | pred_spread | 0.0014 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | quantile_width | -0.0003 | residual_log | lowers prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | ppv8_minus_stable | -0.0029 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_loose_k8_conservative_gap | -0.0049 | residual_log | lowers prediction | HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | coverage_numeric | -0.0070 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | svc_minus_stable | -0.0094 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_low_risk_flag | -0.0149 | residual_log | lowers prediction | HCOEF23 위험 신호가 없는 저위험 구간 여부다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | current_minus_stable | -0.0321 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef23_risk_score | -0.0533 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0298 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | svc_group_n_log | 0.0172 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | pred_spread | 0.0010 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | quantile_width | -0.0003 | residual_log | lowers prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | ppv8_minus_stable | -0.0030 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | coverage_numeric | -0.0069 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_loose_k8_no_extreme_gap | -0.0071 | residual_log | lowers prediction | HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | svc_minus_stable | -0.0094 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_low_risk_flag | -0.0148 | residual_log | lowers prediction | HCOEF23 위험 신호가 없는 저위험 구간 여부다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | current_minus_stable | -0.0322 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef23_risk_score | -0.0537 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0298 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | svc_group_n_log | 0.0172 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | pred_spread | 0.0010 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | quantile_width | -0.0003 | residual_log | lowers prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | ppv8_minus_stable | -0.0030 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | coverage_numeric | -0.0069 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_loose_k8_no_extreme_gap | -0.0071 | residual_log | lowers prediction | HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | svc_minus_stable | -0.0094 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef25_low_risk_flag | -0.0148 | residual_log | lowers prediction | HCOEF23 위험 신호가 없는 저위험 구간 여부다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | current_minus_stable | -0.0322 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | residual_huber | hcoef23_risk_score | -0.0537 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | residual_huber | hcoef25_high_risk_flag | 0.0297 | residual_log | raises prediction | quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다. |

## 7. 기준가 Coverage

| policy | split | basis_level | rows | covered_rows | covered_share | median_n_when_covered |
| --- | --- | --- | --- | --- | --- | --- |
| loose | validation | artist_medium_support_size | 519 | 310 | 0.5973 | 6.0000 |
| loose | validation | artist_size | 519 | 370 | 0.7129 | 6.0000 |
| loose | validation | artist | 519 | 519 | 1.0000 | 12.0000 |
| loose | validation | medium_support_size | 519 | 479 | 0.9229 | 875.0000 |
| loose | validation | medium_category_support_size | 519 | 479 | 0.9229 | 875.0000 |
| loose | validation | medium_size | 519 | 504 | 0.9711 | 1600.0000 |
| loose | test | artist_medium_support_size | 607 | 354 | 0.5832 | 7.0000 |
| loose | test | artist_size | 607 | 433 | 0.7133 | 7.0000 |
| loose | test | artist | 607 | 607 | 1.0000 | 13.0000 |
| loose | test | medium_support_size | 607 | 576 | 0.9489 | 938.5000 |
| loose | test | medium_category_support_size | 607 | 576 | 0.9489 | 938.5000 |
| loose | test | medium_size | 607 | 593 | 0.9769 | 1606.0000 |
| loose | 0604_ex50 | artist_medium_support_size | 829 | 182 | 0.2195 | 4.5000 |
| loose | 0604_ex50 | artist_size | 829 | 494 | 0.5959 | 6.0000 |
| loose | 0604_ex50 | artist | 829 | 755 | 0.9107 | 12.0000 |
| loose | 0604_ex50 | medium_support_size | 829 | 452 | 0.5452 | 1277.0000 |
| loose | 0604_ex50 | medium_category_support_size | 829 | 452 | 0.5452 | 1277.0000 |
| loose | 0604_ex50 | medium_size | 829 | 582 | 0.7021 | 1402.0000 |
| default | validation | artist_medium_support_size | 519 | 202 | 0.3892 | 8.0000 |
| default | validation | artist_size | 519 | 267 | 0.5145 | 9.0000 |
| default | validation | artist | 519 | 519 | 1.0000 | 12.0000 |
| default | validation | medium_support_size | 519 | 469 | 0.9037 | 894.0000 |
| default | validation | medium_category_support_size | 519 | 469 | 0.9037 | 894.0000 |
| default | validation | medium_size | 519 | 502 | 0.9672 | 1600.0000 |
| default | test | artist_medium_support_size | 607 | 247 | 0.4069 | 8.0000 |
| default | test | artist_size | 607 | 312 | 0.5140 | 9.0000 |
| default | test | artist | 607 | 607 | 1.0000 | 13.0000 |
| default | test | medium_support_size | 607 | 552 | 0.9094 | 983.0000 |
| default | test | medium_category_support_size | 607 | 552 | 0.9094 | 983.0000 |
| default | test | medium_size | 607 | 589 | 0.9703 | 1606.0000 |
| default | 0604_ex50 | artist_medium_support_size | 829 | 91 | 0.1098 | 7.0000 |
| default | 0604_ex50 | artist_size | 829 | 315 | 0.3800 | 8.0000 |
| default | 0604_ex50 | artist | 829 | 727 | 0.8770 | 12.0000 |
| default | 0604_ex50 | medium_support_size | 829 | 429 | 0.5175 | 1277.0000 |
| default | 0604_ex50 | medium_category_support_size | 829 | 429 | 0.5175 | 1277.0000 |
| default | 0604_ex50 | medium_size | 829 | 576 | 0.6948 | 1402.0000 |
| strict | validation | artist_medium_support_size | 519 | 85 | 0.1638 | 15.0000 |
| strict | validation | artist_size | 519 | 125 | 0.2408 | 15.0000 |
| strict | validation | artist | 519 | 339 | 0.6532 | 21.0000 |
| strict | validation | medium_support_size | 519 | 440 | 0.8478 | 983.0000 |
| strict | validation | medium_category_support_size | 519 | 440 | 0.8478 | 983.0000 |
| strict | validation | medium_size | 519 | 486 | 0.9364 | 1606.0000 |
| strict | test | artist_medium_support_size | 607 | 113 | 0.1862 | 17.0000 |
| strict | test | artist_size | 607 | 152 | 0.2504 | 17.0000 |
| strict | test | artist | 607 | 363 | 0.5980 | 21.0000 |
| strict | test | medium_support_size | 607 | 529 | 0.8715 | 1059.0000 |
| strict | test | medium_category_support_size | 607 | 529 | 0.8715 | 1059.0000 |
| strict | test | medium_size | 607 | 581 | 0.9572 | 1606.0000 |
| strict | 0604_ex50 | artist_medium_support_size | 829 | 27 | 0.0326 | 15.0000 |
| strict | 0604_ex50 | artist_size | 829 | 131 | 0.1580 | 16.0000 |
| strict | 0604_ex50 | artist | 829 | 431 | 0.5199 | 20.0000 |
| strict | 0604_ex50 | medium_support_size | 829 | 391 | 0.4717 | 1277.0000 |
| strict | 0604_ex50 | medium_category_support_size | 829 | 391 | 0.4717 | 1277.0000 |
| strict | 0604_ex50 | medium_size | 829 | 576 | 0.6948 | 1402.0000 |

## 8. 잔차/큰 오차 구간

| scope | split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | median_residual_log | mean_residual_log | mean_abs_move_log | over_50pct_error_rate | over_100pct_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_020_plus | 402 | 0.5239 | 0.6071 | 1.3189 | 0.3621 | 0.7716 | 0.2761 | 0.5199 | 0.0622 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_020_plus | 402 | 0.5130 | 0.5988 | 1.5918 | 0.1562 | 0.5032 | 0.5894 | 0.5124 | 0.1169 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 0.2961 | 0.6185 | 0.0225 | 0.4328 | 0.0448 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p02_s0p1 | gap_band | gap_020_plus | 402 | 0.4332 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0018 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p02_s0p1 | gap_band | gap_020_plus | 402 | 0.4332 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0018 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_020_plus | 402 | 0.4330 | 0.5044 | 0.9999 | 0.2799 | 0.6042 | 0.0024 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_010_020 | 128 | 0.3203 | 0.4882 | 2.1936 | -0.0384 | 0.0639 | 0.3592 | 0.3359 | 0.0703 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_020_plus | 402 | 0.3131 | 0.4234 | 1.1510 | 0.1623 | 0.2613 | 0.6194 | 0.2910 | 0.0622 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_010_020 | 128 | 0.2777 | 0.3693 | 0.9720 | -0.0734 | 0.0324 | 0.0620 | 0.2891 | 0.0469 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | -0.0556 | 0.0461 | 0.0217 | 0.3125 | 0.0391 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2226 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2226 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2226 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2226 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2226 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2226 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2226 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2226 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2228 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_010_020 | 128 | 0.2228 | 0.3400 | 0.8743 | -0.0490 | 0.0386 | 0.0024 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p02_s0p1 | gap_band | gap_010_020 | 128 | 0.2238 | 0.3399 | 0.8740 | -0.0485 | 0.0389 | 0.0018 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p02_s0p1 | gap_band | gap_010_020 | 128 | 0.2238 | 0.3399 | 0.8740 | -0.0485 | 0.0389 | 0.0018 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0399 | 0.0000 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_010_020 | 128 | 0.2540 | 0.3269 | 0.7844 | 0.0520 | 0.0782 | 0.1447 | 0.2656 | 0.0156 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_005_010 | 125 | 0.1883 | 0.3007 | 0.9169 | 0.0567 | 0.0972 | 0.1938 | 0.1680 | 0.0400 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_005_010 | 125 | 0.1764 | 0.2618 | 0.7685 | 0.0806 | 0.0930 | 0.0754 | 0.0880 | 0.0240 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_005_010 | 125 | 0.1613 | 0.2612 | 0.9572 | 0.0380 | 0.0895 | 0.0361 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.0641 | 0.0905 | 0.0190 | 0.0880 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2516 | 0.9558 | 0.0378 | 0.0867 | 0.0023 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2516 | 0.9558 | 0.0378 | 0.0867 | 0.0023 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2516 | 0.9558 | 0.0378 | 0.0868 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2516 | 0.9558 | 0.0378 | 0.0868 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2516 | 0.9558 | 0.0378 | 0.0867 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2516 | 0.9558 | 0.0378 | 0.0867 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2515 | 0.9558 | 0.0378 | 0.0867 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2515 | 0.9558 | 0.0378 | 0.0867 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2515 | 0.9558 | 0.0378 | 0.0867 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2515 | 0.9558 | 0.0378 | 0.0867 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2515 | 0.9558 | 0.0378 | 0.0867 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_005_010 | 125 | 0.1477 | 0.2515 | 0.9558 | 0.0378 | 0.0867 | 0.0024 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p02_s0p1 | gap_band | gap_005_010 | 125 | 0.1481 | 0.2515 | 0.9556 | 0.0383 | 0.0869 | 0.0018 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p02_s0p1 | gap_band | gap_005_010 | 125 | 0.1481 | 0.2515 | 0.9556 | 0.0383 | 0.0869 | 0.0018 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0872 | 0.0000 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_000_003 | 119 | 0.1387 | 0.2330 | 0.7125 | -0.0071 | 0.0833 | 0.1325 | 0.0924 | 0.0084 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_003_005 | 55 | 0.1531 | 0.2296 | 0.5665 | -0.0167 | 0.1022 | 0.2173 | 0.1636 | 0.0182 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_000_003 | 119 | 0.1025 | 0.1967 | 0.5508 | 0.0404 | 0.0785 | 0.0222 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.0401 | 0.0761 | 0.0164 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_000_003 | 119 | 0.1162 | 0.1942 | 0.5405 | 0.0395 | 0.0705 | 0.0125 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_003_005 | 55 | 0.1039 | 0.1925 | 0.4983 | 0.0427 | 0.0915 | 0.0397 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_003_005 | 55 | 0.1117 | 0.1922 | 0.5421 | 0.0171 | 0.0778 | 0.0356 | 0.0727 | 0.0000 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.0305 | 0.0819 | 0.0227 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p02_s0p1 | gap_band | gap_000_003 | 119 | 0.1031 | 0.1887 | 0.5290 | 0.0269 | 0.0699 | 0.0015 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p02_s0p1 | gap_band | gap_000_003 | 119 | 0.1031 | 0.1887 | 0.5290 | 0.0269 | 0.0699 | 0.0015 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p01_s0p25 | gap_band | gap_000_003 | 119 | 0.1025 | 0.1886 | 0.5288 | 0.0266 | 0.0699 | 0.0021 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p01_s0p25 | gap_band | gap_000_003 | 119 | 0.1025 | 0.1886 | 0.5288 | 0.0266 | 0.0699 | 0.0021 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_000_003 | 119 | 0.1053 | 0.1886 | 0.5300 | 0.0272 | 0.0704 | 0.0000 | 0.0756 | 0.0084 |

## 9. Bootstrap 요약

| source_scope | validation_scheme | candidate | method | n_bootstrap | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | mean_delta_RMSE_log_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_row | row_bootstrap | hcoef25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5 | direct_huber_capped | 300 | -0.0011 | -0.0006 | -0.0037 | -0.0010 | 0.6533 | 0.9067 | 0.7833 | 0.4933 | 0.8667 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0004 | -0.0006 | -0.0037 | -0.0009 | 0.5833 | 0.9700 | 0.8100 | 0.4800 | 0.8933 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0004 | -0.0006 | -0.0037 | -0.0009 | 0.5833 | 0.9700 | 0.8100 | 0.4800 | 0.8933 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0004 | -0.0006 | -0.0037 | -0.0009 | 0.5833 | 0.9700 | 0.8100 | 0.4800 | 0.8933 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0004 | -0.0006 | -0.0037 | -0.0009 | 0.5833 | 0.9700 | 0.8100 | 0.4800 | 0.8933 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0028 | -0.0009 | 0.6367 | 0.9567 | 0.7500 | 0.4767 | 0.8767 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0028 | -0.0009 | 0.6367 | 0.9567 | 0.7500 | 0.4767 | 0.8767 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0028 | -0.0009 | 0.6367 | 0.9567 | 0.7500 | 0.4767 | 0.8767 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0028 | -0.0009 | 0.6367 | 0.9567 | 0.7500 | 0.4767 | 0.8767 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0003 | -0.0006 | -0.0037 | -0.0009 | 0.5700 | 0.9700 | 0.8100 | 0.4700 | 0.8933 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0003 | -0.0006 | -0.0037 | -0.0009 | 0.5700 | 0.9700 | 0.8100 | 0.4700 | 0.8933 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0005 | -0.0006 | -0.0032 | -0.0009 | 0.6000 | 0.9667 | 0.7867 | 0.4667 | 0.8967 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0005 | -0.0006 | -0.0032 | -0.0009 | 0.6000 | 0.9667 | 0.7867 | 0.4667 | 0.8967 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0005 | -0.0006 | -0.0032 | -0.0009 | 0.5867 | 0.9667 | 0.7867 | 0.4633 | 0.8867 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0005 | -0.0006 | -0.0032 | -0.0009 | 0.5867 | 0.9667 | 0.7867 | 0.4633 | 0.8867 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0007 | -0.0006 | -0.0028 | -0.0009 | 0.6200 | 0.9500 | 0.7500 | 0.4600 | 0.8733 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0007 | -0.0006 | -0.0028 | -0.0009 | 0.6200 | 0.9500 | 0.7500 | 0.4600 | 0.8733 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0005 | -0.0006 | -0.0031 | -0.0008 | 0.5700 | 0.9667 | 0.7833 | 0.4567 | 0.8733 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0005 | -0.0006 | -0.0031 | -0.0008 | 0.5700 | 0.9667 | 0.7833 | 0.4567 | 0.8733 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0009 | -0.0006 | -0.0023 | -0.0009 | 0.6567 | 0.9633 | 0.7000 | 0.4533 | 0.8733 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_strict_no_extreme_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0009 | -0.0006 | -0.0023 | -0.0009 | 0.6567 | 0.9633 | 0.7000 | 0.4533 | 0.8733 |
| validation_oof_row | row_bootstrap | hcoef25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5 | direct_huber_capped | 300 | -0.0013 | -0.0007 | -0.0048 | -0.0014 | 0.6367 | 0.8733 | 0.7433 | 0.4533 | 0.8300 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0004 | -0.0006 | -0.0032 | -0.0008 | 0.5567 | 0.9700 | 0.7833 | 0.4500 | 0.8733 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0004 | -0.0006 | -0.0032 | -0.0008 | 0.5567 | 0.9700 | 0.7833 | 0.4500 | 0.8733 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0007 | -0.0023 | -0.0009 | 0.6467 | 0.9700 | 0.6900 | 0.4467 | 0.8667 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_loose_conservative_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0007 | -0.0023 | -0.0009 | 0.6467 | 0.9700 | 0.6900 | 0.4467 | 0.8667 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0023 | -0.0009 | 0.6433 | 0.9633 | 0.7067 | 0.4433 | 0.8767 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0023 | -0.0009 | 0.6433 | 0.9633 | 0.7067 | 0.4433 | 0.8767 |
| validation_oof_row | artist_bootstrap | hcoef25_direct_huber_guarded_strict_a0p01_cap0p02_s0p5 | direct_huber_capped | 300 | -0.0015 | -0.0006 | -0.0028 | -0.0011 | 0.6800 | 0.8933 | 0.7300 | 0.4433 | 0.8700 |
| validation_oof_row | row_bootstrap | hcoef25_direct_huber_guarded_strict_a0p01_cap0p03_s0p25 | direct_huber_capped | 300 | -0.0007 | -0.0005 | -0.0024 | -0.0008 | 0.6133 | 0.9200 | 0.7500 | 0.4400 | 0.8600 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0003 | -0.0006 | -0.0033 | -0.0008 | 0.5433 | 0.9667 | 0.7733 | 0.4400 | 0.8567 |
| validation_oof_row | row_bootstrap | hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0003 | -0.0006 | -0.0033 | -0.0008 | 0.5433 | 0.9667 | 0.7733 | 0.4400 | 0.8567 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0022 | -0.0009 | 0.6333 | 0.9667 | 0.6867 | 0.4367 | 0.8567 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_conservative_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0022 | -0.0009 | 0.6333 | 0.9667 | 0.6867 | 0.4367 | 0.8567 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_no_extreme_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0007 | -0.0006 | -0.0023 | -0.0009 | 0.6233 | 0.9700 | 0.6933 | 0.4367 | 0.8533 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p001_cap0p02_s0p1 | residual_huber | 300 | -0.0003 | -0.0002 | -0.0009 | -0.0003 | 0.6167 | 0.9767 | 0.7033 | 0.4333 | 0.8700 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_loose_lowrisk_only_guard_core_a0p01_cap0p02_s0p1 | residual_huber | 300 | -0.0003 | -0.0002 | -0.0009 | -0.0003 | 0.6167 | 0.9767 | 0.7033 | 0.4333 | 0.8700 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p001_cap0p02_s0p1 | residual_huber | 300 | -0.0003 | -0.0002 | -0.0009 | -0.0003 | 0.6167 | 0.9767 | 0.7033 | 0.4333 | 0.8700 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_lowrisk_only_guard_core_a0p01_cap0p02_s0p1 | residual_huber | 300 | -0.0003 | -0.0002 | -0.0009 | -0.0003 | 0.6167 | 0.9767 | 0.7033 | 0.4333 | 0.8700 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p001_cap0p02_s0p1 | residual_huber | 300 | -0.0003 | -0.0002 | -0.0009 | -0.0003 | 0.6167 | 0.9767 | 0.7033 | 0.4333 | 0.8700 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_strict_lowrisk_only_guard_core_a0p01_cap0p02_s0p1 | residual_huber | 300 | -0.0003 | -0.0002 | -0.0009 | -0.0003 | 0.6167 | 0.9767 | 0.7033 | 0.4333 | 0.8700 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_no_extreme_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0007 | -0.0006 | -0.0023 | -0.0009 | 0.6200 | 0.9700 | 0.6933 | 0.4333 | 0.8533 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_loose_no_extreme_guard_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0007 | -0.0006 | -0.0022 | -0.0009 | 0.6333 | 0.9600 | 0.6833 | 0.4300 | 0.8567 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_loose_no_extreme_guard_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0007 | -0.0006 | -0.0022 | -0.0009 | 0.6333 | 0.9600 | 0.6833 | 0.4300 | 0.8567 |
| validation_oof_row | artist_bootstrap | hcoef25_resid_huber_default_lowrisk_only_guard_reliability_a0p001_cap0p02_s0p25 | residual_huber | 300 | -0.0003 | -0.0003 | -0.0026 | -0.0004 | 0.5933 | 0.8833 | 0.7833 | 0.4300 | 0.8400 |

## 10. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/coverage_summary.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`