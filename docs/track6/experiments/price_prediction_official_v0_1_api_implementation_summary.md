# 가격 예측 서비스 공식 테스트 v0.1 API 구현 요약

- 작성일: 2026-06-12
- 공식 버전: `price_prediction_v0.1`
- 구현 단계: DB/cache 기반 API + 보고서 최종층 raw 호환 proxy adapter 1차 연결 + Cold 검색/전시·갤러리 feature cache 연결 + 작가 식별자 이관 감사 큐 구축 + 외부 피처 검수 큐 구축

## 1. 구현 범위

- 공식 v0.1 전용 FastAPI server 추가
- 공식 v0.1 전용 Pydantic schema 추가
- 공식 v0.1 DB/cache 조회 service 추가
- `/test/v0.1` 로컬 테스트 화면 추가
- v0.2 입력 UX를 참고해 작가 확인 패널, 대표 작품 후보, 작품 기본 정보, 크기/재료, 고급 입력 접기 구조 적용
- 작가 후보 조회와 동명이인 확인
- 이력 기반 예측/참고 예측 route 판단
- DB/cache 기반 기준 가격 계산
- 보고서 기준 Warm/Cold 최종 계산층 raw 호환 proxy adapter 적용
- 유사작품/유사작가/시장 참고 가격 반환
- 계산 과정 응답과 DB 저장
- 실제 판매가 피드백 저장
- 동일 입력 반복 시 같은 예측 ID와 같은 가격 반환
- DB 이관 과정에서 동일 작가가 여러 `artist_key`로 분리된 후보 감사
- Cold 신규 외부 피처 후보는 바로 feature cache에 넣지 않고 검수 큐에서 중복/개선 여부를 먼저 판정

## 2. 구현 파일

| 파일 | 역할 |
|---|---|
| `src/visionai/price_engine/api/official_v0_1_schemas.py` | 공식 v0.1 API request/response schema |
| `src/visionai/price_engine/api/official_v0_1_service.py` | DB/cache 기반 작가 매칭, route 판단, 가격 근거 조회, 예측 저장 |
| `src/visionai/price_engine/api/official_v0_1_report_adapters.py` | 보고서 최종층 raw 호환 proxy adapter |
| `src/visionai/price_engine/api/official_v0_1_server.py` | 공식 v0.1 FastAPI endpoint |
| `src/visionai/price_engine/api/static/official_v0_1_test.html` | `/test/v0.1` 로컬 테스트 화면 |
| `data/track6/service_v0_1/price_prediction_v0_1.sqlite` | 공식 v0.1 local DB/cache |
| `data/track6/service_v0_1/official_v0_1_artist_external_feature_cache.csv` | Cold 전시/갤러리 작가 단위 feature cache |
| `data/track6/service_v0_1/official_v0_1_cold_feature_store.csv` | Cold fixed-test replay용 row-level feature store |
| `scripts/track6/audit_official_v0_1_exact_adapter_readiness.py` | 정확 상류 adapter readiness 감사 |
| `scripts/track6/build_official_v0_1_artist_external_feature_cache.py` | 기존 실험 row 피처를 공식 DB artist_key로 묶어 전시/갤러리 cache 생성 |
| `scripts/track6/build_official_v0_1_cold_feature_store.py` | Cold 실험 입력 피처를 row-level feature store로 생성 |
| `scripts/track6/audit_official_v0_1_cold_feature_parity.py` | Cold fixed-test feature/prediction parity 감사 |
| `scripts/track6/audit_official_v0_1_cold_new_input_pipeline.py` | Cold 신규 입력 feature mode와 반복 일관성 감사 |
| `scripts/track6/audit_official_v0_1_artist_identity_migration.py` | DB 이관 후 작가 식별자 분리/동명이인 후보 감사 |
| `scripts/track6/prioritize_official_v0_1_identity_and_external_review.py` | 작가 식별자 감사와 외부 피처 승격 영향도를 합친 검수 우선순위 산정 |
| `scripts/track6/build_official_v0_1_artist_identity_merge_dry_run.py` | P0/P1 동일 작가 분리 후보 canonical artist_key 병합 dry-run |
| `scripts/track6/build_official_v0_1_artist_identity_merge_shadow_db.py` | 병합 dry-run map을 shadow DB에 적용해 작가 후보/이력 수 영향 감사 |
| `scripts/track6/rebuild_official_v0_1_artist_identity_post_merge_caches.py` | 병합 shadow DB 기준 alias/profile/유사작품/유사작가/외부 피처 cache 재집계 dry-run |
| `scripts/track6/audit_official_v0_1_artist_identity_post_merge_prediction_impact.py` | 재집계 shadow DB 기준 병합 전후 resolve/route/가격 영향 감사 |
| `scripts/track6/build_official_v0_1_feature_review_queue.py` | Cold 외부 피처 후보 중복/개선 검수 큐 생성 |
| `scripts/track6/audit_official_v0_1_feature_review_gate.py` | 승인 후보만 cache 승격 대상으로 선별되는지 dry-run 감사 |
| `scripts/track6/promote_official_v0_1_approved_external_features.py` | 승인된 작가 단위 외부 피처만 모아 승격 후보 cache 생성. 기본은 dry-run |
| `scripts/track6/audit_official_v0_1_external_feature_promotion_impact.py` | 승인 후보 cache 적용 전 예측 영향 표본 감사 |
| `scripts/track6/build_warm_pp252_upstream_refreeze_candidate.py` | Warm PP252 일부 상류 refreeze 후보 생성 |
| `scripts/track6/build_cold_v03_research_upstream_refreeze_candidate.py` | Cold v0.3 연구 기준 일부 상류 refreeze 후보 생성 |
| `docs/track6/experiments/price_prediction_official_v0_1_exact_adapter_readiness.md` | readiness 감사 결과 |
| `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_migration_audit.md` | 작가 식별자 이관 품질 감사 결과 |
| `docs/track6/experiments/price_prediction_official_v0_1_identity_external_review_priority.md` | 작가 식별자/외부 피처 검수 우선순위 결과 |
| `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_merge_dry_run.md` | canonical artist_key 병합 dry-run 결과 |
| `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_merge_shadow.md` | 병합 shadow DB 영향 감사 결과 |
| `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_post_merge_cache_rebuild.md` | 병합 후 cache 재집계 dry-run 결과 |
| `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_post_merge_prediction_impact.md` | 재집계 shadow DB 기준 예측 영향 감사 결과 |
| `docs/track6/experiments/price_prediction_official_v0_1_live_feature_review_plan.md` | 외부 피처 중복/개선 검수 및 승격 정책 |

