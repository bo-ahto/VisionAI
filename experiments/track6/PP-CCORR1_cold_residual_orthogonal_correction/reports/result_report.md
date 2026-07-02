# PP-CCORR1 Cold 잔여 보정 직교 결합

## 직교성 감사 (validation OOF)

{
 "resid_huber": {
  "corr_with_guard_shift": -0.3101857737731532,
  "corr_with_search_delta": 0.08009107220087038,
  "oof_corr_pred_vs_actual_residual": -0.10901232961533569
 },
 "segment_median": {
  "corr_with_guard_shift": -0.25114553871946965,
  "corr_with_search_delta": 0.1472922986714157,
  "oof_corr_pred_vs_actual_residual": -0.08980756581878865
 }
}

## validation OOF 상위

       kind             mask  cap  strength  val_MdAPE  val_MAPE  val_p95_APE  val_dMAPE  val_dp95  val_dMdAPE
resid_huber   qwidth_extreme 0.05      0.25    0.35528   0.49983      1.49964    0.00205   0.00000     0.00000
resid_huber   qwidth_extreme 0.05      0.50    0.35521   0.50013      1.51004    0.00235   0.01040    -0.00007
resid_huber   qwidth_extreme 0.05      1.00    0.35528   0.50038      1.51004    0.00260   0.01040     0.00000
resid_huber   qwidth_extreme 0.10      0.25    0.35521   0.50056      1.49964    0.00278   0.00000    -0.00007
resid_huber   qwidth_extreme 0.20      0.25    0.35521   0.50075      1.49964    0.00297   0.00000    -0.00007
resid_huber   qwidth_extreme 0.10      0.50    0.35499   0.50205      1.52479    0.00427   0.02514    -0.00029
resid_huber   qwidth_extreme 0.10      1.00    0.35498   0.50273      1.54344    0.00495   0.04380    -0.00030
resid_huber   qwidth_extreme 0.20      0.50    0.35498   0.50366      1.52479    0.00588   0.02514    -0.00030
resid_huber qwidth_high_plus 0.05      0.25    0.35521   0.50454      1.51584    0.00676   0.01620    -0.00007
resid_huber qwidth_high_plus 0.05      0.50    0.35521   0.50613      1.53717    0.00835   0.03753    -0.00007

## artist 반복 holdout 게이트

(OOF 통과 후보 없음)

## fixed test 최종 확인

    candidate  MdAPE   MAPE  p95_APE
research_base 0.4098 0.8493   2.3465