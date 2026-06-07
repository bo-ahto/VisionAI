# IMG-P1 Cold CLIP 이미지 결합 파일럿

- 목적: Cold 가격 예측에서 작품 이미지 임베딩이 추가 신호를 갖는지 파일럿으로 확인한다.
- 기준: 기존 Track6 Cold split을 유지하되, 이미지 임베딩이 생성된 Saatchi/Artsy 샘플만 사용한다.
- 주의: 이번 결과는 600건 샘플 기반 파일럿이므로 최종 성능 결론이 아니라 전체 확장 여부 판단용이다.

## 실험 구성

- `sample_tabular_lgb`: 600건 샘플 중 train 200건만 사용한 정형 피처 기준.
- `image_pca*_ridge`: CLIP 이미지 임베딩만 사용한 기준.
- `sample_tabular_lgb_clip_pca*`: 정형 피처와 CLIP PCA 피처를 결합한 기준.
- `full_tabular_*_reference`: 기존 전체 Cold train으로 학습한 정형 모델을 같은 이미지 샘플 val/test에 평가한 참고 기준.

## 결과

| split | candidate | train_scope | n_eval | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | note |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| test | `full_tabular_catboost_reference` | full_cold_train | 200 | 0.4908 | 2.1338 | 5.0367 | 1.0427 | 0.2950 | 전체 Cold train으로 학습한 CatBoost 참고 기준 |
| test | `full_tabular_lgb_reference` | full_cold_train | 200 | 0.5204 | 1.7956 | 8.1969 | 1.0574 | 0.2750 | 전체 Cold train으로 학습한 LightGBM 참고 기준 |
| test | `sample_tabular_lgb_clip_pca32` | image_sample_train | 200 | 0.5682 | 1.4511 | 4.2944 | 1.1020 | 0.3050 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `sample_tabular_lgb_clip_pca16` | image_sample_train | 200 | 0.5693 | 1.4562 | 5.2939 | 1.1065 | 0.2600 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `sample_tabular_lgb` | image_sample_train | 200 | 0.6032 | 2.5680 | 14.0070 | 1.2876 | 0.2650 | 샘플 train만 사용한 정형 피처 기준 |
| test | `sample_tabular_lgb_clip_pca64` | image_sample_train | 200 | 0.6273 | 1.5508 | 4.6531 | 1.1457 | 0.2100 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `image_pca64_ridge` | image_sample_train | 200 | 0.7568 | 1.4124 | 5.2145 | 1.3189 | 0.1800 | CLIP 이미지만 사용한 Ridge 기준 |
| test | `image_pca16_ridge` | image_sample_train | 200 | 0.7703 | 1.3920 | 5.1311 | 1.3102 | 0.1500 | CLIP 이미지만 사용한 Ridge 기준 |
| test | `image_pca32_ridge` | image_sample_train | 200 | 0.7940 | 1.4253 | 5.1343 | 1.3023 | 0.1550 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `full_tabular_lgb_reference` | full_cold_train | 200 | 0.4109 | 0.8071 | 1.9277 | 0.7906 | 0.3550 | 전체 Cold train으로 학습한 LightGBM 참고 기준 |
| validation | `full_tabular_catboost_reference` | full_cold_train | 200 | 0.5013 | 0.7681 | 2.1680 | 0.8036 | 0.2850 | 전체 Cold train으로 학습한 CatBoost 참고 기준 |
| validation | `sample_tabular_lgb_clip_pca32` | image_sample_train | 200 | 0.5375 | 1.0038 | 4.5947 | 1.0010 | 0.2650 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb_clip_pca64` | image_sample_train | 200 | 0.5838 | 1.3407 | 6.1019 | 1.0587 | 0.2750 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb_clip_pca16` | image_sample_train | 200 | 0.5842 | 1.0879 | 4.9000 | 1.0104 | 0.2750 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb` | image_sample_train | 200 | 0.6736 | 1.4706 | 6.6115 | 1.1327 | 0.1600 | 샘플 train만 사용한 정형 피처 기준 |
| validation | `image_pca16_ridge` | image_sample_train | 200 | 0.6809 | 1.6791 | 7.7894 | 1.3069 | 0.2150 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `image_pca32_ridge` | image_sample_train | 200 | 0.6950 | 1.5885 | 7.1967 | 1.3003 | 0.2400 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `image_pca64_ridge` | image_sample_train | 200 | 0.7329 | 1.6516 | 6.7775 | 1.3554 | 0.2100 | CLIP 이미지만 사용한 Ridge 기준 |

## 해석 기준

- 이미지 단독 후보가 샘플 정형 후보보다 의미 있게 낮으면 이미지 자체에 가격 신호가 있다는 근거가 된다.
- 정형+이미지 후보가 샘플 정형 후보보다 낮으면 이미지 결합의 파일럿 개선 가능성이 있다.
- 전체 정형 참고 기준은 train 규모가 다르므로 샘플 후보와 직접 공정 비교하지 않고 운영 기준과의 거리만 본다.
- 다음 단계는 train 표본을 늘리고 같은 구조로 재검증하는 것이다.

## 현재 해석

- 이미지 단독 모델은 MdAPE 기준으로 정형 피처 기준보다 좋지 않았다.
- 즉, 이미지 정보만으로 가격을 직접 맞히기에는 현재 200건 train 샘플이 부족하다.
- 반면 `sample_tabular_lgb_clip_pca32`는 샘플 정형 기준보다 validation/test 모두 개선됐다.
- validation 기준 개선:
  - MdAPE: `0.6736 -> 0.5375`
  - MAPE: `1.4706 -> 1.0038`
  - p95_APE: `6.6115 -> 4.5947`
- test 기준 개선:
  - MdAPE: `0.6032 -> 0.5682`
  - MAPE: `2.5680 -> 1.4511`
  - p95_APE: `14.0070 -> 4.2944`
- 해석:
  - 이미지만 단독으로 쓰는 것보다, 기존 크기/재료/형태 피처에 이미지 임베딩을 보조 피처로 붙이는 방식이 더 적합하다.
  - CLIP PCA32는 작품의 색감, 구도, 시각적 스타일, 이미지 품질 같은 비정형 신호를 압축해 정형 피처의 빈틈을 보완한 것으로 볼 수 있다.
  - 특히 test에서 MAPE와 p95_APE가 크게 낮아졌기 때문에, 큰 오차를 줄이는 보정/보조 신호로 이미지가 유효할 가능성이 있다.
- 한계:
  - 전체 Cold train으로 학습한 기존 CatBoost 참고 기준보다 MdAPE는 아직 낮지 않다.
  - 이번 이미지 결합 후보는 train 200건만 사용했기 때문에, 전체 모델과 직접 비교해 최종 우열을 판단하면 안 된다.
  - 다음 단계는 train 샘플을 늘려 이미지 결합 효과가 유지되는지 확인하는 것이다.

## 설정

```json
{
  "experiment_id": "IMG-P1",
  "slug": "IMG-P1_cold_clip_multimodal_pilot",
  "created_at": "2026-06-04T03:28:39",
  "embedding_path": "data/track6/image_multimodal/track6_clip_cold_pilot_600_embeddings.npy",
  "index_path": "data/track6/image_multimodal/track6_clip_cold_pilot_600_index.csv",
  "sample_rows": {
    "train": 200,
    "validation": 200,
    "test": 200
  },
  "lgb_features": [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "size_bucket",
    "support_size_bucket"
  ],
  "catboost_features": [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "shape_bucket",
    "medium_shape_bucket"
  ],
  "seed": 20260602
}
```
