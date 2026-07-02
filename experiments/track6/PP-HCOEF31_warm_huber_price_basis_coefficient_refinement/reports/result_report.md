# PP-HCOEF31 Warm Huber p95-neutral directional micro correction

- 작성일: 2026-06-08 06:54
- 목적: HCOEF30의 fixed p95 병목을 줄이기 위해 방향이 맞는 segment에만 매우 작은 보정 적용.
- 후보 선택: validation row/artist OOF segment consensus + residual direction consensus만 사용.
- fixed test와 0604는 확인용으로만 사용.

## 1. 실행 결론

- 새 운영 후보 채택 없음.
- 현재 안정 기준 `hcoef_stable` fixed test: `0.1388/0.2730/0.8064`.
- p95를 지키는 작은 이동만 허용했으므로, 개선폭이 작으면 운영 후보가 아니라 MAPE 목적 참고 후보로만 분리.

## 2. 보정 공식

- 방향 확인: segment의 `actual_log - hcoef_stable` 중앙값과 `source - hcoef_stable` 중앙값의 부호가 row/artist OOF 양쪽에서 일치하는지 확인.
- 적용식: `corrected_log = hcoef_stable + clip(weight * (source_candidate - hcoef_stable), -cap, cap)`.
- 조건을 만족하지 않으면 `hcoef_stable`을 그대로 유지.

## 3. 사용한 source 후보

| source_candidate | source_tag | source_reason |
| --- | --- | --- |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | s01 | HCOEF29 repeated any2 0.928, all3 0.548; fixed 0.1442/0.2718/0.8081 |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | s02 | HCOEF29 repeated any2 0.926, all3 0.544; fixed 0.1442/0.2719/0.8081 |
| hcoef29_core_component_delta_s0p5_cap0p08 | s03 | HCOEF29 repeated any2 0.912, all3 0.552; fixed 0.1453/0.2731/0.8288 |
| hcoef29_core_component_delta_s0p5_cap0p05 | s04 | HCOEF29 repeated any2 0.904, all3 0.542; fixed 0.1453/0.2731/0.8288 |
| hcoef29_core_component_delta_s0p5_cap0p03 | s05 | HCOEF29 repeated any2 0.876, all3 0.480; fixed 0.1453/0.2731/0.8288 |
| hcoef29_core_component_delta_s0p5_cap0p02 | s06 | HCOEF29 repeated any2 0.874, all3 0.496; fixed 0.1452/0.2732/0.8283 |

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
| hcoef29_core_component_delta_s0p5_cap0p03 | level_gap | svc_group_level=artist & gap_band=gap_003_005 | 26 | -0.1674 | -0.0555 | 0.0081 | -0.0555 | 0.0082 | -0.0206 | -0.0207 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p05 | level_gap | svc_group_level=artist & gap_band=gap_003_005 | 26 | -0.1588 | -0.0555 | 0.0081 | -0.0555 | 0.0082 | -0.0206 | -0.0189 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_003_005 | 26 | -0.1588 | -0.0555 | 0.0081 | -0.0555 | 0.0082 | -0.0206 | -0.0189 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p02 | level_gap | svc_group_level=artist & gap_band=gap_003_005 | 26 | -0.1585 | -0.0555 | 0.0081 | -0.0555 | 0.0082 | -0.0190 | -0.0191 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth | qwidth_band=qwidth_extreme | 104 | -0.1369 | 0.0201 | -0.0062 | 0.0201 | -0.0089 | 0.0086 | 0.0055 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth | qwidth_band=qwidth_extreme | 104 | -0.1363 | 0.0201 | -0.0062 | 0.0201 | -0.0089 | 0.0086 | 0.0055 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_extreme | 54 | -0.1054 | -0.0168 | 0.0094 | -0.0168 | 0.0091 | -0.0015 | -0.0059 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_extreme | 54 | -0.1051 | -0.0168 | 0.0094 | -0.0168 | 0.0091 | -0.0015 | -0.0059 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p03 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_extreme | 54 | -0.1045 | -0.0168 | 0.0094 | -0.0168 | 0.0091 | -0.0015 | -0.0059 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p02 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_extreme | 54 | -0.1002 | -0.0168 | 0.0094 | -0.0168 | 0.0091 | -0.0015 | -0.0059 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p03 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_high | 37 | -0.0969 | 0.0121 | -0.0012 | 0.0121 | -0.0034 | -0.0183 | -0.0168 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p02 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_high | 37 | -0.0964 | 0.0121 | -0.0012 | 0.0121 | -0.0034 | -0.0183 | -0.0168 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p03 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_10_19 | 33 | -0.0950 | -0.1515 | -0.0050 | -0.1515 | -0.0055 | 0.0062 | -0.0019 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p05 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_10_19 | 33 | -0.0950 | -0.1515 | -0.0050 | -0.1515 | -0.0055 | 0.0062 | -0.0019 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_10_19 | 33 | -0.0950 | -0.1515 | -0.0050 | -0.1515 | -0.0055 | 0.0062 | -0.0019 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_high | 37 | -0.0932 | 0.0121 | -0.0012 | 0.0121 | -0.0034 | -0.0183 | -0.0168 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_high | 37 | -0.0932 | 0.0121 | -0.0012 | 0.0121 | -0.0034 | -0.0183 | -0.0168 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p05 | level_gap | svc_group_level=artist & gap_band=gap_000_003 | 62 | -0.0890 | 0.0136 | -0.0010 | 0.0136 | -0.0015 | -0.0117 | -0.0069 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_000_003 | 62 | -0.0890 | 0.0136 | -0.0010 | 0.0136 | -0.0015 | -0.0117 | -0.0069 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p03 | level_gap | svc_group_level=artist & gap_band=gap_000_003 | 62 | -0.0888 | 0.0136 | -0.0010 | 0.0136 | -0.0015 | -0.0117 | -0.0069 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p02 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_10_19 | 33 | -0.0847 | -0.1515 | -0.0050 | -0.1515 | -0.0055 | 0.0062 | -0.0019 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p02 | level_gap | svc_group_level=artist & gap_band=gap_000_003 | 62 | -0.0790 | 0.0136 | -0.0010 | 0.0136 | -0.0015 | -0.0064 | -0.0052 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_020_plus | 54 | -0.0728 | -0.0404 | -0.0093 | -0.0404 | -0.0219 | -0.0070 | -0.0195 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_010_020 | 29 | -0.0696 | 0.0277 | -0.0011 | 0.0277 | 0.0021 | -0.0173 | -0.0041 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_010_020 | 29 | -0.0696 | 0.0277 | -0.0011 | 0.0277 | 0.0021 | -0.0173 | -0.0041 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_020_plus | 54 | -0.0650 | -0.0404 | -0.0093 | -0.0404 | -0.0219 | -0.0049 | -0.0149 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_n | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | 87 | -0.0645 | 0.0144 | 0.0179 | 0.0144 | 0.0166 | -0.0107 | -0.0129 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_low & svc_group_n_band=n_5_9 | 87 | -0.0645 | 0.0144 | 0.0179 | 0.0144 | 0.0166 | -0.0107 | -0.0129 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p03 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_mid | 87 | -0.0624 | -0.0343 | -0.0026 | -0.0343 | -0.0003 | 0.0049 | -0.0018 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_010_020 | 36 | -0.0623 | -0.0491 | -0.0088 | -0.0491 | -0.0089 | -0.0127 | -0.0200 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_mid | 87 | -0.0622 | -0.0343 | -0.0026 | -0.0343 | -0.0003 | 0.0049 | -0.0018 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_mid | 87 | -0.0622 | -0.0343 | -0.0026 | -0.0343 | -0.0003 | 0.0049 | -0.0018 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread_gap | pred_spread_band=spread_extreme & gap_band=gap_010_020 | 36 | -0.0619 | -0.0491 | -0.0088 | -0.0491 | -0.0089 | -0.0127 | -0.0200 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level | svc_group_level=artist | 252 | -0.0603 | 0.0111 | 0.0003 | 0.0111 | -0.0015 | -0.0057 | -0.0036 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p03 | level_qwidth | svc_group_level=artist_medium_support_size & qwidth_band=qwidth_high | 27 | -0.0598 | -0.0363 | 0.0075 | -0.0363 | 0.0037 | -0.0156 | -0.0102 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level | svc_group_level=artist | 252 | -0.0595 | 0.0111 | 0.0003 | 0.0111 | -0.0015 | -0.0057 | -0.0036 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p02 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_mid | 87 | -0.0546 | -0.0343 | -0.0026 | -0.0343 | -0.0003 | 0.0034 | -0.0018 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p02 | level_qwidth | svc_group_level=artist_medium_support_size & qwidth_band=qwidth_high | 27 | -0.0524 | -0.0363 | 0.0075 | -0.0363 | 0.0037 | -0.0143 | -0.0086 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_gap | svc_group_level=artist & gap_band=gap_010_020 | 75 | -0.0523 | 0.0485 | -0.0012 | 0.0485 | -0.0026 | -0.0130 | -0.0085 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_gap | svc_group_level=artist & gap_band=gap_010_020 | 75 | -0.0521 | 0.0485 | -0.0012 | 0.0485 | -0.0026 | -0.0130 | -0.0085 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p02 | spread_gap | pred_spread_band=spread_low_mid & gap_band=gap_003_005 | 53 | -0.0517 | -0.0302 | 0.0114 | -0.0302 | 0.0100 | -0.0043 | -0.0116 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p03 | level | svc_group_level=artist | 252 | -0.0515 | 0.0111 | 0.0006 | 0.0111 | 0.0022 | -0.0032 | -0.0063 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 66 | -0.0511 | 0.0616 | -0.0034 | 0.0616 | -0.0039 | -0.0095 | 0.0033 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_n | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 66 | -0.0511 | 0.0616 | -0.0034 | 0.0616 | -0.0039 | -0.0095 | 0.0033 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p02 | level | svc_group_level=artist | 252 | -0.0509 | 0.0111 | 0.0006 | 0.0111 | 0.0022 | -0.0022 | -0.0063 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_low | 74 | -0.0507 | 0.0504 | 0.0027 | 0.0504 | -0.0005 | -0.0086 | -0.0067 | True | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_low | 74 | -0.0506 | 0.0504 | 0.0027 | 0.0504 | -0.0005 | -0.0086 | -0.0067 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p08 | level | svc_group_level=artist | 252 | -0.0500 | 0.0111 | 0.0006 | 0.0111 | 0.0022 | -0.0032 | -0.0063 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p05 | level | svc_group_level=artist | 252 | -0.0499 | 0.0111 | 0.0006 | 0.0111 | 0.0022 | -0.0032 | -0.0063 | True | True | True |
| hcoef29_core_component_delta_s0p5_cap0p03 | spread_gap | pred_spread_band=spread_low_mid & gap_band=gap_003_005 | 53 | -0.0476 | -0.0302 | 0.0114 | -0.0302 | 0.0100 | -0.0043 | -0.0099 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p05 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_005_010 | 40 | -0.0471 | 0.0461 | 0.0086 | 0.0461 | 0.0125 | -0.0019 | -0.0126 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_005_010 | 40 | -0.0471 | 0.0461 | 0.0086 | 0.0461 | 0.0125 | -0.0019 | -0.0126 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p05 | level_qwidth | svc_group_level=artist_medium_support_size & qwidth_band=qwidth_high | 27 | -0.0469 | -0.0363 | 0.0075 | -0.0363 | 0.0037 | -0.0143 | -0.0060 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist_medium_support_size & qwidth_band=qwidth_high | 27 | -0.0469 | -0.0363 | 0.0075 | -0.0363 | 0.0037 | -0.0143 | -0.0060 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p03 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_005_010 | 40 | -0.0467 | 0.0461 | 0.0086 | 0.0461 | 0.0125 | -0.0016 | -0.0126 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_005_010 | 40 | -0.0459 | 0.0461 | 0.0076 | 0.0461 | 0.0043 | -0.0091 | -0.0114 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_low & gap_band=gap_005_010 | 40 | -0.0459 | 0.0461 | 0.0076 | 0.0461 | 0.0043 | -0.0091 | -0.0114 | False | False | False |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | spread_gap | pred_spread_band=spread_high & gap_band=gap_010_020 | 34 | -0.0456 | 0.0789 | 0.0026 | 0.0789 | 0.0041 | -0.0143 | -0.0041 | False | True | False |
| hcoef29_core_component_delta_s0p5_cap0p02 | n | svc_group_n_band=n_10_19 | 160 | -0.0452 | -0.0254 | 0.0034 | -0.0254 | 0.0027 | 0.0008 | 0.0010 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | spread_gap | pred_spread_band=spread_high & gap_band=gap_010_020 | 34 | -0.0445 | 0.0789 | 0.0026 | 0.0789 | 0.0041 | -0.0143 | -0.0041 | False | True | False |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth | qwidth_band=qwidth_high | 73 | -0.0427 | -0.0307 | 0.0101 | -0.0307 | 0.0082 | 0.0033 | 0.0035 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_gap | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 37 | -0.0425 | 0.0819 | 0.0062 | 0.0819 | 0.0030 | -0.0070 | -0.0120 | False | True | True |
| hcoef29_core_component_delta_s0p5_cap0p05 | qwidth_gap | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 37 | -0.0422 | 0.0819 | 0.0062 | 0.0819 | 0.0030 | -0.0070 | -0.0120 | False | True | True |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth | qwidth_band=qwidth_high | 73 | -0.0421 | -0.0307 | 0.0101 | -0.0307 | 0.0082 | 0.0033 | 0.0035 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p05 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_low | 74 | -0.0412 | 0.0504 | 0.0026 | 0.0504 | 0.0082 | -0.0096 | -0.0062 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p08 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_low | 74 | -0.0412 | 0.0504 | 0.0026 | 0.0504 | 0.0082 | -0.0096 | -0.0062 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p03 | level_qwidth | svc_group_level=artist & qwidth_band=qwidth_low | 74 | -0.0412 | 0.0504 | 0.0026 | 0.0504 | 0.0082 | -0.0095 | -0.0062 | False | False | False |
| hcoef29_core_component_delta_s0p5_cap0p03 | qwidth_gap | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 37 | -0.0408 | 0.0819 | 0.0062 | 0.0819 | 0.0030 | -0.0070 | -0.0120 | False | True | True |

