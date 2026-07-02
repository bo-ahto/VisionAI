# Warm WMIN4 운영 후보 아티팩트

- 작성일: 2026-06-12T20:53:11
- 서비스 버전: `price_prediction_v0.1`
- 문서용 모델명: 이력 기반 최소 1건 유사작품 Huber 보정 후보
- 내부 추적 ID: `WMIN4 min1 Huber refit partial`
- 선택 후보: `min1_huber_refit_partial`

## 1. 선택 결론

- WMIN4 반복 검증에서 기존 PP258 운영 후보보다 validation MAPE, p95 APE, fixed test MAPE가 함께 개선됨.
- fixed test 기준 MAPE는 0.239302로, 직전 운영 후보 0.269888 대비 0.030586 감소.
- fixed test 기준 p95 APE는 0.779196로, 직전 운영 후보 0.807325 대비 0.028129 감소.

## 2. 핵심 지표

| 구간 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|---:|
| validation OOF | 519 | 0.101568 | 0.178407 | 0.571291 | 0.297318 |
| fixed test | 607 | 0.106598 | 0.239302 | 0.779196 | 0.376884 |

## 3. 반복 검증 안정성

| 항목 | 값 |
|---|---:|
| validation MAPE 승률 | 0.996795 |
| validation p95 승률 | 0.980769 |
| validation all3 승률 | 0.965385 |
| validation replacement score | -0.027222 |

## 4. 운영 연결 상태

- 현재 상태: 선택 후보 산출물 고정 완료.
- 아직 불가: 신규 사용자 입력에서 WMIN4를 정확히 재현하는 raw-input adapter.
- 남은 연결: min1 유사작품 통계 기반 SVC payload 저장, partial Huber refit 경로 저장, API 고정 테스트 재현 검증.
