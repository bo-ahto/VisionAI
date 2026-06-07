# T6-E048 원본 재료 문구 키워드 추가 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H10`
- 가설: 원본 재료 문구에는 표준 재료 분류가 담지 못한 가격 차이 설명 정보가 있을 수 있다.
- 확인할 작품 피처: `collected_material_raw, nant_material_idx, nant_tool`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 기준 피처: Warm 기준: artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool / Cold 기준: ln_estimated_ho + nant_material_idx + nant_tool
- 추가 피처: Warm 추가: collected_material_raw에서 생성한 keyword flags / Cold 추가: collected_material_raw에서 생성한 keyword flags
- 학습 정답값: `ln_price_krw`
- 비교 기준: 표준 재료 피처 모델과 원본 재료 키워드 추가 모델 비교
- 유의미함 기준: 원본 키워드 추가 시 median APE 또는 특정 재료 slice 오차가 개선되면 후보 유지

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
