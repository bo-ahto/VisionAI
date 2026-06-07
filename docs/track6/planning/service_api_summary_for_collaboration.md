# Track6 가격 예측 서비스 API 초안

- 작성일: 2026-06-03
- 문서 목적: 협업자가 실제 서비스 연동 전에 API 요청값, 응답값, Warm/Cold 처리 방식, 가격 범위, 비교군 통계, 신뢰도 표시 방식을 이해할 수 있게 정리한다.
- 전제:
  - 이 문서는 신규 Track6 서비스 API 초안이다.
  - 기존 셀프 테스트용 API와는 분리한다.
  - path, 필드명, 응답 구조는 협업 과정에서 조정 가능하지만, API가 전달해야 하는 정보의 범위는 이 문서를 기준으로 한다.
  - 최신 실험 기준은 `PP-SVC3`, `PP-SVC4`, `latest_experiment_result_synthesis.md`다.

## 1. 현재 결론

| 구분 | 현재 서비스 적용 판단 |
|---|---|
| Warm 점 예측 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`을 1순위 후보로 사용 |
| Warm 검증 근거 | `PP-SVC4` 반복 holdout에서 `mape_guarded` 기준 안정적으로 재선택 |
| Cold 점 예측 | 아직 Warm 수준의 서비스 대표 모델로 보기 어려움 |
| Cold 서비스 방향 | 단일 가격보다 참고 예측가, 넓은 범위, 낮은 신뢰도, 비교군 통계 중심 |
| 비교군 통계 | API 응답에 반드시 포함할 서비스 설명값으로 관리 |
| 외부 검색/수집 | 실시간 기본값은 비활성화하고, 별도 수집/캐시 기반으로 운영하는 방향 권장 |

## 2. API가 제공해야 하는 기능

Track6 가격 예측 API는 작품 정보를 입력받아 아래 값을 반환한다.

- 예측 가격
- 예측 가격 범위
- 신뢰도 등급
- Warm/Cold 판단 결과
- 사용된 모델 정책
- 적용된 후처리 정책
- 비교군 통계
- 작가 이력 또는 유사 작품 참고 정보
- 화면 표시 정책

서비스 화면에서는 단일 가격만 보여주는 것이 아니라, 예측 가격과 함께 신뢰도 및 가격 범위를 같이 보여주는 것을 기본 방향으로 한다.

## 3. Warm / Cold 처리 기준

| 구분 | 의미 | API 처리 방향 | 화면 표시 방향 |
|---|---|---|---|
| Warm | 학습 데이터에 같은 작가가 존재하는 경우 | 검증 완료된 Warm 결합 후보 사용 | 예측 가격을 중심으로 보여주되 가격 범위와 비교군 통계도 함께 표시 |
| Cold | 학습 데이터에 같은 작가가 없거나 매칭이 불확실한 경우 | 작품 정보와 보조 피처 기반 Cold 후보 사용 | 단일 가격보다 참고 예측가, 넓은 가격 범위, 낮은 신뢰도 표시 |

### Warm 기준

- 작가명이 학습 작가 목록과 안정적으로 매칭되면 Warm으로 처리한다.
- Warm은 기존 작가의 가격대 정보를 활용할 수 있으므로 Cold보다 예측 신뢰도가 높다.
- 최신 실험 기준 Warm 운영 후보:
  - `model_policy`: `warm_pp_svc3_svcnum_ppv8_070`
  - 내부 의미: `svc_numeric_seed_mean 70% + PP-V8 30%`
  - 고정 test 성능: MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`
  - 반복 검증: `PP-SVC4`에서 `mape_guarded` 기준 `wsvc=0.70`이 row holdout 109/200회, artist holdout 91/200회 선택

### Warm 예측 계산 방식

Warm 최종 예측은 로그 가격 스케일에서 결합한다.

```text
pred_log_final = 0.70 * pred_log_svc_numeric + 0.30 * pred_log_pp_v8
price_krw = exp(pred_log_final)
```

- `pred_log_svc_numeric`: 비교군 통계 피처를 포함한 Warm Huber 계열 후보의 예측값
- `pred_log_pp_v8`: 기존 Warm 후보 중 MAPE와 p95 방어가 좋았던 compact blend 후보의 예측값
- 로그 가격에서 결합하는 이유:
  - 가격 데이터는 고가 작품 때문에 분포가 크게 치우친다.
  - 로그 가격에서 평균/결합을 하면 극단 고가 작품의 영향이 줄어든다.
  - 최종 표시 가격은 다시 원화 가격으로 변환한다.

### Cold 기준

