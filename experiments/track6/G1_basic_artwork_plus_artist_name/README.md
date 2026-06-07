# Track6 G1 작품 기본 피처 + 작가명 실험 결과

- 실험 목적: 호수·재료·지지체를 통제한 뒤에도 작가명이 가격 예측력을 높이는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `작품 기본 피처 + 작가명` / `Huber` / MdAPE `0.1831`
- Cold 최고: `작품 기본 피처 + 작가명` / `LightGBM` / MdAPE `0.4956`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/G1_basic_artwork_plus_artist_name/experiment_config.json`
- 사용 프롬프트: `experiments/track6/G1_basic_artwork_plus_artist_name/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 호수·재료·지지체를 통제한 뒤에도 작가명이 가격 예측력을 높이는지 확인
- 학습 피처: ln_estimated_ho, nant_material_idx, nant_tool, nant_support / ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_name_ko
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 통제 기준: Group G는 작품 기본 피처 묶음(ln_estimated_ho + nant_material_idx + nant_tool + nant_support)을 기준선으로 둔다.
- 실험군: Group G: 작가 메타/작가명 + 작품 변수
- 해석 중심: Warm 결과 중심. Cold의 작가명 효과는 참고값이다.
- purpose: 호수·재료·지지체를 통제한 뒤에도 작가명이 가격 예측력을 높이는지 확인
- summary: Warm 최고는 작품 기본 피처 + 작가명 + Huber(MdAPE 0.1831), Cold 최고는 작품 기본 피처 + 작가명 + LightGBM(MdAPE 0.4956)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