## 5. 정책 후보 설정

| candidate | source_candidate | source_tag | objective | top_n | weight | cap | rule_count | rules | mean_directional_score | min_n | formula |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.1000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.1000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.1000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.2000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.2000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.2000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.3000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.3000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.3000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.5000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.5000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | all3_dir | 1 | 0.5000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.1000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.1000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.1000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.2000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.2000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.2000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.3000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.3000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.3000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.5000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.5000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 1 | 0.5000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.1000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.1000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.1000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.2000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.2000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.2000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.3000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.3000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.3000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.5000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.5000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_any2_dir_top3_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | any2_dir | 3 | 0.5000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0407 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.1000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.1000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.1000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.2000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.2000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.2000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.3000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.3000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.3000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.5000 | 0.0050 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.5000 | 0.0100 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 1 | 0.5000 | 0.0200 | 1 | svc_group_level=artist | -0.0509 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.1000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.1000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.1000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.2000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.2000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.2000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.3000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.3000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.3000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.5000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.5000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s06_mape_dir_top3_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | s06 | mape_dir | 3 | 0.5000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0382 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.1000 | 0.0050 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.1000 | 0.0100 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.1000 | 0.0200 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.2000 | 0.0050 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.2000 | 0.0100 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.2000 | 0.0200 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.3000 | 0.0050 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.3000 | 0.0100 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.3000 | 0.0200 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.5000 | 0.0050 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.5000 | 0.0100 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_all3_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | all3_dir | 1 | 0.5000 | 0.0200 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.1000 | 0.0050 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.1000 | 0.0100 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.1000 | 0.0200 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.2000 | 0.0050 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.2000 | 0.0100 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.2000 | 0.0200 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.3000 | 0.0050 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.3000 | 0.0100 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.3000 | 0.0200 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.5000 | 0.0050 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.5000 | 0.0100 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 1 | 0.5000 | 0.0200 | 1 | svc_group_level=artist | -0.0515 | 252 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.1000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.1000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.1000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.2000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.2000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.2000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.3000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.3000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.3000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.5000 | 0.0050 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.5000 | 0.0100 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top3_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 3 | 0.5000 | 0.0200 | 3 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 | -0.0463 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top5_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 5 | 0.1000 | 0.0050 | 5 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top5_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 5 | 0.1000 | 0.0100 | 5 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top5_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 5 | 0.1000 | 0.0200 | 5 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 37 | stable + clipped directional micro move inside validation-consensus segments |
| hcoef31_s05_any2_dir_top5_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | s05 | any2_dir | 5 | 0.2000 | 0.0050 | 5 | svc_group_level=artist \|\| qwidth_band=qwidth_low & gap_band=gap_005_010 \|\| qwidth_band=qwidth_extreme & gap_band=gap_010_020 \|\| qwidth_band=qwidth_low & svc_group_n_band=n_5_9 \|\| qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | -0.0410 | 37 | stable + clipped directional micro move inside validation-consensus segments |

## 6. 선택 후보 요약

