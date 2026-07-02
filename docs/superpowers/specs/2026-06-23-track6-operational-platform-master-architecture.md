# Track6 가격예측 운영 플랫폼 — 마스터 아키텍처

- 작성일: 2026-06-23
- 대상: Warm/Cold 모델 확정을 전제로 한 **운영 + 데이터수집 + 재학습 + 어드민** 통합 플랫폼
- 성격: **마스터 아키텍처(통합 청사진)**. 서브시스템별 상세 구현은 각자 별도 spec→plan→구현으로 분해한다.
- 리뷰: 코덱스(OpenAI) 독립 아키텍처 리뷰 1회 반영 — P1 8건 + P2 3건(소스 lineage·raw 디듑·MySQL 격리·durable 스케줄러·active 포인터·strict-Cold pool 제외·수동입력 스키마·641 마이그레이션·parity 해시·빌드순서·최소 admin·인증).
- 상위/연관 문서
  - `docs/superpowers/specs/2026-06-22-track6-operational-serving-design.md` — 서빙·데이터·재학습 **상세 설계(§7 데이터 §8-9 재학습)**. 본 문서는 이를 MySQL/어드민 위에서 통합·실체화한다.
  - 메모리: `track6_price_prediction_state`, `track6_service_version_namespaces`

---

## 1. 목적 · 범위 · Non-goals

### 1.1 목적

Warm/Cold(+Warm-lite) 모델이 확정됐다는 전제 하에:
1. 두 모델로 **서비스를 운영**하고,
2. 4개 소스에서 **주기적으로 학습 데이터를 수집·표준화**하고,
3. 그 데이터로 **재학습·검증·승격**하고,
4. 위 전 과정을 **어드민에서 관리**하며,
5. **수동 데이터 입력·학습**도 지원하는

체계화된 플랫폼을 설계한다.

> **전제 정합(코덱스 P2-7)**: 위 "모델 확정 전제"는 서술 편의다. **실제로는 Warm/Cold가 아직 실험·미확정**이며, 본 아키텍처는 모델을 "순환 안에서 교체되는 부품"으로 다뤄 **모델 버전이 무엇이든 동일하게 작동**한다. 모델 버전과 무관하게 항상 구속력 있는 제약은 strict-Cold·불변 아티팩트·route별 독립 버전/포인터·전 워커 사전로드 후 승격·성능 게이트·parity·소스 추적성이다. 시나리오·순환 상세는 `2026-06-23-track6-scenarios-and-cycles.md` 참조.

### 1.2 In-scope (이번 마스터 설계가 그리는 범위)

- 4개 플레인(Data / Training / Serving / Admin) + **MySQL 통합 system-of-record**의 전경과 경계.
- MySQL 스키마(raw · standardized · snapshot · registry · serving log · review queue).
- 4개 소스(Artsy / Art1 / Saatchi / Printbakery) 크롤 → raw 적재 → 표준화 → train-ready snapshot 흐름.
- 재학습 오케스트레이션(자동 주기 + 수동 트리거) → parity·성능게이트 → 불변 레지스트리 승격/롤백.
- 수동 데이터 입력 경로(어드민 폼 → 동일 표준화 → snapshot 합류).
- 어드민 화면맵 · 백엔드 라우트 · 권한.
- 배포 토폴로지(dokploy 관리형 + 앱내 스케줄러 + 백그라운드 잡).

### 1.3 Non-goals (본 문서가 정하지 않는 것 — 하위 spec에서)

- 각 플레인의 **코드 레벨 상세 구현**(클래스·함수 시그니처). → 서브시스템별 plan.
- 모델 알고리즘 변경/실험(Warm/Cold는 확정 전제).
- 이미지·멀티모달 가격 모델.
- 신규 외부 소스 추가(4종 고정, 확장은 §4.1 규칙만 정의).
- 서빙 설계 §1~§14에서 이미 확정된 predictor I/O·라우팅·strict-Cold 세부(중복 정의 안 함, 참조).

### 1.4 확정 전제 (이 설계의 입력)

| 결정 | 값 | 근거 |
|---|---|---|
| 데이터 소스 | Artsy / Art1 / Saatchi / Printbakery (4종, 전부 가격 라벨 보유) | 오늘 구현된 크롤러, 헤더 검증 완료 |
| DB 경계 | MySQL = 통합 system-of-record (raw~serving 전부) | 어드민 운영 일원화 |
| 기존 SQLite | 실서비스 로그 641건 + 피드백 + 검수큐 → **MySQL로 마이그레이션(파괴 금지)** | 메모리 PP-MONLIVE1 |
| 어드민 스택 | FastAPI + Jinja/HTMX + Tailwind 서버렌더 (단일 배포) | 가벼운 ML 운영툴 |
| 배포/자동화 | dokploy 관리형 MySQL+FastAPI, **DB 기반 durable 잡 테이블 + 스케줄러 리더 락**(앱내 APScheduler는 트리거만), 수집·학습은 백그라운드 잡 | dokploy MCP 연결됨 |

