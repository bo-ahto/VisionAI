# Track6 가격 예측 모델 서비스 적용 시스템 기획 문서

- 작성일: 2026-06-04
- 문서 목적: 검증된 가격 예측 모델을 실제 서비스에 적용하기 위한 시스템 구조, DB 구성, 데이터 관리, 모델 재학습, 운영 모니터링 방식을 정의
- 관련 API 문서: `docs/track6/planning/service_api_detailed_spec.md`
- 기준 모델:
  - Warm: `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`
  - Warm 안정성: `PP-SVC4`
  - Cold: `PP-Y18 qwidth_bin_oof_min30_cap0.25` 참고 예측가 정책

## 1. 서비스 적용 목표

Track6 모델을 서비스에 적용할 때의 목표:

- 작품 단건 입력으로 예측 가격 제공
- 예측 가격과 함께 가격 범위, 신뢰도, 비교군 통계 제공
- Warm/Cold를 분리해 예측 신뢰도 차이를 화면에 반영
- 서비스 화면에서 필요한 호당가 중앙값, 범위, 매체별 분포, 표본 수 N 제공
- 유사 작품/비교 표본 정보를 설명 근거로 제공
- 신규 데이터가 들어오면 비교군 통계와 모델을 주기적으로 갱신
- 운영 로그를 쌓아 실제 서비스 성능을 추적

## 2. 현재 모델 적용 판단

| 영역 | 적용 판단 | 근거 |
|---|---|---|
| Warm 점 예측 | 서비스 1순위 적용 가능 | `PP-SVC3` test MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331` |
| Warm 안정성 | 반복 검증 통과 | `PP-SVC4` row/artist holdout에서 결합 구조 재선택 |
| Cold 점 예측 | 확정 가격으로는 부적합 | Warm 대비 MdAPE/MAPE/p95 모두 높음 |
| Cold 서비스 표시 | 참고 예측가 + 넓은 범위 + 낮은 신뢰도 | `PP-Y18` 개선 신호는 있으나 p95 위험 존재 |
| 비교군 통계 | 서비스 필수 DB로 관리 | 화면 표시와 신뢰도 산정에 필요 |
| 호당가 | 기존 Track6 `estimated_ho` 산출식으로 서비스 적용 가능 | PP-SVC1 일부 split은 면적 단가 대체 검증, 서비스 v1은 호수 기준으로 산출 |
| 외부 검색 | 실시간 기본값 비활성화 | 품질/동명이인/latency 리스크 |

## 3. 전체 시스템 구조

Figure 1. 서비스 추론 흐름:

```text
서비스 요청
  |
  v
입력 검증
  |
  v
작가명/작품 정보 표준화
  |
  +-- artist_registry 조회
  |       |
  |       +-- Warm: 학습 작가 매칭
  |       +-- Cold: 미매칭 또는 매칭 불확실
  |
  v
comparable_group_stats 조회
  |
  v
모델 피처 생성
  |
  +-- Warm: PP-SVC3 결합 추론
  |       - svc_numeric Huber 예측
  |       - PP-V8 방어 후보 예측
  |       - 로그 가격 70:30 결합
  |
  +-- Cold: LightGBM Quantile 참고 추론
          - q10/q50/q90
          - qwidth 기반 보정
          - 넓은 범위/낮은 신뢰도
  |
  v
가격 범위와 신뢰도 산정
  |
  v
API 응답 생성
  |
  v
