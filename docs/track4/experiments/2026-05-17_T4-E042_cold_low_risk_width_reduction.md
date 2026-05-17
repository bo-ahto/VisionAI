# T4-E042 Cold 저위험 구간 범위 폭 축소 검증

- 날짜: 2026-05-17
- 연결 가설: T4-H33
- 목적: Cold `low_risk` 구간의 가격 범위 폭을 줄이면서 coverage를 유지할 수 있는지 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_cold.csv`
- `data/track4_split/track4_test_cold.csv`

## 가설

- T4-E040 기준 Cold `low_risk`는 q90에서 coverage `0.7834`, 범위 폭 x`5.54`였음
- 이 범위 폭을 줄이면서 coverage를 유지할 수 있다면 Cold `low_risk`의 서비스 가능성이 올라갈 수 있음

## 실험 방법

- Cold `low_risk` test 구간만 별도로 평가함
- validation `low_risk` 오차로 q80/q85/q90 범위를 정함
- test `low_risk`에서 coverage와 범위 폭을 확인함
- test 정답값으로 범위를 다시 맞추지 않음
- 학습 범위는 2가지로 비교함
- 전체 train으로 학습
- train 내 `low_risk` 후보만 학습
- 모델 후보:
- Quantile
- Huber
- Ridge
- 피처 후보:
- full size: `width_cm`, `height_cm`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`
- area only: `log_area`, `medium_category`
- area aspect: `log_area`, `aspect_ratio`, `medium_category`
- support area aspect: `log_area`, `aspect_ratio`, `medium_category`, `support_category`

## 기준값

- 기준 실험: T4-E040 `cold_full_size` `low_risk` q90
- 기준 coverage: `0.7834`
- 기준 범위 폭: x`5.54`
- 성공 기준:
- coverage가 `0.7834` 이상
- 범위 폭이 x`5.54`보다 작음

## 결과

| 후보 | 학습 범위 | q90 coverage | q90 범위 폭 | median APE | 판정 |
|---|---|---:|---:|---:|---|
| quantile_support_area_aspect | 전체 train | 0.7695 | x4.96 | 0.4264 | coverage 하락 |
| quantile_support_area_aspect | low_risk train | 0.7732 | x4.97 | 0.4319 | coverage 하락 |
| quantile_area_only | low_risk train | 0.7739 | x5.09 | 0.4307 | coverage 하락 |
| huber_full_size | low_risk train | 0.7747 | x5.14 | 0.4202 | coverage 하락 |
| quantile_area_aspect | 전체 train | 0.7747 | x5.16 | 0.4359 | coverage 하락 |
| quantile_full_size | 전체 train | 0.7834 | x5.54 | 0.4077 | 기존 기준 |
| huber_full_size | 전체 train | 0.7863 | x5.57 | 0.4247 | coverage 유지, 폭 증가 |

## 해석

- 범위 폭을 줄이는 후보는 있었음
- 가장 좁은 후보는 `quantile_support_area_aspect` 전체 train 학습임
- q90 범위 폭은 x`4.96`으로 줄었지만 coverage가 `0.7695`로 하락함
- 기존 coverage `0.7834` 이상을 유지하면서 범위 폭을 줄인 후보는 없음
- `huber_full_size` 전체 train은 coverage `0.7863`으로 조금 높지만 범위 폭이 x`5.57`로 더 넓음
- 현재 데이터와 후보 피처만으로는 Cold `low_risk`의 범위 폭을 실질적으로 줄이기 어렵다고 판단함

## 결론

- T4-H33은 검증 완료로 변경함
- 결론은 “개선 가능”이 아니라 “현재 후보군에서는 개선 실패”임
- Cold `low_risk` 정책은 현재 기준으로 `cold_full_size` q90 범위 후보를 유지함
- Cold 범위 폭을 더 줄이려면 현재 작품 구조 피처만으로는 한계가 있음
- 추가 개선은 새 정보가 필요함
- 예: 작가 메타데이터, 외부 거래 이력, 더 안정적인 재료/크기 세분화, 추가 데이터

## 실행 명령

```bash
python3 scripts/track4/run_t4_e042_cold_low_risk_width_reduction.py
```

## 산출물

- 결과 JSON: `data/track4/results/t4_e042_cold_low_risk_width_reduction_metrics.json`
