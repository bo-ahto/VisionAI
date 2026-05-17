# T4-E053 Warm 재검증 split 생성 및 반복 평가

- 날짜: 2026-05-18
- 관련 가설: T4-H40
- 상태: 완료
- 목적: 기존 Track 4 Warm test가 `137`건으로 작아 최종 Warm 성능 판단이 흔들릴 수 있는 문제를 보완

## 1. 확인하려는 것

- 기존 `track4_test_warm.csv` 1회 평가만으로 Warm 최종 성능을 판단해도 되는가
- 평가 rows와 작가 수를 늘린 반복 Warm holdout에서도 RandomForest 후보 성능이 유지되는가
- Warm 성능이 특정 작은 test split에만 우연히 좋게 나온 것은 아닌가

## 2. 사용 데이터

- 입력 원본: `data/track4_primary_market_feature_candidates_v1.csv`
- 기존 split 참조: `data/track4_split/`
- 새 재검증 split 저장 위치: `data/track4_warm_recheck_split/`
- 기존 Cold validation/test 작가는 제외하고 Warm 재검증 pool 구성
- 기존 Track 4 split은 덮어쓰지 않음

## 3. split 생성 방식

- seed 5개 사용:
  - `20260518`
  - `20260519`
  - `20260520`
  - `20260521`
  - `20260522`
- Warm 후보 작가 기준:
  - 기존 Cold validation/test 작가 제외
  - 학습 후보 데이터에 작품이 5개 이상 있는 작가만 평가 후보로 사용
- holdout 방식:
  - seed마다 후보 작가의 20%를 Warm 평가 작가로 선택
  - 평가 작가별 최대 3작품까지 평가셋으로 분리
  - 평가 작가도 train에 최소 2작품은 남기도록 제한
- 저장 방식:
  - seed별 train CSV는 복제하지 않음
  - `warm_recheck_split_membership.csv`로 seed별 Warm 평가 holdout row membership 저장
  - train은 원본 pool에서 해당 seed의 평가 holdout row를 제외해 재구성
  - seed별 평가 rows는 `seed_*_warm_eval.csv`로 저장

## 4. 사용 모델과 피처

- 모델: `RandomForestRegressor`
- 기준: T4-E049 Warm 최종 후보와 같은 설정
- 사용 피처:
  - `artist_key`
  - `medium_category`
  - `support_category`
  - `artist_works_log`
  - `artist_works_count_train`
  - `artist_train_median_log_price`
  - `artist_train_mean_log_price`
  - `artist_train_iqr_log_price`
  - `log_area`
  - `aspect_ratio`
- 작가 통계 피처는 각 seed의 train 기준으로 다시 계산

## 5. 실행 방법

- 실행 명령:
  - `python3 scripts/track4/run_t4_e053_warm_recheck_split_revalidation.py`

## 6. 결과

| 항목 | 값 |
|---|---:|
| seed 수 | 5 |
| 평균 평가 rows | 534.4 |
| 평균 평가 작가 수 | 217.0 |
| median APE 평균 | 0.1687 |
| median APE 표준편차 | 0.0103 |
| median APE 범위 | 0.1512 ~ 0.1834 |
| p95 APE 평균 | 0.9379 |
| p95 APE 표준편차 | 0.0379 |
| Within-30 평균 | 0.6879 |
| Within-50 평균 | 0.8313 |

## 7. 기존 137건 test와 비교

| 평가 기준 | rows | median APE | p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|---:|
| 기존 T4-E049 fixed test | 137 | 0.1970 | 0.9219 | 0.6715 | 0.8613 |
| T4-E053 반복 Warm recheck 평균 | 534.4 | 0.1687 | 0.9379 | 0.6879 | 0.8313 |

- 반복 평가에서도 median APE는 기존 137건 test보다 낮게 나왔다.
- p95 APE는 기존 test와 비슷한 수준이다.
- Within-50은 기존 test보다 낮지만 큰 차이는 아니다.
- 기존 137건 test가 성능을 과대평가했다고 보기는 어렵다.
- 다만 최종 Warm 성능 보고는 단일 137건 수치보다 반복 평균/표준편차를 함께 제시하는 것이 더 안전하다.

## 8. 결론

- 기존 Warm test 137건은 최종 판단용으로 작다는 지적은 타당하다.
- 보완 split을 추가로 만들어 반복 검증한 결과, Warm RandomForest 후보는 성능이 유지되었다.
- 현재 기준 Warm 최종 후보는 유지 가능하다.
- 앞으로 Warm 성능을 보고할 때는 아래처럼 함께 표기한다.
  - 고정 test 성능: T4-E049 median APE `0.1970`
  - 반복 recheck 평균: T4-E053 median APE `0.1687 ± 0.0103`

## 9. 산출물

- 실행 스크립트: `scripts/track4/run_t4_e053_warm_recheck_split_revalidation.py`
- 결과 JSON: `data/track4/results/t4_e053_warm_recheck_split_revalidation_metrics.json`
- 재검증 split 폴더: `data/track4_warm_recheck_split/`
- split membership: `data/track4_warm_recheck_split/warm_recheck_split_membership.csv`
