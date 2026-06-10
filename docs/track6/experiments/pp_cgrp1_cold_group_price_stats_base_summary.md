# PP-CGRP1 비교군 그룹 가격 통계 base 투입 요약

- 실험 ID: `PP-CGRP1` (Cold 개선 경로 ①)
- 실행일: 2026-06-10
- 목적: Warm 기준가 최강 피처군(비교군 가격 통계)의 작가 미사용 버전을 Cold base에 최초 투입 (PP-Y 라인 미검증 갭 확인 후 실행).
- 스크립트: `scripts/track6/run_pp_cgrp1_cold_group_price_stats_base.py`
- 폴더: `experiments/track6/PP-CGRP1_cold_group_price_stats_base/`

## 설계

- 매칭 사다리(작가 미사용): medium_support×size(min30) → medium+support+size(min30) → medium×size(min50) → 전체 fallback. validation 매칭율: L1 93.5%.
- leakage 차단: train 통계는 5-fold 자기 fold 제외, val/test/pseudo는 학습 train 전체 기준.
- 후보: base12 / +grp_full(8피처) / +grp_lean(4피처), LGB Quantile seed 3 평균.
- 게이트(base 재학습용 경량): validation 3지표 + artist-cluster bootstrap 400회 + pseudo-cold(PCOLD1 마스크 3 seed) 방향 + fixed test 1회.

## 결과: 기각 — validation 전 지표 악화

| 후보(defense) | validation MdAPE/MAPE/p95 | bootstrap 개선확률(MAPE/p95/MdAPE) |
| --- | --- | --- |
| base12 | 0.3823 / 0.6115 / 1.6341 | — |
| +grp_lean | 0.3852 / 0.6387 / 1.6953 | 0.02 / 0.32 / 0.37 |
| +grp_full | 0.4043 / 0.6422 / 1.7455 | 0.09 / 0.10 / 0.04 |

- pseudo-cold: lean이 3 seed 중 1개만 개선 — 외부 축에서도 일관성 없음.
- **test-only 관찰 (채택 불가, 기록만)**: test에서는 grp 후보가 MAPE/p95를 개선(defense 1.2030/4.2408 → lean 1.1779/3.9122, full 1.1859/3.7831)하고 MdAPE 악화. validation과 정반대 — Cold의 val↔test 작가 구성 분기가 다시 확인됨. "0604/test 단독 신호 승격 금지" 원칙(PP-V8 사례)에 따라 채택하지 않음.

## 해석

**그룹 가격 통계가 Warm에서 강력했던 이유는 base가 선형 Huber였기 때문**이다 — 선형 모델에는 그룹 중앙값이 새 정보다. Cold base는 LGBM이라 medium/support/size categorical 분기에서 같은 조건부 분포를 이미 내부적으로 학습하며, 명시적 통계 피처는 추가 정보 없이 분산(과적합 표면)만 늘린다. 경로 ①은 이 형태로는 닫힘. 변형 후보(선형 보조 모델 + 그룹 통계의 블렌드)는 기대값 낮아 보류.

## 산출물

- `outputs/candidate_metrics.csv`, `outputs/validation_artist_bootstrap.csv`, `outputs/pseudo_cold_metrics.csv`
- `artifacts/run_config.json`, `reports/result_report.md`
