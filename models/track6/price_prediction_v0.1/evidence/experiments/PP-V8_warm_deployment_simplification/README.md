# PP-V8 Warm 배포 단순화 후보 검증

- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.
- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.

## Test 결과 상위

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `component_v1_representative` | `deployment_component` | 0.1621 | 0.3044 | 1.0335 | 0.4220 |
| `warm` | `deployment_single_mdape` | `deployment_simplification` | 0.1621 | 0.3044 | 1.0335 | 0.4220 |
| `warm` | `deployment_single_p95_guarded` | `deployment_simplification` | 0.1621 | 0.3044 | 1.0335 | 0.4220 |
| `warm` | `compact_blend_mape_guarded` | `deployment_simplification` | 0.1632 | 0.2816 | 0.9311 | 0.4028 |
| `warm` | `compact_blend_mdape` | `deployment_simplification` | 0.1635 | 0.2868 | 0.9190 | 0.4067 |
| `warm` | `compact_blend_p95_guarded` | `deployment_simplification` | 0.1651 | 0.2852 | 0.9322 | 0.4065 |
| `warm` | `component_v2_defensive` | `deployment_component` | 0.1680 | 0.2873 | 0.9287 | 0.4102 |
| `warm` | `deployment_single_mape_guarded` | `deployment_simplification` | 0.1680 | 0.2873 | 0.9287 | 0.4102 |
| `warm` | `component_l10_meta_external_search_seq` | `deployment_component` | 0.1708 | 0.3363 | 1.1432 | 0.4507 |
| `warm` | `component_l10_generated_bucket_seq` | `deployment_component` | 0.1743 | 0.3265 | 0.9818 | 0.4396 |

## 선택/가중치 맵

| experiment_id | policy | selected_label | validation_RMSE_log | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_Within_30 | validation_Within_50 | step | weight_v1_representative | weight_v2_defensive | weight_l10_generated_bucket_seq | weight_l10_meta_external_search_seq |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-V8 | single_mdape | v1_representative | 0.391965 | 0.153965 | 0.265989 | 0.804721 | 0.720617 | 0.878613 |  |  |  |  |  |
| PP-V8 | single_mape_guarded | v2_defensive | 0.378699 | 0.160273 | 0.261253 | 0.814728 | 0.712909 | 0.888247 |  |  |  |  |  |
| PP-V8 | single_p95_guarded | v1_representative | 0.391965 | 0.153965 | 0.265989 | 0.804721 | 0.720617 | 0.878613 |  |  |  |  |  |
| PP-V8 | compact_blend_mdape |  | 0.373915 | 0.142265 | 0.256939 | 0.757757 | 0.71869 | 0.876686 | 0.25 | 0 | 0.5 | 0.25 | 0.25 |
| PP-V8 | compact_blend_mape_guarded |  | 0.372063 | 0.154389 | 0.254387 | 0.808363 | 0.722543 | 0.888247 | 0.25 | 0 | 0.75 | 0.25 | 0 |
| PP-V8 | compact_blend_p95_guarded |  | 0.37281 | 0.156583 | 0.255235 | 0.749131 | 0.726397 | 0.890173 | 0.25 | 0 | 0.75 | 0 | 0.25 |
