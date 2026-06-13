# PP-WMIN7 Warm min1 weight retuning 결과

- 작성일: 2026-06-12 23:07
- 데이터 기준: 기존 Warm validation OOF 519건 + fixed test 607건
- 선택 기준: WMIN4와 동일하게 validation 반복 안정성 + validation replacement score
- fixed test: 최종 확인용으로만 기록
- 0604: 사용하지 않음
- 결론: adopt_candidate: `min1_w800_huber_refit_partial` 선택. validation 0.095327/0.177354/0.576197, fixed test 0.105178/0.240637/0.761417.
- 판단 근거: validation gate를 통과했고 fixed test 확인에서도 기존 PP258 운영 후보보다 MdAPE/MAPE/p95가 모두 낮다.

## 1. 후보별 교체 판단
| candidate_label | passes_validation_gate | passes_fixed_confirmation | fixed_validation_MdAPE | fixed_validation_MAPE | fixed_validation_p95_APE | validation_avg_MAPE_win_rate | validation_avg_p95_win_rate | validation_replacement_score | fixed_test_MdAPE | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_MAPE_vs_current_pp258 | fixed_test_delta_p95_vs_current_pp258 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min1_w800_huber_refit_partial | True | True | 0.095327 | 0.177354 | 0.576197 | 0.996795 | 0.962821 | -0.028275 | 0.105178 | 0.240637 | 0.761417 | -0.029252 | -0.045907 |
| min1_w850_huber_refit_partial | True | True | 0.093414 | 0.177395 | 0.572921 | 0.996154 | 0.956410 | -0.028233 | 0.103804 | 0.241772 | 0.778254 | -0.028117 | -0.029071 |
| min1_w775_huber_refit_partial | True | True | 0.095678 | 0.177440 | 0.577824 | 0.996795 | 0.968590 | -0.028188 | 0.106316 | 0.240247 | 0.753071 | -0.029641 | -0.054253 |
| min1_w750_huber_refit_partial | True | True | 0.098162 | 0.177711 | 0.578309 | 0.996154 | 0.976923 | -0.027918 | 0.104964 | 0.239963 | 0.747940 | -0.029925 | -0.059385 |
| min1_w725_huber_refit_partial | True | True | 0.099916 | 0.178064 | 0.578493 | 0.996795 | 0.979487 | -0.027565 | 0.105504 | 0.239619 | 0.773420 | -0.030270 | -0.033904 |
| min1_w900_huber_refit_partial | True | True | 0.092410 | 0.178307 | 0.569616 | 0.994872 | 0.954487 | -0.027322 | 0.102547 | 0.243822 | 0.783997 | -0.026066 | -0.023328 |
| min1_huber_refit_partial | True | True | 0.101568 | 0.178407 | 0.571291 | 0.996795 | 0.980769 | -0.027222 | 0.106598 | 0.239302 | 0.779196 | -0.030586 | -0.028129 |
| min1_w700_huber_refit_partial | True | True | 0.101568 | 0.178407 | 0.571291 | 0.996795 | 0.980769 | -0.027222 | 0.106598 | 0.239302 | 0.779196 | -0.030586 | -0.028129 |
| min1_w675_huber_refit_partial | True | True | 0.100893 | 0.178936 | 0.571257 | 0.996795 | 0.982051 | -0.026693 | 0.108605 | 0.239055 | 0.778599 | -0.030833 | -0.028726 |
| min1_w800_70_30_basis | True | True | 0.099068 | 0.179103 | 0.586669 | 0.995513 | 0.972436 | -0.026525 | 0.106429 | 0.241258 | 0.758787 | -0.028631 | -0.048537 |
| min1_w775_70_30_basis | True | True | 0.102992 | 0.179235 | 0.587293 | 0.995513 | 0.975641 | -0.026394 | 0.107798 | 0.240493 | 0.758897 | -0.029395 | -0.048428 |
| min1_w850_70_30_basis | True | True | 0.096241 | 0.179477 | 0.589008 | 0.995513 | 0.956410 | -0.026152 | 0.106698 | 0.243349 | 0.770609 | -0.026539 | -0.036716 |
| min1_w750_70_30_basis | True | True | 0.103933 | 0.179527 | 0.576264 | 0.996154 | 0.979487 | -0.026102 | 0.106196 | 0.240056 | 0.776676 | -0.029832 | -0.030649 |
| min1_w650_huber_refit_partial | True | True | 0.101536 | 0.179581 | 0.581426 | 0.996795 | 0.977564 | -0.026048 | 0.110762 | 0.238952 | 0.778004 | -0.030937 | -0.029321 |
| min1_w725_70_30_basis | True | True | 0.106839 | 0.179962 | 0.583359 | 0.996154 | 0.982692 | -0.025666 | 0.104877 | 0.239783 | 0.783824 | -0.030105 | -0.023500 |
| min1_w625_huber_refit_partial | True | True | 0.101964 | 0.180263 | 0.580959 | 0.996154 | 0.971154 | -0.025366 | 0.110670 | 0.238935 | 0.777410 | -0.030953 | -0.029915 |
| min1_w700_70_30_basis | True | True | 0.107480 | 0.180564 | 0.581859 | 0.996154 | 0.985256 | -0.025065 | 0.108304 | 0.239684 | 0.782621 | -0.030205 | -0.024703 |
| min1_w900_70_30_basis | True | True | 0.096361 | 0.180754 | 0.589491 | 0.991026 | 0.951282 | -0.024875 | 0.108258 | 0.246063 | 0.783739 | -0.023825 | -0.023586 |
| min1_w600_huber_refit_partial | True | True | 0.105340 | 0.181034 | 0.590468 | 0.996154 | 0.971154 | -0.024595 | 0.112864 | 0.239008 | 0.797755 | -0.030880 | -0.009569 |
| min1_w675_70_30_basis | True | True | 0.108416 | 0.181274 | 0.589032 | 0.996154 | 0.984615 | -0.024355 | 0.109397 | 0.239746 | 0.781422 | -0.030143 | -0.025903 |
| min1_w650_70_30_basis | True | True | 0.110209 | 0.182077 | 0.588882 | 0.995513 | 0.977564 | -0.023551 | 0.112905 | 0.239918 | 0.780052 | -0.029970 | -0.027272 |
| min1_w625_70_30_basis | True | True | 0.110901 | 0.182975 | 0.588626 | 0.994872 | 0.975000 | -0.022654 | 0.115416 | 0.240163 | 0.782688 | -0.029725 | -0.024637 |
| min1_w550_huber_refit_partial | True | True | 0.109591 | 0.183358 | 0.600981 | 0.992308 | 0.944231 | -0.022271 | 0.114251 | 0.239457 | 0.788636 | -0.030431 | -0.018689 |
| min1_w600_70_30_basis | True | True | 0.113428 | 0.184121 | 0.593175 | 0.992308 | 0.968590 | -0.021507 | 0.112490 | 0.240471 | 0.782933 | -0.029417 | -0.024392 |
| min1_w500_huber_refit_partial | True | True | 0.110809 | 0.186340 | 0.632058 | 0.985897 | 0.821795 | -0.019289 | 0.115474 | 0.240210 | 0.762697 | -0.029678 | -0.044628 |
| min1_w550_70_30_basis | True | True | 0.119151 | 0.187289 | 0.613898 | 0.981410 | 0.857692 | -0.018340 | 0.114749 | 0.241505 | 0.750709 | -0.028383 | -0.056615 |
| min1_w500_70_30_basis | True | True | 0.119126 | 0.190935 | 0.637793 | 0.960897 | 0.611538 | -0.014694 | 0.118534 | 0.243109 | 0.777578 | -0.026780 | -0.029747 |
| current_pp258_operational_reference | True | True | 0.122707 | 0.205629 | 0.637888 | 0.000000 | 0.000000 | 0.000000 | 0.140976 | 0.269888 | 0.807325 | 0.000000 | 0.000000 |

