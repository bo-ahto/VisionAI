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

- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
- [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [원천 사이트별 수집 항목 정리](source_site_collected_fields_20260624.md)

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
| 운영자 | 수집 run 확인, 검수 큐 처리, 보류/제외 처리 |
| 데이터 관리자 | 신규 `artist_key` 생성 승인, 기존 `artist_key` 연결 확정, snapshot 생성 승인 |
| 개발자 | 원천 등록, 수집 재실행, parser 장애 확인, 기술 로그 확인 |

원칙:

- 일반 사용자는 최종 `artist_key`를 만들 수 없다.
- 신규 작가 후보 등록과 신규 `artist_key` 생성 승인은 별도 API다.
- 모든 어드민 쓰기 API는 `actor_id`, 처리 시각, 처리 사유를 남긴다.

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
| 모델 버전 목록 | `GET /api/v1/admin/model-versions` |
| 모델 버전 상세 | `GET /api/v1/admin/model-versions/{model_version}` |
| 모델 승격/롤백 | `POST /api/v1/admin/model-deployments` |
| 현재 운영 모델 확인 | `GET /api/v1/admin/model-deployments/current` |
| 작품 품질 검수 큐 | `GET /api/v1/admin/review/artworks` |
| 작품 품질 검수 처리 | `POST /api/v1/admin/review/artworks/{normalized_artwork_id}/decision` |
| 작가명 검수 큐 | `GET /api/v1/admin/review/artist-names` |
| 작가명 검수 처리 | `POST /api/v1/admin/review/artist-names/{alias_id}/decision` |
| artist_key 연결 검수 큐 | `GET /api/v1/admin/review/artist-identities` |
| artist_key 연결 검수 처리 | `POST /api/v1/admin/review/artist-identities/{candidate_id}/decision` |
| 신규 작가 후보 큐 | `GET /api/v1/admin/review/new-artists` |
| 신규 artist_key 생성 승인 | `POST /api/v1/admin/review/new-artists/{candidate_id}/approve` |
| snapshot 후보 요약 | `GET /api/v1/admin/snapshots/candidates/summary` |
| snapshot 후보 목록 | `GET /api/v1/admin/snapshots/candidates/items` |
| snapshot 생성 | `POST /api/v1/admin/snapshots` |
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

- 읽기: `artist_identity`, `artist_name_alias`
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
  "candidate_id": "new_artist_candidate_123",
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
- 조각, 설치, 영상, 혼합매체 후보는 예측 불가 또는 검수 필요로 분리한다.

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
    "sample_count": 24
  }
}
```

주의:

- `primary_market_summary`에는 원천 사이트명, 원천 URL, 원천 작품 ID를 넣지 않는다.
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
  "action": "hold",
  "reason": "상세 실패율이 높아 이번 snapshot 반영 보류",
  "actor_id": "admin_123"
}
```

허용 action:

| action | 의미 |
|---|---|
| `approve_for_snapshot` | warning/partial_success run을 snapshot 후보로 승인 |
| `hold` | 반영 보류 |
| `request_retry` | 재수집 요청 |
| `clear_blocked_with_override` | 차단 상태를 사유와 함께 해제 |

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
  "source": "new_market",
  "display_name": "New Market",
  "collection_mode": "api",
  "default_enabled": false,
  "raw_payload_format": "json",
  "parser_version": "new_market_parser_2026_06_25",
  "normalizer_version": "normalizer_2026_06_25",
  "note": "신규 원천 테스트 등록"
}
```

주의:

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
  "reason": "컬럼 의미 확인 후 매핑",
  "actor_id": "operator_123"
}
```

처리:

- 매핑 확정 후 `source_*_interpreted_staging` 생성 job을 실행한다.
- 매핑되지 않은 컬럼은 버리지 않고 원천 부가 정보 또는 unmapped 목록에 남긴다.
- 가격/크기/작가명처럼 핵심 컬럼이 매핑되지 않으면 snapshot 후보로 보내지 않는다.

## 7. 모델 버전 / 배포 API

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
| `route` | `warm`, `cold`, `unified` 등 모델 경로 |
| `status` | `candidate`, `approved`, `deployed`, `retired`, `rejected` |
| `page` / `page_size` | 페이지 |

응답 항목:

- 모델 버전
- 모델 경로
- 학습 snapshot ID
- feature generation 버전
- 학습 코드 버전
- artifact 경로
- 주요 성능 지표
- parity 검증 상태
- 현재 배포 여부

### 7.2 모델 버전 상세

```text
GET /api/v1/admin/model-versions/{model_version}
```

응답 항목:

- 모델 버전
- 모델 경로
- 학습 snapshot ID
- train/validation/test split ID
- feature generation 버전
- 학습 코드 git SHA
- model artifact URI
- feature store URI
- 성능 지표 JSON
- 검증 리포트 URI
- parity 검증 결과
- 승인자/승인시각/승인 사유

