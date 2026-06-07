# Track6 H1 작가명 x 호수 교차항 실험 결과

- 실험 목적: 같은 호수라도 작가명에 따라 가격대가 다른지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `H1 교차항: 작가명 x 호수` / `Huber` / MdAPE `0.1762`
- Cold 최고: `H1 기준: 작가명 + 호수` / `LightGBM` / MdAPE `0.5062`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/H1_artist_name_x_ln_ho/experiment_config.json`
- 사용 프롬프트: `experiments/track6/H1_artist_name_x_ln_ho/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 같은 호수라도 작가명에 따라 가격대가 다른지 확인
- 학습 피처: artist_name_ko, ln_estimated_ho / artist_name_ko, ln_estimated_ho
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group H: 작가명과 작품 변수 교차항
- 해석 중심: 작가명이 포함되므로 Warm 결과를 중심으로 판단한다.
- 중복 검토: H2/H3/H4는 기존 D8/D9/D10과 중복되어 신규 실행하지 않고 결과 매핑한다.
- purpose: 같은 호수라도 작가명에 따라 가격대가 다른지 확인
- summary: Warm 최고는 H1 교차항: 작가명 x 호수 + Huber(MdAPE 0.1762), Cold 최고는 H1 기준: 작가명 + 호수 + LightGBM(MdAPE 0.5062)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
