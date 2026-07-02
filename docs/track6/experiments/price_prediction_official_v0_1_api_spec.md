# 가격 예측 서비스 공식 테스트 v0.1 API 상세 명세

- 작성일: 2026-06-12
- 공식 버전: `price_prediction_v0.1`
- API prefix: `/api/v1`
- 테스트 화면: `/test/v0.1`
- 기준 문서:
  - `docs/track6/experiments/price_prediction_official_v0_1_test_plan.md`
  - `docs/track6/experiments/price_prediction_official_v0_1_db_cache_schema.md`

## 1. API 설계 원칙

- 공식 테스트 v0.1은 보고서 기준 Warm/Cold 모델을 raw 입력에서 실행하는 것을 목표로 함
- 사용자 화면에는 `Warm`, `Cold`, 내부 실험 번호를 직접 노출하지 않음
- API 내부 route는 `warm`, `cold`, `review_required`를 사용하되, 화면 표시명은 별도로 반환
- 동일 입력과 동일 DB/cache snapshot이면 같은 예측값을 반환해야 함
- 예측 응답에는 가격뿐 아니라 계산 근거, 사용 피처, route 사유, 신뢰도, 보완 입력 안내를 포함
- 예측 이벤트는 항상 저장 가능해야 함
- 실제 판매가는 검수 전 학습에 반영하지 않음

## 2. 공통 응답 규칙

### 2.1 성공 응답 공통 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `request_id` | string | API 요청 ID |
| `status` | string | `success`, `partial_success`, `failed` |
| `created_at` | string | ISO datetime |
| `service_version` | string | `price_prediction_v0.1` |

### 2.2 오류 응답

```json
{
  "request_id": "req_xxx",
  "status": "failed",
  "created_at": "2026-06-12T13:00:00+09:00",
  "service_version": "price_prediction_v0.1",
  "error": {
    "code": "MODEL_UNAVAILABLE",
    "message": "모델 또는 DB/cache를 사용할 수 없습니다."
  }
}
```

오류 코드:

| code | 의미 |
|---|---|
| `MODEL_UNAVAILABLE` | 모델 또는 artifact 로딩 실패 |
| `DB_UNAVAILABLE` | DB/cache 연결 실패 |
| `INVALID_INPUT` | 입력 형식 오류 |
| `INVALID_DIMENSIONS` | 작품 크기 오류 |
| `ARTIST_REVIEW_REQUIRED` | 작가 후보 선택 필요 |
| `MINIMUM_INPUT_FAILED` | 최소 입력 부족 |
| `PREDICTION_FAILED` | 예측 계산 실패 |

## 3. Endpoint 목록

| Method | Endpoint | 목적 |
|---|---|---|
| `GET` | `/api/v1/health` | 서비스 상태 확인 |
| `GET` | `/api/v1/price-models/current` | 현재 공식 v0.1 모델/정책 조회 |
| `POST` | `/api/v1/artists/resolve` | 작가 후보 조회와 동명이인 확인 |
| `POST` | `/api/v1/artworks/price-estimate` | 단일 작품 가격 예측 |
| `GET` | `/api/v1/predictions/{prediction_id}` | 예측 결과와 계산 과정 재조회 |
| `POST` | `/api/v1/feedback/sale-price` | 실제 판매가 피드백 저장 |
| `GET` | `/api/v1/admin/model-audit` | 운영자용 모델/피처 상태 확인 |

## 4. `GET /api/v1/health`

### 4.1 목적

API, 모델 artifact, DB/cache 로딩 상태를 확인한다.

### 4.2 Response

```json
{
  "request_id": "req_001",
  "status": "success",
  "created_at": "2026-06-12T13:00:00+09:00",
  "service_version": "price_prediction_v0.1",
  "service_loaded": true,
  "db_loaded": true,
  "warm_adapter_loaded": true,
  "cold_adapter_loaded": true,
  "search_cache_loaded": true,
  "model_registry_loaded": true
}
```

## 5. `GET /api/v1/price-models/current`

### 5.1 목적

현재 공식 v0.1에서 사용하는 route 정책, 모델 구성, DB/cache snapshot 버전을 반환한다.

### 5.2 Response

