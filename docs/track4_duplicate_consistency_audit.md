# Track 4 중복 정합성 감사

- 목적: 동일 작품 중복 후보를 원본 ID, URL, 이미지, 의미 기반 기준으로 분리해서 점검
- 입력: `data/track4_primary_market_raw_collected.csv`
- 감사 CSV: `data/track4_duplicate_consistency_audit.csv`
- 전체 rows: `54,842`
- 중복/검토 flag 없음: `51,449`
- 중복/검토 flag 있음: `3,393`

## 1. 출처별 요약

| 출처 | rows | flag 없음 | flag 있음 | ID 중복 | 같은 출처 의미 중복 | 출처 간 엄격 중복 | 출처 간 느슨한 후보 |
|---|---:|---:|---:|---:|---:|---:|---:|
| artsy | `30,046` | `28,723` | `1,323` | `0` | `1,020` | `4` | `235` |
| artue | `2,783` | `2,516` | `267` | `0` | `108` | `4` | `169` |
| gallery_primary | `292` | `292` | `0` | `0` | `0` | `0` | `0` |
| saatchi | `21,721` | `19,918` | `1,803` | `0` | `1,773` | `0` | `35` |

## 2. 중복 그룹 수

| 기준 | 그룹 수 | 해석 |
|---|---:|---|
| `same_source_id_groups` | `0` | 같은 출처 안에서 원본 작품 ID가 같은 그룹 |
| `same_source_url_groups` | `0` | 같은 출처 안에서 작품 URL이 같은 그룹 |
| `same_source_image_groups` | `0` | 같은 출처 안에서 이미지 URL이 같은 그룹 |
| `same_source_semantic_groups` | `954` | 같은 출처 안에서 작가+제목+가격+크기가 같은 그룹 |
| `cross_source_semantic_groups` | `4` | 출처가 달라도 작가+제목+가격+크기가 같은 그룹 |
| `loose_cross_source_groups` | `180` | 출처가 달라도 작가+제목+크기가 같은 후보 그룹 |

## 3. 이슈 카운트

| 이슈 | 건수 | 해석 |
|---|---:|---|
| `same_source_semantic_duplicate` | `2,901` | 같은 출처 안에서 작가+제목+가격+크기 중복 |
| `loose_cross_source_candidate` | `439` | 출처 간 작가+제목+크기 기준 중복 후보 |
| `missing_title_key` | `70` | 제목 key 없음 |
| `cross_source_semantic_duplicate` | `8` | 출처 간 작가+제목+가격+크기 중복 |

## 4. 현재 판단

- 같은 출처의 원본 ID/URL 중복은 실제 중복 가능성이 높음
- 이미지 URL 중복은 같은 작품일 수도 있지만, 대표 이미지 재사용 가능성이 있어 수동 검토가 필요함
- 작가+제목+가격+크기가 같은 경우는 학습에서 가중치가 중복될 수 있으므로 flag로 관리해야 함
- 출처 간 중복은 삭제보다 대표 row 선택 정책이 필요함
- 대표 row 선택에 source 자체를 모델 피처로 쓰지는 않음
- 가격이나 크기가 조금 다른 출처 간 후보는 별도 검토 후 하나만 대표 row로 선택해야 함

## 5. 제안 클렌징 규칙

- 원본 ID가 같은 같은 출처 중복은 대표 1건만 학습 후보로 유지
- URL이 같은 같은 출처 중복도 대표 1건만 학습 후보로 유지
- 같은 출처의 의미 중복은 가격/크기/이미지 샘플 확인 후 대표 1건만 유지
- 출처 간 엄격 중복은 가격/크기/URL/원본 완성도 기준으로 대표 row를 선택
- 출처 간 느슨한 후보는 자동 삭제하지 않고 `duplicate_review_candidate`로 관리
- 중복 제외 row는 삭제하지 않고 `is_training_candidate=false`, `exclude_reason=duplicate_*`로 남김

## 6. 다음 단계

- 중복 대표 row 선택 우선순위 정의
- 이후 출처 편향 점검 `T4-C6` 감사 진행
- 단, source는 모델 입력 피처로 사용하지 않음
