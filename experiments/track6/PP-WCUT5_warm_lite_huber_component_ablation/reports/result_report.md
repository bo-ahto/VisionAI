# PP-WCUT5 Warm-lite Huber 6구성 ablation

## 실험 목적

Warm-lite의 현재 6개 Huber 구성 평균이 단일 구성, full 구성만, lean 구성만보다 안정적인지 확인한다.

## 구성 메타데이터

component                  label feature_set  alpha  epsilon  n_num_cols  uses_q25_q75  uses_unit_area_iqr
       c0 full_alpha1e-4_eps1.35        full 0.0001     1.35          17          True                True
       c1 full_alpha1e-3_eps1.35        full 0.0010     1.35          17          True                True
       c2 full_alpha1e-4_eps1.20        full 0.0001     1.20          17          True                True
       c3 full_alpha1e-4_eps1.50        full 0.0001     1.50          17          True                True
       c4 lean_alpha1e-4_eps1.35        lean 0.0001     1.35          13         False               False
       c5 lean_alpha1e-3_eps1.50        lean 0.0010     1.50          13         False               False

## Overall metrics

                       candidate        components    n    MdAPE     MAPE  p95_APE  rank_MdAPE  delta_MdAPE_minus_all6  rank_MAPE  delta_MAPE_minus_all6  rank_p95_APE  delta_p95_APE_minus_all6
             c2_full_low_epsilon                c2 1947 0.108869 0.285808 0.873016           1               -0.000358          1              -0.000758             2                 -0.003454
                      full4_only       c0,c1,c2,c3 1947 0.109365 0.286545 0.873505           3                0.000138          2              -0.000021             4                 -0.002965
                    all6_current c0,c1,c2,c3,c4,c5 1947 0.109227 0.286566 0.876470           2                0.000000          3               0.000000             8                  0.000000
        c1_full_more_regularized                c1 1947 0.110042 0.286761 0.873552           5                0.000815          4               0.000195             5                 -0.002918
                 c0_full_default                c0 1947 0.110275 0.286763 0.873574           8                0.001048          5               0.000197             6                 -0.002896
            c3_full_high_epsilon                c3 1947 0.110304 0.287041 0.876935           9                0.001077          6               0.000475             9                  0.000465
                 c4_lean_default                c4 1947 0.109383 0.287336 0.872140           4                0.000156          7               0.000770             1                 -0.004330
                      lean2_only             c4,c5 1947 0.110166 0.287515 0.873201           7                0.000939          8               0.000949             3                 -0.003269
c5_lean_regularized_high_epsilon                c5 1947 0.110076 0.287711 0.875656           6                0.000849          9               0.001145             7                 -0.000814

## Metrics by history_k

                       candidate  history_k   n    MdAPE     MAPE  p95_APE
                    all6_current          1 621 0.120677 0.341476 0.955881
                 c0_full_default          1 621 0.123748 0.341414 0.956318
        c1_full_more_regularized          1 621 0.123688 0.341409 0.956317
             c2_full_low_epsilon          1 621 0.121214 0.340116 0.956066
            c3_full_high_epsilon          1 621 0.124677 0.341526 0.956225
                 c4_lean_default          1 621 0.118773 0.342762 0.954528
c5_lean_regularized_high_epsilon          1 621 0.118071 0.343116 0.954441
                      full4_only          1 621 0.123499 0.341098 0.956178
                      lean2_only          1 621 0.118970 0.342933 0.954485
                    all6_current          2 489 0.118375 0.270704 0.877912
                 c0_full_default          2 489 0.115270 0.271184 0.872886
        c1_full_more_regularized          2 489 0.115416 0.271179 0.872859
             c2_full_low_epsilon          2 489 0.116303 0.271851 0.872528
            c3_full_high_epsilon          2 489 0.117632 0.270646 0.875737
                 c4_lean_default          2 489 0.120604 0.271009 0.878525
