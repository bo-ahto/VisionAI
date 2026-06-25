# artist_key 및 작가명 표준화 흐름

작성일: 2026-06-24

목적:

- 작가명 한글화/영문화, 동명이인 처리, `artist_key` 생성 과정을 한 문서에서 이해할 수 있게 정리한다.
- 원천값, 자동 변환값, 서비스 표시값, 최종 작가 키를 섞지 않도록 기준을 명확히 한다.
- 운영자가 어떤 단계에서 무엇을 검수해야 하는지 확인할 수 있게 한다.

관련 문서:

- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [4개 원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
- [4개 원천 사이트 주기 수집 및 MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)

## 문서 세트에서의 위치

데이터 수집 문서는 아래 순서로 읽는 것을 기준으로 한다.

1. [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
   - 사용자/어드민/수집 job이 어떤 상황에서 어떻게 동작하는지 설명한다.
2. [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
   - 작가 검색, 작가명 검수, artist_key 연결 검수 화면 구조를 설명한다.
3. [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
   - 작가 검색, 신규 작가 후보 등록, artist_key 승인 API를 설명한다.
4. [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
   - 수집 실행, 실패 처리, 운영자 알림, snapshot 반영 기준을 설명한다.
5. [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
   - 작가명 한글화/영문화, alias, 동명이인, 최종 artist_key 생성 기준을 설명한다.
6. [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
   - 각 원천에서 어떤 작품/작가 값을 수집하고, 어떤 공통 컬럼으로 옮기는지 설명한다.
7. [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
   - DB 구조, job 구조, migration, 테스트 기준을 설명한다.

이 문서는 네 문서 중 작가명과 작가 키 판단 기준을 담당한다. 다른 문서에서는 핵심 요약만 남기고, 상세한 판단 흐름은 이 문서를 기준으로 한다.

> 권한 기준(이 문서 전체 적용): 검수 큐의 보류·반려·연결 검토·신규 작가 후보 판단은 운영자가 수행한다. 그러나 `artist_identity`에 쓰는 최종 확정(신규 `artist_key` 생성, 기존 `artist_key` 연결 확정)은 데이터 관리자 권한이다. 아래에서 "운영자 검수 큐에서 승인 시 생성/확정"이라고 적힌 단계의 최종 승인 주체는 데이터 관리자다. 권한 단일 기준은 [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md) 5장과 [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md) 2.2다.

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
        |     -> 신규 작가 후보
        |     -> artist_key는 아직 생성하지 않음
        |     -> 운영자 검수 큐
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
        |     -> 다른 후보 비교 또는 신규 작가 후보
        |
        +-- 판단 근거 부족 또는 동명이인 가능성 있음
              -> needs_review
        |
        v
artist_identity
  - 기존 artist_key 연결 확정
  - 또는 데이터 관리자 승인 후 신규 artist_key 생성 확정
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

## 4. 이름 보강 / 한글화 처리

### 4.0 처리 원칙

한글명 생성은 단일 규칙이 아니라 **입력이 무엇인지부터 판별한 뒤** 유형별로 다른 규칙을 쓴다. 가장 중요한 구분은 아래 둘이다. 이 둘을 섞으면 `choonjae kim`을 `김초온재`로 만드는 류의 오류가 난다.

- **한글 복원**: 원래 한국 이름이 로마자로 적혀 들어온 경우. 로마자를 글자 단위로 음역하지 않고, 원래의 한글 표기를 복원한다(`choonjae kim` → `김춘재`).
- **음역(transliteration)**: 외국 작가명/단체명을 외래어 표기법으로 한글 표기한다(`matthew anderson` → `매튜 앤더슨`).

공통 원칙:

- 자동 음역 결과를 `*_source`에 쓰지 않는다. `*_candidate`/`*_display`에만 쓴다.
- 확정 한글명은 override(4.6)가 1순위다. override에 없을 때만 자동 후보를 만든다.
- 한글 복원은 자동으로 추정하지 않는다. 명백한 케이스만 override로 등록하고, 나머지는 검수 큐에 남긴다.
- `artist_name_ko_orig`(보정 전 원본)은 항상 보존한다.

### 4.1 입력 유형 분류 (먼저 무엇인지 판별)

```text
normalized_artist_staging
        |
        v
이름 문자열 메타 오염 제거 (생년·suffix·중복토큰)
        |
        v
입력 유형 판별
        |
        +-- ① 원천에 한글명 있음            -> source alias, 재추정 안 함
        +-- ② 한 문자열에 한글+영문 동시      -> parsed alias로 분리
        +-- ③ 로마자화된 '한국' 이름         -> 한글 복원 대상 (override/검수)
        +-- ④ 외국 작가명                   -> 외래어 음역 후보
        +-- ⑤ 갤러리/스튜디오/단체명          -> 표기 규칙 + 띄어쓰기
        +-- ⑥ 예명/브랜드명                 -> 공식 표기 고정 (override)
        |
        v
artist_name_alias 저장 + reason code 기록
```

③ vs ④ 판별 신호:

| 신호 | ③ 한국 이름(복원) | ④ 외국 이름(음역) |
|---|---|---|
| 성씨 토큰 | `kim/lee/park/choi/yoon` 등 한국 성씨 사전에 있음 | 없음 |
| 음절 패턴 | 한국식 로마자 음절 | 비한국식 |
| 원천 국적/한글 alias | 한국 또는 한글 alias 존재 | 비한국 |
| 판별 불가 | — | → `needs_review`(자동 음역 금지) |

### 4.2 유형별 처리 기준

`input_type` 코드는 `normalized_artist_staging.artist_name_ko_input_type`([MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) 5.9)에 저장한다.

| 입력 유형 | `input_type` 코드 | 판별 신호 | 처리 | 절대 금지 |
|---|---|---|---|---|
| ① 원천 한글명 | `source_hangul` | source에 한글 존재 | `source` alias, `*_ko_source` 보존 | 재추정 |
| ② 한글+영문 혼재 | `parsed_mixed` | `한글 \| English` | `parsed` alias로 분리 | 한쪽 폐기 |
| ③ 로마자화 한국 이름 | `hangul_restore` | 한국 성씨/음절 패턴 | override 복원, 미등록은 검수 | **글자 단위 음역** |
| ④ 외국 작가명 | `foreign_translit` | 비한국 토큰 | 외래어 음역 후보 + 검수 | 한국식 성+이름 강제 |
| ⑤ 갤러리/스튜디오/단체 | `foreign_translit` | `gallery/studio/collective` 토큰 | 표기 규칙 + 종별어 띄어쓰기 | 인명 어순 규칙 적용 |
| ⑥ 예명/브랜드 | `pen_name` | 등록 예명 | 공식 표기 고정(override) | 음역 |
| (공통) 자동 변환만 있음 | — | — | 표시/후보 사용 가능, `artist_key` 단독 확정 금지 | — |

메타 오염(생년·suffix)이 있는 입력은 4.1 첫 단계에서 `input_type=meta_polluted`(임시값)로 두었다가, 정리 후 위 ①~⑥의 최종 코드로 재분류한다. 최종 `input_type`에는 `meta_polluted`가 남지 않는다.

### 4.3 이름 어순 기준

`lookha bark → 박루카`, `mihei her → 허미혜`처럼 어순이 뒤집혀 들어오는 케이스가 많다.

- 한국 작가: **성 + 이름** 고정. 성씨 사전으로 성 토큰을 식별해 앞으로 보낸다.
- 외국 작가: **이름 + 성** 원어 순서를 유지한다.
- 성/이름 판별이 불가하면 자동으로 뒤집지 않고 `needs_review`로 둔다.

### 4.4 한글화 reason code (표준 분류)

각 한글명 후보는 `artist_name_ko_reason`에 아래 코드를 기록하고, 코드에 따라 자동/검수 게이트가 정해진다. (코드 체계는 `scripts/track6/artist_ko_overrides.csv` 및 [작가 한글명 개선 보고서](../dataset/artist_name_ko_improvement_report.md)와 동일하게 유지한다.)

| reason code | 의미 | 게이트 |
|---|---|---|
| `source_hangul` | 원천 한글명 그대로 | 자동 |
| `obvious_bad_romanization` | 로마자 한국 이름의 한글 복원 | **override 등록 필수**, 자동 음역 금지 |
| `metadata_removed_and_romanization_fixed` | 메타 오염 제거 후 복원 | 검수 |
| `readable_foreign_name_transliteration` | 외국 인명 음역 | 자동 후보 + 검수 |
| `readable_gallery_name_transliteration` | 갤러리명 음역 | 자동 후보 + 검수 |
| `readable_studio_name_transliteration` | 스튜디오/단체명 음역 | 자동 후보 + 검수 |
| `pen_name_official` | 예명/브랜드 공식 표기 | override 고정 |

`obvious_bad_romanization`과 `pen_name_official`은 자동 후보를 만들지 않는다. override에 등록된 값만 적용하고, 미등록이면 검수 큐로 보낸다.

### 4.5 표기 규칙 출처

"읽을 수 있게"는 주관적이라 검수가 흔들린다. 기준 표준을 고정한다.

- 외래어 음역: 국립국어원 **외래어 표기법** 준거.
- 로마자 역복원: RR/MR 로마자 표기를 가정하되 **한국 성씨 사전을 우선** 적용한다.
- 단체명 띄어쓰기: 종별어를 분리한다(`gallery hexagon` → `갤러리 헥사곤`, `stepper studio` → `스테퍼 스튜디오`).

### 4.6 override 우선 적용

확정 한글명의 single source of truth는 `scripts/track6/artist_ko_overrides.csv`다. 한글화 파이프라인은 다음 순서로 적용한다.

```text
1) override 적용  -> 등록된 artist_key는 override 한글명으로 확정
2) 미등록 자동 후보 -> 4.1~4.4 기준으로 ko_candidate 생성
3) 잔여            -> 한글명 검수 큐(7장)로 이동
```

override 행 스키마:

| 컬럼 | 의미 |
|---|---|
| `artist_key` | 대상 작가 키 |
| `artist_name_ko` | 확정 한글명 |
| `reason` | 4.4의 reason code |
| `approved_by` / `approved_at` | 승인자 / 승인 시각 |

### 4.7 track6 한글 복원에 자동 음역기 사용 금지

과거 track3 데이터셋 생성기(`scripts/track3/build_unified_dataset.py`의 `_romanize_to_hangul`, `lookup_artist_name_ko`)는 로마자를 greedy longest-match 음절표로 글자 단위 음역했고, 이것이 `choonjae kim` → `김초온재` 같은 오표기를 **생성한 원인**이다. 이 음역기는 아직 코드에 살아 있다.

- track6 한글 복원(유형 ③)에는 이 음역기를 사용하지 않는다. 신규 작가가 들어와도 자동 음역으로 한글명을 만들지 않고, override(4.6) 또는 검수 큐로 보낸다.
- track3/track4 경로에서 생성된 기존 한글명은 그대로 신뢰하지 않고, 4.8의 자동 플래그로 위험도를 재산정한다.

### 4.8 한글명 자동 플래그 (파이프라인 단계)

한글명 검수는 운영자가 일일이 찾는 게 아니라, `normalized_artist_staging` 생성 시 **자동으로 플래그를 매기고 검수 큐에 적재**한다. 오프라인 1회성 스크립트가 아니라 수집 파이프라인의 한 단계다.

각 작가 row에 대해 자동 산출한다.

| 산출값 | 방법 |
|---|---|
| `artist_name_ko_input_type` | 4.1 분기로 ①~⑥ 최종 코드 판별(메타 오염은 `meta_polluted` 임시값 후 재분류) |
| `artist_name_ko_reason` | 4.4 reason code 후보 |
| `artist_name_ko_risk_score` / `_risk_reasons` | 위험 패턴 검출(`흐/운그/우르/엑스응` 등 기계 음역 흔적, 8자 이상 장음절, 브랜드명 공백 누락). 로직 기준은 `scripts/track6/audit_artist_korean_name_quality.py` |
| `artist_name_ko_roundtrip_confidence` | 복원 한글명을 RR로 재로마자화(`korean-romanizer` 류)해 원천 로마자와 유사도 비교 |

자동 게이트:

```text
input_type=source_hangul              -> review_status=auto_approved (자동 음역 아님)
override 등록됨                        -> override 값 확정, override_status=registered
reason=obvious_bad_romanization / pen_name_official 인데 override 없음
                                       -> review_status=needs_review (자동 음역 금지)
risk_score>0 또는 roundtrip 낮음        -> review_status=needs_review
그 외 음역 후보                        -> ko_candidate 생성, review_status=needs_review
```

자동 확정은 `source_hangul`과 override 등록분에만 적용한다. 나머지는 모두 한글명 검수 큐(7장)로 보내 사람이 확인한다.

## 5. 동명이인 처리

동명이인 처리는 모든 작가 row에 적용하지 않는다. 같은 `alias_name` 또는 승인 alias가 기존 `artist_key` 후보와 겹칠 때만 이 로직에 들어간다.

동명이인은 같은 `alias_name`이 여러 작가 후보에 걸리는 상황이다. 기존 후보가 없고 원천 ID도 처음 등장한 작가는 동명이인 처리 없이 신규 작가 후보로 둔다. 이 단계에서는 최종 운영 키인 `artist_key`를 아직 생성하지 않는다.

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
        |     -> 신규 작가 후보
        |     -> artist_key는 아직 생성하지 않음
        |     -> 운영자 검수 큐
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
        |     -> 다른 후보 비교 또는 신규 작가 후보로 이동
        |
        +-- 자동 확정/반려 기준 모두 미달
            (6.1의 "수동 검수 필요" 기준)
              -> artist_key에 바로 연결하지 않음
              -> review_status=needs_review 기록
              -> 운영자 검수 큐에서 검토(보류/반려), 신규 artist_key 생성·연결 확정은 데이터 관리자 승인
```

동명이인 상태 기준:

| 상태 | 의미 | 처리 |
|---|---|---|
| `unique` | 같은 `alias_name`으로 연결 가능한 작가 후보가 1개뿐임 | 고신뢰 생년과 충돌 조건 확인 후 자동 확정 검토 가능 |
| `ambiguous` | alias가 여러 작가 후보에 걸림 | 자동 병합 금지 |
| `needs_review` | 자동 확정도 반려도 할 수 없는 상태 | 원천 row는 유지하고 artist_key에 바로 연결하지 않음. 운영자 검수 큐에서 검토하고, 신규 artist_key 생성·연결 확정은 데이터 관리자가 승인 |
| `match_rejected` | 특정 후보 artist_key와는 같은 작가가 아님 | 해당 후보와의 연결만 금지. 원천 row는 유지하고 다른 후보 비교 또는 신규 작가 후보로 이동 |

중요 원칙:

- 같은 이름이라는 이유만으로 병합하지 않는다.
- 같은 alias가 여러 artist_key 후보에 걸리면 `ambiguity_status=ambiguous`로 둔다.
- 데이터 관리자가 승인한 후보만 `artist_key`에 연결한다(운영자 검수 큐의 검토를 거친 뒤).
- 잘못 병합하는 것보다 일시적으로 분리해 두는 편이 안전하다.

## 6. artist_key 확정 기준

`artist_key`는 서비스와 모델에서 사용하는 최종 작가 키다. 원천 사이트의 `artist_source_id`, `artist_slug`, `artist_idx`와 다르다.

```text
normalized_artist_staging / artist_name_alias
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
        |     -> 신규 작가 후보
        |     -> artist_key는 아직 생성하지 않음
        |     -> 운영자 검수 후 데이터 관리자 승인 시 신규 artist_key 생성
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
              -> 다른 후보 비교 또는 신규 작가 후보로 이동
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
        |     -> 신규 작가 후보
        |     -> artist_key는 아직 생성하지 않음
        |     -> 운영자 검수 후 데이터 관리자 승인 시 신규 artist_key 생성
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
        |     -> 다른 후보 비교 또는 신규 작가 후보로 이동
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
- 같은 이름인데 dominant medium 분류가 다르고, 양쪽 모두 가격 row가 5건 이상이며 같은 통화 기준 가격 중앙값 차이가 2.0 log 이상이다. 자동 반려가 아니라 검수 경고로 둔다.

`needs_review`는 반려가 아니다. 원천 row는 유지하고 운영자 검수 큐에서 보류/반려를 처리하며, 기존 `artist_key` 연결 확정과 신규 `artist_key` 생성은 데이터 관리자가 승인한다.

**강한 충돌 조건 기준**

5장의 `강한 충돌 조건 충족` 분기는 이 기준을 따른다.

- 양쪽 모두 고신뢰 생년이 있는데 연도가 다르다.
- 같은 alias가 이미 다른 `artist_key`에 `approved`로 연결되어 있다.
- 같은 원천에서 같은 `artist_source_id`가 서로 다른 `artist_key`에 승인되어 있다.
- 운영자가 후보 비교 후 같은 작가가 아니라고 반려했다.

`match_rejected`는 데이터 삭제나 격리가 아니다. 원천 row는 유지하고, 다른 후보가 있으면 계속 비교한다. 맞는 후보가 없으면 신규 작가 후보 또는 `needs_review`로 이동한다.

**신규 작가 후보 기준**

- `source + artist_source_id`가 있고, 해당 조합에 연결된 기존 `artist_key`가 없고, 강한 충돌 조건이 없다.
- `artist_source_id`가 없으면 자동으로 `artist_key`를 만들지 않는다. 원천 작가명, 원천 작가 URL 또는 `source_artist_raw_id`, 작품 row 연결 정보처럼 최소 식별값이 있을 때만 신규 작가 후보로 두고 운영자 검수 큐에 올린다.

신규 작가 후보는 바로 최종 확정하지 않는다. `artist_identity_candidate`를 거치지 않는 경우에도 별도 신규 후보 큐에 저장하고, 운영자 검수를 거쳐 데이터 관리자가 승인한 뒤에만 `artist_identity.artist_key`를 생성한다. 즉 `artist_key`는 `active` 상태로 확정된 최종 운영 키만 의미한다.

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

### 6.2 병합 취소(un-merge) 기준

잘못 병합한 작가는 되돌릴 수 있어야 한다. "잘못 병합이 분리보다 위험"하다는 원칙은 사고 시 복구 경로가 있을 때만 성립한다.

- 병합으로 `identity_status=merged`가 된 작가 키는 삭제하지 않고 보존한다. 어느 `artist_key`로 병합됐는지와 `merge_evidence_json`을 남긴다.
- 병합이 틀렸다고 판단되면 데이터 관리자가 un-merge를 확정한다. 운영자는 un-merge 후보를 검수 큐에 올릴 수 있으나 확정 권한은 데이터 관리자다.
- un-merge 시 병합됐던 원천 작가 row를 원래 또는 신규 `artist_key`로 다시 연결하고, 처리자·시각·사유와 직전 상태를 `identity_event_log`([MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) 5.12.1)에 append한다.
- 병합/un-merge로 영향받은 작가의 가격 이력·Warm feature는 재생성 대상으로 표시한다. 과거 snapshot은 수정하지 않고 다음 snapshot부터 반영한다.

## 7. 운영 화면에서 봐야 할 항목

운영자는 아래 큐를 분리해서 봐야 한다.

| 큐 | 확인 대상 | 주요 조치 |
|---|---|---|
| 이름 alias / 한글명 검수 큐 | 한글명/영문명 표시 후보, 자동 변환 후보, override 미등록 한글 복원 후보, 자동 음역 후보(4장) | 표시명 승인/수정/반려, 한글명 승인/수정/반려, override 등록 |
| 동명이인 큐 | 같은 alias가 여러 artist_key 후보에 걸린 경우 | 후보 비교 후 승인/반려 |
| artist identity 큐 | 동명이인 가능성이 있거나 기존 artist_key 연결 후보가 있는 작가 row | 연결 검토/보류/반려(운영자), 기존 키 연결 확정(데이터 관리자) |
| 신규 작가 후보 큐 | 연결 가능한 기존 artist_key 후보가 없는 작가 row | 검토/보류/반려(운영자), 신규 artist_key 생성 승인(데이터 관리자) |

> 큐 명칭 매핑: 위 `이름 alias / 한글명 검수 큐`는 어드민의 단일 `작가명 검수 큐`(API `GET /api/v1/admin/review/artist-names`)와 같은 큐다. 한글 복원/음역 검수와 표시명/alias 검수는 별도 물리 큐가 아니라 이 큐의 탭/필터로 운영한다. `동명이인 큐`+`artist identity 큐`는 어드민의 `artist_key 연결 검수 큐`에 대응한다. 다른 문서(`data_collection_service_scenarios`, `weekly_crawler_mysql_operation_plan`)의 `이름 alias 큐`도 이 큐를 가리킨다.

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

한글명 검수 큐 추가 표시(4장 기준):

- 원천 작가명 원문(`artist_name_raw`)
- 보정 전 한글명(`artist_name_ko_orig`)
- 입력 유형(4.1의 ①~⑥)
- reason code(`artist_name_ko_reason`, 4.4)
- 한글 복원/음역 후보값
- override 등록 여부 및 등록 시 확정 한글명
- 자동/검수 게이트 사유(reason code는 4.4, 게이트 규칙은 4.8)

한글명 검수(이름 alias / 한글명 검수 큐의 한글명 탭)는 동명이인·artist identity 큐와 분리해 운영한다. 한글명 검수에서 확정한 값은 `scripts/track6/artist_ko_overrides.csv`(4.6)에 등록하고, 등록 결과는 다음 snapshot부터 반영한다.

검수 트리아지(우선순위): 잔여 검수 후보가 누적되므로 큐를 무한정 쌓지 않도록 정렬·필터한다.

- 1차 정렬: `artist_name_ko_risk_score` 내림차순 → 영향 행수(작가별 row 수) 내림차순.
- 가격 영향 가중: 가격 row가 많은 작가, snapshot 포함 후보를 우선 노출한다.
- `reason=obvious_bad_romanization`처럼 자동 음역 금지 대상은 항상 상단에 둔다.
- 행수 1~2건의 저영향 후보는 배치 일괄 처리 또는 후순위로 내려도 된다.

이 기준은 4.8의 자동 산출값(`risk_score`, `input_type`, `reason`)을 그대로 정렬 키로 쓴다.

승인/반려 이력은 각 테이블의 현재 승인/반려 필드(`approved_by`/`approved_at`/`approval_note`, `rejected_by`/`rejected_at`/`reject_reason`)로 현재 상태를 보존한다. 변경 전체 audit 이력 테이블은 별도 고도화 항목으로 둔다. 단, 신규 생성·연결 확정·병합·un-merge 같은 비가역 identity 결정은 `identity_event_log`([MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) 5.12.1)에 append-only로 남긴다.

## 8. 요약

```text
원천 이름은 source 컬럼에 보존한다.
자동 변환 이름은 candidate/display 컬럼에 분리한다.
alias는 같은 작가를 찾기 위한 이름 후보 목록이다.
동명이인은 ambiguous로 분리하고 자동 병합하지 않는다.
artist_key는 자동 확정 조건 통과 또는 데이터 관리자 승인 후에만 생성/확정되는 최종 운영 키다(운영자 검수 큐를 거친 뒤). 신규 작가 후보 단계에서는 artist_key를 발급하지 않는다.
```
