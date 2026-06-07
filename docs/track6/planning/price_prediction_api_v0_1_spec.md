# 가격 예측 API v0.1 명세

- 작성일: 2026-06-04
- 기준 모델: `price_prediction_v0.1`
- 목적: 서비스에서 가격 예측 모델을 안정적으로 호출하고, 화면에 필요한 예측 가격/범위/신뢰도/1차 시장 가격 카드 정보를 제공
- 문서 형태: 사람이 읽는 Markdown 명세 + 개발자가 사용할 OpenAPI 명세 병행
- OpenAPI 파일: `docs/track6/planning/openapi_price_prediction_v0_1.yaml`

## 1. API 설계 원칙

- 1차 MVP에 필요한 API만 정의
- 모델 내부 실험명은 응답에 노출하지 않음
- 작가 매핑을 먼저 안정화한 뒤 가격 예측을 수행
- 예측 가격만 제공하지 않고 가격 범위, 신뢰도, warning, 1차 시장 가격 카드까지 함께 제공
- Cold 예측은 확정 가격처럼 보이지 않도록 참고 가격/범위 중심으로 반환
- 별도 API로 쪼갤 필요가 없는 화면 정보는 `price-estimate` 응답에 포함
- 운영 DB/검수 정책이 확정되지 않은 API는 미리 만들지 않음

## 2. 1차 MVP API

| 우선순위 | Method | Endpoint | 목적 | 포함 여부 |
|---:|---|---|---|---|
| 1 | `GET` | `/price-models/current` | 현재 모델 버전/기준 확인 | 1차 |
| 2 | `POST` | `/artists:resolve` | 작가명 후보 검색, 동명이인 구분, artist_key 확정 | 1차 |
| 3 | `POST` | `/artworks/price-estimate` | 단일 작품 가격 예측 | 1차 |

## 3. 2차 후보 API

| Method | Endpoint | 목적 | 2차로 미루는 이유 |
|---|---|---|---|
| `GET` | `/artists:search?q={query}` | 작가명 입력창 실시간 자동완성 | 1차는 `/artists:resolve`로 입력 완료 후 후보 선택 처리 가능 |
| `POST` | `/artworks/price-estimates:batch` | 대량 예측 | 실제 대량 처리량/CSV 업로드 정책 확정 후 구현 |
| `POST` | `/artworks/price-feedback` | 실제 판매가/운영 검수 결과 저장 | 운영 DB와 검수 상태 정책 확정 후 구현 |

## 4. 이번 문서에서 제외한 API

| 제외 API | 제외 이유 |
|---|---|
| `POST /artworks/market-price-card` | 1차 시장 가격 카드는 `price-estimate` 응답에 포함하면 충분 |
| `POST /artworks/comparable-stats` | 예측 없이 통계만 조회하는 화면 요구가 확정되지 않음 |
| `POST /artworks/price-estimate:validate-input` | 입력 검증은 `price-estimate`의 error/warning으로 처리 가능 |
| `GET /price-estimates/{estimate_id}` | 예측 이력 DB 설계 후 결정 |
| `POST /price-estimates/{estimate_id}/override` | 운영자 수동 조정 정책 확정 후 결정 |
| 비동기 batch job API | 처리 시간이 실제로 길어지는 경우에만 필요 |

## 5. v0.1 모델 기준

### 5.1 Warm / Cold 정의

| 구분 | 의미 | 서비스 표시 |
|---|---|---|
| Warm | `artist_key`가 확정되고 v0.1 학습 작가 목록에 있으며, 유효 가격 표본 수가 Warm route 정책을 만족하는 경우 | 예측 가격과 가격 범위를 함께 표시 |
| Cold | `artist_key`는 확정됐지만 v0.1 학습 작가 목록 미포함, 또는 유효 가격 표본 수가 부족한 경우 | 참고 가격/넓은 범위/낮은 신뢰도 중심으로 표시 |

작가 미확정 처리:

