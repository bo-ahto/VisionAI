# IMG-P2 Cold CLIP 이미지 결합 파일럿

- 목적: Cold 가격 예측에서 작품 이미지 임베딩이 추가 신호를 갖는지 파일럿으로 확인한다.
- 기준: 기존 Track6 Cold split을 유지하되, 이미지 임베딩이 생성된 Saatchi/Artsy 샘플만 사용한다.
- 샘플 규모: train `992`건, validation `200`건, test `200`건.
- 주의: 이번 결과는 샘플 기반 파일럿이므로 최종 성능 결론이 아니라 전체 확장 여부 판단용이다.

## 실험 구성

- `sample_tabular_lgb`: 이미지 임베딩이 있는 train `992`건만 사용한 정형 피처 기준.
- `image_pca*_ridge`: CLIP 이미지 임베딩만 사용한 기준.
- `sample_tabular_lgb_clip_pca*`: 정형 피처와 CLIP PCA 피처를 결합한 기준.
- `full_tabular_*_reference`: 기존 전체 Cold train으로 학습한 정형 모델을 같은 이미지 샘플 val/test에 평가한 참고 기준.

## 결과

| split | candidate | train_scope | n_eval | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | note |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| test | `sample_tabular_lgb_clip_pca32` | image_sample_train | 200 | 0.4894 | 1.2190 | 3.4606 | 0.9719 | 0.2700 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `full_tabular_catboost_reference` | full_cold_train | 200 | 0.4908 | 2.1338 | 5.0367 | 1.0427 | 0.2950 | 전체 Cold train으로 학습한 CatBoost 참고 기준 |
| test | `sample_tabular_lgb_clip_pca16` | image_sample_train | 200 | 0.4980 | 1.2153 | 3.9720 | 0.9629 | 0.2650 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `full_tabular_lgb_reference` | full_cold_train | 200 | 0.5204 | 1.7956 | 8.1969 | 1.0574 | 0.2750 | 전체 Cold train으로 학습한 LightGBM 참고 기준 |
| test | `sample_tabular_lgb` | image_sample_train | 200 | 0.5343 | 1.6339 | 8.7697 | 1.0669 | 0.2700 | 샘플 train만 사용한 정형 피처 기준 |
| test | `sample_tabular_lgb_clip_pca64` | image_sample_train | 200 | 0.5557 | 1.2725 | 4.2590 | 0.9826 | 0.3100 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| test | `image_pca64_ridge` | image_sample_train | 200 | 0.7306 | 1.5134 | 7.2971 | 1.2710 | 0.1900 | CLIP 이미지만 사용한 Ridge 기준 |
| test | `image_pca32_ridge` | image_sample_train | 200 | 0.7854 | 1.3654 | 5.7274 | 1.2342 | 0.1600 | CLIP 이미지만 사용한 Ridge 기준 |
| test | `image_pca16_ridge` | image_sample_train | 200 | 0.7908 | 1.3305 | 5.4955 | 1.2641 | 0.1800 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `full_tabular_lgb_reference` | full_cold_train | 200 | 0.4109 | 0.8071 | 1.9277 | 0.7906 | 0.3550 | 전체 Cold train으로 학습한 LightGBM 참고 기준 |
| validation | `full_tabular_catboost_reference` | full_cold_train | 200 | 0.5013 | 0.7681 | 2.1680 | 0.8036 | 0.2850 | 전체 Cold train으로 학습한 CatBoost 참고 기준 |
| validation | `sample_tabular_lgb_clip_pca16` | image_sample_train | 200 | 0.5122 | 0.7842 | 2.0644 | 0.8205 | 0.2900 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb_clip_pca64` | image_sample_train | 200 | 0.5231 | 0.7992 | 2.4728 | 0.8501 | 0.2500 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb_clip_pca32` | image_sample_train | 200 | 0.5473 | 0.8645 | 2.7690 | 0.8612 | 0.2400 | 샘플 train에서 정형 피처와 CLIP PCA 결합 |
| validation | `sample_tabular_lgb` | image_sample_train | 200 | 0.5630 | 0.8800 | 2.1251 | 0.8600 | 0.2650 | 샘플 train만 사용한 정형 피처 기준 |
| validation | `image_pca32_ridge` | image_sample_train | 200 | 0.6877 | 1.7299 | 7.4706 | 1.2909 | 0.2250 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `image_pca16_ridge` | image_sample_train | 200 | 0.7067 | 1.6771 | 7.7427 | 1.2789 | 0.1850 | CLIP 이미지만 사용한 Ridge 기준 |
| validation | `image_pca64_ridge` | image_sample_train | 200 | 0.7233 | 1.6199 | 7.0476 | 1.2868 | 0.2100 | CLIP 이미지만 사용한 Ridge 기준 |

