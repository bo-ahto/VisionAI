# PP-FPOL4~8 배치 실험 최종 요약

- 작성일: 2026-06-08 15:51
- 목적: 후버 기반 잔차 보정에서 작가/작품/SVC 보정 조합을 한 번에 계획하고 순서대로 검증
- 기준 baseline: 기존 Warm/SVC 후버 계열 base candidate

## 결론

1. test MAPE 최저 후보는 `PP-FPOL6`의 `artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none`입니다.
   - MdAPE `0.139051`, MAPE `0.271750`, p95 `0.810159`
2. MdAPE/MAPE/p95 균형 최저 후보는 `PP-FPOL6`의 `artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=none__price=mid_open_tail_guard`입니다.
   - MdAPE `0.136283`, MAPE `0.273273`, p95 `0.801948`, balanced_delta `-0.011951`
3. 반복 안정성 최상위 후보는 `PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all`입니다.
   - stability_score `3.628333`, bootstrap MAPE 개선확률 `0.999167`, artist-fold MAPE 개선확률 `0.940000`

## 추천 후보

| recommendation | source | candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | stability_score | bootstrap_improve_MAPE | fold_improve_MAPE | fold_improve_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 성능 최우선: test MAPE 최저 | PP-FPOL6 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none | 0.139051 | 0.271750 | 0.810159 | -0.001432 | -0.003049 | -0.022915 | -0.009064 |  |  |  |  |
| 균형 우선: MdAPE/MAPE/p95 동시 개선 | PP-FPOL6 | artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=none__price=mid_open_tail_guard | 0.136283 | 0.273273 | 0.801948 | -0.004201 | -0.001526 | -0.031126 | -0.011951 |  |  |  |  |
| p95 안정 우선: 큰 오차 꼬리 최소 | PP-FPOL4 | artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08 | 0.139569 | 0.273253 | 0.801649 | -0.000914 | -0.001546 | -0.031424 | -0.008745 |  |  |  |  |
| 반복 안정성 우선: bootstrap/artist-fold 개선확률 | PP-FPOL7 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.137718 | 0.272655 | 0.810596 | -0.002766 | -0.002144 | -0.022477 | -0.009405 | 3.628333 | 0.999167 | 0.940000 | 0.800000 |

## 기존 최고 후보 기준

| selection | source | candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MdAPE 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.132780 | 0.274335 | 0.844676 | -0.007704 | -0.000464 | 0.011602 | -0.005847 |
| MAPE 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08 | 0.136828 | 0.272871 | 0.815180 | -0.003656 | -0.001928 | -0.017894 | -0.009162 |
| p95 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08 | 0.139569 | 0.273253 | 0.801649 | -0.000915 | -0.001546 | -0.031425 | -0.008746 |
| 세 지표 균형 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.136110 | 0.274013 | 0.806151 | -0.004374 | -0.000786 | -0.026923 | -0.010545 |
| 세 지표 모두 개선 중 균형 최저 | PP-WHUBER7 | PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.136110 | 0.274013 | 0.806151 | -0.004374 | -0.000786 | -0.026923 | -0.010545 |
| 이번 정책 실험 최선 | PP-FPOL2 | huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5 | 0.138589 | 0.274630 | 0.815797 | -0.001895 | -0.000169 | -0.017277 | -0.005519 |

## 실험별 최적 후보

| selection | source | candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-FPOL4_mape_best | PP-FPOL4 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08 | 0.139781 | 0.272179 | 0.810159 | -0.000703 | -0.002620 | -0.022915 | -0.007906 | True |
| PP-FPOL4_balanced_best | PP-FPOL4 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.136167 | 0.272976 | 0.809351 | -0.004316 | -0.001823 | -0.023723 | -0.010884 | True |
| PP-FPOL4_p95_best | PP-FPOL4 | artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08 | 0.139569 | 0.273253 | 0.801649 | -0.000914 | -0.001546 | -0.031424 | -0.008745 | True |
| PP-FPOL5_mape_best | PP-FPOL5 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04 | 0.139781 | 0.272179 | 0.810159 | -0.000703 | -0.002620 | -0.022915 | -0.007906 | True |
| PP-FPOL5_balanced_best | PP-FPOL5 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.04 | 0.136167 | 0.272976 | 0.809351 | -0.004316 | -0.001823 | -0.023723 | -0.010884 | True |
| PP-FPOL5_p95_best | PP-FPOL5 | artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03 | 0.139569 | 0.273253 | 0.801649 | -0.000914 | -0.001546 | -0.031424 | -0.008745 | True |
| PP-FPOL6_mape_best | PP-FPOL6 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none | 0.139051 | 0.271750 | 0.810159 | -0.001432 | -0.003049 | -0.022915 | -0.009064 | True |
| PP-FPOL6_balanced_best | PP-FPOL6 | artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=none__price=mid_open_tail_guard | 0.136283 | 0.273273 | 0.801948 | -0.004201 | -0.001526 | -0.031126 | -0.011951 | True |
| PP-FPOL6_p95_best | PP-FPOL6 | artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=under_guard__price=none | 0.138911 | 0.272821 | 0.801948 | -0.001573 | -0.001978 | -0.031126 | -0.009776 | True |
| PP-FPOL7_mape_best | PP-FPOL7 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.137718 | 0.272655 | 0.810596 | -0.002766 | -0.002144 | -0.022477 | -0.009405 | True |
| PP-FPOL7_balanced_best | PP-FPOL7 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.137718 | 0.272655 | 0.810596 | -0.002766 | -0.002144 | -0.022477 | -0.009405 | True |
| PP-FPOL7_p95_best | PP-FPOL7 | artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.137718 | 0.272655 | 0.810596 | -0.002766 | -0.002144 | -0.022477 | -0.009405 | True |