- 작가명이 학습 작가 목록에 없거나 매칭이 불확실하면 Cold로 처리한다.
- Cold는 작가 기준선을 직접 사용할 수 없으므로 예측 오차가 더 크다.
- 현재 실험 기준 Cold는 다음처럼 다룬다.
  - 점 예측 후보: `PP-Y2` 기준선 및 `PP-Y18/PP-Y21` 검증 후보를 내부 비교 대상으로 유지
  - 서비스 표시는 단일 확정 가격보다 참고 예측가와 넓은 범위 중심
  - CatBoost/LightGBM/Quantile 계열 결과는 신뢰도, 위험 구간, 가격 범위 보정에 우선 활용

## 4. 엔드포인트 초안

| 구분 | Method | Path | 용도 | 우선순위 |
|---|---|---|---|---|
| 헬스체크 | GET | `/api/track6/health` | 서버 상태 확인 | 필수 |
| 모델 정보 | GET | `/api/track6/model-info` | 모델 버전, 정책, 성능 요약 확인 | 필수 |
| 단건 예측 | POST | `/api/track6/price-estimate` | 작품 1건 가격 예측 | 필수 |
| 배치 예측 | POST | `/api/track6/price-estimate/batch` | 작품 여러 건 가격 예측 | 선택 |
| 모니터링 | GET | `/api/track6/monitor` | 예측 건수, Warm/Cold 비율, 신뢰도 분포 확인 | 운영 필수 |

## 5. 단건 예측 API

### 5.1 요청

`POST /api/track6/price-estimate`

```json
{
  "artist": {
    "name": "김OO",
    "artist_key": null
  },
  "artwork": {
    "title": "Untitled",
    "width_cm": 72.7,
    "height_cm": 60.6,
    "depth_cm": null,
    "medium": "oil on canvas",
    "support": "canvas",
    "year_made": 2022
  },
  "market_context": {
    "target_market": "gallery",
    "currency": "KRW"
  },
  "options": {
    "include_comparable_stats": true,
    "include_explanation": true,
    "external_lookup_enabled": false
  },
  "artist_profile": {
    "birth_year": null,
    "total_works": null,
    "followers": null,
    "solo_count": null,
    "group_count": null
  }
}
```

### 5.2 필수 입력값

| 필드 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| `artist.name` | string | 예 | 작가명 |
| `artwork.width_cm` | number | 예 | 작품 가로 길이 |
| `artwork.height_cm` | number | 예 | 작품 세로 길이 |
| `artwork.medium` | string | 예 | 작품 매체 |

### 5.3 선택 입력값

| 필드 | 타입 | 설명 |
|---|---|---|
| `artist.artist_key` | string or null | 내부 작가 식별자가 있으면 작가명보다 우선 사용 |
| `artwork.title` | string or null | 작품 제목 |
| `artwork.depth_cm` | number or null | 입체 작품 또는 두께 정보 |
| `artwork.support` | string or null | canvas, paper, panel 등 지지체 |
| `artwork.year_made` | integer or null | 제작년도 |
| `market_context.target_market` | string | 기본값 `gallery` |
| `options.include_comparable_stats` | boolean | 비교군 통계 포함 여부 |
| `options.include_explanation` | boolean | 설명 정보 포함 여부 |
| `options.external_lookup_enabled` | boolean | 외부 데이터 실시간 조회 여부 |
| `artist_profile.*` | object | 작가 메타 정보가 있으면 Cold 보조 피처 또는 신뢰도 판단에 사용 |

## 6. 단건 예측 응답

### 6.1 Warm 응답 예시

```json
{
  "status": "success",
  "request_id": "trk6_20260603_000001",
  "prediction": {
    "price_krw": 4200000,
    "price_log": 15.2506,
    "price_range": {
      "low_krw": 2900000,
      "high_krw": 6100000,
      "range_policy": "warm_calibrated_range"
    },
    "confidence_grade": "B",
    "confidence_label": "보통",
    "display_policy": "point_with_range"
  },
  "model_info": {
    "route": "warm",
    "routing_reason": "artist_matched_in_training_data",
    "is_known_artist": true,
    "artist_history_count": 12,
    "model_family": "huber_blend",
    "model_policy": "warm_pp_svc3_svcnum_ppv8_070",
    "postprocessing_policy": "log_price_weighted_blend",
    "formula": "0.70 * pred_log_svc_numeric + 0.30 * pred_log_pp_v8"
  },
  "comparable_stats": {
    "available": true,
    "group_level": "artist_medium_size",
    "group_key": "artist=kimoo|medium=painting|size=medium",
    "sample_count": 24,
    "unit_price_per_ho": {
      "median_krw": 350000,
      "q25_krw": 280000,
      "q75_krw": 460000
    },
    "medium_distribution": [
      {
        "medium_category": "painting",
        "median_unit_price_per_ho_krw": 330000,
        "sample_count": 14
      },
      {
        "medium_category": "drawing",
        "median_unit_price_per_ho_krw": 280000,
        "sample_count": 10
      }
    ]
  },
  "risk_info": {
    "risk_level": "medium",
    "risk_reasons": [
      "artist_history_count_is_moderate",
      "price_range_width_is_moderate"
    ],
    "cold_start": false
  },
  "processing": {
    "total_ms": 120,
    "external_lookup_ms": 0
  }
}
```

