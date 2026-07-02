# 보고서 기준 Warm/Cold 모델 공식 테스트 v0.1 운영 입력 적용 계획

- 작성일: 2026-06-12
- 공식 버전: `price_prediction_v0.1`
- 목적: `partner_warm_cold_best_model_report.md`에 정리된 Warm/Cold 최고 성능 모델을 사용자가 입력한 작품 정보에서 직접 실행할 수 있는 서비스 구조로 승격
- 적용 대상:
  - Warm: 기준가격 기반 미세 보정 모델
  - Cold: 검색 피처 포함 Quantile 예측 + 과대예측 방어 + 작가 검색 보정 모델
- 현재 판단: fixed-test 재현은 가능하지만, raw 입력 기반 운영 추론은 추가 파이프라인 구축이 필요
- 버전 기준: 이번 문서의 `v0.1`은 공식 서비스 테스트 시작 버전이며, 기존 실험/로컬 구현의 `v0.1`, `v0.2`, `v0.3`, `v0.5` 표기는 내부 개발 이력 또는 아티팩트 버전으로만 취급

## 1. 결론

- 목표는 fixed-test 재현이 아니라, 사용자가 입력한 작가명/작품 정보에서 보고서 기준 Warm/Cold 모델이 실제로 계산되도록 만드는 것
- 기존 로컬 프로토타입 `/test/v0.2`는 raw 입력으로 실행 가능하지만, 보고서의 최종 Warm/Cold 모델과 완전히 같은 계산 경로는 아님
- Warm 보고서 모델은 이미 계산된 중간 예측 컬럼을 입력으로 받는 재현 패키지 상태
- Cold 보고서 모델은 검색 포함 기준 예측값을 받은 뒤 guard+search 후처리를 적용하는 재현 패키지 상태
- 서비스 적용을 위해서는 중간 예측 컬럼을 raw 입력에서 생성하는 feature/model adapter가 필요
- 운영 환경에서는 DB 또는 캐시 저장소가 필요함
- DB는 작가 매칭, 검색 피처, 유사작품 통계, 예측 스냅샷, 실제 판매가 피드백을 저장하는 역할
- v0.5 Cold 운영 아티팩트는 이번 목표의 기본 적용 대상이 아님
- v0.5는 사용자가 별도 승인하기 전까지 적용하지 않음

## 2. 현재 상태

| 구분 | 보고서 기준 모델 | 현재 보유 파일 | raw 입력 직접 실행 | 판단 |
|---|---|---|---|---|
| Warm | 기준가격 기반 미세 보정 모델 | `SUB-WARM-PP258_operational_fixed_test_submission` | 불가 | fixed-test 중간 컬럼을 받아 재현 |
| Cold | 검색 피처 포함 Quantile 예측 + guard+search | `cold_prediction_v0.3` | 불가 | 후처리층은 있으나 상류 검색 포함 기준 예측 생성기가 부족 |
| 기존 로컬 프로토타입 Warm | 내부 Warm 운영 모델 | `price_prediction_v0.1/operational` | 가능 | raw 입력 테스트 가능하지만 보고서 Warm과 다름 |
| 기존 로컬 프로토타입 Cold | search-free Cold 운영 모델 | `cold_prediction_v0.2_operational` | 가능 | 검색 피처 없이 실행 가능하지만 보고서 Cold와 다름 |
| Cold v0.5 | search-free p95 방어 운영 옵션 | `cold_prediction_v0.5_operational` | 가능 | 보고서 기준 최고 성능 모델이 아니므로 기본 적용 제외 |

## 3. 목표 서비스 계산 흐름

```text
[사용자 입력]
  - 작가명
  - 작품명
  - 제작연도
  - 가로/세로/깊이
  - 작품 유형
  - 매체
  - 지지체
        |
        v
[작가 매칭]
  - 한글명/영문명 정규화
  - alias 조회
  - 동명이인 후보 확인
  - 작가 매칭 신뢰도 계산
        |
        v
[운영 피처 생성]
  - 작품 물리 피처
  - 작가 메타 피처
  - 유사작품 통계 피처
  - 검색 피처
  - 예측 불확실성 피처
        |
        v
[Warm/Cold 라우팅]
  - 작가 매칭 신뢰도
  - 같은 작가 사용 가능 가격 이력 수
  - 입력 품질
        |
        +-----------------------------+
        |                             |
        v                             v
[Warm 보고서 모델 경로]         [Cold 보고서 모델 경로]
  - Warm 기준가격 생성           - 검색 피처 포함 Quantile 예측
  - 방향 확률 계산               - 대표 로그가격 생성
  - Huber 잔차 계산              - 과대예측 방어
  - 위험도 기반 보정 상한 계산   - 작가 검색 보정
  - 미세 보정 적용               - 검수 플래그 계산
        |                             |
        +--------------+--------------+
                       |
                       v
              [예측 결과 반환]
                - 예측가격
                - 가격 범위
                - 신뢰도
                - 계산 설명
                - 사용 피처 설명
                - 유사작품/유사작가 근거
```