## 3. Endpoint

| Method | Endpoint | 상태 |
|---|---|---|
| `GET` | `/api/v1/health` | 구현 |
| `GET` | `/api/v1/price-models/current` | 구현 |
| `POST` | `/api/v1/artists/resolve` | 구현 |
| `POST` | `/api/v1/artworks/price-estimate` | 구현 |
| `GET` | `/api/v1/predictions/{prediction_id}` | 구현 |
| `POST` | `/api/v1/feedback/sale-price` | 구현 |
| `GET` | `/api/v1/admin/model-audit` | 구현 |
| `GET` | `/test/v0.1` | 구현 |

## 4. 현재 adapter 실행 수준

```text
adapter_execution_level = report_final_layer_proxy
```

- 현재 응답은 공식 v0.1 DB/cache 가격 근거를 유지하면서 보고서 최종 계산층을 raw 호환 partial refreeze proxy adapter로 1차 적용
- Warm은 기존 운영 Warm runtime이 생성하는 70:30 기준 후보, 안정 후보, Quantile 폭, 유사작품 표본 수를 PP258 최종층 입력으로 보수 매핑
- Warm의 방향 확률과 Huber 잔차는 저장된 refreeze 상류 모델을 실제 호출
- Cold는 저장된 LightGBM Quantile q10/q50/q90, LightGBM q40, qwidth segment 보정 후보를 v0.3 guard+search 후처리 입력으로 매핑
- Cold row-level feature store가 적중하면 실험 당시 입력 피처를 그대로 재사용
- Cold의 검색 피처는 공식 v0.1 DB의 `artist_search_feature_snapshots`에서 작가키 또는 정규화 작가명으로 조회
- Cold의 전시/갤러리 피처는 기존 실험 row 피처를 공식 DB의 작가키로 묶은 `official_v0_1_artist_external_feature_cache.csv`에서 조회
- Cold의 전시/갤러리 cache가 없는 작가는 missing/default로 처리
- Cold live 외부 수집 후보는 `external_feature_review_queue`를 거친 뒤 승인 후보만 cache 승격
- 승인 후보 승격 스크립트는 기본적으로 `approved_external_feature_cache_candidate.csv`만 만들고 운영 cache는 수정하지 않음
- 작가 식별자 이관 감사에서 동일 작가 분리 후보를 `artist_identity_review_queue`에 저장하며, 자동 병합은 하지 않음
- 동일 작가 분리 후보 검수가 끝나기 전에는 외부 피처 cache 실제 승격을 보류
- 작가명 fallback 매칭에서 `__MISSING__`, `missing`, `unknown` 같은 placeholder 이름은 제외해 다른 작가와 오매칭되지 않도록 방어
- 보고서 parity용 상류 모델 일부는 refreeze 후보로 저장 완료
- 정확한 보고서 parity용 전체 raw adapter는 아직 미완료
- API 응답 warning에 `WARM_REPORT_PROXY_ADAPTER_APPLIED` 또는 `COLD_REPORT_PROXY_ADAPTER_APPLIED`를 포함해 현재 상태를 명확히 표시

