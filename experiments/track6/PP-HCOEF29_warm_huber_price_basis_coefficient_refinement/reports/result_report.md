# PP-HCOEF29 Warm Huber OOF meta coefficient 실험

- 작성일: 2026-06-08 06:19
- 목적: 현재 안정 후보 `hcoef_stable` 위에 component delta와 신뢰도 피처를 Huber로 다시 계수화해 고정 70:30보다 안정적인 보정 후보가 나오는지 확인.
- 후보 선택: validation OOF와 반복 split/artist holdout 우선.
- fixed test와 0604는 확인용으로만 사용.

## 1. 실행 결론

- 새 운영 후보 채택 없음.
- 현재 안정 기준 `hcoef_stable` fixed test: `0.1388/0.2730/0.8064`.
- fixed test에서만 좋아진 후보는 운영 후보가 아니라 추가 재검증 후보로 분리.

## 2. 보정 공식

- 학습 target: `actual_log - hcoef_stable_log`.
- Huber 입력: component delta, 유사 작품 표본 신뢰도, quantile/risk 피처.
- 적용식: `corrected_log = hcoef_stable_log + clip(strength * HuberResidual, -cap, cap)`.
- cap은 0.02/0.03/0.05/0.08 log 단위로 고정하고 fixed test에서 고르지 않음.

## 3. 후보 설정

| candidate | feature_set | features | strength | cap | formula | purpose |
| --- | --- | --- | --- | --- | --- | --- |
| hcoef29_core_component_delta_s0p5_cap0p02 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 0.5000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s0p5_cap0p03 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 0.5000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s0p5_cap0p05 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 0.5000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s0p5_cap0p08 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 0.5000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s0p75_cap0p02 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 0.7500 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s0p75_cap0p03 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 0.7500 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s0p75_cap0p05 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 0.7500 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s0p75_cap0p08 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 0.7500 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s1_cap0p02 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 1.0000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s1_cap0p03 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 1.0000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s1_cap0p05 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 1.0000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_core_component_delta_s1_cap0p08 | core_component_delta | current_delta, ppv8_delta, svc_delta, l10_delta | 1.0000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습 |
| hcoef29_svc_reliability_delta_s0p5_cap0p02 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 0.5000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s0p5_cap0p03 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 0.5000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s0p5_cap0p05 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 0.5000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s0p5_cap0p08 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 0.5000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s0p75_cap0p02 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 0.7500 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s0p75_cap0p03 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 0.7500 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s0p75_cap0p05 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 0.7500 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s0p75_cap0p08 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 0.7500 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s1_cap0p02 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 1.0000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s1_cap0p03 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 1.0000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s1_cap0p05 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 1.0000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_svc_reliability_delta_s1_cap0p08 | svc_reliability_delta | svc_delta, svc_delta_reliable, svc_delta_low_n, svc_group_n_log, is_svc_artist_fallback, is_svc_high_n | 1.0000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습 |
| hcoef29_risk_guarded_component_s0p5_cap0p02 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 0.5000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s0p5_cap0p03 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 0.5000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 0.5000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 0.5000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s0p75_cap0p02 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 0.7500 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s0p75_cap0p03 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 0.7500 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s0p75_cap0p05 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 0.7500 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s0p75_cap0p08 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 0.7500 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s1_cap0p02 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 1.0000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s1_cap0p03 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 1.0000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s1_cap0p05 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 1.0000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_risk_guarded_component_s1_cap0p08 | risk_guarded_component | current_delta, ppv8_delta, svc_delta, l10_delta, quantile_width, l10_price_range_ratio, pred_spread_numeric, hcoef23_risk_score, risk_norm, svc_group_n_log | 1.0000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습 |
| hcoef29_h26_candidate_delta_s0p5_cap0p02 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 0.5000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s0p5_cap0p03 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 0.5000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s0p5_cap0p05 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 0.5000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s0p5_cap0p08 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 0.5000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s0p75_cap0p02 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 0.7500 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s0p75_cap0p03 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 0.7500 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s0p75_cap0p05 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 0.7500 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s0p75_cap0p08 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 0.7500 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s1_cap0p02 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 1.0000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s1_cap0p03 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 1.0000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s1_cap0p05 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 1.0000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_h26_candidate_delta_s1_cap0p08 | h26_candidate_delta | h26_fixed_delta, h26_direct_delta, h26_fixed_delta_safe, h26_direct_delta_safe, risk_norm, svc_group_n_log | 1.0000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 0.5000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 0.5000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 0.5000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 0.5000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 0.7500 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 0.7500 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s0p75_cap0p05 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 0.7500 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s0p75_cap0p08 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 0.7500 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s1_cap0p02 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 1.0000 | 0.0200 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s1_cap0p03 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 1.0000 | 0.0300 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s1_cap0p05 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 1.0000 | 0.0500 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |
| hcoef29_all_lowdim_signal_s1_cap0p08 | all_lowdim_signal | current_delta, ppv8_delta, svc_delta, l10_delta, h26_fixed_delta, h26_direct_delta, svc_delta_reliable, ppv8_delta_safe, current_delta_safe, quantile_width, pred_spread_numeric, risk_norm, svc_group_n_log, is_svc_artist_fallback | 1.0000 | 0.0800 | hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap) | 저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어 |

## 4. 선택 후보 요약

