# Cleansed Dataset Tiers (2026-05-08)

**Decision binding**: ❌ X (정리 자료 만 / 운영 코드 / parquet 변경 X)

## 검수 + 코덱스 의견 반영

- 원본 column 수: 66
- 보존 (KEEP): 51 columns
- 분리 (SEPARATE / display companion): 2 columns
- 제거 (REMOVE): 13 columns

## 산출 파일

| 파일 | rows | cols | 크기 |
|---|---:|---:|---:|
| `T0_operational_28376_cleansed.csv` | 28,376 | 51 | 14.64 MB |
| `T1_artsy_only_cleansed.csv` | 7,289 | 51 | 3.84 MB |
| `T2_artsy_year_notna_cleansed.csv` | 7,231 | 51 | 3.81 MB |
| `T3_artsy_year_birth_notna_cleansed.csv` | 5,845 | 51 | 3.08 MB |
| `T4_artsy_strict_4field_cleansed.csv` | 4,628 | 51 | 2.47 MB |
| `T5_krw_only_cleansed.csv` | 868 | 51 | 0.47 MB |
| `T6_t4_anomaly_filtered_cleansed.csv` | 4,458 | 51 | 2.38 MB |
| `display_companion_T0.csv` | 28,376 | 5 | (mediums_json / supports_json 분리 보존) |
| `human_readable_T0.csv` | 28,376 | 51 | (한글 column 명 사람용 파생본) |
| `column_dictionary.csv` | 53 entries | 8 | (영문/한글/분류/정의/처리결정/사유/생성방식/계산공식 — 제거 row 미포함) |
| `removed_columns_log.csv` | 13 entries | 2 | (제거된 column 의 영문명 + 사유 record) |
