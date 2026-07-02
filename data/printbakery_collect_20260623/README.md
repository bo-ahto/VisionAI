# Print Bakery 오리지널 평면 수집 패키지

## 대상
- https://printbakery.com/product/list.html?cate_no=367
- 2026-06-23 기준 화면 표시 총 1,743개

## 수집 항목
- 목록: product_no, 작가명, 작품명, 표시 가격, 상세 URL, 대표 이미지 URL
- 상세: artwork, artist, price, maker, size, method, material, edition, code, 상품 설명, meta/og 정보

## 실행
목록만 빠르게 수집:

```bash
python3 data/printbakery_collect_20260623/scripts/collect_printbakery_originals.py --list-only --delay-sec 1.0
```

상세까지 전체 수집:

```bash
python3 data/printbakery_collect_20260623/scripts/collect_printbakery_originals.py --delay-sec 1.0
```

테스트 실행:

```bash
python3 data/printbakery_collect_20260623/scripts/collect_printbakery_originals.py --max-pages 1 --delay-sec 0.2
```

## 산출물
- outputs/printbakery_originals_list.csv
- outputs/printbakery_originals_detail.csv
- outputs/printbakery_originals_detail_partial.csv
- outputs/collection_summary.json
- raw_html/list/: 목록 HTML 캐시
- raw_html/detail/: 상세 HTML 캐시

## 운영 메모
- robots.txt에서 /product/list.html, /product/detail.html은 금지되어 있지 않다.
- 기본 요청 간격은 1초다.
- 캐시 HTML이 있으면 재실행 시 재다운로드하지 않는다.
- 최신 상태로 다시 받고 싶으면 --refresh를 붙인다.
