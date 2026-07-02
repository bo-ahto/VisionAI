# Warm WMIN4 서비스 연결 상태 점검

- 작성일: 2026-06-12
- 대상 API: `price_prediction_v0.1`
- 로컬 확인 URL: `http://127.0.0.1:8031`

## 1. 적용 내용

- WMIN4 선택 후보 산출물 생성 완료.
- 산출물 위치: `models/track6/warm_wmin4_operational_candidate`
- 선택 후보: `min1_huber_refit_partial`
- 문서용 설명: 최소 1건 유사작품 통계 기준가와 partial Huber 잔차 보정을 결합한 Warm 후보.

## 2. 성능 지표

| 구간 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|---:|
| validation OOF | 519 | 0.101568 | 0.178407 | 0.571291 | 0.297318 |
| fixed test | 607 | 0.106598 | 0.239302 | 0.779196 | 0.376884 |

## 3. API 노출 상태

- `/api/v1/price-models/current`에 WMIN4 목표 후보 상태 노출 완료.
- `/api/v1/admin/model-audit`에 WMIN4 목표 후보 상태 노출 완료.
- `warm_wmin4_candidate_artifact_ready`: `true`
- `warm_wmin4_proxy_adapter_ready`: `true`
- `warm_wmin4_exact_raw_adapter_ready`: `false`
- `warm_wmin4_adapter_state`: `target_artifact_ready_but_exact_raw_adapter_pending`

## 4. 결정성 확인

- 같은 입력을 3회 반복 호출했을 때 핵심 결과가 동일함.
- 작가 선택 전 검수 경로 결과:
  - route: `review_required`
  - price: `3,315,300 KRW`
  - deterministic core: `true`
- 작가 키 `park seo bo` 선택 후 Warm 경로 결과:
  - route: `warm`
  - adapter execution level: `report_final_layer_proxy`
  - price: `13,218,987 KRW`
  - range: `4,477,426 ~ 15,222,028 KRW`
  - deterministic core: `true`

## 5. 중요한 해석

- 현재 신규 입력 예측값은 WMIN4 fixed-test 성능을 그대로 재현한 값으로 보지 않는다.
- 이유: 신규 입력 계산 경로는 아직 PP258 최종층 proxy adapter를 사용한다.
- WMIN4는 목표 운영 후보 산출물로 고정됐고, 현재 API는 해당 목표 후보와 미완료 상태를 명확히 노출한다.
- active DB registry는 기존 PP258 Warm 후보를 유지했다.
- 이유: WMIN4 exact raw adapter가 연결되기 전에 active registry를 교체하면 실제 신규 입력 계산 경로와 성능 지표가 불일치할 수 있다.

## 6. 다음 작업

- min1 유사작품 통계 기반 SVC payload를 raw 입력 서비스에서 생성 가능하게 저장.
- WMIN3 partial Huber refit 경로를 raw 입력 서비스에서 호출 가능하게 저장.
- fixed test row-level parity 검증을 API 경로로 수행.
- 동일 입력 반복, 순서 변경, cold/warm 라우팅 경계 케이스를 자동 테스트로 고정.
