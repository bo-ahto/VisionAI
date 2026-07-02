# PP-FPOL9~12 남은 방법 배치 최종 요약

- 작성일: 2026-06-08 16:32
- 공통 source: FPOL6 상위 20개 후보
- 평가 기준: validation/test 동일 split, baseline은 각 row의 `base_pred_log`

## 최종 추천

| selection | source | candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAPE 최저 | PP-FPOL10 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__gaproute=l8_agreement_soft_blend | 0.142687 | 0.272080 | 0.834172 | 0.002203 | -0.002718 | 0.001098 | 0.000194 | False |
| 균형 최저 | PP-FPOL9 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=conservative_high_width | 0.136549 | 0.272893 | 0.808567 | -0.003935 | -0.001906 | -0.024507 | -0.010116 | True |
| p95 최저 | PP-FPOL9 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=confident_strong_uncertain_weak | 0.138455 | 0.272603 | 0.807755 | -0.002028 | -0.002196 | -0.025318 | -0.009848 | True |
| PP-FPOL9 균형 최저 | PP-FPOL9 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=conservative_high_width | 0.136549 | 0.272893 | 0.808567 | -0.003935 | -0.001906 | -0.024507 | -0.010116 | True |
| PP-FPOL10 균형 최저 | PP-FPOL10 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.136967 | 0.272366 | 0.810388 | -0.003517 | -0.002433 | -0.022686 | -0.009545 | True |
| PP-FPOL11 균형 최저 | PP-FPOL11 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__tail=price_or_size_tail | 0.138401 | 0.272752 | 0.813008 | -0.002083 | -0.002047 | -0.020065 | -0.008065 | True |
| PP-FPOL12 균형 최저 | PP-FPOL12 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__segmix=source_hybrid_segment_soft_blend | 0.157908 | 0.288279 | 0.878751 | 0.017424 | 0.013480 | 0.045677 | 0.025527 | False |

## 해석

- `PP-FPOL9`는 quantile width가 큰 불확실 구간에서는 보정 cap/strength를 줄이고, 낮은 구간에서는 보정을 열어주는 실험입니다.
- `PP-FPOL10`은 P2/L8/L9/M1 보조 예측과 source 예측의 gap을 이용해 blend 또는 damp를 수행합니다.
- `PP-FPOL11`은 pred price tail과 size tail에만 보정을 집중해 p95 방어력을 확인합니다.
- `PP-FPOL12`는 segment median prior에 FPOL6 residual을 제한적으로 얹는 방식입니다.

## 산출물

- `outputs/all_fpol9_12_test_metrics.csv`
- `outputs/final_remaining_method_recommendations.csv`
