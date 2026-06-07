# Track6 A11 작품 기본 피처 묶음 + 제작연도 + 작품 유형 실험 결과

- 실험 목적: 작품 기본 피처 묶음과 제작연도 계열 변수에 작품 유형을 추가했을 때 가격 예측 성능이 개선되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `A10 기준 피처 묶음 + 작품 유형 전체 구분` / `Huber` / MdAPE `0.4804`
- Cold 최고: `A10 기준 피처 묶음 + 작품 유형 전체 구분` / `LightGBM` / MdAPE `0.4816`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A11_basic_artwork_features_plus_type/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A11_basic_artwork_features_plus_type/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: A10 기준 작품 정보에 작품 유형을 추가했을 때 예측 성능이 개선되는지 확인한다.
- 실험 위치: Group A의 작품 변수만 실험 중 A11에 해당하며, 작가명 없이 작품 자체 정보만 사용한다.
- 기준 피처: A10 기준 피처는 ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artwork_year, artwork_age로 둔다.
- 추가 피처: 작품 유형은 artwork_type_final과 artwork_type_final_major3를 비교한다.
- 제외 피처: artwork_type_source, artwork_type_match_method, artwork_type_raw, artwork_type_confidence는 출처/처리 과정 정보이므로 모델 입력에서 제외한다.
- 숫자형 처리: ln_estimated_ho, artwork_year, artwork_age는 numeric_features에 명시하고 중앙값 결측 보정 후 StandardScaler를 적용한다.
- 범주형 처리: nant_material_idx, nant_tool, nant_support, artwork_type_final, artwork_type_final_major3는 범주형으로 처리한다.
- 공통 실행 코드: 모든 조합은 scripts/track6/fixed_variable_experiment_runner.py로 실행하며, 실험별 차이는 experiment_config.json의 변수 조합만 바꾼다.
- 판단 기준: A10 기준 피처 대비 MdAPE와 p95 APE가 낮아지면 작품 유형의 추가 효과가 있다고 본다.
- 재현성 기준: 이번 A11은 요청에 따라 1회 실행 결과만 기록한다.
- purpose: 작품 기본 피처 묶음과 제작연도 계열 변수에 작품 유형을 추가했을 때 가격 예측 성능이 개선되는지 확인
- summary: Warm 최고는 A10 기준 피처 묶음 + 작품 유형 전체 구분 + Huber(MdAPE 0.4804), Cold 최고는 A10 기준 피처 묶음 + 작품 유형 전체 구분 + LightGBM(MdAPE 0.4816)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
