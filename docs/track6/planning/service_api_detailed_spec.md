# Track6 가격 예측 서비스 API 상세 문서

- 작성일: 2026-06-04
- 문서 목적: 실제 서비스에서 사용할 가격 예측 API의 요청값, 응답값, 모델 라우팅, 가격 범위, 신뢰도, 비교군 통계, 유사 작품 정보를 구현자가 바로 검토할 수 있게 정의
- 적용 범위: 신규 Track6 서비스 API
- 제외 범위: 기존 셀프 테스트용 API와의 호환성
- 기준 모델:
  - Warm: `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`
  - Warm 검증: `PP-SVC4` 반복 holdout 안정성
  - Cold: `PP-Y18 qwidth_bin_oof_min30_cap0.25` 참고 예측가 정책
  - Cold 보조: `PP-Y16` 큰 오차 방어 참고

## 1. API 설계 원칙

- 기존 테스트 API와 완전히 분리된 신규 계약
- 서비스 화면이 필요한 데이터를 한 번에 받을 수 있는 응답 구조
- Warm/Cold 라우팅 결과와 라우팅 이유를 항상 응답
- Warm은 예측 가격 중심, Cold는 참고 예측가와 넓은 가격 범위 중심
- 비교군 통계는 모델 결과와 별도 블록으로 제공
- 호당가 통계는 기존 Track6 `estimated_ho` 산출식을 서비스 v1 표준으로 사용
- 외부 검색은 실시간 기본값 비활성화, 사전 수집/캐시 기반 사용 권장
- 모델명과 내부 실험명은 운영/협업자용 필드에만 포함하고, 사용자 화면 문구와 분리

## 2. 서비스 화면 데이터 매핑

| 화면 필요 항목 | API 응답 위치 | 산출 기준 | 비고 |
|---|---|---|---|
| 예측 가격 | `prediction.price_krw` | Warm은 PP-SVC3 최종 결합, Cold는 참고 예측가 | Cold는 화면 문구를 `참고 예측가`로 권장 |
| 예측 가격 범위 | `prediction.price_range` | Warm calibration 또는 Cold q10~q90/비교군 범위 | Cold는 넓게 제공 |
| 신뢰도 | `prediction.confidence` | route, 비교군 N, 가격 범위 폭, 입력 품질 | A/B/C/D |
| 호당가 중앙값 | `comparable_stats.unit_price_per_ho.median_krw` | 비교군 호당가 median | Track6 `estimated_ho` v1 기준 |
| 호당가 범위 | `comparable_stats.unit_price_per_ho.q25_krw`, `q75_krw` | 비교군 호당가 분위 범위 | 필요 시 q10/q90 추가 |
| 매체별 호당가 분포 | `comparable_stats.medium_unit_price_distribution` | 매체별 호당가 median, 표본 수 | 화면의 매체별 분포 카드 |
| 비교 표본 수 N | `comparable_stats.sample_count` | 비교군 유효 표본 수 | 신뢰도 산정에도 사용 |
| 유사 작품 정보 | `similar_artworks` | 비교군에서 대표 표본 추출 | 공개 가능 필드만 노출 |
| 모델/정책 정보 | `model_info` | route, model_policy, postprocessing_policy | 운영/협업자 확인용 |
| 위험 사유 | `risk_info` | 낮은 신뢰도 원인 | 화면 문구 또는 내부 로그 |

## 3. 서비스 버전

| 항목 | 값 |
|---|---|
| `service_version` | `track6-price-api-v0.3` |
| `model_version` | `track6-final-candidate-20260604` |
| `warm_primary_policy` | `warm_pp_svc3_svcnum_ppv8_070` |
| `warm_postprocessing_policy` | `log_price_weighted_blend_70_30` |
| `cold_reference_policy` | `cold_lgb_quantile_qwidth_reference` |
| `comparable_stats_policy` | `fallback_comparable_group_stats_v1` |
| `external_lookup_policy` | `cache_or_manual_only_by_default` |

