# IMG-P4 Cold CLIP 이미지 결합 파일럿

- 목적: Cold 가격 예측에서 작품 이미지 임베딩이 추가 신호를 갖는지 파일럿으로 확인한다.
- 기준: 기존 Track6 Cold split을 유지하되, 이미지 임베딩이 생성된 Saatchi/Artsy 전체 이미지 가능 표본을 사용한다.
- 샘플 규모: train `24367`건, validation `2535`건, test `2886`건.
- 주의: 이번 결과는 이미지가 있는 Cold 표본 기준 평가이므로, 이미지가 없는 행의 fallback 성능은 별도 확인이 필요하다.

## 임베딩 생성 결과

- 전체 대상: 29,970건.
- 성공: 29,788건.
- 실패: 182건.
- 성공률: 0.9939.
- 실패 분포:
  - train Saatchi 180건.
  - validation Saatchi 1건.
  - test Saatchi 1건.
- 실패 유형: 최종 재시도 후에도 HTTPError로 유지된 원본 이미지 URL 실패.
- 사용 모델: CLIP `ViT-B-32` / pretrained `openai`.
- 실행 장치: `mps`.
- 임베딩 shape: `(29788, 512)`.

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

## 이번 결과 해석

- 이미지 단독 Ridge는 validation/test 모두 정형 피처 기준보다 MdAPE가 높음.
- 따라서 이미지 임베딩만으로 가격 중심값을 직접 예측하는 방식은 Cold 기본 모델로 적합하지 않음.
- test에서는 `정형 + CLIP PCA32`가 샘플 정형 LightGBM 대비 MdAPE를 0.4726에서 0.4723으로 아주 소폭 낮춤.
- test에서는 `정형 + CLIP PCA32`가 MAPE를 1.3468에서 1.2371로 낮춤.
- test에서는 `정형 + CLIP PCA32`가 p95_APE를 4.5763에서 4.4606으로 낮춤.
- test 기준으로는 이미지 임베딩이 큰 오차 방어에 일부 도움을 줌.
- validation에서는 `정형 + CLIP PCA16/32/64`가 모두 샘플 정형 LightGBM보다 MdAPE, MAPE, p95_APE가 악화됨.
- validation 기준 최선은 전체 Cold train으로 학습한 LightGBM 참고 기준임.
- 따라서 IMG-P4 전체 확장 결과만 보면 CLIP 결합을 Cold 기본 모델로 바로 채택하기는 어려움.
- 다만 test의 MAPE/p95 개선은 반복적으로 관찰되므로, 이미지는 기본 예측값을 대체하기보다 고위험 구간 보정 또는 tail 방어용 보조 피처로 재설계할 가치가 있음.

## 판단

- 기본 Cold 가격 예측 모델 후보: 기존 정형 피처 중심 모델 유지.
- 이미지 임베딩 후보: 최종 기본 모델이 아니라 후처리/오차 방어/신뢰도 보조 후보로 유지.
- 다음 실험:
  - 이미지 결측 fallback 정책 확인.
  - 이미지 임베딩을 전 구간에 동일하게 넣는 방식 대신, 예측 불확실성이 큰 샘플이나 시각 차이가 큰 매체/크기 구간에만 선택 적용.
  - CLIP PCA를 직접 LightGBM에 붙이는 방식 외에 residual 보정 모델로 활용.

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
