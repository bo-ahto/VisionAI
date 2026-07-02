# 기존 Track6 실험 데이터셋 생성 흐름

이 문서는 기존 Track6 가격 예측 실험에서 사용한 데이터셋이 어떤 흐름으로 만들어졌는지 설명한다. 여기서 말하는 데이터셋은 모델 번들에 고정된 frozen split이며, 기존 성능표와 fixed test 결과의 기준이다.

## 1. 전체 흐름

```text
[1차 원본 CSV]
  - Saatchi
  - Artsy
  - Artue
  - Gallery primary
        |
        v
[Track4 raw 통합/정제]
  - 원본 row 추적 컬럼 부여
  - 가격, 크기, 재료/지지체 정리
  - 중복 후보와 학습 제외 사유 표시
        |
        v
[Track4 feature candidate 생성]
  - 가격이 있는 학습 후보와 예측 입력 후보를 포함한 작품 단위 후보 생성
        |
        v
[Track6 작가명 보정/동명이인 처리]
  - 한글 작가명 보정
  - 같은 한글명 안의 다른 작가 entity 분리
  - 작가 메타 보강
        |
        v
[Track6 split 생성]
  - train
  - validation warm
  - test warm
  - validation cold
  - test cold
        |
        v
[feature/label 분리]
  - Warm feature
  - Cold feature
  - label
        |
        v
[모델 번들 frozen split 고정]
  - 기존 실험과 모델 학습/평가 기준으로 고정
```

## 2. 원본 입력 파일

| 출처 | 공유 폴더 내 파일 |
|---|---|
| Saatchi | `01_source_files/saatchi_cleaned.csv` |
| Artsy | `01_source_files/artsy_kr_artworks.csv` |
| Artue | `01_source_files/artue_테스트_가격포함.csv` |
| Gallery primary | `01_source_files/1차 시장 데이터 - 전달본_260504.csv` |

## 3. Track4 정제 단계

Track4 단계에서는 여러 출처의 원본 데이터를 작품 단위로 통합하고, 모델 학습에 필요한 공통 컬럼으로 정리한다.

주요 처리:

- `track4_source`, `track4_source_row_index`로 원본 row 추적
- 가격을 원화 기준 `price_krw`로 정리
- `ln_price_krw` 로그 가격 생성
- `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio` 생성
- 매체/지지체를 `medium_category`, `support_category`로 정규화
- 학습에 쓰기 어려운 row는 삭제하지 않고 `is_training_candidate=False` 또는 audit flag로 표시
- 중복 후보는 대표 여부와 사유를 남김

관련 코드:

```text
02_pipeline_code/track4/run_cleaning_pipeline.py
02_pipeline_code/track4/build_primary_market_cleaned_v1.py
02_pipeline_code/track4/build_primary_market_cleaned_v2.py
02_pipeline_code/track4/audit_*.py
```

## 4. Track6 작가명 보정과 동명이인 처리

Track6 단계에서는 가격 예측 split을 만들기 전에 작가 식별 정보를 보정한다.

주요 처리:

- 작가 한글명을 보정해 `artist_name_ko`를 안정화
- 기존 한글명은 `artist_name_ko_orig`로 보존
- 같은 한글명에 여러 작가가 섞일 수 있는 경우 `artist_key`와 `artist_entity_suffix`로 분리
- Cold split에서 train과 같은 작가가 섞이지 않도록 `artist_key`, `artist_name_ko`, `artist_name_ko_orig`를 함께 확인
- 작가 메타는 row 단위 추적 키로 붙이며, 기본 feature export에서는 필요한 범위만 사용

관련 코드:

```text
02_pipeline_code/track6/improve_artist_korean_names.py
02_pipeline_code/track6/enrich_track6_artist_metadata.py
02_pipeline_code/track6/artist_ko_overrides.csv
```

## 5. Track6 split 생성

split 생성은 `02_pipeline_code/track6/create_track6_splits.py`의 기준을 따른다.

핵심 기준:

