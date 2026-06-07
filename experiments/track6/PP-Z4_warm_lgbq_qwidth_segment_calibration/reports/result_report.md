# PP-Z4 Warm LightGBM Quantile q-width 구간 보정

## 목적
- Cold에서 사용한 작가 메타, 전시/갤러리, 검색 피처와 트리/분위수 모델 축을 Warm에 적용해 개선 여지가 있는지 확인한다.
- Track6 Warm split은 고정하고, 보정값과 후보 선택은 validation 기준으로만 판단한다.

## Validation Top 10
```csv
experiment_id,candidate,scope,split,policy,RMSE_log,MdAPE,MAPE,p95_APE,Within_30,Within_50,search_coverage_rate,search_covered_n,base_candidate,model,segment_col,min_rows,cap
PP-Z4,warm_base_search_context__pred_x_qwidth_min30_cap0.25,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7343403655596759,0.2681093673544959,0.5303593176637869,1.2460646908433803,0.5317919075144508,0.6840077071290944,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,30,0.25
PP-Z4,warm_base_search_context__pred_x_qwidth_min30_cap0.15,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7320484623890329,0.26930040739217986,0.5382542443423753,1.3069149215610625,0.5260115606936416,0.6840077071290944,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,30,0.15
PP-Z4,warm_base_search_context__size_x_qwidth_min30_cap0.25,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7304767266152236,0.27826219369196853,0.5601853927342587,1.5167447340498856,0.5260115606936416,0.674373795761079,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,size_x_qwidth,30,0.25
PP-Z4,warm_base_search_context__pred_x_qwidth_min50_cap0.15,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7310092612312357,0.27985940587348673,0.5512597871651672,1.4732659973864128,0.5202312138728323,0.6840077071290944,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,50,0.15
PP-Z4,warm_base_search_context__pred_x_qwidth_min50_cap0.25,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7310092612312357,0.27985940587348673,0.5512597871651672,1.4732659973864128,0.5202312138728323,0.6840077071290944,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,50,0.25
PP-Z4,warm_base_search_context__pred_x_qwidth_min50_cap0.1,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7289480161970365,0.2805227215311681,0.5535574221876585,1.4761578006393183,0.5144508670520231,0.6820809248554913,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,50,0.1
PP-Z4,base_warm_base_search_context,warm,validation,warm_lgbq_qwidth_segment_base,0.7273855880802423,0.28376086291161945,0.5552054145852592,1.5186297555548487,0.5202312138728323,0.6724470134874759,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,none,0,0.0
PP-Z4,warm_base_search_context__size_x_qwidth_min30_cap0.05,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7259923343413103,0.2850067257035788,0.5612729605596317,1.5167447340498856,0.5144508670520231,0.6685934489402697,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,size_x_qwidth,30,0.05
PP-Z4,warm_base_search_context__size_x_qwidth_min30_cap0.15,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7272135074725803,0.28850268456124367,0.5655800881516012,1.5167447340498856,0.5202312138728323,0.674373795761079,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,size_x_qwidth,30,0.15
PP-Z4,warm_base_search_context__pred_x_qwidth_min30_cap0.1,warm,validation,warm_lgbq_qwidth_segment_calibration,0.7292941456505825,0.29041304686222946,0.5451294852697601,1.384341331080952,0.51252408477842,0.6820809248554913,0.10404624277456648,54,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,30,0.1
```

## Test Top 10
```csv
experiment_id,candidate,scope,split,policy,RMSE_log,MdAPE,MAPE,p95_APE,Within_30,Within_50,search_coverage_rate,search_covered_n,base_candidate,model,segment_col,min_rows,cap
PP-Z4,warm_base_search_context__pred_x_qwidth_min30_cap0.25,warm,test,warm_lgbq_qwidth_segment_calibration,0.7216584745073994,0.3170856816343296,0.5553137869058326,1.7700892915272248,0.4728171334431631,0.6441515650741351,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,30,0.25
PP-Z4,warm_base_search_context__pred_x_qwidth_min30_cap0.15,warm,test,warm_lgbq_qwidth_segment_calibration,0.7181284769273213,0.31810156048668753,0.5617208053430186,1.9213494410878171,0.4645799011532125,0.6441515650741351,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,30,0.15
PP-Z4,warm_base_search_context__size_x_qwidth_min30_cap0.05,warm,test,warm_lgbq_qwidth_segment_calibration,0.7203189580641605,0.31827482221797965,0.5939154577262212,1.9422893737928686,0.4645799011532125,0.627677100494234,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,size_x_qwidth,30,0.05
PP-Z4,warm_base_search_context__pred_x_qwidth_min50_cap0.15,warm,test,warm_lgbq_qwidth_segment_calibration,0.7156434908054287,0.32055290559597094,0.5722530940157939,1.9213494410878171,0.4645799011532125,0.6392092257001647,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,50,0.15
PP-Z4,warm_base_search_context__pred_x_qwidth_min50_cap0.25,warm,test,warm_lgbq_qwidth_segment_calibration,0.7156434908054287,0.32055290559597094,0.5722530940157939,1.9213494410878171,0.4645799011532125,0.6392092257001647,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,50,0.25
PP-Z4,warm_base_search_context__pred_x_qwidth_min50_cap0.1,warm,test,warm_lgbq_qwidth_segment_calibration,0.7158203221676294,0.3208208411919388,0.5767310831776677,1.9488742112120365,0.46787479406919275,0.6375617792421746,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,50,0.1
PP-Z4,warm_base_search_context__pred_x_qwidth_min80_cap0.05,warm,test,warm_lgbq_qwidth_segment_calibration,0.7220151800619462,0.3208208411919388,0.5782960247364284,1.9437680164446491,0.47611202635914335,0.6375617792421746,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,80,0.05
PP-Z4,warm_base_search_context__pred_x_qwidth_min80_cap0.1,warm,test,warm_lgbq_qwidth_segment_calibration,0.7220151800619462,0.3208208411919388,0.5782960247364284,1.9437680164446491,0.47611202635914335,0.6375617792421746,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,80,0.1
PP-Z4,warm_base_search_context__pred_x_qwidth_min80_cap0.15,warm,test,warm_lgbq_qwidth_segment_calibration,0.7220151800619462,0.3208208411919388,0.5782960247364284,1.9437680164446491,0.47611202635914335,0.6375617792421746,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,80,0.15
PP-Z4,warm_base_search_context__pred_x_qwidth_min80_cap0.25,warm,test,warm_lgbq_qwidth_segment_calibration,0.7220151800619462,0.3208208411919388,0.5782960247364284,1.9437680164446491,0.47611202635914335,0.6375617792421746,0.11367380560131796,69,warm_base_search_context,LightGBM Quantile,pred_x_qwidth,80,0.25
```

## 산출물
- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/policy_map.csv`
