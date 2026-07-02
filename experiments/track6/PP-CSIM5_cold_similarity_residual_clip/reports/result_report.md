# Cold 유사작품 기준가격 + 잔차 clip 검증

- 작성일: 2026-06-18T15:24:36
- 목적: 유사작품 k160을 최종 가격 직접 예측이 아니라 기준가격 + 제한된 잔차 보정 구조로 바꿔 극단 오차를 줄일 수 있는지 검증한다.
- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.

## 1. Test 결과: MdAPE 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artwork_similarity_k160_direct | test | 0.467623 | 1.068718 | 2.920315 | 0.876089 | 0.328816 | 0.529848 | 564 | 263 | 76 | 38 | 유사작품 k160 직접 q50 예측 |
| user_meta_core_bucket | test | 0.473483 | 1.100452 | 2.942330 | 0.887405 | 0.321071 | 0.527267 | 582 | 269 | 72 | 39 | 기존 사용자 메타 core bucket |
| similar_basis_residual_clip_m070_p050 | test | 0.479339 | 1.083878 | 3.172460 | 0.884149 | 0.302678 | 0.524040 | 591 | 288 | 78 | 40 | 유사작품 median 기준가격 + residual strength=1.0 clip=(-0.7,0.5) |
| similar_basis_residual_clip_m030_p030 | test | 0.479339 | 1.086004 | 3.172460 | 0.887214 | 0.299774 | 0.529526 | 588 | 290 | 76 | 41 | 유사작품 median 기준가격 + residual strength=1.0 clip=(-0.3,0.3) |
| similar_basis_residual_clip_m050_p040 | test | 0.479798 | 1.082789 | 3.172460 | 0.884166 | 0.301710 | 0.524685 | 586 | 287 | 77 | 41 | 유사작품 median 기준가격 + residual strength=1.0 clip=(-0.5,0.4) |
| similar_basis_residual_clip_m040_p030 | test | 0.481010 | 1.081668 | 3.172460 | 0.887173 | 0.298161 | 0.528880 | 582 | 290 | 76 | 41 | 유사작품 median 기준가격 + residual strength=1.0 clip=(-0.4,0.3) |
| similar_basis_residual_half_clip_m050_p040 | test | 0.487855 | 1.084443 | 3.192564 | 0.896305 | 0.300097 | 0.520813 | 574 | 263 | 76 | 39 | 유사작품 median 기준가격 + residual strength=0.5 clip=(-0.5,0.4) |
| similar_basis_residual_basis_only | test | 0.500000 | 1.105908 | 3.212766 | 0.926334 | 0.303969 | 0.501775 | 561 | 258 | 84 | 40 | 유사작품 median 기준가격 + residual strength=0.0 clip=(0.0,0.0) |

## 2. Test 결과: APE > 5 안정성 기준
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | APE_gt_1 | APE_gt_2 | APE_gt_5 | APE_gt_10 | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| user_meta_core_bucket | test | 0.473483 | 1.100452 | 2.942330 | 0.887405 | 0.321071 | 0.527267 | 582 | 269 | 72 | 39 | 기존 사용자 메타 core bucket |
| artwork_similarity_k160_direct | test | 0.467623 | 1.068718 | 2.920315 | 0.876089 | 0.328816 | 0.529848 | 564 | 263 | 76 | 38 | 유사작품 k160 직접 q50 예측 |
| similar_basis_residual_clip_m040_p030 | test | 0.481010 | 1.081668 | 3.172460 | 0.887173 | 0.298161 | 0.528880 | 582 | 290 | 76 | 41 | 유사작품 median 기준가격 + residual strength=1.0 clip=(-0.4,0.3) |
| similar_basis_residual_clip_m030_p030 | test | 0.479339 | 1.086004 | 3.172460 | 0.887214 | 0.299774 | 0.529526 | 588 | 290 | 76 | 41 | 유사작품 median 기준가격 + residual strength=1.0 clip=(-0.3,0.3) |
| similar_basis_residual_half_clip_m050_p040 | test | 0.487855 | 1.084443 | 3.192564 | 0.896305 | 0.300097 | 0.520813 | 574 | 263 | 76 | 39 | 유사작품 median 기준가격 + residual strength=0.5 clip=(-0.5,0.4) |
| similar_basis_residual_clip_m050_p040 | test | 0.479798 | 1.082789 | 3.172460 | 0.884166 | 0.301710 | 0.524685 | 586 | 287 | 77 | 41 | 유사작품 median 기준가격 + residual strength=1.0 clip=(-0.5,0.4) |
| similar_basis_residual_clip_m070_p050 | test | 0.479339 | 1.083878 | 3.172460 | 0.884149 | 0.302678 | 0.524040 | 591 | 288 | 78 | 40 | 유사작품 median 기준가격 + residual strength=1.0 clip=(-0.7,0.5) |
| similar_basis_residual_basis_only | test | 0.500000 | 1.105908 | 3.212766 | 0.926334 | 0.303969 | 0.501775 | 561 | 258 | 84 | 40 | 유사작품 median 기준가격 + residual strength=0.0 clip=(0.0,0.0) |

