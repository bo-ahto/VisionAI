# OP-V01-CAL-05 범위 정책 반복 검증

## 1. 목적

- CAL-04의 `fixed_125_width` 범위/신뢰도 보정 후보가 특정 test split에서만 좋아진 결과인지 확인한다.
- 점가격은 바꾸지 않는다.
- 범위 정책만 기존 v0.1 예측값 위에서 반복 검증한다.

## 2. 기준 후보

- 기준 범위: `baseline_centered_width`
- 검증 후보: `fixed_125_width`
- 기준 후보 의미: `routing_width`를 그대로 사용
- 검증 후보 의미: `routing_width * 1.25`로 표시 범위를 25% 넓힘

## 3. 검증 방식

- validation/test 전체 지표를 먼저 비교한다.
- test row bootstrap으로 행 단위 안정성을 확인한다.
- test artist bootstrap으로 작가 단위 안정성을 확인한다.
- 0604 신규 라벨은 반복 검증에 사용하지 않는다.

## 4. 판단 기준

- 범위 포함률 개선 평균이 양수여야 한다.
- bootstrap 반복 중 95% 이상에서 포함률이 개선되어야 한다.
- p90 범위 폭 증가가 과도하면 서비스 기본 정책으로 채택하지 않는다.

