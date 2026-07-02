# 원본 소스 -> 코드 -> 최종 데이터셋 계보

## 1. 전체 흐름

```text
[원본 CSV 4종]
  data/saatchi_cleaned.csv
  data/artsy_kr_artworks.csv
  data/artue_테스트_가격포함.csv
  data/1차 시장 데이터 - 전달본_260504.csv
        |
        v
[Track4 raw 통합/감사/정제]
  scripts/track4/run_cleaning_pipeline.py
        |
        v
[Track4 모델 후보 데이터]
  data/track4_primary_market_feature_candidates_v1.csv
        |
        v
[Track6 한글명 보정 + 작가 메타 보강]
  scripts/track6/improve_artist_korean_names.py
  scripts/track6/enrich_track6_artist_metadata.py
        |
        v
[Track6 보정 후보 데이터]
  data/track6/track6_feature_candidates_name_corrected.csv
        |
        v
[Track6 train/validation/test split]
  scripts/track6/create_track6_splits.py
        |
        v
[Track6 full split]
  data/track6_split/track6_train.csv
  data/track6_split/track6_val_warm.csv
  data/track6_split/track6_test_warm.csv
  data/track6_split/track6_val_cold.csv
  data/track6_split/track6_test_cold.csv
        |
        v
[Feature/label 분리]
  scripts/track6/export_feature_label_splits.py
        |
        v
[최종 실험 기준 데이터셋]
  data/track6_split/features/warm/*.csv
  data/track6_split/features/cold/*.csv
  data/track6_split/labels/*.csv
        |
        v
[모델 번들 frozen split 고정]
  models/track6/price_prediction_v0.1/data/training/track6_split/
        |
        v
[Track6 모델 학습/평가 기준]
  이후 성능표, fixed test, 재현 검증은 frozen split 기준
```

## 2. 원본 소스

| 출처명 | 원본 파일 | 설명 |
|---|---|---|
| Saatchi | `data/saatchi_cleaned.csv` | Saatchi 수집/정리 데이터 |
| Artsy | `data/artsy_kr_artworks.csv` | Artsy 한국 작가 작품 데이터 |
| Artue | `data/artue_테스트_가격포함.csv` | Artue 가격 포함 데이터 |
| Gallery primary | `data/1차 시장 데이터 - 전달본_260504.csv` | 갤러리 1차 시장 전달본 |

근거 문서: `docs/track4/dataset/cleaning_pipeline.md`

## 3. Track4 정제 파이프라인

대표 실행 코드:

```bash
python3 scripts/track4/run_cleaning_pipeline.py
```

순서:

| 순서 | 단계 | 코드 | 주요 산출물 |
|---:|---|---|---|
| 1 | raw 통합 | `scripts/track4/build_primary_market_raw_collected.py` | `data/track4_primary_market_raw_collected.csv` |
| 2 | 가격 감사 | `scripts/track4/audit_price_consistency.py` | `data/track4_price_consistency_audit.csv` |
| 3 | 크기 감사 | `scripts/track4/audit_size_consistency.py` | `data/track4_size_consistency_audit.csv` |
| 4 | 작가 감사 | `scripts/track4/audit_artist_consistency.py` | `data/track4_artist_consistency_audit.csv` |
| 5 | 재료/지지체 감사 | `scripts/track4/audit_medium_support_consistency.py` | `data/track4_medium_support_consistency_audit.csv` |
| 6 | 중복 감사 | `scripts/track4/audit_duplicate_consistency.py` | `data/track4_duplicate_consistency_audit.csv` |
| 7 | 갤러리 메타 감사 | `scripts/track4/audit_gallery_metadata.py` | `data/track4_gallery_metadata_audit.csv` |
| 8 | 정제/피처 후보 생성 | `scripts/track4/build_primary_market_cleaned_v2.py` | `data/track4_primary_market_cleaned_v2.csv`, `data/track4_primary_market_feature_candidates_v1.csv` |

Track4 feature 후보 생성 결과:

| 항목 | 값 |
|---|---|
| 전체 rows | 54,842 |
| 학습 후보 rows | 34,219 |
| feature 후보 파일 | `data/track4_primary_market_feature_candidates_v1.csv` |
| 보고서 | `docs/track4/dataset/primary_market_cleaned_v2_report.md` |