- 작가 매핑 실패, 동명이인 후보, 미검수 alias는 Cold로 바로 보내지 않음
- `ARTIST_NOT_RESOLVED`, `ARTIST_AMBIGUOUS`, `ARTIST_REVIEW_REQUIRED` warning을 반환하고 후보 선택/검수 흐름으로 분리
- 가격 예측 API는 가능하면 확정된 `artist_key`를 받은 뒤 호출

### 5.2 v0.1 기준 모델

| 구분 | 기준 | 표시 정책 |
|---|---|---|
| Warm | 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% 결합 | 예측 가격, 가격 범위, 유사 작품 기반 통계 제공 |
| Cold | LightGBM Quantile 기반 기준 후보 | 단일 확정가보다 참고 가격 범위 중심 제공 |

### 5.3 환율 기준

v0.1 평가 파일에서 확인된 환산 기준은 아래와 같다.

| 통화 | 원화 환산 |
|---|---:|
| USD | 1,380 KRW |
| EUR | 1,530 KRW |
| GBP | 1,780 KRW |
| HKD | 178 KRW |
| JPY | 9.5 KRW |

v0.1에서는 위 고정 환율 기준을 사용한다.

- 가격 이력 저장 시 원문 통화와 원화 환산가를 함께 저장
- 예측 API 응답의 기본 통화는 KRW
- v0.1 고정 환율도 `exchange_rate` 스냅샷으로 저장해 재현 가능하게 관리
- 실시간 환율 자동 갱신은 v0.2 이후 별도 검토

### 5.4 가격 계산 방식

v0.1 모델은 내부적으로 원화 가격의 로그값을 예측한다.

```text
ln_price_krw = log(price_krw)
pred_price_krw = exp(pred_log_price)
```

Warm 계산:

```text
warm_pred_log =
  0.70 * 유사_작품_기반_가격_피처_후보_log
+ 0.30 * 오차_안정화_후보_log

warm_pred_price_krw = exp(warm_pred_log)
```

Cold 계산:

```text
cold_q10_log, cold_q50_log, cold_q90_log = LightGBM Quantile 예측값
quantile_width = cold_q90_log - cold_q10_log
cold_pred_log = cold_q50_log + quantile_width_based_correction
cold_pred_price_krw = exp(cold_pred_log)
```

호당가 계산:

```text
estimated_ho = 실험과 동일한 F형 캔버스 면적표 기준 환산 호수
unit_price_per_ho = price_krw / estimated_ho
```

v0.1에서는 호수 환산과 호당가 계산을 기존 실험 기준으로 고정한다.

## 6. 공통 규칙

### 6.1 Base URL

```text
https://api.example.com/api/v1
```

### 6.2 인증

