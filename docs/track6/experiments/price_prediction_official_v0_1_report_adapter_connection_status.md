# 보고서 기준 Warm/Cold 최종 adapter 연결 상태

- 작성일: 2026-06-12
- 공식 서비스 버전: `price_prediction_v0.1`
- 기준 보고서: `docs/track6/experiments/partner_warm_cold_best_model_report.md`

## 1. 결론

- 보고서 기준 최종 Warm/Cold 모델을 서비스에서 사용하려면 최종 계산층뿐 아니라 raw 입력 상류 adapter가 필요하다.
- 현재 v0.1 API에는 최종 계산층 파일의 import 검증과 raw 호환 partial refreeze proxy adapter를 연결했다.
- 현재 `/api/v1/artworks/price-estimate`의 가격은 `report_final_layer_proxy` 단계 결과다.
- Warm은 저장된 방향 분류/Huber 잔차 모델을 실제 호출하고, PP252 기준/안정 후보값은 기존 운영 Warm 후보값으로 보수 매핑한다.
- Cold는 저장된 LightGBM Quantile/q40/qwidth segment 보정 후보를 실제 호출하고, row-level Cold feature store가 적중하면 실험 당시 입력 피처를 그대로 재사용한다.
- Cold row-level feature store는 `artwork_url` 또는 `source_artwork_id` 기준으로 조회하며, fixed-test 3,099건에서 exact feature/prediction parity를 통과했다.
- Cold 신규 입력용 외부 데이터는 바로 feature cache에 넣지 않고, `external_feature_review_queue`에서 중복/개선 여부를 검수한 뒤 승인 후보만 승격하는 구조로 분리했다.
- proxy adapter는 서비스 흐름 테스트용 1차 연결이다. 단, Cold fixed-test 행처럼 feature store에 존재하는 행은 실험 입력과 동일한 재현 경로를 사용한다.
- Warm/Cold 모두 일부 상류 모델은 refreeze 후보로 저장했고 fixed-test parity를 확인했다.
- 보고서 기준 최종 가격으로 완전 승격하려면 남은 raw feature 생성 adapter를 연결한 뒤, 서비스 입력 기준 parity 검증이 필요하다.

## 2. Warm 연결 상태

| 항목 | 내용 |
|---|---|
| 서비스 표시명 | 이력 기반 예측 |
| 보고서 기준 모델 | 기준가격 기반 미세 보정 모델 |
| 최종 계산층 파일 | `experiments/track6/SUB-WARM-PP258_operational_fixed_test_submission/scripts/pp258_reproduce_fixed_test.py` |
| 최종 계산층 상태 | `calculate_pp258_predictions`, `MODEL_PARAMS` import 확인 |
| raw 호환 proxy adapter 상태 | 연결 |
| 정확 상류 adapter 상태 | 부분 refreeze 완료, 전체 raw adapter 미연결 |
| 현재 API warning | `WARM_REPORT_PROXY_ADAPTER_APPLIED` |

### 2.1 Warm 최종 계산층 요구 컬럼

| 컬럼 | 의미 | 서비스 raw 입력에서 만들어야 하는 값 |
|---|---|---|
| `pp252_log` | 미세 보정 전 기준 로그가격 | 같은 작가 가격 이력, 유사작품 통계, 작품 크기/재료/지지체를 반영한 기준 후보 |
| `pp252_stability_log` | 안정성 우선 기준 로그가격 | p95 방어와 반복 안정성을 더 중시한 기준 후보 |
| `prob_hist35_pp252` | 기준가격보다 실제 가격이 높을 확률 | 방향 분류 모델 또는 동일한 방향 확률 생성기 |
| `resid_huber_pp252` | Huber 잔차 보정 후보 | 기준가격의 남은 오차를 이상치에 둔감하게 추정한 값 |
| `quantile_width` | 예측 불확실성 폭 | 가격 하단/중앙/상단 후보의 폭 |
| `l10_price_range_ratio` | 가격 범위 비율 | 가격 상단과 하단의 상대 폭 |
| `component_prediction_spread` | 후보 모델 간 예측 차이 | 기준 후보, 안정 후보, 보조 후보 사이의 로그가격 차이 |
| `confidence_tier` | 신뢰도 구간 | 작가 매칭, 표본 수, 예측 폭 기반의 high/medium/low 구간 |
| `svc_group_n` | 유사작품 통계 표본 수 | 선택된 유사작품 그룹의 사용 가능 가격 이력 수 |

