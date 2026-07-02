# Track6 frozen dataset build report

- created_at: `2026-06-19T13:51:54`
- status: `pass`
- repo_root: `/Users/bo/VisionAI`
- source_dir: `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share`
- frozen_output_dir: `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/05_generated_frozen_training_dataset/track6_split`

## 1. Source files

| source | destination | bytes | sha256 |
|---|---|---:|---|
| `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/01_source_files/saatchi_cleaned.csv` | `/Users/bo/VisionAI/data/saatchi_cleaned.csv` | `12551671` | `e8ba0d545ee43c0bc3449085c948c1641a84fae6d94445a9ab43e9fa3692f3d7` |
| `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/01_source_files/artsy_kr_artworks.csv` | `/Users/bo/VisionAI/data/artsy_kr_artworks.csv` | `11749057` | `b3ca65992975afed49f8cf9936b6975fcbb8c208a559ca51be0b0efcc569b583` |
| `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/01_source_files/artue_테스트_가격포함.csv` | `/Users/bo/VisionAI/data/artue_테스트_가격포함.csv` | `488469` | `7bb51da9f7b0dff8a6d30d811d5f425a8e76afb46d42511b13d6fb8e6e005682` |
| `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/01_source_files/1차 시장 데이터 - 전달본_260504.csv` | `/Users/bo/VisionAI/data/1차 시장 데이터 - 전달본_260504.csv` | `83592` | `89b6779331a80c67aa61bd5995136b2cf6eb3f939eec32e2442f9d7b91e7b7e4` |
| `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/01_source_files/track6_reference/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv` | `/Users/bo/VisionAI/data/track6/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv` | `426782` | `1b9608fe483c3c4d18f491e918faa71033a1775c17ee0ab05cca336d7369fd03` |

## 2. Pipeline steps

| step | script | return code | role |
|---|---|---:|---|
| `track4_cleaning_pipeline` | `scripts/track4/run_cleaning_pipeline.py` | `0` | 원본 CSV를 통합하고 가격/크기/재료/중복 감사를 거쳐 Track4 feature candidate를 만든다. |
| `track6_artist_korean_name_correction` | `scripts/track6/improve_artist_korean_names.py` | `0` | 검수된 override 기준으로 작가 한글명을 보정하고 원래 이름을 보존한다. |
| `track6_artist_metadata_enrichment` | `scripts/track6/enrich_track6_artist_metadata.py` | `0` | raw 수집 row에서 작가 메타 정보를 Track6 후보 데이터에 row 단위로 붙인다. |
| `track6_nant_material_enrichment` | `scripts/track6/enrich_track6_nant_material.py` | `0` | 난트 기준 재료/지지체 보강 컬럼을 후보 데이터에 붙인다. |
| `track6_feature_label_export` | `scripts/track6/export_feature_label_splits.py` | `0` | full split에서 모델 입력 feature와 평가 label을 물리적으로 분리한다. |

## 3. Frozen output audit

- audit_status: `pass`

| path | status | actual | expected | reason |
|---|---|---|---|---|
| `track6_train.csv` | `PASS` | `{"rows": 26914, "columns": 50}` | `{"rows": 26914, "columns": 50}` | `ok` |
| `track6_val_warm.csv` | `PASS` | `{"rows": 519, "columns": 50}` | `{"rows": 519, "columns": 50}` | `ok` |
| `track6_test_warm.csv` | `PASS` | `{"rows": 607, "columns": 50}` | `{"rows": 607, "columns": 50}` | `ok` |
| `track6_val_cold.csv` | `PASS` | `{"rows": 2753, "columns": 50}` | `{"rows": 2753, "columns": 50}` | `ok` |
| `track6_test_cold.csv` | `PASS` | `{"rows": 3099, "columns": 50}` | `{"rows": 3099, "columns": 50}` | `ok` |
| `features/warm/track6_train_warm_features.csv` | `PASS` | `{"rows": 26914, "columns": 23}` | `{"rows": 26914, "columns": 23}` | `ok` |
| `features/warm/track6_val_warm_warm_features.csv` | `PASS` | `{"rows": 519, "columns": 23}` | `{"rows": 519, "columns": 23}` | `ok` |
| `features/warm/track6_test_warm_warm_features.csv` | `PASS` | `{"rows": 607, "columns": 23}` | `{"rows": 607, "columns": 23}` | `ok` |
| `features/cold/track6_train_cold_features.csv` | `PASS` | `{"rows": 26914, "columns": 20}` | `{"rows": 26914, "columns": 20}` | `ok` |
| `features/cold/track6_val_cold_cold_features.csv` | `PASS` | `{"rows": 2753, "columns": 20}` | `{"rows": 2753, "columns": 20}` | `ok` |
| `features/cold/track6_test_cold_cold_features.csv` | `PASS` | `{"rows": 3099, "columns": 20}` | `{"rows": 3099, "columns": 20}` | `ok` |
| `labels/track6_train_labels.csv` | `PASS` | `{"rows": 26914, "columns": 12}` | `{"rows": 26914, "columns": 12}` | `ok` |
| `labels/track6_val_warm_labels.csv` | `PASS` | `{"rows": 519, "columns": 12}` | `{"rows": 519, "columns": 12}` | `ok` |
| `labels/track6_test_warm_labels.csv` | `PASS` | `{"rows": 607, "columns": 12}` | `{"rows": 607, "columns": 12}` | `ok` |
| `labels/track6_val_cold_labels.csv` | `PASS` | `{"rows": 2753, "columns": 12}` | `{"rows": 2753, "columns": 12}` | `ok` |
| `labels/track6_test_cold_labels.csv` | `PASS` | `{"rows": 3099, "columns": 12}` | `{"rows": 3099, "columns": 12}` | `ok` |
| `track6_val_warm.csv` | `PASS` | `{"min_train_history": 5}` | `{"min_train_history_gte": 5}` | `warm_train_history_check` |
| `track6_test_warm.csv` | `PASS` | `{"min_train_history": 5}` | `{"min_train_history_gte": 5}` | `warm_train_history_check` |
| `track6_val_cold.csv` | `PASS` | `{"artist_key_overlap": 0, "artist_name_ko_overlap": 0, "artist_name_ko_orig_overlap": 0, "artist_works_log_nonzero_rows": 0}` | `{"artist_key_overlap": 0, "artist_name_ko_overlap": 0, "artist_name_ko_orig_overlap": 0, "artist_works_log_nonzero_rows": 0}` | `cold_no_train_overlap_check` |
| `track6_test_cold.csv` | `PASS` | `{"artist_key_overlap": 0, "artist_name_ko_overlap": 0, "artist_name_ko_orig_overlap": 0, "artist_works_log_nonzero_rows": 0}` | `{"artist_key_overlap": 0, "artist_name_ko_overlap": 0, "artist_name_ko_orig_overlap": 0, "artist_works_log_nonzero_rows": 0}` | `cold_no_train_overlap_check` |
