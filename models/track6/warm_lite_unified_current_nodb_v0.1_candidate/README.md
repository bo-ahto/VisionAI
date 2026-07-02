# Warm-lite unified current no-DB candidate

이 번들은 official 0.1v Warm-lite unified current 모델을 DB 없이 실행하기 위한 후보 번들이다.

## 포함된 것

- 기존 Warm-lite unified LightGBM 모델 파일
- 기존 params JSON
- `artifacts/artist_registry.csv`
- `artifacts/artist_aliases.csv`
- `artifacts/artist_train_history.csv`

## 포함하지 않는 것

- `fixed_replay_feature_store.csv`
- SQLite DB
- validation/test 가격 이력

## frozen table summary

```json
{
  "artist_registry_rows": 1773,
  "artist_alias_rows": 3600,
  "train_history_rows": 26914,
  "train_history_unique_track6_row_ids": 26914,
  "train_history_duplicate_track6_row_ids_before_remap": 1,
  "train_history_duplicate_track6_row_ids_after_remap": 0,
  "track6_row_id_source": "models/track6/price_prediction_v0.1/data/training/track6_split/track6_train.csv",
  "train_history_artists": 1773,
  "train_only": true
}
```

## 운영 해석

새 작품 예측 시 작가명 또는 artist_key를 입력하면, 이 번들 내부의 alias/registry CSV로
artist_key를 찾고, `artist_train_history.csv`에서 같은 작가 train 이력만 조회한다.
그 결과를 기존 Warm-lite unified current 모델에 넣어 예측한다.
