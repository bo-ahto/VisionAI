# 사용자 / 어드민 화면 구조 및 기능 기획

작성일: 2026-06-25

대상:

- 가격 예측 사용자 화면
- 데이터 수집/검수 어드민 화면
- Artsy / Saatchi / Print Bakery / Art1 수집 데이터 운영 화면

목적:

- 사용자와 운영자가 어떤 화면에서 어떤 정보를 보고 어떤 결정을 하는지 정의한다.
- 화면 구조, 필터, 버튼, 상태 표시, 검수 기능을 정리한다.
- 시나리오 문서의 흐름을 실제 화면 설계 기준으로 옮긴다.

관련 문서:

- [1차 개발 로드맵](first_development_roadmap_20260625.md)
- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [사용자 화면 상세 명세](user_frontend_screen_spec_20260625.md)
- [어드민 화면 상세 명세](admin_screen_detail_spec_20260625.md)
- [프론트 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)
- [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md)
- [프론트 API Mock / Fixture 기준](frontend_api_mock_fixtures_20260625.md)
- [프론트 E2E 테스트 계획](frontend_e2e_test_plan_20260625.md)
- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
- [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
- [NANT 재료(지지체/매체) 분류 기준](nant_material_classification_criteria_20260626.md)

## 1. 문서 역할

이 문서는 화면 기획 문서다. 따라서 개발 일정, 서버 기능 상세, DB migration 상세는 다루지 않는다.

```text
시나리오 문서
  -> 사용자가 어떤 상황에서 무엇을 하는지 정의
        |
        v
화면 구조 및 기능 기획
  -> 그 상황을 어떤 화면, 필터, 버튼, 상태 표시로 처리할지 정의
        |
        v
API 기획
  -> 화면 기능이 호출할 사용자/어드민 서버 기능 정의
        |
        v
기술 상세 문서
  -> 화면 동작을 구현하기 위한 DB, 서버, 작업 실행 상세 정의
```

## 2. 전체 화면 구성

```text
[사용자 화면]
  - 가격 예측 입력
  - 작가 검색/선택
  - 작품 정보 입력
  - 예측 결과
  - 입력값 보완 안내

[어드민 화면]
  - 수집 대시보드
  - 수집 run 상세
  - 작품 품질 검수 큐
  - 작가명 검수 큐
  - artist_key 연결 검수 큐
  - 신규 작가 후보 큐
  - snapshot 후보 확인
  - NANT mapping 관리
  - 모델 운영
  - 운영 로그/알림
```

## 3. 사용자 화면

### 3.1 가격 예측 입력 화면

목적:

- 사용자가 작품과 작가 정보를 입력해 가격 예측을 요청한다.
- 예측에 필요한 필수값을 빠뜨리지 않게 한다.

주요 영역:

| 영역 | 내용 |
|---|---|
| 작가 입력 | 작가명 검색, 후보 선택, 신규 작가 후보 입력 |
| 작품 기본 정보 | 작품명, 제작연도, 작품 유형 |
| 크기 입력 | 가로 cm, 세로 cm, 깊이 cm |
| 재료/지지체 입력 | 재료, 지지체, 매체 카테고리 |
| 가격 예측 요청 | 입력값 검증 후 예측 요청 |

필수 검증:

- 가로 cm와 세로 cm는 양수여야 한다.
- 깊이 cm는 입체 작품 판단에 쓰므로 값이 있으면 함께 검증한다.
- 재료/지지체가 DB active NANT mapping 기준에서 매핑되지 않거나 학습 제외 기준에 해당하면 예측 전 확인 메시지를 보여준다.
- 작가가 확정되지 않은 경우 예측 가능 여부와 검수 필요 상태를 분리해서 보여준다.

화면 표시 원칙:

- 호당 가격은 계산 기준이 아니라 표시용 참고값으로만 보여준다.
- cm 기준 입력값이 실제 가격 예측의 기본 입력임을 명확히 보여준다.
- 사용자가 수정할 수 있는 오류와 운영자 검수가 필요한 상태를 구분한다.
- 사용자 화면에는 수집 원천 사이트명을 노출하지 않는다. 원천 사이트, 원천 URL, 원천 작가 ID는 어드민 검수와 운영 추적용 정보다.

### 3.2 작가 검색/선택 화면

목적:

- 사용자가 입력한 작가명이 어떤 확정 작가인지 선택하게 한다.
- 동명이인 또는 유사 이름 작가를 잘못 선택하지 않게 한다.

검색 결과에 표시할 항목:

| 항목 | 이유 |
|---|---|
| 서비스 표시용 한글명 | 사용자 화면 기본 표시명 |
| 서비스 표시용 영문명 | 영문 작가명 확인 |
| 생년 | 동명이인 구분 |
| 국적/활동지 | 보조 확인 정보 |
| 대표 작품 수 | 작가 이력 규모 확인 |
| 가격 이력 보유 여부 | Warm 예측 가능성 확인 |

상태별 화면 동작:

| 상태 | 사용자 화면 동작 |
|---|---|
| 후보 1명 | 후보 정보를 보여주고 선택하게 함 |
| 후보 2명 이상 | 후보 목록에서 사용자가 직접 선택 |
| 후보 없음 | 신규 작가 후보 입력으로 이동 |
| 후보 정보 부족 | 검수 필요 안내 표시 |

### 3.3 신규 작가 후보 입력 화면

목적:

- 기존 확정 작가에 없는 작가를 운영 검수 대상으로 등록한다.

입력 항목:

- 작가명
- 작가명 원문 언어
- 알고 있는 영문명
- 알고 있는 한글명
- 생년
- 국적
- 활동지
- 작가 홈페이지 또는 참고 URL
- 참고 메모

처리 원칙:

- 사용자 입력만으로 최종 `artist_key`를 생성하지 않는다.
- 신규 작가 후보는 어드민 신규 작가 후보 큐로 보낸다.
- 사용자가 입력한 값은 수집 데이터와 구분해서 저장한다.

### 3.4 예측 결과 화면

목적:

- 예측 가격과 함께 예측을 해석하는 데 필요한 보조 정보를 보여준다.
- 사용자가 가격을 판단할 때 필요한 1차 시장 가격 참고 정보를 함께 보여준다.

표시 항목:

| 항목 | 표시 방식 |
|---|---|
| 예측 가격 | 원화 기준 가격 |
| 입력 크기 | 가로 x 세로 cm |
| 표시용 호당 환산 | 필요한 경우 참고값으로 표시 |
| 예측 신뢰도 | 높음/보통/검수 필요 등급 |
| 검수 필요 사유 | 작가 미확정, 입력값 부족, 작품 유형 확인 필요 등 |
| 사용한 작가 | 선택된 작가명과 보조 정보 |
| 1차 시장 가격 카드 | 호당가 중앙값, 호당가 범위, 매체별 분포, 표본 수 |
| 데이터 기준일/최신성 | 예측에 사용한 데이터의 기준일(as_of)과 최신성 표시 |

1차 시장 가격 카드에 표시할 정보:

| 항목 | 표시 예 | 의미 |
|---|---|---|
| 카드 제목 | 1차 시장 가격 | 사용자에게 보여줄 참고 가격 영역 |
| 기준값 라벨 | 호당가 중앙값 | 표본의 대표 호당가 |
| 기준값 | 35만원/호 | 중앙값 기준 호당 가격 |
| 범위 | 28만 - 46만원/호 | 참고 표본의 하위/상위 범위 |
| 매체별 분포 | 회화 33만, 드로잉 28만 | 매체별 호당가 참고값 |
| 표본 수 | N=24건 | 계산에 사용한 참고 작품 수 |

주의:

- 예측 가격과 표시용 환산값을 같은 수준의 계산 결과처럼 보이게 하면 안 된다.
- 검수 필요 상태에서도 예측 가격을 보여줄 수 있지만, 확정 결과처럼 표현하면 안 된다.
- 1차 시장 가격 카드는 사용자 이해를 돕는 참고 정보다. 모델의 최종 예측 가격을 대체하지 않는다.
- 카드에는 원천 사이트명, 원천 URL, 원천 작품 ID를 노출하지 않는다. 표본 수와 분포 요약만 보여준다.
- 데이터 기준일/최신성은 예측 API 응답의 `as_of` 값을 표기한다. 예측 결과가 항상 최신 수집 데이터를 반영하는 것은 아님을 사용자가 알 수 있게 한다.

### 3.5 입력값 보완 화면

목적:

- 예측이 불가능한 이유를 사용자가 바로 이해하고 수정하게 한다.

보완 안내 예:

| 상황 | 안내 |
|---|---|
| 가로/세로 누락 | 작품 크기를 cm 단위로 입력해야 함 |
| 재료 누락 | 재료 또는 매체를 선택해야 함 |
| 작가 미선택 | 작가 검색 후 후보를 선택해야 함 |
| NANT 매핑 불가/학습 제외 | 현재 가격 예측 범위에서 제외될 수 있음 |
| 신규 작가 후보 | 운영 검수 후 작가 확정 가능 |

## 4. 어드민 화면

### 4.1 수집 대시보드

목적:

- 운영자가 주기 수집 결과를 한 화면에서 확인한다.

상단 요약:

| 항목 | 설명 |
|---|---|
| 마지막 수집 시각 | 최근 run 종료 시각 |
| 전체 수집 상태 | 성공, 부분 실패, 실패, 검수 필요 |
| 사이트별 수집 row 수 | Artsy / Saatchi / Print Bakery / Art1 |
| 상세 수집 실패 수 | 상세 페이지 또는 상세 응답 실패 |
| 가격 보유 row 수 | 가격 숫자가 있는 row |
| 크기 파싱 성공률 | 가로/세로 cm 추출 성공률 |
| 신규 검수 큐 수 | 새로 운영자 검수가 필요한 row |
| snapshot 후보 수 | 반영 가능한 row 수 |

지표 출처:

- 이 화면의 요약 지표는 수집 대시보드 요약 API(`GET /api/v1/admin/collection-runs/summary`)에서 온다.
- 가격 보유 row 수, 크기 파싱 성공률은 사이트별 `raw_artwork_rows`/`normalized_artwork_rows`와 품질 집계 기준으로 계산한 수집 모집단 값이다.
- 신규 검수 큐 수는 요약 API의 `review_queue_counts`(작품/작가명/artist_key/신규 작가), snapshot 후보 수는 `snapshot_candidate_count`에서 온다.
- snapshot 후보 수는 검수를 통과해 반영 가능한 모집단이고, 위 가격/크기 지표는 수집 직후 모집단이다. 두 모집단이 다르므로 같은 값으로 보지 않는다(§4.7 snapshot 후보 요약은 후보 모집단 기준 지표를 따로 보여준다).

필터:

- 수집일
- 원천 사이트
- 수집 상태
- 실패 유형
- 검수 필요 여부

### 4.2 수집 run 상세 화면

목적:

- 특정 수집 run에서 어떤 문제가 있었는지 확인한다.

표시 항목:

- run 시작/종료 시각
- 원천 사이트
- 목록 수집 건수
- 상세 수집 건수
- 실패 URL 목록
- 실패 사유
- parser 경고
- 중복 후보 수
- 신규/변경/삭제 후보 수

지표 출처:

- 이 화면의 run 단위 지표(중복 후보 수, 신규/변경/삭제 후보 수, 실패 URL/사유)는 수집 run 상세 API(`GET /api/v1/admin/collection-runs/{run_id}`)에서 온다.
- §4.1 대시보드 지표는 기간/사이트 단위 집계이고, 이 화면은 단일 run 단위다. 같은 이름의 지표라도 모집단(run 1건 vs 기간 전체)이 다르다.

운영자 액션:

| 버튼 | 동작 | API 매핑 |
|---|---|---|
| 재수집 요청 | 실패한 범위만 다시 수집 대상으로 표시 | `request_retry` (scope=`failed_only`) |
| 보류 | 이번 run의 snapshot 반영을 보류 | `hold` |
| 검수 큐로 이동 | 상세 검수 대상 목록으로 이동 | (화면 이동) |
| 메모 저장 | 운영 판단 사유 기록 | action `reason` 필드 |

- 재수집 요청은 수집 run 조치 API(`POST /api/v1/admin/collection-runs/{run_id}/actions`)의 `request_retry`에 매핑되며, "실패 범위만" 재수집은 `scope=failed_only`와 일치한다. run 전체 재수집과 구분한다.

### 4.3 작품 품질 검수 큐

목적:

- 작품 단위로 가격, 크기, 재료, 유형, 중복 문제를 검수한다.

목록 필터:

- 원천 사이트
- 가격 있음/없음
- 크기 파싱 성공/실패
- NANT 재료 분류 성공/실패/학습 제외
- 제외 후보(`nant_learning_excluded`, `nant_unmapped` 포함)
- 중복 후보
- 검수 상태(검수 중 포함)

목록에는 각 row의 "검수 중(처리 중)" 여부와 담당자(claim한 운영자)를 표시한다. 다른 운영자가 claim한 row는 동시 처리 충돌을 막기 위해 처리 중임을 화면에서 드러낸다(§6 상태표 "검수 중" 참조).

상세 화면:

| 영역 | 내용 |
|---|---|
| 원천값 | 사이트에서 받은 원문 값 |
| 분해/정리값 | 원천 문자열을 분해한 값 |
| 표준화 후보값 | 공통 컬럼에 들어갈 후보값 |
| NANT 분류 | `nant_support`, `nant_medium`, `nant_category_key`, `nant_mapping_status` |
| 품질 플래그 | 가격 없음, 크기 없음, NANT 제외 후보 등 |
| 원천 링크 | 원문 확인용 URL |
| 처리 버튼 | 승인, 수정 후 승인, 보류, 제외 |

### 4.4 작가명 검수 큐

목적:

- 작가명 한글화/영문화, 서비스 표시명, alias 후보를 검수한다.

표시 항목:

- 원천 작가명
- 원천 언어
- 보정 전 한글명(`artist_name_ko_orig`)
- 자동 변환 한글명
- 자동 변환 영문명
- 서비스 표시용 한글명 후보
- 서비스 표시용 영문명 후보
- 기존 alias 후보
- 한글화 입력 유형(①~⑥, [표준화 흐름](artist_key_standardization_flow_20260624.md) 4.1)
- reason code(`obvious_bad_romanization` 등, 4.4)
- 위험 점수/사유(`흐/운그/우르`… 기계 음역 흔적)
- RR 역검증 신뢰도
- override 등록 여부
- 검수 필요 사유

> 한글화 입력 유형·reason code·위험 점수·역검증 신뢰도는 [표준화 흐름](artist_key_standardization_flow_20260624.md) 4.8에서 자동 산출해 큐에 함께 적재한다. 위험 점수·영향 행수 순으로 정렬(트리아지)한다.

목록에는 각 row의 "검수 중(처리 중)" 여부와 담당자(claim한 운영자)를 표시한다(§6 상태표 "검수 중" 참조).

처리 버튼:

| 버튼 | API 매핑 |
|---|---|
| 표시명 승인 | `decision=approve` |
| 표시명 수정 후 승인 | `decision=approve_with_edit` |
| override 등록(확정 한글명을 `artist_ko_overrides.csv`에 등록, 4.6) | `decision=register_override` |
| alias 추가 | `decision=add_alias` |
| 보류 | `decision=hold` |
| 반려 | `decision=reject` |

처리는 작가명 검수 처리 API(`POST /api/v1/admin/review/artist-names/{alias_id}/decision`)에 매핑된다. 각 버튼은 decision 동사와 1:1로 대응한다: 표시명 승인=`approve`, 표시명 수정 후 승인=`approve_with_edit`, alias 추가=`add_alias`, 보류=`hold`, 반려=`reject`. "alias 추가"는 별도 `decision=add_alias`로 보내며, `approve`/`approve_with_edit`와 겹치지 않는다(표시명 승인이 alias를 추가하지 않고, alias 추가가 표시명을 확정하지 않는다).

### 4.5 artist_key 연결 검수 큐

목적:

- 수집된 작가가 기존 `artist_key`와 같은 작가인지 판단한다.

목록 필터:

- 원천 사이트
- 후보 수
- 생년 일치 여부
- alias 일치 유형
- 동명이인 후보 여부
- 자동 확정 실패 사유

목록에는 각 후보의 "검수 중(처리 중)" 여부와 담당자(claim한 검수자)를 표시해 동시 처리 충돌을 막는다(§6 상태표 "검수 중" 참조).

상세 화면 비교 항목:

| 비교 항목 | 설명 |
|---|---|
| 원천 작가 정보 | 새로 수집된 작가 row |
| 기존 artist_key 후보 | 연결 가능한 기존 작가 |
| alias 비교 | exact, approved, fuzzy 여부 |
| 생년 비교 | 양쪽 생년과 신뢰도 |
| 국적/활동지 | 보조 확인 정보 |
| 대표 작품 | 잘못 연결을 막기 위한 보조 확인 |
| 원천 URL | 추적용 링크 |

처리 버튼:

| 버튼 | 최소 권한 |
|---|---|
| 기존 `artist_key`에 연결 승인 | 데이터 관리자 |
| 후보 반려 | 운영 담당자 |
| 보류 | 운영 담당자 |
| 신규 작가 후보로 전환 | 운영 담당자 |

기록:

- 처리자
- 처리시각
- 처리 사유
- 이전 상태
- 변경 후 상태

### 4.6 신규 작가 후보 큐

목적:

- 기존 `artist_key`와 연결되지 않은 작가 후보를 새 작가로 확정할지 판단한다.

표시 항목:

- 원천 사이트
- 원천 작가 ID/slug
- 원천 작가명
- 서비스 표시명 후보
- 작품 목록
- 가격 보유 작품 수
- 원천 URL
- 유사 alias 검색 결과
- 보류/반려 이력

목록에는 각 후보의 "검수 중(처리 중)" 여부와 담당자(claim한 검수자)를 표시한다(§6 상태표 "검수 중" 참조).

처리:

처리는 신규 작가 후보 결정 API(`POST /api/v1/admin/review/new-artists/{candidate_id}/decision`)에 매핑된다.

| 버튼 | 결과 | API 매핑 | 최소 권한 |
|---|---|---|---|
| 신규 artist_key 생성 승인 | 최종 `artist_key` 생성 | `decision=approve` | 데이터 관리자 |
| 기존 후보 재검색 | 이름/생년 조건으로 다시 검색 | `decision=recheck` | 운영 담당자 |
| 보류 | 검수 대기 유지 | `decision=hold` | 운영 담당자 |
| 반려 | 신규 작가로 쓰지 않음 | `decision=reject` | 운영 담당자 |

이 화면의 4개 버튼은 신규 작가 후보 결정 API의 decision 동사와 1:1로 대응한다: 신규 artist_key 생성 승인=`approve`, 기존 후보 재검색=`recheck`, 보류=`hold`, 반려=`reject`. `decision=approve`만 최종 `artist_key`를 생성하고, 나머지 3개는 키를 만들지 않는다. "기존 후보 재검색(`recheck`)"은 새 artist_key를 만들기 전에 동일 작가가 기존에 있는지 이름/생년 조건으로 다시 확인하는 동작이다.

### 4.7 snapshot 후보 확인 화면

목적:

- 학습 또는 운영 반영 전 최종 후보 데이터를 확인한다.

표시 항목:

- snapshot 후보 row 수
- 사이트별 row 수
- 가격 보유율
- 크기 파싱 성공률
- NANT 분류 성공/학습 제외/unmapped 수
- 작가 확정률
- 제외 row 수
- 보류 row 수
- 직전 snapshot 대비 변화량

지표 출처:

- 이 화면 지표(후보 row 수, 가격 보유율, 크기 파싱 성공률, 작가 확정률, 제외/보류 row 수, 직전 snapshot 대비 변화량)는 snapshot 후보 요약 API(`GET /api/v1/admin/snapshots/candidates/summary`)에서 온다.
- 이 모집단은 검수를 통과해 반영 가능한 후보 row다. §4.1 대시보드의 가격/크기 지표(수집 직후 모집단)와 모집단이 다르므로 직접 비교하지 않는다.

액션(권한별):

snapshot 반영은 3단계 권한 흐름(확정 요청 → 생성 승인 → 서빙 승인)이며, API의 3개 액션과 1:1로 매핑된다.

```text
확정 요청(운영자)          생성 승인(데이터 관리자)        서빙 승인(데이터 관리자)
  snapshot_request   ->   generated(비서빙/빌드 완료)  ->   approved(서빙 대상)
```

| 화면 액션 | 권한 | API 액션 |
|---|---|---|
| snapshot 후보 확정 요청 | 운영 담당자 | 확정 요청(snapshot 후보 확정 요청 액션) |
| snapshot 생성 승인 | 데이터 관리자 | 생성 승인(`POST /api/v1/admin/snapshots`) |
| snapshot 서빙 승인 | 데이터 관리자 | 서빙 승인(`POST /api/v1/admin/snapshots/{snapshot_id}/approve`) |
| 보류 | 운영 담당자 | 후보 보류 액션 |
| 보류 사유 입력 | 운영자 / 데이터 관리자 | 액션 `reason` 필드 |
| 후보 목록 다운로드 | 운영 담당자 | `GET /api/v1/admin/snapshots/candidates/items` |

- 운영자의 "확정 요청", 데이터 관리자의 "생성 승인", 데이터 관리자의 "서빙 승인"은 모두 별도 액션이며, 한 사람이 여러 단계를 동시에 끝내지 않는다. 화면의 세 버튼은 API의 세 액션(확정 요청, 생성 승인, 서빙 승인)과 1:1로 대응한다.
- "생성 승인"은 빌드만 완료한 `generated`(비서빙) snapshot을 만든다. `generated`는 빌드 완료 상태일 뿐 사용자 서빙/노출 기준이 아니다.
- "서빙 승인"은 `generated` snapshot을 `approved`(서빙 가능)로 올리는 액션이며, `POST /snapshots/{snapshot_id}/approve`에 매핑된다. 사용자 서빙·freshness 비교 대상은 `approved` snapshot만이며, 사용자 노출 `as_of`는 active deployment 기준으로 산정한다(§4.9 모델 운영). 화면에서는 `generated` snapshot에 "서빙 승인" 버튼을 노출하고, 승인 전까지 비서빙으로 표시한다.

### 4.8 NANT mapping 관리 화면

목적:

- NANT 지지체/매체 mapping을 DB version으로 관리한다.
- unmapped 재료를 draft mapping에 반영하고, 검증 후 데이터 관리자가 active version으로 전환한다.

주요 영역:

- active version 요약
- draft/import version 목록
- validation 결과
- mapping row 검색/수정
- unmapped 재료 목록
- active 전환 영향 안내

표시 항목:

- `version_key`, `status`, `source_file_sha256`
- category 수, mapping row 수, 학습 제외 row 수
- `source_material_text`
- `nant_support`, `nant_medium`, `nant_category_key`
- `learning_excluded`, `learning_exclusion_reason`
- 수정자/수정시각

액션:

| 액션 | 권한 | 설명 |
|---|---|---|
| version 조회 | 운영 담당자 | active/draft/archived 확인 |
| CSV import | 데이터 분석가 | 새 draft version 생성 |
| draft row 추가/수정/삭제 | 데이터 분석가 | active row 직접 수정 금지 |
| validation 실행 | 데이터 분석가 | 95개 category, 중복, 잘못된 category key 검증 |
| active 전환 | 데이터 관리자 | validation passed draft만 active 가능 |

### 4.9 모델 운영 화면

목적:

- 모델 학습/import job, candidate 승인, active deployment 전환, rollback을 처리한다.
- 새 snapshot이 승인되어도 운영 모델이 자동으로 바뀌지 않는다는 점을 화면에서 명확히 보여준다.

표시 항목:

- 현재 active deployment
- active 모델의 `model_version`, `deployment_id`, route
- active 모델이 학습에 사용한 `training_snapshot_id`, `source_cutoff_at`
- 학습/import job 목록과 상태
- candidate/approved/rejected/retired 모델 목록
- validation/test metric 요약
- fixed-test parity, API smoke, data contract gate 결과
- artifact URI/SHA-256, feature schema hash

처리 버튼:

| 버튼 | 의미 | API | 권한 |
|---|---|---|---|
| 학습/import job 생성 | approved snapshot 기준 job 생성 | `POST /api/v1/admin/model-training/jobs` | 데이터 분석가 |
| 후보 승인 | candidate를 approved로 전환 | `POST /api/v1/admin/model-versions/{model_version}/decision` | 데이터 관리자 |
| 후보 반려 | candidate를 rejected로 전환 | `POST /api/v1/admin/model-versions/{model_version}/decision` | 데이터 관리자 |
| 운영 승격 | approved 모델을 active deployment로 전환 | `POST /api/v1/admin/model-deployments` | 데이터 관리자 |
| 롤백 | 이전 approved 모델로 active deployment 전환 | `POST /api/v1/admin/model-deployments` | 데이터 관리자 |

화면 규칙:

- `candidate` 모델에는 운영 승격 버튼을 노출하지 않는다.
- `approved` 모델에만 운영 승격 버튼을 노출한다.
- 현재 운영 중 여부는 model status가 아니라 deployment active 상태로 표시한다.
- job 재실행은 기존 job을 덮어쓰지 않고 새 job을 만든다.

### 4.10 운영 로그/알림 화면

목적:

- 수집 실패, 검수 처리, snapshot 생성, 모델 변경, artist_key 변경 이력을 추적한다.

표시 항목:

- 발생 시각
- 원천 사이트
- 대상 row 또는 artist_key
- 이벤트 유형
- 이전 상태
- 변경 후 상태
- 처리자
- 처리 사유

알림이 필요한 상황:

- 사이트 전체 수집 실패
- 상세 수집 실패율 급증
- 가격 보유율 급감
- 크기 파싱 성공률 급감
- 신규 검수 큐 급증
- snapshot 생성 실패
- 모델 학습/import job 실패
- 모델 승격 후 API smoke 실패
- 동일 작가 후보 충돌 증가

## 5. 권한 기준

| 역할 | 가능 작업 |
|---|---|
| 일반 사용자 | 가격 예측 입력, 작가 검색/선택, 신규 작가 후보 제출 |
| 운영 담당자 | 수집 run 확인/재수집 요청, 검수 큐 처리, 보류/제외, snapshot 후보 확인, NANT mapping 조회 |
| 데이터 분석가 | 수동 CSV 업로드/매핑, NANT draft import/편집/validation, snapshot 품질/분포 검토, 학습 피처 승격 판단, 모델 학습/import job 생성 |
| 데이터 관리자 | 원천 등록/수정, 신규 artist_key 생성 승인, 기존 artist_key 연결 확정, alias 정책 관리, NANT active 전환, snapshot 생성/서빙 승인, 모델 승인/승격/롤백 |
| 개발자 | crawler/parser 장애 확인, migration/배포 점검, 기술 로그 확인 |
| 슈퍼유저 | 운영 초기 전용 관리자. 운영 담당자, 데이터 분석가, 데이터 관리자, 개발자 화면 기능을 모두 사용 |

권한 원칙:

- 일반 사용자는 최종 `artist_key`를 생성할 수 없다.
- 운영 담당자는 검수 상태를 변경하고 연결 후보를 검토할 수 있지만, `artist_identity`에 쓰는 최종 확정(신규 artist_key 생성·기존 키 연결 확정)은 데이터 관리자 권한으로 제한한다.
- 운영 초기에는 슈퍼유저가 운영 담당자/데이터 분석가/데이터 관리자/개발자 작업을 모두 수행할 수 있다. 다만 화면에는 실제 처리자, 처리시각, 처리 사유가 남아야 하며, 추후 역할 분리 시 같은 이력이 그대로 추적 가능해야 한다.
- 슈퍼유저는 초기 운영 편의를 위한 임시 통합 권한이다. 장기 운영에서는 운영 담당자/데이터 분석가/데이터 관리자/개발자 권한을 분리한다.
- 모든 승인/반려/보류는 처리자와 처리시각을 남긴다.

## 6. 화면 상태 기준

| 상태 | 사용자 화면 | 어드민 화면 |
|---|---|---|
| 정상 | 예측 결과 표시 | 완료 상태 |
| 입력 부족 | 보완 안내 | 해당 없음 |
| 검수 필요 | 검수 필요 표시 | 검수 큐 노출 |
| 검수 중(처리 중) | 해당 없음 | 담당자 claim 표시, 다른 검수자에게 처리 중으로 표시 |
| 보류 | 결과 확정 불가 안내 | 보류 사유 표시 |
| 제외 | 예측 불가 또는 제외 안내 | 제외 사유 표시 |
| 수집 실패 | 사용자에게 직접 노출하지 않음 | 운영 알림 표시 |
| snapshot generated(비서빙) | 서빙 대상 아님(노출하지 않음) | 빌드 완료/서빙 승인 대기로 표시, "서빙 승인" 버튼 노출 |
| snapshot approved(서빙) | 서빙·freshness 비교 대상(`as_of`는 active deployment 기준) | 서빙 가능으로 표시 |

상태 표시 원칙:

- 같은 상태명을 사용자와 운영자에게 다르게 설명할 수는 있지만, 내부 의미는 같아야 한다.
- “실패”와 “검수 필요”를 섞지 않는다.
- 사용자가 해결할 수 있는 문제와 운영자가 해결해야 하는 문제를 분리한다.
- "검수 중(처리 중)"은 "검수 필요"와 다른 상태다. 검수 필요는 아직 아무도 잡지 않은 큐 대기 상태이고, 검수 중은 특정 검수자가 claim해 처리하고 있는 상태다. 검수 큐(§4.3~§4.6)는 이 둘을 구분해 동시 작업 충돌을 화면에서 드러낸다.
- snapshot의 `generated`(비서빙)와 `approved`(서빙)는 다른 상태다. `generated`는 빌드만 완료된 상태로 사용자 서빙·노출 기준이 아니며, 데이터 관리자의 "서빙 승인"(§4.7)을 거쳐 `approved`가 된 snapshot만 서빙·freshness 비교 대상이 되며, 사용자 노출 `as_of`는 active deployment 기준으로 산정한다. 화면 상태 표기는 이 둘을 섞지 않는다.

## 7. 화면 설계 검토 기준

이 문서는 아래 질문에 답할 수 있어야 한다.

- 사용자가 작가를 찾고 작품 정보를 입력하는 화면 흐름이 명확한가?
- 동명이인 작가를 잘못 선택하지 않도록 생년, 국적, 활동지, 대표 작품 등 구분 정보가 화면에 표시되는가?
- 신규 작가 후보가 바로 최종 artist_key로 확정되지 않는가?
- 운영자가 수집 실패와 품질 미달을 구분해서 볼 수 있는가?
- 운영자가 승인/반려/보류 사유를 남길 수 있는가?
- snapshot 반영 전 보류/제외 row를 확인할 수 있는가?
- 모든 중요한 운영 판단에 처리자와 처리시각이 남는가?
