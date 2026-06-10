# PP-FPOL10 모델 간 예측 gap 기반 라우팅

- 작성일: 2026-06-08 16:32
- source: FPOL6 top candidates
- row-aligned auxiliary models: P2, L8, L9, M1

## Test 상위 후보

| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.136967 | 0.272366 | 0.810388 | -0.003517 | -0.002433 | -0.022686 | -0.009545 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.136967 | 0.272366 | 0.810388 | -0.003517 | -0.002433 | -0.022686 | -0.009545 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.136967 | 0.272366 | 0.810388 | -0.003517 | -0.002433 | -0.022686 | -0.009545 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.136750 | 0.272426 | 0.812108 | -0.003734 | -0.002373 | -0.020966 | -0.009024 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.136750 | 0.272426 | 0.812108 | -0.003734 | -0.002373 | -0.020966 | -0.009024 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__gaproute=large_gap_damp_source | 0.139051 | 0.272130 | 0.811140 | -0.001432 | -0.002669 | -0.021934 | -0.008678 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__gaproute=large_gap_damp_source | 0.139051 | 0.272130 | 0.811140 | -0.001432 | -0.002669 | -0.021934 | -0.008678 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__gaproute=large_gap_damp_source | 0.139051 | 0.272130 | 0.811140 | -0.001432 | -0.002669 | -0.021934 | -0.008678 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=tail_open_mid_guard__gaproute=large_gap_damp_source | 0.138397 | 0.272447 | 0.811791 | -0.002087 | -0.002352 | -0.021282 | -0.008574 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=tail_open_mid_guard__gaproute=large_gap_damp_source | 0.138397 | 0.272447 | 0.811791 | -0.002087 | -0.002352 | -0.021282 | -0.008574 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=tail_open_mid_guard__gaproute=large_gap_damp_source | 0.138397 | 0.272447 | 0.811791 | -0.002087 | -0.002352 | -0.021282 | -0.008574 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=none__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.140476 | 0.272667 | 0.810388 | -0.000008 | -0.002132 | -0.022686 | -0.008275 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=none__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.140476 | 0.272667 | 0.810388 | -0.000008 | -0.002132 | -0.022686 | -0.008275 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=none__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.140476 | 0.272667 | 0.810388 | -0.000008 | -0.002132 | -0.022686 | -0.008275 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__gaproute=large_gap_damp_source | 0.139118 | 0.272143 | 0.812661 | -0.001366 | -0.002656 | -0.020413 | -0.008145 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__gaproute=large_gap_damp_source | 0.139118 | 0.272143 | 0.812661 | -0.001366 | -0.002656 | -0.020413 | -0.008145 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=none__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.139480 | 0.272748 | 0.812108 | -0.001004 | -0.002051 | -0.020966 | -0.008007 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=none__price=mid_open_tail_guard__gaproute=large_gap_damp_source | 0.139480 | 0.272748 | 0.812108 | -0.001004 | -0.002051 | -0.020966 | -0.008007 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=tail_open_mid_guard__gaproute=large_gap_damp_source | 0.139118 | 0.272425 | 0.813169 | -0.001366 | -0.002374 | -0.019905 | -0.007882 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=tail_open_mid_guard__gaproute=large_gap_damp_source | 0.139118 | 0.272425 | 0.813169 | -0.001366 | -0.002374 | -0.019905 | -0.007882 | True |

## 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions.csv`
- `artifacts/experiment_manifest.json`
