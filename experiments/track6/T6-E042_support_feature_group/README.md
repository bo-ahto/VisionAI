# T6-E042 지지체 정보 추가 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H4`
- 가설: 지지체 정보는 기준 모델 + 재료 피처보다 가격 예측을 개선한다.
- 확인할 작품 피처: `support_category, nant_support`
- 피처 비교 원칙: `support_category` only, `nant_support` only, 둘 다 사용한 모델을 비교하고 최종 후보는 난트 피처를 우선
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 기준 피처: Warm `artist_name_ko + ln_estimated_ho`, Cold `ln_estimated_ho`
- 재료 묶음: `nant_material_idx + nant_tool`
- 지지체 묶음: `support_category + nant_support`
- 학습에 사용된 피처: `Warm 학습: artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + support_category + nant_support / Cold 학습: ln_estimated_ho + nant_material_idx + nant_tool + support_category + nant_support`
- 테스트에 사용된 피처: `학습 피처와 동일`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 기준 모델 + 재료 피처에 지지체 묶음을 추가해 비교
- 유의미함 기준: 성능 개선 시 후보 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Warm 기준 조건: `artist_name_ko + ln_estimated_ho`
- Cold 기준 조건: `ln_estimated_ho`
- 선행 재료 묶음 컬럼: `nant_material_idx`, `nant_tool`
- 지지체 묶음 컬럼: `support_category`, `nant_support`
- Cold에서는 `artist_name_ko` 제외

## 초기 실험 테스트: Warm

- 목적: 재료 정보를 이미 사용한 상태에서 지지체 정보가 추가 설명력을 주는지 확인
- 비교 기준 모델 피처: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool`
- 지지체 추가 모델 피처: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + support_category + nant_support`
- 추가 확인: `support_category`, `nant_support` 구간별 오차

## 초기 실험 테스트: Cold

- 목적: 신규 작가 상황에서 지지체가 재료 정보의 부족분을 보완하는지 확인
- 비교 기준 모델 피처: `ln_estimated_ho + nant_material_idx + nant_tool`
- 지지체 추가 모델 피처: `ln_estimated_ho + nant_material_idx + nant_tool + support_category + nant_support`
- 제외 피처: `artist_name_ko`
- 추가 확인: 지지체 결측 및 주요 지지체 구간별 p95 APE

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