## 안정성 상위 후보

| source | candidate | MdAPE | MAPE | p95_APE | stability_score | bootstrap_improve_MAPE | bootstrap_improve_p95_APE | fold_improve_MAPE | fold_improve_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-FPOL7 | PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.137718 | 0.272655 | 0.810596 | 3.628333 | 0.999167 | 0.889167 | 0.940000 | 0.800000 |
| PP-FPOL7 | PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=soft_rel__size=all | 0.137718 | 0.272655 | 0.810596 | 3.628333 | 0.999167 | 0.889167 | 0.940000 | 0.800000 |
| PP-FPOL7 | PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__rel=soft_rel__size=all | 0.137718 | 0.272655 | 0.810596 | 3.628333 | 0.999167 | 0.889167 | 0.940000 | 0.800000 |
| PP-FPOL6 | PP-FPOL6::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none | 0.139051 | 0.271750 | 0.810159 | 3.596667 | 0.997500 | 0.879167 | 0.920000 | 0.800000 |
| PP-FPOL6 | PP-FPOL6::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none | 0.139051 | 0.271750 | 0.810159 | 3.596667 | 0.997500 | 0.879167 | 0.920000 | 0.800000 |
| PP-FPOL6 | PP-FPOL6::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none | 0.139051 | 0.271750 | 0.810159 | 3.596667 | 0.997500 | 0.879167 | 0.920000 | 0.800000 |
| PP-FPOL7 | PP-FPOL7::artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.139048 | 0.272692 | 0.812053 | 3.590000 | 0.998333 | 0.891667 | 0.920000 | 0.780000 |
| PP-FPOL7 | PP-FPOL7::artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=soft_rel__size=all | 0.139048 | 0.272692 | 0.812053 | 3.590000 | 0.998333 | 0.891667 | 0.920000 | 0.780000 |
| PP-FPOL7 | PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=strict_rel__size=all | 0.138743 | 0.273039 | 0.813004 | 3.568333 | 0.999167 | 0.869167 | 0.920000 | 0.780000 |
| PP-FPOL7 | PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=strict_rel__size=all | 0.138743 | 0.273039 | 0.813004 | 3.568333 | 0.999167 | 0.869167 | 0.920000 | 0.780000 |
| PP-FPOL7 | PP-FPOL7::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__rel=strict_rel__size=all | 0.138743 | 0.273039 | 0.813004 | 3.568333 | 0.999167 | 0.869167 | 0.920000 | 0.780000 |
| PP-FPOL4 | PP-FPOL4::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08 | 0.139781 | 0.272179 | 0.810159 | 3.515000 | 0.994167 | 0.860833 | 0.880000 | 0.780000 |
| PP-FPOL5 | PP-FPOL5::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04 | 0.139781 | 0.272179 | 0.810159 | 3.515000 | 0.994167 | 0.860833 | 0.880000 | 0.780000 |
| PP-FPOL5 | PP-FPOL5::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05 | 0.139781 | 0.272179 | 0.810159 | 3.515000 | 0.994167 | 0.860833 | 0.880000 | 0.780000 |
| PP-FPOL5 | PP-FPOL5::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06 | 0.139781 | 0.272179 | 0.810159 | 3.515000 | 0.994167 | 0.860833 | 0.880000 | 0.780000 |
| PP-FPOL4 | PP-FPOL4::artist=huber_birth_generation_followers_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08 | 0.139639 | 0.272243 | 0.810549 | 3.480000 | 0.991667 | 0.848333 | 0.880000 | 0.760000 |
| PP-FPOL4 | PP-FPOL4::artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08 | 0.139118 | 0.272238 | 0.811295 | 3.449167 | 0.990000 | 0.859167 | 0.860000 | 0.740000 |
| PP-FPOL4 | PP-FPOL4::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.136167 | 0.272976 | 0.809351 | 3.328333 | 0.953333 | 0.835000 | 0.800000 | 0.740000 |
| PP-FPOL5 | PP-FPOL5::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.04 | 0.136167 | 0.272976 | 0.809351 | 3.328333 | 0.953333 | 0.835000 | 0.800000 | 0.740000 |
| PP-FPOL5 | PP-FPOL5::artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.05 | 0.136167 | 0.272976 | 0.809351 | 3.328333 | 0.953333 | 0.835000 | 0.800000 | 0.740000 |

## 해석

- 작가 생년/세대 보정을 기존 SVC/작품 보정 위에 얹는 방식은 MAPE 개선 가능성이 확인되었습니다.
- 총 보정량 cap은 `0.04` 이상에서 대부분 포화되어, cap을 더 키우는 것보다 방향/가격구간 guard가 더 의미 있었습니다.
- 가격구간 guard는 p95 큰 오차 꼬리를 낮추는 데 효과가 있었고, 방향 guard는 MAPE를 더 낮추는 데 효과가 있었습니다.
- SVC 신뢰도/작품 크기 gate는 블라인드 안전장치 후보로는 의미가 있지만, 현재 고정 테스트 점수는 FPOL6보다 낮습니다.
- 최종 후보를 하나만 고르면 test MAPE 최저인 FPOL6 후보를 우선 검토하고, 외부 블라인드 안정성을 더 중시하면 FPOL7 soft reliability 후보를 보조 후보로 두는 것이 합리적입니다.

## 산출물

- `outputs/all_fpol4_7_test_metrics.csv`
- `outputs/experiment_best_summary.csv`
- `outputs/stability_joined_test_metrics.csv`
- `outputs/final_recommendations.csv`
