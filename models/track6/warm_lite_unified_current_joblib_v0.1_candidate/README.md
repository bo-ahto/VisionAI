# Warm-lite unified current joblib-only candidate

이 번들은 Warm-lite unified current 모델을 CSV/DB 없이 실행하기 위한 후보 번들이다.

## Runtime input files

- `artifacts/runtime_store.joblib`
- `predict/predict_warm_lite_unified_current_joblib_v0_1.py`

## Store contents

```json
{
  "store": "models/track6/warm_lite_unified_current_joblib_v0.1_candidate/artifacts/runtime_store.joblib",
  "store_bytes": 6376592,
  "artist_registry_rows": 1773,
  "artist_alias_rows": 3600,
  "train_history_rows": 26914,
  "train_history_artists": 1773,
  "seed_count": 3,
  "feature_generation_embedded": true
}
```

## Runtime contract

- SQLite DB를 읽지 않는다.
- CSV lookup/history 파일을 읽지 않는다.
- `fixed_replay_feature_store.csv`를 포함하지도, 읽지도 않는다.
- repo feature helper를 import하지 않는다.
- 같은 작가 train 이력은 `runtime_store.joblib` 안의 DataFrame에서 조회한다.
- size/shape bucket 생성 기준도 `runtime_store.joblib` 안에 동결되어 있다.
