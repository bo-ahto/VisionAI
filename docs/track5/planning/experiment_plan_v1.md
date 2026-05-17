# Track 5 실험 계획서 v1

- 목적: 작품 1건의 정보를 보고 가격을 예측하는 모델을 새 split 기준으로 다시 구축
- 배경: Track 4는 Warm test가 `137`건으로 작아 최종 성능 판단 기준으로 약했음
- 방향: Track 5는 데이터셋 split을 먼저 고정하고, 같은 기준으로 모델/피처 실험을 다시 진행

## 1. Track 5에서 먼저 해결할 문제

- Warm test 표본 수 부족 문제 해결
- Warm / Cold 분리 기준 명확화
- validation과 test 역할 분리
- 작가 기준 누수 방지
- 동일 작품 후보가 train과 평가셋에 동시에 들어가는 문제 방지
- 최종 성능을 단일 작은 test가 아니라 충분한 평가셋 기준으로 판단

## 2. 예측 상황 정의

- Warm:
  - 예측 대상 작가가 학습 데이터에 존재하는 경우
  - 운영 표현: 학습 DB에 작가 이력이 있는 경우
  - 사용 가능 정보: 작품 구조 정보 + train 기준 작가 이력 정보
- Cold:
  - 예측 대상 작가가 학습 데이터에 존재하지 않는 경우
  - 운영 표현: 처음 보는 작가인 경우
  - 사용 가능 정보: 작품 구조 정보만 사용
  - 작가명, 작가 과거 가격, 작가 이력 피처는 제외

## 3. 데이터셋 고정 기준

- 입력 원본:
  - `data/track4_primary_market_feature_candidates_v1.csv`
- Track 5 split:
  - `data/track5_split/track5_train.csv`
  - `data/track5_split/track5_val_warm.csv`
  - `data/track5_split/track5_test_warm.csv`
  - `data/track5_split/track5_val_cold.csv`
  - `data/track5_split/track5_test_cold.csv`
- split 재생성 명령:
  - `python3 scripts/track5/create_track5_splits.py`

## 4. split 설계 원칙

- Cold는 작가 단위로 train과 완전히 분리
- Warm은 평가 작가가 train에 반드시 남아 있어야 함
- Warm 평가 작가는 train에 최소 2작품 이상 남김
- Warm test는 Track 4보다 충분히 크게 구성
- train과 평가셋에 동일 작품 후보가 겹치면 train에서 제거
- source, URL, gallery tier는 split 기준이나 모델 피처로 사용하지 않음

## 5. 현재 Track 5 split 결과

| split | rows | 작가 수 | 역할 |
|---|---:|---:|---|
| train | 29,216 | 1,844 | 모델 학습 |
| val_warm | 221 | 86 | Warm 후보 선택 |
| test_warm | 511 | 215 | Warm 최종 확인 |
| val_cold | 1,278 | 97 | Cold 후보 선택 |
| test_cold | 2,896 | 216 | Cold 최종 확인 |

## 6. 실험 진행 순서

- 1단계: 데이터셋 기준 고정
- 2단계: 기본 피처 정의
- 3단계: 구조-only baseline 생성
- 4단계: Warm / Cold 분리 모델 비교
- 5단계: Warm 피처 실험
- 6단계: Cold 피처 실험
- 7단계: 모델군 비교
- 8단계: 가격 범위/신뢰도 정책 실험
- 9단계: 최종 후보 artifact 생성

## 7. 기본 피처 후보

- 공통 작품 구조 피처:
  - `medium_category`
  - `support_category`
  - `log_area`
  - `aspect_ratio`
  - `width_cm`
  - `height_cm`
  - `has_depth`
  - `is_3d_candidate`
- Warm 전용 후보:
  - `artist_key`
  - `artist_works_log`
  - `artist_works_count_train`
  - train 기준 작가 가격 통계 후보
- Cold 금지 피처:
  - `artist_key`
  - `artist_works_log`
  - `artist_works_count_train`
  - 작가 가격 통계
  - source / gallery / URL / image URL

## 8. 평가 지표

- 1순위:
  - median APE
  - 낮을수록 좋음
- 2순위:
  - p95 APE
  - 큰 오차 위험 확인용
  - 낮을수록 좋음
- 3순위:
  - Within-30
  - 30% 이내로 맞춘 비율
  - 높을수록 좋음
- 4순위:
  - Within-50
  - 50% 이내로 맞춘 비율
  - 높을수록 좋음
- 보조:
  - RMSE(log)
  - 로그 가격 학습 안정성 확인

## 9. 기록 원칙

- 모든 실험은 가설 ID와 실험 ID를 연결
- validation에서 후보를 고르고 test는 최종 확인에 사용
- Warm / Cold 성능은 합치지 않고 따로 기록
- 사용 데이터, 피처, 모델, 비교 기준, 결과, 결론을 개별 실험 문서에 남김
- 성능이 좋아도 운영에서 만들 수 없는 피처는 최종 후보에서 제외
