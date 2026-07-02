# Cold adaptive-k / Quantile 유사작품 검증

- 작성일: 2026-06-19T10:36:03
- 목적: Cold 유사작품 개수 k와 Quantile/불확실성 기반 adaptive-k 선택이 의미 있는지 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, lookup 후처리, `search_*`, 외부 live 검색 미사용.
- k 후보: 40, 80, 120, 160, 200, 240, 320, 480, 640
- Quantile 후보: q35, q45, q50. q10/q90은 예측 불확실성 폭(q90-q10) 계산용.

## 1. 고정 k Test 성능: MAPE 기준
| candidate | family | split | top_k | alpha | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | adaptive_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k640_q35 | fixed_k | test | 640.000000 | q35 | 0.498496 | 0.944133 | 2.431232 | 0.937956 | 211 | 53 | 41 | nan | 유사작품 640건 통계 + LightGBM Quantile q35 |
| k320_q35 | fixed_k | test | 320.000000 | q35 | 0.508301 | 0.946180 | 2.190874 | 0.934777 | 209 | 59 | 40 | nan | 유사작품 320건 통계 + LightGBM Quantile q35 |
| k40_q35 | fixed_k | test | 40.000000 | q35 | 0.525402 | 0.958516 | 2.285429 | 0.956173 | 195 | 69 | 45 | nan | 유사작품 40건 통계 + LightGBM Quantile q35 |
| k240_q35 | fixed_k | test | 240.000000 | q35 | 0.507210 | 0.968201 | 2.533838 | 0.945549 | 210 | 58 | 40 | nan | 유사작품 240건 통계 + LightGBM Quantile q35 |
| k80_q35 | fixed_k | test | 80.000000 | q35 | 0.506315 | 0.969216 | 2.543680 | 0.951335 | 215 | 58 | 41 | nan | 유사작품 80건 통계 + LightGBM Quantile q35 |
| k160_q35 | fixed_k | test | 160.000000 | q35 | 0.495018 | 0.971691 | 2.090436 | 0.943144 | 163 | 58 | 40 | nan | 유사작품 160건 통계 + LightGBM Quantile q35 |
| k120_q35 | fixed_k | test | 120.000000 | q35 | 0.504265 | 0.980088 | 2.751208 | 0.956450 | 214 | 60 | 40 | nan | 유사작품 120건 통계 + LightGBM Quantile q35 |
| k200_q35 | fixed_k | test | 200.000000 | q35 | 0.516875 | 0.981006 | 2.364513 | 0.950109 | 213 | 65 | 40 | nan | 유사작품 200건 통계 + LightGBM Quantile q35 |
| k480_q35 | fixed_k | test | 480.000000 | q35 | 0.516426 | 0.987623 | 2.089975 | 0.947660 | 211 | 55 | 41 | nan | 유사작품 480건 통계 + LightGBM Quantile q35 |
| k640_q45 | fixed_k | test | 640.000000 | q45 | 0.515535 | 1.051303 | 2.471533 | 0.902014 | 259 | 62 | 43 | nan | 유사작품 640건 통계 + LightGBM Quantile q45 |
| k320_q45 | fixed_k | test | 320.000000 | q45 | 0.511586 | 1.065470 | 2.516942 | 0.904464 | 281 | 70 | 42 | nan | 유사작품 320건 통계 + LightGBM Quantile q45 |
| k80_q45 | fixed_k | test | 80.000000 | q45 | 0.507116 | 1.069322 | 2.666641 | 0.915636 | 308 | 84 | 44 | nan | 유사작품 80건 통계 + LightGBM Quantile q45 |
| k240_q45 | fixed_k | test | 240.000000 | q45 | 0.503517 | 1.078562 | 2.562228 | 0.912914 | 268 | 71 | 42 | nan | 유사작품 240건 통계 + LightGBM Quantile q45 |
| k480_q45 | fixed_k | test | 480.000000 | q45 | 0.521678 | 1.081844 | 2.521096 | 0.914812 | 279 | 63 | 43 | nan | 유사작품 480건 통계 + LightGBM Quantile q45 |
| k160_q45 | fixed_k | test | 160.000000 | q45 | 0.496699 | 1.086514 | 2.452153 | 0.909771 | 232 | 66 | 43 | nan | 유사작품 160건 통계 + LightGBM Quantile q45 |
| k120_q45 | fixed_k | test | 120.000000 | q45 | 0.518031 | 1.088309 | 2.767266 | 0.918459 | 276 | 73 | 42 | nan | 유사작품 120건 통계 + LightGBM Quantile q45 |
| k200_q45 | fixed_k | test | 200.000000 | q45 | 0.523661 | 1.091616 | 2.698641 | 0.918419 | 291 | 77 | 42 | nan | 유사작품 200건 통계 + LightGBM Quantile q45 |
| k40_q45 | fixed_k | test | 40.000000 | q45 | 0.505320 | 1.095720 | 3.518901 | 0.933291 | 288 | 97 | 46 | nan | 유사작품 40건 통계 + LightGBM Quantile q45 |
| k240_q50 | fixed_k | test | 240.000000 | q50 | 0.500537 | 1.131501 | 3.100104 | 0.907304 | 306 | 82 | 43 | nan | 유사작품 240건 통계 + LightGBM Quantile q50 |
| k320_q50 | fixed_k | test | 320.000000 | q50 | 0.502840 | 1.134290 | 3.148638 | 0.898789 | 287 | 77 | 43 | nan | 유사작품 320건 통계 + LightGBM Quantile q50 |
| k640_q50 | fixed_k | test | 640.000000 | q50 | 0.514266 | 1.138466 | 2.814681 | 0.908189 | 303 | 80 | 44 | nan | 유사작품 640건 통계 + LightGBM Quantile q50 |
| k480_q50 | fixed_k | test | 480.000000 | q50 | 0.504108 | 1.148634 | 3.024783 | 0.911358 | 300 | 72 | 44 | nan | 유사작품 480건 통계 + LightGBM Quantile q50 |
| k160_q50 | fixed_k | test | 160.000000 | q50 | 0.496943 | 1.164918 | 2.850111 | 0.906483 | 322 | 74 | 45 | nan | 유사작품 160건 통계 + LightGBM Quantile q50 |
| k200_q50 | fixed_k | test | 200.000000 | q50 | 0.506501 | 1.165988 | 2.952922 | 0.910461 | 313 | 82 | 46 | nan | 유사작품 200건 통계 + LightGBM Quantile q50 |
| k120_q50 | fixed_k | test | 120.000000 | q50 | 0.520777 | 1.169675 | 3.151543 | 0.919728 | 325 | 80 | 46 | nan | 유사작품 120건 통계 + LightGBM Quantile q50 |
| k40_q50 | fixed_k | test | 40.000000 | q50 | 0.512990 | 1.177573 | 4.081129 | 0.932162 | 333 | 101 | 50 | nan | 유사작품 40건 통계 + LightGBM Quantile q50 |
| k80_q50 | fixed_k | test | 80.000000 | q50 | 0.518242 | 1.180314 | 3.383914 | 0.926003 | 335 | 85 | 45 | nan | 유사작품 80건 통계 + LightGBM Quantile q50 |

