# PP-L10 Warm PP-L8 순차 구조 피처 변형 실험 요약

- 작성일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_l10_warm_l8_feature_variant_experiments.py`
- 요약 지표: `experiments/track6/PP-L10_warm_l8_feature_variant_summary_metrics.csv`
- 실험 폴더: `experiments/track6/PP-L10_warm_l8_feature_variant_sequential`

## 1. 목적

- 기존 `PP-L8`에서 사용한 `Quantile -> Huber -> CatBoost residual` 구조를 유지한다.
- 모델 순서는 바꾸지 않고 Warm 피처셋만 바꿔 성능 차이를 확인한다.
- 질문의 핵심인 “해당 구조를 피처를 바꿔서도 해봤는가?”에 대해 실행 결과로 답한다.

## 2. 고정한 모델 구조

```text
1단계: CatBoost Quantile
  q10_log, q50_log, q90_log 예측
  quantile_width = q90_log - q10_log
  price_range_ratio = exp(quantile_width)

2단계: Huber 중심 가격선
  기존 피처 + q10/q50/q90/quantile_width/price_range_ratio 입력
  huber_pred_log 생성

3단계: CatBoost residual 보정
  residual_log = actual_log - oof_huber_pred_log
  CatBoost가 residual_log 학습
  final_pred_log = huber_pred_log + catboost_residual_pred
```

## 3. 바꿔본 피처셋

| 피처셋 | 피처 수 | 의도 |
|---|---:|---|
| `base_existing_combo` | 13 | 기존 PP-L8 기준 구조 재확인 |
| `artist_size_only` | 5 | Warm 핵심축인 작가+크기만 남겨 노이즈 제거 여부 확인 |
| `artist_size_works` | 7 | 작가 학습량을 추가해 작가 기준선 안정화 여부 확인 |
| `full_plus_generated_buckets` | 21 | PP-U1에서 개선 신호가 있던 생성 bucket 추가 |
| `warm_base_search_all` | 60 | PP-Z1에서 Huber baseline 개선 신호가 있던 검색 피처 추가 |
| `warm_base_artist_meta_all` | 35 | 작가 메타 전체 추가 |
| `warm_base_meta_external_search_all` | 90 | 작가 메타 + 전시/갤러리 + 검색 전체 추가 |

## 4. 주요 결과

### 4.1 PP-L10 내부 test MdAPE 상위

| 후보 | Test MdAPE | Test MAPE | Test p95_APE | 해석 |
|---|---:|---:|---:|---|
| `l8_seq__warm_base_meta_external_search_all` | 0.1708 | 0.3363 | 1.1432 | MdAPE 최상. 외부 피처 전체가 중심 오차를 조금 낮춤 |
| `l8_seq__base_existing_combo` | 0.1742 | 0.3386 | 1.0888 | 기존 PP-L8 구조 재현 후보 |
| `l8_seq__full_plus_generated_buckets` | 0.1743 | 0.3265 | 0.9818 | MAPE와 p95 균형이 가장 좋음 |
| `l8_seq__warm_base_search_all` | 0.1777 | 0.3399 | 1.0822 | 검색 피처는 validation은 좋았으나 test 개선은 제한적 |
| `l8_seq__warm_base_artist_meta_all` | 0.1825 | 0.3430 | 1.0557 | 작가 메타만으로는 중심 오차 개선 부족 |

### 4.2 기존 Warm 최종 후보와 비교

| 후보 | Test MdAPE | Test MAPE | Test p95_APE | 판단 |
|---|---:|---:|---:|---|
| `PP-V1 / PP-T1 fine_blend_mape_guarded` | 0.1621 | 0.3044 | 1.0335 | Warm 대표 후보 유지 |
| `PP-V2 huber_component_range_clipped` | 0.1680 | 0.2873 | 0.9287 | Warm MAPE/p95 방어 후보 유지 |
| `PP-L10 l8_seq__warm_base_meta_external_search_all` | 0.1708 | 0.3363 | 1.1432 | MdAPE는 PP-L8 변형 중 최고이나 최종 후보보다 약함 |
| `PP-L10 l8_seq__full_plus_generated_buckets` | 0.1743 | 0.3265 | 0.9818 | p95는 양호하나 MdAPE/MAPE 최종 후보보다 약함 |
| Warm Huber baseline | 0.2274 | 0.4952 | 2.0130 | 후처리 전 기준선 |

## 5. 해석

- 같은 순차 구조에서 피처를 바꾸면 성능 차이가 분명히 발생했다.
- `base_existing_combo`보다 외부 피처 전체를 넣은 후보가 MdAPE를 `0.1742 -> 0.1708`로 낮췄다.
- 생성 bucket을 넣은 후보는 MdAPE 최고는 아니지만 MAPE `0.3265`, p95 `0.9818`로 균형이 가장 좋았다.
- 단순 Huber direct 후보들은 모두 MdAPE `0.21~0.23` 수준이므로, 개선의 핵심은 피처 하나가 아니라 `Quantile -> Huber -> CatBoost residual` 순차 구조 자체다.
- Quantile q50 단독은 MdAPE `0.35~0.37`대로 약했다. Quantile은 단독 예측보다 Huber/CatBoost에 불확실성 피처를 제공하는 보조 역할이 더 적합하다.

## 6. 결론

- “PP-L8 구조를 피처를 바꿔서도 해봤는가?”에 대해서는 이번 `PP-L10`으로 실행 완료했다.
- 피처 변형 후보 중 최고는 `warm_base_meta_external_search_all`의 MdAPE `0.1708`이다.
- MAPE/p95 균형은 `full_plus_generated_buckets`가 가장 낫다.
- 다만 둘 다 기존 Warm 최종 후보 `PP-V1/PP-V2`를 넘지 못했으므로 대표 모델 교체는 보류한다.
- 후속으로는 `PP-L10`을 단독 운영 후보로 쓰기보다, `PP-V1/PP-V2` 조합 후보에 `l8_seq__full_plus_generated_buckets` 또는 `l8_seq__warm_base_meta_external_search_all`을 component로 추가했을 때 가중치가 실제로 선택되는지 확인하는 방향이 적절하다.
