# Track6 데이터 수집 개발 착수 전 결정안

작성일: 2026-06-25

목적:

- 운영하면서 조정 가능한 임계치가 아니라, 개발 착수 전에 API/DB/프론트/배치 구현을 고정하기 위해 필요한 결정을 정한다.
- 기본값은 "권장 확정안"이다. 사용자가 별도 선택을 하지 않으면 이 조합으로 Phase 0 산출물(DDL/OpenAPI/seed/test)을 작성한다.
- 운영 실측 후 조정 가능한 값은 [운영 파라미터](operational_parameters_20260625.md)에 남기고, 이 문서에서는 구조적 결정을 우선한다.

관련 문서:

- [1차 개발 로드맵](first_development_roadmap_20260625.md)
- [PRD](product_requirements_20260625.md)
- [API 기획](user_admin_api_plan_20260625.md)
- [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
- [프론트 mock fixture 기준](frontend_api_mock_fixtures_20260625.md)

## 1. 추천 조합 요약

권장 개발 조합:

```text
MySQL 8.0 + 명시 SQL migration
  -> private object storage에 raw payload 저장
  -> Art1 수직 슬라이스(M1)
  -> approved snapshot 기반 feature/export
  -> 데이터 수집 서비스 내부 joblib serving adapter
  -> Warm joblib + Cold k80 보수적 운영 joblib 번들을 model registry/deployment에 연결
  -> 사용자 API는 로그인 없이 익명 세션 + rate limit
  -> 어드민 API는 제공 이메일/비밀번호 로그인 + JWT + 역할 claim + actor 서버 주입
  -> rate limit/idempotency/익명세션 카운터는 M1 단일 인스턴스 + MySQL 저장(확장 시 Redis)
  -> 비동기 job은 cron + collector_run/watchdog DB 패턴(별도 큐는 후속)
  -> 어드민 프론트는 React + TypeScript SPA(데이터테이블/쿼리 라이브러리), 사용자 화면 SSR은 SEO 필요 시 택
```

이 조합을 추천하는 이유:

- 기존 문서의 핵심 원칙(raw object storage, 수집 DB 실시간 조회 금지, approved snapshot만 서빙, actor body 금지)과 충돌하지 않는다.
- 새 ORM/SSO/회원 시스템을 동시에 도입하지 않아 M1의 불확실성을 줄인다.
- DDL/OpenAPI/프론트 mock/E2E를 병렬로 작성하기 쉽다.

## 2. 개발 착수 기준으로 확정할 항목

| 항목 | 권장 확정안 | 개발 산출물 |
|---|---|---|
| 스펙 산출물 위치 | data_collection 문서 하위에 `openapi/`와 `mysql/`을 둔다. | `docs/track6/data_collection/openapi/track6_data_collection_v1.yaml`, `docs/track6/data_collection/mysql/001_track6_data_collection_core.up.sql` |
| DB/migration | MySQL 8.0, InnoDB, `utf8mb4`, 명시 SQL migration. Alembic/ORM migration은 1차에서 도입하지 않는다. | `schema_migrations` 테이블, `.up.sql`/`.down.sql`, dev DB migration smoke test |
| ID 전략 | 내부 조인 PK는 `BIGINT UNSIGNED AUTO_INCREMENT`, API/public 식별자는 prefix id 또는 기존 업무 키(`artist_key`, `snapshot_id`)를 사용한다. | DDL PK/FK, OpenAPI id format |
| OpenAPI | OpenAPI 3.1 YAML을 계약서로 고정하고 FastAPI/Pydantic 구현이 이를 만족하는지 테스트한다. | OpenAPI lint, request/response fixture 검증 |
| 공통 에러 | 기존 API 기획의 error envelope를 유지하고, HTTP 상태는 400/401/403/404/409/429/500을 기본으로 쓴다. async job 생성은 202를 허용한다. | error enum matrix |
| 멱등성 | 기존 문서대로 JSON body의 `idempotency_key`를 1차 기준으로 유지한다. 같은 key+같은 payload는 replay, 같은 key+다른 payload는 409. | idempotency utility, request hash 저장 |
| 사용자 API 인증 | 사용자 로그인은 두지 않는다. 완전 공개가 아니라 first-party 익명 세션을 발급하고 session/IP 기준 rate limit을 적용한다. | anonymous session middleware, rate limit seed |
| 어드민 인증 | 제공된 이메일/비밀번호로 로그인하고 JWT access token + role claim, refresh token을 발급한다. SSO는 후속 도입 예정이다. `actor_id`는 body 금지, 서버가 claim에서 주입한다. | admin auth middleware, role test |
| 어드민 bootstrap | 초기 superuser 1개를 CLI 또는 seed command로 생성한다. 공유 계정은 금지하고, 최초 계정도 개인 식별 가능한 email/login을 갖는다. | `admin_user` seed, password hash, audit actor |
| suppression | 컬럼-only가 아니라 별도 `suppression_rule` 테이블을 SoT로 둔다. 서비스 노출 차단, 학습 제외, raw 보존/삭제 요청 scope를 분리한다. | DDL, query filter, snapshot exclusion test |
| raw object storage | 1차부터 private object storage 사용. DB에는 `payload_path`, `payload_hash`, `payload_size`만 저장한다. | object key convention, storage adapter |
| object path | raw는 `raw/{env}/source={source}/dt={YYYY-MM-DD}/run={run_id}/{raw_fetch_id}-{sha16}.{ext}.gz`, CSV는 `manual/{env}/source={source}/dt={YYYY-MM-DD}/import={import_id}/original.csv`. | `payload_path`, `manual_import_file.file_uri` 규칙 |
| 1차 시장 카드 저장 위치 | feature store 실시간 계산이 아니라 approved snapshot 생성 시 집계 테이블을 만든다. API는 active deployment의 training snapshot 기준 row를 조회한다. | `primary_market_artist_summary` 또는 동등 테이블 |
| 1차 시장 카드 계산 | 기존 Track6 `estimated_ho` 기준을 사용한다. `estimated_ho = argmin_h |area_cm2 - HO_TABLE_F[h]|`, `unit_price_per_ho = price_krw / estimated_ho`. | summary build job, API fixture |
| 1차 시장 카드 표본 | 승인 snapshot의 정상화 row 중 가격/크기/작가키/품질/suppression 조건을 통과한 row만 사용한다. 전체 표본 최소 N=5, 매체별 분포는 매체 그룹 N>=3만 표시한다. | aggregation test |
| 1차 시장 카드 이상치 | artist+medium 그룹 내 `unit_price_per_ho`의 q05~q95 winsorized 값을 기준으로 median/q25/q75를 계산한다. 표본이 20개 미만이면 winsorize 없이 median/q25/q75만 계산하고 low_sample flag를 붙인다. | calculation spec/test |
| prediction API 연결 | 기존 가격 예측 API를 호출하지 않고, 데이터 수집 서비스 안에 joblib serving adapter를 둔다. adapter는 active deployment/model registry에서 joblib artifact를 읽고 직접 예측한다. | joblib serving adapter, parity smoke |
| M1 모델 | Warm은 `models/track6/warm_lite_unified_current_joblib_v0.1_candidate`를 active deployment 후보로 둔다. Cold는 `k80 보수적 운영` 후보(`resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05`)를 `models/track6/cold_k80_conservative_official_v0.1_candidate/` joblib runtime bundle로 freeze한 뒤 active deployment에 올린다. `cold_prediction_v0.5_operational`은 M1 적용 후보가 아니라 과거 raw-input p95 방어 참고 산출물로만 둔다. | model registry seed, deployment seed, cold k80 joblib freeze/parity |
| 신규 작가 후보 | 사용자 신규 작가 후보 제출을 M1에 포함한다. 따라서 SQL view/export만으로 시작하지 않고 물리 후보 큐 테이블을 1차 DDL에 포함한다. | physical candidate queue table, public submit API |

## 3. 선택이 필요한 항목

아래 항목은 권장안이 있지만, 제품/조직 정책에 따라 선택지가 갈릴 수 있다.

### 3.1 사용자 API 인증 범위

확정: 사용자 로그인 없음 + 익명 세션 + rate limit.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| 익명 세션 + rate limit | 사용자 가입 없이 M1 검증 가능. abuse 차단과 request 추적은 가능. | 장기 사용자 이력/과금/개인화에는 부족. | 확정 |
| 사용자 로그인 필수 | abuse 대응과 사용자 이력 관리가 강함. | 회원/세션/비밀번호/약관 UI가 M1 범위를 키움. | 후속 검토 |
| 완전 공개 API | 가장 빠름. | 기존 문서의 `public`은 무인증 아님 원칙과 충돌. scraping/abuse 위험 큼. | 비권장 |

권장 rate limit 초안:

| endpoint | session 기준 | IP 기준 |
|---|---:|---:|
| `GET /api/v1/public/artists/search` | 60/min | 300/day |
| `POST /api/v1/public/price-predictions` | 20/hour | 100/day |
| `POST /api/v1/public/artist-candidates` | 5/day | 20/day |

주의: `session 기준` 한도는 쿠키 초기화로 우회되므로 abuse 방어가 아니라 UX 가드로 본다. 실질 방어선은 `IP 기준` 한도이며, 분산 IP 스크래핑까지 막으려면 후속에서 사용자 인증 또는 추가 방어가 필요하다.

### 3.2 admin 인증 방식

확정: 제공 이메일/비밀번호 기반 admin user + JWT. SSO는 후속.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| 제공 이메일/비밀번호 + JWT | M1에서 바로 구현 가능. actor/audit/role claim을 통제하기 쉽다. | 장기적으로 SSO/MFA 요구가 생기면 교체 필요. | 확정 |
| 외부 IdP/SSO 우선 | 조직 보안 정책과 잘 맞을 수 있다. | IdP 결정 없이는 개발이 막히고 local/dev 환경이 복잡해진다. | 후속 도입 |
| 공유 superuser | 빠르다. | 감사 추적이 깨진다. 기존 문서 원칙과 충돌한다. | 비권장 |

### 3.3 migration 도구

권장: 명시 SQL migration + 얇은 runner.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| 명시 SQL migration | MySQL 생성 컬럼/unique/check를 정확히 리뷰 가능. 현재 repo 의존성 증가가 작다. | 자동 모델 diff는 없다. | 권장 |
| Alembic/SQLAlchemy | 장기적으로 Python 모델과 migration 연동이 좋다. | 현재 프로젝트에 스택이 없고, 1차 DDL이 문서 중심이라 도입 비용이 큼. | 후속 검토 |

### 3.4 신규 작가 후보 저장

확정: 사용자 신규 작가 후보 제출을 M1에 포함하므로 물리 큐 테이블.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| SQL view/export | M1에서 identity 후보 검증을 빨리 시작할 수 있다. 기존 SoT 테이블 중복이 적다. | 사용자 후보 제출/claim/상태 이력에는 부족하다. | 후보 제출 없는 경우만 |
| 물리 큐 테이블 | public 후보 제출, admin queue, claim, history, SLA를 명확히 구현 가능. | M1 범위가 커진다. | 확정 |

### 3.5 object storage 제공자

권장: S3-compatible adapter interface + local filesystem dev backend.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| local dev + S3-compatible prod | dev가 쉽고 prod 이관 경로가 명확하다. MinIO/S3/R2를 같은 interface로 묶을 수 있다. | 실제 cloud IAM 세부값은 별도 확정 필요. | 권장 |
| cloud provider 직접 고정 | 운영 IAM/보안정책을 빨리 고정할 수 있다. | 제공자 변경 비용이 크고 초기 dev가 느려진다. | 조직 인프라 확정 시 |
| DB 본문 저장 | 구현은 가장 단순하다. | 기존 문서의 운영 기준과 충돌. 비용/보안/retention 리스크 큼. | 비권장 |

### 3.6 prediction API 연결 방식

확정: 기존 예측 API 호출이 아니라 joblib serving adapter.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| joblib serving adapter | 기존 API 서버에 의존하지 않고 M1에서 실제 모델을 로드해 동작 검증 가능. `model_version`/`deployment_id`/`as_of` 로그 주입도 서비스 내부에서 통제할 수 있다. | 모델 artifact 입출력 스키마를 adapter가 직접 맞춰야 한다. | 확정 |
| 기존 가격 예측 API wrapper | 기존 API 동작을 재사용할 수 있다. | 기존 API 계약과 data_collection 계약이 얽히고, 사용자가 원하는 "joblib로 직접 작동" 조건과 다르다. | 제외 |
| 기존 가격 예측 API 직접 확장 | 레이어가 적다. | 기존 API 회귀 위험이 크고 data_collection 요구사항이 가격 엔진 내부로 번진다. | 비권장 |

### 3.7 Cold 모델 적용 후보

확정: M1 Cold 기본 후보는 `k80 보수적 운영` 모델을 joblib runtime bundle로 freeze한 산출물이다.

선택 이유:

- `k80 보수적 운영` 후보(`resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05`)는 validation 기준 선택 논리가 가장 방어적이다. k40은 fixed test 일부 지표가 더 좋아도 validation 안정성이 약해 운영 기본값으로는 사후 과적합 리스크가 더 크다.
- v0.3 guard+search는 search/lookup 포함 조건의 연구 성능 후보라서, M1의 "서비스 내부 joblib 직접 로드" 기본 경로와 결합하기 전에 별도 feature/lookup 계약이 필요하다.
- `cold_prediction_v0.5_operational`은 즉시 참조 가능한 과거 raw-input p95 방어 산출물이지만, M1 Cold 기본 적용 후보는 아니다.

Cold k80 joblib 적용 산출물:

1. `models/track6/cold_k80_conservative_official_v0.1_candidate/runtime_store.joblib`
2. predictor entrypoint: `predict_cold_k80_conservative_v0_1.py` 또는 동등한 import 가능한 predictor module
3. feature schema/order, policy thresholds, model metadata를 담은 manifest 또는 model card
4. fixed test parity report
5. serving smoke fixture
6. `price_model_registry` / `price_model_deployment` seed

적용 규칙:

- Cold k80 joblib freeze/parity가 실패하면 `cold_prediction_v0.5_operational`로 자동 fallback하지 않는다.
- 이 경우 M1 cold route를 보류하거나, 별도 승인 후 fallback 후보를 다시 선택한다.

### 3.8 공유 상태 저장소 (rate limit / idempotency / 익명 세션)

권장: M1은 단일 인스턴스 + MySQL 테이블 카운터/idempotency 저장. 멀티 인스턴스로 확장할 때 Redis로 이관한다.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| MySQL 테이블(단일 인스턴스) | 새 컴포넌트 없음, M1 빠름. idempotency `request hash` 저장(§2)과 한 곳에서 관리. | 고빈도 카운터/TTL을 직접 구현해야 하고 멀티 인스턴스 동시성에 약함. | 권장(M1) |
| Redis | rate limit/idempotency/세션 카운터에 atomic 연산 + TTL이 최적. | 운영 컴포넌트 1개 추가. | 멀티 인스턴스 전환 시 |
| in-memory(프로세스 로컬) | 가장 빠르고 의존성 0. | 멀티 인스턴스에서 깨지고 재시작 시 소실. | 비권장 |

### 3.9 비동기 job 실행 방식

권장: M1은 cron + 기존 `collector_run`/watchdog DB 패턴(이미 SoT에 존재)을 재사용한다. 별도 작업 큐는 후속.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| cron + DB job/watchdog 패턴 | 기존 `collector_run` single-flight/heartbeat([MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) §5.2.2/§5.16)와 정합. 새 broker 없음. | 복잡한 fan-out/우선순위 제어엔 약함. | 권장(M1) |
| 작업 큐(Celery/RQ/arq) | 재시도/스케줄/가시성/동시성 제어가 강함. | broker(Redis/RabbitMQ) 추가, M1 범위 확대. | 작업량/동시성 증가 시 |
| 요청 스레드 내 동기 처리 | 구현이 가장 단순. | snapshot 생성 등 long-running이 API 타임아웃을 유발. | 비권장 |

### 3.10 프론트엔드 프레임워크 / 렌더링

권장: 어드민은 React + TypeScript SPA(데이터테이블/쿼리/라우터 라이브러리). 사용자 화면 SSR 여부는 SEO 요구로 판단한다.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| React + TypeScript SPA | [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md)(DataTable/FilterBar/URL-query 보존)과 1:1 매핑. 생태계/채용 넓음. | 사용자 화면 SEO/초기 로딩에는 약함. | 권장(어드민) |
| Next.js(React + SSR) | 사용자 화면 SEO/초기 로딩에 유리하고 같은 React 생태계를 어드민과 공유. | 어드민 전용엔 과하고 배포 복잡도가 늘어남. | 사용자 화면 SEO 필요 시 |
| Vue/Svelte 등 비React | 팀 역량에 따라 생산성이 좋을 수 있음. | 컴포넌트 기준 매핑/채용을 재검증해야 함. | 팀 역량 기준 선택 |

## 4. Phase 0에서 바로 만들어야 할 산출물

1. `docs/track6/data_collection/openapi/track6_data_collection_v1.yaml`
2. `docs/track6/data_collection/mysql/001_track6_data_collection_core.up.sql`
3. `docs/track6/data_collection/mysql/001_track6_data_collection_core.down.sql`
4. `docs/track6/data_collection/mysql/002_track6_data_collection_seed_operational_parameters.up.sql`
5. API enum/status/error/idempotency matrix
6. anonymous session + admin JWT auth fixture
7. object storage key convention test fixture
8. suppression query/snapshot exclusion test fixture
9. primary market summary calculation fixture
10. model registry/deployment seed for Warm joblib + Cold k80 joblib M1
11. public artist candidate submit queue fixture
12. Warm joblib + Cold k80 joblib serving smoke/parity fixture

## 5. 개발 착수 전 확인 질문

사용자가 별도 선택하지 않으면 아래 기본값으로 확정한다.

| 질문 | 기본 선택 |
|---|---|
| 사용자 API를 로그인 필수로 둘 것인가? | 아니오. M1은 로그인 없음 + 익명 세션 + rate limit |
| admin 인증을 외부 IdP로 시작할 것인가? | 아니오. M1은 제공 이메일/비밀번호 + JWT. SSO는 후속 |
| 신규 작가 후보 제출을 M1에 포함할 것인가? | 예. 물리 후보 큐 테이블을 M1 DDL에 포함 |
| object storage provider를 지금 특정 cloud로 고정할 것인가? | 아직 미정. adapter + local dev + S3-compatible path |
| 기존 예측 API를 직접 수정/호출할 것인가? | 아니오. joblib serving adapter 우선 |
| rate limit/idempotency 저장을 별도 Redis로 둘 것인가? | 아니오. M1은 단일 인스턴스 + MySQL. 확장 시 Redis |
| 비동기 job에 별도 작업 큐를 도입할 것인가? | 아니오. M1은 cron + collector_run/watchdog DB 패턴 |
| 프론트 프레임워크를 무엇으로 둘 것인가? | 어드민 React + TypeScript SPA. 사용자 화면 SSR은 SEO 필요 시 |
