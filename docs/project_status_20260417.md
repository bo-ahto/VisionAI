# VisionAI 1차 시장 가격 예측 프로젝트 현황

> **작성일**: 2026-04-17
> **API URL**: https://visionai-api.ahto.city
> **코덱스 리뷰**: 10회 통과 (57건 지적, 47건 수정)

---

## 1. 프로젝트 개요

한국 신진/중견 작가의 1차 시장(갤러리) 작품 가격을 예측하는 AI API 서비스.
작가명 + 크기 + 매체만 입력하면, 학습 데이터 매칭 + 외부 프로필 자동 수집으로 가격을 예측한다.

---

## 2. 데이터 수집 완료

| 소스 | 작품 | 작가 | 프로필 | 수집일 |
|------|:----:|:----:|:------:|:------:|
| Artsy (GraphQL API) | 30,046 | 1,925 | 전시 이력 포함 | 2026-04-13 |
| Saatchi Art (Constructor.io) | 30,607 | 1,161 | bio/education/exhibitions | 2026-04-16 |
| Artue | 2,756 | 363 | 가격 데이터 | 기존 |
| **합계** | **63,409** | **~3,000** | | |

### 수집 방법
- **Artsy**: GraphQL API (`metaphysics-cdn.artsy.net/v2`), 카테고리+매체 분할로 10K 제한 우회
- **Saatchi**: Constructor.io API + `__NEXT_DATA__` 프로필 파싱, 카테고리 분할 수집
- **뷰어**: artsy.ahto.city (30,046건), saatchi.ahto.city (30,607건)

---

## 3. 모델 학습

### 3.1 학습 데이터

| 소스 | 건수 | 작가 | 가격 중앙 | 클린징 |
|------|:----:|:----:|:---------:|--------|
| Artsy+Artue | 7,640 | 757 | 414만원 | painting, 10만~50억, 크기 유효 |
| Saatchi | 21,721 | 832 | 256만원 | painting, USD→KRW(×1,380) |
| **합계** | **29,361** | **1,589** | **300만원** | |

### 3.2 모델 고도화 이력

| 버전 | 접근법 | GroupKFold MdAPE | 결과 |
|:----:|--------|:----------------:|------|
| v2 | 단순 통합 CatBoost | 43.8% | 기준선 |
| **v3** | **피처 보강 + source + 앙상블** | **38.7%** | **최적** |
| v4 | 피처 확장 (46개) | 40.4% | 과적합 |
| v5 | 하이퍼파라미터 탐색 | 39.0% | 변화 없음 |
| v6 | ratio 보정 | 39.0% | 비율 1.00x |

### 3.3 최종 모델 성능 (v3)

| 평가 | MdAPE | W30 | 비율 |
|------|:-----:|:---:|:----:|
| **KFold (XGBoost, 학습 작가)** | **11.7%** | **78.8%** | — |
| KFold (CatBoost) | 17.1% | 70.1% | — |
| GroupKFold (Cold Start, CatBoost) | 38.9% | 39.9% | 1.07x |

### 3.4 피처 중요도 (상위 5)

| 순위 | 피처 | 중요도 | 카테고리 |
|:----:|------|:------:|----------|
| 1 | artist_total_works | 37.1% | 작가 — 총 작품수 |
| 2 | ln_followers | 10.0% | 작가 — 팔로워 |
| 3 | profile_completeness | 8.4% | 작가 — 프로필 충실도 |
| 4 | artist_birth_year | 7.1% | 작가 — 생년 |
| 5 | area_cm2 | 5.7% | 크기 — 면적 |

---

## 4. API 서비스 (Phase 1~3 완료)

### 4.1 배포 현황

| 서비스 | URL | 상태 | Dokploy |
|--------|-----|:----:|---------|
| **가격 예측 API** | visionai-api.ahto.city | **200 OK** | dev.ahto.city |
| Saatchi 뷰어 | saatchi.ahto.city | 200 OK | dev.ahto.city |
| Artsy 뷰어 | artsy.ahto.city | 200 OK | dev.ahto.city |

