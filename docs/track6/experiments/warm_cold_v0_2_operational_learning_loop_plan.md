# Warm/Cold v0.2 운영 학습 루프 기획서

- 작성일: 2026-06-11
- 적용 버전: `price_prediction_v0.2`
- 문서 목적: 실제 서비스 운영 중 새로 들어오는 작품 정보, 예측 결과, 실제 판매가를 안전하게 축적하고 다음 모델 학습에 반영하는 구조를 정의
- 관련 문서: `warm_cold_service_operationalization_plan_next_version.md`, `partner_warm_cold_best_model_report.md`

## 1. 결론

- v0.2에서는 예측 API만 만드는 것이 아니라, 운영 중 생성되는 데이터를 다음 학습에 연결하는 구조까지 포함해야 함
- 사용자가 입력한 작품 정보는 즉시 모델 학습에 쓰지 않고, 예측 요청 기록과 피처 스냅샷으로 먼저 저장
- 실제 판매가, 거래일, 판매 채널, 증빙 정보가 들어온 경우에만 학습 후보 라벨로 승격
- 검수 전 데이터는 학습에 반영하지 않음
- 검수 완료 데이터도 곧바로 운영 모델에 반영하지 않고, 정해진 주기마다 재학습 후보 데이터셋으로 묶어 검증
- 새 모델은 기존 fixed test, 신규 운영 holdout, route별 성능, 큰 오차 지표를 모두 통과한 뒤에만 다음 버전으로 승격
- v0.2의 핵심은 "운영 예측"과 "운영 학습 데이터 축적"을 같은 서비스 안에서 연결하되, 모델 오염을 막는 검수 단계를 두는 것

## 2. 버전 범위

| 구분 | 이전 버전(v0.1) | 다음 버전(v0.2) |
|---|---|---|
| 예측 기능 | Warm 중심 예측, Cold는 참고 범위 중심 | Warm/Cold 라우팅, Cold 예상 가격, 계산 설명 제공 |
| 사용자 입력 | 작품 정보 입력과 작가 후보 확인 | 동일 구조 유지, 부족 정보 안내 추가 |
| 실제 판매가 입력 | 별도 구조 필요 | 예측 결과와 연결된 피드백 입력 구조 추가 |
| 학습 데이터 축적 | 수동 수집 중심 | 예측 이벤트, 피처, 실제 판매가, 검수 상태를 구조화 저장 |
| 학습 반영 | 실험 단위 수동 반영 | 검수 완료 데이터만 주기적 재학습 후보로 반영 |
| 모델 배포 | 수동 교체 | 후보 모델 검증 후 버전 승격 |

## 3. 운영 학습 루프 전체 구조

```text
[사용자 작품 입력]
  - 작가명
  - 작품 크기
  - 매체/지지체
  - 제작연도
  - 작품 URL 또는 이미지
        |
        v
[v0.2 가격 예측]
  - 작가 매칭
  - Warm/Cold 라우팅
  - 예측가격/가격범위/신뢰도 산출
  - 사용 피처와 계산 요약 저장
        |
        v
[예측 이벤트 저장]
  - prediction_id
  - 입력 스냅샷
  - 피처 스냅샷
  - 예측 결과
  - 모델 버전
        |
        +------------------------------+
        |                              |
        v                              v
[사용자 보완 입력]              [실제 판매가 입력]
  - 누락된 제작연도              - 실제 판매가
  - 매체/지지체 정정             - 통화
  - 작가 정보 정정               - 판매일
  - 작품 이미지/URL              - 판매 채널
        |                              - 증빙 상태
        |                              |
        +---------------+--------------+
                        |
                        v
              [운영 데이터 검수]
                - 작가 매칭 검수
                - 작품 중복 검수
                - 가격 이상치 검수
                - 판매 증빙 검수
                - 학습 동의 확인
                        |
                        v
              [학습 후보 데이터셋]
                - training_eligible=true
                - route별 후보 분리
                - holdout 후보 분리
                        |
                        v
              [주기적 재학습/검증]
                - Warm 재학습 후보
                - Cold 재학습 후보
                - 보정값 재산출
                - 성능 회귀 검증
                        |
                        v
              [모델 버전 승격]
                - v0.2.x 실험 후보
                - v0.3 운영 후보
```

## 4. 핵심 원칙

