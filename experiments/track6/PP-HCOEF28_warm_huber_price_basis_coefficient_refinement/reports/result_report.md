# PP-HCOEF28 Warm Huber p95 risk-aware shrinkage 실험

- 작성일: 2026-06-08 05:59
- 목적: HCOEF26/27 후보 이동분을 그대로 쓰지 않고, Huber로 예측한 큰 오차 위험도에 따라 이동폭을 줄여 p95와 반복 안정성을 개선할 수 있는지 확인.
- 후보 선택: validation OOF 기반 risk Huber와 반복 split/artist holdout 기준.
- fixed test와 0604는 확인용으로만 사용.

## 1. 실행 결론

- 상위 확인 후보: `hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1` (판단: fixed 확인 후보, fixed test `0.1371/0.2727/0.8064`, repeated min any2 `0.4540`, min all3 `0.1080`).
- 현재 기준 후보 `hcoef_stable` fixed test: `0.1388/0.2730/0.8064`.
- repeated all3/any2 gate를 통과하지 못하면 운영 후보가 아니라 연구 후보로만 유지.

## 2. 보정 공식

- 위험도 학습식: `risk = HuberRegressor(risk_features, abs(actual_log - hcoef_stable_log))`.
- 위험도 정규화: validation row OOF risk의 q10~q90 구간을 0~1로 변환.
- 적용식: `corrected_log = hcoef_stable_log + weight * (source_candidate_log - hcoef_stable_log)`.
- 기본 weight: `floor + (1 - floor) * (1 - alpha * risk_norm)`.
- high-risk guard: risk가 validation q80/q90 이상이면 weight를 0 또는 0.25 이하로 제한.
- low-risk boost: risk가 validation q33 이하이면 일부 후보에서 weight를 25%만큼 키움.

## 3. 사용한 source 후보

| source_candidate | source_tag | source_reason |
| --- | --- | --- |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | HCOEF26/HCOEF27 fixed test 2개 지표 개선 + p95 방어 후보 |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | h26_direct_guarded | HCOEF27 반복 any2 개선 확률이 가장 높지만 fixed MdAPE가 악화된 후보 |

## 4. 최종 선택표

| candidate | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | repeated_min_any2_improve_prob | repeated_min_all3_improve_prob | fixed_test_p95_guard | stress0604_p95_guard | test_mean_move_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | True | True |  |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4540 | 0.1080 | True | True |  |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6420 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3940 | 0.0860 | True | True | 0.7119 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80floor025_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6420 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4220 | 0.0900 | True | True | 0.7770 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_noguard_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6420 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4260 | 0.0880 | True | True | 0.9424 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q90zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6420 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4260 | 0.0880 | True | True | 0.8285 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6432 | 0.1260 | 0.2082 | 0.6422 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3820 | 0.0860 | True | True | 0.6980 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80floor025_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6432 | 0.1260 | 0.2082 | 0.6422 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4220 | 0.0880 | True | True | 0.7631 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | fixed 확인 후보 | 0.1259 | 0.2082 | 0.6432 | 0.1260 | 0.2082 | 0.6422 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4260 | 0.0880 | True | True | 0.9136 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q90zero_boost0 | fixed 확인 후보 | 0.1259 | 0.2082 | 0.6432 | 0.1260 | 0.2082 | 0.6422 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4260 | 0.0880 | True | True | 0.8079 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3800 | 0.0860 | True | True | 0.6841 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q80zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3800 | 0.0860 | True | True | 0.6841 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q80floor025_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4120 | 0.0900 | True | True | 0.7492 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q80floor025_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4120 | 0.0900 | True | True | 0.7492 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80zero_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6420 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2760 | 0.0480 | True | True | 0.8011 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_noguard_boost0 | fixed 확인 후보 | 0.1259 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4200 | 0.0900 | True | True | 0.8849 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q90zero_boost0 | fixed 확인 후보 | 0.1259 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4200 | 0.0900 | True | True | 0.7872 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_noguard_boost0 | fixed 확인 후보 | 0.1259 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4200 | 0.0900 | True | True | 0.8849 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q90zero_boost0 | fixed 확인 후보 | 0.1259 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4200 | 0.0900 | True | True | 0.7872 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80floor025_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6420 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2880 | 0.0500 | True | True | 0.8662 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_noguard_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6420 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2900 | 0.0520 | True | True | 1.0316 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q90zero_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6420 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2900 | 0.0520 | True | True | 0.9178 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80zero_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6432 | 0.1260 | 0.2082 | 0.6422 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2700 | 0.0480 | True | True | 0.7867 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80floor025_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6432 | 0.1260 | 0.2082 | 0.6422 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2820 | 0.0500 | True | True | 0.8518 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6432 | 0.1260 | 0.2082 | 0.6422 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2880 | 0.0520 | True | True | 1.0024 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q90zero_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6432 | 0.1260 | 0.2082 | 0.6422 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2880 | 0.0520 | True | True | 0.8966 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2660 | 0.0460 | True | True | 0.7724 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q80zero_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2660 | 0.0460 | True | True | 0.7724 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q80floor025_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2780 | 0.0500 | True | True | 0.8374 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q80floor025_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2727 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2780 | 0.0500 | True | True | 0.8374 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_noguard_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2880 | 0.0520 | True | True | 0.9731 |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q90zero_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2880 | 0.0520 | True | True | 0.8755 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_noguard_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2880 | 0.0520 | True | True | 0.9731 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q90zero_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6435 | 0.1260 | 0.2082 | 0.6423 | 0.1372 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2880 | 0.0520 | True | True | 0.8755 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q80zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3700 | 0.0760 | True | True | 0.6563 |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q80zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3700 | 0.0760 | True | True | 0.6563 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q80floor025_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3980 | 0.0840 | True | True | 0.7214 |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q80floor025_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3980 | 0.0840 | True | True | 0.7214 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_noguard_boost0 | fixed 확인 후보 | 0.1258 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4160 | 0.0900 | True | True | 0.8273 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q90zero_boost0 | fixed 확인 후보 | 0.1258 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4160 | 0.0900 | True | True | 0.7459 |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_noguard_boost0 | fixed 확인 후보 | 0.1258 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4160 | 0.0900 | True | True | 0.8273 |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q90zero_boost0 | fixed 확인 후보 | 0.1258 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4160 | 0.0900 | True | True | 0.7459 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q80zero_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2280 | 0.0380 | True | True | 0.7436 |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q80zero_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2280 | 0.0380 | True | True | 0.7436 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q80floor025_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2300 | 0.0400 | True | True | 0.8087 |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q80floor025_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2300 | 0.0400 | True | True | 0.8087 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_noguard_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2440 | 0.0420 | True | True | 0.9145 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q90zero_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2440 | 0.0420 | True | True | 0.8332 |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_noguard_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2440 | 0.0420 | True | True | 0.9145 |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q90zero_boost0p25 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6440 | 0.1260 | 0.2082 | 0.6427 | 0.1373 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2440 | 0.0420 | True | True | 0.8332 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q80zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3600 | 0.0760 | True | True | 0.6285 |
| hcoef28_h26_lowrisk_fixed_a1_f0p5_q80zero_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3600 | 0.0760 | True | True | 0.6285 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q80floor025_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3900 | 0.0800 | True | True | 0.6936 |
| hcoef28_h26_lowrisk_fixed_a1_f0p5_q80floor025_boost0 | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.3900 | 0.0800 | True | True | 0.6936 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_noguard_boost0 | fixed 확인 후보 | 0.1256 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4100 | 0.0880 | True | True | 0.7697 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q90zero_boost0 | fixed 확인 후보 | 0.1256 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4100 | 0.0880 | True | True | 0.7046 |
| hcoef28_h26_lowrisk_fixed_a1_f0p5_noguard_boost0 | fixed 확인 후보 | 0.1256 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4100 | 0.0880 | True | True | 0.7697 |
| hcoef28_h26_lowrisk_fixed_a1_f0p5_q90zero_boost0 | fixed 확인 후보 | 0.1256 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4100 | 0.0880 | True | True | 0.7046 |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q80zero_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2160 | 0.0340 | True | True | 0.7148 |
| hcoef28_h26_lowrisk_fixed_a1_f0p5_q80zero_boost0p25 | fixed 확인 후보 | 0.1266 | 0.2082 | 0.6444 | 0.1260 | 0.2082 | 0.6431 | 0.1375 | 0.2728 | 0.8064 | 0.2731 | 0.3746 | 0.9835 | 0.2160 | 0.0340 | True | True | 0.7148 |

