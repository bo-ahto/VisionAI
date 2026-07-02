# Track6 단계별 데이터셋 생성 흐름

## Auto Split 흐름

```text
[원본 CSV]
        |
        v
[1. 원본 파일 배치]
  step_01_prepare_source_files.py
        |
        v
[2. Track4 정제 파이프라인]
  step_02_track4_cleaning.py
  - 원본 row 통합
  - 가격/크기/재료/지지체/중복 기본 정제
  - Track6 후보 데이터 기반 생성
        |
        v
[3. Track6 작가명 보정]
  step_03_artist_name_correction.py
        |
        v
[4. 작가 메타 정보 보강]
  step_04_artist_meta_enrichment.py
        |
        v
[5. NANT 재료/지지체 보강]
  step_05_nant_material_enrichment.py
        |
        v
[6A. 자동 split 생성]
  step_06a_create_auto_split.py
        |
        v
[7. feature / label 파일 생성]
  step_07_export_feature_label.py
        |
        v
[8A. auto output 복사 및 검증]
  step_08a_copy_verify_auto_output.py
```

## Frozen Split 흐름

```text
[원본 CSV + 02_frozen_reference]
        |
        v
[1~5. 동일 전처리]
  step_01_prepare_source_files.py
  step_02_track4_cleaning.py
  step_03_artist_name_correction.py
  step_04_artist_meta_enrichment.py
  step_05_nant_material_enrichment.py
        |
        v
[6B. frozen split 재현]
  step_06b_create_frozen_split.py
        |
        v
[7. feature / label 파일 생성]
  step_07_export_feature_label.py
        |
        v
[8B. frozen output 복사 및 검증]
  step_08b_copy_verify_frozen_output.py
```
