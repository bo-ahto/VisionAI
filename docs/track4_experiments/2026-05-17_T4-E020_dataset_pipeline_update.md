# T4-E020 데이터셋 파이프라인 보완 기록

- 날짜: 2026-05-17
- 상태: 완료
- 연결 항목: Track 4 데이터셋 구성/클렌징 파이프라인
- 목적: 추가 1차 시장 데이터가 들어왔을 때 같은 기준으로 raw 통합, 감사, 클렌징, split 생성을 반복할 수 있게 문서와 안내를 정리

## 1. 작업 배경

- Track 4는 Track 3과 달리 기존 수집 원본을 다시 모아 데이터셋을 구성하는 단계임
- 추가 데이터가 들어오면 매번 수동으로 판단하면 기준이 흔들릴 수 있음
- 따라서 아래 내용을 고정할 필요가 있음
- 새 원본 파일을 어디에 추가하는지
- 어떤 순서로 클렌징 스크립트를 실행하는지
- 어떤 감사 리포트를 확인하는지
- Warm / Cold split 누수 여부를 어떻게 확인하는지
- 출처/URL/이미지 같은 추적 컬럼을 모델 피처에서 어떻게 제외하는지

## 2. 반영 내용

- `docs/track4_cleaning_pipeline.md` 보완
- raw 통합부터 split 생성까지 전체 실행 순서 정리
- 추가 데이터 반영 절차 정리
- 작가 동명이인 처리 기준 정리
- train/eval 동일 작품 후보 제거 기준 정리
- `artist_works_log`는 split 이후 train 기준으로 재계산한다는 기준 명시
- Cold split의 `artist_works_log`는 0이어야 한다는 누수 점검 기준 명시
- 출처 컬럼과 URL/이미지 컬럼은 추적용이며 모델 입력에서 제외한다는 기준 명시

- `scripts/track4/README.md` 보완
- 새 CSV 추가 위치 안내
- 전체 파이프라인 실행 명령 안내
- 실행 후 확인해야 할 split 파일 목록 추가
- Cold 누수, 중복 제거, 동명이인 보존 여부 확인 항목 추가

## 3. 현재 파이프라인

- 실행 명령

```bash
python3 scripts/track4/run_cleaning_pipeline.py
```

- 실행 순서
- raw 통합 생성
- 가격 감사
- 크기 감사
- 작가명 감사
- 재료/지지체 감사
- 중복 감사
- 갤러리 메타 감사
- 출처 편향 감사
- cleaned_v2 생성
- Warm / Cold split 생성
- 컬럼별 값 정합성 재점검

## 4. 추가 데이터 반영 기준

- 새 CSV는 `data/` 아래에 저장함
- `scripts/track4/build_primary_market_raw_collected.py`의 `SOURCES`에 출처명과 경로를 추가함
- 새 출처 컬럼명이 기존과 다르면 감사 스크립트의 source별 매핑을 추가함
- 원본 row 추적을 위해 가능한 경우 아래 값을 연결함
- 작품 URL
- 이미지 URL
- 원본 row id
- 출처명
- 원본 row index

## 5. 실행 후 필수 확인

- `docs/track4_price_consistency_audit.md`
- `docs/track4_size_consistency_audit.md`
- `docs/track4_artist_consistency_audit.md`
- `docs/track4_medium_support_consistency_audit.md`
- `docs/track4_duplicate_consistency_audit.md`
- `docs/track4_primary_market_cleaned_v2_report.md`
- `docs/track4_split_report.md`
- `docs/track4_column_value_consistency_audit.md`

## 6. 누수/품질 확인 기준

- Cold 평가셋 작가가 train에 없어야 함
- Cold split의 `artist_works_log > 0` rows는 0이어야 함
- train/eval 간 동일 작품 후보는 train에서 제거되어야 함
- 동명이인 suffix와 원본 한글명 컬럼이 보존되어야 함
- 출처/URL/이미지 컬럼은 모델 피처로 쓰지 않아야 함
- `gallery_tier_validated`는 현재 모델 피처에서 제외해야 함

## 7. 현재 기준 결과

- raw 통합 rows: `54,842`
- cleaned_v2 rows: `54,842`
- 학습 후보 rows: `34,239`
- train rows: `28,920`
- validation warm rows: `68`
- validation cold rows: `1,835`
- test warm rows: `137`
- test cold rows: `3,269`
- 동명이인 분리 작가 수: `31`
- 동명이인 분리 작품 rows: `1,819`
- train/eval 동일 작품 후보 제거 rows: `10`
- validation cold의 `artist_works_log > 0` rows: `0`
- test cold의 `artist_works_log > 0` rows: `0`

## 8. 결론

- Track 4 데이터셋은 추가 원본 CSV가 들어와도 같은 파이프라인으로 다시 생성할 수 있는 구조로 정리됨
- 데이터 추가 후에는 모델 실험보다 먼저 감사 리포트와 split 누수 체크를 확인해야 함
- split 기준이 바뀌면 모델 성능 비교 기준도 바뀌므로 별도 실험 ID로 기록해야 함
