# 작품 가격 데이터 플랫폼 1차 개발 로드맵

작성일: 2026-06-25

## 1. 목적

이 문서는 `projects/art-price-data-platform/docs/` 문서 세트 전체를 **1차 개발 범위**로 보고, 실제 구현 순서와 산출물을 고정하기 위한 로드맵이다.

이 문서는 범위를 줄이는 MVP 문서가 아니다. 기존 설계 문서의 기능 범위를 유지하되, 개발자가 어떤 순서로 구현하고 어떤 산출물이 준비되어야 다음 단계로 넘어갈 수 있는지 명확히 한다.

## 2. 범위 원칙

1차 개발 범위에 포함되는 것은 아래 전체 흐름이다.

```text
원천 등록/수집 설정
  -> 4개 원천 raw 수집 및 payload 보존
  -> 원천별 interpreted staging
  -> 공통 normalized staging
  -> NANT 재료(지지체/매체) 95분류와 mapping row 기준 학습 제외 판단
  -> 작가명/alias/artist_key 표준화
  -> standardization_review_item 공통 검수 큐와 어드민 처리
  -> snapshot 확정요청/생성/서빙승인
  -> 모델 버전/배포 관리
  -> 사용자 가격 예측 화면/API
  -> 1차 시장 가격 카드
  -> 운영 알림/로그/장애 대응
```

제외하지 않는 항목:

- Artsy / Saatchi / Print Bakery / Art1 4개 원천 모두
- 사용자 화면과 어드민 화면
- public API, admin API, internal/job API
- MySQL 스키마, migration, object storage payload store
- 작가 identity 검수, 신규 artist_key 생성 승인, merge/un-merge 이력 기반
- snapshot 3단계 전이: 확정요청 -> 생성승인 -> 서빙승인
- 운영 파라미터, freshness, canary, watchdog, 감사 로그

## 3. 문서별 역할

| 문서 | 개발에서의 역할 |
|---|---|
| `product_requirements_20260625.md` | 제품 목표, 사용자, 1차 성공 기준 |
| `first_development_backlog_20260625.md` | Epic/Task 단위 개발 추적 |
| `first_development_roadmap_20260625.md` | 1차 개발 순서, 단계별 산출물, gate 기준 |
| `periodic_raw_collection_mysql_plan_20260623.md` | DB/스키마/수집 레이어 SoT |
| `weekly_crawler_mysql_operation_plan_20260624.md` | 주기 수집, 실패 처리, 알림, 운영 루틴 |
| `source_site_collected_fields_20260624.md` | 원천별 필드와 표준화 입력 기준 |
| `nant_material_classification_criteria_20260626.md` | 표준화 이후 DB active NANT 지지체/매체 95분류와 CSV `비고2` -> DB `learning_excluded` import 변환 기준 |
| `artist_key_standardization_flow_20260624.md` | 작가명, alias, identity, artist_key 확정 기준 |
| `data_collection_service_scenarios_20260625.md` | 사용자/운영자/job 시나리오 |
| `user_admin_api_plan_20260625.md` | API 기능과 request/response 기준 |
| `user_admin_screen_structure_plan_20260625.md` | 사용자/어드민 화면 구조와 버튼/상태 기준 |
| `user_frontend_screen_spec_20260625.md` | 사용자 가격 예측 화면 상세 입력/결과/상태 기준 |
| `admin_screen_detail_spec_20260625.md` | 어드민 화면별 필드/액션/API 매핑 상세 기준 |
| `frontend_state_error_ux_spec_20260625.md` | loading/empty/error/claim/conflict/freshness 표시 기준 |
| `frontend_component_guidelines_20260625.md` | 프론트 공통 컴포넌트 설계 기준 |
| `frontend_api_mock_fixtures_20260625.md` | API mock/fixture 파일 구조와 예시 응답 기준 |
| `frontend_e2e_test_plan_20260625.md` | 사용자/어드민 E2E 검증 시나리오 |
| `operational_parameters_20260625.md` | 운영 임계치/권한/보존/스케줄 정책 상수 SoT |
| `development_prestart_decisions_20260625.md` | 개발 착수 전 확정할 API/DB/auth/storage/model 연결 기본 조합과 선택지 |