### 4.2 API 엔드포인트

| 메서드 | 경로 | 기능 | Phase |
|--------|------|------|:-----:|
| POST | `/api/v1/predict` | 단건 예측 + 외부 수집 + SHAP + 작품 매칭 | 1~3 |
| POST | `/api/v1/predict/batch` | 배치 예측 (최대 50건) | 3 |
| GET | `/api/v1/model/info` | 모델 정보 | 1 |
| GET | `/api/v1/monitor` | 모니터링 대시보드 | 3 |
| GET | `/health` | 헬스체크 + DB 상태 | 1 |

### 4.3 주요 기능

**모델 라우팅**:
- 학습 작가 매칭 (5건+) → XGBoost (MdAPE 11.7%, A등급 ±20%)
- Cold Start → CatBoost (MdAPE 38.9%, D등급 ±70%)

**외부 수집** (Phase 2):
- Artsy GraphQL: searchConnection → slug → 프로필+전시
- Saatchi Constructor.io: autocomplete → __NEXT_DATA__ 파싱
- 인메모리 캐시 (성공만, 5,000건 제한)

**웹검색 생년 보강** (Phase 3):
- DuckDuckGo (키 불필요)
- 동명이인 5단계 필터 (2개 독립 도메인 필수)
- D등급 → C등급 상향 (생년 확보 시)

**SHAP 피처 기여도** (Phase 3):
- CatBoost 예측 시 상위 5개 피처 기여도 반환
- TreeExplainer, threadpool 비동기 실행

**작품 매칭**:
- 제목+작가+크기 정확 매칭 (`exact_title_size`)
- fuzzy 제목 매칭 (띄어쓰기/오타 허용, rapidfuzz 90+)
- 한글/영문 제목 독립 매칭
- 작가 없이 제목만 검색 (전체 인덱스, O(1))
- 크기+매체만 매칭 (`same_size_medium`)

**작가 가격 이력**:
- 매칭 작가의 실제 가격 범위, 중앙값, 호수 범위, 매체, 갤러리
- 수집 날짜 표시 ("Artsy 2026-04-13")

**예측 로그**: JSONL 파일 적재 (매 예측마다)

**모니터링**: 인메모리 카운터 (등급별/모델별/평균ms)

### 4.4 종합 테스트 결과 (21건/21건 PASS, 수동 curl 테스트)

| 카테고리 | 테스트 항목 | 결과 |
|----------|-----------|:----:|
| 인프라 | Health, Model Info, Monitor | PASS |
| 학습 작가 | A등급, XGBoost, 가격 이력 | PASS |
| Cold Start | D등급, SHAP 5건 | PASS |
| 수동 프로필 | C등급 상향 | PASS |
| 외부 수집 | Artsy/웹검색 → C등급, skip | PASS |
| source 보정 | gallery vs online (공식 -7.2%, 실측 -11.9%) | PASS |
| 작품 매칭 | 제목 정확/fuzzy/한글/전체/크기 | PASS |
| 크기별 | 44만→933만 단조 증가 | PASS |
| 배치 | 5건 성공, 60ms | PASS |
| 에러 | 422/400 정상 반환 | PASS |

---

## 5. DB 현황

**postgres-proxy**: `https://postgres-proxy.ahto.city/db/visionai_dev`

| 테이블 | 건수 | 용도 |
|--------|:----:|------|
| artists | 1,589 | 작가 마스터 (pg_trgm 인덱스) |
| artist_profiles | 1,577 | 외부 프로필 캐시 (TTL 기반) |
| model_versions | 1 | v3 활성 |
| predictions | 0 | 예측 로그 (배치 적재 예정) |
| training_candidates | 0 | 학습 후보 적재 (Phase 4) |

---