## 4. 엔드포인트 목록

| Method | Path | 목적 | 필수 여부 |
|---|---|---|---|
| GET | `/api/track6/health` | API 상태 확인 | 필수 |
| GET | `/api/track6/model-info` | 모델 버전, 적용 정책, 성능 요약 확인 | 필수 |
| POST | `/api/track6/price-estimate` | 단건 가격 예측 | 필수 |
| POST | `/api/track6/price-estimate/batch` | 다건 가격 예측 | 선택 |
| GET | `/api/track6/predictions/{request_id}` | 예측 결과 재조회 | 선택 |
| GET | `/api/track6/monitor` | 운영 통계 확인 | 운영 필수 |

## 5. 단건 예측 API

### 5.1 요청

`POST /api/track6/price-estimate`

```json
{
  "request_id": "client_optional_id_001",
  "artist": {
    "name": "김OO",
    "name_ko": null,
    "name_en": null,
    "artist_key": null
  },
  "artwork": {
    "title": "Untitled",
    "width_cm": 72.7,
    "height_cm": 60.6,
    "depth_cm": null,
    "estimated_ho": null,
    "medium": "oil on canvas",
    "support": "canvas",
    "year_made": 2022,
    "is_edition": false
  },
  "market_context": {
    "target_market": "gallery",
    "currency": "KRW",
    "as_of_date": "2026-06-04"
  },
  "artist_profile": {
    "birth_year": null,
    "death_year": null,
    "nationality": null,
    "total_works": null,
    "solo_count": null,
    "group_count": null,
    "gallery_tier": null,
    "followers": null
  },
  "options": {
    "include_comparable_stats": true,
    "include_similar_artworks": true,
    "include_explanation": true,
    "external_lookup_enabled": false
  }
}
```

### 5.2 필수 요청 필드

| 필드 | 타입 | 조건 | 설명 |
|---|---|---|---|
| `artist.name` | string | 빈 문자열 불가 | 작가명 |
| `artwork.width_cm` | number | `> 0` | 작품 가로 |
| `artwork.height_cm` | number | `> 0` | 작품 세로 |
| `artwork.medium` | string | 빈 문자열 불가 | 작품 매체 |