## 4. 1차 개발 기준 결정

아래 항목은 구현 착수 전에 선택지로 남기지 않고 1차 기준으로 고정한다. 이 절은 **확정된 설계 결정(원칙)**이고, Phase 0(§6)은 그 결정을 개발 가능한 산출물(OpenAPI/DDL/seed)로 내리는 작업이다. PRD §12는 이 결정 위에 얹는 개발 전 확정 기본값과 정책 선택 항목을 다룬다.

| 항목 | 1차 개발 기준 |
|---|---|
| interpreted/normalized 분리 | 물리 테이블 2단계로 구현한다. 분해 실패와 표준화 실패를 운영상 분리 추적해야 하므로 단일 staging 흡수안은 채택하지 않는다. |
| raw payload 저장 | 1차부터 object storage에 저장하고 MySQL에는 `payload_path`/`payload_hash`/`payload_size`만 저장한다. |
| NANT 재료 분류 | `normalized_artwork_staging` 다음 단계에서 DB active NANT mapping version으로 지지체/매체 95분류를 수행한다. 학습 제외는 mapping row의 `learning_excluded=true` 기준이며, 기존 재료/지지체 하드코딩 학습 필터는 쓰지 않는다. |
| 수집 DB와 예측 API 연결 | 예측 API는 수집 DB를 실시간 조회하지 않는다. 승인 snapshot과 운영 feature store/model bundle만 본다. |
| snapshot 상태 | 사용자 기준은 `artwork_snapshot.status=approved`만 사용한다. `generated`는 비서빙 상태다. |
| 어드민 actor | `actor_id`는 body로 받지 않고 인증 컨텍스트에서 주입한다. |
| 사용자 API 인증 | `public` prefix는 인증 없음이 아니다. 사용자 세션/익명 사용/rate limit 정책은 Phase 0에서 구현 기준으로 확정한다. |
| 개인정보/삭제 요청 | 1차부터 suppression/do-not-show/do-not-train 상태를 지원한다. 정식 정책 전이라도 서비스 노출과 학습 반영 차단은 구현한다. |
| 1차 시장 가격 카드 | 원천 URL/사이트명/작품 ID는 사용자에게 노출하지 않고, 집계 기준/최소 표본/이상치 처리 규칙을 별도 구현 기준으로 고정한다. |

## 5. 개발 단계 개요

```text
Phase 0. API/DB/운영 기준 확정
Phase 1. DB/migration/object storage 기반
Phase 2. collector 공통 인터페이스와 raw 적재
Phase 3. 4개 원천별 interpreted/normalized 파이프라인
Phase 3.5. NANT 재료(지지체/매체) 분류와 학습 제외 기준 적용
Phase 4. 작가명/artist_key 표준화와 검수 큐
Phase 5. snapshot/export/model training/registry/deployment
Phase 6. API 구현
Phase 7. 사용자/어드민 화면 구현
Phase 8. 운영 자동화와 runbook
Phase 9. 통합 검증과 운영 전환
```

## 5.5 마일스톤: 수직 슬라이스 우선 (M1 → M2)

Phase는 "레이어 완성" 순서지만, 모든 레이어를 4원천·전체 UI·전체 운영까지 폭으로 채운 뒤에야 첫 동작을 확인하면 통합 리스크가 끝에 몰린다(§11 범위 과대). 이를 막기 위해 Phase 1~7 구현은 **먼저 1원천을 끝까지 관통하는 얇은 수직 슬라이스(M1)** 를 완성한 뒤 **폭으로 확장(M2)** 한다.

구현 적용은 M1을 한 번에 만들지 않고 아래 컷으로 나눈다.

