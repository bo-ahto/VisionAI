# Track6 A4-1 제작연도/작품 연한 StandardScaler 실험 결과

- 실험 목적: 제작연도 관련 숫자형 변수만으로 가격 예측에 도움이 되는지 StandardScaler 전처리 기준으로 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `artwork_year 단독` / `Huber` / MdAPE `0.7491`
- Cold 최고: `artwork_age 단독` / `LightGBM` / MdAPE `0.7119`
- 사용 코드: `scripts/track6/a4_1_standard_scaled_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A4-1_artwork_year_age_standard_scaled/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A4-1_artwork_year_age_standard_scaled/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 제작연도 계열 변수만으로 가격 예측에 도움이 되는지 확인한다.
- 구현 기준: artwork_year와 artwork_age는 문자열이나 범주형으로 바꾸지 않고 연속형 숫자 피처로 처리한다.
- 전처리 기준: 숫자형 피처는 중앙값으로 결측 보정 후 StandardScaler를 적용한다.
- 제외 기준: 제작연도 출처, 제작연도 결측 여부 flag, HTML 보강 source, Saatchi 상세페이지 보강 출처는 모델 입력에서 제외한다.
- 데이터 기준: train/warm/cold split은 data/track6_split_with_year 기준으로 고정하고 sampling 없이 전체 split을 사용한다.
- 라벨 기준: feature 파일과 label 파일은 _track6_row_id로 연결하며, label은 학습 target과 평가 지표 계산에만 사용한다.
- 재현성 기준: 동일 설정으로 재실행 후 metrics_long 결과가 동일한지 비교한다.
- 결론 기준: Warm/Cold MdAPE, p95_APE, R2를 함께 보고 제작연도 계열 변수를 후속 작품 기본 피처 후보로 둘지 판단한다.
- purpose: 제작연도 관련 숫자형 변수만으로 가격 예측에 도움이 되는지 StandardScaler 전처리 기준으로 확인
- summary: Warm 최고는 artwork_year 단독 + Huber(MdAPE 0.7491), Cold 최고는 artwork_age 단독 + LightGBM(MdAPE 0.7119)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
