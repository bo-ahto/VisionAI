# PP-MONLIVE1 실서비스 매칭 로그 연동 + R5 실행 요약

- 작성일: 2026-06-13 / 스크립트: `scripts/track6/run_pp_monlive1_service_log_monitor.py` / 폴더: `experiments/track6/PP-MONLIVE1_service_log_monitor/`
- 데이터: `data/track6/service_v0_1/price_prediction_v0_1.sqlite` (실서비스 운영 DB). 합성 아님, 데이터 조작 없이 현재 상태 그대로.

## 연동 결과 (R1~R5, 실 라우팅 로그 637건)

| 검사 | 결과 | 판정 |
|---|---|---|
| R1 라우팅 규칙 위반 | 0건 | 정상 — 운영 라우팅이 0.80/이력 규칙 준수 |
| R2 트래픽 비중 | warm 97.2% / cold 1.4% / warm_lite 0.9% / review_required 0.5% | 초기 트래픽이 고이력 작가에 쏠림(warm_lite/cold 표본 적음) |
| R2 warm_lite k 분포 | k=4 0.67 / k=1 0.33 (n=6) | 표본 6건 — 분포 판단 보류 |
| R3 보조정보 무 구간(0.80~0.90) | 0.0 | 현재 warm은 전부 score 1.0(artist_key 직접일치), 보조정보 무 통과 사례 없음 |
| R4 warm_lite 성능 | 측정 불가 | 확정 판매 라벨 0건(원시 피드백 1건은 needs_review) < 최소 50 |
| R5 사전 밖 동명이인율 | 측정 불가(pending) | 검수 결정 0건 → proxy 5%(PP-RHO1) 유지, 대기 큐 92건 해소 시 측정 |

## 정직한 상태 진단

- **하니스↔실서비스 연동 자체는 검증 완료**: prediction_events/sale_price_feedback/identity_review 테이블을 모니터 스키마로 매핑해 R1~R5 전부 실행. R1(규칙 위반 0), R2(트래픽 분포)는 실데이터로 정상 산출.
- **R4/R5는 "측정 불가"가 정답**: 운영 초기라 ① 확정 판매 라벨 0건(피드백 1건도 미확정), ② 동명이인 검수 결정 0건(대기 92건). 라벨/결정이 쌓이기 전에는 성능·ρ를 실측할 수 없으며, 없는 값을 만들지 않고 proxy(5%)·동결 기준을 유지하는 것이 설계 의도.
- R5 산식: `ρ = 오매칭 결정 / 전체 해소 결정`, ρ > 16.7%(RMAP1 k≥5 허용 한계)면 임계 0.80 재검토 경보 — 구현·연결 완료, 데이터 대기 상태.

## 운영 트리거 (자동 측정 시작 조건)

- R4: 확정 판매 라벨이 warm_lite k별 50건 이상 누적되면 자동 측정·경보(MdAPE 한계 WCUT4×1.5).
- R5: `artist_identity_review_decisions`에 동명이인 검수 결정이 쌓이면 자동 ρ 실측 → proxy 5% 대체.
