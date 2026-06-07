# Track6 A12 작품 정보 전체 확장 실험 결과

- 실험 목적: A11 피처 묶음에 depth/3D와 edition 정보를 추가했을 때 작품 자체 정보 전체 모델의 성능이 개선되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `A11 기준 피처 묶음 + edition` / `Huber` / MdAPE `0.4733`
- Cold 최고: `A11 기준 피처 묶음 + depth/3D` / `LightGBM` / MdAPE `0.4727`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A12_full_artwork_features_expanded/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A12_full_artwork_features_expanded/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: A11 기준 작품 정보에 depth/3D와 edition을 추가했을 때 작품 자체 정보 전체 모델이 개선되는지 확인한다.
- 실험 위치: Group A의 작품 변수만 실험 중 A12에 해당하며, 작가명 없이 작품 자체 정보만 사용한다.
- 기준 피처: A11 기준 피처는 ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artwork_year, artwork_age, artwork_type_final로 둔다.
- 추가 피처: depth/3D는 depth_cm, has_depth, is_3d_candidate를 사용하고, edition은 edition_class 및 에디션 파생 플래그를 사용한다.
- signed 제외: signed는 구조화 수집 컬럼이 없어 A12 모델 입력에서 제외한다.
- 출처 제외: edition_source, artwork_type_source, artwork_year_source 등 출처/처리 과정 정보는 모델 입력에서 제외한다.
- 숫자형 처리: ln_estimated_ho, artwork_year, artwork_age, depth_cm, has_depth, is_3d_candidate, edition flag는 numeric_features에 명시하고 중앙값 결측 보정 후 StandardScaler를 적용한다.
- 범주형 처리: nant_material_idx, nant_tool, nant_support, artwork_type_final, edition_class는 범주형으로 처리한다.
- 공통 실행 코드: 모든 조합은 scripts/track6/fixed_variable_experiment_runner.py로 실행하며, 실험별 차이는 experiment_config.json의 변수 조합만 바꾼다.
- 판단 기준: A11 기준 피처 대비 MdAPE와 p95 APE가 낮아지면 depth/3D 또는 edition의 추가 효과가 있다고 본다.
- 재현성 기준: 이번 A12는 요청에 따라 1회 실행 결과만 기록한다.
- purpose: A11 피처 묶음에 depth/3D와 edition 정보를 추가했을 때 작품 자체 정보 전체 모델의 성능이 개선되는지 확인
- summary: Warm 최고는 A11 기준 피처 묶음 + edition + Huber(MdAPE 0.4733), Cold 최고는 A11 기준 피처 묶음 + depth/3D + LightGBM(MdAPE 0.4727)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
