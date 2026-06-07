# 2026-06-04 신규 무가격 테스트 가격 예측 결과

- 생성일: 2026-06-04T17:32:21
- 입력 피처 폴더: `/Users/bo/VisionAI/models/track6/price_prediction_v0.1/data/evaluation/test_new_artworks_test_noprice_0604_features`
- 전체 행: 6,873
- Warm 행: 6,873
- Cold 행: 0

## 생성 파일

| 파일 | 설명 |
|---|---|
| `predictions_all.csv` | Warm/Cold 실행 가능 예측값 통합 파일 |
| `warm_predictions.csv` | Warm 행 예측값 |
| `cold_predictions.csv` | Cold 행 예측값. 이번 파일은 0건 |
| `prediction_summary.json` | 실행 요약과 가격 분포 |

## 예측값 해석

- `svc_group_median_pred_price_krw`: 유사 작품 기반 가격 피처의 중앙값 예측. 현재 피처 파일만으로 바로 산출 가능한 값
- `legacy_warm_huber_pred_price_krw`: 이전 Warm Huber baseline artifact 예측. v0.1 현재 1순위 후보가 아니라 비교 기준
- `exact_v01_primary_policy_runnable`: 정확한 v0.1 1순위 결합식을 신규 데이터에 바로 실행할 수 있는지 여부

## 환산 기준

예측 가격의 기준 단위는 원화(KRW)다. 외화 표시는 다음 고정 환산 기준으로 나누어 계산했다.

- 1 USD = 1,380.0 KRW
- 1 EUR = 1,530.0 KRW
- 1 GBP = 1,780.0 KRW
- 1 HKD = 178.0 KRW
- 1 JPY = 9.5 KRW
