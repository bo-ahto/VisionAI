# 가격 예측 API 및 서비스 아키텍처 v0.2 종합 기획서

- 작성일: 2026-06-11
- 적용 버전: `price_prediction_v0.2`
- 문서 목적: v0.1 API/서비스 기획 문서를 바탕으로, v0.2 Warm/Cold 가격 예측 서비스의 API 계약, 화면 연동, 추론 아키텍처, 운영 데이터 학습 루프를 통합 정의
- 참고 v0.1 문서:
  - `models/track6/price_prediction_v0.1/evidence/reports/price_prediction_api_v0_1_spec.md`
  - `models/track6/price_prediction_v0.1/evidence/reports/service_api_detailed_spec.md`
  - `models/track6/price_prediction_v0.1/evidence/reports/service_model_operationalization_plan.md`
- 참고 v0.2 문서:
  - `docs/track6/experiments/warm_cold_service_operationalization_plan_next_version.md`
  - `docs/track6/experiments/warm_cold_v0_2_operational_learning_loop_plan.md`
  - `docs/track6/experiments/partner_warm_cold_best_model_report.md`

## 1. 결론

- v0.2는 v0.1의 작가명 기반 `artist_key` 매칭 구조를 유지
- v0.2는 가격 예측 API에 계산 설명, 입력 품질, 부족 정보, 실제 판매가 피드백 연결 정보를 추가
- v0.2는 Warm/Cold route를 더 명확하게 분리
- Warm은 작가 매칭이 확실하고 같은 작가 가격 이력이 충분한 경우에만 적용
- Cold는 같은 작가 가격 이력이 부족한 경우에도 최소 입력 기준을 만족하면 참고용 예상 가격을 표시
- Cold 예상 가격은 정확 감정가가 아니라 입력 정보 기반 예상 가격으로 표시
- v0.2는 예측만 하는 버전이 아니라, 운영 중 들어오는 실제 판매가를 검수 후 학습 후보 데이터로 축적하는 구조까지 포함
- 로컬 테스트는 v0.1과 동일하게 FastAPI 서버가 `/test/v0.2` 프론트 화면을 직접 서빙하는 방식으로 시작

## 2. v0.1 대비 v0.2 변경점

| 항목 | v0.1 | v0.2 |
|---|---|---|
| 서비스 버전 | `price_prediction_v0.1` | `price_prediction_v0.2` |
| 로컬 테스트 화면 | `/test/v0.1` | `/test/v0.2` |
| API prefix | `/api/v1` | `/api/v2` 기준 |
| 작가 입력 | 한글명/영문명으로 후보 확인 | 동일 유지 |
| 사용자 `artist_key` 입력 | 내부 테스트 옵션 | 일반 사용자 비노출 유지 |
| 작가 매칭 결과 | 후보/확정 여부 중심 | `artist_match_score`, 동명이인 위험, Warm 가능 기준 추가 |
| Warm 기준 | 유효 가격 이력 1건 이상이면 Warm 가능 처리 | `작가매칭신뢰도점수 >= 0.90` AND `같은작가_사용가능가격이력수 >= 5` |
| Cold 처리 | 자동 예측 보류 또는 참고 범위 중심 | 최소 입력 충족 시 참고용 예상 가격 표시 |
| 계산 설명 | 제한적 | `calculation_summary`, `model_components`, `guard_applied` 제공 |
| 입력 품질 | warning 중심 | `input_quality`, 누락 필수/권장 정보 제공 |
| 실제 판매가 피드백 | 2차 후보 | v0.2 핵심 기능으로 포함 |
| 학습 루프 | 별도 운영 필요 | 검수 후 학습 후보 데이터셋으로 축적 |

## 3. v0.2 서비스 범위

### 3.1 v0.2에 포함

- 모델 버전 조회
- 작가명 기반 작가 후보 확인
- 단일 작품 가격 예측
- Warm/Cold route와 라우팅 이유 반환
- Cold 최소 입력 정책 적용
- 예측가격, 가격범위, 신뢰도 반환
- 계산 요약 반환
- 부족 정보와 보완 입력 안내
- 실제 판매가 입력 API
- 예측 이벤트와 피드백 저장 구조
- 운영자 검수와 학습 후보 승격 구조
- 로컬 테스트 프론트

