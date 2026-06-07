# Track6 실험 결과 통합 CSV 안내

## 목적

- 각 실험 폴더에 흩어진 결과 CSV를 하나의 기준으로 모아 본다.
- 피처 조합별로 어떤 모델이 Warm / Cold에서 좋았는지 비교한다.
- 같은 실험 안에서 어떤 피처 조합이 가장 좋았는지 확인한다.

## 생성 스크립트

- 실행 파일: `scripts/track6/build_unified_experiment_metrics.py`
- 실행 명령:

```bash
python3 scripts/track6/build_unified_experiment_metrics.py
```

## 생성 파일

### 1. 전체 통합 long CSV

- 파일: `track6_all_experiment_model_metrics_long.csv`
- 용도:
  - 모든 실험 결과를 한 줄 단위로 모은 원본 통합표
  - 단위: `실험 x 피처 조합 x Warm/Cold x 모델`
- 주요 컬럼:
  - `experiment_id`
  - `experiment_dir`
  - `group_label`
  - `feature_block`
  - `features`
  - `scope`
  - `model_name`
  - `MdAPE`
  - `p95_APE`
  - `Within_30`
  - `RMSE_log`
  - `R2`
  - `source_csv`

### 2. 피처 조합별 모델 1~3위 CSV

- 파일: `track6_best_model_by_feature_block.csv`
- 용도:
  - 같은 피처 조합 안에서 어떤 모델이 1위, 2위, 3위인지 확인
- 순위 기준:
  - 1순위: `MdAPE` 낮은 모델
  - 2순위: `p95_APE` 낮은 모델
  - 3순위: `Within_30` 높은 모델
  - 4순위: `RMSE_log` 낮은 모델
  - 5순위: `R2` 높은 모델

### 3. Warm / Cold 요약 CSV

- 파일: `track6_feature_model_pivot_summary.csv`
- 용도:
  - 피처 조합별 Warm 최고 모델과 Cold 최고 모델을 한 줄에서 비교
  - 보고용으로 가장 보기 쉬운 표

### 4. 실험 내부 피처 차이 CSV

- 파일: `track6_feature_influence_delta.csv`
- 용도:
  - 같은 실험 안에서 가장 좋은 피처 조합과 다른 후보 피처 조합의 차이를 확인
  - `MdAPE_gap_vs_best`가 작을수록 1위 조합과 성능 차이가 작다.
  - `MdAPE_gap_pct_vs_best`가 클수록 1위 조합보다 많이 나쁘다.

### 5. 제외된 소스 목록

- 파일: `track6_unified_metric_skipped_sources.csv`
- 용도:
  - 결과 CSV가 없어 통합에서 제외된 폴더 확인
  - 실험이 아직 실행되지 않았거나 산출물이 없는 폴더를 점검할 때 사용

## 해석 기준

- 모델 성능 비교는 기본적으로 `MdAPE`를 먼저 본다.
- `MdAPE`가 비슷하면 `p95_APE`와 `Within_30`을 함께 본다.
- `RMSE_log`와 `R2`는 보조 지표로 사용한다.
- Warm과 Cold는 예측 상황이 다르므로 성능을 합쳐 판단하지 않는다.