## 4. Warm 모델 운영화 계획

### 4.1 보고서 Warm 모델이 요구하는 입력

보고서 Warm 모델은 아래 중간 컬럼을 이미 가진 row를 입력으로 받는다.

| 필요한 컬럼 | 의미 | raw 입력에서 생성해야 하는 방법 |
|---|---|---|
| `pp252_log` | 미세 보정 전 기준 로그가격 | Warm 기준가격 생성 모델을 운영 아티팩트로 고정 |
| `pp252_stability_log` | 안정성 우선 기준 로그가격 | 안정성 후보 생성 로직을 운영 아티팩트로 고정 |
| `prob_hist35_pp252` | 실제 가격이 기준가보다 높을 확률 | 방향 분류 모델 저장 및 추론 |
| `resid_huber_pp252` | Huber 잔차 보정 후보 | Huber 잔차 모델 저장 및 추론 |
| `quantile_width` | 예측 불확실성 폭 | Quantile 후보 또는 저장된 범위 모델로 생성 |
| `l10_price_range_ratio` | 가격 범위 비율 | Quantile 하단/상단 가격으로 계산 |
| `svc_group_n` | 유사작품 통계 표본 수 | 같은 작가/매체/크기 통계 DB 또는 캐시에서 조회 |
| `component_prediction_spread` | 후보 모델 간 예측 차이 | Warm 구성 후보들의 로그가격 차이로 계산 |
| `confidence_tier` | 신뢰도 구간 | 표본 수, 예측 폭, 매칭 신뢰도로 계산 |
| `stable_price_band` | 안정 가격대 구간 | 기준가격을 가격대 bucket으로 변환 |

### 4.2 Warm 최종 계산식

```text
기준로그가격 = pp252_log

방향확신도 = abs(prob_hist35_pp252 - 0.5) * 2

보정적용강도 =
  clip(
    (방향확신도 - 0.12) / (1 - 0.12),
    0,
    1
  )

Huber잔차방향일치 =
  sign(resid_huber_pp252) == 방향분류모델이 예측한 방향

원시보정로그값 =
  resid_huber_pp252
  * Huber잔차방향일치
  * 보정적용강도
  * 0.025

row위험도 =
  0.25 * Quantile폭순위
+ 0.20 * 가격범위비율순위
+ 0.20 * 후보모델간차이순위
+ 0.18 * 기준가격과안정가격차이순위
+ 0.09 * 낮은신뢰도여부
+ 0.08 * 낮은유사작품표본여부

보정상한 =
  방향별기본상한
  * (1 - 0.55 * Quantile폭순위)
  * (1 - 0.80 * row위험도)

적용보정로그값 =
  clip(원시보정로그값, -보정상한, +보정상한)

최종Warm로그가격 =
  기준로그가격 + 적용보정로그값

최종Warm가격 =
  exp(최종Warm로그가격)
```

### 4.3 Warm 구현 작업

| 단계 | 작업 | 산출물 |
|---|---|---|
| W1 | PP252 기준가격 생성 코드 추적 | Warm 중간 컬럼 dependency map |
| W2 | PP252/안정성 후보/방향분류/Huber잔차 모델을 재학습 또는 재생성 | 저장 모델 파일 |
| W3 | 유사작품 통계 조회기 구현 | same-artist comparable stats cache |
| W4 | raw 입력 -> PP258 입력 컬럼 변환기 구현 | `warm_pp258_feature_builder.py` |
| W5 | fixed-test feature parity 검증 | 기존 `pp258_model_input_validation_test.csv`와 컬럼 오차 비교 |
| W6 | PP258 최종 보정기 API 연결 | 공식 v0.1 Warm API endpoint |
| W7 | 화면 계산 과정 표시 | 기준가, 보정값, 위험도, 상한 설명 |

### 4.4 Warm 검증 기준

```text
1차 검증:
  기존 fixed-test row를 raw feature builder로 재생성했을 때
  주요 중간 컬럼의 최대 차이가 허용오차 이내인지 확인

2차 검증:
  PP258 최종 예측값이 기존 재현 패키지 결과와 일치하는지 확인

3차 검증:
  동일 입력을 10회 반복 호출해 결과가 완전히 같은지 확인

4차 검증:
  작가 후보 순서 변경, 입력 JSON key 순서 변경, 요청 순서 변경에도 가격이 같아야 함
```