| candidate | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | repeated_min_any2_improve_prob | repeated_min_all3_improve_prob | fixed_test_p95_guard | stress0604_p95_guard | test_mean_move_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | True | True |  |
| current_70_30 | 최소 비교 기준 | 0.1305 | 0.2110 | 0.6580 | 0.1305 | 0.2110 | 0.6580 | 0.1405 | 0.2748 | 0.8331 | 0.2779 | 0.3774 | 0.9871 | 0.0000 | 0.0000 | False | False |  |
| svc_numeric_seed_mean | component 대조군 | 0.1272 | 0.2176 | 0.6504 | 0.1272 | 0.2176 | 0.6504 | 0.1520 | 0.2942 | 0.9381 | 0.3072 | 0.4318 | 0.9998 | 0.0640 | 0.0000 | False | False |  |
| ppv8_service_proxy | component 대조군 | 0.1544 | 0.2544 | 0.8084 | 0.1544 | 0.2544 | 0.8084 | 0.1632 | 0.2816 | 0.9311 | 0.2298 | 0.3359 | 0.9273 | 0.0000 | 0.0000 | False | True |  |
| l10_seq_full_generated_bucket | component 대조군 | 0.1685 | 0.2981 | 0.8769 | 0.1685 | 0.2981 | 0.8769 | 0.1743 | 0.3265 | 0.9818 | 0.3207 | 0.4598 | 1.2569 | 0.0000 | 0.0000 | False | False |  |
| hcoef31_s06_mape_dir_top3_w0p1_cap0p005 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2729 | 0.8070 | 0.2720 | 0.3744 | 0.9834 | 0.8820 | 0.3880 | False | True | 0.0568 |
| hcoef31_s06_mape_dir_top3_w0p1_cap0p01 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2729 | 0.8070 | 0.2720 | 0.3744 | 0.9834 | 0.8820 | 0.3880 | False | True | 0.0568 |
| hcoef31_s06_mape_dir_top3_w0p1_cap0p02 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2729 | 0.8070 | 0.2720 | 0.3744 | 0.9834 | 0.8820 | 0.3880 | False | True | 0.0568 |
| hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | 보류 | 0.1248 | 0.2081 | 0.6450 | 0.1249 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8980 | 0.4100 | False | True | 0.0596 |
| hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | 보류 | 0.1248 | 0.2081 | 0.6450 | 0.1249 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8980 | 0.4100 | False | True | 0.0596 |
| hcoef31_s06_any2_dir_top3_w0p1_cap0p02 | 보류 | 0.1248 | 0.2081 | 0.6450 | 0.1249 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8980 | 0.4100 | False | True | 0.0596 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p01 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p02 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p005 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p01 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p02 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_mape_dir_top1_w0p1_cap0p005 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_mape_dir_top1_w0p1_cap0p01 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_mape_dir_top1_w0p1_cap0p02 | 보류 | 0.1260 | 0.2080 | 0.6450 | 0.1260 | 0.2080 | 0.6450 | 0.1382 | 0.2730 | 0.8066 | 0.2731 | 0.3744 | 0.9834 | 0.8720 | 0.3860 | False | True | 0.0486 |
| hcoef31_s06_mape_dir_top3_w0p2_cap0p005 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2727 | 0.8084 | 0.2705 | 0.3743 | 0.9834 | 0.9280 | 0.4940 | False | True | 0.1137 |
| hcoef31_s06_mape_dir_top3_w0p2_cap0p01 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2727 | 0.8084 | 0.2705 | 0.3743 | 0.9834 | 0.9280 | 0.4940 | False | True | 0.1137 |
| hcoef31_s06_mape_dir_top3_w0p2_cap0p02 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2727 | 0.8084 | 0.2705 | 0.3743 | 0.9834 | 0.9280 | 0.4940 | False | True | 0.1137 |
| hcoef31_s06_any2_dir_top3_w0p2_cap0p005 | 보류 | 0.1231 | 0.2079 | 0.6420 | 0.1233 | 0.2079 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3744 | 0.9834 | 0.9360 | 0.5000 | False | True | 0.1193 |
| hcoef31_s06_any2_dir_top3_w0p2_cap0p01 | 보류 | 0.1231 | 0.2079 | 0.6420 | 0.1233 | 0.2079 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3744 | 0.9834 | 0.9360 | 0.5000 | False | True | 0.1193 |
| hcoef31_s06_any2_dir_top3_w0p2_cap0p02 | 보류 | 0.1231 | 0.2079 | 0.6420 | 0.1233 | 0.2079 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3744 | 0.9834 | 0.9360 | 0.5000 | False | True | 0.1193 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p005 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p01 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p02 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p005 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p01 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p02 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s06_mape_dir_top1_w0p2_cap0p005 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s06_mape_dir_top1_w0p2_cap0p01 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s06_mape_dir_top1_w0p2_cap0p02 | 보류 | 0.1246 | 0.2079 | 0.6420 | 0.1246 | 0.2078 | 0.6420 | 0.1383 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9320 | 0.5120 | False | True | 0.0972 |
| hcoef31_s01_any2_dir_top1_w0p2_cap0p01 | 보류 | 0.1231 | 0.2082 | 0.6479 | 0.1231 | 0.2082 | 0.6479 | 0.1384 | 0.2731 | 0.8064 | 0.2728 | 0.3742 | 0.9835 | 0.4160 | 0.0240 | True | True | 0.0241 |
| hcoef31_s01_any2_dir_top1_w0p2_cap0p02 | 보류 | 0.1231 | 0.2082 | 0.6479 | 0.1231 | 0.2082 | 0.6479 | 0.1384 | 0.2731 | 0.8064 | 0.2728 | 0.3741 | 0.9835 | 0.4160 | 0.0240 | True | True | 0.0241 |
| hcoef31_s02_any2_dir_top1_w0p2_cap0p01 | 보류 | 0.1231 | 0.2082 | 0.6479 | 0.1231 | 0.2082 | 0.6479 | 0.1384 | 0.2731 | 0.8064 | 0.2728 | 0.3742 | 0.9835 | 0.4160 | 0.0240 | True | True | 0.0241 |
| hcoef31_s02_any2_dir_top1_w0p2_cap0p02 | 보류 | 0.1231 | 0.2082 | 0.6479 | 0.1231 | 0.2082 | 0.6479 | 0.1384 | 0.2731 | 0.8064 | 0.2728 | 0.3742 | 0.9835 | 0.4160 | 0.0240 | True | True | 0.0241 |
| hcoef31_s06_mape_dir_top3_w0p3_cap0p01 | 보류 | 0.1231 | 0.2077 | 0.6390 | 0.1234 | 0.2077 | 0.6390 | 0.1388 | 0.2726 | 0.8097 | 0.2690 | 0.3743 | 0.9834 | 0.9640 | 0.6240 | False | True | 0.1705 |
| hcoef31_s06_mape_dir_top3_w0p3_cap0p02 | 보류 | 0.1231 | 0.2077 | 0.6390 | 0.1234 | 0.2077 | 0.6390 | 0.1388 | 0.2726 | 0.8097 | 0.2690 | 0.3743 | 0.9834 | 0.9640 | 0.6240 | False | True | 0.1705 |
| hcoef31_s03_mape_dir_top3_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2726 | 0.8091 | 0.2698 | 0.3744 | 0.9834 | 0.9580 | 0.5900 | False | True | 0.2842 |
| hcoef31_s04_mape_dir_top3_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2726 | 0.8091 | 0.2698 | 0.3744 | 0.9834 | 0.9580 | 0.5900 | False | True | 0.2842 |
| hcoef31_s05_mape_dir_top3_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2726 | 0.8091 | 0.2698 | 0.3744 | 0.9834 | 0.9580 | 0.5900 | False | True | 0.2842 |
| hcoef31_s06_mape_dir_top3_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2726 | 0.8091 | 0.2698 | 0.3744 | 0.9834 | 0.9580 | 0.5900 | False | True | 0.2842 |
| hcoef31_s03_mape_dir_top3_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2727 | 0.8091 | 0.2698 | 0.3744 | 0.9834 | 0.9580 | 0.5800 | False | True | 0.1705 |
| hcoef31_s04_mape_dir_top3_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2727 | 0.8091 | 0.2698 | 0.3744 | 0.9834 | 0.9580 | 0.5800 | False | True | 0.1705 |
| hcoef31_s05_mape_dir_top3_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2727 | 0.8091 | 0.2698 | 0.3744 | 0.9834 | 0.9580 | 0.5800 | False | True | 0.1705 |
| hcoef31_s06_mape_dir_top3_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2727 | 0.8091 | 0.2698 | 0.3744 | 0.9834 | 0.9580 | 0.5800 | False | True | 0.1705 |
| hcoef31_s03_mape_dir_top3_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2727 | 0.8085 | 0.2698 | 0.3743 | 0.9834 | 0.9200 | 0.4860 | False | True | 0.1137 |
| hcoef31_s04_mape_dir_top3_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2727 | 0.8085 | 0.2698 | 0.3743 | 0.9834 | 0.9200 | 0.4860 | False | True | 0.1137 |
| hcoef31_s05_mape_dir_top3_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2727 | 0.8085 | 0.2698 | 0.3743 | 0.9834 | 0.9200 | 0.4860 | False | True | 0.1137 |
| hcoef31_s03_mape_dir_top3_w0p1_cap0p005 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2705 | 0.3743 | 0.9834 | 0.9400 | 0.5240 | False | True | 0.0568 |
| hcoef31_s03_mape_dir_top3_w0p1_cap0p01 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2705 | 0.3743 | 0.9834 | 0.9400 | 0.5240 | False | True | 0.0568 |
| hcoef31_s03_mape_dir_top3_w0p1_cap0p02 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2705 | 0.3743 | 0.9834 | 0.9400 | 0.5240 | False | True | 0.0568 |
| hcoef31_s04_mape_dir_top3_w0p1_cap0p005 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2705 | 0.3743 | 0.9834 | 0.9400 | 0.5240 | False | True | 0.0568 |
| hcoef31_s04_mape_dir_top3_w0p1_cap0p01 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2705 | 0.3743 | 0.9834 | 0.9400 | 0.5240 | False | True | 0.0568 |
| hcoef31_s04_mape_dir_top3_w0p1_cap0p02 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2705 | 0.3743 | 0.9834 | 0.9400 | 0.5240 | False | True | 0.0568 |
| hcoef31_s05_mape_dir_top3_w0p1_cap0p005 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2712 | 0.3743 | 0.9834 | 0.9060 | 0.4420 | False | True | 0.0568 |
| hcoef31_s05_mape_dir_top3_w0p1_cap0p01 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2712 | 0.3743 | 0.9834 | 0.9060 | 0.4420 | False | True | 0.0568 |
| hcoef31_s05_mape_dir_top3_w0p1_cap0p02 | 보류 | 0.1260 | 0.2080 | 0.6436 | 0.1259 | 0.2080 | 0.6449 | 0.1388 | 0.2728 | 0.8071 | 0.2712 | 0.3743 | 0.9834 | 0.9060 | 0.4420 | False | True | 0.0568 |
| hcoef31_s03_all3_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s03_any2_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s03_mape_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s04_all3_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s04_any2_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s04_mape_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s05_all3_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s05_any2_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s05_mape_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s06_any2_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s06_mape_dir_top1_w0p5_cap0p005 | 보류 | 0.1238 | 0.2077 | 0.6404 | 0.1238 | 0.2077 | 0.6404 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3746 | 0.9834 | 0.9600 | 0.6440 | False | True | 0.2430 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p01 | 보류 | 0.1231 | 0.2077 | 0.6390 | 0.1232 | 0.2077 | 0.6390 | 0.1388 | 0.2729 | 0.8072 | 0.2731 | 0.3745 | 0.9834 | 0.9680 | 0.6800 | False | True | 0.1458 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p02 | 보류 | 0.1231 | 0.2077 | 0.6390 | 0.1232 | 0.2077 | 0.6390 | 0.1388 | 0.2729 | 0.8072 | 0.2731 | 0.3745 | 0.9834 | 0.9680 | 0.6800 | False | True | 0.1458 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p01 | 보류 | 0.1231 | 0.2077 | 0.6390 | 0.1232 | 0.2077 | 0.6390 | 0.1388 | 0.2729 | 0.8072 | 0.2731 | 0.3745 | 0.9834 | 0.9680 | 0.6800 | False | True | 0.1458 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p02 | 보류 | 0.1231 | 0.2077 | 0.6390 | 0.1232 | 0.2077 | 0.6390 | 0.1388 | 0.2729 | 0.8072 | 0.2731 | 0.3745 | 0.9834 | 0.9680 | 0.6800 | False | True | 0.1458 |
| hcoef31_s06_mape_dir_top1_w0p3_cap0p01 | 보류 | 0.1231 | 0.2077 | 0.6390 | 0.1232 | 0.2077 | 0.6390 | 0.1388 | 0.2729 | 0.8072 | 0.2731 | 0.3745 | 0.9834 | 0.9680 | 0.6800 | False | True | 0.1458 |
| hcoef31_s06_mape_dir_top1_w0p3_cap0p02 | 보류 | 0.1231 | 0.2077 | 0.6390 | 0.1232 | 0.2077 | 0.6390 | 0.1388 | 0.2729 | 0.8072 | 0.2731 | 0.3745 | 0.9834 | 0.9680 | 0.6800 | False | True | 0.1458 |
| hcoef31_s03_all3_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s03_any2_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s03_mape_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s04_all3_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s04_any2_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s04_mape_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s05_all3_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s05_any2_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s05_mape_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s06_mape_dir_top1_w0p3_cap0p005 | 보류 | 0.1238 | 0.2078 | 0.6405 | 0.1238 | 0.2077 | 0.6405 | 0.1388 | 0.2729 | 0.8070 | 0.2731 | 0.3745 | 0.9834 | 0.9600 | 0.6460 | False | True | 0.1458 |
| hcoef31_s03_all3_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |
| hcoef31_s03_any2_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |
| hcoef31_s03_mape_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |
| hcoef31_s04_all3_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |
| hcoef31_s04_any2_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |
| hcoef31_s04_mape_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |
| hcoef31_s05_all3_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |
| hcoef31_s05_any2_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |
| hcoef31_s05_mape_dir_top1_w0p2_cap0p005 | 보류 | 0.1241 | 0.2079 | 0.6405 | 0.1238 | 0.2078 | 0.6419 | 0.1388 | 0.2729 | 0.8069 | 0.2731 | 0.3745 | 0.9834 | 0.9260 | 0.5120 | False | True | 0.0972 |