### 5.3 선택 요청 필드

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request_id` | string or null | 서버 생성 | 클라이언트 추적 ID |
| `artist.artist_key` | string or null | null | 내부 작가 식별자, 있으면 작가명 매칭보다 우선 |
| `artist.name_ko` | string or null | null | 한글 작가명 |
| `artist.name_en` | string or null | null | 영문 작가명 |
| `artwork.title` | string or null | null | 작품명 |
| `artwork.depth_cm` | number or null | null | 깊이/입체 정보 |
| `artwork.estimated_ho` | number or null | null | 호수. 제공되면 검증 후 사용, 없으면 Track6 `estimated_ho` v1로 계산 |
| `artwork.support` | string or null | `unknown` | canvas, paper, panel 등 지지체 |
| `artwork.year_made` | integer or null | null | 제작년도 |
| `artwork.is_edition` | boolean | false | 에디션 여부 |
| `market_context.target_market` | string | `gallery` | 서비스 기준 시장 |
| `market_context.currency` | string | `KRW` | 1차 구현은 KRW 우선 |
| `artist_profile.*` | object | null | Cold 보조 피처 및 신뢰도 판단 |
| `options.include_comparable_stats` | boolean | true | 비교군 통계 포함 여부 |
| `options.include_similar_artworks` | boolean | true | 유사 작품 정보 포함 여부 |
| `options.include_explanation` | boolean | true | 설명 블록 포함 여부 |
| `options.external_lookup_enabled` | boolean | false | 실시간 외부 조회 여부 |

## 6. 입력 표준화

| 처리 | 기준 |
|---|---|
| 작가명 정규화 | 공백, 특수문자, 영문 대소문자, 한글/영문 alias 정규화 |
| 작가 매칭 | `artist_key` 우선, 없으면 정규화 작가명으로 registry 검색 |
| 크기 | cm 기준으로 통일 |
| 면적 | `area_cm2 = width_cm * height_cm` |
| 로그 면적 | `log_area = log(area_cm2)` |
| 호수 | `estimated_ho`가 있으면 검증 후 사용, 없으면 `area_cm2`를 F형 호수 면적표에 근접 매핑해 계산 |
| 3D 후보 | `depth_cm` 유효 시 `has_depth=true`, `is_3d_candidate=true` 후보 |
| medium/support | 내부 표준 category로 매핑, 실패 시 `unknown` |

## 7. Warm/Cold 라우팅

| route | 조건 | 적용 정책 |
|---|---|---|
| `warm` | `artist_key`가 학습 artist registry에 안정 매칭 | Warm PP-SVC3 결합 후보 |
| `cold` | 학습 artist registry에 없음 | Cold 참고 예측가 + 넓은 범위 |
| `unknown_artist_match` | 동명이인 또는 매칭 충돌 | 기본 Cold, 또는 낮은 신뢰도 Warm 후보 |
| `unsupported` | 필수 피처 부족 또는 지원 범위 밖 조건 | 예측 불가 응답 |

라우팅 응답 필수값:

- `model_info.route`
- `model_info.routing_reason`
- `model_info.artist_match_status`
- `model_info.artist_history_count`

## 8. Warm 모델 정책

### 8.1 적용 후보

| 항목 | 값 |
|---|---|
| `model_policy` | `warm_pp_svc3_svcnum_ppv8_070` |
| `model_family` | `huber_blend` |
| `postprocessing_policy` | `log_price_weighted_blend_70_30` |
| 검증 실험 | `PP-SVC3`, `PP-SVC4` |
| test MdAPE | `0.1405` |
| test MAPE | `0.2748` |
| test p95_APE | `0.8331` |

### 8.2 예측 공식

```text
pred_log_final = 0.70 * pred_log_svc_numeric + 0.30 * pred_log_pp_v8
price_krw = exp(pred_log_final)
```

| 구성값 | 의미 |
|---|---|
| `pred_log_svc_numeric` | 비교군 통계 피처를 포함한 Warm Huber 후보 예측값 |
| `pred_log_pp_v8` | 기존 Warm compact blend 후보 예측값 |
| `0.70` | 비교군 통계 후보 비중 |
| `0.30` | PP-V8 평균오차/큰 오차 방어 후보 비중 |

운영 주의:

- API 배포 전 `pred_log_svc_numeric`과 `pred_log_pp_v8`을 동일 입력에서 재현해야 함
- 실험 성능은 저장 예측값 결합 기준이므로 artifact 재현성 테스트가 필요
- 사용자 화면에는 내부 후보명보다 “검증된 예측 가격”과 “비교군 기반 보정” 정도로 표현 권장

## 9. Cold 모델 정책

Cold는 단일 확정 가격으로 제공하지 않는다.

| 항목 | 값 |
|---|---|
| `model_policy` | `cold_lgb_quantile_qwidth_reference` |
| `model_family` | `lightgbm_quantile_reference` |
| `postprocessing_policy` | `qwidth_bin_oof_min30_cap025` |
| 대표 후보 | `PP-Y18 qwidth_bin_oof_min30_cap0.25` |
| 보조 후보 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` |
| display_policy | `reference_price_with_wide_range` |
| 기본 confidence | `C` 또는 `D` |

Cold 응답 원칙:

- `prediction.price_krw`는 참고 예측가
- `prediction.price_range`는 Warm보다 넓게 산출
- `confidence.grade`는 예측 신뢰도 차이를 반영하기 위해 보수적으로 산정
- `risk_info.risk_reasons`에 Cold 사유를 반드시 포함

