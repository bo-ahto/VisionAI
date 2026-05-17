# T5-E009 test 전 최종 확인 후보 목록 고정

- 날짜: 2026-05-18
- 관련 가설: T5-H12
- 상태: 완료
- 목적: test를 보기 전에 Warm / Cold 최종 확인 후보와 판단 기준을 문서로 고정

## 1. 왜 필요한가

- validation 결과를 본 뒤 test에서 계속 후보를 바꾸면 test에 맞춘 선택이 될 수 있음
- 최종 성능은 test에서 한 번 확인하는 것이 원칙
- 따라서 test 실행 전 후보와 판단 기준을 먼저 고정해야 함

## 2. 근거 실험

- T5-E002: 구조-only baseline
- T5-E003: Warm 작가 피처 ablation
- T5-E004: Cold 모델군 비교
- T5-E006: size/support/3D 피처 ablation
- T5-E007: 생성 조합 피처 검증
- T5-E008: 후보 피처 기반 모델군 재비교

## 3. Warm 최종 확인 후보

### 1순위 후보

- 모델: `HuberRegressor`
- 피처셋: `warm_full_size`
- validation 성능:
  - median APE: `0.1506`
  - p95 APE: `0.6999`
  - Within-30: `0.7014`
  - Within-50: `0.8914`

### 보조 후보

- 모델: `HuberRegressor`
- 피처셋: `warm_all_combo`
- validation 성능:
  - median APE: `0.1564`
  - p95 APE: `0.6634`
  - Within-30: `0.7330`
  - Within-50: `0.9005`

### Warm 판단 기준

- 1순위는 median APE 기준으로 판단
- p95 APE가 크게 악화되면 보조 후보를 함께 검토
- 두 후보의 test 결과 차이가 작으면 더 단순한 `warm_full_size`를 우선

## 4. Cold 최종 확인 후보

### 1순위 후보

- 모델: `QuantileRegressor`
- 피처셋: `cold_full_size`
- validation 성능:
  - median APE: `0.3432`
  - p95 APE: `1.8235`
  - Within-30: `0.4538`
  - Within-50: `0.6659`

### 보조 후보

- 모델: `QuantileRegressor`
- 피처셋: `cold_all_combo`
- validation 성능:
  - median APE: `0.3364`
  - p95 APE: `1.9122`
  - Within-30: `0.4515`
  - Within-50: `0.6761`

### Cold 판단 기준

- median APE만 보지 않고 p95 APE를 함께 본다.
- `cold_all_combo`가 median은 낮지만 p95가 나쁘므로, test에서도 p95가 악화되면 최종 후보에서 제외한다.
- Cold는 큰 오차 위험이 중요하므로 `cold_full_size`를 기본 우선 후보로 둔다.

## 5. test 사용 규칙

- test는 T5-E010에서 처음 사용한다.
- test 결과를 본 뒤 새로운 후보를 추가하지 않는다.
- test에서 후보가 모두 불안정하면, 최종 확정이 아니라 “Track5 추가 실험 필요”로 결론낸다.

## 6. 결론

- T5-H12는 완료로 본다.
- test 전 후보 목록이 고정되었다.
- 다음 단계는 T5-E010 최종 후보 test 확인이다.
