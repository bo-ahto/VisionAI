# PP-FPOL9 quantile width 기반 동적 cap/strength

- 작성일: 2026-06-08 16:32
- source: FPOL6 top 20
- validation routing_width 33/66 cuts: 1.184692, 1.614263

## Test 상위 후보

| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=conservative_high_width | 0.136549 | 0.272893 | 0.808567 | -0.003935 | -0.001906 | -0.024507 | -0.010116 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__qwidth=conservative_high_width | 0.136549 | 0.272893 | 0.808567 | -0.003935 | -0.001906 | -0.024507 | -0.010116 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=mid_open_tail_guard__qwidth=conservative_high_width | 0.136549 | 0.272893 | 0.808567 | -0.003935 | -0.001906 | -0.024507 | -0.010116 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=balanced_width_budget | 0.137738 | 0.272482 | 0.808250 | -0.002745 | -0.002317 | -0.024823 | -0.009962 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__qwidth=balanced_width_budget | 0.137738 | 0.272482 | 0.808250 | -0.002745 | -0.002317 | -0.024823 | -0.009962 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=mid_open_tail_guard__qwidth=balanced_width_budget | 0.137738 | 0.272482 | 0.808250 | -0.002745 | -0.002317 | -0.024823 | -0.009962 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=confident_strong_uncertain_weak | 0.138455 | 0.272603 | 0.807755 | -0.002028 | -0.002196 | -0.025318 | -0.009848 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__qwidth=confident_strong_uncertain_weak | 0.138455 | 0.272603 | 0.807755 | -0.002028 | -0.002196 | -0.025318 | -0.009848 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=mid_open_tail_guard__qwidth=confident_strong_uncertain_weak | 0.138455 | 0.272603 | 0.807755 | -0.002028 | -0.002196 | -0.025318 | -0.009848 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__qwidth=balanced_width_budget | 0.137738 | 0.272308 | 0.808890 | -0.002745 | -0.002491 | -0.024183 | -0.009807 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__qwidth=balanced_width_budget | 0.137738 | 0.272308 | 0.808890 | -0.002745 | -0.002491 | -0.024183 | -0.009807 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__qwidth=balanced_width_budget | 0.137738 | 0.272308 | 0.808890 | -0.002745 | -0.002491 | -0.024183 | -0.009807 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__qwidth=balanced_width_budget | 0.136523 | 0.272590 | 0.810630 | -0.003961 | -0.002209 | -0.022443 | -0.009538 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__qwidth=balanced_width_budget | 0.136523 | 0.272590 | 0.810630 | -0.003961 | -0.002209 | -0.022443 | -0.009538 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__qwidth=confident_strong_uncertain_weak | 0.139066 | 0.272474 | 0.808230 | -0.001418 | -0.002325 | -0.024844 | -0.009529 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__qwidth=confident_strong_uncertain_weak | 0.139066 | 0.272474 | 0.808230 | -0.001418 | -0.002325 | -0.024844 | -0.009529 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__qwidth=confident_strong_uncertain_weak | 0.139066 | 0.272474 | 0.808230 | -0.001418 | -0.002325 | -0.024844 | -0.009529 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__qwidth=conservative_high_width | 0.138397 | 0.272757 | 0.808848 | -0.002087 | -0.002041 | -0.024226 | -0.009451 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__qwidth=conservative_high_width | 0.138397 | 0.272757 | 0.808848 | -0.002087 | -0.002041 | -0.024226 | -0.009451 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__qwidth=conservative_high_width | 0.138397 | 0.272757 | 0.808848 | -0.002087 | -0.002041 | -0.024226 | -0.009451 | True |

## 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions.csv`
- `artifacts/experiment_manifest.json`