c5_lean_regularized_high_epsilon          2 489 0.119902 0.270400 0.883699
                      full4_only          2 489 0.117628 0.271165 0.872749
                      lean2_only          2 489 0.118941 0.270698 0.881342
                    all6_current          3 324 0.105981 0.254102 0.714172
                 c0_full_default          3 324 0.108264 0.255063 0.719907
        c1_full_more_regularized          3 324 0.108289 0.255061 0.719923
             c2_full_low_epsilon          3 324 0.111397 0.251406 0.731172
            c3_full_high_epsilon          3 324 0.113584 0.257313 0.713653
                 c4_lean_default          3 324 0.101637 0.253690 0.713823
c5_lean_regularized_high_epsilon          3 324 0.100783 0.255753 0.703095
                      full4_only          3 324 0.107952 0.254633 0.721286
                      lean2_only          3 324 0.101431 0.254701 0.708505
                    all6_current          4 513 0.092263 0.255719 0.788372
                 c0_full_default          4 513 0.088628 0.255479 0.793967
        c1_full_more_regularized          4 513 0.088553 0.255481 0.794063
             c2_full_low_epsilon          4 513 0.091070 0.255098 0.787675
            c3_full_high_epsilon          4 513 0.088536 0.255487 0.797387
                 c4_lean_default          4 513 0.094836 0.257057 0.776982
c5_lean_regularized_high_epsilon          4 513 0.092152 0.257326 0.780492
                      full4_only          4 513 0.088264 0.255322 0.793271
                      lean2_only          4 513 0.094114 0.257184 0.778054

## all6 vs ablations bootstrap

                                      comparison                        candidate  n_boot  p_all6_better_MdAPE  p_tie_MdAPE  p_all6_better_MAPE  p_tie_MAPE  p_all6_better_p95_APE  p_tie_p95_APE
                 all6_current_vs_c0_full_default                  c0_full_default     400               0.4600          0.0              0.6950         0.0                 0.4775            0.0
        all6_current_vs_c1_full_more_regularized         c1_full_more_regularized     400               0.4000          0.0              0.6775         0.0                 0.5000            0.0
             all6_current_vs_c2_full_low_epsilon              c2_full_low_epsilon     400               0.2925          0.0              0.1250         0.0                 0.5950            0.0
            all6_current_vs_c3_full_high_epsilon             c3_full_high_epsilon     400               0.5700          0.0              0.8200         0.0                 0.5600            0.0
                 all6_current_vs_c4_lean_default                  c4_lean_default     400               0.5350          0.0              0.8475         0.0                 0.3525            0.0
all6_current_vs_c5_lean_regularized_high_epsilon c5_lean_regularized_high_epsilon     400               0.5375          0.0              0.8800         0.0                 0.4125            0.0
                      all6_current_vs_full4_only                       full4_only     400               0.4175          0.0              0.5125         0.0                 0.4875            0.0
                      all6_current_vs_lean2_only                       lean2_only     400               0.5925          0.0              0.8925         0.0                 0.3950            0.0

## Config

{
  "experiment_id": "PP-WCUT5",
  "eval_design": "PP-WCUT4 same real low-history leave-one-out, train history 2~5, seeds [20260612, 20260613, 20260614]",
  "rows": 1947,
  "artist_count": 649,
  "candidates": {
    "all6_current": [
      "c0",
      "c1",
      "c2",
      "c3",
      "c4",
      "c5"
    ],
    "full4_only": [
      "c0",
      "c1",
      "c2",
      "c3"
    ],
    "lean2_only": [
      "c4",
      "c5"
    ],
    "c0_full_default": [
      "c0"
    ],
    "c1_full_more_regularized": [
      "c1"
    ],
    "c2_full_low_epsilon": [
      "c2"
    ],
    "c3_full_high_epsilon": [
      "c3"
    ],
    "c4_lean_default": [
      "c4"
    ],
    "c5_lean_regularized_high_epsilon": [
      "c5"
    ]
  },
  "all6_current_metrics": {
    "MdAPE": 0.109227,
    "MAPE": 0.286566,
    "p95_APE": 0.87647
  },
  "best_by_metric": {
    "MdAPE": "c2_full_low_epsilon",
    "MAPE": "c2_full_low_epsilon",
    "p95_APE": "c4_lean_default"
  },
  "bootstrap": "artist-cluster bootstrap comparing all6_current vs each ablation",
  "n_boot": 400,
  "prohibitions": [
    "0604 사용 금지"
  ]
}