## 2. 고정 k Validation 성능: MAPE 기준
| candidate | family | split | top_k | alpha | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | adaptive_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k40_q35 | fixed_k | validation | 40.000000 | q35 | 0.380835 | 0.471788 | 1.074980 | 0.686590 | 50 | 5 | 2 | nan | 유사작품 40건 통계 + LightGBM Quantile q35 |
| k320_q35 | fixed_k | validation | 320.000000 | q35 | 0.373800 | 0.472872 | 1.069764 | 0.674193 | 47 | 8 | 1 | nan | 유사작품 320건 통계 + LightGBM Quantile q35 |
| k160_q35 | fixed_k | validation | 160.000000 | q35 | 0.359201 | 0.475196 | 1.115400 | 0.673808 | 46 | 8 | 1 | nan | 유사작품 160건 통계 + LightGBM Quantile q35 |
| k120_q35 | fixed_k | validation | 120.000000 | q35 | 0.367219 | 0.478218 | 1.110508 | 0.676214 | 49 | 9 | 1 | nan | 유사작품 120건 통계 + LightGBM Quantile q35 |
| k240_q35 | fixed_k | validation | 240.000000 | q35 | 0.365096 | 0.481079 | 1.279865 | 0.677041 | 46 | 9 | 1 | nan | 유사작품 240건 통계 + LightGBM Quantile q35 |
| k640_q35 | fixed_k | validation | 640.000000 | q35 | 0.377712 | 0.481156 | 1.156095 | 0.682282 | 52 | 9 | 1 | nan | 유사작품 640건 통계 + LightGBM Quantile q35 |
| k200_q35 | fixed_k | validation | 200.000000 | q35 | 0.365265 | 0.486289 | 1.319110 | 0.681325 | 49 | 8 | 1 | nan | 유사작품 200건 통계 + LightGBM Quantile q35 |
| k80_q35 | fixed_k | validation | 80.000000 | q35 | 0.376067 | 0.488890 | 1.265712 | 0.688318 | 52 | 9 | 2 | nan | 유사작품 80건 통계 + LightGBM Quantile q35 |
| k480_q35 | fixed_k | validation | 480.000000 | q35 | 0.384945 | 0.497493 | 1.359877 | 0.691932 | 52 | 10 | 1 | nan | 유사작품 480건 통계 + LightGBM Quantile q35 |
| k40_q45 | fixed_k | validation | 40.000000 | q45 | 0.368136 | 0.540082 | 1.560580 | 0.663577 | 84 | 19 | 4 | nan | 유사작품 40건 통계 + LightGBM Quantile q45 |
| k160_q45 | fixed_k | validation | 160.000000 | q45 | 0.365821 | 0.540571 | 1.471871 | 0.655823 | 73 | 18 | 4 | nan | 유사작품 160건 통계 + LightGBM Quantile q45 |
| k200_q45 | fixed_k | validation | 200.000000 | q45 | 0.363221 | 0.541898 | 1.539059 | 0.657601 | 81 | 16 | 4 | nan | 유사작품 200건 통계 + LightGBM Quantile q45 |
| k320_q45 | fixed_k | validation | 320.000000 | q45 | 0.383255 | 0.547801 | 1.489478 | 0.660853 | 69 | 12 | 4 | nan | 유사작품 320건 통계 + LightGBM Quantile q45 |
| k80_q45 | fixed_k | validation | 80.000000 | q45 | 0.360112 | 0.551619 | 1.445794 | 0.659987 | 79 | 19 | 4 | nan | 유사작품 80건 통계 + LightGBM Quantile q45 |
| k240_q45 | fixed_k | validation | 240.000000 | q45 | 0.357207 | 0.552466 | 1.697696 | 0.659058 | 88 | 13 | 4 | nan | 유사작품 240건 통계 + LightGBM Quantile q45 |
| k640_q45 | fixed_k | validation | 640.000000 | q45 | 0.397686 | 0.554299 | 1.595951 | 0.665065 | 74 | 13 | 5 | nan | 유사작품 640건 통계 + LightGBM Quantile q45 |
| k120_q45 | fixed_k | validation | 120.000000 | q45 | 0.374071 | 0.573769 | 1.690910 | 0.673516 | 85 | 14 | 3 | nan | 유사작품 120건 통계 + LightGBM Quantile q45 |
| k480_q45 | fixed_k | validation | 480.000000 | q45 | 0.394646 | 0.580106 | 1.739392 | 0.673470 | 103 | 16 | 4 | nan | 유사작품 480건 통계 + LightGBM Quantile q45 |
| k40_q50 | fixed_k | validation | 40.000000 | q50 | 0.374611 | 0.586586 | 1.648890 | 0.658404 | 101 | 22 | 4 | nan | 유사작품 40건 통계 + LightGBM Quantile q50 |
| k200_q50 | fixed_k | validation | 200.000000 | q50 | 0.365201 | 0.592894 | 1.748593 | 0.659397 | 94 | 21 | 4 | nan | 유사작품 200건 통계 + LightGBM Quantile q50 |
| k480_q50 | fixed_k | validation | 480.000000 | q50 | 0.381865 | 0.594473 | 1.835309 | 0.664473 | 110 | 24 | 4 | nan | 유사작품 480건 통계 + LightGBM Quantile q50 |
| k640_q50 | fixed_k | validation | 640.000000 | q50 | 0.357638 | 0.600456 | 1.910332 | 0.664146 | 122 | 24 | 5 | nan | 유사작품 640건 통계 + LightGBM Quantile q50 |
| k160_q50 | fixed_k | validation | 160.000000 | q50 | 0.377243 | 0.607980 | 1.711060 | 0.668099 | 101 | 24 | 8 | nan | 유사작품 160건 통계 + LightGBM Quantile q50 |
| k240_q50 | fixed_k | validation | 240.000000 | q50 | 0.369079 | 0.609123 | 1.926731 | 0.669432 | 129 | 21 | 4 | nan | 유사작품 240건 통계 + LightGBM Quantile q50 |
| k320_q50 | fixed_k | validation | 320.000000 | q50 | 0.377881 | 0.622638 | 1.907816 | 0.675386 | 123 | 23 | 4 | nan | 유사작품 320건 통계 + LightGBM Quantile q50 |
| k120_q50 | fixed_k | validation | 120.000000 | q50 | 0.376374 | 0.625297 | 1.915950 | 0.676813 | 106 | 25 | 4 | nan | 유사작품 120건 통계 + LightGBM Quantile q50 |
| k80_q50 | fixed_k | validation | 80.000000 | q50 | 0.379143 | 0.627152 | 1.876562 | 0.677758 | 125 | 24 | 4 | nan | 유사작품 80건 통계 + LightGBM Quantile q50 |