| candidate | candidate_type | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | repeated_min_any2_improve_prob | repeated_min_all3_improve_prob | fixed_test_p95_guard | stress0604_p95_guard | test_mean_move_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 안정 기준 | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | True | True |  |
| current_70_30 | 기존 70:30 기준 | 최소 비교 기준 | 0.1305 | 0.2110 | 0.6580 | 0.1305 | 0.2110 | 0.6580 | 0.1405 | 0.2748 | 0.8331 | 0.2779 | 0.3774 | 0.9871 | 0.0000 | 0.0000 | False | False |  |
| svc_numeric_seed_mean | 보류 | component 대조군 | 0.1272 | 0.2176 | 0.6504 | 0.1272 | 0.2176 | 0.6504 | 0.1520 | 0.2942 | 0.9381 | 0.3072 | 0.4318 | 0.9998 | 0.0640 | 0.0000 | False | False |  |
| ppv8_service_proxy | 보류 | component 대조군 | 0.1544 | 0.2544 | 0.8084 | 0.1544 | 0.2544 | 0.8084 | 0.1632 | 0.2816 | 0.9311 | 0.2298 | 0.3359 | 0.9273 | 0.0000 | 0.0000 | False | True |  |
| l10_seq_full_generated_bucket | 보류 | component 대조군 | 0.1685 | 0.2981 | 0.8769 | 0.1685 | 0.2981 | 0.8769 | 0.1743 | 0.3265 | 0.9818 | 0.3207 | 0.4598 | 1.2569 | 0.0000 | 0.0000 | False | False |  |
| hcoef29_h26_candidate_delta_s0p5_cap0p05 | 보류 | 보류 | 0.1288 | 0.2084 | 0.6498 | 0.1270 | 0.2086 | 0.6500 | 0.1399 | 0.2736 | 0.8145 | 0.2699 | 0.3726 | 0.9454 | 0.0020 | 0.0000 | False | True | 0.5000 |
| hcoef29_h26_candidate_delta_s0p5_cap0p08 | 보류 | 보류 | 0.1288 | 0.2084 | 0.6498 | 0.1270 | 0.2086 | 0.6500 | 0.1399 | 0.2736 | 0.8145 | 0.2699 | 0.3724 | 0.9456 | 0.0020 | 0.0000 | False | True | 0.5000 |
| hcoef29_h26_candidate_delta_s0p5_cap0p03 | 보류 | 보류 | 0.1288 | 0.2084 | 0.6498 | 0.1270 | 0.2086 | 0.6500 | 0.1399 | 0.2736 | 0.8145 | 0.2699 | 0.3734 | 0.9691 | 0.0020 | 0.0000 | False | True | 0.5000 |
| hcoef29_h26_candidate_delta_s0p5_cap0p02 | 보류 | 보류 | 0.1288 | 0.2084 | 0.6498 | 0.1270 | 0.2086 | 0.6500 | 0.1399 | 0.2736 | 0.8145 | 0.2699 | 0.3738 | 0.9791 | 0.0020 | 0.0000 | False | True | 0.4988 |
| hcoef29_h26_candidate_delta_s0p75_cap0p02 | 보류 | 보류 | 0.1298 | 0.2086 | 0.6504 | 0.1267 | 0.2089 | 0.6553 | 0.1409 | 0.2741 | 0.8216 | 0.2682 | 0.3739 | 0.9792 | 0.0020 | 0.0000 | False | True | 0.7397 |
| hcoef29_h26_candidate_delta_s1_cap0p02 | 보류 | 보류 | 0.1281 | 0.2089 | 0.6519 | 0.1274 | 0.2091 | 0.6582 | 0.1409 | 0.2747 | 0.8287 | 0.2693 | 0.3740 | 0.9792 | 0.0040 | 0.0000 | False | True | 0.9728 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | 보류 | 보류 | 0.1236 | 0.2084 | 0.6446 | 0.1279 | 0.2079 | 0.6446 | 0.1410 | 0.2734 | 0.8302 | 0.2702 | 0.3711 | 0.9697 | 0.5520 | 0.1540 | False | True | 0.4825 |
| hcoef29_svc_reliability_delta_s0p5_cap0p08 | 보류 | 보류 | 0.1243 | 0.2090 | 0.6531 | 0.1252 | 0.2087 | 0.6511 | 0.1416 | 0.2740 | 0.8401 | 0.2722 | 0.3660 | 0.9399 | 0.1480 | 0.0120 | False | True | 0.4983 |
| hcoef29_svc_reliability_delta_s0p5_cap0p03 | 보류 | 보류 | 0.1243 | 0.2088 | 0.6531 | 0.1252 | 0.2085 | 0.6511 | 0.1416 | 0.2742 | 0.8401 | 0.2722 | 0.3711 | 0.9697 | 0.1480 | 0.0120 | False | True | 0.4845 |
| hcoef29_h26_candidate_delta_s1_cap0p08 | 보류 | 보류 | 0.1281 | 0.2088 | 0.6519 | 0.1274 | 0.2092 | 0.6582 | 0.1416 | 0.2744 | 0.8287 | 0.2693 | 0.3723 | 0.9418 | 0.0040 | 0.0000 | False | True | 1.0000 |
| hcoef29_h26_candidate_delta_s1_cap0p05 | 보류 | 보류 | 0.1281 | 0.2088 | 0.6519 | 0.1274 | 0.2092 | 0.6582 | 0.1416 | 0.2745 | 0.8287 | 0.2693 | 0.3730 | 0.9453 | 0.0040 | 0.0000 | False | True | 0.9997 |
| hcoef29_h26_candidate_delta_s1_cap0p03 | 보류 | 보류 | 0.1281 | 0.2088 | 0.6519 | 0.1274 | 0.2092 | 0.6582 | 0.1416 | 0.2745 | 0.8287 | 0.2693 | 0.3737 | 0.9689 | 0.0040 | 0.0000 | False | True | 0.9902 |
| hcoef29_h26_candidate_delta_s0p75_cap0p05 | 보류 | 보류 | 0.1298 | 0.2085 | 0.6504 | 0.1267 | 0.2089 | 0.6553 | 0.1419 | 0.2740 | 0.8216 | 0.2682 | 0.3728 | 0.9454 | 0.0020 | 0.0000 | False | True | 0.7500 |
| hcoef29_h26_candidate_delta_s0p75_cap0p08 | 보류 | 보류 | 0.1298 | 0.2085 | 0.6504 | 0.1267 | 0.2089 | 0.6553 | 0.1419 | 0.2740 | 0.8216 | 0.2682 | 0.3721 | 0.9418 | 0.0020 | 0.0000 | False | True | 0.7500 |
| hcoef29_h26_candidate_delta_s0p75_cap0p03 | 보류 | 보류 | 0.1298 | 0.2085 | 0.6504 | 0.1267 | 0.2089 | 0.6553 | 0.1419 | 0.2740 | 0.8216 | 0.2682 | 0.3735 | 0.9690 | 0.0020 | 0.0000 | False | True | 0.7482 |
| hcoef29_svc_reliability_delta_s0p5_cap0p05 | 보류 | 보류 | 0.1246 | 0.2089 | 0.6531 | 0.1252 | 0.2086 | 0.6511 | 0.1419 | 0.2741 | 0.8401 | 0.2722 | 0.3687 | 0.9411 | 0.1520 | 0.0080 | False | True | 0.4951 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | 보류 | 보류 | 0.1235 | 0.2083 | 0.6405 | 0.1253 | 0.2078 | 0.6446 | 0.1421 | 0.2728 | 0.8302 | 0.2737 | 0.3678 | 0.9521 | 0.7000 | 0.2720 | False | True | 0.4992 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | 보류 | 보류 | 0.1220 | 0.2088 | 0.6512 | 0.1259 | 0.2083 | 0.6434 | 0.1430 | 0.2744 | 0.8297 | 0.2702 | 0.3710 | 0.9719 | 0.3560 | 0.0380 | False | True | 0.6645 |
| hcoef29_all_lowdim_signal_s1_cap0p03 | 보류 | 보류 | 0.1249 | 0.2091 | 0.6512 | 0.1255 | 0.2086 | 0.6468 | 0.1430 | 0.2747 | 0.8293 | 0.2702 | 0.3710 | 0.9738 | 0.2420 | 0.0160 | False | True | 0.7964 |
| hcoef29_svc_reliability_delta_s0p5_cap0p02 | 보류 | 보류 | 0.1246 | 0.2089 | 0.6529 | 0.1269 | 0.2087 | 0.6511 | 0.1431 | 0.2741 | 0.8367 | 0.2800 | 0.3722 | 0.9789 | 0.0680 | 0.0020 | False | True | 0.4640 |
| hcoef29_risk_guarded_component_s0p5_cap0p03 | 보류 | 보류 | 0.1282 | 0.2077 | 0.6443 | 0.1279 | 0.2077 | 0.6396 | 0.1439 | 0.2723 | 0.8081 | 0.2758 | 0.3707 | 0.9697 | 0.7200 | 0.2520 | False | True | 0.4845 |
| hcoef29_risk_guarded_component_s0p5_cap0p02 | 보류 | 보류 | 0.1282 | 0.2079 | 0.6372 | 0.1281 | 0.2078 | 0.6366 | 0.1441 | 0.2724 | 0.8081 | 0.2725 | 0.3717 | 0.9794 | 0.6820 | 0.1360 | False | True | 0.4403 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | 보류 | 보류 | 0.1235 | 0.2083 | 0.6405 | 0.1229 | 0.2080 | 0.6446 | 0.1441 | 0.2735 | 0.8273 | 0.2737 | 0.3718 | 0.9789 | 0.5840 | 0.1700 | False | True | 0.4430 |
| hcoef29_all_lowdim_signal_s1_cap0p02 | 보류 | 보류 | 0.1237 | 0.2086 | 0.6417 | 0.1243 | 0.2084 | 0.6417 | 0.1441 | 0.2740 | 0.8273 | 0.2747 | 0.3717 | 0.9789 | 0.3800 | 0.0560 | False | True | 0.6552 |
| hcoef29_svc_reliability_delta_s0p75_cap0p02 | 보류 | 보류 | 0.1257 | 0.2093 | 0.6541 | 0.1259 | 0.2091 | 0.6505 | 0.1441 | 0.2746 | 0.8367 | 0.2800 | 0.3723 | 0.9789 | 0.0320 | 0.0000 | False | True | 0.6496 |
| hcoef29_risk_guarded_component_s1_cap0p03 | 보류 | 보류 | 0.1273 | 0.2084 | 0.6423 | 0.1261 | 0.2081 | 0.6417 | 0.1442 | 0.2728 | 0.8097 | 0.2758 | 0.3707 | 0.9697 | 0.5300 | 0.1400 | False | True | 0.7916 |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | 보류 | 보류 | 0.1242 | 0.2071 | 0.6347 | 0.1239 | 0.2071 | 0.6392 | 0.1442 | 0.2718 | 0.8081 | 0.2789 | 0.3678 | 0.9446 | 0.9280 | 0.5480 | False | True | 0.5000 |
| hcoef29_risk_guarded_component_s0p5_cap0p05 | 보류 | 보류 | 0.1242 | 0.2072 | 0.6347 | 0.1239 | 0.2072 | 0.6392 | 0.1442 | 0.2719 | 0.8081 | 0.2751 | 0.3690 | 0.9466 | 0.9260 | 0.5440 | False | True | 0.4992 |
| hcoef29_core_component_delta_s0p75_cap0p03 | 보류 | 보류 | 0.1245 | 0.2080 | 0.6447 | 0.1209 | 0.2071 | 0.6457 | 0.1443 | 0.2739 | 0.8321 | 0.2662 | 0.3745 | 0.9845 | 0.7700 | 0.3480 | False | False | 0.6923 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | 보류 | 보류 | 0.1236 | 0.2084 | 0.6405 | 0.1279 | 0.2079 | 0.6446 | 0.1445 | 0.2731 | 0.8302 | 0.2713 | 0.3695 | 0.9570 | 0.6300 | 0.1920 | False | True | 0.4970 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | 보류 | 보류 | 0.1229 | 0.2085 | 0.6422 | 0.1229 | 0.2083 | 0.6421 | 0.1446 | 0.2738 | 0.8273 | 0.2710 | 0.3718 | 0.9789 | 0.4640 | 0.0900 | False | True | 0.5675 |
| hcoef29_risk_guarded_component_s1_cap0p02 | 보류 | 보류 | 0.1293 | 0.2080 | 0.6369 | 0.1266 | 0.2078 | 0.6368 | 0.1446 | 0.2724 | 0.8089 | 0.2725 | 0.3717 | 0.9794 | 0.6660 | 0.1920 | False | True | 0.6552 |
| hcoef29_svc_reliability_delta_s1_cap0p02 | 보류 | 보류 | 0.1259 | 0.2096 | 0.6548 | 0.1281 | 0.2093 | 0.6524 | 0.1446 | 0.2751 | 0.8373 | 0.2800 | 0.3724 | 0.9789 | 0.0240 | 0.0000 | False | True | 0.8060 |
| hcoef29_risk_guarded_component_s0p75_cap0p02 | 보류 | 보류 | 0.1301 | 0.2080 | 0.6370 | 0.1274 | 0.2078 | 0.6370 | 0.1449 | 0.2725 | 0.8085 | 0.2725 | 0.3717 | 0.9794 | 0.6740 | 0.1720 | False | True | 0.5643 |
| hcoef29_all_lowdim_signal_s0p75_cap0p08 | 보류 | 보류 | 0.1220 | 0.2095 | 0.6428 | 0.1236 | 0.2088 | 0.6464 | 0.1450 | 0.2742 | 0.8297 | 0.2677 | 0.3679 | 0.9549 | 0.4540 | 0.0380 | False | True | 0.7463 |
| hcoef29_all_lowdim_signal_s0p75_cap0p05 | 보류 | 보류 | 0.1220 | 0.2093 | 0.6428 | 0.1252 | 0.2086 | 0.6464 | 0.1452 | 0.2744 | 0.8297 | 0.2669 | 0.3698 | 0.9657 | 0.4080 | 0.0340 | False | True | 0.7321 |
| hcoef29_core_component_delta_s0p5_cap0p02 | 보류 | 보류 | 0.1239 | 0.2077 | 0.6459 | 0.1233 | 0.2072 | 0.6438 | 0.1452 | 0.2732 | 0.8283 | 0.2659 | 0.3742 | 0.9834 | 0.8740 | 0.4960 | False | True | 0.4615 |
| hcoef29_core_component_delta_s0p5_cap0p03 | 보류 | 보류 | 0.1208 | 0.2078 | 0.6460 | 0.1233 | 0.2074 | 0.6438 | 0.1453 | 0.2731 | 0.8288 | 0.2641 | 0.3741 | 0.9833 | 0.8760 | 0.4800 | False | True | 0.4961 |
| hcoef29_core_component_delta_s1_cap0p02 | 보류 | 보류 | 0.1237 | 0.2077 | 0.6433 | 0.1229 | 0.2071 | 0.6434 | 0.1453 | 0.2736 | 0.8283 | 0.2671 | 0.3742 | 0.9789 | 0.8320 | 0.3760 | False | True | 0.6471 |
| hcoef29_core_component_delta_s0p5_cap0p05 | 보류 | 보류 | 0.1208 | 0.2078 | 0.6448 | 0.1233 | 0.2075 | 0.6438 | 0.1453 | 0.2731 | 0.8288 | 0.2641 | 0.3740 | 0.9833 | 0.9040 | 0.5420 | False | True | 0.5000 |
| hcoef29_core_component_delta_s0p5_cap0p08 | 보류 | 보류 | 0.1208 | 0.2077 | 0.6448 | 0.1233 | 0.2075 | 0.6438 | 0.1453 | 0.2731 | 0.8288 | 0.2641 | 0.3742 | 0.9833 | 0.9120 | 0.5520 | False | True | 0.5000 |
| hcoef29_core_component_delta_s0p75_cap0p02 | 보류 | 보류 | 0.1250 | 0.2077 | 0.6447 | 0.1229 | 0.2070 | 0.6446 | 0.1455 | 0.2735 | 0.8283 | 0.2662 | 0.3743 | 0.9807 | 0.8320 | 0.3960 | False | True | 0.5759 |
| hcoef29_svc_reliability_delta_s0p75_cap0p03 | 보류 | 보류 | 0.1257 | 0.2095 | 0.6552 | 0.1259 | 0.2091 | 0.6505 | 0.1456 | 0.2750 | 0.8491 | 0.2726 | 0.3712 | 0.9697 | 0.0380 | 0.0000 | False | True | 0.6960 |
| hcoef29_core_component_delta_s1_cap0p03 | 보류 | 보류 | 0.1225 | 0.2080 | 0.6437 | 0.1193 | 0.2069 | 0.6512 | 0.1457 | 0.2743 | 0.8319 | 0.2688 | 0.3747 | 0.9834 | 0.7360 | 0.3420 | False | True | 0.8171 |
| hcoef29_risk_guarded_component_s0p75_cap0p03 | 보류 | 보류 | 0.1283 | 0.2082 | 0.6439 | 0.1268 | 0.2080 | 0.6434 | 0.1461 | 0.2726 | 0.8091 | 0.2758 | 0.3707 | 0.9697 | 0.5040 | 0.1420 | False | True | 0.6605 |
| hcoef29_risk_guarded_component_s0p75_cap0p08 | 보류 | 보류 | 0.1270 | 0.2075 | 0.6258 | 0.1250 | 0.2076 | 0.6435 | 0.1470 | 0.2720 | 0.8091 | 0.2843 | 0.3685 | 0.9446 | 0.6900 | 0.2300 | False | True | 0.7493 |
| hcoef29_svc_reliability_delta_s0p75_cap0p05 | 보류 | 보류 | 0.1257 | 0.2097 | 0.6552 | 0.1256 | 0.2093 | 0.6505 | 0.1470 | 0.2753 | 0.8547 | 0.2752 | 0.3690 | 0.9410 | 0.0600 | 0.0000 | False | True | 0.7316 |
| hcoef29_risk_guarded_component_s0p75_cap0p05 | 보류 | 보류 | 0.1270 | 0.2080 | 0.6258 | 0.1250 | 0.2079 | 0.6429 | 0.1473 | 0.2724 | 0.8091 | 0.2739 | 0.3691 | 0.9466 | 0.6140 | 0.1880 | False | True | 0.7357 |
| hcoef29_svc_reliability_delta_s1_cap0p03 | 보류 | 보류 | 0.1259 | 0.2100 | 0.6569 | 0.1274 | 0.2097 | 0.6525 | 0.1475 | 0.2756 | 0.8508 | 0.2726 | 0.3714 | 0.9697 | 0.0140 | 0.0000 | False | True | 0.8855 |
| hcoef29_svc_reliability_delta_s0p75_cap0p08 | 보류 | 보류 | 0.1234 | 0.2100 | 0.6552 | 0.1251 | 0.2094 | 0.6505 | 0.1480 | 0.2753 | 0.8547 | 0.2693 | 0.3660 | 0.9395 | 0.0700 | 0.0000 | False | True | 0.7438 |
| hcoef29_all_lowdim_signal_s1_cap0p05 | 보류 | 보류 | 0.1246 | 0.2101 | 0.6421 | 0.1240 | 0.2093 | 0.6468 | 0.1483 | 0.2757 | 0.8293 | 0.2648 | 0.3698 | 0.9663 | 0.2740 | 0.0080 | False | True | 0.9366 |
| hcoef29_all_lowdim_signal_s1_cap0p08 | 보류 | 보류 | 0.1242 | 0.2109 | 0.6421 | 0.1249 | 0.2101 | 0.6468 | 0.1483 | 0.2758 | 0.8293 | 0.2673 | 0.3684 | 0.9792 | 0.1800 | 0.0020 | False | True | 0.9870 |
| hcoef29_core_component_delta_s1_cap0p08 | 보류 | 보류 | 0.1233 | 0.2090 | 0.6437 | 0.1243 | 0.2084 | 0.6560 | 0.1484 | 0.2749 | 0.8326 | 0.2664 | 0.3750 | 0.9859 | 0.3940 | 0.0900 | False | False | 0.9995 |
| hcoef29_core_component_delta_s1_cap0p05 | 보류 | 보류 | 0.1229 | 0.2088 | 0.6437 | 0.1243 | 0.2077 | 0.6467 | 0.1487 | 0.2751 | 0.8326 | 0.2688 | 0.3751 | 0.9860 | 0.4640 | 0.1180 | False | False | 0.9743 |
| hcoef29_svc_reliability_delta_s1_cap0p05 | 보류 | 보류 | 0.1246 | 0.2105 | 0.6573 | 0.1275 | 0.2100 | 0.6525 | 0.1492 | 0.2765 | 0.8714 | 0.2755 | 0.3693 | 0.9410 | 0.0260 | 0.0000 | False | True | 0.9544 |
| hcoef29_svc_reliability_delta_s1_cap0p08 | 보류 | 보류 | 0.1246 | 0.2112 | 0.6573 | 0.1277 | 0.2104 | 0.6525 | 0.1492 | 0.2770 | 0.8714 | 0.2691 | 0.3663 | 0.9392 | 0.0140 | 0.0000 | False | True | 0.9838 |
| hcoef29_risk_guarded_component_s1_cap0p08 | 보류 | 보류 | 0.1253 | 0.2088 | 0.6391 | 0.1266 | 0.2087 | 0.6589 | 0.1499 | 0.2729 | 0.8123 | 0.2843 | 0.3686 | 0.9446 | 0.2380 | 0.0280 | False | True | 0.9929 |
| hcoef29_core_component_delta_s0p75_cap0p05 | 보류 | 보류 | 0.1245 | 0.2082 | 0.6423 | 0.1217 | 0.2076 | 0.6443 | 0.1505 | 0.2738 | 0.8323 | 0.2662 | 0.3745 | 0.9844 | 0.6480 | 0.2580 | False | False | 0.7478 |
| hcoef29_core_component_delta_s0p75_cap0p08 | 보류 | 보류 | 0.1245 | 0.2081 | 0.6423 | 0.1217 | 0.2077 | 0.6443 | 0.1510 | 0.2738 | 0.8323 | 0.2662 | 0.3744 | 0.9844 | 0.6620 | 0.2820 | False | False | 0.7500 |
| hcoef29_risk_guarded_component_s1_cap0p05 | 보류 | 보류 | 0.1247 | 0.2090 | 0.6391 | 0.1259 | 0.2086 | 0.6468 | 0.1514 | 0.2731 | 0.8123 | 0.2739 | 0.3692 | 0.9466 | 0.3960 | 0.0780 | False | True | 0.9362 |

