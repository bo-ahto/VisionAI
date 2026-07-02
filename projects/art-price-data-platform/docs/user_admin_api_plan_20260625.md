# 사용자 / 어드민 API 기획

작성일: 2026-06-25

대상:

- 가격 예측 사용자 화면 API
- 데이터 수집/검수 어드민 화면 API
- snapshot 생성/확인 API

목적:

- 사용자 화면과 어드민 화면에 필요한 API를 정의한다.
- API가 어떤 DB 테이블을 참조하는지 연결한다.
- DB 컬럼/enum 정의를 API 문서에서 중복하지 않고 MySQL 스키마 문서를 참조한다.
- 원천 사이트가 추가되거나 수동 CSV 데이터가 들어와도 같은 수집/검수/snapshot 흐름을 사용할 수 있게 API 경계를 정의한다.

관련 문서:

- [1차 개발 로드맵](first_development_roadmap_20260625.md)
- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
- [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)
- [NANT 재료(지지체/매체) 분류 기준](nant_material_classification_criteria_20260626.md)

## 1. 문서 역할

이 문서는 화면 기능을 서버 기능으로 옮기기 위한 API 기획 문서다.

```text
시나리오 문서
  -> 사용자가 어떤 상황에서 무엇을 하는지 정의
        |
        v
화면 구조 및 기능 기획
  -> 화면, 필터, 버튼, 상태 표시 정의
        |
        v
API 기획
  -> 화면 기능이 호출할 서버 기능 정의
        |
        v
MySQL 스키마 문서
  -> 테이블, 컬럼, enum, FK의 단일 기준
```

이 문서에는 DB 컬럼 전체를 복사하지 않는다. 테이블/컬럼/상태값의 단일 기준은 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)의 `5. MySQL 스키마 설계`다.

## 2. 공통 원칙

### 2.1 API 경로

권장 base path:

```text
/api/v1
```

리소스 구분:

| 영역 | prefix |
|---|---|
| 사용자 가격 예측 | `/api/v1/public` |
| 어드민 수집/검수 | `/api/v1/admin` |
| 내부 job 실행/상태 | `/api/v1/internal` |

`public`은 사용자 화면에서 호출하는 API라는 뜻이다. 인증이 필요 없는 공개 API라는 뜻은 아니다. 실제 인증 정책은 서비스 배포 정책에 맞춘다.

### 2.2 권한

| 역할 | 권한 |
|---|---|
| 일반 사용자 | 작가 검색, 신규 작가 후보 제출, 가격 예측 요청 |
| 운영 담당자 | 수집 run 확인, 재수집 요청, 검수 큐 처리, 보류/제외 처리 |
| 데이터 분석가 | 수동 CSV 업로드/매핑, snapshot 품질/분포 검토, 학습 피처 승격 판단 |
| 데이터 관리자 | 원천 등록/수정, 신규 `artist_key` 생성 승인, 기존 `artist_key` 연결 확정, snapshot 생성/서빙 승인, 모델 승인/승격/롤백/retire |
| 개발자 | crawler/parser 장애 확인, migration/배포 점검, 기술 로그 확인 |
| 슈퍼유저 | 운영 초기 전용 역할. 운영 담당자, 데이터 분석가, 데이터 관리자, 개발자 권한을 모두 수행 |

원칙:

- 일반 사용자는 최종 `artist_key`를 만들 수 없다.
- 신규 작가 후보 등록과 신규 `artist_key` 생성 승인은 별도 API다.
- 운영 초기에는 슈퍼유저 계정 1개 또는 소수 계정으로 시작할 수 있다. 이 경우 슈퍼유저는 모든 어드민 쓰기 API를 호출할 수 있지만, 응답/로그에는 실제 처리자의 `actor_id`와 처리 사유를 반드시 남긴다.
- 운영이 안정화되면 슈퍼유저를 상시 운영 역할로 쓰지 않고, 운영 담당자/데이터 분석가/데이터 관리자/개발자 역할로 분리한다.
- 모든 어드민 쓰기 API는 `actor_id`, 처리 시각, 처리 사유를 남긴다.

### 2.2.1 인증 주체와 권한 게이트

`actor_id`는 request body로 받지 않는다. 서버가 인증 컨텍스트(세션 또는 JWT claim)에서 인증된 주체를 식별해 주입한다.

- request body에 `actor_id`를 넣는 방식은 금지한다. body로 받으면 위조한 `actor_id`로 다른 사람 이름으로 처리할 수 있고, 감사 로그가 무력화된다.
- 따라서 이 문서의 쓰기 API request 예시에는 `actor_id`를 넣지 않는다. `actor_id`는 서버가 인증 컨텍스트에서 채우는 값으로, response/감사 로그(`10.1`) 필드로만 나타난다.
- 인증된 주체 식별자는 감사 로그(`10.1`)에 `request_id`와 함께 남긴다.
- 공용/공유 계정으로 어드민 쓰기 API를 호출하지 않는다. 처리자를 1인으로 특정할 수 없는 계정은 감사 추적을 깨뜨린다.

프론트 앱 분리 배포 기준:

- `service-web`과 `admin-web`은 별도 앱/배포 단위지만, 둘 다 이 API의 인증/권한 정책을 따른다([개발 착수 전 결정안](development_prestart_decisions_20260625.md) §3.10).
- 기본 origin은 `service.{base_domain}`, `admin.{base_domain}`, `api.{base_domain}`처럼 같은 site의 subdomain 분리를 권장한다.
- API CORS allowlist는 service/admin origin과 local dev origin만 허용한다. wildcard origin은 금지한다.
- 어드민 refresh token은 `HttpOnly; Secure; SameSite=Lax; Domain=.base_domain` 쿠키를 기본으로 하고, refresh/logout 등 쿠키가 개입되는 상태 변경 endpoint는 CSRF token 또는 double-submit 검증을 적용한다.
- browser public env와 서버 내부 env는 분리한다. 예: 앱별 public API base URL과 `INTERNAL_API_BASE_URL`을 섞지 않는다.

쓰기 엔드포인트 최소 권한(`required_role`):

| 엔드포인트 | 동작 | required_role |
|---|---|---|
| `GET /api/v1/admin/...` (조회 전반) | 대시보드/큐/상세 조회 (GET) | 운영 담당자 |
| `POST /api/v1/admin/collection-runs/{run_id}/actions` | 수집 run 재수집 (5.4) | 운영 담당자 |
| `POST /api/v1/admin/sources` · `PATCH /api/v1/admin/sources/{source}` | 원천 등록/수정 (6.x) | 데이터 관리자 |
| `POST /api/v1/admin/manual-imports` 계열 | 수동 CSV 업로드/매핑 (6.3/6.5) | 데이터 분석가 |
| `POST /api/v1/admin/model-training/jobs` | 모델 학습/import job 생성 (7.0) | 데이터 분석가 |
| `POST /api/v1/admin/model-versions/{model_version}/decision` | 후보 모델 승인/반려 (7.2.1) | 데이터 관리자 |
| `POST /api/v1/admin/model-deployments` (`promote`/`rollback`/`retire`) | 모델 승격/롤백/retire (7.3) | 데이터 관리자 |
| `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` | 작품 품질/작가명 검수(8.2/8.4) | 운영 담당자 |
| `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` | artist identity 후보 검토(8.6 `reject_candidate`/`hold`/`move_to_new_artist_candidate`) | 운영 담당자 |
| `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` | 기존 artist_key 연결 확정(8.6 `approve_existing_artist_key`) | 데이터 관리자 |
| `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` | 신규 작가 후보 검토(8.8 `recheck`/`hold`/`reject`) | 운영 담당자 |
| `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` | 신규 artist_key 생성(8.8 `approve`) | 데이터 관리자 |
| `POST /api/v1/admin/snapshots/requests` | snapshot 확정요청 (9.3.1) | 운영 담당자 |
| `POST /api/v1/admin/snapshots` | snapshot 생성승인 (9.3.2) | 데이터 관리자 |
| `POST /api/v1/admin/snapshots/{snapshot_id}/approve` | snapshot 서빙승인 (9.3.3) | 데이터 관리자 |
| `GET /api/v1/admin/audit-logs` | audit-logs 조회 (10.1) | 데이터 관리자 |

- 역할 위계는 개발자 < 운영 담당자 < 데이터 분석가 < 데이터 관리자이며, `required_role`은 해당 역할 "이상"을 의미한다(상위 역할은 하위 권한 포함). 1차는 이 상속형 RBAC로 구현하고, 직무별 capability matrix는 후속으로 분리한다.
- 후보 모델 승인/반려(7.2.1), 모델 승격/롤백/retire(7.3), artist identity 최종 확정(8.6 `approve_existing_artist_key`), 신규 artist_key 생성(8.8 `approve`), snapshot 생성승인(9.3.2) 및 snapshot 서빙승인(9.3.3)은 데이터 관리자 권한으로 게이트한다. 운영 담당자는 후보 보류/반려/재검토를 처리할 수 있지만 최종 artist_key 확정, 모델 승인/승격/롤백/retire, snapshot 서빙승인은 할 수 없다.
- 운영 초기 슈퍼유저는 위 역할을 모두 수행할 수 있으나, 실제 처리자 식별과 사유 기록 의무는 동일하게 적용된다.
- 전체 역할 매핑의 단일 기준은 [운영 파라미터](operational_parameters_20260625.md) §A-1.

### 2.3 사용자 화면 응답 제한

사용자 화면 API는 원천 추적용 정보를 기본 응답에 포함하지 않는다.

기본 응답에서 제외:

- `source`
- `source_artwork_url`
- `source_artist_id`
- `artist_source_id`
- `artist_source_url`
- raw payload 경로
- 원천별 내부 row ID

사용자에게 보여주는 정보:

- 서비스 표시용 작가명
- 생년, 국적, 활동지, 대표 작품처럼 작가 구분에 필요한 보조 정보
- 예측 가격
- 예측 신뢰도/검수 필요 사유
- 1차 시장 가격 카드 요약

어드민 API는 원천 추적용 정보를 표시해야 한다.

### 2.4 에러 형식