## 5. Scope별 metrics

| scope | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mean_move_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |  |
| 0604_stress | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 |  |
| 0604_stress | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 |  |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9699 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1699 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9520 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1520 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9433 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1433 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9500 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1500 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p25_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9774 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p25_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1777 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p25_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9575 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p25_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1577 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p25_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9487 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p25_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1490 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p25_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9559 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p25_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1561 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9849 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1855 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p5_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9629 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p5_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1635 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p5_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9542 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p5_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1547 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9617 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1623 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9398 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1386 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9303 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1291 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9216 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1204 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9265 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1253 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p25_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9548 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p25_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1542 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p25_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9412 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p25_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1406 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p25_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9324 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p25_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1318 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p25_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9382 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p25_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1376 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p5_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9699 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p5_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1699 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p5_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9520 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p5_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1520 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p5_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9433 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p5_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1433 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p5_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9500 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p5_f0p5_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1500 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9097 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1073 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9086 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1062 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.8998 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.0975 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9030 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1007 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p25_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9322 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p25_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1308 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p25_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9249 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p25_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1234 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p25_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9161 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p25_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1146 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p25_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9206 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p25_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1192 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p5_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9548 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p5_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1542 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p5_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9412 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p5_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1406 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p5_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9324 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p5_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1318 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p5_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9382 |
| 0604_stress | hcoef28_h26_direct_guarded_a0p75_f0p5_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1376 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.8795 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.0760 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.8795 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.0760 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.8781 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.0746 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.8795 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.0760 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p25_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9097 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p25_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1073 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p25_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9086 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p25_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1062 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p25_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.8998 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p25_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.0975 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p25_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9030 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p25_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1007 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p5_noguard_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9398 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p5_noguard_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1386 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p5_q80floor025_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9303 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p5_q80floor025_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1291 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p5_q80zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9216 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p5_q80zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1204 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p5_q90zero_boost0 | 0.2775 | 0.3749 | 0.9835 | 1.3078 | 0.0045 | 0.0006 | 0.0000 | 0.9265 |
| 0604_stress | hcoef28_h26_direct_guarded_a1_f0p5_q90zero_boost0p25 | 0.2775 | 0.3751 | 0.9835 | 1.3079 | 0.0045 | 0.0008 | 0.0000 | 1.1253 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0_noguard_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9699 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0_noguard_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1699 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80floor025_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9520 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80floor025_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1520 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9433 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1433 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0_q90zero_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9500 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0_q90zero_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1500 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9774 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1777 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80floor025_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9575 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80floor025_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1577 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80zero_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9487 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80zero_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1490 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q90zero_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9559 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q90zero_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1561 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p5_noguard_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9849 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p5_noguard_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1855 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80floor025_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9629 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80floor025_boost0p25 | 0.2731 | 0.3746 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 1.1635 |
| 0604_stress | hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80zero_boost0 | 0.2731 | 0.3745 | 0.9835 | 1.3078 | 0.0000 | 0.0002 | 0.0000 | 0.9542 |

## 6. 반복 split/artist holdout 요약

