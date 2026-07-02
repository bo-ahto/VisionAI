# Track6 기존 학습/테스트 데이터셋 검증 리포트

- 검증일: 2026-06-19
- 기준 데이터셋: `models/track6/price_prediction_v0.1/data/training/track6_split/`
- 목적: 그동안 모델 학습/평가에 사용한 frozen split을 패키지로 공유할 수 있는지 확인
- 제외: 운영 DB/API/cache 생성

## 1. 결론

- 모델 번들 frozen split과 패키지 복사본 SHA256 전체 일치: `True`
- `data/track6_split/`도 frozen split과 byte 단위로 일치: `True`
- Track6 split status: `pass`
- feature/label manifest status: `pass`
- feature leak columns 존재 여부: `False`

## 2. 왜 현재 코드 재실행 숫자와 달라졌는가

- `models/track6/price_prediction_v0.1/data/training/track6_split/`은 모델 번들 생성 시점에 고정된 학습/평가 스냅샷이다.
- `data/track6_split/`은 생성 스크립트가 쓰는 작업용 산출물이라 현재 코드/현재 입력으로 다시 돌리면 달라질 수 있다.
- 기존 모델 학습/평가 재현 기준은 작업용 재생성 결과가 아니라 모델 번들 안의 frozen split이다.

## 3. frozen split row 수

| 파일 | rows | columns |
|---|---:|---:|
| `models/track6/price_prediction_v0.1/data/training/track6_split/track6_train.csv` | `26,914` | `50` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/track6_val_warm.csv` | `519` | `50` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/track6_test_warm.csv` | `607` | `50` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/track6_val_cold.csv` | `2,753` | `50` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/track6_test_cold.csv` | `3,099` | `50` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/features/warm/track6_train_warm_features.csv` | `26,914` | `23` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/features/warm/track6_val_warm_warm_features.csv` | `519` | `23` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/features/warm/track6_test_warm_warm_features.csv` | `607` | `23` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/features/cold/track6_train_cold_features.csv` | `26,914` | `20` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/features/cold/track6_val_cold_cold_features.csv` | `2,753` | `20` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/features/cold/track6_test_cold_cold_features.csv` | `3,099` | `20` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/labels/track6_train_labels.csv` | `26,914` | `12` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/labels/track6_val_warm_labels.csv` | `519` | `12` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/labels/track6_test_warm_labels.csv` | `607` | `12` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/labels/track6_val_cold_labels.csv` | `2,753` | `12` |
| `models/track6/price_prediction_v0.1/data/training/track6_split/labels/track6_test_cold_labels.csv` | `3,099` | `12` |

## 4. split 검증

- val_warm_artists_all_in_train: `True`
- val_warm_min_train_count: `5`
- val_warm_meets_min_rows: `True`
- val_warm_meets_min_artists: `True`
- test_warm_artists_all_in_train: `True`
- test_warm_min_train_count: `5`
- test_warm_meets_min_rows: `True`
- test_warm_meets_min_artists: `True`
- val_cold_overlap_train_artist_key: `0`
- val_cold_overlap_train_artist_name_ko: `0`
- val_cold_overlap_train_artist_name_ko_orig: `0`
- val_cold_artist_works_log_nonzero: `0`
- val_cold_meets_min_rows: `True`
- val_cold_meets_min_artists: `True`
- test_cold_overlap_train_artist_key: `0`
- test_cold_overlap_train_artist_name_ko: `0`
- test_cold_overlap_train_artist_name_ko_orig: `0`
- test_cold_artist_works_log_nonzero: `0`
- test_cold_meets_min_rows: `True`
- test_cold_meets_min_artists: `True`
- train_eval_duplicate_key_overlap: `0`

## 5. 전달 기준

- 협업자에게는 `frozen_training_dataset/track6_split/`을 학습/테스트 기준 데이터셋으로 전달한다.
- `pipeline_code/`는 생성 로직 참고용이다. 기존 모델 결과를 그대로 재현하려면 frozen split을 사용해야 한다.
- 현재 코드로 전체 파이프라인을 다시 실행하는 것은 새 데이터셋 생성이며, 기존 학습셋 재현과 구분한다.