```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 6.3 공통 응답 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `request_id` | string | 요청 추적용 ID |
| `status` | string | `success`, `partial_success`, `failed` |
| `created_at` | string | 응답 생성 시각 |
| `model_version` | string | 모델 버전. 모델 관련 API에서 제공 |

### 6.4 confidence 표기

v0.1에서는 숫자 confidence score를 API 표준 필드로 두지 않는다.

- 이유: 점수 산식이 아직 서비스 정책으로 확정되지 않음
- 대신 `level`과 `reason_codes`를 제공
- 화면에서는 `high`, `medium`, `low`를 사용

```json
{
  "confidence": {
    "level": "medium",
    "reason_codes": [
      "WARM_ARTIST_MATCHED",
      "LOW_SIMILAR_SAMPLE_COUNT"
    ]
  }
}
```

## 7. API 1: 모델 버전 조회

### 7.1 Endpoint

```http
GET /price-models/current
```

### 7.2 목적

- 현재 서비스가 사용하는 모델 버전 확인
- Warm/Cold 표시 정책 확인
- 환율 기준 확인

### 7.3 Response 예시

```json
{
  "request_id": "req_20260604_000001",
  "status": "success",
  "created_at": "2026-06-04T18:30:00+09:00",
  "model_version": "price_prediction_v0.1",
  "model_status": "active",
  "display_policy": {
    "warm": "price_with_range",
    "cold": "reference_range_only"
  },
  "exchange_rates": {
    "base_currency": "KRW",
    "USD": 1380,
    "EUR": 1530,
    "GBP": 1780,
    "HKD": 178,
    "JPY": 9.5
  }
}
```

## 8. API 2: 작가 매핑

### 8.1 Endpoint

```http
POST /artists:resolve
```

### 8.2 목적

- 서비스 입력값의 작가명을 모델에서 사용하는 `artist_key`로 매핑
- 동명이인 또는 유사 작가명 후보를 반환
- 가격 예측 전에 Warm/Cold 판단 가능성을 확인
- 한글/영문/로마자/원천별 작가명 표기 차이를 `artist_alias` 기준으로 흡수
- 서비스 작가명 입력창에서 후보 선택 모달을 띄우기 위한 정보를 반환

### 8.3 Request 예시

```json
{
  "artist": {
    "artist_key": null,
    "name_ko": "박서보",
    "name_en": "Park Seo-Bo"
  },
  "options": {
    "max_candidates": 5
  }
}
```

### 8.4 Response 예시

```json
{
  "request_id": "req_20260604_000002",
  "status": "success",
  "created_at": "2026-06-04T18:31:00+09:00",
  "model_version": "price_prediction_v0.1",
  "resolved": true,
  "requires_selection": false,
  "selected_artist": {
    "artist_key": "park-seobo",
    "name_ko": "박서보",
    "name_en": "Park Seo-Bo",
    "birth_year": 1931,
    "nationality": "Korea",
    "entity_suffix": null,
    "match_status": "exact",
    "matched_alias": "박서보",
    "match_basis": "verified_ko_name",
    "review_required": false,
    "warm_available": true,
    "valid_training_label_count": 24,
    "route_recommendation": "warm"
  },
  "candidates": [
    {
      "artist_key": "park-seobo",
      "name_ko": "박서보",
      "name_en": "Park Seo-Bo",
      "birth_year": 1931,
      "nationality": "Korea",
      "entity_suffix": null,
      "match_status": "exact",
      "matched_alias": "박서보",
      "match_basis": "verified_ko_name",
      "review_required": false,
      "warm_available": true,
      "valid_training_label_count": 24,
      "route_recommendation": "warm"
    }
  ],
  "warnings": []
}
```

### 8.5 동명이인 후보 선택 응답 예시

서비스에서 작가명 입력 후 후보가 여러 명이면 `requires_selection=true`로 반환한다. 이 경우 프론트는 후보 선택 창을 띄우고, 사용자가 선택한 `artist_key`를 가격 예측 API에 전달한다.

```json
{
  "request_id": "req_20260604_000002",
  "status": "partial_success",
  "created_at": "2026-06-04T18:31:00+09:00",
  "model_version": "price_prediction_v0.1",
  "resolved": false,
  "requires_selection": true,
  "selected_artist": null,
  "candidates": [
    {
      "artist_key": "kim-minjun-1978-kr",
      "name_ko": "김민준",
      "name_en": "Kim Min-Jun",
      "birth_year": 1978,
      "nationality": "Korea",
      "entity_suffix": "1978-kr",
      "match_status": "alias",
      "matched_alias": "Kim Minjun",
      "match_basis": "romanized_alias",
      "review_required": false,
      "warm_available": true,
      "valid_training_label_count": 12,
      "route_recommendation": "warm"
    },
    {
      "artist_key": "kim-minjun-1986-kr",
      "name_ko": "김민준",
      "name_en": "Kim Min-Jun",
      "birth_year": 1986,
      "nationality": "Korea",
      "entity_suffix": "1986-kr",
      "match_status": "alias",
      "matched_alias": "Kim Minjun",
      "match_basis": "romanized_alias",
      "review_required": true,
      "warm_available": false,
      "valid_training_label_count": 0,
      "route_recommendation": "review_required"
    }
  ],
  "warnings": [
    {
      "code": "ARTIST_AMBIGUOUS",
      "severity": "warning",
      "message": "유사한 작가 후보가 2명 이상입니다. 작가를 선택한 뒤 가격 예측을 진행해야 합니다."
    }
  ]
}
```

### 8.6 작가 매핑 정책

- 서비스 입력 단계에서 가능하면 `artist_key`를 확정해서 가격 예측 API에 전달
- 작가명 자유 입력만으로 가격 예측을 바로 호출하지 않는 것을 권장
- 한글명, 영문명, 로마자 표기, 하이픈/띄어쓰기 변형은 `artist_alias` 기준으로 매칭
- `matched_alias`는 실제로 매칭된 표기값
- `match_basis`는 매칭 근거. 예: `verified_ko_name`, `verified_en_alias`, `romanized_alias`, `fuzzy_name`
- `review_required=true`이면 가격 예측 전 사용자 또는 운영자 선택을 권장
- `requires_selection=true`이면 프론트에서 후보 선택 창을 띄움
- 후보 구분에는 `name_ko`, `name_en`, `birth_year`, `nationality`, `entity_suffix`, `matched_alias`를 사용
- 후보가 2개 이상이면 프론트에서 사용자가 작가를 선택하게 함
- 매칭 실패 시 Cold로 바로 보내기보다 `ARTIST_NOT_RESOLVED` warning을 먼저 제공
- `warm_available=true`는 작가 목록 포함 여부뿐 아니라 v0.1 route 정책상 최소 표본 기준을 만족했음을 의미
- 자동 확정은 검수된 alias와 단일 후보가 동시에 만족될 때만 허용

## 9. API 3: 단일 작품 가격 예측

### 9.1 Endpoint

```http
POST /artworks/price-estimate
```

### 9.2 목적

- 작품 1건의 가격 예측
- 서비스 화면에 필요한 예측 가격, 가격 범위, 신뢰도, 1차 시장 가격 카드, warning 반환

### 9.3 Request 예시

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
    }
  },
  "options": {
    "currency": "KRW",
    "include_comparable_samples": true,
    "max_comparable_samples": 10
  }
}
```