### 4.1 연결된 최종 계산층 파일

| 구분 | 연결 대상 | 상태 |
|---|---|---|
| Warm | `experiments/track6/SUB-WARM-PP258_operational_fixed_test_submission/scripts/pp258_reproduce_fixed_test.py` | 필수 함수 import 확인 |
| Cold | `models/track6/cold_prediction_v0.3/predict/apply_cold_postprocess_v0_3.py` | 필수 함수 import 확인 |

### 4.2 아직 필요한 raw 입력 adapter

| 구분 | 최종 계산층 요구 컬럼 | 현재 상태 |
|---|---|---|
| Warm | `pp252_log`, `pp252_stability_log`, `prob_hist35_pp252`, `resid_huber_pp252`, `quantile_width`, `l10_price_range_ratio`, `component_prediction_spread`, `confidence_tier`, `svc_group_n` | 방향 분류/Huber 잔차 refreeze 모델 서비스 호출 완료. PP252 기준/안정 후보 raw 생성 필요 |
| Cold | `y18_qwidth_pred_log`, `lgb_q40_pred_log`, `quantile_width_log`, `artist_key` | PP-Y2/QR1/PP-Y16 refreeze 모델 서비스 호출 완료. 검색 snapshot 조회 연결 완료. 전시/갤러리 작가 단위 cache 연결 완료. row-level feature store fixed-test parity 통과 |

### 4.3 proxy adapter 매핑

| 구분 | proxy 입력 생성 방식 | 정확한 parity 미완료 사유 |
|---|---|---|
| Warm | 기존 운영 Warm 70:30 기준 로그가격과 안정 후보 로그가격을 PP258 입력으로 매핑하고, 방향/잔차는 저장 모델 출력 사용 | PP252 기준 후보와 안정 후보를 원시 입력에서 생성하는 adapter가 아직 없음 |
| Cold | 저장된 LightGBM Quantile q50/q40/qwidth와 qwidth segment 보정값을 v0.3 후처리 입력으로 매핑. row-level feature store가 적중하면 실험 입력 피처를 그대로 재사용 | fixed-test feature store parity는 통과. 신규 입력의 검색/전시/갤러리 피처 생성 pipeline은 추가 필요 |

### 4.4 API 표시 정책

- `GET /api/v1/price-models/current`
  - 최종 계산층 파일 존재 여부 표시
  - raw 호환 proxy adapter 준비 여부 표시
  - Cold 검색 snapshot feature adapter 준비 여부 표시
  - Cold 전시/갤러리 feature cache 준비 여부 표시
  - 작가 식별자 이관 감사 큐 준비 여부와 동일 작가 분리 후보 수 표시
  - Cold 외부 피처 검수 큐 준비 여부와 검수 대기/중복 제외 수량 표시
  - Cold 외부 피처 승격 dry-run 결과와 실제 적용 여부 표시
  - raw 상류 adapter 준비 여부 표시
  - fixed-test final-layer replay 가능 여부 표시
  - exact raw adapter 준비 여부 표시
  - 필요한 상류 컬럼 목록 표시
- `GET /api/v1/admin/model-audit`
  - DB/cache row 수와 adapter 연결 상태를 함께 표시
  - readiness 감사 결과 파일 기준으로 Warm/Cold final-layer replay와 exact raw adapter 상태 표시
- `POST /api/v1/artworks/price-estimate`
  - 계산 단계 5번에 보고서 최종 adapter 연결 상태 표시
  - 현재 예측가격은 partial refreeze가 포함된 `report_final_layer_proxy` 단계 결과임을 warning으로 표시
  - `raw_proxy_adapter_ready=true`, `raw_upstream_adapter_ready=false`로 proxy와 정확한 상류 adapter를 분리 표시

## 5. 라우팅 기준

```text
이력 기반 예측 조건 =
  작가매칭점수 >= 0.90
  AND 같은작가가격이력수 >= 5
  AND 동명이인위험점수 < 0.60
```

- 조건 충족: `route = warm`, 화면 표시명 `이력 기반 예측`
- 조건 미충족: `route = cold`, 화면 표시명 `참고 예측`
- 동명이인 후보가 2명 이상이고 사용자가 작가를 선택하지 않음: `route = review_required`, 화면 표시명 `확인 필요`

## 6. 검증 결과

```text
python3 -m py_compile src/visionai/price_engine/api/official_v0_1_schemas.py src/visionai/price_engine/api/official_v0_1_service.py src/visionai/price_engine/api/official_v0_1_server.py
```

- Python 문법 검증 통과

FastAPI `TestClient` 검증:

| 항목 | 결과 |
|---|---|
| `/api/v1/health` | 200 OK |
| `/api/v1/artists/resolve` 박서보 | 후보 2명, `ARTIST_AMBIGUOUS` |
| 작가키 선택 후 `/api/v1/artworks/price-estimate` | 200 OK, `route=warm`, 계산 단계 5개 저장 |
| 신규 작가 `/api/v1/artworks/price-estimate` | 200 OK, `route=cold` |
| Warm proxy adapter | `adapter_execution_level=report_final_layer_proxy`, `WARM_REPORT_PROXY_ADAPTER_APPLIED` |
| Cold proxy adapter | `adapter_execution_level=report_final_layer_proxy`, `COLD_REPORT_PROXY_ADAPTER_APPLIED` |
| Cold 검색 snapshot feature adapter | HTTP 검증 기준 `search_feature_pipeline_ready=true` |
| Cold 전시/갤러리 feature cache | 1,773명 cache 생성, HTTP 검증 기준 `external_feature_pipeline_ready=true` |
| Cold fixed-test feature parity 감사 | row-level feature store 기준 3,099건 exact feature/prediction parity 통과 |
| Cold 신규 입력 feature pipeline 감사 | 4개 feature input mode, 3회 반복 deterministic 통과 |
| 작가 식별자 이관 품질 감사 | 충돌 alias 그룹 92건, 높은 확률의 잘못 분리 후보 68건, 자동 병합 미적용 |
| 작가 식별자/외부 피처 검수 우선순위 | 고유 작가키 묶음 기준 P0 최우선 병합 검수 40건, P1 병합 검수 19건, P2 사람 검수 22건 |
| canonical artist_key 병합 dry-run | 57개 component, 60개 source artist_key 이동 후보, 가격 이력 425건 재배치 후보, 실제 DB 미수정 |
| 병합 shadow DB 영향 감사 | P0/P1 component 57건 모두 단일 작가 후보로 정리, 기존 최대 이력 대비 425건 증가, 운영 DB 미수정 |
| 병합 후 cache 재집계 dry-run | alias 3,600->3,530, registry/profile 1,773->1,713, 유사작품 통계 9,421->9,285, 유사작가 8,388->8,212, 운영 DB 미수정 |
| 재집계 shadow DB 기준 예측 영향 감사 | 57건 모두 단일 resolve, alias review_required 57->0, direct 가격 변동 2건, 고영향 변동 1건은 자동 적용 보류 |
| Cold 외부 피처 검수 큐 | 2,982건 후보 분류, 중복/개선/사람 검수 필요 상태 저장 |
| Cold 외부 피처 승격 gate 감사 | 통과. 승격 dry-run 후보 712건, 승격 차단 후보 2,270건, 위반 없음 |
| Cold 작가 단위 외부 피처 cache 승격 후보 | 통과. 현재 cache 1,773건 중 승인 후보 638건, 차단 후보 1,135건, 운영 cache 미수정 |
| Cold 외부 피처 승격 전 예측 영향 감사 | 전체 1,773건 기준 변화 row 1,134건, coverage 상실 row 1,135건, p95 절대 변화율 5.58%, 운영 cache 미수정 |
| Warm final-layer replay readiness | 가능 |
| Cold final-layer replay readiness | 가능 |
| Warm partial upstream refreeze readiness | 완료 |
| Cold partial upstream refreeze readiness | 완료 |
| Warm exact raw adapter readiness | 미완료 |
| Cold exact raw adapter readiness | 미완료 |
| `/api/v1/predictions/{prediction_id}` | 200 OK, 계산 단계 재조회 |
| `/api/v1/feedback/sale-price` | 200 OK, `needs_review` 저장 |
| 동일 입력 2회 반복 | 같은 `prediction_id`, 같은 가격 |
| `/test/v0.1` 화면 | v0.2 흐름 기반 입력 UI, 인라인 JavaScript 문법 검증 통과 |

## 7. 로컬 실행

```text
PYTHONPATH=src uvicorn visionai.price_engine.api.official_v0_1_server:app --host 127.0.0.1 --port 8031
```

테스트 화면:

```text
http://127.0.0.1:8031/test/v0.1
```

Swagger:

```text
http://127.0.0.1:8031/docs
```

## 8. 다음 단계

- Warm PP252 기준/안정 후보 raw adapter 연결
- 작가 식별자 이관 감사 큐 68건 병합 후보 검수 및 canonical artist_key 적용 dry-run
- Cold live 외부 검색/전시/갤러리 수집·검수·저장 pipeline 구축
- Cold 승인 후보 promotion script의 실제 적용 전후 예측 영향 감사
- 신규 입력 반복/일관성 검증을 CI 또는 배포 전 점검 스크립트에 포함
- `/test/v0.1` 화면에서 최종 모델 adapter 준비 상태와 DB/cache 기반 임시 결과를 더 명확히 분리 표시
