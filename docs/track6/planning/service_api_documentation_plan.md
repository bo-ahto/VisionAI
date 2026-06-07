# Track6 서비스 API 정리 문서 작성 계획

- 작성일: 2026-06-02
- 최신 갱신: 2026-06-03
- 목적: 협업자에게 실제 서비스에 사용할 신규 가격 예측 API의 구조, 요청값, 응답값, 모델 라우팅, 신뢰도/가격 범위 정책을 명확하게 전달하기 위한 문서 작성 계획
- 전제:
  - 기존 API 코드는 셀프 테스트용이므로 본 문서의 기준 API로 사용하지 않는다.
  - 기존 API path, request schema, response schema와의 하위 호환성은 고려하지 않는다.
  - Track6 실험 결과를 기준으로 서비스용 API 계약을 새로 정의한다.
- 최신 기준 실험:
  - `docs/track6/experiments/latest_experiment_result_synthesis.md`
  - `docs/track6/experiments/pp_svc3_warm_svc_blend_routing_summary.md`
  - `docs/track6/experiments/pp_svc4_warm_blend_holdout_stability_summary.md`

## 1. 문서 작성 방향

- 실험용 모델 설명이 아니라, 서비스에서 실제 호출할 신규 API 기준으로 작성한다.
- 협업자가 바로 확인해야 하는 내용은 앞쪽에 둔다.
- 모델명, 피처명, 후처리명은 필요한 경우만 쓰고, 먼저 서비스 관점의 의미를 설명한다.
- 기존 셀프 테스트 API와 분리된 새 계약임을 명확히 표시한다.
- 아직 확정되지 않은 실험 후보는 API 계약에 바로 넣지 않고, `적용 후보` 또는 `추후 확정 필요`로 분리한다.

## 2. 먼저 정리해야 할 핵심 질문

