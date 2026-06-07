# v0.1 70:30 재예측 실험

## 목적

- 2026-06-04 신규 운영형 테스트 파일에 대해 v0.1 Warm 1순위 정책을 다시 적용한다.
- 전처리, 예측, 비교를 기능별 스크립트로 분리해 나중에 각 단계만 재실행할 수 있게 한다.

## 실행 순서

```bash
python3 experiments/track6/OP-0605_v01_70_30_reprediction/scripts/01_preprocess_features.py
python3 experiments/track6/OP-0605_v01_70_30_reprediction/scripts/02_predict_v01_70_30.py
python3 experiments/track6/OP-0605_v01_70_30_reprediction/scripts/03_compare_predictions.py
```

## 입력

- 가격 없는 운영 입력: `data/test_new_artworks_test_noprice_0604.csv`
- 가격 라벨 비교 입력: `data/test_new_artworks_test_0604.csv`
- v0.1 정책 파일: `models/track6/price_prediction_v0.1/config/model_policy_v0.1.json`

## 산출물

- 전처리 피처: `experiments/track6/OP-0605_v01_70_30_reprediction/data/features`
- 재예측 파일: `experiments/track6/OP-0605_v01_70_30_reprediction/outputs/predictions/predictions_all.csv`
- 비교 결과: `experiments/track6/OP-0605_v01_70_30_reprediction/outputs/comparison/candidate_metrics.csv`
- 보고서: `experiments/track6/OP-0605_v01_70_30_reprediction/reports/result_report.md`

## 현재 실행 결과 요약

- 전체 행: 6,873건
- Warm 행: 6,873건
- Cold 행: 0건
- 숫자 가격 라벨: 837건
- 50달러 미만 검수 필요 라벨: 8건

50달러 미만 검수 필요 라벨 제외 기준:

| 후보 | MdAPE | MAPE | p95_APE | 해석 |
|---|---:|---:|---:|---|
| 유사 작품 기반 중앙값 | 0.3714 | 0.8681 | 3.6706 | 기존 직접 산출 proxy |
| 기존 proxy 70% + legacy Huber 30% | 0.3656 | 0.6224 | 1.9915 | 이전 임시 조합 |
| v0.1 70:30 재예측 | 0.2708 | 0.3773 | 0.9946 | 이번 재실행 후보 |

## exact 해석

- v0.1 정책 식은 `0.70 * svc_numeric_seed_mean + 0.30 * pp_v8_compact_blend_mape_guarded`다.
- `svc_numeric_seed_mean`은 PP-SVC2와 같은 방식으로 seed 10개 Warm Huber를 재학습해 신규 데이터에 적용한다.
- `pp_v8_compact_blend_mape_guarded`는 원천 후보 전체가 신규 데이터용 단일 artifact로 저장되어 있지 않다.
- 이번 스크립트는 기존 PP-V8 validation/test 예측값을 CatBoost로 모사한 distillation component를 사용한다.
- 따라서 이번 결과는 v0.1 70:30 식을 재적용한 결과이지만, PP-V8 축은 source-decomposed exact가 아니라 재현용 component다.
- PP-V8 distillation fidelity는 validation-only 학습 후 test 기준 RMSE_log 약 0.3427, MdAE_log 약 0.1521이다.
