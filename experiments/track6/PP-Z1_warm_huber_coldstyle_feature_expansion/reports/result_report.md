# PP-Z1 Warm Huber Cold형 확장 피처 재학습

## 목적
- Cold에서 사용한 작가 메타, 전시/갤러리, 검색 피처와 트리/분위수 모델 축을 Warm에 적용해 개선 여지가 있는지 확인한다.
- Track6 Warm split은 고정하고, 보정값과 후보 선택은 validation 기준으로만 판단한다.

## Validation Top 10
```csv
experiment_id,candidate,scope,split,policy,RMSE_log,MdAPE,MAPE,p95_APE,Within_30,Within_50,search_coverage_rate,search_covered_n,model,feature_strategy,n_features
PP-Z1,baseline_warm_base_existing_combo,warm,validation,warm_huber_coldstyle_feature_expansion,0.6446120239301169,0.21258310983821582,0.4166803017538871,1.319355563256341,0.5953757225433526,0.7321772639691715,0.10404624277456648,54,Huber,Warm final artifact 기준 피처셋,13
PP-Z1,warm_base_meta_external_search_all,warm,validation,warm_huber_coldstyle_feature_expansion,0.638395835127619,0.21283042067063726,0.4131075061986198,1.3343370029673138,0.5915221579961464,0.7456647398843931,0.10404624277456648,54,Huber,Warm 기준 + 작가 메타 + 전시/갤러리 + 검색 전체,90
PP-Z1,warm_base_artist_volume,warm,validation,warm_huber_coldstyle_feature_expansion,0.6492944292564649,0.2175960166652377,0.4088533105964351,1.306074323196452,0.5992292870905588,0.7456647398843931,0.10404624277456648,54,Huber,Warm 기준 + 작가 학습량,15
PP-Z1,warm_base_exhibition_gallery,warm,validation,warm_huber_coldstyle_feature_expansion,0.6353156139249122,0.22059442576640098,0.40647892121823254,1.2793976863501342,0.5992292870905588,0.7398843930635838,0.10404624277456648,54,Huber,Warm 기준 + 전시/갤러리,39
PP-Z1,warm_base_search_context,warm,validation,warm_huber_coldstyle_feature_expansion,0.6417061793383632,0.2207944900746351,0.4140632275375712,1.2960312827280263,0.6011560693641619,0.7360308285163777,0.10404624277456648,54,Huber,Warm 기준 + 검색 핵심 문맥,45
PP-Z1,warm_base_external_interaction,warm,validation,warm_huber_coldstyle_feature_expansion,0.63772078905689,0.22213110455987176,0.4131305791477758,1.3260735258229528,0.5953757225433526,0.7495183044315993,0.10404624277456648,54,Huber,Warm 기준 + 전시/갤러리 상호작용,65
PP-Z1,warm_base_artist_meta_all,warm,validation,warm_huber_coldstyle_feature_expansion,0.6420366675620973,0.22240161006064088,0.4137064740298667,1.2948604639104744,0.5992292870905588,0.7379576107899807,0.10404624277456648,54,Huber,Warm 기준 + 작가 메타 전체,35
PP-Z1,warm_base_search_all,warm,validation,warm_huber_coldstyle_feature_expansion,0.6411817426713271,0.22458799539147487,0.4125923034510076,1.353115403460883,0.5934489402697495,0.7456647398843931,0.10404624277456648,54,Huber,Warm 기준 + 검색 전체,60
```

## Test Top 10
```csv
experiment_id,candidate,scope,split,policy,RMSE_log,MdAPE,MAPE,p95_APE,Within_30,Within_50,search_coverage_rate,search_covered_n,model,feature_strategy,n_features
PP-Z1,warm_base_search_all,warm,test,warm_huber_coldstyle_feature_expansion,0.613074481446099,0.21947739662697566,0.48542033455069344,1.8119000421124314,0.5881383855024712,0.7347611202635914,0.11367380560131796,69,Huber,Warm 기준 + 검색 전체,60
PP-Z1,warm_base_artist_volume,warm,test,warm_huber_coldstyle_feature_expansion,0.6082498320086818,0.22138342057108015,0.48130040591501294,1.9082859799176695,0.5914332784184514,0.729818780889621,0.11367380560131796,69,Huber,Warm 기준 + 작가 학습량,15
PP-Z1,warm_base_exhibition_gallery,warm,test,warm_huber_coldstyle_feature_expansion,0.6129952576184519,0.2260178003433291,0.4809916378766756,1.887088815787471,0.586490939044481,0.7331136738056013,0.11367380560131796,69,Huber,Warm 기준 + 전시/갤러리,39
PP-Z1,warm_base_artist_meta_all,warm,test,warm_huber_coldstyle_feature_expansion,0.6153326364482159,0.22659212913691518,0.4881719712582257,1.8945321069852434,0.5881383855024712,0.7232289950576606,0.11367380560131796,69,Huber,Warm 기준 + 작가 메타 전체,35
PP-Z1,warm_base_search_context,warm,test,warm_huber_coldstyle_feature_expansion,0.6155014125254712,0.22724061932582104,0.48832093084490186,1.89012198990539,0.5881383855024712,0.7232289950576606,0.11367380560131796,69,Huber,Warm 기준 + 검색 핵심 문맥,45
PP-Z1,baseline_warm_base_existing_combo,warm,test,warm_huber_coldstyle_feature_expansion,0.6080536379575995,0.22742478152712733,0.49520126521975283,2.0130405516998966,0.5897858319604613,0.7232289950576606,0.11367380560131796,69,Huber,Warm final artifact 기준 피처셋,13
PP-Z1,warm_base_external_interaction,warm,test,warm_huber_coldstyle_feature_expansion,0.6130159149427549,0.22896008715738952,0.48130953777173613,1.7324038111550555,0.5848434925864909,0.7331136738056013,0.11367380560131796,69,Huber,Warm 기준 + 전시/갤러리 상호작용,65
PP-Z1,warm_base_meta_external_search_all,warm,test,warm_huber_coldstyle_feature_expansion,0.6119624392673382,0.22945909332196085,0.48186002108786063,1.7697730126892823,0.5881383855024712,0.7314662273476112,0.11367380560131796,69,Huber,Warm 기준 + 작가 메타 + 전시/갤러리 + 검색 전체,90
```

## 산출물
- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/policy_map.csv`