## 3. adaptive-k Validation 성능: MAPE 기준
| candidate | family | split | top_k | alpha | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | adaptive_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low_or_ref_low_and_k320_lower | adaptive_low_tail | validation | nan | q35 | 0.389339 | 0.464977 | 1.023729 | 0.684838 | 44 | 8 | 1 | 0.482020 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k320 q35가 k160 q35보다 낮으면 k320, 아니면 k160 |
| low_or_ref_low_and_k640_lower | adaptive_low_tail | validation | nan | q35 | 0.386585 | 0.465853 | 1.050889 | 0.689504 | 42 | 8 | 1 | 0.400654 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k640 q35가 k160 q35보다 낮으면 k640, 아니면 k160 |
| low_or_ref_low_and_k240_lower | adaptive_low_tail | validation | nan | q35 | 0.357966 | 0.466484 | 1.071175 | 0.682877 | 43 | 8 | 1 | 0.414820 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k240 q35가 k160 q35보다 낮으면 k240, 아니면 k160 |
| uncertain_and_k640_lower | adaptive_qwidth_lower | validation | nan | q35 | 0.353212 | 0.466771 | 1.071175 | 0.684266 | 42 | 8 | 1 | 0.179441 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k640 q35가 k160 q35보다 낮으면 k640, 아니면 k160 |
| low_or_ref_low_and_k200_lower | adaptive_low_tail | validation | nan | q35 | 0.360553 | 0.467032 | 1.071175 | 0.683551 | 44 | 8 | 1 | 0.407555 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k200 q35가 k160 q35보다 낮으면 k200, 아니면 k160 |
| uncertain_and_k320_lower | adaptive_qwidth_lower | validation | nan | q35 | 0.355152 | 0.468266 | 1.071175 | 0.681885 | 44 | 8 | 1 | 0.176898 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k320 q35가 k160 q35보다 낮으면 k320, 아니면 k160 |
| uncertain_and_k480_lower | adaptive_qwidth_lower | validation | nan | q35 | 0.354259 | 0.468605 | 1.071175 | 0.683322 | 40 | 8 | 1 | 0.186705 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k480 q35가 k160 q35보다 낮으면 k480, 아니면 k160 |
| uncertain_and_k200_lower | adaptive_qwidth_lower | validation | nan | q35 | 0.355679 | 0.470392 | 1.096067 | 0.680126 | 45 | 8 | 1 | 0.182347 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k200 q35가 k160 q35보다 낮으면 k200, 아니면 k160 |
| uncertain_and_k240_lower | adaptive_qwidth_lower | validation | nan | q35 | 0.357822 | 0.470551 | 1.087417 | 0.681779 | 43 | 8 | 1 | 0.173629 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k240 q35가 k160 q35보다 낮으면 k240, 아니면 k160 |
| low_or_ref_low_and_k480_lower | adaptive_low_tail | validation | nan | q35 | 0.390521 | 0.471532 | 1.049788 | 0.692585 | 40 | 8 | 1 | 0.467853 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k480 q35가 k160 q35보다 낮으면 k480, 아니면 k160 |
| if_qwidth_q75_use_k200 | adaptive_qwidth | validation | nan | q35 | 0.351423 | 0.474171 | 1.115400 | 0.675919 | 46 | 8 | 1 | 0.250272 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k200 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k200 | adaptive_qwidth | validation | nan | q35 | 0.351423 | 0.474425 | 1.124522 | 0.675074 | 49 | 8 | 1 | 0.331275 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k200 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k320 | adaptive_qwidth | validation | nan | q35 | 0.352853 | 0.474715 | 1.076000 | 0.677023 | 48 | 8 | 1 | 0.250272 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k320 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k640 | adaptive_qwidth | validation | nan | q35 | 0.352506 | 0.474863 | 1.107118 | 0.677523 | 52 | 8 | 1 | 0.250272 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k640 q35, 아니면 k160 q35 |
| if_refiqr_q75_use_k480 | adaptive_ref_iqr | validation | nan | q35 | 0.353188 | 0.475439 | 1.077069 | 0.672515 | 48 | 10 | 1 | 0.250272 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k480 q35, 아니면 k160 q35 |
| if_refiqr_q75_use_k240 | adaptive_ref_iqr | validation | nan | q35 | 0.353833 | 0.475781 | 1.108537 | 0.675132 | 45 | 9 | 1 | 0.250272 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k240 q35, 아니면 k160 q35 |
| if_refiqr_q75_use_k640 | adaptive_ref_iqr | validation | nan | q35 | 0.353212 | 0.475908 | 1.087417 | 0.670764 | 48 | 9 | 1 | 0.250272 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k640 | adaptive_qwidth | validation | nan | q35 | 0.352506 | 0.475947 | 1.107118 | 0.678197 | 52 | 8 | 1 | 0.331275 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k240 | adaptive_qwidth | validation | nan | q35 | 0.352935 | 0.476353 | 1.124522 | 0.678013 | 47 | 8 | 1 | 0.250272 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k240 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k320 | adaptive_qwidth | validation | nan | q35 | 0.353212 | 0.476376 | 1.102205 | 0.676881 | 48 | 8 | 1 | 0.331275 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k320 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k480 | adaptive_qwidth | validation | nan | q35 | 0.351578 | 0.476694 | 1.074140 | 0.677775 | 49 | 9 | 1 | 0.250272 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k480 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k240 | adaptive_qwidth | validation | nan | q35 | 0.355679 | 0.476943 | 1.117529 | 0.677185 | 46 | 8 | 1 | 0.331275 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k240 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k480 | adaptive_qwidth | validation | nan | q35 | 0.352123 | 0.477323 | 1.080931 | 0.677698 | 49 | 9 | 1 | 0.331275 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k480 q35, 아니면 k160 q35 |
| if_refiqr_q75_use_k200 | adaptive_ref_iqr | validation | nan | q35 | 0.352685 | 0.477345 | 1.115514 | 0.675662 | 47 | 8 | 1 | 0.250272 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k200 q35, 아니면 k160 q35 |
| if_refiqr_q67_use_k320 | adaptive_ref_iqr | validation | nan | q35 | 0.355054 | 0.477699 | 1.124522 | 0.673561 | 47 | 8 | 1 | 0.330185 | k160 유사작품 가격 IQR이 validation refiqr_q67(1.0030) 이상이면 k320 q35, 아니면 k160 q35 |
| if_refiqr_q75_use_k320 | adaptive_ref_iqr | validation | nan | q35 | 0.355688 | 0.478352 | 1.106138 | 0.673557 | 47 | 8 | 1 | 0.250272 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k320 q35, 아니면 k160 q35 |
| if_refiqr_q50_use_k320 | adaptive_ref_iqr | validation | nan | q35 | 0.356362 | 0.478835 | 1.124522 | 0.675933 | 49 | 8 | 1 | 0.500182 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k320 q35, 아니면 k160 q35 |
| if_qwidth_q50_use_k320 | adaptive_qwidth | validation | nan | q35 | 0.355321 | 0.480309 | 1.108614 | 0.677508 | 48 | 8 | 1 | 0.500182 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q50(1.3502) 이상이면 k320 q35, 아니면 k160 q35 |
| if_refiqr_q67_use_k640 | adaptive_ref_iqr | validation | nan | q35 | 0.359162 | 0.481735 | 1.179401 | 0.673302 | 50 | 9 | 1 | 0.330185 | k160 유사작품 가격 IQR이 validation refiqr_q67(1.0030) 이상이면 k640 q35, 아니면 k160 q35 |
| if_refiqr_q50_use_k640 | adaptive_ref_iqr | validation | nan | q35 | 0.358227 | 0.483711 | 1.165541 | 0.679411 | 53 | 9 | 1 | 0.500182 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k640 q35, 아니면 k160 q35 |