### 3.2 v0.2 이후로 미루는 항목

- 완전 자동 재학습
- 자동 모델 승격
- 실시간 외부 검색 API 상시 호출
- 검색 캐시 자동 수집/자동 갱신
- 이미지 피처를 운영 모델에 직접 반영
- 비동기 대량 배치 예측
- 운영자 수동 예측가 override

참고: 이미 사전 수집/검수된 검색 캐시를 조회해 사용하는 것은 v0.2 범위에 포함한다.

## 4. 전체 아키텍처

```text
[웹/앱 프론트]
  - 작품 입력
  - 작가 후보 선택
  - 예측 결과 확인
  - 실제 판매가 입력
        |
        v
[Price Prediction API v0.2]
  - /api/v2/price-models/current
  - /api/v2/artists:resolve
  - /api/v2/artworks/price-estimate
  - /api/v2/feedback/sale-price
        |
        v
[서비스 계층]
  - 입력 검증
  - 작가명 정규화
  - artist_key 매칭
  - Warm/Cold 라우팅
  - 피처 생성
  - 모델 추론
  - 계산 설명 생성
  - 예측 이벤트 저장
        |
        +--------------------------+
        |                          |
        v                          v
[모델/피처 계층]              [운영 데이터 계층]
  - Warm 예측기                 - prediction events
  - Cold 예측기                 - feedback
  - 비교군 통계                 - training candidates
  - 검색/작가 메타 캐시          - training runs
        |
        v
[응답 생성]
  - 예측 가격
  - 가격 범위
  - 신뢰도
  - 계산 설명
  - 부족 정보
  - 피드백 입력 토큰
```

## 5. 로컬 테스트 아키텍처

v0.1과 같은 방식으로 FastAPI 서버가 테스트 HTML을 직접 제공한다.

| 구성 | v0.2 권장 파일 |
|---|---|
| 서버 | `src/visionai/price_engine/api/operational_v0_2_server.py` |
| 서비스 계층 | `src/visionai/price_engine/api/operational_v0_2_service.py` |
| 스키마 | `src/visionai/price_engine/api/operational_v0_2_schemas.py` |
| 테스트 프론트 | `src/visionai/price_engine/api/static/operational_v0_2_test.html` |
| 로컬 화면 | `http://127.0.0.1:8020/test/v0.2` |
| API base | `http://127.0.0.1:8020/api/v2` |

로컬 테스트 흐름:

```text
[브라우저 /test/v0.2]
        |
        v
[작가명 입력]
        |
        v
POST /api/v2/artists:resolve
        |
        v
[작가 후보 선택 또는 자동 확정]
        |
        v
POST /api/v2/artworks/price-estimate
        |
        v
[예측 결과 + 계산 설명 + 부족 정보 표시]
        |
        v
POST /api/v2/feedback/sale-price
```

## 6. API 설계 원칙

- 서비스 화면에서 필요한 정보를 한 번의 예측 응답으로 받을 수 있게 구성
- 내부 실험명은 사용자 화면에 노출하지 않음
- 기능 중심 이름을 API 응답에 사용
- Warm/Cold route와 route 사유를 항상 반환
- Cold는 참고용 예상 가격임을 응답과 화면 문구에서 명확히 표시
- 작가 매칭이 불확실하면 자동 예측보다 후보 선택 또는 운영 검수를 우선
- 예측 당시 입력값과 피처는 반드시 저장
- 실제 판매가 피드백은 예측 결과와 `prediction_id`로 연결
- 검수 전 피드백은 학습에 반영하지 않음

## 7. 엔드포인트 목록

| Method | Endpoint | 목적 | v0.2 포함 |
|---|---|---|---|
| `GET` | `/api/v2/health` | API 상태 확인 | 필수 |
| `GET` | `/api/v2/price-models/current` | 현재 모델/정책 조회 | 필수 |
| `POST` | `/api/v2/artists:resolve` | 작가명으로 artist_key 후보 확인 | 필수 |
| `POST` | `/api/v2/artworks/price-estimate` | 단일 작품 가격 예측 | 필수 |
| `POST` | `/api/v2/feedback/sale-price` | 실제 판매가 입력 | 필수 |
| `PATCH` | `/api/v2/predictions/{prediction_id}/additional-input` | 예측 후 보완 정보 입력 | 권장 |
| `GET` | `/api/v2/predictions/{prediction_id}` | 예측 결과 재조회 | 선택 |
| `GET` | `/api/v2/admin/training-candidates` | 학습 후보 검수 목록 | 운영자용 |
| `POST` | `/api/v2/admin/training-candidates/{candidate_id}:approve` | 학습 후보 승인 | 운영자용 |

