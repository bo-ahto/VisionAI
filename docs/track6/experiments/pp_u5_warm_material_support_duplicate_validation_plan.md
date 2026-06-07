# PP-U5 Warm Huber 재료/지지체 조합 안정성 검증 계획 및 실행 결과

- 실험 ID: `PP-U5`
- 실험명: Warm Huber 재료/지지체 원본 피처와 조합 피처 안정성 검증
- 대상 모델: Warm `Huber`
- 기준 피처셋: Warm Huber `base_existing_combo`
- 목적: `medium_category`, `support_category`, `medium_support_bucket`을 함께 쓰는 현재 구조가 재료/지지체 조합 차이를 안정적으로 반영하는지 확인

## 1. 실험 배경

- 현재 Warm Huber 기준 피처셋에는 아래 세 피처가 함께 포함됨
  - `medium_category`: 작품 재료 대분류
  - `support_category`: 작품이 올라간 바탕/지지체 대분류
  - `medium_support_bucket`: `medium_category`와 `support_category`를 결합한 재료/지지체 조합 피처
- `medium_support_bucket`은 재료와 지지체를 따로 보지 않고 “재료+바탕” 조합 단위로 가격 차이를 반영하기 위한 피처
- Warm Huber 전처리에서는 one-hot encoding의 `min_frequency=10` 기준을 사용하므로, 10건 미만 희소 조합은 자동으로 희소 범주로 묶임
- 따라서 조합 피처의 핵심 의미는 단순 중복이 아니라 희소한 재료/지지체 조합을 과도하게 세분화하지 않고 안정적으로 반영하는 것
- 기존 `PRE-PP-W`에서는 재료/지지체 그룹 전체를 제거했을 때 validation MdAPE가 `0.2126 -> 0.2170`으로 악화되어 그룹 단위 신호는 확인됨
- 하지만 기존 실험만으로는 아래 질문에 답하기 어려움
  - 원본 피처인 `medium_category`, `support_category`만으로 충분한가?
  - 조합 피처인 `medium_support_bucket`만 쓰는 것이 더 안정적인가?
  - 원본 피처와 조합 피처를 모두 쓰는 현재 방식이 가장 좋은가?
  - 재료/지지체 피처를 빼도 실제 성능 차이가 작다면 설명 편의상 제거하는 것이 나은가?

## 2. 핵심 질문

- Q1. Warm Huber에서 재료/지지체 정보는 유지해야 하는가?
- Q2. 유지한다면 원본 피처와 조합 피처 중 어떤 구조가 가장 안정적인가?
- Q3. 조합 피처가 희소 재료/지지체 조합을 안정화하는 데 도움이 되는가?
- Q4. 최종 보고서에서 재료/지지체 영향도를 어떤 단위로 설명하는 것이 가장 타당한가?

## 3. 통제 기준

- 데이터 split: 기존 Warm 고정 split 사용
- target: `ln_price_krw`
- 모델: `HuberRegressor`
- 모델 설정: Warm Huber 기준 설정 고정
- 전처리:
  - 숫자형 피처는 중앙값 결측 보정 후 표준화
  - 범주형 피처는 one-hot encoding
  - one-hot rare category 처리 기준은 기존 Warm Huber 설정 유지
  - 10건 미만 희소 범주는 자동 묶음 처리
- 평가 기준:
  - validation 기준으로 후보 판단
  - test는 선택 후보의 재현성 확인으로만 사용
- 변경 허용 범위:
  - 재료/지지체 관련 피처만 변경
  - 작가, 크기, 깊이/입체, 형태 피처는 모두 고정

## 4. 비교 후보

| 후보 ID | 후보명 | 재료/지지체 피처 구성 | 목적 |
|---|---|---|---|
| `baseline_all_three` | 현재 기준 구조 | `medium_category`, `support_category`, `medium_support_bucket` | 현재 Warm Huber 기준 피처셋 재현 |
| `raw_medium_support_only` | 원본 재료/지지체만 사용 | `medium_category`, `support_category` | 조합 피처 없이 원본 피처만으로 충분한지 확인 |
| `combo_bucket_only` | 조합 피처만 사용 | `medium_support_bucket` | 원본 피처를 빼고 조합 피처 하나로 설명 가능한지 확인 |
| `medium_only` | 재료만 사용 | `medium_category` | 재료 대분류만으로 보조 신호가 충분한지 확인 |
| `support_only` | 지지체만 사용 | `support_category` | 지지체 대분류만으로 보조 신호가 충분한지 확인 |
| `no_material_support` | 재료/지지체 제거 | 없음 | 재료/지지체 정보 자체의 필요성 재확인 |

