# Track 4 1차 시장 raw 통합본 컬럼 감사

- 목적: 크롤링/수집 데이터가 공통 schema로 들어오면서 컬럼 밀림, 오입력, 이상값이 생겼는지 점검
- 기준 파일: `data/track4_primary_market_raw_unified.csv`
- 전체 rows: `33,276`
- 전체 columns: `28`

## 1. 출처별 요약

| 출처 | rows | 작가 수 | 가격 중앙값 | 가격 Q25 | 가격 Q75 | 최대 가격 |
|---|---:|---:|---:|---:|---:|---:|
| artsy | `10,111` | `1,020` | `4,140,000` | `1,656,000` | `11,000,000` | `55,200,000,000` |
| artue | `2,599` | `362` | `2,740,200` | `1,200,000` | `6,850,500` | `444,861,500` |
| gallery_primary | `288` | `78` | `20,000,000` | `4,500,000` | `79,013,000` | `2,765,568,000` |
| saatchi | `20,278` | `820` | `2,622,000` | `1,104,000` | `6,085,800` | `145,507,200` |

## 2. 주요 이상 신호

| 점검 항목 | 건수 | 비율 | 주요 출처 | 해석 |
|---|---:|---:|---|---|
| `price_extreme_over_100m` | `956` | `2.87%` | saatchi:762, artsy:130, gallery_primary:57, artue:7 | 고가 이상치 후보. gallery_primary와 일부 Artsy 가격대 확인 필요 |
| `width_height_missing` | `93` | `0.28%` | artsy:93 | 크기 파싱 실패 또는 원본 크기 결측 |
| `price_too_low_under_10000` | `50` | `0.15%` | artsy:49, artue:1 | 가격 파싱 오류 또는 테스트/자리표시값 가능성 |
| `aspect_extreme_under_0_05_or_over_20` | `20` | `0.06%` | saatchi:16, artsy:4 | 가로/세로 중 하나가 잘못 들어갔을 가능성 |
| `year_too_old_before_1000` | `14` | `0.04%` | artsy:14 | 확인 필요 |
| `width_or_height_extreme_over_1000cm` | `12` | `0.04%` | artsy:11, gallery_primary:1 | 크기 단위 오류 또는 컬럼 오입력 가능성 |
| `price_extreme_over_1b` | `10` | `0.03%` | artsy:5, gallery_primary:5 | 초고가 이상치 후보. 학습 제외 또는 별도 구간 검토 필요 |
| `year_future_after_2026` | `10` | `0.03%` | artsy:10 | 확인 필요 |
| `depth_extreme_over_300cm` | `8` | `0.02%` | artsy:7, saatchi:1 | 깊이 단위 오류 또는 설치/조각 작품 가능성 |
| `title_empty` | `1` | `0.00%` | artsy:1 | 작품명 결측 |

## 3. 컬럼별 결측률