## 8. API 1: Health

### 8.1 Endpoint

```http
GET /api/v2/health
```

### 8.2 Response 예시

```json
{
  "status": "ok",
  "service_version": "price_prediction_v0.2",
  "operational_loaded": true,
  "warm_model_loaded": true,
  "cold_model_loaded": true,
  "feedback_store_loaded": true
}
```

## 9. API 2: 현재 모델 조회

### 9.1 Endpoint

```http
GET /api/v2/price-models/current
```

### 9.2 Response 예시

```json
{
  "request_id": "req_20260611_000001",
  "status": "success",
  "created_at": "2026-06-11T12:00:00+09:00",
  "model_version": "price_prediction_v0.2",
  "model_status": "candidate",
  "display_policy": {
    "warm": "price_with_range",
    "cold": "estimated_price_with_reference_warning",
    "review_required": "no_single_price"
  },
  "routing_policy": {
    "warm_artist_match_score_min": 0.9,
    "warm_same_artist_price_count_min": 5
  },
  "exchange_rates": {
    "base_currency": "KRW",
    "USD": 1380,
    "EUR": 1530,
    "GBP": 1780,
    "HKD": 178,
    "JPY": 9.5
  },
  "feedback_policy": {
    "actual_sale_price_feedback_enabled": true,
    "auto_training_enabled": false,
    "review_required_before_training": true
  }
}
```

## 10. API 3: 작가 매칭

### 10.1 Endpoint

```http
POST /api/v2/artists:resolve
```

### 10.2 Request 예시

```json
{
  "artist": {
    "artist_key": null,
    "name_ko": "박서보",
    "name_en": "Park Seo-Bo",
    "birth_year": 1931,
    "nationality": "Korea"
  },
  "options": {
    "max_candidates": 5
  }
}
```

### 10.3 작가 매칭 점수

```text
작가매칭신뢰도점수 =
  0.70 * 이름일치점수
+ 0.20 * 보조정보일치점수
+ 0.10 * 학습작가등록점수
- 0.15 * 동명이인위험점수
- 0.20 * 핵심정보충돌점수
```

직접 `artist_key`가 검증된 경우에는 `1.00`으로 처리할 수 있다. 이름 기반 후보는 최대 `0.95`로 제한해, 사용자가 직접 입력한 이름만으로 과도하게 확정하지 않도록 한다.

### 10.4 Response 예시

```json
{
  "request_id": "req_20260611_000002",
  "status": "success",
  "created_at": "2026-06-11T12:01:00+09:00",
  "model_version": "price_prediction_v0.2",
  "resolved": true,
  "requires_selection": false,
  "selected_artist": {
    "artist_key": "park-seobo",
    "name_ko": "박서보",
    "name_en": "Park Seo-Bo",
    "birth_year": 1931,
    "nationality": "Korea",
    "match_status": "exact",
    "matched_alias": "박서보",
    "match_basis": "verified_ko_name",
    "artist_match_score": 0.95,
    "homonym_risk_score": 0.02,
    "review_required": false,
    "same_artist_training_price_count": 24,
    "warm_available": true,
    "route_recommendation": "warm"
  },
  "candidates": [
    {
      "artist_key": "park-seobo",
      "name_ko": "박서보",
      "name_en": "Park Seo-Bo",
      "birth_year": 1931,
      "nationality": "Korea",
      "match_status": "exact",
      "matched_alias": "박서보",
      "match_basis": "verified_ko_name",
      "artist_match_score": 0.95,
      "homonym_risk_score": 0.02,
      "review_required": false,
      "same_artist_training_price_count": 24,
      "warm_available": true,
      "route_recommendation": "warm"
    }
  ],
  "warnings": []
}
```

