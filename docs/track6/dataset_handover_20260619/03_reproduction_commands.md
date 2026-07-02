# 재현 실행 순서

## 0. 전제

작업 위치:

```bash
cd /Users/bo/VisionAI
```

주의:

- 아래 명령은 현재 데이터셋 산출물을 덮어쓸 수 있다.
- 기존 산출물을 보존해야 하면 먼저 `data/track6_split/`, `data/track6/`, `data/track4_*`를 백업한다.
- 모델 번들 내부 training copy까지 맞추려면 별도 copy/sync 단계가 필요하다.

## 1. Track4 raw/cleaning/feature 후보 재생성

```bash
python3 scripts/track4/run_cleaning_pipeline.py
```

확인 파일:

```text
data/track4_primary_market_raw_collected.csv
data/track4_primary_market_cleaned_v2.csv
data/track4_primary_market_feature_candidates_v1.csv
docs/track4/dataset/primary_market_cleaned_v2_report.md
```

## 2. Track6 한글명 보정

```bash
python3 scripts/track6/improve_artist_korean_names.py
```

확인 파일:

```text
scripts/track6/artist_ko_overrides.csv
data/track6/track6_feature_candidates_name_corrected.csv
data/track6/quality/track6_artist_name_ko_applied_overrides.csv
data/track6/quality/track6_artist_name_ko_review_candidates.csv
docs/track6/dataset/artist_name_ko_improvement_report.md
```

## 3. Track6 작가 메타 보강

```bash
python3 scripts/track6/enrich_track6_artist_metadata.py
```

확인 파일:

```text
data/track6/track6_feature_candidates_name_corrected.csv
data/track6/quality/track6_artist_metadata_enrichment_summary.json
docs/track6/dataset/artist_metadata_enrichment_report.md
```

## 4. Track6 split 생성

```bash
python3 scripts/track6/create_track6_splits.py
```

확인 파일:

```text
data/track6_split/track6_train.csv
data/track6_split/track6_val_warm.csv
data/track6_split/track6_test_warm.csv
data/track6_split/track6_val_cold.csv
data/track6_split/track6_test_cold.csv
data/track6_split/track6_split_summary.json
docs/track6/dataset/split_report.md
```

핵심 확인:

```text
status = pass
val_cold/test_cold train artist_key 겹침 = 0
val_cold/test_cold train artist_name_ko 겹침 = 0
val_cold/test_cold train artist_name_ko_orig 겹침 = 0
test_warm rows = 607
test_cold rows = 3099
```

## 5. Feature/label 분리

```bash
python3 scripts/track6/export_feature_label_splits.py
```

확인 파일:

```text
data/track6_split/features/warm/track6_train_warm_features.csv
data/track6_split/features/warm/track6_val_warm_warm_features.csv
data/track6_split/features/warm/track6_test_warm_warm_features.csv
data/track6_split/features/cold/track6_train_cold_features.csv
data/track6_split/features/cold/track6_val_cold_cold_features.csv
data/track6_split/features/cold/track6_test_cold_cold_features.csv
data/track6_split/labels/track6_train_labels.csv
data/track6_split/labels/track6_val_warm_labels.csv
data/track6_split/labels/track6_test_warm_labels.csv
data/track6_split/labels/track6_val_cold_labels.csv
data/track6_split/labels/track6_test_cold_labels.csv
data/track6/manifests/track6_feature_label_manifest.json
```

핵심 확인:

```text
manifest status = pass
feature_leak_columns = []
Cold feature에서 artist_key, artist_works_log, artist_works_count_train 제거
```

## 6. 모델 번들 frozen split 고정/확인

그동안 모델 학습/평가에 사용한 고정 training copy는 아래 경로다.

```text
models/track6/price_prediction_v0.1/data/training/track6_split/
```

데이터셋 생성 당시에는 `data/track6_split/`을 만든 뒤, 모델 후보를 고정하는 시점에 이 폴더를 모델 번들 내부로 복사해 frozen split으로 고정했다. 기존 모델 검증을 재현할 때는 이 frozen copy를 기준으로 사용한다.

확인해야 할 row 수:

```text
track6_train.csv      26,914
track6_val_warm.csv      519
track6_test_warm.csv     607
track6_val_cold.csv    2,753
track6_test_cold.csv   3,099
```

주의:

- `data/track6_split/`을 현재 코드로 새로 재생성하면 row 수가 달라질 수 있다.
- 새로 재생성한 값은 새 데이터셋 후보이지, 기존 Track6 학습/평가 재현 기준이 아니다.
- 기존 결과를 검증할 때는 `models/track6/price_prediction_v0.1/data/training/track6_split/`을 사용한다.

## 7. 최종 체크 리스트

- 원본 raw 파일 4종이 존재하는가?
- `data/track4_primary_market_feature_candidates_v1.csv`가 생성됐는가?
- `data/track6/track6_feature_candidates_name_corrected.csv`가 생성됐는가?
- 한글명 override 적용 보고서가 갱신됐는가?
- split report status가 `pass`인가?
- Cold split에서 train artist/name overlap이 0인가?
- feature/label manifest status가 `pass`인가?
- Cold feature에 `artist_key`가 없는가?
- 기존 모델 재현 기준을 `models/track6/price_prediction_v0.1/data/training/track6_split/` frozen split으로 잡았는가?