#### 소스 lineage 계약 (코덱스 P1-1 반영)

본 플랫폼 소스(`artsy/art1/saatchi/printbakery`)는 업스트림 서빙 설계 §7의 소스 집합(`saatchi/artsy/artue/gallery_primary` + `track4_source`)과 **이름·개수가 다르다**. 무시하면 manifest 재현성·기존 스크립트·fixed test·lineage가 깨진다. 따라서 **명시적 매핑 계약**을 둔다:

| 본 플랫폼 `source` | 업스트림 `track4_source` 대응 | 처리 |
|---|---|---|
| `saatchi` | `saatchi` | 동일 유지 |
| `artsy` | `artsy` | 동일 유지 |
| `art1` | (신규) | 신규 소스로 등록, §4.1 확장 규칙 적용 |
| `printbakery` | (신규) | 신규 소스로 등록 |
| (없음) | `artue`, `gallery_primary` | **유지** — 과거 snapshot/모델 재현용 lineage로 보존, 신규 수집은 안 함 |

- 신규 학습 snapshot은 활성 4소스만 사용하되, `source` 컬럼은 업스트림 `track4_source`와 **동일 네임스페이스**로 둬 과거 산출물과 join·역추적이 가능해야 한다.
- 기존 fixed test/모델 manifest의 `track4_source` 값은 그대로 보존(불변 아티팩트).

### 1.5 불변식 (Invariants — 위반 시 배포 차단)

서빙 설계 §1.4를 계승하고 플랫폼 차원으로 확장한다.

1. **strict-Cold** — Cold 경로는 입력 작가 `artist_key`로 같은 작가 가격 이력/검색을 lookup하지 않는다. **추가(코덱스 P1-6): `artist_key`가 알려진 경우(`cold_registered`) 이웃 잔차 reference pool에서 같은 작가 행을 제외(leave-one-artist-out)** — pool 경유 동일작가 가격 누수 차단. 학습 OOF는 이미 artist GroupKFold로 보장, 서빙 시점에도 동일 강제.
2. **미지 작가는 Warm 금지** — 매칭 실패·동명이인·이력부족이면 Cold.
3. **불변 아티팩트** — 배포된 모델 버전은 덮어쓰지 않는다. 재학습은 새 버전, 승격은 active 포인터 교체만.
4. **소스 추적성** — 모든 학습 행은 `source` + `source_row_index` + `run_id`로 원천까지 역추적.
5. **결정성** — 동일 입력 + 동일 아티팩트 → 동일 출력(부동소수 허용오차 이내).
6. **학습↔서빙 parity** — 학습 feature 생성 규칙과 운영 추론 feature 생성 규칙이 동일. **메커니즘(코덱스 P1-9): 컬럼 리스트 선언이 아니라 불변 `feature_schema_hash` + transformer 코드 버전 + enum 버전 + 파이프라인 git SHA를 아티팩트 manifest에 고정하고, 아티팩트별 golden train-vs-serve fixture로 회귀 검증.**
7. **원본 불변** — raw 레이어는 표준화/필터 없이 원본 보존. 파생은 하위 레이어에서만.

---

## 2. 시스템 전경 & 컴포넌트 맵

데이터가 **들어오는 입구(외부 수집 소스 4곳)** → 플랫폼 내부 → **나가는 출구(사용자 단)** 까지 한 흐름으로 본다.

```
╔══════════════════ 입구: 외부 수집 소스 (4 사이트) ══════════════════╗
║   Artsy        Art1        Saatchi        Printbakery               ║
║   (1·2차)      (1차)        (1차)          (1차/판화)                 ║
╚═══════════╤═══════════╤═══════════╤═══════════╤═════════════════════╝
            │ 크롤 잡    │           │           │   (소스별 독립 수집)
            └───────────┴─────┬─────┴───────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ADMIN  (FastAPI + Jinja/HTMX)                      │
│  대시보드 · 데이터검수큐 · 수동입력 · 학습트리거 · 승격/롤백 · 모니터링  │
└───────────────┬─────────────────────────────────────┬───────────────┘
                │ 제어/조회                              │ 제어/조회
   ┌────────────▼───────────┐              ┌────────────▼────────────┐
   │   DATA PLANE           │   snapshot   │   TRAINING PLANE         │
   │ 수집수신 → L0 raw       ├─────────────►│ warm/cold 재학습 → 평가   │
   │ → L1~L4 표준화/보강      │              │ → parity → 성능게이트     │
   │ → L5~L7 train snapshot  │              │ → registry(불변 버전)     │
   └────────────┬───────────┘              └────────────┬────────────┘
                │ 적재/조회                               │ active_pointer 교체
                ▼                                        ▼
   ┌────────────────────────────────────────────────────────────────┐
   │              MySQL  (통합 system-of-record)                      │
   │  raw · standardized · snapshot · registry · serving log · queue  │
   └────────────────────────────────────────────────────────────────┘
                ▲                                        ▲
                │ active 버전 로드(메타)                   │ 예측로그/피드백 적재
   ┌────────────┴────────────────────────────────────────┴───────────┐
   │         SERVING API  (기존 official_v0_1, 연동만)                │
   │  /artists:search · /price-predictions · /feedback · /health      │
   └───────────────────────────────┬──────────────────────────────────┘
                                    │ 작가후보·예측결과(JSON)
                                    ▼
╔════════════════ 출구: 사용자 단 (프론트엔드 / 클라이언트) ═══════════╗
║  ① 작가 이름 검색 → ② 후보 선택(미등록=신규) → ③ 작품 입력            ║
║  → ④ 가격·범위·신뢰표시 → (선택) ⑤ 실판매가 피드백 입력               ║
╚══════════════════════════════════════════════════════════════════════╝
```

