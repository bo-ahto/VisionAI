# 등급별 마진 실측 캘리브레이션 보고서 — 목표 coverage 80%

- 총 평가 샘플: 28,376
- 목표 coverage: 80% (가격이 예측 범위 안에 들어올 비율)

## 등급별 결과

| 등급 | 표본 | production-time MdAPE | 현재 m | 현재 coverage | 권장 m | 변화 |
|:---:|---:|---:|---:|---:|---:|---:|
| A | 27,062 | 9.8% | 0.20 | 71.5% | **0.286** | +0.086 |
| B | 1,006 | 29.7% | 0.30 | 50.6% | **0.609** | +0.309 |
| C | 128 | 39.0% | 0.50 | 60.2% | **0.896** | +0.396 |
| D | 180 | 43.6% | 0.70 | 72.8% | **0.827** | +0.127 |

## 해석

- **production-time MdAPE**: 5-fold CV. 단, OOF는 모델 weights에만 적용되고 routing/calibration은 production full-data artifacts 사용:
  · `warm_artist_slugs.json` (PR #20) — A 등급 + XGB train slice 결정
  · `source_calibration.json cold_factors` (PR #21) — cold path 후처리
  → 결과는 'OOF model weights + full-data routing artifacts' 결합 평가. 운영 시 메트릭의 추정치로 해석. 순수 OOF 평가는 아님.
  · Routing/calibration artifact 자체의 OOS 일반화 별도 평가는 PR #20+#21 산출물 참고.
- **현재 coverage**: 현재 m 값으로 계산한 가격 범위에 실제 가격이 들어가는 비율.
  - 80% 미만이면 m이 너무 좁음 (사용자에게 신뢰도 낮은 약속).
  - 80% 훨씬 초과면 m이 너무 넓음 (불필요하게 보수적).
- **권장 m**: 등급별 APE의 quantile_80에 안전 마진 5% 추가.

## 권장 적용

1. `primary_predictor.determine_confidence`의 margin을 권장값으로 교체 (서비스 정책 결정)
2. 보고서 §6.2 등급 마진 표 갱신 + 본 결과 인용
3. 보고서 §7.3 "MdAPE (추정)" → 실측값으로 정정