| 원칙 | 내용 |
|---|---|
| 즉시 학습 금지 | 사용자가 입력한 판매가를 바로 운영 모델에 반영하지 않음 |
| 예측 당시 상태 저장 | 입력값, 파생 피처, 모델 버전, 예측 결과를 함께 저장 |
| 검수 후 학습 반영 | 실제 판매가와 증빙이 검수된 데이터만 학습 후보로 사용 |
| route별 분리 관리 | Warm 데이터와 Cold 데이터는 성격이 다르므로 별도 지표로 관리 |
| 중복 방지 | 동일 작품이 여러 번 입력되면 병합 또는 대표 라벨 하나만 사용 |
| 동의 기반 학습 | 사용자가 학습 활용에 동의한 데이터만 학습 후보로 승격 |
| 재현 가능성 유지 | 학습에 사용된 입력 스냅샷과 피처 생성 버전을 항상 저장 |
| 기존 성능 보호 | 신규 데이터 반영 모델이 기존 fixed test를 크게 악화시키면 배포하지 않음 |

## 5. 데이터 수집 종류

### 5.1 예측 이벤트 데이터

예측 이벤트 데이터는 사용자가 가격 예측을 요청할 때마다 저장한다. 이 데이터는 정답 가격이 없기 때문에 즉시 학습 라벨은 아니다.

| 항목 | 설명 | 학습 사용 |
|---|---|---|
| 입력 작품 정보 | 작가명, 작품명, 제작연도, 크기, 매체, 지지체, 작품 유형 | 라벨 없음. 피처 분석용 |
| 작가 매칭 결과 | artist_key, 매칭 점수, 후보 수, 동명이인 위험 | 라우팅/매칭 품질 개선용 |
| Warm/Cold route | 어떤 경로로 예측했는지 | route 분포 모니터링 |
| 예측 결과 | 예측가격, 가격범위, 신뢰도 | 실제 판매가 입력 시 오차 계산 기준 |
| 피처 스냅샷 | 면적, 크기 구간, 매체 구간, Quantile 폭 등 | 재현 및 원인 분석 |
| 모델 버전 | `price_prediction_v0.2`, 내부 Warm/Cold 구성 버전 | 버전별 성능 추적 |

### 5.2 사용자 보완 입력 데이터

보완 입력은 예측 정확도를 높이기 위해 사용자가 나중에 추가하는 정보다. 가격 라벨이 아니므로 단독으로 supervised learning에는 사용하지 않는다.

| 보완 입력 | 활용 방식 |
|---|---|
| 제작연도 추가 | 다음 예측 시 작품 시기 피처 개선 |
| 매체/지지체 정정 | 재료 구간 피처 개선 |
| 작품 이미지/URL 추가 | 중복 검수, 이미지 피처 후속 실험 후보 |
| 작가 생년/국적 보완 | Cold 작가 메타 피처 개선 |
| 전시/갤러리 이력 보완 | Cold 검색/활동성 피처 후보 |

### 5.3 실제 판매가 데이터

실제 판매가는 모델 학습에 직접적인 정답 라벨이 될 수 있다. 다만 검수 조건을 통과해야 한다.

| 항목 | 설명 |
|---|---|
| 실제 판매가 | 사용자가 입력한 실제 거래 가격 |
| 통화 | KRW, USD, EUR 등 |
| 원화 환산 가격 | 판매일 기준 또는 서비스 기준 환율로 환산 |
| 판매일 | 거래가 발생한 날짜 |
| 판매 채널 | 갤러리, 개인 거래, 경매, 온라인 플랫폼 등 |
| 거래 유형 | 실제 판매, 제안가, 호가, 감정가 구분 |
| 증빙 상태 | 영수증, 계약서, 플랫폼 기록, 운영자 확인 등 |
| 학습 활용 동의 | 모델 학습에 사용할 수 있는지 여부 |

## 6. 데이터 품질 등급

### 6.1 품질 점수 계산

운영 데이터는 품질이 섞여 들어오므로 학습 반영 전에 점수화한다.

```text
운영데이터품질점수 =
  0.30 * 판매가격증빙점수
+ 0.25 * 작가매칭신뢰도점수
+ 0.20 * 작품정보완성도점수
+ 0.15 * 판매채널신뢰도점수
+ 0.10 * 중복검수통과점수
```

| 점수 항목 | 계산 기준 |
|---|---|
| 판매가격증빙점수 | 증빙 있음 1.0, 부분 증빙 0.6, 자기 신고만 있음 0.3, 없음 0.0 |
| 작가매칭신뢰도점수 | v0.2 작가 매칭 점수 사용 |
| 작품정보완성도점수 | 필수 입력과 권장 입력의 충족률 |
| 판매채널신뢰도점수 | 검증 가능한 채널 1.0, 제한 검증 0.6, 불명확 0.2 |
| 중복검수통과점수 | 중복 없음 1.0, 병합 필요 0.5, 중복 제외 0.0 |