## 2. WMIN4 선택 후보 대비 변화량
| candidate_label | eval_split | delta_MdAPE_vs_wmin4_selected | delta_MAPE_vs_wmin4_selected | delta_p95_APE_vs_wmin4_selected | delta_RMSE_log_vs_wmin4_selected |
| --- | --- | --- | --- | --- | --- |
| min1_w625_huber_refit_partial | test | 0.004073 | -0.000367 | -0.001786 | -0.001796 |
| min1_w650_huber_refit_partial | test | 0.004164 | -0.000350 | -0.001192 | -0.001261 |
| min1_w600_huber_refit_partial | test | 0.006267 | -0.000294 | 0.018559 | -0.002263 |
| min1_w675_huber_refit_partial | test | 0.002007 | -0.000247 | -0.000597 | -0.000671 |
| min1_w700_huber_refit_partial | test | -0.000000 | 0.000000 | -0.000000 | -0.000000 |
| min1_w550_huber_refit_partial | test | 0.007653 | 0.000155 | 0.009440 | -0.002899 |
| min1_w725_huber_refit_partial | test | -0.001094 | 0.000316 | -0.005776 | 0.000737 |
| min1_w700_70_30_basis | test | 0.001707 | 0.000382 | 0.003425 | -0.000423 |
| min1_w675_70_30_basis | test | 0.002800 | 0.000443 | 0.002226 | -0.001025 |
| min1_w725_70_30_basis | test | -0.001721 | 0.000481 | 0.004628 | 0.000293 |
| min1_w650_70_30_basis | test | 0.006308 | 0.000616 | 0.000856 | -0.001510 |
| min1_w750_huber_refit_partial | test | -0.001633 | 0.000661 | -0.031256 | 0.001523 |
| min1_w750_70_30_basis | test | -0.000401 | 0.000754 | -0.002520 | 0.001125 |
| min1_w625_70_30_basis | test | 0.008818 | 0.000861 | 0.003492 | -0.001878 |
| min1_w500_huber_refit_partial | test | 0.008877 | 0.000908 | -0.016499 | -0.003144 |
| min1_w775_huber_refit_partial | test | -0.000282 | 0.000945 | -0.026125 | 0.002243 |
| min1_w600_70_30_basis | test | 0.005893 | 0.001169 | 0.003737 | -0.002130 |
| min1_w775_70_30_basis | test | 0.001200 | 0.001191 | -0.020299 | 0.002071 |
| min1_w800_huber_refit_partial | test | -0.001420 | 0.001334 | -0.017779 | 0.002932 |
| min1_w800_70_30_basis | test | -0.000169 | 0.001955 | -0.020409 | 0.003129 |
| min1_w550_70_30_basis | test | 0.008151 | 0.002203 | -0.028487 | -0.002282 |
| min1_w850_huber_refit_partial | test | -0.002793 | 0.002469 | -0.000942 | 0.004508 |
| min1_w500_70_30_basis | test | 0.011937 | 0.003807 | -0.001618 | -0.001965 |
| min1_w850_70_30_basis | test | 0.000100 | 0.004047 | -0.008587 | 0.005583 |
| min1_w900_huber_refit_partial | test | -0.004051 | 0.004520 | 0.004801 | 0.006676 |
| min1_w900_70_30_basis | test | 0.001661 | 0.006761 | 0.004543 | 0.008477 |
| min1_w800_huber_refit_partial | validation_oof | -0.006240 | -0.001053 | 0.004905 | 0.001396 |
| min1_w850_huber_refit_partial | validation_oof | -0.008153 | -0.001012 | 0.001630 | 0.002575 |
| min1_w775_huber_refit_partial | validation_oof | -0.005890 | -0.000967 | 0.006533 | 0.000989 |
| min1_w750_huber_refit_partial | validation_oof | -0.003406 | -0.000696 | 0.007018 | 0.000593 |
| min1_w725_huber_refit_partial | validation_oof | -0.001652 | -0.000343 | 0.007202 | 0.000218 |
| min1_w900_huber_refit_partial | validation_oof | -0.009158 | -0.000100 | -0.001675 | 0.004564 |
| min1_w700_huber_refit_partial | validation_oof | 0.000000 | 0.000000 | 0.000000 | -0.000000 |
| min1_w675_huber_refit_partial | validation_oof | -0.000675 | 0.000529 | -0.000035 | -0.000011 |
| min1_w800_70_30_basis | validation_oof | -0.002500 | 0.000696 | 0.015378 | 0.003913 |
| min1_w775_70_30_basis | validation_oof | 0.001424 | 0.000827 | 0.016001 | 0.003185 |
| min1_w850_70_30_basis | validation_oof | -0.005326 | 0.001070 | 0.017717 | 0.005980 |
| min1_w750_70_30_basis | validation_oof | 0.002366 | 0.001120 | 0.004972 | 0.002662 |
| min1_w650_huber_refit_partial | validation_oof | -0.000032 | 0.001173 | 0.010135 | 0.000178 |
| min1_w725_70_30_basis | validation_oof | 0.005271 | 0.001555 | 0.012067 | 0.002346 |
| min1_w625_huber_refit_partial | validation_oof | 0.000397 | 0.001856 | 0.009668 | 0.000538 |
| min1_w700_70_30_basis | validation_oof | 0.005912 | 0.002157 | 0.010567 | 0.002238 |
| min1_w900_70_30_basis | validation_oof | -0.005207 | 0.002347 | 0.018199 | 0.008847 |
| min1_w600_huber_refit_partial | validation_oof | 0.003772 | 0.002627 | 0.019177 | 0.001078 |
| min1_w675_70_30_basis | validation_oof | 0.006848 | 0.002867 | 0.017740 | 0.002337 |
| min1_w650_70_30_basis | validation_oof | 0.008641 | 0.003670 | 0.017590 | 0.002644 |
| min1_w625_70_30_basis | validation_oof | 0.009334 | 0.004568 | 0.017334 | 0.003157 |
| min1_w550_huber_refit_partial | validation_oof | 0.008024 | 0.004951 | 0.029690 | 0.002717 |
| min1_w600_70_30_basis | validation_oof | 0.011860 | 0.005714 | 0.021883 | 0.003877 |
| min1_w500_huber_refit_partial | validation_oof | 0.009242 | 0.007933 | 0.060767 | 0.005079 |
| min1_w550_70_30_basis | validation_oof | 0.017584 | 0.008882 | 0.042606 | 0.005926 |
| min1_w500_70_30_basis | validation_oof | 0.017558 | 0.012528 | 0.066502 | 0.008776 |

