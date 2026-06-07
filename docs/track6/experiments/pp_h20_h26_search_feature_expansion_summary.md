# PP-H20~H26 검색 피처 보완 실행 요약

- 실행일: 2026-06-03
- 기준 모델: `PP-Y2 lgbq_search_all_external_interaction`
- 목적: 외부 검색 결과를 서비스 운영에 쓸 수 있는 표준 피처로 만들고, 검색 피처가 Cold 가격 예측 보정에 실제로 도움이 되는지 검증한다.
- 최신 결론:
  - 공식 Naver Search API `blog/news/webkr` 수집은 완료됐다.
  - Python 검색 라이브러리 기반 `python_ddg`, `python_ddg_art_context` provider를 추가 수집했다.
  - Google CSE 공개 URL은 브라우저 화면용으로는 확인 가능하지만, 파이썬 `requests` 기준으로 제목/링크/스니펫이 구조화되어 내려오지 않아 자동 피처 수집 provider로는 적용하지 않는다.
  - 점수 기준으로는 `h23_news_median_cap0.2`가 MdAPE 최상위 후보이고, 운영 안정성 기준으로는 `h23_gallery_museum_median_cap0.2`가 여전히 강하다.

## 1. API/Provider 상태

| 실험 | 상태 | 필요한 조건 | 다음 작업 |
|---|---|---|---|
| `PP-H20` Naver 공식 API 다중 소스 수집 | `completed_latest_snapshot` | Naver Search API 인증값 | 완료된 최신 snapshot 사용 |
| `PP-H21` 보조 글로벌 검색 수집 | `completed_python_latest_snapshot` | `python_ddg`, `python_ddg_art_context` | 완료된 Python 검색 snapshot 사용 |
| `PP-H21-G` Google Custom Search JSON API | `blocked_api_access` | Google Cloud 프로젝트의 Custom Search JSON API 접근 권한 | 접근 권한 해결 전까지 보류 |
| `PP-H21-CSE-PUBLIC` Google CSE 공개 URL | `manual_only_not_provider` | 브라우저 화면 렌더링 | 자동 수집에는 미적용 |
| `PP-H22` Provider 일치도 검증 | `ready` | Naver + Python provider 결과 | Naver x Python 검색 라이브러리 agreement score 계산 |

해석:

- Naver 공식 API 인증값은 환경변수로만 주입했다. 인증값은 코드나 문서에 저장하지 않는다.
- Google Custom Search JSON API는 키와 CSE ID를 넣어 호출했지만 `This project does not have the access to Custom Search JSON API` 403 응답을 받았다.
- Google CSE 공개 URL은 `https://cse.google.com/cse?cx=...&q=...` 형태로 열리지만, 파이썬에서 받은 HTML에는 검색 결과 링크가 없고 JavaScript 렌더링 코드만 있었다.
- 따라서 Google CSE 공개 URL은 수동 확인용으로만 두고, 실험 provider는 `Naver 공식 API + Python 검색 라이브러리` 조합으로 진행한다.

## 2. PP-H11 최신 수집 결과

| 항목 | 값 |
|---|---:|
| 수집 작가 수 | 80 |
| provider 수 | 5 (`naver_api_blog`, `naver_api_news`, `naver_api_webkr`, `python_ddg`, `python_ddg_art_context`) |
| 요청 수 | 2,000 |
| 요청 성공률 | 0.9390 |
| 요청 에러율 | 0.0000 |
| 작가 단위 성공률 | 1.0000 |
| 작가당 평균 결과 수 | 114.2125 |
| 작가당 평균 고유 도메인 수 | 38.7250 |
| 평균 품질 점수 | 0.3784 |
| 미술 문맥 비율 평균 | 0.5604 |
| 전시 문맥 비율 평균 | 0.3150 |
| 시장 문맥 비율 평균 | 0.0770 |
| 이름 매칭 비율 평균 | 0.5468 |

Provider별 반환률:

