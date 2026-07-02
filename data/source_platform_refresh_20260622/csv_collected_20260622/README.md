# CSV collected on 2026-06-22

이 폴더는 2026-06-22에 수집하거나 생성한 작품/작가 CSV를 재현 가능하게 관리하기 위한 1차 정리 패키지입니다.
원천 CSV, 실행 스크립트, 생성 산출물을 분리해 보관합니다.

## Stage definition

이 패키지의 산출물은 `1차 정리본`입니다.

1차 정리 범위:

- 기존 실험 원본 데이터와 추가 수집 데이터를 합친다.
- 플랫폼별 컬럼명을 공통 컬럼명으로 표준화한다.
- 같은 작품으로 판단되는 중복 행을 제거한다.
- 가격 숫자가 전혀 없는 작품을 제거한다.
- `1원`, `999,999,999원`처럼 placeholder 가능성이 높은 가격을 제거한다.
- 입체 작품과 명백한 크기 오류 후보를 제거한다.
- 이상치 후보는 제거하지 않고 감사 파일에 별도로 남긴다.
- `price_krw` 컬럼은 유지하되, 고정 환율로 변환된 값은 비우고 원천 KRW 가격만 보존한다.

1차 정리에서 하지 않는 일:

- 외화 가격을 원화로 환율 변환하지 않는다.
- 가격을 새로 산정하거나 보정하지 않는다.
- 모델 학습 피처를 생성하지 않는다.
- 작가 키를 최종 확정하지 않는다.

## Folder structure

- `01_source_raw/`: 원천 CSV 보관 폴더
- `02_scripts/`: 표준화/비교 실행 스크립트
- `03_outputs/`: 표준화 결과, 제거 행, 이상치 감사, 기존 원천 비교 결과
- `03_outputs_legacy_stage1/`: 기존 실험 원본만 대상으로 만든 1차 정리 결과
- `04_docs/`: 컬럼 의미 감사 등 보조 문서
- `README.md`: 폴더 구조와 실행 방법 설명

## AHTO viewer site exports

아래 파일은 내부 수집 페이지에서 내려받은 데이터입니다.

- Source: https://artsy.ahto.city/
  - `01_source_raw/ahto_viewer_exports/ahto_export_artsy_artists.csv`
  - `01_source_raw/ahto_viewer_exports/ahto_export_artsy_artworks.csv`

- Source: https://saatchi.ahto.city/
  - `01_source_raw/ahto_viewer_exports/ahto_export_saatchi_artists.csv`
  - `01_source_raw/ahto_viewer_exports/ahto_export_saatchi_artworks.csv`

## Source platform refresh

아래 파일은 Artsy/Saatchi 원천 플랫폼에서 새로 수집한 최신 데이터입니다.

- `01_source_raw/source_platform_latest/source_platform_artsy_kr_artists_full.csv`
- `01_source_raw/source_platform_latest/source_platform_artsy_kr_artworks.csv`
- `01_source_raw/source_platform_latest/source_platform_saatchi_kr_artworks_split_13102.csv`

`source_platform_saatchi_kr_artworks_split_13102.csv`는 size 구간별로 나눠 수집해 13,102건까지 확장한 Saatchi 최종 수집본입니다.

## Artue exports

아래 파일은 Artue 원천 수집본입니다.

- `01_source_raw/artue_exports/artue_artists.csv`
- `01_source_raw/artue_exports/artue_artworks.csv`
- `01_source_raw/artue_exports/artue_careers.csv`

## Legacy experiment source files

아래 파일은 기존 실험 데이터셋 생성 패키지의 `source_files` 원본을 복사한 것이다.
새 수집본과 함께 표준화한 뒤, 중복 제거에서 최신 수집본을 우선 남기고 새 수집본에 없는 과거 원본만 보존한다.

- `01_source_raw/legacy_experiment_sources/legacy_artsy_kr_artworks.csv`
- `01_source_raw/legacy_experiment_sources/legacy_saatchi_cleaned.csv`
- `01_source_raw/legacy_experiment_sources/legacy_artue_price_included.csv`
- `01_source_raw/legacy_experiment_sources/legacy_gallery_primary_260504.csv`

## Standardized merged output

아래 스크립트는 `01_source_raw/`의 작품 CSV를 표준 컬럼으로 맞춘 뒤, 작품 단위 중복과 1차 제거 대상을 정리해 하나의 CSV로 만든다.

```bash
python3 02_scripts/standardize_merge_collected_artworks.py
```

기존 실험 원본만 1차 정리할 때:

```bash
python3 02_scripts/standardize_merge_collected_artworks.py \
  --source-scope legacy \
  --output-dir 03_outputs_legacy_stage1
```

