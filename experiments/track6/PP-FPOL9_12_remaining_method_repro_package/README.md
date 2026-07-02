# PP-FPOL9~12 남은 방법 재현 패키지

이 폴더는 FPOL6 상위 후보를 공통 source로 고정한 뒤, 남은 4개 방법을 동일 split과 동일 지표로 재현하기 위한 독립 패키지다.

## 재현 명령

```bash
python3 experiments/track6/PP-FPOL9_12_remaining_method_repro_package/scripts/run_remaining_methods.py --step all
```

패키지 폴더를 다른 위치로 옮긴 경우:

```bash
python3 scripts/run_remaining_methods.py --step all
```

## 포함 데이터

- `data/source_fpol6_candidate_predictions.csv`: FPOL6 상위 후보를 만들기 위한 validation/test row-level 예측 데이터
- `data/source_fpol6_candidate_metrics.csv`: FPOL6 후보 성능표
- `data/aux_p2_predictions.csv`: quantile width model routing 보조 예측
- `data/aux_l4_predictions.csv`: quantile width segment median 보조 예측
- `data/aux_m1_predictions.csv`: artist median + Huber residual 보조 예측
- `data/aux_l8_predictions.csv`: quantile feature + CatBoost residual 보조 예측
- `data/aux_l9_predictions.csv`: Huber quantile + CatBoost residual 보조 예측
- `data/train_index.csv`, `data/valid_index.csv`, `data/test_index.csv`: 원본 split 재현용 row id

## 실험 구성

1. `PP-FPOL9`: quantile width 기반 동적 cap/strength
2. `PP-FPOL10`: 모델 간 예측 gap 기반 라우팅
3. `PP-FPOL11`: tail-only 보정
4. `PP-FPOL12`: segment median + Huber residual 혼합

## 출력

실행 후 아래 파일이 생성된다.

- `reports/final_remaining_method_summary.md`
- `reports/final_remaining_method_summary.html`
- `outputs/final_remaining_method_recommendations.csv`
- `outputs/all_fpol9_12_test_metrics.csv`
- `experiments/PP-FPOL9_quantile_width_dynamic_cap_strength/outputs/candidate_metrics.csv`
- `experiments/PP-FPOL10_model_gap_routing/outputs/candidate_metrics.csv`
- `experiments/PP-FPOL11_tail_only_correction/outputs/candidate_metrics.csv`
- `experiments/PP-FPOL12_segment_median_huber_mix/outputs/candidate_metrics.csv`

## 주의

이 패키지는 새 원천 모델을 재학습하는 패키지가 아니라, 기존 학습/검증/test split에서 생성된 row-level 예측과 보조 예측을 입력으로 후처리 후보를 재현하는 패키지다. 정답 로그/가격은 validation/test 성능 계산에 포함되어 있으며, 후보 선택과 성능 검증의 재현성을 위해 함께 포함한다.
