# Track6 A6 깊이/has_depth 실험 결과

- 실험 목적: 깊이 정보와 깊이 존재 여부가 작품 가격 예측에 도움이 되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `깊이 수치` / `Huber` / MdAPE `0.7458`
- Cold 최고: `깊이 수치 + 깊이 존재 여부` / `LightGBM` / MdAPE `0.6761`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A6_depth_has_depth_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A6_depth_has_depth_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 입체성 정보가 가격대 구분에 도움이 되는지 확인한다.
- 사용 피처: A6 기준에 맞춰 depth_cm과 has_depth만 사용한다.
- 제외 피처: is_3d_candidate는 3D 후보 플래그라 별도 실험에서 다루고, 이번 A6에는 넣지 않는다.
- 처리 기준: depth_cm은 숫자형으로 처리하고 결측은 학습 데이터 중앙값으로 보정한다. has_depth는 범주형 플래그로 처리한다.
- 해석 기준: 같은 고정 모델군에서 MdAPE와 p95 APE가 낮아지면 깊이 정보가 가격 예측에 도움이 된다고 본다.
- 주의: 깊이 값이 있는 작품이 반드시 조각/입체 작품이라는 뜻은 아니므로, A6는 깊이 변수 자체의 영향만 확인한다.
- purpose: 깊이 정보와 깊이 존재 여부가 작품 가격 예측에 도움이 되는지 확인
- summary: Warm 최고는 깊이 수치 + Huber(MdAPE 0.7458), Cold 최고는 깊이 수치 + 깊이 존재 여부 + LightGBM(MdAPE 0.6761)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
