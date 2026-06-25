# Track6 어드민 화면 상세 명세

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 Track6 데이터 수집/표준화/검수/운영 어드민 화면을 실제 프론트엔드 개발 단위로 구체화한다.

상위 화면 구조는 [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)을 따르고, API 기준은 [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)을 따른다.

관련 문서:

- [PRD](product_requirements_20260625.md)
- [1차 개발 로드맵](first_development_roadmap_20260625.md)
- [1차 개발 백로그](first_development_backlog_20260625.md)
- [화면 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)
- [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md)
- [프론트 마이크로카피 기준](frontend_microcopy_spec_20260625.md)
- [API mock/fixture 기준](frontend_api_mock_fixtures_20260625.md)
- [프론트 E2E 테스트 계획](frontend_e2e_test_plan_20260625.md)

## 2. 공통 어드민 레이아웃

권장 route prefix:

```text
/admin/track6
```

공통 레이아웃:

- 좌측 navigation
- 상단 현재 source/snapshot/model 상태 요약
- 본문 필터/목록/상세 영역
- 처리 결과 toast 또는 inline banner
- 권한 부족 또는 로그인 만료 상태 처리

공통 navigation:

| 메뉴 | Route | 최소 권한 |
|---|---|---|
| 수집 대시보드 | `/admin/track6/collection-runs` | 운영 담당자 |
| 수집 run 상세 | `/admin/track6/collection-runs/:run_id` | 운영 담당자 |
| 작품 품질 검수 | `/admin/track6/review/artworks` | 운영 담당자 |
| 작가명 검수 | `/admin/track6/review/artist-names` | 운영 담당자 |
| artist_key 연결 검수 | `/admin/track6/review/artist-identities` | 운영 담당자(조회/triage), 키 연결 확정은 데이터 관리자 |
| 신규 작가 후보 | `/admin/track6/review/new-artists` | 운영 담당자(조회/triage), 키 생성은 데이터 관리자 |
| snapshot 후보/승인 | `/admin/track6/snapshots` | 운영 담당자 |
| 모델 배포 | `/admin/track6/model-deployments` | 데이터 관리자 |
| 운영 로그/알림 | `/admin/track6/audit-logs` | 데이터 관리자 |

## 3. 수집 대시보드

Route:

```text
/admin/track6/collection-runs
```

API:

- `GET /api/v1/admin/collection-runs/summary`
- `GET /api/v1/admin/collection-runs`

주요 영역:

| 영역 | 내용 |
|---|---|
| 상단 요약 | 마지막 수집 시각, 전체 상태, snapshot 후보 수, 검수 큐 수 |
| source 카드 | source별 run 상태, raw/normalized row, 실패율, 품질 상태 |
| 필터 | 기간, source, status, quality_status |
| run 테이블 | run id, source, started/finished, status, quality_status, row 수, 실패 수, 액션 |

필수 상태:

- loading: skeleton table
- empty: 조회 기간에 run 없음
- error: 대시보드 조회 실패, 재시도 버튼
- stale: 마지막 수집 기준이 `FRESH-WARN-N` 초과이면 경고 badge

액션:

| 액션 | 조건 | API |
|---|---|---|
| run 상세 보기 | 모든 row | 상세 route 이동 |
| 실패분 재수집 | `failed` 또는 `partial_success` | `POST /collection-runs/{run_id}/actions`, `action=request_retry`, `scope=failed_only` |
| 전체 재수집 | 운영 담당자(비용 큼 → confirm dialog 필수, 역할 게이트는 실패분 재수집과 동일) | `POST /collection-runs/{run_id}/actions`, `scope=full` |

## 4. 수집 run 상세

Route:

```text
/admin/track6/collection-runs/:run_id
```

API:

- `GET /api/v1/admin/collection-runs/{run_id}`
- `POST /api/v1/admin/collection-runs/{run_id}/actions`

주요 영역:

| 영역 | 내용 |
|---|---|
| run summary | source, status, failure_type, quality_status, started/finished, collector_version |
| 요청/응답 지표 | total_requested, total_success, total_failed, raw/interpreted/normalized row |
| 실패 URL 목록 | fetch_type, url_sanitized, http_status, error_message |
| 품질 flags | 가격/크기/작가명 보유율, parser error, blocked/rate_limited |
| 처리 이력 | approved_by, approved_at, approval_note, override_reason |

액션:

- 실패분 재수집
- run 반영 승인
- run 보류
- source 일시 중지 상태 확인

## 5. 작품 품질 검수 큐

Route:

```text
/admin/track6/review/artworks
```

API:

- `GET /api/v1/admin/review/artworks`
- `POST /api/v1/admin/review/artworks/{normalized_artwork_id}/decision`

목록 필터:

- source
- price_status
- size_status
- medium_status
- review_status
- claim 상태

작품 품질 큐의 `review_status`는 저장된 컬럼이 아니라 `quality_flags_json` + `artwork_snapshot_item.include_status`에서 파생한 필터값이다(MySQL 5.0.2). 작가명/identity 큐의 `review_status`와 값 집합이 다르다.

테이블 컬럼:

| 컬럼 | 설명 |
|---|---|
| normalized_artwork_id | decision path parameter |
| source | 원천 |
| title_raw / title_candidate | 원천명과 후보명 |
| artist_name_raw | 원천 작가명 |
| price_raw / price_krw_normalized | 원천 가격과 환산 후보 |
| size | width/height/depth 후보 |
| quality_flags | 가격 없음, 크기 실패, 제외 후보 등 |
| claim | 담당자/만료 |

상세 패널:

- 원천값
- interpreted 값
- normalized 후보값
- 원천 URL
- 변경 patch 입력
- reason 입력

버튼/API 매핑:

| 버튼 | decision | 필수 입력 |
|---|---|---|
| 승인 | `approve` | reason |
| 수정 후 승인 | `approve_with_patch` | patch, reason |
| 보류 | `hold` | reason |
| 제외 | `exclude` | exclude_reason, reason |

상태 전이 decision은 `expected_review_status`를 함께 보낸다. `recheck_candidates`는 상태 전이가 아니므로 제외한다(아래 주의 참조).

## 6. 작가명 검수 큐

Route:

```text
/admin/track6/review/artist-names
```

API:

- `GET /api/v1/admin/review/artist-names`
- `POST /api/v1/admin/review/artist-names/{alias_id}/decision`

정렬:

- `artist_name_ko_risk_score` 내림차순
- 영향 row 수 내림차순

테이블 컬럼:

| 컬럼 | 설명 |
|---|---|
| alias_id | decision path parameter |
| source | 원천 |
| artist_name_raw | 원천 작가명 |
| display_name_ko/en 후보 | 서비스 표시 후보 |
| input_type | 한글화 입력 유형 |
| reason code | 한글화 reason |
| risk score | 위험 점수 |
| override status | override 등록 여부 |
| claim | 담당자/만료 |

버튼/API 매핑:

| 버튼 | decision |
|---|---|
| 표시명 승인 | `approve` |
| 표시명 수정 후 승인 | `approve_with_edit` |
| override 등록 | `register_override` |
| alias 추가 | `add_alias` |
| 후보 재검색 | `recheck_candidates` |
| 보류 | `hold` |
| 반려 | `reject` |

주의:

- `approve`와 `add_alias`는 별도 동작이다.
- `recheck_candidates`는 상태 전이가 아니므로 conflict 검사 대상이 아니다.

## 7. artist_key 연결 검수 큐

Route:

```text
/admin/track6/review/artist-identities
```

API:

- `GET /api/v1/admin/review/artist-identities`
- `POST /api/v1/admin/review/artist-identities/{candidate_id}/decision`

권한:

- 조회/후보 반려/보류/신규 후보 전환: 운영 담당자 이상
- 기존 `artist_key` 연결 확정(`approve_existing_artist_key`): 데이터 관리자 이상

상세 비교 영역:

| 영역 | 내용 |
|---|---|
| 신규 원천 작가 | source, artist_source_id, 원천명, 생년, 국적, 활동지 |
| 기존 후보 | artist_key, 표시명, 생년, 국적, 대표 작품 |
| 매칭 근거 | alias_exact, alias_approved, fuzzy, birth_year_confidence |
| 충돌 정보 | 생년/국적/활동지/alias 충돌 |
| 영향 범위 | 연결 시 영향 row 수 |

버튼/API 매핑:

| 버튼 | decision | 필수 입력 | 최소 권한 |
|---|---|---|---|
| 기존 artist_key 연결 승인 | `approve_existing_artist_key` | artist_key, reason | 데이터 관리자 |
| 후보 반려 | `reject_candidate` | reason | 운영 담당자 |
| 보류 | `hold` | reason | 운영 담당자 |
| 신규 작가 후보로 전환 | `move_to_new_artist_candidate` | reason | 운영 담당자 |

## 8. 신규 작가 후보 큐

Route:

```text
/admin/track6/review/new-artists
```

API:

- `GET /api/v1/admin/review/new-artists`
- `POST /api/v1/admin/review/new-artists/{candidate_id}/decision`

권한:

