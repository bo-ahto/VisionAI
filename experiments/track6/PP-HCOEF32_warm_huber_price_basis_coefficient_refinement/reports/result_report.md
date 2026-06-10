# PP-HCOEF32 Warm Huber ultra-micro p95-first directional correction

- 작성일: 2026-06-08 07:19
- 목적: HCOEF31의 fixed p95 근소 악화를 줄이기 위해 더 작은 weight/cap과 p95-first segment를 검증.
- 후보 선택: validation row/artist OOF segment consensus + residual direction consensus + p95 guard 후보를 사용.
- fixed test와 0604는 확인용으로만 사용.

## 1. 실행 결론

- 상위 확인 후보: `hcoef32_s03_all3_dir_top2_w0p025_cap0p001` (판단: fixed 확인 후보, fixed `0.1388/0.2729/0.8062`, repeated min any2/all3 `0.8280/0.3060`).
- 현재 안정 기준 `hcoef_stable` fixed test: `0.1388/0.2730/0.8064`.
- p95를 지키는 초미세 이동만 허용했으므로, 개선폭이 작으면 운영 후보가 아니라 p95-neutral 참고 후보로만 분리.

## 2. 보정 공식

- 방향 확인: segment의 `actual_log - hcoef_stable` 중앙값과 `source - hcoef_stable` 중앙값의 부호가 row/artist OOF 양쪽에서 일치하는지 확인.
- 적용식: `corrected_log = hcoef_stable + clip(weight * (source_candidate - hcoef_stable), -cap, cap)`.
- p95-first 후보는 row/artist OOF segment 양쪽에서 p95가 기준보다 나빠지지 않는 rule만 사용.
- 조건을 만족하지 않으면 `hcoef_stable`을 그대로 유지.

## 3. 사용한 source 후보

| source_candidate | source_tag | source_reason |
| --- | --- | --- |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | HCOEF29 repeated any2 0.928, all3 0.548; fixed 0.1442/0.2718/0.8081 |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | HCOEF29 repeated any2 0.926, all3 0.544; fixed 0.1442/0.2719/0.8081 |
| hcoef29_core_component_delta_s0p5_cap0p08 | s03 | HCOEF29 repeated any2 0.912, all3 0.552; fixed 0.1453/0.2731/0.8288 |

## 4. 방향 일치 segment rule

| source_candidate | group_name | rule_key | min_n | directional_score | stable_residual_median_row | source_move_median_row | stable_residual_median_artist | source_move_median_artist | median_abs_residual_delta_row | median_abs_residual_delta_artist | all3_safe | any2_safe | mape_guarded |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_10_19 | 33 | -0.2484 | -0.1515 | -0.0261 | -0.1515 | -0.0211 | 0.0194 | 0.0086 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_000_003 | 62 | -0.2180 | 0.0136 | 0.0027 | 0.0136 | 0.0000 | -0.0040 | 0.0010 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_gap | svc_group_level=artist & gap_band=gap_000_003 | 62 | -0.2173 | 0.0136 | 0.0027 | 0.0136 | 0.0000 | -0.0040 | 0.0010 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_10_19 | 33 | -0.2169 | -0.1515 | -0.0261 | -0.1515 | -0.0211 | 0.0194 | 0.0086 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_high | 37 | -0.2008 | 0.0121 | 0.0033 | 0.0121 | -0.0038 | -0.0266 | -0.0291 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_extreme | 54 | -0.1885 | -0.0168 | -0.0044 | -0.0168 | -0.0090 | 0.0132 | 0.0086 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_high | 37 | -0.1846 | 0.0121 | 0.0033 | 0.0121 | -0.0038 | -0.0273 | -0.0273 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_gap | svc_group_level=artist & gap_band=gap_003_005 | 26 | -0.1781 | -0.0555 | 0.0135 | -0.0555 | 0.0119 | -0.0063 | -0.0060 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_003_005 | 26 | -0.1781 | -0.0555 | 0.0135 | -0.0555 | 0.0119 | -0.0063 | -0.0060 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | n | svc_group_n_band=n_10_19 | 160 | -0.1764 | -0.0254 | -0.0073 | -0.0254 | -0.0084 | 0.0018 | 0.0010 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | n | svc_group_n_band=n_10_19 | 160 | -0.1756 | -0.0254 | -0.0073 | -0.0254 | -0.0084 | 0.0018 | 0.0010 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_extreme | 54 | -0.1738 | -0.0168 | -0.0044 | -0.0168 | -0.0090 | 0.0132 | 0.0086 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_003_005 | 26 | -0.1588 | -0.0555 | 0.0081 | -0.0555 | 0.0082 | -0.0206 | -0.0189 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth | qwidth_band=qwidth_extreme | 104 | -0.1369 | 0.0201 | -0.0062 | 0.0201 | -0.0089 | 0.0086 | 0.0055 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth | qwidth_band=qwidth_extreme | 104 | -0.1363 | 0.0201 | -0.0062 | 0.0201 | -0.0089 | 0.0086 | 0.0055 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_extreme | 54 | -0.1054 | -0.0168 | 0.0094 | -0.0168 | 0.0091 | -0.0015 | -0.0059 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_10_19 | 33 | -0.0950 | -0.1515 | -0.0050 | -0.1515 | -0.0055 | 0.0062 | -0.0019 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_high | 37 | -0.0932 | 0.0121 | -0.0012 | 0.0121 | -0.0034 | -0.0183 | -0.0168 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_000_003 | 62 | -0.0890 | 0.0136 | -0.0010 | 0.0136 | -0.0015 | -0.0117 | -0.0069 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_020_plus | 54 | -0.0728 | -0.0404 | -0.0093 | -0.0404 | -0.0219 | -0.0070 | -0.0195 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_010_020 | 29 | -0.0696 | 0.0277 | -0.0011 | 0.0277 | 0.0021 | -0.0173 | -0.0041 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_010_020 | 29 | -0.0696 | 0.0277 | -0.0011 | 0.0277 | 0.0021 | -0.0173 | -0.0041 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_020_plus | 54 | -0.0650 | -0.0404 | -0.0093 | -0.0404 | -0.0219 | -0.0049 | -0.0149 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_n | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | 87 | -0.0645 | 0.0144 | 0.0179 | 0.0144 | 0.0166 | -0.0107 | -0.0129 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | 87 | -0.0645 | 0.0144 | 0.0179 | 0.0144 | 0.0166 | -0.0107 | -0.0129 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_010_020 | 36 | -0.0623 | -0.0491 | -0.0088 | -0.0491 | -0.0089 | -0.0127 | -0.0200 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_mid | 87 | -0.0622 | -0.0343 | -0.0026 | -0.0343 | -0.0003 | 0.0049 | -0.0018 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_010_020 | 36 | -0.0619 | -0.0491 | -0.0088 | -0.0491 | -0.0089 | -0.0127 | -0.0200 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level | svc_group_level=artist | 252 | -0.0603 | 0.0111 | 0.0003 | 0.0111 | -0.0015 | -0.0057 | -0.0036 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level | svc_group_level=artist | 252 | -0.0595 | 0.0111 | 0.0003 | 0.0111 | -0.0015 | -0.0057 | -0.0036 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_gap | svc_group_level=artist & gap_band=gap_010_020 | 75 | -0.0523 | 0.0485 | -0.0012 | 0.0485 | -0.0026 | -0.0130 | -0.0085 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_010_020 | 75 | -0.0521 | 0.0485 | -0.0012 | 0.0485 | -0.0026 | -0.0130 | -0.0085 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 66 | -0.0511 | 0.0616 | -0.0034 | 0.0616 | -0.0039 | -0.0095 | 0.0033 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 66 | -0.0511 | 0.0616 | -0.0034 | 0.0616 | -0.0039 | -0.0095 | 0.0033 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_low | 74 | -0.0507 | 0.0504 | 0.0027 | 0.0504 | -0.0005 | -0.0086 | -0.0067 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_low | 74 | -0.0506 | 0.0504 | 0.0027 | 0.0504 | -0.0005 | -0.0086 | -0.0067 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level | svc_group_level=artist | 252 | -0.0500 | 0.0111 | 0.0006 | 0.0111 | 0.0022 | -0.0032 | -0.0063 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_005_010 | 40 | -0.0471 | 0.0461 | 0.0086 | 0.0461 | 0.0125 | -0.0019 | -0.0126 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist_medium_support_size & qwidth_band=qwidth_high | 27 | -0.0469 | -0.0363 | 0.0075 | -0.0363 | 0.0037 | -0.0143 | -0.0060 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_005_010 | 40 | -0.0459 | 0.0461 | 0.0076 | 0.0461 | 0.0043 | -0.0091 | -0.0114 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_005_010 | 40 | -0.0459 | 0.0461 | 0.0076 | 0.0461 | 0.0043 | -0.0091 | -0.0114 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread_gap | pred_spread_band=spread_high & gap_band=gap_010_020 | 34 | -0.0456 | 0.0789 | 0.0026 | 0.0789 | 0.0041 | -0.0143 | -0.0041 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_high & gap_band=gap_010_020 | 34 | -0.0445 | 0.0789 | 0.0026 | 0.0789 | 0.0041 | -0.0143 | -0.0041 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth | qwidth_band=qwidth_high | 73 | -0.0427 | -0.0307 | 0.0101 | -0.0307 | 0.0082 | 0.0033 | 0.0035 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 37 | -0.0425 | 0.0819 | 0.0062 | 0.0819 | 0.0030 | -0.0070 | -0.0120 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth | qwidth_band=qwidth_high | 73 | -0.0421 | -0.0307 | 0.0101 | -0.0307 | 0.0082 | 0.0033 | 0.0035 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_low | 74 | -0.0412 | 0.0504 | 0.0026 | 0.0504 | 0.0082 | -0.0096 | -0.0062 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | gap | gap_band=gap_020_plus | 76 | -0.0388 | -0.0467 | -0.0084 | -0.0467 | -0.0149 | -0.0065 | -0.0125 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth | qwidth_band=qwidth_low | 171 | -0.0380 | 0.0050 | 0.0043 | 0.0050 | 0.0075 | -0.0095 | -0.0099 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth | qwidth_band=qwidth_low | 171 | -0.0380 | 0.0050 | 0.0043 | 0.0050 | 0.0075 | -0.0095 | -0.0099 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | n | svc_group_n_band=n_10_19 | 160 | -0.0374 | -0.0254 | 0.0034 | -0.0254 | 0.0027 | 0.0019 | 0.0059 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | spread | pred_spread_band=spread_high | 73 | -0.0372 | 0.0129 | -0.0022 | 0.0129 | -0.0019 | -0.0056 | 0.0035 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_low & svc_group_n_band=n_10_19 | 50 | -0.0356 | 0.0152 | -0.0039 | 0.0152 | -0.0026 | -0.0000 | -0.0035 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_n | qwidth_band=qwidth_low & svc_group_n_band=n_10_19 | 50 | -0.0355 | 0.0152 | -0.0039 | 0.0152 | -0.0026 | -0.0000 | -0.0035 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread | pred_spread_band=spread_high | 73 | -0.0354 | 0.0129 | 0.0005 | 0.0129 | -0.0006 | -0.0019 | 0.0019 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | 87 | -0.0353 | 0.0144 | 0.0147 | 0.0144 | 0.0149 | -0.0050 | -0.0047 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread | pred_spread_band=spread_high | 73 | -0.0349 | 0.0129 | 0.0005 | 0.0129 | -0.0006 | -0.0019 | 0.0019 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_low_mid & gap_band=gap_003_005 | 53 | -0.0346 | -0.0302 | 0.0114 | -0.0302 | 0.0100 | -0.0043 | -0.0040 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 66 | -0.0319 | 0.0616 | 0.0075 | 0.0616 | 0.0111 | -0.0011 | -0.0011 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth | qwidth_band=qwidth_extreme | 104 | -0.0313 | 0.0201 | 0.0043 | 0.0201 | 0.0033 | 0.0039 | -0.0003 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread_gap | pred_spread_band=spread_low_mid & gap_band=gap_003_005 | 53 | -0.0294 | -0.0302 | 0.0145 | -0.0302 | 0.0127 | -0.0061 | 0.0020 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_low_mid & gap_band=gap_003_005 | 53 | -0.0294 | -0.0302 | 0.0145 | -0.0302 | 0.0127 | -0.0061 | 0.0020 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_010_020 | 29 | -0.0257 | 0.0277 | 0.0007 | 0.0277 | 0.0041 | -0.0063 | -0.0139 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | gap | gap_band=gap_020_plus | 76 | -0.0244 | -0.0467 | -0.0084 | -0.0467 | -0.0149 | 0.0034 | -0.0177 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | confidence | service_confidence_tier=__MISSING__ | 458 | -0.0244 | -0.0012 | 0.0034 | -0.0012 | 0.0043 | -0.0038 | -0.0062 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | confidence | service_confidence_tier=__MISSING__ | 458 | -0.0242 | -0.0012 | 0.0034 | -0.0012 | 0.0043 | -0.0038 | -0.0062 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | confidence | service_confidence_tier=__MISSING__ | 458 | -0.0242 | -0.0012 | 0.0039 | -0.0012 | 0.0041 | -0.0038 | -0.0022 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | n | svc_group_n_band=n_5_9 | 300 | -0.0234 | 0.0147 | 0.0058 | 0.0147 | 0.0072 | -0.0045 | -0.0050 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 37 | -0.0208 | 0.0819 | -0.0019 | 0.0819 | -0.0085 | 0.0042 | 0.0013 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | gap | gap_band=gap_020_plus | 76 | -0.0206 | -0.0467 | -0.0011 | -0.0467 | 0.0023 | -0.0078 | -0.0118 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_010_020 | 75 | -0.0205 | 0.0485 | -0.0009 | 0.0485 | 0.0014 | -0.0089 | -0.0131 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_gap | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 37 | -0.0205 | 0.0819 | -0.0019 | 0.0819 | -0.0085 | 0.0042 | 0.0013 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_010_020 | 36 | -0.0198 | -0.0491 | -0.0065 | -0.0491 | 0.0024 | -0.0004 | -0.0073 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_mid | 87 | -0.0182 | -0.0343 | 0.0020 | -0.0343 | 0.0054 | 0.0112 | 0.0013 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_mid | 87 | -0.0181 | -0.0343 | 0.0020 | -0.0343 | 0.0054 | 0.0112 | 0.0013 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_mid & gap_band=gap_020_plus | 28 | -0.0146 | 0.0994 | -0.0042 | 0.0994 | -0.0114 | 0.0027 | -0.0026 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_high & gap_band=gap_010_020 | 34 | -0.0118 | 0.0789 | 0.0004 | 0.0789 | -0.0003 | -0.0085 | -0.0030 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread | pred_spread_band=spread_extreme | 104 | -0.0107 | -0.0309 | -0.0093 | -0.0309 | -0.0153 | 0.0005 | -0.0023 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread | pred_spread_band=spread_extreme | 104 | -0.0106 | -0.0309 | -0.0093 | -0.0309 | -0.0153 | 0.0005 | -0.0023 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | gap | gap_band=gap_003_005 | 55 | -0.0103 | -0.0302 | 0.0145 | -0.0302 | 0.0127 | -0.0015 | 0.0035 | False | False | False |

