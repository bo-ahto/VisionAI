# PP-H 검색/소셜 인지도 피처 운영형 고도화 실험 계획

- 작성일: 2026-06-03
- 목적: PP-H 검색 피처 실험을 단발성 파일럿이 아니라, 서비스와 모델 학습에 반복적으로 사용할 수 있는 운영형 데이터 수집/검증 체계로 고도화한다.
- 기존 근거:
  - `PP-H8` CatBoost 검색 피처 추가는 MdAPE/MAPE가 악화되어 대표 점 예측 후보로 보류했다.
  - `PP-H9` LightGBM Quantile 검색 피처는 MdAPE는 거의 유지하면서 MAPE/RMSE/p95 일부 개선 신호가 있었다.
  - 현재 검색 피처는 점 예측보다 위험도, 가격 범위, 신뢰도, q-width 보정 보조 피처로 더 적합하다.
- 최신 업데이트:
  - 2026-06-03 기준 `Naver 공식 API + Python 검색 라이브러리` provider까지 반영한 최신 결론은 **17장**을 우선한다.
  - 15~16장은 Naver 공식 API 단독 실행 당시의 기록으로 보존한다.

## 1. PP-H 고도화의 핵심 방향

현재 PP-H의 문제는 검색 피처라는 개념 자체가 아니라, 수집 품질과 표준화 부족이다.

| 문제 | 기존 파일럿 상태 | 고도화 방향 |
|---|---|---|
| 검색 결과 품질 | DuckDuckGo 상위 6건 기반, 품질 `low`가 대부분 | 공식 API 또는 안정 공급원 기반으로 결과 수, 출처, 문맥을 표준화 |
| 동명이인 위험 | 단순 키워드 카운트 중심 | 작가명 + 미술 문맥 + 출처 신뢰도 + 동명이인 문맥을 분리 |
| 반복 수집 | 단발 수집에 가까움 | 월간/주간 스냅샷으로 저장하고 수집 버전을 관리 |
| 모델 적용 | CatBoost/LightGBM에 바로 투입 | 품질 점수, 신뢰도, 가격 범위, q-width 보정에 우선 적용 |
| 운영 사용성 | raw search 피처가 모델 실험에만 존재 | DB 테이블, API 응답 필드, 재수집 주기까지 정의 |

## 2. 외부 API 운영 전제

| 공급원 | 운영 판단 | 비고 |
|---|---|---|
| Naver Search Open API | 국내 작가 검색에는 1순위 후보 | 블로그/뉴스/웹문서 결과를 JSON으로 받을 수 있고, `total`, `items`, `postdate` 등 구조화 가능 |
| Python 검색 라이브러리 | 보조 글로벌 provider 후보 | `python_ddg`, `python_ddg_art_context`로 작가별 글로벌 검색 결과를 구조화해 수집 가능 |
| Google Custom Search JSON API | 기존 계정이 있을 때만 보조 후보 | 공식 문서상 신규 고객은 제한되고, 기존 고객도 전환 기한이 있어 장기 운영 주 공급원으로는 위험 |
| Google CSE 공개 URL | 수동 확인용 | 브라우저 화면은 열리지만 파이썬에서 구조화 결과가 내려오지 않아 자동 수집에는 부적합 |
| Google Trends API | 장기적으로 유망하지만 현재는 alpha 신청 필요 | 정식 접근권 확보 전까지 운영 필수 피처로 두지 않음 |
| 비공식 scraping / pytrends | 운영 필수 수집에는 부적합 | 재현성, 약관, 차단, 스키마 변경 위험이 큼 |

따라서 H11은 `Naver 공식 API 중심 + Python 검색 라이브러리 보조 + Google/Trends는 향후 확장`으로 설계한다.

## 3. PP-H11 운영형 검색 수집 표준화

### 3.1 실험 질문

- 같은 작가에 대해 같은 검색어, 같은 공급원, 같은 결과 수, 같은 정규화 규칙으로 주기 수집하면 검색 피처가 안정적인 모델 입력이 되는가?
- 단순 검색 결과 수가 아니라 미술 문맥, 전시/갤러리/경매 문맥, 동명이인 위험을 분리하면 Cold 가격 예측의 신뢰도와 큰 오차 방어가 개선되는가?

### 3.2 수집 단위

검색 피처는 작품 단위가 아니라 작가 단위로 수집한다.

```text
artist_key
-> canonical_artist_name
-> query_template별 검색
-> provider별 raw result 저장
-> 검색 결과 표준화
-> artist_search_snapshot 생성
-> 작품 row에 artist_key로 join
```

### 3.3 표준 검색어 템플릿

| template_id | 검색어 형태 | 목적 |
|---|---|---|
| `name_artist_ko` | `{작가명} 미술 작가` | 기본 작가 검색, 동명이인 노이즈 감소 |
| `name_artwork_ko` | `{작가명} 작품 미술` | 작품/미술 문맥 확인 |
| `name_exhibition_ko` | `{작가명} 전시 작가` | 전시 활동 확인 |
| `name_gallery_ko` | `{작가명} 갤러리 미술` | 갤러리/소속/전시 공간 확인 |
| `name_auction_ko` | `{작가명} 작품 경매` | 시장/판매 문맥 확인 |
| `name_artist_en` | `{영문명} artist` | 글로벌 노출 확인, 영문명이 있을 때만 |

운영 원칙:

- 템플릿은 마음대로 늘리지 않고 버전으로 관리한다.
- 모델 학습에는 `query_template_version`을 함께 남긴다.
- 새 템플릿을 추가하면 기존 데이터와 섞지 않고 새 버전으로 재수집한다.
- 실행 중 검색 결과에 `검색옵션`, `Keep`, `탭`, `도메인 breadcrumb` 같은 UI 링크가 섞이면 raw 결과에는 남기지 않고 표준 결과에서 제외한다.

### 3.4 수집 주기

| 작가 구분 | 수집 주기 | 이유 |
|---|---|---|
| 서비스 노출 후보 전체 작가 | 월 1회 | 검색 노출/전시 언급은 매일 크게 바뀌지 않음 |
| 최근 거래/등록/조회가 많은 작가 | 주 1회 | 시장 관심 변화 가능성이 큼 |
| 신규 작가 | 등록 시 1회 즉시 수집, 이후 월간 수집 편입 | Cold 예측에서 초기 정보 보강 필요 |
| 검색 품질 low 또는 동명이인 위험 high | 월 1회 유지, 모델 반영은 제한 | 자주 수집해도 품질 개선 가능성이 낮음 |

수집 스케줄은 `collector_run_id`, `collected_at`, `provider`, `query_template_version`으로 추적한다.

## 4. 표준 저장 스키마

### 4.1 Raw 결과 테이블

`artist_search_result_raw`