| source_scope | validation_scheme | candidate | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | any2_improve_prob | all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | -0.0017 | -0.0001 | -0.0008 | 0.8840 | 0.6740 | 0.6100 | 0.8260 | 0.3660 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0 | -0.0016 | -0.0001 | -0.0007 | 0.8580 | 0.6400 | 0.6100 | 0.7980 | 0.3360 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0 | -0.0007 | -0.0002 | -0.0016 | 0.6640 | 0.9000 | 0.5980 | 0.7960 | 0.3820 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0 | -0.0007 | -0.0002 | -0.0016 | 0.6640 | 0.9000 | 0.5980 | 0.7960 | 0.3820 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | -0.0008 | -0.0002 | -0.0016 | 0.6540 | 0.9020 | 0.5980 | 0.7960 | 0.3760 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0 | -0.0016 | -0.0001 | -0.0007 | 0.8580 | 0.6480 | 0.6100 | 0.7960 | 0.3460 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0p25 | -0.0017 | -0.0000 | -0.0005 | 0.9080 | 0.5140 | 0.6400 | 0.7900 | 0.2920 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | -0.0016 | -0.0001 | -0.0006 | 0.8120 | 0.6680 | 0.6400 | 0.7880 | 0.3500 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0p25 | -0.0017 | -0.0000 | -0.0005 | 0.9080 | 0.5000 | 0.6400 | 0.7880 | 0.2800 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q80floor025_boost0 | -0.0007 | -0.0002 | -0.0016 | 0.6640 | 0.8780 | 0.5980 | 0.7840 | 0.3740 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_noguard_boost0 | -0.0007 | -0.0002 | -0.0015 | 0.6360 | 0.9000 | 0.5980 | 0.7840 | 0.3680 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_q90zero_boost0 | -0.0007 | -0.0002 | -0.0015 | 0.6360 | 0.9000 | 0.5980 | 0.7840 | 0.3680 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_noguard_boost0 | -0.0015 | -0.0001 | -0.0007 | 0.8340 | 0.6380 | 0.6100 | 0.7840 | 0.3320 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_q90zero_boost0 | -0.0015 | -0.0000 | -0.0007 | 0.8340 | 0.6280 | 0.6100 | 0.7800 | 0.3260 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | -0.0009 | -0.0002 | -0.0010 | 0.6580 | 0.9100 | 0.5580 | 0.7780 | 0.3600 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0 | -0.0008 | -0.0002 | -0.0010 | 0.6560 | 0.9120 | 0.5580 | 0.7780 | 0.3600 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0 | -0.0008 | -0.0002 | -0.0010 | 0.6560 | 0.9120 | 0.5580 | 0.7780 | 0.3600 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0_noguard_boost0 | -0.0006 | -0.0002 | -0.0015 | 0.6200 | 0.8980 | 0.5980 | 0.7780 | 0.3580 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0_q90zero_boost0 | -0.0006 | -0.0002 | -0.0015 | 0.6200 | 0.8980 | 0.5980 | 0.7780 | 0.3580 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_noguard_boost0 | -0.0006 | -0.0002 | -0.0015 | 0.6200 | 0.8980 | 0.5980 | 0.7780 | 0.3580 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_q90zero_boost0 | -0.0006 | -0.0002 | -0.0015 | 0.6200 | 0.8980 | 0.5980 | 0.7780 | 0.3580 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0_noguard_boost0 | -0.0015 | -0.0000 | -0.0007 | 0.8300 | 0.6280 | 0.6100 | 0.7760 | 0.3280 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_noguard_boost0 | -0.0015 | -0.0000 | -0.0007 | 0.8300 | 0.6280 | 0.6100 | 0.7760 | 0.3280 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0p25 | -0.0018 | -0.0000 | -0.0007 | 0.9120 | 0.5180 | 0.6100 | 0.7760 | 0.2900 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_noguard_boost0p25 | -0.0016 | -0.0000 | -0.0005 | 0.8960 | 0.4960 | 0.6400 | 0.7760 | 0.2760 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p25_noguard_boost0 | -0.0006 | -0.0002 | -0.0014 | 0.6180 | 0.8900 | 0.5980 | 0.7720 | 0.3580 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p25_q90zero_boost0 | -0.0006 | -0.0002 | -0.0014 | 0.6180 | 0.8900 | 0.5980 | 0.7720 | 0.3580 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p75_f0p5_noguard_boost0 | -0.0006 | -0.0002 | -0.0014 | 0.6180 | 0.8900 | 0.5980 | 0.7720 | 0.3580 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p75_f0p5_q90zero_boost0 | -0.0006 | -0.0002 | -0.0014 | 0.6180 | 0.8900 | 0.5980 | 0.7720 | 0.3580 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_q80floor025_boost0 | -0.0007 | -0.0002 | -0.0015 | 0.6360 | 0.8720 | 0.5980 | 0.7720 | 0.3560 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_noguard_boost0 | -0.0008 | -0.0002 | -0.0010 | 0.6440 | 0.9120 | 0.5580 | 0.7720 | 0.3540 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_q90zero_boost0 | -0.0008 | -0.0002 | -0.0010 | 0.6440 | 0.9120 | 0.5580 | 0.7720 | 0.3540 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0_noguard_boost0 | -0.0007 | -0.0002 | -0.0009 | 0.6400 | 0.9100 | 0.5580 | 0.7720 | 0.3500 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0_q90zero_boost0 | -0.0007 | -0.0002 | -0.0009 | 0.6400 | 0.9100 | 0.5580 | 0.7720 | 0.3500 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_noguard_boost0 | -0.0007 | -0.0002 | -0.0009 | 0.6400 | 0.9100 | 0.5580 | 0.7720 | 0.3500 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_q90zero_boost0 | -0.0007 | -0.0002 | -0.0009 | 0.6400 | 0.9100 | 0.5580 | 0.7720 | 0.3500 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0p25 | -0.0018 | -0.0000 | -0.0007 | 0.9120 | 0.5020 | 0.6100 | 0.7700 | 0.2820 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_noguard_boost0p25 | -0.0017 | -0.0000 | -0.0006 | 0.9060 | 0.5060 | 0.6100 | 0.7700 | 0.2800 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q80floor025_boost0 | -0.0008 | -0.0002 | -0.0010 | 0.6560 | 0.8840 | 0.5580 | 0.7680 | 0.3460 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0_q90zero_boost0 | -0.0015 | -0.0000 | -0.0007 | 0.8300 | 0.6020 | 0.6100 | 0.7680 | 0.3100 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_q90zero_boost0 | -0.0015 | -0.0000 | -0.0007 | 0.8300 | 0.6020 | 0.6100 | 0.7680 | 0.3100 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_q90zero_boost0p25 | -0.0016 | 0.0000 | -0.0005 | 0.8960 | 0.4760 | 0.6400 | 0.7680 | 0.2640 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q80zero_boost0 | -0.0007 | -0.0001 | -0.0016 | 0.6520 | 0.8580 | 0.5980 | 0.7660 | 0.3680 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0 | -0.0014 | -0.0001 | -0.0006 | 0.7780 | 0.6460 | 0.6400 | 0.7640 | 0.3280 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0_noguard_boost0p25 | -0.0015 | -0.0000 | -0.0004 | 0.8760 | 0.4840 | 0.6400 | 0.7640 | 0.2600 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_noguard_boost0p25 | -0.0015 | -0.0000 | -0.0004 | 0.8760 | 0.4840 | 0.6400 | 0.7640 | 0.2600 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0_q80floor025_boost0 | -0.0006 | -0.0002 | -0.0015 | 0.6200 | 0.8700 | 0.5980 | 0.7620 | 0.3500 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_q80floor025_boost0 | -0.0006 | -0.0002 | -0.0015 | 0.6200 | 0.8700 | 0.5980 | 0.7620 | 0.3500 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p25_noguard_boost0 | -0.0007 | -0.0002 | -0.0009 | 0.6260 | 0.9060 | 0.5580 | 0.7620 | 0.3440 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p25_q90zero_boost0 | -0.0007 | -0.0002 | -0.0009 | 0.6260 | 0.9060 | 0.5580 | 0.7620 | 0.3440 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p75_f0p5_noguard_boost0 | -0.0007 | -0.0002 | -0.0009 | 0.6260 | 0.9060 | 0.5580 | 0.7620 | 0.3440 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p75_f0p5_q90zero_boost0 | -0.0007 | -0.0002 | -0.0009 | 0.6260 | 0.9060 | 0.5580 | 0.7620 | 0.3440 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_q80floor025_boost0 | -0.0007 | -0.0002 | -0.0010 | 0.6440 | 0.8840 | 0.5580 | 0.7620 | 0.3400 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0 | -0.0014 | -0.0001 | -0.0006 | 0.7780 | 0.6280 | 0.6400 | 0.7620 | 0.3120 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p25_q80floor025_boost0 | -0.0006 | -0.0002 | -0.0014 | 0.6180 | 0.8680 | 0.5980 | 0.7600 | 0.3500 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p75_f0p5_q80floor025_boost0 | -0.0006 | -0.0002 | -0.0014 | 0.6180 | 0.8680 | 0.5980 | 0.7600 | 0.3500 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0_q80floor025_boost0 | -0.0007 | -0.0001 | -0.0009 | 0.6400 | 0.8800 | 0.5580 | 0.7580 | 0.3360 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_q80floor025_boost0 | -0.0007 | -0.0001 | -0.0009 | 0.6400 | 0.8800 | 0.5580 | 0.7580 | 0.3360 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0_noguard_boost0p25 | -0.0016 | 0.0000 | -0.0006 | 0.9000 | 0.4960 | 0.6100 | 0.7580 | 0.2760 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_noguard_boost0p25 | -0.0016 | 0.0000 | -0.0006 | 0.9000 | 0.4960 | 0.6100 | 0.7580 | 0.2760 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_q80zero_boost0 | -0.0007 | -0.0001 | -0.0015 | 0.6240 | 0.8580 | 0.5980 | 0.7560 | 0.3520 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0_q90zero_boost0p25 | -0.0015 | 0.0000 | -0.0004 | 0.8760 | 0.4660 | 0.6400 | 0.7560 | 0.2500 |
| validation_oof_row | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_q90zero_boost0p25 | -0.0015 | 0.0000 | -0.0004 | 0.8760 | 0.4660 | 0.6400 | 0.7560 | 0.2500 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0p25 | -0.0007 | -0.0001 | -0.0014 | 0.6600 | 0.8180 | 0.5980 | 0.7540 | 0.3560 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0p25 | -0.0007 | -0.0001 | -0.0014 | 0.6600 | 0.8180 | 0.5980 | 0.7540 | 0.3560 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_q90zero_boost0p25 | -0.0017 | 0.0000 | -0.0006 | 0.9060 | 0.4880 | 0.6100 | 0.7540 | 0.2800 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0_noguard_boost0 | -0.0006 | -0.0001 | -0.0008 | 0.6120 | 0.8980 | 0.5580 | 0.7520 | 0.3320 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0_q90zero_boost0 | -0.0006 | -0.0001 | -0.0008 | 0.6120 | 0.8980 | 0.5580 | 0.7520 | 0.3320 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a1_f0p5_noguard_boost0 | -0.0006 | -0.0001 | -0.0008 | 0.6120 | 0.8980 | 0.5580 | 0.7520 | 0.3320 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a1_f0p5_q90zero_boost0 | -0.0006 | -0.0001 | -0.0008 | 0.6120 | 0.8980 | 0.5580 | 0.7520 | 0.3320 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0_q80zero_boost0 | -0.0006 | -0.0001 | -0.0015 | 0.6080 | 0.8560 | 0.5980 | 0.7480 | 0.3460 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_q80zero_boost0 | -0.0006 | -0.0001 | -0.0015 | 0.6080 | 0.8560 | 0.5980 | 0.7480 | 0.3460 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_noguard_boost0p25 | -0.0008 | -0.0001 | -0.0007 | 0.6600 | 0.8060 | 0.5580 | 0.7480 | 0.3160 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q90zero_boost0p25 | -0.0008 | -0.0001 | -0.0007 | 0.6600 | 0.8060 | 0.5580 | 0.7480 | 0.3160 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p25_f0_q90zero_boost0p25 | -0.0016 | 0.0000 | -0.0006 | 0.9000 | 0.4820 | 0.6100 | 0.7480 | 0.2740 |
| validation_oof_row | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p5_q90zero_boost0p25 | -0.0016 | 0.0000 | -0.0006 | 0.9000 | 0.4820 | 0.6100 | 0.7480 | 0.2740 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p5_q80floor025_boost0p25 | -0.0007 | -0.0001 | -0.0014 | 0.6580 | 0.8000 | 0.5980 | 0.7460 | 0.3480 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p5_f0p25_q80floor025_boost0 | -0.0006 | -0.0001 | -0.0009 | 0.6260 | 0.8760 | 0.5580 | 0.7460 | 0.3300 |
| validation_oof_artist | artist_holdout_80pct | hcoef28_h26_direct_guarded_a0p75_f0p5_q80floor025_boost0 | -0.0006 | -0.0001 | -0.0009 | 0.6260 | 0.8760 | 0.5580 | 0.7460 | 0.3300 |
| validation_oof_artist | row_subsample_80pct | hcoef28_h26_direct_guarded_a0p25_f0p25_noguard_boost0p25 | -0.0007 | -0.0001 | -0.0014 | 0.6340 | 0.8160 | 0.5980 | 0.7440 | 0.3420 |