## 5. 정책 후보 설정

| candidate | source_candidate | source_tag | objective | top_n | weight | cap | rule_count | rules | mean_directional_score | min_n | formula |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 1 | 0.0250 | 0.0010 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 1 | 0.0250 | 0.0025 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 1 | 0.0250 | 0.0050 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 1 | 0.0500 | 0.0010 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 1 | 0.0500 | 0.0025 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 1 | 0.0500 | 0.0050 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 2 | 0.0250 | 0.0010 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 2 | 0.0250 | 0.0025 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 2 | 0.0250 | 0.0050 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 2 | 0.0500 | 0.0010 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 2 | 0.0500 | 0.0025 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | p95_dir | 2 | 0.0500 | 0.0050 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 1 | 0.0250 | 0.0010 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 1 | 0.0250 | 0.0025 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 1 | 0.0250 | 0.0050 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 1 | 0.0500 | 0.0010 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 1 | 0.0500 | 0.0025 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 1 | 0.0500 | 0.0050 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 2 | 0.0250 | 0.0010 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 66 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 2 | 0.0250 | 0.0025 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 66 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 2 | 0.0250 | 0.0050 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 66 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 2 | 0.0500 | 0.0010 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 66 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 2 | 0.0500 | 0.0025 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 66 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | all3_dir | 2 | 0.0500 | 0.0050 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 66 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 1 | 0.0250 | 0.0010 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 1 | 0.0250 | 0.0025 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 1 | 0.0250 | 0.0050 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 1 | 0.0500 | 0.0010 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 1 | 0.0500 | 0.0025 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 1 | 0.0500 | 0.0050 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 2 | 0.0250 | 0.0010 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 2 | 0.0250 | 0.0025 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top2_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 2 | 0.0250 | 0.0050 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top2_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 2 | 0.0500 | 0.0010 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 2 | 0.0500 | 0.0025 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_any2_dir_top2_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | any2_dir | 2 | 0.0500 | 0.0050 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 | -0.0485 | 40 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top1_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 1 | 0.0250 | 0.0010 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top1_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 1 | 0.0250 | 0.0025 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top1_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 1 | 0.0250 | 0.0050 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top1_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 1 | 0.0500 | 0.0010 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top1_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 1 | 0.0500 | 0.0025 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top1_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 1 | 0.0500 | 0.0050 | 1 | svc_group_level=artist | -0.0500 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 2 | 0.0250 | 0.0010 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 2 | 0.0250 | 0.0025 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top2_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 2 | 0.0250 | 0.0050 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 2 | 0.0500 | 0.0010 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 2 | 0.0500 | 0.0025 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | s03 | mape_dir | 2 | 0.0500 | 0.0050 | 2 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 1 | 0.0250 | 0.0010 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 1 | 0.0250 | 0.0025 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 1 | 0.0250 | 0.0050 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 1 | 0.0500 | 0.0010 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top1_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 1 | 0.0500 | 0.0025 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top1_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 1 | 0.0500 | 0.0050 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 2 | 0.0250 | 0.0010 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 2 | 0.0250 | 0.0025 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 2 | 0.0250 | 0.0050 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 2 | 0.0500 | 0.0010 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 2 | 0.0500 | 0.0025 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_p95_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | p95_dir | 2 | 0.0500 | 0.0050 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 1 | 0.0250 | 0.0010 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 1 | 0.0250 | 0.0025 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 1 | 0.0250 | 0.0050 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 1 | 0.0500 | 0.0010 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top1_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 1 | 0.0500 | 0.0025 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top1_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 1 | 0.0500 | 0.0050 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 2 | 0.0250 | 0.0010 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 2 | 0.0250 | 0.0025 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 2 | 0.0250 | 0.0050 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 2 | 0.0500 | 0.0010 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 2 | 0.0500 | 0.0025 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s02_any2_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | any2_dir | 2 | 0.0500 | 0.0050 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0551 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 1 | 0.0250 | 0.0010 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 1 | 0.0250 | 0.0025 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 1 | 0.0250 | 0.0050 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 1 | 0.0500 | 0.0010 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top1_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 1 | 0.0500 | 0.0025 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top1_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 1 | 0.0500 | 0.0050 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 2 | 0.0250 | 0.0010 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 2 | 0.0250 | 0.0025 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 2 | 0.0250 | 0.0050 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 2 | 0.0500 | 0.0010 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 2 | 0.0500 | 0.0025 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_p95_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | p95_dir | 2 | 0.0500 | 0.0050 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 1 | 0.0250 | 0.0010 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 1 | 0.0250 | 0.0025 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 1 | 0.0250 | 0.0050 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 1 | 0.0500 | 0.0010 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top1_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 1 | 0.0500 | 0.0025 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top1_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 1 | 0.0500 | 0.0050 | 1 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | -0.0645 | 87 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 2 | 0.0250 | 0.0010 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 2 | 0.0250 | 0.0025 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 2 | 0.0250 | 0.0050 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 2 | 0.0500 | 0.0010 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 2 | 0.0500 | 0.0025 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | any2_dir | 2 | 0.0500 | 0.0050 | 2 | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| pred_spread_band=spread_high & gap_band=gap_010_020 | -0.0545 | 34 | stable + clipped directional micro move inside validation-consensus segments |

