# Track6 E2-1 같은 작가 학습량 비교 실험

- 목적: 같은 작가에서 학습 작품 수가 늘어날수록 Warm 예측이 안정적인지 확인
- 기존 E2 보완점:
  - 기존 E2는 `artist_works_log` 단독 피처 영향 확인
  - E2-1은 동일 작가/동일 테스트셋에서 학습 작품 수만 변경
- 학습량 조건:
  - 작가당 5개
  - 작가당 10개
  - 작가당 20개
  - 작가당 30개
- 사용 피처:
  - `artist_name_ko`
  - `width_cm`
  - `height_cm`
  - `log_area`
  - `aspect_ratio`
- 제외 피처:
  - `artist_works_log`
  - 학습량 자체를 바꾸는 실험이므로 입력 피처에서는 제외
- 사용 모델:
  - Huber
  - Linear Regression
  - Ridge
- 실행 코드:
  - `run_experiment.py`
- 결과:
  - `outputs/result_sheet.html`
  - `outputs/metrics_by_cap.csv`
  - `outputs/mdape_trend_by_model.csv`
  - `outputs/per_artist_metrics.csv`
  - `outputs/predictions.csv`

## 실행 결과 요약

| 작가당 학습 작품 수 | Huber MdAPE | Linear Regression MdAPE | Ridge MdAPE | 해석 |
|---:|---:|---:|---:|---|
| 5 | 0.1947 | 0.2033 | 0.1961 | 학습량이 적어 작가별 가격대 추정이 상대적으로 불안정 |
| 10 | 0.1556 | 0.1440 | 0.1659 | 5개 대비 큰 폭 개선 |
| 20 | 0.1310 | 0.1452 | 0.1465 | Huber 기준 추가 개선 |
| 30 | 0.1269 | 0.1386 | 0.1426 | Huber 기준 최고 MdAPE |

## 결론

- 같은 작가와 같은 테스트 작품을 고정하고 학습 작품 수만 바꿨을 때, 학습 작품 수가 많아질수록 Warm 예측이 대체로 안정화됐다.
- Huber 기준 MdAPE는 `5개 0.1947` → `10개 0.1556` → `20개 0.1310` → `30개 0.1269`로 낮아졌다.
- 따라서 “작가별 학습 작품 수가 많을수록 예측 안정성이 높아질 수 있다”는 E2 가설은 보완 실험 기준으로 지지된다.
- 다만 이 실험은 train 30개 이상 보유 작가 48명, Warm test 147건으로 제한한 비교이므로 전체 Warm 작가 전체에 일반화하기 전 추가 검증이 필요하다.
- `artist_works_log`는 가격을 직접 맞추는 단독 피처라기보다, Warm 신뢰도와 저이력 작가 라우팅 기준으로 쓰는 것이 더 적절하다.
