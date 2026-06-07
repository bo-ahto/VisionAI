# Cold prediction v0.1

PP-QR4가 반복검증한 Cold 정책 고정 번들.

- 대표 점예측: PP-Y18 qwidth
- MAPE/p95 방어층: guard (PP-QR4 채택)
- fallback: PP-Y2

재생성: `python3 scripts/track6/freeze_cold_prediction_artifact_v0_1.py`
릴리스 문서: `reports/cold_artifact_release_v0_1.md`
후처리기: `predict/apply_cold_postprocess_v0_1.py`