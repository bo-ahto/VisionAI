# Frozen Track6 기존 실험 데이터셋 종합 점검

- status: `pass`
- repo root: `/Users/bo/VisionAI`
- 공유 폴더: `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share`
- 모델 번들 기준 split: `/Users/bo/VisionAI/models/track6/price_prediction_v0.1/data/training/track6_split`
- 공유 frozen split: `/Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/03_frozen_training_dataset/track6_split`

## 원본 CSV 요약

| file | rows | columns | bytes |
|---|---:|---:|---:|
| `1차 시장 데이터 - 전달본_260504.csv` | `292` | `26` | `83592` |
| `artsy_kr_artworks.csv` | `30046` | `30` | `11749057` |
| `artue_테스트_가격포함.csv` | `2783` | `15` | `488469` |
| `saatchi_cleaned.csv` | `21721` | `58` | `12551671` |

## 점검 결과

| check | status | detail |
|---|---|---|
| exists: share root | `PASS` | /Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share |
| exists: model bundle frozen split | `PASS` | /Users/bo/VisionAI/models/track6/price_prediction_v0.1/data/training/track6_split |
| exists: shared frozen split | `PASS` | /Users/bo/VisionAI/docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/03_frozen_training_dataset/track6_split |
| checksum: shared frozen split matches model bundle | `PASS` | checked=21, missing=0, mismatch=0 |
| shape: full split: track6_train.csv | `PASS` | actual={'rows': 26914, 'columns': 50}, expected={'rows': 26914, 'columns': 50} |
| shape: full split: track6_val_warm.csv | `PASS` | actual={'rows': 519, 'columns': 50}, expected={'rows': 519, 'columns': 50} |
| shape: full split: track6_test_warm.csv | `PASS` | actual={'rows': 607, 'columns': 50}, expected={'rows': 607, 'columns': 50} |
| shape: full split: track6_val_cold.csv | `PASS` | actual={'rows': 2753, 'columns': 50}, expected={'rows': 2753, 'columns': 50} |
| shape: full split: track6_test_cold.csv | `PASS` | actual={'rows': 3099, 'columns': 50}, expected={'rows': 3099, 'columns': 50} |
| shape: features: features/warm/track6_train_warm_features.csv | `PASS` | actual={'rows': 26914, 'columns': 23}, expected={'rows': 26914, 'columns': 23} |
| shape: features: features/warm/track6_val_warm_warm_features.csv | `PASS` | actual={'rows': 519, 'columns': 23}, expected={'rows': 519, 'columns': 23} |
| shape: features: features/warm/track6_test_warm_warm_features.csv | `PASS` | actual={'rows': 607, 'columns': 23}, expected={'rows': 607, 'columns': 23} |
| shape: features: features/cold/track6_train_cold_features.csv | `PASS` | actual={'rows': 26914, 'columns': 20}, expected={'rows': 26914, 'columns': 20} |
| shape: features: features/cold/track6_val_cold_cold_features.csv | `PASS` | actual={'rows': 2753, 'columns': 20}, expected={'rows': 2753, 'columns': 20} |
| shape: features: features/cold/track6_test_cold_cold_features.csv | `PASS` | actual={'rows': 3099, 'columns': 20}, expected={'rows': 3099, 'columns': 20} |
| shape: labels: labels/track6_train_labels.csv | `PASS` | actual={'rows': 26914, 'columns': 12}, expected={'rows': 26914, 'columns': 12} |
| shape: labels: labels/track6_val_warm_labels.csv | `PASS` | actual={'rows': 519, 'columns': 12}, expected={'rows': 519, 'columns': 12} |
| shape: labels: labels/track6_test_warm_labels.csv | `PASS` | actual={'rows': 607, 'columns': 12}, expected={'rows': 607, 'columns': 12} |
| shape: labels: labels/track6_val_cold_labels.csv | `PASS` | actual={'rows': 2753, 'columns': 12}, expected={'rows': 2753, 'columns': 12} |
| shape: labels: labels/track6_test_cold_labels.csv | `PASS` | actual={'rows': 3099, 'columns': 12}, expected={'rows': 3099, 'columns': 12} |
| warm definition: track6_val_warm.csv | `PASS` | min_train_history=5, missing_artist_rows=0 |
| warm definition: track6_test_warm.csv | `PASS` | min_train_history=5, missing_artist_rows=0 |
| cold definition: track6_val_cold.csv | `PASS` | artist_key_overlap=0, artist_name_ko_overlap=0, artist_name_ko_orig_overlap=0, artist_works_log_nonzero_rows=0 |
| cold definition: track6_test_cold.csv | `PASS` | artist_key_overlap=0, artist_name_ko_overlap=0, artist_name_ko_orig_overlap=0, artist_works_log_nonzero_rows=0 |
| feature/label alignment: warm train | `PASS` | feature_rows=26914, label_rows=26914, has_row_id=True, same_row_ids=True |
| feature/label alignment: warm validation | `PASS` | feature_rows=519, label_rows=519, has_row_id=True, same_row_ids=True |
| feature/label alignment: warm test | `PASS` | feature_rows=607, label_rows=607, has_row_id=True, same_row_ids=True |
| feature/label alignment: cold train | `PASS` | feature_rows=26914, label_rows=26914, has_row_id=True, same_row_ids=True |
| feature/label alignment: cold validation | `PASS` | feature_rows=2753, label_rows=2753, has_row_id=True, same_row_ids=True |
| feature/label alignment: cold test | `PASS` | feature_rows=3099, label_rows=3099, has_row_id=True, same_row_ids=True |
| cold forbidden feature columns: features/cold/track6_train_cold_features.csv | `PASS` | forbidden_columns=[] |
| cold forbidden feature columns: features/cold/track6_val_cold_cold_features.csv | `PASS` | forbidden_columns=[] |
| cold forbidden feature columns: features/cold/track6_test_cold_cold_features.csv | `PASS` | forbidden_columns=[] |
