# PP-CGRP1 비교군 그룹 가격 통계 base 투입

## 후보 지표 (seed 3 평균 예측)

      candidate      split           role  MdAPE   MAPE  p95_APE  seed_MAPE_std
         base12 validation representative 0.3848 0.6527   1.7522         0.0048
         base12 validation        defense 0.3823 0.6115   1.6341         0.0043
         base12       test representative 0.4864 1.2809   4.6240         0.0120
         base12       test        defense 0.4860 1.2030   4.2408         0.0047
base12_grp_full validation representative 0.4101 0.6820   1.8843         0.0052
base12_grp_full validation        defense 0.4043 0.6422   1.7455         0.0041
base12_grp_full       test representative 0.4917 1.2242   4.1694         0.0178
base12_grp_full       test        defense 0.4950 1.1859   3.7831         0.0117
base12_grp_lean validation representative 0.4017 0.6889   1.8584         0.0072
base12_grp_lean validation        defense 0.3852 0.6387   1.6953         0.0067
base12_grp_lean       test representative 0.4942 1.2166   4.1404         0.0118
base12_grp_lean       test        defense 0.4909 1.1779   3.9122         0.0113

## validation artist-cluster bootstrap (defense, vs base12)

      candidate  p_MAPE  p_p95  p_MdAPE
base12_grp_full  0.0875  0.095   0.0400
base12_grp_lean  0.0200  0.320   0.3675

## pseudo-cold (PP-PCOLD1 마스크)

 pcold_seed       candidate  MdAPE   MAPE  p95_APE
   20260610          base12 0.5793 1.0050   3.5936
   20260610 base12_grp_lean 0.5665 0.9779   3.5893
   20260610 base12_grp_full 0.5724 1.0195   3.8471
   20260611          base12 0.5856 1.3335   5.7399
   20260611 base12_grp_lean 0.6146 1.4882   6.2864
   20260611 base12_grp_full 0.6045 1.4329   5.7797
   20260612          base12 0.5767 1.2610   2.9748
   20260612 base12_grp_lean 0.5926 1.3564   3.3342
   20260612 base12_grp_full 0.5787 1.2997   3.3403

[{"pcold_seed": 20260610, "lean_improves_MAPE": true, "full_improves_MAPE": false}, {"pcold_seed": 20260611, "lean_improves_MAPE": false, "full_improves_MAPE": false}, {"pcold_seed": 20260612, "lean_improves_MAPE": false, "full_improves_MAPE": false}]