# Track6 D4 artwork_age x 재료 숫자형 교차항 실험 결과

- 실험 목적: 작품 연한에 따라 재료별 가격 효과가 달라지는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `D4 교차항: 연한 x 난트 도구명` / `Huber` / MdAPE `0.7311`
- Cold 최고: `D4 기준: 연한 + 난트 재료` / `LightGBM` / MdAPE `0.7015`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/D4_artwork_age_material_numeric_interaction/experiment_config.json`
- 사용 프롬프트: `experiments/track6/D4_artwork_age_material_numeric_interaction/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 오래된 유화, 오래된 수묵처럼 작품 연한과 재료가 함께 작용할 때 가격 예측이 개선되는지 확인한다.
- 실험군: Group D: 작품 변수끼리의 교차항
- 기준선: artwork_age + nant_material_idx + nant_tool
- 학습 피처: 기준선과 artwork_age x NANT 재료 교차항
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 구현 방식: artwork_age는 숫자형으로 유지하고, 상위 재료 카테고리별 표시값과 곱한 숫자형 교차항을 생성한다.
- 주의: 제작연도 출처와 결측 여부 flag는 사용하지 않는다.
- 해석 기준: 교차항 추가 후 MdAPE 또는 RMSE(log)가 낮아지고 p95 APE가 악화되지 않으면 재료별 연한 효과가 있다고 본다.
- purpose: 작품 연한에 따라 재료별 가격 효과가 달라지는지 확인
- summary: Warm 최고는 D4 교차항: 연한 x 난트 도구명 + Huber(MdAPE 0.7311), Cold 최고는 D4 기준: 연한 + 난트 재료 + LightGBM(MdAPE 0.7015)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
