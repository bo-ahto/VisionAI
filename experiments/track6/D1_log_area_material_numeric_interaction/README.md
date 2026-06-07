# Track6 D1 log_area x 재료 숫자형 교차항 실험 결과

- 실험 목적: 같은 면적이라도 재료에 따라 가격 증가 방식이 달라지는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `D1 교차항: 면적 x 난트 재료번호` / `Huber` / MdAPE `0.4747`
- Cold 최고: `D1 기준: 면적 + 난트 재료` / `Quantile-LAD` / MdAPE `0.4979`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/D1_log_area_material_numeric_interaction/experiment_config.json`
- 사용 프롬프트: `experiments/track6/D1_log_area_material_numeric_interaction/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 큰 유화, 큰 아크릴처럼 면적과 재료가 함께 작용할 때 가격 예측이 개선되는지 확인한다.
- 실험군: Group D: 작품 변수끼리의 교차항
- 기준선: log_area + nant_material_idx + nant_tool
- 학습 피처: 기준선과 log_area x NANT 재료 교차항
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 구현 방식: log_area는 숫자형으로 유지하고, 상위 재료 카테고리별 표시값과 곱한 숫자형 교차항을 생성한다.
- 해석 기준: 교차항 추가 후 MdAPE 또는 RMSE(log)가 낮아지고 p95 APE가 악화되지 않으면 재료별 면적 프리미엄이 있다고 본다.
- purpose: 같은 면적이라도 재료에 따라 가격 증가 방식이 달라지는지 확인
- summary: Warm 최고는 D1 교차항: 면적 x 난트 재료번호 + Huber(MdAPE 0.4747), Cold 최고는 D1 기준: 면적 + 난트 재료 + Quantile-LAD(MdAPE 0.4979)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
