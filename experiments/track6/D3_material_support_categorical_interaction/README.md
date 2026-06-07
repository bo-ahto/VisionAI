# Track6 D3 재료 x 지지체 범주형 조합 실험 결과

- 실험 목적: 재료와 지지체 조합이 단독 재료/지지체보다 가격 차이를 더 잘 설명하는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `D3 조합: 난트 재료번호 x 지지체` / `Huber` / MdAPE `0.7177`
- Cold 최고: `D3 조합: 난트 재료번호 x 지지체` / `Huber` / MdAPE `0.6977`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/D3_material_support_categorical_interaction/experiment_config.json`
- 사용 프롬프트: `experiments/track6/D3_material_support_categorical_interaction/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 유화+캔버스, 수묵+종이처럼 재료와 지지체 조합이 가격 예측에 추가 설명력을 주는지 확인한다.
- 실험군: Group D: 작품 변수끼리의 교차항
- 기준선: nant_material_idx + nant_tool + nant_support
- 학습 피처: 기준선과 NANT 재료 x NANT 지지체 조합 피처
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 구현 방식: 범주형 변수끼리의 조합이므로 상위 조합만 유지하고 나머지는 other로 묶는다.
- 해석 기준: 조합 피처 추가 후 MdAPE 또는 RMSE(log)가 낮아지고 p95 APE가 악화되지 않으면 재료-지지체 조합 효과가 있다고 본다.
- purpose: 재료와 지지체 조합이 단독 재료/지지체보다 가격 차이를 더 잘 설명하는지 확인
- summary: Warm 최고는 D3 조합: 난트 재료번호 x 지지체 + Huber(MdAPE 0.7177), Cold 최고는 D3 조합: 난트 재료번호 x 지지체 + Huber(MdAPE 0.6977)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
