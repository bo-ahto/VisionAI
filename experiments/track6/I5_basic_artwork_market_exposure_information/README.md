# Track6 I5 작품 기본 피처 + 시장 노출/정보량 실험 결과

- 실험 목적: 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `I5 후보: 작품 기본 피처 + 시장 노출/정보량` / `Huber` / MdAPE `0.4727`
- Cold 최고: `I5 후보: 작품 기본 피처 + 시장 노출/정보량` / `LightGBM` / MdAPE `0.4598`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/I5_basic_artwork_market_exposure_information/experiment_config.json`
- 사용 프롬프트: `experiments/track6/I5_basic_artwork_market_exposure_information/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인
- 학습 피처: ln_estimated_ho, nant_material_idx, nant_tool, nant_support / ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group I: 작가명 없는 Cold 후보 조합
- 해석 중심: Cold MdAPE와 p95 APE를 함께 본다.
- purpose: 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인
- summary: Warm 최고는 I5 후보: 작품 기본 피처 + 시장 노출/정보량 + Huber(MdAPE 0.4727), Cold 최고는 I5 후보: 작품 기본 피처 + 시장 노출/정보량 + LightGBM(MdAPE 0.4598)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