## 6. 선택 후보 요약

| candidate | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | repeated_min_any2_improve_prob | repeated_min_all3_improve_prob | fixed_test_p95_guard | stress0604_p95_guard | test_mean_move_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | True | True |  |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2729 | 0.8062 | 0.2727 | 0.3744 | 0.9834 | 0.8280 | 0.3060 | True | True | 0.0139 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2729 | 0.8062 | 0.2726 | 0.3744 | 0.9834 | 0.8280 | 0.3060 | True | True | 0.0139 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2729 | 0.8062 | 0.2726 | 0.3744 | 0.9834 | 0.8280 | 0.3060 | True | True | 0.0139 |
| hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | MAPE 목적 후보 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3320 | 0.0400 | True | True | 0.0093 |
| hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | MAPE 목적 후보 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3742 | 0.9835 | 0.2700 | 0.0300 | True | True | 0.0093 |
| hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | MAPE 목적 후보 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3320 | 0.0400 | True | True | 0.0093 |
| hcoef32_s01_p95_dir_top2_w0p05_cap0p005 | MAPE 목적 후보 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3742 | 0.9835 | 0.2700 | 0.0300 | True | True | 0.0093 |
| hcoef32_s02_any2_dir_top2_w0p05_cap0p0025 | MAPE 목적 후보 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3320 | 0.0400 | True | True | 0.0093 |
| hcoef32_s02_any2_dir_top2_w0p05_cap0p005 | MAPE 목적 후보 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3320 | 0.0400 | True | True | 0.0093 |
| hcoef32_s02_p95_dir_top2_w0p05_cap0p0025 | MAPE 목적 후보 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3320 | 0.0400 | True | True | 0.0093 |
| hcoef32_s02_p95_dir_top2_w0p05_cap0p005 | MAPE 목적 후보 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3320 | 0.0400 | True | True | 0.0093 |
| hcoef32_s01_any2_dir_top2_w0p05_cap0p001 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1257 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.4420 | 0.0860 | True | True | 0.0093 |
| hcoef32_s01_p95_dir_top2_w0p05_cap0p001 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1257 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.4420 | 0.0860 | True | True | 0.0093 |
| hcoef32_s02_any2_dir_top2_w0p05_cap0p001 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1257 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.4420 | 0.0860 | True | True | 0.0093 |
| hcoef32_s02_p95_dir_top2_w0p05_cap0p001 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1257 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.4420 | 0.0860 | True | True | 0.0093 |
| hcoef32_s01_any2_dir_top2_w0p025_cap0p0025 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.2600 | 0.0280 | True | True | 0.0047 |
| hcoef32_s01_any2_dir_top2_w0p025_cap0p005 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.2600 | 0.0280 | True | True | 0.0047 |
| hcoef32_s01_p95_dir_top2_w0p025_cap0p0025 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.2600 | 0.0280 | True | True | 0.0047 |
| hcoef32_s01_p95_dir_top2_w0p025_cap0p005 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.2600 | 0.0280 | True | True | 0.0047 |
| hcoef32_s02_any2_dir_top2_w0p025_cap0p0025 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3160 | 0.0420 | True | True | 0.0047 |
| hcoef32_s02_any2_dir_top2_w0p025_cap0p005 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3160 | 0.0420 | True | True | 0.0047 |
| hcoef32_s02_p95_dir_top2_w0p025_cap0p0025 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3160 | 0.0420 | True | True | 0.0047 |
| hcoef32_s02_p95_dir_top2_w0p025_cap0p005 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3160 | 0.0420 | True | True | 0.0047 |
| hcoef32_s01_any2_dir_top2_w0p025_cap0p001 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3380 | 0.0440 | True | True | 0.0047 |
| hcoef32_s01_p95_dir_top2_w0p025_cap0p001 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3380 | 0.0440 | True | True | 0.0047 |
| hcoef32_s02_any2_dir_top2_w0p025_cap0p001 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3380 | 0.0440 | True | True | 0.0047 |
| hcoef32_s02_p95_dir_top2_w0p025_cap0p001 | MAPE 목적 후보 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3380 | 0.0440 | True | True | 0.0047 |
| current_70_30 | 최소 비교 기준 | 0.1305 | 0.2110 | 0.6580 | 0.1305 | 0.2110 | 0.6580 | 0.1405 | 0.2748 | 0.8331 | 0.2779 | 0.3774 | 0.9871 | 0.0000 | 0.0000 | False | False |  |
| svc_numeric_seed_mean | component 대조군 | 0.1272 | 0.2176 | 0.6504 | 0.1272 | 0.2176 | 0.6504 | 0.1520 | 0.2942 | 0.9381 | 0.3072 | 0.4318 | 0.9998 | 0.0640 | 0.0000 | False | False |  |
| ppv8_service_proxy | component 대조군 | 0.1544 | 0.2544 | 0.8084 | 0.1544 | 0.2544 | 0.8084 | 0.1632 | 0.2816 | 0.9311 | 0.2298 | 0.3359 | 0.9273 | 0.0000 | 0.0000 | False | True |  |
| l10_seq_full_generated_bucket | component 대조군 | 0.1685 | 0.2981 | 0.8769 | 0.1685 | 0.2981 | 0.8769 | 0.1743 | 0.3265 | 0.9818 | 0.3207 | 0.4598 | 1.2569 | 0.0000 | 0.0000 | False | False |  |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2729 | 0.8064 | 0.2719 | 0.3744 | 0.9834 | 0.8760 | 0.3660 | False | True | 0.0278 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2729 | 0.8064 | 0.2719 | 0.3744 | 0.9834 | 0.8760 | 0.3660 | False | True | 0.0278 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2729 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8580 | 0.3520 | False | True | 0.0259 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p005 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2729 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8580 | 0.3520 | False | True | 0.0259 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p0025 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8560 | 0.3520 | False | True | 0.0243 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p005 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8560 | 0.3520 | False | True | 0.0243 |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p0025 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8560 | 0.3520 | False | True | 0.0243 |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p005 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8560 | 0.3520 | False | True | 0.0243 |
| hcoef32_s03_mape_dir_top1_w0p05_cap0p0025 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8560 | 0.3520 | False | True | 0.0243 |
| hcoef32_s03_mape_dir_top1_w0p05_cap0p005 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8560 | 0.3520 | False | True | 0.0243 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p0025 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8560 | 0.3520 | False | True | 0.0243 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p005 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1381 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8560 | 0.3520 | False | True | 0.0243 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | 보류 | 0.1260 | 0.2081 | 0.6465 | 0.1260 | 0.2081 | 0.6465 | 0.1386 | 0.2729 | 0.8064 | 0.2727 | 0.3744 | 0.9834 | 0.8420 | 0.3360 | False | True | 0.0278 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p001 | 보류 | 0.1260 | 0.2081 | 0.6465 | 0.1260 | 0.2081 | 0.6465 | 0.1386 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8340 | 0.3280 | False | True | 0.0259 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p001 | 보류 | 0.1260 | 0.2081 | 0.6465 | 0.1260 | 0.2081 | 0.6465 | 0.1386 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8320 | 0.3280 | False | True | 0.0243 |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p001 | 보류 | 0.1260 | 0.2081 | 0.6465 | 0.1260 | 0.2081 | 0.6465 | 0.1386 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8320 | 0.3280 | False | True | 0.0243 |
| hcoef32_s03_mape_dir_top1_w0p05_cap0p001 | 보류 | 0.1260 | 0.2081 | 0.6465 | 0.1260 | 0.2081 | 0.6465 | 0.1386 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8320 | 0.3280 | False | True | 0.0243 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p001 | 보류 | 0.1260 | 0.2081 | 0.6465 | 0.1260 | 0.2081 | 0.6465 | 0.1386 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8320 | 0.3280 | False | True | 0.0243 |
| hcoef32_s03_any2_dir_top2_w0p05_cap0p001 | 보류 | 0.1260 | 0.2081 | 0.6465 | 0.1260 | 0.2081 | 0.6465 | 0.1386 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8380 | 0.3320 | False | True | 0.0268 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | 보류 | 0.1260 | 0.2081 | 0.6465 | 0.1260 | 0.2081 | 0.6465 | 0.1386 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8380 | 0.3320 | False | True | 0.0268 |
| hcoef32_s03_mape_dir_top2_w0p025_cap0p001 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8200 | 0.2980 | False | True | 0.0130 |
| hcoef32_s03_mape_dir_top2_w0p025_cap0p0025 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8200 | 0.2980 | False | True | 0.0130 |
| hcoef32_s03_mape_dir_top2_w0p025_cap0p005 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8200 | 0.2980 | False | True | 0.0130 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p001 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p001 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_mape_dir_top1_w0p025_cap0p001 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p001 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p0025 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p005 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p0025 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p005 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_mape_dir_top1_w0p025_cap0p0025 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_mape_dir_top1_w0p025_cap0p005 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p0025 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p005 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8180 | 0.2980 | False | True | 0.0121 |
| hcoef32_s03_any2_dir_top2_w0p05_cap0p0025 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1388 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8620 | 0.3560 | False | True | 0.0268 |
| hcoef32_s03_any2_dir_top2_w0p05_cap0p005 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1388 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8620 | 0.3560 | False | True | 0.0268 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1388 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8620 | 0.3560 | False | True | 0.0268 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | 보류 | 0.1260 | 0.2081 | 0.6457 | 0.1260 | 0.2081 | 0.6464 | 0.1388 | 0.2730 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8620 | 0.3560 | False | True | 0.0268 |
| hcoef32_s03_any2_dir_top2_w0p025_cap0p001 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8380 | 0.3320 | False | True | 0.0134 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8380 | 0.3320 | False | True | 0.0134 |
| hcoef32_s03_any2_dir_top2_w0p025_cap0p0025 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8380 | 0.3320 | False | True | 0.0134 |
| hcoef32_s03_any2_dir_top2_w0p025_cap0p005 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8380 | 0.3320 | False | True | 0.0134 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8380 | 0.3320 | False | True | 0.0134 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | 보류 | 0.1260 | 0.2082 | 0.6468 | 0.1260 | 0.2082 | 0.6472 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9834 | 0.8380 | 0.3320 | False | True | 0.0134 |
| hcoef32_s01_any2_dir_top1_w0p025_cap0p001 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3000 | 0.0420 | True | True | 0.0030 |
| hcoef32_s01_any2_dir_top1_w0p025_cap0p0025 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3040 | 0.0420 | True | True | 0.0030 |
| hcoef32_s01_any2_dir_top1_w0p025_cap0p005 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3040 | 0.0420 | True | True | 0.0030 |
| hcoef32_s01_p95_dir_top1_w0p025_cap0p001 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3000 | 0.0420 | True | True | 0.0030 |
| hcoef32_s01_p95_dir_top1_w0p025_cap0p0025 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3040 | 0.0420 | True | True | 0.0030 |
| hcoef32_s01_p95_dir_top1_w0p025_cap0p005 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3040 | 0.0420 | True | True | 0.0030 |
| hcoef32_s02_any2_dir_top1_w0p025_cap0p001 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3000 | 0.0420 | True | True | 0.0030 |
| hcoef32_s02_any2_dir_top1_w0p025_cap0p0025 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3040 | 0.0420 | True | True | 0.0030 |
| hcoef32_s02_any2_dir_top1_w0p025_cap0p005 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3040 | 0.0420 | True | True | 0.0030 |
| hcoef32_s02_p95_dir_top1_w0p025_cap0p001 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3000 | 0.0420 | True | True | 0.0030 |
| hcoef32_s02_p95_dir_top1_w0p025_cap0p0025 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3040 | 0.0420 | True | True | 0.0030 |
| hcoef32_s02_p95_dir_top1_w0p025_cap0p005 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1259 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3040 | 0.0420 | True | True | 0.0030 |
| hcoef32_s01_any2_dir_top1_w0p05_cap0p001 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1257 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.3680 | 0.0460 | True | True | 0.0060 |
| hcoef32_s01_p95_dir_top1_w0p05_cap0p001 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1257 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.3680 | 0.0460 | True | True | 0.0060 |
| hcoef32_s02_any2_dir_top1_w0p05_cap0p001 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1257 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.3680 | 0.0460 | True | True | 0.0060 |
| hcoef32_s02_p95_dir_top1_w0p05_cap0p001 | 보류 | 0.1257 | 0.2082 | 0.6479 | 0.1257 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.3680 | 0.0460 | True | True | 0.0060 |
| hcoef32_s01_any2_dir_top1_w0p05_cap0p0025 | 보류 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3340 | 0.0100 | True | True | 0.0060 |
| hcoef32_s01_any2_dir_top1_w0p05_cap0p005 | 보류 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3340 | 0.0100 | True | True | 0.0060 |
| hcoef32_s01_p95_dir_top1_w0p05_cap0p0025 | 보류 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3340 | 0.0100 | True | True | 0.0060 |
| hcoef32_s01_p95_dir_top1_w0p05_cap0p005 | 보류 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3340 | 0.0100 | True | True | 0.0060 |
| hcoef32_s02_any2_dir_top1_w0p05_cap0p0025 | 보류 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3340 | 0.0100 | True | True | 0.0060 |
| hcoef32_s02_any2_dir_top1_w0p05_cap0p005 | 보류 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3340 | 0.0100 | True | True | 0.0060 |
| hcoef32_s02_p95_dir_top1_w0p05_cap0p0025 | 보류 | 0.1249 | 0.2082 | 0.6479 | 0.1253 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3743 | 0.9835 | 0.3340 | 0.0100 | True | True | 0.0060 |

