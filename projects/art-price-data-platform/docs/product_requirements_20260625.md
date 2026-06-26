# 작품 가격 데이터 플랫폼 PRD

작성일: 2026-06-25

## 1. 문서 목적

이 PRD는 작품 가격 예측 서비스의 데이터 수집/표준화/운영 기능을 왜 만들고, 1차 개발에서 어떤 사용자 가치와 운영 기준을 만족해야 하는지 정의한다.

상세 DB/API/화면/운영 설계는 관련 문서를 따른다. 이 문서는 제품 목표, 사용자, 기능 요구사항, 성공 기준을 한 곳에서 정리한다.

관련 문서:

- [1차 개발 로드맵](first_development_roadmap_20260625.md)
- [1차 개발 백로그](first_development_backlog_20260625.md)
- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 화면 구조 및 기능 기획](user_admin_screen_structure_plan_20260625.md)
- [사용자 화면 상세 명세](user_frontend_screen_spec_20260625.md)
- [어드민 화면 상세 명세](admin_screen_detail_spec_20260625.md)
- [프론트 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [MySQL 적재 기획](periodic_raw_collection_mysql_plan_20260623.md)
- [주기 수집 운영 문서](weekly_crawler_mysql_operation_plan_20260624.md)
- [artist_key 및 작가명 표준화 흐름](artist_key_standardization_flow_20260624.md)
- [NANT 재료(지지체/매체) 분류 기준](nant_material_classification_criteria_20260626.md)
- [운영 파라미터](operational_parameters_20260625.md)

## 2. 문제 정의

작품 가격 예측은 작품/작가/시장 데이터를 기준으로 동작하지만, 현재 데이터 수집과 표준화가 운영 서비스 기준으로 충분히 고정되어 있지 않다.

해결해야 할 문제:

- 원천별 수집 방식과 필드가 달라 공통 데이터로 안정적으로 쓰기 어렵다.
- raw 데이터, 표준화 데이터, 학습 snapshot 사이의 재현 경로가 명확해야 한다.
- 작가명/alias/동명이인/신규 작가를 잘못 연결하면 Warm feature와 가격 이력이 오염된다.
- 사용자는 가격 예측과 1차 시장 참고 정보를 보되, 원천 추적용 내부 정보는 보지 않아야 한다.
- 운영자는 수집 실패, 품질 저하, 검수 대기, snapshot 반영 여부를 화면에서 처리할 수 있어야 한다.
- 모델과 데이터 snapshot이 언제 기준인지 사용자와 운영자가 추적할 수 있어야 한다.

## 3. 제품 목표

1차 개발 목표:

- 4개 원천(Artsy, Saatchi, Print Bakery, Art1)의 데이터를 주기적으로 수집한다.
- raw, interpreted, normalized, artist identity, snapshot, model deployment가 끊기지 않게 연결된다.
- 사용자 가격 예측 화면에서 예측 가격, 신뢰도, 데이터 기준일, 1차 시장 가격 카드를 제공한다.
- 어드민 화면에서 수집 상태, 검수 큐, snapshot, 모델 운영 상태를 운영할 수 있다.
- 수집 장애가 사용자 예측 API 장애로 번지지 않게 한다.
- 모든 주요 운영 결정은 actor, 시각, 사유, 변경 전/후 상태를 추적할 수 있게 한다.

## 4. 대상 사용자

| 사용자 | 목적 | 주요 기능 |
|---|---|---|
| 일반 사용자 | 작품 가격 예측과 참고 시장 정보를 확인 | 작가 검색, 작품 입력, 예측 요청, 1차 시장 가격 카드 확인 |
| 운영 담당자 | 수집 결과와 검수 큐를 처리 | 수집 대시보드, run 상세, 작품/작가명 검수, 보류/제외 |
| 데이터 관리자 | 비가역 데이터 결정을 승인 | artist_key 생성/연결 확정, snapshot 생성/서빙 승인, 모델 승격/롤백 |
| 개발자 | 수집/파서/API 장애를 진단 | run 로그, raw_fetch, parser error, watchdog/알림 확인 |
| 데이터 분석가 | 학습 snapshot과 품질을 검토 | snapshot 후보, export, 품질 지표, 모델 학습 데이터 추적 |

역할 위계는 개발자 < 운영 담당자 < 데이터 분석가 < 데이터 관리자이며, 엔드포인트별 최소 권한 매핑은 [운영 파라미터](operational_parameters_20260625.md) §A-1을 SoT로 따른다. 1차 RBAC는 상위 역할이 하위 역할의 권한을 포함하는 단순 모델이다. 장기적으로 직무별 capability 분리는 후속 고도화로 둔다.

## 5. 1차 개발 범위

1차 개발 범위는 MVP가 아니라 운영 가능한 첫 버전이다. 아래 항목을 모두 포함한다.

### 5.1 데이터 수집

- 4개 원천 수집: Artsy, Saatchi, Print Bakery, Art1
- `source_registry` 기반 원천 설정
- `collector_run`, `raw_fetch` 기반 run 추적
- raw payload object storage 저장
- 요청 backoff, user-agent, robots/ToS 정책 기록
- source별 single-flight, heartbeat, watchdog
- 수동 CSV 업로드 경로

### 5.2 데이터 표준화

- `source_*_raw` 저장
- `source_*_interpreted_staging` 생성
- `normalized_*_staging` 생성
- 가격/통화/환율/크기/재료/판매상태 표준화
- 표준화 이후 DB active NANT 재료(지지체/매체) 95분류와 `learning_excluded` 학습 제외 플래그 생성
- unmapped/quality flag 생성
- source별 품질 지표 산출

### 5.3 작가명과 artist_key

- 작가명 한글화/영문화 후보 생성
- alias 후보와 검수 상태 관리
- `source + artist_source_id` 기존 연결 확인
- alias + 고신뢰 생년 기반 자동 확정
- 동명이인/충돌/메타 부족 후보 검수 큐
- 신규 artist_key 후보 큐
- 확정 artist_key의 작가 프로필/메타는 `artist_profile_item`으로 항목 단위 관리하고, `artist_profile_current`는 현재 표시/검색/feature 후보용 요약으로 identity와 분리
- identity 결정 append-only 이력
- merge/un-merge 영향 추적

### 5.4 Snapshot과 모델 운영

- snapshot 후보 summary/items
- snapshot 확정요청, 생성승인, 서빙승인 3단계
- `generated`와 `approved` 상태 분리
- parquet export와 manifest
- 모델 학습/import job 추적
- 모델 registry, candidate 승인, deployment 관리
- prediction log 적재
- active deployment 기준 `as_of` 산정

### 5.5 사용자 기능

- 작가 검색/선택
- 신규 작가 후보 제출
- 작품 입력과 필수값 검증
- 가격 예측 요청
- 예측 가격, 신뢰도, 검수 필요 사유 표시
- 데이터 기준일/freshness 표시
- 1차 시장 가격 카드 표시
- 최신성 임계 초과 시 경고/숨김 처리

### 5.6 어드민 기능

- 수집 대시보드
- 수집 run 상세
- 작품 품질 검수 큐
- 작가명 검수 큐
- artist_key 연결 검수 큐
- 신규 작가 후보 큐
- snapshot 후보 확인과 승인
- NANT mapping version/import/draft/activate 관리
- 모델 버전/배포 관리
- 운영 로그/알림

### 5.7 운영 기능

- 주간 cron
- collector watchdog
- snapshot watchdog
- canary 품질 감사
- 운영 알림
- 일일 운영 runbook
- 주간 snapshot 승인 runbook
- 장애 대응 runbook
- 개인정보/삭제 요청 runbook

### 5.8 1차 비범위 (Non-goals)

범위 과대(§11)를 통제하기 위해 아래 항목은 1차에서 **명시적으로 하지 않는다.** 1차 완료 기준 판정에서 제외한다.

- 4개 외 원천 추가 및 자동 온보딩 UI
- 모델 자동 재학습/스케줄 재배포 (1차는 수동 승격/롤백만)
- canonical artwork 단위 merge (1차는 작가 identity 단위까지만)
- 조직 SSO 연동과 세분화된 capability RBAC (1차는 §4 상속형 역할 위계만)
- 고급 대시보드 시각화/BI (1차는 운영 처리에 필요한 표/상태 표시까지만)
- raw 물리 삭제 job 자동화 (1차는 `RAW-RETENTION` 보존기간 정책값과 수동/운영 절차, suppression 차단까지 구현한다. 만료분 일괄 purge 자동 job은 후속)

## 6. 후속 고도화

아래 항목은 1차 범위를 약화하지 않지만, 1차 완료 뒤 정교화할 수 있다.

- 고급 대시보드 시각화
- 자동 모델 재학습 완전 자동화
- 복잡한 canonical artwork merge
- 원천 추가 자동 온보딩 UI
- 더 정교한 권한 분리와 조직 SSO 연동
- 검수 생산성 분석과 자동 확정 기준 튜닝

## 7. 핵심 사용자 시나리오

### 7.1 일반 사용자: 확정 작가 예측

1. 사용자가 작가명을 검색한다.
2. 확정 artist_key가 있는 후보를 선택한다.
3. 작품 크기, 제작연도, 재료/지지체를 입력한다.
4. 예측을 요청한다.
5. 예측 가격, 신뢰도, 데이터 기준일, 1차 시장 가격 카드를 확인한다.

성공 기준:

- 사용자는 같은 이름의 작가를 구분할 수 있다.
- 예측 결과가 어떤 데이터 기준일을 사용하는지 볼 수 있다.
- 호당가는 계산 기준이 아니라 표시용 참고값으로 표시된다.

### 7.2 일반 사용자: 신규 작가 후보

1. 작가 검색 결과가 없다.
2. 사용자가 신규 작가 후보 정보를 입력한다.
3. 시스템은 즉시 artist_key를 만들지 않고 검수 큐로 보낸다.
4. 예측은 미확정 작가 상태와 검수 필요 사유를 표시한다.

성공 기준:

- 사용자 입력만으로 최종 artist_key가 생성되지 않는다.
- 운영자가 신규 작가 후보를 검수할 수 있다.

### 7.3 운영 담당자: 수집 run 확인

1. 운영자가 수집 대시보드를 확인한다.
2. source별 run 상태, row 수, 실패율, 품질 지표를 본다.
3. 실패/경고 run을 상세 화면에서 확인한다.
4. 재수집, 보류, 승인, parser 점검 요청을 처리한다.

성공 기준:

- 운영자가 CSV/SQL을 열지 않고 run 상태를 판단할 수 있다.
- failed/blocked run은 자동 snapshot 반영에서 제외된다.

### 7.4 데이터 관리자: snapshot 승인

1. 운영자가 snapshot 확정요청을 만든다.
2. 데이터 관리자가 후보 summary와 제외 사유를 확인한다.
3. 생성승인으로 `generated` snapshot을 만든다.
4. 검토 후 서빙승인으로 `approved` 상태로 올린다.

성공 기준:

- `generated` snapshot은 사용자 기준 데이터가 되지 않는다.
- `approved` snapshot만 서빙·freshness 비교 기준이 되고(`generated`는 비서빙), 사용자 as_of는 active deployment가 학습/import에 쓴 cutoff로 산정한다.

## 8. 기능 요구사항

| ID | 요구사항 | 기준 문서 | 구현 Epic/Task |
|---|---|---|---|
| FR-01 | 4개 원천을 주기 수집하고 run 단위로 추적한다. | MySQL, 주기 수집 운영 | E1-T02, E2, E8-T01 |
| FR-02 | raw payload는 object storage에 저장하고 DB에는 hash/path/size만 저장한다. | MySQL | E1-T08 |
| FR-03 | raw -> interpreted -> normalized 단계를 분리한다. | MySQL, 로드맵 | E1-T04, E3 |
| FR-04 | 표준화 이후 DB active NANT 재료(지지체/매체) 95분류를 적용하고 `learning_excluded=true` 기준으로 학습 제외를 고정한다. 어드민은 draft mapping을 관리하고 데이터 관리자가 active version을 전환한다. | NANT 분류 기준, MySQL | E0-T09, E1-T10, E3-T08~T09, E6-T12, E7-T13 |
| FR-05 | 작가 identity는 이름만으로 자동 확정하지 않는다. | artist_key 표준화 | E4-T05 |
| FR-06 | 신규 작가 후보는 승인 전 artist_key를 생성하지 않는다. | artist_key 표준화, API | E4-T06 |
| FR-07 | 어드민 검수 decision은 actor, 시각, 사유를 남긴다. | API, MySQL | E6-T01, E6-T07, E6-T10 |
| FR-08 | snapshot은 확정요청/생성승인/서빙승인 3단계로 처리한다. | API, MySQL | E5-T02~T04, E6-T08 |
| FR-09 | 사용자 API는 원천 URL/source/internal ID를 노출하지 않는다. | API, 화면 | E6-T04, E6-T05, E7-T02, E9-T04 |
| FR-10 | 예측 응답은 model_version, deployment_id, as_of를 포함한다. | API | E6-T05 |
| FR-11 | 1차 시장 가격 카드는 집계값만 사용자에게 노출한다. | 시나리오, API | E0-T06, E6-T05 |
| FR-12 | 개인정보/삭제 요청은 서비스 노출과 학습 반영을 차단할 수 있어야 한다. | 로드맵, 운영 | E0-T05, E1-T09, E8-T09 |
| FR-13 | run 미생성/stuck/blocked/품질 하락은 알림으로 감지한다. | 주기 수집 운영 | E2-T09, E8-T02~T05 |
| FR-14 | 모델 학습/import job, candidate 승인, active deployment 승격/롤백을 분리해 관리한다. 새 snapshot이나 candidate 생성만으로 운영 모델이 자동 변경되지 않는다. | 모델 학습/배포 수명주기, API | E1-T07, E5-T07~T11, E6-T09, E7-T10 |

## 9. 비기능 요구사항

| ID | 요구사항 | 설명 | 구현/검증 |
|---|---|---|---|
| NFR-01 | 재현성 | raw hash, collector_version, rules_version, snapshot_id, model_version으로 결과를 역추적한다. | E5-T05(deterministic), E9-T03 |
| NFR-02 | 장애 격리 | 수집 DB 장애가 사용자 예측 API 장애로 직접 전파되지 않는다. | 로드맵 §4 설계 고정, E9-T08 |
| NFR-03 | 감사 가능성 | 주요 쓰기 액션은 actor/시각/사유/전후 상태를 남긴다. | E6-T01, E6-T10 |
| NFR-04 | 멱등성 | 생성/승인 계열 API는 idempotency key 중복 호출을 안전하게 처리한다. | E6-T03 |
| NFR-05 | 동시성 | 검수 decision은 expected status 또는 claim/lock으로 충돌을 막는다. (`REVIEW-CLAIM-TTL`) | E6-T03, E6-T07 |
| NFR-06 | 개인정보 보호 | suppression/do-not-train/do-not-show 상태를 1차부터 지원한다. | E0-T05, E1-T09 |
| NFR-07 | 데이터 신선도 | active deployment 학습 snapshot 기준 as_of와 freshness 경고를 제공한다. (`FRESH-WARN-N`/`FRESH-HIDE-M`/`FRESH-MODEL-GAP`) | E5-T04, E6-T05, E6-T11, E7-T12 |

## 10. 성공 기준

1차 개발 성공 기준:

- 4개 원천의 첫 full run이 raw/interpreted/normalized까지 완료된다.
- 표준화 이후 DB active NANT 분류와 `learning_excluded` 학습 제외 플래그가 snapshot 후보에 반영된다.
- 작가명/alias/artist_key 후보 큐가 생성되고 어드민이 처리할 수 있다.
- snapshot 후보를 만들고, generated/approved 전이를 완료할 수 있다.
- 모델 학습/import 결과가 candidate로 등록되고, approved 모델만 active deployment로 승격된다.
- active deployment 기준으로 사용자 예측 API가 응답한다.
- 사용자 화면에서 예측 가격, 신뢰도, 기준일, 1차 시장 가격 카드가 표시된다.
- 어드민 화면에서 수집 상태, 검수 큐, snapshot, 모델 운영 상태를 처리할 수 있다.
- 원천 추적 정보가 사용자 API/화면에 노출되지 않는다.
- stuck run, run 미생성, 품질 하락, blocked source가 알림으로 잡힌다.
- 개인정보/삭제 요청이 서비스 노출과 snapshot 후보에 반영된다.

정량 launch gate (값은 [운영 파라미터](operational_parameters_20260625.md)를 SoT로 따른다):

- 4개 원천의 첫 full run 작가명 보유율이 `QUAL-ARTIST-MIN` 이상이다.
- 가격/크기 보유율이 `QUAL-PRICE-MIN`/`QUAL-SIZE-MIN` 미달이면 snapshot 보류로 잡힌다.
- auto_approved identity 샘플 검수에서 오연결 0건이다(E9-T02).
- 같은 입력과 `rules_version`이면 동일 snapshot export가 재현된다(byte-level 또는 합의된 비교 기준).

## 11. 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| 원천 사이트 구조 변경 | 파싱 실패, 수집량 급감 | raw 보존, parser fixture, canary, source별 품질 지표 |
| 작가 오연결 | Warm feature 오염 | 보수적 자동 확정, 검수 큐, identity_event_log, un-merge 영향 추적 |
| snapshot 상태 혼동 | 미승인 데이터 사용자 노출 | generated/approved 분리, API/화면 상태 표기 고정 |
| API/화면/DB 상태값 불일치 | 개발 지연, 운영 오류 | Phase 0에서 OpenAPI/DDL/enum 기준 확정 |
| 개인정보 삭제 요청 미흡 | 서비스/정책 리스크 | 1차부터 suppression/do-not-train/do-not-show 구현 |
| 범위 과대 | 일정 지연, 통합 리스크 후반 집중 | 1원천 end-to-end 수직 슬라이스(로드맵 §5.5 M1)로 조기 검증 후 폭 확장(M2), §5.8 비범위 고정, 백로그 의존성/완료 기준 추적 |

## 12. 오픈 이슈

아래 항목은 **구현 원칙(1차 포함 여부)이 아니라 세부 파라미터/스키마 결정**이다. 2026-06-25 기준 기본 선택은 [개발 착수 전 결정안](development_prestart_decisions_20260625.md)을 따른다. 사용자가 별도 선택하지 않으면 아래 "권장 기본값"으로 Phase 0 산출물(DDL/OpenAPI/seed/test)을 작성한다.

| 항목 | 권장 기본값 | 사용자 선택이 필요한 경우 | 결정 시점 |
|---|---|---|---|
| 사용자 API 인증/남용 방지 | 사용자 로그인 없음. first-party 익명 세션 + session/IP rate limit. 완전 공개 API는 채택하지 않는다. | M1부터 사용자 로그인/회원 기능이 필요하면 로그인 필수안으로 변경 | Phase 0 |
| 어드민 계정 | 제공 이메일/비밀번호 기반 admin user + JWT + 역할 claim. 초기 superuser는 개인 식별 가능한 계정으로 seed/CLI 생성. SSO는 후속 도입 | 조직 IdP/SSO를 M1부터 강제해야 하면 외부 IdP 우선안 선택 | Phase 0 |
| suppression 스키마 | 별도 `suppression_rule` 테이블을 SoT로 두고 service display/model training/raw scope를 분리 | 컬럼-only 단순화가 필요하면 audit/범위 확장 리스크 승인 필요 | Phase 0 |
| 1차 시장 가격 카드 계산 | 기존 가격 예측 `estimated_ho` nearest mapping, 최소 N=5, 매체별 N>=3, q05~q95 winsorized median/q25/q75 | 표본 부족 시 카드 숨김 기준을 더 강하게 둘지 정책 선택 | Phase 0 |
| 1차 시장 가격 카드 데이터 위치 | approved snapshot 생성 시 집계 테이블 생성. API는 active deployment training snapshot 또는 import manifest cutoff 기준 조회 | 실시간 feature store 계산을 원하면 latency/재현성 리스크 승인 필요 | Phase 0 |
| 예측 API 연결 방식 | 기존 예측 API를 호출하지 않고 데이터 수집 서비스 내부 joblib serving adapter가 active deployment의 joblib artifact를 직접 로드 | 기존 가격 예측 API를 직접 확장/호출하려면 회귀 테스트 범위 확대 필요 | Phase 0 |
| 신규 작가 후보 저장 방식 | 사용자 후보 제출을 M1에 포함하므로 물리 후보 큐 테이블을 1차 DDL에 포함 | 후보 제출을 M1에서 제외하면 SQL view/export로 축소 가능 | Phase 0/1 |
| object storage | local dev backend + S3-compatible adapter/path convention. DB에는 URI/hash/size만 저장 | 특정 cloud provider/IAM을 M1부터 고정해야 하면 provider 직접 고정 | Phase 1 |
| 모델 학습/변경 흐름 | Warm/Cold route와 model family는 고정한다. M1은 기존 joblib import/seed + fixed-test parity + active deployment. 이후 재학습은 같은 family 안에서 `model_training_job -> registry candidate -> approved -> deployment`로 `model_version`만 올린다 | model family/알고리즘/feature contract 변경은 별도 개발 작업으로 분리 | Phase 5 |
| M1 모델 연결 | Warm은 `warm_lite_unified_current_joblib_v0.1_candidate`, Cold는 `k80 보수적 운영` 후보(`resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05`)를 `cold_k80_conservative_official_v0.1_candidate` joblib bundle로 freeze해 registry/deployment에 등록 | Cold k80 joblib freeze/parity가 막히면 M1 cold route는 보류하고 fallback은 별도 승인 필요. `cold_prediction_v0.5_operational`은 과거 raw-input p95 방어 참고 산출물 | Phase 5 |