- random seed: `20260518`
- target: `ln_price_krw`, `price_krw`
- Warm 평가셋은 train에 같은 작가의 작품이 최소 5건 이상 남도록 구성
- Cold 평가셋은 train과 작가가 겹치지 않도록 구성
- Cold 겹침 검사는 `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 모두 사용
- train/eval 동일 작품 후보는 제거
- split 후 `artist_works_count_train`, `artist_works_log`는 train 기준으로 다시 계산

기존 실험의 최종 split:

| split | rows | 파일 |
|---|---:|---|
| train | 26,914 | `03_frozen_training_dataset/track6_split/track6_train.csv` |
| val_warm | 519 | `03_frozen_training_dataset/track6_split/track6_val_warm.csv` |
| test_warm | 607 | `03_frozen_training_dataset/track6_split/track6_test_warm.csv` |
| val_cold | 2,753 | `03_frozen_training_dataset/track6_split/track6_val_cold.csv` |
| test_cold | 3,099 | `03_frozen_training_dataset/track6_split/track6_test_cold.csv` |

## 6. feature/label 분리

split 이후 모델 학습용 feature와 평가 label을 분리한다.

관련 코드:

```text
02_pipeline_code/track6/export_feature_label_splits.py
```

출력:

```text
03_frozen_training_dataset/track6_split/features/warm/
03_frozen_training_dataset/track6_split/features/cold/
03_frozen_training_dataset/track6_split/labels/
```

Warm feature는 같은 작가 이력을 사용할 수 있는 입력을 대상으로 한다.

Cold feature는 같은 작가 가격 이력을 직접 쓰지 않는 입력을 대상으로 하므로, `artist_key`, `artist_works_log`, `artist_works_count_train`처럼 같은 작가 이력 누수 가능성이 있는 컬럼을 feature에서 제외한다.

## 7. frozen split으로 고정한 이유

데이터셋 생성 파이프라인은 원본 파일, 보정 테이블, 작가명 처리, 중복 처리, 코드 버전에 영향을 받는다. 따라서 시간이 지난 뒤 전체 파이프라인을 다시 실행하면 같은 이름의 스크립트를 쓰더라도 입력 후보가 달라질 수 있다.

기존 실험의 성능 수치와 fixed test 결과를 재현하려면 당시 확정한 split을 그대로 써야 한다. 그래서 모델 후보를 고정하는 시점에 아래 경로의 데이터셋을 모델 번들 내부에 보관했다.

```text
models/track6/price_prediction_v0.1/data/training/track6_split/
```

이 공유 패키지의 `03_frozen_training_dataset/track6_split/`은 위 모델 번들 기준 데이터셋의 복사본이다.

## 8. 원본 CSV부터 frozen output까지 한 번에 확인하는 스크립트

공유 폴더에는 아래 생성 스크립트가 포함되어 있다.

```text
build_track6_frozen_dataset_from_sources.py
```

이 스크립트는 `01_source_files/`의 원본 CSV를 repo의 `data/` 위치에 복사한 뒤, Track4/Track6 처리 단계를 순서대로 실행한다.

실행 단계:

```text
[01_source_files 원본 CSV 복사]
        |
        v
[Track4 raw 통합/정제]
        |
        v
[Track6 작가명 보정]
        |
        v
[작가 메타 보강]
        |
        v
[NANT 재료/지지체 보강]
        |
        v
[기존 frozen membership 적용]
        |
        v
[feature/label 생성 및 검증]
        |
        v
[05_generated_frozen_training_dataset/track6_split 출력]
```

중요한 점은 split을 새로 무작위 생성하지 않는다는 것이다. 현재 코드의 자동 split 결과를 그대로 쓰면 기존 실험 기준과 달라질 수 있으므로, 기존 실험에서 확정된 membership을 적용해 최종 train/validation/test 배정을 고정한다.

실행 명령:

```bash
python3 docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/build_track6_frozen_dataset_from_sources.py
```

실행 결과는 아래 리포트에서 확인한다.

```text
05_generated_frozen_training_dataset/verification/build_report.md
```
