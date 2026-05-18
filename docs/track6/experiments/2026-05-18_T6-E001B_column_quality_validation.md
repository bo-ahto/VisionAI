# T6-E001B 컬럼 품질 검증

- 날짜: 2026-05-18
- 관련 가설: T6-H1
- 상태: 검토 완료
- 사용 데이터:
  - `data/track6_split/track6_train.csv`
  - `data/track6_split/track6_val_warm.csv`
  - `data/track6_split/track6_test_warm.csv`
  - `data/track6_split/track6_val_cold.csv`
  - `data/track6_split/track6_test_cold.csv`
- 사용 스크립트: `scripts/track6/validate_track6_dataset_columns.py`
- 결과 문서: `docs/track6/dataset/column_quality_report.md`
- 결과 JSON: `data/track6/quality/track6_column_quality_report.json`

## 실험 목적

- Track6 모델 실험 전에 컬럼별 데이터 이상 여부를 확인
- 필수 컬럼 결측, 숫자 범위, 파생값 계산 일치, 카테고리 unknown, Warm/Cold 누수 여부를 점검
- 모델 피처로 쓰는 값과 원본 추적용 값을 구분

## 핵심 결과

- 전체 상태: `review`
- 모델 실험을 막는 fail 이슈: `0`
- split 간 `_track6_row_id` 중복: `0`
- Warm 평가 작가 train 누락 rows: `0`
- Warm 평가셋 1작품 작가 수: `0`
- Cold train 작가명 겹침: `0`
- Cold `artist_works_count_train > 0` rows: `0`

## 검토 필요 항목

- `support_category=unknown`이 일부 남아 있음
  - train: `2,351`
  - val_warm: `24`
  - test_warm: `45`
  - val_cold: `55`
  - test_cold: `289`
- `medium_category=unknown`은 train에만 `26`건 존재
- 극단 크기 후보가 일부 존재
  - train width > 500cm: `13`
  - train height > 500cm: `23`
  - train depth > 500cm: `6`
  - train aspect_ratio > 8: `3`
- `title_raw` 결측은 train에 `1`건 있음

## 해석

- 현재 컬럼 품질은 모델 실험 진행을 막는 수준은 아님
- `support_category=unknown`은 제거하지 않고 unknown 카테고리로 유지
- unknown/극단 크기 후보는 후속 실험에서 slice 성능과 tail risk를 따로 확인
- `track4_source`, URL, image URL, source artwork ID는 감사용으로만 보존하고 모델 피처로 사용하지 않음

## 결론

- Track6 split은 컬럼 단위 품질 검증 기준을 통과함
- 상태가 `review`인 이유는 제거 대상이 아니라 후속 slice 관리 대상이 남아 있기 때문임
- 다음 단계는 T6-E002 구조-only baseline 실행
