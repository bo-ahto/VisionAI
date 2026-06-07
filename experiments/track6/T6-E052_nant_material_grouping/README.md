# T6-E052 난트 재료 분류 그룹화 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H14`
- 가설: 난트 재료 분류 번호가 너무 세분화되어 있으면 그룹화했을 때 더 안정적인 가격 예측이 가능할 수 있다.
- 확인할 작품 피처: `nant_material_idx, nant_tool, nant_material_group`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 기준 피처: Warm 기준: artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool / Cold 기준: ln_estimated_ho + nant_material_idx + nant_tool
- 추가 피처: Warm/Cold 비교: nant_material_idx 원본 vs nant_material_group
- 학습 정답값: `ln_price_krw`
- 비교 기준: 원본 idx 모델과 상위 그룹화 모델 비교
- 유의미함 기준: Cold p95 APE 감소 또는 성능 유지 시 그룹화 후보 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Cold에서는 `artist_name_ko` 제외

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
