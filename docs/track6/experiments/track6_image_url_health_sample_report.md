# Track6 이미지 URL 샘플 다운로드 검증

- 생성 시각: 2026-06-04 03:07:52
- 목적: Track6 전용 이미지 임베딩 추출 전에 실제 이미지 URL이 다운로드 가능한지 확인한다.
- 결과 파일: `data/track6/image_multimodal/track6_image_url_health_sample.csv`

## 요약

| split | source | checked_rows | ok_rows | ok_rate | median_elapsed_ms |
| --- | --- | --- | --- | --- | --- |
| train | saatchi | 2 | 2 | 1.0 | 256 |
| train | artsy | 2 | 2 | 1.0 | 807 |
| val_cold | saatchi | 2 | 2 | 1.0 | 287 |
| val_cold | artsy | 2 | 2 | 1.0 | 697 |
| test_cold | saatchi | 2 | 2 | 1.0 | 356 |
| test_cold | artsy | 2 | 2 | 1.0 | 747 |
| val_warm | saatchi | 2 | 2 | 1.0 | 354 |
| val_warm | artsy | 2 | 2 | 1.0 | 729 |
| test_warm | saatchi | 2 | 2 | 1.0 | 356 |
| test_warm | artsy | 2 | 2 | 1.0 | 694 |

## 해석 기준

- `ok_rate`가 높으면 해당 출처의 이미지를 임베딩 추출 대상으로 삼을 수 있다.
- 특정 출처의 실패율이 높으면 해당 출처는 별도 다운로드 로직이나 fallback 정책이 필요하다.
- 이 검증은 샘플 확인이므로 전체 임베딩 추출 전 대량 다운로드 실패 가능성을 완전히 제거하지는 않는다.
