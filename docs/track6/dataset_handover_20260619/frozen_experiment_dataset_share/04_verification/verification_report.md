# Frozen Track6 실험 데이터셋 검증 보고서

- 기준 모델 번들: `models/track6/price_prediction_v0.1/data/training/track6_split`
- 공유 폴더 복사본: `docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/03_frozen_training_dataset/track6_split`
- 비교 파일 수: `21`
- SHA256 mismatch: `0`

## Row count

| file | rows | columns | artist_key 수 | 한글 작가명 수 |
|---|---:|---:|---:|---:|
| `track6_train.csv` | `26914` | `50` | `1773` | `1713` |
| `track6_val_warm.csv` | `519` | `50` | `178` | `178` |
| `track6_test_warm.csv` | `607` | `50` | `207` | `205` |
| `track6_val_cold.csv` | `2753` | `50` | `172` | `168` |
| `track6_test_cold.csv` | `3099` | `50` | `200` | `189` |
| `features/warm/track6_train_warm_features.csv` | `26914` | `23` | `` | `` |
| `features/warm/track6_val_warm_warm_features.csv` | `519` | `23` | `` | `` |
| `features/warm/track6_test_warm_warm_features.csv` | `607` | `23` | `` | `` |
| `features/cold/track6_train_cold_features.csv` | `26914` | `20` | `` | `` |
| `features/cold/track6_val_cold_cold_features.csv` | `2753` | `20` | `` | `` |
| `features/cold/track6_test_cold_cold_features.csv` | `3099` | `20` | `` | `` |
| `labels/track6_train_labels.csv` | `26914` | `12` | `` | `` |
| `labels/track6_val_warm_labels.csv` | `519` | `12` | `` | `` |
| `labels/track6_test_warm_labels.csv` | `607` | `12` | `` | `` |
| `labels/track6_val_cold_labels.csv` | `2753` | `12` | `` | `` |
| `labels/track6_test_cold_labels.csv` | `3099` | `12` | `` | `` |