## 10. 비교군 통계

### 10.1 목적

비교군 통계는 모델 설명값이자 서비스 화면 데이터다.

- 예측 가격의 주변 시장 기준 제공
- 호당가 중앙값/범위 표시
- 매체별 분포 표시
- 신뢰도 산정
- 유사 작품 후보 추출

### 10.2 비교군 fallback 순서

| 순서 | group_level | 의미 | 최소 표본 기준 |
|---:|---|---|---:|
| 1 | `artist_medium_support_size` | 같은 작가 + 같은 재료/지지체 + 유사 크기 | 5 |
| 2 | `artist_size` | 같은 작가 + 유사 크기 | 5 |
| 3 | `artist` | 같은 작가 전체 | 5 |
| 4 | `medium_support_size` | 같은 재료/지지체 + 유사 크기 | 30 |
| 5 | `medium_category_support_size` | 같은 재료 + 같은 지지체 + 유사 크기 | 30 |
| 6 | `medium_size` | 같은 재료 + 유사 크기 | 50 |
| 7 | `global` | 전체 train 기준 | 전체 |

### 10.3 비교군 통계 응답 스키마

```json
{
  "comparable_stats": {
    "available": true,
    "group_level": "artist_medium_support_size",
    "group_key": "artist=a_123|medium=painting|support=canvas|size=medium",
    "fallback_used": false,
    "sample_count": 24,
    "sample_count_label": "N=24",
    "price": {
      "median_krw": 4200000,
      "q25_krw": 3000000,
      "q75_krw": 5900000,
      "q10_krw": 2100000,
      "q90_krw": 8500000
    },
    "unit_price_per_ho": {
      "ho_policy": "track6_estimated_ho_f_nearest_v1",
      "median_krw": 350000,
      "q25_krw": 280000,
      "q75_krw": 460000,
      "q10_krw": 180000,
      "q90_krw": 720000
    },
    "unit_price_per_area": {
      "median_krw_per_cm2": 950,
      "q25_krw_per_cm2": 680,
      "q75_krw_per_cm2": 1300
    },
    "medium_unit_price_distribution": [
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
    ],
    "as_of_date": "2026-06-04"
  }
}
```

호당가 산출 기준:

- 서비스 화면 요구는 호당가 기준
- 서비스 v1 기준: 기존 Track6 `estimated_ho` 산출식을 사용
- 산출식: `area_cm2 = width_cm * height_cm`, `estimated_ho = argmin_h |area_cm2 - HO_TABLE_F[h]|`
- `HO_TABLE_F`: 한국 캔버스 F형 기준 호수별 참조 면적표
- 기준 구현: `scripts/track6_add_size_ho_features.py`의 Track6 split 생성 방식과 동일한 nearest mapping
- 참고: 공용 모듈에는 보간 방식 `area_to_ho_f`도 있으나, 서비스 v1 API 문서는 Track6 실험 split과 맞추기 위해 nearest mapping을 표준으로 둠
- 호당가: `unit_price_per_ho = price_krw / estimated_ho`
- `estimated_ho <= 0` 또는 크기 정보 부족 시 호당가 null
- PP-SVC1 비교군 통계 실험 일부 split에서는 `estimated_ho`가 없어 면적 단가를 대체 검증했지만, 서비스 API는 기존 Track6 호수 산출식을 적용

## 11. 유사 작품 / 비교 표본 정보

### 11.1 목적

- 예측 가격을 설명할 근거 제공
- 비교군 통계가 어떤 표본에서 나왔는지 확인
- 내부 검수자가 가격 범위와 신뢰도를 판단할 수 있게 지원

### 11.2 응답 스키마