```json
{
  "request_id": "req_002",
  "status": "success",
  "created_at": "2026-06-12T13:00:00+09:00",
  "service_version": "price_prediction_v0.1",
  "model_status": "candidate",
  "routing_policy": {
    "warm_artist_match_score_min": 0.9,
    "warm_same_artist_price_count_min": 5,
    "ambiguous_artist_policy": "review_required",
    "cold_minimum_input_policy": "artist_name + width_cm + height_cm + medium + support"
  },
  "display_policy": {
    "warm": "이력 기반 예측",
    "cold": "참고 예측",
    "review_required": "확인 필요"
  },
  "artifact_versions": {
    "warm_display_name": "기준가격 기반 미세 보정 모델",
    "cold_display_name": "검색 피처 포함 참고 예측 모델",
    "artist_registry_version": "track6_train_seed_v0_1",
    "search_snapshot_version": "latest_operational_snapshot",
    "similar_stats_cache_version": "v0_1_initial"
  }
}
```

## 6. `POST /api/v1/artists/resolve`

### 6.1 목적

사용자가 입력한 한글/영문 작가명을 내부 작가 후보와 연결한다. 동명이인 위험이 있으면 단일 가격 예측을 보류하거나 후보 선택을 요구한다.

### 6.2 Request

```json
{
  "artist": {
    "name_ko": "박서보",
    "name_en": "Park Seo-Bo",
    "birth_year": 1931
  },
  "options": {
    "max_candidates": 5
  }
}
```

### 6.3 Response

```json
{
  "request_id": "req_003",
  "status": "success",
  "created_at": "2026-06-12T13:00:00+09:00",
  "service_version": "price_prediction_v0.1",
  "resolved": true,
  "requires_selection": false,
  "selected_artist": {
    "artist_key": "park-seo-bo",
    "name_ko": "박서보",
    "name_en": "Park Seo-Bo",
    "birth_year": 1931,
    "nationality": "Korean",
    "artist_match_score": 1.0,
    "homonym_risk_score": 0.0,
    "same_artist_training_price_count": 21,
    "route_recommendation": "warm",
    "display_route_recommendation": "이력 기반 예측",
    "representative_artworks": [
      {
        "title": "Ecriture",
        "sale_price_krw": 5800000,
        "width_cm": 80.3,
        "height_cm": 55.2,
        "medium_category": "mixed_media",
        "support_category": "unknown",
        "ho_size": 20
      }
    ]
  },
  "candidates": [],
  "warnings": []
}
```

### 6.4 작가 매칭 점수

```text
작가키가 직접 일치하면:
작가매칭신뢰도점수 = 1.00

그 외:
작가매칭신뢰도점수 =
  clip(
      0.70 * 이름일치점수
    + 0.20 * 보조정보일치점수
    + 0.10 * 학습작가등록점수
    - 0.15 * 동명이인위험점수
    - 0.20 * 핵심정보충돌점수,
    0.00,
    0.95
  )
```

## 7. `POST /api/v1/artworks/price-estimate`

### 7.1 목적

단일 작품 가격을 예측한다. 입력값과 작가 매칭 결과에 따라 이력 기반 예측 또는 참고 예측으로 route를 결정한다.

### 7.2 Request

```json
{
  "artwork": {
    "artist": {
      "name_ko": "박서보",
      "name_en": "Park Seo-Bo",
      "selected_artist_key": "park-seo-bo"
    },
    "title": "Untitled",
    "year": 2020,
    "category": "Painting",
    "dimensions": {
      "width_cm": 72.7,
      "height_cm": 60.6,
      "depth_cm": 0
    },
    "medium": {
      "medium_category": "painting",
      "support_category": "canvas"
    }
  },
  "options": {
    "currency": "KRW",
    "include_comparable_samples": true,
    "max_comparable_samples": 10,
    "include_calculation_steps": true,
    "include_debug_fields": false
  }
}
```

### 7.3 Response 공통 구조