## 4. Track6 한글명 보정

실행 코드:

```bash
python3 scripts/track6/improve_artist_korean_names.py
```

입출력:

| 구분 | 경로 |
|---|---|
| 입력 | `data/track4_primary_market_feature_candidates_v1.csv` |
| 수동 override | `scripts/track6/artist_ko_overrides.csv` |
| 출력 | `data/track6/track6_feature_candidates_name_corrected.csv` |
| 적용 내역 | `data/track6/quality/track6_artist_name_ko_applied_overrides.csv` |
| 잔여 검토 후보 | `data/track6/quality/track6_artist_name_ko_review_candidates.csv` |
| 보고서 | `docs/track6/dataset/artist_name_ko_improvement_report.md` |

확인된 결과:

| 항목 | 값 |
|---|---:|
| 적용 작가 key 수 | 144 |
| 적용 rows | 4,454 |
| 잔여 검토 후보 작가 key 수 | 506 |
| 잔여 검토 후보 rows | 3,109 |

처리 원칙:

- 자동 음역으로 대량 보정하지 않고, 검토된 override만 적용한다.
- 보정 전 이름은 `artist_name_ko_orig`에 보존한다.
- split은 보정된 `artist_name_ko` 기준으로 다시 생성한다.

## 5. Track6 작가 메타 보강

실행 코드:

```bash
python3 scripts/track6/enrich_track6_artist_metadata.py
```

입출력:

| 구분 | 경로 |
|---|---|
| 입력 정제 데이터 | `data/track6/track6_feature_candidates_name_corrected.csv` |
| 원본 raw 데이터 | `data/track4_primary_market_raw_collected.csv` |
| 출력 | `data/track6/track6_feature_candidates_name_corrected.csv` |
| 요약 | `data/track6/quality/track6_artist_metadata_enrichment_summary.json` |
| 보고서 | `docs/track6/dataset/artist_metadata_enrichment_report.md` |

메타 보강은 `track4_source + track4_source_row_index`로 row 단위 매칭한다. 기본 feature export에서는 `artist_meta_` prefix 컬럼을 제외하고, 별도 작가 메타 실험에서만 명시적으로 사용한다.

## 6. Track6 split 생성

실행 코드:

```bash
python3 scripts/track6/create_track6_splits.py
```

입출력:

| 구분 | 경로 |
|---|---|
| 입력 | `data/track6/track6_feature_candidates_name_corrected.csv` |
| 출력 폴더 | `data/track6_split/` |
| split 요약 | `data/track6_split/track6_split_summary.json` |
| membership | `data/track6_split/track6_split_membership.csv` |
| 보고서 | `docs/track6/dataset/split_report.md` |

고정 정책:

| 항목 | 값 |
|---|---:|
| random seed | 20260518 |
| Stable Warm train 최소 이력 | 5 |
| Warm holdout per artist | 2~3 |
| Cold validation 최소 rows | 2,500 |
| Cold test 최소 rows | 3,000 |

split 결과:

| split | rows | 작가 수 | 파일 |
|---|---:|---:|---|
| train | 26,914 | 1,773 | `data/track6_split/track6_train.csv` |
| val_warm | 519 | 178 | `data/track6_split/track6_val_warm.csv` |
| test_warm | 607 | 207 | `data/track6_split/track6_test_warm.csv` |
| val_cold | 2,753 | 172 | `data/track6_split/track6_val_cold.csv` |
| test_cold | 3,099 | 200 | `data/track6_split/track6_test_cold.csv` |

핵심 검증:

