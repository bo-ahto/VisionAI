# Track6 J6 기본 프로필 x 재료 교차항 실험 결과

- 실험 목적: 작가 기본 프로필에 따라 재료 효과가 다르게 나타나는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `J6 교차항: 기본 프로필 x 재료` / `Huber` / MdAPE `0.7003`
- Cold 최고: `J6 기준: 기본 프로필 + 재료` / `Quantile-LAD` / MdAPE `0.6920`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/J6_profile_x_material/experiment_config.json`
- 사용 프롬프트: `experiments/track6/J6_profile_x_material/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작가 기본 프로필에 따라 재료 효과가 다르게 나타나는지 확인
- 학습 피처: artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_meta_nationality, nant_material_idx, nant_tool / artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_meta_nationality, nant_material_idx, nant_tool, nationality_material_idx_combo, nationality_tool_combo
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group J: 작가 메타와 작품 변수 교차항
- purpose: 작가 기본 프로필에 따라 재료 효과가 다르게 나타나는지 확인
- summary: Warm 최고는 J6 교차항: 기본 프로필 x 재료 + Huber(MdAPE 0.7003), Cold 최고는 J6 기준: 기본 프로필 + 재료 + Quantile-LAD(MdAPE 0.6920)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