## 5. Scope별 metrics

| scope | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mean_move_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |  |
| 0604_stress | hcoef29_all_lowdim_signal_s0p5_cap0p02 | 0.2737 | 0.3718 | 0.9789 | 1.3062 | 0.0006 | -0.0025 | -0.0045 | 0.3606 |
| 0604_stress | hcoef29_all_lowdim_signal_s0p5_cap0p03 | 0.2702 | 0.3711 | 0.9697 | 1.3056 | -0.0029 | -0.0033 | -0.0138 | 0.4099 |
| 0604_stress | hcoef29_all_lowdim_signal_s0p5_cap0p05 | 0.2713 | 0.3695 | 0.9570 | 1.3048 | -0.0018 | -0.0049 | -0.0264 | 0.4449 |
| 0604_stress | hcoef29_all_lowdim_signal_s0p5_cap0p08 | 0.2737 | 0.3678 | 0.9521 | 1.3040 | 0.0006 | -0.0065 | -0.0314 | 0.4719 |
| 0604_stress | hcoef29_all_lowdim_signal_s0p75_cap0p02 | 0.2710 | 0.3718 | 0.9789 | 1.3062 | -0.0020 | -0.0025 | -0.0045 | 0.4519 |
| 0604_stress | hcoef29_all_lowdim_signal_s0p75_cap0p03 | 0.2702 | 0.3710 | 0.9719 | 1.3055 | -0.0029 | -0.0034 | -0.0115 | 0.5409 |
| 0604_stress | hcoef29_all_lowdim_signal_s0p75_cap0p05 | 0.2669 | 0.3698 | 0.9657 | 1.3045 | -0.0061 | -0.0045 | -0.0177 | 0.6284 |
| 0604_stress | hcoef29_all_lowdim_signal_s0p75_cap0p08 | 0.2677 | 0.3679 | 0.9549 | 1.3034 | -0.0054 | -0.0065 | -0.0286 | 0.6735 |
| 0604_stress | hcoef29_all_lowdim_signal_s1_cap0p02 | 0.2747 | 0.3717 | 0.9789 | 1.3062 | 0.0016 | -0.0026 | -0.0045 | 0.5160 |
| 0604_stress | hcoef29_all_lowdim_signal_s1_cap0p03 | 0.2702 | 0.3710 | 0.9738 | 1.3055 | -0.0029 | -0.0033 | -0.0096 | 0.6375 |
| 0604_stress | hcoef29_all_lowdim_signal_s1_cap0p05 | 0.2648 | 0.3698 | 0.9663 | 1.3042 | -0.0082 | -0.0046 | -0.0172 | 0.7807 |
| 0604_stress | hcoef29_all_lowdim_signal_s1_cap0p08 | 0.2673 | 0.3684 | 0.9792 | 1.3032 | -0.0058 | -0.0059 | -0.0043 | 0.8625 |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p02 | 0.2659 | 0.3742 | 0.9834 | 1.3048 | -0.0072 | -0.0002 | -0.0000 | 0.4086 |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p03 | 0.2641 | 0.3741 | 0.9833 | 1.3032 | -0.0090 | -0.0003 | -0.0001 | 0.4653 |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p05 | 0.2641 | 0.3740 | 0.9833 | 1.3012 | -0.0090 | -0.0004 | -0.0001 | 0.4952 |
| 0604_stress | hcoef29_core_component_delta_s0p5_cap0p08 | 0.2641 | 0.3742 | 0.9833 | 1.2996 | -0.0090 | -0.0002 | -0.0001 | 0.4993 |
| 0604_stress | hcoef29_core_component_delta_s0p75_cap0p02 | 0.2662 | 0.3743 | 0.9807 | 1.3048 | -0.0069 | -0.0001 | -0.0028 | 0.5032 |
| 0604_stress | hcoef29_core_component_delta_s0p75_cap0p03 | 0.2662 | 0.3745 | 0.9845 | 1.3033 | -0.0069 | 0.0001 | 0.0011 | 0.6129 |
| 0604_stress | hcoef29_core_component_delta_s0p75_cap0p05 | 0.2662 | 0.3745 | 0.9844 | 1.3005 | -0.0069 | 0.0001 | 0.0010 | 0.7129 |
| 0604_stress | hcoef29_core_component_delta_s0p75_cap0p08 | 0.2662 | 0.3744 | 0.9844 | 1.2977 | -0.0069 | 0.0000 | 0.0010 | 0.7444 |
| 0604_stress | hcoef29_core_component_delta_s1_cap0p02 | 0.2671 | 0.3742 | 0.9789 | 1.3048 | -0.0060 | -0.0001 | -0.0045 | 0.5705 |
| 0604_stress | hcoef29_core_component_delta_s1_cap0p03 | 0.2688 | 0.3747 | 0.9834 | 1.3033 | -0.0043 | 0.0003 | -0.0001 | 0.7136 |
| 0604_stress | hcoef29_core_component_delta_s1_cap0p05 | 0.2688 | 0.3751 | 0.9860 | 1.3005 | -0.0043 | 0.0007 | 0.0026 | 0.8858 |
| 0604_stress | hcoef29_core_component_delta_s1_cap0p08 | 0.2664 | 0.3750 | 0.9859 | 1.2967 | -0.0067 | 0.0007 | 0.0025 | 0.9750 |
| 0604_stress | hcoef29_h26_candidate_delta_s0p5_cap0p02 | 0.2699 | 0.3738 | 0.9791 | 1.3083 | -0.0032 | -0.0006 | -0.0043 | 0.4636 |
| 0604_stress | hcoef29_h26_candidate_delta_s0p5_cap0p03 | 0.2699 | 0.3734 | 0.9691 | 1.3086 | -0.0032 | -0.0010 | -0.0144 | 0.4740 |
| 0604_stress | hcoef29_h26_candidate_delta_s0p5_cap0p05 | 0.2699 | 0.3726 | 0.9454 | 1.3093 | -0.0032 | -0.0018 | -0.0381 | 0.4909 |
| 0604_stress | hcoef29_h26_candidate_delta_s0p5_cap0p08 | 0.2699 | 0.3724 | 0.9456 | 1.3099 | -0.0032 | -0.0019 | -0.0378 | 0.4986 |
| 0604_stress | hcoef29_h26_candidate_delta_s0p75_cap0p02 | 0.2682 | 0.3739 | 0.9792 | 1.3080 | -0.0048 | -0.0005 | -0.0043 | 0.6812 |
| 0604_stress | hcoef29_h26_candidate_delta_s0p75_cap0p03 | 0.2682 | 0.3735 | 0.9690 | 1.3085 | -0.0048 | -0.0008 | -0.0145 | 0.6954 |
| 0604_stress | hcoef29_h26_candidate_delta_s0p75_cap0p05 | 0.2682 | 0.3728 | 0.9454 | 1.3093 | -0.0048 | -0.0016 | -0.0381 | 0.7153 |
| 0604_stress | hcoef29_h26_candidate_delta_s0p75_cap0p08 | 0.2682 | 0.3721 | 0.9418 | 1.3103 | -0.0048 | -0.0023 | -0.0416 | 0.7404 |
| 0604_stress | hcoef29_h26_candidate_delta_s1_cap0p02 | 0.2693 | 0.3740 | 0.9792 | 1.3077 | -0.0038 | -0.0003 | -0.0042 | 0.8857 |
| 0604_stress | hcoef29_h26_candidate_delta_s1_cap0p03 | 0.2693 | 0.3737 | 0.9689 | 1.3083 | -0.0038 | -0.0006 | -0.0145 | 0.9134 |
| 0604_stress | hcoef29_h26_candidate_delta_s1_cap0p05 | 0.2693 | 0.3730 | 0.9453 | 1.3093 | -0.0038 | -0.0013 | -0.0381 | 0.9389 |
| 0604_stress | hcoef29_h26_candidate_delta_s1_cap0p08 | 0.2693 | 0.3723 | 0.9418 | 1.3103 | -0.0038 | -0.0020 | -0.0417 | 0.9649 |
| 0604_stress | hcoef29_risk_guarded_component_s0p5_cap0p02 | 0.2725 | 0.3717 | 0.9794 | 1.3129 | -0.0006 | -0.0027 | -0.0040 | 0.1262 |
| 0604_stress | hcoef29_risk_guarded_component_s0p5_cap0p03 | 0.2758 | 0.3707 | 0.9697 | 1.3155 | 0.0027 | -0.0037 | -0.0138 | 0.1869 |
| 0604_stress | hcoef29_risk_guarded_component_s0p5_cap0p05 | 0.2751 | 0.3690 | 0.9466 | 1.3208 | 0.0020 | -0.0053 | -0.0369 | 0.2932 |
| 0604_stress | hcoef29_risk_guarded_component_s0p5_cap0p08 | 0.2789 | 0.3678 | 0.9446 | 1.3281 | 0.0058 | -0.0065 | -0.0389 | 0.3990 |
| 0604_stress | hcoef29_risk_guarded_component_s0p75_cap0p02 | 0.2725 | 0.3717 | 0.9794 | 1.3129 | -0.0006 | -0.0027 | -0.0040 | 0.1270 |
| 0604_stress | hcoef29_risk_guarded_component_s0p75_cap0p03 | 0.2758 | 0.3707 | 0.9697 | 1.3156 | 0.0027 | -0.0037 | -0.0138 | 0.1892 |
| 0604_stress | hcoef29_risk_guarded_component_s0p75_cap0p05 | 0.2739 | 0.3691 | 0.9466 | 1.3210 | 0.0008 | -0.0052 | -0.0369 | 0.3090 |
| 0604_stress | hcoef29_risk_guarded_component_s0p75_cap0p08 | 0.2843 | 0.3685 | 0.9446 | 1.3293 | 0.0112 | -0.0059 | -0.0389 | 0.4627 |
| 0604_stress | hcoef29_risk_guarded_component_s1_cap0p02 | 0.2725 | 0.3717 | 0.9794 | 1.3129 | -0.0006 | -0.0027 | -0.0040 | 0.1276 |
| 0604_stress | hcoef29_risk_guarded_component_s1_cap0p03 | 0.2758 | 0.3707 | 0.9697 | 1.3156 | 0.0027 | -0.0037 | -0.0138 | 0.1901 |
| 0604_stress | hcoef29_risk_guarded_component_s1_cap0p05 | 0.2739 | 0.3692 | 0.9466 | 1.3211 | 0.0008 | -0.0051 | -0.0369 | 0.3143 |
| 0604_stress | hcoef29_risk_guarded_component_s1_cap0p08 | 0.2843 | 0.3686 | 0.9446 | 1.3297 | 0.0112 | -0.0058 | -0.0389 | 0.4856 |
| 0604_stress | hcoef29_svc_reliability_delta_s0p5_cap0p02 | 0.2800 | 0.3722 | 0.9789 | 1.3049 | 0.0069 | -0.0022 | -0.0045 | 0.3731 |
| 0604_stress | hcoef29_svc_reliability_delta_s0p5_cap0p03 | 0.2722 | 0.3711 | 0.9697 | 1.3036 | -0.0009 | -0.0033 | -0.0138 | 0.4016 |
| 0604_stress | hcoef29_svc_reliability_delta_s0p5_cap0p05 | 0.2722 | 0.3687 | 0.9411 | 1.3011 | -0.0009 | -0.0056 | -0.0423 | 0.4280 |
| 0604_stress | hcoef29_svc_reliability_delta_s0p5_cap0p08 | 0.2722 | 0.3660 | 0.9399 | 1.2983 | -0.0009 | -0.0084 | -0.0436 | 0.4498 |
| 0604_stress | hcoef29_svc_reliability_delta_s0p75_cap0p02 | 0.2800 | 0.3723 | 0.9789 | 1.3049 | 0.0069 | -0.0021 | -0.0045 | 0.5093 |
| 0604_stress | hcoef29_svc_reliability_delta_s0p75_cap0p03 | 0.2726 | 0.3712 | 0.9697 | 1.3036 | -0.0005 | -0.0032 | -0.0138 | 0.5596 |
| 0604_stress | hcoef29_svc_reliability_delta_s0p75_cap0p05 | 0.2752 | 0.3690 | 0.9410 | 1.3010 | 0.0022 | -0.0054 | -0.0425 | 0.6117 |
| 0604_stress | hcoef29_svc_reliability_delta_s0p75_cap0p08 | 0.2693 | 0.3660 | 0.9395 | 1.2975 | -0.0037 | -0.0083 | -0.0439 | 0.6464 |
| 0604_stress | hcoef29_svc_reliability_delta_s1_cap0p02 | 0.2800 | 0.3724 | 0.9789 | 1.3048 | 0.0069 | -0.0019 | -0.0045 | 0.6206 |
| 0604_stress | hcoef29_svc_reliability_delta_s1_cap0p03 | 0.2726 | 0.3714 | 0.9697 | 1.3035 | -0.0005 | -0.0030 | -0.0138 | 0.6986 |
| 0604_stress | hcoef29_svc_reliability_delta_s1_cap0p05 | 0.2755 | 0.3693 | 0.9410 | 1.3010 | 0.0024 | -0.0050 | -0.0425 | 0.7797 |
| 0604_stress | hcoef29_svc_reliability_delta_s1_cap0p08 | 0.2691 | 0.3663 | 0.9392 | 1.2971 | -0.0040 | -0.0080 | -0.0443 | 0.8354 |
| 0604_stress | hcoef_stable | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 |  |
| 0604_stress | l10_seq_full_generated_bucket | 0.3207 | 0.4598 | 1.2569 | 1.0793 | 0.0477 | 0.0854 | 0.2734 |  |
| 0604_stress | ppv8_service_proxy | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 |  |
| 0604_stress | svc_numeric_seed_mean | 0.3072 | 0.4318 | 0.9998 | 1.6906 | 0.0342 | 0.0575 | 0.0164 |  |
| fixed_confirmation | current_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 |  |
| fixed_confirmation | hcoef29_all_lowdim_signal_s0p5_cap0p02 | 0.1441 | 0.2735 | 0.8273 | 0.3993 | 0.0053 | 0.0005 | 0.0209 | 0.4430 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s0p5_cap0p03 | 0.1410 | 0.2734 | 0.8302 | 0.3993 | 0.0022 | 0.0004 | 0.0239 | 0.4825 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s0p5_cap0p05 | 0.1445 | 0.2731 | 0.8302 | 0.3991 | 0.0057 | 0.0001 | 0.0239 | 0.4970 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s0p5_cap0p08 | 0.1421 | 0.2728 | 0.8302 | 0.3988 | 0.0033 | -0.0002 | 0.0239 | 0.4992 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s0p75_cap0p02 | 0.1446 | 0.2738 | 0.8273 | 0.3994 | 0.0058 | 0.0008 | 0.0209 | 0.5675 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s0p75_cap0p03 | 0.1430 | 0.2744 | 0.8297 | 0.3997 | 0.0042 | 0.0014 | 0.0234 | 0.6645 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s0p75_cap0p05 | 0.1452 | 0.2744 | 0.8297 | 0.4000 | 0.0064 | 0.0014 | 0.0234 | 0.7321 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s0p75_cap0p08 | 0.1450 | 0.2742 | 0.8297 | 0.3996 | 0.0062 | 0.0012 | 0.0234 | 0.7463 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s1_cap0p02 | 0.1441 | 0.2740 | 0.8273 | 0.3995 | 0.0053 | 0.0010 | 0.0209 | 0.6552 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s1_cap0p03 | 0.1430 | 0.2747 | 0.8293 | 0.3998 | 0.0042 | 0.0017 | 0.0229 | 0.7964 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s1_cap0p05 | 0.1483 | 0.2757 | 0.8293 | 0.4006 | 0.0095 | 0.0027 | 0.0229 | 0.9366 |
| fixed_confirmation | hcoef29_all_lowdim_signal_s1_cap0p08 | 0.1483 | 0.2758 | 0.8293 | 0.4007 | 0.0095 | 0.0029 | 0.0229 | 0.9870 |
| fixed_confirmation | hcoef29_core_component_delta_s0p5_cap0p02 | 0.1452 | 0.2732 | 0.8283 | 0.3990 | 0.0064 | 0.0002 | 0.0220 | 0.4615 |
| fixed_confirmation | hcoef29_core_component_delta_s0p5_cap0p03 | 0.1453 | 0.2731 | 0.8288 | 0.3991 | 0.0065 | 0.0001 | 0.0224 | 0.4961 |
| fixed_confirmation | hcoef29_core_component_delta_s0p5_cap0p05 | 0.1453 | 0.2731 | 0.8288 | 0.3991 | 0.0065 | 0.0001 | 0.0224 | 0.5000 |
| fixed_confirmation | hcoef29_core_component_delta_s0p5_cap0p08 | 0.1453 | 0.2731 | 0.8288 | 0.3991 | 0.0065 | 0.0001 | 0.0224 | 0.5000 |
| fixed_confirmation | hcoef29_core_component_delta_s0p75_cap0p02 | 0.1455 | 0.2735 | 0.8283 | 0.3990 | 0.0067 | 0.0005 | 0.0220 | 0.5759 |
| fixed_confirmation | hcoef29_core_component_delta_s0p75_cap0p03 | 0.1443 | 0.2739 | 0.8321 | 0.3993 | 0.0054 | 0.0009 | 0.0258 | 0.6923 |
| fixed_confirmation | hcoef29_core_component_delta_s0p75_cap0p05 | 0.1505 | 0.2738 | 0.8323 | 0.3996 | 0.0117 | 0.0008 | 0.0259 | 0.7478 |
| fixed_confirmation | hcoef29_core_component_delta_s0p75_cap0p08 | 0.1510 | 0.2738 | 0.8323 | 0.3996 | 0.0122 | 0.0008 | 0.0259 | 0.7500 |
| fixed_confirmation | hcoef29_core_component_delta_s1_cap0p02 | 0.1453 | 0.2736 | 0.8283 | 0.3990 | 0.0065 | 0.0006 | 0.0220 | 0.6471 |
| fixed_confirmation | hcoef29_core_component_delta_s1_cap0p03 | 0.1457 | 0.2743 | 0.8319 | 0.3994 | 0.0069 | 0.0013 | 0.0255 | 0.8171 |
| fixed_confirmation | hcoef29_core_component_delta_s1_cap0p05 | 0.1487 | 0.2751 | 0.8326 | 0.4001 | 0.0099 | 0.0021 | 0.0263 | 0.9743 |
| fixed_confirmation | hcoef29_core_component_delta_s1_cap0p08 | 0.1484 | 0.2749 | 0.8326 | 0.4002 | 0.0096 | 0.0020 | 0.0263 | 0.9995 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s0p5_cap0p02 | 0.1399 | 0.2736 | 0.8145 | 0.3989 | 0.0011 | 0.0007 | 0.0081 | 0.4988 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s0p5_cap0p03 | 0.1399 | 0.2736 | 0.8145 | 0.3989 | 0.0011 | 0.0006 | 0.0081 | 0.5000 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s0p5_cap0p05 | 0.1399 | 0.2736 | 0.8145 | 0.3989 | 0.0011 | 0.0006 | 0.0081 | 0.5000 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s0p5_cap0p08 | 0.1399 | 0.2736 | 0.8145 | 0.3989 | 0.0011 | 0.0006 | 0.0081 | 0.5000 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s0p75_cap0p02 | 0.1409 | 0.2741 | 0.8216 | 0.3990 | 0.0021 | 0.0011 | 0.0152 | 0.7397 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s0p75_cap0p03 | 0.1419 | 0.2740 | 0.8216 | 0.3990 | 0.0030 | 0.0010 | 0.0152 | 0.7482 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s0p75_cap0p05 | 0.1419 | 0.2740 | 0.8216 | 0.3990 | 0.0030 | 0.0010 | 0.0152 | 0.7500 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s0p75_cap0p08 | 0.1419 | 0.2740 | 0.8216 | 0.3990 | 0.0030 | 0.0010 | 0.0152 | 0.7500 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s1_cap0p02 | 0.1409 | 0.2747 | 0.8287 | 0.3991 | 0.0021 | 0.0017 | 0.0223 | 0.9728 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s1_cap0p03 | 0.1416 | 0.2745 | 0.8287 | 0.3991 | 0.0028 | 0.0015 | 0.0223 | 0.9902 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s1_cap0p05 | 0.1416 | 0.2745 | 0.8287 | 0.3991 | 0.0028 | 0.0015 | 0.0223 | 0.9997 |
| fixed_confirmation | hcoef29_h26_candidate_delta_s1_cap0p08 | 0.1416 | 0.2744 | 0.8287 | 0.3991 | 0.0028 | 0.0015 | 0.0223 | 1.0000 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p5_cap0p02 | 0.1441 | 0.2724 | 0.8081 | 0.3982 | 0.0053 | -0.0005 | 0.0018 | 0.4403 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p5_cap0p03 | 0.1439 | 0.2723 | 0.8081 | 0.3978 | 0.0051 | -0.0007 | 0.0018 | 0.4845 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p5_cap0p05 | 0.1442 | 0.2719 | 0.8081 | 0.3975 | 0.0054 | -0.0010 | 0.0018 | 0.4992 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p5_cap0p08 | 0.1442 | 0.2718 | 0.8081 | 0.3974 | 0.0054 | -0.0012 | 0.0018 | 0.5000 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p75_cap0p02 | 0.1449 | 0.2725 | 0.8085 | 0.3982 | 0.0060 | -0.0005 | 0.0021 | 0.5643 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p75_cap0p03 | 0.1461 | 0.2726 | 0.8091 | 0.3980 | 0.0073 | -0.0004 | 0.0027 | 0.6605 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p75_cap0p05 | 0.1473 | 0.2724 | 0.8091 | 0.3976 | 0.0085 | -0.0006 | 0.0027 | 0.7357 |
| fixed_confirmation | hcoef29_risk_guarded_component_s0p75_cap0p08 | 0.1470 | 0.2720 | 0.8091 | 0.3973 | 0.0082 | -0.0010 | 0.0027 | 0.7493 |
| fixed_confirmation | hcoef29_risk_guarded_component_s1_cap0p02 | 0.1446 | 0.2724 | 0.8089 | 0.3980 | 0.0058 | -0.0006 | 0.0025 | 0.6552 |
| fixed_confirmation | hcoef29_risk_guarded_component_s1_cap0p03 | 0.1442 | 0.2728 | 0.8097 | 0.3981 | 0.0054 | -0.0002 | 0.0033 | 0.7916 |
| fixed_confirmation | hcoef29_risk_guarded_component_s1_cap0p05 | 0.1514 | 0.2731 | 0.8123 | 0.3980 | 0.0126 | 0.0001 | 0.0060 | 0.9362 |
| fixed_confirmation | hcoef29_risk_guarded_component_s1_cap0p08 | 0.1499 | 0.2729 | 0.8123 | 0.3975 | 0.0111 | -0.0001 | 0.0060 | 0.9929 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s0p5_cap0p02 | 0.1431 | 0.2741 | 0.8367 | 0.3987 | 0.0043 | 0.0011 | 0.0304 | 0.4640 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s0p5_cap0p03 | 0.1416 | 0.2742 | 0.8401 | 0.3988 | 0.0028 | 0.0012 | 0.0337 | 0.4845 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s0p5_cap0p05 | 0.1419 | 0.2741 | 0.8401 | 0.3987 | 0.0031 | 0.0011 | 0.0337 | 0.4951 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s0p5_cap0p08 | 0.1416 | 0.2740 | 0.8401 | 0.3986 | 0.0028 | 0.0010 | 0.0337 | 0.4983 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s0p75_cap0p02 | 0.1441 | 0.2746 | 0.8367 | 0.3988 | 0.0053 | 0.0016 | 0.0304 | 0.6496 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s0p75_cap0p03 | 0.1456 | 0.2750 | 0.8491 | 0.3988 | 0.0068 | 0.0020 | 0.0427 | 0.6960 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s0p75_cap0p05 | 0.1470 | 0.2753 | 0.8547 | 0.3990 | 0.0082 | 0.0023 | 0.0483 | 0.7316 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s0p75_cap0p08 | 0.1480 | 0.2753 | 0.8547 | 0.3990 | 0.0092 | 0.0023 | 0.0483 | 0.7438 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s1_cap0p02 | 0.1446 | 0.2751 | 0.8373 | 0.3990 | 0.0058 | 0.0021 | 0.0309 | 0.8060 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s1_cap0p03 | 0.1475 | 0.2756 | 0.8508 | 0.3990 | 0.0087 | 0.0026 | 0.0445 | 0.8855 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s1_cap0p05 | 0.1492 | 0.2765 | 0.8714 | 0.3991 | 0.0104 | 0.0035 | 0.0650 | 0.9544 |
| fixed_confirmation | hcoef29_svc_reliability_delta_s1_cap0p08 | 0.1492 | 0.2770 | 0.8714 | 0.3994 | 0.0104 | 0.0040 | 0.0650 | 0.9838 |
| fixed_confirmation | hcoef_stable | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |  |
| fixed_confirmation | l10_seq_full_generated_bucket | 0.1743 | 0.3265 | 0.9818 | 0.4396 | 0.0355 | 0.0535 | 0.1755 |  |
| fixed_confirmation | ppv8_service_proxy | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 0.0244 | 0.0086 | 0.1247 |  |
| fixed_confirmation | svc_numeric_seed_mean | 0.1520 | 0.2942 | 0.9381 | 0.4179 | 0.0132 | 0.0212 | 0.1317 |  |
| validation_oof_artist | current_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 |  |
| validation_oof_artist | hcoef29_all_lowdim_signal_s0p5_cap0p02 | 0.1229 | 0.2080 | 0.6446 | 0.3237 | -0.0031 | -0.0002 | -0.0033 | 0.4328 |
| validation_oof_artist | hcoef29_all_lowdim_signal_s0p5_cap0p03 | 0.1279 | 0.2079 | 0.6446 | 0.3235 | 0.0019 | -0.0003 | -0.0033 | 0.4757 |
| validation_oof_artist | hcoef29_all_lowdim_signal_s0p5_cap0p05 | 0.1279 | 0.2079 | 0.6446 | 0.3235 | 0.0019 | -0.0003 | -0.0033 | 0.4958 |
| validation_oof_artist | hcoef29_all_lowdim_signal_s0p5_cap0p08 | 0.1253 | 0.2078 | 0.6446 | 0.3236 | -0.0007 | -0.0004 | -0.0033 | 0.4993 |
| validation_oof_artist | hcoef29_all_lowdim_signal_s0p75_cap0p02 | 0.1229 | 0.2083 | 0.6421 | 0.3236 | -0.0031 | 0.0001 | -0.0059 | 0.5594 |
| validation_oof_artist | hcoef29_all_lowdim_signal_s0p75_cap0p03 | 0.1259 | 0.2083 | 0.6434 | 0.3232 | -0.0001 | 0.0001 | -0.0045 | 0.6493 |
| validation_oof_artist | hcoef29_all_lowdim_signal_s0p75_cap0p05 | 0.1252 | 0.2086 | 0.6464 | 0.3231 | -0.0008 | 0.0004 | -0.0015 | 0.7247 |
| validation_oof_artist | hcoef29_all_lowdim_signal_s0p75_cap0p08 | 0.1236 | 0.2088 | 0.6464 | 0.3233 | -0.0024 | 0.0006 | -0.0015 | 0.7453 |
| validation_oof_artist | hcoef29_all_lowdim_signal_s1_cap0p02 | 0.1243 | 0.2084 | 0.6417 | 0.3237 | -0.0016 | 0.0002 | -0.0063 | 0.6458 |