- Warm 평가 작가는 모두 train에 존재한다.
- Warm 평가 작가는 train에 최소 5작품 이상 남는다.
- Cold validation/test는 train과 `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 겹침이 0이다.
- train/eval 동일 작품 후보 겹침은 0이다.

## 7. Feature/label 분리

실행 코드:

```bash
python3 scripts/track6/export_feature_label_splits.py
```

산출물:

| 구분 | 경로 |
|---|---|
| Warm features | `data/track6_split/features/warm/` |
| Cold features | `data/track6_split/features/cold/` |
| Labels | `data/track6_split/labels/` |
| Manifest | `data/track6/manifests/track6_feature_label_manifest.json` |
| 보고서 | `docs/track6/dataset/feature_label_pipeline_report.md` |

제거 정책:

- feature 파일에서 `price_krw`, `ln_price_krw` 등 target/가격 컬럼 제거
- URL/source 추적 컬럼 제거
- `artist_name_ko`, `artist_name_ko_orig`, `is_homonym`, `artist_entity_suffix` 제거
- Cold feature에서는 추가로 `artist_key`, `artist_works_log`, `artist_works_count_train` 제거

Cold에서 제거하는 이유:

- Cold는 같은 작가 가격 이력을 직접 사용할 수 없는 상황을 평가한다.
- 따라서 `artist_key`나 train 내 같은 작가 작품 수가 feature에 남으면 실험 정의와 충돌한다.

## 8. 모델 번들 frozen split 고정

Track6 split과 feature/label 파일은 먼저 작업용 경로인 `data/track6_split/`에 생성된다. 모델 후보를 고정할 때 이 작업용 split을 모델 번들 내부로 복사해 **frozen split**으로 고정했다.

frozen 기준 경로:

```text
models/track6/price_prediction_v0.1/data/training/track6_split/
```

이 단계가 필요한 이유:

- `data/track6_split/`은 생성 스크립트가 쓰는 작업용 산출물이라, 현재 코드나 입력 파일 상태로 다시 실행하면 row 수와 컬럼 구성이 달라질 수 있다.
- 모델 성능표와 fixed test 결과는 당시 고정된 데이터셋 기준이어야 재현 가능하다.
- 따라서 기존 Track6 모델 학습/평가를 검증할 때는 `data/track6_split/`을 새로 생성한 결과가 아니라 모델 번들 안의 frozen split을 기준으로 사용한다.

frozen split row 수:

| split | rows | columns | 파일 |
|---|---:|---:|---|
| train | 26,914 | 50 | `models/track6/price_prediction_v0.1/data/training/track6_split/track6_train.csv` |
| val_warm | 519 | 50 | `models/track6/price_prediction_v0.1/data/training/track6_split/track6_val_warm.csv` |
| test_warm | 607 | 50 | `models/track6/price_prediction_v0.1/data/training/track6_split/track6_test_warm.csv` |
| val_cold | 2,753 | 50 | `models/track6/price_prediction_v0.1/data/training/track6_split/track6_val_cold.csv` |
| test_cold | 3,099 | 50 | `models/track6/price_prediction_v0.1/data/training/track6_split/track6_test_cold.csv` |

관련 근거:

- `models/track6/price_prediction_v0.1/README.md`의 재현 기준에 `data/training/track6_split/` 스냅샷 사용이 명시되어 있다.
- `docs/track6/dataset_handover_20260619/reproduction_package/verification/verification_report.md`에서 frozen split, 패키지 복사본, 현재 `data/track6_split/`의 SHA256 일치를 확인했다.

## 9. 최종 학습/검증/테스트 데이터셋 위치

| 목적 | 경로 |
|---|---|
| 작업용 Track6 full split | `data/track6_split/track6_*.csv` |
| 작업용 Track6 모델 feature | `data/track6_split/features/{warm,cold}/*.csv` |
| 작업용 Track6 평가 label | `data/track6_split/labels/*.csv` |
| 기존 모델 학습/평가 기준 frozen split | `models/track6/price_prediction_v0.1/data/training/track6_split/` |
| 공유 패키지 내 frozen copy | `docs/track6/dataset_handover_20260619/reproduction_package/frozen_training_dataset/track6_split/` |

주의: 그동안 모델 학습/평가에 사용한 고정 기준은 `models/track6/price_prediction_v0.1/data/training/track6_split/` 스냅샷이다. 현재 `data/track6_split/`도 이 스냅샷에 맞춰 복원했다.

## 10. 범위 제외

이 문서는 학습/검증/테스트 데이터셋 생성까지만 다룬다. 운영/API 연결 단계는 제외한다.