```json
{
  "similar_artworks": {
    "available": true,
    "display_limit": 5,
    "items": [
      {
        "artwork_id": "aw_001",
        "artist_key": "a_123",
        "artist_name_display": "김OO",
        "title_display": "Untitled",
        "year_made": 2020,
        "medium_category": "painting",
        "support_category": "canvas",
        "width_cm": 72.7,
        "height_cm": 60.6,
        "estimated_ho": null,
        "price_krw": 3900000,
        "unit_price_per_ho_krw": null,
        "unit_price_per_area_krw_per_cm2": 880,
        "similarity_reason": [
          "same_artist",
          "similar_size",
          "same_medium_support"
        ],
        "data_source": "internal_price_history",
        "display_permission": "internal_or_public_summary"
      }
    ]
  }
}
```

노출 정책:

- 대외 화면에는 저작권/계약 문제가 없는 요약 필드만 노출
- 내부 운영 화면에는 `artwork_id`, 가격, 비교 사유를 더 상세히 제공 가능
- 비교 표본이 적으면 `similar_artworks.available=false`와 사유 반환

## 12. 가격 범위 산출

### 12.1 Warm

Warm 범위는 최종 예측 가격과 Warm residual calibration을 중심으로 산출한다.

```text
range_low_krw = price_krw * warm_lower_factor
range_high_krw = price_krw * warm_upper_factor
```

운영 기준:

- 비교군 q25/q75가 존재하면 모델 범위와 비교군 분위 범위를 함께 참고
- 비교군 N이 충분하면 범위 신뢰도 상승
- 극단 크기, 저이력 작가, 비교군 부족이면 범위 확대

### 12.2 Cold

Cold 범위는 Quantile 범위와 비교군 범위를 함께 사용한다.

```text
model_low_krw = exp(q10_log)
model_mid_krw = exp(q50_log)
model_high_krw = exp(q90_log)

range_low_krw = min(model_low_krw, comparable_q25_or_q10)
range_high_krw = max(model_high_krw, comparable_q75_or_q90)
```

운영 기준:

- `quantile_width`가 클수록 범위 확대
- 비교군 N이 부족하면 신뢰도 하향
- 고위험 Cold는 `range_only_recommended` 가능

## 13. 신뢰도

### 13.1 응답 스키마

```json
{
  "confidence": {
    "grade": "B",
    "label": "보통",
    "score": 0.68,
    "score_version": "confidence_policy_v1",
    "reasons": [
      "warm_artist_matched",
      "comparable_sample_count_moderate",
      "price_range_width_moderate"
    ]
  }
}
```

### 13.2 등급 기준 초안

| grade | 의미 | 대표 조건 | 화면 표시 |
|---|---|---|---|
| A | 높은 신뢰도 | Warm, 작가 이력 충분, 비교군 N 충분, 범위 좁음 | 예측 가격 중심 |
| B | 보통 신뢰도 | Warm 일반, 일부 조건 부족 | 예측 가격 + 범위 |
| C | 낮은 신뢰도 | Cold이지만 비교군/입력 정보 충분 | 참고 가격 + 넓은 범위 |
| D | 매우 낮은 신뢰도 | Cold, 비교군 부족, 범위 넓음, 매칭 불확실 | 참고용 문구 필수 |

### 13.3 신뢰도 산정 요인

| 요인 | 신뢰도 영향 |
|---|---|
| Warm route | 상승 |
| artist_history_count 충분 | 상승 |
| comparable sample_count 충분 | 상승 |
| price_range 폭 좁음 | 상승 |
| Cold route | 하락 |
| unknown artist match | 하락 |
| medium/support 매핑 실패 | 하락 |
| 3D/극단 크기 | 하락 |
| external signal conflict | 하락 |

## 14. 단건 응답 예시

### 14.1 Warm 응답

