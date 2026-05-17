# Track 4 재료/지지체 정합성 감사

- 목적: 출처별로 다른 재료 표현을 표준 재료/지지체 카테고리로 묶을 수 있는지 점검
- 입력: `data/track4_primary_market_raw_collected.csv`
- 감사 CSV: `data/track4_medium_support_consistency_audit.csv`
- 전체 rows: `54,842`
- 정상 rows: `53,646`
- 이슈 rows: `1,196`

## 1. 출처별 요약

| 출처 | rows | 정상 | 이슈 | 재료 미분류 | 지지체 미분류 | 다중 재료 | 다중 지지체 |
|---|---:|---:|---:|---:|---:|---:|---:|
| artsy | `30,046` | `29,253` | `793` | `793` | `5,145` | `9,457` | `2,051` |
| artue | `2,783` | `2,698` | `85` | `85` | `638` | `726` | `200` |
| gallery_primary | `292` | `291` | `1` | `1` | `24` | `159` | `53` |
| saatchi | `21,721` | `21,404` | `317` | `317` | `479` | `6,581` | `34` |

## 2. 표준 재료 카테고리 상위

- mixed_media `19,491`, acrylic `14,127`, oil `13,662`, painting_material `1,929`, sculpture_material `1,248`, other `1,142`, ink `1,008`, ceramic `615`, print `456`, gouache `345`, pencil `225`, textile `157`, digital `146`, charcoal `90`, photo `57`, unknown `54`, pastel `51`, collage `39`

## 3. 표준 지지체 카테고리 상위

- canvas `32,502`, paper `9,752`, unknown `6,286`, panel `1,833`, linen `1,491`, fabric `1,124`, wood `797`, metal `656`, glass `401`

## 4. 이슈 카운트

| 이슈 | 건수 | 해석 |
|---|---:|---|
| `medium_unmapped` | `1,196` | 현재 규칙으로 재료 대분류를 정하지 못함 |
| `missing_medium_raw` | `28` | 원본 재료 문자열 없음 |
| `placeholder_medium_raw` | `26` | `-` 같은 자리표시값 |

## 5. 현재 판단

- 원본 재료 문자열은 반드시 `medium_raw`로 보존함
- 모델 피처는 원본 문자열을 그대로 쓰기보다 `medium_category`, `support_category`로 단순화하는 것이 안전함
- `Oil on canvas`, `캔버스에 유채`, `oil on Canvas`는 모두 `medium_category=oil`, `support_category=canvas`로 묶을 수 있음
- `Acrylic on canvas`, `아크릴`, `Airbrushed acrylics on canvas`는 `medium_category=acrylic`으로 묶을 수 있음
- `Mixed media`, `Oil and acrylic`, 재료 3개 이상 조합은 `mixed_media`로 묶는 것이 1차 기준으로 적절함
- 지지체가 없는 조각/도자/디지털 작품은 `support_category=unknown`이 오류가 아닐 수 있음
- Saatchi의 기존 category 컬럼은 참고용으로만 쓰고, 전체 출처 공통 규칙을 우선함

## 6. 제안 매칭 규칙

- 재료 표준 카테고리
- `oil`, `acrylic`, `watercolor`, `ink`, `gouache`, `charcoal`, `pencil`, `pastel`, `print`, `photo`, `digital`, `ceramic`, `sculpture_material`, `textile`, `collage`, `mixed_media`, `other`, `unknown`
- 지지체 표준 카테고리
- `canvas`, `linen`, `paper`, `panel`, `glass`, `wood`, `metal`, `fabric`, `unknown`
- 매칭 방식
- 원본 문자열을 소문자/공백 정리함
- 재료 키워드와 지지체 키워드를 따로 찾음
- 재료가 여러 개이거나 `mixed media`가 있으면 `mixed_media`로 우선 묶음
- 지지체는 첫 번째 명확한 지지체를 대표값으로 둠
- 미분류 원문 상위값을 보고 규칙을 반복 보완함

## 7. 클렌징 규칙 제안

- `medium_raw`가 없거나 `-`이면 재료 결측 flag를 남김
- `medium_category=other/unknown`은 기본 학습에서 제외하지 않고 미분류 flag로 관리
- `support_category=unknown`은 조각/도자/디지털 작품일 수 있으므로 제외하지 않음
- 다중 재료는 `mixed_media`로 대표화하되 원본 매칭 목록을 보존함
- 다중 지지체는 대표 support와 전체 support match 목록을 함께 보존함

## 8. 다음 단계

- 미분류 상위 원문을 확인해 매핑 규칙 2차 보완
- 이후 중복 정합성 `T4-C5` 진행
