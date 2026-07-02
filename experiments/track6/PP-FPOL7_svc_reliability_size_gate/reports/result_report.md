# PP-FPOL7 SVC 신뢰도/작품 크기 gate 실험

- 작성일: 2026-06-08 15:47
- source 후보 수: 20
- reliability modes: ['soft_rel', 'strict_rel']
- size modes: ['all', 'non_small', 'large_tail']

## Test 상위 후보

| candidate | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | balanced_delta | improves_all_three |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1377 | 0.2727 | 0.8106 | -0.0028 | -0.0021 | -0.0225 | -0.0094 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1377 | 0.2727 | 0.8106 | -0.0028 | -0.0021 | -0.0225 | -0.0094 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1377 | 0.2727 | 0.8106 | -0.0028 | -0.0021 | -0.0225 | -0.0094 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1390 | 0.2727 | 0.8121 | -0.0014 | -0.0021 | -0.0210 | -0.0077 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1390 | 0.2727 | 0.8121 | -0.0014 | -0.0021 | -0.0210 | -0.0077 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=strict_rel__size=all | 0.1387 | 0.2730 | 0.8130 | -0.0017 | -0.0018 | -0.0201 | -0.0075 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=strict_rel__size=all | 0.1387 | 0.2730 | 0.8130 | -0.0017 | -0.0018 | -0.0201 | -0.0075 | True |
| artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__rel=strict_rel__size=all | 0.1387 | 0.2730 | 0.8130 | -0.0017 | -0.0018 | -0.0201 | -0.0075 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1385 | 0.2734 | 0.8136 | -0.0020 | -0.0014 | -0.0195 | -0.0073 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1385 | 0.2734 | 0.8136 | -0.0020 | -0.0014 | -0.0195 | -0.0073 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1385 | 0.2734 | 0.8136 | -0.0020 | -0.0014 | -0.0195 | -0.0073 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.06__direction=under_guard__price=none__rel=soft_rel__size=all | 0.1385 | 0.2734 | 0.8136 | -0.0020 | -0.0014 | -0.0195 | -0.0073 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=under_guard__price=mid_open_tail_guard__rel=soft_rel__size=all | 0.1395 | 0.2735 | 0.8136 | -0.0009 | -0.0013 | -0.0195 | -0.0061 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=mid_open_tail_guard__rel=soft_rel__size=all | 0.1395 | 0.2735 | 0.8136 | -0.0009 | -0.0013 | -0.0195 | -0.0061 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.04__direction=under_guard__price=none__rel=strict_rel__size=all | 0.1400 | 0.2731 | 0.8137 | -0.0004 | -0.0017 | -0.0194 | -0.0060 | True |
| artist=huber_birth_generation_for_sale_gatenone_alpha0p01_cap0p03_s0p5__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08__totalcap=0.05__direction=under_guard__price=none__rel=strict_rel__size=all | 0.1400 | 0.2731 | 0.8137 | -0.0004 | -0.0017 | -0.0194 | -0.0060 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.03__direction=none__price=mid_open_tail_guard__rel=soft_rel__size=all | 0.1395 | 0.2737 | 0.8136 | -0.0009 | -0.0011 | -0.0195 | -0.0059 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.04__direction=none__price=mid_open_tail_guard__rel=soft_rel__size=all | 0.1395 | 0.2737 | 0.8136 | -0.0009 | -0.0011 | -0.0195 | -0.0059 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.05__direction=none__price=mid_open_tail_guard__rel=soft_rel__size=all | 0.1395 | 0.2737 | 0.8136 | -0.0009 | -0.0011 | -0.0195 | -0.0059 | True |
| artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08__totalcap=0.06__direction=none__price=mid_open_tail_guard__rel=soft_rel__size=all | 0.1395 | 0.2737 | 0.8136 | -0.0009 | -0.0011 | -0.0195 | -0.0059 | True |

## 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/experiment_manifest.json`