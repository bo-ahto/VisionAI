# Track 4 split 생성 보고서

- 목적: Track 4 모델 실험용 train / validation / test split 생성
- 입력: `data/track4_primary_market_feature_candidates_v1.csv`
- random seed: `20260515`
- 기준: `artist_key` 기준 Cold 작가 분리
- `artist_name_ko`는 표시/리포트용 작가명으로 함께 보존
- source는 split 기준이나 모델 피처로 사용하지 않음

## 1. split 결과

| split | rows | artists | 파일 |
|---|---:|---:|---|
| `train` | `28,930` | `1,836` | `data/track4_split/track4_train.csv` |
| `val_warm` | `68` | `68` | `data/track4_split/track4_val_warm.csv` |
| `val_cold` | `1,835` | `108` | `data/track4_split/track4_val_cold.csv` |
| `test_warm` | `137` | `137` | `data/track4_split/track4_test_warm.csv` |
| `test_cold` | `3,269` | `216` | `data/track4_split/track4_test_cold.csv` |

## 2. 검증

- validation cold와 train 작가 겹침: `0`
- test cold와 train 작가 겹침: `0`
- validation warm 작가가 train에 모두 존재: `True`
- test warm 작가가 train에 모두 존재: `True`

## 3. 다음 단계

- 이 split을 기준으로 Track 4 baseline 모델 실험 진행
- Warm / Cold 성능은 반드시 분리 기록
