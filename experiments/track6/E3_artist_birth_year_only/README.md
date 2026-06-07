# Track6 E3 작가 생년 단독 실험 결과

- 실험 목적: 작가의 생년 정보가 가격 차이를 설명할 수 있는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `생년 원값 + 결측 여부` / `Ridge` / MdAPE `0.7508`
- Cold 최고: `생년 원값` / `Quantile-LAD` / MdAPE `0.6985`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/E3_artist_birth_year_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/E3_artist_birth_year_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작가의 생년 정보가 가격 차이를 설명할 수 있는지 확인
- 학습 피처: artist_meta_birth_year / artist_meta_birth_year, artist_meta_birth_year_is_missing
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group E: 작가 변수만
- 해석 중심: 생년 또는 세대 정보가 단독으로 가격대 차이를 설명하는지 본다.
- 결측 주의: 메타가 있는 작품만 골라 평가하지 않고 결측 flag를 함께 비교한다.
- purpose: 작가의 생년 정보가 가격 차이를 설명할 수 있는지 확인
- summary: Warm 최고는 생년 원값 + 결측 여부 + Ridge(MdAPE 0.7508), Cold 최고는 생년 원값 + Quantile-LAD(MdAPE 0.6985)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
