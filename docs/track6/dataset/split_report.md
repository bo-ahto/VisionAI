# Track 6 split 생성 보고서

- 상태: 아직 split 생성 전
- 생성 후 이 문서에 결과를 기록

## 1. 예정 산출물

| split | 파일 | 역할 |
|---|---|---|
| train | `data/track6_split/track6_train.csv` | 모델 학습 |
| val_warm | `data/track6_split/track6_val_warm.csv` | Warm 후보 선택 |
| test_warm | `data/track6_split/track6_test_warm.csv` | Warm 최종 확인 |
| val_cold | `data/track6_split/track6_val_cold.csv` | Cold 후보 선택 |
| test_cold | `data/track6_split/track6_test_cold.csv` | Cold 최종 확인 |

## 2. 생성 후 기록할 항목

- rows 수
- 작가 수
- 작가당 rows 중앙값
- 가격 중앙값
- 가격 p90
- Warm train 최소 작품 수
- Cold train 작가 겹침
- Cold train 작가명 겹침
- 동일 작품 후보 제거 수