## 6. 반복 split/artist holdout 요약

| source_scope | validation_scheme | candidate | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | any2_improve_prob | all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p75_cap0p02 | -0.0034 | -0.0012 | -0.0022 | 0.9460 | 1.0000 | 0.6180 | 0.9820 | 0.5820 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p02 | -0.0031 | -0.0010 | -0.0032 | 0.9340 | 0.9960 | 0.6820 | 0.9800 | 0.6320 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s1_cap0p03 | -0.0054 | -0.0013 | 0.0009 | 0.9840 | 0.9820 | 0.3800 | 0.9760 | 0.3700 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p02 | -0.0028 | -0.0010 | -0.0030 | 0.9360 | 0.9960 | 0.7440 | 0.9740 | 0.7020 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p75_cap0p03 | -0.0040 | -0.0012 | -0.0009 | 0.9700 | 0.9820 | 0.4820 | 0.9740 | 0.4620 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p75_cap0p02 | -0.0030 | -0.0012 | -0.0017 | 0.9340 | 0.9980 | 0.6180 | 0.9700 | 0.5800 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s1_cap0p03 | -0.0055 | -0.0013 | -0.0003 | 0.9820 | 0.9720 | 0.4200 | 0.9700 | 0.4060 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p75_cap0p03 | -0.0043 | -0.0012 | -0.0021 | 0.9780 | 0.9620 | 0.5240 | 0.9660 | 0.5020 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s1_cap0p02 | -0.0031 | -0.0011 | -0.0017 | 0.9040 | 0.9960 | 0.5520 | 0.9580 | 0.4960 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p03 | -0.0026 | -0.0008 | -0.0038 | 0.8800 | 0.9660 | 0.7660 | 0.9560 | 0.6600 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s1_cap0p02 | -0.0027 | -0.0011 | -0.0014 | 0.9140 | 0.9960 | 0.5220 | 0.9560 | 0.4760 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p05 | -0.0027 | -0.0007 | -0.0037 | 0.8740 | 0.9540 | 0.7620 | 0.9500 | 0.6440 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p08 | -0.0027 | -0.0007 | -0.0037 | 0.8740 | 0.9540 | 0.7620 | 0.9500 | 0.6440 |
| validation_oof_row | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p05 | -0.0010 | -0.0010 | -0.0087 | 0.6840 | 0.9660 | 0.8940 | 0.9440 | 0.6000 |
| validation_oof_row | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | -0.0010 | -0.0011 | -0.0087 | 0.6840 | 0.9660 | 0.8940 | 0.9440 | 0.6000 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p03 | -0.0029 | -0.0008 | -0.0041 | 0.9080 | 0.9480 | 0.6860 | 0.9440 | 0.6000 |
| validation_oof_row | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | -0.0013 | -0.0011 | -0.0083 | 0.6660 | 0.9260 | 0.9080 | 0.9320 | 0.5700 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | -0.0017 | -0.0011 | -0.0062 | 0.7740 | 0.9500 | 0.8580 | 0.9300 | 0.6540 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p05 | -0.0016 | -0.0010 | -0.0062 | 0.7740 | 0.9480 | 0.8580 | 0.9300 | 0.6520 |
| validation_oof_row | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p05 | -0.0012 | -0.0010 | -0.0083 | 0.6660 | 0.9260 | 0.9080 | 0.9300 | 0.5720 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p05 | -0.0029 | -0.0007 | -0.0039 | 0.9060 | 0.9160 | 0.6780 | 0.9280 | 0.5800 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p08 | -0.0029 | -0.0007 | -0.0039 | 0.9060 | 0.9160 | 0.6780 | 0.9280 | 0.5800 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | -0.0019 | -0.0011 | -0.0050 | 0.7800 | 0.9240 | 0.7680 | 0.9280 | 0.5480 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p05 | -0.0018 | -0.0010 | -0.0050 | 0.7780 | 0.9200 | 0.7680 | 0.9260 | 0.5440 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p08 | -0.0039 | -0.0005 | -0.0034 | 0.9600 | 0.8500 | 0.7020 | 0.9200 | 0.5980 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p05 | -0.0039 | -0.0004 | -0.0034 | 0.9600 | 0.8400 | 0.7020 | 0.9120 | 0.5960 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p08 | -0.0037 | -0.0005 | -0.0041 | 0.9660 | 0.7960 | 0.7000 | 0.9120 | 0.5520 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p05 | -0.0037 | -0.0004 | -0.0041 | 0.9660 | 0.7780 | 0.7000 | 0.9040 | 0.5420 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p03 | -0.0037 | -0.0004 | -0.0025 | 0.9600 | 0.8240 | 0.6340 | 0.8920 | 0.5360 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p02 | -0.0015 | -0.0005 | -0.0025 | 0.7980 | 0.9040 | 0.6940 | 0.8880 | 0.5200 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p03 | -0.0035 | -0.0004 | -0.0032 | 0.9560 | 0.7620 | 0.6360 | 0.8760 | 0.4800 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p02 | -0.0016 | -0.0005 | -0.0029 | 0.8080 | 0.8540 | 0.6920 | 0.8740 | 0.4960 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p75_cap0p05 | -0.0030 | -0.0006 | -0.0014 | 0.8880 | 0.8240 | 0.5860 | 0.8640 | 0.4680 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s1_cap0p02 | -0.0009 | -0.0005 | -0.0033 | 0.5980 | 0.9040 | 0.7040 | 0.8500 | 0.3760 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p75_cap0p08 | -0.0029 | -0.0006 | -0.0014 | 0.8680 | 0.7980 | 0.5860 | 0.8440 | 0.4440 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p75_cap0p05 | -0.0033 | -0.0006 | -0.0024 | 0.9120 | 0.7880 | 0.6040 | 0.8360 | 0.4800 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s0p75_cap0p02 | -0.0014 | -0.0005 | -0.0026 | 0.7060 | 0.8800 | 0.6200 | 0.8340 | 0.3960 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s1_cap0p02 | -0.0012 | -0.0005 | -0.0037 | 0.6660 | 0.8600 | 0.7120 | 0.8320 | 0.4260 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s0p75_cap0p02 | -0.0016 | -0.0005 | -0.0032 | 0.7520 | 0.8380 | 0.6500 | 0.8320 | 0.4240 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p75_cap0p08 | -0.0032 | -0.0006 | -0.0024 | 0.8980 | 0.7520 | 0.6040 | 0.8120 | 0.4540 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s0p75_cap0p03 | -0.0023 | -0.0002 | -0.0018 | 0.8480 | 0.6880 | 0.5740 | 0.7920 | 0.3580 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p02 | 0.0013 | -0.0004 | -0.0070 | 0.2880 | 0.8400 | 0.8820 | 0.7900 | 0.2400 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s1_cap0p03 | -0.0027 | -0.0002 | -0.0015 | 0.8640 | 0.6640 | 0.5640 | 0.7820 | 0.3460 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p03 | 0.0008 | -0.0005 | -0.0061 | 0.4140 | 0.8440 | 0.7960 | 0.7760 | 0.3060 |
| validation_oof_row | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p03 | 0.0009 | -0.0004 | -0.0048 | 0.3760 | 0.8220 | 0.7820 | 0.7720 | 0.2520 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s0p75_cap0p03 | -0.0027 | -0.0003 | -0.0024 | 0.8520 | 0.6460 | 0.5840 | 0.7700 | 0.3480 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s1_cap0p02 | 0.0007 | -0.0004 | -0.0083 | 0.3340 | 0.8380 | 0.8300 | 0.7660 | 0.2660 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s1_cap0p02 | 0.0004 | -0.0004 | -0.0071 | 0.4140 | 0.8180 | 0.7640 | 0.7620 | 0.2620 |
| validation_oof_row | row_subsample_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p08 | -0.0026 | 0.0001 | -0.0024 | 0.8740 | 0.4540 | 0.6640 | 0.7600 | 0.2760 |
| validation_oof_row | row_subsample_80pct | hcoef29_risk_guarded_component_s0p75_cap0p08 | 0.0002 | -0.0007 | -0.0080 | 0.4840 | 0.8040 | 0.6940 | 0.7520 | 0.2720 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s1_cap0p05 | -0.0026 | -0.0005 | 0.0013 | 0.8260 | 0.7580 | 0.3500 | 0.7500 | 0.2440 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s1_cap0p05 | -0.0031 | -0.0005 | -0.0000 | 0.8420 | 0.7060 | 0.4460 | 0.7480 | 0.2800 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s0p75_cap0p02 | 0.0010 | -0.0004 | -0.0075 | 0.2680 | 0.8320 | 0.8260 | 0.7460 | 0.2140 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s1_cap0p03 | -0.0028 | -0.0002 | -0.0022 | 0.8340 | 0.6160 | 0.5860 | 0.7360 | 0.3420 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p02 | -0.0005 | -0.0002 | -0.0031 | 0.5820 | 0.7040 | 0.7260 | 0.7360 | 0.3140 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p75_cap0p02 | 0.0007 | -0.0004 | -0.0064 | 0.3700 | 0.7960 | 0.7560 | 0.7360 | 0.2220 |
| validation_oof_row | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p03 | 0.0007 | -0.0005 | -0.0049 | 0.4180 | 0.7760 | 0.7720 | 0.7320 | 0.2660 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p02 | 0.0010 | -0.0004 | -0.0059 | 0.3000 | 0.8080 | 0.7740 | 0.7320 | 0.1900 |
| validation_oof_row | artist_holdout_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p08 | -0.0029 | 0.0001 | -0.0027 | 0.9040 | 0.4260 | 0.6340 | 0.7240 | 0.2780 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s0p75_cap0p05 | -0.0015 | -0.0003 | -0.0001 | 0.7480 | 0.6620 | 0.5940 | 0.7220 | 0.3260 |
| validation_oof_artist | row_subsample_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p02 | -0.0003 | -0.0002 | -0.0028 | 0.5480 | 0.7280 | 0.7160 | 0.7200 | 0.3340 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p03 | 0.0005 | -0.0005 | -0.0051 | 0.4320 | 0.8080 | 0.7100 | 0.7200 | 0.2600 |
| validation_oof_row | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p02 | 0.0019 | -0.0003 | -0.0061 | 0.2000 | 0.7880 | 0.8180 | 0.7180 | 0.1360 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s0p75_cap0p08 | -0.0011 | -0.0006 | 0.0022 | 0.6720 | 0.7700 | 0.4440 | 0.7100 | 0.2440 |
| validation_oof_row | row_subsample_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p05 | -0.0020 | 0.0002 | -0.0024 | 0.8200 | 0.3900 | 0.6640 | 0.7100 | 0.2180 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p08 | -0.0006 | -0.0004 | -0.0020 | 0.5640 | 0.7340 | 0.6460 | 0.7080 | 0.2820 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p75_cap0p05 | -0.0017 | -0.0004 | 0.0004 | 0.7500 | 0.6740 | 0.5540 | 0.7040 | 0.3200 |
| validation_oof_artist | row_subsample_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p08 | -0.0001 | -0.0003 | -0.0017 | 0.5240 | 0.7300 | 0.6400 | 0.7000 | 0.2720 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s0p75_cap0p08 | -0.0017 | -0.0001 | -0.0019 | 0.7060 | 0.5320 | 0.6760 | 0.6980 | 0.2820 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p03 | -0.0004 | -0.0003 | -0.0019 | 0.5680 | 0.7140 | 0.6460 | 0.6920 | 0.2920 |
| validation_oof_row | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p75_cap0p08 | -0.0003 | -0.0007 | -0.0058 | 0.5240 | 0.7380 | 0.6120 | 0.6920 | 0.2300 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p75_cap0p08 | -0.0012 | -0.0007 | 0.0024 | 0.6540 | 0.7460 | 0.4720 | 0.6900 | 0.2440 |
| validation_oof_row | artist_holdout_80pct | hcoef29_risk_guarded_component_s1_cap0p02 | 0.0006 | -0.0002 | -0.0079 | 0.3680 | 0.6600 | 0.8220 | 0.6900 | 0.2080 |
| validation_oof_row | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p02 | 0.0016 | -0.0003 | -0.0059 | 0.2740 | 0.7480 | 0.8060 | 0.6820 | 0.1760 |
| validation_oof_row | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p75_cap0p02 | 0.0011 | -0.0002 | -0.0074 | 0.3300 | 0.6700 | 0.8180 | 0.6800 | 0.1860 |
| validation_oof_artist | row_subsample_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p03 | 0.0000 | -0.0003 | -0.0016 | 0.5200 | 0.7260 | 0.6400 | 0.6780 | 0.2780 |
| validation_oof_row | row_subsample_80pct | hcoef29_risk_guarded_component_s0p75_cap0p02 | 0.0016 | -0.0002 | -0.0082 | 0.2540 | 0.6980 | 0.8460 | 0.6740 | 0.1720 |
| validation_oof_row | artist_holdout_80pct | hcoef29_all_lowdim_signal_s0p5_cap0p05 | -0.0022 | 0.0002 | -0.0027 | 0.8360 | 0.3820 | 0.6340 | 0.6700 | 0.2340 |
| validation_oof_row | row_subsample_80pct | hcoef29_risk_guarded_component_s1_cap0p02 | 0.0011 | -0.0002 | -0.0088 | 0.2800 | 0.6820 | 0.8520 | 0.6660 | 0.1920 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s0p75_cap0p08 | -0.0021 | -0.0001 | -0.0022 | 0.7400 | 0.5100 | 0.6520 | 0.6620 | 0.3020 |