### 2.2 Warm 최종 계산식 요약

```text
최종 Warm 로그가격
  = pp252 기준 로그가격
  + 적용 보정 로그값

적용 보정 로그값
  = clip(
      Huber 잔차 보정 후보
      * 방향 일치 여부
      * 방향 확신도 기반 적용 강도
      * 0.025,
      -동적 보정 상한,
      +동적 보정 상한
    )

동적 보정 상한
  = 방향별 기본 상한
  * (1 - 0.55 * 예측 불확실성 폭 순위)
  * (1 - 0.80 * row 위험도)

최종 Warm 예측가격
  = exp(최종 Warm 로그가격)
```

### 2.3 현재 v0.1 partial refreeze proxy 매핑

```text
proxy 기준 로그가격
  = 기존 운영 Warm 70:30 로그가격

기존 운영 Warm 70:30 로그가격
  = 0.70 * 유사작품통계 기반 로그가격
  + 0.30 * 운영 안정 후보 로그가격

운영 안정 후보 로그가격
  = 0.75 * 방어형 후보 로그가격
  + 0.25 * L10 순차 보정 로그가격

부분 재동결 Huber 잔차 후보
  = 저장된 Huber 잔차 모델(
      가격대,
      신뢰도 구간,
      Quantile 폭,
      유사작품 표본 수,
      후보 간 gap feature
    )
  단, 서비스 입력 분포 방어를 위해 로그 기준 ±0.8 안으로 제한

부분 재동결 방향 확률
  = 저장된 방향 분류 모델(
      가격대,
      신뢰도 구간,
      Quantile 폭,
      유사작품 표본 수,
      후보 간 gap feature
    )

proxy 최종 Warm 로그가격
  = PP258 최종층(
      proxy 기준 로그가격,
      운영 안정 후보 로그가격,
      부분 재동결 방향 확률,
      부분 재동결 Huber 잔차 후보,
      L10 Quantile 폭,
      유사작품 표본 수
    )
```

- proxy 목적: raw 입력에서 보고서 최종층까지 이어지는 서비스 흐름 검증
- 현재 서비스 호출 완료: `prob_hist35_pp252` 방향 분류 모델, `resid_huber_pp252` Huber 잔차 모델
- 남은 한계: `pp252_log`, `pp252_stability_log`를 원시 입력에서 만드는 직전 기준 후보 생성 adapter 필요

## 3. Cold 연결 상태

| 항목 | 내용 |
|---|---|
| 서비스 표시명 | 참고 예측 |
| 보고서 기준 모델 | 검색 피처 포함 Quantile 예측 + 과대예측 방어 + 작가 검색 보정 |
| 최종 후처리 파일 | `models/track6/cold_prediction_v0.3/predict/apply_cold_postprocess_v0_3.py` |
| 최종 후처리 상태 | `apply`, `load_params`, `load_search_lookup` import 확인 |
| raw 호환 proxy adapter 상태 | 연결 |
| 정확 상류 adapter 상태 | 주요 모델 refreeze 완료, 검색 snapshot adapter 연결, 작가 단위 전시/갤러리 cache 연결, row-level feature store fixed-test parity 통과 |
| 현재 API warning | `COLD_REPORT_PROXY_ADAPTER_APPLIED` |

### 3.1 Cold 최종 후처리 요구 컬럼

| 컬럼 | 의미 | 서비스 raw 입력에서 만들어야 하는 값 |
|---|---|---|
| `y18_qwidth_pred_log` | 대표 로그가격 후보 | 검색 피처 포함 대표 가격 후보 |
| `lgb_q40_pred_log` | 낮은 쪽 Quantile 로그가격 | LightGBM Quantile 40% 지점 후보 |
| `quantile_width_log` | 예측 가격 범위 폭 | 상단/하단 Quantile 후보 사이의 로그 폭 |
| `artist_key` | 작가 식별자 | 작가 매칭 결과 또는 신규 작가 fallback 키 |

### 3.2 Cold 최종 계산식 요약

```text
대표 로그가격
  = y18_qwidth_pred_log

과대예측 방어 로그가격
  = 조건 충족 시
      (1 - 방어가중치) * 대표 로그가격
      + 방어가중치 * LightGBM Quantile 40% 로그가격
    조건 미충족 시
      대표 로그가격

검색 보정 로그값
  = 작가 검색 보정 lookup[artist_key]
    단, lookup이 없으면 0

최종 Cold 로그가격
  = 과대예측 방어 로그가격 + 검색 보정 로그값

최종 Cold 예측가격
  = exp(최종 Cold 로그가격)
```