| provider | 결과 row 수 | 성공 row 수 | 성공률 |
|---|---:|---:|---:|
| `naver_api_blog` | 1,760 | 1,723 | 0.9790 |
| `naver_api_news` | 1,599 | 1,530 | 0.9568 |
| `naver_api_webkr` | 1,900 | 1,884 | 0.9916 |
| `python_ddg` | 2,000 | 2,000 | 1.0000 |
| `python_ddg_art_context` | 2,000 | 2,000 | 1.0000 |

소스군 분포:

| 소스군 | 비중 |
|---|---:|
| 기타 | 0.3194 |
| 갤러리/미술관 | 0.2790 |
| 블로그/소셜 | 0.1386 |
| 뉴스 | 0.0995 |
| 시장/거래 | 0.0812 |
| 일반 미술 정보 | 0.0596 |
| 전시 | 0.0228 |

해석:

- Python provider는 검색 성공률과 고유 도메인 수를 크게 늘렸다.
- 다만 전역 웹 검색 특성상 `other` 문맥도 함께 늘어나 평균 품질 점수와 미술 문맥 비율은 Naver 단독보다 낮아졌다.
- 따라서 Python 검색 결과는 전체 품질 점수에 단순 합산하기보다, source group별 보정이나 provider 일치도 검증에 분리해서 쓰는 것이 적합하다.

## 3. 현재 데이터로 실행한 실험

| 실험 | 내용 | 실행 여부 |
|---|---|---|
| `PP-H23` 검색 소스군별 보정 | H11 source group별 validation median residual 보정 | 실행 완료 |
| `PP-H24` 최근성 기반 보정 | 최근 검색 결과 count/ratio 기반 보정 | 실행 완료 |
| `PP-H25` 수동 검수 우선순위 생성 | H12B 라벨 + validation 오차 + 검색 소스 결합 | 실행 완료 |
| `PP-H26` 위험 segment fallback | H12/H12B action 구간 전용 보정 | 실행 완료 |

## 4. PP-H23 검색 소스군별 보정 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `h23_news_median_cap0.2` | 0.4253 | 0.9534 | 3.1542 | 0.8338 | MdAPE 최우선 후보 |
| `h23_news_median_cap0.1` | 0.4283 | 0.9890 | 3.2196 | 0.8440 | 보수적 news 후보 |
| `h23_gallery_museum_median_cap0.2` | 0.4313 | 0.9285 | 3.1390 | 0.8378 | 운영 안정형 후보 |
| `h23_social_blog_median_cap0.2` | 0.4344 | 0.9270 | 3.1390 | 0.8400 | MAPE/p95 보조 후보 |
| `h23_gallery_museum_median_cap0.1` | 0.4348 | 0.9770 | 3.2196 | 0.8460 | 보수 후보 |
| `h23_exhibition_median_cap0.1` | 0.4452 | 1.0756 | 2.9394 | 0.8733 | p95 방어 참고, 전체 후보 제외 |
| `h23_exhibition_median_cap0.2` | 0.4502 | 1.1382 | 2.7635 | 0.8918 | p95는 강하지만 전체 오차 악화 |

해석:

- Python provider를 추가하자 `news` source group이 MdAPE 관점에서 가장 강한 후보로 올라왔다.
- `news`는 가격 변동성이나 작가 활동 노출을 빠르게 반영하는 신호로 볼 수 있어 중앙 오차 개선에 유리했다.
- `gallery_museum`은 MdAPE 1위는 아니지만 MAPE, p95_APE, RMSE_log가 모두 안정적으로 개선되어 운영 보정 후보로 여전히 타당하다.
- `exhibition`은 큰 오차 꼬리(p95)를 줄이지만 MdAPE/MAPE/RMSE가 악화되어 전체 가격점 보정에는 쓰지 않는다.

