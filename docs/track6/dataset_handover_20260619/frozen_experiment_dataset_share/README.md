# Track6 기존 실험 데이터셋 공유 패키지

이 폴더는 Track6 기존 가격 예측 실험에서 사용한 학습/검증/테스트 데이터셋을 다른 팀원이 확인할 수 있게 정리한 공유용 패키지다.

범위는 **기존 실험 데이터셋이 어떻게 만들어졌는지**에 한정한다. 현재 코드로 새로 재생성한 데이터셋 후보나 이후 실험 데이터셋 설명은 포함하지 않는다.

## 1. 가장 먼저 볼 문서

| 문서 | 용도 |
|---|---|
| `00_docs/01_existing_experiment_dataset_lineage.md` | 기존 실험 데이터셋 생성 흐름 설명 |
| `00_docs/02_split_definition.md` | train/validation/test, Warm/Cold split 기준 설명 |
| `00_docs/03_reproduction_notes.md` | 재현 시 주의점과 확인 순서 |
| `04_verification/verification_report.md` | 공유 폴더의 frozen dataset이 모델 번들 기준과 같은지 검증 |
| `run_frozen_dataset_audit.py` | 공유 폴더 기준 데이터셋을 한 번에 점검하는 종합 스크립트 |
| `build_track6_frozen_dataset_from_sources.py` | 원본 CSV에서 Track6 split 생성 후 frozen output으로 고정하는 종합 생성 스크립트 |

## 2. 폴더 구성

| 폴더 | 내용 |
|---|---|
| `01_source_files/` | 당시 파이프라인의 1차 입력 원본 CSV. 생성 스크립트는 이 폴더 또는 공유 폴더 직하위에서 원본 파일을 찾는다 |
| `02_pipeline_code/` | 데이터셋 생성 흐름을 확인하기 위한 관련 코드 스냅샷 |
| `03_frozen_training_dataset/track6_split/` | 기존 실험과 모델 학습/평가에 사용한 고정 데이터셋 |
| `04_verification/` | 기존 frozen dataset의 row count와 checksum 검증 결과 |
| `05_generated_frozen_training_dataset/` | `build_track6_frozen_dataset_from_sources.py` 실행 결과로 생성되는 재현 산출물 |

## 3. 기준 데이터셋

기존 Track6 실험과 모델 성능표의 기준 데이터셋은 아래 복사본이다.

```text
03_frozen_training_dataset/track6_split/
```

이 폴더는 모델 번들 내부의 기준 데이터셋과 SHA256 checksum이 일치한다.

원본 기준 위치:

```text
models/track6/price_prediction_v0.1/data/training/track6_split/
```

## 4. 핵심 row 수

| split | rows | 의미 |
|---|---:|---|
| `track6_train.csv` | 26,914 | 모델 학습용 |
| `track6_val_warm.csv` | 519 | Warm 검증용 |
| `track6_test_warm.csv` | 607 | Warm fixed test |
| `track6_val_cold.csv` | 2,753 | Cold 검증용 |
| `track6_test_cold.csv` | 3,099 | Cold fixed test |

## 5. 해석 기준

- 이 패키지의 목적은 기존 실험 결과를 설명하고 검증하는 것이다.
- 기존 성능표의 `n`은 이 frozen split 안의 평가 행 수다.
- 기존 실험 결과를 재현할 때는 이 frozen split을 기준으로 사용한다.
- 기존 성능표 재현 기준은 `03_frozen_training_dataset/track6_split/`이다.
- 원본 CSV부터 생성 절차를 확인해야 할 때는 `build_track6_frozen_dataset_from_sources.py`를 사용한다.
- 단, 이 스크립트는 현재 코드의 자동 split 결과를 그대로 쓰지 않고, 기존 실험에서 확정된 frozen membership을 적용해 최종 split을 고정한다. 그래서 원본 처리 흐름은 확인하면서도 기존 실험 데이터셋 기준에서 벗어나지 않게 한다.

## 6. 원본 CSV에서 frozen split 생성하기

아래 명령은 공유 폴더 또는 `01_source_files/`의 원본 CSV를 repo의 `data/` 위치에 배치한 뒤, Track4/Track6 데이터셋 생성 파이프라인을 순서대로 실행한다. 이후 현재 코드의 자동 split을 그대로 채택하지 않고, 기존 실험에서 확정된 `track6_split_membership.csv`를 적용해 frozen split을 다시 만든다.

이 스크립트의 목적은 새 split 후보를 만드는 것이 아니라, 기존 실험에 사용된 frozen dataset이 원본 처리 흐름과 어떤 관계인지 한 번에 재현하고 점검하는 것이다.

```bash
python3 docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/build_track6_frozen_dataset_from_sources.py
```

기본 출력:

```text
05_generated_frozen_training_dataset/track6_split/
05_generated_frozen_training_dataset/verification/build_report.md
05_generated_frozen_training_dataset/verification/build_summary.json
05_generated_frozen_training_dataset/verification/files_manifest.csv
```

생성 스크립트가 찾는 필수 입력 파일:

```text
saatchi_cleaned.csv
artsy_kr_artworks.csv
artue_테스트_가격포함.csv
1차 시장 데이터 - 전달본_260504.csv
track6_reference/k-artmarket 1차 데이터 정제 - 실험데이터분류.csv
03_frozen_training_dataset/track6_split/track6_split_membership.csv
03_frozen_training_dataset/track6_split/features/
03_frozen_training_dataset/track6_split/labels/
```

원본 CSV는 공유 폴더 직하위에 직접 두거나 `01_source_files/` 아래에 둘 수 있다. 결과 데이터는 같은 공유 폴더의 `05_generated_frozen_training_dataset/` 아래에 생성된다.

실행 전 계획만 확인하려면:

```bash
python3 docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/build_track6_frozen_dataset_from_sources.py --dry-run
```

주의:

- 이 스크립트는 repo의 `data/` 산출물을 갱신한다.
- 기존 성능표 재현 기준은 이미 포함된 `03_frozen_training_dataset/track6_split/`이다.
- 생성 결과는 `05_generated_frozen_training_dataset/track6_split/`에 저장된다.
- 생성 결과가 기존 기준과 다르면 원본 파일, 보정 테이블, 코드 버전, frozen membership 적용 중 하나가 기존 실험 기준과 달라진 것이다.

## 7. 기존 frozen split 한 번에 점검하기

아래 명령을 repo root에서 실행하면 공유 폴더의 frozen split을 종합 점검한다.

```bash
python3 docs/track6/dataset_handover_20260619/frozen_experiment_dataset_share/run_frozen_dataset_audit.py
```

점검 내용:

- 모델 번들 기준 split과 공유 폴더 split의 SHA256 checksum 일치 여부
- full split, feature, label 파일의 row/column 수
- Warm validation/test가 train에 같은 작가 이력 5건 이상을 갖는지
- Cold validation/test가 train과 작가 식별자/한글명 기준으로 겹치지 않는지
- Cold feature에 `artist_key`, `artist_works_log`, `artist_works_count_train` 같은 누수 가능 컬럼이 없는지
- feature와 label의 `_track6_row_id` 정렬이 맞는지

결과 파일:

```text
04_verification/frozen_dataset_audit_report.md
04_verification/frozen_dataset_audit_summary.json
```