## 4. adaptive-k Test 성능: MAPE 기준
| candidate | family | split | top_k | alpha | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | adaptive_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low_or_ref_low_and_k640_lower | adaptive_low_tail | test | nan | q35 | 0.496475 | 0.916058 | 1.997548 | 0.945764 | 154 | 53 | 40 | 0.415295 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k640 q35가 k160 q35보다 낮으면 k640, 아니면 k160 |
| low_or_ref_low_and_k320_lower | adaptive_low_tail | test | nan | q35 | 0.493347 | 0.917608 | 1.999310 | 0.941410 | 155 | 56 | 40 | 0.363343 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k320 q35가 k160 q35보다 낮으면 k320, 아니면 k160 |
| low_or_ref_low_and_k240_lower | adaptive_low_tail | test | nan | q35 | 0.493688 | 0.934137 | 2.001607 | 0.946467 | 156 | 54 | 40 | 0.402711 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k240 q35가 k160 q35보다 낮으면 k240, 아니면 k160 |
| uncertain_and_k320_lower | adaptive_qwidth_lower | test | nan | q35 | 0.497998 | 0.935989 | 1.999310 | 0.946301 | 155 | 55 | 40 | 0.263311 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k320 q35가 k160 q35보다 낮으면 k320, 아니면 k160 |
| low_or_ref_low_and_k200_lower | adaptive_low_tail | test | nan | q35 | 0.497998 | 0.939048 | 2.001313 | 0.948637 | 156 | 56 | 40 | 0.340755 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k200 q35가 k160 q35보다 낮으면 k200, 아니면 k160 |
| uncertain_and_k200_lower | adaptive_qwidth_lower | test | nan | q35 | 0.502835 | 0.942057 | 2.003293 | 0.952037 | 157 | 56 | 40 | 0.257825 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k200 q35가 k160 q35보다 낮으면 k200, 아니면 k160 |
| uncertain_and_k640_lower | adaptive_qwidth_lower | test | nan | q35 | 0.506511 | 0.943359 | 2.003293 | 0.953826 | 157 | 52 | 40 | 0.284608 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k640 q35가 k160 q35보다 낮으면 k640, 아니면 k160 |
| low_or_ref_low_and_k480_lower | adaptive_low_tail | test | nan | q35 | 0.501657 | 0.946647 | 1.973696 | 0.949348 | 152 | 54 | 40 | 0.374960 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k480 q35가 k160 q35보다 낮으면 k480, 아니면 k160 |
| if_qwidth_q75_use_k320 | adaptive_qwidth | test | nan | q35 | 0.496517 | 0.946651 | 2.212824 | 0.934870 | 205 | 58 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k320 q35, 아니면 k160 q35 |
| if_qwidth_q50_use_k320 | adaptive_qwidth | test | nan | q35 | 0.504647 | 0.948341 | 2.204838 | 0.935189 | 203 | 59 | 40 | 0.617619 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q50(1.3502) 이상이면 k320 q35, 아니면 k160 q35 |
| uncertain_and_k240_lower | adaptive_qwidth_lower | test | nan | q35 | 0.501991 | 0.949049 | 2.010825 | 0.951077 | 159 | 53 | 40 | 0.264924 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k240 q35가 k160 q35보다 낮으면 k240, 아니면 k160 |
| if_qwidth_q67_use_k320 | adaptive_qwidth | test | nan | q35 | 0.501991 | 0.949676 | 2.212824 | 0.935998 | 203 | 59 | 40 | 0.523395 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k320 q35, 아니면 k160 q35 |
| if_refiqr_q50_use_k320 | adaptive_ref_iqr | test | nan | q35 | 0.501991 | 0.949975 | 2.190874 | 0.934029 | 205 | 58 | 40 | 0.652469 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k320 q35, 아니면 k160 q35 |
| uncertain_and_k480_lower | adaptive_qwidth_lower | test | nan | q35 | 0.505804 | 0.952967 | 1.973696 | 0.954058 | 152 | 54 | 40 | 0.291384 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k480 q35가 k160 q35보다 낮으면 k480, 아니면 k160 |
| if_refiqr_q50_use_k640 | adaptive_ref_iqr | test | nan | q35 | 0.496475 | 0.954048 | 2.431232 | 0.938396 | 208 | 54 | 41 | 0.652469 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q50_use_k640 | adaptive_qwidth | test | nan | q35 | 0.505804 | 0.954357 | 2.431232 | 0.941893 | 209 | 53 | 41 | 0.617619 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q50(1.3502) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k200 | adaptive_qwidth | test | nan | q35 | 0.504518 | 0.959002 | 2.364513 | 0.946479 | 212 | 63 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k200 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k640 | adaptive_qwidth | test | nan | q35 | 0.501044 | 0.960122 | 2.431232 | 0.942990 | 208 | 53 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k200 | adaptive_qwidth | test | nan | q35 | 0.504735 | 0.962323 | 2.364513 | 0.947925 | 209 | 65 | 40 | 0.523395 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k200 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k640 | adaptive_qwidth | test | nan | q35 | 0.506468 | 0.965955 | 2.431232 | 0.944510 | 209 | 54 | 41 | 0.523395 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q50_use_k200 | adaptive_qwidth | test | nan | q35 | 0.505069 | 0.966101 | 2.364513 | 0.948007 | 209 | 64 | 40 | 0.617619 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q50(1.3502) 이상이면 k200 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k240 | adaptive_qwidth | test | nan | q35 | 0.502590 | 0.968190 | 2.533838 | 0.945757 | 209 | 54 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k240 q35, 아니면 k160 q35 |
| if_refiqr_q50_use_k200 | adaptive_ref_iqr | test | nan | q35 | 0.507641 | 0.968899 | 2.364513 | 0.947641 | 209 | 63 | 40 | 0.652469 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k200 q35, 아니면 k160 q35 |
| if_refiqr_q75_use_k320 | adaptive_ref_iqr | test | nan | q35 | 0.500857 | 0.968905 | 2.193069 | 0.937338 | 206 | 59 | 40 | 0.384640 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k320 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k240 | adaptive_qwidth | test | nan | q35 | 0.501991 | 0.969633 | 2.533838 | 0.946280 | 209 | 57 | 40 | 0.523395 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k240 q35, 아니면 k160 q35 |
| if_refiqr_q67_use_k320 | adaptive_ref_iqr | test | nan | q35 | 0.501181 | 0.970007 | 2.204838 | 0.936886 | 206 | 59 | 40 | 0.426589 | k160 유사작품 가격 IQR이 validation refiqr_q67(1.0030) 이상이면 k320 q35, 아니면 k160 q35 |
| if_qwidth_q50_use_k240 | adaptive_qwidth | test | nan | q35 | 0.502852 | 0.974527 | 2.533838 | 0.946497 | 209 | 57 | 40 | 0.617619 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q50(1.3502) 이상이면 k240 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k480 | adaptive_qwidth | test | nan | q35 | 0.501991 | 0.975213 | 2.053297 | 0.945922 | 204 | 54 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k480 q35, 아니면 k160 q35 |
| if_refiqr_q50_use_k240 | adaptive_ref_iqr | test | nan | q35 | 0.501512 | 0.975728 | 2.533838 | 0.945833 | 209 | 57 | 40 | 0.652469 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k240 q35, 아니면 k160 q35 |
| if_refiqr_q75_use_k480 | adaptive_ref_iqr | test | nan | q35 | 0.506328 | 0.977531 | 2.090470 | 0.945194 | 210 | 56 | 40 | 0.384640 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k480 q35, 아니면 k160 q35 |