## 3. 저가/고가 구간 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| similar_basis_residual_clip_m050_p040 | test | 1m_3m | 866 | 0.489947 | 0.789821 | 2.432797 | 0.690850 | 82 | 5 |
| similar_basis_residual_clip_m070_p050 | test | 1m_3m | 866 | 0.500206 | 0.789568 | 2.432797 | 0.695043 | 82 | 5 |
| similar_basis_residual_clip_m040_p030 | test | 1m_3m | 866 | 0.493136 | 0.792217 | 2.433133 | 0.693229 | 82 | 5 |
| similar_basis_residual_clip_m030_p030 | test | 1m_3m | 866 | 0.493136 | 0.795896 | 2.459231 | 0.692693 | 82 | 5 |
| similar_basis_residual_half_clip_m050_p040 | test | 1m_3m | 866 | 0.500669 | 0.806053 | 2.566541 | 0.704373 | 62 | 5 |
| similar_basis_residual_basis_only | test | 1m_3m | 866 | 0.549542 | 0.838689 | 2.631344 | 0.735774 | 67 | 5 |
| artwork_similarity_k160_direct | test | 1m_3m | 866 | 0.531981 | 0.762641 | 2.187840 | 0.677232 | 58 | 6 |
| user_meta_core_bucket | test | 1m_3m | 866 | 0.523406 | 0.784250 | 2.278503 | 0.691021 | 65 | 6 |
| similar_basis_residual_clip_m030_p030 | test | 3m_10m | 1057 | 0.408508 | 0.503152 | 1.200584 | 0.647294 | 23 | 1 |
| similar_basis_residual_clip_m040_p030 | test | 3m_10m | 1057 | 0.410318 | 0.500506 | 1.200584 | 0.647821 | 23 | 1 |
| similar_basis_residual_half_clip_m050_p040 | test | 3m_10m | 1057 | 0.424069 | 0.503895 | 1.248880 | 0.661204 | 21 | 1 |
| similar_basis_residual_basis_only | test | 3m_10m | 1057 | 0.445252 | 0.523192 | 1.360031 | 0.712957 | 30 | 1 |
| user_meta_core_bucket | test | 3m_10m | 1057 | 0.383002 | 0.471443 | 1.031206 | 0.614236 | 16 | 2 |
| artwork_similarity_k160_direct | test | 3m_10m | 1057 | 0.380260 | 0.467040 | 1.069804 | 0.606447 | 20 | 2 |
| similar_basis_residual_clip_m050_p040 | test | 3m_10m | 1057 | 0.407468 | 0.497416 | 1.191164 | 0.638832 | 20 | 2 |
| similar_basis_residual_clip_m070_p050 | test | 3m_10m | 1057 | 0.408160 | 0.497542 | 1.191164 | 0.634868 | 21 | 3 |
| similar_basis_residual_basis_only | test | gt_10m | 636 | 0.485372 | 0.472756 | 0.897904 | 1.092700 | 0 | 0 |
| similar_basis_residual_half_clip_m050_p040 | test | gt_10m | 636 | 0.474021 | 0.471985 | 0.902802 | 1.058123 | 0 | 0 |
| artwork_similarity_k160_direct | test | gt_10m | 636 | 0.471703 | 0.465663 | 0.905791 | 1.047368 | 0 | 0 |
| similar_basis_residual_clip_m030_p030 | test | gt_10m | 636 | 0.474372 | 0.477184 | 0.906599 | 1.039756 | 0 | 0 |
| similar_basis_residual_clip_m040_p030 | test | gt_10m | 636 | 0.475347 | 0.478183 | 0.906599 | 1.041938 | 0 | 0 |
| similar_basis_residual_clip_m050_p040 | test | gt_10m | 636 | 0.482162 | 0.480038 | 0.907895 | 1.037704 | 0 | 0 |
| user_meta_core_bucket | test | gt_10m | 636 | 0.453373 | 0.473580 | 0.907910 | 1.059568 | 0 | 0 |
| similar_basis_residual_clip_m070_p050 | test | gt_10m | 636 | 0.482162 | 0.482021 | 0.908808 | 1.036815 | 0 | 0 |
| user_meta_core_bucket | test | lt_1m | 540 | 1.000966 | 3.577087 | 29.759225 | 1.301054 | 188 | 64 |
| artwork_similarity_k160_direct | test | lt_1m | 540 | 1.011363 | 3.447568 | 28.190455 | 1.287387 | 185 | 68 |
| similar_basis_residual_clip_m030_p030 | test | lt_1m | 540 | 1.015461 | 3.409187 | 26.795083 | 1.286252 | 185 | 70 |
| similar_basis_residual_clip_m040_p030 | test | lt_1m | 540 | 1.015461 | 3.394202 | 26.795083 | 1.283024 | 185 | 70 |
| similar_basis_residual_clip_m050_p040 | test | lt_1m | 540 | 1.015461 | 3.408341 | 26.795083 | 1.286029 | 185 | 70 |
| similar_basis_residual_clip_m070_p050 | test | lt_1m | 540 | 1.047712 | 3.412418 | 26.795083 | 1.287027 | 185 | 70 |
| similar_basis_residual_half_clip_m050_p040 | test | lt_1m | 540 | 1.003076 | 3.388606 | 27.283816 | 1.280750 | 180 | 70 |
| similar_basis_residual_basis_only | test | lt_1m | 540 | 0.943594 | 3.420776 | 27.259441 | 1.286505 | 161 | 78 |

## 4. 결론

- MdAPE 기준 최상위 후보는 `artwork_similarity_k160_direct`이다.
- APE > 5 안정성 기준 최상위 후보는 `user_meta_core_bucket`이다.
- 잔차 clip 구조가 직접 q50 예측보다 극단 오차를 줄이는지와 중앙 오차를 얼마나 희생하는지를 함께 봐야 한다.
- 라우터는 사용하지 않았으므로 결과는 모델 구조 변경 효과로 해석한다.