| 컬럼 | 결측 수 | 결측률 | unique/top 또는 범위 |
|---|---:|---:|---|
| `year_made` | `20,987` | `63.07%` | min `0.000`, median `2,024.000`, max `4,800,000.000` |
| `width_cm` | `93` | `0.28%` | min `1.000`, median `60.500`, max `2,290.000` |
| `height_cm` | `93` | `0.28%` | min `0.700`, median `60.500`, max `1,818.000` |
| `depth_cm` | `8,511` | `25.58%` | min `0.100`, median `2.500`, max `2,025.000` |
| `has_depth` | `0` | `0.00%` | min `0.000`, median `1.000`, max `1.000` |
| `area_cm2` | `93` | `0.28%` | min `1.000`, median `3,672.360`, max `3,305,124.000` |
| `log_area` | `93` | `0.28%` | min `0.693`, median `8.209`, max `15.011` |
| `aspect_ratio` | `93` | `0.28%` | min `0.031`, median `1.000`, max `140.949` |
| `estimated_ho` | `12,998` | `39.06%` | min `0.000`, median `15.000`, max `200.000` |
| `price_krw` | `0` | `0.00%` | min `1.000`, median `3,000,000.000`, max `55,200,000,000.000` |
| `ln_price` | `0` | `0.00%` | min `0.000`, median `14.914`, max `24.734` |
| `is_excluded_for_training` | `0` | `0.00%` | min `0.000`, median `0.000`, max `1.000` |
| `source` | `0` | `0.00%` | `saatchi`:20278, `artsy`:10111, `artue`:2599 |
| `source_file` | `0` | `0.00%` | `data/saatchi_cleaned.csv`:20278, `data/artsy_kr_artworks.csv`:10111, `data/artue_테스트_가격포함.csv`:2599 |
| `source_artwork_id` | `0` | `0.00%` | `13458973`:1, `13247449`:1, `13374385`:1 |
| `artist_name_raw` | `0` | `0.00%` | `hyera lee`:699, `gyobeom an`:590, `ko byung jun`:346 |
| `artist_slug` | `0` | `0.00%` | `1803528`:699, `781688`:590, `976343`:346 |
| `title` | `1` | `0.00%` | `Untitled`:197, `image-face(model)`:170, `secret garden`:139 |
| `medium_raw` | `28` | `0.08%` | `acrylic`:6768, `oil`:5624, `Oil on canvas`:1946 |
| `medium_category` | `0` | `0.00%` | `acrylic`:9960, `oil`:9199, `painting`:6974 |
| `support_category` | `0` | `0.00%` | `canvas`:21766, `paper`:5493, `unknown`:2891 |
| `price_raw` | `0` | `0.00%` | `US$3,000`:280, `US$2,000`:261, `US$4,000`:209 |
| `price_currency` | `0` | `0.00%` | `USD`:29140, `KRW`:3958, `GBP`:102 |
| `artwork_url` | `288` | `0.87%` | `https://www.saatchiart.com/art/Painting-secret-garden/1889924/13458973/view`:1, `https://www.saatchiart.com/art/Painting-secret-garden/1889924/13247449/view`:1, `https://www.saatchiart.com/art/Painting-Green-summer-ocean/2815263/13374385/view`:1 |
| `image_url` | `2,902` | `8.72%` | `https://images.saatchiart.com/saatchi/1889924/art/13458973/12521107-ITDXRBBA-7.jpg`:1, `https://images.saatchiart.com/saatchi/1889924/art/13247449/12309585-PLRGOGKV-7.jpg`:1, `https://images.saatchiart.com/saatchi/2815263/art/13374385/12436519-EPSAFTMR-7.jpg`:1 |
| `gallery_name` | `2,599` | `7.81%` | `Saatchi Art`:20278, `Art Spoon`:1097, `The Trinity Gallery`:852 |
| `gallery_tier` | `2,887` | `8.68%` | `3`:20278, `Gallery`:10111 |
| `exclude_reason` | `32,659` | `98.15%` | `support_excluded`:520, `keyword_3d:glass`:35, `keyword_3d:stainless`:35 |

## 4. 중복 점검

- `source_artwork_id_duplicates`: rows `0`, groups `0`
- `semantic_duplicates`: rows `191`, groups `87`

## 5. 현재 판단

- raw 통합본은 바로 학습에 쓰면 안 됨
- 가격 이상치, 낮은 가격, 크기 이상값, URL 오입력, 출처별 가격대 차이를 먼저 정리해야 함
- 컬럼 밀림으로 강하게 의심되는 항목은 현재 자동 점검 기준상 많지 않지만, 가격/크기/URL 이상값 샘플을 수동 확인해야 함
- 다음 단계는 감사 결과를 기준으로 `track4_primary_market_cleaned_v1.csv` 생성 규칙을 확정하는 것임

## 6. 원본 감사 JSON

- `data/track4_primary_market_column_audit.json`
