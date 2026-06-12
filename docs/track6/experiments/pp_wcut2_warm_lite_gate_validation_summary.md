# PP-WCUT2 Warm-lite 게이트 검증 요약 — 통과

- 실행일: 2026-06-12 / 스크립트: `scripts/track6/run_pp_wcut2_warm_lite_gate_validation.py` / 폴더: `experiments/track6/PP-WCUT2_warm_lite_gate_validation/`
- 목적: PP-WCUT1의 min1 사다리 결과를 운영 반영 기준으로 검증 — 절단 seed 3개 × k∈{1,2,3,4} 전 조합 재학습, warm test 607행 artist-cluster bootstrap 400회.

## 결과: 전 조합 통과

- **12조합(3 seed × 4 k) 전부 Warm-lite가 Cold serving 대비 MdAPE/MAPE/p95 개선확률 ≥ 0.995** (최소값: k=2~4 p95 0.9975, k=1 p95 0.995).
- k=1도 게이트 통과 — 단 WCUT1에서 k=1 p95(1.62)가 k=2+(0.9~1.0)보다 약했으므로 운영 시 k=1 차등 cap 정책 여지는 유지.

## 판정

- **Warm-lite(고신뢰 매칭 + 이력 1~4건, 저표본 사다리 경로) 신설은 검증 통과.** 권고 구조 = 기존 파이프라인 유지 + 3-경로 라우팅(Warm 5+ / Warm-lite 1~4 / Cold).
- 전제 조건(PP-WMATCH1): 매칭 실제 정확도 ~85%+ 필요(오매칭 비용 비대칭) — 점수 캘리브레이션은 운영 매칭 로그 과제.
- 잔여 한계: 5+ 보유 작가의 절단 시뮬레이션(진짜 저이력 작가와 분포 차이 가능), 선형 proxy 기준 — 운영 반영 시 신규 트래픽 모니터링 전제.