**입구(4 소스) → 4 플레인 + 1 DB → 출구(사용자 단).** 플레인 간 결합은 오직 MySQL 스키마(계약)로만.

| 플레인 | 책임 | 기존 자산 | 신규 |
|---|---|---|---|
| **Data** | 4 크롤 → raw → 표준화/보강 → train-ready snapshot | 크롤러 4종, 표준화 스크립트(track6/) | MySQL 적재, 잡 오케스트레이션 |
| **Training** | snapshot → 재학습 → parity·게이트 → 레지스트리 승격 | 학습 스크립트 70+, 번들 동결 로직 | 자동 트리거, 게이트 자동화, registry 테이블화 |
| **Serving** | 작가해석 → 라우팅 → 예측 → 응답 | `official_v0_1` FastAPI 동작 | active 버전을 MySQL에서 로드, 로그 MySQL 적재 |
| **Admin** | 위 3개를 사람이 운영(검수·트리거·승격·관측) | 정적 `frontend/index.html` 일부 재사용 | 전부 신규 |

**입구·출구 (플랫폼 경계의 양 끝)**

| 경계 | 무엇 | 본 플랫폼 책임 |
|---|---|---|
| **입구: 수집 소스 4곳** | Artsy / Art1 / Saatchi / Printbakery 외부 사이트 | 크롤 잡이 수집 → Data Plane이 수신·표준화. 소스별 독립 수집(§4.1) |
| **출구: 사용자 단** | 프론트엔드/클라이언트(작가검색→선택→입력→가격표시→피드백) | **입력 계약·검색 흐름만 정의**(서빙 §5.1, §2 스키마). UI 구현 자체는 범위 밖(§1.3) |

**왜 이 구조인가**: 각 플레인이 MySQL 계약으로만 통신하면 — 크롤러를 바꿔도 표준화가 안 깨지고, 학습이 서빙을 모르며, 어드민은 각 플레인을 호출/조회만 한다. 단일 책임 + 독립 테스트 가능(§11 검증).

---

## 3. MySQL 통합 스키마 (system-of-record)

7개 논리 그룹. `init_visionai_db.sql`(기존 설계 초안)을 본 구조로 대체·확장한다. 기존 SQLite 데이터는 §3.6 마이그레이션 절차로 이관.

**MySQL 격리(코덱스 P1-3)**: "단일 system-of-record"가 곧 "단일 부하"는 아니다. 서빙 요청 로깅과 크롤·학습·표준화 부하가 한 MySQL에 몰리므로 다음을 강제한다 — ①논리 그룹별 **스키마/유저 분리**(serving_log·raw·training 등) + 최소 권한, ②서빙 예측 로그는 **비동기·배치 적재**(요청 경로에서 동기 INSERT 금지), ③로깅 DB 장애 시 **fail-open**(예측은 계속, 로그는 큐잉/드롭+알림), ④커넥션 풀 분리 + 무거운 분석 쿼리 LIMIT/타임아웃. (물리 분리가 필요해지면 serving_log를 별 인스턴스로 떼낼 수 있게 그룹 경계를 유지.)

### 3.1 RAW 그룹 (소스 원본 보존, 불변식 7)

| 테이블 | 핵심 컬럼 | 설명 |
|---|---|---|
| `raw_collection_run` | `run_id`, `source`, `started_at`, `finished_at`, `status`, `row_count`, `crawler_git_sha` | 크롤 1회 실행 단위 |
| `raw_artwork` | `raw_id`, `run_id`, `source`, `source_row_index`, `source_artwork_id`, `content_hash`, `payload_json`, `collected_at` | 소스별 원본 1행 = `payload_json`(원천 컬럼 그대로). 표준화 없음 |

- `source ∈ {artsy, art1, saatchi, printbakery, manual}` (manual = §5.3 수동 입력, P1-7 반영).
- **유니크/디듑(코덱스 P1-2)**: `(source, source_row_index)` 단독 유니크는 **재수집(recrawl) 시 여러 런을 보존 못 하고 크롤러 행 순서 안정성을 가정**하므로 금지. 실제 키 = **`(run_id, source_row_index)`**(런별 원본 보존) + 안정적 `source_artwork_id`/URL과 `content_hash`로 **논리적 디듑**(표준화 단계에서 최신 런 선택). 덮어쓰기 없음(불변식 7).
- 한 소스만 재수집해도 다른 소스 파티션 불변(불변식 4·7).