## 11. API 4: 가격 예측

### 11.1 Endpoint

```http
POST /api/v2/artworks/price-estimate
```

### 11.2 Request 예시

```json
{
  "artwork": {
    "external_artwork_id": "artwork_12345",
    "title": "Untitled",
    "artist": {
      "artist_key": "park-seobo",
      "name_ko": "박서보",
      "name_en": "Park Seo-Bo"
    },
    "year": 2010,
    "dimensions": {
      "width_cm": 130.0,
      "height_cm": 162.0,
      "depth_cm": null
    },
    "medium": {
      "medium_category": "mixed",
      "support_category": "paper"
    },
    "category": "Painting",
    "artwork_url": "https://example.com/artwork/12345"
  },
  "options": {
    "currency": "KRW",
    "include_comparable_samples": true,
    "max_comparable_samples": 10,
    "include_calculation_summary": true,
    "include_feedback_token": true
  }
}
```

### 11.3 최소 입력 정책

Warm은 작가 매칭과 같은 작가 가격 이력이 핵심이다. Cold는 최소 입력이 충족되어야 단일 예상 가격을 표시한다.

```text
Cold 예상 가격 표시 가능 =
  (한글 작가명 또는 영문 작가명 존재)
  AND (가로 cm 존재)
  AND (세로 cm 존재)
  AND (매체 존재)
  AND (지지체 존재)
```

| 입력 상태 | 처리 |
|---|---|
| 작가명 + 가로/세로 + 매체 + 지지체 존재 | Cold 예상 가격 표시 가능 |
| 크기/매체/지지체 일부 누락 | 단일 예상 가격 숨김, 부족 정보 요청 |
| 작가명 없음 | 예측 보류 |
| 동명이인 후보 여러 명 | 예측 보류, 후보 선택 요청 |

### 11.4 Warm/Cold 라우팅 공식

```text
Warm 적용 여부 =
  (작가매칭신뢰도점수 >= 0.90)
  AND
  (같은작가_사용가능가격이력수 >= 5)
```

위 조건을 만족하지 못하면 Cold 또는 review_required로 보낸다.

### 11.5 Response 예시

```json
{
  "request_id": "req_20260611_000003",
  "prediction_id": "pred_20260611_000003",
  "status": "success",
  "created_at": "2026-06-11T12:02:00+09:00",
  "model_version": "price_prediction_v0.2",
  "route": "warm",
  "display_policy": "price_with_range",
  "prediction": {
    "price_krw": 19854740,
    "price_display": "1,985만원",
    "range_krw": {
      "low": 11868000,
      "mid": 19854740,
      "high": 32640000
    },
    "range_display": "1,187만 - 3,264만원",
    "confidence": {
      "level": "medium",
      "score": 0.72,
      "reason_codes": [
        "WARM_ARTIST_MATCHED",
        "LOW_SIMILAR_SAMPLE_COUNT"
      ]
    }
  },
  "routing": {
    "artist_matched": true,
    "matched_artist_key": "park-seobo",
    "artist_match_score": 1.0,
    "same_artist_training_price_count": 24,
    "route_policy": "warm_match_score_0.90_and_price_count_5",
    "route_reason": "작가 매칭 신뢰도와 같은 작가 가격 이력 기준을 모두 만족해 Warm route 적용"
  },
  "input_quality": {
    "minimum_input_status": "passed",
    "missing_required_fields": [],
    "missing_recommended_fields": [
      "artwork_url"
    ],
    "confidence_penalty_reasons": []
  },
  "calculation_summary": {
    "user_facing_formula": "예측가격 = 기준가격 + 보정값",
    "route": "warm",
    "model_components": [
      "같은 작가와 유사 작품 가격 이력 기반 기준가격",
      "방향 분류 기반 보정 여부 판단",
      "Huber 잔차 기반 미세 보정"
    ],
    "guard_applied": false,
    "explanation_text": "같은 작가 가격 이력이 충분하여 Warm 기준가격을 만들고, 보정 신호가 안정적인 경우에만 작은 폭으로 보정했습니다."
  },
  "feedback": {
    "can_submit_actual_sale_price": true,
    "feedback_endpoint": "/api/v2/feedback/sale-price",
    "required_fields": [
      "actual_sale_price",
      "actual_sale_currency",
      "sale_date",
      "sale_channel",
      "user_consent_for_training"
    ]
  },
  "warnings": []
}
```