공통 유지 피처:

- 작가 기준선: `artist_key`
- 크기: `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`
- 입체/깊이: `has_depth`, `is_3d_candidate`
- 형태: `aspect_ratio`, `is_extreme_aspect_ratio`

## 5. 기대 해석 기준

| 결과 패턴 | 해석 | 후속 판단 |
|---|---|---|
| `baseline_all_three`가 validation/test 모두 우세 | 세 피처 동시 사용이 중복보다 성능 이득이 큼 | 현재 구조 유지 |
| `raw_medium_support_only`가 비슷하거나 우세 | 조합 피처 없이 원본 피처만으로 충분 | `medium_support_bucket` 제거 검토 |
| `combo_bucket_only`가 비슷하거나 우세 | 재료와 지지체는 각각보다 조합 단위가 더 중요 | 원본 피처 제거 후 조합 피처 중심 설명 |
| `medium_only` 또는 `support_only`가 비슷 | 한쪽 피처만으로 충분할 가능성 | 더 단순한 피처셋 검토 |
| `no_material_support`가 비슷 | 재료/지지체는 Warm Huber에서 핵심 피처가 아님 | 최종 피처셋 단순화 검토 |
| validation과 test의 방향이 다름 | 데이터 분할에 민감한 불안정 신호 | 기준 피처셋 즉시 교체 보류 |

## 6. 판단 우선순위

- 1순위: validation MdAPE 개선
- 2순위: validation MAPE 개선
- 3순위: validation p95_APE 악화 여부
- 4순위: test에서 방향이 재현되는지 확인
- 5순위: 피처 설명의 단순성

판단 원칙:

- MdAPE가 비슷하면 더 단순한 피처 구성을 우선 검토
- MdAPE는 좋아지지만 MAPE 또는 p95_APE가 크게 악화되면 채택 보류
- test에서만 좋아진 후보는 최종 피처셋 교체 근거로 쓰지 않음

## 7. 산출물

- 실험 폴더: `experiments/track6/PP-U5_warm_huber_material_support_duplicate_validation/`
- 설정 파일: `experiment_config.json`
- 결과 리포트: `reports/result_report.md`, `reports/result_report.html`
- 결과 요약: `experiments/track6/PP-U5_summary_metrics.csv`
- 최종 리포트 반영:
  - Warm 재료/지지체 피처를 원본 중심으로 설명할지
  - 조합 bucket 중심으로 설명할지
  - 세 피처 동시 사용을 유지할지
  - 희소 조합 안정화 효과를 근거로 설명할지

## 8. 보고 문장 초안

- 현재 Warm Huber 기준 피처셋은 재료 대분류, 지지체 대분류, 재료-지지체 조합 피처를 함께 사용하고 있음
- 조합 피처는 재료와 지지체를 따로 보는 것보다 실제 작품 조건에 가까운 “재료+바탕” 단위로 가격 차이를 반영함
- 10건 미만 희소 조합은 one-hot 처리에서 자동으로 묶이므로, 소수 조합을 과도하게 따로 학습하는 위험을 줄임
- 기존 그룹 제거 실험에서는 재료/지지체 그룹의 보조 신호는 확인됐지만, 원본 피처와 조합 피처 중 어떤 구성이 가장 안정적인지는 분리 검증이 부족했음
- 이에 따라 같은 데이터 분할과 같은 Huber 설정에서 원본만, 조합만, 세 피처 동시 사용, 전체 제거 조건을 비교해 최종 피처 설명과 모델 입력 구조를 확정할 예정

## 9. 실행 결과

- 실행 스크립트: `scripts/track6/run_pp_u5_warm_material_support_duplicate_validation.py`
- 실행 결과 폴더: `experiments/track6/PP-U5_warm_huber_material_support_duplicate_validation/`
- 결과 요약: `experiments/track6/PP-U5_summary_metrics.csv`
- 공통 기준: 같은 Warm split, 같은 `HuberRegressor`, 같은 target(`ln_price_krw`)

