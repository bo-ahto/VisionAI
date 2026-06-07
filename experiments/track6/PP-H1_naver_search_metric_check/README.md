# PP-H1 네이버 검색 결과 수 검증

- 목적: 신규 외부 데이터 또는 검색/소셜 지표가 후처리 이후 추가 개선에 필요한지 판단한다.
- 실행 기준: 기존 컬럼 재사용이 아니라 신규/보강 데이터가 있을 때만 모델 성능 실험을 실행한다.
- 현재 상태: `blocked_data_needed`
- 판단: required 신규 외부/search/social columns are not available locally

## 필요한 컬럼

- `naver_blog_count`
- `naver_news_count`
- `naver_web_count`
- `naver_search_success`
- `homonym_risk`

## 현재 누락 컬럼

- `naver_blog_count`
- `naver_news_count`
- `naver_web_count`
- `naver_search_success`
- `homonym_risk`