prediction_log 저장
```

## 4. 추론 단계 상세

| 순서 | 단계 | 처리 내용 | 주요 산출물 |
|---:|---|---|---|
| 1 | 입력 검증 | 필수 필드, 타입, 지원 범위 확인 | validated request |
| 2 | 표준화 | 작가명, 매체, 지지체, 크기, 호수 정규화 | normalized input |
| 3 | 작가 매칭 | 내부 작가 registry 조회 | route, artist_key, match_status |
| 4 | 비교군 통계 조회 | fallback 순서로 비교군 선택 | comparable_stats |
| 5 | 피처 생성 | Warm/Cold별 feature vector 생성 | model features |
| 6 | 모델 추론 | Warm PP-SVC3 또는 Cold PP-Y18 정책 | pred_log, price_krw |
| 7 | 가격 범위 산출 | 모델 불확실성 + 비교군 분위 범위 반영 | low/high |
| 8 | 신뢰도 산정 | route, N, 범위 폭, 입력 품질 기준 | confidence |
| 9 | 유사 작품 추출 | 비교군 대표 표본 선택 | similar_artworks |
| 10 | 응답 생성 | 화면/협업자용 response 생성 | API response |
| 11 | 로그 저장 | 추론 결과와 latency 저장 | prediction_log |

## 5. 서비스용 DB 구성 방향

### 5.1 핵심 테이블 목록

| 테이블 | 목적 | 필수 여부 |
|---|---|---|
| `artist_registry` | 작가 식별, Warm/Cold 라우팅 | 필수 |
| `artwork_master` | 작품 기본 정보 관리 | 필수 |
| `price_history` | 과거 가격 이력 관리 | 필수 |
| `comparable_group_stats` | 비교군 가격/호당가 통계 | 필수 |
| `comparable_sample_index` | 유사 작품/비교 표본 조회 | 필수 |
| `model_artifact_registry` | 모델 artifact 버전 관리 | 필수 |
| `feature_schema_registry` | 피처 스키마 버전 관리 | 필수 |
| `prediction_log` | 예측 운영 로그 | 필수 |
| `external_artist_signal_cache` | 검색/전시/갤러리 외부 신호 캐시 | 선택 |
| `model_training_run` | 재학습 이력 관리 | 필수 |
| `data_ingestion_run` | 데이터 수집/정제 이력 관리 | 필수 |

## 6. DB 스키마 초안

### 6.1 `artist_registry`

| 필드 | 타입 | 설명 |
|---|---|---|
| `artist_key` | string | 내부 작가 식별자 |
| `artist_name_primary` | string | 대표 작가명 |
| `artist_name_normalized` | string | 정규화 작가명 |
| `artist_name_aliases_json` | json | 한글/영문/별칭 |
| `birth_year` | integer nullable | 출생연도 |
| `death_year` | integer nullable | 사망연도 |
| `nationality` | string nullable | 국적 |
| `is_warm_artist` | boolean | 학습 데이터 내 작가 여부 |
| `train_artwork_count` | integer | 학습 데이터 내 작품 수 |
| `price_history_count` | integer | 전체 가격 이력 수 |
| `artist_match_quality` | string | high/medium/low/conflict |
| `profile_source` | string | internal/manual/external |
| `updated_at` | datetime | 갱신 시각 |

관리 원칙:

- 작가명 매칭은 서비스 신뢰도에 직접 영향
- 동명이인 가능성이 있으면 `artist_match_quality=conflict`
- conflict 작가는 기본 Cold 또는 낮은 신뢰도 Warm route
- 신규 작가 데이터가 누적되면 Warm 전환 후보로 관리

### 6.2 `artwork_master`

| 필드 | 타입 | 설명 |
|---|---|---|
| `artwork_id` | string | 작품 식별자 |
| `artist_key` | string nullable | 내부 작가 식별자 |
| `title` | string nullable | 작품명 |
| `year_made` | integer nullable | 제작년도 |
| `width_cm` | number | 가로 |
| `height_cm` | number | 세로 |
| `depth_cm` | number nullable | 깊이 |
| `area_cm2` | number | 면적 |
| `estimated_ho` | number nullable | 호수 |
| `medium_raw` | string | 원본 매체 |
| `medium_category` | string | 표준 매체 |
| `support_raw` | string nullable | 원본 지지체 |
| `support_category` | string | 표준 지지체 |
| `is_3d_candidate` | boolean | 3D 후보 여부 |
| `source_system` | string | 데이터 출처 |
| `created_at` | datetime | 생성 시각 |
| `updated_at` | datetime | 갱신 시각 |

관리 원칙:

- 모델 피처 생성의 기준 테이블
- 크기 단위는 cm로 통일
- `estimated_ho`가 없으면 기존 Track6 호수 산출식으로 계산 가능. 크기 정보가 부족하면 호당가 산출 불가
- medium/support 표준화 실패는 신뢰도 하락 사유

### 6.3 `price_history`

| 필드 | 타입 | 설명 |
|---|---|---|
| `price_event_id` | string | 가격 이벤트 식별자 |
| `artwork_id` | string | 작품 식별자 |
| `artist_key` | string nullable | 작가 식별자 |
| `price_krw` | integer | 원화 가격 |
| `price_original` | number nullable | 원 통화 가격 |
| `currency_original` | string nullable | 원 통화 |
| `price_date` | date nullable | 가격 기준일 |
| `market_type` | string | gallery/auction/private/unknown |
| `source_type` | string | internal/gallery/cv/manual 등 |
| `is_valid_for_training` | boolean | 학습 사용 가능 여부 |
| `is_valid_for_comparable` | boolean | 비교군 통계 사용 가능 여부 |
| `validation_status` | string | raw/cleaned/verified/excluded |
| `exclusion_reason` | string nullable | 제외 사유 |
| `created_at` | datetime | 생성 시각 |

관리 원칙:

- 학습용 가격과 비교군 통계용 가격을 구분
- 이상치, 중복, 통화 오류, 크기 누락은 제외 또는 검수
- 가격 기준일을 보관해 향후 시장 시점 보정 가능하게 설계

### 6.4 `comparable_group_stats`

| 필드 | 타입 | 설명 |
|---|---|---|
| `stats_id` | string | 통계 row 식별자 |
| `group_key` | string | 비교군 식별자 |
| `group_level` | string | fallback 수준 |
| `artist_key` | string nullable | 작가 기준 그룹일 때 |
| `medium_category` | string nullable | 매체 기준 |
| `support_category` | string nullable | 지지체 기준 |
| `size_bucket` | string nullable | 크기 구간 |
| `sample_count` | integer | 유효 표본 수 N |
| `price_median_krw` | integer nullable | 가격 중앙값 |
| `price_q25_krw` | integer nullable | 가격 25 분위 |
| `price_q75_krw` | integer nullable | 가격 75 분위 |
| `price_q10_krw` | integer nullable | 가격 10 분위 |
| `price_q90_krw` | integer nullable | 가격 90 분위 |
| `unit_price_per_ho_median_krw` | integer nullable | 호당가 중앙값 |
| `unit_price_per_ho_q25_krw` | integer nullable | 호당가 25 분위 |
| `unit_price_per_ho_q75_krw` | integer nullable | 호당가 75 분위 |
| `unit_price_per_area_median` | number nullable | 면적 단가 중앙값 |
| `medium_distribution_json` | json | 매체별 분포 |
| `cutoff_at` | datetime | 통계 산출 기준 시각 |
| `stats_version` | string | 통계 산출 버전 |
| `updated_at` | datetime | 갱신 시각 |

관리 원칙:

- 비교군 통계는 train 기준과 서비스 기준을 분리 관리
- 학습/검증에서는 누수 방지를 위해 시점 또는 split 기준 통계 사용
- 서비스에서는 최신 유효 가격 이력 기준 통계 사용
- `unit_price_per_ho_*`는 기존 Track6 `estimated_ho` v1 기준으로 활성화
- `unit_price_per_area_*`는 내부 검증과 호수 산출 불가 케이스의 보조값으로 유지

### 6.5 `comparable_sample_index`

| 필드 | 타입 | 설명 |
|---|---|---|
| `group_key` | string | 비교군 식별자 |
| `artwork_id` | string | 비교 표본 작품 |
| `price_event_id` | string | 가격 이벤트 |
| `similarity_tags_json` | json | same_artist, similar_size 등 |
| `rank_in_group` | integer | 대표 표본 순위 |
| `display_permission` | string | public_summary/internal_only |
| `created_at` | datetime | 생성 시각 |

관리 원칙:

- 서비스 화면의 유사 작품 리스트에 사용
- 외부 노출 가능 필드와 내부 검수 필드 분리
- 표본 수가 부족할 때는 빈 배열과 사유 반환

### 6.6 `model_artifact_registry`

| 필드 | 타입 | 설명 |
|---|---|---|
| `model_version` | string | 모델 버전 |
| `model_policy` | string | 적용 정책 |
| `model_family` | string | huber_blend/lightgbm_quantile 등 |
| `artifact_path` | string | 모델 파일 위치 |
| `feature_schema_version` | string | 피처 스키마 |
| `postprocessing_policy` | string | 후처리 정책 |
| `metric_summary_json` | json | 검증 성능 |
| `training_data_cutoff_at` | datetime | 학습 데이터 기준일 |
| `is_active` | boolean | 운영 적용 여부 |
| `created_at` | datetime | 생성 시각 |

관리 원칙:

- Warm PP-SVC3는 `svc_numeric`과 PP-V8 산출물을 둘 다 재현해야 함
- 모델 파일만이 아니라 후처리 정책과 피처 스키마를 함께 버전 관리
- API 응답의 `model_version`, `model_policy`와 연결

### 6.7 `prediction_log`

| 필드 | 타입 | 설명 |
|---|---|---|
| `request_id` | string | 요청 ID |
| `created_at` | datetime | 예측 시각 |
| `route` | string | warm/cold/unknown_artist_match |
| `model_version` | string | 모델 버전 |
| `model_policy` | string | 모델 정책 |
| `postprocessing_policy` | string | 후처리 정책 |
| `artist_key` | string nullable | 매칭 작가 |
| `artist_match_status` | string | matched/not_matched/conflict |
| `comparable_group_key` | string nullable | 비교군 |
| `comparable_sample_count` | integer nullable | 비교군 N |
| `price_krw` | integer nullable | 예측 가격 |
| `range_low_krw` | integer nullable | 범위 하한 |
| `range_high_krw` | integer nullable | 범위 상한 |
| `confidence_grade` | string | A/B/C/D |
| `display_policy` | string | 화면 표시 정책 |
| `risk_reasons_json` | json | 위험 사유 |
| `latency_ms` | integer | 처리 시간 |
| `error_code` | string nullable | 에러 코드 |

관리 원칙:

- 운영 품질 모니터링의 핵심 테이블
- Warm/Cold 비율, 신뢰도 분포, 오류율, latency 확인
- 실제 판매/피드백 데이터가 들어오면 사후 성능 평가와 연결

## 7. 비교군 통계 관리 방식

### 7.1 생성 원칙

비교군은 가장 세밀한 조건부터 찾고, 표본 수가 부족하면 더 넓은 조건으로 fallback한다.

| 순서 | group_level | 의미 | 최소 N |
|---:|---|---|---:|
| 1 | `artist_medium_support_size` | 같은 작가 + 같은 재료/지지체 + 유사 크기 | 5 |
| 2 | `artist_size` | 같은 작가 + 유사 크기 | 5 |
| 3 | `artist` | 같은 작가 전체 | 5 |
| 4 | `medium_support_size` | 같은 재료/지지체 + 유사 크기 | 30 |
| 5 | `medium_category_support_size` | 같은 재료 + 같은 지지체 + 유사 크기 | 30 |
| 6 | `medium_size` | 같은 재료 + 유사 크기 | 50 |
| 7 | `global` | 전체 기준 | 전체 |

### 7.2 통계 항목

- 가격 중앙값
- 가격 q25/q75
- 가격 q10/q90
- 호당가 중앙값
- 호당가 q25/q75
- 면적 단가 중앙값
- 매체별 호당가 분포
- 표본 수 N
- 비교군 수준
- 통계 산출 기준일

### 7.3 호당가 관리

호당가 산출은 기존 Track6 `estimated_ho` 산출식을 서비스 v1 표준으로 사용한다.

서비스 v1 산출식:

```text
area_cm2 = width_cm * height_cm
estimated_ho = argmin_h |area_cm2 - HO_TABLE_F[h]|
unit_price_per_ho = price_krw / estimated_ho
```

기준:

- `HO_TABLE_F`: 한국 캔버스 F형 기준 호수별 참조 면적표
- 기준 구현: `scripts/track6_add_size_ho_features.py`의 Track6 split 생성 방식과 동일한 nearest mapping
- 참고: 공용 모듈에는 보간 방식 `area_to_ho_f`도 있으나, 서비스 v1은 Track6 실험 split과 맞추기 위해 nearest mapping을 표준으로 둠
- `ln_estimated_ho = log(max(estimated_ho, 0.01))`
- 실험에서 반복 사용한 `estimated_ho`, `ln_estimated_ho`와 같은 계열

남은 결정은 공식 자체가 아니라 서비스 예외 정책:

- 클라이언트가 `estimated_ho`를 직접 제공한 경우 자동 계산값과 다르면 어느 값을 우선할지
- 3D/입체 작품에 호당가를 표시할지
- 비표준 규격 작품에서 F형 기준 호수 환산을 그대로 쓸지, “추정 호수” 문구를 붙일지
- 호수 산출이 불가능한 경우 면적 단가를 보조로 같이 보여줄지

운영 정책 초안:

- `estimated_ho`가 있는 경우: 검증 후 호당가 계산
- `estimated_ho`가 없는 경우: `width_cm * height_cm` 기반으로 `estimated_ho` 자동 계산
- 크기 정보가 부족하거나 `estimated_ho <= 0`인 경우: 호당가 null, 면적 단가 내부 참고
- API는 `unit_price_per_ho.ho_policy=track6_estimated_ho_f_nearest_v1`을 함께 반환

## 8. 모델 artifact 운영

### 8.1 Warm artifact

필수 구성:

| 구성 | 목적 |
|---|---|
| `svc_numeric` Huber 모델 | 비교군 통계 후보 예측 |
| PP-V8 compact blend 재현 정책 | 방어 후보 예측 |
| PP-SVC3 결합 정책 | 로그 가격 70:30 결합 |
| feature schema | 실험/운영 피처 일치 |
| comparable stats builder | 비교군 통계 피처 생성 |
| preprocessing pipeline | 매체/지지체/크기 표준화 |
| manifest | 버전, 성능, 파일 경로, checksum |

Warm 재현성 테스트:

```text
샘플 입력
  |
  +-- svc_numeric pred_log 재현
  +-- PP-V8 pred_log 재현
  +-- 0.70/0.30 결합 재현
  |
  v
