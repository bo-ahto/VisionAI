# H48-H60 후속 검증 기록

- 날짜: 2026-05-14
- 실험 ID: `H48_H60_pending_followups`
- 관련 가설: H48, H49, H50, H51, H52, H57, H58, H59, H60
- 실행 스크립트: `scripts/track3/h48_h60_pending_followups.py`
- 결과 파일: `data/track3_h48_h60_pending_followups_results.json`

## 1. 실험 목적

- H46/H47 이후 남아 있던 신뢰도/가격 범위 정책 가설을 확인함
- H57~H60의 성능 개선 후보를 단일 seed 기준으로 먼저 스크리닝함
- Warm은 H66 후보를 기준으로 비교함
- Cold는 H32 조건부 fallback을 기준으로 비교함

## 2. 사용 데이터

- 학습 데이터: `data/release_split/track3_train.csv`
- Warm 평가 데이터: `data/release_split/track3_test_warm.csv`
- Cold 평가 데이터: `data/release_split/track3_test_cold.csv`
- 실행 기준 행 수
- train: 34,629
- Warm: 1,685
- Cold: 3,823

## 3. 기준 모델

- Warm 기준 모델
- H66 `larger_low_lr` LightGBM
- 기준 Warm median APE: `0.1027` 단일 seed 기준
- Cold 기준 모델
- H32 조건부 fallback
- Cold 2D는 기본 Quantile/LAD 모델 사용
- Cold 3D는 3D 피처 모델 사용
- 기준 Cold median APE: `0.2786`

## 4. 핵심 결과

### H48. Cold high-risk 기준 재정의

- `large_ho_only`
- high-risk median APE `0.4448`
- low-risk median APE `0.2394`
- high-risk p95 APE `2.5694`
- `very_large_area_only`
- high-risk median APE `0.4448`
- low-risk median APE `0.2346`
- high-risk p95 APE `1.9132`
- `3d_only`
- high-risk median APE `0.2364`
- low-risk median APE `0.3767`
- 단순 3D 여부는 high-risk 기준으로 부적합

### H49. Cold 3D 중간 부피 예외

- H32 전체 Cold median APE: `0.2786`
- 중간 부피 예외 적용 전체 Cold median APE: `0.2765`
- 중간 3D 구간 median APE: `0.2238 -> 0.1912`
- 전체 p95 APE: `1.4860 -> 1.6229`
- 중간 3D p95 APE: `0.9427 -> 1.3670`
- median은 개선되지만 tail risk가 커져 전면 채택은 보류

### H50. Warm 신뢰도 등급

- A, 작가 학습 이력 51건 이상
- median APE `0.0570`
- p95 APE `0.5604`
- B, 11~50건
- median APE `0.0705`
- p95 APE `0.7167`
- C, 4~10건
- median APE `0.1288`
- p95 APE `0.9585`
- D, 1~3건
- median APE `0.1714`
- p95 APE `2.0514`
- 작가 이력 수 기반 등급은 신뢰도 구분에 유효함

### H51. Warm 등급별 가격 범위

- A/B 등급은 전역 width보다 더 좁은 등급별 width로도 coverage 확보 가능
- D 등급은 전역 width80 coverage가 `0.6667`로 부족함
- D 등급은 별도 width80 적용 시 coverage `0.8004`
- 저이력 작가는 더 넓은 가격 범위가 필요함

### H52. Cold 조건별 가격 범위

- 전체 Cold width80 coverage: `0.7999`
- Cold 2D는 전역 width80 coverage `0.6915`로 부족함
- Cold large_ho는 전역 width80 coverage `0.6770`로 부족함
- Cold very_large_area는 전역 width80 coverage `0.6187`로 부족함
- Cold는 단일 가격 범위보다 2D/대형/초대형 조건별 범위가 더 적절함

### H57/H58. Warm 피처 확장 단일 seed 스크리닝

- H66 base median APE: `0.1027`
- H57 extended history: `0.1008`
- H58 interactions: `0.1014`
- H57+H58 combined: `0.1012`
- 단일 seed에서는 개선 신호가 있으나 multi-seed 확인 필요

### H59. Cold 재료별 스케일 보정

- H32 base median APE: `0.2786`
- medium shift 0.10: `0.2783`
- 개선 폭이 매우 작고 within-30%는 악화되어 채택 보류

### H60. Cold medium/support 조합 정리

- H32 base median APE: `0.2786`
- combo base only: `0.2922`
- combo base + 3D fallback: `0.2803`
- 기존 H32보다 악화되어 기각

## 5. 결론

- H48은 `large_ho`, `very_large_area` 중심 high-risk 기준이 유효함
- H49는 median 개선은 있으나 p95 악화 때문에 채택 보류
- H50/H51은 Warm 신뢰도 등급과 등급별 가격 범위 정책 근거로 채택 가능
- H52는 Cold 조건별 가격 범위 정책 근거로 채택 가능
- H57/H58은 단일 seed 개선 신호가 있어 H67 multi-seed 재검증으로 이관
- H59는 개선 폭이 너무 작아 보류
- H60은 기각

## 6. 다음 작업

- H57/H58은 H67에서 multi-seed 재검증
- 최종 운영 정책 문서에는 Warm 등급별 범위와 Cold 조건별 범위를 분리해 반영
- Cold high-risk 경고 조건은 `large_ho`, `very_large_area`, `extra_large_ho` 중심으로 정리
