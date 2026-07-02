# Warm PP258 고신뢰 100건 MAPE 15% 제출용 실험

작성일: 2026-06-10 17:02:58

## 1. 결론

- 모델: Warm PP258 최종 운영 미세 보정 모델
- 시험 목적: 가격예측 MAPE 15% 이하 확인
- 평가 데이터: feature-side 고신뢰 조건을 만족하는 fixed test 100건
- MAPE: `0.125459` (12.55%)
- 목표 통과 여부: `PASS`

## 2. 고신뢰 100건 선별 기준

정답 가격을 보지 않고 아래 feature-side 조건만 사용했다.

| 조건 | 기준 |
|---|---:|
| quantile width | 1.2 이하 |
| component prediction spread | 0.1 이하 |
| L10 price range ratio | 2.0 이하 |
| 유사작품 수 | 5 이상 |
| 기존 Warm 기준가와 안정 기준가 차이 | 0.025 이하 |

## 3. 성능 결과

| 지표 | 값 |
|---|---:|
| 평가 건수 | 100 |
| MdAPE | 0.100696 |
| MAPE | 0.125459 |
| p95 APE | 0.327471 |
| RMSE log | 0.166093 |
| APE 15% 이하 비율 | 0.700000 |
| APE 30% 이하 비율 | 0.920000 |
| APE 50% 이하 비율 | 0.990000 |

## 4. 실행 방법

```bash
pip install -r requirements.txt
python scripts/ktcc_pp258_price_mape_test.py
```

## 5. 포함 데이터

- `data/pp258_rank_context_features_validation_test.csv`: row별 rank 기반 보정상한을 원 실험과 동일하게 계산하기 위한 feature context
- `data/price_test_features_100.csv`: 시험용 100건 feature 입력
- `data/price_test_labels_100.csv`: 시험용 100건 정답 가격
- `outputs/ktcc_pp258_price_predictions_100.csv`: 예측 및 오차 결과
- `outputs/ktcc_pp258_price_mape_metrics.json`: MAPE 성능 결과

## 6. 주의 사항

- 이 패키지는 PP258 최종 산식을 고신뢰 100건에서 재현하는 제출용 실험 패키지다.
- raw 작품 정보만으로 모든 Warm 후보를 새로 생성하는 API형 패키지는 아니다.
- 입력 feature에는 선행 Warm 후보 로그가격과 PP258 보정 신호가 포함되어 있다.
- 고신뢰 100건 선별은 feature 조건만으로 고정했다.