### 6.2 Cold 응답 예시

```json
{
  "status": "success",
  "request_id": "trk6_20260603_000002",
  "prediction": {
    "price_krw": 2800000,
    "price_range": {
      "low_krw": 1100000,
      "high_krw": 7200000,
      "range_policy": "cold_wide_reference_range"
    },
    "confidence_grade": "D",
    "confidence_label": "매우 낮음",
    "display_policy": "reference_price_with_wide_range"
  },
  "model_info": {
    "route": "cold",
    "routing_reason": "artist_not_matched_in_training_data",
    "is_known_artist": false,
    "artist_history_count": 0,
    "model_family": "lightgbm_or_quantile_reference",
    "model_policy": "cold_reference_candidate",
    "postprocessing_policy": "cold_risk_and_range_policy"
  },
  "comparable_stats": {
    "available": true,
    "group_level": "medium_size_support",
    "sample_count": 41,
    "unit_price_per_ho": {
      "median_krw": 220000,
      "q25_krw": 90000,
      "q75_krw": 510000
    }
  },
  "risk_info": {
    "risk_level": "high",
    "risk_reasons": [
      "artist_not_seen_in_training_data",
      "cold_price_range_is_wide"
    ],
    "cold_start": true
  }
}
```

## 7. 비교군 통계 응답 기준

서비스에서 필요한 비교군 통계는 모델 설명과 화면 표시를 위해 별도로 제공한다.

| 항목 | 의미 | 산출 방식 |
|---|---|---|
| 호당가 중앙값 | 같은 비교군 표본들의 호당가 대표값 | 유효 표본의 median |
| 범위 | 같은 비교군 표본들의 호당가 분위 범위 | 기본 `q25~q75`, 필요 시 `q10~q90` 추가 |
| 매체별 분포 | 비교군을 매체별로 나눈 호당가 대표값 | 매체별 median과 표본 수 |
| 표본 수 N | 비교군에 포함된 유효 표본 수 | 가격, 크기, 매체가 유효한 표본만 카운트 |
| group_level | 어떤 기준으로 비교군을 만들었는지 | 예: 작가+매체+크기, 매체+크기+지지체 |

주의:

- 기존 Track6 실험에서는 `estimated_ho`, `ln_estimated_ho` 산출식이 이미 사용됐다.
- 서비스 v1도 같은 계열의 `estimated_ho` 산출식을 사용한다.
- 산출식: `area_cm2 = width_cm * height_cm`, `estimated_ho = argmin_h |area_cm2 - HO_TABLE_F[h]|`
- PP-SVC1 비교군 통계 실험 일부 split에서는 `estimated_ho`가 없어 면적 기준 단가를 대체 검증했다.
- 서비스에서는 호당가를 기본 표시값으로 두고, 면적 기준 단가는 호수 산출 불가 케이스의 보조값으로 남긴다.

## 8. 신뢰도 등급 초안

| 등급 | 의미 | 대표 조건 | 화면 표시 |
|---|---|---|---|
| A | 높은 신뢰도 | Warm, 작가 이력 충분, 비교군 N 충분, 가격 범위 좁음 | 예측 가격 중심 |
| B | 보통 신뢰도 | Warm이지만 작가 이력 또는 조건 일부 부족 | 예측 가격 + 범위 |
| C | 낮은 신뢰도 | Cold이지만 입력 정보와 비교군이 비교적 충분 | 참고 가격 + 넓은 범위 |
| D | 매우 낮은 신뢰도 | Cold, 작가 정보 부족, 비교군 N 부족, 범위 넓음 | 참고용 문구 필수 |

## 9. display_policy 초안

| 값 | 의미 | 사용 조건 |
|---|---|---|
| `point_with_range` | 예측 가격과 범위를 함께 표시 | Warm 일반 케이스 |
| `point_with_caution` | 예측 가격은 표시하되 주의 문구 추가 | Warm 저이력/극단 조건 |
| `reference_price_with_wide_range` | 참고 예측가와 넓은 범위 표시 | Cold 일반 케이스 |
| `range_only_recommended` | 단일 가격보다 범위 중심 표시 권장 | Cold 고위험 케이스 |

