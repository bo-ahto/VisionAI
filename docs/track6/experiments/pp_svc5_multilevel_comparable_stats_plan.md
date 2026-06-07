# PP-SVC5 다층 비교군 통계 피처 실험 계획

## 1. 실험 목적

- 기존 `PP-SVC1~PP-SVC4`에서 비교군 통계 피처가 Warm Huber 성능을 크게 개선한 점 확인
- 기존 방식은 한 샘플마다 조건을 만족하는 비교군 하나만 선택하는 fallback 구조
- 추가 실험은 여러 비교군 수준을 동시에 피처로 제공
- 목적은 Huber가 작가 기준, 작가+크기 기준, 작가+재료/지지체+크기 기준, 재료/크기 기준 중 어떤 정보를 더 신뢰해야 하는지 직접 학습하는지 확인

## 2. 이전 실험에서 확인한 근거

- `PP-SVC1`
  - Warm Huber baseline test MdAPE `0.2274`
  - Warm Huber `svc_full` test MdAPE `0.1496`
  - 비교군 통계가 Warm에서 가격 기준선을 크게 보완
- `PP-SVC3`
  - `svc_numeric` 계열과 `PP-V8` 방어형 후보를 70:30으로 결합
  - test MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`
  - Warm 서비스 1순위 후보
- 남은 질문
  - fallback으로 선택된 하나의 비교군만 쓰는 것이 최적인지 확인 필요
  - 여러 비교군 수준을 동시에 보여주면 Huber가 더 좋은 조합을 찾을 가능성 존재

## 3. 실험 대상

- 대상 데이터
  - Warm split
  - train/validation/test 고정
- 대상 모델
  - Warm Huber
- 기준 피처
  - 기존 Warm final artifact 기준 피처셋
  - `base_existing_combo`로 사용하던 Warm Huber 기준 피처
- 추가 피처
  - train-only 비교군 통계
  - train row는 교차검증 방식으로 자기 자신의 가격이 들어가지 않게 생성

## 4. 비교군 수준

| 비교군 수준 | 의미 | 최소 표본 기준 |
|---|---|---:|
| `artist_medium_support_size` | 같은 작가 + 같은 재료/지지체 + 비슷한 크기 | 5 |
| `artist_size` | 같은 작가 + 비슷한 크기 | 5 |
| `artist` | 같은 작가 전체 | 5 |
| `medium_support_size` | 같은 재료/지지체 + 비슷한 크기 | 30 |
| `medium_category_support_size` | 같은 재료 + 같은 지지체 + 비슷한 크기 | 30 |
| `medium_size` | 같은 재료 + 비슷한 크기 | 50 |

## 5. 실험 후보

| 후보 | 구성 | 확인 질문 |
|---|---|---|
| `baseline_huber` | 기존 Warm Huber 피처만 사용 | 기존 기준선 |
| `fallback_numeric` | 기존 PP-SVC1 방식의 선택된 비교군 통계 사용 | 기존 비교군 방식 재현 |
| `multi_default_median_n` | 모든 비교군 수준의 중앙값, 면적단가 중앙값, 표본 수를 동시에 사용 | 여러 비교군 수준을 동시에 주면 개선되는가? |
| `multi_default_full_numeric` | 모든 비교군 수준의 중앙값, 분위값, 범위, 면적단가, 표본 수를 동시에 사용 | 더 많은 통계량이 도움이 되는가? |
| `multi_loose_median_n` | 최소 표본 기준을 완화한 다층 비교군 통계 | 작가 세부 비교군 coverage를 늘리면 개선되는가? |
| `multi_strict_median_n` | 최소 표본 기준을 강화한 다층 비교군 통계 | 표본 수가 충분한 비교군만 쓰면 안정성이 좋아지는가? |
| `multi_plus_fallback` | 기존 fallback 통계 + 다층 중앙값/표본 수 결합 | 기존 최적 구조와 새 구조를 같이 쓰면 개선되는가? |

- 다층 피처 후보는 비교군 통계가 서로 겹치는 구조
- Huber 계수가 불안정해질 수 있으므로 `alpha=0.01`, `alpha=0.1` 정규화 후보를 함께 실행
- validation에서 비정상적으로 큰 오차가 나는 후보는 PP-V8 결합 대상에서 제외

## 6. 보정/결합 확인

- 각 후보의 Warm Huber 예측값 생성
- 기존 방어형 후보 `PP-V8 compact_blend_mape_guarded`와 로그 가격 기준 가중 결합
- 가중치 후보
  - 새 비교군 후보 `50~90%`
  - PP-V8 방어 후보 `10~50%`
- 선택 기준
  - validation에서 MAPE를 줄이되 MdAPE가 기존 PP-V8보다 나빠지지 않는 후보 우선
  - test는 확인 전용

## 7. 기대 결과

- 개선 가능성이 있는 경우
  - `multi_default_median_n` 또는 `multi_plus_fallback`이 `fallback_numeric`보다 validation/test에서 MdAPE 또는 MAPE 개선
  - 기존 `PP-SVC3 70:30` 후보보다 test MdAPE/MAPE/p95 중 하나 이상 개선
- 개선이 없더라도 얻는 결론
  - fallback으로 하나의 비교군을 선택하는 기존 방식이 충분히 안정적이라는 근거 확보
  - 서비스 API에는 기존 비교군 통계 구조를 유지하는 판단 가능

## 8. 리스크 통제

- 데이터 누수 방지
  - train 비교군 통계는 5-fold 교차검증 방식으로 생성
  - validation/test 비교군 통계는 train 데이터만 사용
- 과세분화 방지
  - 기본/완화/강화 최소 표본 기준을 나눠 비교
  - 표본 수가 부족한 비교군은 통계값을 직접 쓰지 않고 coverage만 기록
- 과적합 방지
  - validation 선택, test 확인 구조 유지
  - 개선 후보는 이후 PP-SVC4와 같은 반복 holdout 검증 대상으로 승격

## 9. 후속 판단

- 새 후보가 `PP-SVC3`보다 개선
  - PP-SVC6 안정성 검증으로 승격
  - row/artist holdout 반복 검증 진행
- 새 후보가 `PP-SVC3`와 비슷하거나 약함
  - 기존 Warm 서비스 후보 유지
  - 다층 비교군 통계는 설명용/API 표시용 보조 정보로만 활용