| 컬럼 | 의미 |
|---|---|
| `collector_run_id` | 수집 실행 ID |
| `artist_key` | 내부 작가 ID |
| `canonical_artist_name` | 정규화 작가명 |
| `provider` | `naver_blog`, `naver_news`, `naver_web`, `google_cse`, `trends` 등 |
| `query_template_id` | 검색어 템플릿 ID |
| `query_text` | 실제 검색어 |
| `rank` | 결과 순위 |
| `title` | 결과 제목 |
| `snippet` | 요약문 |
| `url` | 결과 URL |
| `domain` | 출처 도메인 |
| `published_at` | 결과 작성일 또는 노출일 |
| `raw_payload_hash` | 원문 중복/변경 감지 |
| `collected_at` | 수집 시각 |

Raw 결과는 모델에 직접 쓰지 않고, 재처리와 검증을 위해 보관한다.

### 4.2 작가별 표준 피처 테이블

`artist_search_feature_snapshot`

| 컬럼 | 의미 |
|---|---|
| `artist_key` | 내부 작가 ID |
| `snapshot_month` | 월 단위 기준일 |
| `provider_coverage_count` | 수집 성공 provider 수 |
| `search_total_count_norm` | 공급원별 total count를 표준화한 값 |
| `search_result_top_n_count` | 상위 N건 중 유효 결과 수 |
| `search_unique_domain_count` | 중복 제거 출처 수 |
| `search_art_context_count` | 미술/작가 문맥 결과 수 |
| `search_exhibition_context_count` | 전시 문맥 결과 수 |
| `search_gallery_context_count` | 갤러리/기관 문맥 결과 수 |
| `search_auction_market_context_count` | 경매/판매/시장 문맥 결과 수 |
| `search_news_context_count` | 뉴스/언론 문맥 결과 수 |
| `search_social_context_count` | SNS/영상/커뮤니티 문맥 결과 수 |
| `search_homonym_risk_count` | 동명이인 위험 문맥 수 |
| `search_artist_match_score` | 결과가 해당 작가와 맞는 정도 |
| `search_quality_score` | 모델 입력 가능성 점수 |
| `search_quality_grade` | `high`, `medium`, `low`, `missing` |
| `search_feature_version` | 피처 생성 로직 버전 |

### 4.3 모델용 파생 피처

| 피처 | 계산 방식 | 쓰임 |
|---|---|---|
| `log_search_total_count_norm` | `log1p(search_total_count_norm)` | 전체 노출량 |
| `log_search_unique_domain_count` | `log1p(search_unique_domain_count)` | 출처 다양성 |
| `art_match_ratio` | `art_context_count / top_n_count` | 검색 결과의 미술 문맥 일치도 |
| `exhibition_ratio` | `exhibition_context_count / top_n_count` | 전시 활동 신호 |
| `market_ratio` | `auction_market_context_count / top_n_count` | 시장/판매 신호 |
| `homonym_risk_ratio` | `homonym_risk_count / top_n_count` | 동명이인 오염 위험 |
| `search_quality_score` | 아래 품질 점수식 | 모델 반영 강도/신뢰도 |
| `search_recency_score` | 최근 12개월 결과 비율 | 최근 활동성 |

## 5. 검색 품질 점수 표준식

검색 품질 점수는 결과 수가 많다고 높게 주지 않는다. 작가 본인과 관련된 미술 문맥인지가 더 중요하다.

```text
search_quality_score =
  0.30 * art_match_ratio
+ 0.20 * trusted_domain_ratio
+ 0.15 * exhibition_ratio
+ 0.15 * market_ratio
+ 0.10 * recent_result_ratio
+ 0.10 * provider_coverage_score
- 0.30 * homonym_risk_ratio
```

등급 기준:

| grade | 기준 | 모델 반영 |
|---|---|---|
| `high` | `score >= 0.70` and `homonym_risk_ratio < 0.20` | 점 예측/보정/신뢰도 모두 사용 가능 |
| `medium` | `0.45 <= score < 0.70` | 신뢰도/범위/보정 보조로 사용 |
| `low` | `score < 0.45` or `homonym_risk_ratio >= 0.40` | 점 예측에는 직접 사용하지 않음 |
| `missing` | 수집 실패 또는 작가명 없음 | 결측 flag만 사용 |

이 점수식은 H11에서 고정 초안으로 시작하고, H12에서 수동 검수 샘플로 보정한다.

## 6. PP-H11~PP-H18 상세 실험

### PP-H11. 운영형 검색 수집 표준화

| 항목 | 내용 |
|---|---|
| 목적 | 검색 피처를 주기적으로 재수집 가능한 표준 데이터로 만든다 |
| 입력 | 작가명, 작가 영문명, 내부 `artist_key`, 기존 작가 메타 |
| 수집 | Naver Blog/News/Web 중심, 가능 시 Google/Trends 보조 |
| 산출물 | raw result table, monthly feature snapshot, 품질 점수 |
| 성공 기준 | 작가 coverage, 수집 성공률, 품질 high/medium 비율, 재수집 변동률 기록 |
| 모델 적용 | 이 단계에서는 모델 성능보다 데이터 품질과 운영 가능성 확인 |

H11에서 반드시 남길 값:

- 수집 가능한 작가 비율
- 공급원별 성공률
- 작가당 평균 유효 검색 결과 수
- 작가당 unique domain 수
- high/medium/low/missing 비율
- 한 달 뒤 재수집 시 주요 피처 변동률

### PP-H12. 동명이인/작가 일치 판정 고도화

| 항목 | 내용 |
|---|---|
| 목적 | 검색 결과가 해당 작가 본인인지 판정하는 기준을 만든다 |
| 방법 | 상위 결과 제목/요약/도메인에서 미술 키워드, 전시/갤러리 키워드, 동명이인 키워드를 분리 |
| 추가 검수 | 샘플 100~200명 수동 검수로 품질 점수 threshold 보정 |
| 성공 기준 | high/medium 등급의 실제 작가 일치율이 충분히 높아야 함 |

수동 검수 라벨:

| 라벨 | 의미 |
|---|---|
| `match_artist` | 해당 작가 본인 검색 결과 |
| `partial_match` | 작가명은 맞지만 가격 예측에 약한 정보 |
| `homonym` | 동명이인 또는 다른 분야 인물 |
| `irrelevant` | 무관 결과 |

### PP-H13. 검색 품질 등급별 모델 반영

| 항목 | 내용 |
|---|---|
| 목적 | 검색 품질이 높은 작가에서만 검색 피처를 점 예측에 쓰면 성능이 개선되는지 확인 |
| 모델 | Cold LightGBM Quantile, Cold CatBoost |
| 비교 | 전체 검색 피처 사용 vs high/medium만 사용 vs low는 missing 처리 |
| 성공 기준 | high/medium 구간에서 MdAPE/MAPE 개선, 전체 p95 악화 없음 |

핵심은 검색 피처를 모든 작가에 강제로 넣지 않는 것이다.

### PP-H14. 검색 피처 기반 신뢰도/가격 범위 보조

| 항목 | 내용 |
|---|---|
| 목적 | 검색 피처를 점 예측이 아니라 가격 범위와 신뢰도 산출에 사용 |
| 입력 | `search_quality_grade`, `homonym_risk_ratio`, `provider_coverage_count`, `search_recency_score` |
| 적용 | 품질 low/high에 따라 가격 범위 폭, 신뢰도 등급, p95 위험 표시 조정 |
| 성공 기준 | 가격 범위 포함률 개선, high/medium/low 등급별 오차 차이가 명확해야 함 |

