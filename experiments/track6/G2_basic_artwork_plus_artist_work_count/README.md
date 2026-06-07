# Track6 G2 작품 기본 피처 + 작가별 학습 작품 수 실험 결과

- 실험 목적: 작품 조건을 통제한 후 작가별 데이터 보유량이 예측 안정성에 도움 되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `작품 기본 피처 + 작가별 학습 작품 수` / `Huber` / MdAPE `0.4752`
- Cold 최고: `작품 기본 피처 + 작가별 학습 작품 수` / `Quantile-LAD` / MdAPE `0.5076`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/G2_basic_artwork_plus_artist_work_count/experiment_config.json`
- 사용 프롬프트: `experiments/track6/G2_basic_artwork_plus_artist_work_count/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작품 조건을 통제한 후 작가별 데이터 보유량이 예측 안정성에 도움 되는지 확인
- 학습 피처: ln_estimated_ho, nant_material_idx, nant_tool, nant_support / ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_works_log
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 통제 기준: Group G는 작품 기본 피처 묶음(ln_estimated_ho + nant_material_idx + nant_tool + nant_support)을 기준선으로 둔다.
- 실험군: Group G: 작가 메타/작가명 + 작품 변수
- purpose: 작품 조건을 통제한 후 작가별 데이터 보유량이 예측 안정성에 도움 되는지 확인
- summary: Warm 최고는 작품 기본 피처 + 작가별 학습 작품 수 + Huber(MdAPE 0.4752), Cold 최고는 작품 기본 피처 + 작가별 학습 작품 수 + Quantile-LAD(MdAPE 0.5076)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
