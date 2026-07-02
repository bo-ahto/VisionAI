# Art1 원화 데이터 수집 패키지

## 목적

Art1 원화 카테고리의 작품, 작가, 가격, 크기, 재료, 제작연도 등 가격 예측 학습에 사용할 수 있는 정보를 수집한다.

## 수집 대상

- 목록 URL: `https://www.art1.com/marketPlace/market_list.php?medium=0`
- 추가 목록 AJAX: `https://www.art1.com/marketPlace/__artworks_list.php?page={page}&medium=0`
- 상세 AJAX: `https://www.art1.com/marketPlace/__detail_view.php?goods={goods_id}`

## 실행

```bash
python3 data/art1_collect_20260623/scripts/collect_art1_fine_art.py --delay-sec 1.0
```

캐시를 무시하고 다시 수집할 때:

```bash
python3 data/art1_collect_20260623/scripts/collect_art1_fine_art.py --delay-sec 1.0 --refresh
```

테스트로 앞쪽 일부 페이지만 수집할 때:

```bash
python3 data/art1_collect_20260623/scripts/collect_art1_fine_art.py --max-pages 2 --delay-sec 0.2
```

## 폴더 구조

- `scripts/collect_art1_fine_art.py`: 수집/정규화 스크립트
- `raw_html/list/`: 목록 HTML 캐시
- `raw_html/detail/`: 상세 HTML 캐시
- `outputs/art1_fine_art_list.csv`: 목록 기준 수집 결과
- `outputs/art1_fine_art_detail.csv`: 목록 + 상세 원본 파싱 결과
- `outputs/art1_fine_art_detail_normalized.csv`: 학습/분석에 쓰기 쉬운 최종 정규화 결과
- `outputs/collection_summary.json`: 수집 요약
- `outputs/art1_fine_art_quality_summary.json`: 품질 점검 요약

## 현재 수집 결과

- 목록 반환 작품 수: 1,541건
- 상세 수집 성공: 1,541건
- 상세 수집 실패: 0건
- 중복 `goods_id`: 0건
- 양수 가격 보유: 1,142건
- 목록 기준 판매완료 표시: 804건
- 작가명 보유: 1,541건
- 제작연도 보유: 1,541건
- 재료 보유: 1,541건
- 가로/세로 크기 파싱: 1,540건

## 참고

화면 상단의 총 건수와 실제 AJAX 목록에서 반환되는 작품 수가 다를 수 있다. 현재 스크립트는 실제 목록/상세 API에서 반환된 `goods_id` 기준으로 중복 제거 후 저장한다.
