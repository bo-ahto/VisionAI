# T4-E028 공유 모델 / 분리 모델 및 반복 검증

- 실험 ID: `T4-E028`
- 연결 가설: `T4-H21`, `T4-H22`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- Warm / Cold를 하나의 공유 모델로 처리해도 되는지 확인함
- Warm / Cold 분리 정책이 반복 검증에서도 안정적인지 확인함
- 단일 validation split만 보고 판단하는 위험을 줄이기 위해 내부 반복 검증을 수행함

## 2. 확인하려는 질문

- 구조-only 공유 모델 하나로 Warm과 Cold를 모두 처리해도 되는가
- Warm은 작가 key를 포함한 분리 모델이 더 안정적인가
- Cold는 seed에 따라 성능 흔들림이 큰가
- 반복 검증 평균과 표준편차 기준으로 어떤 정책이 더 안전한가

## 3. 사용 데이터

- 기준 데이터: `data/track4_split/track4_train.csv`
- 방식:
- 기존 train 내부에서 seed별로 임시 train / warm holdout / cold artist holdout을 다시 생성
- seed: `11`, `22`, `33`, `44`, `55`
- 내부 Warm:
- 학습에 남아 있는 작가의 작품 1건을 holdout
- 내부 Cold:
- 일부 작가를 통째로 holdout
- 작가 이력 피처:
- 각 seed의 내부 train 기준으로 다시 계산

## 4. 비교 정책

- `shared_structure`
- 하나의 구조-only Quantile 모델을 Warm / Cold에 모두 적용
- 사용 피처:
- `medium_category`
- `log_area`
- `aspect_ratio`
- `split_policy`
- Warm:
- `Ridge`
- 구조 피처 + `support_category` + `artist_key` + 작가 이력 피처
- Cold:
- `QuantileRegressor`
- 구조-only 피처

## 5. 실행 명령

```bash
python3 scripts/track4/run_t4_e028_shared_vs_split_repeated.py
```

## 6. 결과 파일

- 결과 JSON: `data/track4/results/t4_e028_shared_vs_split_repeated_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e028_shared_vs_split_repeated_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e028_shared_vs_split_repeated.py`

## 7. 반복 검증 요약

| 정책 | split | median APE 평균 | median APE 표준편차 | p95 APE 평균 | Within-30% 평균 |
|---|---|---:|---:|---:|---:|
| shared_structure | Warm | 0.5325 | 0.0096 | 2.7286 | 0.2996 |
| split_policy | Warm | 0.3559 | 0.0076 | 1.8749 | 0.4376 |
| shared_structure | Cold | 0.4280 | 0.0454 | 2.0242 | 0.3701 |
| split_policy | Cold | 0.4280 | 0.0454 | 2.0242 | 0.3701 |

## 8. 해석

- Warm에서는 분리 정책이 공유 구조-only 모델보다 명확히 좋음
- Warm median APE 평균이 `0.5325`에서 `0.3559`로 개선됨
- Warm p95 APE 평균도 `2.7286`에서 `1.8749`로 개선됨
- Cold는 이번 비교에서 공유 모델과 분리 정책이 같은 구조-only Quantile 모델을 쓰므로 결과가 동일함
- Cold median APE 표준편차 `0.0454`는 Warm보다 크므로 Cold는 split 구성에 더 민감함
- 따라서 Warm / Cold를 합쳐 하나의 정책으로 판단하면 Warm 개선 효과와 Cold 불안정성을 모두 놓칠 수 있음

## 9. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H21`: 공유 구조-only 모델보다 Warm/Cold 분리 정책이 유리함
- `T4-H22`: 반복 검증이 필요하다는 가설은 지지됨
- 운영 후보:
- Warm은 작가 key/이력 포함 모델 유지
- Cold는 구조-only robust 모델 유지
- Cold는 이후 위험 구간과 가격 범위 검증을 추가해야 함

## 10. 후속 작업

- `T4-H10`, `T4-H19`: 작가 작품 수 기준 라우팅 실험
- `T4-H17`: Cold 저위험/고위험 구간 분리
- `T4-H18`, `T4-H29`: 가격 범위와 신뢰도 calibration
