# 가격 예측 서비스 공식 테스트 v0.1 기획서

- 작성일: 2026-06-12
- 공식 버전: `price_prediction_v0.1`
- 문서 목적: 보고서에 정리된 Warm/Cold 최고 성능 모델을 실제 서비스 테스트용 `0.1` 버전으로 운영화하기 위한 기준, 범위, API, DB, 화면, 검증 절차 정의
- 기준 보고서: `docs/track6/experiments/partner_warm_cold_best_model_report.md`
- 상세 문서:
  - DB/cache: `docs/track6/experiments/price_prediction_official_v0_1_db_cache_schema.md`
  - DB 생성 결과: `docs/track6/experiments/price_prediction_official_v0_1_db_build_summary.md`
  - API: `docs/track6/experiments/price_prediction_official_v0_1_api_spec.md`
  - API 구현 요약: `docs/track6/experiments/price_prediction_official_v0_1_api_implementation_summary.md`
  - 보고서 모델 adapter 연결 상태: `docs/track6/experiments/price_prediction_official_v0_1_report_adapter_connection_status.md`
  - 화면: `docs/track6/experiments/price_prediction_official_v0_1_test_ui_plan.md`
  - SQL schema 초안: `docs/track6/experiments/price_prediction_official_v0_1_schema.sql`
  - DB 생성 스크립트: `scripts/track6/build_price_prediction_official_v0_1_db.py`
  - 문서 일관성 검토: `docs/track6/experiments/price_prediction_official_v0_1_consistency_review.md`
- 중요 기준:
  - 이번 문서에서 말하는 `v0.1`은 공식 서비스 테스트 시작 버전
  - 이전 실험/로컬 구현의 버전 표기는 내부 개발 이력 또는 모델 아티팩트 버전
  - 외부 설명과 서비스 화면에서 사용하는 공식 서비스 버전은 `0.1`
  - 이번 버전의 목표는 보고서 기준 Warm/Cold 모델을 raw 입력 기반으로 서비스에서 테스트할 수 있게 만드는 것

## 1. 결론

- 공식 테스트 v0.1의 목표는 단순 실험 재현이 아님
- 사용자가 입력한 작가명, 작품 크기, 제작연도, 매체, 지지체를 기반으로 가격 예측이 실제로 계산되는 구조를 만든다
- 보고서 기준 Warm 모델과 Cold 모델을 서비스 적용 가능한 형태로 승격한다
- Warm은 같은 작가의 가격 이력과 유사작품 통계를 강하게 활용하는 이력 기반 예측 경로
- Cold는 같은 작가 이력이 부족한 경우 작품 정보, 작가 메타, 검색 피처를 활용하는 참고 예측 경로
- 공식 테스트 v0.1에서는 내부 실험 번호를 사용자 화면에 노출하지 않는다
- 공식 테스트 v0.1에서는 예측 결과뿐 아니라 계산 근거, 사용 피처, 유사작품/유사작가 기준, 신뢰도, 보완 입력 안내를 함께 제공한다
- 운영 적용을 위해 DB 또는 캐시 저장소가 필요하다
- DB는 작가 매칭, 검색 피처, 유사작품 통계, 예측 이벤트, 실제 판매가 피드백을 저장한다

## 2. 버전 정의

| 구분 | 표기 | 의미 | 외부 노출 |
|---|---|---|---|
| 공식 서비스 테스트 버전 | `price_prediction_v0.1` | 이번에 새로 시작하는 본격 서비스 테스트 버전 | 노출 가능 |
| 기존 로컬 Warm 구현 | `legacy warm operational artifact` | raw 입력 테스트에 사용했던 기존 Warm 실행 가능 아티팩트 | 외부 노출 금지 |
| 보고서 Warm 모델 | `기준가격 기반 미세 보정 모델` | 공식 v0.1에 적용하려는 Warm 목표 모델 | 기능명으로 노출 |
| 보고서 Cold 모델 | `검색 피처 포함 참고 예측 모델` | 공식 v0.1에 적용하려는 Cold 목표 모델 | 기능명으로 노출 |
| 내부 실험/아티팩트 번호 | `PP258`, `cold_prediction_v0.3` 등 | 추적과 재현을 위한 내부 ID | 운영자/문서 하단에서만 관리 |

## 3. 공식 v0.1 적용 범위

### 3.1 포함 범위

- 작가명 기반 작가 후보 조회
- 동명이인 후보 확인
- 작가 매칭 신뢰도 계산
- Warm/Cold 라우팅
- Warm 가격 예측
- Cold 참고 가격 예측
- 유사작품/유사작가 근거 표시
- 가격 범위와 신뢰도 표시
- 계산 과정 상세 표시
- 부족 정보 안내
- 실제 판매가 피드백 저장
- 예측 이벤트와 피처 스냅샷 저장
- fixed-test 재현성 검증
- 동일 입력 반복 결과 검증

