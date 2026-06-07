# PP-WHUBER11 Warm 원인 기반 보정 + MAPE guard + 과대예측 전용 cap (설계서)

- 작성일: 2026-06-07
- 작성 목적: PP-WHUBER10 원인 기반 보정이 보인 **MdAPE/p95 개선**을 살리되, 동반된 **MAPE 악화를 제거**해 Warm 기준 후보를 순수하게 개선한다.
- 성격: 신규 모델 학습이 아니라, 기존 Warm 최고 조합 위에 적용하는 **후처리 보정 개선** 실험.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 모든 산출물은 전용 폴더 `experiments/track6/PP-WHUBER11_warm_cause_correction_mape_guard/` 아래에만 저장한다(추적·재현 보장).

## 1. 배경 (PP-WHUBER10에서 확인된 사실)

- 기준 Warm 후보: `blend_svcnum_ppv8_wsvc_0.70` → test MdAPE/MAPE/p95 = `0.14048 / 0.2748 / 0.83307`.
- PP-WHUBER10 test 결과(요약: `PP-WHUBER10_warm_artwork_error_cause_correction.md`):
  - `pred_svc_min20_cap0p05_s0p5`: MdAPE `0.13736`(-0.0031), p95 `0.82915`(-0.0039), 그러나 **MAPE `0.27737`(+0.0026 악화)**.
  - `pred_size_min20_cap0p05_s0p5`: MdAPE `0.14002`, p95 `0.82606`(p95 최저), MAPE `0.2752`(거의 중립).
- 진단:
  - 지배적 오차원은 **과대예측 꼬리 구간** — `유사작품_적음+작가이력_적음`, `작가이력_표본_부족`처럼 작가 가격 기준선이 약한 작품.
  - MAPE 악화의 원인은 보정 hierarchy가 broad fallback(`risk_cause`/`pred_log_bin`/`global`)으로 떨어지면서, 같은 cause군의 **정상범위 다수 행**(예: `유사작품_적음+작가이력_적음` 정상 229행)과 일부 **과소예측 행**까지 하향 보정이 새어 들어가기 때문.

## 2. 단일 가설

- H(PP-WHUBER11): "보정을 **과대예측 위험 segment로 한정**하고 **하향 방향만** 적용하며 **validation MAPE 악화를 게이트로 차단**하면, MdAPE 또는 p95_APE를 PP-WHUBER10 수준으로 낮추면서 MAPE는 기준선(0.2748) 이상으로 악화시키지 않는 후보를 얻을 수 있다."
- 변수 축은 **보정 적용 범위·방향·MAPE guard 1축**만 비교한다. 새 원인 라벨·새 피처·새 기준모델은 추가하지 않는다(PP-WHUBER10 진단 자산 재사용).

## 3. 기준선 / 비교 후보

| 역할 | 후보 | 비고 |
|---|---|---|
| 기준선(control) | `blend_svcnum_ppv8_wsvc_0.70` | 현재 Warm 실험 1순위(v0.1 정책) |
| 참고(상한 신호) | `PP-WHUBER10 pred_svc_min20_cap0p05_s0p5` | MdAPE 최저지만 MAPE 악화 |
| 참고(p95 신호) | `PP-WHUBER10 pred_size_min20_cap0p05_s0p5` | p95 최저, MAPE 중립 |
| 신규 후보군 | PP-WHUBER11 guarded variants | §4 설계 |

## 4. 설계 변경 요소 (PP-WHUBER10 대비)

1. **과대예측 전용 적용 마스크**: 보정은 `예측 과대 위험 segment`에만 적용한다.
   - 위험 segment 정의(운영 입력으로 산출 가능한 값만 사용): 낮은 `svc_reliability_bin`(유사작품 표본 부족) AND/OR 낮은 `artist_works_bin`(작가 이력 부족) AND 높은 `pred_log_bin`.
   - 정상범위·과소예측 행은 보정값 0으로 고정(미접촉) → MAPE 보호.
2. **하향 방향 전용 cap**: 보정값 중 음수(하향)만 적용하고 양수(상향) 보정은 0으로 절단한다. 과대예측만 끌어내리고 과소예측은 건드리지 않는다.
3. **MAPE guard 게이트**: validation 작가 holdout에서 후보 선택 시, **mean_delta_MAPE ≤ 0** 또는 **improvement_probability_MAPE ≥ 0.5** 를 통과한 후보만 test 확인 대상으로 올린다.
4. **fallback 차단**: hierarchy fallback을 `risk_cause+pred_log_bin` → `risk_cause`까지만 허용하고 `global` fallback은 사용하지 않는다(정상 행 누수 방지). 표본 부족 segment는 보정 미적용.
5. cap/strength/min_rows grid는 PP-WHUBER10 범위를 재사용하되(`cap ∈ {0.05, 0.08}`, `strength ∈ {0.25, 0.5}`, `min_rows ∈ {8, 20}`, `smooth=20`), 적용 마스크만 위와 같이 좁힌다.

