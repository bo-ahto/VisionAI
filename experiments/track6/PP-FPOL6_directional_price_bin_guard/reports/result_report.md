# PP-FPOL6 방향별/가격구간 guard 실험

- 작성일: 2026-06-08 15:46
- source 후보 수: 20
- direction modes: ['none', 'under_guard', 'over_guard', 'balanced_soft']
- price modes: ['none', 'mid_open_tail_guard', 'tail_open_mid_guard']

## Test 상위 후보

| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=none__price=mid_open_tail_guard | 0.1363 | 0.2733 | 0.8019 | -0.0042 | -0.0015 | -0.0311 | -0.0120 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.04__direction=none__price=mid_open_tail_guard | 0.1363 | 0.2733 | 0.8019 | -0.0042 | -0.0015 | -0.0311 | -0.0120 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.05__direction=none__price=mid_open_tail_guard | 0.1363 | 0.2733 | 0.8019 | -0.0042 | -0.0015 | -0.0311 | -0.0120 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.06__direction=none__price=mid_open_tail_guard | 0.1363 | 0.2733 | 0.8019 | -0.0042 | -0.0015 | -0.0311 | -0.0120 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=under_guard__price=mid_open_tail_guard | 0.1368 | 0.2730 | 0.8022 | -0.0037 | -0.0018 | -0.0308 | -0.0117 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard | 0.1368 | 0.2730 | 0.8022 | -0.0037 | -0.0018 | -0.0308 | -0.0117 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard | 0.1368 | 0.2730 | 0.8022 | -0.0037 | -0.0018 | -0.0308 | -0.0117 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=mid_open_tail_guard | 0.1368 | 0.2730 | 0.8022 | -0.0037 | -0.0018 | -0.0308 | -0.0117 | True |
| artist=none__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.02__direction=under_guard__price=mid_open_tail_guard | 0.1342 | 0.2732 | 0.8147 | -0.0063 | -0.0016 | -0.0183 | -0.0116 | True |
| artist=none__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.03__direction=under_guard__price=mid_open_tail_guard | 0.1343 | 0.2731 | 0.8147 | -0.0061 | -0.0017 | -0.0183 | -0.0115 | True |
| artist=none__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard | 0.1343 | 0.2731 | 0.8147 | -0.0061 | -0.0017 | -0.0183 | -0.0115 | True |
| artist=none__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.05__direction=under_guard__price=mid_open_tail_guard | 0.1343 | 0.2731 | 0.8147 | -0.0061 | -0.0017 | -0.0183 | -0.0115 | True |
| artist=none__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.06__direction=under_guard__price=mid_open_tail_guard | 0.1343 | 0.2731 | 0.8147 | -0.0061 | -0.0017 | -0.0183 | -0.0115 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_predbin_mid_open_tail_guard_cap0p06_s0p35__totalcap=0.02__direction=under_guard__price=mid_open_tail_guard | 0.1358 | 0.2730 | 0.8079 | -0.0047 | -0.0018 | -0.0252 | -0.0115 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.03__direction=none__price=mid_open_tail_guard | 0.1368 | 0.2733 | 0.8021 | -0.0037 | -0.0015 | -0.0309 | -0.0113 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=balanced_soft__price=mid_open_tail_guard | 0.1366 | 0.2735 | 0.8034 | -0.0039 | -0.0013 | -0.0296 | -0.0112 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.04__direction=balanced_soft__price=mid_open_tail_guard | 0.1366 | 0.2735 | 0.8034 | -0.0039 | -0.0013 | -0.0296 | -0.0112 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.05__direction=balanced_soft__price=mid_open_tail_guard | 0.1366 | 0.2735 | 0.8034 | -0.0039 | -0.0013 | -0.0296 | -0.0112 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.06__direction=balanced_soft__price=mid_open_tail_guard | 0.1366 | 0.2735 | 0.8034 | -0.0039 | -0.0013 | -0.0296 | -0.0112 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard | 0.1370 | 0.2720 | 0.8089 | -0.0035 | -0.0028 | -0.0242 | -0.0112 | True |

## 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/experiment_manifest.json`