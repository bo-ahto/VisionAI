# Track6 J7 시장 노출/정보량 x 깊이 교차항 실험 결과

- 실험 목적: 작가의 시장 노출/정보량에 따라 입체성 효과가 다르게 나타나는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `J7 교차항: 시장 노출/정보량 x 깊이` / `Huber` / MdAPE `0.7582`
- Cold 최고: `J7 기준: 시장 노출/정보량 + 깊이` / `LightGBM` / MdAPE `0.6793`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/J7_market_exposure_x_depth/experiment_config.json`
- 사용 프롬프트: `experiments/track6/J7_market_exposure_x_depth/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작가의 시장 노출/정보량에 따라 입체성 효과가 다르게 나타나는지 확인
- 학습 피처: depth_cm, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score / depth_cm, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_meta_total_works_x_depth, artist_meta_for_sale_works_x_depth, artist_meta_followers_x_depth, artist_meta_is_p1_x_depth, artist_meta_available_count_x_depth, artist_meta_completeness_score_x_depth
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group J: 작가 메타와 작품 변수 교차항
- purpose: 작가의 시장 노출/정보량에 따라 입체성 효과가 다르게 나타나는지 확인
- summary: Warm 최고는 J7 교차항: 시장 노출/정보량 x 깊이 + Huber(MdAPE 0.7582), Cold 최고는 J7 기준: 시장 노출/정보량 + 깊이 + LightGBM(MdAPE 0.6793)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