### 3.3 현재 v0.1 partial refreeze proxy 매핑

```text
저장 LightGBM Quantile q10/q50/q90
  = 저장된 PP-Y2 검색 포함 LightGBM Quantile 모델(
      작품 크기,
      재료,
      지지체,
      작가 메타,
      검색/전시/갤러리 피처
    )
  검색 피처: 공식 v0.1 DB의 artist_search_feature_snapshots에서 작가키 또는 정규화 작가명으로 조회
  전시/갤러리 피처: 공식 v0.1 artist external feature cache에서 작가키 또는 정규화 작가명으로 조회

저장 LightGBM q40
  = 저장된 QR1 LightGBM Quantile 40% 모델(
      작품 크기,
      재료,
      지지체,
      파생 bucket
    )

qwidth segment 보정 대표 로그가격
  = q50 로그가격 + clip(segment_correction[qwidth_bin], -0.25, +0.25)

proxy 예측 폭
  = 저장 LightGBM Quantile q90 로그가격
  - 저장 LightGBM Quantile q10 로그가격

proxy 최종 Cold 로그가격
  = v0.3 guard+search 후처리(
      qwidth segment 보정 대표 로그가격,
      저장 LightGBM q40 로그가격,
      proxy 예측 폭,
      artist_key
    )
```

- proxy 목적: raw 입력에서 Cold guard+search 후처리까지 이어지는 서비스 흐름 검증
- 현재 서비스 호출 완료: PP-Y2 검색 포함 LightGBM Quantile q10/q50/q90, QR1 LightGBM q40, PP-Y16 qwidth segment 보정 map
- 현재 추가 연결 완료: `artist_search_feature_snapshots` 기반 검색 피처 조회, `official_v0_1_artist_external_feature_cache.csv` 기반 전시/갤러리 피처 조회
- 현재 추가 연결 완료: `official_v0_1_cold_feature_store.csv` 기반 row-level feature replay. `artwork_url` 또는 `source_artwork_id`가 일치하는 fixed-test 행은 실험 입력 피처와 예측값이 동일하게 재현됨
- 현재 추가 연결 완료: 외부 검색/전시/갤러리/판매가 후보를 `external_feature_review_queue`에 모아 중복 후보와 개선 후보를 분류하는 검수 큐
- 현재 추가 연결 완료: 승인된 작가 단위 외부 피처만 모아 `approved_external_feature_cache_candidate.csv`를 만드는 promotion dry-run
- 현재 추가 연결 완료: 작가명 fallback에서 `__MISSING__` 같은 placeholder 이름을 제외해 외부 피처 cache 오매칭 방어
- 남은 한계: feature store에 없는 신규 작품은 검색/전시/갤러리 피처를 새로 수집한 뒤 검수 승인된 후보만 운영 cache로 승격하는 pipeline이 필요함
- 신규/미보유 작가는 search lookup이 없어 `search_delta=0`으로 처리

### 3.4 Cold 외부 피처 검수 게이트

```text
외부 수집 후보
  -> 정규화
  -> 중복 판정
  -> 개선 판정
  -> external_feature_review_queue 저장
  -> 승인 후보만 feature cache 승격
```

| 항목 | 현재 상태 |
|---|---:|
| 검수 큐 전체 후보 | 2,982 |
| 승인 baseline 후보 | 712 |
| 개선 수집 필요 후보 | 1,075 |
| 사람 검수 필요 후보 | 724 |
| 자동 중복 제외 후보 | 470 |
| 승격 dry-run 후보 | 712 |
| 승격 차단 후보 | 2,270 |
| 작가 단위 외부 피처 cache 승격 후보 | 638 |
| 작가 단위 외부 피처 cache 승격 차단 | 1,135 |
| 승격 전 예측 영향 감사 대상 | 1,773 |
| 전체 예측 변화 row | 1,134 |
| 전체 외부 피처 coverage 상실 row | 1,135 |
| 전체 p95 절대 변화율 | 5.58% |

