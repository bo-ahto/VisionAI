# Track6 A~J + OPT 피처/모델 종합 분석

- 생성일: `2026-05-28T06:48:48`
- 목적: A~J 실험 전체와 추가 최적화 실험을 종합해 Warm/Cold별 최고 피처 조합과 모델 후보를 선정한다.
- 전체 지표 원본: `docs/track6/experiments/a_to_j_plus_opt_all_metrics.csv`

## 지표 해석 우선순위

- 1순위: `MdAPE`를 본다. 작품별 비율 오차의 중앙값이므로 대표적인 예측 오차를 가장 안정적으로 보여준다. 낮을수록 좋다.
- 2순위: `p95_APE`를 본다. 오차가 큰 상위 5% 구간이 얼마나 위험한지 보여준다. 낮을수록 좋다.
- 3순위: `Within_30`을 본다. 실제 가격 대비 30% 이내로 맞춘 비율이다. 높을수록 좋다.
- 4순위: `RMSE_log`와 `R2`를 본다. 로그 가격 공간에서 모델이 안정적인지 확인하는 보조 지표다. `RMSE_log`는 낮을수록, `R2`는 높을수록 좋다.
- `MAPE`는 평균 비율 오차라 고가/이상치 영향을 크게 받으므로 최종 결론에서는 보조로만 사용한다.

## 지표 계산 공식

- 실제 가격: `y`
- 예측 가격: `ŷ`
- 실제 로그가격: `log_y = ln(y)`
- 예측 로그가격: `log_ŷ = ln(ŷ)`
- 작품 수: `n`

| 지표 | 공식 | 해석 | 좋은 방향 |
|---|---|---|---|
| `APE` | `APE_i = abs(ŷ_i - y_i) / y_i` | 작품 1건이 실제 가격 대비 몇 % 틀렸는지 보는 값 | 낮을수록 좋음 |
| `MdAPE` | `median(APE_i)` | 작품별 비율 오차의 중앙값 | 낮을수록 좋음 |
| `MAPE` | `(1/n) * sum(APE_i)` | 작품별 비율 오차의 평균값 | 낮을수록 좋음 |
| `p95_APE` | `percentile_95(APE_i)` | 오차가 큰 상위 5% 구간의 위험도 | 낮을수록 좋음 |
| `Within_30` | `count(APE_i <= 0.30) / n` | 실제 가격 대비 30% 이내로 맞춘 비율 | 높을수록 좋음 |
| `Within_50` | `count(APE_i <= 0.50) / n` | 실제 가격 대비 50% 이내로 맞춘 비율 | 높을수록 좋음 |
| `RMSE_log` | `sqrt((1/n) * sum((log_ŷ_i - log_y_i)^2))` | 로그 가격 기준 평균 오차 | 낮을수록 좋음 |
| `R2` | `1 - sum((log_y_i - log_ŷ_i)^2) / sum((log_y_i - mean(log_y))^2)` | 로그 가격 변동을 모델이 얼마나 설명하는지 | 높을수록 좋음 |

- 이 문서의 `MdAPE`, `p95_APE`, `Within_30`, `Within_50`은 가격 원 단위로 복원한 뒤 계산한다.
- `RMSE_log`, `R2`는 로그 가격 기준으로 계산한다.
- 가격 예측 서비스 관점에서는 `MdAPE`와 `Within_30`이 사용자 체감에 가깝다.
- 모델 안정성 관점에서는 `p95_APE`와 `RMSE_log`를 함께 본다.
- `R2`는 설명력 확인용 보조 지표이며, `MdAPE`가 나쁜 모델을 `R2`만 보고 채택하지 않는다.

## 종합 점수 환산 방식

- 누락 사유:
  - 이 문서는 처음에 A~J 전체 실험의 원 지표를 사람이 직접 해석하는 요약 문서로 작성했다.
  - 종합 점수 환산 방식은 별도 모델 비교 리포트인 `WM1`, `CM1` 결과표에 먼저 적용했다.
  - 따라서 이 문서에는 지표 우선순위만 있고, 점수 환산 방식 설명이 빠져 있었다.

- 종합 점수의 역할:
  - 여러 지표가 서로 다르게 나올 때 후보를 정렬하기 위한 보조 기준이다.
  - 모델 학습 결과를 바꾸는 값은 아니다.
  - 최종 결론은 종합 점수만 보지 않고 원 지표인 `MdAPE`, `p95_APE`, `Within_30`, `RMSE_log`, `R2`를 함께 확인한다.

- 계산 방식:
  - 같은 비교표 안에서 각 지표를 `0~100점`으로 바꾼다.
  - 낮을수록 좋은 지표는 값이 낮을수록 높은 점수를 준다.
  - 높을수록 좋은 지표는 값이 높을수록 높은 점수를 준다.
  - 각 지표 점수에 비중을 곱한 뒤 더해서 종합 점수를 만든다.