```json
{
  "status": "success",
  "request_id": "trk6_20260604_000001",
  "prediction": {
    "price_krw": 4200000,
    "price_log": 15.2506,
    "price_range": {
      "low_krw": 2900000,
      "high_krw": 6100000,
      "range_policy": "warm_calibrated_range"
    },
    "display_policy": "point_with_range",
    "price_label": "예측 가격"
  },
  "confidence": {
    "grade": "B",
    "label": "보통",
    "score": 0.68,
    "reasons": [
      "warm_artist_matched",
      "comparable_sample_count_moderate"
    ]
  },
  "model_info": {
    "route": "warm",
    "routing_reason": "artist_matched_in_training_data",
    "artist_match_status": "matched",
    "artist_history_count": 12,
    "model_family": "huber_blend",
    "model_policy": "warm_pp_svc3_svcnum_ppv8_070",
    "postprocessing_policy": "log_price_weighted_blend_70_30",
    "formula": "0.70 * pred_log_svc_numeric + 0.30 * pred_log_pp_v8"
  },
  "comparable_stats": {
    "available": true,
    "group_level": "artist_medium_support_size",
    "sample_count": 24,
    "price": {
      "median_krw": 4200000,
      "q25_krw": 3000000,
      "q75_krw": 5900000
    },
    "unit_price_per_ho": {
      "ho_policy": "track6_estimated_ho_f_nearest_v1",
      "median_krw": 350000,
      "q25_krw": 280000,
      "q75_krw": 460000
    }
  },
  "similar_artworks": {
    "available": true,
    "display_limit": 5,
    "items": []
  },
  "risk_info": {
    "risk_level": "medium",
    "risk_reasons": [
      "price_range_width_moderate"
    ]
  },
  "processing": {
    "total_ms": 120,
    "external_lookup_ms": 0
  }
}
```

### 14.2 Cold 응답

```json
{
  "status": "success",
  "request_id": "trk6_20260604_000002",
  "prediction": {
    "price_krw": 2800000,
    "price_range": {
      "low_krw": 900000,
      "high_krw": 7800000,
      "range_policy": "cold_quantile_wide_reference_range"
    },
    "display_policy": "reference_price_with_wide_range",
    "price_label": "참고 예측가"
  },
  "confidence": {
    "grade": "D",
    "label": "매우 낮음",
    "score": 0.31,
    "reasons": [
      "artist_not_seen_in_training_data",
      "cold_price_range_is_wide"
    ]
  },
  "model_info": {
    "route": "cold",
    "routing_reason": "artist_not_matched_in_training_data",
    "artist_match_status": "not_matched",
    "artist_history_count": 0,
    "model_family": "lightgbm_quantile_reference",
    "model_policy": "cold_lgb_quantile_qwidth_reference",
    "postprocessing_policy": "qwidth_bin_oof_min30_cap025"
  },
  "comparable_stats": {
    "available": true,
    "group_level": "medium_support_size",
    "sample_count": 41,
    "unit_price_per_ho": {
      "ho_policy": "track6_estimated_ho_f_nearest_v1",
      "median_krw": 220000,
      "q25_krw": 90000,
      "q75_krw": 510000
    }
  },
  "risk_info": {
    "risk_level": "high",
    "risk_reasons": [
      "cold_start",
      "wide_quantile_range"
    ]
  }
}
```

## 15. 배치 예측 API

`POST /api/track6/price-estimate/batch`

