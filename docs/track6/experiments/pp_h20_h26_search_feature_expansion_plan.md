# PP-H20~H26 검색 피처 보완 실험 리스트

- 작성일: 2026-06-03
- 목적: PP-H11~H19 이후에도 남아 있는 검색/소셜 인지도 피처의 미검증 영역을 정리하고, 실행 가능한 실험부터 추가 검증한다.
- 현재 전제:
  - 공식 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`는 현재 실행 환경에 없다.
  - 따라서 공식 API 기반 실험은 preflight로 실행 가능 여부를 남기고, 현재 보유한 H11 `naver_html` 수집 결과로 가능한 실험을 먼저 수행한다.

## 1. 전체 실험 목록

| 실험 ID | 실험명 | 목적 | 실행 가능 상태 |
|---|---|---|---|
| `PP-H20` | Naver 공식 API 다중 소스 수집 | 블로그/뉴스/웹문서 결과를 분리 수집해 검색 피처를 안정화 | API 키 필요 |
| `PP-H21` | Google Custom Search 수집 | Google 검색 기반 글로벌/외부 노출 피처 생성 | API 키와 CSE ID 필요 |
| `PP-H22` | Provider 일치도/안정성 검증 | Naver와 Google 결과가 같은 작가 신호를 주는지 확인 | 최소 2개 provider 필요 |
| `PP-H23` | 검색 소스군별 보정 검증 | 갤러리/뉴스/전시/시장/SNS 중 어떤 검색 문맥이 보정에 유효한지 확인 | 현재 H11 데이터로 실행 가능 |
| `PP-H24` | 최근성 기반 보정 검증 | 최근 검색 결과가 있는 작가의 예측 오차가 다른지 확인 | 현재 H11 데이터로 제한 실행 가능 |
| `PP-H25` | 수동 검수 우선순위 생성 | 자동 라벨만으로 부족한 작가를 사람이 검수할 우선순위로 정리 | 현재 H12B/H19 데이터로 실행 가능 |
| `PP-H26` | 위험 segment 전용 fallback | `confidence_only_or_manual_review`처럼 큰 오차가 나는 구간을 별도 정책으로 방어 | 현재 H12B/H19 데이터로 실행 가능 |

## 2. PP-H20 Naver 공식 API 다중 소스 수집

### 실험 질문

- `naver_html` 폴백보다 공식 Naver API가 더 안정적인 검색 피처를 만드는가?
- 블로그, 뉴스, 웹문서 결과를 나누면 가격 예측에 유효한 신호가 더 명확해지는가?

### 수집 대상

| provider | endpoint | 기대 피처 |
|---|---|---|
| `naver_blog` | `/v1/search/blog.json` | 블로그 노출, 개인/리뷰/전시 언급 |
| `naver_news` | `/v1/search/news.json` | 언론 노출, 최근 활동성 |
| `naver_webkr` | `/v1/search/webkr.json` | 일반 웹문서, 기관/갤러리/마켓 출처 |

### 산출 피처

- `naver_blog_total`
- `naver_news_total`
- `naver_webkr_total`
- `naver_blog_recent_count`
- `naver_news_recent_count`
- `naver_webkr_unique_domain_count`
- `naver_provider_coverage_count`
- `naver_art_context_ratio`
- `naver_market_context_ratio`
- `naver_homonym_risk_ratio`

### 성공 기준

- 수집 성공률 95% 이상
- 기존 `naver_html` 대비 UI/광고/프로필 노이즈 감소
- H14 가격 범위 또는 H18 보정에서 p95_APE/MAPE 개선

## 3. PP-H21 Google Custom Search 수집

### 실험 질문

- Google 검색 결과는 국내 Naver 검색으로 잡히지 않는 글로벌 작가 인지도 신호를 제공하는가?
- 영문 작가명 검색 결과가 Cold 가격 예측의 불확실성을 줄이는가?

### 필요 조건

- `GOOGLE_API_KEY`
- `GOOGLE_CSE_ID` 또는 `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`

### 산출 피처

- `google_result_total`
- `google_unique_domain_count`
- `google_art_context_ratio`
- `google_gallery_museum_ratio`
- `google_market_ratio`
- `google_global_visibility_score`
- `google_query_success_flag`

### 성공 기준

- Naver에 없는 작가에서 coverage 증가
- `candidate_for_h14_h18` 또는 `not_collected_by_h11_h12` 구간의 MdAPE/MAPE 개선
- Google 단독보다 Naver+Google 결합의 신뢰도 분리가 더 명확해야 함

## 4. PP-H22 Provider 일치도/안정성 검증

### 실험 질문

- Naver와 Google이 모두 미술/전시/시장 문맥으로 잡는 작가는 예측 오차가 낮은가?
- provider 간 결과가 크게 다르면 동명이인/노이즈 위험으로 볼 수 있는가?

### 산출 피처

- `provider_agreement_score`
- `naver_google_domain_overlap_count`
- `naver_google_art_context_agreement`
- `provider_disagreement_risk_flag`

### 성공 기준

- provider agreement가 높은 구간의 p95_APE가 낮아야 한다.
- disagreement가 높은 구간은 가격 범위를 넓히거나 confidence를 낮추는 정책에 연결되어야 한다.

## 5. PP-H23 검색 소스군별 보정 검증

### 실험 질문

- 갤러리/미술관, 전시, 경매/마켓, 뉴스, SNS/블로그 중 어떤 검색 문맥이 보정에 가장 유효한가?
- 모든 검색 피처를 묶는 것보다 소스군별로 분리하는 것이 더 안정적인가?

### 방법

- H11 표준화 결과에서 작가별 source group count/ratio를 생성한다.
- validation에서 source group 구간별 median residual을 계산한다.
- test에는 validation에서 만든 보정값만 적용한다.

### 성공 기준

- PP-Y2 기준 대비 MdAPE/MAPE/p95_APE 중 하나 이상 개선
- RMSE_log 악화가 과도하지 않아야 함
- 특정 소스군 하나만 과하게 의존하지 않아야 함

## 6. PP-H24 최근성 기반 보정 검증

### 실험 질문

- 최근 검색 결과가 있는 작가는 가격 예측 오차가 다른가?
- 최근 전시/뉴스/시장 언급은 confidence나 가격 범위 조정에 활용 가능한가?

### 방법

- `search_recent_result_count`, `search_recent_result_ratio`를 구간화한다.
- validation median residual 기반으로 test 보정을 적용한다.

### 주의

- 현재 H11의 `naver_html`은 공식 API보다 날짜 정보가 불완전할 수 있다.
- 따라서 H24는 “가능성 확인”으로만 보고, 공식 API 수집 후 재실행해야 한다.

## 7. PP-H25 수동 검수 우선순위 생성

### 실험 질문

- 어떤 작가부터 사람이 검색 결과를 검수해야 H18/H26 보정 안정성이 가장 빨리 개선되는가?

### 방법

- H12B 라벨, validation 오차, 검색 소스군, q-width를 결합한다.
- 아래 조건을 우선 검수 대상으로 둔다.
  - `confidence_only_or_manual_review`
  - validation 오차가 큰 작가
  - 검색 결과는 있으나 작가명 일치율이 낮은 작가
  - market/news/gallery 결과가 있는데 자동 라벨이 약한 작가

### 산출물

- `h25_manual_review_priority.csv`
- `h25_manual_review_template.csv`

## 8. PP-H26 위험 segment 전용 fallback

### 실험 질문

- `confidence_only_or_manual_review` 구간처럼 test p95가 매우 큰 segment를 전체 모델과 같은 방식으로 보정하는 것이 맞는가?
- 위험 segment에만 더 보수적인 fallback을 적용하면 큰 오차를 줄일 수 있는가?

### 방법

- 위험 segment만 별도 보정한다.
- 비교 정책:
  - action별 median residual 보정
  - q-width x action별 median residual 보정
  - q10/q90 방향 블렌딩
  - 보정 강도 cap 축소

### 성공 기준

- `confidence_only_or_manual_review` 구간 p95_APE 개선
- 전체 MdAPE/MAPE가 악화되지 않아야 함
- 작가 단위 안정성 검증 대상 후보로 남길 수 있어야 함

## 9. 실행 순서

| 순서 | 실험 | 이유 |
|---:|---|---|
| 1 | `PP-H20/H21/H22 preflight` | 공식 API 실행 가능 여부를 먼저 명확히 해야 함 |
| 2 | `PP-H23` | 현재 H11 데이터로 바로 가능한 소스군별 검증 |
| 3 | `PP-H24` | 최근성 피처의 제한적 가능성 확인 |
| 4 | `PP-H25` | 수동 검수 우선순위 생성 |
| 5 | `PP-H26` | 큰 오차 위험 segment 보정 |
| 6 | 공식 API 키 확보 후 `PP-H20~H22` 재실행 | 네이버/구글 피처의 완전 검증 |

## 10. 현재 판단

- 지금까지 검색 피처를 “모두” 검증한 것은 아니다.
- 검증 완료된 것은 DuckDuckGo 파일럿과 Naver HTML 폴백 기반의 제한된 검색 피처다.
- 공식 Naver API와 Google Custom Search 기반 피처는 아직 데이터 수집 자체가 되지 않았으므로, 별도 실험으로 남겨야 한다.
- 현 단계에서 가장 실용적인 추가 실험은 `PP-H23~H26`이다.
