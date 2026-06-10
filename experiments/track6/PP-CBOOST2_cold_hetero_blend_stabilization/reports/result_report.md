# PP-CBOOST2 이종 blend 안정화

            candidate  val_dMdAPE  val_dMAPE  val_dp95
     w0.4_none_capinf     0.00579   -0.02568  -0.02652
     w0.5_none_capinf     0.00647   -0.02504  -0.02717
     w0.3_none_capinf    -0.00003   -0.02452  -0.02478
     w0.3_none_cap0.1    -0.00003   -0.00351  -0.02478
     w0.4_none_cap0.1    -0.00102   -0.00250  -0.01690
    w0.3_none_cap0.05    -0.00239   -0.00191  -0.01916
    w0.5_none_cap0.05    -0.00134   -0.00162  -0.01940
    w0.4_none_cap0.05    -0.00134   -0.00145  -0.01940
     w0.5_none_cap0.1     0.00095   -0.00134  -0.02134
w0.5_agree_q50_capinf    -0.00044   -0.00050  -0.01608

       candidate  p_MAPE  p_p95  p_MdAPE  gate_pass
w0.3_none_capinf  0.8675 0.7625   0.2475      False
w0.3_none_cap0.1  0.7625 0.7250   0.3700      False
w0.4_none_cap0.1  0.6750 0.6700   0.4150      False

[{"seed": 20260610, "blend_improves_MAPE": true}, {"seed": 20260611, "blend_improves_MAPE": true}, {"seed": 20260612, "blend_improves_MAPE": true}]

       candidate  MdAPE   MAPE  p95_APE
    B_seed_mean5 0.4857 1.2138   4.2175
w0.3_none_capinf 0.4823 1.1787   3.6613
w0.3_none_cap0.1 0.4821 1.2145   4.1960
w0.4_none_cap0.1 0.4815 1.2189   4.2052