서비스 적용 예:

```text
if search_quality_grade == "high" and qwidth_bin is stable:
    confidence = "높음"
    range_multiplier = 1.0
elif search_quality_grade == "medium":
    confidence = "보통"
    range_multiplier = 1.2
else:
    confidence = "낮음"
    range_multiplier = 1.5
```

### PP-H15. 최근성 기반 검색 피처

| 항목 | 내용 |
|---|---|
| 목적 | 전체 검색량보다 최근 12개월 전시/뉴스/경매 언급이 가격 예측에 더 유효한지 확인 |
| 피처 | `recent_12m_result_count`, `recent_exhibition_count`, `recent_market_count`, `recent_news_count` |
| 성공 기준 | Cold MAPE/p95 또는 신뢰도 구간 분리가 개선되어야 함 |

최근성 피처는 작품 가격 예측에서 “요즘 시장에서 보이는 작가인가”를 설명하는 데 쓰인다.

### PP-H16. 출처별 검색 피처 분리

| 출처 | 기대 의미 |
|---|---|
| 갤러리/미술관 도메인 | 작가 활동/전시 신뢰도 |
| 뉴스 도메인 | 대중/언론 노출 |
| 경매/마켓 도메인 | 시장 거래 신호 |
| 블로그/카페 | 대중 관심, 노이즈 가능성도 높음 |
| SNS/영상 | 관심도 보조, 가격 예측에는 신중히 사용 |

실험은 모든 출처를 합치지 않고 출처군별로 분리해서 한다.

### PP-H17. 검색 기반 작가 인지도 점수

| 항목 | 내용 |
|---|---|
| 목적 | raw 검색 피처 수십 개 대신 운영용 단일/소수 score로 단순화 |
| 산출 | `artist_search_awareness_score`, `artist_market_visibility_score`, `artist_search_quality_score` |
| 성공 기준 | raw 전체 피처보다 성능이 유지되거나, 설명/운영 안정성이 높아야 함 |

권장 점수:

```text
artist_search_awareness_score
= log_search_total_count_norm
  + unique_domain_score
  + news/social visibility
  - homonym penalty

artist_market_visibility_score
= gallery_context_score
  + exhibition_context_score
  + auction_market_context_score
  + recent_market_score
```

### PP-H18. 검색 품질 + q-width 보정 결합

| 항목 | 내용 |
|---|---|
| 목적 | 현재 Cold 유망 후보인 `PP-Y18 qwidth_bin` 보정에 검색 품질을 결합 |
| 기준 모델 | `PP-Y2` 또는 `PP-Y18 qwidth_bin_oof_min30_cap0.25` |
| 보정 기준 | `qwidth_bin x search_quality_grade`, `qwidth_bin x homonym_risk_grade` |
| 성공 기준 | `PP-Y18` 대비 MdAPE/MAPE/p95 중 하나 이상 개선, 나머지 악화 제한 |

가설:

- q-width는 모델이 느끼는 예측 불확실성이다.
- 검색 품질은 작가 정보 신뢰도다.
- 두 값을 결합하면 “예측이 불확실하고 검색 품질도 낮은 작가”를 별도 위험 구간으로 분리할 수 있다.

## 7. 운영 DB/API 연결 방식

### 7.1 학습 DB

모델 학습에는 반드시 snapshot 기준을 사용한다.

```text
artwork row
-> artist_key
-> prediction_date
-> latest artist_search_feature_snapshot before prediction_date
```

운영에서 미래 데이터를 쓰는 누수를 막기 위해, 예측 시점 이후 수집된 검색 스냅샷은 학습/검증에 사용하지 않는다.

### 7.2 서비스 API 응답 예시

```json
{
  "artist_search_signal": {
    "quality_grade": "medium",
    "awareness_score": 0.62,
    "market_visibility_score": 0.48,
    "homonym_risk_grade": "watch",
    "snapshot_month": "2026-06",
    "provider_count": 3
  },
  "prediction_confidence": {
    "grade": "보통",
    "reason_codes": [
      "작가 검색 품질 보통",
      "예측 불확실성 중간"
    ]
  }
}
```

서비스에 보여줄 값은 raw 검색 결과 수가 아니라, 품질 등급과 신뢰도 사유 코드 중심으로 둔다.

## 8. 실행 우선순위

| 순서 | 실험 | 이유 |
|---:|---|---|
| 1 | `PP-H11` | 운영형 수집 표준이 없으면 이후 실험이 재현되지 않음 |
| 2 | `PP-H12` | 동명이인/무관 검색 제거 없이는 CatBoost/LightGBM 모두 노이즈 위험 |
| 3 | `PP-H12B` | 검색 UI/무관 결과를 보수적으로 제거해 운영 후보를 더 엄격하게 선별 |
| 4 | `PP-H14` | 현재 결과상 점 예측보다 신뢰도/범위 보조가 더 가능성 높음 |
| 5 | `PP-H18` | 최신 Cold 유망 후보 `PP-Y2/PP-Y18`의 q-width 보정과 직접 연결 가능 |
| 6 | `PP-H19` | H18 개선이 특정 row/작가 구성에 의존하는지 안정성 확인 |
| 7 | `PP-H13` | 검색 품질이 충분히 개선된 후 점 예측 모델에 제한적으로 재투입 |
| 8 | `PP-H15~H17` | 최근성, 출처별 분리, score 단순화는 운영 안정화 단계 |

## 9. 채택/중단 기준

| 기준 | 채택 | 보류 |
|---|---|---|
| 수집 성공률 | 주요 작가 coverage가 충분함 | missing이 많아 모델 적용 불가 |
| 품질 등급 | high/medium 비율이 충분하고 수동 검수 일치율 양호 | low/homonym 비율이 높음 |
| 성능 | MAPE/p95 또는 신뢰도 구간 분리 개선 | MdAPE/MAPE/p95 전반 악화 |
| 운영성 | 월간 재수집 가능, provider 비용/쿼터 관리 가능 | 수집 비용 과다 또는 API 지속성 불안 |
| 설명력 | 신뢰도 사유 코드로 설명 가능 | 모델 입력값으로만 쓰이고 해석 불가 |

## 10. PP-H11 1차 실행 결과

### 10.1 실행 설정

| 항목 | 값 |
|---|---|
| 실행 ID | `pp_h11_20260603_131328` |
| 작가 수 | 80명 |
| provider | `naver_html` |
| query template 수 | 5개 |
| 요청 수 | 400개 |
| 요청당 결과 수 | 최대 5개 |
| 실행 시간 | 286.33초 |
| 산출 snapshot | `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv` |

이 절은 Naver 공식 API 등록 전 수행한 1차 `naver_html` 폴백 실행 이력이다. 이후 2026-06-03에 공식 Naver API `blog/news/webkr` 수집을 완료했으므로, 최종 판단에는 15~16장의 공식 API 기준 결과를 우선 적용한다.

### 10.2 수집/표준화 결과

