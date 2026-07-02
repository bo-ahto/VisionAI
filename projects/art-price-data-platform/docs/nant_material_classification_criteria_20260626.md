# NANT 재료(지지체/매체) 분류 기준

작성일: 2026-06-26

## 1. 목적

이 문서는 작품 표준화 이후 학습 snapshot에 들어갈 재료/지지체 기준을 고정한다.

핵심 결정:

- 재료/지지체 학습 포함 여부는 기존 하드코딩 필터가 아니라 DB의 active NANT mapping version으로 판단한다.
- CSV는 초기 seed/import 원본과 감사 기준으로 보존하되, 운영 SoT는 DB의 versioned mapping table이다.
- NANT 분류는 `normalized_artwork_staging` row 생성 중 수행하고, 분류 결과는 같은 row의 `nant_*` 컬럼에 저장한다.
- 학습 제외는 DB mapping row의 `learning_excluded=true` 기준으로 판단한다. 초기 import 시에는 CSV `비고2`가 `학습 제외`로 시작하는 값을 `learning_excluded=true`로 변환한다.
- 제외 row는 raw/interpreted/normalized에는 보존하고, 학습 snapshot/export/model feature 생성에서만 제외한다.

## 2. 기준 원본과 DB SoT

초기 import 원본:

`projects/art-price-data-platform/docs/k-artmarket 1차 데이터 정제 - 실험데이터분류(데이터 수정).csv`

CSV 역할:

| 영역 | 컬럼 | DB 적재 대상 |
|---|---|---|
| NANT 기준 조합 | `재료(지지체)`, `도구(매체)` | `nant_allowed_category` |
| 원천 매핑 | `수집 재료` | `nant_material_mapping.source_material_text` |
| NANT 매핑 결과 | `난트 기준 재료(지지체)`, `난트 기준 도구(매체)` | `nant_support`, `nant_medium`, `nant_category_key` |
| 학습 제외 기준 | `비고2` | `learning_excluded`, `learning_exclusion_reason`, `raw_note2` |

2026-06-26 확인값:

- NANT 기준 support/medium 조합: 95개
- `수집 재료` 매핑 행: 6,049개
- `비고2`가 `학습 제외`로 시작하는 행: 1,369개
- 현재 파일 SHA-256: `d3349cb0be41aa78ecec5a1047b6b17b06dac727e0ac4aa6da2fa0d79c3c02fe`

DB SoT:

| 테이블 | 역할 |
|---|---|
| `nant_mapping_version` | mapping 버전, 상태(`draft`/`active`/`archived`), import hash, 승인 이력 |
| `nant_allowed_category` | 해당 버전에서 허용되는 95개 NANT support/medium 조합 |
| `nant_material_mapping` | 원천/표준화 재료 표현을 NANT support/medium과 학습 제외 여부로 매핑 |
| `normalized_artwork_staging.nant_*` | normalized 작품 row에 active mapping version을 적용한 분류 결과. 학습 제외 여부는 `nant_material_mapping_id`로 mapping row를 조인해 판단 |

## 3. 운영 워크플로우

```text
CSV import 또는 admin draft 생성
  -> nant_mapping_version(status=draft)
  -> nant_allowed_category / nant_material_mapping 적재
  -> validation(95 category, 중복 source_material_text, category key 유효성, exclusion rule)
  -> 데이터 관리자 activate
  -> 이전 active version archived
  -> 새 normalized row부터 active mapping version으로 분류 결과 저장
  -> snapshot은 사용한 mapping_version을 고정
```

운영 원칙:

- active version은 직접 수정하지 않는다.
- 수정은 draft version에서만 가능하다.
- activate는 데이터 관리자 권한이다.
- snapshot/export/model artifact에는 `nant_mapping_version_id`, `version_key`, import SHA-256을 기록한다.
- 과거 snapshot은 당시 고정된 mapping version으로 재현한다.

## 4. 파이프라인 위치

NANT 분류는 작품 표준화 row 생성 중 수행한다.

```text
raw 수집
  -> interpreted staging
  -> active NANT mapping version 조회
  -> price_conversion + artist_key resolve + NANT 재료(지지체/매체) 분류
  -> normalized_artwork_staging INSERT
  -> mapping row 조인으로 학습 제외 여부 판단
  -> snapshot 후보 summary/items
  -> snapshot export/model 학습
```

가격 환산(`price_conversion`)과 NANT 분류는 둘 다 artwork normalizer 내부 계산이다. 둘 다 `normalized_artwork_staging` row INSERT 전에 계산하고, snapshot/export에서는 저장된 값을 복사한다.

## 5. 매핑 규칙

