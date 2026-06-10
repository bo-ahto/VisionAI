# Cold artifact release v0.4 (confidence/display policy)

- 동결일: 2026-06-10T00:00:00
- 점 예측: v0.3 그대로 (guard+search 2단 방어).
- 추가 층: PP-CCONF1 research tier + 표시 정책 + 2단 검수, PP-CSRCH1 미커버 상수 fallback(기본 off).

## 검증

- PP-CCONF1 tier 배정 재현: mismatch 0행 / review flag mismatch 0행
- PP-CSRCH1 미커버 시나리오 재현: max abs diff 1.11e-16
- full lookup ↔ v0.3 defense 일치: max abs diff 5.33e-15

## 사용

- 적용기: `predict/apply_cold_confidence_policy_v0_4.py` (입력: qwidth, y18/v0.2 예측, artist_key)
- fallback 활성화: `confidence_tier_policy_v0_4.json`의 `uncovered_constant_delta.enabled`
- 재생성: `python3 scripts/track6/freeze_cold_prediction_artifact_v0_4.py`