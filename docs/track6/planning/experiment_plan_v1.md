# Track 6 실험 계획서 v1

- 목적: 작품 1건의 정보를 보고 가격을 예측하는 최종 보고용 모델 기준을 재정리
- 배경: Track5는 split을 개선했지만 Cold 이름 중복, Warm 작가 피처 의존, test 기반 정책 선택 리스크가 남음
- 방향: Track6는 split 기준을 더 엄격히 고정한 뒤 모델/피처 실험을 다시 수행

## 1. Track6에서 먼저 해결할 문제

- 1작가 1작품 평가 문제를 split 단계에서 더 줄임
- 작가 이름 한글화 상태를 split 전에 검증함
- 동명이인 후보를 split 전에 분리 또는 별도 표시함
- Cold 작가가 `artist_key`뿐 아니라 한글 작가명 기준으로도 train과 겹치지 않게 함
- Warm 평가 작가는 train에 충분한 작품 수가 남도록 기준을 강화함
- validation과 test 역할을 엄격히 분리함
- test 결과를 보고 피처, 모델, 보정 정책을 고르지 않음
- Track5에서 복잡해진 보조 검증을 Track6 기준 실험으로 정리함

## 2. 예측 상황 정의

- Cold:
  - 예측 대상 작가가 학습 데이터에 없는 경우
  - `artist_key` 또는 한글 작가명 기준으로도 train과 겹치지 않는 경우
  - 작가 피처는 사용하지 않고 작품 구조 정보만 사용
- Low-history Warm:
  - 예측 대상 작가가 학습 데이터에 존재함
  - 다만 train 기준 해당 작가 작품 수가 1~4개인 경우
  - Warm/Cold 경계 구간으로 보고 별도 slice 성능과 신뢰도 경고를 검토
- Stable Warm:
  - 예측 대상 작가가 학습 데이터에 존재하는 경우
  - train 기준 해당 작가 작품 수가 5개 이상인 경우
  - 작품 구조 정보와 train 기준 작가 이력 피처 사용 가능
- Track6의 공식 Warm validation/test는 Stable Warm 기준으로 구성함
- `5개` 기준은 Warm/Cold 구분 기준이 아니라 Stable Warm 평가 안정성 기준임

## 3. 데이터셋 고정 기준

- 입력 원본:
  - `data/track4_primary_market_feature_candidates_v1.csv`
- Track6 split 출력:
  - `data/track6_split/track6_train.csv`
  - `data/track6_split/track6_val_warm.csv`
  - `data/track6_split/track6_test_warm.csv`
  - `data/track6_split/track6_val_cold.csv`
  - `data/track6_split/track6_test_cold.csv`
- split 기준은 `docs/track6/dataset/split_policy_v1.md`에 먼저 고정
- split 생성 후 `docs/track6/dataset/split_report.md`에 rows, 작가 수, 누수 검증 결과 기록
- 모델 실험은 full split CSV가 아니라 feature/label 분리 파일을 기준으로 진행
- 학습/예측 스크립트는 `features/warm` 또는 `features/cold` 파일만 읽음
- 평가 스크립트만 `labels` 파일을 읽음

## 4. split 설계 원칙

- Track3의 Warm/Cold 작가명 기준, Track4의 동명이인 처리, Track5의 split/감사 방식을 참고함
- Cold는 작가 단위로 train과 완전히 분리
- Cold는 `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 기준 중복을 모두 점검
- Cold는 동명이인 suffix가 붙은 `artist_name_ko`와 원본명 `artist_name_ko_orig`를 함께 확인
- Warm은 평가 작가가 train에 반드시 존재해야 함
- Stable Warm 평가 작가는 train에 최소 5작품 이상 남기는 기준을 우선 검토
- train 작품 수 1~4개 작가는 Low-history Warm으로 별도 관리
- Warm 평가셋은 작가당 가능한 2~3작품 이상을 포함
- 동일 작품 후보가 train과 평가셋에 동시에 있으면 train에서 제거
- source, URL, gallery tier는 모델 피처로 사용하지 않음

## 5. 데이터셋 생성 순서

- 1단계: 클렌징 계획 고정
- 2단계: 작가명 한글화/동명이인 상태 점검
- 3단계: 학습 후보 row 확정
- 4단계: validation/test 우선 선정
- 5단계: 남은 데이터로 train 구성
- 6단계: split 품질 검증

## 6. 실험 진행 순서

- 1단계: 이전 트랙 방법 반영 기준 확인
- 2단계: 클렌징 계획 확인
- 3단계: split 정책 고정
- 4단계: Track6 split 생성 및 검증
- 5단계: 컬럼 품질 검증
- 6단계: feature/label 분리 파이프라인 생성
- 7단계: 기본 피처 정의
- 8단계: 구조-only baseline 생성
- 9단계: Warm 작가 피처 ablation
- 10단계: Cold 모델 비교
- 11단계: 피처 조합 실험
- 12단계: 후보 모델군 비교
- 13단계: validation 기준 최종 후보 선정
- 14단계: test 최종 확인
- 15단계: 가격 범위/신뢰도 정책 검증
- 16단계: 최종 artifact 생성

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
  - train 기준 작가 가격 통계
- Cold 금지 피처:
  - `artist_key`
  - `artist_name_ko`
  - `artist_works_log`
  - `artist_works_count_train`
  - 작가 가격 통계
  - source
  - gallery tier
  - URL
  - image URL

## 8. 평가 지표

- 1순위:
  - median APE
  - 대표 오차 수준
  - 낮을수록 좋음
- 2순위:
  - p95 APE
  - 큰 오차 위험 확인용
  - 낮을수록 좋음
- 3순위:
  - Within-30
  - 실제 가격의 30% 이내로 맞춘 비율
  - 높을수록 좋음
- 4순위:
  - Within-50
  - 실제 가격의 50% 이내로 맞춘 비율
  - 높을수록 좋음
- 보조:
  - RMSE(log)
  - 로그 가격 기준 안정성 확인

## 9. 기록 원칙

- 모든 실험은 가설 ID와 실험 ID를 연결
- 실험 전 연구 방법을 먼저 문서에 남김
- validation 결과로 후보를 고름
- test는 최종 확인용으로만 사용함
- Warm / Cold 결과는 합치지 않음
- 사용 데이터, 피처, 모델, 비교 기준, 결과, 결론을 개별 실험 문서에 남김