## 5. 방법 (검증 프로토콜)

1. **OOF/holdout 보정값 산출**: 보정 중앙값은 validation 작가 단위 holdout에서만 계산(test 미사용). PP-WHUBER10의 `repeated_artist_holdout` 루프 재사용.
2. **후보 선택**: §4-3 MAPE guard 통과 + balanced_score(ΔMdAPE+Δp95 가중) 상위 후보만 선택.
3. **test 1회 확인**: 선택 후보에 대해서만 test 적용, MdAPE/MAPE/p95/RMSE_log + Δ 기록. test로 후보 재선택 금지.
4. **작품별 진단 재생성**: 보정 전/후 과대예측 꼬리 구간 개선/악화 행 수를 기록(과보정 부작용 점검).

## 6. 채택 / 중단 기준

- 채택(Warm 보조 후보 또는 대표 교체 검토): 아래 모두 만족.
  - validation: MAPE guard 통과(MAPE 비악화).
  - test: MdAPE ≤ `0.14048`(비악화) **그리고** (p95_APE < `0.83307` **또는** MdAPE < `0.14048` 명확 개선).
  - test: **MAPE ≤ `0.2748`** (PP-WHUBER10의 핵심 실패점을 넘지 않음).
- 보조 채택: MAPE 비악화 + p95만 개선 → "큰 오차 방어 보조 후보"로 분리(대표 교체는 보류).
- 중단: MAPE 비악화를 만족하는 후보가 MdAPE/p95 어느 쪽도 개선하지 못하면 → 원인 기반 보정은 진단 용도로만 종결하고 Warm 대표는 기존 유지.

## 7. 산출물 (전용 폴더)

- 실험 폴더: `experiments/track6/PP-WHUBER11_warm_cause_correction_mape_guard/`
  - `outputs/repeated_holdout_metrics.csv` — validation 작가 holdout 반복 성능
  - `outputs/validation_selection_summary.csv` — MAPE guard 통과/탈락 후보와 개선확률
  - `outputs/test_once_metrics.csv` — 선택 후보 test 확인 성능
  - `outputs/test_artwork_error_diagnostics.csv` — 보정 전/후 작품별 진단
  - `reports/result_report.md` / `result_report.html` — 9항목 결과
  - `config/run_config.json` — seed, grid, mask 정의(재현용)
- 요약 문서: `docs/track6/experiments/pp_whuber11_warm_cause_correction_mape_guard_summary.md`
- 인덱스/매트릭스 갱신: `docs/track6/experiments/INDEX.md`, `postprocessing_experiment_matrix.md`

## 8. 실행 명령 (예정)

```bash
python3 scripts/track6/run_pp_whuber11_warm_cause_correction_mape_guard.py
```

- 스크립트는 `run_pp_whuber10_warm_artwork_error_cause_correction.py`를 템플릿으로 하고, §4의 적용 마스크·방향 cap·MAPE guard만 추가한다.

## 9. 누수 방지 체크리스트

- [ ] 보정 중앙값·segment 기준·guard 임계값은 validation holdout에서만 산출했는가.
- [ ] test는 §5-3 최종 확인 1회에만 사용했는가(후보 재선택 금지).
- [ ] 위험 segment 정의에 운영 입력 불가 값(실제 가격 등)을 쓰지 않았는가(`svc_reliability_bin`, `artist_works_bin`, `pred_log_bin`만 사용).
- [ ] 라벨 파일은 학습·평가에서만 read했는가.
- [ ] 하향 전용 cap이 과소예측 행을 건드리지 않음을 진단표로 확인했는가.

## 10. 다음 액션 연결

- 채택 시 → Warm 대표/보조 후보 정책을 PP-I6 service_recommendation 표에 반영하고, 운영 artifact화(component chain) 후보로 승급 검토.
- 중단 시 → 원인 기반 보정은 진단·검수 플래그 용도로만 유지, 다음 Warm 성능 실험은 `PP-SVC6` 비율 재검증 또는 WMAPE residual 반복검증으로 이동.