- 점수 공식:
  - 낮을수록 좋은 지표 점수: `score = 100 * (max_value - value) / (max_value - min_value)`
  - 높을수록 좋은 지표 점수: `score = 100 * (value - min_value) / (max_value - min_value)`
  - 종합점수: `total_score = sum(metric_score * metric_weight)`
  - `max_value`와 `min_value`는 같은 비교표 안의 후보들에서 계산한다.
  - 같은 비교표 안에서만 상대 순위를 보기 위한 점수다.
  - 다른 표의 점수와 절대값으로 직접 비교하지 않는다.

- 낮을수록 좋은 지표:
  - `MdAPE`
  - `p95_APE`
  - `RMSE_log`

- 높을수록 좋은 지표:
  - `Within_30`
  - `R2`

- Warm 가중치:
  - `MdAPE`: 45%
  - `Within_30`: 20%
  - `p95_APE`: 20%
  - `RMSE_log`: 10%
  - `R2`: 5%

- Cold 가중치:
  - `MdAPE`: 35%
  - `p95_APE`: 30%
  - `Within_30`: 20%
  - `RMSE_log`: 10%
  - `R2`: 5%

- Warm과 Cold 가중치가 다른 이유:
  - Warm은 이미 학습 데이터에 있는 작가를 예측하므로 대표 오차인 `MdAPE`를 가장 중요하게 본다.
  - Cold는 처음 보는 작가를 예측하므로 큰 오차 위험이 더 크다.
  - 그래서 Cold는 `p95_APE` 비중을 Warm보다 높게 둔다.

- 해석 원칙:
  - 종합 점수가 높을수록 여러 지표를 함께 봤을 때 더 좋은 후보로 본다.
  - 단, 특정 실험 안의 후보끼리 비교하는 상대 점수이므로 다른 실험군의 점수와 절대값으로 직접 비교하지 않는다.
  - 종합 점수 1위라도 `p95_APE`가 과하게 나쁘면 운영 후보로 바로 확정하지 않고 안정성 검증을 추가한다.

## 모델군 비교 종합 점수 요약

- `WM1`, `CM1`은 상위 피처 조합을 대상으로 여러 모델을 다시 비교한 실험이다.
- 아래 결과는 실제 모델 후보 확정에 더 직접적으로 사용한 점수표다.
- `피처 조합`은 실험 코드를 제거하고 사람이 바로 이해할 수 있는 피처 묶음 이름으로 표기했다.
- `실제 사용 피처`는 모델 입력에 들어간 원본 피처명을 함께 적었다.
- 표 정렬 기준은 `종합순위` 오름차순이다.

## 실험군별 세부 순위표

- 목적: 각 실험 안의 세부 변수/피처 블록별로 Warm과 Cold 모델 1~3위를 따로 확인한다.
- 사용 기준: `MdAPE` 낮은 순 -> `p95_APE` 낮은 순 -> `Within_30` 높은 순 -> `RMSE_log` 낮은 순 -> `R2` 높은 순.
- 활용 방식: A2처럼 한 실험 안에 여러 변수 표현 방식이 있을 때, 각 방식마다 어떤 모델이 1위인지 비교한다.
- HTML 문서: `docs/track6/experiments/experiment_group_top3_ranking_summary.html`
- Markdown 문서: `docs/track6/experiments/experiment_group_top3_ranking_summary.md`
- CSV 상세표: `docs/track6/experiments/experiment_group_top3_ranking_summary.csv`
- CSV 실험별 최고 요약: `docs/track6/experiments/experiment_group_top3_overview.csv`

### Warm 모델군 비교 상위 결과

| 종합순위 | 종합점수 | 피처 조합 | 실제 사용 피처 | 모델 | MdAPE | p95_APE | Within_30 | RMSE_log | R2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 98.2730 | 작가명 + 전체 크기 + 작가 학습 작품 수 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>작가 학습 작품 수 (artist_works_log)<br>작가 학습 작품 수 결측 여부 (artist_works_log_is_missing) | Huber | 0.1562 | 1.0548 | 0.7364 | 0.4128 | 0.9081 |
| 2 | 98.2335 | 작가명 + 전체 크기 + 작가명 x 호수 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>로그 호수 (ln_estimated_ho)<br>작가명 x 로그 호수(상위 10명) | Huber | 0.1545 | 1.0041 | 0.7183 | 0.4108 | 0.9090 |
| 3 | 98.1964 | 작가명 + 전체 크기 + 작가명 x 면적 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>작가명 x 로그 면적(상위 10명) | Huber | 0.1545 | 1.0181 | 0.7232 | 0.4152 | 0.9070 |
| 4 | 98.1018 | 작가명 + 전체 크기 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio) | Huber | 0.1566 | 1.0434 | 0.7315 | 0.4131 | 0.9080 |
| 5 | 97.9368 | 작가명 + 면적 | 작가명 (artist_name_ko)<br>로그 면적 (log_area) | Huber | 0.1578 | 1.0161 | 0.7265 | 0.4157 | 0.9068 |
| 6 | 94.7420 | 작가명 + 전체 크기 + 작가명 x 호수 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>로그 호수 (ln_estimated_ho)<br>작가명 x 로그 호수(상위 10명) | Linear Regression | 0.1762 | 1.0465 | 0.7133 | 0.4117 | 0.9086 |
| 7 | 94.3962 | 작가명 + 전체 크기 + 작가명 x 면적 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>작가명 x 로그 면적(상위 10명) | Linear Regression | 0.1771 | 1.0145 | 0.7035 | 0.4154 | 0.9069 |
| 8 | 94.3370 | 작가명 + 전체 크기 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio) | Linear Regression | 0.1776 | 0.9777 | 0.6952 | 0.4153 | 0.9070 |

