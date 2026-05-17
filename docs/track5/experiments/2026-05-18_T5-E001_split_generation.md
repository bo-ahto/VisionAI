# T5-E001 Track5 split 생성

- 날짜: 2026-05-18
- 관련 가설: T5-H1
- 상태: 완료
- 목적: Track4 Warm test 표본 부족 문제를 해결한 새 Track5 데이터셋 기준 생성

## 1. 확인하려는 것

- Track4보다 Warm 최종 평가셋이 충분히 커졌는가
- Cold 평가셋은 train과 작가가 완전히 분리되었는가
- Warm 평가 작가는 train에 남아 있는가
- 동일 작품 후보가 train과 평가셋에 동시에 들어가 성능이 과대평가될 가능성을 줄였는가

## 2. 사용 데이터

- 입력 원본:
  - `data/track4_primary_market_feature_candidates_v1.csv`
- 생성 split:
  - `data/track5_split/track5_train.csv`
  - `data/track5_split/track5_val_warm.csv`
  - `data/track5_split/track5_test_warm.csv`
  - `data/track5_split/track5_val_cold.csv`
  - `data/track5_split/track5_test_cold.csv`

## 3. split 방법

- Cold:
  - `artist_key` 기준으로 train과 완전히 분리
  - Cold validation 작가와 Cold test 작가를 별도 선택
  - Cold 평가 rows의 `artist_works_log`는 0이어야 함
- Warm:
  - 평가 작가가 train에 반드시 존재해야 함
  - 평가 작가별 train에 최소 2작품 이상 남김
  - 작가당 최대 3작품까지 평가셋으로 분리
- 중복 방지:
  - 같은 작가, 제목, 가격, 크기, 재료/지지체가 평가셋에 있으면 train에서 제거

## 4. 실행 방법

- 실행 명령:
  - `python3 scripts/track5/create_track5_splits.py`

## 5. 결과

| split | rows | 작가 수 | 역할 |
|---|---:|---:|---|
| train | 29,216 | 1,844 | 모델 학습 |
| val_warm | 221 | 86 | Warm 후보 선택 |
| test_warm | 511 | 215 | Warm 최종 확인 |
| val_cold | 1,278 | 97 | Cold 후보 선택 |
| test_cold | 2,896 | 216 | Cold 최종 확인 |

## 6. 검증 결과

- val_cold와 train 작가 겹침: `0`
- test_cold와 train 작가 겹침: `0`
- val_cold의 `artist_works_log > 0` rows: `0`
- test_cold의 `artist_works_log > 0` rows: `0`
- val_warm 작가가 train에 모두 존재: `True`
- test_warm 작가가 train에 모두 존재: `True`
- val_warm 평가 rows의 최소 train 작품 수: `3`
- test_warm 평가 rows의 최소 train 작품 수: `2`
- train에서 제거한 동일 작품 후보 rows: `92`

## 7. 결론

- Track5 split은 Track4보다 Warm 최종 평가에 더 적합하다.
- 기존 Track4 test_warm `137`건에서 Track5 test_warm `511`건으로 늘었다.
- Cold는 train과 작가 기준 겹침이 없어 신규 작가 평가 조건을 만족한다.
- Track5의 이후 모델 실험은 이 split을 기준으로 진행한다.

## 8. 산출물

- 생성 스크립트: `scripts/track5/create_track5_splits.py`
- split 보고서: `docs/track5/dataset/split_report.md`
- split summary: `data/track5_split/track5_split_summary.json`
- split membership: `data/track5_split/track5_split_membership.csv`
