# 작품 가격 데이터 플랫폼 1차 개발 백로그

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 1차 개발 로드맵을 실제 개발 추적 단위로 나눈 백로그다.

각 항목은 Epic, Task, 선행 조건, 산출물, 완료 기준, 검증 방법을 포함한다. 작업 상세 설계는 관련 문서를 따른다.

관련 문서:

- [PRD](product_requirements_20260625.md)
- [1차 개발 로드맵](first_development_roadmap_20260625.md)
- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
- [사용자 화면 상세 명세](user_frontend_screen_spec_20260625.md)
- [어드민 화면 상세 명세](admin_screen_detail_spec_20260625.md)
- [프론트 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)
- [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md)
- [프론트 API Mock / Fixture 기준](frontend_api_mock_fixtures_20260625.md)
- [프론트 E2E 테스트 계획](frontend_e2e_test_plan_20260625.md)
- [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [NANT 재료(지지체/매체) 분류 기준](nant_material_classification_criteria_20260626.md)
- [운영 파라미터](operational_parameters_20260625.md)

## 2. 백로그 상태값

| 상태 | 의미 |
|---|---|
| `todo` | 아직 시작하지 않음 |
| `ready` | 선행 조건 충족, 개발 착수 가능 |
| `in_progress` | 개발 중 |
| `blocked` | 외부 결정/선행 작업 필요 |
| `review` | 코드/문서 검토 중 |
| `done` | 완료 기준과 검증 통과 |

이 문서의 표는 착수 시점 기준 전부 `todo`다. 실제 상태/담당/규모는 이슈 트래커 카드(§16 템플릿)에서 관리하고, 이 문서는 Task 정의(선행/산출물/완료기준/검증)의 SoT로만 유지한다.

## 3. 우선순위 기준

| 우선순위 | 의미 |
|---|---|
| P0 | 1차 개발 기반. 지연되면 **다른 트랙이 막힘**(차단). 같은 Epic 안에서도 차단 효과가 없으면 P0가 아니다 |
| P1 | 1차 개발 필수 기능. 차단은 아님 |
| P2 | 1차 개발 포함 기능이지만 P0/P1 이후 병렬 진행 가능 |

P0는 "중요"가 아니라 "차단"으로만 부여한다. 한 Epic의 모든 Task가 P0가 되면 우선순위 신호가 사라지므로, 스프린트 계획 시 실제 cross-track 차단 Task만 P0로 유지한다.

**`(gate)` 표기**: 출시에는 반드시 필요하지만 **P0 빌드 트랙을 막지는 않는** 작업(사용자/어드민 화면, 통합 검증)은 `P1 (gate)`로 표기한다. 스케줄 우선순위는 P1(빌드 이후)이지만 1차 완료 정의(§13 Epic 9 / PRD §10)에는 필수다. 이들에 의존하는 후행은 운영 runbook(E8-T06)·통합 검증(E9)뿐이고 그 작업들도 gate/P1이라, gate를 미루어도 어떤 P0 빌드 트랙도 멈추지 않는다.

**`(M1-gate)` 표기**: P0 빌드 트랙은 아니지만 M1 완료 판정에 필요한 화면/흐름이다. 예를 들어 사용자 신규 작가 후보 제출 화면과 신규 후보 최소 큐는 M1-gate다.

**`(M2-gate)` 표기**: M1 수직 슬라이스를 막지는 않지만 M2 폭 확장과 1차 최종 완료에는 필수인 작업이다. 대표적으로 Art1 외 원천 연결처럼 M1 검증 후 확장하는 작업에 쓴다. 사용자 신규 작가 후보 제출은 M1 포함으로 확정되어 M2-gate가 아니다.

선행 조건이 Epic 단위(예: `E3/E4`)로 적힌 항목은 **해당 Epic의 P0 및 gate 계열 Task 완료**를 의미한다(`(gate)`, `(M1-gate)`, `(M2-gate)` 포함). Task 단위 의존이 명확한 경우는 Task ID로 적는다.

## 4. Epic 0. API/DB/운영 기준 확정

목표:

- 구현 전에 API, DB, 상태값, 권한, 운영 임계치, 계산 기준을 확정한다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E0-T01 | MySQL DDL 초안 작성 | P0 | MySQL 문서 | migration 초안 | SoT 테이블/enum/FK/unique가 반영됨 | DDL review |
| E0-T02 | OpenAPI 초안 작성 | P0 | API 문서 | `openapi/art_price_data_platform_v1.yaml` | request/response/status/error/pagination 반영 | schema lint |
| E0-T03 | API enum/status/error 표 정리 | P0 | API/DB 문서 | enum matrix | API/DB/화면 상태값 충돌 없음 | 문서 review |
| E0-T04 | 사용자 API 인증/rate limit 기준 확정 | P0 | PRD | 인증/사용량 기준 | 익명/로그인/rate limit/abuse 대응 결정 | 보안 review |
| E0-T05 | suppression/do-not-train/do-not-show 기준 확정 | P0 | PRD/운영 문서 | 개인정보 처리 기준 | 서비스 노출/snapshot/model 반영 차단 흐름 확정 | privacy review |
| E0-T06 | 1차 시장 가격 카드 계산 기준 확정 | P0 | PRD/API 문서 | 계산 기준 문서 | 최소 N, 이상치, 매체 그룹, 호당 환산 기준 확정 | 샘플 계산 review |
| E0-T07 | 운영 파라미터 seed 정의 | P1 | 운영 파라미터 문서 | seed 파일 | 운영 파라미터 문서 A~H의 **모든 키**가 seed에 존재하고 기본값과 일치 | seed load test + 키 누락 0건 assert |
| E0-T08 | 어드민 계정 부트스트랩 기준 확정 | P0 | E0-T04 | 부트스트랩 기준/스크립트 | 초기 슈퍼유저 생성, 역할 위계, audit actor 주체 확정 | 첫 어드민 로그인 + 검수 화면 접근 |
| E0-T09 | NANT 분류 기준 DB seed/fixture 확정 | P0 | NANT 분류 기준 문서 | NANT CSV import fixture, mapping DB seed, version/file hash | 기준 조합 95개와 CSV `비고2` -> DB `learning_excluded` 변환 규칙이 seed/fixture에 고정됨 | CSV import validation test |

## 5. Epic 1. DB/migration/object storage 기반

목표:

- raw 수집부터 snapshot/model deployment까지 저장할 영속 기반을 만든다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E1-T01 | migration 실행 구조 마련 | P0 | E0-T01 | migration runner | dev DB에 up/down 가능 | migration test |
| E1-T02 | source/run/raw 테이블 구현 | P0 | E1-T01 | `source_registry`, `collector_run`, `raw_fetch` | single-flight 제약 포함 | DB constraint test |
| E1-T03 | raw structured 테이블 구현 | P0 | E1-T02 | `source_artwork_raw`, `source_artist_raw` | run/source/id 유니크 반영 | insert idempotency test |
| E1-T04 | interpreted/normalized 테이블 구현 | P0 | E1-T03 | 4개 staging 테이블 | quality flag/parsed json 포함 | migration test |
| E1-T05 | artist identity 테이블 구현 | P0 | E1-T04 | alias/candidate/identity/event/version/history | identity event append-only 기준 반영 | DB test |
| E1-T06 | snapshot 테이블 구현 | P0 | E1-T05 | snapshot/request/item | generated/approved 분리, active request lock 반영 | transition test |
| E1-T07 | model training/registry/deployment/log 테이블 구현 | P1 | E1-T06 | `model_training_job`, registry/deployment/log 테이블 | active deployment route lock, training job 상태, registry candidate/approved 상태 반영 | DB test |
| E1-T08 | object storage payload store 구현 | P0 | E1-T03 | payload writer/reader | DB에는 path/hash/size만 저장 | unit/integration test |
| E1-T09 | suppression 저장 구조 구현 | P0 | E0-T05 | 컬럼 또는 테이블 | 서비스 노출/snapshot 제외에 쓸 수 있음 | DB/query test |
| E1-T10 | NANT mapping 관리 테이블 구현 | P0 | E0-T09, E1-T01 | `nant_mapping_version`, `nant_allowed_category`, `nant_material_mapping`, `artwork_nant_classification` | active version 단일성, draft-only edit, category/mapping unique 제약 반영 | migration/constraint test |

## 6. Epic 2. Collector 공통 인터페이스와 raw 적재

목표:

- 4개 원천 collector가 같은 run/raw 처리 기준으로 동작한다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E2-T01 | collector result schema 정의 | P0 | E0-T03 | Python schema/dataclass | 4개 원천 공통 필드 표현 가능 | type/unit test |
| E2-T02 | DB writer 구현 | P0 | E1-T02/E1-T03 | writer module | run/raw/source row 적재 가능 | integration test |
| E2-T03 | HTTP client/backoff/UA 정책 적용 | P1 | E0-T07 | http client | source_registry 설정 사용 | unit test |
| E2-T04 | Art1 raw 적재 연결 | P0 | E2-T02 | Art1 collector DB path | full/list/detail raw 적재 | fixture run |
| E2-T05 | Print Bakery raw 적재 연결 | P1 (M2-gate) | E2-T02 | Print Bakery collector DB path | Cafe24/API/HTML fallback 적재 | fixture run |
| E2-T06 | Artsy DB writer/backfill 연결 | P1 (M2-gate) | E2-T02 | Artsy adapter | 기존 CSV/export 결과 적재 | backfill test |
| E2-T07 | Saatchi DB writer/backfill 연결 | P1 (M2-gate) | E2-T02 | Saatchi adapter | 기존 CSV/export 결과 적재 | backfill test |
| E2-T08 | manual CSV upload run 생성 | P1 | E1-T02 | manual import job | mapping 승인 후 run 생성 | integration test |
| E2-T09 | collector watchdog 구현 | P1 | E1-T02 | watchdog job | stuck run failed 전환 | watchdog test |

## 7. Epic 3. Interpreted/normalized 파이프라인

목표:

- 원천별 데이터를 공통 표준화 후보로 변환하고 품질 지표를 만든다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E3-T01 | 작품 interpreted job 구현 | P0 | E2-T04 (M2: +E2-T05~T07) | artwork parser job | 가격/크기/재료/상태 후보 추출 | parser fixture test |
| E3-T02 | 작가 interpreted job 구현 | P0 | E2-T04 (M2: +E2-T05~T07) | artist parser job | 이름/생년/국적/활동지 후보 추출 | parser fixture test |
| E3-T03 | 작품 normalized job 구현 | P0 | E3-T01 | artwork normalizer | 공통 컬럼/quality flag 생성 | integration test |
| E3-T04 | 작가 normalized job 구현 | P0 | E3-T02 | artist normalizer | 표시명/source artist key/상태 생성 | integration test |
| E3-T05 | 환율/KRW 환산 구현 | P1 | E1-T06/E3-T03 | fx job | point-in-time 환산 저장 | calculation test |
| E3-T06 | unmapped 리포트 구현 | P1 | E3-T03 | material/support report | 미매핑 항목 집계 | report test |
| E3-T07 | run 품질 감사 구현 | P1 | E3-T03/E3-T04 | quality audit job | 보유율/성공률/차단 기준 산출 | audit test |
| E3-T08 | NANT 지지체/매체 95분류 구현 | P0 | E1-T10, E3-T03 | NANT classification job | active DB mapping version으로 normalized 작품 row에 `nant_support`/`nant_medium`/`nant_category_key`/mapping version/status가 생성됨 | 95 category fixture + mapping test |
| E3-T09 | NANT 학습 제외 필터 구현 | P0 | E3-T08 | snapshot exclusion flag | DB mapping row의 `learning_excluded=true` row는 학습 snapshot/export/model feature 생성에서 제외되고 raw/staging은 보존됨 | exclusion test + 기존 hard-code filter 미사용 test |
| E3-T10 | 레이어 수정/재처리 정책 가드 | P0 | E3-T03, E3-T04 | mutation policy tests + service guards | raw/source raw 직접 수정 금지, normalized 직접 patch 금지, override/change_event 경로 사용, snapshot 참조 row 보존, current cache rebuild 경로 검증 | DB constraint/service test |

## 8. Epic 4. 작가명/artist_key 표준화와 검수 큐

목표:

- artist_key를 안전하게 확정하고 검수 큐로 운영 가능하게 만든다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E4-T01 | artist_name_alias 후보 생성 | P0 | E3-T04 | alias job | alias/review_status 생성 | unit/integration test |
| E4-T02 | 한글명 risk/reason/override 계산 | P1 | E4-T01 | name quality job | risk score/reason/override status 생성 | sample review |
| E4-T03 | 기존 source artist 연결 확인 | P0 | E4-T01 | identity matching job | 같은 source+artist_source_id 자동 연결 | integration test |
| E4-T04 | identity candidate 생성 | P0 | E4-T01 | candidate job | alias 기반 후보 생성 | integration test |
| E4-T05 | 자동 확정 규칙 구현 | P0 | E4-T04 | auto approval logic | 승인 alias+고신뢰 생년+충돌 없음만 자동 확정 | rule test |
| E4-T06 | 신규 작가 후보 큐 생성 | P0 | E4-T04 | physical new artist candidate queue | 사용자 후보 제출을 받고 승인 전 artist_key 미생성 | query/API test |
| E4-T07 | identity_event_log 기록 | P0 | E4-T05 | event writer | 연결/생성/merge/un-merge append-only | event test |
| E4-T08 | 영향 범위 조회 구현 | P1 | E4-T07 | impact query | row -> snapshot -> model/deployment 추적 | query test |
| E4-T09 | artist_profile_item/current 구현 | P0 | E4-T05, E4-T06 | profile item table + current summary build job | 확정 artist_key의 프로필/메타를 `artist_profile_item`에 항목 단위 저장하고 `artist_profile_current`는 현재 요약/cache로 생성. `artist_identity`에 bio/학력/전시/팔로워를 몰아넣지 않음 | DB/query test |

## 9. Epic 5. Snapshot/export/model deployment

목표:

- 검수된 데이터를 학습/운영 가능한 snapshot과 모델 배포 이력으로 연결한다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E5-T01 | snapshot 후보 summary/items query | P0 | E3-T03, E3-T04, E3-T09, E4-T05 | query/service | 포함/제외/보류/품질 요약 제공. NANT 제외 사유(`nant_learning_excluded`, `nant_unmapped`) 포함(상세 품질감사는 E3-T07로 보강) | query test |
| E5-T02 | snapshot 확정요청 구현 | P0 | E5-T01 | request API/job | 운영자 요청 생성, 멱등 처리 | API test |
| E5-T03 | snapshot 생성승인 구현 | P0 | E5-T02 | create job/API | generated snapshot 생성 | transition test |
| E5-T04 | snapshot 서빙승인 구현 | P0 | E5-T03 | approve API | approved 상태 전이 | transition test |
| E5-T05 | parquet export/manifest 구현 | P0 | E5-T03 | export files | 같은 입력/규칙이면 재현 가능 | deterministic test |
| E5-T06 | CSV export 구현 | P2 | E5-T05 | review/share CSV | 검수/공유/호환용 생성 | export test |
| E5-T07 | model training/import job 구현 | P1 | E5-T05, E1-T07 | `model_training_job` service | approved snapshot/export 기준으로 학습/import job 생성, 상태 추적, artifact/hash/metric 기록 가능 | job state/API test |
| E5-T08 | model registry + candidate 승인 구현 | P0 | E5-T05, E1-T07 | model registration/approval | job 또는 seed/import 결과를 `candidate`로 등록하고, 같은 Warm/Cold model family/contract 안에서 gate 통과 모델만 `approved` 전환 가능. family/contract 변경은 승인 불가 | API/DB/permission test |
| E5-T09 | model deployment 구현 | P0 | E5-T08 | deployment service | `approved` 모델만 active/rollback 전이, candidate 직접 배포 금지 | transition test |
| E5-T10 | prediction log 구현 | P0 | E5-T09 | log writer | model/deployment/route 추적 가능 | API test |
| E5-T11 | M1 joblib 모델 번들/feature store 연결 | P0 | E5-T05, E5-T08, E5-T09 | Warm joblib + Cold k80 joblib freeze/parity + serving adapter + active deployment seed | Art1 M1 예측 API가 Warm joblib와 Cold k80 joblib active deployment 기준으로 응답하고 `model_version`/`deployment_id`/`route`를 남김 | Warm/Cold joblib smoke + fixed-test parity + prediction log test |

E5-T11 세부 산출물:

- Cold k80: `projects/art-price-data-platform/models/cold_k80_conservative_official_v0.1_candidate/runtime_store.joblib`
- Cold k80 predictor module: `predict_cold_k80_conservative_v0_1.py` 또는 동등한 import 가능한 entrypoint
- Warm/Cold model manifest 또는 model card
- fixed test parity report와 serving smoke fixture
- `model_training_job` import/seed 이력 또는 동등한 seed manifest
- `price_model_registry` / `price_model_deployment` active seed

## 10. Epic 6. API 구현

목표:

- 사용자/어드민/job 기능을 API로 제공한다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E6-T01 | 공통 인증/권한/actor 주입 | P0 | E0-T04 | auth middleware | body actor_id 금지 | API test |
| E6-T02 | error envelope/request id 구현 | P0 | E0-T02 | error handler | 공통 에러 형식 반환 | API test |
| E6-T03 | idempotency/expected status 유틸 구현 | P0 | E0-T03 | API utility | 중복 생성/동시 충돌 방지 | concurrency test |
| E6-T04 | public artist/search/candidate API | P0 | E4-T04, E4-T06 | public API | M1에서 artist search와 신규 작가 후보 제출을 모두 포함. 두 경로 모두 원천 정보 비노출 | schema/API test |
| E6-T05 | public price prediction API | P0 | E5-T10, E5-T11, E6-T04, E0-T06 | prediction endpoint | active deployment 기준 model/as_of/card 포함, prediction log 기록 | API test |
| E6-T06 | admin collection/source/manual import API | P1 | E2/E3 | admin APIs | 대시보드/run/source/upload 처리 | API test |
| E6-T07 | admin review APIs | P0 | E4 | review APIs | queue/decision/claim 처리 | API/concurrency test |
| E6-T08 | snapshot APIs | P0 | E5 | snapshot APIs | 3단계 전이 제공 | API test |
| E6-T09 | model operation APIs | P1 | E5 | model-training/registry/deployment APIs | 학습/import job, registry, candidate 승인/반려, deployment/current 제공 | API/permission test |
| E6-T10 | audit log/impact APIs | P1 | E4/E5 | audit APIs | 운영 추적 가능 | API test |
| E6-T11 | freshness 상태 계산 API | P1 | E6-T05 | freshness fields | `FRESH-WARN-N`/`FRESH-HIDE-M`/`FRESH-MODEL-GAP` 임계로 as_of 신선도 상태 반환 | API test |
| E6-T12 | admin NANT mapping 관리 API | P1 (gate) | E1-T10, E3-T09 | version/import/mapping/unmapped/activate APIs | draft 생성/수정, unmapped 조회, validation, active 전환 가능. active version 직접 수정 불가 | API/permission/constraint test |

## 11. Epic 7. 사용자/어드민 화면

목표:

- 사용자와 운영자가 API 기능을 화면에서 사용할 수 있게 한다.

구현 기준:

- 프론트는 `service-web`과 `admin-web` 두 앱으로 분리한다. `service-web`은 Next.js + React + TypeScript, `admin-web`은 React + TypeScript SPA다.
- 두 앱은 OpenAPI 기반 `packages/api-client`와 공통 UI primitive만 공유하고, 비즈니스 쓰기 로직은 FastAPI/OpenAPI API를 호출한다.
- 사용자 화면 상세는 `user_frontend_screen_spec_20260625.md`를 따른다.
- 어드민 화면 상세는 `admin_screen_detail_spec_20260625.md`를 따른다.
- 공통 상태/에러/claim/conflict/freshness UX는 `frontend_state_error_ux_spec_20260625.md`를 따른다.
- 공통 컴포넌트와 mock/fixture는 `frontend_component_guidelines_20260625.md`, `frontend_api_mock_fixtures_20260625.md`를 따른다.
- E2E 검증은 `frontend_e2e_test_plan_20260625.md`를 따른다.
- E7-T01~T13은 E7-T00 scaffold 이후 구현한다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E7-T00 | 프론트 workspace scaffold | P1 (gate) | E0-T02 | pnpm workspace, `apps/service-web` Next.js, `apps/admin-web` Vite React SPA, `packages/api-client`, `packages/ui`, MSW, Tailwind/Radix/lucide, test setup | `service-web`의 `/price-prediction`과 `admin-web`의 `/admin/art-price-data` route shell이 각각 열리고, 앱별 API base URL/MSW fixture 전환 기준이 있음 | 두 앱 build test + route smoke + unit test smoke |
| E7-T01 | 가격 예측 입력 화면 | P1 (gate) | E6-T04/E6-T05 | user form | 필수값 검증/작가 선택 가능 | UI test |
| E7-T02 | 예측 결과 화면 | P1 (gate) | E6-T05 | result view | 가격/신뢰도/as_of/card 표시 | UI test |
| E7-T03 | 신규 작가 후보 화면 | P1 (M1-gate) | E6-T04 | candidate form | M1은 제출/검수 필요 표시까지, artist_key 즉시 생성 없음 | UI/API test |
| E7-T04 | 수집 대시보드 | P1 (gate) | E6-T06 | admin dashboard | source별 상태/품질/큐 표시 | UI test |
| E7-T05 | 수집 run 상세 | P1 | E6-T06 | run detail | raw/failure/quality 확인 | UI test |
| E7-T06 | 작품 품질 검수 큐 | P1 (gate) | E6-T07 | review screen | claim/decision/patch 처리 | UI/API test |
| E7-T07 | 작가명 검수 큐 | P1 (gate) | E6-T07 | review screen | risk/reason/override 처리 | UI/API test |
| E7-T08 | artist_key 연결 검수 큐 | P1 (gate) | E6-T07 | review screen | 후보 비교/승인/반려 처리 | UI/API test |
| E7-T09 | 신규 작가 후보 큐 | P1 (M1-gate) | E6-T07 | review screen | M1은 최소 큐 1건 처리, M2에서 필터/대량 처리/전체 상태 보강 | UI/API test |
| E7-T10 | snapshot/모델 운영 화면 | P1 | E6-T08/E6-T09 | admin screens | snapshot 승인, model training/import job, candidate 승인, model 배포/롤백 처리 | UI/API test |
| E7-T11 | 운영 로그/알림 화면 | P2 | E6-T10 | admin log view | actor/사유/시간 조회 | UI test |
| E7-T12 | freshness 경고/카드 숨김 화면 | P1 (gate) | E6-T11, E7-T02 | result view 보강 | `FRESH-WARN-N` 경고 표시, `FRESH-HIDE-M` 카드 숨김 | UI test |
| E7-T13 | NANT mapping 관리 화면 | P1 (gate) | E6-T12 | admin NANT mapping screen | version 목록/import/draft edit/unmapped 처리/activate 화면 제공 | UI/API test |

## 12. Epic 8. 운영 자동화와 runbook

목표:

- 수집, 품질 감사, 알림, 장애 대응을 반복 가능한 운영 절차로 만든다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E8-T01 | 주간 cron 구성 | P0 | E2/E3 | scheduler | 월 03:00 source별 실행 | dry run |
| E8-T02 | run 미생성 감지 | P1 | E8-T01 | dead-man alert | 예정 시간+유예 후 알림 | alert test |
| E8-T03 | collector watchdog 운영화 | P1 | E2-T09 | watchdog deploy | stuck run 회수 + blocked/rate_limited(429/403) source 감지·알림 | alert/test |
| E8-T04 | snapshot watchdog 운영화 | P1 | E5 | watchdog deploy | stuck snapshot request 회수 | alert/test |
| E8-T05 | canary 품질 알림 | P1 | E3-T07 | alert job | 수집량/가격/크기/작가명 하락 감지 | alert test |
| E8-T06 | 일일 운영 runbook 작성 | P1 | E7 admin screens | runbook | 담당자가 매일 볼 순서 명시 | tabletop review |
| E8-T07 | 주간 snapshot 승인 runbook 작성 | P1 | E5/E7-T10 | runbook | 요청/생성/서빙승인 절차 명시 | tabletop review |
| E8-T08 | 장애 대응 runbook 작성 | P1 | E8 alerts | runbook | blocked/rate_limited/parser 실패 대응 | tabletop review |
| E8-T09 | 개인정보/삭제 요청 runbook 작성 | P0 | E0-T05/E1-T09 | runbook | suppression 처리 절차 명시 | privacy review |

## 13. Epic 9. 통합 검증과 운영 전환

목표:

- 전체 기능을 end-to-end로 검증하고 운영 가능한 상태로 전환한다.

| ID | Task | 우선순위 | 선행 조건 | 산출물 | 완료 기준 | 검증 |
|---|---|---|---|---|---|---|
| E9-T01 | 4개 source full run 검증 | P1 (gate) | E2/E3 | full run report | raw/interpreted/normalized 완료 | E2E test |
| E9-T02 | identity 샘플 검수 | P1 (gate) | E4 | sample audit | auto_approved 오연결 없음 | manual review |
| E9-T03 | snapshot/model E2E 검증 | P1 (gate) | E5 | snapshot/model report | approved snapshot -> active deployment 연결 | E2E test |
| E9-T04 | public API 비노출 검증 | P1 (gate) | E6 | schema test | source/url/internal id 미노출 | API test |
| E9-T05 | 사용자 화면 E2E 검증 | P1 (gate) | E7 | UI E2E report | 예측/카드/freshness 표시 | browser test |
| E9-T06 | 어드민 운영 E2E 검증 | P1 (gate) | E7/E8 | admin E2E report | 검수/snapshot/model 처리 가능 | browser test |
| E9-T07 | 장애/알림 리허설 | P1 | E8 | drill report | failed/stuck/blocked 알림 확인 | drill |
| E9-T08 | 장애 격리 검증 (NFR-02) | P1 (gate) | E6-T05 | isolation test report | 수집 DB 비가용 시에도 예측 API가 승인 snapshot/feature store/model bundle로 정상 응답 | fault injection test |
| E9-T09 | 운영 전환 체크리스트 | P1 (gate) | E9-T01~T08 | launch checklist | PRD 성공 기준 충족 | final review |

## 14. 마일스톤 구성 (M1 수직 슬라이스 / M2 확장)

로드맵 §5.5에 따라 Epic 1~7 구현은 1원천(Art1) end-to-end **수직 슬라이스(M1)** 를 먼저 완성하고 폭으로 확장(M2)한다. M1은 별도 완화 기준이 아니라 1차 완료의 **부분집합을 조기 검증**하는 단계다.

### M1 구성 Task (Art1 1원천 · 작가명/신규 후보 최소 검수 큐 · 최소 화면)

- 기반: E0-T01~T04, E0-T06, E0-T07, E0-T08, E0-T09, E1-T01~T08, E1-T10
- 수집: E2-T01, E2-T02, E2-T03, E2-T04 (Art1만)
- 표준화: E3-T01~T04, E3-T08~T10 (Art1만)
- 작가 identity/profile: E4-T01~T06 (최소 identity 후보/자동 확정 경로 + 사용자 신규 작가 후보 제출 큐), E4-T07은 M1에서 "연결 확정 이벤트 1종"만 기록, E4-T09는 Art1 기준 최소 `artist_profile_item` 생성 + `artist_profile_current` 요약 갱신
- snapshot/model: E5-T01~T05, E5-T08~T11
- API: E6-T01~T05, E6-T06(수집 대시보드), E6-T07(작가명 큐/신규 작가 후보 최소 큐), E6-T08. E6-T04는 M1에서 artist search와 신규 작가 후보 제출을 모두 구현
- 화면: E7-T01, E7-T02, E7-T03(M1 제출 폼), E7-T04, E7-T07, E7-T09(M1 최소 신규 후보 큐)

**M1 의존 닫힘 규칙**: 위 목록은 M1 spine이다. (1) 여기 나열된 Task의 **직접 선행 Task는 M1에 함께 포함**된다(예: E2-T03, E0-T03). (2) 다중 원천 Task(E3-T01~T04 parser, E6-T06 대시보드)는 **Art1 경로로만 구현·검증**하고, 그 Task의 Epic 단위 선행(`E2/E3`)은 M1에서는 Art1 관련 Task로만 해석한다. 나머지 원천 확장은 M2에서 같은 Task로 완성한다. (3) 따라서 M1에는 M2 전용 Task(E3-T07 등)에 대한 의존이 없다. (4) 집계 품질감사(E3-T07)는 M2다. M1의 수집 대시보드(E7-T04)·snapshot 요약(E5-T01)은 normalized quality flag 기반 **기본 표시**까지로 한정하고, 보유율/성공률 등 집계 지표는 M2에서 보강한다. (5) full merge/un-merge event 범위와 영향 범위 조회(E4-T08)는 M2다. M1은 작가명 alias, 사용자 신규 작가 후보 제출, 최소 identity 후보 연결을 통해 예측 경로를 닫는 데 집중한다.

M1 완료 = Art1 데이터로 사용자 예측 화면이 active deployment 기준 응답(가격/신뢰도/as_of/1차 시장 카드)을 표시하고, 사용자가 신규 작가 후보를 제출할 수 있으며, 어드민이 화면에서 작가명 검수 1건과 신규 후보 최소 큐 1건을 처리한다(로드맵 §5.5 M1 완료 기준). freshness 경고/카드 숨김은 M2.

### M2 구성 Task (폭 확장)

- 나머지 원천: E2-T05~T08, E3-T05~T09
- identity 확장: E4-T07 full event coverage, E4-T08(영향 범위)
- 검수 큐/freshness/NANT/model 운영 전체: E5-T06, E5-T07, E6-T09/T10/T11/T12, E7-T05/T06/T08/T10/T11/T12/T13
- M1 화면 보강: E7-T03/E7-T09은 M1에서 최소 경로를 닫고, M2에서는 필터/상세 상태/대량 처리/전체 E2E fixture를 보강한다(새 Task로 중복 산정하지 않음). E4-T09는 M1에서 최소 profile item/current summary 생성, M2에서 원천 우선순위/충돌 검수/프로필 품질 플래그를 보강한다
- 운영 자동화/runbook: E8 전체
- 통합 검증/운영 전환: E9 전체

M2 완료 = §13 Epic 9 완료 기준 및 PRD §10 성공 기준 충족.

## 15. 첫 스프린트 권장 작업

첫 스프린트는 아래 항목만 완료해도 이후 병렬 개발이 가능해진다.

1. E0-T01 MySQL DDL 초안 작성
2. E0-T02 OpenAPI 초안 작성
3. E0-T04 사용자 API 인증/rate limit 기준 확정
4. E0-T05 suppression/do-not-train/do-not-show 기준 확정
5. E0-T06 1차 시장 가격 카드 계산 기준 확정
6. E0-T09 NANT 분류 기준 DB seed/fixture 확정
7. E1-T01 migration 실행 구조 마련
8. E1-T02 source/run/raw 테이블 구현
9. E1-T08 object storage payload store 구현
10. E1-T10 NANT mapping 관리 테이블 구현
11. E2-T01 collector result schema 정의
12. E2-T02 DB writer 구현

## 16. 추적 기준

각 Task는 issue 또는 작업 카드로 옮길 때 아래 템플릿을 사용한다.

```text
ID:
제목:
우선순위:
관련 문서:
선행 조건:
구현 범위:
완료 기준:
검증 방법:
비고/리스크:
```