- 같은 작가 내 반복 URL은 `auto_reject_duplicate`로 제외한다.
- 여러 작가에 같은 URL이 반복되거나 정규화 작가명이 여러 artist_key에 매핑되면 `needs_human_review`로 둔다.
- 검색 품질 점수, 전시/갤러리 evidence, 출처 수가 부족하면 `needs_improvement`로 둔다.
- 실제 판매가 feedback은 `needs_review`로 저장하고, 검수 승인 후 학습 후보로 승격한다.
- 운영 원칙: `approved_baseline` 또는 검수자가 `approved`로 확정한 후보만 feature cache 승격 대상이다.
- 승격 gate dry-run 감사 결과, 중복/검수대기/개선필요 후보가 승격 대상에 섞이지 않았고 위반 건수는 0건이다.
- 작가 단위 외부 피처 cache promotion dry-run 결과, 기존 1,773건 중 승인 후보 638건만 승격 후보 cache에 포함됐다.
- 전체 영향 감사 결과, 차단 후보가 빠지는 경우 외부 피처 coverage 상실과 예측 변동이 확인됐다.
- 현재 단계에서는 승격 후보 목록과 후보 cache만 생성하며, 운영 feature cache는 아직 수정하지 않는다.
- 승인 후보 cache를 바로 적용하면 1,135건의 외부 피처 coverage가 사라지므로, 실제 적용은 보류하고 차단 후보 보강/검수를 먼저 진행한다.

## 4. 다음 연결 작업

| 순서 | 작업 | 완료 기준 |
|---|---|---|
| 1 | Warm proxy adapter 연결 | 완료 |
| 2 | Cold proxy adapter 연결 | 완료 |
| 3 | Warm 방향/Huber 상류 refreeze | 완료 |
| 4 | Warm 부분 refreeze adapter 서비스 호출 | 완료 |
| 5 | Warm PP252 기준/안정 후보 raw adapter 구현 | 사용자 입력 1건에서 `pp252_log`, `pp252_stability_log` 생성 |
| 6 | Cold PP-Y2/QR1/PP-Y16 상류 refreeze | 완료 |
| 7 | Cold 부분 refreeze adapter 서비스 호출 | 완료 |
| 8 | Cold 검색 snapshot feature adapter 연결 | 완료 |
| 9 | Cold 전시/갤러리 작가 단위 feature cache 연결 | 완료 |
| 10 | Cold fixed-test feature parity 감사 | 완료. row-level feature store 기준 exact feature/prediction parity 통과 |
| 11 | Cold 운영 feature store builder 구축 | 완료. 32,766건 feature store 생성 |
| 12 | Cold 신규 입력 cache/default feature pipeline 감사 | 완료. 4개 모드 3회 반복 deterministic 통과 |
| 13 | Warm/Cold fixed-test parity 검증 | Cold 완료. Warm은 PP252 기준/안정 후보 raw adapter 연결 후 추가 검증 필요 |
| 14 | 동일 입력 반복 검증 | 같은 입력 반복 시 같은 가격과 같은 계산 단계 반환 |
| 15 | 화면 표시 정리 | DB/cache 기준가격과 보고서 최종가격을 혼동 없이 표시 |
| 16 | Cold 외부 피처 검수 큐 | 완료. 2,982건 후보 중 중복/개선/사람 검수 필요 상태 분류 |
| 17 | Cold 외부 피처 승격 gate 감사 | 완료. dry-run 후보 712건, 차단 후보 2,270건, 위반 0건 |
| 18 | Cold 작가 단위 외부 피처 promotion dry-run | 완료. 승인 후보 cache 638건 생성, 운영 cache 미수정 |
| 19 | Cold 외부 피처 promotion 전체 영향 감사 | 완료. 1,773건 전체, p95 절대 변화율 5.58%, coverage 상실 1,135건 |
| 20 | Cold live feature collection pipeline | feature cache에 없는 작가의 검색/전시/갤러리 피처를 review queue에 저장 |
| 21 | Cold 승인 후보 cache 실제 적용 판단 | 보류. 차단 후보 보강/검수 후 재감사 필요 |

## 5. 현재 API에서 확인할 수 있는 항목

```text
GET /api/v1/price-models/current
```

- 최종 계산층 파일 존재 여부
- raw 상류 adapter 준비 여부
- Warm/Cold 요구 컬럼 목록

```text
GET /api/v1/admin/model-audit
```

- DB/cache row 수
- 최종 계산층 파일 존재 여부
- fixed-test parity 검증 여부
- 동일 입력 반복 검증 여부

```text
POST /api/v1/artworks/price-estimate
```

- 현재 계산 단계
- 보고서 최종층 proxy adapter 적용 warning
- proxy adapter 입력 컬럼
- 정확 상류 adapter에서 아직 parity 검증이 필요한 컬럼 목록