실험 저장 예측값과 diff 확인
```

배포 전 합격 기준:

- 동일 샘플의 `pred_log_svc_numeric` diff 허용 범위 이내
- 동일 샘플의 `pred_log_pp_v8` diff 허용 범위 이내
- 최종 `price_krw` diff 허용 범위 이내
- feature schema mismatch 없음

### 8.2 Cold artifact

필수 구성:

| 구성 | 목적 |
|---|---|
| LightGBM Quantile q10 | 낮은 가격 범위 |
| LightGBM Quantile q50 | 참고 예측가 |
| LightGBM Quantile q90 | 높은 가격 범위 |
| qwidth 보정 정책 | 불확실성 구간별 보정 |
| Cold feature schema | 작가 메타/전시/검색/작품 피처 |
| confidence policy | 낮은 신뢰도 표시 |

Cold 운영 주의:

- 단일 확정 가격으로 표현 금지
- qwidth가 큰 경우 범위 확대
- 작가 매칭 실패와 외부 정보 부족을 risk reason으로 노출
- 사전 수집된 외부 신호만 안정적으로 사용

## 9. 데이터 추가 수집과 갱신 흐름

Figure 2. 데이터 수집부터 모델 재학습까지:

```text
신규 데이터 수집
  |
  +-- 작가 프로필
  +-- 작품 기본 정보
  +-- 가격 이력
  +-- 전시/갤러리/검색 신호
  |
  v