1. 입력값은 표준화된 작품 row의 재료 원문/후보값에서 가져온다.
2. 입력값을 trim, 공백 정규화, 대소문자 정규화한 뒤 active version의 `nant_material_mapping.source_material_text_normalized`와 매칭한다.
3. 매칭된 row의 `nant_support`와 `nant_medium`을 `normalized_artwork_staging`에 저장한다.
4. `nant_category_key = nant_support + '|' + nant_medium`으로 만든다.
5. `nant_category_key`는 같은 version의 `nant_allowed_category`에 존재해야 한다.
6. 매칭된 `nant_material_mapping.material_mapping_id`를 `normalized_artwork_staging.nant_material_mapping_id`에 저장한다.
7. 학습 제외 여부는 작품 row에 복사하지 않고 `nant_material_mapping.learning_excluded` 조인으로 판단한다.

매칭 실패 시 임의로 가장 가까운 재료에 넣지 않는다. `standardization_review_item(review_type=nant_mapping)`에 보류하고, 검수/매핑 확정 전에는 완료 표준화 row와 학습 snapshot 후보에 올리지 않는다.

## 6. 학습 제외 규칙

DB 기준:

```text
nant_material_mapping.learning_excluded = true
```

CSV import 변환 규칙:

```text
TRIM(비고2) LIKE '학습 제외%' -> learning_excluded=true
```

예:

- `학습 제외`
- `학습 제외(입체)`
- `학습 제외(고미술)`
- `학습 제외(판단 불가)`

처리:

| 상태 | snapshot 처리 | 보존 여부 |
|---|---|---|
| NANT 매핑 성공, `learning_excluded=false` | 다른 품질 조건을 통과하면 포함 후보 | 보존 |
| NANT 매핑 성공, `learning_excluded=true` | `include_status=excluded`, `exclude_reason=nant_learning_excluded` | 보존 |
| NANT 매핑 실패 | `standardization_review_item(review_type=nant_mapping)`에 보류. 검수/매핑 확정 전 snapshot 후보 제외 | 보존 |

이 규칙은 재료/지지체/작품 유형에 대한 기존 하드코딩 학습 필터를 대체한다. 단, 아래 필터는 별개로 유지한다.

- 가격 없음 또는 가격 환산 실패
- 가로/세로 cm 등 필수 크기 누락
- suppression/do-not-train
- 작가 identity 미확정으로 Warm 학습에 사용할 수 없는 row
- 운영자 수동 제외

## 7. 어드민 관리 범위

어드민은 NANT mapping을 DB에서 관리한다.

필수 화면/API:

- mapping version 목록과 active version 확인
- CSV import로 draft version 생성
- draft mapping row 검색/추가/수정/삭제
- unmapped 재료 목록 조회 후 draft mapping에 추가
- `learning_excluded`와 제외 사유 수정
- validation 결과 확인
- 데이터 관리자 activate
- activation 후 해당 version을 사용한 snapshot/model 영향 범위 조회

권한:

| 액션 | 최소 권한 |
|---|---|
| version/row 조회 | 운영 담당자 |
| CSV import, draft row 추가/수정/삭제 | 데이터 분석가 |
| active version 전환 | 데이터 관리자 |

## 8. 구현 산출물

Phase 0/1에서 아래 산출물을 만든다.

- NANT CSV import/validator
- `nant_mapping_version`, `nant_allowed_category`, `nant_material_mapping` DDL
- `normalized_artwork_staging`의 NANT 결과 컬럼과 인덱스
- active version 단일성 제약
- draft-only edit 제약
- snapshot 후보 query에서 NANT 제외 사유 반영
- admin NANT mapping API와 fixture
- fixture test:
  - 기준 조합 95개 검증
  - CSV `비고2 LIKE '학습 제외%'` -> DB `learning_excluded=true` 변환 검증
  - unmapped row 보류/제외 검증
  - active version 직접 수정 금지 검증
  - 기존 하드코딩 재료/지지체 필터 미사용 검증

## 9. 운영 원칙

- CSV 파일을 다시 import하면 새 draft version을 만든다. 기존 active version을 덮어쓰지 않는다.
- DB row 수정은 draft version에서만 한다.
- 같은 `source_cutoff_at`, 같은 `rules_version`, 같은 `nant_mapping_version_id`이면 같은 snapshot 후보가 재현되어야 한다.
- mapping DB는 학습 필터의 단일 기준이므로 코드 안에 별도 재료 제외 목록을 두지 않는다.
- `normalized_artwork_staging`에는 `learning_excluded`/`learning_exclusion_reason`을 중복 저장하지 않는다. snapshot 생성 시점에 mapping row를 조인해 `exclude_reason`을 고정한다.
- 원천 row는 삭제하지 않는다. 제외 사유는 snapshot item에 고정하고, 학습 제외 기준은 mapping row에 남긴다.
