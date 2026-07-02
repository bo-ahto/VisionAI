# PP-WLITE-NOREPLAY operational feature path

## 목적

`fixed_replay_feature_store.csv`를 쓰지 않고 Warm-lite unified current 모델을 실행했다.
테스트 CSV는 평가 입력과 정답 라벨로만 사용했고, 모델 입력 feature는 API adapter의 운영 feature builder로 다시 계산했다.

## 핵심 설정

- fixed replay feature store: disabled by `adapter.warm_lite_unified_feature_store = pd.DataFrame()`
- route policy: `warm_lite_unified_current`
- input rows: `607`
- predicted rows: `607`
- error rows: `0`
- feature store hit rows: `0`

## Metrics

```json
{
  "n": 607,
  "MdAPE": 0.08697002277019135,
  "MAPE": 0.22368207891309544,
  "p95_APE": 0.8203661800254315,
  "RMSE_log": 0.38282311543666864,
  "APE_gt_1": 21,
  "APE_gt_5": 2
}
```

## Outputs

- `outputs/no_replay_predictions.csv`
- `outputs/no_replay_errors.csv`
- `artifacts/summary.json`
