# T4-E015 Track 4 split 생성

- 날짜: 2026-05-15
- 연결 가설: T4-H0
- 상태: 완료
- 목적: `feature_candidates_v1` 기준으로 Warm / Cold 평가가 가능한 Track 4 split 생성

## 1. 실행 방법

- 스크립트: `scripts/track4/create_track4_splits.py`
- 입력: `data/track4_primary_market_feature_candidates_v1.csv`
- random seed: `20260515`
- 기준:
  - `artist_key` 기준으로 Cold 작가를 train에서 완전히 제외
  - Warm 평가는 train에 남아 있는 작가의 작품 1건을 holdout
  - `artist_name_ko`는 표시/리포트용 작가명으로 split에 함께 보존
  - source는 split 기준이나 모델 피처로 사용하지 않음

## 2. 생성 파일

| split | rows | artists | 파일 |
|---|---:|---:|---|
| train | `28,930` | `1,836` | `data/track4_split/track4_train.csv` |
| val_warm | `68` | `68` | `data/track4_split/track4_val_warm.csv` |
| val_cold | `1,835` | `108` | `data/track4_split/track4_val_cold.csv` |
| test_warm | `137` | `137` | `data/track4_split/track4_test_warm.csv` |
| test_cold | `3,269` | `216` | `data/track4_split/track4_test_cold.csv` |

## 3. 검증 결과

- validation cold와 train 작가 겹침: `0`
- test cold와 train 작가 겹침: `0`
- validation warm 작가는 모두 train에 존재함
- test warm 작가는 모두 train에 존재함

## 4. 결론

- 채택: Track 4 모델 실험용 split 기준으로 사용 가능
- 주의: 현재 split은 1차 기준이며, 모델 성능 실험 후 작가 수 기준 라우팅 실험에서 조정 가능

## 5. 다음 작업

- Track 4 baseline 모델 실험 진행
- Warm / Cold 성능을 분리 기록
- feature 후보 컬럼 결측률 점검 후 모델 입력 schema 확정