## 7. Scope별 metrics

| scope | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mean_move_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |  |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p02 | 0.2659 | 0.3742 | 0.9834 | 1.3048 | -0.0072 | -0.0002 | -0.0000 | 0.4086 |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p03 | 0.2641 | 0.3741 | 0.9833 | 1.3032 | -0.0090 | -0.0003 | -0.0001 | 0.4653 |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p05 | 0.2641 | 0.3740 | 0.9833 | 1.3012 | -0.0090 | -0.0004 | -0.0001 | 0.4952 |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p08 | 0.2641 | 0.3742 | 0.9833 | 1.2996 | -0.0090 | -0.0002 | -0.0001 | 0.4993 |
| 0604_stress | hcoef29_risk_guarded_component_s0p5_cap0p05 | 0.2751 | 0.3690 | 0.9466 | 1.3208 | 0.0020 | -0.0053 | -0.0369 | 0.2932 |
| 0604_stress | hcoef29_risk_guarded_component_s0p5_cap0p08 | 0.2789 | 0.3678 | 0.9446 | 1.3281 | 0.0058 | -0.0065 | -0.0389 | 0.3990 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p1_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0064 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p1_cap0p01 | 0.2731 | 0.3742 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0064 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p1_cap0p02 | 0.2731 | 0.3742 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0064 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p2_cap0p005 | 0.2728 | 0.3743 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0128 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p2_cap0p01 | 0.2728 | 0.3742 | 0.9835 | 1.3077 | -0.0002 | -0.0002 | 0.0000 | 0.0128 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p2_cap0p02 | 0.2728 | 0.3741 | 0.9835 | 1.3077 | -0.0002 | -0.0002 | 0.0000 | 0.0128 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p3_cap0p005 | 0.2728 | 0.3743 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0192 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p3_cap0p01 | 0.2728 | 0.3742 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0192 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p3_cap0p02 | 0.2728 | 0.3741 | 0.9835 | 1.3077 | -0.0002 | -0.0003 | 0.0000 | 0.0192 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p5_cap0p005 | 0.2728 | 0.3743 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0320 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p5_cap0p01 | 0.2728 | 0.3743 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0320 |
| 0604_stress | hcoef31_s01_any2_dir_top1_w0p5_cap0p02 | 0.2731 | 0.3741 | 0.9835 | 1.3077 | 0.0000 | -0.0002 | 0.0000 | 0.0320 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p1_cap0p005 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0064 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p1_cap0p01 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0064 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p1_cap0p02 | 0.2731 | 0.3743 | 0.9835 | 1.3078 | 0.0000 | -0.0001 | 0.0000 | 0.0064 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p2_cap0p005 | 0.2728 | 0.3743 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0128 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p2_cap0p01 | 0.2728 | 0.3742 | 0.9835 | 1.3077 | -0.0002 | -0.0002 | 0.0000 | 0.0128 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p2_cap0p02 | 0.2728 | 0.3742 | 0.9835 | 1.3077 | -0.0002 | -0.0002 | 0.0000 | 0.0128 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p3_cap0p005 | 0.2728 | 0.3743 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0192 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p3_cap0p01 | 0.2728 | 0.3742 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0192 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p3_cap0p02 | 0.2728 | 0.3742 | 0.9835 | 1.3077 | -0.0002 | -0.0002 | 0.0000 | 0.0192 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p5_cap0p005 | 0.2728 | 0.3743 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0320 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p5_cap0p01 | 0.2728 | 0.3743 | 0.9835 | 1.3078 | -0.0002 | -0.0001 | 0.0000 | 0.0320 |
| 0604_stress | hcoef31_s02_any2_dir_top1_w0p5_cap0p02 | 0.2731 | 0.3741 | 0.9835 | 1.3077 | 0.0000 | -0.0002 | 0.0000 | 0.0320 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p1_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p1_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3071 | 0.0000 | 0.0001 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p1_cap0p02 | 0.2731 | 0.3744 | 0.9834 | 1.3071 | 0.0000 | 0.0001 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p2_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.0994 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p2_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3068 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p2_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3065 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p3_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.1491 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p3_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3067 | 0.0000 | 0.0001 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p3_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3060 | 0.0000 | 0.0002 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p5_cap0p005 | 0.2731 | 0.3746 | 0.9834 | 1.3072 | 0.0000 | 0.0002 | -0.0000 | 0.2485 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p5_cap0p01 | 0.2731 | 0.3746 | 0.9834 | 1.3066 | 0.0000 | 0.0002 | -0.0001 | 0.2485 |
| 0604_stress | hcoef31_s03_all3_dir_top1_w0p5_cap0p02 | 0.2713 | 0.3746 | 0.9833 | 1.3057 | -0.0018 | 0.0002 | -0.0002 | 0.2485 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p1_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p1_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3071 | 0.0000 | 0.0001 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p1_cap0p02 | 0.2731 | 0.3744 | 0.9834 | 1.3071 | 0.0000 | 0.0001 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p2_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.0994 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p2_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3068 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p2_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3065 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p3_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.1491 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p3_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3067 | 0.0000 | 0.0001 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p3_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3060 | 0.0000 | 0.0002 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p5_cap0p005 | 0.2731 | 0.3746 | 0.9834 | 1.3072 | 0.0000 | 0.0002 | -0.0000 | 0.2485 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p5_cap0p01 | 0.2731 | 0.3746 | 0.9834 | 1.3066 | 0.0000 | 0.0002 | -0.0001 | 0.2485 |
| 0604_stress | hcoef31_s03_any2_dir_top1_w0p5_cap0p02 | 0.2713 | 0.3746 | 0.9833 | 1.3057 | -0.0018 | 0.0002 | -0.0002 | 0.2485 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p1_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | -0.0000 | -0.0000 | 0.0545 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p1_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3071 | 0.0000 | -0.0000 | -0.0000 | 0.0545 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p1_cap0p02 | 0.2731 | 0.3744 | 0.9834 | 1.3071 | 0.0000 | -0.0000 | -0.0000 | 0.0545 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p2_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3072 | 0.0000 | -0.0000 | -0.0000 | 0.1090 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p2_cap0p01 | 0.2731 | 0.3743 | 0.9834 | 1.3068 | 0.0000 | -0.0000 | -0.0001 | 0.1090 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p2_cap0p02 | 0.2731 | 0.3744 | 0.9834 | 1.3064 | 0.0000 | -0.0000 | -0.0001 | 0.1090 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p3_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3072 | 0.0000 | 0.0000 | -0.0000 | 0.1636 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p3_cap0p01 | 0.2731 | 0.3743 | 0.9834 | 1.3066 | 0.0000 | -0.0000 | -0.0001 | 0.1636 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p3_cap0p02 | 0.2731 | 0.3743 | 0.9834 | 1.3060 | 0.0000 | -0.0000 | -0.0001 | 0.1636 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p5_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.2726 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p5_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3066 | 0.0000 | 0.0000 | -0.0001 | 0.2726 |
| 0604_stress | hcoef31_s03_any2_dir_top3_w0p5_cap0p02 | 0.2713 | 0.3743 | 0.9833 | 1.3056 | -0.0018 | -0.0001 | -0.0002 | 0.2726 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p1_cap0p005 | 0.2705 | 0.3743 | 0.9834 | 1.3071 | -0.0025 | -0.0001 | -0.0000 | 0.0647 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p1_cap0p01 | 0.2705 | 0.3743 | 0.9834 | 1.3069 | -0.0025 | -0.0001 | -0.0000 | 0.0647 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p1_cap0p02 | 0.2705 | 0.3743 | 0.9834 | 1.3069 | -0.0025 | -0.0001 | -0.0000 | 0.0647 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p2_cap0p005 | 0.2698 | 0.3743 | 0.9834 | 1.3070 | -0.0033 | -0.0001 | -0.0000 | 0.1293 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p2_cap0p01 | 0.2689 | 0.3742 | 0.9834 | 1.3064 | -0.0042 | -0.0001 | -0.0001 | 0.1293 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p2_cap0p02 | 0.2689 | 0.3743 | 0.9834 | 1.3061 | -0.0042 | -0.0001 | -0.0001 | 0.1293 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p3_cap0p005 | 0.2698 | 0.3743 | 0.9834 | 1.3070 | -0.0033 | -0.0000 | -0.0000 | 0.1940 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p3_cap0p01 | 0.2683 | 0.3742 | 0.9834 | 1.3063 | -0.0048 | -0.0001 | -0.0001 | 0.1940 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p3_cap0p02 | 0.2683 | 0.3742 | 0.9834 | 1.3055 | -0.0048 | -0.0002 | -0.0001 | 0.1940 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p5_cap0p005 | 0.2698 | 0.3744 | 0.9834 | 1.3070 | -0.0033 | 0.0000 | -0.0000 | 0.3233 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p5_cap0p01 | 0.2671 | 0.3743 | 0.9834 | 1.3062 | -0.0060 | -0.0001 | -0.0001 | 0.3233 |
| 0604_stress | hcoef31_s03_any2_dir_top5_w0p5_cap0p02 | 0.2675 | 0.3741 | 0.9833 | 1.3049 | -0.0055 | -0.0002 | -0.0002 | 0.3233 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p1_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p1_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3071 | 0.0000 | 0.0001 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p1_cap0p02 | 0.2731 | 0.3744 | 0.9834 | 1.3071 | 0.0000 | 0.0001 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p2_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.0994 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p2_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3068 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p2_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3065 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p3_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.1491 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p3_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3067 | 0.0000 | 0.0001 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p3_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3060 | 0.0000 | 0.0002 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p5_cap0p005 | 0.2731 | 0.3746 | 0.9834 | 1.3072 | 0.0000 | 0.0002 | -0.0000 | 0.2485 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p5_cap0p01 | 0.2731 | 0.3746 | 0.9834 | 1.3066 | 0.0000 | 0.0002 | -0.0001 | 0.2485 |
| 0604_stress | hcoef31_s03_mape_dir_top1_w0p5_cap0p02 | 0.2713 | 0.3746 | 0.9833 | 1.3057 | -0.0018 | 0.0002 | -0.0002 | 0.2485 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p1_cap0p005 | 0.2705 | 0.3743 | 0.9834 | 1.3071 | -0.0025 | -0.0001 | -0.0000 | 0.0606 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p1_cap0p01 | 0.2705 | 0.3743 | 0.9834 | 1.3069 | -0.0025 | -0.0000 | -0.0000 | 0.0606 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p1_cap0p02 | 0.2705 | 0.3743 | 0.9834 | 1.3069 | -0.0025 | -0.0000 | -0.0000 | 0.0606 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p2_cap0p005 | 0.2698 | 0.3743 | 0.9834 | 1.3070 | -0.0033 | -0.0000 | -0.0000 | 0.1211 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p2_cap0p01 | 0.2689 | 0.3743 | 0.9834 | 1.3064 | -0.0042 | -0.0001 | -0.0001 | 0.1211 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p2_cap0p02 | 0.2689 | 0.3743 | 0.9834 | 1.3061 | -0.0042 | -0.0001 | -0.0001 | 0.1211 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p3_cap0p005 | 0.2698 | 0.3744 | 0.9834 | 1.3070 | -0.0033 | 0.0000 | -0.0000 | 0.1817 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p3_cap0p01 | 0.2683 | 0.3742 | 0.9834 | 1.3063 | -0.0048 | -0.0001 | -0.0001 | 0.1817 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p3_cap0p02 | 0.2683 | 0.3742 | 0.9834 | 1.3055 | -0.0048 | -0.0001 | -0.0001 | 0.1817 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p5_cap0p005 | 0.2698 | 0.3744 | 0.9834 | 1.3070 | -0.0033 | 0.0000 | -0.0000 | 0.3028 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p5_cap0p01 | 0.2671 | 0.3743 | 0.9834 | 1.3062 | -0.0060 | -0.0000 | -0.0001 | 0.3028 |
| 0604_stress | hcoef31_s03_mape_dir_top3_w0p5_cap0p02 | 0.2675 | 0.3742 | 0.9833 | 1.3049 | -0.0055 | -0.0002 | -0.0002 | 0.3028 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p1_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p1_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p1_cap0p02 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p2_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.0994 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p2_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3068 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p2_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3068 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p3_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.1491 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p3_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3067 | 0.0000 | 0.0001 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p3_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3063 | 0.0000 | 0.0001 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p5_cap0p005 | 0.2731 | 0.3746 | 0.9834 | 1.3072 | 0.0000 | 0.0002 | -0.0000 | 0.2485 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p5_cap0p01 | 0.2731 | 0.3746 | 0.9834 | 1.3066 | 0.0000 | 0.0002 | -0.0001 | 0.2485 |
| 0604_stress | hcoef31_s04_all3_dir_top1_w0p5_cap0p02 | 0.2713 | 0.3746 | 0.9833 | 1.3057 | -0.0018 | 0.0002 | -0.0002 | 0.2485 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p1_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p1_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p1_cap0p02 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | 0.0000 | -0.0000 | 0.0497 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p2_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.0994 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p2_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3068 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p2_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3068 | 0.0000 | 0.0001 | -0.0001 | 0.0994 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p3_cap0p005 | 0.2731 | 0.3745 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.1491 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p3_cap0p01 | 0.2731 | 0.3745 | 0.9834 | 1.3067 | 0.0000 | 0.0001 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p3_cap0p02 | 0.2731 | 0.3745 | 0.9834 | 1.3063 | 0.0000 | 0.0001 | -0.0001 | 0.1491 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p5_cap0p005 | 0.2731 | 0.3746 | 0.9834 | 1.3072 | 0.0000 | 0.0002 | -0.0000 | 0.2485 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p5_cap0p01 | 0.2731 | 0.3746 | 0.9834 | 1.3066 | 0.0000 | 0.0002 | -0.0001 | 0.2485 |
| 0604_stress | hcoef31_s04_any2_dir_top1_w0p5_cap0p02 | 0.2713 | 0.3746 | 0.9833 | 1.3057 | -0.0018 | 0.0002 | -0.0002 | 0.2485 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p1_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | -0.0000 | -0.0000 | 0.0545 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p1_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | -0.0000 | -0.0000 | 0.0545 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p1_cap0p02 | 0.2731 | 0.3744 | 0.9834 | 1.3073 | 0.0000 | -0.0000 | -0.0000 | 0.0545 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p2_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3072 | 0.0000 | -0.0000 | -0.0000 | 0.1090 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p2_cap0p01 | 0.2731 | 0.3743 | 0.9834 | 1.3068 | 0.0000 | -0.0000 | -0.0001 | 0.1090 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p2_cap0p02 | 0.2731 | 0.3743 | 0.9834 | 1.3068 | 0.0000 | -0.0000 | -0.0001 | 0.1090 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p3_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3072 | 0.0000 | 0.0000 | -0.0000 | 0.1636 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p3_cap0p01 | 0.2731 | 0.3743 | 0.9834 | 1.3066 | 0.0000 | -0.0000 | -0.0001 | 0.1636 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p3_cap0p02 | 0.2731 | 0.3743 | 0.9834 | 1.3062 | 0.0000 | -0.0000 | -0.0001 | 0.1636 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p5_cap0p005 | 0.2731 | 0.3744 | 0.9834 | 1.3072 | 0.0000 | 0.0001 | -0.0000 | 0.2726 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p5_cap0p01 | 0.2731 | 0.3744 | 0.9834 | 1.3066 | 0.0000 | 0.0000 | -0.0001 | 0.2726 |
| 0604_stress | hcoef31_s04_any2_dir_top3_w0p5_cap0p02 | 0.2713 | 0.3743 | 0.9833 | 1.3056 | -0.0018 | -0.0001 | -0.0002 | 0.2726 |
| 0604_stress | hcoef31_s04_any2_dir_top5_w0p1_cap0p005 | 0.2705 | 0.3743 | 0.9834 | 1.3071 | -0.0025 | -0.0001 | -0.0000 | 0.0647 |

