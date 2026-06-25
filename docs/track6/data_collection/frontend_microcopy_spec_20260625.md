# Track6 프론트 마이크로카피 기준

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 사용자 화면과 어드민 화면에서 노출하는 **클라이언트 소유 정적 문구**(버튼 라벨, 빈 상태, toast/banner 템플릿, confirm dialog, 제출 전 validation, 에러 fallback)의 단일 기준이다.

상태/에러 taxonomy는 [화면 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)을, 컴포넌트는 [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md)을 따른다. 본 문서는 그 구조에 들어갈 실제 문구만 정의한다.

관련 문서:

- [사용자 화면 상세 명세](user_frontend_screen_spec_20260625.md)
- [어드민 화면 상세 명세](admin_screen_detail_spec_20260625.md)
- [화면 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)
- [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [운영 파라미터](operational_parameters_20260625.md)

## 2. 클라이언트 문구 vs 서버 문구 경계

| 구분 | 소유 | 처리 |
|---|---|---|
| `error.message` | 서버 | 받은 문자열을 그대로 표시(verbatim). 본 문서의 fallback은 message가 비었을 때만 사용 |
| `error.field_errors[].message` | 서버 | 해당 필드 하단에 그대로 표시 |
| `freshness_label` (예: "최신 snapshot 기준, 최대 10일") | 서버 | 그대로 표시 |
| `confidence_label`, `review_reasons` | 서버 | 그대로 표시 |
| 제출 전 입력 validation | 클라이언트 | 본 문서 §4 |
| 버튼/CTA 라벨, 빈 상태, toast/banner, confirm dialog | 클라이언트 | 본 문서 §5~§10 |

원칙: 같은 의미의 문구를 서버와 클라이언트가 중복 정의하지 않는다. 서버가 주는 문구는 클라이언트가 다시 쓰지 않는다.

## 3. 작성 원칙(voice/tone)

- 존댓말, 1~2문장. 군더더기 없이 간결하게.
- 사용자를 비난하지 않는다. "잘못 입력했습니다"가 아니라 "확인해 주세요".
- 항상 **다음 행동**을 제시한다(재시도/입력 수정/문의).
- 실패 문구에는 `request_id`를 함께 노출하고 복사 가능하게 한다([컴포넌트 §12](frontend_component_guidelines_20260625.md)).
- 어드민 문구는 사용자 문구보다 구체적이어도 되지만, 원천 URL/source/internal ID는 노출 정책([API 기획](user_admin_api_plan_20260625.md) §2.3)을 따른다.
- 정책 상수가 들어가는 문구는 placeholder 키로 표기한다(`{N}`=`FRESH-WARN-N`=10일 등). 값 변경은 [운영 파라미터](operational_parameters_20260625.md)에서만 한다.

## 4. 제출 전 입력 validation(사용자, 클라이언트)

API 호출 전 클라이언트가 표시한다([사용자 명세](user_frontend_screen_spec_20260625.md) §9). 서버 `field_errors` 수신 시에는 서버 문구를 우선한다.

| 필드 | 조건 | 문구 |
|---|---|---|
| width_cm | 미입력 | 가로(cm)를 입력해 주세요. |
| width_cm | 0 이하 | 가로(cm)는 0보다 큰 값이어야 합니다. |
| height_cm | 미입력 | 세로(cm)를 입력해 주세요. |
| height_cm | 0 이하 | 세로(cm)는 0보다 큰 값이어야 합니다. |
| depth_cm | 값 있고 0 이하 | 깊이(cm)는 0보다 큰 값이어야 합니다. |
| medium | 미입력 | 재료를 입력하거나 선택해 주세요. |
| artwork_type | 미입력 | 작품 종류를 선택해 주세요. |
| artwork_year | 미래 연도 | 미래 연도가 입력되었습니다. 다시 확인해 주세요.(경고, 진행 가능) |

## 5. 사용자 화면 상태 문구

| 상황 | 제목/본문 | CTA |
|---|---|---|
| 작가 검색 결과 없음 | "검색 결과가 없습니다. 찾는 작가가 없다면 신규 작가로 등록할 수 있습니다." | 신규 작가 후보 등록 |
| 작가 검색 실패 | "검색에 실패했습니다. 잠시 후 다시 시도해 주세요." (request_id) | 다시 검색 |
| 후보 정보 부족 | "이 작가는 정보 검수가 진행 중입니다. 결과에 검수 필요 표시가 함께 나올 수 있습니다." | — |
| 신규 작가 후보 접수 | "신규 작가 후보가 접수되었습니다. 검수 후 반영됩니다." | 예측 계속하기 |
| 예측 처리 실패 | "예측을 완료하지 못했습니다. 잠시 후 다시 시도해 주세요." (request_id) | 다시 시도 |
| 모델/원천 일시 불가 | "지금은 예측을 제공할 수 없습니다. 잠시 후 다시 시도해 주세요." (request_id) | 다시 시도 |

주의:

- 신규 작가 접수 문구는 최종 `artist_key`가 생성된 것처럼 표현하지 않는다([사용자 명세](user_frontend_screen_spec_20260625.md) §5).
- `review_required=true`라도 계산값이 있으면 가격과 검수 필요 사유를 함께 보여준다. 검수 필요는 계산 실패와 다른 상태다.

## 6. Freshness 문구(사용자)

`{N}`=`FRESH-WARN-N`=10일, `{M}`=`FRESH-HIDE-M`=21일([운영 파라미터](operational_parameters_20260625.md) §E).

| 상태 | 문구 |
|---|---|
| normal | "데이터 기준일: {data_reference_date}" |
| warn | "데이터 기준일이 {N}일 이상 지났습니다. 참고용으로만 확인해 주세요. (기준일: {data_reference_date})" |
| hide | "최신 데이터 기준일이 너무 오래되어 1차 시장 가격 카드를 숨겼습니다." |
| model_gap | "최신 데이터보다 이전 데이터로 학습한 모델 기준입니다. (기준일: {data_reference_date})" |

## 7. 1차 시장 가격 카드 문구

| 상태 | 문구 |
|---|---|
| sample_count 충분 | 카드 정상 표시(표본 수 N 표기) |
| sample_count 부족 | "참고할 표본이 충분하지 않습니다. 가격은 참고용입니다." |

원천 사이트명/URL/작품 ID는 어떤 상태에서도 노출하지 않는다([사용자 명세](user_frontend_screen_spec_20260625.md) §7).

## 8. Toast 문구(어드민 성공)

| 액션 | 문구 |
|---|---|
| 검수 승인 | 승인되었습니다. |
| 검수 보류 | 보류 처리되었습니다. |
| 검수 반려/제외 | 반려되었습니다. / snapshot에서 제외되었습니다. |
| 표시명 수정 후 승인 | 수정 후 승인되었습니다. |
| alias 추가 | alias가 추가되었습니다. |
| 실패분 재수집 요청 | 재수집을 요청했습니다. |
| 후보 목록 다운로드 | 다운로드를 시작했습니다. |

## 9. Inline banner 문구(어드민)

`{role}`=필요 역할, `{source}`=원천, `{request_id}` 치환.

| 상황 | 문구 | 동작 |
|---|---|---|
| conflict (expected status 불일치) | "다른 담당자가 먼저 처리했거나 상태가 변경되었습니다. 항목을 다시 불러옵니다." | row 재조회 |
| forbidden | "이 작업에는 {role} 권한이 필요합니다." | — |
| unauthenticated | "로그인이 만료되었습니다. 다시 로그인해 주세요." | 재로그인 |
| stale/freshness 경고 | "데이터 기준일이 오래되었습니다. 재학습/승격이 필요한지 확인해 주세요." | — |
| source blocked | "{source} 원천이 차단 상태입니다. 자동 재시도하지 않습니다. 운영 확인이 필요합니다." | source 상세 |
| source rate_limited | "{source} 원천이 요청 제한 상태입니다. 자동 재시도하지 않습니다." | source 상세 |
| snapshot generated(미승인) | "빌드는 완료되었지만 아직 서빙 승인 전입니다. 사용자에게 노출되지 않습니다." | — |
| 처리 실패 | "처리에 실패했습니다. 로그를 확인해 주세요. (request_id: {request_id})" | 로그 확인 |

## 10. Confirm dialog 문구(비가역/위험 액션)

공통 구성: 제목 / 영향 요약 / reason 입력 / [취소] [확인]. 대상 ID와 영향 범위는 본문에 표기한다([컴포넌트 §9](frontend_component_guidelines_20260625.md)).

| 액션 | 제목 | 본문 | 확인 버튼 |
|---|---|---|---|
| 신규 artist_key 생성 | "신규 작가를 생성할까요?" | "생성 후에는 되돌리기 어렵습니다. 기존 후보와 중복이 없는지 확인해 주세요." | 생성 |
| snapshot 생성승인 | "snapshot 생성을 승인할까요?" | "승인하면 생성 작업이 시작됩니다. 후보 범위: 약 {count} row." | 생성승인 |
| snapshot 서빙승인 | "이 snapshot을 서빙 대상으로 승인할까요?" | "승인하면 사용자에게 이 기준 데이터가 노출됩니다." | 서빙승인 |
| 모델 승격 | "이 모델을 운영 모델로 승격할까요?" | "현재 운영 모델이 교체됩니다. ({route})" | 승격 |
| 모델 롤백 | "이전 모델로 롤백할까요?" | "운영 배포가 지정한 이전 모델로 전환됩니다." | 롤백 |
| run 전체 재수집 | "run 전체를 재수집할까요?" | "실패분만 재수집(권장)이 아니라 전체를 다시 수집합니다. 비용이 큽니다." | 전체 재수집 |
| source 일시 중지/재개 | "{source} 수집을 일시 중지할까요?" | "다음 수집 주기까지 이 원천을 수집하지 않습니다." | 일시 중지 |

reason 입력은 모든 쓰기 액션에서 필수다([API 기획](user_admin_api_plan_20260625.md) §2.2). 빈 reason 제출 시: "처리 사유를 입력해 주세요."

## 11. Claim/lock 문구(어드민 검수)

`{name}`=담당자, `{mm}`=남은 분. claim TTL 기본 30분(`REVIEW-CLAIM-TTL`).

| 상태 | 문구 |
|---|---|
| unclaimed | "검수 가능" |
| claimed_by_me | "내가 검수 중 (남은 시간 {mm}분)" |
| claimed_by_other | "{name} 검수 중 — 처리할 수 없습니다." |
| expired | "claim이 만료되었습니다. 다시 가져올 수 있습니다." |

## 12. 어드민 공통 상태 문구

| 상태 | 문구 |
|---|---|
| loading | (skeleton, 문구 없음) |
| empty(필터 결과 없음) | "조건에 맞는 항목이 없습니다. 필터를 조정해 보세요." |
| empty(검수 큐 없음) | "검수 대기 항목이 없습니다." |
| error(목록 조회 실패) | "목록을 불러오지 못했습니다. 다시 시도해 주세요. (request_id: {request_id})" |

## 13. Placeholder/변수 규칙

- `{request_id}`, `{role}`, `{source}`, `{name}`, `{count}`, `{route}`, `{data_reference_date}`, `{mm}`는 런타임 치환 변수다.
- `{N}`, `{M}`은 정책 상수 placeholder이며 값의 단일 기준은 [운영 파라미터](operational_parameters_20260625.md)다. 문구에 숫자를 직접 하드코딩하지 않는다.
- i18n 도입 시 본 문서의 키 단위로 번역 리소스를 구성한다(1차는 ko 단일).
