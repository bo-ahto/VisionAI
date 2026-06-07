# T6-E010 결과 요약

- 실험 목적: 작가명(한글)과 추정 호수만으로 가격 예측 신호가 있는지 확인
- 비교 목적: 원 가격/원 호수 조합과 ln 변환 조합 중 어떤 방식이 나은지 확인
- 모델: Ridge 기반 헤도닉 선형 회귀
- 데이터 원본: `data/track6/track6_feature_candidates_name_corrected.csv`
- 호수 생성: `area_cm2`를 기존 F형 호수 면적표와 비교해 가장 가까운 호수로 변환

## 데이터 구성

- train: 28,204건 / 1,987명
- warm_test: 2,445건 / 943명
- cold_test: 3,005건 / 156명
- Cold/train 작가 겹침: 0
- Warm test 작가별 train 최소 작품 수: 5
- Warm test 작가별 평가 최소 작품 수: 2

## 핵심 결과

- Warm 최고: `warm_model_warm_test_log` median APE `0.1946`
- Cold 최고: `warm_model_cold_test_log` median APE `0.4840`
- 낮을수록 좋은 지표: median APE, p95 APE, MAPE, RMSE(log)
- 높을수록 좋은 지표: Within-30, Within-50

## 생성 파일

- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/warm_train_base_features.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/warm_train_base_labels.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/warm_train_log_features.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/warm_train_log_labels.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/warm_test_base_features.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/warm_test_log_features.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/warm_test_labels.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/warm_test_metadata.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/cold_train_base_features.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/cold_train_base_labels.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/cold_train_log_features.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/cold_train_log_labels.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/cold_test_base_features.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/cold_test_log_features.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/cold_test_labels.csv`
- `experiments/track6/T6-E010_hedonic_artist_ho_log/data/cold_test_metadata.csv`

## 전체 지표

| experiment_case | n | median_ape | p95_ape | mape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cold_model_cold_test_base | 3005 | 2.4777 | 13.7330 | 4.1035 | 0.0855 | 0.1381 | 1.5241 |
| cold_model_cold_test_log | 3005 | 0.5083 | 2.8076 | 0.9455 | 0.2722 | 0.4902 | 0.8191 |
| cold_model_warm_test_base | 2445 | 2.0209 | 11.5371 | 3.4465 | 0.1018 | 0.1575 | 1.4277 |
| cold_model_warm_test_log | 2445 | 0.5431 | 2.6801 | 0.8577 | 0.3076 | 0.4695 | 0.8938 |
| warm_model_cold_test_base | 3005 | 2.5484 | 15.4060 | 4.3351 | 0.0942 | 0.1521 | 1.6076 |
| warm_model_cold_test_log | 3005 | 0.4840 | 2.7899 | 0.8906 | 0.3098 | 0.5288 | 0.7964 |
| warm_model_warm_test_base | 2445 | 0.4372 | 2.2297 | 0.8496 | 0.3836 | 0.5403 | 2.5057 |
| warm_model_warm_test_log | 2445 | 0.1946 | 0.8654 | 0.3249 | 0.6777 | 0.8519 | 0.4174 |
