# T5-E014 Warm 작가 통계 확장 실험

- 날짜: 2026-05-18
- 관련 가설: T5-H17
- 목적: 작가별 가격 통계를 더 세분화하면 Warm 성능이 개선되는지 확인

## 실험 방법

- 기준 모델: HuberRegressor
- 평가 데이터: `track5_val_warm.csv`
- 기준 피처: Warm full_size
- 추가 피처
  - 작가별 q10 / q25 / q75 / q90 로그가격
  - 작가별 min / max / std / price span
  - 작가별 작품 수 bucket

## 결과

| 설정 | median APE | p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|
| base stats | 0.1500 | 0.7035 | 0.6968 | 0.8914 |
| extended stats | 0.1516 | 0.7049 | 0.7059 | 0.8869 |

## 해석

- 확장 통계 단독으로는 median APE와 p95 APE가 모두 개선되지 않음
- Within-30은 소폭 좋아졌지만 최종 채택 근거로는 약함
- 피처 수가 늘어난 만큼의 성능 개선은 확인되지 않음

## 결론

- 확장 작가 통계 단독 추가는 보류
- OOF 안정성 실험에서 tail 개선 신호가 있는지 별도로 판단