## 6. 1차 검증 결과

### 6.1 직접 호출 검증

| 구분 | 입력 예시 | 결과 |
|---|---|---|
| Warm | 박서보, 72.7 x 60.6cm, painting/canvas | `route=warm`, `adapter_execution_level=report_final_layer_proxy`, `partial_refreeze_adapter_used=true` |
| Cold 검색 snapshot 있음 | 정직성, 72.7 x 60.6cm, painting/canvas | `route=cold`, `adapter_execution_level=report_final_layer_proxy`, `partial_refreeze_adapter_used=true`, `search_feature_pipeline_ready=true`, `external_feature_pipeline_ready=true` |
| Cold 전시/갤러리 cache 있음 | 장아브여르, 72.7 x 60.6cm, painting/canvas | `route=cold`, `adapter_execution_level=report_final_layer_proxy`, `partial_refreeze_adapter_used=true`, `search_feature_pipeline_ready=false`, `external_feature_pipeline_ready=true` |
| Cold 검색/외부 cache 없음 | 신규작가테스트, 72.7 x 60.6cm, painting/canvas | `route=cold`, `adapter_execution_level=report_final_layer_proxy`, `partial_refreeze_adapter_used=true`, `search_feature_pipeline_ready=false`, `external_feature_pipeline_ready=false` |

### 6.2 HTTP 검증

| 항목 | 결과 |
|---|---|
| `/api/v1/health` | `success` |
| `/api/v1/price-models/current` | Warm/Cold partial refreeze readiness = `true`, Cold row feature store = `true`, Cold 신규 입력 cache/default pipeline = `true`, exact raw adapter = `false` |
| Warm 가격 예측 | `WARM_REPORT_PROXY_ADAPTER_APPLIED`, `partial_refreeze_adapter_used=true` |
| Cold 가격 예측, 검색 snapshot 있음 | `COLD_REPORT_PROXY_ADAPTER_APPLIED`, `partial_refreeze_adapter_used=true`, `search_feature_pipeline_ready=true`, `external_feature_pipeline_ready=true` |
| Cold 가격 예측, 전시/갤러리 cache 있음 | `COLD_REPORT_PROXY_ADAPTER_APPLIED`, `partial_refreeze_adapter_used=true`, `search_feature_pipeline_ready=false`, `external_feature_pipeline_ready=true` |
| Cold 가격 예측, 검색/외부 cache 없음 | `COLD_REPORT_PROXY_ADAPTER_APPLIED`, `partial_refreeze_adapter_used=true`, `search_feature_pipeline_ready=false`, `external_feature_pipeline_ready=false` |

### 6.3 동일 입력 반복 검증

| 구분 | 반복 횟수 | 가격 동일 | prediction_id 동일 | 실행 수준 |
|---|---:|---|---|---|
| Warm | 3회 | 예, 13,218,987원 | 예, `pred_fb4efdbca4dd730b7e0f` | `report_final_layer_proxy` |
| Cold 검색 snapshot 있음 | 3회 | 예, 7,614,532원 | 예, `pred_37f30ea09f7b72c61c3f` | `report_final_layer_proxy` |
| Cold 전시/갤러리 cache 있음 | 3회 | 예, 2,558,577원 | 예, `pred_1a40172dc4dc9deac836` | `report_final_layer_proxy` |
| Cold 검색/외부 cache 없음 | 3회 | 예, 2,310,325원 | 예, `pred_dcadb4ce106fca1de8da` | `report_final_layer_proxy` |

## 7. exact adapter readiness 감사

감사 스크립트:

```text
python3 scripts/track6/audit_official_v0_1_exact_adapter_readiness.py
```

감사 결과:

| 구분 | final-layer fixed-test replay | 부분 상류 refreeze | exact raw adapter | 판단 |
|---|---|---|---|---|
| Warm | 가능 | 완료 | 미완료 | 방향 분류/Huber 잔차는 저장 가능. PP252 기준/안정 후보 생성 adapter가 남아 있음 |
| Cold | 가능 | 완료 | 미완료 | PP-Y2/QR1/PP-Y16 주요 모델은 저장 가능. row-level feature store 기준 fixed-test exact parity 통과. 신규 입력 cache/default feature pipeline은 deterministic 통과. live collection pipeline은 별도 필요 |

결과 파일:

