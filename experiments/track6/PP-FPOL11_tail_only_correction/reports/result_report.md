# PP-FPOL11 tail-only 보정

- 작성일: 2026-06-08 16:06
- tail definition: pred_log_bin low/high plus optional size small/large
- purpose: p95 큰 오차 방어 전용 후보 확인

## Test 상위 후보

| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__tail=price_or_size_tail | 0.138401 | 0.272752 | 0.813008 | -0.002083 | -0.002047 | -0.020065 | -0.008065 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__tail=price_or_size_tail | 0.138401 | 0.272752 | 0.813008 | -0.002083 | -0.002047 | -0.020065 | -0.008065 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=mid_open_tail_guard__tail=price_or_size_tail | 0.138401 | 0.272752 | 0.813008 | -0.002083 | -0.002047 | -0.020065 | -0.008065 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__tail=tail_full_core_soft | 0.137686 | 0.273195 | 0.815350 | -0.002797 | -0.001604 | -0.017724 | -0.007375 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__tail=tail_full_core_soft | 0.137686 | 0.273195 | 0.815350 | -0.002797 | -0.001604 | -0.017724 | -0.007375 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=mid_open_tail_guard__tail=tail_full_core_soft | 0.137686 | 0.273195 | 0.815350 | -0.002797 | -0.001604 | -0.017724 | -0.007375 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=none__price=mid_open_tail_guard__tail=price_or_size_tail | 0.139978 | 0.273011 | 0.813671 | -0.000506 | -0.001788 | -0.019402 | -0.007232 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=none__price=mid_open_tail_guard__tail=price_or_size_tail | 0.139978 | 0.273011 | 0.813671 | -0.000506 | -0.001788 | -0.019402 | -0.007232 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=none__price=mid_open_tail_guard__tail=price_or_size_tail | 0.140864 | 0.272989 | 0.813008 | 0.000380 | -0.001810 | -0.020065 | -0.007165 | False |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=none__price=mid_open_tail_guard__tail=price_or_size_tail | 0.140864 | 0.272989 | 0.813008 | 0.000380 | -0.001810 | -0.020065 | -0.007165 | False |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=none__price=mid_open_tail_guard__tail=price_or_size_tail | 0.140864 | 0.272989 | 0.813008 | 0.000380 | -0.001810 | -0.020065 | -0.007165 | False |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__tail=price_or_size_tail | 0.140520 | 0.272768 | 0.813671 | 0.000036 | -0.002031 | -0.019402 | -0.007132 | False |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__tail=price_or_size_tail | 0.140520 | 0.272768 | 0.813671 | 0.000036 | -0.002031 | -0.019402 | -0.007132 | False |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__tail=price_or_size_tail | 0.140912 | 0.272517 | 0.813561 | 0.000429 | -0.002282 | -0.019513 | -0.007122 | False |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__tail=price_or_size_tail | 0.140912 | 0.272517 | 0.813561 | 0.000429 | -0.002282 | -0.019513 | -0.007122 | False |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__tail=price_or_size_tail | 0.140912 | 0.272517 | 0.813561 | 0.000429 | -0.002282 | -0.019513 | -0.007122 | False |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__tail=price_or_size_tail | 0.140695 | 0.272482 | 0.814224 | 0.000211 | -0.002317 | -0.018850 | -0.006985 | False |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__tail=price_or_size_tail | 0.140695 | 0.272482 | 0.814224 | 0.000211 | -0.002317 | -0.018850 | -0.006985 | False |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=tail_open_mid_guard__tail=price_or_size_tail | 0.140695 | 0.272683 | 0.814419 | 0.000211 | -0.002116 | -0.018654 | -0.006853 | False |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=tail_open_mid_guard__tail=price_or_size_tail | 0.140695 | 0.272683 | 0.814419 | 0.000211 | -0.002116 | -0.018654 | -0.006853 | False |

## 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions.csv`
- `artifacts/experiment_manifest.json`