### 6.2 학습 후보 승격 기준

```text
학습후보승격 =
  (실제판매가_원화 > 0)
  AND (학습활용동의 = true)
  AND (검수상태 = approved)
  AND (운영데이터품질점수 >= 0.80)
  AND (중복상태 != duplicate_excluded)
```

| 상태 | 의미 | 학습 반영 |
|---|---|---|
| `raw_collected` | 입력만 수집됨 | 불가 |
| `needs_review` | 검수 필요 | 불가 |
| `approved` | 검수 완료 | 조건 충족 시 가능 |
| `rejected` | 신뢰 불가 | 불가 |
| `duplicate_merged` | 중복 병합됨 | 대표 row만 가능 |
| `training_candidate` | 학습 후보 확정 | 다음 재학습 후보 |
| `training_holdout_candidate` | 검증용 후보 확정 | 학습에는 넣지 않고 신규 holdout으로 보관 |

## 7. Warm/Cold별 학습 반영 방식

### 7.1 Warm 데이터

Warm은 같은 작가의 가격 이력이 충분한 경우에 사용된다. 따라서 신규 실제 판매가가 들어오면 같은 작가 기준가격과 유사작품 통계 품질을 개선하는 데 효과가 크다.

| 반영 대상 | 설명 |
|---|---|
| 같은 작가 가격 이력 | artist_key별 가격 이력 수 증가 |
| 유사작품 통계 | 같은 작가/매체/크기 구간의 중앙값, 사분위수, 표본 수 갱신 |
| 기준가격 생성 | Warm 기준 로그가격 생성 근거 강화 |
| 보정 위험도 | Quantile 폭, 유사작품 가격 분산, 표본 수 기반 위험도 재계산 |

Warm 재학습 후보는 아래 조건을 우선으로 한다.

```text
Warm학습후보 =
  학습후보승격
  AND (작가매칭신뢰도점수 >= 0.90)
  AND (artist_key 존재)
  AND (작품정보완성도점수 >= 0.80)
```

### 7.2 Cold 데이터

Cold는 같은 작가 가격 이력이 부족하거나 작가 매칭이 불확실한 작품에 적용된다. Cold 운영 데이터는 신규/저이력 작가의 가격 패턴을 보강하는 데 중요하다.

| 반영 대상 | 설명 |
|---|---|
| 작품 물리 피처 | 크기, 면적, 가로세로비, 깊이, 3D 여부 |
| 매체/지지체 피처 | medium/support 조합별 가격 패턴 |
| 작가 메타 | 생년, 국적, 활동성, 작품 수, 팔로워 수 |
| 검색/활동성 피처 | 전시, 갤러리, 미술관, 작가명 검색 문맥 |
| 과대예측 방어 | 실제 오차를 보고 Quantile 폭/낮은쪽 40% 기준 방어 조건 재검증 |

Cold 재학습 후보는 아래 조건을 우선으로 한다.

```text
Cold학습후보 =
  학습후보승격
  AND (가로_cm 존재)
  AND (세로_cm 존재)
  AND (매체 존재)
  AND (지지체 존재)
```

## 8. 데이터베이스 테이블 기획

### 8.1 `price_prediction_events`

예측 요청 1건마다 생성되는 기본 로그 테이블이다.

| 필드 | 타입 예시 | 설명 |
|---|---|---|
| `prediction_id` | string | 예측 요청 고유 ID |
| `created_at` | datetime | 예측 시각 |
| `model_version` | string | `price_prediction_v0.2` |
| `warm_model_version` | string | Warm 내부 모델 버전 |
| `cold_model_version` | string | Cold 내부 모델 버전 |
| `route` | string | warm/cold/review_required |
| `display_policy` | string | price_with_range/reference_range_only |
| `artist_key` | string/null | 내부 작가 식별자 |
| `artist_match_score` | float | 작가 매칭 신뢰도 |
| `same_artist_training_price_count` | int | 같은 작가 사용 가능 가격 이력 수 |
| `input_snapshot_json` | json | 사용자 입력 원본 |
| `feature_snapshot_json` | json | 예측에 사용한 파생 피처 |
| `prediction_price_krw` | int/null | 예측 가격 |
| `range_low_krw` | int/null | 가격 범위 하단 |
| `range_high_krw` | int/null | 가격 범위 상단 |
| `confidence_level` | string | high/medium/low |
| `calculation_summary_json` | json | 사용자 설명용 계산 요약 |

