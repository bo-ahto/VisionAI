# T4-E010 재료/지지체 정합성 감사

- 날짜: 2026-05-15
- 연결 가설: T4-C3
- 상태: 완료
- 목적: Track 4 원본 보존 통합본에서 출처별로 다른 재료/지지체 표현을 공통 카테고리로 묶을 수 있는지 확인

## 1. 사용 데이터

- 입력 데이터: `data/track4_primary_market_raw_collected.csv`
- 입력 행 수: `54,842`
- 감사 결과 CSV: `data/track4_medium_support_consistency_audit.csv`
- 감사 요약 JSON: `data/track4_medium_support_consistency_audit_summary.json`
- 요약 문서: `docs/track4/audits/medium_support_consistency_audit.md`

## 2. 실행 방법

- 스크립트: `scripts/track4/audit_medium_support_consistency.py`
- 출처별 원본 재료 문자열을 `medium_raw`로 보존함
- 원본 문자열에서 재료 키워드와 지지체 키워드를 따로 매칭함
- 표준 재료 후보 `medium_category`를 생성함
- 표준 지지체 후보 `support_category`를 생성함
- 다중 재료와 다중 지지체는 원본 매칭 목록을 별도 컬럼으로 보존함
- Saatchi는 원본 재료 문자열에 지지체가 없을 때 기존 `support_type`을 보조값으로 사용함

## 3. 사용한 재료/지지체 컬럼

- Saatchi: `saatchi__medium`, `saatchi__support_type`, `saatchi__medium_category`, `saatchi__medium_l1`, `saatchi__support_l1`
- Artsy: `artsy__medium`, `artsy__category`, `artsy__medium_type`
- Artue: `artue__Medium (EN)`, `artue__Medium (KO)`
- Gallery primary: `gallery_primary__materials`

## 4. 주요 결과

- 전체 행: `54,842`
- 재료 매핑 정상 후보: `53,646`
- 재료 이슈 후보: `1,196`
- 재료 미분류: `1,196`
- 원본 재료 문자열 결측: `28`
- `-` 같은 자리표시값: `26`
- 지지체 미분류: `6,286`
- 다중 재료 후보: `16,923`
- 다중 지지체 후보: `2,338`

## 5. 출처별 결과

| 출처 | 전체 | 정상 | 이슈 | 재료 미분류 | 지지체 미분류 | 다중 재료 |
|---|---:|---:|---:|---:|---:|---:|
| Artsy | `30,046` | `29,253` | `793` | `793` | `5,145` | `9,457` |
| Artue | `2,783` | `2,698` | `85` | `85` | `638` | `726` |
| Gallery primary | `292` | `291` | `1` | `1` | `24` | `159` |
| Saatchi | `21,721` | `21,404` | `317` | `317` | `479` | `6,581` |

## 6. 표준 재료 카테고리

- 상위 카테고리:
  - `mixed_media`: `19,491`
  - `acrylic`: `14,127`
  - `oil`: `13,662`
  - `painting_material`: `1,929`
  - `sculpture_material`: `1,248`
  - `other`: `1,142`
  - `ink`: `1,008`
  - `ceramic`: `615`
- `Oil on canvas`, `캔버스에 유채`, `oil on Canvas`는 `oil` + `canvas`로 묶음
- `Acrylic on canvas`, `Airbrushed acrylics on canvas`, 아크릴 표현은 `acrylic`으로 묶음
- `Oil and acrylic`, `Mixed media`, 재료가 2개 이상 매칭되는 경우는 `mixed_media`로 묶음
- `Color`, `Pigment`, `Painting`, `Lacquer`, `Crayon`, `Pen` 계열은 `painting_material`로 묶음

## 7. 표준 지지체 카테고리

- 상위 카테고리:
  - `canvas`: `32,502`
  - `paper`: `9,752`
  - `unknown`: `6,286`
  - `panel`: `1,833`
  - `linen`: `1,491`
  - `fabric`: `1,124`
- `support_category=unknown`은 바로 오류로 보지 않음
- 이유:
  - 원문에 지지체가 없는 작품이 있음
  - 조각/도자/디지털 작품은 지지체 개념이 없을 수 있음
  - 일부 출처는 재료와 지지체를 분리해서 제공하지 않음

## 8. 해석

- 재료는 1차 규칙만으로 대부분 공통 카테고리화 가능함
- 미분류는 `1,196`건으로 남아 있어 2차 보완 대상임
- 지지체는 결측이 많지만, 이것만으로 학습 제외하면 조각/디지털/복합 작품이 과도하게 빠질 수 있음
- 원본 문자열은 복잡하므로 최종 모델에는 원문 그대로보다 표준 카테고리와 flag를 쓰는 것이 안전함
- 다중 재료는 작품 가격에 의미가 있을 수 있으므로 `mixed_media`와 `medium_match_labels`를 함께 보존해야 함

## 9. 결론

- 채택: `medium_raw` 원본 보존
- 채택: `medium_category`, `support_category` 표준 컬럼 생성
- 채택: 다중 재료는 `mixed_media`로 대표화
- 채택: `medium_match_labels`, `support_match_labels`로 매칭 근거 보존
- 보류: `support_category=unknown`은 제외 사유가 아니라 정보 부족 flag로 관리
- 보완 필요: 미분류 재료 `1,196`건은 상위 원문을 보고 매핑 규칙을 추가 개선

## 10. 다음 작업

- `T4-C5` 중복 정합성 감사 진행
- 이후 `cleaned_v2` 생성 시 재료/지지체 매핑 규칙을 코드로 고정
- 미분류 상위값을 기준으로 재료 매핑 v2 보완
