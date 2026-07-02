# Warm 기준 성능 정리 및 Base 고정

- 작성일: 2026-06-08 16:40
- 목적: 이후 CatBoost/XGBoost/LightGBM 등 다른 residual 모델 실험에서 기준 base가 흔들리지 않도록 고정한다.

## 고정 결정

1. **모델링용 raw base는 `WARM_BASE_RAW_V1`로 고정한다.**
   - source column: `PP-FPOL6_directional_price_bin_guard/outputs/candidate_predictions.csv`의 `base_pred_log`
   - 의미: 기존 Warm 70:30 계열 기준 로그 가격, FPOL/WHUBER 보정이 들어가기 전 기준값
   - residual target: `actual_log - fixed_base_pred_log`
2. **현재 성능 비교 champion은 FPOL6 후보로 별도 고정한다.**
   - MAPE champion: `artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none`
   - balanced/p95 guardrail: `artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=none__price=mid_open_tail_guard`
3. 다른 모델 실험은 `WARM_BASE_RAW_V1`의 residual을 학습하고, 결과를 아래 두 기준과 모두 비교한다.
   - raw base 대비 개선폭
   - FPOL6 champion 대비 개선/악화 여부

## Warm 성능 요약

| selection | role | source | candidate | split | n | MdAPE | MAPE | p95_APE | RMSE_log | balanced_delta | locked_for_future_modeling |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WARM_BASE_RAW_V1_test | fixed_raw_base_for_future_modeling | REFERENCE | blend_svcnum_ppv8_wsvc_0.70 / base_pred_log | test | 607.000000 | 0.140484 | 0.274799 | 0.833074 | 0.399609 | 0.000000 | True |
| WARM_BASE_RAW_V1_validation | fixed_raw_base_for_future_modeling | REFERENCE | blend_svcnum_ppv8_wsvc_0.70 / base_pred_log | validation | 519.000000 | 0.130522 | 0.211028 | 0.658041 | 0.329201 | 0.000000 | True |
| MdAPE 최저 | previous_warm_huber_reference | PP-WHUBER7 | PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | test | nan | 0.132780 | 0.274335 | 0.844676 | 0.398848 | -0.005847 | False |
| MAPE 최저 | previous_warm_huber_reference | PP-WHUBER7 | PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08 | test | nan | 0.136828 | 0.272871 | 0.815180 | 0.397753 | -0.009162 | False |
| p95 최저 | previous_warm_huber_reference | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08 | test | nan | 0.139569 | 0.273253 | 0.801649 | 0.399128 | -0.008746 | False |
| 세 지표 균형 최저 | previous_warm_huber_reference | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | test | nan | 0.136110 | 0.274013 | 0.806151 | 0.398932 | -0.010545 | False |
| 세 지표 모두 개선 중 균형 최저 | previous_warm_huber_reference | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | test | nan | 0.136110 | 0.274013 | 0.806151 | 0.398932 | -0.010545 | False |
| 이번 정책 실험 최선 | previous_warm_huber_reference | PP-FPOL2 | huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | test | nan | 0.138589 | 0.274630 | 0.815797 | 0.399667 | -0.005519 | False |
| current_mape_champion_for_comparison | current_mape_champion_for_comparison | PP-FPOL6 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none | test | nan | 0.139051 | 0.271750 | 0.810159 | 0.397970 | -0.009064 | False |
| current_balanced_champion_for_guardrail | current_balanced_champion_for_guardrail | PP-FPOL6 | artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=none__price=mid_open_tail_guard | test | nan | 0.136283 | 0.273273 | 0.801948 | 0.398930 | -0.011951 | False |
| current_p95_champion_for_guardrail | current_p95_champion_for_guardrail | PP-FPOL6 | artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=under_guard__price=none | test | nan | 0.138911 | 0.272821 | 0.801948 | 0.399077 | -0.009776 | False |
| MAPE 최저 | remaining_method_reference | PP-FPOL10 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__gaproute=l8_agreement_soft_blend | test | nan | 0.142687 | 0.272080 | 0.834172 | 0.396291 | 0.000194 | False |
| 균형 최저 | remaining_method_reference | PP-FPOL9 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=conservative_high_width | test | nan | 0.136549 | 0.272893 | 0.808567 | 0.398641 | -0.010116 | False |
| p95 최저 | remaining_method_reference | PP-FPOL9 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=confident_strong_uncertain_weak | test | nan | 0.138455 | 0.272603 | 0.807755 | 0.398503 | -0.009848 | False |
| PP-FPOL9 균형 최저 | remaining_method_reference | PP-FPOL9 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=conservative_high_width | test | nan | 0.136549 | 0.272893 | 0.808567 | 0.398641 | -0.010116 | False |
| PP-FPOL10 균형 최저 | remaining_method_reference | PP-FPOL10 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__gaproute=large_gap_damp_source | test | nan | 0.136967 | 0.272366 | 0.810388 | 0.398242 | -0.009545 | False |
| PP-FPOL11 균형 최저 | remaining_method_reference | PP-FPOL11 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__tail=price_or_size_tail | test | nan | 0.138401 | 0.272752 | 0.813008 | 0.398478 | -0.008065 | False |
| PP-FPOL12 균형 최저 | remaining_method_reference | PP-FPOL12 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__segmix=source_hybrid_segment_soft_blend | test | nan | 0.157908 | 0.288279 | 0.878751 | 0.404807 | 0.025527 | False |

## 안정성 참고 Top 8

| candidate | stability_score | bootstrap_improve_MAPE | bootstrap_improve_p95_APE | fold_improve_MAPE | fold_improve_p95_APE |
| --- | --- | --- | --- | --- | --- |
| PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 3.628333 | 0.999167 | 0.889167 | 0.940000 | 0.800000 |
| PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=soft_rel__size=all | 3.628333 | 0.999167 | 0.889167 | 0.940000 | 0.800000 |
| PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__rel=soft_rel__size=all | 3.628333 | 0.999167 | 0.889167 | 0.940000 | 0.800000 |
| PP-FPOL6::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none | 3.596667 | 0.997500 | 0.879167 | 0.920000 | 0.800000 |
| PP-FPOL6::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none | 3.596667 | 0.997500 | 0.879167 | 0.920000 | 0.800000 |
| PP-FPOL6::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none | 3.596667 | 0.997500 | 0.879167 | 0.920000 | 0.800000 |
| PP-FPOL7::artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 3.590000 | 0.998333 | 0.891667 | 0.920000 | 0.780000 |
| PP-FPOL7::artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=soft_rel__size=all | 3.590000 | 0.998333 | 0.891667 | 0.920000 | 0.780000 |

## 다음 모델 실험 규칙

- base prediction은 항상 `fixed_base_pred_log`를 사용한다.
- residual target은 `actual_log - fixed_base_pred_log`로 둔다.
- Huber 계수나 FPOL6 보정값을 새 모델의 입력 target으로 쓰지 않는다.
- CatBoost/XGBoost/LightGBM 후보는 validation split에서 학습/튜닝하고, test split 607건은 최종 비교에만 사용한다.
- 성능 표는 최소 `MdAPE`, `MAPE`, `p95_APE`, `RMSE_log`, `Within_30`, `Within_50`을 포함한다.
- 최종 후보는 MAPE 단독이 아니라 `MAPE`, `p95_APE`, `balanced_delta`, 반복 안정성 순서로 판단한다.

## 산출물

- `data/fixed_warm_base_validation_test_rows.csv`
- `outputs/warm_base_performance_summary.csv`
- `outputs/warm_stability_reference.csv`
- `artifacts/warm_base_lock_manifest.json`