## 5. PP-H24 최근성 기반 보정 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `h24_search_recent_result_ratio_median_cap0.2` | 0.4367 | 0.9571 | 3.1542 | 0.8506 | 개선은 있으나 H23보다 약함 |
| `h24_search_recent_result_ratio_median_cap0.1` | 0.4349 | 0.9919 | 3.2196 | 0.8523 | MdAPE 일부 개선, H23보다 약함 |
| `h24_search_recent_result_count_median_cap0.1` | 0.4579 | 1.0907 | 3.2196 | 0.8691 | 전체 악화 |
| `h24_search_recent_result_count_median_cap0.2` | 0.4666 | 1.1574 | 3.2196 | 0.8840 | 전체 악화 |

해석:

- 최근성 ratio는 일부 개선 신호가 있으나 H23 source group 보정보다 약하다.
- 최근성 count는 검색량 자체의 노이즈가 커서 가격점 보정 후보로 부적합하다.
- 최근성은 신뢰도 표시, 수동 검수 우선순위, 신규 작가 업데이트 알림에 쓰는 쪽이 더 적합하다.

## 6. PP-H26 위험 segment fallback 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `h26_risk_action_median_cap0.1` | 0.4352 | 1.0094 | 3.1821 | 0.8571 | MdAPE/MAPE/p95 개선, RMSE 유지 수준 |
| `h26_risk_qwidth_action_median_cap0.1` | 0.4352 | 1.0094 | 3.1821 | 0.8571 | 위와 동일 |
| q10/q90 blend 계열 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준 모델과 동일 |

해석:

- H26은 이전 Naver 단독 기준보다 개선됐지만, H23의 `news`/`gallery_museum` 후보보다 약하다.
- 위험 구간 fallback은 전체 적용 후보가 아니라, H12/H12B action 기반의 보수적 보조 정책으로 남긴다.

## 7. 후속 판단

| 우선순위 | 작업 | 이유 |
|---:|---|---|
| 1 | `h23_news_median_cap0.2` 안정성 검증 | MdAPE 최상위 후보 검증 |
| 2 | `h23_gallery_museum_median_cap0.2` 안정성 검증 | 운영 안정형 후보 검증 |
| 3 | Naver x Python provider agreement score 계산 | 외부 검색 신호가 provider 간 일관적인지 확인 |
| 4 | H25 상위 작가 수동 검수 | 검색 누락/고오차 작가 보완 |
| 5 | Google JSON API 접근 권한이 해결될 경우 별도 PP-H21-G로 재검증 | Google CSE 공개 URL은 자동 수집 제외 |

현재 결정:

- MdAPE 우선 후보: `h23_news_median_cap0.2`
- 운영 안정형 후보: `h23_gallery_museum_median_cap0.2`
- MAPE/p95 보조 후보: `h23_social_blog_median_cap0.2`
- p95 방어 참고 후보: `h23_exhibition_median_cap0.1` 또는 `h23_exhibition_median_cap0.2`
- 현재 제외 후보: Google CSE 공개 URL 자동 수집, 최근성 count 단독 보정

## 8. 산출물

| 산출물 | 경로 |
|---|---|
| PP-H11 최신 수집 결과 | `experiments/track6/PP-H11_operational_search_feature_standardization/outputs/artist_search_result_standardized.csv` |
| PP-H11 metrics | `experiments/track6/PP-H11_operational_search_feature_standardization/outputs/metrics.csv` |
| 최신 운영용 검색 snapshot | `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv` |
| PP-H20~H26 실행 리포트 | `experiments/track6/PP-H20_H26_search_feature_expansion/reports/result_report.html` |
| PP-H20~H26 metrics | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/metrics.csv` |
| API preflight | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/api_preflight.csv` |
| source group features | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/source_group_features.csv` |
| correction maps | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/correction_maps.csv` |
| manual review priority | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/h25_manual_review_priority.csv` |
| PP-H27 안정성 리포트 | `experiments/track6/PP-H27_search_candidate_stability_validation/reports/result_report.html` |
| PP-H27 bootstrap summary | `experiments/track6/PP-H27_search_candidate_stability_validation/outputs/bootstrap_summary.csv` |