### 3.2 제외 범위

- 자동 재학습
- 자동 모델 승격
- 실시간 검색 API 상시 호출
- 검수 없는 실제 판매가 자동 학습 반영
- 이미지 모델 직접 반영
- 외부 사용자 대상 정식 배포

## 4. 공식 v0.1 전체 흐름

```text
[사용자 입력]
  - 한글/영문 작가명
  - 작품명
  - 제작연도
  - 가로/세로/깊이
  - 작품 유형
  - 매체
  - 지지체
        |
        v
[작가 확인]
  - 이름 정규화
  - alias 조회
  - 동명이인 후보 확인
  - 작가 매칭 신뢰도 계산
        |
        v
[입력 품질 확인]
  - 필수 입력 충족 여부
  - 권장 입력 누락 여부
  - Cold 최소 입력 충족 여부
        |
        v
[Warm/Cold 라우팅]
  - 작가 매칭 신뢰도
  - 같은 작가 사용 가능 가격 이력 수
  - 유사작품 통계 표본 수
        |
        +--------------------------------+
        |                                |
        v                                v
[이력 기반 예측 경로]              [참고 예측 경로]
  - Warm 모델                       - Cold 모델
  - 기준가격 생성                   - 작품/작가/검색 피처 생성
  - 방향 확률 계산                  - LightGBM Quantile 예측
  - Huber 잔차 계산                 - 과대예측 방어
  - 위험도 기반 미세 보정           - 작가 검색 보정
        |                                |
        +---------------+----------------+
                        |
                        v
[결과 화면]
  - 예상 가격
  - 참고 가격 범위
  - 신뢰도
  - 가격 근거
  - 유사작품/유사작가
  - 계산 과정
  - 보완 입력 안내
  - 실제 판매가 피드백
```

## 5. 사용자 화면 표현 기준

| 내부 개념 | 사용자 화면 표현 | 설명 |
|---|---|---|
| Warm | 이력 기반 예측 | 같은 작가의 가격 이력과 유사작품 정보가 충분한 경우 |
| Cold | 참고 예측 | 같은 작가 가격 이력이 부족해 작품/작가/검색 피처 중심으로 계산하는 경우 |
| artist_key | 표시하지 않음 | 내부 작가 식별자 |
| Quantile | 가격 범위 예측 | 여러 가능 가격 구간을 함께 계산하는 방식 |
| Huber | 이상치에 강한 보정 | 큰 오차에 덜 흔들리도록 잔차를 보정하는 방식 |
| guard | 과대예측 방어 | 불확실성이 큰 경우 너무 높게 예측되는 것을 줄이는 처리 |
| search delta | 작가 검색 정보 보정 | 검색 피처에서 확인된 작가 문맥을 가격에 반영한 보정 |

## 6. Warm 경로

### 6.1 적용 조건

```text
이력 기반 예측 적용 =
  (작가매칭신뢰도점수 >= 0.90)
  AND
  (같은작가_사용가능가격이력수 >= 5)
```

위 조건을 만족하지 못하면 참고 예측 경로로 이동한다.

### 6.2 Warm 계산 구조

```text
최종 이력기반 예측가격 =
  기준가격 + 미세보정값
```

```text
기준가격 =
  같은 작가 가격 이력
  + 유사작품 통계
  + 작품 크기/매체/지지체
  + 기존 Warm 기준 후보 모델
```

```text
미세보정값 =
  방향 확률
  + Huber 잔차
  + 예측 불확실성
  + 유사작품 표본 수
  + 후보 모델 간 차이
```

### 6.3 Warm 상세 계산식

```text
기준로그가격 = 미세보정전_기준로그가격

방향확신도 =
  abs(기준가격보다_높을확률 - 0.5) * 2

보정적용강도 =
  clip((방향확신도 - 0.12) / 0.88, 0, 1)

Huber잔차방향일치 =
  sign(Huber잔차보정후보) == 방향분류모델이_예상한방향

원시보정로그값 =
  Huber잔차보정후보
  * Huber잔차방향일치
  * 보정적용강도
  * 0.025

row위험도 =
  0.25 * 가격범위폭순위
+ 0.20 * 가격범위비율순위
+ 0.20 * 후보모델간차이순위
+ 0.18 * 기준가격과안정가격차이순위
+ 0.09 * 낮은신뢰도여부
+ 0.08 * 낮은유사작품표본여부

보정상한 =
  방향별기본상한
  * (1 - 0.55 * 가격범위폭순위)
  * (1 - 0.80 * row위험도)

적용보정로그값 =
  clip(원시보정로그값, -보정상한, +보정상한)

최종이력기반로그가격 =
  기준로그가격 + 적용보정로그값

최종이력기반예측가격 =
  exp(최종이력기반로그가격)
```