| 지표 | 결과 | 해석 |
|---|---:|---|
| 요청 성공률 | 1.0000 | 400개 검색 요청 모두 결과 반환 |
| 요청 오류율 | 0.0000 | 네트워크/HTTP 오류 없음 |
| 작가 성공률 | 1.0000 | 80명 모두 검색 결과 확보 |
| medium 이상 비율 | 0.4625 | 80명 중 37명은 보조 피처 후보 |
| low 비율 | 0.5375 | 80명 중 43명은 점 예측 직접 투입 보류 |
| high 비율 | 0.0000 | 공식 API/수동 검수 전 high 판정은 보수적으로 없음 |
| 평균 품질 점수 | 0.421175 | 검색 피처는 직접 점 예측보다 신뢰도/범위 보조가 적합 |
| 평균 미술 문맥 비율 | 0.6225 | 강화 템플릿 후 미술 문맥 결과는 충분히 늘어남 |
| 평균 작가명 매칭률 | 0.4200 | 작가 식별은 추가 고도화 필요 |

### 10.3 수집기 수정 효과

초기 실행은 검색어가 넓고 UI 링크가 섞여 품질이 낮았다. 이후 질의 템플릿을 미술 문맥 중심으로 바꾸고, Naver UI 링크를 제거한 뒤 재수집했다.

| 실행 | medium 작가 수 | low 작가 수 | 평균 품질 점수 | 평균 작가명 매칭률 | 평균 미술 문맥 비율 |
|---|---:|---:|---:|---:|---:|
| 초기 템플릿 | 5 | 75 | 0.314850 | 0.1465 | 0.4110 |
| 강화 템플릿 + UI 링크 제거 | 37 | 43 | 0.421175 | 0.4200 | 0.6225 |

따라서 H11은 “외부 검색 수집 자체는 가능하나, 검색어와 결과 필터를 표준화하지 않으면 운영 피처로 쓰기 어렵다”는 결론이다.

### 10.4 후속 판단

- `medium` 등급 37명은 PP-H13/PP-H14/PP-H18의 후보 입력으로 사용할 수 있다.
- `low` 등급 43명은 가격점 예측 피처로 직접 쓰지 않고, 신뢰도 하향 또는 검수 대상으로 둔다.
- `high` 등급이 없는 것은 공식 API 미사용, 단일 provider, 수동 검수 부재 때문이므로 H12에서 작가 일치 라벨을 보강해야 한다.
- 운영에서는 월간 스냅샷을 누적해 같은 작가의 검색 품질 변화량과 최근 전시/시장 노출 변화를 보는 방식이 더 의미 있다.

## 11. 현재 단계의 결론

- PP-H는 지금 상태로 CatBoost 대표 점 예측에 다시 넣는 것은 우선순위가 낮다.
- 먼저 `PP-H11`로 검색 수집을 표준화하고, `PP-H12`로 작가 일치/동명이인 판정을 고도화해야 한다.
- 이후 `PP-H14`와 `PP-H18`처럼 신뢰도, 가격 범위, q-width 보정에 연결하는 실험이 가장 실용적이다.
- 검색 피처는 “가격을 직접 맞추는 피처”보다 “예측을 믿을 수 있는지, 범위를 얼마나 넓혀야 하는지, 위험 구간인지”를 알려주는 운영 피처로 설계하는 것이 맞다.

## 12. PP-H12 1차 실행 결과

### 12.1 실행 설정

| 항목 | 값 |
|---|---|
| 실행 ID | `pp_h12_20260603_132409` |
| 입력 snapshot | `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv` |
| 입력 표준 검색 결과 | `data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv` |
| 검색 결과 row 수 | 2,000 |
| 작가 수 | 80 |
| 수동 검수 템플릿 row 수 | 240 |
| 리포트 | `experiments/track6/PP-H12_search_match_disambiguation_review/reports/result_report.html` |

### 12.2 검색 결과 단위 자동 판정

| 자동 라벨 | 결과 수 | 비율 | 해석 |
|---|---:|---:|---|
| `match_artist` | 719 | 0.3595 | 작가명과 미술/전시/갤러리/시장 문맥이 함께 확인됨 |
| `partial_match` | 479 | 0.2395 | 일부 문맥은 맞지만 가격 예측 피처로 쓰기 전 검수 필요 |
| `irrelevant` | 786 | 0.3930 | 무관 결과 가능성이 높음 |
| `homonym` | 16 | 0.0080 | 동명이인 위험 결과 |

### 12.3 작가 단위 자동 판정

| 자동 라벨 | 작가 수 | 후속 처리 |
|---|---:|---|
| `usable_match` | 37 | H14/H18 후보 |
| `weak_match` | 21 | 신뢰도 보조 또는 수동 검수 필요 |
| `low_match` | 22 | 점 예측 직접 사용 보류 |

추천 액션 기준으로 보면:

| 추천 액션 | 작가 수 | 의미 |
|---|---:|---|
| `candidate_for_h14_h18` | 37 | 검색 품질을 신뢰도/가격 범위/q-width 보정에 제한적으로 사용 가능 |
| `confidence_only_or_manual_review` | 21 | 사람이 확인하기 전까지 점 예측에는 넣지 않음 |
| `do_not_use_for_point_prediction` | 22 | 검색 결과가 있어도 노이즈 가능성이 커서 점 예측에는 사용하지 않음 |

### 12.4 해석

- H12 결과는 H11의 `medium` 등급 37명을 그대로 H14/H18 후보군으로 확인했다.
- `low` 등급 중 일부는 부분 매칭이 있으나, 작가 본인 여부가 약해 수동 검수 없이 모델 점 예측 피처로 넣기 어렵다.
- 따라서 검색 피처는 전체 Cold 데이터에 일괄 투입하지 않고, `candidate_for_h14_h18` 작가에 한정해 신뢰도/범위/q-width 보정으로 연결하는 것이 타당하다.
- 수동 검수용 파일은 `experiments/track6/PP-H12_search_match_disambiguation_review/outputs/manual_review_template.csv`에 생성했다.

## 13. PP-H14/H18 1차 실행 결과

### 13.1 실행 설정

| 항목 | 값 |
|---|---|
| 기준 예측 | `PP-Y2 lgbq_search_all_external_interaction` |
| H12 입력 | `experiments/track6/PP-H12_search_match_disambiguation_review/outputs/artist_match_review_queue.csv` |
| q-width 경계 | validation 33/66 분위 |
| 범위 정책 | 기존 q10~q90, 단순 배율, conformal80, conformal90 비교 |
| 보정 정책 | `qwidth_bin x H12 recommended_action` segment별 validation median residual |
| 리포트 | `experiments/track6/PP-H14_H18_search_confidence_qwidth_policy/reports/result_report.html` |

### 13.2 H14 가격 범위 결과

| 후보 | test coverage | median range ratio | 판단 |
|---|---:|---:|---|
| 기존 q10~q90 | 0.6089 | 3.8452 | 포함률 부족 |
| 단순 배율 정책 | 0.7541 | 7.3457 | 개선되지만 등급별 안정성 약함 |
| `conformal80` | 0.7899 | 7.6368 | 80% 목표에 가장 가까운 후보 |
| `conformal90` | 0.8751 | 11.3506 | 보수적이나 범위가 넓음 |

