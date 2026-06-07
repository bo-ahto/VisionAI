# Track6 A10 작품 기본 피처 묶음 + 제작연도 실험 결과

- 실험 목적: 작품 기본 피처 묶음에 제작연도 계열 숫자 피처를 추가했을 때 가격 예측 성능이 개선되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `작품 기본 피처 묶음` / `Huber` / MdAPE `0.4962`
- Cold 최고: `작품 기본 피처 묶음 + 작품 연한` / `LightGBM` / MdAPE `0.4999`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A10_basic_artwork_features_plus_year/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A10_basic_artwork_features_plus_year/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: A9에서 정의한 작품 기본 피처 묶음에 제작 시기 정보가 추가 설명력을 주는지 확인한다.
- 실험 위치: Group A의 작품 변수만 실험 중 A10에 해당하며, 작가명 없이 작품 자체 정보만 사용한다.
- 기준 피처: 작품 기본 피처 묶음은 ln_estimated_ho, nant_material_idx, nant_tool, nant_support로 둔다.
- 추가 피처: 제작연도 계열 피처는 artwork_year와 artwork_age만 사용한다.
- 숫자형 처리: ln_estimated_ho, artwork_year, artwork_age는 numeric_features에 명시하고 숫자형으로 학습한다. 숫자형은 one-hot 변환하지 않고 중앙값 결측 보정 후 StandardScaler를 적용한다.
- 범주형 처리: nant_material_idx, nant_tool, nant_support는 범주형으로 처리한다.
- 제외 피처: artwork_year_source, artwork_year_match_method, artwork_year_missing은 운영 입력값이 아니거나 이번 실험 판단 대상이 아니므로 제외한다.
- 공통 실행 코드: 모든 조합은 scripts/track6/fixed_variable_experiment_runner.py로 실행하며, 실험별 차이는 experiment_config.json의 변수 조합만 바꾼다.
- 판단 기준: 기준 피처 묶음 대비 MdAPE와 p95 APE가 낮아지면 제작연도 계열 피처의 추가 효과가 있다고 본다.
- 재현성 확인: 1차 실행 결과를 baseline으로 저장한 뒤 동일 데이터, 동일 설정, 동일 공통 실행 코드로 2차 재실행해 결과가 재현되는지 확인한다.
- purpose: 작품 기본 피처 묶음에 제작연도 계열 숫자 피처를 추가했을 때 가격 예측 성능이 개선되는지 확인
- summary: Warm 최고는 작품 기본 피처 묶음 + Huber(MdAPE 0.4962), Cold 최고는 작품 기본 피처 묶음 + 작품 연한 + LightGBM(MdAPE 0.4999)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
