# PP-CBOOST3 이종 blend 게이트 재도전

   w  adaptive  val_dMdAPE  val_dMAPE  val_dp95
0.35     False     0.00626   -0.02493  -0.02989
0.30     False     0.00145   -0.02424  -0.02306
0.35      True     0.00566   -0.02420  -0.02453
0.30      True     0.00074   -0.02350  -0.01346
0.25     False     0.00352   -0.02236  -0.01328
0.25      True     0.00332   -0.02166  -0.00903
0.20     False     0.00186   -0.01978  -0.00521
0.20      True     0.00167   -0.01921   0.01104

  w  adaptive  boot_p_MAPE  boot_p_p95  boot_p_MdAPE  sub0.8_p_MAPE  sub0.8_p_p95  sub0.8_p_MdAPE  sub0.7_p_MAPE  sub0.7_p_p95  sub0.7_p_MdAPE  gate_pass
0.3     False       0.8625      0.7425        0.2475          0.980         0.860           0.115          0.915         0.810            0.12      False
0.3      True       0.8675      0.7375        0.2825          0.965         0.795           0.235          0.910         0.720            0.12      False
0.2     False       0.9100      0.6725        0.2700          0.980         0.650           0.125          0.950         0.695            0.16      False

[{"seed": 20260610, "improves_MAPE": true}, {"seed": 20260611, "improves_MAPE": true}, {"seed": 20260612, "improves_MAPE": true}]

   candidate  MdAPE   MAPE  p95_APE
B_seed_mean5 0.4857 1.2138   4.2175
w0.3_adFalse 0.4822 1.1790   3.6490
 w0.3_adTrue 0.4849 1.1759   3.6462
w0.2_adFalse 0.4820 1.1909   4.0343