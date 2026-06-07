# PP-Z3 Warm CatBoost Cold형 확장 피처 재학습

## 목적
- Cold에서 사용한 작가 메타, 전시/갤러리, 검색 피처와 트리/분위수 모델 축을 Warm에 적용해 개선 여지가 있는지 확인한다.
- Track6 Warm split은 고정하고, 보정값과 후보 선택은 validation 기준으로만 판단한다.

## Validation Top 10
```csv
experiment_id,candidate,scope,split,policy,RMSE_log,MdAPE,MAPE,p95_APE,Within_30,Within_50,search_coverage_rate,search_covered_n,model,feature_strategy,n_features
PP-Z3,warm_base_artist_meta_all,warm,validation,warm_catboost_coldstyle_feature_expansion,0.5519893314008706,0.260635355858842,0.3939765341376036,1.106773654448422,0.5452793834296724,0.7572254335260116,0.10404624277456648,54,CatBoost RMSE,Warm 기준 + 작가 메타 전체,35
PP-Z3,warm_base_search_context,warm,validation,warm_catboost_coldstyle_feature_expansion,0.5538814037223349,0.26102637623996533,0.3977854174663142,1.1325603146273027,0.5414258188824663,0.7552986512524085,0.10404624277456648,54,CatBoost RMSE,Warm 기준 + 검색 핵심 문맥,45
PP-Z3,warm_base_search_all,warm,validation,warm_catboost_coldstyle_feature_expansion,0.5487107629882282,0.265178908367224,0.39340185823462326,1.1529595491972615,0.5394990366088632,0.7495183044315993,0.10404624277456648,54,CatBoost RMSE,Warm 기준 + 검색 전체,60
PP-Z3,warm_base_external_interaction,warm,validation,warm_catboost_coldstyle_feature_expansion,0.5503888165161047,0.26972027170438684,0.3933707317178374,1.148768349391486,0.5394990366088632,0.7418111753371869,0.10404624277456648,54,CatBoost RMSE,Warm 기준 + 전시/갤러리 상호작용,65
PP-Z3,warm_base_exhibition_gallery,warm,validation,warm_catboost_coldstyle_feature_expansion,0.5531041017980249,0.2739359635553528,0.4007460110642756,1.208491399004135,0.5240847784200385,0.7514450867052023,0.10404624277456648,54,CatBoost RMSE,Warm 기준 + 전시/갤러리,39
PP-Z3,warm_base_meta_external_search_all,warm,validation,warm_catboost_coldstyle_feature_expansion,0.5518016991200108,0.27590867426336835,0.39206315964431465,1.1465266717973126,0.535645472061657,0.7495183044315993,0.10404624277456648,54,CatBoost RMSE,Warm 기준 + 작가 메타 + 전시/갤러리 + 검색 전체,90
PP-Z3,warm_base_artist_volume,warm,validation,warm_catboost_coldstyle_feature_expansion,0.5539942013980399,0.2807840991295757,0.40066578619641274,1.1651738480994631,0.5202312138728323,0.7360308285163777,0.10404624277456648,54,CatBoost RMSE,Warm 기준 + 작가 학습량,15
PP-Z3,baseline_warm_base_existing_combo,warm,validation,warm_catboost_coldstyle_feature_expansion,0.559110319558683,0.294260759863964,0.411042158886114,1.2501355614118292,0.51252408477842,0.7225433526011561,0.10404624277456648,54,CatBoost RMSE,Warm final artifact 기준 피처셋,13
```

## Test Top 10
```csv
experiment_id,candidate,scope,split,policy,RMSE_log,MdAPE,MAPE,p95_APE,Within_30,Within_50,search_coverage_rate,search_covered_n,model,feature_strategy,n_features
PP-Z3,warm_base_artist_meta_all,warm,test,warm_catboost_coldstyle_feature_expansion,0.5499966727558756,0.3185691319431856,0.466312700397516,1.3888956991096304,0.4546952224052718,0.6985172981878089,0.11367380560131796,69,CatBoost RMSE,Warm 기준 + 작가 메타 전체,35
PP-Z3,warm_base_search_context,warm,test,warm_catboost_coldstyle_feature_expansion,0.5506480213215814,0.3206831706012599,0.4627944299908829,1.4370786647875924,0.4645799011532125,0.7051070840197694,0.11367380560131796,69,CatBoost RMSE,Warm 기준 + 검색 핵심 문맥,45
PP-Z3,baseline_warm_base_existing_combo,warm,test,warm_catboost_coldstyle_feature_expansion,0.6360498626839965,0.3229864363260302,0.5010438792049475,1.5513905662344825,0.46293245469522243,0.6705107084019769,0.11367380560131796,69,CatBoost RMSE,Warm final artifact 기준 피처셋,13
PP-Z3,warm_base_meta_external_search_all,warm,test,warm_catboost_coldstyle_feature_expansion,0.5493661763718105,0.322995020703121,0.45733754197929594,1.4644045541365425,0.4596375617792422,0.7018121911037891,0.11367380560131796,69,CatBoost RMSE,Warm 기준 + 작가 메타 + 전시/갤러리 + 검색 전체,90
PP-Z3,warm_base_search_all,warm,test,warm_catboost_coldstyle_feature_expansion,0.5499143914065443,0.3255099610638707,0.457570871097568,1.3915718992255557,0.46622734761120266,0.7067545304777595,0.11367380560131796,69,CatBoost RMSE,Warm 기준 + 검색 전체,60
PP-Z3,warm_base_external_interaction,warm,test,warm_catboost_coldstyle_feature_expansion,0.5523152318275785,0.3268391961639199,0.4614459482380466,1.507433542659447,0.4546952224052718,0.7018121911037891,0.11367380560131796,69,CatBoost RMSE,Warm 기준 + 전시/갤러리 상호작용,65
PP-Z3,warm_base_artist_volume,warm,test,warm_catboost_coldstyle_feature_expansion,0.6250988837339873,0.3285600803339753,0.47613778034377385,1.4438742327311158,0.4514003294892916,0.6820428336079077,0.11367380560131796,69,CatBoost RMSE,Warm 기준 + 작가 학습량,15
PP-Z3,warm_base_exhibition_gallery,warm,test,warm_catboost_coldstyle_feature_expansion,0.6135605421877479,0.33415280022721805,0.4752102086953006,1.4665244129664783,0.4546952224052718,0.6985172981878089,0.11367380560131796,69,CatBoost RMSE,Warm 기준 + 전시/갤러리,39
```

## 산출물
- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/policy_map.csv`