### Cold 모델군 비교 상위 결과

| 종합순위 | 종합점수 | 피처 조합 | 실제 사용 피처 | 모델 | MdAPE | p95_APE | Within_30 | RMSE_log | R2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 94.0240 | 작품 기본 피처 + 활동량/인지도 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1) | CatBoost | 0.4488 | 2.9885 | 0.3304 | 0.8797 | 0.5519 |
| 2 | 92.5817 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 호수 (total_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (followers_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (for_sale_works_x_ln_ho) | HistGradientBoosting | 0.4666 | 2.9012 | 0.3314 | 0.8676 | 0.5643 |
| 3 | 89.9601 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 면적 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 면적 (total_works_x_log_area)<br>팔로워 수 x 로그 면적 (followers_x_log_area)<br>판매 중 작품 수 x 로그 면적 (for_sale_works_x_log_area) | LightGBM | 0.4580 | 2.9412 | 0.3082 | 0.8697 | 0.5622 |
| 4 | 88.6962 | 작품 기본 피처 + 활동량/인지도 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1) | HistGradientBoosting | 0.4601 | 3.2319 | 0.3437 | 0.8699 | 0.5619 |
| 5 | 88.0576 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 호수 (total_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (followers_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (for_sale_works_x_ln_ho) | LightGBM | 0.4612 | 2.9737 | 0.3075 | 0.8724 | 0.5594 |
| 6 | 86.2834 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 호수 (total_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (followers_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (for_sale_works_x_ln_ho) | XGBoost | 0.4594 | 2.9500 | 0.2965 | 0.8836 | 0.5480 |
| 7 | 86.1530 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 면적 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 면적 (total_works_x_log_area)<br>팔로워 수 x 로그 면적 (followers_x_log_area)<br>판매 중 작품 수 x 로그 면적 (for_sale_works_x_log_area) | HistGradientBoosting | 0.4721 | 2.9366 | 0.3066 | 0.8697 | 0.5621 |
| 8 | 86.0630 | 작품 기본 피처 + 활동량/인지도 + 정보량 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing) | HistGradientBoosting | 0.4741 | 3.0820 | 0.3246 | 0.8615 | 0.5703 |

## 선택 모델 특성 및 적합성

| 구분 | 선택 모델 | 모델 특성 | Track6에 적합한 이유 | 주의점 |
|---|---|---|---|---|
| Warm 1순위 | `Huber` | 선형 회귀 계열이며, 큰 오차 작품의 영향력을 줄여 학습함 | Warm은 작가명과 크기 정보가 강하게 작동하고, Huber가 이상치 가격에 덜 흔들리면서 MdAPE와 종합점수 모두 상위권을 유지함 | 계수 해석은 가능하지만, 작가명 one-hot 계수는 학습 작품 수가 적은 작가에서 과신하면 안 됨 |
| Warm 보조 | `Linear Regression` | 가장 단순한 선형 회귀이며, 모든 오차를 동일한 방식으로 반영함 | Huber 결과를 설명할 때 비교 기준으로 유용하고, 피처 방향성 확인에 좋음 | 고가 작품과 이상치에 민감해 MdAPE가 Huber보다 낮게 나오지 않았음 |
| Warm 보조 | `Ridge` | 선형 회귀에 규제를 넣어 계수 과대화를 줄임 | 피처가 많아질 때 계수 폭주를 막는 안정성 비교 후보로 적합함 | 이번 상위 결과에서는 Huber보다 대표 오차 개선 근거가 약함 |
| Cold 1순위 | `CatBoost` | 범주형 피처와 비선형 관계를 잘 다루는 트리 부스팅 모델 | Cold는 작가명을 쓸 수 없고 재료, 지지체, 활동량/인지도처럼 범주형과 숫자형이 섞여 있어 CatBoost가 구조적으로 적합함 | p95_APE가 여전히 커서 단일 가격만 제공하기에는 위험함 |
| Cold 보조 | `LightGBM` | 빠른 트리 부스팅 모델이며, 다양한 피처 조합과 상호작용을 잘 탐색함 | A~J/OPT 탐색에서 활동량/인지도 x 면적, 활동량/인지도 x 호수 같은 조합에서 상위권을 반복적으로 보임 | 최종 모델군 비교에서는 CatBoost보다 MdAPE가 낮지 않아 보조 후보로 둠 |
| Cold 보조 | `Quantile-LAD` | 평균보다 중앙값 방향의 예측을 중시하는 강건 회귀 계열 | 큰 오차 방어와 가격 범위 비교용 기준 모델로 의미가 있음 | 최종 정확도 1순위는 아니므로 단독 운영 후보보다는 안정성 비교 후보로 사용함 |

- Warm에서 `Huber`가 적합한 이유:
  - 미술품 가격은 고가 작품과 특이 케이스가 있어 일반 선형 회귀가 이상치에 끌릴 수 있음.
  - Huber는 작은 오차는 일반 회귀처럼 학습하고, 큰 오차는 영향력을 줄여 학습함.
  - Warm 상위 결과에서 Huber가 `MdAPE`와 종합점수 기준 모두 가장 안정적으로 상위권을 차지함.
  - 작가명과 크기 피처의 방향성을 계수로 점검할 수 있어 설명 가능성도 유지됨.

- Cold에서 `CatBoost`가 적합한 이유:
  - Cold는 작가명을 사용할 수 없어 작품 조건과 작가 메타의 비선형 조합을 더 많이 활용해야 함.
  - CatBoost는 난트 재료 번호, 난트 지지체, 주요 작가 여부 같은 범주형 성격의 피처를 다루는 데 유리함.
  - CM1 모델군 비교에서 `작품 기본 피처 + 활동량/인지도` 조합의 CatBoost가 `MdAPE 0.4488`로 Cold 1순위였음.
  - LightGBM 상위 후보보다 최종 모델군 비교 기준에서 대표 오차가 낮아 1차 운영 후보로 둠.

- Cold에서 `LightGBM`을 보조 후보로 두는 이유:
  - 여러 A~J/OPT 탐색 실험에서 상위권을 반복적으로 기록함.
  - 활동량/인지도와 면적/호수의 상호작용처럼 복합 피처를 빠르게 실험하기 좋음.
  - CatBoost보다 최종 대표 오차가 낮지는 않았으므로 1순위가 아니라 fallback, 가격 범위, 후처리 비교 후보로 둠.

## Warm 결론

- Warm 모델군 비교 종합점수 1위: `작가명 + 전체 크기 + 작가 학습 작품 수 + Huber`.
- Warm 모델군 비교 MdAPE 최저 후보: `작가명 + 전체 크기 + 작가명 x 면적 + Huber`.
- Warm A~J/OPT 탐색 종합점수 1위: `작가명 + 전체 크기 + 작가 학습 작품 수 + Huber`.
- Warm A~J/OPT 탐색 MdAPE 최저 후보: `작가명 + 전체 크기 + 작가명 x 면적 + Huber`.
- 핵심 피처 축: `작가명 + 전체 크기`.
- 전체 크기 구성: `width_cm`, `height_cm`, `log_area`, `aspect_ratio`.
- 해석: 학습 데이터에 있는 작가라면 작가명으로 기본 가격대를 잡고, 실제 크기 정보로 작품별 가격 차이를 보정하는 조합이 가장 안정적이다.
- 추가 피처 해석: `작가 학습 작품 수`는 종합점수 기준에서 강하고, `작가명 x 면적`은 MdAPE 최저 후보에서 강하다.
- 운영 후보: 안정성과 단순성을 중시하면 `작가명 + 전체 크기 + Huber`.
- 정확도 우선 후보: MdAPE를 더 낮추는 목적이면 `작가명 + 전체 크기 + 작가명 x 면적 + Huber`.

## Cold 결론

- Cold 모델군 비교 종합점수 1위: `작품 기본 피처 + 활동량/인지도 + CatBoost`.
- Cold 모델군 비교 MdAPE 최저 후보: `작품 기본 피처 + 활동량/인지도 + CatBoost`.
- Cold A~J/OPT 탐색 종합점수 1위: `작품 기본 피처 + 활동량/인지도 + 정보량 + 기본 작가 프로필/전시 + LightGBM`.
- Cold A~J/OPT 탐색 LightGBM MdAPE 최저 후보: `면적 + 활동량/인지도 + 활동량/인지도 x 면적 + LightGBM`.
- Cold 안정성 후보: `작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 호수 + LightGBM`.
- 1차 운영 후보: `작품 기본 피처 + 활동량/인지도 + CatBoost`.
- 보조 후보: `활동량/인지도 x 면적` 또는 `활동량/인지도 x 호수` 기반 `LightGBM`.
- 해석: Cold는 작가명을 사용할 수 없으므로 `호수 + 난트 재료 + 난트 지지체`로 작품 조건을 잡고, 작가 활동량/인지도 메타로 시장 노출 차이를 보완하는 방식이 가장 유리하다.
- 주의: Cold는 MdAPE가 약 `0.45` 수준이라 Warm보다 오차가 크다. 단일 가격만 제공하기보다 가격 범위와 신뢰도 경고가 필요하다.

## 최종 추천안

- Warm 운영 후보: `작가명 + 전체 크기` 기반 `Huber`.
- Warm 정확도 우선 후보: `작가명 + 전체 크기 + 작가명 x 면적` 기반 `Huber`.
- Cold 운영 1순위 후보: `작품 기본 피처 + 활동량/인지도` 기반 `CatBoost`.
- Cold 보조 후보: `활동량/인지도 x 면적` 또는 `활동량/인지도 x 호수` 기반 `LightGBM`.
- Cold 운영 방식: 단일 가격 + 가격 범위 + 신뢰도 경고를 함께 제공하는 방향이 필요하다.

## 실제 예측력 해석

- Warm 최고 후보는 MdAPE 약 `0.1548` 수준이다. 대표 작품 기준 예측 가격이 실제 가격에서 약 15~16% 정도 벗어나는 수준으로 해석할 수 있다.
- Warm p95_APE는 약 `1.0537` 수준이다. 오차가 큰 상위 5% 작품은 실제 가격 대비 100% 이상 벗어날 수 있어 예외 케이스 관리는 필요하다.
- Cold 1순위 후보는 MdAPE `0.4488` 수준이다. 처음 보는 작가의 경우 대표 오차가 약 45%라 Warm보다 훨씬 어렵다.
- Cold p95_APE는 `2.9885` 수준이다. Cold의 큰 오차 구간은 매우 크므로 운영에서는 가격 범위/주의 문구/추가 입력값 수집이 필요하다.

## Warm 상위 결과

- 아래 표는 A~J/OPT 후속 실험 안에서 나온 Warm 상위 결과다.
- 표 정렬 기준은 `종합순위` 오름차순이다.
- MdAPE만 가장 낮은 후보와 종합점수 1위가 다를 수 있으므로 결론에서는 둘을 분리해 해석한다.

| 종합순위 | 종합점수 | 피처 조합 | 실제 사용 피처 | 모델 | MdAPE | p95_APE | Within_30 | RMSE_log | R2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 99.3713 | 작가명 + 전체 크기 + 작가 학습 작품 수 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>작가 학습 작품 수 (artist_works_log)<br>작가 학습 작품 수 결측 여부 (artist_works_log_is_missing) | Huber | 0.1562 | 1.0548 | 0.7364 | 0.4128 | 0.9081 |
| 2 | 99.3465 | 작가명 + 전체 크기 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio) | Huber | 0.1569 | 1.0464 | 0.7364 | 0.4129 | 0.9081 |
| 3 | 99.2030 | 작가명 + 전체 크기 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio) | Huber | 0.1566 | 1.0434 | 0.7315 | 0.4131 | 0.9080 |
| 4 | 99.2030 | 작가명 + 전체 크기 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio) | Huber | 0.1566 | 1.0434 | 0.7315 | 0.4131 | 0.9080 |
| 5 | 98.9950 | 작가명 + 면적 | 작가명 (artist_name_ko)<br>로그 면적 (log_area) | Huber | 0.1578 | 1.0161 | 0.7265 | 0.4157 | 0.9068 |
| 6 | 98.9950 | 작가명 + 면적 | 작가명 (artist_name_ko)<br>로그 면적 (log_area) | Huber | 0.1578 | 1.0161 | 0.7265 | 0.4157 | 0.9068 |
| 7 | 98.9128 | 작가명 + 전체 크기 + 작가명 x 면적 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>작가명 x 로그 면적(상위 10명) | Huber | 0.1548 | 1.0537 | 0.7232 | 0.4215 | 0.9042 |
| 8 | 98.7199 | 작가명 + 면적 + 작가명 x 면적 | 작가명 (artist_name_ko)<br>로그 면적 (log_area)<br>작가명 x 로그 면적(상위 10명) | Huber | 0.1565 | 1.0765 | 0.7282 | 0.4352 | 0.8979 |
| 9 | 98.7014 | 작가명 + 전체 크기 + 작가명 x 호수 | 작가명 (artist_name_ko)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>로그 호수 (ln_estimated_ho)<br>작가명 x 로그 호수(상위 10명) | Huber | 0.1583 | 0.9960 | 0.7166 | 0.4139 | 0.9076 |
| 10 | 98.2507 | 작가명 + 전체 크기 + 작품 기본 피처 + 제작연도/작품 유형 + 에디션 | 작가명 (artist_name_ko)<br>로그 호수 (ln_estimated_ho)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>제작연도 (artwork_year)<br>작품 연한 (artwork_age)<br>작품 유형 (artwork_type_final)<br>작품 유형 대분류 (artwork_type_final_major3)<br>에디션 구분 (edition_class)<br>에디션 여부 (is_edition)<br>리미티드 에디션 여부 (is_limited_edition)<br>오픈 에디션 여부 (is_open_edition)<br>에디션 미상 여부 (is_unknown_edition)<br>에디션 정보 보유 여부 (edition_info_available) | Huber | 0.1648 | 1.0607 | 0.7199 | 0.4071 | 0.9106 |
| 11 | 98.1821 | 작가명 + 전체 크기 + 작품 기본 피처 + 제작연도/작품 유형 + 깊이/3D | 작가명 (artist_name_ko)<br>로그 호수 (ln_estimated_ho)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>제작연도 (artwork_year)<br>작품 연한 (artwork_age)<br>작품 유형 (artwork_type_final)<br>작품 유형 대분류 (artwork_type_final_major3)<br>깊이 (depth_cm)<br>깊이값 있음 (has_depth)<br>3D 후보 (is_3d_candidate) | Huber | 0.1615 | 1.0525 | 0.7100 | 0.4060 | 0.9111 |
| 12 | 98.1650 | 작가명 + 전체 크기 + 작품 기본 피처 | 작가명 (artist_name_ko)<br>로그 호수 (ln_estimated_ho)<br>가로 (width_cm)<br>세로 (height_cm)<br>로그 면적 (log_area)<br>가로세로 비율 (aspect_ratio)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support) | Huber | 0.1649 | 1.1073 | 0.7232 | 0.4114 | 0.9087 |