| 컷 | 범위 | 완료 의미 |
|---|---|---|
| D1 | Art1 raw 수집 -> interpreted -> standardization_review_item 보류/승인 -> normalized -> NANT/FX/artist_key resolve -> snapshot 후보/생성/승인 -> parquet export/manifest | 학습 전 데이터 플랫폼 완성. 모델 학습/배포는 아직 하지 않음 |
| D2 | approved snapshot export -> Warm/Cold feature generation spec/dataset build | feature column, target, split, 결측/encoding, schema hash가 닫힘 |
| D3 | model training/import job + 평가/parity | 모델 artifact 또는 imported joblib 후보 생성 |
| D4 | registry candidate 승인/반려 + deployment promote/rollback/retire + prediction log | 모델 version 적용과 운영 route 반영 |

D1이 첫 개발 목표다. 기존 M1 완료 기준("사용자가 예측을 본다")은 D1~D4가 모두 통과된 뒤에 충족된다.

### M1. 수직 슬라이스 (1원천 end-to-end)

대상 원천은 `Art1`(§17 최우선 착수의 첫 원천). 아래를 **하나의 흐름으로 관통**해 "사용자가 예측을 본다"를 조기 검증한다.

```text
D1: Art1 raw 적재
  -> interpreted/normalized (Art1만)
  -> NANT 지지체/매체 분류 + mapping row 기준 학습 제외 판단 (Art1만)
  -> standardization_review_item 공통 큐 최소 타입 3개(artist_name_ko 1건 + artist_key/new_artist 1건 + nant_mapping 또는 fx_rate 1건)
  -> 작가명 alias + 사용자 신규 작가 후보 제출 + 최소 identity 후보
  -> snapshot 확정요청 -> 생성승인 -> 서빙승인
D2: feature generation spec/dataset build
D3: joblib 모델 번들 import 또는 모델 학습 job
D4: registry/deployment active
  -> 사용자 예측 API + 예측 결과 화면
  -> 어드민 수집 대시보드 + 작가명 검수 큐 + 신규 작가 후보 최소 큐 화면
```

M1 완료 기준:

- Art1 1원천 데이터로 사용자 예측 API가 active deployment 기준 응답을 반환한다.
- 예측 결과 화면에 가격/신뢰도/as_of/1차 시장 카드가 표시된다(freshness 경고/카드 숨김은 M2).
- 어드민이 화면에서 Art1 run 상태를 보고 작가명 검수 1건을 처리할 수 있다.
- 사용자가 신규 작가 후보를 제출할 수 있고, 어드민이 신규 후보 최소 큐 1건을 처리할 수 있다. `approve`로 최종 artist_key를 생성하는 경로는 데이터 관리자 권한으로만 통과한다.
- D3/D4 모델 경로는 기존 예측 API 호출이 아니라 joblib 모델 번들을 training/import 이력과 registry/deployment에 등록해 active deployment로 둔다. Warm 기본 후보는 `projects/art-price-data-platform/models/warm_lite_unified_current_joblib_v0.1_candidate`이고, Cold 기본 후보는 `k80 보수적 운영` 후보(`resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05`)를 `projects/art-price-data-platform/models/cold_k80_conservative_official_v0.1_candidate/` joblib runtime bundle로 freeze한 산출물이다. Cold k80은 fixed test parity/joblib smoke 통과 후 active deployment에 등록한다. `projects/art-price-data-platform/models/cold_prediction_v0.5_operational`은 적용 fallback이 아니라 과거 raw-input p95 방어 참고 산출물이다. 어떤 방식을 쓰든 prediction log가 `model_version`/`deployment_id`/`route`를 남겨야 한다.
- 스키마/상태값/합성키 정합성이 실데이터로 한 번 깨져보고 고정된다.
- M1 범위는 **원천 1개·사용자 예측 최소 경로·공통 표준화 검수 큐 최소 타입 3개(`artist_name_ko`, `artist_key`/`new_artist`, `nant_mapping` 또는 `fx_rate`)**로 한정한다. 작품 품질/freshness/나머지 원천/전체 검수 큐는 M2에서 확장한다.

### M2. 폭 확장 (운영 가능한 1차 완성)

M1 흐름이 고정되면 폭을 채운다.

