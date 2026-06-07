# Track 6 split 생성 보고서

- 생성일: `2026-05-18`
- 입력: `data/track6/track6_feature_candidates_name_corrected.csv`
- random seed: `20260518`
- 상태: `pass`
- 방식: validation/test를 먼저 충분히 확보하고 규모를 근접하게 맞춘 뒤 남은 데이터를 train으로 구성
- Cold 기준: `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 모두 train 겹침 0
- Stable Warm 평가 기준: 평가 작가가 train에 최소 5작품 이상 남음
- Low-history Warm 기준: train에 1~4작품만 있는 작가는 별도 분석 대상으로 관리
- 주의: `5작품` 기준은 Warm/Cold 구분 기준이 아니라 Stable Warm 평가 안정성 기준

## 1. split 결과

| split | rows | 작가 수 | 한글명 수 | 가격 중앙값 | 가격 p90 | 작가당 rows 중앙값 | 1작품 작가 수 | 파일 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `train` | `26,914` | `1,773` | `1,713` | `3,008,400` | `19,039,500` | `5.0` | `245` | `data/track6_split/track6_train.csv` |
| `val_warm` | `519` | `178` | `178` | `3,036,000` | `19,798,920` | `3.0` | `0` | `data/track6_split/track6_val_warm.csv` |
| `test_warm` | `607` | `207` | `205` | `2,829,000` | `18,802,180` | `3.0` | `0` | `data/track6_split/track6_test_warm.csv` |
| `val_cold` | `2,753` | `172` | `168` | `2,622,000` | `12,249,312` | `5.0` | `28` | `data/track6_split/track6_val_cold.csv` |
| `test_cold` | `3,099` | `200` | `189` | `3,450,000` | `20,087,280` | `6.0` | `33` | `data/track6_split/track6_test_cold.csv` |

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

## 4. 라우팅 해석

- Cold: train 내 작가 작품 수 0개이면 Cold 모델 대상
- Low-history Warm: train 내 작가 작품 수 1~4개이면 별도 위험 구간으로 표시
- Stable Warm: train 내 작가 작품 수 5개 이상이면 Warm 모델 평가 기준에 해당

## 5. 해석

- Track6는 Track5보다 Cold 이름 중복 기준을 강화함
- Stable Warm 평가는 train에 충분한 작품이 남는 작가 중심으로 구성함
- split 상태가 `pass`이면 T6-E002 구조-only baseline으로 진행 가능