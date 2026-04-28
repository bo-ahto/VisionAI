# 등급별 마진 실측 캘리브레이션 보고서 — 목표 coverage 80%

- 총 평가 샘플: 28,376
- 목표 coverage: 80% (가격이 예측 범위 안에 들어올 비율)

## 등급별 결과

| 등급 | 표본 | 실측 MdAPE | 현재 m | 현재 coverage | 권장 m | 변화 |
|:---:|---:|---:|---:|---:|---:|---:|
| A | 27,062 | 9.8% | 0.20 | 71.5% | **0.286** | +0.086 |
| B | 1,006 | 29.7% | 0.30 | 50.6% | **0.609** | +0.309 |
| C | 128 | 39.0% | 0.50 | 60.2% | **0.896** | +0.396 |
| D | 180 | 43.6% | 0.70 | 72.8% | **0.827** | +0.127 |

## 해석

- **production-time MdAPE**: 5-fold CV로 measured. 모델 prediction은 fold-out (OOF), 단 source × target_market calibration은 PR #21 production guarded factors (full-data fit) 직접 적용 → factor는 OOF 보장 X. 
  운영 시 사용자가 받을 메트릭의 추정치로 해석. Calibrator의 OOS 일반화 평가는 별도 산출물 (`integrated_v3_filtered_tuned_source_calibration.json`의 `cold_overall`).
- **현재 coverage**: 현재 m 값으로 계산한 가격 범위에 실제 가격이 들어가는 비율.
  - 80% 미만이면 m이 너무 좁음 (사용자에게 신뢰도 낮은 약속).
  - 80% 훨씬 초과면 m이 너무 넓음 (불필요하게 보수적).
- **권장 m**: 등급별 APE의 quantile_80에 안전 마진 5% 추가.

## 권장 적용

1. `primary_predictor.determine_confidence`의 margin을 권장값으로 교체 (서비스 정책 결정)
2. 보고서 §6.2 등급 마진 표 갱신 + 본 결과 인용
3. 보고서 §7.3 "MdAPE (추정)" → 실측값으로 정정