## 5. Test 성능: APE > 5 기준
| candidate | family | split | top_k | alpha | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | adaptive_selected_rate | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| uncertain_and_k640_lower | adaptive_qwidth_lower | test | nan | q35 | 0.506511 | 0.943359 | 2.003293 | 0.953826 | 157 | 52 | 40 | 0.284608 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k640 q35가 k160 q35보다 낮으면 k640, 아니면 k160 |
| low_or_ref_low_and_k640_lower | adaptive_low_tail | test | nan | q35 | 0.496475 | 0.916058 | 1.997548 | 0.945764 | 154 | 53 | 40 | 0.415295 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k640 q35가 k160 q35보다 낮으면 k640, 아니면 k160 |
| k640_q35 | fixed_k | test | 640.000000 | q35 | 0.498496 | 0.944133 | 2.431232 | 0.937956 | 211 | 53 | 41 | nan | 유사작품 640건 통계 + LightGBM Quantile q35 |
| uncertain_and_k240_lower | adaptive_qwidth_lower | test | nan | q35 | 0.501991 | 0.949049 | 2.010825 | 0.951077 | 159 | 53 | 40 | 0.264924 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k240 q35가 k160 q35보다 낮으면 k240, 아니면 k160 |
| if_qwidth_q50_use_k640 | adaptive_qwidth | test | nan | q35 | 0.505804 | 0.954357 | 2.431232 | 0.941893 | 209 | 53 | 41 | 0.617619 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q50(1.3502) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k640 | adaptive_qwidth | test | nan | q35 | 0.501044 | 0.960122 | 2.431232 | 0.942990 | 208 | 53 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k640 q35, 아니면 k160 q35 |
| low_or_ref_low_and_k240_lower | adaptive_low_tail | test | nan | q35 | 0.493688 | 0.934137 | 2.001607 | 0.946467 | 156 | 54 | 40 | 0.402711 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k240 q35가 k160 q35보다 낮으면 k240, 아니면 k160 |
| low_or_ref_low_and_k480_lower | adaptive_low_tail | test | nan | q35 | 0.501657 | 0.946647 | 1.973696 | 0.949348 | 152 | 54 | 40 | 0.374960 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k480 q35가 k160 q35보다 낮으면 k480, 아니면 k160 |
| uncertain_and_k480_lower | adaptive_qwidth_lower | test | nan | q35 | 0.505804 | 0.952967 | 1.973696 | 0.954058 | 152 | 54 | 40 | 0.291384 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k480 q35가 k160 q35보다 낮으면 k480, 아니면 k160 |
| if_refiqr_q50_use_k640 | adaptive_ref_iqr | test | nan | q35 | 0.496475 | 0.954048 | 2.431232 | 0.938396 | 208 | 54 | 41 | 0.652469 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k640 | adaptive_qwidth | test | nan | q35 | 0.506468 | 0.965955 | 2.431232 | 0.944510 | 209 | 54 | 41 | 0.523395 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k240 | adaptive_qwidth | test | nan | q35 | 0.502590 | 0.968190 | 2.533838 | 0.945757 | 209 | 54 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k240 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k480 | adaptive_qwidth | test | nan | q35 | 0.501991 | 0.975213 | 2.053297 | 0.945922 | 204 | 54 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k480 q35, 아니면 k160 q35 |
| if_qwidth_q50_use_k480 | adaptive_qwidth | test | nan | q35 | 0.507905 | 0.982242 | 2.072743 | 0.947230 | 205 | 54 | 41 | 0.617619 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q50(1.3502) 이상이면 k480 q35, 아니면 k160 q35 |
| uncertain_and_k320_lower | adaptive_qwidth_lower | test | nan | q35 | 0.497998 | 0.935989 | 1.999310 | 0.946301 | 155 | 55 | 40 | 0.263311 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k320 q35가 k160 q35보다 낮으면 k320, 아니면 k160 |
| if_qwidth_q67_use_k480 | adaptive_qwidth | test | nan | q35 | 0.507905 | 0.979302 | 2.072743 | 0.947172 | 204 | 55 | 41 | 0.523395 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k480 q35, 아니면 k160 q35 |
| if_refiqr_q50_use_k480 | adaptive_ref_iqr | test | nan | q35 | 0.508690 | 0.985004 | 2.089942 | 0.945749 | 206 | 55 | 41 | 0.652469 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k480 q35, 아니면 k160 q35 |
| k480_q35 | fixed_k | test | 480.000000 | q35 | 0.516426 | 0.987623 | 2.089975 | 0.947660 | 211 | 55 | 41 | nan | 유사작품 480건 통계 + LightGBM Quantile q35 |
| low_or_ref_low_and_k320_lower | adaptive_low_tail | test | nan | q35 | 0.493347 | 0.917608 | 1.999310 | 0.941410 | 155 | 56 | 40 | 0.363343 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k320 q35가 k160 q35보다 낮으면 k320, 아니면 k160 |
| low_or_ref_low_and_k200_lower | adaptive_low_tail | test | nan | q35 | 0.497998 | 0.939048 | 2.001313 | 0.948637 | 156 | 56 | 40 | 0.340755 | k160 예측가 또는 유사작품 기준가가 800만원 미만이고 k200 q35가 k160 q35보다 낮으면 k200, 아니면 k160 |
| uncertain_and_k200_lower | adaptive_qwidth_lower | test | nan | q35 | 0.502835 | 0.942057 | 2.003293 | 0.952037 | 157 | 56 | 40 | 0.257825 | k160 q90-q10 예측 불확실성 폭이 validation q67 이상이고 k200 q35가 k160 q35보다 낮으면 k200, 아니면 k160 |
| if_refiqr_q75_use_k480 | adaptive_ref_iqr | test | nan | q35 | 0.506328 | 0.977531 | 2.090470 | 0.945194 | 210 | 56 | 40 | 0.384640 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k480 q35, 아니면 k160 q35 |
| if_refiqr_q75_use_k640 | adaptive_ref_iqr | test | nan | q35 | 0.501991 | 0.978243 | 2.431232 | 0.942560 | 209 | 56 | 40 | 0.384640 | k160 유사작품 가격 IQR이 validation refiqr_q75(1.0544) 이상이면 k640 q35, 아니면 k160 q35 |
| if_refiqr_q67_use_k480 | adaptive_ref_iqr | test | nan | q35 | 0.505804 | 0.978531 | 2.089975 | 0.944769 | 208 | 56 | 41 | 0.426589 | k160 유사작품 가격 IQR이 validation refiqr_q67(1.0030) 이상이면 k480 q35, 아니면 k160 q35 |
| if_refiqr_q67_use_k640 | adaptive_ref_iqr | test | nan | q35 | 0.501044 | 0.979842 | 2.431232 | 0.942251 | 209 | 56 | 41 | 0.426589 | k160 유사작품 가격 IQR이 validation refiqr_q67(1.0030) 이상이면 k640 q35, 아니면 k160 q35 |
| if_qwidth_q67_use_k240 | adaptive_qwidth | test | nan | q35 | 0.501991 | 0.969633 | 2.533838 | 0.946280 | 209 | 57 | 40 | 0.523395 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q67(1.5458) 이상이면 k240 q35, 아니면 k160 q35 |
| if_qwidth_q50_use_k240 | adaptive_qwidth | test | nan | q35 | 0.502852 | 0.974527 | 2.533838 | 0.946497 | 209 | 57 | 40 | 0.617619 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q50(1.3502) 이상이면 k240 q35, 아니면 k160 q35 |
| if_refiqr_q50_use_k240 | adaptive_ref_iqr | test | nan | q35 | 0.501512 | 0.975728 | 2.533838 | 0.945833 | 209 | 57 | 40 | 0.652469 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k240 q35, 아니면 k160 q35 |
| if_qwidth_q75_use_k320 | adaptive_qwidth | test | nan | q35 | 0.496517 | 0.946651 | 2.212824 | 0.934870 | 205 | 58 | 40 | 0.436915 | k160 q90-q10 예측 불확실성 폭이 validation qwidth_q75(1.7437) 이상이면 k320 q35, 아니면 k160 q35 |
| if_refiqr_q50_use_k320 | adaptive_ref_iqr | test | nan | q35 | 0.501991 | 0.949975 | 2.190874 | 0.934029 | 205 | 58 | 40 | 0.652469 | k160 유사작품 가격 IQR이 validation refiqr_q50(0.8022) 이상이면 k320 q35, 아니면 k160 q35 |

