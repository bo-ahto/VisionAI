# T4-E017 클렌징 파이프라인 문서화

- 날짜: 2026-05-15
- 상태: 완료
- 연결 가설: T4-H0
- 목적: 추가 데이터 수집 후 같은 기준으로 클렌징을 반복 실행할 수 있도록 절차를 문서화하고 실행 스크립트를 고정

## 1. 배경

- Track 4는 원본 수집 데이터가 계속 추가될 수 있음
- 수작업으로 스크립트를 하나씩 실행하면 누락이나 순서 오류가 생길 수 있음
- 클렌징 기준이 문서화되어 있어야 이후 데이터가 추가되어도 같은 기준으로 비교 가능함

## 2. 작업 내용

- 전체 클렌징 실행 스크립트 추가
- `scripts/track4/run_cleaning_pipeline.py`
- 클렌징 기준 문서 추가
- `docs/track4_cleaning_pipeline.md`
- 스크립트 README 업데이트
- `scripts/track4/README.md`
- Track 4 종합 안내 문서에 클렌징 문서 링크 추가
- `docs/track4_overview_guide.md`

## 3. 실행 방식

```bash
python3 scripts/track4/run_cleaning_pipeline.py
```

## 4. 파이프라인 순서

- raw 통합 생성
- 가격 감사
- 크기 감사
- 작가명 감사
- 재료/지지체 감사
- 중복 감사
- 갤러리 메타 감사
- 출처 편향 감사
- cleaned_v2 생성
- Warm/Cold split 생성
- 컬럼별 값 정합성 재점검

## 5. 현재 판단

- 추가 데이터가 들어오면 raw 통합부터 split 생성까지 한 명령으로 재실행 가능함
- 새 출처가 추가되는 경우에는 먼저 source별 컬럼 매핑을 감사 스크립트에 추가해야 함
- 클렌징 결과 비교는 `track4_column_value_consistency_audit.md`와 `track4_primary_market_cleaned_v2_report.md`를 기준으로 확인함
- 실제 실행 검증 결과 `run_cleaning_pipeline.py`는 raw 통합부터 컬럼별 값 정합성 감사까지 완료됨
- 최종 산출물 존재 확인도 통과함

## 6. 다음 작업

- 새 출처가 추가될 때 `SOURCES`와 source별 매핑 함수를 수정
- 실행 후 row 수 변화와 주요 이슈 수 변화를 실험 기록에 남김
- split이 바뀌는 경우 모델 성능 비교 기준이 달라지므로 별도 실험 ID로 기록
