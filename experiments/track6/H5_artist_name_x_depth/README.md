# Track6 H5 작가명 x 깊이 교차항 실험 결과

- 실험 목적: 같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다른지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `H5 교차항: 작가명 x 깊이` / `Huber` / MdAPE `0.4225`
- Cold 최고: `H5 교차항: 작가명 x 깊이` / `LightGBM` / MdAPE `0.6514`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/H5_artist_name_x_depth/experiment_config.json`
- 사용 프롬프트: `experiments/track6/H5_artist_name_x_depth/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다른지 확인
- 학습 피처: artist_name_ko, depth_cm / artist_name_ko, depth_cm
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group H: 작가명과 작품 변수 교차항
- 해석 중심: 작가명이 포함되므로 Warm 결과를 중심으로 판단한다.
- purpose: 같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다른지 확인
- summary: Warm 최고는 H5 교차항: 작가명 x 깊이 + Huber(MdAPE 0.4225), Cold 최고는 H5 교차항: 작가명 x 깊이 + LightGBM(MdAPE 0.6514)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
