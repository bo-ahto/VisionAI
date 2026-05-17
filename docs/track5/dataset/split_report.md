# Track 5 split 생성 보고서

- 목적: Track 4에서 확인된 Warm test 표본 부족 문제를 해결한 새 실험용 split 생성
- 생성일: `2026-05-18`
- 입력: `data/track4_primary_market_feature_candidates_v1.csv`
- random seed: `20260518`
- 기준: `artist_key` 기준 Warm / Cold 분리
- 운영 설명: 학습 DB에 작가가 있으면 Warm, 없으면 Cold

## 1. split 정책

- Cold test 작가 비율: `0.1`
- Cold validation 작가 비율: `0.05`
- Warm test 후보 작가 비율: `0.2`
- Warm validation 후보 작가 비율: `0.1`
- Warm 평가 후보 최소 작품 수: `5`
- Warm 평가 작가별 최대 holdout 작품 수: `3`
- Warm 평가 작가별 train에 남기는 최소 작품 수: `2`

## 2. split 결과

| split | rows | artist_key 수 | 한글명 수 | 가격 중앙값 | 가격 p90 | 작가당 rows 중앙값 | 파일 |
|---|---:|---:|---:|---:|---:|---:|---|
| `train` | `29,216` | `1,844` | `1,790` | `3,063,600` | `19,320,000` | `6.0` | `data/track5_split/track5_train.csv` |
| `val_warm` | `221` | `86` | `86` | `3,174,000` | `22,000,000` | `3.0` | `data/track5_split/track5_val_warm.csv` |
| `test_warm` | `511` | `215` | `215` | `3,864,000` | `20,700,000` | `3.0` | `data/track5_split/track5_test_warm.csv` |
| `val_cold` | `1,278` | `97` | `97` | `2,632,350` | `12,544,200` | `6.0` | `data/track5_split/track5_val_cold.csv` |
| `test_cold` | `2,896` | `216` | `213` | `2,500,000` | `12,741,540` | `6.0` | `data/track5_split/track5_test_cold.csv` |

## 3. 누수/분리 검증

- val_cold와 train 작가 겹침: `0`
- test_cold와 train 작가 겹침: `0`
- val_cold의 `artist_works_log > 0` rows: `0`
- test_cold의 `artist_works_log > 0` rows: `0`
- val_warm 작가가 train에 모두 존재: `True`
- test_warm 작가가 train에 모두 존재: `True`
- val_warm 평가 rows의 최소 train 작품 수: `3`
- test_warm 평가 rows의 최소 train 작품 수: `2`

## 4. 동일 작품 후보 처리

- train에서 제거한 동일 작품 후보 rows: `92`
- 제거된 rows의 작가 수: `26`
- 같은 작가, 제목, 가격, 크기, 재료/지지체가 평가셋에 있으면 train에서 제거
- 평가셋은 그대로 두고 train만 제거해 평가 성능 과대평가를 줄임

## 5. 해석

- Track5는 Track4 split을 덮어쓰지 않는 새 기준 split임
- Warm test는 기존 Track4의 137건보다 크게 늘어 최종 성능 판단에 더 적합함
- Cold는 작가 기준으로 train과 완전히 분리되어 신규 작가 상황을 평가함
- 이 split을 기준으로 Track5 모델 실험을 새로 시작해야 함
