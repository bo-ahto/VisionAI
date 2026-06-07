# T6-E041 재료 정보 추가 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H3`
- 가설: 재료 정보는 기준 모델보다 가격 예측을 개선한다.
- 확인할 작품 피처: `nant_material_idx, nant_tool`
- 피처 비교 원칙: `nant_material_idx + nant_tool` only, 둘 다 사용한 모델을 비교하고 최종 후보는 난트 피처를 우선
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 재료 컬럼: `nant_material_idx + nant_tool`
- 학습에 사용된 피처: `Warm 학습: artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool / Cold 학습: ln_estimated_ho + nant_material_idx + nant_tool`
- 테스트에 사용된 피처: `학습 피처와 동일`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 기준 모델에 `nant_material_idx + nant_tool` 추가해 비교
- 유의미함 기준: median APE 또는 p95 APE 개선 시 후보 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Warm 기준 조건: `artist_name_ko + ln_estimated_ho`
- Cold 기준 조건: `ln_estimated_ho`
- Cold에서는 `artist_name_ko` 제외

## 초기 실험 테스트: Warm

- 목적: Warm에서 재료 정보가 작가명+호수 기준 모델보다 가격 예측을 개선하는지 확인
- 기준 모델 피처: `artist_name_ko + ln_estimated_ho`
- 재료 추가 모델 피처: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool`
- 추가 확인: `nant_material_idx`, `nant_tool` 값 있음/없음 구간별 성능

## 초기 실험 테스트: Cold

- 목적: 신규 작가 예측에서 작가명 없이 재료 정보가 가격 예측을 개선하는지 확인
- 기준 모델 피처: `ln_estimated_ho`
- 재료 추가 모델 피처: `ln_estimated_ho + nant_material_idx + nant_tool`
- 제외 피처: `artist_name_ko`
- 추가 확인: 재료 unknown 또는 난트 재료 결측 구간의 오차

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