## 12. Warm 모델 처리 흐름

사용자 설명용 구조:

```text
Warm 예측가격 =
  같은 작가/유사 작품 기반 기준가격
+ 안정 조건을 통과한 미세 보정값
```

운영 내부 처리 흐름:

```text
[작가 매칭 확정]
        |
        v
[같은 작가 가격 이력 수 확인]
        |
        v
[기준 로그가격 생성]
  - 같은 작가 가격 이력
  - 유사 작품 통계
  - 작품 크기/매체/지지체
        |
        v
[위험도와 불확실성 계산]
  - 유사 작품 표본 수
  - 가격 범위 비율
  - Quantile 예측 폭
  - 내부 예측값 간 차이
        |
        v
[보정 방향 판단]
  - 방향 분류 모델
  - Huber 잔차 모델
        |
        v
[상한 내 미세 보정]
        |
        v
[최종 Warm 가격 = exp(최종 Warm 로그가격)]
```

Warm은 기준가격을 크게 흔드는 모델이 아니라, 기준가격이 안정적일 때만 작은 보정값을 더하는 구조다.

## 13. Cold 모델 처리 흐름

사용자 설명용 구조:

```text
Cold 예상 가격 =
  작품 정보 기반 기준 가격
+ 작가 정보 보정
+ 사전 수집/검수된 검색 문맥 보정
- 과대예측 방어 보정
```

운영 내부 처리 흐름:

```text
[Cold 최소 입력 확인]
        |
        v
[작품 기본 피처 생성]
  - 가로/세로/깊이
  - 면적
  - 로그 면적
  - 가로세로비
  - 매체/지지체
  - 크기 구간
        |
        v
[작가 메타/검색 피처 결합]
  - 작가 생년/국적
  - 작가 활동성
  - 사전 수집/검수된 검색 품질
  - 사전 수집/검수된 갤러리/미술관 문맥
        |
        v
[LightGBM Quantile 예측]
  - 낮은 분위 가격
  - 중앙 분위 가격
  - 높은 분위 가격
  - Quantile 예측구간폭
        |
        v
[과대예측 방어]
  - 예측구간폭이 넓고
  - 중앙 예측이 낮은쪽 40% 지점보다 충분히 높으면
  - 방어 가격 쪽으로 일부 이동
        |
        v
[작가 검색 보정]
        |
        v
[최종 Cold 가격 = exp(최종 Cold 로그가격)]
```

검색 캐시가 없는 경우:

- 실시간 외부 검색을 즉시 호출하지 않음
- 검색 문맥 보정값은 `0`으로 처리
- raw-input 실행 가능 Cold fallback을 사용하거나 신뢰도를 하향
- 화면에는 검색 문맥이 부족해 예상 가격의 신뢰도가 낮아질 수 있음을 표시

Cold 화면 문구:

```text
이 가격은 입력 정보 기반 예상 가격입니다.
같은 작가의 충분한 가격 이력이 없거나 작가 정보가 제한적인 경우,
작품 크기, 매체, 지지체, 작가 정보, 검색 문맥을 이용해 계산합니다.
정확 감정가 또는 판매 보장 가격은 아닙니다.
```

## 14. API 5: 실제 판매가 피드백

### 14.1 Endpoint

```http
POST /api/v2/feedback/sale-price
```

### 14.2 Request 예시

```json
{
  "prediction_id": "pred_20260611_000003",
  "actual_sale_price": 12000000,
  "actual_sale_currency": "KRW",
  "sale_date": "2026-06-11",
  "sale_channel": "gallery",
  "sale_type": "actual_sale",
  "evidence_status": "partial",
  "user_consent_for_training": true,
  "additional_input": {
    "year": 2024,
    "medium_category": "acrylic",
    "support_category": "canvas"
  }
}
```

### 14.3 Response 예시

```json
{
  "feedback_id": "fb_20260611_000001",
  "prediction_id": "pred_20260611_000003",
  "status": "received",
  "review_status": "needs_review",
  "message": "실제 판매가가 접수되었습니다. 운영 검수 후 학습 후보 데이터로 반영될 수 있습니다."
}
```