### 9.4 Request 필드 정책

| 필드 | 정책 |
|---|---|
| `artist.artist_key` | 강력 권장. 없으면 `/artists:resolve`로 먼저 확정하는 것을 권장 |
| `artist.name_ko` / `artist.name_en` | 작가키가 없을 때 보조 매칭에 사용. 후보가 확정되지 않으면 가격 예측 대신 warning 반환 |
| `width_cm`, `height_cm` | 가격 예측에 중요. 누락 시 warning 또는 error |
| `depth_cm` | 입체 작품/깊이 보조 판단 |
| `medium_category` | 재료 대분류 |
| `support_category` | 지지체 대분류 |
| `include_comparable_samples` | 유사 작품 목록 포함 여부 |

### 9.5 Response 예시

```json
{
  "request_id": "req_20260604_000003",
  "status": "success",
  "created_at": "2026-06-04T18:32:00+09:00",
  "model_version": "price_prediction_v0.1",
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
      "reason_codes": [
        "WARM_ARTIST_MATCHED",
        "LOW_SIMILAR_SAMPLE_COUNT"
      ]
    }
  },
  "routing": {
    "artist_matched": true,
    "matched_artist_key": "park-seobo",
    "valid_training_label_count": 24,
    "route_policy": "warm_min_label_count",
    "route_reason": "작가키가 확정됐고 v0.1 Warm route 정책의 유효 표본 기준을 만족해 Warm route 적용"
  },
  "basis": {
    "similar_group_level": "artist_size",
    "similar_sample_count": 8,
    "similar_coverage_tier": "low_n",
    "similar_price_median_krw": 19854740,
    "similar_price_q25_krw": 11868000,
    "similar_price_q75_krw": 32640000
  },
  "market_price_card": {
    "title": "1차 시장 가격",
    "metric_label": "호당가 중앙값",
    "median_krw_per_ho": 350000,
    "median_display": "35만원/호",
    "range_krw_per_ho": {
      "low": 280000,
      "high": 460000
    },
    "range_display": "28만 - 46만원/호",
    "medium_distribution": [
      {
        "label": "회화",
        "medium_group": "painting",
        "median_krw_per_ho": 330000,
        "display": "33만",
        "sample_count": 16
      },
      {
        "label": "드로잉",
        "medium_group": "drawing",
        "median_krw_per_ho": 280000,
        "display": "28만",
        "sample_count": 8
      }
    ],
    "sample_count": 24,
    "sample_count_display": "표본 수 N=24건"
  },
  "comparable_samples": [
    {
      "artwork_id": "sample_001",
      "title": "Ecriture No.040412",
      "artist_name": "Park Seo-Bo",
      "sale_price_krw": 165600000,
      "width_cm": 45.5,
      "height_cm": 52.7,
      "medium_category": "other",
      "support_category": "paper",
      "similarity_reason": "same_artist_same_support"
    }
  ],
  "warnings": [
    {
      "code": "LOW_SIMILAR_SAMPLE_COUNT",
      "severity": "warning",
      "message": "유사 작품 표본 수가 적어 가격 범위를 넓게 해석해야 합니다."
    }
  ]
}
```

