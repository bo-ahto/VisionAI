# 재현 확인 노트

## 1. 기존 실험 재현 기준

기존 Track6 실험과 모델 성능표를 확인할 때는 아래 폴더를 기준으로 한다.

```text
03_frozen_training_dataset/track6_split/
```

이 폴더는 모델 번들 내부 기준 데이터셋과 checksum이 일치한다.

검증 결과:

```text
04_verification/verification_report.md
04_verification/checksum_manifest.csv
04_verification/row_count_summary.csv
```

## 2. 확인 순서

1. `README.md`에서 폴더 구조를 확인한다.
2. `00_docs/01_existing_experiment_dataset_lineage.md`에서 생성 흐름을 확인한다.
3. `00_docs/02_split_definition.md`에서 Warm/Cold split 기준을 확인한다.
4. `04_verification/verification_report.md`에서 row 수와 checksum 일치 여부를 확인한다.
5. 모델 실험을 재현할 때는 `03_frozen_training_dataset/track6_split/`을 입력으로 사용한다.
6. 원본 CSV부터 생성 절차를 확인해야 하면 `build_track6_frozen_dataset_from_sources.py`를 실행하고 `05_generated_frozen_training_dataset/verification/build_report.md`를 확인한다.

## 3. 재현 시 주의점

전체 원본 파이프라인을 다시 실행하는 것과 기존 실험 데이터셋을 재현하는 것은 다르다.

기존 실험 데이터셋 재현은 frozen split을 기준으로 한다.

전체 파이프라인 재실행은 원본 파일, 보정 테이블, 코드 버전, 중복 처리, 작가명 처리 결과에 따라 입력 후보가 달라질 수 있다. 이 경우 생성되는 split은 새 데이터셋 후보이며, 기존 실험 성능표의 기준으로 쓰면 안 된다.

공유 폴더의 `build_track6_frozen_dataset_from_sources.py`는 이 문제를 피하기 위해 현재 코드의 자동 split 결과를 최종 기준으로 쓰지 않는다. 원본 CSV 처리, 작가명 보정, 작가 메타 보강, NANT 재료 보강까지 실행한 뒤, 기존 실험에서 확정된 frozen membership을 적용해 train/validation/test 배정을 고정한다.

따라서 이 스크립트는 "현재 코드로 새 split을 찾는 도구"가 아니라 "원본 처리 흐름을 실행한 뒤 기존 frozen split 기준으로 결과를 고정하고 검증하는 도구"다.

실행 명령:

```bash
python3 docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/build_track6_frozen_dataset_from_sources.py
```

주요 출력:

```text
05_generated_frozen_training_dataset/track6_split/
05_generated_frozen_training_dataset/verification/build_report.md
05_generated_frozen_training_dataset/verification/build_summary.json
05_generated_frozen_training_dataset/verification/files_manifest.csv
```

## 4. 기존 실험 데이터셋 row 수

| 파일 | rows |
|---|---:|
| `track6_train.csv` | 26,914 |
| `track6_val_warm.csv` | 519 |
| `track6_test_warm.csv` | 607 |
| `track6_val_cold.csv` | 2,753 |
| `track6_test_cold.csv` | 3,099 |

## 5. 왜 frozen split이 필요한가

모델 성능은 train/validation/test 구성이 같을 때만 직접 재현할 수 있다.

작품 한두 개가 다른 split으로 이동하거나, 작가명이 다르게 보정되거나, Cold 작가 그룹이 달라지면 평가 대상 자체가 바뀐다. 그러면 성능 수치도 기존 실험과 직접 비교할 수 없다.

따라서 기존 실험의 성능을 설명하거나 이어서 실험할 때는 먼저 frozen split을 기준으로 맞춘 뒤 진행해야 한다.
