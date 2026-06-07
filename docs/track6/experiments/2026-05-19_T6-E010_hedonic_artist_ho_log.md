# T6-E010 헤도닉 작가명 + 호수 / ln 변환 초기 실험

- 날짜: 2026-05-19
- 상태: 검증 완료
- 관련 가설: T6-H9, T6-H10
- 실험 폴더: `experiments/track6/T6-E010_hedonic_artist_ho_log/`
- HTML 일지: `experiments/track6/T6-E010_hedonic_artist_ho_log/experiment_log.html`
- 원본 데이터: `data/track6/track6_feature_candidates_name_corrected.csv`
- 실행 스크립트: `experiments/track6/T6-E010_hedonic_artist_ho_log/scripts/run_experiment.py`

## 1. 실험 목적

- 작가명(한글)과 추정 호수만으로 가격 예측 신호가 있는지 확인
- 원 가격/원 호수보다 ln 변환 가격/ln 호수가 더 안정적인지 확인
- 상사 피드백의 “실험별 폴더링, 실험별 데이터 생성, 결과 기록” 방식으로 재현 가능한 실험 단위를 구성

## 2. 데이터 구성

- 사용 원본: Track6 한글명 보정 후보 데이터
- 사용 row: `is_training_candidate = true`이고 가격, 작가, 면적이 있는 row
- 호수 생성:
  - 원본에 직접 호수 컬럼이 없으므로 `area_cm2`를 F형 호수 면적표에 매칭
  - 가장 가까운 F형 호수를 `estimated_ho`로 사용
- Warm test:
  - train에 같은 작가가 존재
  - 평가 작가별 train 최소 작품 수 5개
  - 평가 작가별 test 최소 작품 수 2개
- Cold test:
  - train에 한 번도 등장하지 않는 작가
  - Cold/train 작가 겹침 0

## 3. 생성 데이터

- Warm 일반 학습: `warm_train_base_features.csv`, `warm_train_base_labels.csv`
- Warm ln 학습: `warm_train_log_features.csv`, `warm_train_log_labels.csv`
- Warm 평가: `warm_test_base_features.csv`, `warm_test_log_features.csv`, `warm_test_labels.csv`
- Cold 일반 학습: `cold_train_base_features.csv`, `cold_train_base_labels.csv`
- Cold ln 학습: `cold_train_log_features.csv`, `cold_train_log_labels.csv`
- Cold 평가: `cold_test_base_features.csv`, `cold_test_log_features.csv`, `cold_test_labels.csv`

## 4. 모델

- 모델: Ridge 기반 헤도닉 선형 회귀
- Warm base:
  - 피처: `artist_name_ko`, `estimated_ho`
  - 정답: `price_krw`
- Warm log:
  - 피처: `artist_name_ko`, `ln_estimated_ho`
  - 정답: `ln_price_krw`
- Cold base:
  - 피처: `estimated_ho`
  - 정답: `price_krw`
- Cold log:
  - 피처: `ln_estimated_ho`
  - 정답: `ln_price_krw`

## 5. 결과

| 케이스 | n | median APE | p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|---:|
| warm_model_warm_test_base | 2,445 | 0.4372 | 2.2297 | 0.3836 | 0.5403 |
| warm_model_warm_test_log | 2,445 | 0.1946 | 0.8654 | 0.6777 | 0.8519 |
| warm_model_cold_test_base | 3,005 | 2.5484 | 15.4060 | 0.0942 | 0.1521 |
| warm_model_cold_test_log | 3,005 | 0.4840 | 2.7899 | 0.3098 | 0.5288 |
| cold_model_cold_test_base | 3,005 | 2.4777 | 13.7330 | 0.0855 | 0.1381 |
| cold_model_cold_test_log | 3,005 | 0.5083 | 2.8076 | 0.2722 | 0.4902 |
| cold_model_warm_test_base | 2,445 | 2.0209 | 11.5371 | 0.1018 | 0.1575 |
| cold_model_warm_test_log | 2,445 | 0.5431 | 2.6801 | 0.3076 | 0.4695 |

## 6. 해석

- ln 변환은 이번 실험에서 명확히 유리함
- Warm에서는 `artist_name_ko + ln_estimated_ho -> ln_price_krw` 조합이 가장 좋음
- Warm 최고 median APE는 `0.1946`
- Cold에서는 작가명을 쓸 수 없으므로 `ln_estimated_ho -> ln_price_krw` 모델을 기준으로 보는 것이 더 적절함
- Cold 전용 log 모델 median APE는 `0.5083`
- Warm 모델을 Cold에 적용한 log 결과가 `0.4840`으로 약간 더 낮지만, 이 경우 신규 작가명은 one-hot에서 모두 미등록 처리되므로 사실상 학습 데이터의 절편과 호수 효과에 기대는 형태임
- 따라서 운영 관점에서는 Cold 전용 log 모델을 더 정직한 baseline으로 둠

## 7. 결론

- T6-H9: 부분 채택
  - Warm에서는 작가명과 호수만으로도 강한 예측 신호가 있음
  - Cold에서는 작가명을 사용할 수 없어 호수 단독 신호만으로는 충분하지 않음
- T6-H10: 채택
  - base보다 log 변환이 Warm/Cold 모두에서 큰 폭으로 개선됨
- 후속:
  - Warm은 `작가명 + ln호수`를 최소 baseline으로 유지
  - Cold는 `ln호수` 단독보다 재료, 지지체, 크기 구간, 작가 메타 후보를 추가하는 후속 실험 필요
