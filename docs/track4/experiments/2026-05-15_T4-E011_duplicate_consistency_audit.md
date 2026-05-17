# T4-E011 중복 정합성 감사

- 날짜: 2026-05-15
- 연결 가설: T4-C5
- 상태: 완료
- 목적: Track 4 원본 보존 통합본에서 동일 작품 중복 후보를 찾아 학습 데이터 편향 가능성을 점검

## 1. 사용 데이터

- 입력 데이터: `data/track4_primary_market_raw_collected.csv`
- 보조 입력:
  - `data/track4_price_consistency_audit.csv`
  - `data/track4_size_consistency_audit.csv`
  - `data/track4_artist_consistency_audit.csv`
- 입력 행 수: `54,842`
- 감사 결과 CSV: `data/track4_duplicate_consistency_audit.csv`
- 감사 요약 JSON: `data/track4_duplicate_consistency_audit_summary.json`
- 요약 문서: `docs/track4/audits/duplicate_consistency_audit.md`

## 2. 실행 방법

- 스크립트: `scripts/track4/audit_duplicate_consistency.py`
- 원본 작품 ID 중복 확인
- 작품 URL 중복 확인
- 이미지 URL 중복 확인
- 같은 출처 내부 의미 중복 확인
  - source + artist_key + title_key + price bucket + width/height/depth bucket
- 출처 간 엄격 중복 확인
  - artist_key + title_key + price bucket + width/height/depth bucket
  - 단, 실제로 서로 다른 출처가 포함된 경우만 인정
- 출처 간 느슨한 중복 후보 확인
  - artist_key + title_key + width/height bucket
  - 가격 차이가 있거나 가격이 없는 경우까지 후보로 봄

## 3. 주요 결과

- 전체 행: `54,842`
- 중복/검토 flag 없음: `51,449`
- 중복/검토 flag 있음: `3,393`
- 같은 출처 내부 의미 중복 row: `2,901`
- 출처 간 엄격 중복 row: `8`
- 출처 간 느슨한 중복 후보 row: `439`
- 제목 key 없음: `70`

## 4. 중복 그룹 수

- 같은 출처 원본 ID 중복 그룹: `0`
- 같은 출처 URL 중복 그룹: `0`
- 같은 출처 이미지 URL 중복 그룹: `0`
- 같은 출처 의미 중복 그룹: `954`
- 출처 간 엄격 중복 그룹: `4`
- 출처 간 느슨한 후보 그룹: `180`

## 5. 출처별 결과

| 출처 | 전체 | flag 없음 | flag 있음 | 같은 출처 의미 중복 | 출처 간 엄격 중복 | 출처 간 느슨한 후보 |
|---|---:|---:|---:|---:|---:|---:|
| Artsy | `30,046` | `28,723` | `1,323` | `1,020` | `4` | `235` |
| Artue | `2,783` | `2,516` | `267` | `108` | `4` | `169` |
| Gallery primary | `292` | `292` | `0` | `0` | `0` | `0` |
| Saatchi | `21,721` | `19,918` | `1,803` | `1,773` | `0` | `35` |

## 6. 해석

- 원본 ID/URL 기준의 명확한 중복은 발견되지 않음
- 같은 출처 안에서 작가+제목+가격+크기가 같은 의미 중복은 존재함
- 출처 간 완전히 같은 조건의 중복은 매우 적음
- 출처 간 느슨한 후보는 가격 차이, 가격 결측, 크기 표기 차이가 있을 수 있어 자동 삭제하면 위험함
- 중복 row를 그대로 학습하면 특정 작품이나 특정 작가가 과대표집될 수 있음

## 7. 결론

- 채택: 같은 출처 내부 의미 중복은 학습 후보에서 대표 1건만 남기는 방향으로 관리
- 채택: 출처 간 엄격 중복은 대표 row 선택 우선순위를 정한 뒤 1건만 유지
- 보류: 출처 간 느슨한 후보는 자동 제외하지 않고 `duplicate_review_candidate`로 관리
- 보류: 이미지 URL 중복은 대표 이미지 재사용 가능성이 있어 단독 기준으로 제외하지 않음
- 유지: 원본 row는 삭제하지 않고 `is_training_candidate=false`, `exclude_reason=duplicate_*` 방식으로 남김

## 8. 대표 row 선택 우선순위 제안

- 1순위: 가격이 있는 row
- 2순위: width/height/depth가 안정적으로 있는 row
- 3순위: 작품 URL이 있는 row
- 4순위: 작가명/제목이 더 구체적인 row
- 5순위: source 자체가 아니라 가격/크기/URL/원본 완성도 기준으로 결정

## 9. 다음 작업

- `T4-C6` 출처 편향 점검 진행
- 단, source는 모델 입력 피처로 사용하지 않음
- 이후 `cleaned_v2` 생성 시 중복 flag와 대표 row 선택 규칙 반영
