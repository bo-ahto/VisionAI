# Track6 D6 depth x 작품 유형 숫자형 교차항 실험 결과

- 실험 목적: 작품 유형에 따라 깊이 정보의 가격 효과가 달라지는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `D6 교차항: 깊이 x 작품 유형 전체` / `Huber` / MdAPE `0.7463`
- Cold 최고: `D6 교차항: 깊이 x 작품 유형 전체` / `LightGBM` / MdAPE `0.6467`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/D6_depth_artwork_type_numeric_interaction/experiment_config.json`
- 사용 프롬프트: `experiments/track6/D6_depth_artwork_type_numeric_interaction/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 조각이나 입체 후보 작품에서 깊이 정보가 작품 유형에 따라 다르게 작용하는지 확인한다.
- 실험군: Group D: 작품 변수끼리의 교차항
- 기준선: depth_cm + has_depth + is_3d_candidate + artwork_type
- 학습 피처: 기준선과 depth_cm x 작품 유형 교차항
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 구현 방식: depth_cm은 숫자형으로 유지하고, 작품 유형별 표시값과 곱한 숫자형 교차항을 생성한다.
- 주의: depth_cm 결측이 많으므로 전체 성능뿐 아니라 p95 APE와 3D 후보 구간 해석이 중요하다.
- 해석 기준: 교차항 추가 후 MdAPE 또는 RMSE(log)가 낮아지고 p95 APE가 악화되지 않으면 작품 유형별 깊이 효과가 있다고 본다.
- purpose: 작품 유형에 따라 깊이 정보의 가격 효과가 달라지는지 확인
- summary: Warm 최고는 D6 교차항: 깊이 x 작품 유형 전체 + Huber(MdAPE 0.7463), Cold 최고는 D6 교차항: 깊이 x 작품 유형 전체 + LightGBM(MdAPE 0.6467)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
