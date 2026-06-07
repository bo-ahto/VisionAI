# Track6 D10 artist_name x 지지체 범주형 조합 실험 결과

- 실험 목적: 특정 작가가 특정 지지체에서 가격 프리미엄을 갖는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `D10 기준: 작가명 + 난트 지지체` / `Huber` / MdAPE `0.4250`
- Cold 최고: `D10 기준: 작가명 + 난트 지지체` / `LightGBM` / MdAPE `0.6891`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/D10_artist_support_categorical_interaction/experiment_config.json`
- 사용 프롬프트: `experiments/track6/D10_artist_support_categorical_interaction/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 특정 작가가 캔버스, 종이, 목재 등 특정 지지체에서 가격 프리미엄을 갖는지 확인한다.
- 실험군: Group D: 작가명과 작품 변수의 교차항
- 기준선: artist_name_ko + nant_support
- 학습 피처: 기준선과 artist_name_ko x NANT 지지체 조합 피처
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 구현 방식: 범주형 변수끼리의 조합이므로 상위 조합만 유지하고 나머지는 other로 묶는다.
- 해석 중심: 작가명이 들어간 조합 피처이므로 Warm 결과를 중심으로 판단한다.
- Cold 해석 주의: Cold는 신규 작가 상황이라 조합 피처 대부분이 other로 처리될 수 있어 참고값으로만 본다.
- 해석 기준: 조합 피처 추가 후 Warm MdAPE 또는 RMSE(log)가 낮아지고 p95 APE가 악화되지 않으면 작가별 지지체 프리미엄이 있다고 본다.
- purpose: 특정 작가가 특정 지지체에서 가격 프리미엄을 갖는지 확인
- summary: Warm 최고는 D10 기준: 작가명 + 난트 지지체 + Huber(MdAPE 0.4250), Cold 최고는 D10 기준: 작가명 + 난트 지지체 + LightGBM(MdAPE 0.6891)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