## 15. 운영 데이터 학습 루프

v0.2에서는 실제 판매가를 바로 모델에 넣지 않는다. 검수된 데이터만 학습 후보로 승격한다.

```text
[예측 이벤트 저장]
        |
        v
[실제 판매가 또는 보완 입력 접수]
        |
        v
[운영 검수]
  - 작가 매칭 검수
  - 작품 중복 검수
  - 가격 이상치 검수
  - 판매 증빙 검수
  - 학습 활용 동의 확인
        |
        v
[학습 후보 승격]
        |
        v
[주기적 재학습 후보 데이터셋 생성]
        |
        v
[기존 fixed test + 신규 운영 holdout 검증]
        |
        v
[후보 모델 승격 또는 보류]
```

학습 후보 승격 기준:

```text
학습후보승격 =
  (실제판매가_원화 > 0)
  AND (거래유형 = actual_sale)
  AND (판매증빙상태 IN {partial, verified})
  AND (학습활용동의 = true)
  AND (검수상태 = approved)
  AND (운영데이터품질점수 >= 0.80)
  AND (중복상태 != duplicate_excluded)
```

운영데이터품질점수:

```text
운영데이터품질점수 =
  0.30 * 판매가격증빙점수
+ 0.25 * 작가매칭신뢰도점수
+ 0.20 * 작품정보완성도점수
+ 0.15 * 판매채널신뢰도점수
+ 0.10 * 중복검수통과점수
```

## 16. DB 테이블 구성

| 테이블 | 목적 | v0.2 필수 |
|---|---|---|
| `artist_registry` | 작가 식별, alias, 동명이인 관리 | 필수 |
| `artwork_master` | 작품 기본 정보 관리 | 필수 |
| `price_history` | 검수된 가격 이력 관리 | 필수 |
| `comparable_group_stats` | 유사 작품 통계와 호당가 카드 | 필수 |
| `search_artist_signal_cache` | 사전 수집/검수된 작가 검색/전시/갤러리 문맥 캐시 | 권장 |
| `model_artifact_registry` | 모델 artifact 버전 관리 | 필수 |
| `feature_schema_registry` | 피처 생성 버전 관리 | 필수 |
| `price_prediction_events` | 예측 이벤트 저장 | 필수 |
| `price_prediction_feedback` | 실제 판매가/보완 입력 저장 | 필수 |
| `training_candidate_labels` | 학습 후보 라벨 관리 | 필수 |
| `model_training_runs` | 재학습 실행 이력 | 필수 |

## 17. 핵심 테이블 필드

### 17.1 `price_prediction_events`

| 필드 | 설명 |
|---|---|
| `prediction_id` | 예측 요청 고유 ID |
| `model_version` | `price_prediction_v0.2` |
| `warm_model_version` | Warm 내부 모델 버전 |
| `cold_model_version` | Cold 내부 모델 버전 |
| `route` | warm/cold/review_required |
| `display_policy` | price_with_range/estimated_price_with_reference_warning/no_single_price |
| `artist_key` | 내부 작가 식별자 |
| `artist_match_score` | 작가 매칭 신뢰도 |
| `same_artist_training_price_count` | 같은 작가 사용 가능 가격 이력 수 |
| `input_snapshot_json` | 사용자 입력 원본 |
| `feature_snapshot_json` | 예측에 사용한 파생 피처 |
| `prediction_price_krw` | 예측 가격 |
| `range_low_krw`, `range_high_krw` | 가격 범위 |
| `confidence_level` | high/medium/low |
| `calculation_summary_json` | 계산 설명 |

### 17.2 `price_prediction_feedback`

| 필드 | 설명 |
|---|---|
| `feedback_id` | 피드백 고유 ID |
| `prediction_id` | 연결된 예측 ID |
| `actual_sale_price` | 실제 판매가 |
| `actual_sale_currency` | 통화 |
| `actual_sale_price_krw` | 원화 환산 판매가 |
| `sale_date` | 판매일 |
| `sale_channel` | 판매 채널 |
| `sale_type` | actual_sale/offer_price/listing_price/appraisal |
| `evidence_status` | none/partial/verified |
| `user_consent_for_training` | 학습 활용 동의 |
| `review_status` | raw_collected/needs_review/approved/rejected |