### 15.1 요청

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
    }
  ],
  "options": {
    "include_comparable_stats": true,
    "include_similar_artworks": false,
    "external_lookup_enabled": false
  }
}
```

### 15.2 제한

- 1회 요청 최대 50건
- item별 성공/실패 분리 반환
- 외부 실시간 수집 기본 비활성화
- 배치 응답은 `prediction`, `confidence`, `model_info`, `comparable_stats`, `error`를 item별로 포함

## 16. 모델 정보 API

`GET /api/track6/model-info`

```json
{
  "status": "success",
  "service_version": "track6-price-api-v0.3",
  "model_version": "track6-final-candidate-20260604",
  "policies": {
    "warm_primary": "warm_pp_svc3_svcnum_ppv8_070",
    "warm_display_policy": "point_with_range",
    "cold_reference": "cold_lgb_quantile_qwidth_reference",
    "cold_display_policy": "reference_price_with_wide_range",
    "comparable_stats_policy": "fallback_comparable_group_stats_v1"
  },
  "metrics_summary": {
    "warm_test_mdape": 0.1405,
    "warm_test_mape": 0.2748,
    "warm_test_p95_ape": 0.8331,
    "cold_reference_mdape": 0.4247,
    "cold_reference_mape": 0.9910,
    "cold_reference_p95_ape": 3.3053
  },
  "warnings": [
    "unit_price_per_ho_formula_must_be_confirmed_before_public_display",
    "cold_prediction_should_be_displayed_as_reference_price"
  ]
}
```

## 17. 에러 응답

| error_code | HTTP | 의미 |
|---|---:|---|
| `INVALID_REQUEST` | 400 | 필수값 누락 또는 타입 오류 |
| `ARTIST_MATCH_CONFLICT` | 409 | 작가 매칭 후보 충돌 |
| `UNSUPPORTED_ARTWORK_TYPE` | 422 | 지원 범위 밖 작품 |
| `FEATURE_GENERATION_FAILED` | 500 | 피처 생성 실패 |
| `PREDICTION_UNAVAILABLE` | 503 | 모델 추론 실패 |
| `COMPARABLE_STATS_UNAVAILABLE` | 200 또는 206 | 예측은 가능하나 비교군 통계 부족 |

예시:

```json
{
  "status": "error",
  "request_id": "trk6_20260604_000003",
  "error": {
    "error_code": "INVALID_REQUEST",
    "message": "artist.name, artwork.width_cm, artwork.height_cm, artwork.medium are required.",
    "details": [
      {
        "field": "artwork.width_cm",
        "reason": "required"
      }
    ]
  }
}
```

## 18. 운영 로그 필드

| 필드 | 설명 |
|---|---|
| `request_id` | 요청 ID |
| `created_at` | 예측 시각 |
| `route` | warm/cold/unknown_artist_match |
| `model_version` | 모델 버전 |
| `model_policy` | 적용 모델 정책 |
| `postprocessing_policy` | 후처리 정책 |
| `artist_key` | 매칭 작가 |
| `artist_match_status` | matched/not_matched/conflict |
| `artist_history_count` | 작가 학습 이력 수 |
| `comparable_group_level` | 비교군 level |
| `comparable_sample_count` | 비교군 N |
| `pred_log` | 내부 로그 예측값 |
| `price_krw` | 표시 예측값 |
| `range_low_krw` | 가격 범위 하한 |
| `range_high_krw` | 가격 범위 상한 |
| `confidence_grade` | 신뢰도 |
| `display_policy` | 화면 표시 정책 |
| `risk_reasons_json` | 위험 사유 |
| `latency_ms` | 처리 시간 |
| `error_code` | 실패 시 에러 코드 |

## 19. 구현 전 확정 필요

| 항목 | 이유 |
|---|---|
| Warm artifact 구성 | `svc_numeric_seed_mean`과 PP-V8 예측값 재현 필요 |
| 호수 산출 예외 정책 | 클라이언트 제공 `estimated_ho`와 자동 계산값이 다를 때의 우선순위, 3D/비표준 작품 표시 기준 |
| 비교군 fallback 최소 N | 통계 신뢰도와 신뢰도 등급에 직접 영향 |
| 가격 범위 calibration | Warm/Cold 범위 폭 결정 |
| Cold 참고가 노출 문구 | 예측 신뢰도 차이를 화면에 반영 |
| 유사 작품 노출 범위 | 저작권/계약/개인정보 이슈 방지 |
| 외부 검색 캐시 정책 | latency와 검색 품질 안정성 |
| API prefix | 협업자 서비스 라우팅과 맞춤 |
