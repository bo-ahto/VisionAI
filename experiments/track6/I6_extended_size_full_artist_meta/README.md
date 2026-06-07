# Track6 I6 실제 크기 확장 + 전체 작가 메타 실험 결과

- 실험 목적: 실제 크기 정보와 전체 작가 메타 묶음을 함께 쓰면 호수 중심 모델보다 안정적인지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `I6 후보: 실제 크기 확장 + 전체 작가 메타` / `Huber` / MdAPE `0.4156`
- Cold 최고: `I6 후보: 실제 크기 확장 + 전체 작가 메타` / `Quantile-LAD` / MdAPE `0.4802`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/I6_extended_size_full_artist_meta/experiment_config.json`
- 사용 프롬프트: `experiments/track6/I6_extended_size_full_artist_meta/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 실제 크기 정보와 전체 작가 메타 묶음을 함께 쓰면 호수 중심 모델보다 안정적인지 확인
- 학습 피처: width_cm, height_cm, log_area, aspect_ratio / width_cm, height_cm, log_area, aspect_ratio, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_meta_nationality, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group I: 작가명 없는 Cold 후보 조합
- 해석 중심: Cold 결과 중심으로 판단한다.
- purpose: 실제 크기 정보와 전체 작가 메타 묶음을 함께 쓰면 호수 중심 모델보다 안정적인지 확인
- summary: Warm 최고는 I6 후보: 실제 크기 확장 + 전체 작가 메타 + Huber(MdAPE 0.4156), Cold 최고는 I6 후보: 실제 크기 확장 + 전체 작가 메타 + Quantile-LAD(MdAPE 0.4802)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
