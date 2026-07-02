# Track6 stepwise source-only dataset build package

이 폴더는 원본 CSV만 포함하고, 각 처리 단계를 하나씩 실행해 Track6 데이터셋을 생성할 수 있게 만든 공유 패키지다.

완성 데이터셋 파일은 포함하지 않는다. 실행 후 `05_generated_dataset/` 아래에 생성된다.

## 포함 파일

```text
01_source_files/
  saatchi_cleaned.csv
  artsy_kr_artworks.csv
  artue_테스트_가격포함.csv
  1차 시장 데이터 - 전달본_260504.csv
  k-artmarket 1차 데이터 정제 - 실험데이터분류.csv

build_track6_dataset_from_source_files.py
run_all_auto_steps.py
run_all_frozen_steps.py
step_01_prepare_source_files.py
step_02_track4_cleaning.py
step_03_artist_name_correction.py
step_04_artist_meta_enrichment.py
step_05_nant_material_enrichment.py
step_06a_create_auto_split.py
step_06b_create_frozen_split.py
step_07_export_feature_label.py
step_08a_copy_verify_auto_output.py
step_08b_copy_verify_frozen_output.py
```

## Auto Split 실행

이 source-only 패키지의 기본 사용 방식이다. frozen reference 없이 현재 코드의 자동 split 정책으로 새 데이터셋을 만든다.

```bash
cd track6_dataset_stepwise_source_only_package

python3 step_01_prepare_source_files.py
python3 step_02_track4_cleaning.py
python3 step_03_artist_name_correction.py
python3 step_04_artist_meta_enrichment.py
python3 step_05_nant_material_enrichment.py
python3 step_06a_create_auto_split.py
python3 step_07_export_feature_label.py
python3 step_08a_copy_verify_auto_output.py
```

한 번에 실행하려면:

```bash
python3 run_all_auto_steps.py
```

## Frozen Split 실행

기존 실험 split을 재현해야 할 때만 사용한다. 먼저 아래 기준 파일을 추가해야 한다.

```text
02_frozen_reference/track6_split_membership.csv
02_frozen_reference/track6_identity_overrides.csv
```

그 다음 아래처럼 실행한다.

```bash
cd track6_dataset_stepwise_source_only_package

python3 step_01_prepare_source_files.py
python3 step_02_track4_cleaning.py
python3 step_03_artist_name_correction.py
python3 step_04_artist_meta_enrichment.py
python3 step_05_nant_material_enrichment.py
python3 step_06b_create_frozen_split.py
python3 step_07_export_feature_label.py
python3 step_08b_copy_verify_frozen_output.py
```

한 번에 실행하려면:

```bash
python3 run_all_frozen_steps.py
```

## 단계별 역할

| 단계 | Auto 파일 | Frozen 파일 | 역할 |
|---:|---|---|---|
| 1 | `step_01_prepare_source_files.py` | 동일 | 원본 CSV를 repo `data/` 위치로 복사 |
| 2 | `step_02_track4_cleaning.py` | 동일 | 원본 row 통합, 가격/크기/재료/지지체/중복 기본 정제, Track6 후보 기반 생성 |
| 3 | `step_03_artist_name_correction.py` | 동일 | 한글 작가명 보정, 원래 작가명 보존, 동명이인 suffix 반영 |
| 4 | `step_04_artist_meta_enrichment.py` | 동일 | 원본 수집 row의 작가 메타 컬럼을 후보 데이터에 병합 |
| 5 | `step_05_nant_material_enrichment.py` | 동일 | NANT 기준표로 재료/지지체/도구 보강 컬럼 생성 |
| 6 | `step_06a_create_auto_split.py` | `step_06b_create_frozen_split.py` | train / val_warm / test_warm / val_cold / test_cold 생성 |
| 7 | `step_07_export_feature_label.py` | 동일 | Warm/Cold feature와 label 파일 생성 |
| 8 | `step_08a_copy_verify_auto_output.py` | `step_08b_copy_verify_frozen_output.py` | 패키지 output으로 복사, legacy feature/label 재생성, 검증 리포트 작성 |

## 출력

```text
05_generated_dataset/track6_split/
05_generated_dataset/verification/build_report.md
05_generated_dataset/verification/build_summary.json
05_generated_dataset/verification/files_manifest.csv
```