## 3. fixed validation/test 지표
| candidate_label | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_current_pp258_MAPE | delta_vs_current_pp258_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min1_w625_huber_refit_partial | test | 607 | 0.110670 | 0.238935 | 0.777410 | 0.375087 | -0.030953 | -0.029915 |
| min1_w650_huber_refit_partial | test | 607 | 0.110762 | 0.238952 | 0.778004 | 0.375622 | -0.030937 | -0.029321 |
| min1_w600_huber_refit_partial | test | 607 | 0.112864 | 0.239008 | 0.797755 | 0.374621 | -0.030880 | -0.009569 |
| min1_w675_huber_refit_partial | test | 607 | 0.108605 | 0.239055 | 0.778599 | 0.376213 | -0.030833 | -0.028726 |
| min1_huber_refit_partial | test | 607 | 0.106598 | 0.239302 | 0.779196 | 0.376884 | -0.030586 | -0.028129 |
| min1_w700_huber_refit_partial | test | 607 | 0.106598 | 0.239302 | 0.779196 | 0.376884 | -0.030586 | -0.028129 |
| min1_w550_huber_refit_partial | test | 607 | 0.114251 | 0.239457 | 0.788636 | 0.373985 | -0.030431 | -0.018689 |
| min1_w725_huber_refit_partial | test | 607 | 0.105504 | 0.239619 | 0.773420 | 0.377621 | -0.030270 | -0.033904 |
| min1_w700_70_30_basis | test | 607 | 0.108304 | 0.239684 | 0.782621 | 0.376460 | -0.030205 | -0.024703 |
| min1_w675_70_30_basis | test | 607 | 0.109397 | 0.239746 | 0.781422 | 0.375859 | -0.030143 | -0.025903 |
| min1_w725_70_30_basis | test | 607 | 0.104877 | 0.239783 | 0.783824 | 0.377177 | -0.030105 | -0.023500 |
| min1_w650_70_30_basis | test | 607 | 0.112905 | 0.239918 | 0.780052 | 0.375374 | -0.029970 | -0.027272 |
| min1_w750_huber_refit_partial | test | 607 | 0.104964 | 0.239963 | 0.747940 | 0.378406 | -0.029925 | -0.059385 |
| min1_w750_70_30_basis | test | 607 | 0.106196 | 0.240056 | 0.776676 | 0.378008 | -0.029832 | -0.030649 |
| min1_w625_70_30_basis | test | 607 | 0.115416 | 0.240163 | 0.782688 | 0.375005 | -0.029725 | -0.024637 |
| min1_w500_huber_refit_partial | test | 607 | 0.115474 | 0.240210 | 0.762697 | 0.373740 | -0.029678 | -0.044628 |
| min1_w775_huber_refit_partial | test | 607 | 0.106316 | 0.240247 | 0.753071 | 0.379127 | -0.029641 | -0.054253 |
| min1_w600_70_30_basis | test | 607 | 0.112490 | 0.240471 | 0.782933 | 0.374754 | -0.029417 | -0.024392 |
| min1_w775_70_30_basis | test | 607 | 0.107798 | 0.240493 | 0.758897 | 0.378954 | -0.029395 | -0.048428 |
| min1_w800_huber_refit_partial | test | 607 | 0.105178 | 0.240637 | 0.761417 | 0.379816 | -0.029252 | -0.045907 |
| min1_w800_70_30_basis | test | 607 | 0.106429 | 0.241258 | 0.758787 | 0.380013 | -0.028631 | -0.048537 |
| min1_w550_70_30_basis | test | 607 | 0.114749 | 0.241505 | 0.750709 | 0.374602 | -0.028383 | -0.056615 |
| min1_w850_huber_refit_partial | test | 607 | 0.103804 | 0.241772 | 0.778254 | 0.381392 | -0.028117 | -0.029071 |
| min1_w500_70_30_basis | test | 607 | 0.118534 | 0.243109 | 0.777578 | 0.374918 | -0.026780 | -0.029747 |
| min1_w850_70_30_basis | test | 607 | 0.106698 | 0.243349 | 0.770609 | 0.382467 | -0.026539 | -0.036716 |
| min1_w900_huber_refit_partial | test | 607 | 0.102547 | 0.243822 | 0.783997 | 0.383559 | -0.026066 | -0.023328 |
| min1_w900_70_30_basis | test | 607 | 0.108258 | 0.246063 | 0.783739 | 0.385361 | -0.023825 | -0.023586 |
| current_pp258_operational_reference | test | 607 | 0.140976 | 0.269888 | 0.807325 | 0.397454 | 0.000000 | 0.000000 |
| min1_w800_huber_refit_partial | validation_oof | 519 | 0.095327 | 0.177354 | 0.576197 | 0.298713 | -0.028275 | -0.061691 |
| min1_w850_huber_refit_partial | validation_oof | 519 | 0.093414 | 0.177395 | 0.572921 | 0.299892 | -0.028233 | -0.064967 |
| min1_w775_huber_refit_partial | validation_oof | 519 | 0.095678 | 0.177440 | 0.577824 | 0.298306 | -0.028188 | -0.060064 |
| min1_w750_huber_refit_partial | validation_oof | 519 | 0.098162 | 0.177711 | 0.578309 | 0.297911 | -0.027918 | -0.059579 |
| min1_w725_huber_refit_partial | validation_oof | 519 | 0.099916 | 0.178064 | 0.578493 | 0.297536 | -0.027565 | -0.059395 |
| min1_w900_huber_refit_partial | validation_oof | 519 | 0.092410 | 0.178307 | 0.569616 | 0.301882 | -0.027322 | -0.068272 |
| min1_huber_refit_partial | validation_oof | 519 | 0.101568 | 0.178407 | 0.571291 | 0.297318 | -0.027222 | -0.066597 |
| min1_w700_huber_refit_partial | validation_oof | 519 | 0.101568 | 0.178407 | 0.571291 | 0.297318 | -0.027222 | -0.066597 |
| min1_w675_huber_refit_partial | validation_oof | 519 | 0.100893 | 0.178936 | 0.571257 | 0.297306 | -0.026693 | -0.066632 |
| min1_w800_70_30_basis | validation_oof | 519 | 0.099068 | 0.179103 | 0.586669 | 0.301231 | -0.026525 | -0.051219 |
| min1_w775_70_30_basis | validation_oof | 519 | 0.102992 | 0.179235 | 0.587293 | 0.300502 | -0.026394 | -0.050595 |
| min1_w850_70_30_basis | validation_oof | 519 | 0.096241 | 0.179477 | 0.589008 | 0.303298 | -0.026152 | -0.048880 |
| min1_w750_70_30_basis | validation_oof | 519 | 0.103933 | 0.179527 | 0.576264 | 0.299980 | -0.026102 | -0.061624 |
| min1_w650_huber_refit_partial | validation_oof | 519 | 0.101536 | 0.179581 | 0.581426 | 0.297496 | -0.026048 | -0.056462 |
| min1_w725_70_30_basis | validation_oof | 519 | 0.106839 | 0.179962 | 0.583359 | 0.299664 | -0.025666 | -0.054529 |
| min1_w625_huber_refit_partial | validation_oof | 519 | 0.101964 | 0.180263 | 0.580959 | 0.297856 | -0.025366 | -0.056929 |
| min1_w700_70_30_basis | validation_oof | 519 | 0.107480 | 0.180564 | 0.581859 | 0.299556 | -0.025065 | -0.056029 |
| min1_w900_70_30_basis | validation_oof | 519 | 0.096361 | 0.180754 | 0.589491 | 0.306165 | -0.024875 | -0.048397 |
| min1_w600_huber_refit_partial | validation_oof | 519 | 0.105340 | 0.181034 | 0.590468 | 0.298395 | -0.024595 | -0.047420 |
| min1_w675_70_30_basis | validation_oof | 519 | 0.108416 | 0.181274 | 0.589032 | 0.299655 | -0.024355 | -0.048856 |
| min1_w650_70_30_basis | validation_oof | 519 | 0.110209 | 0.182077 | 0.588882 | 0.299961 | -0.023551 | -0.049006 |
| min1_w625_70_30_basis | validation_oof | 519 | 0.110901 | 0.182975 | 0.588626 | 0.300475 | -0.022654 | -0.049262 |
| min1_w550_huber_refit_partial | validation_oof | 519 | 0.109591 | 0.183358 | 0.600981 | 0.300035 | -0.022271 | -0.036907 |
| min1_w600_70_30_basis | validation_oof | 519 | 0.113428 | 0.184121 | 0.593175 | 0.301194 | -0.021507 | -0.044714 |
| min1_w500_huber_refit_partial | validation_oof | 519 | 0.110809 | 0.186340 | 0.632058 | 0.302397 | -0.019289 | -0.005830 |
| min1_w550_70_30_basis | validation_oof | 519 | 0.119151 | 0.187289 | 0.613898 | 0.303244 | -0.018340 | -0.023990 |
| min1_w500_70_30_basis | validation_oof | 519 | 0.119126 | 0.190935 | 0.637793 | 0.306093 | -0.014694 | -0.000095 |
| current_pp258_operational_reference | validation_oof | 519 | 0.122707 | 0.205629 | 0.637888 | 0.323337 | 0.000000 | 0.000000 |