- 나머지 3원천(Saatchi/Print Bakery/Artsy) interpreted/normalized/identity 연결
- 작품 품질·artist_key 연결·신규 작가 검수 큐 전체(`standardization_review_item` 타입 확장)
- freshness 경고/카드 숨김(1차 시장 카드 자체는 M1)
- 운영 자동화 전체(cron/watchdog/canary/알림)와 runbook 4종
- Phase 9 통합 검증과 운영 전환

M2 완료 기준은 §18 완료 정의 및 PRD §10 성공 기준과 동일하다. M1은 그 부분집합을 조기 검증하는 단계이지 별도 완화 기준이 아니다.

## 6. Phase 0. API/DB/운영 기준 확정

목표:

- 문서 설계를 개발자가 바로 구현할 수 있는 확정 기준 산출물로 내린다.

산출물:

- `projects/art-price-data-platform/docs/mysql/` migration 초안
- `projects/art-price-data-platform/docs/openapi/art_price_data_platform_v1.yaml`
- API enum/status/error/idempotency 규칙 표
- 사용자 API 인증/rate limit/abuse 방지 정책
- 개인정보 suppression/do-not-train/do-not-show 처리 기준
- 1차 시장 가격 카드 계산 기준
- 운영 파라미터 seed 데이터
- 어드민 계정 부트스트랩 기준 (초기 슈퍼유저, 역할 위계, audit actor 주체)

완료 기준:

- API request/response의 nullable, enum, pagination, HTTP status가 OpenAPI에 반영되어 있다.
- MySQL DDL이 문서의 SoT 테이블을 migration으로 표현한다.
- `source`, `artist_source_id`, `source_artwork_id` 합성키 규칙이 코드/DB/API에서 같은 형태로 쓰인다.
- 사용자 API가 노출하지 말아야 할 원천 추적 필드 목록이 schema test로 고정된다.
- 초기 슈퍼유저로 어드민 인증/검수 화면 검증이 가능하다(Phase 7 검수 화면의 선행 조건).

## 7. Phase 1. DB/migration/object storage 기반

목표:

- 수집/표준화/검수/snapshot/model 운영의 영속 기반을 만든다.

구현 순서:

1. `source_registry`, `collector_run`, `raw_fetch`, `manual_import_file`
2. `source_artwork_raw`, `source_artist_raw`
3. `source_artwork_interpreted_staging`, `source_artist_interpreted_staging`
4. `fx_rate_daily`, `nant_mapping_version`, `nant_allowed_category`, `nant_material_mapping`
5. `standardization_review_item`
6. `normalized_artwork_staging`(확정 `artist_key`/NANT resolve 컬럼 포함), `normalized_artist_staging`
7. `artist_name_alias`, `artist_identity_candidate`, `artist_identity`, `artist_profile_meta`
8. `identity_event_log`, `artist_identity_version`, `artist_key_membership_history`
9. `artwork_snapshot`, `artwork_snapshot_item`, `snapshot_request`
10. `price_model_registry`, `price_model_deployment`, `price_prediction_log`
11. suppression/do-not-train/do-not-show 상태 또는 동등한 정책 컬럼

완료 기준:

- migration 재실행/rollback 전략이 있다.
- `collector_run` source별 single-flight 제약이 동작한다.
- `snapshot_request` cutoff/rules별 진행 중 요청 1개 제약이 동작한다.
- raw payload 원문은 DB에 저장되지 않고 object storage 경로와 hash만 저장된다.

## 8. Phase 2. collector 공통 인터페이스와 raw 적재

목표:

- 4개 원천 collector가 같은 run/raw 처리 기준으로 동작하게 한다.

구현 순서:

1. 공통 collector result schema 정의
2. DB writer 구현
3. payload store 구현
4. HTTP client/backoff/robots/user-agent 정책 적용
5. Art1 collector 연결
6. Print Bakery collector 연결
7. Artsy 기존 수집 결과 DB writer/backfill 연결
8. Saatchi 기존 수집 결과 DB writer/backfill 연결
9. manual CSV upload run 생성 경로 연결

완료 기준:

