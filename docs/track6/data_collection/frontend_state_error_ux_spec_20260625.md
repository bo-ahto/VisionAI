# Track6 프론트 상태/에러 UX 기준

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 사용자 화면과 어드민 화면에서 공통으로 처리해야 할 loading, empty, error, permission, conflict, freshness, claim/lock 상태의 UX 기준을 정의한다.

관련 문서:

- [사용자 화면 상세 명세](user_frontend_screen_spec_20260625.md)
- [어드민 화면 상세 명세](admin_screen_detail_spec_20260625.md)
- [프론트 마이크로카피 기준](frontend_microcopy_spec_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [운영 파라미터](operational_parameters_20260625.md)

본 문서는 상태/에러 taxonomy를 정의하고, 각 상태에 들어갈 실제 문구는 [프론트 마이크로카피 기준](frontend_microcopy_spec_20260625.md)을 단일 기준으로 한다.

## 2. 공통 상태

| 상태 | UX 기준 |
|---|---|
| loading | skeleton 또는 spinner. 테이블은 skeleton row 우선 |
| empty | 필터 조건과 함께 빈 결과 안내 |
| error | 사용자 메시지 + 재시도 버튼 + request_id |
| forbidden | 권한 부족 안내, 필요한 역할 표시 |
| unauthenticated | 로그인 만료 안내, 재로그인 유도 |
| stale | 데이터 기준일과 최신성 경고 표시 |

인증 방식(JWT 액세스 토큰 + 역할 claim)과 토큰 만료, 역할별 최소 권한(`required_role`)의 단일 기준은 [API 기획](user_admin_api_plan_20260625.md) §2.2.1과 [운영 파라미터](operational_parameters_20260625.md) §A다. forbidden/unauthenticated 표시는 이 정책을 따른다.

## 3. API 에러 표시

공통 error envelope:

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

표시 기준:

| code | 사용자 화면 | 어드민 화면 |
|---|---|---|
| VALIDATION_ERROR | 필드 하단 표시 | 필드 하단 표시 |
| NOT_FOUND | 대상 없음 안내 | 대상 없음 + 목록으로 이동 |
| CONFLICT | 재조회 후 다시 처리 안내 | 상태 충돌 banner + reload |
| FORBIDDEN | 권한 부족 안내 | 필요한 역할 표시 |
| UPSTREAM_UNAVAILABLE | 잠시 후 재시도 안내 | source/run 상태 링크 |
| PROCESSING_FAILED | 재시도 안내 | request_id와 로그 확인 안내 |

## 4. 검수 claim/lock 상태

상태:

| 상태 | 표시 | 액션 |
|---|---|---|
| unclaimed | 검수 가능 | claim 후 처리 |
| claimed_by_me | 내가 처리 중 | decision 가능 |
| claimed_by_other | 다른 담당자 처리 중 | decision 비활성 |
| expired | claim 만료 | 다시 claim 가능 |

표시 항목:

- claimed_by
- claim_expires_at
- 남은 시간

기준값:

- `REVIEW-CLAIM-TTL` 기본 30분

## 5. expected status conflict

발생 조건:

- 화면이 받은 `expected_review_status`와 서버 현재 상태가 다르다.

UX:

1. decision 실패 banner 표시
2. "다른 담당자가 먼저 처리했거나 상태가 변경되었습니다." 표시
3. row 재조회
4. 사용자가 다시 판단하도록 상세 패널 갱신

금지:

- local 상태만으로 성공 처리 금지
- 마지막 호출이 이긴 것으로 덮어쓰기 금지

## 6. Idempotency 상태

적용:

- 신규 artist_key 생성
- snapshot 확정요청/생성승인/서빙승인
- 모델 승격/롤백

UX:

- 버튼 더블클릭 방지
- 진행 중 버튼 disabled
- 같은 idempotency key 재시도 시 같은 결과 표시
- 다른 payload 충돌 시 conflict banner 표시

## 7. Snapshot 상태 표시

badge enum/라벨의 단일 기준은 [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md) §4다. 아래는 상태 전이 흐름 설명이다.

| 레이어/상태 | Badge | 설명 |
|---|---|---|
| snapshot_request / requested | 확정요청됨 | 운영자가 후보 범위/규칙을 고정 |
| snapshot_request / approved | 생성승인됨 | 생성 job 진입 전/중 |
| artwork_snapshot / generating | 생성 중 | snapshot build 진행 |
| artwork_snapshot / generated | 빌드완료(비서빙) | 사용자 기준 아님 |
| artwork_snapshot / approved | 서빙승인 | 사용자 기준 |
| artwork_snapshot / failed | 실패 | 재시도 또는 조사 필요 |

주의:

- request 레이어의 `approved`와 snapshot 레이어의 `approved`를 화면 라벨로 구분한다.
- 사용자 기준은 artwork_snapshot `approved`만이다.

## 8. Freshness 상태

기준:

- `FRESH-WARN-N`
- `FRESH-HIDE-M`
- `FRESH-MODEL-GAP`

사용자 화면:

| 상태 | 표시 |
|---|---|
| 정상 | 데이터 기준일 표시 |
| warn | 최신성 경고 + 데이터 기준일 |
| hide | 1차 시장 가격 카드 숨김 |
| model_gap | 모델 데이터 기준이 최신 승인 snapshot보다 오래됨 표시 |

어드민 화면:

- active deployment snapshot 기준일
- 최신 approved snapshot 기준일
- gap 일수
- 모델 재학습/승격 필요 여부

## 9. Source 상태

| 상태 | 표시 | 액션 |
|---|---|---|
| success | 정상 | 상세 보기 |
| partial_success | 부분 성공 | 실패분 재수집 |
| failed | 실패 | 상세/재수집 |
| rate_limited | 요청 제한 | 자동 재시도 금지, 운영 확인 |
| blocked | 차단 | source 일시 중지, 운영 확인 |
| auth_failed | 인증 실패 | 키 회전 안내 |
| stuck_timeout | 멈춘 run | watchdog 회수 표시 |

## 10. Toast/Banner 기준

Toast:

- 단순 성공: 저장 완료, 승인 완료, 재수집 요청 완료

Inline banner:

- conflict
- forbidden
- stale/freshness 경고
- source blocked/rate_limited
- snapshot generated but not approved

Modal confirmation:

- 신규 artist_key 생성
- snapshot 생성승인
- snapshot 서빙승인
- 모델 승격/롤백
- run 전체 재수집