출력 파일:

- `03_outputs/standardized_artworks_merged_deduped.csv`
- `03_outputs/standardization_merge_summary.json`
- `03_outputs/standardized_artworks_removed_by_filter.csv`
- `03_outputs/standardized_artworks_outlier_audit.csv`
- `03_outputs/standardized_artworks_outlier_audit_summary.json`
- `03_outputs/standardized_artworks_new_added_since_05월.csv`
- `03_outputs/standardized_artworks_new_added_since_05월_summary.json`

레거시 기준 1차 정리 출력 파일:

- `03_outputs_legacy_stage1/standardized_artworks_merged_deduped.csv`
- `03_outputs_legacy_stage1/standardization_merge_summary.json`
- `03_outputs_legacy_stage1/standardized_artworks_removed_by_filter.csv`
- `03_outputs_legacy_stage1/standardized_artworks_outlier_audit.csv`
- `03_outputs_legacy_stage1/standardized_artworks_outlier_audit_summary.json`

처리 기준:

- 최종 CSV는 작품 1건을 1행으로 둔다.
- Artsy, Saatchi, Artue 작품 CSV를 공통 컬럼으로 표준화한다.
- 작가 CSV는 작가 메타 보강용으로만 사용한다.
- 중복 제거는 `source_family + source_artwork_id`를 우선 사용한다.
- 같은 작품이 여러 수집본에 있으면 최신/상세 수집본을 우선 남긴다.
- 양수 가격 숫자가 없는 행은 최종 CSV에서 제외한다.
- 원화 가격이 없어도 외화 가격 원문에 숫자가 있으면 가격 정보가 있는 행으로 보고 유지한다.
- `price_krw` 컬럼은 유지한다. 단, Artsy/Saatchi 수집 과정에서 고정 환율로 계산된 값은 비우고 Artue처럼 원천 KRW 가격이 있는 값만 보존한다.
- 원화 환산이 필요하면 2차 단계에서 별도 환율 정책으로 일괄 처리한다.
- `1원`, `999,999,999원`은 placeholder 가능성이 높아 최종 CSV에서 제외한다.
- 입체 작품과 명백한 크기 오류 후보는 최종 CSV에서 제외한다.
- 제거된 행은 `standardized_artworks_removed_by_filter.csv`에 사유와 함께 남긴다.
- 이상치 후보는 자동 삭제하지 않고 `standardized_artworks_outlier_audit.csv`에 별도로 남긴다.
- 가격을 새로 계산하거나 모델 피처를 새로 만들지는 않는다.
- 외화 가격을 원화로 환율 변환하지 않는다.

현재 생성 결과:

- 표준화 전 행 수: 164,105
- 중복 제거 후 가격 필터 전 행 수: 68,769
- 제거된 중복 행 수: 95,336
- 가격 없음 또는 양수 가격 숫자 없음으로 제거된 행 수: 23,567
- placeholder 가격으로 제거된 행 수: 11
  - `1원`: 3
  - `999,999,999원`: 8
- 입체 작품으로 제거된 행 수: 1,937
- 명백한 크기 오류로 제거된 행 수: 21
- 최종 행 수: 43,233
- 최종 구성: Artsy 10,830 / Saatchi 28,289 / Artue 3,837 / Gallery primary 277
- legacy에서 최종 보존된 행 수: 315
  - `legacy_gallery_primary`: 277
  - `legacy_artue`: 38
- 이상치 후보 행 수: 199

05월 레거시 기준 대비 06/22 신규 추가분:

- 기준 파일: `03_outputs_legacy_stage1/standardized_artworks_merged_deduped_05월.csv`
- 비교 파일: `03_outputs/standardized_artworks_merged_deduped_0622.csv`
- 신규 추가분 파일: `03_outputs/standardized_artworks_new_added_since_05월.csv`
- 신규 추가분 행 수: 9,247
- 신규 추가분 구성: Saatchi 6,593 / Artsy 1,461 / Artue 1,193

레거시 기준 1차 정리 결과:

- 표준화 전 행 수: 54,842
- 중복 제거 후 가격 필터 전 행 수: 54,842
- 제거된 중복 행 수: 0
- 가격 없음 또는 양수 가격 숫자 없음으로 제거된 행 수: 18,926
- placeholder 가격으로 제거된 행 수: 1
- 입체 작품으로 제거된 행 수: 1,131
- 명백한 크기 오류로 제거된 행 수: 13
- 최종 행 수: 34,771
- 최종 구성: Artsy 10,086 / Saatchi 21,696 / Artue 2,712 / Gallery primary 277