```json
{
  "request_id": "req_004",
  "status": "success",
  "created_at": "2026-06-12T13:00:00+09:00",
  "service_version": "price_prediction_v0.1",
  "prediction_id": "pred_abc",
  "route": "warm",
  "display_route": "이력 기반 예측",
  "prediction": {
    "price_krw": 13280000,
    "price_display": "1,328만원",
    "range_krw": {
      "low": 4360000,
      "mid": 13280000,
      "high": 15820000
    },
    "range_display": "436만원 - 1,582만원",
    "confidence": {
      "level": "medium",
      "score": 0.62,
      "reason_codes": [
        "ARTIST_MATCHED",
        "SIMILAR_PRICE_HISTORY_USED"
      ]
    }
  },
  "routing": {
    "artist_matched": true,
    "matched_artist_key": "park-seo-bo",
    "artist_match_score": 1.0,
    "homonym_risk_score": 0.0,
    "same_artist_training_price_count": 21,
    "route_policy": "artist_match_score >= 0.90 AND same_artist_training_price_count >= 5",
    "route_reason": "같은 작가 가격 이력이 충분해 이력 기반 예측을 적용했습니다."
  },
  "input_quality": {
    "minimum_input_status": "passed",
    "missing_required_fields": [],
    "missing_recommended_fields": [],
    "confidence_penalty_reasons": []
  },
  "calculation_summary": {
    "user_facing_formula": "예측가격 = 기준가격 + 보정값",
    "explanation": "같은 작가 가격 이력과 유사작품 통계로 기준가격을 만든 뒤, 방향성과 위험도가 확인된 경우만 미세 보정했습니다.",
    "steps": []
  },
  "market_reference": {},
  "similar_artworks": [],
  "similar_artists": [],
  "feedback": {
    "can_submit_actual_sale_price": true,
    "feedback_endpoint": "/api/v1/feedback/sale-price"
  },
  "warnings": []
}
```

## 8. 이력 기반 예측 응답 상세

이력 기반 예측은 같은 작가 이력과 유사작품 통계가 충분할 때 적용된다.

### 8.1 계산 단계 예시

```json
{
  "calculation_summary": {
    "route": "warm",
    "display_route": "이력 기반 예측",
    "user_facing_formula": "예측가격 = 기준가격 + 미세보정값",
    "steps": [
      {
        "step_order": 1,
        "name": "기준가격 생성",
        "role": "같은 작가 가격 이력과 유사작품 통계를 기반으로 미세보정 전 기준가격을 계산",
        "formula": "기준로그가격 = Warm_기준가격생성기(작품피처 + 작가피처 + 유사작품통계)",
        "display_output": {
          "base_price_display": "1,327만원"
        }
      },
      {
        "step_order": 2,
        "name": "방향 확률 계산",
        "role": "기준가격보다 실제 가격이 높을 가능성을 계산",
        "formula": "방향확신도 = abs(기준가격보다_높을확률 - 0.5) * 2"
      },
      {
        "step_order": 3,
        "name": "Huber 잔차 미세 보정",
        "role": "이상치에 덜 흔들리는 잔차 모델로 보정 후보를 계산",
        "formula": "원시보정로그값 = Huber잔차 * 방향일치여부 * 보정적용강도 * 0.025"
      },
      {
        "step_order": 4,
        "name": "위험도 기반 보정 상한",
        "role": "불확실성이 높은 row는 보정폭을 줄임",
        "formula": "보정상한 = 방향별기본상한 * (1 - 0.55 * 가격범위폭순위) * (1 - 0.80 * row위험도)"
      },
      {
        "step_order": 5,
        "name": "최종 가격 변환",
        "role": "로그가격을 원화 가격으로 변환",
        "formula": "최종가격 = exp(기준로그가격 + 적용보정로그값)"
      }
    ]
  }
}
```

## 9. 참고 예측 응답 상세

참고 예측은 같은 작가 이력이 부족하거나 작가 매칭 신뢰도가 부족할 때 적용된다.

### 9.1 계산 단계 예시

```json
{
  "calculation_summary": {
    "route": "cold",
    "display_route": "참고 예측",
    "user_facing_formula": "참고가격 = 검색 피처 포함 대표가격 + 과대예측 방어 + 작가 검색 보정",
    "steps": [
      {
        "step_order": 1,
        "name": "검색 피처 조회",
        "role": "작가명 검색 snapshot에서 미술 문맥, 전시 문맥, 검색 품질 점수를 조회",
        "formula": "검색피처 = artist_search_feature_snapshots[artist_key 또는 작가명]"
      },
      {
        "step_order": 2,
        "name": "가격 범위 예측",
        "role": "LightGBM Quantile 모델이 여러 가능 가격 구간을 계산",
        "formula": "q10, q40, q50, q90 = LightGBM_Quantile(작품피처 + 작가메타 + 검색피처)"
      },
      {
        "step_order": 3,
        "name": "과대예측 방어",
        "role": "불확실성이 크고 낮은쪽 가격과 차이가 큰 경우 대표가격을 낮은쪽 40% 가격 방향으로 조정",
        "formula": "조건 충족 시 방어로그가격 = 0.50 * 대표로그가격 + 0.50 * 낮은쪽40퍼센트로그가격"
      },
      {
        "step_order": 4,
        "name": "작가 검색 보정",
        "role": "작가별 검색 문맥에서 검증된 보정값을 적용",
        "formula": "최종로그가격 = 방어로그가격 + 작가검색보정값"
      },
      {
        "step_order": 5,
        "name": "최종 가격 변환",
        "role": "로그가격을 원화 가격으로 변환",
        "formula": "최종가격 = exp(최종로그가격)"
      }
    ]
  }
}
```

