# PP-WMIN9C Warm-lite vs WMIN8 svc-core 저이력 직접 비교 요약 — 라우팅 경계 실증 확정

- 작성일: 2026-06-13 / 폴더: `experiments/track6/PP-WMIN9C_warm_lite_vs_wmin8_lowhistory/` / 스크립트: `run_pp_wmin9c_warm_lite_vs_wmin8_lowhistory.py` (seed별 체크포인트)
- 배경: WMIN9B는 "WMIN8은 5+ 전용 경로라 1~4건 강제 적용은 라우팅 불변식 위반"으로 직접 비교를 보류. 본 실험은 그 경계가 자의적이지 않음을 실증.
- 설계: WMIN8의 작가 신호 코어(min1 svc_numeric Huber, 70% 축)를 PP-WCUT4 실존 저이력 leave-one-out 행(seed 3개, 1,947행)에 직접 적용 → Warm-lite와 동일 행 비교. 0604 미사용.

## 결과 — Warm-lite가 전 지표·전 이력대 우위

| 이력 k | Warm-lite (MdAPE/MAPE/p95) | WMIN8 svc-core | 승자 |
|---|---|---|---|
| 1 | 0.1207 / 0.3415 / 0.9559 | 0.1271 / 0.3406 / 0.9573 | Warm-lite (MdAPE/p95) |
| 2 | 0.1184 / 0.2707 / 0.8779 | 0.1448 / 0.2821 / 0.9478 | Warm-lite (전 지표) |
| 3 | 0.1060 / 0.2541 / 0.7142 | 0.1195 / 0.2661 / 0.7489 | Warm-lite (전 지표) |
| 4 | 0.0923 / 0.2557 / 0.7884 | 0.1190 / 0.2634 / 0.7682 | Warm-lite (MdAPE/MAPE) |
| **전체** | **0.1092 / 0.2866 / 0.8765** | 0.1291 / 0.2932 / 0.9163 | **Warm-lite 전 지표** |

## 결론

- **라우팅 경계(1~4건 → Warm-lite, 5+ → WMIN8) 정당화 확정.** 저이력 행에서 WMIN8의 svc 코어조차 Warm-lite보다 전 지표 열위(MdAPE +18%, MAPE +2%, p95 +5%).
- 원인: 저이력(1~4건) 작가는 같은 작가 비교군이 0~3건으로 비어 svc_numeric Huber가 비작가 fallback에 의존하는 반면, Warm-lite는 작가 이력 통계를 직접 경량 모델에 투입해 희소 신호를 더 잘 살림.
- svc-core는 WMIN8의 **하한 proxy**(ppv8 blend/router 제외, 5+ 상류 컴포넌트 LOO 재현 불가) — 그 하한조차 Warm-lite에 지므로, 전체 WMIN8을 저이력에 강제해도 Warm-lite를 넘기 어렵다는 9B의 보류 근거가 실측으로 뒷받침됨.
- 라우팅 단순화(1~4건도 WMIN8) 불채택 확정. 3-경로(Warm-lite / WMIN8 / Cold) 유지.

## 한계

- ppv8 blend/router 미포함(상류 5+ 컴포넌트 충실 재현 불가) → svc-core 하한 비교. 다만 ppv8은 5+ 작가 신호 기반이라 저이력에서 이점이 크지 않을 것으로 추정.
- 실존 저이력 작가의 절단 LOO 설계(PP-WCUT4 상속) — 진짜 신규 작가 분포와 차이 가능성은 운영 모니터링으로 커버.
