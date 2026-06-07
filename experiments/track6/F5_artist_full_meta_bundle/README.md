# Track6 F5 전체 작가 메타 묶음 실험 결과

- 실험 목적: 작가명 없이 전체 작가 메타 묶음만으로 가격 예측이 가능한지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `전체 작가 메타 묶음` / `Ridge` / MdAPE `0.7311`
- Cold 최고: `전체 작가 메타 묶음` / `Huber` / MdAPE `0.6956`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/F5_artist_full_meta_bundle/experiment_config.json`
- 사용 프롬프트: `experiments/track6/F5_artist_full_meta_bundle/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작가명 없이 전체 작가 메타 묶음만으로 가격 예측이 가능한지 확인
- 학습 피처: artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_meta_nationality, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_exhibition_available_count, artist_meta_birth_year_is_missing, artist_exhibition_solo_count_is_missing, artist_exhibition_group_count_is_missing, artist_exhibition_fair_count_is_missing, artist_meta_nationality_is_missing, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 통제 기준: Group G는 작품 기본 피처 묶음(ln_estimated_ho + nant_material_idx + nant_tool + nant_support)을 기준선으로 둔다.
- 실험군: Group F: 작가 메타 변수 조합
- 확인 결과 활용: 작가명 대체 가능성이 낮으면 작가 메타는 단독 모델보다 보조 피처로만 사용한다.
- purpose: 작가명 없이 전체 작가 메타 묶음만으로 가격 예측이 가능한지 확인
- summary: Warm 최고는 전체 작가 메타 묶음 + Ridge(MdAPE 0.7311), Cold 최고는 전체 작가 메타 묶음 + Huber(MdAPE 0.6956)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
