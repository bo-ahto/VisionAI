# Track6 B1 작가명 단독 실험 결과

- 실험 목적: 작가명 한글 변수만으로 작품 가격대가 어느 정도 설명되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `artist_name_ko only` / `Huber` / MdAPE `0.4352`
- Cold 최고: `artist_name_ko only` / `LightGBM` / MdAPE `0.7018`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/B1_artist_name_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/B1_artist_name_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작품의 크기, 재료, 지지체를 모두 제외하고 작가명 하나만으로 가격대가 얼마나 설명되는지 확인한다.
- 실험군: Group B: 작가 변수만
- 학습 피처: artist_name_ko
- 테스트 피처: artist_name_ko
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 최신 split에 artist_name_ko를 _track6_row_id 기준으로 보강한 별도 split을 사용한다.
- 해석 주의: Warm은 학습 데이터에 같은 작가가 있는 상황이라 작가명 효과를 직접 확인할 수 있다. Cold는 학습에 없는 신규 작가명이므로 대부분 미학습 카테고리로 처리되어 최종 Cold 모델 판단에는 쓰지 않고 참고값으로만 본다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE를 확인한다.
- 결론 기준: Warm에서 작가명 only가 낮은 MdAPE와 RMSE(log)를 보이면 작가 효과가 크다고 판단한다. Cold에서 성능이 낮으면 신규 작가에는 작가명 단독 모델을 쓰기 어렵다는 근거로 남긴다.
- purpose: 작가명 한글 변수만으로 작품 가격대가 어느 정도 설명되는지 확인
- summary: Warm 최고는 artist_name_ko only + Huber(MdAPE 0.4352), Cold 최고는 artist_name_ko only + LightGBM(MdAPE 0.7018)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
