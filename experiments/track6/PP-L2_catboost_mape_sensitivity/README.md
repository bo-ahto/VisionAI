# PP-L2 CatBoost 옵션별 MAPE 민감도

- 실행 시각: `2026-06-02T13:51:06`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `PP-L2_depth8_lr0.05_warm` | `warm` | `0.3053` | `0.4102` | `1.3286` | `0.5540` | `519` |
| `PP-L2_l2_3_warm` | `warm` | `0.3094` | `0.4324` | `1.3956` | `0.5745` | `519` |
| `PP-L2_depth6_lr0.05_warm` | `warm` | `0.3114` | `0.4289` | `1.3032` | `0.5736` | `519` |
| `PP-L2_depth6_lr0.03_warm` | `warm` | `0.3207` | `0.4467` | `1.3664` | `0.5864` | `519` |
| `PP-L2_depth4_lr0.03_warm` | `warm` | `0.3270` | `0.4625` | `1.5802` | `0.6012` | `519` |
| `PP-L2_l2_10_warm` | `warm` | `0.3283` | `0.4388` | `1.3388` | `0.5831` | `519` |
| `PP-L2_depth8_lr0.03_warm` | `warm` | `0.3290` | `0.4353` | `1.3184` | `0.5791` | `519` |
| `PP-L2_depth4_lr0.05_warm` | `warm` | `0.3343` | `0.4595` | `1.4911` | `0.6009` | `519` |
| `PP-L2_depth8_lr0.05_cold` | `cold` | `0.4121` | `0.7398` | `2.3233` | `0.7062` | `2753` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |
| `PP-L2_depth6_lr0.05_cold` | `cold` | `0.4437` | `0.7813` | `2.7258` | `0.7255` | `2753` |
| `PP-L2_depth8_lr0.03_cold` | `cold` | `0.4460` | `0.7675` | `2.6887` | `0.7180` | `2753` |
| `PP-L2_l2_3_cold` | `cold` | `0.4489` | `0.7837` | `2.7670` | `0.7256` | `2753` |
| `PP-L2_l2_10_cold` | `cold` | `0.4581` | `0.7889` | `2.8044` | `0.7296` | `2753` |
| `PP-L2_depth4_lr0.05_cold` | `cold` | `0.4584` | `0.8250` | `3.1728` | `0.7449` | `2753` |
| `PP-L2_depth4_lr0.03_cold` | `cold` | `0.4662` | `0.8572` | `3.3785` | `0.7582` | `2753` |
| `PP-L2_depth6_lr0.03_cold` | `cold` | `0.4728` | `0.8039` | `2.9311` | `0.7356` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `PP-L2_depth4_lr0.03_cold` | `cold` | `B1_Cold_CatBoost` | `0.0966` | `0.0803` | `0.1142` | `0.0000` |
| `PP-L2_depth4_lr0.05_cold` | `cold` | `B1_Cold_CatBoost` | `0.0643` | `0.0524` | `0.0749` | `0.0000` |
| `PP-L2_depth6_lr0.03_cold` | `cold` | `B1_Cold_CatBoost` | `0.0433` | `0.0342` | `0.0525` | `0.0000` |
| `PP-L2_depth6_lr0.05_cold` | `cold` | `B1_Cold_CatBoost` | `0.0206` | `0.0152` | `0.0257` | `0.0000` |
| `PP-L2_depth8_lr0.03_cold` | `cold` | `B1_Cold_CatBoost` | `0.0068` | `0.0015` | `0.0118` | `0.0000` |
| `PP-L2_depth8_lr0.05_cold` | `cold` | `B1_Cold_CatBoost` | `-0.0208` | `-0.0275` | `-0.0144` | `0.0000` |
| `PP-L2_l2_10_cold` | `cold` | `B1_Cold_CatBoost` | `0.0283` | `0.0202` | `0.0358` | `0.0000` |
| `PP-L2_l2_3_cold` | `cold` | `B1_Cold_CatBoost` | `0.0230` | `0.0172` | `0.0288` | `0.0000` |
| `PP-L2_depth4_lr0.03_warm` | `warm` | `B0_Warm_Huber` | `0.0458` | `-0.0060` | `0.1010` | `0.0002` |
| `PP-L2_depth4_lr0.05_warm` | `warm` | `B0_Warm_Huber` | `0.0428` | `-0.0076` | `0.0952` | `0.0001` |
| `PP-L2_depth6_lr0.03_warm` | `warm` | `B0_Warm_Huber` | `0.0300` | `-0.0186` | `0.0805` | `0.0010` |
| `PP-L2_depth6_lr0.05_warm` | `warm` | `B0_Warm_Huber` | `0.0122` | `-0.0364` | `0.0576` | `0.0035` |
| `PP-L2_depth8_lr0.03_warm` | `warm` | `B0_Warm_Huber` | `0.0186` | `-0.0280` | `0.0697` | `0.0026` |
| `PP-L2_depth8_lr0.05_warm` | `warm` | `B0_Warm_Huber` | `-0.0065` | `-0.0508` | `0.0402` | `0.0446` |
| `PP-L2_l2_10_warm` | `warm` | `B0_Warm_Huber` | `0.0222` | `-0.0261` | `0.0709` | `0.0013` |
| `PP-L2_l2_3_warm` | `warm` | `B0_Warm_Huber` | `0.0157` | `-0.0316` | `0.0648` | `0.0050` |
| `PP-L2_depth6_lr0.04_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth6_lr0.04_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth6_lr0.04_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth6_lr0.04_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth8_lr0.05_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth8_lr0.05_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth8_lr0.05_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth8_lr0.05_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth6_lr0.04_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth6_lr0.04_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth6_lr0.04_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth6_lr0.04_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth8_lr0.05_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth8_lr0.05_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth8_lr0.05_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L2_depth8_lr0.05_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |

## 구간 기준

