# PP-FPOL5 총 보정량 cap/budget 실험

- 작성일: 2026-06-08 15:45
- source 후보 수: 24
- cap 후보: [0.02, 0.03, 0.04, 0.05, 0.06]

## Test 상위 후보

| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.04 | 0.1362 | 0.2730 | 0.8094 | -0.0043 | -0.0018 | -0.0237 | -0.0109 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.05 | 0.1362 | 0.2730 | 0.8094 | -0.0043 | -0.0018 | -0.0237 | -0.0109 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.06 | 0.1362 | 0.2730 | 0.8094 | -0.0043 | -0.0018 | -0.0237 | -0.0109 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.03 | 0.1362 | 0.2730 | 0.8093 | -0.0043 | -0.0018 | -0.0238 | -0.0108 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.02 | 0.1362 | 0.2733 | 0.8082 | -0.0043 | -0.0015 | -0.0249 | -0.0108 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.03 | 0.1361 | 0.2740 | 0.8062 | -0.0044 | -0.0008 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.04 | 0.1361 | 0.2740 | 0.8062 | -0.0044 | -0.0008 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.05 | 0.1361 | 0.2740 | 0.8062 | -0.0044 | -0.0008 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.06 | 0.1361 | 0.2740 | 0.8062 | -0.0044 | -0.0008 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.03 | 0.1361 | 0.2741 | 0.8062 | -0.0044 | -0.0007 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.04 | 0.1361 | 0.2741 | 0.8062 | -0.0044 | -0.0007 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.05 | 0.1361 | 0.2741 | 0.8062 | -0.0044 | -0.0007 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.06 | 0.1361 | 0.2741 | 0.8062 | -0.0044 | -0.0007 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.02 | 0.1361 | 0.2741 | 0.8067 | -0.0044 | -0.0007 | -0.0264 | -0.0104 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.02 | 0.1361 | 0.2741 | 0.8067 | -0.0044 | -0.0007 | -0.0264 | -0.0104 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p06__totalcap=0.04 | 0.1357 | 0.2732 | 0.8138 | -0.0048 | -0.0016 | -0.0193 | -0.0102 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p06__totalcap=0.05 | 0.1357 | 0.2732 | 0.8138 | -0.0048 | -0.0016 | -0.0193 | -0.0102 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p06__totalcap=0.06 | 0.1357 | 0.2732 | 0.8138 | -0.0048 | -0.0016 | -0.0193 | -0.0102 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p06__totalcap=0.03 | 0.1357 | 0.2732 | 0.8136 | -0.0048 | -0.0016 | -0.0194 | -0.0102 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p06__totalcap=0.02 | 0.1357 | 0.2734 | 0.8131 | -0.0048 | -0.0014 | -0.0200 | -0.0101 | True |

## 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/experiment_manifest.json`