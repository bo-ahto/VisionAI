# PP-Q4 Probabilistic 모델 후보 검토

- 목적: 모델별 장점을 조합하고 커스텀해 Cold 성능 개선 가능성을 확인한다.
- 기준: validation에서 선택한 조합/가중치/정책을 test에 그대로 적용한다.

## 실행 상태

| 항목 | 값 |
|---|---|
| `experiment_id` | `PP-Q4` |
| `candidate` | `ngboost_probabilistic_regression` |
| `scope` | `cold` |
| `split` | `not_run` |
| `policy` | `optional_probabilistic_model` |
| `status` | `blocked_missing_dependency` |
| `notes` | `NGBoost는 현재 로컬 환경에 설치되어 있지 않아 실행하지 않음. 설치 후 확률분포 예측 후보로 재검증 가능.` |
