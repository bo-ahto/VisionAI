# PP-Z2 Warm LightGBM Quantile Cold형 확장 피처 재학습

## 목적
- Cold에서 사용한 작가 메타, 전시/갤러리, 검색 피처와 트리/분위수 모델 축을 Warm에 적용해 개선 여지가 있는지 확인한다.
- Track6 Warm split은 고정하고, 보정값과 후보 선택은 validation 기준으로만 판단한다.

## Validation Top 10
```csv
experiment_id,candidate,scope,split,policy,RMSE_log,MdAPE,MAPE,p95_APE,Within_30,Within_50,search_coverage_rate,search_covered_n,model,feature_strategy,n_features
PP-Z2,warm_base_search_context,warm,validation,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7273855880802423,0.28376086291161945,0.5552054145852592,1.5186297555548487,0.5202312138728323,0.6724470134874759,0.10404624277456648,54,LightGBM Quantile,Warm 기준 + 검색 핵심 문맥,45
PP-Z2,warm_base_meta_external_search_all,warm,validation,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7248196807860573,0.28919138332489014,0.5245497341883079,1.5626952194699975,0.5221579961464354,0.6859344894026975,0.10404624277456648,54,LightGBM Quantile,Warm 기준 + 작가 메타 + 전시/갤러리 + 검색 전체,90
PP-Z2,warm_base_external_interaction,warm,validation,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7187875336478723,0.29157772567367746,0.535186826708039,1.4703301177449968,0.51252408477842,0.6666666666666666,0.10404624277456648,54,LightGBM Quantile,Warm 기준 + 전시/갤러리 상호작용,65
PP-Z2,warm_base_artist_meta_all,warm,validation,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7251043997554304,0.2995170858859753,0.546995096456348,1.495665090788312,0.5009633911368016,0.6685934489402697,0.10404624277456648,54,LightGBM Quantile,Warm 기준 + 작가 메타 전체,35
PP-Z2,warm_base_search_all,warm,validation,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7280910036577511,0.30489019256506095,0.5555213353183823,1.5780530218096989,0.4932562620423892,0.6647398843930635,0.10404624277456648,54,LightGBM Quantile,Warm 기준 + 검색 전체,60
PP-Z2,warm_base_exhibition_gallery,warm,validation,warm_lightgbm_quantile_coldstyle_feature_expansion,0.6980416653625905,0.30566337544376543,0.4932554065079852,1.4841980177151173,0.4951830443159923,0.6685934489402697,0.10404624277456648,54,LightGBM Quantile,Warm 기준 + 전시/갤러리,39
PP-Z2,warm_base_artist_volume,warm,validation,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7287408209678763,0.3254837590845687,0.5260675129573028,1.5479327947842978,0.4662813102119461,0.6473988439306358,0.10404624277456648,54,LightGBM Quantile,Warm 기준 + 작가 학습량,15
PP-Z2,baseline_warm_base_existing_combo,warm,validation,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7436614904340733,0.34891748029410924,0.5774493151043835,1.5312580489385323,0.4527938342967245,0.6242774566473989,0.10404624277456648,54,LightGBM Quantile,Warm final artifact 기준 피처셋,13
```

## Test Top 10
```csv
experiment_id,candidate,scope,split,policy,RMSE_log,MdAPE,MAPE,p95_APE,Within_30,Within_50,search_coverage_rate,search_covered_n,model,feature_strategy,n_features
PP-Z2,warm_base_external_interaction,warm,test,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7165190921037287,0.3228933229322557,0.5732407917138088,1.9530899105627006,0.47611202635914335,0.6474464579901154,0.11367380560131796,69,LightGBM Quantile,Warm 기준 + 전시/갤러리 상호작용,65
PP-Z2,warm_base_meta_external_search_all,warm,test,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7127064627652078,0.32302868399413187,0.589957310399784,1.8571573422147785,0.4744645799011532,0.642504118616145,0.11367380560131796,69,LightGBM Quantile,Warm 기준 + 작가 메타 + 전시/갤러리 + 검색 전체,90
PP-Z2,warm_base_search_context,warm,test,warm_lightgbm_quantile_coldstyle_feature_expansion,0.721544241303453,0.325073179717021,0.58474018529173,1.976215765758414,0.47775947281713343,0.6293245469522241,0.11367380560131796,69,LightGBM Quantile,Warm 기준 + 검색 핵심 문맥,45
PP-Z2,warm_base_exhibition_gallery,warm,test,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7982207913757158,0.32806053852592315,0.5545177053567828,1.7836829656662354,0.4612850082372323,0.6490939044481054,0.11367380560131796,69,LightGBM Quantile,Warm 기준 + 전시/갤러리,39
PP-Z2,warm_base_search_all,warm,test,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7267163296503165,0.3336040468334246,0.6237156026742154,1.861985157987633,0.4695222405271829,0.6309719934102141,0.11367380560131796,69,LightGBM Quantile,Warm 기준 + 검색 전체,60
PP-Z2,warm_base_artist_meta_all,warm,test,warm_lightgbm_quantile_coldstyle_feature_expansion,0.7236618684546259,0.35142856281778007,0.5934594330506848,1.7765255658042256,0.4645799011532125,0.6095551894563427,0.11367380560131796,69,LightGBM Quantile,Warm 기준 + 작가 메타 전체,35
PP-Z2,warm_base_artist_volume,warm,test,warm_lightgbm_quantile_coldstyle_feature_expansion,0.8343018289381717,0.36565292582075204,0.593916025892392,2.0420498233791013,0.43657331136738053,0.5980230642504119,0.11367380560131796,69,LightGBM Quantile,Warm 기준 + 작가 학습량,15
PP-Z2,baseline_warm_base_existing_combo,warm,test,warm_lightgbm_quantile_coldstyle_feature_expansion,0.8692913920779332,0.40648762581631975,0.6790631035242922,2.313359804027164,0.3986820428336079,0.586490939044481,0.11367380560131796,69,LightGBM Quantile,Warm final artifact 기준 피처셋,13
```

## 산출물
- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/policy_map.csv`
