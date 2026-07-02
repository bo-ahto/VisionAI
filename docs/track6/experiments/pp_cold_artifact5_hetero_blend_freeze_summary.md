# PP-COLD-ARTIFACT5 이종 blend 운영 옵션 동결 (v0.5)

- 실행일: 2026-06-10 / 채택: 사용자 결정(p95 방어 목적)
- freeze: `scripts/track6/freeze_cold_prediction_artifact_v0_5.py` / 번들: `models/track6/cold_prediction_v0.5_operational/`

## 동결 내용

- 레시피(PP-CBOOST3 w0.3): **0.7 × LGB Quantile 5-seed 평균(900est) + 0.3 × 선형 Huber 6구성 앙상블**(비작가 그룹통계 사다리 + grp_price_proxy), q40 guard(blend 전 B 기준 label-free 분위수).
- 직렬화: LGB 20개 + Huber 6개 joblib(비추적, freeze로 재생성·해시는 MANIFEST 기록) + **그룹통계 사다리 테이블 JSON**(full-train 동결, 신규 행 raw-input 추론 가능) + blend/guard params + 정책 JSON.
- C 학습은 fold-제외 내부 통계(자기가격 leakage 차단), 추론은 동결 사다리 — CBOOST3 레시피와 동일.

## 검증

- 동봉 예측기 test 재현 vs PP-CBOOST3 fixed test: **diff ≤ 4.4e-16** (3지표 모두).
- 사다리 테이블 추론 ≡ 실험 코드 merge 추론: diff 행 0.

## 성능과 정직한 위치

| | MdAPE | MAPE | p95 |
|---|---|---|---|
| 동결 v0.2 defense | 0.4852 | 1.1771 | 4.1223 |
| **v0.5 blend defense** | **0.4822** | 1.1790 (동등) | **3.6490 (-11.5%)** |

- **목적별(p95 방어) 옵션**이며 all-metric 교체가 아님 — MdAPE 반복 비악화 확률 0.12~0.28(PP-CBOOST3)을 정책 JSON honest_note에 명시.
- 기본 서빙은 v0.3(점 예측)+v0.4(정책층) 유지. v0.5는 **raw-input(search 불가) 환경의 p95 방어 모드** — v0.2를 대체하는 선택지.
- 기존 원칙 유지: 0604 사용 금지, v0.2/v0.5 단독 환경 tier 표시 금지.

## Cold artifact 최종 현황

v0.1(guard) / v0.2(search-free 기본) / v0.3(점 예측 최고) / v0.4(정책층, fallback 활성) / **v0.5(raw-input p95 방어 blend, 채택 동결)**
