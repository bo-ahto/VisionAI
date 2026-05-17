# Track 4 split 생성 보고서

- 목적: Track 4 모델 실험용 train / validation / test split 생성
- 입력: `data/track4_primary_market_feature_candidates_v1.csv`
- random seed: `20260515`
- 기준: `artist_key` 기준 Cold 작가 분리
- `artist_name_ko`는 표시/리포트용 작가명으로 함께 보존
- 동명이인은 `artist_name_ko_orig`, `is_homonym`, `artist_entity_suffix`로 함께 보존
- source는 split 기준이나 모델 피처로 사용하지 않음

## 1. split 결과

| split | rows | artist_key 수 | 한글명 수 | 동명이인 rows | 파일 |
|---|---:|---:|---:|---:|---|
| `train` | `28,930` | `1,836` | `1,788` | `921` | `data/track4_split/track4_train.csv` |
| `val_warm` | `68` | `68` | `68` | `2` | `data/track4_split/track4_val_warm.csv` |
| `val_cold` | `1,835` | `108` | `107` | `66` | `data/track4_split/track4_val_cold.csv` |
| `test_warm` | `137` | `137` | `136` | `6` | `data/track4_split/track4_test_warm.csv` |
| `test_cold` | `3,269` | `216` | `216` | `99` | `data/track4_split/track4_test_cold.csv` |

## 2. 검증

- validation cold와 train 작가 겹침: `0`
- test cold와 train 작가 겹침: `0`
- validation warm 작가가 train에 모두 존재: `True`
- test warm 작가가 train에 모두 존재: `True`
- validation cold와 train 한글 표시명 겹침: `6`
- test cold와 train 한글 표시명 겹침: `20`
- validation cold와 train 원본 한글명 겹침: `8`
- test cold와 train 원본 한글명 겹침: `23`

## 3. 동명이인 해석

- Warm/Cold의 실제 분리 기준은 `artist_key`임
- `artist_key` 기준 train과 cold의 작가 겹침은 0건임
- 원본 한글명은 같은데 `artist_key`가 다른 경우가 있어 `artist_name_ko_orig`는 cold와 train 사이에서 겹칠 수 있음
- 이 경우는 이름이 같은 다른 작가 또는 표기 변형 후보이므로, 모델/평가 기준에서는 `artist_key`를 우선함
- 동명이인으로 판정된 경우 `artist_name_ko`에 `_A`, `_B` suffix가 붙어 표시됨

## 4. 다음 단계

- 이 split을 기준으로 Track 4 baseline 모델 실험 진행
- Warm / Cold 성능은 반드시 분리 기록
