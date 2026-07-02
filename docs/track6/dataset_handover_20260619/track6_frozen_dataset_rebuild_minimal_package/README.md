# Track6 dataset build package

이 폴더는 원본 CSV에서 Track6 데이터셋을 생성하고 검증하기 위한 최소 공유 패키지다. frozen 기준 파일이 있으면 기존 실험 데이터셋을 재현하고, 없으면 현재 코드 기준 자동 split으로 새 데이터셋을 만든다.

## 1. 목적

이 패키지는 두 용도를 모두 지원한다. 기본값은 frozen 기준 파일이 있으면 기존 실험에서 확정된 split을 재현하고, 기준 파일이 없으면 현재 코드 기준으로 새 train/validation/test split을 만든다.

## 2. 포함 파일

필수 원본 파일:

```text
01_source_files/saatchi_cleaned.csv
01_source_files/artsy_kr_artworks.csv
01_source_files/artue_테스트_가격포함.csv
01_source_files/1차 시장 데이터 - 전달본_260504.csv
01_source_files/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv
```

선택 frozen 기준 파일:

```text
02_frozen_reference/track6_split_membership.csv
02_frozen_reference/track6_identity_overrides.csv
```

이 두 파일이 있으면 기존 실험 데이터셋을 재현한다. 이 두 파일이 없으면 현재 코드의 자동 split 정책으로 새 데이터셋을 생성한다.

`track6_train.csv`, `features/`, `labels/` 같은 완성 데이터셋 파일은 입력으로 필요하지 않다. 이 파일들은 스크립트 실행 결과로 새로 생성된다.

실행 스크립트:

```text
build_track6_dataset_from_source_files.py
step_01_prepare_source_files.py
step_02_run_cleaning_enrichment.py
step_03_create_split.py
step_04_export_feature_label.py
step_05_copy_verify_output.py
```

## 3. 실행 방법

### 3.1 통합 실행

패키지 폴더로 이동해서 실행하는 방식을 기본으로 안내한다.

```bash
cd track6_frozen_dataset_rebuild_minimal_package
python3 build_track6_dataset_from_source_files.py
```

기본값은 `frozen-if-available`이다.

- `02_frozen_reference/` 기준 파일 2개가 있으면 기존 실험 split을 재현한다.
- 기준 파일이 없으면 자동 split으로 새 dataset을 만든다.
- 기존 실험 재현을 강제하려면 `--split-mode frozen`을 사용한다.
- 새 자동 split 생성을 강제하려면 `--split-mode auto`를 사용한다.

```bash
python3 build_track6_dataset_from_source_files.py --split-mode frozen
python3 build_track6_dataset_from_source_files.py --split-mode auto
```

실행 전 계획만 확인하려면:

```bash
cd track6_frozen_dataset_rebuild_minimal_package
python3 build_track6_dataset_from_source_files.py --dry-run
```

현재 터미널 위치가 패키지 폴더가 아니어도 실행은 가능하다. 이 경우에는 각자 패키지를 풀어둔 경로를 사용하면 된다.

```bash
python3 /path/to/track6_frozen_dataset_rebuild_minimal_package/build_track6_dataset_from_source_files.py
```

스크립트는 자기 자신의 위치를 기준으로 VisionAI repo root를 찾고, 기존 파이프라인은 repo root에서 실행한다. 따라서 패키지 폴더는 VisionAI repo 안에 있어야 한다.

데이터셋 생성 흐름은 아래 문서에 따로 정리했다.

```text
DATASET_GENERATION_FLOW.md
```

### 3.2 단계별 실행

문제 원인을 단계별로 확인하거나, 특정 단계부터 다시 실행해야 할 때는 아래 py 파일을 순서대로 실행한다.

```bash
cd track6_frozen_dataset_rebuild_minimal_package

# 1. 원본 CSV를 repo data/ 위치로 복사
python3 step_01_prepare_source_files.py

# 2. Track4 정제 + Track6 작가명/작가메타/NANT 보강
python3 step_02_run_cleaning_enrichment.py

# 3. split 생성
# 기본값: frozen reference가 있으면 frozen, 없으면 auto
python3 step_03_create_split.py

# 필요하면 split mode를 명시
python3 step_03_create_split.py --split-mode frozen
python3 step_03_create_split.py --split-mode auto

# 4. feature/label export
python3 step_04_export_feature_label.py

# 5. 패키지 output 폴더로 복사 + legacy feature/label 재생성 + 검증 리포트 작성
python3 step_05_copy_verify_output.py
```

각 단계는 `--dry-run`을 지원한다. 단, `step_05_copy_verify_output.py`는 실제 생성된 `data/track6_split`이 있어야 검증할 수 있으므로 dry-run을 제공하지 않는다.

## 4. 출력 위치

결과 데이터는 같은 패키지 폴더 아래에 생성된다.

```text
05_generated_frozen_training_dataset/track6_split/
05_generated_frozen_training_dataset/verification/build_report.md
05_generated_frozen_training_dataset/verification/build_summary.json
05_generated_frozen_training_dataset/verification/files_manifest.csv
```

## 5. 주의사항

- 실행 중 기존 Track4/Track6 파이프라인이 repo의 `data/` 산출물을 갱신한다.
- 최종 공유/검증 대상 결과는 이 패키지 안의 `05_generated_frozen_training_dataset/`이다.
- frozen mode에서는 현재 코드의 자동 split을 최종 기준으로 쓰지 않고, 이 패키지에 포함된 `track6_split_membership.csv`를 적용한다.
- frozen mode의 동명이인/작가명 고정은 완성 데이터셋 전체가 아니라 `track6_identity_overrides.csv`만 사용한다.
- auto mode에서는 frozen reference를 쓰지 않고 현재 `scripts/track6/create_track6_splits.py` 정책으로 split을 새로 만든다.
- 생성 결과가 기존 기준과 다르면 원본 파일, 보정 테이블, 코드 버전, frozen membership 적용 중 하나가 달라진 것이다.

## 6. 정상 결과 기준

정상 실행 시 `build_report.md`에 아래 조건이 모두 PASS로 기록된다.

frozen mode에서는 기존 실험 기준과 row/column 수가 정확히 일치해야 한다.

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

추가로 Warm 평가셋은 train에 같은 작가 이력 5건 이상이 있어야 하고, Cold 평가셋은 train과 작가 식별자가 겹치면 안 된다.

auto mode에서는 row 수가 새 split 정책에 따라 달라질 수 있으므로, 고정 row 수 일치가 아니라 파일 생성 여부, 컬럼 구조, Warm/Cold split 조건을 검증한다.