## 5. Cold 모델 운영화 계획

### 5.1 보고서 Cold 모델이 요구하는 입력

Cold 보고서 모델의 후처리층은 아래 값을 요구한다.

| 필요한 컬럼 | 의미 | raw 입력에서 생성해야 하는 방법 |
|---|---|---|
| `y18_qwidth_pred_log` | 검색 피처 포함 대표 로그가격 | LightGBM Quantile + 검색 피처 후보를 운영 아티팩트로 저장 |
| `lgb_q40_pred_log` | 낮은쪽 40% 지점 로그가격 | LightGBM 40분위 모델 저장 |
| `quantile_width_log` | q90 - q10 예측 폭 | LightGBM q10/q90 예측값으로 계산 |
| `artist_key` | 작가 검색 보정 lookup key | 작가 매칭 또는 검색 기반 식별 |
| 검색 보정 delta | 작가별 검색 기반 보정값 | DB 또는 frozen lookup에서 조회 |

### 5.2 Cold 최종 계산식

```text
대표로그가격 =
  검색피처포함_LightGBM_Quantile_대표로그가격

과대예측방어조건 =
  (Quantile예측구간폭 >= 폭상위67퍼센트기준)
  AND
  (대표로그가격 - LightGBM_40분위_로그가격 >= gap중앙값기준)
  AND
  (LightGBM_40분위_로그가격 < 대표로그가격)

방어로그가격 =
  if 과대예측방어조건:
    0.50 * 대표로그가격 + 0.50 * LightGBM_40분위_로그가격
  else:
    대표로그가격

검색보정로그값 =
  작가검색보정lookup[artist_key]
  단, lookup이 없으면 0

최종Cold로그가격 =
  방어로그가격 + 검색보정로그값

최종Cold가격 =
  exp(최종Cold로그가격)
```

### 5.3 검색 피처 운영화

검색 피처는 실시간 검색 API에 매 요청마다 의존하지 않고, DB/캐시 기반으로 운영한다.

| 피처 그룹 | 예시 컬럼 | 생성 방식 |
|---|---|---|
| 검색 결과 수 | `search_result_count` | 작가명 검색 결과 수 |
| 미술 문맥 수 | `search_art_context_count` | 결과 제목/본문에서 미술 관련 키워드 수 |
| 전시 문맥 수 | `search_exhibition_context_count` | 전시/개인전/단체전 관련 키워드 수 |
| 갤러리 문맥 수 | `search_gallery_context_count` | 갤러리/미술관/기관 관련 키워드 수 |
| 작가명 일치율 | `search_name_match_ratio` | 검색 결과에서 입력 작가명과 일치하는 비율 |
| 미술 문맥 일치율 | `search_art_match_ratio` | 검색 결과 중 미술 문맥 비율 |
| 검색 품질 점수 | `search_quality_score` | 검색 성공, 문맥 수, 이름 일치율을 결합 |
| 동명이인 위험 | `search_homonym_risk_grade` | 비미술 문맥 또는 이름 혼선 정도 |
| 상호작용 피처 | `search_quality_x_log_area` 등 | 검색 품질과 작품/작가 조건의 조합 |

### 5.4 Cold 구현 작업

| 단계 | 작업 | 산출물 |
|---|---|---|
| C1 | Cold 검색 보정 후처리 상류 입력 생성 dependency 추적 | Cold 중간 컬럼 dependency map |
| C2 | 검색 피처 DB/cache 스키마 확정 | `artist_search_feature_snapshot` |
| C3 | 검색 포함 LightGBM Quantile 모델 재생성 또는 재학습 | q10/q40/q50/q90 모델 파일 |
| C4 | `y18_qwidth_pred_log` 생성 로직 운영 아티팩트화 | representative candidate generator |
| C5 | 과대예측 방어와 작가 검색 보정 후처리 연결 | 기존 `apply_cold_postprocess_v0_3.py` 재사용 |
| C6 | 검색 보정 lookup DB 연결 | frozen lookup + 신규 작가 fallback |
| C7 | raw 입력 -> Cold 검색 보정 입력 컬럼 변환기 구현 | `cold_v03_feature_builder.py` |
| C8 | 화면 계산 과정 표시 | 대표가, 40분위가, 방어조건, 검색보정 설명 |

### 5.5 Cold 검증 기준

