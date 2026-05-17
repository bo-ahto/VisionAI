# T4-E035 재료-크기 조합 피처 실험

- 날짜: 2026-05-17
- 연결 가설: T4-H28
- 목적: 재료와 크기를 묶은 피처가 단독 재료/크기 피처보다 가격 예측 성능을 개선하는지 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_warm.csv`
- `data/track4_split/track4_val_cold.csv`

## 가설

- 재료와 크기 구간을 함께 묶은 피처는 일부 약점 구간에서 단독 피처보다 가격을 더 잘 설명할 수 있다.

## 실험 방법

- train 데이터 기준으로 `log_area`를 3개 구간으로 나눔
- `small`: train 하위 33% 이하
- `medium`: train 33~67%
- `large`: train 상위 33% 이상
- 이 구간을 재료/지지체와 결합해 조합 피처를 만듦
- 희소 조합은 `rare_combo`로 묶어 과도한 one-hot 증가를 줄임
- Warm / Cold를 같은 피처 후보로 비교함
- Warm 모델: Ridge
- Cold 모델: HuberRegressor
- Quantile 회귀는 조합 categorical 차원 증가로 실행 시간이 길어져, 이번 실험에서는 빠른 robust 선형 모델인 Huber로 피처 효과를 먼저 확인함

## 비교 피처셋

- `baseline_area_aspect`
- `medium_category`
- `support_category`
- `artist_key`
- `artist_works_log`
- `artist_works_count_train`
- `log_area`
- `aspect_ratio`

- `size_bucket`
- baseline + 크기 구간

- `medium_size_bucket`
- baseline + 재료와 크기 구간 조합

- `support_size_bucket`
- baseline + 지지체와 크기 구간 조합

- `combo_flags`
- baseline + 해석 가능한 rule flag
- `is_large_oil`
- `is_large_acrylic`
- `is_large_mixed_media`
- `is_small_print`
- `is_large_unknown_support`

## 결과

- 결과 파일: `data/track4/results/t4_e035_medium_size_combo_metrics.json`
- 예측 파일: `data/track4/predictions/t4_e035_medium_size_combo_predictions.csv`

| 피처셋 | Warm median APE | Warm p95 APE | Cold median APE | Cold p95 APE |
|---|---:|---:|---:|---:|
| baseline_area_aspect | 0.2597 | 1.5644 | 0.3711 | 1.1848 |
| size_bucket | 0.2948 | 1.5587 | 0.3622 | 1.1941 |
| medium_size_bucket | 0.2741 | 1.5871 | 0.3524 | 1.1737 |
| support_size_bucket | 0.2635 | 1.5450 | 0.3661 | 1.1693 |
| combo_flags | 0.2686 | 1.5305 | 0.3732 | 1.1946 |

## 해석

- Warm에서는 조합 피처가 baseline median APE `0.2597`보다 좋아지지 않음
- Cold에서는 `medium_size_bucket`이 median APE `0.3524`로 이번 Huber 기준 baseline `0.3711`보다 개선됨
- Cold p95 APE는 `support_size_bucket`이 `1.1693`으로 가장 낮음
- 다만 기존 Quantile/size 실험의 최고 후보와 직접 비교하면 아직 최종 채택 근거로는 부족함
- 조합 피처는 전체 모델 교체보다 Cold 보조 후보 또는 약점 구간 분석 피처로 보는 것이 적절함

## 결론

- T4-H28은 부분 검증으로 처리함
- 재료-크기 조합은 Cold에서 개선 신호가 있음
- Warm에서는 조합 피처를 기본 후보로 채택하지 않음
- 다음 단계에서는 Quantile 최종 후보와 같은 기준으로 조합 피처를 다시 비교하거나, Cold 위험 구간 보완용으로 제한 적용을 검토함

## 실행 명령

```bash
python3 scripts/track4/run_t4_e035_medium_size_combo.py
```

## 재현성 확인

- 금지 피처 manifest 검사 통과:

```bash
python3 scripts/track4/check_feature_manifest.py
```
