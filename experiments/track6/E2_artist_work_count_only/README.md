# Track6 E2 작가별 학습 작품 수 단독 실험 결과

- 실험 목적: 학습 데이터 안에 작품 수가 많은 작가일수록 예측이 안정적인지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `작가별 학습 작품 수 로그` / `Huber` / MdAPE `0.7374`
- Cold 최고: `작가별 학습 작품 수 로그` / `Huber` / MdAPE `0.7028`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/E2_artist_work_count_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/E2_artist_work_count_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 학습 데이터 안에 작품 수가 많은 작가일수록 예측이 안정적인지 확인
- 학습 피처: artist_works_log
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group E: 작가 변수만
- 변수 성격: 수집값이 아니라 split의 train 기준 작가별 작품 수로 만든 생성 변수
- 해석 중심: Warm에서 작가별 학습량이 성능 안정성에 영향을 주는지 본다.
- Cold 해석 주의: Cold 신규 작가는 학습 작품 수가 0이므로 Cold 결과는 참고값으로만 본다.
- purpose: 학습 데이터 안에 작품 수가 많은 작가일수록 예측이 안정적인지 확인
- summary: Warm 최고는 작가별 학습 작품 수 로그 + Huber(MdAPE 0.7374), Cold 최고는 작가별 학습 작품 수 로그 + Huber(MdAPE 0.7028)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
