# PP-SVC1 서비스 비교군 통계 피처 검증 계획

- 작성일: 2026-06-03
- 실험 ID: `PP-SVC1`
- 실험명: 서비스 비교군 통계 피처 검증
- 목적: 서비스 화면/API에서 필요한 비교군 통계값을 모델 입력 피처로도 사용할 수 있는지 검증한다.

## 1. 실험 배경

- 실제 서비스에서는 단일 예측 가격만 제공하면 사용자가 가격의 근거를 이해하기 어렵다.
- 서비스 화면에는 아래와 같은 비교군 기반 참고값이 필요하다.
  - 비교군 중앙 가격
  - 비교군 가격 범위
  - 비교군 표본 수
  - 매체/지지체/크기 구간별 가격 분포
- 이 값들은 API 응답에 직접 들어갈 수 있고, 동시에 모델이 가격을 예측할 때도 유용한 피처가 될 수 있다.
- 기존 실험에서는 `qwidth_bin`, 검색/외부 피처, 모델 조합이 성능 개선에 일부 도움이 됐다.
- 다음 단계에서는 운영에서 설명 가능한 비교군 통계값이 Warm/Cold 성능도 개선하는지 확인한다.

## 2. 현재 데이터 기준

- 현재 Track6 split 파일에는 `estimated_ho` 컬럼이 없다.
- 따라서 이번 실험에서는 “호당가”를 직접 계산하지 않는다.
- 이번 실험의 단가 기준은 아래처럼 정의한다.

```text
면적 기준 단가 = price_krw / area_cm2
로그 면적 단가 = ln_price_krw - log(area_cm2)
```

- 서비스 문서에서는 이를 `호당가`로 확정하지 않고 `면적 기준 단가` 또는 `비교군 단가`로 표현한다.
- 추후 `estimated_ho`가 split과 운영 DB에 추가되면 아래 식으로 교체할 수 있다.

```text
호당가 = price_krw / estimated_ho
```

## 3. 비교군 정의

비교군은 운영에서 예측 대상 작품의 가격을 몰라도 알 수 있는 값만 사용한다.

| 우선순위 | 비교군 이름 | 비교군 기준 | 최소 표본 수 | 의미 |
|---:|---|---|---:|---|
| 1 | 작가+재료/지지체+크기 | `artist_key`, `medium_support_bucket`, `size_bucket` | 5 | 같은 작가의 비슷한 재료/크기 작품 |
| 2 | 작가+크기 | `artist_key`, `size_bucket` | 5 | 같은 작가의 비슷한 크기 작품 |
| 3 | 작가 전체 | `artist_key` | 5 | 같은 작가의 과거 거래/판매 작품 |
| 4 | 재료/지지체+크기 | `medium_support_bucket`, `size_bucket` | 30 | 작가 정보가 약할 때 작품 조건 기반 비교군 |
| 5 | 재료+지지체+크기 | `medium_category`, `support_category`, `size_bucket` | 30 | 재료와 지지체를 분리한 조건 비교군 |
| 6 | 재료+크기 | `medium_category`, `size_bucket` | 50 | 더 넓은 작품 조건 비교군 |
| 7 | 전체 기준 | 전체 학습 데이터 | 0 | 모든 비교군이 부족할 때 fallback |

## 4. 생성 피처

모델에 추가할 피처는 예측 대상의 실제 가격을 사용하지 않는다.

