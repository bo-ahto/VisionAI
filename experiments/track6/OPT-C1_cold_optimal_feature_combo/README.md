# Track6 OPT-C1 Cold 최적 피처 조합 후보 실험

- 실험 목적: A1-D11 결과에서 Cold 성능이 좋았던 작품 변수 확장, 깊이/3D, 면적 x 지지체 교차항을 같은 기준으로 다시 비교한다.
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `COLD2: A12 + 면적 x 지지체` / `Huber` / MdAPE `0.3803`
- Cold 최고: `COLD3: C9형 깊이/3D 포함 작품 피처` / `LightGBM` / MdAPE `0.4671`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/OPT-C1_cold_optimal_feature_combo/experiment_config.json`
- 사용 프롬프트: `experiments/track6/OPT-C1_cold_optimal_feature_combo/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: A1-D11을 종합한 뒤 Cold 예측 정확도를 높일 수 있는 최적 피처 조합을 찾는다.
- 해석 중심: Cold 결과를 중심으로 해석한다. 작가명은 사용하지 않는다.
- 판단 기준: Cold MdAPE를 1순위로 보고, p95 APE와 Within-30이 악화되지 않는 조합을 우선한다.
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 공통 실행 코드: scripts/track6/fixed_variable_experiment_runner.py
- purpose: A1-D11 결과에서 Cold 성능이 좋았던 작품 변수 확장, 깊이/3D, 면적 x 지지체 교차항을 같은 기준으로 다시 비교한다.
- summary: Warm 최고는 COLD2: A12 + 면적 x 지지체 + Huber(MdAPE 0.3803), Cold 최고는 COLD3: C9형 깊이/3D 포함 작품 피처 + LightGBM(MdAPE 0.4671)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