## 6. 코덱스 리뷰 이력

| Round | 대상 | 지적 | 수정 | 주요 수정 |
|:-----:|------|:----:|:----:|-----------|
| 1~5 | API 기획 문서 | 33 | 28 | Phase 1 스펙 분리, 신뢰도 공식, ratio 보정 |
| 6 | Phase 1 코드 | 8 | 4 | XGBoost label map, 소스 우선순위 |
| 7 | Phase 2+3 코드 | 5 | 5 | threadpool, 캐시 제한, 웹검색 엄격화 |
| 8 | SHAP + 모니터 | 4 | 4 | SHAP→threadpool, 모니터→인메모리 |
| 9 | 작품 매칭 | 7 | 6 | 제목 인덱스 O(1), DoS 방지, 과매칭 수정 |
| **총** | | **57** | **47** | |

---

## 7. 소스 코드 구조

```
src/visionai/price_engine/api/
├── primary_server.py          # 1차 시장 API (현재 운영, visionai-api.ahto.city)
├── primary_schemas.py         # 1차 시장 Pydantic 스키마
├── primary_predictor.py       # 모델 라우팅 + 예측
├── primary_feature_builder.py # 37개 피처 생성
├── artist_matcher.py          # 학습 작가 fuzzy 매칭
├── artsy_client.py            # Artsy GraphQL 실시간 조회
├── saatchi_client.py          # Saatchi 프로필 실시간 조회
├── web_searcher.py            # 웹검색 생년 보강 (DuckDuckGo)
├── external_collector.py      # 외부 수집 오케스트레이터
├── shap_explainer.py          # SHAP 피처 기여도
├── server.py                  # [레거시] 경매(2차시장) API — 현재 미사용
└── schemas.py                 # [레거시] 경매 스키마 — 현재 미사용
```

> `server.py`/`schemas.py`는 경매(2차시장) 전용 레거시 코드. 1차 시장 API는 `primary_*` 파일에서 구현.

**미구현 엔드포인트** (기획서에는 있으나 Phase 4+):
- `GET /api/v1/artist/{name}` — 작가 조회 전용 (Phase 2에서 계획, 미착수)
- `POST /api/v1/training-data` — 학습 데이터 적재 (Phase 4)

---

## 8. 향후 과제 (Phase 4~5)

### Phase 4: 학습 데이터 적재 + 수동 재학습 (3주)

- `POST /api/v1/training-data` 엔드포인트
- training_candidates 워크플로우 (pending → approved → trained)
- 재학습 스크립트 + 성능 비교 리포트 자동 생성
- 모델 교체/롤백 (model_versions 쌍 관리)
- 재학습 판단 기준: 전체의 1%(~300건) 누적 또는 고가 50건+

### Phase 5: 이미지 피처 (4주)

- 작품 이미지 CLIP 임베딩 → 스타일 피처
- conformal prediction (교정된 예측 구간)

### 기타

- 운영 배포 (`visionai-api.brut.bot`, 2대 로드밸런서)
- requirements 버전 고정 + 컨테이너 non-root
- 고가(1천만+) 데이터 보강
- 외부 작가 DB 확장 (Artsy 1,168명 + Saatchi 329명)

---

## 9. 주요 문서

| 문서 | 경로 | 내용 |
|------|------|------|
| API 기획서 v1.5 | `docs/price_prediction_api_plan.md` | 아키텍처, API 스펙, DB 설계, 로드맵 |
| Saatchi 통합 결과 | `docs/saatchi_integration_result.md` | 데이터 수집→학습→고도화 v3~v6 |
| 골든셋 테스트 | `docs/golden_set_test_result.md` | 150건 전문가 검증 |
| 통합 모델 결과 | `docs/integrated_model_result.md` | Artsy+Artue 통합 효과 |
| DB 초기화 SQL | `scripts/init_visionai_db.sql` | 5개 테이블 DDL |
