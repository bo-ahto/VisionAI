# Track 5 Split

- 목적: Track 5 가격 예측 실험용 train / validation / test split
- 생성 명령:
  - `python3 scripts/track5/create_track5_splits.py`
- 기준:
  - Warm: 평가 작가가 train에 존재
  - Cold: 평가 작가가 train에 존재하지 않음
- 보고서:
  - `docs/track5/dataset/split_report.md`

## 파일

- `track5_train.csv`: 학습 데이터
- `track5_val_warm.csv`: Warm validation
- `track5_test_warm.csv`: Warm test
- `track5_val_cold.csv`: Cold validation
- `track5_test_cold.csv`: Cold test
- `track5_split_membership.csv`: split membership
- `track5_split_summary.json`: split 생성 요약
