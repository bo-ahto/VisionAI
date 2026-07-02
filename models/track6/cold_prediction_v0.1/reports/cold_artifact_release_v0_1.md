# Cold prediction v0.1 release

- 작성일(고정): 2026-06-07T00:00:00
- 상태: validated_policy_freeze

## 정책

- 대표 점예측: `component_pp_y18_qwidth_bin` (PP-Y18) — test MdAPE 0.4247 / MAPE 0.9910 / p95 3.3053
- MAPE/p95 방어층: `guard_y18_lgb_q40_qwidth67_gap50_down_w0p50` — test MdAPE 0.4178 / MAPE 0.9640 / p95 2.5377
- fallback: `component_pp_y2_baseline` — test MdAPE 0.4421 / MAPE 1.0484 / p95 3.3537
- 신뢰도/범위: 확정가 아님, 참고가 + 넓은 범위 + 낮은 신뢰도.

## 검증

- 후처리기 재현: shipped 후처리기 vs PP-QR2 guard 정의 max abs diff = 0.00e+00
- PP-QR4 guard test MdAPE 재현: True (PP-QR4 0.4178 vs artifact 0.4178)
- PP-QR4 반복검증 근거: MAPE 개선확률 row/artist 1.00/0.98, p95 0.98/0.85 (evidence/PP-QR4).

## 정직한 범위

- 후처리 파라미터층만 실행 가능(component 예측 입력 필요). 하부 LightGBM Quantile 모델은 상류 OOF 예측 참조 — 신규 raw-input 추론은 하부 모델 직렬화 별도 필요.
- 0604 신규 라벨은 전부 warm(6873 warm/0 cold)이라 cold 운영 트래픽 확보 후 재평가 필요.

## 구성

- `config/cold_model_policy_v0_1.json`, `config/cold_postprocess_params_v0_1.json`
- `predict/apply_cold_postprocess_v0_1.py` (후처리기 + self-test)
- `evidence/PP-QR4/`, `reproduction/upstream_sources.json`
- `manifest/files_manifest.csv`, `manifest/MANIFEST.sha256`