- 각 source에서 `collector_run`과 `raw_fetch`가 생성된다.
- run 중복 실행이 차단된다.
- 실패 URL/error/payload hash가 추적된다.
- API key/token 등 비밀 파라미터가 DB에 저장되지 않는다.

## 9. Phase 3. interpreted/normalized 파이프라인

목표:

- 원천별 문자열과 구조 차이를 공통 표준화 후보로 변환한다.

구현 순서:

1. 작품 interpreted job: 가격/크기/재료/판매상태/title/year 후보 추출
2. 작가 interpreted job: 원천명, 한글/영문 후보, 생년/국적/활동지 후보 추출
3. 작가 normalized job: 표시명 후보, source artist key, 후보 상태 생성
4. 자동 표준화 gate: 작가명 한글화 위험, artist_key 미확정, NANT 미매핑, FX 누락/이상치를 `standardization_review_item`에 등록
5. artist_key resolve: 기존 확정 키 자동 연결, 후보 생성, 승인된 키만 작품 row에 사용
6. 작품 normalized job: 확정된 active `artist_key`, 적용 가능한 `fx_rate_daily`, 매핑된 DB active NANT 95분류가 모두 있는 작품만 공통 컬럼과 quality flag를 함께 생성
7. NANT mapping row 기준 `learning_excluded` 판단은 작품 row에 복사하지 않고 snapshot 후보 query에서 조인
8. 미매핑 medium/support/material 리포트는 `standardization_review_item(review_type=nant_mapping)`에서 조회
9. parser/normalizer/NANT/review queue fixture integration test 추가

완료 기준:

- 4개 source 모두 raw -> interpreted -> normalized row 수 추적이 가능하다.
- 가격/크기/작가명 보유율이 source별로 집계되고, `QUAL-PRICE-MIN`/`QUAL-SIZE-MIN`/`QUAL-ARTIST-MIN` 임계 미달 시 parser 점검/snapshot 보류 신호가 산출된다.
- 분해 실패와 표준화 실패가 별도 flag로 남는다.
- `artist_key` 미확정 작품은 `normalized_artwork_staging`에 올리지 않고 `standardization_review_item(review_type=artist_key)`에 보류된다.
- 작가명 한글화 검수는 `standardization_review_item.review_type=artist_name_ko`로 등록된다.
- NANT 미매핑과 환율 누락/이상치는 `standardization_review_item`에 보류되고, 승인/apply 후 영향 row만 normalizer 재실행 대상이 된다.
- NANT 기준 조합 95개와 CSV import -> DB `learning_excluded` 변환이 fixture로 검증된다.
- snapshot 후보에서 제외해야 할 row의 사유가 NANT 제외 사유를 포함해 계산된다.

## 9.5 Phase 3.5. NANT 재료(지지체/매체) 분류

목표:

- 공통 표준화가 끝난 작품 row를 NANT 지지체/매체 95분류로 고정한다.
- 학습 snapshot의 재료/지지체 제외 기준을 DB mapping row의 `learning_excluded=true`로 단일화한다.

구현 기준:

- 기준 파일은 [NANT 재료(지지체/매체) 분류 기준](nant_material_classification_criteria_20260626.md)을 따른다.
- 결과는 `nant_support`, `nant_medium`, `nant_category_key`, `mapping_version_id`, `material_mapping_id`를 포함해야 한다. `learning_excluded`는 classification row에 중복 저장하지 않고 mapping row 조인으로 판단한다.
- NANT mapping은 DB에서 `draft`를 편집하고 데이터 관리자가 `active`로 전환한다. active version은 직접 수정하지 않는다.
- 기존 코드에 있던 재료/지지체/작품 유형 하드코딩 학습 필터는 새 snapshot 후보 query에서 사용하지 않는다.
- 매핑 실패 row는 임의 분류하지 않고 `standardization_review_item(review_type=nant_mapping)`에 보류한다.

완료 기준:

- Art1 M1 데이터에서 표준화 다음 NANT 분류가 실행된다.
- 기준 조합 95개와 초기 CSV import SHA-256이 fixture로 검증된다.
- DB mapping row의 `learning_excluded=true`가 학습 snapshot/export에서 제외된다.
- raw/interpreted/normalized row는 삭제되지 않고 제외 사유만 snapshot과 분류 결과에 남는다.

## 10. Phase 4. 작가명/artist_key 표준화와 검수 큐

목표:

- 서비스와 모델이 사용할 최종 작가 identity를 안전하게 확정한다.

구현 순서:

1. `artist_name_alias` 후보 생성
2. 한글명/영문명 reason code, risk score, override 상태 계산
3. 같은 `source + artist_source_id` 기존 연결 자동 확인
4. alias 기반 `artist_identity_candidate` 생성
5. 자동 확정 조건 적용: 승인 alias + 고신뢰 생년 일치 + 충돌 없음
6. 동명이인/충돌/메타 부족 후보를 검수 큐로 적재
7. 신규 artist_key 후보 큐 생성
8. identity 결정 append-only event 기록
9. merge/un-merge 영향 범위 조회 기반 구현

완료 기준:

- 이름만으로 자동 artist_key를 생성하지 않는다.
- 신규 작가 후보는 승인 전 `artist_identity`에 들어가지 않는다.
- 자동 확정 샘플 검수 리포트가 생성된다.
- 비가역 identity 결정은 `identity_event_log`에 남는다.

## 11. Phase 5. snapshot/export/model training/registry/deployment

목표:

- 학습 전 고정 데이터(snapshot/export)를 먼저 만들고, feature generation, 모델 학습/import, 모델 배포 이력을 별도 컷으로 연결한다.

구현 순서:

1. snapshot 후보 summary/items query
2. snapshot 확정요청 API/job
3. snapshot 생성승인 job
4. `artwork_snapshot_item` 포함/제외 고정(`nant_learning_excluded` 포함)
5. parquet export와 manifest 생성
6. 검수/공유/호환용 CSV export 생성
7. Warm/Cold feature generation spec 작성
8. feature dataset build + feature manifest/schema hash 생성
9. `model_training_job` 생성 또는 기존 joblib import 이력 생성
10. model registry에 `candidate` 등록
11. validation/test, fixed-test parity, API smoke gate 확인
12. candidate 승인/반려(`approved`/`rejected`)
13. model deployment active/rollback/retire 전이
14. prediction log 적재

D1 적용:

- 첫 구현 컷은 1~6까지만 닫는다. 즉 모델 학습/import, registry/deployment, prediction log는 D1 범위가 아니다.
- D1 완료 후 D2에서 feature generation spec/dataset build를 별도로 닫는다.
- 기존 Warm joblib와 Cold k80 joblib bundle 적용은 D3(import/parity)와 D4(registry/deployment)에서 처리한다.

완료 기준:

- 같은 입력과 같은 `rules_version`이면 같은 snapshot export가 생성된다.
- `generated` snapshot은 사용자 기준 데이터가 되지 않는다.
- `approved` snapshot만 서빙·freshness 비교 기준이 되고, 사용자 `as_of`는 active deployment가 학습/import에 쓴 cutoff로 산정한다.
- feature generation은 column/target/split/schema hash가 정해진 뒤에만 학습으로 넘어간다.
- 모델 학습/import job에서 registry candidate까지 추적할 수 있다.
- `candidate` 모델은 운영 승격되지 않는다.
- active deployment가 사용한 학습 snapshot 또는 legacy import manifest를 역추적할 수 있다.

## 12. Phase 6. API 구현

목표:

- 사용자 화면, 어드민 화면, job 실행이 사용할 API를 구현한다.

구현 순서:

1. 공통 인증/권한/actor 주입
2. 공통 error envelope와 request id
3. idempotency key 저장/replay
4. review claim/lock
5. public artist search / artist candidate / price prediction / primary-market-summary
6. admin collection run dashboard/list/detail/action
7. source registry/manual import API
8. model operation API(training/import, registry, deployment)
9. review queues and decisions
10. snapshot APIs
11. audit log and impact lookup