공통 에러 응답:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "가로 cm와 세로 cm를 입력해야 합니다.",
    "field_errors": [
      {"field": "width_cm", "message": "필수값입니다."}
    ],
    "request_id": "req_..."
  }
}
```

공통 에러 코드:

| 코드 | 의미 |
|---|---|
| `VALIDATION_ERROR` | 입력값 오류 |
| `NOT_FOUND` | 대상 없음 |
| `CONFLICT` | 이미 처리되었거나 상태 충돌 |
| `FORBIDDEN` | 권한 없음 |
| `UPSTREAM_UNAVAILABLE` | 수집/외부 원천 장애 |
| `PROCESSING_FAILED` | 내부 처리 실패 |

### 2.5 확장성 원칙

이 시스템은 Artsy / Saatchi / Print Bakery / Art1 네 곳만을 전제로 고정하지 않는다. 새 원천 사이트나 수동 CSV도 아래 공통 흐름에 태운다.

```text
source 등록
  -> crawler 또는 CSV upload로 raw 수집
  -> source_*_raw 저장
  -> source_*_interpreted_staging 생성
  -> normalized_*_staging 표준화
  -> 검수 큐
  -> snapshot 후보
```

원칙:

- 새 원천이 추가되어도 사용자 API 응답 구조는 바꾸지 않는다.
- 원천별 차이는 `source`, `metadata_json`, `parsed_parts_json`, `quality_flags_json`, 원천별 parser/normalizer 버전으로 흡수한다.
- CSV 업로드는 운영자가 직접 넣은 데이터지만, 예외 테이블로 바로 넣지 않는다. `manual_csv` 같은 하나의 source로 보고 raw 수집 레이어부터 같은 검수 흐름을 탄다.
- 원천별 컬럼명이 달라도 API는 공통 표준화 결과(`normalized_*_staging`, snapshot 집계)를 읽는다.
- 새 원천의 컬럼이 아직 표준화되지 않으면 공통 컬럼에 추측해서 넣지 않고 부가 JSON과 unmapped/quality flag로 남긴다.

### 2.6 데이터 최신성(freshness)

사용자 예측/가격 카드 응답은 어느 시점 데이터로 산출된 값인지 함께 표시한다.

서빙(정상) snapshot 정의:

- 사용자 서빙/freshness 비교 대상이 되는 최신 데이터 snapshot은 `status=approved`(운영 사용 승인 완료)이고 보존기간 내에 있는 snapshot뿐이다. 사용자 노출 `as_of`는 active deployment가 기록한 학습/import cutoff를 기준으로 하고, 최신 `approved` snapshot은 freshness 괴리 비교에 사용한다.
- `status=generated`는 빌드는 완료됐지만 운영 승인 전(비서빙) 상태다. 빌드 완료 snapshot이라도 데이터 관리자의 운영 승인을 받기 전에는 사용자 기준데이터로 쓰지 않는다.
- 그 외(만료·폐기·미승인 또는 `generated`) snapshot은 사용자 응답의 기준으로 쓰지 않는다.
- snapshot 생성 흐름과의 연결: `snapshot_request` 승인 → `generating` → `generated`(비서빙) → 데이터 관리자가 운영 승인하면 `artwork_snapshot.status=approved`(서빙 가능)로 전이한다(9.3). 미승인 `generated` snapshot이 사용자 기준데이터가 되지 않도록 서빙은 `approved`만 본다.

as_of 기준(모델이 실제 쓴 값):

- 사용자에게 노출하는 `as_of`는 "현재 active deployment가 학습에 사용한 데이터 cutoff"이다. 일반 재학습 모델은 training snapshot의 `source_cutoff_at`, legacy joblib import는 registry/import manifest의 `source_cutoff_at`을 사용한다(모델이 실제 쓴 값이며, 단순 최신 snapshot이 아니다). 7.0 / 7.3 / 9.3 참조.
- 예측/가격 카드는 이 active deployment 기준 snapshot을 참조한다. 응답에 `as_of`와 데이터 기준일을 표기한다.

지연 임계와 차단:

- SLA 문구: "운영 모델 기준, 최대 `N`일." active deployment의 `as_of`가 `N`=10일([운영 파라미터](operational_parameters_20260625.md) §E `FRESH-WARN-N`)을 초과하면 화면에 최신성 경고를 표시한다(카드는 계속 노출).
- 완전 차단 임계 `M`=21일(`M>N`, §E `FRESH-HIDE-M`)을 초과하면 구데이터의 무한 노출을 막기 위해 카드 자체를 숨긴다.
- 따라서 응답에는 기준일(`as_of`/`data_reference_date`)을 항상 포함해 화면이 경고/차단을 판단할 수 있게 한다.

deployment freshness vs 데이터 freshness 불일치:

- 두 snapshot의 역할을 구분한다: 사용자에게 노출하는 `as_of`/기준은 "현재 active deployment가 학습 또는 import 기준으로 기록한 `source_cutoff_at`"가 1차 기준이고, "마지막(최신) `approved` snapshot"은 그 1차 기준과 비교해 신선도 괴리를 판단하는 비교 대상일 뿐 사용자 `as_of`로 노출하지 않는다.
- `as_of`는 모델이 실제 학습/import 기준으로 기록한 cutoff이므로, 그 후 더 최신 `approved` snapshot이 생성·승인됐어도 운영 모델이 갱신되지 않았으면 `as_of`는 옛 값으로 남는다.
- active deployment의 학습/import cutoff와 현재 최신 `approved` snapshot의 `source_cutoff_at` 괴리가 임계 14일(§E `FRESH-MODEL-GAP`)을 초과하면, 데이터는 신선해도 모델이 옛 데이터를 쓰고 있다는 뜻이므로 신선도 경고를 띄운다.

### 2.7 동시성과 멱등(idempotency)

검수/생성 계열 쓰기 API는 동시 처리와 중복 호출을 전제로 설계한다.

- 검수 decision API(8.2/8.4/8.6/8.8)는 request에 `expected_review_status`(또는 리소스 version)를 받는다. 서버 상태와 불일치하면 처리하지 않고 `CONFLICT`를 반환한다. 마지막 호출이 무조건 이긴다(last-write-wins)면 이미 다른 담당자가 끝낸 결정을 덮어쓴다.
- 생성 계열(8.8 신규 `artist_key` 생성, 9.3 snapshot 생성, 6.1 원천 등록)은 `idempotency_key`를 받는다. 같은 키의 재요청은 새로 만들지 않고 직전 결과를 반환한다(네트워크 재시도/더블클릭 중복 생성 방지).
- 검수 큐 항목은 `standardization_review_item`의 claim/lock(담당자 + 만료시간) 또는 "검수 중" 상태를 둔다. 같은 항목을 두 사람이 동시에 처리하지 않게 한다. claim/lock 만료시간 기본값은 30분이며 방치 시 자동 해제한다([운영 파라미터](operational_parameters_20260625.md) §F `REVIEW-CLAIM-TTL`).

## 3. API 목록 요약

| 화면/기능 | API |
|---|---|
| 작가 검색 | `GET /api/v1/public/artists/search` |
| 신규 작가 후보 등록 | `POST /api/v1/public/artist-candidates` |
| 가격 예측 | `POST /api/v1/public/price-predictions` |
| 1차 시장 가격 카드 | `GET /api/v1/public/artists/{artist_key}/primary-market-summary` |
| 수집 대시보드 | `GET /api/v1/admin/collection-runs/summary` |
| 수집 run 목록 | `GET /api/v1/admin/collection-runs` |
| 수집 run 상세 | `GET /api/v1/admin/collection-runs/{run_id}` |
| 수집 run 조치 | `POST /api/v1/admin/collection-runs/{run_id}/actions` |
| 원천 목록 조회 | `GET /api/v1/admin/sources` |
| 원천 등록/수정 | `POST /api/v1/admin/sources`, `PATCH /api/v1/admin/sources/{source}` |
| 수동 CSV 업로드 | `POST /api/v1/admin/manual-imports` |
| 수동 CSV 업로드 상세 | `GET /api/v1/admin/manual-imports/{import_id}` |
| 수동 CSV 컬럼 매핑 확정 | `POST /api/v1/admin/manual-imports/{import_id}/mapping` |
| 표준화 검수 공통 큐 | `GET /api/v1/admin/standardization-review-items` |
| 표준화 검수 공통 처리 | `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` |
| 모델 학습/import job 생성 | `POST /api/v1/admin/model-training/jobs` |
| 모델 학습/import job 목록 | `GET /api/v1/admin/model-training/jobs` |
| 모델 학습/import job 상세 | `GET /api/v1/admin/model-training/jobs/{training_job_id}` |
| 모델 버전 목록 | `GET /api/v1/admin/model-versions` |
| 모델 버전 상세 | `GET /api/v1/admin/model-versions/{model_version}` |
| 후보 모델 승인/반려 | `POST /api/v1/admin/model-versions/{model_version}/decision` |
| 모델 승격/롤백/retire | `POST /api/v1/admin/model-deployments` |
| 현재 운영 모델 확인 | `GET /api/v1/admin/model-deployments/current` |
| 작품 품질 검수 큐 | `GET /api/v1/admin/review/artworks` 또는 공통 큐 `review_type=artwork_field` |
| 작품 품질 검수 처리 | `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` |
| 작가명 검수 큐 | `GET /api/v1/admin/review/artist-names` 또는 공통 큐 `review_type=artist_name_ko/artist_name_en` |
| 작가명 검수 처리 | `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` |
| artist_key 연결 검수 큐 | `GET /api/v1/admin/review/artist-identities` 또는 공통 큐 `review_type=artist_key` |
| artist_key 연결 검수 처리 | `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` |
| 신규 작가 후보 큐 | `GET /api/v1/admin/review/new-artists` 또는 공통 큐 `review_type=new_artist` |
| 신규 작가 후보 결정 | `POST /api/v1/admin/standardization-review-items/{review_item_id}/decision` |
| snapshot 후보 요약 | `GET /api/v1/admin/snapshots/candidates/summary` |
| snapshot 후보 목록 | `GET /api/v1/admin/snapshots/candidates/items` |
| snapshot 확정요청(운영자) | `POST /api/v1/admin/snapshots/requests` |
| snapshot 생성승인(데이터 관리자) | `POST /api/v1/admin/snapshots` |
| snapshot 서빙승인(데이터 관리자) | `POST /api/v1/admin/snapshots/{snapshot_id}/approve` |
| row 영향 범위 역조회 | `GET /api/v1/admin/normalized-artworks/{normalized_artwork_id}/impact` |
| 운영 로그 | `GET /api/v1/admin/audit-logs` |

## 4. 사용자 API

### 4.1 작가 검색

```text
GET /api/v1/public/artists/search
```

목적:

- 사용자가 입력한 작가명으로 확정 작가 후보를 찾는다.
- 동명이인 후보를 구분할 수 있는 보조 정보를 제공한다.
- 원천 사이트명/URL/ID는 응답하지 않는다.

query:

| 파라미터 | 필수 | 설명 |
|---|---|---|
| `q` | Y | 검색어 |
| `limit` | N | 기본 10 |

응답 예:

```json
{
  "items": [
    {
      "artist_key": "artist_123",
      "display_name_ko": "홍길동",
      "display_name_en": "Hong Gildong",
      "birth_year": 1980,
      "nationality": "Korean",
      "activity_location": "Seoul",
      "representative_artwork_count": 24,
      "has_price_history": true,
      "match_label": "이름 일치"
    }
  ],
  "total": 1
}
```

참조:

- 읽기: `artist_identity`, `artist_name_alias`, `artist_profile_meta` 현재값 조회
- 필요 시 읽기: `normalized_artist_staging`
- 상태 기준: `artist_identity.identity_status=active`

### 4.2 신규 작가 후보 등록

```text
POST /api/v1/public/artist-candidates
```

목적:

- 검색되지 않는 작가를 신규 작가 후보로 등록한다.
- 이 API는 최종 `artist_key`를 생성하지 않는다.

request:

```json
{
  "artist_name": "홍길동",
  "artist_name_language": "ko",
  "artist_name_en": "Hong Gildong",
  "artist_name_ko": "홍길동",
  "birth_year": 1980,
  "nationality": "Korean",
  "activity_location": "Seoul",
  "website_or_reference_url": "https://example.com/artist",
  "note": "사용자 입력 참고 메모"
}
```

response:

```json
{
  "candidate_id": "review_item_new_artist_123",
  "status": "needs_review",
  "message": "신규 작가 후보가 등록되었습니다."
}
```

참조:

- 쓰기: `normalized_artist_staging` 기반 신규 후보 상태 또는 신규 후보 view/export 대상
- 승인 전 `artist_identity.artist_key` 생성 금지
- 세부 기준: MySQL 문서 `5.0.5 신규 작가 후보 큐 기준`

### 4.3 가격 예측

```text
POST /api/v1/public/price-predictions
```

목적:

- 작품 정보와 선택 작가를 기반으로 가격 예측을 수행한다.
- 예측 가격, 신뢰도, 검수 필요 사유, 1차 시장 가격 카드를 반환한다.

request:

```json
{
  "artist_key": "artist_123",
  "artist_candidate_id": null,
  "title": "Untitled",
  "artwork_year": 2024,
  "width_cm": 60.0,
  "height_cm": 72.7,
  "depth_cm": null,
  "medium": "Oil",
  "support": "Canvas",
  "artwork_type": "painting"
}
```

입력 규칙:

- `width_cm`, `height_cm`는 필수다.
- `artist_key`가 있으면 확정 작가 기준으로 예측한다.
- `artist_candidate_id`만 있으면 작가 미확정 상태로 처리하고 검수 필요 표시를 반환한다.
- 재료/지지체가 DB active NANT mapping 기준으로 매핑되지 않거나 학습 제외 기준에 걸리면 예측 불가 또는 검수 필요로 분리한다.

response:

```json
{
  "prediction_id": "pred_123",
  "predicted_price_krw": 3500000,
  "display_price": "350만원",
  "display_hodang_price": "35만원/호",
  "confidence_label": "보통",
  "review_required": false,
  "review_reasons": [],
  "model": {
    "model_version": "official_v0_1_warm_20260625_01",
    "model_route": "warm",
    "deployment_id": "deploy_20260625_01"
  },
  "artist": {
    "artist_key": "artist_123",
    "display_name_ko": "홍길동",
    "display_name_en": "Hong Gildong"
  },
  "primary_market_summary": {
    "title": "1차 시장 가격",
    "hodang_median_label": "호당가 중앙값",
    "hodang_median_krw": 350000,
    "hodang_range_krw": [280000, 460000],
    "medium_distribution": [
      {"medium": "회화", "hodang_median_krw": 330000},
      {"medium": "드로잉", "hodang_median_krw": 280000}
    ],
    "sample_count": 24,
    "as_of": "2026-06-25T00:00:00Z",
    "data_reference_date": "2026-06-25"
  }
}
```

주의:

- `primary_market_summary`에는 원천 사이트명, 원천 URL, 원천 작품 ID를 넣지 않는다.
- `primary_market_summary`의 데이터 출처는 `primary_market_artist_summary`이며, active deployment의 `training_snapshot_id` 또는 import manifest cutoff에 맞는 row를 조회한다.
- `as_of`/`data_reference_date`는 active deployment가 학습/import 기준으로 기록한 cutoff 표기다(2.6 / 4.4).
- 예측 API는 수집 DB를 직접 조회하지 않고, 승인된 snapshot과 운영 feature store를 참조한다.
- 예측 응답에는 사용된 `model_version`, `model_route`, `deployment_id`를 남긴다. 모델이 중간에 바뀌어도 특정 예측이 어느 모델에서 나온 값인지 추적하기 위함이다.
- 응답의 `model_route`는 `price_prediction_log.route`(MySQL 문서 5.19)와 동일 값이며 표시 필드명만 다르다.
- 호당 표기는 표시용 참고값이며 모델 계산 기준이 아니다.

### 4.4 1차 시장 가격 카드 조회

```text
GET /api/v1/public/artists/{artist_key}/primary-market-summary
```

목적:

- 작가 상세 또는 예측 결과 화면에서 1차 시장 가격 참고 카드를 별도로 조회한다.

응답:

```json
{
  "artist_key": "artist_123",
  "as_of": "2026-06-25T00:00:00Z",
  "data_reference_date": "2026-06-25",
  "freshness_label": "운영 모델 기준, 최대 10일",
  "summary": {
    "title": "1차 시장 가격",
    "hodang_median_krw": 350000,
    "hodang_range_krw": [280000, 460000],
    "medium_distribution": [
      {"medium": "회화", "hodang_median_krw": 330000},
      {"medium": "드로잉", "hodang_median_krw": 280000}
    ],
    "sample_count": 24
  }
}
```

주의:

- `as_of`는 현재 active deployment가 학습/import 기준으로 기록한 `source_cutoff_at`(2.6 / 7.0 / 7.3 / 9.3)이며, `data_reference_date`는 화면 표시용 기준일이다.
- 조회 원천은 `primary_market_artist_summary`다. API 응답에는 집계값만 넣고 원천 사이트명/URL/원천 작품 ID는 넣지 않는다.
- `freshness_label`의 `N`(경고 임계, 허용 지연 상한)은 10일이다. `N`=10일 초과 시 경고, 완전 차단 임계 `M`=21일(M>N) 초과 시 카드를 숨긴다. 최신성 정책은 2.6을 따른다.

## 5. 어드민 수집 API

### 5.1 수집 대시보드 요약

```text
GET /api/v1/admin/collection-runs/summary
```

query:

| 파라미터 | 설명 |
|---|---|
| `from` | 조회 시작일 |
| `to` | 조회 종료일 |
| `source` | 원천 사이트 필터 |

response:

```json
{
  "last_finished_at": "2026-06-25T02:00:00Z",
  "overall_status": "warning",
  "sources": [
    {
      "source": "art1",
      "status": "success",
      "raw_artwork_rows": 1541,
      "normalized_artwork_rows": 1142,
      "size_parse_success_rate": 0.92,
      "price_present_rows": 980,
      "price_present_rate": 0.86,
      "total_failed": 0
    }
  ],
  "review_queue_counts": {
    "artworks": 20,
    "artist_names": 12,
    "artist_identities": 5,
    "new_artists": 8
  },
  "snapshot_candidate_count": 1100
}
```

화면 대응 수치:

- `size_parse_success_rate`: 화면의 "크기 파싱 성공률". 모집단은 해당 원천의 `normalized_artwork_rows`다.
- `price_present_rows` / `price_present_rate`: 화면의 "가격 보유 row 수" / "가격 보유율". 모집단은 해당 원천의 `normalized_artwork_rows`다(문의가 등 가격 없음 row 제외 비율).
- 두 비율의 분모(모집단)는 normalized 기준이다([운영 파라미터](operational_parameters_20260625.md) §H `SUMMARY-DENOM`).

참조:

- 읽기: `collector_run`, `raw_fetch`, `normalized_*_staging`, 검수 큐 집계

### 5.2 수집 run 목록

```text
GET /api/v1/admin/collection-runs
```

query:

| 파라미터 | 설명 |
|---|---|
| `source` | 원천 사이트 |
| `status` | `running`, `success`, `partial_success`, `failed` |
| `quality_status` | `ok`, `warning`, `blocked`. `blocked`는 이번 수집 결과를 snapshot 후보에 자동 포함하지 않는 반영 차단 상태 |
| `from` / `to` | 기간 |
| `page` / `page_size` | 페이지 |

### 5.3 수집 run 상세

```text
GET /api/v1/admin/collection-runs/{run_id}
```

응답 포함:

- run 시작/종료 시각
- 원천 사이트
- 수집 row 수
- 실패 URL 목록
- 실패 사유
- 품질 플래그
- raw/normalized row 수
- snapshot 반영 가능 여부

참조:

- 읽기: `collector_run`, `raw_fetch`, `source_artwork_raw`, `source_artist_raw`

### 5.4 수집 run 조치

```text
POST /api/v1/admin/collection-runs/{run_id}/actions
```

request:

```json
{
  "action": "request_retry",
  "scope": "failed_only",
  "reason": "상세 실패 URL만 재수집"
}
```

허용 action:

| action | 의미 |
|---|---|
| `approve_for_snapshot` | warning/partial_success run을 snapshot 후보로 승인 |
| `hold` | 반영 보류 |
| `request_retry` | 재수집 요청 |
| `clear_blocked_with_override` | 차단 상태를 사유와 함께 해제 |

`request_retry` 범위 파라미터:

| `scope` | 의미 |
|---|---|
| `failed_only` | 실패 URL/row만 재수집(기본 권장) |
| `full` | run 전체 재수집 |

- `scope` 미지정 시 기본값은 `failed_only`다(운영 비용상 실패분만 재수집; [운영 파라미터](operational_parameters_20260625.md) §H `RETRY-SCOPE-DEFAULT`).

쓰기:

- `collector_run.approved_by`
- `collector_run.approved_at`
- `collector_run.approval_note`
- `collector_run.override_reason`

## 6. 원천 확장 / 수동 업로드 API

### 6.1 원천 목록 조회

```text
GET /api/v1/admin/sources
```

목적:

- 현재 운영 중인 수집 원천과 수집 방식을 확인한다.
- 새 원천 추가 시 기존 원천과 같은 설정 구조를 쓰게 한다.

응답 항목:

- source 코드
- 표시명
- 수집 방식: `crawler`, `api`, `html`, `csv_upload`
- 활성 여부
- 마지막 성공 run
- 마지막 실패 run
- parser/normalizer 버전
- snapshot 반영 가능 여부

### 6.2 원천 등록/수정

```text
POST /api/v1/admin/sources
PATCH /api/v1/admin/sources/{source}
```

request 예:

```json
{
  "idempotency_key": "source_create_new_market_001",
  "source": "new_market",
  "display_name": "New Market",
  "collection_mode": "api",
  "is_enabled": false,
  "raw_payload_format": "json",
  "default_parser_version": "new_market_parser_2026_06_25",
  "default_normalizer_version": "normalizer_2026_06_25",
  "note": "신규 원천 테스트 등록"
}
```

주의:

- `POST`(원천 등록)는 `idempotency_key`로 중복 생성을 막는다. 같은 키의 재요청은 기존 원천을 그대로 반환한다(2.7).
- 원천 등록은 수집 가능 상태를 등록하는 것이지, 곧바로 학습 snapshot에 반영한다는 뜻이 아니다.
- 새 원천은 최소 1회 수집, raw 저장, staging 생성, 검수 큐 확인, snapshot 후보 검증을 통과한 뒤 활성화한다.
- 원천별 고유 컬럼은 API 응답 스키마를 늘리지 않고 `metadata_json` 또는 원천별 staging parser에서 관리한다.

참조:

- 원천 설정은 MySQL 문서의 `source_registry` 물리 테이블을 기준으로 저장한다.
- 운영 기준은 `source_registry`다.

### 6.3 수동 CSV 업로드

```text
POST /api/v1/admin/manual-imports
```

목적:

- 운영자가 외부에서 받은 작품/작가 CSV를 수동으로 추가한다.
- 수동 CSV도 예외 처리하지 않고 raw 수집 레이어부터 같은 표준화/검수/snapshot 흐름을 탄다.

request:

```json
{
  "source": "manual_csv",
  "file_name": "gallery_price_list_2026_06.csv",
  "source_label": "갤러리 제공 2026년 6월 가격표",
  "encoding": "utf-8",
  "delimiter": ",",
  "uploaded_by": "operator_123",
  "note": "협력 갤러리 수동 제공 데이터"
}
```

response:

```json
{
  "import_id": "manual_import_123",
  "status": "uploaded",
  "detected_columns": [
    "artist_name",
    "title",
    "width",
    "height",
    "price"
  ],
  "row_count": 100
}
```

주의:

- 업로드 직후에는 학습 데이터가 아니다.
- 컬럼 매핑, 가격/크기 파싱, 작가명 검수, 중복 확인, snapshot 후보 검증을 통과해야 반영된다.
- 수동 CSV도 `collector_run` 또는 import run으로 기록하고, `source_artwork_raw` / `source_artist_raw`에 원본 row를 보존한다.

### 6.4 수동 CSV 업로드 상세

```text
GET /api/v1/admin/manual-imports/{import_id}
```

응답 항목:

- 업로드 파일명
- 업로드 관리자
- row 수
- 감지된 컬럼
- 매핑 완료 여부
- 파싱 실패 row 수
- 중복 후보 수
- 검수 대기 수
- snapshot 후보 가능 row 수

### 6.5 수동 CSV 컬럼 매핑 확정

```text
POST /api/v1/admin/manual-imports/{import_id}/mapping
```

request 예:

```json
{
  "mapping": {
    "artist_name": "artist_name_raw",
    "title": "title_raw",
    "width": "width_raw",
    "height": "height_raw",
    "price": "price_raw",
    "currency": "price_currency"
  },
  "reason": "컬럼 의미 확인 후 매핑"
}
```

처리:

- 매핑 확정 후 `source_*_interpreted_staging` 생성 job을 실행한다.
- 매핑되지 않은 컬럼은 버리지 않고 원천 부가 정보 또는 unmapped 목록에 남긴다.
- 가격/크기/작가명처럼 핵심 컬럼이 매핑되지 않으면 snapshot 후보로 보내지 않는다.

## 7. 모델 버전 / 배포 API

모델 학습과 운영 모델 변경 수명주기는 [모델 학습과 운영 모델 변경 수명주기](model_training_deployment_lifecycle_20260626.md)를 기준으로 한다. API는 학습/import job, candidate 승인, active deployment 전환을 분리한다.

### 7.0 모델 학습/import job

```text
POST /api/v1/admin/model-training/jobs
GET /api/v1/admin/model-training/jobs
GET /api/v1/admin/model-training/jobs/{training_job_id}
```

목적:

- approved snapshot parquet export를 입력으로 모델 학습 job을 만든다.
- 기존 joblib bundle을 import할 때도 같은 job 이력으로 남긴다.
- job 상태와 artifact, metric, gate 결과를 조회한다.

POST request 예:

```json
{
  "route": "cold",
  "training_profile": "cold_k80_conservative",
  "training_snapshot_id": "snapshot_2026_06_25",
  "snapshot_export_id": "export_2026_06_25_parquet",
  "source_cutoff_at": "2026-06-25T00:00:00+09:00",
  "feature_generation_version": "feature_gen_20260625_01",
  "baseline_model_version": "cold_k80_conservative_official_v0.1",
  "reason": "approved snapshot 기준 cold route 재학습 후보 생성"
}
```

주의:

- `training_snapshot_id`는 `approved` snapshot만 허용한다.
- `generated` snapshot은 학습 입력으로 사용할 수 없다.
- 기존 legacy joblib import는 `training_snapshot_id` 없이도 가능하지만, `source_cutoff_at`, `source_manifest_uri`, artifact SHA-256을 반드시 제공한다.
- route는 `warm`/`cold`로 고정한다.
- model family, feature schema, serving input/output contract 변경은 이 API의 routine training/import로 처리하지 않고 별도 개발 작업으로 처리한다.
- job 생성은 운영 배포가 아니다.
- job이 `succeeded`가 된 뒤에만 `price_model_registry(candidate)` 등록이 가능하다.

### 7.1 모델 버전 목록

```text
GET /api/v1/admin/model-versions
```

목적:

- 학습되어 등록된 가격 예측 모델 버전을 조회한다.
- 운영 중인 모델, 후보 모델, 폐기된 모델을 구분한다.

query:

| 파라미터 | 설명 |
|---|---|
| `route` | `warm`, `cold` 모델 경로 |
| `status` | `candidate`, `approved`, `retired`, `rejected` |
| `page` / `page_size` | 페이지 |

응답 항목:

- 모델 버전
- 모델 경로
- training job ID
- 학습 snapshot ID
- feature generation 버전
- 학습 코드 버전
- artifact 경로
- feature schema hash
- 주요 성능 지표
- gate 결과
- parity 검증 상태
- 현재 배포 여부

### 7.2 모델 버전 상세

```text
GET /api/v1/admin/model-versions/{model_version}
```

응답 항목:

- 모델 버전
- 모델 경로
- training job ID
- 학습 snapshot ID
- train/validation/test split ID
- feature generation 버전
- 학습 코드 git SHA
- feature schema hash
- model artifact URI
- feature store URI
- 성능 지표 JSON
- gate 결과 JSON
- 검증 리포트 URI
- parity 검증 결과
- 승인자/승인시각/승인 사유

### 7.2.1 후보 모델 승인/반려

```text
POST /api/v1/admin/model-versions/{model_version}/decision
```

목적:

- `candidate` 모델을 `approved` 또는 `rejected`로 전환한다.
- 운영 배포 전 검증 gate 확인과 승인 사유를 남긴다.

request 예:

```json
{
  "decision": "approve",
  "reason": "validation/test, fixed-test parity, API smoke 통과",
  "known_limitations": "Art1 M1 범위 기준"
}
```

허용 decision:

| decision | 의미 | required_role |
|---|---|---|
| `approve` | 운영 배포 가능 모델로 승인 | 데이터 관리자 |
| `reject` | 후보 모델 반려 | 데이터 관리자 |

주의:

- approval은 운영 active 전환이 아니다.
- `approved` 모델만 7.3의 `promote` 대상이 될 수 있다.
- 승인자/승인시각은 인증 컨텍스트에서 채우며 request body로 받지 않는다.

### 7.3 모델 승격/롤백/retire

```text
POST /api/v1/admin/model-deployments
```

목적:

- 검증 완료된 모델을 운영 모델로 승격한다.
- 문제가 생기면 이전 모델로 롤백한다.

request 예:

```json
{
  "model_version": "official_v0_1_warm_20260625_01",
  "route": "warm",
  "action": "promote",
  "reason": "fixed test와 parity 검증 통과"
}
```

허용 action:

| action | 의미 |
|---|---|
| `promote` | approved 모델을 운영 active deployment로 승격 |
| `rollback` | 지정한 이전 모델로 운영 배포 전환 |
| `retire` | 더 이상 운영 후보로 쓰지 않음 |

주의:

- `candidate` 모델은 바로 배포하지 않는다.
- validation/test 성능, parity 검증, API smoke test를 통과한 `approved` 모델만 운영 승격할 수 있다.
- 모델 승격은 수집 snapshot 생성과 별도 단계다. 새 데이터가 수집되어도 자동으로 운영 모델이 바뀌지 않는다.
- 승격 후 serving adapter가 artifact SHA-256을 검증하고, prediction log에 새 `deployment_id`가 남는지 확인한다.

### 7.4 현재 운영 모델 확인

```text
GET /api/v1/admin/model-deployments/current
```

응답 예:

```json
{
  "items": [
    {
      "route": "warm",
      "model_version": "official_v0_1_warm_20260625_01",
      "deployment_id": "deploy_20260625_01",
      "deployed_at": "2026-06-25T02:00:00Z",
      "deployed_by": "data_admin_123"
    },
    {
      "route": "cold",
      "model_version": "official_v0_1_cold_20260625_01",
      "deployment_id": "deploy_20260625_02",
      "deployed_at": "2026-06-25T02:10:00Z",
      "deployed_by": "data_admin_123"
    }
  ]
}
```

## 8. 어드민 검수 API

검수 처리 API의 `decision` 동사는 [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md) 5.0.2의 검수 상태값으로 매핑된다.

| decision | 매핑 상태 |
|---|---|
| `approve` / `approve_with_edit` / `approve_existing_artist_key` | `review_status=approved` |
| `reject` / `reject_candidate` | `review_status=match_rejected` |
| `hold` | `review_status=needs_review` |
| `move_to_new_artist_candidate` | 해당 후보 연결을 `match_rejected`로 막고 신규 작가 후보 큐로 이동 |
| `add_alias`(8.4 전용) | review_status 전이가 아니라 해당 작가에 alias 1건 등록 |
| `register_override`(8.4 전용) | review_status 전이가 아니라 확정 한글명을 override로 등록(표준화 흐름 4.6). `expected_review_status` 비대상 |
| `recheck_candidates`(8.4) / `recheck`(8.8) | review_status 전이가 아니라 후보 재계산. conflict 검사·`expected_review_status` 비대상 |

`move_to_new_artist_candidate`는 별도 `new_artist_candidate` 테이블을 의미하지 않는다. 기존 artist_key 후보 연결을 반려하고 `standardization_review_item(review_type=new_artist)` 일감을 열거나 기존 열린 일감에 연결하는 동작이다.

작가명 검수(8.4)에서 alias 등록은 `decision=add_alias` 한 동사로만 한다. `approve`/`approve_with_edit`는 표시명을 승인할 뿐 alias를 등록하지 않는다. 화면의 "alias 추가" 버튼은 항상 `decision=add_alias`로만 보낸다(8.4).

작품 품질 검수(8.2)의 `approve`/`approve_with_patch`/`hold`/`exclude`는 별도 `review_status` enum이 아니라 `normalized_artwork_staging.quality_flags_json`과 snapshot 포함 여부(`artwork_snapshot_item.include_status`)로 표현한다. `exclude`는 `include_status=excluded`(+`exclude_reason`)에 대응한다.

큐 응답 ID와 decision 경로 정렬:

각 큐 응답의 item ID는 `standardization_review_item.review_item_id`다. 화면이 큐 항목에서 받은 `review_item_id`를 변환 없이 공통 decision API에 넘긴다. 화면별 `/review/artworks`, `/review/artist-names`, `/review/artist-identities`, `/review/new-artists` 조회 API는 공통 큐의 필터링 view/facade다.

| 큐 조회 | 큐 item ID 필드 | decision 경로 파라미터 |
|---|---|---|
| 작품 품질 (8.1) | `review_item_id` | `.../standardization-review-items/{review_item_id}/decision` |
| 작가명 (8.3) | `review_item_id` | `.../standardization-review-items/{review_item_id}/decision` |
| artist_key 연결 (8.5) | `review_item_id` | `.../standardization-review-items/{review_item_id}/decision` |
| 신규 작가 (8.7) | `review_item_id` | `.../standardization-review-items/{review_item_id}/decision` |

### 8.0 표준화 검수 공통 큐

```text
GET /api/v1/admin/standardization-review-items
POST /api/v1/admin/standardization-review-items/{review_item_id}/decision
```

query:

| 파라미터 | 설명 |
|---|---|
| `review_type` | `artist_name_ko`, `artist_name_en`, `artist_key`, `new_artist`, `nant_mapping`, `fx_rate`, `artwork_field`, `profile_meta` |
| `status` | `open`, `claimed`, `approved`, `rejected`, `applied`, `blocked` |
| `source` | 원천 |
| `issue_code` | 표준화가 막힌 사유 |
| `claim_by` | 담당자 |
| `page` / `page_size` | 페이지 |

공통 처리 원칙:

- `decision=approve` 또는 `approve_with_edit`은 `decision_value_json`을 저장하고, `target_action`에 따라 도메인 SoT에 적용한다.
- `artist_name_ko` 승인 결과는 `artist_name_alias`에 반영한다.
- `artist_key`/`new_artist` 승인 결과는 `artist_identity_candidate`, `artist_identity`, `identity_event_log`에 반영한다.
- `nant_mapping` 승인 결과는 active version 직접 수정이 아니라 draft `nant_material_mapping`에 반영하고, version validation/active 전환을 거친다.
- `fx_rate` 승인 결과는 `fx_rate_daily`에 반영한다.
- apply 완료 후 영향받은 row만 normalizer 재실행 대상이 되고, 그때 `normalized_artwork_staging` 생성이 가능해진다.

### 8.1 작품 품질 검수 큐 조회

```text
GET /api/v1/admin/review/artworks
```

이 조회 API는 `standardization_review_item.review_type=artwork_field` 및 작품 품질 이슈를 화면용으로 조인한 facade다.

query:

| 파라미터 | 설명 |
|---|---|
| `source` | 원천 사이트 |
| `price_status` | 가격 있음/없음/문의 |
| `size_status` | 크기 파싱 성공/실패 |
| `medium_status` | NANT 재료(지지체/매체) 분류 성공/실패/학습 제외 |
| `review_status` | 검수 상태 |
| `page` / `page_size` | 페이지 |

응답 항목:

- 원천 사이트
- 원천 작품 ID
- 원천 URL
- 원천값
- 분해/정리값
- 표준화 후보값
- NANT 분류값(`nant_support`, `nant_medium`, `nant_category_key`) 또는 `review_type=nant_mapping` 보류 사유
- 품질 플래그
- 처리 상태

참조:

- 읽기: `standardization_review_item`, `source_artwork_raw`, `source_artwork_interpreted_staging`, `normalized_artwork_staging`

### 8.2 작품 품질 검수 처리

```text
POST /api/v1/admin/standardization-review-items/{review_item_id}/decision
```

request:

```json
{
  "decision": "approve_with_patch",
  "expected_review_status": "needs_review",
  "patch": {
    "width_cm": 60.0,
    "height_cm": 72.7,
    "medium_raw": "Oil on canvas"
  },
  "reason": "원천 상세 페이지 확인 후 크기 수정"
}
```

- `patch`를 포함하는 검수는 `decision=approve_with_patch`로 보낸다. 수정 없이 후보값을 그대로 승인할 때만 `decision=approve`(이때 `patch` 미포함)다.

허용 decision:

| decision | 의미 |
|---|---|
| `approve` | 후보값 승인 |
| `approve_with_patch` | 수정 후 승인 |
| `hold` | 보류 |
| `exclude` | snapshot 제외 |

동시성:

- `expected_review_status`가 서버 현재 상태와 다르면 처리하지 않고 `CONFLICT`를 반환한다(2.7).

쓰기:

- `standardization_review_item.decision_value_json`/`status`
- `normalized_artwork_override`
- `normalized_artwork_change_event`

`approve_with_patch` 패치 적재(되돌리기/영향추적):

- `approve_with_patch`는 normalized 후보값을 직접 덮어쓰지 않는다. normalized 후보값(`*_candidate`)은 불변으로 유지하고, 패치는 override 레이어로 적용한다.
- 패치는 항목별 `(field, old_value, new_value)`를 append-only 이벤트로 적재한다. 이 이벤트(`normalized_artwork_change_event`)의 범위는 작품 normalized 필드 변경(크기/가격/재료 등 작품 검수 패치)으로 한정한다. artist identity 결정(연결 확정/신규 키 생성 등 비가역 결정)은 이 테이블이 아니라 `identity_event_log`(MySQL 5.12.1)가 SoT다(8.6/8.8, 12.1).
- 이 패치 이벤트가 `10.1` 감사 로그의 작품 필드 변경 before/after 원천이다. override는 언제든 사유와 함께 되돌릴 수 있고, 원본 후보값은 보존된다.

### 8.3 작가명 검수 큐 조회

```text
GET /api/v1/admin/review/artist-names
```

목적:

- 한글명/영문명 표시 후보와 alias 후보를 검수한다.
- 이 조회 API는 `standardization_review_item.review_type=artist_name_ko` 또는 `artist_name_en`을 화면용으로 조인한 facade다. 작가명 한글화 검수는 반드시 `artist_name_ko` 타입으로 등록한다.

각 큐 항목은 decision 경로 파라미터와 동일한 `review_item_id`를 item ID로 반환한다(8절 큐-decision 정렬 표). `alias_id`는 대상 row 참조로 함께 내려준다.

응답에 한글화 검수 필드를 포함한다(표준화 흐름 4.8 자동 산출값):

- `artist_name_ko_orig` 보정 전 한글명
- `artist_name_ko_input_type` 입력 유형(①~⑥)
- `artist_name_ko_reason` reason code
- `artist_name_ko_risk_score` / `artist_name_ko_risk_reasons` 위험 점수/사유
- `artist_name_ko_roundtrip_confidence` RR 역검증 신뢰도
- `artist_name_ko_override_status` override 등록 여부

정렬 기준은 `artist_name_ko_risk_score` 내림차순 → 영향 행수 내림차순(트리아지).

참조:

- 읽기: `standardization_review_item`, `normalized_artist_staging`, `artist_name_alias`

### 8.4 작가명 검수 처리

```text
POST /api/v1/admin/standardization-review-items/{review_item_id}/decision
```

request:

```json
{
  "decision": "approve",
  "expected_review_status": "needs_review",
  "display_name_ko": "홍길동",
  "display_name_en": "Hong Gildong",
  "reason": "작가 공식 표기 확인"
}
```

허용 decision:

- `approve`
- `approve_with_edit`
- `register_override` — 확정 한글명을 override로 등록(표준화 흐름 4.6)
- `add_alias` — 화면 "alias 추가" 버튼 대응. 해당 작가에 표시/연결 alias를 추가한다.
- `recheck_candidates` — 화면 "기존 후보 재검색" 버튼 대응. alias 후보를 다시 검색해 큐 항목을 갱신한다(쓰기 결정이 아니라 후보 재계산).
- `reject`
- `hold`

동시성:

- `expected_review_status`가 서버 현재 상태와 다르면 처리하지 않고 `CONFLICT`를 반환한다(2.7). `recheck_candidates`는 상태 전이가 아니므로 충돌 검사 대상이 아니다.

쓰기:

- `artist_name_alias.review_status`
- `artist_name_alias.approved_by`
- `artist_name_alias.approved_at`
- `artist_name_alias.approval_note`
- `standardization_review_item.status`/`decision_value_json`/`target_id`
- `register_override` 시: CSV를 직접 수정하지 않고 `artist_name_alias`에 승인 alias/override row를 추가한다. `artist_key`, `alias_name=artist_name_ko`, `source_name_normalized`, `reason_code`, `seed_source='admin_override'`, `approved_by/at`을 기록하고, 필요 시 `normalized_artist_staging.artist_name_ko_display`/`artist_name_ko_override_status=registered`를 반영한다.
- 필요 시 `normalized_artist_staging.artist_name_*_display`

### 8.5 artist_key 연결 검수 큐 조회

```text
GET /api/v1/admin/review/artist-identities
```

이 조회 API는 `standardization_review_item.review_type=artist_key`를 화면용으로 조인한 facade다. `candidate_id`는 대상 row 참조이고, decision path에는 `review_item_id`를 사용한다.

query:

| 파라미터 | 설명 |
|---|---|
| `source` | 원천 사이트 |
| `ambiguity_status` | `unique`, `ambiguous`, `needs_review` |
| `review_status` | `pending`, `needs_review`, `match_rejected` 등 |
| `alias_match_type` | `alias_exact`, `alias_approved`, `alias_fuzzy_only` |

참조:

- 읽기: `standardization_review_item`, `artist_identity_candidate`, `artist_identity`, `artist_name_alias`, `normalized_artist_staging`

### 8.6 artist_key 연결 검수 처리

```text
POST /api/v1/admin/standardization-review-items/{review_item_id}/decision
```

request:

```json
{
  "decision": "approve_existing_artist_key",
  "expected_review_status": "needs_review",
  "artist_key": "artist_123",
  "reason": "생년과 승인 alias가 일치"
}
```

허용 decision:

| decision | 의미 | required_role |
|---|---|---|
| `approve_existing_artist_key` | 기존 `artist_key`에 연결 | 데이터 관리자 |
| `reject_candidate` | 해당 후보와의 연결 반려 | 운영 담당자 |
| `hold` | 판단 보류 | 운영 담당자 |
| `move_to_new_artist_candidate` | 신규 작가 후보로 전환 | 운영 담당자 |

권한:

- endpoint 전체를 데이터 관리자 전용으로 묶지 않는다. 최종 `artist_key` 연결 확정(`approve_existing_artist_key`)만 데이터 관리자 권한이고, 보류/반려/신규 후보 전환은 운영 담당자 권한으로 처리한다(운영 파라미터 §A-1).

동시성:

- `expected_review_status`가 서버 현재 상태와 다르면 처리하지 않고 `CONFLICT`를 반환한다(2.7).
- `move_to_new_artist_candidate`는 신규 `artist_key`를 만들지 않고 `standardization_review_item(review_type=new_artist)` 일감만 만든다. 신규 `artist_key` 생성은 8.8의 `approve`에서만 가능하며, 이때 8.8의 `idempotency_key`로 중복 생성을 막는다.

쓰기:

- `artist_identity_candidate.review_status`
- `artist_identity_candidate.approved_by`
- `artist_identity_candidate.approved_at`
- `artist_identity_candidate.approval_note`
- `artist_identity_candidate.rejected_by`
- `artist_identity_candidate.rejected_at`
- `artist_identity_candidate.reject_reason`
- 승인 시 `artist_identity` 연결 근거 갱신
- `standardization_review_item.status`/`decision_value_json`/`target_id`

### 8.7 신규 작가 후보 큐 조회

```text
GET /api/v1/admin/review/new-artists
```

목적:

- 기존 `artist_key` 후보가 없는 신규 작가 후보를 조회한다.
- 이 큐는 최종 `artist_key` 테이블이 아니라 검수 대상 목록이다.
- 이 조회 API는 `standardization_review_item.review_type=new_artist`를 화면용으로 조인한 facade다. decision path에는 `review_item_id`를 사용한다.

응답 항목:

- 후보 ID
- 원천 사이트
- 원천 작가 ID/slug
- 원천 작가명
- 서비스 표시명 후보
- 작품 목록 요약
- 가격 보유 작품 수
- 원천 URL
- 유사 alias 검색 결과
- 보류/반려 이력

참조:

- 읽기: `standardization_review_item`, `normalized_artist_staging`, `artist_name_alias`
- 기준: MySQL 문서 `5.0.5 신규 작가 후보 큐 기준`

### 8.8 신규 작가 후보 결정

```text
POST /api/v1/admin/standardization-review-items/{review_item_id}/decision
```

화면(4.6)의 4개 버튼(신규 artist_key 생성 승인 / 기존 후보 재검색 / 보류 / 반려)을 단일 decision endpoint로 통합한다. `decision` 값으로 동작을 구분한다.

request(`decision=approve`, 신규 `artist_key` 생성):

```json
{
  "decision": "approve",
  "idempotency_key": "new_artist_create_2026_06_25_001",
  "expected_review_status": "needs_review",
  "canonical_name_ko": "홍길동",
  "canonical_name_en": "Hong Gildong",
  "birth_year": 1980,
  "nationality": "Korean",
  "reason": "기존 후보 없음, 작가 페이지와 작품 row 확인"
}
```

response(`decision=approve`):

```json
{
  "artist_key": "artist_456",
  "identity_status": "active",
  "created_at": "2026-06-25T02:00:00Z"
}
```

허용 decision:

| decision | 의미 | 화면 버튼(4.6) | required_role |
|---|---|---|---|
| `approve` | 신규 `artist_key`를 생성하고 후보를 확정 | 신규 artist_key 생성 승인 | 데이터 관리자 |
| `recheck` | 새 키를 만들기 전, 동일 작가가 기존에 있는지 이름/생년 조건으로 다시 검색해 후보를 갱신(상태 전이 아님, 후보 재계산) | 기존 후보 재검색 | 운영 담당자 |
| `hold` | 검수 대기 유지 | 보류 | 운영 담당자 |
| `reject` | 신규 작가로 쓰지 않음 | 반려 | 운영 담당자 |

쓰기:

- `approve` 시: `artist_identity`, `artist_profile_meta`, 필요 시 `artist_name_alias.artist_key`
- `hold`/`reject` 시: 신규 작가 후보의 `review_status`, 처리자/시각/사유(2.2.1)
- `standardization_review_item.status`/`decision_value_json`/`target_id`

권한/주의:

- endpoint 전체를 데이터 관리자 전용으로 묶지 않는다. 신규 `artist_key`를 실제 생성하는 `approve`만 데이터 관리자 권한이고, `recheck`/`hold`/`reject`는 운영 담당자 권한으로 처리한다(운영 파라미터 §A-1).
- `decision=approve`만 신규 `artist_key`를 생성할 수 있다. `recheck`/`hold`/`reject`는 키를 만들지 않는다.
- 일반 사용자 API에서는 호출할 수 없다.
- `approve`는 `idempotency_key`로 중복 생성을 막는다. 같은 키의 재요청은 이미 생성된 `artist_key`를 그대로 반환한다(2.7).
- 신규 `artist_key` 생성 시 원천에서 분해 가능한 작가 소개/학력/전시/팔로워 같은 프로필성 메타와 현재 표시값은 `artist_profile_meta`에 항목 단위로 만든다. 프로필성 메타는 `artist_identity`에 쓰지 않는다.
- `approve`/`hold`/`reject`는 `expected_review_status`가 서버 현재 상태와 다르면 처리하지 않고 `CONFLICT`를 반환한다(2.7). `recheck`는 상태 전이가 아니므로 충돌 검사 대상이 아니다(8.4 `recheck_candidates`와 동일 원칙).

### 8.9 NANT mapping 관리

NANT 재료(지지체/매체) mapping은 DB version으로 관리한다. CSV는 draft version import 원본이며, active version은 직접 수정하지 않는다.

Endpoints:

```text
GET  /api/v1/admin/nant/mapping-versions
POST /api/v1/admin/nant/mapping-versions/import
POST /api/v1/admin/nant/mapping-versions/{mapping_version_id}/validate
POST /api/v1/admin/nant/mapping-versions/{mapping_version_id}/activate
GET  /api/v1/admin/nant/mappings
POST /api/v1/admin/nant/mappings
PATCH /api/v1/admin/nant/mappings/{material_mapping_id}
DELETE /api/v1/admin/nant/mappings/{material_mapping_id}
GET  /api/v1/admin/nant/unmapped-materials
```

권한:

| 액션 | required_role |
|---|---|
| version/mapping/unmapped 조회 | 운영 담당자 |
| CSV import, draft row 추가/수정/삭제 | 데이터 분석가 |
| validate | 데이터 분석가 |
| activate | 데이터 관리자 |

version 응답 항목:

- `mapping_version_id`
- `version_key`
- `status`: `draft`/`active`/`archived`
- `source_file_sha256`
- `allowed_category_count`
- `mapping_row_count`
- `learning_excluded_count`
- `validation_status`
- `created_by`/`created_at`
- `activated_by`/`activated_at`

mapping row 응답 항목:

- `material_mapping_id`
- `mapping_version_id`
- `source_material_text`
- `nant_support`
- `nant_medium`
- `nant_category_key`
- `learning_excluded`
- `learning_exclusion_reason`
- `raw_note`/`raw_note2`/`raw_note3`
- `updated_by`/`updated_at`

처리 원칙:

- `POST /mapping-versions/import`는 새 `draft` version을 만든다. 기존 active version을 덮어쓰지 않는다.
- `PATCH`/`DELETE`는 `draft` version row에만 허용한다. active/archived row 수정은 `CONFLICT`로 거부한다.
- `activate`는 validation passed 상태에서만 허용한다. 성공 시 기존 active는 `archived`, 대상 draft는 `active`가 된다.
- snapshot 후보 query는 `normalized_artwork_staging.nant_*` 컬럼과 mapping row 조인을 사용한다. 과거 snapshot은 당시 `nant_mapping_version_id`를 고정한다.

참조:

- 읽기/쓰기: `nant_mapping_version`, `nant_allowed_category`, `nant_material_mapping`
- 읽기: `normalized_artwork_staging.nant_*`

## 9. Snapshot API

### 9.1 snapshot 후보 요약

```text
GET /api/v1/admin/snapshots/candidates/summary
```

응답 항목:

- 후보 row 수
- 포함 가능 row 수
- 제외 row 수
- 보류 row 수
- 사이트별 row 수
- 가격 보유율
- 크기 파싱 성공률
- NANT 분류 성공/학습 제외/unmapped 수
- 작가 확정률
- 직전 snapshot 대비 변화량

참조:

- 읽기: `normalized_artwork_staging`, `normalized_artist_staging`, `artist_identity`

### 9.2 snapshot 후보 목록

```text
GET /api/v1/admin/snapshots/candidates/items
```

query:

| 파라미터 | 설명 |
|---|---|
| `source` | 원천 사이트 |
| `include_status` | 포함/제외 후보 |
| `exclude_reason` | 제외 사유. NANT 제외는 `nant_learning_excluded`. 매핑 실패/검수 필요 재료는 snapshot 전에 `standardization_review_item(review_type=nant_mapping)`에서 해결한다 |
| `artist_identity_status` | 작가 확정 상태 |
| `page` / `page_size` | 페이지 |

### 9.3 snapshot 확정요청 / 생성승인 / 서빙승인

snapshot 전이는 **3단계**로 나뉘며, 각 단계는 서로 다른 액션·엔드포인트다.

1. **요청 확정 (운영자, 9.3.1)** — 운영자가 후보 범위/규칙을 고정한 생성요청을 만든다(`snapshot_request`). snapshot을 직접 만들지 않는다.
2. **생성 승인 (데이터 관리자, 9.3.2)** — 데이터 관리자가 확정요청을 받아 실제 snapshot을 만든다. 결과는 `artwork_snapshot.status=generated`(빌드 완료·비서빙)다.
3. **서빙 승인 (데이터 관리자, 9.3.3)** — 데이터 관리자가 `generated` snapshot을 운영 사용 승인해 `status=approved`(서빙 가능)로 올린다.

한 번의 호출로 운영자가 곧장 snapshot을 생성하지 않게, 그리고 생성과 서빙 노출을 분리하기 위해 세 액션을 나눈다. 사용자 서빙/freshness 기준이 되는 정상 snapshot은 `approved`뿐이며(2.6), `generated`까지만으로는 사용자 `as_of`/freshness 기준이 되지 않는다.

#### 9.3.1 확정요청 (운영자)

```text
POST /api/v1/admin/snapshots/requests
```

request:

```json
{
  "idempotency_key": "snapshot_req_2026_06_25_001",
  "snapshot_name": "train_candidate_2026_06_25",
  "source_cutoff_at": "2026-06-25T00:00:00Z",
  "rules_version": "rules_2026_06_25",
  "reason": "주간 수집 검수 완료, 생성 요청"
}
```

response:

```json
{
  "snapshot_request_id": "snapshot_req_2026_06_25",
  "status": "requested",
  "candidate_included_count": 12000,
  "candidate_excluded_count": 300
}
```

- required_role: 운영자. snapshot을 직접 만들지 않고 후보 범위/규칙을 고정한 생성요청만 만든다.
- `idempotency_key`로 중복 요청을 막는다(2.7).

#### 9.3.2 생성승인 (데이터 관리자)

```text
POST /api/v1/admin/snapshots
```

request:

```json
{
  "idempotency_key": "snapshot_create_2026_06_25_001",
  "snapshot_request_id": "snapshot_req_2026_06_25",
  "reason": "확정요청 검토 완료, snapshot 생성 승인"
}
```

response:

```json
{
  "snapshot_id": "snapshot_2026_06_25",
  "snapshot_name": "train_candidate_2026_06_25",
  "included_count": 12000,
  "excluded_count": 300,
  "created_at": "2026-06-25T02:00:00Z"
}
```

- required_role: 데이터 관리자(2.2.1). 확정요청(`snapshot_request_id`)을 받아 실제 snapshot을 생성한다.
- `snapshot_name`은 승인 request에 다시 받지 않는다. 확정요청(9.3.1)에서 입력한 `snapshot_request.snapshot_name`이 영속 출처이므로, 승인 endpoint가 `snapshot_request_id`만 넘겨도 그 이름이 `artwork_snapshot.snapshot_name`으로 재현돼 response에 그대로 반환된다(SoT §5.14.1).
- 생성 완료 snapshot은 `artwork_snapshot.status=generated`(비서빙)로 만들어진다. 이 endpoint는 `generated`까지만 만든다. 서빙 대상으로 올리려면 별도 액션인 서빙 승인(9.3.3)으로 `status=approved`로 전이해야 한다(2.6). `generated` 상태로는 사용자 `as_of`/freshness 기준이 되지 않는다.
- 생성승인의 `idempotency_key`는 확정요청(9.3.1)의 요청 `idempotency_key`와 별개 값이다. 요청 `idempotency_key`는 `snapshot_request`의 요청 멱등키로, 생성승인 `idempotency_key`는 같은 `snapshot_request` 행의 `approval_idempotency_key`(생성승인 전용) 컬럼에 저장·replay된다(SoT §5.14.1). 이 컬럼은 전역 UNIQUE다. 따라서 같은 `snapshot_request_id`에 대한 생성승인 중복 호출(네트워크 재시도/더블클릭)은 `approval_idempotency_key`로 판별돼 새 snapshot을 다시 만들지 않고 이미 만든 `snapshot_id`를 그대로 반환한다(중복 승인/중복 생성 방지, 2.7). 같은 키에 다른 payload가 오면 충돌로 거부한다. 이 컬럼은 생성승인 전용이며, 서빙승인(9.3.3)의 멱등키는 별개 컬럼(`artwork_snapshot.serving_approval_idempotency_key`, SoT §5.13)에 저장된다(한 컬럼 공유 안 함).

쓰기:

- `artwork_snapshot`
- `artwork_snapshot_item`

주의:

- `collector_run.status=failed` 또는 `collector_run.quality_status=blocked`인 run은 자동 포함하지 않는다.
- `blocked`는 수집 결과 삭제가 아니라 snapshot 자동 반영 차단 상태다. 운영자 override 사유가 있을 때만 후보에 포함할 수 있다.
- 환율이 없어 `price_krw_normalized`를 만들 수 없는 row는 snapshot 포함 대상에서 제외한다.
- DB active NANT mapping 기준 `learning_excluded=true` row는 `exclude_reason=nant_learning_excluded`로 제외한다. 매핑 실패 row는 snapshot 후보가 아니라 `standardization_review_item(review_type=nant_mapping)`에 보류한다. 기존 재료/지지체 하드코딩 학습 필터는 사용하지 않는다.

#### 9.3.3 서빙승인 (데이터 관리자)

```text
POST /api/v1/admin/snapshots/{snapshot_id}/approve
```

목적:

- `generated`(빌드 완료·비서빙) snapshot을 운영 사용 승인해 서빙 대상으로 올린다.
- 생성승인(9.3.2)과 별개 액션이다. 생성은 snapshot을 만들 뿐이고, 서빙 대상 전환은 이 액션으로만 일어난다(실제 사용자 노출은 이 snapshot으로 학습·승격된 모델이 배포된 뒤).

request:

```json
{
  "idempotency_key": "snapshot_approve_2026_06_25_001",
  "reason": "생성 snapshot 검토 완료, 서빙 사용 승인"
}
```

response:

```json
{
  "snapshot_id": "snapshot_2026_06_25",
  "status": "approved",
  "approved_at": "2026-06-25T02:30:00Z"
}
```

효과:

- `artwork_snapshot.status` `generated` → `approved`. 이 전이 이후에만 해당 snapshot이 사용자 서빙/freshness 기준이 된다(2.6).

처리 규칙:

- required_role: 데이터 관리자(2.2.1). 운영자는 snapshot을 서빙 대상으로 승인할 수 없다.
- `idempotency_key`는 `artwork_snapshot.serving_approval_idempotency_key` 컬럼에 저장·replay된다(SoT §5.13). 이 컬럼은 생성승인(9.3.2)의 `snapshot_request.approval_idempotency_key`와 별개 컬럼/저장소다(서빙승인 전용). 이 컬럼은 전역 UNIQUE이므로, 같은 키의 재호출(네트워크 재시도/더블클릭)은 다시 전이시키지 않고 직전 결과(`approved` 상태와 `snapshot_id`)를 그대로 반환한다(2.7). 같은 키에 다른 payload(다른 `snapshot_id`/`reason`)가 오면 충돌로 거부한다.
- `generated` 상태가 아닌 snapshot(이미 `approved`이거나 만료·폐기 등)에 대한 호출은 새로 전이하지 않고 `CONFLICT`(또는 멱등 재호출이면 직전 결과)를 반환한다.
- 서빙 승인의 영속 기준은 `artwork_snapshot.approved_by`/`approved_at`/`approval_note` 컬럼이다(SoT). 이 전이 시 세 컬럼을 채우는 것이 승인 사실의 단일 출처이며, 운영 로그(10.1)는 부가 감사로만 남긴다. `approved_by`(=`actor_id`)는 body로 받지 않고 인증 컨텍스트에서 주입한다(2.2.1).

쓰기:

- `artwork_snapshot.status`(`generated` → `approved`)
- `artwork_snapshot.serving_approval_idempotency_key`(서빙승인 멱등키, 전역 UNIQUE; 생성승인의 `snapshot_request.approval_idempotency_key`와 별개 컬럼)
- `artwork_snapshot.approved_by`/`approved_at`/`approval_note`(서빙 승인의 영속 기준 = 이 컬럼; 운영 로그 10.1은 부가 감사)

### 9.4 row 영향 범위 역조회

```text
GET /api/v1/admin/normalized-artworks/{normalized_artwork_id}/impact
```

목적:

- 잘못된 row가 어느 snapshot에, 어느 배포에 반영됐는지 역조회한다.
- 작품 row → `artwork_snapshot_item` → `artwork_snapshot` → 그 snapshot으로 학습된 모델/배포까지 영향 범위를 산정한다.

응답 항목:

- 대상 `normalized_artwork_id`와 현재 include_status
- 포함된 snapshot 목록(`snapshot_id`, `include_status`, `source_cutoff_at`)
- 각 snapshot으로 학습된 `model_version` 목록
- 그 모델이 운영에 올라간 적이 있으면 `deployment_id`와 배포 기간

참조:

- 읽기: `artwork_snapshot_item`, `artwork_snapshot`, 모델 학습 job/registry 매핑(7.0~7.2), `price_model_deployment`

주의:

- 이 조회는 영향 산정용 읽기 전용이다. row 정정 자체는 8.2 검수 처리로 한다.

## 10. 운영 로그 API

### 10.1 운영 로그 조회

```text
GET /api/v1/admin/audit-logs
```

query:

| 파라미터 | 설명 |
|---|---|
| `entity_type` | `collection_run`, `artwork`, `artist_name`, `artist_identity`, `snapshot`, `model_training_job`, `model_version`, `model_deployment`, `nant_mapping_version`, `nant_material_mapping` |
| `entity_id` | 대상 ID |
| `actor_id` | 처리자 |
| `from` / `to` | 기간 |

응답 항목:

- 발생 시각
- 대상 유형
- 대상 ID
- 이벤트 유형
- 이전 상태(before)
- 변경 후 상태(after)
- 처리자(인증 컨텍스트에서 식별한 주체 식별자, 2.2.1)
- `request_id`(요청 추적용)
- 처리 사유

주의:

- 이 API는 1차에서 별도 audit write SoT를 만들지 않고, 도메인별 SoT 테이블의 처리자/시각/사유 컬럼을 읽는 조회 facade다. 통합 audit 테이블 확대는 고도화 대상이다(12.1).
- 작품 field patch의 before/after 단일 기준은 MySQL 문서 [`periodic_raw_collection_mysql_plan_20260623.md`](periodic_raw_collection_mysql_plan_20260623.md)의 §5.8.1 `normalized_artwork_change_event`(append-only)다.
- 비가역 artist identity 결정은 §5.12.1 `identity_event_log`를 source로 읽는다.
- 모델 학습/import, 후보 승인/반려, 운영 승격/롤백/retire 이력은 `model_training_job`, `price_model_registry`, `price_model_deployment`의 상태/처리자/시각/사유 컬럼을 source로 읽는다.
- NANT CSV import, draft row 편집, active 전환 이력은 `nant_mapping_version`과 `nant_material_mapping`의 생성/수정/활성화 처리자 컬럼을 source로 읽는다. active version row 직접 수정은 금지되므로, active 변경 이력은 새 draft 생성 후 activate 이벤트로 남긴다.
- 처리자는 body 입력값이 아니라 인증 주체이며, `request_id`와 함께 남겨 단일 요청 단위로 추적한다.

## 11. API 작성 기준

API 구현 시 반드시 지켜야 할 기준:

- 사용자 API와 어드민 API 응답 필드를 분리한다.
- 사용자 API에는 원천 사이트명/URL/ID를 노출하지 않는다.
- 신규 작가 후보 등록과 신규 `artist_key` 생성 승인은 분리한다.
- 새 원천 사이트와 수동 CSV는 별도 예외 경로가 아니라 raw -> interpreted staging -> normalized staging -> 검수 -> snapshot 흐름으로 처리한다.
- 원천별 고유 컬럼은 공통 컬럼에 추측해서 채우지 않고 부가 JSON과 품질 플래그로 보존한다.
- `artist_identity.identity_status=active`인 작가만 사용자 검색의 기본 결과로 노출한다.
- 검수 상태값은 MySQL 문서 `5.0.2 상태값 기준`을 따른다.
- 모든 어드민 쓰기 API는 처리자, 처리시각, 처리 사유를 남긴다.
- `actor_id`는 request body로 받지 않고 인증 컨텍스트에서 주입한다(2.2.1). 인증은 본 설계의 전제다(12.0).
- 검수 decision API는 `expected_review_status`로 충돌을 검사하고, 생성 계열은 `idempotency_key`로 중복 생성을 막는다(2.7).
- 사용자 예측/가격 카드 응답에는 active deployment가 기록한 `as_of`/기준일을 표기한다(2.6).
- 수집 DB 장애가 가격 예측 API 장애로 번지지 않게 예측 API는 운영 feature store와 모델 번들을 우선한다.
- snapshot 생성은 `artwork_snapshot`과 `artwork_snapshot_item`에 남기고, 모델 학습/import는 approved snapshot export를 기준으로 `model_training_job`에 남긴다.
- 모델 candidate 등록, 승인/반려, 운영 승격, 롤백은 API와 DB에 이력으로 남긴다.
- 예측 응답과 예측 로그에는 `model_version`과 `deployment_id`를 남긴다.

## 12. 정책 확정/조정 항목 (운영 파라미터 참조)

> 운영 임계·기간·역할 등 정책 상수는 [운영 파라미터](operational_parameters_20260625.md)에서 기본값으로 확정되어 있다. 개발 착수 전에 고정해야 하는 구조적 선택은 [개발 착수 전 결정안](development_prestart_decisions_20260625.md)을 따른다. 아래는 그 전제와, 조직 정책/운영 실측에 따라 갱신할 항목을 정리한 것이다.

### 12.0 전제(precondition)

인증 방식은 "다음에 정할 항목"이 아니라 본 설계의 전제다. `actor_id` 서버 주입(`2.2.1`)과 권한 게이트가 인증 컨텍스트 위에서만 성립하기 때문이다.

- 기본 인증 방식은 JWT 액세스 토큰 + 역할 claim(액세스 60분 / 리프레시 14일)으로 결정한다([운영 파라미터](operational_parameters_20260625.md) §A `AUTH-METHOD`/`AUTH-TOKEN-TTL`). `actor_id`는 토큰 claim에서 서버가 주입한다(2.2.1). 프론트 분리 배포의 origin/CORS/refresh cookie/CSRF 기본값도 운영 파라미터 §A의 `AUTH-ORIGIN-POLICY`/`AUTH-CORS-POLICY`/`AUTH-ADMIN-REFRESH-COOKIE`/`AUTH-CSRF-POLICY`를 따른다. 이 값은 조직 정책 확정 시 갱신한다.
- 인증 컨텍스트에서 주체를 식별하는 방식이 운영되기 전에는 어드민 쓰기 API를 열지 않는다. 인증 미정 상태에서 쓰기 API를 열면 `actor_id` 위조 차단과 `required_role` 게이트가 무력화된다.
- 세션/내부 관리자 계정 등 구체 구현 방식은 조직 정책 확정 시 갱신하되, "인증 컨텍스트에서 주체를 식별한다"는 전제 자체는 협상 대상이 아니다.

### 12.1 그 외 정책/실측 조정 항목

아래 항목은 [운영 파라미터](operational_parameters_20260625.md)에서 기본값으로 확정되어 있으며, 조직 정책 또는 운영 실측 후 갱신한다.

| 항목 | 결정 필요 내용 |
|---|---|
| 인증 방식 상세 | 사용자는 로그인 없이 first-party 익명 세션 + rate limit을 기본값으로 둔다. 어드민은 제공 이메일/비밀번호 로그인 후 JWT 액세스 토큰 + 역할 claim을 발급한다. SSO는 후속 도입 예정이다([개발 착수 전 결정안](development_prestart_decisions_20260625.md) §3.1/§3.2). 토큰 TTL은 [운영 파라미터](operational_parameters_20260625.md) 기준을 따른다. |
| freshness 임계 `N`/`M` | 예측/가격 카드 `as_of` 경고 임계 `N`일·카드 차단 임계 `M`일(M>N)·deployment 괴리 경고 임계(2.6 / 4.4) → [운영 파라미터](operational_parameters_20260625.md)에서 기본값 확정, 운영 실측/정책 확정 시 갱신 |
| 신규 작가 후보 저장 방식 | 사용자 신규 작가 후보 제출을 M1에 포함하므로 `standardization_review_item(review_type=new_artist)`를 물리 큐로 1차 DDL에 포함한다([개발 착수 전 결정안](development_prestart_decisions_20260625.md) §3.4). 별도 `new_artist_candidate` 테이블은 만들지 않는다. |
| 수동 CSV 업로드 파일 저장 위치 | `manual_import_file.file_uri`는 `manual/{env}/source={source}/dt={YYYY-MM-DD}/import={import_id}/original.csv` 규칙을 기본값으로 둔다([개발 착수 전 결정안](development_prestart_decisions_20260625.md) §2). row 처리 구조는 MySQL 문서 5.3.1의 `manual_import_file` + `collector_run` 기준으로 확정 |
| 운영 로그 저장 방식 | `GET /api/v1/admin/audit-logs`는 별도 audit write SoT가 아니라 도메인별 SoT 읽기 facade다. 작품 field patch는 `normalized_artwork_change_event`, 비가역 작가 identity 결정은 `identity_event_log`, 모델 운영은 `model_training_job`/`price_model_registry`/`price_model_deployment`, NANT 운영은 `nant_mapping_version`/`nant_material_mapping`의 처리자·시각·사유 컬럼을 사용한다. 검수 큐 claim/lock TTL 등 동시성 수치 → [운영 파라미터](operational_parameters_20260625.md)에서 기본값 확정, 운영 실측/정책 확정 시 갱신. 전체 필드 변경 audit 테이블 확대는 고도화 |
| 예측 API 연결 방식 | 기존 예측 API를 호출하지 않고, 데이터 수집 서비스 내부 joblib serving adapter가 active deployment의 joblib artifact를 직접 로드한다([개발 착수 전 결정안](development_prestart_decisions_20260625.md) §3.6). |
| 1차 시장 가격 카드 데이터 위치 | approved snapshot 생성 시 `primary_market_artist_summary`를 만들고, API는 active deployment의 training snapshot 또는 import manifest cutoff 기준 row를 조회한다([개발 착수 전 결정안](development_prestart_decisions_20260625.md) §2). |
