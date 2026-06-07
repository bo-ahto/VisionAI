# IMG-P3 Cold CLIP 이미지 결합 파일럿

- 목적: Cold 가격 예측에서 작품 이미지 임베딩이 추가 신호를 갖는지 파일럿으로 확인한다.
- 기준: 기존 Track6 Cold split을 유지하되, 이미지 임베딩이 생성된 Saatchi/Artsy 샘플만 사용한다.
- 샘플 규모: train `1988`건, validation `400`건, test `400`건.
- 주의: 이번 결과는 샘플 기반 파일럿이므로 최종 성능 결론이 아니라 전체 확장 여부 판단용이다.

## 임베딩 생성 결과

- 전체 목표: 2,800건.
- 성공: 2,788건.
- 실패: 12건.
- 실패 위치: train Saatchi 12건.
- 실패 사유: 이미지 URL 404.
- validation/test는 Saatchi 200건, Artsy 200건씩 모두 성공.
- 따라서 이번 validation/test 평가는 이미지 다운로드 실패로 인한 표본 누락 없이 진행됨.

## 실험 구성

- `sample_tabular_lgb`: 이미지 임베딩이 있는 train `1988`건만 사용한 정형 피처 기준.
- `image_pca*_ridge`: CLIP 이미지 임베딩만 사용한 기준.
- `sample_tabular_lgb_clip_pca*`: 정형 피처와 CLIP PCA 피처를 결합한 기준.
- `full_tabular_*_reference`: 기존 전체 Cold train으로 학습한 정형 모델을 같은 이미지 샘플 val/test에 평가한 참고 기준.

## 결과

| split | candidate | train_scope | n_eval | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | note |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| test | `full_tabular_catboost_reference` | full_cold_train | 400 | 0.4841 | 1.6856 | 4.8887 | 0.9673 | 0.2975 | 전체 Cold train으로 학습한 CatBoost 참고 기준 |
| test | `sample_tabular_lgb_clip_pca32` | image_sample_train | 400 | 0.4884 | 1.1941 | 3.7407 | 0.9200 | 0.3100 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `sample_tabular_lgb` | image_sample_train | 400 | 0.5031 | 1.5804 | 6.3018 | 1.0056 | 0.3000 | 샘플 train만 사용한 정형 피처 기준 |
| test | `sample_tabular_lgb_clip_pca64` | image_sample_train | 400 | 0.5095 | 1.1954 | 3.7983 | 0.9354 | 0.2875 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `sample_tabular_lgb_clip_pca16` | image_sample_train | 400 | 0.5100 | 1.1849 | 4.1869 | 0.9149 | 0.3100 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `full_tabular_lgb_reference` | full_cold_train | 400 | 0.5150 | 1.5467 | 5.0220 | 0.9901 | 0.2500 | 전체 Cold train으로 학습한 LightGBM 참고 기준 |
| test | `image_pca64_ridge` | image_sample_train | 400 | 0.7341 | 1.4889 | 6.1865 | 1.2518 | 0.1775 | CLIP 이미지만 사용한 Ridge 기준 |
| test | `image_pca16_ridge` | image_sample_train | 400 | 0.7529 | 1.4042 | 5.7701 | 1.2548 | 0.1950 | CLIP 이미지만 사용한 Ridge 기준 |
| test | `image_pca32_ridge` | image_sample_train | 400 | 0.7663 | 1.3827 | 5.8017 | 1.2345 | 0.1875 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `full_tabular_lgb_reference` | full_cold_train | 400 | 0.4166 | 0.7567 | 1.9918 | 0.7606 | 0.3325 | 전체 Cold train으로 학습한 LightGBM 참고 기준 |
| validation | `sample_tabular_lgb` | image_sample_train | 400 | 0.4579 | 0.8243 | 2.6638 | 0.8185 | 0.3050 | 샘플 train만 사용한 정형 피처 기준 |
| validation | `full_tabular_catboost_reference` | full_cold_train | 400 | 0.4844 | 0.7613 | 2.2053 | 0.7757 | 0.2775 | 전체 Cold train으로 학습한 CatBoost 참고 기준 |
| validation | `sample_tabular_lgb_clip_pca32` | image_sample_train | 400 | 0.5018 | 0.9582 | 3.6688 | 0.8600 | 0.2675 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb_clip_pca16` | image_sample_train | 400 | 0.5059 | 0.9189 | 3.5725 | 0.8435 | 0.2750 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb_clip_pca64` | image_sample_train | 400 | 0.5214 | 0.8519 | 2.8125 | 0.8254 | 0.2850 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `image_pca32_ridge` | image_sample_train | 400 | 0.6931 | 1.8518 | 8.1017 | 1.2422 | 0.2375 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `image_pca16_ridge` | image_sample_train | 400 | 0.6936 | 1.8420 | 7.5296 | 1.2388 | 0.1975 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `image_pca64_ridge` | image_sample_train | 400 | 0.7093 | 1.9226 | 7.9884 | 1.2563 | 0.1775 | CLIP 이미지만 사용한 Ridge 기준 |

## 해석 기준

- 이미지 단독 후보가 샘플 정형 후보보다 의미 있게 낮으면 이미지 자체에 가격 신호가 있다는 근거가 된다.
- 정형+이미지 후보가 샘플 정형 후보보다 낮으면 이미지 결합의 파일럿 개선 가능성이 있다.
- 전체 정형 참고 기준은 train 규모가 다르므로 샘플 후보와 직접 공정 비교하지 않고 운영 기준과의 거리만 본다.
- 다음 단계는 train 표본을 늘리고 같은 구조로 재검증하는 것이다.

## 이번 결과 해석

- 이미지 단독 Ridge는 validation/test 모두 샘플 정형 LightGBM보다 MdAPE가 높음.
- 따라서 이미지만으로 가격을 직접 맞히는 구조는 현재 우선순위가 낮음.
- test에서는 정형+CLIP PCA32가 샘플 정형 LightGBM 대비 MdAPE를 0.5031에서 0.4884로 낮춤.
- test에서는 정형+CLIP PCA32가 MAPE를 1.5804에서 1.1941로 낮춤.
- test에서는 정형+CLIP PCA32가 p95_APE를 6.3018에서 3.7407로 낮춤.
- 이는 이미지 임베딩이 큰 오차를 줄이는 보조 신호로 작동할 가능성을 보여줌.
- validation에서는 정형+CLIP PCA16/32/64 모두 샘플 정형 LightGBM보다 MdAPE가 높음.
- 따라서 이번 결과만으로 이미지 결합 후보를 최종 채택하면 test 샘플에 맞춘 선택이 될 위험이 있음.
- 다음 단계는 PCA16/PCA32를 중심으로 후보를 고정하고, 더 큰 Cold 이미지 가능 표본에서 validation 기준으로 다시 확인하는 것임.

## 설정

```json
{
  "experiment_id": "IMG-P3",
  "slug": "IMG-P3_cold_clip_train2000_multimodal_pilot",
  "created_at": "2026-06-04T04:10:54",
  "embedding_path": "data/track6/image_multimodal/track6_clip_cold_train2000_valtest800_embeddings.npy",
  "index_path": "data/track6/image_multimodal/track6_clip_cold_train2000_valtest800_index.csv",
  "sample_rows": {
    "train": 1988,
    "validation": 400,
    "test": 400
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
