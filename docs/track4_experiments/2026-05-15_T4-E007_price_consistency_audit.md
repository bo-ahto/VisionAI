# T4-E007 가격 정합성 감사

- 날짜: 2026-05-15
- 연결 가설: T4-C1
- 상태: 완료
- 목적: Track 4 원본 보존 통합본에서 가격값을 학습 target으로 사용할 수 있는지 확인

## 1. 사용 데이터

- 입력 데이터: `data/track4_primary_market_raw_collected.csv`
- 입력 행 수: `54,842`
- 감사 결과 CSV: `data/track4_price_consistency_audit.csv`
- 감사 요약 JSON: `data/track4_price_consistency_audit_summary.json`
- 요약 문서: `docs/track4_price_consistency_audit.md`

## 2. 실행 방법

- 스크립트: `scripts/track4/audit_price_consistency.py`
- 출처별 원본 가격 컬럼을 그대로 읽음
- 표준 KRW 가격 후보를 생성함
- 가격 누락, 1만원 미만, 1억 초과, 10억 초과, 통화 누락을 flag로 기록함
- 원본 가격 문자열과 표준 가격 후보를 분리해서 관리함

## 3. 사용한 가격 컬럼

- Saatchi: `saatchi__price_raw`, `saatchi__price_currency`, `saatchi__price_krw`
- Artsy: `artsy__price_raw`, `artsy__price_currency`, `artsy__price_amount`, `artsy__price_krw`
- Artue: `artue__Price (KRW)`, `artue__Price (USD)`
- Gallery primary: `gallery_primary__price`, `gallery_primary__price_raw`

## 4. 주요 결과

- 전체 행: `54,842`
- 가격 정상 후보: `34,883`
- 가격 이슈 후보: `19,959`
- KRW 가격 누락: `18,928`
- 원본 가격 문자열 누락: `3,091`
- 1만원 미만: `55`
- 1억 초과: `976`
- 10억 초과: `10`

## 5. 출처별 결과

| 출처 | 전체 | 정상 | 이슈 | 중앙값 | 최대 |
|---|---:|---:|---:|---:|---:|
| Artsy | `30,046` | `10,924` | `19,122` | `4,140,000` | `55,200,000,000` |
| Artue | `2,783` | `2,775` | `8` | `2,785,900` | `444,861,500` |
| Gallery primary | `292` | `235` | `57` | `20,336,700` | `2,765,568,000` |
| Saatchi | `21,721` | `20,949` | `772` | `2,559,900` | `145,507,200` |

## 6. 해석

- Artsy는 가격 없는 작품이 많아 학습 target 후보에서 제외되는 행이 많음
- Saatchi / Artue는 가격 사용 가능 비율이 높음
- Gallery primary는 행 수는 적지만 고가 작품 비중이 높음
- 1만원 미만 가격은 실제 가격이라기보다 파싱 오류나 자리표시값일 가능성이 높음
- 10억 초과 가격은 일반 학습 target을 흔들 수 있어 기본 학습에서 분리하는 것이 안전함
- 1억 초과 가격은 무조건 제외하지 말고 고가 flag로 관리하는 것이 적절함

## 7. 결론

- 채택: 가격 클렌징 규칙을 다음 단계 데이터 생성에 반영
- 제외 규칙:
  - `price_krw`가 없으면 제외
  - `price_krw <= 0`이면 제외
  - `price_krw < 10,000`이면 제외
  - `price_krw > 1,000,000,000`이면 기본 학습 후보에서 제외하고 별도 검토
- 유지 규칙:
  - `100,000,000 < price_krw <= 1,000,000,000`은 유지
  - 단, `is_high_price_candidate` flag를 붙여 이후 실험에서 영향 확인

## 8. 다음 작업

- `T4-C2` 크기 정합성 감사 진행
- 이후 `cleaned_v2` 생성 시 가격 규칙을 코드로 고정
- 고가 flag가 모델 성능과 tail risk에 미치는 영향은 별도 피처 실험으로 검증
