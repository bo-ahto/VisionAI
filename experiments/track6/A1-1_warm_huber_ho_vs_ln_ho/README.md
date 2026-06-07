# Track6 A1-1 Warm Huber Ho vs ln Ho

- 실험 목적: Warm Huber 모델에서 Ho 원값과 ln Ho 중 어느 표현이 더 나은지 비교
- 학습 데이터: `data/track6_split/features/warm/track6_train_warm_features.csv` + `data/track6_split/labels/track6_train_labels.csv`
- Warm 테스트 데이터: `data/track6_split/features/warm/track6_test_warm_warm_features.csv` + `data/track6_split/labels/track6_test_warm_labels.csv`
- 사용 코드: `experiments/track6/A1-1_warm_huber_ho_vs_ln_ho/scripts/run_experiment.py`
- 사용 프롬프트: `experiments/track6/A1-1_warm_huber_ho_vs_ln_ho/prompts/used_prompt.md`
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- 최저 MdAPE 변수: `ln Ho`

## 비교 조건

- `Ho`: `estimated_ho`
- `ln Ho`: `ln_estimated_ho`

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