```text
1차 검증:
  fixed-test의 y18_qwidth_pred_log, lgb_q40_pred_log, quantile_width_log를 재생성해 기존 값과 비교

2차 검증:
  Cold 검색 보정 후처리 결과가 기존 재현 결과와 일치하는지 확인

3차 검증:
  검색 lookup이 있는 작가와 없는 작가를 분리해 fallback 동작 확인

4차 검증:
  동일 입력 반복 호출 결과가 완전히 같은지 확인

5차 검증:
  검색 피처 snapshot 버전이 바뀌면 예측 결과도 버전과 함께 저장되는지 확인
```

## 6. DB 적용 계획

### 6.1 로컬 테스트 DB

- 로컬 테스트 단계에서는 SQLite 또는 파일 기반 DuckDB를 사용할 수 있음
- 목적은 DB 의존 구조를 먼저 검증하는 것
- 외부 배포 또는 운영 후보 단계에서는 PostgreSQL로 옮기는 것을 기준으로 함

### 6.2 운영 DB 권장 테이블

| 테이블 | 목적 |
|---|---|
| `artist_registry` | 내부 artist_key와 작가 기본 메타 저장 |
| `artist_aliases` | 한글명/영문명/slug/외부명 alias 저장 |
| `artwork_price_observations` | 학습/검증/운영 가격 이력 저장 |
| `artist_search_feature_snapshots` | 작가별 검색 피처 snapshot 저장 |
| `similar_artwork_stats_cache` | 유사작품 통계와 호당 참고가 cache 저장 |
| `warm_feature_snapshots` | Warm 중간 피처 생성 결과 저장 |
| `cold_feature_snapshots` | Cold 중간 피처 생성 결과 저장 |
| `prediction_events` | 예측 요청, 입력, route, 모델 버전 저장 |
| `prediction_calculation_steps` | 계산 단계별 값과 식 저장 |
| `sale_price_feedback` | 실제 판매가 피드백 저장 |
| `training_candidates` | 검수 완료 후 학습 후보 저장 |
| `model_artifact_registry` | 모델 파일, 피처 버전, 성능 지표 관리 |

### 6.3 예측 이벤트 저장 원칙

```text
예측 1건 저장 =
  사용자 입력 원본
+ 작가 매칭 결과
+ route 판단 결과
+ 원천 피처
+ 파생 피처
+ 중간 예측값
+ 최종 예측값
+ 모델/피처/검색 snapshot 버전
+ 계산 설명
```

## 7. 공식 테스트 v0.1 API 적용 계획

### 7.1 기존 API 유지

- 기존 로컬 프로토타입 `/test/v0.2`와 `/api/v2`는 개발 이력 확인과 비교용으로 유지
- 공식 테스트 v0.1 경로는 `/test/v0.1`과 `/api/v1`로 새로 정의
- 기존 화면을 갑자기 보고서 모델로 바꾸지 않음
- 비교와 회귀 검증을 위해 기존 경로를 보존

### 7.2 공식 테스트 v0.1 API 추가

| Method | Endpoint | 목적 |
|---|---|---|
| `GET` | `/api/v1/health` | 공식 테스트 v0.1 모델 adapter 로딩 상태 |
| `GET` | `/api/v1/price-models/current` | Warm/Cold 보고서 모델 버전과 feature snapshot 버전 |
| `POST` | `/api/v1/artists/resolve` | 작가 매칭과 Warm 가능성 판단 |
| `POST` | `/api/v1/artworks/price-estimate` | 보고서 기준 Warm/Cold 가격 예측 |
| `GET` | `/api/v1/predictions/{prediction_id}` | 예측 결과와 계산 단계 재조회 |
| `POST` | `/api/v1/feedback/sale-price` | 실제 판매가 피드백 저장 |

### 7.3 테스트 화면

| 화면 | 목적 |
|---|---|
| `/test/v0.2` | 기존 로컬 프로토타입 비교용 화면 |
| `/test/v0.1` | 공식 테스트 v0.1 메인 화면 |
| `/test/v0.1/debug` | 중간 피처와 계산값 상세 검증용 |

## 8. 화면 표시 정책

### 8.1 사용자 화면

- 내부 실험명은 노출하지 않음
- `Warm`, `Cold`라는 용어도 사용자에게 직접 노출하지 않음
- 사용자 화면에서는 아래 표현을 사용
  - `이력 기반 예측`
  - `참고 예측`
  - `작가 확인 필요`
  - `정보 보완 필요`

### 8.2 내부 테스트 화면

- 내부 테스트 화면에는 모델 경로를 명확히 노출
- 예시:
  - `보고서 기준 Warm 모델`
  - `보고서 기준 Cold 검색 보정 모델`
  - `검색 피처 snapshot 버전`
  - `feature builder 버전`

