# PP-S2 Cold Quantile LightGBM 선행 + CatBoost residual

- 목적: 모델 순서 변경, 목적함수 커스텀, 메타 조합이 기존 PP-Q/PP-R 이후 추가 개선을 주는지 확인한다.
- 근거: CatBoost/LightGBM의 MAPE/Quantile/Huber 목적함수와 stacking의 모델 출력값 결합 구조를 Track6 후보에 적용한다.
- 기준: 가중치, residual 모델, meta 모델, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `n1_quantile_lgb_huber_cap0.5_s1` | `test` | `ordered_residual_model` | `0.4765` | `1.2453` | `3.5543` | `0.9451` |
| `n1_quantile_lgb_huber_cap0.35_s1` | `test` | `ordered_residual_model` | `0.4765` | `1.2580` | `3.5804` | `0.9438` |
| `n1_quantile_lgb_huber_cap0.2_s1` | `test` | `ordered_residual_model` | `0.4765` | `1.2777` | `3.8467` | `0.9424` |
| `n1_quantile_lgb_ridge_10_cap0.35_s0.5` | `test` | `ordered_residual_model` | `0.4778` | `1.2657` | `3.9392` | `0.9407` |
| `n1_quantile_lgb_ridge_1_cap0.35_s0.5` | `test` | `ordered_residual_model` | `0.4779` | `1.2664` | `3.9377` | `0.9409` |
| `n1_quantile_lgb_ridge_10_cap0.5_s1` | `test` | `ordered_residual_model` | `0.4781` | `1.2570` | `3.6831` | `0.9432` |
| `n1_quantile_lgb_ridge_10_cap0.35_s1` | `test` | `ordered_residual_model` | `0.4781` | `1.2700` | `3.7381` | `0.9432` |
| `n1_quantile_lgb_ridge_10_cap0.2_s1` | `test` | `ordered_residual_model` | `0.4781` | `1.2901` | `3.8358` | `0.9428` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.5_s0.5` | `test` | `ordered_residual_model` | `0.4783` | `1.2515` | `3.9075` | `0.9358` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.5_s0.5` | `test` | `ordered_residual_model` | `0.4783` | `1.2515` | `3.9075` | `0.9358` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.35_s0.5` | `test` | `ordered_residual_model` | `0.4783` | `1.2615` | `3.9254` | `0.9375` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.35_s0.5` | `test` | `ordered_residual_model` | `0.4783` | `1.2615` | `3.9254` | `0.9375` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.2_s0.5` | `test` | `ordered_residual_model` | `0.4783` | `1.2760` | `3.9859` | `0.9393` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.2_s0.5` | `test` | `ordered_residual_model` | `0.4783` | `1.2760` | `3.9859` | `0.9393` |
| `n1_quantile_lgb_ridge_1_cap0.2_s1` | `test` | `ordered_residual_model` | `0.4783` | `1.2912` | `3.8346` | `0.9431` |
| `n1_quantile_lgb_huber_cap0.35_s0.5` | `test` | `ordered_residual_model` | `0.4784` | `1.2595` | `3.8870` | `0.9407` |
| `n1_quantile_lgb_huber_cap0.2_s0.5` | `test` | `ordered_residual_model` | `0.4786` | `1.2717` | `4.1284` | `0.9411` |
| `n1_quantile_lgb_ridge_1_cap0.5_s1` | `test` | `ordered_residual_model` | `0.4786` | `1.2584` | `3.6672` | `0.9438` |
| `n1_quantile_lgb_ridge_1_cap0.35_s1` | `test` | `ordered_residual_model` | `0.4786` | `1.2713` | `3.7391` | `0.9436` |
| `n1_quantile_lgb_ridge_1_cap0.2_s0.5` | `test` | `ordered_residual_model` | `0.4790` | `1.2786` | `4.0827` | `0.9416` |
| `n1_quantile_lgb_ridge_10_cap0.2_s0.5` | `test` | `ordered_residual_model` | `0.4790` | `1.2780` | `4.0784` | `0.9414` |
| `n1_quantile_lgb_ridge_1_cap0.5_s0.5` | `test` | `ordered_residual_model` | `0.4795` | `1.2581` | `3.8950` | `0.9403` |
| `n1_quantile_lgb_huber_cap0.5_s0.5` | `test` | `ordered_residual_model` | `0.4795` | `1.2509` | `3.8647` | `0.9405` |
| `n1_quantile_lgb_ridge_10_cap0.5_s0.5` | `test` | `ordered_residual_model` | `0.4796` | `1.2573` | `3.8958` | `0.9400` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.2_s1` | `test` | `ordered_residual_model` | `0.4801` | `1.2903` | `3.8625` | `0.9397` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.2_s1` | `test` | `ordered_residual_model` | `0.4801` | `1.2903` | `3.8625` | `0.9397` |
| `base_n1_quantile_lgb` | `test` | `stage1_base_model` | `0.4810` | `1.2743` | `4.3168` | `0.9436` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.35_s1` | `test` | `ordered_residual_model` | `0.4854` | `1.2691` | `3.5088` | `0.9390` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.35_s1` | `test` | `ordered_residual_model` | `0.4854` | `1.2691` | `3.5088` | `0.9390` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.5_s1` | `test` | `ordered_residual_model` | `0.4858` | `1.2545` | `3.5042` | `0.9371` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.5_s1` | `test` | `ordered_residual_model` | `0.4858` | `1.2545` | `3.5042` | `0.9371` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.5_s1` | `validation` | `ordered_residual_model` | `0.3126` | `0.5278` | `1.7015` | `0.6211` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.5_s1` | `validation` | `ordered_residual_model` | `0.3126` | `0.5278` | `1.7015` | `0.6211` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.35_s1` | `validation` | `ordered_residual_model` | `0.3149` | `0.5444` | `1.7203` | `0.6274` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.35_s1` | `validation` | `ordered_residual_model` | `0.3149` | `0.5444` | `1.7203` | `0.6274` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.2_s1` | `validation` | `ordered_residual_model` | `0.3225` | `0.5825` | `1.7369` | `0.6395` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.2_s1` | `validation` | `ordered_residual_model` | `0.3225` | `0.5825` | `1.7369` | `0.6395` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.5_s0.5` | `validation` | `ordered_residual_model` | `0.3388` | `0.5834` | `1.6819` | `0.6408` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.5_s0.5` | `validation` | `ordered_residual_model` | `0.3388` | `0.5834` | `1.6819` | `0.6408` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.35_s0.5` | `validation` | `ordered_residual_model` | `0.3408` | `0.5940` | `1.6819` | `0.6458` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.35_s0.5` | `validation` | `ordered_residual_model` | `0.3408` | `0.5940` | `1.6819` | `0.6458` |
| `n1_quantile_lgb_huber_cap0.5_s1` | `validation` | `ordered_residual_model` | `0.3528` | `0.5759` | `1.7203` | `0.6476` |
| `n1_quantile_lgb_ridge_1_cap0.5_s1` | `validation` | `ordered_residual_model` | `0.3559` | `0.5838` | `1.7454` | `0.6478` |
| `n1_quantile_lgb_ridge_1_cap0.35_s1` | `validation` | `ordered_residual_model` | `0.3561` | `0.5930` | `1.7593` | `0.6498` |
| `n1_quantile_lgb_huber_cap0.35_s1` | `validation` | `ordered_residual_model` | `0.3563` | `0.5859` | `1.7472` | `0.6495` |
| `n1_quantile_lgb_huber_cap0.2_s1` | `validation` | `ordered_residual_model` | `0.3563` | `0.6108` | `1.7613` | `0.6550` |
| `n1_quantile_lgb_ridge_10_cap0.5_s1` | `validation` | `ordered_residual_model` | `0.3570` | `0.5839` | `1.7409` | `0.6478` |
| `n1_quantile_lgb_ridge_10_cap0.35_s1` | `validation` | `ordered_residual_model` | `0.3572` | `0.5931` | `1.7569` | `0.6498` |
| `n1_quantile_lgb_ridge_10_cap0.2_s1` | `validation` | `ordered_residual_model` | `0.3608` | `0.6149` | `1.7740` | `0.6553` |
| `n1_quantile_lgb_ridge_1_cap0.2_s1` | `validation` | `ordered_residual_model` | `0.3621` | `0.6148` | `1.7792` | `0.6553` |
| `n1_quantile_lgb_catboost_mae_residual_cap0.2_s0.5` | `validation` | `ordered_residual_model` | `0.3627` | `0.6180` | `1.7416` | `0.6557` |
| `n1_quantile_lgb_catboost_quantile_residual_cap0.2_s0.5` | `validation` | `ordered_residual_model` | `0.3627` | `0.6180` | `1.7416` | `0.6557` |
| `n1_quantile_lgb_huber_cap0.5_s0.5` | `validation` | `ordered_residual_model` | `0.3749` | `0.6076` | `1.7078` | `0.6568` |
| `n1_quantile_lgb_ridge_1_cap0.5_s0.5` | `validation` | `ordered_residual_model` | `0.3762` | `0.6137` | `1.7213` | `0.6583` |
| `n1_quantile_lgb_huber_cap0.35_s0.5` | `validation` | `ordered_residual_model` | `0.3763` | `0.6154` | `1.7078` | `0.6589` |
| `n1_quantile_lgb_ridge_10_cap0.5_s0.5` | `validation` | `ordered_residual_model` | `0.3764` | `0.6138` | `1.7218` | `0.6583` |
| `n1_quantile_lgb_ridge_10_cap0.35_s0.5` | `validation` | `ordered_residual_model` | `0.3766` | `0.6199` | `1.7218` | `0.6600` |
| `n1_quantile_lgb_ridge_1_cap0.35_s0.5` | `validation` | `ordered_residual_model` | `0.3769` | `0.6198` | `1.7213` | `0.6600` |
| `n1_quantile_lgb_ridge_10_cap0.2_s0.5` | `validation` | `ordered_residual_model` | `0.3770` | `0.6340` | `1.7663` | `0.6645` |
| `n1_quantile_lgb_ridge_1_cap0.2_s0.5` | `validation` | `ordered_residual_model` | `0.3770` | `0.6340` | `1.7664` | `0.6644` |
| `n1_quantile_lgb_huber_cap0.2_s0.5` | `validation` | `ordered_residual_model` | `0.3795` | `0.6319` | `1.7529` | `0.6641` |
| `base_n1_quantile_lgb` | `validation` | `stage1_base_model` | `0.3972` | `0.6618` | `1.7709` | `0.6798` |