### 6.4 Warm 운영화에 필요한 작업

| 순서 | 작업 | 설명 |
|---:|---|---|
| 1 | 기준가격 생성기 운영화 | raw 입력에서 미세보정전 기준가격 생성 |
| 2 | 방향 확률 모델 운영화 | 기준가보다 실제 가격이 높을 가능성 계산 |
| 3 | Huber 잔차 모델 운영화 | 기준가를 얼마나 미세 조정할지 계산 |
| 4 | 유사작품 통계 cache 구축 | 같은 작가/매체/크기 기반 표본 수와 가격 통계 조회 |
| 5 | 위험도 계산기 구현 | 가격 범위, 표본 수, 후보 차이 기반 보정 상한 계산 |
| 6 | 최종 보정기 연결 | 기준가격과 보정값을 합산해 최종 예측가격 생성 |

## 7. Cold 경로

### 7.1 적용 조건

```text
참고 예측 적용 =
  (이력 기반 예측 조건을 만족하지 못함)
  AND
  (Cold 최소 입력 기준을 만족함)
```

```text
Cold 최소 입력 기준 =
  (한글 작가명 또는 영문 작가명 존재)
  AND (가로 cm 존재)
  AND (세로 cm 존재)
  AND (매체 존재)
  AND (지지체 존재)
```

### 7.2 Cold 계산 구조

```text
최종 참고 예측가격 =
  검색 피처 포함 대표 예측가격
  + 과대예측 방어
  + 작가 검색 보정
```

### 7.3 Cold 상세 계산식

```text
대표로그가격 =
  검색피처포함_LightGBM_Quantile_대표로그가격
```

```text
과대예측방어조건 =
  (가격범위예측폭 >= 폭상위67퍼센트기준)
  AND
  (대표로그가격 - 낮은쪽40퍼센트로그가격 >= gap중앙값기준)
  AND
  (낮은쪽40퍼센트로그가격 < 대표로그가격)
```

```text
방어로그가격 =
  if 과대예측방어조건:
    0.50 * 대표로그가격
  + 0.50 * 낮은쪽40퍼센트로그가격
  else:
    대표로그가격
```

```text
검색보정로그값 =
  작가검색보정lookup[artist_key]
  단, lookup이 없으면 0
```

```text
최종참고예측로그가격 =
  방어로그가격 + 검색보정로그값

최종참고예측가격 =
  exp(최종참고예측로그가격)
```

### 7.4 Cold 운영화에 필요한 작업

| 순서 | 작업 | 설명 |
|---:|---|---|
| 1 | 검색 피처 cache/DB 구축 | 작가명 기반 검색 결과와 품질 점수 저장 |
| 2 | 검색 포함 Quantile 모델 운영화 | q10/q40/q50/q90 가격 구간 예측 |
| 3 | 대표 예측가격 생성기 구현 | 검색 피처 포함 기준 로그가격 생성 |
| 4 | 과대예측 방어 연결 | 불확실성이 큰 경우 낮은쪽 40% 가격 방향으로 조정 |
| 5 | 작가 검색 보정 lookup 연결 | 작가별 검색 기반 보정값 적용 |
| 6 | 신규/검색 없음 fallback 정의 | 검색 피처가 없을 때 보수적 기준으로 처리 |

## 8. DB/cache 계획

공식 테스트 v0.1은 파일만으로도 1차 구동할 수 있지만, 서비스 적용을 목표로 하므로 DB/cache 구조를 전제로 설계한다.

| 테이블 또는 cache | 목적 |
|---|---|
| `artist_registry` | 내부 작가 식별자, 한글명, 영문명, 생년, 국적 저장 |
| `artist_aliases` | 작가명 alias, 영문 slug, 한글/영문 표기 변형 저장 |
| `artwork_price_observations` | 학습/검증/운영 가격 이력 저장 |
| `similar_artwork_stats_cache` | 유사작품 통계와 호당 참고가 저장 |
| `artist_search_feature_snapshots` | 검색 피처와 검색 품질 점수 저장 |
| `warm_feature_snapshots` | Warm 중간 피처 저장 |
| `cold_feature_snapshots` | Cold 중간 피처 저장 |
| `prediction_events` | 예측 요청과 결과 저장 |
| `prediction_calculation_steps` | 계산 단계별 값과 식 저장 |
| `sale_price_feedback` | 실제 판매가 피드백 저장 |
| `training_candidates` | 검수 후 학습 후보 저장 |
| `model_artifact_registry` | 모델 파일, 피처 버전, 성능 지표 관리 |

## 9. 공식 v0.1 API 계획

