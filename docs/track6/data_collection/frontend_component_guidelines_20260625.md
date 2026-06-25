# Track6 프론트 컴포넌트 기준

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 사용자 화면과 어드민 화면에서 반복되는 UI 컴포넌트의 역할과 표시 기준을 정의한다.

관련 문서:

- [사용자 화면 상세 명세](user_frontend_screen_spec_20260625.md)
- [어드민 화면 상세 명세](admin_screen_detail_spec_20260625.md)
- [화면 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)
- [프론트 마이크로카피 기준](frontend_microcopy_spec_20260625.md)

## 2. 디자인 원칙

- 운영 도구는 조용하고 정보 밀도가 높은 UI로 만든다.
- 카드 중첩을 피하고, 테이블/필터/상세 패널 중심으로 구성한다.
- 상태값은 badge로 일관되게 표시한다.
- 위험 액션은 confirmation modal을 거친다.
- 사용자 화면은 원천 추적 정보를 노출하지 않는다.

## 3. 공통 컴포넌트

| 컴포넌트 | 사용처 |
|---|---|
| StatusBadge | run, snapshot, review, source, model 상태 |
| FreshnessIndicator | 사용자 결과, admin model/snapshot 화면 |
| FilterBar | admin 목록 화면 |
| DataTable | run 목록, 검수 큐, 로그 |
| DetailPanel | 검수 상세, run 상세 |
| DecisionBar | 검수 처리 버튼 |
| ConfirmDialog | 비가역/위험 액션 |
| ReasonTextarea | 모든 쓰기 액션 reason |
| ClaimBadge | 검수 row claim 상태 |
| AuditTrail | 처리 이력 |
| MetricTile | 대시보드 요약 |
| Toast | 단순 성공 알림(저장/승인/재수집 요청 완료) |
| InlineBanner | conflict/forbidden/stale/source blocked 등 inline 경고 |
| Pagination | 목록/검수 큐 페이지 이동 |
| EmptyState | 필터 조건과 함께 빈 결과 안내 |
| ErrorState | 조회 실패 + request_id + 재시도 |

## 4. StatusBadge 기준

Run:

| 값 | 라벨 |
|---|---|
| running | 실행 중 |
| success | 성공 |
| partial_success | 부분 성공 |
| failed | 실패 |

Quality:

| 값 | 라벨 |
|---|---|
| ok | 정상 |
| warning | 경고 |
| blocked | 반영 차단 |

Review:

| 값 | 라벨 |
|---|---|
| pending | 대기 |
| needs_review | 검수 필요 |
| auto_approved | 자동 승인 |
| approved | 승인 |
| match_rejected | 반려 |

`review_status` 값 집합과 decision→status 매핑의 단일 기준은 [API 기획](user_admin_api_plan_20260625.md) §8(및 MySQL 5.0.2)이다. 화면이 `expected_review_status`로 비교/전송하는 값도 이 enum을 따른다.

Snapshot:

snapshot 계열 상태값은 두 엔터티로 나뉜다(단일 기준: [API 기획](user_admin_api_plan_20260625.md) §2.6/§9.3). 같은 `approved` 문자열이 두 레이어에 모두 있으므로 badge는 `(레이어, 상태)`로 구분해 라벨을 그린다.

snapshot_request(확정요청 → 생성승인):

| 값 | 라벨 | 사용자 기준 |
|---|---|---|
| requested | 확정요청됨 | 아님 |
| approved | 생성승인됨(생성 job 진입 전/중) | 아님 |

artwork_snapshot(생성 → 서빙):

| 값 | 라벨 | 사용자 기준 |
|---|---|---|
| generating | 생성 중 | 아님 |
| generated | 빌드완료(비서빙) | 아님 |
| approved | 서빙승인 | 사용자 기준 |
| failed | 실패 | 아님 |

이 표가 snapshot badge 라벨의 단일 기준이며, [어드민 화면 명세](admin_screen_detail_spec_20260625.md) §9와 [상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md) §7은 이 표를 참조한다.

## 5. FilterBar 기준

구성:

- source select
- status select
- quality/review status select
- date range
- search input
- reset button

동작:

- 필터 변경 시 page는 1로 초기화
- URL query로 필터 상태를 보존
- reset은 전체 기본값으로 복귀

## 6. DataTable 기준

필수:

- stable row height
- loading skeleton
- empty row
- pagination
- sortable column은 명확한 sort icon
- row action은 우측 고정

금지:

- 긴 원천 URL을 그대로 테이블에 노출
- 상태별 색만으로 의미 전달
- decision 버튼을 테이블 row 안에 과도하게 배치

## 7. DetailPanel 기준

사용:

- 검수 큐 상세
- run 상세
- source 설정 상세

구성:

- 제목/상태/claim
- 원천값
- interpreted 값
- normalized 후보
- 변경 입력
- 처리 이력
- DecisionBar

## 8. DecisionBar 기준

버튼 순서:

1. primary 승인 계열
2. 보류
3. 반려/제외
4. 보조 액션(재검색, alias 추가)

모든 decision:

- reason 필수
- expected_review_status 포함
- 처리 중 disabled
- 성공 후 row 재조회 또는 목록 갱신

## 9. ConfirmDialog 기준

필수 사용:

- 신규 artist_key 생성
- snapshot 생성승인
- snapshot 서빙승인
- 모델 승격/롤백
- run 전체 재수집
- source 일시 중지/재개

내용:

- 액션명
- 대상 ID
- 영향 범위 요약
- reason 입력
- 취소/확인 버튼

## 10. FreshnessIndicator 기준

표시:

- 데이터 기준일
- 상태: normal/warn/hide/model_gap
- 경고 사유

사용처:

- 예측 결과 화면
- 1차 시장 가격 카드
- 모델 배포 화면
- snapshot 화면

## 11. MetricTile 기준

사용처:

- 수집 대시보드
- snapshot 후보 요약
- 모델 배포 요약

구성:

- label
- value
- delta
- status badge
- 설명 tooltip

## 12. 접근성/사용성 기준

- 모든 버튼은 텍스트 또는 accessible label을 가진다.
- 상태 badge는 텍스트를 포함한다.
- 위험 액션은 키보드로도 취소 가능해야 한다.
- 테이블 필터와 pagination은 URL로 복원 가능해야 한다.
- request_id는 복사 가능하게 표시한다.
