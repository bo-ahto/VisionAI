# IMG-P4 Cold CLIP 이미지 결합 파일럿

- 목적: Cold 가격 예측에서 작품 이미지 임베딩이 추가 신호를 갖는지 파일럿으로 확인한다.
- 기준: 기존 Track6 Cold split을 유지하되, 이미지 임베딩이 생성된 Saatchi/Artsy 샘플만 사용한다.
- 샘플 규모: train `24367`건, validation `2535`건, test `2886`건.
- 주의: 이번 결과는 샘플 기반 파일럿이므로 최종 성능 결론이 아니라 전체 확장 여부 판단용이다.

## 실험 구성

- `sample_tabular_lgb`: 이미지 임베딩이 있는 train `24367`건만 사용한 정형 피처 기준.
- `image_pca*_ridge`: CLIP 이미지 임베딩만 사용한 기준.
- `sample_tabular_lgb_clip_pca*`: 정형 피처와 CLIP PCA 피처를 결합한 기준.
- `full_tabular_*_reference`: 기존 전체 Cold train으로 학습한 정형 모델을 같은 이미지 샘플 val/test에 평가한 참고 기준.

## 결과

| split | candidate | train_scope | n_eval | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | note |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| test | `sample_tabular_lgb_clip_pca32` | image_sample_train | 2886 | 0.4723 | 1.2371 | 4.4606 | 0.9147 | 0.3042 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `sample_tabular_lgb` | image_sample_train | 2886 | 0.4726 | 1.3468 | 4.5763 | 0.9278 | 0.2935 | 샘플 train만 사용한 정형 피처 기준 |
| test | `sample_tabular_lgb_clip_pca16` | image_sample_train | 2886 | 0.4787 | 1.2711 | 4.4706 | 0.9236 | 0.3004 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `full_tabular_catboost_reference` | full_cold_train | 2886 | 0.4833 | 1.5021 | 4.8250 | 0.9526 | 0.2907 | 전체 Cold train으로 학습한 CatBoost 참고 기준 |
| test | `sample_tabular_lgb_clip_pca64` | image_sample_train | 2886 | 0.4841 | 1.2757 | 4.2776 | 0.9234 | 0.3108 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `full_tabular_lgb_reference` | full_cold_train | 2886 | 0.4846 | 1.4490 | 5.8846 | 0.9609 | 0.3056 | 전체 Cold train으로 학습한 LightGBM 참고 기준 |
| test | `image_pca32_ridge` | image_sample_train | 2886 | 0.7074 | 1.4979 | 6.5291 | 1.2263 | 0.2003 | CLIP 이미지만 사용한 Ridge 기준 |
| test | `image_pca16_ridge` | image_sample_train | 2886 | 0.7155 | 1.5042 | 6.1732 | 1.2404 | 0.2024 | CLIP 이미지만 사용한 Ridge 기준 |
| test | `image_pca64_ridge` | image_sample_train | 2886 | 0.7167 | 1.6392 | 7.5227 | 1.2345 | 0.1972 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `full_tabular_lgb_reference` | full_cold_train | 2535 | 0.3754 | 0.7019 | 1.9574 | 0.6738 | 0.3941 | 전체 Cold train으로 학습한 LightGBM 참고 기준 |
| validation | `sample_tabular_lgb` | image_sample_train | 2535 | 0.4076 | 0.6961 | 2.2053 | 0.6728 | 0.3937 | 샘플 train만 사용한 정형 피처 기준 |
| validation | `full_tabular_catboost_reference` | full_cold_train | 2535 | 0.4114 | 0.7189 | 2.2053 | 0.6885 | 0.3696 | 전체 Cold train으로 학습한 CatBoost 참고 기준 |
| validation | `sample_tabular_lgb_clip_pca64` | image_sample_train | 2535 | 0.4403 | 0.7260 | 2.3487 | 0.6925 | 0.3590 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb_clip_pca32` | image_sample_train | 2535 | 0.4427 | 0.8172 | 3.0099 | 0.7382 | 0.3456 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb_clip_pca16` | image_sample_train | 2535 | 0.4455 | 0.8045 | 2.9688 | 0.7325 | 0.3515 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `image_pca64_ridge` | image_sample_train | 2535 | 0.7223 | 1.9324 | 8.4511 | 1.1965 | 0.1925 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `image_pca32_ridge` | image_sample_train | 2535 | 0.7288 | 2.0247 | 8.3795 | 1.2293 | 0.1890 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `image_pca16_ridge` | image_sample_train | 2535 | 0.7381 | 2.0042 | 8.0462 | 1.2217 | 0.1870 | CLIP 이미지만 사용한 Ridge 기준 |

## 해석 기준

- 이미지 단독 후보가 샘플 정형 후보보다 의미 있게 낮으면 이미지 자체에 가격 신호가 있다는 근거가 된다.
- 정형+이미지 후보가 샘플 정형 후보보다 낮으면 이미지 결합의 파일럿 개선 가능성이 있다.
- 전체 정형 참고 기준은 train 규모가 다르므로 샘플 후보와 직접 공정 비교하지 않고 운영 기준과의 거리만 본다.
- 다음 단계는 train 표본을 늘리고 같은 구조로 재검증하는 것이다.

## 설정

```json
{
  "experiment_id": "IMG-P4",
  "slug": "IMG-P4_cold_clip_full_saatchi_artsy_multimodal",
  "created_at": "2026-06-04T10:02:34",
  "embedding_path": "data/track6/image_multimodal/track6_clip_cold_full_saatchi_artsy_embeddings.npy",
  "index_path": "data/track6/image_multimodal/track6_clip_cold_full_saatchi_artsy_index.csv",
  "sample_rows": {
    "train": 24367,
    "validation": 2535,
    "test": 2886
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