## 6. Paired bootstrap vs base k160 q35
| split | candidate_a | candidate_b | n | n_boot | delta_MdAPE_a_minus_b_mean | delta_MAPE_a_minus_b_mean | delta_p95_APE_a_minus_b_mean | p_delta_MAPE_a_minus_b_lt_0 | p_delta_p95_APE_a_minus_b_lt_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | low_or_ref_low_and_k320_lower | k160_q35 | 2753 | 800 | 0.029005 | -0.010221 | -0.089404 | 1.000000 | 1.000000 |
| validation | low_or_ref_low_and_k640_lower | k160_q35 | 2753 | 800 | 0.024349 | -0.009342 | -0.081920 | 1.000000 | 0.997500 |
| validation | low_or_ref_low_and_k240_lower | k160_q35 | 2753 | 800 | -0.000924 | -0.008684 | -0.029167 | 1.000000 | 0.817500 |
| validation | uncertain_and_k640_lower | k160_q35 | 2753 | 800 | -0.004750 | -0.008411 | -0.030771 | 1.000000 | 0.855000 |
| validation | low_or_ref_low_and_k200_lower | k160_q35 | 2753 | 800 | 0.000480 | -0.008136 | -0.048214 | 1.000000 | 0.956250 |
| validation | uncertain_and_k320_lower | k160_q35 | 2753 | 800 | -0.003719 | -0.006926 | -0.034860 | 1.000000 | 0.857500 |
| validation | uncertain_and_k480_lower | k160_q35 | 2753 | 800 | -0.004035 | -0.006564 | -0.038067 | 1.000000 | 0.908750 |
| validation | uncertain_and_k200_lower | k160_q35 | 2753 | 800 | -0.003273 | -0.004785 | -0.014447 | 1.000000 | 0.676250 |
| validation | uncertain_and_k240_lower | k160_q35 | 2753 | 800 | -0.001637 | -0.004629 | -0.016998 | 1.000000 | 0.677500 |
| validation | low_or_ref_low_and_k480_lower | k160_q35 | 2753 | 800 | 0.029975 | -0.003648 | -0.075368 | 0.982500 | 0.997500 |
| validation | k640_q35 | k160_q35 | 2753 | 800 | 0.018684 | 0.005840 | 0.068170 | 0.035000 | 0.028750 |
| validation | k320_q35 | k160_q35 | 2753 | 800 | 0.016655 | -0.002407 | -0.037066 | 0.800000 | 0.872500 |
| validation | if_qwidth_q50_use_k640 | k160_q35 | 2753 | 800 | -0.001315 | 0.010286 | 0.082579 | 0.000000 | 0.010000 |
| validation | if_qwidth_q75_use_k640 | k160_q35 | 2753 | 800 | -0.006435 | -0.000460 | -0.006513 | 0.578750 | 0.446250 |
| test | low_or_ref_low_and_k320_lower | k160_q35 | 3099 | 800 | -0.001179 | -0.054446 | -0.101067 | 1.000000 | 0.978750 |
| test | low_or_ref_low_and_k640_lower | k160_q35 | 3099 | 800 | -0.000806 | -0.056160 | -0.084631 | 1.000000 | 0.972500 |
| test | low_or_ref_low_and_k240_lower | k160_q35 | 3099 | 800 | -0.001614 | -0.037660 | -0.081449 | 1.000000 | 0.971250 |
| test | uncertain_and_k640_lower | k160_q35 | 3099 | 800 | 0.009108 | -0.028739 | -0.064297 | 1.000000 | 0.955000 |
| test | low_or_ref_low_and_k200_lower | k160_q35 | 3099 | 800 | 0.001344 | -0.032840 | -0.072476 | 1.000000 | 0.961250 |
| test | uncertain_and_k320_lower | k160_q35 | 3099 | 800 | 0.001524 | -0.036042 | -0.085083 | 1.000000 | 0.970000 |
| test | uncertain_and_k480_lower | k160_q35 | 3099 | 800 | 0.007992 | -0.018629 | -0.108556 | 1.000000 | 0.973750 |
| test | uncertain_and_k200_lower | k160_q35 | 3099 | 800 | 0.005167 | -0.029811 | -0.063250 | 1.000000 | 0.958750 |
| test | uncertain_and_k240_lower | k160_q35 | 3099 | 800 | 0.003123 | -0.022756 | -0.055327 | 1.000000 | 0.938750 |
| test | low_or_ref_low_and_k480_lower | k160_q35 | 3099 | 800 | 0.003671 | -0.024905 | -0.105507 | 1.000000 | 0.973750 |
| test | k640_q35 | k160_q35 | 3099 | 800 | 0.001249 | -0.027913 | 0.334949 | 0.985000 | 0.002500 |
| test | k320_q35 | k160_q35 | 3099 | 800 | 0.010896 | -0.025873 | 0.122731 | 0.986250 | 0.125000 |
| test | if_qwidth_q50_use_k640 | k160_q35 | 3099 | 800 | 0.006863 | -0.017563 | 0.333000 | 0.866250 | 0.002500 |
| test | if_qwidth_q75_use_k640 | k160_q35 | 3099 | 800 | 0.002323 | -0.011799 | 0.327294 | 0.763750 | 0.007500 |