## 7. Scope별 metrics

| scope | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mean_move_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |  |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p08 | 0.2641 | 0.3742 | 0.9833 | 1.2996 | -0.0090 | -0.0002 | -0.0001 | 0.4993 |
| 0604_stress | hcoef29_risk_guarded_component_s0p5_cap0p05 | 0.2751 | 0.3690 | 0.9466 | 1.3208 | 0.0020 | -0.0053 | -0.0369 | 0.2932 |
| 0604_stress | hcoef29_risk_guarded_component_s0p5_cap0p08 | 0.2789 | 0.3678 | 0.9446 | 1.3281 | 0.0058 | -0.0065 | -0.0389 | 0.3990 |
| 0604_stress | hcoef32_s01_any2_dir_top1_w0p025_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s01_any2_dir_top1_w0p025_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s01_any2_dir_top1_w0p025_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s01_any2_dir_top1_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s01_any2_dir_top1_w0p05_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s01_any2_dir_top1_w0p05_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s01_any2_dir_top2_w0p025_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s01_any2_dir_top2_w0p025_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s01_any2_dir_top2_w0p025_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s01_any2_dir_top2_w0p05_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | 0.2731 | 0.3742 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s01_p95_dir_top1_w0p025_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s01_p95_dir_top1_w0p025_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s01_p95_dir_top1_w0p025_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s01_p95_dir_top1_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s01_p95_dir_top1_w0p05_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s01_p95_dir_top1_w0p05_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s01_p95_dir_top2_w0p025_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s01_p95_dir_top2_w0p025_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s01_p95_dir_top2_w0p025_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s01_p95_dir_top2_w0p05_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s01_p95_dir_top2_w0p05_cap0p005 | 0.2731 | 0.3742 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s02_any2_dir_top1_w0p025_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s02_any2_dir_top1_w0p025_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s02_any2_dir_top1_w0p025_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s02_any2_dir_top1_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s02_any2_dir_top1_w0p05_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s02_any2_dir_top1_w0p05_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s02_any2_dir_top2_w0p025_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s02_any2_dir_top2_w0p025_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s02_any2_dir_top2_w0p025_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s02_any2_dir_top2_w0p05_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s02_any2_dir_top2_w0p05_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s02_any2_dir_top2_w0p05_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s02_p95_dir_top1_w0p025_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s02_p95_dir_top1_w0p025_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s02_p95_dir_top1_w0p025_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0016 |
| 0604_stress | hcoef32_s02_p95_dir_top1_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s02_p95_dir_top1_w0p05_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s02_p95_dir_top1_w0p05_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0032 |
| 0604_stress | hcoef32_s02_p95_dir_top2_w0p025_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s02_p95_dir_top2_w0p025_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s02_p95_dir_top2_w0p025_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0024 |
| 0604_stress | hcoef32_s02_p95_dir_top2_w0p05_cap0p001 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s02_p95_dir_top2_w0p05_cap0p0025 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s02_p95_dir_top2_w0p05_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0047 |
| 0604_stress | hcoef32_s03_all3_dir_top1_w0p025_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_all3_dir_top1_w0p025_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_all3_dir_top1_w0p025_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_all3_dir_top1_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_all3_dir_top1_w0p05_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3075 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_all3_dir_top1_w0p05_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3074 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 0.2727 | 0.3744 | 0.9834 | 1.3076 | -0.0004 | -0.0000 | -0.0000 | 0.0146 |
| 0604_stress | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 0.2726 | 0.3744 | 0.9834 | 1.3076 | -0.0004 | -0.0000 | -0.0000 | 0.0146 |
| 0604_stress | hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | 0.2726 | 0.3744 | 0.9834 | 1.3076 | -0.0004 | -0.0000 | -0.0000 | 0.0146 |
| 0604_stress | hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | 0.2727 | 0.3744 | 0.9834 | 1.3076 | -0.0004 | 0.0000 | -0.0000 | 0.0291 |
| 0604_stress | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 0.2719 | 0.3744 | 0.9834 | 1.3074 | -0.0012 | -0.0000 | -0.0000 | 0.0291 |
| 0604_stress | hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | 0.2719 | 0.3744 | 0.9834 | 1.3074 | -0.0012 | -0.0000 | -0.0000 | 0.0291 |
| 0604_stress | hcoef32_s03_any2_dir_top1_w0p025_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_any2_dir_top1_w0p025_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_any2_dir_top1_w0p025_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_any2_dir_top1_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_any2_dir_top1_w0p05_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3075 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_any2_dir_top1_w0p05_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3074 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_any2_dir_top2_w0p025_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0127 |
| 0604_stress | hcoef32_s03_any2_dir_top2_w0p025_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0127 |
| 0604_stress | hcoef32_s03_any2_dir_top2_w0p025_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0127 |
| 0604_stress | hcoef32_s03_any2_dir_top2_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0255 |
| 0604_stress | hcoef32_s03_any2_dir_top2_w0p05_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3075 | 0.0000 | 0.0000 | -0.0000 | 0.0255 |
| 0604_stress | hcoef32_s03_any2_dir_top2_w0p05_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3074 | 0.0000 | 0.0000 | -0.0000 | 0.0255 |
| 0604_stress | hcoef32_s03_mape_dir_top1_w0p025_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_mape_dir_top1_w0p025_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_mape_dir_top1_w0p025_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_mape_dir_top1_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_mape_dir_top1_w0p05_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3075 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_mape_dir_top1_w0p05_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3074 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_mape_dir_top2_w0p025_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0133 |
| 0604_stress | hcoef32_s03_mape_dir_top2_w0p025_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0133 |
| 0604_stress | hcoef32_s03_mape_dir_top2_w0p025_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0133 |
| 0604_stress | hcoef32_s03_mape_dir_top2_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0267 |
| 0604_stress | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3075 | 0.0000 | 0.0000 | -0.0000 | 0.0267 |
| 0604_stress | hcoef32_s03_mape_dir_top2_w0p05_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3074 | 0.0000 | 0.0000 | -0.0000 | 0.0267 |
| 0604_stress | hcoef32_s03_p95_dir_top1_w0p025_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_p95_dir_top1_w0p025_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_p95_dir_top1_w0p025_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0124 |
| 0604_stress | hcoef32_s03_p95_dir_top1_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_p95_dir_top1_w0p05_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3075 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_p95_dir_top1_w0p05_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3074 | 0.0000 | 0.0000 | -0.0000 | 0.0248 |
| 0604_stress | hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0127 |
| 0604_stress | hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0127 |
| 0604_stress | hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3076 | 0.0000 | 0.0000 | -0.0000 | 0.0127 |
| 0604_stress | hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | 0.2731 | 0.3744 | 0.9834 | 1.3077 | 0.0000 | 0.0000 | -0.0000 | 0.0255 |
| 0604_stress | hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | 0.2731 | 0.3744 | 0.9834 | 1.3075 | 0.0000 | 0.0000 | -0.0000 | 0.0255 |
| 0604_stress | hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3074 | 0.0000 | 0.0000 | -0.0000 | 0.0255 |
| 0604_stress | hcoef_stable | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 |  |
| 0604_stress | l10_seq_full_generated_bucket | 0.3207 | 0.4598 | 1.2569 | 1.0793 | 0.0477 | 0.0854 | 0.2734 |  |
| 0604_stress | ppv8_service_proxy | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 |  |
| 0604_stress | svc_numeric_seed_mean | 0.3072 | 0.4318 | 0.9998 | 1.6906 | 0.0342 | 0.0575 | 0.0164 |  |
| fixed_confirmation | current_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 |  |
| fixed_confirmation | hcoef29_core_component_delta_s0p5_cap0p08 | 0.1453 | 0.2731 | 0.8288 | 0.3991 | 0.0065 | 0.0001 | 0.0224 | 0.5000 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p5_cap0p05 | 0.1442 | 0.2719 | 0.8081 | 0.3975 | 0.0054 | -0.0010 | 0.0018 | 0.4992 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p5_cap0p08 | 0.1442 | 0.2718 | 0.8081 | 0.3974 | 0.0054 | -0.0012 | 0.0018 | 0.5000 |
| fixed_confirmation | hcoef32_s01_any2_dir_top1_w0p025_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s01_any2_dir_top1_w0p025_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s01_any2_dir_top1_w0p025_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s01_any2_dir_top1_w0p05_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s01_any2_dir_top1_w0p05_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s01_any2_dir_top1_w0p05_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s01_any2_dir_top2_w0p025_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| fixed_confirmation | hcoef32_s01_any2_dir_top2_w0p025_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| fixed_confirmation | hcoef32_s01_any2_dir_top2_w0p025_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| fixed_confirmation | hcoef32_s01_any2_dir_top2_w0p05_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0093 |
| fixed_confirmation | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0093 |
| fixed_confirmation | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0093 |
| fixed_confirmation | hcoef32_s01_p95_dir_top1_w0p025_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s01_p95_dir_top1_w0p025_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s01_p95_dir_top1_w0p025_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s01_p95_dir_top1_w0p05_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s01_p95_dir_top1_w0p05_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s01_p95_dir_top1_w0p05_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s01_p95_dir_top2_w0p025_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| fixed_confirmation | hcoef32_s01_p95_dir_top2_w0p025_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| fixed_confirmation | hcoef32_s01_p95_dir_top2_w0p025_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| fixed_confirmation | hcoef32_s01_p95_dir_top2_w0p05_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0093 |
| fixed_confirmation | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0093 |
| fixed_confirmation | hcoef32_s01_p95_dir_top2_w0p05_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0093 |
| fixed_confirmation | hcoef32_s02_any2_dir_top1_w0p025_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s02_any2_dir_top1_w0p025_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s02_any2_dir_top1_w0p025_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0030 |
| fixed_confirmation | hcoef32_s02_any2_dir_top1_w0p05_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s02_any2_dir_top1_w0p05_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s02_any2_dir_top1_w0p05_cap0p005 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 0.0060 |
| fixed_confirmation | hcoef32_s02_any2_dir_top2_w0p025_cap0p001 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |
| fixed_confirmation | hcoef32_s02_any2_dir_top2_w0p025_cap0p0025 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | -0.0000 | 0.0000 | 0.0047 |