## 7. Huber 계수 해석

| candidate | model_label | feature_set | feature | coefficient | direction | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | artist_oof_full | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | artist_oof_full | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | artist_oof_full | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p05 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | artist_oof_full | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p5_cap0p08 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | artist_oof_full | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p02 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | svc_group_n_log | -0.0062 | 가격 하락 보정 방향 | 유사 작품 표본 수의 로그값; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | pred_spread_numeric | -0.0052 | 가격 하락 보정 방향 | 주요 후보 예측값 사이의 벌어짐; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | quantile_width | -0.0036 | 가격 하락 보정 방향 | 예측 가격 범위가 넓은 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | current_delta | 0.0011 | 가격 상승 보정 방향 | 기존 70:30 후보가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | current_delta_safe | 0.0011 | 가격 상승 보정 방향 | risk가 낮을 때의 기존 70:30 후보 이동분; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | h26_fixed_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 fixed 확인 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | h26_direct_delta | 0.0000 | 가격 하락 보정 방향 | HCOEF26 direct 후보의 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | artist_oof_full | all_lowdim_signal | risk_norm | 0.0000 | 가격 하락 보정 방향 | HCOEF28 Huber risk model의 정규화된 위험도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta_reliable | -0.1250 | 가격 하락 보정 방향 | 유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | svc_delta | 0.0377 | 가격 상승 보정 방향 | 유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta | -0.0364 | 가격 하락 보정 방향 | 오차 안정화 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | ppv8_delta_safe | -0.0364 | 가격 하락 보정 방향 | risk가 낮을 때의 오차 안정화 component 이동분; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | l10_delta | -0.0165 | 가격 하락 보정 방향 | quantile 계열 component가 stable보다 높거나 낮게 보는 정도; 계수 기준 높일 때 실제 가격이 stable보다 낮았던 방향 |
| hcoef29_all_lowdim_signal_s0p75_cap0p03 | row_validation_full_for_fixed_and_0604 | all_lowdim_signal | is_svc_artist_fallback | 0.0081 | 가격 상승 보정 방향 | 세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부; 계수 기준 높일 때 실제 가격이 stable보다 높았던 방향 |

