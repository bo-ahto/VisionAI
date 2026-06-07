# Track6 J1 세대/경력 x 호수 교차항 실험 결과

- 실험 목적: 작가의 세대/경력 단계에 따라 호수 효과가 다르게 나타나는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `J1 기준: 호수 + 세대/경력` / `Huber` / MdAPE `0.5169`
- Cold 최고: `J1 기준: 호수 + 세대/경력` / `Quantile-LAD` / MdAPE `0.4769`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/J1_profile_x_ln_ho/experiment_config.json`
- 사용 프롬프트: `experiments/track6/J1_profile_x_ln_ho/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작가의 세대/경력 단계에 따라 호수 효과가 다르게 나타나는지 확인
- 학습 피처: ln_estimated_ho, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count / ln_estimated_ho, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, birth_year_x_ln_ho, artist_exhibition_solo_count_x_ln_ho, artist_exhibition_group_count_x_ln_ho, artist_exhibition_fair_count_x_ln_ho
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group J: 작가 메타와 작품 변수 교차항
- 해석 중심: Cold 후보 가능성 중심으로 판단한다.
- purpose: 작가의 세대/경력 단계에 따라 호수 효과가 다르게 나타나는지 확인
- summary: Warm 최고는 J1 기준: 호수 + 세대/경력 + Huber(MdAPE 0.5169), Cold 최고는 J1 기준: 호수 + 세대/경력 + Quantile-LAD(MdAPE 0.4769)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