## 8. 반복 split/artist holdout 요약

| source_scope | validation_scheme | candidate | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | any2_improve_prob | all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | -0.0002 | -0.0001 | -0.0006 | 0.5240 | 1.0000 | 0.9080 | 0.9680 | 0.4640 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top2_w0p05_cap0p001 | -0.0002 | -0.0001 | -0.0006 | 0.5240 | 1.0000 | 0.9080 | 0.9680 | 0.4640 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | -0.0002 | -0.0001 | -0.0006 | 0.5380 | 1.0000 | 0.9080 | 0.9660 | 0.4800 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | -0.0002 | -0.0001 | -0.0007 | 0.5240 | 1.0000 | 0.9080 | 0.9660 | 0.4660 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | -0.0002 | -0.0001 | -0.0007 | 0.5240 | 1.0000 | 0.9080 | 0.9660 | 0.4660 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top2_w0p05_cap0p0025 | -0.0002 | -0.0001 | -0.0007 | 0.5240 | 1.0000 | 0.9080 | 0.9660 | 0.4660 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top2_w0p05_cap0p005 | -0.0002 | -0.0001 | -0.0007 | 0.5240 | 1.0000 | 0.9080 | 0.9660 | 0.4660 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.5020 | 1.0000 | 0.9080 | 0.9660 | 0.4440 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.5020 | 1.0000 | 0.9080 | 0.9660 | 0.4440 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.5020 | 1.0000 | 0.9080 | 0.9660 | 0.4440 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top2_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.5020 | 1.0000 | 0.9080 | 0.9660 | 0.4440 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top2_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.5020 | 1.0000 | 0.9080 | 0.9660 | 0.4440 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top2_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.5020 | 1.0000 | 0.9080 | 0.9660 | 0.4440 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p001 | -0.0002 | -0.0001 | -0.0006 | 0.4980 | 1.0000 | 0.9080 | 0.9660 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top1_w0p05_cap0p001 | -0.0002 | -0.0001 | -0.0006 | 0.4960 | 1.0000 | 0.9080 | 0.9660 | 0.4380 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top1_w0p05_cap0p001 | -0.0002 | -0.0001 | -0.0006 | 0.4960 | 1.0000 | 0.9080 | 0.9660 | 0.4380 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top1_w0p05_cap0p001 | -0.0002 | -0.0001 | -0.0006 | 0.4960 | 1.0000 | 0.9080 | 0.9660 | 0.4380 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top1_w0p05_cap0p001 | -0.0002 | -0.0001 | -0.0006 | 0.4960 | 1.0000 | 0.9080 | 0.9660 | 0.4380 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | -0.0002 | -0.0001 | -0.0007 | 0.5500 | 1.0000 | 0.9080 | 0.9640 | 0.4940 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | -0.0002 | -0.0001 | -0.0007 | 0.5500 | 1.0000 | 0.9080 | 0.9640 | 0.4940 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top1_w0p05_cap0p0025 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top1_w0p05_cap0p005 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top1_w0p05_cap0p0025 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top1_w0p05_cap0p005 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top1_w0p05_cap0p0025 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top1_w0p05_cap0p005 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top1_w0p05_cap0p0025 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top1_w0p05_cap0p005 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p005 | -0.0002 | -0.0001 | -0.0007 | 0.4960 | 1.0000 | 0.9080 | 0.9640 | 0.4400 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.4940 | 1.0000 | 0.9080 | 0.9640 | 0.4380 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.4940 | 1.0000 | 0.9080 | 0.9640 | 0.4380 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.4940 | 1.0000 | 0.9080 | 0.9640 | 0.4380 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top2_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.4540 | 1.0000 | 0.9080 | 0.9640 | 0.3980 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top2_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.4540 | 1.0000 | 0.9080 | 0.9640 | 0.3980 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top2_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.4540 | 1.0000 | 0.9080 | 0.9640 | 0.3980 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top1_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top1_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_p95_dir_top1_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top1_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top1_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top1_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top1_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top1_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_any2_dir_top1_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top1_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top1_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top1_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.4520 | 1.0000 | 0.9080 | 0.9640 | 0.3960 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | -0.0003 | -0.0001 | -0.0006 | 0.4560 | 1.0000 | 0.9160 | 0.9560 | 0.4160 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | -0.0003 | -0.0001 | -0.0008 | 0.4560 | 1.0000 | 0.9160 | 0.9560 | 0.4160 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | -0.0003 | -0.0001 | -0.0008 | 0.4560 | 1.0000 | 0.9160 | 0.9560 | 0.4160 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top2_w0p05_cap0p001 | -0.0003 | -0.0001 | -0.0006 | 0.4560 | 1.0000 | 0.9160 | 0.9560 | 0.4160 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top2_w0p05_cap0p0025 | -0.0003 | -0.0001 | -0.0008 | 0.4560 | 1.0000 | 0.9160 | 0.9560 | 0.4160 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top2_w0p05_cap0p005 | -0.0003 | -0.0001 | -0.0008 | 0.4560 | 1.0000 | 0.9160 | 0.9560 | 0.4160 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | -0.0003 | -0.0001 | -0.0008 | 0.4360 | 1.0000 | 0.9160 | 0.9560 | 0.3960 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | -0.0003 | -0.0001 | -0.0008 | 0.4360 | 1.0000 | 0.9160 | 0.9560 | 0.3960 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | -0.0003 | -0.0001 | -0.0006 | 0.4300 | 1.0000 | 0.9160 | 0.9560 | 0.3900 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top1_w0p05_cap0p001 | -0.0003 | -0.0001 | -0.0006 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top1_w0p05_cap0p0025 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top1_w0p05_cap0p005 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top1_w0p05_cap0p001 | -0.0003 | -0.0001 | -0.0006 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top1_w0p05_cap0p0025 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top1_w0p05_cap0p005 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top1_w0p05_cap0p001 | -0.0003 | -0.0001 | -0.0006 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top1_w0p05_cap0p0025 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top1_w0p05_cap0p005 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_mape_dir_top1_w0p05_cap0p001 | -0.0003 | -0.0001 | -0.0006 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_mape_dir_top1_w0p05_cap0p0025 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_mape_dir_top1_w0p05_cap0p005 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p001 | -0.0003 | -0.0001 | -0.0006 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p005 | -0.0003 | -0.0001 | -0.0008 | 0.4120 | 1.0000 | 0.9160 | 0.9560 | 0.3720 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.4220 | 1.0000 | 0.9160 | 0.9520 | 0.3860 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.4220 | 1.0000 | 0.9160 | 0.9520 | 0.3860 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.4220 | 1.0000 | 0.9160 | 0.9520 | 0.3860 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top2_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.4220 | 1.0000 | 0.9160 | 0.9520 | 0.3860 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top2_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.4220 | 1.0000 | 0.9160 | 0.9520 | 0.3860 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_any2_dir_top2_w0p025_cap0p005 | -0.0001 | -0.0000 | -0.0004 | 0.4220 | 1.0000 | 0.9160 | 0.9520 | 0.3860 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | -0.0001 | -0.0000 | -0.0004 | 0.3980 | 1.0000 | 0.9160 | 0.9520 | 0.3620 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | -0.0001 | -0.0000 | -0.0004 | 0.3980 | 1.0000 | 0.9160 | 0.9520 | 0.3620 |

