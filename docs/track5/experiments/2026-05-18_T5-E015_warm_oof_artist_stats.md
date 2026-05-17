# T5-E015 Warm OOF 작가 통계 안정성 검증

- 날짜: 2026-05-18
- 관련 가설: T5-H18
- 목적: 작가 통계를 OOF 방식으로 만들어도 Warm 성능이 유지되는지 확인

## 실험 방법

- train 내부 작가 통계를 KFold OOF 방식으로 생성
- validation은 기존처럼 train 전체 기준 작가 통계를 사용
- 비교 대상
  - OOF base stats
  - OOF extended stats

## 결과

| 설정 | median APE | p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|
| OOF base stats | 0.1516 | 0.7105 | 0.7104 | 0.8959 |
| OOF extended stats | 0.1525 | 0.6893 | 0.7149 | 0.9005 |

## 해석

- median APE는 기존 base보다 약간 나빠짐
- OOF extended는 p95 APE와 Within 계열이 좋아져 큰 오차 완화 신호가 있음
- 작가 통계 피처가 완전히 불안정한 것은 아니지만, median 개선용 피처라기보다 tail 안정화 후보에 가까움

## 결론

- OOF 작가 통계는 후속 후보로 유지
- 최종 후보로 올리려면 `max_iter=3000` 설정으로 재검증 필요