운영 해석:

- 서비스 표시 범위는 단순 배율보다 validation conformal buffer가 더 설명 가능하다.
- 현재는 `conformal80`을 우선 후보로 보고, 보수 표시가 필요한 경우에만 `conformal90`을 검토한다.
- validation에서 calibration되지 않은 `high` 등급은 제거하고, `medium/low` 2단계부터 시작하는 것이 안전하다.

### 13.3 H18 q-width x 검색 신뢰도 보정 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| H18 best `min80_cap0.2` | 0.4239 | 1.0328 | 3.0077 | 0.8598 | 대표/평균/tail 개선, RMSE_log 소폭 악화 |

개선폭:

| 지표 | 변화 |
|---|---:|
| MdAPE | -0.0183 |
| MAPE | -0.0156 |
| p95_APE | -0.3460 |
| RMSE_log | +0.0031 |

운영 해석:

- 검색 신뢰도와 q-width를 결합한 보정은 Cold 큰 오차를 줄이는 데 의미 있는 신호가 있다.
- 이 결과는 H12 자동 라벨 기반이므로 최종 채택 전 수동 검수 라벨을 반영해 재실행해야 한다.
- PP-H는 점 예측 피처라기보다 `불확실성 보정`, `가격 범위`, `신뢰도 표시` 축으로 유지하는 것이 타당하다.

### 13.4 H12B 보수 라벨 보정 결과

H12 자동 라벨은 검색 결과가 조금만 맞아도 후보로 남기는 경향이 있어, 운영 적용 전 보수 라벨 보정 실험을 추가했다.

| 구분 | H12 자동 라벨 | H12B 보수 라벨 | 해석 |
|---|---:|---:|---|
| H14/H18 후보 작가 | 37 | 31 | 검색 노이즈 가능성이 있는 작가를 후보에서 제외 |
| 수동 검수/신뢰도 보조 | 21 | 21 | 애매한 작가는 유지 |
| 점 예측 직접 사용 보류 | 22 | 28 | 제외 대상 증가 |

H12B 기반으로 H14/H18을 다시 실행한 결과는 다음과 같다.

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `min80_cap0.2` | 0.4253 | 1.0471 | 3.0077 | 0.8621 | MdAPE 최우선 후보 |
| `min30_cap0.2` | 0.4347 | 0.9602 | 3.0077 | 0.8437 | MAPE/RMSE 균형 후보 |
| `min30_cap0.1` | 0.4316 | 0.9832 | 3.0077 | 0.8504 | 보정 강도 낮춘 안정 후보 |

H12B 적용 후에도 p95_APE 개선은 유지됐다. 다만 어떤 지표를 우선할지에 따라 후보가 달라지므로, H19에서 안정성 검증을 추가했다.

### 13.5 PP-H19 안정성 검증 결과

H19는 H12B 기반 H18 후보를 row bootstrap 600회, artist bootstrap 600회로 검증했다. delta는 `기준 모델 점수 - 보정 후보 점수`이며, 오차 지표에서는 양수일수록 좋다.

| 후보 | 기준 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | RMSE 개선확률 | 판단 |
|---|---|---:|---:|---:|---:|---|
| `min30_cap0.1` | row | 0.9650 | 1.0000 | 1.0000 | 1.0000 | 작품 단위 매우 안정 |
| `min30_cap0.1` | artist | 0.8517 | 1.0000 | 0.9650 | 0.7600 | 작가 단위도 비교적 안정 |
| `min30_cap0.2` | row | 0.9050 | 1.0000 | 1.0000 | 1.0000 | 평균 오차 개선 강함 |
| `min30_cap0.2` | artist | 0.7317 | 0.9417 | 0.8467 | 0.7583 | 작가 구성에 다소 민감 |
| `min80_cap0.2` | row | 1.0000 | 0.6233 | 0.9650 | 0.0000 | MdAPE 중심 후보 |
| `min80_cap0.2` | artist | 0.9383 | 0.5400 | 0.5467 | 0.2100 | MdAPE 외 지표는 불안정 |

현재 판단:

- 운영 안전안: `min30_cap0.1`
- 평균 오차 개선안: `min30_cap0.2`
- MdAPE 전용 탐색안: `min80_cap0.2`
- 최종 채택 전 필수 조건: 수동 검수 라벨 기반 H18/H19 재실행

## 14. 참고 공식 문서

- Naver Search API: `https://developers.naver.com/docs/serviceapi/search/blog/blog.md`
- Google Custom Search JSON API: `https://developers.google.com/custom-search/v1/overview`
- Google Trends API alpha: `https://developers.google.com/search/apis/trends`

## 15. PP-H20~H26 보완 실행 결과 - Naver 공식 API 단독 기준 기록

### 15.1 실행 상태

PP-H11~H19 이후 검색 피처의 미검증 영역을 보완하기 위해 `PP-H20~H26`을 추가했다. 2026-06-03 기준 공식 Naver Search API 인증값을 환경변수로 주입해 `blog/news/webkr` 수집을 완료했다. 인증값은 코드나 문서에 저장하지 않는다.

| 실험 | 내용 | 현재 상태 |
|---|---|---|
| `PP-H20` | Naver 공식 API blog/news/webkr 분리 수집 | 완료 |
| `PP-H21` | Google Custom Search 수집 | Custom Search JSON API 접근 권한 문제로 blocked |
| `PP-H22` | Naver x Google provider agreement 검증 | 성공한 Google provider 결과가 없어 blocked |
| `PP-H23` | H11 source group별 보정 | 실행 완료 |
| `PP-H24` | 최근성 기반 보정 | 실행 완료 |
| `PP-H25` | 수동 검수 우선순위 생성 | 실행 완료 |
| `PP-H26` | 위험 segment fallback | 실행 완료 |

따라서 “Naver 공식 API 기반 피처 검증은 완료, Google 기반 글로벌 노출 및 provider 일치도 검증은 미완료”로 정리한다. Google API 키와 CSE ID를 넣은 1차 호출은 403 `This project does not have the access to Custom Search JSON API`로 실패했으므로, Google Cloud 프로젝트에서 Custom Search JSON API 사용 설정/권한을 먼저 해결해야 한다.

공식 Naver 수집 요약:

| 항목 | 값 |
|---|---:|
| 수집 작가 수 | 80 |
| provider 수 | 3 |
| 요청 수 | 1,200 |
| 요청 성공률 | 0.8983 |
| 작가 단위 성공률 | 0.9750 |
| 작가당 평균 결과 수 | 64.2125 |
| 작가당 평균 고유 도메인 수 | 20.6125 |
| 미술 문맥 비율 평균 | 0.8910 |
| 전시 문맥 비율 평균 | 0.5381 |
| 이름 매칭 비율 평균 | 0.7568 |

공식 Naver 소스군 비중:

| 소스군 | 비중 |
|---|---:|
| 갤러리/미술관 | 0.4851 |
| 시장/거래 | 0.1390 |
| 블로그/소셜 | 0.1372 |
| 뉴스 | 0.1304 |
| 일반 미술 정보 | 0.0500 |
| 전시 | 0.0370 |

