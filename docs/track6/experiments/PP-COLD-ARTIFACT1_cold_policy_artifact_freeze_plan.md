# PP-COLD-ARTIFACT1 Cold 예측 정책 artifact 고정 (설계서)

- 작성일: 2026-06-07
- 작성 목적: PP-QR4가 견고하게 검증한 Cold guard 방어 후보 + PP-Y18 대표 점예측 + fallback/신뢰도·범위 정책을 운영 artifact로 고정한다. Cold가 "운영 자동적용 보류" 상태에서 "정책·파라미터 고정" 상태로 전진한다.
- 성격: 엔지니어링(artifact 고정). Warm v0.1 freeze 패턴을 미러링.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 산출물은 artifact 번들 `models/track6/cold_prediction_v0.1/` + freeze 스크립트.

## 1. 배경 / 전제 충족

- 기존 Cold 운영 보류 사유: artifact 고정 + 신뢰도/범위 정책 부재(핸드오프 §2).
- PP-QR4 결과로 전제 충족: guard 후보(`guard_y18_lgb_q40_qwidth67_gap50_down_w0p50`)가 row/artist holdout 양쪽에서 MAPE(1.00/0.98)·p95(0.98/0.85) 견고 + test MdAPE 비악화 → "최종 교체 전 재검증" 완료.
- 대표 점예측 PP-Y18(`stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25`)은 유지(대표 후보는 교체하지 않음).

## 2. 고정 대상 (정책 + 직렬화 가능 파라미터)

| 구분 | 내용 |
|---|---|
| 대표 점예측 | PP-Y18 qwidth (LightGBM Quantile + qwidth bin OOF 보정) |
| MAPE/p95 방어층 | guard: 고위험 구간(qwidth 높음 + y18-lgb_q40 gap 큼)에서 lgb_q40 쪽으로 하향 결합 |
| fallback | PP-Y2 baseline |
| 신뢰도/범위 정책 | Cold = 확정가 아님. 참고 예측가 + 넓은 범위 + 낮은 신뢰도 표시 |

직렬화 가능 guard 파라미터(validation에서 산출, 고정):
- components: `y18_qwidth_pred_log`(base), `lgb_q40_pred_log`(comp)
- thresholds: `qwidth_q67`(quantile_width_log 67분위), `gap_q50`(base−cat_q40 gap 50분위)
- mask(하향 전용): `qwidth >= qwidth_q67` AND `(base − lgb_q40) >= gap_q50` AND `lgb_q40 < base`
- weight: `0.50` → 적용행 `pred = 0.5*base + 0.5*lgb_q40`

## 3. 산출물 (번들 `models/track6/cold_prediction_v0.1/`)

- `config/cold_model_policy_v0_1.json` — 대표/방어/fallback/신뢰도·범위 정책 + guard 파라미터 + 지표
- `config/cold_postprocess_params_v0_1.json` — 직렬화 guard 파라미터(threshold 값 포함)
- `predict/apply_cold_postprocess_v0_1.py` — 후처리기(component 예측 입력 → 대표/방어 출력, 고정 파라미터 사용). self-test로 PP-QR4 test 지표 재현
- `evidence/PP-QR4/` — PP-QR4 보고서/요약/CSV 복사
- `reports/cold_artifact_release_v0_1.md` — 릴리스 문서 + 지표 + 정직한 범위(후처리층 실행 가능 / 하부 Quantile 모델은 상류 참조)
- `reproduction/` — 상류 소스(PP-Y18/PP-QR1/PP-Y2 예측 CSV) 경로 + checksum + 재현 명령
- `manifest/files_manifest.csv`, `manifest/MANIFEST.sha256`
- `README.md`

## 4. 방법

1. validation에서 guard threshold(qwidth_q67, gap_q50) 산출(고정).
2. 후처리기로 test에 적용한 결과가 PP-QR4 guard 지표(test MdAPE 0.4178 / MAPE 0.964 / p95 2.538)와 **정확히 일치**하는지 검증(검증 실패 시 freeze 중단).
3. 대표(PP-Y18)·방어(guard)·fallback(PP-Y2) 지표를 정책 JSON에 기록.
4. manifest checksum 생성, README/릴리스 문서 작성.

## 5. 채택/검증 기준

- 후처리기 재현: guard test 지표가 PP-QR4와 1e-6 이내 일치해야 freeze 확정.
- 정책 JSON에 대표/방어 분리 명시(대표 점예측 PP-Y18 유지, guard는 방어층).
- 정직성: 후처리 파라미터층만 실행 가능, 하부 LightGBM Quantile 모델은 상류 OOF 예측 참조임을 README/릴리스에 명시.

## 6. 데이터 소스

- guard/representative 예측: `experiments/track6/PP-Y18_cold_y16_top_candidate_stability/outputs/predictions.csv`, `experiments/track6/PP-QR1_cold_quantile_regression_alpha_grid/outputs/predictions.csv`, `experiments/track6/PP-Y2_cold_lgbq_search_external_combo/outputs/predictions.csv` (QR2 로더 재사용).
- 검증 근거: `experiments/track6/PP-QR4_cold_qwidth_repeated_split_revalidation/`.

## 7. 다음 액션 연결

- 고정 후 → 운영 API에서 Cold 출력 시 대표(PP-Y18) + 방어(guard) + 범위/신뢰도 정책 적용 검토. 단 신규 cold 라우팅 행이 0604에 없었으므로(6873 warm/0 cold) 실제 cold 운영 트래픽 확보 시 재평가 필요.
- 하부 Quantile 모델 재학습/직렬화는 별도 엔지니어링 작업으로 분리.
