# Stage 1 Cleaning Definition

이 문서는 `csv_collected_20260622` 패키지의 1차 정리 기준을 고정하기 위한 문서다.

## 목적

1차 정리는 기존 실험 원본 데이터와 추가 수집 데이터를 하나로 합치고, 모델 학습 전 공통으로 적용해야 하는 기본 정리만 수행하는 단계다.

## 입력

- `01_source_raw/ahto_viewer_exports/`
- `01_source_raw/source_platform_latest/`
- `01_source_raw/artue_exports/`
- `01_source_raw/legacy_experiment_sources/`

## 수행하는 일

- 원천별 CSV를 하나의 표준 컬럼 체계로 맞춘다.
- 같은 작품으로 판단되는 중복 행을 제거한다.
- 가격 숫자가 전혀 없는 작품을 제거한다.
- `1원`, `999,999,999원`처럼 placeholder 가능성이 높은 가격을 제거한다.
- 입체 작품을 제거한다.
- 명백한 크기 오류 후보를 제거한다.
- 이상치 후보는 삭제하지 않고 감사 파일에 별도로 남긴다.

## 수행하지 않는 일

- 외화 가격을 원화로 환율 변환하지 않는다.
- 가격을 새로 산정하거나 보정하지 않는다.
- 모델 학습 피처를 생성하지 않는다.
- 최종 `artist_key`를 확정하지 않는다.
- Warm/Cold 학습 split을 만들지 않는다.

## 가격 처리 원칙

- 1차 정리 최종 산출물에는 `price_krw` 컬럼을 유지한다.
- 다만 Artsy/Saatchi 수집 과정에서 고정 환율로 계산된 `price_krw`는 원천 가격으로 오해할 수 있으므로 비워둔다.
- Artue처럼 원천 CSV에 실제 KRW 가격 컬럼이 있는 경우에는 `price_krw`에 그대로 보존한다.
- `price_raw`, `price_currency`, `price_amount`, `price_usd`, `price_eur`처럼 원천 가격 해석에 필요한 값은 보존한다.
- 원화 가격이 없더라도 `price_raw`에 `CHF2,200`처럼 외화 숫자 가격이 있으면 가격 정보가 있는 행으로 본다.
- `Sold`, `On hold`, `Price on request`, 빈 값, `0.0`은 가격 숫자가 없는 행으로 본다.
- 환율 변환은 2차 단계에서 별도 정책으로 일괄 처리한다.

## 주요 산출물

- `03_outputs/standardized_artworks_merged_deduped.csv`
  - 1차 정리가 끝난 최종 사용 후보 CSV다.
- `03_outputs/standardized_artworks_removed_by_filter.csv`
  - 1차 정리에서 제거된 행과 제거 사유다.
- `03_outputs/standardized_artworks_outlier_audit.csv`
  - 제거하지 않고 검토용으로 표시한 이상치 후보다.
- `03_outputs/standardization_merge_summary.json`
  - 입력 행 수, 제거 행 수, 최종 행 수를 기록한 요약 파일이다.

## 레거시 기준 1차 정리본

기존 실험 원본만 같은 1차 정리 규칙으로 처리한 별도 산출물도 함께 유지한다.

생성 명령:

```bash
python3 02_scripts/standardize_merge_collected_artworks.py \
  --source-scope legacy \
  --output-dir 03_outputs_legacy_stage1
```

주요 파일:

- `03_outputs_legacy_stage1/standardized_artworks_merged_deduped.csv`
- `03_outputs_legacy_stage1/standardization_merge_summary.json`
- `03_outputs_legacy_stage1/standardized_artworks_removed_by_filter.csv`
- `03_outputs_legacy_stage1/standardized_artworks_outlier_audit.csv`

## 현재 결과

- 표준화 전 행 수: 164,105
- 중복 제거 후 가격 필터 전 행 수: 68,769
- 최종 1차 정리 행 수: 43,233
- 최종 1차 정리 산출물 컬럼 수: 61
- `price_krw`는 원천 KRW 가격이 확인되는 행에만 보존함

## 레거시 기준 현재 결과

- 표준화 전 행 수: 54,842
- 중복 제거 후 가격 필터 전 행 수: 54,842
- 최종 1차 정리 행 수: 34,771
- 최종 구성: Artsy 10,086 / Saatchi 21,696 / Artue 2,712 / Gallery primary 277
