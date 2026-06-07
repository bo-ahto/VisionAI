# Track6 E5-1 작품 조건 통제 후 작가 국적 효과 실험

- 실험 목적: 호수, 난트 재료, 난트 도구, 난트 지지체를 통제한 뒤 작가 국적 정보가 가격 예측력을 높이는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `통제 기준 + 국적` / `Huber` / MdAPE `0.4899`
- Cold 최고: `통제 기준 + 국적 + 국적 결측 여부` / `Quantile-LAD` / MdAPE `0.4888`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/E5-1_controlled_nationality_effect/experiment_config.json`
- 사용 프롬프트: `experiments/track6/E5-1_controlled_nationality_effect/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작품 조건을 통제한 뒤 작가 국적 정보가 가격 예측력을 높이는지 확인
- 통제 조건: ln_estimated_ho, nant_material_idx, nant_tool, nant_support
- 학습 피처: 통제 기준 / 통제 기준 + artist_meta_nationality / 통제 기준 + artist_meta_nationality + artist_meta_nationality_is_missing
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 보조 분석: 호수 구간, 난트 재료, 난트 도구, 난트 지지체가 같은 조건 묶음 안에서 국적별 오차를 따로 확인한다.
- 해석 주의: 국적은 작가 자체 효과, 시장/플랫폼 표본 편향, 데이터 수집 편향이 섞일 수 있으므로 원인으로 단정하지 않는다.
- purpose: 호수, 난트 재료, 난트 도구, 난트 지지체를 통제한 뒤 작가 국적 정보가 가격 예측력을 높이는지 확인
- summary: Warm 최고는 통제 기준 + 국적 + Huber(MdAPE 0.4899), Cold 최고는 통제 기준 + 국적 + 국적 결측 여부 + Quantile-LAD(MdAPE 0.4888)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
- `outputs/controlled_condition_summary.csv`
- `outputs/controlled_nationality_within_condition_summary.csv`
- `outputs/controlled_slice_manifest.json`

## 해석 요약

- E5 단독 실험과 달리 E5-1은 작품 기본 조건을 먼저 통제했다.
- 통제 조건은 `ln_estimated_ho`, `nant_material_idx`, `nant_tool`, `nant_support`다.
- Warm Huber 기준 MdAPE는 `0.4962`에서 `0.4899`로 낮아졌다.
- Warm Huber 기준 Within-30은 `0.3344`에서 `0.3509`로 높아졌다.
- Warm Huber 기준 p95_APE는 `2.9236`에서 `2.9453`으로 소폭 악화됐다.
- Cold Quantile-LAD 기준 MdAPE는 `0.5128`에서 `0.4888`로 낮아졌다.
- Cold Quantile-LAD 기준 p95_APE는 `3.2103`에서 `3.2427`로 소폭 악화됐다.
- Cold Quantile-LAD 기준 Within-30은 `0.2588`에서 `0.2585`로 거의 변하지 않았다.
- 결론적으로 국적은 대표 오차 개선 신호가 있으나, 큰 오차 개선 근거는 아직 약하다.
- 조건 묶음 보조 분석에서는 비교 가능한 조건 묶음이 Warm `9`개, Cold `24`개 확인됐다.
- 국적은 최종 운영 피처라기보다 후속 검증 후보로 유지하는 것이 적절하다.