## 7. 가격대별 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| if_qwidth_q50_use_k640 | test | 1m_3m | 866 | 0.445483 | 0.771168 | 2.059044 | 48 | 4 | 2 |
| if_qwidth_q50_use_k640 | test | 3m_10m | 1057 | 0.449487 | 0.472081 | 0.891376 | 6 | 2 | 0 |
| if_qwidth_q50_use_k640 | test | gt_10m | 636 | 0.558168 | 0.555340 | 0.910363 | 0 | 0 | 0 |
| if_qwidth_q50_use_k640 | test | lt_1m | 540 | 0.816242 | 2.662099 | 20.253455 | 155 | 47 | 39 |
| if_qwidth_q50_use_k640 | validation | 1m_3m | 846 | 0.323855 | 0.405464 | 1.124522 | 7 | 0 | 0 |
| if_qwidth_q50_use_k640 | validation | 3m_10m | 903 | 0.408470 | 0.424161 | 0.773093 | 2 | 0 | 0 |
| if_qwidth_q50_use_k640 | validation | gt_10m | 374 | 0.497798 | 0.504702 | 0.863856 | 0 | 0 | 0 |
| if_qwidth_q50_use_k640 | validation | lt_1m | 630 | 0.316941 | 0.669899 | 2.548683 | 44 | 8 | 1 |
| k160_q35 | test | 1m_3m | 866 | 0.449293 | 0.775798 | 2.215003 | 51 | 6 | 2 |
| k160_q35 | test | 3m_10m | 1057 | 0.464583 | 0.482630 | 0.895791 | 7 | 2 | 0 |
| k160_q35 | test | gt_10m | 636 | 0.554615 | 0.547219 | 0.909412 | 0 | 0 | 0 |
| k160_q35 | test | lt_1m | 540 | 0.695267 | 2.743070 | 20.911669 | 105 | 50 | 38 |
| k160_q35 | validation | 1m_3m | 846 | 0.317789 | 0.397369 | 1.124522 | 7 | 0 | 0 |
| k160_q35 | validation | 3m_10m | 903 | 0.415972 | 0.421715 | 0.774961 | 2 | 0 | 0 |
| k160_q35 | validation | gt_10m | 374 | 0.489243 | 0.502903 | 0.862685 | 0 | 0 | 0 |
| k160_q35 | validation | lt_1m | 630 | 0.316941 | 0.639914 | 2.399600 | 37 | 8 | 1 |
| k640_q35 | test | 1m_3m | 866 | 0.461835 | 0.773323 | 2.111891 | 51 | 4 | 2 |
| k640_q35 | test | 3m_10m | 1057 | 0.450112 | 0.472129 | 0.898972 | 6 | 2 | 0 |
| k640_q35 | test | gt_10m | 636 | 0.557273 | 0.555337 | 0.910363 | 0 | 0 | 0 |
| k640_q35 | test | lt_1m | 540 | 0.854378 | 2.599879 | 20.253455 | 154 | 47 | 39 |
| k640_q35 | validation | 1m_3m | 846 | 0.325028 | 0.406357 | 1.006606 | 7 | 0 | 0 |
| k640_q35 | validation | 3m_10m | 903 | 0.396726 | 0.415258 | 0.773093 | 2 | 0 | 0 |
| k640_q35 | validation | gt_10m | 374 | 0.485522 | 0.501886 | 0.863138 | 0 | 0 | 0 |
| k640_q35 | validation | lt_1m | 630 | 0.365550 | 0.663750 | 2.548683 | 43 | 9 | 1 |
| low_or_ref_low_and_k200_lower | test | 1m_3m | 866 | 0.456749 | 0.758231 | 2.060400 | 47 | 6 | 2 |
| low_or_ref_low_and_k200_lower | test | 3m_10m | 1057 | 0.468990 | 0.480750 | 0.896380 | 7 | 2 | 0 |
| low_or_ref_low_and_k200_lower | test | gt_10m | 636 | 0.558025 | 0.551446 | 0.909872 | 0 | 0 | 0 |
| low_or_ref_low_and_k200_lower | test | lt_1m | 540 | 0.627793 | 2.582609 | 20.716356 | 102 | 48 | 38 |
| low_or_ref_low_and_k200_lower | validation | 1m_3m | 846 | 0.318764 | 0.392841 | 0.941679 | 6 | 0 | 0 |
| low_or_ref_low_and_k200_lower | validation | 3m_10m | 903 | 0.424945 | 0.426506 | 0.777515 | 2 | 0 | 0 |
| low_or_ref_low_and_k200_lower | validation | gt_10m | 374 | 0.499078 | 0.508522 | 0.863789 | 0 | 0 | 0 |
| low_or_ref_low_and_k200_lower | validation | lt_1m | 630 | 0.316941 | 0.600118 | 2.316039 | 36 | 8 | 1 |
| low_or_ref_low_and_k240_lower | test | 1m_3m | 866 | 0.449205 | 0.742953 | 2.039879 | 46 | 6 | 2 |
| low_or_ref_low_and_k240_lower | test | 3m_10m | 1057 | 0.469604 | 0.481646 | 0.895791 | 7 | 2 | 0 |
| low_or_ref_low_and_k240_lower | test | gt_10m | 636 | 0.557419 | 0.551068 | 0.909753 | 0 | 0 | 0 |
| low_or_ref_low_and_k240_lower | test | lt_1m | 540 | 0.631985 | 2.577619 | 20.716356 | 103 | 46 | 38 |
| low_or_ref_low_and_k240_lower | validation | 1m_3m | 846 | 0.318764 | 0.396308 | 1.124522 | 7 | 0 | 0 |
| low_or_ref_low_and_k240_lower | validation | 3m_10m | 903 | 0.421820 | 0.425868 | 0.774961 | 2 | 0 | 0 |
| low_or_ref_low_and_k240_lower | validation | gt_10m | 374 | 0.494466 | 0.507405 | 0.864342 | 0 | 0 | 0 |
| low_or_ref_low_and_k240_lower | validation | lt_1m | 630 | 0.321113 | 0.594642 | 2.198473 | 34 | 8 | 1 |
| low_or_ref_low_and_k320_lower | test | 1m_3m | 866 | 0.453386 | 0.733523 | 2.078282 | 48 | 6 | 2 |
| low_or_ref_low_and_k320_lower | test | 3m_10m | 1057 | 0.465278 | 0.482519 | 0.895791 | 7 | 2 | 0 |
| low_or_ref_low_and_k320_lower | test | gt_10m | 636 | 0.554981 | 0.550386 | 0.909780 | 0 | 0 | 0 |
| low_or_ref_low_and_k320_lower | test | lt_1m | 540 | 0.648314 | 2.496974 | 20.308285 | 100 | 48 | 38 |
| low_or_ref_low_and_k320_lower | validation | 1m_3m | 846 | 0.317779 | 0.389372 | 0.906200 | 7 | 0 | 0 |
| low_or_ref_low_and_k320_lower | validation | 3m_10m | 903 | 0.421820 | 0.429813 | 0.772978 | 2 | 0 | 0 |
| low_or_ref_low_and_k320_lower | validation | gt_10m | 374 | 0.497001 | 0.507113 | 0.862685 | 0 | 0 | 0 |
| low_or_ref_low_and_k320_lower | validation | lt_1m | 630 | 0.330228 | 0.591889 | 2.134762 | 35 | 8 | 1 |
| low_or_ref_low_and_k640_lower | test | 1m_3m | 866 | 0.449293 | 0.740058 | 2.023219 | 45 | 6 | 2 |
| low_or_ref_low_and_k640_lower | test | 3m_10m | 1057 | 0.467096 | 0.484394 | 0.896997 | 7 | 2 | 0 |
| low_or_ref_low_and_k640_lower | test | gt_10m | 636 | 0.556383 | 0.550899 | 0.909753 | 0 | 0 | 0 |
| low_or_ref_low_and_k640_lower | test | lt_1m | 540 | 0.667425 | 2.473328 | 20.254337 | 102 | 45 | 38 |
| low_or_ref_low_and_k640_lower | validation | 1m_3m | 846 | 0.316760 | 0.391190 | 0.913906 | 7 | 0 | 0 |
| low_or_ref_low_and_k640_lower | validation | 3m_10m | 903 | 0.421820 | 0.431723 | 0.773093 | 2 | 0 | 0 |
| low_or_ref_low_and_k640_lower | validation | gt_10m | 374 | 0.498915 | 0.508072 | 0.863291 | 0 | 0 | 0 |
| low_or_ref_low_and_k640_lower | validation | lt_1m | 630 | 0.319552 | 0.589971 | 2.094692 | 33 | 8 | 1 |
| uncertain_and_k240_lower | test | 1m_3m | 866 | 0.450922 | 0.753137 | 2.183348 | 50 | 5 | 2 |
| uncertain_and_k240_lower | test | 3m_10m | 1057 | 0.467096 | 0.479550 | 0.889340 | 6 | 2 | 0 |
| uncertain_and_k240_lower | test | gt_10m | 636 | 0.562515 | 0.557406 | 0.911116 | 0 | 0 | 0 |
| uncertain_and_k240_lower | test | lt_1m | 540 | 0.682328 | 2.643499 | 20.894702 | 103 | 46 | 38 |
| uncertain_and_k240_lower | validation | 1m_3m | 846 | 0.318764 | 0.396119 | 1.124522 | 6 | 0 | 0 |
| uncertain_and_k240_lower | validation | 3m_10m | 903 | 0.415022 | 0.423255 | 0.773488 | 2 | 0 | 0 |
| uncertain_and_k240_lower | validation | gt_10m | 374 | 0.496149 | 0.507731 | 0.863628 | 0 | 0 | 0 |
| uncertain_and_k240_lower | validation | lt_1m | 630 | 0.316941 | 0.616221 | 2.198473 | 35 | 8 | 1 |
| uncertain_and_k320_lower | test | 1m_3m | 866 | 0.451840 | 0.743290 | 2.169788 | 47 | 5 | 2 |
| uncertain_and_k320_lower | test | 3m_10m | 1057 | 0.464583 | 0.479744 | 0.887727 | 7 | 2 | 0 |
| uncertain_and_k320_lower | test | gt_10m | 636 | 0.562005 | 0.559652 | 0.911383 | 0 | 0 | 0 |
| uncertain_and_k320_lower | test | lt_1m | 540 | 0.679415 | 2.581320 | 20.911669 | 101 | 48 | 38 |
| uncertain_and_k320_lower | validation | 1m_3m | 846 | 0.318764 | 0.395087 | 1.124522 | 6 | 0 | 0 |
| uncertain_and_k320_lower | validation | 3m_10m | 903 | 0.412235 | 0.426440 | 0.774961 | 2 | 0 | 0 |
| uncertain_and_k320_lower | validation | gt_10m | 374 | 0.488422 | 0.504094 | 0.863628 | 0 | 0 | 0 |
| uncertain_and_k320_lower | validation | lt_1m | 630 | 0.316941 | 0.605218 | 2.134762 | 36 | 8 | 1 |
| uncertain_and_k640_lower | test | 1m_3m | 866 | 0.454061 | 0.767792 | 2.038157 | 47 | 5 | 2 |
| uncertain_and_k640_lower | test | 3m_10m | 1057 | 0.468990 | 0.481524 | 0.887279 | 6 | 2 | 0 |
| uncertain_and_k640_lower | test | gt_10m | 636 | 0.565993 | 0.563630 | 0.911249 | 0 | 0 | 0 |
| uncertain_and_k640_lower | test | lt_1m | 540 | 0.679649 | 2.576155 | 20.911669 | 104 | 45 | 38 |
| uncertain_and_k640_lower | validation | 1m_3m | 846 | 0.312918 | 0.391031 | 1.124522 | 6 | 0 | 0 |
| uncertain_and_k640_lower | validation | 3m_10m | 903 | 0.408470 | 0.425726 | 0.773093 | 2 | 0 | 0 |
| uncertain_and_k640_lower | validation | gt_10m | 374 | 0.499722 | 0.511191 | 0.863628 | 0 | 0 | 0 |
| uncertain_and_k640_lower | validation | lt_1m | 630 | 0.316941 | 0.600941 | 2.094692 | 34 | 8 | 1 |

## 8. 해석
- k를 촘촘하게 늘려도 validation과 test가 같은 방향으로 좋아지는지 확인해야 한다.
- q90-q10은 예측 불확실성 폭으로, k160이 불확실한 행에서 더 넓은 k를 쓰는 규칙이 효과적인지 확인하기 위한 신호다.
- adaptive-k 후보는 실제 가격을 보지 않고 사용 단계에서 알 수 있는 예측값과 유사작품 통계만 사용한다.