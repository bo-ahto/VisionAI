# Track6 G3 작품 기본 피처 + 작가 생년 실험 결과

- 실험 목적: 작품 조건을 통제한 후 작가 생년/세대 정보가 가격 예측력을 높이는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `작품 기본 피처 + 생년 + 결측` / `Huber` / MdAPE `0.4870`
- Cold 최고: `작품 기본 피처 + 생년` / `Quantile-LAD` / MdAPE `0.4716`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/G3_basic_artwork_plus_birth_year/experiment_config.json`
- 사용 프롬프트: `experiments/track6/G3_basic_artwork_plus_birth_year/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작품 조건을 통제한 후 작가 생년/세대 정보가 가격 예측력을 높이는지 확인
- 학습 피처: ln_estimated_ho, nant_material_idx, nant_tool, nant_support / ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_birth_year / ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_birth_year, artist_meta_birth_year_is_missing
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 통제 기준: Group G는 작품 기본 피처 묶음(ln_estimated_ho + nant_material_idx + nant_tool + nant_support)을 기준선으로 둔다.
- 실험군: Group G: 작가 메타/작가명 + 작품 변수
- purpose: 작품 조건을 통제한 후 작가 생년/세대 정보가 가격 예측력을 높이는지 확인
- summary: Warm 최고는 작품 기본 피처 + 생년 + 결측 + Huber(MdAPE 0.4870), Cold 최고는 작품 기본 피처 + 생년 + Quantile-LAD(MdAPE 0.4716)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
