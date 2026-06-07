# Track6 I1 호수 + 세대/경력 메타 실험 결과

- 실험 목적: 호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아지는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `I1 후보: 호수 + 세대/경력` / `Huber` / MdAPE `0.5169`
- Cold 최고: `I1 후보: 호수 + 세대/경력` / `Quantile-LAD` / MdAPE `0.4769`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/I1_ho_birth_exhibition_cold_candidate/experiment_config.json`
- 사용 프롬프트: `experiments/track6/I1_ho_birth_exhibition_cold_candidate/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아지는지 확인
- 학습 피처: ln_estimated_ho / ln_estimated_ho, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group I: 작가명 없는 Cold 후보 조합
- 해석 중심: Cold 결과 중심으로 판단한다.
- purpose: 호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아지는지 확인
- summary: Warm 최고는 I1 후보: 호수 + 세대/경력 + Huber(MdAPE 0.5169), Cold 최고는 I1 후보: 호수 + 세대/경력 + Quantile-LAD(MdAPE 0.4769)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
