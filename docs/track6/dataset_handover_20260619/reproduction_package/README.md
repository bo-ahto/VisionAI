# Track6 학습/테스트 데이터셋 재현 패키지

- 생성일: 2026-06-19
- 범위: 모델 학습/검증/테스트 CSV 데이터셋 생성까지
- 제외: 운영 DB, API adapter, service cache

## 기준 데이터셋

기존 Track6 모델 학습/평가에 사용한 기준은 모델 번들 내부 frozen split이다.

```text
models/track6/price_prediction_v0.1/data/training/track6_split/
```

이 패키지에서는 같은 내용을 아래 폴더에 복사해 둔다.

```text
frozen_training_dataset/track6_split/
```

`data/track6_split/`은 생성 스크립트의 작업용 산출물이므로 현재 코드로 다시 실행하면 달라질 수 있다. 기존 성능표와 실험 결과를 검증할 때는 frozen split을 사용한다.

## 폴더 구조

| 폴더 | 내용 |
|---|---|
| `source_files/` | 1차 원본 CSV 4종 |
| `pipeline_code/track4/` | Track4 raw 통합/감사/정제 코드 |
| `pipeline_code/track6/` | Track6 한글명 보정/split/feature-label 분리 코드 |
| `current_outputs/track4/` | Track4 중간/후보 산출물 보관본 |
| `current_outputs/track6/` | Track6 보정 후보 파일 보관본 |
| `current_outputs/track6_split/full_track6_split/` | 기존 모델 학습/검증/테스트에 사용한 frozen split, features, labels |
| `frozen_training_dataset/track6_split/` | 모델 번들에서 복사한 원본 frozen training split |
| `current_outputs/manifests/` | feature/label manifest |
| `current_outputs/quality/` | 한글명/작가 메타 품질 요약 |
| `reports/` | 생성/검증 보고서 복사본 |
| `verification/` | 해시 검증, row 수 요약, 재현 검증 리포트 |

## 재현 실행 순서

```bash
python3 scripts/track4/run_cleaning_pipeline.py
python3 scripts/track6/improve_artist_korean_names.py
python3 scripts/track6/enrich_track6_artist_metadata.py
python3 scripts/track6/create_track6_splits.py
python3 scripts/track6/export_feature_label_splits.py
```

## 확인 결과

- 검증 리포트: `verification/verification_report.md`
- checksum manifest: `verification/checksum_manifest.csv`
- row count summary: `verification/row_count_summary.csv`
- 모델 번들 frozen split과 패키지 복사본 SHA256 전체 일치: `True`
- `data/track6_split/`도 frozen split과 byte 단위 일치하도록 복원: `True`
- Track6 split status: `pass`
- feature/label manifest status: `pass`
- feature leak columns: 없음
