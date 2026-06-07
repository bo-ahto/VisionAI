# Track6 A9 크기 + 재료 + 지지체 조합 실험 결과

- 실험 목적: 크기와 재료에 지지체 정보를 추가했을 때 작품 자체 정보의 가격 예측력이 개선되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `A8-2 Warm 최고 크기/재료 조합 + NANT 지지체` / `Huber` / MdAPE `0.4277`
- Cold 최고: `로그면적 + 수집 재료 대분류 + 수집 지지체 대분류` / `Huber` / MdAPE `0.4795`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A9_size_material_support_combo/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A9_size_material_support_combo/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: A8에서 확인한 크기+재료 조합에 지지체를 붙였을 때 예측 성능이 추가로 개선되는지 확인한다.
- 실험 위치: Group A의 작품 변수만 실험 중 A9에 해당하며, 작가명 없이 작품 자체 정보만 사용한다.
- 지지체 변수 설명: support_category는 수집/정제된 지지체 대분류이고, nant_support는 NANT 기준으로 정리한 지지체 값이다.
- 중복 변수 주의: support_category와 nant_support는 의미가 겹칠 수 있으므로 최종 후보에서는 둘 중 하나를 우선 선택한다. A9에서는 비교를 위해 둘 다 실험한다.
- 재료 변수 기준: medium_category는 수집 재료 대분류이고, collected_material_raw_bucket은 수집 원문 재료명 빈도 묶음이다. nant_material_idx와 nant_tool은 NANT 기준 재료 번호와 도구명이다.
- 크기 변수 기준: log_area는 공통 크기 기준이고, 일부 조합에서는 A8-1 Warm 후보인 ln_estimated_ho, log_area, width_cm, height_cm 묶음을 함께 사용한다.
- 숫자형 처리: ln_estimated_ho, log_area, width_cm, height_cm는 numeric_features에 명시하고 숫자형으로 학습한다. 숫자형은 one-hot 변환하지 않고 중앙값 결측 보정 후 StandardScaler를 적용한다.
- 범주형 처리: medium_category, nant_material_idx, nant_tool, support_category, nant_support, collected_material_raw_bucket은 범주형으로 처리한다.
- 공통 실행 코드: 모든 조합은 scripts/track6/fixed_variable_experiment_runner.py로 실행하며, 실험별 차이는 experiment_config.json의 변수 조합만 바꾼다.
- 판단 기준: A8 또는 A8-2의 같은 크기/재료 기준 대비 MdAPE와 p95 APE가 낮아지면 지지체 추가 효과가 있다고 본다.
- 재현성 확인: 1차 실행 결과를 baseline으로 저장한 뒤 동일 데이터, 동일 설정, 동일 공통 실행 코드로 2차 재실행해 결과가 재현되는지 확인한다.
- purpose: 크기와 재료에 지지체 정보를 추가했을 때 작품 자체 정보의 가격 예측력이 개선되는지 확인
- summary: Warm 최고는 A8-2 Warm 최고 크기/재료 조합 + NANT 지지체 + Huber(MdAPE 0.4277), Cold 최고는 로그면적 + 수집 재료 대분류 + 수집 지지체 대분류 + Huber(MdAPE 0.4795)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