```text
docs/track6/experiments/price_prediction_official_v0_1_exact_adapter_readiness.md
docs/track6/experiments/price_prediction_official_v0_1_exact_adapter_readiness.json
```

API 반영:

- `/api/v1/price-models/current`
  - `warm_final_layer_fixed_test_replay_ready=true`
  - `warm_partial_upstream_refreeze_ready=true`
  - `cold_final_layer_fixed_test_replay_ready=true`
  - `cold_partial_upstream_refreeze_ready=true`
  - `cold_search_snapshot_feature_adapter_ready=true`
  - `cold_external_feature_cache_ready=true`
  - `cold_external_feature_cache_rows=1773`
  - `cold_row_feature_store_ready=true`
  - `cold_new_input_cache_feature_pipeline_ready=true`
  - `cold_live_external_collection_pipeline_ready=false`
  - `warm_exact_raw_adapter_ready=false`
  - `cold_exact_raw_adapter_ready=false`
- `/api/v1/admin/model-audit`
  - 동일 상태를 audit check로 표시

## 8. Cold feature parity 감사

감사 스크립트:

```text
python3 scripts/track6/audit_official_v0_1_cold_feature_parity.py
```

감사 결과:

| 항목 | 값 |
|---|---:|
| fixed-test row 수 | 3,099 |
| fixed-test 작가 수 | 200 |
| 공식 전시/갤러리 cache 작가 수 | 1,773 |
| fixed-test와 전시/갤러리 cache 작가 교집합 | 0 |
| 공식 검색 snapshot 작가 수 | 150 |
| fixed-test와 검색 snapshot 작가 교집합 | 0 |
| row-level Cold feature store hit rate | 1.0000 |
| exact feature parity | 통과 |
| exact prediction parity | 통과 |

성능 영향:

| 항목 | 실험 feature 기준 | 서비스 feature 기준 |
|---|---:|---:|
| MdAPE | 0.409820 | 0.409820 |
| MAPE | 0.849260 | 0.849260 |
| p95 APE | 2.346465 | 2.346465 |
| RMSE log | 0.850259 | 0.850259 |

판단:

- 현재 서비스 adapter는 실제 운영 입력에 대해 검색 snapshot과 전시/갤러리 cache를 조회할 수 있다.
- fixed-test 행은 row-level feature store에서 `artwork_url` 또는 `source_artwork_id`로 조회해 실험 당시 Cold 입력 피처를 그대로 재사용한다.
- fixed-test 3,099건 기준 exact feature parity와 exact prediction parity를 모두 통과했다.
- 신규 작품은 row-level feature store에 존재하지 않으므로, 공식 DB search snapshot, 작가 단위 전시/갤러리 cache, missing/default fallback 순서로 deterministic feature를 생성한다.
- cache에 없는 신규 작가의 검색/전시/갤러리 정보를 새로 수집·검수·저장하는 live collection pipeline은 별도 후속 단계다.

결과 파일:

```text
docs/track6/experiments/price_prediction_official_v0_1_cold_feature_parity_audit.md
docs/track6/experiments/price_prediction_official_v0_1_cold_feature_parity_audit.json
experiments/track6/PP-OFFICIAL-V01_cold_feature_parity_audit/outputs/
```

## 9. Cold 신규 입력 feature pipeline 감사

감사 스크립트:

```text
python3 scripts/track6/audit_official_v0_1_cold_new_input_pipeline.py
```

감사 결과:

| 항목 | 값 |
|---|---|
| 전체 deterministic | 통과 |
| 전체 feature input mode 기대값 일치 | 통과 |
| 검증 모드 | `row_feature_store_replay`, `service_search_external_cache`, `service_external_cache`, `service_default_missing` |

판단:

- row-level feature store 적중 행은 실험 입력 피처 재사용 경로를 탄다.
- 신규 입력 중 search snapshot과 전시/갤러리 cache가 있으면 해당 피처를 주입한다.
- 신규 입력 중 cache가 없으면 missing/default 피처로 계산하되, 같은 입력은 같은 결과를 반환한다.
- live 외부 수집은 아직 API 계산 경로에 직접 연결하지 않았다.

결과 파일:

```text
docs/track6/experiments/price_prediction_official_v0_1_cold_new_input_pipeline_audit.md
docs/track6/experiments/price_prediction_official_v0_1_cold_new_input_pipeline_audit.json
experiments/track6/PP-OFFICIAL-V01_cold_new_input_pipeline_audit/outputs/
```