## 8. 잔차/큰 오차 구간

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
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_level | medium_support_size | 66 | 0.4286 | 0.4756 | 1.0263 | 0.9305 | 0.3485 | 0.5909 | 4 | 14 | 0.1585 | 0.1045 | 0.0566 | -0.0165 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | gap_band | gap_020_plus | 402 | 0.4286 | 0.5016 | 0.9999 | 1.7930 | 0.3184 | 0.5622 | 17 | 121 | 0.1585 | 0.1305 | 0.0302 | 0.2662 | 0.4378 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | pred_spread_band | spread_extreme | 438 | 0.4382 | 0.4982 | 0.9968 | 1.7307 | 0.3288 | 0.5479 | 15 | 136 | 0.1681 | 0.1271 | 0.0271 | 0.2833 | 0.4521 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | qwidth_band | qwidth_extreme | 301 | 0.3842 | 0.4363 | 0.9959 | 1.9658 | 0.4086 | 0.6246 | 7 | 99 | 0.1140 | 0.0652 | 0.0262 | 0.3466 | 0.3754 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | qwidth_band | qwidth_high | 185 | 0.2443 | 0.3696 | 0.9863 | 0.9868 | 0.5514 | 0.7459 | 6 | 23 | -0.0259 | -0.0015 | 0.0166 | 0.0584 | 0.2541 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_n_band | n_5_9 | 435 | 0.2361 | 0.3311 | 0.9863 | 1.6306 | 0.5678 | 0.7563 | 9 | 62 | -0.0341 | -0.0400 | 0.0166 | 0.0686 | 0.2437 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_level | artist | 412 | 0.3079 | 0.3754 | 0.9863 | 1.5783 | 0.4830 | 0.7451 | 13 | 59 | 0.0377 | 0.0043 | 0.0166 | 0.0686 | 0.2549 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_n_band | n_50_plus | 105 | 0.5431 | 0.5355 | 0.9844 | 1.0310 | 0.2667 | 0.4286 | 5 | 42 | 0.2730 | 0.1643 | 0.0147 | 0.5477 | 0.5714 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | service_confidence_tier | high | 22 | 0.5687 | 0.5371 | 0.9745 | 0.8050 | 0.3636 | 0.4545 | 1 | 4 | 0.2985 | 0.1660 | 0.0048 | 0.1403 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | service_confidence_tier | low | 499 | 0.2689 | 0.3521 | 0.9727 | 1.5787 | 0.5271 | 0.7234 | 9 | 89 | -0.0013 | -0.0190 | 0.0030 | 0.0974 | 0.2766 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | service_confidence_tier | medium | 308 | 0.2646 | 0.3900 | 0.9417 | 0.7098 | 0.5162 | 0.7078 | 12 | 53 | -0.0056 | 0.0189 | -0.0280 | 0.0236 | 0.2922 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_n_band | n_20_49 | 90 | 0.1922 | 0.3367 | 0.9329 | 0.6243 | 0.5889 | 0.7667 | 3 | 12 | -0.0780 | -0.0345 | -0.0368 | 0.0734 | 0.2333 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | qwidth_band | qwidth_mid | 242 | 0.2231 | 0.3348 | 0.9111 | 0.4655 | 0.5661 | 0.7438 | 9 | 21 | -0.0470 | -0.0363 | -0.0586 | -0.0083 | 0.2562 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | gap_band | gap_010_020 | 128 | 0.2214 | 0.3328 | 0.9111 | 0.5128 | 0.5625 | 0.6875 | 1 | 16 | -0.0488 | -0.0383 | -0.0586 | -0.0364 | 0.3125 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | gap_band | gap_005_010 | 125 | 0.1437 | 0.2483 | 0.9105 | 0.7516 | 0.7840 | 0.9040 | 3 | 3 | -0.1265 | -0.1228 | -0.0592 | 0.0405 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_n_band | n_10_19 | 199 | 0.2898 | 0.3875 | 0.8674 | 0.7429 | 0.5126 | 0.7337 | 5 | 30 | 0.0196 | 0.0163 | -0.1023 | 0.0236 | 0.2663 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_level | medium_size | 18 | 0.7489 | 0.6604 | 0.8639 | 1.1891 | 0.1111 | 0.2222 | 1 | 12 | 0.4787 | 0.2893 | -0.1058 | 1.3200 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_level | artist_size | 224 | 0.1922 | 0.3444 | 0.8537 | 0.9960 | 0.5982 | 0.7143 | 4 | 45 | -0.0780 | -0.0267 | -0.1160 | 0.0731 | 0.2857 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_level | global | 18 | 0.6252 | 0.6647 | 0.8488 | 1.2214 | 0.0000 | 0.0556 | 0 | 14 | 0.3551 | 0.2936 | -0.1209 | 0.9348 | 0.9444 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | qwidth_band | qwidth_low | 101 | 0.1614 | 0.2667 | 0.8434 | 0.4142 | 0.6733 | 0.8218 | 0 | 3 | -0.1087 | -0.1044 | -0.1263 | -0.0109 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | pred_spread_band | spread_high | 124 | 0.2065 | 0.2702 | 0.8372 | 0.7686 | 0.6210 | 0.8548 | 3 | 3 | -0.0637 | -0.1009 | -0.1325 | -0.0493 | 0.1452 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | svc_group_level | artist_medium_support_size | 91 | 0.1614 | 0.2263 | 0.8026 | 0.7783 | 0.7912 | 0.8571 | 0 | 2 | -0.1087 | -0.1448 | -0.1671 | -0.0116 | 0.1429 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | pred_spread_band | spread_low_mid | 267 | 0.1199 | 0.2094 | 0.6391 | 0.3232 | 0.7828 | 0.9101 | 4 | 7 | -0.1503 | -0.1617 | -0.3306 | 0.0199 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | gap_band | gap_000_003 | 119 | 0.0928 | 0.1858 | 0.5240 | 0.3111 | 0.7815 | 0.9244 | 1 | 5 | -0.1774 | -0.1853 | -0.4457 | 0.0236 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef29_all_lowdim_signal_s0p5_cap0p03 | gap_band | gap_003_005 | 55 | 0.0951 | 0.1862 | 0.5042 | 0.2982 | 0.7091 | 0.9455 | 0 | 1 | -0.1750 | -0.1849 | -0.4655 | 0.0028 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_level | medium_support_size | 66 | 0.4349 | 0.4851 | 1.0441 | 0.9382 | 0.3485 | 0.5909 | 4 | 14 | 0.1650 | 0.1113 | 0.0650 | -0.0265 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | gap_band | gap_020_plus | 402 | 0.4449 | 0.5042 | 0.9999 | 1.7958 | 0.3159 | 0.5597 | 17 | 127 | 0.1750 | 0.1304 | 0.0208 | 0.2730 | 0.4403 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | pred_spread_band | spread_extreme | 438 | 0.4456 | 0.5019 | 0.9969 | 1.7339 | 0.3196 | 0.5365 | 15 | 142 | 0.1757 | 0.1281 | 0.0178 | 0.2924 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_n_band | n_50_plus | 105 | 0.5427 | 0.5443 | 0.9961 | 1.0497 | 0.2667 | 0.4476 | 5 | 42 | 0.2728 | 0.1705 | 0.0170 | 0.5707 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | qwidth_band | qwidth_extreme | 301 | 0.3764 | 0.4382 | 0.9960 | 1.9682 | 0.4053 | 0.6312 | 7 | 99 | 0.1065 | 0.0644 | 0.0169 | 0.3490 | 0.3688 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | service_confidence_tier | high | 22 | 0.5886 | 0.5506 | 0.9944 | 0.8150 | 0.3636 | 0.4545 | 1 | 4 | 0.3187 | 0.1768 | 0.0153 | 0.1466 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_n_band | n_5_9 | 435 | 0.2349 | 0.3317 | 0.9867 | 1.6295 | 0.5678 | 0.7655 | 9 | 62 | -0.0349 | -0.0420 | 0.0076 | 0.0595 | 0.2345 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_level | artist | 412 | 0.3140 | 0.3767 | 0.9867 | 1.5781 | 0.4879 | 0.7427 | 13 | 61 | 0.0441 | 0.0029 | 0.0076 | 0.0857 | 0.2573 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | qwidth_band | qwidth_high | 185 | 0.2323 | 0.3733 | 0.9867 | 0.9908 | 0.5514 | 0.7297 | 6 | 27 | -0.0376 | -0.0004 | 0.0075 | 0.0671 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | service_confidence_tier | low | 499 | 0.2617 | 0.3531 | 0.9717 | 1.5792 | 0.5271 | 0.7355 | 9 | 89 | -0.0082 | -0.0206 | -0.0074 | 0.0910 | 0.2645 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | service_confidence_tier | medium | 308 | 0.2642 | 0.3945 | 0.9411 | 0.7203 | 0.5130 | 0.6883 | 12 | 59 | -0.0056 | 0.0208 | -0.0380 | 0.0304 | 0.3117 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | gap_band | gap_005_010 | 125 | 0.1566 | 0.2511 | 0.9231 | 0.7550 | 0.7680 | 0.9040 | 3 | 3 | -0.1132 | -0.1226 | -0.0560 | 0.0385 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_n_band | n_20_49 | 90 | 0.2076 | 0.3395 | 0.9100 | 0.6289 | 0.5889 | 0.7556 | 3 | 13 | -0.0622 | -0.0343 | -0.0692 | 0.0589 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | qwidth_band | qwidth_mid | 242 | 0.2347 | 0.3380 | 0.8833 | 0.4713 | 0.5702 | 0.7479 | 9 | 23 | -0.0351 | -0.0357 | -0.0958 | 0.0016 | 0.2521 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | gap_band | gap_010_020 | 128 | 0.2199 | 0.3374 | 0.8783 | 0.5195 | 0.5625 | 0.6953 | 1 | 16 | -0.0499 | -0.0364 | -0.1008 | -0.0265 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_level | medium_size | 18 | 0.7622 | 0.6738 | 0.8754 | 1.2317 | 0.1111 | 0.2222 | 1 | 12 | 0.4923 | 0.3000 | -0.1037 | 1.3700 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_n_band | n_10_19 | 199 | 0.2862 | 0.3912 | 0.8649 | 0.7519 | 0.5075 | 0.7085 | 5 | 35 | 0.0164 | 0.0174 | -0.1143 | 0.0331 | 0.2915 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_level | artist_size | 224 | 0.1930 | 0.3482 | 0.8512 | 1.0021 | 0.5893 | 0.6964 | 4 | 49 | -0.0768 | -0.0255 | -0.1279 | 0.0564 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_level | global | 18 | 0.6435 | 0.6649 | 0.8484 | 1.2450 | 0.0000 | 0.1667 | 0 | 14 | 0.3736 | 0.2912 | -0.1307 | 0.9848 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | qwidth_band | qwidth_low | 101 | 0.1738 | 0.2683 | 0.8155 | 0.4159 | 0.6634 | 0.8218 | 0 | 3 | -0.0961 | -0.1055 | -0.1636 | 0.0086 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | pred_spread_band | spread_high | 124 | 0.2021 | 0.2751 | 0.8085 | 0.7720 | 0.6210 | 0.8952 | 3 | 3 | -0.0678 | -0.0987 | -0.1706 | -0.0456 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | svc_group_level | artist_medium_support_size | 91 | 0.1738 | 0.2258 | 0.7799 | 0.7747 | 0.7802 | 0.8901 | 0 | 2 | -0.0961 | -0.1479 | -0.1992 | -0.0080 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | pred_spread_band | spread_low_mid | 267 | 0.1147 | 0.2094 | 0.6386 | 0.3245 | 0.7940 | 0.9101 | 4 | 7 | -0.1551 | -0.1644 | -0.3405 | 0.0166 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | gap_band | gap_000_003 | 119 | 0.1011 | 0.1882 | 0.5291 | 0.3136 | 0.7983 | 0.9244 | 1 | 5 | -0.1688 | -0.1855 | -0.4500 | 0.0336 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p02 | gap_band | gap_003_005 | 55 | 0.0852 | 0.1854 | 0.5183 | 0.2995 | 0.7091 | 0.9455 | 0 | 1 | -0.1846 | -0.1884 | -0.4608 | 0.0118 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_level | medium_support_size | 66 | 0.4405 | 0.4801 | 1.0263 | 0.9403 | 0.3485 | 0.5909 | 4 | 14 | 0.1707 | 0.1067 | 0.0572 | -0.0165 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | gap_band | gap_020_plus | 402 | 0.4405 | 0.5042 | 0.9999 | 1.7965 | 0.3159 | 0.5597 | 17 | 127 | 0.1707 | 0.1308 | 0.0309 | 0.2730 | 0.4403 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | pred_spread_band | spread_extreme | 438 | 0.4511 | 0.5016 | 0.9969 | 1.7345 | 0.3196 | 0.5365 | 15 | 142 | 0.1812 | 0.1283 | 0.0279 | 0.2924 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | qwidth_band | qwidth_extreme | 301 | 0.3764 | 0.4383 | 0.9960 | 1.9690 | 0.4053 | 0.6312 | 7 | 99 | 0.1065 | 0.0650 | 0.0269 | 0.3490 | 0.3688 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_n_band | n_5_9 | 435 | 0.2349 | 0.3317 | 0.9867 | 1.6295 | 0.5678 | 0.7655 | 9 | 62 | -0.0349 | -0.0416 | 0.0177 | 0.0595 | 0.2345 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_level | artist | 412 | 0.3140 | 0.3767 | 0.9867 | 1.5781 | 0.4879 | 0.7427 | 13 | 61 | 0.0441 | 0.0033 | 0.0177 | 0.0857 | 0.2573 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | qwidth_band | qwidth_high | 185 | 0.2323 | 0.3725 | 0.9867 | 0.9906 | 0.5514 | 0.7297 | 6 | 27 | -0.0376 | -0.0008 | 0.0176 | 0.0671 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_n_band | n_50_plus | 105 | 0.5472 | 0.5411 | 0.9845 | 1.0535 | 0.2667 | 0.4476 | 5 | 42 | 0.2774 | 0.1677 | 0.0155 | 0.5807 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | service_confidence_tier | high | 22 | 0.5886 | 0.5460 | 0.9745 | 0.8135 | 0.3636 | 0.4545 | 1 | 4 | 0.3188 | 0.1727 | 0.0055 | 0.1466 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | service_confidence_tier | low | 499 | 0.2617 | 0.3531 | 0.9717 | 1.5796 | 0.5271 | 0.7355 | 9 | 89 | -0.0082 | -0.0202 | 0.0027 | 0.0910 | 0.2645 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | service_confidence_tier | medium | 308 | 0.2642 | 0.3938 | 0.9361 | 0.7209 | 0.5130 | 0.6883 | 12 | 59 | -0.0056 | 0.0204 | -0.0330 | 0.0311 | 0.3117 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_n_band | n_20_49 | 90 | 0.2076 | 0.3395 | 0.9100 | 0.6289 | 0.5889 | 0.7556 | 3 | 13 | -0.0622 | -0.0339 | -0.0591 | 0.0589 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | gap_band | gap_005_010 | 125 | 0.1566 | 0.2505 | 0.9075 | 0.7547 | 0.7680 | 0.9040 | 3 | 3 | -0.1132 | -0.1228 | -0.0616 | 0.0385 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | qwidth_band | qwidth_mid | 242 | 0.2347 | 0.3372 | 0.8833 | 0.4710 | 0.5702 | 0.7479 | 9 | 23 | -0.0351 | -0.0362 | -0.0858 | 0.0016 | 0.2521 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | gap_band | gap_010_020 | 128 | 0.2199 | 0.3358 | 0.8783 | 0.5193 | 0.5625 | 0.6953 | 1 | 16 | -0.0499 | -0.0375 | -0.0907 | -0.0173 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_level | medium_size | 18 | 0.7623 | 0.6733 | 0.8739 | 1.2364 | 0.1111 | 0.2222 | 1 | 12 | 0.4924 | 0.2999 | -0.0951 | 1.3735 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_n_band | n_10_19 | 199 | 0.2862 | 0.3912 | 0.8649 | 0.7519 | 0.5075 | 0.7085 | 5 | 35 | 0.0164 | 0.0178 | -0.1042 | 0.0331 | 0.2915 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_level | artist_size | 224 | 0.1930 | 0.3482 | 0.8512 | 1.0021 | 0.5893 | 0.6964 | 4 | 49 | -0.0768 | -0.0251 | -0.1178 | 0.0564 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_level | global | 18 | 0.6426 | 0.6650 | 0.8499 | 1.2530 | 0.0000 | 0.1667 | 0 | 14 | 0.3728 | 0.2916 | -0.1191 | 0.9948 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | qwidth_band | qwidth_low | 101 | 0.1738 | 0.2680 | 0.8155 | 0.4158 | 0.6634 | 0.8218 | 0 | 3 | -0.0961 | -0.1054 | -0.1536 | 0.0086 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | pred_spread_band | spread_high | 124 | 0.2021 | 0.2739 | 0.8085 | 0.7717 | 0.6210 | 0.8952 | 3 | 3 | -0.0678 | -0.0995 | -0.1606 | -0.0456 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | svc_group_level | artist_medium_support_size | 91 | 0.1738 | 0.2259 | 0.7799 | 0.7747 | 0.7802 | 0.8901 | 0 | 2 | -0.0961 | -0.1475 | -0.1891 | -0.0080 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | pred_spread_band | spread_low_mid | 267 | 0.1139 | 0.2092 | 0.6382 | 0.3244 | 0.7940 | 0.9101 | 4 | 7 | -0.1559 | -0.1642 | -0.3309 | 0.0186 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | gap_band | gap_000_003 | 119 | 0.1011 | 0.1879 | 0.5291 | 0.3135 | 0.7983 | 0.9244 | 1 | 5 | -0.1688 | -0.1855 | -0.4400 | 0.0336 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef29_h26_candidate_delta_s0p5_cap0p03 | gap_band | gap_003_005 | 55 | 0.0852 | 0.1850 | 0.5183 | 0.2993 | 0.7091 | 0.9455 | 0 | 1 | -0.1846 | -0.1884 | -0.4507 | 0.0118 | 0.0545 |

## 9. 다음 방향

- 반복 검증 후보가 있으면 HCOEF30에서 후보 수를 줄이고 artist-level holdout을 더 강하게 재검증.
- fixed 확인 후보만 있으면 cap/strength를 더 세밀하게 조정하지 말고, 계수 방향을 기준으로 원인 구간을 별도 분석.
- 새 후보가 없으면 Huber 계수 기반 점 보정보다 가격 범위/신뢰도 정책을 우선 반영.

## 10. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/repeated_iteration_metrics.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/residual_analysis.csv`
- `outputs/selected_candidates.csv`
- `outputs/policy_configurations.csv`
- `artifacts/experiment_config.json`