### 17.3 `training_candidate_labels`

| 필드 | 설명 |
|---|---|
| `candidate_id` | 학습 후보 ID |
| `prediction_id` | 원 예측 ID |
| `feedback_id` | 원 피드백 ID |
| `route_at_prediction` | 예측 당시 route |
| `artist_key` | 작가 식별자 |
| `actual_price_krw` | 학습 라벨 |
| `actual_log_price` | `log(actual_price_krw)` |
| `quality_score` | 운영데이터품질점수 |
| `training_eligible` | 학습 사용 가능 여부 |
| `holdout_reserved` | 신규 holdout 보관 여부 |
| `feature_snapshot_json` | 당시 피처 |
| `source_model_version` | 예측 당시 모델 버전 |

## 18. 프론트 화면 구성

### 18.1 입력 화면

| 영역 | 필드 |
|---|---|
| 작가 정보 | 한글 작가명, 영문 작가명, 후보 선택 |
| 작품 정보 | 작품명, 제작연도, 가로, 세로, 깊이 |
| 재료 정보 | 매체, 지지체, 작품 유형 |
| 선택 정보 | 작품 URL, 이미지, 판매 채널 후보 |
| 내부 테스트 옵션 | artist_key, 샘플 수, 원본 JSON 보기 |

### 18.2 결과 화면

| 카드 | 내용 |
|---|---|
| 예측 가격 | 가격 또는 참고 예상 가격 |
| 가격 범위 | 하단/대표/상단 |
| route | Warm/Cold/review_required |
| 신뢰도 | level, score, reason code |
| 계산 설명 | 기준가격, 보정값, 방어 적용 여부 |
| 사용된 입력 | 예측에 반영된 필드 |
| 부족 정보 | 추가하면 좋은 필드 |
| 실제 판매가 입력 | 피드백 API 연결 |
| 원본 JSON | 개발/검수용 |

## 19. Warning Code

| 코드 | 의미 |
|---|---|
| `ARTIST_NOT_RESOLVED` | 작가 매칭 실패 |
| `ARTIST_AMBIGUOUS` | 동명이인 또는 후보 다수 |
| `ARTIST_REVIEW_REQUIRED` | 작가 검수 필요 |
| `WARM_ROUTE_APPLIED` | Warm route 적용 |
| `COLD_ROUTE_APPLIED` | Cold route 적용 |
| `LOW_SAME_ARTIST_HISTORY` | 같은 작가 가격 이력 부족 |
| `COLD_REFERENCE_PRICE_ONLY` | Cold 참고용 예상 가격 |
| `MISSING_REQUIRED_INPUT` | 필수 입력 누락 |
| `MISSING_RECOMMENDED_INPUT` | 권장 입력 누락 |
| `LOW_SIMILAR_SAMPLE_COUNT` | 유사 작품 표본 부족 |
| `WIDE_PRICE_RANGE` | 가격 범위 넓음 |
| `OVERPREDICTION_GUARD_APPLIED` | 과대예측 방어 적용 |
| `SEARCH_QUALITY_LOW` | 검색 문맥 품질 낮음 |
| `FEEDBACK_REVIEW_REQUIRED` | 실제 판매가 검수 필요 |

## 20. Error Code

| HTTP Status | 코드 | 의미 |
|---:|---|---|
| 400 | `INVALID_REQUEST` | 요청 JSON 형식 오류 |
| 400 | `MISSING_REQUIRED_FIELD` | 필수 입력값 누락 |
| 404 | `ARTIST_NOT_FOUND` | 요청한 artist_key 없음 |
| 409 | `ARTIST_SELECTION_REQUIRED` | 후보 선택 필요 |
| 422 | `INVALID_DIMENSIONS` | 크기 값 비정상 |
| 422 | `UNSUPPORTED_MEDIUM` | 지원하지 않는 매체/지지체 |
| 422 | `COLD_MINIMUM_INPUT_NOT_MET` | Cold 예상 가격 최소 입력 미충족 |
| 500 | `MODEL_INFERENCE_FAILED` | 모델 추론 실패 |
| 503 | `MODEL_UNAVAILABLE` | 모델 artifact 또는 feature store 사용 불가 |

