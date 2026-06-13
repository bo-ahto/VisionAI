# PP-MONTEST1 Warm-lite 모니터링 하니스 스모크 테스트

- 작성일: 2026-06-13
- 대상: `scripts/track6/monitor_warm_lite_routing.py` (routing_policy_v0.1 운영 과제 ②)
- 목적: 실운영 로그 연동 전, 하니스가 정상/위반 로그를 올바르게 구분하는지 합성 로그로 검증.

## 합성 로그 2종 (각 1,500행, 스키마: ts/artist_key/match_score/history_n/route/pred_price_krw/actual_price_krw)

- `log_clean.csv`: 라우팅 규칙 준수(cold/warm_lite 1~4/warm 5+), route별 성능을 동결 기준 부근으로 생성
- `log_violation.csv`: R1 위반 주입(warm_lite인데 history_n=6 8행, warm인데 score 0.7 6행) + R4 성능 악화(warm_lite k=2 예측 2배 오류)

## 결과 — 정상/위반 정확히 구분

| 검사 | 정상 로그 | 위반 로그 |
|---|---|---|
| R1 규칙 위반 | 0건 | 14건 경보 (주입 14건과 일치) |
| R2 트래픽 비중 | cold 0.46 / wlite 0.29 / warm 0.25 | wlite k 분포에 비정상 k=6 0.018 노출 |
| R3 보조정보 무 구간(0.80~0.90) | 0.277 | 0.268 |
| R4 warm_lite k별 MdAPE | 전 k ALERT false (0.074~0.104) | k=2 MdAPE 1.0 ALERT true (주입 악화 포착) |
| alerts | `["없음"]` | `["R1 14건", "R4 k=2 한계 초과"]` |

## 결론

- 하니스 동작 검증 완료: R1(규칙 위반 카운트), R4(k별 성능 경보 한계 WCUT4×1.5) 모두 의도대로 작동.
- 비정상 history_n(k=6)이 R2 k 분포에 노출돼 라우팅 오류의 2차 탐지 경로도 확인.
- 운영 연동 시 남은 작업: 실로그 스키마 매핑(컬럼명 일치) + R5(사전 밖 동명이인율, 오매칭 검수 결과 입력) 활성화. R5는 검수 라벨이 쌓여야 측정 가능.

## 산출물
- `outputs/log_clean.csv`, `outputs/log_violation.csv` (합성, 재생성 가능)