### 8.2 `price_prediction_feedback`

예측 이후 사용자가 입력한 실제 판매가와 보완 정보를 저장한다.

| 필드 | 타입 예시 | 설명 |
|---|---|---|
| `feedback_id` | string | 피드백 고유 ID |
| `prediction_id` | string | 연결된 예측 ID |
| `submitted_at` | datetime | 입력 시각 |
| `actual_sale_price` | float/null | 입력 통화 기준 판매가 |
| `actual_sale_currency` | string/null | 판매 통화 |
| `actual_sale_price_krw` | int/null | 원화 환산 판매가 |
| `sale_date` | date/null | 판매일 |
| `sale_channel` | string/null | 판매 채널 |
| `sale_type` | string | actual_sale/offer_price/listing_price/appraisal |
| `evidence_status` | string | none/partial/verified |
| `additional_input_json` | json | 추가 입력/정정 정보 |
| `user_consent_for_training` | bool | 학습 활용 동의 |
| `review_status` | string | raw_collected/needs_review/approved/rejected |
| `reviewer_note` | text/null | 운영 검수 메모 |

### 8.3 `training_candidate_labels`

검수 완료 후 학습 후보로 승격된 라벨 테이블이다.

| 필드 | 타입 예시 | 설명 |
|---|---|---|
| `candidate_id` | string | 학습 후보 ID |
| `prediction_id` | string | 원 예측 ID |
| `feedback_id` | string | 원 피드백 ID |
| `route_at_prediction` | string | 예측 당시 warm/cold |
| `artist_key` | string/null | 작가 식별자 |
| `actual_price_krw` | int | 학습 라벨 |
| `actual_log_price` | float | `log(actual_price_krw)` |
| `quality_score` | float | 운영데이터품질점수 |
| `training_eligible` | bool | 학습 사용 가능 여부 |
| `holdout_reserved` | bool | 신규 holdout 보관 여부 |
| `feature_snapshot_json` | json | 당시 피처 |
| `source_model_version` | string | 예측 당시 모델 버전 |

### 8.4 `model_training_runs`

재학습 실행 단위의 메타데이터를 저장한다.

| 필드 | 설명 |
|---|---|
| `training_run_id` | 재학습 실행 ID |
| `started_at`, `finished_at` | 실행 시간 |
| `base_model_version` | 기준 모델 |
| `candidate_model_version` | 후보 모델 |
| `training_dataset_version` | 학습 데이터셋 버전 |
| `new_training_candidate_count` | 신규 학습 후보 수 |
| `holdout_count` | 신규 holdout 수 |
| `warm_metrics_json` | Warm 검증 지표 |
| `cold_metrics_json` | Cold 검증 지표 |
| `release_decision` | promote/reject/needs_review |
| `decision_reason` | 승격 또는 보류 사유 |

## 9. API 기획

### 9.1 예측 API 응답에 포함할 피드백 토큰

`POST /api/v2/artworks/price-estimate` 응답에는 실제 판매가 입력을 연결할 수 있는 정보를 포함한다.

```json
{
  "prediction_id": "pred_20260611_000001",
  "model_version": "price_prediction_v0.2",
  "route": "cold",
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
  }
}
```

### 9.2 실제 판매가 입력 API

```text
POST /api/v2/feedback/sale-price
```

요청 예시:

```json
{
  "prediction_id": "pred_20260611_000001",
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

응답 예시:

```json
{
  "feedback_id": "fb_20260611_000001",
  "prediction_id": "pred_20260611_000001",
  "status": "received",
  "review_status": "needs_review",
  "message": "실제 판매가가 접수되었습니다. 운영 검수 후 학습 후보 데이터로 반영될 수 있습니다."
}
```

### 9.3 보완 입력 API

```text
PATCH /api/v2/predictions/{prediction_id}/additional-input
```

역할:

- 예측 이후 사용자가 누락 정보를 보완
- 같은 prediction_id에 입력 스냅샷을 추가 저장
- 실제 판매가가 없으면 학습 라벨로는 사용하지 않음
- 다음 예측 재계산 또는 운영 검수에 사용

## 10. 오차 계산과 운영 성능 추적

실제 판매가가 들어오면 예측 당시 결과와 비교해 운영 오차를 계산한다.

```text
실제로그가격 = log(실제판매가_KRW)

