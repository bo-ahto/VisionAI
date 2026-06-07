# PP-H27 H23/H26 검색 보정 후보 안정성 검증 요약

- 실행일: 2026-06-03
- 기준 모델: `PP-Y2 lgbq_search_all_external_interaction`
- 목적: Naver 공식 API + Python 검색 라이브러리 기반 검색 보정 후보가 단일 test 결과에서만 좋아진 것인지, 아니면 표본을 바꿔도 반복적으로 개선되는지 확인한다.
- 결론:
  - MdAPE 최우선 후보는 `h23_news_median_cap0.2`다.
  - 운영 안정형 후보는 `h23_gallery_museum_median_cap0.2`다.
  - `h23_exhibition` 계열은 p95_APE 방어에는 강하지만 MdAPE/MAPE/RMSE가 악화되어 전체 가격점 보정 후보로는 제외한다.

## 1. 검증 방식

| 항목 | 내용 |
|---|---|
| 기준 모델 | `PP-Y2 lgbq_search_all_external_interaction` |
| 검증 후보 | H23 갤러리/미술관, 뉴스, 전시, 블로그/소셜 보정 후보 + H26 위험 fallback |
| row bootstrap | 작품 row 기준 800회 |
| artist bootstrap | 작가 기준 800회 |
| 검증 slice | 전체 test, H12B action 구간 |
| delta 해석 | `기준 모델 점수 - 후보 점수`, 오차 지표에서는 양수일수록 좋음 |

## 2. Test 전체 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `h23_news_median_cap0.2` | 0.4253 | 0.9534 | 3.1542 | 0.8338 | MdAPE 최우선 후보 |
| `h23_news_median_cap0.1` | 0.4283 | 0.9890 | 3.2196 | 0.8440 | 보수적 news 후보 |
| `h23_gallery_museum_median_cap0.2` | 0.4313 | 0.9285 | 3.1390 | 0.8378 | 운영 안정형 후보 |
| `h23_social_blog_median_cap0.2` | 0.4344 | 0.9270 | 3.1390 | 0.8400 | MAPE/p95 보조 후보 |
| `h23_gallery_museum_median_cap0.1` | 0.4348 | 0.9770 | 3.2196 | 0.8460 | 보수 후보 |
| `h26_risk_qwidth_action_median_cap0.1` | 0.4352 | 1.0094 | 3.1821 | 0.8571 | H23보다 약함 |
| `h23_exhibition_median_cap0.1` | 0.4452 | 1.0756 | 2.9394 | 0.8733 | p95 방어 후보, 전체 후보 제외 |
| `h23_exhibition_median_cap0.2` | 0.4502 | 1.1382 | 2.7635 | 0.8918 | p95만 개선, 전체 후보 제외 |

## 3. 전체 test bootstrap 핵심 결과

개선확률은 bootstrap 표본에서 후보가 기준 모델보다 좋아진 비율이다.

| 후보 | 기준 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | RMSE 개선확률 | 판단 |
|---|---|---:|---:|---:|---:|---|
| `h23_news_cap0.2` | row | 0.9988 | 1.0000 | 0.9438 | 1.0000 | row 기준 매우 안정 |
| `h23_news_cap0.2` | artist | 0.8938 | 0.8950 | 0.7075 | 0.9138 | MdAPE/RMSE 중심 유효 |
| `h23_gallery_museum_cap0.2` | row | 0.9813 | 1.0000 | 1.0000 | 1.0000 | MAPE/p95/RMSE 매우 안정 |
| `h23_gallery_museum_cap0.2` | artist | 0.7100 | 0.9925 | 1.0000 | 0.8338 | 작가 기준 p95 안정성 강함 |
| `h23_social_blog_cap0.2` | row | 0.9063 | 1.0000 | 1.0000 | 1.0000 | MAPE/p95 보조 후보 |
| `h23_social_blog_cap0.2` | artist | 0.6788 | 0.9925 | 1.0000 | 0.7763 | MdAPE 안정성은 약함 |
| `h23_news_cap0.1` | row | 0.9938 | 1.0000 | 0.9638 | 1.0000 | 보수 후보 |
| `h23_news_cap0.1` | artist | 0.9038 | 0.9700 | 0.7863 | 0.9313 | 보수 후보 |

## 4. 해석