## 7. Huber risk 계수 해석

| coefficient_scope | model_label | feature | coefficient | interpretation |
| --- | --- | --- | --- | --- |
| risk_huber_abs_residual | row_oof_full | quantile_width | 0.0291 | 예측 가격 범위가 넓을수록 큰 오차 위험이 커지는지 보는 피처; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_oof_full | l10_price_range_ratio | -0.0305 | q90/q10 가격 범위 비율이 큰 구간의 불확실성; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_oof_full | svc_group_n_log | 0.0028 | 유사 작품 표본 수가 많을수록 기준가가 안정되는지 보는 피처; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_oof_full | hcoef23_risk_score | 0.0050 | HCOEF23에서 확인한 위험 신호의 합; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_oof_full | stable_current_gap_abs | 0.0099 | 안정 후보와 기존 70:30 후보의 의견 차이; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_oof_full | stable_ppv8_gap_abs | -0.0302 | 안정 후보와 PP-V8 component의 의견 차이; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_oof_full | stable_svc_gap_abs | -0.0412 | 안정 후보와 유사 작품 기준가의 의견 차이; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_oof_full | ppv8_svc_gap_abs | 0.0605 | 오차 안정화 후보와 유사 작품 기준가의 의견 차이; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_oof_full | pred_spread_numeric | 0.0268 | 주요 후보 예측값 전체의 벌어짐; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_oof_full | log_area | -0.0006 | 작품 크기 축; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_oof_full | risk_qwidth_extreme | 0.0105 | quantile width 극단 구간; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_oof_full | risk_gap_020_plus | 0.0246 | 후보 간 gap이 0.20 log 이상인 구간; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_oof_full | risk_spread_extreme | -0.0092 | 후보 예측 spread 극단 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_oof_full | risk_low_n | -0.0041 | 유사 표본 수 10건 미만 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_oof_full | risk_n_10_19 | -0.0097 | 유사 표본 수 10~19건 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_oof_full | risk_artist_fallback | 0.0263 | 작가 전체 기준으로 fallback된 구간; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | quantile_width | 0.0291 | 예측 가격 범위가 넓을수록 큰 오차 위험이 커지는지 보는 피처; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | l10_price_range_ratio | -0.0305 | q90/q10 가격 범위 비율이 큰 구간의 불확실성; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | artist_oof_full | svc_group_n_log | 0.0028 | 유사 작품 표본 수가 많을수록 기준가가 안정되는지 보는 피처; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | hcoef23_risk_score | 0.0050 | HCOEF23에서 확인한 위험 신호의 합; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | stable_current_gap_abs | 0.0099 | 안정 후보와 기존 70:30 후보의 의견 차이; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | stable_ppv8_gap_abs | -0.0302 | 안정 후보와 PP-V8 component의 의견 차이; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | artist_oof_full | stable_svc_gap_abs | -0.0412 | 안정 후보와 유사 작품 기준가의 의견 차이; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | artist_oof_full | ppv8_svc_gap_abs | 0.0605 | 오차 안정화 후보와 유사 작품 기준가의 의견 차이; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | pred_spread_numeric | 0.0268 | 주요 후보 예측값 전체의 벌어짐; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | log_area | -0.0006 | 작품 크기 축; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | artist_oof_full | risk_qwidth_extreme | 0.0105 | quantile width 극단 구간; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | risk_gap_020_plus | 0.0246 | 후보 간 gap이 0.20 log 이상인 구간; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | artist_oof_full | risk_spread_extreme | -0.0092 | 후보 예측 spread 극단 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | artist_oof_full | risk_low_n | -0.0041 | 유사 표본 수 10건 미만 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | artist_oof_full | risk_n_10_19 | -0.0097 | 유사 표본 수 10~19건 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | artist_oof_full | risk_artist_fallback | 0.0263 | 작가 전체 기준으로 fallback된 구간; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | quantile_width | 0.0291 | 예측 가격 범위가 넓을수록 큰 오차 위험이 커지는지 보는 피처; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | l10_price_range_ratio | -0.0305 | q90/q10 가격 범위 비율이 큰 구간의 불확실성; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | svc_group_n_log | 0.0028 | 유사 작품 표본 수가 많을수록 기준가가 안정되는지 보는 피처; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | hcoef23_risk_score | 0.0050 | HCOEF23에서 확인한 위험 신호의 합; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | stable_current_gap_abs | 0.0099 | 안정 후보와 기존 70:30 후보의 의견 차이; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | stable_ppv8_gap_abs | -0.0302 | 안정 후보와 PP-V8 component의 의견 차이; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | stable_svc_gap_abs | -0.0412 | 안정 후보와 유사 작품 기준가의 의견 차이; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | ppv8_svc_gap_abs | 0.0605 | 오차 안정화 후보와 유사 작품 기준가의 의견 차이; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | pred_spread_numeric | 0.0268 | 주요 후보 예측값 전체의 벌어짐; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | log_area | -0.0006 | 작품 크기 축; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | risk_qwidth_extreme | 0.0105 | quantile width 극단 구간; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | risk_gap_020_plus | 0.0246 | 후보 간 gap이 0.20 log 이상인 구간; 계수 기준 위험 증가 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | risk_spread_extreme | -0.0092 | 후보 예측 spread 극단 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | risk_low_n | -0.0041 | 유사 표본 수 10건 미만 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | risk_n_10_19 | -0.0097 | 유사 표본 수 10~19건 구간; 계수 기준 위험 감소 방향 |
| risk_huber_abs_residual | row_validation_full_for_test | risk_artist_fallback | 0.0263 | 작가 전체 기준으로 fallback된 구간; 계수 기준 위험 증가 방향 |

