# Track6 사용자 화면 상세 명세

작성일: 2026-06-25

## 1. 문서 목적

이 문서는 일반 사용자가 보는 가격 예측 화면의 route, 입력, 상태, API 매핑, 검증 기준을 정의한다.

관련 문서:

- [PRD](product_requirements_20260625.md)
- [데이터 수집 서비스 시나리오](data_collection_service_scenarios_20260625.md)
- [사용자 / 어드민 API 기획](user_admin_api_plan_20260625.md)
- [화면 상태/에러 UX 기준](frontend_state_error_ux_spec_20260625.md)
- [프론트 컴포넌트 기준](frontend_component_guidelines_20260625.md)
- [프론트 마이크로카피 기준](frontend_microcopy_spec_20260625.md)

## 2. 사용자 route 구조

권장 route:

| 화면 | Route |
|---|---|
| 가격 예측 입력 | `/price-prediction` |
| 작가 검색/선택 | `/price-prediction` 내부 step 또는 modal |
| 신규 작가 후보 입력 | `/price-prediction/new-artist` 또는 modal |
| 예측 결과 | `/price-prediction/result/:prediction_id` 또는 same-page result |

1차 구현은 single-page flow로 시작할 수 있다.

```text
작가 검색/선택
  -> 작품 정보 입력
  -> 예측 요청
  -> 결과 표시
```

## 3. 가격 예측 입력 화면

API:

- `GET /api/v1/public/artists/search`
- `POST /api/v1/public/price-predictions`

입력 필드:

| 필드 | 필수 | 검증 |
|---|---|---|
| artist_key | 조건부 | 확정 작가 선택 시 필수 |
| artist_candidate_id | 조건부 | 신규 후보로 진행 시 사용 |
| title | 선택 | 빈 문자열 허용 |
| artwork_year | 선택 | 숫자, 미래 연도는 경고 |
| width_cm | 필수 | 양수 |
| height_cm | 필수 | 양수 |
| depth_cm | 선택 | 값이 있으면 양수 |
| medium | 필수 | 입력 또는 선택 |
| support | 선택 | canvas/paper/panel 등 |
| artwork_type | 필수 | painting/drawing/print 등 |

사용자 안내:

- cm 기준 입력이 가격 예측의 기본 입력임을 명확히 표시한다.
- 호당가는 계산 기준이 아니라 결과 화면의 표시용 참고값이다.
- 작가가 미확정이면 검수 필요 상태가 함께 표시된다.

## 4. 작가 검색/선택

API:

- `GET /api/v1/public/artists/search?q=&limit=`

검색 결과 표시:

| 항목 | 표시 |
|---|---|
| display_name_ko | 주 표시명 |
| display_name_en | 보조 표시명 |
| birth_year | 동명이인 구분 |
| nationality | 보조 정보 |
| activity_location | 보조 정보 |
| representative_artwork_count | 이력 규모 |
| has_price_history | Warm 가능성 표시 |
| match_label | 매칭 근거 라벨(예: 이름 일치) |

상태별 동작:

| 상태 | 동작 |
|---|---|
| 후보 1명 | 후보 card를 표시하고 사용자가 선택 |
| 후보 2명 이상 | 리스트에서 직접 선택 |
| 후보 없음 | 신규 작가 후보 입력으로 이동 |
| 후보 정보 부족 | 검수 필요 안내 |

노출 금지:

- source
- source_artwork_url
- artist_source_id
- artist_source_url
- raw/internal row id

## 5. 신규 작가 후보 입력

API:

- `POST /api/v1/public/artist-candidates`

입력 필드:

- artist_name
- artist_name_language
- artist_name_en
- artist_name_ko
- birth_year
- nationality
- activity_location
- website_or_reference_url
- note

성공 표시:

- 신규 작가 후보가 접수되었음을 표시한다.
- 최종 artist_key가 즉시 생성된 것처럼 표현하지 않는다.
- 예측을 계속 진행하는 경우 검수 필요 상태를 표시한다.

## 6. 예측 결과 화면

API:

- `POST /api/v1/public/price-predictions`
- 필요 시 `GET /api/v1/public/artists/{artist_key}/primary-market-summary`

표시 항목:

| 항목 | 설명 |
|---|---|
| predicted_price_krw | 원화 예측 가격 |
| display_price | 사용자 표시용 가격 |
| display_hodang_price | 표시용 참고값 |
| confidence_label | 높음/보통/검수 필요 등 |
| review_required | 검수 필요 여부 |
| review_reasons | 검수 필요 사유 |
| model_version | 사용 모델 |
| model_route | warm/cold/unified |
| deployment_id | 운영 배포 ID |
| artist | 선택 작가 표시명 |
| as_of | 모델이 참조한 snapshot 기준일 |
| primary_market_summary | 1차 시장 가격 카드 |

주의:

- `review_required=true`여도 계산값이 있으면 예측 가격과 검수 필요 사유를 함께 보여준다.
- 계산 실패와 검수 필요는 다른 상태다.
- `as_of`는 최신 수집일이 아니라 active deployment가 학습에 사용한 snapshot 기준일이다.
- 위 표는 화면 표시 항목이며, 응답 구조상 `model_version`/`model_route`/`deployment_id`는 `model` 객체 하위, `as_of`는 `primary_market_summary`(또는 응답 최상위) 기준이다([API 기획](user_admin_api_plan_20260625.md) §4.3).

## 7. 1차 시장 가격 카드

표시 항목:

| 항목 | 표시 예 |
|---|---|
| 제목 | 1차 시장 가격 |
| 호당가 중앙값 | 35만원/호 |
| 범위 | 28만 - 46만원/호 |
| 매체별 분포 | 회화 33만, 드로잉 28만 |
| 표본 수 | N=24 |
| 데이터 기준일 | 2026-06-25 |

상태:

| 상태 | 표시 |
|---|---|
| sample_count 충분 | 카드 표시 |
| sample_count 부족 | 참고 표본 부족 안내 |
| `FRESH-WARN-N` 초과 | 최신성 경고 |
| `FRESH-HIDE-M` 초과 | 카드 숨김, 기준일 오래됨 안내 |

원천 사이트명, 원천 URL, 원천 작품 ID는 노출하지 않는다.

## 8. 사용자 화면 에러/빈 상태

각 상황의 실제 노출 문구는 [프론트 마이크로카피 기준](frontend_microcopy_spec_20260625.md) §4~§7을 단일 기준으로 한다.

| 상황 | 표시 |
|---|---|
| 작가 검색 실패 | 검색을 다시 시도하도록 안내 |
| 후보 없음 | 신규 작가 후보 입력 안내 |
| 필수 입력 누락 | 필드 하단 validation |
| 예측 처리 실패 | 재시도 안내와 request_id 표시 |
| upstream/model unavailable | 잠시 후 다시 시도 안내 |
| freshness 경고 | 데이터 기준일과 경고 표시 |

## 9. 완료 기준

- 사용자 화면은 원천 추적 정보를 노출하지 않는다.
- 필수 입력 validation이 API 호출 전에 동작한다.
- API error envelope의 `field_errors`를 필드별로 표시한다.
- 예측 결과는 `model_version`, `deployment_id`, `as_of`를 표시하거나 디버그/상세 영역에서 확인 가능하다.
- 1차 시장 가격 카드는 freshness 정책을 따른다.
