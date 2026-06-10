# PP-CBOOST3 이종 blend 게이트 재도전 요약 — CBOOST 라인 종결

- 실행일: 2026-06-10 / 스크립트: `scripts/track6/run_pp_cboost3_cold_hetero_blend_gate_retry.py` / 폴더: `experiments/track6/PP-CBOOST3_cold_hetero_blend_gate_retry/`
- 시도: C 6구성 앙상블(α/ε/피처셋 변형) 분산 축소 + w 미세 grid(0.20~0.35) + 적응 변형(최정밀 매칭 한정) + 이중 게이트(bootstrap 400 + artist subsample 80/70% 200회).

## 결과: 게이트 미통과 — 단 후보의 정체가 확정됨

대표 `w0.3` (val dMAPE -0.0242/dp95 -0.0231, test 1.2138→1.1790/p95 4.22→3.65, pseudo-cold 3/3):

| 게이트 축 | MAPE | p95 | MdAPE |
|---|---|---|---|
| bootstrap | 0.86 | 0.74 | 0.25 |
| subsample 0.8 | **0.98** | 0.86 | 0.12 |
| subsample 0.7 | **0.92** | 0.81 | 0.12 |

- **MAPE 개선은 반복 검증 통과 수준(0.91~0.98)으로 확립.** p95는 0.65~0.86, **MdAPE 비악화 확률 0.12~0.28은 C 앙상블/적응 w로도 개선 안 됨** — 선형 모델 방향 이동이 중앙을 미세하게 흔드는 구조적 center-vs-tail 트레이드오프.

## CBOOST 라인 종결 판정

1. **all-metric 운영 base 교체는 불가** (3회 시도로 구조적 확인). 추가 안정화 실험(CBOOST4+)은 기대값 낮음.
2. 후보의 정체 = **"MAPE/p95 방어 목적별 후보"** (Warm의 MAPE 특화 후보와 동일 범주). 수집 없이 확보 가능한 Cold 개선분: test MAPE -3.5%/p95 -13%, 대가 MdAPE +0.001~0.006.
3. **채택 여부는 서비스 목적 의사결정** (v0.4 상수 fallback과 같은 구조): 큰 오차 회피 우선이면 운영 base의 "p95 방어 모드"로 채택 가능 — 원하면 v0.2에 옵션 동결(ARTIFACT5) 가능.

## Cold 트랙 최종 좌표

- 전 지표 동시 개선: **검색 수집 확대만 가능** (미커버 MAPE 0.938→0.849).
- 수집 없는 목적별 개선: **이종 blend w0.3** (MAPE/p95, 의사결정 대기).
- 운영 현행: v0.3 점 예측 + v0.4 정책층(tier/2단 검수/미커버 상수 fallback 활성).