## 9. 계수/구간 해석

| candidate | source_candidate | feature | coefficient | direction | interpretation |
| --- | --- | --- | --- | --- | --- |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top1_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0471 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0086, artist residual/move 0.0461/0.0125 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0471 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0086, artist residual/move 0.0461/0.0125 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0471 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0086, artist residual/move 0.0461/0.0125 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0471 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0086, artist residual/move 0.0461/0.0125 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0471 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0086, artist residual/move 0.0461/0.0125 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0471 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0086, artist residual/move 0.0461/0.0125 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_p95_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_low & gap_band=gap_005_010 | 0.0459 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0461/0.0076, artist residual/move 0.0461/0.0043 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top1_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_any2_dir_top1_w0p025_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef32_s03_any2_dir_top1_w0p05_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |

## 10. 잔차/큰 오차 구간

| scope | split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | over_2x_n | under_half_n | delta_MdAPE_vs_candidate_overall | delta_MAPE_vs_candidate_overall | delta_p95_APE_vs_candidate_overall | median_residual_log | over_50pct_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | medium_support_size | 66 | 0.4181 | 0.5088 | 1.1162 | 0.9316 | 0.3636 | 0.5909 | 12 | 14 | 0.1401 | 0.1315 | 0.1292 | -0.0715 | 0.4091 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_n_band | n_50_plus | 105 | 0.5325 | 0.5600 | 1.0880 | 1.0454 | 0.2667 | 0.4476 | 13 | 42 | 0.2546 | 0.1827 | 0.1009 | 0.5257 | 0.5524 |
| 0604_stress | 0604_ex50 | current_70_30 | service_confidence_tier | high | 22 | 0.5918 | 0.5668 | 1.0862 | 0.8226 | 0.3636 | 0.4545 | 5 | 4 | 0.3138 | 0.1895 | 0.0991 | 0.1379 | 0.5455 |
| 0604_stress | 0604_ex50 | current_70_30 | pred_spread_band | spread_extreme | 438 | 0.4488 | 0.5067 | 1.0206 | 1.7385 | 0.3333 | 0.5434 | 23 | 144 | 0.1709 | 0.1294 | 0.0336 | 0.3172 | 0.4566 |
| 0604_stress | 0604_ex50 | current_70_30 | service_confidence_tier | medium | 308 | 0.2812 | 0.3979 | 1.0085 | 0.7228 | 0.5357 | 0.7045 | 16 | 59 | 0.0032 | 0.0206 | 0.0214 | 0.0374 | 0.2955 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 1.7996 | 0.3433 | 0.5672 | 18 | 129 | 0.1522 | 0.1280 | 0.0129 | 0.2961 | 0.4328 |
| 0604_stress | 0604_ex50 | current_70_30 | qwidth_band | qwidth_high | 185 | 0.2549 | 0.3810 | 0.9966 | 0.9949 | 0.5514 | 0.7514 | 9 | 28 | -0.0230 | 0.0037 | 0.0096 | 0.0782 | 0.2486 |
| 0604_stress | 0604_ex50 | current_70_30 | qwidth_band | qwidth_extreme | 301 | 0.3750 | 0.4420 | 0.9959 | 1.9726 | 0.4086 | 0.6279 | 7 | 100 | 0.0971 | 0.0646 | 0.0088 | 0.3569 | 0.3721 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_n_band | n_5_9 | 435 | 0.2484 | 0.3352 | 0.9871 | 1.6347 | 0.5701 | 0.7609 | 9 | 63 | -0.0296 | -0.0421 | 0.0000 | 0.0819 | 0.2391 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | artist | 412 | 0.3063 | 0.3774 | 0.9871 | 1.5835 | 0.4927 | 0.7403 | 13 | 63 | 0.0283 | 0.0000 | 0.0000 | 0.0866 | 0.2597 |
| 0604_stress | 0604_ex50 | current_70_30 | service_confidence_tier | low | 499 | 0.2689 | 0.3563 | 0.9726 | 1.5831 | 0.5291 | 0.7315 | 9 | 90 | -0.0090 | -0.0211 | -0.0145 | 0.1014 | 0.2685 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.7607 | 0.7600 | 0.9120 | 6 | 3 | -0.1248 | -0.1201 | -0.0410 | 0.0641 | 0.0880 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | medium_size | 18 | 0.7774 | 0.6869 | 0.9043 | 1.2389 | 0.1111 | 0.2222 | 1 | 12 | 0.4995 | 0.3095 | -0.0827 | 1.3750 | 0.7778 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_n_band | n_20_49 | 90 | 0.1979 | 0.3351 | 0.8965 | 0.6260 | 0.6000 | 0.7667 | 3 | 13 | -0.0800 | -0.0423 | -0.0906 | 0.0328 | 0.2333 |
| 0604_stress | 0604_ex50 | current_70_30 | qwidth_band | qwidth_mid | 242 | 0.2432 | 0.3387 | 0.8870 | 0.4745 | 0.5950 | 0.7479 | 12 | 22 | -0.0348 | -0.0387 | -0.1001 | 0.0003 | 0.2521 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_n_band | n_10_19 | 199 | 0.2854 | 0.3922 | 0.8850 | 0.7570 | 0.5377 | 0.7286 | 5 | 35 | 0.0075 | 0.0149 | -0.1021 | 0.0401 | 0.2714 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | 0.5226 | 0.5469 | 0.6875 | 5 | 16 | -0.0531 | -0.0354 | -0.1214 | -0.0556 | 0.3125 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | artist_size | 224 | 0.2138 | 0.3533 | 0.8487 | 1.0062 | 0.6071 | 0.7098 | 4 | 49 | -0.0641 | -0.0240 | -0.1383 | 0.0782 | 0.2902 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | global | 18 | 0.6453 | 0.6603 | 0.8423 | 1.2349 | 0.0000 | 0.1667 | 0 | 14 | 0.3673 | 0.2830 | -0.1447 | 0.9898 | 0.8333 |
| 0604_stress | 0604_ex50 | current_70_30 | qwidth_band | qwidth_low | 101 | 0.1977 | 0.2707 | 0.7769 | 0.4180 | 0.6733 | 0.8218 | 2 | 3 | -0.0802 | -0.1067 | -0.2102 | 0.0214 | 0.1782 |
| 0604_stress | 0604_ex50 | current_70_30 | pred_spread_band | spread_high | 124 | 0.2182 | 0.2749 | 0.7671 | 0.7736 | 0.6452 | 0.8952 | 3 | 3 | -0.0598 | -0.1025 | -0.2199 | -0.0591 | 0.1048 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | artist_medium_support_size | 91 | 0.1735 | 0.2238 | 0.7597 | 0.7716 | 0.7912 | 0.9011 | 0 | 1 | -0.1045 | -0.1535 | -0.2273 | 0.0077 | 0.0989 |
| 0604_stress | 0604_ex50 | current_70_30 | pred_spread_band | spread_low_mid | 267 | 0.1275 | 0.2127 | 0.6786 | 0.3262 | 0.7903 | 0.9101 | 4 | 6 | -0.1504 | -0.1646 | -0.3085 | 0.0281 | 0.0899 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.3186 | 0.7983 | 0.9244 | 1 | 4 | -0.1713 | -0.1820 | -0.4427 | 0.0401 | 0.0756 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.3080 | 0.7091 | 0.9455 | 0 | 1 | -0.1971 | -0.1865 | -0.4545 | 0.0305 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4958 | 1.0854 | 0.9327 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1216 | 0.1020 | -0.0440 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5503 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1761 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | service_confidence_tier | high | 22 | 0.5814 | 0.5579 | 1.0347 | 0.8123 | 0.3636 | 0.4545 | 4 | 4 | 0.3084 | 0.1836 | 0.0512 | 0.1319 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5029 | 1.0000 | 1.7332 | 0.3196 | 0.5365 | 19 | 142 | 0.1673 | 0.1286 | 0.0165 | 0.2965 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5046 | 0.9999 | 1.7951 | 0.3159 | 0.5597 | 17 | 127 | 0.1613 | 0.1303 | 0.0165 | 0.2799 | 0.4403 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_extreme | 301 | 0.3786 | 0.4380 | 0.9960 | 1.9673 | 0.4053 | 0.6279 | 7 | 100 | 0.1056 | 0.0637 | 0.0125 | 0.3534 | 0.3721 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_high | 185 | 0.2364 | 0.3758 | 0.9867 | 0.9911 | 0.5514 | 0.7297 | 6 | 27 | -0.0366 | 0.0015 | 0.0033 | 0.0736 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_5_9 | 435 | 0.2383 | 0.3309 | 0.9867 | 1.6307 | 0.5655 | 0.7632 | 9 | 63 | -0.0348 | -0.0434 | 0.0033 | 0.0655 | 0.2368 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_level | artist | 412 | 0.3193 | 0.3765 | 0.9867 | 1.5786 | 0.4854 | 0.7427 | 13 | 61 | 0.0462 | 0.0022 | 0.0033 | 0.0847 | 0.2573 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | service_confidence_tier | low | 499 | 0.2654 | 0.3523 | 0.9719 | 1.5793 | 0.5251 | 0.7335 | 9 | 90 | -0.0077 | -0.0219 | -0.0115 | 0.0952 | 0.2665 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | service_confidence_tier | medium | 308 | 0.2651 | 0.3967 | 0.9707 | 0.7178 | 0.5130 | 0.6916 | 13 | 58 | -0.0079 | 0.0224 | -0.0127 | 0.0253 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.7559 | 0.7680 | 0.9040 | 5 | 3 | -0.1233 | -0.1229 | -0.0309 | 0.0417 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_20_49 | 90 | 0.2007 | 0.3404 | 0.9167 | 0.6256 | 0.5889 | 0.7556 | 3 | 13 | -0.0723 | -0.0339 | -0.0668 | 0.0512 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_mid | 242 | 0.2383 | 0.3383 | 0.8841 | 0.4712 | 0.5661 | 0.7521 | 11 | 22 | -0.0348 | -0.0360 | -0.0993 | 0.0066 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2997 | -0.1045 | 1.3500 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | gap_band | gap_010_020 | 128 | 0.2240 | 0.3390 | 0.8728 | 0.5174 | 0.5547 | 0.6953 | 3 | 16 | -0.0490 | -0.0352 | -0.1106 | -0.0440 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_10_19 | 199 | 0.2862 | 0.3916 | 0.8641 | 0.7514 | 0.5075 | 0.7136 | 5 | 34 | 0.0132 | 0.0173 | -0.1194 | 0.0272 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_level | artist_size | 224 | 0.1911 | 0.3480 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0820 | -0.0263 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2906 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_low | 101 | 0.1785 | 0.2680 | 0.8001 | 0.4145 | 0.6634 | 0.8218 | 2 | 3 | -0.0946 | -0.1063 | -0.1833 | 0.0071 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_high | 124 | 0.2067 | 0.2766 | 0.7912 | 0.7724 | 0.6129 | 0.8952 | 3 | 3 | -0.0664 | -0.0977 | -0.1923 | -0.0440 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2239 | 0.7684 | 0.7745 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1504 | -0.2150 | -0.0021 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_low_mid | 267 | 0.1169 | 0.2086 | 0.6586 | 0.3240 | 0.7940 | 0.9101 | 4 | 7 | -0.1562 | -0.1657 | -0.3249 | 0.0131 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | gap_band | gap_000_003 | 119 | 0.1053 | 0.1887 | 0.5300 | 0.3147 | 0.7983 | 0.9244 | 1 | 5 | -0.1678 | -0.1856 | -0.4535 | 0.0272 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p0025 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1845 | 0.5173 | 0.3006 | 0.7091 | 0.9455 | 0 | 1 | -0.1862 | -0.1898 | -0.4661 | 0.0125 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4957 | 1.0854 | 0.9327 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1214 | 0.1020 | -0.0425 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5502 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1760 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | service_confidence_tier | high | 22 | 0.5814 | 0.5579 | 1.0347 | 0.8123 | 0.3636 | 0.4545 | 4 | 4 | 0.3084 | 0.1836 | 0.0512 | 0.1319 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5029 | 1.0000 | 1.7332 | 0.3196 | 0.5365 | 19 | 142 | 0.1673 | 0.1287 | 0.0165 | 0.2965 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5046 | 0.9999 | 1.7951 | 0.3159 | 0.5597 | 17 | 127 | 0.1613 | 0.1304 | 0.0165 | 0.2799 | 0.4403 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | qwidth_band | qwidth_extreme | 301 | 0.3786 | 0.4379 | 0.9960 | 1.9673 | 0.4053 | 0.6279 | 7 | 100 | 0.1056 | 0.0637 | 0.0125 | 0.3534 | 0.3721 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | qwidth_band | qwidth_high | 185 | 0.2364 | 0.3758 | 0.9867 | 0.9911 | 0.5514 | 0.7297 | 6 | 27 | -0.0366 | 0.0015 | 0.0033 | 0.0736 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_n_band | n_5_9 | 435 | 0.2383 | 0.3308 | 0.9867 | 1.6307 | 0.5655 | 0.7632 | 9 | 63 | -0.0348 | -0.0434 | 0.0033 | 0.0655 | 0.2368 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_level | artist | 412 | 0.3193 | 0.3765 | 0.9867 | 1.5786 | 0.4854 | 0.7427 | 13 | 61 | 0.0462 | 0.0023 | 0.0033 | 0.0847 | 0.2573 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | service_confidence_tier | low | 499 | 0.2654 | 0.3523 | 0.9719 | 1.5793 | 0.5251 | 0.7335 | 9 | 90 | -0.0077 | -0.0219 | -0.0115 | 0.0952 | 0.2665 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | service_confidence_tier | medium | 308 | 0.2651 | 0.3966 | 0.9707 | 0.7178 | 0.5130 | 0.6916 | 13 | 58 | -0.0079 | 0.0224 | -0.0127 | 0.0253 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2513 | 0.9526 | 0.7559 | 0.7680 | 0.9040 | 5 | 3 | -0.1233 | -0.1229 | -0.0309 | 0.0417 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_n_band | n_20_49 | 90 | 0.2007 | 0.3404 | 0.9167 | 0.6256 | 0.5889 | 0.7556 | 3 | 13 | -0.0723 | -0.0338 | -0.0668 | 0.0512 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | qwidth_band | qwidth_mid | 242 | 0.2383 | 0.3382 | 0.8841 | 0.4711 | 0.5661 | 0.7521 | 11 | 22 | -0.0348 | -0.0360 | -0.0993 | 0.0066 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2997 | -0.1045 | 1.3500 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | gap_band | gap_010_020 | 128 | 0.2234 | 0.3388 | 0.8728 | 0.5173 | 0.5547 | 0.6953 | 3 | 16 | -0.0497 | -0.0354 | -0.1106 | -0.0425 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_n_band | n_10_19 | 199 | 0.2862 | 0.3916 | 0.8641 | 0.7514 | 0.5075 | 0.7136 | 5 | 34 | 0.0132 | 0.0174 | -0.1194 | 0.0272 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_level | artist_size | 224 | 0.1911 | 0.3480 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0820 | -0.0263 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2907 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | qwidth_band | qwidth_low | 101 | 0.1785 | 0.2678 | 0.7991 | 0.4144 | 0.6634 | 0.8218 | 2 | 3 | -0.0946 | -0.1064 | -0.1843 | 0.0071 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | pred_spread_band | spread_high | 124 | 0.2058 | 0.2764 | 0.7912 | 0.7723 | 0.6129 | 0.8952 | 3 | 3 | -0.0673 | -0.0979 | -0.1923 | -0.0425 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2238 | 0.7679 | 0.7744 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1504 | -0.2155 | -0.0021 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | pred_spread_band | spread_low_mid | 267 | 0.1169 | 0.2086 | 0.6586 | 0.3240 | 0.7940 | 0.9101 | 4 | 7 | -0.1562 | -0.1656 | -0.3249 | 0.0131 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | gap_band | gap_000_003 | 119 | 0.1053 | 0.1887 | 0.5300 | 0.3147 | 0.7983 | 0.9244 | 1 | 5 | -0.1678 | -0.1856 | -0.4535 | 0.0272 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef32_s01_any2_dir_top2_w0p05_cap0p005 | gap_band | gap_003_005 | 55 | 0.0871 | 0.1845 | 0.5173 | 0.3007 | 0.7091 | 0.9455 | 0 | 1 | -0.1860 | -0.1897 | -0.4661 | 0.0125 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4958 | 1.0854 | 0.9327 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1216 | 0.1020 | -0.0440 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5503 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1761 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | service_confidence_tier | high | 22 | 0.5814 | 0.5579 | 1.0347 | 0.8123 | 0.3636 | 0.4545 | 4 | 4 | 0.3084 | 0.1836 | 0.0512 | 0.1319 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5029 | 1.0000 | 1.7332 | 0.3196 | 0.5365 | 19 | 142 | 0.1673 | 0.1286 | 0.0165 | 0.2965 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5046 | 0.9999 | 1.7951 | 0.3159 | 0.5597 | 17 | 127 | 0.1613 | 0.1303 | 0.0165 | 0.2799 | 0.4403 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_extreme | 301 | 0.3786 | 0.4380 | 0.9960 | 1.9673 | 0.4053 | 0.6279 | 7 | 100 | 0.1056 | 0.0637 | 0.0125 | 0.3534 | 0.3721 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_high | 185 | 0.2364 | 0.3758 | 0.9867 | 0.9911 | 0.5514 | 0.7297 | 6 | 27 | -0.0366 | 0.0015 | 0.0033 | 0.0736 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_5_9 | 435 | 0.2383 | 0.3309 | 0.9867 | 1.6307 | 0.5655 | 0.7632 | 9 | 63 | -0.0348 | -0.0434 | 0.0033 | 0.0655 | 0.2368 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_level | artist | 412 | 0.3193 | 0.3765 | 0.9867 | 1.5786 | 0.4854 | 0.7427 | 13 | 61 | 0.0462 | 0.0022 | 0.0033 | 0.0847 | 0.2573 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | service_confidence_tier | low | 499 | 0.2654 | 0.3523 | 0.9719 | 1.5793 | 0.5251 | 0.7335 | 9 | 90 | -0.0077 | -0.0219 | -0.0115 | 0.0952 | 0.2665 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | service_confidence_tier | medium | 308 | 0.2651 | 0.3967 | 0.9707 | 0.7178 | 0.5130 | 0.6916 | 13 | 58 | -0.0079 | 0.0224 | -0.0127 | 0.0253 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.7559 | 0.7680 | 0.9040 | 5 | 3 | -0.1233 | -0.1229 | -0.0309 | 0.0417 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_20_49 | 90 | 0.2007 | 0.3404 | 0.9167 | 0.6256 | 0.5889 | 0.7556 | 3 | 13 | -0.0723 | -0.0339 | -0.0668 | 0.0512 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_mid | 242 | 0.2383 | 0.3383 | 0.8841 | 0.4712 | 0.5661 | 0.7521 | 11 | 22 | -0.0348 | -0.0360 | -0.0993 | 0.0066 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2997 | -0.1045 | 1.3500 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | gap_band | gap_010_020 | 128 | 0.2240 | 0.3390 | 0.8728 | 0.5174 | 0.5547 | 0.6953 | 3 | 16 | -0.0490 | -0.0352 | -0.1106 | -0.0440 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_10_19 | 199 | 0.2862 | 0.3916 | 0.8641 | 0.7514 | 0.5075 | 0.7136 | 5 | 34 | 0.0132 | 0.0173 | -0.1194 | 0.0272 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_level | artist_size | 224 | 0.1911 | 0.3480 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0820 | -0.0263 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2906 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_low | 101 | 0.1785 | 0.2680 | 0.8001 | 0.4145 | 0.6634 | 0.8218 | 2 | 3 | -0.0946 | -0.1063 | -0.1833 | 0.0071 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_high | 124 | 0.2067 | 0.2766 | 0.7912 | 0.7724 | 0.6129 | 0.8952 | 3 | 3 | -0.0664 | -0.0977 | -0.1923 | -0.0440 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2239 | 0.7684 | 0.7745 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1504 | -0.2150 | -0.0021 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_low_mid | 267 | 0.1169 | 0.2086 | 0.6586 | 0.3240 | 0.7940 | 0.9101 | 4 | 7 | -0.1562 | -0.1657 | -0.3249 | 0.0131 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | gap_band | gap_000_003 | 119 | 0.1053 | 0.1887 | 0.5300 | 0.3147 | 0.7983 | 0.9244 | 1 | 5 | -0.1678 | -0.1856 | -0.4535 | 0.0272 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef32_s01_p95_dir_top2_w0p05_cap0p0025 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1845 | 0.5173 | 0.3006 | 0.7091 | 0.9455 | 0 | 1 | -0.1862 | -0.1898 | -0.4661 | 0.0125 | 0.0545 |

## 11. 다음 방향

- ultra-micro p95-first correction도 기준 후보를 넘지 못하면 점 예측 이동 추가 세분화는 중단.
- 방향 일치 segment는 가격 범위, 신뢰도, 수동 검수 기준으로 재사용.

## 12. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/segment_rule_metrics.csv`
- `outputs/consensus_rules.csv`
- `outputs/repeated_iteration_metrics.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/residual_analysis.csv`
- `outputs/selected_candidates.csv`
- `outputs/policy_configurations.csv`
- `artifacts/experiment_config.json`