## 8. 반복 split/artist holdout 요약

| source_scope | validation_scheme | candidate | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | any2_improve_prob | all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_artist | row_subsample_80pct | hcoef31_s06_any2_dir_top3_w0p5_cap0p01 | -0.0023 | -0.0008 | -0.0048 | 0.9660 | 1.0000 | 0.9540 | 1.0000 | 0.9200 |
| validation_oof_artist | row_subsample_80pct | hcoef31_s06_any2_dir_top3_w0p5_cap0p02 | -0.0023 | -0.0008 | -0.0048 | 0.9660 | 1.0000 | 0.9540 | 1.0000 | 0.9200 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_any2_dir_top3_w0p5_cap0p01 | -0.0020 | -0.0006 | -0.0037 | 0.9640 | 1.0000 | 0.9540 | 1.0000 | 0.9180 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_any2_dir_top3_w0p5_cap0p02 | -0.0020 | -0.0006 | -0.0037 | 0.9640 | 1.0000 | 0.9540 | 1.0000 | 0.9180 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s06_any2_dir_top3_w0p5_cap0p01 | -0.0022 | -0.0008 | -0.0046 | 0.9680 | 1.0000 | 0.9460 | 1.0000 | 0.9140 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s06_any2_dir_top3_w0p5_cap0p02 | -0.0022 | -0.0008 | -0.0046 | 0.9680 | 1.0000 | 0.9460 | 1.0000 | 0.9140 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s05_any2_dir_top5_w0p5_cap0p02 | -0.0022 | -0.0008 | -0.0053 | 0.9620 | 1.0000 | 0.9500 | 1.0000 | 0.9120 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s05_any2_dir_top3_w0p5_cap0p01 | -0.0020 | -0.0010 | -0.0048 | 0.9580 | 1.0000 | 0.9520 | 1.0000 | 0.9100 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s04_any2_dir_top3_w0p5_cap0p01 | -0.0020 | -0.0010 | -0.0048 | 0.9580 | 1.0000 | 0.9520 | 1.0000 | 0.9100 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s03_any2_dir_top3_w0p5_cap0p01 | -0.0020 | -0.0010 | -0.0048 | 0.9580 | 1.0000 | 0.9520 | 1.0000 | 0.9100 |
| validation_oof_row | row_subsample_80pct | hcoef31_s05_any2_dir_top3_w0p5_cap0p01 | -0.0016 | -0.0008 | -0.0058 | 0.9040 | 1.0000 | 0.9920 | 1.0000 | 0.8960 |
| validation_oof_row | row_subsample_80pct | hcoef31_s04_any2_dir_top3_w0p5_cap0p01 | -0.0016 | -0.0008 | -0.0058 | 0.9040 | 1.0000 | 0.9920 | 1.0000 | 0.8960 |
| validation_oof_row | row_subsample_80pct | hcoef31_s03_any2_dir_top3_w0p5_cap0p01 | -0.0016 | -0.0008 | -0.0058 | 0.9040 | 1.0000 | 0.9920 | 1.0000 | 0.8960 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_any2_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_any2_dir_top1_w0p5_cap0p02 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_mape_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_mape_dir_top1_w0p5_cap0p02 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s05_all3_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s05_any2_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s05_mape_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s04_all3_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s04_any2_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s04_mape_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s03_all3_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s03_any2_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s03_mape_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0058 | 0.9020 | 1.0000 | 0.9920 | 1.0000 | 0.8940 |
| validation_oof_row | row_subsample_80pct | hcoef31_s05_any2_dir_top5_w0p5_cap0p01 | -0.0018 | -0.0006 | -0.0037 | 0.9160 | 1.0000 | 0.9540 | 1.0000 | 0.8700 |
| validation_oof_row | row_subsample_80pct | hcoef31_s04_any2_dir_top5_w0p5_cap0p01 | -0.0018 | -0.0006 | -0.0037 | 0.9160 | 1.0000 | 0.9540 | 1.0000 | 0.8700 |
| validation_oof_row | row_subsample_80pct | hcoef31_s03_any2_dir_top5_w0p5_cap0p01 | -0.0018 | -0.0006 | -0.0037 | 0.9160 | 1.0000 | 0.9540 | 1.0000 | 0.8700 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s06_any2_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s06_any2_dir_top1_w0p5_cap0p02 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s06_mape_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s06_mape_dir_top1_w0p5_cap0p02 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s05_all3_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s05_any2_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s05_mape_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s04_all3_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s04_any2_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s04_mape_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s03_all3_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s03_any2_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s03_mape_dir_top1_w0p5_cap0p01 | -0.0014 | -0.0009 | -0.0048 | 0.9140 | 1.0000 | 0.9520 | 1.0000 | 0.8660 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_any2_dir_top3_w0p3_cap0p01 | -0.0017 | -0.0004 | -0.0024 | 0.9000 | 1.0000 | 0.9100 | 1.0000 | 0.8100 |
| validation_oof_row | row_subsample_80pct | hcoef31_s06_any2_dir_top3_w0p3_cap0p02 | -0.0017 | -0.0004 | -0.0024 | 0.9000 | 1.0000 | 0.9100 | 1.0000 | 0.8100 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s05_any2_dir_top3_w0p5_cap0p01 | -0.0017 | -0.0008 | -0.0056 | 0.9280 | 1.0000 | 0.9840 | 0.9980 | 0.9140 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s04_any2_dir_top3_w0p5_cap0p01 | -0.0017 | -0.0008 | -0.0056 | 0.9280 | 1.0000 | 0.9840 | 0.9980 | 0.9140 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s03_any2_dir_top3_w0p5_cap0p01 | -0.0017 | -0.0008 | -0.0056 | 0.9280 | 1.0000 | 0.9840 | 0.9980 | 0.9140 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s06_any2_dir_top3_w0p5_cap0p01 | -0.0019 | -0.0006 | -0.0042 | 0.9500 | 1.0000 | 0.9540 | 0.9980 | 0.9060 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s06_any2_dir_top3_w0p5_cap0p02 | -0.0019 | -0.0006 | -0.0042 | 0.9500 | 1.0000 | 0.9540 | 0.9980 | 0.9060 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s06_any2_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s06_any2_dir_top1_w0p5_cap0p02 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s06_mape_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s06_mape_dir_top1_w0p5_cap0p02 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s05_all3_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s05_any2_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s05_mape_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s04_all3_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s04_any2_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s04_mape_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s03_all3_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s03_any2_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s03_mape_dir_top1_w0p5_cap0p01 | -0.0015 | -0.0007 | -0.0056 | 0.9160 | 1.0000 | 0.9840 | 0.9980 | 0.9020 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s05_any2_dir_top5_w0p5_cap0p01 | -0.0019 | -0.0006 | -0.0042 | 0.9420 | 1.0000 | 0.9540 | 0.9980 | 0.8980 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s04_any2_dir_top5_w0p5_cap0p01 | -0.0019 | -0.0006 | -0.0042 | 0.9420 | 1.0000 | 0.9540 | 0.9980 | 0.8980 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s03_any2_dir_top5_w0p5_cap0p01 | -0.0019 | -0.0006 | -0.0042 | 0.9420 | 1.0000 | 0.9540 | 0.9980 | 0.8980 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s04_any2_dir_top5_w0p5_cap0p02 | -0.0021 | -0.0007 | -0.0053 | 0.9440 | 1.0000 | 0.9500 | 0.9980 | 0.8960 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s03_any2_dir_top5_w0p5_cap0p02 | -0.0021 | -0.0007 | -0.0053 | 0.9440 | 1.0000 | 0.9500 | 0.9980 | 0.8960 |
| validation_oof_artist | row_subsample_80pct | hcoef31_s05_any2_dir_top5_w0p5_cap0p01 | -0.0021 | -0.0008 | -0.0048 | 0.9280 | 1.0000 | 0.9540 | 0.9980 | 0.8840 |
| validation_oof_artist | row_subsample_80pct | hcoef31_s04_any2_dir_top5_w0p5_cap0p01 | -0.0021 | -0.0008 | -0.0048 | 0.9280 | 1.0000 | 0.9540 | 0.9980 | 0.8840 |
| validation_oof_artist | row_subsample_80pct | hcoef31_s03_any2_dir_top5_w0p5_cap0p01 | -0.0021 | -0.0008 | -0.0048 | 0.9280 | 1.0000 | 0.9540 | 0.9980 | 0.8840 |
| validation_oof_artist | artist_holdout_80pct | hcoef31_s05_any2_dir_top3_w0p5_cap0p02 | -0.0018 | -0.0010 | -0.0054 | 0.9300 | 1.0000 | 0.9520 | 0.9980 | 0.8840 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s05_mape_dir_top3_w0p5_cap0p02 | -0.0015 | -0.0008 | -0.0070 | 0.8820 | 1.0000 | 0.9840 | 0.9980 | 0.8680 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s04_mape_dir_top3_w0p5_cap0p02 | -0.0017 | -0.0008 | -0.0072 | 0.8800 | 1.0000 | 0.9840 | 0.9980 | 0.8660 |
| validation_oof_row | artist_holdout_80pct | hcoef31_s03_mape_dir_top3_w0p5_cap0p02 | -0.0017 | -0.0008 | -0.0072 | 0.8800 | 1.0000 | 0.9840 | 0.9980 | 0.8660 |