완료 기준:

- OpenAPI 예시와 실제 response가 입출력 검증 테스트로 일치한다.
- 어드민 쓰기 API는 body의 `actor_id`를 받지 않는다.
- 동일 idempotency key 재호출이 중복 생성 없이 같은 결과를 반환한다.
- `expected_review_status` 불일치 시 `CONFLICT`가 난다.

## 13. Phase 7. 사용자/어드민 화면 구현

목표:

- 서비스 페이지와 운영자가 실제로 사용할 어드민 화면을 구현한다.

사용자 화면 구현 순서:

1. 가격 예측 입력
2. 작가 검색/선택
3. 신규 작가 후보 제출
4. 예측 결과
5. 입력값 보완 안내
6. 1차 시장 가격 카드
7. freshness 경고/카드 숨김 처리

상세 기준:

- 사용자 화면은 `service-web` Next.js 앱으로 구현하고, 어드민 화면은 별도 `admin-web` React SPA로 구현한다.
- 화면별 필드/검증/결과 표시는 `user_frontend_screen_spec_20260625.md`를 따른다.
- loading/empty/error/freshness 상태 표시는 `frontend_state_error_ux_spec_20260625.md`를 따른다.
- API mock과 화면 fixture는 `frontend_api_mock_fixtures_20260625.md`를 따른다.

어드민 화면 구현 순서:

1. 수집 대시보드
2. 수집 run 상세
3. 작품 품질 검수 큐
4. 작가명 검수 큐
5. artist_key 연결 검수 큐
6. 신규 작가 후보 큐
7. snapshot 후보 확인과 승인
8. 모델 버전/배포 관리
9. 운영 로그/알림

상세 기준:

- 어드민은 별도 `admin-web` React SPA의 `/admin/art-price-data/**` route로 구현한다. 비즈니스 쓰기 로직은 프론트 dev proxy나 별도 프론트 서버가 아니라 FastAPI/OpenAPI 기준 API를 호출한다.
- 화면별 필드/액션/API 매핑은 `admin_screen_detail_spec_20260625.md`를 따른다.
- 공통 badge/table/filter/dialog/decision 컴포넌트는 `frontend_component_guidelines_20260625.md`를 따른다.
- Phase 7 완료 검증은 `frontend_e2e_test_plan_20260625.md`의 M1/M2 시나리오를 따른다.

완료 기준:

- 큐 item ID가 decision API path parameter로 그대로 쓰인다.
- claim된 항목은 화면에서 담당자와 만료 상태가 보인다.
- 사용자 화면은 원천 사이트명/URL/원천 ID를 노출하지 않는다.
- 어드민 화면은 원천 추적 정보와 처리 사유 입력을 제공한다.

## 14. Phase 8. 운영 자동화와 runbook

목표:

- 수집과 검수가 사람이 기억하는 절차가 아니라 반복 가능한 운영 루틴으로 동작하게 한다.

구현 순서:

1. 주간 cron
2. collector watchdog
3. snapshot watchdog
4. canary 품질 감사
5. run summary report
6. 알림 발송
7. 일일 운영 runbook
8. 주간 snapshot 승인 runbook
9. 장애 대응 runbook
10. 개인정보/삭제 요청 runbook

완료 기준:

- run 미생성, stuck run, blocked source, 품질 하락이 알림으로 올라온다.
- 운영자가 SQL/CSV를 직접 열지 않고 대시보드에서 상태를 확인할 수 있다.
- suppression/do-not-train 요청이 서비스 노출과 snapshot 후보에 반영된다.

## 15. Phase 9. 통합 검증과 운영 전환

목표:

- 4개 원천에서 수집한 데이터가 사용자 예측/어드민 운영/snapshot/model deployment까지 끊기지 않는지 검증한다.

필수 검증:

