# T4-E023 구조-only Warm / Cold baseline

- 실험 ID: `T4-E023`
- 연결 가설: `T4-H1`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- Track 4 데이터셋에서 작가 정보 없이도 작품 구조 정보만으로 가격 예측 baseline이 성립하는지 확인함
- Warm / Cold를 합치지 않고 각각 따로 평가함
- 이후 피처 추가/제거 실험의 비교 기준을 만들기 위함

## 2. 확인하려는 질문

- 단순 중앙값 가격 예측보다 작품 구조 피처 기반 모델이 더 나은가
- Warm과 Cold에서 같은 구조 피처가 모두 유효한가
- 작가 정보 없이 만든 Cold baseline으로 후속 실험을 시작해도 되는가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- Warm 평가 데이터: `data/track4_split/track4_val_warm.csv`
- Cold 평가 데이터: `data/track4_split/track4_val_cold.csv`
- calibration 데이터: 사용하지 않음

| 구분 | rows | 작가 수 | 가격 중앙값 |
|---|---:|---:|---:|
| train | 28,905 | 1,834 | 3,091,200 |
| val_warm | 67 | 67 | 2,346,000 |
| val_cold | 1,814 | 108 | 2,652,020 |

## 4. 사용 피처

- `medium_category`
- `support_category`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`

## 5. 제외한 피처

- 작가 정보
- `artist_key`
- `artist_name_ko`
- `artist_works_log`
- 출처 정보
- `track4_source`
- `source_artwork_id`
- URL / 이미지 정보
- 가격 관련 정답 컬럼

## 6. 사용 모델

- `dummy_median`
- 학습 데이터의 로그 가격 중앙값만 예측
- 가장 단순한 비교 기준
- `ridge`
- 기본 선형 회귀 계열
- `huber`
- 큰 오차에 덜 끌려가는 robust 선형 회귀 계열

## 7. 비교 기준

- Track 4 비교군
- `dummy_median`
- 판단 기준
- `median APE`가 낮을수록 좋음
- `p95 APE`가 낮을수록 큰 오차 위험이 작음
- `Within-30%`, `Within-50%`는 높을수록 좋음

## 8. 실행 명령

```bash
python3 scripts/track4/run_t4_e023_structure_baseline.py
```

## 9. 결과 파일

- 결과 JSON: `data/track4/results/t4_e023_structure_baseline_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e023_structure_baseline_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e023_structure_baseline.py`

## 10. 주요 결과

| 구분 | 모델 | median APE | MAPE | RMSE(log) | Within-30% | Within-50% | p95 APE |
|---|---|---:|---:|---:|---:|---:|---:|
| Warm | dummy_median | 0.7027 | 1.6996 | 1.2388 | 0.1642 | 0.3284 | 6.9758 |
| Warm | ridge | 0.4619 | 0.9191 | 0.7977 | 0.3433 | 0.5075 | 3.1280 |
| Warm | huber | 0.4148 | 0.7885 | 0.7664 | 0.3881 | 0.5373 | 2.4710 |
| Cold | dummy_median | 0.7424 | 1.3365 | 1.1582 | 0.1979 | 0.3280 | 4.1520 |
| Cold | ridge | 0.3962 | 0.5899 | 0.6968 | 0.3942 | 0.5783 | 1.5736 |
| Cold | huber | 0.3567 | 0.5013 | 0.6720 | 0.4454 | 0.6213 | 1.2373 |

## 11. 해석

- 구조-only 피처만으로도 단순 중앙값 baseline보다 Warm / Cold 모두 개선됨
- Huber가 Warm과 Cold에서 모두 가장 좋은 validation 결과를 보임
- Cold median APE `0.3567`은 구조 정보만으로도 일정 수준 예측 가능하다는 근거임
- Warm median APE `0.4148`은 작가 정보 없이도 기본 예측은 가능하지만, Warm에서는 작가 피처 추가 실험이 필요함
- p95 APE가 여전히 높아 고위험 구간 분석과 가격 범위 실험은 별도로 필요함

## 12. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H1`은 validation 기준 부분 검증됨
- 구조-only baseline 모델은 `huber`를 우선 기준으로 둠
- 이후 피처 실험은 이 결과를 기준선으로 삼아 개선 여부를 판단함

## 13. 후속 작업

- `T4-E024`: Warm 작가 피처 ablation
- `T4-E025`: Cold robust 모델 비교 확장
- `T4-E026`: support unknown 처리 ablation
- `T4-E027`: 2D/3D slice 및 depth 피처 실험