공식 테스트 v0.1의 API prefix는 `/api/v1`로 둔다.

| Method | Endpoint | 목적 |
|---|---|---|
| `GET` | `/api/v1/health` | 서비스 상태 확인 |
| `GET` | `/api/v1/price-models/current` | 현재 공식 v0.1 모델/정책 조회 |
| `POST` | `/api/v1/artists/resolve` | 작가 후보 조회와 동명이인 확인 |
| `POST` | `/api/v1/artworks/price-estimate` | 단일 작품 가격 예측 |
| `GET` | `/api/v1/predictions/{prediction_id}` | 예측 결과와 계산 과정 재조회 |
| `POST` | `/api/v1/feedback/sale-price` | 실제 판매가 피드백 저장 |
| `GET` | `/api/v1/admin/model-audit` | 운영자용 모델/피처 상태 확인 |

## 10. 공식 v0.1 테스트 화면

| 화면 | 목적 |
|---|---|
| `/test/v0.1` | 공식 테스트 v0.1 메인 화면 |
| `/test/v0.1/debug` | 중간 피처와 계산 단계 검증용 화면 |
| `/test/v0.1/model-status` | 모델/DB/cache 로딩 상태 확인 |

### 10.1 화면 구성

```text
[왼쪽 입력]
  - 작가명 입력
  - 작가 후보 선택
  - 작품 정보 입력
  - 고급 입력 접기/펼치기

[오른쪽 결과]
  - 예상 가격
  - 가격 범위
  - 신뢰도
  - 라우팅 사유
  - 가격 근거
  - 유사작품/유사작가
  - 계산 과정
  - 정보 보완 안내
  - 실제 판매가 피드백
```

## 11. 검증 계획

### 11.1 재현성 검증

```text
동일 입력 반복 검증 =
  같은 입력을 10회 호출
  AND 예측가격 동일
  AND route 동일
  AND 중간 계산값 동일
```

### 11.2 fixed-test parity 검증

```text
fixed-test parity =
  기존 fixed-test 입력 row를 공식 v0.1 feature builder로 재생성
  AND 기존 재현 패키지 중간 컬럼과 비교
  AND 최종 예측값 차이 허용오차 이내
```

### 11.3 라우팅 검증

| 케이스 | 기대 결과 |
|---|---|
| 작가 매칭 신뢰도 높음 + 가격 이력 충분 | 이력 기반 예측 |
| 작가 매칭 신뢰도 높음 + 가격 이력 부족 | 참고 예측 |
| 동명이인 후보 다수 | 예측 보류 또는 후보 선택 요청 |
| 작가명 없음 | 예측 보류 |
| 크기/매체/지지체 부족 | 단일 가격 보류 |
| 검색 피처 없음 | 참고 예측 fallback 또는 낮은 신뢰도 |

## 12. 구현 순서

| 순서 | 작업 | 산출물 |
|---:|---|---|
| 1 | 공식 v0.1 문서 확정 | 본 문서 |
| 2 | 모델 gap 감사 보완 | Warm/Cold 중간 컬럼 dependency map |
| 3 | local DB/cache schema 작성 | SQLite 또는 PostgreSQL 호환 schema |
| 4 | CSV -> DB/cache import script 작성 | 작가/가격/검색/유사작품 기초 데이터 적재 |
| 5 | Warm feature builder skeleton 작성 | raw 입력 -> Warm 중간 피처 |
| 6 | Cold feature builder skeleton 작성 | raw 입력 -> Cold 중간 피처 |
| 7 | `/api/v1` skeleton 작성 | health/current/resolve/estimate |
| 8 | `/test/v0.1` 화면 작성 | 공식 테스트 화면 |
| 9 | fixed-test parity 검증 | 기존 재현 결과와 비교 |
| 10 | 동일 입력 반복 검증 | deterministic test |

## 13. 완료 기준

```text
공식 테스트 v0.1 완료 =
  (사용자 raw 입력으로 이력 기반 예측 가능)
  AND (사용자 raw 입력으로 참고 예측 가능)
  AND (보고서 기준 모델의 fixed-test 결과 재현 가능)
  AND (동일 입력 반복 결과 동일)
  AND (계산 과정이 화면에 설명 가능)
  AND (예측 이벤트와 피처 스냅샷 저장 가능)
  AND (실제 판매가 피드백 저장 가능)
```

## 14. 다음 작업

- 본 문서를 기준으로 기존 내부 개발용 버전 표현과 `report-model` 표현을 정리
- 공식 테스트 v0.1 전용 DB/cache schema 문서 작성
- 공식 테스트 v0.1 API 상세 명세 작성
- 공식 테스트 v0.1 화면 설계 문서 작성
- 이후 코드 구현 시작