- Python 검색 라이브러리 provider를 추가하면서 `news` source group의 역할이 커졌다.
- `news`는 작가 활동, 전시/거래 노출, 최근 이슈가 반영되기 쉬워 중앙 오차(MdAPE)를 줄이는 데 유리했다.
- 다만 작가 단위 p95 안정성은 `gallery_museum`이 더 강하다. 이는 갤러리/미술관 맥락이 검색량 노이즈보다 미술계에서 확인되는 작가 신뢰도를 더 잘 나타내기 때문이다.
- `social_blog`는 MAPE와 p95에는 좋지만 MdAPE 개선 확률이 상대적으로 약해 단독 대표 후보로 두기 어렵다.
- `exhibition`은 큰 오차 꼬리(p95)를 줄이지만 평균/중앙 오차가 악화된다. 전체 가격점 보정에는 쓰지 않고, 범위 표시나 tail-risk 정책에서만 참고한다.

## 5. 결정

| 용도 | 후보 | 판단 |
|---|---|---|
| MdAPE 우선 후보 | `h23_news_median_cap0.2` | 채택 후보 |
| 운영 안정형 후보 | `h23_gallery_museum_median_cap0.2` | 채택 후보 |
| 보수 후보 | `h23_news_median_cap0.1`, `h23_gallery_museum_median_cap0.1` | 비교 유지 |
| MAPE/p95 보조 후보 | `h23_social_blog_median_cap0.2` | 단독 적용보다 앙상블/조건부 후보 |
| p95 방어 참고 후보 | `h23_exhibition_median_cap0.1`, `h23_exhibition_median_cap0.2` | 전체 적용 제외, tail 정책 참고 |
| 위험 구간 fallback | H26 계열 | H23보다 약해 현재 보조 정책으로 보류 |

## 6. Google CSE 공개 URL 판단

- 공개 URL은 브라우저에서 검색 UI를 확인하는 용도로는 사용할 수 있다.
- 파이썬 `requests`로 `https://cse.google.com/cse?cx=...&q=...`를 호출하면 HTTP 200은 반환되지만, HTML 안에 검색 결과 링크가 없고 JavaScript 로더만 내려온다.
- 따라서 공개 URL을 자동 수집 provider로 쓰려면 브라우저 자동화가 필요하다.
- 브라우저 자동화는 느리고, 재현성/차단/화면 구조 변경 위험이 있어 운영형 피처 수집에는 부적합하다.
- 결론: Google CSE 공개 URL은 수동 확인용으로만 두고, 모델 실험 provider에는 반영하지 않는다.

## 7. 남은 H 실험

- `PP-H22`: Naver x Python provider agreement score 계산 완료
- H25 상위 검색 누락/고오차 작가 수동 검수
- `h23_news_median_cap0.2`와 `h23_gallery_museum_median_cap0.2`의 조건부 결합 실험
- Google JSON API 접근 권한이 해결될 경우 별도 `PP-H21-G`로 재검증

### 7.1 PP-H22 실행 결과

| 항목 | 결과 | 판단 |
|---|---:|---|
| Naver 공식 API 대상 작가 | 80명 | 공식 API 수집 완료 |
| Python provider 대상 작가 | 428명 | 커버리지는 넓음 |
| provider agreement medium | 9명 | 제한적 사용 가능 |
| provider agreement low | 69명 | 직접 점 예측 피처 사용 부적합 |

해석:

- Python provider는 커버리지는 넓지만 일반 웹 결과가 많이 섞여 Naver 공식 API와 source group 일치도가 낮았다.
- agreement score는 가격을 직접 보정하는 피처보다, 동명이인/무관 결과 위험을 표시하고 수동 검수 우선순위를 잡는 데 더 적합하다.
- 따라서 H 계열의 남은 핵심 작업은 자동 모델 실험보다 H25 수동 검수와 운영 데이터 품질 관리다.

## 8. 산출물

| 산출물 | 경로 |
|---|---|
| HTML 리포트 | `experiments/track6/PP-H27_search_candidate_stability_validation/reports/result_report.html` |
| metrics | `experiments/track6/PP-H27_search_candidate_stability_validation/outputs/metrics.csv` |
| bootstrap summary | `experiments/track6/PP-H27_search_candidate_stability_validation/outputs/bootstrap_summary.csv` |
| 실행 스크립트 | `scripts/track6/run_pp_h27_search_candidate_stability_validation.py` |
| PP-H22 HTML 리포트 | `experiments/track6/PP-H22_provider_agreement_stability/reports/result_report.html` |
| PP-H22 artist agreement | `experiments/track6/PP-H22_provider_agreement_stability/outputs/provider_agreement_by_artist.csv` |
