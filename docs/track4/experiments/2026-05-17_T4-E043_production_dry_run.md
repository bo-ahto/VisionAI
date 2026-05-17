# T4-E043 최종 운영 후보 패키지 dry-run

- 날짜: 2026-05-17
- 연결 가설: T4-H12, T4-H30
- 목적: Track 4 최종 후보를 운영 후보 형태로 재학습하고, 금지 피처 검사와 artifact 생성을 한 번에 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_test_warm.csv`
- `data/track4_split/track4_test_cold.csv`

## 가설

- 최종 후보 모델은 성능만 좋아서는 부족함
- 운영 가능 피처만 사용해야 함
- Warm / Cold 라우팅 기준이 명확해야 함
- 모델 artifact와 결과 manifest가 재현 가능하게 생성되어야 함

## 실험 방법

- 최종 후보 피처셋을 manifest 기준으로 검사함
- 배포 가능한 Warm 후보를 재학습함
- 배포 가능한 Cold 후보를 재학습함
- 재학습한 모델 artifact를 `data/track4/models/`에 저장함
- test 성능을 함께 기록함

## 후보 구분

- Warm 성능 최고 후보:
- `warm_performance_artist_price_stats`
- 작가별 train 기준 가격 통계 피처 포함
- 현재 manifest에서는 `price` 패턴 금지로 차단됨
- Warm 배포 가능 후보:
- `warm_deployable_artist_count`
- 작가 key와 작가 작품 수만 사용
- manifest 통과
- Cold 배포 가능 후보:
- `cold_deployable_full_size`
- 작가 피처 없이 작품 구조 피처만 사용
- manifest 통과

## 결과

| 후보 | manifest 통과 | test median APE | test p95 APE | 판단 |
|---|---:|---:|---:|---|
| warm_performance_artist_price_stats | 실패 | - | - | 과거 가격 통계 피처 허용 여부 정책 결정 필요 |
| warm_deployable_artist_count | 통과 | 0.2810 | 2.5504 | 배포 가능 보수 후보 |
| cold_deployable_full_size | 통과 | 0.4199 | 2.7609 | Cold 배포 가능 후보 |

## 생성 artifact

- Warm 배포 가능 후보:
- `data/track4/models/track4_warm_deployable_ridge.joblib`
- Cold 배포 가능 후보:
- `data/track4/models/track4_cold_deployable_quantile.joblib`
- dry-run 결과:
- `data/track4/results/t4_e043_production_dry_run.json`

## 운영 라우팅 기준

- Warm:
- 입력 작가가 train 작가 집합에 있으면 Warm 모델 사용
- Cold:
- 입력 작가가 train 작가 집합에 없으면 Cold 모델 사용

## 출력 정책 후보

- Warm `low_history`:
- 경고 + q90 넓은 범위 후보
- Warm `mid_history`, `high_history`:
- 일반 q80 범위 후보
- Cold `low_risk`:
- q90 제한적 범위 후보
- Cold `mid_risk`, `high_risk`:
- 단일 가격 보류 또는 강한 경고

## 해석

- Track 4는 운영 후보 artifact 생성까지는 가능함
- 다만 성능 최고 Warm 후보는 현재 manifest 기준으로는 배포 불가함
- 이유는 `artist_train_median_log_price`, `artist_train_mean_log_price`, `artist_train_iqr_log_price`가 `price` 패턴 금지에 걸리기 때문임
- 이 피처는 test 성능에는 유리하지만, 운영 정책상 과거 거래 가격 통계를 허용할지 결정이 필요함
- 보수적으로 가면 Warm 배포 후보 median APE는 `0.2810`임
- 성능 우선으로 과거 가격 통계를 허용하면 이전 실험 기준 Warm median APE는 `0.2201`까지 좋아짐

## 결론

- T4-H12는 부분 검증으로 둠
- 성능/운영/재현 조건 중 재현 조건은 통과했지만, Warm 가격 통계 피처 정책 결정이 남아 있음
- T4-H30은 부분 검증으로 둠
- 모델 artifact와 결과 manifest는 생성됐지만 최종 운영 후보 확정 전 정책 판단이 필요함
- 후속 가설로 Warm 과거 가격 통계 피처 허용 여부를 별도로 관리함

## 실행 명령

```bash
python3 scripts/track4/run_t4_e043_production_dry_run.py
```

## 산출물

- 결과 JSON: `data/track4/results/t4_e043_production_dry_run.json`
- Warm artifact: `data/track4/models/track4_warm_deployable_ridge.joblib`
- Cold artifact: `data/track4/models/track4_cold_deployable_quantile.joblib`