### 3.2 STANDARDIZED 그룹 (표준 데이터 계약 = 서빙 설계 §2)

| 테이블 | 핵심 컬럼 |
|---|---|
| `artist` | `artist_key`(PK), `name_ko`, `name_en`, `birth_year`, `nationality`, `career_stage`, `followers`, `homonym_flag` |
| `artist_alias` | `alias_id`, `artist_key`, `alias_text`, `alias_type`(ko/en/slug), `match_kind` |
| `standardized_artwork` | `std_id`, `raw_id`(FK), `source`, `source_row_index`, `artist_key`(nullable), `price_krw`, `width_cm`, `height_cm`, `depth_cm`, `medium_category`(enum), `support_category`(enum), `year`, `edition_size`, `estimated_ho`, `is_training_candidate`, `exclude_reason` |

- 단위/통화/enum은 서빙 설계 §2.1 단일 정의를 따른다(cm, KRW 정수, log 공간 예측).
- `raw_id` FK로 원천 추적(불변식 4). `artist_key`는 §3.2 `artist`로 해석.

### 3.3 SNAPSHOT 그룹 (train-ready 동결, 서빙 설계 §7 L5~L7)

| 테이블 | 핵심 컬럼 |
|---|---|
| `training_snapshot` | `snapshot_id`, `created_at`, `training_data_cutoff`, `source_snapshot_json`(소스별 rev), `row_count`, `split_summary_json`, `manifest_json`, `status` |
| `snapshot_row` | `snapshot_id`, `std_id`(FK), `split`(train/val_warm/test_warm/val_cold/test_cold), `route_eligibility`(warm/cold) |

- snapshot은 **불변**. 재수집/수동데이터 합류 시 새 `snapshot_id` 생성(불변식 3와 동형).
- `manifest_json`에 `target_columns`, `tracking_only_columns`, `model_exclude_columns`, `cold_forbidden_columns`, `price_leak_allowlist`(서빙 §7.4) 기록.

### 3.4 REGISTRY 그룹 (불변 모델 버전, 서빙 설계 §9)

| 테이블 | 핵심 컬럼 |
|---|---|
| `model_artifact` | `artifact_id`, `route`(warm/cold), `model_version`, `bundle_path`, `artifact_sha256`, `snapshot_id`(FK), `created_at`, `fixed_test_metrics_json`, `dependency_lock_json`, `feature_schema_hash`, `transformer_version`, `enum_version`, `pipeline_git_sha`, `status`(candidate/archived) |
| `active_pointer` | `route`(warm/cold, PK), `artifact_id`(FK), `promoted_by`, `promoted_at` |
| `promotion_audit` | `audit_id`, `route`, `from_artifact`, `to_artifact`, `action`(promote/rollback), `actor`, `gate_result_json`, `ts` |

- 아티팩트 파일(joblib 번들)은 디스크/스토리지에, MySQL은 **메타+포인터+감사**만. Warm/Cold 포인터 독립(서빙 §3.5).
- **active 상태 단일화(코덱스 P1-5)**: `model_artifact.status`에 `active`를 두지 않는다(중복 상태원 제거). "어느 게 active인가"는 **오직 `active_pointer`** 가 단일 진실. status는 `candidate`/`archived`만.
- **parity 고정(P1-9)**: `feature_schema_hash`·`transformer_version`·`enum_version`·`pipeline_git_sha`로 학습-서빙 변환을 버전 고정(불변식 6). 로드 시 서비스가 지원하는 schema_hash와 불일치하면 route unavailable.
- **멀티프로세스 승격 규칙(P1-5, §6 연계)**: ①승격 전 대상 아티팩트를 **모든 서빙 워커가 로드·검증** 성공해야 포인터 교체(부분 승격 금지) ②`active_pointer` 갱신은 단일 트랜잭션(원자적) ③각 워커는 헬스에 **현재 로드된 artifact_id**를 노출 → 승격 후 전 워커 수렴 확인 ④로드 실패 워커 발견 시 롤백.

### 3.5 SERVING LOG 그룹 (예측·피드백·모니터링, 서빙 설계 §11)

| 테이블 | 핵심 컬럼 |
|---|---|
| `prediction_event` | `prediction_id`, `ts`, `route`, `route_reason`, `artist_key`, `model_version_json`, `predicted_price_krw`, `price_low/high`, `q10/q50/q90`, `diagnostics_json`, `review_flags_json`, `latency_ms` |
| `sale_feedback` | `feedback_id`, `prediction_id`(FK), `actual_price_krw`, `sold_at`, `outlier_flag`, `created_at` |
| `routing_monitor` | 메모리 R1~R5 모니터 집계(라우팅 위반·warm비율·동명이인 검수 등) |

- **기존 SQLite `prediction_events`(641) / feedback / 검수큐를 이 그룹으로 이관**(§3.6).

