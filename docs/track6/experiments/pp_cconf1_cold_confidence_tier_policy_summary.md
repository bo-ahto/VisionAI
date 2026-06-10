# PP-CCONF1 Cold 신뢰도 tier 정책 요약

- 실험 ID: `PP-CCONF1` (Cold 로드맵 Phase 2-1)
- 실행일: 2026-06-10
- 목적: Warm PP-CF1의 신뢰도 tier를 Cold에 이식. 점 예측은 바꾸지 않고, 정답 미사용 신호만으로 행 단위 tier를 정의해 서비스 표시 정책(점 예측/가격 범위/검수)의 근거를 만든다.
- 스크립트: `scripts/track6/run_pp_cconf1_cold_confidence_tier_policy.py`
- 폴더: `experiments/track6/PP-CCONF1_cold_confidence_tier_policy/`
- 입력: PP-CBASE1 고정 base CSV. tier 경계는 validation 분위수 동결(`artifacts/run_config.json`), test/pseudo-cold는 확인 전용. 0604 미사용.

## tier 정의 (정답 미사용)

| scheme | 신호 | 규칙 |
|---|---|---|
| **research** | qwidth(y18 체인) + 모델 gap(\|y18−v0.2\|) + 검색 lookup 커버 | low: qwidth≥val q90 OR gap≥val q90 / high: qwidth≤q33 AND gap≤q50 AND covered / 나머지 medium |
| **operational** | v0.2 qwidth 단독 (raw-input 환경에서 계산 가능한 신호만) | low: ≥val q90 / high: ≤val q33 / 나머지 medium |

## 결과 1 — research tier: 분리 유지, 채택 권고 (연구 base APE 기준)

| split | tier | share | MdAPE / MAPE / p95 |
|---|---|---:|---|
| validation | high | 14.8% | 0.2448 / 0.3400 / 0.9333 |
| validation | low | 19.2% | 0.4648 / 0.6551 / 1.6761 |
| **test** | **high** | 8.2% | 0.3828 / 0.6811 / **0.9904** |
| test | medium | 62.6% | 0.3709 / 0.9025 / 1.8243 |
| **test** | **low** | 29.2% | 0.5549 / 0.7824 / **2.9877** |

- **p95 분리가 test에서도 강하게 유지** (high 0.99 vs low 2.99; 전체 2.35). high tier는 "큰 오차가 거의 없는 구간"으로 표시 가치 충분.
- 단 test에서 medium의 MdAPE가 high보다 약간 낮고 MAPE 순서도 일부 섞임 → tier는 **p95(큰 오차 위험) 분리 정책**으로 쓰는 것이 정직하다. "high = 좁은 범위 표시 허용, low = 넓은 범위 + 검수"가 적정.

## 결과 2 — operational tier(v0.2 qwidth 단독): test에서 역전, 기각

| split | tier | 운영 base MAPE / p95 | 범위(q10~q90) 적중률 |
|---|---|---|---:|
| validation | high | 0.3906 / 0.8786 | 0.713 |
| **test** | **high** | **2.1045 / 8.3992** | **0.538** |
| test | medium | 0.7573 / 2.3283 | 0.740 |
| test | low | 1.2912 / 5.0946 | 0.794 |

- v0.2 qwidth가 좁은(=모델이 자신 있는) 행이 test에서 **최악의 MAPE/p95** — unseen 작가에서 "자신 있게 틀리는" 과신 신호임이 확인됨. 범위 적중률도 high tier에서 53.8%로 최저.
- **결론: raw-input 환경에서 v0.2 qwidth 단독 신뢰도 표시는 위험. 기각.** 운영 환경 신뢰도 신호는 추가 입력(검색 커버리지, 작가 메타, 이미지 등)이 확보돼야 가능 — Phase 2 신호 추가와 직결.

## 결과 3 — 외부 검증 및 기존 검수 플래그 비교

- **pseudo-cold(PP-PCOLD1) 방향 일치: seed 3개 모두 high < medium < low (MdAPE)** — tier 개념 자체는 신규 작가 상황에서도 유효. 단 real test의 operational tier 역전과 종합하면, pseudo-cold는 방향 검증용이지 과신 위험까지 잡아주지는 못함.
- 기존 v0.3 검수 플래그(qwidth≥q67 OR 미커버, test 45.2%) vs research low tier(29.2%): 겹침 19.6%. test에서 low tier의 평균 APE(0.782)가 v0.3 플래그(0.654)보다 높음 = **low tier가 더 적은 행으로 더 위험한 행을 찾음(정밀)**. 권고: v0.3 플래그(재현율 축) 유지 + low tier(정밀 축)를 "우선 검수" 등급으로 추가하는 2단 검수.

## 정책 권고 (점 예측 변경 없음)

1. **high (research tier)**: 점 예측 + 좁은 범위 표시 허용 (test p95 0.99).
2. **medium**: 점 예측 + 표준 범위(q10~q90, 적중률 ~74%).
3. **low**: 넓은 범위 강조 + 우선 검수. v0.3 플래그와 OR 결합으로 기존 검수율 유지.
4. v0.2 단독 환경에서는 tier 표시를 제공하지 않음 (과신 위험).

## 산출물

- `outputs/tier_metrics.csv`, `outputs/tier_assignments.csv`, `outputs/review_flag_comparison.csv`, `outputs/pseudo_cold_tier_metrics.csv`
- `artifacts/run_config.json` (동결 경계값), `reports/result_report.md`

## 다음 실험

- **PP-CIMG1 (Phase 2-2)**: 이미지 임베딩(CLIP ViT-B/32 캐시 보유 확인)을 CDIAG1 위험 구간(qwidth_extreme, 저행수 작가)과 low tier에 한정한 residual 보정으로 검증. pseudo-cold를 외부 검증 축으로 사용.