## 10. 유사작품/유사작가 응답

### 10.1 유사작품

```json
{
  "similar_artworks": [
    {
      "title": "Ecriture",
      "artist_name": "박서보",
      "sale_price_krw": 5800000,
      "price_display": "580만원",
      "width_cm": 80.3,
      "height_cm": 55.2,
      "ho_size": 20,
      "medium_category": "mixed_media",
      "support_category": "unknown",
      "similarity_tier": "strong",
      "similarity_reason": "같은 작가 + 비슷한 크기"
    }
  ]
}
```

### 10.2 유사작가

```json
{
  "similar_artists": [
    {
      "artist_key": "candidate-artist",
      "name_ko": "유사 작가",
      "birth_year": 1935,
      "nationality": "Korean",
      "similarity_score": 0.72,
      "price_history_count": 18,
      "match_reasons": [
        "국적 유사",
        "생년대 유사",
        "주 사용 재료 유사"
      ]
    }
  ]
}
```

## 11. `GET /api/v1/predictions/{prediction_id}`

예측 저장 결과와 계산 단계를 다시 조회한다.

```json
{
  "request_id": "req_005",
  "status": "success",
  "created_at": "2026-06-12T13:00:00+09:00",
  "service_version": "price_prediction_v0.1",
  "prediction_id": "pred_abc",
  "prediction_event": {},
  "feature_snapshot": {},
  "calculation_steps": []
}
```

## 12. `POST /api/v1/feedback/sale-price`

### 12.1 목적

예측 후 실제 판매가를 저장한다. 검수 전에는 학습에 반영하지 않는다.

### 12.2 Request

```json
{
  "prediction_id": "pred_abc",
  "actual_sale_price_krw": 12000000,
  "sale_date": "2026-06-12",
  "sale_channel": "gallery",
  "evidence_status": "partial",
  "consent_for_training": true,
  "note": "검수자가 확인한 메모"
}
```

### 12.3 Response

```json
{
  "request_id": "req_006",
  "status": "success",
  "created_at": "2026-06-12T13:00:00+09:00",
  "service_version": "price_prediction_v0.1",
  "accepted": true,
  "review_status": "needs_review",
  "message": "실제 판매가 피드백을 저장했습니다. 검수 승인 후 학습 후보로 승격할 수 있습니다."
}
```

## 13. `GET /api/v1/admin/model-audit`

운영자용 endpoint다. 모델과 DB/cache 준비 상태를 확인한다.

```json
{
  "request_id": "req_007",
  "status": "success",
  "created_at": "2026-06-12T13:00:00+09:00",
  "service_version": "price_prediction_v0.1",
  "checks": {
    "artist_registry_rows": 1000,
    "price_observation_rows": 10000,
    "search_snapshot_rows": 372,
    "similar_stats_rows": 5000,
    "warm_adapter_ready": false,
    "cold_adapter_ready": false,
    "fixed_test_parity_checked": false,
    "deterministic_repeat_checked": false
  }
}
```

## 14. 저장 정책

가격 예측 API 호출이 성공하면 아래 테이블에 저장한다.

```text
prediction_events
prediction_calculation_steps
warm_feature_snapshots 또는 cold_feature_snapshots
```

저장 실패 시 정책:

| 상황 | API 응답 |
|---|---|
| 예측은 성공, 저장 실패 | `partial_success`, 가격 표시 가능, warning 포함 |
| 예측 실패 | `failed`, 가격 표시 불가 |
| 작가 확인 필요 | `partial_success`, 단일 가격 표시 보류 |
| 최소 입력 부족 | `partial_success`, 단일 가격 표시 보류 |

## 15. 공식 v0.1 완료 기준

```text
API 완료 =
  (작가명으로 후보 조회 가능)
  AND (작가 후보 선택 후 예측 가능)
  AND (이력 기반 예측과 참고 예측 route가 모두 동작)
  AND (계산 단계가 응답에 포함)
  AND (예측 이벤트가 DB에 저장)
  AND (동일 입력 반복 결과가 동일)
  AND (fixed-test parity 검증 결과를 admin audit에서 확인 가능)
```

