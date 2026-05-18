# T5-E020 Cold 보정 + 위험 경고 정책 결합 검증

- 날짜: 2026-05-18
- 관련 가설: T5-H23
- 목적: Cold 가격대 보정과 위험 경고 정책을 함께 쓰면 서비스 해석 가능성이 높아지는지 확인

## 실험 방법

- 기준 예측: T5-E010 Cold final 후보
- 보정 예측: T5-E018 가격대별 residual 보정
- 정책 구분
  - standard: 재료/지지체 정보가 있고 초대형 작품이 아님
  - caution: 재료 unknown, 지지체 unknown, 초대형 작품 중 하나라도 해당
- 비교 정책
  - baseline: 기존 Cold 예측
  - corrected: 전체 Cold에 가격대 보정 적용
  - hybrid: standard만 보정 적용, caution은 기존 예측 유지

## 결과

| 정책 | median APE | p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|
| baseline | 0.3918 | 2.0152 | 0.3930 | 0.5746 |
| corrected 전체 적용 | 0.3837 | 2.0194 | 0.4047 | 0.6008 |
| hybrid | 0.3764 | 1.9047 | 0.4064 | 0.6046 |

## 구간별 결과

| 정책 | 구간 | rows | median APE | p95 APE |
|---|---|---:|---:|---:|
| baseline | standard | 2125 | 0.3809 | 1.7409 |
| baseline | caution | 771 | 0.4258 | 2.5798 |
| corrected | standard | 2125 | 0.3671 | 1.5992 |
| corrected | caution | 771 | 0.4482 | 2.8088 |
| hybrid | standard | 2125 | 0.3671 | 1.5992 |
| hybrid | caution | 771 | 0.4258 | 2.5798 |

## 해석

- 전체 보정은 median과 Within을 개선하지만 caution 구간을 악화시킴
- standard 구간에서는 보정 효과가 뚜렷함
- caution 구간은 보정하지 않고 경고 정책으로 관리하는 편이 더 안전함
- hybrid 정책이 전체 median, p95, Within-30/50을 모두 개선함

## 결론

- Cold 운영 정책 후보
  - standard: 가격대 보정 적용
  - caution: 가격대 보정 미적용, 신뢰도 경고 표시
- Cold 단일 가격만 제공하는 방식보다 hybrid 정책이 더 적합함
