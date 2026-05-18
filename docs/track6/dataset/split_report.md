# Track 6 split 생성 보고서

- 생성일: `2026-05-18`
- 입력: `data/track4_primary_market_feature_candidates_v1.csv`
- random seed: `20260518`
- 상태: `pass`
- 방식: validation/test를 먼저 충분히 확보한 뒤 남은 데이터를 train으로 구성
- Cold 기준: `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 모두 train 겹침 0
- Warm 기준: 평가 작가가 train에 최소 5작품 이상 남음

## 1. split 결과

| split | rows | 작가 수 | 한글명 수 | 가격 중앙값 | 가격 p90 | 작가당 rows 중앙값 | 1작품 작가 수 | 파일 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `train` | `27,982` | `1,879` | `1,812` | `2,842,800` | `15,180,000` | `6.0` | `270` | `data/track6_split/track6_train.csv` |
| `val_warm` | `261` | `90` | `90` | `3,063,600` | `13,731,000` | `3.0` | `0` | `data/track6_split/track6_val_warm.csv` |
| `test_warm` | `608` | `208` | `208` | `2,848,260` | `16,560,000` | `3.0` | `0` | `data/track6_split/track6_test_warm.csv` |
| `val_cold` | `1,952` | `80` | `78` | `8,400,000` | `138,165,600` | `5.0` | `12` | `data/track6_split/track6_val_cold.csv` |
| `test_cold` | `3,342` | `200` | `195` | `3,422,400` | `14,000,000` | `7.0` | `25` | `data/track6_split/track6_test_cold.csv` |

## 2. 핵심 검증

- val_warm 작가 모두 train 존재: `True`
- test_warm 작가 모두 train 존재: `True`
- val_warm 최소 train 작품 수: `5`
- test_warm 최소 train 작품 수: `5`
- val_cold train artist_key 겹침: `0`
- test_cold train artist_key 겹침: `0`
- val_cold train artist_name_ko 겹침: `0`
- test_cold train artist_name_ko 겹침: `0`
- val_cold train artist_name_ko_orig 겹침: `0`
- test_cold train artist_name_ko_orig 겹침: `0`
- val_cold `artist_works_log > 0` rows: `0`
- test_cold `artist_works_log > 0` rows: `0`
- train/eval 동일 작품 후보 겹침: `0`

## 3. 최소 평가셋 크기 통과 여부

- val_warm rows 기준 통과: `True`
- val_warm 작가 수 기준 통과: `True`
- test_warm rows 기준 통과: `True`
- test_warm 작가 수 기준 통과: `True`
- val_cold rows 기준 통과: `True`
- val_cold 작가 수 기준 통과: `True`
- test_cold rows 기준 통과: `True`
- test_cold 작가 수 기준 통과: `True`

## 4. 해석

- Track6는 Track5보다 Cold 이름 중복 기준을 강화함
- Warm 평가는 train에 충분한 작품이 남는 작가 중심으로 구성함
- split 상태가 `pass`이면 T6-E002 구조-only baseline으로 진행 가능