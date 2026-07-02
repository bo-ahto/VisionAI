# PP-CBOOST2 이종 blend 안정화 요약

- 실행일: 2026-06-10 / 스크립트: `scripts/track6/run_pp_cboost2_cold_hetero_blend_stabilization.py` / 폴더: `experiments/track6/PP-CBOOST2_cold_hetero_blend_stabilization/`
- 목적: CBOOST1의 이종 blend(LGB 5-seed + 선형 Huber·그룹통계) 신호를 MdAPE 희생 없이 안정화. C 강화 = `grp_price_proxy`(비교군 면적단가 중앙값 + log_area) 추가. 합의 게이트/cap/w 격자. 0604 미사용.

## 결과: 보류(강한 후보) — 세션 내 Cold 최강, 단 공식 게이트 미통과

대표 후보 `w0.3_none_capinf` (B 0.7 + 강화C 0.3, 전 행):

| 축 | 결과 |
|---|---|
| validation (vs B) | MdAPE **-0.00003(비악화 달성)** / MAPE -0.0245 / p95 -0.0248 |
| pseudo-cold | **3 seed 전부 MAPE 개선 방향 일치** |
| fixed test (1회) | **3지표 전부 개선**: 0.4857→0.4823 / 1.2138→**1.1787** / 4.2175→**3.6613** |
| bootstrap 게이트 | p_MAPE 0.8675 / p_p95 0.7625 / p_MdAPE 0.2475 → **미통과** (기준 0.90/0.90/0.50) |

- C 강화(price proxy)가 CBOOST1 대비 MdAPE 문제를 point 기준 해소(+0.009→-0.000). 그러나 작가 재표집 반복에서의 일관성은 0.87/0.76으로 부족 — 작가 구성에 따라 이득이 출렁임.
- 합의 게이트(agree_q50/q67)는 역효과(개선 축소), cap도 이득만 깎음 — 무제한 전행 blend가 최선.

## 판정과 의미

- **운영 base(v0.2) 교체는 불가** (게이트 미통과). 단 증거의 무게(val 비악화+개선, pseudo 3/3, test 3지표)는 이번 세션 Cold에서 유일하며, **"수집 없이 확보된 가장 유망한 Cold 후보"**로 등재.
- Warm의 경험칙으로는 PP148 채택 직전 단계(반복 안정성 보강 필요)에 해당.

## 후속 (PP-CBOOST3, Cold 재개 1순위 갱신)

① C 다중 구성 평균(피처 subset/alpha 변형 앙상블)으로 분산 축소 ② w 미세 grid(0.2~0.35) ③ artist 80%/70% holdout 직접 게이트(재학습 포함) ④ 통과 시 v0.2 교체 + CBASE 재lock + guard/tier 재적합.
