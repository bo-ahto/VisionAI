# PP-CCONF1 Cold 신뢰도 tier 정책

- tier 경계는 validation 분위수 동결. test/pseudo-cold는 확인 전용.
- 0604 미사용 (Warm 시험 제출 전용).

## tier별 성능

     tier_scheme      split   tier        base    n  MdAPE   MAPE p95_APE within_30 over_50pct_error_rate  share range_q10_q90_hit_rate
tier_operational       test   high operational  764 0.4794 2.1045  8.3992    0.2997                0.4699 0.2465                 0.5380
tier_operational       test    low operational  509 0.5409 1.2912  5.0946    0.2829                0.5147 0.1642                 0.7937
tier_operational       test medium operational 1826 0.4773 0.7573  2.3283    0.2837                0.4770 0.5892                 0.7399
tier_operational       test   high    research  764 0.4027 1.6077  4.7595    0.4018                0.4162 0.2465                 0.5380
tier_operational       test    low    research  509 0.4318 0.6683  1.9058    0.3635                0.4538 0.1642                 0.7937
tier_operational       test medium    research 1826 0.4065 0.5824  1.4162    0.3658                0.4042 0.5892                 0.7399
tier_operational validation   high operational  909 0.3171 0.3906  0.8786    0.3894                0.1925 0.3302                 0.7129
tier_operational validation    low operational  276 0.4712 1.0413  3.7064    0.2681                0.4529 0.1003                 0.8333
tier_operational validation medium operational 1568 0.4098 0.6734  1.8042    0.3501                0.4011 0.5696                 0.7870
tier_operational validation   high    research  909 0.2495 0.3935  1.6593    0.5666                0.2134 0.3302                 0.7129
tier_operational validation    low    research  276 0.4890 0.6836  2.4011    0.2717                0.4746 0.1003                 0.8333
tier_operational validation medium    research 1568 0.3951 0.5256  1.2102    0.3540                0.3253 0.5696                 0.7870
   tier_research       test   high operational  255 0.3867 0.8031  1.6312    0.3608                0.3451 0.0823                 0.7137
   tier_research       test    low operational  904 0.6967 1.4995  6.5371    0.1903                0.6715 0.2917                 0.6162
   tier_research       test medium operational 1940 0.4373 1.0761  2.5214    0.3232                0.4108 0.6260                 0.7356
   tier_research       test   high    research  255 0.3828 0.6811  0.9904    0.4275                0.3373 0.0823                 0.7137
   tier_research       test    low    research  904 0.5549 0.7824  2.9877    0.2954                0.5542 0.2917                 0.6162
   tier_research       test medium    research 1940 0.3709 0.9025  1.8243    0.4041                0.3608 0.6260                 0.7356
   tier_research validation   high operational  407 0.3267 0.3497  0.8382    0.4570                0.1548 0.1478                 0.8624
   tier_research validation    low operational  529 0.5379 1.0972  4.0919    0.2079                0.5255 0.1922                 0.7637
   tier_research validation medium operational 1817 0.3737 0.5369  1.4854    0.3748                0.3236 0.6600                 0.7468
   tier_research validation   high    research  407 0.2448 0.3400  0.9333    0.6044                0.2236 0.1478                 0.8624
   tier_research validation    low    research  529 0.4648 0.6551  1.6761    0.2760                0.4442 0.1922                 0.7637
   tier_research validation medium    research 1817 0.3514 0.4873  1.6593    0.4144                0.2801 0.6600                 0.7468

## 기존 v0.3 검수 플래그 비교

     split  v03_review_rate  tier_low_rate  low_and_v03_overlap  v03_review_MAPE_research  tier_low_MAPE_research
      test         0.452404       0.291707             0.195547                  0.653552                0.782425
validation         0.330185       0.192154             0.131856                  0.728934                0.655117

## pseudo-cold 방향 일치 (operational tier)

    seed   tier   n    MdAPE     MAPE
20260610   high 257 0.441628 0.726324
20260610    low 159 0.727219 1.275079
20260610 medium 791 0.591573 1.016171
20260611   high 252 0.459424 0.736402
20260611    low 228 0.719922 2.734689
20260611 medium 726 0.573436 1.074313
20260612   high 211 0.473667 0.621408
20260612    low 218 0.629584 1.898398
20260612 medium 777 0.605097 1.249317

[{"seed": 20260610, "high_lt_medium_lt_low_MdAPE": true}, {"seed": 20260611, "high_lt_medium_lt_low_MdAPE": true}, {"seed": 20260612, "high_lt_medium_lt_low_MdAPE": true}]