## 10. 배치 예측 API

`POST /api/track6/price-estimate/batch`

### 요청 예시

```json
{
  "items": [
    {
      "client_item_id": "item_001",
      "artist": {
        "name": "김OO"
      },
      "artwork": {
        "width_cm": 72.7,
        "height_cm": 60.6,
        "medium": "oil on canvas",
        "support": "canvas"
      }
    },
    {
      "client_item_id": "item_002",
      "artist": {
        "name": "이OO"
      },
      "artwork": {
        "width_cm": 45.5,
        "height_cm": 53.0,
        "medium": "acrylic on paper",
        "support": "paper"
      }
    }
  ],
  "options": {
    "include_comparable_stats": true,
    "external_lookup_enabled": false
  }
}
```

### 배치 제한 초안

- 1회 요청 최대 50건
- 배치 요청에서는 외부 실시간 수집 기본 비활성화
- 각 item별 성공/실패를 따로 반환

## 11. 모델 정보 API

`GET /api/track6/model-info`

### 응답 예시

```json
{
  "status": "success",
  "service_version": "track6-price-api-v0.2",
  "model_version": "track6-warm-pp-svc3-20260603",
  "policies": {
    "warm_primary": "warm_pp_svc3_svcnum_ppv8_070",
    "warm_validation": "pp_svc4_holdout_stability_passed",
    "cold_primary": "cold_reference_candidate",
    "cold_display_policy": "reference_price_with_wide_range"
  },
  "metrics_summary": {
    "warm_test_mdape": 0.1405,
    "warm_test_mape": 0.2748,
    "warm_test_p95_ape": 0.8331,
    "cold_status": "not_final_service_grade"
  }
}
```

## 12. 에러 응답 초안

### 필수값 누락

```json
{
  "status": "error",
  "error_code": "INVALID_REQUEST",
  "message": "artist.name, artwork.width_cm, artwork.height_cm, artwork.medium are required."
}
```

### 예측 불가

```json
{
  "status": "error",
  "error_code": "PREDICTION_UNAVAILABLE",
  "message": "Price prediction is temporarily unavailable."
}
```

### 지원하지 않는 작품 조건

```json
{
  "status": "error",
  "error_code": "UNSUPPORTED_ARTWORK_TYPE",
  "message": "This artwork type is outside the supported Track6 prediction scope."
}
```

## 13. 협업자 확인 필요 사항

| 항목 | 확인 필요 내용 |
|---|---|
| API path | `/api/track6/*` prefix 사용 가능 여부 |
| 가격 단위 | 원화만 제공할지, USD도 제공할지 |
| 호수 환산 | 서비스 화면의 `호당가` 계산 기준 |
| 화면 문구 | Warm/Cold별 문구 톤 |
| 신뢰도 등급 | A/B/C/D 또는 한글 라벨 사용 여부 |
| 외부 정보 수집 | 실시간 조회를 허용할지, 내부 캐시만 사용할지 |
| 배치 예측 | 1회 최대 요청 건수 |
| 참고 작품 노출 | 유사 작품/작가 가격 이력을 응답에 포함할지 |
| 모델명 노출 | `Huber`, `LightGBM` 같은 모델명을 사용자에게 노출할지 |

## 14. 아직 확정되지 않은 항목

- Warm 최종 후보를 서비스 artifact로 패키징하는 작업
- `svc_numeric_seed_mean`과 `PP-V8`을 운영 추론에서 동일하게 재현하는 artifact 구성
- Cold 점 예측 최종 후보
- Cold 가격 범위 보수화 정책
- 호당가 예외 정책과 비교군 group level fallback 순서
- 외부 데이터 수집을 API 기본 흐름에 넣을지 별도 배치 수집으로 둘지
- feature contribution을 사용자 화면에 노출할지 내부 운영용으로만 쓸지

## 15. 1차 구현 우선순위

| 우선순위 | 기능 | 이유 |
|---:|---|---|
| 1 | 단건 예측 API | 서비스 핵심 기능 |
| 2 | Warm/Cold 라우팅 결과 응답 | 화면 표시와 신뢰도 판단에 필요 |
| 3 | Warm `PP-SVC3` 결합 후보 artifact 패키징 | 검증된 후보를 운영에서 재현해야 함 |
| 4 | 비교군 통계 DB/API 응답 | 서비스 화면에서 바로 필요한 정보 |
| 5 | 가격 범위와 신뢰도 등급 | 단일 가격 오해 방지 |
| 6 | 모델 정보 API | 협업자와 운영자가 적용 정책 확인 |
| 7 | 배치 예측 API | 대량 작품 견적 요청 대응 |
| 8 | 모니터링 API | 운영 안정성 확인 |
