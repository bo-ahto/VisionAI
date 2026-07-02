# PP-HCOEF24 Warm Huber 위험 완화 기준가 생성 실험

- 작성일: 2026-06-08 04:50
- 목적: HCOEF23에서 확인한 위험 구간에서 유사 작품 기준가 이동을 줄이고, Huber 계수 후보가 현재 Warm 안정 후보를 넘는지 검증.
- 현재 기준 후보: `hcoef_stable`.
- 최소 비교 기준: `current_70_30`.
- 선택 원칙: validation OOF/bootstrap에서 후보를 고르고 fixed test/0604는 확인용으로만 사용.

## 1. 실행 결론

- 새 운영 기본 후보는 없음. 상위 목적별 후보는 `hcoef24_default_risk_basis_k8_cap0p05_s0p75` (판단: MAPE 특화 후보, fixed test MdAPE/MAPE/p95 `0.1383/0.2729/0.8079`). `hcoef_stable`은 계속 현재 기준 후보로 유지.
- 현재 기준 fixed test: MdAPE `0.1388`, MAPE `0.2730`, p95 `0.8064`, RMSE_log `0.3988`.
- 최소 비교 기준 fixed test: MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`, RMSE_log `0.3996`.
- HCOEF24는 HCOEF4/5의 loose 기준가를 반복하지 않고, `qwidth_extreme`, `gap_020_plus`, `n_10_19`, `spread_extreme` 구간에서 기준가 반영 강도를 낮춘 실험임.

## 2. 후보 선택표

| candidate | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | bootstrap_all3_gate | fixed_test_p95_guard | stress0604_p95_guard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | False | True | True |
| hcoef24_default_risk_basis_k8_cap0p05_s0p75 | MAPE 특화 후보 | 0.1245 | 0.2082 | 0.6484 | 0.1245 | 0.2082 | 0.6484 | 0.1383 | 0.2729 | 0.8079 | 0.2734 | 0.3736 | 0.9835 | False | False | True |
| hcoef24_loose_risk_basis_k8_cap0p05_s0p75 | MAPE 특화 후보 | 0.1253 | 0.2084 | 0.6477 | 0.1253 | 0.2084 | 0.6477 | 0.1384 | 0.2717 | 0.8079 | 0.2731 | 0.3727 | 0.9835 | False | False | True |
| hcoef24_loose_risk_basis_k8_cap0p05_s0p5 | MAPE 특화 후보 | 0.1251 | 0.2081 | 0.6479 | 0.1251 | 0.2081 | 0.6479 | 0.1388 | 0.2719 | 0.8063 | 0.2775 | 0.3732 | 0.9835 | False | True | True |
| hcoef24_default_risk_basis_k8_cap0p05_s0p5 | MAPE 특화 후보 | 0.1247 | 0.2080 | 0.6484 | 0.1247 | 0.2080 | 0.6484 | 0.1388 | 0.2727 | 0.8064 | 0.2775 | 0.3739 | 0.9835 | False | True | True |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | MAPE 특화 후보 | 0.1262 | 0.2078 | 0.6404 | 0.1259 | 0.2079 | 0.6404 | 0.1388 | 0.2725 | 0.8071 | 0.2716 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | MAPE 특화 후보 | 0.1262 | 0.2078 | 0.6404 | 0.1259 | 0.2079 | 0.6404 | 0.1388 | 0.2725 | 0.8071 | 0.2716 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | MAPE 특화 후보 | 0.1262 | 0.2078 | 0.6404 | 0.1259 | 0.2079 | 0.6404 | 0.1388 | 0.2726 | 0.8071 | 0.2714 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | MAPE 특화 후보 | 0.1262 | 0.2078 | 0.6404 | 0.1259 | 0.2079 | 0.6404 | 0.1388 | 0.2726 | 0.8071 | 0.2714 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | MAPE 특화 후보 | 0.1263 | 0.2078 | 0.6404 | 0.1259 | 0.2079 | 0.6404 | 0.1388 | 0.2726 | 0.8071 | 0.2714 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | MAPE 특화 후보 | 0.1263 | 0.2078 | 0.6404 | 0.1259 | 0.2079 | 0.6404 | 0.1388 | 0.2726 | 0.8071 | 0.2714 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_default_risk_basis_k8_cap0p03_s0p75 | MAPE 특화 후보 | 0.1249 | 0.2078 | 0.6484 | 0.1249 | 0.2078 | 0.6484 | 0.1389 | 0.2726 | 0.8064 | 0.2753 | 0.3738 | 0.9835 | False | True | True |
| hcoef24_default_risk_basis_k16_cap0p05_s0p5 | MAPE 특화 후보 | 0.1247 | 0.2081 | 0.6482 | 0.1247 | 0.2081 | 0.6482 | 0.1389 | 0.2730 | 0.8064 | 0.2750 | 0.3739 | 0.9835 | False | True | True |
| hcoef24_resid_huber_loose_risk_basis_reliability_a0p01_cap0p02_s0p25 | MAPE 특화 후보 | 0.1263 | 0.2078 | 0.6423 | 0.1263 | 0.2082 | 0.6423 | 0.1394 | 0.2729 | 0.8077 | 0.2765 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_resid_huber_loose_risk_basis_reliability_a0p001_cap0p02_s0p25 | MAPE 특화 후보 | 0.1263 | 0.2078 | 0.6423 | 0.1263 | 0.2082 | 0.6423 | 0.1394 | 0.2729 | 0.8077 | 0.2765 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_default_risk_basis_k16_cap0p03_s0p75 | MAPE 특화 후보 | 0.1249 | 0.2079 | 0.6484 | 0.1249 | 0.2079 | 0.6484 | 0.1395 | 0.2727 | 0.8064 | 0.2753 | 0.3739 | 0.9835 | False | True | True |
| hcoef24_default_risk_basis_k8_cap0p08_s0p25 | MAPE 특화 후보 | 0.1253 | 0.2081 | 0.6479 | 0.1253 | 0.2081 | 0.6479 | 0.1395 | 0.2729 | 0.8064 | 0.2731 | 0.3740 | 0.9835 | False | True | True |
| hcoef24_strict_risk_basis_k8_cap0p03_s0p25 | MAPE 특화 후보 | 0.1266 | 0.2081 | 0.6479 | 0.1266 | 0.2081 | 0.6479 | 0.1395 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | False | True | True |
| hcoef24_default_risk_basis_k8_cap0p03_s0p5 | MAPE 특화 후보 | 0.1253 | 0.2078 | 0.6484 | 0.1253 | 0.2078 | 0.6484 | 0.1399 | 0.2726 | 0.8064 | 0.2731 | 0.3740 | 0.9835 | False | True | True |
| hcoef24_default_risk_basis_k16_cap0p03_s0p5 | MAPE 특화 후보 | 0.1260 | 0.2079 | 0.6482 | 0.1260 | 0.2079 | 0.6482 | 0.1399 | 0.2727 | 0.8064 | 0.2731 | 0.3740 | 0.9835 | False | True | True |
| hcoef24_resid_huber_default_risk_basis_reliability_a0p01_cap0p02_s0p25 | MAPE 특화 후보 | 0.1263 | 0.2079 | 0.6462 | 0.1263 | 0.2081 | 0.6433 | 0.1401 | 0.2729 | 0.8091 | 0.2765 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_resid_huber_default_risk_basis_reliability_a0p001_cap0p02_s0p25 | MAPE 특화 후보 | 0.1263 | 0.2079 | 0.6462 | 0.1263 | 0.2081 | 0.6433 | 0.1401 | 0.2729 | 0.8091 | 0.2765 | 0.3736 | 0.9835 | False | False | False |
| hcoef24_loose_risk_basis_k8_cap0p03_s0p75 | MAPE 특화 후보 | 0.1258 | 0.2078 | 0.6477 | 0.1258 | 0.2078 | 0.6477 | 0.1401 | 0.2717 | 0.8063 | 0.2753 | 0.3732 | 0.9835 | False | True | True |
| hcoef24_loose_risk_basis_k16_cap0p03_s0p75 | MAPE 특화 후보 | 0.1249 | 0.2080 | 0.6479 | 0.1249 | 0.2080 | 0.6479 | 0.1402 | 0.2719 | 0.8063 | 0.2753 | 0.3733 | 0.9835 | False | True | True |
| hcoef24_loose_risk_basis_k8_cap0p03_s0p5 | MAPE 특화 후보 | 0.1260 | 0.2078 | 0.6479 | 0.1260 | 0.2078 | 0.6479 | 0.1403 | 0.2720 | 0.8063 | 0.2734 | 0.3736 | 0.9835 | False | True | True |
| hcoef24_loose_risk_basis_k16_cap0p03_s0p5 | MAPE 특화 후보 | 0.1260 | 0.2079 | 0.6479 | 0.1260 | 0.2079 | 0.6479 | 0.1403 | 0.2722 | 0.8063 | 0.2734 | 0.3737 | 0.9835 | False | True | True |
| hcoef24_loose_risk_basis_k16_cap0p05_s0p5 | MAPE 특화 후보 | 0.1233 | 0.2082 | 0.6479 | 0.1233 | 0.2082 | 0.6479 | 0.1403 | 0.2724 | 0.8063 | 0.2750 | 0.3735 | 0.9835 | False | True | True |
| hcoef24_loose_risk_basis_k8_cap0p03_s0p25 | MAPE 특화 후보 | 0.1260 | 0.2080 | 0.6448 | 0.1260 | 0.2080 | 0.6448 | 0.1403 | 0.2725 | 0.8063 | 0.2734 | 0.3740 | 0.9835 | False | True | True |
| hcoef24_loose_risk_basis_k8_cap0p08_s0p5 | MAPE 특화 후보 | 0.1260 | 0.2086 | 0.6479 | 0.1260 | 0.2086 | 0.6479 | 0.1403 | 0.2725 | 0.8100 | 0.2735 | 0.3729 | 0.9835 | False | False | True |
| hcoef24_loose_risk_basis_k16_cap0p03_s0p25 | MAPE 특화 후보 | 0.1247 | 0.2080 | 0.6416 | 0.1247 | 0.2080 | 0.6416 | 0.1403 | 0.2726 | 0.8063 | 0.2734 | 0.3740 | 0.9835 | False | True | True |

## 3. Validation OOF 상위 후보

### Row OOF

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.1147 | 0.2046 | 0.6431 | 0.3202 | -0.0112 | -0.0036 | -0.0048 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.1153 | 0.2046 | 0.6449 | 0.3203 | -0.0107 | -0.0037 | -0.0030 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p5 | direct_huber_capped | 0.1185 | 0.2052 | 0.6448 | 0.3213 | -0.0075 | -0.0030 | -0.0032 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p75 | direct_huber_capped | 0.1186 | 0.2057 | 0.6488 | 0.3215 | -0.0074 | -0.0025 | 0.0008 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p75 | direct_huber_capped | 0.1188 | 0.2056 | 0.6497 | 0.3215 | -0.0072 | -0.0027 | 0.0018 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p5 | direct_huber_capped | 0.1191 | 0.2061 | 0.6448 | 0.3224 | -0.0069 | -0.0021 | -0.0032 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p5 | direct_huber_capped | 0.1201 | 0.2051 | 0.6412 | 0.3214 | -0.0059 | -0.0031 | -0.0068 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p5 | direct_huber_capped | 0.1206 | 0.2060 | 0.6447 | 0.3224 | -0.0054 | -0.0022 | -0.0032 |
| hcoef24_direct_huber_capped_strict_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.1210 | 0.2085 | 0.6164 | 0.3226 | -0.0049 | 0.0002 | -0.0315 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.1213 | 0.2095 | 0.6580 | 0.3221 | -0.0047 | 0.0013 | 0.0100 |
| hcoef24_direct_huber_capped_strict_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.1221 | 0.2088 | 0.6174 | 0.3230 | -0.0039 | 0.0006 | -0.0305 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p08_s0p5 | direct_huber_capped | 0.1228 | 0.2085 | 0.6524 | 0.3227 | -0.0032 | 0.0002 | 0.0044 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p08_s0p5 | direct_huber_capped | 0.1229 | 0.2084 | 0.6477 | 0.3225 | -0.0030 | 0.0002 | -0.0002 |
| hcoef24_loose_risk_basis_k16_cap0p05_s0p5 | basis_component | 0.1233 | 0.2082 | 0.6479 | 0.3256 | -0.0027 | -0.0000 | -0.0000 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.1236 | 0.2095 | 0.6538 | 0.3220 | -0.0024 | 0.0013 | 0.0059 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p05_s0p5 | direct_huber_capped | 0.1237 | 0.2083 | 0.6524 | 0.3232 | -0.0023 | 0.0001 | 0.0044 |
| hcoef24_loose_risk_basis_k8_cap0p08_s0p25 | basis_component | 0.1240 | 0.2082 | 0.6450 | 0.3255 | -0.0020 | -0.0000 | -0.0029 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p05_s0p5 | direct_huber_capped | 0.1243 | 0.2083 | 0.6477 | 0.3232 | -0.0017 | 0.0001 | -0.0002 |
| hcoef24_default_risk_basis_k8_cap0p05_s0p75 | basis_component | 0.1245 | 0.2082 | 0.6484 | 0.3249 | -0.0014 | -0.0000 | 0.0004 |
| hcoef24_loose_risk_basis_k16_cap0p08_s0p25 | basis_component | 0.1246 | 0.2083 | 0.6411 | 0.3254 | -0.0014 | 0.0001 | -0.0069 |

### Artist OOF

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.1185 | 0.2047 | 0.6409 | 0.3204 | -0.0075 | -0.0035 | -0.0071 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.1203 | 0.2051 | 0.6519 | 0.3204 | -0.0057 | -0.0031 | 0.0040 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.1218 | 0.2098 | 0.6516 | 0.3220 | -0.0042 | 0.0016 | 0.0037 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p5 | direct_huber_capped | 0.1229 | 0.2053 | 0.6491 | 0.3214 | -0.0030 | -0.0029 | 0.0011 |
| hcoef24_loose_risk_basis_k16_cap0p05_s0p5 | basis_component | 0.1233 | 0.2082 | 0.6479 | 0.3256 | -0.0027 | -0.0000 | -0.0000 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p5 | direct_huber_capped | 0.1234 | 0.2056 | 0.6472 | 0.3215 | -0.0026 | -0.0026 | -0.0008 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p75 | direct_huber_capped | 0.1235 | 0.2058 | 0.6497 | 0.3217 | -0.0025 | -0.0024 | 0.0018 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p08_s0p5 | direct_huber_capped | 0.1236 | 0.2087 | 0.6517 | 0.3226 | -0.0024 | 0.0005 | 0.0037 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p08_s0p5 | direct_huber_capped | 0.1236 | 0.2087 | 0.6491 | 0.3225 | -0.0024 | 0.0005 | 0.0011 |
| hcoef24_direct_huber_capped_strict_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.1237 | 0.2096 | 0.6326 | 0.3233 | -0.0023 | 0.0014 | -0.0153 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.1237 | 0.2099 | 0.6500 | 0.3219 | -0.0023 | 0.0017 | 0.0021 |
| hcoef24_loose_risk_basis_k8_cap0p08_s0p25 | basis_component | 0.1240 | 0.2082 | 0.6450 | 0.3255 | -0.0020 | -0.0000 | -0.0029 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p5 | direct_huber_capped | 0.1242 | 0.2064 | 0.6472 | 0.3226 | -0.0018 | -0.0018 | -0.0008 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p5 | direct_huber_capped | 0.1242 | 0.2062 | 0.6491 | 0.3226 | -0.0018 | -0.0020 | 0.0011 |
| hcoef24_default_risk_basis_k8_cap0p05_s0p75 | basis_component | 0.1245 | 0.2082 | 0.6484 | 0.3249 | -0.0014 | -0.0000 | 0.0004 |
| hcoef24_loose_risk_basis_k16_cap0p08_s0p25 | basis_component | 0.1246 | 0.2083 | 0.6411 | 0.3254 | -0.0014 | 0.0001 | -0.0069 |
| hcoef24_default_risk_basis_k8_cap0p05_s0p5 | basis_component | 0.1247 | 0.2080 | 0.6484 | 0.3249 | -0.0013 | -0.0002 | 0.0004 |
| hcoef24_loose_risk_basis_k16_cap0p03_s0p25 | basis_component | 0.1247 | 0.2080 | 0.6416 | 0.3252 | -0.0013 | -0.0002 | -0.0064 |
| hcoef24_loose_risk_basis_k16_cap0p05_s0p25 | basis_component | 0.1247 | 0.2081 | 0.6411 | 0.3253 | -0.0013 | -0.0001 | -0.0069 |
| hcoef24_default_risk_basis_k16_cap0p05_s0p5 | basis_component | 0.1247 | 0.2081 | 0.6482 | 0.3249 | -0.0013 | -0.0001 | 0.0003 |

## 4. Fixed Test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p5 | direct_huber_capped | 0.1358 | 0.2697 | 0.8315 | 0.3957 | -0.0030 | -0.0033 | 0.0252 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.1362 | 0.2687 | 0.8618 | 0.3948 | -0.0026 | -0.0043 | 0.0555 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p5 | direct_huber_capped | 0.1364 | 0.2698 | 0.8315 | 0.3958 | -0.0024 | -0.0031 | 0.0252 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p5 | direct_huber_capped | 0.1372 | 0.2705 | 0.8269 | 0.3965 | -0.0016 | -0.0024 | 0.0205 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p75 | direct_huber_capped | 0.1374 | 0.2695 | 0.8304 | 0.3955 | -0.0014 | -0.0035 | 0.0241 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p75 | direct_huber_capped | 0.1374 | 0.2698 | 0.8304 | 0.3957 | -0.0014 | -0.0032 | 0.0241 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.1380 | 0.2690 | 0.8605 | 0.3949 | -0.0008 | -0.0040 | 0.0541 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p5 | direct_huber_capped | 0.1380 | 0.2703 | 0.8269 | 0.3964 | -0.0008 | -0.0027 | 0.0205 |
| hcoef24_default_risk_basis_k8_cap0p05_s0p75 | basis_component | 0.1383 | 0.2729 | 0.8079 | 0.3993 | -0.0005 | -0.0001 | 0.0015 |
| hcoef24_loose_risk_basis_k8_cap0p05_s0p75 | basis_component | 0.1384 | 0.2717 | 0.8079 | 0.3987 | -0.0004 | -0.0013 | 0.0015 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.1385 | 0.2713 | 0.8382 | 0.3962 | -0.0003 | -0.0017 | 0.0318 |
| hcoef24_loose_risk_basis_k8_cap0p05_s0p5 | basis_component | 0.1388 | 0.2719 | 0.8063 | 0.3986 | 0.0000 | -0.0010 | -0.0001 |
| hcoef24_default_risk_basis_k8_cap0p05_s0p5 | basis_component | 0.1388 | 0.2727 | 0.8064 | 0.3990 | 0.0000 | -0.0003 | 0.0000 |
| hcoef_stable | source | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | 0.1388 | 0.2725 | 0.8071 | 0.3985 | 0.0000 | -0.0005 | 0.0008 |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | 0.1388 | 0.2725 | 0.8071 | 0.3985 | 0.0000 | -0.0005 | 0.0008 |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | 0.1388 | 0.2726 | 0.8071 | 0.3985 | 0.0000 | -0.0004 | 0.0008 |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | 0.1388 | 0.2726 | 0.8071 | 0.3985 | 0.0000 | -0.0004 | 0.0008 |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | 0.1388 | 0.2726 | 0.8071 | 0.3985 | 0.0000 | -0.0004 | 0.0008 |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | 0.1388 | 0.2726 | 0.8071 | 0.3985 | 0.0000 | -0.0004 | 0.0008 |
| hcoef24_default_risk_basis_k8_cap0p03_s0p75 | basis_component | 0.1389 | 0.2726 | 0.8064 | 0.3990 | 0.0001 | -0.0004 | 0.0000 |
| hcoef24_default_risk_basis_k16_cap0p05_s0p5 | basis_component | 0.1389 | 0.2730 | 0.8064 | 0.3990 | 0.0001 | -0.0000 | 0.0000 |
| hcoef24_default_risk_basis_k8_cap0p08_s0p5 | basis_component | 0.1389 | 0.2733 | 0.8100 | 0.3993 | 0.0001 | 0.0003 | 0.0037 |
| hcoef24_default_risk_basis_k8_cap0p08_s0p75 | basis_component | 0.1389 | 0.2741 | 0.8312 | 0.3999 | 0.0001 | 0.0012 | 0.0248 |

## 5. 0604 Stress Test 상위 후보

| candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppv8_service_proxy | source | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.2508 | 0.3550 | 0.9444 | 1.2962 | -0.0223 | -0.0193 | -0.0391 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.2526 | 0.3546 | 0.9449 | 1.2967 | -0.0205 | -0.0197 | -0.0386 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p08_s0p75 | direct_huber_capped | 0.2553 | 0.3602 | 0.9830 | 1.2944 | -0.0177 | -0.0142 | -0.0005 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p08_s0p75 | direct_huber_capped | 0.2573 | 0.3589 | 0.9789 | 1.2951 | -0.0157 | -0.0155 | -0.0046 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p5 | direct_huber_capped | 0.2589 | 0.3605 | 0.9543 | 1.3002 | -0.0141 | -0.0138 | -0.0292 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p5 | direct_huber_capped | 0.2589 | 0.3607 | 0.9543 | 1.2999 | -0.0141 | -0.0136 | -0.0292 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p08_s0p5 | direct_huber_capped | 0.2589 | 0.3636 | 0.9826 | 1.2992 | -0.0141 | -0.0108 | -0.0008 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p05_s0p75 | direct_huber_capped | 0.2590 | 0.3634 | 0.9793 | 1.2993 | -0.0140 | -0.0110 | -0.0042 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p75 | direct_huber_capped | 0.2611 | 0.3609 | 0.9573 | 1.3004 | -0.0120 | -0.0135 | -0.0262 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p75 | direct_huber_capped | 0.2611 | 0.3610 | 0.9573 | 1.3001 | -0.0120 | -0.0134 | -0.0262 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p05_s0p75 | direct_huber_capped | 0.2621 | 0.3641 | 0.9832 | 1.2989 | -0.0110 | -0.0102 | -0.0003 |
| hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p5 | direct_huber_capped | 0.2626 | 0.3651 | 0.9760 | 1.3025 | -0.0105 | -0.0092 | -0.0074 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p08_s0p5 | direct_huber_capped | 0.2629 | 0.3644 | 0.9831 | 1.2987 | -0.0102 | -0.0100 | -0.0003 |
| hcoef24_direct_huber_capped_default_a0p1_cap0p05_s0p5 | direct_huber_capped | 0.2629 | 0.3667 | 0.9827 | 1.3020 | -0.0101 | -0.0076 | -0.0007 |
| hcoef24_direct_huber_capped_default_a0p01_cap0p05_s0p5 | direct_huber_capped | 0.2635 | 0.3672 | 0.9833 | 1.3018 | -0.0096 | -0.0072 | -0.0002 |
| hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p5 | direct_huber_capped | 0.2636 | 0.3651 | 0.9760 | 1.3028 | -0.0095 | -0.0093 | -0.0074 |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p03_s0p5 | residual_huber | 0.2697 | 0.3722 | 0.9793 | 1.3060 | -0.0033 | -0.0021 | -0.0041 |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p5 | residual_huber | 0.2697 | 0.3728 | 0.9792 | 1.3066 | -0.0033 | -0.0015 | -0.0042 |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p03_s0p5 | residual_huber | 0.2697 | 0.3722 | 0.9793 | 1.3060 | -0.0033 | -0.0021 | -0.0041 |

## 6. 주요 계수 해석

- 계수는 표준화된 피처 기준이며 방향성과 상대 영향 비교용.
- `risk_shrunk_basis` 계열은 유사 작품 기준가를 그대로 쓰지 않고 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가.
- `quantile_width`, `pred_spread`, `hcoef23_risk_score`는 가격을 직접 결정하는 피처라기보다 기준가를 얼마나 믿을지 판단하는 위험 신호.

| candidate | method | feature | standardized_coefficient | raw_role | direction | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| current_70_30 | source | current_70_30 | 1.0000 | source_prediction | positive | 서비스 v0.1 70:30 기준 후보 |
| hcoef24_default_risk_basis_k8_cap0p03_s0p75 | basis_component | default_risk_shrunk_basis_k8_gap | 0.7500 | capped_basis_move | raises_or_lowers_with_basis | 위험도 완화 기준가와 안정 후보의 차이를 cap 안에서만 반영한다. |
| hcoef24_default_risk_basis_k8_cap0p05_s0p5 | basis_component | default_risk_shrunk_basis_k8_gap | 0.5000 | capped_basis_move | raises_or_lowers_with_basis | 위험도 완화 기준가와 안정 후보의 차이를 cap 안에서만 반영한다. |
| hcoef24_default_risk_basis_k8_cap0p05_s0p75 | basis_component | default_risk_shrunk_basis_k8_gap | 0.7500 | capped_basis_move | raises_or_lowers_with_basis | 위험도 완화 기준가와 안정 후보의 차이를 cap 안에서만 반영한다. |
| hcoef24_loose_risk_basis_k8_cap0p05_s0p5 | basis_component | loose_risk_shrunk_basis_k8_gap | 0.5000 | capped_basis_move | raises_or_lowers_with_basis | 위험도 완화 기준가와 안정 후보의 차이를 cap 안에서만 반영한다. |
| hcoef24_loose_risk_basis_k8_cap0p05_s0p75 | basis_component | loose_risk_shrunk_basis_k8_gap | 0.7500 | capped_basis_move | raises_or_lowers_with_basis | 위험도 완화 기준가와 안정 후보의 차이를 cap 안에서만 반영한다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | quantile_width | 0.0068 | residual_log | raises prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | svc_group_n_log | 0.0038 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | pred_spread | 0.0036 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | default_risk_shrunk_basis_k8_gap | -0.0027 | residual_log | lowers prediction | 유사 작품 기준가를 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0050 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0075 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | coverage_numeric | -0.0078 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | hcoef23_risk_score | -0.0290 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0327 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | quantile_width | 0.0068 | residual_log | raises prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | svc_group_n_log | 0.0038 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | pred_spread | 0.0036 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | default_risk_shrunk_basis_k8_gap | -0.0027 | residual_log | lowers prediction | 유사 작품 기준가를 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0050 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0075 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | coverage_numeric | -0.0078 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | hcoef23_risk_score | -0.0290 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0327 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | quantile_width | 0.0067 | residual_log | raises prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | svc_group_n_log | 0.0038 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | pred_spread | 0.0038 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | loose_risk_shrunk_basis_k8_gap | -0.0033 | residual_log | lowers prediction | 유사 작품 기준가를 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0050 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0075 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | coverage_numeric | -0.0078 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | hcoef23_risk_score | -0.0290 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0326 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | quantile_width | 0.0067 | residual_log | raises prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | svc_group_n_log | 0.0038 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | pred_spread | 0.0038 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | loose_risk_shrunk_basis_k8_gap | -0.0033 | residual_log | lowers prediction | 유사 작품 기준가를 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0050 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0075 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | coverage_numeric | -0.0078 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | hcoef23_risk_score | -0.0290 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0326 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | quantile_width | 0.0065 | residual_log | raises prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | pred_spread | 0.0032 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | svc_group_n_log | 0.0031 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0048 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | strict_risk_shrunk_basis_k8_gap | -0.0057 | residual_log | lowers prediction | 유사 작품 기준가를 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | coverage_numeric | -0.0069 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0076 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | hcoef23_risk_score | -0.0288 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0324 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | quantile_width | 0.0065 | residual_log | raises prediction | 퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | pred_spread | 0.0032 | residual_log | raises prediction | 여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | svc_group_n_log | 0.0031 | residual_log | raises prediction | 유사 작품 표본 수를 로그 변환한 신뢰도 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | ppv8_minus_stable | -0.0048 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | strict_risk_shrunk_basis_k8_gap | -0.0057 | residual_log | lowers prediction | 유사 작품 기준가를 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | coverage_numeric | -0.0069 | residual_log | lowers prediction | 유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | svc_minus_stable | -0.0076 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | hcoef23_risk_score | -0.0288 | residual_log | lowers prediction | HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다. |
| hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | residual_huber | current_minus_stable | -0.0324 | residual_log | lowers prediction | 저차원 Huber 보정에 사용하는 보조 피처다. |
| hcoef_stable | source | hcoef_stable | 1.0000 | source_prediction | positive | 현재 HCOEF 안정 후보 |
| l10_seq_full_generated_bucket | source | l10_seq_pred_log | 1.0000 | source_prediction | positive | PP-L10 순차 component |
| ppv8_service_proxy | source | ppv8_service_proxy | 1.0000 | source_prediction | positive | PP-V8/service component proxy |
| svc_numeric_seed_mean | source | svc_numeric_seed_mean | 1.0000 | source_prediction | positive | 유사 작품 기반 가격 피처 |

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
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p03_s0p75 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5044 | 0.9999 | 0.2799 | 0.6044 | 0.0006 | 0.4478 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p05_s0p5 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5043 | 0.9999 | 0.2799 | 0.6045 | 0.0006 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p05_s0p75 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5041 | 0.9999 | 0.2799 | 0.6046 | 0.0008 | 0.4478 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5036 | 0.9999 | 0.2799 | 0.6046 | 0.0037 | 0.4353 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5036 | 0.9999 | 0.2799 | 0.6046 | 0.0037 | 0.4353 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5036 | 0.9999 | 0.2799 | 0.6045 | 0.0037 | 0.4353 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5036 | 0.9999 | 0.2799 | 0.6045 | 0.0037 | 0.4353 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5036 | 0.9999 | 0.2799 | 0.6047 | 0.0036 | 0.4353 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_020_plus | 402 | 0.4337 | 0.5036 | 0.9999 | 0.2799 | 0.6047 | 0.0036 | 0.4353 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_loose_risk_basis_k8_cap0p05_s0p5 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5029 | 0.9999 | 0.2799 | 0.6058 | 0.0021 | 0.4353 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef24_loose_risk_basis_k8_cap0p05_s0p75 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5020 | 0.9999 | 0.2781 | 0.6066 | 0.0032 | 0.4428 | 0.0423 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_010_020 | 128 | 0.3203 | 0.4882 | 2.1936 | -0.0384 | 0.0639 | 0.3592 | 0.3359 | 0.0703 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_020_plus | 402 | 0.3131 | 0.4234 | 1.1510 | 0.1623 | 0.2613 | 0.6194 | 0.2910 | 0.0622 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_010_020 | 128 | 0.2777 | 0.3693 | 0.9720 | -0.0734 | 0.0324 | 0.0620 | 0.2891 | 0.0469 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | -0.0556 | 0.0461 | 0.0217 | 0.3125 | 0.0391 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0399 | 0.0000 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2199 | 0.3390 | 0.8757 | -0.0415 | 0.0389 | 0.0046 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2199 | 0.3390 | 0.8757 | -0.0415 | 0.0389 | 0.0046 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2199 | 0.3390 | 0.8757 | -0.0415 | 0.0390 | 0.0046 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2199 | 0.3390 | 0.8757 | -0.0415 | 0.0390 | 0.0046 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p05_s0p5 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3390 | 0.8716 | -0.0465 | 0.0404 | 0.0014 | 0.3203 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p03_s0p75 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3390 | 0.8728 | -0.0465 | 0.0404 | 0.0013 | 0.3125 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2198 | 0.3389 | 0.8757 | -0.0415 | 0.0390 | 0.0045 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_010_020 | 128 | 0.2198 | 0.3389 | 0.8757 | -0.0415 | 0.0390 | 0.0045 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p05_s0p75 | gap_band | gap_010_020 | 128 | 0.2279 | 0.3388 | 0.8564 | -0.0465 | 0.0407 | 0.0022 | 0.3203 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_loose_risk_basis_k8_cap0p05_s0p5 | gap_band | gap_010_020 | 128 | 0.2255 | 0.3386 | 0.8716 | -0.0465 | 0.0411 | 0.0020 | 0.3203 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef24_loose_risk_basis_k8_cap0p05_s0p75 | gap_band | gap_010_020 | 128 | 0.2279 | 0.3383 | 0.8564 | -0.0465 | 0.0417 | 0.0031 | 0.3203 | 0.0234 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_010_020 | 128 | 0.2540 | 0.3269 | 0.7844 | 0.0520 | 0.0782 | 0.1447 | 0.2656 | 0.0156 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_005_010 | 125 | 0.1883 | 0.3007 | 0.9169 | 0.0567 | 0.0972 | 0.1938 | 0.1680 | 0.0400 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_005_010 | 125 | 0.1764 | 0.2618 | 0.7685 | 0.0806 | 0.0930 | 0.0754 | 0.0880 | 0.0240 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_005_010 | 125 | 0.1613 | 0.2612 | 0.9572 | 0.0380 | 0.0895 | 0.0361 | 0.0960 | 0.0480 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.0641 | 0.0905 | 0.0190 | 0.0880 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef24_loose_risk_basis_k8_cap0p05_s0p75 | gap_band | gap_005_010 | 125 | 0.1502 | 0.2530 | 0.9526 | 0.0392 | 0.0858 | 0.0107 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p05_s0p75 | gap_band | gap_005_010 | 125 | 0.1557 | 0.2526 | 0.9526 | 0.0392 | 0.0856 | 0.0076 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_loose_risk_basis_k8_cap0p05_s0p5 | gap_band | gap_005_010 | 125 | 0.1468 | 0.2525 | 0.9526 | 0.0364 | 0.0863 | 0.0072 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p05_s0p5 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2522 | 0.9526 | 0.0364 | 0.0862 | 0.0050 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_default_risk_basis_k8_cap0p03_s0p75 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2519 | 0.9526 | 0.0392 | 0.0862 | 0.0049 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0872 | 0.0000 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2505 | 0.9464 | 0.0353 | 0.0866 | 0.0042 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2505 | 0.9464 | 0.0353 | 0.0866 | 0.0042 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2505 | 0.9464 | 0.0353 | 0.0865 | 0.0043 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2505 | 0.9464 | 0.0353 | 0.0865 | 0.0043 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2505 | 0.9464 | 0.0353 | 0.0865 | 0.0043 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_005_010 | 125 | 0.1494 | 0.2505 | 0.9464 | 0.0353 | 0.0865 | 0.0043 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_000_003 | 119 | 0.1387 | 0.2330 | 0.7125 | -0.0071 | 0.0833 | 0.1325 | 0.0924 | 0.0084 |
| 0604_stress | 0604_ex50 | l10_seq_full_generated_bucket | gap_band | gap_003_005 | 55 | 0.1531 | 0.2296 | 0.5665 | -0.0167 | 0.1022 | 0.2173 | 0.1636 | 0.0182 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_000_003 | 119 | 0.1025 | 0.1967 | 0.5508 | 0.0404 | 0.0785 | 0.0222 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.0401 | 0.0761 | 0.0164 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_000_003 | 119 | 0.1162 | 0.1942 | 0.5405 | 0.0395 | 0.0705 | 0.0125 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | ppv8_service_proxy | gap_band | gap_003_005 | 55 | 0.1039 | 0.1925 | 0.4983 | 0.0427 | 0.0915 | 0.0397 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | svc_numeric_seed_mean | gap_band | gap_003_005 | 55 | 0.1117 | 0.1922 | 0.5421 | 0.0171 | 0.0778 | 0.0356 | 0.0727 | 0.0000 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.0305 | 0.0819 | 0.0227 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_000_003 | 119 | 0.1053 | 0.1886 | 0.5300 | 0.0272 | 0.0704 | 0.0000 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.1012 | 0.1886 | 0.5276 | 0.0265 | 0.0690 | 0.0039 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.1012 | 0.1886 | 0.5276 | 0.0265 | 0.0690 | 0.0039 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p25 | gap_band | gap_000_003 | 119 | 0.1012 | 0.1886 | 0.5276 | 0.0267 | 0.0689 | 0.0038 | 0.0756 | 0.0084 |

## 9. Bootstrap 요약

| source_scope | validation_scheme | candidate | method | n_bootstrap | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | mean_delta_RMSE_log_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | any2_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_row | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p75 | direct_huber_capped | 300 | -0.0104 | -0.0037 | -0.0032 | -0.0049 | 0.9767 | 0.9800 | 0.5833 | 0.5567 | 0.9833 |
| validation_oof_row | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p75 | direct_huber_capped | 300 | -0.0105 | -0.0036 | -0.0024 | -0.0050 | 0.9700 | 0.9633 | 0.5767 | 0.5467 | 0.9667 |
| validation_oof_row | artist_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p75 | direct_huber_capped | 300 | -0.0108 | -0.0037 | -0.0024 | -0.0048 | 0.9867 | 0.9467 | 0.5500 | 0.5233 | 0.9633 |
| validation_oof_row | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p5 | direct_huber_capped | 300 | -0.0066 | -0.0031 | -0.0029 | -0.0038 | 0.9433 | 0.9933 | 0.5267 | 0.5067 | 0.9600 |
| validation_oof_row | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p5 | direct_huber_capped | 300 | -0.0068 | -0.0030 | -0.0024 | -0.0039 | 0.9333 | 0.9933 | 0.5367 | 0.5067 | 0.9567 |
| validation_oof_row | artist_bootstrap | hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p75 | direct_huber_capped | 300 | -0.0111 | -0.0036 | -0.0016 | -0.0049 | 0.9733 | 0.9400 | 0.5367 | 0.5000 | 0.9533 |
| validation_oof_row | artist_bootstrap | hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p5 | direct_huber_capped | 300 | -0.0076 | -0.0030 | -0.0017 | -0.0038 | 0.9667 | 0.9800 | 0.5200 | 0.4933 | 0.9767 |
| validation_oof_row | artist_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p5 | direct_huber_capped | 300 | -0.0074 | -0.0031 | -0.0023 | -0.0037 | 0.9667 | 0.9800 | 0.5233 | 0.4900 | 0.9800 |
| validation_oof_artist | artist_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p75 | direct_huber_capped | 300 | -0.0082 | -0.0035 | -0.0001 | -0.0048 | 0.9533 | 0.9433 | 0.5233 | 0.4900 | 0.9333 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0028 | -0.0008 | 0.6567 | 0.9667 | 0.7333 | 0.4833 | 0.8767 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0028 | -0.0008 | 0.6567 | 0.9667 | 0.7333 | 0.4833 | 0.8767 |
| validation_oof_artist | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p75 | direct_huber_capped | 300 | -0.0083 | -0.0035 | -0.0007 | -0.0048 | 0.9467 | 0.9767 | 0.5200 | 0.4767 | 0.9667 |
| validation_oof_row | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p5 | direct_huber_capped | 300 | -0.0048 | -0.0021 | -0.0010 | -0.0028 | 0.8933 | 0.9900 | 0.5200 | 0.4733 | 0.9300 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0025 | -0.0008 | 0.6300 | 0.9567 | 0.7333 | 0.4700 | 0.8600 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0008 | -0.0006 | -0.0025 | -0.0008 | 0.6300 | 0.9567 | 0.7333 | 0.4700 | 0.8600 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0007 | -0.0006 | -0.0026 | -0.0008 | 0.6300 | 0.9600 | 0.7300 | 0.4667 | 0.8600 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0007 | -0.0006 | -0.0026 | -0.0008 | 0.6300 | 0.9600 | 0.7300 | 0.4667 | 0.8600 |
| validation_oof_artist | artist_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p5 | direct_huber_capped | 300 | -0.0054 | -0.0029 | -0.0006 | -0.0038 | 0.9100 | 0.9833 | 0.5100 | 0.4633 | 0.9400 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_default_risk_basis_core_a0p001_cap0p02_s0p5 | residual_huber | 300 | -0.0012 | -0.0008 | -0.0040 | -0.0009 | 0.6567 | 0.9500 | 0.6933 | 0.4633 | 0.8500 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_default_risk_basis_core_a0p01_cap0p02_s0p5 | residual_huber | 300 | -0.0012 | -0.0008 | -0.0040 | -0.0009 | 0.6567 | 0.9500 | 0.6933 | 0.4633 | 0.8500 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p5 | residual_huber | 300 | -0.0012 | -0.0007 | -0.0043 | -0.0009 | 0.6567 | 0.9467 | 0.7067 | 0.4600 | 0.8600 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p5 | residual_huber | 300 | -0.0012 | -0.0007 | -0.0043 | -0.0009 | 0.6567 | 0.9467 | 0.7067 | 0.4600 | 0.8600 |
| validation_oof_row | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p5 | direct_huber_capped | 300 | -0.0047 | -0.0022 | -0.0010 | -0.0027 | 0.8900 | 0.9900 | 0.5033 | 0.4567 | 0.9267 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p5 | residual_huber | 300 | -0.0013 | -0.0008 | -0.0040 | -0.0009 | 0.6600 | 0.9500 | 0.6900 | 0.4567 | 0.8533 |
| validation_oof_row | row_bootstrap | hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p5 | residual_huber | 300 | -0.0013 | -0.0008 | -0.0040 | -0.0009 | 0.6600 | 0.9500 | 0.6900 | 0.4567 | 0.8533 |
| validation_oof_artist | artist_bootstrap | hcoef24_direct_huber_capped_loose_a0p01_cap0p08_s0p5 | direct_huber_capped | 300 | -0.0047 | -0.0026 | 0.0003 | -0.0037 | 0.8233 | 0.9600 | 0.5367 | 0.4533 | 0.8700 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p03_s0p25 | residual_huber | 300 | -0.0011 | -0.0006 | -0.0020 | -0.0008 | 0.6933 | 0.9567 | 0.6633 | 0.4467 | 0.8767 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p03_s0p25 | residual_huber | 300 | -0.0011 | -0.0006 | -0.0020 | -0.0008 | 0.6933 | 0.9567 | 0.6633 | 0.4467 | 0.8767 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p03_s0p5 | residual_huber | 300 | -0.0021 | -0.0011 | -0.0041 | -0.0015 | 0.7100 | 0.9300 | 0.6633 | 0.4467 | 0.8700 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p03_s0p5 | residual_huber | 300 | -0.0021 | -0.0011 | -0.0041 | -0.0015 | 0.7100 | 0.9300 | 0.6633 | 0.4467 | 0.8700 |
| validation_oof_artist | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p08_s0p5 | direct_huber_capped | 300 | -0.0054 | -0.0029 | -0.0014 | -0.0037 | 0.8933 | 0.9967 | 0.5033 | 0.4433 | 0.9500 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p02_s0p5 | residual_huber | 300 | -0.0016 | -0.0008 | -0.0030 | -0.0010 | 0.7033 | 0.9400 | 0.6733 | 0.4400 | 0.8833 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p02_s0p5 | residual_huber | 300 | -0.0016 | -0.0008 | -0.0030 | -0.0010 | 0.7033 | 0.9400 | 0.6733 | 0.4400 | 0.8833 |
| validation_oof_row | row_bootstrap | hcoef24_direct_huber_capped_strict_a0p01_cap0p08_s0p5 | direct_huber_capped | 300 | -0.0034 | -0.0006 | -0.0090 | -0.0022 | 0.7733 | 0.6833 | 0.7667 | 0.4400 | 0.8167 |
| validation_oof_row | artist_bootstrap | hcoef24_direct_huber_capped_loose_a0p01_cap0p05_s0p5 | direct_huber_capped | 300 | -0.0055 | -0.0021 | -0.0003 | -0.0027 | 0.9267 | 0.9767 | 0.4867 | 0.4367 | 0.9533 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_loose_risk_basis_core_a0p001_cap0p02_s0p5 | residual_huber | 300 | -0.0016 | -0.0008 | -0.0026 | -0.0009 | 0.7000 | 0.9467 | 0.6667 | 0.4367 | 0.8867 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_loose_risk_basis_core_a0p01_cap0p02_s0p5 | residual_huber | 300 | -0.0016 | -0.0008 | -0.0026 | -0.0009 | 0.7000 | 0.9467 | 0.6667 | 0.4367 | 0.8867 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p001_cap0p05_s0p5 | residual_huber | 300 | -0.0028 | -0.0013 | -0.0053 | -0.0020 | 0.7433 | 0.8800 | 0.6533 | 0.4367 | 0.8600 |
| validation_oof_row | artist_bootstrap | hcoef24_resid_huber_strict_risk_basis_core_a0p01_cap0p05_s0p5 | residual_huber | 300 | -0.0028 | -0.0013 | -0.0053 | -0.0020 | 0.7433 | 0.8800 | 0.6533 | 0.4367 | 0.8600 |
| validation_oof_row | row_bootstrap | hcoef24_direct_huber_capped_loose_a0p1_cap0p05_s0p75 | direct_huber_capped | 300 | -0.0068 | -0.0027 | 0.0001 | -0.0037 | 0.9200 | 0.9800 | 0.4667 | 0.4333 | 0.9333 |

## 10. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/coverage_summary.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`