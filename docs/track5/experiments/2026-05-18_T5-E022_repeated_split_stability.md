# T5-E022 반복 split 안정성 검증

- 날짜: 2026-05-18
- 관련 가설: T5-H25
- 목적: Track5 결론이 고정 split 1회에만 의존하는지 확인
- 사용 데이터: Track5 전체 split을 다시 합친 뒤 보조 split 3개 생성
- 사용 스크립트: `scripts/track5/run_t5_e022_e025_audit_closure.py`
- 결과 파일: `data/track5/results/t5_e022_e025_audit_closure_metrics.json`
- 예측 파일: `data/track5/predictions/t5_e022_e025_audit_closure_predictions.csv`

## 실험 방법

- Track5 전체 행을 합친 뒤 seed 3개로 보조 split 생성
- 각 seed에서 Cold 작가는 train에서 완전히 제외
- 각 seed에서 Warm 작가는 train에 2개 이상 남기고 일부 작품을 holdout
- Warm 후보는 `HuberRegressor + warm_full_size` 사용
- Cold 후보는 `QuantileRegressor + cold_full_size` 사용
- 감사용 빠른 검증이라 Huber `max_iter=500`으로 실행
- 최종 artifact 학습 설정은 기존 T5-E011의 `max_iter=3000` 기준을 유지

## 주요 결과

- Warm median APE 평균: `0.1668`
- Warm median APE 범위: `0.1496 ~ 0.1786`
- Warm p95 APE 평균: `0.9674`
- Cold median APE 평균: `0.4144`
- Cold median APE 범위: `0.3944 ~ 0.4416`
- Cold p95 APE 평균: `2.2281`

## 해석

- Warm은 반복 split에서도 median APE가 `0.15~0.18` 수준으로 유지됨
- Cold는 median APE가 `0.39~0.44` 범위로 유지되지만 p95 변동이 큼
- 따라서 Warm/Cold 분리 자체는 유지 가능
- Cold는 split에 따라 큰 오차 구간이 흔들리므로 단일 가격만으로 운영 판단하기 어려움

## 결론

- 상태: 검증 완료
- Track5는 `1작가 1작품` 평가 문제를 상당 부분 완화했음
- 다만 Cold tail risk는 반복 split에서도 남아 있어 가격 범위/경고 정책이 필요함