### 7.3 모델 승격/롤백

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
  "reason": "fixed test와 parity 검증 통과",
  "actor_id": "data_admin_123"
}
```

허용 action:

| action | 의미 |
|---|---|
| `promote` | 후보 모델을 운영 모델로 승격 |
| `rollback` | 지정한 이전 모델로 운영 배포 전환 |
| `retire` | 더 이상 운영 후보로 쓰지 않음 |

주의:

- `candidate` 모델은 바로 배포하지 않는다.
- validation/test 성능, parity 검증, API smoke test를 통과한 `approved` 모델만 운영 승격할 수 있다.
- 모델 승격은 수집 snapshot 생성과 별도 단계다. 새 데이터가 수집되어도 자동으로 운영 모델이 바뀌지 않는다.

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

작품 품질 검수(8.2)의 `approve`/`approve_with_patch`/`hold`/`exclude`는 별도 `review_status` enum이 아니라 `normalized_artwork_staging.quality_flags_json`과 snapshot 포함 여부(`artwork_snapshot_item.include_status`)로 표현한다. `exclude`는 `include_status=excluded`(+`exclude_reason`)에 대응한다.

### 8.1 작품 품질 검수 큐 조회

```text
GET /api/v1/admin/review/artworks
```

query:

| 파라미터 | 설명 |
|---|---|
| `source` | 원천 사이트 |
| `price_status` | 가격 있음/없음/문의 |
| `size_status` | 크기 파싱 성공/실패 |
| `medium_status` | 재료 분류 성공/실패 |
| `review_status` | 검수 상태 |
| `page` / `page_size` | 페이지 |

응답 항목:

- 원천 사이트
- 원천 작품 ID
- 원천 URL
- 원천값
- 분해/정리값
- 표준화 후보값
- 품질 플래그
- 처리 상태

참조:

- 읽기: `source_artwork_raw`, `source_artwork_interpreted_staging`, `normalized_artwork_staging`

### 8.2 작품 품질 검수 처리

```text
POST /api/v1/admin/review/artworks/{normalized_artwork_id}/decision
```

request:

```json
{
  "decision": "approve",
  "patch": {
    "width_cm": 60.0,
    "height_cm": 72.7,
    "medium_category_candidate": "painting"
  },
  "reason": "원천 상세 페이지 확인 후 크기 수정",
  "actor_id": "operator_123"
}
```

허용 decision:

| decision | 의미 |
|---|---|
| `approve` | 후보값 승인 |
| `approve_with_patch` | 수정 후 승인 |
| `hold` | 보류 |
| `exclude` | snapshot 제외 |

쓰기:

- `normalized_artwork_staging.quality_flags_json`
- 검수 상태/메모 컬럼 또는 감사 로그

### 8.3 작가명 검수 큐 조회

```text
GET /api/v1/admin/review/artist-names
```

목적:

- 한글명/영문명 표시 후보와 alias 후보를 검수한다.

참조:

- 읽기: `normalized_artist_staging`, `artist_name_alias`

### 8.4 작가명 검수 처리

```text
POST /api/v1/admin/review/artist-names/{alias_id}/decision
```

request:

```json
{
  "decision": "approve",
  "display_name_ko": "홍길동",
  "display_name_en": "Hong Gildong",
  "reason": "작가 공식 표기 확인",
  "actor_id": "operator_123"
}
```

허용 decision:

- `approve`
- `approve_with_edit`
- `reject`
- `hold`

쓰기:

- `artist_name_alias.review_status`
- `artist_name_alias.approved_by`
- `artist_name_alias.approved_at`
- `artist_name_alias.approval_note`
- 필요 시 `normalized_artist_staging.artist_name_*_display`

### 8.5 artist_key 연결 검수 큐 조회

```text
GET /api/v1/admin/review/artist-identities
```

query:

| 파라미터 | 설명 |
|---|---|
| `source` | 원천 사이트 |
| `ambiguity_status` | `unique`, `ambiguous`, `needs_review` |
| `review_status` | `pending`, `needs_review`, `match_rejected` 등 |
| `alias_match_type` | `alias_exact`, `alias_approved`, `alias_fuzzy_only` |

참조:

- 읽기: `artist_identity_candidate`, `artist_identity`, `artist_name_alias`, `normalized_artist_staging`

### 8.6 artist_key 연결 검수 처리

```text
POST /api/v1/admin/review/artist-identities/{candidate_id}/decision
```

request:

```json
{
  "decision": "approve_existing_artist_key",
  "artist_key": "artist_123",
  "reason": "생년과 승인 alias가 일치",
  "actor_id": "data_admin_123"
}
```

허용 decision:

| decision | 의미 |
|---|---|
| `approve_existing_artist_key` | 기존 `artist_key`에 연결 |
| `reject_candidate` | 해당 후보와의 연결 반려 |
| `hold` | 판단 보류 |
| `move_to_new_artist_candidate` | 신규 작가 후보로 전환 |

쓰기:

- `artist_identity_candidate.review_status`
- `artist_identity_candidate.approved_by`
- `artist_identity_candidate.approved_at`
- `artist_identity_candidate.approval_note`
- `artist_identity_candidate.rejected_by`
- `artist_identity_candidate.rejected_at`
- `artist_identity_candidate.reject_reason`
- 승인 시 `artist_identity` 연결 근거 갱신

### 8.7 신규 작가 후보 큐 조회

```text
GET /api/v1/admin/review/new-artists
```

목적:

- 기존 `artist_key` 후보가 없는 신규 작가 후보를 조회한다.
- 이 큐는 최종 `artist_key` 테이블이 아니라 검수 대상 목록이다.

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

- 읽기: `normalized_artist_staging`, `artist_name_alias`
- 기준: MySQL 문서 `5.0.5 신규 작가 후보 큐 기준`

### 8.8 신규 artist_key 생성 승인

```text
POST /api/v1/admin/review/new-artists/{candidate_id}/approve
```

request:

```json
{
  "canonical_name_ko": "홍길동",
  "canonical_name_en": "Hong Gildong",
  "birth_year": 1980,
  "nationality": "Korean",
  "reason": "기존 후보 없음, 작가 페이지와 작품 row 확인",
  "actor_id": "data_admin_123"
}
```

response:

```json
{
  "artist_key": "artist_456",
  "identity_status": "active",
  "created_at": "2026-06-25T02:00:00Z"
}
```

쓰기:

- `artist_identity`
- 필요 시 `artist_name_alias.artist_key`

주의:

- 이 API만 신규 `artist_key`를 생성할 수 있다.
- 일반 사용자 API에서는 호출할 수 없다.

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
- 작가 확정률
- 직전 snapshot 대비 변화량

참조:

- 읽기: `normalized_artwork_staging`, `normalized_artist_staging`, `artist_identity`, `fx_rate_daily`

### 9.2 snapshot 후보 목록

```text
GET /api/v1/admin/snapshots/candidates/items
```

query:

| 파라미터 | 설명 |
|---|---|
| `source` | 원천 사이트 |
| `include_status` | 포함/제외 후보 |
| `exclude_reason` | 제외 사유 |
| `artist_identity_status` | 작가 확정 상태 |
| `page` / `page_size` | 페이지 |

### 9.3 snapshot 생성

```text
POST /api/v1/admin/snapshots
```

request:

```json
{
  "snapshot_name": "train_candidate_2026_06_25",
  "source_cutoff_at": "2026-06-25T00:00:00Z",
  "rules_version": "rules_2026_06_25",
  "reason": "주간 수집 검수 완료",
  "actor_id": "data_admin_123"
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

쓰기:

- `artwork_snapshot`
- `artwork_snapshot_item`

주의:

- `collector_run.status=failed` 또는 `collector_run.quality_status=blocked`인 run은 자동 포함하지 않는다.
- `blocked`는 수집 결과 삭제가 아니라 snapshot 자동 반영 차단 상태다. 운영자 override 사유가 있을 때만 후보에 포함할 수 있다.
- 환율이 없어 `price_krw_normalized`를 만들 수 없는 row는 snapshot 포함 대상에서 제외한다.

## 10. 운영 로그 API

### 10.1 운영 로그 조회

```text
GET /api/v1/admin/audit-logs
```

query:

| 파라미터 | 설명 |
|---|---|
| `entity_type` | `collection_run`, `artwork`, `artist_name`, `artist_identity`, `snapshot` |
| `entity_id` | 대상 ID |
| `actor_id` | 처리자 |
| `from` / `to` | 기간 |

응답 항목:

- 발생 시각
- 대상 유형
- 대상 ID
- 이벤트 유형
- 이전 상태
- 변경 후 상태
- 처리자
- 처리 사유

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
- 수집 DB 장애가 가격 예측 API 장애로 번지지 않게 예측 API는 운영 feature store와 모델 번들을 우선한다.
- snapshot 생성은 `artwork_snapshot`과 `artwork_snapshot_item`에 남기고, 모델 학습은 snapshot export를 기준으로 한다.
- 모델 버전 등록, 승인, 운영 승격, 롤백은 API와 DB에 이력으로 남긴다.
- 예측 응답과 예측 로그에는 `model_version`과 `deployment_id`를 남긴다.

## 12. 다음 확정 필요 항목

API 구현 전에 아래 항목을 정해야 한다.

| 항목 | 결정 필요 내용 |
|---|---|
| 인증 방식 | 세션, JWT, 내부 관리자 계정 중 선택 |
| 신규 작가 후보 저장 방식 | SQL view/export로 시작할지, 별도 물리 큐 테이블을 만들지 |
| 수동 CSV 업로드 저장 방식 | 파일 스토리지 경로와 import run 테이블을 어떻게 둘지 |
| 운영 로그 저장 방식 | 비가역 작가 identity 결정은 `identity_event_log`(MySQL 5.12.1)에 append-only로 남기고, 그 외 엔티티는 각 테이블 승인/반려 컬럼을 사용한다. 전체 필드 변경 audit 테이블 확대는 고도화 |
| 예측 API 연결 방식 | 기존 가격 예측 API에 이 입력/응답 구조를 맞출지, wrapper를 둘지 |
| 1차 시장 가격 카드 데이터 위치 | feature store, snapshot 집계 테이블, 캐시 중 선택 |
