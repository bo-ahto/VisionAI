# Track 4 scripts

- Track 4 전용 실험 스크립트를 두는 폴더
- Track 3 스크립트는 수정하지 않고 필요한 경우 참고만 함
- 결과 파일은 `data/track4_*.json` 또는 `data/track4_*.csv`로 저장함

## 클렌징 파이프라인 실행

- 추가 1차 시장 데이터를 반영한 뒤 전체 클렌징을 재실행하려면 아래 명령을 사용함

```bash
python3 scripts/track4/run_cleaning_pipeline.py
```

- 새 데이터 추가 위치
- `scripts/track4/build_primary_market_raw_collected.py`의 `SOURCES`에 새 CSV 출처명과 경로를 추가함
- 새 출처의 컬럼명이 기존과 다르면 가격/크기/작가/재료 감사 스크립트의 source별 매핑도 함께 추가함
- 원본 row 추적을 위해 가능한 경우 작품 URL, 이미지 URL, 원본 row id를 trace 컬럼에 연결함

- 실행 순서
- raw 통합 생성
- 가격 감사
- 크기 감사
- 작가명 감사
- 재료/지지체 감사
- 중복 감사
- 갤러리 메타 감사
- 출처 편향 감사
- `cleaned_v2` 생성
- Warm/Cold split 생성
- 컬럼별 값 정합성 재점검

- 실행 후 필수 확인
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_warm.csv`
- `data/track4_split/track4_val_cold.csv`
- `data/track4_split/track4_test_warm.csv`
- `data/track4_split/track4_test_cold.csv`
- Cold split의 `artist_works_log > 0` rows가 0인지 확인함
- train/eval 간 동일 작품 후보가 제거되었는지 확인함
- 동명이인 suffix(`_A`, `_B` 등)와 `artist_name_ko_orig`가 보존되는지 확인함
- 출처/URL/이미지 컬럼은 추적용이며 모델 입력 피처로 사용하지 않음

- 상세 기준 문서
- `docs/track4_cleaning_pipeline.md`
