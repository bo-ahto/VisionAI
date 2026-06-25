# Track6 프론트 API Mock / Fixture 기준

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 프론트엔드가 백엔드 구현과 병렬로 개발/테스트할 수 있도록 필요한 mock API 응답과 fixture 시나리오를 정의한다.

관련 문서:

- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [사용자 화면 상세 명세](user_frontend_screen_spec_20260625.md)
- [어드민 화면 상세 명세](admin_screen_detail_spec_20260625.md)
- [프론트 E2E 테스트 계획](frontend_e2e_test_plan_20260625.md)

## 2. Mock 원칙

- mock 필드는 API 문서의 response 필드명과 맞춘다.
- 사용자 mock에는 source URL/internal row id를 넣지 않는다.
- 어드민 mock에는 원천 추적 정보를 포함한다.
- success, empty, error, conflict, forbidden, stale 상태를 모두 가진다.
- id 값은 화면 decision path parameter와 일치해야 한다.
- 페이지 목록 응답은 표준 envelope `{items, page, page_size, total}`를, 검색 등 비페이지 목록은 `{items, total}`를 따른다(API 기획 응답 예시 기준).
- 필드명의 단일 기준은 API 기획 응답 예시다. 특히 작가명 검수 큐 필드는 API §8.3(`artist_name_ko_orig`, `artist_name_ko_input_type`, `artist_name_ko_reason`, `artist_name_ko_risk_score`, `artist_name_ko_roundtrip_confidence`, `artist_name_ko_override_status`)을 따른다. 아래 §5.2 예시의 `display_name_*_candidate`는 표시 후보용 보조 필드이며, API 표준 필드를 대체하지 않는다.

## 3. 권장 fixture 파일 구조

```text
fixtures/track6/
  public/
    artists_search_success.json
    artists_search_multiple.json
    artists_search_empty.json
    artists_search_error.json
    price_prediction_success_warm.json
    price_prediction_success_cold.json
    price_prediction_review_required.json
    price_prediction_validation_error.json
    price_prediction_processing_failed.json
    primary_market_summary_success.json
    primary_market_summary_warning.json
    primary_market_summary_low_sample.json
    primary_market_summary_stale_hidden.json
  admin/
    collection_summary_success.json
    collection_runs_success.json
    collection_run_detail_failed.json
    review_artworks_queue.json
    review_artist_names_queue.json
    review_artist_identities_queue.json
    review_new_artists_queue.json
    snapshots_candidates_summary.json
    snapshots_candidates_items.json
    model_deployments_current.json
    audit_logs_success.json
  errors/
    validation_error.json
    forbidden.json
    conflict.json
    upstream_unavailable.json
    processing_failed.json
```

검수 큐 fixture는 claim 상태별(`unclaimed`/`claimed_by_me`/`claimed_by_other`) 변형을 같은 큐 파일 안에서 row item의 `claim` 필드 값으로 표현한다(파일을 상태별로 분리하지 않는다). conflict 시나리오는 `errors/conflict.json`을 재사용한다.

## 4. Public fixtures

### 4.1 작가 검색 성공

```json
{
  "items": [
    {
      "artist_key": "artist_123",
      "display_name_ko": "홍길동",
      "display_name_en": "Hong Gildong",
      "birth_year": 1980,
      "nationality": "Korean",
      "activity_location": "Seoul",
      "representative_artwork_count": 24,
      "has_price_history": true,
      "match_label": "이름 일치"
    }
  ],
  "total": 1
}
```

### 4.2 예측 성공

```json
{
  "prediction_id": "pred_123",
  "predicted_price_krw": 3500000,
  "display_price": "350만원",
  "display_hodang_price": "35만원/호",
  "confidence_label": "보통",
  "review_required": false,
  "review_reasons": [],
  "model": {
    "model_version": "official_v0_1_warm_20260625_01",
    "model_route": "warm",
    "deployment_id": "deploy_20260625_01"
  },
  "artist": {
    "artist_key": "artist_123",
    "display_name_ko": "홍길동",
    "display_name_en": "Hong Gildong"
  },
  "primary_market_summary": {
    "title": "1차 시장 가격",
    "hodang_median_label": "호당가 중앙값",
    "hodang_median_krw": 350000,
    "hodang_range_krw": [280000, 460000],
    "medium_distribution": [
      {"medium": "회화", "hodang_median_krw": 330000}
    ],
    "sample_count": 24,
    "as_of": "2026-06-25T00:00:00Z",
    "data_reference_date": "2026-06-25"
  }
}
```

## 5. Admin fixtures

### 5.1 수집 대시보드

```json
{
  "last_finished_at": "2026-06-25T02:00:00Z",
  "overall_status": "warning",
  "sources": [
    {
      "source": "art1",
      "status": "success",
      "raw_artwork_rows": 1541,
      "normalized_artwork_rows": 1142,
      "size_parse_success_rate": 0.92,
      "price_present_rows": 980,
      "price_present_rate": 0.86,
      "total_failed": 0
    }
  ],
  "review_queue_counts": {
    "artworks": 20,
    "artist_names": 12,
    "artist_identities": 5,
    "new_artists": 8
  },
  "snapshot_candidate_count": 1100
}
```

### 5.2 작가명 검수 큐

```json
{
  "items": [
    {
      "alias_id": "alias_123",
      "source": "art1",
      "artist_name_raw": "Hong Gildong",
      "artist_name_ko_orig": "홍길동",
      "display_name_ko_candidate": "홍길동",
      "display_name_en_candidate": "Hong Gildong",
      "artist_name_ko_input_type": "romanized_korean",
      "artist_name_ko_reason": "roundtrip_high",
      "artist_name_ko_risk_score": 0.12,
      "artist_name_ko_risk_reasons": [],
      "artist_name_ko_roundtrip_confidence": 0.95,
      "artist_name_ko_override_status": "none",
      "review_status": "needs_review",
      "claim": {
        "claimed_by": null,
        "claim_expires_at": null
      }
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

## 6. Error fixtures

### 6.1 validation error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값을 확인해야 합니다.",
    "field_errors": [
      {"field": "width_cm", "message": "필수값입니다."}
    ],
    "request_id": "req_validation_001"
  }
}
```

### 6.2 conflict

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "이미 다른 담당자가 처리한 항목입니다.",
    "field_errors": [],
    "request_id": "req_conflict_001"
  }
}
```

## 7. Fixture coverage checklist

- artist search: success / multiple / empty / error
- price prediction: warm / cold / review_required / validation_error / processing_failed
- primary market card: normal / warning / hidden / low sample
- admin dashboard: success / empty / failed source / blocked source
- review queues: unclaimed / claimed_by_me / claimed_by_other / conflict
- snapshot: snapshot_request(requested / approved) / artwork_snapshot(generating / generated / approved / failed)
- model deployment: active / rollback available / no active model
- audit logs: normal / empty / filtered
