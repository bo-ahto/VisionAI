# Track 5 Experiment Artifacts

- `results/`: 실험별 metrics JSON
- `predictions/`: 실험별 예측 결과 CSV
- `models/`: 최종 후보 모델 artifact

## 원칙

- `data/track5_split/`은 고정 데이터셋
- `data/track5/results/`는 실험 결과 요약
- `data/track5/predictions/`는 상세 오차 분석용 예측값
- 최종 모델 확정 전까지 `models/`에는 임시 artifact를 남기지 않음
