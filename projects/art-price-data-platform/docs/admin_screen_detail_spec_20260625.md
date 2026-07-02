# 작품 가격 데이터 플랫폼 어드민 화면 상세 명세

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 작품 가격 데이터 플랫폼/표준화/검수/운영 어드민 화면을 실제 프론트엔드 개발 단위로 구체화한다.

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
- [NANT 재료(지지체/매체) 분류 기준](nant_material_classification_criteria_20260626.md)

## 2. 공통 어드민 레이아웃

프론트 앱 기준:

- 어드민 화면은 별도 `admin-web` React + TypeScript SPA에 둔다.
- 어드민 route는 `/admin/art-price-data/**`로 분리하고, route guard와 공통 레이아웃을 적용한다.
- 어드민 화면의 데이터 조회/쓰기 SoT는 FastAPI/OpenAPI 기준 API다. 프론트 dev proxy나 별도 프론트 서버에 검수, snapshot, 모델 배포 쓰기 로직을 중복 구현하지 않는다.

권장 route prefix:

```text
/admin/art-price-data
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
| 수집 대시보드 | `/admin/art-price-data/collection-runs` | 운영 담당자 |
| 수집 run 상세 | `/admin/art-price-data/collection-runs/:run_id` | 운영 담당자 |
| 작품 품질 검수 | `/admin/art-price-data/review/artworks` | 운영 담당자 |
| 작가명 검수 | `/admin/art-price-data/review/artist-names` | 운영 담당자 |
| artist_key 연결 검수 | `/admin/art-price-data/review/artist-identities` | 운영 담당자(조회/triage), 키 연결 확정은 데이터 관리자 |
| 신규 작가 후보 | `/admin/art-price-data/review/new-artists` | 운영 담당자(조회/triage), 키 생성은 데이터 관리자 |
| snapshot 후보/승인 | `/admin/art-price-data/snapshots` | 운영 담당자 |
| NANT mapping 관리 | `/admin/art-price-data/nant-mapping` | 운영 담당자(조회), 편집은 데이터 분석가, active 전환은 데이터 관리자 |
| 모델 운영 | `/admin/art-price-data/model-deployments` | 데이터 분석가(학습/import job), 데이터 관리자(승인/승격/롤백/retire) |
| 운영 로그/알림 | `/admin/art-price-data/audit-logs` | 데이터 관리자 |

## 3. 수집 대시보드

Route:

```text
/admin/art-price-data/collection-runs
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
/admin/art-price-data/collection-runs/:run_id
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
/admin/art-price-data/review/artworks
```

API:

- `GET /api/v1/admin/review/artworks`
- `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision`

이 화면은 `standardization_review_item`의 작품 관련 타입(`artwork_field`, `nant_mapping`, `fx_rate`)을 작품 raw/interpreted/normalized 정보와 조인해 보여주는 화면이다.

목록 필터:

- source
- price_status
- size_status
- medium_status(파생 필터: NANT mapped/learning_excluded/review_required)
- review_status
- claim 상태

작품 품질 큐의 `review_status`는 `standardization_review_item.status`를 기준으로 하고, snapshot 포함/제외는 `artwork_snapshot_item.include_status`에서 별도로 판단한다(MySQL 5.0.2, 5.0.3.1).

테이블 컬럼:

| 컬럼 | 설명 |
|---|---|
| review_item_id | decision path parameter |
| review_type | `artwork_field`, `nant_mapping`, `fx_rate` |
| source | 원천 |
| title_raw / title_candidate | 원천명과 후보명 |
| artist_name_raw | 원천 작가명 |
| price_raw / price_krw_normalized | 원천 가격과 환산 후보 |
| size | width/height/depth 후보 |
| NANT 분류 | `nant_support`, `nant_medium`, `nant_category_key` 또는 `nant_mapping` 보류 사유 |
| quality_flags | 가격 없음, 크기 실패, NANT 제외 후보 등 |
| claim | 담당자/만료 |

상세 패널:

- 원천값
- interpreted 값
- normalized 후보값
- NANT 분류와 DB `learning_excluded` 여부
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
/admin/art-price-data/review/artist-names
```