| 질문 | 문서에서 답해야 하는 내용 |
|---|---|
| 어떤 API를 호출해야 하는가? | 신규 서비스용 단건 예측, 배치 예측, 모델 정보, 모니터링 엔드포인트 |
| 요청값은 무엇이 필수인가? | 작가명, 가로/세로, 매체, 타깃 시장 |
| 어떤 값은 선택 입력인가? | 작품 제목, 제작년도, 작가 메타 정보, 외부 수집 스킵 여부 |
| Warm/Cold는 어떻게 나뉘는가? | 학습 작가 매칭 여부와 warm artist set 기준 |
| 가격은 어떻게 계산되는가? | 로그 가격 예측 후 원 가격으로 변환 |
| 응답값에는 무엇이 들어가는가? | 예측 가격, 가격 범위, 신뢰도 등급, 모델 정보, 처리 시간, 참고 작품 |
| 신뢰도는 어떻게 해석해야 하는가? | Warm/Cold 여부, 작가 이력, 외부 정보 여부, 가격 범위 폭 |
| 후처리는 어디까지 API에 반영할 것인가? | Warm은 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` 후보, Cold는 참고 예측가 + 넓은 범위 + 낮은 신뢰도 정책 |
| 비교군 통계는 어떻게 제공할 것인가? | 호당가 중앙값, 분위 범위, 매체별 분포, 표본 수 N을 별도 응답 블록으로 제공 |
| 협업자가 바로 구현해야 할 것은 무엇인가? | 요청/응답 JSON, 에러 처리, 화면 표시 정책, 로그/모니터링 필드 |

## 3. 작성할 문서 구성안

### 3.1 1페이지 요약

- API 목적
- 서비스에서 제공할 결과
- 단건 예측 API 경로
- 필수 입력값
- 응답의 핵심 필드
- Warm/Cold 처리 방식
- 현재 확정/미확정 항목

### 3.2 신규 API 엔드포인트 목록

| 구분 | Method | Path | 용도 | 우선순위 |
|---|---|---|---|---|
| 헬스체크 | GET | `/api/track6/health` | 서버 상태 확인 | 필수 |
| 모델 정보 | GET | `/api/track6/model-info` | 모델 버전, 후보 정책, 성능 요약 확인 | 필수 |
| 단건 예측 | POST | `/api/track6/price-estimate` | 작품 1건 가격 예측 | 필수 |
| 배치 예측 | POST | `/api/track6/price-estimate/batch` | 작품 여러 건 가격 예측 | 선택 |
| 모니터링 | GET | `/api/track6/monitor` | 예측 건수, Warm/Cold 비율, 신뢰도 분포 확인 | 운영 필수 |
| 메트릭 | GET | `/api/track6/metrics` | 운영 메트릭 수집용 | 운영 선택 |

- 위 path는 신규 서비스 API 초안이다.
- 협업자가 원하는 prefix 규칙이 있으면 path만 조정하고, 요청/응답 계약은 유지한다.
- 기존 테스트 API의 `/api/v1/*` path와는 분리한다.

### 3.3 단건 예측 요청 스펙

- 필수 입력:
  - `artist_name`: 작가명
  - `width_cm`: 작품 가로 길이
  - `height_cm`: 작품 세로 길이
  - `medium`: 작품 매체
- 기본값 입력:
  - `target_market`: 기본 `gallery`
  - `skip_external_lookup`: 기본 `false`
- 선택 입력:
  - `title`: 작품 제목
  - `artwork_id`: 외부 작품 ID
  - `artwork_url`: 외부 작품 URL
  - `year_made`: 제작년도
  - `artist_birth_year`
  - `artist_total_works`
  - `solo_count`
  - `group_count`
  - `followers`

### 3.4 단건 예측 응답 스펙

- `prediction`
  - `price_krw`: 원화 예측 가격
  - `price_usd`: 달러 환산 가격
  - `price_range.low`: 하한 가격
  - `price_range.high`: 상한 가격
  - `confidence_grade`: 신뢰도 등급
  - `margin`: 가격 범위 산정에 사용한 마진
- `model_info`
  - `route`: `warm` 또는 `cold`
  - `model_family`: `huber`, `lightgbm`, `catboost_auxiliary` 등 서비스 설명용 모델군
  - `model_policy`: 실제 적용 정책 이름
  - `is_known_artist`: 학습 작가 매칭 여부
  - `artist_history_count`: 학습 데이터 내 해당 작가 작품 수
  - `routing_reason`: Warm/Cold 라우팅 이유
  - `postprocessing_policy`: 적용된 후처리 정책
- `processing`
  - `total_ms`: 전체 처리 시간
  - `external_fetch_ms`: 외부 정보 수집 시간
- `external_sources_used`
  - 예측에 사용된 외부 소스 목록
- `matched_artworks`
  - 동일/유사 작품 참고 목록
- `artist_price_history`
  - 학습 데이터 내 작가 가격 이력 요약
- `feature_contributions`
  - 모델 설명용 피처 기여도

## 4. Track6 결과를 API에 반영하는 기준

### 4.1 Warm 처리

- Warm은 학습 데이터에 같은 작가가 존재하는 경우다.
- 현재 Track6 최신 실험 기준 Warm 운영 후보는 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`이다.
- `PP-SVC4`에서 반복 holdout 안정성까지 확인했으므로 API 문서에서는 아래처럼 정리한다.
  - 운영 후보: `warm_pp_svc3_svcnum_ppv8_070`
  - 내부 공식: `pred_log_final = 0.70 * pred_log_svc_numeric + 0.30 * pred_log_pp_v8`
  - 검증 상태: `PP-SVC4 holdout stability passed`
- 최종 artifact 반영 전까지는 API 응답의 `model_info`에 실제 사용 후보와 artifact 버전을 명시해야 한다.

### 4.2 Cold 처리

- Cold는 학습 데이터에 같은 작가가 없거나 작가 매칭이 불확실한 경우다.
- 현재 Track6 실험 기준 Cold는 Warm 수준의 단일 대표 가격으로 보기 어렵다.
- `PP-Y2`, `PP-Y18/PP-Y21` 등 개선 후보는 내부 비교 후보로 유지하되, 서비스 응답은 다음 용도로 먼저 정리한다.
  - 큰 오차 위험 판단
  - 가격 범위 조정
  - 낮은 신뢰도 표시
- API 문서에서는 Cold 응답을 확정 가격처럼 보이지 않게 정리해야 한다.

### 4.3 가격 범위와 신뢰도

- Warm:
  - 가격 범위 제공 가능
  - 신뢰도 등급은 실제 화면 표시 후보로 쓸 수 있음
- Cold:
  - 가격 범위가 넓고 test 포함률이 부족하므로 보수적인 문구가 필요
  - 단일 가격보다 `참고 예측가 + 넓은 범위 + 낮은 신뢰도` 구조로 응답 설명 필요

## 5. 문서에서 반드시 구분할 항목

| 구분 | 확정 여부 | 문서 표기 방식 |
|---|---|---|
| 신규 API path | 초안 | 기존 `/api/v1/*`와 분리해서 명시 |
| 요청/응답 기본 스키마 | 신규 정의 | Track6 서비스 기준으로 명시 |
| Warm/Cold 라우팅 개념 | 확정 | 학습 작가 매칭 기준으로 설명 |
| Warm 최종 후보 | 확정 후보 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`, `PP-SVC4` 반복 검증 완료 |
| Cold 최종 후보 | 부분 확정 | 참고 예측가 + 넓은 범위 + 낮은 신뢰도. 점 예측 후보는 내부 비교 유지 |
| 가격 범위 정책 | 부분 확정 | Warm 우선 적용, Cold 보수화 필요 |
| 비교군 통계 | 서비스 필수 | 호당가 중앙값, 범위, 매체별 분포, 표본 수 N |
| 외부 데이터 기반 고도화 | 미확정 | 수집 후 재실험 필요 |
| 운영 artifact 버전 | 확인 필요 | Track6 후보를 어떤 artifact 이름으로 고정할지 결정 필요 |

## 6. 협업자에게 보내는 문서 형태

### 6.1 1차 공유 문서

- 파일명 후보: `docs/track6/planning/service_api_summary_for_collaboration.md`
- 목적: 협업자가 API 구조와 화면 연동 방식을 빠르게 이해
- 포함 내용:
  - API 목적
  - 엔드포인트 목록
  - 요청 JSON 예시
  - 응답 JSON 예시
  - Warm/Cold 응답 차이
  - 신뢰도/가격 범위 표시 방식
  - 아직 확정되지 않은 항목

### 6.2 상세 스펙 문서

- 파일명: `docs/track6/planning/service_api_detailed_spec.md`
- 목적: 실제 구현자 또는 백엔드 협업자가 API 계약을 그대로 사용할 수 있게 정리
- 포함 내용:
  - 신규 API request/response 필드 정의
  - 필수/선택/기본값 구분
  - response field 타입
  - 에러 코드
  - 배치 예측 제한
  - 로그/모니터링 필드
  - 모델 라우팅 및 후처리 정책

### 6.3 서비스 적용 계획 문서

- 파일명: `docs/track6/planning/service_model_operationalization_plan.md`
- 목적: 모델 artifact, 비교군 DB, 추론 순서, 운영 로그, 배포 전 확인 사항 정리
- 포함 내용:
  - Warm 최종 후보 공식
  - Cold 표시 정책
  - 비교군 통계 DB 초안
  - artifact 재현성 점검 항목
  - 단기 실행 계획

## 7. 문서 작성 순서

| 순서 | 작업 | 산출물 |
|---:|---|---|
| 1 | 신규 서비스 API path와 응답 정책 확정 | API 초안표 |
| 2 | Track6 최종 후보를 API 응답 정책에 연결 | 반영 필요 항목표 |
| 3 | 협업자용 요약 문서 작성 | `service_api_summary_for_collaboration.md` |
| 4 | 요청/응답 JSON 예시 작성 | 단건/배치 예시 |
| 5 | Warm/Cold 화면 표시 정책 정리 | 신뢰도/가격 범위 설명 |
| 6 | 상세 스펙 문서 작성 | `service_api_detailed_spec.md` |
| 7 | 서비스 적용 계획 작성 | `service_model_operationalization_plan.md` |
| 8 | 코드 반영 필요 사항 목록 작성 | API TODO / risk list |

## 8. 예상 쟁점

- 기존 셀프 테스트 API와 신규 서비스 API가 혼동되지 않게 path와 문서명을 분리해야 한다.
- Track6 최신 결론은 Warm `PP-SVC3` 결합 후보 중심이므로 신규 API의 모델 설명도 이 기준으로 작성해야 한다.
- API 응답의 `model_policy`와 `postprocessing_policy`는 협업자와 사용자에게 노출될 수 있으므로 모델 후보가 바뀌면 반드시 갱신해야 한다.
- Cold는 예측 오차가 크므로 화면에서 단일 가격만 강조하면 안 된다.
- 외부 수집을 실시간으로 할지, 캐시/수동 입력 중심으로 할지에 따라 latency와 응답 안정성이 달라진다.
  - 비교군 통계는 모델 성능뿐 아니라 서비스 화면 요구사항이므로 API 응답과 DB 설계에 반드시 포함해야 한다.

## 9. 다음 작업 제안

- 협업자에게는 먼저 `service_api_summary_for_collaboration.md`를 공유한다.
- 구현자는 `service_api_detailed_spec.md`를 기준으로 request/response 계약을 검토한다.
- 모델/DB 담당자는 `service_model_operationalization_plan.md`를 기준으로 artifact, 비교군 통계 DB, 운영 로그를 준비한다.
