# 가격 예측 서비스 공식 테스트 v0.1 문서 일관성 검토

- 검토일: 2026-06-12
- 대상 범위:
  - `price_prediction_official_v0_1_test_plan.md`
  - `price_prediction_official_v0_1_db_cache_schema.md`
  - `price_prediction_official_v0_1_api_spec.md`
  - `price_prediction_official_v0_1_test_ui_plan.md`
  - `price_prediction_official_v0_1_schema.sql`
  - `report_model_raw_input_operationalization_plan.md`
  - `report_model_raw_input_gap_audit.md`

## 1. 검토 결론

- 공식 서비스 테스트 버전은 `price_prediction_v0.1`로 일관됨
- `/api/v1`, `/test/v0.1`을 공식 테스트 경로로 사용하는 구조가 일관됨
- 기존 `/api/v2`, `/test/v0.2`는 비교용 로컬 프로토타입으로만 설명됨
- `v0.5` Cold 운영 아티팩트는 사용자 승인 전 적용하지 않는 제외 대상으로 일관됨
- 보고서 기준 Warm/Cold 모델은 raw 입력에 바로 붙일 수 없고, 상류 feature adapter와 DB/cache가 필요하다는 설명이 일관됨
- 사용자 화면에는 내부 실험명과 내부 식별자를 직접 노출하지 않는다는 정책이 일관됨

## 2. 수정한 표현

| 구분 | 수정 전 | 수정 후 | 이유 |
|---|---|---|---|
| 공식 버전 설명 | 외부 설명 대상을 직접 나열한 표현 | 외부 설명과 서비스 화면에서 사용하는 공식 서비스 버전 | 공유 문서에서 대상자를 직접 언급하지 않도록 정리 |
| 감사 문서 구현 순서 | 내부 모델 검증용 API처럼 보일 수 있는 표현 | 공식 테스트 v0.1 API와 테스트 화면 추가 | 공식 버전명과 API 경로 기준으로 정리 |
| DB 조회 순서 | 내부 Cold 후처리 아티팩트명을 직접 쓴 표현 | 과대예측 방어와 작가 검색 보정 후처리 적용 | 내부 아티팩트명을 기능 중심 표현으로 정리 |
| Warm API 연결 | 내부 모델 endpoint처럼 보일 수 있는 표현 | 공식 v0.1 Warm API endpoint | 내부 검증 표현 제거 |
| Cold adapter | 내부 Cold adapter 버전명을 직접 쓴 표현 | Cold 검색 보정 adapter | 내부 버전명을 기능 중심 표현으로 정리 |

## 3. 논리 검토 결과

### 3.1 버전 체계

- 공식 버전: `price_prediction_v0.1`
- 내부 추적 ID: `PP258`, `cold_prediction_v0.3` 등
- 판단:
  - 공식 버전과 내부 실험/아티팩트 버전이 분리되어 있음
  - 문서상 “v0.3을 공식 v0.3으로 운영한다”는 식의 모순 없음

### 3.2 모델 적용 범위

- Warm:
  - 보고서 기준 최고 성능 모델은 같은 작가 이력과 유사작품 통계를 강하게 활용
  - 현재 재현 패키지는 중간 컬럼을 입력으로 받으므로 raw 입력 adapter가 필요
- Cold:
  - 보고서 기준 최고 성능 모델은 작품 정보, 작가 메타, 검색 피처, 과대예측 방어를 활용
  - 현재 후처리층은 존재하지만 검색 포함 기준 예측값을 생성하는 상류 adapter가 필요
- 판단:
  - “모델은 정해졌지만 서비스 raw 입력에 바로 연결되지는 않는다”는 설명이 문서 전반에서 일관됨

### 3.3 DB/cache 필요성

- DB/cache는 모델 학습 장소가 아님
- DB/cache는 작가 매칭, 가격 이력, 검색 피처, 유사작품 통계, 예측 이벤트, 피드백을 저장하는 조회/기록 계층
- 판단:
  - DB 도입 목적이 모델 성능 과장이나 학습 대체가 아니라 운영 안정성 확보로 설명되어 있음

### 3.4 사용자 화면 정책

- 사용자 화면 노출명:
  - Warm -> `이력 기반 예측`
  - Cold -> `참고 예측`
- 내부명:
  - 운영자/검증 문서에서만 관리
- 판단:
  - 사용자에게 `Warm`, `Cold`, `artist_key`, 내부 실험 번호를 직접 설명하지 않는 방향이 일관됨

## 4. 수행한 검증

```text
python3 scripts/track6/audit_report_model_raw_input_gap.py
python3 scripts/track6/build_price_prediction_official_v0_1_db.py
python3 -m py_compile scripts/track6/audit_report_model_raw_input_gap.py scripts/track6/build_price_prediction_official_v0_1_db.py
sqlite3 data/track6/service_v0_1/price_prediction_v0_1.sqlite "PRAGMA integrity_check;"
sqlite3 data/track6/service_v0_1/price_prediction_v0_1.sqlite "PRAGMA foreign_key_check;"
```

검증 결과:

- Python 문법 오류 없음
- SQLite `integrity_check` 결과: `ok`
- SQLite 외래키 오류 없음
- 혼동 표현 검색 결과 추가 수정 필요 항목 없음

## 5. 다음 작업 판단

- 공식 v0.1 문서 기준은 현재 진행 가능한 상태
- 다음 작업은 DB/cache를 사용하는 `/api/v1` adapter skeleton 구현
- 그 다음 작업은 Warm/Cold 중간 피처 생성 adapter와 fixed-test parity 검증