### 3.6 REVIEW QUEUE 그룹 (품질 게이트 & 사람 개입, 서빙 §7.5)

| 테이블 | 핵심 컬럼 |
|---|---|
| `review_queue` | `item_id`, `queue_type`(artist_name/nant_material/homonym/low_confidence/manual_data), `ref`, `payload_json`, `status`(open/resolved/rejected), `assignee`, `resolved_at` |
| `quality_gate_result` | `gate_id`, `snapshot_id`, `metric`, `value`, `baseline`, `passed`, `ts` |

**SQLite → MySQL 마이그레이션(불변식: 641 로그 무손실 — 코덱스 P1-8 반영)**: row count/체크섬만으로는 사용가능성을 보장 못 한다. 마이그레이션 잡은 다음을 충족한다:
- **컬럼 매핑 명세** — `prediction_events`/feedback/검수큐 각 컬럼 → §3.5/§3.6 타겟 컬럼 1:1 매핑표(누락/타입 변환 명시).
- **ID 보존** — 원본 `prediction_id` 보존 또는 `legacy_id` 컬럼으로 유지. **feedback FK 정합**(feedback→prediction 참조 끊김 0 검증).
- **JSON canonicalization** — diagnostics/review_flags 등 JSON 직렬화 형식 통일.
- **dry-run 리포트** → 검토 → 본 실행. **멱등 재실행**(중복 insert 0).
- **freeze 윈도우 또는 dual-write** — 마이그레이션 중 신규 예측 유실 방지.
- **롤백 계획** — 실패 시 원본 SQLite로 즉시 복귀. 원본은 백업 보존.

### 3.7 JOB & SCHEDULER 그룹 (durable 오케스트레이션, 코덱스 P1-4)

앱내 APScheduler만으로는 멀티 워커·레플리카·재시작·dokploy 재배포에서 **이중 실행**을 못 막는다. DB 기반 durable 잡으로 강제한다.

| 테이블 | 핵심 컬럼 |
|---|---|
| `job` | `job_id`, `job_type`(crawl/standardize/train/migrate/...), `params_json`, `status`(queued/leased/running/done/failed), `idempotency_key`(유니크), `lease_owner`, `lease_expires_at`, `heartbeat_at`, `attempts`, `max_attempts`, `created_at` |
| `scheduler_lock` | `lock_name`(PK), `holder`, `acquired_at`, `expires_at` |

- **단일 스케줄러 리더**: 스케줄러 인스턴스는 `scheduler_lock` advisory lock을 획득한 1개만 트리거(리더 선출). APScheduler는 그 리더에서만 enqueue.
- **멱등키**: 동일 주기/소스 잡은 `idempotency_key`로 중복 enqueue 차단.
- **리스 + heartbeat**: 워커가 잡을 lease(만료시각), 주기 heartbeat. **stale-lock 복구**: `lease_expires_at` 경과 잡은 재큐.
- **재시도**: `attempts < max_attempts` 내 백오프 재시도, 초과 시 failed + 알림.

---

## 4. Data Plane — 수집 → 표준화 → snapshot

서빙 설계 §7(L0~L7)을 MySQL/잡으로 실체화한다. 레이어 ↔ 테이블 매핑:

| 레이어 | 입력 | 출력(테이블) | 잡 |
|---|---|---|---|
| L0 수집 | 크롤러 4종 | `raw_collection_run`, `raw_artwork` | `crawl_<source>` 백그라운드 잡 |
| L1 표준화 | `raw_artwork` | `standardized_artwork`(artist_key·price_krw·크기·medium/support·`is_training_candidate`) | `standardize_<source>` |
| L2 이름보정 | L1 + 한글명 override | `artist`/`artist_alias` 갱신, std 행 `artist_key` 확정 | `resolve_artist_names` (+review_queue) |
| L3 메타보강 | L2 + Artsy/Saatchi 메타 | `artist` 메타 컬럼 채움 | `enrich_artist_meta` (+summary) |
| L4 작품속성 | L3 | std 행 year/edition/estimated_ho | `enrich_artwork_attrs` |
| L5 split | L4 | `snapshot_row.split` | `build_split`(Cold-first) |
| L6 feature/label | L5 | snapshot 파일(가격 누수 물리분리) | `export_feature_label` |
| L7 manifest | L6 | `training_snapshot.manifest_json` | `freeze_snapshot` |

### 4.1 소스별 역할 & 클린징

| 소스 | 가격 | 작품 피처 | 작가 메타 | 소스별 클린징 |
|---|---|---|---|---|
| Artsy | `price_krw` | 크기·medium·attribution_class | 국적·생년·팔로워(Cold 풍부) | category/medium_type 파싱 |
| Saatchi | ✓ | ✓ | 작가 파일 | detail enrichment, attribution |
| Art1 | `price_krw_final` | 크기·호수·장르·medium | 작가 프로필 텍스트 | KO medium 파싱, has_positive_price 필터 |
| Printbakery | `price_krw_detail` | 크기·재료·에디션 | maker | 판화 재료/에디션 파싱 |