## 10. 1차 시장 가격 카드

서비스 화면에서 아래 카드 형태가 필요하면 `market_price_card`를 그대로 사용한다.

```text
1차 시장 가격

호당가 중앙값
35만원/호

범위 28만 - 46만원/호

매체별 분포
회화 33만    드로잉 28만

표본 수 N=24건
```

### 10.1 카드 필드 매핑

| 화면 문구 | API 필드 | 생성 기준 |
|---|---|---|
| `1차 시장 가격` | `market_price_card.title` | 카드 제목 |
| `호당가 중앙값` | `market_price_card.metric_label` | 대표 지표명 |
| `35만원/호` | `market_price_card.median_display` | 유사 작품 표본의 호당가 중앙값 |
| `범위 28만 - 46만원/호` | `market_price_card.range_display` | 유사 작품 표본의 호당가 분위 범위 |
| `회화 33만` | `market_price_card.medium_distribution[].display` | 매체 그룹별 호당가 중앙값 |
| `표본 수 N=24건` | `market_price_card.sample_count_display` | 통계 계산에 사용한 유효 표본 수 |

### 10.2 카드 표시 정책

- 이 카드는 개별 작품 예측가가 아니라 유사 작품 묶음의 시장 기준 통계
- `N`이 작으면 `LOW_SIMILAR_SAMPLE_COUNT` warning을 함께 표시
- Warm은 같은 작가 기반 통계를 우선 사용
- Cold는 같은 작가 기준이 약하므로 작품 조건/작가 메타 기반 유사 그룹 통계를 사용하되, 낮은 신뢰도/넓은 범위 중심으로 표시
- 호당가 계산 공식은 서비스 공통 유틸로 고정

## 11. Warning Code

