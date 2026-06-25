# Track6 프론트 E2E 테스트 계획

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 사용자 화면과 어드민 화면의 E2E 테스트 시나리오를 정의한다.

관련 문서:

- [사용자 화면 상세 명세](user_frontend_screen_spec_20260625.md)
- [어드민 화면 상세 명세](admin_screen_detail_spec_20260625.md)
- [화면 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)
- [API mock/fixture 기준](frontend_api_mock_fixtures_20260625.md)

## 2. 테스트 원칙

- 사용자 화면은 원천 정보 비노출을 반드시 검증한다.
- 어드민 decision은 API payload까지 검증한다.
- conflict, forbidden, stale, loading, empty 상태를 포함한다.
- M1은 Art1 수직 슬라이스를 우선 검증한다.
- M2는 4개 원천과 전체 검수 큐를 검증한다.

## 3. M1 E2E

### E2E-M1-01 Art1 예측 성공

절차:

1. `/price-prediction` 진입
2. 작가명 검색
3. 확정 작가 선택
4. 작품 크기/재료 입력
5. 예측 요청
6. 결과 확인

검증:

- 가격 표시
- confidence 표시
- as_of 표시
- 1차 시장 가격 카드 표시
- source/source_url/internal id 비노출

### E2E-M1-02 작가명 검수 1건 처리

절차:

1. `/admin/track6/review/artist-names` 진입
2. 검수 row 선택
3. 상세 패널 확인
4. 표시명 승인
5. reason 입력
6. decision 제출

검증:

- `POST /review/artist-names/{alias_id}/decision`
- payload에 `decision=approve`, `expected_review_status`, `reason` 포함
- 성공 후 row 상태 갱신

### E2E-M1-03 수집 대시보드 기본 표시

절차:

1. `/admin/track6/collection-runs` 진입
2. Art1 source 카드 확인
3. run 상세 이동

검증:

- status badge 표시
- raw/normalized row 표시
- failed URL이 있으면 상세에 표시

## 4. 사용자 화면 E2E

### E2E-U-01 작가 검색 결과 없음

검증:

- 후보 없음 안내
- 신규 작가 후보 입력 CTA 표시

### E2E-U-02 신규 작가 후보 제출

검증:

- `POST /public/artist-candidates`
- artist_key 생성처럼 표현하지 않음
- 검수 필요 안내 표시

### E2E-U-03 필수 입력 validation

검증:

- width/height 누락 시 API 호출 전 validation 표시
- field_errors 수신 시 필드 하단 표시

### E2E-U-04 freshness 경고/카드 숨김

검증:

- warn 상태: 경고 표시
- hide 상태: 1차 시장 가격 카드 숨김

## 5. 어드민 검수 E2E

### E2E-A-01 작품 품질 수정 후 승인

검증:

- patch 입력
- `decision=approve_with_patch`
- reason 필수
- conflict 발생 시 row 재조회 안내

### E2E-A-02 artist_key 기존 연결 승인

검증:

- 데이터 관리자 권한 필요
- artist_key와 reason 전송
- 승인 후 상태 갱신

### E2E-A-03 신규 artist_key 생성 승인

검증:

- confirm dialog 표시
- idempotency_key 포함
- 성공 후 artist_key 표시

## 6. Snapshot/모델 E2E

### E2E-S-01 snapshot 3단계 전이

절차:

1. 확정요청
2. 생성승인
3. generated 상태 확인
4. 서빙승인
5. approved 상태 확인

검증:

- generated는 사용자 기준이 아님
- approved만 사용자 기준
- 각 단계 actor/reason 기록

### E2E-S-02 모델 승격/롤백

검증:

- 데이터 관리자 권한
- confirm dialog
- active deployment 변경
- current API 반영

## 7. 에러/권한 E2E

### E2E-E-01 권한 부족

검증:

- 데이터 관리자 화면에 운영 담당자로 접근 시 forbidden
- 필요한 역할 표시

### E2E-E-02 로그인 만료

검증:

- unauthenticated 상태 표시
- 재로그인 유도

### E2E-E-03 expected status conflict

검증:

- conflict banner
- row 재조회
- local 성공 처리 금지

### E2E-E-04 수집 DB 장애 격리

검증:

- 수집 DB 비가용 mock
- 사용자 예측 API는 승인 snapshot/feature store/model bundle 기준으로 정상 응답

## 8. 운영 알림 E2E/리허설

시나리오:

- run 미생성
- stuck run
- source blocked
- rate_limited
- 품질 하락

검증:

- 어드민 알림 화면에 표시
- run 상세 또는 source 상세로 이동 가능
- runbook 링크 또는 대응 안내 표시

## 9. 완료 기준

- M1 E2E 3개 통과
- 사용자 핵심 flow 통과
- 어드민 검수 핵심 flow 통과
- snapshot/model flow 통과
- conflict/forbidden/freshness 상태 통과
- source/internal 정보 비노출 테스트 통과