## 9. 계수/구간 해석

| candidate | source_candidate | feature | coefficient | direction | interpretation |
| --- | --- | --- | --- | --- | --- |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p1_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p2_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p3_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_all3_dir_top1_w0p5_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p1_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p02 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p2_cap0p02 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p005 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p005 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p02 | svc_group_level=artist | 0.0509 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p03 | svc_group_level=artist | 0.0515 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p05 | svc_group_level=artist | 0.0499 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p01 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |
| hcoef31_s06_any2_dir_top1_w0p3_cap0p01 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 |

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
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4961 | 1.0854 | 0.9327 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1217 | 0.1020 | -0.0465 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5505 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1761 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | service_confidence_tier | high | 22 | 0.5810 | 0.5579 | 1.0347 | 0.8118 | 0.3636 | 0.4545 | 4 | 4 | 0.3079 | 0.1835 | 0.0512 | 0.1324 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5030 | 1.0000 | 1.7329 | 0.3196 | 0.5388 | 19 | 141 | 0.1673 | 0.1286 | 0.0165 | 0.2975 | 0.4612 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5049 | 0.9999 | 1.7948 | 0.3159 | 0.5622 | 17 | 126 | 0.1613 | 0.1305 | 0.0165 | 0.2788 | 0.4378 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | qwidth_band | qwidth_extreme | 301 | 0.3779 | 0.4380 | 0.9960 | 1.9670 | 0.4053 | 0.6312 | 7 | 99 | 0.1048 | 0.0636 | 0.0126 | 0.3514 | 0.3688 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | qwidth_band | qwidth_high | 185 | 0.2339 | 0.3758 | 0.9867 | 0.9909 | 0.5514 | 0.7297 | 6 | 27 | -0.0391 | 0.0014 | 0.0033 | 0.0731 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_n_band | n_5_9 | 435 | 0.2396 | 0.3309 | 0.9867 | 1.6304 | 0.5678 | 0.7655 | 9 | 62 | -0.0335 | -0.0435 | 0.0033 | 0.0635 | 0.2345 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_level | artist | 412 | 0.3186 | 0.3767 | 0.9867 | 1.5783 | 0.4879 | 0.7451 | 13 | 60 | 0.0455 | 0.0023 | 0.0033 | 0.0859 | 0.2549 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | service_confidence_tier | low | 499 | 0.2654 | 0.3524 | 0.9719 | 1.5790 | 0.5271 | 0.7355 | 9 | 89 | -0.0077 | -0.0220 | -0.0115 | 0.0923 | 0.2645 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | service_confidence_tier | medium | 308 | 0.2647 | 0.3970 | 0.9707 | 0.7177 | 0.5130 | 0.6916 | 13 | 58 | -0.0084 | 0.0226 | -0.0127 | 0.0252 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | gap_band | gap_005_010 | 125 | 0.1496 | 0.2513 | 0.9530 | 0.7557 | 0.7680 | 0.9040 | 5 | 3 | -0.1235 | -0.1231 | -0.0304 | 0.0403 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_n_band | n_20_49 | 90 | 0.2007 | 0.3407 | 0.9166 | 0.6257 | 0.5889 | 0.7556 | 3 | 13 | -0.0723 | -0.0338 | -0.0669 | 0.0512 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | qwidth_band | qwidth_mid | 242 | 0.2395 | 0.3385 | 0.8841 | 0.4711 | 0.5702 | 0.7521 | 11 | 22 | -0.0336 | -0.0359 | -0.0993 | 0.0059 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2995 | -0.1045 | 1.3500 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | gap_band | gap_010_020 | 128 | 0.2245 | 0.3394 | 0.8740 | 0.5173 | 0.5625 | 0.6953 | 3 | 16 | -0.0485 | -0.0350 | -0.1094 | -0.0465 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_n_band | n_10_19 | 199 | 0.2884 | 0.3919 | 0.8640 | 0.7511 | 0.5075 | 0.7136 | 5 | 34 | 0.0153 | 0.0175 | -0.1194 | 0.0272 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_level | artist_size | 224 | 0.1911 | 0.3480 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0820 | -0.0264 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2905 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | qwidth_band | qwidth_low | 101 | 0.1774 | 0.2684 | 0.8046 | 0.4145 | 0.6634 | 0.8218 | 2 | 3 | -0.0957 | -0.1060 | -0.1788 | 0.0055 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | pred_spread_band | spread_high | 124 | 0.2092 | 0.2772 | 0.7965 | 0.7723 | 0.6210 | 0.8952 | 3 | 3 | -0.0639 | -0.0973 | -0.1869 | -0.0465 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2242 | 0.7707 | 0.7745 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1502 | -0.2128 | -0.0036 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | pred_spread_band | spread_low_mid | 267 | 0.1175 | 0.2086 | 0.6586 | 0.3239 | 0.7940 | 0.9101 | 4 | 7 | -0.1556 | -0.1658 | -0.3249 | 0.0131 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | gap_band | gap_000_003 | 119 | 0.1031 | 0.1886 | 0.5299 | 0.3146 | 0.7983 | 0.9244 | 1 | 5 | -0.1699 | -0.1858 | -0.4536 | 0.0272 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef31_s06_all3_dir_top1_w0p1_cap0p005 | gap_band | gap_003_005 | 55 | 0.0882 | 0.1843 | 0.5157 | 0.3002 | 0.7091 | 0.9455 | 0 | 1 | -0.1849 | -0.1901 | -0.4677 | 0.0125 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4960 | 1.0854 | 0.9328 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1216 | 0.1020 | -0.0465 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5504 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1760 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | service_confidence_tier | high | 22 | 0.5810 | 0.5579 | 1.0347 | 0.8118 | 0.3636 | 0.4545 | 4 | 4 | 0.3079 | 0.1835 | 0.0512 | 0.1324 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5030 | 1.0000 | 1.7329 | 0.3196 | 0.5388 | 19 | 141 | 0.1673 | 0.1286 | 0.0165 | 0.2958 | 0.4612 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5049 | 0.9999 | 1.7948 | 0.3159 | 0.5622 | 17 | 126 | 0.1613 | 0.1305 | 0.0165 | 0.2788 | 0.4378 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | qwidth_band | qwidth_extreme | 301 | 0.3779 | 0.4379 | 0.9960 | 1.9670 | 0.4053 | 0.6312 | 7 | 99 | 0.1048 | 0.0635 | 0.0126 | 0.3514 | 0.3688 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | qwidth_band | qwidth_high | 185 | 0.2339 | 0.3758 | 0.9867 | 0.9909 | 0.5514 | 0.7297 | 6 | 27 | -0.0391 | 0.0014 | 0.0033 | 0.0731 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_n_band | n_5_9 | 435 | 0.2396 | 0.3308 | 0.9867 | 1.6304 | 0.5678 | 0.7655 | 9 | 62 | -0.0335 | -0.0435 | 0.0033 | 0.0635 | 0.2345 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_level | artist | 412 | 0.3186 | 0.3767 | 0.9867 | 1.5783 | 0.4879 | 0.7451 | 13 | 60 | 0.0455 | 0.0023 | 0.0033 | 0.0859 | 0.2549 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | service_confidence_tier | low | 499 | 0.2654 | 0.3523 | 0.9719 | 1.5790 | 0.5271 | 0.7355 | 9 | 89 | -0.0077 | -0.0221 | -0.0115 | 0.0923 | 0.2645 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | service_confidence_tier | medium | 308 | 0.2647 | 0.3970 | 0.9707 | 0.7177 | 0.5130 | 0.6916 | 13 | 58 | -0.0084 | 0.0226 | -0.0127 | 0.0252 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | gap_band | gap_005_010 | 125 | 0.1496 | 0.2512 | 0.9530 | 0.7556 | 0.7680 | 0.9040 | 5 | 3 | -0.1235 | -0.1232 | -0.0304 | 0.0383 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_n_band | n_20_49 | 90 | 0.2007 | 0.3406 | 0.9166 | 0.6255 | 0.5889 | 0.7556 | 3 | 13 | -0.0723 | -0.0337 | -0.0669 | 0.0512 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | qwidth_band | qwidth_mid | 242 | 0.2395 | 0.3385 | 0.8841 | 0.4711 | 0.5702 | 0.7521 | 11 | 22 | -0.0336 | -0.0359 | -0.0993 | 0.0059 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2996 | -0.1045 | 1.3505 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | gap_band | gap_010_020 | 128 | 0.2245 | 0.3393 | 0.8740 | 0.5172 | 0.5625 | 0.6953 | 3 | 16 | -0.0485 | -0.0351 | -0.1094 | -0.0465 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_n_band | n_10_19 | 199 | 0.2884 | 0.3919 | 0.8640 | 0.7511 | 0.5075 | 0.7136 | 5 | 34 | 0.0153 | 0.0175 | -0.1194 | 0.0272 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_level | artist_size | 224 | 0.1899 | 0.3479 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0831 | -0.0265 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2905 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | qwidth_band | qwidth_low | 101 | 0.1757 | 0.2683 | 0.8081 | 0.4145 | 0.6634 | 0.8218 | 2 | 3 | -0.0973 | -0.1060 | -0.1753 | 0.0036 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | pred_spread_band | spread_high | 124 | 0.2082 | 0.2771 | 0.7965 | 0.7723 | 0.6210 | 0.8952 | 3 | 3 | -0.0649 | -0.0973 | -0.1869 | -0.0465 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2240 | 0.7725 | 0.7745 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1503 | -0.2110 | -0.0056 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | pred_spread_band | spread_low_mid | 267 | 0.1175 | 0.2086 | 0.6586 | 0.3239 | 0.7940 | 0.9101 | 4 | 7 | -0.1556 | -0.1658 | -0.3249 | 0.0131 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | gap_band | gap_000_003 | 119 | 0.1031 | 0.1885 | 0.5299 | 0.3145 | 0.7983 | 0.9244 | 1 | 5 | -0.1699 | -0.1859 | -0.4536 | 0.0272 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p005 | gap_band | gap_003_005 | 55 | 0.0882 | 0.1843 | 0.5157 | 0.3002 | 0.7091 | 0.9455 | 0 | 1 | -0.1849 | -0.1901 | -0.4677 | 0.0125 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4960 | 1.0854 | 0.9328 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1216 | 0.1020 | -0.0465 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5504 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1760 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | service_confidence_tier | high | 22 | 0.5810 | 0.5579 | 1.0347 | 0.8118 | 0.3636 | 0.4545 | 4 | 4 | 0.3079 | 0.1835 | 0.0512 | 0.1324 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5030 | 1.0000 | 1.7329 | 0.3196 | 0.5388 | 19 | 141 | 0.1673 | 0.1286 | 0.0165 | 0.2958 | 0.4612 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5049 | 0.9999 | 1.7948 | 0.3159 | 0.5622 | 17 | 126 | 0.1613 | 0.1305 | 0.0165 | 0.2788 | 0.4378 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | qwidth_band | qwidth_extreme | 301 | 0.3779 | 0.4379 | 0.9960 | 1.9670 | 0.4053 | 0.6312 | 7 | 99 | 0.1048 | 0.0635 | 0.0126 | 0.3514 | 0.3688 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | qwidth_band | qwidth_high | 185 | 0.2339 | 0.3758 | 0.9867 | 0.9909 | 0.5514 | 0.7297 | 6 | 27 | -0.0391 | 0.0014 | 0.0033 | 0.0731 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_n_band | n_5_9 | 435 | 0.2396 | 0.3308 | 0.9867 | 1.6304 | 0.5678 | 0.7655 | 9 | 62 | -0.0335 | -0.0435 | 0.0033 | 0.0635 | 0.2345 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_level | artist | 412 | 0.3186 | 0.3767 | 0.9867 | 1.5783 | 0.4879 | 0.7451 | 13 | 60 | 0.0455 | 0.0023 | 0.0033 | 0.0859 | 0.2549 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | service_confidence_tier | low | 499 | 0.2654 | 0.3523 | 0.9719 | 1.5790 | 0.5271 | 0.7355 | 9 | 89 | -0.0077 | -0.0221 | -0.0115 | 0.0923 | 0.2645 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | service_confidence_tier | medium | 308 | 0.2647 | 0.3970 | 0.9707 | 0.7177 | 0.5130 | 0.6916 | 13 | 58 | -0.0084 | 0.0226 | -0.0127 | 0.0252 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | gap_band | gap_005_010 | 125 | 0.1496 | 0.2512 | 0.9530 | 0.7556 | 0.7680 | 0.9040 | 5 | 3 | -0.1235 | -0.1232 | -0.0304 | 0.0383 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_n_band | n_20_49 | 90 | 0.2007 | 0.3406 | 0.9166 | 0.6255 | 0.5889 | 0.7556 | 3 | 13 | -0.0723 | -0.0337 | -0.0669 | 0.0512 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | qwidth_band | qwidth_mid | 242 | 0.2395 | 0.3385 | 0.8841 | 0.4711 | 0.5702 | 0.7521 | 11 | 22 | -0.0336 | -0.0359 | -0.0993 | 0.0059 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2996 | -0.1045 | 1.3505 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | gap_band | gap_010_020 | 128 | 0.2245 | 0.3393 | 0.8740 | 0.5172 | 0.5625 | 0.6953 | 3 | 16 | -0.0485 | -0.0351 | -0.1094 | -0.0465 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_n_band | n_10_19 | 199 | 0.2884 | 0.3919 | 0.8640 | 0.7511 | 0.5075 | 0.7136 | 5 | 34 | 0.0153 | 0.0175 | -0.1194 | 0.0272 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_level | artist_size | 224 | 0.1899 | 0.3479 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0831 | -0.0265 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2905 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | qwidth_band | qwidth_low | 101 | 0.1757 | 0.2683 | 0.8081 | 0.4145 | 0.6634 | 0.8218 | 2 | 3 | -0.0973 | -0.1060 | -0.1753 | 0.0036 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | pred_spread_band | spread_high | 124 | 0.2082 | 0.2771 | 0.7965 | 0.7723 | 0.6210 | 0.8952 | 3 | 3 | -0.0649 | -0.0973 | -0.1869 | -0.0465 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2240 | 0.7725 | 0.7745 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1503 | -0.2110 | -0.0056 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | pred_spread_band | spread_low_mid | 267 | 0.1175 | 0.2086 | 0.6586 | 0.3239 | 0.7940 | 0.9101 | 4 | 7 | -0.1556 | -0.1658 | -0.3249 | 0.0131 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | gap_band | gap_000_003 | 119 | 0.1031 | 0.1885 | 0.5299 | 0.3145 | 0.7983 | 0.9244 | 1 | 5 | -0.1699 | -0.1859 | -0.4536 | 0.0272 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef31_s06_any2_dir_top3_w0p1_cap0p01 | gap_band | gap_003_005 | 55 | 0.0882 | 0.1843 | 0.5157 | 0.3002 | 0.7091 | 0.9455 | 0 | 1 | -0.1849 | -0.1901 | -0.4677 | 0.0125 | 0.0545 |

## 11. 다음 방향

- p95-neutral micro correction도 기준 후보를 넘지 못하면 점 예측 이동 추가 세분화는 중단.
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