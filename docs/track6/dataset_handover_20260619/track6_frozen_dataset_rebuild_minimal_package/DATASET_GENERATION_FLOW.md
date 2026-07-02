# Track6 dataset 생성 흐름

이 문서는 `build_track6_dataset_from_source_files.py`가 원본 CSV에서 Track6 데이터셋을 생성하는 흐름을 설명한다.

## 1. 이 패키지의 목적

목적은 기존 Warm/Cold 실험에서 사용한 데이터셋이 어떤 원본 파일과 어떤 처리 순서로 만들어졌는지 공유하고, 필요하면 같은 기준의 frozen dataset을 다시 생성해 검증하는 것이다. frozen 기준 파일이 없을 때는 현재 코드 기준 자동 split으로 신규 데이터셋을 생성할 수 있다.

기본 동작은 `frozen-if-available`이다. 패키지에 `02_frozen_reference/track6_split_membership.csv`와 `track6_identity_overrides.csv`가 있으면 기존 실험 split을 재현하고, 두 파일이 없으면 현재 코드의 자동 split 정책으로 새 데이터셋을 만든다.

## 2. 입력 파일

원본 CSV는 `01_source_files/` 아래에 둔다.

```text
01_source_files/saatchi_cleaned.csv
01_source_files/artsy_kr_artworks.csv
01_source_files/artue_테스트_가격포함.csv
01_source_files/1차 시장 데이터 - 전달본_260504.csv
01_source_files/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv
```

기존 실험 재현에 쓰는 frozen 기준 파일은 `02_frozen_reference/` 아래에 둔다.

```text
track6_split_membership.csv
track6_identity_overrides.csv
```

`track6_train.csv`, `features/`, `labels/` 같은 완성 데이터셋 파일은 입력으로 쓰지 않는다. 이 파일들은 스크립트가 원본 CSV와 frozen 기준 파일을 사용해 새로 만든다.

## 3. 전체 처리 순서

```text
[원본 CSV]
  saatchi / artsy / artue / 1차 시장 데이터 / NANT 기준표
        |
        v
[Track4 정제 파이프라인]
  - 원본 row 통합
  - 가격, 크기, 재료, 지지체, 중복 등 기본 정제
  - Track6 후보 데이터 생성
        |
        v
[Track6 작가명 보정]
  - 검수된 override 기준으로 한글 작가명 보정
  - 원래 작가명은 별도 컬럼으로 보존
  - 동명이인 구분 suffix 반영
        |
        v
[작가 메타 정보 보강]
  - 원본 수집 row에서 작가 메타 컬럼을 후보 데이터에 병합
        |
        v
[NANT 재료/지지체 보강]
  - NANT 기준표로 재료, 지지체, 도구 관련 보강 컬럼 생성
        |
        v
[split 생성]
  - frozen mode: 기존 실험에서 확정한 track6_row_id와 split 값을 적용
  - frozen mode: 동명이인/작가명은 track6_identity_overrides.csv로 고정
  - auto mode: 현재 scripts/track6/create_track6_splits.py 정책으로 새 split 생성
  - 결과: train / val_warm / test_warm / val_cold / test_cold 생성
        |
        v
[feature / label 파일 생성]
  - Warm feature
  - Cold feature
  - label 파일 분리
  - 기존 v0.1 실험 당시의 legacy feature 컬럼 기준으로 재생성
        |
        v
[검증 리포트 생성]
  - row 수, column 수 확인
  - Warm 평가셋의 train 작가 이력 5건 이상 조건 확인
  - Cold 평가셋의 train 작가 겹침 없음 확인
  - 파일별 checksum manifest 생성
```

## 4. frozen membership을 쓰는 이유

현재 코드로 split을 다시 만들면 같은 원본 파일을 쓰더라도 결과가 달라질 수 있다.

이유는 작가명 보정, 동명이인 처리, 메타 보강, split 생성 코드가 시간이 지나며 바뀔 수 있기 때문이다. split row가 바뀌면 Warm 607건, Cold 3,099건 기준의 성능표도 같은 의미로 재현되지 않는다.

그래서 기존 실험에서 확정한 `track6_split_membership.csv`를 사용한다. 이 파일은 각 row가 train, validation, test 중 어디에 들어갔는지 고정한 명세다.