## 21. 모니터링

### 21.1 API 모니터링

| 지표 | 목적 |
|---|---|
| 요청 수 | 사용량 확인 |
| latency p50/p95 | 응답 속도 |
| error rate | 장애 감지 |
| route별 요청 비율 | Warm/Cold 데이터 커버리지 확인 |
| 작가 매칭 실패율 | alias/registry 보강 필요성 확인 |
| 동명이인 후보율 | 검수 UX 개선 필요성 확인 |

### 21.2 모델 모니터링

| 지표 | 목적 |
|---|---|
| 예측 가격 분포 | 비정상 예측 감지 |
| 가격 범위 폭 분포 | 과도하게 넓은 범위 감지 |
| confidence 분포 | 낮은 신뢰도 비중 추적 |
| Cold 최소 입력 부족률 | 입력 UX 개선 |
| 실제 판매가 입력률 | 학습 데이터 확보 속도 확인 |
| 예측가 대비 실제 판매가 APE | 운영 성능 추적 |
| route별 MAPE/p95 APE | Warm/Cold 성능 분리 추적 |

## 22. 구현 단계

| 순서 | 작업 | 산출물 |
|---:|---|---|
| 1 | v0.2 API 스키마 정의 | `operational_v0_2_schemas.py` |
| 2 | v0.1 작가 매칭 로직 재사용/확장 | `artist_match_score`, 후보 사유 |
| 3 | v0.2 라우팅 정책 적용 | Warm/Cold route validator |
| 4 | Cold 최소 입력 validator 추가 | `input_quality` |
| 5 | Warm/Cold 추론 서비스 연결 | `operational_v0_2_service.py`, Warm raw adapter, Cold cache-backed/fallback 경로 |
| 6 | 계산 설명 생성기 추가 | `calculation_summary` |
| 7 | 예측 이벤트 저장 추가 | `price_prediction_events` |
| 8 | 실제 판매가 피드백 API 추가 | `price_prediction_feedback` |
| 9 | 로컬 테스트 프론트 작성 | `/test/v0.2` |
| 10 | 학습 후보 승격 배치 작성 | `training_candidate_labels` |
| 11 | 회귀 테스트 작성 | 반복 입력, route, 누락 입력, feedback |
| 12 | HTML/API 문서 갱신 | 개발 공유 문서 |

## 23. 배포 전 체크리스트

| 항목 | 기준 |
|---|---|
| 같은 입력 반복 호출 | 예측값 동일 |
| 작가명 입력 | 한글/영문명으로 후보 조회 가능 |
| 동명이인 처리 | 자동 예측 보류 |
| Warm 라우팅 | 점수 0.90 이상, 같은 작가 가격 이력 5건 이상 |
| Cold 최소 입력 | 누락 시 단일 예상 가격 숨김 |
| Cold 문구 | 정확 감정가/판매 보장 표현 없음 |
| 계산 설명 | 사용자용 설명과 내부 JSON 모두 제공 |
| 예측 이벤트 저장 | prediction_id로 입력/피처/결과 재조회 가능 |
| 실제 판매가 피드백 | prediction_id와 연결 저장 |
| 학습 후보 승격 | 검수 전 데이터 학습 반영 금지 |
| 로컬 프론트 | `/test/v0.2`에서 작가 매칭부터 피드백까지 테스트 가능 |

## 24. 요약

```text
v0.2 가격 예측 API는 v0.1의 작가명 기반 매칭 구조를 유지하면서,
Warm/Cold 라우팅 기준을 수치화하고,
Cold에서도 최소 입력이 충족되면 참고용 예상 가격을 보여줄 수 있게 확장한 버전입니다.

예측 결과에는 단순 가격만 제공하지 않고,
어떤 입력과 모델 구성으로 계산됐는지,
어떤 정보가 부족한지,
실제 판매가를 입력하면 향후 모델 개선에 어떻게 연결되는지를 함께 제공합니다.

또한 실제 판매가는 바로 학습에 넣지 않고,
예측 당시 입력·피처·모델 버전과 연결해 저장한 뒤
운영 검수와 품질 점수를 통과한 데이터만 다음 재학습 후보로 사용합니다.
```
