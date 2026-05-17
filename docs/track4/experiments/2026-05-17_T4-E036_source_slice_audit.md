# T4-E036 출처별 성능/결측 감사 slice

- 날짜: 2026-05-17
- 연결 가설: T4-H23
- 목적: 출처를 모델 피처로 쓰지 않더라도, 특정 출처에서만 성능이 좋거나 나쁜지 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_warm.csv`
- `data/track4_split/track4_val_cold.csv`

## 가설

- 출처별 분포 차이는 피처로 쓰지 않더라도 감사 slice로 확인해야 한다.

## 실험 방법

- `track4_source`는 모델 입력 피처에 넣지 않음
- 모델 예측 후 결과를 출처별로 나눠 성능을 확인함
- 확인 항목:
- rows
- artists
- median APE
- p95 APE
- median price
- medium/support unknown 비율
- 3D 비율
- sample 수가 20건 미만이면 해석 주의 표시

## 사용 모델과 피처

- `warm_area_aspect`
- 모델: Ridge
- 피처: `medium_category`, `support_category`, `artist_key`, `log_area`, `aspect_ratio`, `artist_works_log`, `artist_works_count_train`

- `cold_area_only`
- 모델: QuantileRegressor
- 피처: `medium_category`, `log_area`

- `cold_full_size`
- 모델: QuantileRegressor
- 피처: `medium_category`, `width_cm`, `height_cm`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`

## 결과

- 결과 파일: `data/track4/results/t4_e036_source_slice_audit_metrics.json`
- 예측 파일: `data/track4/predictions/t4_e036_source_slice_audit_predictions.csv`

| 모델 | split | 전체 median APE | 전체 p95 APE | 출처별 주요 결과 |
|---|---|---:|---:|---|
| warm_area_aspect | Warm | 0.2597 | 1.5644 | artsy `0.3913`, saatchi `0.2545`, artue `0.1663` 단 artue 9건 |
| cold_area_only | Cold | 0.3613 | 1.1135 | saatchi `0.2569`, artsy `0.4122`, artue `0.4949` |
| cold_full_size | Cold | 0.3349 | 1.3041 | saatchi `0.2334`, artsy `0.4044`, artue `0.5501` |

## 해석

- Cold는 출처별 차이가 큼
- saatchi는 Cold median APE가 상대적으로 낮음
- artue와 artsy는 Cold median APE가 상대적으로 높음
- `cold_full_size`는 전체 median APE는 좋지만, p95 APE가 `cold_area_only`보다 나빠짐
- gallery_primary는 val_cold 3건뿐이라 성능 판단에서 제외해야 함
- 출처는 운영 입력으로 알 수 없으므로 모델 피처로 쓰면 안 됨
- 다만 결과 해석에서는 “특정 출처에 성능이 치우칠 수 있다”는 주의가 필요함

## 결론

- T4-H23은 부분 검증으로 처리함
- source는 모델 피처 제외 원칙을 유지함
- 후속 피처 실험에서는 전체 성능뿐 아니라 source slice도 함께 확인하는 것이 좋음
- Cold 후보는 median APE만 보면 `cold_full_size`, tail risk까지 보면 `cold_area_only`가 더 안정적임

## 실행 명령

```bash
python3 scripts/track4/run_t4_e036_source_slice_audit.py
```

## 재현성 확인

```bash
python3 scripts/track4/check_feature_manifest.py
```
