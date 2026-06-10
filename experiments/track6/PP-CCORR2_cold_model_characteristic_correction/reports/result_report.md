# PP-CCORR2 모델 특성 보정 (V2식 meta + PP148식 라우팅)

{"meta_oof_corr_vs_actual": 0.8242229195987613, "base_corr_vs_actual": 0.8437834409395281}

 kind             param           mask  val_dMAPE  val_dp95  val_dMdAPE
route       guard_w0.25    gap_extreme    0.00031   0.00000     0.00055
route v02_defense_w0.25 qwidth_extreme    0.00041  -0.00924    -0.00007
route       guard_w0.25 qwidth_extreme    0.00050   0.00000     0.00059
route        guard_w0.5    gap_extreme    0.00063   0.00547     0.00069
route  v02_defense_w0.5 qwidth_extreme    0.00089  -0.01930    -0.00007
route v02_defense_w0.25    gap_extreme    0.00091   0.01040     0.00000
route        guard_w0.5 qwidth_extreme    0.00101   0.00000    -0.00007
route          y2_w0.25    gap_extreme    0.00123   0.01040     0.00055
route          y2_w0.25 qwidth_extreme    0.00273   0.01040    -0.00007
route           y2_w0.5    gap_extreme    0.00316   0.01040     0.00069
route           y2_w0.5 qwidth_extreme    0.00580   0.04311    -0.00019
route  v02_defense_w0.5    gap_extreme    0.01152   0.11733     0.00069
 meta             w0.25            all    0.01427   0.00987     0.00713
 meta              w0.5            all    0.03267   0.05897     0.01537
 meta              w1.0            all    0.08361   0.24061     0.04758

(OOF 통과 후보 없음)

    candidate  MdAPE   MAPE  p95_APE
research_base 0.4098 0.8493   2.3465