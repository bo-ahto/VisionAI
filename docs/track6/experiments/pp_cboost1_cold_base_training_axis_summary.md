# PP-CBOOST1 Cold base 학습 축 검증 요약

- 실행일: 2026-06-10 / 스크립트: `scripts/track6/run_pp_cboost1_cold_base_training_axis.py` / 폴더: `experiments/track6/PP-CBOOST1_cold_base_training_axis/`
- 대상: raw-input 운영 base 축(연구 base는 상류 동결). 게이트: validation 선택 + artist-cluster bootstrap(400) vs seed_mean + fixed test 1회. 0604 미사용.

## 결과 (defense 기준, val / test MAPE)

| 후보 | val MAPE | test MAPE | 판정 |
|---|---|---|---|
| ① B 5-seed 평균 | 0.6100 | 1.2138 | 기각 — 단일 seed(0.6094/1.2126)와 차이 없음 |
| ② HPO 3종 | 0.616~0.628 | 1.157~1.229 | 기각 — validation 전부 악화(lr06은 test-only 개선 = 채택 불가) |
| ③ C 선형 Huber+그룹통계 단독 | 0.6228 | 1.1732 | 단독 약함(예상대로) |
| **③+blend D w0.4 (B 0.6 + C 0.4)** | **0.5853** | **1.1717** (p95 4.22→3.92) | **보류(유망)** — 세션 최초 val+test 동방향 개선 |

## 핵심 발견

- **CCORR2의 가설("후보 다양성 부재가 병목") 입증**: 이종 계열(선형 Huber+그룹통계) 후보 하나를 추가하자 blend가 즉시 val/test 일관 개선(MAPE -4%/-3.5%, p95 개선).
- 단 게이트 미통과: bootstrap vs seed_mean — w0.4 p_MAPE 0.80/p_p95 0.77/**p_MdAPE 0.17** (MdAPE 0.383→0.392 일관 희생 = center-vs-tail 트레이드오프).
- ①시드 앙상블·②HPO는 깨끗이 기각 — base 학습 축에서 살아남은 것은 ③이종 다양성뿐.

## 후속 (Cold 재개 시 1순위)

PP-CBOOST2: C 모델 강화(그룹통계 선형 모델 개선) + MdAPE-guard blend(모델 합의 구간만 이동) + pseudo-cold 외부 검증 → 게이트 재도전. 통과 시 운영 base(v0.2) 교체 + CBASE 재lock.
