# PP-FPOL4 2단계 작가+SVC 보정 스택

- 작성일: 2026-06-08 15:45
- artist 후보 수: 5
- SVC 후보 수: 10

## Test 상위 후보

| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.1362 | 0.2730 | 0.8094 | -0.0043 | -0.0018 | -0.0237 | -0.0109 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.1361 | 0.2740 | 0.8062 | -0.0044 | -0.0008 | -0.0269 | -0.0105 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.1361 | 0.2741 | 0.8062 | -0.0044 | -0.0007 | -0.0269 | -0.0105 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p06 | 0.1357 | 0.2732 | 0.8138 | -0.0048 | -0.0016 | -0.0193 | -0.0102 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p06 | 0.1373 | 0.2735 | 0.8055 | -0.0032 | -0.0013 | -0.0275 | -0.0100 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p06 | 0.1361 | 0.2731 | 0.8137 | -0.0043 | -0.0017 | -0.0194 | -0.0099 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.1371 | 0.2739 | 0.8047 | -0.0033 | -0.0009 | -0.0284 | -0.0099 | True |
| artist=none__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.1354 | 0.2736 | 0.8153 | -0.0051 | -0.0012 | -0.0177 | -0.0099 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.1372 | 0.2739 | 0.8047 | -0.0032 | -0.0009 | -0.0284 | -0.0099 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08 | 0.1384 | 0.2731 | 0.8036 | -0.0021 | -0.0017 | -0.0295 | -0.0097 | True |
| artist=none__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p06 | 0.1362 | 0.2731 | 0.8148 | -0.0043 | -0.0017 | -0.0182 | -0.0096 | True |
| artist=none__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p06 | 0.1362 | 0.2732 | 0.8150 | -0.0043 | -0.0016 | -0.0181 | -0.0095 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08 | 0.1368 | 0.2728 | 0.8140 | -0.0036 | -0.0020 | -0.0191 | -0.0095 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.1361 | 0.2736 | 0.8142 | -0.0044 | -0.0012 | -0.0189 | -0.0094 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p08 | 0.1368 | 0.2729 | 0.8140 | -0.0036 | -0.0019 | -0.0191 | -0.0094 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_dir_under_guard_cap0p08 | 0.1387 | 0.2731 | 0.8036 | -0.0018 | -0.0017 | -0.0294 | -0.0093 | True |
| artist=huber_birth_generation_followers_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p001_dir_under_guard_cap0p06 | 0.1380 | 0.2727 | 0.8098 | -0.0025 | -0.0021 | -0.0232 | -0.0093 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p06 | 0.1383 | 0.2725 | 0.8094 | -0.0021 | -0.0023 | -0.0237 | -0.0092 | True |
| artist=ridge_birth_generation_gatenone_alpha0p1_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p06 | 0.1387 | 0.2734 | 0.8032 | -0.0018 | -0.0014 | -0.0298 | -0.0092 | True |
| artist=huber_birth_generation_followers_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35 | 0.1377 | 0.2730 | 0.8097 | -0.0028 | -0.0018 | -0.0233 | -0.0092 | True |

## 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/experiment_manifest.json`