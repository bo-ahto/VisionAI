# artist_key 및 작가명 표준화 흐름

작성일: 2026-06-24

목적:

- 작가명 한글화/영문화, 동명이인 처리, `artist_key` 생성 과정을 한 문서에서 이해할 수 있게 정리한다.
- 원천값, 자동 변환값, 서비스 표시값, 최종 작가 키를 섞지 않도록 기준을 명확히 한다.
- 운영자가 어떤 단계에서 무엇을 검수해야 하는지 확인할 수 있게 한다.

관련 문서:

- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [4개 원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
- [4개 원천 사이트 주기 수집 및 MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)

## 문서 세트에서의 위치

데이터 수집 문서는 아래 순서로 읽는 것을 기준으로 한다.

1. [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
   - 수집 실행, 실패 처리, 운영자 알림, snapshot 반영 기준을 설명한다.
2. [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
   - 작가명 한글화/영문화, alias, 동명이인, 최종 artist_key 생성 기준을 설명한다.
3. [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
   - 각 원천에서 어떤 작품/작가 값을 수집하고, 어떤 공통 컬럼으로 옮기는지 설명한다.
4. [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
   - DB 구조, job 구조, migration, 테스트 기준을 설명한다.

이 문서는 네 문서 중 작가명과 작가 키 판단 기준을 담당한다. 다른 문서에서는 핵심 요약만 남기고, 상세한 판단 흐름은 이 문서를 기준으로 한다.

## 1. 전체 흐름

```text
source_artist_raw
  - 원천 사이트에서 받은 작가 원문 보존
        |
        v
source_artist_interpreted_staging
  - 원천 문자열 분해
  - 한글명/영문명/국적/생년/활동지 후보 생성
  - 전시/갤러리 원문은 보존하되 artist_key 자동 판단 근거로 쓰지 않음
        |
        v
normalized_artist_staging
  - 원천값과 후보값을 공통 컬럼으로 정리
  - 원천 이름과 자동 변환 이름은 분리
        |
        v
artist_name_alias
  - 한글명/영문명 alias 생성
  - 서비스 표시명 후보 생성
  - 같은 alias 또는 승인 alias에 연결된 기존 artist_key 후보 확인
        |
        +-- 기존 후보 없음
        |     -> 신규 artist_key 후보
        |     -> artist_identity_candidate 생성 안 함
        |
        +-- 기존 후보 있음
              |
              v
artist_identity_candidate
  - 기존 artist_key 연결 후보와만 비교
  - 같은 alias가 여러 기존 후보에 걸릴 때 동명이인 처리
        |
        +-- 기존 artist_key와 자동 확정 가능
        |     -> 기존 artist_key에 연결
        |
        +-- 기존 후보와 같은 작가로 볼 수 없음
        |     -> 해당 후보와의 연결만 match_rejected
        |     -> 다른 후보 비교 또는 신규 artist_key 후보
        |
        +-- 판단 근거 부족 또는 동명이인 가능성 있음
              -> needs_review
        |
        v
artist_identity
  - 기존 artist_key 연결 확정
  - 또는 신규 artist_key 생성 확정
  - 승인/반려/자동 확정 이력 보존
```

## 2. 이름 컬럼 분리 기준

`artist_name_ko`와 `artist_name_en`처럼 하나의 컬럼에 원천값과 변환값을 섞지 않는다. 이름은 아래처럼 역할별로 분리한다.

| 컬럼 | 의미 | 자동 변환값 저장 여부 |
|---|---|---|
| `artist_name_raw` | 원천 작가명 원문 | 저장하지 않음. 원문 그대로 |
| `artist_name_ko_source` | 원천에서 직접 받은 한글명 또는 원천 문자열에서 명확히 분리한 한글명 | 저장하지 않음 |
| `artist_name_en_source` | 원천에서 직접 받은 영문명 또는 원천 문자열에서 명확히 분리한 영문명 | 저장하지 않음 |
| `artist_name_ko_candidate` | 자동 한글화/표기 변환 후보 | 저장 가능 |
| `artist_name_en_candidate` | 자동 영문화/로마자 표기 후보 | 저장 가능 |
| `artist_name_ko_display` | 서비스 표시용 한글명 | 저장 가능 |
| `artist_name_en_display` | 서비스 표시용 영문명 | 저장 가능 |
| `artist_name_display_source` | 표시명이 어디서 왔는지 | `source`, `parsed`, `alias_approved`, `manual`, `auto_transliteration`, `auto_translation` |
| `artist_name_review_status` | 이름 보강 검수 상태 | `auto_approved`, `approved`, `needs_review`, `match_rejected` |

핵심 원칙:

- `*_source`에는 자동 변환값을 넣지 않는다.
- 자동 변환값은 `*_candidate` 또는 `*_display`에만 넣는다.
- 서비스는 `artist_name_ko_display`를 우선 사용한다.
- `artist_key` 확정은 이름 하나만으로 하지 않는다.

## 3. artist_name_alias 역할

`alias`는 같은 작가를 가리킬 수 있는 다른 이름 표기다.

예:

```text
김환기
Kim Whanki
Whanki Kim
Kim Hwan-ki
김환기 | Kim Whanki
```

`artist_name_alias`는 이 표기들을 모아 서비스 표시와 작가 매칭 후보 생성에 사용한다.

| 컬럼 | 의미 |
|---|---|
| `artist_key` | 이미 확정된 작가라면 연결되는 최종 작가 키 |
| `normalized_artist_id` | 표준화 작가 row |
| `alias_name` | 이름 별칭/다른 표기 |
| `alias_language` | `ko`, `en`, `other`, `unknown` |
| `alias_type` | `source`, `parsed`, `manual`, `transliteration_candidate`, `translation_candidate` |
| `display_target` | `ko_display`, `en_display`, `matching_only` |
| `is_primary_display` | 서비스 대표 표시명 여부 |
| `confidence` | 자동 분리/변환 신뢰도 |
| `ambiguity_status` | `unique`, `ambiguous`, `needs_review` |
| `conflict_group_id` | 같은 alias가 여러 작가 후보에 걸릴 때의 충돌 그룹 ID |
| `review_status` | `auto_approved`, `approved`, `needs_review`, `match_rejected` |
| `approved_by` | 수동 승인 관리자 ID |
| `approved_at` | 수동 승인 시각 |

## 4. 이름 보강 처리

```text
normalized_artist_staging
        |
        v
원천 이름 확인
        |
        +-- 한글명/영문명이 모두 있음
        |     -> source alias 생성
        |
        +-- 한 문자열에 한글/영문이 함께 있음
        |     -> parsed alias 생성
        |
        +-- 한글명만 있음
        |     -> 영문 후보 생성, needs_review
        |
        +-- 영문명만 있음
        |     -> 한글 표시 후보 생성, needs_review
        |
        v
artist_name_alias 저장
```

처리 기준:

| 상황 | 처리 |
|---|---|
| 원천에 한글명/영문명이 모두 있음 | `source` alias로 저장 |
| `한글 | English`처럼 둘 다 있음 | `parsed` alias로 분리 |
| 한글명만 있음 | `artist_name_en_candidate` 생성 |
| 영문명만 있음 | `artist_name_ko_candidate`, `artist_name_ko_display` 생성 가능 |
| 승인 alias와 일치 | 확정 alias로 승격 가능 |
| 자동 변환만 있음 | 표시/후보에는 사용 가능하나 artist_key 단독 확정 금지 |

## 5. 동명이인 처리

동명이인 처리는 모든 작가 row에 적용하지 않는다. 같은 `alias_name` 또는 승인 alias가 기존 `artist_key` 후보와 겹칠 때만 이 로직에 들어간다.

동명이인은 같은 `alias_name`이 여러 작가 후보에 걸리는 상황이다. 기존 후보가 없고 원천 ID도 처음 등장한 작가는 동명이인 처리 없이 신규 `artist_key` 후보로 둔다.

아래 분기 기준은 [6.1 자동 확정/검수/반려 기준](#61-자동-확정검수반려-기준)을 따른다.

```text
[신규 작가 row]
        |
        v
[같은 source + artist_source_id가 이미 artist_key에 연결되어 있는가?]
        |
        +-- YES
        |     -> 기존 artist_key에 바로 연결
        |     -> 동명이인 처리 진입 안 함
        |
        +-- NO
              |
              v
[같은 alias 또는 승인 alias에 연결된 기존 artist_key 후보가 있는가?]
        |
        +-- NO
        |     -> 신규 artist_key 후보
        |     -> 동명이인 처리 진입 안 함
        |
        +-- YES
              |
              v
동명이인 가능성 검토 시작
        |
        v
alias 기반 1차 후보 artist_key 목록 조회
  - 같은 alias 또는 승인 alias에 연결된 기존 artist_key
  - 같은 원천 ID로 이미 연결된 artist_key
        |
        v
각 후보 artist_key와 보조 메타 비교
  - 생년
  - 국적
  - 활동지
  - 작품군/가격대
        |
        +-- 자동 확정 조건 충족
        |   (6.1의 "자동 확정 가능" 기준)
        |     -> 해당 후보 artist_key에 연결
        |     -> review_status=auto_approved 기록
        |     -> auto_approved_at, auto_approved_rule_version 저장
        |
        +-- 강한 충돌 조건 충족
        |   (6.1의 "강한 충돌 조건" 기준)
        |   (해당 후보와 같은 작가로 볼 수 없는 경우)
        |     -> 해당 후보 artist_key와의 연결만 match_rejected로 기록
        |     -> 원천 row는 유지
        |     -> 다른 후보 비교 또는 신규 artist_key 후보로 이동
        |
        +-- 자동 확정/반려 기준 모두 미달
            (6.1의 "수동 검수 필요" 기준)
              -> artist_key에 바로 연결하지 않음
              -> review_status=needs_review 기록
              -> 운영자 검수 큐에서 승인/반려/신규 생성 판단
```

동명이인 상태 기준:

| 상태 | 의미 | 처리 |
|---|---|---|
| `unique` | 같은 `alias_name`으로 연결 가능한 작가 후보가 1개뿐임 | 고신뢰 생년과 충돌 조건 확인 후 자동 확정 검토 가능 |
| `ambiguous` | alias가 여러 작가 후보에 걸림 | 자동 병합 금지 |
| `needs_review` | 자동 확정도 반려도 할 수 없는 상태 | 원천 row는 유지하고 artist_key에 바로 연결하지 않음. 운영자 검수 큐에서 승인/반려/신규 생성 판단 |
| `match_rejected` | 특정 후보 artist_key와는 같은 작가가 아님 | 해당 후보와의 연결만 금지. 원천 row는 유지하고 다른 후보 비교 또는 신규 artist_key 후보로 이동 |

중요 원칙:

- 같은 이름이라는 이유만으로 병합하지 않는다.
- 같은 alias가 여러 artist_key 후보에 걸리면 `ambiguity_status=ambiguous`로 둔다.
- 운영자가 승인한 후보만 `artist_key`에 연결한다.
- 잘못 병합하는 것보다 일시적으로 분리해 두는 편이 안전하다.

## 6. artist_key 생성 기준

`artist_key`는 서비스와 모델에서 사용하는 최종 작가 키다. 원천 사이트의 `artist_source_id`, `artist_slug`, `artist_idx`와 다르다.

```text
artist_identity_candidate
        |
        v
1순위: 같은 원천의 같은 artist_source_id 확인
        |
        +-- 이미 연결된 artist_key 있음
        |     -> 해당 artist_key에 바로 연결
        |
        +-- 연결된 artist_key 없음
              |
              v
2순위: 같은 alias 또는 승인 alias에 연결된 기존 artist_key 후보 확인
        |
        +-- 기존 후보 없음
        |     -> 신규 artist_key 후보
        |     -> 동명이인 처리 진입 안 함
        |
        +-- 기존 후보 있음
              |
              v
3순위: 후보 artist_key와 병합 조건 확인
        |
        +-- 이름 alias + 고신뢰 생년 일치 + 충돌 없음
        |     -> 기존 artist_key 연결
        |     -> review_status=auto_approved 기록
        |
        +-- 동명이인/메타 부족
        |     -> artist_key에 바로 연결하지 않음
        |     -> review_status=needs_review
        |     -> 운영자 검수 큐로 이동
        |
        +-- 강한 충돌 기준 충족
              -> 해당 후보 artist_key와의 연결만 match_rejected로 기록
              -> 원천 row는 유지
              -> 다른 후보 비교 또는 신규 artist_key 후보로 이동
```

### 6.1 자동 확정/검수/반려 기준

아래 기준은 5장의 동명이인 처리 순서도에서 쓰는 판정 기준이다. 먼저 순서도대로 판단하고, 각 분기의 상세 조건은 바로 아래 목록을 따른다.

```text
[신규 작가 row]
        |
        v
[같은 source + artist_source_id가 이미 artist_key에 연결되어 있는가?]
        |
        +-- YES
        |     -> 기존 artist_key에 바로 연결
        |     -> 종료
        |
        +-- NO
              |
              v
[같은 alias 또는 승인 alias에 연결된 기존 artist_key 후보가 있는가?]
        |
        +-- NO
        |     -> 신규 artist_key 후보
        |     -> 동명이인 처리 진입 안 함
        |
        +-- YES
              |
              v
[alias_exact 또는 alias_approved 후보인가?]
        |
        +-- NO
        |     -> fuzzy 후보만 있음
        |     -> needs_review
        |     -> 운영자 검수 큐
        |
        +-- YES
              |
              v
[강한 충돌 조건이 있는가?]
  - 해당 후보와 같은 작가로 볼 수 없는 경우
        |
        +-- YES
        |     -> 해당 후보 artist_key와의 연결만 match_rejected
        |     -> 원천 row는 유지
        |     -> 다른 후보 비교 또는 신규 artist_key 후보로 이동
        |
        +-- NO
              |
              v
[같은 alias가 2개 이상의 artist_key 후보에 걸리는가?]
        |
        +-- YES
        |     -> ambiguous
        |     -> needs_review
        |
        +-- NO
              |
              v
[서로 다른 원천 후보인가?]
        |
        +-- NO
        |     -> 같은 원천 ID 기준으로 처리
        |
        +-- YES
              |
              v
[양쪽 모두 고신뢰 생년이 있고 같은 연도인가?]
        |
        +-- YES
        |     -> 해당 후보 artist_key에 연결
        |     -> review_status=auto_approved
        |     -> auto_approved_at, auto_approved_rule_version 저장
        |
        +-- NO
              -> artist_key에 바로 연결하지 않음
              -> review_status=needs_review
              -> 운영자 검수 큐
```

alias 일치 분류(`alias_match_type`, `artist_identity_candidate`에 저장)는 다음과 같이 정의한다.

- `alias_exact`: 후보의 정규화 이름이 기존 `artist_key`의 alias와 정확히 일치(대소문자/공백/기호 정규화 후).
- `alias_approved`: 일치한 alias가 `artist_name_alias.review_status=approved`인 승인 alias.
- `alias_fuzzy_only`: 정확 일치는 없고 편집거리/부분 일치 같은 fuzzy 일치만 있음.

**자동 확정 가능 기준**

5장의 `자동 확정 조건 충족` 분기는 이 기준을 따른다.

> MVP 범위: MVP에서는 cross-source(서로 다른 원천 간) 자동 확정을 비활성화하고 같은 `source + artist_source_id` 자동 연결만 운영한다. 아래 서로 다른 원천 간 자동 확정 기준은 비교 가능한 작가 메타가 충분히 확보된 post-MVP에서만 적용한다. MVP 단계의 cross-source 후보는 전부 `needs_review`로 두고 수동 검수 큐로 보낸다.

- `alias_exact` 또는 `alias_approved` 중 하나를 만족한다.
- 서로 다른 원천 후보라면 양쪽 모두 `birth_year_confidence=high`인 생년이 있고 같은 연도다.
- 같은 alias가 2개 이상의 `artist_key` 후보에 걸린 `ambiguous` 상태가 아니다.
- 강한 충돌 조건이 없다.
- `conflict_reasons_json`이 비어 있다.

**수동 검수 필요 기준**

5장의 `자동 확정/반려 기준 모두 미달` 분기는 이 기준을 따른다.

- 기존 `artist_key` 연결 후보가 있고 alias는 일치하지만 양쪽 모두에서 고신뢰 생년을 확인할 수 없다.
- 기존 `artist_key` 연결 후보가 있고 fuzzy alias만 있다.
- 생년이 없고 국적/활동지 같은 참고 메타만 있다.
- 같은 alias가 2개 이상의 `artist_key` 후보에 걸린다.
- 국적이 서로 다르지만 생년 충돌처럼 강한 충돌까지는 아니다.
- 한글명은 같지만 영문명이 다르다. 표기 변형일 수도, 다른 인물일 수도 있어 자동 확정하지 않는다.
- 원천 프로필 URL이 같은 원천 안에서 서로 다른 인물을 가리키는 것으로 보인다.
- 같은 이름인데 dominant medium 분류가 다르고, 양쪽 모두 가격 row가 5건 이상이며 같은 통화 기준 가격 중앙값 차이가 2.0 log 이상이다. 자동 반려가 아니라 검수 경고로 둔다. MVP에서는 참고 경고로만 두고 자동/필수 검수 조건에서는 제외한다.

`needs_review`는 반려가 아니다. 원천 row는 유지하고 운영자 검수 큐에서 승인, 반려, 신규 `artist_key` 생성 여부를 판단한다.

**강한 충돌 조건 기준**

5장의 `강한 충돌 조건 충족` 분기는 이 기준을 따른다.

- 양쪽 모두 고신뢰 생년이 있는데 연도가 다르다.
- 같은 alias가 이미 다른 `artist_key`에 `approved`로 연결되어 있다.
- 같은 원천에서 같은 `artist_source_id`가 서로 다른 `artist_key`에 승인되어 있다.
- 운영자가 후보 비교 후 같은 작가가 아니라고 반려했다.

`match_rejected`는 데이터 삭제나 격리가 아니다. 원천 row는 유지하고, 다른 후보가 있으면 계속 비교한다. 맞는 후보가 없으면 신규 `artist_key` 후보 또는 `needs_review`로 이동한다.

**신규 artist_key 후보 기준**

- `source + artist_source_id`가 있고, 해당 조합에 연결된 기존 `artist_key`가 없고, 강한 충돌 조건이 없다.
- `artist_source_id`가 없더라도 `alias_exact` 또는 `alias_approved`가 있고, 기존 `artist_key` 후보가 0개이며, 강한 충돌 조건이 없다.

이 경우도 바로 최종 확정하지 않고 신규 후보로 생성한 뒤 운영자 확인 대상에 둔다. 신규 후보는 `artist_identity_candidate`를 거치지 않고 `artist_identity`에 `identity_status=needs_review`, `created_by=auto_new_candidate`로 저장해 운영자 확인 큐에 노출한다(저장 위치 정의는 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) 5.10/5.11).

**보조 메타 사용 원칙**

고신뢰 생년은 교차 원천 자동 확정의 핵심 보조 근거다. 고신뢰 생년은 구조화된 생년 필드에서 왔거나, `born`, `born in`, `b.`, `출생`, `년생`처럼 출생 문맥에서 추출된 값이어야 한다. 단순한 4자리 연도는 전시 연도나 수상 연도일 수 있으므로 고신뢰 생년으로 보지 않는다.

국적은 충돌 경고로만 쓴다. 한국 작가 데이터에서는 같은 국적이 많아 같은 작가라는 긍정 근거로 쓰기 어렵다. 활동지는 원천별 의미가 달라 자동 점수로 쓰지 않고 운영자 검수 화면에만 노출한다. 작가 URL은 원천 추적용으로 보존하지만, 서로 다른 원천에서는 URL이 같을 수 없으므로 cross-source 자동 확정 근거로 쓰지 않는다.

**현재 수집 데이터 점검 결과**

| 원천쌍 | 정규화 이름이 같은 후보쌍 | 양쪽 생년 비교 가능 | 양쪽 국적 비교 가능 | 양쪽 활동지 비교 가능 | 운영 판단 |
|---|---:|---:|---:|---:|---|
| Artsy - Print Bakery | 66 | 18 | 0 | 0 | 생년 외 자동 근거 부족 |
| Artsy - Saatchi | 37 | 29 | 37 | 0 | 국적은 대부분 한국 계열이라 보조 구분력 낮음. Saatchi 생년은 자유 텍스트에서 잘못 추출될 수 있어 검수 필요 |
| Art1 - Artsy | 6 | 0 | 0 | 0 | 자동 병합 근거 없음 |
| Art1 - Saatchi | 4 | 0 | 0 | 0 | 자동 병합 근거 없음 |
| Print Bakery - Saatchi | 3 | 0 | 0 | 0 | 자동 병합 근거 없음 |

이 표는 현재 수집 산출물 기준 점검 결과다. 크롤러나 파서가 바뀌어 작가 메타 보유율이 달라지면 같은 집계를 다시 산출하고, 자동 확정 기준을 재검토한다.

수동 승인 시 기록:

| 컬럼 | 의미 |
|---|---|
| `approved_by` | 승인 관리자 ID |
| `approved_at` | 승인 시각 |
| `approval_note` | 승인 사유 |
| `match_evidence_json` | 승인 근거 |

## 7. 운영 화면에서 봐야 할 항목

운영자는 아래 큐를 분리해서 봐야 한다.

| 큐 | 확인 대상 | 주요 조치 |
|---|---|---|
| 이름 alias 큐 | 한글명/영문명 후보, 자동 변환 후보 | 표시명 승인/수정/반려 |
| 동명이인 큐 | 같은 alias가 여러 artist_key 후보에 걸린 경우 | 후보 비교 후 승인/반려 |
| artist identity 큐 | 동명이인 가능성이 있거나 기존 artist_key 연결 후보가 있는 작가 row | 기존 artist_key 연결 승인, 신규 artist_key 생성, 보류, 반려 |

운영 화면 필수 표시:

- 원천 사이트
- 원천 작가 ID/URL
- 원천 작가명
- 한글 source 이름
- 영문 source 이름
- 자동 변환 후보
- 서비스 표시명 후보
- 후보 artist_key 목록
- 생년/국적/활동지
- 대표 작품군/가격대
- 자동 확정 근거 또는 검수 필요 사유
- 충돌 사유
- 승인/반려 버튼
- 승인자/승인시각/승인메모

승인/반려 이력은 MVP에서는 각 테이블의 현재 승인/반려 필드(`approved_by`/`approved_at`/`approval_note`, `rejected_by`/`rejected_at`/`reject_reason`)로 현재 상태만 보존한다. 변경 전체를 남기는 audit 이력 테이블은 post-MVP다.

## 8. 요약

```text
원천 이름은 source 컬럼에 보존한다.
자동 변환 이름은 candidate/display 컬럼에 분리한다.
alias는 같은 작가를 찾기 위한 이름 후보 목록이다.
동명이인은 ambiguous로 분리하고 자동 병합하지 않는다.
운영(active) artist_key는 자동 확정 조건 통과 또는 운영자 승인 후에만 확정한다. 신규 후보는 provisional artist_key(needs_review)로 생성되며 active가 아니다.
```
