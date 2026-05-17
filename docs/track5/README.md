# Track 5 문서 인덱스

- 목적: Track 4에서 확인된 split 한계를 보완하고, 새 데이터 기준으로 가격 예측 모델을 다시 실험
- 핵심 원칙: 데이터셋 split을 먼저 고정한 뒤 모델/피처 실험 진행
- Warm / Cold는 분리 평가
- 실험 결과는 가설표, 결과표, 개별 실험 기록으로 관리

## 주요 문서

- 실험 계획서: `docs/track5/planning/experiment_plan_v1.md`
- split 생성 보고서: `docs/track5/dataset/split_report.md`
- 실험 인덱스: `docs/track5/experiments/INDEX.md`
- 가설 상태표: `docs/track5/tables/hypothesis_table.md`
- 실험 결과표: `docs/track5/tables/experiment_results_table.md`

## 주요 데이터

- 학습 데이터: `data/track5_split/track5_train.csv`
- Warm validation: `data/track5_split/track5_val_warm.csv`
- Warm test: `data/track5_split/track5_test_warm.csv`
- Cold validation: `data/track5_split/track5_val_cold.csv`
- Cold test: `data/track5_split/track5_test_cold.csv`

## 재생성 명령

- split 재생성:
  - `python3 scripts/track5/create_track5_splits.py`