- **소스별 독립**(불변식 4·7): 한 소스만 재수집→재표준화해도 나머지 파티션 불변. 병합은 `(source, source_row_index)` 키로.
- **확장 규칙**: 신규 소스는 동일 `source` 네임스페이싱 + L1 표준화 매핑 + manifest 등록 절차만 추가.

### 4.2 품질 게이트 & 검토 큐 (서빙 §7.5)

각 단계가 `quality_gate_result`에 기록. 임계(소스별 가격 파싱률·메타 커버리지·재료 매칭률이 직전 snapshot 대비 비악화) 미달 시 **해당 소스만 보류**, 나머지로 진행. 미해결 항목(미보정 한글명·미매칭 재료·동명이인)은 `review_queue`로 → 어드민이 처리.

### 4.3 주기 운영 흐름

```
[주기 도래(스케줄러) or 어드민 수동 트리거 or 소스 갱신 이벤트]
   → 갱신 대상 소스만 L0~L4 재실행 (미갱신 소스 파티션 유지)
   → 품질 게이트 통과분만 → cutoff 고정 → L5~L7 → 새 training_snapshot
   → Training Plane 입력으로 전달(§5)
```

---

## 5. Training Plane — 재학습 → 게이트 → 승격

서빙 설계 §8(학습)·§9(프로모션)을 오케스트레이션으로 실체화. 모델 알고리즘은 불변(확정 전제), **언제·어떻게 재학습·검증·승격하느냐**만 정의.

### 5.1 재학습 파이프라인 (하이브리드: 자동 주기 + 성능 게이트)

```
[트리거: 주기 도래 | 어드민 수동 | 신 snapshot 준비됨]
   → 대상 snapshot_id 선택
   → Warm 학습(서빙 §8.1) / Cold 학습(§8.2)  ── 백그라운드 잡
   → fixed test / hold-out 평가 (누수 통제: cutoff 이후 라벨 미사용, OOF 규칙)
   → parity 검증: 실험 산출값 == 신 joblib predictor 산출값 (diff ~0)
   → 성능 게이트(§5.2): 신버전 ≥ 구버전 (전체 + 슬라이스)
       pass → model_artifact(status=candidate) 등록 → shadow run → (어드민 승인) → active_pointer 교체
       fail → 승격 보류, 구버전 유지, gate_result 기록
```

### 5.2 성능 게이트 (서빙 §9.2, 수치화)

| 지표 | 기준 |
|---|---|
| 전체 MdAPE/MAPE/p95 APE | 구버전 대비 비악화(tolerance 내) |
| 슬라이스 | warm/cold/고가/메타결측/신규작가 슬라이스 비악화 |
| 안정성 | paired bootstrap CI로 개선/비악화 방향 확인 |
| 누수 | cutoff 이후 라벨 미사용, OOF 규칙 준수 |
| parity | 실험 vs predictor diff 0(허용오차) — Warm 607 / Cold 3,099 fixed test |

기준선(참고): Warm fixed test MdAPE 0.086970 / p95 0.820366 (n=607). Cold k80 test MdAPE 0.479052 / p95 2.231840.

### 5.3 수동 데이터 학습 경로

```
[어드민 수동 입력 폼]  (단건 또는 CSV 업로드)
   → 검증(필수/단위/enum) → review_queue(queue_type=manual_data)로 진입
   → 사람 승인 →
       ① raw_artwork에 source='manual' 행 생성 (payload_json=원입력, provenance·
          관측/판매/게시일·검수자·출처메모 포함, run_id=수동 run)   ← raw 경유(P1-7)
       ② standardized_artwork(raw_id FK 충족)로 표준화 적재
   → 다음 snapshot 빌드 시 cutoff 규칙 따라 자동 합류 (별도 학습경로 아님 — 동일 표준화·동일 게이트)
```

- **스키마 정합(코덱스 P1-7)**: 수동 데이터도 raw→standardized 경로를 그대로 탄다(raw_id FK·`source='manual'` enum·provenance·날짜·검수자 보존). std에 직접 insert하지 않는다.
- 핵심: 수동 데이터도 **같은 표준 계약·같은 게이트**를 통과한다. 우회 학습 금지(parity·재현성 보존).
- strict-Cold 준수: 수동 메타는 서빙 §2.4 허용 필드(생년/국적/경력)만, 가격 이력 lookup 유발 금지.

### 5.4 승격 · 롤백 (서빙 §9)

- 아티팩트 불변. 승격 = `active_pointer` 교체 + `promotion_audit` 기록. Warm/Cold 독립.
- 롤백 트리거: 로드 검증 실패, 출력 비정상률 급증, 모니터 지표 악화, shadow diff 이상 → 직전 정상 버전으로 포인터 즉시 교체(무손실).
- **포인터 스왑·롤백은 admin 전용**(서빙 §9.4).

---

## 6. Serving 연동 (기존 자산, 변경 최소)

기존 `official_v0_1` FastAPI는 **두 지점만** MySQL과 연동:

1. **기동/리로드 시** `active_pointer`에서 warm/cold active `artifact_id` → `bundle_path` 로드(서빙 §3.4 로드 검증 그대로).
2. **요청마다** `prediction_event` 적재, 피드백은 `sale_feedback` 적재.

- 라우팅·predictor·strict-Cold·응답 스키마는 서빙 설계 §2·§5·§6 **그대로**(재정의 안 함). strict-Cold reference pool 같은작가 제외(불변식 1)를 서빙 시점에 강제.
- **무중단 승격(코덱스 P1-5 반영)**: ①신 아티팩트를 **모든 워커가 사전 로드·검증** 성공해야 포인터 교체(부분 리로드/stale 워커 방지) ②`active_pointer`는 원자적 갱신 ③각 워커 `/health`가 로드된 artifact_id 노출 → 전 워커 수렴 확인 후 승격 완료 처리 ④로드 실패 워커 시 자동 롤백. 인플라이트 요청은 구버전 유지.

---

## 7. Admin Plane — 화면맵 · 라우트 · 권한

FastAPI + Jinja/HTMX. 배포상 어드민+잡은 서빙과 별도 앱으로 분리한다(§8 권장 토폴로지). 초기 단계에서는 단일 앱 내 `/admin/*` 분리 라우터로 시작해도 무방하며, 학습 부하가 커지면 §8대로 분리한다.

**v1 최소 범위(코덱스 P2-2)**: 7화면 전체를 한 번에 만들지 않는다. **v1 = ①검수 큐 ②잡 상태(`job` 테이블 조회) ③승격/롤백 ④감사 로그** 만. 대시보드·모니터링·수동입력·학습실험 화면은 durable 잡과 서빙 마이그레이션이 선 적용된 뒤 v2로 확장. 그 전까지 수집·학습 트리거는 CLI/잡 테이블로 충분.

### 7.1 화면맵

| 화면 | 역할 | 주 테이블 |
|---|---|---|
| **대시보드** | 서비스 헬스, 최근 예측량/라우팅 분포, active 버전, 최신 snapshot 상태 | prediction_event, active_pointer, training_snapshot |
| **데이터 수집** | 소스별 마지막 수집 시각/행수/상태, 수동 재수집 트리거, 품질게이트 결과 | raw_collection_run, quality_gate_result |
| **검수 큐** | 한글명/재료/동명이인/저신뢰/수동데이터 항목 처리(승인/반려) | review_queue |
| **수동 입력** | 단건/CSV 학습데이터 입력 → 검수 큐 진입 | review_queue, standardized_artwork |
| **학습/실험** | snapshot 선택 → 재학습 트리거, 진행상태, 평가지표, parity 결과 | training_snapshot, model_artifact |
| **모델 레지스트리** | warm/cold 버전 목록, 게이트 결과, **승격/롤백 버튼**(admin), 감사로그 | model_artifact, active_pointer, promotion_audit |
| **모니터링** | R1~R5 라우팅 모니터, 피드백 누적, 보정 과다/방어 발동 구간 | routing_monitor, sale_feedback |

### 7.2 백엔드 라우트(요약) & 권한

- 조회 라우트(`GET /admin/...`) = 운영자 읽기.
- 제어 라우트(재수집·재학습 트리거, 검수 처리, **승격/롤백**) = admin 권한 + `promotion_audit`/`review_queue` 기록.
- 승격/롤백은 서빙 설계 §9.4대로 admin 전용 + 감사 필수.

**실제 인증/인가(코덱스 P2-3 — "admin 권한"을 메커니즘으로)**: ①auth provider(세션 기반 로그인, 비밀번호 해시 또는 SSO) ②서버측 세션 + **CSRF 토큰**(상태변경 POST 전부) ③`user`/`role` 테이블(role∈{viewer, admin}) ④`promotion_audit.actor` 등 감사 actor는 **인증된 세션 사용자**에서만. 미인증 제어 호출은 401. 피드백/판매가 등 PII 접근은 role 게이트(서빙 §9.4).

### 7.3 잡 실행 모델

- 어드민의 "트리거" 버튼 = **`job` 테이블에 멱등키로 enqueue**(§3.7) → 즉시 응답 + `job.status` 폴링(HTMX).
- 장기 잡(크롤·학습)은 절대 요청 스레드에서 동기 실행하지 않음. 워커가 lease·heartbeat로 실행(§3.7 durable 잡).

---

## 8. 배포 토폴로지

```
dokploy project: track6-price-platform
├── mysql (dokploy 관리형)          ── 통합 system-of-record
├── app: price-serving (FastAPI)    ── 예측 API + active 버전 로드
└── app: price-admin+jobs (FastAPI) ── 어드민 UI + APScheduler + 백그라운드 잡(크롤/학습)
     └── (모델 번들 볼륨/스토리지 공유)
```

