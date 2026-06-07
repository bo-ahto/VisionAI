# Track6 OPT-W1 Warm 최적 피처 조합 후보 실험

- 실험 목적: A1-D11 결과에서 Warm 성능이 좋았던 작가명, 크기, 작품 기본 피처, 확장 피처, 작가명 x 면적 교차항을 같은 기준으로 다시 비교한다.
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `W1: 작가명 + 전체 크기` / `Huber` / MdAPE `0.1566`
- Cold 최고: `W5: W4 + 깊이/3D` / `LightGBM` / MdAPE `0.4588`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/OPT-W1_warm_optimal_feature_combo/experiment_config.json`
- 사용 프롬프트: `experiments/track6/OPT-W1_warm_optimal_feature_combo/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: A1-D11을 종합한 뒤 Warm 예측 정확도를 높일 수 있는 최적 피처 조합을 찾는다.
- 해석 중심: Warm 결과를 중심으로 해석한다. Cold 결과는 작가명 미학습 상황이므로 참고값으로만 본다.
- 판단 기준: Warm MdAPE를 1순위로 보고, p95 APE와 Within-30이 악화되지 않는 조합을 우선한다.
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 공통 실행 코드: scripts/track6/fixed_variable_experiment_runner.py
- purpose: A1-D11 결과에서 Warm 성능이 좋았던 작가명, 크기, 작품 기본 피처, 확장 피처, 작가명 x 면적 교차항을 같은 기준으로 다시 비교한다.
- summary: Warm 최고는 W1: 작가명 + 전체 크기 + Huber(MdAPE 0.1566), Cold 최고는 W5: W4 + 깊이/3D + LightGBM(MdAPE 0.4588)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
