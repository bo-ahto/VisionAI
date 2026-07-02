# 보고서 기준 모델 raw 입력 적용 gap 감사

- 작성일: 2026-06-12T13:17:50
- 기준 문서: `docs/track6/experiments/partner_warm_cold_best_model_report.md`

## 1. 요약

- Warm 기준 모델: Warm 기준가격 기반 미세 보정 모델
- Warm 패키지 유형: `fixed_test_reproduction_submission_candidate`
- Warm 범위 메모: This package reproduces the report model on the existing Warm fixed test split. It is not a raw blind-test inference API package.
- Cold 기준 모델: Cold 검색 피처 포함 Quantile 예측 + 과대예측 방어 + 작가 검색 보정
- Cold 상태: `validated_two_layer_defense_freeze`
- Cold 운영 메모: 후처리층만 실행 가능(component 예측 + artist_key 입력). 하부 Quantile/PP-Y18은 상류 참조. 검색 delta는 작가 단위 frozen snapshot(372 작가) — 신규 작가는 fallback(guard). 0604는 전부 warm(0 cold)이라 cold 운영 트래픽 확보 후 재평가 필요.
- 판단: 보고서 모델 raw-input 서비스 적용에는 상류 feature/model adapter와 DB/cache가 필요

## 2. 현재 아티팩트 확인

| 항목 | 경로 | 존재 | 유형 |
| --- | --- | --- | --- |
| warm_pp258_reproduce_script | experiments/track6/SUB-WARM-PP258_operational_fixed_test_submission/scripts/pp258_reproduce_fixed_test.py | 예 | file |
| warm_pp258_fixed_test_input | experiments/track6/SUB-WARM-PP258_operational_fixed_test_submission/data/pp258_model_input_validation_test.csv | 예 | file |
| warm_v01_raw_operational_root | models/track6/price_prediction_v0.1/operational | 예 | dir |
| cold_v03_postprocessor | models/track6/cold_prediction_v0.3/predict/apply_cold_postprocess_v0_3.py | 예 | file |
| cold_v03_search_delta_lookup | models/track6/cold_prediction_v0.3/config/search_delta_lookup_v0_3.json | 예 | file |
| cold_v02_raw_operational_root | models/track6/cold_prediction_v0.2_operational | 예 | dir |
| cold_v05_raw_operational_root_excluded | models/track6/cold_prediction_v0.5_operational | 예 | dir |

## 3. Warm required column gap

| 컬럼 | 의미 | raw 입력 의존 요소 | fixed-test 패키지 존재 | raw 실행 가능 | 필요 작업 |
| --- | --- | --- | --- | --- | --- |
| pp252_log | 미세 보정 전 기준 로그가격 | PP252 기준가격 생성 모델/로직 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| pp252_stability_log | 안정성 우선 기준 로그가격 | 안정성 후보 생성 모델/로직 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| prob_hist35_pp252 | 기준가 대비 실제가격 상승 방향 확률 | 방향 분류 모델 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| resid_huber_pp252 | Huber 잔차 보정 후보 | Huber 잔차 모델 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| quantile_width | 예측 불확실성 폭 | Quantile 범위 모델 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| l10_price_range_ratio | 가격 범위 비율 | Quantile 하단/상단 기반 계산 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| svc_group_n | 유사작품 통계 표본 수 | 유사작품 통계 DB/cache | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| component_prediction_spread | 후보 모델 간 예측 차이 | Warm 후보 예측값 생성기 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| confidence_tier | 신뢰도 구간 | 표본 수/예측 폭/매칭 신뢰도 정책 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |
| stable_price_band | 안정 가격대 구간 | 기준가격 bucket 정책 | 예 | 아니오 | 상류 feature/model adapter 구축 필요 |

## 4. Cold required column gap

| 컬럼 | 의미 | raw 입력 의존 요소 | v0.3 현재 보유 | raw 실행 가능 | 필요 작업 |
| --- | --- | --- | --- | --- | --- |
| y18_qwidth_pred_log | 검색 피처 포함 대표 로그가격 | 검색 포함 LightGBM Quantile 대표 후보 | 일부/아니오 | 아니오 | 검색 포함 Quantile 상류 생성기 구축 필요 |
| lgb_q40_pred_log | 낮은쪽 40% 지점 로그가격 | LightGBM 40분위 모델 | 일부/아니오 | 아니오 | 검색 포함 Quantile 상류 생성기 구축 필요 |
| quantile_width_log | 예측구간폭 로그값 | LightGBM q10/q90 또는 상류 보강값 | 일부/아니오 | 아니오 | 검색 포함 Quantile 상류 생성기 구축 필요 |
| artist_key | 작가 검색 보정 lookup key | 작가 매칭/검색 기반 식별 | 일부/아니오 | 아니오 | 검색 포함 Quantile 상류 생성기 구축 필요 |
| search_delta_lookup | 작가별 검색 기반 보정값 | frozen lookup 또는 DB snapshot | 예 | 아니오 | DB/cache fallback 정책 연결 필요 |

## 5. 구현 순서

| 순서 | 작업 |
| --- | --- |
| 1 | Warm/Cold required column dependency 확정 |
| 2 | local DB/cache schema 생성 |
| 3 | Warm PP258 상류 feature/model adapter 구현 |
| 4 | Cold 검색 포함 Quantile 상류 adapter 구현 |
| 5 | 공식 테스트 v0.1 API와 테스트 화면 추가 |
| 6 | fixed-test parity 및 deterministic repeat 검증 |

## 6. 결론

- 보고서 기준 모델은 재현 가능하지만, 현재 상태 그대로 raw 입력 서비스에 붙일 수는 없음
- Warm은 PP258 입력 컬럼을 만드는 상류 adapter가 필요
- Cold는 검색 포함 Quantile 기준 예측을 만드는 상류 adapter가 필요
- DB/cache는 선택이 아니라 운영 적용을 위한 필수 기반
- 다음 구현은 local DB/cache schema와 adapter skeleton부터 진행하는 것이 맞음
