# 2026-06-23 월별 Artsy/Saatchi 1차 정리본 - styles 제외 버전

## 정리 기준
1. 가격 데이터가 없는 작품 제거
   - Artsy: price_raw에 숫자가 있거나 price_currency + price_amount가 있는 경우만 유지
   - Saatchi: price_usd가 0보다 큰 경우만 유지
   - Price on request, Sold, Not for sale 계열은 제거
2. 작품 형식 제거
   - sculpture / installation / mixed media / animation / film / video
   - 한국어 표기: 조각, 설치, 믹스미디어, 혼합매체, 애니메이션, 영화, 영상, 비디오, 필름
3. styles 컬럼은 제거 판단에 사용하지 않음
   - Saatchi의 styles는 작품 형식이 아니라 스타일 태그이므로 제외

## 출력
- *_price_only_no_sculpture_installation_mixedmedia_film_no_style_filter.csv: 최종 유지 데이터
- *_removed_no_price.csv: 가격 없음/문의/판매완료로 제거된 데이터
- *_removed_sculpture_installation_mixedmedia_film_no_style_filter.csv: 형식 기준으로 제거된 데이터
- cleaning_summary.json: 건수와 제거 사유 요약
