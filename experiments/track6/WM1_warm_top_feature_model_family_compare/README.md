# Track6 WM1 Warm 상위 피처 조합별 모델군 비교

- 목적: Warm 상위 피처 조합을 고정한 뒤 모델만 바꿔 Huber가 실제로 Warm 최적 모델인지 검증한다.
- 종합 점수 1위: `WM1-F3: F1 + 작가 학습 작품 수` + `Huber`
- 종합 점수: `98.2730`
- MdAPE: `0.1562`
- p95_APE: `1.0548`
- Within_30: `0.7364`
- 참고: MdAPE 단일 기준 최저는 `WM1-F2: F1 + 작가명 x 면적` + `Huber` (`0.1545`)
- 결과 HTML: `outputs/result_sheet.html`
- 결과 CSV: `outputs/metrics_long.csv`
- 종합 점수 CSV: `outputs/metrics_scored.csv`

## 피처 조합별 실제 피처명

- `WM1-F1: 작가명 + 전체 크기`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio`
- `WM1-F2: F1 + 작가명 x 면적`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio, log_area_x_artist_name_ko_01, log_area_x_artist_name_ko_02, log_area_x_artist_name_ko_03, log_area_x_artist_name_ko_04, log_area_x_artist_name_ko_05, log_area_x_artist_name_ko_06, log_area_x_artist_name_ko_07, log_area_x_artist_name_ko_08, log_area_x_artist_name_ko_09, log_area_x_artist_name_ko_10`
- `WM1-F3: F1 + 작가 학습 작품 수`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio, artist_works_log, artist_works_log_is_missing`
- `WM1-F4: 작가명 + 로그 면적`: `artist_name_ko, log_area`
- `WM1-F5: F1 + 작가명 x 호수`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio, ln_estimated_ho, ln_ho_x_artist_name_ko_01, ln_ho_x_artist_name_ko_02, ln_ho_x_artist_name_ko_03, ln_ho_x_artist_name_ko_04, ln_ho_x_artist_name_ko_05, ln_ho_x_artist_name_ko_06, ln_ho_x_artist_name_ko_07, ln_ho_x_artist_name_ko_08, ln_ho_x_artist_name_ko_09, ln_ho_x_artist_name_ko_10`