- 서빙과 어드민+잡을 분리해도 **MySQL 경합은 앱 분리로 격리 안 됨**(코덱스 P1-3) → §3 MySQL 격리(스키마/유저 분리·비동기 로깅·fail-open·풀 분리)를 반드시 적용. serving_log 부하가 커지면 별 인스턴스로 분리 가능하게 그룹 경계 유지.
- 스케줄러 인스턴스가 여러 개여도 **`scheduler_lock` 리더 1개만 트리거**(중복 실행 방지, §3.7). 워커는 N개 가능.
- 모델 번들은 공유 볼륨 또는 오브젝트 스토리지, MySQL은 경로·sha만.

---

## 9. 서브시스템 분해 & 구현 순서

각 서브시스템 = 별도 spec → plan → 구현 사이클.

**빌드 순서 재배치(코덱스 P2-1): 라이브 자산을 먼저 보호한다.** 처음 설계는 데이터 레이어부터였으나, 운영 리스크 관점에서 **이미 돌고 있는 서빙·641 로그가 최우선 보호 대상**이다. 따라서 스키마+마이그레이션 → 동결 아티팩트용 서빙 어댑터 → 최소 admin → 그 다음에 data/training 자동화.

| 순서 | 서브시스템 | 산출물 | 의존 |
|---|---|---|---|
| **0** | MySQL 스키마 + SQLite 마이그레이션 | §3 DDL(7그룹), 641건 무손실 이관(P1-8 절차) | — |
| **1** | Serving 연동 | **동결 아티팩트**용 active 포인터 로드 + 비동기 로그 적재 + 멀티워커 승격(§6) — 라이브 서빙을 새 DB 위로 먼저 이전 | 0 |
| **2** | 최소 Admin + 인증 + durable 잡 | auth/role/CSRF + 검수큐 + `job` 테이블 + 승격/롤백 + 감사(§7 v1, §3.7) | 0,1 |
| **3** | Data Plane | 4 크롤 → raw → 표준화 → snapshot 잡 (§4) | 0,2 |
| **4** | Training Plane | 재학습 오케스트레이션 + 게이트 + 레지스트리 승격 (§5) | 0~3 |
| **5** | 배포 + Admin v2 | dokploy 토폴로지(§8) + 대시보드/모니터링/수동입력/학습화면 확장 | 0~4 |

> 추천 첫 spec: **서브시스템 0+1(스키마+마이그레이션+서빙 어댑터)** — 라이브 로그·예측을 새 DB로 안전 이전하는 게 가장 먼저. data plane은 새 가치(재학습)의 입력이라 그 다음.

---

## 10. 검증 · 테스트 (플랫폼 차원)

서빙 설계 §12를 계승 + 플랫폼 항목 추가:

| 분류 | 테스트 |
|---|---|
| 마이그레이션 | SQLite 641 → MySQL 무손실(컬럼 매핑·ID/FK 정합·dry-run·**멱등 재실행**·롤백) (P1-8) |
| raw 디듑 | recrawl 시 여러 run 보존 + `content_hash`/`source_artwork_id` 논리 디듑, 덮어쓰기 0 (P1-2) |
| 소스 추적 | `source`+`source_row_index`+`run_id` 역추적, 소스 부분 재빌드 후 비대상 소스 불변 |
| 데이터 parity | 학습 vs 추론 feature 동일 + **`feature_schema_hash` 불일치 시 route unavailable** + golden fixture 회귀 (P1-9) |
| 스키마 | raw/std/snapshot enum·단위·통화 계약, manual 소스 raw→std 경로 (P1-7) |
| strict-Cold guard | Cold 실행 중 history/search/artist_key lookup 시 실패 + **reference pool 같은작가 제외** (P1-6) |
| 게이트 | 성능 게이트 통과/보류 분기, parity diff 0 |
| 레지스트리 | 불변 아티팩트, active=`active_pointer` 단일 진실, **멀티워커 로드 수렴 후 승격**, 롤백, 감사 (P1-5) |
| 권한/인증 | 승격/롤백 admin 전용 + 미인증 401 + CSRF + role 게이트 (P2-3) |
| 잡/스케줄러 | 비동기 실행·폴링·실패복구 + **멱등키 중복 차단** + **스케줄러 리더 단일 발화** + stale-lock 재큐 (P1-4) |
| MySQL 격리 | 서빙 로그 비동기 적재, 로깅 DB 장애 시 fail-open(예측 계속) (P1-3) |

---

## 11. 한 줄 정리

확정된 Warm/Cold 모델 위에, **4개 소스 크롤 → MySQL raw → 표준화 → train-ready snapshot → 재학습·게이트·불변 레지스트리 → active 포인터 교체로 무중단 서빙**까지를, 모든 상태를 MySQL 단일 원천에 두고 **어드민(FastAPI+HTMX)에서 검수·트리거·승격·모니터링**하는 4-플레인 플랫폼. 수동 데이터도 동일 표준 계약·동일 게이트로 합류한다. 상세 서빙·데이터·재학습 규칙은 2026-06-22 서빙 설계를 계승하고, 본 문서는 이를 MySQL·어드민·배포 위에서 통합·실체화한다.