## 8. 정책 후보 설정

| candidate | source_candidate | source_tag | alpha | floor | guard_name | guard_quantile | guard_weight | lowrisk_boost | formula |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.0000 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.0000 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.0000 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.0000 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.0000 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.0000 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.0000 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.0000 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.2500 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.2500 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.2500 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.2500 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.2500 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.2500 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.2500 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p25_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.2500 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.5000 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.5000 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.5000 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.5000 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.5000 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.5000 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.5000 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p25_f0p5_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.2500 | 0.5000 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.0000 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.0000 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.0000 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.0000 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.0000 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.0000 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.0000 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.0000 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.2500 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.2500 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.2500 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.2500 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.2500 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.2500 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.2500 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p25_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.2500 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.5000 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.5000 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.5000 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.5000 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.5000 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.5000 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.5000 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p5_f0p5_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.5000 | 0.5000 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.0000 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.0000 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.0000 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.0000 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.0000 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.0000 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.0000 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.0000 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p25_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.2500 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p25_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.2500 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p25_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.2500 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p25_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.2500 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p25_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.2500 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p25_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.2500 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p25_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.2500 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p25_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.2500 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.5000 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.5000 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.5000 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.5000 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.5000 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.5000 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.5000 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a0p75_f0p5_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 0.7500 | 0.5000 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a1_f0_noguard_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 1.0000 | 0.0000 | noguard |  |  | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a1_f0_noguard_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 1.0000 | 0.0000 | noguard |  |  | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a1_f0_q80zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 1.0000 | 0.0000 | q80zero | 0.8000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a1_f0_q80zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 1.0000 | 0.0000 | q80zero | 0.8000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a1_f0_q90zero_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 1.0000 | 0.0000 | q90zero | 0.9000 | 0.0000 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a1_f0_q90zero_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 1.0000 | 0.0000 | q90zero | 0.9000 | 0.0000 | 0.2500 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a1_f0_q80floor025_boost0 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 1.0000 | 0.0000 | q80floor025 | 0.8000 | 0.2500 | 0.0000 | stable + weight * (source - stable) |
| hcoef28_h26_lowrisk_fixed_a1_f0_q80floor025_boost0p25 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | h26_lowrisk_fixed | 1.0000 | 0.0000 | q80floor025 | 0.8000 | 0.2500 | 0.2500 | stable + weight * (source - stable) |