## 4. 선택 후보 반복 validation 시나리오
| candidate_label | scenario | mean_MdAPE | mean_MAPE | mean_p95_APE | current_pp258_MAPE_win_rate | current_pp258_p95_win_rate | current_pp258_all3_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| min1_w800_huber_refit_partial | artist_group_holdout | 0.095622 | 0.176920 | 0.570816 | 1.000000 | 0.976923 | 0.976923 |
| min1_w800_huber_refit_partial | confidence_stratified_rows | 0.095420 | 0.176608 | 0.571051 | 1.000000 | 0.980769 | 0.980769 |
| min1_w800_huber_refit_partial | full_validation | 0.095327 | 0.177354 | 0.576197 | 1.000000 | 1.000000 | 1.000000 |
| min1_w800_huber_refit_partial | price_band_stratified_rows | 0.096066 | 0.178075 | 0.576367 | 1.000000 | 0.973077 | 0.973077 |
| min1_w800_huber_refit_partial | risk_focus_bootstrap | 0.108947 | 0.206922 | 0.682024 | 0.980769 | 0.965385 | 0.942308 |
| min1_w800_huber_refit_partial | row_bootstrap | 0.097111 | 0.176654 | 0.571508 | 1.000000 | 0.880769 | 0.873077 |

## 5. 실행 설정
```json
{
  "experiment_id": "PP-WMIN7",
  "experiment_slug": "PP-WMIN7_warm_min1_weight_retuning",
  "created_at": "2026-06-12T23:07:01",
  "selection_policy": "validation repeated stability and validation replacement score only; fixed test is confirmation; 0604 is not used",
  "reference_candidate_label": "current_pp258_operational_reference",
  "wmin4_selected_candidate_label": "min1_huber_refit_partial",
  "svc_weights": [
    0.5,
    0.55,
    0.6,
    0.625,
    0.65,
    0.675,
    0.7,
    0.725,
    0.75,
    0.775,
    0.8,
    0.85,
    0.9
  ],
  "basis_formula": "weight * min1_svc_numeric_seed_mean + (1-weight) * pp_v8_compact_blend_mape_guarded",
  "huber_refit": {
    "mode": "WMIN3 partial",
    "current_70_30": "weight-retuned basis",
    "svc_fallback": "WMIN2 min1 SVC seed mean",
    "stable_config": {
      "candidate": "hcoef2_size_reliability_cap005_s050",
      "source_candidate": "residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50",
      "feature_key": "resid_basis_size_reliability",
      "alpha": 0.01,
      "cap": 0.05,
      "strength": 0.5,
      "purpose": "작은 폭 MAPE/p95 안정화 대안"
    }
  },
  "decision": {
    "decision_status": "adopt_candidate",
    "selected_candidate_label": "min1_w800_huber_refit_partial",
    "reason": "validation gate를 통과했고 fixed test 확인에서도 기존 PP258 운영 후보보다 MdAPE/MAPE/p95가 모두 낮다.",
    "selected_fixed_validation_MdAPE": 0.09532721279946713,
    "selected_fixed_validation_MAPE": 0.17735387101830122,
    "selected_fixed_validation_p95_APE": 0.5761968681437315,
    "selected_fixed_test_MdAPE": 0.1051779972895374,
    "selected_fixed_test_MAPE": 0.24063655775815587,
    "selected_fixed_test_p95_APE": 0.7614173838278141,
    "selected_validation_MAPE_win_rate": 0.9967948717948718,
    "selected_validation_p95_win_rate": 0.9628205128205128,
    "selected_validation_replacement_score": -0.028274688961340333
  }
}
```
