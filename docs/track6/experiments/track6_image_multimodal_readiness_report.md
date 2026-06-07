# Track6 이미지 멀티모달 실험 준비 상태 점검

- 생성 시각: 2026-06-04 03:05:24
- 목적: Deep Learning for Art Market Valuation 논문 방식처럼 이미지 정보와 정형 피처를 결합하는 실험이 가능한지 확인한다.
- 결론: 이미지 URL 커버리지는 충분하나, 기존 이미지 임베딩은 Track6 row와 직접 매칭되는 키가 없어 바로 사용하지 않는다.

## 1. Split별 이미지 URL 커버리지

| split | rows | image_url_rows | missing_image_url_rows | image_url_rate | unique_image_urls |
| --- | --- | --- | --- | --- | --- |
| train | 26914 | 24547 | 2367 | 0.9121 | 24547 |
| val_cold | 2753 | 2536 | 217 | 0.9212 | 2536 |
| test_cold | 3099 | 2887 | 212 | 0.9316 | 2887 |
| val_warm | 519 | 448 | 71 | 0.8632 | 448 |
| test_warm | 607 | 528 | 79 | 0.8699 | 528 |

## 2. 출처별 이미지 URL 커버리지

| split | source | rows | image_url_rows | missing_image_url_rows | image_url_rate |
| --- | --- | --- | --- | --- | --- |
| train | saatchi | 16285 | 16285 | 0 | 1.0 |
| train | artsy | 8276 | 8262 | 14 | 0.9983 |
| train | artue | 2151 | 0 | 2151 | 0.0 |
| train | gallery_primary | 202 | 0 | 202 | 0.0 |
| val_cold | saatchi | 1902 | 1902 | 0 | 1.0 |
| val_cold | artsy | 634 | 634 | 0 | 1.0 |
| val_cold | artue | 210 | 0 | 210 | 0.0 |
| val_cold | gallery_primary | 7 | 0 | 7 | 0.0 |
| test_cold | saatchi | 1702 | 1702 | 0 | 1.0 |
| test_cold | artsy | 1185 | 1185 | 0 | 1.0 |
| test_cold | artue | 158 | 0 | 158 | 0.0 |
| test_cold | gallery_primary | 54 | 0 | 54 | 0.0 |
| val_warm | gallery_primary | 17 | 0 | 17 | 0.0 |
| val_warm | saatchi | 218 | 218 | 0 | 1.0 |
| val_warm | artue | 53 | 0 | 53 | 0.0 |
| val_warm | artsy | 231 | 230 | 1 | 0.9957 |
| test_warm | saatchi | 276 | 276 | 0 | 1.0 |
| test_warm | artsy | 252 | 252 | 0 | 1.0 |
| test_warm | artue | 73 | 0 | 73 | 0.0 |
| test_warm | gallery_primary | 6 | 0 | 6 | 0.0 |

## 3. 전체 요약

- 전체 행 수: 33892
- 이미지 URL 보유 행 수: 30946
- 이미지 URL 보유율: 0.9131
- 고유 이미지 URL 수: 30946
- 중복 이미지 URL 수: 0

## 4. 기존 이미지 임베딩 재사용 가능성

- 기존 `data/clip_embeddings.npy`와 `data/image_embeddings_raw.npy`는 존재한다.
- 기존 인덱스 파일의 키는 `idx`이다.
- Track6 split의 기준 키는 `_track6_row_id`, `image_url`, `artwork_url`이다.
- 따라서 숫자 값이 일부 겹치더라도 같은 작품이라고 해석하면 안 된다.
- 현재 기준으로는 Track6 전용 이미지 임베딩을 새로 생성하는 것이 안전하다.

```json
{
  "clip": {
    "index_path": "data/clip_embeddings_index.csv",
    "embedding_path": "data/clip_embeddings.npy",
    "index_exists": true,
    "embedding_exists": true,
    "index_rows": 54815,
    "index_columns": [
      "idx"
    ],
    "has_direct_track6_key": false,
    "numeric_id_overlap_count": 33701,
    "numeric_id_overlap_note": "Numeric overlap is not a valid match because the index column is named idx, not _track6_row_id or image_url.",
    "embedding_shape": [
      54815,
      512
    ],
    "embedding_dtype": "float32",
    "embedding_size_mb": 107.06
  },
  "image": {
    "index_path": "data/image_embeddings_index.csv",
    "embedding_path": "data/image_embeddings_raw.npy",
    "index_exists": true,
    "embedding_exists": true,
    "index_rows": 54815,
    "index_columns": [
      "idx"
    ],
    "has_direct_track6_key": false,
    "numeric_id_overlap_count": 33701,
    "numeric_id_overlap_note": "Numeric overlap is not a valid match because the index column is named idx, not _track6_row_id or image_url.",
    "embedding_shape": [
      54815,
      2048
    ],
    "embedding_dtype": "float32",
    "embedding_size_mb": 428.24
  }
}
```

## 5. 다음 실행 기준

- 1단계: 이 매니페스트를 기준으로 이미지 URL 샘플 다운로드 성공률을 확인한다.
- 2단계: 다운로드 가능성이 확인되면 Track6 전용 CLIP 임베딩을 `_track6_row_id` 기준으로 생성한다.
- 3단계: Cold부터 이미지 단독, 정형 피처 단독, 정형 피처 + 이미지 결합을 비교한다.
- 4단계: Cold에서 개선이 확인되면 Warm에도 같은 구조를 확장한다.
