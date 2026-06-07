# PP-U Warm/Cold 피처 교환 재학습 실행 요약

- 실행일: 2026-06-02
- 실행 스크립트: `scripts/track6/run_pp_u_experiments.py`
- 결과 요약 파일: `experiments/track6/PP-U_summary_metrics.csv`
- 목적: 기존 피처 영향도 실험 결과를 바탕으로 피처셋을 축소, 확장, 교환했을 때 Warm/Cold 모델 성능이 바뀌는지 확인한다.

## 실험 원칙

- 데이터 분할은 기존 Track6 고정 split을 그대로 사용한다.
- target은 `ln_price_krw`로 고정한다.
- 모델 설정은 고정하고 피처셋만 변경한다.
- 후보 선택은 validation 기준으로 판단하고, test는 재현성 확인으로만 사용한다.
- validation과 test의 1위 후보가 다르면 즉시 기준 모델을 교체하지 않고 후속 조합 후보로만 둔다.

## 실행한 세부 실험

| 실험 | 대상 | 기준 후보 | 비교 방향 |
|---|---|---|---|
| `PP-U1` | Warm Huber | `base_existing_combo` | 작가+크기 핵심축, depth/aspect/material/artist_works 추가, 생성 bucket 확장 |
| `PP-U2` | Warm CatBoost | `base_existing_combo` | Warm에서도 CatBoost가 작가 x 크기 x bucket 조합을 더 잘 나누는지 확인 |
| `PP-U3` | Cold LightGBM | `base_support_size` | CatBoost형 `medium_shape`, `support_shape`, `medium_size`, 전체 bucket 확장 비교 |
| `PP-U4` | Cold CatBoost | `base_medium_shape` | LightGBM형 `support_size`, `support_shape`, `medium_size`, depth-shape 조합 비교 |
| `PP-U5` | Warm Huber | `base_existing_combo` | `medium_category`, `support_category`, `medium_support_bucket`의 중복 여부를 원본만/조합만/동시 사용/제거 조건으로 분리 검증 |

## 핵심 결과

| 실험 | validation 1위 | validation MdAPE | test 1위 | test MdAPE | 판단 |
|---|---|---:|---|---:|---|
| `PP-U1` | `artist_size_depth` | `0.2093` | `full_plus_generated_buckets` | `0.2131` | Warm Huber는 생성 bucket 확장 후보가 test에서 개선되지만 validation 1위가 달라 즉시 교체보다 후속 조합 입력 후보 |
| `PP-U2` | `artist_size_only` | `0.2778` | `artist_size_generated_buckets` | `0.3125` | Warm CatBoost는 피처 변경으로 기존 CatBoost보다 개선되지만 Warm Huber/PP-T 후보보다 약해 주모델 후보는 아님 |
| `PP-U3` | `support_shape_combo` | `0.3834` | `medium_size_combo` | `0.4803` | Cold LightGBM은 피처 교환으로 기준보다 개선 여지가 확인됨. `support_shape`와 `medium_size`를 후속 후보로 유지 |
| `PP-U4` | `baseline_base_medium_shape` | `0.4194` | `lightgbm_swap_support_size` | `0.4835` | Cold CatBoost는 validation 기준 baseline 유지가 안전. support-size 교환은 test 개선 후보지만 즉시 교체는 보류 |
| `PP-U5` | `combo_bucket_only` | `0.2121` | `support_only` | `0.2165` | 재료/지지체 조합 피처 단독은 validation MdAPE가 가장 낮지만 MAPE/p95/RMSE가 악화. test 1위도 달라 현재 세 피처 동시 사용 구조는 유지 |

## 모델별 해석

### Warm Huber

