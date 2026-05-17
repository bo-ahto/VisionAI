# T4-E032 재료 세분화 피처 실험

- 실험 ID: `T4-E032`
- 연결 가설: `T4-H13`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- Cold 예측에서 재료 피처를 더 세분화하면 성능이 개선되는지 확인함
- 희소 재료를 rare bucket으로 묶으면 큰 오차가 줄어드는지 확인함

## 2. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- 평가 데이터: `data/track4_split/track4_val_cold.csv`

## 3. 사용 모델

- 모델: `QuantileRegressor`
- 기본 피처:
- `medium_category`
- `log_area`
- `aspect_ratio`

## 4. 비교한 피처 조합

- `baseline_medium_category`
- 기존 `medium_category` 사용
- `rare_bucket_category`
- 학습 데이터 100건 미만 재료를 `rare`로 묶음
- `material_flags_only`
- `is_oil`, `is_acrylic`, `is_mixed_media`, `is_print`, `is_ink`, `is_sculpture_material`, `is_other_material`, `is_rare_material`
- `medium_category_plus_flags`
- 기존 `medium_category`와 재료 flag를 함께 사용

## 5. 실행 명령

```bash
python3 scripts/track4/run_t4_e032_material_granularity.py
```

## 6. 결과 파일

- 결과 JSON: `data/track4/results/t4_e032_material_granularity_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e032_material_granularity_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e032_material_granularity.py`

## 7. 주요 결과

| 피처 조합 | median APE | p95 APE | Within-30% | Within-50% | 해석 |
|---|---:|---:|---:|---:|---|
| baseline_medium_category | 0.3642 | 1.1421 | 0.4305 | 0.6389 | 기존 기준 |
| rare_bucket_category | 0.3643 | 1.1311 | 0.4311 | 0.6417 | p95 소폭 개선, median 유지 |
| material_flags_only | 0.3627 | 1.1316 | 0.4305 | 0.6389 | median 소폭 개선 |
| medium_category_plus_flags | 0.3638 | 1.1921 | 0.4305 | 0.6395 | p95 악화 |

## 8. 해석

- 재료 flag만 사용하면 median APE가 `0.3642`에서 `0.3627`로 아주 작게 개선됨
- rare bucket은 p95 APE를 `1.1421`에서 `1.1311`로 소폭 개선함
- 기존 `medium_category`와 flag를 함께 넣으면 p95 APE가 악화됨
- 개선 폭이 작아 최종 피처로 바로 채택하기에는 근거가 약함

## 9. 결론

- 채택 / 보류 / 중단: 보류
- 판단:
- `T4-H13`은 약한 개선 신호가 있으나 강한 채택 근거는 부족함
- `material_flags_only`와 `rare_bucket_category`는 후속 조합 실험 후보로 유지
- `medium_category_plus_flags`는 p95 악화로 우선 제외

## 10. 후속 작업

- `T4-H28` 재료와 크기 조합 피처 실험에서 재료 flag를 다시 확인
- 반복 검증에서 개선 폭이 유지되는지 확인