## 9. 구현 순서

### 9.1 1단계: 모델 gap 감사

목표: 보고서 모델을 raw 입력으로 실행하기 위해 없는 구성요소를 확정한다.

산출물:
- Warm required column map
- Cold required column map
- raw 입력에서 생성 가능한 컬럼과 불가능한 컬럼 구분
- 필요한 저장 모델 목록
- 필요한 DB/cache 목록

### 9.2 2단계: DB/cache 기반 구축

목표: 작가 매칭, 가격 이력, 검색 피처, 유사작품 통계를 조회 가능한 구조로 만든다.

산출물:
- local SQLite schema
- CSV -> DB import script
- 작가 alias 조회 API
- 검색 피처 조회 API
- 유사작품 통계 조회 API

### 9.3 3단계: Warm PP258 adapter 구축

목표: 사용자의 입력값에서 PP258이 요구하는 중간 컬럼을 생성한다.

산출물:
- Warm raw feature builder
- Warm PP252 기준가격 generator
- Warm 방향 확률 generator
- Warm Huber 잔차 generator
- Warm PP258 final corrector
- fixed-test parity report

### 9.4 4단계: Cold 검색 보정 adapter 구축

목표: 사용자의 입력값에서 과대예측 방어와 작가 검색 보정 후처리가 요구하는 중간 컬럼을 생성한다.

산출물:
- Cold raw feature builder
- 검색 피처 snapshot loader
- 검색 포함 LightGBM Quantile generator
- Cold guard+search postprocessor
- fixed-test parity report

### 9.5 5단계: API/UI 통합

목표: 보고서 모델을 공식 테스트 v0.1 화면에서 실제 입력값으로 확인한다.

산출물:
- `/api/v1/*`
- `/test/v0.1`
- 계산 과정 상세 표시
- 예측 이벤트 저장
- 피드백 저장

### 9.6 6단계: 운영 검증

목표: 서비스 적용 전에 신뢰성 의심 포인트를 제거한다.

검증 항목:
- 동일 입력 반복 결과 동일성
- 입력 순서 변경 결과 동일성
- random seed 고정성
- fixed-test 재현성
- 기존 로컬 프로토타입과의 결과 차이 설명
- 검색 피처 snapshot 변경 시 버전 관리
- DB 미조회/검색 피처 없음 fallback 동작
- Warm/Cold 라우팅 경계 케이스 검증

## 10. 우선순위

| 우선순위 | 작업 | 이유 |
|---:|---|---|
| 1 | Warm/Cold required column gap 감사 | 정확히 무엇이 없어서 raw 입력이 안 되는지 확정 |
| 2 | DB/cache schema 생성 | 작가/검색/유사작품 통계가 없으면 운영화 불가 |
| 3 | Warm PP258 feature builder | Warm은 서비스 핵심 경로이고 신뢰도가 상대적으로 높음 |
| 4 | Cold search feature builder | Cold 최고 성능은 검색 피처 의존도가 높음 |
| 5 | 공식 테스트 v0.1 API/UI | 기존 로컬 프로토타입과 섞지 않고 비교 가능 |
| 6 | 운영 학습 루프 연결 | 실제 판매가 피드백을 다음 학습 후보로 축적 |

## 11. 즉시 착수 범위

바로 시작할 수 있는 1차 작업은 아래와 같다.

```text
1. Warm PP258 입력 컬럼별 dependency audit 생성
2. Cold 검색 보정 입력 컬럼별 dependency audit 생성
3. local DB schema 초안 작성
4. CSV 기반 artist/price/search cache import script 작성
5. 공식 테스트 v0.1 API skeleton 추가
6. /test/v0.1 화면 skeleton 추가
7. fixed-test parity 검증 스크립트 추가
```

1차 작업은 실제 모델 적용 전 기반 작업이므로, v0.5나 다른 운영 후보를 적용하지 않는다.

## 12. 완료 기준

보고서 기준 모델 운영화는 아래 조건을 만족해야 완료로 본다.

```text
완료 조건 =
  (raw 입력으로 Warm 보고서 모델 계산 가능)
  AND (raw 입력으로 Cold 보고서 모델 계산 가능)
  AND (fixed-test 재현 결과와 수치 일치)
  AND (동일 입력 반복 결과 동일)
  AND (계산 과정이 화면과 API 응답에 설명 가능)
  AND (예측 이벤트와 feature snapshot 저장 가능)
  AND (검색 피처/DB fallback 정책 명확)
```