| 코드 | 의미 | 화면 표시 |
|---|---|---|
| `WARM_ARTIST_MATCHED` | 같은 작가 학습 이력과 Warm route 최소 표본 기준 충족 | 신뢰도 보조 사유 |
| `COLD_ARTIST` | 학습 작가 목록 미포함 또는 Warm route 기준 미충족 | 참고 가격/범위 중심 표시 |
| `ARTIST_NOT_RESOLVED` | 작가 매핑 실패 또는 불확실 | 작가 선택 요청 |
| `ARTIST_AMBIGUOUS` | 동일하거나 유사한 작가 후보가 2명 이상 | 후보 선택 요청 |
| `ARTIST_REVIEW_REQUIRED` | 미검수 alias 또는 낮은 매칭 확신도 | 운영자 검수 권장 |
| `LOW_WARM_TRAINING_LABEL_COUNT` | 같은 작가가 있으나 유효 가격 표본 수 부족 | Cold 방식의 넓은 범위 또는 낮은 신뢰도 표시 |
| `LOW_SIMILAR_SAMPLE_COUNT` | 유사 작품 표본 수 부족 | 가격 범위 넓게 표시 |
| `GLOBAL_FALLBACK_USED` | 유사 작품 묶음 실패로 전체 fallback 사용 | 신뢰도 낮음 |
| `SEARCH_QUALITY_LOW` | 외부 검색 스냅샷의 미술 문맥/신뢰 도메인 품질이 낮음 | 신뢰도 하향 또는 수동 검수 권장 |
| `SEARCH_HOMONYM_RISK` | 검색 결과에서 동명이인 또는 무관 인물 위험이 큼 | 후보 선택/운영 검수 권장 |
| `SEARCH_SNAPSHOT_STALE` | 서비스 신뢰도 판단에 쓰는 검색 스냅샷이 오래됨 | 최신 검색 스냅샷 갱신 권장 |
| `MISSING_DIMENSIONS` | 크기 정보 부족 | 입력 보완 요청 |
| `WIDE_PRICE_RANGE` | 예측 범위가 넓음 | 확정가 아님을 표시 |
| `HIGH_PRICE_TAIL_RISK` | 고가 작품 과소 예측 가능성 | 운영자 검수 권장 |
| `LOW_PRICE_OVER_PREDICTION_RISK` | 저가/소형 작품 과대 예측 가능성 | 운영자 검수 권장 |

## 12. Error Code

| HTTP Status | 코드 | 의미 |
|---:|---|---|
| 400 | `INVALID_REQUEST` | 요청 JSON 형식 오류 |
| 400 | `MISSING_REQUIRED_FIELD` | 필수 입력값 누락 |
| 404 | `ARTIST_NOT_FOUND` | 요청한 `artist_key`가 존재하지 않음 |
| 422 | `UNSUPPORTED_MEDIUM` | 지원하지 않는 재료/지지체 |
| 422 | `INVALID_DIMENSIONS` | 크기 값이 비정상 |
| 500 | `MODEL_INFERENCE_FAILED` | 모델 추론 실패 |
| 503 | `MODEL_UNAVAILABLE` | 모델 서버 또는 feature store 사용 불가 |

### 12.1 Error Response 예시

```json
{
  "request_id": "req_20260604_000004",
  "status": "failed",
  "created_at": "2026-06-04T18:35:00+09:00",
  "error": {
    "code": "MISSING_REQUIRED_FIELD",
    "message": "width_cm 또는 height_cm 값이 필요합니다.",
    "field": "artwork.dimensions.width_cm"
  }
}
```

## 13. 구현 우선순위

### 13.1 1차 구현

- `GET /price-models/current`
- `POST /artists:resolve`
- `POST /artworks/price-estimate`

### 13.2 2차 검토

- `POST /artworks/price-estimates:batch`
- `POST /artworks/price-feedback`

## 14. 남은 결정 사항

| 항목 | 결정 필요 내용 |
|---|---|
| 인증 방식 | 내부 API인지 외부 연동 API인지에 따라 JWT/API key 결정 |
| 실시간 환율 자동 갱신 | v0.1은 고정 환율 스냅샷을 사용하고, 실시간 운영 환율 자동 갱신은 v0.2 이후 검토 |
| 호당가 정책 변경 | v0.1은 기존 실험 기준 공식을 사용하고, 다른 호수 환산 정책은 v0.2 이후 검토 |
| 작가 매핑 UI | 자유 입력만 허용할지, 후보 선택을 강제할지 결정 |
| Cold 표시 문구 | v0.1은 참고 가격/범위 중심으로 반환하고, 실제 화면 문구는 서비스 UX에서 확정 |
| feedback API | 실제 판매가/문의가/수동 수정가를 어떻게 구분 저장할지 결정 |