로그오차 = 실제로그가격 - 예측로그가격

절대비율오차_APE =
  abs(실제판매가_KRW - 예측가격_KRW) / 실제판매가_KRW
```

| 지표 | 설명 |
|---|---|
| `APE` | 개별 예측의 실제 판매가 대비 오차율 |
| `MdAPE` | 여러 예측의 APE 중앙값 |
| `MAPE` | 여러 예측의 APE 평균값 |
| `p95 APE` | 큰 오차 상위 5% 지점 |
| `log_error` | 로그가격 기준 오차 방향 |
| `coverage` | 실제 판매가가 예측 범위 안에 들어왔는지 |

운영 모니터링은 route별로 나눠야 한다.

| 구분 | 확인 지표 |
|---|---|
| Warm | APE, 범위 적중률, 같은 작가 이력 수별 오차 |
| Cold | APE, p95 APE, 낮은 신뢰도 비율, 최소 입력 누락률 |
| 작가 매칭 | 매칭 실패율, 동명이인 후보율, 수동 검수율 |
| 사용자 입력 | 보완 입력률, 실제 판매가 입력률, 학습 동의율 |

## 11. 재학습 주기

### 11.1 v0.2 권장 운영 주기

| 주기 | 작업 |
|---|---|
| 실시간 | 예측 이벤트 저장, 입력 품질 검사, 피드백 접수 |
| 매일 | 중복 후보, 이상 가격, 작가 매칭 실패 목록 생성 |
| 매주 | 운영자 검수, 학습 후보 승격, 데이터 품질 리포트 |
| 매월 | 신규 학습 후보가 충분하면 재학습 후보 실험 실행 |
| 분기 | 모델 버전 승격 여부 판단 |

### 11.2 재학습 실행 조건

재학습은 일정 기간마다 무조건 실행하기보다 데이터가 충분히 쌓였을 때 실행한다.

| 조건 | 권장 기준 |
|---|---|
| 전체 신규 학습 후보 | 300건 이상 |
| Warm 신규 후보 | 같은 작가 가격 이력 보강 데이터 100건 이상 |
| Cold 신규 후보 | 신규/저이력 작가 데이터 200건 이상 |
| 신규 holdout 후보 | 최소 50건 이상 |
| 특정 구간 큰 오차 누적 | 같은 원인 구간에서 p95 APE 악화 반복 |

## 12. 재학습 검증 절차

새 데이터가 들어와도 기존 모델을 바로 교체하지 않는다. 아래 순서로 검증한다.

```text
[학습 후보 데이터셋 생성]
        |
        v
[중복/이상치 제거]
        |
        v
[train / validation / 신규 holdout 분리]
        |
        v
[기준 모델 재현]
        |
        v
[후보 모델 재학습]
        |
        v
[기존 fixed test 평가]
        |
        v
[신규 운영 holdout 평가]
        |
        v
[route별 성능 비교]
        |
        v
