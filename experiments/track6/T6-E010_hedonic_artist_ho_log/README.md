# T6-E010 실험 일지

- 실험명: 작가명 + 추정 호수 기반 헤도닉 선형 회귀
- 목적: 작품 가격 예측에서 `작가명(한글)`과 `호수`만으로 유의미한 예측 신호가 있는지 확인
- 추가 목적: `호수`와 `가격`을 ln 변환했을 때 예측 성능이 개선되는지 확인
- 실행 스크립트: `experiments/track6/T6-E010_hedonic_artist_ho_log/scripts/run_experiment.py`
- 원본 데이터: `data/track6/track6_feature_candidates_name_corrected.csv`
- 생성 데이터 위치: `experiments/track6/T6-E010_hedonic_artist_ho_log/data/`
- 결과 위치: `experiments/track6/T6-E010_hedonic_artist_ho_log/outputs/`
- 로그 위치: `experiments/track6/T6-E010_hedonic_artist_ho_log/logs/`
- HTML 일지: `experiments/track6/T6-E010_hedonic_artist_ho_log/experiment_log.html`
- 실행 모델: Ridge 기반 Hedonic Linear Regression
- 비고: 초기 샘플 실행 일지라 기본 비교 모델군 통제 대상이 아님

## 1. 가설

- T6-H9: 작가명(한글)과 호수만으로도 가격 예측에서 유의미한 결과를 볼 수 있다.
- T6-H10: 호수와 가격을 ln 변환하면 원값을 쓰는 것보다 예측 결과가 개선될 것이다.

## 2. 유의미함 기준

- 1순위: `median APE`가 기준 모델보다 낮아지는지 확인
- 2순위: `p95 APE`가 과도하게 커지지 않는지 확인
- 3순위: `Within-30`, `Within-50` 비율이 높아지는지 확인
- 4순위: Warm / Cold에서 같은 방향으로 개선되는지 분리 확인
- 운영 판단: 사용자가 입력 가능한 값으로 재현 가능한지 확인

## 3. 데이터 생성 기준

- 전체 정제 후보 파일에서 `is_training_candidate = true`인 row만 사용
- 가격, 작가명, 작가 key, 면적이 없는 row는 제외
- 원본에 호수 컬럼이 없으므로 `area_cm2`를 F형 호수 면적표와 비교해 가장 가까운 호수로 변환
- `ln_estimated_ho = ln(estimated_ho)`로 생성
- `ln_price_krw = ln(price_krw)`로 생성

## 4. Warm / Cold 기준

- Warm test:
  - 학습 데이터에 같은 작가가 남아 있는 작품
  - 평가 대상 작가는 학습 데이터에 최소 5개 작품이 남도록 구성
  - 1작가 1작품 평가 문제가 반복되지 않도록 작가당 최소 2개, 최대 3개 평가 row를 분리
- Cold test:
  - 학습 데이터에 한 번도 등장하지 않는 작가의 작품
  - Cold 모델은 작가명을 입력 피처로 사용하지 않음

## 5. 실험 방법

- Warm 일반 실험:
  - 학습 입력: `artist_name_ko`, `estimated_ho`
  - 학습 정답: `price_krw`
  - 평가: Warm test / Cold test 모두에 적용
- Warm ln 변환 실험:
  - 학습 입력: `artist_name_ko`, `ln_estimated_ho`
  - 학습 정답: `ln_price_krw`
  - 예측값은 다시 원화 가격으로 변환해 평가
- Cold 일반 실험:
  - 학습 입력: `estimated_ho`
  - 학습 정답: `price_krw`
  - 평가: Cold test / Warm test 모두에 적용
- Cold ln 변환 실험:
  - 학습 입력: `ln_estimated_ho`
  - 학습 정답: `ln_price_krw`
  - 예측값은 다시 원화 가격으로 변환해 평가

## 6. 모델

- 기본 모델: Ridge 기반 헤도닉 선형 회귀
- 작가명은 one-hot encoding으로 처리
- 수치형 피처는 표준화 후 학습
- 이번 실험은 모델 성능 최적화가 아니라 `작가명 + 호수`, `ln 변환`의 기본 신호 확인이 목적

## 7. 생성 파일

- `warm_train_base_features.csv`
- `warm_train_base_labels.csv`
- `warm_train_log_features.csv`
- `warm_train_log_labels.csv`
- `warm_test_base_features.csv`
- `warm_test_log_features.csv`
- `warm_test_labels.csv`
- `cold_train_base_features.csv`
- `cold_train_base_labels.csv`
- `cold_train_log_features.csv`
- `cold_train_log_labels.csv`
- `cold_test_base_features.csv`
- `cold_test_log_features.csv`
- `cold_test_labels.csv`

## 8. 재현 방법

```bash
python3 experiments/track6/T6-E010_hedonic_artist_ho_log/scripts/run_experiment.py
python3 scripts/track6/generate_experiment_log_html.py experiments/track6/T6-E010_hedonic_artist_ho_log
```

- 실행 모델: Ridge 기반 Hedonic Linear Regression
- 비고: 초기 샘플 실행 일지라 기본 비교 모델군 통제 대상이 아님
