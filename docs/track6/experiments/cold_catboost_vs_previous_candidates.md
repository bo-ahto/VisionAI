# Cold CatBoost가 기존 실험 결론을 뒤집는지 비교

## 결론

- CatBoost는 Cold 대표 오차 기준으로 기존 A~J/OPT 최고 후보를 소폭 앞선다.
- 같은 피처 조합 안에서 LightGBM보다 CatBoost가 더 좋게 나와 모델 변경 근거가 있다.
- 다만 p95_APE, RMSE_log, R2 기준에서는 OPT-C2 LightGBM 안정성 후보가 일부 더 좋다.
- 따라서 결론은 `CatBoost 단독 확정`이 아니라 `Cold 1순위 CatBoost + 안정성 보조 LightGBM`이 맞다.

## 판단 기준

- 1순위: MdAPE가 낮은가.
- 2순위: p95_APE가 낮아 큰 오차 위험이 줄었는가.
- 3순위: Within_30이 높아 30% 이내 적중률이 좋아졌는가.
- 4순위: RMSE_log는 낮고 R2는 높은가.
- 보조 판단: 같은 피처 조합에서 모델만 바꿨을 때도 CatBoost가 이겼는가.

## 후보 성능 비교

| 구분 | 후보명 | 모델 | MdAPE | p95_APE | Within_30 | RMSE_log | R2 | 종합점수 | 실제 사용 피처 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| CM1 모델군 비교 | CatBoost 최종 후보: 작품 기본 피처 + 활동량/인지도 | CatBoost | 0.4488 | 2.9885 | 0.3304 | 0.8797 | 0.5519 | 94.0240 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1 |
| 기존 A~J/OPT | 기존 MdAPE 최저: J5 활동량/인지도 x 면적 + LightGBM | LightGBM | 0.4516 | 3.1609 | 0.3153 | 0.8883 | 0.5431 |  | log_area, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_total_works_x_log_area, artist_meta_for_sale_works_x_log_area, artist_meta_followers_x_log_area, artist_meta_is_p1_x_log_area |
| 기존 A~J/OPT | 기존 안정성 후보: OPT-C2 활동량/인지도 x 호수 + LightGBM | LightGBM | 0.4579 | 2.7983 | 0.3085 | 0.8645 | 0.5673 |  | ln_estimated_ho, log_area, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing, total_works_x_ln_ho, followers_x_ln_ho, for_sale_works_x_ln_ho |
| 기존 A~J/OPT | 기존 기본+활동량 후보: G6 + LightGBM | LightGBM | 0.4577 | 2.9056 | 0.3246 | 0.8742 | 0.5576 |  | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing |
| CM1 모델군 비교 | 같은 피처 비교: CM1-F2 + LightGBM | LightGBM | 0.4621 | 3.1539 | 0.3214 | 0.8847 | 0.5469 | 84.9811 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1 |
| CM1 모델군 비교 | 같은 피처 비교: CM1-F2 + HistGradientBoosting | HistGradientBoosting | 0.4601 | 3.2319 | 0.3437 | 0.8699 | 0.5619 | 88.6962 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1 |

## CatBoost 기준 차이

| 비교 대상 | MdAPE 판정 | MdAPE 상대개선율 | p95_APE 판정 | p95_APE 상대개선율 | Within_30 판정 | Within_30 상대개선율 | RMSE_log 판정 | R2 판정 |
|---|---|---:|---|---:|---|---:|---|---|
| 기존 MdAPE 최저: J5 활동량/인지도 x 면적 + LightGBM | CatBoost 우세 | 0.62% | CatBoost 우세 | 5.45% | CatBoost 우세 | 4.81% | CatBoost 우세 | CatBoost 우세 |
| 기존 안정성 후보: OPT-C2 활동량/인지도 x 호수 + LightGBM | CatBoost 우세 | 2.00% | 기존 후보 우세 | -6.80% | CatBoost 우세 | 7.11% | 기존 후보 우세 | 기존 후보 우세 |
| 기존 기본+활동량 후보: G6 + LightGBM | CatBoost 우세 | 1.94% | 기존 후보 우세 | -2.85% | CatBoost 우세 | 1.79% | 기존 후보 우세 | 기존 후보 우세 |
| 같은 피처 비교: CM1-F2 + LightGBM | CatBoost 우세 | 2.88% | CatBoost 우세 | 5.24% | CatBoost 우세 | 2.81% | CatBoost 우세 | CatBoost 우세 |
| 같은 피처 비교: CM1-F2 + HistGradientBoosting | CatBoost 우세 | 2.46% | CatBoost 우세 | 7.53% | 기존 후보 우세 | -3.85% | 기존 후보 우세 | 기존 후보 우세 |

## 판정 요약

| 판단 항목 | 판정 | 근거 | 운영 해석 |
|---|---|---|---|
| 대표 오차(MdAPE) | CatBoost 우세 | CM1 CatBoost 0.4488 < 기존 A~J/OPT 최저 J5 LightGBM 0.4516 | 결론을 CatBoost 쪽으로 수정할 근거가 있음 |
| 큰 오차 위험(p95_APE) | 부분 우세 | CatBoost 2.9885는 J5 3.1609보다 좋지만, OPT-C2 안정성 후보 2.7983보다는 나쁨 | CatBoost 단독 확정 대신 LightGBM 안정성 후보 유지 필요 |
| 30% 이내 적중률(Within_30) | CatBoost 우세 | CatBoost 0.3304 > J5 0.3153, OPT-C2 0.3085 | 실무 근사 적중률은 CatBoost가 더 좋음 |
| 로그 공간 안정성(RMSE_log/R2) | 기존 안정성 후보 일부 우세 | OPT-C2 LightGBM은 RMSE_log 0.8645, R2 0.5673으로 CatBoost보다 좋음 | 가격 범위/신뢰도 후처리 후보로 LightGBM 유지 |
| 같은 피처에서 모델 비교 | CatBoost 우세 | CM1-F2 같은 피처에서 CatBoost MdAPE 0.4488, LightGBM 0.4621 | 모델 자체 비교에서도 CatBoost 선택 근거가 있음 |

## 최종 해석

- 기존 A~J/OPT만 보면 Cold는 LightGBM 상위 후보가 많았다.
- CM1에서 같은 상위 피처 조합에 여러 모델을 다시 적용하니 CatBoost가 종합 1위였다.
- CatBoost는 `MdAPE`, `Within_30`, 같은 피처 모델 비교에서 결론을 바꿀 만큼 성과가 있다.
- 그러나 큰 오차 위험과 로그 공간 안정성은 LightGBM 후보가 일부 더 좋으므로 LightGBM은 버리지 않는다.
- 현재 문서 결론은 `Cold 1순위 CatBoost`, `Cold 안정성/후처리 보조 LightGBM`으로 두는 것이 가장 정확하다.
