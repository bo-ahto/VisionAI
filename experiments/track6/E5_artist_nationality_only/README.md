# Track6 E5 작가 국적 단독 실험 결과

- 실험 목적: 작가 국적 정보가 가격 차이를 설명할 수 있는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `국적 only` / `Huber` / MdAPE `0.7752`
- Cold 최고: `국적 only` / `Quantile-LAD` / MdAPE `0.7036`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/E5_artist_nationality_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/E5_artist_nationality_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작가 국적 정보가 가격 차이를 설명할 수 있는지 확인
- 학습 피처: artist_meta_nationality / artist_meta_nationality, artist_meta_nationality_is_missing
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group E: 작가 변수만
- 해석 중심: 국적별 가격대 차이가 모델 성능으로 나타나는지 확인한다.
- 주의: 국적은 출처/표본 수 편차가 있을 수 있어 단독 채택보다 후속 통제 실험이 필요하다.
- purpose: 작가 국적 정보가 가격 차이를 설명할 수 있는지 확인
- summary: Warm 최고는 국적 only + Huber(MdAPE 0.7752), Cold 최고는 국적 only + Quantile-LAD(MdAPE 0.7036)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
