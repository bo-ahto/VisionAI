# T4-E045 조건부 허용 manifest 기반 최종 artifact dry-run

- 날짜: 2026-05-17
- 연결 가설: T4-H12, T4-H30, T4-H35
- 목적: 조건부 허용 피처 정책을 manifest에 반영한 뒤 Warm/Cold 최종 artifact를 재생성
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_test_warm.csv`
- `data/track4_split/track4_test_cold.csv`

## 가설

- Warm 과거 가격 통계 피처를 조건부 허용하면 성능 후보를 운영 후보로 고정할 수 있다.
- 최종 후보는 manifest 검사, artifact 생성, test 재현 결과를 모두 통과해야 한다.

## 조건부 허용 피처

- `artist_train_median_log_price`
- `artist_train_mean_log_price`
- `artist_train_iqr_log_price`

## 조건부 허용 규칙

- 예측 시점 이전 train/거래 데이터만 사용해 계산함
- 예측 대상 작품의 가격은 계산에 포함하지 않음
- 운영 파이프라인에서 같은 방식으로 재계산 가능해야 함

## 최종 후보

- Warm final:
- 모델: Ridge
- artifact: `data/track4/models/track4_warm_final_conditional_stats_ridge.joblib`
- 주요 피처: 작가 key, 작가 작품 수, 작가 train 가격 통계, 재료/지지체/크기
- Cold final:
- 모델: Quantile
- artifact: `data/track4/models/track4_cold_final_full_size_quantile.joblib`
- 주요 피처: 재료, 폭, 높이, 면적, 비율, 3D 여부

## manifest 검사 결과

| 후보 | 결과 | 설명 |
|---|---|---|
| warm_final_conditional_stats | 통과 | 조건부 허용 가격 통계 피처 포함 |
| cold_final_full_size | 통과 | 운영 가능 작품 구조 피처만 사용 |

## 성능 결과

| 후보 | rows | median APE | p95 APE | within-30 | within-50 |
|---|---:|---:|---:|---:|---:|
| Warm final | 137 | 0.2201 | 1.1118 | 0.6131 | 0.8321 |
| Cold final | 3277 | 0.4199 | 2.7609 | 0.3699 | 0.5917 |

## 구간별 결과

| 모델 | 구간 | rows | median APE | p95 APE | within-50 |
|---|---|---:|---:|---:|---:|
| Warm final | low_history | 37 | 0.3581 | 1.6149 | 0.7027 |
| Warm final | mid_history | 70 | 0.2068 | 0.9422 | 0.8714 |
| Warm final | high_history | 30 | 0.1889 | 0.8449 | 0.9000 |
| Cold final | low_risk | 2738 | 0.4077 | 2.6384 | 0.5986 |
| Cold final | mid_risk | 488 | 0.4274 | 4.1932 | 0.5738 |
| Cold final | high_risk | 51 | 0.5672 | 4.2456 | 0.3922 |

## 운영 라우팅 정책

- Warm:
- 입력 작가가 train 작가 집합에 있으면 Warm final 모델 사용
- Cold:
- 입력 작가가 train 작가 집합에 없으면 Cold final 모델 사용

## 출력 정책

- Warm `low_history`:
- 경고 + q90 넓은 범위 후보
- Warm `mid_history`, `high_history`:
- 일반 q80 범위 후보
- Cold `low_risk`:
- q90 제한적 범위 후보
- Cold `mid_risk`, `high_risk`:
- 단일 가격 보류 또는 강한 경고

## 결론

- T4-H35는 검증 완료로 변경함
- T4-H12는 검증 완료로 변경함
- T4-H30은 검증 완료로 변경함
- Track 4 최종 후보 artifact 생성과 manifest 통과를 확인함
- 현재 기준 최종 운영 후보는 아래와 같음
- Warm final: `track4_warm_final_conditional_stats_ridge.joblib`
- Cold final: `track4_cold_final_full_size_quantile.joblib`

## 남은 주의점

- Cold는 단일 가격 신뢰도가 낮음
- Cold는 특히 `mid_risk`, `high_risk`에서 강한 경고 또는 보류 정책이 필요함
- Warm 가격 통계 피처는 반드시 예측 시점 이전 데이터로만 계산해야 함

## 실행 명령

```bash
python3 scripts/track4/run_t4_e045_final_artifact_dry_run.py
```

## 산출물

- 결과 JSON: `data/track4/results/t4_e045_final_artifact_dry_run.json`
- Warm artifact: `data/track4/models/track4_warm_final_conditional_stats_ridge.joblib`
- Cold artifact: `data/track4/models/track4_cold_final_full_size_quantile.joblib`