## Cold 상위 결과

- 아래 표는 A~J/OPT 후속 실험 안에서 나온 Cold 상위 결과다.
- 표 정렬 기준은 `종합순위` 오름차순이다.
- 이 표만 보면 `LightGBM`이 상위권에 많지만, 별도 모델군 비교 실험인 `CM1`에서는 `CatBoost`가 MdAPE `0.4488`로 1순위였다.
- 따라서 최종 운영 1순위는 `CatBoost`, LightGBM은 보조 후보로 해석한다.

| 종합순위 | 종합점수 | 피처 조합 | 실제 사용 피처 | 모델 | MdAPE | p95_APE | Within_30 | RMSE_log | R2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 96.8491 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 기본 작가 프로필/전시 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 생년 (artist_meta_birth_year)<br>개인전 수 (artist_exhibition_solo_count)<br>단체전 수 (artist_exhibition_group_count)<br>아트페어 수 (artist_exhibition_fair_count)<br>작가 국적 (artist_meta_nationality)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>artist_exhibition_available_count<br>작가 생년 결측 여부 (artist_meta_birth_year_is_missing)<br>개인전 수 결측 여부 (artist_exhibition_solo_count_is_missing)<br>단체전 수 결측 여부 (artist_exhibition_group_count_is_missing)<br>아트페어 수 결측 여부 (artist_exhibition_fair_count_is_missing)<br>작가 국적 결측 여부 (artist_meta_nationality_is_missing)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing) | LightGBM | 0.4684 | 3.5812 | 0.3462 | 0.8495 | 0.5822 |
| 2 | 96.3096 | 작품 기본 피처 + 활동량/인지도 + 정보량 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing) | LightGBM | 0.4577 | 2.9056 | 0.3246 | 0.8742 | 0.5576 |
| 3 | 95.7308 | 작품 기본 피처 + 활동량/인지도 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works) | LightGBM | 0.4580 | 3.0833 | 0.3243 | 0.8804 | 0.5512 |
| 4 | 95.5192 | 면적 + 활동량/인지도 | 로그 면적 (log_area)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1) | LightGBM | 0.4608 | 3.0955 | 0.3266 | 0.8898 | 0.5416 |
| 5 | 95.2554 | 호수 + 활동량/인지도 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 전체 작품 수 x 로그 호수 (artist_meta_total_works_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (artist_meta_for_sale_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (artist_meta_followers_x_ln_ho)<br>주요 작가 여부 x 로그 호수 (artist_meta_is_p1_x_ln_ho) | LightGBM | 0.4544 | 3.1807 | 0.3211 | 0.8888 | 0.5427 |
| 6 | 95.1156 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 호수 (total_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (followers_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (for_sale_works_x_ln_ho) | LightGBM | 0.4579 | 2.7983 | 0.3085 | 0.8645 | 0.5673 |
| 7 | 95.0072 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 면적 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 면적 (total_works_x_log_area)<br>팔로워 수 x 로그 면적 (followers_x_log_area)<br>판매 중 작품 수 x 로그 면적 (for_sale_works_x_log_area) | LightGBM | 0.4604 | 2.9683 | 0.3136 | 0.8685 | 0.5634 |
| 8 | 94.9232 | 면적 + 활동량/인지도 + 활동량/인지도 x 면적 | 로그 면적 (log_area)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 전체 작품 수 x 로그 면적 (artist_meta_total_works_x_log_area)<br>판매 중 작품 수 x 로그 면적 (artist_meta_for_sale_works_x_log_area)<br>팔로워 수 x 로그 면적 (artist_meta_followers_x_log_area)<br>주요 작가 여부 x 로그 면적 (artist_meta_is_p1_x_log_area) | LightGBM | 0.4516 | 3.1609 | 0.3153 | 0.8883 | 0.5431 |
| 9 | 94.3959 | 작품 기본 피처 + 활동량/인지도 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1) | LightGBM | 0.4720 | 2.9687 | 0.3191 | 0.8836 | 0.5480 |
| 10 | 94.2628 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 기본 작가 프로필/전시 + 활동량/인지도 x 면적 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 생년 (artist_meta_birth_year)<br>작가 경력 단계 (artist_meta_career_stage)<br>작가 국적 (artist_meta_nationality)<br>개인전 수 (artist_exhibition_solo_count)<br>단체전 수 (artist_exhibition_group_count)<br>아트페어 수 (artist_exhibition_fair_count)<br>전시/아트페어 총수 (artist_exhibition_total_count)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 생년 결측 여부 (artist_meta_birth_year_is_missing)<br>작가 경력 단계 결측 여부 (artist_meta_career_stage_is_missing)<br>작가 국적 결측 여부 (artist_meta_nationality_is_missing)<br>개인전 수 결측 여부 (artist_exhibition_solo_count_is_missing)<br>단체전 수 결측 여부 (artist_exhibition_group_count_is_missing)<br>아트페어 수 결측 여부 (artist_exhibition_fair_count_is_missing)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 면적 (total_works_x_log_area)<br>팔로워 수 x 로그 면적 (followers_x_log_area)<br>판매 중 작품 수 x 로그 면적 (for_sale_works_x_log_area)<br>작가 전체 작품 수 x 로그 호수 (total_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (followers_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (for_sale_works_x_ln_ho) | Quantile-LAD | 0.4584 | 3.7071 | 0.3214 | 0.8724 | 0.5594 |
| 11 | 93.6918 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 면적 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 면적 (total_works_x_log_area)<br>팔로워 수 x 로그 면적 (followers_x_log_area)<br>판매 중 작품 수 x 로그 면적 (for_sale_works_x_log_area)<br>작가 전체 작품 수 x 로그 호수 (total_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (followers_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (for_sale_works_x_ln_ho) | LightGBM | 0.4645 | 2.8631 | 0.3030 | 0.8763 | 0.5554 |
| 12 | 93.5471 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 기본 작가 프로필/전시 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 생년 (artist_meta_birth_year)<br>개인전 수 (artist_exhibition_solo_count)<br>단체전 수 (artist_exhibition_group_count)<br>아트페어 수 (artist_exhibition_fair_count)<br>작가 국적 (artist_meta_nationality)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>artist_exhibition_available_count<br>작가 생년 결측 여부 (artist_meta_birth_year_is_missing)<br>개인전 수 결측 여부 (artist_exhibition_solo_count_is_missing)<br>단체전 수 결측 여부 (artist_exhibition_group_count_is_missing)<br>아트페어 수 결측 여부 (artist_exhibition_fair_count_is_missing)<br>작가 국적 결측 여부 (artist_meta_nationality_is_missing)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing) | Quantile-LAD | 0.4746 | 3.5073 | 0.3285 | 0.9036 | 0.5273 |

## Cold 안정성 후보

- 아래 표는 Cold 후보 중 큰 오차를 줄이는 데 유리한 후보를 보기 위한 표다.
- 정렬 기준은 `p95_APE` 낮은 순이다.
- 이 표는 최종 1순위 표가 아니라 가격 범위, fallback, 앙상블 후처리 비교용 후보표다.

| 안정성순위 | 종합점수 | 피처 조합 | 실제 사용 피처 | 모델 | MdAPE | p95_APE | Within_30 | RMSE_log | R2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 95.1156 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 호수 (total_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (followers_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (for_sale_works_x_ln_ho) | LightGBM | 0.4579 | 2.7983 | 0.3085 | 0.8645 | 0.5673 |
| 2 | 93.6918 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 면적 + 활동량/인지도 x 호수 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 면적 (total_works_x_log_area)<br>팔로워 수 x 로그 면적 (followers_x_log_area)<br>판매 중 작품 수 x 로그 면적 (for_sale_works_x_log_area)<br>작가 전체 작품 수 x 로그 호수 (total_works_x_ln_ho)<br>팔로워 수 x 로그 호수 (followers_x_ln_ho)<br>판매 중 작품 수 x 로그 호수 (for_sale_works_x_ln_ho) | LightGBM | 0.4645 | 2.8631 | 0.3030 | 0.8763 | 0.5554 |
| 3 | 96.3096 | 작품 기본 피처 + 활동량/인지도 + 정보량 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing) | LightGBM | 0.4577 | 2.9056 | 0.3246 | 0.8742 | 0.5576 |
| 4 | 95.0072 | 작품 기본 피처 + 활동량/인지도 + 정보량 + 활동량/인지도 x 면적 | 로그 호수 (ln_estimated_ho)<br>로그 면적 (log_area)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing)<br>작가 전체 작품 수 x 로그 면적 (total_works_x_log_area)<br>팔로워 수 x 로그 면적 (followers_x_log_area)<br>판매 중 작품 수 x 로그 면적 (for_sale_works_x_log_area) | LightGBM | 0.4604 | 2.9683 | 0.3136 | 0.8685 | 0.5634 |
| 5 | 94.3959 | 작품 기본 피처 + 활동량/인지도 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1) | LightGBM | 0.4720 | 2.9687 | 0.3191 | 0.8836 | 0.5480 |
| 6 | 90.9306 | 작품 기본 피처 + 활동량/인지도 + 정보량 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing) | LightGBM | 0.4754 | 2.9884 | 0.2869 | 0.8807 | 0.5510 |
| 7 | 93.2107 | 작품 기본 피처 + 활동량/인지도 + 정보량 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 전체 작품 수 결측 여부 (artist_meta_total_works_is_missing)<br>판매 중 작품 수 결측 여부 (artist_meta_for_sale_works_is_missing)<br>팔로워 수 결측 여부 (artist_meta_followers_is_missing)<br>주요 작가 여부 결측 여부 (artist_meta_is_p1_is_missing) | LightGBM | 0.4756 | 2.9964 | 0.3091 | 0.8776 | 0.5542 |
| 8 | 92.9167 | 작품 기본 피처 + 활동량/인지도 + 정보량 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 메타 보유 개수 (artist_meta_available_count)<br>작가 메타 완성도 (artist_meta_completeness_score) | LightGBM | 0.4598 | 3.0662 | 0.2988 | 0.8872 | 0.5443 |
| 9 | 95.7308 | 작품 기본 피처 + 활동량/인지도 | 로그 호수 (ln_estimated_ho)<br>난트 재료 번호 (nant_material_idx)<br>난트 도구 (nant_tool)<br>난트 지지체 (nant_support)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works) | LightGBM | 0.4580 | 3.0833 | 0.3243 | 0.8804 | 0.5512 |
| 10 | 95.5192 | 면적 + 활동량/인지도 | 로그 면적 (log_area)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1) | LightGBM | 0.4608 | 3.0955 | 0.3266 | 0.8898 | 0.5416 |
| 11 | 93.1964 | 호수 + 활동량/인지도 | 로그 호수 (ln_estimated_ho)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1) | LightGBM | 0.4673 | 3.1003 | 0.3088 | 0.8927 | 0.5386 |
| 12 | 94.9232 | 면적 + 활동량/인지도 + 활동량/인지도 x 면적 | 로그 면적 (log_area)<br>작가 전체 작품 수 (artist_meta_total_works)<br>판매 중 작품 수 (artist_meta_for_sale_works)<br>팔로워 수 (artist_meta_followers)<br>주요 작가 여부 (artist_meta_is_p1)<br>작가 전체 작품 수 x 로그 면적 (artist_meta_total_works_x_log_area)<br>판매 중 작품 수 x 로그 면적 (artist_meta_for_sale_works_x_log_area)<br>팔로워 수 x 로그 면적 (artist_meta_followers_x_log_area)<br>주요 작가 여부 x 로그 면적 (artist_meta_is_p1_x_log_area) | LightGBM | 0.4516 | 3.1609 | 0.3153 | 0.8883 | 0.5431 |

## 추가로 해볼 실험

- Warm 후속 1: `작가명 + 전체 크기 + 작가명 x 면적`을 상위 10명, 20명, 40명으로 바꿔 계산 비용과 p95 변화를 비교한다.
- Warm 후속 2: Huber 수렴 경고가 반복되므로 `Ridge`와 `Linear Regression` 기준에서 p95 안정성을 우선하는 운영 후보를 따로 비교한다.
- Cold 후속 1: `작품 기본 피처 + 활동량/인지도 + CatBoost`를 1순위 기준으로 두고, `활동량/인지도 x 면적`와 `활동량/인지도 x 호수 안정성 후보` LightGBM 후보를 가격 범위/신뢰도 경고 비교 대상으로 둔다. Cold는 단일 가격만 보여주기에는 p95가 크다.
- Cold 후속 2: `활동량/인지도 x 면적`과 `활동량/인지도 x 호수`를 둘 다 넣으면 MdAPE가 오히려 나빠졌으므로, 상호작용은 하나씩 선택하는 방향이 더 적절하다.
- Cold 후속 3: Cold 저위험/고위험 구간을 나누어 CatBoost, LightGBM, Quantile-LAD 후보를 라우팅하는 실험을 추가한다.

## 실행 메모

- `OPT-C2`는 정상 완료했다.
- `OPT-W2`, `OPT-W2L`은 작가 상호작용 차원이 커 Huber 반복 학습 시간이 과도해 중단하고, 핵심 조합만 남긴 `OPT-W3`로 재실행했다.
- 중단된 실험은 최종 성능 비교에는 포함하지 않았다.