- 기존 결론처럼 `artist_key`와 크기는 핵심이다.
- `artist_size_depth`는 validation MdAPE를 `0.2126 -> 0.2093`으로 낮췄지만 MAPE와 p95는 악화됐다.
- `full_plus_generated_buckets`는 test MdAPE를 `0.2274 -> 0.2131`, MAPE를 `0.4952 -> 0.4814`, p95를 `2.0130 -> 1.8591`로 낮췄다.
- 다만 validation에서는 기준 피처셋보다 MdAPE가 나빠졌으므로, 바로 Warm 기준 피처셋을 바꾸기보다 PP-T 계열 조합 후보로 넣는 것이 안전하다.
- PP-U5 재료/지지체 중복 검증에서는 `medium_support_bucket` 단독이 validation MdAPE `0.2121`로 가장 낮았다.
- 그러나 `medium_support_bucket` 단독은 validation MAPE `0.4350`, p95 `1.3815`, RMSE_log `0.6532`로 현재 기준 구조보다 불안정했다.
- `support_category` 단독과 원본 재료/지지체만 쓰는 구조는 test MdAPE가 좋았지만 validation에서 기준보다 나빴다.
- 따라서 Warm Huber의 재료/지지체 피처는 현재처럼 원본 재료, 원본 지지체, 조합 피처를 함께 쓰되, 보고서에서는 중복 가능성과 추가 안정성 검증 필요성을 명시한다.

### Warm CatBoost

- 피처셋을 바꾸면 Warm CatBoost 자체는 개선된다.
- test 기준 `artist_size_generated_buckets`가 기존 Warm CatBoost baseline 대비 MdAPE `0.3259 -> 0.3125`로 개선됐다.
- 그러나 Warm Huber 원 모델과 PP-T 최종 후보보다 여전히 약하다.
- 따라서 Warm CatBoost는 주모델보다 보조 residual/segment 후보로만 유지한다.

### Cold LightGBM

- validation에서는 `support_shape_combo`가 기준 LightGBM보다 소폭 개선됐다.
- test에서는 `medium_size_combo`가 MdAPE `0.4909 -> 0.4803`, MAPE `1.4131 -> 1.3722`, p95 `4.8212 -> 4.6205`로 개선됐다.
- `support_shape_combo`는 test MdAPE 개선폭은 작지만 MAPE와 p95 개선폭이 크다.
- LightGBM은 support-size만 고정하기보다 `medium_shape`, `medium_size` 조합을 후속 조합 후보로 추가할 가치가 있다.

### Cold CatBoost

- validation 기준으로는 기존 `base_medium_shape`가 여전히 가장 안전하다.
- test에서는 LightGBM형 `base_support_size`를 적용한 `lightgbm_swap_support_size`가 MdAPE `0.4867 -> 0.4835`, p95 `4.6329 -> 4.4439`로 개선됐다.
- 다만 validation에서 기준을 이기지 못했기 때문에 CatBoost 기준 피처셋을 바로 교체하는 것은 위험하다.
- support-size 교환 후보는 CatBoost Quantile 또는 PP-S 순차 구조의 입력 후보로만 유지한다.

## 후속 작업

- Warm: `full_plus_generated_buckets`를 PP-T fine blend 또는 meta stacking 입력 후보로 추가할지 검토한다.
- Warm: `PP-U5` 결과 기준으로 재료/지지체 피처는 현재 구조를 유지한다.
  - 이유: 조합 bucket 단독은 validation MdAPE만 소폭 개선됐고 MAPE/p95/RMSE가 악화
  - 후속: OOF 또는 다른 split seed에서 `combo_bucket_only`, `support_only`, `raw_medium_support_only` 안정성 재확인
- Cold LightGBM: `medium_size_combo`, `support_shape_combo`를 PP-Q/PP-S 계열 조합 후보에 추가하는 실험을 계획한다.
- Cold CatBoost: `lightgbm_swap_support_size`를 CatBoost Quantile 또는 CatBoost 선행 + Huber residual 구조에서 재검증한다.
- 기준 모델 교체는 validation/test 방향이 더 일치하는 추가 검증 후 결정한다.
