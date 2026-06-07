# Track6 A1 Ho/Size 전체 데이터 실험

- 실험 목적: 결과 양식 기준으로 `Ho / ln Ho / Size / ln Size` 변수별 Warm/Cold 모델 결과를 기록
- 기준 데이터: 고정된 Track6 feature/label split
- 학습 데이터: `data/track6_split/features/warm/track6_train_warm_features.csv` + `data/track6_split/labels/track6_train_labels.csv`
- Warm 테스트 데이터: `data/track6_split/features/warm/track6_test_warm_warm_features.csv` + `data/track6_split/labels/track6_test_warm_labels.csv`
- Cold 테스트 데이터: `data/track6_split/features/cold/track6_test_cold_cold_features.csv` + `data/track6_split/labels/track6_test_cold_labels.csv`
- 사용 코드: `experiments/track6/A1_ho_size_sample_result_sheet/scripts/run_sample_experiment.py`
- 사용 프롬프트: `experiments/track6/A1_ho_size_sample_result_sheet/prompts/used_prompt.md`
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건

## 데이터 사용 기준

- feature 파일은 모델 입력값이다.
- label 파일은 정답 가격이다.
- 학습 시에는 `train_features.csv`와 `train_labels.csv`를 `_track6_row_id`로 연결해 학습한다.
- 평가 시에는 테스트 feature로 예측한 뒤, 테스트 label과 `_track6_row_id`로 연결해 성능을 계산한다.
- 이 실험에서는 샘플링하지 않고 전체 split에서 A1 필수 값이 있는 행을 모두 사용한다.

## 모델 코드

- `A`: Warm Huber
- `B`: Warm Linear Regression
- `C`: Warm Ridge
- `D`: Cold Huber
- `E`: Cold Quantile-LAD
- `F`: Cold LightGBM

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
