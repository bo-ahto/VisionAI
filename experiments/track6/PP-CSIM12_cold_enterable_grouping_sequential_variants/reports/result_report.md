# Cold enterable 그룹핑/순차 학습 변형 검증

- 작성일: 2026-06-18T16:33:29
- 목적: 현재 권장 Cold 후보인 enterable_only 계열에서 유사작품 그룹핑과 순차 잔차 보정 변형으로 성능 개선 여지를 확인한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.

## 1. Test 결과: MdAPE 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | top_k | model_type | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enterable_k160_q45 | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 160 | quantile | enterable + 유사작품 k160 통계 + LightGBM q45 |
| enterable_k160_q45_residual_s0p5_cap0p05 | test | 0.499501 | 1.131638 | 2.576805 | 0.911879 | 0.319458 | 0.501129 | 615 | 310 | 69 | 43 | 160 | q45_plus_residual | k160 q45 기준가격 + LightGBM residual * 0.5 clip ±0.05 |
| enterable_k160_q45_residual_s0p35_cap0p08 | test | 0.500711 | 1.134913 | 2.652151 | 0.910843 | 0.320426 | 0.498225 | 635 | 311 | 72 | 43 | 160 | q45_plus_residual | k160 q45 기준가격 + LightGBM residual * 0.35 clip ±0.08 |
| enterable_k160_q45_residual_s0p5_cap0p1 | test | 0.502123 | 1.152689 | 2.704807 | 0.911986 | 0.320103 | 0.497903 | 645 | 321 | 75 | 43 | 160 | q45_plus_residual | k160 q45 기준가격 + LightGBM residual * 0.5 clip ±0.1 |
| enterable_k80_q45 | test | 0.507116 | 1.069322 | 2.666641 | 0.915636 | 0.302356 | 0.493708 | 596 | 308 | 84 | 44 | 80 | quantile | enterable + 유사작품 k80 통계 + LightGBM q45 |
| enterable_k320_q45 | test | 0.511586 | 1.065470 | 2.516942 | 0.904464 | 0.312682 | 0.491449 | 580 | 281 | 70 | 42 | 320 | quantile | enterable + 유사작품 k320 통계 + LightGBM q45 |
| enterable_multi_k80_160_320_q45 | test | 0.516971 | 1.046947 | 2.674021 | 0.912032 | 0.306551 | 0.488222 | 627 | 293 | 78 | 44 | 80,160,320 | quantile | enterable + 유사작품 k80/k160/k320 통계 동시 사용 + LightGBM q45 |

## 2. Test 결과: APE > 5 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | top_k | model_type | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enterable_k160_q45 | test | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 0.322039 | 0.503066 | 578 | 232 | 66 | 43 | 160 | quantile | enterable + 유사작품 k160 통계 + LightGBM q45 |
| enterable_k160_q45_residual_s0p5_cap0p05 | test | 0.499501 | 1.131638 | 2.576805 | 0.911879 | 0.319458 | 0.501129 | 615 | 310 | 69 | 43 | 160 | q45_plus_residual | k160 q45 기준가격 + LightGBM residual * 0.5 clip ±0.05 |
| enterable_k320_q45 | test | 0.511586 | 1.065470 | 2.516942 | 0.904464 | 0.312682 | 0.491449 | 580 | 281 | 70 | 42 | 320 | quantile | enterable + 유사작품 k320 통계 + LightGBM q45 |
| enterable_k160_q45_residual_s0p35_cap0p08 | test | 0.500711 | 1.134913 | 2.652151 | 0.910843 | 0.320426 | 0.498225 | 635 | 311 | 72 | 43 | 160 | q45_plus_residual | k160 q45 기준가격 + LightGBM residual * 0.35 clip ±0.08 |
| enterable_k160_q45_residual_s0p5_cap0p1 | test | 0.502123 | 1.152689 | 2.704807 | 0.911986 | 0.320103 | 0.497903 | 645 | 321 | 75 | 43 | 160 | q45_plus_residual | k160 q45 기준가격 + LightGBM residual * 0.5 clip ±0.1 |
| enterable_multi_k80_160_320_q45 | test | 0.516971 | 1.046947 | 2.674021 | 0.912032 | 0.306551 | 0.488222 | 627 | 293 | 78 | 44 | 80,160,320 | quantile | enterable + 유사작품 k80/k160/k320 통계 동시 사용 + LightGBM q45 |
| enterable_k80_q45 | test | 0.507116 | 1.069322 | 2.666641 | 0.915636 | 0.302356 | 0.493708 | 596 | 308 | 84 | 44 | 80 | quantile | enterable + 유사작품 k80 통계 + LightGBM q45 |