| 피처 | 타입 | 설명 |
|---|---|---|
| `svc_group_log_price_median` | 숫자 | 선택된 비교군의 로그 가격 중앙값 |
| `svc_group_log_price_q25` | 숫자 | 선택된 비교군의 로그 가격 25% 지점 |
| `svc_group_log_price_q75` | 숫자 | 선택된 비교군의 로그 가격 75% 지점 |
| `svc_group_log_price_iqr` | 숫자 | `q75 - q25`, 비교군 가격 분산 폭 |
| `svc_group_log_unit_area_median` | 숫자 | 선택된 비교군의 로그 면적 단가 중앙값 |
| `svc_group_log_unit_area_iqr` | 숫자 | 비교군 로그 면적 단가의 분산 폭 |
| `svc_group_n_log` | 숫자 | `log(1 + 비교군 표본 수)` |
| `svc_group_level` | 범주 | 실제로 선택된 비교군 단계 |
| `svc_coverage_tier` | 범주 | 표본 수 기준 안정성 등급 |
| `svc_has_artist_level` | 범주 | 작가 기반 비교군이 사용됐는지 여부 |

## 5. 누수 방지 기준

- validation/test 비교군 통계는 반드시 train 데이터만 사용해서 계산한다.
- validation/test의 실제 가격은 통계 계산에 사용하지 않고 평가 라벨로만 사용한다.
- train에 들어가는 비교군 통계는 자기 자신의 가격이 들어가지 않도록 5-fold 방식으로 만든다.
- train fold별로 아래 순서를 지킨다.
  - fold 학습 부분으로 비교군 통계 계산
  - fold 검증 부분에 해당 통계 적용
  - 비교군 표본이 부족하면 상위 fallback 적용
- 이렇게 만든 train 피처로 모델을 학습하고, validation/test에는 전체 train 기준 통계를 적용한다.

## 6. 평가 대상 모델

| 세부 실험 | 대상 | 기준 모델 | 기준 피처셋 | 추가 피처 |
|---|---|---|---|---|
| `PP-SVC1-W` | Warm | Huber | `base_existing_combo` | 비교군 통계 |
| `PP-SVC1-CB` | Cold | CatBoost | `base_medium_shape` | 비교군 통계 |
| `PP-SVC1-LGBM` | Cold | LightGBM | `base_support_size` | 비교군 통계 |

## 7. 후보 구성

| 후보 | 설명 |
|---|---|
| `baseline` | 기존 기준 피처셋만 사용 |
| `svc_numeric` | 기존 기준 피처셋 + 숫자형 비교군 통계 |
| `svc_full` | 기존 기준 피처셋 + 숫자형 비교군 통계 + 비교군 단계/표본 등급 |

## 8. 기대 효과

- Warm에서는 작가 기반 비교군이 사용될 수 있어, Huber의 작가 기준선과 가격 중심선을 더 안정적으로 보완할 가능성이 있다.
- Cold에서는 작가 기반 비교군 사용률이 낮을 수 있으나, 재료/지지체/크기 기반 비교군이 기본 가격대 prior 역할을 할 수 있다.
- 모델 성능 개선이 작더라도 API 응답에 필요한 값의 coverage와 안정성을 동시에 확인할 수 있다.

## 9. 채택 기준

| 기준 | 내용 |
|---|---|
| 성능 | baseline 대비 MdAPE가 개선되거나, MdAPE 유지 상태에서 MAPE/p95_APE가 개선되면 후보로 유지 |
| 안정성 | validation과 test의 개선 방향이 크게 충돌하지 않아야 함 |
| 누수 | train OOF 통계, validation/test train-only 통계 원칙이 지켜져야 함 |
| 서비스성 | 비교군 coverage와 fallback 단계가 API 문서에 설명 가능한 수준이어야 함 |

## 10. 결과물

- `experiments/track6/PP-SVC1_comparable_stats_feature_validation/outputs/metrics.csv`
- `experiments/track6/PP-SVC1_comparable_stats_feature_validation/outputs/predictions.csv`
- `experiments/track6/PP-SVC1_comparable_stats_feature_validation/outputs/coverage_summary.csv`
- `experiments/track6/PP-SVC1_comparable_stats_feature_validation/reports/result_report.md`
- `experiments/track6/PP-SVC1_comparable_stats_feature_validation/reports/result_report.html`
- `docs/track6/experiments/pp_svc1_comparable_stats_feature_validation_summary.md`