- 조회/기존 후보 재검색/보류/반려: 운영 담당자 이상
- 신규 `artist_key` 생성 승인(`approve`): 데이터 관리자 이상

버튼/API 매핑:

| 버튼 | decision | 최소 권한 |
|---|---|---|
| 신규 artist_key 생성 승인 | `approve` | 데이터 관리자 |
| 기존 후보 재검색 | `recheck` | 운영 담당자 |
| 보류 | `hold` | 운영 담당자 |
| 반려 | `reject` | 운영 담당자 |

주의:

- `approve`만 최종 `artist_key`를 생성한다.
- `approve`는 `idempotency_key`가 필수다.

## 9. Snapshot 후보/승인 화면

Route:

```text
/admin/track6/snapshots
```

API:

- `GET /api/v1/admin/snapshots/candidates/summary`
- `GET /api/v1/admin/snapshots/candidates/items`
- `POST /api/v1/admin/snapshots/requests`
- `POST /api/v1/admin/snapshots`
- `POST /api/v1/admin/snapshots/{snapshot_id}/approve`

상단 summary:

- 후보 row 수
- 포함 가능 row 수
- 제외 row 수
- 보류 row 수
- source별 row 수
- 가격 보유율
- 크기 파싱 성공률
- 작가 확정률
- 직전 snapshot 대비 변화량

상태 표시(badge enum 단일 기준: [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md) §4, API 기획 §2.6/§9.3):

snapshot 계열은 `snapshot_request`와 `artwork_snapshot` 두 엔터티로 나뉘며 `approved` 문자열이 두 레이어에 모두 있으므로 화면 라벨로 구분한다.

| 레이어 | 상태 | 화면 라벨 | 사용자 기준 여부 |
|---|---|---|---|
| snapshot_request | requested | 확정요청됨 | 아님 |
| snapshot_request | approved | 생성승인됨 | 아님 |
| snapshot_request | generating | 생성 진행 중 | 아님 |
| snapshot_request | generated | 생성 완료(요청 terminal) | 아님 |
| snapshot_request | rejected | 요청 반려 | 아님 |
| snapshot_request | failed | 생성 실패 | 아님 |
| snapshot_request | cancelled | 요청 취소 | 아님 |
| artwork_snapshot | building | 생성 중 | 아님 |
| artwork_snapshot | generated | 빌드완료(비서빙) | 아님 |
| artwork_snapshot | approved | 서빙승인 | 사용자 기준 |
| artwork_snapshot | failed | 생성 실패 | 아님 |
| artwork_snapshot | discarded | 폐기 | 아님 |

버튼/API 매핑:

| 버튼 | 권한 | API |
|---|---|---|
| 확정요청 | 운영 담당자 | `POST /snapshots/requests` |
| 생성승인 | 데이터 관리자 | `POST /snapshots` |
| 서빙승인 | 데이터 관리자 | `POST /snapshots/{snapshot_id}/approve` |
| 후보 목록 다운로드 | 운영 담당자 | `GET /snapshots/candidates/items` |

## 10. 모델 배포 화면

Route:

```text
/admin/track6/model-deployments
```

API:

- `GET /api/v1/admin/model-versions`
- `GET /api/v1/admin/model-versions/{model_version}`
- `POST /api/v1/admin/model-deployments`
- `GET /api/v1/admin/model-deployments/current`

주요 영역:

- 현재 active deployment
- 모델 후보 목록
- 학습 snapshot 연결
- validation/test 요약
- promote/rollback/retire 액션

버튼/API 매핑:

| 버튼 | action | 권한 |
|---|---|---|
| 승격 | `promote` | 데이터 관리자 |
| 롤백 | `rollback` | 데이터 관리자 |
| retired 처리 | `retire` | 데이터 관리자 |

## 11. 운영 로그/알림

Route:

```text
/admin/track6/audit-logs
```

API:

- `GET /api/v1/admin/audit-logs`

필터:

- actor
- entity_type
- action
- source
- 기간
- request_id

테이블 컬럼:

- occurred_at
- actor_id
- action
- entity_type
- entity_id
- before/after 요약
- reason
- request_id

## 12. 공통 완료 기준

- 모든 쓰기 액션은 reason 입력을 요구한다.
- 상태 전이 decision API는 `expected_review_status`를 보낸다(`recheck`/`recheck_candidates` 제외).
- 생성/승인 계열은 `idempotency_key`를 보낸다.
- claim된 row는 담당자와 만료 상태를 표시한다.
- 사용자 화면에 노출 금지인 원천 URL/source/internal ID는 어드민에서만 표시한다.