## 5. 실행 위치와 출력 위치

기본 실행 방식은 패키지 폴더로 이동해서 스크립트를 실행하는 것이다.

```bash
cd track6_frozen_dataset_rebuild_minimal_package
python3 build_track6_dataset_from_source_files.py
```

split 모드를 강제로 지정할 수도 있다.

```bash
python3 build_track6_dataset_from_source_files.py --split-mode frozen
python3 build_track6_dataset_from_source_files.py --split-mode auto
```

현재 터미널 위치가 패키지 폴더가 아니어도 실행은 가능하다. 이 경우에는 각자 패키지를 풀어둔 경로를 사용한다.

```bash
python3 /path/to/track6_frozen_dataset_rebuild_minimal_package/build_track6_dataset_from_source_files.py
```

스크립트는 자기 자신의 위치를 기준으로 VisionAI repo root를 찾고, 기존 Track4/Track6 파이프라인은 repo root에서 실행한다.

역할별로 나누어 실행할 수도 있다.

```bash
python3 step_01_prepare_source_files.py
python3 step_02_run_cleaning_enrichment.py
python3 step_03_create_split.py
python3 step_04_export_feature_label.py
python3 step_05_copy_verify_output.py
```

역할은 아래와 같다.

| 파일 | 역할 |
|---|---|
| `step_01_prepare_source_files.py` | 원본 CSV를 repo `data/` 경로로 복사 |
| `step_02_run_cleaning_enrichment.py` | Track4 정제, 작가명 보정, 작가 메타 보강, NANT 보강 |
| `step_03_create_split.py` | frozen 또는 auto 방식으로 train/validation/test split 생성 |
| `step_04_export_feature_label.py` | repo `data/track6_split` 기준 feature/label export |
| `step_05_copy_verify_output.py` | 패키지 output으로 복사, legacy feature/label 재생성, 검증 리포트 작성 |

최종 결과는 패키지 폴더 아래에 생성된다.

```text
05_generated_frozen_training_dataset/track6_split/
05_generated_frozen_training_dataset/verification/build_report.md
05_generated_frozen_training_dataset/verification/build_summary.json
05_generated_frozen_training_dataset/verification/files_manifest.csv
```

## 6. 정상 생성 기준

정상 생성 시 `verification/build_report.md`의 audit status가 `pass`여야 한다.

frozen mode의 주요 기준은 아래와 같다.

| 파일 | rows | columns |
|---|---:|---:|
| `track6_train.csv` | 26,914 | 50 |
| `track6_val_warm.csv` | 519 | 50 |
| `track6_test_warm.csv` | 607 | 50 |
| `track6_val_cold.csv` | 2,753 | 50 |
| `track6_test_cold.csv` | 3,099 | 50 |
| Warm feature files | split별 row 수 동일 | 23 |
| Cold feature files | split별 row 수 동일 | 20 |
| label files | split별 row 수 동일 | 12 |

Warm 평가셋은 train에 같은 작가 이력이 5건 이상 있어야 한다.

Cold 평가셋은 train과 `artist_key`, `artist_name_ko`, `artist_name_ko_orig`가 겹치면 안 된다.

auto mode에서는 row 수가 새 split 정책에 따라 달라질 수 있다. 따라서 고정 row 수 일치가 아니라 파일 생성 여부, 컬럼 구조, Warm/Cold split 조건을 중심으로 검증한다.

## 7. 결과가 달라질 때 확인할 것

생성 결과가 기존 frozen 기준과 다르면 아래를 확인한다.

1. `01_source_files/`의 원본 파일이 기존 실험 당시 파일과 같은지
2. NANT 기준표 파일이 같은지
3. frozen mode라면 `track6_split_membership.csv`가 기존 기준 파일인지
4. 작가명 보정/동명이인 처리 코드가 변경되었는지
5. feature export 기준이 기존 v0.1 legacy 컬럼 기준으로 적용되었는지

기존 성능표 재현 기준은 `02_frozen_reference/track6_split_membership.csv`의 split 배정과 `02_frozen_reference/track6_identity_overrides.csv`의 작가명/동명이인 고정 기준이다. 신규 데이터셋 생성은 `--split-mode auto` 결과를 별도 기준으로 관리한다.
