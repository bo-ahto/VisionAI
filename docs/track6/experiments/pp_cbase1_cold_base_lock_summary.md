# PP-CBASE1 Cold 이중 base lock 요약

- 실험 ID: `PP-CBASE1`
- 실행일: 2026-06-10
- 목적: Cold 개선 로드맵(Phase 0)의 첫 단계로, 이후 모든 Cold 실험이 같은 기준에서 누적되도록 base 예측·residual target·채택 게이트를 고정한다.
- 로드맵: `docs/track6/experiments/cold_improvement_roadmap.md`
- 스크립트: `scripts/track6/run_pp_cbase1_cold_base_lock.py`
- 폴더: `experiments/track6/PP-CBASE1_cold_base_lock/`

## 고정 결정

1. **연구 base `COLD_BASE_RESEARCH_V1`** = v0.3 체인(PP-Y18 대표 + guard(PP-QR4) + 작가단위 검색 delta(PP-H28), 미커버 작가 → guard fallback). 컬럼 `research_base_pred_log`. residual target = `actual_log - research_base_pred_log`.
2. **운영 base `COLD_BASE_OPERATIONAL_V1`** = v0.2 search-free 직렬화 파이프라인의 guard 적용 서빙값(raw-input 실행 가능, 외부 API 0). 컬럼 `v02_defense_pred_log`. residual target = `actual_log - v02_defense_pred_log`.
3. 모든 후속 후보는 **두 base 대비 성적을 모두 보고**한다. 연구 base만 이기는 후보는 후처리층 한정 후보로 분류.
4. **0604 데이터는 Warm 시험 제출 전용 — Cold 실험 전 단계에서 사용 금지.**
5. 채택 게이트(1차): validation cold **작가 80%/70% holdout 각 ≥200회 — base 대비 MAPE 개선확률 ≥0.90 AND p95 개선확률 ≥0.90, MdAPE ≥0.50**. row subsample은 보조, fixed test는 최종 확인 1회.

## 고정 base 성능 (MdAPE / MAPE / p95_APE)

| candidate | validation (n=2,753) | test (n=3,099) |
| --- | --- | --- |
| component_pp_y2_baseline | 0.4129 / 0.5887 / 1.5042 | 0.4421 / 1.0484 / 3.3537 |
| component_pp_y18_qwidth_bin | 0.3656 / 0.5460 / 1.4000 | 0.4247 / 0.9910 / 3.3053 |
| guard_only_v0_1 | 0.3650 / 0.5182 / 1.3392 | 0.4178 / 0.9640 / 2.5377 |
| **COLD_BASE_RESEARCH_V1 (v0.3 guard+search)** | 0.3553 / 0.4978 / 1.4996 | **0.4098 / 0.8493 / 2.3465** |
| v02_representative_q50 | 0.3962 / 0.6633 / 1.7910 | 0.4823 / 1.2424 / 4.3806 |
| **COLD_BASE_OPERATIONAL_V1 (v0.2 defense)** | 0.3881 / 0.6169 / 1.6482 | **0.4852 / 1.1771 / 4.1223** |

- v0.3/v0.2 정책 JSON의 test 지표를 모두 재현(절대 오차 < 5e-4)해 lock 정합성 검증 통과.
- val→test 악화 폭이 큼(연구 base MAPE 0.498→0.849) = Cold의 작가 구성 의존이 그대로 드러남. fixed test 단독 신호를 신뢰하면 안 되는 근거.

## 작가 단위 구성 (artist holdout 게이트 설계 근거)

| split | rows | artists | 작가당 행 중앙값 | 작가당 행 최대 | 검색 lookup 커버리지 |
| --- | --- | --- | --- | --- | --- |
| validation | 2,753 | 172 | 5 | 366 | 1.0 |
| test | 3,099 | 200 | 6 | 275 | 1.0 |

- 소수 작가가 행의 큰 비중을 차지(최대 275~366행) → row 단위 검증은 사실상 대형 작가 적합도 측정. **artist holdout이 1차 게이트여야 하는 정량 근거.**
- 검색 lookup 커버리지 1.0은 lookup이 이 split들로부터 동결됐기 때문(in-sample). 신규 작가 유입 시 미커버 → guard fallback이며, pseudo-cold(PP-PCOLD1)에서 미커버 상황을 별도 검증해야 함.

## 산출물

- `outputs/fixed_cold_base_rows.csv` — validation/test cold 5,852행 고정 base 예측 (y2/y18/guard/연구 base/v0.2 대표·방어, qwidth, search_covered)
- `outputs/cold_base_performance_summary.csv` — champion 비교표
- `artifacts/cold_base_lock_manifest.json` — base 정의, residual target, 게이트, 금지 조건, 재현 검증 diff
- `reports/cold_base_lock.md`

## 다음 실험

- **PP-PCOLD1 (Phase 0.5)**: 거래량 하위 warm 작가를 train에서 마스킹한 pseudo-cold 평가셋 구축 — 0604가 없는 Cold의 외부 검증 축. 검색 lookup 미커버(fallback) 상황 검증 포함.