- source별 parser fixture test
- raw -> interpreted -> normalized integration test
- artist identity 자동 확정 샘플 검수
- 검수 decision concurrency/idempotency test
- snapshot 생성/서빙승인 전이 test
- public API 원천 정보 비노출 test
- active deployment 기준 `as_of` 산정 test
- primary market card 계산 test
- suppression/do-not-train 반영 test
- 장애 격리 test: 수집 DB 비가용 상황에서도 예측 API가 승인 snapshot/feature store/model bundle로 정상 응답(NFR-02)
- 운영 알림/watchdog test

운영 전환 기준:

- 4개 source의 첫 full run이 완료된다.
- 어드민 큐에서 초기 백로그 처리 루틴이 검증된다.
- 승인 snapshot으로 export가 생성된다.
- 모델 registry/deployment에 active deployment가 기록된다.
- 사용자 예측 API와 화면이 active deployment 기준으로 응답한다.
- 장애 시 마지막 정상 snapshot/model이 유지된다.

## 16. 병렬 작업 트랙

아래 트랙은 순차가 아니라 병렬로 진행하되, gate는 Phase 순서를 따른다.

| 트랙 | 담당 범위 | 먼저 필요한 것 |
|---|---|---|
| Data/DB | migration, DB writer, snapshot/export | Phase 0 기준 |
| Collector | 4개 원천 수집, payload store, retry/backoff | Phase 1 기본 테이블 |
| Standardization | parser/normalizer, artist identity, quality flags | Phase 2 raw 적재 |
| Backend API | public/admin/internal API | Phase 0 OpenAPI, Phase 1 schema |
| Frontend | service-web Next.js, admin-web React SPA | Phase 6 API mock/입출력 기준 |
| ML/Serving | feature store, model training/import, registry/deployment, prediction log | Phase 5 snapshot/export |
| Ops | cron, watchdog, alert, runbook | Phase 1 run tables, Phase 8 jobs |

## 17. 최우선 착수 순서

첫 개발 스프린트는 아래 순서로 시작한다.

1. OpenAPI 초안과 MySQL DDL 초안 작성
2. object storage payload store와 DB writer 구현
3. `source_registry` seed와 운영 파라미터 seed 작성
4. Art1 -> Print Bakery -> Artsy -> Saatchi 순으로 raw 적재 연결
5. interpreted/normalized physical table 기준으로 parser/normalizer job 작성
6. Art1 기준 NANT 분류와 snapshot/export까지 local dev에서 D1 E2E 검증

개발 적용은 local-first다. D1은 `docker-compose`의 MySQL+MinIO+API에서 fixture와 소량 실데이터로 검증한 뒤 staging/preview에 올리고, production은 migration/seed/export 재현성과 rollback이 확인된 뒤 반영한다.
7. artist_name_alias와 identity candidate 생성
8. admin collection dashboard와 review queue API mock 구현
9. snapshot request/create/approve skeleton 구현

이 순서의 이유:

- DB 기준이 먼저 없으면 collector/API/UI가 서로 다른 상태값과 키를 만들 가능성이 크다.
- raw 적재가 먼저 되어야 parser/normalizer와 검수 큐를 실제 데이터로 검증할 수 있다.
- snapshot/export 기준이 잡혀야 이후 feature generation, 모델 version 적용, 사용자 화면의 `as_of`, freshness, 가격 카드가 흔들리지 않는다.

## 18. 완료 정의

1차 개발 완료는 "수집 스크립트가 돈다"가 아니라 아래 조건을 모두 만족하는 상태다.

- 4개 원천 수집 결과가 raw/interpreted/normalized/identity/snapshot/model deployment까지 연결된다.
- 사용자 가격 예측 화면은 active deployment 기준으로 가격, 신뢰도, 기준일, 1차 시장 가격 카드를 표시한다.
- 어드민은 수집 상태, 검수 큐, snapshot 후보, 모델 운영 상태를 화면에서 처리할 수 있다.
- 운영 알림과 watchdog가 수집 실패, 품질 하락, stuck job을 잡는다.
- 개인정보/삭제 요청에 대해 서비스 노출과 학습 반영 차단이 가능하다.
- 모든 주요 쓰기 액션은 actor, 시각, 사유, idempotency 또는 expected status 기준으로 감사 가능하다.