## 9. 잔차/큰 오차 구간

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
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4975 | 1.0854 | 0.9329 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1230 | 0.1020 | -0.0540 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5513 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1768 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | service_confidence_tier | high | 22 | 0.5814 | 0.5575 | 1.0347 | 0.8116 | 0.3636 | 0.4545 | 4 | 4 | 0.3084 | 0.1830 | 0.0512 | 0.1293 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5030 | 1.0000 | 1.7332 | 0.3196 | 0.5365 | 19 | 142 | 0.1673 | 0.1284 | 0.0165 | 0.2965 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 1.7951 | 0.3159 | 0.5597 | 17 | 127 | 0.1613 | 0.1302 | 0.0165 | 0.2799 | 0.4403 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | qwidth_band | qwidth_extreme | 301 | 0.3786 | 0.4380 | 0.9960 | 1.9673 | 0.4053 | 0.6279 | 7 | 100 | 0.1056 | 0.0635 | 0.0125 | 0.3534 | 0.3721 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | qwidth_band | qwidth_high | 185 | 0.2364 | 0.3756 | 0.9867 | 0.9911 | 0.5514 | 0.7297 | 6 | 27 | -0.0366 | 0.0011 | 0.0033 | 0.0709 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_n_band | n_5_9 | 435 | 0.2383 | 0.3310 | 0.9867 | 1.6307 | 0.5655 | 0.7632 | 9 | 63 | -0.0348 | -0.0436 | 0.0033 | 0.0655 | 0.2368 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_level | artist | 412 | 0.3193 | 0.3766 | 0.9867 | 1.5787 | 0.4854 | 0.7427 | 13 | 61 | 0.0462 | 0.0020 | 0.0033 | 0.0847 | 0.2573 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | service_confidence_tier | low | 499 | 0.2654 | 0.3525 | 0.9719 | 1.5793 | 0.5251 | 0.7335 | 9 | 90 | -0.0077 | -0.0221 | -0.0115 | 0.0935 | 0.2665 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | service_confidence_tier | medium | 308 | 0.2703 | 0.3973 | 0.9707 | 0.7181 | 0.5130 | 0.6916 | 13 | 58 | -0.0028 | 0.0227 | -0.0127 | 0.0255 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.7560 | 0.7680 | 0.9040 | 5 | 3 | -0.1238 | -0.1228 | -0.0309 | 0.0403 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_n_band | n_20_49 | 90 | 0.2052 | 0.3412 | 0.9231 | 0.6262 | 0.5889 | 0.7556 | 3 | 13 | -0.0678 | -0.0333 | -0.0604 | 0.0587 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | qwidth_band | qwidth_mid | 242 | 0.2374 | 0.3389 | 0.8841 | 0.4713 | 0.5661 | 0.7521 | 11 | 22 | -0.0357 | -0.0357 | -0.0993 | 0.0054 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2994 | -0.1045 | 1.3500 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | 0.5175 | 0.5547 | 0.6953 | 3 | 16 | -0.0521 | -0.0349 | -0.1106 | -0.0540 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_n_band | n_10_19 | 199 | 0.2862 | 0.3916 | 0.8641 | 0.7515 | 0.5075 | 0.7136 | 5 | 34 | 0.0132 | 0.0170 | -0.1194 | 0.0267 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_level | artist_size | 224 | 0.1911 | 0.3480 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0820 | -0.0266 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2904 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | qwidth_band | qwidth_low | 101 | 0.1774 | 0.2688 | 0.8046 | 0.4150 | 0.6634 | 0.8218 | 2 | 3 | -0.0957 | -0.1058 | -0.1788 | 0.0055 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | pred_spread_band | spread_high | 124 | 0.2112 | 0.2772 | 0.7949 | 0.7724 | 0.6129 | 0.8952 | 3 | 3 | -0.0619 | -0.0974 | -0.1886 | -0.0540 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2249 | 0.7707 | 0.7748 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1497 | -0.2128 | -0.0009 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | pred_spread_band | spread_low_mid | 267 | 0.1171 | 0.2091 | 0.6616 | 0.3245 | 0.7940 | 0.9101 | 4 | 7 | -0.1560 | -0.1655 | -0.3219 | 0.0117 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.3153 | 0.7983 | 0.9244 | 1 | 5 | -0.1754 | -0.1854 | -0.4535 | 0.0267 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.3011 | 0.7091 | 0.9455 | 0 | 1 | -0.1862 | -0.1897 | -0.4661 | 0.0078 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4975 | 1.0854 | 0.9329 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1230 | 0.1020 | -0.0540 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5513 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1768 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | service_confidence_tier | high | 22 | 0.5814 | 0.5575 | 1.0347 | 0.8116 | 0.3636 | 0.4545 | 4 | 4 | 0.3084 | 0.1830 | 0.0512 | 0.1293 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5030 | 1.0000 | 1.7332 | 0.3196 | 0.5365 | 19 | 142 | 0.1673 | 0.1284 | 0.0165 | 0.2965 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 1.7951 | 0.3159 | 0.5597 | 17 | 127 | 0.1613 | 0.1302 | 0.0165 | 0.2799 | 0.4403 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | qwidth_band | qwidth_extreme | 301 | 0.3786 | 0.4380 | 0.9960 | 1.9673 | 0.4053 | 0.6279 | 7 | 100 | 0.1056 | 0.0635 | 0.0125 | 0.3534 | 0.3721 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | qwidth_band | qwidth_high | 185 | 0.2364 | 0.3756 | 0.9867 | 0.9911 | 0.5514 | 0.7297 | 6 | 27 | -0.0366 | 0.0011 | 0.0033 | 0.0709 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_n_band | n_5_9 | 435 | 0.2383 | 0.3310 | 0.9867 | 1.6307 | 0.5655 | 0.7632 | 9 | 63 | -0.0348 | -0.0436 | 0.0033 | 0.0655 | 0.2368 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_level | artist | 412 | 0.3193 | 0.3766 | 0.9867 | 1.5787 | 0.4854 | 0.7427 | 13 | 61 | 0.0462 | 0.0020 | 0.0033 | 0.0847 | 0.2573 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | service_confidence_tier | low | 499 | 0.2654 | 0.3525 | 0.9719 | 1.5793 | 0.5251 | 0.7335 | 9 | 90 | -0.0077 | -0.0221 | -0.0115 | 0.0935 | 0.2665 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | service_confidence_tier | medium | 308 | 0.2703 | 0.3973 | 0.9707 | 0.7181 | 0.5130 | 0.6916 | 13 | 58 | -0.0028 | 0.0227 | -0.0127 | 0.0255 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.7560 | 0.7680 | 0.9040 | 5 | 3 | -0.1238 | -0.1228 | -0.0309 | 0.0403 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_n_band | n_20_49 | 90 | 0.2052 | 0.3412 | 0.9231 | 0.6262 | 0.5889 | 0.7556 | 3 | 13 | -0.0678 | -0.0333 | -0.0604 | 0.0587 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | qwidth_band | qwidth_mid | 242 | 0.2374 | 0.3389 | 0.8841 | 0.4713 | 0.5661 | 0.7521 | 11 | 22 | -0.0357 | -0.0357 | -0.0993 | 0.0054 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2994 | -0.1045 | 1.3500 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | 0.5175 | 0.5547 | 0.6953 | 3 | 16 | -0.0521 | -0.0349 | -0.1106 | -0.0540 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_n_band | n_10_19 | 199 | 0.2862 | 0.3916 | 0.8641 | 0.7515 | 0.5075 | 0.7136 | 5 | 34 | 0.0132 | 0.0170 | -0.1194 | 0.0267 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_level | artist_size | 224 | 0.1911 | 0.3480 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0820 | -0.0266 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2904 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | qwidth_band | qwidth_low | 101 | 0.1774 | 0.2688 | 0.8046 | 0.4150 | 0.6634 | 0.8218 | 2 | 3 | -0.0957 | -0.1058 | -0.1788 | 0.0055 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | pred_spread_band | spread_high | 124 | 0.2112 | 0.2772 | 0.7949 | 0.7724 | 0.6129 | 0.8952 | 3 | 3 | -0.0619 | -0.0974 | -0.1886 | -0.0540 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2249 | 0.7707 | 0.7748 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1497 | -0.2128 | -0.0009 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | pred_spread_band | spread_low_mid | 267 | 0.1171 | 0.2091 | 0.6616 | 0.3245 | 0.7940 | 0.9101 | 4 | 7 | -0.1560 | -0.1655 | -0.3219 | 0.0117 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.3153 | 0.7983 | 0.9244 | 1 | 5 | -0.1754 | -0.1854 | -0.4535 | 0.0267 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0_q80zero_boost0 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.3011 | 0.7091 | 0.9455 | 0 | 1 | -0.1862 | -0.1897 | -0.4661 | 0.0078 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4975 | 1.0854 | 0.9329 | 0.3485 | 0.5909 | 8 | 14 | 0.1559 | 0.1230 | 0.1020 | -0.0540 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5513 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2604 | 0.1768 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | service_confidence_tier | high | 22 | 0.5814 | 0.5575 | 1.0347 | 0.8116 | 0.3636 | 0.4545 | 4 | 4 | 0.3084 | 0.1830 | 0.0512 | 0.1293 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5030 | 1.0000 | 1.7332 | 0.3196 | 0.5365 | 19 | 142 | 0.1673 | 0.1284 | 0.0165 | 0.2965 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 1.7951 | 0.3159 | 0.5597 | 17 | 127 | 0.1613 | 0.1302 | 0.0165 | 0.2799 | 0.4403 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | qwidth_band | qwidth_extreme | 301 | 0.3786 | 0.4380 | 0.9960 | 1.9673 | 0.4053 | 0.6279 | 7 | 100 | 0.1056 | 0.0635 | 0.0125 | 0.3534 | 0.3721 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | qwidth_band | qwidth_high | 185 | 0.2364 | 0.3756 | 0.9867 | 0.9911 | 0.5514 | 0.7297 | 6 | 27 | -0.0366 | 0.0011 | 0.0033 | 0.0709 | 0.2703 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_n_band | n_5_9 | 435 | 0.2383 | 0.3310 | 0.9867 | 1.6307 | 0.5655 | 0.7632 | 9 | 63 | -0.0348 | -0.0436 | 0.0033 | 0.0655 | 0.2368 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_level | artist | 412 | 0.3193 | 0.3766 | 0.9867 | 1.5787 | 0.4854 | 0.7427 | 13 | 61 | 0.0462 | 0.0020 | 0.0033 | 0.0847 | 0.2573 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | service_confidence_tier | low | 499 | 0.2654 | 0.3525 | 0.9719 | 1.5793 | 0.5251 | 0.7335 | 9 | 90 | -0.0077 | -0.0221 | -0.0115 | 0.0935 | 0.2665 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | service_confidence_tier | medium | 308 | 0.2703 | 0.3973 | 0.9707 | 0.7181 | 0.5130 | 0.6916 | 13 | 58 | -0.0028 | 0.0227 | -0.0127 | 0.0255 | 0.3084 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.7560 | 0.7680 | 0.9040 | 5 | 3 | -0.1238 | -0.1228 | -0.0309 | 0.0403 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_n_band | n_20_49 | 90 | 0.2052 | 0.3412 | 0.9231 | 0.6262 | 0.5889 | 0.7556 | 3 | 13 | -0.0678 | -0.0333 | -0.0604 | 0.0587 | 0.2444 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | qwidth_band | qwidth_mid | 242 | 0.2374 | 0.3389 | 0.8841 | 0.4713 | 0.5661 | 0.7521 | 11 | 22 | -0.0357 | -0.0357 | -0.0993 | 0.0054 | 0.2479 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_level | medium_size | 18 | 0.7718 | 0.6740 | 0.8790 | 1.2162 | 0.1111 | 0.2222 | 1 | 12 | 0.4987 | 0.2994 | -0.1045 | 1.3500 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | 0.5175 | 0.5547 | 0.6953 | 3 | 16 | -0.0521 | -0.0349 | -0.1106 | -0.0540 | 0.3047 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_n_band | n_10_19 | 199 | 0.2862 | 0.3916 | 0.8641 | 0.7515 | 0.5075 | 0.7136 | 5 | 34 | 0.0132 | 0.0170 | -0.1194 | 0.0267 | 0.2864 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_level | artist_size | 224 | 0.1911 | 0.3480 | 0.8507 | 1.0027 | 0.5893 | 0.6964 | 4 | 49 | -0.0820 | -0.0266 | -0.1327 | 0.0532 | 0.3036 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_level | global | 18 | 0.6363 | 0.6649 | 0.8453 | 1.2291 | 0.0000 | 0.1667 | 0 | 14 | 0.3632 | 0.2904 | -0.1381 | 0.9648 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | qwidth_band | qwidth_low | 101 | 0.1774 | 0.2688 | 0.8046 | 0.4150 | 0.6634 | 0.8218 | 2 | 3 | -0.0957 | -0.1058 | -0.1788 | 0.0055 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | pred_spread_band | spread_high | 124 | 0.2112 | 0.2772 | 0.7949 | 0.7724 | 0.6129 | 0.8952 | 3 | 3 | -0.0619 | -0.0974 | -0.1886 | -0.0540 | 0.1048 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | svc_group_level | artist_medium_support_size | 91 | 0.1745 | 0.2249 | 0.7707 | 0.7748 | 0.7802 | 0.8901 | 0 | 2 | -0.0985 | -0.1497 | -0.2128 | -0.0009 | 0.1099 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | pred_spread_band | spread_low_mid | 267 | 0.1171 | 0.2091 | 0.6616 | 0.3245 | 0.7940 | 0.9101 | 4 | 7 | -0.1560 | -0.1655 | -0.3219 | 0.0117 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.3153 | 0.7983 | 0.9244 | 1 | 5 | -0.1754 | -0.1854 | -0.4535 | 0.0267 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef28_h26_lowrisk_fixed_a0p25_f0p25_noguard_boost0 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.3011 | 0.7091 | 0.9455 | 0 | 1 | -0.1862 | -0.1897 | -0.4661 | 0.0078 | 0.0545 |

## 10. 다음 방향

- risk Huber shrinkage가 repeated gate를 통과하면 HCOEF29에서 후보를 축소해 재검증.
- 통과하지 못하면 점 예측 이동보다 가격 범위/신뢰도 정책 또는 독립 피처 신호 추가가 우선.

## 11. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/repeated_iteration_metrics.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/residual_analysis.csv`
- `outputs/selected_candidates.csv`
- `outputs/policy_configurations.csv`
- `outputs/risk_model_thresholds.csv`
- `artifacts/experiment_config.json`