## 해석 기준

- 이미지 단독 후보가 샘플 정형 후보보다 의미 있게 낮으면 이미지 자체에 가격 신호가 있다는 근거가 된다.
- 정형+이미지 후보가 샘플 정형 후보보다 낮으면 이미지 결합의 파일럿 개선 가능성이 있다.
- 전체 정형 참고 기준은 train 규모가 다르므로 샘플 후보와 직접 공정 비교하지 않고 운영 기준과의 거리만 본다.
- 다음 단계는 train 표본을 늘리고 같은 구조로 재검증하는 것이다.

## 현재 해석

- train 샘플을 200건에서 992건으로 늘리자 정형+이미지 결합 후보가 더 안정화됐다.
- 이미지 단독 모델은 여전히 MdAPE 기준으로 정형 피처 기준보다 좋지 않았다.
- 즉, 이미지 임베딩은 단독 예측 모델보다는 정형 피처의 보조 신호로 쓰는 방식이 더 적합하다.
- `sample_tabular_lgb_clip_pca16`:
  - validation MdAPE: `0.5630 -> 0.5122`
  - validation MAPE: `0.8800 -> 0.7842`
  - validation p95_APE: `2.1251 -> 2.0644`
  - test MdAPE: `0.5343 -> 0.4980`
  - test MAPE: `1.6339 -> 1.2153`
  - test p95_APE: `8.7697 -> 3.9720`
- `sample_tabular_lgb_clip_pca32`:
  - validation MdAPE: `0.5630 -> 0.5473`
  - validation MAPE: `0.8800 -> 0.8645`
  - validation p95_APE: `2.1251 -> 2.7690`
  - test MdAPE: `0.5343 -> 0.4894`
  - test MAPE: `1.6339 -> 1.2190`
  - test p95_APE: `8.7697 -> 3.4606`
- 해석:
  - PCA16은 validation에서 가장 안정적이다.
  - PCA32는 test에서 MdAPE와 p95_APE가 가장 좋다.
  - PCA64는 test p95_APE는 개선되지만 MdAPE가 악화되어 현재 후보로는 약하다.
  - 현재 기준으로는 PCA16/PCA32를 다음 확장 후보로 유지하고 PCA64는 보조 비교군으로 낮추는 것이 적절하다.
- 운영 기준과의 비교:
  - test에서 PCA32 결합 후보 MdAPE는 `0.4894`로 전체 Cold CatBoost 참고 기준 `0.4908`과 거의 같다.
  - test에서 PCA32 결합 후보 MAPE는 `1.2190`으로 전체 Cold CatBoost 참고 기준 `2.1338`보다 낮다.
  - test에서 PCA32 결합 후보 p95_APE는 `3.4606`으로 전체 Cold CatBoost 참고 기준 `5.0367`보다 낮다.
  - 단, validation에서는 전체 Cold LightGBM 참고 기준이 가장 좋기 때문에 이 결과만으로 최종 교체를 결정하면 안 된다.
- 다음 단계:
  - 전체 Cold 이미지 가능 행으로 확장하기 전에, 중복 다운로드를 피하는 캐시/이어하기 구조를 추가한다.
  - train 표본을 더 늘린 IMG-P3 또는 전체 Saatchi/Artsy 이미지 임베딩 실험으로 재검증한다.
  - 최종 판단은 동일 validation/test 전체 또는 이미지 가능 전체 샘플에서 paired 비교로 진행한다.

## 설정

```json
{
  "experiment_id": "IMG-P2",
  "slug": "IMG-P2_cold_clip_train1000_multimodal_pilot",
  "created_at": "2026-06-04T03:43:29",
  "embedding_path": "data/track6/image_multimodal/track6_clip_cold_train1000_valtest400_embeddings.npy",
  "index_path": "data/track6/image_multimodal/track6_clip_cold_train1000_valtest400_index.csv",
  "sample_rows": {
    "train": 992,
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
