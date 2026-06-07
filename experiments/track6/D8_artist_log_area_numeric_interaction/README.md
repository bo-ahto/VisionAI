# Track6 D8 artist_name x log_area 숫자형 교차항 실험 결과

- 실험 목적: 작가별로 대형 작품 프리미엄이 달라지는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `D8 교차항: 작가명 x 면적` / `Huber` / MdAPE `0.1565`
- Cold 최고: `D8 교차항: 작가명 x 면적` / `Quantile-LAD` / MdAPE `0.5071`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/D8_artist_log_area_numeric_interaction/experiment_config.json`
- 사용 프롬프트: `experiments/track6/D8_artist_log_area_numeric_interaction/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 같은 면적 증가라도 작가별로 대형작 가격 프리미엄이 달라지는지 확인한다.
- 실험군: Group D: 작가명과 작품 변수의 교차항
- 기준선: artist_name_ko + log_area
- 학습 피처: 기준선과 log_area x artist_name_ko 숫자형 교차항
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 구현 방식: log_area는 숫자형으로 유지하고, 학습 데이터 작품 수 상위 작가별 표시값과 곱한 숫자형 교차항을 생성한다.
- 해석 중심: 작가명이 들어간 교차항이므로 Warm 결과를 중심으로 판단한다.
- Cold 해석 주의: Cold는 신규 작가 상황이라 artist_name_ko 교차항 대부분이 학습된 작가와 맞지 않으므로 참고값으로만 본다.
- 해석 기준: 교차항 추가 후 Warm MdAPE 또는 RMSE(log)가 낮아지고 p95 APE가 악화되지 않으면 작가별 대형작 프리미엄이 있다고 본다.
- purpose: 작가별로 대형 작품 프리미엄이 달라지는지 확인
- summary: Warm 최고는 D8 교차항: 작가명 x 면적 + Huber(MdAPE 0.1565), Cold 최고는 D8 교차항: 작가명 x 면적 + Quantile-LAD(MdAPE 0.5071)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