## 3. 가격대별 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enterable_k160_q45 | test | 1m_3m | 866 | 0.509186 | 0.915907 | 2.500168 | 0.726037 | 75 | 8 |
| enterable_k160_q45_residual_s0p35_cap0p08 | test | 1m_3m | 866 | 0.504693 | 0.958591 | 2.779057 | 0.738029 | 100 | 8 |
| enterable_k160_q45_residual_s0p5_cap0p05 | test | 1m_3m | 866 | 0.505097 | 0.958147 | 2.676184 | 0.738782 | 102 | 9 |
| enterable_k160_q45_residual_s0p5_cap0p1 | test | 1m_3m | 866 | 0.513264 | 0.975338 | 2.823011 | 0.743098 | 109 | 9 |
| enterable_k320_q45 | test | 1m_3m | 866 | 0.535265 | 0.913574 | 2.576772 | 0.727741 | 82 | 8 |
| enterable_k80_q45 | test | 1m_3m | 866 | 0.540816 | 0.892412 | 2.785166 | 0.730024 | 89 | 10 |
| enterable_multi_k80_160_320_q45 | test | 1m_3m | 866 | 0.568910 | 0.866072 | 2.686212 | 0.721552 | 78 | 7 |
| enterable_k160_q45 | test | 3m_10m | 1057 | 0.429399 | 0.512366 | 1.222818 | 0.706357 | 15 | 2 |
| enterable_k160_q45_residual_s0p35_cap0p08 | test | 3m_10m | 1057 | 0.444782 | 0.529257 | 1.318153 | 0.693427 | 17 | 3 |
| enterable_k160_q45_residual_s0p5_cap0p05 | test | 3m_10m | 1057 | 0.445867 | 0.527475 | 1.321914 | 0.697189 | 16 | 3 |
| enterable_k160_q45_residual_s0p5_cap0p1 | test | 3m_10m | 1057 | 0.460101 | 0.536223 | 1.341270 | 0.690608 | 17 | 3 |
| enterable_k320_q45 | test | 3m_10m | 1057 | 0.445811 | 0.510862 | 1.242327 | 0.694277 | 13 | 2 |
| enterable_k80_q45 | test | 3m_10m | 1057 | 0.451395 | 0.535400 | 1.291910 | 0.713795 | 22 | 4 |
| enterable_multi_k80_160_320_q45 | test | 3m_10m | 1057 | 0.451212 | 0.528915 | 1.317214 | 0.708952 | 18 | 4 |
| enterable_k160_q45 | test | gt_10m | 636 | 0.459469 | 0.478404 | 0.898497 | 1.100473 | 0 | 0 |
| enterable_k160_q45_residual_s0p35_cap0p08 | test | gt_10m | 636 | 0.439493 | 0.470437 | 0.896645 | 1.075176 | 0 | 0 |
| enterable_k160_q45_residual_s0p5_cap0p05 | test | gt_10m | 636 | 0.443325 | 0.471440 | 0.894063 | 1.080303 | 0 | 0 |
| enterable_k160_q45_residual_s0p5_cap0p1 | test | gt_10m | 636 | 0.433056 | 0.468420 | 0.896682 | 1.067507 | 0 | 0 |
| enterable_k320_q45 | test | gt_10m | 636 | 0.454713 | 0.486211 | 0.901822 | 1.097913 | 0 | 0 |
| enterable_k80_q45 | test | gt_10m | 636 | 0.458247 | 0.483377 | 0.904944 | 1.106308 | 0 | 0 |
| enterable_multi_k80_160_320_q45 | test | gt_10m | 636 | 0.463627 | 0.483260 | 0.905209 | 1.102034 | 0 | 0 |
| enterable_k160_q45 | test | lt_1m | 540 | 0.880594 | 3.200176 | 24.822371 | 1.225420 | 142 | 56 |
| enterable_k160_q45_residual_s0p35_cap0p08 | test | lt_1m | 540 | 1.014388 | 3.385802 | 26.053284 | 1.258947 | 194 | 61 |
| enterable_k160_q45_residual_s0p5_cap0p05 | test | lt_1m | 540 | 0.971774 | 3.370028 | 26.133216 | 1.253296 | 192 | 57 |
| enterable_k160_q45_residual_s0p5_cap0p1 | test | lt_1m | 540 | 1.064583 | 3.449701 | 26.383828 | 1.269589 | 195 | 63 |
| enterable_k320_q45 | test | lt_1m | 540 | 0.972515 | 3.076901 | 22.754243 | 1.217446 | 186 | 60 |
| enterable_k80_q45 | test | lt_1m | 540 | 0.973701 | 3.088249 | 22.671031 | 1.232048 | 197 | 70 |
| enterable_multi_k80_160_320_q45 | test | lt_1m | 540 | 1.046857 | 3.014914 | 21.563368 | 1.234694 | 197 | 67 |

## 4. 결론

- MdAPE 기준 최상위 후보는 `enterable_k160_q45`이다.
- APE > 5 안정성 기준 최상위 후보는 `enterable_k160_q45`이다.
- 순차 residual 후보는 q45 기준가격을 먼저 만든 뒤, OOF basis residual을 학습하고 clip된 보정만 더한다.
- 최종 채택은 MdAPE/MAPE 개선뿐 아니라 p95와 APE > 5 악화 여부를 함께 봐야 한다.