Validation 결과:

| 후보 | 구성 | MdAPE | MAPE | p95_APE | RMSE_log | 기준 대비 MdAPE |
|---|---|---:|---:|---:|---:|---:|
| `combo_bucket_only` | 조합 피처만 사용 | `0.2121` | `0.4350` | `1.3815` | `0.6532` | `-0.0005` |
| `baseline_all_three` | 원본 2개 + 조합 피처 | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `+0.0000` |
| `medium_only` | 재료만 사용 | `0.2147` | `0.4448` | `1.3669` | `0.6584` | `+0.0021` |
| `support_only` | 지지체만 사용 | `0.2154` | `0.4345` | `1.3015` | `0.6562` | `+0.0028` |
| `no_material_support` | 재료/지지체 제거 | `0.2170` | `0.4450` | `1.3546` | `0.6651` | `+0.0044` |
| `raw_medium_support_only` | 원본 재료/지지체만 사용 | `0.2181` | `0.4351` | `1.3357` | `0.6520` | `+0.0055` |

Test 확인 결과:

| 후보 | 구성 | MdAPE | MAPE | p95_APE | RMSE_log | 기준 대비 MdAPE |
|---|---|---:|---:|---:|---:|---:|
| `support_only` | 지지체만 사용 | `0.2165` | `0.4944` | `2.0386` | `0.6078` | `-0.0109` |
| `raw_medium_support_only` | 원본 재료/지지체만 사용 | `0.2165` | `0.4955` | `2.0382` | `0.6097` | `-0.0109` |
| `medium_only` | 재료만 사용 | `0.2252` | `0.4958` | `1.9790` | `0.6148` | `-0.0022` |
| `no_material_support` | 재료/지지체 제거 | `0.2253` | `0.4987` | `1.9928` | `0.6148` | `-0.0021` |
| `combo_bucket_only` | 조합 피처만 사용 | `0.2273` | `0.4931` | `2.0145` | `0.6054` | `-0.0001` |
| `baseline_all_three` | 원본 2개 + 조합 피처 | `0.2274` | `0.4952` | `2.0130` | `0.6081` | `+0.0000` |

## 10. 실행 결과 해석

- 재료/지지체 그룹 자체는 제거하지 않는 것이 안전
  - `no_material_support`는 validation MdAPE가 `0.2126 -> 0.2170`으로 악화
  - 재료/지지체 정보가 Warm Huber에서 완전히 불필요하다고 보기는 어려움
- 조합 피처 단독 사용은 가능성이 있으나 즉시 교체 근거는 부족
  - `combo_bucket_only`는 validation MdAPE가 `0.2121`로 가장 낮음
  - 하지만 validation MAPE, p95_APE, RMSE_log는 현재 기준 구조보다 모두 악화
- 원본 피처만 사용하는 방식은 test MdAPE가 좋지만 validation에서 불안정
  - `raw_medium_support_only`와 `support_only`는 test MdAPE가 `0.2165` 수준으로 좋아짐
  - 하지만 validation에서는 현재 기준 구조보다 MdAPE가 나빠져 기준 피처셋 교체 근거로 쓰기 어려움
- 현재 기준 구조는 보수적으로 유지
  - validation에서 MdAPE 2위
  - validation MAPE, p95_APE, RMSE_log는 가장 안정적
  - validation/test의 1위 후보가 다르기 때문에 즉시 단순화는 보류

최종 판단:

- 현재 Warm Huber 기준 피처셋에서 `medium_category`, `support_category`, `medium_support_bucket`을 함께 쓰는 방식은 재료/지지체 단독 신호와 조합 신호를 함께 반영하는 구조임
- 다만 이번 통제 실험에서는 세 피처를 제거하거나 단순화했을 때 validation 안정성이 일관되게 개선되지는 않음
- 따라서 현재 모델 입력은 유지하되, 보고서에는 “재료/지지체 그룹은 보조 신호가 있으며, 조합 피처는 희소한 재료/지지체 조합을 안정적으로 반영하기 위한 피처”로 설명
- 후속으로 OOF 또는 다른 split seed에서 `combo_bucket_only`, `support_only`, `raw_medium_support_only`의 안정성을 재확인하면 단순화 여부를 더 명확히 판단 가능