### 15.2 PP-H23 검색 소스군별 보정

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `h23_gallery_museum_median_cap0.2` | 0.4313 | 0.9285 | 3.1390 | 0.8378 | 전체 최우선 후보 |
| `h23_gallery_museum_median_cap0.1` | 0.4348 | 0.9770 | 3.2196 | 0.8460 | 보수 후보 |
| `h23_exhibition_median_cap0.1` | 0.4452 | 1.0756 | 2.9394 | 0.8733 | p95 방어 후보, 전체 후보 아님 |
| `h23_exhibition_median_cap0.2` | 0.4502 | 1.1382 | 2.7635 | 0.8918 | p95는 강하지만 전체 오차 악화 |
| `h23_social_blog_median_cap0.1` | 0.4521 | 0.9858 | 3.2196 | 0.8484 | MAPE/RMSE 보조 후보, MdAPE 약함 |

해석:

- 공식 Naver API 기준에서는 `source_group_gallery_museum_ratio`가 전체 보정 후보로 가장 강했다.
- 갤러리/미술관 비율 `high` 구간은 validation에서 기준 모델이 낮게 예측하는 경향이 있어 `+0.2` log 보정이 적용됐다.
- 갤러리/미술관 비율 `low` 구간은 기준 모델이 높게 예측하는 경향이 있어 `-0.2` log 보정이 적용됐다.
- 전시 문맥 보정은 p95_APE를 크게 낮추지만 MdAPE, MAPE, RMSE가 악화되어 전체 가격점 보정에는 쓰지 않는다.

### 15.3 PP-H24 최근성 기반 보정

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| recent cap0.1 계열 | 0.4635 | 1.1218 | 3.5388 | 0.8667 | 전체 악화 |
| recent cap0.2 계열 | 0.4643 | 1.1877 | 3.5388 | 0.8794 | 전체 악화 |

해석:

- 공식 Naver API에서도 최근성 피처는 단독 보정 후보로 약하다.
- 최근 결과 비율은 최종 가격점 보정보다 신뢰도 표시, 수동 검수 우선순위, 신규 작가 업데이트 알림에 쓰는 쪽이 적합하다.

### 15.4 PP-H26 위험 segment fallback

전체 test 기준:

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| q10/q90 blend 계열 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 공식 H12B 기준 적용 대상 없음 |
| `h26_risk_qwidth_action_median_cap0.1` | 0.4474 | 1.0673 | 3.4348 | 0.8571 | 전체 후보 제외 |
| `h26_risk_qwidth_action_median_cap0.2` | 0.4474 | 1.0673 | 3.4348 | 0.8571 | 전체 후보 제외 |

해석:

- 공식 Naver API 기반 H12B에서는 `confidence_only_or_manual_review` 구간이 0건으로 정리됐다.
- 그 결과 q10/q90 fallback은 전체 test에서 기준 모델과 동일한 값이 됐다.
- H26은 현재 공식 Naver 기준에서는 가격점 보정 후보가 아니라, 향후 수동 검수나 Google 교차검증에서 위험 구간이 다시 생길 때 쓰는 정책 후보로 남긴다.

### 15.5 다음 검증 우선순위

| 우선순위 | 작업 | 이유 |
|---:|---|---|
| 1 | `PP-H23 gallery_museum` bootstrap 안정성 검증 | PP-H27에서 완료 |
| 2 | H25 수동 검수 우선순위 기반 검수 | 검색 누락/고오차 작가 보완 |
| 3 | 공식 API 기준 H12B/H23/H27 재실행 자동화 | 수동 검수 반영 후 반복 검증 필요 |
| 4 | Google Cloud Custom Search JSON API 접근 권한 해결 후 PP-H21 실행 | 글로벌 노출 피처 검증 |
| 5 | PP-H22 provider agreement 검증 | 서비스 운영용 외부 신호 안정성 판단 |

### 15.6 산출물

