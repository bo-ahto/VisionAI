# VisionAI 1차 시장 가격 예측 프로젝트 현황

> **작성일**: 2026-04-17
> **API URL**: https://visionai-api.ahto.city
> **Phase**: 1~3 완료 (Phase 4~5 미착수)

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

## 6. API 호출 가이드

### 6.1 기본 예측 (작가명 + 크기 + 매체)

```bash
curl -X POST "https://visionai-api.ahto.city/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_name": "Yoo Suntai",
    "width_cm": 53,
    "height_cm": 45.5,
    "medium": "oil on canvas"
  }'
```

**응답 예시**:
```json
{
  "status": "success",
  "prediction": {
    "price_krw": 5230175,
    "price_usd": 3789,
    "price_range": {"low": 4184140, "high": 6276210},
    "confidence_grade": "A",
    "margin": 0.2
  },
  "model_info": {
    "model_type": "xgboost_v3",
    "is_known_artist": true,
    "training_count": 70
  },
  "processing": {"total_ms": 36, "external_fetch_ms": 0},
  "external_sources_used": [],
  "feature_contributions": [],
  "matched_artworks": [],
  "artist_price_history": {
    "artist_name": "Yoo Suntai",
    "total_works_in_data": 70,
    "price_min": 2911800,
    "price_max": 68061600,
    "price_median": 37853400,
    "ho_range": "1~100호",
    "mediums": ["acrylic", "oil"],
    "galleries": ["Galerie GAIA", "Art Works Paris Seoul Gallery"],
    "data_collected_date": "Artsy 2026-04-13",
    "samples": [
      {"title": "The Words", "price_krw": 68061600, "ho": 100, "medium": "acrylic", "gallery": "Galerie GAIA", "source": "artsy"}
    ]
  }
}
```

> XGBoost 경로는 `feature_contributions`가 빈 배열. CatBoost 경로(Cold Start)에서만 SHAP 기여도 반환.

### 6.2 작품 제목으로 검색

```bash
curl -X POST "https://visionai-api.ahto.city/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_name": "Yoo Suntai",
    "width_cm": 116.8,
    "height_cm": 91,
    "medium": "acrylic",
    "title": "The Words"
  }'
```

제목+작가+크기가 학습 데이터에 있으면 **실제 가격**을 `matched_artworks`로 반환:
```json
{
  "matched_artworks": [
    {
      "title": "The Words",
      "price_krw": 39481800,
      "price_usd": 28610,
      "ho": 50,
      "medium": "acrylic",
      "gallery": "Galerie GAIA",
      "source": "artsy",
      "match_type": "exact_title_size"
    }
  ]
}
```

제목은 띄어쓰기/오타/한글 모두 매칭: `"thewords"`, `"말과글"`, `"Words"` 등.

### 6.3 수동 프로필 입력 (D→C등급 상향)

```bash
curl -X POST "https://visionai-api.ahto.city/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_name": "신진작가",
    "width_cm": 72.7,
    "height_cm": 60.6,
    "medium": "oil on canvas",
    "artist_birth_year": 1990,
    "solo_count": 5,
    "followers": 200
  }'
```

Cold Start(CatBoost)에서는 `feature_contributions`로 **가격에 가장 큰 영향을 준 피처**를 확인 가능:
```json
{
  "feature_contributions": [
    {"feature": "ln_followers", "value": "5.30", "contribution": "+20.1%"},
    {"feature": "artist_total_works", "value": "0", "contribution": "-24.0%"}
  ]
}
```

### 6.4 온라인 마켓 가격 (갤러리 대비 저렴)

```bash
curl -X POST "https://visionai-api.ahto.city/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_name": "작가명",
    "width_cm": 50,
    "height_cm": 50,
    "medium": "acrylic",
    "target_market": "online"
  }'
```

`target_market`: `"gallery"` (기본, 갤러리 가격) 또는 `"online"` (온라인 플랫폼, ~7% 저렴)

### 6.5 외부 수집 스킵

```bash
curl -X POST "https://visionai-api.ahto.city/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_name": "작가명",
    "width_cm": 50,
    "height_cm": 50,
    "medium": "oil",
    "skip_external_lookup": true
  }'
```

`skip_external_lookup: true`면 Artsy/Saatchi/웹검색을 하지 않음 (응답 속도 < 100ms).

### 6.6 배치 예측 (최대 50건)

```bash
curl -X POST "https://visionai-api.ahto.city/api/v1/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "artworks": [
      {"artist_name": "Yoo Suntai", "width_cm": 53, "height_cm": 45.5, "medium": "oil"},
      {"artist_name": "Abang", "width_cm": 72.7, "height_cm": 60.6, "medium": "acrylic"},
      {"artist_name": "unknown", "width_cm": 50, "height_cm": 50, "medium": "watercolor"}
    ],
    "skip_external_lookup": true
  }'
```

**배치 응답 예시**:
```json
{
  "total": 3,
  "success": 3,
  "failed": 0,
  "results": [
    {"index": 0, "status": "success", "prediction": {"price_krw": 5398412, "confidence_grade": "A"}, "model_info": {"model_type": "xgboost_v3"}},
    {"index": 1, "status": "success", "prediction": {"price_krw": 2105716, "confidence_grade": "A"}, "model_info": {"model_type": "xgboost_v3"}},
    {"index": 2, "status": "success", "prediction": {"price_krw": 1795971, "confidence_grade": "D"}, "model_info": {"model_type": "catboost_v3"}}
  ],
  "processing": {"total_ms": 60}
}
```

### 6.7 모니터링

```bash
# 서버 상태
curl "https://visionai-api.ahto.city/health"

# 모델 정보
curl "https://visionai-api.ahto.city/api/v1/model/info"

# 예측 통계
curl "https://visionai-api.ahto.city/api/v1/monitor"
```

### 6.8 신뢰도 등급

| 등급 | 조건 | 마진 | 의미 |
|:----:|------|:----:|------|
| **A** | 학습 작가, 5건+ 이력 | ±20% | 높은 신뢰도 |
| **B** | 학습 작가 소량 (1~4건) | ±30% | 보통 신뢰도 |
| **C** | 외부 프로필 확보 또는 수동 입력 | ±50% | 참고용 |
| **D** | 프로필 없음 | ±70% | 추정치 |

### 6.9 입력 필드

| 필드 | 필수 | 타입 | 설명 |
|------|:----:|------|------|
| artist_name | O | string | 작가명 (한/영 모두 가능) |
| width_cm | O | float | 가로 cm (1~500) |
| height_cm | O | float | 세로 cm (1~500) |
| medium | O | string | 매체 (예: "oil on canvas", "acrylic") |
| title | | string | 작품 제목 (기존 작품 매칭용) |
| target_market | | string | "gallery" (기본) 또는 "online" |
| skip_external_lookup | | bool | true면 외부 수집 스킵 |
| artist_birth_year | | int | 작가 생년 (1900~2010) |
| artist_total_works | | int | 총 작품 수 |
| solo_count | | int | 개인전 횟수 |
| group_count | | int | 단체전 횟수 |
| followers | | int | 팔로워 수 |

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