API:

- `GET /api/v1/admin/review/artist-names`
- `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision`

이 화면은 `standardization_review_item.review_type=artist_name_ko` 또는 `artist_name_en`을 `artist_name_alias`/`normalized_artist_staging`과 조인해 보여주는 화면이다. 작가명 한글화 검수는 `artist_name_ko` 타입으로 등록한다.

정렬:

- `artist_name_ko_risk_score` 내림차순
- 영향 row 수 내림차순

테이블 컬럼:

| 컬럼 | 설명 |
|---|---|
| review_item_id | decision path parameter |
| alias_id | 대상 alias row |
| review_type | `artist_name_ko` 또는 `artist_name_en` |
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
/admin/art-price-data/review/artist-identities
```

API:

- `GET /api/v1/admin/review/artist-identities`
- `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision`

이 화면은 `standardization_review_item.review_type=artist_key`를 `artist_identity_candidate`/`artist_identity`와 조인해 보여주는 화면이다.

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

`move_to_new_artist_candidate`는 별도 `new_artist_candidate` 테이블을 뜻하지 않는다. 공통 검수 큐의 `standardization_review_item(review_type=new_artist)` 일감을 열거나 기존 열린 일감에 연결하는 화면 동작이다.

## 8. 신규 작가 후보 큐

Route:

```text
/admin/art-price-data/review/new-artists
```

API:

- `GET /api/v1/admin/review/new-artists`
- `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision`

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
/admin/art-price-data/snapshots
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
- NANT 분류 성공/학습 제외/unmapped 수
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

## 10. NANT mapping 관리 화면

Route:

```text
/admin/art-price-data/nant-mapping
```

API:

- `GET /api/v1/admin/nant/mapping-versions`
- `POST /api/v1/admin/nant/mapping-versions/import`
- `POST /api/v1/admin/nant/mapping-versions/{mapping_version_id}/validate`
- `POST /api/v1/admin/nant/mapping-versions/{mapping_version_id}/activate`
- `GET /api/v1/admin/nant/mappings`
- `POST /api/v1/admin/nant/mappings`
- `PATCH /api/v1/admin/nant/mappings/{material_mapping_id}`
- `DELETE /api/v1/admin/nant/mappings/{material_mapping_id}`
- `GET /api/v1/admin/nant/unmapped-materials`

주요 영역:

- active mapping version 요약
- draft/import version 목록
- validation 결과
- mapping row 검색/필터
- unmapped 재료 목록
- draft row 편집 패널
- activate 영향 범위 안내

목록 필터:

- version status: draft/active/archived
- mapping filter: mapped/learning_excluded/unmapped. `learning_excluded`는 mapping row의 값이며 `normalized_artwork_staging` 저장 컬럼이 아님
- source material 검색
- NANT support/medium
- learning_excluded 여부

테이블 컬럼:

| 컬럼 | 설명 |
|---|---|
| source_material_text | 원천/표준화 재료 표현 |
| nant_support / nant_medium | NANT 지지체/매체 |
| nant_category_key | 95개 허용 조합 key |
| learning_excluded | 학습 제외 여부 |
| learning_exclusion_reason | 제외 사유 |
| raw_note2 | CSV `비고2` 또는 admin 메모 |
| updated_by / updated_at | 마지막 수정자/시각 |

버튼/API 매핑:

| 버튼 | API | 권한 |
|---|---|---|
| CSV import로 draft 생성 | `POST /mapping-versions/import` | 데이터 분석가 |
| draft row 추가 | `POST /mappings` | 데이터 분석가 |
| draft row 수정 | `PATCH /mappings/{material_mapping_id}` | 데이터 분석가 |
| draft row 삭제 | `DELETE /mappings/{material_mapping_id}` | 데이터 분석가 |
| validation 실행 | `POST /mapping-versions/{mapping_version_id}/validate` | 데이터 분석가 |
| active 전환 | `POST /mapping-versions/{mapping_version_id}/activate` | 데이터 관리자 |

상태/제약:

- active/archived version row는 수정 버튼을 비활성화한다.
- validation failed 상태에서는 active 전환 버튼을 비활성화한다.
- active 전환은 현재 active를 archived로 닫고 대상 draft를 active로 올리는 단일 트랜잭션이어야 한다.

## 11. 모델 운영 화면

Route:

```text
/admin/art-price-data/model-deployments
```

API:

- `POST /api/v1/admin/model-training/jobs`
- `GET /api/v1/admin/model-training/jobs`
- `GET /api/v1/admin/model-training/jobs/{training_job_id}`
- `GET /api/v1/admin/model-versions`
- `GET /api/v1/admin/model-versions/{model_version}`
- `POST /api/v1/admin/model-versions/{model_version}/decision`
- `POST /api/v1/admin/model-deployments`
- `GET /api/v1/admin/model-deployments/current`

주요 영역:

- 현재 active deployment
- 학습/import job 목록과 상태
- 모델 candidate/approved 목록
- 학습 snapshot/export 연결
- validation/test 요약
- gate 결과(data contract, fixed-test parity, API smoke)
- artifact URI/SHA-256, feature schema hash
- promote/rollback/retire 액션

버튼/API 매핑:

| 버튼 | action | 권한 |
|---|---|---|
| 학습/import job 생성 | `POST /model-training/jobs` | 데이터 분석가 |
| 후보 승인 | `POST /model-versions/{model_version}/decision`, `decision=approve` | 데이터 관리자 |
| 후보 반려 | `POST /model-versions/{model_version}/decision`, `decision=reject` | 데이터 관리자 |
| 운영 승격 | `POST /model-deployments`, `action=promote` | 데이터 관리자 |
| 롤백 | `POST /model-deployments`, `action=rollback` | 데이터 관리자 |
| retired 처리 | `POST /model-deployments`, `action=retire` | 데이터 관리자 |

표시 규칙:

- `candidate`는 운영 중 모델이 아니며 승격 버튼을 노출하지 않는다.
- `approved` 모델에만 운영 승격 버튼을 노출한다.
- 현재 운영 중 여부는 `price_model_registry.model_status`가 아니라 `price_model_deployment.deployment_status=active`로 표시한다.
- active deployment의 `training_snapshot_id`, `source_cutoff_at`, `model_version`, `deployment_id`를 상단에 고정 표시한다.
- job 실패 row는 error 요약과 재실행 버튼을 보여주되, 기존 job을 덮어쓰지 않고 새 job을 만든다.

## 12. 운영 로그/알림

Route:

```text
/admin/art-price-data/audit-logs
```

API:

- `GET /api/v1/admin/audit-logs`

필터:

- actor
- entity_type(`collection_run`, `artwork`, `artist_name`, `artist_identity`, `snapshot`, `model_training_job`, `model_version`, `model_deployment`, `nant_mapping_version`, `nant_material_mapping`)
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

주의:

- 운영 로그 화면은 별도 audit 테이블을 전제로 하지 않는다. API `10.1`이 도메인별 SoT 테이블의 처리자/시각/사유를 합쳐 제공하며, 모델 운영과 NANT mapping 변경도 동일 화면에서 조회 가능해야 한다.

## 13. 공통 완료 기준

- 모든 쓰기 액션은 reason 입력을 요구한다.
- 상태 전이 decision API는 `expected_review_status`를 보낸다(`recheck`/`recheck_candidates` 제외).
- 생성/승인 계열은 `idempotency_key`를 보낸다.
- claim된 row는 담당자와 만료 상태를 표시한다.
- 사용자 화면에 노출 금지인 원천 URL/source/internal ID는 어드민에서만 표시한다.