| 산출물 | 경로 |
|---|---|
| PP-H11 공식 Naver 수집 결과 | `experiments/track6/PP-H11_operational_search_feature_standardization/outputs/artist_search_result_standardized.csv` |
| PP-H20~H26 실행 리포트 | `experiments/track6/PP-H20_H26_search_feature_expansion/reports/result_report.html` |
| PP-H20~H26 metrics | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/metrics.csv` |
| API preflight | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/api_preflight.csv` |
| 수동 검수 우선순위 | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/h25_manual_review_priority.csv` |
| 실행 요약 문서 | `docs/track6/experiments/pp_h20_h26_search_feature_expansion_summary.md` |

## 16. PP-H27 H23/H26 안정성 검증 결과 - Naver 공식 API 단독 기준 기록

### 16.1 실행 내용

| 항목 | 내용 |
|---|---|
| 목적 | 공식 Naver API 기반 H23/H26 후보가 test 단일 결과에서만 좋아진 것인지 검증 |
| 기준 모델 | `PP-Y2 lgbq_search_all_external_interaction` |
| 검증 후보 | H23 갤러리/미술관 보정 2개, H23 전시 보정 2개, H23 블로그/소셜 보정 1개, H26 위험 fallback 3개 |
| bootstrap | row 800회, artist 800회 |
| slice | 전체 test, H12B action 구간 |

### 16.2 전체 test 기준 결정

| 후보 | MdAPE | MAPE | p95_APE | row 안정성 | artist 안정성 | 결정 |
|---|---:|---:|---:|---|---|---|
| `h23_gallery_museum_median_cap0.2` | 0.4313 | 0.9285 | 3.1390 | MdAPE/MAPE/p95/RMSE 안정 | MAPE/p95 개선확률 높음 | 전체 최우선 후보 |
| `h23_gallery_museum_median_cap0.1` | 0.4348 | 0.9770 | 3.2196 | 전반 안정 | cap0.2보다 보수적 | 보수 후보 유지 |
| `h23_exhibition_median_cap0.1` | 0.4452 | 1.0756 | 2.9394 | p95만 안정 | 전체 오차 악화 | p95 방어 참고 |
| `h23_exhibition_median_cap0.2` | 0.4502 | 1.1382 | 2.7635 | p95만 안정 | 전체 오차 악화 | 전체 후보 제외 |
| `h23_social_blog_median_cap0.1` | 0.4521 | 0.9858 | 3.2196 | MAPE/RMSE 안정, MdAPE 악화 | 보조 후보 | 단독 적용 제외 |

해석:

- 전체 Cold 보정에는 `source_group_gallery_museum_ratio` 기반 보정이 가장 타당하다.
- 전시 문맥 보정은 p95_APE 방어에는 좋지만 평균/중앙 오차가 악화되어 전체 가격점 보정에는 쓰지 않는다.

### 16.3 위험 구간 기준 결정

공식 Naver API 기반 H12B에서는 `confidence_only_or_manual_review` 위험 구간이 test에서 비어 있다. 따라서 H26 q10/q90 fallback은 이번 실행에서는 기준 모델과 동일한 예측을 냈다.

| 후보 | MdAPE | MAPE | p95_APE | row 안정성 | artist 안정성 | 결정 |
|---|---:|---:|---:|---|---|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 기준선 | 기준선 | 기준선 |
| `h26_q10_blend0.5` | 0.4421 | 1.0484 | 3.3537 | 기준 모델과 동일 | 기준 모델과 동일 | 현재 보류 |
| `h26_qwidth_action_cap0.1` | 0.4474 | 1.0673 | 3.4348 | 악화 | 악화 | 전체 후보 제외 |

해석:

- H26은 공식 Naver 기준으로 현재 채택하지 않는다.
- 다만 Google provider agreement나 수동 검수 이후 위험 구간이 다시 정의되면, H26은 위험 구간 전용 fallback으로 재검증한다.

### 16.4 H 실험 현재 완료/미완료 상태

| 구분 | 상태 |
|---|---|
| 현재 보유 데이터 기반 H 실험 | `PP-H7~H19`, `PP-H20`, `PP-H23~H27` 완료 |
| 공식 Naver API 기반 H 실험 | `PP-H20` 완료 |
| Google CSE 기반 H 실험 | `PP-H21` blocked, Custom Search JSON API 접근 권한 필요 |
| Provider agreement | `PP-H22` blocked, 성공한 Google provider 필요 |
| 수동 검수 기반 재실행 | H25 검수 결과가 채워진 뒤 가능 |

현재 결론:

- Naver 공식 API 기준으로 가능한 H 실험과 안정성 검증은 완료했다.
- Google 수집 및 provider agreement는 아직 Google Cloud API 접근 권한/data dependency로 blocked 상태다.
- 최종 운영 후보는 `H23 gallery_museum 보정 + H14 conformal80 범위 표시` 조합으로 검토한다.

### 16.5 PP-H27 산출물

| 산출물 | 경로 |
|---|---|
| PP-H27 HTML 리포트 | `experiments/track6/PP-H27_search_candidate_stability_validation/reports/result_report.html` |
| PP-H27 metrics | `experiments/track6/PP-H27_search_candidate_stability_validation/outputs/metrics.csv` |
| PP-H27 bootstrap summary | `experiments/track6/PP-H27_search_candidate_stability_validation/outputs/bootstrap_summary.csv` |
| PP-H27 요약 문서 | `docs/track6/experiments/pp_h27_search_candidate_stability_validation_summary.md` |

## 17. 최신 PP-H21 Python Provider 반영 결과

### 17.1 왜 추가했는가

Naver 공식 API는 국내 작가/국내 문맥에는 강하지만, 한 provider에만 의존하면 검색 결과가 Naver 생태계에 편향될 수 있다. Google Custom Search JSON API는 접근 권한 문제로 blocked 상태였고, CSE 공개 URL은 브라우저 화면용이라 자동 수집에는 부적합했다. 따라서 무인 수집과 반복 실험이 가능한 Python 검색 라이브러리 provider를 추가했다.

### 17.2 CSE 공개 URL 확인 결과

| 항목 | 결과 |
|---|---|
| 테스트 대상 | Google CSE 공개 URL |
| 파이썬 요청 결과 | HTTP 200 |
| 구조화 결과 | 제목/링크/스니펫 없음 |
| 원인 | 검색 결과가 JavaScript로 브라우저에서 렌더링됨 |
| 판단 | 수동 확인용은 가능, 자동 피처 수집 provider로는 미적용 |

### 17.3 Python Provider 수집 결과

| 항목 | 값 |
|---|---:|
| 수집 작가 수 | 80 |
| provider 수 | 5 |
| 요청 수 | 2,000 |
| 요청 성공률 | 0.9390 |
| 작가 단위 성공률 | 1.0000 |
| 작가당 평균 결과 수 | 114.2125 |
| 작가당 평균 고유 도메인 수 | 38.7250 |
| 평균 품질 점수 | 0.3784 |

Provider 구성:

| provider | 역할 |
|---|---|
| `naver_api_blog` | 국내 블로그 노출 |
| `naver_api_news` | 국내 뉴스 노출 |
| `naver_api_webkr` | 국내 웹문서 노출 |
| `python_ddg` | 일반 글로벌 검색 |
| `python_ddg_art_context` | artist/gallery/exhibition/auction/artwork 문맥을 추가한 글로벌 검색 |

해석:

- Python provider는 결과 수와 도메인 다양성을 크게 늘렸다.
- 반대로 `other` 문맥도 늘어나 전체 품질 점수는 낮아졌다.
- 따라서 Python provider 결과는 전체 품질 점수에 단순 합산하기보다 source group별 보정과 provider agreement 검증에 분리해서 사용한다.

### 17.4 최신 H23 후보 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `h23_news_median_cap0.2` | 0.4253 | 0.9534 | 3.1542 | 0.8338 | MdAPE 최우선 후보 |
| `h23_news_median_cap0.1` | 0.4283 | 0.9890 | 3.2196 | 0.8440 | 보수적 news 후보 |
| `h23_gallery_museum_median_cap0.2` | 0.4313 | 0.9285 | 3.1390 | 0.8378 | 운영 안정형 후보 |
| `h23_social_blog_median_cap0.2` | 0.4344 | 0.9270 | 3.1390 | 0.8400 | MAPE/p95 보조 후보 |

### 17.5 최신 H27 안정성 판단

| 후보 | 기준 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | RMSE 개선확률 | 판단 |
|---|---|---:|---:|---:|---:|---|
| `h23_news_cap0.2` | row | 0.9988 | 1.0000 | 0.9438 | 1.0000 | row 기준 매우 안정 |
| `h23_news_cap0.2` | artist | 0.8938 | 0.8950 | 0.7075 | 0.9138 | MdAPE/RMSE 중심 유효 |
| `h23_gallery_museum_cap0.2` | row | 0.9813 | 1.0000 | 1.0000 | 1.0000 | MAPE/p95/RMSE 매우 안정 |
| `h23_gallery_museum_cap0.2` | artist | 0.7100 | 0.9925 | 1.0000 | 0.8338 | 작가 기준 p95 안정성 강함 |

### 17.6 최신 결정

| 용도 | 후보 | 판단 |
|---|---|---|
| MdAPE 우선 후보 | `h23_news_median_cap0.2` | 채택 후보 |
| 운영 안정형 후보 | `h23_gallery_museum_median_cap0.2` | 채택 후보 |
| MAPE/p95 보조 후보 | `h23_social_blog_median_cap0.2` | 단독 적용보다 조건부/앙상블 후보 |
| 수동 확인용 | Google CSE 공개 URL | 자동 수집 제외 |
| 다음 실험 | Naver x Python provider agreement, news x gallery 조건부 결합 | 외부 검색 신호의 운영 안정성 확인 |

### 17.7 최신 산출물

| 산출물 | 경로 |
|---|---|
| H20~H26 최신 요약 | `docs/track6/experiments/pp_h20_h26_search_feature_expansion_summary.md` |
| H27 최신 안정성 요약 | `docs/track6/experiments/pp_h27_search_candidate_stability_validation_summary.md` |
| H11 최신 snapshot | `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv` |
| H20~H26 HTML 리포트 | `experiments/track6/PP-H20_H26_search_feature_expansion/reports/result_report.html` |
| H27 HTML 리포트 | `experiments/track6/PP-H27_search_candidate_stability_validation/reports/result_report.html` |

## 18. Warm 기준 추가 검색 피처 보정 실험

### 18.1 왜 추가했는가

기존 H 실험은 Cold 중심으로 설계되어 있었다. 그러나 서비스 후보는 Warm/Cold가 함께 운영되어야 하므로, 외부 검색 피처가 Warm에서도 추가 보정 가치가 있는지 별도로 확인해야 한다.

기존 latest 검색 스냅샷은 Cold 작가 중심 80명 기준이라 Warm 평가셋 커버리지가 낮았다. 이 상태에서 Warm 보정을 진행하면 검색 피처의 효과가 아니라 검색 피처가 붙은 일부 작가만 보는 표본 편향이 될 수 있다.

따라서 H11 수집 스크립트에 Warm 작가 선택 옵션을 추가하고, Warm validation/test 작가 중심으로 검색 피처를 추가 수집한 뒤 PP-H29를 실행했다.

### 18.2 H11 Warm 수집 보완 내용

| 항목 | 내용 |
|---|---|
| 추가 옵션 | `--artist-scope warm` |
| 추가 선택 기준 | `eval_frequency`, `test_frequency` |
| 목적 | Warm validation/test에 많이 등장하는 작가를 우선 수집 |
| 병합 방식 | 기존 latest 검색 결과를 덮어쓰지 않고 병합 |
| 최종 latest snapshot 작가 수 | 428명 |

커버리지 변화:

| split | rows | unique artist | covered rows | row coverage | covered unique artist |
|---|---:|---:|---:|---:|---:|
| Warm validation | 519 | 177 | 489 | 0.9422 | 162 |
| Warm test | 607 | 205 | 607 | 1.0000 | 205 |
| Cold validation | 2,753 | 168 | 1,381 | 0.5016 | 9 |
| Cold test | 3,099 | 188 | 1,192 | 0.3846 | 10 |

해석:

- Warm validation/test는 검색 피처 보정 실험을 해석 가능한 수준으로 커버됐다.
- Cold 쪽 최신 성능 검증은 기존 H20~H27 산출물을 기준으로 유지한다.
- Warm 추가 수집은 Cold 결과를 대체하지 않고, Warm 후처리 검증을 가능하게 하기 위한 보완이다.

### 18.3 PP-H29 실험 방식

| 항목 | 내용 |
|---|---|
| 실험 ID | `PP-H29` |
| 기준 예측값 | `PP-V8_warm_deployment_simplification`의 Warm 후보 |
| 기준 후보 | `deployment_single_mdape`, `compact_blend_mdape`, `compact_blend_mape_guarded` |
| 보정 학습 데이터 | Warm validation |
| 보정 적용 데이터 | Warm validation/test |
| 보정값 | `actual_log - pred_log`의 구간별 중앙값 |
| 보정 cap | log 가격 기준 `±0.05`, `±0.10`, `±0.15` |
| 사용 피처 | 검색 품질, 작가명 일치율, 동명이인 위험, 갤러리/미술관 비중, 뉴스 비중, 소셜/블로그 비중, 시장/경매 비중, provider 커버리지 |

핵심 원칙:

- test 잔차는 보정값 계산에 사용하지 않는다.
- 검색 피처가 없는 validation 행은 `no_search`로 분리하고 보정값을 0으로 둔다.
- 이미 Warm V8 후보가 강한 상태이므로 큰 이동보다 작은 잔차 보정만 허용한다.

### 18.4 PP-H29 결과

기준 후보 test 성능:

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| `baseline__v8_single_mdape` | 0.1621 | 0.3044 | 1.0335 | 0.4220 | MdAPE 기준 단일 후보 |
| `baseline__v8_compact_mape` | 0.1632 | 0.2816 | 0.9311 | 0.4028 | MAPE 방어 후보 |
| `baseline__v8_compact_mdape` | 0.1635 | 0.2868 | 0.9190 | 0.4067 | p95 방어 후보 |

상위 test 후보:

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 해석 |
|---|---:|---:|---:|---:|---|
| `h29_v8_compact_mape_gallery_median_cap0p05` | 0.1617 | 0.2809 | 0.9309 | 0.4028 | 가장 균형적인 소폭 개선 |
| `h29_v8_compact_mape_market_median_cap0p05` | 0.1617 | 0.2809 | 0.9309 | 0.4028 | gallery와 같은 수준의 소폭 개선 |
| `h29_v8_compact_mape_name_match_median_cap0p05` | 0.1617 | 0.2809 | 0.9309 | 0.4028 | 작가명 일치 구간 기준 소폭 개선 |
| `h29_v8_compact_mape_provider_cov_median_cap0p05` | 0.1617 | 0.2809 | 0.9309 | 0.4028 | provider 커버리지 기준 소폭 개선 |
| `h29_v8_compact_mdape_news_median_cap0p05` | 0.1628 | 0.2819 | 0.8850 | 0.4067 | p95 방어 측면에서 추가 후보 |

개선 폭:

| 기준 | 기준값 | H29 최상위 | 개선 |
|---|---:|---:|---:|
| MdAPE | 0.1621 | 0.1617 | 0.0004 개선 |
| MAPE | 0.2816 | 0.2809 | 0.0007 개선 |
| p95_APE | 0.9311 | 0.9309 | 0.0002 개선 |

### 18.5 PP-H29 해석

- Warm에서는 외부 검색 피처 기반 보정이 큰 폭의 개선을 만들지는 않았다.
- 이유는 Warm 모델이 이미 작가 기준 이력, 작품 크기, 작품 조건 정보를 많이 학습하고 있어 외부 검색 신호가 새로 설명할 잔차가 작기 때문이다.
- 그래도 `compact_blend_mape_guarded` 위에 검색 피처 기반 작은 보정을 얹으면 MdAPE/MAPE/p95가 모두 소폭 개선됐다.
- 따라서 Warm의 외부 검색 피처는 주력 모델을 바꾸는 용도보다, 이미 강한 Warm 후보의 잔차를 미세 조정하는 보조 후처리로 보는 것이 맞다.
- p95를 더 줄이고 싶을 때는 `compact_mdape + news 보정` 후보도 별도 검토할 수 있다.

### 18.6 PP-H29 산출물

| 산출물 | 경로 |
|---|---|
| H29 HTML 리포트 | `experiments/track6/PP-H29_warm_search_feature_calibration/reports/result_report.html` |
| H29 metrics | `experiments/track6/PP-H29_warm_search_feature_calibration/outputs/metrics.csv` |
| H29 predictions | `experiments/track6/PP-H29_warm_search_feature_calibration/outputs/candidate_predictions.csv` |
| H29 correction maps | `experiments/track6/PP-H29_warm_search_feature_calibration/outputs/correction_maps.csv` |
| H29 coverage | `experiments/track6/PP-H29_warm_search_feature_calibration/outputs/coverage.csv` |
