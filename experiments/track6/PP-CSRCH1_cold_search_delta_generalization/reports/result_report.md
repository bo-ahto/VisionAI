# PP-CSRCH1 검색 delta 그룹 일반화 (수집 없음)

- 비교 기준 = guard-only(현행 미커버 fallback), 상한 = true per-artist delta(v0.3).

## validation OOF

          candidate  strength  val_MdAPE  val_MAPE  val_p95_APE  val_dMAPE  val_dp95  val_dMdAPE
       const_median       1.0    0.36748   0.50493      1.26711   -0.01330  -0.07207     0.00245
medium_group_median       1.0    0.36748   0.50493      1.26711   -0.01330  -0.07207     0.00245
  price_band_median       1.0    0.36748   0.50493      1.26711   -0.01330  -0.07207     0.00245
  huber_lowdim_meta       1.0    0.36748   0.50493      1.26711   -0.01330  -0.07207     0.00245
         const_mean       1.0    0.36700   0.50515      1.26896   -0.01307  -0.07022     0.00197
medium_group_median       0.5    0.36491   0.51136      1.30286   -0.00686  -0.03632    -0.00012
  price_band_median       0.5    0.36491   0.51136      1.30286   -0.00686  -0.03632    -0.00012
       const_median       0.5    0.36491   0.51136      1.30286   -0.00686  -0.03632    -0.00012
  huber_lowdim_meta       0.5    0.36491   0.51136      1.30286   -0.00686  -0.03632    -0.00012
         const_mean       0.5    0.36433   0.51149      1.30380   -0.00674  -0.03538    -0.00070

## artist 반복 holdout 게이트 (vs guard-only)

          candidate  strength  p_MAPE_0.8  p_p95_0.8  p_MdAPE_0.8  p_MAPE_0.7  p_p95_0.7  p_MdAPE_0.7  gate_pass
       const_median       1.0       0.975      0.995        0.450       1.000      1.000         0.41      False
medium_group_median       1.0       0.960      0.985        0.460       1.000      0.995         0.43      False
  price_band_median       1.0       0.980      0.995        0.415       0.985      1.000         0.46      False

## test 최종 확인 (미커버 시나리오)

                     candidate  MdAPE   MAPE  p95_APE  search_gain_recovered_MAPE
       guard_only_fallback(현행) 0.4178 0.9640   2.5377                         NaN
true_per_artist_delta(v0.3 상한) 0.4098 0.8493   2.3465                         NaN
             const_median_s1.0 0.4262 0.9381   2.4287                      0.2253
      medium_group_median_s1.0 0.4262 0.9381   2.4287                      0.2253
        price_band_median_s1.0 0.4262 0.9381   2.4287                      0.2253