[배포 여부 결정]
```

### 12.1 승격 기준

| 기준 | 통과 조건 |
|---|---|
| 재현성 | 기존 기준 모델 지표가 저장값과 동일하게 재현 |
| 기존 fixed test | 기존 Warm/Cold 주요 지표를 심하게 악화시키지 않음 |
| 신규 운영 holdout | 신규 데이터에서 MAPE 또는 p95 APE 개선 |
| Warm 안정성 | 같은 작가 이력 수가 적은 구간에서 p95 악화 없음 |
| Cold 안정성 | Cold low-confidence 구간에서 과신 증가 없음 |
| 라우팅 안정성 | Warm/Cold route 비율 급변 없음 |
| 설명 가능성 | 계산 설명과 사용 피처가 API 응답에 유지됨 |

### 12.2 배포 보류 조건

| 조건 | 판단 |
|---|---|
| 신규 데이터에서는 좋아졌지만 기존 fixed test가 크게 악화 | 보류 |
| 전체 MAPE는 좋아졌지만 p95 APE가 악화 | 목적별 후보로만 보류 |
| Cold high confidence가 실제로 더 틀림 | 신뢰도 정책 배포 금지 |
| 특정 작가/채널 데이터가 과도하게 많음 | 가중치 조정 또는 샘플링 필요 |
| 실제 판매가 증빙이 부족함 | 학습 제외 |

## 13. 프론트 화면 반영

### 13.1 예측 결과 화면

예측 결과 화면에는 학습 루프와 연결되는 입력 유도 문구를 넣는다.

| 화면 요소 | 내용 |
|---|---|
| 예측가격 | Warm/Cold 경로별 가격 또는 범위 |
| 계산 설명 | 어떤 입력과 피처가 사용됐는지 표시 |
| 부족 정보 | 제작연도, 매체, 지지체, 작가 정보 등 누락 항목 |
| 정보 추가 버튼 | 보완 입력 API로 연결 |
| 실제 판매가 입력 버튼 | 피드백 API로 연결 |
| 학습 활용 동의 | 실제 판매가 입력 시 별도 체크 |

### 13.2 Cold 화면 문구

Cold는 정확도 보장 모델이 아니므로 화면에서 아래처럼 안내한다.

```text
이 가격은 입력 정보 기반 예상 가격입니다.
같은 작가의 충분한 가격 이력이 없거나 작가 정보가 제한적인 경우,
작품 크기, 매체, 지지체, 작가 정보, 검색 문맥을 이용해 계산합니다.
정확 감정가 또는 판매 보장 가격은 아닙니다.
```

### 13.3 실제 판매가 입력 문구

```text
이 작품의 실제 판매가를 알고 있다면 입력해 주세요.
입력된 판매가는 운영 검수 후 향후 가격 예측 모델 개선에 활용될 수 있습니다.
학습 활용에 동의하지 않아도 예측 기록 관리에는 사용할 수 있습니다.
```

## 14. 운영자 검수 화면

운영자 검수 화면은 학습 후보 승격을 결정하는 내부 화면이다.

| 기능 | 설명 |
|---|---|
| 예측 기록 조회 | prediction_id 기준 입력값, 피처, 예측 결과 확인 |
| 실제 판매가 확인 | 판매가, 통화, 판매일, 판매 채널 확인 |
| 작가 매칭 확인 | artist_key, 후보, 매칭 점수, 동명이인 여부 확인 |
| 중복 검사 | 작품명, 작가, 크기, 이미지/URL 기반 중복 확인 |
| 가격 이상치 표시 | 예측가 대비 실제가 차이가 큰 row 표시 |
| 학습 후보 승인 | `training_eligible=true` 전환 |
| holdout 지정 | 일부 신규 검수 데이터를 학습하지 않고 평가용으로 보관 |

## 15. v0.2 구현 단계

| 순서 | 작업 | 산출물 |
|---:|---|---|
| 1 | 예측 이벤트 저장 스키마 정의 | `price_prediction_events` |
| 2 | v0.2 예측 API에 `prediction_id`, `feedback` 응답 추가 | API 응답 확장 |
| 3 | 실제 판매가 입력 API 추가 | `/api/v2/feedback/sale-price` |
| 4 | 보완 입력 API 추가 | `/api/v2/predictions/{prediction_id}/additional-input` |
| 5 | 운영자 검수 상태 모델 정의 | review status enum |
| 6 | 학습 후보 승격 배치 작성 | `training_candidate_labels` 생성 job |
| 7 | 운영 성능 집계 배치 작성 | route별 APE/MAPE/p95 리포트 |
| 8 | 재학습 후보 데이터셋 export 작성 | train/validation/holdout split export |
| 9 | 재학습 검증 리포트 템플릿 작성 | 후보 모델 비교 리포트 |
| 10 | 모델 버전 승격 체크리스트 작성 | promote/reject decision record |

## 16. v0.2에서 바로 해야 할 것과 나중에 할 것

### 16.1 v0.2에서 바로 포함

- 예측 이벤트 저장
- 입력 스냅샷 저장
- 피처 스냅샷 저장
- 실제 판매가 입력 API
- 학습 활용 동의
- 운영자 검수 상태
- 학습 후보 승격 기준
- route별 운영 성능 집계
- 재학습 후보 export

### 16.2 v0.2 이후 단계

- 자동 재학습 실행
- 자동 모델 승격
- 이미지 피처 기반 재학습
- 외부 검색 자동 수집과 동명이인 검수 자동화
- 작가/작품 지식베이스 자동 확장

v0.2에서는 자동 재학습보다 안전한 데이터 축적 구조를 먼저 완성하는 것이 우선이다.

## 17. 최종 운영 정의

v0.2의 운영 학습 구조는 아래 한 문장으로 정의한다.

```text
price_prediction_v0.2는 예측 결과를 제공하는 동시에,
예측 당시의 입력값·피처·모델 버전·결과를 저장하고,
검수된 실제 판매가만 학습 후보 데이터로 승격하여
다음 모델 재학습과 검증에 사용할 수 있게 하는 운영형 가격 예측 구조다.
```