정제/표준화
  |
  +-- 작가명 매칭
  +-- 매체/지지체 표준화
  +-- 크기/호수 검증
  +-- 가격 통화/시점 정리
  |
  v
품질 검수
  |
  +-- 중복 제거
  +-- 이상치 확인
  +-- 학습 사용 가능 여부 표시
  |
  v
DB 반영
  |
  +-- artist_registry
  +-- artwork_master
  +-- price_history
  +-- external_artist_signal_cache
  |
  v
비교군 통계 재계산
  |
  v
모델 재학습 후보 생성
  |
  v
검증/승인
  |
  v
모델 artifact 배포
```

### 9.1 수집 데이터

| 데이터 | 사용 목적 | 갱신 방식 |
|---|---|---|
| 갤러리 판매 데이터 | 가격 이력, 비교군 통계 | 수시/배치 |
| 작가 DB | Warm/Cold 라우팅, 작가 메타 | 주기 배치 |
| CV 데이터 | 작가 활동성 피처 | 주기 배치 |
| 전시/갤러리 정보 | Cold 보조 피처, 신뢰도 | 주기 배치 |
| 검색/뉴스 신호 | 참고 신뢰도, Cold 보조 | 캐시/검수 후 반영 |
| 호수/크기 정보 | 호당가, 크기 피처 | 입력 시 검증 |

### 9.2 데이터 품질 기준

| 검수 항목 | 기준 |
|---|---|
| 작가명 매칭 | alias와 동명이인 검토 |
| 가격 | 통화, 단위, 0/음수, 비정상 고가 검토 |
| 크기 | cm 단위, width/height 양수 |
| 호수 | 공식 기준에 맞는 값인지 확인 |
| 매체/지지체 | 표준 category 매핑 |
| 중복 | 같은 작품/가격 이벤트 중복 제거 |
| 외부 검색 | 동명이인, 무관 검색 결과 제거 |

## 10. 모델 재학습 흐름

### 10.1 재학습 트리거

| 트리거 | 기준 |
|---|---|
| 신규 가격 이력 증가 | 유효 가격 데이터 일정 건수 이상 추가 |
| 신규 작가 증가 | Cold 작가가 Warm 전환 가능한 수준으로 이력 확보 |
| 비교군 통계 변화 | 주요 작가/매체 비교군 중앙값 큰 변화 |
| 운영 오차 증가 | 실제 피드백 기준 오차 상승 |
| 데이터 스키마 변경 | 호수 산출 정책, 매체 category, 작가 메타 변경 |

### 10.2 재학습 절차

| 단계 | 내용 | 산출물 |
|---:|---|---|
| 1 | 데이터 snapshot 생성 | `dataset_snapshot_id` |
| 2 | train/validation/test split 생성 | split manifest |
| 3 | 비교군 통계 생성 | comparable stats snapshot |
| 4 | Warm 후보 재학습 | Huber, svc_numeric, PP-V8 재현 |
| 5 | Cold 후보 재학습 | LightGBM Quantile, qwidth 보정 |
| 6 | 지표 평가 | MdAPE, MAPE, p95_APE, RMSE_log |
| 7 | 안정성 검증 | seed, holdout, bootstrap |
| 8 | 리포트 생성 | model evaluation report |
| 9 | 승인 | 운영 반영 여부 결정 |
| 10 | artifact 배포 | model registry update |

### 10.3 모델 승격 기준

Warm 신규 후보 승격 조건:

- 기존 PP-SVC3 대비 MdAPE 개선
- MAPE 또는 p95_APE 악화 없음
- row/artist holdout에서 선택 안정성 확인
- artifact 재현성 테스트 통과
- 피처 영향도 해석 가능

Cold 신규 후보 승격 조건:

- PP-Y18 대비 MdAPE/MAPE/p95 중 최소 2개 개선
- p95_APE 악화 없음
- qwidth 큰 구간의 위험 감소
- display_policy와 신뢰도 정책 유지 가능
- 단일 확정 가격처럼 보이지 않는 응답 정책 유지

## 11. 운영 모니터링

### 11.1 API 모니터링

| 지표 | 목적 |
|---|---|
| 요청 수 | 사용량 확인 |
| latency p50/p95 | 응답 속도 |
| error rate | 장애 감지 |
| Warm/Cold 비율 | 데이터 커버리지 확인 |
| confidence 분포 | 낮은 신뢰도 비중 추적 |
| comparable_stats available rate | 비교군 DB 품질 |
| similar_artworks available rate | 화면 근거 제공률 |

### 11.2 모델 모니터링

| 지표 | 목적 |
|---|---|
| 예측 가격 분포 | 비정상 예측 감지 |
| 가격 범위 폭 분포 | 과도하게 넓은 범위 감지 |
| route별 가격 분포 | Warm/Cold 편차 확인 |
| 비교군 N 분포 | 통계 신뢰도 확인 |
| qwidth 분포 | Cold 불확실성 변화 확인 |
| 사용자/검수 피드백 오차 | 실제 서비스 품질 확인 |

### 11.3 알림 기준 초안

| 조건 | 조치 |
|---|---|
| error rate 급증 | API 장애 점검 |
| Cold 비율 급증 | 작가 매칭/registry 점검 |
| comparable_stats unavailable 증가 | 비교군 통계 배치 점검 |
| confidence D 비율 급증 | 입력 품질 또는 신규 작가 유입 확인 |
| 가격 범위 폭 비정상 확대 | qwidth/비교군 통계 점검 |

## 12. 배포 전 체크리스트

| 항목 | 확인 내용 |
|---|---|
| API 계약 확정 | 협업자와 path/request/response 합의 |
| Warm artifact 재현 | PP-SVC3 결합 예측 재현 |
| 비교군 DB 구축 | fallback 순서와 최소 N 적용 |
| 호당가 예외 정책 | 직접 입력 호수/자동 계산 호수 충돌, 3D/비표준 작품 표시 기준 |
| Cold 표시 문구 | 참고 예측가/낮은 신뢰도 문구 확정 |
| 유사 작품 노출 | 공개 가능 필드와 내부 필드 분리 |
| prediction_log | 운영 로그 저장 확인 |
| 모니터링 | API/모델 지표 대시보드 준비 |
| 롤백 | 이전 artifact 또는 API 비활성화 계획 |

## 13. 단계별 실행 계획

### 13.1 1단계: API/DB 계약 고정

결과물:

- API 상세 스펙 확정
- DB 테이블 초안 확정
- 기존 Track6 `estimated_ho` v1 적용 확인
- 비교군 fallback 최소 N 결정
- 유사 작품 노출 범위 결정

### 13.2 2단계: 추론 파이프라인 구현

결과물:

- 입력 표준화 모듈
- 작가 매칭 모듈
- 비교군 통계 조회 모듈
- Warm PP-SVC3 추론 모듈
- Cold PP-Y18 참고 추론 모듈
- 가격 범위/신뢰도 산정 모듈

### 13.3 3단계: 운영 검증

결과물:

- 샘플 100건 dry-run
- Warm artifact diff 리포트
- Cold qwidth 범위 sanity check
- 비교군 통계 coverage 리포트
- latency/error 리포트

### 13.4 4단계: 서비스 연동

결과물:

- 단건 예측 API
- 배치 예측 API
- 모델 정보 API
- prediction log 저장
- 모니터링 API 또는 대시보드

## 14. 상사 보고용 요약

- Warm은 `PP-SVC3` 결합 후보가 최종 서비스 1순위
- Warm은 예측 가격과 가격 범위를 제공 가능
- Cold는 아직 확정 가격으로 제공하기 어렵고 참고 예측가와 넓은 범위가 적합
- 서비스 화면에 필요한 호당가/비교군/유사 작품 정보는 별도 DB로 관리 필요
- 호당가 예외 정책, 비교군 fallback, 유사 작품 노출 범위는 서비스 적용 전 결정 필요
- 모델 배포 전 가장 중요한 검증은 Warm PP-SVC3 artifact 재현성
- 데이터가 추가되면 가격 이력과 비교군 통계를 먼저 갱신하고, 일정 기준 충족 시 모델 재학습

## 15. 남은 의사결정

| 항목 | 결정 필요 이유 |
|---|---|
| 호당가 예외 정책 | 직접 입력 호수/자동 계산 호수 충돌, 3D/비표준 작품 표시 기준 |
| API prefix | 협업자 시스템 라우팅 |
| 비교군 fallback 최소 N | 신뢰도와 화면 문구 |
| 가격 범위 calibration | 화면 범위 폭 |
| Cold 참고가 노출 문구 | 예측 신뢰도 차이를 화면에 반영 |
| 유사 작품 공개 범위 | 권리/계약 이슈 방지 |
| 외부 검색 반영 방식 | latency와 검색 품질 안정성 |
| 재학습 주기 | 신규 데이터 반영 속도 |
